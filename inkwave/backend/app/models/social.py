"""
Social feature models for MongoDB.

Pydantic models for social interactions: follows, reading activity,
blocks, and reports.
"""

from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class FollowStatus(str, Enum):
    """Status of a follow request."""
    PENDING = "pending"     # Request sent but not accepted
    ACCEPTED = "accepted"   # Follow is active
    REJECTED = "rejected"   # Request was rejected


class UserFollow(BaseModel):
    """
    Follow relationship between users.

    Asymmetric model: User A can follow User B without B following A back.
    """

    follow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    follower_user_id: str = Field(..., description="User who is following")
    following_user_id: str = Field(..., description="User being followed")
    status: FollowStatus = Field(default=FollowStatus.ACCEPTED)
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    notify_on_activity: bool = True  # Receive notifications about this user's activity

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        populate_by_name = True


class ActivityType(str, Enum):
    """Types of reading activities."""
    STARTED_BOOK = "started_book"           # User started reading a book
    COMPLETED_BOOK = "completed_book"       # User finished a book
    MILESTONE_REACHED = "milestone_reached"  # Reached 25%, 50%, 75%


class ActivityVisibility(str, Enum):
    """Visibility settings for reading activities."""
    PUBLIC = "public"               # Visible to everyone
    FOLLOWERS_ONLY = "followers_only"  # Visible to followers only
    PRIVATE = "private"             # Not visible to anyone


class ReadingActivity(BaseModel):
    """
    Public-facing reading activity for social feeds.

    Created automatically when users start/complete books or reach milestones.
    Respects user privacy settings.
    """

    activity_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User who performed the activity")
    activity_type: ActivityType
    book_id: str
    book_title: str
    book_cover_url: Optional[str] = None
    book_author: Optional[str] = None
    progress_percentage: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Progress percentage for milestone activities"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    visibility: ActivityVisibility = Field(default=ActivityVisibility.FOLLOWERS_ONLY)

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        populate_by_name = True


class UserBlock(BaseModel):
    """
    User blocking for safety and privacy.

    When User A blocks User B:
    - B cannot see A's profile
    - B cannot follow A
    - Existing follow is removed
    - B cannot see A in search
    """

    block_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    blocker_user_id: str = Field(..., description="User doing the blocking")
    blocked_user_id: str = Field(..., description="User being blocked")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for blocking")
    blocked_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        populate_by_name = True


class ReportType(str, Enum):
    """Types of user reports."""
    HARASSMENT = "harassment"                   # Harassment or bullying
    SPAM = "spam"                               # Spam or fake account
    INAPPROPRIATE_CONTENT = "inappropriate_content"  # Inappropriate profile/bio
    IMPERSONATION = "impersonation"             # Impersonating another person
    OTHER = "other"                             # Other issues


class ReportStatus(str, Enum):
    """Status of a user report."""
    PENDING = "pending"         # Not yet reviewed
    REVIEWED = "reviewed"       # Reviewed by moderator
    ACTION_TAKEN = "action_taken"  # Action was taken
    DISMISSED = "dismissed"     # Report dismissed as invalid


class UserReport(BaseModel):
    """
    User reporting for moderation.

    Allows users to report others for violations of community guidelines.
    Reports are reviewed by administrators.
    """

    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reporter_user_id: str = Field(..., description="User making the report")
    reported_user_id: str = Field(..., description="User being reported")
    report_type: ReportType
    description: str = Field(..., max_length=1000, description="Description of the issue")
    evidence_urls: List[str] = Field(
        default_factory=list,
        description="URLs to screenshots or other evidence"
    )
    status: ReportStatus = Field(default=ReportStatus.PENDING)
    reviewed_by: Optional[str] = Field(None, description="Admin user ID who reviewed")
    reviewed_at: Optional[datetime] = None
    action_taken: Optional[str] = Field(
        None,
        max_length=500,
        description="Action taken by moderator"
    )
    admin_notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Internal notes from moderator"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        populate_by_name = True
