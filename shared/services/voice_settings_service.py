"""
Voice Settings Service

Manages user and organization voice preferences for TTS, ASR, and LLM services.
Stores preferences in MongoDB and provides CRUD operations.

Usage:
    from apps.shared.services.voice_settings_service import (
        VoiceSettingsService,
        VoiceSettings
    )

    # Initialize service
    service = VoiceSettingsService(db)

    # Get or create user settings
    settings = await service.get_settings("user_123", "org_456")

    # Update settings
    updated = await service.update_settings(
        "user_123",
        "org_456",
        {"tts": {"default_provider": "coqui_xtts"}}
    )

Author: KasaAI
Date: 2025-11-03
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class TTSSettings(BaseModel):
    """TTS preferences."""
    default_provider: str = "kokoro"
    default_voice: Optional[str] = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-1.0, le=1.0)


class ASRSettings(BaseModel):
    """ASR preferences."""
    default_provider: str = "whisper_large_v3"  # Self-hosted at whisper.ailabsafrica.com
    language: str = "en"
    task: str = "transcribe"  # or "translate"


class LLMSettings(BaseModel):
    """LLM preferences."""
    default_model: str = "llama3.2"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=100000)


class VoicePreferences(BaseModel):
    """Voice library preferences."""
    favorite_voices: list[str] = Field(default_factory=list)
    custom_voices: list[str] = Field(default_factory=list)


class VoiceSettings(BaseModel):
    """Complete voice settings model."""
    user_id: str
    organization_id: str
    tts: TTSSettings = Field(default_factory=TTSSettings)
    asr: ASRSettings = Field(default_factory=ASRSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    voices: VoicePreferences = Field(default_factory=VoicePreferences)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# Service Class
# ============================================================================

class VoiceSettingsService:
    """
    Service for managing voice settings.

    Handles CRUD operations for user and organization voice preferences.
    Stores data in MongoDB with proper indexing for fast lookups.
    """

    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str = "voice_settings"):
        """
        Initialize the service.

        Args:
            db: MongoDB database connection
            collection_name: Name of the collection (default: "voice_settings")
        """
        self.db = db
        self.collection = db[collection_name]

    async def ensure_indexes(self):
        """
        Create MongoDB indexes for performance.

        Indexes:
            - (user_id, organization_id): Unique index for user settings
            - organization_id: For querying org defaults
            - updated_at: For sorting by recency
        """
        try:
            # Unique index on user_id + organization_id
            await self.collection.create_index(
                [("user_id", 1), ("organization_id", 1)],
                unique=True,
                name="user_org_unique"
            )

            # Index on organization_id for org-wide queries
            await self.collection.create_index(
                [("organization_id", 1)],
                name="organization_index"
            )

            # Index on updated_at for sorting
            await self.collection.create_index(
                [("updated_at", -1)],
                name="updated_at_index"
            )

            logger.info("Voice settings indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    async def get_settings(
        self,
        user_id: str,
        organization_id: str
    ) -> VoiceSettings:
        """
        Get or create voice settings for a user.

        If settings don't exist, creates default settings.
        Falls back to organization defaults if available.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            VoiceSettings object
        """
        try:
            # Try to fetch existing settings
            doc = await self.collection.find_one({
                "user_id": user_id,
                "organization_id": organization_id
            })

            if doc:
                # Remove MongoDB _id field
                doc.pop("_id", None)
                return VoiceSettings(**doc)

            # No settings found, check for org defaults
            org_defaults = await self.get_organization_defaults(organization_id)

            # Create new settings with org defaults or system defaults
            new_settings = VoiceSettings(
                user_id=user_id,
                organization_id=organization_id,
                tts=org_defaults.tts if org_defaults else TTSSettings(),
                asr=org_defaults.asr if org_defaults else ASRSettings(),
                llm=org_defaults.llm if org_defaults else LLMSettings(),
                voices=VoicePreferences()
            )

            # Save to database
            await self.collection.insert_one(new_settings.dict())

            logger.info(f"Created new voice settings for user {user_id}")
            return new_settings

        except Exception as e:
            logger.error(f"Error getting settings for user {user_id}: {e}")
            # Return defaults on error
            return VoiceSettings(
                user_id=user_id,
                organization_id=organization_id
            )

    async def update_settings(
        self,
        user_id: str,
        organization_id: str,
        updates: Dict[str, Any]
    ) -> VoiceSettings:
        """
        Update voice settings for a user.

        Performs partial update (only updates provided fields).

        Args:
            user_id: User ID
            organization_id: Organization ID
            updates: Dictionary of updates (supports nested updates)

        Returns:
            Updated VoiceSettings object

        Example:
            updates = {
                "tts": {"default_provider": "f5tts", "speed": 1.2},
                "llm": {"temperature": 0.8}
            }
        """
        try:
            # Get current settings
            current = await self.get_settings(user_id, organization_id)

            # Build update document
            update_doc = {}

            # Handle nested updates for each category
            if "tts" in updates:
                for key, value in updates["tts"].items():
                    update_doc[f"tts.{key}"] = value

            if "asr" in updates:
                for key, value in updates["asr"].items():
                    update_doc[f"asr.{key}"] = value

            if "llm" in updates:
                for key, value in updates["llm"].items():
                    update_doc[f"llm.{key}"] = value

            if "voices" in updates:
                for key, value in updates["voices"].items():
                    update_doc[f"voices.{key}"] = value

            # Always update timestamp
            update_doc["updated_at"] = datetime.utcnow()

            # Perform update
            result = await self.collection.update_one(
                {"user_id": user_id, "organization_id": organization_id},
                {"$set": update_doc}
            )

            if result.modified_count == 0:
                logger.warning(f"No settings updated for user {user_id}")

            # Fetch and return updated settings
            updated_settings = await self.get_settings(user_id, organization_id)
            logger.info(f"Updated voice settings for user {user_id}")
            return updated_settings

        except Exception as e:
            logger.error(f"Error updating settings for user {user_id}: {e}")
            raise

    async def delete_settings(
        self,
        user_id: str,
        organization_id: str
    ) -> bool:
        """
        Delete voice settings for a user.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            True if deleted, False if not found
        """
        try:
            result = await self.collection.delete_one({
                "user_id": user_id,
                "organization_id": organization_id
            })

            if result.deleted_count > 0:
                logger.info(f"Deleted voice settings for user {user_id}")
                return True
            else:
                logger.warning(f"No settings found to delete for user {user_id}")
                return False

        except Exception as e:
            logger.error(f"Error deleting settings for user {user_id}: {e}")
            raise

    async def get_organization_defaults(
        self,
        organization_id: str
    ) -> Optional[VoiceSettings]:
        """
        Get organization-wide default settings.

        Organization defaults are stored with user_id = "org_default"

        Args:
            organization_id: Organization ID

        Returns:
            VoiceSettings object or None if no defaults exist
        """
        try:
            doc = await self.collection.find_one({
                "user_id": "org_default",
                "organization_id": organization_id
            })

            if doc:
                doc.pop("_id", None)
                return VoiceSettings(**doc)

            return None

        except Exception as e:
            logger.error(f"Error getting org defaults for {organization_id}: {e}")
            return None

    async def set_organization_defaults(
        self,
        organization_id: str,
        settings: Dict[str, Any]
    ) -> VoiceSettings:
        """
        Set organization-wide default settings.

        Only admins should call this method.

        Args:
            organization_id: Organization ID
            settings: Dictionary of default settings

        Returns:
            Updated VoiceSettings object
        """
        try:
            # Build default settings
            org_defaults = VoiceSettings(
                user_id="org_default",
                organization_id=organization_id,
                tts=TTSSettings(**settings.get("tts", {})),
                asr=ASRSettings(**settings.get("asr", {})),
                llm=LLMSettings(**settings.get("llm", {})),
                voices=VoicePreferences(**settings.get("voices", {}))
            )

            # Upsert (insert or update)
            await self.collection.update_one(
                {"user_id": "org_default", "organization_id": organization_id},
                {"$set": org_defaults.dict()},
                upsert=True
            )

            logger.info(f"Set organization defaults for {organization_id}")
            return org_defaults

        except Exception as e:
            logger.error(f"Error setting org defaults for {organization_id}: {e}")
            raise

    async def get_all_settings_for_org(
        self,
        organization_id: str,
        limit: int = 100,
        skip: int = 0
    ) -> list[VoiceSettings]:
        """
        Get all user settings for an organization.

        Useful for admin dashboards.

        Args:
            organization_id: Organization ID
            limit: Maximum number of results
            skip: Number of results to skip (for pagination)

        Returns:
            List of VoiceSettings objects
        """
        try:
            cursor = self.collection.find({
                "organization_id": organization_id,
                "user_id": {"$ne": "org_default"}  # Exclude org defaults
            }).sort("updated_at", -1).skip(skip).limit(limit)

            settings_list = []
            async for doc in cursor:
                doc.pop("_id", None)
                settings_list.append(VoiceSettings(**doc))

            return settings_list

        except Exception as e:
            logger.error(f"Error getting org settings for {organization_id}: {e}")
            return []

    async def get_statistics(self, organization_id: str) -> Dict[str, Any]:
        """
        Get statistics about voice settings usage for an organization.

        Args:
            organization_id: Organization ID

        Returns:
            Dictionary with statistics
        """
        try:
            # Count total users with settings
            total_users = await self.collection.count_documents({
                "organization_id": organization_id,
                "user_id": {"$ne": "org_default"}
            })

            # Get provider usage statistics
            tts_providers = await self.collection.distinct(
                "tts.default_provider",
                {"organization_id": organization_id}
            )

            asr_providers = await self.collection.distinct(
                "asr.default_provider",
                {"organization_id": organization_id}
            )

            llm_models = await self.collection.distinct(
                "llm.default_model",
                {"organization_id": organization_id}
            )

            return {
                "total_users": total_users,
                "tts_providers": tts_providers,
                "asr_providers": asr_providers,
                "llm_models": llm_models,
                "organization_id": organization_id
            }

        except Exception as e:
            logger.error(f"Error getting statistics for {organization_id}: {e}")
            return {}
