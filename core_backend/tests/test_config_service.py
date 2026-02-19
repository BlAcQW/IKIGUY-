"""
Tests for Core Backend ConfigService integration with shared libraries.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from backend.services.config_service import ConfigService
from apps.shared.config import TenantConfig, SystemConfig, FeatureFlags


class TestConfigService:
    """Test cases for ConfigService integration with shared libraries."""

    @pytest.fixture
    def config_service(self):
        """Create a config service instance for testing."""
        service = ConfigService()
        return service

    @pytest.mark.asyncio
    async def test_config_service_initialization(self, config_service):
        """Test that config service initializes correctly with shared library."""
        assert config_service.config_engine is not None
        assert hasattr(config_service.config_engine, 'get_tenant_config')
        assert hasattr(config_service.config_engine, 'update_tenant_config')

    @pytest.mark.asyncio
    async def test_get_tenant_config(self, config_service):
        """Test getting tenant configuration."""
        tenant_id = "test-tenant-123"
        
        # Mock the config engine response
        mock_config = TenantConfig(
            tenant_id=tenant_id,
            name="Test Tenant",
            settings={"timezone": "UTC", "language": "en"},
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        with patch.object(config_service.config_engine, 'get_tenant_config', return_value=mock_config):
            result = await config_service.get_tenant_config(tenant_id)
            
            assert result is not None
            assert result.tenant_id == tenant_id
            assert result.name == "Test Tenant"
            assert result.settings["timezone"] == "UTC"

    @pytest.mark.asyncio
    async def test_update_tenant_config(self, config_service):
        """Test updating tenant configuration."""
        tenant_id = "test-tenant-123"
        
        config = TenantConfig(
            tenant_id=tenant_id,
            name="Updated Tenant",
            settings={"timezone": "EST", "language": "es"},
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        with patch.object(config_service.config_engine, 'update_tenant_config', return_value=True):
            result = await config_service.update_tenant_config(tenant_id, config)
            assert result is True

    @pytest.mark.asyncio
    async def test_get_system_config(self, config_service):
        """Test getting system configuration."""
        mock_system_config = SystemConfig(
            system_id="kasaai-core",
            environment="production",
            debug_mode=True,
            log_level="INFO"
        )
        
        with patch.object(config_service.config_engine, 'get_system_config', return_value=mock_system_config):
            result = await config_service.get_system_config()
            
            assert result is not None
            assert result.system_id == "kasaai-core"
            assert result.environment == "production"
            assert result.debug_mode is True

    @pytest.mark.asyncio
    async def test_update_system_config(self, config_service):
        """Test updating system configuration."""
        system_config = SystemConfig(
            system_id="kasaai-core-updated",
            environment="staging",
            debug_mode=False,
            log_level="WARNING"
        )
        
        with patch.object(config_service.config_engine, 'update_system_config', return_value=True):
            result = await config_service.update_system_config(system_config)
            assert result is True

    @pytest.mark.asyncio
    async def test_get_feature_flags(self, config_service):
        """Test getting feature flags."""
        tenant_id = "test-tenant-123"
        
        mock_flags = {
            "advanced_analytics": True,
            "ai_summarization": False,
            "multi_language": True,
            "real_time_transcription": True
        }
        
        with patch.object(config_service.config_engine, 'get_all_feature_flags', return_value=mock_flags):
            result = await config_service.get_feature_flags(tenant_id)
            
            assert result is not None
            assert result["advanced_analytics"] is True
            assert result["ai_summarization"] is False
            assert result["multi_language"] is True

    @pytest.mark.asyncio
    async def test_update_feature_flags(self, config_service):
        """Test updating feature flags."""
        tenant_id = "test-tenant-123"
        
        flags = FeatureFlags(
            advanced_analytics=True,
            ai_summarization=True,
            multi_language=True,
            real_time_transcription=False
        )
        
        with patch.object(config_service.config_engine, 'set_feature_flag', return_value=True):
            result = await config_service.update_feature_flags(tenant_id, flags)
            assert result is True

    @pytest.mark.asyncio
    async def test_is_feature_enabled(self, config_service):
        """Test checking if a feature is enabled."""
        tenant_id = "test-tenant-123"
        feature = "advanced_analytics"
        
        with patch.object(config_service.config_engine, 'get_feature_flag', return_value=True):
            result = await config_service.is_feature_enabled(tenant_id, feature)
            assert result is True
        
        with patch.object(config_service.config_engine, 'get_feature_flag', return_value=False):
            result = await config_service.is_feature_enabled(tenant_id, "disabled_feature")
            assert result is False

    @pytest.mark.asyncio
    async def test_get_config_summary(self, config_service):
        """Test getting configuration summary."""
        tenant_id = "test-tenant-123"
        
        mock_summary = {
            "tenant_id": tenant_id,
            "config_status": "active",
            "features_enabled": 3,
            "features_disabled": 1,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        with patch.object(config_service.config_engine, 'get_config_summary', return_value=mock_summary):
            result = await config_service.get_config_summary(tenant_id)
            
            assert result is not None
            assert result["tenant_id"] == tenant_id
            assert result["config_status"] == "active"
            assert result["features_enabled"] == 3

    @pytest.mark.asyncio
    async def test_export_config(self, config_service):
        """Test exporting configuration."""
        tenant_id = "test-tenant-123"
        
        mock_export = '{"tenant_id": "test-tenant-123", "config": {...}}'
        
        with patch.object(config_service.config_engine, 'export_config', return_value=mock_export):
            result = await config_service.export_config(tenant_id, "json")
            
            assert result is not None
            assert isinstance(result, str)
            assert "tenant_id" in result

    @pytest.mark.asyncio
    async def test_import_config(self, config_service):
        """Test importing configuration."""
        tenant_id = "test-tenant-123"
        config_data = '{"tenant_id": "test-tenant-123", "config": {...}}'
        
        with patch.object(config_service.config_engine, 'import_config', return_value=True):
            result = await config_service.import_config(tenant_id, config_data, "json")
            assert result is True



    @pytest.mark.asyncio
    async def test_config_service_error_handling(self, config_service):
        """Test error handling in config service."""
        tenant_id = "test-tenant-123"
        
        # Test with invalid tenant ID
        with patch.object(config_service.config_engine, 'get_tenant_config', side_effect=Exception("Config not found")):
            result = await config_service.get_tenant_config(tenant_id)
            assert result is None

    @pytest.mark.asyncio
    async def test_config_service_performance(self, config_service):
        """Test config service performance."""
        import time
        
        start_time = time.time()
        
        # Test multiple config operations
        tenant_id = "test-tenant-123"
        
        with patch.object(config_service.config_engine, 'get_tenant_config', return_value=Mock()):
            for i in range(10):
                await config_service.get_tenant_config(f"{tenant_id}-{i}")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (2 seconds)
        assert execution_time < 2.0

    @pytest.mark.asyncio
    async def test_config_service_concurrent_operations(self, config_service):
        """Test concurrent config operations."""
        async def get_config(i):
            tenant_id = f"tenant-{i}"
            with patch.object(config_service.config_engine, 'get_tenant_config', return_value=Mock()):
                return await config_service.get_tenant_config(tenant_id)
        
        # Run 5 concurrent operations
        tasks = [get_config(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All operations should complete
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_feature_flag_validation(self, config_service):
        """Test feature flag validation."""
        tenant_id = "test-tenant-123"
        
        # Test with valid feature names
        valid_features = ["advanced_analytics", "ai_summarization", "multi_language"]
        
        with patch.object(config_service.config_engine, 'get_feature_flag', return_value=True):
            for feature in valid_features:
                result = await config_service.is_feature_enabled(tenant_id, feature)
                assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_config_export_formats(self, config_service):
        """Test config export in different formats."""
        tenant_id = "test-tenant-123"
        
        formats = ["json", "yaml", "xml"]
        
        for format_type in formats:
            with patch.object(config_service.config_engine, 'export_config', return_value=f"exported_{format_type}"):
                result = await config_service.export_config(tenant_id, format_type)
                assert result is not None
                assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_config_import_validation(self, config_service):
        """Test config import validation."""
        tenant_id = "test-tenant-123"
        
        # Test with valid JSON config
        valid_config = '{"tenant_id": "test-tenant-123", "name": "Test Tenant"}'
        
        with patch.object(config_service.config_engine, 'import_config', return_value=True):
            result = await config_service.import_config(tenant_id, valid_config, "json")
            assert result is True

    @pytest.mark.asyncio
    async def test_config_service_initialization_with_custom_storage(self, config_service):
        """Test config service initialization with custom storage backend."""
        from apps.shared.storage import MemoryStorageBackend
        from apps.shared.storage.interfaces import StorageConfig
        
        # Create custom storage backend
        storage_config = StorageConfig(backend_type="memory", connection_string="memory://")
        custom_storage = MemoryStorageBackend(storage_config)
        
        # Create config service with custom storage
        custom_config_service = ConfigService(storage_backend=custom_storage)
        
        assert custom_config_service.config_engine is not None
        assert custom_config_service.config_engine.storage == custom_storage

    @pytest.mark.asyncio
    async def test_config_service_tenant_isolation(self, config_service):
        """Test tenant isolation in config service."""
        tenant_1 = "tenant-1"
        tenant_2 = "tenant-2"
        
        # Mock different configs for different tenants
        config_1 = TenantConfig(
            tenant_id=tenant_1,
            name="Tenant 1",
            settings={"timezone": "UTC"},
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        config_2 = TenantConfig(
            tenant_id=tenant_2,
            name="Tenant 2",
            settings={"timezone": "EST"},
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        with patch.object(config_service.config_engine, 'get_tenant_config') as mock_get:
            mock_get.side_effect = lambda tid: config_1 if tid == tenant_1 else config_2
            
            result_1 = await config_service.get_tenant_config(tenant_1)
            result_2 = await config_service.get_tenant_config(tenant_2)
            
            assert result_1.tenant_id == tenant_1
            assert result_2.tenant_id == tenant_2
            assert result_1.settings["timezone"] == "UTC"
            assert result_2.settings["timezone"] == "EST"

    @pytest.mark.asyncio
    async def test_config_service_feature_flag_operations(self, config_service):
        """Test comprehensive feature flag operations."""
        tenant_id = "test-tenant-123"
        
        # Test getting feature flags
        mock_flags = {
            "advanced_analytics": True,
            "ai_summarization": False,
            "multi_language": True
        }
        
        with patch.object(config_service.config_engine, 'get_all_feature_flags', return_value=mock_flags):
            flags = await config_service.get_feature_flags(tenant_id)
            assert flags["advanced_analytics"] is True
            assert flags["ai_summarization"] is False
        
        # Test updating feature flags
        updated_flags = FeatureFlags(
            advanced_analytics=False,
            ai_summarization=True,
            multi_language=True
        )
        
        with patch.object(config_service.config_engine, 'set_feature_flag', return_value=True):
            result = await config_service.update_feature_flags(tenant_id, updated_flags)
            assert result is True

    @pytest.mark.asyncio
    async def test_config_service_system_config_operations(self, config_service):
        """Test comprehensive system config operations."""
        # Test getting system config
        mock_system_config = SystemConfig(
            system_id="test-system",
            environment="development",
            debug_mode=True,
            log_level="DEBUG"
        )
        
        with patch.object(config_service.config_engine, 'get_system_config', return_value=mock_system_config):
            system_config = await config_service.get_system_config()
            assert system_config.system_id == "test-system"
            assert system_config.environment == "development"
            assert system_config.debug_mode is True
        
        # Test updating system config
        updated_system_config = SystemConfig(
            system_id="updated-system",
            environment="production",
            debug_mode=False,
            log_level="INFO"
        )
        
        with patch.object(config_service.config_engine, 'update_system_config', return_value=True):
            result = await config_service.update_system_config(updated_system_config)
            assert result is True


if __name__ == "__main__":
    pytest.main([__file__])
