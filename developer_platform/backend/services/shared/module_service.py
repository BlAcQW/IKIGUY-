"""
Module service wrapper for Developer Platform using shared libraries.

This service integrates the shared module system to provide
module management and loading functionality for the Developer Platform.
"""

from typing import Dict, List, Optional, Any
import logging

# Use centralized import configuration
try:
    from ..import_config import get_module_engine, get_storage_backend
    ModuleSystemManager = get_module_engine()
    MemoryStorageBackend = get_storage_backend()
    from apps.shared.modules import ModuleInfo, ModuleInstance, ModuleSystemRegistry, ModuleSystemLoader
    from apps.shared.storage import StorageConfig
    SHARED_LIBRARIES_AVAILABLE = True
except ImportError as e:
    logging.error(f"SHARED LIBRARY IMPORT FAILURE - modules: {e}")
    # Define fallback types for when shared libraries are not available
    from typing import TypedDict, Optional as OptionalType
    
    class ModuleInfo(TypedDict):
        name: str
        version: str
        description: str
        dependencies: List[str]
        config_schema: Dict[str, Any]
    
    class ModuleInstance(TypedDict):
        module_id: str
        module_name: str
        tenant_id: str
        status: str
        config: Dict[str, Any]
        created_at: str
    
    class ModuleSystemRegistry:
        def __init__(self, storage):
            self.storage = storage
            self.modules = {}
    
    class ModuleSystemLoader:
        def __init__(self, storage):
            self.storage = storage
    
    class ModuleSystemManager:
        def __init__(self, registry, loader, storage):
            self.registry = registry
            self.loader = loader
            self.storage = storage
    
    class StorageConfig(TypedDict):
        backend_type: str
        connection_string: str
    
    class MemoryStorageBackend:
        def __init__(self, config):
            self.config = config
    
    SHARED_LIBRARIES_AVAILABLE = False

logger = logging.getLogger(__name__)


class SharedModuleService:
    """Service for module management using shared libraries."""

    def __init__(self, storage_backend=None):
        """
        Initialize the module service.

        Args:
            storage_backend: Storage backend for module data. Defaults to in-memory.
        """
        if storage_backend is None:
            config = StorageConfig(backend_type="memory", connection_string="memory://")
            storage_backend = MemoryStorageBackend(config)
            
        self.storage = storage_backend
        self.registry = ModuleSystemRegistry(storage_backend)
        self.loader = ModuleSystemLoader(storage_backend)
        self.manager = ModuleSystemManager(self.registry, self.loader, storage_backend)

    async def _ensure_initialized(self):
        """Ensure the module service is initialized."""
        # Note: _ensure_initialized will be called when needed
        pass

    async def load_module(self, module_name: str, tenant_id: str) -> Optional[ModuleInstance]:
        """
        Load a module for a tenant.

        Args:
            module_name: Name of the module to load
            tenant_id: Tenant identifier

        Returns:
            ModuleInstance: Loaded module instance or None if failed
        """
        await self._ensure_initialized()
        
        try:
            module_instance = await self.manager.load_module(module_name, tenant_id)
            if module_instance:
                logger.info(f"Loaded module {module_name} for tenant {tenant_id}")
            return module_instance
        except Exception as e:
            logger.error(f"Failed to load module {module_name} for tenant {tenant_id}: {e}")
            return None

    async def get_loaded_modules(self, tenant_id: str) -> List[ModuleInstance]:
        """
        Get all loaded modules for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List[ModuleInstance]: List of loaded module instances
        """
        await self._ensure_initialized()
        
        try:
            modules = await self.manager.get_loaded_modules(tenant_id)
            return modules
        except Exception as e:
            logger.error(f"Failed to get loaded modules for tenant {tenant_id}: {e}")
            return []

    async def unload_module(self, module_name: str, tenant_id: str) -> bool:
        """
        Unload a module for a tenant.

        Args:
            module_name: Name of the module to unload
            tenant_id: Tenant identifier

        Returns:
            bool: True if module was unloaded successfully
        """
        await self._ensure_initialized()
        
        try:
            success = await self.manager.unload_module(module_name, tenant_id)
            if success:
                logger.info(f"Unloaded module {module_name} for tenant {tenant_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to unload module {module_name} for tenant {tenant_id}: {e}")
            return False

    async def reload_module(self, module_name: str, tenant_id: str) -> Optional[ModuleInstance]:
        """
        Reload a module for a tenant.

        Args:
            module_name: Name of the module to reload
            tenant_id: Tenant identifier

        Returns:
            ModuleInstance: Reloaded module instance or None if failed
        """
        await self._ensure_initialized()
        
        try:
            module_instance = await self.manager.reload_module(module_name, tenant_id)
            if module_instance:
                logger.info(f"Reloaded module {module_name} for tenant {tenant_id}")
            return module_instance
        except Exception as e:
            logger.error(f"Failed to reload module {module_name} for tenant {tenant_id}: {e}")
            return None

    async def get_module_info(self, module_name: str) -> Optional[ModuleInfo]:
        """
        Get information about a module.

        Args:
            module_name: Name of the module

        Returns:
            ModuleInfo: Module information or None if not found
        """
        await self._ensure_initialized()
        
        try:
            module_info = await self.registry.get_module_info(module_name)
            return module_info
        except Exception as e:
            logger.error(f"Failed to get module info for {module_name}: {e}")
            return None

    async def list_available_modules(self, category: Optional[str] = None) -> List[ModuleInfo]:
        """
        List all available modules.

        Args:
            category: Optional category filter

        Returns:
            List[ModuleInfo]: List of available modules
        """
        await self._ensure_initialized()
        
        try:
            modules = await self.registry.list_modules(category=category)
            return modules
        except Exception as e:
            logger.error(f"Failed to list available modules: {e}")
            return []

    async def search_modules(self, query: str, category: Optional[str] = None) -> List[ModuleInfo]:
        """
        Search for modules.

        Args:
            query: Search query
            category: Optional category filter

        Returns:
            List[ModuleInfo]: List of matching modules
        """
        await self._ensure_initialized()
        
        try:
            modules = await self.registry.search_modules(query, category=category)
            return modules
        except Exception as e:
            logger.error(f"Failed to search modules with query '{query}': {e}")
            return []

    async def install_module(self, module_name: str, tenant_id: str) -> bool:
        """
        Install a module for a tenant.

        Args:
            module_name: Name of the module to install
            tenant_id: Tenant identifier

        Returns:
            bool: True if module was installed successfully
        """
        await self._ensure_initialized()
        
        try:
            success = await self.manager.install_module(module_name, tenant_id)
            if success:
                logger.info(f"Installed module {module_name} for tenant {tenant_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to install module {module_name} for tenant {tenant_id}: {e}")
            return False

    async def uninstall_module(self, module_name: str, tenant_id: str) -> bool:
        """
        Uninstall a module for a tenant.

        Args:
            module_name: Name of the module to uninstall
            tenant_id: Tenant identifier

        Returns:
            bool: True if module was uninstalled successfully
        """
        await self._ensure_initialized()
        
        try:
            success = await self.manager.uninstall_module(module_name, tenant_id)
            if success:
                logger.info(f"Uninstalled module {module_name} for tenant {tenant_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to uninstall module {module_name} for tenant {tenant_id}: {e}")
            return False

    async def enable_module(self, module_name: str, tenant_id: str) -> bool:
        """
        Enable a module for a tenant.

        Args:
            module_name: Name of the module to enable
            tenant_id: Tenant identifier

        Returns:
            bool: True if module was enabled successfully
        """
        await self._ensure_initialized()
        
        try:
            success = await self.manager.enable_module(module_name, tenant_id)
            if success:
                logger.info(f"Enabled module {module_name} for tenant {tenant_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to enable module {module_name} for tenant {tenant_id}: {e}")
            return False

    async def disable_module(self, module_name: str, tenant_id: str) -> bool:
        """
        Disable a module for a tenant.

        Args:
            module_name: Name of the module to disable
            tenant_id: Tenant identifier

        Returns:
            bool: True if module was disabled successfully
        """
        await self._ensure_initialized()
        
        try:
            success = await self.manager.disable_module(module_name, tenant_id)
            if success:
                logger.info(f"Disabled module {module_name} for tenant {tenant_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to disable module {module_name} for tenant {tenant_id}: {e}")
            return False

    async def get_module_status(self, module_name: str, tenant_id: str) -> Dict[str, Any]:
        """
        Get status of a module for a tenant.

        Args:
            module_name: Name of the module
            tenant_id: Tenant identifier

        Returns:
            Dict[str, Any]: Module status information
        """
        await self._ensure_initialized()
        
        try:
            status = await self.manager.get_module_status(module_name, tenant_id)
            return {
                "module_name": module_name,
                "tenant_id": tenant_id,
                "installed": status.installed,
                "enabled": status.enabled,
                "loaded": status.loaded,
                "error_message": status.error_message,
                "last_updated": status.last_updated
            }
        except Exception as e:
            logger.error(f"Failed to get module status for {module_name} and tenant {tenant_id}: {e}")
            return {
                "module_name": module_name,
                "tenant_id": tenant_id,
                "installed": False,
                "enabled": False,
                "loaded": False,
                "error_message": str(e),
                "last_updated": None
            }

    async def validate_module_dependencies(self, module_name: str, tenant_id: str) -> Dict[str, Any]:
        """
        Validate module dependencies for a tenant.

        Args:
            module_name: Name of the module
            tenant_id: Tenant identifier

        Returns:
            Dict[str, Any]: Dependency validation result
        """
        await self._ensure_initialized()
        
        try:
            validation = await self.manager.validate_dependencies(module_name, tenant_id)
            return {
                "valid": validation.valid,
                "missing_dependencies": validation.missing_dependencies,
                "conflicts": validation.conflicts,
                "warnings": validation.warnings
            }
        except Exception as e:
            logger.error(f"Failed to validate dependencies for {module_name} and tenant {tenant_id}: {e}")
            return {
                "valid": False,
                "missing_dependencies": [],
                "conflicts": [],
                "warnings": [str(e)]
            }
