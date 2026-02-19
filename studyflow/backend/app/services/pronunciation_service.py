"""
Pronunciation service for StudyFlow.

Provides text-to-speech functionality for:
- Answer pronunciation (students can listen to AI answers)
- Word/phrase pronunciation (language learning support)
- Study material narration

Uses the unified @shared/tts/ system with:
- AsyncTTSClient for synthesis
- TTSBillingManager for automatic wallet integration
- MongoDB GridFS caching (40% cost reduction)
- Provider health monitoring

Migration: Migrated from TTSProviderService to AsyncTTSClient (2025-11-23)
"""

import sys
import logging
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime

# Add shared services to path
sys.path.insert(0, "/opt/kasaai/apps")

from shared.tts.client import AsyncTTSClient
from shared.tts.models import TTSProvider, TTSRequest, TTSResponse, AudioFormat
from shared.tts.billing import TTSBillingManager
from shared.integration.wallet import WalletService, Currency
from shared.integration.usage_calculator import PricingTier
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.core.database import MongoDB

logger = logging.getLogger(__name__)


class PronunciationService:
    """
    Service for pronunciation and audio generation.

    Uses unified @shared/tts/ system with automatic billing, caching,
    and multi-provider support.
    """

    _billing_manager: Optional[TTSBillingManager] = None
    _initialized: bool = False

    @classmethod
    async def get_billing_manager(cls) -> TTSBillingManager:
        """
        Get or create TTSBillingManager instance.

        Returns:
            TTSBillingManager instance

        Raises:
            RuntimeError: If billing manager initialization fails
        """
        if cls._billing_manager is None:
            try:
                # Get MongoDB database
                db = MongoDB.get_database()

                # Initialize wallet service
                wallet_service = WalletService(database=db)

                # Initialize billing manager
                cls._billing_manager = TTSBillingManager(
                    wallet_service=wallet_service,
                    pricing_tier=PricingTier.BASIC,
                    currency=Currency.GHS
                )

                cls._initialized = True
                logger.info("✓ TTS Billing Manager initialized for StudyFlow")

            except Exception as e:
                logger.error(f"Failed to initialize TTS billing manager: {e}")
                raise RuntimeError(f"TTS billing manager initialization failed: {e}")

        return cls._billing_manager

    @staticmethod
    async def synthesize_answer(
        user_id: str,
        answer_text: str,
        language: str = "en",
        provider: TTSProvider = TTSProvider.COQUI_XTTS,
        speed: float = 0.9
    ) -> Tuple[bytes, float, str]:
        """
        Synthesize AI answer to audio for student listening.

        Args:
            user_id: User ID for billing (typically parent's wallet)
            answer_text: Answer text to synthesize
            language: Language code (default: en)
            provider: TTS provider to use (default: COQUI_XTTS)
            speed: Speech speed (default: 0.9 - slightly slower for learning)

        Returns:
            Tuple of (audio_bytes, cost_ghs, transaction_id)

        Note:
            Cost is automatically deducted from user's wallet.
            Slower speed (0.9) aids comprehension for students.
        """
        try:
            # Get billing manager
            billing_manager = await PronunciationService.get_billing_manager()

            # Synthesize with automatic billing
            response, transaction = await billing_manager.synthesize_with_billing(
                user_id=user_id,
                text=answer_text,
                provider=provider,
                language=language,
                output_format=AudioFormat.WAV,
                # Note: speed parameter not yet supported in unified API
                # Will be added in future enhancement
            )

            logger.info(
                f"Answer audio synthesized: {len(response.audio)} bytes, "
                f"duration={response.duration:.2f}s, cost=GHS {response.cost:.6f}"
            )

            return response.audio, response.cost, transaction.id

        except ValueError as e:
            logger.error(f"Answer synthesis validation error: {e}")
            raise ValueError(f"Invalid synthesis parameters: {e}")
        except Exception as e:
            logger.error(f"Answer synthesis failed: {e}")
            raise Exception(f"Synthesis failed: {e}")

    @staticmethod
    async def synthesize_word_pronunciation(
        user_id: str,
        word: str,
        language: str = "en",
        provider: TTSProvider = TTSProvider.COQUI_XTTS
    ) -> Tuple[bytes, float, str]:
        """
        Synthesize word/phrase pronunciation for language learning.

        Args:
            user_id: User ID for billing
            word: Word or phrase to pronounce
            language: Language code (default: en)
            provider: TTS provider to use (default: COQUI_XTTS)

        Returns:
            Tuple of (audio_bytes, cost_ghs, transaction_id)

        Note:
            Uses unified TTS system with automatic caching.
            Repeated words will hit cache (free, instant).
        """
        try:
            # Get billing manager
            billing_manager = await PronunciationService.get_billing_manager()

            # Synthesize with automatic billing
            response, transaction = await billing_manager.synthesize_with_billing(
                user_id=user_id,
                text=word,
                provider=provider,
                language=language,
                output_format=AudioFormat.WAV
            )

            logger.info(
                f"Pronunciation synthesized: '{word}' ({language}), "
                f"cost=GHS {response.cost:.6f}, cache_hit={response.cache_hit}"
            )

            return response.audio, response.cost, transaction.id

        except ValueError as e:
            logger.error(f"Pronunciation synthesis validation error: {e}")
            raise ValueError(f"Invalid synthesis parameters: {e}")
        except Exception as e:
            logger.error(f"Pronunciation synthesis failed: {e}")
            raise Exception(f"Synthesis failed: {e}")

    @staticmethod
    async def estimate_synthesis_cost(
        text: str,
        provider: TTSProvider = TTSProvider.COQUI_XTTS,
        voice_cloning: bool = False
    ) -> float:
        """
        Estimate cost of synthesizing text before actual synthesis.

        Args:
            text: Text to synthesize
            provider: TTS provider to use
            voice_cloning: Whether voice cloning will be used

        Returns:
            Estimated cost in GHS

        Raises:
            Exception: If cost estimation fails
        """
        try:
            # Get billing manager
            billing_manager = await PronunciationService.get_billing_manager()

            # Estimate cost
            cost_estimate = await billing_manager.estimate_cost(
                text=text,
                provider=provider,
                voice_cloning=voice_cloning
            )

            return cost_estimate

        except Exception as e:
            logger.error(f"Cost estimation failed: {e}")
            raise Exception(f"Cost estimation failed: {e}")

    @staticmethod
    async def get_available_providers() -> List[Dict[str, Any]]:
        """
        Get list of available TTS providers with their capabilities.

        Returns:
            List of provider dictionaries with id, name, status, etc.

        Raises:
            Exception: If provider retrieval fails

        Note:
            Providers are fetched from unified TTS system with real-time
            health status monitoring.
        """
        try:
            # Use AsyncTTSClient to get providers
            async with AsyncTTSClient() as client:
                providers = await client.get_providers()

            # Format for StudyFlow compatibility
            provider_list = []
            for provider in providers:
                provider_list.append({
                    "id": provider.id,
                    "name": provider.name,
                    "description": provider.description,
                    "status": provider.status.value,
                    "is_available": provider.status.value == "online",
                    "languages": provider.languages,
                    "voices": provider.voices,
                    "features": {
                        "voice_cloning": provider.voice_cloning_supported,
                        "streaming": provider.streaming_supported,
                        "multilingual": len(provider.languages) > 1
                    },
                    "quality": "high" if provider.quality_score >= 8 else "medium",
                    "latency": "low" if provider.latency_ms < 500 else "medium"
                })

            return provider_list

        except Exception as e:
            logger.error(f"Failed to get providers: {e}")
            raise Exception(f"Provider retrieval failed: {e}")

    @staticmethod
    async def get_synthesis_history(
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get user's recent TTS synthesis history.

        Args:
            user_id: User ID
            limit: Maximum number of records (default: 10)

        Returns:
            List of synthesis records with text, cost, timestamp

        Note:
            This would require implementing transaction history
            retrieval from WalletService. Placeholder for now.
        """
        # TODO: Implement transaction history retrieval
        # This would query WalletService for TTS-related transactions
        logger.warning("Synthesis history not yet implemented")
        return []
