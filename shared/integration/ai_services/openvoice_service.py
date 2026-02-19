#!/usr/bin/env python3
"""
OpenVoice Service (Client)
Voice cloning with tone and emotion control.

Endpoint: https://openvoice.ailabsafrica.com (local Docker)
Sample Rate: 24kHz
Languages: EN, ZH

Usage:
    from apps.shared.integration.ai_services import get_openvoice_service

    # Blocking mode
    service = get_openvoice_service()
    audio_bytes = await service.synthesize(
        text="Hello world",
        language="EN"
    )

    # Voice cloning
    audio_bytes = await service.clone_voice(
        text="Hello world",
        reference_audio=audio_bytes,
        language="EN"
    )

    # Streaming mode
    async for audio_chunk in service.stream_synthesize(
        text="Hello world",
        language="EN"
    ):
        await websocket.send(audio_chunk)
"""

import logging
import httpx
import re
from typing import Optional, Union, AsyncGenerator
import asyncio
import base64

logger = logging.getLogger(__name__)


class OpenVoiceService:
    """
    OpenVoice service wrapper for voice cloning and tone conversion.

    Features:
    - Voice cloning with reference audio
    - Tone color conversion (cross-lingual)
    - 2 languages: EN, ZH
    - 24kHz sample rate
    - Blocking and streaming synthesis modes
    """

    def __init__(self, endpoint: str = "https://openvoice.ailabsafrica.com"):
        """
        Initialize OpenVoice service.

        Args:
            endpoint (str): OpenVoice API endpoint
        """
        self.endpoint = endpoint
        self.timeout = 60.0  # Longer timeout for voice cloning
        self.sample_rate = 24000  # OpenVoice native sample rate

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
        speed: float = 1.0
    ) -> Optional[bytes]:
        """
        Synthesize speech using default voice (blocking mode).

        Args:
            text (str): Text to synthesize
            language (str): Language code (EN or ZH)
            speed (float): Speech speed multiplier (0.5 to 2.0)

        Returns:
            Optional[bytes]: WAV audio bytes (24kHz) or None on error
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

    async def stream_synthesize(
        self,
        text: str,
        language: str = "EN",
        speed: float = 1.0
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream synthesize speech, sentence by sentence.

        Yields audio chunks as they're generated for real-time playback.
        Requires server-side /synthesize/stream endpoint.

        Args:
            text (str): Text to synthesize
            language (str): Language code (EN or ZH)
            speed (float): Speech speed multiplier (0.5 to 2.0)

        Yields:
            bytes: WAV audio chunks (24kHz) as they arrive
        """
        # Normalize language
        language = language.upper()
        if language not in ["EN", "ZH"]:
            logger.warning(f"Language {language} not supported, using EN")
            language = "EN"

        # Validate speed
        speed = max(0.5, min(2.0, speed))

        # Split text into sentences for streaming
        sentences = self._split_sentences(text)

        logger.info(f"🎙️ OpenVoice streaming: {len(sentences)} sentences, lang={language}")

        # Stream each sentence
        for i, sentence in enumerate(sentences):
            logger.debug(f"🔊 OpenVoice synthesizing sentence {i+1}/{len(sentences)}: {sentence[:50]}...")

            try:
                payload = {
                    "text": sentence,
                    "language": language,
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
                                f"⚠️  OpenVoice stream endpoint not available ({response.status_code}), "
                                f"falling back to blocking mode for sentence {i+1}"
                            )

                            # Use blocking synthesis as fallback
                            audio_bytes = await self.synthesize(
                                text=sentence,
                                language=language,
                                speed=speed
                            )

                            if audio_bytes:
                                yield audio_bytes

            except Exception as e:
                logger.error(f"❌ Error streaming sentence {i+1}: {e}")
                # Continue with next sentence instead of failing completely
                continue

        logger.info(f"🎉 OpenVoice streaming complete: {len(sentences)} sentences")

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

    def get_native_sample_rate(self) -> int:
        """
        Get the model's native sample rate.

        Returns:
            int: Sample rate in Hz (24000)
        """
        return self.sample_rate

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
            list: List of language codes (EN, ZH)
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
        logger.info("🎙️  Creating new OpenVoiceService instance")
        _openvoice_service = OpenVoiceService()
    return _openvoice_service


__all__ = [
    'OpenVoiceService',
    'get_openvoice_service'
]
