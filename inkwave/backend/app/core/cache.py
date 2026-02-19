"""
Redis caching layer for InkWave.

Provides caching for hot data to reduce database load.
Supports 5000+ concurrent users with minimal database queries.
"""

import json
import logging
from typing import Optional, Any
import redis
from redis import asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis cache service for InkWave.

    Cache strategy:
    - User data: 5 min TTL (frequently accessed, rarely changes)
    - Book metadata: 30 min TTL (rarely changes, heavily accessed)
    - Leaderboard: 1 min TTL (dynamic, but can tolerate slight delay)
    - Session data: 10 min TTL (frequently updated, short-lived)
    """

    client: Optional[aioredis.Redis] = None

    @classmethod
    async def connect(cls):
        """Connect to Redis server."""
        try:
            # Use Redis with connection pooling for high concurrency
            cls.client = await aioredis.from_url(
                "redis://localhost",
                encoding="utf-8",
                decode_responses=True,
                max_connections=200,  # Connection pool size
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # Test connection
            await cls.client.ping()
            logger.info("✅ Connected to Redis cache server")

        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            # Don't raise - caching is optional, app should work without it
            cls.client = None

    @classmethod
    async def disconnect(cls):
        """Close Redis connection."""
        if cls.client is not None:
            await cls.client.close()
            logger.info("Redis connection closed")

    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or cache unavailable
        """
        if cls.client is None:
            return None

        try:
            value = await cls.client.get(key)
            if value:
                # Deserialize JSON
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None

    @classmethod
    async def set(cls, key: str, value: Any, ttl: int = 300):
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default 5 minutes)
        """
        if cls.client is None:
            return

        try:
            # Serialize to JSON
            serialized = json.dumps(value, default=str)
            await cls.client.setex(key, ttl, serialized)
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")

    @classmethod
    async def delete(cls, key: str):
        """
        Delete value from cache.

        Args:
            key: Cache key to delete
        """
        if cls.client is None:
            return

        try:
            await cls.client.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")

    @classmethod
    async def delete_pattern(cls, pattern: str):
        """
        Delete all keys matching pattern.

        Args:
            pattern: Redis key pattern (e.g., "user:*")
        """
        if cls.client is None:
            return

        try:
            # Find all keys matching pattern
            keys = []
            async for key in cls.client.scan_iter(match=pattern):
                keys.append(key)

            # Delete in batch
            if keys:
                await cls.client.delete(*keys)
                logger.info(f"Deleted {len(keys)} keys matching pattern: {pattern}")
        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")

    # Helper methods for common cache operations

    @classmethod
    async def get_user(cls, user_id: str) -> Optional[dict]:
        """Get user data from cache."""
        return await cls.get(f"user:{user_id}")

    @classmethod
    async def set_user(cls, user_id: str, user_data: dict):
        """Cache user data (5 min TTL)."""
        await cls.set(f"user:{user_id}", user_data, ttl=300)

    @classmethod
    async def invalidate_user(cls, user_id: str):
        """Invalidate user cache."""
        await cls.delete(f"user:{user_id}")

    @classmethod
    async def get_book(cls, book_id: str) -> Optional[dict]:
        """Get book metadata from cache."""
        return await cls.get(f"book:{book_id}")

    @classmethod
    async def set_book(cls, book_id: str, book_data: dict):
        """Cache book metadata (30 min TTL)."""
        await cls.set(f"book:{book_id}", book_data, ttl=1800)

    @classmethod
    async def invalidate_book(cls, book_id: str):
        """Invalidate book cache."""
        await cls.delete(f"book:{book_id}")

    @classmethod
    async def get_leaderboard(cls, period: str = "all_time") -> Optional[list]:
        """Get leaderboard from cache."""
        return await cls.get(f"leaderboard:{period}")

    @classmethod
    async def set_leaderboard(cls, period: str, leaderboard_data: list):
        """Cache leaderboard (1 min TTL)."""
        await cls.set(f"leaderboard:{period}", leaderboard_data, ttl=60)

    @classmethod
    async def invalidate_leaderboard(cls):
        """Invalidate all leaderboard caches."""
        await cls.delete_pattern("leaderboard:*")

    @classmethod
    async def get_session(cls, session_id: str) -> Optional[dict]:
        """Get session data from cache."""
        return await cls.get(f"session:{session_id}")

    @classmethod
    async def set_session(cls, session_id: str, session_data: dict):
        """Cache session data (10 min TTL)."""
        await cls.set(f"session:{session_id}", session_data, ttl=600)

    @classmethod
    async def invalidate_session(cls, session_id: str):
        """Invalidate session cache."""
        await cls.delete(f"session:{session_id}")


# Convenience function for dependency injection
async def get_cache() -> CacheService:
    """Get cache service instance."""
    return CacheService
