"""
Push notification models for DevotionalFlow.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class PushSubscriptionCreate(BaseModel):
    """Push subscription creation model."""
    endpoint: str
    keys: Dict[str, str] = Field(..., description="Web Push keys (p256dh and auth)")
    user_agent: Optional[str] = None


class AnnouncementCreate(BaseModel):
    """Custom announcement creation model."""
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=500)
    segments: List[str] = Field(default_factory=list, description="Target segments (e.g., 'all_users', 'active_readers')")
    user_ids: Optional[List[str]] = Field(None, description="Specific user IDs (optional)")
    scheduled_at: Optional[str] = Field(None, description="ISO datetime string for scheduling")
    data: Optional[Dict[str, Any]] = None


class AnnouncementResponse(BaseModel):
    """Announcement response model."""
    id: str
    title: str
    message: str
    segments: List[str]
    user_ids: Optional[List[str]]
    scheduled_at: Optional[str]
    sent_at: Optional[str]
    stats: Optional[Dict[str, int]] = None
    status: str  # 'pending', 'sending', 'sent', 'failed'


class NotificationFrequencySettings(BaseModel):
    """Notification frequency settings model."""
    daily_reminders: int = Field(default=1, ge=0, le=3, description="Max daily reminders per day")
    new_devotionals: int = Field(default=3, ge=0, le=10, description="Max new devotional notifications per day")
    announcements: int = Field(default=2, ge=0, le=5, description="Max announcement notifications per day")
    total_per_day: int = Field(default=5, ge=0, le=20, description="Max total notifications per day")

