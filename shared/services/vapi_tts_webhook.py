"""
Vapi TTS Webhook Service

Provides custom TTS integration for Vapi voice AI assistants using
KasaAI's TTS-WebUI infrastructure with 20+ TTS models.

This service acts as a webhook endpoint that receives text from Vapi
and returns raw PCM audio in real-time during voice calls.

Author: AI Labs Africa
Created: November 8, 2025
"""

import os
import io
import logging
import time
import base64
from typing import Optional, Dict, Any
from enum import Enum

import aiohttp
from pydantic import BaseModel, Field
import numpy as np

from .tts_webui_service import (
    TTSWebUIService,
    TTSWebUISynthesisRequest,
    TTSWebUIProvider
)
from ..middleware.rate_limiter import ServiceRateLimiter, RateLimitExceeded


logger = logging.getLogger(__name__)


class VapiAudioFormat(str, Enum):
    """Supported audio formats for Vapi."""
    PCM_8000 = "pcm_8000"
    PCM_16000 = "pcm_16000"
    PCM_22050 = "pcm_22050"
    PCM_24000 = "pcm_24000"


class VapiMessageType(str, Enum):
    """Vapi message types."""
    VOICE_REQUEST = "voice-request"


class VapiVoiceRequest(BaseModel):
    """Vapi voice request message."""
    type: str = Field(..., description="Message type (always 'voice-request')")
    text: str = Field(..., description="Text to synthesize")
    sampleRate: int = Field(..., description="Target sample rate (8000, 16000, 22050, 24000)")


class VapiWebhookRequest(BaseModel):
    """Complete Vapi webhook request."""
    message: VapiVoiceRequest
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    call: Optional[Dict[str, Any]] = Field(default=None, description="Call metadata")
    assistant: Optional[Dict[str, Any]] = Field(default=None, description="Assistant metadata")
    customer: Optional[Dict[str, Any]] = Field(default=None, description="Customer metadata")


class VapiTTSWebhookService:
    """
    Custom TTS webhook service for Vapi integration.

    Converts Vapi webhook requests into TTS-WebUI synthesis requests
    and returns raw PCM audio in the format required by Vapi.

    Features:
    - Support for 20+ TTS models via TTS-WebUI
    - Real-time PCM audio conversion
    - Rate limiting per organization/user
    - Authentication via Vapi API key
    - Fallback provider support
    - Request logging and monitoring

    Example:
        >>> service = VapiTTSWebhookService(
        ...     default_provider=TTSWebUIProvider.STYLETTS2,
        ...     enable_rate_limiting=True
        ... )
        >>>
        >>> # Process Vapi webhook request
        >>> pcm_audio = await service.process_webhook_request(vapi_request)
        >>> # Returns raw PCM audio bytes ready for Vapi
    """

    def __init__(
        self,
        tts_service: Optional[TTSWebUIService] = None,
        default_provider: TTSWebUIProvider = TTSWebUIProvider.STYLETTS2,
        fallback_provider: Optional[TTSWebUIProvider] = None,
        vapi_api_key: Optional[str] = None,
        enable_rate_limiting: bool = True,
        org_rpm: Optional[int] = None,
        user_rpm: Optional[int] = None,
        timeout: int = 30
    ):
        """
        Initialize Vapi TTS webhook service.

        Args:
            tts_service: TTSWebUIService instance (creates new if None)
            default_provider: Default TTS provider to use
            fallback_provider: Fallback provider if default fails
            vapi_api_key: Vapi API key for authentication
            enable_rate_limiting: Enable rate limiting
            org_rpm: Requests per minute per organization
            user_rpm: Requests per minute per user
            timeout: Request timeout in seconds
        """
        # TTS service
        self.tts_service = tts_service or TTSWebUIService()
        self.default_provider = default_provider
        self.fallback_provider = fallback_provider or TTSWebUIProvider.KOKORO

        # Authentication
        self.vapi_api_key = vapi_api_key or os.getenv("VAPI_API_KEY")
        if not self.vapi_api_key:
            logger.warning("VAPI_API_KEY not set - authentication disabled")

        # Rate limiting
        self.enable_rate_limiting = enable_rate_limiting
        if enable_rate_limiting:
            self.rate_limiter = ServiceRateLimiter(
                org_rpm=org_rpm or int(os.getenv("VAPI_ORG_RPM", "100")),
                org_rph=int(os.getenv("VAPI_ORG_RPH", "2000")),
                user_rpm=user_rpm or int(os.getenv("VAPI_USER_RPM", "30")),
                user_rph=int(os.getenv("VAPI_USER_RPH", "500"))
            )

        self.timeout = timeout

        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_audio_seconds": 0.0,
            "fallback_used": 0
        }

    def validate_authentication(self, auth_header: Optional[str]) -> bool:
        """
        Validate Vapi API key from Authorization header.

        Args:
            auth_header: Authorization header value (e.g., "Bearer <key>")

        Returns:
            True if valid, False otherwise
        """
        if not self.vapi_api_key:
            return True  # Auth disabled

        if not auth_header:
            return False

        # Extract token from "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return False

        token = parts[1]
        return token == self.vapi_api_key

    async def _check_rate_limit(
        self,
        org_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        Check rate limit for request.

        Args:
            org_id: Organization identifier
            user_id: User identifier

        Raises:
            RateLimitExceeded: If rate limit exceeded
        """
        if not self.enable_rate_limiting:
            return

        allowed, failed_scope = await self.rate_limiter.check_limit_async(
            org_id=org_id,
            user_id=user_id
        )

        if not allowed:
            identifier = org_id if failed_scope.value == "organization" else user_id
            retry_after = self.rate_limiter.get_retry_after(
                failed_scope,
                identifier or "unknown"
            )
            raise RateLimitExceeded(
                f"Rate limit exceeded for {failed_scope.value}. Try again in {retry_after}s.",
                retry_after=retry_after
            )

    def _validate_request(self, request: VapiWebhookRequest) -> None:
        """
        Validate Vapi webhook request.

        Args:
            request: Vapi webhook request

        Raises:
            ValueError: If request is invalid
        """
        # Check message type
        if request.message.type != VapiMessageType.VOICE_REQUEST:
            raise ValueError(f"Invalid message type: {request.message.type}")

        # Check text
        if not request.message.text or not request.message.text.strip():
            raise ValueError("Text cannot be empty")

        # Check sample rate
        valid_rates = [8000, 16000, 22050, 24000]
        if request.message.sampleRate not in valid_rates:
            raise ValueError(
                f"Invalid sample rate: {request.message.sampleRate}. "
                f"Must be one of: {valid_rates}"
            )

    async def _synthesize_with_fallback(
        self,
        text: str,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None
    ) -> bytes:
        """
        Synthesize speech with fallback provider support.

        Args:
            text: Text to synthesize
            user_id: User identifier for rate limiting
            org_id: Organization identifier for rate limiting

        Returns:
            Audio data in original format (WAV, MP3, etc.)

        Raises:
            Exception: If both primary and fallback fail
        """
        # Try primary provider
        try:
            request = TTSWebUISynthesisRequest(
                text=text,
                provider_id=self.default_provider.value,
                language="en"
            )

            response = await self.tts_service.synthesize(
                request,
                user_id=user_id,
                org_id=org_id
            )

            logger.info(
                f"Synthesized with {self.default_provider.value}: "
                f"{len(text)} chars, {response.duration:.2f}s"
            )

            # Decode base64 audio
            return base64.b64decode(response.audio_base64)

        except Exception as e:
            logger.warning(
                f"Primary provider {self.default_provider.value} failed: {e}. "
                f"Trying fallback {self.fallback_provider.value}"
            )

            # Try fallback provider
            try:
                request = TTSWebUISynthesisRequest(
                    text=text,
                    provider_id=self.fallback_provider.value,
                    language="en"
                )

                response = await self.tts_service.synthesize(
                    request,
                    user_id=user_id,
                    org_id=org_id
                )

                self.stats["fallback_used"] += 1
                logger.info(
                    f"Synthesized with fallback {self.fallback_provider.value}: "
                    f"{len(text)} chars, {response.duration:.2f}s"
                )

                # Decode base64 audio
                return base64.b64decode(response.audio_base64)

            except Exception as fallback_error:
                logger.error(
                    f"Both providers failed. Primary: {e}, Fallback: {fallback_error}"
                )
                raise Exception(f"TTS synthesis failed: {fallback_error}") from fallback_error

    def _convert_to_pcm(
        self,
        audio_data: bytes,
        target_sample_rate: int
    ) -> bytes:
        """
        Convert audio to raw PCM format required by Vapi.

        Vapi requires:
        - Format: Raw PCM (no headers)
        - Channels: Mono
        - Bit depth: 16-bit signed integer
        - Byte order: Little-endian
        - Sample rate: Must match request

        Args:
            audio_data: Audio data (WAV, MP3, etc.)
            target_sample_rate: Target sample rate (8000, 16000, 22050, 24000)

        Returns:
            Raw PCM audio bytes
        """
        try:
            # Import audio processing libraries
            from pydub import AudioSegment

            # Load audio (pydub auto-detects format)
            audio = AudioSegment.from_file(io.BytesIO(audio_data))

            # Convert to mono if needed
            if audio.channels > 1:
                audio = audio.set_channels(1)

            # Resample if needed
            if audio.frame_rate != target_sample_rate:
                audio = audio.set_frame_rate(target_sample_rate)

            # Ensure 16-bit
            if audio.sample_width != 2:  # 2 bytes = 16 bits
                audio = audio.set_sample_width(2)

            # Get raw PCM data
            pcm_data = audio.raw_data

            logger.debug(
                f"Converted to PCM: {target_sample_rate}Hz, "
                f"{len(pcm_data)} bytes, {audio.duration_seconds:.2f}s"
            )

            return pcm_data

        except ImportError:
            logger.error("pydub not installed. Install with: pip install pydub")
            raise
        except Exception as e:
            logger.error(f"PCM conversion failed: {e}")
            raise

    async def process_webhook_request(
        self,
        request: VapiWebhookRequest,
        auth_header: Optional[str] = None
    ) -> bytes:
        """
        Process Vapi webhook request and return raw PCM audio.

        Args:
            request: Vapi webhook request
            auth_header: Authorization header for validation

        Returns:
            Raw PCM audio bytes ready for Vapi

        Raises:
            ValueError: If request is invalid
            RateLimitExceeded: If rate limit exceeded
            Exception: If TTS synthesis fails
        """
        start_time = time.time()
        self.stats["total_requests"] += 1

        try:
            # Validate authentication
            if not self.validate_authentication(auth_header):
                raise ValueError("Invalid or missing authentication")

            # Validate request
            self._validate_request(request)

            # Extract identifiers for rate limiting
            org_id = None
            user_id = None

            if request.assistant:
                org_id = request.assistant.get("organizationId")

            if request.customer:
                user_id = request.customer.get("number") or request.customer.get("id")

            # Check rate limit
            await self._check_rate_limit(org_id=org_id, user_id=user_id)

            # Synthesize speech
            audio_data = await self._synthesize_with_fallback(
                text=request.message.text,
                user_id=user_id,
                org_id=org_id
            )

            # Convert to PCM
            pcm_audio = self._convert_to_pcm(
                audio_data,
                target_sample_rate=request.message.sampleRate
            )

            # Update stats
            self.stats["successful_requests"] += 1
            elapsed = time.time() - start_time

            logger.info(
                f"Vapi webhook request completed in {elapsed:.2f}s: "
                f"{len(request.message.text)} chars → {len(pcm_audio)} bytes PCM"
            )

            return pcm_audio

        except Exception as e:
            self.stats["failed_requests"] += 1
            elapsed = time.time() - start_time

            logger.error(
                f"Vapi webhook request failed after {elapsed:.2f}s: {e}"
            )
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get service statistics.

        Returns:
            Dictionary with service statistics
        """
        return {
            **self.stats,
            "success_rate": (
                self.stats["successful_requests"] / self.stats["total_requests"]
                if self.stats["total_requests"] > 0
                else 0.0
            ),
            "fallback_rate": (
                self.stats["fallback_used"] / self.stats["successful_requests"]
                if self.stats["successful_requests"] > 0
                else 0.0
            )
        }

    def reset_stats(self):
        """Reset service statistics."""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_audio_seconds": 0.0,
            "fallback_used": 0
        }


# Singleton instance
_vapi_webhook_service: Optional[VapiTTSWebhookService] = None


def get_vapi_webhook_service() -> VapiTTSWebhookService:
    """
    Get singleton Vapi webhook service instance.

    Returns:
        VapiTTSWebhookService instance
    """
    global _vapi_webhook_service

    if _vapi_webhook_service is None:
        _vapi_webhook_service = VapiTTSWebhookService()

    return _vapi_webhook_service
