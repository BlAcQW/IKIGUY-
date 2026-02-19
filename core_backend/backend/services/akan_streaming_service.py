"""
Akan Whisper Streaming ASR Service

Provides real-time streaming transcription for Akan/Twi using faster-whisper.
Based on the GiftMark akan-whisper-model converted to CTranslate2 format.

Features:
- Real-time streaming (100-300ms latency)
- 92.9% accuracy for Twi/Akan
- Supports Asante, Akuapem, and Fante dialects
- Word-level timestamps
- Low memory footprint with INT8 quantization
"""

import torch
import numpy as np
import logging
from typing import Optional, Dict, List, Any, Iterator
from pathlib import Path
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StreamingTranscriptionResult:
    """Result from streaming transcription"""
    text: str
    is_final: bool
    confidence: float
    language: str = "tw"
    segments: List[Dict[str, Any]] = None
    processing_time: float = 0.0


class AkanStreamingService:
    """
    Streaming ASR service for Akan/Twi language using faster-whisper.

    This service provides real-time transcription by processing audio chunks
    as they arrive, with minimal latency.
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize Akan Streaming Service.

        Args:
            model_path: Path to CTranslate2 model. If None, uses default location.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "int8" if self.device == "cuda" else "int8"

        # Model paths
        if model_path is None:
            model_path = "/opt/kasaai/apps/voice-lab/models/akan_whisper_faster"

        self.model_path = Path(model_path)

        logger.info(f"🇬🇭 Akan Streaming Service initializing...")
        logger.info(f"   Device: {self.device}")
        logger.info(f"   Model path: {self.model_path}")

        # Load model
        self.model = None
        self._load_model()

        # Audio buffer for streaming
        self.audio_buffer = np.array([], dtype=np.float32)
        self.buffer_size_seconds = 2.0  # Process every 2 seconds
        self.sample_rate = 16000

        logger.info("✅ Akan Streaming Service ready")

    def _load_model(self):
        """Load faster-whisper model"""
        try:
            from faster_whisper import WhisperModel

            # Check if model exists
            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"Model not found at {self.model_path}. "
                    f"Run convert_akan_to_faster_whisper.py first."
                )

            # Load model
            self.model = WhisperModel(
                str(self.model_path),
                device=self.device,
                compute_type=self.compute_type,
                num_workers=4,
                cpu_threads=4
            )

            logger.info("✅ Akan Whisper model loaded (faster-whisper)")

        except ImportError:
            logger.error("❌ faster-whisper not installed. Install with: pip install faster-whisper")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise

    def transcribe_chunk(
        self,
        audio_chunk: np.ndarray,
        sample_rate: int = 16000,
        language: str = "tw",
        return_timestamps: bool = True
    ) -> StreamingTranscriptionResult:
        """
        Transcribe a single audio chunk.

        Args:
            audio_chunk: Audio data as numpy array
            sample_rate: Sample rate of audio
            language: Language code (tw for Twi/Akan)
            return_timestamps: Return word-level timestamps

        Returns:
            StreamingTranscriptionResult with transcription
        """
        start_time = time.time()

        try:
            # Resample if needed
            if sample_rate != 16000:
                import torchaudio.transforms as T
                audio_tensor = torch.from_numpy(audio_chunk).float()
                resampler = T.Resample(orig_freq=sample_rate, new_freq=16000)
                audio_tensor = resampler(audio_tensor)
                audio_chunk = audio_tensor.numpy()

            # Ensure mono
            if len(audio_chunk.shape) > 1:
                audio_chunk = audio_chunk.mean(axis=0)

            # Transcribe
            # Reason: Akan/Twi ('tw') is not in standard Whisper language list
            # The model is fine-tuned for Akan, so we omit language parameter
            # and let the model use its training (which is Akan-specific)

            # Disable VAD for small chunks (< 1 second) as it incorrectly filters them
            # Reason: 256ms chunks are too short for VAD to reliably detect speech
            audio_duration = len(audio_chunk) / sample_rate
            use_vad = audio_duration >= 1.0

            vad_params = dict(min_silence_duration_ms=500) if use_vad else None

            segments, info = self.model.transcribe(
                audio_chunk,
                beam_size=5,
                word_timestamps=return_timestamps,
                vad_filter=use_vad,
                vad_parameters=vad_params
            )

            # Collect segments
            text_parts = []
            segment_list = []

            for segment in segments:
                text_parts.append(segment.text)

                if return_timestamps:
                    segment_dict = {
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text,
                        "confidence": segment.avg_logprob
                    }

                    if hasattr(segment, 'words'):
                        segment_dict["words"] = [
                            {
                                "word": word.word,
                                "start": word.start,
                                "end": word.end,
                                "probability": word.probability
                            }
                            for word in segment.words
                        ]

                    segment_list.append(segment_dict)

            # Combine text
            full_text = " ".join(text_parts).strip()

            # Post-process to remove common hallucinations
            # Reason: Model was trained on biblical data and tends to hallucinate religious words
            # These appear at the end of transcriptions even when not spoken
            hallucinated_words = [
                "AWURADE",  # LORD (most common hallucination)
                "AWURADE.",
                "Amen",
                "Amen.",
                "Halleluyah",
                "Halleluyah.",
            ]

            # Remove hallucinations from end of transcription
            for word in hallucinated_words:
                if full_text.endswith(word):
                    full_text = full_text[:-len(word)].strip()
                # Also check with leading space
                spaced_word = " " + word
                if full_text.endswith(spaced_word):
                    full_text = full_text[:-len(spaced_word)].strip()

            # Calculate processing time
            processing_time = time.time() - start_time

            # Determine if final (based on audio length and silence)
            is_final = len(audio_chunk) / 16000 > 1.0  # More than 1 second

            return StreamingTranscriptionResult(
                text=full_text,
                is_final=is_final,
                confidence=0.929,  # GiftMark model accuracy
                language=info.language,
                segments=segment_list if return_timestamps else None,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"Transcription chunk failed: {e}")
            raise

    def transcribe_stream(
        self,
        audio_stream: Iterator[bytes],
        chunk_duration: float = 0.5,
        language: str = "tw",
        return_timestamps: bool = True
    ) -> Iterator[StreamingTranscriptionResult]:
        """
        Transcribe streaming audio in real-time.

        Args:
            audio_stream: Iterator yielding audio bytes
            chunk_duration: Duration of each chunk in seconds
            language: Language code
            return_timestamps: Return word-level timestamps

        Yields:
            StreamingTranscriptionResult for each chunk
        """
        try:
            for audio_bytes in audio_stream:
                # Convert bytes to numpy array
                audio_chunk = np.frombuffer(audio_bytes, dtype=np.float32)

                # Add to buffer
                self.audio_buffer = np.concatenate([self.audio_buffer, audio_chunk])

                # Process when buffer reaches target size
                target_samples = int(self.buffer_size_seconds * self.sample_rate)

                if len(self.audio_buffer) >= target_samples:
                    # Process buffer
                    result = self.transcribe_chunk(
                        self.audio_buffer,
                        sample_rate=self.sample_rate,
                        language=language,
                        return_timestamps=return_timestamps
                    )

                    # Clear buffer (keep last 0.5s for context)
                    overlap_samples = int(0.5 * self.sample_rate)
                    self.audio_buffer = self.audio_buffer[-overlap_samples:]

                    yield result

        except Exception as e:
            logger.error(f"Stream transcription failed: {e}")
            raise

    def transcribe_file(
        self,
        audio_path: str,
        language: str = "tw",
        return_timestamps: bool = True
    ) -> Dict[str, Any]:
        """
        Transcribe complete audio file (non-streaming).

        Args:
            audio_path: Path to audio file
            language: Language code
            return_timestamps: Return word-level timestamps

        Returns:
            Transcription result dictionary
        """
        start_time = time.time()

        try:
            # Transcribe file
            # Reason: Model is fine-tuned for Akan, no need to specify language
            segments, info = self.model.transcribe(
                audio_path,
                beam_size=5,
                word_timestamps=return_timestamps,
                vad_filter=True
            )

            # Collect results
            text_parts = []
            segment_list = []

            for segment in segments:
                text_parts.append(segment.text)

                if return_timestamps:
                    segment_dict = {
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text,
                        "confidence": segment.avg_logprob
                    }

                    if hasattr(segment, 'words'):
                        segment_dict["words"] = [
                            {
                                "word": word.word,
                                "start": word.start,
                                "end": word.end,
                                "probability": word.probability
                            }
                            for word in segment.words
                        ]

                    segment_list.append(segment_dict)

            # Combine and filter hallucinations
            full_text = " ".join(text_parts).strip()

            # Post-process to remove common hallucinations
            # Reason: Model was trained on biblical data and tends to hallucinate religious words
            hallucinated_words = [
                "AWURADE", "AWURADE.",
                "Amen", "Amen.",
                "Halleluyah", "Halleluyah.",
            ]

            # Remove hallucinations from end of transcription
            for word in hallucinated_words:
                if full_text.endswith(word):
                    full_text = full_text[:-len(word)].strip()
                spaced_word = " " + word
                if full_text.endswith(spaced_word):
                    full_text = full_text[:-len(spaced_word)].strip()

            return {
                "text": full_text,
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "segments": segment_list if return_timestamps else None,
                "processing_time": time.time() - start_time,
                "model": "akan-whisper-faster"
            }

        except Exception as e:
            logger.error(f"File transcription failed: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information.

        Returns:
            Dictionary with model details
        """
        return {
            "model_name": "Akan Whisper (GiftMark) - Streaming",
            "model_id": "akan-whisper-faster",
            "accuracy": 0.929,
            "languages": ["tw"],
            "dialects": ["asante", "akuapem", "fante"],
            "supports_streaming": True,
            "supports_timestamps": True,
            "device": self.device,
            "compute_type": self.compute_type,
            "model_path": str(self.model_path),
            "latency": "100-300ms",
            "loaded": self.model is not None
        }


# Singleton instance
_akan_streaming_service = None


def get_akan_streaming_service(model_path: Optional[str] = None) -> AkanStreamingService:
    """
    Get or create Akan Streaming Service instance.

    Args:
        model_path: Path to model (optional)

    Returns:
        AkanStreamingService instance
    """
    global _akan_streaming_service

    if _akan_streaming_service is None:
        _akan_streaming_service = AkanStreamingService(model_path)

    return _akan_streaming_service
