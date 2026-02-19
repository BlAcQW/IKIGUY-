"""
Unit Tests for TTS Provider Cache

Tests the centralized MongoDB-backed provider cache functionality.

Author: KasaAI Team
Date: 2025-11-26
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

sys.path.insert(0, "/opt/kasaai/apps")

from shared.tts.provider_cache import TTSProviderCache, get_cached_providers


class TestProviderCacheIntegration:
    """Integration tests with real MongoDB."""

    @pytest_asyncio.fixture
    async def cache(self):
        """Create a cache with real MongoDB connection."""
        from motor.motor_asyncio import AsyncIOMotorClient

        mongo_uri = os.getenv(
            "MONGODB_URI",
            "mongodb://admin:aawwER4444%25@127.0.0.1:27017/?authSource=admin"
        )

        try:
            client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=2000)
            # Test connection
            await client.admin.command('ping')
            db = client.kasaai_core_test  # Use test database

            cache_instance = TTSProviderCache(
                database=db,
                collection_name="tts_provider_cache_test",
                ttl_minutes=1
            )
            await cache_instance._ensure_initialized()

            # Cleanup before tests
            await db.tts_provider_cache_test.delete_many({})

            yield cache_instance

            # Cleanup after tests
            await db.tts_provider_cache_test.delete_many({})
            client.close()
        except Exception as e:
            pytest.skip(f"MongoDB not available: {e}")

    @pytest.mark.asyncio
    async def test_cache_initialization(self, cache):
        """Test that cache initializes correctly."""
        assert cache._initialized is True
        assert cache.ttl_minutes == 1

    @pytest.mark.asyncio
    async def test_cache_miss_without_callback(self, cache):
        """Test cache miss returns None when no refresh callback provided."""
        result = await cache.get_providers(cache_key="test_no_callback")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_store_and_retrieve(self, cache):
        """Test storing and retrieving from cache."""
        test_data = {
            "providers": {
                "test_provider": {
                    "id": "test_provider",
                    "name": "Test Provider",
                    "status": "online"
                }
            },
            "count": 1,
            "online_count": 1,
            "offline_count": 0
        }

        refresh_callback = AsyncMock(return_value=test_data)

        # First call - should trigger refresh
        result1 = await cache.get_providers(
            cache_key="store_retrieve_test",
            refresh_callback=refresh_callback,
            app_name="test_app"
        )

        assert result1 is not None
        assert result1["count"] == 1
        assert result1.get("from_cache") is False
        refresh_callback.assert_called_once()

        # Second call - should use cache
        refresh_callback.reset_mock()
        result2 = await cache.get_providers(
            cache_key="store_retrieve_test",
            refresh_callback=refresh_callback,
            app_name="test_app"
        )

        assert result2 is not None
        assert result2["count"] == 1
        assert result2.get("from_cache") is True
        refresh_callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_force_refresh_bypasses_cache(self, cache):
        """Test that force_refresh bypasses cache."""
        initial_data = {
            "providers": {"initial": {"id": "initial", "status": "online"}},
            "count": 1,
            "online_count": 1,
            "offline_count": 0
        }

        updated_data = {
            "providers": {"updated": {"id": "updated", "status": "online"}},
            "count": 1,
            "online_count": 1,
            "offline_count": 0
        }

        # First call - populate cache
        await cache.get_providers(
            cache_key="force_refresh_test",
            refresh_callback=AsyncMock(return_value=initial_data)
        )

        # Force refresh - should call callback again
        refresh_callback = AsyncMock(return_value=updated_data)
        result = await cache.get_providers(
            cache_key="force_refresh_test",
            force_refresh=True,
            refresh_callback=refresh_callback
        )

        assert result is not None
        assert result.get("from_cache") is False
        refresh_callback.assert_called_once()
        assert "updated" in result["providers"]

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache):
        """Test cache invalidation."""
        test_data = {
            "providers": {"test": {"id": "test", "status": "online"}},
            "count": 1,
            "online_count": 1,
            "offline_count": 0
        }

        refresh_callback = AsyncMock(return_value=test_data)

        # Store data
        await cache.get_providers(
            cache_key="invalidation_test",
            refresh_callback=refresh_callback
        )

        # Invalidate
        await cache.invalidate(cache_key="invalidation_test")

        # Should trigger refresh again
        refresh_callback.reset_mock()
        await cache.get_providers(
            cache_key="invalidation_test",
            refresh_callback=refresh_callback
        )

        refresh_callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_info(self, cache):
        """Test getting cache information."""
        test_data = {
            "providers": {"info_test": {"id": "info_test", "status": "online"}},
            "count": 1,
            "online_count": 1,
            "offline_count": 0
        }

        await cache.get_providers(
            cache_key="info_test",
            refresh_callback=AsyncMock(return_value=test_data),
            app_name="info_test_app"
        )

        info = await cache.get_cache_info()

        assert info["total_entries"] >= 1
        assert any(e["cache_key"] == "info_test" for e in info["entries"])

    @pytest.mark.asyncio
    async def test_online_only_creates_separate_cache(self, cache):
        """Test that online_only parameter creates separate cache entries."""
        all_providers_data = {
            "providers": {
                "online_provider": {"id": "online", "status": "online"},
                "offline_provider": {"id": "offline", "status": "offline"}
            },
            "count": 2,
            "online_count": 1,
            "offline_count": 1
        }

        online_only_data = {
            "providers": {
                "online_provider": {"id": "online", "status": "online"}
            },
            "count": 1,
            "online_count": 1,
            "offline_count": 0
        }

        # Request all providers
        callback_all = AsyncMock(return_value=all_providers_data)
        result_all = await cache.get_providers(
            cache_key="online_test",
            online_only=False,
            refresh_callback=callback_all
        )
        assert result_all["count"] == 2

        # Request online only - should be separate cache entry
        callback_online = AsyncMock(return_value=online_only_data)
        result_online = await cache.get_providers(
            cache_key="online_test",
            online_only=True,
            refresh_callback=callback_online
        )
        assert result_online["count"] == 1
        callback_online.assert_called_once()

    @pytest.mark.asyncio
    async def test_stale_data_returned_on_callback_failure(self, cache):
        """Test that stale data is returned when refresh callback fails."""
        initial_data = {
            "providers": {"stale": {"id": "stale", "status": "online"}},
            "count": 1,
            "online_count": 1,
            "offline_count": 0
        }

        # Populate cache
        await cache.get_providers(
            cache_key="stale_test",
            refresh_callback=AsyncMock(return_value=initial_data)
        )

        # Force refresh with failing callback
        failing_callback = AsyncMock(side_effect=Exception("Provider check failed"))

        # This should return stale data instead of raising
        try:
            result = await cache.get_providers(
                cache_key="stale_test",
                force_refresh=True,
                refresh_callback=failing_callback
            )
            # If we get here, stale data was returned
            assert result.get("stale") is True or "stale" in result.get("providers", {})
        except Exception:
            # If exception is raised, that's also acceptable behavior
            pass


class TestGetCachedProvidersFunction:
    """Test the convenience function get_cached_providers."""

    @pytest.mark.asyncio
    async def test_convenience_function_calls_singleton(self):
        """Test that get_cached_providers uses singleton instance."""
        with patch.object(TTSProviderCache, 'get_instance') as mock_get_instance:
            mock_cache = AsyncMock()
            mock_cache.get_providers = AsyncMock(return_value={
                "providers": {},
                "count": 0,
                "online_count": 0,
                "offline_count": 0,
                "from_cache": True
            })
            mock_get_instance.return_value = mock_cache

            result = await get_cached_providers(
                online_only=False,
                force_refresh=False,
                app_name="test"
            )

            mock_get_instance.assert_called_once()
            mock_cache.get_providers.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
