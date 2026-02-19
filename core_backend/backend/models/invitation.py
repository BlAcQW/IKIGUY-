"""
User Invitation Models for KasaAI Core Backend.

Handles user invitation system with email-based invites where invited users
can set their own passwords. Integrates with affiliate system for automatic
referral tracking.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid
import secrets


class InvitationStatus(str, Enum):
    """Invitation status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class UserInvitation(BaseModel):
    """
    User invitation record.

    Tracks invitation sent to a user with a secure token for signup.
    Integrates with affiliate system to auto-register invited users.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr = Field(..., description="Email address of invitee")
    token: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secure invitation token"
    )

    # Inviter information
    invited_by_user_id: str = Field(..., description="User ID who sent invitation")
    invited_by_email: str = Field(..., description="Email of user who sent invitation")
    invited_by_name: str = Field(..., description="Name of user who sent invitation")
    inviter_referral_code: Optional[str] = Field(
        None,
        description="Inviter's affiliate referral code (for auto-registration)"
    )

    # User role and organization
    role: str = Field(
        "user",
        description="Role to assign to invited user (user, admin, moderator)"
    )
    organization_id: Optional[str] = Field(
        None,
        description="Organization ID to add user to (optional)"
    )

    # Invitation details
    message: Optional[str] = Field(
        None,
        description="Personal message from inviter"
    )
    status: InvitationStatus = Field(
        InvitationStatus.PENDING,
        description="Invitation status"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(days=7),
        description="Invitation expiry (7 days default)"
    )
    accepted_at: Optional[datetime] = Field(None, description="When invitation was accepted")
    cancelled_at: Optional[datetime] = Field(None, description="When invitation was cancelled")

    # Acceptance details
    accepted_user_id: Optional[str] = Field(
        None,
        description="User ID created upon acceptance"
    )
    accepted_ip_address: Optional[str] = Field(
        None,
        description="IP address where invitation was accepted"
    )
    accepted_user_agent: Optional[str] = Field(
        None,
        description="User agent where invitation was accepted"
    )

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    @validator("email")
    def validate_email_lowercase(cls, v):
        """Ensure email is lowercase."""
        return v.lower()

    @property
    def is_expired(self) -> bool:
        """Check if invitation is expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if invitation is valid (pending and not expired)."""
        return (
            self.status == InvitationStatus.PENDING and
            not self.is_expired
        )

    class Config:
        json_schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "invited_by_user_id": "user_123",
                "invited_by_email": "admin@example.com",
                "invited_by_name": "Admin User",
                "inviter_referral_code": "ADMIN001",
                "role": "user",
                "message": "Welcome to our platform!",
                "status": "pending"
            }
        }


class InviteUserRequest(BaseModel):
    """Request model for inviting a user."""

    email: EmailStr = Field(..., description="Email address to invite")
    role: str = Field(
        "user",
        description="Role to assign (user, admin, moderator, universal_admin)"
    )
    message: Optional[str] = Field(
        None,
        description="Personal message to include in invitation email"
    )
    organization_id: Optional[str] = Field(
        None,
        description="Organization to add user to upon acceptance"
    )
    send_email: bool = Field(
        True,
        description="Whether to send invitation email"
    )

    @validator("email")
    def validate_email_lowercase(cls, v):
        """Ensure email is lowercase."""
        return v.lower()

    @validator("role")
    def validate_role(cls, v):
        """Validate role is allowed."""
        allowed_roles = ["user", "admin", "moderator", "universal_admin"]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "role": "user",
                "message": "Join our platform and start building!",
                "send_email": True
            }
        }


class AcceptInvitationRequest(BaseModel):
    """Request model for accepting an invitation."""

    token: str = Field(..., description="Invitation token from email")
    password: str = Field(..., min_length=8, description="Password for new account")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")

    @validator("password")
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        # Add more password validation as needed
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123def456",
                "password": "SecureP@ssw0rd",
                "first_name": "John",
                "last_name": "Doe"
            }
        }


class InvitationListResponse(BaseModel):
    """Response model for listing invitations."""

    invitations: list
    total: int
    pending: int
    accepted: int
    expired: int
    cancelled: int


# Database collection name
USER_INVITATIONS_COLLECTION = "user_invitations"
