"""
Provider Registry

Centralized registry for all AI service providers across the platform.
Provides configuration management, provider discovery, and environment-based setup.

Usage:
    from apps.shared.integration.ai_services import ProviderRegistry

    registry = ProviderRegistry()
    registry.register_providers_from_config(config_dict)

    # Get all TTS providers
    tts_providers = registry.get_providers_by_type(ProviderType.TTS)

    # Get specific provider
    coqui = registry.get_provider("coqui_xtts")
"""

import os
import logging
from typing import Dict, List, Optional, Any
from .ai_provider_service import (
    AIProvider,
    ProviderType,
    ProviderStatus,
    ProviderCapabilities,
)

logger = logging.getLogger(__name__)


class AIProviderRegistry:
    """
    Centralized registry for AI service providers.

    Manages provider configurations and provides lookup functionality.
    Supports loading from configuration files, environment variables, or code.
    """

    def __init__(self):
        """Initialize empty provider registry."""
        self._providers: Dict[str, AIProvider] = {}
        logger.info("Initialized AI provider registry")

    def register_provider(
        self,
        provider: AIProvider,
        override: bool = False,
    ) -> None:
        """
        Register a single provider.

        Args:
            provider: Provider instance to register
            override: Allow overriding existing provider

        Raises:
            ValueError: If provider already exists and override=False
        """
        if provider.id in self._providers and not override:
            raise ValueError(
                f"Provider {provider.id} already registered. "
                f"Use override=True to replace."
            )

        self._providers[provider.id] = provider
        # Handle both enum and string values (Pydantic use_enum_values=True converts to string)
        provider_type_str = (
            provider.provider_type.value
            if hasattr(provider.provider_type, "value")
            else provider.provider_type
        )
        logger.info(
            f"Registered provider: {provider.id} ({provider.name}) "
            f"[{provider_type_str}]"
        )

    def register_providers_from_config(
        self,
        config: Dict[str, Dict[str, Any]],
        provider_type: Optional[ProviderType] = None,
    ) -> None:
        """
        Register multiple providers from configuration dict.

        Args:
            config: Dict mapping provider IDs to provider configs
            provider_type: Optional provider type to validate against

        Example config:
            {
                "coqui_xtts": {
                    "name": "Coqui XTTS v2",
                    "endpoint": "https://coqui.ailabsafrica.com",
                    "provider_type": "tts",
                    "capabilities": {"voiceCloning": true},
                    ...
                }
            }
        """
        for provider_id, provider_config in config.items():
            try:
                # Ensure provider_type is set
                if provider_type and "provider_type" not in provider_config:
                    provider_config["provider_type"] = provider_type.value

                # Add ID if not present
                if "id" not in provider_config:
                    provider_config["id"] = provider_id

                # Convert capabilities dict to ProviderCapabilities if needed
                if "capabilities" in provider_config and isinstance(
                    provider_config["capabilities"], dict
                ):
                    provider_config["capabilities"] = ProviderCapabilities(
                        **provider_config["capabilities"]
                    )

                provider = AIProvider(**provider_config)
                self.register_provider(provider, override=True)

            except Exception as e:
                logger.error(f"Failed to register provider {provider_id}: {e}")
                continue

    def get_provider(self, provider_id: str) -> Optional[AIProvider]:
        """
        Get provider by ID.

        Args:
            provider_id: Provider identifier

        Returns:
            Provider instance or None if not found
        """
        return self._providers.get(provider_id)

    def get_providers_by_type(
        self,
        provider_type: ProviderType,
    ) -> List[AIProvider]:
        """
        Get all providers of a specific type.

        Args:
            provider_type: Type of providers to retrieve

        Returns:
            List of providers matching the type
        """
        return [
            provider
            for provider in self._providers.values()
            if provider.provider_type == provider_type
        ]

    def get_tts_providers(self) -> List[AIProvider]:
        """
        Get all TTS providers.

        Returns:
            List of TTS providers
        """
        return self.get_providers_by_type(ProviderType.TTS)

    def get_llm_providers(self) -> List[AIProvider]:
        """
        Get all LLM providers.

        Returns:
            List of LLM providers
        """
        return self.get_providers_by_type(ProviderType.LLM)

    def get_asr_providers(self) -> List[AIProvider]:
        """
        Get all ASR providers.

        Returns:
            List of ASR providers
        """
        return self.get_providers_by_type(ProviderType.ASR)

    def get_providers_by_status(
        self,
        status: ProviderStatus,
    ) -> List[AIProvider]:
        """
        Get all providers with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of providers matching the status
        """
        return [
            provider
            for provider in self._providers.values()
            if provider.status == status
        ]

    def get_providers_by_capability(
        self,
        capability: str,
        provider_type: Optional[ProviderType] = None,
    ) -> List[AIProvider]:
        """
        Get providers supporting a specific capability.

        Args:
            capability: Capability name (e.g., "voiceCloning", "streaming")
            provider_type: Optional provider type filter

        Returns:
            List of providers with the capability
        """
        providers = self._providers.values()

        if provider_type:
            providers = [p for p in providers if p.provider_type == provider_type]

        return [
            provider
            for provider in providers
            if getattr(provider.capabilities, capability, False)
        ]

    def get_all_providers(self) -> Dict[str, AIProvider]:
        """Get all registered providers."""
        return self._providers.copy()

    def list_provider_ids(
        self,
        provider_type: Optional[ProviderType] = None,
    ) -> List[str]:
        """
        List all provider IDs.

        Args:
            provider_type: Optional type filter

        Returns:
            List of provider IDs
        """
        if provider_type:
            return [
                p.id
                for p in self._providers.values()
                if p.provider_type == provider_type
            ]
        return list(self._providers.keys())

    def update_provider_status(
        self,
        provider_id: str,
        status: ProviderStatus,
    ) -> bool:
        """
        Update provider status.

        Args:
            provider_id: Provider identifier
            status: New status

        Returns:
            True if updated, False if provider not found
        """
        provider = self.get_provider(provider_id)
        if provider:
            provider.status = status
            logger.info(f"Updated {provider_id} status to {status.value}")
            return True
        return False

    def remove_provider(self, provider_id: str) -> bool:
        """
        Remove a provider from registry.

        Args:
            provider_id: Provider identifier

        Returns:
            True if removed, False if not found
        """
        if provider_id in self._providers:
            del self._providers[provider_id]
            logger.info(f"Removed provider: {provider_id}")
            return True
        return False

    def clear(self) -> None:
        """Clear all providers from registry."""
        self._providers.clear()
        logger.info("Cleared provider registry")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dict with counts by type and status
        """
        stats = {
            "total": len(self._providers),
            "by_type": {},
            "by_status": {},
        }

        for provider in self._providers.values():
            # Count by type
            type_name = (
                provider.provider_type.value
                if hasattr(provider.provider_type, "value")
                else provider.provider_type
            )
            stats["by_type"][type_name] = stats["by_type"].get(type_name, 0) + 1

            # Count by status
            status_name = (
                provider.status.value
                if hasattr(provider.status, "value")
                else provider.status
            )
            stats["by_status"][status_name] = (
                stats["by_status"].get(status_name, 0) + 1
            )

        return stats


# Singleton instance for global registry
_global_registry: Optional[AIProviderRegistry] = None


def get_global_registry() -> AIProviderRegistry:
    """
    Get or create the global provider registry singleton.

    Returns:
        Global AIProviderRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = AIProviderRegistry()
    return _global_registry


def reset_global_registry() -> None:
    """Reset the global registry (useful for testing)."""
    global _global_registry
    _global_registry = None


# Backward compatibility alias
ProviderRegistry = AIProviderRegistry


# Pre-configured provider definitions
# These can be loaded from environment or config files

def get_default_tts_providers_config() -> Dict[str, Dict[str, Any]]:
    """
    Get default TTS provider configurations.

    Includes all self-hosted TTS providers plus utility services.

    Returns:
        Dict of TTS provider configs
    """
    return {
        "coqui_xtts": {
            "name": "Coqui XTTS v2",
            "endpoint": os.getenv("COQUI_ENDPOINT", "https://coqui.ailabsafrica.com"),
            "provider_type": "tts",
            "languages": 17,
            "languageList": ["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "hu", "ko", "ja", "hi"],
            "capabilities": {
                "voiceCloning": True,
                "multiLanguage": True,
                "speedControl": True,
                "pitchControl": True,  # Enable pitch control
            },
            "description": "Multilingual TTS with voice cloning capabilities. Supports 17 languages with high-quality synthesis.",
            "icon": "🎙️",
        },
        "melotts": {
            "name": "MeloTTS",
            "endpoint": os.getenv("MELOTTS_ENDPOINT", "https://melotts.ailabsafrica.com"),
            "provider_type": "tts",
            "languages": 6,
            "languageList": ["EN", "ES", "FR", "ZH", "JP", "KR"],
            "capabilities": {
                "voiceCloning": False,
                "multiLanguage": True,
                "speedControl": True,
                "pitchControl": True,
                "multiSpeaker": True,
            },
            "description": "Fast multilingual synthesis with multi-speaker support. Optimized for speed and quality.",
            "icon": "🔊",
        },
        "openvoice": {
            "name": "OpenVoice",
            "endpoint": os.getenv("OPENVOICE_ENDPOINT", "https://openvoice.ailabsafrica.com"),
            "provider_type": "tts",
            "languages": 2,
            "languageList": ["EN", "ZH"],
            "capabilities": {
                "voiceCloning": True,
                "multiLanguage": True,
                "speedControl": True,  # Enable speed control
                "pitchControl": True,
                "emotionControl": True,
            },
            "description": "Advanced voice cloning with emotion control for English and Chinese.",
            "icon": "🎭",
        },
        "kokoro": {
            "name": "Kokoro TTS",
            "endpoint": os.getenv("KOKORO_ENDPOINT", "https://kokoro.ailabsafrica.com"),
            "provider_type": "tts",
            "languages": 1,
            "languageList": ["en"],
            "capabilities": {
                "voiceCloning": False,
                "multiLanguage": False,
                "speedControl": True,
                "pitchControl": True,  # Enable pitch control
            },
            "description": "High-quality English TTS synthesis.",
            "icon": "💬",
        },
        "chatterbox": {
            "name": "Chatterbox",
            "endpoint": os.getenv("CHATTERBOX_ENDPOINT", "http://localhost:8004"),
            "provider_type": "tts",
            "languages": 1,
            "languageList": ["en"],
            "capabilities": {
                "voiceCloning": True,
                "multiLanguage": False,
                "speedControl": True,
                "pitchControl": False,
                "emotionControl": False,
                "multiSpeaker": False,
            },
            "description": "Expressive text-to-speech with voice cloning from reference audio. Running locally on Docker (Port 8004).",
            "icon": "🎤",
        },
        "f5tts": {
            "name": "F5-TTS",
            "endpoint": os.getenv("F5TTS_ENDPOINT", "https://kyutai.ailabsafrica.com"),
            "provider_type": "tts",
            "languages": 4,
            "languageList": ["en", "zh", "ja", "ko"],
            "capabilities": {
                "voiceCloning": True,
                "multiLanguage": True,
                "speedControl": True,
                "pitchControl": True,  # Enable pitch control
                "emotionControl": False,
                "multiSpeaker": False,
            },
            "description": "Flow-matching based TTS with voice cloning. Requires reference audio for synthesis.",
            "icon": "🌊",
        },
        "styletts2": {
            "name": "StyleTTS2",
            "endpoint": os.getenv("STYLETTS_ENDPOINT", "https://styletts.ailabsafrica.com"),
            "provider_type": "tts",
            "languages": 1,
            "languageList": ["en"],
            "capabilities": {
                "voiceCloning": True,
                "multiLanguage": False,
                "speedControl": True,  # Enable speed control
                "pitchControl": True,  # Enable pitch control
                "emotionControl": True,
                "multiSpeaker": False,
            },
            "description": "High-quality expressive TTS with style transfer. Requires reference audio for synthesis.",
            "icon": "🎨",
        },
        "moshi": {
            "name": "Kyutai Moshi",
            "endpoint": os.getenv("MOSHI_ENDPOINT", "http://localhost:8011"),
            "provider_type": "tts",
            "languages": 1,
            "languageList": ["en"],
            "capabilities": {
                "voiceCloning": False,
                "multiLanguage": False,
                "speedControl": False,
                "pitchControl": False,
                "emotionControl": False,
                "multiSpeaker": False,
                "realtime": True,
            },
            "description": "Real-time conversational AI with full-duplex spoken dialogue. Ultra-low latency bidirectional conversation.",
            "icon": "⚡",
        },
        "akan_mms": {
            "name": "AKAN MMS (Twi)",
            "endpoint": os.getenv("AKAN_MMS_ENDPOINT", "https://flow-api.ailabsafrica.com/api/voice-lab"),
            "provider_type": "tts",
            "languages": 1,
            "languageList": ["tw"],
            "capabilities": {
                "voiceCloning": False,
                "multiLanguage": False,
                "speedControl": True,
                "pitchControl": True,
                "multiSpeaker": True,
            },
            "description": "Fine-tuned Twi TTS with native speakers. Supports Asante, Akuapem, and Fante dialects with 6 voices (3 male, 3 female).",
            "icon": "🇬🇭",
        },
        "crawl4ai": {
            "name": "Crawl4AI",
            "endpoint": os.getenv("CRAWL4AI_ENDPOINT", "https://crawl4ai.ailabsafrica.com"),
            "provider_type": "tts",
            "languages": 0,
            "languageList": [],
            "capabilities": {
                "voiceCloning": False,
                "multiLanguage": False,
                "speedControl": False,
                "pitchControl": False,
            },
            "description": "Web scraping and content extraction service. Utility service for TTS content preparation.",
            "icon": "🕷️",
        },
        "indextts": {
            "name": "IndexTTS 2.0",
            "endpoint": os.getenv("INDEXTTS_ENDPOINT", "https://jzfmzviw26huka-8016.proxy.runpod.net"),
            "provider_type": "tts",
            "languages": 2,
            "languageList": ["en", "zh"],
            "capabilities": {
                "voiceCloning": True,
                "multiLanguage": True,
                "speedControl": True,
                "pitchControl": False,
                "emotionControl": True,
                "multiSpeaker": True,
            },
            "description": "Advanced TTS with voice cloning and emotion control. Features text normalization, speech editing, and high-quality synthesis.",
            "icon": "📑",
        },
        "voxcpm": {
            "name": "VoxCPM",
            "endpoint": os.getenv("VOXCPM_ENDPOINT", "https://jzfmzviw26huka-8016.proxy.runpod.net"),
            "provider_type": "tts",
            "languages": 2,
            "languageList": ["en", "zh"],
            "capabilities": {
                "voiceCloning": True,
                "multiLanguage": True,
                "speedControl": True,
                "pitchControl": False,
                "emotionControl": False,
                "multiSpeaker": False,
            },
            "description": "Context-aware TTS model with voice cloning. Part of the CPM (Chinese Pre-trained Model) family for natural speech synthesis.",
            "icon": "🎯",
        },
    }


def get_default_llm_providers_config() -> Dict[str, Dict[str, Any]]:
    """
    Get default LLM provider configurations with enhanced metadata.

    Includes both cloud API (Gemini) and local models (Ollama).

    Returns:
        Dict of LLM provider configs with capabilities, pricing, limits, and metadata
    """
    return {
        # Gemini Cloud Models (Default)
        "gemini-2.5-flash": {
            "name": "Gemini 2.5 Flash",
            "endpoint": "https://generativelanguage.googleapis.com/v1beta/models",
            "provider_type": "llm",
            "model_name": "gemini-2.5-flash",  # Model name for API calls
            "languages": 100,
            "languageList": ["en", "es", "fr", "de", "it", "pt", "nl", "pl", "tw", "ak", "ar", "zh", "ja", "ko", "hi", "ru", "tr"],
            "capabilities": {
                "multiLanguage": True,
                "streaming": True,  # Gemini supports streaming
                "reasoning": True,
                "codeGeneration": True,
                "functionCalling": True,
                "vision": False,  # 2.5 Flash text-only
                "culturalContext": True,
                "longContext": True,
            },
            "description": "Google's fastest and most cost-effective LLM. Excellent for real-time applications, multilingual chat, and code generation. Default model for KasaAI platform.",
            "icon": "⚡",
            "status": "online",
            "metadata": {
                "baseModel": "Google Gemini 2.5",
                "modelSize": "Unknown (Cloud API)",
                "contextWindow": 1048576,  # 1M tokens
                "maxOutputTokens": 8192,
                "fineTuned": False,
                "trainingData": "Multilingual web data, code, scientific papers (Google proprietary)",
                "lastUpdated": "2025-01-15",
                "pricing": {
                    "inputPer1kTokens": 0.000075,  # $0.075 per 1M tokens
                    "outputPer1kTokens": 0.0003,    # $0.30 per 1M tokens
                    "currency": "USD"
                },
                "limits": {
                    "maxInputTokens": 1048576,  # 1M tokens
                    "maxOutputTokens": 8192,
                    "rateLimitRPM": 1000  # Higher rate limit for cloud API
                },
                "useCases": ["General chat", "Code generation", "Multilingual conversation", "Real-time applications", "Document analysis", "Content creation"],
                "strengths": ["Ultra-fast responses", "Massive context window (1M tokens)", "Excellent multilingual support", "Function calling", "Very low cost"],
                "limitations": ["Requires internet connection", "No vision support (text-only)", "Cloud API latency"]
            },
        },
        "gemini-2.0-flash-exp": {
            "name": "Gemini 2.0 Flash (Experimental)",
            "endpoint": "https://generativelanguage.googleapis.com/v1beta/models",
            "provider_type": "llm",
            "model_name": "gemini-2.0-flash-exp",
            "languages": 100,
            "languageList": ["en", "es", "fr", "de", "it", "pt", "nl", "pl", "tw", "ak", "ar", "zh", "ja", "ko", "hi", "ru", "tr"],
            "capabilities": {
                "multiLanguage": True,
                "streaming": True,
                "reasoning": True,
                "codeGeneration": True,
                "functionCalling": True,
                "vision": False,
                "culturalContext": True,
                "longContext": True,
            },
            "description": "Experimental version of Gemini 2.0 Flash with cutting-edge features. Free tier available for testing and development.",
            "icon": "🧪",
            "status": "online",
            "metadata": {
                "baseModel": "Google Gemini 2.0",
                "modelSize": "Unknown (Cloud API)",
                "contextWindow": 1048576,
                "maxOutputTokens": 8192,
                "fineTuned": False,
                "trainingData": "Latest Google training data (experimental)",
                "lastUpdated": "2024-12-15",
                "pricing": {
                    "inputPer1kTokens": 0.0,  # Free tier
                    "outputPer1kTokens": 0.0,
                    "currency": "USD"
                },
                "limits": {
                    "maxInputTokens": 1048576,
                    "maxOutputTokens": 8192,
                    "rateLimitRPM": 500  # Lower rate limit for experimental
                },
                "useCases": ["Testing", "Development", "Experimentation", "Free tier projects"],
                "strengths": ["Free tier", "Latest features", "Large context window", "Fast responses"],
                "limitations": ["Experimental (may change)", "Lower rate limits", "No SLA guarantees"]
            },
        },

        # Local Ollama Models
        "aya_8b": {
            "name": "Aya 8B (Multilingual)",
            "endpoint": os.getenv("OLLAMA_ENDPOINT", "https://ollama.ailabsafrica.com"),
            "provider_type": "llm",
            "model_name": "aya:8b",  # Actual Ollama model name
            "languages": 23,
            "languageList": ["en", "tw", "ak", "yo", "ig", "ha", "sw", "am", "ar", "zh", "fr", "de", "es", "pt", "hi", "ja", "ko", "ru", "tr", "vi", "th", "id", "ms"],
            "capabilities": {
                "multiLanguage": True,
                "streaming": True,
                "culturalContext": True,
                "reasoning": True,
                "codeGeneration": True,
                "functionCalling": False,
                "vision": False,
            },
            "description": "Cohere's Aya model optimized for 23 languages including African languages (Twi, Yoruba, Igbo, Hausa, Swahili). Excellent for multilingual conversations and cultural context.",
            "icon": "🌍",
            "metadata": {
                "baseModel": "cohere/aya-8b",
                "modelSize": "8B",
                "contextWindow": 8192,
                "maxOutputTokens": 4096,
                "fineTuned": False,
                "trainingData": "Multilingual web data including African languages",
                "lastUpdated": "2024-12-01",
                "pricing": {
                    "inputPer1kTokens": 0.0001,
                    "outputPer1kTokens": 0.0002,
                    "currency": "USD"
                },
                "limits": {
                    "maxInputTokens": 8192,
                    "maxOutputTokens": 4096,
                    "rateLimitRPM": 100
                },
                "useCases": ["African language support", "Multilingual chat", "Translation", "Cultural context"],
                "strengths": ["23 language support", "African languages", "Cultural understanding", "Streaming"],
                "limitations": ["Smaller context window", "No function calling", "No vision support"]
            },
        },
        "llama_32_3b": {
            "name": "Llama 3.2 3B",
            "endpoint": os.getenv("OLLAMA_ENDPOINT", "https://ollama.ailabsafrica.com"),
            "provider_type": "llm",
            "model_name": "llama3.2:3b",  # Actual Ollama model name
            "languages": 8,
            "languageList": ["en", "es", "fr", "de", "it", "pt", "nl", "pl"],
            "capabilities": {
                "multiLanguage": True,
                "streaming": True,
                "reasoning": True,
                "codeGeneration": True,
                "functionCalling": False,
                "vision": False,
                "culturalContext": False,
            },
            "description": "Compact but powerful Llama model for general tasks. Excellent for coding, reasoning, and multilingual conversations with fast response times.",
            "icon": "🦙",
            "metadata": {
                "baseModel": "meta-llama/Llama-3.2-3B",
                "modelSize": "3B",
                "contextWindow": 8192,
                "maxOutputTokens": 4096,
                "fineTuned": False,
                "trainingData": "General web data, code, multilingual text",
                "lastUpdated": "2024-09-25",
                "pricing": {
                    "inputPer1kTokens": 0.00015,
                    "outputPer1kTokens": 0.0003,
                    "currency": "USD"
                },
                "limits": {
                    "maxInputTokens": 8192,
                    "maxOutputTokens": 4096,
                    "rateLimitRPM": 150
                },
                "useCases": ["General chat", "Code generation", "Text analysis", "Creative writing", "Summarization"],
                "strengths": ["Fast responses", "Good reasoning", "Code understanding", "Multilingual"],
                "limitations": ["Smaller context window", "No function calling", "No vision support"]
            },
        },
        "llama_31_8b": {
            "name": "Llama 3.1 8B",
            "endpoint": os.getenv("OLLAMA_ENDPOINT", "https://ollama.ailabsafrica.com"),
            "provider_type": "llm",
            "model_name": "llama3.1:8b",  # Actual Ollama model name
            "languages": 8,
            "languageList": ["en", "es", "fr", "de", "it", "pt", "nl", "pl"],
            "capabilities": {
                "multiLanguage": True,
                "streaming": True,
                "reasoning": True,
                "codeGeneration": True,
                "functionCalling": False,
                "vision": False,
                "longContext": True,
            },
            "description": "Larger Llama model with better reasoning and longer context. Great for complex tasks, coding, and document analysis.",
            "icon": "🦙",
            "metadata": {
                "baseModel": "meta-llama/Llama-3.1-8B",
                "modelSize": "8B",
                "contextWindow": 128000,
                "maxOutputTokens": 8192,
                "fineTuned": False,
                "trainingData": "General web data, code, multilingual text",
                "lastUpdated": "2024-07-23",
                "pricing": {
                    "inputPer1kTokens": 0.0002,
                    "outputPer1kTokens": 0.0004,
                    "currency": "USD"
                },
                "limits": {
                    "maxInputTokens": 128000,
                    "maxOutputTokens": 8192,
                    "rateLimitRPM": 100
                },
                "useCases": ["Complex reasoning", "Code generation", "Document analysis", "Long context tasks"],
                "strengths": ["Large context window", "Better reasoning", "Code understanding", "Multilingual"],
                "limitations": ["Slower than 3B", "No function calling", "No vision support"]
            },
        },
        "mistral_7b": {
            "name": "Mistral 7B",
            "endpoint": os.getenv("OLLAMA_ENDPOINT", "https://ollama.ailabsafrica.com"),
            "provider_type": "llm",
            "model_name": "mistral:7b",  # Actual Ollama model name
            "languages": 5,
            "languageList": ["en", "es", "fr", "de", "it"],
            "capabilities": {
                "multiLanguage": True,
                "streaming": True,
                "reasoning": True,
                "codeGeneration": True,
                "functionCalling": False,
                "vision": False,
            },
            "description": "Fast and efficient Mistral model. Excellent balance of speed and quality for general tasks and code generation.",
            "icon": "💨",
            "metadata": {
                "baseModel": "mistralai/Mistral-7B-v0.1",
                "modelSize": "7B",
                "contextWindow": 8192,
                "maxOutputTokens": 4096,
                "fineTuned": False,
                "trainingData": "General web data, code",
                "lastUpdated": "2024-09-01",
                "pricing": {
                    "inputPer1kTokens": 0.00015,
                    "outputPer1kTokens": 0.0003,
                    "currency": "USD"
                },
                "limits": {
                    "maxInputTokens": 8192,
                    "maxOutputTokens": 4096,
                    "rateLimitRPM": 100
                },
                "useCases": ["General chat", "Code generation", "Fast responses", "Text analysis"],
                "strengths": ["Fast inference", "Good code generation", "Efficient"],
                "limitations": ["Limited language support", "No function calling", "No vision support"]
            },
        },
    }


def get_default_asr_providers_config() -> Dict[str, Dict[str, Any]]:
    """
    Get default ASR provider configurations.

    Returns:
        Dict of ASR provider configs
    """
    # Centralized Whisper API endpoint (GPU-accelerated)
    whisper_endpoint = os.getenv("WHISPER_ENDPOINT", "https://whisper.ailabsafrica.com")

    return {
        "openai_whisper": {
            "name": "OpenAI Whisper",
            "endpoint": "https://api.openai.com",
            "provider_type": "asr",
            "languages": 99,
            "languageList": ["en", "es", "fr", "de", "it", "pt", "ar", "zh", "ja", "ko"],
            "capabilities": {
                "multiLanguage": True,
                "timestamps": True,
                "wordLevelTimestamps": True,
                "diarization": False,
                "punctuation": True,
            },
            "description": "OpenAI's Whisper API - reliable cloud ASR with 99+ language support.",
            "icon": "🤖",
            "metadata": {
                "accuracy": "96%",
                "latency": "1-3s",
                "cost_per_minute": "$0.006",
            },
            "requires_api_key": True,
            "api_key_env": "OPENAI_API_KEY",
        },
        "akan_whisper_giftmark": {
            "name": "GiftMark Akan Whisper",
            "endpoint": os.getenv("AKAN_WHISPER_ENDPOINT", whisper_endpoint),
            "provider_type": "asr",
            "model_name": "akan-whisper",
            "languages": 2,
            "languageList": ["tw", "ak"],
            "capabilities": {
                "multiLanguage": False,
                "timestamps": True,
                "wordLevelTimestamps": True,
                "punctuation": True,
            },
            "description": "Specialized Akan/Twi ASR with 92.9% accuracy. Best for Ghanaian languages.",
            "icon": "🇬🇭",
            "metadata": {
                "accuracy": "92.9%",
                "latency": "500ms",
                "model_size": "fine-tuned",
            },
        },
        "faster_whisper_medium": {
            "name": "Faster Whisper Medium",
            "endpoint": whisper_endpoint,
            "provider_type": "asr",
            "model_name": "medium",
            "languages": 99,
            "languageList": ["en", "es", "fr", "de", "it", "pt", "ar", "zh", "ja", "ko", "tw", "ak"],
            "capabilities": {
                "multiLanguage": True,
                "timestamps": True,
                "wordLevelTimestamps": True,
                "diarization": False,
                "punctuation": True,
                "streaming": False,
            },
            "description": "GPU-accelerated Whisper Medium model. Good balance of speed and accuracy.",
            "icon": "⚡",
            "metadata": {
                "accuracy": "93%",
                "latency": "1-2s",
                "model_size": "medium",
                "vram_required": "5GB",
            },
        },
        "faster_whisper_large": {
            "name": "Faster Whisper Large v3",
            "endpoint": whisper_endpoint,
            "provider_type": "asr",
            "model_name": "large-v3",
            "languages": 99,
            "languageList": ["en", "es", "fr", "de", "it", "pt", "ar", "zh", "ja", "ko", "tw", "ak"],
            "capabilities": {
                "multiLanguage": True,
                "timestamps": True,
                "wordLevelTimestamps": True,
                "diarization": False,
                "punctuation": True,
                "streaming": False,
            },
            "description": "State-of-the-art Whisper Large v3 model. Best accuracy for all languages.",
            "icon": "🎤",
            "metadata": {
                "accuracy": "96%",
                "latency": "2-4s",
                "model_size": "large-v3",
                "vram_required": "10GB",
            },
        },
        "faster_whisper_small": {
            "name": "Faster Whisper Small",
            "endpoint": whisper_endpoint,
            "provider_type": "asr",
            "model_name": "small",
            "languages": 99,
            "languageList": ["en", "es", "fr", "de", "it", "pt", "ar", "zh", "ja", "ko"],
            "capabilities": {
                "multiLanguage": True,
                "timestamps": True,
                "wordLevelTimestamps": True,
                "diarization": False,
                "punctuation": True,
                "streaming": False,
            },
            "description": "Fast and lightweight Whisper Small model. Good for real-time applications.",
            "icon": "🚀",
            "metadata": {
                "accuracy": "89%",
                "latency": "0.5-1s",
                "model_size": "small",
                "vram_required": "2GB",
            },
        },
        # Legacy alias - kept for backward compatibility
        "whisper_large_v3": {
            "name": "Whisper Large v3",
            "endpoint": whisper_endpoint,
            "provider_type": "asr",
            "model_name": "large-v3",
            "languages": 99,
            "languageList": ["en", "es", "fr", "de", "it", "pt", "ar", "zh", "ja", "ko"],
            "capabilities": {
                "multiLanguage": True,
                "timestamps": True,
                "wordLevelTimestamps": True,
                "diarization": False,
                "punctuation": True,
            },
            "description": "State-of-the-art multilingual speech recognition (alias for faster_whisper_large).",
            "icon": "🎤",
            "metadata": {
                "accuracy": "96%",
                "latency": "2-5s",
            },
        },
        "groq_whisper_large_v3_turbo": {
            "name": "Groq Whisper Large v3 Turbo",
            "endpoint": "https://api.groq.com/openai",
            "provider_type": "asr",
            "model_name": "whisper-large-v3-turbo",
            "languages": 99,
            "languageList": ["en", "es", "fr", "de", "it", "pt", "ar", "zh", "ja", "ko", "hi", "ru", "tr", "nl", "pl"],
            "capabilities": {
                "multiLanguage": True,
                "timestamps": True,
                "wordLevelTimestamps": True,
                "diarization": False,
                "punctuation": True,
            },
            "description": "Groq's ultra-fast Whisper - 228x real-time speed at $0.04/hour. Best price/performance.",
            "icon": "⚡",
            "metadata": {
                "accuracy": "88%",
                "latency": "<1s",
                "cost_per_hour": "$0.04",
                "speed_factor": "228x",
            },
            "requires_api_key": True,
            "api_key_env": "GROQ_API_KEY",
        },
        "groq_whisper_large_v3": {
            "name": "Groq Whisper Large v3",
            "endpoint": "https://api.groq.com/openai",
            "provider_type": "asr",
            "model_name": "whisper-large-v3",
            "languages": 99,
            "languageList": ["en", "es", "fr", "de", "it", "pt", "ar", "zh", "ja", "ko", "hi", "ru", "tr", "nl", "pl"],
            "capabilities": {
                "multiLanguage": True,
                "timestamps": True,
                "wordLevelTimestamps": True,
                "diarization": False,
                "punctuation": True,
                "translation": True,
            },
            "description": "Groq's high-accuracy Whisper - 217x real-time speed. Supports translation to English.",
            "icon": "🚀",
            "metadata": {
                "accuracy": "90%",
                "latency": "<1s",
                "cost_per_hour": "$0.111",
                "speed_factor": "217x",
            },
            "requires_api_key": True,
            "api_key_env": "GROQ_API_KEY",
        },
    }
