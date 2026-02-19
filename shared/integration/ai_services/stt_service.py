"""
Speech-to-Text (STT) Service.

Provides unified interface for STT providers:
- OpenAI Whisper
- Google Speech-to-Text
- Assembly AI
- Deepgram

Usage:
    stt_service = STTService(provider="openai", api_key="...")
    transcript = await stt_service.transcribe(audio_bytes)
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)


class STTProvider(str, Enum):
    """Available STT providers."""
    OPENAI = "openai"  # OpenAI Whisper
    GOOGLE = "google"  # Google Speech-to-Text
    ASSEMBLYAI = "assemblyai"  # Assembly AI
    DEEPGRAM = "deepgram"  # Deepgram


class STTService:
    """
    Speech-to-Text service with multi-provider support.

    Supports:
    - OpenAI Whisper (default)
    - Google Speech-to-Text
    - Assembly AI
    - Deepgram
    """

    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        language: str = "en",
        **kwargs
    ):
        """
        Initialize STT service.

        Args:
            provider: STT provider name
            api_key: API key for the provider
            model: Model name (provider-specific)
            language: Language code (ISO 639-1)
            **kwargs: Additional provider-specific parameters
        """
        self.provider = STTProvider(provider.lower())
        self.api_key = api_key
        self.language = language
        self.kwargs = kwargs

        # Provider-specific configuration
        if self.provider == STTProvider.OPENAI:
            self.model = model or "whisper-1"
            self.api_url = "https://api.openai.com/v1/audio/transcriptions"
        elif self.provider == STTProvider.GOOGLE:
            self.model = model or "default"
            self.api_url = "https://speech.googleapis.com/v1/speech:recognize"
        elif self.provider == STTProvider.ASSEMBLYAI:
            self.model = model or "best"
            self.api_url = "https://api.assemblyai.com/v2/transcript"
        elif self.provider == STTProvider.DEEPGRAM:
            self.model = model or "nova-2"
            self.api_url = "https://api.deepgram.com/v1/listen"

        logger.info(f"Initialized STTService with provider={self.provider}, model={self.model}")

    async def transcribe(
        self,
        audio_bytes: bytes,
        audio_format: str = "webm",
        **options
    ) -> str:
        """
        Transcribe audio to text.

        Args:
            audio_bytes: Audio file bytes
            audio_format: Audio format (webm, mp3, wav, etc.)
            **options: Provider-specific options

        Returns:
            Transcribed text

        Raises:
            Exception: If transcription fails
        """
        if self.provider == STTProvider.OPENAI:
            return await self._transcribe_openai(audio_bytes, audio_format, **options)
        elif self.provider == STTProvider.GOOGLE:
            return await self._transcribe_google(audio_bytes, audio_format, **options)
        elif self.provider == STTProvider.ASSEMBLYAI:
            return await self._transcribe_assemblyai(audio_bytes, audio_format, **options)
        elif self.provider == STTProvider.DEEPGRAM:
            return await self._transcribe_deepgram(audio_bytes, audio_format, **options)
        else:
            raise ValueError(f"Unsupported STT provider: {self.provider}")

    async def _transcribe_openai(
        self,
        audio_bytes: bytes,
        audio_format: str,
        **options
    ) -> str:
        """
        Transcribe using OpenAI Whisper.

        API: https://platform.openai.com/docs/api-reference/audio/createTranscription
        Cost: $0.006 per minute
        """
        try:
            # Prepare multipart form data
            form_data = aiohttp.FormData()
            form_data.add_field(
                'file',
                audio_bytes,
                filename=f'audio.{audio_format}',
                content_type=f'audio/{audio_format}'
            )
            form_data.add_field('model', self.model)
            form_data.add_field('language', options.get('language', self.language))

            # Optional parameters
            if 'prompt' in options:
                form_data.add_field('prompt', options['prompt'])
            if 'temperature' in options:
                form_data.add_field('temperature', str(options['temperature']))

            # Make API request
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    data=form_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenAI Whisper API error: {response.status} - {error_text}")

                    result = await response.json()
                    transcript = result.get('text', '')

                    logger.info(f"OpenAI Whisper transcription successful, length={len(transcript)}")
                    return transcript.strip()

        except Exception as e:
            logger.error(f"OpenAI Whisper transcription failed: {str(e)}")
            raise

    async def _transcribe_google(
        self,
        audio_bytes: bytes,
        audio_format: str,
        **options
    ) -> str:
        """
        Transcribe using Google Speech-to-Text.

        API: https://cloud.google.com/speech-to-text/docs/reference/rest
        """
        # TODO: Implement Google Speech-to-Text
        raise NotImplementedError("Google Speech-to-Text not yet implemented")

    async def _transcribe_assemblyai(
        self,
        audio_bytes: bytes,
        audio_format: str,
        **options
    ) -> str:
        """
        Transcribe using Assembly AI.

        API: https://www.assemblyai.com/docs
        """
        # TODO: Implement Assembly AI
        raise NotImplementedError("Assembly AI not yet implemented")

    async def _transcribe_deepgram(
        self,
        audio_bytes: bytes,
        audio_format: str,
        **options
    ) -> str:
        """
        Transcribe using Deepgram.

        API: https://developers.deepgram.com/docs
        """
        # TODO: Implement Deepgram
        raise NotImplementedError("Deepgram not yet implemented")

    async def transcribe_with_timestamps(
        self,
        audio_bytes: bytes,
        audio_format: str = "webm"
    ) -> List[Dict[str, Any]]:
        """
        Transcribe with word-level timestamps.

        Returns:
            List of word segments with timestamps:
            [
                {"word": "Hello", "start": 0.0, "end": 0.5},
                {"word": "world", "start": 0.6, "end": 1.0},
            ]
        """
        # Currently only supported by some providers
        if self.provider == STTProvider.OPENAI:
            # Whisper API doesn't provide word-level timestamps by default
            # Would need to use whisper.cpp or other implementation
            raise NotImplementedError("Word-level timestamps not available with OpenAI Whisper API")
        else:
            raise NotImplementedError(f"Timestamps not implemented for {self.provider}")

    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported audio formats.

        Returns:
            List of format extensions
        """
        if self.provider == STTProvider.OPENAI:
            return ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
        elif self.provider == STTProvider.GOOGLE:
            return ["flac", "wav", "mp3", "ogg"]
        elif self.provider == STTProvider.ASSEMBLYAI:
            return ["mp3", "wav", "flac", "ogg", "webm"]
        elif self.provider == STTProvider.DEEPGRAM:
            return ["mp3", "wav", "flac", "ogg", "opus", "webm"]
        else:
            return []

    def get_cost_per_minute(self) -> float:
        """
        Get cost per minute for this provider.

        Returns:
            Cost in USD per minute
        """
        costs = {
            STTProvider.OPENAI: 0.006,  # $0.006/minute
            STTProvider.GOOGLE: 0.006,  # $0.006/minute (standard)
            STTProvider.ASSEMBLYAI: 0.00025,  # $0.00025/second = $0.015/minute
            STTProvider.DEEPGRAM: 0.0043,  # $0.0043/minute (nova-2)
        }
        return costs.get(self.provider, 0.01)


# Example usage
if __name__ == "__main__":
    async def test_stt():
        """Test STT service."""
        import os

        stt = STTService(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY")
        )

        # Mock audio bytes
        audio_bytes = b"mock_audio_data"

        try:
            transcript = await stt.transcribe(audio_bytes, "mp3")
            print(f"Transcript: {transcript}")
        except Exception as e:
            print(f"Error: {e}")

    asyncio.run(test_stt())
