"""
Unified ASR Service - Production-grade abstraction for multiple ASR models

Supports:
- Akan Whisper (92.9% accuracy)
- Faster Whisper
- Meta MMS-1B
- Wav2Vec2 variants
- Real-time streaming with VAD
"""

import logging
import time
import numpy as np
from typing import Dict, Any, Optional, List, AsyncGenerator
from enum import Enum
from dataclasses import dataclass
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class ASRModel(str, Enum):
    """Available ASR model types"""
    AKAN_WHISPER = "akan-whisper"
    FASTER_WHISPER = "faster-whisper"
    AFRICAN_WHISPER = "african-whisper"
    WHISPER_LARGE_V3 = "whisper-large-v3"
    META_MMS = "meta-mms"
    WAV2VEC2_AKAN = "wav2vec2-akan"
    MOSHI = "moshi"


@dataclass
class ASRResult:
    """Standardized ASR result format"""
    text: str
    confidence: float
    language: str
    dialect: Optional[str]
    duration: float
    processing_time: float
    model: str
    timestamps: Optional[List[Dict[str, Any]]] = None
    segments: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ASRModelConfig:
    """Configuration for an ASR model"""
    model_id: str
    name: str
    accuracy: float
    languages: List[str]
    dialects: List[str]
    provider: str
    supports_streaming: bool = False
    supports_timestamps: bool = True
    max_duration: float = 30.0
    sample_rate: int = 16000


class UnifiedASRService:
    """
    Unified interface for all ASR models with automatic fallback,
    performance monitoring, and production features.
    """

    # Model configurations
    MODEL_CONFIGS = {
        ASRModel.AKAN_WHISPER: ASRModelConfig(
            model_id="GiftMark/akan-whisper-model",
            name="Akan Whisper (92.9%)",
            accuracy=0.929,
            languages=["tw"],
            dialects=["asante", "akuapem", "fante"],
            provider="GiftMark",
            supports_streaming=True,  # Enabled via faster-whisper conversion
            supports_timestamps=True
        ),
        ASRModel.FASTER_WHISPER: ASRModelConfig(
            model_id="Systran/faster-whisper-base",
            name="Faster Whisper",
            accuracy=0.95,
            languages=["tw", "en", "fr"],
            dialects=["asante", "akuapem"],
            provider="Systran",
            supports_streaming=True,
            supports_timestamps=True
        ),
        ASRModel.META_MMS: ASRModelConfig(
            model_id="facebook/mms-1b-all",
            name="Meta MMS-1B",
            accuracy=0.88,
            languages=["tw", "en", "ewe", "ga"],
            dialects=["asante", "akuapem"],
            provider="Meta",
            supports_streaming=False,
            supports_timestamps=False
        ),
        ASRModel.WAV2VEC2_AKAN: ASRModelConfig(
            model_id="wav2vec2-akan",
            name="Wav2Vec2 Akan",
            accuracy=0.85,
            languages=["tw"],
            dialects=["asante"],
            provider="Community",
            supports_streaming=False,
            supports_timestamps=False
        ),
        ASRModel.WHISPER_LARGE_V3: ASRModelConfig(
            model_id="openai/whisper-large-v3",
            name="Whisper Large v3",
            accuracy=0.96,
            languages=["en", "tw", "fr", "es", "zh", "ja", "ko", "ar"],  # 99 languages
            dialects=["asante", "akuapem"],
            provider="OpenAI",
            supports_streaming=False,
            supports_timestamps=True,
            max_duration=30.0,
            sample_rate=16000
        ),
        ASRModel.AFRICAN_WHISPER: ASRModelConfig(
            model_id="African-Whisper/african-whisper",
            name="African Whisper (Multi-dialect)",
            accuracy=0.91,
            languages=["tw", "en", "ewe", "ga", "hau", "yor"],
            dialects=["asante", "akuapem", "fante"],
            provider="Community",
            supports_streaming=False,
            supports_timestamps=True,
            max_duration=30.0,
            sample_rate=16000
        ),
        ASRModel.MOSHI: ASRModelConfig(
            model_id="kyutai/moshi",
            name="Moshi (Real-time Conversational)",
            accuracy=0.88,
            languages=["en", "fr", "es"],
            dialects=[],
            provider="Kyutai",
            supports_streaming=True,
            supports_timestamps=False,
            max_duration=300.0,  # 5 minutes for conversations
            sample_rate=24000
        ),
    }

    def __init__(self, default_model: ASRModel = ASRModel.AKAN_WHISPER):
        """
        Initialize unified ASR service.

        Args:
            default_model: Default ASR model to use
        """
        self.default_model = default_model
        self.loaded_models: Dict[ASRModel, Any] = {}
        self.model_stats: Dict[ASRModel, Dict[str, Any]] = {}

        # Initialize stats for all models
        for model in ASRModel:
            self.model_stats[model] = {
                "total_requests": 0,
                "total_duration": 0.0,
                "total_processing_time": 0.0,
                "errors": 0,
                "last_used": None
            }

        # Lazy load models
        self._load_lock = asyncio.Lock()

        logger.info(f"Unified ASR Service initialized with default model: {default_model}")

    async def _load_model(self, model: ASRModel) -> Any:
        """
        Load an ASR model on-demand.

        Args:
            model: Model to load

        Returns:
            Loaded model instance
        """
        async with self._load_lock:
            # Check if already loaded
            if model in self.loaded_models:
                return self.loaded_models[model]

            logger.info(f"Loading ASR model: {model}")
            start_time = time.time()

            try:
                if model == ASRModel.AKAN_WHISPER:
                    from .twi_whisper_service import get_twi_whisper_service
                    model_instance = get_twi_whisper_service(model_name="akan")

                elif model == ASRModel.FASTER_WHISPER:
                    # Use standalone GPU-accelerated Whisper API at whisper.ailabsafrica.com
                    # Falls back to local faster_whisper_service if API unavailable
                    from .whisper_api_client import get_whisper_api_client
                    api_client = get_whisper_api_client()
                    health = await api_client.health_check()
                    if health.get("status") == "healthy":
                        logger.info("Using standalone Whisper API (GPU-accelerated)")
                        model_instance = api_client
                    else:
                        logger.warning(f"Whisper API unavailable, falling back to local: {health}")
                        from .faster_whisper_service import get_faster_whisper_service
                        model_instance = get_faster_whisper_service()

                elif model == ASRModel.META_MMS:
                    from .meta_mms_service import mms_service
                    await mms_service.initialize()
                    model_instance = mms_service

                elif model == ASRModel.WHISPER_LARGE_V3:
                    from .whisper_service import get_whisper_service
                    model_instance = get_whisper_service(model_size="large-v3")

                elif model == ASRModel.AFRICAN_WHISPER:
                    from .twi_whisper_service import get_twi_whisper_service
                    model_instance = get_twi_whisper_service(model_name="african")

                elif model == ASRModel.MOSHI:
                    # Moshi uses a different architecture (conversational AI)
                    # Fall back to Whisper API for now
                    logger.warning(f"Model {model} requires separate service, using Whisper API fallback")
                    from .whisper_api_client import get_whisper_api_client
                    model_instance = get_whisper_api_client()

                elif model == ASRModel.WAV2VEC2_AKAN:
                    # Placeholder for Wav2Vec2
                    logger.warning(f"Model {model} not yet implemented, using Akan Whisper fallback")
                    from .twi_whisper_service import get_twi_whisper_service
                    model_instance = get_twi_whisper_service(model_name="akan")

                else:
                    raise ValueError(f"Unknown model: {model}")

                self.loaded_models[model] = model_instance
                load_time = time.time() - start_time

                logger.info(f"✅ Model {model} loaded in {load_time:.2f}s")
                return model_instance

            except Exception as e:
                logger.error(f"Failed to load model {model}: {e}")
                raise

    async def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        model: Optional[ASRModel] = None,
        language: str = "tw",
        dialect: str = "asante",
        return_timestamps: bool = False,
        enable_vad: bool = False,
        enable_streaming: bool = False,
        user_id: Optional[str] = None
    ) -> ASRResult:
        """
        Transcribe audio using specified model.

        Args:
            audio_data: Audio numpy array
            sample_rate: Sample rate
            model: ASR model to use (defaults to service default)
            language: Language code
            dialect: Dialect
            return_timestamps: Return word-level timestamps
            enable_vad: Enable voice activity detection
            enable_streaming: Enable streaming mode
            user_id: User ID for tracking

        Returns:
            ASRResult with transcription
        """
        model = model or self.default_model
        start_time = time.time()

        try:
            # Debug: Log model before and after
            logger.info(f"🔍 DEBUG ASR: Received model={model}, type={type(model)}, default={self.default_model}")

            # Load model if needed
            model_instance = await self._load_model(model)

            # Calculate duration
            duration = len(audio_data) / sample_rate if len(audio_data.shape) == 1 else len(audio_data[0]) / sample_rate

            logger.info(f"Transcribing {duration:.2f}s audio with {model}")

            # Apply VAD if requested
            if enable_vad:
                audio_data = await self._apply_vad(audio_data, sample_rate)

            # Route to appropriate model
            result = await self._transcribe_with_model(
                model_instance,
                model,
                audio_data,
                sample_rate,
                language,
                return_timestamps
            )

            processing_time = time.time() - start_time

            # Update stats
            self._update_stats(model, duration, processing_time, success=True)

            # Create standardized result
            asr_result = ASRResult(
                text=result["text"],
                confidence=result.get("confidence", 0.9),
                language=language,
                dialect=result.get("dialect", dialect),
                duration=duration,
                processing_time=processing_time,
                model=model.value,
                timestamps=result.get("timestamps"),
                segments=result.get("segments"),
                metadata={
                    "sample_rate": sample_rate,
                    "vad_enabled": enable_vad,
                    "streaming_enabled": enable_streaming,
                    "user_id": user_id,
                    "accuracy": self.MODEL_CONFIGS[model].accuracy
                }
            )

            logger.info(f"✅ Transcription complete: {len(result['text'])} chars in {processing_time:.2f}s")
            return asr_result

        except Exception as e:
            processing_time = time.time() - start_time
            self._update_stats(model, 0, processing_time, success=False)
            logger.error(f"Transcription failed with {model}: {e}")

            # Try fallback to Akan Whisper if not already using it
            if model != ASRModel.AKAN_WHISPER:
                logger.info(f"Attempting fallback to {ASRModel.AKAN_WHISPER}")
                return await self.transcribe(
                    audio_data,
                    sample_rate,
                    model=ASRModel.AKAN_WHISPER,
                    language=language,
                    dialect=dialect,
                    return_timestamps=return_timestamps,
                    enable_vad=False,
                    enable_streaming=False,
                    user_id=user_id
                )

            raise

    async def _transcribe_with_model(
        self,
        model_instance: Any,
        model: ASRModel,
        audio_data: np.ndarray,
        sample_rate: int,
        language: str,
        return_timestamps: bool
    ) -> Dict[str, Any]:
        """
        Transcribe with a specific model instance.

        Args:
            model_instance: Loaded model instance
            model: Model type
            audio_data: Audio data
            sample_rate: Sample rate
            language: Language code
            return_timestamps: Return timestamps

        Returns:
            Raw transcription result
        """
        if model in [ASRModel.AKAN_WHISPER, ASRModel.FASTER_WHISPER, ASRModel.WAV2VEC2_AKAN,
                     ASRModel.WHISPER_LARGE_V3, ASRModel.AFRICAN_WHISPER, ASRModel.MOSHI]:
            # Whisper-based models (includes all Whisper variants)

            # FASTER_WHISPER uses transcribe_audio(), others use transcribe()
            if model == ASRModel.FASTER_WHISPER:
                # Save audio temporarily for Faster Whisper
                import tempfile
                import soundfile as sf
                from pathlib import Path

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    sf.write(tmp.name, audio_data, sample_rate)
                    tmp_path = tmp.name

                try:
                    result = await model_instance.transcribe_audio(
                        tmp_path,
                        language=language,
                        task="transcribe"
                    )

                    # Handle both dict and object responses
                    if isinstance(result, dict):
                        return result
                    else:
                        # It's a dataclass object
                        segments_list = []
                        if hasattr(result, 'segments') and result.segments:
                            for seg in result.segments:
                                if isinstance(seg, dict):
                                    segments_list.append(seg)
                                else:
                                    segments_list.append({
                                        "text": seg.get('text') if isinstance(seg, dict) else getattr(seg, 'text', ''),
                                        "start": seg.get('start') if isinstance(seg, dict) else getattr(seg, 'start', 0),
                                        "end": seg.get('end') if isinstance(seg, dict) else getattr(seg, 'end', 0)
                                    })

                        return {
                            "text": result.text,
                            "confidence": getattr(result, 'confidence', 0.9),
                            "segments": segments_list
                        }
                finally:
                    Path(tmp_path).unlink(missing_ok=True)
            else:
                # Akan Whisper and other Whisper variants use transcribe()
                return model_instance.transcribe(
                    audio_data,
                    sample_rate=sample_rate,
                    language=language,
                    return_timestamps=return_timestamps
                )

        elif model == ASRModel.META_MMS:
            # Save audio temporarily for MMS
            import tempfile
            import soundfile as sf
            from pathlib import Path

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, audio_data, sample_rate)
                tmp_path = tmp.name

            try:
                result = await model_instance.transcribe_audio(
                    tmp_path,
                    language=language
                )
                return {
                    "text": result.text,
                    "confidence": result.confidence,
                    "segments": [{"text": s["text"], "start": s["start"], "end": s["end"]}
                                for s in result.segments]
                }
            finally:
                Path(tmp_path).unlink(missing_ok=True)

        else:
            raise ValueError(f"Unknown model type: {model}")

    async def _apply_vad(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Apply Voice Activity Detection to remove silence.

        Args:
            audio_data: Audio data
            sample_rate: Sample rate

        Returns:
            Audio with silence removed
        """
        try:
            import torch

            # Simple energy-based VAD
            # TODO: Replace with more sophisticated VAD (e.g., Silero VAD)
            energy = np.abs(audio_data)
            threshold = np.mean(energy) * 0.5

            # Find voice segments
            is_voice = energy > threshold

            # Apply some smoothing
            from scipy.ndimage import binary_dilation
            is_voice = binary_dilation(is_voice, iterations=5)

            # Extract voice segments
            voice_audio = audio_data[is_voice]

            logger.info(f"VAD: Reduced audio from {len(audio_data)} to {len(voice_audio)} samples")
            return voice_audio

        except Exception as e:
            logger.warning(f"VAD failed, using original audio: {e}")
            return audio_data

    async def stream_transcribe(
        self,
        audio_stream: AsyncGenerator[np.ndarray, None],
        model: Optional[ASRModel] = None,
        language: str = "tw",
        dialect: str = "asante"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream transcription for real-time ASR.

        Args:
            audio_stream: Async generator yielding audio chunks
            model: ASR model to use
            language: Language code
            dialect: Dialect

        Yields:
            Partial transcription results
        """
        model = model or self.default_model

        # Check if model supports streaming
        if not self.MODEL_CONFIGS[model].supports_streaming:
            raise ValueError(f"Model {model} does not support streaming")

        model_instance = await self._load_model(model)

        buffer = []
        chunk_duration = 0.0

        async for chunk in audio_stream:
            buffer.append(chunk)
            chunk_duration += len(chunk) / 16000  # Assuming 16kHz

            # Process every 2 seconds
            if chunk_duration >= 2.0:
                full_audio = np.concatenate(buffer)

                try:
                    result = await self._transcribe_with_model(
                        model_instance,
                        model,
                        full_audio,
                        16000,
                        language,
                        False
                    )

                    yield {
                        "text": result["text"],
                        "is_final": False,
                        "confidence": result.get("confidence", 0.85)
                    }

                except Exception as e:
                    logger.error(f"Streaming transcription error: {e}")

                # Keep last 1 second for context
                buffer = [buffer[-1]]
                chunk_duration = len(buffer[0]) / 16000

    def _update_stats(self, model: ASRModel, duration: float, processing_time: float, success: bool):
        """
        Update model statistics.

        Args:
            model: Model used
            duration: Audio duration
            processing_time: Processing time
            success: Whether transcription succeeded
        """
        stats = self.model_stats[model]
        stats["total_requests"] += 1
        stats["total_duration"] += duration
        stats["total_processing_time"] += processing_time
        if not success:
            stats["errors"] += 1
        stats["last_used"] = datetime.now().isoformat()

    def get_model_info(self, model: Optional[ASRModel] = None) -> Dict[str, Any]:
        """
        Get information about a model.

        Args:
            model: Model to get info for (None for all models)

        Returns:
            Model information
        """
        if model:
            config = self.MODEL_CONFIGS[model]
            stats = self.model_stats[model]

            return {
                "model": model.value,
                "name": config.name,
                "accuracy": config.accuracy,
                "provider": config.provider,
                "languages": config.languages,
                "dialects": config.dialects,
                "supports_streaming": config.supports_streaming,
                "supports_timestamps": config.supports_timestamps,
                "loaded": model in self.loaded_models,
                "stats": stats
            }
        else:
            # Only return models that have configurations
            return {
                model.value: self.get_model_info(model)
                for model in ASRModel
                if model in self.MODEL_CONFIGS
            }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall service statistics.

        Returns:
            Service statistics
        """
        total_requests = sum(s["total_requests"] for s in self.model_stats.values())
        total_duration = sum(s["total_duration"] for s in self.model_stats.values())
        total_processing = sum(s["total_processing_time"] for s in self.model_stats.values())
        total_errors = sum(s["errors"] for s in self.model_stats.values())

        return {
            "total_requests": total_requests,
            "total_audio_duration": total_duration,
            "total_processing_time": total_processing,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "avg_processing_time": total_processing / total_requests if total_requests > 0 else 0,
            "real_time_factor": total_duration / total_processing if total_processing > 0 else 0,
            "loaded_models": [m.value for m in self.loaded_models.keys()],
            "per_model_stats": {
                model.value: stats
                for model, stats in self.model_stats.items()
                if stats["total_requests"] > 0
            }
        }


# Global service instance
_unified_asr_service: Optional[UnifiedASRService] = None


def get_unified_asr_service(default_model: ASRModel = ASRModel.AKAN_WHISPER) -> UnifiedASRService:
    """
    Get or create the global unified ASR service instance.

    Args:
        default_model: Default ASR model to use

    Returns:
        UnifiedASRService instance
    """
    global _unified_asr_service

    if _unified_asr_service is None:
        _unified_asr_service = UnifiedASRService(default_model)

    return _unified_asr_service