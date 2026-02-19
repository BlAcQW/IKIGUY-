"""
Enhanced Voice Service - Integrates Unified and Shared Services

This service acts as a bridge between:
- Unified ASR/TTS Services (core_backend)
- Shared STT/TTS Services (@apps/shared)
- ASR Provider Service (with billing & health monitoring)

Features:
- Automatic fallback chains
- Cost tracking and billing
- Provider health monitoring
- Comprehensive error handling
- Performance metrics

Author: AI Labs Africa
Created: 2025-11-07
"""

import logging
import asyncio
import numpy as np
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Import unified services (local)
from .unified_asr_service import (
    UnifiedASRService,
    ASRModel,
    ASRResult as UnifiedASRResult,
    get_unified_asr_service
)
from apps.shared.integration.ai_services import (
    UnifiedTTSService,
    TTSModel,
    TTSResult,
    get_unified_tts_service
)

# Import shared services (fallback)
try:
    from apps.shared.integration.ai_services.stt_service import STTService, STTProvider
    from apps.shared.integration.ai_services.tts_service import TTSService, TTSProvider
    from apps.shared.services.asr_provider_service import (
        ASRProviderService,
        TranscriptionRequest,
        get_asr_service
    )
    SHARED_SERVICES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Shared services not available: {e}")
    SHARED_SERVICES_AVAILABLE = False

logger = logging.getLogger(__name__)


class ServiceMode(str, Enum):
    """Service operation mode"""
    UNIFIED_ONLY = "unified_only"  # Use only unified services
    SHARED_ONLY = "shared_only"    # Use only shared services
    HYBRID = "hybrid"                # Try unified first, fallback to shared
    AUTO = "auto"                    # Automatically choose best provider


@dataclass
class VoiceServiceConfig:
    """Configuration for enhanced voice service"""
    mode: ServiceMode = ServiceMode.HYBRID
    enable_cost_tracking: bool = True
    enable_health_monitoring: bool = True
    enable_fallback: bool = True
    max_retries: int = 2
    timeout_seconds: float = 30.0

    # Primary providers
    primary_stt_model: ASRModel = ASRModel.AKAN_WHISPER
    primary_tts_model: TTSModel = TTSModel.AKAN_MMS

    # Fallback providers
    fallback_stt_provider: str = "openai"  # For shared service
    fallback_tts_provider: str = "openai"  # For shared service


@dataclass
class EnhancedASRResult:
    """Enhanced ASR result with provider info and costs"""
    text: str
    confidence: float
    language: str
    dialect: Optional[str]
    duration: float
    processing_time: float
    model: str
    provider: str  # "unified" or "shared"
    cost_usd: float = 0.0
    transaction_id: Optional[str] = None
    fallback_used: bool = False
    timestamps: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class EnhancedTTSResult:
    """Enhanced TTS result with provider info and costs"""
    audio_base64: str
    text: str
    voice_id: str
    duration: float
    processing_time: float
    sample_rate: int
    model: str
    provider: str  # "unified" or "shared"
    cost_usd: float = 0.0
    format: str = "wav"
    fallback_used: bool = False
    metadata: Optional[Dict[str, Any]] = None


class EnhancedVoiceService:
    """
    Enhanced voice service with unified + shared integration.

    Provides:
    - Automatic provider selection
    - Fallback chains
    - Cost tracking
    - Health monitoring
    - Performance metrics
    """

    def __init__(self, config: Optional[VoiceServiceConfig] = None):
        """
        Initialize enhanced voice service.

        Args:
            config: Service configuration
        """
        self.config = config or VoiceServiceConfig()

        # Initialize unified services
        self.unified_asr = get_unified_asr_service(
            default_model=self.config.primary_stt_model
        )
        self.unified_tts = get_unified_tts_service(
            default_model=self.config.primary_tts_model
        )

        # Initialize shared services if available
        self.shared_stt: Optional[STTService] = None
        self.shared_tts: Optional[TTSService] = None
        self.asr_provider_service: Optional[ASRProviderService] = None

        if SHARED_SERVICES_AVAILABLE and self.config.mode != ServiceMode.UNIFIED_ONLY:
            self._initialize_shared_services()

        # Performance tracking
        self.stats = {
            "total_stt_requests": 0,
            "total_tts_requests": 0,
            "unified_stt_success": 0,
            "unified_tts_success": 0,
            "shared_stt_fallback": 0,
            "shared_tts_fallback": 0,
            "total_cost_usd": 0.0,
            "errors": []
        }

        logger.info(f"Enhanced Voice Service initialized (mode={self.config.mode})")

    def _initialize_shared_services(self):
        """Initialize shared services for fallback."""
        try:
            import os

            # Initialize shared STT service
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self.shared_stt = STTService(
                    provider=self.config.fallback_stt_provider,
                    api_key=openai_key,
                    model="whisper-1"
                )
                logger.info(f"Shared STT service initialized ({self.config.fallback_stt_provider})")

            # Initialize shared TTS service
            if openai_key:
                self.shared_tts = TTSService(
                    provider=self.config.fallback_tts_provider,
                    api_key=openai_key,
                    voice="nova",
                    model="tts-1"
                )
                logger.info(f"Shared TTS service initialized ({self.config.fallback_tts_provider})")

            # Initialize ASR provider service (with billing)
            if self.config.enable_cost_tracking:
                # Note: This requires database setup
                logger.info("Cost tracking enabled - ASR Provider Service will be used when available")

        except Exception as e:
            logger.warning(f"Failed to initialize shared services: {e}")

    async def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        model: Optional[ASRModel] = None,
        language: str = "tw",
        dialect: str = "asante",
        user_id: Optional[str] = None,
        return_timestamps: bool = False
    ) -> EnhancedASRResult:
        """
        Transcribe audio with automatic fallback.

        Args:
            audio_data: Audio numpy array
            sample_rate: Sample rate
            model: ASR model to use
            language: Language code
            dialect: Dialect
            user_id: User ID for billing
            return_timestamps: Return word timestamps

        Returns:
            EnhancedASRResult with transcription and metadata
        """
        self.stats["total_stt_requests"] += 1
        start_time = datetime.utcnow()
        fallback_used = False
        cost = 0.0
        transaction_id = None

        # Try unified service first (or if mode is UNIFIED_ONLY)
        if self.config.mode in [ServiceMode.UNIFIED_ONLY, ServiceMode.HYBRID, ServiceMode.AUTO]:
            try:
                logger.info(f"🎤 Attempting transcription with unified service (model={model or self.config.primary_stt_model})")

                result = await self.unified_asr.transcribe(
                    audio_data=audio_data,
                    sample_rate=sample_rate,
                    model=model or self.config.primary_stt_model,
                    language=language,
                    dialect=dialect,
                    return_timestamps=return_timestamps,
                    user_id=user_id
                )

                processing_time = (datetime.utcnow() - start_time).total_seconds()
                self.stats["unified_stt_success"] += 1

                # Calculate cost (estimated)
                duration = result.duration
                cost = self._estimate_stt_cost(duration, str(result.model))
                self.stats["total_cost_usd"] += cost

                logger.info(f"✅ Unified STT success: '{result.text[:50]}...' (cost=${cost:.4f})")

                return EnhancedASRResult(
                    text=result.text,
                    confidence=result.confidence,
                    language=result.language,
                    dialect=result.dialect,
                    duration=result.duration,
                    processing_time=processing_time,
                    model=str(result.model),
                    provider="unified",
                    cost_usd=cost,
                    transaction_id=transaction_id,
                    fallback_used=False,
                    timestamps=result.timestamps,
                    metadata=result.metadata
                )

            except Exception as unified_error:
                logger.error(f"❌ Unified STT failed: {unified_error}")
                self.stats["errors"].append({
                    "service": "unified_stt",
                    "error": str(unified_error),
                    "timestamp": datetime.utcnow().isoformat()
                })

                # Try fallback if enabled
                if not self.config.enable_fallback:
                    raise

                if self.config.mode == ServiceMode.UNIFIED_ONLY:
                    raise

                logger.warning("⚠️ Trying shared service fallback...")
                fallback_used = True

        # Try shared service (fallback or if mode is SHARED_ONLY)
        if (fallback_used or self.config.mode == ServiceMode.SHARED_ONLY) and self.shared_stt:
            try:
                logger.info(f"🔄 Attempting transcription with shared service ({self.config.fallback_stt_provider})")

                # Convert numpy array to bytes
                import soundfile as sf
                import io
                import base64

                buffer = io.BytesIO()
                sf.write(buffer, audio_data, sample_rate, format='WAV')
                audio_bytes = buffer.getvalue()

                # Transcribe
                result_text = await self.shared_stt.transcribe(
                    audio_bytes=audio_bytes,
                    audio_format="wav",
                    language=language
                )

                processing_time = (datetime.utcnow() - start_time).total_seconds()
                self.stats["shared_stt_fallback"] += 1

                # Calculate cost
                duration = len(audio_data) / sample_rate
                cost = self.shared_stt.get_cost_per_minute() * (duration / 60)
                self.stats["total_cost_usd"] += cost

                logger.info(f"✅ Shared STT success: '{result_text[:50]}...' (cost=${cost:.4f})")

                return EnhancedASRResult(
                    text=result_text,
                    confidence=0.9,  # Shared service doesn't provide confidence
                    language=language,
                    dialect=dialect,
                    duration=duration,
                    processing_time=processing_time,
                    model=self.config.fallback_stt_provider,
                    provider="shared",
                    cost_usd=cost,
                    transaction_id=None,
                    fallback_used=True,
                    timestamps=None,
                    metadata={"provider_type": "api"}
                )

            except Exception as shared_error:
                logger.error(f"❌ Shared STT also failed: {shared_error}")
                self.stats["errors"].append({
                    "service": "shared_stt",
                    "error": str(shared_error),
                    "timestamp": datetime.utcnow().isoformat()
                })
                raise Exception(f"Both unified and shared STT failed. Last error: {shared_error}")

        # If we get here and no service worked
        raise Exception("No STT service available or all failed")

    async def synthesize(
        self,
        text: str,
        model: Optional[TTSModel] = None,
        voice_id: str = "default",
        speed: float = 1.0,
        language: str = "tw",
        dialect: str = "asante",
        user_id: Optional[str] = None
    ) -> EnhancedTTSResult:
        """
        Synthesize speech with automatic fallback.

        Args:
            text: Text to synthesize
            model: TTS model to use
            voice_id: Voice identifier
            speed: Speech speed
            language: Language code
            dialect: Dialect
            user_id: User ID for billing

        Returns:
            EnhancedTTSResult with audio and metadata
        """
        self.stats["total_tts_requests"] += 1
        start_time = datetime.utcnow()
        fallback_used = False
        cost = 0.0

        # Try unified service first
        if self.config.mode in [ServiceMode.UNIFIED_ONLY, ServiceMode.HYBRID, ServiceMode.AUTO]:
            try:
                logger.info(f"🔊 Attempting synthesis with unified service (model={model or self.config.primary_tts_model})")

                # Unified TTS is sync, run in thread pool to avoid blocking
                result = await asyncio.to_thread(
                    self.unified_tts.synthesize,
                    text=text,
                    model=model or self.config.primary_tts_model,
                    voice_id=voice_id,
                    speed=speed,
                    language=language,
                    dialect=dialect,
                    user_id=user_id
                )

                processing_time = (datetime.utcnow() - start_time).total_seconds()
                self.stats["unified_tts_success"] += 1

                # Calculate cost
                cost = self._estimate_tts_cost(len(text), str(result.model))
                self.stats["total_cost_usd"] += cost

                logger.info(f"✅ Unified TTS success: {len(text)} chars (cost=${cost:.4f})")

                return EnhancedTTSResult(
                    audio_base64=result.audio_base64,
                    text=text,
                    voice_id=voice_id,
                    duration=result.duration,
                    processing_time=processing_time,
                    sample_rate=result.sample_rate,
                    model=str(result.model),
                    provider="unified",
                    cost_usd=cost,
                    format=result.format,
                    fallback_used=False,
                    metadata=result.metadata
                )

            except Exception as unified_error:
                logger.error(f"❌ Unified TTS failed: {unified_error}")
                self.stats["errors"].append({
                    "service": "unified_tts",
                    "error": str(unified_error),
                    "timestamp": datetime.utcnow().isoformat()
                })

                if not self.config.enable_fallback or self.config.mode == ServiceMode.UNIFIED_ONLY:
                    raise

                logger.warning("⚠️ Trying shared service fallback...")
                fallback_used = True

        # Try shared service (fallback or if mode is SHARED_ONLY)
        if (fallback_used or self.config.mode == ServiceMode.SHARED_ONLY) and self.shared_tts:
            try:
                logger.info(f"🔄 Attempting synthesis with shared service ({self.config.fallback_tts_provider})")

                # Import here to avoid circular dependencies
                import asyncio

                # Synthesize (async)
                audio_bytes = await self.shared_tts.synthesize(
                    text=text,
                    speed=speed
                )

                # Convert to base64
                import base64
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

                processing_time = (datetime.utcnow() - start_time).total_seconds()
                self.stats["shared_tts_fallback"] += 1

                # Calculate cost
                cost = self.shared_tts.get_cost_per_1k_chars() * (len(text) / 1000)
                self.stats["total_cost_usd"] += cost

                logger.info(f"✅ Shared TTS success: {len(text)} chars (cost=${cost:.4f})")

                # Estimate duration (rough)
                # Typical speech: ~150 words per minute, ~5 chars per word
                words = len(text) / 5
                duration = (words / 150) * 60

                return EnhancedTTSResult(
                    audio_base64=audio_base64,
                    text=text,
                    voice_id=voice_id,
                    duration=duration,
                    processing_time=processing_time,
                    sample_rate=24000,  # OpenAI default
                    model=self.config.fallback_tts_provider,
                    provider="shared",
                    cost_usd=cost,
                    format="mp3",
                    fallback_used=True,
                    metadata={"provider_type": "api"}
                )

            except Exception as shared_error:
                logger.error(f"❌ Shared TTS also failed: {shared_error}")
                self.stats["errors"].append({
                    "service": "shared_tts",
                    "error": str(shared_error),
                    "timestamp": datetime.utcnow().isoformat()
                })
                raise Exception(f"Both unified and shared TTS failed. Last error: {shared_error}")

        raise Exception("No TTS service available or all failed")

    def _estimate_stt_cost(self, duration_seconds: float, model: str) -> float:
        """Estimate STT cost based on duration and model."""
        # Default costs per minute
        costs = {
            "akan-whisper": 0.0,  # Self-hosted
            "faster-whisper": 0.0,  # Self-hosted
            "openai": 0.006,  # $0.006 per minute
            "google": 0.006,
            "assemblyai": 0.015,
            "deepgram": 0.0043
        }

        # Get cost per minute
        cost_per_min = costs.get(model.lower(), 0.01)

        # Calculate total cost
        return (duration_seconds / 60) * cost_per_min

    def _estimate_tts_cost(self, char_count: int, model: str) -> float:
        """Estimate TTS cost based on character count and model."""
        # Default costs per 1K characters
        costs = {
            "akan-mms": 0.0,  # Self-hosted
            "xtts-v2": 0.0,  # Self-hosted
            "openai": 0.015,  # $15 per 1M chars
            "google": 0.004,
            "elevenlabs": 0.30,
            "playht": 0.015
        }

        # Get cost per 1K chars
        cost_per_1k = costs.get(model.lower(), 0.02)

        # Calculate total cost
        return (char_count / 1000) * cost_per_1k

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        total_requests = self.stats["total_stt_requests"] + self.stats["total_tts_requests"]
        unified_success = self.stats["unified_stt_success"] + self.stats["unified_tts_success"]
        shared_fallback = self.stats["shared_stt_fallback"] + self.stats["shared_tts_fallback"]

        return {
            **self.stats,
            "total_requests": total_requests,
            "unified_success_rate": unified_success / total_requests if total_requests > 0 else 0,
            "fallback_rate": shared_fallback / total_requests if total_requests > 0 else 0,
            "average_cost_per_request": self.stats["total_cost_usd"] / total_requests if total_requests > 0 else 0
        }


# Singleton instance
_enhanced_voice_service: Optional[EnhancedVoiceService] = None


def get_enhanced_voice_service(config: Optional[VoiceServiceConfig] = None) -> EnhancedVoiceService:
    """Get singleton enhanced voice service instance."""
    global _enhanced_voice_service

    if _enhanced_voice_service is None:
        _enhanced_voice_service = EnhancedVoiceService(config)

    return _enhanced_voice_service
