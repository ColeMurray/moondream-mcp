"""
Configuration management for Moondream MCP Server.

Handles environment variables, device detection, and model configuration
with sensible defaults and clear validation.
"""

import os
import platform
import sys
from dataclasses import dataclass
from typing import Literal, Optional, Tuple

import torch

DeviceType = Literal["cpu", "cuda", "mps"]


@dataclass
class Config:
    """Configuration for Moondream MCP Server."""

    # Model settings
    model_name: str = "vikhyatk/moondream2"
    model_revision: str = "2025-01-09"
    trust_remote_code: bool = True

    # Device settings
    device: DeviceType = "cpu"
    device_auto_detect: bool = True

    # Image processing settings
    max_image_size: Tuple[int, int] = (2048, 2048)
    supported_formats: Tuple[str, ...] = ("JPEG", "PNG", "WebP", "BMP", "TIFF")
    max_file_size_mb: int = 50

    # Performance settings
    timeout_seconds: int = 120
    max_concurrent_requests: int = 5
    enable_streaming: bool = True
    max_batch_size: int = 10
    batch_concurrency: int = 3
    enable_batch_progress: bool = True

    # Network settings (for remote URLs)
    request_timeout_seconds: int = 30
    max_redirects: int = 5
    user_agent: str = "Moondream-MCP/1.0.0"

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        config = cls()

        # Model configuration
        config.model_name = os.getenv("MOONDREAM_MODEL_NAME", config.model_name)
        config.model_revision = os.getenv(
            "MOONDREAM_MODEL_REVISION", config.model_revision
        )
        config.trust_remote_code = _parse_bool(
            os.getenv("MOONDREAM_TRUST_REMOTE_CODE", "true")
        )

        # Device configuration
        device_env = os.getenv("MOONDREAM_DEVICE")
        if device_env:
            if device_env.lower() not in ("cpu", "cuda", "mps"):
                raise ValueError(
                    f"Invalid MOONDREAM_DEVICE: {device_env}. "
                    "Must be one of: cpu, cuda, mps"
                )
            config.device = device_env.lower()  # type: ignore
            config.device_auto_detect = False
        else:
            config.device = config._detect_best_device()

        # Image processing settings
        max_size_env = os.getenv("MOONDREAM_MAX_IMAGE_SIZE")
        if max_size_env:
            try:
                if "x" in max_size_env:
                    width, height = map(int, max_size_env.split("x"))
                    config.max_image_size = (width, height)
                else:
                    size = int(max_size_env)
                    config.max_image_size = (size, size)
            except ValueError:
                raise ValueError(
                    f"Invalid MOONDREAM_MAX_IMAGE_SIZE: {max_size_env}. "
                    "Use format: '2048' or '2048x1536'"
                )

        config.max_file_size_mb = int(
            os.getenv("MOONDREAM_MAX_FILE_SIZE_MB", str(config.max_file_size_mb))
        )

        # Performance settings
        config.timeout_seconds = int(
            os.getenv("MOONDREAM_TIMEOUT_SECONDS", str(config.timeout_seconds))
        )
        config.max_concurrent_requests = int(
            os.getenv(
                "MOONDREAM_MAX_CONCURRENT_REQUESTS", str(config.max_concurrent_requests)
            )
        )
        config.enable_streaming = _parse_bool(
            os.getenv("MOONDREAM_ENABLE_STREAMING", "true")
        )
        config.max_batch_size = int(
            os.getenv("MOONDREAM_MAX_BATCH_SIZE", str(config.max_batch_size))
        )
        config.batch_concurrency = int(
            os.getenv("MOONDREAM_BATCH_CONCURRENCY", str(config.batch_concurrency))
        )
        config.enable_batch_progress = _parse_bool(
            os.getenv("MOONDREAM_ENABLE_BATCH_PROGRESS", "true")
        )

        # Network settings
        config.request_timeout_seconds = int(
            os.getenv(
                "MOONDREAM_REQUEST_TIMEOUT_SECONDS", str(config.request_timeout_seconds)
            )
        )
        config.max_redirects = int(
            os.getenv("MOONDREAM_MAX_REDIRECTS", str(config.max_redirects))
        )
        config.user_agent = os.getenv("MOONDREAM_USER_AGENT", config.user_agent)

        # Validate configuration
        config._validate()

        return config

    def _detect_best_device(self) -> DeviceType:
        """Detect the best available device for inference."""
        # Check for Apple Silicon MPS
        if torch.backends.mps.is_available() and platform.system() == "Darwin":
            return "mps"

        # Check for CUDA
        if torch.cuda.is_available():
            return "cuda"

        # Fallback to CPU
        return "cpu"

    def _validate(self) -> None:
        """Validate configuration values."""
        # Validate timeout
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be at least 1")

        # Validate image size
        max_width, max_height = self.max_image_size
        if max_width < 1 or max_height < 1:
            raise ValueError("max_image_size dimensions must be at least 1")
        if max_width > 4096 or max_height > 4096:
            raise ValueError("max_image_size dimensions cannot exceed 4096")

        # Validate file size
        if self.max_file_size_mb < 1:
            raise ValueError("max_file_size_mb must be at least 1")
        if self.max_file_size_mb > 500:
            raise ValueError("max_file_size_mb cannot exceed 500")

        # Validate concurrent requests
        if self.max_concurrent_requests < 1:
            raise ValueError("max_concurrent_requests must be at least 1")
        if self.max_concurrent_requests > 50:
            raise ValueError("max_concurrent_requests cannot exceed 50")

        # Validate batch settings
        if self.max_batch_size < 1:
            raise ValueError("max_batch_size must be at least 1")
        if self.max_batch_size > 100:
            raise ValueError("max_batch_size cannot exceed 100")

        if self.batch_concurrency < 1:
            raise ValueError("batch_concurrency must be at least 1")
        if self.batch_concurrency > self.max_concurrent_requests:
            raise ValueError("batch_concurrency cannot exceed max_concurrent_requests")

        # Validate network settings
        if self.request_timeout_seconds < 1:
            raise ValueError("request_timeout_seconds must be at least 1")
        if self.max_redirects < 0:
            raise ValueError("max_redirects cannot be negative")

    def validate_dependencies(self) -> None:
        """Validate that required dependencies are available."""
        try:
            import aiohttp
            import requests
            import torch
            import transformers
            from PIL import Image
        except ImportError as e:
            raise ValueError(
                f"Missing required dependency: {e.name}. "
                "Please install with: pip install moondream-mcp[dev]"
            )

        # Check PyTorch version
        torch_version = torch.__version__
        if not torch_version.startswith(("2.", "1.13", "1.14")):
            print(
                f"⚠️  Warning: PyTorch {torch_version} may not be fully supported",
                file=sys.stderr,
            )

        # Check device availability
        if self.device == "cuda" and not torch.cuda.is_available():
            raise ValueError(
                "CUDA device requested but not available. "
                "Please install CUDA-enabled PyTorch or use CPU/MPS"
            )

        if self.device == "mps" and not torch.backends.mps.is_available():
            raise ValueError(
                "MPS device requested but not available. "
                "MPS requires macOS 12.3+ and Apple Silicon"
            )

    def get_device_info(self) -> str:
        """Get human-readable device information."""
        if self.device == "cuda":
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                memory_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
                return f"CUDA ({device_name}, {memory_gb:.1f}GB)"
            else:
                return "CUDA (not available)"
        elif self.device == "mps":
            if torch.backends.mps.is_available():
                return "MPS (Apple Silicon)"
            else:
                return "MPS (not available)"
        else:
            return "CPU"

    def __str__(self) -> str:
        """String representation for logging."""
        return (
            f"Config("
            f"model={self.model_name}@{self.model_revision}, "
            f"device={self.get_device_info()}, "
            f"max_size={self.max_image_size[0]}x{self.max_image_size[1]}, "
            f"timeout={self.timeout_seconds}s, "
            f"max_concurrent={self.max_concurrent_requests}"
            f")"
        )


def _parse_bool(value: str) -> bool:
    """Parse a string as a boolean value."""
    return value.lower() in ("true", "1", "yes", "on")
