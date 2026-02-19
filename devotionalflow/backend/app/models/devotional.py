"""
Devotional models for devotional content management.
Supports structured content blocks (paragraph, scripture, prayer, reflection).
"""

from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Optional, List, Literal
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


class ContentBlock(BaseModel):
    """
    Structured content block for devotional content.
    Supports different types: paragraph, scripture, prayer, reflection, other_bible_references.
    """

    type: Literal["paragraph", "scripture", "prayer", "reflection", "other_bible_references"]
    text: str = Field(..., min_length=1)
    scripture_reference: Optional[str] = None  # e.g., "John 3:16" (for scripture type)

    @model_validator(mode='after')
    def validate_scripture_reference(self):
        """Ensure scripture_reference is provided for scripture blocks."""
        if self.type == "scripture" and not self.scripture_reference:
            raise ValueError("scripture_reference is required for scripture blocks")
        return self


class DevotionalBase(BaseModel):
    """Base devotional model with common fields."""

    title: str = Field(..., min_length=1, max_length=200)
    content: List[ContentBlock] = Field(..., min_items=1)
    scripture_references: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)


class DevotionalCreate(DevotionalBase):
    """Model for creating a new devotional."""

    cover_image_url: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    status: Literal["draft", "scheduled", "published"] = "draft"
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None  # Allow custom publish date
    
    # Series support
    series_id: Optional[str] = None  # Series ID if part of a series
    series_name: Optional[str] = None  # Series name (for new series)
    part_number: Optional[int] = Field(None, ge=1)  # Part number in the series (1, 2, 3, etc.)

    @model_validator(mode='after')
    def validate_scheduled_at(self):
        """Ensure scheduled_at is provided and in the future for scheduled devotionals."""
        if self.status == "scheduled":
            if not self.scheduled_at:
                raise ValueError("scheduled_at is required for scheduled devotionals")
            # Ensure both datetimes are timezone-aware for comparison
            from datetime import timezone
            now = datetime.now(timezone.utc)
            scheduled = self.scheduled_at
            # If scheduled_at is timezone-naive, assume it's UTC
            if scheduled.tzinfo is None:
                scheduled = scheduled.replace(tzinfo=timezone.utc)
            # If scheduled_at is timezone-aware, convert now to same timezone
            elif now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
            if scheduled <= now:
                raise ValueError("scheduled_at must be in the future")
        return self

    @model_validator(mode='after')
    def validate_categories(self):
        """Validate categories against allowed list."""
        allowed_categories = [
            "faith",
            "purpose",
            "prayer",
            "wisdom",
            "love",
            "hope",
            "gratitude",
            "forgiveness",
            "courage",
            "patience",
            "healing",
            "peace",
            "joy",
            "strength",
            "grace",
            "obedience",
            "worship",
            "family",
            "service",
            "spiritual-growth",
        ]
        for category in self.categories:
            if category.lower() not in allowed_categories:
                raise ValueError(
                    f"Invalid category: {category}. Allowed: {', '.join(allowed_categories)}"
                )
        # Normalize categories to lowercase
        self.categories = [c.lower() for c in self.categories]
        return self


class DevotionalUpdate(BaseModel):
    """Model for updating an existing devotional."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[List[ContentBlock]] = Field(None, min_items=1)
    scripture_references: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    cover_image_url: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    summary: Optional[str] = None  # AI-generated summary
    status: Optional[Literal["draft", "scheduled", "published"]] = None
    scheduled_at: Optional[datetime] = None
    
    # Series support
    series_id: Optional[str] = None
    series_name: Optional[str] = None
    part_number: Optional[int] = Field(None, ge=1)

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v):
        """Validate categories against allowed list."""
        if v is None:
            return v
        allowed_categories = [
            "faith",
            "purpose",
            "prayer",
            "wisdom",
            "love",
            "hope",
            "gratitude",
            "forgiveness",
            "courage",
            "patience",
        ]
        for category in v:
            if category.lower() not in allowed_categories:
                raise ValueError(
                    f"Invalid category: {category}. Allowed: {', '.join(allowed_categories)}"
                )
        # Normalize categories to lowercase
        normalized = [c.lower() for c in v]
        return normalized


class DevotionalInDB(DevotionalBase):
    """Devotional model as stored in MongoDB."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    author_id: PyObjectId
    slug: str
    excerpt: str  # First 150 chars

    # Media
    cover_image_url: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None

    # AI-generated content
    summary: Optional[str] = None

    # Status and publishing
    status: Literal["draft", "scheduled", "published"] = "draft"
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    
    # Day of year (1-365 or 1-366)
    day_of_year: Optional[int] = None
    day_of_year_total: Optional[int] = None  # 365 or 366

    # Engagement metrics
    views_count: int = 0
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    bookmarks_count: int = 0

    # Metadata
    reading_time_minutes: int = 0
    
    # Series support
    series_id: Optional[PyObjectId] = None
    series_name: Optional[str] = None
    part_number: Optional[int] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class DevotionalResponse(BaseModel):
    """Devotional model for API responses."""

    id: str
    author_id: str
    author_name: Optional[str] = None  # Author's display name
    author_avatar: Optional[str] = None  # Author's avatar URL
    title: str
    slug: str
    content: List[ContentBlock]
    excerpt: str
    scripture_references: List[str]
    categories: List[str]

    # Media
    cover_image_url: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None

    # AI-generated content
    summary: Optional[str] = None

    # Status and publishing
    status: Literal["draft", "scheduled", "published"]
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    
    # Day of year (1-365 or 1-366)
    day_of_year: Optional[int] = None
    day_of_year_total: Optional[int] = None  # 365 or 366

    # Engagement metrics
    views_count: int
    likes_count: int
    comments_count: int
    shares_count: int
    bookmarks_count: int

    # User-specific engagement (requires authentication)
    is_liked: Optional[bool] = None  # Whether current user has liked this devotional
    is_bookmarked: Optional[bool] = None  # Whether current user has bookmarked this devotional

    # Metadata
    reading_time_minutes: int
    
    # Series support
    series_id: Optional[str] = None
    series_name: Optional[str] = None
    part_number: Optional[int] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class DevotionalListResponse(BaseModel):
    """Response model for list of devotionals with pagination."""

    items: List[DevotionalResponse]  # Changed from 'devotionals' to 'items' for standard pagination
    total: int
    page: int
    page_size: int
    total_pages: int


class DevotionalFilters(BaseModel):
    """Query parameters for filtering devotionals."""

    status: Optional[Literal["draft", "scheduled", "published"]] = None
    category: Optional[str] = None
    author_id: Optional[str] = None
    search: Optional[str] = None  # Full-text search

    # Date filtering
    start_date: Optional[str] = None  # Start date in YYYY-MM-DD format
    end_date: Optional[str] = None    # End date in YYYY-MM-DD format
    days: Optional[int] = Field(None, ge=1)  # Last N days from today

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: Literal["created_at", "published_at", "views_count", "likes_count"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"


def generate_slug(title: str) -> str:
    """
    Generate URL-friendly slug from title.

    Args:
        title (str): Devotional title.

    Returns:
        str: URL-friendly slug.
    """
    return slugify(title, max_length=100)


def generate_excerpt(content, max_length: int = 150) -> str:
    """
    Generate excerpt from content blocks.

    Args:
        content: Devotional content blocks (List[ContentBlock] or List[dict]).
        max_length (int): Maximum excerpt length.

    Returns:
        str: Excerpt text.
    """
    # Handle both ContentBlock objects and dicts
    texts = []
    for block in content:
        if isinstance(block, dict):
            texts.append(block.get("text", ""))
        else:
            texts.append(block.text)
    
    # Concatenate all text from content blocks
    full_text = " ".join(texts)

    # Trim to max_length and add ellipsis
    if len(full_text) > max_length:
        return full_text[: max_length - 3] + "..."
    return full_text


def estimate_reading_time(content) -> int:
    """
    Estimate reading time in minutes based on content.
    Assumes average reading speed of 200 words per minute.

    Args:
        content: Devotional content blocks (List[ContentBlock] or List[dict]).

    Returns:
        int: Estimated reading time in minutes.
    """
    # Handle both ContentBlock objects and dicts
    word_count = 0
    for block in content:
        if isinstance(block, dict):
            text = block.get("text", "")
        else:
            text = block.text
        word_count += len(text.split())

    # Calculate reading time (200 words/minute)
    reading_time = max(1, round(word_count / 200))

    return reading_time
