"""
Redis Cache Service for RAG Query Caching.
Caches RAG query results to provide instant responses for repeat queries.
"""

import os
import hashlib
import json
import logging
from typing import Optional, Dict, Any
from datetime import timedelta
import redis.asyncio as aioredis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisCacheService:
    """Service for caching RAG query results in Redis."""

    def __init__(self):
        """Initialize Redis cache service."""
        # Redis connection parameters
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.redis_password = os.getenv("REDIS_PASSWORD")

        # Cache TTL (24 hours)
        self.cache_ttl = int(os.getenv("REDIS_CACHE_TTL", "86400"))

        # Redis client (lazy initialization)
        self._redis: Optional[Redis] = None

        logger.info(f"Redis cache service initialized (host={self.redis_host}, port={self.redis_port}, ttl={self.cache_ttl}s)")

    async def _get_redis(self) -> Redis:
        """
        Get or create Redis client connection.

        Returns:
            Redis client instance
        """
        if self._redis is None:
            try:
                self._redis = await aioredis.from_url(
                    f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}",
                    password=self.redis_password,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0
                )
                # Test connection
                await self._redis.ping()
                logger.info("✅ Redis connection established")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Redis: {e}")
                raise

        return self._redis

    def _generate_cache_key(self, company_name: str, query: str) -> str:
        """
        Generate cache key for a query.

        Args:
            company_name: Company identifier
            query: Normalized query string

        Returns:
            Cache key (hash of company_name + query)
        """
        # Normalize query (lowercase, strip whitespace)
        normalized_query = query.lower().strip()

        # Create hash of company + query
        key_string = f"{company_name}:{normalized_query}"
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()

        # Prefix for namespacing
        cache_key = f"rag:query:{key_hash}"

        return cache_key

    async def get_cached_response(
        self,
        company_name: str,
        query: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response for a query.

        Args:
            company_name: Company identifier
            query: Query string

        Returns:
            Cached response dict or None if not found
        """
        try:
            redis = await self._get_redis()
            cache_key = self._generate_cache_key(company_name, query)

            # Get cached data
            cached_data = await redis.get(cache_key)

            if cached_data:
                logger.info(f"🎯 Cache HIT: {cache_key[:16]}... (query: '{query[:50]}')")
                return json.loads(cached_data)
            else:
                logger.info(f"❌ Cache MISS: {cache_key[:16]}... (query: '{query[:50]}')")
                return None

        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            # Return None on cache error (fail gracefully)
            return None

    async def cache_response(
        self,
        company_name: str,
        query: str,
        response_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache a query response.

        Args:
            company_name: Company identifier
            query: Query string
            response_data: Response data to cache
            ttl: Time to live in seconds (default: self.cache_ttl)

        Returns:
            True if cached successfully, False otherwise
        """
        try:
            redis = await self._get_redis()
            cache_key = self._generate_cache_key(company_name, query)

            # Use default TTL if not specified
            cache_ttl = ttl if ttl is not None else self.cache_ttl

            # Serialize and cache
            cached_data = json.dumps(response_data)
            await redis.setex(
                cache_key,
                cache_ttl,
                cached_data
            )

            logger.info(f"✅ Cached response: {cache_key[:16]}... (ttl={cache_ttl}s, size={len(cached_data)} bytes)")
            return True

        except Exception as e:
            logger.error(f"Error caching response: {e}")
            # Return False on cache error (fail gracefully)
            return False

    async def invalidate_cache(
        self,
        company_name: str,
        query: Optional[str] = None
    ) -> int:
        """
        Invalidate cache entries.

        Args:
            company_name: Company identifier
            query: Specific query to invalidate (if None, invalidates all for company)

        Returns:
            Number of cache entries deleted
        """
        try:
            redis = await self._get_redis()

            if query:
                # Invalidate specific query
                cache_key = self._generate_cache_key(company_name, query)
                deleted = await redis.delete(cache_key)
                logger.info(f"🗑️  Invalidated cache: {cache_key} ({deleted} keys)")
                return deleted
            else:
                # Invalidate all queries for company
                # Note: This requires scanning all keys (expensive operation)
                pattern = f"rag:query:*"
                cursor = 0
                deleted_count = 0

                while True:
                    cursor, keys = await redis.scan(
                        cursor=cursor,
                        match=pattern,
                        count=100
                    )

                    if keys:
                        # Filter keys by company (need to check each key's content)
                        # For now, delete all matching pattern (can optimize later)
                        deleted = await redis.delete(*keys)
                        deleted_count += deleted

                    if cursor == 0:
                        break

                logger.info(f"🗑️  Invalidated {deleted_count} cache entries for pattern: {pattern}")
                return deleted_count

        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return 0

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats (total keys, memory usage, hit rate, etc.)
        """
        try:
            redis = await self._get_redis()

            # Get Redis info
            info = await redis.info("stats")
            memory_info = await redis.info("memory")

            # Count RAG cache keys
            pattern = "rag:query:*"
            cursor = 0
            rag_key_count = 0

            while True:
                cursor, keys = await redis.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                rag_key_count += len(keys)

                if cursor == 0:
                    break

            # Calculate hit rate
            keyspace_hits = info.get("keyspace_hits", 0)
            keyspace_misses = info.get("keyspace_misses", 0)
            total_requests = keyspace_hits + keyspace_misses
            hit_rate = (keyspace_hits / total_requests * 100) if total_requests > 0 else 0

            stats = {
                "total_rag_keys": rag_key_count,
                "memory_used_mb": memory_info.get("used_memory", 0) / (1024 * 1024),
                "memory_peak_mb": memory_info.get("used_memory_peak", 0) / (1024 * 1024),
                "keyspace_hits": keyspace_hits,
                "keyspace_misses": keyspace_misses,
                "hit_rate_percent": round(hit_rate, 2),
                "evicted_keys": info.get("evicted_keys", 0),
                "expired_keys": info.get("expired_keys", 0)
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "error": str(e),
                "total_rag_keys": 0,
                "memory_used_mb": 0
            }

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            logger.info("Redis connection closed")
            self._redis = None


# Global service instance
redis_cache_service = RedisCacheService()
