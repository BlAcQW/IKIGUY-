"""
Notification schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SendBusDelayNotificationRequest(BaseModel):
    """Request schema for sending bus delay notification."""

    bus_route_id: str = Field(..., description="Bus route ID")
    delay_minutes: int = Field(..., ge=1, description="Minutes of delay")
    new_eta: str = Field(..., description="New estimated arrival time (e.g., '7:45 PM')")
    message: Optional[str] = Field(None, description="Optional custom message")


class NotificationResponse(BaseModel):
    """Response schema for notification operations."""

    success: bool
    message: str
    total_users: int
    notifications_sent: int
    notifications_failed: int
    channels_used: List[str]
    priority: str


class NotificationLogResponse(BaseModel):
    """Response schema for notification log entry."""

    id: str
    user_id: str
    notification_type: str
    channels: List[str]
    priority: str
    status: str
    created_at: datetime
