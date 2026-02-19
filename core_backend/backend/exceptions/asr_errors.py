"""
ASR-specific error classes for better error handling and user feedback.

Provides detailed, user-friendly error messages for common ASR failures.
Follows the same pattern as tts_errors.py for consistency.

Created: 2025-10-27
Phase 1: Error Handling & Security
"""

from typing import Optional


class ASRError(Exception):
    """
    Base exception for ASR errors.

    All ASR-specific errors inherit from this class.
    """

    def __init__(self, message: str, status_code: int = 500, details: Optional[dict] = None):
        """
        Initialize ASR error.

        Args:
            message: User-friendly error message
            status_code: HTTP status code
            details: Optional additional error details
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert error to dictionary for JSON response."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class InsufficientBalanceError(ASRError):
    """User has insufficient balance for transcription."""

    def __init__(self, required: float, available: float):
        """
        Initialize insufficient balance error.

        Args:
            required: Required amount in USD
            available: Available balance in USD
        """
        message = (
            f"Insufficient balance for transcription. "
            f"Required: ${required:.4f}, Available: ${available:.4f}. "
            f"Please add ${(required - available):.4f} to your wallet."
        )
        details = {
            "required_usd": round(required, 4),
            "available_usd": round(available, 4),
            "shortage_usd": round(required - available, 4),
        }
        super().__init__(message, status_code=402, details=details)


class ProviderOfflineError(ASRError):
    """ASR provider is offline or unreachable."""

    def __init__(self, provider_id: str, error_message: Optional[str] = None):
        """
        Initialize provider offline error.

        Args:
            provider_id: ID of offline provider
            error_message: Optional error message from health check
        """
        message = (
            f"ASR provider '{provider_id}' is currently offline or unreachable. "
            f"Please try another provider or wait a few minutes."
        )
        if error_message:
            message += f" Error: {error_message}"

        details = {"provider_id": provider_id, "error": error_message}
        super().__init__(message, status_code=503, details=details)


class AudioTooLongError(ASRError):
    """Audio file exceeds maximum duration."""

    def __init__(self, duration: float, max_duration: float, tier: str = "free"):
        """
        Initialize audio too long error.

        Args:
            duration: Actual audio duration in seconds
            max_duration: Maximum allowed duration in seconds
            tier: User's pricing tier
        """
        message = (
            f"Audio is too long ({duration:.1f}s). "
            f"Maximum duration for {tier} tier: {max_duration:.1f}s. "
        )

        if tier == "free":
            message += "Upgrade to Pro for longer transcriptions (up to 1 hour)."

        details = {
            "duration_seconds": round(duration, 2),
            "max_duration_seconds": round(max_duration, 2),
            "tier": tier,
            "exceeded_by_seconds": round(duration - max_duration, 2),
        }
        super().__init__(message, status_code=413, details=details)


class AudioTooLargeError(ASRError):
    """Audio file exceeds maximum size."""

    def __init__(self, size_mb: float, max_size_mb: float):
        """
        Initialize audio too large error.

        Args:
            size_mb: Actual file size in MB
            max_size_mb: Maximum allowed size in MB
        """
        message = (
            f"Audio file is too large ({size_mb:.1f} MB). "
            f"Maximum allowed: {max_size_mb:.1f} MB. "
            f"Please compress your audio or split it into smaller files."
        )
        details = {
            "size_mb": round(size_mb, 2),
            "max_size_mb": round(max_size_mb, 2),
        }
        super().__init__(message, status_code=413, details=details)


class InvalidProviderError(ASRError):
    """Invalid or unsupported provider."""

    def __init__(self, provider_id: str, available_providers: Optional[list] = None):
        """
        Initialize invalid provider error.

        Args:
            provider_id: Invalid provider ID
            available_providers: Optional list of available providers
        """
        message = f"Invalid ASR provider: '{provider_id}'."

        if available_providers:
            message += f" Available providers: {', '.join(available_providers)}"

        details = {
            "invalid_provider": provider_id,
            "available_providers": available_providers or [],
        }
        super().__init__(message, status_code=404, details=details)


class InvalidLanguageError(ASRError):
    """Unsupported language for provider."""

    def __init__(
        self, language: str, provider_id: str, supported_languages: Optional[list] = None
    ):
        """
        Initialize invalid language error.

        Args:
            language: Unsupported language code
            provider_id: Provider ID
            supported_languages: Optional list of supported languages
        """
        message = f"Language '{language}' is not supported by provider '{provider_id}'."

        if supported_languages:
            message += f" Supported languages: {', '.join(supported_languages[:10])}"
            if len(supported_languages) > 10:
                message += f" (and {len(supported_languages) - 10} more)"

        details = {
            "language": language,
            "provider_id": provider_id,
            "supported_languages": supported_languages or [],
        }
        super().__init__(message, status_code=400, details=details)


class AudioProcessingError(ASRError):
    """Error processing audio file."""

    def __init__(self, detail: str, audio_info: Optional[dict] = None):
        """
        Initialize audio processing error.

        Args:
            detail: Detailed error message
            audio_info: Optional audio file metadata
        """
        message = f"Audio processing failed: {detail}"
        details = {"error": detail, "audio_info": audio_info or {}}
        super().__init__(message, status_code=422, details=details)


class InvalidAudioFormatError(ASRError):
    """Invalid or unsupported audio format."""

    def __init__(self, format: str, supported_formats: Optional[list] = None):
        """
        Initialize invalid format error.

        Args:
            format: Invalid format
            supported_formats: Optional list of supported formats
        """
        supported = supported_formats or ["wav", "mp3", "ogg", "flac", "m4a", "webm"]
        message = (
            f"Audio format '{format}' is not supported. "
            f"Supported formats: {', '.join(supported)}"
        )
        details = {"format": format, "supported_formats": supported}
        super().__init__(message, status_code=415, details=details)


class MaliciousFileError(ASRError):
    """Potentially malicious file detected."""

    def __init__(self, reason: str):
        """
        Initialize malicious file error.

        Args:
            reason: Reason file was flagged
        """
        message = (
            f"File rejected: {reason}. "
            f"Please ensure you're uploading a valid audio file."
        )
        details = {"reason": reason}
        super().__init__(message, status_code=400, details=details)


class TranscriptionTimeoutError(ASRError):
    """Transcription timed out."""

    def __init__(self, provider_id: str, timeout_seconds: float):
        """
        Initialize transcription timeout error.

        Args:
            provider_id: Provider that timed out
            timeout_seconds: Timeout duration
        """
        message = (
            f"Transcription timed out after {timeout_seconds:.0f}s using provider '{provider_id}'. "
            f"This may be due to high server load. Please try again or use a different provider."
        )
        details = {
            "provider_id": provider_id,
            "timeout_seconds": timeout_seconds,
        }
        super().__init__(message, status_code=504, details=details)


def map_exception_to_asr_error(exc: Exception, provider_id: str = "unknown") -> ASRError:
    """
    Map generic exceptions to specific ASR errors.

    Analyzes exception message and type to provide user-friendly error messages.

    Args:
        exc: Original exception
        provider_id: Provider ID for context

    Returns:
        ASRError: Specific ASR error instance

    Examples:
        >>> try:
        ...     # Some operation that fails
        ... except Exception as e:
        ...     asr_error = map_exception_to_asr_error(e, "whisper_large_v3")
        ...     raise HTTPException(status_code=asr_error.status_code, detail=asr_error.message)
    """
    # If already an ASR error, return as-is
    if isinstance(exc, ASRError):
        return exc

    error_msg = str(exc).lower()

    # Balance errors
    if "balance" in error_msg or "insufficient" in error_msg:
        return InsufficientBalanceError(required=0.0, available=0.0)

    # Provider offline errors
    if "offline" in error_msg or "unreachable" in error_msg or "connection" in error_msg:
        return ProviderOfflineError(provider_id, str(exc))

    # Duration errors
    if "too long" in error_msg or "duration" in error_msg or "exceeds" in error_msg:
        return AudioTooLongError(duration=0, max_duration=300)

    # Size errors
    if "too large" in error_msg or "file size" in error_msg:
        return AudioTooLargeError(size_mb=0, max_size_mb=100)

    # Language errors
    if "language" in error_msg or "not supported" in error_msg:
        return InvalidLanguageError(language="unknown", provider_id=provider_id)

    # Format errors
    if "format" in error_msg or "codec" in error_msg or "invalid audio" in error_msg:
        return InvalidAudioFormatError(format="unknown")

    # Audio processing errors
    if "audio" in error_msg or "decode" in error_msg or "corrupt" in error_msg:
        return AudioProcessingError(str(exc))

    # Timeout errors
    if "timeout" in error_msg or "timed out" in error_msg:
        return TranscriptionTimeoutError(provider_id, timeout_seconds=120)

    # Generic fallback
    return ASRError(f"Transcription failed: {str(exc)}", status_code=500)
