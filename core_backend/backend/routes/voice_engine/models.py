"""
Pydantic models for voice engine API endpoints.

This module contains all the request/response models used by the voice engine routes.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from uuid import UUID


# LLM Provider models
class LLMProviderCreate(BaseModel):
    """Request model for creating LLM provider."""
    name: str = Field(..., description="Provider name")
    display_name: str = Field(..., description="Display name")
    description: str = Field(..., description="Provider description")
    website: str = Field(..., description="Provider website")
    api_base_url: str = Field(..., description="API base URL")
    pricing_model: str = Field(..., description="Pricing model")
    features: List[str] = Field(default_factory=list, description="Available features")
    supported_languages: List[str] = Field(default_factory=list, description="Supported languages")
    max_context_length: int = Field(..., description="Maximum context length")


class LLMModelCreate(BaseModel):
    """Request model for creating LLM model."""
    provider_id: str = Field(..., description="Provider ID")
    name: str = Field(..., description="Model name")
    display_name: str = Field(..., description="Display name")
    description: str = Field(..., description="Model description")
    model_type: str = Field(..., description="Model type")
    context_length: int = Field(..., description="Context length")
    input_cost_per_1k_tokens: float = Field(..., description="Input cost per 1K tokens")
    output_cost_per_1k_tokens: float = Field(..., description="Output cost per 1K tokens")
    capabilities: List[str] = Field(default_factory=list, description="Model capabilities")
    supported_languages: List[str] = Field(default_factory=list, description="Supported languages")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")


class LLMProviderUpdate(BaseModel):
    """Request model for updating LLM provider."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    api_base_url: Optional[str] = None
    pricing_model: Optional[str] = None
    features: Optional[List[str]] = None
    supported_languages: Optional[List[str]] = None
    max_context_length: Optional[int] = None
    is_active: Optional[bool] = None


class LLMModelUpdate(BaseModel):
    """Request model for updating LLM model."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    model_type: Optional[str] = None
    context_length: Optional[int] = None
    input_cost_per_1k_tokens: Optional[float] = None
    output_cost_per_1k_tokens: Optional[float] = None
    capabilities: Optional[List[str]] = None
    supported_languages: Optional[List[str]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


# Voice Provider models
class VoiceProviderCreate(BaseModel):
    """Request model for creating voice provider."""
    name: str = Field(..., description="Provider name")
    display_name: str = Field(..., description="Display name")
    description: str = Field(..., description="Provider description")
    website: str = Field(..., description="Provider website")
    api_base_url: str = Field(..., description="API base URL")
    pricing_model: str = Field(..., description="Pricing model")
    features: List[str] = Field(default_factory=list, description="Available features")
    supported_languages: List[str] = Field(default_factory=list, description="Supported languages")


class VoiceProviderUpdate(BaseModel):
    """Request model for updating voice provider."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    api_base_url: Optional[str] = None
    pricing_model: Optional[str] = None
    features: Optional[List[str]] = None
    supported_languages: Optional[List[str]] = None
    is_active: Optional[bool] = None


class VoiceCreate(BaseModel):
    """Request model for creating voice."""
    provider_id: str = Field(..., description="Provider ID")
    name: str = Field(..., description="Voice name")
    display_name: str = Field(..., description="Display name")
    description: str = Field(..., description="Voice description")
    gender: str = Field(..., description="Voice gender")
    age_group: str = Field(..., description="Age group")
    accent: str = Field(..., description="Accent/dialect")
    language_codes: List[str] = Field(..., description="Supported language codes")
    sample_rate: int = Field(default=22050, description="Sample rate in Hz")
    voice_characteristics: Dict[str, Any] = Field(default_factory=dict, description="Voice characteristics")


class VoiceUpdate(BaseModel):
    """Request model for updating voice."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    gender: Optional[str] = None
    age_group: Optional[str] = None
    accent: Optional[str] = None
    language_codes: Optional[List[str]] = None
    sample_rate: Optional[int] = None
    voice_characteristics: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


# Core voice engine models
class EnergyRequest(BaseModel):
    """Audio samples to calculate energy."""
    samples: List[int]


class EnergyResponse(BaseModel):
    """Energy calculation result."""
    energy: float


class EchoRequest(BaseModel):
    """Audio samples to echo back."""
    samples: List[int]


class EchoResponse(BaseModel):
    """Echoed audio samples."""
    samples: List[int]


class VADResponse(BaseModel):
    """Voice activity detection result."""
    energy: float
    voice: bool


class LanguagesResponse(BaseModel):
    """Available languages for a given country."""
    country: str
    languages: List[str]


class LanguageSelection(BaseModel):
    """Manually selected session language."""
    language: str = Field(min_length=1)


class TranscribeRequest(BaseModel):
    """Audio samples to be converted into text."""
    samples: List[int]


class TranscribeResponse(BaseModel):
    """Partial and final transcript."""
    transcript: str
    is_final: bool
    confidence: float
    language_detected: Optional[str] = None


class SynthesizeRequest(BaseModel):
    """Text to be converted to speech."""
    text: str = Field(min_length=1)
    provider: Optional[str] = None
    model: Optional[str] = None
    voice: Optional[str] = None
    language: Optional[str] = "en"


class SynthesizeResponse(BaseModel):
    """Synthesized audio response."""
    audio_data: bytes
    sample_rate: int = 22050
    duration: Optional[float] = None


class OptionsResponse(BaseModel):
    """Available provider and model combinations."""
    providers: Dict[str, Dict[str, List[str]]]


class LoopRequest(BaseModel):
    """Request for voice loop processing."""
    samples: List[int]
    provider: str = "mock"
    model: str = "base"
    language: str = "en"
    voice: Optional[str] = None


class LoopResponse(BaseModel):
    """Voice loop processing result."""
    transcript: str
    response: str
    audio: List[int]
    energy: float
    is_final: bool = True


class BargeInRequest(BaseModel):
    """Request for barge-in detection."""
    samples: List[int]
    threshold: float = 0.5


class BargeInResponse(BaseModel):
    """Barge-in detection result."""
    interrupted: bool
    energy: float
    timestamp: float


class FallbackRequest(BaseModel):
    """Request for fallback processing."""
    samples: List[int]
    primary_provider: str = "mock"
    fallback_provider: str = "mock"
    model: str = "base"


class FallbackResponse(BaseModel):
    """Fallback processing result."""
    transcript: str
    provider_used: str
    fallback_triggered: bool
    error_details: Optional[str] = None


class ConsentRequest(BaseModel):
    """Request for consent detection."""
    samples: List[int]
    consent_phrases: Optional[List[str]] = None


class ConsentResponse(BaseModel):
    """Consent detection result."""
    consent_detected: bool
    confidence: float
    detected_phrases: List[str]
    timestamp: float


class RetentionRequest(BaseModel):
    """Request for audio retention."""
    samples: List[int]
    user_id: str
    session_id: str
    retention_policy: str = "default"


class RetentionResponse(BaseModel):
    """Audio retention result."""
    retained: bool
    retention_id: Optional[str] = None
    expiry_date: Optional[str] = None


class OfflineModeRequest(BaseModel):
    """Request for offline mode processing."""
    samples: List[int]
    offline_models: List[str] = Field(default_factory=list)


class OfflineModeResponse(BaseModel):
    """Offline mode processing result."""
    transcript: str
    models_used: List[str]
    offline_mode: bool = True


class PstnInboundRequest(BaseModel):
    """PSTN inbound call request."""
    call_id: str = Field(..., description="Unique call identifier")
    from_number: str = Field(..., description="Caller phone number")
    to_number: str = Field(..., description="Called phone number")
    provider: str = Field(default="vonage", description="PSTN provider")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional call metadata")


class PstnInboundResponse(BaseModel):
    """PSTN inbound call response."""
    call_id: str
    status: str
    session_id: str
    webhook_url: Optional[str] = None


class PstnOutboundRequest(BaseModel):
    """PSTN outbound call request."""
    to_number: str = Field(..., description="Number to call")
    from_number: Optional[str] = Field(None, description="Caller ID number")
    provider: str = Field(default="vonage", description="PSTN provider")
    assistant_id: str = Field(..., description="Assistant to use for the call")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional call metadata")


class PstnOutboundResponse(BaseModel):
    """PSTN outbound call response."""
    call_id: str
    status: str
    to_number: str
    session_id: str


class AssistantConfigRequest(BaseModel):
    """Request for assistant configuration."""
    name: str = Field(..., description="Assistant name")
    description: str = Field(..., description="Assistant description")
    system_prompt: str = Field(..., description="System prompt")
    first_message: str = Field(..., description="First message to user")
    voice_provider_id: str = Field(..., description="Voice provider ID")
    voice_id: str = Field(..., description="Voice ID")
    llm_provider_id: str = Field(..., description="LLM provider ID")
    llm_model_id: str = Field(..., description="LLM model ID")
    language: str = Field(default="en", description="Primary language")
    personality_traits: Dict[str, Any] = Field(default_factory=dict, description="Personality configuration")
    conversation_settings: Dict[str, Any] = Field(default_factory=dict, description="Conversation settings")


class AssistantConfigUpdate(BaseModel):
    """Update request for assistant configuration."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    # LLM configuration
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_provider_id: Optional[str] = None  # Legacy field
    llm_model_id: Optional[str] = None     # Legacy field
    system_prompt: Optional[str] = None
    first_message: Optional[str] = None
    first_message_mode: Optional[str] = None
    # TTS configuration
    tts_provider: Optional[str] = None
    tts_model: Optional[str] = None
    tts_voice: Optional[str] = None
    voice_provider_id: Optional[str] = None  # Legacy field
    voice_id: Optional[str] = None           # Legacy field
    # STT configuration
    stt_provider: Optional[str] = None
    stt_model: Optional[str] = None
    # Additional settings
    language: Optional[str] = None
    country: Optional[str] = None
    background_sound: Optional[str] = None
    background_sound_url: Optional[str] = None
    # Voice parameters
    stability: Optional[float] = None
    clarity_similarity: Optional[float] = None
    speed: Optional[float] = None
    style_exaggeration: Optional[float] = None
    optimize_streaming_latency: Optional[float] = None
    # Advanced settings
    input_min_characters: Optional[int] = None
    punctuation_boundaries: Optional[str] = None
    background_denoising: Optional[bool] = None
    confidence_threshold: Optional[float] = None
    use_numerals: Optional[bool] = None
    # Other
    personality_traits: Optional[Dict[str, Any]] = None
    conversation_settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    knowledge_base_files: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None