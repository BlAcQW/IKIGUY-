"""
Unit tests for Ghanaian offline processor

Tests offline processing capabilities, caching, and fallback mechanisms.
"""

import asyncio
import json
import pickle
import sqlite3
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.shared.ai.ghanaian_offline_processor import (
    CacheConfig,
    CacheEntry,
    OfflineModelConfig,
    OfflineProcessor,
    ProcessingMode,
    CacheStrategy
)


class TestCacheConfig:
    """Test cache configuration"""
    
    def test_default_config(self):
        """Test default cache configuration"""
        config = CacheConfig()
        
        assert config.max_memory_size == 100 * 1024 * 1024  # 100MB
        assert config.max_disk_size == 1024 * 1024 * 1024  # 1GB
        assert config.ttl_hours == 24
        assert config.cleanup_interval_hours == 6
        assert config.compression_enabled is True
        assert config.encryption_enabled is False
    
    def test_custom_config(self):
        """Test custom cache configuration"""
        config = CacheConfig(
            max_memory_size=50 * 1024 * 1024,
            max_disk_size=500 * 1024 * 1024,
            ttl_hours=12,
            cleanup_interval_hours=3,
            compression_enabled=False,
            encryption_enabled=True
        )
        
        assert config.max_memory_size == 50 * 1024 * 1024
        assert config.max_disk_size == 500 * 1024 * 1024
        assert config.ttl_hours == 12
        assert config.cleanup_interval_hours == 3
        assert config.compression_enabled is False
        assert config.encryption_enabled is True


class TestOfflineModelConfig:
    """Test offline model configuration"""
    
    def test_default_config(self):
        """Test default offline model configuration"""
        config = OfflineModelConfig(
            model_path="/path/to/model",
            model_type="sentiment",
            language="tw",
            version="1.0.0"
        )
        
        assert config.model_path == "/path/to/model"
        assert config.model_type == "sentiment"
        assert config.language == "tw"
        assert config.version == "1.0.0"
        assert config.accuracy_threshold == 0.7
        assert config.max_input_length == 512
        assert config.batch_size == 32
    
    def test_custom_config(self):
        """Test custom offline model configuration"""
        config = OfflineModelConfig(
            model_path="/custom/path",
            model_type="ner",
            language="en-GH",
            version="2.0.0",
            accuracy_threshold=0.8,
            max_input_length=1024,
            batch_size=64
        )
        
        assert config.model_path == "/custom/path"
        assert config.model_type == "ner"
        assert config.language == "en-GH"
        assert config.version == "2.0.0"
        assert config.accuracy_threshold == 0.8
        assert config.max_input_length == 1024
        assert config.batch_size == 64


class TestCacheEntry:
    """Test cache entry model"""
    
    def test_default_entry(self):
        """Test default cache entry"""
        entry = CacheEntry(
            key="test_key",
            data={"test": "data"},
            timestamp=datetime.utcnow()
        )
        
        assert entry.key == "test_key"
        assert entry.data == {"test": "data"}
        assert entry.ttl == 86400  # 24 hours
        assert entry.size == 0
        assert entry.access_count == 0
    
    def test_custom_entry(self):
        """Test custom cache entry"""
        timestamp = datetime.utcnow()
        entry = CacheEntry(
            key="custom_key",
            data={"custom": "data"},
            timestamp=timestamp,
            ttl=3600,  # 1 hour
            size=1024,
            access_count=5
        )
        
        assert entry.key == "custom_key"
        assert entry.data == {"custom": "data"}
        assert entry.timestamp == timestamp
        assert entry.ttl == 3600
        assert entry.size == 1024
        assert entry.access_count == 5


class TestOfflineProcessor:
    """Test offline processor functionality"""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def cache_config(self):
        """Create cache configuration"""
        return CacheConfig(
            max_memory_size=1024 * 1024,  # 1MB
            max_disk_size=10 * 1024 * 1024,  # 10MB
            ttl_hours=1,
            cleanup_interval_hours=1
        )
    
    @pytest.fixture
    async def processor(self, cache_config, temp_cache_dir):
        """Create offline processor instance"""
        processor = OfflineProcessor(cache_config, temp_cache_dir)
        yield processor
        # Cleanup
        await processor.clear_cache("all")
    
    def test_initialization(self, cache_config, temp_cache_dir):
        """Test processor initialization"""
        processor = OfflineProcessor(cache_config, temp_cache_dir)
        
        assert processor.config == cache_config
        assert processor.cache_dir == Path(temp_cache_dir)
        assert processor.memory_cache == {}
        assert processor.memory_size == 0
        assert processor.offline_models == {}
        assert processor.model_configs == {}
        assert processor.stats["cache_hits"] == 0
        assert processor.stats["cache_misses"] == 0
    
    def test_database_initialization(self, cache_config, temp_cache_dir):
        """Test database initialization"""
        processor = OfflineProcessor(cache_config, temp_cache_dir)
        
        # Check if database file exists
        assert processor.db_path.exists()
        
        # Check if tables exist
        with sqlite3.connect(processor.db_path) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='cache_entries'
            """)
            assert cursor.fetchone() is not None
    
    @pytest.mark.asyncio
    async def test_cache_result_and_retrieve(self, processor):
        """Test caching and retrieving results"""
        test_data = {"sentiment": "positive", "confidence": 0.8}
        cache_key = "test_sentiment_123"
        
        # Cache result
        await processor.cache_result(cache_key, test_data, "sentiment")
        
        # Retrieve from cache
        result = await processor.get_cached_result(cache_key, "sentiment")
        
        assert result == test_data
        assert processor.stats["cache_hits"] == 1
        assert processor.stats["cache_misses"] == 0
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, processor):
        """Test cache miss scenario"""
        result = await processor.get_cached_result("nonexistent_key", "sentiment")
        
        assert result is None
        assert processor.stats["cache_hits"] == 0
        assert processor.stats["cache_misses"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, processor):
        """Test cache expiration"""
        test_data = {"sentiment": "negative", "confidence": 0.7}
        cache_key = "expiring_key"
        
        # Cache with short TTL
        await processor.cache_result(cache_key, test_data, "sentiment", ttl=1)
        
        # Should be available immediately
        result = await processor.get_cached_result(cache_key, "sentiment")
        assert result == test_data
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        result = await processor.get_cached_result(cache_key, "sentiment")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_memory_cache_eviction(self, processor):
        """Test memory cache eviction when full"""
        # Fill memory cache with large entries
        large_data = "x" * (512 * 1024)  # 512KB
        
        for i in range(3):  # Should exceed 1MB limit
            await processor.cache_result(f"large_key_{i}", large_data, "sentiment")
        
        # Check that some entries were evicted
        assert len(processor.memory_cache) < 3
        assert processor.memory_size <= processor.config.max_memory_size
    
    @pytest.mark.asyncio
    async def test_disk_cache_persistence(self, processor):
        """Test disk cache persistence across instances"""
        test_data = {"entities": ["person", "location"], "confidence": 0.9}
        cache_key = "persistent_key"
        
        # Cache result
        await processor.cache_result(cache_key, test_data, "ner")
        
        # Create new processor instance (should load from disk)
        new_processor = OfflineProcessor(processor.config, processor.cache_dir)
        
        # Should retrieve from disk cache
        result = await new_processor.get_cached_result(cache_key, "ner")
        assert result == test_data
    
    @pytest.mark.asyncio
    async def test_offline_processing_not_available(self, processor):
        """Test offline processing when models not available"""
        result = await processor.process_offline("test text", "sentiment", "tw")
        
        assert result is None
        assert processor.stats["offline_processing"] == 0
    
    @pytest.mark.asyncio
    async def test_offline_processing_available(self, processor):
        """Test offline processing with available models"""
        # Mock offline model
        mock_model = MagicMock()
        processor.offline_models["sentiment_tw"] = mock_model
        
        result = await processor.process_offline("test text", "sentiment", "tw")
        
        assert result is not None
        assert result["sentiment"] == "positive"
        assert result["confidence"] == 0.8
        assert result["source"] == "offline_model"
        assert processor.stats["offline_processing"] == 1
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, processor):
        """Test cache clearing"""
        # Add some cache entries
        await processor.cache_result("key1", {"data": 1}, "sentiment")
        await processor.cache_result("key2", {"data": 2}, "ner")
        
        # Clear memory cache only
        await processor.clear_cache("memory")
        assert len(processor.memory_cache) == 0
        assert processor.memory_size == 0
        
        # Disk cache should still have entries
        result = await processor.get_cached_result("key1", "sentiment")
        assert result is not None
        
        # Clear all cache
        await processor.clear_cache("all")
        result = await processor.get_cached_result("key1", "sentiment")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_stats(self, processor):
        """Test statistics retrieval"""
        # Add some cache entries
        await processor.cache_result("key1", {"data": 1}, "sentiment")
        await processor.cache_result("key2", {"data": 2}, "ner")
        
        # Access cache
        await processor.get_cached_result("key1", "sentiment")
        await processor.get_cached_result("nonexistent", "sentiment")
        
        stats = processor.get_stats()
        
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "offline_processing" in stats
        assert "online_fallback" in stats
        assert "errors" in stats
        assert "memory_cache_size" in stats
        assert "memory_cache_memory" in stats
        assert "disk_cache_size" in stats
        assert "offline_models" in stats
    
    @pytest.mark.asyncio
    async def test_export_cache_stats(self, processor):
        """Test detailed cache statistics export"""
        # Add some cache entries
        await processor.cache_result("key1", {"data": 1}, "sentiment")
        await processor.cache_result("key2", {"data": 2}, "ner")
        
        # Access cache multiple times
        await processor.get_cached_result("key1", "sentiment")
        await processor.get_cached_result("key1", "sentiment")
        
        stats = await processor.export_cache_stats()
        
        assert "memory_cache" in stats
        assert "disk_cache" in stats
        assert "processing_stats" in stats
        assert "config" in stats
        
        memory_stats = stats["memory_cache"]
        assert "entries" in memory_stats
        assert "size_bytes" in memory_stats
        assert "max_size_bytes" in memory_stats
        
        disk_stats = stats["disk_cache"]
        assert "entries" in disk_stats
        assert "size_bytes" in disk_stats
        assert "avg_access_count" in disk_stats
        assert "last_access" in disk_stats
    
    @pytest.mark.asyncio
    async def test_error_handling_cache_operations(self, processor):
        """Test error handling in cache operations"""
        # Test with invalid data that can't be pickled
        invalid_data = lambda x: x  # Functions can't be pickled
        
        # Should handle error gracefully
        await processor.cache_result("invalid_key", invalid_data, "sentiment")
        
        # Should not crash and should increment error count
        assert processor.stats["errors"] > 0
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_entries(self, processor):
        """Test cleanup of expired entries"""
        # Add expired entry
        expired_entry = CacheEntry(
            key="expired_key",
            data={"expired": "data"},
            timestamp=datetime.utcnow() - timedelta(hours=2),
            ttl=3600  # 1 hour
        )
        processor.memory_cache["expired_key"] = expired_entry
        processor.memory_size = 100
        
        # Run cleanup
        await processor._cleanup_expired_entries()
        
        # Expired entry should be removed
        assert "expired_key" not in processor.memory_cache
        assert processor.memory_size == 0
    
    @pytest.mark.asyncio
    async def test_lru_eviction(self, processor):
        """Test least recently used eviction"""
        # Add multiple entries
        for i in range(5):
            await processor.cache_result(f"key_{i}", {"data": i}, "sentiment")
        
        # Access some entries to change their last_accessed time
        await processor.get_cached_result("key_0", "sentiment")
        await processor.get_cached_result("key_2", "sentiment")
        
        # Add a large entry that will trigger eviction
        large_data = "x" * (512 * 1024)
        await processor.cache_result("large_key", large_data, "sentiment")
        
        # Check that LRU entries were evicted
        # key_1, key_3, key_4 should be evicted before key_0, key_2
        assert "key_0" in processor.memory_cache or "key_2" in processor.memory_cache
    
    @pytest.mark.asyncio
    async def test_batch_operations(self, processor):
        """Test batch cache operations"""
        # Cache multiple entries
        test_data = [
            ("key1", {"sentiment": "positive"}),
            ("key2", {"sentiment": "negative"}),
            ("key3", {"sentiment": "neutral"})
        ]
        
        for key, data in test_data:
            await processor.cache_result(key, data, "sentiment")
        
        # Retrieve all
        results = []
        for key, _ in test_data:
            result = await processor.get_cached_result(key, "sentiment")
            results.append(result)
        
        # All should be retrieved successfully
        assert len(results) == 3
        assert all(result is not None for result in results)
        assert processor.stats["cache_hits"] == 3
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, processor):
        """Test concurrent cache access"""
        # Create multiple tasks accessing cache simultaneously
        async def cache_and_retrieve(key, data):
            await processor.cache_result(key, data, "sentiment")
            return await processor.get_cached_result(key, "sentiment")
        
        tasks = [
            cache_and_retrieve(f"concurrent_key_{i}", {"data": i})
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 10
        assert all(result is not None for result in results)
        assert processor.stats["cache_hits"] == 10


class TestProcessingMode:
    """Test processing mode enum"""
    
    def test_processing_modes(self):
        """Test processing mode values"""
        assert ProcessingMode.ONLINE.value == "online"
        assert ProcessingMode.OFFLINE.value == "offline"
        assert ProcessingMode.HYBRID.value == "hybrid"


class TestCacheStrategy:
    """Test cache strategy enum"""
    
    def test_cache_strategies(self):
        """Test cache strategy values"""
        assert CacheStrategy.MEMORY.value == "memory"
        assert CacheStrategy.DISK.value == "disk"
        assert CacheStrategy.HYBRID.value == "hybrid"
