"""
Tests for Configuration Engine

This module tests the comprehensive configuration engine with all features:
- Tenant configuration management
- Feature flags
- Configuration inheritance
- Validation
- Export/import
- Configuration watchers
"""

import pytest
import asyncio
import json
import yaml
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from apps.shared.config.engine import ConfigurationEngine
from apps.shared.config.interfaces import TenantConfig, ProviderConfig, BrandingConfig
from apps.shared.config.models import SystemConfig, FeatureFlags


class SimpleStorageAdapter:
    """Simple storage adapter for configuration engine testing"""
    
    def __init__(self):
        self._data = {}
    
    async def get(self, key: str):
        """Get value by key"""
        return self._data.get(key)
    
    async def set(self, key: str, value):
        """Set value by key"""
        self._data[key] = value
    
    async def delete(self, key: str):
        """Delete value by key"""
        if key in self._data:
            del self._data[key]
    
    async def query(self, pattern: str):
        """Query keys by pattern"""
        import fnmatch
        return [key for key in self._data.keys() if fnmatch.fnmatch(key, pattern)]


class TestConfigurationEngine:
    """Test suite for ConfigurationEngine"""
    
    @pytest.fixture
    def storage_backend(self):
        """Create memory storage backend for testing"""
        return SimpleStorageAdapter()
    
    @pytest.fixture
    async def config_engine(self, storage_backend):
        """Create configuration engine for testing"""
        engine = ConfigurationEngine(storage_backend)
        await engine.start()
        return engine
    
    @pytest.fixture
    def sample_tenant_config(self):
        """Sample tenant configuration for testing"""
        return TenantConfig(
            tenant_id="test_tenant",
            name="Test Tenant",
            features={
                "multi_language": True,
                "real_time_transcription": True,
                "call_recording": True,
                "webhook_support": True,
                "custom_branding": True,
                "advanced_analytics": False,
                "ai_powered_features": False
            },
            providers={
                "vapi": {"enabled": True, "priority": 1},
                "vonage": {"enabled": True, "priority": 2}
            },
            branding={
                "primary_color": "#1f2937",
                "secondary_color": "#f59e0b",
                "company_name": "Test Company"
            },
            modules=["analytics", "compliance"],
            workflows={
                "sales": "sales_workflow_v1",
                "support": "support_workflow_v1"
            },
            settings={
                "max_concurrent_calls": 100,
                "data_retention_days": 30
            }
        )
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, storage_backend):
        """Test configuration engine initialization"""
        engine = ConfigurationEngine(storage_backend)
        
        assert engine._cache == {}
        assert engine._cache_ttl == {}
        assert engine._feature_flags == {}
        assert engine._config_watchers == {}
        assert engine._validation_schemas == {}
        assert engine._config_hashes == {}
        
        await engine.start()
        assert engine._default_config is not None
        assert engine._system_config is not None
        assert "global" in engine._feature_flags
        assert "tenant_config" in engine._validation_schemas
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_get_tenant_config_new_tenant(self, config_engine):
        """Test getting configuration for new tenant"""
        config_engine = await config_engine
        config = await config_engine.get_tenant_config("new_tenant")
        
        assert config.tenant_id == "new_tenant"
        assert config.name == "Tenant new_tenant"
        assert len(config.features) > 0
        assert len(config.providers) >= 0
        assert len(config.branding) > 0
    
    @pytest.mark.asyncio
    async def test_get_tenant_config_existing_tenant(self, config_engine, sample_tenant_config):
        """Test getting configuration for existing tenant"""
        config_engine = await config_engine
        # Save configuration first
        await config_engine.update_tenant_config("test_tenant", sample_tenant_config)
        
        # Get configuration
        config = await config_engine.get_tenant_config("test_tenant")
        
        assert config.tenant_id == "test_tenant"
        assert config.name == "Test Tenant"
        assert config.features["multi_language"] is True
        assert config.features["call_recording"] is True
        assert "vapi" in config.providers
        assert config.branding["company_name"] == "Test Company"
    
    @pytest.mark.asyncio
    async def test_configuration_inheritance(self, config_engine, sample_tenant_config):
        """Test configuration inheritance from default configuration"""
        config_engine = await config_engine
        # Update default configuration
        default_config = config_engine._default_config
        default_config.features["new_feature"] = True
        default_config.settings["default_setting"] = "default_value"
        
        # Create tenant config without these features
        tenant_config = TenantConfig(
            tenant_id="inherit_test",
            name="Inheritance Test",
            features={"custom_feature": True},
            providers={},
            branding={},
            modules=[],
            workflows={},
            settings={"custom_setting": "custom_value"}
        )
        
        await config_engine.update_tenant_config("inherit_test", tenant_config)
        
        # Get configuration and check inheritance
        config = await config_engine.get_tenant_config("inherit_test")
        
        # Should inherit from default
        assert config.features["new_feature"] is True
        assert config.settings["default_setting"] == "default_value"
        
        # Should have tenant-specific values
        assert config.features["custom_feature"] is True
        assert config.settings["custom_setting"] == "custom_value"
    
    @pytest.mark.asyncio
    async def test_feature_flags(self, config_engine):
        """Test feature flag functionality"""
        config_engine = await config_engine
        # Set feature flag
        await config_engine.set_feature_flag("test_tenant", "advanced_analytics", True)
        await config_engine.set_feature_flag("test_tenant", "ai_powered_features", False)
        
        # Get individual feature flags
        assert await config_engine.get_feature_flag("test_tenant", "advanced_analytics") is True
        assert await config_engine.get_feature_flag("test_tenant", "ai_powered_features") is False
        
        # Get all feature flags
        all_flags = await config_engine.get_all_feature_flags("test_tenant")
        assert all_flags["advanced_analytics"] is True
        assert all_flags["ai_powered_features"] is False
        assert "multi_provider_support" in all_flags  # Global flag
    
    @pytest.mark.asyncio
    async def test_feature_flags_application(self, config_engine, sample_tenant_config):
        """Test that feature flags are applied to configuration"""
        config_engine = await config_engine
        # Set feature flag
        await config_engine.set_feature_flag("test_tenant", "advanced_analytics", True)
        
        # Save configuration with feature flag set to False
        sample_tenant_config.features["advanced_analytics"] = False
        await config_engine.update_tenant_config("test_tenant", sample_tenant_config)
        
        # Get configuration - feature flag should override
        config = await config_engine.get_tenant_config("test_tenant")
        assert config.features["advanced_analytics"] is True
    
    @pytest.mark.asyncio
    async def test_configuration_validation(self, config_engine):
        """Test configuration validation"""
        config_engine = await config_engine
        # Valid configuration
        valid_config = TenantConfig(
            tenant_id="valid_tenant",
            name="Valid Tenant",
            features={},
            providers={},
            branding={},
            modules=[],
            workflows={},
            settings={"max_concurrent_calls": 100}
        )
        
        # Should not raise validation errors
        success = await config_engine.update_tenant_config("valid_tenant", valid_config)
        assert success is True
        
        # Invalid configuration - missing required fields
        invalid_config = TenantConfig(
            tenant_id="",  # Empty tenant_id
            name="",  # Empty name
            features={},
            providers={},
            branding={},
            modules=[],
            workflows={},
            settings={}
        )
        
        # Should return False for validation errors
        success = await config_engine.update_tenant_config("invalid_tenant", invalid_config)
        assert success is False
        
        # Invalid configuration - business rule violation
        invalid_business_config = TenantConfig(
            tenant_id="business_invalid",
            name="Business Invalid",
            features={},
            providers={},
            branding={},
            modules=[],
            workflows={},
            settings={"max_concurrent_calls": 15000}  # Exceeds limit
        )
        
        # Should return False for business rule violations
        success = await config_engine.update_tenant_config("business_invalid", invalid_business_config)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_configuration_export_import(self, config_engine, sample_tenant_config):
        """Test configuration export and import"""
        config_engine = await config_engine
        
        # Create a configuration with the correct tenant ID
        export_config = TenantConfig(
            tenant_id="export_test",
            name="Export Test Tenant",
            features=sample_tenant_config.features,
            providers=sample_tenant_config.providers,
            branding=sample_tenant_config.branding,
            modules=sample_tenant_config.modules,
            workflows=sample_tenant_config.workflows,
            settings=sample_tenant_config.settings
        )
        
        # Save configuration
        await config_engine.update_tenant_config("export_test", export_config)
        
        # Export as JSON
        json_export = await config_engine.export_config("export_test", "json")
        assert isinstance(json_export, str)
        exported_data = json.loads(json_export)
        assert exported_data["tenant_id"] == "export_test"
        assert exported_data["name"] == "Export Test Tenant"
        
        # Export as YAML
        yaml_export = await config_engine.export_config("export_test", "yaml")
        assert isinstance(yaml_export, str)
        exported_data = yaml.safe_load(yaml_export)
        assert exported_data["tenant_id"] == "export_test"
        
        # Import configuration
        new_tenant_config = TenantConfig(
            tenant_id="import_test",
            name="Import Test",
            features={"imported_feature": True},
            providers={},
            branding={},
            modules=[],
            workflows={},
            settings={}
        )
        
        # Export and import
        export_data = await config_engine.export_config("export_test", "json")
        success = await config_engine.import_config("import_test", export_data, "json")
        assert success is True
        
        # Verify imported configuration
        imported_config = await config_engine.get_tenant_config("import_test")
        assert imported_config.tenant_id == "import_test"  # Should be updated
        assert imported_config.name == "Export Test Tenant"
        assert imported_config.features["multi_language"] is True
    
    @pytest.mark.asyncio
    async def test_configuration_watchers(self, config_engine):
        """Test configuration watchers"""
        config_engine = await config_engine
        watcher_called = False
        watcher_tenant_id = None
        watcher_config = None
        
        async def config_watcher(tenant_id: str, config: TenantConfig):
            nonlocal watcher_called, watcher_tenant_id, watcher_config
            watcher_called = True
            watcher_tenant_id = tenant_id
            watcher_config = config
        
        # Add watcher
        await config_engine.add_config_watcher("watcher_test", config_watcher)
        
        # Update configuration
        test_config = TenantConfig(
            tenant_id="watcher_test",
            name="Watcher Test",
            features={},
            providers={},
            branding={},
            modules=[],
            workflows={},
            settings={}
        )
        
        await config_engine.update_tenant_config("watcher_test", test_config)
        
        # Wait for watcher to be called
        await asyncio.sleep(0.1)
        
        assert watcher_called is True
        assert watcher_tenant_id == "watcher_test"
        assert watcher_config.tenant_id == "watcher_test"
        
        # Remove watcher
        await config_engine.remove_config_watcher("watcher_test", config_watcher)
        
        # Update again - watcher should not be called
        watcher_called = False
        test_config.name = "Updated Watcher Test"
        await config_engine.update_tenant_config("watcher_test", test_config)
        
        await asyncio.sleep(0.1)
        assert watcher_called is False
    
    @pytest.mark.asyncio
    async def test_configuration_caching(self, config_engine, sample_tenant_config):
        """Test configuration caching"""
        config_engine = await config_engine
        
        # Create a configuration with the correct tenant ID
        cache_config = TenantConfig(
            tenant_id="cache_test",
            name="Cache Test Tenant",
            features=sample_tenant_config.features,
            providers=sample_tenant_config.providers,
            branding=sample_tenant_config.branding,
            modules=sample_tenant_config.modules,
            workflows=sample_tenant_config.workflows,
            settings=sample_tenant_config.settings
        )
        
        # Save configuration
        await config_engine.update_tenant_config("cache_test", cache_config)
        
        # First get - should load from storage
        config1 = await config_engine.get_tenant_config("cache_test")
        assert "cache_test" in config_engine._cache
        
        # Second get - should load from cache
        config2 = await config_engine.get_tenant_config("cache_test")
        assert config1.tenant_id == config2.tenant_id
        
        # Clear cache
        await config_engine.clear_cache("cache_test")
        assert "cache_test" not in config_engine._cache
        
        # Get again - should load from storage
        config3 = await config_engine.get_tenant_config("cache_test")
        assert config3.tenant_id == "cache_test"
    
    @pytest.mark.asyncio
    async def test_configuration_hash_detection(self, config_engine, sample_tenant_config):
        """Test configuration hash detection for change detection"""
        config_engine = await config_engine
        # Save configuration
        await config_engine.update_tenant_config("hash_test", sample_tenant_config)
        
        # Get hash
        original_hash = config_engine._config_hashes.get("hash_test")
        assert original_hash is not None
        
        # Update with same configuration - should skip update
        with patch.object(config_engine.storage, 'set') as mock_set:
            await config_engine.update_tenant_config("hash_test", sample_tenant_config)
            mock_set.assert_not_called()
        
        # Update with different configuration - should update
        sample_tenant_config.name = "Updated Hash Test"
        with patch.object(config_engine.storage, 'set') as mock_set:
            await config_engine.update_tenant_config("hash_test", sample_tenant_config)
            mock_set.assert_called_once()
        
        # Hash should be updated
        new_hash = config_engine._config_hashes.get("hash_test")
        assert new_hash != original_hash
    
    @pytest.mark.asyncio
    async def test_configuration_summary(self, config_engine, sample_tenant_config):
        """Test configuration summary generation"""
        config_engine = await config_engine
        
        # Create a configuration with the correct tenant ID
        summary_config = TenantConfig(
            tenant_id="summary_test",
            name="Summary Test Tenant",
            features=sample_tenant_config.features,
            providers=sample_tenant_config.providers,
            branding=sample_tenant_config.branding,
            modules=sample_tenant_config.modules,
            workflows=sample_tenant_config.workflows,
            settings=sample_tenant_config.settings
        )
        
        # Save configuration
        await config_engine.update_tenant_config("summary_test", summary_config)
        
        # Set feature flags
        await config_engine.set_feature_flag("summary_test", "advanced_analytics", True)
        
        # Get summary
        summary = await config_engine.get_config_summary("summary_test")
        
        assert summary["tenant_id"] == "summary_test"
        assert summary["name"] == "Summary Test Tenant"
        assert summary["features_count"] > 0
        assert summary["providers_count"] > 0
        assert summary["modules_count"] > 0
        assert summary["workflows_count"] > 0
        assert summary["feature_flags_count"] > 0
        assert "last_updated" in summary
        assert summary["cache_status"] in ["cached", "not_cached"]
    
    @pytest.mark.asyncio
    async def test_configuration_statistics(self, config_engine):
        """Test configuration engine statistics"""
        config_engine = await config_engine
        stats = await config_engine.get_config_statistics()
        
        assert "cached_tenants" in stats
        assert "total_watchers" in stats
        assert "feature_flags_tenants" in stats
        assert "validation_schemas" in stats
        assert "cache_hit_ratio" in stats
        assert "uptime" in stats
        
        assert isinstance(stats["cached_tenants"], int)
        assert isinstance(stats["total_watchers"], int)
        assert isinstance(stats["validation_schemas"], int)
        assert isinstance(stats["cache_hit_ratio"], float)
        assert isinstance(stats["uptime"], str)
    
    @pytest.mark.asyncio
    async def test_system_config_management(self, config_engine):
        """Test system configuration management"""
        config_engine = await config_engine
        # Get current system config
        system_config = await config_engine.get_system_config()
        assert system_config is not None
        assert system_config.system_id == "kasaai"
        
        # Update system config
        new_system_config = SystemConfig(
            system_id="kasaai",
            environment="testing",
            debug_mode=True,
            log_level="debug",
            max_concurrent_calls=500,
            max_call_duration=1800,
            data_retention_days=30,
            backup_enabled=True,
            backup_interval_hours=12,
            monitoring_enabled=True,
            alerting_enabled=True,
            maintenance_window={},
            security_settings={},
            performance_settings={}
        )
        
        success = await config_engine.update_system_config(new_system_config)
        assert success is True
        
        # Verify update
        updated_config = await config_engine.get_system_config()
        assert updated_config.environment == "testing"
        assert updated_config.debug_mode is True
        assert updated_config.log_level == "debug"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, config_engine):
        """Test error handling in configuration engine"""
        config_engine = await config_engine
        # Test invalid export format
        result = await config_engine.export_config("test", "invalid_format")
        assert result == ""
        
        # Test invalid import format
        success = await config_engine.import_config("test", "{}", "invalid_format")
        assert success is False
        
        # Test invalid JSON import
        success = await config_engine.import_config("test", "invalid json", "json")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, config_engine, sample_tenant_config):
        """Test concurrent access to configuration engine"""
        config_engine = await config_engine
        
        # Create a configuration with the correct tenant ID
        concurrent_config = TenantConfig(
            tenant_id="concurrent_test",
            name="Concurrent Test Tenant",
            features=sample_tenant_config.features,
            providers=sample_tenant_config.providers,
            branding=sample_tenant_config.branding,
            modules=sample_tenant_config.modules,
            workflows=sample_tenant_config.workflows,
            settings=sample_tenant_config.settings
        )
        
        # Save configuration
        await config_engine.update_tenant_config("concurrent_test", concurrent_config)
        
        # Create multiple concurrent tasks
        async def get_config():
            return await config_engine.get_tenant_config("concurrent_test")
        
        # Run concurrent gets
        tasks = [get_config() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All results should be the same
        for result in results:
            assert result.tenant_id == "concurrent_test"
            assert result.name == "Concurrent Test Tenant"
    
    @pytest.mark.asyncio
    async def test_configuration_persistence(self, storage_backend):
        """Test configuration persistence across engine restarts"""
        # Create engine and save configuration
        engine1 = ConfigurationEngine(storage_backend)
        await engine1.start()
        
        test_config = TenantConfig(
            tenant_id="persistence_test",
            name="Persistence Test",
            features={"persistent_feature": True},
            providers={},
            branding={},
            modules=[],
            workflows={},
            settings={}
        )
        
        await engine1.update_tenant_config("persistence_test", test_config)
        await engine1.stop()
        
        # Create new engine and verify persistence
        engine2 = ConfigurationEngine(storage_backend)
        await engine2.start()
        
        config = await engine2.get_tenant_config("persistence_test")
        assert config.tenant_id == "persistence_test"
        assert config.features["persistent_feature"] is True
        
        await engine2.stop()


class TestConfigurationEngineIntegration:
    """Integration tests for ConfigurationEngine"""
    
    @pytest.fixture
    def storage_backend(self):
        """Create memory storage backend for testing"""
        return SimpleStorageAdapter()
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, storage_backend):
        """Test complete configuration workflow"""
        engine = ConfigurationEngine(storage_backend)
        await engine.start()
        
        # 1. Create tenant configuration
        config = TenantConfig(
            tenant_id="workflow_test",
            name="Workflow Test",
            features={"feature1": True, "feature2": False, "feature3": False},
            providers={"vapi": {"enabled": True}},
            branding={"company_name": "Workflow Company"},
            modules=["module1"],
            workflows={"workflow1": "config1"},
            settings={"setting1": "value1"}
        )
        
        # 2. Save configuration
        success = await engine.update_tenant_config("workflow_test", config)
        assert success is True
        
        # 3. Set feature flags
        await engine.set_feature_flag("workflow_test", "feature2", True)
        await engine.set_feature_flag("workflow_test", "feature3", True)
        
        # 4. Get configuration with inheritance and feature flags
        final_config = await engine.get_tenant_config("workflow_test")
        assert final_config.features["feature1"] is True
        assert final_config.features["feature2"] is True  # Overridden by feature flag
        assert final_config.features["feature3"] is True  # Added by feature flag
        
        # 5. Export configuration
        export_data = await engine.export_config("workflow_test", "json")
        exported_config = json.loads(export_data)
        assert exported_config["tenant_id"] == "workflow_test"
        
        # 6. Import to new tenant
        success = await engine.import_config("workflow_test2", export_data, "json")
        assert success is True
        
        # 7. Verify imported configuration
        imported_config = await engine.get_tenant_config("workflow_test2")
        assert imported_config.tenant_id == "workflow_test2"
        assert imported_config.name == "Workflow Test"
        
        # 8. Get summary and statistics
        summary = await engine.get_config_summary("workflow_test")
        assert summary["tenant_id"] == "workflow_test"
        
        stats = await engine.get_config_statistics()
        assert stats["cached_tenants"] >= 2
        
        await engine.stop()
