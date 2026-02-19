"""
TTS Audio Cache

Provides caching for TTS audio to reduce costs and improve response times.
Uses MongoDB GridFS for audio storage with 24-hour TTL.

Expected cost reduction: 40%

Usage:
    from apps.shared.tts.cache import TTSAudioCache
    from motor.motor_asyncio import AsyncIOMotorClient

    client = AsyncIOMotorClient("mongodb://localhost:27017")
    cache = TTSAudioCache(database=client.tts_cache)

    # Generate cache key
    cache_key = cache.generate_key(text="Hello", provider="coqui_xtts", voice="default", language="en")

    # Try to get from cache
    audio = await cache.get(cache_key)
    if audio is None:
        # Cache miss - synthesize and cache
        audio = await synthesize_audio(...)
        await cache.set(cache_key, audio, ttl_hours=24)

Author: KasaAI Team
Date: 2025-11-23
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorGridFSBucket
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CacheStats(BaseModel):
    """Cache statistics."""
    total_entries: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    total_size_mb: float
    avg_audio_size_kb: float
    oldest_entry: Optional[datetime] = None
    newest_entry: Optional[datetime] = None


class TTSAudioCache:
    """
    MongoDB GridFS-based cache for TTS audio.

    Features:
    - SHA256 key generation from (text + provider + voice + language)
    - 24-hour TTL with automatic cleanup
    - Cache hit/miss metrics tracking
    - GridFS storage for large audio files
    """

    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        collection_name: str = "tts_audio_cache",
        default_ttl_hours: int = 24,
        enable_metrics: bool = True
    ):
        """
        Initialize TTS audio cache.

        Args:
            database: Motor AsyncIO MongoDB database instance
            collection_name: Name of GridFS collection for audio storage
            default_ttl_hours: Default TTL in hours (default: 24)
            enable_metrics: Whether to track cache hit/miss metrics
        """
        self.database = database
        self.collection_name = collection_name
        self.default_ttl_hours = default_ttl_hours
        self.enable_metrics = enable_metrics

        # GridFS bucket for audio storage
        self.fs_bucket = AsyncIOMotorGridFSBucket(database, bucket_name=collection_name)

        # Metadata collection (tracks cache entries with TTL)
        self.metadata_collection = database[f"{collection_name}_metadata"]

        # Metrics collection
        if enable_metrics:
            self.metrics_collection = database[f"{collection_name}_metrics"]

        logger.info(
            f"TTSAudioCache initialized: collection={collection_name}, "
            f"ttl={default_ttl_hours}h, metrics={enable_metrics}"
        )

    async def ensure_indexes(self):
        """
        Create indexes for cache metadata and metrics.

        Should be called once at application startup.
        """
        # TTL index on expires_at field (auto-delete expired entries)
        await self.metadata_collection.create_index(
            "expires_at",
            expireAfterSeconds=0,
            name="ttl_index"
        )

        # Index on cache_key for fast lookups
        await self.metadata_collection.create_index(
            "cache_key",
            unique=True,
            name="cache_key_index"
        )

        # Index on created_at for stats queries
        await self.metadata_collection.create_index(
            "created_at",
            name="created_at_index"
        )

        logger.info("Cache indexes created successfully")

    def generate_key(
        self,
        text: str,
        provider: str,
        voice: str,
        language: str,
        speed: float = 1.0,
        **kwargs
    ) -> str:
        """
        Generate cache key from synthesis parameters.

        Args:
            text: Text to synthesize
            provider: TTS provider ID
            voice: Voice/speaker ID
            language: Language code
            speed: Speech speed
            **kwargs: Additional parameters (pitch, emotion, etc.)

        Returns:
            SHA256 hash as cache key
        """
        # Normalize parameters
        text_normalized = text.strip().lower()
        provider_normalized = provider.lower()
        voice_normalized = voice.lower()
        language_normalized = language.lower()

        # Include optional parameters if provided
        optional_params = sorted(kwargs.items())
        optional_str = ":".join(f"{k}={v}" for k, v in optional_params)

        # Create key string
        key_string = (
            f"{text_normalized}:{provider_normalized}:"
            f"{voice_normalized}:{language_normalized}:"
            f"{speed}:{optional_str}"
        )

        # Generate SHA256 hash
        cache_key = hashlib.sha256(key_string.encode('utf-8')).hexdigest()

        logger.debug(f"Generated cache key: {cache_key[:16]}... for provider={provider}, voice={voice}")

        return cache_key

    async def get(self, cache_key: str) -> Optional[bytes]:
        """
        Retrieve audio from cache.

        Args:
            cache_key: Cache key generated from synthesis parameters

        Returns:
            Audio bytes if found and not expired, None otherwise
        """
        try:
            # Check metadata
            metadata = await self.metadata_collection.find_one({"cache_key": cache_key})

            if not metadata:
                logger.debug(f"Cache MISS: {cache_key[:16]}... (not found)")
                await self._record_metric("cache_miss")
                return None

            # Check expiration
            if datetime.utcnow() > metadata["expires_at"]:
                logger.debug(f"Cache MISS: {cache_key[:16]}... (expired)")
                await self._record_metric("cache_miss")
                # TTL index will automatically delete this entry
                return None

            # Retrieve audio from GridFS
            grid_out = await self.fs_bucket.open_download_stream(metadata["file_id"])
            audio_data = await grid_out.read()

            # Update access time
            await self.metadata_collection.update_one(
                {"cache_key": cache_key},
                {"$set": {"last_accessed_at": datetime.utcnow()}}
            )

            logger.debug(
                f"Cache HIT: {cache_key[:16]}... "
                f"(size={len(audio_data)/1024:.1f}KB, "
                f"created={metadata['created_at'].isoformat()})"
            )

            await self._record_metric("cache_hit")

            return audio_data

        except Exception as e:
            logger.error(f"Cache retrieval error for key {cache_key[:16]}...: {str(e)}")
            await self._record_metric("cache_miss")
            return None

    async def set(
        self,
        cache_key: str,
        audio_data: bytes,
        ttl_hours: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store audio in cache.

        Args:
            cache_key: Cache key generated from synthesis parameters
            audio_data: Audio bytes to cache
            ttl_hours: TTL in hours (uses default if not provided)
            metadata: Additional metadata to store
        """
        try:
            ttl = ttl_hours or self.default_ttl_hours
            expires_at = datetime.utcnow() + timedelta(hours=ttl)

            # Check if entry already exists
            existing = await self.metadata_collection.find_one({"cache_key": cache_key})

            if existing:
                # Delete old audio file from GridFS
                try:
                    await self.fs_bucket.delete(existing["file_id"])
                except Exception as delete_error:
                    logger.warning(f"Failed to delete old audio file: {str(delete_error)}")

            # Upload audio to GridFS
            file_id = await self.fs_bucket.upload_from_stream(
                filename=f"tts_{cache_key[:16]}.audio",
                source=audio_data,
                metadata={
                    "cache_key": cache_key,
                    "size_bytes": len(audio_data),
                    "created_at": datetime.utcnow()
                }
            )

            # Store metadata with TTL
            cache_metadata = {
                "cache_key": cache_key,
                "file_id": file_id,
                "audio_size_bytes": len(audio_data),
                "ttl_hours": ttl,
                "expires_at": expires_at,
                "created_at": datetime.utcnow(),
                "last_accessed_at": datetime.utcnow(),
                **(metadata or {})
            }

            # Upsert metadata
            await self.metadata_collection.update_one(
                {"cache_key": cache_key},
                {"$set": cache_metadata},
                upsert=True
            )

            logger.debug(
                f"Cache SET: {cache_key[:16]}... "
                f"(size={len(audio_data)/1024:.1f}KB, ttl={ttl}h)"
            )

            await self._record_metric("cache_set")

        except Exception as e:
            logger.error(f"Cache storage error for key {cache_key[:16]}...: {str(e)}")
            # Don't raise - caching is optional

    async def invalidate(self, cache_key: str) -> bool:
        """
        Invalidate (delete) cache entry.

        Args:
            cache_key: Cache key to invalidate

        Returns:
            True if entry was deleted, False if not found
        """
        try:
            # Get metadata
            metadata = await self.metadata_collection.find_one({"cache_key": cache_key})

            if not metadata:
                logger.debug(f"Cache invalidate: {cache_key[:16]}... not found")
                return False

            # Delete audio from GridFS
            await self.fs_bucket.delete(metadata["file_id"])

            # Delete metadata
            await self.metadata_collection.delete_one({"cache_key": cache_key})

            logger.info(f"Cache invalidated: {cache_key[:16]}...")
            return True

        except Exception as e:
            logger.error(f"Cache invalidation error for key {cache_key[:16]}...: {str(e)}")
            return False

    async def clear_all(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries deleted
        """
        try:
            # Count entries before deletion
            count = await self.metadata_collection.count_documents({})

            # Delete all audio files from GridFS
            async for metadata in self.metadata_collection.find({}):
                try:
                    await self.fs_bucket.delete(metadata["file_id"])
                except Exception as delete_error:
                    logger.warning(f"Failed to delete audio file: {str(delete_error)}")

            # Delete all metadata
            await self.metadata_collection.delete_many({})

            logger.info(f"Cache cleared: {count} entries deleted")
            return count

        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return 0

    async def get_stats(self) -> CacheStats:
        """
        Get cache statistics.

        Returns:
            CacheStats with hit rate, size, and other metrics
        """
        try:
            # Count total entries
            total_entries = await self.metadata_collection.count_documents({})

            # Calculate total size
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_size": {"$sum": "$audio_size_bytes"},
                        "avg_size": {"$avg": "$audio_size_bytes"},
                        "oldest": {"$min": "$created_at"},
                        "newest": {"$max": "$created_at"}
                    }
                }
            ]

            size_stats = await self.metadata_collection.aggregate(pipeline).to_list(length=1)

            total_size_bytes = size_stats[0]["total_size"] if size_stats else 0
            avg_size_bytes = size_stats[0]["avg_size"] if size_stats else 0
            oldest_entry = size_stats[0]["oldest"] if size_stats else None
            newest_entry = size_stats[0]["newest"] if size_stats else None

            # Get metrics
            cache_hits = 0
            cache_misses = 0

            if self.enable_metrics:
                # Sum metrics from last 24 hours
                since = datetime.utcnow() - timedelta(hours=24)

                hit_docs = await self.metrics_collection.find(
                    {"metric_type": "cache_hit", "timestamp": {"$gte": since}}
                ).to_list(length=None)
                cache_hits = len(hit_docs)

                miss_docs = await self.metrics_collection.find(
                    {"metric_type": "cache_miss", "timestamp": {"$gte": since}}
                ).to_list(length=None)
                cache_misses = len(miss_docs)

            # Calculate hit rate
            total_requests = cache_hits + cache_misses
            hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0.0

            return CacheStats(
                total_entries=total_entries,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                hit_rate=hit_rate,
                total_size_mb=total_size_bytes / (1024 * 1024),
                avg_audio_size_kb=avg_size_bytes / 1024,
                oldest_entry=oldest_entry,
                newest_entry=newest_entry
            )

        except Exception as e:
            logger.error(f"Stats calculation error: {str(e)}")
            return CacheStats(
                total_entries=0,
                cache_hits=0,
                cache_misses=0,
                hit_rate=0.0,
                total_size_mb=0.0,
                avg_audio_size_kb=0.0
            )

    async def cleanup_expired(self) -> int:
        """
        Manually cleanup expired entries.

        Note: TTL index handles this automatically, but this method
        can be used for manual cleanup or testing.

        Returns:
            Number of entries deleted
        """
        try:
            # Find expired entries
            expired_cursor = self.metadata_collection.find({
                "expires_at": {"$lt": datetime.utcnow()}
            })

            count = 0
            async for metadata in expired_cursor:
                try:
                    # Delete audio from GridFS
                    await self.fs_bucket.delete(metadata["file_id"])

                    # Delete metadata
                    await self.metadata_collection.delete_one({"_id": metadata["_id"]})

                    count += 1

                except Exception as delete_error:
                    logger.warning(f"Failed to delete expired entry: {str(delete_error)}")

            if count > 0:
                logger.info(f"Cleaned up {count} expired cache entries")

            return count

        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")
            return 0

    async def _record_metric(self, metric_type: str):
        """
        Record cache metric (hit/miss/set).

        Args:
            metric_type: Type of metric (cache_hit, cache_miss, cache_set)
        """
        if not self.enable_metrics:
            return

        try:
            await self.metrics_collection.insert_one({
                "metric_type": metric_type,
                "timestamp": datetime.utcnow()
            })
        except Exception as e:
            logger.warning(f"Failed to record metric {metric_type}: {str(e)}")
