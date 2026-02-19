#!/usr/bin/env python3
"""
F5-TTS Service
Flow-matching based TTS with zero-shot voice cloning.
Endpoint: https://f5tts.ailabsafrica.com
"""

import logging
import httpx
from typing import Optional, Union
import asyncio
import base64

logger = logging.getLogger(__name__)


class F5TTSService:
    """F5-TTS service wrapper for flow-matching based synthesis."""

    def __init__(self, endpoint: str = "https://f5tts.ailabsafrica.com"):
        """
        Initialize F5-TTS service.

        Args:
            endpoint (str): F5-TTS API endpoint
        """
        self.endpoint = endpoint
        self.timeout = 60.0  # Longer timeout for high-quality synthesis

    async def check_health(self) -> bool:
        """
        Check if F5-TTS service is healthy.

        Returns:
            bool: True if service is up, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.endpoint}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"F5-TTS health check failed: {e}")
            return False

    async def synthesize(
        self,
        text: str,
        language: str = "en",
        speed: float = 1.0,
        remove_silence: bool = True
    ) -> Optional[bytes]:
        """
        Synthesize speech using default voice.

        Args:
            text (str): Text to synthesize
            language (str): Language code (en, zh, ja, ko)
            speed (float): Speech speed multiplier (0.5 to 2.0)
            remove_silence (bool): Remove silence from generated audio

        Returns:
            Optional[bytes]: WAV audio bytes or None on error
        """
        try:
            # Normalize language
            language = language.lower()
            if language not in ["en", "zh", "ja", "ko"]:
                logger.warning(f"Language {language} may not be supported, using en")
                language = "en"

            # Validate speed
            speed = max(0.5, min(2.0, speed))

            logger.info(f"🎙️ F5-TTS synthesizing: lang={language}, speed={speed}")

            payload = {
                "text": text,
                "language": language,
                "speed": speed,
                "remove_silence": remove_silence
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.endpoint}/synthesize",
                    json=payload
                )

                if response.status_code == 200:
                    audio_bytes = response.content
                    logger.info(f"✅ F5-TTS generated {len(audio_bytes)} bytes of audio")
                    return audio_bytes
                else:
                    logger.error(f"❌ F5-TTS error: {response.status_code} - {response.text}")
                    return None

        except asyncio.TimeoutError:
            logger.error("❌ F5-TTS request timeout")
            return None
        except Exception as e:
            logger.error(f"❌ F5-TTS synthesis error: {e}")
            return None

    async def synthesize_with_reference(
        self,
        text: str,
        reference_audio: Union[bytes, str],
        reference_text: str = "",
        language: str = "en",
        speed: float = 1.0,
        remove_silence: bool = True
    ) -> Optional[bytes]:
        """
        Synthesize speech with voice cloning from reference audio.

        Args:
            text (str): Text to synthesize
            reference_audio (Union[bytes, str]): Reference audio bytes or base64 string
            reference_text (str): Transcription of reference audio (optional but recommended)
            language (str): Language code (en, zh, ja, ko)
            speed (float): Speech speed multiplier (0.5 to 2.0)
            remove_silence (bool): Remove silence from generated audio

        Returns:
            Optional[bytes]: WAV audio bytes or None on error
        """
        try:
            logger.info(f"🎨 F5-TTS voice cloning for: '{text[:50]}...'")

            # Prepare reference audio
            if isinstance(reference_audio, str):
                # Assume base64 encoded
                reference_audio = base64.b64decode(reference_audio)

            # Normalize language
            language = language.lower()
            if language not in ["en", "zh", "ja", "ko"]:
                logger.warning(f"Language {language} may not be supported, using en")
                language = "en"

            # Validate speed
            speed = max(0.5, min(2.0, speed))

            # Prepare multipart form data
            files = {
                "reference_audio": ("reference.wav", reference_audio, "audio/wav")
            }

            data = {
                "text": text,
                "reference_text": reference_text,
                "language": language,
                "speed": speed,
                "remove_silence": str(remove_silence).lower()
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.endpoint}/synthesize_with_reference",
                    files=files,
                    data=data
                )

                if response.status_code == 200:
                    audio_bytes = response.content
                    logger.info(f"✅ F5-TTS cloned voice: {len(audio_bytes)} bytes")
                    return audio_bytes
                else:
                    logger.error(f"❌ F5-TTS clone error: {response.status_code} - {response.text}")
                    return None

        except asyncio.TimeoutError:
            logger.error("❌ F5-TTS clone request timeout")
            return None
        except Exception as e:
            logger.error(f"❌ F5-TTS clone error: {e}")
            return None

    async def get_model_info(self) -> dict:
        """
        Get F5-TTS model information.

        Returns:
            dict: Model information
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.endpoint}/")

                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "service": "F5-TTS",
                        "model": "F5-TTS v1 Base (335M parameters)",
                        "description": "Flow-matching TTS with zero-shot voice cloning"
                    }
        except Exception as e:
            logger.error(f"Error fetching F5-TTS info: {e}")
            return {
                "service": "F5-TTS",
                "model": "F5-TTS v1 Base (335M parameters)",
                "description": "Flow-matching TTS with zero-shot voice cloning"
            }

    def get_supported_languages(self) -> list:
        """
        Get list of supported language codes.

        Returns:
            list: List of language codes
        """
        return ["en", "zh", "ja", "ko"]


# Singleton instance
_f5tts_service = None


def get_f5tts_service() -> F5TTSService:
    """
    Get singleton F5-TTS service instance.

    Returns:
        F5TTSService: The F5-TTS service
    """
    global _f5tts_service
    if _f5tts_service is None:
        _f5tts_service = F5TTSService()
    return _f5tts_service
