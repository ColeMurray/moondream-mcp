"""
Tests for vision tools utilities.
"""

import json
import time
from unittest.mock import MagicMock

import pytest

from moondream_mcp.models import (
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
from moondream_mcp.tools.utils import (
    create_batch_summary,
    create_error_response,
    format_result_as_json,
    get_error_code_for_exception,
    measure_time_ms,
    parse_image_paths,
    parse_json_parameters,
    sanitize_error_message,
    validate_caption_length,
    validate_input_parameters,
    validate_operation,
)


class TestCreateErrorResponse:
    """Test error response creation."""

    def test_create_error_response_minimal(self):
        """Test creating error response with minimal parameters."""
        result = create_error_response("TEST_ERROR", "Test error message")

        data = json.loads(result)
        assert data["success"] is False
        assert data["error_code"] == "TEST_ERROR"
        assert data["error_message"] == "Test error message"
        assert "timestamp" in data

    def test_create_error_response_with_operation(self):
        """Test creating error response with operation."""
        result = create_error_response(
            "TEST_ERROR", "Test error message", operation="caption"
        )

        data = json.loads(result)
        assert data["operation"] == "caption"

    def test_create_error_response_with_image_path(self):
        """Test creating error response with image path."""
        result = create_error_response(
            "TEST_ERROR", "Test error message", image_path="test.jpg"
        )

        data = json.loads(result)
        assert data["image_path"] == "test.jpg"

    def test_create_error_response_complete(self):
        """Test creating error response with all parameters."""
        result = create_error_response(
            "TEST_ERROR", "Test error message", operation="query", image_path="test.jpg"
        )

        data = json.loads(result)
        assert data["success"] is False
        assert data["error_code"] == "TEST_ERROR"
        assert data["error_message"] == "Test error message"
        assert data["operation"] == "query"
        assert data["image_path"] == "test.jpg"
        assert isinstance(data["timestamp"], (int, float))


class TestValidateCaptionLength:
    """Test caption length validation in utils."""

    def test_validate_caption_length_valid(self):
        """Test validation of valid caption lengths."""
        assert validate_caption_length("short") == CaptionLength.SHORT
        assert validate_caption_length("normal") == CaptionLength.NORMAL
        assert validate_caption_length("detailed") == CaptionLength.DETAILED

    def test_validate_caption_length_case_insensitive(self):
        """Test case insensitive validation."""
        assert validate_caption_length("SHORT") == CaptionLength.SHORT
        assert validate_caption_length("Normal") == CaptionLength.NORMAL
        assert validate_caption_length("DETAILED") == CaptionLength.DETAILED

    def test_validate_caption_length_invalid(self):
        """Test validation with invalid lengths."""
        with pytest.raises(ValueError, match="Invalid length"):
            validate_caption_length("invalid")

        with pytest.raises(ValueError, match="Invalid length"):
            validate_caption_length("")


class TestValidateOperation:
    """Test operation validation in utils."""

    def test_validate_operation_valid(self):
        """Test validation of valid operations."""
        valid_operations = ["caption", "query", "detect", "point"]

        for operation in valid_operations:
            result = validate_operation(operation)
            assert result == operation

    def test_validate_operation_invalid(self):
        """Test validation with invalid operations."""
        with pytest.raises(ValueError, match="Invalid operation"):
            validate_operation("invalid")

        with pytest.raises(ValueError, match="Invalid operation"):
            validate_operation("")


class TestParseJsonParameters:
    """Test JSON parameters parsing."""

    def test_parse_json_parameters_valid(self):
        """Test parsing valid JSON parameters."""
        params_json = '{"key": "value", "number": 42}'
        result = parse_json_parameters(params_json)
        assert result == {"key": "value", "number": 42}

    def test_parse_json_parameters_empty_object(self):
        """Test parsing empty JSON object."""
        result = parse_json_parameters("{}")
        assert result == {}

    def test_parse_json_parameters_invalid_json(self):
        """Test parsing invalid JSON."""
        with pytest.raises(ValueError, match="Invalid JSON parameters"):
            parse_json_parameters("invalid json")

    def test_parse_json_parameters_not_object(self):
        """Test parsing non-object JSON."""
        with pytest.raises(ValueError, match="Parameters must be a JSON object"):
            parse_json_parameters('"not an object"')

        with pytest.raises(ValueError, match="Parameters must be a JSON object"):
            parse_json_parameters("[1, 2, 3]")


class TestParseImagePaths:
    """Test image paths parsing."""

    def test_parse_image_paths_valid(self):
        """Test parsing valid image paths."""
        paths_json = '["image1.jpg", "image2.jpg"]'
        result = parse_image_paths(paths_json)
        assert result == ["image1.jpg", "image2.jpg"]

    def test_parse_image_paths_single_image(self):
        """Test parsing single image path."""
        paths_json = '["single.jpg"]'
        result = parse_image_paths(paths_json)
        assert result == ["single.jpg"]

    def test_parse_image_paths_invalid_json(self):
        """Test parsing invalid JSON."""
        with pytest.raises(ValueError, match="image_paths must be valid JSON array"):
            parse_image_paths("invalid json")

    def test_parse_image_paths_not_array(self):
        """Test parsing non-array JSON."""
        with pytest.raises(ValueError, match="image_paths must be a JSON array"):
            parse_image_paths('"not an array"')

    def test_parse_image_paths_empty_array(self):
        """Test parsing empty array."""
        with pytest.raises(ValueError, match="image_paths cannot be empty"):
            parse_image_paths("[]")

    def test_parse_image_paths_too_many(self):
        """Test parsing too many image paths."""
        many_paths = json.dumps([f"image{i}.jpg" for i in range(11)])
        with pytest.raises(ValueError, match="Cannot process more than 10 images"):
            parse_image_paths(many_paths)

    def test_parse_image_paths_max_allowed(self):
        """Test parsing maximum allowed image paths."""
        max_paths = json.dumps([f"image{i}.jpg" for i in range(10)])
        result = parse_image_paths(max_paths)
        assert len(result) == 10


class TestFormatResultAsJson:
    """Test result formatting."""

    def test_format_caption_result(self):
        """Test formatting caption result."""
        result = CaptionResult(
            success=True,
            caption="A test image",
            length=CaptionLength.NORMAL,
            processing_time_ms=100.0,
            metadata={"test": "data"},
        )

        json_str = format_result_as_json(result)
        data = json.loads(json_str)

        assert data["success"] is True
        assert data["caption"] == "A test image"
        assert data["length"] == "normal"

    def test_format_query_result(self):
        """Test formatting query result."""
        result = QueryResult(
            success=True,
            answer="Test answer",
            question="Test question?",
            processing_time_ms=150.0,
            metadata={"test": "data"},
        )

        json_str = format_result_as_json(result)
        data = json.loads(json_str)

        assert data["success"] is True
        assert data["answer"] == "Test answer"
        assert data["question"] == "Test question?"

    def test_format_detection_result(self):
        """Test formatting detection result."""
        detected_object = DetectedObject(
            name="person",
            confidence=0.95,
            bounding_box=BoundingBox(x=0.1, y=0.2, width=0.3, height=0.4),
        )

        result = DetectionResult(
            success=True,
            objects=[detected_object],
            object_name="person",
            total_found=1,
            processing_time_ms=200.0,
            metadata={"test": "data"},
        )

        json_str = format_result_as_json(result)
        data = json.loads(json_str)

        assert data["success"] is True
        assert data["total_found"] == 1
        assert len(data["objects"]) == 1

    def test_format_pointing_result(self):
        """Test formatting pointing result."""
        pointed_object = PointedObject(
            name="car", confidence=0.88, point=Point(x=0.5, y=0.3)
        )

        result = PointingResult(
            success=True,
            points=[pointed_object],
            object_name="car",
            total_found=1,
            processing_time_ms=180.0,
            metadata={"test": "data"},
        )

        json_str = format_result_as_json(result)
        data = json.loads(json_str)

        assert data["success"] is True
        assert data["total_found"] == 1
        assert len(data["points"]) == 1


class TestCreateBatchSummary:
    """Test batch summary creation."""

    def test_create_batch_summary_all_successful(self):
        """Test creating summary with all successful results."""
        results = [
            {"success": True, "caption": "Image 1"},
            {"success": True, "caption": "Image 2"},
        ]

        summary = create_batch_summary(results, "caption", 500.0)

        assert summary["operation"] == "caption"
        assert summary["total_processed"] == 2
        assert summary["total_successful"] == 2
        assert summary["total_failed"] == 0
        assert summary["total_processing_time_ms"] == 500.0
        assert summary["average_time_per_image_ms"] == 250.0
        assert summary["results"] == results

    def test_create_batch_summary_mixed_results(self):
        """Test creating summary with mixed results."""
        results = [
            {"success": True, "caption": "Image 1"},
            {"success": False, "error": "Failed"},
            {"success": True, "caption": "Image 3"},
        ]

        summary = create_batch_summary(results, "caption", 750.0)

        assert summary["total_processed"] == 3
        assert summary["total_successful"] == 2
        assert summary["total_failed"] == 1
        assert summary["average_time_per_image_ms"] == 250.0

    def test_create_batch_summary_all_failed(self):
        """Test creating summary with all failed results."""
        results = [
            {"success": False, "error": "Failed 1"},
            {"success": False, "error": "Failed 2"},
        ]

        summary = create_batch_summary(results, "query", 300.0)

        assert summary["total_successful"] == 0
        assert summary["total_failed"] == 2

    def test_create_batch_summary_empty_results(self):
        """Test creating summary with empty results."""
        summary = create_batch_summary([], "caption", 0.0)

        assert summary["total_processed"] == 0
        assert summary["total_successful"] == 0
        assert summary["total_failed"] == 0
        assert summary["average_time_per_image_ms"] == 0


class TestSanitizeErrorMessage:
    """Test error message sanitization."""

    def test_sanitize_error_message_simple(self):
        """Test sanitizing simple error message."""
        error = ValueError("Simple error message")
        result = sanitize_error_message(error)
        assert result == "Simple error message"

    def test_sanitize_error_message_with_sensitive_info(self):
        """Test sanitizing error message with sensitive information."""
        error = ValueError("Error with /sensitive/path/file.txt")
        result = sanitize_error_message(error)
        # Should still contain the message but could be sanitized
        assert "Error with" in result

    def test_sanitize_error_message_empty(self):
        """Test sanitizing empty error message."""
        error = ValueError("")
        result = sanitize_error_message(error)
        # Empty error messages return empty string, not "Unknown error"
        assert result == ""

    def test_sanitize_error_message_none(self):
        """Test sanitizing None error message."""
        error = ValueError()
        result = sanitize_error_message(error)
        # Should handle cases where str(error) might be empty
        assert isinstance(result, str)


class TestValidateInputParameters:
    """Test input parameter validation."""

    def test_validate_input_parameters_image_path_only(self):
        """Test validation with only image path."""
        # Should not raise exception
        validate_input_parameters("test.jpg")

    def test_validate_input_parameters_empty_image_path(self):
        """Test validation with empty image path."""
        with pytest.raises(ValueError, match="image_path cannot be empty"):
            validate_input_parameters("")

    def test_validate_input_parameters_with_operation(self):
        """Test validation with operation."""
        validate_input_parameters("test.jpg", operation="caption")

    def test_validate_input_parameters_invalid_operation(self):
        """Test validation with invalid operation."""
        with pytest.raises(ValueError, match="Invalid operation"):
            validate_input_parameters("test.jpg", operation="invalid")

    def test_validate_input_parameters_with_question(self):
        """Test validation with question."""
        validate_input_parameters("test.jpg", question="What is this?")

    def test_validate_input_parameters_empty_question(self):
        """Test validation with empty question."""
        with pytest.raises(ValueError, match="question cannot be empty"):
            validate_input_parameters("test.jpg", question="")

    def test_validate_input_parameters_with_object_name(self):
        """Test validation with object name."""
        validate_input_parameters("test.jpg", object_name="person")

    def test_validate_input_parameters_empty_object_name(self):
        """Test validation with empty object name."""
        with pytest.raises(ValueError, match="object_name cannot be empty"):
            validate_input_parameters("test.jpg", object_name="")


class TestGetErrorCodeForException:
    """Test error code determination."""

    def test_get_error_code_value_error(self):
        """Test error code for ValueError."""
        error = ValueError("Test error")
        code = get_error_code_for_exception(error)
        assert code == "INVALID_REQUEST"  # Actual error code used

    def test_get_error_code_file_not_found(self):
        """Test error code for FileNotFoundError."""
        error = FileNotFoundError("File not found")
        code = get_error_code_for_exception(error)
        assert code == "FILE_NOT_FOUND"

    def test_get_error_code_permission_error(self):
        """Test error code for PermissionError."""
        error = PermissionError("Permission denied")
        code = get_error_code_for_exception(error)
        assert code == "PERMISSION_DENIED"  # Actual error code used

    def test_get_error_code_generic_exception(self):
        """Test error code for generic exception."""
        error = RuntimeError("Runtime error")
        code = get_error_code_for_exception(error)
        assert code == "UNKNOWN_ERROR"


class TestMeasureTimeMs:
    """Test time measurement utility."""

    def test_measure_time_ms(self):
        """Test measuring time in milliseconds."""
        start_time = time.time()
        # Simulate some processing time
        time.sleep(0.01)  # 10ms

        elapsed_ms = measure_time_ms(start_time)

        # Should be approximately 10ms, but allow for some variance
        assert 5.0 <= elapsed_ms <= 50.0  # Allow for system variance

    def test_measure_time_ms_immediate(self):
        """Test measuring time with immediate call."""
        start_time = time.time()
        elapsed_ms = measure_time_ms(start_time)

        # Should be very small but positive
        assert 0.0 <= elapsed_ms <= 10.0
