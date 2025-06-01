"""
Moondream MCP Server.

A FastMCP server for Moondream AI vision language model integration.
Provides image analysis capabilities including captioning, visual question answering,
object detection, and visual pointing through the Model Context Protocol (MCP).
"""

__version__ = "1.0.0"
__author__ = "Moondream MCP Contributors"
__email__ = "support@example.com"
__description__ = "FastMCP server for Moondream AI vision language model"

from .config import Config
from .models import (
    AnalysisResult,
    CaptionRequest,
    CaptionResult,
    DetectionRequest,
    DetectionResult,
    ImageAnalysisRequest,
    PointingRequest,
    PointingResult,
    QueryRequest,
    QueryResult,
)
from .moondream import MoondreamClient, MoondreamError
from .server import create_server, main

__all__ = [
    # Core components
    "Config",
    "MoondreamClient",
    "MoondreamError",
    "create_server",
    "main",
    # Data models
    "ImageAnalysisRequest",
    "CaptionRequest",
    "QueryRequest",
    "DetectionRequest",
    "PointingRequest",
    "AnalysisResult",
    "CaptionResult",
    "QueryResult",
    "DetectionResult",
    "PointingResult",
]
