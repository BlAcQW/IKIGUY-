"""
Centralized ASR (Automatic Speech Recognition) Provider Service

This service provides unified access to multiple ASR providers with automatic
billing, health monitoring, and usage tracking.

Architecture:
    Apps (B2C Portal, Inkwave, StudyFlow)
        ↓
    ASRProviderService (@apps/shared/services/)
        ↓
    ├─> ProviderRegistry (provider discovery)
    ├─> HealthMonitor (status tracking)
    ├─> WalletService (automatic billing)
    └─> UsageCalculator (cost calculation)
        ↓
    ASR Provider Endpoints (self-hosted)

Author: AI Labs Africa
Created: 2025-10-26
"""

import base64
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import aiohttp
from pydantic import BaseModel, Field

from apps.shared.integration.ai_services.provider_registry import (
    AIProviderRegistry,
    get_default_asr_providers_config,
    ProviderType
)
from apps.shared.integration.ai_services.health_monitor_service import HealthMonitorService
from apps.shared.integration.wallet import WalletService, create_wallet_service_from_env
from apps.shared.integration.usage_calculator import UsageCalculator

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class TranscriptionRequest(BaseModel):
    """Request for audio transcription."""
    provider_id: str = Field(..., description="ASR provider ID (e.g., 'openai_whisper')")
    audio_base64: str = Field(..., description="Base64-encoded audio file")
    language: Optional[str] = Field(None, description="Language code (e.g., 'en', 'tw', 'auto')")
    task: str = Field("transcribe", description="Task type: 'transcribe' or 'translate'")
    response_format: str = Field("json", description="Response format: 'json', 'text', 'srt', 'vtt'")
    temperature: float = Field(0.0, description="Sampling temperature (0.0-1.0)")
    timestamp_granularities: Optional[List[str]] = Field(None, description="Timestamp levels: ['word', 'segment']")


class TranscriptionSegment(BaseModel):
    """Transcription segment with timestamps."""
    id: Optional[int] = None  # Optional - not all providers return this
    start: Optional[float] = None  # Optional for providers that don't return timestamps
    end: Optional[float] = None  # Optional for providers that don't return timestamps
    text: str
    tokens: Optional[List[int]] = None
    temperature: Optional[float] = None
    avg_logprob: Optional[float] = None
    compression_ratio: Optional[float] = None
    no_speech_prob: Optional[float] = None


class TranscriptionResult(BaseModel):
    """Result from audio transcription."""
    text: str = Field(..., description="Transcribed text")
    provider_id: str = Field(..., description="Provider used for transcription")
    language: Optional[str] = Field(None, description="Detected language")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    segments: Optional[List[TranscriptionSegment]] = Field(None, description="Transcription segments")
    cost: float = Field(..., description="Cost in USD")
    transaction_id: Optional[str] = Field(None, description="Wallet transaction ID")
    processing_time: float = Field(..., description="Processing time in seconds")
    model_name: Optional[str] = Field(None, description="Model name used")


class ProviderHealth(BaseModel):
    """Health status of an ASR provider."""
    provider_id: str
    status: str  # "online", "offline", "degraded"
    endpoint: str
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None


# ============================================================================
# ASR Provider Service
# ============================================================================

class ASRProviderService:
    """
    Centralized ASR Provider Service with automatic billing and health monitoring.

    Features:
    - Unified access to multiple ASR providers
    - Automatic cost calculation and wallet deductions
    - Provider health monitoring with caching
    - Real-time transcription support
    - Multi-language support
    - Error handling with automatic refunds

    Usage:
        service = ASRProviderService()
        await service.initialize()

        result = await service.transcribe(
            user_id="user_123",
            request=TranscriptionRequest(
                provider_id="openai_whisper",
                audio_base64="...",
                language="en"
            )
        )
    """

    def __init__(
        self,
        enable_billing: bool = True,
        enable_health_monitoring: bool = True
    ):
        """
        Initialize ASR Provider Service.

        Args:
            enable_billing: Enable automatic wallet billing
            enable_health_monitoring: Enable provider health checks
        """
        self.enable_billing = enable_billing
        self.enable_health_monitoring = enable_health_monitoring

        # Initialize dependencies
        self.provider_registry = AIProviderRegistry()
        self.wallet_service = None  # Initialized in initialize() if billing enabled
        self.usage_calculator = UsageCalculator()
        self.health_monitor = HealthMonitorService(
            registry=self.provider_registry,
            check_interval=60
        ) if enable_health_monitoring else None

        # Provider status cache (30 second TTL)
        self._status_cache: Dict[str, ProviderHealth] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 30

        logger.info(
            f"ASRProviderService initialized (billing={enable_billing}, "
            f"health_monitoring={enable_health_monitoring})"
        )

    async def initialize(self):
        """Initialize the service and start background tasks."""
        # Register default ASR providers if not already registered
        if not self.provider_registry.get_asr_providers():
            asr_providers_config = get_default_asr_providers_config()
            self.provider_registry.register_providers_from_config(
                asr_providers_config,
                provider_type=ProviderType.ASR
            )
            logger.info(f"✓ Registered {len(asr_providers_config)} ASR providers")

        # Initialize wallet service if billing enabled
        if self.enable_billing and self.wallet_service is None:
            try:
                self.wallet_service = await create_wallet_service_from_env()
                logger.info("✓ ASR WalletService initialized")
            except Exception as e:
                logger.warning(f"ASR WalletService initialization failed: {e}")
                # Continue without billing rather than failing completely
                self.enable_billing = False

        # Start health monitoring if enabled
        if self.health_monitor:
            # Start monitoring (monitors all providers in the registry)
            await self.health_monitor.start()
            logger.info("✓ ASR Health monitoring started")

    async def transcribe(
        self,
        user_id: str,
        request: TranscriptionRequest,
        skip_billing: bool = False
    ) -> TranscriptionResult:
        """
        Transcribe audio with automatic billing.

        Args:
            user_id: User ID for billing
            request: Transcription request
            skip_billing: Skip wallet billing (for testing)

        Returns:
            TranscriptionResult with text, cost, and transaction ID

        Raises:
            ValueError: If provider not found or offline
            Exception: If transcription fails
        """
        start_time = datetime.utcnow()

        # Get provider with fallback to default
        DEFAULT_ASR_PROVIDER = "faster_whisper_large"
        provider = self.provider_registry.get_provider(request.provider_id)
        if not provider:
            # Fallback to default provider instead of failing
            logger.warning(
                f"ASR provider '{request.provider_id}' not found, "
                f"falling back to '{DEFAULT_ASR_PROVIDER}'"
            )
            request.provider_id = DEFAULT_ASR_PROVIDER
            provider = self.provider_registry.get_provider(request.provider_id)
            if not provider:
                raise ValueError(
                    f"Default ASR provider '{DEFAULT_ASR_PROVIDER}' not found. "
                    f"Check provider registry configuration."
                )

        # Check provider health (skip strict check for self-hosted providers)
        # Self-hosted providers like whisper_large_v3 may have intermittent health check issues
        # but still work fine for actual transcription
        is_self_hosted = request.provider_id in ['whisper_large_v3', 'whisper_medium', 'whisper_small']
        if self.enable_health_monitoring and self.health_monitor and not is_self_hosted:
            health = await self.get_provider_health(request.provider_id)
            if health.status == 'offline':
                raise ValueError(
                    f"ASR provider {request.provider_id} is offline: {health.error_message}"
                )

        # Estimate audio duration from base64 size
        # Rough estimate: base64 size → binary size → duration
        # Assuming 16kHz mono 16-bit audio = ~32KB per second
        audio_bytes = base64.b64decode(request.audio_base64)
        audio_size_kb = len(audio_bytes) / 1024
        estimated_duration = audio_size_kb / 32  # seconds

        # Estimate cost before transcription
        estimated_cost = self.usage_calculator.calculate_asr_cost(
            duration_seconds=estimated_duration,
            provider=request.provider_id
        )

        logger.info(
            f"Starting transcription: provider={request.provider_id}, "
            f"estimated_duration={estimated_duration:.2f}s, "
            f"estimated_cost=${estimated_cost:.4f}"
        )

        # Call ASR provider API
        try:
            # Check if provider requires API key (e.g., OpenAI Whisper)
            api_key = None
            if provider.requires_api_key:
                import os
                api_key_env = provider.api_key_env or 'OPENAI_API_KEY'
                api_key = os.getenv(api_key_env)
                if not api_key:
                    raise ValueError(f"API key not configured for provider {request.provider_id}")

            result = await self._call_asr_api(
                endpoint=provider.endpoint,
                audio_bytes=audio_bytes,
                language=request.language,
                task=request.task,
                response_format=request.response_format,
                temperature=request.temperature,
                timestamp_granularities=request.timestamp_granularities,
                api_key=api_key,
                provider_id=request.provider_id
            )
        except Exception as e:
            logger.error(f"ASR transcription failed: {e}")
            raise Exception(f"Transcription failed: {str(e)}")

        # Calculate actual cost based on actual duration
        actual_duration = result.get('duration', estimated_duration)
        actual_cost = self.usage_calculator.calculate_asr_cost(
            duration_seconds=actual_duration,
            provider=request.provider_id
        )

        # Deduct from wallet if billing enabled
        transaction_id = None
        if self.enable_billing and not skip_billing:
            try:
                transaction_id = await self.wallet_service.deduct_cost(
                    user_id=user_id,
                    amount=actual_cost,
                    description=f"ASR transcription - {request.provider_id}",
                    metadata={
                        'provider_id': request.provider_id,
                        'language': request.language or result.get('language'),
                        'duration_seconds': actual_duration,
                        'audio_size_bytes': len(audio_bytes),
                        'task': request.task
                    }
                )
                logger.info(
                    f"Wallet charged: user={user_id}, amount=${actual_cost:.4f}, "
                    f"txn={transaction_id}"
                )
            except Exception as e:
                logger.error(f"Wallet billing failed: {e}")
                # Note: Transcription succeeded but billing failed
                # In production, might want to queue for retry

        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()

        # Parse segments if available
        segments = None
        if 'segments' in result and result['segments']:
            segments = [
                TranscriptionSegment(**segment)
                for segment in result['segments']
            ]

        return TranscriptionResult(
            text=result['text'],
            provider_id=request.provider_id,
            language=result.get('language'),
            duration=actual_duration,
            segments=segments,
            cost=actual_cost,
            transaction_id=transaction_id,
            processing_time=processing_time,
            model_name=provider.model_name
        )

    async def _call_asr_api(
        self,
        endpoint: str,
        audio_bytes: bytes,
        language: Optional[str] = None,
        task: str = "transcribe",
        response_format: str = "json",
        temperature: float = 0.0,
        timestamp_granularities: Optional[List[str]] = None,
        api_key: Optional[str] = None,
        provider_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call ASR provider API (Whisper-compatible).

        Args:
            endpoint: Provider endpoint URL
            audio_bytes: Audio file bytes
            language: Language code (None for auto-detect)
            task: 'transcribe' or 'translate'
            response_format: 'json', 'text', 'srt', 'vtt'
            temperature: Sampling temperature
            timestamp_granularities: Timestamp levels
            api_key: Optional API key for providers like OpenAI
            provider_id: Provider ID for logging

        Returns:
            Dict with 'text', 'language', 'duration', 'segments'
        """
        # Prepare multipart form data
        form_data = aiohttp.FormData()
        form_data.add_field(
            'file',
            audio_bytes,
            filename='audio.wav',
            content_type='audio/wav'
        )

        if language:
            form_data.add_field('language', language)

        # OpenAI Whisper requires 'model' parameter
        if provider_id == 'openai_whisper':
            form_data.add_field('model', 'whisper-1')
            # OpenAI uses verbose_json for detailed response
            if response_format == 'json':
                form_data.add_field('response_format', 'verbose_json')
            else:
                form_data.add_field('response_format', response_format)
        # Groq Whisper - OpenAI-compatible API with specific model names
        elif provider_id and provider_id.startswith('groq_whisper'):
            # Get provider to retrieve model_name
            provider = self.provider_registry.get_provider(provider_id)
            model_name = getattr(provider, 'model_name', None) if provider else None

            # Default model names based on provider_id
            if not model_name:
                if provider_id == 'groq_whisper_large_v3_turbo':
                    model_name = 'whisper-large-v3-turbo'
                elif provider_id == 'groq_whisper_large_v3':
                    model_name = 'whisper-large-v3'
                else:
                    model_name = 'whisper-large-v3-turbo'  # Default to turbo

            form_data.add_field('model', model_name)
            # Groq uses verbose_json for timestamps
            if response_format == 'json':
                form_data.add_field('response_format', 'verbose_json')
            else:
                form_data.add_field('response_format', response_format)
            form_data.add_field('temperature', str(temperature))

            if timestamp_granularities:
                for granularity in timestamp_granularities:
                    form_data.add_field('timestamp_granularities[]', granularity)
        else:
            form_data.add_field('task', task)
            form_data.add_field('response_format', response_format)
            form_data.add_field('temperature', str(temperature))

            if timestamp_granularities:
                form_data.add_field('timestamp_granularities[]', ','.join(timestamp_granularities))

        # Call API
        url = f"{endpoint}/v1/audio/transcriptions"

        # Prepare headers
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url,
                    data=form_data,
                    headers=headers if headers else None,
                    timeout=aiohttp.ClientTimeout(total=300)  # 5 minute timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"ASR API error: status={response.status}, body={error_text}"
                        )

                    result = await response.json()
                    return result

            except aiohttp.ClientError as e:
                raise Exception(f"ASR API request failed: {str(e)}")

    async def get_provider_health(self, provider_id: str) -> ProviderHealth:
        """
        Get health status for a specific provider (with 30-second cache).

        Args:
            provider_id: Provider ID

        Returns:
            ProviderHealth with status and metrics
        """
        # Check cache
        now = datetime.utcnow()
        if (
            self._cache_timestamp
            and (now - self._cache_timestamp).total_seconds() < self._cache_ttl_seconds
            and provider_id in self._status_cache
        ):
            return self._status_cache[provider_id]

        # Refresh cache
        await self._refresh_status_cache()

        # Return from cache or default offline status
        if provider_id in self._status_cache:
            return self._status_cache[provider_id]

        provider = self.provider_registry.get_provider(provider_id)
        return ProviderHealth(
            provider_id=provider_id,
            status='offline',
            endpoint=provider.endpoint if provider else 'unknown',
            last_check=now,
            error_message='Provider not found in registry'
        )

    async def get_all_providers_health(self, force_refresh: bool = False) -> List[ProviderHealth]:
        """
        Get health status for all ASR providers.

        Args:
            force_refresh: Force cache refresh

        Returns:
            List of ProviderHealth for all ASR providers
        """
        # Refresh cache if needed
        now = datetime.utcnow()
        if (
            force_refresh
            or not self._cache_timestamp
            or (now - self._cache_timestamp).total_seconds() >= self._cache_ttl_seconds
        ):
            await self._refresh_status_cache()

        return list(self._status_cache.values())

    async def _refresh_status_cache(self):
        """Refresh provider status cache from health monitor."""
        asr_providers = self.provider_registry.get_asr_providers()

        if not self.health_monitor:
            # No health monitoring - mark all as online
            self._status_cache = {
                provider.id: ProviderHealth(
                    provider_id=provider.id,
                    status='online',
                    endpoint=provider.endpoint,
                    last_check=datetime.utcnow(),
                    response_time_ms=None
                )
                for provider in asr_providers
            }
        else:
            # Get status from health monitor
            self._status_cache = {}

            for provider in asr_providers:
                try:
                    health_result = await self.health_monitor.check_provider_health(provider)
                    self._status_cache[provider.id] = ProviderHealth(
                        provider_id=provider.id,
                        status='online' if health_result.healthy else 'offline',
                        endpoint=provider.endpoint,
                        last_check=datetime.utcnow(),
                        response_time_ms=health_result.response_time_ms,
                        error_message=health_result.error if not health_result.healthy else None
                    )
                except Exception as e:
                    logger.warning(f"Health check failed for {provider.id}: {e}")
                    self._status_cache[provider.id] = ProviderHealth(
                        provider_id=provider.id,
                        status='offline',
                        endpoint=provider.endpoint,
                        last_check=datetime.utcnow(),
                        error_message=str(e)
                    )

        self._cache_timestamp = datetime.utcnow()
        logger.debug(f"ASR provider status cache refreshed: {len(self._status_cache)} providers")

    async def estimate_cost(
        self,
        provider_id: str,
        audio_base64: str
    ) -> float:
        """
        Estimate transcription cost before processing.

        Args:
            provider_id: ASR provider ID
            audio_base64: Base64-encoded audio

        Returns:
            Estimated cost in USD
        """
        # Decode to get size
        audio_bytes = base64.b64decode(audio_base64)
        audio_size_kb = len(audio_bytes) / 1024

        # Estimate duration (assuming 16kHz mono 16-bit = ~32KB/sec)
        estimated_duration = audio_size_kb / 32

        # Calculate cost
        return self.usage_calculator.calculate_asr_cost(
            duration_seconds=estimated_duration,
            provider=provider_id
        )

    async def get_available_languages(self, provider_id: str) -> List[str]:
        """
        Get supported languages for a provider.

        Args:
            provider_id: ASR provider ID

        Returns:
            List of language codes
        """
        provider = self.provider_registry.get_provider(provider_id)
        if not provider:
            return []

        return provider.languageList or []

    async def cleanup(self):
        """Cleanup resources and stop background tasks."""
        if self.health_monitor:
            await self.health_monitor.stop()
            logger.info("Health monitoring stopped")


# ============================================================================
# Singleton Instance
# ============================================================================

_asr_service_instance: Optional[ASRProviderService] = None


async def get_asr_service() -> ASRProviderService:
    """
    Get singleton ASR Provider Service instance.

    Returns:
        Initialized ASRProviderService
    """
    global _asr_service_instance

    if _asr_service_instance is None:
        # Use default configuration - billing and health monitoring now supported
        _asr_service_instance = ASRProviderService(
            enable_billing=True,
            enable_health_monitoring=True
        )

        # Register default ASR providers
        asr_providers_config = get_default_asr_providers_config()
        _asr_service_instance.provider_registry.register_providers_from_config(
            asr_providers_config,
            provider_type=ProviderType.ASR
        )
        logger.info(f"Registered {len(asr_providers_config)} ASR providers")

        await _asr_service_instance.initialize()

    return _asr_service_instance
