"""
Series models for managing devotional series.
Supports full CRUD operations, scheduling, and reordering of devotionals within series.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from slugify import slugify


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


class SeriesBase(BaseModel):
    """Base series model with common fields."""

    name: str = Field(..., min_length=1, max_length=200, description="Series name")
    description: Optional[str] = Field(None, max_length=1000, description="Series description")
    cover_image_url: Optional[str] = Field(None, description="URL to series cover image")


class SeriesCreate(SeriesBase):
    """Model for creating a new series."""

    start_date: Optional[datetime] = Field(None, description="Series start date for scheduling Part 1")

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, v):
        """Allow past dates for backdating series."""
        # No validation needed - allow any date including past
        return v


class SeriesUpdate(BaseModel):
    """Model for updating an existing series."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    cover_image_url: Optional[str] = None
    start_date: Optional[datetime] = Field(None, description="Changing start_date reschedules ALL devotionals")


class SeriesInDB(SeriesBase):
    """Series model as stored in MongoDB."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    slug: str = Field(..., description="URL-friendly slug generated from name")
    author_id: PyObjectId = Field(..., description="Author who created the series")
    start_date: Optional[datetime] = Field(None, description="Series start date for scheduling")
    total_parts: int = Field(0, description="Total devotionals in series (auto-calculated)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class DevotionalSummary(BaseModel):
    """Lightweight devotional info for series response."""

    id: str
    title: str
    part_number: int
    status: str
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    excerpt: Optional[str] = None


class SeriesResponse(BaseModel):
    """Series model for API responses."""

    id: str
    name: str
    slug: str
    description: Optional[str]
    cover_image_url: Optional[str]
    author_id: str
    author_name: Optional[str] = Field(None, description="Populated from author lookup")
    start_date: Optional[datetime]
    total_parts: int
    devotionals_count: Optional[int] = Field(None, description="Count of devotionals in series")
    devotionals: Optional[List[DevotionalSummary]] = Field(None, description="Only included in detail view")
    created_at: datetime
    updated_at: datetime


class SeriesListResponse(BaseModel):
    """Response for paginated series list."""

    items: List[SeriesResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DevotionalOrder(BaseModel):
    """Devotional ID and its new part number."""

    devotional_id: str = Field(..., description="Devotional ID")
    part_number: int = Field(..., ge=1, description="New part number (1-indexed)")


class ReorderDevotionalsRequest(BaseModel):
    """Request to reorder devotionals in a series."""

    devotional_order: List[str] = Field(..., min_length=1, description="List of devotional IDs in new order")
    reschedule: bool = Field(False, description="If True, reschedule based on new order + series start_date")

    @field_validator("devotional_order")
    @classmethod
    def validate_no_duplicates(cls, v):
        """Ensure no duplicate devotional IDs."""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate devotional IDs found in reorder request")
        return v


class ScheduleSeriesRequest(BaseModel):
    """Request to schedule all devotionals in a series."""

    start_date: datetime = Field(..., description="Start date for series scheduling")
    interval_days: int = Field(1, ge=1, le=7, description="Days between devotionals (default: 1)")
    overwrite_existing: bool = Field(False, description="Overwrite existing scheduled dates")


class RemoveDevotionalRequest(BaseModel):
    """Request to remove a devotional from series."""

    auto_renumber: bool = Field(True, description="Auto-renumber remaining devotionals")


def generate_slug(name: str) -> str:
    """
    Generate URL-friendly slug from series name.

    Args:
        name (str): Series name

    Returns:
        str: URL-friendly slug
    """
    return slugify(name, max_length=200, word_boundary=True)
