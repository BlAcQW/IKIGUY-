"""
Notification models for InkWave.

Defines in-app notifications for achievements, streaks, and social activities.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class NotificationType(str, Enum):
    """Notification types."""
    ACHIEVEMENT_EARNED = "achievement_earned"
    STREAK_MILESTONE = "streak_milestone"
    STREAK_REMINDER = "streak_reminder"
    STREAK_BROKEN = "streak_broken"
    LEADERBOARD_POSITION = "leaderboard_position"
    SOCIAL_FOLLOW = "social_follow"
    SOCIAL_MENTION = "social_mention"
    BOOK_RECOMMENDATION = "book_recommendation"
    SYSTEM_ANNOUNCEMENT = "system_announcement"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Notification(BaseModel):
    """
    In-app notification.

    Sent to users for achievements, streaks, social activities, etc.
    """

    notification_id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    user_id: str = Field(..., description="Recipient user ID")

    # Notification content
    type: NotificationType = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message body")
    priority: NotificationPriority = Field(default=NotificationPriority.MEDIUM)

    # Actions
    action_url: Optional[str] = Field(None, description="URL to navigate to on click")
    action_label: Optional[str] = Field(None, description="Action button label")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context data")

    # Status
    is_read: bool = Field(default=False, description="Whether notification was read")
    is_delivered: bool = Field(default=False, description="Whether push notification was delivered")
    read_at: Optional[datetime] = Field(None, description="When notification was read")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="When notification expires (optional)")

    class Config:
        """Pydantic config."""
        use_enum_values = True


class NotificationInDB(Notification):
    """Notification model with MongoDB _id."""
    id: Optional[str] = Field(None, alias="_id")

    class Config:
        """Pydantic config."""
        populate_by_name = True
        use_enum_values = True


class NotificationPreferences(BaseModel):
    """
    User notification preferences.

    Controls which notifications to receive and delivery channels.
    """

    # Achievement notifications
    achievement_earned: bool = Field(default=True, description="New achievement earned")
    achievement_progress: bool = Field(default=False, description="Achievement progress milestones")

    # Streak notifications
    streak_milestones: bool = Field(default=True, description="Streak milestones (7, 30, 100 days)")
    streak_reminders: bool = Field(default=True, description="Daily reminder to maintain streak")
    streak_broken: bool = Field(default=True, description="Notification when streak is broken")

    # Leaderboard notifications
    leaderboard_position: bool = Field(default=True, description="Position changes in leaderboard")
    leaderboard_summary: bool = Field(default=True, description="Weekly leaderboard summary")

    # Social notifications
    social_follows: bool = Field(default=True, description="New follower")
    social_mentions: bool = Field(default=True, description="Mentions in comments/reviews")

    # Content recommendations
    book_recommendations: bool = Field(default=True, description="Personalized book recommendations")

    # System notifications
    system_announcements: bool = Field(default=True, description="Important system announcements")

    # Delivery channels
    in_app: bool = Field(default=True, description="In-app notifications")
    push: bool = Field(default=True, description="Push notifications (mobile)")
    email: bool = Field(default=False, description="Email notifications")
    email_digest: bool = Field(default=True, description="Weekly email digest")

    # Quiet hours
    quiet_hours_enabled: bool = Field(default=False, description="Enable quiet hours")
    quiet_hours_start: Optional[str] = Field(None, description="Start time (HH:MM, 24h format)")
    quiet_hours_end: Optional[str] = Field(None, description="End time (HH:MM, 24h format)")

    # Metadata
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationBatch(BaseModel):
    """Batch of notifications for efficient delivery."""
    user_id: str
    notifications: list[Notification]
    total_unread: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
