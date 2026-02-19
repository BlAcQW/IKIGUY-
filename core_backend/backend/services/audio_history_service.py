"""
Audio History Service

Manages TTS synthesis history with MongoDB storage, soft deletes, and 30-day retention.

Created: 2025-10-27
Sprint 2: User Experience Enhancements (Phase 8)
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pydantic import BaseModel, Field
from bson import ObjectId
import os

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class AudioHistoryItem(BaseModel):
    """Audio synthesis history item."""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    text: str  # First 200 characters
    full_text: str  # Complete text (for regeneration)
    provider_id: str
    voice_id: Optional[str] = None
    language: str = "en"
    audio_base64: Optional[str] = None  # Store audio data (consider S3 for production)
    duration_seconds: float = 0.0
    cost: float = 0.0
    character_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None  # Soft delete

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class AudioHistoryListResponse(BaseModel):
    """Response for listing audio history."""
    items: List[Dict[str, Any]]
    total: int
    page: int
    limit: int
    has_more: bool


# ============================================================================
# Audio History Service
# ============================================================================

class AudioHistoryService:
    """Service for managing TTS synthesis history."""

    def __init__(self):
        """Initialize audio history service with MongoDB connection."""
        # MongoDB connection
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.client = AsyncIOMotorClient(mongodb_url)
        self.db = self.client[os.getenv("MONGODB_DATABASE", "kasaai_core")]
        self.collection: AsyncIOMotorCollection = self.db["tts_audio_history"]

        logger.info("AudioHistoryService initialized")

    async def create_indexes(self):
        """Create database indexes for efficient queries."""
        try:
            # Index for user queries
            await self.collection.create_index([
                ("user_id", 1),
                ("deleted_at", 1),
                ("created_at", -1)
            ])

            # Index for text search
            await self.collection.create_index([("text", "text")])

            # Index for cleanup (TTL index for 30-day retention)
            await self.collection.create_index(
                "created_at",
                expireAfterSeconds=30 * 24 * 60 * 60  # 30 days
            )

            logger.info("Audio history indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    async def add_to_history(
        self,
        user_id: str,
        text: str,
        provider_id: str,
        audio_base64: str,
        duration_seconds: float,
        cost: float,
        voice_id: Optional[str] = None,
        language: str = "en"
    ) -> str:
        """
        Add a synthesis result to user's history.

        Args:
            user_id: User ID
            text: Text that was synthesized
            provider_id: TTS provider used
            audio_base64: Base64-encoded audio data
            duration_seconds: Audio duration
            cost: Synthesis cost
            voice_id: Voice/speaker ID used
            language: Language code

        Returns:
            str: Created history item ID
        """
        try:
            history_item = AudioHistoryItem(
                user_id=user_id,
                text=text[:200] + ("..." if len(text) > 200 else ""),  # Truncate for display
                full_text=text,  # Store complete text
                provider_id=provider_id,
                voice_id=voice_id,
                language=language,
                audio_base64=audio_base64,
                duration_seconds=duration_seconds,
                cost=cost,
                character_count=len(text)
            )

            result = await self.collection.insert_one(history_item.dict(by_alias=True))

            logger.info(
                f"Added to history: user={user_id}, provider={provider_id}, "
                f"chars={len(text)}, cost=${cost:.4f}"
            )

            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error adding to history: {e}")
            raise

    async def get_user_history(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        search_text: Optional[str] = None,
        provider_filter: Optional[str] = None
    ) -> AudioHistoryListResponse:
        """
        Get user's synthesis history with pagination and filters.

        Args:
            user_id: User ID
            page: Page number (1-indexed)
            limit: Items per page
            search_text: Optional text search
            provider_filter: Optional provider filter

        Returns:
            AudioHistoryListResponse: Paginated history items
        """
        try:
            # Build query
            query: Dict[str, Any] = {
                "user_id": user_id,
                "deleted_at": None  # Exclude soft-deleted items
            }

            if search_text:
                query["$text"] = {"$search": search_text}

            if provider_filter:
                query["provider_id"] = provider_filter

            # Count total
            total = await self.collection.count_documents(query)

            # Get paginated results
            skip = (page - 1) * limit
            cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)

            items = []
            async for doc in cursor:
                # Convert ObjectId to string
                doc["_id"] = str(doc["_id"])
                # Remove audio_base64 from list view (save bandwidth)
                doc.pop("audio_base64", None)
                items.append(doc)

            has_more = (skip + len(items)) < total

            return AudioHistoryListResponse(
                items=items,
                total=total,
                page=page,
                limit=limit,
                has_more=has_more
            )

        except Exception as e:
            logger.error(f"Error getting history: {e}")
            raise

    async def get_history_item(
        self,
        user_id: str,
        item_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific history item with full audio data.

        Args:
            user_id: User ID (for authorization)
            item_id: History item ID

        Returns:
            Optional[Dict[str, Any]]: History item or None
        """
        try:
            doc = await self.collection.find_one({
                "_id": ObjectId(item_id),
                "user_id": user_id,
                "deleted_at": None
            })

            if doc:
                doc["_id"] = str(doc["_id"])
                return doc

            return None

        except Exception as e:
            logger.error(f"Error getting history item {item_id}: {e}")
            return None

    async def delete_history_item(
        self,
        user_id: str,
        item_id: str
    ) -> bool:
        """
        Soft delete a history item.

        Args:
            user_id: User ID (for authorization)
            item_id: History item ID

        Returns:
            bool: True if deleted, False if not found
        """
        try:
            result = await self.collection.update_one(
                {
                    "_id": ObjectId(item_id),
                    "user_id": user_id,
                    "deleted_at": None
                },
                {
                    "$set": {
                        "deleted_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.modified_count > 0:
                logger.info(f"Soft deleted history item: {item_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error deleting history item {item_id}: {e}")
            return False

    async def cleanup_old_history(self, days: int = 30):
        """
        Cleanup history items older than specified days (hard delete).

        Args:
            days: Number of days to retain
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            result = await self.collection.delete_many({
                "created_at": {"$lt": cutoff_date}
            })

            logger.info(f"Cleaned up {result.deleted_count} old history items (older than {days} days)")

        except Exception as e:
            logger.error(f"Error cleaning up history: {e}")


# ============================================================================
# Global Service Instance
# ============================================================================

_audio_history_service: Optional[AudioHistoryService] = None


async def get_audio_history_service() -> AudioHistoryService:
    """Get or create audio history service singleton."""
    global _audio_history_service

    if _audio_history_service is None:
        _audio_history_service = AudioHistoryService()
        await _audio_history_service.create_indexes()

    return _audio_history_service
