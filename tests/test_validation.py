"""
Tests for validation utilities.
"""

import json
from pathlib import Path

import pytest

from moondream_mcp.models import CaptionLength
from moondream_mcp.validation import (
    ValidationError,
    _is_url,
    sanitize_string,
    validate_caption_length,
    validate_image_path,
    validate_image_paths_list,
    validate_json_parameters,
    validate_object_name,
    validate_operation,
    validate_question,
)


class TestValidationError:
    """Test ValidationError custom exception."""

    def test_validation_error_with_default_code(self):
        """Test ValidationError with default error code."""
        error = ValidationError("Test message")
        assert error.message == "Test message"
        assert error.error_code == "VALIDATION_ERROR"
        assert str(error) == "Test message"

    def test_validation_error_with_custom_code(self):
        """Test ValidationError with custom error code."""
        error = ValidationError("Custom message", "CUSTOM_ERROR")
        assert error.message == "Custom message"
        assert error.error_code == "CUSTOM_ERROR"


class TestValidateImagePath:
    """Test image path validation."""

    def test_validate_image_path_local_file(self):
        """Test validation of local file paths."""
        # Valid local path
        result = validate_image_path("test.jpg")
        assert result == str(Path("test.jpg").expanduser())

        # Path with user expansion
        result = validate_image_path("~/test.jpg")
        assert result == str(Path("~/test.jpg").expanduser())

    def test_validate_image_path_url(self):
        """Test validation of URL paths."""
        # Valid HTTP URL
        url = "http://example.com/image.jpg"
        result = validate_image_path(url)
        assert result == url

        # Valid HTTPS URL
        url = "https://example.com/image.jpg"
        result = validate_image_path(url)
        assert result == url

    def test_validate_image_path_empty(self):
        """Test validation with empty paths."""
        with pytest.raises(ValidationError) as exc_info:
            validate_image_path("")
        assert exc_info.value.error_code == "EMPTY_PATH"

        with pytest.raises(ValidationError) as exc_info:
            validate_image_path("   ")
        assert exc_info.value.error_code == "EMPTY_PATH"

    def test_validate_image_path_invalid_url(self):
        """Test validation with invalid URLs."""
        # Test that incomplete URLs are treated as local paths (not errors)
        # because _is_url returns False for them
        result = validate_image_path("http://")
        assert result == str(Path("http://").expanduser())

        result = validate_image_path("://example.com")
        assert result == str(Path("://example.com").expanduser())

        # Test that non-URL strings are treated as local paths (not errors)
        result = validate_image_path("not-a-url")
        assert result == str(Path("not-a-url").expanduser())


class TestValidateQuestion:
    """Test question validation."""

    def test_validate_question_valid(self):
        """Test validation of valid questions."""
        question = "What is in this image?"
        result = validate_question(question)
        assert result == question

        # Question with extra whitespace
        result = validate_question("  What is this?  ")
        assert result == "What is this?"

    def test_validate_question_empty(self):
        """Test validation with empty questions."""
        with pytest.raises(ValidationError) as exc_info:
            validate_question("")
        assert exc_info.value.error_code == "EMPTY_QUESTION"

        with pytest.raises(ValidationError) as exc_info:
            validate_question("   ")
        assert exc_info.value.error_code == "EMPTY_QUESTION"

    def test_validate_question_too_long(self):
        """Test validation with overly long questions."""
        long_question = "x" * 1001
        with pytest.raises(ValidationError) as exc_info:
            validate_question(long_question)
        assert exc_info.value.error_code == "QUESTION_TOO_LONG"

    def test_validate_question_max_length(self):
        """Test validation at maximum allowed length."""
        max_question = "x" * 1000
        result = validate_question(max_question)
        assert result == max_question


class TestValidateObjectName:
    """Test object name validation."""

    def test_validate_object_name_valid(self):
        """Test validation of valid object names."""
        name = "person"
        result = validate_object_name(name)
        assert result == name

        # Name with whitespace
        result = validate_object_name("  car  ")
        assert result == "car"

    def test_validate_object_name_empty(self):
        """Test validation with empty object names."""
        with pytest.raises(ValidationError) as exc_info:
            validate_object_name("")
        assert exc_info.value.error_code == "EMPTY_OBJECT_NAME"

        with pytest.raises(ValidationError) as exc_info:
            validate_object_name("   ")
        assert exc_info.value.error_code == "EMPTY_OBJECT_NAME"

    def test_validate_object_name_too_long(self):
        """Test validation with overly long object names."""
        long_name = "x" * 101
        with pytest.raises(ValidationError) as exc_info:
            validate_object_name(long_name)
        assert exc_info.value.error_code == "OBJECT_NAME_TOO_LONG"

    def test_validate_object_name_invalid_characters(self):
        """Test validation with invalid characters."""
        invalid_names = ["person<script>", "car>alert", 'dog"test', "cat'hack"]

        for name in invalid_names:
            with pytest.raises(ValidationError) as exc_info:
                validate_object_name(name)
            assert exc_info.value.error_code == "INVALID_OBJECT_NAME"

    def test_validate_object_name_max_length(self):
        """Test validation at maximum allowed length."""
        max_name = "x" * 100
        result = validate_object_name(max_name)
        assert result == max_name


class TestValidateCaptionLength:
    """Test caption length validation."""

    def test_validate_caption_length_valid(self):
        """Test validation of valid caption lengths."""
        assert validate_caption_length("short") == CaptionLength.SHORT
        assert validate_caption_length("normal") == CaptionLength.NORMAL
        assert validate_caption_length("detailed") == CaptionLength.DETAILED

    def test_validate_caption_length_invalid(self):
        """Test validation with invalid caption lengths."""
        invalid_lengths = ["brief", "long", "medium", ""]

        for length in invalid_lengths:
            with pytest.raises(ValidationError) as exc_info:
                validate_caption_length(length)
            assert exc_info.value.error_code == "INVALID_LENGTH"


class TestValidateOperation:
    """Test operation validation."""

    def test_validate_operation_valid(self):
        """Test validation of valid operations."""
        valid_operations = ["caption", "query", "detect", "point"]

        for operation in valid_operations:
            result = validate_operation(operation)
            assert result == operation

    def test_validate_operation_invalid(self):
        """Test validation with invalid operations."""
        invalid_operations = ["analyze", "process", "generate", ""]

        for operation in invalid_operations:
            with pytest.raises(ValidationError) as exc_info:
                validate_operation(operation)
            assert exc_info.value.error_code == "INVALID_OPERATION"


class TestValidateImagePathsList:
    """Test image paths list validation."""

    def test_validate_image_paths_list_valid(self):
        """Test validation of valid image paths lists."""
        paths_json = '["image1.jpg", "image2.jpg"]'
        result = validate_image_paths_list(paths_json)
        expected = [
            str(Path("image1.jpg").expanduser()),
            str(Path("image2.jpg").expanduser()),
        ]
        assert result == expected

    def test_validate_image_paths_list_empty_string(self):
        """Test validation with empty string."""
        with pytest.raises(ValidationError) as exc_info:
            validate_image_paths_list("")
        assert exc_info.value.error_code == "EMPTY_PATHS"

        with pytest.raises(ValidationError) as exc_info:
            validate_image_paths_list("   ")
        assert exc_info.value.error_code == "EMPTY_PATHS"

    def test_validate_image_paths_list_invalid_json(self):
        """Test validation with invalid JSON."""
        with pytest.raises(ValidationError) as exc_info:
            validate_image_paths_list("invalid json")
        assert exc_info.value.error_code == "INVALID_JSON"

        with pytest.raises(ValidationError) as exc_info:
            validate_image_paths_list('["unclosed array"')
        assert exc_info.value.error_code == "INVALID_JSON"

    def test_validate_image_paths_list_not_array(self):
        """Test validation with non-array JSON."""
        with pytest.raises(ValidationError) as exc_info:
            validate_image_paths_list('"not an array"')
        assert exc_info.value.error_code == "INVALID_PATHS_TYPE"

        with pytest.raises(ValidationError) as exc_info:
            validate_image_paths_list('{"not": "array"}')
        assert exc_info.value.error_code == "INVALID_PATHS_TYPE"

    def test_validate_image_paths_list_empty_array(self):
        """Test validation with empty array."""
        with pytest.raises(ValidationError) as exc_info:
            validate_image_paths_list("[]")
        assert exc_info.value.error_code == "EMPTY_PATHS_ARRAY"

    def test_validate_image_paths_list_invalid_path_type(self):
        """Test validation with non-string paths."""
        with pytest.raises(ValidationError) as exc_info:
            validate_image_paths_list('[123, "valid.jpg"]')
        assert exc_info.value.error_code == "INVALID_PATH_TYPE"
        assert "Path at index 0" in exc_info.value.message

    def test_validate_image_paths_list_invalid_path(self):
        """Test validation with invalid individual paths."""
        with pytest.raises(ValidationError) as exc_info:
            validate_image_paths_list('["", "valid.jpg"]')
        assert exc_info.value.error_code == "EMPTY_PATH"
        assert "Path at index 0" in exc_info.value.message


class TestValidateJsonParameters:
    """Test JSON parameters validation."""

    def test_validate_json_parameters_valid(self):
        """Test validation of valid JSON parameters."""
        params_json = '{"key": "value", "number": 42}'
        result = validate_json_parameters(params_json)
        assert result == {"key": "value", "number": 42}

    def test_validate_json_parameters_empty(self):
        """Test validation with empty parameters."""
        result = validate_json_parameters("")
        assert result == {}

        result = validate_json_parameters("   ")
        assert result == {}

    def test_validate_json_parameters_invalid_json(self):
        """Test validation with invalid JSON."""
        with pytest.raises(ValidationError) as exc_info:
            validate_json_parameters("invalid json")
        assert exc_info.value.error_code == "INVALID_JSON"

    def test_validate_json_parameters_not_object(self):
        """Test validation with non-object JSON."""
        with pytest.raises(ValidationError) as exc_info:
            validate_json_parameters('"not an object"')
        assert exc_info.value.error_code == "INVALID_PARAMS_TYPE"

        with pytest.raises(ValidationError) as exc_info:
            validate_json_parameters("[1, 2, 3]")
        assert exc_info.value.error_code == "INVALID_PARAMS_TYPE"


class TestSanitizeString:
    """Test string sanitization."""

    def test_sanitize_string_valid(self):
        """Test sanitization of valid strings."""
        result = sanitize_string("normal text")
        assert result == "normal text"

        # Test whitespace trimming
        result = sanitize_string("  text with spaces  ")
        assert result == "text with spaces"

    def test_sanitize_string_invalid_type(self):
        """Test sanitization with non-string input."""
        with pytest.raises(ValidationError) as exc_info:
            sanitize_string(123)
        assert exc_info.value.error_code == "INVALID_TYPE"

    def test_sanitize_string_max_length(self):
        """Test sanitization with length limits."""
        # Within limit
        result = sanitize_string("short", max_length=10)
        assert result == "short"

        # Exceeds limit
        with pytest.raises(ValidationError) as exc_info:
            sanitize_string("very long string", max_length=5)
        assert exc_info.value.error_code == "STRING_TOO_LONG"

    def test_sanitize_string_control_characters(self):
        """Test sanitization removes control characters."""
        # Test with null bytes and control characters
        dirty_string = "text\x00with\x01control\x02chars"
        result = sanitize_string(dirty_string)
        assert result == "textwithcontrolchars"

        # Test preserving allowed whitespace (but \r gets stripped)
        text_with_whitespace = "text\twith\nwhitespace\r"
        result = sanitize_string(text_with_whitespace)
        assert result == "text\twith\nwhitespace"  # \r is stripped


class TestIsUrl:
    """Test URL detection utility."""

    def test_is_url_valid_urls(self):
        """Test detection of valid URLs."""
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "http://example.com/path",
            "https://example.com/path/to/file.jpg",
            "ftp://example.com/file.txt",
        ]

        for url in valid_urls:
            assert _is_url(url) is True

    def test_is_url_invalid_urls(self):
        """Test detection of invalid URLs."""
        invalid_urls = [
            "not-a-url",
            "file.txt",
            "/local/path",
            "example.com",  # Missing scheme
            "http://",  # Missing netloc
            "",
        ]

        for url in invalid_urls:
            assert _is_url(url) is False

    def test_is_url_edge_cases(self):
        """Test URL detection edge cases."""
        # Malformed URLs that might cause exceptions
        edge_cases = [
            "http:///",
            "://example.com",
            "http:/example.com",
        ]

        for url in edge_cases:
            # Should not raise exception, just return False
            assert _is_url(url) is False
