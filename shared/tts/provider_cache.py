"""
TTS Provider Cache - MongoDB-backed Centralized Cache

Provides centralized caching of TTS provider health status across all applications.
This ensures that health checks are performed once globally instead of per-app,
reducing cold start times from ~10s to <50ms.

Features:
- MongoDB-backed persistence (survives app restarts)
- Shared across all apps (InkWave, StudyFlow, EventFlow, etc.)
- Configurable TTL (default 60 minutes / 1 hour)
- Automatic refresh on cache expiry
- Lock mechanism to prevent thundering herd

Usage:
    from shared.tts.provider_cache import TTSProviderCache

    cache = TTSProviderCache(database=mongo_client.kasaai_core)

    # Get providers (returns cached or refreshes if expired)
    providers = await cache.get_providers(refresh_callback=do_health_checks)

    # Force refresh
    providers = await cache.get_providers(force_refresh=True, refresh_callback=do_health_checks)

Author: KasaAI Team
Date: 2025-11-26
"""

from typing import Optional, Dict, Any, List, Callable, Awaitable
from datetime import datetime, timedelta
from pydantic import BaseModel
import asyncio
import logging
import os

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient

logger = logging.getLogger(__name__)


class CachedProviderData(BaseModel):
    """Model for cached provider data."""
    providers: Dict[str, Any]
    count: int
    online_count: int
    offline_count: int
    cached_at: datetime
    expires_at: datetime
    refreshed_by: Optional[str] = None  # App that performed the refresh


class TTSProviderCache:
    """
    MongoDB-backed centralized cache for TTS provider health status.

    This cache is shared across all applications that import from shared/.
    Only one app performs health checks when cache expires; others wait or
    use slightly stale data.

    Attributes:
        database: MongoDB database instance
        collection_name: Name of cache collection
        ttl_minutes: Cache TTL in minutes
        lock_timeout_seconds: How long to hold refresh lock
    """

    # Singleton instance for connection reuse
    _instance: Optional['TTSProviderCache'] = None
    _lock = asyncio.Lock()

    def __init__(
        self,
        database: Optional[AsyncIOMotorDatabase] = None,
        collection_name: str = "tts_provider_cache",
        ttl_minutes: int = 60,
        lock_timeout_seconds: int = 30
    ):
        """
        Initialize the provider cache.

        Args:
            database: MongoDB database instance. If None, connects using env vars.
            collection_name: Name of the cache collection
            ttl_minutes: How long cached data is valid (default 10 minutes)
            lock_timeout_seconds: Max time to hold refresh lock (default 30s)
        """
        self.database = database
        self.collection_name = collection_name
        self.ttl_minutes = ttl_minutes
        self.lock_timeout_seconds = lock_timeout_seconds
        self._collection = None
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure database connection and indexes are set up."""
        if self._initialized:
            return

        # Connect to MongoDB if not provided
        if self.database is None:
            mongo_uri = os.getenv(
                "MONGODB_URI",
                "mongodb://admin:aawwER4444%25@127.0.0.1:27017/?authSource=admin"
            )
            client = AsyncIOMotorClient(mongo_uri)
            self.database = client.kasaai_core

        self._collection = self.database[self.collection_name]

        # Create indexes
        await self._collection.create_index("cache_key", unique=True)
        await self._collection.create_index("expires_at")
        await self._collection.create_index("lock_expires_at")

        self._initialized = True
        logger.info(f"TTSProviderCache initialized: collection={self.collection_name}, ttl={self.ttl_minutes}min")

    @classmethod
    async def get_instance(cls) -> 'TTSProviderCache':
        """
        Get singleton instance of the cache.

        Returns:
            TTSProviderCache instance
        """
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance._ensure_initialized()
        return cls._instance

    async def get_providers(
        self,
        cache_key: str = "default",
        online_only: bool = False,
        force_refresh: bool = False,
        refresh_callback: Optional[Callable[[], Awaitable[Dict[str, Any]]]] = None,
        app_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached provider data, refreshing if expired.

        Args:
            cache_key: Cache key (use "default" for main provider list)
            online_only: Whether to filter for online providers only
            force_refresh: Force a cache refresh regardless of TTL
            refresh_callback: Async function to call for refreshing data
            app_name: Name of the calling app (for logging)

        Returns:
            Dict with providers, count, online_count, offline_count
            or None if cache miss and no refresh_callback provided
        """
        await self._ensure_initialized()

        full_key = f"{cache_key}_online" if online_only else cache_key
        now = datetime.utcnow()

        # Try to get cached data
        if not force_refresh:
            cached = await self._collection.find_one({"cache_key": full_key})

            if cached and cached.get("expires_at", now) > now:
                # Cache hit - return data
                logger.debug(
                    f"Provider cache HIT: key={full_key}, "
                    f"expires_in={(cached['expires_at'] - now).total_seconds():.0f}s"
                )
                return {
                    "providers": cached["providers"],
                    "count": cached["count"],
                    "online_count": cached["online_count"],
                    "offline_count": cached["offline_count"],
                    "cached_at": cached.get("cached_at"),
                    "from_cache": True
                }

        # Cache miss or force refresh - need to refresh
        if refresh_callback is None:
            logger.warning(f"Provider cache MISS and no refresh_callback: key={full_key}")
            # Return stale data if available
            stale = await self._collection.find_one({"cache_key": full_key})
            if stale:
                logger.info("Returning stale cache data")
                return {
                    "providers": stale["providers"],
                    "count": stale["count"],
                    "online_count": stale["online_count"],
                    "offline_count": stale["offline_count"],
                    "cached_at": stale.get("cached_at"),
                    "from_cache": True,
                    "stale": True
                }
            return None

        # Try to acquire refresh lock
        lock_acquired = await self._try_acquire_lock(full_key, app_name)

        if not lock_acquired:
            # Another process is refreshing - wait briefly then return stale/fresh data
            logger.info(f"Another process is refreshing cache for key={full_key}, waiting...")
            await asyncio.sleep(1)  # Brief wait

            # Try to get data again (might be fresh now)
            cached = await self._collection.find_one({"cache_key": full_key})
            if cached:
                return {
                    "providers": cached["providers"],
                    "count": cached["count"],
                    "online_count": cached["online_count"],
                    "offline_count": cached["offline_count"],
                    "cached_at": cached.get("cached_at"),
                    "from_cache": True,
                    "stale": cached.get("expires_at", now) <= now
                }
            return None

        try:
            # We have the lock - perform refresh
            logger.info(f"Provider cache REFRESH: key={full_key}, app={app_name}")

            fresh_data = await refresh_callback()

            # Store in cache
            await self._store_cache(full_key, fresh_data, app_name)

            fresh_data["from_cache"] = False
            return fresh_data

        except Exception as e:
            logger.error(f"Provider cache refresh failed: {e}")
            # Return stale data if available
            stale = await self._collection.find_one({"cache_key": full_key})
            if stale:
                return {
                    "providers": stale["providers"],
                    "count": stale["count"],
                    "online_count": stale["online_count"],
                    "offline_count": stale["offline_count"],
                    "cached_at": stale.get("cached_at"),
                    "from_cache": True,
                    "stale": True,
                    "error": str(e)
                }
            raise
        finally:
            # Release lock
            await self._release_lock(full_key)

    async def _try_acquire_lock(self, cache_key: str, app_name: Optional[str] = None) -> bool:
        """
        Try to acquire refresh lock using MongoDB atomic operation.

        Args:
            cache_key: Cache key to lock
            app_name: Name of app acquiring lock

        Returns:
            True if lock acquired, False if already locked
        """
        now = datetime.utcnow()
        lock_expires = now + timedelta(seconds=self.lock_timeout_seconds)

        # Try to set lock atomically (only if not already locked or lock expired)
        result = await self._collection.update_one(
            {
                "cache_key": f"{cache_key}_lock",
                "$or": [
                    {"lock_expires_at": {"$exists": False}},
                    {"lock_expires_at": {"$lt": now}}
                ]
            },
            {
                "$set": {
                    "cache_key": f"{cache_key}_lock",
                    "locked_by": app_name or "unknown",
                    "locked_at": now,
                    "lock_expires_at": lock_expires
                }
            },
            upsert=True
        )

        # Check if we actually set the lock (not just matched an existing one)
        if result.upserted_id or result.modified_count > 0:
            logger.debug(f"Lock acquired for key={cache_key} by {app_name}")
            return True

        # Check if lock exists and is not expired
        lock_doc = await self._collection.find_one({"cache_key": f"{cache_key}_lock"})
        if lock_doc and lock_doc.get("lock_expires_at", now) > now:
            logger.debug(f"Lock already held for key={cache_key} by {lock_doc.get('locked_by')}")
            return False

        return True

    async def _release_lock(self, cache_key: str):
        """
        Release refresh lock.

        Args:
            cache_key: Cache key to unlock
        """
        await self._collection.delete_one({"cache_key": f"{cache_key}_lock"})
        logger.debug(f"Lock released for key={cache_key}")

    async def _store_cache(
        self,
        cache_key: str,
        data: Dict[str, Any],
        refreshed_by: Optional[str] = None
    ):
        """
        Store provider data in cache.

        Args:
            cache_key: Cache key
            data: Provider data dict
            refreshed_by: Name of app that refreshed
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=self.ttl_minutes)

        cache_doc = {
            "cache_key": cache_key,
            "providers": data.get("providers", {}),
            "count": data.get("count", 0),
            "online_count": data.get("online_count", 0),
            "offline_count": data.get("offline_count", 0),
            "cached_at": now,
            "expires_at": expires_at,
            "refreshed_by": refreshed_by
        }

        await self._collection.update_one(
            {"cache_key": cache_key},
            {"$set": cache_doc},
            upsert=True
        )

        logger.info(
            f"Provider cache stored: key={cache_key}, "
            f"providers={data.get('count', 0)}, "
            f"online={data.get('online_count', 0)}, "
            f"expires_at={expires_at.isoformat()}"
        )

    async def invalidate(self, cache_key: str = "default"):
        """
        Invalidate cached data.

        Args:
            cache_key: Cache key to invalidate
        """
        await self._ensure_initialized()

        # Delete both regular and online_only variants
        await self._collection.delete_many({
            "cache_key": {"$in": [cache_key, f"{cache_key}_online"]}
        })

        logger.info(f"Provider cache invalidated: key={cache_key}")

    async def get_cache_info(self) -> Dict[str, Any]:
        """
        Get cache statistics and info.

        Returns:
            Dict with cache stats
        """
        await self._ensure_initialized()

        now = datetime.utcnow()

        # Get all cache entries
        entries = await self._collection.find({
            "cache_key": {"$not": {"$regex": "_lock$"}}
        }).to_list(length=100)

        info = {
            "total_entries": len(entries),
            "entries": []
        }

        for entry in entries:
            expires_at = entry.get("expires_at", now)
            info["entries"].append({
                "cache_key": entry["cache_key"],
                "provider_count": entry.get("count", 0),
                "online_count": entry.get("online_count", 0),
                "offline_count": entry.get("offline_count", 0),
                "cached_at": entry.get("cached_at"),
                "expires_at": expires_at,
                "is_expired": expires_at <= now,
                "expires_in_seconds": max(0, (expires_at - now).total_seconds()),
                "refreshed_by": entry.get("refreshed_by")
            })

        return info


    async def store_health_results(
        self,
        providers_data: Dict[str, Any],
        refreshed_by: str = "health_monitor"
    ) -> None:
        """
        Directly store health check results in cache.

        Called by HealthMonitorService after completing health checks
        to keep the cache warm proactively.

        Args:
            providers_data: Dict with providers, count, online_count, offline_count
            refreshed_by: Name of service that performed the refresh
        """
        await self._ensure_initialized()

        # Store for both default and online_only cache keys
        await self._store_cache("default", providers_data, refreshed_by)

        # Also store online_only variant
        online_providers = {
            k: v for k, v in providers_data.get("providers", {}).items()
            if v.get("status") == "online"
        }
        online_data = {
            "providers": online_providers,
            "count": len(online_providers),
            "online_count": len(online_providers),
            "offline_count": 0
        }
        await self._store_cache("default_online", online_data, refreshed_by)

        logger.info(
            f"Provider cache warmed by {refreshed_by}: "
            f"{providers_data.get('count', 0)} providers, "
            f"{providers_data.get('online_count', 0)} online"
        )


class BackgroundCacheWarmer:
    """
    Background service to keep provider cache warm.

    Can run independently or be triggered by HealthMonitorService.
    Ensures cache is always fresh so user requests never wait.
    """

    def __init__(
        self,
        refresh_callback: Callable[[], Awaitable[Dict[str, Any]]],
        interval_minutes: int = 5,
        app_name: str = "background_warmer"
    ):
        """
        Initialize background cache warmer.

        Args:
            refresh_callback: Async function that performs health checks
            interval_minutes: Minutes between cache refreshes
            app_name: Name for logging
        """
        self.refresh_callback = refresh_callback
        self.interval_minutes = interval_minutes
        self.app_name = app_name
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start background cache warming."""
        if self._running:
            logger.warning("Cache warmer already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._warm_loop())
        logger.info(
            f"Started background cache warmer (interval: {self.interval_minutes}m)"
        )

    async def stop(self) -> None:
        """Stop background cache warming."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("Stopped background cache warmer")

    async def _warm_loop(self) -> None:
        """Background loop that periodically warms the cache."""
        # Wait 10 seconds before first warm to let startup complete
        # This avoids network congestion and ensures providers respond
        await asyncio.sleep(10)

        # Initial warm on startup
        await self._warm_cache()

        while self._running:
            try:
                await asyncio.sleep(self.interval_minutes * 60)
                await self._warm_cache()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache warmer error: {e}")
                # Continue running even on error
                await asyncio.sleep(60)  # Wait 1 minute before retry

    async def _warm_cache(self) -> None:
        """Perform a single cache warm operation."""
        try:
            logger.info(f"Cache warmer: Refreshing provider cache...")
            start = datetime.utcnow()

            # Get fresh provider data
            data = await self.refresh_callback()

            # Store in centralized cache
            cache = await TTSProviderCache.get_instance()
            await cache.store_health_results(data, self.app_name)

            elapsed = (datetime.utcnow() - start).total_seconds()
            logger.info(
                f"Cache warmer: Refreshed {data.get('count', 0)} providers "
                f"({data.get('online_count', 0)} online) in {elapsed:.2f}s"
            )

        except Exception as e:
            logger.error(f"Cache warmer: Failed to warm cache: {e}")

    async def warm_now(self) -> Dict[str, Any]:
        """
        Manually trigger a cache warm.

        Returns:
            Provider data that was cached
        """
        await self._warm_cache()
        cache = await TTSProviderCache.get_instance()
        return await cache.get_providers(cache_key="default")


# Convenience function for quick access
async def get_cached_providers(
    online_only: bool = False,
    force_refresh: bool = False,
    refresh_callback: Optional[Callable[[], Awaitable[Dict[str, Any]]]] = None,
    app_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get cached providers using singleton instance.

    Args:
        online_only: Filter for online providers only
        force_refresh: Force cache refresh
        refresh_callback: Async function to refresh data
        app_name: Name of calling app

    Returns:
        Provider data dict or None
    """
    cache = await TTSProviderCache.get_instance()
    return await cache.get_providers(
        online_only=online_only,
        force_refresh=force_refresh,
        refresh_callback=refresh_callback,
        app_name=app_name
    )


async def warm_provider_cache(
    providers_data: Dict[str, Any],
    refreshed_by: str = "health_monitor"
) -> None:
    """
    Convenience function to warm the cache with health check results.

    Called by HealthMonitorService after completing health checks.

    Args:
        providers_data: Dict with providers, count, online_count, offline_count
        refreshed_by: Name of service that performed refresh
    """
    cache = await TTSProviderCache.get_instance()
    await cache.store_health_results(providers_data, refreshed_by)
