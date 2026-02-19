"""
Voice Greeting Service.

Handles generation of personalized voice greetings for check-ins using the
shared TTS Provider Service.
"""

import logging
import base64
import os
import asyncio
from typing import Dict, Optional
from datetime import datetime

from app.models.voice_greeting import VoiceGreetingConfig, GreetingAudioResponse
from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest,
    SynthesisResult
)

logger = logging.getLogger(__name__)

# Module-level singleton instance to avoid race conditions
_tts_service_instance: Optional[TTSProviderService] = None
_tts_service_lock = asyncio.Lock()


class VoiceGreetingService:
    """
    Service for generating voice greetings for check-ins.

    Handles both simple and personalized greetings, integrating with
    the shared TTS Provider Service for audio synthesis.
    """

    def __init__(self):
        """Initialize the voice greeting service."""
        self.tts_service = None  # Will be set to singleton instance
        self._initialized = False
        # Storage path for generated greeting audio files
        self.storage_path = os.getenv(
            "GREETING_AUDIO_PATH",
            "/opt/kasaai/apps/churchflow/backend/storage/greetings"
        )
        # Base URL for accessing stored audio
        self.storage_base_url = os.getenv(
            "GREETING_AUDIO_URL",
            "https://churchflow-api.ailabsafrica.com/storage/greetings"
        )

    async def initialize(self) -> None:
        """
        Initialize the TTS service singleton.

        Must be called before generating greetings.
        Uses a module-level singleton to avoid race conditions where
        health checks haven't completed yet.
        """
        if self._initialized:
            return

        global _tts_service_instance

        try:
            async with _tts_service_lock:
                # Check if singleton is already initialized
                if _tts_service_instance is None:
                    logger.info("Initializing singleton TTSProviderService...")
                    _tts_service_instance = TTSProviderService(
                        enable_billing=False,  # Disable billing for now
                        enable_health_monitoring=True,
                        enable_email_alerts=False,
                        cache_ttl=300
                    )
                    await _tts_service_instance.initialize()

                    # Wait for initial health check to complete
                    # This prevents race condition where providers are marked offline
                    logger.info("Waiting for initial provider health check...")
                    await asyncio.sleep(2.0)
                    logger.info("TTSProviderService singleton ready")

            # Use the singleton instance
            self.tts_service = _tts_service_instance
            self._initialized = True
            logger.info("VoiceGreetingService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize VoiceGreetingService: {e}")
            raise

    async def generate_greeting(
        self,
        user_data: Dict,
        event_data: Dict,
        config: VoiceGreetingConfig,
        user_id: str
    ) -> Optional[GreetingAudioResponse]:
        """
        Generate a voice greeting for a user checking in.

        Args:
            user_data: User information (name, phone, branch, volunteer_roles, etc.)
            event_data: Event information (conference name, bus route name, etc.)
            config: Voice greeting configuration
            user_id: User ID for billing

        Returns:
            GreetingAudioResponse with audio URL and metadata, or None if disabled

        Raises:
            Exception: If greeting generation fails
        """
        if not config or not config.enabled:
            logger.debug("Voice greeting disabled, skipping generation")
            return None

        if not self._initialized:
            await self.initialize()

        # Generate greeting text based on type
        if config.greeting_type == "personalized" and config.personalization_enabled:
            greeting_text = self._build_personalized_greeting(
                user_data=user_data,
                event_data=event_data,
                template=config.message_template
            )
        else:
            # Simple greeting - just use template as-is or with basic substitution
            greeting_text = self._build_simple_greeting(
                event_data=event_data,
                template=config.message_template
            )

        logger.info(f"Generating voice greeting: '{greeting_text[:50]}...'")

        # Try dynamic TTS synthesis first
        try:
            synthesis_request = SynthesisRequest(
                provider_id=config.tts_provider,
                text=greeting_text,
                language=config.language,
                voice_id=config.voice_id,
                speed=config.speed,
                pitch=config.pitch,
                remove_silence=True,  # Remove silence to prevent audio cutoff issues
                output_format="mp3"  # Use MP3 for web playback
            )

            result: SynthesisResult = await self.tts_service.synthesize(
                user_id=user_id,
                request=synthesis_request
            )

            # Return audio as data URL for immediate playback (no file storage)
            audio_url = f"data:audio/mp3;base64,{result.audio_base64}"

            greeting_response = GreetingAudioResponse(
                audio_url=audio_url,
                text=greeting_text,
                duration_seconds=result.duration,
                provider_used=result.provider_id,
                cost_usd=result.cost,
                is_fallback=False
            )

            logger.info(
                f"✅ Dynamic TTS greeting generated: "
                f"{result.duration:.2f}s, ${result.cost:.4f}"
            )

            return greeting_response

        except Exception as e:
            logger.warning(f"Dynamic TTS failed: {e}")

            # Fall back to pre-recorded audio if configured
            if config.fallback_audio_url:
                logger.info(f"Using fallback pre-recorded audio: {config.fallback_audio_url}")

                # Use generic greeting text for fallback
                fallback_text = "Welcome! Thank you for checking in."
                if config.message_template and "{user_name}" not in config.message_template:
                    fallback_text = config.message_template

                greeting_response = GreetingAudioResponse(
                    audio_url=config.fallback_audio_url,
                    text=fallback_text,
                    duration_seconds=None,  # Unknown duration for pre-recorded
                    provider_used="fallback",
                    cost_usd=0.0,
                    is_fallback=True
                )

                logger.info(f"✅ Using fallback pre-recorded audio")
                return greeting_response

            else:
                logger.error(f"No fallback audio configured, greeting unavailable")
                # Don't fail the check-in, just return None
                return None

    async def preview_greeting(
        self,
        message_template: str,
        sample_user_data: Dict,
        event_data: Dict,
        tts_provider: str,
        voice_id: Optional[str],
        speed: float,
        pitch: float,
        language: str,
        personalization_enabled: bool,
        user_id: str
    ) -> GreetingAudioResponse:
        """
        Generate a preview of a voice greeting for testing.

        Args:
            message_template: Greeting template text
            sample_user_data: Sample user data for personalization
            event_data: Event data (conference or bus route info)
            tts_provider: TTS provider to use
            voice_id: Voice ID (optional)
            speed: Voice speed (0.5-2.0)
            pitch: Voice pitch (-1.0 to 1.0)
            language: Language code
            personalization_enabled: Whether to use personalization
            user_id: User ID for billing

        Returns:
            GreetingAudioResponse with preview audio

        Raises:
            Exception: If preview generation fails
        """
        if not self._initialized:
            await self.initialize()

        # Generate preview text
        if personalization_enabled:
            greeting_text = self._build_personalized_greeting(
                user_data=sample_user_data,
                event_data=event_data,
                template=message_template
            )
        else:
            greeting_text = self._build_simple_greeting(
                event_data=event_data,
                template=message_template
            )

        # Synthesize speech
        synthesis_request = SynthesisRequest(
            provider_id=tts_provider,
            text=greeting_text,
            language=language,
            voice_id=voice_id,
            speed=speed,
            pitch=pitch,
            output_format="mp3"
        )

        result: SynthesisResult = await self.tts_service.synthesize(
            user_id=user_id,
            request=synthesis_request
        )

        # For preview, return base64 audio directly (no storage)
        audio_url = f"data:audio/mp3;base64,{result.audio_base64}"

        return GreetingAudioResponse(
            audio_url=audio_url,
            text=greeting_text,
            duration_seconds=result.duration,
            provider_used=result.provider_id,
            cost_usd=result.cost
        )

    def _build_personalized_greeting(
        self,
        user_data: Dict,
        event_data: Dict,
        template: Optional[str]
    ) -> str:
        """
        Build personalized greeting text from template and user data.

        Available template variables:
        - {user_name}: User's full name
        - {first_name}: User's first name
        - {branch}: User's branch name
        - {volunteer_role}: User's primary volunteer role
        - {event_name}: Conference/bus route name
        - {venue}: Conference venue

        Args:
            user_data: User information
            event_data: Event information
            template: Greeting template with variables

        Returns:
            Personalized greeting text
        """
        if not template:
            template = "Hello {user_name}, how are you doing today? Thank you for checking in"

        # Extract user information
        user_name = user_data.get("user_name", "friend")
        first_name = user_name.split()[0] if user_name else "friend"
        branch = user_data.get("branch_name", user_data.get("branch", ""))
        volunteer_roles = user_data.get("volunteer_roles", [])
        volunteer_role = volunteer_roles[0] if volunteer_roles else ""

        # Extract event information
        event_name = event_data.get("conference_name", event_data.get("bus_route_name", "our event"))
        venue = event_data.get("venue", "")

        # Build context dictionary for template substitution
        context = {
            "user_name": user_name,
            "first_name": first_name,
            "branch": branch,
            "volunteer_role": volunteer_role,
            "event_name": event_name,
            "venue": venue
        }

        # Substitute variables in template
        try:
            greeting_text = template.format(**context)
        except KeyError as e:
            logger.warning(f"Template variable {e} not found, using default greeting")
            greeting_text = f"Hello {user_name}, how are you doing today? Thank you for checking in"

        return greeting_text

    def _build_simple_greeting(
        self,
        event_data: Dict,
        template: Optional[str]
    ) -> str:
        """
        Build simple greeting text with basic event information.

        Args:
            event_data: Event information
            template: Greeting template

        Returns:
            Simple greeting text
        """
        if not template:
            template = "Welcome! Thank you for checking in."

        # Only substitute event name if present in template
        event_name = event_data.get("conference_name", event_data.get("bus_route_name", ""))

        if "{event_name}" in template and event_name:
            try:
                greeting_text = template.format(event_name=event_name)
            except KeyError:
                greeting_text = template
        else:
            greeting_text = template

        return greeting_text

    async def _save_audio_file(self, audio_base64: str, user_id: str) -> str:
        """
        Save generated audio to file storage.

        Args:
            audio_base64: Base64-encoded audio data
            user_id: User ID (for organizing files)

        Returns:
            Public URL to access the audio file

        Raises:
            Exception: If file save fails
        """
        try:
            # Create storage directory if it doesn't exist
            os.makedirs(self.storage_path, exist_ok=True)

            # Generate unique filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"greeting_{user_id}_{timestamp}.mp3"
            file_path = os.path.join(self.storage_path, filename)

            # Decode and save audio
            audio_bytes = base64.b64decode(audio_base64)
            with open(file_path, "wb") as f:
                f.write(audio_bytes)

            # Return public URL
            audio_url = f"{self.storage_base_url}/{filename}"

            logger.debug(f"Saved greeting audio to {file_path}")

            return audio_url

        except Exception as e:
            logger.error(f"Failed to save audio file: {e}")
            # Fallback to base64 data URL
            return f"data:audio/mp3;base64,{audio_base64}"
