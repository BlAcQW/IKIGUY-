"""
Organization Invitation Model for ERP.

Handles invitation workflow for adding users to organizations.
"""

from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId
import secrets


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class InvitationCreate(BaseModel):
    """Schema for creating an organization invitation."""

    email: EmailStr
    role: str = Field(default="user", pattern="^(admin|user)$")
    display_name: Optional[str] = None
    message: Optional[str] = None


class Invitation(BaseModel):
    """Organization invitation model."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    organization_id: str
    email: EmailStr
    role: str = Field(pattern="^(admin|user)$")
    status: str = Field(default="pending", pattern="^(pending|accepted|cancelled|expired)$")
    token: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    invited_by: str  # User ID
    invited_by_email: str
    display_name: Optional[str] = None
    message: Optional[str] = None
    invited_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(days=7)
    )
    accepted_at: Optional[datetime] = None
    accepted_by: Optional[str] = None  # User ID who accepted

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "organization_id": "org_123",
                "email": "user@example.com",
                "role": "user",
                "status": "pending",
                "invited_by": "user_456",
                "invited_by_email": "admin@example.com",
                "display_name": "John Doe",
                "message": "Welcome to our organization!",
                "invited_at": "2025-11-14T10:00:00",
                "expires_at": "2025-11-21T10:00:00"
            }
        }


class InvitationAccept(BaseModel):
    """Schema for accepting an invitation."""

    user_id: str
    display_name: str
