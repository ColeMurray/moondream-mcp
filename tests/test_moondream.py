"""
Tests for Moondream client wrapper.
"""

import asyncio
import io
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from moondream_mcp.config import Config
from moondream_mcp.models import CaptionLength
from moondream_mcp.moondream import (
    ImageProcessingError,
    InferenceError,
    ModelLoadError,
    MoondreamClient,
    MoondreamError,
)


class TestMoondreamClient:
    """Test MoondreamClient functionality."""

    @pytest.fixture
    def config(self) -> Config:
        """Create test configuration."""
        config = Config()
        config.device = "cpu"
        config.max_image_size = (512, 512)
        config.max_file_size_mb = 10
        return config

    @pytest.fixture
    def client(self, config: Config) -> MoondreamClient:
        """Create test client."""
        return MoondreamClient(config)

    @pytest.fixture
    def sample_image(self) -> Image.Image:
        """Create a sample test image."""
        return Image.new("RGB", (100, 100), color="red")

    def test_client_initialization(self, config: Config) -> None:
        """Test client initialization."""
        client = MoondreamClient(config)

        assert client.config == config
        assert client._model is None
        assert client._tokenizer is None
        assert client._device is None
        assert client._session is None

    @pytest.mark.asyncio
    async def test_context_manager(self, client: MoondreamClient) -> None:
        """Test async context manager functionality."""
        async with client as ctx_client:
            assert ctx_client is client
            assert client._session is not None

    @pytest.mark.asyncio
    async def test_cleanup(self, client: MoondreamClient) -> None:
        """Test resource cleanup."""
        # Set up some mock resources
        mock_session = AsyncMock()
        client._session = mock_session
        client._model = MagicMock()
        client._tokenizer = MagicMock()

        await client.cleanup()

        # Check that session.close() was called
        mock_session.close.assert_called_once()
        # Check that resources were cleared
        assert client._session is None
        assert client._model is None
        assert client._tokenizer is None

    def test_is_url(self, client: MoondreamClient) -> None:
        """Test URL detection."""
        assert client._is_url("https://example.com/image.jpg")
        assert client._is_url("http://example.com/image.jpg")
        assert not client._is_url("/path/to/image.jpg")
        assert not client._is_url("image.jpg")
        assert not client._is_url("invalid-url")

    def test_preprocess_image(
        self, client: MoondreamClient, sample_image: Image.Image
    ) -> None:
        """Test image preprocessing."""
        # Test RGB conversion
        grayscale_image = Image.new("L", (100, 100), color=128)
        processed = client._preprocess_image(grayscale_image)
        assert processed.mode == "RGB"

        # Test resizing
        large_image = Image.new("RGB", (1000, 1000), color="blue")
        processed = client._preprocess_image(large_image)
        assert processed.width <= client.config.max_image_size[0]
        assert processed.height <= client.config.max_image_size[1]

    @pytest.mark.asyncio
    async def test_load_image_from_file_not_found(
        self, client: MoondreamClient
    ) -> None:
        """Test loading non-existent file."""
        with pytest.raises(ImageProcessingError, match="Image file not found"):
            await client._load_image_from_file("/nonexistent/path.jpg")

    @pytest.mark.asyncio
    async def test_load_image_from_file_too_large(
        self, client: MoondreamClient, tmp_path: Path
    ) -> None:
        """Test loading file that's too large."""
        # Create a file that exceeds size limit
        large_file = tmp_path / "large.jpg"
        large_file.write_bytes(
            b"x" * (client.config.max_file_size_mb * 1024 * 1024 + 1)
        )

        with pytest.raises(ImageProcessingError, match="Image too large"):
            await client._load_image_from_file(str(large_file))

    @pytest.mark.asyncio
    @patch("aiofiles.open")
    async def test_load_image_from_file_success(
        self,
        mock_aiofiles_open: AsyncMock,
        client: MoondreamClient,
        sample_image: Image.Image,
        tmp_path: Path,
    ) -> None:
        """Test successful file loading."""
        # Create a real image file
        image_file = tmp_path / "test.jpg"
        sample_image.save(image_file, "JPEG")

        # Mock aiofiles to return the image data
        image_data = image_file.read_bytes()
        mock_file = AsyncMock()
        mock_file.read.return_value = image_data
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file

        result = await client._load_image_from_file(str(image_file))

        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"

    @pytest.mark.asyncio
    async def test_load_image_from_url_http_error(
        self, client: MoondreamClient
    ) -> None:
        """Test URL loading with HTTP error."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response

            await client._ensure_session()

            with pytest.raises(
                ImageProcessingError, match="Failed to download image: HTTP 404"
            ):
                await client._load_image_from_url("https://example.com/notfound.jpg")

    @pytest.mark.asyncio
    async def test_load_image_from_url_wrong_content_type(
        self, client: MoondreamClient
    ) -> None:
        """Test URL loading with wrong content type."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.headers = {"content-type": "text/html"}
            mock_get.return_value.__aenter__.return_value = mock_response

            await client._ensure_session()

            with pytest.raises(
                ImageProcessingError, match="URL does not point to an image"
            ):
                await client._load_image_from_url("https://example.com/page.html")

    @pytest.mark.asyncio
    async def test_load_image_from_url_too_large(self, client: MoondreamClient) -> None:
        """Test URL loading with file too large."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.headers = {
                "content-type": "image/jpeg",
                "content-length": str(client.config.max_file_size_mb * 1024 * 1024 + 1),
            }
            mock_get.return_value.__aenter__.return_value = mock_response

            await client._ensure_session()

            with pytest.raises(ImageProcessingError, match="Image too large"):
                await client._load_image_from_url("https://example.com/large.jpg")

    @pytest.mark.asyncio
    async def test_caption_image_success(
        self, client: MoondreamClient, sample_image: Image.Image
    ) -> None:
        """Test successful image captioning."""
        with (
            patch.object(client, "_ensure_model_loaded") as mock_ensure_model,
            patch.object(
                client, "_load_image", return_value=sample_image
            ) as mock_load_image,
            patch("asyncio.get_event_loop") as mock_get_loop,
        ):
            # Mock the model
            mock_model = MagicMock()
            mock_model.caption.return_value = {"caption": "A red square"}
            client._model = mock_model

            # Mock the executor
            mock_loop = MagicMock()
            mock_loop.run_in_executor.return_value = asyncio.Future()
            mock_loop.run_in_executor.return_value.set_result(
                {"caption": "A red square"}
            )
            mock_get_loop.return_value = mock_loop

            result = await client.caption_image("test.jpg", CaptionLength.NORMAL)

            assert result.success is True
            assert result.caption == "A red square"
            assert result.length == CaptionLength.NORMAL
            assert result.processing_time_ms is not None
            mock_ensure_model.assert_called_once()
            mock_load_image.assert_called_once_with("test.jpg")

    @pytest.mark.asyncio
    async def test_caption_image_model_error(self, client: MoondreamClient) -> None:
        """Test image captioning with model error."""
        with patch.object(
            client,
            "_ensure_model_loaded",
            side_effect=ModelLoadError("Model failed to load"),
        ):
            with pytest.raises(ModelLoadError, match="Model failed to load"):
                await client.caption_image("test.jpg")

    @pytest.mark.asyncio
    async def test_query_image_success(
        self, client: MoondreamClient, sample_image: Image.Image
    ) -> None:
        """Test successful visual question answering."""
        with (
            patch.object(client, "_ensure_model_loaded") as mock_ensure_model,
            patch.object(
                client, "_load_image", return_value=sample_image
            ) as mock_load_image,
            patch("asyncio.get_event_loop") as mock_get_loop,
        ):
            # Mock the model
            mock_model = MagicMock()
            mock_model.query.return_value = {"answer": "Yes, it is red"}
            client._model = mock_model

            # Mock the executor
            mock_loop = MagicMock()
            mock_loop.run_in_executor.return_value = asyncio.Future()
            mock_loop.run_in_executor.return_value.set_result(
                {"answer": "Yes, it is red"}
            )
            mock_get_loop.return_value = mock_loop

            result = await client.query_image("test.jpg", "Is this red?")

            assert result.success is True
            assert result.answer == "Yes, it is red"
            assert result.question == "Is this red?"
            assert result.processing_time_ms is not None

    @pytest.mark.asyncio
    async def test_detect_objects_success(
        self, client: MoondreamClient, sample_image: Image.Image
    ) -> None:
        """Test successful object detection."""
        with (
            patch.object(client, "_ensure_model_loaded") as mock_ensure_model,
            patch.object(
                client, "_load_image", return_value=sample_image
            ) as mock_load_image,
            patch("asyncio.get_event_loop") as mock_get_loop,
        ):
            # Mock the model
            mock_model = MagicMock()
            mock_model.detect.return_value = {
                "objects": [
                    {"confidence": 0.9, "x": 0.1, "y": 0.1, "width": 0.8, "height": 0.8}
                ]
            }
            client._model = mock_model

            # Mock the executor
            mock_loop = MagicMock()
            mock_loop.run_in_executor.return_value = asyncio.Future()
            mock_loop.run_in_executor.return_value.set_result(
                {
                    "objects": [
                        {
                            "confidence": 0.9,
                            "x": 0.1,
                            "y": 0.1,
                            "width": 0.8,
                            "height": 0.8,
                        }
                    ]
                }
            )
            mock_get_loop.return_value = mock_loop

            result = await client.detect_objects("test.jpg", "square")

            assert result.success is True
            assert result.object_name == "square"
            assert result.total_found == 1
            assert len(result.objects) == 1
            assert result.objects[0].confidence == 0.9

    @pytest.mark.asyncio
    async def test_point_objects_success(
        self, client: MoondreamClient, sample_image: Image.Image
    ) -> None:
        """Test successful visual pointing."""
        with (
            patch.object(client, "_ensure_model_loaded") as mock_ensure_model,
            patch.object(
                client, "_load_image", return_value=sample_image
            ) as mock_load_image,
            patch("asyncio.get_event_loop") as mock_get_loop,
        ):
            # Mock the model
            mock_model = MagicMock()
            mock_model.point.return_value = {
                "points": [{"confidence": 0.8, "x": 0.5, "y": 0.5}]
            }
            client._model = mock_model

            # Mock the executor
            mock_loop = MagicMock()
            mock_loop.run_in_executor.return_value = asyncio.Future()
            mock_loop.run_in_executor.return_value.set_result(
                {"points": [{"confidence": 0.8, "x": 0.5, "y": 0.5}]}
            )
            mock_get_loop.return_value = mock_loop

            result = await client.point_objects("test.jpg", "center")

            assert result.success is True
            assert result.object_name == "center"
            assert result.total_found == 1
            assert len(result.points) == 1
            assert result.points[0].confidence == 0.8
            assert result.points[0].point.x == 0.5
            assert result.points[0].point.y == 0.5

    @pytest.mark.asyncio
    async def test_model_loading_error(self, client: MoondreamClient) -> None:
        """Test model loading failure."""
        with patch(
            "moondream_mcp.moondream.AutoModelForCausalLM.from_pretrained",
            side_effect=Exception("Model not found"),
        ):
            with pytest.raises(ModelLoadError, match="Failed to load Moondream model"):
                await client._load_model()

    @pytest.mark.asyncio
    async def test_semaphore_concurrency_control(
        self, client: MoondreamClient, sample_image: Image.Image
    ) -> None:
        """Test that semaphore controls concurrency."""
        # Set a low concurrency limit
        client._semaphore = asyncio.Semaphore(1)

        with (
            patch.object(client, "_ensure_model_loaded"),
            patch.object(client, "_load_image", return_value=sample_image),
            patch("asyncio.get_event_loop") as mock_get_loop,
        ):
            mock_model = MagicMock()
            mock_model.caption.return_value = {"caption": "Test"}
            client._model = mock_model

            mock_loop = MagicMock()
            mock_loop.run_in_executor.return_value = asyncio.Future()
            mock_loop.run_in_executor.return_value.set_result({"caption": "Test"})
            mock_get_loop.return_value = mock_loop

            # Start multiple concurrent requests
            tasks = [
                client.caption_image("test1.jpg"),
                client.caption_image("test2.jpg"),
            ]

            results = await asyncio.gather(*tasks)

            # Both should succeed
            assert all(result.success for result in results)
            assert all(result.caption == "Test" for result in results)
