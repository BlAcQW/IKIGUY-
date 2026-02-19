#!/usr/bin/env python3
"""
MeloTTS Service
Fast multilingual TTS with 6 language support.
Endpoint: https://melotts.ailabsafrica.com
"""

import logging
import httpx
from typing import Optional, Dict, Any
import asyncio

logger = logging.getLogger(__name__)


class MeloTTSService:
    """MeloTTS service wrapper for fast multilingual synthesis."""

    def __init__(self, endpoint: str = "https://melotts.ailabsafrica.com"):
        """
        Initialize MeloTTS service.

        Args:
            endpoint (str): MeloTTS API endpoint
        """
        self.endpoint = endpoint
        self.timeout = 30.0

        # Language mappings
        self.language_map = {
            "en": "EN",
            "es": "ES",
            "fr": "FR",
            "zh": "ZH",
            "jp": "JP",
            "kr": "KR"
        }

        # Speaker IDs per language (0-based)
        self.speaker_ranges = {
            "EN": 8,  # 0-7
            "ES": 4,  # 0-3
            "FR": 4,  # 0-3
            "ZH": 8,  # 0-7
            "JP": 4,  # 0-3
            "KR": 4,  # 0-3
        }

    async def check_health(self) -> bool:
        """
        Check if MeloTTS service is healthy.

        Returns:
            bool: True if service is up, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.endpoint}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"MeloTTS health check failed: {e}")
            return False

    async def synthesize(
        self,
        text: str,
        language: str = "EN",
        speaker_id: int = 0,
        speed: float = 1.0
    ) -> Optional[bytes]:
        """
        Synthesize speech using MeloTTS.

        Args:
            text (str): Text to synthesize
            language (str): Language code (EN, ES, FR, ZH, JP, KR)
            speaker_id (int): Speaker voice ID (0-based, varies by language)
            speed (float): Speech speed multiplier (0.5 to 2.0)

        Returns:
            Optional[bytes]: WAV audio bytes or None on error
        """
        try:
            # Normalize language code
            language = language.upper()
            if language not in self.language_map.values():
                # Try mapping from 2-letter code
                language = self.language_map.get(language.lower(), "EN")

            # Validate speaker_id
            max_speakers = self.speaker_ranges.get(language, 1)
            if speaker_id >= max_speakers:
                logger.warning(f"Speaker ID {speaker_id} out of range for {language}, using 0")
                speaker_id = 0

            # Validate speed
            speed = max(0.5, min(2.0, speed))

            logger.info(f"🎙️ MeloTTS synthesizing: lang={language}, speaker={speaker_id}, speed={speed}")

            # Prepare request
            payload = {
                "text": text,
                "language": language,
                "speaker_id": speaker_id,
                "speed": speed
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.endpoint}/synthesize",
                    json=payload
                )

                if response.status_code == 200:
                    audio_bytes = response.content
                    logger.info(f"✅ MeloTTS generated {len(audio_bytes)} bytes of audio")
                    return audio_bytes
                else:
                    logger.error(f"❌ MeloTTS error: {response.status_code} - {response.text}")
                    return None

        except asyncio.TimeoutError:
            logger.error("❌ MeloTTS request timeout")
            return None
        except Exception as e:
            logger.error(f"❌ MeloTTS synthesis error: {e}")
            return None

    async def get_voices(self) -> Dict[str, Any]:
        """
        Get available voices for all languages.

        Returns:
            Dict[str, Any]: Dictionary of language -> speaker info
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.endpoint}/voices")

                if response.status_code == 200:
                    return response.json()
                else:
                    # Return default mapping if endpoint not available
                    return {
                        lang: {"speakers": list(range(count))}
                        for lang, count in self.speaker_ranges.items()
                    }
        except Exception as e:
            logger.error(f"Error fetching MeloTTS voices: {e}")
            return {
                lang: {"speakers": list(range(count))}
                for lang, count in self.speaker_ranges.items()
            }

    def get_supported_languages(self) -> list:
        """
        Get list of supported language codes.

        Returns:
            list: List of language codes
        """
        return list(self.language_map.values())


# Singleton instance
_melotts_service = None


def get_melotts_service() -> MeloTTSService:
    """
    Get singleton MeloTTS service instance.

    Returns:
        MeloTTSService: The MeloTTS service
    """
    global _melotts_service
    if _melotts_service is None:
        _melotts_service = MeloTTSService()
    return _melotts_service
