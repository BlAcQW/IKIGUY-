"""
TTS-specific exceptions with actionable error messages.

Provides clear, user-friendly error messages that guide users on how to resolve issues.
"""


class TTSError(Exception):
    """Base TTS error with user-friendly message."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class InsufficientBalanceError(TTSError):
    """User has insufficient wallet balance."""

    def __init__(self, required: float, available: float):
        message = (
            f"Insufficient wallet balance. "
            f"Required: ${required:.4f}, Available: ${available:.4f}. "
            f"Please add funds to your wallet to continue."
        )
        super().__init__(message, status_code=402)
        self.required = required
        self.available = available


class ProviderOfflineError(TTSError):
    """TTS provider is currently offline."""

    def __init__(self, provider_id: str, alternatives: list = None):
        alt_text = ""
        if alternatives:
            alt_text = f" Try these alternatives: {', '.join(alternatives)}"
        message = (
            f"TTS provider '{provider_id}' is currently offline. "
            f"Please try again later or select a different provider.{alt_text}"
        )
        super().__init__(message, status_code=503)
        self.provider_id = provider_id
        self.alternatives = alternatives or []


class TextTooLongError(TTSError):
    """Text exceeds maximum character limit."""

    def __init__(self, length: int, max_length: int = 5000):
        message = (
            f"Text is too long ({length} characters). "
            f"Maximum allowed: {max_length} characters. "
            f"Please shorten your text and try again."
        )
        super().__init__(message, status_code=400)
        self.length = length
        self.max_length = max_length


class RateLimitExceededError(TTSError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int, limit: str = "10 requests/minute"):
        message = (
            f"Rate limit exceeded ({limit}). "
            f"Please wait {retry_after} seconds before trying again. "
            f"Consider upgrading your plan for higher limits."
        )
        super().__init__(message, status_code=429)
        self.retry_after = retry_after
        self.limit = limit


class InvalidProviderError(TTSError):
    """Provider ID is invalid or not supported."""

    def __init__(self, provider_id: str, available_providers: list = None):
        prov_text = ""
        if available_providers:
            prov_text = f" Available providers: {', '.join(available_providers)}"
        message = (
            f"Invalid TTS provider: '{provider_id}'. "
            f"Please select a valid provider.{prov_text}"
        )
        super().__init__(message, status_code=400)
        self.provider_id = provider_id
        self.available_providers = available_providers or []


class InvalidLanguageError(TTSError):
    """Language is not supported by the provider."""

    def __init__(self, language: str, provider_id: str, supported: list = None):
        lang_text = ""
        if supported:
            lang_text = f" Supported languages for {provider_id}: {', '.join(supported)}"
        message = (
            f"Language '{language}' is not supported by provider '{provider_id}'.{lang_text}"
        )
        super().__init__(message, status_code=400)
        self.language = language
        self.provider_id = provider_id
        self.supported_languages = supported or []


class VoiceNotFoundError(TTSError):
    """Voice ID not found."""

    def __init__(self, voice_id: str, provider_id: str):
        message = (
            f"Voice '{voice_id}' not found for provider '{provider_id}'. "
            f"Please select a valid voice from the available voices list."
        )
        super().__init__(message, status_code=404)
        self.voice_id = voice_id
        self.provider_id = provider_id


class AudioProcessingError(TTSError):
    """Error during audio processing."""

    def __init__(self, detail: str):
        message = (
            f"Audio processing failed: {detail}. "
            f"Please try again or contact support if the issue persists."
        )
        super().__init__(message, status_code=500)


class VoiceCloningNotSupportedError(TTSError):
    """Voice cloning is not supported by this provider."""

    def __init__(self, provider_id: str, supported_providers: list = None):
        prov_text = ""
        if supported_providers:
            prov_text = f" Providers with voice cloning: {', '.join(supported_providers)}"
        message = (
            f"Voice cloning is not supported by '{provider_id}'.{prov_text}"
        )
        super().__init__(message, status_code=400)
        self.provider_id = provider_id
        self.supported_providers = supported_providers or []


class InvalidAudioFormatError(TTSError):
    """Invalid audio file format."""

    def __init__(self, format_provided: str, supported_formats: list = None):
        fmt_text = ""
        if supported_formats:
            fmt_text = f" Supported formats: {', '.join(supported_formats)}"
        message = (
            f"Invalid audio format: '{format_provided}'.{fmt_text}"
        )
        super().__init__(message, status_code=400)
        self.format_provided = format_provided
        self.supported_formats = supported_formats or []


class InvalidParameterError(TTSError):
    """Invalid parameter value."""

    def __init__(self, param_name: str, param_value: any, reason: str):
        message = (
            f"Invalid value for parameter '{param_name}': {param_value}. "
            f"{reason}"
        )
        super().__init__(message, status_code=400)
        self.param_name = param_name
        self.param_value = param_value


class ProviderTimeoutError(TTSError):
    """Provider request timed out."""

    def __init__(self, provider_id: str, timeout: int):
        message = (
            f"Request to '{provider_id}' timed out after {timeout} seconds. "
            f"The provider may be experiencing high load. Please try again."
        )
        super().__init__(message, status_code=504)
        self.provider_id = provider_id
        self.timeout = timeout


class TransactionError(TTSError):
    """Wallet transaction failed."""

    def __init__(self, detail: str):
        message = (
            f"Wallet transaction failed: {detail}. "
            f"Your wallet was not charged. Please try again or contact support."
        )
        super().__init__(message, status_code=500)


def map_exception_to_tts_error(e: Exception) -> TTSError:
    """
    Map generic exceptions to specific TTS errors.

    Args:
        e: Original exception

    Returns:
        TTSError: Mapped TTS error with user-friendly message
    """
    error_msg = str(e).lower()

    # Check for common error patterns
    if "insufficient" in error_msg and "balance" in error_msg:
        return InsufficientBalanceError(required=0.0, available=0.0)

    elif "offline" in error_msg or "unavailable" in error_msg:
        return ProviderOfflineError(provider_id="unknown")

    elif "too long" in error_msg or "exceeds" in error_msg:
        return TextTooLongError(length=0)

    elif "rate limit" in error_msg:
        return RateLimitExceededError(retry_after=60)

    elif "invalid provider" in error_msg:
        return InvalidProviderError(provider_id="unknown")

    elif "language" in error_msg and "not supported" in error_msg:
        return InvalidLanguageError(language="unknown", provider_id="unknown")

    elif "voice" in error_msg and "not found" in error_msg:
        return VoiceNotFoundError(voice_id="unknown", provider_id="unknown")

    elif "timeout" in error_msg:
        return ProviderTimeoutError(provider_id="unknown", timeout=30)

    elif "transaction" in error_msg or "wallet" in error_msg:
        return TransactionError(detail=str(e))

    # Default generic error
    return AudioProcessingError(detail=str(e))
