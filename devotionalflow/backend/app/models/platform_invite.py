"""
Platform-level user invitation models for DevotionalFlow.

Handles invitations to join FreshManna (DevotionalFlow) platform.
Separate from group invites which are for Bible study groups.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal, List
from datetime import datetime, timedelta
from bson import ObjectId
import secrets


def generate_invite_token() -> str:
    """Generate a secure invitation token."""
    return secrets.token_urlsafe(32)


def get_default_expiry() -> datetime:
    """Get default invitation expiry (7 days from now)."""
    return datetime.utcnow() + timedelta(days=7)


class PlatformInviteCreate(BaseModel):
    """
    Model for creating a platform invitation.

    Args:
        email: Email address to invite
        role: Role to assign on signup (user or admin)
        message: Optional custom message from inviter
    """

    email: EmailStr = Field(..., description="Email address to invite")
    role: Literal["user", "admin"] = Field(
        default="user",
        description="Role to assign when user signs up"
    )
    message: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional personal message from inviter"
    )


class PlatformInviteBulkCreate(BaseModel):
    """
    Model for bulk invitation creation.

    Args:
        emails: List of email addresses to invite (max 50)
        role: Role to assign on signup
        message: Optional shared message for all invites
    """

    emails: List[EmailStr] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of email addresses to invite"
    )
    role: Literal["user", "admin"] = Field(
        default="user",
        description="Role to assign when users sign up"
    )
    message: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional message for all invitations"
    )


class PlatformInviteInDB(BaseModel):
    """
    Platform invitation as stored in MongoDB.

    This model represents the full invitation document including
    tracking fields for email delivery and acceptance.
    """

    id: Optional[str] = Field(default=None, alias="_id")
    email: EmailStr
    role: Literal["user", "admin"] = "user"
    status: Literal["pending", "accepted", "revoked", "expired"] = "pending"
    token: str = Field(default_factory=generate_invite_token)

    # Inviter information
    invited_by_id: str
    invited_by_name: str
    invited_by_email: str
    message: Optional[str] = None

    # Timestamps
    invited_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=get_default_expiry)
    accepted_at: Optional[datetime] = None
    accepted_by_user_id: Optional[str] = None

    # Email tracking
    last_email_sent_at: Optional[datetime] = None
    email_count: int = 0

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class PlatformInviteResponse(BaseModel):
    """
    Platform invitation response model for API responses.

    Excludes sensitive fields like token from list responses.
    """

    id: str
    email: EmailStr
    role: Literal["user", "admin"]
    status: Literal["pending", "accepted", "revoked", "expired"]
    invited_by_name: str
    invited_by_email: str
    message: Optional[str] = None
    invited_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    email_count: int = 0

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class PlatformInviteListResponse(BaseModel):
    """
    Response model for paginated list of platform invitations.

    Args:
        invites: List of invitation responses
        total: Total count of matching invitations
        page: Current page number
        page_size: Items per page
        total_pages: Total number of pages
    """

    invites: List[PlatformInviteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PlatformInviteVerifyResponse(BaseModel):
    """
    Response when verifying an invitation token.

    Used by the signup page to validate invitation and
    pre-fill email and role information.

    Args:
        valid: Whether the token is valid
        email: Email address (if valid)
        role: Assigned role (if valid)
        invited_by_name: Name of person who sent invite
        message: Optional message from inviter
        expires_at: When the invitation expires
        error: Error message (if invalid)
    """

    valid: bool
    email: Optional[EmailStr] = None
    role: Optional[Literal["user", "admin"]] = None
    invited_by_name: Optional[str] = None
    message: Optional[str] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class PlatformInviteStats(BaseModel):
    """
    Statistics about platform invitations.

    Used for admin dashboard metrics.
    """

    total_invites: int = 0
    pending_invites: int = 0
    accepted_invites: int = 0
    expired_invites: int = 0
    revoked_invites: int = 0
    invites_this_week: int = 0
    acceptance_rate: float = 0.0
