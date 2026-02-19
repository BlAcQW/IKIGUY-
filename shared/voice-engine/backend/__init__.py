from __future__ import annotations

"""Lightweight helpers for the voice-engine backend.

These helpers provide minimal implementations of speech-to-text (STT),
language detection, large language model (LLM) generation, and text-to-speech
(TTS) synthesis. They are intentionally simple and deterministic so they can be
used in unit tests without external dependencies.
"""

from typing import Dict, List, Tuple
import asyncio
import logging

# Import real TTS providers
try:
    from .real_tts_providers import tts_manager, generate_tts, VOICE_OPTIONS as REAL_VOICE_OPTIONS
    TTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Real TTS providers not available: {e}")
    TTS_AVAILABLE = False
    REAL_VOICE_OPTIONS = {
        "stt": {"mock": ["base"]},
        "llm": {"mock": ["base"]},
        "tts": {"mock": ["base"]},
    }

VOICE_OPTIONS: Dict[str, Dict[str, List[str]]] = REAL_VOICE_OPTIONS


def get_voice_options() -> Dict[str, Dict[str, List[str]]]:
    """Return available provider and model combinations."""

    return VOICE_OPTIONS


async def detect_language(audio_data: bytes) -> Tuple[str, float]:
    """Detect the language of the provided audio.

    Args:
        audio_data (bytes): Raw audio bytes.

    Returns:
        Tuple[str, float]: ISO language code and confidence score.
    """

    return "en", 0.99


async def transcribe(audio_data: bytes, provider: str, model: str) -> Tuple[str, float]:
    """Transcribe audio data using a mock STT engine.

    Args:
        audio_data (bytes): Raw audio bytes.
        provider (str): STT provider identifier.
        model (str): STT model name.

    Returns:
        Tuple[str, float]: Transcript text and confidence score.
    """

    return "hello world", 0.9


async def generate_llm_response(prompt: str, provider: str, model: str) -> str:
    """Generate a mock LLM response.

    Args:
        prompt (str): Prompt to send to the model.
        provider (str): LLM provider identifier.
        model (str): LLM model name.

    Returns:
        str: Generated response text.
    """

    return f"response: {prompt}"


async def generate_tts_backend(text: str, provider: str, model: str, language: str = "en") -> bytes:
    """Synthesize speech for the given text using real TTS models.

    Args:
        text (str): Text to synthesize.
        provider (str): TTS provider identifier.
        model (str): TTS model name.
        language (str): Target language code.

    Returns:
        bytes: Encoded audio data.
    """
    
    if TTS_AVAILABLE:
        try:
            return await generate_tts(text=text, provider=provider, model=model, language=language)
        except Exception as e:
            logging.error(f"Real TTS failed, using fallback: {e}")
    
    # Fallback for compatibility
    return text.encode()

# Maintain backward compatibility
async def generate_tts_legacy(text: str, provider: str, model: str) -> bytes:
    """Legacy TTS function for backward compatibility."""
    return await generate_tts_backend(text, provider, model)

# Export the legacy function with original name
generate_tts_original = generate_tts_legacy
