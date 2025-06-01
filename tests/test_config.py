"""
Tests for configuration management.
"""

import os

import pytest

from moondream_mcp.config import Config


class TestConfig:
    """Test configuration management."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = Config()

        assert config.model_name == "vikhyatk/moondream2"
        assert config.model_revision == "2025-01-09"
        assert config.trust_remote_code is True
        assert config.max_image_size == (2048, 2048)
        assert config.timeout_seconds == 120
        assert config.max_concurrent_requests == 5

    def test_from_env_with_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test configuration from environment with defaults."""
        # Clear any existing environment variables
        for key in os.environ:
            if key.startswith("MOONDREAM_"):
                monkeypatch.delenv(key, raising=False)

        config = Config.from_env()

        assert config.model_name == "vikhyatk/moondream2"
        assert config.device in ("cpu", "cuda", "mps")

    def test_from_env_with_custom_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test configuration from environment with custom values."""
        monkeypatch.setenv("MOONDREAM_MODEL_NAME", "custom/model")
        monkeypatch.setenv("MOONDREAM_MODEL_REVISION", "custom-revision")
        monkeypatch.setenv("MOONDREAM_DEVICE", "cpu")
        monkeypatch.setenv("MOONDREAM_MAX_IMAGE_SIZE", "1024x768")
        monkeypatch.setenv("MOONDREAM_TIMEOUT_SECONDS", "60")

        config = Config.from_env()

        assert config.model_name == "custom/model"
        assert config.model_revision == "custom-revision"
        assert config.device == "cpu"
        assert config.max_image_size == (1024, 768)
        assert config.timeout_seconds == 60

    def test_invalid_device(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test invalid device configuration."""
        monkeypatch.setenv("MOONDREAM_DEVICE", "invalid")

        with pytest.raises(ValueError, match="Invalid MOONDREAM_DEVICE"):
            Config.from_env()

    def test_invalid_image_size(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test invalid image size configuration."""
        monkeypatch.setenv("MOONDREAM_MAX_IMAGE_SIZE", "invalid")

        with pytest.raises(ValueError, match="Invalid MOONDREAM_MAX_IMAGE_SIZE"):
            Config.from_env()

    def test_validation_errors(self) -> None:
        """Test configuration validation errors."""
        config = Config()

        # Test invalid timeout
        config.timeout_seconds = 0
        with pytest.raises(ValueError, match="timeout_seconds must be at least 1"):
            config._validate()

        # Test invalid image size
        config.timeout_seconds = 120  # Reset to valid value
        config.max_image_size = (0, 0)
        with pytest.raises(
            ValueError, match="max_image_size dimensions must be at least 1"
        ):
            config._validate()

        # Test oversized image
        config.max_image_size = (5000, 5000)
        with pytest.raises(
            ValueError, match="max_image_size dimensions cannot exceed 4096"
        ):
            config._validate()

    def test_device_info(self) -> None:
        """Test device information string."""
        config = Config()
        device_info = config.get_device_info()

        assert isinstance(device_info, str)
        assert len(device_info) > 0

    def test_config_string_representation(self) -> None:
        """Test configuration string representation."""
        config = Config()
        config_str = str(config)

        assert "Config(" in config_str
        assert config.model_name in config_str
        assert str(config.timeout_seconds) in config_str
