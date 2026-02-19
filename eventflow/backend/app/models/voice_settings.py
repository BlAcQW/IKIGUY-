"""
Voice settings models for EventFlow.

Provides data models for:
- User-level voice preferences
- Event-level voice settings
- Ama assistant customization
- Cost control settings
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VoicePreferences(BaseModel):
    """Voice preferences for event organizers and team members."""

    # TTS Preferences
    tts_provider: str = Field(
        default="coqui_xtts",
        description="Preferred TTS provider"
    )
    voice_id: Optional[str] = Field(
        default=None,
        description="Preferred voice ID"
    )
    language: str = Field(
        default="en",
        description="Preferred language (en, tw, ga, fr)"
    )
    speed: float = Field(
        default=1.0,
        description="Speech speed (0.5-2.0)",
        ge=0.5,
        le=2.0
    )
    pitch: float = Field(
        default=0.0,
        description="Voice pitch (-1.0 to 1.0)",
        ge=-1.0,
        le=1.0
    )

    # ASR Preferences
    asr_provider: str = Field(
        default="whisper_large_v3",
        description="Preferred ASR provider"
    )
    asr_language: Optional[str] = Field(
        default=None,
        description="ASR language (None for auto-detect)"
    )

    # Voice Call Preferences
    enable_voice_calls: bool = Field(
        default=True,
        description="Allow automated voice calls"
    )
    preferred_call_time_start: str = Field(
        default="08:00",
        description="Preferred call start time (HH:MM)"
    )
    preferred_call_time_end: str = Field(
        default="20:00",
        description="Preferred call end time (HH:MM)"
    )
    max_call_attempts: int = Field(
        default=3,
        description="Max number of call attempts",
        ge=1,
        le=5
    )

    # Voice Notifications
    enable_voice_reminders: bool = Field(
        default=True,
        description="Enable voice reminders for tasks"
    )
    enable_daily_voice_summary: bool = Field(
        default=True,
        description="Enable daily voice summary"
    )
    daily_summary_time: str = Field(
        default="18:00",
        description="Time for daily summary (HH:MM)"
    )

    # Cost Control
    max_daily_voice_cost: Optional[float] = Field(
        default=5.0,
        description="Max daily cost in USD for voice features",
        ge=0.0
    )
    alert_at_percentage: int = Field(
        default=80,
        description="Alert when daily budget reaches X%",
        ge=0,
        le=100
    )


class EventVoiceSettings(BaseModel):
    """Voice settings specific to an event."""

    event_id: str = Field(..., description="Event ID")

    # Event-level voice preferences
    voice_preferences: VoicePreferences = Field(
        default_factory=VoicePreferences,
        description="Voice preferences for this event"
    )

    # Ama assistant customization
    assistant_name: str = Field(
        default="Ama",
        description="Name of voice assistant"
    )
    assistant_personality: str = Field(
        default="friendly",
        description="Assistant personality (friendly, professional, casual)"
    )
    custom_greeting: Optional[str] = Field(
        default=None,
        description="Custom greeting for calls (e.g., 'Hi, this is Ama calling about the Impact Conference')"
    )

    # Escalation settings
    escalation_enabled: bool = Field(
        default=True,
        description="Enable automatic escalation for overdue tasks"
    )
    escalation_threshold_days: int = Field(
        default=2,
        description="Days overdue before escalation",
        ge=0,
        le=30
    )
    escalation_channels: List[str] = Field(
        default=["voice_call", "sms", "email"],
        description="Channels for escalation notifications"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Settings creation time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Settings last update time"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class VoicePreferencesUpdate(BaseModel):
    """Request model for updating voice preferences."""

    # TTS Preferences (all optional for partial updates)
    tts_provider: Optional[str] = None
    voice_id: Optional[str] = None
    language: Optional[str] = None
    speed: Optional[float] = Field(None, ge=0.5, le=2.0)
    pitch: Optional[float] = Field(None, ge=-1.0, le=1.0)

    # ASR Preferences
    asr_provider: Optional[str] = None
    asr_language: Optional[str] = None

    # Voice Call Preferences
    enable_voice_calls: Optional[bool] = None
    preferred_call_time_start: Optional[str] = None
    preferred_call_time_end: Optional[str] = None
    max_call_attempts: Optional[int] = Field(None, ge=1, le=5)

    # Voice Notifications
    enable_voice_reminders: Optional[bool] = None
    enable_daily_voice_summary: Optional[bool] = None
    daily_summary_time: Optional[str] = None

    # Cost Control
    max_daily_voice_cost: Optional[float] = Field(None, ge=0.0)
    alert_at_percentage: Optional[int] = Field(None, ge=0, le=100)


class EventVoiceSettingsUpdate(BaseModel):
    """Request model for updating event voice settings."""

    voice_preferences: Optional[VoicePreferencesUpdate] = None
    assistant_name: Optional[str] = None
    assistant_personality: Optional[str] = None
    custom_greeting: Optional[str] = None
    escalation_enabled: Optional[bool] = None
    escalation_threshold_days: Optional[int] = Field(None, ge=0, le=30)
    escalation_channels: Optional[List[str]] = None
