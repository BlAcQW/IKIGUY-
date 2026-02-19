"""
User models for MongoDB.

Pydantic models for user documents and profiles.
"""

from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, validator
import re


class UserRole(str, Enum):
    """User roles for access control."""
    USER = "user"           # Basic user - book voice settings only
    AUTHOR = "author"       # Can upload books, global voice settings
    ADMIN = "admin"         # Admin access, global voice settings
    SUPERADMIN = "superadmin"  # Full access, global voice settings


# Roles that have access to global voice settings
GLOBAL_VOICE_SETTINGS_ROLES = {UserRole.AUTHOR, UserRole.ADMIN, UserRole.SUPERADMIN}


class InteractionPreferences(BaseModel):
    """User interaction preferences."""

    explanation_depth: str = "detailed"  # brief, detailed
    discussion_topics: List[str] = Field(
        default_factory=lambda: ["themes", "characters", "context"]
    )


class VoicePreferences(BaseModel):
    """Voice narration preferences."""

    provider_id: str = "coqui_xtts"  # TTS provider
    voice_id: str = "nova"  # Voice identifier
    speed: float = 1.0  # Playback speed (0.5 - 2.0)
    language: str = "en"  # Language code
    voice_clone_reference: Optional[str] = None  # URL to reference audio for cloning


class PrivacySettings(BaseModel):
    """
    User privacy settings for social features.

    Controls what information is visible to other users and how the user
    appears in social features like search, leaderboards, and profiles.
    """

    # Profile visibility
    profile_visibility: str = "followers_only"  # public, followers_only, private

    # What to show on profile
    show_currently_reading: bool = False  # Show books currently reading
    show_reading_history: bool = False  # Show completed books
    show_library: bool = False  # Show entire library
    show_listening_stats: bool = False  # Show total hours listened, books completed

    # Social connections visibility
    show_followers_list: bool = False  # Allow others to see who follows me
    show_following_list: bool = False  # Allow others to see who I follow
    show_follower_count: bool = True  # Show follower count
    show_following_count: bool = True  # Show following count

    # Leaderboard settings
    appear_in_leaderboard: bool = True  # Opt-in to leaderboard by default
    leaderboard_display_mode: str = "anonymous"  # opt_out, anonymous, full_profile

    # Discovery settings
    discoverable_by_search: bool = True  # Can be found via search
    allow_follow_requests: bool = True  # Allow others to follow me
    require_follow_approval: bool = False  # Require approval for follow requests (future feature)

    # Metadata
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SocialStats(BaseModel):
    """
    Denormalized social statistics for performance.

    These are cached values updated when social actions occur
    (follow/unfollow, reading progress, etc.)
    """

    followers_count: int = 0  # Number of users following this user
    following_count: int = 0  # Number of users this user follows
    total_listening_hours: float = 0.0  # Total hours listened across all books
    books_completed: int = 0  # Number of books completed
    current_streak_days: int = 0  # Current daily reading streak
    last_stats_update: datetime = Field(default_factory=datetime.utcnow)


class UserProfile(BaseModel):
    """User profile settings."""

    # Legacy fields (for backward compatibility)
    preferred_voice: str = "nova"
    playback_speed: float = 1.0

    # Enhanced voice preferences
    voice_preferences: VoicePreferences = Field(default_factory=VoicePreferences)

    reading_level: str = "intermediate"  # beginner, intermediate, advanced
    interaction_preferences: InteractionPreferences = Field(
        default_factory=InteractionPreferences
    )


class LibraryBook(BaseModel):
    """A book in user's library with access info."""

    book_id: str
    book_title: str
    book_cover_url: Optional[str] = None
    book_author: Optional[str] = None
    access_type: str = "invitation"  # invitation, purchase, free
    invitation_id: Optional[str] = None
    granted_by: Optional[str] = None
    granted_at: datetime = Field(default_factory=datetime.utcnow)


class User(BaseModel):
    """
    User document model.

    Represents a user in the MongoDB users collection.
    Extends Supabase auth with application-specific data.
    """

    user_id: str = Field(..., description="Supabase user ID")
    email: EmailStr
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

    # Personal information (optional)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None  # Phone number with country code (e.g., +233...)
    date_of_birth: Optional[datetime] = None  # Date of birth

    profile: UserProfile = Field(default_factory=UserProfile)

    # Social identity
    username: Optional[str] = Field(
        None,
        min_length=3,
        max_length=30,
        description="Unique username handle (e.g., @john_reader)"
    )
    bio: Optional[str] = Field(
        None,
        max_length=500,
        description="User bio/description"
    )

    # Privacy settings
    privacy_settings: PrivacySettings = Field(default_factory=PrivacySettings)

    # Social statistics (denormalized for performance)
    social_stats: SocialStats = Field(default_factory=SocialStats)

    # Username change tracking (prevent rapid changes)
    username_last_changed: Optional[datetime] = None

    @validator('username')
    def validate_username(cls, v):
        """
        Validate username format.

        Username must be:
        - 3-30 characters
        - Alphanumeric, dots, underscores, hyphens only
        - Cannot start or end with dot/underscore/hyphen
        """
        if v is None:
            return v

        # Check format
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$', v):
            raise ValueError(
                'Username must be alphanumeric and can contain dots, underscores, '
                'or hyphens (but cannot start or end with them)'
            )

        # Check for consecutive special characters
        if re.search(r'[._-]{2,}', v):
            raise ValueError('Username cannot contain consecutive special characters')

        return v.lower()  # Store usernames in lowercase for consistency

    # Wallet
    wallet_id: Optional[str] = None  # Reference to wallet in WalletService
    credits: int = 0  # Cached balance for quick access

    # Library - books user has access to
    library_books: List[LibraryBook] = Field(
        default_factory=list,
        description="Books user has access to via invitations or purchases"
    )

    # Role-based access control
    role: UserRole = Field(default=UserRole.USER, description="User role for access control")

    # Admin (deprecated - use role instead, kept for backward compatibility)
    is_admin: bool = False

    @property
    def has_global_voice_settings_access(self) -> bool:
        """Check if user has access to global voice settings."""
        return self.role in GLOBAL_VOICE_SETTINGS_ROLES or self.is_admin

    @property
    def can_upload_books(self) -> bool:
        """Check if user can upload books."""
        return self.role in {UserRole.AUTHOR, UserRole.ADMIN, UserRole.SUPERADMIN} or self.is_admin

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        populate_by_name = True


class UserInDB(User):
    """
    User model with MongoDB _id.

    Used for documents retrieved from database.
    """

    id: Optional[str] = Field(None, alias="_id")

    class Config:
        """Pydantic config."""

        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
