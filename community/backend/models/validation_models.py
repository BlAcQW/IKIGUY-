"""
Validation models for African Language Community Platform.

Pydantic models for community validation of submissions.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from models.language_models import PyObjectId


class ValidationAction(str, Enum):
    """Actions validators can take."""

    APPROVE = "approve"
    REJECT = "reject"
    FLAG = "flag"
    REQUEST_CHANGES = "request_changes"


class ValidationCategory(str, Enum):
    """Categories for validation focus."""

    CONTENT_QUALITY = "content_quality"
    LINGUISTIC_ACCURACY = "linguistic_accuracy"
    CULTURAL_APPROPRIATENESS = "cultural_appropriateness"
    TECHNICAL_QUALITY = "technical_quality"
    AUDIO_CLARITY = "audio_clarity"
    PRONUNCIATION = "pronunciation"


class Validation(BaseModel):
    """
    Validation model for community reviews.

    Represents quality reviews by community validators.
    """

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    validator_id: PyObjectId = Field(..., description="User performing validation")
    submission_id: PyObjectId = Field(..., description="Submission being validated")
    submission_type: str = Field(..., description="Type of submission")

    # Validation decision
    action: ValidationAction = Field(..., description="Validation action taken")
    category: ValidationCategory = Field(..., description="Primary validation category")

    # Quality assessment
    quality_rating: int = Field(..., ge=1, le=5, description="Overall quality rating (1-5)")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Validator confidence")

    # Detailed feedback
    comments: Optional[str] = Field(None, description="Validation comments")
    specific_issues: List[str] = Field(default=[], description="Specific issues identified")
    suggested_corrections: Optional[str] = Field(None, description="Suggested corrections")

    # Technical validation (for audio/video)
    audio_quality: Optional[int] = Field(None, ge=1, le=5, description="Audio quality rating")
    pronunciation_accuracy: Optional[int] = Field(None, ge=1, le=5, description="Pronunciation accuracy")

    # Cultural validation
    cultural_accuracy: Optional[int] = Field(None, ge=1, le=5, description="Cultural accuracy rating")

    # Metadata
    time_spent_seconds: Optional[int] = Field(None, description="Time spent validating")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class ValidationCreate(BaseModel):
    """Request model for creating validations."""

    submission_id: str
    submission_type: str
    action: ValidationAction
    category: ValidationCategory
    quality_rating: int = Field(..., ge=1, le=5)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    comments: Optional[str] = None
    specific_issues: List[str] = []
    suggested_corrections: Optional[str] = None
    audio_quality: Optional[int] = Field(None, ge=1, le=5)
    pronunciation_accuracy: Optional[int] = Field(None, ge=1, le=5)
    cultural_accuracy: Optional[int] = Field(None, ge=1, le=5)
    time_spent_seconds: Optional[int] = None


class ValidationSummary(BaseModel):
    """Summary of validations for a submission."""

    submission_id: str
    total_validations: int
    average_quality_rating: float
    approval_percentage: float
    rejection_percentage: float
    flag_percentage: float
    consensus_reached: bool
    recommended_action: str
    top_issues: List[str]
    validator_levels: Dict[str, int]


class ValidationStats(BaseModel):
    """Statistics for validation activity."""

    total_validations: int
    by_action: Dict[ValidationAction, int]
    by_category: Dict[ValidationCategory, int]
    average_quality_rating: float
    average_time_spent: float
    top_validators: List[Dict[str, Any]]
    quality_trends: List[Dict[str, Any]]