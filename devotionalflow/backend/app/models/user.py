"""
User models for authentication and profile management.
Supports two roles: User (regular user) and Admin (administrator).
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic_core import core_schema
from typing import Optional, Literal, Any, List
from datetime import datetime
from bson import ObjectId


class PyObjectId(str):
    """Custom type for MongoDB ObjectId in Pydantic V2 models."""

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler):
        """Define how Pydantic should validate this type."""
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v):
        """Validate and convert to ObjectId."""
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError(f"Invalid ObjectId: {v}")


class ReadingPreferences(BaseModel):
    """User reading preferences."""

    font_size: Literal["small", "medium", "large"] = "medium"
    theme: Literal["light", "sepia", "dark"] = "light"
    line_height: Literal["compact", "normal", "relaxed"] = "normal"
    notification_time: str = "08:00"  # HH:MM format
    notifications_enabled: bool = True


class PrivacySettings(BaseModel):
    """User privacy settings."""

    profile_visibility: Literal["public", "private"] = "public"
    show_reading_history: bool = True
    show_bookmarks: bool = True
    show_email: bool = False
    show_activity: bool = True
    allow_comments_on_activity: bool = True
    marketing_emails: bool = True
    announcement_emails: bool = True
    notifications_enabled: bool = True


class UserBase(BaseModel):
    """Base user model with common fields."""

    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    role: Literal["user", "admin"] = "user"
    avatar_url: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)


class UserCreate(UserBase):
    """Model for user registration."""

    password: str = Field(..., min_length=8, max_length=100)

    # Optional profile fields
    ministry_name: Optional[str] = Field(None, max_length=200)
    ministry_website: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """Ensure password meets security requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """Model for user login."""

    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Model for updating user profile."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    avatar_url: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    ministry_name: Optional[str] = Field(None, max_length=200)
    ministry_website: Optional[str] = None
    reading_preferences: Optional[ReadingPreferences] = None
    privacy_settings: Optional[PrivacySettings] = None


class UserInDB(UserBase):
    """User model as stored in MongoDB."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    password_hash: str

    # Optional profile fields
    ministry_name: Optional[str] = None
    ministry_website: Optional[str] = None
    subscription_plan: Literal["free", "pro", "ministry"] = "free"
    subscription_expires_at: Optional[datetime] = None

    # User engagement fields
    reading_streak: int = 0
    reading_preferences: ReadingPreferences = Field(default_factory=ReadingPreferences)
    privacy_settings: PrivacySettings = Field(default_factory=PrivacySettings)

    # User status
    is_active: bool = True
    is_suspended: bool = False
    last_active: Optional[datetime] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class UserResponse(BaseModel):
    """User model for API responses (without sensitive data)."""

    id: str
    email: EmailStr
    name: str
    role: Literal["user", "admin"] = "user"
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

    # Optional profile fields
    ministry_name: Optional[str] = None
    ministry_website: Optional[str] = None
    subscription_plan: Optional[Literal["free", "pro", "ministry"]] = None

    # User engagement fields
    reading_streak: Optional[int] = None
    reading_preferences: Optional[ReadingPreferences] = None
    privacy_settings: Optional[PrivacySettings] = None

    # User status
    is_active: Optional[bool] = True
    is_suspended: Optional[bool] = False
    last_active: Optional[datetime] = None

    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class Token(BaseModel):
    """JWT token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Data stored in JWT token."""

    user_id: str
    email: str
    role: str
    exp: Optional[int] = None


class PasswordReset(BaseModel):
    """Model for password reset request."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Model for password reset confirmation."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        """Ensure password meets security requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserRoleUpdate(BaseModel):
    """Model for updating user role (admin only)."""

    role: Literal["user", "admin"]


class UserStatusUpdate(BaseModel):
    """Model for updating user status (admin only)."""

    is_suspended: bool


class UserListFilters(BaseModel):
    """Query parameters for filtering users."""

    role: Optional[Literal["user", "admin"]] = None
    is_suspended: Optional[bool] = None
    search: Optional[str] = None  # Search by name or email
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: Literal["created_at", "name", "email", "last_active"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"


class UserStatsResponse(BaseModel):
    """Response model for user statistics with devotional count."""

    id: str
    email: EmailStr
    name: str
    role: Literal["user", "admin"] = "user"
    avatar_url: Optional[str] = None
    is_active: bool
    is_suspended: bool
    last_active: Optional[datetime] = None
    created_at: datetime

    # Additional stats
    devotionals_count: int = 0  # For content creators

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class UserListResponse(BaseModel):
    """Response model for list of users with pagination."""

    users: List[UserStatsResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
