"""
Module service that integrates shared module system library.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID
import logging

from config.module_system import ModuleSystemManager, ModuleSystemRegistry, ModuleSystemLoader
from config.interfaces import ModuleInfo, ModuleInstance
from storage.memory import MemoryStorageBackend

logger = logging.getLogger(__name__)


class ModuleService:
    """Service for module management using shared libraries."""

    def __init__(self, storage_backend=None):
        """
        Initialize the module service.

        Args:
            storage_backend: Storage backend for module data. Defaults to in-memory.
        """
        if storage_backend is None:
            from storage.interfaces import StorageConfig
            config = StorageConfig(backend_type="memory", connection_string="memory://")
            storage_backend = MemoryStorageBackend(config)
        
        self.registry = ModuleSystemRegistry(storage_backend)
        self.loader = ModuleSystemLoader(storage_backend)
        self.module_manager = ModuleSystemManager(self.registry, self.loader, storage_backend)
        # Note: _ensure_initialized will be called when needed

    async def _ensure_initialized(self):
        """Ensure the module manager is initialized."""
        try:
            await self.module_manager.get_available_modules()
        except Exception:
            # This will trigger initialization
            pass

    async def register_module(
        self,
        module_info: ModuleInfo
    ) -> bool:
        """
        Register a module.

        Args:
            module_info: Module information

        Returns:
            bool: True if module was registered successfully
        """
        try:
            return await self.module_manager.register_module(module_info)
        except Exception as e:
            logger.error(f"Failed to register module: {e}")
            return False

    async def unregister_module(
        self,
        module_id: str
    ) -> bool:
        """
        Unregister a module.

        Args:
            module_id: Module identifier

        Returns:
            bool: True if module was unregistered successfully
        """
        try:
            return await self.module_manager.unregister_module(module_id)
        except Exception as e:
            logger.error(f"Failed to unregister module: {e}")
            return False

    async def get_available_modules(self) -> List[ModuleInfo]:
        """
        Get all available modules.

        Returns:
            List[ModuleInfo]: List of available modules
        """
        try:
            return await self.module_manager.get_available_modules()
        except Exception as e:
            logger.error(f"Failed to get available modules: {e}")
            return []

    async def get_module_info(
        self,
        module_id: str
    ) -> Optional[ModuleInfo]:
        """
        Get module information.

        Args:
            module_id: Module identifier

        Returns:
            ModuleInfo: Module information
        """
        try:
            return await self.module_manager.get_module_info(module_id)
        except Exception as e:
            logger.error(f"Failed to get module info: {e}")
            return None

    async def create_module_instance(
        self,
        tenant_id: str,
        module_id: str,
        instance_name: str,
        configuration: Optional[Dict[str, Any]] = None
    ) -> Optional[ModuleInstance]:
        """
        Create a module instance for a tenant.

        Args:
            tenant_id: Tenant identifier
            module_id: Module identifier
            instance_name: Instance name
            configuration: Instance configuration

        Returns:
            ModuleInstance: Created module instance
        """
        try:
            return await self.module_manager.create_instance(
                tenant_id, module_id, instance_name, configuration
            )
        except Exception as e:
            logger.error(f"Failed to create module instance: {e}")
            return None

    async def destroy_module_instance(
        self,
        tenant_id: str,
        instance_id: str
    ) -> bool:
        """
        Destroy a module instance.

        Args:
            tenant_id: Tenant identifier
            instance_id: Instance identifier

        Returns:
            bool: True if instance was destroyed successfully
        """
        try:
            return await self.module_manager.destroy_instance(tenant_id, instance_id)
        except Exception as e:
            logger.error(f"Failed to destroy module instance: {e}")
            return False

    async def get_tenant_instances(
        self,
        tenant_id: str
    ) -> List[ModuleInstance]:
        """
        Get all module instances for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List[ModuleInstance]: List of module instances
        """
        try:
            return await self.module_manager.get_tenant_instances(tenant_id)
        except Exception as e:
            logger.error(f"Failed to get tenant instances: {e}")
            return []

    async def get_instance_info(
        self,
        tenant_id: str,
        instance_id: str
    ) -> Optional[ModuleInstance]:
        """
        Get module instance information.

        Args:
            tenant_id: Tenant identifier
            instance_id: Instance identifier

        Returns:
            ModuleInstance: Module instance information
        """
        try:
            return await self.module_manager.get_instance_info(tenant_id, instance_id)
        except Exception as e:
            logger.error(f"Failed to get instance info: {e}")
            return None

    async def update_instance_configuration(
        self,
        tenant_id: str,
        instance_id: str,
        configuration: Dict[str, Any]
    ) -> bool:
        """
        Update module instance configuration.

        Args:
            tenant_id: Tenant identifier
            instance_id: Instance identifier
            configuration: New configuration

        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            return await self.module_manager.update_instance_configuration(
                tenant_id, instance_id, configuration
            )
        except Exception as e:
            logger.error(f"Failed to update instance configuration: {e}")
            return False

    async def start_instance(
        self,
        tenant_id: str,
        instance_id: str
    ) -> bool:
        """
        Start a module instance.

        Args:
            tenant_id: Tenant identifier
            instance_id: Instance identifier

        Returns:
            bool: True if instance was started successfully
        """
        try:
            return await self.module_manager.start_instance(tenant_id, instance_id)
        except Exception as e:
            logger.error(f"Failed to start instance: {e}")
            return False

    async def stop_instance(
        self,
        tenant_id: str,
        instance_id: str
    ) -> bool:
        """
        Stop a module instance.

        Args:
            tenant_id: Tenant identifier
            instance_id: Instance identifier

        Returns:
            bool: True if instance was stopped successfully
        """
        try:
            return await self.module_manager.stop_instance(tenant_id, instance_id)
        except Exception as e:
            logger.error(f"Failed to stop instance: {e}")
            return False

    async def restart_instance(
        self,
        tenant_id: str,
        instance_id: str
    ) -> bool:
        """
        Restart a module instance.

        Args:
            tenant_id: Tenant identifier
            instance_id: Instance identifier

        Returns:
            bool: True if instance was restarted successfully
        """
        try:
            return await self.module_manager.restart_instance(tenant_id, instance_id)
        except Exception as e:
            logger.error(f"Failed to restart instance: {e}")
            return False

    async def get_instance_status(
        self,
        tenant_id: str,
        instance_id: str
    ) -> Dict[str, Any]:
        """
        Get module instance status.

        Args:
            tenant_id: Tenant identifier
            instance_id: Instance identifier

        Returns:
            Dict[str, Any]: Instance status
        """
        try:
            return await self.module_manager.get_instance_status(tenant_id, instance_id)
        except Exception as e:
            logger.error(f"Failed to get instance status: {e}")
            return {}

    async def resolve_dependencies(
        self,
        module_id: str
    ) -> List[str]:
        """
        Resolve module dependencies.

        Args:
            module_id: Module identifier

        Returns:
            List[str]: List of dependency module IDs
        """
        try:
            return await self.module_manager.resolve_dependencies(module_id)
        except Exception as e:
            logger.error(f"Failed to resolve dependencies: {e}")
            return []

    async def check_compatibility(
        self,
        module_id: str,
        target_module_id: str
    ) -> bool:
        """
        Check module compatibility.

        Args:
            module_id: Module identifier
            target_module_id: Target module identifier

        Returns:
            bool: True if modules are compatible
        """
        try:
            return await self.module_manager.check_compatibility(module_id, target_module_id)
        except Exception as e:
            logger.error(f"Failed to check compatibility: {e}")
            return False

    async def get_module_dependencies(
        self,
        module_id: str
    ) -> List[str]:
        """
        Get module dependencies.

        Args:
            module_id: Module identifier

        Returns:
            List[str]: List of dependency module IDs
        """
        try:
            return await self.module_manager.get_module_dependencies(module_id)
        except Exception as e:
            logger.error(f"Failed to get module dependencies: {e}")
            return []

    async def get_module_dependents(
        self,
        module_id: str
    ) -> List[str]:
        """
        Get modules that depend on this module.

        Args:
            module_id: Module identifier

        Returns:
            List[str]: List of dependent module IDs
        """
        try:
            return await self.module_manager.get_module_dependents(module_id)
        except Exception as e:
            logger.error(f"Failed to get module dependents: {e}")
            return []

    async def validate_module_configuration(
        self,
        module_id: str,
        configuration: Dict[str, Any]
    ) -> bool:
        """
        Validate module configuration.

        Args:
            module_id: Module identifier
            configuration: Configuration to validate

        Returns:
            bool: True if configuration is valid
        """
        try:
            return await self.module_manager.validate_module_configuration(
                module_id, configuration
            )
        except Exception as e:
            logger.error(f"Failed to validate module configuration: {e}")
            return False

    async def get_module_metadata(
        self,
        module_id: str
    ) -> Dict[str, Any]:
        """
        Get module metadata.

        Args:
            module_id: Module identifier

        Returns:
            Dict[str, Any]: Module metadata
        """
        try:
            return await self.module_manager.get_module_metadata(module_id)
        except Exception as e:
            logger.error(f"Failed to get module metadata: {e}")
            return {}

    async def search_modules(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[ModuleInfo]:
        """
        Search for modules.

        Args:
            query: Search query
            category: Module category filter
            tags: Module tags filter

        Returns:
            List[ModuleInfo]: List of matching modules
        """
        try:
            return await self.module_manager.search_modules(query, category, tags)
        except Exception as e:
            logger.error(f"Failed to search modules: {e}")
            return []
