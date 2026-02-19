"""
Bible Study Group models for DevotionalFlow.
Supports group creation, membership, discussions, and chat.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
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


class GroupBase(BaseModel):
    """Base group model with common fields."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_public: bool = True  # Public groups can be discovered, private require invite


class GroupCreate(GroupBase):
    """Model for creating a new Bible study group."""

    devotional_id: Optional[str] = None  # Optional: link to specific devotional
    discussion_topic: Optional[str] = Field(None, max_length=200)


class GroupUpdate(BaseModel):
    """Model for updating a group."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None
    discussion_topic: Optional[str] = Field(None, max_length=200)


class GroupMember(BaseModel):
    """Group member information."""

    user_id: str
    name: str
    avatar_url: Optional[str] = None
    role: Literal["member", "admin"] = "member"
    joined_at: datetime


class GroupResponse(GroupBase):
    """Group response model."""

    id: str
    creator_id: str
    creator_name: str
    devotional_id: Optional[str] = None
    discussion_topic: Optional[str] = None
    members_count: int = 0
    messages_count: int = 0
    members: List[GroupMember] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat(), ObjectId: str}


class GroupMessage(BaseModel):
    """Model for group chat messages."""

    text: str = Field(..., min_length=1, max_length=1000)
    devotional_id: Optional[str] = None  # Optional: reference to devotional being discussed


class GroupMessageResponse(BaseModel):
    """Group message response model."""

    id: str
    group_id: str
    user_id: str
    user_name: str
    user_avatar_url: Optional[str] = None
    text: str
    devotional_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat(), ObjectId: str}


class GroupListResponse(BaseModel):
    """Response model for list of groups with pagination."""

    items: List[GroupResponse]
    total: int
    page: int
    page_size: int
    total_pages: int





