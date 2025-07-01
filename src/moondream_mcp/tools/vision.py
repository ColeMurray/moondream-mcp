"""
Vision analysis tools for Moondream MCP Server.

Provides FastMCP tools for image captioning, visual question answering,
object detection, and visual pointing.
"""

import asyncio
import json
import time
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from moondream_mcp.models import (
    CaptionResult,
    DetectionResult,
    PointingResult,
    QueryResult,
)
from moondream_mcp.moondream import ImageProcessingError, ModelLoadError
from moondream_mcp.validation import (
    ValidationError,
    validate_caption_length,
    validate_image_path,
    validate_image_paths_list,
    validate_object_name,
    validate_operation,
    validate_question,
)

if TYPE_CHECKING:
    from fastmcp import FastMCP

    from ..config import Config
    from ..moondream import MoondreamClient


async def _route_single_operation(
    client: "MoondreamClient",
    operation: str,
    image_path: str,
    params: Dict[str, Any],
) -> Union[CaptionResult, QueryResult, DetectionResult, PointingResult]:
    """
    Route a single image analysis operation to the appropriate client method.

    Args:
        client: MoondreamClient instance
        operation: Operation type ('caption', 'query', 'detect', 'point')
        image_path: Path to image file
        params: Operation-specific parameters

    Returns:
        Analysis result

    Raises:
        ValidationError: If parameters are invalid
        MoondreamError: If analysis fails
    """
    if operation == "caption":
        length = params.get("length", "normal")
        stream = params.get("stream", False)

        # Validate length parameter
        caption_length = validate_caption_length(length)

        return await client.caption_image(
            image_path=image_path,
            length=caption_length,
            stream=stream,
        )

    elif operation == "query":
        question = params.get("question")
        if not question:
            raise ValidationError(
                "question parameter is required for query operation", "MISSING_QUESTION"
            )

        # Validate question
        validated_question = validate_question(question)

        return await client.query_image(
            image_path=image_path,
            question=validated_question,
        )

    elif operation == "detect":
        object_name = params.get("object_name")
        if not object_name:
            raise ValidationError(
                "object_name parameter is required for detect operation",
                "MISSING_OBJECT_NAME",
            )

        # Validate object name
        validated_object_name = validate_object_name(object_name)

        return await client.detect_objects(
            image_path=image_path,
            object_name=validated_object_name,
        )

    elif operation == "point":
        object_name = params.get("object_name")
        if not object_name:
            raise ValidationError(
                "object_name parameter is required for point operation",
                "MISSING_OBJECT_NAME",
            )

        # Validate object name
        validated_object_name = validate_object_name(object_name)

        return await client.point_objects(
            image_path=image_path,
            object_name=validated_object_name,
        )

    else:
        # This should never happen due to earlier validation
        raise ValidationError(f"Unknown operation: {operation}", "INVALID_OPERATION")


def _create_error_response_dict(
    error: Exception, operation: str, context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized error response as dictionary."""
    from datetime import datetime, timezone

    from .utils import get_error_code_for_exception

    # Determine error code and message using centralized logic
    if isinstance(error, ValidationError):
        error_code = error.error_code
        error_message = error.message
    elif isinstance(error, (ModelLoadError, ImageProcessingError)):
        error_code = "PROCESSING_ERROR"
        error_message = str(error)
    elif isinstance(error, FileNotFoundError):
        error_code = "FILE_NOT_FOUND"
        error_message = f"Image file not found: {str(error)}"
    elif isinstance(error, PermissionError):
        error_code = "PERMISSION_DENIED"
        error_message = f"Permission denied accessing image: {str(error)}"
    else:
        # Use centralized error code mapping for consistency
        error_code = get_error_code_for_exception(error)
        error_message = f"Unexpected error: {str(error)}"

    return {
        "success": False,
        "error_message": error_message,
        "error_code": error_code,
        "error_context": context or {},
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "operation": operation,
    }


def _create_error_response(
    error: Exception, operation: str, context: Optional[Dict[str, Any]] = None
) -> str:
    """Create standardized error response as JSON string."""
    error_dict = _create_error_response_dict(error, operation, context)
    return json.dumps(error_dict, indent=2)


def register_vision_tools(
    mcp: "FastMCP",
    moondream_client: "MoondreamClient",
    config: Optional["Config"] = None,
) -> None:
    """Register vision analysis MCP tools."""

    # Import here to avoid circular imports
    from ..config import Config

    # Use default config if none provided
    if config is None:
        config = Config.from_env()

    @mcp.tool()
    async def caption_image(
        image_path: str,
        length: str = "normal",
        stream: bool = False,
    ) -> str:
        """
        Generate a caption for an image.

        Args:
            image_path: Path to image file (local path or URL)
            length: Caption length - 'short', 'normal', or 'detailed'
            stream: Whether to stream the caption generation

        Returns:
            JSON string with caption result
        """
        try:
            # Validate inputs
            validated_path = validate_image_path(image_path)
            caption_length = validate_caption_length(length)

            result = await moondream_client.caption_image(
                image_path=validated_path,
                length=caption_length,
                stream=stream,
            )

            return json.dumps(result.model_dump(), indent=2)

        except Exception as e:
            return _create_error_response(
                error=e,
                operation="caption",
                context={"image_path": image_path, "length": length, "stream": stream},
            )

    @mcp.tool()
    async def query_image(image_path: str, question: str) -> str:
        """
        Ask a question about an image (Visual Question Answering).

        Args:
            image_path: Path to image file (local path or URL)
            question: Question to ask about the image

        Returns:
            JSON string with answer result
        """
        try:
            # Validate inputs
            validated_path = validate_image_path(image_path)
            validated_question = validate_question(question)

            result = await moondream_client.query_image(
                image_path=validated_path,
                question=validated_question,
            )

            return json.dumps(result.model_dump(), indent=2)

        except Exception as e:
            return _create_error_response(
                error=e,
                operation="query",
                context={"image_path": image_path, "question": question},
            )

    @mcp.tool()
    async def detect_objects(image_path: str, object_name: str) -> str:
        """
        Detect specific objects in an image.

        Args:
            image_path: Path to image file (local path or URL)
            object_name: Name of object to detect (e.g., 'person', 'car', 'face')

        Returns:
            JSON string with detection results including bounding boxes
        """
        try:
            # Validate inputs
            validated_path = validate_image_path(image_path)
            validated_object_name = validate_object_name(object_name)

            result = await moondream_client.detect_objects(
                image_path=validated_path,
                object_name=validated_object_name,
            )

            return json.dumps(result.model_dump(), indent=2)

        except Exception as e:
            return _create_error_response(
                error=e,
                operation="detect",
                context={"image_path": image_path, "object_name": object_name},
            )

    @mcp.tool()
    async def point_objects(image_path: str, object_name: str) -> str:
        """
        Point to specific objects in an image (get coordinates).

        Args:
            image_path: Path to image file (local path or URL)
            object_name: Name of object to locate (e.g., 'person', 'car', 'face')

        Returns:
            JSON string with pointing results including coordinates
        """
        try:
            # Validate inputs
            validated_path = validate_image_path(image_path)
            validated_object_name = validate_object_name(object_name)

            result = await moondream_client.point_objects(
                image_path=validated_path,
                object_name=validated_object_name,
            )

            return json.dumps(result.model_dump(), indent=2)

        except Exception as e:
            return _create_error_response(
                error=e,
                operation="point",
                context={"image_path": image_path, "object_name": object_name},
            )

    @mcp.tool()
    async def analyze_image(
        image_path: str,
        operation: str,
        # Typed parameters for different operations
        question: str = "",
        object_name: str = "",
        length: str = "normal",
        stream: bool = False,
    ) -> str:
        """
        Multi-purpose image analysis tool with typed parameters.

        Args:
            image_path: Path to image file (local path or URL)
            operation: Operation to perform ('caption', 'query', 'detect', 'point')
            question: Question for 'query' operation (required for query)
            object_name: Object name for 'detect' or 'point' operations (required for detect/point)
            length: Caption length for 'caption' operation ('short', 'normal', 'detailed')
            stream: Whether to stream caption generation (for caption operation)

        Returns:
            JSON string with analysis results
        """
        try:
            # Validate inputs
            validated_path = validate_image_path(image_path)
            validated_operation = validate_operation(operation)

            # Build parameters based on operation type
            params = {}

            if validated_operation == "caption":
                params = {
                    "length": length,
                    "stream": stream,
                }
            elif validated_operation == "query":
                if not question.strip():
                    raise ValidationError(
                        "question parameter is required for query operation",
                        "MISSING_QUESTION",
                    )
                params = {"question": question}
            elif validated_operation in ("detect", "point"):
                if not object_name.strip():
                    raise ValidationError(
                        f"object_name parameter is required for "
                        f"{validated_operation} operation",
                        "MISSING_OBJECT_NAME",
                    )
                params = {"object_name": object_name}

            # Route to appropriate method using shared logic
            result = await _route_single_operation(
                client=moondream_client,
                operation=validated_operation,
                image_path=validated_path,
                params=params,
            )

            return json.dumps(result.model_dump(), indent=2)

        except Exception as e:
            return _create_error_response(
                error=e,
                operation=operation,
                context={
                    "image_path": image_path,
                    "question": question,
                    "object_name": object_name,
                    "length": length,
                    "stream": stream,
                },
            )

    @mcp.tool()
    async def batch_analyze_images(
        image_paths: str,
        operation: str,
        # Typed parameters for different operations
        question: str = "",
        object_name: str = "",
        length: str = "normal",
        stream: bool = False,
    ) -> str:
        """
        Analyze multiple images in batch with parallel processing and typed parameters.

        Args:
            image_paths: JSON array of image paths (local paths or URLs)
            operation: Operation to perform ('caption', 'query', 'detect', 'point')
            question: Question for 'query' operation (required for query)
            object_name: Object name for 'detect' or 'point' operations (required for detect/point)
            length: Caption length for 'caption' operation ('short', 'normal', 'detailed')
            stream: Whether to stream caption generation (for caption operation)

        Returns:
            JSON string with batch analysis results
        """
        start_time = time.time()

        try:
            # Validate operation first
            validated_operation = validate_operation(operation)

            # Validate and parse image paths
            validated_paths = validate_image_paths_list(image_paths)

            # Check batch size limits
            if len(validated_paths) > config.max_batch_size:
                raise ValidationError(
                    f"Batch size {len(validated_paths)} exceeds maximum "
                    f"allowed {config.max_batch_size}",
                    "BATCH_SIZE_EXCEEDED",
                )

            # Build parameters based on operation type
            params = {}

            if validated_operation == "caption":
                params = {
                    "length": length,
                    "stream": stream,
                }
            elif validated_operation == "query":
                if not question.strip():
                    raise ValidationError(
                        "question parameter is required for query operation",
                        "MISSING_QUESTION",
                    )
                params = {"question": question}
            elif validated_operation in ("detect", "point"):
                if not object_name.strip():
                    raise ValidationError(
                        f"object_name parameter is required for "
                        f"{validated_operation} operation",
                        "MISSING_OBJECT_NAME",
                    )
                params = {"object_name": object_name}

            # Process images in parallel batches
            results = []
            semaphore = asyncio.Semaphore(config.batch_concurrency)

            async def process_single_image(image_path: str) -> Dict[str, Any]:
                async with semaphore:
                    try:
                        result = await _route_single_operation(
                            client=moondream_client,
                            operation=validated_operation,
                            image_path=image_path,
                            params=params,
                        )
                        return result.model_dump()
                    except Exception as e:
                        # Return error result for this specific image
                        error_result = _create_error_response_dict(
                            error=e,
                            operation=validated_operation,
                            context={"image_path": image_path},
                        )
                        return error_result

            # Execute all tasks concurrently
            tasks = [process_single_image(path) for path in validated_paths]
            results = await asyncio.gather(*tasks, return_exceptions=False)

            # Calculate statistics
            successful_count = sum(
                1 for result in results if result.get("success", False)
            )
            failed_count = len(results) - successful_count

            # Sum individual processing times if available (handle None values)
            individual_processing_time = sum(
                result.get("processing_time_ms") or 0 for result in results
            )

            total_time_ms = (time.time() - start_time) * 1000

            # Create batch result
            batch_result = {
                "success": True,
                "operation": validated_operation,
                "total_processed": len(validated_paths),
                "successful_count": successful_count,
                "failed_count": failed_count,
                "results": results,
                "batch_processing_time_ms": total_time_ms,
                "individual_processing_time_ms": individual_processing_time,
                "average_time_per_image_ms": (
                    individual_processing_time / len(results) if results else 0
                ),
                "metadata": {
                    "batch_size": len(validated_paths),
                    "concurrency": config.batch_concurrency,
                    "operation_params": params,
                },
            }

            return json.dumps(batch_result, indent=2)

        except Exception as e:
            return _create_error_response(
                error=e,
                operation=f"batch_{operation}",
                context={
                    "image_paths": image_paths,
                    "question": question,
                    "object_name": object_name,
                    "length": length,
                    "stream": stream,
                },
            )
