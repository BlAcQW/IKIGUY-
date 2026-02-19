"""
Tests for Storage Backends

This module contains tests for all storage backend implementations.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from ..storage.interfaces import StorageConfig
from ..storage.memory import MemoryStorageBackend
from ..storage.postgres import PostgresStorageBackend
from ..storage.redis import RedisStorageBackend


class TestMemoryStorageBackend:
    """Test memory storage backend"""
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, memory_storage):
        """Test connection and disconnection"""
        storage = await memory_storage
        assert await storage.is_connected()
        assert await storage.disconnect()
        assert not await storage.is_connected()
    
    @pytest.mark.asyncio
    async def test_create_table(self, memory_storage):
        """Test table creation"""
        storage = await memory_storage
        schema = {
            "id": "string",
            "name": "string",
            "age": "integer",
            "created_at": "datetime"
        }
        
        assert await storage.create_table("test_table", schema)
        assert await storage.table_exists("test_table")
    
    @pytest.mark.asyncio
    async def test_insert_get_update_delete(self, memory_storage):
        """Test basic CRUD operations"""
        storage = await memory_storage
        # Create table
        schema = {"id": "string", "name": "string", "age": "integer"}
        await storage.create_table("users", schema)
        
        # Insert record
        data = {"name": "John Doe", "age": 30}
        record_id = await storage.insert("users", data)
        assert record_id is not None
        
        # Get record
        record = await storage.get_by_id("users", record_id)
        assert record is not None
        assert record["name"] == "John Doe"
        assert record["age"] == 30
        
        # Update record
        update_data = {"age": 31}
        assert await storage.update("users", record_id, update_data)
        
        # Verify update
        updated_record = await storage.get_by_id("users", record_id)
        assert updated_record["age"] == 31
        
        # Delete record
        assert await storage.delete("users", record_id)
        
        # Verify deletion
        deleted_record = await storage.get_by_id("users", record_id)
        assert deleted_record is None
    
    @pytest.mark.asyncio
    async def test_query_with_filters(self, memory_storage):
        """Test querying with filters"""
        storage = await memory_storage
        # Create table and insert test data
        schema = {"id": "string", "name": "string", "age": "integer", "city": "string"}
        await storage.create_table("users", schema)
        
        await storage.insert("users", {"name": "John", "age": 30, "city": "NYC"})
        await storage.insert("users", {"name": "Jane", "age": 25, "city": "LA"})
        await storage.insert("users", {"name": "Bob", "age": 35, "city": "NYC"})
        
        # Query with filter
        results = await storage.query("users", filters={"city": "NYC"})
        assert len(results) == 2
        
        # Query with multiple filters
        results = await storage.query("users", filters={"city": "NYC", "age": 30})
        assert len(results) == 1
        assert results[0]["name"] == "John"
    
    @pytest.mark.asyncio
    async def test_count(self, memory_storage):
        """Test counting records"""
        storage = await memory_storage
        schema = {"id": "string", "name": "string"}
        await storage.create_table("users", schema)
        
        await storage.insert("users", {"name": "John"})
        await storage.insert("users", {"name": "Jane"})
        await storage.insert("users", {"name": "Bob"})
        
        assert await storage.count("users") == 3
        assert await storage.count("users", filters={"name": "John"}) == 1
    
    @pytest.mark.asyncio
    async def test_health_check(self, memory_storage):
        """Test health check"""
        storage = await memory_storage
        health = await storage.health_check()
        assert health["status"] == "healthy"
        assert health["backend_type"] == "memory"
        assert "timestamp" in health


class TestRedisStorageBackend:
    """Test Redis storage backend"""
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, redis_storage):
        """Test connection and disconnection"""
        storage = await redis_storage
        assert await storage.is_connected()
        assert await storage.disconnect()
        assert not await storage.is_connected()
    
    @pytest.mark.asyncio
    async def test_cache_operations(self, redis_storage):
        """Test cache operations"""
        storage = await redis_storage
        # Set cache
        assert await storage.set_cache("test_key", {"data": "value"}, ttl=60)
        
        # Get cache
        cached_data = await storage.get_cache("test_key")
        assert cached_data == {"data": "value"}
        
        # Delete cache
        assert await storage.delete_cache("test_key")
        
        # Verify deletion
        cached_data = await storage.get_cache("test_key")
        assert cached_data is None
    
    @pytest.mark.asyncio
    async def test_session_operations(self, redis_storage):
        """Test session operations"""
        storage = await redis_storage
        session_data = {"user_id": "123", "permissions": ["read", "write"]}
        
        # Set session
        assert await storage.set_session("session_123", session_data, ttl=3600)
        
        # Get session
        retrieved_data = await storage.get_session("session_123")
        assert retrieved_data == session_data
        
        # Delete session
        assert await storage.delete_session("session_123")
        
        # Verify deletion
        retrieved_data = await storage.get_session("session_123")
        assert retrieved_data is None


class TestPostgresStorageBackend:
    """Test PostgreSQL storage backend"""
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, postgres_storage):
        """Test connection and disconnection"""
        storage = await postgres_storage
        assert await storage.is_connected()
        assert await storage.disconnect()
        assert not await storage.is_connected()
    
    @pytest.mark.asyncio
    async def test_table_operations(self, postgres_storage):
        """Test table operations"""
        storage = await postgres_storage
        schema = {
            "id": "string",
            "name": "string",
            "age": "integer",
            "created_at": "datetime"
        }
        
        # Create table
        assert await storage.create_table("test_table", schema)
        assert await storage.table_exists("test_table")
        
        # Drop table
        assert await storage.drop_table("test_table")
        assert not await storage.table_exists("test_table")


class TestStorageBackendCompatibility:
    """Test that all storage backends implement the same interface"""
    
    @pytest.mark.parametrize("backend_class", [
        MemoryStorageBackend,
        RedisStorageBackend,
        PostgresStorageBackend
    ])
    def test_backend_interface(self, backend_class):
        """Test that backend implements required interface"""
        config = StorageConfig(backend_type="test")
        backend = backend_class(config)
        
        # Check required methods exist
        required_methods = [
            'connect', 'disconnect', 'is_connected',
            'create_table', 'drop_table', 'table_exists',
            'insert', 'update', 'delete', 'get_by_id',
            'query', 'count', 'execute_raw',
            'begin_transaction', 'commit_transaction', 'rollback_transaction',
            'health_check'
        ]
        
        for method in required_methods:
            assert hasattr(backend, method), f"Missing method: {method}"
    
    @pytest.mark.asyncio
    async def test_memory_backend_full_workflow(self):
        """Test complete workflow with memory backend"""
        config = StorageConfig(backend_type="memory")
        storage = MemoryStorageBackend(config)
        
        try:
            # Connect
            assert await storage.connect()
            
            # Create table
            schema = {
                "id": "string",
                "tenant_id": "string",
                "service": "string",
                "metric": "string",
                "value": "integer",
                "cost": "float",
                "timestamp": "datetime"
            }
            assert await storage.create_table("usage_records", schema)
            
            # Insert usage records
            records = [
                {"tenant_id": "tenant1", "service": "voice", "metric": "calls", "value": 10, "cost": 5.0},
                {"tenant_id": "tenant1", "service": "voice", "metric": "minutes", "value": 120, "cost": 12.0},
                {"tenant_id": "tenant2", "service": "voice", "metric": "calls", "value": 5, "cost": 2.5},
            ]
            
            record_ids = []
            for record in records:
                record_id = await storage.insert("usage_records", record)
                record_ids.append(record_id)
            
            # Query records
            tenant1_records = await storage.query("usage_records", filters={"tenant_id": "tenant1"})
            assert len(tenant1_records) == 2
            
            # Count records
            total_count = await storage.count("usage_records")
            assert total_count == 3
            
            # Health check
            health = await storage.health_check()
            assert health["status"] == "healthy"
            
        finally:
            await storage.disconnect()


if __name__ == "__main__":
    pytest.main([__file__])
