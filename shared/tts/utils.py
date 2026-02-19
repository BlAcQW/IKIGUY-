"""
TTS Utilities
Audio processing and utility functions.
"""

import io
import wave
import struct
import base64
import logging
from typing import Optional, Tuple, Union, BinaryIO
from pathlib import Path
import numpy as np

from .models import AudioFormat
from .exceptions import AudioProcessingError

logger = logging.getLogger(__name__)


class AudioUtils:
    """Audio processing utilities."""

    @staticmethod
    def convert_format(
        audio_data: bytes,
        input_format: AudioFormat,
        output_format: AudioFormat,
        sample_rate: int = 22050
    ) -> bytes:
        """Convert audio between formats.

        Args:
            audio_data: Input audio data
            input_format: Input format
            output_format: Output format
            sample_rate: Sample rate

        Returns:
            Converted audio data

        Raises:
            AudioProcessingError: If conversion fails
        """
        if input_format == output_format:
            return audio_data

        try:
            # Convert to numpy array first
            audio_array = AudioUtils.bytes_to_numpy(
                audio_data,
                input_format,
                sample_rate
            )

            # Convert to target format
            return AudioUtils.numpy_to_bytes(
                audio_array,
                output_format,
                sample_rate
            )
        except Exception as e:
            raise AudioProcessingError(f"Format conversion failed: {e}")

    @staticmethod
    def bytes_to_numpy(
        audio_data: bytes,
        format: AudioFormat,
        sample_rate: int = 22050
    ) -> np.ndarray:
        """Convert audio bytes to numpy array.

        Args:
            audio_data: Audio data
            format: Audio format
            sample_rate: Sample rate

        Returns:
            Numpy array of audio samples

        Raises:
            AudioProcessingError: If conversion fails
        """
        try:
            if format == AudioFormat.WAV:
                # Read WAV data
                with io.BytesIO(audio_data) as wav_io:
                    with wave.open(wav_io, 'rb') as wav:
                        frames = wav.readframes(wav.getnframes())
                        dtype = np.int16 if wav.getsampwidth() == 2 else np.int32
                        audio_array = np.frombuffer(frames, dtype=dtype)
                        # Normalize to float32 [-1, 1]
                        audio_array = audio_array.astype(np.float32) / np.iinfo(dtype).max
                        return audio_array

            elif format == AudioFormat.PCM:
                # Assume 16-bit PCM
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                return audio_array.astype(np.float32) / 32768.0

            else:
                raise AudioProcessingError(f"Unsupported format for numpy conversion: {format}")

        except Exception as e:
            raise AudioProcessingError(f"Failed to convert to numpy: {e}")

    @staticmethod
    def numpy_to_bytes(
        audio_array: np.ndarray,
        format: AudioFormat,
        sample_rate: int = 22050
    ) -> bytes:
        """Convert numpy array to audio bytes.

        Args:
            audio_array: Audio samples
            format: Target audio format
            sample_rate: Sample rate

        Returns:
            Audio bytes

        Raises:
            AudioProcessingError: If conversion fails
        """
        try:
            # Ensure float32 normalized audio
            if audio_array.dtype != np.float32:
                audio_array = audio_array.astype(np.float32)

            # Clip to [-1, 1]
            audio_array = np.clip(audio_array, -1.0, 1.0)

            if format == AudioFormat.WAV:
                # Convert to 16-bit PCM for WAV
                pcm_data = (audio_array * 32767).astype(np.int16)

                # Create WAV file in memory
                wav_io = io.BytesIO()
                with wave.open(wav_io, 'wb') as wav:
                    wav.setnchannels(1)  # Mono
                    wav.setsampwidth(2)  # 16-bit
                    wav.setframerate(sample_rate)
                    wav.writeframes(pcm_data.tobytes())

                return wav_io.getvalue()

            elif format == AudioFormat.PCM:
                # Convert to 16-bit PCM
                pcm_data = (audio_array * 32767).astype(np.int16)
                return pcm_data.tobytes()

            else:
                raise AudioProcessingError(f"Unsupported format for bytes conversion: {format}")

        except Exception as e:
            raise AudioProcessingError(f"Failed to convert to bytes: {e}")

    @staticmethod
    def save_audio(
        audio_data: bytes,
        file_path: Union[str, Path],
        format: Optional[AudioFormat] = None,
        sample_rate: int = 22050
    ) -> Path:
        """Save audio data to file.

        Args:
            audio_data: Audio data
            file_path: Output file path
            format: Audio format (inferred from extension if not provided)
            sample_rate: Sample rate

        Returns:
            Path to saved file

        Raises:
            AudioProcessingError: If save fails
        """
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Infer format from extension if not provided
            if format is None:
                ext = file_path.suffix.lower().lstrip('.')
                format = AudioFormat(ext) if ext in AudioFormat.__members__ else AudioFormat.WAV

            # Ensure correct extension
            if not file_path.suffix:
                file_path = file_path.with_suffix(f'.{format.value}')

            # Write file
            with open(file_path, 'wb') as f:
                f.write(audio_data)

            logger.info(f"Saved audio to {file_path}")
            return file_path

        except Exception as e:
            raise AudioProcessingError(f"Failed to save audio: {e}")

    @staticmethod
    def load_audio(
        file_path: Union[str, Path],
        format: Optional[AudioFormat] = None
    ) -> Tuple[bytes, AudioFormat]:
        """Load audio from file.

        Args:
            file_path: Input file path
            format: Audio format (inferred from extension if not provided)

        Returns:
            Tuple of (audio data, format)

        Raises:
            AudioProcessingError: If load fails
        """
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                raise AudioProcessingError(f"File not found: {file_path}")

            # Infer format from extension if not provided
            if format is None:
                ext = file_path.suffix.lower().lstrip('.')
                format = AudioFormat(ext) if ext in AudioFormat.__members__ else AudioFormat.WAV

            # Read file
            with open(file_path, 'rb') as f:
                audio_data = f.read()

            return audio_data, format

        except Exception as e:
            raise AudioProcessingError(f"Failed to load audio: {e}")

    @staticmethod
    def get_audio_duration(
        audio_data: bytes,
        format: AudioFormat,
        sample_rate: int = 22050
    ) -> float:
        """Get duration of audio in seconds.

        Args:
            audio_data: Audio data
            format: Audio format
            sample_rate: Sample rate

        Returns:
            Duration in seconds

        Raises:
            AudioProcessingError: If duration calculation fails
        """
        try:
            if format == AudioFormat.WAV:
                with io.BytesIO(audio_data) as wav_io:
                    with wave.open(wav_io, 'rb') as wav:
                        frames = wav.getnframes()
                        rate = wav.getframerate()
                        return frames / rate

            elif format == AudioFormat.PCM:
                # Assume 16-bit PCM
                num_samples = len(audio_data) // 2  # 2 bytes per sample
                return num_samples / sample_rate

            else:
                # Convert to numpy and calculate
                audio_array = AudioUtils.bytes_to_numpy(audio_data, format, sample_rate)
                return len(audio_array) / sample_rate

        except Exception as e:
            logger.warning(f"Failed to calculate duration: {e}")
            return 0.0

    @staticmethod
    def encode_base64(audio_data: bytes) -> str:
        """Encode audio data to base64 string.

        Args:
            audio_data: Audio data

        Returns:
            Base64 encoded string
        """
        return base64.b64encode(audio_data).decode('utf-8')

    @staticmethod
    def decode_base64(audio_base64: str) -> bytes:
        """Decode base64 string to audio data.

        Args:
            audio_base64: Base64 encoded audio

        Returns:
            Audio data
        """
        return base64.b64decode(audio_base64)

    @staticmethod
    def resample(
        audio_data: bytes,
        format: AudioFormat,
        input_rate: int,
        output_rate: int
    ) -> bytes:
        """Resample audio to different sample rate.

        Args:
            audio_data: Audio data
            format: Audio format
            input_rate: Input sample rate
            output_rate: Output sample rate

        Returns:
            Resampled audio data

        Raises:
            AudioProcessingError: If resampling fails
        """
        if input_rate == output_rate:
            return audio_data

        try:
            # Convert to numpy
            audio_array = AudioUtils.bytes_to_numpy(audio_data, format, input_rate)

            # Simple resampling (for better quality, use scipy.signal.resample)
            ratio = output_rate / input_rate
            new_length = int(len(audio_array) * ratio)
            x_old = np.linspace(0, len(audio_array), len(audio_array))
            x_new = np.linspace(0, len(audio_array), new_length)
            resampled = np.interp(x_new, x_old, audio_array)

            # Convert back to bytes
            return AudioUtils.numpy_to_bytes(resampled, format, output_rate)

        except Exception as e:
            raise AudioProcessingError(f"Resampling failed: {e}")

    @staticmethod
    def normalize_audio(
        audio_data: bytes,
        format: AudioFormat,
        sample_rate: int = 22050,
        target_db: float = -20.0
    ) -> bytes:
        """Normalize audio volume.

        Args:
            audio_data: Audio data
            format: Audio format
            sample_rate: Sample rate
            target_db: Target volume in dB

        Returns:
            Normalized audio data

        Raises:
            AudioProcessingError: If normalization fails
        """
        try:
            # Convert to numpy
            audio_array = AudioUtils.bytes_to_numpy(audio_data, format, sample_rate)

            # Calculate current RMS
            rms = np.sqrt(np.mean(audio_array**2))
            if rms == 0:
                return audio_data

            # Calculate target RMS from dB
            target_rms = 10**(target_db / 20)

            # Apply gain
            gain = target_rms / rms
            normalized = audio_array * gain

            # Clip to prevent clipping
            normalized = np.clip(normalized, -1.0, 1.0)

            # Convert back to bytes
            return AudioUtils.numpy_to_bytes(normalized, format, sample_rate)

        except Exception as e:
            raise AudioProcessingError(f"Normalization failed: {e}")


class AudioStreamer:
    """Audio streaming utilities for real-time processing."""

    def __init__(self, chunk_size: int = 1024, sample_rate: int = 22050):
        """Initialize audio streamer.

        Args:
            chunk_size: Size of audio chunks in samples
            sample_rate: Sample rate
        """
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.buffer = io.BytesIO()

    def add_chunk(self, audio_chunk: bytes):
        """Add audio chunk to buffer.

        Args:
            audio_chunk: Audio chunk to add
        """
        self.buffer.write(audio_chunk)

    def get_chunks(self, format: AudioFormat = AudioFormat.PCM) -> bytes:
        """Get buffered audio chunks.

        Args:
            format: Audio format

        Returns:
            Buffered audio data
        """
        data = self.buffer.getvalue()
        self.buffer = io.BytesIO()
        return data

    def clear(self):
        """Clear the buffer."""
        self.buffer = io.BytesIO()