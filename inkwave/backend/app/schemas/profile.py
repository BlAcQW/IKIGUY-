"""
Profile schemas.

Request/response models for user profile endpoints.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, HttpUrl


class InteractionPreferencesUpdate(BaseModel):
    """Update interaction preferences request."""

    explanation_depth: Optional[str] = Field(
        None,
        description="Explanation depth preference",
        pattern="^(concise|balanced|detailed)$",
    )
    discussion_topics: Optional[List[str]] = Field(
        None,
        description="Preferred discussion topics",
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "explanation_depth": "detailed",
                "discussion_topics": ["themes", "characters", "plot", "context"],
            }
        }


class VoicePreferencesResponse(BaseModel):
    """Voice preferences in profile response."""

    provider_id: str = Field(..., description="TTS provider ID")
    voice_id: str = Field(..., description="Voice identifier")
    speed: float = Field(..., description="Playback speed (0.5 - 2.0)")
    language: str = Field(..., description="Language code")
    voice_clone_reference: Optional[str] = Field(
        None, description="Voice clone reference URL"
    )


class InteractionPreferencesResponse(BaseModel):
    """Interaction preferences in profile response."""

    explanation_depth: str = Field(..., description="Explanation depth preference")
    discussion_topics: List[str] = Field(..., description="Discussion topics")


class UserProfileResponse(BaseModel):
    """User profile nested in ProfileResponse."""

    preferred_voice: str = Field(..., description="Legacy preferred voice")
    playback_speed: float = Field(..., description="Legacy playback speed")
    voice_preferences: VoicePreferencesResponse = Field(
        ..., description="Enhanced voice preferences"
    )
    reading_level: str = Field(..., description="Reading difficulty level")
    interaction_preferences: InteractionPreferencesResponse = Field(
        ..., description="AI interaction preferences"
    )


class ProfileResponse(BaseModel):
    """User profile response."""

    user_id: str = Field(..., description="Supabase user ID")
    email: EmailStr = Field(..., description="User email")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    profile: UserProfileResponse = Field(..., description="User profile settings")
    wallet_id: Optional[str] = Field(None, description="Wallet ID")
    credits: int = Field(..., description="Cached credit balance")
    is_admin: bool = Field(..., description="Admin flag")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_active: datetime = Field(..., description="Last activity timestamp")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "user_id": "uuid-123-456",
                "email": "user@example.com",
                "display_name": "John Doe",
                "avatar_url": "https://dev-inkwave-api.ailabsafrica.com/static/avatars/avatar.jpg",
                "profile": {
                    "preferred_voice": "nova",
                    "playback_speed": 1.0,
                    "voice_preferences": {
                        "provider_id": "coqui_xtts",
                        "voice_id": "nova",
                        "speed": 1.0,
                        "language": "en",
                        "voice_clone_reference": None,
                    },
                    "reading_level": "intermediate",
                    "interaction_preferences": {
                        "explanation_depth": "detailed",
                        "discussion_topics": ["themes", "characters", "context"],
                    },
                },
                "wallet_id": None,
                "credits": 0,
                "is_admin": False,
                "created_at": "2025-11-12T12:00:00Z",
                "last_active": "2025-11-12T15:30:00Z",
            }
        }


class ProfileUpdateRequest(BaseModel):
    """Update basic profile request."""

    display_name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Display name"
    )
    avatar_url: Optional[HttpUrl] = Field(None, description="Avatar image URL")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "display_name": "John Doe",
                "avatar_url": "https://example.com/avatar.jpg",
            }
        }


class AvatarUrlUpdate(BaseModel):
    """Update avatar from URL request."""

    avatar_url: HttpUrl = Field(..., description="Avatar image URL from the web")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {"avatar_url": "https://example.com/my-avatar.jpg"}
        }


class AvatarUploadResponse(BaseModel):
    """Avatar upload response."""

    avatar_url: str = Field(..., description="Uploaded avatar URL")
    message: str = Field(..., description="Success message")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "avatar_url": "https://dev-inkwave-api.ailabsafrica.com/static/avatars/user_123_abc.jpg",
                "message": "Avatar uploaded successfully",
            }
        }


class ProfileStatsResponse(BaseModel):
    """User reading statistics response."""

    books_started: int = Field(..., description="Number of books started")
    questions_asked: int = Field(..., description="Number of questions asked")
    listening_time_minutes: int = Field(..., description="Total listening time in minutes")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "books_started": 5,
                "questions_asked": 42,
                "listening_time_minutes": 320,
            }
        }
