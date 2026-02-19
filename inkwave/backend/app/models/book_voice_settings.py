"""
Book Voice Settings models.

Pydantic models for per-book voice settings that persist across sessions.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class BookVoiceSettings(BaseModel):
    """
    Per-book voice settings that persist across sessions.

    These settings apply to all reading sessions for a specific book.
    They override user defaults but can be overridden by session settings.

    Settings hierarchy (highest to lowest priority):
    1. Session overrides (temporary)
    2. Book-level settings (this model) - persistent per book
    3. User defaults
    4. Organization defaults
    5. System defaults (lowest priority)
    """

    # TTS Settings
    tts_provider: Optional[str] = Field(None, description="TTS provider for this book")
    tts_voice: Optional[str] = Field(None, description="Voice ID for this book")
    tts_speed: Optional[float] = Field(None, ge=0.5, le=2.0, description="Playback speed")
    tts_pitch: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Voice pitch")

    # ASR Settings
    asr_provider: Optional[str] = Field(None, description="ASR provider for this book")
    asr_language: Optional[str] = Field(None, description="Language for speech recognition")
    asr_task: Optional[str] = Field(None, description="ASR task (transcribe/translate)")

    # LLM Settings
    llm_provider: Optional[str] = Field(None, description="LLM provider (gemini, openai, anthropic)")
    llm_model: Optional[str] = Field(None, description="LLM model for this book")
    llm_temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="LLM temperature")
    llm_max_tokens: Optional[int] = Field(None, ge=1, le=100000, description="Max response tokens")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt for LLM")

    # Metadata
    applied_at: Optional[datetime] = Field(None, description="When settings were applied")
    source: str = Field(default="user_override", description="Source: user_override or preset")


class BookVoiceSettingsUpdate(BaseModel):
    """Request model for updating book voice settings."""

    tts_provider: Optional[str] = None
    tts_voice: Optional[str] = None
    tts_speed: Optional[float] = Field(None, ge=0.5, le=2.0)
    tts_pitch: Optional[float] = Field(None, ge=-1.0, le=1.0)
    asr_provider: Optional[str] = None
    asr_language: Optional[str] = None
    asr_task: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    llm_max_tokens: Optional[int] = Field(None, ge=1, le=100000)
    system_prompt: Optional[str] = None

