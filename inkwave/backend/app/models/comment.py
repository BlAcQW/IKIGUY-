"""
Book comment and rating models.

Models for user comments, ratings, and reviews on books.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class CommentHelpful(BaseModel):
    """Track users who found a comment helpful."""

    user_id: str = Field(..., description="User ID who voted")
    voted_at: datetime = Field(default_factory=datetime.utcnow)


class BookComment(BaseModel):
    """Book comment/review model."""

    comment_id: str = Field(..., description="Unique comment identifier")
    book_id: str = Field(..., description="Book ID")
    user_id: str = Field(..., description="User ID who posted comment")

    # Comment content
    rating: Optional[int] = Field(None, ge=1, le=5, description="Star rating (1-5)")
    title: Optional[str] = Field(None, description="Review title")
    comment_text: str = Field(..., description="Comment/review text")

    # Engagement
    helpful_votes: List[CommentHelpful] = Field(default_factory=list, description="Users who found this helpful")
    helpful_count: int = Field(default=0, description="Count of helpful votes")

    # Moderation
    is_flagged: bool = Field(default=False, description="Flagged for review")
    is_hidden: bool = Field(default=False, description="Hidden by admin")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BookCommentInDB(BookComment):
    """Book comment with MongoDB _id."""

    id: Optional[str] = Field(None, alias="_id")


class CommentCreateRequest(BaseModel):
    """Request model for creating a comment."""

    rating: Optional[int] = Field(None, ge=1, le=5, description="Star rating (1-5)")
    title: Optional[str] = Field(None, max_length=200, description="Review title")
    comment_text: str = Field(..., min_length=1, max_length=5000, description="Comment text")


class CommentUpdateRequest(BaseModel):
    """Request model for updating a comment."""

    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    comment_text: Optional[str] = Field(None, min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    """Response model for comment with user info."""

    comment_id: str
    book_id: str
    user_id: str
    user_email: str
    user_display_name: Optional[str] = None
    user_avatar_url: Optional[str] = None

    rating: Optional[int] = None
    title: Optional[str] = None
    comment_text: str

    helpful_count: int
    user_found_helpful: bool = False  # Whether current user voted helpful

    is_author: bool = False  # Whether current user is the author

    created_at: str
    updated_at: str
