"""
Voice greeting API schemas.
"""

from typing import Optional
from pydantic import BaseModel, Field


class VoiceGreetingConfigUpdate(BaseModel):
    """
    Schema for updating voice greeting configuration.

    All fields are optional to allow partial updates.
    """

    enabled: Optional[bool] = None
    greeting_type: Optional[str] = Field(
        None,
        pattern="^(simple|personalized)$"
    )
    message_template: Optional[str] = Field(None, max_length=500)
    tts_provider: Optional[str] = None
    voice_id: Optional[str] = None
    speed: Optional[float] = Field(None, ge=0.5, le=2.0)
    pitch: Optional[float] = Field(None, ge=-1.0, le=1.0)
    language: Optional[str] = None
    personalization_enabled: Optional[bool] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "enabled": True,
                "greeting_type": "personalized",
                "message_template": "Welcome {user_name} from {branch}!",
                "tts_provider": "coqui_xtts",
                "speed": 1.2,
                "language": "en"
            }
        }


class VoiceGreetingPreviewRequest(BaseModel):
    """
    Schema for voice greeting preview request.

    Allows admins to test how a greeting will sound before saving.

    Attributes:
        message_template: The greeting text template
        tts_provider: TTS provider to use
        voice_id: Specific voice ID (optional)
        speed: Voice playback speed
        pitch: Voice pitch adjustment
        language: Language code
        sample_user_data: Sample user data for personalization testing
    """

    message_template: str = Field(..., min_length=1, max_length=500)
    tts_provider: str = Field(default="coqui_xtts")
    voice_id: Optional[str] = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-1.0, le=1.0)
    language: str = Field(default="en")
    sample_user_data: Optional[dict] = Field(
        default_factory=lambda: {
            "user_name": "John Mensah",
            "branch": "Legon",
            "volunteer_role": "choir"
        }
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "message_template": "Welcome {user_name} from {branch}! Thanks for serving in the {volunteer_role}.",
                "tts_provider": "coqui_xtts",
                "speed": 1.0,
                "pitch": 0.0,
                "language": "en",
                "sample_user_data": {
                    "user_name": "John Mensah",
                    "branch": "Legon",
                    "volunteer_role": "choir"
                }
            }
        }


class VoiceGreetingConfigResponse(BaseModel):
    """
    Schema for voice greeting configuration response.
    """

    enabled: bool
    greeting_type: str
    message_template: Optional[str]
    tts_provider: str
    voice_id: Optional[str]
    speed: float
    pitch: float
    language: str
    personalization_enabled: bool

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "enabled": True,
                "greeting_type": "personalized",
                "message_template": "Welcome {user_name} from {branch}!",
                "tts_provider": "coqui_xtts",
                "voice_id": None,
                "speed": 1.0,
                "pitch": 0.0,
                "language": "en",
                "personalization_enabled": True
            }
        }
