"""
Community governance models for dispute resolution and content moderation.

Handles disputes, content reports, moderation actions, and community guidelines.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId


class DisputeType(str, Enum):
    """Types of disputes that can be raised."""
    VALIDATION_DISAGREEMENT = "validation_disagreement"
    QUALITY_DISPUTE = "quality_dispute"
    CULTURAL_ACCURACY = "cultural_accuracy"
    COPYRIGHT_CLAIM = "copyright_claim"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    SPAM_REPORT = "spam_report"
    USER_CONDUCT = "user_conduct"


class DisputeStatus(str, Enum):
    """Status of a dispute."""
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class ModerationAction(str, Enum):
    """Types of moderation actions."""
    WARNING = "warning"
    TEMPORARY_SUSPENSION = "temporary_suspension"
    PERMANENT_BAN = "permanent_ban"
    CONTENT_REMOVAL = "content_removal"
    QUALITY_DOWNGRADE = "quality_downgrade"
    POINTS_DEDUCTION = "points_deduction"
    REINSTATEMENT = "reinstatement"


class DisputeCreate(BaseModel):
    """Model for creating a new dispute."""
    dispute_type: DisputeType
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20, max_length=2000)
    related_submission_id: Optional[str] = None
    related_user_id: Optional[str] = None
    evidence_urls: List[str] = []
    language_code: Optional[str] = None
    priority: int = Field(default=3, ge=1, le=5)  # 1=highest, 5=lowest

    @validator('evidence_urls')
    def validate_evidence_urls(cls, v):
        """Validate evidence URLs."""
        if len(v) > 10:
            raise ValueError("Maximum 10 evidence URLs allowed")
        return v


class DisputeUpdate(BaseModel):
    """Model for updating an existing dispute."""
    status: Optional[DisputeStatus] = None
    moderator_notes: Optional[str] = None
    resolution: Optional[str] = None
    assigned_moderator_id: Optional[str] = None


class Dispute(BaseModel):
    """Complete dispute model."""
    id: str = Field(alias="_id")
    dispute_type: DisputeType
    title: str
    description: str
    status: DisputeStatus = DisputeStatus.OPEN
    priority: int

    # Related entities
    reporter_id: str
    related_submission_id: Optional[str] = None
    related_user_id: Optional[str] = None
    assigned_moderator_id: Optional[str] = None

    # Content
    evidence_urls: List[str] = []
    language_code: Optional[str] = None

    # Resolution
    resolution: Optional[str] = None
    moderator_notes: Optional[str] = None
    moderation_actions: List[Dict[str, Any]] = []

    # Metadata
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    escalated_at: Optional[datetime] = None

    # Community voting
    community_votes: Dict[str, int] = {}  # {user_id: vote} where vote is -1, 0, 1

    class Config:
        populate_by_name = True


class ContentReportCreate(BaseModel):
    """Model for creating a content report."""
    content_type: str = Field(..., pattern="^(submission|comment|profile|message)$")
    content_id: str
    report_reason: str = Field(..., min_length=10, max_length=500)
    category: str = Field(..., pattern="^(spam|inappropriate|copyright|quality|other)$")
    severity: int = Field(..., ge=1, le=5)  # 1=low, 5=critical


class ContentReport(BaseModel):
    """Complete content report model."""
    id: str = Field(alias="_id")
    content_type: str
    content_id: str
    reporter_id: str
    report_reason: str
    category: str
    severity: int
    status: str = "pending"  # pending, reviewed, resolved, dismissed
    reviewer_id: Optional[str] = None
    review_notes: Optional[str] = None
    action_taken: Optional[ModerationAction] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class ModerationActionCreate(BaseModel):
    """Model for creating a moderation action."""
    action_type: ModerationAction
    target_user_id: str
    target_content_id: Optional[str] = None
    reason: str = Field(..., min_length=10, max_length=1000)
    duration_hours: Optional[int] = None  # For temporary actions
    points_affected: Optional[int] = None  # For point deductions
    internal_notes: Optional[str] = None


class ModerationActionRecord(BaseModel):
    """Complete moderation action record."""
    id: str = Field(alias="_id")
    action_type: ModerationAction
    moderator_id: str
    target_user_id: str
    target_content_id: Optional[str] = None
    reason: str
    duration_hours: Optional[int] = None
    points_affected: Optional[int] = None
    internal_notes: Optional[str] = None

    # Status tracking
    is_active: bool = True
    executed_at: datetime
    expires_at: Optional[datetime] = None
    reversed_at: Optional[datetime] = None
    reversed_by: Optional[str] = None
    reverse_reason: Optional[str] = None

    # Related dispute
    related_dispute_id: Optional[str] = None

    class Config:
        populate_by_name = True


class GuidelineViolation(BaseModel):
    """Model for tracking guideline violations."""
    id: str = Field(alias="_id")
    user_id: str
    violation_type: str
    description: str
    severity: int = Field(..., ge=1, le=5)
    reported_by: str
    reviewed_by: Optional[str] = None
    status: str = "pending"  # pending, confirmed, dismissed

    # Consequences
    warning_issued: bool = False
    points_deducted: int = 0
    suspension_hours: int = 0

    created_at: datetime
    reviewed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class CommunityGuideline(BaseModel):
    """Model for community guidelines."""
    id: str = Field(alias="_id")
    title: str
    description: str
    category: str
    severity_level: int = Field(..., ge=1, le=5)
    examples: List[str] = []
    consequences: List[str] = []
    language_specific: bool = False
    target_languages: List[str] = []

    # Version control
    version: str = "1.0"
    created_by: str
    approved_by: List[str] = []

    created_at: datetime
    updated_at: datetime
    effective_date: datetime

    # Status
    is_active: bool = True

    class Config:
        populate_by_name = True


# Response models
class DisputeStats(BaseModel):
    """Statistics for disputes."""
    total_disputes: int
    open_disputes: int
    resolved_disputes: int
    average_resolution_time_hours: float
    disputes_by_type: Dict[str, int]
    disputes_by_language: Dict[str, int]


class ModerationStats(BaseModel):
    """Statistics for moderation actions."""
    total_actions: int
    actions_by_type: Dict[str, int]
    active_suspensions: int
    points_deducted_total: int
    content_removed_total: int
    average_response_time_hours: float