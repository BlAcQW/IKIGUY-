"""
Book Club Models.

Data models for book clubs, memberships, invitations, and discussions.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class ClubVisibility(str, Enum):
    """Club visibility options."""
    PUBLIC = "public"
    PRIVATE = "private"
    FOLLOWERS_ONLY = "followers_only"


class MemberRole(str, Enum):
    """Member roles in a club."""
    CREATOR = "creator"
    MODERATOR = "moderator"
    MEMBER = "member"


class MemberStatus(str, Enum):
    """Membership status."""
    ACTIVE = "active"
    PENDING = "pending"
    REMOVED = "removed"
    LEFT = "left"


class InvitationStatus(str, Enum):
    """Invitation status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class ActivityType(str, Enum):
    """Discussion activity types."""
    COMMENT = "comment"
    REPLY = "reply"


class ClubSettings(BaseModel):
    """Book club settings."""
    allow_member_invites: bool = Field(
        False,
        description="Allow members to invite others"
    )
    require_approval: bool = Field(
        False,
        description="Require approval to join"
    )
    allow_comments: bool = Field(
        True,
        description="Allow members to comment"
    )
    notify_on_new_members: bool = Field(
        True,
        description="Notify creator on new members"
    )
    notify_on_new_comments: bool = Field(
        True,
        description="Notify members on new comments"
    )


class BookClub(BaseModel):
    """
    Book Club model.

    A reading community for a specific book.
    """
    club_id: str = Field(..., description="UUID for club")
    name: str = Field(..., min_length=3, max_length=100, description="Club name")
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Club description"
    )

    # Book reference
    book_id: str = Field(..., description="Book this club is for")
    book_title: str = Field(..., description="Denormalized book title")
    book_cover_url: Optional[str] = Field(None, description="Denormalized cover URL")

    # Creator
    creator_user_id: str = Field(..., description="User who created club")

    # Visibility
    visibility: ClubVisibility = Field(
        ClubVisibility.PUBLIC,
        description="Who can see and join this club"
    )

    # Denormalized counts
    member_count: int = Field(0, description="Number of members")
    discussion_count: int = Field(0, description="Number of discussions")

    # Settings
    settings: ClubSettings = Field(default_factory=ClubSettings)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)

    # Status
    archived: bool = Field(False, description="Whether club is archived")


class ClubMember(BaseModel):
    """
    Club membership model.

    Represents a user's membership in a book club.
    """
    membership_id: str = Field(..., description="UUID for membership")
    club_id: str = Field(..., description="Club reference")
    user_id: str = Field(..., description="User reference")

    # Role and status
    role: MemberRole = Field(MemberRole.MEMBER, description="Member role")
    status: MemberStatus = Field(MemberStatus.ACTIVE, description="Membership status")

    # Invitation tracking
    invited_by: Optional[str] = Field(None, description="User ID who invited")

    # Timestamps
    joined_at: datetime = Field(default_factory=datetime.utcnow)


class ClubInvitation(BaseModel):
    """
    Club invitation model.

    Represents an invitation to join a book club.
    Supports both registered users and email invitations.
    """
    invitation_id: str = Field(..., description="UUID for invitation")
    club_id: str = Field(..., description="Club reference")
    invited_by_user_id: str = Field(..., description="User who sent invitation")

    # For registered users
    invited_user_id: Optional[str] = Field(
        None,
        description="User ID for registered user invitations"
    )

    # For non-registered users (email invitations)
    invited_email: Optional[str] = Field(
        None,
        description="Email for non-registered user invitations"
    )
    invitation_token: str = Field(
        ...,
        description="Unique token for email invitation links"
    )

    # Status
    status: InvitationStatus = Field(
        InvitationStatus.PENDING,
        description="Invitation status"
    )

    # Custom message
    message: Optional[str] = Field(
        None,
        max_length=500,
        description="Custom invitation message"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(..., description="Expiration timestamp (7 days)")
    accepted_at: Optional[datetime] = Field(None, description="Acceptance timestamp")


class ClubDiscussion(BaseModel):
    """
    Club discussion model.

    Represents a comment or discussion thread in a book club.
    """
    discussion_id: str = Field(..., description="UUID for discussion")
    club_id: str = Field(..., description="Club reference")

    # Author
    user_id: str = Field(..., description="User who posted")
    username: str = Field(..., description="Denormalized username")
    user_avatar_url: Optional[str] = Field(None, description="Denormalized avatar")

    # Content
    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Discussion content"
    )
    chapter_reference: Optional[int] = Field(
        None,
        description="Chapter number reference"
    )

    # Threading
    reply_to_discussion_id: Optional[str] = Field(
        None,
        description="Parent discussion ID for replies"
    )

    # Reactions (emoji -> list of user IDs)
    reactions: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Reactions with user IDs"
    )

    # Denormalized count
    reply_count: int = Field(0, description="Number of replies")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    edited_at: Optional[datetime] = Field(None, description="Last edit timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")


# Response models for API
class ClubMemberInDB(ClubMember):
    """Club member with MongoDB _id."""
    id: Optional[str] = Field(None, alias="_id")


class BookClubInDB(BookClub):
    """Book club with MongoDB _id."""
    id: Optional[str] = Field(None, alias="_id")


class ClubInvitationInDB(ClubInvitation):
    """Club invitation with MongoDB _id."""
    id: Optional[str] = Field(None, alias="_id")


class ClubDiscussionInDB(ClubDiscussion):
    """Club discussion with MongoDB _id."""
    id: Optional[str] = Field(None, alias="_id")
