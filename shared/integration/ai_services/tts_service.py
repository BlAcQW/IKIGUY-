"""
Text-to-Speech (TTS) Service.

⚠️ DEPRECATION WARNING ⚠️
This service is deprecated and will be removed in a future release.

Please migrate to the new unified TTS system:
- Use: apps.shared.tts.client.AsyncTTSClient
- Documentation: apps/shared/tts/README.md
- Migration Guide: apps/shared/tts/MIGRATION.md

New features available in unified system:
- Automatic billing and wallet integration
- MongoDB GridFS caching (40% cost reduction)
- Provider health monitoring and alerting
- Standardized provider IDs (snake_case)
- TypeScript type generation
- Comprehensive testing

Legacy providers supported:
- OpenAI TTS
- Google Text-to-Speech
- ElevenLabs
- Play.ht
- Coqui XTTS (self-hosted)

Usage (DEPRECATED):
    tts_service = TTSService(provider="openai", api_key="...", voice="nova")
    audio_bytes = await tts_service.synthesize("Hello world!")
"""

import asyncio
import logging
import warnings
from typing import Optional, Dict, Any, List
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)

# Issue deprecation warning on import
warnings.warn(
    "apps.shared.integration.ai_services.tts_service.TTSService is deprecated. "
    "Please use apps.shared.tts.client.AsyncTTSClient instead. "
    "See apps/shared/tts/MIGRATION.md for migration guide.",
    DeprecationWarning,
    stacklevel=2
)


class TTSProvider(str, Enum):
    """Available TTS providers."""
    OPENAI = "openai"  # OpenAI TTS
    GOOGLE = "google"  # Google Text-to-Speech
    ELEVENLABS = "elevenlabs"  # ElevenLabs
    PLAYHT = "playht"  # Play.ht
    COQUI = "coqui"  # Coqui XTTS (self-hosted)


class TTSService:
    """
    Text-to-Speech service with multi-provider support.

    Supports:
    - OpenAI TTS (default)
    - Google Text-to-Speech
    - ElevenLabs
    - Play.ht
    - Coqui XTTS
    """

    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize TTS service.

        Args:
            provider: TTS provider name
            api_key: API key for the provider
            voice: Voice ID/name
            model: Model name (provider-specific)
            **kwargs: Additional provider-specific parameters
        """
        self.provider = TTSProvider(provider.lower())
        self.api_key = api_key
        self.kwargs = kwargs

        # Provider-specific configuration
        if self.provider == TTSProvider.OPENAI:
            self.model = model or "tts-1"  # tts-1 or tts-1-hd
            self.voice = voice or "nova"  # alloy, echo, fable, onyx, nova, shimmer
            self.api_url = "https://api.openai.com/v1/audio/speech"
        elif self.provider == TTSProvider.GOOGLE:
            self.model = model or "en-US-Neural2-C"
            self.voice = voice or "en-US-Neural2-C"
            self.api_url = "https://texttospeech.googleapis.com/v1/text:synthesize"
        elif self.provider == TTSProvider.ELEVENLABS:
            self.model = model or "eleven_monolingual_v1"
            self.voice = voice or "21m00Tcm4TlvDq8ikWAM"  # Default voice
            self.api_url = "https://api.elevenlabs.io/v1/text-to-speech"
        elif self.provider == TTSProvider.PLAYHT:
            self.model = model or "Play3.0-mini"
            self.voice = voice or "s3://voice-cloning-zero-shot/..."
            self.api_url = "https://api.play.ht/api/v2/tts"
        elif self.provider == TTSProvider.COQUI:
            self.model = model or "xtts_v2"
            self.voice = voice or "default"
            self.api_url = kwargs.get("coqui_url", "http://localhost:5002/api/tts")

        logger.info(f"Initialized TTSService with provider={self.provider}, model={self.model}, voice={self.voice}")

    async def synthesize(
        self,
        text: str,
        speed: float = 1.0,
        **options
    ) -> bytes:
        """
        Synthesize text to speech.

        Args:
            text: Text to synthesize
            speed: Playback speed (0.25 - 4.0)
            **options: Provider-specific options

        Returns:
            Audio bytes (typically MP3 format)

        Raises:
            Exception: If synthesis fails
        """
        if self.provider == TTSProvider.OPENAI:
            return await self._synthesize_openai(text, speed, **options)
        elif self.provider == TTSProvider.GOOGLE:
            return await self._synthesize_google(text, speed, **options)
        elif self.provider == TTSProvider.ELEVENLABS:
            return await self._synthesize_elevenlabs(text, speed, **options)
        elif self.provider == TTSProvider.PLAYHT:
            return await self._synthesize_playht(text, speed, **options)
        elif self.provider == TTSProvider.COQUI:
            return await self._synthesize_coqui(text, speed, **options)
        else:
            raise ValueError(f"Unsupported TTS provider: {self.provider}")

    async def _synthesize_openai(
        self,
        text: str,
        speed: float,
        **options
    ) -> bytes:
        """
        Synthesize using OpenAI TTS.

        API: https://platform.openai.com/docs/api-reference/audio/createSpeech
        Cost: $15 per 1M characters (tts-1), $30 per 1M characters (tts-1-hd)
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'model': self.model,
                'input': text,
                'voice': self.voice,
                'speed': max(0.25, min(4.0, speed)),  # Clamp to valid range
            }

            # Optional format (mp3, opus, aac, flac)
            if 'response_format' in options:
                payload['response_format'] = options['response_format']

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenAI TTS API error: {response.status} - {error_text}")

                    audio_bytes = await response.read()

                    logger.info(f"OpenAI TTS synthesis successful, size={len(audio_bytes)} bytes")
                    return audio_bytes

        except Exception as e:
            logger.error(f"OpenAI TTS synthesis failed: {str(e)}")
            raise

    async def _synthesize_google(
        self,
        text: str,
        speed: float,
        **options
    ) -> bytes:
        """
        Synthesize using Google Text-to-Speech.

        API: https://cloud.google.com/text-to-speech/docs/reference/rest
        """
        # TODO: Implement Google TTS
        raise NotImplementedError("Google TTS not yet implemented")

    async def _synthesize_elevenlabs(
        self,
        text: str,
        speed: float,
        **options
    ) -> bytes:
        """
        Synthesize using ElevenLabs.

        API: https://docs.elevenlabs.io/api-reference/text-to-speech
        """
        try:
            headers = {
                'xi-api-key': self.api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                'text': text,
                'model_id': self.model,
                'voice_settings': {
                    'stability': options.get('stability', 0.5),
                    'similarity_boost': options.get('similarity_boost', 0.75),
                }
            }

            url = f"{self.api_url}/{self.voice}"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"ElevenLabs API error: {response.status} - {error_text}")

                    audio_bytes = await response.read()

                    logger.info(f"ElevenLabs synthesis successful, size={len(audio_bytes)} bytes")
                    return audio_bytes

        except Exception as e:
            logger.error(f"ElevenLabs synthesis failed: {str(e)}")
            raise

    async def _synthesize_playht(
        self,
        text: str,
        speed: float,
        **options
    ) -> bytes:
        """
        Synthesize using Play.ht.

        API: https://docs.play.ht/reference/api-getting-started
        """
        # TODO: Implement Play.ht
        raise NotImplementedError("Play.ht not yet implemented")

    async def _synthesize_coqui(
        self,
        text: str,
        speed: float,
        **options
    ) -> bytes:
        """
        Synthesize using Coqui XTTS (self-hosted).

        Requires Coqui TTS server running.
        """
        # TODO: Implement Coqui XTTS
        raise NotImplementedError("Coqui XTTS not yet implemented")

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices for this provider.

        Returns:
            List of voice information dicts
        """
        if self.provider == TTSProvider.OPENAI:
            return [
                {"id": "alloy", "name": "Alloy", "gender": "neutral", "description": "Neutral, balanced"},
                {"id": "echo", "name": "Echo", "gender": "male", "description": "Male, warm"},
                {"id": "fable", "name": "Fable", "gender": "neutral", "description": "Neutral, storytelling"},
                {"id": "onyx", "name": "Onyx", "gender": "male", "description": "Male, deep"},
                {"id": "nova", "name": "Nova", "gender": "female", "description": "Female, energetic"},
                {"id": "shimmer", "name": "Shimmer", "gender": "female", "description": "Female, soft"},
            ]
        else:
            return []

    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported output formats.

        Returns:
            List of format extensions
        """
        if self.provider == TTSProvider.OPENAI:
            return ["mp3", "opus", "aac", "flac"]
        elif self.provider == TTSProvider.GOOGLE:
            return ["mp3", "wav", "ogg"]
        elif self.provider == TTSProvider.ELEVENLABS:
            return ["mp3"]
        elif self.provider == TTSProvider.PLAYHT:
            return ["mp3", "wav", "ogg"]
        elif self.provider == TTSProvider.COQUI:
            return ["wav"]
        else:
            return []

    def get_cost_per_1k_chars(self) -> float:
        """
        Get cost per 1000 characters for this provider.

        Returns:
            Cost in USD per 1000 characters
        """
        costs = {
            TTSProvider.OPENAI: 0.015,  # $15/1M chars = $0.015/1k chars (tts-1)
            TTSProvider.GOOGLE: 0.004,  # $4/1M chars (Neural2)
            TTSProvider.ELEVENLABS: 0.30,  # ~$0.30/1k chars (varies by plan)
            TTSProvider.PLAYHT: 0.015,  # ~$0.015/1k chars
            TTSProvider.COQUI: 0.0,  # Free (self-hosted)
        }
        return costs.get(self.provider, 0.02)

    def get_max_text_length(self) -> int:
        """
        Get maximum text length for single request.

        Returns:
            Maximum character count
        """
        limits = {
            TTSProvider.OPENAI: 4096,  # 4096 characters
            TTSProvider.GOOGLE: 5000,  # 5000 characters
            TTSProvider.ELEVENLABS: 5000,  # 5000 characters
            TTSProvider.PLAYHT: 10000,  # 10000 characters
            TTSProvider.COQUI: 500,  # 500 characters per chunk
        }
        return limits.get(self.provider, 4096)


# Example usage
if __name__ == "__main__":
    async def test_tts():
        """Test TTS service."""
        import os

        tts = TTSService(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            voice="nova"
        )

        try:
            audio_bytes = await tts.synthesize("Hello, this is a test of the text to speech system.")
            print(f"Generated audio: {len(audio_bytes)} bytes")

            # Save to file
            with open("test_output.mp3", "wb") as f:
                f.write(audio_bytes)
            print("Saved to test_output.mp3")

        except Exception as e:
            print(f"Error: {e}")

    asyncio.run(test_tts())
