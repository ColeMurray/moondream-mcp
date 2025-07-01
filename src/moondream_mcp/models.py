"""
Data models for moondream-mcp.

Defines Pydantic models for API requests, responses, and internal data structures
used throughout the vision analysis tools.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class CaptionLength(str, Enum):
    """Caption length options."""

    SHORT = "short"
    NORMAL = "normal"
    DETAILED = "detailed"


class ImageAnalysisRequest(BaseModel):
    """Base request model for image analysis."""

    image_path: str = Field(
        ..., description="Path to image file (local path or URL)", min_length=1
    )

    @field_validator("image_path")
    @classmethod
    def validate_image_path(cls, v: str) -> str:
        """Validate image path format."""
        v = v.strip()
        if not v:
            raise ValueError("Image path cannot be empty")

        # Check if it's a URL or local path
        if v.startswith(("http://", "https://")):
            return v
        elif v.startswith(("/", "~", ".", "\\")):
            return v
        else:
            # Assume relative path
            return v


class CaptionRequest(ImageAnalysisRequest):
    """Request model for image captioning."""

    length: CaptionLength = Field(
        default=CaptionLength.NORMAL, description="Length of caption to generate"
    )

    stream: bool = Field(
        default=False, description="Whether to stream the caption generation"
    )


class QueryRequest(ImageAnalysisRequest):
    """Request model for visual question answering."""

    question: str = Field(
        ...,
        description="Question to ask about the image",
        min_length=1,
        max_length=1000,
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Validate question format."""
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty")
        return v


class DetectionRequest(ImageAnalysisRequest):
    """Request model for object detection."""

    object_name: str = Field(
        ..., description="Name of object to detect", min_length=1, max_length=100
    )

    @field_validator("object_name")
    @classmethod
    def validate_object_name(cls, v: str) -> str:
        """Validate object name format."""
        v = v.strip()
        if not v:
            raise ValueError("Object name cannot be empty")
        return v


class PointingRequest(ImageAnalysisRequest):
    """Request model for visual pointing."""

    object_name: str = Field(
        ..., description="Name of object to locate", min_length=1, max_length=100
    )

    @field_validator("object_name")
    @classmethod
    def validate_object_name(cls, v: str) -> str:
        """Validate object name format."""
        v = v.strip()
        if not v:
            raise ValueError("Object name cannot be empty")
        return v


class BatchAnalysisRequest(BaseModel):
    """Request model for batch image analysis."""

    image_paths: List[str] = Field(
        ...,
        description="List of image paths (local paths or URLs)",
        min_length=1,
        max_length=10,
    )

    operation: str = Field(
        ...,
        description="Operation to perform on all images",
        pattern="^(caption|query|detect|point)$",
    )

    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Parameters for the operation"
    )

    @field_validator("image_paths")
    @classmethod
    def validate_image_paths(cls, v: List[str]) -> List[str]:
        """Validate image paths are not empty."""
        if not v:
            raise ValueError("Image paths list cannot be empty")

        validated_paths = []
        for path in v:
            if not path or not path.strip():
                raise ValueError("Image path cannot be empty")
            validated_paths.append(path.strip())

        return validated_paths


# Response Models


class StandardError(BaseModel):
    """Standardized error response model."""

    success: bool = Field(default=False, description="Always false for errors")

    error_message: str = Field(..., description="Human-readable error message")

    error_code: str = Field(..., description="Machine-readable error code")

    error_context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context about the error"
    )

    timestamp: Optional[str] = Field(
        None, description="ISO timestamp when error occurred"
    )


class AnalysisResult(BaseModel):
    """Base result model for image analysis."""

    success: bool = Field(..., description="Whether the analysis was successful")

    processing_time_ms: Optional[float] = Field(
        None, description="Processing time in milliseconds"
    )

    error_message: Optional[str] = Field(
        None, description="Error message if analysis failed"
    )

    error_code: Optional[str] = Field(
        None, description="Machine-readable error code if analysis failed"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the analysis"
    )

    @classmethod
    def create_error(
        cls,
        error_message: str,
        error_code: str = "ANALYSIS_ERROR",
        metadata: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[float] = None,
    ) -> "AnalysisResult":
        """Create a standardized error result."""
        return cls(
            success=False,
            error_message=error_message,
            error_code=error_code,
            metadata=metadata or {},
            processing_time_ms=processing_time_ms,
        )


class CaptionResult(AnalysisResult):
    """Result model for image captioning."""

    caption: Optional[str] = Field(None, description="Generated caption")

    confidence: Optional[float] = Field(
        None, description="Confidence score (0.0 to 1.0)", ge=0.0, le=1.0
    )

    length: Optional[CaptionLength] = Field(
        None, description="Length of generated caption"
    )


class QueryResult(AnalysisResult):
    """Result model for visual question answering."""

    answer: Optional[str] = Field(None, description="Answer to the question")

    question: Optional[str] = Field(None, description="Original question")

    confidence: Optional[float] = Field(
        None, description="Confidence score (0.0 to 1.0)", ge=0.0, le=1.0
    )


class BoundingBox(BaseModel):
    """Bounding box coordinates."""

    x: float = Field(
        ..., description="X coordinate (normalized 0.0 to 1.0)", ge=0.0, le=1.0
    )

    y: float = Field(
        ..., description="Y coordinate (normalized 0.0 to 1.0)", ge=0.0, le=1.0
    )

    width: float = Field(
        ..., description="Width (normalized 0.0 to 1.0)", ge=0.0, le=1.0
    )

    height: float = Field(
        ..., description="Height (normalized 0.0 to 1.0)", ge=0.0, le=1.0
    )


class DetectedObject(BaseModel):
    """Detected object with location and confidence."""

    name: str = Field(..., description="Name of detected object")

    confidence: float = Field(
        ..., description="Detection confidence (0.0 to 1.0)", ge=0.0, le=1.0
    )

    bounding_box: BoundingBox = Field(..., description="Bounding box coordinates")


class DetectionResult(AnalysisResult):
    """Result model for object detection."""

    objects: List[DetectedObject] = Field(
        default_factory=list, description="List of detected objects"
    )

    object_name: Optional[str] = Field(
        None, description="Name of object that was searched for"
    )

    total_found: int = Field(
        default=0, description="Total number of objects found", ge=0
    )


class Point(BaseModel):
    """Point coordinates."""

    x: float = Field(
        ..., description="X coordinate (normalized 0.0 to 1.0)", ge=0.0, le=1.0
    )

    y: float = Field(
        ..., description="Y coordinate (normalized 0.0 to 1.0)", ge=0.0, le=1.0
    )


class PointedObject(BaseModel):
    """Pointed object with location and confidence."""

    name: str = Field(..., description="Name of pointed object")

    confidence: float = Field(
        ..., description="Pointing confidence (0.0 to 1.0)", ge=0.0, le=1.0
    )

    point: Point = Field(..., description="Point coordinates")


class PointingResult(AnalysisResult):
    """Result model for visual pointing."""

    points: List[PointedObject] = Field(
        default_factory=list, description="List of pointed objects"
    )

    object_name: Optional[str] = Field(
        None, description="Name of object that was searched for"
    )

    total_found: int = Field(
        default=0, description="Total number of objects found", ge=0
    )


class BatchAnalysisResult(BaseModel):
    """Result model for batch image analysis."""

    results: List[AnalysisResult] = Field(..., description="List of analysis results")

    total_processed: int = Field(
        ..., description="Total number of images processed", ge=0
    )

    total_successful: int = Field(
        ..., description="Total number of successful analyses", ge=0
    )

    total_failed: int = Field(..., description="Total number of failed analyses", ge=0)

    total_processing_time_ms: float = Field(
        ..., description="Total processing time in milliseconds", ge=0.0
    )


# Union types for convenience
AnalysisRequestType = Union[
    CaptionRequest,
    QueryRequest,
    DetectionRequest,
    PointingRequest,
    BatchAnalysisRequest,
]

AnalysisResultType = Union[
    CaptionResult, QueryResult, DetectionResult, PointingResult, BatchAnalysisResult
]
