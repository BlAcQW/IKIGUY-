"""
TTS Client
Unified client interface for all TTS providers.
"""

from typing import Optional, Dict, Any, List, AsyncGenerator, Union
import asyncio
import logging
from datetime import datetime, timedelta

from .models import (
    TTSProvider,
    TTSRequest,
    TTSResponse,
    VoiceCloneRequest,
    ConversationRequest,
    ProviderStatus,
    BatchTTSRequest,
    BatchTTSResponse,
)
from .providers import (
    BaseTTSProvider,
    F5TTSProvider,
    StyleTTS2Provider,
    MoshiProvider,
    CoquiXTTSProvider,
    MeloTTSProvider,
    OpenVoiceProvider,
    KokoroTTSProvider,
    ChatterboxProvider,
    TTSWebUIProvider,
    FishSpeechProvider,
    ZonosTTSProvider,
    IndexTTSProvider,
    VoxCPMProvider,
    GPTSoVITSProvider,
    # TTS-WebUI model providers
    BarkProvider,
    TortoiseProvider,
    MahaTTSProvider,
    MMSProvider,
    ValleXProvider,
)
from .exceptions import (
    TTSException,
    ProviderNotAvailableError,
    InvalidRequestError,
)
from .config import get_provider_config, get_available_providers

logger = logging.getLogger(__name__)


class TTSClient:
    """Synchronous TTS client."""

    def __init__(self):
        """Initialize TTS client."""
        self.async_client = AsyncTTSClient()

    def synthesize(
        self,
        text: str,
        provider: Optional[TTSProvider] = None,
        **kwargs
    ) -> TTSResponse:
        """Synthesize speech from text.

        Args:
            text: Text to synthesize
            provider: TTS provider to use (auto-selects if not provided)
            **kwargs: Additional request parameters

        Returns:
            TTS response with audio
        """
        return asyncio.run(self.async_client.synthesize(text, provider, **kwargs))

    def synthesize_batch(
        self,
        texts: List[str],
        provider: Optional[TTSProvider] = None,
        **kwargs
    ) -> BatchTTSResponse:
        """Synthesize multiple texts.

        Args:
            texts: List of texts to synthesize
            provider: TTS provider to use
            **kwargs: Additional request parameters

        Returns:
            Batch TTS response
        """
        return asyncio.run(self.async_client.synthesize_batch(texts, provider, **kwargs))

    def clone_voice(
        self,
        text: str,
        reference_audio: bytes,
        provider: Optional[TTSProvider] = None,
        **kwargs
    ) -> TTSResponse:
        """Synthesize speech with voice cloning.

        Args:
            text: Text to synthesize
            reference_audio: Reference audio for cloning
            provider: TTS provider to use
            **kwargs: Additional request parameters

        Returns:
            TTS response with cloned audio
        """
        return asyncio.run(
            self.async_client.clone_voice(text, reference_audio, provider, **kwargs)
        )

    def get_provider_status(self, provider: TTSProvider) -> ProviderStatus:
        """Get provider status.

        Args:
            provider: TTS provider

        Returns:
            Provider status
        """
        return asyncio.run(self.async_client.get_provider_status(provider))

    def get_all_statuses(self) -> Dict[TTSProvider, ProviderStatus]:
        """Get status of all providers.

        Returns:
            Dictionary of provider statuses
        """
        return asyncio.run(self.async_client.get_all_statuses())


class AsyncTTSClient:
    """Asynchronous TTS client with provider management."""

    def __init__(self):
        """Initialize async TTS client."""
        self._providers: Dict[TTSProvider, BaseTTSProvider] = {}
        self._provider_status: Dict[TTSProvider, ProviderStatus] = {}
        self._status_cache_duration = timedelta(minutes=5)
        self._default_provider: Optional[TTSProvider] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_providers()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _initialize_providers(self):
        """Initialize all available providers."""
        provider_classes = {
            # Core TTS providers
            TTSProvider.F5TTS: F5TTSProvider,
            TTSProvider.STYLETTS2: StyleTTS2Provider,
            TTSProvider.MOSHI: MoshiProvider,
            TTSProvider.COQUI_XTTS: CoquiXTTSProvider,
            TTSProvider.MELOTTS: MeloTTSProvider,
            TTSProvider.OPENVOICE: OpenVoiceProvider,

            # Additional deployed providers (2025-11-23)
            TTSProvider.KOKORO: KokoroTTSProvider,
            TTSProvider.CHATTERBOX: ChatterboxProvider,  # 23 language support, voice cloning
            TTSProvider.TTS_WEBUI: TTSWebUIProvider,
            TTSProvider.FISH_SPEECH: FishSpeechProvider,
            TTSProvider.ZONOS: ZonosTTSProvider,
            TTSProvider.INDEXTTS: IndexTTSProvider,
            TTSProvider.VOXCPM: VoxCPMProvider,
            TTSProvider.GPT_SOVITS: GPTSoVITSProvider,

            # TTS-WebUI model providers (2025-11-24)
            TTSProvider.BARK: BarkProvider,
            TTSProvider.TORTOISE: TortoiseProvider,
            TTSProvider.MAHATTS: MahaTTSProvider,
            TTSProvider.MMS: MMSProvider,
            TTSProvider.VALLE_X: ValleXProvider,
        }

        for provider_id, provider_class in provider_classes.items():
            try:
                provider = provider_class()
                self._providers[provider_id] = provider
                logger.info(f"Initialized provider: {provider_id.value}")
            except Exception as e:
                logger.error(f"Failed to initialize provider {provider_id.value}: {e}")

    async def close(self):
        """Close all provider connections."""
        tasks = []
        for provider in self._providers.values():
            tasks.append(provider.disconnect())
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _get_provider(self, provider_id: Optional[TTSProvider] = None) -> BaseTTSProvider:
        """Get a TTS provider instance.

        Args:
            provider_id: Provider ID (auto-selects if not provided)

        Returns:
            Provider instance

        Raises:
            ProviderNotAvailableError: If provider is not available
        """
        # Auto-select provider if not specified
        if provider_id is None:
            provider_id = await self._select_best_provider()

        if provider_id not in self._providers:
            raise ProviderNotAvailableError(
                provider_id.value if provider_id else "unknown",
                "Provider not initialized"
            )

        provider = self._providers[provider_id]

        # Check if provider is available
        if not provider._is_available:
            try:
                await provider.connect()
            except Exception as e:
                raise ProviderNotAvailableError(provider_id.value, str(e))

        return provider

    async def _select_best_provider(self) -> TTSProvider:
        """Auto-select the best available provider.

        Returns:
            Best available provider ID

        Raises:
            ProviderNotAvailableError: If no providers are available
        """
        # Check provider statuses
        statuses = await self.get_all_statuses()

        # Priority order (prefer online providers)
        priority_order = [
            TTSProvider.F5TTS,
            TTSProvider.STYLETTS2,
            TTSProvider.MOSHI,
            TTSProvider.COQUI_XTTS,
            TTSProvider.MELOTTS,
            TTSProvider.OPENVOICE,
        ]

        for provider_id in priority_order:
            if provider_id in statuses:
                status = statuses[provider_id]
                if status.status == "online" and status.model_loaded:
                    return provider_id

        raise ProviderNotAvailableError("auto", "No providers available")

    async def synthesize(
        self,
        text: str,
        provider: Optional[TTSProvider] = None,
        language: str = "en",
        speaker: Optional[str] = None,
        speed: float = 1.0,
        **kwargs
    ) -> TTSResponse:
        """Synthesize speech from text.

        Args:
            text: Text to synthesize
            provider: TTS provider to use (auto-selects if not provided)
            language: Language code
            speaker: Speaker ID/name
            speed: Speech speed (0.5-2.0)
            **kwargs: Additional parameters

        Returns:
            TTS response with audio

        Raises:
            InvalidRequestError: If request is invalid
            ProviderNotAvailableError: If provider is not available
            AudioProcessingError: If synthesis fails
        """
        # Validate request
        if not text or len(text.strip()) == 0:
            raise InvalidRequestError("Text cannot be empty")

        # Create request
        request = TTSRequest(
            text=text,
            provider=provider,
            language=language,
            speaker=speaker,
            speed=speed,
            **kwargs
        )

        # Get provider
        provider_instance = await self._get_provider(provider)

        # Synthesize
        start_time = datetime.utcnow()
        response = await provider_instance.synthesize(request)
        response.processing_time = (datetime.utcnow() - start_time).total_seconds()

        logger.info(
            f"Synthesized {len(text)} characters using {provider_instance.config.id.value} "
            f"in {response.processing_time:.2f}s"
        )

        return response

    async def synthesize_batch(
        self,
        texts: List[str],
        provider: Optional[TTSProvider] = None,
        parallel: bool = True,
        max_workers: int = 4,
        **kwargs
    ) -> BatchTTSResponse:
        """Synthesize multiple texts.

        Args:
            texts: List of texts to synthesize
            provider: TTS provider to use
            parallel: Process in parallel
            max_workers: Maximum parallel workers
            **kwargs: Additional parameters

        Returns:
            Batch TTS response
        """
        start_time = datetime.utcnow()
        results = []
        successful = 0
        failed = 0

        if parallel:
            # Process in parallel with semaphore
            semaphore = asyncio.Semaphore(max_workers)

            async def process_item(text: str) -> TTSResponse:
                async with semaphore:
                    try:
                        return await self.synthesize(text, provider, **kwargs)
                    except Exception as e:
                        logger.error(f"Failed to synthesize: {e}")
                        raise

            tasks = [process_item(text) for text in texts]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            for response in responses:
                if isinstance(response, Exception):
                    failed += 1
                    results.append(None)
                else:
                    successful += 1
                    results.append(response)
        else:
            # Process sequentially
            for text in texts:
                try:
                    response = await self.synthesize(text, provider, **kwargs)
                    results.append(response)
                    successful += 1
                except Exception as e:
                    logger.error(f"Failed to synthesize: {e}")
                    results.append(None)
                    failed += 1

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        return BatchTTSResponse(
            results=[r for r in results if r is not None],
            total_items=len(texts),
            successful=successful,
            failed=failed,
            processing_time=processing_time
        )

    async def clone_voice(
        self,
        text: str,
        reference_audio: bytes,
        provider: Optional[TTSProvider] = None,
        **kwargs
    ) -> TTSResponse:
        """Synthesize speech with voice cloning.

        Args:
            text: Text to synthesize
            reference_audio: Reference audio for cloning
            provider: TTS provider to use
            **kwargs: Additional parameters

        Returns:
            TTS response with cloned audio

        Raises:
            NotImplementedError: If provider doesn't support voice cloning
        """
        # Auto-select provider with voice cloning capability if not specified
        if provider is None:
            provider = await self._select_voice_cloning_provider()

        # Create request
        request = VoiceCloneRequest(
            text=text,
            reference_audio=reference_audio,
            provider=provider,
            **kwargs
        )

        # Get provider
        provider_instance = await self._get_provider(provider)

        # Check capability
        if not provider_instance.config.capabilities.voice_cloning:
            raise NotImplementedError(
                f"Provider {provider_instance.config.name} does not support voice cloning"
            )

        # Synthesize with cloning
        start_time = datetime.utcnow()
        response = await provider_instance.synthesize_with_clone(request)
        response.processing_time = (datetime.utcnow() - start_time).total_seconds()

        return response

    async def _select_voice_cloning_provider(self) -> TTSProvider:
        """Select a provider with voice cloning capability.

        Returns:
            Provider ID with voice cloning support

        Raises:
            ProviderNotAvailableError: If no voice cloning providers available
        """
        voice_cloning_providers = [
            TTSProvider.F5TTS,
            TTSProvider.STYLETTS2,
            TTSProvider.COQUI_XTTS,
            TTSProvider.OPENVOICE,
        ]

        statuses = await self.get_all_statuses()

        for provider_id in voice_cloning_providers:
            if provider_id in statuses:
                status = statuses[provider_id]
                if status.status == "online" and status.model_loaded:
                    return provider_id

        raise ProviderNotAvailableError("auto", "No voice cloning providers available")

    async def start_conversation(
        self,
        request: ConversationRequest,
        provider: TTSProvider = TTSProvider.MOSHI
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Start real-time conversation (Moshi only).

        Args:
            request: Conversation request
            provider: Provider (must be Moshi)

        Yields:
            WebSocket messages

        Raises:
            NotImplementedError: If provider doesn't support conversations
        """
        if provider != TTSProvider.MOSHI:
            raise NotImplementedError(
                f"Provider {provider.value} does not support real-time conversation"
            )

        provider_instance = await self._get_provider(provider)

        if not hasattr(provider_instance, 'start_conversation'):
            raise NotImplementedError(
                f"Provider {provider.value} does not implement conversation support"
            )

        async for message in provider_instance.start_conversation(request):
            yield message

    async def get_provider_status(self, provider: TTSProvider) -> ProviderStatus:
        """Get provider status.

        Args:
            provider: TTS provider

        Returns:
            Provider status
        """
        # Check cache
        if provider in self._provider_status:
            cached_status = self._provider_status[provider]
            if (datetime.utcnow() - cached_status.last_check) < self._status_cache_duration:
                return cached_status

        # Get fresh status
        try:
            provider_instance = await self._get_provider(provider)
            status = await provider_instance.check_health()
            self._provider_status[provider] = status
            return status
        except Exception as e:
            logger.error(f"Failed to get status for {provider.value}: {e}")
            # Return offline status
            config = get_provider_config(provider)
            return ProviderStatus(
                provider=provider,
                name=config.name,
                endpoint=config.endpoint.base_url,
                status="offline",
                capabilities=config.capabilities,
                description=config.description,
                error=str(e),
                last_check=datetime.utcnow()
            )

    async def get_all_statuses(self) -> Dict[TTSProvider, ProviderStatus]:
        """Get status of all providers.

        Returns:
            Dictionary of provider statuses
        """
        tasks = {}
        for provider_id in TTSProvider:
            if provider_id == TTSProvider.CRAWL4AI:
                continue  # Skip non-TTS provider
            tasks[provider_id] = self.get_provider_status(provider_id)

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        statuses = {}
        for provider_id, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Failed to get status for {provider_id.value}: {result}")
                # Create offline status
                config = get_provider_config(provider_id)
                statuses[provider_id] = ProviderStatus(
                    provider=provider_id,
                    name=config.name,
                    endpoint=config.endpoint.base_url,
                    status="offline",
                    capabilities=config.capabilities,
                    description=config.description,
                    error=str(result),
                    last_check=datetime.utcnow()
                )
            else:
                statuses[provider_id] = result

        return statuses