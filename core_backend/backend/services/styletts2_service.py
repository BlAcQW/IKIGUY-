#!/usr/bin/env python3
"""
StyleTTS2 Service
High-quality expressive TTS with voice cloning via reference audio.
Endpoint: https://styletts.ailabsafrica.com
"""

import logging
import httpx
from typing import Optional, Union
import asyncio
import base64

logger = logging.getLogger(__name__)


class StyleTTS2Service:
    """StyleTTS2 service wrapper for expressive voice synthesis."""

    def __init__(self, endpoint: str = "https://styletts.ailabsafrica.com"):
        """
        Initialize StyleTTS2 service.

        Args:
            endpoint (str): StyleTTS2 API endpoint
        """
        self.endpoint = endpoint
        self.timeout = 60.0  # Longer timeout for quality synthesis

    async def check_health(self) -> bool:
        """
        Check if StyleTTS2 service is healthy.

        Returns:
            bool: True if service is up, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.endpoint}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"StyleTTS2 health check failed: {e}")
            return False

    async def synthesize_with_reference(
        self,
        text: str,
        reference_audio: Union[bytes, str],
        language: str = "en",
        alpha: float = 0.3,
        beta: float = 0.7,
        diffusion_steps: int = 10,
        embedding_scale: float = 1.0
    ) -> Optional[bytes]:
        """
        Synthesize speech using reference audio for voice cloning.

        Args:
            text (str): Text to synthesize
            reference_audio (Union[bytes, str]): Reference audio bytes or base64 string
            language (str): Language code (en, zh, etc.)
            alpha (float): Style control (0-1, higher = more expressive)
            beta (float): Speaker similarity (0-1, higher = more similar)
            diffusion_steps (int): Quality steps (5-50, higher = better quality)
            embedding_scale (float): Voice embedding strength (0.5-2.0)

        Returns:
            Optional[bytes]: WAV audio bytes or None on error
        """
        try:
            logger.info(f"🎨 StyleTTS2 synthesizing with reference audio: alpha={alpha}, beta={beta}")

            # Prepare reference audio
            if isinstance(reference_audio, str):
                # Assume base64 encoded
                reference_audio = base64.b64decode(reference_audio)

            # Prepare multipart form data
            files = {
                "reference_audio": ("reference.wav", reference_audio, "audio/wav")
            }

            data = {
                "text": text,
                "language": language,
                "alpha": alpha,
                "beta": beta,
                "diffusion_steps": diffusion_steps,
                "embedding_scale": embedding_scale
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.endpoint}/synthesize_with_reference",
                    files=files,
                    data=data
                )

                if response.status_code == 200:
                    audio_bytes = response.content
                    logger.info(f"✅ StyleTTS2 generated {len(audio_bytes)} bytes of audio")
                    return audio_bytes
                else:
                    logger.error(f"❌ StyleTTS2 error: {response.status_code} - {response.text}")
                    return None

        except asyncio.TimeoutError:
            logger.error("❌ StyleTTS2 request timeout")
            return None
        except Exception as e:
            logger.error(f"❌ StyleTTS2 synthesis error: {e}")
            return None

    async def synthesize_default(
        self,
        text: str,
        language: str = "en",
        speaker_id: int = 0
    ) -> Optional[bytes]:
        """
        Synthesize speech using default voice (no reference audio).

        Args:
            text (str): Text to synthesize
            language (str): Language code (en, zh)
            speaker_id (int): Default speaker ID (0-based)

        Returns:
            Optional[bytes]: WAV audio bytes or None on error
        """
        try:
            logger.info(f"🎨 StyleTTS2 synthesizing with default voice: speaker={speaker_id}")

            payload = {
                "text": text,
                "language": language,
                "speaker_id": speaker_id
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.endpoint}/synthesize",
                    json=payload
                )

                if response.status_code == 200:
                    audio_bytes = response.content
                    logger.info(f"✅ StyleTTS2 generated {len(audio_bytes)} bytes of audio")
                    return audio_bytes
                else:
                    logger.error(f"❌ StyleTTS2 error: {response.status_code} - {response.text}")
                    return None

        except asyncio.TimeoutError:
            logger.error("❌ StyleTTS2 request timeout")
            return None
        except Exception as e:
            logger.error(f"❌ StyleTTS2 synthesis error: {e}")
            return None

    async def get_default_voices(self) -> list:
        """
        Get list of available default voices.

        Returns:
            list: List of speaker info dictionaries
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.endpoint}/voices")

                if response.status_code == 200:
                    return response.json()
                else:
                    # Return default if endpoint not available
                    return [
                        {"id": 0, "name": "Default Female", "language": "en"},
                        {"id": 1, "name": "Default Male", "language": "en"}
                    ]
        except Exception as e:
            logger.error(f"Error fetching StyleTTS2 voices: {e}")
            return [
                {"id": 0, "name": "Default Female", "language": "en"},
                {"id": 1, "name": "Default Male", "language": "en"}
            ]

    def get_supported_languages(self) -> list:
        """
        Get list of supported language codes.

        Returns:
            list: List of language codes
        """
        return ["en", "zh"]


# Singleton instance
_styletts2_service = None


def get_styletts2_service() -> StyleTTS2Service:
    """
    Get singleton StyleTTS2 service instance.

    Returns:
        StyleTTS2Service: The StyleTTS2 service
    """
    global _styletts2_service
    if _styletts2_service is None:
        _styletts2_service = StyleTTS2Service()
    return _styletts2_service
