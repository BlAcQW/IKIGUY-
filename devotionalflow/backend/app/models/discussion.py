"""
Discussion models for community-wide discussions.
Discussions are separate from groups - they're public discussion threads.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom type for MongoDB ObjectId in Pydantic models."""

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


class DiscussionCreate(BaseModel):
    """Model for creating a new discussion."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    devotional_id: Optional[str] = None
    scripture_reference: Optional[str] = None
    category: Optional[str] = None


class DiscussionResponse(BaseModel):
    """Discussion response model."""

    id: str
    title: str
    description: str
    devotional_id: Optional[str] = None
    devotional_title: Optional[str] = None
    scripture_reference: Optional[str] = None
    author_id: str
    author_name: str
    author_avatar: Optional[str] = None
    participants_count: int = 0
    messages_count: int = 0
    last_activity_at: datetime
    created_at: datetime
    category: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat(), ObjectId: str}


class DiscussionListResponse(BaseModel):
    """Response model for list of discussions."""

    items: list[DiscussionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

