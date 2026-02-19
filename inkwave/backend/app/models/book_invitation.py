"""
Book Invitation models for MongoDB.

Pydantic models for book invitation/access link documents.
Used to share book access with users via registration links.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
import secrets


def generate_invitation_token() -> str:
    """
    Generate a secure random invitation token.

    Returns:
        A 32-character URL-safe token
    """
    return secrets.token_urlsafe(24)


class BookInvitation(BaseModel):
    """
    Book invitation document model.

    Represents an invitation link that grants access to a specific book
    when a user registers using the link.
    """

    invitation_id: str = Field(
        default_factory=generate_invitation_token,
        description="Unique invitation token (used in URL)"
    )
    book_id: str = Field(..., description="Book ID to grant access to")
    book_title: str = Field(..., description="Book title (for display)")
    book_cover_url: Optional[str] = Field(None, description="Book cover URL")

    # Creator info
    created_by: str = Field(..., description="Admin user ID who created this")
    created_by_email: Optional[str] = Field(None, description="Admin email for reference")

    # Usage limits
    max_uses: Optional[int] = Field(
        None,
        description="Maximum number of times this link can be used (None = unlimited)"
    )
    used_count: int = Field(0, description="Number of times used")

    # Validity
    expires_at: Optional[datetime] = Field(
        None,
        description="Expiration datetime (None = never expires)"
    )
    is_active: bool = Field(True, description="Whether invitation is active")

    # Optional message
    welcome_message: Optional[str] = Field(
        None,
        description="Custom welcome message to show on signup"
    )

    # Tracking
    redeemed_by: List[str] = Field(
        default_factory=list,
        description="List of user IDs who redeemed this invitation"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        populate_by_name = True

    def is_valid(self) -> bool:
        """
        Check if the invitation is still valid.

        Returns:
            True if invitation can be used, False otherwise
        """
        # Check if active
        if not self.is_active:
            return False

        # Check expiration
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False

        # Check usage limit
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False

        return True

    def get_status(self) -> str:
        """
        Get human-readable status.

        Returns:
            Status string (active, expired, exhausted, revoked)
        """
        if not self.is_active:
            return "revoked"
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return "expired"
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return "exhausted"
        return "active"


class BookInvitationInDB(BookInvitation):
    """
    Book invitation model with MongoDB _id.

    Used for documents retrieved from database.
    """

    id: Optional[str] = Field(None, alias="_id")

    class Config:
        """Pydantic config."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserLibraryBook(BaseModel):
    """
    A book in a user's library.

    Represents access to a book granted via invitation or purchase.
    """

    book_id: str = Field(..., description="Book ID")
    book_title: str = Field(..., description="Book title")
    book_cover_url: Optional[str] = Field(None, description="Cover URL")
    book_author: Optional[str] = Field(None, description="Author name")

    # Access info
    access_type: str = Field(
        "invitation",
        description="How access was granted (invitation, purchase, free)"
    )
    invitation_id: Optional[str] = Field(
        None,
        description="Invitation ID if granted via invitation"
    )
    granted_by: Optional[str] = Field(
        None,
        description="Admin user ID who granted access"
    )

    # Timestamps
    granted_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
