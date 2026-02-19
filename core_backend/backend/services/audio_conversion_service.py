"""
Audio Conversion Service

Converts audio files between different formats (WAV, MP3, OGG, FLAC, M4A).
Uses pydub with ffmpeg backend for high-quality conversions.

Created: 2025-10-27
Sprint 4: Advanced Features (Phase 9)
"""

import os
import tempfile
import base64
from typing import Literal
from pydub import AudioSegment
import io

AudioFormat = Literal["wav", "mp3", "ogg", "flac", "m4a"]


class AudioConversionService:
    """Service for converting audio between different formats"""

    # Format configurations (bitrate, codec settings)
    FORMAT_CONFIGS = {
        "mp3": {
            "bitrate": "192k",  # High quality MP3
            "codec": "libmp3lame",
        },
        "ogg": {
            "bitrate": "192k",  # High quality OGG
            "codec": "libvorbis",
        },
        "flac": {
            "codec": "flac",  # Lossless
        },
        "m4a": {
            "bitrate": "192k",
            "codec": "aac",
        },
        "wav": {
            "codec": "pcm_s16le",  # 16-bit PCM
        },
    }

    def __init__(self):
        """Initialize audio conversion service"""
        pass

    def convert_audio(
        self,
        audio_data: bytes,
        source_format: AudioFormat,
        target_format: AudioFormat,
        bitrate: str = "192k",
    ) -> bytes:
        """
        Convert audio from one format to another.

        Args:
            audio_data: Audio data in bytes
            source_format: Source audio format
            target_format: Target audio format
            bitrate: Target bitrate (e.g., "128k", "192k", "320k")

        Returns:
            Converted audio data in bytes
        """
        try:
            # Load audio from bytes
            audio = AudioSegment.from_file(
                io.BytesIO(audio_data), format=source_format
            )

            # Prepare export parameters
            export_params = {}

            if target_format == "mp3":
                export_params = {
                    "format": "mp3",
                    "bitrate": bitrate,
                    "parameters": ["-codec:a", "libmp3lame"],
                }
            elif target_format == "ogg":
                export_params = {
                    "format": "ogg",
                    "codec": "libvorbis",
                    "bitrate": bitrate,
                }
            elif target_format == "flac":
                export_params = {
                    "format": "flac",
                }
            elif target_format == "m4a":
                export_params = {
                    "format": "ipod",  # M4A format in ffmpeg
                    "codec": "aac",
                    "bitrate": bitrate,
                }
            elif target_format == "wav":
                export_params = {
                    "format": "wav",
                }

            # Export to bytes
            output_buffer = io.BytesIO()
            audio.export(output_buffer, **export_params)
            output_buffer.seek(0)

            return output_buffer.read()

        except Exception as e:
            raise ValueError(f"Failed to convert audio: {str(e)}")

    def convert_base64_audio(
        self,
        audio_base64: str,
        source_format: AudioFormat,
        target_format: AudioFormat,
        bitrate: str = "192k",
    ) -> str:
        """
        Convert base64-encoded audio from one format to another.

        Args:
            audio_base64: Base64-encoded audio data
            source_format: Source audio format
            target_format: Target audio format
            bitrate: Target bitrate

        Returns:
            Base64-encoded converted audio
        """
        # Decode base64
        audio_data = base64.b64decode(audio_base64)

        # Convert
        converted_data = self.convert_audio(
            audio_data, source_format, target_format, bitrate
        )

        # Encode to base64
        return base64.b64encode(converted_data).decode("utf-8")

    def get_audio_info(self, audio_data: bytes, audio_format: AudioFormat) -> dict:
        """
        Get audio file information.

        Args:
            audio_data: Audio data in bytes
            audio_format: Audio format

        Returns:
            Dictionary with audio info (duration, channels, sample_rate, etc.)
        """
        try:
            audio = AudioSegment.from_file(
                io.BytesIO(audio_data), format=audio_format
            )

            return {
                "duration_seconds": len(audio) / 1000.0,
                "channels": audio.channels,
                "sample_rate": audio.frame_rate,
                "sample_width": audio.sample_width,
                "frame_count": audio.frame_count(),
                "size_bytes": len(audio_data),
            }
        except Exception as e:
            raise ValueError(f"Failed to get audio info: {str(e)}")

    def batch_convert(
        self,
        audio_data: bytes,
        source_format: AudioFormat,
        target_formats: list[AudioFormat],
        bitrate: str = "192k",
    ) -> dict[AudioFormat, bytes]:
        """
        Convert audio to multiple formats at once.

        Args:
            audio_data: Source audio data
            source_format: Source format
            target_formats: List of target formats
            bitrate: Target bitrate

        Returns:
            Dictionary mapping format to converted audio bytes
        """
        results = {}

        # Load audio once
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format=source_format)

        for target_format in target_formats:
            try:
                # Prepare export parameters
                export_params = {}

                if target_format == "mp3":
                    export_params = {
                        "format": "mp3",
                        "bitrate": bitrate,
                        "parameters": ["-codec:a", "libmp3lame"],
                    }
                elif target_format == "ogg":
                    export_params = {
                        "format": "ogg",
                        "codec": "libvorbis",
                        "bitrate": bitrate,
                    }
                elif target_format == "flac":
                    export_params = {
                        "format": "flac",
                    }
                elif target_format == "m4a":
                    export_params = {
                        "format": "ipod",
                        "codec": "aac",
                        "bitrate": bitrate,
                    }
                elif target_format == "wav":
                    export_params = {
                        "format": "wav",
                    }

                # Export to bytes
                output_buffer = io.BytesIO()
                audio.export(output_buffer, **export_params)
                output_buffer.seek(0)

                results[target_format] = output_buffer.read()

            except Exception as e:
                print(f"Failed to convert to {target_format}: {e}")
                results[target_format] = None

        return results
