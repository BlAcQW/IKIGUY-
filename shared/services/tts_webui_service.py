"""
TTS-WebUI Service - Programmatic Access to Comprehensive TTS Platform

This service provides programmatic access to TTS-WebUI, a comprehensive platform
supporting 20+ TTS models including StyleTTS2, RVC, Bark, Tortoise, and more.

Author: AI Labs Africa
Created: November 8, 2025
"""

import os
import base64
from typing import Optional, Dict, Any, List
from enum import Enum
import httpx
from pydantic import BaseModel, Field
from apps.shared.middleware.rate_limiter import ServiceRateLimiter, RateLimitExceeded


class TTSWebUIProvider(str, Enum):
    """Available TTS providers in TTS-WebUI."""
    STYLETTS2 = "styletts2"
    RVC = "rvc"
    BARK = "bark"
    TORTOISE = "tortoise"
    MELO_TTS = "melotts"
    MMS = "mms"
    KOKORO = "kokoro"
    OPENVOICE = "openvoice"
    F5_TTS = "f5tts"
    PARLER_TTS = "parlertts"
    VALLE_X = "vallex"
    XTTS_V2 = "xttsv2"
    DEMUCS = "demucs"
    VOCOS = "vocos"
    WHISPER = "whisper"
    MUSIC_GEN = "musicgen"
    STABLE_AUDIO = "stableaudio"
    CHATTERBOX = "chatterbox"
    MAHA_TTS = "mahatts"
    COQUI = "coqui"


class TTSWebUISynthesisRequest(BaseModel):
    """Request model for TTS synthesis via TTS-WebUI."""
    text: str = Field(..., description="Text to synthesize")
    provider_id: TTSWebUIProvider = Field(..., description="TTS provider to use")
    language: Optional[str] = Field("en", description="Language code (e.g., 'en', 'zh', 'ja')")
    voice_id: Optional[str] = Field(None, description="Voice ID or speaker name")
    speed: Optional[float] = Field(1.0, description="Speech speed (0.5-2.0)")
    pitch: Optional[float] = Field(1.0, description="Pitch adjustment (-1.0 to 1.0)")
    emotion: Optional[str] = Field(None, description="Emotion for compatible providers")
    reference_audio_base64: Optional[str] = Field(None, description="Base64-encoded reference audio for voice cloning")
    reference_text: Optional[str] = Field(None, description="Transcript of reference audio")
    output_format: Optional[str] = Field("wav", description="Output format: wav, mp3, flac")


class TTSWebUIVoiceCloneRequest(BaseModel):
    """Request model for voice cloning via TTS-WebUI."""
    text: str = Field(..., description="Text to synthesize with cloned voice")
    provider_id: TTSWebUIProvider = Field(..., description="Voice cloning provider (styletts2, rvc, f5tts, etc)")
    reference_audio_base64: str = Field(..., description="Base64-encoded reference audio")
    reference_text: Optional[str] = Field(None, description="Transcript of reference audio (recommended)")
    language: Optional[str] = Field("en", description="Language code")
    speed: Optional[float] = Field(1.0, description="Speech speed")
    output_format: Optional[str] = Field("wav", description="Output format")


class TTSWebUISynthesisResponse(BaseModel):
    """Response model for TTS synthesis."""
    audio_base64: str = Field(..., description="Base64-encoded audio output")
    duration: float = Field(..., description="Audio duration in seconds")
    provider_used: str = Field(..., description="Provider ID that generated the audio")
    sample_rate: int = Field(22050, description="Audio sample rate in Hz")
    format: str = Field("wav", description="Audio format")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TTSWebUIProviderInfo(BaseModel):
    """Information about a TTS-WebUI provider."""
    provider_id: str = Field(..., description="Unique provider ID")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Provider description")
    capabilities: Dict[str, bool] = Field(..., description="Provider capabilities")
    languages: List[str] = Field(..., description="Supported languages")
    voices: List[str] = Field(default_factory=list, description="Available voices")
    installed: bool = Field(..., description="Whether extension is installed")


class TTSWebUIService:
    """
    Service for interacting with TTS-WebUI programmatically.

    TTS-WebUI is a comprehensive platform supporting 20+ TTS models with a React UI
    and Gradio backend. This service provides Python wrappers for the API.

    Architecture:
        User → TTSWebUIService → TTS-WebUI API (port 7778) → Gradio Backend (port 7770)

    Features:
        - 20+ TTS models (StyleTTS2, RVC, Bark, Tortoise, etc.)
        - Voice cloning support
        - Multi-language synthesis
        - Extension management
        - OpenAI-compatible API
    """

    def __init__(
        self,
        api_endpoint: Optional[str] = None,
        webui_endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 300,
        enable_rate_limiting: bool = True,
        user_rpm: Optional[int] = None,
        org_rpm: Optional[int] = None
    ):
        """
        Initialize TTS-WebUI service.

        Args:
            api_endpoint: OpenAI-compatible API endpoint (default: from env TTSWEBUI_API_ENDPOINT)
            webui_endpoint: Web UI endpoint for Gradio API (default: from env TTSWEBUI_WEBUI_ENDPOINT)
            api_key: API key for authentication (optional)
            timeout: Request timeout in seconds (default: 300)
            enable_rate_limiting: Enable rate limiting (default: True)
            user_rpm: Requests per minute per user (default: 60)
            org_rpm: Requests per minute per organization (default: 600)
        """
        self.api_endpoint = api_endpoint or os.getenv(
            "TTSWEBUI_API_ENDPOINT",
            "https://tts-webui.ailabsafrica.com/api"
        )
        self.webui_endpoint = webui_endpoint or os.getenv(
            "TTSWEBUI_WEBUI_ENDPOINT",
            "https://tts-webui.ailabsafrica.com"
        )
        self.api_key = api_key or os.getenv("TTSWEBUI_API_KEY")
        self.timeout = timeout

        # Provider-specific endpoint mapping
        # Maps provider ID to its service domain
        self.provider_endpoints = {
            "styletts2": "https://styletts.ailabsafrica.com",
            "kokoro": "https://kokoro.ailabsafrica.com",
            "melotts": "https://melotts.ailabsafrica.com",
            "openvoice": "https://openvoice.ailabsafrica.com",
            "chatterbox": "https://chatterbox.ailabsafrica.com",
            "coqui": "https://coqui.ailabsafrica.com",
            "f5tts": "https://f5tts.ailabsafrica.com",
        }

        # HTTP client
        self.client = httpx.AsyncClient(timeout=timeout)

        # Rate limiting
        self.enable_rate_limiting = enable_rate_limiting
        if enable_rate_limiting:
            self.rate_limiter = ServiceRateLimiter(
                user_rpm=user_rpm or int(os.getenv("TTSWEBUI_USER_RPM", "60")),
                user_rph=int(os.getenv("TTSWEBUI_USER_RPH", "1000")),
                org_rpm=org_rpm or int(os.getenv("TTSWEBUI_ORG_RPM", "600")),
                org_rph=int(os.getenv("TTSWEBUI_ORG_RPH", "10000"))
            )
        else:
            self.rate_limiter = None

    async def _check_rate_limit(
        self,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None
    ):
        """
        Check rate limit for user/organization.

        Args:
            user_id: User identifier
            org_id: Organization identifier

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        if self.enable_rate_limiting and self.rate_limiter:
            allowed, failed_scope = await self.rate_limiter.check_limit_async(
                user_id=user_id,
                org_id=org_id
            )

            if not allowed:
                identifier = user_id if failed_scope.value == "user" else org_id
                retry_after = self.rate_limiter.get_retry_after(failed_scope, identifier or "unknown")
                raise RateLimitExceeded(
                    f"Rate limit exceeded for {failed_scope.value}. Try again in {retry_after}s.",
                    retry_after=retry_after
                )

    def get_providers(self) -> List[TTSWebUIProvider]:
        """
        Get list of available TTS providers.

        Returns:
            List of TTSWebUIProvider enum values

        Example:
            >>> service = TTSWebUIService()
            >>> providers = service.get_providers()
            >>> print(providers)  # [TTSWebUIProvider.STYLETTS2, TTSWebUIProvider.KOKORO, ...]
        """
        # Return providers that have configured endpoints
        return [
            TTSWebUIProvider(provider_id)
            for provider_id in self.provider_endpoints.keys()
        ]

    async def synthesize(
        self,
        request: TTSWebUISynthesisRequest,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None
    ) -> TTSWebUISynthesisResponse:
        """
        Synthesize speech using TTS-WebUI.

        Args:
            request: Synthesis request parameters
            user_id: User identifier for rate limiting and analytics
            org_id: Organization identifier for rate limiting

        Returns:
            Synthesis response with audio data

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If provider not found or invalid parameters
            RateLimitExceeded: If rate limit is exceeded

        Example:
            >>> service = TTSWebUIService()
            >>> request = TTSWebUISynthesisRequest(
            ...     text="Hello world",
            ...     provider_id=TTSWebUIProvider.STYLETTS2,
            ...     language="en"
            ... )
            >>> response = await service.synthesize(
            ...     request,
            ...     user_id="user_123",
            ...     org_id="org_abc"
            ... )
            >>> audio_bytes = base64.b64decode(response.audio_base64)
        """
        # Check rate limit
        await self._check_rate_limit(user_id, org_id)

        # Get provider-specific endpoint
        provider_id = request.provider_id.value
        provider_url = self.provider_endpoints.get(provider_id)

        if not provider_url:
            raise ValueError(f"Provider '{provider_id}' not found. Available providers: {list(self.provider_endpoints.keys())}")

        # Prepare request payload for our TTS service format
        payload = {
            "text": request.text,
            "voice": request.voice_id or "default",
            "speed": request.speed or 1.0,
            "pitch": request.pitch or 1.0,
        }

        # Add optional parameters
        if request.language:
            payload["language"] = request.language
        if request.emotion:
            payload["emotion"] = request.emotion
        if request.reference_audio_base64:
            payload["reference_audio"] = request.reference_audio_base64
        if request.reference_text:
            payload["reference_text"] = request.reference_text

        # Prepare headers
        headers = {"Content-Type": "application/json"}

        # Make API request to provider's /synthesize endpoint
        response = await self.client.post(
            f"{provider_url}/synthesize",
            json=payload,
            headers=headers
        )
        response.raise_for_status()

        # Get binary audio data
        audio_data = response.content
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        # Estimate duration (assuming 24kHz, 16-bit, mono WAV)
        # WAV header is 44 bytes, then audio data
        audio_bytes = len(audio_data) - 44 if len(audio_data) > 44 else len(audio_data)
        duration = audio_bytes / (24000 * 2)  # bytes / (sample_rate * bytes_per_sample)

        return TTSWebUISynthesisResponse(
            audio_base64=audio_base64,
            duration=duration,
            provider_used=provider_id,
            sample_rate=24000,
            format=request.output_format or "wav",
            metadata={"provider_url": provider_url}
        )

    async def synthesize_with_voice_cloning(
        self,
        request: TTSWebUIVoiceCloneRequest,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None
    ) -> TTSWebUISynthesisResponse:
        """
        Synthesize speech with voice cloning.

        Args:
            request: Voice cloning request parameters
            user_id: User identifier for rate limiting and analytics
            org_id: Organization identifier for rate limiting

        Returns:
            Synthesis response with cloned voice audio

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If provider doesn't support voice cloning
            RateLimitExceeded: If rate limit is exceeded

        Example:
            >>> service = TTSWebUIService()
            >>> # Load reference audio
            >>> with open("reference.wav", "rb") as f:
            ...     ref_audio_b64 = base64.b64encode(f.read()).decode()
            >>>
            >>> request = TTSWebUIVoiceCloneRequest(
            ...     text="This is my cloned voice",
            ...     provider_id=TTSWebUIProvider.STYLETTS2,
            ...     reference_audio_base64=ref_audio_b64,
            ...     language="en"
            ... )
            >>> response = await service.synthesize_with_voice_cloning(
            ...     request,
            ...     user_id="user_123",
            ...     org_id="org_abc"
            ... )
        """
        # Verify provider supports voice cloning
        voice_cloning_providers = [
            TTSWebUIProvider.STYLETTS2,
            TTSWebUIProvider.RVC,
            TTSWebUIProvider.F5_TTS,
            TTSWebUIProvider.OPENVOICE,
            TTSWebUIProvider.XTTS_V2
        ]

        if request.provider_id not in voice_cloning_providers:
            raise ValueError(
                f"Provider {request.provider_id} does not support voice cloning. "
                f"Supported providers: {[p.value for p in voice_cloning_providers]}"
            )

        # Convert to standard synthesis request
        synthesis_request = TTSWebUISynthesisRequest(
            text=request.text,
            provider_id=request.provider_id,
            language=request.language,
            speed=request.speed,
            reference_audio_base64=request.reference_audio_base64,
            reference_text=request.reference_text,
            output_format=request.output_format
        )

        return await self.synthesize(synthesis_request, user_id=user_id, org_id=org_id)

    async def list_providers(self) -> List[TTSWebUIProviderInfo]:
        """
        List all available TTS providers in TTS-WebUI.

        Returns:
            List of provider information

        Example:
            >>> service = TTSWebUIService()
            >>> providers = await service.list_providers()
            >>> for provider in providers:
            ...     print(f"{provider.name}: {provider.description}")
        """
        response = await self.client.get(
            f"{self.webui_endpoint}/api/providers"
        )
        response.raise_for_status()

        providers_data = response.json()
        return [
            TTSWebUIProviderInfo(**provider)
            for provider in providers_data
        ]

    async def get_provider_info(
        self,
        provider_id: TTSWebUIProvider
    ) -> TTSWebUIProviderInfo:
        """
        Get information about a specific provider.

        Args:
            provider_id: Provider ID to query

        Returns:
            Provider information

        Example:
            >>> service = TTSWebUIService()
            >>> info = await service.get_provider_info(TTSWebUIProvider.STYLETTS2)
            >>> print(f"StyleTTS2 supports voice cloning: {info.capabilities['voice_cloning']}")
        """
        response = await self.client.get(
            f"{self.webui_endpoint}/api/providers/{provider_id.value}"
        )
        response.raise_for_status()

        return TTSWebUIProviderInfo(**response.json())

    async def list_voices(
        self,
        provider_id: TTSWebUIProvider
    ) -> List[str]:
        """
        List available voices for a provider.

        Args:
            provider_id: Provider ID to query

        Returns:
            List of voice IDs

        Example:
            >>> service = TTSWebUIService()
            >>> voices = await service.list_voices(TTSWebUIProvider.KOKORO)
            >>> print(f"Kokoro voices: {voices}")
        """
        response = await self.client.get(
            f"{self.webui_endpoint}/api/providers/{provider_id.value}/voices"
        )
        response.raise_for_status()

        return response.json().get("voices", [])

    async def health_check(self) -> Dict[str, Any]:
        """
        Check TTS-WebUI health status.

        Returns:
            Health status information

        Example:
            >>> service = TTSWebUIService()
            >>> health = await service.health_check()
            >>> print(f"Status: {health['status']}")
        """
        response = await self.client.get(
            f"{self.webui_endpoint}/health"
        )
        response.raise_for_status()

        return response.json()

    async def close(self):
        """
        Close HTTP client connections.

        Example:
            >>> service = TTSWebUIService()
            >>> # ... use service ...
            >>> await service.close()
        """
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Singleton instance
_tts_webui_service: Optional[TTSWebUIService] = None


async def get_tts_webui_service() -> TTSWebUIService:
    """
    Get singleton TTS-WebUI service instance.

    Returns:
        TTSWebUIService instance

    Example:
        >>> from apps.shared.services.tts_webui_service import get_tts_webui_service
        >>>
        >>> service = await get_tts_webui_service()
        >>> request = TTSWebUISynthesisRequest(
        ...     text="Hello world",
        ...     provider_id=TTSWebUIProvider.STYLETTS2
        ... )
        >>> response = await service.synthesize(request)
    """
    global _tts_webui_service

    if _tts_webui_service is None:
        _tts_webui_service = TTSWebUIService()

    return _tts_webui_service


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        """Example usage of TTS-WebUI service."""
        # Create service
        async with TTSWebUIService() as service:
            # Check health
            health = await service.health_check()
            print(f"TTS-WebUI Status: {health}")

            # List providers
            providers = await service.list_providers()
            print(f"\nAvailable Providers: {len(providers)}")
            for provider in providers[:5]:  # Show first 5
                print(f"  - {provider.name}: {provider.description}")

            # Synthesize speech
            request = TTSWebUISynthesisRequest(
                text="Hello from AI Labs Africa!",
                provider_id=TTSWebUIProvider.STYLETTS2,
                language="en",
                speed=1.0
            )

            print(f"\nSynthesizing with {request.provider_id}...")
            response = await service.synthesize(request)

            print(f"Audio duration: {response.duration:.2f}s")
            print(f"Sample rate: {response.sample_rate}Hz")
            print(f"Format: {response.format}")

            # Save audio
            audio_bytes = base64.b64decode(response.audio_base64)
            with open("output.wav", "wb") as f:
                f.write(audio_bytes)
            print("Audio saved to output.wav")

    asyncio.run(main())
