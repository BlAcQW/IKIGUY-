"""
Group Invite models for DevotionalFlow.
Handles invitations to join Bible study groups.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId


class InviteBase(BaseModel):
    """Base invite model."""

    group_id: str
    invitee_email: Optional[EmailStr] = None
    invitee_id: Optional[str] = None  # If user already exists


class InviteCreate(InviteBase):
    """Model for creating an invite."""

    pass


class InviteResponse(InviteBase):
    """Invite response model."""

    id: str
    inviter_id: str
    inviter_name: str
    invite_token: str
    status: Literal["pending", "accepted", "declined", "expired"] = "pending"
    expires_at: datetime
    created_at: datetime
    accepted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat(), ObjectId: str}


class InviteListResponse(BaseModel):
    """Response model for list of invites."""

    items: list[InviteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AcceptInviteRequest(BaseModel):
    """Request model for accepting an invite."""

    user_id: Optional[str] = None  # If not provided, uses current user

