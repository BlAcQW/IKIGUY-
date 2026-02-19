"""
Comment models for devotional comments and engagement.
Supports threaded replies (parent-child relationship).
"""

from pydantic import BaseModel, Field
from pydantic_core import core_schema
from typing import Optional, List, Any
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


class CommentBase(BaseModel):
    """Base comment model."""

    text: str = Field(..., min_length=1, max_length=500)


class CommentCreate(CommentBase):
    """Model for creating a new comment."""

    parent_comment_id: Optional[str] = None  # For threaded replies


class CommentUpdate(BaseModel):
    """Model for updating a comment."""

    text: str = Field(..., min_length=1, max_length=500)


class CommentInDB(CommentBase):
    """Comment model as stored in MongoDB."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    devotional_id: PyObjectId
    user_id: PyObjectId
    parent_comment_id: Optional[PyObjectId] = None
    is_pastor_reply: bool = False  # True if comment author is devotional author
    likes_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None  # Soft delete

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class CommentResponse(BaseModel):
    """Comment model for API responses."""

    id: str
    devotional_id: str
    user_id: str
    user_name: str  # Joined from users collection
    user_avatar_url: Optional[str] = None  # Joined from users collection
    text: str
    parent_comment_id: Optional[str] = None
    is_pastor_reply: bool
    likes_count: int
    created_at: datetime
    updated_at: datetime

    # Optional: Include replies for threaded comments
    replies: Optional[List["CommentResponse"]] = None

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class CommentListResponse(BaseModel):
    """Response model for list of comments with pagination."""

    comments: List[CommentResponse]
    total: int
    page: int
    page_size: int


# Enable forward references for nested CommentResponse
CommentResponse.model_rebuild()
