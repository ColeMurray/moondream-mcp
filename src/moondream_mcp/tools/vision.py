"""
Vision analysis tools for Moondream MCP Server.

Provides FastMCP tools for image captioning, visual question answering,
object detection, and visual pointing.
"""

import json
from typing import TYPE_CHECKING, List

from ..models import CaptionLength
from ..moondream import ImageProcessingError, ModelLoadError, MoondreamError

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from ..moondream import MoondreamClient


def register_vision_tools(mcp: "FastMCP", moondream_client: "MoondreamClient") -> None:
    """Register vision analysis MCP tools."""

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
            # Validate length parameter
            if length not in ("short", "normal", "detailed"):
                raise ValueError("length must be 'short', 'normal', or 'detailed'")

            caption_length = CaptionLength(length)
            result = await moondream_client.caption_image(
                image_path=image_path,
                length=caption_length,
                stream=stream,
            )

            return json.dumps(result.dict(), indent=2)

        except (ModelLoadError, ImageProcessingError) as e:
            return json.dumps(
                {
                    "success": False,
                    "error_message": e.message,
                    "error_code": e.error_code,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "error_message": str(e),
                    "error_code": "INVALID_REQUEST",
                },
                indent=2,
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
            if not image_path.strip():
                raise ValueError("image_path cannot be empty")
            if not question.strip():
                raise ValueError("question cannot be empty")

            result = await moondream_client.query_image(
                image_path=image_path,
                question=question,
            )

            return json.dumps(result.dict(), indent=2)

        except (ModelLoadError, ImageProcessingError) as e:
            return json.dumps(
                {
                    "success": False,
                    "error_message": e.message,
                    "error_code": e.error_code,
                    "question": question,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "error_message": str(e),
                    "error_code": "INVALID_REQUEST",
                    "question": question,
                },
                indent=2,
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
            if not image_path.strip():
                raise ValueError("image_path cannot be empty")
            if not object_name.strip():
                raise ValueError("object_name cannot be empty")

            result = await moondream_client.detect_objects(
                image_path=image_path,
                object_name=object_name,
            )

            return json.dumps(result.dict(), indent=2)

        except (ModelLoadError, ImageProcessingError) as e:
            return json.dumps(
                {
                    "success": False,
                    "error_message": e.message,
                    "error_code": e.error_code,
                    "object_name": object_name,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "error_message": str(e),
                    "error_code": "INVALID_REQUEST",
                    "object_name": object_name,
                },
                indent=2,
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
            if not image_path.strip():
                raise ValueError("image_path cannot be empty")
            if not object_name.strip():
                raise ValueError("object_name cannot be empty")

            result = await moondream_client.point_objects(
                image_path=image_path,
                object_name=object_name,
            )

            return json.dumps(result.dict(), indent=2)

        except (ModelLoadError, ImageProcessingError) as e:
            return json.dumps(
                {
                    "success": False,
                    "error_message": e.message,
                    "error_code": e.error_code,
                    "object_name": object_name,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "error_message": str(e),
                    "error_code": "INVALID_REQUEST",
                    "object_name": object_name,
                },
                indent=2,
            )

    @mcp.tool()
    async def analyze_image(
        image_path: str,
        operation: str,
        parameters: str = "{}",
    ) -> str:
        """
        Multi-purpose image analysis tool.

        Args:
            image_path: Path to image file (local path or URL)
            operation: Operation to perform ('caption', 'query', 'detect', 'point')
            parameters: JSON string with operation-specific parameters

        Returns:
            JSON string with analysis results
        """
        try:
            if not image_path.strip():
                raise ValueError("image_path cannot be empty")
            if operation not in ("caption", "query", "detect", "point"):
                raise ValueError("operation must be 'caption', 'query', 'detect', or 'point'")

            # Parse parameters
            try:
                params = json.loads(parameters) if parameters.strip() else {}
            except json.JSONDecodeError:
                raise ValueError("parameters must be valid JSON")

            # Route to appropriate method
            if operation == "caption":
                length = params.get("length", "normal")
                stream = params.get("stream", False)
                result = await moondream_client.caption_image(
                    image_path=image_path,
                    length=CaptionLength(length),
                    stream=stream,
                )

            elif operation == "query":
                question = params.get("question")
                if not question:
                    raise ValueError("question parameter is required for query operation")
                result = await moondream_client.query_image(
                    image_path=image_path,
                    question=question,
                )

            elif operation == "detect":
                object_name = params.get("object_name")
                if not object_name:
                    raise ValueError("object_name parameter is required for detect operation")
                result = await moondream_client.detect_objects(
                    image_path=image_path,
                    object_name=object_name,
                )

            elif operation == "point":
                object_name = params.get("object_name")
                if not object_name:
                    raise ValueError("object_name parameter is required for point operation")
                result = await moondream_client.point_objects(
                    image_path=image_path,
                    object_name=object_name,
                )

            return json.dumps(result.dict(), indent=2)

        except (ModelLoadError, ImageProcessingError) as e:
            return json.dumps(
                {
                    "success": False,
                    "error_message": e.message,
                    "error_code": e.error_code,
                    "operation": operation,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "error_message": str(e),
                    "error_code": "INVALID_REQUEST",
                    "operation": operation,
                },
                indent=2,
            )

    @mcp.tool()
    async def batch_analyze_images(
        image_paths: str,
        operation: str,
        parameters: str = "{}",
    ) -> str:
        """
        Analyze multiple images in batch.

        Args:
            image_paths: JSON array of image paths (local paths or URLs)
            operation: Operation to perform on all images ('caption', 'query', 'detect', 'point')
            parameters: JSON string with operation-specific parameters

        Returns:
            JSON string with batch analysis results
        """
        try:
            # Parse image paths
            try:
                paths = json.loads(image_paths)
                if not isinstance(paths, list):
                    raise ValueError("image_paths must be a JSON array")
                if len(paths) == 0:
                    raise ValueError("image_paths cannot be empty")
                if len(paths) > 10:
                    raise ValueError("Cannot process more than 10 images at once")
            except json.JSONDecodeError:
                raise ValueError("image_paths must be valid JSON array")

            # Parse parameters
            try:
                params = json.loads(parameters) if parameters.strip() else {}
            except json.JSONDecodeError:
                raise ValueError("parameters must be valid JSON")

            # Validate operation
            if operation not in ("caption", "query", "detect", "point"):
                raise ValueError("operation must be 'caption', 'query', 'detect', or 'point'")

            # Process each image
            results = []
            total_processing_time = 0.0
            successful_count = 0
            failed_count = 0

            for image_path in paths:
                try:
                    # Route to appropriate method
                    if operation == "caption":
                        length = params.get("length", "normal")
                        stream = params.get("stream", False)
                        result = await moondream_client.caption_image(
                            image_path=image_path,
                            length=CaptionLength(length),
                            stream=stream,
                        )

                    elif operation == "query":
                        question = params.get("question")
                        if not question:
                            raise ValueError("question parameter is required for query operation")
                        result = await moondream_client.query_image(
                            image_path=image_path,
                            question=question,
                        )

                    elif operation == "detect":
                        object_name = params.get("object_name")
                        if not object_name:
                            raise ValueError("object_name parameter is required for detect operation")
                        result = await moondream_client.detect_objects(
                            image_path=image_path,
                            object_name=object_name,
                        )

                    elif operation == "point":
                        object_name = params.get("object_name")
                        if not object_name:
                            raise ValueError("object_name parameter is required for point operation")
                        result = await moondream_client.point_objects(
                            image_path=image_path,
                            object_name=object_name,
                        )

                    results.append(result.dict())
                    if result.success:
                        successful_count += 1
                    else:
                        failed_count += 1
                    
                    if result.processing_time_ms:
                        total_processing_time += result.processing_time_ms

                except Exception as e:
                    error_result = {
                        "success": False,
                        "error_message": str(e),
                        "metadata": {"image_path": image_path},
                    }
                    results.append(error_result)
                    failed_count += 1

            # Create batch result
            batch_result = {
                "results": results,
                "total_processed": len(paths),
                "total_successful": successful_count,
                "total_failed": failed_count,
                "total_processing_time_ms": total_processing_time,
                "operation": operation,
                "parameters": params,
            }

            return json.dumps(batch_result, indent=2)

        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "error_message": str(e),
                    "error_code": "INVALID_REQUEST",
                    "operation": operation,
                },
                indent=2,
            ) 