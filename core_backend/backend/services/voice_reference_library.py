"""
Voice Reference Library Service
Manages reference audio samples for voice cloning
"""

import base64
import io
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import wave
import numpy as np

logger = logging.getLogger(__name__)


class AudioValidator:
    """Validates reference audio for voice cloning"""

    # Validation constants
    MIN_DURATION = 3.0  # seconds
    MAX_DURATION = 10.0  # seconds
    OPTIMAL_MIN_DURATION = 3.0
    OPTIMAL_MAX_DURATION = 6.0
    MIN_SAMPLE_RATE = 16000
    RECOMMENDED_SAMPLE_RATE = 22050
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    @staticmethod
    def validate_audio_bytes(audio_bytes: bytes) -> Dict[str, any]:
        """
        Validate audio data for voice cloning

        Args:
            audio_bytes: Audio data as bytes

        Returns:
            Dict with validation results and metadata
        """
        try:
            # Check file size
            if len(audio_bytes) > AudioValidator.MAX_FILE_SIZE:
                return {
                    "valid": False,
                    "error": f"File too large: {len(audio_bytes)} bytes (max: {AudioValidator.MAX_FILE_SIZE})",
                    "metadata": {}
                }

            # Try to parse as WAV
            try:
                with io.BytesIO(audio_bytes) as buffer:
                    with wave.open(buffer, 'rb') as wav:
                        channels = wav.getnchannels()
                        sample_rate = wav.getframerate()
                        frames = wav.getnframes()
                        duration = frames / sample_rate
                        sample_width = wav.getsampwidth()

                        metadata = {
                            "format": "wav",
                            "channels": channels,
                            "sample_rate": sample_rate,
                            "duration": duration,
                            "frames": frames,
                            "sample_width": sample_width
                        }

            except Exception as e:
                logger.warning(f"Not a valid WAV file: {e}")
                # Try other formats or fall back
                return {
                    "valid": False,
                    "error": f"Invalid audio format: {str(e)}",
                    "metadata": {}
                }

            # Validate duration
            if duration < AudioValidator.MIN_DURATION:
                return {
                    "valid": False,
                    "error": f"Audio too short: {duration:.1f}s (minimum: {AudioValidator.MIN_DURATION}s)",
                    "metadata": metadata
                }

            if duration > AudioValidator.MAX_DURATION:
                return {
                    "valid": False,
                    "error": f"Audio too long: {duration:.1f}s (maximum: {AudioValidator.MAX_DURATION}s)",
                    "metadata": metadata
                }

            # Validate sample rate
            if sample_rate < AudioValidator.MIN_SAMPLE_RATE:
                return {
                    "valid": False,
                    "error": f"Sample rate too low: {sample_rate}Hz (minimum: {AudioValidator.MIN_SAMPLE_RATE}Hz)",
                    "metadata": metadata
                }

            # Check for silence/low energy
            try:
                with io.BytesIO(audio_bytes) as buffer:
                    with wave.open(buffer, 'rb') as wav:
                        audio_data = wav.readframes(frames)
                        audio_array = np.frombuffer(audio_data, dtype=np.int16)

                        # Calculate RMS energy
                        rms = np.sqrt(np.mean(audio_array.astype(float) ** 2))

                        # Check if audio is too quiet (likely silence)
                        if rms < 100:  # Very low threshold
                            return {
                                "valid": False,
                                "error": f"Audio appears to be silent (RMS: {rms:.1f})",
                                "metadata": metadata
                            }

                        metadata["rms_energy"] = float(rms)
                        metadata["quality_score"] = AudioValidator._calculate_quality_score(
                            duration, sample_rate, rms
                        )

            except Exception as e:
                logger.warning(f"Could not analyze audio energy: {e}")

            # Generate warnings for non-optimal settings
            warnings = []
            if duration < AudioValidator.OPTIMAL_MIN_DURATION:
                warnings.append(f"Audio shorter than optimal ({AudioValidator.OPTIMAL_MIN_DURATION}s)")
            if duration > AudioValidator.OPTIMAL_MAX_DURATION:
                warnings.append(f"Audio longer than optimal ({AudioValidator.OPTIMAL_MAX_DURATION}s)")
            if sample_rate < AudioValidator.RECOMMENDED_SAMPLE_RATE:
                warnings.append(f"Sample rate below recommended ({AudioValidator.RECOMMENDED_SAMPLE_RATE}Hz)")
            if channels > 1:
                warnings.append("Stereo audio (mono recommended for voice cloning)")

            return {
                "valid": True,
                "metadata": metadata,
                "warnings": warnings
            }

        except Exception as e:
            logger.error(f"Audio validation error: {e}")
            return {
                "valid": False,
                "error": f"Validation failed: {str(e)}",
                "metadata": {}
            }

    @staticmethod
    def _calculate_quality_score(duration: float, sample_rate: int, rms: float) -> float:
        """Calculate quality score (0-100) for reference audio"""
        score = 50.0  # Base score

        # Duration score (optimal: 3-6 seconds)
        if AudioValidator.OPTIMAL_MIN_DURATION <= duration <= AudioValidator.OPTIMAL_MAX_DURATION:
            score += 20
        elif AudioValidator.MIN_DURATION <= duration <= AudioValidator.MAX_DURATION:
            score += 10

        # Sample rate score
        if sample_rate >= AudioValidator.RECOMMENDED_SAMPLE_RATE:
            score += 15
        elif sample_rate >= AudioValidator.MIN_SAMPLE_RATE:
            score += 10

        # Energy score (RMS between 1000-10000 is good)
        if 1000 <= rms <= 10000:
            score += 15
        elif 500 <= rms <= 15000:
            score += 10

        return min(score, 100.0)

    @staticmethod
    def validate_base64_audio(audio_base64: str) -> Dict[str, any]:
        """Validate base64 encoded audio"""
        try:
            audio_bytes = base64.b64decode(audio_base64)
            return AudioValidator.validate_audio_bytes(audio_bytes)
        except Exception as e:
            return {
                "valid": False,
                "error": f"Invalid base64: {str(e)}",
                "metadata": {}
            }


class VoiceReferenceLibrary:
    """Manages a library of reference voices for XTTS"""

    def __init__(self, library_path: Optional[Path] = None):
        """
        Initialize voice reference library

        Args:
            library_path: Path to store reference voices
        """
        self.library_path = library_path or Path("/opt/kasaai/apps/voice-lab/reference_voices")
        self.library_path.mkdir(parents=True, exist_ok=True)
        self.validator = AudioValidator()

        logger.info(f"Voice library initialized at: {self.library_path}")

    def add_reference_voice(
        self,
        voice_id: str,
        audio_bytes: bytes,
        metadata: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Add a reference voice to the library

        Args:
            voice_id: Unique identifier for the voice
            audio_bytes: Audio data as bytes
            metadata: Optional metadata (speaker info, etc.)

        Returns:
            Dict with result status and validation info
        """
        # Validate audio
        validation = self.validator.validate_audio_bytes(audio_bytes)

        if not validation["valid"]:
            return {
                "success": False,
                "error": validation.get("error"),
                "validation": validation
            }

        try:
            # Save audio file
            audio_path = self.library_path / f"{voice_id}.wav"
            audio_path.write_bytes(audio_bytes)

            # Save metadata
            meta_path = self.library_path / f"{voice_id}.json"
            meta_data = {
                "voice_id": voice_id,
                "audio_file": str(audio_path),
                "validation": validation,
                **(metadata or {})
            }

            import json
            meta_path.write_text(json.dumps(meta_data, indent=2))

            logger.info(f"Added reference voice: {voice_id}")

            return {
                "success": True,
                "voice_id": voice_id,
                "audio_path": str(audio_path),
                "validation": validation,
                "warnings": validation.get("warnings", [])
            }

        except Exception as e:
            logger.error(f"Failed to add reference voice: {e}")
            return {
                "success": False,
                "error": str(e),
                "validation": validation
            }

    def get_reference_voice(self, voice_id: str) -> Optional[bytes]:
        """Get reference voice audio bytes"""
        audio_path = self.library_path / f"{voice_id}.wav"
        if audio_path.exists():
            return audio_path.read_bytes()
        return None

    def list_reference_voices(self) -> List[Dict[str, any]]:
        """List all reference voices in library"""
        import json
        voices = []

        for meta_file in self.library_path.glob("*.json"):
            try:
                meta_data = json.loads(meta_file.read_text())
                voices.append(meta_data)
            except Exception as e:
                logger.warning(f"Failed to read metadata: {meta_file}: {e}")

        return voices

    def delete_reference_voice(self, voice_id: str) -> bool:
        """Delete a reference voice from library"""
        try:
            audio_path = self.library_path / f"{voice_id}.wav"
            meta_path = self.library_path / f"{voice_id}.json"

            if audio_path.exists():
                audio_path.unlink()
            if meta_path.exists():
                meta_path.unlink()

            logger.info(f"Deleted reference voice: {voice_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete reference voice: {e}")
            return False


# Singleton instance
_voice_library = None


def get_voice_reference_library() -> VoiceReferenceLibrary:
    """Get or create voice reference library instance"""
    global _voice_library

    if _voice_library is None:
        _voice_library = VoiceReferenceLibrary()

    return _voice_library
