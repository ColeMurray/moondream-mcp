"""
Extended tests for configuration management.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from moondream_mcp.config import Config


class TestConfigExtended:
    """Extended tests for Config class covering edge cases and missing coverage."""

    def test_config_from_env_with_all_variables(self):
        """Test config creation with all environment variables set."""
        env_vars = {
            "MOONDREAM_MODEL_NAME": "custom-model",
            "MOONDREAM_DEVICE": "cuda",
            "MOONDREAM_MAX_IMAGE_SIZE": "2048",
            "MOONDREAM_REQUEST_TIMEOUT_SECONDS": "45",
            "MOONDREAM_MAX_CONCURRENT_REQUESTS": "8",
            "MOONDREAM_ENABLE_STREAMING": "true",
            "MOONDREAM_MAX_BATCH_SIZE": "15",
            "MOONDREAM_BATCH_CONCURRENCY": "5",
            "MOONDREAM_ENABLE_BATCH_PROGRESS": "false",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = Config.from_env()

            assert config.model_name == "custom-model"
            assert config.device == "cuda"
            assert config.max_image_size == (2048, 2048)
            assert config.request_timeout_seconds == 45
            assert config.max_concurrent_requests == 8
            assert config.enable_streaming is True
            assert config.max_batch_size == 15
            assert config.batch_concurrency == 5
            assert config.enable_batch_progress is False

    def test_config_from_env_boolean_parsing(self):
        """Test boolean environment variable parsing."""
        # Test various boolean representations
        boolean_tests = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
            ("", False),
            ("invalid", False),
        ]

        for env_value, expected in boolean_tests:
            with patch.dict(
                os.environ, {"MOONDREAM_ENABLE_STREAMING": env_value}, clear=False
            ):
                config = Config.from_env()
                assert (
                    config.enable_streaming == expected
                ), f"Failed for value: {env_value}"

    def test_config_from_env_integer_parsing_invalid(self):
        """Test integer environment variable parsing with invalid values."""
        with pytest.raises(ValueError, match="Invalid MOONDREAM_MAX_IMAGE_SIZE"):
            with patch.dict(
                os.environ, {"MOONDREAM_MAX_IMAGE_SIZE": "invalid"}, clear=False
            ):
                Config.from_env()

    def test_config_max_image_size_formats(self):
        """Test different max image size formats."""
        # Test single dimension format
        with patch.dict(os.environ, {"MOONDREAM_MAX_IMAGE_SIZE": "1024"}, clear=False):
            config = Config.from_env()
            assert config.max_image_size == (1024, 1024)

        # Test width x height format
        with patch.dict(
            os.environ, {"MOONDREAM_MAX_IMAGE_SIZE": "1920x1080"}, clear=False
        ):
            config = Config.from_env()
            assert config.max_image_size == (1920, 1080)

    def test_config_validation_max_image_size(self):
        """Test validation of max_image_size parameter."""
        # Test valid sizes
        config = Config(max_image_size=(64, 64))
        config._validate()  # Should not raise

        config = Config(max_image_size=(4096, 4096))
        config._validate()  # Should not raise

        # Test invalid sizes
        with pytest.raises(
            ValueError, match="max_image_size dimensions must be at least 1"
        ):
            config = Config(max_image_size=(0, 100))
            config._validate()

        with pytest.raises(
            ValueError, match="max_image_size dimensions cannot exceed 4096"
        ):
            config = Config(max_image_size=(5000, 100))
            config._validate()

    def test_config_validation_timeout_seconds(self):
        """Test validation of timeout parameters."""
        # Test valid timeout
        config = Config(timeout_seconds=1)
        config._validate()  # Should not raise

        config = Config(timeout_seconds=300)
        config._validate()  # Should not raise

        # Test invalid timeout
        with pytest.raises(ValueError, match="timeout_seconds must be at least 1"):
            config = Config(timeout_seconds=0)
            config._validate()

    def test_config_validation_concurrent_requests(self):
        """Test validation of concurrent requests parameter."""
        # Test valid values (need to set batch_concurrency to be <= max_concurrent_requests)
        config = Config(max_concurrent_requests=1, batch_concurrency=1)
        config._validate()  # Should not raise

        config = Config(max_concurrent_requests=50, batch_concurrency=3)
        config._validate()  # Should not raise

        # Test invalid values
        with pytest.raises(
            ValueError, match="max_concurrent_requests must be at least 1"
        ):
            config = Config(max_concurrent_requests=0, batch_concurrency=0)
            config._validate()

        with pytest.raises(
            ValueError, match="max_concurrent_requests cannot exceed 50"
        ):
            config = Config(max_concurrent_requests=51, batch_concurrency=3)
            config._validate()

    def test_config_validation_batch_size(self):
        """Test validation of batch size parameters."""
        # Test valid values
        config = Config(max_batch_size=1)
        config._validate()  # Should not raise

        config = Config(max_batch_size=100)
        config._validate()  # Should not raise

        # Test invalid values
        with pytest.raises(ValueError, match="max_batch_size must be at least 1"):
            config = Config(max_batch_size=0)
            config._validate()

        with pytest.raises(ValueError, match="max_batch_size cannot exceed 100"):
            config = Config(max_batch_size=101)
            config._validate()

    def test_config_validation_batch_concurrency(self):
        """Test validation of batch concurrency parameter."""
        # Test valid values
        config = Config(batch_concurrency=1, max_concurrent_requests=5)
        config._validate()  # Should not raise

        config = Config(batch_concurrency=5, max_concurrent_requests=5)
        config._validate()  # Should not raise

        # Test invalid values
        with pytest.raises(ValueError, match="batch_concurrency must be at least 1"):
            config = Config(batch_concurrency=0)
            config._validate()

        with pytest.raises(
            ValueError, match="batch_concurrency cannot exceed max_concurrent_requests"
        ):
            config = Config(batch_concurrency=10, max_concurrent_requests=5)
            config._validate()

    def test_config_device_validation(self):
        """Test device validation."""
        # Test valid devices
        valid_devices = ["cpu", "cuda", "mps"]

        for device in valid_devices:
            config = Config(device=device)
            assert config.device == device

        # Test invalid device through environment variable
        with pytest.raises(ValueError, match="Invalid MOONDREAM_DEVICE"):
            with patch.dict(
                os.environ, {"MOONDREAM_DEVICE": "invalid_device"}, clear=False
            ):
                Config.from_env()

    def test_config_model_name_validation(self):
        """Test model name configuration."""
        # Test valid model names
        valid_models = [
            "vikhyatk/moondream2",
            "custom/model",
            "local-model",
            "model_with_underscores",
        ]

        for model_name in valid_models:
            config = Config(model_name=model_name)
            assert config.model_name == model_name

    def test_config_file_size_validation(self):
        """Test file size validation."""
        # Test valid file sizes
        config = Config(max_file_size_mb=1)
        config._validate()  # Should not raise

        config = Config(max_file_size_mb=500)
        config._validate()  # Should not raise

        # Test invalid file sizes
        with pytest.raises(ValueError, match="max_file_size_mb must be at least 1"):
            config = Config(max_file_size_mb=0)
            config._validate()

        with pytest.raises(ValueError, match="max_file_size_mb cannot exceed 500"):
            config = Config(max_file_size_mb=501)
            config._validate()

    def test_config_repr_and_str(self):
        """Test string representation of config."""
        config = Config()

        # Test __repr__
        repr_str = repr(config)
        assert "Config" in repr_str
        assert "model_name" in repr_str

        # Test __str__
        str_str = str(config)
        assert isinstance(str_str, str)
        assert "Config(" in str_str
        assert "model=" in str_str
        assert "device=" in str_str

    def test_config_equality(self):
        """Test config equality comparison."""
        config1 = Config()
        config2 = Config()

        # Should be equal with same parameters
        assert config1 == config2

        # Should not be equal with different parameters
        config3 = Config(max_image_size=(1024, 1024))
        assert config1 != config3

    def test_config_device_info(self):
        """Test device information retrieval."""
        config = Config(device="cpu")
        device_info = config.get_device_info()
        assert device_info == "CPU"

        # Test with different devices
        config = Config(device="cuda")
        device_info = config.get_device_info()
        assert "CUDA" in device_info

        config = Config(device="mps")
        device_info = config.get_device_info()
        assert "MPS" in device_info

    def test_config_env_var_precedence(self):
        """Test environment variable precedence over defaults."""
        # Set environment variable
        with patch.dict(os.environ, {"MOONDREAM_MAX_IMAGE_SIZE": "512"}, clear=False):
            config = Config.from_env()
            assert config.max_image_size == (512, 512)

        # Without environment variable, should use default
        with patch.dict(os.environ, {}, clear=True):
            config = Config.from_env()
            assert config.max_image_size == (2048, 2048)  # default value

    def test_config_partial_env_vars(self):
        """Test config with only some environment variables set."""
        partial_env = {
            "MOONDREAM_MODEL_NAME": "partial-model",
            "MOONDREAM_MAX_IMAGE_SIZE": "512",
            # Other variables not set, should use defaults
        }

        with patch.dict(os.environ, partial_env, clear=False):
            config = Config.from_env()

            # Set variables should use env values
            assert config.model_name == "partial-model"
            assert config.max_image_size == (512, 512)

            # Unset variables should use defaults
            assert config.device in ["cpu", "cuda", "mps"]  # auto-detected
            assert config.request_timeout_seconds == 30  # default
            assert config.max_concurrent_requests == 5  # default

    def test_config_network_settings(self):
        """Test network-related configuration."""
        config = Config(
            request_timeout_seconds=60, max_redirects=10, user_agent="Custom-Agent/1.0"
        )

        assert config.request_timeout_seconds == 60
        assert config.max_redirects == 10
        assert config.user_agent == "Custom-Agent/1.0"

    def test_config_network_validation(self):
        """Test network settings validation."""
        # Test valid values
        config = Config(request_timeout_seconds=1, max_redirects=0)
        config._validate()  # Should not raise

        # Test invalid values
        with pytest.raises(
            ValueError, match="request_timeout_seconds must be at least 1"
        ):
            config = Config(request_timeout_seconds=0)
            config._validate()

        with pytest.raises(ValueError, match="max_redirects cannot be negative"):
            config = Config(max_redirects=-1)
            config._validate()

    def test_config_supported_formats(self):
        """Test supported image formats configuration."""
        config = Config()

        # Check default supported formats
        assert "JPEG" in config.supported_formats
        assert "PNG" in config.supported_formats
        assert "WebP" in config.supported_formats
        assert "BMP" in config.supported_formats
        assert "TIFF" in config.supported_formats

    def test_config_model_revision(self):
        """Test model revision configuration."""
        # Test default revision
        config = Config()
        assert config.model_revision == "2025-01-09"

        # Test custom revision via environment
        with patch.dict(
            os.environ, {"MOONDREAM_MODEL_REVISION": "custom-rev"}, clear=False
        ):
            config = Config.from_env()
            assert config.model_revision == "custom-rev"

    def test_config_trust_remote_code(self):
        """Test trust_remote_code configuration."""
        # Test default value
        config = Config()
        assert config.trust_remote_code is True

        # Test via environment variable
        with patch.dict(
            os.environ, {"MOONDREAM_TRUST_REMOTE_CODE": "false"}, clear=False
        ):
            config = Config.from_env()
            assert config.trust_remote_code is False
