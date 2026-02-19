"""
Content moderation models for flagging and reviewing content.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime


class FlagReason(BaseModel):
    """Model for content flag reason."""

    category: Literal[
        "spam",
        "inappropriate",
        "offensive",
        "plagiarism",
        "misleading",
        "other",
    ]
    details: Optional[str] = Field(None, max_length=500)


class FlagContent(BaseModel):
    """Model for flagging content."""

    content_id: str  # Devotional ID or Comment ID
    content_type: Literal["devotional", "comment"]
    reason: FlagReason


class ContentFlag(BaseModel):
    """Model for a content flag record."""

    id: str
    content_id: str
    content_type: Literal["devotional", "comment"]
    flagged_by_user_id: str
    flagged_by_user_name: str
    flagged_by_user_email: str
    reason: FlagReason
    status: Literal["pending", "reviewed", "dismissed", "action_taken"] = "pending"
    created_at: datetime

    # Content preview
    content_preview: str  # First 200 chars of content

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class ModerationAction(BaseModel):
    """Model for moderation action."""

    action: Literal[
        "approve",
        "delete",
        "hide",
        "warn_author",
        "suspend_author",
        "dismiss_flag",
    ]
    reason: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)


class ModerationRecord(BaseModel):
    """Model for moderation action record."""

    id: str
    flag_id: str
    content_id: str
    content_type: Literal["devotional", "comment"]
    action: Literal[
        "approve",
        "delete",
        "hide",
        "warn_author",
        "suspend_author",
        "dismiss_flag",
    ]
    reason: Optional[str] = None
    notes: Optional[str] = None
    moderated_by_user_id: str
    moderated_by_user_name: str
    moderated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class ModerationQueueFilters(BaseModel):
    """Query parameters for moderation queue."""

    status: Optional[Literal["pending", "reviewed", "dismissed", "action_taken"]] = None
    content_type: Optional[Literal["devotional", "comment"]] = None
    reason_category: Optional[
        Literal["spam", "inappropriate", "offensive", "plagiarism", "misleading", "other"]
    ] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: Literal["created_at", "status"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"


class ModerationQueueResponse(BaseModel):
    """Response model for moderation queue."""

    flags: List[ContentFlag]
    total: int
    page: int
    page_size: int
    total_pages: int


class ModerationStats(BaseModel):
    """Statistics for content moderation."""

    total_flags: int
    pending_flags: int
    reviewed_flags: int
    dismissed_flags: int
    action_taken_flags: int

    # By content type
    devotional_flags: int
    comment_flags: int

    # By reason category
    spam_flags: int
    inappropriate_flags: int
    offensive_flags: int
    plagiarism_flags: int
    misleading_flags: int
    other_flags: int

    # Recent activity
    flags_last_24h: int
    flags_last_7d: int
    flags_last_30d: int
