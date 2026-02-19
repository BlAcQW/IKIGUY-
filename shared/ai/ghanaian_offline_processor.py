"""
Offline processing capabilities for Ghanaian language features

This module provides offline processing capabilities for Ghanaian language
features including local caching, offline models, and fallback mechanisms.
"""

import asyncio
import json
import logging
import os
import pickle
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """Processing modes for offline capabilities"""
    ONLINE = "online"
    OFFLINE = "offline"
    HYBRID = "hybrid"


class CacheStrategy(Enum):
    """Cache strategies for different data types"""
    MEMORY = "memory"
    DISK = "disk"
    HYBRID = "hybrid"


@dataclass
class CacheConfig:
    """Configuration for caching system"""
    max_memory_size: int = 100 * 1024 * 1024  # 100MB
    max_disk_size: int = 1024 * 1024 * 1024  # 1GB
    ttl_hours: int = 24
    cleanup_interval_hours: int = 6
    compression_enabled: bool = True
    encryption_enabled: bool = False


@dataclass
class OfflineModelConfig:
    """Configuration for offline models"""
    model_path: str
    model_type: str  # "sentiment", "ner", "intent"
    language: str
    version: str
    accuracy_threshold: float = 0.7
    max_input_length: int = 512
    batch_size: int = 32


class CacheEntry(BaseModel):
    """Cache entry model"""
    key: str
    data: Any
    timestamp: datetime
    ttl: int = 86400  # 24 hours in seconds
    size: int = 0
    access_count: int = 0
    last_accessed: datetime = Field(default_factory=datetime.utcnow)


class OfflineProcessor:
    """
    Offline processing system for Ghanaian language features
    
    Provides local processing capabilities with caching, offline models,
    and intelligent fallback mechanisms.
    """
    
    def __init__(self, config: CacheConfig, cache_dir: str = "./cache"):
        """
        Initialize offline processor
        
        Args:
            config: Cache configuration
            cache_dir: Directory for disk cache
        """
        self.config = config
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory cache
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.memory_size = 0
        
        # Database for persistent cache
        self.db_path = self.cache_dir / "cache.db"
        self._init_database()
        
        # Offline models
        self.offline_models: Dict[str, Any] = {}
        self.model_configs: Dict[str, OfflineModelConfig] = {}
        
        # Processing statistics
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "offline_processing": 0,
            "online_fallback": 0,
            "errors": 0
        }
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_task())
    
    def _init_database(self):
        """Initialize SQLite database for persistent cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        key TEXT PRIMARY KEY,
                        data BLOB,
                        timestamp TEXT,
                        ttl INTEGER,
                        size INTEGER,
                        access_count INTEGER,
                        last_accessed TEXT
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON cache_entries(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)")
        except Exception as e:
            logger.error(f"Failed to initialize cache database: {e}")
    
    async def get_cached_result(self, key: str, operation: str) -> Optional[Any]:
        """
        Get cached result for operation
        
        Args:
            key: Cache key
            operation: Operation type (sentiment, ner, intent, etc.)
            
        Returns:
            Cached result or None if not found/expired
        """
        try:
            # Check memory cache first
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if not self._is_expired(entry):
                    entry.access_count += 1
                    entry.last_accessed = datetime.utcnow()
                    self.stats["cache_hits"] += 1
                    return entry.data
            
            # Check disk cache
            disk_result = await self._get_from_disk_cache(key)
            if disk_result is not None:
                # Move to memory cache
                await self._add_to_memory_cache(key, disk_result, operation)
                self.stats["cache_hits"] += 1
                return disk_result
            
            self.stats["cache_misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached result: {e}")
            self.stats["errors"] += 1
            return None
    
    async def cache_result(self, key: str, data: Any, operation: str, ttl: Optional[int] = None):
        """
        Cache result for future use
        
        Args:
            key: Cache key
            data: Data to cache
            operation: Operation type
            ttl: Time to live in seconds
        """
        try:
            # Add to memory cache
            await self._add_to_memory_cache(key, data, operation, ttl)
            
            # Add to disk cache
            await self._add_to_disk_cache(key, data, operation, ttl)
            
        except Exception as e:
            logger.error(f"Error caching result: {e}")
            self.stats["errors"] += 1
    
    async def _add_to_memory_cache(self, key: str, data: Any, operation: str, ttl: Optional[int] = None):
        """Add entry to memory cache"""
        try:
            # Serialize data to get size
            serialized = pickle.dumps(data)
            size = len(serialized)
            
            # Check if we need to evict entries
            while self.memory_size + size > self.config.max_memory_size and self.memory_cache:
                await self._evict_memory_entry()
            
            entry = CacheEntry(
                key=key,
                data=data,
                timestamp=datetime.utcnow(),
                ttl=ttl or self.config.ttl_hours * 3600,
                size=size,
                access_count=1,
                last_accessed=datetime.utcnow()
            )
            
            self.memory_cache[key] = entry
            self.memory_size += size
            
        except Exception as e:
            logger.error(f"Error adding to memory cache: {e}")
    
    async def _add_to_disk_cache(self, key: str, data: Any, operation: str, ttl: Optional[int] = None):
        """Add entry to disk cache"""
        try:
            serialized = pickle.dumps(data)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cache_entries 
                    (key, data, timestamp, ttl, size, access_count, last_accessed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    key,
                    serialized,
                    datetime.utcnow().isoformat(),
                    ttl or self.config.ttl_hours * 3600,
                    len(serialized),
                    1,
                    datetime.utcnow().isoformat()
                ))
                
        except Exception as e:
            logger.error(f"Error adding to disk cache: {e}")
    
    async def _get_from_disk_cache(self, key: str) -> Optional[Any]:
        """Get entry from disk cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT data, timestamp, ttl, access_count, last_accessed
                    FROM cache_entries WHERE key = ?
                """, (key,))
                
                row = cursor.fetchone()
                if row:
                    data_blob, timestamp_str, ttl, access_count, last_accessed_str = row
                    
                    # Check if expired
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if datetime.utcnow() - timestamp > timedelta(seconds=ttl):
                        # Remove expired entry
                        conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                        return None
                    
                    # Update access count
                    conn.execute("""
                        UPDATE cache_entries 
                        SET access_count = ?, last_accessed = ?
                        WHERE key = ?
                    """, (access_count + 1, datetime.utcnow().isoformat(), key))
                    
                    return pickle.loads(data_blob)
                    
            return None
            
        except Exception as e:
            logger.error(f"Error getting from disk cache: {e}")
            return None
    
    async def _evict_memory_entry(self):
        """Evict least recently used entry from memory cache"""
        if not self.memory_cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self.memory_cache.keys(),
            key=lambda k: self.memory_cache[k].last_accessed
        )
        
        entry = self.memory_cache[lru_key]
        self.memory_size -= entry.size
        del self.memory_cache[lru_key]
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired"""
        return datetime.utcnow() - entry.timestamp > timedelta(seconds=entry.ttl)
    
    async def _cleanup_task(self):
        """Background task to clean up expired cache entries"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval_hours * 3600)
                await self._cleanup_expired_entries()
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    async def _cleanup_expired_entries(self):
        """Clean up expired cache entries"""
        try:
            # Clean memory cache
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if self._is_expired(entry)
            ]
            
            for key in expired_keys:
                entry = self.memory_cache[key]
                self.memory_size -= entry.size
                del self.memory_cache[key]
            
            # Clean disk cache
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    DELETE FROM cache_entries 
                    WHERE datetime(timestamp) + ttl < datetime('now')
                """)
                
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired entries: {e}")
    
    async def process_offline(self, text: str, operation: str, language: str = "auto") -> Optional[Any]:
        """
        Process text using offline models
        
        Args:
            text: Text to process
            operation: Operation type (sentiment, ner, intent)
            language: Language code
            
        Returns:
            Processing result or None if offline processing not available
        """
        try:
            model_key = f"{operation}_{language}"
            
            if model_key not in self.offline_models:
                logger.warning(f"Offline model not available for {model_key}")
                return None
            
            # Use offline model for processing
            model = self.offline_models[model_key]
            result = await self._run_offline_model(model, text, operation)
            
            if result:
                self.stats["offline_processing"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error in offline processing: {e}")
            self.stats["errors"] += 1
            return None
    
    async def _run_offline_model(self, model: Any, text: str, operation: str) -> Optional[Any]:
        """Run offline model for processing"""
        try:
            # This would be implemented based on the specific model type
            # For now, return a placeholder result
            if operation == "sentiment":
                return {
                    "sentiment": "positive",
                    "confidence": 0.8,
                    "source": "offline_model"
                }
            elif operation == "ner":
                return {
                    "entities": [],
                    "confidence": 0.7,
                    "source": "offline_model"
                }
            elif operation == "intent":
                return {
                    "intent": "unknown",
                    "confidence": 0.6,
                    "source": "offline_model"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error running offline model: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            **self.stats,
            "memory_cache_size": len(self.memory_cache),
            "memory_cache_memory": self.memory_size,
            "disk_cache_size": self._get_disk_cache_size(),
            "offline_models": len(self.offline_models)
        }
    
    def _get_disk_cache_size(self) -> int:
        """Get disk cache size in bytes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT SUM(size) FROM cache_entries")
                result = cursor.fetchone()
                return result[0] or 0
        except Exception as e:
            logger.error(f"Error getting disk cache size: {e}")
            return 0
    
    async def clear_cache(self, cache_type: str = "all"):
        """
        Clear cache entries
        
        Args:
            cache_type: Type of cache to clear (memory, disk, all)
        """
        try:
            if cache_type in ["memory", "all"]:
                self.memory_cache.clear()
                self.memory_size = 0
            
            if cache_type in ["disk", "all"]:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM cache_entries")
            
            logger.info(f"Cleared {cache_type} cache")
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    async def export_cache_stats(self) -> Dict[str, Any]:
        """Export detailed cache statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_entries,
                        SUM(size) as total_size,
                        AVG(access_count) as avg_access_count,
                        MAX(last_accessed) as last_access
                    FROM cache_entries
                """)
                row = cursor.fetchone()
                
                return {
                    "memory_cache": {
                        "entries": len(self.memory_cache),
                        "size_bytes": self.memory_size,
                        "max_size_bytes": self.config.max_memory_size
                    },
                    "disk_cache": {
                        "entries": row[0] or 0,
                        "size_bytes": row[1] or 0,
                        "avg_access_count": row[2] or 0,
                        "last_access": row[3]
                    },
                    "processing_stats": self.stats,
                    "config": {
                        "max_memory_size": self.config.max_memory_size,
                        "max_disk_size": self.config.max_disk_size,
                        "ttl_hours": self.config.ttl_hours
                    }
                }
                
        except Exception as e:
            logger.error(f"Error exporting cache stats: {e}")
            return {}
