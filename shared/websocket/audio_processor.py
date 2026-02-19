"""
Audio Processing Utilities

Provides audio buffering, format conversion, and streaming utilities
for WebSocket voice conversations.

Author: KasaAI Team
Date: 2025-11-26
"""

import logging
import base64
import io
import wave
import struct
from typing import Optional, List, Generator, AsyncGenerator
from collections import deque

logger = logging.getLogger(__name__)


class AudioBuffer:
    """
    Thread-safe audio buffer for collecting and chunking audio data.

    Supports:
    - Adding audio chunks
    - Getting fixed-size chunks
    - Draining all data
    """

    def __init__(
        self,
        chunk_size: int = 480,  # 20ms at 24kHz (mono, 16-bit)
        sample_rate: int = 24000,
        max_buffer_size: int = 480000,  # 10 seconds
    ):
        """
        Initialize audio buffer.

        Args:
            chunk_size: Size of output chunks in samples
            sample_rate: Audio sample rate
            max_buffer_size: Maximum buffer size in samples
        """
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.max_buffer_size = max_buffer_size
        self._buffer = bytearray()
        self._bytes_per_sample = 2  # 16-bit audio

    def add(self, data: bytes):
        """
        Add audio data to buffer.

        Args:
            data: Audio data bytes (16-bit PCM)
        """
        # Add data first
        self._buffer.extend(data)

        # Trim if exceeding max size
        max_bytes = self.max_buffer_size * self._bytes_per_sample
        if len(self._buffer) > max_bytes:
            overflow = len(self._buffer) - max_bytes
            self._buffer = self._buffer[overflow:]
            logger.warning(f"Audio buffer overflow, trimmed {overflow} bytes")

    def add_base64(self, data: str):
        """
        Add base64-encoded audio data.

        Args:
            data: Base64-encoded audio
        """
        try:
            audio_bytes = base64.b64decode(data)
            self.add(audio_bytes)
        except Exception as e:
            logger.error(f"Error decoding base64 audio: {e}")

    def get_chunk(self) -> Optional[bytes]:
        """
        Get a fixed-size chunk from buffer.

        Returns:
            Audio chunk or None if insufficient data
        """
        chunk_bytes = self.chunk_size * self._bytes_per_sample
        if len(self._buffer) < chunk_bytes:
            return None

        chunk = bytes(self._buffer[:chunk_bytes])
        self._buffer = self._buffer[chunk_bytes:]
        return chunk

    def get_chunks(self) -> Generator[bytes, None, None]:
        """
        Get all available chunks from buffer.

        Yields:
            Audio chunks
        """
        while True:
            chunk = self.get_chunk()
            if chunk is None:
                break
            yield chunk

    def drain(self) -> bytes:
        """
        Drain all data from buffer.

        Returns:
            All buffered data
        """
        data = bytes(self._buffer)
        self._buffer.clear()
        return data

    def clear(self):
        """Clear the buffer."""
        self._buffer.clear()

    @property
    def size(self) -> int:
        """Get buffer size in bytes."""
        return len(self._buffer)

    @property
    def duration_ms(self) -> float:
        """Get buffer duration in milliseconds."""
        samples = len(self._buffer) // self._bytes_per_sample
        return (samples / self.sample_rate) * 1000


class AudioProcessor:
    """
    Audio processing utilities for format conversion and manipulation.
    """

    @staticmethod
    def pcm_to_wav(
        pcm_data: bytes,
        sample_rate: int = 16000,
        channels: int = 1,
        bits_per_sample: int = 16,
    ) -> bytes:
        """
        Convert raw PCM audio to WAV format.

        Args:
            pcm_data: Raw PCM audio bytes
            sample_rate: Sample rate in Hz
            channels: Number of channels (1=mono, 2=stereo)
            bits_per_sample: Bits per sample (8, 16, or 24)

        Returns:
            WAV audio bytes
        """
        buffer = io.BytesIO()

        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(channels)
            wav.setsampwidth(bits_per_sample // 8)
            wav.setframerate(sample_rate)
            wav.writeframes(pcm_data)

        return buffer.getvalue()

    @staticmethod
    def wav_to_pcm(wav_data: bytes) -> tuple[bytes, int, int]:
        """
        Extract PCM data from WAV file.

        Args:
            wav_data: WAV audio bytes

        Returns:
            Tuple of (pcm_data, sample_rate, channels)
        """
        buffer = io.BytesIO(wav_data)

        with wave.open(buffer, "rb") as wav:
            sample_rate = wav.getframerate()
            channels = wav.getnchannels()
            pcm_data = wav.readframes(wav.getnframes())

        return pcm_data, sample_rate, channels

    @staticmethod
    def encode_base64(data: bytes) -> str:
        """
        Encode bytes to base64 string.

        Args:
            data: Bytes to encode

        Returns:
            Base64-encoded string
        """
        return base64.b64encode(data).decode("utf-8")

    @staticmethod
    def decode_base64(data: str) -> bytes:
        """
        Decode base64 string to bytes.

        Args:
            data: Base64-encoded string

        Returns:
            Decoded bytes
        """
        return base64.b64decode(data)

    @staticmethod
    def resample(
        audio_data: bytes,
        from_rate: int,
        to_rate: int,
    ) -> bytes:
        """
        Simple linear resampling of audio data.

        Note: For production use, consider using a proper resampling
        library like scipy or librosa for better quality.

        Args:
            audio_data: Input audio (16-bit PCM)
            from_rate: Original sample rate
            to_rate: Target sample rate

        Returns:
            Resampled audio data
        """
        if from_rate == to_rate:
            return audio_data

        # Convert bytes to samples
        samples = []
        for i in range(0, len(audio_data), 2):
            sample = struct.unpack("<h", audio_data[i:i+2])[0]
            samples.append(sample)

        # Calculate resampling ratio
        ratio = to_rate / from_rate
        new_length = int(len(samples) * ratio)

        # Linear interpolation
        resampled = []
        for i in range(new_length):
            src_idx = i / ratio
            idx_floor = int(src_idx)
            idx_ceil = min(idx_floor + 1, len(samples) - 1)
            frac = src_idx - idx_floor

            sample = int(
                samples[idx_floor] * (1 - frac) + samples[idx_ceil] * frac
            )
            resampled.append(sample)

        # Convert back to bytes
        return struct.pack("<" + "h" * len(resampled), *resampled)

    @staticmethod
    def calculate_energy(audio_data: bytes) -> float:
        """
        Calculate audio energy (RMS).

        Args:
            audio_data: Audio bytes (16-bit PCM)

        Returns:
            RMS energy value (0.0 to 1.0)
        """
        if len(audio_data) < 2:
            return 0.0

        # Convert to samples
        samples = []
        for i in range(0, len(audio_data), 2):
            sample = struct.unpack("<h", audio_data[i:i+2])[0]
            samples.append(sample)

        if not samples:
            return 0.0

        # Calculate RMS
        sum_squares = sum(s * s for s in samples)
        rms = (sum_squares / len(samples)) ** 0.5

        # Normalize to 0-1 range
        return min(1.0, rms / 32768.0)

    @staticmethod
    def is_silent(
        audio_data: bytes,
        threshold: float = 0.01,
    ) -> bool:
        """
        Check if audio is silent.

        Args:
            audio_data: Audio bytes
            threshold: Energy threshold (0.0 to 1.0)

        Returns:
            True if audio is below threshold
        """
        energy = AudioProcessor.calculate_energy(audio_data)
        return energy < threshold

    @staticmethod
    def split_into_chunks(
        audio_data: bytes,
        chunk_size: int = 960,  # 20ms at 24kHz
    ) -> List[bytes]:
        """
        Split audio into fixed-size chunks.

        Args:
            audio_data: Audio bytes
            chunk_size: Samples per chunk

        Returns:
            List of audio chunks
        """
        bytes_per_chunk = chunk_size * 2  # 16-bit audio
        chunks = []

        for i in range(0, len(audio_data), bytes_per_chunk):
            chunk = audio_data[i:i + bytes_per_chunk]
            if len(chunk) == bytes_per_chunk:
                chunks.append(chunk)

        return chunks

    @staticmethod
    async def collect_audio_stream(
        stream: AsyncGenerator[bytes, None],
        max_duration_ms: int = 30000,
        sample_rate: int = 16000,
    ) -> bytes:
        """
        Collect audio from an async stream.

        Args:
            stream: Async generator of audio chunks
            max_duration_ms: Maximum duration to collect
            sample_rate: Sample rate for duration calculation

        Returns:
            Collected audio data
        """
        buffer = AudioBuffer(sample_rate=sample_rate)
        max_bytes = int(max_duration_ms * sample_rate * 2 / 1000)

        async for chunk in stream:
            buffer.add(chunk)
            if buffer.size >= max_bytes:
                logger.warning("Audio collection reached max duration")
                break

        return buffer.drain()
