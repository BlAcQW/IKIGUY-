"""
Voice greeting configuration models.
"""

from typing import Optional
from pydantic import BaseModel, Field


class VoiceGreetingConfig(BaseModel):
    """
    Voice greeting configuration for check-ins.

    This model can be embedded in Conference or BusRoute models to configure
    voice greetings that play after successful check-ins.

    Attributes:
        enabled: Whether voice greetings are enabled
        greeting_type: Type of greeting ("simple" or "personalized")
        message_template: Template text for the greeting
            - Simple mode: Direct message (e.g., "Welcome to Impact 2025!")
            - Personalized mode: Template with variables (e.g., "Welcome {user_name} from {branch}!")
        tts_provider: TTS provider to use (e.g., "coqui_xtts", "openai", "f5tts")
        voice_id: Specific voice ID to use (optional)
        speed: Voice playback speed (0.5-2.0)
        pitch: Voice pitch adjustment (-1.0 to 1.0)
        language: Language code (e.g., "en", "tw", "ga")
        personalization_enabled: Whether to include personalized user data
    """

    enabled: bool = Field(default=True)  # Enabled by default
    greeting_type: str = Field(
        default="personalized",  # Personalized greetings
        pattern="^(simple|personalized)$"
    )
    message_template: Optional[str] = Field(
        default="Hello {user_name}, how are you doing today? Thank you for checking in for {event_name}",
        max_length=500
    )
    tts_provider: str = Field(default="coqui_xtts")  # Default TTS provider
    voice_id: Optional[str] = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-1.0, le=1.0)
    language: str = Field(default="en")  # Default language: English
    personalization_enabled: bool = Field(default=True)  # Personalization enabled by default
    fallback_audio_url: Optional[str] = Field(
        default=None,
        description="Pre-recorded audio URL to use if dynamic TTS fails"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "enabled": True,
                "greeting_type": "personalized",
                "message_template": "Hello {user_name}, how are you doing today? Thank you for checking in for {event_name}",
                "tts_provider": "coqui_xtts",
                "voice_id": None,
                "speed": 1.0,
                "pitch": 0.0,
                "language": "en",
                "personalization_enabled": True,
                "fallback_audio_url": "https://churchflow-api.ailabsafrica.com/storage/greetings/default_welcome.mp3"
            }
        }


class GreetingAudioResponse(BaseModel):
    """
    Response model for generated greeting audio.

    Attributes:
        audio_url: URL to the generated audio file
        text: The actual greeting text that was synthesized
        duration_seconds: Duration of the audio in seconds
        provider_used: TTS provider that was used (or "fallback" for pre-recorded)
        cost_usd: Cost of generating the audio (if applicable)
        is_fallback: Whether this is pre-recorded fallback audio (not dynamic TTS)
    """

    audio_url: str
    text: str
    duration_seconds: Optional[float] = None
    provider_used: str
    cost_usd: Optional[float] = None
    is_fallback: bool = Field(default=False, description="True if using pre-recorded fallback audio")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "audio_url": "https://storage.ailabsafrica.com/greetings/greeting_123.mp3",
                "text": "Welcome John Mensah from Legon branch! Thank you for checking in to Impact 2025.",
                "duration_seconds": 5.2,
                "provider_used": "coqui_xtts",
                "cost_usd": 0.015
            }
        }
