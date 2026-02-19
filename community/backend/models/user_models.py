"""
User and authentication models for African Language Community Platform.

Pydantic models for users, authentication, and community roles.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from models.language_models import PyObjectId


class UserLevel(str, Enum):
    """User levels in the community hierarchy."""

    NEWCOMER = "newcomer"
    CONTRIBUTOR = "contributor"
    VALIDATOR = "validator"
    EXPERT = "expert"
    GUARDIAN = "guardian"


class ValidatorSpecialization(str, Enum):
    """Validator specialization areas."""

    NATIVE_SPEAKER = "native_speaker"
    LINGUISTIC_EXPERT = "linguistic_expert"
    CULTURAL_AUTHORITY = "cultural_authority"
    TECHNICAL_REVIEWER = "technical_reviewer"
    AUDIO_SPECIALIST = "audio_specialist"


class User(BaseModel):
    """
    User model for community members.

    Represents platform users with roles, expertise, and gamification data.
    """

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    supabase_id: Optional[str] = Field(None, description="Supabase user ID (legacy)")
    email: EmailStr = Field(..., description="User email address")
    username: Optional[str] = Field(None, description="Unique username")
    full_name: Optional[str] = Field(None, description="Full display name")
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")

    # Community profile
    bio: Optional[str] = Field(None, description="User biography")
    location: Optional[str] = Field(None, description="Geographic location")
    languages_spoken: List[str] = Field(default=[], description="Languages user speaks")

    # Community status and gamification
    level: UserLevel = Field(default=UserLevel.NEWCOMER)
    total_points: int = Field(default=0)
    level_points: int = Field(default=0, description="Points in current level")
    achievements: List[str] = Field(default=[], description="Achievement IDs")
    badges: List[str] = Field(default=[], description="Special badges earned")

    # Language expertise
    language_expertise: List[Dict[str, Any]] = Field(
        default=[], description="Language proficiency and expertise areas"
    )
    validator_qualifications: List[ValidatorSpecialization] = Field(
        default=[], description="Validation specializations"
    )
    verified_languages: List[str] = Field(
        default=[], description="Languages user is verified to validate"
    )

    # Community permissions and role
    role: str = Field(default="user", description="User role: user, moderator, admin")
    permissions: List[str] = Field(default=[], description="User permissions")
    can_validate: bool = Field(default=False)
    can_moderate: bool = Field(default=False)
    can_create_proposals: bool = Field(default=False)

    # Statistics
    contributions_count: int = Field(default=0)
    validations_count: int = Field(default=0)
    quality_rating: float = Field(default=0.0, description="Average quality score")
    reputation_score: int = Field(default=0)

    # Account status
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    email_verified: bool = Field(default=False)
    phone_verified: bool = Field(default=False)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    last_activity: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class UserCreate(BaseModel):
    """Request model for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=6, description="User password (min 6 characters)")
    full_name: Optional[str] = None
    username: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    languages_spoken: List[str] = []
    language_expertise: List[Dict[str, Any]] = []


class UserUpdate(BaseModel):
    """Request model for updating user profile."""

    full_name: Optional[str] = None
    username: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    avatar_url: Optional[str] = None
    languages_spoken: List[str] = []
    language_expertise: List[Dict[str, Any]] = []


class UserAuth(BaseModel):
    """Authentication response model."""

    user: User
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class UserProfile(BaseModel):
    """Public user profile model."""

    id: str
    username: Optional[str]
    full_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    level: UserLevel
    total_points: int
    achievements: List[str]
    badges: List[str]
    verified_languages: List[str]
    contributions_count: int
    validations_count: int
    quality_rating: float
    reputation_score: int
    member_since: datetime


class Achievement(BaseModel):
    """User achievement model."""

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="User who earned achievement")
    achievement_type: str = Field(..., description="Type of achievement")
    achievement_id: str = Field(..., description="Achievement identifier")
    title: str = Field(..., description="Achievement title")
    description: str = Field(..., description="Achievement description")
    icon: Optional[str] = Field(None, description="Achievement icon/emoji")
    rarity: str = Field(default="common", description="Achievement rarity level")
    points_awarded: int = Field(default=0, description="Points awarded for achievement")
    metadata: Dict[str, Any] = Field(default={}, description="Additional achievement data")
    awarded_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class Leaderboard(BaseModel):
    """Leaderboard entry model."""

    rank: int
    user_id: str
    username: Optional[str]
    full_name: Optional[str]
    avatar_url: Optional[str]
    points: int
    contributions: int
    avg_quality: float
    badges: List[str]
    level: UserLevel


class ValidatorApplication(BaseModel):
    """Validator application model."""

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="Applicant user ID")
    languages: List[str] = Field(..., description="Languages to validate")
    specializations: List[ValidatorSpecialization] = Field(
        ..., description="Validation specializations"
    )
    qualifications: str = Field(..., description="Qualification details")
    native_speaker_proof: Optional[str] = Field(None, description="Native speaker evidence")
    experience_description: str = Field(..., description="Relevant experience")
    references: List[str] = Field(default=[], description="References or endorsements")
    status: str = Field(default="pending", description="Application status")
    reviewed_by: Optional[PyObjectId] = Field(None)
    review_notes: Optional[str] = Field(None)
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}