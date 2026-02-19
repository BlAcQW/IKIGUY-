"""
Community models for African Language Community Platform.

Pydantic models for community features like achievements, badges, and statistics.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from models.language_models import PyObjectId


class AchievementType(str, Enum):
    """Types of achievements users can earn."""

    FIRST_SUBMISSION = "first_submission"
    FIRST_VALIDATION = "first_validation"
    CONTRIBUTOR_LEVEL = "contributor_level"
    VALIDATOR_LEVEL = "validator_level"
    EXPERT_LEVEL = "expert_level"
    QUALITY_CONTRIBUTOR = "quality_contributor"
    CULTURAL_EXPERT = "cultural_expert"
    MULTILINGUAL = "multilingual"
    COMMUNITY_BUILDER = "community_builder"
    TOP_CONTRIBUTOR = "top_contributor"


class BadgeType(str, Enum):
    """Types of badges users can earn."""

    BRONZE_CONTRIBUTOR = "bronze_contributor"
    SILVER_CONTRIBUTOR = "silver_contributor"
    GOLD_CONTRIBUTOR = "gold_contributor"
    QUALITY_VALIDATOR = "quality_validator"
    CULTURAL_GUARDIAN = "cultural_guardian"
    LINGUISTIC_EXPERT = "linguistic_expert"
    COMMUNITY_CHAMPION = "community_champion"
    PIONEER = "pioneer"


class Achievement(BaseModel):
    """Achievement model for user accomplishments."""

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="User who earned the achievement")
    type: AchievementType = Field(..., description="Type of achievement")
    title: str = Field(..., description="Achievement title")
    description: str = Field(..., description="Achievement description")
    icon_url: Optional[str] = Field(None, description="Achievement icon URL")
    points_awarded: int = Field(default=0, description="Points awarded for achievement")

    # Metadata
    earned_at: datetime = Field(default_factory=datetime.utcnow)
    language_specific: Optional[str] = Field(None, description="Language code if language-specific")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class Badge(BaseModel):
    """Badge model for user recognition."""

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="User who earned the badge")
    type: BadgeType = Field(..., description="Type of badge")
    title: str = Field(..., description="Badge title")
    description: str = Field(..., description="Badge description")
    icon_url: str = Field(..., description="Badge icon URL")
    level: int = Field(default=1, description="Badge level (for tiered badges)")

    # Requirements
    requirements_met: Dict[str, Any] = Field(default={}, description="Requirements that were met")

    # Metadata
    earned_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="Badge expiration date")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class LeaderboardEntry(BaseModel):
    """Individual entry in a leaderboard."""

    user_id: str
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    rank: int
    score: float
    level: str
    badge_count: int
    achievement_count: int
    recent_activity: Optional[datetime]


class Leaderboard(BaseModel):
    """Leaderboard model for community rankings."""

    category: str = Field(..., description="Leaderboard category")
    timeframe: str = Field(..., description="Time frame (weekly, monthly, all_time)")
    language_filter: Optional[str] = Field(None, description="Language filter")
    entries: List[LeaderboardEntry] = Field(..., description="Leaderboard entries")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    total_participants: int = Field(..., description="Total number of participants")


class CommunityStats(BaseModel):
    """Community statistics model."""

    # User statistics
    total_users: int = 0
    active_users: int = 0
    new_users_this_month: int = 0

    # Contribution statistics
    total_contributions: int = 0
    total_validations: int = 0
    contributions_this_month: int = 0
    validations_this_month: int = 0

    # Language statistics
    total_languages: int = 0
    active_languages: int = 0

    # Submission statistics
    text_submissions: int = 0
    audio_submissions: int = 0
    translation_submissions: int = 0
    gold_standard_submissions: int = 0
    pending_submissions: int = 0

    # Quality statistics
    average_quality_score: float = 0.0
    validation_completion_rate: float = 0.0

    # Engagement statistics
    daily_active_users: int = 0
    weekly_active_users: int = 0
    monthly_active_users: int = 0

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    language_filter: Optional[str] = None


class ActivityFeed(BaseModel):
    """Activity feed model for community updates."""

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="User who performed the activity")
    activity_type: str = Field(..., description="Type of activity")
    description: str = Field(..., description="Activity description")

    # Related entities
    submission_id: Optional[PyObjectId] = Field(None, description="Related submission")
    language_code: Optional[str] = Field(None, description="Related language")

    # Activity data
    metadata: Dict[str, Any] = Field(default={}, description="Additional activity metadata")
    points_earned: int = Field(default=0, description="Points earned from activity")

    # Visibility
    is_public: bool = Field(default=True, description="Whether activity is publicly visible")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class CommunityChallenge(BaseModel):
    """Community challenge model for engagement."""

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    title: str = Field(..., description="Challenge title")
    description: str = Field(..., description="Challenge description")

    # Challenge parameters
    target_metric: str = Field(..., description="Target metric (submissions, validations, etc.)")
    target_value: int = Field(..., description="Target value to achieve")
    language_filter: Optional[str] = Field(None, description="Language-specific challenge")

    # Rewards
    points_reward: int = Field(default=0, description="Points reward for completion")
    badge_reward: Optional[BadgeType] = Field(None, description="Badge reward")

    # Status
    is_active: bool = Field(default=True)
    participants: List[PyObjectId] = Field(default=[], description="Participating users")
    completed_by: List[PyObjectId] = Field(default=[], description="Users who completed")

    # Timing
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: datetime = Field(..., description="Challenge end date")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}