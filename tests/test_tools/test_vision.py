"""
Tests for vision analysis tools.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from moondream_mcp.models import (
    CaptionLength,
    CaptionResult,
    DetectionResult,
    PointingResult,
    QueryResult,
)
from moondream_mcp.moondream import ImageProcessingError, ModelLoadError
from moondream_mcp.tools.vision import register_vision_tools


class TestVisionTools:
    """Test vision analysis tools."""

    @pytest.fixture
    def mock_mcp(self) -> MagicMock:
        """Create a mock FastMCP instance."""
        mock = MagicMock()
        # Mock the tool decorator to capture registered functions
        mock_decorator = MagicMock()
        mock.tool.return_value = mock_decorator
        return mock

    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        """Create mock MoondreamClient."""
        return AsyncMock()

    @pytest.fixture
    def sample_caption_result(self) -> CaptionResult:
        """Create sample caption result."""
        return CaptionResult(
            success=True,
            caption="A red square on a white background",
            length=CaptionLength.NORMAL,
            processing_time_ms=150.5,
            metadata={"image_path": "test.jpg", "device": "cpu"},
        )

    @pytest.fixture
    def sample_query_result(self) -> QueryResult:
        """Create sample query result."""
        return QueryResult(
            success=True,
            answer="Yes, there are 3 people in the image",
            question="How many people are in this image?",
            processing_time_ms=200.0,
            metadata={"image_path": "test.jpg", "device": "cpu"},
        )

    def test_register_vision_tools(
        self, mock_mcp: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Test that all vision tools are registered correctly."""
        register_vision_tools(mock_mcp, mock_client)

        # Verify that tool decorator was called for each tool
        assert mock_mcp.tool.call_count == 6  # 6 tools total

        # Get the registered tool functions from the decorator calls
        mock_decorator = mock_mcp.tool.return_value
        decorator_calls = mock_decorator.call_args_list
        registered_functions = [call[0][0] for call in decorator_calls if call[0]]

        # Verify all expected tools are registered
        tool_names = [
            func.__name__ for func in registered_functions if hasattr(func, "__name__")
        ]
        expected_tools = [
            "caption_image",
            "query_image",
            "detect_objects",
            "point_objects",
            "analyze_image",
            "batch_analyze_images",
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Tool {expected_tool} not found"

    def _get_registered_function(self, mock_mcp: MagicMock, function_name: str):
        """Helper method to get a registered function by name."""
        mock_decorator = mock_mcp.tool.return_value
        decorator_calls = mock_decorator.call_args_list

        for call in decorator_calls:
            if call[0] and hasattr(call[0][0], "__name__"):
                func_name = call[0][0].__name__
                # Be more specific about matching to avoid conflicts
                if function_name == "analyze" and func_name == "analyze_image":
                    return call[0][0]
                elif function_name == "batch" and func_name == "batch_analyze_images":
                    return call[0][0]
                elif function_name in func_name and function_name not in [
                    "analyze",
                    "batch",
                ]:
                    return call[0][0]
        return None

    @pytest.mark.asyncio
    async def test_caption_image_success(
        self,
        mock_mcp: MagicMock,
        mock_client: AsyncMock,
        sample_caption_result: CaptionResult,
    ) -> None:
        """Test successful image captioning."""
        mock_client.caption_image.return_value = sample_caption_result

        # Register tools to get the actual function
        register_vision_tools(mock_mcp, mock_client)

        # Get the caption_image function
        caption_func = self._get_registered_function(mock_mcp, "caption")
        assert caption_func is not None, "caption_image function not found"

        # Test the function
        result = await caption_func("test.jpg", "detailed", False)

        # Verify the result
        result_data = json.loads(result)
        assert result_data["success"] is True
        assert result_data["caption"] == "A red square on a white background"
        assert result_data["length"] == "normal"

        # Verify client was called correctly
        mock_client.caption_image.assert_called_once_with(
            image_path="test.jpg", length=CaptionLength.DETAILED, stream=False
        )

    @pytest.mark.asyncio
    async def test_caption_image_invalid_length(
        self, mock_mcp: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Test caption_image with invalid length parameter."""
        register_vision_tools(mock_mcp, mock_client)

        # Get the caption_image function
        caption_func = self._get_registered_function(mock_mcp, "caption")

        result = await caption_func("test.jpg", "invalid", False)
        result_data = json.loads(result)

        assert result_data["success"] is False
        assert "Invalid caption length" in result_data["error_message"]
        assert result_data["error_code"] == "INVALID_LENGTH"

    @pytest.mark.asyncio
    async def test_caption_image_model_error(
        self, mock_mcp: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Test caption_image with model loading error."""
        mock_client.caption_image.side_effect = ModelLoadError("Model failed to load")

        register_vision_tools(mock_mcp, mock_client)

        # Get the caption_image function
        caption_func = self._get_registered_function(mock_mcp, "caption")

        result = await caption_func("test.jpg", "normal", False)

        result_data = json.loads(result)
        assert result_data["success"] is False
        assert result_data["error_message"] == "Model failed to load"
        assert result_data["error_code"] == "PROCESSING_ERROR"

    @pytest.mark.asyncio
    async def test_query_image_success(
        self,
        mock_mcp: MagicMock,
        mock_client: AsyncMock,
        sample_query_result: QueryResult,
    ) -> None:
        """Test successful visual question answering."""
        mock_client.query_image.return_value = sample_query_result

        register_vision_tools(mock_mcp, mock_client)

        # Get the query_image function
        query_func = self._get_registered_function(mock_mcp, "query")

        result = await query_func("test.jpg", "How many people?")

        result_data = json.loads(result)
        assert result_data["success"] is True
        assert result_data["answer"] == "Yes, there are 3 people in the image"
        assert result_data["question"] == "How many people are in this image?"

    @pytest.mark.asyncio
    async def test_query_image_empty_inputs(
        self, mock_mcp: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Test query_image with empty inputs."""
        register_vision_tools(mock_mcp, mock_client)

        # Get the query_image function
        query_func = self._get_registered_function(mock_mcp, "query")

        # Test empty image path
        result = await query_func("", "What is this?")
        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "Image path cannot be empty" in result_data["error_message"]
        assert result_data["error_code"] == "EMPTY_PATH"

        # Test empty question
        result = await query_func("test.jpg", "")
        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "Question cannot be empty" in result_data["error_message"]
        assert result_data["error_code"] == "EMPTY_QUESTION"

    @pytest.mark.asyncio
    async def test_detect_objects_success(
        self, mock_mcp: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Test successful object detection."""
        from moondream_mcp.models import BoundingBox, DetectedObject

        detection_result = DetectionResult(
            success=True,
            objects=[
                DetectedObject(
                    name="person",
                    confidence=0.95,
                    bounding_box=BoundingBox(x=0.1, y=0.2, width=0.3, height=0.6),
                )
            ],
            object_name="person",
            total_found=1,
            processing_time_ms=180.0,
            metadata={"image_path": "test.jpg"},
        )

        mock_client.detect_objects.return_value = detection_result

        register_vision_tools(mock_mcp, mock_client)

        # Get the detect_objects function
        detect_func = self._get_registered_function(mock_mcp, "detect")

        result = await detect_func("test.jpg", "person")

        result_data = json.loads(result)
        assert result_data["success"] is True
        assert result_data["object_name"] == "person"
        assert result_data["total_found"] == 1
        assert len(result_data["objects"]) == 1
        assert result_data["objects"][0]["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_point_objects_success(
        self, mock_mcp: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Test successful visual pointing."""
        from moondream_mcp.models import Point, PointedObject

        pointing_result = PointingResult(
            success=True,
            points=[
                PointedObject(name="car", confidence=0.88, point=Point(x=0.5, y=0.3))
            ],
            object_name="car",
            total_found=1,
            processing_time_ms=160.0,
            metadata={"image_path": "test.jpg"},
        )

        mock_client.point_objects.return_value = pointing_result

        register_vision_tools(mock_mcp, mock_client)

        # Get the point_objects function
        point_func = self._get_registered_function(mock_mcp, "point")

        result = await point_func("test.jpg", "car")

        result_data = json.loads(result)
        assert result_data["success"] is True
        assert result_data["object_name"] == "car"
        assert result_data["total_found"] == 1
        assert len(result_data["points"]) == 1
        assert result_data["points"][0]["point"]["x"] == 0.5

    @pytest.mark.asyncio
    async def test_analyze_image_caption(
        self, mock_mcp: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Test analyze_image with caption operation using typed parameters."""
        # Mock successful caption response
        mock_client.caption_image.return_value = CaptionResult(
            success=True,
            caption="A beautiful sunset",
            processing_time_ms=150.0,
            metadata={"image_path": "test.jpg"},
        )

        register_vision_tools(mock_mcp, mock_client)

        # Get the analyze_image function
        analyze_func = self._get_registered_function(mock_mcp, "analyze")

        # Test with typed parameters instead of JSON
        result = await analyze_func(
            image_path="test.jpg", operation="caption", length="normal", stream=False
        )

        result_data = json.loads(result)
        assert result_data["success"] is True
        assert result_data["caption"] == "A beautiful sunset"

        # Verify the client was called with correct parameters
        mock_client.caption_image.assert_called_once_with(
            image_path="test.jpg",
            length="normal",
            stream=False,
        )

    @pytest.mark.asyncio
    async def test_analyze_image_invalid_operation(
        self, mock_mcp: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Test analyze_image with invalid operation."""
        register_vision_tools(mock_mcp, mock_client)

        # Get the analyze_image function
        analyze_func = self._get_registered_function(mock_mcp, "analyze")

        result = await analyze_func("test.jpg", "invalid_op", "", "", "normal", False)
        result_data = json.loads(result)

        assert result_data["success"] is False
        assert "Invalid operation" in result_data["error_message"]
        assert result_data["error_code"] == "INVALID_OPERATION"

    @pytest.mark.asyncio
    async def test_analyze_image_missing_required_params(
        self, mock_mcp: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Test analyze_image with missing required parameters for operations."""
        register_vision_tools(mock_mcp, mock_client)

        # Get the analyze_image function
        analyze_func = self._get_registered_function(mock_mcp, "analyze")

        # Test query operation without question
        result = await analyze_func(
            image_path="test.jpg",
            operation="query"
            # Missing question parameter
        )
        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "question parameter is required" in result_data["error_message"]
        assert result_data["error_code"] == "MISSING_QUESTION"

        # Test detect operation without object_name
        result = await analyze_func(
            image_path="test.jpg",
            operation="detect"
            # Missing object_name parameter
        )
        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "object_name parameter is required" in result_data["error_message"]
        assert result_data["error_code"] == "MISSING_OBJECT_NAME"

    @pytest.mark.asyncio
    async def test_batch_analyze_images_success(
        self,
        mock_mcp: MagicMock,
        mock_client: AsyncMock,
        sample_caption_result: CaptionResult,
    ) -> None:
        """Test successful batch image analysis with typed parameters."""
        mock_client.caption_image.return_value = sample_caption_result

        register_vision_tools(mock_mcp, mock_client)

        # Get the batch_analyze_images function
        batch_func = self._get_registered_function(mock_mcp, "batch")

        image_paths = json.dumps(["test1.jpg", "test2.jpg"])

        # Use typed parameters instead of JSON
        result = await batch_func(
            image_paths=image_paths, operation="caption", length="normal"
        )

        result_data = json.loads(result)
        assert result_data["total_processed"] == 2
        assert result_data["successful_count"] == 2  # Updated field name
        assert result_data["failed_count"] == 0  # Updated field name
        assert len(result_data["results"]) == 2

    @pytest.mark.asyncio
    async def test_batch_analyze_images_invalid_paths(
        self, mock_mcp: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Test batch_analyze_images with invalid paths JSON."""
        register_vision_tools(mock_mcp, mock_client)

        # Get the batch_analyze_images function
        batch_func = self._get_registered_function(mock_mcp, "batch")

        # Test invalid JSON
        result = await batch_func(image_paths="invalid json", operation="caption")
        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "Invalid JSON format" in result_data["error_message"]
        assert result_data["error_code"] == "INVALID_JSON"

        # Test non-array
        result = await batch_func(image_paths='"not an array"', operation="caption")
        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "Image paths must be a JSON array" in result_data["error_message"]
        assert result_data["error_code"] == "INVALID_PATHS_TYPE"

        # Test empty array
        result = await batch_func(image_paths="[]", operation="caption")
        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "Image paths array cannot be empty" in result_data["error_message"]
        assert result_data["error_code"] == "EMPTY_PATHS_ARRAY"

    @pytest.mark.asyncio
    async def test_batch_analyze_images_mixed_results(
        self, mock_mcp: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Test batch analysis with mixed success/failure results using typed parameters."""

        # Mock client to succeed for first image, fail for second
        def mock_caption_side_effect(image_path: str, **kwargs):
            if "test1.jpg" in image_path:
                return CaptionResult(
                    success=True,
                    caption="Success",
                    processing_time_ms=100.0,
                    metadata={"image_path": image_path},
                )
            else:
                raise ImageProcessingError("Failed to process image")

        mock_client.caption_image.side_effect = mock_caption_side_effect

        register_vision_tools(mock_mcp, mock_client)

        # Get the batch function
        batch_func = self._get_registered_function(mock_mcp, "batch")

        # Test with typed parameters instead of JSON
        image_paths = json.dumps(["test1.jpg", "test2.jpg"])
        result = await batch_func(
            image_paths=image_paths, operation="caption", length="normal"
        )

        result_data = json.loads(result)

        # Check if this is an error response instead of batch result
        if "success" in result_data and not result_data["success"]:
            # This is an error response, not a batch result
            assert (
                False
            ), f"Batch processing failed: {result_data.get('error_message', 'Unknown error')}"

        assert result_data["total_processed"] == 2
        assert result_data["successful_count"] == 1
        assert result_data["failed_count"] == 1

        # Check individual results
        assert result_data["results"][0]["success"] is True
        assert result_data["results"][0]["caption"] == "Success"
        assert result_data["results"][1]["success"] is False
        assert "Failed to process image" in result_data["results"][1]["error_message"]

    @pytest.mark.asyncio
    async def test_analyze_image_query(
        self, mock_mcp: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Test analyze_image with query operation using typed parameters."""
        # Mock successful query response
        mock_client.query_image.return_value = QueryResult(
            success=True,
            answer="This is a test image",
            processing_time_ms=200.0,
            metadata={"image_path": "test.jpg", "question": "What is this?"},
        )

        register_vision_tools(mock_mcp, mock_client)

        # Get the analyze_image function
        analyze_func = self._get_registered_function(mock_mcp, "analyze")

        # Test with typed parameters instead of JSON
        result = await analyze_func(
            image_path="test.jpg", operation="query", question="What is this?"
        )

        result_data = json.loads(result)
        assert result_data["success"] is True
        assert result_data["answer"] == "This is a test image"

        # Verify the client was called with correct parameters
        mock_client.query_image.assert_called_once_with(
            image_path="test.jpg",
            question="What is this?",
        )
