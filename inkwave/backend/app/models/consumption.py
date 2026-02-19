"""
Consumption tracking models for unified activity tracking.

Provides a single source of truth for all book consumption events:
- Book opened
- Reading started
- Listening started
- Progress updates (time-based)
- Completion

Supports all consumption modes:
- manual_reading: User reading text manually
- audio_playback: Pre-generated TTS audio
- ai_voice_narration: Real-time AI voice interaction
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ConsumptionMode(str, Enum):
    """Mode of book consumption."""
    MANUAL_READING = "manual_reading"
    AUDIO_PLAYBACK = "audio_playback"
    AI_VOICE_NARRATION = "ai_voice_narration"


class ConsumptionEventType(str, Enum):
    """Type of consumption event."""
    BOOK_OPENED = "book_opened"
    READING_STARTED = "reading_started"
    LISTENING_STARTED = "listening_started"
    PROGRESS_UPDATE = "progress_update"
    PAUSED = "paused"
    RESUMED = "resumed"
    COMPLETED = "completed"


class ConsumptionEvent(BaseModel):
    """
    Unified consumption event for tracking book usage.

    This is the single source of truth for all consumption activity.
    Both admin and user dashboards query this collection.
    """

    event_id: str = Field(
        default_factory=lambda: str(__import__('uuid').uuid4()),
        description="Unique event identifier"
    )

    # User and book identification
    user_id: str = Field(..., description="User ID from Supabase")
    book_id: str = Field(..., description="Book being consumed")
    session_id: str = Field(..., description="Reading session ID for grouping events")

    # Event type and mode
    event_type: ConsumptionEventType = Field(..., description="Type of consumption event")
    consumption_mode: ConsumptionMode = Field(..., description="How the book is being consumed")

    # Progress tracking
    chunk_index: int = Field(default=0, description="Current chunk being consumed")
    total_chunks: int = Field(default=0, description="Total chunks in the book")
    progress_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Overall progress percentage"
    )
    position_seconds: float = Field(
        default=0.0,
        description="Position within current chunk (for audio)"
    )

    # Time tracking
    duration_seconds: float = Field(
        default=0.0,
        description="Duration since last event (for progress updates)"
    )
    cumulative_time_seconds: float = Field(
        default=0.0,
        description="Total cumulative time spent in this session"
    )

    # Cached book metadata (for efficient queries)
    book_title: Optional[str] = Field(None, description="Cached book title")
    book_author: Optional[str] = Field(None, description="Cached book author")

    # Context
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context: voice_id, speed, chapter_title, etc."
    )

    # Device/browser info
    device_type: Optional[str] = Field(None, description="desktop, mobile, tablet")
    browser: Optional[str] = Field(None, description="Browser name")
    user_agent: Optional[str] = Field(None, description="Full user agent string")

    # Timestamps
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the event occurred"
    )

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConsumptionEventInDB(ConsumptionEvent):
    """Consumption event with MongoDB _id."""

    id: Optional[str] = Field(None, alias="_id")

    class Config:
        """Pydantic config."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConsumptionEventCreate(BaseModel):
    """Request model for creating a consumption event."""

    book_id: str
    session_id: str
    event_type: ConsumptionEventType
    consumption_mode: ConsumptionMode

    chunk_index: int = 0
    total_chunks: int = 0
    progress_percentage: float = 0.0
    position_seconds: float = 0.0
    duration_seconds: float = 0.0
    cumulative_time_seconds: float = 0.0

    book_title: Optional[str] = None
    book_author: Optional[str] = None

    context: Dict[str, Any] = Field(default_factory=dict)
    device_type: Optional[str] = None
    browser: Optional[str] = None
    user_agent: Optional[str] = None


class ConsumptionSession(BaseModel):
    """
    Aggregated consumption session for dashboard display.

    Represents a single reading/listening session with totals.
    Computed from ConsumptionEvent records.
    """

    session_id: str
    user_id: str
    book_id: str
    book_title: Optional[str] = None
    book_author: Optional[str] = None

    # Session details
    consumption_mode: ConsumptionMode
    started_at: datetime
    ended_at: Optional[datetime] = None

    # Progress
    start_chunk: int = 0
    end_chunk: int = 0
    progress_percentage: float = 0.0

    # Time spent
    total_duration_seconds: float = 0.0

    # Completion
    is_completed: bool = False
    completed_at: Optional[datetime] = None


class UserConsumptionStats(BaseModel):
    """
    Aggregated consumption stats for a user.

    Used for user dashboard and admin views.
    """

    user_id: str

    # Overall stats
    total_books_opened: int = 0
    total_books_in_progress: int = 0
    total_books_completed: int = 0

    # Time stats
    total_reading_time_seconds: float = 0.0
    total_listening_time_seconds: float = 0.0
    total_ai_narration_time_seconds: float = 0.0

    # Breakdown by mode
    mode_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Time spent in each mode"
    )

    # Recent activity
    last_activity_at: Optional[datetime] = None

    # Period stats (for dashboard)
    stats_period_start: Optional[datetime] = None
    stats_period_end: Optional[datetime] = None


class BookConsumptionStats(BaseModel):
    """
    Aggregated consumption stats for a book.

    Used for admin analytics.
    """

    book_id: str
    book_title: Optional[str] = None

    # Overall stats
    total_users: int = 0
    total_sessions: int = 0
    total_completions: int = 0
    completion_rate: float = 0.0

    # Time stats
    average_completion_time_seconds: float = 0.0
    total_consumption_time_seconds: float = 0.0

    # Mode breakdown
    mode_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Sessions by consumption mode"
    )

    # Progress distribution
    drop_off_points: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Where users stop reading/listening"
    )


class ProgressUpdateRequest(BaseModel):
    """
    Timer-based progress update request.

    Sent periodically by frontend (every 30 seconds or on pause).
    """

    session_id: str
    book_id: str
    consumption_mode: ConsumptionMode

    chunk_index: int
    position_seconds: float
    duration_since_last_update: float
    cumulative_time_seconds: float

    # For completion detection
    total_chunks: int
    is_final_chunk: bool = False
    chunk_completed: bool = False


class CompletionRequest(BaseModel):
    """
    Deterministic completion request.

    Sent when user finishes the last chunk of a book.
    """

    session_id: str
    book_id: str
    consumption_mode: ConsumptionMode

    total_chunks: int
    final_chunk_index: int
    total_time_seconds: float

    # Verification
    all_chunks_consumed: bool = False
    chunk_indices_consumed: List[int] = Field(default_factory=list)
