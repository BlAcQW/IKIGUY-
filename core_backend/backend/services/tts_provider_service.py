"""
TTS Provider Service

Manages TTS provider status, health checks, and configuration.
Provides dynamic status updates for TTS Lab interface.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TTSCapabilities(BaseModel):
    """TTS provider capabilities."""
    voiceCloning: bool = False
    multiLanguage: bool = False
    speedControl: bool = False
    pitchControl: bool = False
    multiSpeaker: bool = False
    emotionControl: bool = False
    realTimeConversation: bool = False


class TTSProvider(BaseModel):
    """TTS provider configuration."""
    id: str
    name: str
    endpoint: str
    status: str = "offline"  # online, offline, building
    languages: int = 0
    languageList: List[str] = []
    capabilities: TTSCapabilities
    description: str
    icon: str = "🎙️"
    lastChecked: Optional[str] = None
    responseTime: Optional[float] = None


# TTS Provider Configuration
TTS_PROVIDERS_CONFIG = {
    "coqui_xtts": TTSProvider(
        id="coqui_xtts",
        name="Coqui XTTS v2",
        endpoint="https://coqui.ailabsafrica.com",
        languages=17,
        languageList=["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "hu", "ko", "ja", "hi"],
        capabilities=TTSCapabilities(
            voiceCloning=True,
            multiLanguage=True,
            speedControl=True,
            pitchControl=True,  # Enable pitch control
        ),
        description="Multilingual TTS with voice cloning capabilities. Supports 17 languages with high-quality synthesis.",
        icon="🎙️",
    ),
    "melotts": TTSProvider(
        id="melotts",
        name="MeloTTS",
        endpoint="https://melotts.ailabsafrica.com",
        languages=6,
        languageList=["EN", "ES", "FR", "ZH", "JP", "KR"],
        capabilities=TTSCapabilities(
            voiceCloning=False,
            multiLanguage=True,
            speedControl=True,
            pitchControl=True,
            multiSpeaker=True,
        ),
        description="Fast multilingual synthesis with multi-speaker support. Optimized for speed and quality.",
        icon="🔊",
    ),
    "openvoice": TTSProvider(
        id="openvoice",
        name="OpenVoice",
        endpoint="https://openvoice.ailabsafrica.com",
        languages=2,
        languageList=["EN", "ZH"],
        capabilities=TTSCapabilities(
            voiceCloning=True,
            multiLanguage=True,
            speedControl=True,  # Enable speed control
            pitchControl=True,
            emotionControl=True,
        ),
        description="Advanced voice cloning with emotion control for English and Chinese.",
        icon="🎭",
    ),
    "kokoro": TTSProvider(
        id="kokoro",
        name="Kokoro TTS",
        endpoint="https://kokoro.ailabsafrica.com",
        languages=0,
        capabilities=TTSCapabilities(
            voiceCloning=False,
            multiLanguage=False,
            speedControl=True,
            pitchControl=True,  # Enable pitch control
        ),
        description="High-quality TTS synthesis.",
        icon="💬",
    ),
    "f5tts": TTSProvider(
        id="f5tts",
        name="F5-TTS",
        endpoint="https://f5tts.ailabsafrica.com",
        languages=4,
        languageList=["en", "zh", "ja", "ko"],
        capabilities=TTSCapabilities(
            voiceCloning=True,
            multiLanguage=True,
            speedControl=True,
            pitchControl=True,  # Enable pitch control
            emotionControl=False,
            multiSpeaker=False,
        ),
        description="Flow-matching based TTS with voice cloning. Requires reference audio for synthesis.",
        icon="🌊",
    ),
    "styletts2": TTSProvider(
        id="styletts2",
        name="StyleTTS2",
        endpoint="https://styletts.ailabsafrica.com",
        languages=1,
        languageList=["en"],
        capabilities=TTSCapabilities(
            voiceCloning=True,
            multiLanguage=False,
            speedControl=True,  # Enable speed control
            pitchControl=True,  # Enable pitch control
            emotionControl=True,
            multiSpeaker=False,
        ),
        description="High-quality expressive TTS with style transfer. Requires reference audio for synthesis.",
        icon="🎨",
    ),
    "moshi": TTSProvider(
        id="moshi",
        name="Kyutai Moshi",
        endpoint="http://localhost:8011",
        languages=1,
        languageList=["en"],
        capabilities=TTSCapabilities(
            voiceCloning=False,
            multiLanguage=False,
            speedControl=False,
            pitchControl=False,
            emotionControl=False,
            multiSpeaker=False,
            realTimeConversation=True,
        ),
        description="Real-time conversational AI with full-duplex spoken dialogue. Ultra-low latency bidirectional conversation.",
        icon="⚡",
    ),
    "akan_mms": TTSProvider(
        id="akan_mms",
        name="AKAN MMS (Twi)",
        endpoint="https://flow-api.ailabsafrica.com/api/voice-lab",
        languages=1,
        languageList=["tw"],
        capabilities=TTSCapabilities(
            voiceCloning=False,
            multiLanguage=False,
            speedControl=True,
            pitchControl=True,
            multiSpeaker=True,
        ),
        description="Fine-tuned Twi TTS with native speakers. Supports Asante, Akuapem, and Fante dialects with 6 voices (3 male, 3 female).",
        icon="🇬🇭",
    ),
    "crawl4ai": TTSProvider(
        id="crawl4ai",
        name="Crawl4AI",
        endpoint="https://crawl4ai.ailabsafrica.com",
        languages=0,
        capabilities=TTSCapabilities(
            voiceCloning=False,
            multiLanguage=False,
            speedControl=False,
            pitchControl=False,
        ),
        description="Web scraping and content extraction service. Utility service for TTS content preparation.",
        icon="🕷️",
    ),
    "indextts": TTSProvider(
        id="indextts",
        name="IndexTTS 2.0",
        endpoint="https://jzfmzviw26huka-8016.proxy.runpod.net",
        languages=2,
        languageList=["en", "zh"],
        capabilities=TTSCapabilities(
            voiceCloning=True,
            multiLanguage=True,
            speedControl=True,
            pitchControl=False,
            emotionControl=True,
            multiSpeaker=True,
        ),
        description="Advanced TTS with voice cloning and emotion control. Features text normalization, speech editing, and high-quality synthesis.",
        icon="📑",
    ),
    "voxcpm": TTSProvider(
        id="voxcpm",
        name="VoxCPM",
        endpoint="https://jzfmzviw26huka-8016.proxy.runpod.net",
        languages=2,
        languageList=["en", "zh"],
        capabilities=TTSCapabilities(
            voiceCloning=True,
            multiLanguage=True,
            speedControl=True,
            pitchControl=False,
            emotionControl=False,
            multiSpeaker=False,
        ),
        description="Context-aware TTS model with voice cloning. Part of the CPM (Chinese Pre-trained Model) family for natural speech synthesis.",
        icon="🎯",
    ),
}


class TTSProviderService:
    """Service for managing TTS provider health checks and status."""

    def __init__(self):
        """Initialize TTS Provider Service."""
        self.providers = TTS_PROVIDERS_CONFIG.copy()
        self.health_check_timeout = 5  # seconds
        self.cache_duration = timedelta(seconds=30)  # Cache health status for 30s
        self.last_health_check = {}

    async def check_provider_health(self, provider: TTSProvider) -> tuple[str, Optional[float]]:
        """
        Check health status of a TTS provider.

        Args:
            provider: TTS provider configuration

        Returns:
            tuple: (status, response_time) - status is 'online', 'offline', or 'building'
                   response_time is in milliseconds or None
        """
        try:
            start_time = datetime.now()

            # Reason: Use aiohttp for async HTTP requests with timeout
            timeout = aiohttp.ClientTimeout(total=self.health_check_timeout)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Try /health endpoint first (standard)
                health_url = f"{provider.endpoint}/health"

                try:
                    async with session.get(health_url) as response:
                        elapsed = (datetime.now() - start_time).total_seconds() * 1000

                        if response.status == 200:
                            # Check if response contains status info
                            try:
                                data = await response.json()
                                if isinstance(data, dict) and data.get("status") == "healthy":
                                    return "online", elapsed
                            except:
                                pass
                            # If we got 200 but no JSON or no status field, still consider it online
                            return "online", elapsed
                        else:
                            logger.warning(f"Provider {provider.id} returned status {response.status}")
                            return "offline", None

                except aiohttp.ClientError as e:
                    logger.debug(f"Health check failed for {provider.id}: {e}")

                    # Try root endpoint as fallback
                    try:
                        async with session.get(provider.endpoint) as response:
                            elapsed = (datetime.now() - start_time).total_seconds() * 1000
                            if response.status in [200, 404]:  # 404 is OK, means server is up
                                return "online", elapsed
                    except:
                        pass

                    return "offline", None

        except asyncio.TimeoutError:
            logger.debug(f"Timeout checking {provider.id}")
            return "offline", None
        except Exception as e:
            logger.error(f"Error checking health for {provider.id}: {e}")
            return "offline", None

    async def get_all_providers_status(self, force_refresh: bool = False) -> Dict[str, TTSProvider]:
        """
        Get status of all TTS providers with health checks.

        Args:
            force_refresh: Force health check even if cached

        Returns:
            dict: Provider ID -> TTSProvider with updated status
        """
        now = datetime.now()

        # Check if we need to refresh health status
        if not force_refresh and self.last_health_check.get("timestamp"):
            last_check = self.last_health_check["timestamp"]
            if now - last_check < self.cache_duration:
                # Return cached status
                logger.debug("Returning cached provider status")
                return self.providers

        # Perform health checks for all providers concurrently
        logger.info("Performing health checks for all TTS providers")

        tasks = []
        provider_list = list(self.providers.values())

        for provider in provider_list:
            tasks.append(self.check_provider_health(provider))

        # Reason: Run all health checks concurrently for better performance
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update provider status
        for provider, result in zip(provider_list, results):
            if isinstance(result, Exception):
                logger.error(f"Exception checking {provider.id}: {result}")
                provider.status = "offline"
                provider.responseTime = None
            else:
                status, response_time = result
                provider.status = status
                provider.responseTime = response_time

            provider.lastChecked = now.isoformat()
            self.providers[provider.id] = provider

        # Update cache timestamp
        self.last_health_check["timestamp"] = now

        return self.providers

    async def get_provider_by_id(self, provider_id: str) -> Optional[TTSProvider]:
        """
        Get a specific provider by ID with current status.

        Args:
            provider_id: Provider identifier

        Returns:
            TTSProvider or None if not found
        """
        await self.get_all_providers_status()
        return self.providers.get(provider_id)

    def get_providers_by_status(self, status: str) -> List[TTSProvider]:
        """
        Get providers filtered by status.

        Args:
            status: online, offline, or building

        Returns:
            list: List of providers with matching status
        """
        return [p for p in self.providers.values() if p.status == status]

    def get_providers_by_capability(self, capability: str) -> List[TTSProvider]:
        """
        Get providers filtered by capability.

        Args:
            capability: Capability name (e.g., 'voiceCloning')

        Returns:
            list: List of providers with the capability
        """
        result = []
        for provider in self.providers.values():
            if hasattr(provider.capabilities, capability):
                if getattr(provider.capabilities, capability) is True:
                    result.append(provider)
        return result


# Global service instance
tts_provider_service = TTSProviderService()
