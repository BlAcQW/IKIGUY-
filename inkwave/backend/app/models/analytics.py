"""
Analytics models for tracking errors, events, and metrics.

Models for comprehensive tracking of user behavior, errors, and system health.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ErrorType(str, Enum):
    """Types of errors to track."""
    AUDIO_LOAD_FAILED = "audio_load_failed"
    AUDIO_PLAYBACK_FAILED = "audio_playback_failed"
    TTS_GENERATION_FAILED = "tts_generation_failed"
    TTS_TIMEOUT = "tts_timeout"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    VALIDATION_ERROR = "validation_error"
    DATABASE_ERROR = "database_error"
    BROWSER_COMPATIBILITY = "browser_compatibility"
    AUTOPLAY_BLOCKED = "autoplay_blocked"
    INSUFFICIENT_CREDITS = "insufficient_credits"
    UNKNOWN = "unknown"


class EventType(str, Enum):
    """Types of analytics events to track."""
    # Playback events
    PLAY_CLICKED = "play_clicked"
    PAUSE_CLICKED = "pause_clicked"
    SKIP_FORWARD = "skip_forward"
    SKIP_BACKWARD = "skip_backward"
    SPEED_CHANGED = "speed_changed"
    VOLUME_CHANGED = "volume_changed"
    CHUNK_CHANGED = "chunk_changed"

    # Navigation events
    BOOK_VIEWED = "book_viewed"
    BOOK_OPENED = "book_opened"
    CHAPTER_SELECTED = "chapter_selected"

    # Feature usage
    BOOKMARK_CREATED = "bookmark_created"
    BOOKMARK_USED = "bookmark_used"
    QA_OPENED = "qa_opened"
    QUESTION_TYPED = "question_typed"
    QUESTION_SENT = "question_sent"
    RESPONSE_RECEIVED = "response_received"
    RESPONSE_RATED = "response_rated"

    # Settings
    VOICE_CHANGED = "voice_changed"
    SETTINGS_OPENED = "settings_opened"

    # Session events
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    SESSION_COMPLETED = "session_completed"

    # Search and discovery
    SEARCH_PERFORMED = "search_performed"
    LIBRARY_OPENED = "library_opened"


class ErrorLog(BaseModel):
    """
    Error tracking model.

    Captures all errors for debugging and analytics.
    """

    error_id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Error details
    error_type: ErrorType
    error_message: str
    stack_trace: Optional[str] = None

    # Context
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context: book_id, chunk_index, url, etc."
    )

    # Browser/device info
    user_agent: Optional[str] = None
    browser: Optional[str] = None
    device_type: Optional[str] = None

    # Status
    resolved: bool = False
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None

    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorLogInDB(ErrorLog):
    """Error log model with MongoDB _id."""

    id: Optional[str] = Field(None, alias="_id")

    class Config:
        """Pydantic config."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalyticsEvent(BaseModel):
    """
    Analytics event tracking model.

    Captures all user interactions and system events.
    """

    event_id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Event details
    event_type: EventType
    event_name: str = Field(
        ...,
        description="Human-readable event name"
    )

    # Event properties
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data: book_id, chunk_index, value, etc."
    )

    # Context
    page_url: Optional[str] = None
    referrer: Optional[str] = None

    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalyticsEventInDB(AnalyticsEvent):
    """Analytics event model with MongoDB _id."""

    id: Optional[str] = Field(None, alias="_id")

    class Config:
        """Pydantic config."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UsageLog(BaseModel):
    """
    Usage log for cost tracking.

    Tracks every billable action for analytics and billing.
    """

    log_id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    user_id: str
    session_id: Optional[str] = None

    # Service details
    service: str = Field(
        ...,
        description="Service type: inkwave_listening, inkwave_tts, inkwave_qa"
    )
    action: str = Field(
        ...,
        description="Action: play_chunk, generate_audio, ask_question"
    )

    # Cost tracking
    cost_credits: int = Field(
        ...,
        description="Cost in credits (100 credits = $1)"
    )

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Action-specific data: book_id, chunk_index, provider, tokens, etc."
    )

    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UsageLogInDB(UsageLog):
    """Usage log model with MongoDB _id."""

    id: Optional[str] = Field(None, alias="_id")

    class Config:
        """Pydantic config."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PlaybackMetrics(BaseModel):
    """
    Audio playback quality metrics.

    Tracks performance and quality of audio playback.
    """

    metrics_id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    user_id: str
    session_id: str
    book_id: str
    chunk_index: int

    # Performance metrics
    buffer_start_ms: int = Field(
        ...,
        description="Time when buffering started (epoch ms)"
    )
    buffer_end_ms: Optional[int] = Field(
        None,
        description="Time when playback started (epoch ms)"
    )
    buffer_duration_ms: Optional[int] = Field(
        None,
        description="Total buffer time in milliseconds"
    )

    # Quality metrics
    stall_count: int = Field(
        default=0,
        description="Number of playback stalls/rebuffers"
    )
    total_stall_duration_ms: int = Field(
        default=0,
        description="Total time spent stalling"
    )

    # Audio info
    audio_format: Optional[str] = None
    audio_bitrate: Optional[int] = None
    audio_size_bytes: Optional[int] = None

    # Network
    download_time_ms: Optional[int] = None
    cache_hit: bool = False

    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PlaybackMetricsInDB(PlaybackMetrics):
    """Playback metrics model with MongoDB _id."""

    id: Optional[str] = Field(None, alias="_id")

    class Config:
        """Pydantic config."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
