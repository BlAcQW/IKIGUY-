"""
TTS Data Models
Defines data structures for TTS requests and responses.
"""

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class AudioFormat(str, Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"
    PCM = "pcm"


class TTSProvider(str, Enum):
    """Available TTS providers."""
    F5TTS = "f5tts"
    STYLETTS2 = "styletts2"
    MOSHI = "moshi"
    COQUI_XTTS = "coqui_xtts"
    MELOTTS = "melotts"
    OPENVOICE = "openvoice"
    KOKORO = "kokoro"
    CHATTERBOX = "chatterbox"
    TTS_WEBUI = "tts_webui"
    FISH_SPEECH = "fish_speech"
    ZONOS = "zonos"
    CRAWL4AI = "crawl4ai"
    INDEXTTS = "indextts"
    VOXCPM = "voxcpm"
    GPT_SOVITS = "gpt_sovits"

    # TTS-WebUI specific models
    BARK = "bark"
    TORTOISE = "tortoise"
    MMS = "mms"
    MAHATTS = "mahatts"
    VALLE_X = "valle_x"


class TTSCapabilities(BaseModel):
    """TTS provider capabilities."""
    voice_cloning: bool = False
    multi_language: bool = False
    speed_control: bool = False
    pitch_control: bool = False
    multi_speaker: bool = False
    multi_model: bool = False  # For providers like TTS-WebUI with multiple models
    emotion_control: bool = False
    real_time_conversation: bool = False
    ssml_support: bool = False
    streaming: bool = False
    max_text_length: int = 5000
    supported_languages: List[str] = Field(default_factory=lambda: ["en"])
    supported_formats: List[AudioFormat] = Field(default_factory=lambda: [AudioFormat.WAV])
    available_models: List[str] = Field(default_factory=list)  # For multi-model providers


class TTSRequest(BaseModel):
    """Standard TTS synthesis request."""
    text: str = Field(..., min_length=1, max_length=5000)
    provider: Optional[TTSProvider] = None
    model: Optional[str] = None  # For multi-model providers like TTS-WebUI
    language: str = "en"
    speaker: Optional[str] = None
    voice: Optional[str] = None  # Alias for speaker (for OpenAI compatibility)
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)
    emotion: Optional[str] = None
    output_format: AudioFormat = AudioFormat.WAV
    sample_rate: int = Field(default=22050, ge=8000, le=48000)
    streaming: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VoiceCloneRequest(BaseModel):
    """Voice cloning request."""
    text: str = Field(..., min_length=1, max_length=5000)
    reference_audio: bytes = Field(..., description="Reference audio for cloning")
    reference_format: AudioFormat = AudioFormat.WAV
    provider: Optional[TTSProvider] = None
    language: str = "en"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    output_format: AudioFormat = AudioFormat.WAV
    sample_rate: int = Field(default=22050, ge=8000, le=48000)
    enhance: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationRequest(BaseModel):
    """Real-time conversation request (for Moshi)."""
    session_id: Optional[str] = None
    text: Optional[str] = None
    audio_input: Optional[bytes] = None
    context: List[str] = Field(default_factory=list)
    language: str = "en"
    streaming: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TTSResponse(BaseModel):
    """TTS synthesis response."""
    audio: Optional[bytes] = None
    audio_url: Optional[str] = None
    format: AudioFormat
    sample_rate: int
    duration: Optional[float] = None
    provider: TTSProvider
    model_version: Optional[str] = None
    language: str
    speaker: Optional[str] = None
    processing_time: Optional[float] = None
    cost: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            bytes: lambda v: None  # Don't serialize bytes in JSON
        }


class ProviderStatus(BaseModel):
    """TTS provider status."""
    provider: TTSProvider
    name: str
    endpoint: str
    status: Literal["online", "offline", "building", "error"]
    capabilities: TTSCapabilities
    description: str
    gpu_memory_gb: Optional[float] = None
    model_loaded: bool = False
    error: Optional[str] = None
    last_check: datetime = Field(default_factory=datetime.utcnow)


class BatchTTSRequest(BaseModel):
    """Batch TTS synthesis request."""
    items: List[TTSRequest]
    provider: Optional[TTSProvider] = None
    parallel: bool = False
    max_workers: int = Field(default=4, ge=1, le=10)
    output_format: AudioFormat = AudioFormat.WAV
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BatchTTSResponse(BaseModel):
    """Batch TTS synthesis response."""
    results: List[TTSResponse]
    total_items: int
    successful: int
    failed: int
    processing_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebSocketMessage(BaseModel):
    """WebSocket message for real-time communication."""
    type: Literal["audio", "text", "control", "status", "error"]
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    sequence: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)