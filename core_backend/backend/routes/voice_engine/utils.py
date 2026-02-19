"""
Utility functions for voice engine operations.
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID

# Lazy imports to avoid circular dependencies
def _get_voice_session_service():
    """Lazy import for voice session service."""
    try:
        from ...services import voice_session_service
        return voice_session_service
    except ImportError:
        return None

def _get_event_bus():
    """Lazy import for event bus."""
    try:
        from ...events import event_bus, EventType
        return event_bus, EventType
    except ImportError:
        return None, None

logger = logging.getLogger(__name__)


def validate_selection(
    provider: str, model: str, language: str, voice: Optional[str] = None
) -> None:
    """
    Validate provider, model, language, and voice selections.
    
    Args:
        provider: The provider name to validate
        model: The model name to validate  
        language: The language code to validate
        voice: The voice name to validate (optional)
        
    Raises:
        ValueError: If any selection is invalid
    """
    # For now, skip validation since we're only using database providers
    # TODO: Implement validation against database providers
    pass


async def record_turn(
    operation: str,
    request_data: Dict[str, Any],
    response_data: Dict[str, Any],
    session_id: Optional[UUID] = None,
) -> None:
    """
    Record a voice operation turn for tracking and analytics.
    
    Args:
        operation: The operation that was performed
        request_data: The request data
        response_data: The response data
        session_id: Optional session ID
    """
    if not session_id:
        return

    try:
        # Lazy import services
        voice_session_service = _get_voice_session_service()
        event_bus, EventType = _get_event_bus()
        
        if not voice_session_service:
            logger.warning("Voice session service not available, skipping turn recording")
            return

        # Import models lazily
        try:
            from ...models import VoiceTurn, VoiceSession
        except ImportError:
            logger.warning("Voice models not available, skipping turn recording")
            return

        # Get or create voice session
        session = await voice_session_service.get_session(session_id)
        if not session:
            session = VoiceSession(id=session_id, turns=[])
            session = await voice_session_service.create_session(session)

        # Create turn record
        turn = VoiceTurn(
            operation=operation,
            request_data=request_data,
            response_data=response_data
        )

        # Add turn to session
        await voice_session_service.add_turn(session_id, turn)

        # Publish event for real-time updates if available
        if event_bus and EventType:
            await event_bus.publish(EventType.VOICE_TURN_RECORDED, {
                "session_id": str(session_id),
                "operation": operation,
                "turn_data": turn.model_dump()
            })

    except Exception as e:
        logger.error(f"Failed to record voice turn: {e}")
        # Don't raise - this shouldn't break the main operation


def format_error_response(error: Exception, operation: str) -> Dict[str, Any]:
    """
    Format an error response for consistent error handling.
    
    Args:
        error: The exception that occurred
        operation: The operation that failed
        
    Returns:
        Formatted error response
    """
    return {
        "error": True,
        "operation": operation,
        "message": str(error),
        "error_type": type(error).__name__
    }


def validate_audio_samples(samples: list) -> bool:
    """
    Validate audio samples for basic correctness.
    
    Args:
        samples: List of audio sample integers
        
    Returns:
        True if samples are valid, False otherwise
    """
    if not samples:
        return False
        
    if not isinstance(samples, list):
        return False
        
    # Check that all samples are integers
    if not all(isinstance(sample, int) for sample in samples):
        return False
        
    # Check reasonable sample value range (16-bit audio)
    if any(abs(sample) > 32767 for sample in samples):
        logger.warning("Audio samples exceed 16-bit range")
        
    return True


def validate_text_input(text: str, max_length: int = 5000) -> bool:
    """
    Validate text input for synthesis.
    
    Args:
        text: The text to validate
        max_length: Maximum allowed text length
        
    Returns:
        True if text is valid, False otherwise
    """
    if not text or not isinstance(text, str):
        return False
        
    if len(text.strip()) == 0:
        return False
        
    if len(text) > max_length:
        return False
        
    return True


def sanitize_language_code(language: str) -> str:
    """
    Sanitize and normalize language codes.
    
    Args:
        language: The language code to sanitize
        
    Returns:
        Normalized language code
    """
    if not language:
        return "en"
        
    # Convert to lowercase and remove extra whitespace
    language = language.lower().strip()
    
    # Map common variants to standard codes
    language_mappings = {
        "english": "en",
        "twi": "tw",
        "akan": "ak", 
        "ewe": "ee",
        "ga": "gaa",
        "hausa": "ha",
        "yoruba": "yo",
        "igbo": "ig",
        "swahili": "sw",
        "swahili": "sw",
        "kikuyu": "ki",
        "luo": "luo",
        "zulu": "zu",
        "xhosa": "xh",
        "afrikaans": "af"
    }
    
    return language_mappings.get(language, language)


def get_provider_capabilities(provider_name: str) -> Dict[str, Any]:
    """
    Get capabilities information for a provider.
    
    Args:
        provider_name: Name of the provider
        
    Returns:
        Dictionary of provider capabilities
    """
    # This would typically come from a database or config
    # For now, return mock capabilities
    default_capabilities = {
        "languages": ["en"],
        "voices": ["default"],
        "features": ["synthesis"],
        "sample_rates": [22050, 44100]
    }
    
    provider_capabilities = {
        "meta_mms": {
            "languages": ["tw", "ee", "ha", "ak"],
            "voices": ["default"],
            "features": ["synthesis", "multilingual"],
            "sample_rates": [16000, 22050]
        },
        "coqui": {
            "languages": ["en", "es", "fr", "de"],
            "voices": ["ljspeech", "vctk"],
            "features": ["synthesis", "voice_cloning"],
            "sample_rates": [22050, 44100]
        },
        "openvoice": {
            "languages": ["en", "zh", "jp"],
            "voices": ["default", "cloned"],
            "features": ["synthesis", "voice_cloning", "cross_lingual"],
            "sample_rates": [24000, 44100]
        }
    }
    
    return provider_capabilities.get(provider_name, default_capabilities)