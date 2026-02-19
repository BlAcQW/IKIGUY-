"""
Announcement API Schemas.

Request and response models for announcement endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


# Request Schemas

class CreateAnnouncementRequest(BaseModel):
    """Request schema for creating an announcement."""

    title: str = Field(..., min_length=1, max_length=200, description="Announcement title")
    description: Optional[str] = Field(None, max_length=1000, description="Announcement description")
    image_url: Optional[str] = Field(None, description="Image URL for the announcement")
    cta_text: Optional[str] = Field(None, max_length=50, description="CTA button text")
    cta_link: Optional[str] = Field(None, max_length=500, description="CTA button link")
    event_id: Optional[str] = Field(None, description="Reference to related event/conference ID")
    is_active: bool = Field(default=True, description="Whether announcement is active")
    is_hero: bool = Field(default=False, description="Whether this is a hero announcement (shown prominently on landing page)")
    display_order: int = Field(default=0, ge=0, description="Display order (lower = shown first)")
    start_date: Optional[datetime] = Field(None, description="When to start showing the announcement")
    end_date: Optional[datetime] = Field(None, description="When to stop showing the announcement")


class UpdateAnnouncementRequest(BaseModel):
    """Request schema for updating an announcement."""

    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Announcement title")
    description: Optional[str] = Field(None, max_length=1000, description="Announcement description")
    image_url: Optional[str] = Field(None, description="Image URL for the announcement")
    cta_text: Optional[str] = Field(None, max_length=50, description="CTA button text")
    cta_link: Optional[str] = Field(None, max_length=500, description="CTA button link")
    event_id: Optional[str] = Field(None, description="Reference to related event/conference ID")
    is_active: Optional[bool] = Field(None, description="Whether announcement is active")
    is_hero: Optional[bool] = Field(None, description="Whether this is a hero announcement (shown prominently on landing page)")
    display_order: Optional[int] = Field(None, ge=0, description="Display order (lower = shown first)")
    start_date: Optional[datetime] = Field(None, description="When to start showing the announcement")
    end_date: Optional[datetime] = Field(None, description="When to stop showing the announcement")


# Response Schemas

class AnnouncementResponse(BaseModel):
    """Response schema for announcement."""

    id: str = Field(..., description="Announcement ID")
    organization_id: str = Field(..., description="Organization ID")
    title: str = Field(..., description="Announcement title")
    description: Optional[str] = Field(None, description="Announcement description")
    image_url: Optional[str] = Field(None, description="Image URL")
    cta_text: Optional[str] = Field(None, description="CTA button text")
    cta_link: Optional[str] = Field(None, description="CTA button link")
    event_id: Optional[str] = Field(None, description="Related event ID")
    is_active: bool = Field(..., description="Whether announcement is active")
    is_hero: bool = Field(..., description="Whether this is a hero announcement")
    display_order: int = Field(..., description="Display order")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    created_by_user_id: str = Field(..., description="User who created the announcement")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class AnnouncementListResponse(BaseModel):
    """Response schema for announcement list."""

    announcements: list[AnnouncementResponse] = Field(..., description="List of announcements")
    total: int = Field(..., description="Total count")

