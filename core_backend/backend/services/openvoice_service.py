#!/usr/bin/env python3
"""
OpenVoice Service
Voice cloning with tone and emotion control.
Endpoint: https://openvoice.ailabsafrica.com
"""

import logging
import httpx
from typing import Optional, Union
import asyncio
import base64

logger = logging.getLogger(__name__)


class OpenVoiceService:
    """OpenVoice service wrapper for voice cloning and tone conversion."""

    def __init__(self, endpoint: str = "https://openvoice.ailabsafrica.com"):
        """
        Initialize OpenVoice service.

        Args:
            endpoint (str): OpenVoice API endpoint
        """
        self.endpoint = endpoint
        self.timeout = 60.0  # Longer timeout for voice cloning

    async def check_health(self) -> bool:
        """
        Check if OpenVoice service is healthy.

        Returns:
            bool: True if service is up, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.endpoint}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"OpenVoice health check failed: {e}")
            return False

    async def synthesize(
        self,
        text: str,
        language: str = "EN",
        speed: float = 1.0
    ) -> Optional[bytes]:
        """
        Synthesize speech using default voice (no voice cloning).

        Args:
            text (str): Text to synthesize
            language (str): Language code (EN or ZH)
            speed (float): Speech speed multiplier (0.5 to 2.0)

        Returns:
            Optional[bytes]: WAV audio bytes or None on error
        """
        try:
            # Normalize language
            language = language.upper()
            if language not in ["EN", "ZH"]:
                logger.warning(f"Language {language} not supported, using EN")
                language = "EN"

            # Validate speed
            speed = max(0.5, min(2.0, speed))

            logger.info(f"🎙️ OpenVoice synthesizing: lang={language}, speed={speed}")

            payload = {
                "text": text,
                "language": language,
                "speed": speed
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.endpoint}/synthesize",
                    json=payload
                )

                if response.status_code == 200:
                    audio_bytes = response.content
                    logger.info(f"✅ OpenVoice generated {len(audio_bytes)} bytes of audio")
                    return audio_bytes
                else:
                    logger.error(f"❌ OpenVoice error: {response.status_code} - {response.text}")
                    return None

        except asyncio.TimeoutError:
            logger.error("❌ OpenVoice request timeout")
            return None
        except Exception as e:
            logger.error(f"❌ OpenVoice synthesis error: {e}")
            return None

    async def clone_voice(
        self,
        text: str,
        reference_audio: Union[bytes, str],
        language: str = "EN",
        speed: float = 1.0
    ) -> Optional[bytes]:
        """
        Synthesize speech using voice cloning with reference audio.

        Args:
            text (str): Text to synthesize
            reference_audio (Union[bytes, str]): Reference audio bytes or base64 string
            language (str): Language code (EN or ZH)
            speed (float): Speech speed multiplier (0.5 to 2.0)

        Returns:
            Optional[bytes]: WAV audio bytes or None on error
        """
        try:
            logger.info(f"🎨 OpenVoice cloning voice for: '{text[:50]}...'")

            # Prepare reference audio
            if isinstance(reference_audio, str):
                # Assume base64 encoded
                reference_audio = base64.b64decode(reference_audio)

            # Normalize language
            language = language.upper()
            if language not in ["EN", "ZH"]:
                logger.warning(f"Language {language} not supported, using EN")
                language = "EN"

            # Validate speed
            speed = max(0.5, min(2.0, speed))

            # Prepare multipart form data
            files = {
                "reference_audio": ("reference.wav", reference_audio, "audio/wav")
            }

            data = {
                "text": text,
                "language": language,
                "speed": speed
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.endpoint}/clone",
                    files=files,
                    data=data
                )

                if response.status_code == 200:
                    audio_bytes = response.content
                    logger.info(f"✅ OpenVoice cloned voice: {len(audio_bytes)} bytes")
                    return audio_bytes
                else:
                    logger.error(f"❌ OpenVoice clone error: {response.status_code} - {response.text}")
                    return None

        except asyncio.TimeoutError:
            logger.error("❌ OpenVoice clone request timeout")
            return None
        except Exception as e:
            logger.error(f"❌ OpenVoice clone error: {e}")
            return None

    async def convert_tone(
        self,
        text: str,
        base_language: str,
        target_speaker: Union[bytes, str],
        target_language: str = None
    ) -> Optional[bytes]:
        """
        Convert tone color to match target speaker (cross-lingual).

        Args:
            text (str): Text to synthesize
            base_language (str): Source language (EN or ZH)
            target_speaker (Union[bytes, str]): Target speaker audio bytes or base64
            target_language (str): Target language (optional, defaults to base_language)

        Returns:
            Optional[bytes]: WAV audio bytes or None on error
        """
        try:
            logger.info(f"🔄 OpenVoice tone conversion: '{text[:50]}...'")

            # Prepare target speaker audio
            if isinstance(target_speaker, str):
                target_speaker = base64.b64decode(target_speaker)

            # Normalize languages
            base_language = base_language.upper()
            target_language = (target_language or base_language).upper()

            files = {
                "target_audio": ("target.wav", target_speaker, "audio/wav")
            }

            data = {
                "text": text,
                "base_language": base_language,
                "target_language": target_language
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.endpoint}/convert_tone",
                    files=files,
                    data=data
                )

                if response.status_code == 200:
                    audio_bytes = response.content
                    logger.info(f"✅ OpenVoice tone converted: {len(audio_bytes)} bytes")
                    return audio_bytes
                else:
                    logger.error(f"❌ OpenVoice tone convert error: {response.status_code} - {response.text}")
                    return None

        except asyncio.TimeoutError:
            logger.error("❌ OpenVoice tone convert timeout")
            return None
        except Exception as e:
            logger.error(f"❌ OpenVoice tone convert error: {e}")
            return None

    async def get_speakers(self) -> list:
        """
        Get list of available pre-loaded target speakers.

        Returns:
            list: List of speaker info dictionaries
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.endpoint}/speakers")

                if response.status_code == 200:
                    return response.json()
                else:
                    # Return default if endpoint not available
                    return [
                        {"id": "en-default", "name": "English Default", "language": "EN"},
                        {"id": "zh-default", "name": "Chinese Default", "language": "ZH"}
                    ]
        except Exception as e:
            logger.error(f"Error fetching OpenVoice speakers: {e}")
            return [
                {"id": "en-default", "name": "English Default", "language": "EN"},
                {"id": "zh-default", "name": "Chinese Default", "language": "ZH"}
            ]

    def get_supported_languages(self) -> list:
        """
        Get list of supported language codes.

        Returns:
            list: List of language codes
        """
        return ["EN", "ZH"]


# Singleton instance
_openvoice_service = None


def get_openvoice_service() -> OpenVoiceService:
    """
    Get singleton OpenVoice service instance.

    Returns:
        OpenVoiceService: The OpenVoice service
    """
    global _openvoice_service
    if _openvoice_service is None:
        _openvoice_service = OpenVoiceService()
    return _openvoice_service
