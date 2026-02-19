"""
Platform settings models for admin configuration.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


class EmailSettings(BaseModel):
    """Email configuration settings."""

    smtp_host: str = Field(..., min_length=1)
    smtp_port: int = Field(..., ge=1, le=65535)
    smtp_username: str = Field(..., min_length=1)
    smtp_password: str = Field(..., min_length=1)
    smtp_use_tls: bool = True
    from_email: EmailStr
    from_name: str = Field(..., min_length=1)


class NotificationSettings(BaseModel):
    """Notification configuration settings."""

    enable_email_notifications: bool = True
    enable_push_notifications: bool = True
    enable_daily_devotional_reminders: bool = True
    reminder_time: str = Field("08:00", pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    enable_comment_notifications: bool = True
    enable_like_notifications: bool = True
    
    # Subscription drip feed settings
    enable_subscription_drip_feed: bool = True
    subscription_drip_feed_time: str = Field("08:00", pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", description="Time (UTC) to send daily devotionals to subscribers (HH:MM format)")
    subscription_drip_feed_timezone: str = Field("UTC", description="Timezone for drip feed (e.g., UTC, America/New_York)")


class ContentModerationSettings(BaseModel):
    """Content moderation configuration settings."""

    auto_approve_devotionals: bool = False
    require_pastor_verification: bool = True
    enable_profanity_filter: bool = True
    enable_spam_detection: bool = True
    min_devotional_length: int = Field(100, ge=50)
    max_devotional_length: int = Field(5000, ge=100)


class UserManagementSettings(BaseModel):
    """User management configuration settings."""

    allow_public_signup: bool = True
    require_email_verification: bool = True
    allow_pastor_self_registration: bool = False
    auto_approve_pastors: bool = False
    max_failed_login_attempts: int = Field(5, ge=3, le=10)
    account_lockout_duration_minutes: int = Field(30, ge=5, le=1440)


class PlatformSettings(BaseModel):
    """Complete platform settings."""

    # Platform Info
    platform_name: str = Field("FreshManna", min_length=1, max_length=100)
    platform_description: Optional[str] = Field(None, max_length=500)
    platform_logo_url: Optional[str] = None
    support_email: EmailStr
    contact_phone: Optional[str] = None

    # Feature Flags
    enable_ai_features: bool = True
    enable_audio_devotionals: bool = True
    enable_comments: bool = True
    enable_likes: bool = True
    enable_sharing: bool = True

    # Email Settings
    email: EmailSettings

    # Notification Settings
    notifications: NotificationSettings

    # Content Moderation Settings
    moderation: ContentModerationSettings

    # User Management Settings
    users: UserManagementSettings

    # Metadata
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None  # Admin user ID


class PlatformSettingsUpdate(BaseModel):
    """Model for updating platform settings."""

    # Platform Info
    platform_name: Optional[str] = Field(None, min_length=1, max_length=100)
    platform_description: Optional[str] = Field(None, max_length=500)
    platform_logo_url: Optional[str] = None
    support_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None

    # Feature Flags
    enable_ai_features: Optional[bool] = None
    enable_audio_devotionals: Optional[bool] = None
    enable_comments: Optional[bool] = None
    enable_likes: Optional[bool] = None
    enable_sharing: Optional[bool] = None

    # Email Settings
    email: Optional[EmailSettings] = None

    # Notification Settings
    notifications: Optional[NotificationSettings] = None

    # Content Moderation Settings
    moderation: Optional[ContentModerationSettings] = None

    # User Management Settings
    users: Optional[UserManagementSettings] = None


class PlatformSettingsResponse(BaseModel):
    """Response model for platform settings."""

    settings: PlatformSettings
    last_updated: datetime
    last_updated_by: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}
