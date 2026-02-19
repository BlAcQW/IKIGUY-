"""
Real-time Speech Processing

This module provides real-time speech processing capabilities including:
- ASR streaming with barge-in support
- TTS with natural voice synthesis
- Voice activity detection
- Emotion detection and sentiment analysis
"""

import asyncio
import logging
import time
import datetime
from typing import Dict, List, Optional, Any, Callable, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import json
import numpy as np
from collections import deque

# For audio processing
try:
    import librosa
    import soundfile as sf

    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logging.warning(
        "Audio processing libraries not available. Install librosa and soundfile for full functionality."
    )

# For AI/ML features
try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    import torch

    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logging.warning(
        "AI libraries not available. Install transformers and torch for emotion detection."
    )

# For metrics
try:
    from prometheus_client import Histogram, start_http_server

    METRICS_AVAILABLE = True
    VAD_DETECTION_ACCURACY = Histogram(
        "vad_detection_accuracy", "Voice activity detection confidence"
    )
except ImportError:
    METRICS_AVAILABLE = False
    VAD_DETECTION_ACCURACY = None
    logging.warning(
        "Prometheus client not available. Install prometheus_client for metrics."
    )


def start_metrics_server(port: int = 8000) -> None:
    """Start Prometheus metrics exporter."""
    if METRICS_AVAILABLE:
        start_http_server(port)


class SpeechEventType(Enum):
    """Speech event types"""

    SPEECH_START = "speech_start"
    SPEECH_END = "speech_end"
    SILENCE_START = "silence_start"
    SILENCE_END = "silence_end"
    EMOTION_DETECTED = "emotion_detected"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    BARGE_IN_DETECTED = "barge_in_detected"
    ASR_RESULT = "asr_result"
    TTS_START = "tts_start"
    TTS_END = "tts_end"


class EmotionType(Enum):
    """Emotion types"""

    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    NEUTRAL = "neutral"
    EXCITED = "excited"
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    SURPRISED = "surprised"


class SentimentType(Enum):
    """Sentiment types"""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class SpeechEvent:
    """Speech processing event"""

    event_type: SpeechEventType
    timestamp: datetime.datetime
    call_id: str
    data: Dict[str, Any]
    confidence: float = 0.0


@dataclass
class VoiceActivityResult:
    """Voice activity detection result"""

    is_speech: bool
    confidence: float
    energy_level: float
    duration_ms: float
    timestamp: datetime.datetime


@dataclass
class EmotionResult:
    """Emotion detection result"""

    emotion: EmotionType
    confidence: float
    intensity: float
    timestamp: datetime.datetime
    features: Dict[str, float]


@dataclass
class SentimentResult:
    """Sentiment analysis result"""

    sentiment: SentimentType
    confidence: float
    score: float  # -1.0 to 1.0
    timestamp: datetime.datetime
    keywords: List[str]


@dataclass
class ASRResult:
    """ASR (Automatic Speech Recognition) result"""

    text: str
    confidence: float
    is_final: bool
    timestamp: datetime.datetime
    start_time: float
    end_time: float
    alternatives: List[str] = None


@dataclass
class TTSRequest:
    """TTS (Text-to-Speech) request"""

    text: str
    voice_id: str
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    language: str = "en-US"
    emotion: Optional[EmotionType] = None


@dataclass
class TTSResult:
    """TTS (Text-to-Speech) result"""

    audio_data: bytes
    duration_ms: float
    timestamp: datetime.datetime
    voice_id: str
    text: str


class RealTimeSpeechProcessor:
    """Real-time speech processing with AI capabilities"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        # Configuration
        self.vad_threshold = config.get("vad_threshold", 0.5)
        self.vad_frame_duration = config.get("vad_frame_duration", 30)  # ms
        self.silence_threshold = config.get("silence_threshold", 0.3)
        self.min_speech_duration = config.get("min_speech_duration", 100)  # ms
        self.barge_in_threshold = config.get("barge_in_threshold", 0.7)

        # State
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        self.event_callbacks: Dict[str, List[Callable]] = {}
        self.asr_models: Dict[str, Any] = {}
        self.tts_engines: Dict[str, Any] = {}
        self.emotion_models: Dict[str, Any] = {}
        self.sentiment_models: Dict[str, Any] = {}

        # Initialize AI models if available
        if AI_AVAILABLE:
            self._initialize_ai_models()

        # Audio processing
        self.sample_rate = config.get("sample_rate", 16000)
        self.chunk_size = config.get("chunk_size", 1024)

    def _initialize_ai_models(self):
        """Initialize AI models for speech processing"""
        try:
            # Initialize emotion detection model
            if "emotion_model" in self.config:
                self.emotion_models["default"] = pipeline(
                    "text-classification",
                    model=self.config["emotion_model"],
                    device=0 if torch.cuda.is_available() else -1,
                )

            # Initialize sentiment analysis model
            if "sentiment_model" in self.config:
                self.sentiment_models["default"] = pipeline(
                    "sentiment-analysis",
                    model=self.config["sentiment_model"],
                    device=0 if torch.cuda.is_available() else -1,
                )

            self.logger.info("AI models initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize AI models: {e}")

    async def start_call_processing(
        self, call_id: str, config: Dict[str, Any] = None
    ) -> bool:
        """
        Start real-time speech processing for a call

        Args:
            call_id: Unique call identifier
            config: Call-specific configuration

        Returns:
            bool: True if processing started successfully
        """
        try:
            call_config = config or {}

            # Initialize call state
            self.active_calls[call_id] = {
                "config": call_config,
                "vad_state": {
                    "is_speaking": False,
                    "speech_start_time": None,
                    "silence_start_time": None,
                    "last_energy": 0.0,
                    "energy_buffer": deque(maxlen=10),
                },
                "asr_state": {
                    "is_listening": False,
                    "partial_results": [],
                    "final_results": [],
                },
                "tts_state": {"is_speaking": False, "current_text": None, "queue": []},
                "emotion_state": {
                    "current_emotion": None,
                    "emotion_history": deque(maxlen=50),
                },
                "sentiment_state": {
                    "current_sentiment": None,
                    "sentiment_history": deque(maxlen=50),
                },
                "barge_in_state": {"detected": False, "last_detection": None},
                "start_time": datetime.datetime.now(datetime.UTC),
            }

            self.logger.info(f"Started speech processing for call {call_id}")
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to start speech processing for call {call_id}: {e}"
            )
            return False

    async def stop_call_processing(self, call_id: str) -> bool:
        """
        Stop real-time speech processing for a call

        Args:
            call_id: Unique call identifier

        Returns:
            bool: True if processing stopped successfully
        """
        try:
            if call_id in self.active_calls:
                del self.active_calls[call_id]
                self.logger.info(f"Stopped speech processing for call {call_id}")
                return True
            return False

        except Exception as e:
            self.logger.error(
                f"Failed to stop speech processing for call {call_id}: {e}"
            )
            return False

    async def process_audio_chunk(
        self, call_id: str, audio_chunk: bytes
    ) -> List[SpeechEvent]:
        """
        Process an audio chunk for real-time speech analysis

        Args:
            call_id: Unique call identifier
            audio_chunk: Raw audio data

        Returns:
            List[SpeechEvent]: List of speech events detected
        """
        try:
            if call_id not in self.active_calls:
                return []

            events = []
            call_state = self.active_calls[call_id]

            # Convert audio to numpy array
            if AUDIO_AVAILABLE:
                audio_array = np.frombuffer(audio_chunk, dtype=np.float32)

                # Voice Activity Detection
                vad_result = await self._detect_voice_activity(audio_array, call_state)
                if vad_result:
                    events.extend(
                        await self._process_vad_result(call_id, vad_result, call_state)
                    )

                # Emotion detection (if AI available)
                if AI_AVAILABLE and vad_result and vad_result.is_speech:
                    emotion_result = await self._detect_emotion(audio_array, call_state)
                    if emotion_result:
                        events.append(
                            self._create_speech_event(
                                SpeechEventType.EMOTION_DETECTED,
                                call_id,
                                {
                                    "emotion": emotion_result.emotion.value,
                                    "confidence": emotion_result.confidence,
                                    "intensity": emotion_result.intensity,
                                    "features": emotion_result.features,
                                },
                                emotion_result.confidence,
                            )
                        )

                # Barge-in detection
                if (
                    call_state["tts_state"]["is_speaking"]
                    and vad_result
                    and vad_result.is_speech
                ):
                    barge_in_detected = await self._detect_barge_in(
                        audio_array, call_state
                    )
                    if barge_in_detected:
                        events.append(
                            self._create_speech_event(
                                SpeechEventType.BARGE_IN_DETECTED,
                                call_id,
                                {
                                    "confidence": vad_result.confidence,
                                    "energy_level": vad_result.energy_level,
                                },
                                vad_result.confidence,
                            )
                        )

            return events

        except Exception as e:
            self.logger.error(f"Failed to process audio chunk for call {call_id}: {e}")
            return []

    async def _detect_voice_activity(
        self, audio_array: np.ndarray, call_state: Dict[str, Any]
    ) -> Optional[VoiceActivityResult]:
        """Detect voice activity in audio chunk"""
        try:
            # Calculate energy level
            energy = np.mean(np.square(audio_array))
            call_state["vad_state"]["energy_buffer"].append(energy)

            # Calculate average energy over buffer
            avg_energy = np.mean(list(call_state["vad_state"]["energy_buffer"]))

            # Determine if speech is present
            is_speech = bool(avg_energy > self.vad_threshold)
            confidence = float(
                min(avg_energy / self.vad_threshold, 1.0)
                if is_speech
                else 1.0 - (avg_energy / self.vad_threshold)
            )

            if VAD_DETECTION_ACCURACY is not None:
                VAD_DETECTION_ACCURACY.observe(confidence)

            return VoiceActivityResult(
                is_speech=is_speech,
                confidence=confidence,
                energy_level=avg_energy,
                duration_ms=len(audio_array) / self.sample_rate * 1000,
                timestamp=datetime.datetime.now(datetime.UTC),
            )

        except Exception as e:
            self.logger.error(f"Failed to detect voice activity: {e}")
            return None

    async def _process_vad_result(
        self, call_id: str, vad_result: VoiceActivityResult, call_state: Dict[str, Any]
    ) -> List[SpeechEvent]:
        """Process voice activity detection result and generate events"""
        events = []
        vad_state = call_state["vad_state"]

        if vad_result.is_speech and not vad_state["is_speaking"]:
            # Speech started
            vad_state["is_speaking"] = True
            vad_state["speech_start_time"] = vad_result.timestamp

            events.append(
                self._create_speech_event(
                    SpeechEventType.SPEECH_START,
                    call_id,
                    {
                        "confidence": vad_result.confidence,
                        "energy_level": vad_result.energy_level,
                    },
                    vad_result.confidence,
                )
            )

        elif not vad_result.is_speech and vad_state["is_speaking"]:
            # Speech ended
            vad_state["is_speaking"] = False
            vad_state["silence_start_time"] = vad_result.timestamp

            # Check if speech duration meets threshold
            if vad_state["speech_start_time"]:
                speech_duration = (
                    vad_result.timestamp - vad_state["speech_start_time"]
                ).total_seconds() * 1000
                if speech_duration >= self.min_speech_duration:
                    events.append(
                        self._create_speech_event(
                            SpeechEventType.SPEECH_END,
                            call_id,
                            {
                                "duration_ms": speech_duration,
                                "confidence": vad_result.confidence,
                            },
                            vad_result.confidence,
                        )
                    )
                else:
                    # Speech was too short, don't generate event
                    pass

        return events

    async def _detect_emotion(
        self, audio_array: np.ndarray, call_state: Dict[str, Any]
    ) -> Optional[EmotionResult]:
        """Detect emotion in audio"""
        try:
            # Always return a result, even without AI models (simplified implementation)

            # Extract audio features (simplified - in real implementation, use proper feature extraction)
            features = {
                "energy": np.mean(np.square(audio_array)),
                "zero_crossing_rate": np.mean(np.diff(np.sign(audio_array))),
                "spectral_centroid": np.mean(np.abs(audio_array)),
                "mfcc_1": np.mean(audio_array),
                "mfcc_2": np.std(audio_array),
            }

            # Use emotion model (simplified - in real implementation, use proper emotion detection)
            # For now, we'll use a simple rule-based approach
            energy = features["energy"]

            if energy > 0.8:
                emotion = EmotionType.EXCITED
                confidence = 0.8
            elif energy > 0.6:
                emotion = EmotionType.HAPPY
                confidence = 0.7
            elif energy > 0.4:
                emotion = EmotionType.NEUTRAL
                confidence = 0.6
            elif energy > 0.2:
                emotion = EmotionType.SAD
                confidence = 0.7
            else:
                emotion = EmotionType.CONFUSED
                confidence = 0.6

            # Update emotion state
            call_state["emotion_state"]["current_emotion"] = emotion
            call_state["emotion_state"]["emotion_history"].append(
                {
                    "emotion": emotion,
                    "timestamp": datetime.datetime.now(datetime.UTC),
                    "confidence": confidence,
                }
            )

            return EmotionResult(
                emotion=emotion,
                confidence=confidence,
                intensity=energy,
                timestamp=datetime.datetime.now(datetime.UTC),
                features=features,
            )

        except Exception as e:
            self.logger.error(f"Failed to detect emotion: {e}")
            return None

    async def _detect_barge_in(
        self, audio_array: np.ndarray, call_state: Dict[str, Any]
    ) -> bool:
        """Detect barge-in (interruption during TTS)"""
        try:
            energy = np.mean(np.square(audio_array))

            # Check if energy level is high enough to indicate barge-in
            if energy > self.barge_in_threshold:
                call_state["barge_in_state"]["detected"] = True
                call_state["barge_in_state"]["last_detection"] = datetime.datetime.now(datetime.UTC)
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to detect barge-in: {e}")
            return False

    async def process_asr_stream(
        self, call_id: str, audio_stream: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[ASRResult, None]:
        """
        Process ASR streaming with barge-in support

        Args:
            call_id: Unique call identifier
            audio_stream: Async generator of audio chunks

        Yields:
            ASRResult: ASR results as they become available
        """
        try:
            if call_id not in self.active_calls:
                return

            call_state = self.active_calls[call_id]
            asr_state = call_state["asr_state"]

            # Initialize ASR (simplified - in real implementation, use actual ASR service)
            asr_state["is_listening"] = True

            async for audio_chunk in audio_stream:
                # Check for barge-in
                if call_state["barge_in_state"]["detected"]:
                    # Stop TTS if it's playing
                    if call_state["tts_state"]["is_speaking"]:
                        await self._stop_tts(call_id)

                    # Process ASR
                    asr_result = await self._process_asr_chunk(audio_chunk, call_state)
                    if asr_result:
                        yield asr_result

                # Normal ASR processing
                else:
                    asr_result = await self._process_asr_chunk(audio_chunk, call_state)
                    if asr_result:
                        yield asr_result

                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)

            asr_state["is_listening"] = False

        except Exception as e:
            self.logger.error(f"Failed to process ASR stream for call {call_id}: {e}")

    async def _process_asr_chunk(
        self, audio_chunk: bytes, call_state: Dict[str, Any]
    ) -> Optional[ASRResult]:
        """Process ASR chunk (simplified implementation)"""
        try:
            # In a real implementation, this would send audio to an ASR service
            # For now, we'll simulate ASR processing

            # Simulate ASR result
            text = "Hello, this is a simulated ASR result"
            confidence = 0.85
            is_final = True

            result = ASRResult(
                text=text,
                confidence=confidence,
                is_final=is_final,
                timestamp=datetime.datetime.now(datetime.UTC),
                start_time=time.time(),
                end_time=time.time() + 0.1,
                alternatives=["Hello", "Hi there"],
            )

            # Store result
            call_state["asr_state"]["final_results"].append(result)

            return result

        except Exception as e:
            self.logger.error(f"Failed to process ASR chunk: {e}")
            return None

    async def synthesize_speech(
        self, call_id: str, tts_request: TTSRequest
    ) -> Optional[TTSResult]:
        """
        Synthesize speech using TTS

        Args:
            call_id: Unique call identifier
            tts_request: TTS request parameters

        Returns:
            TTSResult: Synthesized audio result
        """
        try:
            if call_id not in self.active_calls:
                return None

            call_state = self.active_calls[call_id]
            tts_state = call_state["tts_state"]

            # Check if TTS is already speaking
            if tts_state["is_speaking"]:
                # Add to queue
                tts_state["queue"].append(tts_request)
                return None

            # Start TTS synthesis
            tts_state["is_speaking"] = True
            tts_state["current_text"] = tts_request.text

            # Emit TTS start event
            await self._emit_event(
                call_id,
                self._create_speech_event(
                    SpeechEventType.TTS_START,
                    call_id,
                    {
                        "text": tts_request.text,
                        "voice_id": tts_request.voice_id,
                        "speed": tts_request.speed,
                        "pitch": tts_request.pitch,
                    },
                    1.0,
                ),
            )

            # Synthesize speech (simplified - in real implementation, use actual TTS service)
            audio_data = await self._synthesize_audio(tts_request)

            # Calculate duration (simplified)
            duration_ms = len(tts_request.text.split()) * 200  # Rough estimate

            result = TTSResult(
                audio_data=audio_data,
                duration_ms=duration_ms,
                timestamp=datetime.datetime.now(datetime.UTC),
                voice_id=tts_request.voice_id,
                text=tts_request.text,
            )

            # Emit TTS end event
            await self._emit_event(
                call_id,
                self._create_speech_event(
                    SpeechEventType.TTS_END,
                    call_id,
                    {"duration_ms": duration_ms, "voice_id": tts_request.voice_id},
                    1.0,
                ),
            )

            # Update state
            tts_state["is_speaking"] = False
            tts_state["current_text"] = None

            # Process queue
            if tts_state["queue"]:
                next_request = tts_state["queue"].pop(0)
                await self.synthesize_speech(call_id, next_request)

            return result

        except Exception as e:
            self.logger.error(f"Failed to synthesize speech for call {call_id}: {e}")
            return None

    async def _synthesize_audio(self, tts_request: TTSRequest) -> bytes:
        """Synthesize audio from text (simplified implementation)"""
        try:
            # In a real implementation, this would use an actual TTS service
            # For now, we'll return dummy audio data

            # Simulate audio synthesis
            sample_rate = 16000
            duration = len(tts_request.text.split()) * 0.2  # 0.2 seconds per word
            samples = int(sample_rate * duration)

            # Generate dummy audio (sine wave)
            frequency = 440  # A4 note
            t = np.linspace(0, duration, samples, False)
            audio = np.sin(2 * np.pi * frequency * t) * 0.3

            # Apply speed and pitch modifications
            if tts_request.speed != 1.0:
                audio = librosa.effects.time_stretch(audio, rate=tts_request.speed)

            # Convert to bytes
            audio_bytes = (audio * 32767).astype(np.int16).tobytes()

            return audio_bytes

        except Exception as e:
            self.logger.error(f"Failed to synthesize audio: {e}")
            return b""

    async def _stop_tts(self, call_id: str) -> bool:
        """Stop current TTS playback"""
        try:
            if call_id in self.active_calls:
                call_state = self.active_calls[call_id]
                call_state["tts_state"]["is_speaking"] = False
                call_state["tts_state"]["current_text"] = None
                call_state["tts_state"]["queue"].clear()
                return True
            return False

        except Exception as e:
            self.logger.error(f"Failed to stop TTS for call {call_id}: {e}")
            return False

    async def analyze_sentiment(
        self, call_id: str, text: str
    ) -> Optional[SentimentResult]:
        """
        Analyze sentiment of text

        Args:
            call_id: Unique call identifier
            text: Text to analyze

        Returns:
            SentimentResult: Sentiment analysis result
        """
        try:
            # Always return a result, even without AI models (simplified implementation)

            # Use sentiment model (simplified - in real implementation, use actual sentiment analysis)
            # For now, we'll use a simple rule-based approach
            positive_words = [
                "good",
                "great",
                "excellent",
                "happy",
                "love",
                "like",
                "wonderful",
            ]
            negative_words = [
                "bad",
                "terrible",
                "hate",
                "awful",
                "dislike",
                "horrible",
                "angry",
            ]

            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)

            if positive_count > negative_count:
                sentiment = SentimentType.POSITIVE
                score = min(positive_count / len(text.split()), 1.0)
            elif negative_count > positive_count:
                sentiment = SentimentType.NEGATIVE
                score = -min(negative_count / len(text.split()), 1.0)
            else:
                sentiment = SentimentType.NEUTRAL
                score = 0.0

            confidence = abs(score)

            # Extract keywords
            keywords = [
                word
                for word in text_lower.split()
                if word in positive_words + negative_words
            ]

            result = SentimentResult(
                sentiment=sentiment,
                confidence=confidence,
                score=score,
                timestamp=datetime.datetime.now(datetime.UTC),
                keywords=keywords,
            )

            # Update sentiment state
            if call_id in self.active_calls:
                call_state = self.active_calls[call_id]
                call_state["sentiment_state"]["current_sentiment"] = sentiment
                call_state["sentiment_state"]["sentiment_history"].append(
                    {
                        "sentiment": sentiment,
                        "score": score,
                        "timestamp": datetime.datetime.now(datetime.UTC),
                    }
                )

            return result

        except Exception as e:
            self.logger.error(f"Failed to analyze sentiment: {e}")
            return None

    def _create_speech_event(
        self,
        event_type: SpeechEventType,
        call_id: str,
        data: Dict[str, Any],
        confidence: float = 0.0,
    ) -> SpeechEvent:
        """Create a speech event"""
        return SpeechEvent(
            event_type=event_type,
            timestamp=datetime.datetime.now(datetime.UTC),
            call_id=call_id,
            data=data,
            confidence=confidence,
        )

    async def _emit_event(self, call_id: str, event: SpeechEvent):
        """Emit speech event to registered callbacks"""
        try:
            if call_id in self.event_callbacks:
                for callback in self.event_callbacks[call_id]:
                    try:
                        await callback(event)
                    except Exception as e:
                        self.logger.error(f"Event callback failed: {e}")

        except Exception as e:
            self.logger.error(f"Failed to emit event: {e}")

    def register_event_callback(self, call_id: str, callback: Callable):
        """Register callback for speech events"""
        if call_id not in self.event_callbacks:
            self.event_callbacks[call_id] = []
        self.event_callbacks[call_id].append(callback)

    def unregister_event_callback(self, call_id: str, callback: Callable):
        """Unregister callback for speech events"""
        if (
            call_id in self.event_callbacks
            and callback in self.event_callbacks[call_id]
        ):
            self.event_callbacks[call_id].remove(callback)

    async def get_call_analytics(self, call_id: str) -> Dict[str, Any]:
        """Get analytics for a call"""
        try:
            if call_id not in self.active_calls:
                return {}

            call_state = self.active_calls[call_id]

            analytics = {
                "call_id": call_id,
                "start_time": call_state["start_time"],
                "duration": (
                    datetime.datetime.now(datetime.UTC) - call_state["start_time"]
                ).total_seconds(),
                "vad_stats": {
                    "total_speech_time": 0.0,
                    "speech_segments": len(call_state["asr_state"]["final_results"]),
                    "average_energy": np.mean(
                        list(call_state["vad_state"]["energy_buffer"])
                    )
                    if call_state["vad_state"]["energy_buffer"]
                    else 0.0,
                },
                "emotion_stats": {
                    "dominant_emotion": None,
                    "emotion_distribution": {},
                    "emotion_changes": len(
                        call_state["emotion_state"]["emotion_history"]
                    ),
                },
                "sentiment_stats": {
                    "overall_sentiment": None,
                    "sentiment_trend": [],
                    "average_score": 0.0,
                },
                "barge_in_stats": {"total_barge_ins": 0, "last_barge_in": None},
                "tts_stats": {"total_tts_time": 0.0, "tts_segments": 0},
            }

            # Calculate emotion distribution
            emotion_counts = {}
            for emotion_record in call_state["emotion_state"]["emotion_history"]:
                emotion = emotion_record["emotion"].value
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

            if emotion_counts:
                analytics["emotion_stats"]["dominant_emotion"] = max(
                    emotion_counts, key=emotion_counts.get
                )
                analytics["emotion_stats"]["emotion_distribution"] = emotion_counts

            # Calculate sentiment trend
            sentiment_scores = [
                record["score"]
                for record in call_state["sentiment_state"]["sentiment_history"]
            ]
            if sentiment_scores:
                analytics["sentiment_stats"]["average_score"] = np.mean(
                    sentiment_scores
                )
                analytics["sentiment_stats"]["sentiment_trend"] = sentiment_scores

            # Calculate barge-in stats
            if call_state["barge_in_state"]["detected"]:
                analytics["barge_in_stats"]["total_barge_ins"] = 1
                analytics["barge_in_stats"]["last_barge_in"] = call_state[
                    "barge_in_state"
                ]["last_detection"]

            return analytics

        except Exception as e:
            self.logger.error(f"Failed to get call analytics for {call_id}: {e}")
            return {}


if __name__ == "__main__":
    # Example usage
    config = {"vad_threshold": 0.5, "sample_rate": 16000, "chunk_size": 1024}

    processor = RealTimeSpeechProcessor(config)
    print("Real-time Speech Processor initialized")
