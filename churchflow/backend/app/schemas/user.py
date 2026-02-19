"""
User request/response schemas.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """User profile response schema."""

    id: str = Field(..., description="User ID")
    phone: Optional[str] = Field(None, description="Phone number")
    name: Optional[str] = Field(None, description="Full name")
    branch_id: Optional[str] = Field(None, description="Branch ID")
    roles: List[str] = Field(default_factory=list, description="User roles")
    volunteer_roles: List[str] = Field(default_factory=list, description="Volunteer roles")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_active: datetime = Field(..., description="Last activity timestamp")
    profile_image_url: Optional[str] = Field(None, description="Profile image URL")


class CreateProfileRequest(BaseModel):
    """Request schema for creating user profile after OTP verification."""

    name: str = Field(..., min_length=1, max_length=100, description="Full name")
    branch_id: Optional[str] = Field(None, description="Branch ID")
    volunteer_roles: Optional[List[str]] = Field(default_factory=list, description="Volunteer roles")


class UpdateProfileRequest(BaseModel):
    """Request schema for updating user profile."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Full name")
    branch_id: Optional[str] = Field(None, description="Branch ID")
    volunteer_roles: Optional[List[str]] = Field(None, description="Volunteer roles")
