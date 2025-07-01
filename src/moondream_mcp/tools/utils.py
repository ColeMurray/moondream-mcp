"""
Utility functions for vision analysis tools.
"""

import json
import time
from typing import Any, Dict, List, Optional, Union

from moondream_mcp.models import (
    CaptionLength,
    CaptionResult,
    DetectionResult,
    PointingResult,
    QueryResult,
)


def create_error_response(
    error_code: str,
    error_message: str,
    operation: Optional[str] = None,
    image_path: Optional[str] = None,
) -> str:
    """
    Create a standardized error response.

    Args:
        error_code: Error code identifier
        error_message: Human-readable error message
        operation: Optional operation that failed
        image_path: Optional image path that caused the error

    Returns:
        JSON string with error details
    """
    error_response = {
        "success": False,
        "error_code": error_code,
        "error_message": error_message,
        "timestamp": time.time(),
    }

    if operation:
        error_response["operation"] = operation

    if image_path:
        error_response["image_path"] = image_path

    return json.dumps(error_response, indent=2)


def validate_caption_length(length: str) -> CaptionLength:
    """
    Validate and convert caption length parameter.

    Args:
        length: Length parameter as string

    Returns:
        CaptionLength enum value

    Raises:
        ValueError: If length is invalid
    """
    length_lower = length.lower()

    if length_lower == "short":
        return CaptionLength.SHORT
    elif length_lower == "normal":
        return CaptionLength.NORMAL
    elif length_lower == "detailed":
        return CaptionLength.DETAILED
    else:
        raise ValueError(
            f"Invalid length '{length}'. Must be 'short', 'normal', or 'detailed'"
        )


def validate_operation(operation: str) -> str:
    """
    Validate operation parameter for analyze_image tool.

    Args:
        operation: Operation to validate

    Returns:
        Validated operation string

    Raises:
        ValueError: If operation is invalid
    """
    valid_operations = {"caption", "query", "detect", "point"}

    if operation not in valid_operations:
        raise ValueError(
            f"Invalid operation '{operation}'. Must be one of: {', '.join(valid_operations)}"
        )

    return operation


def parse_json_parameters(parameters: str) -> Dict[str, Any]:
    """
    Parse and validate JSON parameters.

    Args:
        parameters: JSON string to parse

    Returns:
        Parsed parameters dictionary

    Raises:
        ValueError: If JSON is invalid
    """
    try:
        result = json.loads(parameters)
        if not isinstance(result, dict):
            raise ValueError("Parameters must be a JSON object")
        return result
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON parameters: {e}")


def parse_image_paths(image_paths_json: str) -> List[str]:
    """
    Parse and validate image paths JSON array.

    Args:
        image_paths_json: JSON array string of image paths

    Returns:
        List of image paths

    Raises:
        ValueError: If JSON is invalid or not an array
    """
    try:
        paths = json.loads(image_paths_json)
    except json.JSONDecodeError:
        raise ValueError("image_paths must be valid JSON array")

    if not isinstance(paths, list):
        raise ValueError("image_paths must be a JSON array")

    if not paths:
        raise ValueError("image_paths cannot be empty")

    if len(paths) > 10:  # Reasonable limit for batch processing
        raise ValueError("Cannot process more than 10 images at once")

    return paths


def format_result_as_json(
    result: Union[CaptionResult, QueryResult, DetectionResult, PointingResult],
) -> str:
    """
    Format analysis result as JSON string.

    Args:
        result: Analysis result object

    Returns:
        JSON string representation
    """
    return result.model_dump_json(indent=2)


def create_batch_summary(
    results: List[Dict[str, Any]],
    operation: str,
    total_time_ms: float,
) -> Dict[str, Any]:
    """
    Create summary for batch processing results.

    Args:
        results: List of individual results
        operation: Operation performed
        total_time_ms: Total processing time in milliseconds

    Returns:
        Summary dictionary
    """
    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("success", False)]

    return {
        "operation": operation,
        "total_processed": len(results),
        "total_successful": len(successful),
        "total_failed": len(failed),
        "total_processing_time_ms": total_time_ms,
        "average_time_per_image_ms": total_time_ms / len(results) if results else 0,
        "results": results,
    }


def sanitize_error_message(error: Exception) -> str:
    """
    Sanitize error message to avoid exposing sensitive information.

    Args:
        error: Exception to sanitize

    Returns:
        Sanitized error message
    """
    error_str = str(error)

    # Remove potential file paths
    import re

    error_str = re.sub(r"/[^\s]*", "[PATH]", error_str)
    error_str = re.sub(r"C:\\[^\s]*", "[PATH]", error_str)

    # Remove potential URLs
    error_str = re.sub(r"https?://[^\s]+", "[URL]", error_str)

    # Limit length
    if len(error_str) > 200:
        error_str = error_str[:197] + "..."

    return error_str


def validate_input_parameters(
    image_path: str,
    operation: Optional[str] = None,
    question: Optional[str] = None,
    object_name: Optional[str] = None,
) -> None:
    """
    Validate common input parameters.

    Args:
        image_path: Path to image file
        operation: Optional operation name
        question: Optional question for VQA
        object_name: Optional object name for detection/pointing

    Raises:
        ValueError: If any parameter is invalid
    """
    if not image_path or not image_path.strip():
        raise ValueError("image_path cannot be empty")

    if question is not None and not question.strip():
        raise ValueError("question cannot be empty")

    if object_name is not None and not object_name.strip():
        raise ValueError("object_name cannot be empty")

    if operation is not None:
        validate_operation(operation)


def get_error_code_for_exception(error: Exception) -> str:
    """
    Get appropriate error code for exception type.

    Args:
        error: Exception to categorize

    Returns:
        Error code string
    """
    from moondream_mcp.moondream import (
        ImageProcessingError,
        InferenceError,
        ModelLoadError,
    )

    if isinstance(error, ModelLoadError):
        return "MODEL_LOAD_ERROR"
    elif isinstance(error, ImageProcessingError):
        return "IMAGE_PROCESSING_ERROR"
    elif isinstance(error, InferenceError):
        return "INFERENCE_ERROR"
    elif isinstance(error, ValueError):
        return "INVALID_REQUEST"
    elif isinstance(error, FileNotFoundError):
        return "FILE_NOT_FOUND"
    elif isinstance(error, PermissionError):
        return "PERMISSION_DENIED"
    else:
        return "UNKNOWN_ERROR"


def measure_time_ms(start_time: float) -> float:
    """
    Calculate elapsed time in milliseconds.

    Args:
        start_time: Start time from time.time()

    Returns:
        Elapsed time in milliseconds
    """
    return (time.time() - start_time) * 1000
