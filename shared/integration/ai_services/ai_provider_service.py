"""
AI Provider Service - Base Class

Generic base class for managing AI service providers (TTS, LLM, ASR, etc.)
Provides common functionality for provider management, health checks, and status tracking.

Usage:
    class TTSProviderService(AIProviderService):
        def __init__(self):
            super().__init__(provider_type=ProviderType.TTS)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import aiohttp

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Types of AI providers."""
    TTS = "tts"  # Text-to-Speech
    ASR = "asr"  # Automatic Speech Recognition
    LLM = "llm"  # Large Language Model
    VISION = "vision"  # Vision/Image models
    EMBEDDING = "embedding"  # Embedding models
    MULTIMODAL = "multimodal"  # Multimodal models (text + image + audio)


class ProviderStatus(str, Enum):
    """Provider status states."""
    ONLINE = "online"  # Provider is operational
    OFFLINE = "offline"  # Provider is not responding
    BUILDING = "building"  # Provider is deploying/building
    DEGRADED = "degraded"  # Provider is partially functional
    MAINTENANCE = "maintenance"  # Planned maintenance


class ProviderCapabilities(BaseModel):
    """
    Provider capabilities - flexible structure for any provider type.

    Common capabilities:
        - multiLanguage: Supports multiple languages
        - streaming: Supports streaming responses
        - realtime: Supports real-time processing

    TTS-specific:
        - voiceCloning: Supports voice cloning
        - speedControl: Supports speed adjustment
        - pitchControl: Supports pitch adjustment
        - multiSpeaker: Multiple speaker voices
        - emotionControl: Emotion/style control

    LLM-specific:
        - functionCalling: Supports function calling
        - reasoning: Advanced reasoning capabilities
        - codeGeneration: Code generation support
        - vision: Vision/image understanding

    ASR-specific:
        - diarization: Speaker diarization
        - timestamps: Word-level timestamps
        - punctuation: Automatic punctuation
    """
    # Generic capabilities
    multiLanguage: bool = False
    streaming: bool = False
    realtime: bool = False

    # TTS capabilities
    voiceCloning: bool = False
    speedControl: bool = False
    pitchControl: bool = False
    multiSpeaker: bool = False
    emotionControl: bool = False

    # LLM capabilities
    functionCalling: bool = False
    reasoning: bool = False
    codeGeneration: bool = False
    vision: bool = False
    culturalContext: bool = False

    # ASR capabilities
    diarization: bool = False
    timestamps: bool = False
    wordLevelTimestamps: bool = False
    punctuation: bool = False

    # Custom capabilities (provider-specific)
    custom: Dict[str, Any] = Field(default_factory=dict)


class AIProvider(BaseModel):
    """
    Generic AI Provider model.

    Args:
        id: Unique identifier for the provider
        name: Display name
        provider_type: Type of provider (tts, llm, asr, etc.)
        endpoint: Base URL for the provider API
        status: Current operational status
        capabilities: Provider capabilities
        description: Description of the provider
        icon: Icon/emoji for display
        languages: Number of supported languages
        languageList: List of supported language codes
        metadata: Additional provider-specific metadata
        lastChecked: Last health check timestamp
        responseTime: Average response time in milliseconds
        requires_api_key: Whether the provider requires an API key
        api_key_env: Environment variable name for the API key
        model_name: Model name for the provider (e.g., 'whisper-1')
    """
    id: str
    name: str
    provider_type: ProviderType
    endpoint: str
    status: ProviderStatus = ProviderStatus.OFFLINE
    capabilities: ProviderCapabilities
    description: str
    icon: str = "🤖"
    languages: int = 0
    languageList: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    lastChecked: Optional[datetime] = None
    responseTime: Optional[float] = None
    requires_api_key: bool = False
    api_key_env: Optional[str] = None
    model_name: Optional[str] = None

    class Config:
        use_enum_values = True


class AIProviderService:
    """
    Base service for managing AI providers.

    Provides common functionality:
    - Provider registration and discovery
    - Health checking
    - Status tracking
    - Auto-refresh

    Subclasses should implement provider-specific logic.
    """

    def __init__(
        self,
        provider_type: ProviderType,
        cache_ttl: int = 300,  # 5 minutes default cache
        health_check_interval: int = 60,  # 60 seconds default
    ):
        """
        Initialize AI Provider Service.

        Args:
            provider_type: Type of providers this service manages
            cache_ttl: Cache time-to-live in seconds
            health_check_interval: Health check interval in seconds
        """
        self.provider_type = provider_type
        self.cache_ttl = cache_ttl
        self.health_check_interval = health_check_interval
        self._providers: Dict[str, AIProvider] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._health_check_task: Optional[asyncio.Task] = None
        logger.info(f"Initialized {provider_type.value} provider service")

    def register_provider(self, provider: AIProvider) -> None:
        """
        Register a provider.

        Args:
            provider: Provider instance to register
        """
        if provider.provider_type != self.provider_type:
            raise ValueError(
                f"Provider type mismatch: expected {self.provider_type}, "
                f"got {provider.provider_type}"
            )

        self._providers[provider.id] = provider
        logger.info(f"Registered provider: {provider.id} ({provider.name})")

    def get_provider(self, provider_id: str) -> Optional[AIProvider]:
        """
        Get provider by ID.

        Args:
            provider_id: Provider identifier

        Returns:
            Provider instance or None if not found
        """
        return self._providers.get(provider_id)

    def list_providers(
        self,
        status: Optional[ProviderStatus] = None,
        capability: Optional[str] = None,
    ) -> List[AIProvider]:
        """
        List all providers with optional filtering.

        Args:
            status: Filter by status
            capability: Filter by capability (e.g., "voiceCloning", "streaming")

        Returns:
            List of providers matching filters
        """
        providers = list(self._providers.values())

        if status:
            providers = [p for p in providers if p.status == status]

        if capability:
            providers = [
                p for p in providers
                if getattr(p.capabilities, capability, False)
            ]

        return providers

    async def check_health(
        self,
        provider: AIProvider,
        timeout: int = 5,
    ) -> Dict[str, Any]:
        """
        Check health of a provider.

        Args:
            provider: Provider to check
            timeout: Timeout in seconds

        Returns:
            Health check result with status and response time
        """
        start_time = datetime.now()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{provider.endpoint}/health",
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as response:
                    elapsed = (datetime.now() - start_time).total_seconds() * 1000

                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": ProviderStatus.ONLINE,
                            "response_time": elapsed,
                            "healthy": data.get("status") == "healthy",
                            "details": data,
                        }
                    else:
                        return {
                            "status": ProviderStatus.DEGRADED,
                            "response_time": elapsed,
                            "healthy": False,
                            "error": f"HTTP {response.status}",
                        }

        except asyncio.TimeoutError:
            return {
                "status": ProviderStatus.OFFLINE,
                "response_time": None,
                "healthy": False,
                "error": "Timeout",
            }
        except Exception as e:
            logger.error(f"Health check failed for {provider.id}: {e}")
            return {
                "status": ProviderStatus.OFFLINE,
                "response_time": None,
                "healthy": False,
                "error": str(e),
            }

    async def check_all_providers(self) -> Dict[str, Dict[str, Any]]:
        """
        Check health of all providers concurrently.

        Returns:
            Dict mapping provider ID to health check result
        """
        tasks = [
            self.check_health(provider)
            for provider in self._providers.values()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        health_results = {}
        for provider_id, result in zip(self._providers.keys(), results):
            if isinstance(result, Exception):
                health_results[provider_id] = {
                    "status": ProviderStatus.OFFLINE,
                    "healthy": False,
                    "error": str(result),
                }
            else:
                health_results[provider_id] = result

                # Update provider status
                provider = self._providers[provider_id]
                provider.status = result["status"]
                provider.responseTime = result.get("response_time")
                provider.lastChecked = datetime.now()

        return health_results

    async def refresh_providers(self, force: bool = False) -> Dict[str, AIProvider]:
        """
        Refresh provider status.

        Args:
            force: Force refresh even if cache is valid

        Returns:
            Dict of all providers
        """
        now = datetime.now()

        # Check cache validity
        if not force and self._cache_timestamp:
            age = (now - self._cache_timestamp).total_seconds()
            if age < self.cache_ttl:
                logger.debug(f"Using cached providers (age: {age:.1f}s)")
                return self._providers

        # Refresh health status
        logger.info(f"Refreshing {self.provider_type.value} providers")
        await self.check_all_providers()
        self._cache_timestamp = now

        return self._providers

    async def start_auto_refresh(self) -> None:
        """Start automatic health checking in the background."""
        if self._health_check_task and not self._health_check_task.done():
            logger.warning("Auto-refresh already running")
            return

        async def _refresh_loop():
            while True:
                try:
                    await asyncio.sleep(self.health_check_interval)
                    await self.refresh_providers()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Auto-refresh error: {e}")

        self._health_check_task = asyncio.create_task(_refresh_loop())
        logger.info(f"Started auto-refresh (interval: {self.health_check_interval}s)")

    async def stop_auto_refresh(self) -> None:
        """Stop automatic health checking."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
            logger.info("Stopped auto-refresh")

    def get_providers_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        Get providers as dictionary (for API responses).

        Returns:
            Dict mapping provider ID to provider data
        """
        return {
            provider_id: provider.dict()
            for provider_id, provider in self._providers.items()
        }

    def get_online_providers(self) -> List[AIProvider]:
        """Get all online providers."""
        return self.list_providers(status=ProviderStatus.ONLINE)

    def get_by_capability(self, capability: str) -> List[AIProvider]:
        """Get providers with specific capability."""
        return self.list_providers(capability=capability)
