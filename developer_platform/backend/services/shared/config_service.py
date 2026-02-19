"""
Configuration service wrapper for Developer Platform using shared libraries.

This service integrates the shared configuration engine to provide
tenant-specific configuration management and feature flags.
"""

from typing import Dict, List, Optional, Any
import logging

# Use centralized import configuration
try:
    from ..import_config import get_config_engine, get_storage_backend
    ConfigurationEngine = get_config_engine()
    MemoryStorageBackend = get_storage_backend()
    from apps.shared.config import TenantConfig, SystemConfig, FeatureFlags
    from apps.shared.storage import StorageConfig
    SHARED_LIBRARIES_AVAILABLE = True
except ImportError as e:
    logging.error(f"SHARED LIBRARY IMPORT FAILURE - config: {e}")
    # Define fallback types for when shared libraries are not available
    from typing import TypedDict, Optional as OptionalType
    
    class TenantConfig(TypedDict):
        tenant_id: str
        settings: Dict[str, Any]
        features: List[str]
        created_at: str
        updated_at: str
    
    class SystemConfig(TypedDict):
        system_id: str
        settings: Dict[str, Any]
        version: str
    
    class FeatureFlags(TypedDict):
        tenant_id: str
        flags: Dict[str, bool]
        enabled_features: List[str]
    
    SHARED_LIBRARIES_AVAILABLE = False

logger = logging.getLogger(__name__)


class SharedConfigService:
    """Service for configuration management using shared libraries."""

    def __init__(self, storage_backend=None):
        """
        Initialize the configuration service.

        Args:
            storage_backend: Storage backend for configuration data. Defaults to in-memory.
        """
        if storage_backend is None:
            config = StorageConfig(backend_type="memory", connection_string="memory://")
            storage_backend = MemoryStorageBackend(config)
            
        self.storage = storage_backend
        # Initialize the configuration engine
        self.config_engine = ConfigurationEngine(storage_backend)

    async def _ensure_initialized(self):
        """Ensure the configuration service is initialized."""
        # Note: _ensure_initialized will be called when needed
        pass

    async def get_tenant_config(self, tenant_id: str) -> Optional[TenantConfig]:
        """
        Get configuration for a specific tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            TenantConfig: Tenant configuration or None if not found
        """
        await self._ensure_initialized()
        
        if not SHARED_LIBRARIES_AVAILABLE:
            # Fallback implementation
            return {
                "tenant_id": tenant_id,
                "settings": {"default": True},
                "features": ["basic"],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        
        try:
            config = await self.config_engine.get_tenant_config(tenant_id)
            return config
        except Exception as e:
            logger.error(f"Failed to get tenant config for {tenant_id}: {e}")
            return None

    async def update_tenant_config(self, tenant_id: str, config: TenantConfig) -> bool:
        """
        Update configuration for a specific tenant.

        Args:
            tenant_id: Tenant identifier
            config: New tenant configuration

        Returns:
            bool: True if update was successful
        """
        await self._ensure_initialized()
        
        try:
            success = await self.config_engine.update_tenant_config(tenant_id, config)
            if success:
                logger.info(f"Updated tenant config for {tenant_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to update tenant config for {tenant_id}: {e}")
            return False

    async def get_feature_flags(self, tenant_id: str) -> FeatureFlags:
        """
        Get feature flags for a specific tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            FeatureFlags: Feature flags for the tenant
        """
        await self._ensure_initialized()
        
        try:
            config = await self.get_tenant_config(tenant_id)
            if config and config.features:
                return config.features
            else:
                # Return default feature flags
                return FeatureFlags(
                    advanced_analytics=False,
                    ai_summarization=False,
                    multi_language=False,
                    custom_workflows=False
                )
        except Exception as e:
            logger.error(f"Failed to get feature flags for {tenant_id}: {e}")
            return FeatureFlags()

    async def is_feature_enabled(self, tenant_id: str, feature_name: str) -> bool:
        """
        Check if a specific feature is enabled for a tenant.

        Args:
            tenant_id: Tenant identifier
            feature_name: Name of the feature to check

        Returns:
            bool: True if feature is enabled
        """
        await self._ensure_initialized()
        
        try:
            flags = await self.get_feature_flags(tenant_id)
            return getattr(flags, feature_name, False)
        except Exception as e:
            logger.error(f"Failed to check feature {feature_name} for {tenant_id}: {e}")
            return False

    async def get_provider_config(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get provider configuration for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dict[str, Any]: Provider configuration
        """
        await self._ensure_initialized()
        
        try:
            config = await self.get_tenant_config(tenant_id)
            if config and hasattr(config, 'providers'):
                return config.providers
            else:
                # Return default provider config
                return {
                    "primary": "vapi",
                    "fallback": "sip",
                    "cost_optimization": True
                }
        except Exception as e:
            logger.error(f"Failed to get provider config for {tenant_id}: {e}")
            return {}

    async def get_branding_config(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get branding configuration for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dict[str, Any]: Branding configuration
        """
        await self._ensure_initialized()
        
        try:
            config = await self.get_tenant_config(tenant_id)
            if config and hasattr(config, 'branding'):
                return config.branding
            else:
                # Return default branding config
                return {
                    "logo_url": None,
                    "primary_color": "#1f2937",
                    "company_name": "KasaAI"
                }
        except Exception as e:
            logger.error(f"Failed to get branding config for {tenant_id}: {e}")
            return {}

    async def get_modules_config(self, tenant_id: str) -> List[str]:
        """
        Get enabled modules for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List[str]: List of enabled module names
        """
        await self._ensure_initialized()
        
        try:
            config = await self.get_tenant_config(tenant_id)
            if config and hasattr(config, 'modules'):
                return config.modules
            else:
                # Return default modules
                return ["core"]
        except Exception as e:
            logger.error(f"Failed to get modules config for {tenant_id}: {e}")
            return []

    async def export_config(self, tenant_id: str, format: str = "json") -> str:
        """
        Export tenant configuration.

        Args:
            tenant_id: Tenant identifier
            format: Export format (json, yaml)

        Returns:
            str: Exported configuration
        """
        await self._ensure_initialized()
        
        try:
            return await self.config_engine.export_config(tenant_id, format)
        except Exception as e:
            logger.error(f"Failed to export config for {tenant_id}: {e}")
            return ""

    async def import_config(self, tenant_id: str, config_data: str, format: str = "json") -> bool:
        """
        Import tenant configuration.

        Args:
            tenant_id: Tenant identifier
            config_data: Configuration data to import
            format: Import format (json, yaml)

        Returns:
            bool: True if import was successful
        """
        await self._ensure_initialized()
        
        try:
            success = await self.config_engine.import_config(tenant_id, config_data, format)
            if success:
                logger.info(f"Imported config for {tenant_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to import config for {tenant_id}: {e}")
            return False

    async def validate_config(self, config: TenantConfig) -> bool:
        """
        Validate a tenant configuration.

        Args:
            config: Configuration to validate

        Returns:
            bool: True if configuration is valid
        """
        await self._ensure_initialized()
        
        try:
            return await self.config_engine.validate_config(config)
        except Exception as e:
            logger.error(f"Failed to validate config: {e}")
            return False
