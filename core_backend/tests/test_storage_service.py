"""
Tests for Core Backend Storage Service integration with shared libraries.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from backend.services.storage_service import StorageService


class TestStorageService:
    """Test cases for StorageService integration with shared libraries."""

    @pytest.fixture
    def storage_service(self):
        """Create a storage service instance for testing."""
        service = StorageService(storage_type="memory")
        return service

    @pytest.mark.asyncio
    async def test_storage_service_initialization(self, storage_service):
        """Test that storage service initializes correctly with shared library."""
        assert storage_service.storage_type == "memory"
        assert storage_service.storage_backend is not None
        assert hasattr(storage_service.storage_backend, 'create_table')

    @pytest.mark.asyncio
    async def test_create_table(self, storage_service):
        """Test table creation using shared storage library."""
        table_name = "test_table"
        schema = {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT",
            "created_at": "TEXT"
        }
        
        result = await storage_service.create_table(table_name, schema)
        assert result is True

    @pytest.mark.asyncio
    async def test_insert_and_select_data(self, storage_service):
        """Test data insertion and retrieval using shared storage library."""
        # Create test table
        table_name = "test_data_table"
        schema = {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT",
            "value": "INTEGER"
        }
        await storage_service.create_table(table_name, schema)
        
        # Insert test data
        test_data = {
            "id": "test_1",
            "name": "Test Item",
            "value": 42
        }
        result = await storage_service.insert(table_name, test_data)
        assert result is True
        
        # Select data
        results = await storage_service.select(table_name, {"id": "test_1"})
        assert len(results) == 1
        assert results[0]["name"] == "Test Item"
        assert results[0]["value"] == 42

    @pytest.mark.asyncio
    async def test_update_data(self, storage_service):
        """Test data update using shared storage library."""
        # Create test table
        table_name = "test_update_table"
        schema = {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT",
            "status": "TEXT"
        }
        await storage_service.create_table(table_name, schema)
        
        # Insert initial data
        initial_data = {
            "id": "update_test",
            "name": "Original Name",
            "status": "active"
        }
        await storage_service.insert(table_name, initial_data)
        
        # Update data
        update_data = {"status": "inactive"}
        conditions = {"id": "update_test"}
        result = await storage_service.update(table_name, update_data, conditions)
        assert result == 1
        
        # Verify update
        results = await storage_service.select(table_name, {"id": "update_test"})
        assert results[0]["status"] == "inactive"

    @pytest.mark.asyncio
    async def test_delete_data(self, storage_service):
        """Test data deletion using shared storage library."""
        # Create test table
        table_name = "test_delete_table"
        schema = {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT"
        }
        await storage_service.create_table(table_name, schema)
        
        # Insert test data
        test_data = {
            "id": "delete_test",
            "name": "To Delete"
        }
        await storage_service.insert(table_name, test_data)
        
        # Verify data exists
        results = await storage_service.select(table_name, {"id": "delete_test"})
        assert len(results) == 1
        
        # Delete data
        result = await storage_service.delete(table_name, {"id": "delete_test"})
        assert result == 1
        
        # Verify deletion
        results = await storage_service.select(table_name, {"id": "delete_test"})
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_select_one(self, storage_service):
        """Test single record selection using shared storage library."""
        # Create test table
        table_name = "test_select_one_table"
        schema = {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT"
        }
        await storage_service.create_table(table_name, schema)
        
        # Insert test data
        test_data = {
            "id": "select_one_test",
            "name": "Single Record"
        }
        await storage_service.insert(table_name, test_data)
        
        # Select single record
        result = await storage_service.select_one(table_name, {"id": "select_one_test"})
        assert result is not None
        assert result["name"] == "Single Record"

    @pytest.mark.asyncio
    async def test_upsert_data(self, storage_service):
        """Test upsert functionality using shared storage library."""
        # Create test table
        table_name = "test_upsert_table"
        schema = {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT",
            "count": "INTEGER"
        }
        await storage_service.create_table(table_name, schema)
        
        # Insert initial data
        initial_data = {
            "id": "upsert_test",
            "name": "Initial",
            "count": 1
        }
        await storage_service.insert(table_name, initial_data)
        
        # Upsert same record
        upsert_data = {
            "id": "upsert_test",
            "name": "Updated",
            "count": 2
        }
        result = await storage_service.upsert(table_name, upsert_data, ["id"])
        assert result > 0
        
        # Verify upsert
        results = await storage_service.select(table_name, {"id": "upsert_test"})
        assert len(results) == 1
        assert results[0]["name"] == "Updated"
        assert results[0]["count"] == 2

    @pytest.mark.asyncio
    async def test_list_tables(self, storage_service):
        """Test table listing using shared storage library."""
        # Create test tables
        table_names = ["table_1", "table_2", "table_3"]
        schema = {"id": "TEXT PRIMARY KEY"}
        
        for table_name in table_names:
            await storage_service.create_table(table_name, schema)
        
        # List tables
        tables = await storage_service.list_tables()
        assert all(table in tables for table in table_names)

    @pytest.mark.asyncio
    async def test_get_table_info(self, storage_service):
        """Test table information retrieval using shared storage library."""
        # Create test table
        table_name = "test_info_table"
        schema = {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT"
        }
        await storage_service.create_table(table_name, schema)
        
        # Get table info
        info = await storage_service.get_table_info(table_name)
        assert info is not None
        assert "schema" in info

    @pytest.mark.asyncio
    async def test_backup_and_restore(self, storage_service):
        """Test backup and restore functionality using shared storage library."""
        # Create test table
        table_name = "test_backup_table"
        schema = {
            "id": "TEXT PRIMARY KEY",
            "data": "TEXT"
        }
        await storage_service.create_table(table_name, schema)
        
        # Insert test data
        test_data = [
            {"id": "backup_1", "data": "Data 1"},
            {"id": "backup_2", "data": "Data 2"}
        ]
        for data in test_data:
            await storage_service.insert(table_name, data)
        
        # Create backup
        backup_name = "test_backup"
        result = await storage_service.backup_table(table_name, backup_name)
        assert result is True
        
        # Delete original data
        await storage_service.delete(table_name, {})
        
        # Verify data is gone
        results = await storage_service.select(table_name)
        assert len(results) == 0
        
        # Restore from backup
        result = await storage_service.restore_table(table_name, backup_name)
        assert result is True
        
        # Verify data is restored
        results = await storage_service.select(table_name)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_export_and_import_json(self, storage_service):
        """Test JSON export and import using shared storage library."""
        # Create test table
        table_name = "test_export_table"
        schema = {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT",
            "value": "INTEGER"
        }
        await storage_service.create_table(table_name, schema)
        
        # Insert test data
        test_data = [
            {"id": "export_1", "name": "Item 1", "value": 10},
            {"id": "export_2", "name": "Item 2", "value": 20}
        ]
        for data in test_data:
            await storage_service.insert(table_name, data)
        
        # Export data
        exported = await storage_service.export_table(table_name, "json")
        assert exported is not None
        assert "Item 1" in exported
        assert "Item 2" in exported
        
        # Create new table for import
        import_table_name = "test_import_table"
        await storage_service.create_table(import_table_name, schema)
        
        # Import data
        result = await storage_service.import_table(import_table_name, exported, "json")
        assert result is True
        
        # Verify imported data
        results = await storage_service.select(import_table_name)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_storage_stats(self, storage_service):
        """Test storage statistics retrieval using shared storage library."""
        # Create test table
        table_name = "test_stats_table"
        schema = {"id": "TEXT PRIMARY KEY"}
        await storage_service.create_table(table_name, schema)
        
        # Get stats
        stats = await storage_service.get_storage_stats()
        assert "storage_type" in stats
        assert "total_tables" in stats
        assert "tables" in stats
        assert stats["storage_type"] == "memory"

    @pytest.mark.asyncio
    async def test_cleanup_old_data(self, storage_service):
        """Test old data cleanup using shared storage library."""
        # Create test table
        table_name = "test_cleanup_table"
        schema = {
            "id": "TEXT PRIMARY KEY",
            "created_at": "TEXT"
        }
        await storage_service.create_table(table_name, schema)
        
        # Insert test data with dates
        from datetime import datetime, timedelta
        
        old_date = (datetime.utcnow() - timedelta(days=10)).isoformat()
        new_date = datetime.utcnow().isoformat()
        
        test_data = [
            {"id": "old_1", "created_at": old_date},
            {"id": "old_2", "created_at": old_date},
            {"id": "new_1", "created_at": new_date}
        ]
        for data in test_data:
            await storage_service.insert(table_name, data)
        
        # Cleanup old data (keep only 5 days)
        result = await storage_service.cleanup_old_data(table_name, "created_at", 5)
        assert result == 2
        
        # Verify only new data remains
        results = await storage_service.select(table_name)
        assert len(results) == 1
        assert results[0]["id"] == "new_1"

    @pytest.mark.asyncio
    async def test_storage_service_error_handling(self, storage_service):
        """Test error handling in storage service."""
        # Test with non-existent table
        results = await storage_service.select("non_existent_table")
        assert results == []
        
        # Test with invalid table name
        result = await storage_service.create_table("", {})
        assert result is False

    @pytest.mark.asyncio
    async def test_storage_service_with_different_backends(self):
        """Test storage service with different backend types."""
        # Test memory backend
        memory_service = StorageService(storage_type="memory")
        assert memory_service.storage_type == "memory"
        
        # Test PostgreSQL backend (should handle connection gracefully)
        postgres_service = StorageService(storage_type="postgresql")
        assert postgres_service.storage_type == "postgresql"
        
        # Test Redis backend (should handle connection gracefully)
        redis_service = StorageService(storage_type="redis")
        assert redis_service.storage_type == "redis"


if __name__ == "__main__":
    pytest.main([__file__])
