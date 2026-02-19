"""
Registration Cache Service for ChurchFlow

Provides Redis caching for expensive operations:
- Stats aggregation (total, confirmed, checked_in, requires_bus)
- Search results with pagination

Cache keys format:
- stats: registration:stats:{conference_id}:{filters_hash}
- search: registration:search:{conference_id}:{search_query}:{filters_hash}:{offset}:{limit}
"""

import json
import hashlib
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)


class RegistrationCache:
    """Redis cache for registration queries"""

    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client: Optional[redis.Redis] = None
        self.enabled = False
        self._prefix = "churchflow:registration"

    async def connect(self):
        """Connect to Redis server"""
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            redis_password = os.getenv("REDIS_PASSWORD")

            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=0,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=True
            )

            # Test connection
            await self.redis_client.ping()
            self.enabled = True
            logger.info("✅ Redis cache connected successfully")

        except Exception as e:
            logger.warning(f"⚠️  Redis cache unavailable: {e}. Proceeding without cache.")
            self.enabled = False

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("Redis cache disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting from Redis: {e}")

    def _hash_filters(self, filters: Dict[str, Any]) -> str:
        """
        Create a hash of filter parameters for cache key.

        Args:
            filters: Dictionary of filter parameters

        Returns:
            str: MD5 hash of sorted filter parameters
        """
        # Sort and serialize filters for consistent hashing
        filter_str = json.dumps(filters, sort_keys=True)
        return hashlib.md5(filter_str.encode()).hexdigest()[:8]

    async def get_stats(
        self,
        conference_id: Optional[str],
        status: Optional[str],
        checked_in: Optional[bool]
    ) -> Optional[Dict[str, int]]:
        """
        Get cached stats.

        Args:
            conference_id: Conference filter
            status: Status filter
            checked_in: Checked-in filter

        Returns:
            Optional[Dict]: Cached stats or None if not found
        """
        if not self.enabled:
            return None

        try:
            # Build cache key
            filters = {
                "conference_id": conference_id or "all",
                "status": status or "all",
                "checked_in": str(checked_in) if checked_in is not None else "all"
            }
            filters_hash = self._hash_filters(filters)
            cache_key = f"{self._prefix}:stats:{filters_hash}"

            # Get from cache
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                logger.debug(f"📦 Cache HIT: stats {filters_hash}")
                return json.loads(cached_data)

            logger.debug(f"📭 Cache MISS: stats {filters_hash}")
            return None

        except Exception as e:
            logger.error(f"Error getting stats from cache: {e}")
            return None

    async def set_stats(
        self,
        conference_id: Optional[str],
        status: Optional[str],
        checked_in: Optional[bool],
        stats: Dict[str, int],
        ttl: int = 45
    ) -> bool:
        """
        Cache stats with TTL.

        Args:
            conference_id: Conference filter
            status: Status filter
            checked_in: Checked-in filter
            stats: Stats data to cache
            ttl: Time to live in seconds (default: 45s)

        Returns:
            bool: True if cached successfully
        """
        if not self.enabled:
            return False

        try:
            # Build cache key
            filters = {
                "conference_id": conference_id or "all",
                "status": status or "all",
                "checked_in": str(checked_in) if checked_in is not None else "all"
            }
            filters_hash = self._hash_filters(filters)
            cache_key = f"{self._prefix}:stats:{filters_hash}"

            # Cache with TTL
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(stats)
            )
            logger.debug(f"💾 Cached stats {filters_hash} for {ttl}s")
            return True

        except Exception as e:
            logger.error(f"Error caching stats: {e}")
            return False

    async def get_search_results(
        self,
        conference_id: Optional[str],
        search: Optional[str],
        status: Optional[str],
        checked_in: Optional[bool],
        offset: int,
        limit: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached search results.

        Args:
            conference_id: Conference filter
            search: Search query
            status: Status filter
            checked_in: Checked-in filter
            offset: Pagination offset
            limit: Pagination limit

        Returns:
            Optional[Dict]: Cached results or None if not found
        """
        if not self.enabled or not search:
            return None

        try:
            # Build cache key
            filters = {
                "conference_id": conference_id or "all",
                "search": search,
                "status": status or "all",
                "checked_in": str(checked_in) if checked_in is not None else "all",
                "offset": offset,
                "limit": limit
            }
            filters_hash = self._hash_filters(filters)
            cache_key = f"{self._prefix}:search:{filters_hash}"

            # Get from cache
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                logger.debug(f"📦 Cache HIT: search {filters_hash}")
                return json.loads(cached_data)

            logger.debug(f"📭 Cache MISS: search {filters_hash}")
            return None

        except Exception as e:
            logger.error(f"Error getting search results from cache: {e}")
            return None

    async def set_search_results(
        self,
        conference_id: Optional[str],
        search: Optional[str],
        status: Optional[str],
        checked_in: Optional[bool],
        offset: int,
        limit: int,
        results: Dict[str, Any],
        ttl: int = 20
    ) -> bool:
        """
        Cache search results with TTL.

        Args:
            conference_id: Conference filter
            search: Search query
            status: Status filter
            checked_in: Checked-in filter
            offset: Pagination offset
            limit: Pagination limit
            results: Search results to cache
            ttl: Time to live in seconds (default: 20s)

        Returns:
            bool: True if cached successfully
        """
        if not self.enabled or not search:
            return False

        try:
            # Build cache key
            filters = {
                "conference_id": conference_id or "all",
                "search": search,
                "status": status or "all",
                "checked_in": str(checked_in) if checked_in is not None else "all",
                "offset": offset,
                "limit": limit
            }
            filters_hash = self._hash_filters(filters)
            cache_key = f"{self._prefix}:search:{filters_hash}"

            # Cache with TTL
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(results)
            )
            logger.debug(f"💾 Cached search {filters_hash} for {ttl}s")
            return True

        except Exception as e:
            logger.error(f"Error caching search results: {e}")
            return False

    async def invalidate_all(self):
        """
        Invalidate all registration caches.

        Called when registrations are created, updated, or deleted.
        """
        if not self.enabled:
            return

        try:
            # Delete all cache keys with registration prefix
            pattern = f"{self._prefix}:*"
            keys = []

            # Scan for keys matching pattern
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"🗑️  Invalidated {len(keys)} registration cache entries")

        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")

    async def invalidate_conference(self, conference_id: str):
        """
        Invalidate caches for a specific conference.

        Args:
            conference_id: Conference ID to invalidate
        """
        if not self.enabled:
            return

        try:
            # Delete all cache keys containing this conference ID
            pattern = f"{self._prefix}:*{conference_id}*"
            keys = []

            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"🗑️  Invalidated {len(keys)} cache entries for conference {conference_id}")

        except Exception as e:
            logger.error(f"Error invalidating conference cache: {e}")


# Global cache instance
_cache_instance: Optional[RegistrationCache] = None


async def get_cache() -> RegistrationCache:
    """
    Get or create global cache instance.

    Returns:
        RegistrationCache: Global cache instance
    """
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = RegistrationCache()
        await _cache_instance.connect()

    return _cache_instance
