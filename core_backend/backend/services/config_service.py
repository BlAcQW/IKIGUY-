"""
Configuration service that integrates shared configuration management library.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID
import logging

from apps.shared.config import ConfigurationEngine, TenantConfig, SystemConfig, FeatureFlags
from apps.shared.storage import MemoryStorageBackend

logger = logging.getLogger(__name__)


class ConfigService:
    """Service for managing configuration using shared libraries."""

    def __init__(self, storage_backend=None):
        """
        Initialize the configuration service.

        Args:
            storage_backend: Storage backend for configuration data. Defaults to in-memory.
        """
        if storage_backend is None:
            from apps.shared.storage.interfaces import StorageConfig
            config = StorageConfig(backend_type="memory", connection_string="memory://")
            storage_backend = MemoryStorageBackend(config)
        
        self.config_engine = ConfigurationEngine(storage_backend)
        # Note: _ensure_initialized will be called when needed

    async def _ensure_initialized(self):
        """Ensure the configuration engine is initialized."""
        try:
            await self.config_engine.get_tenant_config("test")
        except Exception:
            # This will trigger initialization
            pass

    async def get_tenant_config(
        self,
        tenant_id: str
    ) -> Optional[TenantConfig]:
        """
        Get tenant configuration.

        Args:
            tenant_id: Tenant identifier

        Returns:
            TenantConfig: Tenant configuration
        """
        try:
            return await self.config_engine.get_tenant_config(tenant_id)
        except Exception as e:
            logger.error(f"Failed to get tenant config: {e}")
            return None

    async def update_tenant_config(
        self,
        tenant_id: str,
        config: TenantConfig
    ) -> bool:
        """
        Update tenant configuration.

        Args:
            tenant_id: Tenant identifier
            config: New configuration

        Returns:
            bool: True if update was successful
        """
        try:
            return await self.config_engine.update_tenant_config(tenant_id, config)
        except Exception as e:
            logger.error(f"Failed to update tenant config: {e}")
            return False

    async def get_system_config(self) -> Optional[SystemConfig]:
        """
        Get system configuration.

        Returns:
            SystemConfig: System configuration
        """
        try:
            return await self.config_engine.get_system_config()
        except Exception as e:
            logger.error(f"Failed to get system config: {e}")
            return None

    async def update_system_config(
        self,
        config: SystemConfig
    ) -> bool:
        """
        Update system configuration.

        Args:
            config: New system configuration

        Returns:
            bool: True if update was successful
        """
        try:
            return await self.config_engine.update_system_config(config)
        except Exception as e:
            logger.error(f"Failed to update system config: {e}")
            return False

    async def get_feature_flags(
        self,
        tenant_id: str
    ) -> Optional[Dict[str, bool]]:
        """
        Get feature flags for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dict[str, bool]: Feature flags configuration
        """
        try:
            return await self.config_engine.get_all_feature_flags(tenant_id)
        except Exception as e:
            logger.error(f"Failed to get feature flags: {e}")
            return None

    async def update_feature_flags(
        self,
        tenant_id: str,
        flags: FeatureFlags
    ) -> bool:
        """
        Update feature flags for a tenant.

        Args:
            tenant_id: Tenant identifier
            flags: New feature flags

        Returns:
            bool: True if update was successful
        """
        try:
            # Convert FeatureFlags to individual flag updates
            success = True
            for field_name, value in flags.model_dump().items():
                if isinstance(value, bool):
                    flag_success = await self.config_engine.set_feature_flag(tenant_id, field_name, value)
                    if not flag_success:
                        success = False
            return success
        except Exception as e:
            logger.error(f"Failed to update feature flags: {e}")
            return False

    async def is_feature_enabled(
        self,
        tenant_id: str,
        feature: str
    ) -> bool:
        """
        Check if a feature is enabled for a tenant.

        Args:
            tenant_id: Tenant identifier
            feature: Feature to check

        Returns:
            bool: True if feature is enabled
        """
        try:
            return await self.config_engine.get_feature_flag(tenant_id, feature)
        except Exception as e:
            logger.error(f"Failed to check feature enabled: {e}")
            return False

    async def get_config_summary(
        self,
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Get configuration summary for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dict[str, Any]: Configuration summary
        """
        try:
            return await self.config_engine.get_config_summary(tenant_id)
        except Exception as e:
            logger.error(f"Failed to get config summary: {e}")
            return {}

    async def export_config(
        self,
        tenant_id: str,
        format: str = "json"
    ) -> str:
        """
        Export configuration for a tenant.

        Args:
            tenant_id: Tenant identifier
            format: Export format (json, yaml)

        Returns:
            str: Exported configuration
        """
        try:
            return await self.config_engine.export_config(tenant_id, format)
        except Exception as e:
            logger.error(f"Failed to export config: {e}")
            return ""

    async def import_config(
        self,
        tenant_id: str,
        data: str,
        format: str = "json"
    ) -> bool:
        """
        Import configuration for a tenant.

        Args:
            tenant_id: Tenant identifier
            data: Configuration data to import
            format: Import format (json, yaml)

        Returns:
            bool: True if import was successful
        """
        try:
            return await self.config_engine.import_config(tenant_id, data, format)
        except Exception as e:
            logger.error(f"Failed to import config: {e}")
            return False

    async def validate_config(
        self,
        tenant_id: str
    ) -> bool:
        """
        Validate configuration for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            bool: True if configuration is valid
        """
        try:
            return await self.config_engine.validate_config(tenant_id)
        except Exception as e:
            logger.error(f"Failed to validate config: {e}")
            return False

    async def get_config_history(
        self,
        tenant_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get configuration history for a tenant.

        Args:
            tenant_id: Tenant identifier
            limit: Number of history entries to return

        Returns:
            List[Dict[str, Any]]: Configuration history
        """
        try:
            return await self.config_engine.get_config_history(tenant_id, limit)
        except Exception as e:
            logger.error(f"Failed to get config history: {e}")
            return []

    async def rollback_config(
        self,
        tenant_id: str,
        version: str
    ) -> bool:
        """
        Rollback configuration to a previous version.

        Args:
            tenant_id: Tenant identifier
            version: Version to rollback to

        Returns:
            bool: True if rollback was successful
        """
        try:
            return await self.config_engine.rollback_config(tenant_id, version)
        except Exception as e:
            logger.error(f"Failed to rollback config: {e}")
            return False

    async def get_config_watchers(
        self,
        tenant_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get configuration watchers for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List[Dict[str, Any]]: Configuration watchers
        """
        try:
            return await self.config_engine.get_config_watchers(tenant_id)
        except Exception as e:
            logger.error(f"Failed to get config watchers: {e}")
            return []

    async def add_config_watcher(
        self,
        tenant_id: str,
        callback_url: str,
        events: List[str]
    ) -> bool:
        """
        Add a configuration watcher for a tenant.

        Args:
            tenant_id: Tenant identifier
            callback_url: URL to call when configuration changes
            events: List of events to watch for

        Returns:
            bool: True if watcher was added successfully
        """
        try:
            return await self.config_engine.add_config_watcher(
                tenant_id, callback_url, events
            )
        except Exception as e:
            logger.error(f"Failed to add config watcher: {e}")
            return False

    async def remove_config_watcher(
        self,
        tenant_id: str,
        watcher_id: str
    ) -> bool:
        """
        Remove a configuration watcher for a tenant.

        Args:
            tenant_id: Tenant identifier
            watcher_id: Watcher identifier

        Returns:
            bool: True if watcher was removed successfully
        """
        try:
            return await self.config_engine.remove_config_watcher(tenant_id, watcher_id)
        except Exception as e:
            logger.error(f"Failed to remove config watcher: {e}")
            return False
