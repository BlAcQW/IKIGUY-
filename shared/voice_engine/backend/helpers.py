"""Helper functions for interacting with voice-engine backend services.

This module provides lightweight wrappers around the Core Backend voice
endpoints used by demos and tests. The helpers make HTTP requests and return
parsed responses.
"""
from typing import Dict, List, Optional
import httpx


async def transcribe(samples: List[int], base_url: str) -> Dict[str, object]:
    """Transcribe audio samples using the backend STT endpoint.

    Args:
        samples: PCM16 integer samples.
        base_url: Base URL of the Core Backend.

    Returns:
        Dictionary containing ``partials`` and ``text``.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{base_url}/voice/stt", json={"samples": samples})
        resp.raise_for_status()
        return resp.json()


async def synthesize(
    text: str, base_url: str, voice: Optional[str] = None
) -> List[int]:
    """Synthesize text to speech using the backend TTS endpoint.

    Args:
        text: Text to synthesize.
        base_url: Base URL of the Core Backend.
        voice: Optional voice identifier.

    Returns:
        PCM16 samples for the synthesized audio.
    """
    payload = {"text": text}
    if voice:
        payload["voice"] = voice
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{base_url}/voice/tts", json=payload)
        resp.raise_for_status()
        return resp.json()["samples"]


async def llm(text: str, base_url: str) -> str:
    """Generate a reply using the backend LLM endpoint.

    Args:
        text: User-provided text.
        base_url: Base URL of the Core Backend.

    Returns:
        Generated reply string.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{base_url}/voice/llm", json={"text": text})
        resp.raise_for_status()
        return resp.json()["reply"]


async def detect_language(samples: List[int], base_url: str) -> Optional[str]:
    """Determine language for audio samples via the STT endpoint.

    Args:
        samples: PCM16 integer samples.
        base_url: Base URL of the Core Backend.

    Returns:
        Optional language code if detection succeeds.
    """
    data = await transcribe(samples, base_url)
    return data.get("language")
