"""
Tests for audio processing utilities.

Tests audio buffering, format conversion, and streaming utilities.
"""

import pytest
import base64
import struct
from apps.shared.websocket.audio_processor import AudioBuffer, AudioProcessor


class TestAudioBuffer:
    """Tests for AudioBuffer class."""

    def test_create_buffer(self):
        """Test creating an audio buffer."""
        buffer = AudioBuffer(
            chunk_size=480,
            sample_rate=24000,
        )

        assert buffer.chunk_size == 480
        assert buffer.sample_rate == 24000
        assert buffer.size == 0
        assert buffer.duration_ms == 0

    def test_add_data(self):
        """Test adding data to buffer."""
        buffer = AudioBuffer()

        # Add 100 samples (200 bytes for 16-bit)
        data = b"\x00" * 200
        buffer.add(data)

        assert buffer.size == 200

    def test_add_base64_data(self):
        """Test adding base64-encoded data."""
        buffer = AudioBuffer()

        data = b"\x00" * 100
        b64 = base64.b64encode(data).decode()
        buffer.add_base64(b64)

        assert buffer.size == 100

    def test_get_chunk(self):
        """Test getting a chunk from buffer."""
        buffer = AudioBuffer(chunk_size=100)  # 100 samples = 200 bytes

        # Add enough data for one chunk
        data = b"\x01" * 200
        buffer.add(data)

        chunk = buffer.get_chunk()

        assert chunk is not None
        assert len(chunk) == 200
        assert buffer.size == 0  # Buffer should be empty

    def test_get_chunk_insufficient_data(self):
        """Test getting chunk with insufficient data."""
        buffer = AudioBuffer(chunk_size=100)

        # Add less than one chunk
        buffer.add(b"\x00" * 100)

        chunk = buffer.get_chunk()

        assert chunk is None
        assert buffer.size == 100  # Data should remain

    def test_get_multiple_chunks(self):
        """Test getting multiple chunks."""
        buffer = AudioBuffer(chunk_size=100)

        # Add data for 3 chunks
        buffer.add(b"\x00" * 600)

        chunks = list(buffer.get_chunks())

        assert len(chunks) == 3
        assert all(len(c) == 200 for c in chunks)
        assert buffer.size == 0

    def test_drain(self):
        """Test draining all data."""
        buffer = AudioBuffer()

        buffer.add(b"\x01\x02\x03\x04")
        data = buffer.drain()

        assert data == b"\x01\x02\x03\x04"
        assert buffer.size == 0

    def test_clear(self):
        """Test clearing buffer."""
        buffer = AudioBuffer()

        buffer.add(b"\x00" * 1000)
        buffer.clear()

        assert buffer.size == 0

    def test_duration_calculation(self):
        """Test duration calculation."""
        buffer = AudioBuffer(sample_rate=16000)

        # Add 16000 samples = 1 second (32000 bytes)
        buffer.add(b"\x00" * 32000)

        assert buffer.duration_ms == 1000.0

    def test_buffer_overflow(self):
        """Test buffer overflow handling."""
        buffer = AudioBuffer(
            max_buffer_size=1000,  # 1000 samples = 2000 bytes
        )

        # Try to add more than max
        buffer.add(b"\x00" * 3000)

        # Should be trimmed to max
        assert buffer.size <= 2000


class TestAudioProcessor:
    """Tests for AudioProcessor class."""

    def test_pcm_to_wav(self):
        """Test PCM to WAV conversion."""
        # Create simple PCM data (100 samples of silence)
        pcm = b"\x00" * 200

        wav = AudioProcessor.pcm_to_wav(
            pcm,
            sample_rate=16000,
            channels=1,
            bits_per_sample=16,
        )

        # WAV should be larger than PCM (header added)
        assert len(wav) > len(pcm)
        # Check WAV header
        assert wav[:4] == b"RIFF"
        assert wav[8:12] == b"WAVE"

    def test_wav_to_pcm(self):
        """Test WAV to PCM conversion."""
        # Create WAV from PCM
        original_pcm = b"\x00\x01" * 100
        wav = AudioProcessor.pcm_to_wav(original_pcm, sample_rate=16000)

        # Convert back
        pcm, sample_rate, channels = AudioProcessor.wav_to_pcm(wav)

        assert pcm == original_pcm
        assert sample_rate == 16000
        assert channels == 1

    def test_encode_decode_base64(self):
        """Test base64 encoding/decoding."""
        original = b"Hello, World!"

        encoded = AudioProcessor.encode_base64(original)
        decoded = AudioProcessor.decode_base64(encoded)

        assert decoded == original
        assert encoded == "SGVsbG8sIFdvcmxkIQ=="

    def test_calculate_energy_silence(self):
        """Test energy calculation for silence."""
        # Silence = all zeros
        silence = b"\x00" * 200

        energy = AudioProcessor.calculate_energy(silence)

        assert energy == 0.0

    def test_calculate_energy_loud(self):
        """Test energy calculation for loud audio."""
        # Max amplitude samples
        samples = [32767] * 100
        loud = struct.pack("<" + "h" * 100, *samples)

        energy = AudioProcessor.calculate_energy(loud)

        assert energy > 0.9  # Should be near max

    def test_is_silent_true(self):
        """Test silence detection for silent audio."""
        silence = b"\x00" * 200

        assert AudioProcessor.is_silent(silence) is True

    def test_is_silent_false(self):
        """Test silence detection for loud audio."""
        samples = [10000] * 100
        loud = struct.pack("<" + "h" * 100, *samples)

        assert AudioProcessor.is_silent(loud) is False

    def test_split_into_chunks(self):
        """Test splitting audio into chunks."""
        # Create data for 3 chunks of 100 samples each
        data = b"\x00" * 600  # 300 samples

        chunks = AudioProcessor.split_into_chunks(data, chunk_size=100)

        assert len(chunks) == 3
        assert all(len(c) == 200 for c in chunks)

    def test_split_into_chunks_remainder(self):
        """Test splitting with remainder (incomplete chunk)."""
        # Create data for 2.5 chunks
        data = b"\x00" * 500

        chunks = AudioProcessor.split_into_chunks(data, chunk_size=100)

        # Should only get complete chunks
        assert len(chunks) == 2

    def test_resample_same_rate(self):
        """Test resampling with same rate (no-op)."""
        data = b"\x00\x01\x02\x03"

        result = AudioProcessor.resample(data, 16000, 16000)

        assert result == data

    def test_resample_upsample(self):
        """Test upsampling audio."""
        # Create 100 samples
        samples = [1000, 2000, 3000, 4000]
        data = struct.pack("<" + "h" * 4, *samples)

        result = AudioProcessor.resample(data, 16000, 32000)

        # Should have approximately double the samples
        assert len(result) >= len(data)

    def test_resample_downsample(self):
        """Test downsampling audio."""
        # Create 100 samples
        samples = [1000] * 100
        data = struct.pack("<" + "h" * 100, *samples)

        result = AudioProcessor.resample(data, 32000, 16000)

        # Should have approximately half the samples
        assert len(result) <= len(data)
