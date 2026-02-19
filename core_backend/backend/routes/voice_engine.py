"""
Voice Engine API Routes - Compatibility Layer

This file maintains backward compatibility while using the new modular structure.
The actual implementation has been refactored into the voice_engine package.
"""

# Import the router from the new modular structure
from .voice_engine import router

# For backward compatibility, re-export commonly used items
from .voice_engine.models import *
from .voice_engine.constants import AVAILABLE_VOICES, LANGUAGES, COUNTRIES, CURRENT_LANGUAGE
from .voice_engine.utils import validate_selection, record_turn as _record_turn

# Legacy compatibility
async def _record_turn(operation, request_data, response_data, session_id=None):
    """Legacy wrapper for record_turn function."""
    return await record_turn(operation, request_data, response_data, session_id)

__all__ = ["router"]