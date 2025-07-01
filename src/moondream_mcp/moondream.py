"""
Moondream client for vision analysis.

Provides async interface to the Moondream vision model for image captioning,
visual question answering, object detection, and visual pointing.
"""

import asyncio
import io
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import aiofiles
import aiohttp
import torch
from PIL import Image
from transformers import AutoModelForCausalLM

from .config import Config
from .models import (
    BoundingBox,
    CaptionLength,
    CaptionResult,
    DetectedObject,
    DetectionResult,
    Point,
    PointedObject,
    PointingResult,
    QueryResult,
)


class MoondreamError(Exception):
    """Base exception for Moondream-related errors."""

    def __init__(self, message: str, error_code: str = "MOONDREAM_ERROR") -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class ModelLoadError(MoondreamError):
    """Error loading the Moondream model."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "MODEL_LOAD_ERROR")


class ImageProcessingError(MoondreamError):
    """Error processing image data."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "IMAGE_PROCESSING_ERROR")


class InferenceError(MoondreamError):
    """Error during model inference."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "INFERENCE_ERROR")


class MoondreamClient:
    """Client for interacting with the Moondream model."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._model: Optional[Any] = None
        self._tokenizer: Optional[Any] = None
        self._device: Optional[torch.device] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(config.max_concurrent_requests)

    async def __aenter__(self) -> "MoondreamClient":
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.cleanup()

    async def _ensure_session(self) -> None:
        """Ensure HTTP session is available."""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout_seconds)
            connector = aiohttp.TCPConnector(limit=10)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={"User-Agent": self.config.user_agent},
            )

    async def _ensure_model_loaded(self) -> None:
        """Ensure the model is loaded and ready."""
        if self._model is None:
            await self._load_model()

    async def _load_model(self) -> None:
        """Load the Moondream model and tokenizer."""
        try:
            print(
                f"🔄 Loading Moondream model: {self.config.model_name}@{self.config.model_revision}",
                file=sys.stderr,
            )

            # Set device
            self._device = torch.device(self.config.device)
            print(f"📱 Using device: {self.config.get_device_info()}", file=sys.stderr)

            # Load model in a thread to avoid blocking
            loop = asyncio.get_event_loop()

            def _load_model_sync() -> Any:
                model = AutoModelForCausalLM.from_pretrained(
                    self.config.model_name,
                    revision=self.config.model_revision,
                    trust_remote_code=self.config.trust_remote_code,
                    torch_dtype=(
                        torch.float16 if self.config.device != "cpu" else torch.float32
                    ),
                )
                return model.to(self._device)

            self._model = await loop.run_in_executor(None, _load_model_sync)

            # Load tokenizer (if needed)
            # Note: Moondream2 might not need a separate tokenizer
            # self._tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)

            print("✅ Moondream model loaded successfully", file=sys.stderr)

        except Exception as e:
            raise ModelLoadError(f"Failed to load Moondream model: {str(e)}")

    async def _load_image(self, image_path: str) -> Image.Image:
        """Load image from local path or remote URL."""
        try:
            if self._is_url(image_path):
                return await self._load_image_from_url(image_path)
            else:
                return await self._load_image_from_file(image_path)
        except Exception as e:
            raise ImageProcessingError(
                f"Failed to load image from {image_path}: {str(e)}"
            )

    def _is_url(self, path: str) -> bool:
        """Check if path is a URL."""
        try:
            result = urlparse(path)
            return bool(result.scheme and result.netloc)
        except Exception:
            return False

    async def _load_image_from_url(self, url: str) -> Image.Image:
        """Load image from remote URL."""
        await self._ensure_session()

        # Type assertion to help mypy
        assert self._session is not None

        try:
            async with self._session.get(url) as response:
                if response.status != 200:
                    raise ImageProcessingError(
                        f"Failed to download image: HTTP {response.status}"
                    )

                # Check content type
                content_type = response.headers.get("content-type", "")
                if not content_type.startswith("image/"):
                    raise ImageProcessingError(
                        f"URL does not point to an image: {content_type}"
                    )

                # Check file size
                content_length = response.headers.get("content-length")
                if content_length:
                    size_mb = int(content_length) / (1024 * 1024)
                    if size_mb > self.config.max_file_size_mb:
                        raise ImageProcessingError(
                            f"Image too large: {size_mb:.1f}MB > {self.config.max_file_size_mb}MB"
                        )

                # Read image data
                image_data = await response.read()
                image = Image.open(io.BytesIO(image_data))

                return self._preprocess_image(image)

        except aiohttp.ClientError as e:
            raise ImageProcessingError(f"Network error loading image: {str(e)}")

    async def _load_image_from_file(self, file_path: str) -> Image.Image:
        """Load image from local file."""
        try:
            # Expand user path
            path = Path(file_path).expanduser().resolve()

            # Check if file exists
            if not path.exists():
                raise ImageProcessingError(f"Image file not found: {file_path}")

            # Check file size
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > self.config.max_file_size_mb:
                raise ImageProcessingError(
                    f"Image too large: {size_mb:.1f}MB > {self.config.max_file_size_mb}MB"
                )

            # Read image file
            async with aiofiles.open(path, "rb") as f:
                image_data = await f.read()

            image = Image.open(io.BytesIO(image_data))
            return self._preprocess_image(image)

        except Exception as e:
            if isinstance(e, ImageProcessingError):
                raise
            raise ImageProcessingError(f"Error reading image file: {str(e)}")

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for model input."""
        try:
            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Resize if too large
            max_width, max_height = self.config.max_image_size
            if image.width > max_width or image.height > max_height:
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            return image

        except Exception as e:
            raise ImageProcessingError(f"Error preprocessing image: {str(e)}")

    async def caption_image(
        self,
        image_path: str,
        length: CaptionLength = CaptionLength.NORMAL,
        stream: bool = False,
    ) -> CaptionResult:
        """Generate a caption for an image."""
        async with self._semaphore:
            start_time = time.time()

            try:
                await self._ensure_model_loaded()
                image = await self._load_image(image_path)

                # Generate caption
                loop = asyncio.get_event_loop()

                def _generate_caption() -> Dict[str, Any]:
                    # Type assertion to help mypy
                    assert self._model is not None

                    if stream and self.config.enable_streaming:
                        # Stream caption generation
                        result = self._model.caption(
                            image, length=length.value, stream=True
                        )
                        caption_parts = []
                        for part in result["caption"]:
                            caption_parts.append(part)
                        caption = "".join(caption_parts)
                    else:
                        # Non-streaming caption generation
                        result = self._model.caption(image, length=length.value)
                        caption = result["caption"]

                    return {"caption": caption}

                result = await loop.run_in_executor(None, _generate_caption)

                processing_time = (time.time() - start_time) * 1000

                return CaptionResult(
                    success=True,
                    caption=result["caption"],
                    length=length,
                    processing_time_ms=processing_time,
                    confidence=None,  # Moondream doesn't provide confidence for captions
                    error_message=None,
                    error_code=None,
                    metadata={
                        "image_path": image_path,
                        "image_size": f"{image.width}x{image.height}",
                        "device": self.config.device,
                    },
                )

            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                error_msg = str(e)

                if isinstance(e, (ModelLoadError, ImageProcessingError)):
                    raise

                return CaptionResult(
                    success=False,
                    error_message=error_msg,
                    error_code="PROCESSING_ERROR",
                    processing_time_ms=processing_time,
                    metadata={"image_path": image_path},
                    caption=None,
                    confidence=None,
                    length=None,
                )

    async def query_image(self, image_path: str, question: str) -> QueryResult:
        """Ask a question about an image."""
        async with self._semaphore:
            start_time = time.time()

            try:
                await self._ensure_model_loaded()
                image = await self._load_image(image_path)

                # Query the image
                loop = asyncio.get_event_loop()

                def _query_image() -> Dict[str, Any]:
                    # Type assertion to help mypy
                    assert self._model is not None
                    result = self._model.query(image, question)
                    return {"answer": result["answer"]}

                result = await loop.run_in_executor(None, _query_image)

                processing_time = (time.time() - start_time) * 1000

                return QueryResult(
                    success=True,
                    answer=result["answer"],
                    question=question,
                    processing_time_ms=processing_time,
                    confidence=None,  # Moondream doesn't provide confidence for VQA
                    error_message=None,
                    error_code=None,
                    metadata={
                        "image_path": image_path,
                        "image_size": f"{image.width}x{image.height}",
                        "device": self.config.device,
                    },
                )

            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                error_msg = str(e)

                if isinstance(e, (ModelLoadError, ImageProcessingError)):
                    raise

                return QueryResult(
                    success=False,
                    error_message=error_msg,
                    error_code="PROCESSING_ERROR",
                    question=question,
                    processing_time_ms=processing_time,
                    answer=None,
                    confidence=None,
                    metadata={"image_path": image_path},
                )

    async def detect_objects(
        self, image_path: str, object_name: str
    ) -> DetectionResult:
        """Detect objects in an image."""
        async with self._semaphore:
            start_time = time.time()

            try:
                await self._ensure_model_loaded()
                image = await self._load_image(image_path)

                # Detect objects
                loop = asyncio.get_event_loop()

                def _detect_objects() -> Dict[str, Any]:
                    # Type assertion to help mypy
                    assert self._model is not None
                    result = self._model.detect(image, object_name)
                    return {"objects": result["objects"]}

                result = await loop.run_in_executor(None, _detect_objects)

                # Convert to our format
                detected_objects = []
                for obj in result["objects"]:
                    # Note: The exact format depends on Moondream's output
                    # This is a placeholder - adjust based on actual API
                    detected_objects.append(
                        DetectedObject(
                            name=object_name,
                            confidence=obj.get("confidence", 0.5),
                            bounding_box=BoundingBox(
                                x=obj.get("x", 0.0),
                                y=obj.get("y", 0.0),
                                width=obj.get("width", 0.1),
                                height=obj.get("height", 0.1),
                            ),
                        )
                    )

                processing_time = (time.time() - start_time) * 1000

                return DetectionResult(
                    success=True,
                    objects=detected_objects,
                    object_name=object_name,
                    total_found=len(detected_objects),
                    processing_time_ms=processing_time,
                    error_message=None,
                    error_code=None,
                    metadata={
                        "image_path": image_path,
                        "image_size": f"{image.width}x{image.height}",
                        "device": self.config.device,
                    },
                )

            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                error_msg = str(e)

                if isinstance(e, (ModelLoadError, ImageProcessingError)):
                    raise

                return DetectionResult(
                    success=False,
                    error_message=error_msg,
                    error_code="PROCESSING_ERROR",
                    object_name=object_name,
                    processing_time_ms=processing_time,
                    metadata={"image_path": image_path},
                )

    async def point_objects(self, image_path: str, object_name: str) -> PointingResult:
        """Point to objects in an image."""
        async with self._semaphore:
            start_time = time.time()

            try:
                await self._ensure_model_loaded()
                image = await self._load_image(image_path)

                # Point to objects
                loop = asyncio.get_event_loop()

                def _point_objects() -> Dict[str, Any]:
                    # Type assertion to help mypy
                    assert self._model is not None
                    result = self._model.point(image, object_name)
                    return {"points": result["points"]}

                result = await loop.run_in_executor(None, _point_objects)

                # Convert to our format
                pointed_objects = []
                for point in result["points"]:
                    # Note: The exact format depends on Moondream's output
                    # This is a placeholder - adjust based on actual API
                    pointed_objects.append(
                        PointedObject(
                            name=object_name,
                            confidence=point.get("confidence", 0.5),
                            point=Point(
                                x=point.get("x", 0.5),
                                y=point.get("y", 0.5),
                            ),
                        )
                    )

                processing_time = (time.time() - start_time) * 1000

                return PointingResult(
                    success=True,
                    points=pointed_objects,
                    object_name=object_name,
                    total_found=len(pointed_objects),
                    processing_time_ms=processing_time,
                    error_message=None,
                    error_code=None,
                    metadata={
                        "image_path": image_path,
                        "image_size": f"{image.width}x{image.height}",
                        "device": self.config.device,
                    },
                )

            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                error_msg = str(e)

                if isinstance(e, (ModelLoadError, ImageProcessingError)):
                    raise

                return PointingResult(
                    success=False,
                    error_message=error_msg,
                    error_code="PROCESSING_ERROR",
                    object_name=object_name,
                    processing_time_ms=processing_time,
                    metadata={"image_path": image_path},
                )

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._session:
            await self._session.close()
            self._session = None

        # Clear model from memory
        if self._model is not None:
            del self._model
            self._model = None

        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None

        # Clear CUDA cache if using GPU
        if self.config.device in ("cuda", "mps"):
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        print("🧹 Moondream client cleaned up", file=sys.stderr)
