"""
VoxCPM TTS Service - Context-aware TTS with voice cloning via TTS-WebUI on RunPod

VoxCPM is part of the CPM (Chinese Pre-trained Model) family with:
- Context-aware speech synthesis
- Voice cloning capabilities
- Multi-language support (English, Chinese)
- Running on RunPod GPU via TTS-WebUI
"""

import logging
import asyncio
import aiohttp
from typing import Optional, AsyncGenerator

logger = logging.getLogger(__name__)


class VoxCPMService:
    """
    VoxCPM TTS service client for context-aware speech synthesis.

    Features:
    - Context-aware TTS with natural prosody
    - Voice cloning from reference audio
    - Multi-language support
    - Streaming synthesis
    """

    def __init__(
        self,
        endpoint: str = "https://jzfmzviw26huka-8016.proxy.runpod.net",
        timeout: int = 60
    ):
        """
        Initialize VoxCPM service.

        Args:
            endpoint: TTS-WebUI endpoint URL
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def synthesize(
        self,
        text: str,
        language: str = "en",
        speaker: Optional[str] = None,
        speed: float = 1.0
    ) -> bytes:
        """
        Synthesize speech using VoxCPM (blocking mode).

        Args:
            text: Text to synthesize
            language: Language code (en, zh)
            speaker: Optional speaker ID
            speed: Speech speed multiplier (0.5-2.0)

        Returns:
            WAV audio bytes
        """
        url = f"{self.endpoint}/synthesize"
        payload = {
            "text": text,
            "language": language,
            "model": "voxcpm",
            "speed": speed
        }

        if speaker:
            payload["speaker"] = speaker

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"VoxCPM synthesis failed: {response.status} - {error_text}")
                        raise RuntimeError(f"VoxCPM synthesis failed: {error_text}")

                    audio = await response.read()
                    logger.info(f"VoxCPM synthesis complete: {len(audio)} bytes")
                    return audio

        except aiohttp.ClientError as e:
            logger.error(f"VoxCPM synthesis error: {e}")
            raise

    async def stream_synthesize(
        self,
        text: str,
        language: str = "en",
        speaker: Optional[str] = None,
        speed: float = 1.0
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream synthesized speech sentence-by-sentence.

        Args:
            text: Text to synthesize
            language: Language code (en, zh)
            speaker: Optional speaker ID
            speed: Speech speed multiplier

        Yields:
            WAV audio chunks (one per sentence)
        """
        url = f"{self.endpoint}/synthesize/stream"
        payload = {
            "text": text,
            "language": language,
            "model": "voxcpm",
            "speed": speed
        }

        if speaker:
            payload["speaker"] = speaker

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"VoxCPM streaming failed: {response.status} - {error_text}")
                        # Fallback to blocking mode
                        logger.warning("Falling back to blocking synthesis")
                        audio = await self.synthesize(
                            text=text,
                            language=language,
                            speaker=speaker,
                            speed=speed
                        )
                        yield audio
                        return

                    # Stream chunks
                    chunk_count = 0
                    async for chunk in response.content.iter_chunked(8192):
                        if chunk:
                            chunk_count += 1
                            logger.debug(f"VoxCPM chunk {chunk_count}: {len(chunk)} bytes")
                            yield chunk

                    logger.info(f"VoxCPM streaming complete: {chunk_count} chunks")

        except aiohttp.ClientError as e:
            logger.error(f"VoxCPM streaming error: {e}")
            # Fallback to blocking mode on error
            logger.warning("Falling back to blocking synthesis due to error")
            audio = await self.synthesize(
                text=text,
                language=language,
                speaker=speaker,
                speed=speed
            )
            yield audio

    async def clone_voice(
        self,
        text: str,
        reference_audio: bytes,
        language: str = "en",
        speed: float = 1.0
    ) -> bytes:
        """
        Synthesize speech with voice cloning from reference audio.

        Args:
            text: Text to synthesize
            reference_audio: Reference audio WAV bytes
            language: Language code
            speed: Speech speed multiplier

        Returns:
            WAV audio bytes with cloned voice
        """
        url = f"{self.endpoint}/clone"

        # Prepare multipart form data
        form_data = aiohttp.FormData()
        form_data.add_field("text", text)
        form_data.add_field("language", language)
        form_data.add_field("model", "voxcpm")
        form_data.add_field("speed", str(speed))
        form_data.add_field(
            "reference_audio",
            reference_audio,
            filename="reference.wav",
            content_type="audio/wav"
        )

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, data=form_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"VoxCPM voice cloning failed: {response.status} - {error_text}")
                        raise RuntimeError(f"VoxCPM voice cloning failed: {error_text}")

                    audio = await response.read()
                    logger.info(f"VoxCPM voice cloning complete: {len(audio)} bytes")
                    return audio

        except aiohttp.ClientError as e:
            logger.error(f"VoxCPM voice cloning error: {e}")
            raise

    @staticmethod
    def get_native_sample_rate() -> int:
        """
        Get the native sample rate for VoxCPM.

        Returns:
            Native sample rate in Hz (24000)
        """
        return 24000


# Singleton instance
_voxcpm_service: Optional[VoxCPMService] = None


def get_voxcpm_service() -> VoxCPMService:
    """
    Get or create the singleton VoxCPMService instance.

    Returns:
        VoxCPMService instance
    """
    global _voxcpm_service
    if _voxcpm_service is None:
        _voxcpm_service = VoxCPMService()
    return _voxcpm_service
