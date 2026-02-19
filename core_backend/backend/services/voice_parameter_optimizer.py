"""
Voice Parameter Optimizer Service

Provides optimized voice parameters for different TTS providers and use cases.
Based on extensive testing and best practices for natural speech and low latency.
"""

from typing import Dict, Any
from enum import Enum


class TTSProvider(str, Enum):
    """TTS Provider identifiers."""
    ELEVENLABS = "elevenlabs"
    OPENAI = "openai"
    META_MMS = "meta_mms"
    COQUI_XTTS = "coqui_xtts"
    COQUI = "coqui"
    GOOGLE = "google"
    AZURE = "azure"


class UseCase(str, Enum):
    """Use case categories for voice optimization."""
    CUSTOMER_SERVICE = "customer_service"
    SALES = "sales"
    SUPPORT = "support"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    NEWS = "news"
    CONVERSATIONAL = "conversational"


class VoiceParameterOptimizer:
    """
    Optimizes voice parameters for natural speech and low latency.

    Key optimization principles:
    1. Natural speech: Balance between stability and variation
    2. Low latency: Streaming optimization and chunk size
    3. Language-specific: Adjust speed for different languages
    4. Use-case specific: Professional vs casual tone
    """

    # Provider-specific optimized parameters
    PROVIDER_OPTIMIZATIONS = {
        TTSProvider.ELEVENLABS: {
            # ElevenLabs has the most control over voice parameters
            "customer_service": {
                "stability": 0.75,  # Higher stability for consistency
                "clarity_similarity": 0.80,  # High clarity for understanding
                "speed": 1.05,  # Slightly faster for efficiency
                "style_exaggeration": 0.35,  # Moderate expressiveness
                "optimize_streaming_latency": 4,  # Maximum streaming optimization
            },
            "sales": {
                "stability": 0.65,  # More variation for engagement
                "clarity_similarity": 0.80,
                "speed": 1.1,  # Faster pace for energy
                "style_exaggeration": 0.55,  # More expressive
                "optimize_streaming_latency": 4,
            },
            "conversational": {
                "stability": 0.60,  # Natural variation
                "clarity_similarity": 0.75,
                "speed": 1.0,  # Normal speed
                "style_exaggeration": 0.45,  # Balanced expressiveness
                "optimize_streaming_latency": 4,
            },
        },
        TTSProvider.OPENAI: {
            # OpenAI TTS has limited parameters but excellent quality
            "customer_service": {
                "speed": 1.05,  # Slightly faster
                "stability": 0.7,  # Not used by API but stored for reference
                "clarity_similarity": 0.8,
                "style_exaggeration": 0.0,
                "optimize_streaming_latency": 3,
            },
            "sales": {
                "speed": 1.15,  # Faster for energy
                "stability": 0.65,
                "clarity_similarity": 0.8,
                "style_exaggeration": 0.0,
                "optimize_streaming_latency": 3,
            },
            "conversational": {
                "speed": 1.0,  # Natural speed
                "stability": 0.6,
                "clarity_similarity": 0.75,
                "style_exaggeration": 0.0,
                "optimize_streaming_latency": 3,
            },
        },
        TTSProvider.META_MMS: {
            # Meta MMS for African languages - focus on clarity and speed
            "customer_service": {
                "speed": 1.1,  # African languages sound better slightly faster
                "stability": 0.7,
                "clarity_similarity": 0.85,  # High clarity critical for understanding
                "style_exaggeration": 0.0,  # MMS doesn't support this
                "optimize_streaming_latency": 2,
            },
            "conversational": {
                "speed": 1.15,  # Faster for natural flow in Twi/Yoruba
                "stability": 0.65,
                "clarity_similarity": 0.8,
                "style_exaggeration": 0.0,
                "optimize_streaming_latency": 2,
            },
        },
        TTSProvider.COQUI_XTTS: {
            # Coqui XTTS for voice cloning
            "customer_service": {
                "speed": 1.05,
                "stability": 0.75,  # Higher for consistency with cloned voice
                "clarity_similarity": 0.85,
                "style_exaggeration": 0.2,
                "optimize_streaming_latency": 2,
                "temperature": 0.75,  # Controls randomness
            },
            "conversational": {
                "speed": 1.0,
                "stability": 0.65,
                "clarity_similarity": 0.8,
                "style_exaggeration": 0.3,
                "optimize_streaming_latency": 2,
                "temperature": 0.8,
            },
        },
        TTSProvider.COQUI: {
            # Standard Coqui TTS
            "customer_service": {
                "speed": 1.05,
                "stability": 0.7,
                "clarity_similarity": 0.8,
                "style_exaggeration": 0.0,
                "optimize_streaming_latency": 2,
            },
            "conversational": {
                "speed": 1.0,
                "stability": 0.65,
                "clarity_similarity": 0.75,
                "style_exaggeration": 0.0,
                "optimize_streaming_latency": 2,
            },
        },
    }

    # Language-specific speed adjustments
    LANGUAGE_SPEED_ADJUSTMENTS = {
        "en": 1.0,  # English baseline
        "twi": 1.15,  # Twi sounds better slightly faster
        "yoruba": 1.12,  # Yoruba also benefits from slight speedup
        "yo": 1.12,
        "akan": 1.15,
        "hausa": 1.1,
        "igbo": 1.1,
        "swahili": 1.05,
        "multilingual": 1.05,
    }

    @classmethod
    def get_optimized_parameters(
        cls,
        tts_provider: str,
        use_case: str = "conversational",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get optimized voice parameters for a specific provider and use case.

        Args:
            tts_provider: TTS provider ID (e.g., "elevenlabs", "openai")
            use_case: Use case category (e.g., "customer_service", "sales")
            language: Language code (e.g., "en", "twi", "yoruba")

        Returns:
            Dictionary of optimized voice parameters
        """
        # Normalize provider ID
        provider = cls._normalize_provider(tts_provider)

        # Get base parameters for provider and use case
        if provider in cls.PROVIDER_OPTIMIZATIONS:
            provider_params = cls.PROVIDER_OPTIMIZATIONS[provider]

            # Get use case specific params, fallback to conversational
            if use_case in provider_params:
                params = provider_params[use_case].copy()
            else:
                params = provider_params.get("conversational", {}).copy()
        else:
            # Default parameters for unknown providers
            params = {
                "stability": 0.7,
                "clarity_similarity": 0.8,
                "speed": 1.0,
                "style_exaggeration": 0.0,
                "optimize_streaming_latency": 2,
            }

        # Apply language-specific speed adjustment
        language_lower = language.lower() if language else "en"
        if language_lower in cls.LANGUAGE_SPEED_ADJUSTMENTS:
            speed_multiplier = cls.LANGUAGE_SPEED_ADJUSTMENTS[language_lower]
            params["speed"] = params.get("speed", 1.0) * speed_multiplier

        return params

    @classmethod
    def _normalize_provider(cls, provider_id: str) -> str:
        """Normalize provider ID to standard format."""
        if not provider_id:
            return TTSProvider.OPENAI

        provider_lower = provider_id.lower()

        # Map variations to standard IDs
        if "eleven" in provider_lower:
            return TTSProvider.ELEVENLABS
        elif "openai" in provider_lower:
            return TTSProvider.OPENAI
        elif "mms" in provider_lower or "meta" in provider_lower:
            return TTSProvider.META_MMS
        elif "xtts" in provider_lower:
            return TTSProvider.COQUI_XTTS
        elif "coqui" in provider_lower:
            return TTSProvider.COQUI

        return provider_lower

    @classmethod
    def get_latency_optimization_config(cls, tts_provider: str) -> Dict[str, Any]:
        """
        Get latency optimization configuration for a TTS provider.

        Returns configuration for:
        - Streaming chunk size
        - Buffer size
        - Pre-buffering strategy
        """
        provider = cls._normalize_provider(tts_provider)

        configs = {
            TTSProvider.ELEVENLABS: {
                "chunk_size": 1024,  # Bytes per chunk
                "buffer_size": 2,  # Number of chunks to buffer
                "enable_streaming": True,
                "optimize_streaming_latency": 4,  # ElevenLabs API param
            },
            TTSProvider.OPENAI: {
                "chunk_size": 4096,
                "buffer_size": 1,
                "enable_streaming": True,
                "optimize_streaming_latency": 3,
            },
            TTSProvider.META_MMS: {
                "chunk_size": 2048,
                "buffer_size": 2,
                "enable_streaming": True,
                "optimize_streaming_latency": 2,
            },
            TTSProvider.COQUI_XTTS: {
                "chunk_size": 2048,
                "buffer_size": 2,
                "enable_streaming": True,
                "optimize_streaming_latency": 2,
            },
        }

        return configs.get(provider, {
            "chunk_size": 2048,
            "buffer_size": 2,
            "enable_streaming": True,
            "optimize_streaming_latency": 2,
        })

    @classmethod
    def get_quality_preset(cls, preset_name: str) -> Dict[str, Any]:
        """
        Get predefined quality presets.

        Presets:
        - ultra_fast: Minimum latency, acceptable quality
        - balanced: Good balance of quality and latency
        - high_quality: Maximum quality, higher latency
        """
        presets = {
            "ultra_fast": {
                "stability": 0.7,
                "clarity_similarity": 0.75,
                "speed": 1.1,
                "style_exaggeration": 0.2,
                "optimize_streaming_latency": 4,
            },
            "balanced": {
                "stability": 0.7,
                "clarity_similarity": 0.8,
                "speed": 1.05,
                "style_exaggeration": 0.3,
                "optimize_streaming_latency": 3,
            },
            "high_quality": {
                "stability": 0.75,
                "clarity_similarity": 0.85,
                "speed": 1.0,
                "style_exaggeration": 0.4,
                "optimize_streaming_latency": 1,
            },
        }

        return presets.get(preset_name, presets["balanced"])


# Singleton instance
voice_parameter_optimizer = VoiceParameterOptimizer()
