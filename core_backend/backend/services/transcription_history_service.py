"""
Transcription History Service

Manages ASR transcription history with MongoDB storage, soft deletes, and 30-day retention.
Similar to audio_history_service.py for TTS, but for ASR transcriptions.

Created: 2025-10-27
Phase 2: Transcription History
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

class TranscriptionHistoryItem(BaseModel):
    """ASR transcription history item."""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    audio_filename: Optional[str] = None  # Original filename if uploaded
    provider_id: str
    model_name: Optional[str] = None
    language: Optional[str] = None
    task: str = "transcribe"  # transcribe or translate
    transcript: str  # Transcribed text
    transcript_preview: str  # First 200 characters
    audio_base64: Optional[str] = None  # Store audio for replay (consider S3 for production)
    duration_seconds: float = 0.0
    processing_time: float = 0.0
    cost: float = 0.0
    word_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None  # Soft delete

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class TranscriptionHistoryListResponse(BaseModel):
    """Response for listing transcription history."""
    items: List[Dict[str, Any]]
    total: int
    page: int
    limit: int
    has_more: bool


# ============================================================================
# Transcription History Service
# ============================================================================

class TranscriptionHistoryService:
    """Service for managing ASR transcription history."""

    def __init__(self):
        """Initialize transcription history service with MongoDB connection."""
        # MongoDB connection
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.client = AsyncIOMotorClient(mongodb_url)
        self.db = self.client[os.getenv("MONGODB_DATABASE", "kasaai_core")]
        self.collection: AsyncIOMotorCollection = self.db["asr_transcription_history"]

        logger.info("TranscriptionHistoryService initialized")

    async def create_indexes(self):
        """Create database indexes for efficient queries."""
        try:
            # Compound index for user queries (most common query pattern)
            await self.collection.create_index([
                ("user_id", 1),
                ("deleted_at", 1),
                ("created_at", -1)
            ])

            # Text index for full-text search on transcripts
            await self.collection.create_index([("transcript", "text")])

            # Index for provider filtering
            await self.collection.create_index([
                ("user_id", 1),
                ("provider_id", 1),
                ("deleted_at", 1)
            ])

            # Index for language filtering
            await self.collection.create_index([
                ("user_id", 1),
                ("language", 1),
                ("deleted_at", 1)
            ])

            # TTL index for 30-day retention (auto-cleanup)
            await self.collection.create_index(
                "created_at",
                expireAfterSeconds=30 * 24 * 60 * 60  # 30 days
            )

            logger.info("Transcription history indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    async def add_to_history(
        self,
        user_id: str,
        provider_id: str,
        transcript: str,
        duration_seconds: float,
        cost: float,
        audio_filename: Optional[str] = None,
        audio_base64: Optional[str] = None,
        language: Optional[str] = None,
        model_name: Optional[str] = None,
        task: str = "transcribe",
        processing_time: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add transcription to user history.

        Args:
            user_id: User ID
            provider_id: ASR provider ID
            transcript: Transcribed text
            duration_seconds: Audio duration
            cost: Transcription cost in USD
            audio_filename: Original filename if uploaded
            audio_base64: Base64-encoded audio (optional, for replay)
            language: Detected/specified language
            model_name: Model used for transcription
            task: Task type (transcribe or translate)
            processing_time: Time taken to process
            metadata: Additional metadata

        Returns:
            str: Inserted document ID
        """
        try:
            # Create preview (first 200 characters)
            transcript_preview = transcript[:200] if len(transcript) > 200 else transcript

            # Count words
            word_count = len(transcript.split())

            # Create history item (only include optional fields if not None)
            history_item = {
                "user_id": user_id,
                "provider_id": provider_id,
                "task": task,
                "transcript": transcript,
                "transcript_preview": transcript_preview,
                "duration_seconds": duration_seconds,
                "processing_time": processing_time,
                "cost": cost,
                "word_count": word_count,
                "created_at": datetime.now(timezone.utc),
                "deleted_at": None,
                "metadata": metadata or {}
            }

            # Add optional fields only if provided (avoids None issues with text indexes)
            if audio_filename:
                history_item["audio_filename"] = audio_filename
            if model_name:
                history_item["model_name"] = model_name
            if language:
                history_item["language"] = language
            if audio_base64:
                history_item["audio_base64"] = audio_base64

            # Insert into MongoDB
            result = await self.collection.insert_one(history_item)

            logger.info(
                f"Added transcription to history: user={user_id}, provider={provider_id}, "
                f"duration={duration_seconds:.2f}s, cost=${cost:.4f}, words={word_count}"
            )

            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error adding to transcription history: {e}")
            # Don't raise - history is non-critical
            return ""

    async def get_user_history(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        search_text: Optional[str] = None,
        provider_filter: Optional[str] = None,
        language_filter: Optional[str] = None,
        task_filter: Optional[str] = None
    ) -> TranscriptionHistoryListResponse:
        """
        Get user's transcription history with pagination and filters.

        Args:
            user_id: User ID
            page: Page number (1-indexed)
            limit: Items per page
            search_text: Optional text search in transcripts
            provider_filter: Filter by provider ID
            language_filter: Filter by language
            task_filter: Filter by task type (transcribe/translate)

        Returns:
            TranscriptionHistoryListResponse: Paginated history
        """
        try:
            # Build query
            query = {
                "user_id": user_id,
                "deleted_at": None  # Exclude soft-deleted items
            }

            # Add filters
            if provider_filter:
                query["provider_id"] = provider_filter

            if language_filter:
                query["language"] = language_filter

            if task_filter:
                query["task"] = task_filter

            if search_text:
                query["$text"] = {"$search": search_text}

            # Calculate skip
            skip = (page - 1) * limit

            # Get total count
            total = await self.collection.count_documents(query)

            # Get items (sorted by created_at desc)
            cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
            items_raw = await cursor.to_list(length=limit)

            # Convert ObjectId to string and format items
            items = []
            for item in items_raw:
                item["_id"] = str(item["_id"])
                # Don't include full audio in list view (too large)
                if "audio_base64" in item:
                    item["has_audio"] = True
                    del item["audio_base64"]
                items.append(item)

            # Check if there are more pages
            has_more = (skip + len(items)) < total

            logger.info(
                f"Retrieved transcription history: user={user_id}, page={page}, "
                f"total={total}, returned={len(items)}"
            )

            return TranscriptionHistoryListResponse(
                items=items,
                total=total,
                page=page,
                limit=limit,
                has_more=has_more
            )

        except Exception as e:
            logger.error(f"Error getting transcription history: {e}")
            # Return empty response on error
            return TranscriptionHistoryListResponse(
                items=[],
                total=0,
                page=page,
                limit=limit,
                has_more=False
            )

    async def get_history_item(
        self,
        user_id: str,
        item_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get specific transcription history item with full details (including audio).

        Args:
            user_id: User ID (for security)
            item_id: History item ID

        Returns:
            Optional[Dict]: History item or None if not found
        """
        try:
            # Query with user_id for security
            query = {
                "_id": ObjectId(item_id),
                "user_id": user_id,
                "deleted_at": None
            }

            item = await self.collection.find_one(query)

            if item:
                # Convert ObjectId to string
                item["_id"] = str(item["_id"])
                logger.info(f"Retrieved transcription history item: {item_id} for user={user_id}")
                return item
            else:
                logger.warning(f"Transcription history item not found: {item_id} for user={user_id}")
                return None

        except Exception as e:
            logger.error(f"Error getting transcription history item: {e}")
            return None

    async def delete_history_item(
        self,
        user_id: str,
        item_id: str
    ) -> bool:
        """
        Soft delete transcription history item.

        Args:
            user_id: User ID (for security)
            item_id: History item ID

        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            # Update with soft delete timestamp
            result = await self.collection.update_one(
                {
                    "_id": ObjectId(item_id),
                    "user_id": user_id,
                    "deleted_at": None  # Only delete if not already deleted
                },
                {
                    "$set": {
                        "deleted_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.modified_count > 0:
                logger.info(f"Soft deleted transcription history item: {item_id} for user={user_id}")
                return True
            else:
                logger.warning(f"Failed to delete transcription history item: {item_id} for user={user_id}")
                return False

        except Exception as e:
            logger.error(f"Error deleting transcription history item: {e}")
            return False

    async def get_user_statistics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get user's transcription statistics for the last N days.

        Args:
            user_id: User ID
            days: Number of days to look back

        Returns:
            Dict: Statistics including total transcriptions, costs, duration, etc.
        """
        try:
            # Calculate date range
            start_date = datetime.now(timezone.utc) - timedelta(days=days)

            # Aggregation pipeline
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "deleted_at": None,
                        "created_at": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_transcriptions": {"$sum": 1},
                        "total_cost": {"$sum": "$cost"},
                        "total_duration": {"$sum": "$duration_seconds"},
                        "total_words": {"$sum": "$word_count"},
                        "avg_processing_time": {"$avg": "$processing_time"},
                        "providers_used": {"$addToSet": "$provider_id"}
                    }
                }
            ]

            result = await self.collection.aggregate(pipeline).to_list(length=1)

            if result:
                stats = result[0]
                stats.pop("_id", None)  # Remove group ID
                stats["period_days"] = days
                stats["providers_count"] = len(stats.get("providers_used", []))
            else:
                stats = {
                    "total_transcriptions": 0,
                    "total_cost": 0.0,
                    "total_duration": 0.0,
                    "total_words": 0,
                    "avg_processing_time": 0.0,
                    "providers_used": [],
                    "providers_count": 0,
                    "period_days": days
                }

            logger.info(f"Retrieved transcription statistics for user={user_id}, days={days}")
            return stats

        except Exception as e:
            logger.error(f"Error getting transcription statistics: {e}")
            return {
                "total_transcriptions": 0,
                "total_cost": 0.0,
                "total_duration": 0.0,
                "total_words": 0,
                "avg_processing_time": 0.0,
                "providers_used": [],
                "providers_count": 0,
                "period_days": days
            }

    async def export_user_history(
        self,
        user_id: str,
        format: str = "json",
        include_audio: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Export user's entire transcription history.

        Args:
            user_id: User ID
            format: Export format (json or csv)
            include_audio: Whether to include audio data

        Returns:
            List[Dict]: All transcriptions
        """
        try:
            # Get all non-deleted items
            query = {
                "user_id": user_id,
                "deleted_at": None
            }

            cursor = self.collection.find(query).sort("created_at", -1)
            items = await cursor.to_list(length=None)  # Get all

            # Format items
            export_items = []
            for item in items:
                item["_id"] = str(item["_id"])

                # Remove audio if not requested
                if not include_audio and "audio_base64" in item:
                    del item["audio_base64"]

                export_items.append(item)

            logger.info(f"Exported {len(export_items)} transcriptions for user={user_id}")
            return export_items

        except Exception as e:
            logger.error(f"Error exporting transcription history: {e}")
            return []


# ============================================================================
# Singleton Instance
# ============================================================================

_transcription_history_service = None


async def get_transcription_history_service() -> TranscriptionHistoryService:
    """
    Get singleton instance of TranscriptionHistoryService.

    Returns:
        TranscriptionHistoryService: Singleton service instance
    """
    global _transcription_history_service
    if _transcription_history_service is None:
        _transcription_history_service = TranscriptionHistoryService()
        # Create indexes on first initialization
        await _transcription_history_service.create_indexes()
    return _transcription_history_service
