"""
Unified TTS Service - Production-grade abstraction for multiple TTS engines

⚠️ DEPRECATION WARNING ⚠️
This service is deprecated and will be removed in a future release.

Please migrate to the new unified TTS system:
- Use: apps.shared.tts.client.AsyncTTSClient
- Documentation: apps/shared/tts/README.md
- Migration Guide: apps/shared/tts/MIGRATION.md

New features in unified system:
- Automatic billing with WalletService integration
- MongoDB GridFS caching (40% cost reduction)
- Provider health monitoring with email alerts
- Standardized provider IDs (snake_case: f5_tts, style_tts2, etc.)
- TypeScript type generation for frontend
- Comprehensive unit tests (80%+ coverage)

Legacy models supported:
- Akan MMS TTS (native Akan/Twi)
- Meta MMS TTS (multiple African languages)
- Google TTS (fallback)
- F5-TTS (zero-shot)
- Coqui TTS
- XTTS-v2 (voice cloning)
"""

import logging
import time
import base64
import asyncio
import warnings
from typing import Dict, Any, Optional, List, AsyncGenerator
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

# Issue deprecation warning on import
warnings.warn(
    "apps.shared.integration.ai_services.unified_tts_service.UnifiedTTSService is deprecated. "
    "Please use apps.shared.tts.client.AsyncTTSClient instead. "
    "See apps/shared/tts/MIGRATION.md for migration guide.",
    DeprecationWarning,
    stacklevel=2
)


class TTSModel(str, Enum):
    """Available TTS model types"""
    AKAN_MMS = "akan-mms"
    COQUI_TTS = "coqui-tts"
    F5_TTS = "f5-tts"
    XTTS_V2 = "xtts-v2"
    KOKORO_82M = "kokoro-82m"
    META_MMS_TTS = "meta-mms-tts"
    CHATTTS = "chattts"
    GTTS = "gtts"
    MELOTTS = "melotts"
    OPENVOICE = "openvoice"
    STYLETTS2 = "styletts2"
    PARLER_TTS = "parler-tts"
    VOXCPM = "voxcpm"


@dataclass
class TTSResult:
    """Standardized TTS result format"""
    audio_base64: str
    text: str
    voice_id: str
    duration: float
    processing_time: float
    sample_rate: int
    model: str
    format: str = "wav"
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TTSModelConfig:
    """Configuration for a TTS model"""
    model_id: str
    name: str
    quality_score: float  # MOS score out of 5.0
    languages: List[str]
    dialects: List[str]
    provider: str
    supports_cloning: bool = False
    supports_speed_control: bool = True
    supports_pitch_control: bool = False
    supports_streaming: bool = False
    sample_rate: int = 16000


class UnifiedTTSService:
    """
    Unified interface for all TTS models with automatic fallback,
    performance monitoring, and production features.
    """

    # Model configurations
    MODEL_CONFIGS = {
        TTSModel.AKAN_MMS: TTSModelConfig(
            model_id="facebook/mms-tts-aka",
            name="Akan MMS TTS",
            quality_score=4.2,
            languages=["tw"],
            dialects=["asante", "akuapem", "fante"],
            provider="Meta",
            supports_cloning=False,
            supports_speed_control=True,
            sample_rate=16000
        ),
        TTSModel.COQUI_TTS: TTSModelConfig(
            model_id="coqui-tts",
            name="Coqui TTS",
            quality_score=4.2,
            languages=["tw", "en", "fr", "es"],
            dialects=["asante"],
            provider="Coqui",
            supports_cloning=True,
            supports_speed_control=True,
            sample_rate=22050
        ),
        TTSModel.F5_TTS: TTSModelConfig(
            model_id="f5-tts",
            name="F5-TTS (Zero-shot)",
            quality_score=4.5,
            languages=["tw", "en"],
            dialects=["asante", "akuapem"],
            provider="Community",
            supports_cloning=True,
            supports_speed_control=True,
            supports_streaming=True,
            sample_rate=24000
        ),
        TTSModel.XTTS_V2: TTSModelConfig(
            model_id="xtts-twi-v1",
            name="XTTS Twi v1 (Cloning)",
            quality_score=4.5,
            languages=["tw", "en"],
            dialects=["asante", "akuapem", "fante"],
            provider="Coqui (Fine-tuned)",
            supports_cloning=True,
            supports_speed_control=True,
            sample_rate=24000
        ),
        TTSModel.META_MMS_TTS: TTSModelConfig(
            model_id="facebook/mms-tts",
            name="Meta MMS TTS",
            quality_score=4.0,
            languages=["tw", "en", "ewe", "ga"],
            dialects=["asante", "akuapem"],
            provider="Meta",
            supports_cloning=False,
            supports_speed_control=True,
            supports_streaming=True,
            sample_rate=16000
        ),
        TTSModel.GTTS: TTSModelConfig(
            model_id="gtts",
            name="Google TTS (Fallback)",
            quality_score=3.5,
            languages=["en", "fr", "es"],
            dialects=[],
            provider="Google",
            supports_cloning=False,
            supports_speed_control=True,
            sample_rate=24000
        ),
        TTSModel.MELOTTS: TTSModelConfig(
            model_id="melotts",
            name="MeloTTS (Fast Multilingual)",
            quality_score=4.0,
            languages=["en", "es", "fr", "zh", "jp", "kr"],
            dialects=[],
            provider="Local GPU",
            supports_cloning=False,
            supports_speed_control=True,
            supports_streaming=True,
            sample_rate=44100
        ),
        TTSModel.OPENVOICE: TTSModelConfig(
            model_id="openvoice",
            name="OpenVoice (Voice Cloning)",
            quality_score=4.3,
            languages=["en", "zh"],
            dialects=[],
            provider="Local GPU",
            supports_cloning=True,
            supports_speed_control=True,
            supports_streaming=True,
            sample_rate=24000
        ),
        TTSModel.STYLETTS2: TTSModelConfig(
            model_id="styletts2",
            name="StyleTTS2 (Expressive)",
            quality_score=4.7,
            languages=["en", "zh"],
            dialects=[],
            provider="RunPod GPU",
            supports_cloning=True,
            supports_speed_control=False,
            supports_streaming=True,
            sample_rate=24000
        ),
        TTSModel.PARLER_TTS: TTSModelConfig(
            model_id="parler-tts/parler-tts-mini-v1",
            name="Parler-TTS (Streaming, Multilingual)",
            quality_score=4.3,
            languages=["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh", "ja", "hu", "ko"],
            dialects=[],
            provider="HuggingFace (Local GPU)",
            supports_cloning=False,
            supports_speed_control=False,
            supports_pitch_control=False,
            supports_streaming=True,
            sample_rate=44100
        ),
        TTSModel.KOKORO_82M: TTSModelConfig(
            model_id="hexgrad/Kokoro-82M",
            name="Kokoro-82M (Lightweight, Fast)",
            quality_score=4.4,
            languages=["en"],
            dialects=["american", "british"],
            provider="Local Docker",
            supports_cloning=False,
            supports_speed_control=True,
            supports_pitch_control=True,
            supports_streaming=True,
            sample_rate=24000
        ),
        TTSModel.VOXCPM: TTSModelConfig(
            model_id="voxcpm",
            name="VoxCPM (Context-aware, Voice Cloning)",
            quality_score=4.5,
            languages=["en", "zh"],
            dialects=[],
            provider="RunPod GPU (TTS-WebUI)",
            supports_cloning=True,
            supports_speed_control=True,
            supports_pitch_control=False,
            supports_streaming=True,
            sample_rate=24000
        ),
    }

    def __init__(self, default_model: TTSModel = TTSModel.AKAN_MMS):
        """
        Initialize unified TTS service.

        Args:
            default_model: Default TTS model to use
        """
        self.default_model = default_model
        self.loaded_models: Dict[TTSModel, Any] = {}
        self.model_stats: Dict[TTSModel, Dict[str, Any]] = {}

        # Initialize stats for all models
        for model in TTSModel:
            self.model_stats[model] = {
                "total_requests": 0,
                "total_characters": 0,
                "total_processing_time": 0.0,
                "errors": 0,
                "last_used": None
            }

        logger.info(f"Unified TTS Service initialized with default model: {default_model}")

    def _load_model(self, model: TTSModel) -> Any:
        """
        Load a TTS model on-demand.

        Args:
            model: Model to load

        Returns:
            Loaded model instance
        """
        # Check if already loaded
        if model in self.loaded_models:
            return self.loaded_models[model]

        logger.info(f"Loading TTS model: {model}")
        start_time = time.time()

        try:
            if model == TTSModel.AKAN_MMS:
                from .akan_tts_service import get_akan_tts_service
                model_instance = get_akan_tts_service()

            elif model == TTSModel.GTTS:
                # GTTS (Google TTS) - fallback to Akan MMS for now
                logger.warning(f"GTTS model requires simple_tts_service which is not available, using Akan MMS fallback")
                from .akan_tts_service import get_akan_tts_service
                model_instance = get_akan_tts_service()

            elif model == TTSModel.META_MMS_TTS:
                from apps.core_backend.backend.services.meta_mms_service import mms_service
                # MMS service needs to be initialized (async)
                model_instance = mms_service

            elif model == TTSModel.XTTS_V2:
                # XTTS Twi v1 model
                from .xtts_twi_service import get_xtts_twi_service
                model_instance = get_xtts_twi_service()

            elif model == TTSModel.MELOTTS:
                from apps.shared.integration.ai_services import get_melotts_service
                model_instance = get_melotts_service()

            elif model == TTSModel.OPENVOICE:
                from apps.shared.integration.ai_services import get_openvoice_service
                model_instance = get_openvoice_service()
                logger.info("✅ Loaded OpenVoice service (24kHz native)")

            elif model == TTSModel.STYLETTS2:
                from apps.shared.integration.ai_services import get_styletts2_service
                model_instance = get_styletts2_service()
                logger.info("✅ Loaded StyleTTS2 service (24kHz native)")

            elif model == TTSModel.F5_TTS:
                from apps.shared.integration.ai_services import get_f5tts_service
                model_instance = get_f5tts_service()
                logger.info("✅ Loaded F5-TTS service (24kHz native)")

            elif model == TTSModel.PARLER_TTS:
                # Parler-TTS (Streaming TTS from shared integration)
                from apps.shared.integration.ai_services import get_streaming_tts_service
                model_instance = get_streaming_tts_service()
                logger.info("✅ Loaded Parler-TTS streaming service (44.1kHz native)")

            elif model == TTSModel.KOKORO_82M:
                # Kokoro-82M (Lightweight, fast TTS with 11 voices)
                from apps.shared.integration.ai_services import get_kokoro_service
                model_instance = get_kokoro_service()
                logger.info("✅ Loaded Kokoro-82M service (24kHz native)")

            elif model == TTSModel.VOXCPM:
                # VoxCPM (Context-aware TTS with voice cloning via TTS-WebUI)
                from apps.shared.integration.ai_services.voxcpm_service import get_voxcpm_service
                model_instance = get_voxcpm_service()
                logger.info("✅ Loaded VoxCPM service (24kHz native)")

            elif model in [TTSModel.COQUI_TTS]:
                # These require separate service installations
                logger.warning(f"Model {model} requires additional setup, using Akan MMS fallback")
                from .akan_tts_service import get_akan_tts_service
                model_instance = get_akan_tts_service()

            else:
                raise ValueError(f"Unknown model: {model}")

            self.loaded_models[model] = model_instance
            load_time = time.time() - start_time

            logger.info(f"✅ Model {model} loaded in {load_time:.2f}s")
            return model_instance

        except Exception as e:
            logger.error(f"Failed to load model {model}: {e}")
            raise

    def synthesize(
        self,
        text: str,
        model: Optional[TTSModel] = None,
        voice_id: str = "default",
        speed: float = 1.0,
        pitch: float = 0.0,
        language: str = "tw",
        dialect: str = "asante",
        output_format: str = "wav",
        user_id: Optional[str] = None,
        _recursion_depth: int = 0  # Internal: prevent infinite recursion
    ) -> TTSResult:
        """
        Synthesize speech using specified model.

        Args:
            text: Text to synthesize
            model: TTS model to use (defaults to service default)
            voice_id: Voice identifier
            speed: Speech speed (0.5-2.0)
            pitch: Pitch adjustment (-5 to 5)
            language: Language code
            dialect: Dialect
            output_format: Output format (wav, mp3)
            user_id: User ID for tracking

        Returns:
            TTSResult with synthesized audio
        """
        # Prevent infinite recursion in fallback logic
        MAX_RECURSION_DEPTH = 2
        if _recursion_depth > MAX_RECURSION_DEPTH:
            raise RuntimeError(f"Maximum TTS fallback recursion depth ({MAX_RECURSION_DEPTH}) exceeded")

        model = model or self.default_model
        start_time = time.time()

        try:
            # Load model if needed
            model_instance = self._load_model(model)

            logger.info(f"Synthesizing {len(text)} chars with {model}")

            # Route to appropriate model (handle both sync and async contexts)
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context - use asyncio.create_task and block
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._synthesize_with_model(
                            model_instance, model, text, voice_id, speed,
                            pitch, language, dialect, output_format
                        )
                    )
                    result = future.result(timeout=60)
            except RuntimeError:
                # No running loop - safe to use asyncio.run()
                result = asyncio.run(self._synthesize_with_model(
                    model_instance, model, text, voice_id, speed,
                    pitch, language, dialect, output_format
                ))

            processing_time = time.time() - start_time

            # Update stats
            self._update_stats(model, len(text), processing_time, success=True)

            # Create standardized result
            tts_result = TTSResult(
                audio_base64=result["audio_base64"],
                text=text,
                voice_id=voice_id,
                duration=result.get("duration", len(text) * 0.06),
                processing_time=processing_time,
                sample_rate=result.get("sample_rate", 16000),
                model=model.value,
                format=output_format,
                metadata={
                    "speed": speed,
                    "pitch": pitch,
                    "language": language,
                    "dialect": dialect,
                    "user_id": user_id,
                    "quality_score": self.MODEL_CONFIGS[model].quality_score
                }
            )

            logger.info(f"✅ Synthesis complete: {len(text)} chars in {processing_time:.2f}s")
            return tts_result

        except Exception as e:
            processing_time = time.time() - start_time
            self._update_stats(model, len(text), processing_time, success=False)
            logger.error(f"Synthesis failed with {model}: {e}")

            # Language-aware fallback logic
            is_english = language and language.lower() in ['en', 'eng', 'english']
            is_twi = language and language.lower() in ['tw', 'twi', 'akan', 'aka', 'asante', 'akuapem', 'fante']

            # For English: fallback to gTTS
            if is_english and model != TTSModel.GTTS:
                logger.info(f"English detected - attempting fallback to {TTSModel.GTTS}")
                return self.synthesize(
                    text,
                    model=TTSModel.GTTS,
                    voice_id=voice_id,
                    speed=speed,
                    language="en",
                    output_format=output_format,
                    user_id=user_id,
                    _recursion_depth=_recursion_depth + 1
                )

            # For Twi/Akan: fallback to Akan MMS
            if is_twi and model != TTSModel.AKAN_MMS:
                logger.info(f"Twi/Akan detected - attempting fallback to {TTSModel.AKAN_MMS}")
                return self.synthesize(
                    text,
                    model=TTSModel.AKAN_MMS,
                    voice_id=voice_id,
                    speed=speed,
                    pitch=pitch,
                    language=language,
                    dialect=dialect,
                    output_format=output_format,
                    user_id=user_id,
                    _recursion_depth=_recursion_depth + 1
                )

            # Default: try gTTS if not already using it
            if model != TTSModel.GTTS:
                logger.info(f"Attempting final fallback to {TTSModel.GTTS}")
                return self.synthesize(
                    text,
                    model=TTSModel.GTTS,
                    voice_id=voice_id,
                    speed=speed,
                    language="en",  # gTTS default
                    output_format=output_format,
                    user_id=user_id,
                    _recursion_depth=_recursion_depth + 1
                )

            raise

    async def _synthesize_with_model(
        self,
        model_instance: Any,
        model: TTSModel,
        text: str,
        voice_id: str,
        speed: float,
        pitch: float,
        language: str,
        dialect: str,
        output_format: str
    ) -> Dict[str, Any]:
        """
        Synthesize with a specific model instance (async for compatibility with async TTS services).

        Args:
            model_instance: Loaded model instance
            model: Model type
            text: Text to synthesize
            voice_id: Voice ID
            speed: Speed
            pitch: Pitch
            language: Language
            dialect: Dialect
            output_format: Output format

        Returns:
            Raw synthesis result with audio_base64
        """
        if model == TTSModel.AKAN_MMS:
            # Akan TTS Service
            audio_base64 = model_instance.synthesize_to_base64(
                text=text,
                speed=speed
            )
            return {
                "audio_base64": audio_base64,
                "sample_rate": 16000,
                "duration": len(text) * 0.06
            }

        elif model == TTSModel.XTTS_V2:
            # XTTS Twi Service
            # Note: XTTS requires speaker reference audio for voice cloning
            # For now, use default synthesis without reference
            audio_base64 = model_instance.synthesize_to_base64(
                text=text,
                speed=speed,
                language=language
            )

            return {
                "audio_base64": audio_base64,
                "sample_rate": 24000,
                "duration": len(text) * 0.06  # Approximate duration
            }

        elif model == TTSModel.META_MMS_TTS:
            # Meta MMS TTS Service - similar to Akan MMS
            # For now, use the same approach as Akan MMS
            logger.warning(f"Meta MMS TTS not fully implemented, using Akan MMS synthesis")
            audio_base64 = model_instance.synthesize_to_base64(
                text=text,
                speed=speed
            )
            return {
                "audio_base64": audio_base64,
                "sample_rate": 16000,
                "duration": len(text) * 0.06
            }

        elif model == TTSModel.MELOTTS:
            # MeloTTS Service (async) - returns bytes directly
            audio_bytes = await model_instance.synthesize(
                text=text,
                speed=speed,
                language=language
            )

            if audio_bytes:
                # Convert bytes to base64
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                return {
                    "audio_base64": audio_base64,
                    "sample_rate": 44100,
                    "duration": len(text) * 0.06
                }
            else:
                raise Exception("MeloTTS returned no audio")

        elif model == TTSModel.OPENVOICE:
            # OpenVoice Service
            result = model_instance.synthesize(
                text=text,
                voice_id=voice_id,
                speed=speed
            )
            return {
                "audio_base64": result.get("audio_base64"),
                "sample_rate": result.get("sample_rate", 24000),
                "duration": result.get("duration", len(text) * 0.06)
            }

        elif model == TTSModel.STYLETTS2:
            # StyleTTS2 Service
            result = model_instance.synthesize(
                text=text,
                voice_id=voice_id
            )
            return {
                "audio_base64": result.get("audio_base64"),
                "sample_rate": result.get("sample_rate", 24000),
                "duration": result.get("duration", len(text) * 0.06)
            }

        elif model == TTSModel.F5_TTS:
            # F5 TTS Service
            result = model_instance.synthesize(
                text=text,
                voice_id=voice_id,
                speed=speed
            )
            return {
                "audio_base64": result.get("audio_base64"),
                "sample_rate": result.get("sample_rate", 24000),
                "duration": result.get("duration", len(text) * 0.06)
            }

        elif model == TTSModel.COQUI_TTS:
            # Coqui TTS Service
            result = model_instance.synthesize(
                text=text,
                voice_id=voice_id,
                speed=speed,
                language=language
            )
            return {
                "audio_base64": result.get("audio_base64"),
                "sample_rate": result.get("sample_rate", 22050),
                "duration": result.get("duration", len(text) * 0.06)
            }

        elif model == TTSModel.GTTS:
            # Simple TTS Service (gTTS)
            result = model_instance.synthesize(
                text=text,
                voice_id=voice_id,
                speed=speed,
                language=language
            )

            # Convert audio bytes to base64
            audio_base64 = base64.b64encode(result["audio"]).decode('utf-8')

            return {
                "audio_base64": audio_base64,
                "sample_rate": result["sample_rate"],
                "duration": result["duration"]
            }

        elif model == TTSModel.PARLER_TTS:
            # Parler-TTS (Streaming TTS) - collect all chunks for blocking mode
            logger.info("🎵 Using Parler-TTS in blocking mode (collecting streaming chunks)")

            # Collect all streaming chunks
            audio_chunks = []
            async for chunk in model_instance.stream_tts(
                text=text,
                voice_description=voice_id,  # voice_id acts as voice_description for Parler
                sample_rate=44100
            ):
                audio_chunks.append(chunk)

            if not audio_chunks:
                raise Exception("Parler-TTS returned no audio chunks")

            # Concatenate all chunks
            complete_audio = np.concatenate(audio_chunks)

            # Convert to WAV with correct 44.1kHz sample rate
            import io
            import wave
            wav_io = io.BytesIO()
            pcm_int16 = (complete_audio * 32767).astype(np.int16)

            with wave.open(wav_io, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(44100)  # Parler native rate!
                wav_file.writeframes(pcm_int16.tobytes())

            wav_io.seek(0)
            wav_bytes = wav_io.read()
            audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')

            duration = len(complete_audio) / 44100

            return {
                "audio_base64": audio_base64,
                "sample_rate": 44100,
                "duration": duration
            }

        else:
            raise ValueError(f"Model {model} synthesis not implemented")

    async def stream_synthesize(
        self,
        text: str,
        model: Optional[TTSModel] = None,
        voice_description: str = "A clear, neutral voice",
        language: str = "en",
        **kwargs
    ) -> 'AsyncGenerator[np.ndarray, None]':
        """
        Stream synthesis for streaming-capable models.

        Yields audio chunks as they're generated for real-time playback.
        Only works with models that have supports_streaming=True.

        Args:
            text: Text to synthesize
            model: TTS model to use (must support streaming)
            voice_description: Voice description (for Parler/description-based models)
            language: Language code
            **kwargs: Additional model-specific parameters

        Yields:
            np.ndarray: Audio chunks as numpy arrays (float32, [-1, 1] range)

        Raises:
            ValueError: If model doesn't support streaming
        """
        model = model or self.default_model

        # Check if model supports streaming
        if not self.MODEL_CONFIGS[model].supports_streaming:
            raise ValueError(
                f"Model {model} does not support streaming. "
                f"Streaming-capable models: {[m.value for m in TTSModel if self.MODEL_CONFIGS[m].supports_streaming]}"
            )

        # Load model
        model_instance = self._load_model(model)

        logger.info(f"🎵 Starting streaming synthesis with {model}: {len(text)} chars")

        if model == TTSModel.PARLER_TTS:
            # Parler-TTS streaming (already implemented)
            async for audio_chunk in model_instance.stream_tts(
                text=text,
                voice_description=voice_description,
                sample_rate=44100  # Parler native rate
            ):
                yield audio_chunk

        elif model == TTSModel.MELOTTS:
            # MeloTTS streaming
            language_code = kwargs.get('language_code', language.upper())
            speaker_id = kwargs.get('speaker_id', 0)
            speed = kwargs.get('speed', 1.0)

            # MeloTTS returns WAV bytes, need to convert to numpy for consistency
            import io
            import wave

            async for wav_chunk in model_instance.stream_synthesize(
                text=text,
                language=language_code,
                speaker_id=speaker_id,
                speed=speed
            ):
                # Convert WAV bytes to numpy array for consistency with Parler
                # Note: This is for interface consistency - callers expecting np.ndarray
                # For direct streaming to clients, the raw bytes are fine
                try:
                    wav_io = io.BytesIO(wav_chunk)
                    with wave.open(wav_io, 'rb') as wav_file:
                        audio_data = wav_file.readframes(wav_file.getnframes())
                        # Convert to numpy float32 [-1, 1] range
                        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                        yield audio_np
                except Exception as e:
                    # If not a WAV file, assume raw PCM and yield as-is
                    logger.warning(f"Could not parse WAV chunk, yielding raw bytes: {e}")
                    # Convert raw bytes to numpy
                    audio_np = np.frombuffer(wav_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                    yield audio_np

        elif model == TTSModel.F5_TTS:
            # F5-TTS streaming
            language_code = kwargs.get('language_code', language.lower())
            speed = kwargs.get('speed', 1.0)
            remove_silence = kwargs.get('remove_silence', True)

            # F5-TTS returns WAV bytes, need to convert to numpy for consistency
            import io
            import wave

            async for wav_chunk in model_instance.stream_synthesize(
                text=text,
                language=language_code,
                speed=speed,
                remove_silence=remove_silence
            ):
                # Convert WAV bytes to numpy array for consistency
                try:
                    wav_io = io.BytesIO(wav_chunk)
                    with wave.open(wav_io, 'rb') as wav_file:
                        audio_data = wav_file.readframes(wav_file.getnframes())
                        # Convert to numpy float32 [-1, 1] range
                        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                        yield audio_np
                except Exception as e:
                    # If not a WAV file, assume raw PCM and yield as-is
                    logger.warning(f"Could not parse WAV chunk, yielding raw bytes: {e}")
                    # Convert raw bytes to numpy
                    audio_np = np.frombuffer(wav_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                    yield audio_np

        elif model == TTSModel.OPENVOICE:
            # OpenVoice streaming
            language_code = kwargs.get('language_code', language.upper())
            speed = kwargs.get('speed', 1.0)

            # OpenVoice returns WAV bytes, need to convert to numpy for consistency
            import io
            import wave

            async for wav_chunk in model_instance.stream_synthesize(
                text=text,
                language=language_code,
                speed=speed
            ):
                # Convert WAV bytes to numpy array for consistency
                try:
                    wav_io = io.BytesIO(wav_chunk)
                    with wave.open(wav_io, 'rb') as wav_file:
                        audio_data = wav_file.readframes(wav_file.getnframes())
                        # Convert to numpy float32 [-1, 1] range
                        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                        yield audio_np
                except Exception as e:
                    # If not a WAV file, assume raw PCM and yield as-is
                    logger.warning(f"Could not parse WAV chunk, yielding raw bytes: {e}")
                    # Convert raw bytes to numpy
                    audio_np = np.frombuffer(wav_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                    yield audio_np

        elif model == TTSModel.STYLETTS2:
            # StyleTTS2 streaming
            alpha = kwargs.get('alpha', 0.3)
            beta = kwargs.get('beta', 0.7)
            diffusion_steps = kwargs.get('diffusion_steps', 5)
            embedding_scale = kwargs.get('embedding_scale', 1.0)

            # StyleTTS2 returns WAV bytes, need to convert to numpy for consistency
            import io
            import wave

            async for wav_chunk in model_instance.stream_synthesize(
                text=text,
                alpha=alpha,
                beta=beta,
                diffusion_steps=diffusion_steps,
                embedding_scale=embedding_scale
            ):
                # Convert WAV bytes to numpy array for consistency
                try:
                    wav_io = io.BytesIO(wav_chunk)
                    with wave.open(wav_io, 'rb') as wav_file:
                        audio_data = wav_file.readframes(wav_file.getnframes())
                        # Convert to numpy float32 [-1, 1] range
                        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                        yield audio_np
                except Exception as e:
                    # If not a WAV file, assume raw PCM and yield as-is
                    logger.warning(f"Could not parse WAV chunk, yielding raw bytes: {e}")
                    # Convert raw bytes to numpy
                    audio_np = np.frombuffer(wav_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                    yield audio_np

        elif model == TTSModel.KOKORO_82M:
            # Kokoro-82M streaming - lightweight, fast synthesis
            voice = kwargs.get('voice', 'af_heart')
            speed = kwargs.get('speed', 1.0)
            pitch = kwargs.get('pitch', 1.0)

            logger.info(f"[KOKORO STREAM] Streaming with voice={voice}, speed={speed}, pitch={pitch}")

            # Kokoro streams raw WAV data - first chunk has header, rest is raw PCM
            import io
            import wave

            first_chunk = True
            wav_header_size = 44  # Standard WAV header is 44 bytes

            async for wav_chunk in model_instance.stream_synthesize(
                text=text,
                voice=voice,
                speed=speed,
                pitch=pitch
            ):
                # Convert WAV bytes to numpy array for consistency
                if first_chunk:
                    # First chunk may have WAV header, try to parse it
                    try:
                        wav_io = io.BytesIO(wav_chunk)
                        with wave.open(wav_io, 'rb') as wav_file:
                            audio_data = wav_file.readframes(wav_file.getnframes())
                            # Convert to numpy float32 [-1, 1] range
                            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                            first_chunk = False
                            yield audio_np
                            continue
                    except Exception as e:
                        logger.debug(f"First chunk not a complete WAV, treating as raw PCM: {e}")
                        first_chunk = False

                # Subsequent chunks or failed first chunk - raw PCM data
                # Ensure buffer is aligned to int16 boundaries (2 bytes)
                if len(wav_chunk) % 2 != 0:
                    logger.warning(f"Chunk size {len(wav_chunk)} not aligned to int16, truncating")
                    wav_chunk = wav_chunk[:len(wav_chunk) - 1]

                # Convert raw bytes to numpy
                if len(wav_chunk) > 0:
                    audio_np = np.frombuffer(wav_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                    yield audio_np

        elif model == TTSModel.VOXCPM:
            # VoxCPM streaming - context-aware TTS with voice cloning
            language_code = kwargs.get('language_code', language.lower())
            speaker = kwargs.get('speaker', None)
            speed = kwargs.get('speed', 1.0)

            logger.info(f"[VOXCPM STREAM] Streaming with language={language_code}, speaker={speaker}, speed={speed}")

            # VoxCPM streams raw WAV data similar to Kokoro
            import io
            import wave

            first_chunk = True

            async for wav_chunk in model_instance.stream_synthesize(
                text=text,
                language=language_code,
                speaker=speaker,
                speed=speed
            ):
                # Convert WAV bytes to numpy array for consistency
                if first_chunk:
                    # First chunk may have WAV header, try to parse it
                    try:
                        wav_io = io.BytesIO(wav_chunk)
                        with wave.open(wav_io, 'rb') as wav_file:
                            audio_data = wav_file.readframes(wav_file.getnframes())
                            # Convert to numpy float32 [-1, 1] range
                            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                            first_chunk = False
                            yield audio_np
                            continue
                    except Exception as e:
                        logger.debug(f"First chunk not a complete WAV, treating as raw PCM: {e}")
                        first_chunk = False

                # Subsequent chunks or failed first chunk - raw PCM data
                # Ensure buffer is aligned to int16 boundaries (2 bytes)
                if len(wav_chunk) % 2 != 0:
                    logger.warning(f"Chunk size {len(wav_chunk)} not aligned to int16, truncating")
                    wav_chunk = wav_chunk[:len(wav_chunk) - 1]

                # Convert raw bytes to numpy
                if len(wav_chunk) > 0:
                    audio_np = np.frombuffer(wav_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                    yield audio_np

        elif model == TTSModel.META_MMS_TTS:
            # Meta MMS TTS streaming
            language_code = kwargs.get('language_code', language.lower())
            voice_id = kwargs.get('voice_id', None)

            logger.info(f"[META MMS STREAM] Streaming with language={language_code}")

            # Meta MMS returns WAV bytes, need to convert to numpy for consistency
            import io
            import wave

            async for wav_chunk in model_instance.stream_synthesize(
                text=text,
                language=language_code,
                voice_id=voice_id
            ):
                # Convert WAV bytes to numpy array for consistency
                try:
                    wav_io = io.BytesIO(wav_chunk)
                    with wave.open(wav_io, 'rb') as wav_file:
                        audio_data = wav_file.readframes(wav_file.getnframes())
                        # Convert to numpy float32 [-1, 1] range
                        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                        yield audio_np
                except Exception as e:
                    # If not a WAV file, assume raw PCM and yield as-is
                    logger.warning(f"Could not parse WAV chunk, yielding raw bytes: {e}")
                    # Convert raw bytes to numpy
                    audio_np = np.frombuffer(wav_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                    yield audio_np

        else:
            # For future streaming models, implement here
            # Example pattern for other models:
            # async for chunk in model_instance.stream_synthesize(...):
            #     yield chunk
            raise NotImplementedError(f"Streaming not yet implemented for {model}")

    def get_model_sample_rate(self, model: TTSModel) -> int:
        """
        Get the native sample rate for a TTS model.

        Args:
            model: TTS model

        Returns:
            Sample rate in Hz (e.g., 16000, 44100)
        """
        return self.MODEL_CONFIGS[model].sample_rate

    def supports_streaming(self, model: TTSModel) -> bool:
        """
        Check if a model supports streaming synthesis.

        Args:
            model: TTS model to check

        Returns:
            True if model supports streaming
        """
        return self.MODEL_CONFIGS[model].supports_streaming

    def get_available_voices(self, model: Optional[TTSModel] = None) -> List[Dict[str, Any]]:
        """
        Get available voices for a model.

        Args:
            model: Model to get voices for (None for all)

        Returns:
            List of available voices
        """
        voices = []

        if model == TTSModel.AKAN_MMS or model is None:
            voices.extend([
                {
                    "voice_id": "asante_male_1",
                    "name": "Kofi (Asante)",
                    "language": "tw",
                    "dialect": "asante",
                    "gender": "male",
                    "model": TTSModel.AKAN_MMS.value
                },
                {
                    "voice_id": "asante_female_1",
                    "name": "Ama (Asante)",
                    "language": "tw",
                    "dialect": "asante",
                    "gender": "female",
                    "model": TTSModel.AKAN_MMS.value
                }
            ])

        if model == TTSModel.XTTS_V2 or model is None:
            voices.extend([
                {
                    "voice_id": "xtts_twi_default",
                    "name": "XTTS Twi (Cloneable)",
                    "language": "tw",
                    "dialect": "asante",
                    "gender": "neutral",
                    "model": TTSModel.XTTS_V2.value,
                    "supports_cloning": True
                }
            ])

        if model == TTSModel.GTTS or model is None:
            voices.append({
                "voice_id": "gtts_default",
                "name": "Google TTS (English)",
                "language": "en",
                "dialect": "standard",
                "gender": "neutral",
                "model": TTSModel.GTTS.value
            })

        return voices

    def _update_stats(self, model: TTSModel, char_count: int, processing_time: float, success: bool):
        """
        Update model statistics.

        Args:
            model: Model used
            char_count: Number of characters synthesized
            processing_time: Processing time
            success: Whether synthesis succeeded
        """
        stats = self.model_stats[model]
        stats["total_requests"] += 1
        stats["total_characters"] += char_count
        stats["total_processing_time"] += processing_time
        if not success:
            stats["errors"] += 1
        stats["last_used"] = datetime.now().isoformat()

    def get_model_info(self, model: Optional[TTSModel] = None) -> Dict[str, Any]:
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
                "quality_score": config.quality_score,
                "provider": config.provider,
                "languages": config.languages,
                "dialects": config.dialects,
                "supports_cloning": config.supports_cloning,
                "supports_speed_control": config.supports_speed_control,
                "supports_pitch_control": config.supports_pitch_control,
                "sample_rate": config.sample_rate,
                "loaded": model in self.loaded_models,
                "stats": stats
            }
        else:
            # Only return models that have configurations
            return {
                model.value: self.get_model_info(model)
                for model in TTSModel
                if model in self.MODEL_CONFIGS
            }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall service statistics.

        Returns:
            Service statistics
        """
        total_requests = sum(s["total_requests"] for s in self.model_stats.values())
        total_chars = sum(s["total_characters"] for s in self.model_stats.values())
        total_processing = sum(s["total_processing_time"] for s in self.model_stats.values())
        total_errors = sum(s["errors"] for s in self.model_stats.values())

        return {
            "total_requests": total_requests,
            "total_characters": total_chars,
            "total_processing_time": total_processing,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "avg_processing_time": total_processing / total_requests if total_requests > 0 else 0,
            "chars_per_second": total_chars / total_processing if total_processing > 0 else 0,
            "loaded_models": [m.value for m in self.loaded_models.keys()],
            "per_model_stats": {
                model.value: stats
                for model, stats in self.model_stats.items()
                if stats["total_requests"] > 0
            }
        }


# Global service instance
_unified_tts_service: Optional[UnifiedTTSService] = None


def get_unified_tts_service(default_model: TTSModel = TTSModel.AKAN_MMS) -> UnifiedTTSService:
    """
    Get or create the global unified TTS service instance.

    Args:
        default_model: Default TTS model to use

    Returns:
        UnifiedTTSService instance
    """
    global _unified_tts_service

    if _unified_tts_service is None:
        _unified_tts_service = UnifiedTTSService(default_model)

    return _unified_tts_service