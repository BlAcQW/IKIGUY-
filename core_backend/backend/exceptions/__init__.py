"""
Backend exceptions module.

Provides custom exception classes for better error handling and user feedback.
"""

from .tts_errors import (
    TTSError,
    InsufficientBalanceError,
    ProviderOfflineError,
    TextTooLongError,
    RateLimitExceededError,
    InvalidProviderError,
    InvalidLanguageError,
    VoiceNotFoundError,
    AudioProcessingError,
    VoiceCloningNotSupportedError,
    InvalidAudioFormatError,
    InvalidParameterError,
    ProviderTimeoutError,
    TransactionError,
    map_exception_to_tts_error,
)

__all__ = [
    "TTSError",
    "InsufficientBalanceError",
    "ProviderOfflineError",
    "TextTooLongError",
    "RateLimitExceededError",
    "InvalidProviderError",
    "InvalidLanguageError",
    "VoiceNotFoundError",
    "AudioProcessingError",
    "VoiceCloningNotSupportedError",
    "InvalidAudioFormatError",
    "InvalidParameterError",
    "ProviderTimeoutError",
    "TransactionError",
    "map_exception_to_tts_error",
]
