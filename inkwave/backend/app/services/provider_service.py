"""
Provider Configuration Service.

Manages AI provider configurations (STT, TTS, LLM) in MongoDB.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.models.provider import ProviderConfig, ProviderConfigInDB, CostInfo

logger = logging.getLogger(__name__)


class ProviderService:
    """Service for managing provider configurations."""

    @staticmethod
    async def list_providers(
        provider_type: Optional[str] = None
    ) -> List[ProviderConfigInDB]:
        """
        List all provider configurations.

        Args:
            provider_type: Filter by type (stt, tts, llm)

        Returns:
            List of provider configurations
        """
        db = get_db()
        query = {}
        if provider_type:
            query["provider_type"] = provider_type

        cursor = db.provider_configs.find(query)
        providers = []

        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            providers.append(ProviderConfigInDB(**doc))

        logger.info(f"Listed {len(providers)} providers (type={provider_type})")
        return providers

    @staticmethod
    async def get_provider(
        provider_type: str, provider_id: str
    ) -> Optional[ProviderConfigInDB]:
        """
        Get a specific provider configuration.

        Args:
            provider_type: Provider type (stt, tts, llm)
            provider_id: Provider ID (openai, google, etc.)

        Returns:
            Provider configuration or None if not found
        """
        db = get_db()
        doc = await db.provider_configs.find_one({
            "provider_type": provider_type,
            "provider_id": provider_id
        })

        if doc:
            doc["_id"] = str(doc["_id"])
            return ProviderConfigInDB(**doc)

        return None

    @staticmethod
    async def create_or_update_provider(
        provider: ProviderConfig
    ) -> ProviderConfigInDB:
        """
        Create or update a provider configuration.

        Args:
            provider: Provider configuration

        Returns:
            Created/updated provider configuration
        """
        db = get_db()

        # Check if provider exists
        existing = await ProviderService.get_provider(
            provider.provider_type, provider.provider_id
        )

        provider_dict = provider.model_dump()
        provider_dict["updated_at"] = datetime.utcnow()

        if existing:
            # Update existing
            await db.provider_configs.update_one(
                {
                    "provider_type": provider.provider_type,
                    "provider_id": provider.provider_id
                },
                {"$set": provider_dict}
            )
            logger.info(f"Updated provider: {provider.provider_type}/{provider.provider_id}")
        else:
            # Create new
            provider_dict["created_at"] = datetime.utcnow()
            await db.provider_configs.insert_one(provider_dict)
            logger.info(f"Created provider: {provider.provider_type}/{provider.provider_id}")

        # Return updated provider
        return await ProviderService.get_provider(
            provider.provider_type, provider.provider_id
        )

    @staticmethod
    async def get_default_provider(provider_type: str) -> Optional[ProviderConfigInDB]:
        """
        Get the default provider for a type.

        Args:
            provider_type: Provider type (stt, tts, llm)

        Returns:
            Default provider or None if not set
        """
        db = get_db()
        doc = await db.provider_configs.find_one({
            "provider_type": provider_type,
            "is_default": True,
            "enabled": True
        })

        if doc:
            doc["_id"] = str(doc["_id"])
            return ProviderConfigInDB(**doc)

        return None

    @staticmethod
    async def set_default_provider(provider_type: str, provider_id: str) -> bool:
        """
        Set a provider as default for its type.

        Unsets all other defaults of the same type.

        Args:
            provider_type: Provider type (stt, tts, llm)
            provider_id: Provider ID to set as default

        Returns:
            True if successful
        """
        db = get_db()

        # Unset all defaults of same type
        await db.provider_configs.update_many(
            {"provider_type": provider_type},
            {"$set": {"is_default": False, "updated_at": datetime.utcnow()}}
        )

        # Set new default
        result = await db.provider_configs.update_one(
            {
                "provider_type": provider_type,
                "provider_id": provider_id
            },
            {
                "$set": {
                    "is_default": True,
                    "enabled": True,  # Auto-enable when setting as default
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:
            logger.info(f"Set default provider: {provider_type}/{provider_id}")
            return True

        return False

    @staticmethod
    async def update_usage_stats(
        provider_type: str,
        provider_id: str,
        cost_usd: float,
        latency_ms: float
    ):
        """
        Update provider usage statistics.

        Args:
            provider_type: Provider type (stt, tts, llm)
            provider_id: Provider ID
            cost_usd: Cost in USD
            latency_ms: Latency in milliseconds
        """
        db = get_db()

        provider = await ProviderService.get_provider(provider_type, provider_id)
        if not provider:
            logger.warning(f"Provider not found: {provider_type}/{provider_id}")
            return

        # Calculate new average latency
        total_usage = provider.total_usage_count
        current_avg = provider.avg_latency_ms
        new_avg = ((current_avg * total_usage) + latency_ms) / (total_usage + 1)

        await db.provider_configs.update_one(
            {
                "provider_type": provider_type,
                "provider_id": provider_id
            },
            {
                "$inc": {
                    "total_usage_count": 1,
                    "total_cost_usd": cost_usd
                },
                "$set": {
                    "avg_latency_ms": round(new_avg, 2),
                    "last_used": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

    @staticmethod
    async def initialize_default_providers():
        """
        Initialize default provider configurations if not exist.

        Creates default entries for:
        - OpenAI Whisper (STT)
        - OpenAI TTS (TTS)
        - Gemini 2.5 Flash (LLM)
        """
        from app.core.config import settings

        default_providers = [
            ProviderConfig(
                provider_type="stt",
                provider_id="openai",
                name="OpenAI Whisper",
                model="whisper-1",
                enabled=True,
                is_default=True,
                status="active",
                cost_info=CostInfo(per_minute_usd=0.006)
            ),
            ProviderConfig(
                provider_type="tts",
                provider_id="openai",
                name="OpenAI TTS",
                model=settings.OPENAI_TTS_MODEL,
                voice=settings.OPENAI_TTS_VOICE,
                enabled=True,
                is_default=True,
                status="active",
                cost_info=CostInfo(per_1k_chars_usd=0.015)
            ),
            ProviderConfig(
                provider_type="llm",
                provider_id="gemini",
                name="Gemini 2.5 Flash",
                model=settings.GEMINI_MODEL,
                enabled=True,
                is_default=True,
                status="active",
                cost_info=CostInfo(per_query_usd=0.0003)
            ),
        ]

        for provider in default_providers:
            existing = await ProviderService.get_provider(
                provider.provider_type, provider.provider_id
            )
            if not existing:
                await ProviderService.create_or_update_provider(provider)
                logger.info(f"Initialized default provider: {provider.name}")
