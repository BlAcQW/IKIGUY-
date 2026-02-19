"""
Prompt Validation Service

Centralized service for validating LLM prompts before sending to models.
Includes token count estimation, context window validation, unsafe content detection,
and parameter validation.

Location: @apps/shared/services/ (centralized for reuse across all apps)
Created: 2025-10-27
Phase: LLM Improvements - Phase 1 (Error Handling & Security)
"""

import re
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class ChatMessage(BaseModel):
    """Chat message in conversation."""
    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")


class ValidationResult(BaseModel):
    """Result from prompt validation."""
    valid: bool = Field(..., description="Whether prompt is valid")
    estimated_tokens: int = Field(..., description="Estimated token count")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# ============================================================================
# Prompt Validation Service
# ============================================================================

class PromptValidationService:
    """
    Centralized service for LLM prompt validation.

    Features:
    - Token count estimation (1 token ≈ 4 characters)
    - Context window validation
    - Unsafe content pattern detection (jailbreak attempts)
    - Message format validation
    - Temperature/top_p range validation
    - Max tokens validation

    Usage:
        service = PromptValidationService()
        result = await service.validate_prompt(
            messages=[ChatMessage(role="user", content="Hello!")],
            model_id="llama_32_3b",
            temperature=0.7,
            max_tokens=1000
        )

        if not result.valid:
            raise ValueError(f"Invalid prompt: {result.errors}")
    """

    # Unsafe patterns that might indicate jailbreak attempts or prompt injection
    UNSAFE_PATTERNS = [
        # Jailbreak attempts
        r"ignore.*previous.*instructions?",
        r"disregard.*previous.*instructions?",
        r"forget.*previous.*instructions?",

        # Prompt injection
        r"system.*prompt.*override",
        r"new.*system.*prompt",
        r"developer.*mode",

        # Explicit jailbreak terms
        r"jailbreak",
        r"DAN\s+mode",  # "Do Anything Now"
        r"evil.*mode",

        # Role confusion
        r"you.*are.*now.*act.*as",
        r"pretend.*you.*are",

        # Instruction bypass
        r"bypass.*safety",
        r"ignore.*safety",
        r"disable.*filter",
    ]

    def __init__(self):
        """Initialize the prompt validation service."""
        # Compile regex patterns for performance
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.UNSAFE_PATTERNS
        ]

        logger.info(f"PromptValidationService initialized with {len(self.compiled_patterns)} safety patterns")

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count from text.

        Uses a simple heuristic: 1 token ≈ 4 characters.
        This is a rough approximation but works well for most cases.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Remove excessive whitespace
        cleaned_text = re.sub(r'\s+', ' ', text)
        char_count = len(cleaned_text)

        # Rough estimate: 1 token ≈ 4 characters
        # For English text, this is typically accurate within 10-20%
        estimated_tokens = max(1, char_count // 4)

        return estimated_tokens

    def estimate_messages_tokens(self, messages: List[ChatMessage]) -> int:
        """
        Estimate total token count from list of messages.

        Includes overhead for message formatting (role labels, etc.).

        Args:
            messages: List of chat messages

        Returns:
            Estimated total token count
        """
        total_tokens = 0

        for message in messages:
            # Count tokens for content
            content_tokens = self.estimate_tokens(message.content)

            # Add overhead for role and formatting (~4 tokens per message)
            # Format: {"role": "user", "content": "..."}
            overhead_tokens = 4

            total_tokens += content_tokens + overhead_tokens

        # Add overhead for conversation structure (~3 tokens)
        total_tokens += 3

        return total_tokens

    def detect_unsafe_content(self, text: str) -> Optional[str]:
        """
        Detect unsafe content patterns in text.

        Args:
            text: Text to check

        Returns:
            Pattern description if unsafe content detected, None otherwise
        """
        for pattern in self.compiled_patterns:
            match = pattern.search(text)
            if match:
                # Return a description of what was detected
                matched_text = match.group(0)
                return f"Potential jailbreak attempt: '{matched_text}'"

        return None

    def validate_message_format(self, messages: List[ChatMessage]) -> List[str]:
        """
        Validate message format and structure.

        Args:
            messages: List of messages to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not messages:
            errors.append("Messages list is empty")
            return errors

        # Check each message
        for idx, message in enumerate(messages):
            # Validate role
            valid_roles = ["system", "user", "assistant"]
            if message.role not in valid_roles:
                errors.append(
                    f"Message {idx}: Invalid role '{message.role}'. "
                    f"Must be one of: {', '.join(valid_roles)}"
                )

            # Validate content is not empty
            if not message.content or not message.content.strip():
                errors.append(f"Message {idx}: Content is empty")

            # Check content length (sanity check: max 100K characters per message)
            if len(message.content) > 100000:
                errors.append(
                    f"Message {idx}: Content too long ({len(message.content)} characters). "
                    "Maximum 100K characters per message."
                )

        # Check message order (should not start with assistant)
        if messages[0].role == "assistant":
            errors.append("First message should not be from assistant")

        # Check for alternating user/assistant (optional warning, not error)
        # This is more of a best practice

        return errors

    def validate_temperature(self, temperature: float) -> List[str]:
        """
        Validate temperature parameter.

        Args:
            temperature: Temperature value (0.0 - 2.0)

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if temperature < 0.0:
            errors.append(f"Temperature {temperature} is too low. Minimum: 0.0")
        elif temperature > 2.0:
            errors.append(f"Temperature {temperature} is too high. Maximum: 2.0")

        return errors

    def validate_top_p(self, top_p: float) -> List[str]:
        """
        Validate top_p parameter.

        Args:
            top_p: Top-p value (0.0 - 1.0)

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if top_p < 0.0:
            errors.append(f"Top-p {top_p} is too low. Minimum: 0.0")
        elif top_p > 1.0:
            errors.append(f"Top-p {top_p} is too high. Maximum: 1.0")

        return errors

    async def validate_prompt(
        self,
        messages: List[ChatMessage],
        model_id: str,
        context_window: int = 128000,
        max_tokens: Optional[int] = None,
        max_output_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 0.9,
        check_unsafe_content: bool = True
    ) -> ValidationResult:
        """
        Comprehensive prompt validation.

        Args:
            messages: List of chat messages
            model_id: Model identifier
            context_window: Model's maximum context window (default: 128K)
            max_tokens: Requested max output tokens
            max_output_tokens: Model's maximum output tokens (default: 4096)
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            check_unsafe_content: Whether to check for unsafe patterns

        Returns:
            ValidationResult with validation status and details
        """
        errors = []
        warnings = []
        metadata = {}

        # 1. Validate message format
        format_errors = self.validate_message_format(messages)
        errors.extend(format_errors)

        # 2. Estimate token count
        estimated_tokens = self.estimate_messages_tokens(messages)
        metadata["estimated_input_tokens"] = estimated_tokens

        # 3. Check context window
        # Reserve space for output tokens
        available_input_tokens = context_window - (max_tokens or max_output_tokens)

        if estimated_tokens > available_input_tokens:
            errors.append(
                f"Estimated {estimated_tokens} tokens exceeds available input space "
                f"({available_input_tokens} tokens). Context window: {context_window}, "
                f"Reserved for output: {max_tokens or max_output_tokens}"
            )
        elif estimated_tokens > context_window * 0.8:
            # Warning if using >80% of context window
            warnings.append(
                f"Prompt uses {(estimated_tokens/context_window)*100:.1f}% of context window. "
                "Consider reducing prompt length for better performance."
            )

        # 4. Validate max_tokens parameter
        if max_tokens is not None:
            if max_tokens <= 0:
                errors.append(f"Max tokens must be positive. Got: {max_tokens}")
            elif max_tokens > max_output_tokens:
                errors.append(
                    f"Max tokens {max_tokens} exceeds model limit ({max_output_tokens})"
                )

        # 5. Validate temperature
        temp_errors = self.validate_temperature(temperature)
        errors.extend(temp_errors)

        # 6. Validate top_p
        top_p_errors = self.validate_top_p(top_p)
        errors.extend(top_p_errors)

        # 7. Check for unsafe content
        if check_unsafe_content:
            for idx, message in enumerate(messages):
                unsafe_pattern = self.detect_unsafe_content(message.content)
                if unsafe_pattern:
                    errors.append(f"Message {idx}: {unsafe_pattern}")

        # 8. Determine validity
        valid = len(errors) == 0

        # 9. Build result
        result = ValidationResult(
            valid=valid,
            estimated_tokens=estimated_tokens,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )

        # Log validation result
        if not valid:
            logger.warning(
                f"Prompt validation failed for model {model_id}: "
                f"{len(errors)} errors, {len(warnings)} warnings"
            )
        elif warnings:
            logger.info(
                f"Prompt validation passed with {len(warnings)} warnings for model {model_id}"
            )

        return result

    def get_unsafe_patterns_info(self) -> Dict[str, Any]:
        """
        Get information about unsafe patterns being detected.

        Returns:
            Dictionary with pattern categories and examples
        """
        return {
            "total_patterns": len(self.UNSAFE_PATTERNS),
            "categories": {
                "jailbreak_attempts": [
                    "ignore previous instructions",
                    "disregard previous instructions",
                    "forget previous instructions"
                ],
                "prompt_injection": [
                    "system prompt override",
                    "new system prompt",
                    "developer mode"
                ],
                "explicit_jailbreak": [
                    "jailbreak",
                    "DAN mode",
                    "evil mode"
                ],
                "role_confusion": [
                    "you are now act as",
                    "pretend you are"
                ],
                "instruction_bypass": [
                    "bypass safety",
                    "ignore safety",
                    "disable filter"
                ]
            },
            "detection_method": "Regular expression pattern matching (case-insensitive)",
            "false_positive_note": "Patterns are designed to be conservative. Some false positives may occur."
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_validation_service_instance: Optional[PromptValidationService] = None


def get_validation_service() -> PromptValidationService:
    """
    Get singleton instance of PromptValidationService.

    Returns:
        Initialized PromptValidationService instance
    """
    global _validation_service_instance

    if _validation_service_instance is None:
        _validation_service_instance = PromptValidationService()
        logger.info("PromptValidationService singleton initialized")

    return _validation_service_instance
