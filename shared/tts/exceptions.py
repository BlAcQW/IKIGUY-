"""
TTS Exception Classes
Custom exceptions for TTS operations.
"""

from typing import Optional, Dict, Any


class TTSException(Exception):
    """Base exception for TTS operations."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize TTS exception.

        Args:
            message: Error message
            provider: TTS provider name
            error_code: Error code for categorization
            details: Additional error details
        """
        self.message = message
        self.provider = provider
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """String representation of the exception."""
        parts = [self.message]
        if self.provider:
            parts.append(f"Provider: {self.provider}")
        if self.error_code:
            parts.append(f"Code: {self.error_code}")
        return " | ".join(parts)


class ProviderNotAvailableError(TTSException):
    """Raised when a TTS provider is not available or offline."""

    def __init__(self, provider: str, reason: Optional[str] = None):
        """Initialize provider not available error."""
        message = f"TTS provider '{provider}' is not available"
        if reason:
            message += f": {reason}"
        super().__init__(message, provider=provider, error_code="PROVIDER_UNAVAILABLE")


class ModelNotLoadedError(TTSException):
    """Raised when TTS models are not loaded."""

    def __init__(self, provider: str, model_name: Optional[str] = None):
        """Initialize model not loaded error."""
        message = f"Model not loaded for provider '{provider}'"
        if model_name:
            message += f": {model_name}"
        super().__init__(message, provider=provider, error_code="MODEL_NOT_LOADED")


class AudioProcessingError(TTSException):
    """Raised when audio processing fails."""

    def __init__(self, message: str, provider: Optional[str] = None):
        """Initialize audio processing error."""
        super().__init__(message, provider=provider, error_code="AUDIO_PROCESSING_ERROR")


class InvalidRequestError(TTSException):
    """Raised when TTS request is invalid."""

    def __init__(self, message: str, field: Optional[str] = None):
        """Initialize invalid request error."""
        details = {"field": field} if field else {}
        super().__init__(message, error_code="INVALID_REQUEST", details=details)


class RateLimitError(TTSException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        provider: str,
        limit: Optional[int] = None,
        reset_time: Optional[int] = None
    ):
        """Initialize rate limit error."""
        message = f"Rate limit exceeded for provider '{provider}'"
        details = {}
        if limit:
            details["limit"] = limit
        if reset_time:
            details["reset_time"] = reset_time
        super().__init__(message, provider=provider, error_code="RATE_LIMIT", details=details)


class AuthenticationError(TTSException):
    """Raised when authentication fails."""

    def __init__(self, provider: str, message: Optional[str] = None):
        """Initialize authentication error."""
        msg = f"Authentication failed for provider '{provider}'"
        if message:
            msg += f": {message}"
        super().__init__(msg, provider=provider, error_code="AUTH_ERROR")


class ConnectionError(TTSException):
    """Raised when connection to TTS service fails."""

    def __init__(self, provider: str, endpoint: str, reason: Optional[str] = None):
        """Initialize connection error."""
        message = f"Failed to connect to {provider} at {endpoint}"
        if reason:
            message += f": {reason}"
        super().__init__(
            message,
            provider=provider,
            error_code="CONNECTION_ERROR",
            details={"endpoint": endpoint}
        )


class TimeoutError(TTSException):
    """Raised when TTS operation times out."""

    def __init__(self, provider: str, timeout: float):
        """Initialize timeout error."""
        message = f"Operation timed out after {timeout}s for provider '{provider}'"
        super().__init__(
            message,
            provider=provider,
            error_code="TIMEOUT",
            details={"timeout": timeout}
        )


class QuotaExceededError(TTSException):
    """Raised when usage quota is exceeded."""

    def __init__(
        self,
        provider: str,
        quota_type: str = "requests",
        limit: Optional[int] = None
    ):
        """Initialize quota exceeded error."""
        message = f"Quota exceeded for provider '{provider}' ({quota_type})"
        details = {"quota_type": quota_type}
        if limit:
            details["limit"] = limit
        super().__init__(message, provider=provider, error_code="QUOTA_EXCEEDED", details=details)


class WebSocketError(TTSException):
    """Raised when WebSocket operation fails."""

    def __init__(self, message: str, provider: Optional[str] = None):
        """Initialize WebSocket error."""
        super().__init__(message, provider=provider, error_code="WEBSOCKET_ERROR")