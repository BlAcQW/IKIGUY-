"""
LLM Service Custom Exceptions

Custom exception classes for LLM service with user-friendly error messages,
appropriate HTTP status codes, and detailed error context.

Created: 2025-10-27
Phase: LLM Improvements - Phase 1 (Error Handling & Security)
"""

from typing import Optional, Dict, Any


class LLMError(Exception):
    """
    Base exception for all LLM-related errors.

    Attributes:
        status_code: HTTP status code for the error
        error_code: Machine-readable error identifier
        user_message: Human-readable error message
        details: Additional error context
    """

    status_code: int = 500
    error_code: str = "LLM_ERROR"
    user_message: str = "Language model processing failed. Please try again."

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize LLM error.

        Args:
            message: Custom error message (overrides user_message)
            details: Additional error context
            **kwargs: Additional parameters to include in error details
        """
        self.message = message or self.user_message
        self.details = details or {}
        self.details.update(kwargs)
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details
        }


class InsufficientBalanceError(LLMError):
    """
    User's wallet balance is insufficient for the requested operation.

    Example:
        User attempts to generate text but wallet balance is $0.05 and
        estimated cost is $0.10.
    """

    status_code = 402  # Payment Required
    error_code = "INSUFFICIENT_BALANCE"
    user_message = (
        "Your wallet balance is insufficient for this request. "
        "Please add credits to continue using the LLM service."
    )


class PromptTooLongError(LLMError):
    """
    The prompt exceeds the model's maximum context window.

    Example:
        User sends a prompt with 150K tokens to a model with 128K context window.
    """

    status_code = 413  # Payload Too Large
    error_code = "PROMPT_TOO_LONG"
    user_message = (
        "Your prompt is too long for this model's context window. "
        "Please shorten your prompt or use a model with a larger context window."
    )

    def __init__(
        self,
        message: Optional[str] = None,
        estimated_tokens: Optional[int] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize error with token information.

        Args:
            message: Custom error message
            estimated_tokens: Number of tokens in the prompt
            max_tokens: Maximum tokens allowed by the model
        """
        details = kwargs.pop("details", {})
        if estimated_tokens:
            details["estimated_tokens"] = estimated_tokens
        if max_tokens:
            details["max_tokens"] = max_tokens
            details["tokens_over_limit"] = estimated_tokens - max_tokens if estimated_tokens else 0

        super().__init__(message, details, **kwargs)


class InvalidModelError(LLMError):
    """
    The requested model is not available or doesn't exist.

    Example:
        User requests model "gpt-5" which doesn't exist in our registry.
    """

    status_code = 404  # Not Found
    error_code = "INVALID_MODEL"
    user_message = (
        "The requested model is not available. "
        "Please check the model ID and try again."
    )

    def __init__(
        self,
        message: Optional[str] = None,
        model_id: Optional[str] = None,
        available_models: Optional[list] = None,
        **kwargs
    ):
        """
        Initialize error with model information.

        Args:
            message: Custom error message
            model_id: The invalid model ID that was requested
            available_models: List of available model IDs
        """
        details = kwargs.pop("details", {})
        if model_id:
            details["requested_model"] = model_id
        if available_models:
            details["available_models"] = available_models[:5]  # First 5 suggestions

        super().__init__(message, details, **kwargs)


class RateLimitExceededError(LLMError):
    """
    User has exceeded their rate limit for LLM requests.

    Example:
        Free tier user makes 6 requests in 1 minute (limit: 5/min).
    """

    status_code = 429  # Too Many Requests
    error_code = "RATE_LIMIT_EXCEEDED"
    user_message = (
        "You have exceeded your rate limit for LLM requests. "
        "Please wait a moment and try again, or upgrade your plan for higher limits."
    )

    def __init__(
        self,
        message: Optional[str] = None,
        limit: Optional[str] = None,
        retry_after: Optional[int] = None,
        tier: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize error with rate limit information.

        Args:
            message: Custom error message
            limit: Rate limit that was exceeded (e.g., "5/minute")
            retry_after: Seconds to wait before retrying
            tier: User's current tier (free, starter, pro, enterprise)
        """
        details = kwargs.pop("details", {})
        if limit:
            details["rate_limit"] = limit
        if retry_after:
            details["retry_after_seconds"] = retry_after
        if tier:
            details["current_tier"] = tier
            details["upgrade_info"] = "Upgrade to a higher tier for increased rate limits"

        super().__init__(message, details, **kwargs)


class ModelOfflineError(LLMError):
    """
    The requested model is currently offline or unavailable.

    Example:
        Ollama service is down or model hasn't been loaded yet.
    """

    status_code = 503  # Service Unavailable
    error_code = "MODEL_OFFLINE"
    user_message = (
        "The selected model is currently offline or unavailable. "
        "Please try a different model or wait a moment and retry."
    )

    def __init__(
        self,
        message: Optional[str] = None,
        model_id: Optional[str] = None,
        alternative_models: Optional[list] = None,
        **kwargs
    ):
        """
        Initialize error with model availability information.

        Args:
            message: Custom error message
            model_id: The offline model ID
            alternative_models: List of online alternative model IDs
        """
        details = kwargs.pop("details", {})
        if model_id:
            details["offline_model"] = model_id
        if alternative_models:
            details["alternative_models"] = alternative_models[:3]  # Top 3 alternatives

        super().__init__(message, details, **kwargs)


class UnsafeContentError(LLMError):
    """
    The prompt contains potentially unsafe or inappropriate content.

    Example:
        Prompt contains jailbreak attempt or prompt injection patterns.
    """

    status_code = 400  # Bad Request
    error_code = "UNSAFE_CONTENT"
    user_message = (
        "Your prompt contains content that violates our safety guidelines. "
        "Please revise your prompt and try again."
    )

    def __init__(
        self,
        message: Optional[str] = None,
        detected_pattern: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize error with unsafe content information.

        Args:
            message: Custom error message
            detected_pattern: Type of unsafe pattern detected
        """
        details = kwargs.pop("details", {})
        if detected_pattern:
            details["detected_pattern"] = detected_pattern
        details["safety_guidelines"] = "Please avoid jailbreak attempts, prompt injections, and harmful content"

        super().__init__(message, details, **kwargs)


class GenerationTimeoutError(LLMError):
    """
    The model response generation timed out.

    Example:
        Model takes longer than 120 seconds to generate response.
    """

    status_code = 504  # Gateway Timeout
    error_code = "GENERATION_TIMEOUT"
    user_message = (
        "The response generation took too long and timed out. "
        "Please try a shorter prompt or a faster model."
    )

    def __init__(
        self,
        message: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize error with timeout information.

        Args:
            message: Custom error message
            timeout_seconds: Timeout duration in seconds
        """
        details = kwargs.pop("details", {})
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        details["suggestion"] = "Try reducing max_tokens or using a faster model"

        super().__init__(message, details, **kwargs)


class InvalidTemperatureError(LLMError):
    """
    The temperature parameter is outside the valid range (0.0 - 2.0).

    Example:
        User sets temperature to 3.5 (valid range: 0.0 - 2.0).
    """

    status_code = 400  # Bad Request
    error_code = "INVALID_TEMPERATURE"
    user_message = (
        "Temperature must be between 0.0 and 2.0. "
        "Use lower values (0.0-0.5) for deterministic outputs, "
        "or higher values (0.7-2.0) for creative outputs."
    )

    def __init__(
        self,
        message: Optional[str] = None,
        provided_temperature: Optional[float] = None,
        **kwargs
    ):
        """
        Initialize error with temperature information.

        Args:
            message: Custom error message
            provided_temperature: The invalid temperature value provided
        """
        details = kwargs.pop("details", {})
        if provided_temperature is not None:
            details["provided_temperature"] = provided_temperature
        details["valid_range"] = "0.0 - 2.0"
        details["recommendation"] = "Use 0.7 for balanced responses"

        super().__init__(message, details, **kwargs)


class MaxTokensExceededError(LLMError):
    """
    The max_tokens parameter exceeds the model's limit.

    Example:
        User requests 8192 tokens from a model with 4096 max output tokens.
    """

    status_code = 400  # Bad Request
    error_code = "MAX_TOKENS_EXCEEDED"
    user_message = (
        "The requested max_tokens exceeds the model's maximum output tokens. "
        "Please reduce max_tokens or use a model with higher output capacity."
    )

    def __init__(
        self,
        message: Optional[str] = None,
        requested_tokens: Optional[int] = None,
        max_allowed: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize error with token limit information.

        Args:
            message: Custom error message
            requested_tokens: The number of tokens requested
            max_allowed: Maximum tokens allowed by the model
        """
        details = kwargs.pop("details", {})
        if requested_tokens:
            details["requested_tokens"] = requested_tokens
        if max_allowed:
            details["max_allowed_tokens"] = max_allowed

        super().__init__(message, details, **kwargs)


# ============================================================================
# Exception Mapping Helper
# ============================================================================

def map_exception_to_llm_error(exception: Exception) -> LLMError:
    """
    Map generic exceptions to appropriate LLM error classes.

    This function converts common exceptions (ValueError, TimeoutError, etc.)
    into user-friendly LLM error classes with appropriate status codes and messages.

    Args:
        exception: The original exception

    Returns:
        LLMError subclass instance

    Example:
        try:
            result = await llm_service.chat(...)
        except ValueError as e:
            llm_error = map_exception_to_llm_error(e)
            raise llm_error
    """
    error_message = str(exception)

    # Check for specific error patterns in message
    if "insufficient" in error_message.lower() and "balance" in error_message.lower():
        return InsufficientBalanceError(message=error_message)

    elif "too long" in error_message.lower() or "context window" in error_message.lower():
        return PromptTooLongError(message=error_message)

    elif "not found" in error_message.lower() or "invalid model" in error_message.lower():
        return InvalidModelError(message=error_message)

    elif "rate limit" in error_message.lower():
        return RateLimitExceededError(message=error_message)

    elif "offline" in error_message.lower() or "unavailable" in error_message.lower():
        return ModelOfflineError(message=error_message)

    elif "unsafe" in error_message.lower() or "inappropriate" in error_message.lower():
        return UnsafeContentError(message=error_message)

    elif "timeout" in error_message.lower():
        return GenerationTimeoutError(message=error_message)

    elif "temperature" in error_message.lower():
        return InvalidTemperatureError(message=error_message)

    elif "max_tokens" in error_message.lower() or "token limit" in error_message.lower():
        return MaxTokensExceededError(message=error_message)

    # Check exception type
    elif isinstance(exception, TimeoutError):
        return GenerationTimeoutError(message=error_message)

    elif isinstance(exception, ValueError):
        # Generic validation error
        return LLMError(message=f"Invalid input: {error_message}")

    elif isinstance(exception, ConnectionError):
        return ModelOfflineError(message=f"Connection error: {error_message}")

    else:
        # Generic LLM error for unknown exceptions
        return LLMError(message=f"LLM processing error: {error_message}")
