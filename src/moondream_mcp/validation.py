"""
Validation utilities for moondream-mcp.

Provides comprehensive input validation, sanitization, and error handling
for all vision analysis operations.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .models import CaptionLength


class ValidationError(Exception):
    """Custom exception for validation errors with error codes."""

    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


def validate_image_path(image_path: str) -> str:
    """
    Validate and normalize image path (local file or URL).

    Args:
        image_path: Path to image file or URL

    Returns:
        Normalized path string

    Raises:
        ValidationError: If path is invalid
    """
    if not image_path or not image_path.strip():
        raise ValidationError("Image path cannot be empty", "EMPTY_PATH")

    image_path = image_path.strip()

    # Check if it's a URL
    if _is_url(image_path):
        return image_path

    # Treat as local file path
    try:
        normalized_path = Path(image_path).expanduser()
        return str(normalized_path)
    except Exception as e:
        raise ValidationError(f"Invalid file path: {str(e)}", "INVALID_PATH")


def validate_question(question: str) -> str:
    """
    Validate question for visual question answering.

    Args:
        question: Question text

    Returns:
        Sanitized question string

    Raises:
        ValidationError: If question is invalid
    """
    if not question or not question.strip():
        raise ValidationError("Question cannot be empty", "EMPTY_QUESTION")

    question = question.strip()

    if len(question) > 1000:
        raise ValidationError(
            f"Question too long: {len(question)} characters (max 1000)",
            "QUESTION_TOO_LONG",
        )

    return question


def validate_object_name(object_name: str) -> str:
    """
    Validate object name for detection/pointing operations.

    Args:
        object_name: Name of object to detect

    Returns:
        Sanitized object name

    Raises:
        ValidationError: If object name is invalid
    """
    if not object_name or not object_name.strip():
        raise ValidationError("Object name cannot be empty", "EMPTY_OBJECT_NAME")

    object_name = object_name.strip()

    if len(object_name) > 100:
        raise ValidationError(
            f"Object name too long: {len(object_name)} characters (max 100)",
            "OBJECT_NAME_TOO_LONG",
        )

    # Check for potentially dangerous characters
    dangerous_chars = ["<", ">", '"', "'"]
    if any(char in object_name for char in dangerous_chars):
        raise ValidationError(
            f"Object name contains invalid characters: {object_name}",
            "INVALID_OBJECT_NAME",
        )

    return object_name


def validate_caption_length(length: str) -> CaptionLength:
    """
    Validate and convert caption length parameter.

    Args:
        length: Caption length string

    Returns:
        CaptionLength enum value

    Raises:
        ValidationError: If length is invalid
    """
    try:
        return CaptionLength(length.lower())
    except ValueError:
        valid_lengths = [e.value for e in CaptionLength]
        raise ValidationError(
            f"Invalid caption length '{length}'. Valid options: {valid_lengths}",
            "INVALID_LENGTH",
        )


def validate_operation(operation: str) -> str:
    """
    Validate operation type.

    Args:
        operation: Operation name

    Returns:
        Validated operation string

    Raises:
        ValidationError: If operation is invalid
    """
    valid_operations = ["caption", "query", "detect", "point"]

    if operation not in valid_operations:
        raise ValidationError(
            f"Invalid operation '{operation}'. Valid operations: {valid_operations}",
            "INVALID_OPERATION",
        )

    return operation


def validate_image_paths_list(paths_json: str) -> List[str]:
    """
    Validate and parse JSON array of image paths.

    Args:
        paths_json: JSON string containing array of paths

    Returns:
        List of validated image paths

    Raises:
        ValidationError: If JSON is invalid or paths are invalid
    """
    if not paths_json or not paths_json.strip():
        raise ValidationError("Image paths cannot be empty", "EMPTY_PATHS")

    try:
        paths_data = json.loads(paths_json.strip())
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON format: {str(e)}", "INVALID_JSON")

    if not isinstance(paths_data, list):
        raise ValidationError("Image paths must be a JSON array", "INVALID_PATHS_TYPE")

    if len(paths_data) == 0:
        raise ValidationError("Image paths array cannot be empty", "EMPTY_PATHS_ARRAY")

    validated_paths = []
    for i, path in enumerate(paths_data):
        if not isinstance(path, str):
            raise ValidationError(
                f"Path at index {i} must be a string, got {type(path).__name__}",
                "INVALID_PATH_TYPE",
            )

        try:
            validated_path = validate_image_path(path)
            validated_paths.append(validated_path)
        except ValidationError as e:
            # Re-raise with index information
            raise ValidationError(f"Path at index {i}: {e.message}", e.error_code)

    return validated_paths


def validate_json_parameters(params_json: str) -> Dict[str, Any]:
    """
    Validate and parse JSON parameters.

    Args:
        params_json: JSON string containing parameters

    Returns:
        Dictionary of parameters

    Raises:
        ValidationError: If JSON is invalid
    """
    if not params_json or not params_json.strip():
        return {}

    try:
        params_data = json.loads(params_json.strip())
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON format: {str(e)}", "INVALID_JSON")

    if not isinstance(params_data, dict):
        raise ValidationError("Parameters must be a JSON object", "INVALID_PARAMS_TYPE")

    return params_data


def sanitize_string(
    value: Any, max_length: int = 10000, allowed_chars: Optional[str] = None
) -> str:
    """
    Sanitize and validate string input.

    Args:
        value: Input value to sanitize
        max_length: Maximum allowed length
        allowed_chars: Regex pattern for allowed characters

    Returns:
        Sanitized string

    Raises:
        ValidationError: If input is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"Expected string, got {type(value).__name__}", "INVALID_TYPE"
        )

    # Remove control characters except tab and newline
    sanitized = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", value)

    # Strip whitespace
    sanitized = sanitized.strip()

    if len(sanitized) > max_length:
        raise ValidationError(
            f"String too long: {len(sanitized)} characters (max {max_length})",
            "STRING_TOO_LONG",
        )

    return sanitized


def _is_url(path: str) -> bool:
    """
    Check if a path is a URL.

    Args:
        path: Path string to check

    Returns:
        True if path is a valid URL, False otherwise
    """
    try:
        parsed = urlparse(path)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False
