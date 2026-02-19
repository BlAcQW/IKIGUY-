#!/usr/bin/env python3
"""
Kokoro-82M TTS Service (Client)
Lightweight, fast TTS with high-quality audio.
Model: hexgrad/Kokoro-82M (82M parameters)
Endpoint: http://localhost:8010
Sample Rate: 24kHz
Languages: English (American & British accents)

Usage:
    from apps.shared.integration.ai_services import get_kokoro_service

    # Get singleton instance
    service = get_kokoro_service()

    # Blocking synthesis
    audio_bytes = await service.synthesize(
        text="Hello from Kokoro!",
        voice="af_heart",  # Female American voice
        speed=1.0
    )

    # Streaming synthesis (sentence-level)
    async for wav_chunk in service.stream_synthesize(
        text="This is a longer text. It will be streamed sentence by sentence.",
        voice="am_adam",  # Male American voice
        speed=1.0
    ):
        # Process chunk (WAV bytes)
        pass
"""

import aiohttp
import io
import logging
import os
from typing import AsyncGenerator, Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class KokoroService:
    """
    Kokoro-82M client for lightweight, high-quality TTS.

    Features:
    - 24kHz sample rate (high quality)
    - Lightweight model (82M parameters)
    - Fast inference
    - Multiple voices (American & British English)
    - Sentence-level streaming
    """

    # Available voices
    VOICES = {
        # American English voices
        "af_heart": "Heart (female, American)",
        "af_bella": "Bella (female, American)",
        "af_nicole": "Nicole (female, American)",
        "af_sarah": "Sarah (female, American)",
        "af_sky": "Sky (female, American)",
        "am_adam": "Adam (male, American)",
        "am_michael": "Michael (male, American)",
        # British English voices
        "bf_emma": "Emma (female, British)",
        "bf_isabella": "Isabella (female, British)",
        "bm_george": "George (male, British)",
        "bm_lewis": "Lewis (male, British)"
    }

    def __init__(
        self,
        endpoint: str = None,
        timeout: int = 120
    ):
        """
        Initialize Kokoro service.

        Args:
            endpoint: Kokoro server URL (default: env var KOKORO_ENDPOINT or localhost:8010)
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint or os.getenv(
            "KOKORO_ENDPOINT",
            "http://localhost:8010"
        )
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        logger.info(f"KokoroService initialized: {self.endpoint}")

    async def synthesize(
        self,
        text: str,
        voice: str = "af_heart",
        speed: float = 1.0,
        pitch: float = 1.0
    ) -> bytes:
        """
        Synthesize speech from text (blocking mode).

        Args:
            text: Text to synthesize
            voice: Voice ID (see VOICES dict for options)
            speed: Speech speed (0.5-2.0, default 1.0)
            pitch: Pitch adjustment (0.5-2.0, default 1.0)

        Returns:
            WAV audio bytes (24kHz)
        """
        url = f"{self.endpoint}/synthesize"
        payload = {
            "text": text,
            "voice": voice,
            "speed": speed,
            "pitch": pitch
        }

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            try:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"Kokoro synthesis failed: {response.status} - {error_text}"
                        )

                    audio_data = await response.read()
                    logger.info(
                        f"Kokoro synthesized {len(audio_data)} bytes "
                        f"for text: '{text[:50]}...'"
                    )
                    return audio_data

            except aiohttp.ClientError as e:
                logger.error(f"Kokoro request error: {e}")
                raise Exception(f"Failed to connect to Kokoro service: {e}")

    async def stream_synthesize(
        self,
        text: str,
        voice: str = "af_heart",
        speed: float = 1.0,
        pitch: float = 1.0
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream synthesized speech sentence-by-sentence.

        Args:
            text: Text to synthesize
            voice: Voice ID (see VOICES dict for options)
            speed: Speech speed (0.5-2.0)
            pitch: Pitch adjustment (0.5-2.0)

        Yields:
            WAV audio chunks (one per sentence)
        """
        url = f"{self.endpoint}/synthesize/stream"
        payload = {
            "text": text,
            "voice": voice,
            "speed": speed,
            "pitch": pitch
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Kokoro streaming failed: {response.status} - {error_text}")
                        # Fallback to blocking mode
                        logger.warning("Falling back to blocking synthesis")
                        audio = await self.synthesize(
                            text=text,
                            voice=voice,
                            speed=speed,
                            pitch=pitch
                        )
                        yield audio
                        return

                    # Stream chunks
                    chunk_count = 0
                    async for chunk in response.content.iter_chunked(8192):
                        if chunk:
                            chunk_count += 1
                            logger.debug(f"Kokoro chunk {chunk_count}: {len(chunk)} bytes")
                            yield chunk

                    logger.info(f"Kokoro streaming complete: {chunk_count} chunks")

        except aiohttp.ClientError as e:
            logger.error(f"Kokoro streaming error: {e}")
            # Fallback to blocking mode on error
            logger.warning("Falling back to blocking synthesis due to error")
            audio = await self.synthesize(
                text=text,
                voice=voice,
                speed=speed,
                pitch=pitch
            )
            yield audio

    async def get_voices(self) -> List[Dict[str, str]]:
        """
        Get available voices from the server.

        Returns:
            List of voice dictionaries with id and name
        """
        url = f"{self.endpoint}/voices"

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.warning("Failed to fetch voices from server, using default list")
                        return [
                            {"id": voice_id, "name": desc}
                            for voice_id, desc in self.VOICES.items()
                        ]

                    data = await response.json()
                    return data.get("voices", [])

            except Exception as e:
                logger.error(f"Error fetching voices: {e}")
                # Return default voices
                return [
                    {"id": voice_id, "name": desc}
                    for voice_id, desc in self.VOICES.items()
                ]

    @staticmethod
    def get_native_sample_rate() -> int:
        """
        Get the native sample rate for Kokoro-82M.

        Returns:
            Native sample rate in Hz (24000)
        """
        return 24000

    @staticmethod
    def list_voices() -> Dict[str, str]:
        """
        Get the default voice list.

        Returns:
            Dictionary of voice_id -> description
        """
        return KokoroService.VOICES.copy()


# Singleton instance
_kokoro_service: Optional[KokoroService] = None


def get_kokoro_service() -> KokoroService:
    """
    Get or create the singleton KokoroService instance.

    Returns:
        KokoroService instance
    """
    global _kokoro_service
    if _kokoro_service is None:
        _kokoro_service = KokoroService()
    return _kokoro_service
