"""
Tests for PCMVADHandler and related utilities.

Tests PCM audio processing, WAV conversion, and VAD handling.
"""

import sys
import os

# Ensure apps path is in sys.path
apps_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
if apps_path not in sys.path:
    sys.path.insert(0, apps_path)

import pytest
import base64
import numpy as np
from apps.shared.voice import (
    PCMVADHandler,
    SimplePCMAccumulator,
    pcm_to_wav,
    pcm_base64_to_wav_base64,
)


class TestPcmToWav:
    """Tests for pcm_to_wav function."""

    def test_basic_conversion(self):
        """Test basic PCM to WAV conversion."""
        # Create 1 second of silence at 16kHz
        pcm = np.zeros(16000, dtype=np.float32)
        wav_bytes = pcm_to_wav(pcm)

        # WAV header is 44 bytes + 16000 samples * 2 bytes = 32044 bytes
        assert len(wav_bytes) == 32044

        # Check WAV header
        assert wav_bytes[:4] == b'RIFF'
        assert wav_bytes[8:12] == b'WAVE'
        assert wav_bytes[12:16] == b'fmt '
        assert wav_bytes[36:40] == b'data'

    def test_sample_rate(self):
        """Test WAV with different sample rate."""
        pcm = np.zeros(8000, dtype=np.float32)  # 0.5 seconds at 8kHz
        wav_bytes = pcm_to_wav(pcm, sample_rate=8000)

        # 44 bytes header + 8000 samples * 2 bytes = 16044 bytes
        assert len(wav_bytes) == 16044

    def test_audio_data_preservation(self):
        """Test that audio data is preserved (just scaled)."""
        # Create known audio pattern
        pcm = np.array([0.0, 0.5, 1.0, -0.5, -1.0], dtype=np.float32)
        wav_bytes = pcm_to_wav(pcm)

        # Extract int16 samples from WAV (after 44-byte header)
        int16_samples = np.frombuffer(wav_bytes[44:], dtype=np.int16)

        # Check scaling (float32 [-1, 1] -> int16 [-32768, 32767])
        assert int16_samples[0] == 0  # 0.0 -> 0
        assert int16_samples[1] == 16383  # 0.5 -> ~16383
        assert int16_samples[2] == 32767  # 1.0 -> 32767 (clipped)
        assert int16_samples[3] == -16383  # -0.5 -> ~-16383
        # -1.0 * 32767 = -32767 (not -32768 due to asymmetric int16 range)
        assert int16_samples[4] == -32767  # -1.0 -> -32767

    def test_clipping(self):
        """Test values outside [-1, 1] are clipped."""
        pcm = np.array([2.0, -2.0], dtype=np.float32)
        wav_bytes = pcm_to_wav(pcm)

        int16_samples = np.frombuffer(wav_bytes[44:], dtype=np.int16)

        # Should be clipped to max/min int16
        assert int16_samples[0] == 32767
        assert int16_samples[1] == -32768


class TestPcmBase64ToWavBase64:
    """Tests for pcm_base64_to_wav_base64 function."""

    def test_basic_conversion(self):
        """Test base64 PCM to base64 WAV conversion."""
        # Create PCM data
        pcm = np.zeros(16000, dtype=np.float32)
        pcm_b64 = base64.b64encode(pcm.tobytes()).decode('utf-8')

        wav_b64 = pcm_base64_to_wav_base64(pcm_b64)

        # Decode and verify
        wav_bytes = base64.b64decode(wav_b64)
        assert wav_bytes[:4] == b'RIFF'
        assert len(wav_bytes) == 32044

    def test_roundtrip(self):
        """Test that data survives roundtrip conversion."""
        # Create known pattern
        pcm = np.array([0.1, 0.2, 0.3] * 1000, dtype=np.float32)
        pcm_b64 = base64.b64encode(pcm.tobytes()).decode('utf-8')

        wav_b64 = pcm_base64_to_wav_base64(pcm_b64)
        wav_bytes = base64.b64decode(wav_b64)

        # Should have valid WAV structure
        assert wav_bytes[:4] == b'RIFF'
        assert len(wav_bytes) == 44 + len(pcm) * 2  # header + samples


class TestSimplePCMAccumulator:
    """Tests for SimplePCMAccumulator (fallback when VAD unavailable)."""

    def test_initial_state(self):
        """Test initial state is not listening."""
        acc = SimplePCMAccumulator("test-session")

        assert acc.is_listening is False
        assert len(acc.audio_chunks) == 0
        assert acc.total_samples == 0

    def test_start_listening(self):
        """Test start_listening enables accumulation."""
        acc = SimplePCMAccumulator("test-session")
        acc.start_listening()

        assert acc.is_listening is True
        assert acc.listening_start_time is not None

    def test_stop_listening_returns_none_when_empty(self):
        """Test stop_listening returns None when no audio."""
        acc = SimplePCMAccumulator("test-session")
        acc.start_listening()

        result = acc.stop_listening()

        assert result is None
        assert acc.is_listening is False

    def test_accumulate_chunks(self):
        """Test chunks are accumulated correctly."""
        acc = SimplePCMAccumulator("test-session")
        acc.start_listening()

        # Add two chunks
        chunk1 = np.ones(1000, dtype=np.float32)
        chunk2 = np.ones(2000, dtype=np.float32) * 0.5

        is_speech1, complete1, audio1 = acc.process_chunk(chunk1)
        is_speech2, complete2, audio2 = acc.process_chunk(chunk2)

        # Should indicate speech detected but not complete
        assert is_speech1 is True
        assert complete1 is False
        assert audio1 is None

        assert is_speech2 is True
        assert complete2 is False
        assert audio2 is None

        # Check accumulated samples
        assert acc.total_samples == 3000

    def test_stop_listening_returns_concatenated_audio(self):
        """Test stop_listening returns all accumulated audio."""
        acc = SimplePCMAccumulator("test-session")
        acc.start_listening()

        chunk1 = np.ones(1000, dtype=np.float32)
        chunk2 = np.ones(2000, dtype=np.float32) * 0.5

        acc.process_chunk(chunk1)
        acc.process_chunk(chunk2)

        result = acc.stop_listening()

        assert result is not None
        assert len(result) == 3000
        assert result[0] == 1.0  # From chunk1
        assert result[1500] == 0.5  # From chunk2

    def test_max_duration_forces_completion(self):
        """Test that max duration triggers automatic completion."""
        # Set very short max duration for testing
        acc = SimplePCMAccumulator("test-session", max_utterance_duration_s=1)
        acc.start_listening()

        # Add more than 1 second of audio
        chunk = np.ones(16001, dtype=np.float32)  # 1.00006 seconds

        is_speech, complete, audio = acc.process_chunk(chunk)

        assert complete is True
        assert audio is not None
        assert len(audio) == 16001

    def test_process_chunk_while_not_listening(self):
        """Test process_chunk returns nothing when not listening."""
        acc = SimplePCMAccumulator("test-session")
        # Don't call start_listening

        chunk = np.ones(1000, dtype=np.float32)
        is_speech, complete, audio = acc.process_chunk(chunk)

        assert is_speech is False
        assert complete is False
        assert audio is None

    def test_get_stats(self):
        """Test get_stats returns correct statistics."""
        acc = SimplePCMAccumulator("test-session")
        acc.start_listening()

        chunk = np.ones(8000, dtype=np.float32)  # 0.5 seconds
        acc.process_chunk(chunk)

        stats = acc.get_stats()

        assert stats["session_id"] == "test-session"
        assert stats["is_listening"] is True
        assert stats["chunks"] == 1
        assert stats["total_samples"] == 8000
        assert abs(stats["duration_s"] - 0.5) < 0.001
        assert stats["vad_enabled"] is False

    def test_cleanup(self):
        """Test cleanup clears state."""
        acc = SimplePCMAccumulator("test-session")
        acc.start_listening()
        acc.process_chunk(np.ones(1000, dtype=np.float32))

        acc.cleanup()

        assert acc.is_listening is False
        assert len(acc.audio_chunks) == 0


class TestPCMVADHandler:
    """Tests for PCMVADHandler."""

    def test_initialization(self):
        """Test handler initializes with fallback when VAD unavailable."""
        handler = PCMVADHandler("test-session")

        # Should have created a session (either VAD or fallback)
        assert handler.session_id == "test-session"
        assert handler.vad_session is not None

    def test_start_and_stop_listening(self):
        """Test start and stop listening."""
        handler = PCMVADHandler("test-session")
        handler.start_listening()

        assert handler.vad_session.is_listening is True

        handler.stop_listening()
        assert handler.vad_session.is_listening is False

    def test_process_pcm_base64(self):
        """Test processing base64-encoded PCM."""
        handler = PCMVADHandler("test-session")
        handler.start_listening()

        # Create base64 PCM
        pcm = np.ones(1000, dtype=np.float32) * 0.5
        pcm_b64 = base64.b64encode(pcm.tobytes()).decode('utf-8')

        is_speech, complete, audio = handler.process_pcm_base64(pcm_b64)

        # Should indicate speech but not complete (with fallback)
        assert is_speech is True
        assert complete is False

    def test_process_invalid_base64(self):
        """Test handling of invalid base64."""
        handler = PCMVADHandler("test-session")
        handler.start_listening()

        is_speech, complete, audio = handler.process_pcm_base64("not-valid-base64!")

        # Should fail gracefully
        assert is_speech is False
        assert complete is False
        assert audio is None

    def test_get_stats(self):
        """Test get_stats returns statistics."""
        handler = PCMVADHandler("test-session")

        stats = handler.get_stats()

        assert "session_id" in stats
        assert "vad_enabled" in stats
        assert stats["session_id"] == "test-session"

    def test_cleanup(self):
        """Test cleanup releases resources."""
        handler = PCMVADHandler("test-session")
        handler.start_listening()

        handler.cleanup()

        assert handler.vad_session.is_listening is False

    def test_custom_threshold(self):
        """Test handler accepts custom VAD parameters."""
        handler = PCMVADHandler(
            "test-session",
            threshold=0.8,
            min_silence_duration_ms=2000,
            max_utterance_duration_s=60
        )

        # Should initialize without error
        assert handler.session_id == "test-session"
