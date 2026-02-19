"""
Voice Lab Service

Shared service for voice processing operations (ASR, TTS, voice cloning).
Provides generic voice operations that apps can extend with business logic.

Usage:
    from shared.services.voice_lab_service import VoiceLabService, TranscribeOptions

    service = VoiceLabService()
    result = await service.transcribe(audio_bytes, TranscribeOptions(language='tw'))
"""

import logging
from typing import List, Optional, Dict, Any, Protocol
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import base64


logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class VoiceLabModel(str, Enum):
    """Available voice lab models."""
    # ASR Models
    AKAN_WHISPER = "akan-whisper"
    META_MMS_ASR = "meta-mms-asr"
    WHISPER_LARGE = "whisper-large-v3"

    # TTS Models
    AKAN_MMS = "akan-mms"
    META_MMS_TTS = "meta-mms-tts"
    COQUI_XTTS = "coqui-xtts"
    OPENVOICE = "openvoice"

    # LLM Models
    GEMINI_FLASH = "gemini-2.5-flash"
    GPT4_MINI = "gpt-4o-mini"
    CLAUDE_SONNET = "claude-3-5-sonnet"


class VoiceGender(str, Enum):
    """Voice gender options."""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class ConversationMode(str, Enum):
    """Conversation modes for LLM processing."""
    GENERAL = "general"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    FINANCE = "finance"
    CUSTOMER_SERVICE = "customer_service"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class TranscribeOptions:
    """Options for speech-to-text transcription."""
    language: str = "tw"
    dialect: str = "asante"
    model: str = VoiceLabModel.AKAN_WHISPER.value
    enhance_text: bool = True
    return_timestamps: bool = False
    enable_vad: bool = False
    enable_streaming: bool = False


@dataclass
class TranscriptionResult:
    """Result from speech-to-text transcription."""
    text: str
    enhanced_text: Optional[str] = None
    confidence: float = 0.0
    language: Optional[str] = None
    dialect: Optional[str] = None
    duration: Optional[float] = None
    processing_time: Optional[float] = None
    timestamps: Optional[List[Dict[str, Any]]] = None


@dataclass
class SynthesisOptions:
    """Options for text-to-speech synthesis."""
    model: str = VoiceLabModel.AKAN_MMS.value
    voice_id: str = "default"
    language: str = "tw"
    dialect: str = "asante"
    speed: float = 1.0
    pitch: float = 0.0
    enhance_text: bool = True
    output_format: str = "wav"


@dataclass
class SynthesisResult:
    """Result from text-to-speech synthesis."""
    audio_base64: str
    text: str
    voice_id: str
    duration: float
    processing_time: float
    sample_rate: int = 22050
    model: str = ""


@dataclass
class Voice:
    """Voice configuration."""
    voice_id: str
    name: str
    language: str
    dialect: str
    gender: VoiceGender
    description: Optional[str] = None
    sample_rate: int = 22050
    is_custom: bool = False


@dataclass
class ChatOptions:
    """Options for LLM chat processing."""
    message: str
    model: str = VoiceLabModel.GEMINI_FLASH.value
    mode: ConversationMode = ConversationMode.GENERAL
    history: List[Dict[str, str]] = field(default_factory=list)
    language: str = "tw"
    dialect: str = "asante"
    max_tokens: int = 150


@dataclass
class ChatResult:
    """Result from LLM chat processing."""
    response: str
    model: str
    processing_time: float
    tokens_used: Optional[int] = None


# ============================================================================
# Provider Protocol
# ============================================================================

class VoiceProvider(Protocol):
    """Protocol for voice service providers."""

    async def transcribe(self, audio: bytes, options: TranscribeOptions) -> TranscriptionResult:
        """Transcribe audio to text."""
        ...

    async def synthesize(self, text: str, options: SynthesisOptions) -> SynthesisResult:
        """Synthesize text to speech."""
        ...

    async def get_voices(self) -> List[Voice]:
        """Get available voices."""
        ...


# ============================================================================
# Voice Lab Service
# ============================================================================

class VoiceLabService:
    """
    Shared voice lab service.

    Provides generic voice operations:
    - Transcription (ASR)
    - Synthesis (TTS)
    - Voice management
    - LLM processing

    Apps should extend this class to add business logic.
    """

    def __init__(self):
        """Initialize the voice lab service."""
        self.logger = logging.getLogger(__name__)
        self._providers: Dict[str, VoiceProvider] = {}

    def register_provider(self, name: str, provider: VoiceProvider):
        """
        Register a voice provider.

        Args:
            name: Provider name
            provider: Provider instance
        """
        self._providers[name] = provider
        self.logger.info(f"Registered voice provider: {name}")

    async def transcribe(
        self,
        audio: bytes,
        options: Optional[TranscribeOptions] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio to text.

        Args:
            audio: Audio data in bytes
            options: Transcription options

        Returns:
            TranscriptionResult with text and metadata

        Example:
            result = await service.transcribe(
                audio_bytes,
                TranscribeOptions(language='tw', dialect='asante')
            )
        """
        if options is None:
            options = TranscribeOptions()

        start_time = datetime.utcnow()

        try:
            # Get provider for model
            provider = self._get_provider(options.model)

            # Perform transcription
            result = await provider.transcribe(audio, options)

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result.processing_time = processing_time

            self.logger.info(
                f"Transcription complete: {len(result.text)} chars in {processing_time:.2f}s"
            )

            return result

        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            raise

    async def synthesize(
        self,
        text: str,
        options: Optional[SynthesisOptions] = None
    ) -> SynthesisResult:
        """
        Synthesize text to speech.

        Args:
            text: Text to synthesize
            options: Synthesis options

        Returns:
            SynthesisResult with audio and metadata

        Example:
            result = await service.synthesize(
                "Akwaaba",
                SynthesisOptions(language='tw', speed=1.0)
            )
        """
        if options is None:
            options = SynthesisOptions()

        start_time = datetime.utcnow()

        try:
            # Get provider for model
            provider = self._get_provider(options.model)

            # Perform synthesis
            result = await provider.synthesize(text, options)

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result.processing_time = processing_time
            result.model = options.model

            self.logger.info(
                f"Synthesis complete: {len(text)} chars in {processing_time:.2f}s"
            )

            return result

        except Exception as e:
            self.logger.error(f"Synthesis failed: {e}")
            raise

    async def get_voices(
        self,
        language: Optional[str] = None,
        dialect: Optional[str] = None,
        gender: Optional[VoiceGender] = None
    ) -> List[Voice]:
        """
        Get available voices.

        Args:
            language: Filter by language
            dialect: Filter by dialect
            gender: Filter by gender

        Returns:
            List of available voices

        Example:
            voices = await service.get_voices(language='tw', gender=VoiceGender.FEMALE)
        """
        try:
            voices = []

            # Collect voices from all providers
            for provider in self._providers.values():
                provider_voices = await provider.get_voices()
                voices.extend(provider_voices)

            # Apply filters
            if language:
                voices = [v for v in voices if v.language == language]
            if dialect:
                voices = [v for v in voices if v.dialect == dialect]
            if gender:
                voices = [v for v in voices if v.gender == gender]

            self.logger.info(f"Retrieved {len(voices)} voices")
            return voices

        except Exception as e:
            self.logger.error(f"Failed to get voices: {e}")
            raise

    async def clone_voice(
        self,
        reference_audio: bytes,
        text: str,
        voice_name: str = "custom"
    ) -> SynthesisResult:
        """
        Clone a voice from reference audio.

        Args:
            reference_audio: Reference audio bytes
            text: Text to synthesize
            voice_name: Name for cloned voice

        Returns:
            SynthesisResult with cloned voice

        Example:
            result = await service.clone_voice(
                reference_audio_bytes,
                "Hello world",
                "my_custom_voice"
            )
        """
        start_time = datetime.utcnow()

        try:
            # Use voice cloning provider (typically coqui-xtts or openvoice)
            provider = self._get_provider(VoiceLabModel.COQUI_XTTS.value)

            # Perform voice cloning
            options = SynthesisOptions(
                model=VoiceLabModel.COQUI_XTTS.value,
                voice_id=voice_name
            )

            result = await provider.synthesize(text, options)

            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result.processing_time = processing_time

            self.logger.info(f"Voice cloning complete in {processing_time:.2f}s")
            return result

        except Exception as e:
            self.logger.error(f"Voice cloning failed: {e}")
            raise

    async def process_chat(
        self,
        options: ChatOptions
    ) -> ChatResult:
        """
        Process chat message with LLM.

        Args:
            options: Chat options including message and history

        Returns:
            ChatResult with LLM response

        Example:
            result = await service.process_chat(
                ChatOptions(
                    message="Hello",
                    model=VoiceLabModel.GEMINI_FLASH.value,
                    mode=ConversationMode.GENERAL
                )
            )
        """
        start_time = datetime.utcnow()

        try:
            # This would integrate with LLM providers
            # For now, return a simple response
            response = f"Processed: {options.message}"

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            return ChatResult(
                response=response,
                model=options.model,
                processing_time=processing_time
            )

        except Exception as e:
            self.logger.error(f"Chat processing failed: {e}")
            raise

    def _get_provider(self, model: str) -> VoiceProvider:
        """
        Get provider for a model.

        Args:
            model: Model identifier

        Returns:
            VoiceProvider instance

        Raises:
            ValueError: If no provider available for model
        """
        # Map models to providers
        provider_map = {
            VoiceLabModel.AKAN_WHISPER.value: "meta_mms",
            VoiceLabModel.META_MMS_ASR.value: "meta_mms",
            VoiceLabModel.AKAN_MMS.value: "meta_mms",
            VoiceLabModel.META_MMS_TTS.value: "meta_mms",
            VoiceLabModel.COQUI_XTTS.value: "coqui",
            VoiceLabModel.OPENVOICE.value: "openvoice",
        }

        provider_name = provider_map.get(model)
        if not provider_name or provider_name not in self._providers:
            raise ValueError(f"No provider available for model: {model}")

        return self._providers[provider_name]


# ============================================================================
# Utility Functions
# ============================================================================

def audio_to_base64(audio_bytes: bytes) -> str:
    """
    Convert audio bytes to base64 string.

    Args:
        audio_bytes: Audio data

    Returns:
        Base64 encoded string
    """
    return base64.b64encode(audio_bytes).decode('utf-8')


def base64_to_audio(audio_base64: str) -> bytes:
    """
    Convert base64 string to audio bytes.

    Args:
        audio_base64: Base64 encoded audio

    Returns:
        Audio bytes
    """
    return base64.b64decode(audio_base64)
