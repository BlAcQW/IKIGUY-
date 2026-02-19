"""
TTS Provider Service - Enhanced Centralized TTS Service

Provides unified access to all TTS providers with integrated billing, usage tracking,
health monitoring, and provider management.

This service wraps the lower-level ai_services TTS infrastructure and adds:
- Automatic cost calculation and wallet deductions
- Provider health monitoring and failover
- Request/response normalization
- Voice cloning support across providers
- Multi-language and multi-speaker support

Usage Example (from any app):
    ```python
    from apps.shared.services.tts_provider_service import (
        TTSProviderService,
        SynthesisRequest,
        VoiceCloneRequest
    )

    # Initialize service
    tts_service = TTSProviderService()
    await tts_service.initialize()

    # Synthesize with automatic billing
    result = await tts_service.synthesize(
        user_id="user_123",
        request=SynthesisRequest(
            provider_id="coqui_xtts",
            text="Hello world",
            language="en",
            voice_id="nova"
        )
    )

    # Voice cloning
    clone_result = await tts_service.synthesize_with_voice_cloning(
        user_id="user_123",
        request=VoiceCloneRequest(
            provider_id="f5tts",
            text="This is cloned voice",
            reference_audio_base64=audio_b64,
            language="en"
        )
    )
    ```

Architecture:
    Apps (Inkwave, StudyFlow, etc.)
        ↓
    TTSProviderService (this file)
        ↓
    ├─> ProviderRegistry (ai_services)
    ├─> HealthMonitor (ai_services)
    ├─> WalletService (wallet integration)
    └─> UsageCalculator (cost calculation)
        ↓
    TTS Provider Endpoints (Coqui, F5-TTS, etc.)
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
import aiohttp
import base64

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class SynthesisRequest(BaseModel):
    """Request for basic TTS synthesis."""
    provider_id: str
    text: str
    language: str = "en"
    voice_id: Optional[str] = None
    speed: float = 1.0
    pitch: float = 0.0
    remove_silence: bool = False
    output_format: str = "wav"


class VoiceCloneRequest(BaseModel):
    """Request for voice cloning TTS synthesis."""
    provider_id: str
    text: str
    reference_audio_base64: str
    language: str = "en"
    speed: float = 1.0
    remove_silence: bool = False
    ref_text: Optional[str] = None  # Transcript of reference audio


class SynthesisResult(BaseModel):
    """Result from TTS synthesis."""
    audio_base64: str
    text: str
    provider_id: str
    voice_id: Optional[str] = None
    duration: float
    processing_time: float
    cost: float
    transaction_id: Optional[str] = None
    format: str = "wav"
    sample_rate: int = 22050


class CostEstimate(BaseModel):
    """Cost estimate for TTS operation."""
    base_cost: float
    voice_cloning_premium: float = 0.0
    provider_premium: float = 0.0
    total_cost: float
    character_count: int
    provider_id: str


class ProviderHealth(BaseModel):
    """Health status of a TTS provider."""
    provider_id: str
    provider_name: str
    status: str  # online, offline, degraded, building
    response_time_ms: Optional[float] = None
    last_checked: datetime
    error: Optional[str] = None


# ============================================================================
# Main Service Class
# ============================================================================

class TTSProviderService:
    """
    Centralized TTS Provider Service with billing integration.

    Manages all TTS providers, handles synthesis requests, tracks usage,
    and integrates with wallet service for automatic billing.
    """

    def __init__(
        self,
        enable_billing: bool = True,
        enable_health_monitoring: bool = True,
        enable_email_alerts: bool = True,
        cache_ttl: int = 30
    ):
        """
        Initialize TTS Provider Service.

        Args:
            enable_billing: Enable automatic wallet deductions
            enable_health_monitoring: Enable background health checks
            enable_email_alerts: Enable email notifications for health issues
            cache_ttl: Provider status cache TTL in seconds
        """
        self.enable_billing = enable_billing
        self.enable_health_monitoring = enable_health_monitoring
        self.enable_email_alerts = enable_email_alerts
        self.cache_ttl = cache_ttl

        # Will be initialized in initialize()
        self.registry = None
        self.health_monitor = None
        self.health_notifier = None
        self.cache_warmer = None
        self.wallet_service = None
        self.usage_calculator = None

        self._initialized = False

        logger.info(
            f"TTSProviderService created (billing={enable_billing}, "
            f"health_monitoring={enable_health_monitoring}, "
            f"email_alerts={enable_email_alerts})"
        )

    async def initialize(self) -> None:
        """
        Initialize service dependencies.

        Must be called before using the service.
        Loads provider registry, starts health monitoring, and initializes billing.
        """
        if self._initialized:
            logger.warning("TTSProviderService already initialized")
            return

        try:
            # Import here to avoid circular dependencies
            from apps.shared.integration.ai_services import (
                ProviderRegistry,
                get_global_registry,
                HealthMonitorService,
                ProviderType,
            )

            # Initialize provider registry
            self.registry = get_global_registry()

            # Load TTS provider configurations
            await self._load_tts_providers()

            # Initialize health monitoring
            if self.enable_health_monitoring:
                import os
                # Configurable health check interval (default: 5 minutes)
                check_interval = int(os.getenv("TTS_HEALTH_CHECK_INTERVAL", "300"))
                self.health_monitor = HealthMonitorService(
                    registry=self.registry,
                    check_interval=check_interval,
                    timeout=10
                )

                # Initialize email alerts if enabled
                if self.enable_email_alerts:
                    import os
                    from apps.shared.services.tts_health_notifier import TTSHealthNotifier

                    # Get SMTP configuration from environment
                    smtp_host = os.getenv("SMTP_HOST", "mail.ailabsafrica.com")
                    smtp_port = int(os.getenv("SMTP_PORT", "587"))
                    smtp_username = os.getenv("SMTP_USERNAME", "noreply@ailabsafrica.com")
                    smtp_password = os.getenv("SMTP_PASSWORD", "")
                    from_email = os.getenv("SENDER_EMAIL", "noreply@ailabsafrica.com")
                    admin_emails = os.getenv("UNIVERSAL_ADMIN_EMAILS", "alfred.anyan@gmail.com")
                    # Use second admin email (alfred.anyan@gmail.com) since admin@ailabsafrica.com doesn't exist on mail server
                    emails_list = admin_emails.split(",")
                    admin_email = emails_list[1].strip() if len(emails_list) > 1 else emails_list[0].strip()

                    # Email cooldown: don't spam alerts (default: 30 minutes)
                    email_cooldown = int(os.getenv("TTS_ALERT_COOLDOWN_MINUTES", "30"))
                    self.health_notifier = TTSHealthNotifier(
                        admin_email=admin_email,
                        from_email=from_email,
                        smtp_host=smtp_host,
                        smtp_port=smtp_port,
                        smtp_username=smtp_username,
                        smtp_password=smtp_password,
                        enable_notifications=True,
                        cooldown_minutes=email_cooldown
                    )
                    await self.health_notifier.initialize(self.health_monitor)
                    logger.info(f"Email alerts initialized for TTS health monitoring (admin: {admin_email})")

                await self.health_monitor.start()
                logger.info("Health monitoring started")

                # Initialize background cache warmer
                # This keeps the centralized MongoDB provider cache warm
                # so other apps (InkWave, StudyFlow, etc.) get instant responses
                try:
                    from apps.shared.tts.provider_cache import BackgroundCacheWarmer
                    from apps.shared.routes.tts_routes import _perform_health_checks

                    self.cache_warmer = BackgroundCacheWarmer(
                        refresh_callback=_perform_health_checks,
                        interval_minutes=30,  # Refresh cache every 30 minutes
                        app_name="core_backend_tts_service"
                    )
                    await self.cache_warmer.start()
                    logger.info("Background provider cache warmer started (30-minute interval)")
                except Exception as e:
                    logger.warning(f"Failed to start cache warmer: {e}")
                    # Non-fatal - cache will be populated on first request

            # Initialize billing services
            if self.enable_billing:
                await self._initialize_billing()

            self._initialized = True
            logger.info("TTSProviderService initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize TTSProviderService: {e}")
            raise

    async def _load_tts_providers(self) -> None:
        """Load TTS provider configurations into registry."""
        from apps.shared.integration.ai_services import (
            get_default_tts_providers_config,
            ProviderType,
        )

        # Get default TTS providers config
        tts_config = get_default_tts_providers_config()

        # Register all providers
        self.registry.register_providers_from_config(
            tts_config,
            provider_type=ProviderType.TTS
        )

        provider_count = len(self.registry.get_providers_by_type(ProviderType.TTS))
        logger.info(f"Loaded {provider_count} TTS providers")

    async def _initialize_billing(self) -> None:
        """Initialize wallet service and usage calculator."""
        try:
            from apps.shared.integration.wallet import create_wallet_service_from_env
            from apps.shared.integration.usage_calculator import UsageCalculator

            # Initialize wallet service using environment config
            self.wallet_service = await create_wallet_service_from_env()

            # Initialize usage calculator (default tier)
            self.usage_calculator = UsageCalculator()

            logger.info("✓ TTS Billing services initialized")

        except Exception as e:
            logger.error(f"Failed to initialize TTS billing: {e}")
            # Don't fail if billing can't be initialized
            self.enable_billing = False
            logger.warning("TTS Billing disabled due to initialization failure")

    async def shutdown(self) -> None:
        """Shutdown service and cleanup resources."""
        if self.cache_warmer:
            await self.cache_warmer.stop()
            logger.info("Cache warmer stopped")

        if self.health_monitor:
            await self.health_monitor.stop()
            logger.info("Health monitoring stopped")

        self._initialized = False
        logger.info("TTSProviderService shut down")

    # ========================================================================
    # Provider Management
    # ========================================================================

    async def get_available_providers(
        self,
        force_refresh: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get all available TTS providers with current health status.

        Args:
            force_refresh: Force refresh provider status

        Returns:
            Dict mapping provider IDs to provider info
        """
        from apps.shared.integration.ai_services import ProviderType

        if not self._initialized:
            await self.initialize()

        providers = self.registry.get_providers_by_type(ProviderType.TTS)

        # Optionally refresh health status
        if force_refresh and self.health_monitor:
            # Trigger immediate health check
            await self.health_monitor.check_all_providers()

        result = {}
        for provider in providers:
            result[provider.id] = {
                "id": provider.id,
                "name": provider.name,
                "endpoint": provider.endpoint,
                "status": provider.status,
                "languages": provider.languages,
                "languageList": provider.languageList,
                "capabilities": provider.capabilities.dict(),
                "description": provider.description,
                "icon": provider.icon,
                "lastChecked": provider.lastChecked,
                "responseTime": provider.responseTime,
            }

        return result

    async def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific provider by ID.

        Args:
            provider_id: Provider identifier

        Returns:
            Provider info dict or None
        """
        if not self._initialized:
            await self.initialize()

        provider = self.registry.get_provider(provider_id)

        if not provider:
            return None

        return {
            "id": provider.id,
            "name": provider.name,
            "endpoint": provider.endpoint,
            "status": provider.status,
            "capabilities": provider.capabilities.dict(),
            "languages": provider.languages,
            "languageList": provider.languageList,
        }

    async def get_providers_with_capability(
        self,
        capability: str
    ) -> List[Dict[str, Any]]:
        """
        Get providers supporting specific capability.

        Args:
            capability: Capability name (e.g., "voiceCloning")

        Returns:
            List of providers with the capability
        """
        from apps.shared.integration.ai_services import ProviderType

        if not self._initialized:
            await self.initialize()

        providers = self.registry.get_providers_by_capability(
            capability,
            provider_type=ProviderType.TTS
        )

        return [
            {
                "id": p.id,
                "name": p.name,
                "endpoint": p.endpoint,
                "status": p.status,
            }
            for p in providers
        ]

    # ========================================================================
    # Cost Estimation
    # ========================================================================

    async def estimate_cost(
        self,
        text: str,
        provider_id: str,
        voice_cloning: bool = False
    ) -> CostEstimate:
        """
        Estimate cost for TTS synthesis.

        Args:
            text: Text to synthesize
            provider_id: Provider to use
            voice_cloning: Whether voice cloning will be used

        Returns:
            CostEstimate with breakdown
        """
        char_count = len(text)

        # Base cost: $0.015 per 1000 characters
        base_cost = (char_count / 1000) * 0.015

        # Voice cloning premium: +$0.05
        voice_cloning_premium = 0.05 if voice_cloning else 0.0

        # Provider premium (some providers cost more)
        provider_premium_multiplier = 1.0
        premium_providers = ["styletts2", "f5tts", "openvoice"]
        if provider_id in premium_providers:
            provider_premium_multiplier = 2.0

        provider_premium = base_cost * (provider_premium_multiplier - 1.0)

        total_cost = base_cost + voice_cloning_premium + provider_premium

        return CostEstimate(
            base_cost=base_cost,
            voice_cloning_premium=voice_cloning_premium,
            provider_premium=provider_premium,
            total_cost=total_cost,
            character_count=char_count,
            provider_id=provider_id
        )

    # ========================================================================
    # TTS Synthesis Operations
    # ========================================================================

    async def synthesize(
        self,
        user_id: str,
        request: SynthesisRequest,
        skip_billing: bool = False
    ) -> SynthesisResult:
        """
        Synthesize speech with automatic billing.

        Args:
            user_id: User ID for billing
            request: Synthesis request parameters
            skip_billing: Skip wallet deduction (for testing)

        Returns:
            SynthesisResult with audio and transaction details

        Raises:
            ValueError: If provider is offline or parameters invalid
            Exception: If billing fails or synthesis fails
        """
        if not self._initialized:
            await self.initialize()

        # 1. Validate provider
        provider = self.registry.get_provider(request.provider_id)
        if not provider:
            raise ValueError(f"Provider {request.provider_id} not found")

        if provider.status != "online":
            raise ValueError(
                f"Provider {request.provider_id} is {provider.status}, "
                f"cannot process request"
            )

        # 2. Estimate cost
        cost_estimate = await self.estimate_cost(
            request.text,
            request.provider_id,
            voice_cloning=False
        )

        # 3. Check balance and deduct (if billing enabled)
        transaction_id = None
        if self.enable_billing and not skip_billing:
            transaction_id = await self._process_billing(
                user_id=user_id,
                cost=cost_estimate.total_cost,
                description=f"TTS: {provider.name} - {len(request.text)} chars",
                metadata={
                    "provider_id": request.provider_id,
                    "character_count": cost_estimate.character_count,
                    "service": "tts_synthesis"
                }
            )

        # 4. Make synthesis request to provider
        start_time = datetime.now()
        try:
            audio_base64, duration = await self._call_provider_synthesize(
                provider=provider,
                request=request
            )
        except Exception as e:
            # If synthesis fails, refund the transaction
            if transaction_id and self.wallet_service:
                await self.wallet_service.refund(
                    transaction_id=transaction_id,
                    reason=f"Synthesis failed: {str(e)}"
                )
            raise

        processing_time = (datetime.now() - start_time).total_seconds()

        # 5. Return result
        return SynthesisResult(
            audio_base64=audio_base64,
            text=request.text,
            provider_id=request.provider_id,
            voice_id=request.voice_id,
            duration=duration,
            processing_time=processing_time,
            cost=cost_estimate.total_cost,
            transaction_id=transaction_id,
            format=request.output_format,
        )

    async def synthesize_with_voice_cloning(
        self,
        user_id: str,
        request: VoiceCloneRequest,
        skip_billing: bool = False
    ) -> SynthesisResult:
        """
        Synthesize speech with voice cloning.

        Args:
            user_id: User ID for billing
            request: Voice cloning request
            skip_billing: Skip wallet deduction (for testing)

        Returns:
            SynthesisResult with cloned voice audio
        """
        if not self._initialized:
            await self.initialize()

        # 1. Validate provider supports voice cloning
        provider = self.registry.get_provider(request.provider_id)
        if not provider:
            raise ValueError(f"Provider {request.provider_id} not found")

        if not provider.capabilities.voiceCloning:
            raise ValueError(
                f"Provider {request.provider_id} does not support voice cloning"
            )

        if provider.status != "online":
            raise ValueError(f"Provider {request.provider_id} is offline")

        # 2. Estimate cost (with voice cloning premium)
        cost_estimate = await self.estimate_cost(
            request.text,
            request.provider_id,
            voice_cloning=True
        )

        # 3. Process billing
        transaction_id = None
        if self.enable_billing and not skip_billing:
            transaction_id = await self._process_billing(
                user_id=user_id,
                cost=cost_estimate.total_cost,
                description=f"Voice Cloning: {provider.name}",
                metadata={
                    "provider_id": request.provider_id,
                    "service": "voice_cloning"
                }
            )

        # 4. Make voice cloning request
        start_time = datetime.now()
        try:
            audio_base64, duration = await self._call_provider_voice_clone(
                provider=provider,
                request=request
            )
        except Exception as e:
            # Refund on failure
            if transaction_id and self.wallet_service:
                await self.wallet_service.refund(
                    transaction_id=transaction_id,
                    reason=f"Voice cloning failed: {str(e)}"
                )
            raise

        processing_time = (datetime.now() - start_time).total_seconds()

        return SynthesisResult(
            audio_base64=audio_base64,
            text=request.text,
            provider_id=request.provider_id,
            duration=duration,
            processing_time=processing_time,
            cost=cost_estimate.total_cost,
            transaction_id=transaction_id,
        )

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    async def _process_billing(
        self,
        user_id: str,
        cost: float,
        description: str,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        Process wallet deduction for TTS operation.

        Args:
            user_id: User ID
            cost: Amount to deduct
            description: Transaction description
            metadata: Additional metadata

        Returns:
            Transaction ID or None if billing skipped (no wallet)
        """
        if not self.wallet_service:
            logger.warning("Wallet service not initialized, skipping billing")
            return None

        try:
            from decimal import Decimal
            from apps.shared.integration.wallet import Currency, WalletNotFoundError

            # Get user wallet (gracefully handle missing wallet)
            try:
                wallet = await self.wallet_service.get_wallet_by_user(
                    user_id=user_id,
                    currency=Currency.GHS  # GHS is the default currency
                )
            except WalletNotFoundError:
                logger.warning(
                    f"No wallet found for user {user_id}, skipping TTS billing"
                )
                return None

            if not wallet:
                logger.warning(f"No wallet found for user {user_id}, skipping TTS billing")
                return None

            # Deduct credits (allow negative balance to not block TTS)
            transaction = await self.wallet_service.debit(
                wallet_id=wallet.id,
                amount=Decimal(str(cost)),
                description=description,
                metadata=metadata,
                allow_negative=True  # Allow negative balance for TTS usage
            )

            return str(transaction.id)

        except Exception as e:
            logger.error(f"TTS billing failed: {e}")
            # Don't fail the TTS request if billing fails
            return None

    async def _call_provider_synthesize(
        self,
        provider,
        request: SynthesisRequest
    ) -> tuple[str, float]:
        """
        Call provider's synthesize endpoint.

        For voice-cloning-only providers (Coqui XTTS, F5-TTS, StyleTTS2),
        uses a default reference voice if none provided.

        Args:
            provider: Provider instance
            request: Synthesis request

        Returns:
            (audio_base64, duration) tuple
        """
        # Providers that require reference audio
        voice_cloning_only = ["coqui_xtts", "f5tts", "styletts2"]

        # If provider requires reference audio, use specified or default reference voice
        if provider.id in voice_cloning_only:
            # Map voice IDs to reference voice files
            available_voices = {
                "nana_aba": "nana_aba.wav",
                "adom_okyere": "adom_okyere.wav",
                "juliet_bawuah": "juliet_bawuah.wav",
                "nana_aba_24bit": "nana_aba_24_bit.wav",
                "archbishop_1": "archbishop_1_ref.wav",
                "archbishop_2": "archbishop_2_ref.wav",
            }

            # Map voice IDs to reference text (transcripts of reference audio)
            # This prevents F5-TTS from auto-transcribing incorrectly and including unwanted content
            voice_transcripts = {
                "archbishop_1": "Living by the scriptures is essential for our faith and walk with God. The Word of God guides us in all things.",
                "archbishop_2": "Living by the scriptures is essential for our faith and walk with God. The Word of God guides us in all things.",
                "nana_aba": "Welcome to our service. Thank you for being here today.",
                "adom_okyere": "Welcome to our service. Thank you for being here today.",
                "juliet_bawuah": "Welcome to our service. Thank you for being here today.",
                "nana_aba_24bit": "Welcome to our service. Thank you for being here today.",
            }

            # Use voice_id if provided, otherwise use default
            voice_id = request.voice_id or "nana_aba"

            # Load reference audio
            import os

            # Check if this is a cloned voice (starts with "voice_")
            if voice_id.startswith("voice_"):
                # Look for cloned voice in storage directory
                # Try to find the voice file by fetching from API or checking directory
                cloned_voices_dir = "/opt/kasaai/apps/shared/storage/voice_clones"

                # Common mappings for cloned voices
                cloned_voice_files = {
                    "voice_archbishop_official": "archbishop_56min.wav",
                }

                voice_file = cloned_voice_files.get(voice_id)
                if voice_file:
                    voice_path = f"{cloned_voices_dir}/{voice_file}"
                    logger.info(f"Using cloned voice '{voice_id}' ({voice_file}) for {provider.id}")
                else:
                    # Try to find any file matching the voice_id in cloned voices directory
                    logger.warning(f"Cloned voice '{voice_id}' not found in mappings, using default")
                    voice_file = available_voices.get("nana_aba", "nana_aba.wav")
                    voice_path = f"/opt/kasaai/apps/voice-lab/voices/{voice_file}"
            else:
                # Use standard voice from voice-lab directory
                voice_file = available_voices.get(voice_id, "nana_aba.wav")
                voice_path = f"/opt/kasaai/apps/voice-lab/voices/{voice_file}"
                logger.info(f"Using reference voice '{voice_id}' ({voice_file}) for {provider.id}")

            if not os.path.exists(voice_path):
                raise ValueError(
                    f"Reference voice file not found: {voice_path}"
                )

            # Read and encode reference audio
            with open(voice_path, "rb") as f:
                ref_audio_bytes = f.read()
                ref_audio_base64 = base64.b64encode(ref_audio_bytes).decode()

            # Get reference text for this voice
            # This is critical for F5-TTS - without proper ref_text, it auto-transcribes
            # the reference audio incorrectly and includes that content in output
            ref_text = voice_transcripts.get(voice_id, "Welcome to our service. Thank you for being here today.")

            # Provider-specific language normalization
            # MeloTTS requires uppercase language codes (EN, ES, FR, ZH, JP, KR)
            language = request.language
            if provider.id == "melotts":
                language = language.upper()

            # Create voice clone request
            clone_request = VoiceCloneRequest(
                provider_id=provider.id,
                text=request.text,
                reference_audio_base64=ref_audio_base64,
                language=language,
                speed=request.speed,
                remove_silence=request.remove_silence,
                ref_text=ref_text  # Proper transcript prevents auto-transcription issues
            )

            # Call voice cloning endpoint
            return await self._call_provider_voice_clone(provider, clone_request)

        # Standard synthesis for other providers
        endpoint = f"{provider.endpoint}/synthesize"

        # Provider-specific language normalization
        # MeloTTS requires uppercase language codes (EN, ES, FR, ZH, JP, KR)
        language = request.language
        if provider.id == "melotts":
            language = language.upper()

        payload = {
            "text": request.text,
            "language": language,
            "speed": request.speed,
            "pitch": request.pitch,  # Include pitch from Voice Settings
            "remove_silence": request.remove_silence,
        }

        # Provider-specific voice parameter naming
        # Kokoro uses "voice", others use "voice_id" or "speaker"
        if request.voice_id:
            if provider.id == "kokoro":
                payload["voice"] = request.voice_id
            else:
                payload["voice_id"] = request.voice_id
                # Also add as "speaker" for providers that use that field
                payload["speaker"] = request.voice_id

        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"Provider returned {response.status}: {error_text}"
                    )

                # Check content type - some providers return raw audio, others return JSON
                content_type = response.headers.get('Content-Type', '')

                if 'audio/' in content_type:
                    # Provider returned raw audio (e.g., Kokoro, OpenVoice)
                    logger.info(f"Provider {provider.id} returned raw audio ({content_type})")
                    audio_bytes = await response.read()
                    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

                    # Estimate duration from audio size (rough estimate)
                    # Assuming 16-bit, 24kHz mono WAV: 48000 bytes/sec
                    duration = len(audio_bytes) / 48000.0

                    return audio_base64, duration
                else:
                    # Provider returned JSON (e.g., MeloTTS, custom providers)
                    result = await response.json()

                    # Extract audio and duration from response
                    audio_base64 = result.get("audio_base64") or result.get("audio")
                    duration = result.get("duration", 0.0)

                    return audio_base64, duration

    async def _call_provider_voice_clone(
        self,
        provider,
        request: VoiceCloneRequest
    ) -> tuple[str, float]:
        """
        Call provider's voice cloning endpoint.

        Args:
            provider: Provider instance
            request: Voice clone request

        Returns:
            (audio_base64, duration) tuple
        """
        # Different providers have different endpoints for voice cloning
        # F5-TTS and StyleTTS2 use /clone
        # Others use /synthesize_with_reference

        if provider.id in ["f5tts", "styletts2"]:
            endpoint = f"{provider.endpoint}/clone"
        else:
            endpoint = f"{provider.endpoint}/synthesize_with_reference"

        # Prepare FormData for file upload
        form_data = aiohttp.FormData()

        # Decode base64 audio
        ref_audio_bytes = base64.b64decode(request.reference_audio_base64)

        # Different providers use different field names
        # Coqui XTTS uses 'reference_audio', others use 'ref_audio'
        audio_field_name = 'reference_audio' if provider.id == 'coqui_xtts' else 'ref_audio'

        form_data.add_field(
            audio_field_name,
            ref_audio_bytes,
            filename='reference.wav',
            content_type='audio/wav'
        )

        form_data.add_field('text', request.text)
        form_data.add_field('language', request.language)
        form_data.add_field('speed', str(request.speed))
        form_data.add_field('remove_silence', str(request.remove_silence).lower())
        # Always send empty ref_text - let F5-TTS handle internally
        form_data.add_field('ref_text', "")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint,
                data=form_data,
                timeout=aiohttp.ClientTimeout(total=120)  # Voice cloning takes longer
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"Voice cloning failed ({response.status}): {error_text}"
                    )

                # Check content type to determine response format
                content_type = response.headers.get('Content-Type', '')

                if 'application/json' in content_type:
                    # JSON response with base64 audio
                    result = await response.json()
                    audio_base64 = result.get("audio_base64") or result.get("audio")
                    duration = result.get("duration", 0.0)
                elif 'audio/' in content_type:
                    # Direct audio file response - encode to base64
                    audio_bytes = await response.read()
                    audio_base64 = base64.b64encode(audio_bytes).decode()

                    # Estimate duration from file size (rough estimate: 16kHz, 16-bit, mono = 32KB/sec)
                    duration = len(audio_bytes) / 32000.0
                else:
                    raise Exception(
                        f"Unexpected content type: {content_type}"
                    )

                return audio_base64, duration


# ============================================================================
# Singleton Instance (optional)
# ============================================================================

# Global instance for apps that want a shared service
_global_tts_service: Optional[TTSProviderService] = None


async def get_tts_service(
    enable_billing: bool = True,
    enable_health_monitoring: bool = True
) -> TTSProviderService:
    """
    Get or create global TTS service instance.

    Args:
        enable_billing: Enable billing integration
        enable_health_monitoring: Enable health monitoring

    Returns:
        Initialized TTSProviderService instance
    """
    global _global_tts_service

    if _global_tts_service is None:
        _global_tts_service = TTSProviderService(
            enable_billing=enable_billing,
            enable_health_monitoring=enable_health_monitoring
        )
        await _global_tts_service.initialize()

    return _global_tts_service


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    async def test_tts_service():
        """Test the TTS service."""

        # Initialize service
        service = TTSProviderService(
            enable_billing=False,  # Disable for testing
            enable_health_monitoring=True
        )
        await service.initialize()

        # Get available providers
        providers = await service.get_available_providers()
        print(f"Available providers: {list(providers.keys())}")

        # Estimate cost
        cost = await service.estimate_cost(
            text="Hello world, this is a test.",
            provider_id="coqui_xtts",
            voice_cloning=False
        )
        print(f"Estimated cost: ${cost.total_cost:.4f}")

        # Synthesize (without billing)
        request = SynthesisRequest(
            provider_id="coqui_xtts",
            text="Hello world, this is a test.",
            language="en",
            speed=1.0
        )

        result = await service.synthesize(
            user_id="test_user",
            request=request,
            skip_billing=True
        )

        print(f"Synthesis complete: {len(result.audio_base64)} bytes, "
              f"duration: {result.duration}s, cost: ${result.cost:.4f}")

        # Shutdown
        await service.shutdown()

    asyncio.run(test_tts_service())
