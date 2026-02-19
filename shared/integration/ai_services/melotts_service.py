#!/usr/bin/env python3
"""
MeloTTS Service (Client)
Fast multilingual TTS with streaming support.

Endpoint: https://melotts.ailabsafrica.com
Sample Rate: 44.1kHz (CD quality)
Languages: EN, ES, FR, ZH, JP, KR

Usage:
    from apps.shared.integration.ai_services import get_melotts_service

    # Blocking mode
    service = get_melotts_service()
    audio_bytes = await service.synthesize(
        text="Hello world",
        language="EN",
        speaker_id=0
    )

    # Streaming mode
    async for audio_chunk in service.stream_synthesize(
        text="Hello world",
        language="EN"
    ):
        # Send chunk to client
        await websocket.send(audio_chunk)
"""

import logging
import httpx
import re
from typing import Optional, Dict, Any, AsyncGenerator
import asyncio

logger = logging.getLogger(__name__)


class MeloTTSService:
    """
    MeloTTS service wrapper for fast multilingual synthesis.

    Features:
    - 6 languages: EN, ES, FR, ZH, JP, KR
    - 44.1kHz sample rate (CD quality)
    - Blocking and streaming synthesis modes
    - Multiple speakers per language
    """

    def __init__(self, endpoint: str = "https://melotts.ailabsafrica.com"):
        """
        Initialize MeloTTS service.

        Args:
            endpoint (str): MeloTTS API endpoint
        """
        self.endpoint = endpoint
        self.timeout = 30.0
        self.sample_rate = 44100  # CD quality, matches Parler-TTS

        # Language mappings (2-letter to uppercase)
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

    def _normalize_language(self, language: str) -> str:
        """
        Normalize language code to uppercase format.

        Args:
            language: Language code (en/EN/english)

        Returns:
            str: Uppercase language code (EN, ES, etc.)
        """
        language = language.upper()
        if language not in self.language_map.values():
            # Try mapping from 2-letter code
            language = self.language_map.get(language.lower(), "EN")
        return language

    def _validate_speaker(self, language: str, speaker_id: int) -> int:
        """
        Validate and clamp speaker ID to valid range.

        Args:
            language: Language code (EN, ES, etc.)
            speaker_id: Requested speaker ID

        Returns:
            int: Valid speaker ID (0 if out of range)
        """
        max_speakers = self.speaker_ranges.get(language, 1)
        if speaker_id >= max_speakers:
            logger.warning(f"Speaker ID {speaker_id} out of range for {language}, using 0")
            return 0
        return speaker_id

    def _split_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences for streaming.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        # Filter out empty strings
        sentences = [s.strip() for s in sentences if s.strip()]

        # If no sentence boundaries found, split by length
        if len(sentences) == 0 or (len(sentences) == 1 and len(sentences[0]) > 200):
            # Split long text into chunks
            words = text.split()
            sentences = []
            current = []
            for word in words:
                current.append(word)
                if len(' '.join(current)) > 100:
                    sentences.append(' '.join(current))
                    current = []
            if current:
                sentences.append(' '.join(current))

        logger.debug(f"📝 Split text into {len(sentences)} sentences")
        return sentences

    async def synthesize(
        self,
        text: str,
        language: str = "EN",
        speaker_id: int = 0,
        speed: float = 1.0
    ) -> Optional[bytes]:
        """
        Synthesize speech using MeloTTS (blocking mode).

        Args:
            text (str): Text to synthesize
            language (str): Language code (EN, ES, FR, ZH, JP, KR)
            speaker_id (int): Speaker voice ID (0-based, varies by language)
            speed (float): Speech speed multiplier (0.5 to 2.0)

        Returns:
            Optional[bytes]: WAV audio bytes (44.1kHz) or None on error
        """
        try:
            # Normalize language code
            language = self._normalize_language(language)

            # Validate speaker_id
            speaker_id = self._validate_speaker(language, speaker_id)

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

    async def stream_synthesize(
        self,
        text: str,
        language: str = "EN",
        speaker_id: int = 0,
        speed: float = 1.0
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream synthesize speech using MeloTTS.

        Yields audio chunks as they're generated for real-time playback.
        Requires server-side /synthesize/stream endpoint.

        Args:
            text (str): Text to synthesize
            language (str): Language code (EN, ES, FR, ZH, JP, KR)
            speaker_id (int): Speaker voice ID (0-based, varies by language)
            speed (float): Speech speed multiplier (0.5 to 2.0)

        Yields:
            bytes: WAV audio chunks (44.1kHz) as they arrive
        """
        # Normalize language code
        language = self._normalize_language(language)

        # Validate speaker_id
        speaker_id = self._validate_speaker(language, speaker_id)

        # Validate speed
        speed = max(0.5, min(2.0, speed))

        # Split text into sentences for streaming
        sentences = self._split_sentences(text)

        logger.info(f"🎙️ MeloTTS streaming: {len(sentences)} sentences, lang={language}")

        # Stream each sentence
        for i, sentence in enumerate(sentences):
            logger.debug(f"🔊 MeloTTS synthesizing sentence {i+1}/{len(sentences)}: {sentence[:50]}...")

            try:
                payload = {
                    "text": sentence,
                    "language": language,
                    "speaker_id": speaker_id,
                    "speed": speed
                }

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    # Try streaming endpoint first
                    async with client.stream(
                        "POST",
                        f"{self.endpoint}/synthesize/stream",
                        json=payload
                    ) as response:
                        if response.status_code == 200:
                            # Stream chunks from server
                            async for chunk in response.aiter_bytes(chunk_size=8192):
                                if chunk:
                                    yield chunk
                            logger.debug(f"✅ Sentence {i+1} streamed")
                        else:
                            # Fallback to blocking mode for this sentence
                            logger.warning(
                                f"⚠️  MeloTTS stream endpoint not available ({response.status_code}), "
                                f"falling back to blocking mode for sentence {i+1}"
                            )

                            # Use blocking synthesis as fallback
                            audio_bytes = await self.synthesize(
                                text=sentence,
                                language=language,
                                speaker_id=speaker_id,
                                speed=speed
                            )

                            if audio_bytes:
                                yield audio_bytes

            except Exception as e:
                logger.error(f"❌ Error streaming sentence {i+1}: {e}")
                # Continue with next sentence instead of failing completely
                continue

        logger.info(f"🎉 MeloTTS streaming complete: {len(sentences)} sentences")

    def get_native_sample_rate(self) -> int:
        """
        Get the model's native sample rate.

        Returns:
            int: Sample rate in Hz (44100)
        """
        return self.sample_rate

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
            list: List of language codes (EN, ES, FR, ZH, JP, KR)
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
        logger.info("🎙️  Creating new MeloTTSService instance")
        _melotts_service = MeloTTSService()
    return _melotts_service


__all__ = [
    'MeloTTSService',
    'get_melotts_service'
]
