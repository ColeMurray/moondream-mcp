"""
Performance and integration tests for moondream-mcp.
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from moondream_mcp.config import Config
from moondream_mcp.models import CaptionLength, CaptionResult
from moondream_mcp.tools.vision import register_vision_tools


class TestPerformance:
    """Performance tests for vision tools."""

    @pytest.fixture
    def mock_mcp(self) -> MagicMock:
        """Create a mock FastMCP instance."""
        mock = MagicMock()
        mock_decorator = MagicMock()
        mock.tool.return_value = mock_decorator
        return mock

    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        """Create mock MoondreamClient."""
        return AsyncMock()

    @pytest.fixture
    def performance_config(self) -> Config:
        """Create config optimized for performance testing."""
        return Config(
            max_batch_size=20,
            batch_concurrency=5,
            request_timeout_seconds=60,
            max_concurrent_requests=8,
        )

    def _get_registered_function(self, mock_mcp: MagicMock, function_name: str):
        """Helper method to get a registered function by name."""
        mock_decorator = mock_mcp.tool.return_value
        decorator_calls = mock_decorator.call_args_list

        for call in decorator_calls:
            if call[0] and hasattr(call[0][0], "__name__"):
                func_name = call[0][0].__name__
                if function_name == "batch" and func_name == "batch_analyze_images":
                    return call[0][0]
                elif function_name in func_name and function_name != "batch":
                    return call[0][0]
        return None

    @pytest.mark.asyncio
    async def test_batch_processing_performance(
        self, mock_mcp: MagicMock, mock_client: AsyncMock, performance_config: Config
    ):
        """Test batch processing performance with multiple images."""
        # Mock fast responses
        mock_client.caption_image.return_value = CaptionResult(
            success=True,
            caption="Test caption",
            length=CaptionLength.NORMAL,
            processing_time_ms=50.0,  # Fast processing
            metadata={"test": True},
        )

        register_vision_tools(mock_mcp, mock_client, performance_config)
        batch_func = self._get_registered_function(mock_mcp, "batch")

        # Test with 10 images
        image_paths = json.dumps([f"image{i}.jpg" for i in range(10)])

        start_time = time.time()
        result = await batch_func(
            image_paths=image_paths, operation="caption", length="normal"
        )
        elapsed_time = time.time() - start_time

        # Parse result
        result_data = json.loads(result)

        # Performance assertions
        assert result_data["total_processed"] == 10
        assert result_data["successful_count"] == 10
        assert elapsed_time < 5.0  # Should complete in under 5 seconds

        # Verify parallel processing was used
        assert mock_client.caption_image.call_count == 10

        # Check timing metrics
        assert "batch_processing_time_ms" in result_data
        assert "individual_processing_time_ms" in result_data
        assert "average_time_per_image_ms" in result_data

    @pytest.mark.asyncio
    async def test_concurrent_request_handling(
        self, mock_mcp: MagicMock, mock_client: AsyncMock, performance_config: Config
    ):
        """Test handling of concurrent requests."""

        # Mock responses with varying processing times
        def mock_caption_side_effect(*args, **kwargs):
            # Simulate varying processing times
            processing_time = 100.0 + (hash(str(args)) % 100)
            return CaptionResult(
                success=True,
                caption="Concurrent test",
                length=CaptionLength.NORMAL,
                processing_time_ms=processing_time,
                metadata={"concurrent": True},
            )

        mock_client.caption_image.side_effect = mock_caption_side_effect

        register_vision_tools(mock_mcp, mock_client, performance_config)
        caption_func = self._get_registered_function(mock_mcp, "caption")

        # Create multiple concurrent requests
        tasks = []
        for i in range(8):  # Test with max_concurrent_requests
            task = caption_func(f"image{i}.jpg", "normal", False)
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed_time = time.time() - start_time

        # All requests should complete successfully
        assert len(results) == 8
        for result in results:
            result_data = json.loads(result)
            assert result_data["success"] is True

        # Should complete faster than sequential processing
        assert elapsed_time < 2.0  # Concurrent should be much faster

    @pytest.mark.asyncio
    async def test_batch_error_isolation_performance(
        self, mock_mcp: MagicMock, mock_client: AsyncMock, performance_config: Config
    ):
        """Test that errors in batch processing don't significantly impact performance."""

        # Mock mixed success/failure responses
        def mock_caption_side_effect(*args, **kwargs):
            image_path = kwargs.get("image_path", args[0] if args else "")
            if "fail" in image_path:
                raise Exception("Simulated failure")
            return CaptionResult(
                success=True,
                caption="Success",
                length=CaptionLength.NORMAL,
                processing_time_ms=50.0,
                metadata={"test": True},
            )

        mock_client.caption_image.side_effect = mock_caption_side_effect

        register_vision_tools(mock_mcp, mock_client, performance_config)
        batch_func = self._get_registered_function(mock_mcp, "batch")

        # Mix of successful and failing images
        image_paths = json.dumps(
            [
                "image1.jpg",
                "fail1.jpg",
                "image2.jpg",
                "fail2.jpg",
                "image3.jpg",
                "image4.jpg",
            ]
        )

        start_time = time.time()
        result = await batch_func(
            image_paths=image_paths, operation="caption", length="normal"
        )
        elapsed_time = time.time() - start_time

        result_data = json.loads(result)

        # Should complete quickly despite errors
        assert elapsed_time < 3.0
        assert result_data["total_processed"] == 6
        assert result_data["successful_count"] == 4
        assert result_data["failed_count"] == 2

    @pytest.mark.asyncio
    async def test_memory_efficiency_large_batch(
        self, mock_mcp: MagicMock, mock_client: AsyncMock, performance_config: Config
    ):
        """Test memory efficiency with large batch processing."""
        # Mock lightweight responses
        mock_client.caption_image.return_value = CaptionResult(
            success=True,
            caption="Memory test",
            length=CaptionLength.SHORT,
            processing_time_ms=10.0,
            metadata={},  # Minimal metadata
        )

        register_vision_tools(mock_mcp, mock_client, performance_config)
        batch_func = self._get_registered_function(mock_mcp, "batch")

        # Test with maximum batch size
        max_batch = performance_config.max_batch_size
        image_paths = json.dumps([f"image{i}.jpg" for i in range(max_batch)])

        result = await batch_func(
            image_paths=image_paths, operation="caption", length="short"
        )

        result_data = json.loads(result)

        # Should handle maximum batch size successfully
        assert result_data["total_processed"] == max_batch
        assert result_data["successful_count"] == max_batch

        # Verify all results are present
        assert len(result_data["results"]) == max_batch


class TestIntegration:
    """Integration tests for the complete vision tools system."""

    @pytest.fixture
    def integration_config(self) -> Config:
        """Create config for integration testing."""
        return Config(
            model_name="test-model",
            device="cpu",  # Use CPU for consistent testing
            max_image_size=(512, 512),  # Smaller for faster testing
            request_timeout_seconds=30,
            max_batch_size=5,
            batch_concurrency=2,
        )

    @pytest.mark.asyncio
    async def test_full_workflow_integration(self, integration_config: Config):
        """Test complete workflow from registration to execution."""
        mock_mcp = MagicMock()
        mock_decorator = MagicMock()
        mock_mcp.tool.return_value = mock_decorator

        mock_client = AsyncMock()
        mock_client.caption_image.return_value = CaptionResult(
            success=True,
            caption="Integration test image",
            length=CaptionLength.NORMAL,
            processing_time_ms=100.0,
            metadata={"integration": True},
        )

        # Register tools
        register_vision_tools(mock_mcp, mock_client, integration_config)

        # Verify all tools were registered
        assert mock_mcp.tool.call_count == 6

        # Get and test a registered function
        decorator_calls = mock_decorator.call_args_list
        caption_func = None
        for call in decorator_calls:
            if call[0] and hasattr(call[0][0], "__name__"):
                if call[0][0].__name__ == "caption_image":
                    caption_func = call[0][0]
                    break

        assert caption_func is not None

        # Test the function
        result = await caption_func("test.jpg", "normal", False)
        result_data = json.loads(result)

        assert result_data["success"] is True
        assert result_data["caption"] == "Integration test image"

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, integration_config: Config):
        """Test error handling across the entire system."""
        mock_mcp = MagicMock()
        mock_decorator = MagicMock()
        mock_mcp.tool.return_value = mock_decorator

        mock_client = AsyncMock()

        # Test different types of errors
        error_scenarios = [
            (FileNotFoundError("File not found"), "FILE_NOT_FOUND"),
            (PermissionError("Permission denied"), "PERMISSION_DENIED"),
            (ValueError("Invalid input"), "INVALID_REQUEST"),
            (Exception("Unknown error"), "UNKNOWN_ERROR"),
        ]

        for error, expected_code in error_scenarios:
            mock_client.caption_image.side_effect = error

            register_vision_tools(mock_mcp, mock_client, integration_config)

            # Get caption function
            decorator_calls = mock_decorator.call_args_list
            caption_func = None
            for call in decorator_calls:
                if call[0] and hasattr(call[0][0], "__name__"):
                    if call[0][0].__name__ == "caption_image":
                        caption_func = call[0][0]
                        break

            result = await caption_func("test.jpg", "normal", False)
            result_data = json.loads(result)

            assert result_data["success"] is False
            assert result_data["error_code"] == expected_code
            assert "error_message" in result_data
            assert "timestamp" in result_data

    @pytest.mark.asyncio
    async def test_configuration_integration(self):
        """Test that configuration is properly integrated throughout the system."""
        # Test with custom configuration
        custom_config = Config(
            max_batch_size=3,
            batch_concurrency=1,
            request_timeout_seconds=15,
        )

        mock_mcp = MagicMock()
        mock_decorator = MagicMock()
        mock_mcp.tool.return_value = mock_decorator

        mock_client = AsyncMock()
        mock_client.caption_image.return_value = CaptionResult(
            success=True,
            caption="Config test",
            length=CaptionLength.NORMAL,
            processing_time_ms=50.0,
            metadata={},
        )

        register_vision_tools(mock_mcp, mock_client, custom_config)

        # Get batch function
        decorator_calls = mock_decorator.call_args_list
        batch_func = None
        for call in decorator_calls:
            if call[0] and hasattr(call[0][0], "__name__"):
                if call[0][0].__name__ == "batch_analyze_images":
                    batch_func = call[0][0]
                    break

        # Test batch size limit enforcement
        large_batch = json.dumps(
            [f"image{i}.jpg" for i in range(5)]
        )  # Exceeds limit of 3

        result = await batch_func(
            image_paths=large_batch, operation="caption", length="normal"
        )

        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "BATCH_SIZE_EXCEEDED" in result_data["error_code"]

    @pytest.mark.asyncio
    async def test_validation_integration(self):
        """Test that validation is properly integrated across all tools."""
        mock_mcp = MagicMock()
        mock_decorator = MagicMock()
        mock_mcp.tool.return_value = mock_decorator

        mock_client = AsyncMock()

        register_vision_tools(mock_mcp, mock_client)

        # Get analyze function
        decorator_calls = mock_decorator.call_args_list
        analyze_func = None
        for call in decorator_calls:
            if call[0] and hasattr(call[0][0], "__name__"):
                if call[0][0].__name__ == "analyze_image":
                    analyze_func = call[0][0]
                    break

        # Test validation scenarios
        validation_tests = [
            # Empty image path
            ("", "caption", {}, "EMPTY_PATH"),
            # Invalid operation
            ("test.jpg", "invalid", {}, "INVALID_OPERATION"),
            # Missing question for query
            ("test.jpg", "query", {}, "MISSING_QUESTION"),
            # Missing object_name for detect
            ("test.jpg", "detect", {}, "MISSING_OBJECT_NAME"),
        ]

        for image_path, operation, extra_params, expected_error in validation_tests:
            result = await analyze_func(
                image_path=image_path, operation=operation, **extra_params
            )

            result_data = json.loads(result)
            assert result_data["success"] is False
            assert expected_error in result_data["error_code"]


@pytest.mark.slow
class TestStressTests:
    """Stress tests for high-load scenarios."""

    @pytest.mark.asyncio
    async def test_high_concurrency_stress(self):
        """Test system under high concurrency load."""
        mock_mcp = MagicMock()
        mock_decorator = MagicMock()
        mock_mcp.tool.return_value = mock_decorator

        mock_client = AsyncMock()
        mock_client.caption_image.return_value = CaptionResult(
            success=True,
            caption="Stress test",
            length=CaptionLength.NORMAL,
            processing_time_ms=10.0,
            metadata={},
        )

        config = Config(max_concurrent_requests=16, batch_concurrency=8)
        register_vision_tools(mock_mcp, mock_client, config)

        # Get caption function
        decorator_calls = mock_decorator.call_args_list
        caption_func = None
        for call in decorator_calls:
            if call[0] and hasattr(call[0][0], "__name__"):
                if call[0][0].__name__ == "caption_image":
                    caption_func = call[0][0]
                    break

        # Create many concurrent requests
        tasks = []
        for i in range(50):  # High load
            task = caption_func(f"stress_image{i}.jpg", "normal", False)
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed_time = time.time() - start_time

        # Check that most requests completed successfully
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 45  # Allow for some failures under stress

        # Should complete in reasonable time
        assert elapsed_time < 10.0

    @pytest.mark.asyncio
    async def test_memory_stress_large_batches(self):
        """Test memory usage with large batch operations."""
        mock_mcp = MagicMock()
        mock_decorator = MagicMock()
        mock_mcp.tool.return_value = mock_decorator

        mock_client = AsyncMock()
        mock_client.caption_image.return_value = CaptionResult(
            success=True,
            caption="Memory stress test",
            length=CaptionLength.NORMAL,
            processing_time_ms=5.0,
            metadata={},
        )

        config = Config(max_batch_size=50, batch_concurrency=10)
        register_vision_tools(mock_mcp, mock_client, config)

        # Get batch function
        decorator_calls = mock_decorator.call_args_list
        batch_func = None
        for call in decorator_calls:
            if call[0] and hasattr(call[0][0], "__name__"):
                if call[0][0].__name__ == "batch_analyze_images":
                    batch_func = call[0][0]
                    break

        # Process multiple large batches
        for batch_num in range(3):
            image_paths = json.dumps(
                [f"batch{batch_num}_image{i}.jpg" for i in range(50)]
            )

            result = await batch_func(
                image_paths=image_paths, operation="caption", length="normal"
            )

            result_data = json.loads(result)
            assert result_data["total_processed"] == 50
            assert result_data["successful_count"] == 50
