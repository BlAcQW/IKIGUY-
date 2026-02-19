#!/usr/bin/env python3
"""
StyleTTS2 Service (Client)
High-quality expressive TTS with style transfer and voice cloning.
Endpoint: https://styletts2.ailabsafrica.com (RunPod)
Sample Rate: 24kHz
Languages: English (primary)

Usage:
    from apps.shared.integration.ai_services import StyleTTS2Service, get_styletts2_service

    # Get singleton instance
    service = get_styletts2_service()

    # Blocking synthesis
    audio_bytes = await service.synthesize(
        text="Hello from StyleTTS2!",
        alpha=0.3,  # Timbre control
        beta=0.7,   # Prosody control
        diffusion_steps=5
    )

    # Streaming synthesis (sentence-level)
    async for wav_chunk in service.stream_synthesize(
        text="This is a longer text that will be streamed. It has multiple sentences.",
        alpha=0.3,
        beta=0.7
    ):
        # Process chunk (WAV bytes)
        pass
"""

import aiohttp
import io
import logging
import os
from typing import AsyncGenerator, Optional, Dict, Any

logger = logging.getLogger(__name__)


class StyleTTS2Service:
    """
    StyleTTS2 client for high-quality expressive TTS.

    Features:
    - 24kHz sample rate (high quality)
    - Expressive speech with timbre and prosody control
    - Sentence-level streaming
    - Alpha (timbre) and Beta (prosody) controls
    """

    def __init__(
        self,
        endpoint: str = None,
        timeout: int = 120
    ):
        """
        Initialize StyleTTS2 service.

        Args:
            endpoint: StyleTTS2 server URL (default: env var STYLETTS2_ENDPOINT)
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint or os.getenv(
            "STYLETTS2_ENDPOINT",
            "https://styletts2.ailabsafrica.com"
        )
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        logger.info(f"StyleTTS2Service initialized: {self.endpoint}")

    async def synthesize(
        self,
        text: str,
        alpha: float = 0.3,
        beta: float = 0.7,
        diffusion_steps: int = 5,
        embedding_scale: float = 1.0,
        output_sample_rate: int = 24000
    ) -> bytes:
        """
        Synthesize speech from text (blocking mode).

        Args:
            text: Text to synthesize
            alpha: Timbre control (0-1, higher = more text-aligned)
            beta: Prosody control (0-1, higher = more text-aligned)
            diffusion_steps: Number of diffusion steps (higher = better quality but slower)
            embedding_scale: Style conditioning strength
            output_sample_rate: Output sample rate in Hz

        Returns:
            WAV audio bytes (24kHz by default)
        """
        url = f"{self.endpoint}/synthesize"
        payload = {
            "text": text,
            "alpha": alpha,
            "beta": beta,
            "diffusion_steps": diffusion_steps,
            "embedding_scale": embedding_scale,
            "output_sample_rate": output_sample_rate
        }

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            try:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"StyleTTS2 synthesis failed: {response.status} - {error_text}"
                        )

                    audio_data = await response.read()
                    logger.info(
                        f"StyleTTS2 synthesized {len(audio_data)} bytes "
                        f"for text: '{text[:50]}...'"
                    )
                    return audio_data

            except aiohttp.ClientError as e:
                logger.error(f"StyleTTS2 request error: {e}")
                raise Exception(f"Failed to connect to StyleTTS2 service: {e}")

    async def stream_synthesize(
        self,
        text: str,
        alpha: float = 0.3,
        beta: float = 0.7,
        diffusion_steps: int = 5,
        embedding_scale: float = 1.0,
        output_sample_rate: int = 24000
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream synthesized speech sentence-by-sentence.

        Args:
            text: Text to synthesize
            alpha: Timbre control (0-1)
            beta: Prosody control (0-1)
            diffusion_steps: Number of diffusion steps
            embedding_scale: Style conditioning strength
            output_sample_rate: Output sample rate in Hz

        Yields:
            WAV audio chunks (one per sentence)
        """
        url = f"{self.endpoint}/synthesize/stream"
        payload = {
            "text": text,
            "alpha": alpha,
            "beta": beta,
            "diffusion_steps": diffusion_steps,
            "embedding_scale": embedding_scale,
            "output_sample_rate": output_sample_rate
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"StyleTTS2 streaming failed: {response.status} - {error_text}")
                        # Fallback to blocking mode
                        logger.warning("Falling back to blocking synthesis")
                        audio = await self.synthesize(
                            text=text,
                            alpha=alpha,
                            beta=beta,
                            diffusion_steps=diffusion_steps,
                            embedding_scale=embedding_scale,
                            output_sample_rate=output_sample_rate
                        )
                        yield audio
                        return

                    # Stream chunks
                    chunk_count = 0
                    async for chunk in response.content.iter_chunked(8192):
                        if chunk:
                            chunk_count += 1
                            logger.debug(f"StyleTTS2 chunk {chunk_count}: {len(chunk)} bytes")
                            yield chunk

                    logger.info(f"StyleTTS2 streaming complete: {chunk_count} chunks")

        except aiohttp.ClientError as e:
            logger.error(f"StyleTTS2 streaming error: {e}")
            # Fallback to blocking mode on error
            logger.warning("Falling back to blocking synthesis due to error")
            audio = await self.synthesize(
                text=text,
                alpha=alpha,
                beta=beta,
                diffusion_steps=diffusion_steps,
                embedding_scale=embedding_scale,
                output_sample_rate=output_sample_rate
            )
            yield audio

    async def clone_voice(
        self,
        text: str,
        reference_audio_path: str,
        alpha: float = 0.3,
        beta: float = 0.7,
        diffusion_steps: int = 5,
        embedding_scale: float = 1.0,
        output_sample_rate: int = 24000
    ) -> bytes:
        """
        Clone a voice from reference audio and synthesize text.

        Args:
            text: Text to synthesize
            reference_audio_path: Path to reference audio file
            alpha: Timbre control
            beta: Prosody control
            diffusion_steps: Number of diffusion steps
            embedding_scale: Style conditioning strength
            output_sample_rate: Output sample rate in Hz

        Returns:
            WAV audio bytes with cloned voice
        """
        url = f"{self.endpoint}/clone"

        # Prepare form data
        form_data = aiohttp.FormData()
        form_data.add_field("text", text)
        form_data.add_field("alpha", str(alpha))
        form_data.add_field("beta", str(beta))
        form_data.add_field("diffusion_steps", str(diffusion_steps))
        form_data.add_field("embedding_scale", str(embedding_scale))
        form_data.add_field("output_sample_rate", str(output_sample_rate))

        # Add reference audio file
        with open(reference_audio_path, "rb") as f:
            form_data.add_field(
                "reference_audio",
                f,
                filename=os.path.basename(reference_audio_path),
                content_type="audio/wav"
            )

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                try:
                    async with session.post(url, data=form_data) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise Exception(
                                f"StyleTTS2 voice cloning failed: {response.status} - {error_text}"
                            )

                        audio_data = await response.read()
                        logger.info(
                            f"StyleTTS2 voice cloned: {len(audio_data)} bytes "
                            f"for text: '{text[:50]}...'"
                        )
                        return audio_data

                except aiohttp.ClientError as e:
                    logger.error(f"StyleTTS2 voice cloning error: {e}")
                    raise Exception(f"Failed to clone voice with StyleTTS2: {e}")

    @staticmethod
    def get_native_sample_rate() -> int:
        """
        Get the native sample rate for StyleTTS2.

        Returns:
            Native sample rate in Hz (24000)
        """
        return 24000


# Singleton instance
_styletts2_service: Optional[StyleTTS2Service] = None


def get_styletts2_service() -> StyleTTS2Service:
    """
    Get or create the singleton StyleTTS2Service instance.

    Returns:
        StyleTTS2Service instance
    """
    global _styletts2_service
    if _styletts2_service is None:
        _styletts2_service = StyleTTS2Service()
    return _styletts2_service
