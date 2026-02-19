"""
PCM Audio and VAD Handler for Voice Conversations.

Provides utilities for:
- Converting raw PCM to WAV format
- Managing VAD sessions for voice conversations
- Processing PCM chunks with real-time VAD

If PyTorch is not installed, uses a simple fallback that accumulates
audio and requires manual stop (no automatic VAD).

Usage:
    from apps.shared.voice import pcm_to_wav, PCMVADHandler

    handler = PCMVADHandler(session_id="ws-123")
    is_speech, complete, audio = handler.process_pcm_base64(pcm_base64)

Author: AI Labs Africa
"""

import struct
import io
import base64
import numpy as np
from typing import Tuple, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import VADSession, fall back to None if not available
VADSession = None
try:
    import sys
    sys.path.insert(0, '/opt/kasaai/apps')
    try:
        from apps.shared.integration.ai_services import VADSession
        logger.info("VADSession imported from shared library")
    except ImportError:
        sys.path.insert(0, '/opt/kasaai/apps/shared')
        from integration.ai_services import VADSession
        logger.info("VADSession imported from fallback path")
except Exception as e:
    logger.warning(f"VADSession not available (PyTorch may not be installed): {e}")
    VADSession = None


def pcm_to_wav(pcm_samples: np.ndarray, sample_rate: int = 16000) -> bytes:
    """
    Convert Float32 PCM samples to WAV file bytes.

    Args:
        pcm_samples: Float32 array normalized to [-1.0, 1.0]
        sample_rate: Sample rate (default 16000)

    Returns:
        WAV file as bytes
    """
    # Convert float32 to int16
    pcm_int16 = np.clip(pcm_samples * 32767, -32768, 32767).astype(np.int16)

    # Create WAV file in memory
    wav_buffer = io.BytesIO()

    # Write WAV header
    num_samples = len(pcm_int16)
    num_channels = 1
    sample_width = 2  # 16-bit

    # RIFF header
    wav_buffer.write(b'RIFF')
    wav_buffer.write(struct.pack('<I', 36 + num_samples * sample_width))
    wav_buffer.write(b'WAVE')

    # fmt subchunk
    wav_buffer.write(b'fmt ')
    wav_buffer.write(struct.pack('<I', 16))  # Subchunk size
    wav_buffer.write(struct.pack('<H', 1))   # Audio format (PCM)
    wav_buffer.write(struct.pack('<H', num_channels))
    wav_buffer.write(struct.pack('<I', sample_rate))
    wav_buffer.write(struct.pack('<I', sample_rate * num_channels * sample_width))
    wav_buffer.write(struct.pack('<H', num_channels * sample_width))
    wav_buffer.write(struct.pack('<H', sample_width * 8))

    # data subchunk
    wav_buffer.write(b'data')
    wav_buffer.write(struct.pack('<I', num_samples * sample_width))
    wav_buffer.write(pcm_int16.tobytes())

    return wav_buffer.getvalue()


class SimplePCMAccumulator:
    """
    Simple PCM accumulator without VAD (fallback when PyTorch not available).

    Accumulates PCM audio chunks until manually stopped.
    Does not perform automatic voice activity detection.

    Attributes:
        session_id: Unique session identifier
        max_utterance_duration_s: Maximum duration before forcing completion
        is_listening: Whether currently accumulating audio
    """

    def __init__(self, session_id: str, max_utterance_duration_s: int = 30):
        """
        Initialize simple PCM accumulator.

        Args:
            session_id: Unique session identifier
            max_utterance_duration_s: Max duration before forcing completion
        """
        self.session_id = session_id
        self.max_utterance_duration_s = max_utterance_duration_s
        self.is_listening = False
        self.audio_chunks: List[np.ndarray] = []
        self.listening_start_time: Optional[datetime] = None
        self.total_samples = 0

    def start_listening(self):
        """Start accumulating audio."""
        self.is_listening = True
        self.audio_chunks = []
        self.listening_start_time = datetime.now()
        self.total_samples = 0
        logger.info(f"SimplePCMAccumulator started for session: {self.session_id}")

    def stop_listening(self) -> Optional[np.ndarray]:
        """
        Stop accumulating and return all audio.

        Returns:
            Concatenated PCM audio or None if no audio
        """
        self.is_listening = False
        if not self.audio_chunks:
            logger.info(f"SimplePCMAccumulator stopped (no audio): {self.session_id}")
            return None

        complete_audio = np.concatenate(self.audio_chunks)
        duration = len(complete_audio) / 16000
        logger.info(
            f"SimplePCMAccumulator stopped: {self.session_id}, "
            f"{len(self.audio_chunks)} chunks, {duration:.2f}s audio"
        )
        self.audio_chunks = []
        return complete_audio

    def process_chunk(
        self,
        pcm_samples: np.ndarray
    ) -> Tuple[bool, bool, Optional[np.ndarray]]:
        """
        Process a PCM chunk (just accumulate, no VAD).

        Args:
            pcm_samples: Float32 PCM samples

        Returns:
            Tuple of (is_speech=True, utterance_complete, complete_audio)
            - Always returns is_speech=True since we can't detect
            - utterance_complete only True if max duration reached
        """
        if not self.is_listening:
            return False, False, None

        self.audio_chunks.append(pcm_samples.copy())
        self.total_samples += len(pcm_samples)

        # Check max duration
        duration = self.total_samples / 16000
        if duration >= self.max_utterance_duration_s:
            logger.info(f"Max duration reached ({duration:.1f}s), forcing completion")
            complete_audio = np.concatenate(self.audio_chunks)
            self.audio_chunks = []
            self.total_samples = 0
            return True, True, complete_audio

        # No automatic completion - user must stop manually
        return True, False, None

    def get_stats(self) -> dict:
        """
        Get accumulator statistics.

        Returns:
            Dictionary with session statistics
        """
        duration = self.total_samples / 16000 if self.total_samples > 0 else 0
        return {
            "session_id": self.session_id,
            "is_listening": self.is_listening,
            "chunks": len(self.audio_chunks),
            "total_samples": self.total_samples,
            "duration_s": duration,
            "vad_enabled": False
        }

    def cleanup(self):
        """Cleanup resources."""
        self.audio_chunks = []
        self.is_listening = False
        logger.info(f"SimplePCMAccumulator cleaned up: {self.session_id}")


class PCMVADHandler:
    """
    Handles PCM audio chunks with integrated VAD for WebSocket conversations.

    If PyTorch/VADSession is available, uses Silero VAD for automatic
    utterance detection. Otherwise, falls back to simple accumulation
    (requires manual stop).

    Attributes:
        session_id: Unique identifier for this conversation session
        vad_session: VADSession or SimplePCMAccumulator
        vad_enabled: True if Silero VAD is available
    """

    def __init__(
        self,
        session_id: str,
        threshold: float = 0.5,
        min_silence_duration_ms: int = 1500,
        max_utterance_duration_s: int = 30
    ):
        """
        Initialize PCM/VAD handler.

        Args:
            session_id: Unique session identifier
            threshold: Speech detection threshold (0-1)
            min_silence_duration_ms: Silence duration to end utterance
            max_utterance_duration_s: Max duration before forcing completion
        """
        self.session_id = session_id
        self.vad_enabled = False

        # Try to use VADSession if available
        if VADSession is not None:
            try:
                self.vad_session = VADSession(
                    session_id=session_id,
                    threshold=threshold,
                    min_silence_duration_ms=min_silence_duration_ms,
                    max_utterance_duration_s=max_utterance_duration_s
                )
                self.vad_enabled = True
                logger.info(
                    f"PCMVADHandler initialized with Silero VAD: {session_id}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize VADSession, using fallback: {e}"
                )
                self.vad_session = SimplePCMAccumulator(
                    session_id=session_id,
                    max_utterance_duration_s=max_utterance_duration_s
                )
        else:
            # Use simple accumulator
            self.vad_session = SimplePCMAccumulator(
                session_id=session_id,
                max_utterance_duration_s=max_utterance_duration_s
            )
            logger.info(
                f"PCMVADHandler initialized without VAD (fallback): {session_id}"
            )

    def start_listening(self):
        """Start listening for a new utterance."""
        self.vad_session.start_listening()
        logger.info(f"Session {self.session_id}: Started listening")

    def stop_listening(self) -> Optional[np.ndarray]:
        """
        Stop listening and return any accumulated audio.

        Returns:
            Accumulated PCM audio or None
        """
        audio = self.vad_session.stop_listening()
        logger.info(f"Session {self.session_id}: Stopped listening")
        return audio

    def process_pcm_base64(
        self,
        pcm_base64: str
    ) -> Tuple[bool, bool, Optional[np.ndarray]]:
        """
        Process base64-encoded PCM chunk.

        Args:
            pcm_base64: Base64-encoded Float32Array PCM samples

        Returns:
            Tuple of (is_speech, utterance_complete, complete_audio)
        """
        try:
            pcm_bytes = base64.b64decode(pcm_base64)

            # Convert bytes to Float32 array
            pcm_array = np.frombuffer(pcm_bytes, dtype=np.float32)

            logger.debug(
                f"Decoded PCM chunk: {len(pcm_array)} samples "
                f"({len(pcm_array) / 16000:.2f}s @ 16kHz)"
            )

            # Process with VAD or accumulator
            return self.vad_session.process_chunk(pcm_array)

        except Exception as e:
            logger.error(f"Error processing PCM base64: {e}")
            return False, False, None

    def get_stats(self) -> dict:
        """
        Get session statistics for monitoring.

        Returns:
            Dictionary with session stats
        """
        stats = self.vad_session.get_stats()
        stats["vad_enabled"] = self.vad_enabled
        return stats

    def cleanup(self):
        """Cleanup resources."""
        self.vad_session.cleanup()
        logger.info(f"PCMVADHandler cleaned up for session: {self.session_id}")


def pcm_base64_to_wav_base64(pcm_base64: str, sample_rate: int = 16000) -> str:
    """
    Convert base64-encoded PCM to base64-encoded WAV.

    Args:
        pcm_base64: Base64-encoded Float32Array PCM
        sample_rate: Sample rate (default 16000)

    Returns:
        Base64-encoded WAV file
    """
    pcm_bytes = base64.b64decode(pcm_base64)
    pcm_array = np.frombuffer(pcm_bytes, dtype=np.float32)

    wav_bytes = pcm_to_wav(pcm_array, sample_rate)

    wav_base64 = base64.b64encode(wav_bytes).decode('utf-8')

    return wav_base64


__all__ = [
    'pcm_to_wav',
    'PCMVADHandler',
    'SimplePCMAccumulator',
    'pcm_base64_to_wav_base64'
]
