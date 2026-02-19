"""
Voice Engine API routes module.

This module provides RESTful API endpoints for voice-related operations including
speech-to-text (STT), text-to-speech (TTS), language detection, and voice processing.
"""

from .router import router

__all__ = ["router"]