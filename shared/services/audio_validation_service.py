"""
Audio Validation Service

Validates audio files for ASR/TTS processing with security checks.
Prevents abuse and ensures audio quality standards.

Centralized service for use across all apps (InkWave, Core Backend, etc.)

Created: 2025-10-27
Phase 1: Error Handling & Security
"""

import base64
import io
import logging
import mimetypes
from typing import Tuple, Optional, Dict
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration Constants
# ============================================================================

# Maximum audio duration by tier (in seconds)
MAX_DURATION_BY_TIER = {
    "free": 300,  # 5 minutes
    "starter": 900,  # 15 minutes
    "pro": 3600,  # 1 hour
    "enterprise": 7200,  # 2 hours
}

# Maximum file size (in MB)
MAX_FILE_SIZE_MB = 100  # 100 MB

# Supported audio formats
SUPPORTED_FORMATS = ["wav", "mp3", "ogg", "flac", "m4a", "webm", "aac"]

# Suspicious file patterns (potential malicious files)
SUSPICIOUS_PATTERNS = [
    b"<?xml",  # XML files
    b"<!DOCTYPE",  # HTML files
    b"<html",  # HTML files
    b"<script",  # Scripts
    b"#!/",  # Shell scripts
    b"MZ",  # Windows executables
    b"\x7fELF",  # Linux executables
]


# ============================================================================
# Custom Exceptions (Basic - apps should catch and convert to their own errors)
# ============================================================================

class AudioValidationError(Exception):
    """Base exception for audio validation errors."""
    pass


class AudioTooLongError(AudioValidationError):
    """Audio exceeds maximum duration."""
    def __init__(self, duration: float, max_duration: float, tier: str = "free"):
        self.duration = duration
        self.max_duration = max_duration
        self.tier = tier
        super().__init__(
            f"Audio is too long ({duration:.1f}s). Maximum for {tier} tier: {max_duration:.1f}s"
        )


class AudioTooLargeError(AudioValidationError):
    """Audio file exceeds maximum size."""
    def __init__(self, size_mb: float, max_size_mb: float):
        self.size_mb = size_mb
        self.max_size_mb = max_size_mb
        super().__init__(
            f"Audio file is too large ({size_mb:.1f} MB). Maximum: {max_size_mb:.1f} MB"
        )


class InvalidAudioFormatError(AudioValidationError):
    """Invalid or unsupported audio format."""
    def __init__(self, format: str, supported_formats: list):
        self.format = format
        self.supported_formats = supported_formats
        super().__init__(
            f"Audio format '{format}' is not supported. "
            f"Supported: {', '.join(supported_formats)}"
        )


class AudioProcessingError(AudioValidationError):
    """Error processing audio file."""
    pass


class MaliciousFileError(AudioValidationError):
    """Potentially malicious file detected."""
    pass


# ============================================================================
# Format Detection
# ============================================================================

def detect_audio_format(audio_data: bytes) -> str:
    """
    Detect audio format from file header (magic bytes).

    Args:
        audio_data: Raw audio bytes

    Returns:
        str: Detected format (wav, mp3, ogg, flac, etc.)

    Raises:
        InvalidAudioFormatError: If format cannot be detected or is unsupported
    """
    if len(audio_data) < 12:
        raise InvalidAudioFormatError(
            format="unknown", supported_formats=SUPPORTED_FORMATS
        )

    # Check magic bytes for common formats
    header = audio_data[:12]

    # WAV (RIFF header)
    if header[:4] == b"RIFF" and header[8:12] == b"WAVE":
        return "wav"

    # MP3 (ID3 tag or MPEG sync)
    if header[:3] == b"ID3" or (header[0:2] == b"\xff\xfb") or (header[0:2] == b"\xff\xf3"):
        return "mp3"

    # OGG (OggS header)
    if header[:4] == b"OggS":
        return "ogg"

    # FLAC (fLaC header)
    if header[:4] == b"fLaC":
        return "flac"

    # M4A/MP4 (ftyp box)
    if header[4:8] == b"ftyp":
        return "m4a"

    # WebM (EBML header with WebM doctype)
    if header[:4] == b"\x1a\x45\xdf\xa3":
        return "webm"

    # AAC (ADTS header)
    if header[:2] == b"\xff\xf1" or header[:2] == b"\xff\xf9":
        return "aac"

    raise InvalidAudioFormatError(
        format="unknown", supported_formats=SUPPORTED_FORMATS
    )


# ============================================================================
# Security Checks
# ============================================================================

def check_malicious_patterns(audio_data: bytes) -> None:
    """
    Check for suspicious patterns that might indicate malicious files.

    Args:
        audio_data: Raw audio bytes

    Raises:
        MaliciousFileError: If suspicious patterns are detected
    """
    # Check first 1KB for suspicious patterns
    sample = audio_data[:1024]

    for pattern in SUSPICIOUS_PATTERNS:
        if pattern in sample:
            raise MaliciousFileError(
                f"Suspicious file pattern detected: {pattern.decode('utf-8', errors='ignore')[:20]}"
            )

    # Check for null bytes in excessive amounts (potential binary exploit)
    null_count = sample.count(b"\x00")
    if null_count > len(sample) * 0.9:  # More than 90% null bytes
        raise MaliciousFileError("Excessive null bytes detected - potential exploit")

    logger.debug("Audio file passed malicious pattern check")


# ============================================================================
# Audio Metadata Extraction
# ============================================================================

def get_audio_info(audio_data: bytes, audio_format: str) -> Dict:
    """
    Get detailed audio file information using pydub.

    Args:
        audio_data: Raw audio bytes
        audio_format: Audio format (wav, mp3, etc.)

    Returns:
        dict: Audio metadata (duration, channels, sample_rate, etc.)

    Raises:
        AudioProcessingError: If audio cannot be processed
    """
    try:
        # Load audio with pydub
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format=audio_format)

        return {
            "duration_seconds": len(audio) / 1000.0,
            "channels": audio.channels,
            "sample_rate": audio.frame_rate,
            "sample_width": audio.sample_width,
            "frame_count": audio.frame_count(),
            "size_bytes": len(audio_data),
            "size_mb": len(audio_data) / (1024 * 1024),
            "format": audio_format,
        }

    except CouldntDecodeError as e:
        logger.error(f"Failed to decode audio: {e}")
        raise AudioProcessingError(f"Could not decode audio file: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting audio info: {e}")
        raise AudioProcessingError(f"Failed to process audio: {str(e)}")


# ============================================================================
# Validation Functions
# ============================================================================

def validate_audio_duration(duration_seconds: float, tier: str = "free") -> None:
    """
    Validate audio duration against tier limits.

    Args:
        duration_seconds: Audio duration in seconds
        tier: User's pricing tier

    Raises:
        AudioTooLongError: If duration exceeds tier limit
    """
    max_duration = MAX_DURATION_BY_TIER.get(tier, MAX_DURATION_BY_TIER["free"])

    if duration_seconds > max_duration:
        raise AudioTooLongError(
            duration=duration_seconds, max_duration=max_duration, tier=tier
        )

    logger.debug(f"Audio duration {duration_seconds:.2f}s is within {tier} tier limit")


def validate_audio_size(size_bytes: int) -> None:
    """
    Validate audio file size.

    Args:
        size_bytes: File size in bytes

    Raises:
        AudioTooLargeError: If file size exceeds maximum
    """
    size_mb = size_bytes / (1024 * 1024)

    if size_mb > MAX_FILE_SIZE_MB:
        raise AudioTooLargeError(size_mb=size_mb, max_size_mb=MAX_FILE_SIZE_MB)

    logger.debug(f"Audio file size {size_mb:.2f}MB is within limit")


def validate_audio_format(audio_format: str) -> None:
    """
    Validate audio format is supported.

    Args:
        audio_format: Audio format string

    Raises:
        InvalidAudioFormatError: If format is not supported
    """
    if audio_format.lower() not in SUPPORTED_FORMATS:
        raise InvalidAudioFormatError(
            format=audio_format, supported_formats=SUPPORTED_FORMATS
        )

    logger.debug(f"Audio format '{audio_format}' is supported")


# ============================================================================
# Main Validation Service
# ============================================================================

class AudioValidationService:
    """
    Centralized audio validation service.

    Provides comprehensive audio file validation including:
    - File size checks
    - Malicious pattern detection
    - Format detection and validation
    - Audio metadata extraction
    - Duration validation by tier
    """

    def __init__(self):
        """Initialize audio validation service."""
        self.supported_formats = SUPPORTED_FORMATS
        self.max_file_size_mb = MAX_FILE_SIZE_MB
        self.max_duration_by_tier = MAX_DURATION_BY_TIER

    def validate_audio_file(
        self,
        audio_data: bytes,
        tier: str = "free",
        detect_format: bool = True,
        check_security: bool = True,
    ) -> Dict:
        """
        Comprehensive audio file validation.

        Performs all validation checks:
        1. File size check
        2. Malicious pattern detection
        3. Format detection
        4. Audio metadata extraction
        5. Duration validation

        Args:
            audio_data: Raw audio bytes
            tier: User's pricing tier
            detect_format: Whether to detect format from magic bytes
            check_security: Whether to run security checks

        Returns:
            dict: Audio metadata including duration, format, size, etc.

        Raises:
            AudioTooLargeError: If file exceeds size limit
            MaliciousFileError: If suspicious patterns detected
            InvalidAudioFormatError: If format unsupported
            AudioTooLongError: If duration exceeds tier limit
            AudioProcessingError: If audio cannot be processed
        """
        # Step 1: Validate file size (quick check first)
        validate_audio_size(len(audio_data))

        # Step 2: Security checks
        if check_security:
            check_malicious_patterns(audio_data)

        # Step 3: Detect audio format
        if detect_format:
            audio_format = detect_audio_format(audio_data)
        else:
            # If not detecting, assume WAV (safest default)
            audio_format = "wav"

        # Step 4: Validate format is supported
        validate_audio_format(audio_format)

        # Step 5: Get audio metadata
        audio_info = get_audio_info(audio_data, audio_format)

        # Step 6: Validate duration
        validate_audio_duration(audio_info["duration_seconds"], tier=tier)

        logger.info(
            f"Audio validation passed: format={audio_format}, "
            f"duration={audio_info['duration_seconds']:.2f}s, "
            f"size={audio_info['size_mb']:.2f}MB, tier={tier}"
        )

        return audio_info

    def validate_audio_base64(
        self,
        audio_base64: str,
        tier: str = "free",
        detect_format: bool = True,
        check_security: bool = True,
    ) -> Tuple[bytes, Dict]:
        """
        Validate base64-encoded audio file.

        Args:
            audio_base64: Base64-encoded audio data
            tier: User's pricing tier
            detect_format: Whether to detect format from magic bytes
            check_security: Whether to run security checks

        Returns:
            Tuple[bytes, dict]: Decoded audio bytes and metadata

        Raises:
            AudioProcessingError: If base64 decoding fails
            Other validation errors from validate_audio_file()
        """
        try:
            # Decode base64
            audio_data = base64.b64decode(audio_base64)
        except Exception as e:
            logger.error(f"Failed to decode base64 audio: {e}")
            raise AudioProcessingError(f"Invalid base64 encoding: {str(e)}")

        # Validate audio file
        audio_info = self.validate_audio_file(
            audio_data=audio_data,
            tier=tier,
            detect_format=detect_format,
            check_security=check_security,
        )

        return audio_data, audio_info

    def get_tier_limits(self, tier: str = "free") -> Dict:
        """
        Get validation limits for a specific tier.

        Args:
            tier: User's pricing tier

        Returns:
            dict: Tier limits including max duration, max size, etc.
        """
        return {
            "tier": tier,
            "max_duration_seconds": self.max_duration_by_tier.get(
                tier, self.max_duration_by_tier["free"]
            ),
            "max_file_size_mb": self.max_file_size_mb,
            "supported_formats": self.supported_formats,
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_audio_validation_service = None


def get_audio_validation_service() -> AudioValidationService:
    """
    Get singleton instance of AudioValidationService.

    Returns:
        AudioValidationService: Singleton service instance
    """
    global _audio_validation_service
    if _audio_validation_service is None:
        _audio_validation_service = AudioValidationService()
    return _audio_validation_service
