#!/usr/bin/env python3
"""
F5-TTS Service (Client)
Flow-matching based TTS with zero-shot voice cloning and streaming support.

Endpoint: https://f5tts.ailabsafrica.com
Sample Rate: 24kHz
Languages: en, zh, ja, ko

Usage:
    from apps.shared.integration.ai_services import get_f5tts_service

    # Blocking mode
    service = get_f5tts_service()
    audio_bytes = await service.synthesize(
        text="Hello world",
        language="en"
    )

    # Streaming mode
    async for audio_chunk in service.stream_synthesize(
        text="Hello world",
        language="en"
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


class F5TTSService:
    """
    F5-TTS service wrapper for flow-matching based synthesis.

    Features:
    - Zero-shot voice cloning
    - 4 languages: en, zh, ja, ko
    - 24kHz sample rate
    - Blocking and streaming synthesis modes
    """

    def __init__(self, endpoint: str = "https://f5tts.ailabsafrica.com"):
        """
        Initialize F5-TTS service.

        Args:
            endpoint (str): F5-TTS API endpoint
        """
        self.endpoint = endpoint
        self.timeout = 60.0  # Longer timeout for high-quality synthesis
        self.sample_rate = 24000  # F5-TTS native sample rate

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
        language: str = "en",
        speed: float = 1.0,
        remove_silence: bool = True
    ) -> Optional[bytes]:
        """
        Synthesize speech using default voice (blocking mode).

        Args:
            text (str): Text to synthesize
            language (str): Language code (en, zh, ja, ko)
            speed (float): Speech speed multiplier (0.5 to 2.0)
            remove_silence (bool): Remove silence from generated audio

        Returns:
            Optional[bytes]: WAV audio bytes (24kHz) or None on error
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

    async def stream_synthesize(
        self,
        text: str,
        language: str = "en",
        speed: float = 1.0,
        remove_silence: bool = True
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream synthesize speech, sentence by sentence.

        Yields audio chunks as they're generated for real-time playback.
        Requires server-side /synthesize/stream endpoint.

        Args:
            text (str): Text to synthesize
            language (str): Language code (en, zh, ja, ko)
            speed (float): Speech speed multiplier (0.5 to 2.0)
            remove_silence (bool): Remove silence from generated audio

        Yields:
            bytes: WAV audio chunks (24kHz) as they arrive
        """
        # Normalize language
        language = language.lower()
        if language not in ["en", "zh", "ja", "ko"]:
            logger.warning(f"Language {language} may not be supported, using en")
            language = "en"

        # Validate speed
        speed = max(0.5, min(2.0, speed))

        # Split text into sentences for streaming
        sentences = self._split_sentences(text)

        logger.info(f"🎙️ F5-TTS streaming: {len(sentences)} sentences, lang={language}")

        # Stream each sentence
        for i, sentence in enumerate(sentences):
            logger.debug(f"🔊 F5-TTS synthesizing sentence {i+1}/{len(sentences)}: {sentence[:50]}...")

            try:
                payload = {
                    "text": sentence,
                    "language": language,
                    "speed": speed,
                    "remove_silence": remove_silence
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
                                f"⚠️  F5-TTS stream endpoint not available ({response.status_code}), "
                                f"falling back to blocking mode for sentence {i+1}"
                            )

                            # Use blocking synthesis as fallback
                            audio_bytes = await self.synthesize(
                                text=sentence,
                                language=language,
                                speed=speed,
                                remove_silence=remove_silence
                            )

                            if audio_bytes:
                                yield audio_bytes

            except Exception as e:
                logger.error(f"❌ Error streaming sentence {i+1}: {e}")
                # Continue with next sentence instead of failing completely
                continue

        logger.info(f"🎉 F5-TTS streaming complete: {len(sentences)} sentences")

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

    def get_native_sample_rate(self) -> int:
        """
        Get the model's native sample rate.

        Returns:
            int: Sample rate in Hz (24000)
        """
        return self.sample_rate

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
        logger.info("🎙️  Creating new F5TTSService instance")
        _f5tts_service = F5TTSService()
    return _f5tts_service


__all__ = [
    'F5TTSService',
    'get_f5tts_service'
]
