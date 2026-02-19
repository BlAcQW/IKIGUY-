"""
Submission and validation models for African Language Community Platform.

Pydantic models for data submissions, quality validation, and community contributions.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from models.language_models import PyObjectId


class SubmissionType(str, Enum):
    """Types of data submissions."""

    AUDIO = "audio"
    TEXT = "text"
    LINK = "link"
    IMAGE = "image"
    VIDEO = "video"


class QualityTier(str, Enum):
    """Quality tiers for submissions."""

    TIER_1_VALIDATED = "tier-1-validated"  # Gold standard (3+ validators)
    TIER_2_REVIEWED = "tier-2-reviewed"    # Community reviewed (2 validators)
    TIER_3_SUBMITTED = "tier-3-submitted"  # Raw submissions


class ValidationStatus(str, Enum):
    """Validation status for submissions."""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    VALIDATED = "validated"
    REJECTED = "rejected"
    NEEDS_IMPROVEMENT = "needs_improvement"


class ContentCategory(str, Enum):
    """Categories for text/audio content."""

    STORY = "story"
    PROVERB = "proverb"
    SONG = "song"
    CONVERSATION = "conversation"
    NEWS = "news"
    EDUCATIONAL = "educational"
    RELIGIOUS = "religious"
    CULTURAL = "cultural"
    TECHNICAL = "technical"
    OTHER = "other"


class Submission(BaseModel):
    """
    Data submission model.

    Represents any type of data contribution from community members.
    """

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    contributor_id: PyObjectId = Field(..., description="User who submitted the data")

    # Language information
    language_family: Optional[str] = Field(None, description="Language family (e.g., 'niger-congo')")
    language_subfamily: Optional[str] = Field(None, description="Language subfamily")
    language_code: str = Field(..., description="ISO 639-3 language code")
    dialect: Optional[str] = Field(None, description="Specific dialect if applicable")

    # Submission details
    type: SubmissionType = Field(..., description="Type of submission")
    category: Optional[ContentCategory] = Field(None, description="Content category")
    title: str = Field(..., description="Submission title")
    description: Optional[str] = Field(None, description="Detailed description")

    # File information (for audio/video/image)
    file_url: Optional[str] = Field(None, description="URL to uploaded file")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    file_format: Optional[str] = Field(None, description="File format/extension")
    duration_seconds: Optional[float] = Field(None, description="Audio/video duration")

    # Text content (for text submissions)
    text_content: Optional[str] = Field(None, description="Text content")
    translation: Optional[str] = Field(None, description="English translation")
    transliteration: Optional[str] = Field(None, description="Romanized version")

    # Link information (for link submissions)
    external_url: Optional[str] = Field(None, description="External resource URL")
    source_attribution: Optional[str] = Field(None, description="Source attribution")

    # Quality and validation
    tier: QualityTier = Field(default=QualityTier.TIER_3_SUBMITTED)
    validation_status: ValidationStatus = Field(default=ValidationStatus.PENDING)
    quality_scores: Dict[str, float] = Field(default={}, description="Various quality metrics")
    automated_scores: Dict[str, float] = Field(default={}, description="AI quality assessment")

    # Cultural context
    cultural_context: Optional[str] = Field(None, description="Cultural significance/context")
    usage_context: Optional[str] = Field(None, description="How/when it's typically used")
    cultural_appropriateness: Optional[float] = Field(None, description="Cultural appropriateness score")

    # Technical metadata
    technical_metadata: Dict[str, Any] = Field(
        default={}, description="Technical information (sample rate, encoding, etc.)"
    )
    processing_notes: List[str] = Field(
        default=[], description="Processing and enhancement notes"
    )

    # Community interaction
    view_count: int = Field(default=0)
    upvotes: int = Field(default=0)
    downvotes: int = Field(default=0)
    comments_count: int = Field(default=0)

    # Moderation
    is_flagged: bool = Field(default=False)
    flag_reasons: List[str] = Field(default=[], description="Reasons for flagging")
    moderation_notes: Optional[str] = Field(None)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}

    @validator('file_url')
    def validate_file_url(cls, v, values):
        """Ensure file URL is provided for file-based submissions."""
        submission_type = values.get('type')
        if submission_type in [SubmissionType.AUDIO, SubmissionType.IMAGE, SubmissionType.VIDEO]:
            if not v:
                raise ValueError(f"file_url is required for {submission_type} submissions")
        return v

    @validator('text_content')
    def validate_text_content(cls, v, values):
        """Ensure text content is provided for text submissions."""
        if values.get('type') == SubmissionType.TEXT and not v:
            raise ValueError("text_content is required for text submissions")
        return v

    @validator('external_url')
    def validate_external_url(cls, v, values):
        """Ensure external URL is provided for link submissions."""
        if values.get('type') == SubmissionType.LINK and not v:
            raise ValueError("external_url is required for link submissions")
        return v


class SubmissionCreate(BaseModel):
    """Request model for creating submissions."""

    language_code: str
    language_family: Optional[str] = None  # Optional, can be inferred from language_code
    type: SubmissionType
    title: str
    description: Optional[str] = None
    category: Optional[ContentCategory] = None
    dialect: Optional[str] = None

    # Optional fields based on type
    text_content: Optional[str] = None
    translation: Optional[str] = None
    external_url: Optional[str] = None
    cultural_context: Optional[str] = None
    usage_context: Optional[str] = None
    source_attribution: Optional[str] = None


class SubmissionUpdate(BaseModel):
    """Request model for updating submissions."""

    title: Optional[str] = None
    description: Optional[str] = None
    text_content: Optional[str] = None
    translation: Optional[str] = None
    cultural_context: Optional[str] = None
    usage_context: Optional[str] = None


class Validation(BaseModel):
    """
    Validation review model.

    Represents quality reviews by community validators.
    """

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    submission_id: PyObjectId = Field(..., description="Submission being validated")
    validator_id: PyObjectId = Field(..., description="User performing validation")

    # Quality scores (1-10 scale)
    quality_score: float = Field(..., ge=1.0, le=10.0, description="Overall quality score")
    technical_quality: Optional[float] = Field(None, ge=1.0, le=10.0, description="Technical quality")
    linguistic_accuracy: Optional[float] = Field(None, ge=1.0, le=10.0, description="Linguistic accuracy")
    cultural_appropriateness: Optional[float] = Field(None, ge=1.0, le=10.0, description="Cultural appropriateness")
    audio_clarity: Optional[float] = Field(None, ge=1.0, le=10.0, description="Audio clarity (for audio)")
    pronunciation_accuracy: Optional[float] = Field(None, ge=1.0, le=10.0, description="Pronunciation accuracy")

    # Detailed feedback
    feedback: Optional[str] = Field(None, description="Detailed validation feedback")
    strengths: List[str] = Field(default=[], description="Identified strengths")
    improvements_needed: List[str] = Field(default=[], description="Suggested improvements")

    # Validation aspects
    validation_aspects: Dict[str, Any] = Field(
        default={}, description="Specific validation criteria checked"
    )

    # Decision
    recommendation: str = Field(..., description="Validation recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Validator confidence")

    # Metadata
    time_spent_minutes: Optional[int] = Field(None, description="Time spent on validation")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class ValidationCreate(BaseModel):
    """Request model for creating validations."""

    quality_score: float = Field(..., ge=1.0, le=10.0)
    technical_quality: Optional[float] = Field(None, ge=1.0, le=10.0)
    linguistic_accuracy: Optional[float] = Field(None, ge=1.0, le=10.0)
    cultural_appropriateness: Optional[float] = Field(None, ge=1.0, le=10.0)
    audio_clarity: Optional[float] = Field(None, ge=1.0, le=10.0)
    pronunciation_accuracy: Optional[float] = Field(None, ge=1.0, le=10.0)
    feedback: Optional[str] = None
    strengths: List[str] = []
    improvements_needed: List[str] = []
    recommendation: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    time_spent_minutes: Optional[int] = None


class ValidationSummary(BaseModel):
    """Summary of validations for a submission."""

    submission_id: str
    total_validations: int
    average_quality_score: float
    consensus_level: float
    tier_eligible: QualityTier
    validation_complete: bool
    next_action: str
    validator_breakdown: List[Dict[str, Any]]


class SubmissionStats(BaseModel):
    """Statistics for submissions."""

    total_submissions: int
    by_type: Dict[SubmissionType, int]
    by_tier: Dict[QualityTier, int]
    by_status: Dict[ValidationStatus, int]
    by_language: Dict[str, int]
    recent_submissions: List[Dict[str, Any]]
    top_contributors: List[Dict[str, Any]]
    quality_trends: List[Dict[str, Any]]