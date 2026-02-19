"""
PCM Audio and VAD Handler for WebSocket Voice Chat

Provides utilities for:
- Converting raw PCM to WAV format
- Managing VAD sessions for voice conversations
- Processing PCM chunks with real-time VAD

Usage:
    from backend.services.pcm_vad_handler import pcm_to_wav, PCMVADHandler

    handler = PCMVADHandler(session_id="ws-123")
    is_speech, complete, audio = handler.process_pcm_chunk(pcm_base64)
"""

import struct
import io
import base64
import numpy as np
from typing import Tuple, Optional
import logging

# Import from shared library
from apps.shared.integration.ai_services import VADSession

logger = logging.getLogger(__name__)


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


class PCMVADHandler:
    """
    Handles PCM audio chunks with integrated VAD for WebSocket conversations.

    Manages VAD session lifecycle and provides convenient methods for
    processing PCM chunks received via WebSocket.

    Attributes:
        session_id: Unique identifier for this conversation session
        vad_session: VADSession instance for voice activity detection
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
        self.vad_session = VADSession(
            session_id=session_id,
            threshold=threshold,
            min_silence_duration_ms=min_silence_duration_ms,
            max_utterance_duration_s=max_utterance_duration_s
        )
        logger.info(f"✅ PCMVADHandler initialized for session: {session_id}")

    def start_listening(self):
        """Start listening for a new utterance."""
        self.vad_session.start_listening()
        logger.info(f"🎤 Session {self.session_id}: Started listening")

    def stop_listening(self) -> Optional[np.ndarray]:
        """
        Stop listening and return any accumulated audio.

        Returns:
            Accumulated PCM audio or None
        """
        audio = self.vad_session.stop_listening()
        logger.info(f"⏹️  Session {self.session_id}: Stopped listening")
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
        # Decode base64
        try:
            pcm_bytes = base64.b64decode(pcm_base64)

            # Convert bytes to Float32 array
            pcm_array = np.frombuffer(pcm_bytes, dtype=np.float32)

            logger.debug(
                f"📦 Decoded PCM chunk: {len(pcm_array)} samples "
                f"({len(pcm_array) / 16000:.2f}s @ 16kHz)"
            )

            # Process with VAD
            return self.vad_session.process_chunk(pcm_array)

        except Exception as e:
            logger.error(f"❌ Error processing PCM base64: {e}")
            return False, False, None

    def get_stats(self) -> dict:
        """
        Get session statistics for monitoring.

        Returns:
            Dictionary with session stats
        """
        return self.vad_session.get_stats()

    def cleanup(self):
        """Cleanup resources."""
        self.vad_session.cleanup()
        logger.info(f"🧹 PCMVADHandler cleaned up for session: {self.session_id}")


def pcm_base64_to_wav_base64(pcm_base64: str, sample_rate: int = 16000) -> str:
    """
    Convert base64-encoded PCM to base64-encoded WAV.

    Convenience function for quick conversion.

    Args:
        pcm_base64: Base64-encoded Float32Array PCM
        sample_rate: Sample rate (default 16000)

    Returns:
        Base64-encoded WAV file
    """
    # Decode PCM
    pcm_bytes = base64.b64decode(pcm_base64)
    pcm_array = np.frombuffer(pcm_bytes, dtype=np.float32)

    # Convert to WAV
    wav_bytes = pcm_to_wav(pcm_array, sample_rate)

    # Encode back to base64
    wav_base64 = base64.b64encode(wav_bytes).decode('utf-8')

    return wav_base64


__all__ = [
    'pcm_to_wav',
    'PCMVADHandler',
    'pcm_base64_to_wav_base64'
]
