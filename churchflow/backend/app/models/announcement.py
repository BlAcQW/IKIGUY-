"""
Announcement database models.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, handler=None):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class Announcement(BaseModel):
    """
    Announcement model for landing page.

    Attributes:
        id: MongoDB document ID
        organization_id: Reference to organization
        title: Announcement title
        description: Announcement description/content
        image_url: Image URL for the announcement
        cta_text: Call-to-action button text
        cta_link: Call-to-action button link/URL
        event_id: Optional reference to related event/conference
        is_active: Whether announcement is active and visible
        display_order: Order for displaying announcements (lower = shown first)
        start_date: When to start showing the announcement
        end_date: When to stop showing the announcement
        created_by_user_id: User who created the announcement
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    organization_id: PyObjectId = Field(..., description="Organization ID")
    title: str = Field(..., min_length=1, max_length=200, description="Announcement title")
    description: Optional[str] = Field(None, max_length=1000, description="Announcement description")
    image_url: Optional[str] = Field(None, description="Image URL for the announcement")
    cta_text: Optional[str] = Field(None, max_length=50, description="CTA button text")
    cta_link: Optional[str] = Field(None, max_length=500, description="CTA button link")
    event_id: Optional[PyObjectId] = Field(None, description="Reference to related event/conference")
    is_active: bool = Field(default=True, description="Whether announcement is active")
    is_hero: bool = Field(default=False, description="Whether this is a hero announcement (shown prominently on landing page)")
    display_order: int = Field(default=0, ge=0, description="Display order (lower = shown first)")
    start_date: Optional[datetime] = Field(None, description="When to start showing the announcement")
    end_date: Optional[datetime] = Field(None, description="When to stop showing the announcement")
    created_by_user_id: PyObjectId = Field(..., description="User who created the announcement")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "title": "Upcoming Conference",
                "description": "Join us for our annual conference",
                "image_url": "https://example.com/image.jpg",
                "cta_text": "Register Now",
                "cta_link": "/events/conference-2025",
                "is_active": True,
                "display_order": 1
            }
        }

