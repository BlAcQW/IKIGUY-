"""
Engagement models for likes, bookmarks, shares, and reading history.
"""

from pydantic import BaseModel, Field
from pydantic_core import core_schema
from typing import Literal, Optional, Any, List
from datetime import datetime
from bson import ObjectId


class PyObjectId(str):
    """Custom type for MongoDB ObjectId in Pydantic V2 models."""

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler):
        """Define how Pydantic should validate this type."""
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v):
        """Validate and convert to ObjectId."""
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError(f"Invalid ObjectId: {v}")


# ==================== LIKES ====================


class LikeCreate(BaseModel):
    """Model for creating a like."""

    target_type: Literal["devotional", "comment"]
    target_id: str


class LikeInDB(BaseModel):
    """Like model as stored in MongoDB."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    target_type: Literal["devotional", "comment"]
    target_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class LikeResponse(BaseModel):
    """Like response model."""

    liked: bool  # True if liked, False if unliked
    likes_count: int


# ==================== BOOKMARKS ====================


class BookmarkCreate(BaseModel):
    """Model for creating a bookmark."""

    devotional_id: str


class BookmarkInDB(BaseModel):
    """Bookmark model as stored in MongoDB."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    devotional_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class BookmarkResponse(BaseModel):
    """Bookmark response model for listing bookmarks."""

    id: str
    title: str
    excerpt: str
    cover_image_url: Optional[str] = None
    published_at: datetime
    reading_time_minutes: int
    categories: List[str] = []
    created_at: datetime  # When bookmark was created

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# ==================== SHARES ====================


class ShareCreate(BaseModel):
    """Model for tracking a share."""

    devotional_id: str
    platform: Literal["whatsapp", "facebook", "twitter", "instagram", "copy_link"]


class ShareResponse(BaseModel):
    """Share response model."""

    id: str
    devotional_id: str
    platform: str
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# ==================== READING HISTORY ====================


class ReadingHistoryCreate(BaseModel):
    """Model for tracking reading history."""

    reading_progress: float = Field(100.0, ge=0, le=100)  # Percentage (0-100)
    listening_progress: float = Field(0.0, ge=0, le=100)  # Audio progress (0-100)
    time_spent_seconds: int = Field(0, ge=0)  # Time spent in seconds


class ReadingHistoryInDB(BaseModel):
    """Reading history model as stored in MongoDB."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    devotional_id: PyObjectId
    read_at: datetime = Field(default_factory=datetime.utcnow)
    reading_progress: int = 100  # Scroll percentage
    listening_progress: int = 0  # Audio progress

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class ReadingHistoryResponse(BaseModel):
    """Reading history response model."""

    id: str
    devotional_id: str
    devotional_title: str  # Joined from devotionals collection
    progress: float  # Reading progress percentage (0-100)
    time_spent: int  # Time spent reading in seconds
    last_read_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# ==================== VIEW TRACKING ====================


class ViewCreate(BaseModel):
    """Model for tracking devotional views."""

    devotional_id: str
