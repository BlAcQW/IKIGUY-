"""
Reading session models for MongoDB.

Pydantic models for reading sessions and related data.
Includes per-session voice settings for customizable TTS/ASR/LLM.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class SessionVoiceSettings(BaseModel):
    """
    Per-session voice settings override.

    These settings temporarily override user defaults for the duration
    of a reading session. They do not change permanent user preferences.

    Settings hierarchy (highest to lowest priority):
    1. Session overrides (this model)
    2. User defaults
    3. Organization defaults
    4. System defaults
    """

    # TTS Settings
    tts_provider: Optional[str] = Field(None, description="TTS provider override")
    tts_voice: Optional[str] = Field(None, description="Voice ID override")
    tts_speed: Optional[float] = Field(None, ge=0.5, le=2.0, description="Playback speed")
    tts_pitch: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Voice pitch")

    # ASR Settings
    asr_provider: Optional[str] = Field(None, description="ASR provider override")
    asr_language: Optional[str] = Field(None, description="Language for speech recognition")
    asr_task: Optional[str] = Field(None, description="ASR task (transcribe/translate)")

    # LLM Settings
    llm_model: Optional[str] = Field(None, description="LLM model override")
    llm_temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="LLM temperature")
    llm_max_tokens: Optional[int] = Field(None, ge=1, le=100000, description="Max response tokens")

    # Metadata
    applied_at: Optional[datetime] = Field(None, description="When settings were applied")
    source: str = Field(default="user_override", description="Source: user_override or preset")


class SessionVoiceSettingsUpdate(BaseModel):
    """Request model for updating session voice settings."""

    tts_provider: Optional[str] = None
    tts_voice: Optional[str] = None
    tts_speed: Optional[float] = Field(None, ge=0.5, le=2.0)
    tts_pitch: Optional[float] = Field(None, ge=-1.0, le=1.0)
    asr_provider: Optional[str] = None
    asr_language: Optional[str] = None
    asr_task: Optional[str] = None
    llm_model: Optional[str] = None
    llm_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    llm_max_tokens: Optional[int] = Field(None, ge=1, le=100000)


class Bookmark(BaseModel):
    """Bookmark within a reading session."""

    bookmark_id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    chunk_index: int
    position_seconds: float = 0.0
    note: Optional[str] = None
    chapter_title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReadingSession(BaseModel):
    """
    Reading session model.

    Tracks user's reading progress through a book.
    Includes per-session voice settings for TTS/ASR/LLM customization.
    """

    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User ID from Supabase")
    book_id: str = Field(..., description="Book being read")

    # Cached book metadata (avoid redundant queries)
    book_title: Optional[str] = Field(None, description="Cached book title")
    book_author: Optional[str] = Field(None, description="Cached book author")

    # Progress tracking
    current_chunk_index: int = 0
    current_position_seconds: float = 0.0  # Position within current chunk audio

    # Bookmarks
    bookmarks: List[Bookmark] = Field(default_factory=list)

    # Per-session voice settings (override user defaults)
    voice_settings: Optional[SessionVoiceSettings] = Field(
        None,
        description="Session-level voice settings that override user defaults"
    )

    # Metrics
    total_time_spent_minutes: int = 0

    # Cost tracking (100 credits = $1)
    total_cost_credits: int = Field(
        default=0,
        description="Total cost of this session in credits"
    )
    tts_cost_credits: int = Field(
        default=0,
        description="Cost of TTS audio generation in credits"
    )
    qa_cost_credits: int = Field(
        default=0,
        description="Cost of Q&A interactions in credits"
    )
    chunks_played: List[int] = Field(
        default_factory=list,
        description="List of chunk indices that were actually played (for accurate progress tracking)"
    )

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    last_transaction_at: Optional[datetime] = Field(
        None,
        description="Last time a wallet transaction was created (for batching)"
    )
    last_transaction_time: Optional[float] = Field(
        None,
        description="Total time spent (minutes) when last transaction was created (for accurate accumulation)"
    )
    completed: bool = False
    completed_at: Optional[datetime] = Field(
        None,
        description="Timestamp when session was completed"
    )

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        populate_by_name = True


class ReadingSessionInDB(ReadingSession):
    """
    Reading session model with MongoDB _id.

    Used for documents retrieved from database.
    """

    id: Optional[str] = Field(None, alias="_id")

    class Config:
        """Pydantic config."""

        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ReadingSessionUpdate(BaseModel):
    """
    Model for updating reading session progress.
    """

    current_chunk_index: Optional[int] = None
    current_position_seconds: Optional[float] = None
    total_time_spent_minutes: Optional[int] = None
    completed: Optional[bool] = None
