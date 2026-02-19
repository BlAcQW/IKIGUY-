"""
Module System Implementation

This module provides the core module system implementation including registry,
loader, and manager functionality for dynamic module management.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
import importlib
import importlib.util
import sys
from dataclasses import asdict

from .interfaces import (
    ModuleRegistry, ModuleLoader, ModuleManager,
    ModuleInfo, ModuleInstance
)
from .models import ModuleConfig


class ModuleSystemRegistry(ModuleRegistry):
    """Module registry implementation"""
    
    def __init__(self, storage_backend: Any):
        """Initialize module registry"""
        self.storage = storage_backend
        self.logger = logging.getLogger("ModuleRegistry")
        self._modules: Dict[str, ModuleInfo] = {}
        self._module_cache: Dict[str, Any] = {}
        
    async def start(self):
        """Start the module registry"""
        self.logger.info("Starting module registry")
        await self._load_registered_modules()
        
    async def stop(self):
        """Stop the module registry"""
        self.logger.info("Stopping module registry")
        self._modules.clear()
        self._module_cache.clear()
        
    async def _load_registered_modules(self):
        """Load registered modules from storage"""
        try:
            modules_data = await self.storage.get("module_registry")
            if modules_data:
                if isinstance(modules_data, str):
                    modules_data = json.loads(modules_data)
                
                for module_id, module_dict in modules_data.items():
                    module_info = ModuleInfo(**module_dict)
                    self._modules[module_id] = module_info
                    
                self.logger.info(f"Loaded {len(self._modules)} registered modules")
            else:
                # Create default modules
                await self._create_default_modules()
                
        except Exception as e:
            self.logger.error(f"Failed to load registered modules: {e}")
            raise
            
    async def _create_default_modules(self):
        """Create default modules"""
        default_modules = [
            ModuleInfo(
                module_id="analytics",
                name="Analytics Module",
                version="1.0.0",
                description="Basic analytics and reporting functionality",
                author="KasaAI",
                license="MIT",
                dependencies=[],
                permissions=["analytics:read", "analytics:write"],
                features=["basic_analytics", "reporting"],
                api_endpoints=["/api/analytics/*"],
                ui_components=["AnalyticsDashboard", "ReportsView"],
                category="analytics",
                tags=["analytics", "reporting", "basic"]
            ),
            ModuleInfo(
                module_id="ai_features",
                name="AI Features Module",
                version="1.0.0",
                description="AI-powered features including summarization and sentiment analysis",
                author="KasaAI",
                license="MIT",
                dependencies=["analytics"],
                permissions=["ai:use", "ai:configure"],
                features=["call_summarization", "sentiment_analysis", "intelligent_routing"],
                api_endpoints=["/api/ai/*"],
                ui_components=["AIDashboard", "AIConfiguration"],
                category="ai",
                tags=["ai", "machine-learning", "nlp"]
            ),
            ModuleInfo(
                module_id="integrations",
                name="Integrations Module",
                version="1.0.0",
                description="Third-party integrations and API connections",
                author="KasaAI",
                license="MIT",
                dependencies=[],
                permissions=["integrations:manage", "integrations:use"],
                features=["crm_integration", "payment_gateway", "webhook_support"],
                api_endpoints=["/api/integrations/*"],
                ui_components=["IntegrationsManager", "APIConfiguration"],
                category="integrations",
                tags=["integrations", "api", "third-party"]
            )
        ]
        
        for module in default_modules:
            await self.register_module(module)
            
        self.logger.info("Created default modules")
        
    async def _save_registry(self):
        """Save registry to storage"""
        try:
            modules_data = {
                module_id: module.dict() 
                for module_id, module in self._modules.items()
            }
            await self.storage.set("module_registry", json.dumps(modules_data))
        except Exception as e:
            self.logger.error(f"Failed to save module registry: {e}")
            raise
            
    async def register_module(self, module_info: ModuleInfo) -> bool:
        """Register a module in the registry"""
        try:
            # Validate module info
            if not module_info.module_id or not module_info.name or not module_info.version:
                self.logger.error("Invalid module info: missing required fields")
                return False
                
            # Check for conflicts
            if module_info.module_id in self._modules:
                self.logger.warning(f"Module {module_info.module_id} already registered, updating")
                
            # Register module
            self._modules[module_info.module_id] = module_info
            
            # Save to storage
            await self._save_registry()
            
            self.logger.info(f"Registered module: {module_info.module_id} v{module_info.version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register module {module_info.module_id}: {e}")
            return False
            
    async def unregister_module(self, module_id: str) -> bool:
        """Unregister a module from the registry"""
        try:
            if module_id not in self._modules:
                self.logger.warning(f"Module {module_id} not found in registry")
                return False
                
            # Remove from registry
            del self._modules[module_id]
            
            # Save to storage
            await self._save_registry()
            
            self.logger.info(f"Unregistered module: {module_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister module {module_id}: {e}")
            return False
            
    async def get_module_info(self, module_id: str) -> Optional[ModuleInfo]:
        """Get module information"""
        return self._modules.get(module_id)
        
    async def list_modules(self, category: Optional[str] = None, tags: Optional[List[str]] = None) -> List[ModuleInfo]:
        """List available modules"""
        modules = list(self._modules.values())
        
        # Filter by category
        if category:
            modules = [m for m in modules if m.category == category]
            
        # Filter by tags
        if tags:
            modules = [m for m in modules if any(tag in m.tags for tag in tags)]
            
        return modules
        
    async def search_modules(self, query: str) -> List[ModuleInfo]:
        """Search for modules"""
        query_lower = query.lower()
        results = []
        
        for module in self._modules.values():
            if (query_lower in module.name.lower() or
                query_lower in module.description.lower() or
                query_lower in module.category.lower() or
                any(query_lower in tag.lower() for tag in module.tags)):
                results.append(module)
                
        return results
        
    async def check_dependencies(self, module_id: str, installed_modules: List[str]) -> List[str]:
        """Check module dependencies"""
        module_info = await self.get_module_info(module_id)
        if not module_info:
            return [f"Module {module_id} not found"]
            
        missing_deps = []
        for dep in module_info.dependencies:
            if dep not in installed_modules:
                missing_deps.append(dep)
                
        return missing_deps
        
    async def check_conflicts(self, module_id: str, installed_modules: List[str]) -> List[str]:
        """Check module conflicts"""
        module_info = await self.get_module_info(module_id)
        if not module_info:
            return [f"Module {module_id} not found"]
            
        conflicts = []
        for conflict in module_info.conflicts:
            if conflict in installed_modules:
                conflicts.append(conflict)
                
        return conflicts


class ModuleSystemLoader(ModuleLoader):
    """Module loader implementation"""
    
    def __init__(self, storage_backend: Any, modules_path: Optional[str] = None):
        """Initialize module loader"""
        self.storage = storage_backend
        self.modules_path = Path(modules_path) if modules_path else Path("./modules")
        self.logger = logging.getLogger("ModuleLoader")
        self._instances: Dict[str, ModuleInstance] = {}
        self._loaded_modules: Dict[str, Any] = {}
        
    async def start(self):
        """Start the module loader"""
        self.logger.info("Starting module loader")
        self.modules_path.mkdir(parents=True, exist_ok=True)
        await self._load_instances()
        
    async def stop(self):
        """Stop the module loader"""
        self.logger.info("Stopping module loader")
        
        # Unload all instances
        for instance_id in list(self._instances.keys()):
            await self.unload_module(instance_id)
            
        self._instances.clear()
        self._loaded_modules.clear()
        
    async def _load_instances(self):
        """Load module instances from storage"""
        try:
            instances_data = await self.storage.get("module_instances")
            if instances_data:
                if isinstance(instances_data, str):
                    instances_data = json.loads(instances_data)
                    
                for instance_id, instance_dict in instances_data.items():
                    instance = ModuleInstance(**instance_dict)
                    self._instances[instance_id] = instance
                    
                self.logger.info(f"Loaded {len(self._instances)} module instances")
                
        except Exception as e:
            self.logger.error(f"Failed to load module instances: {e}")
            raise
            
    async def _save_instances(self):
        """Save instances to storage"""
        try:
            instances_data = {
                instance_id: instance.dict()
                for instance_id, instance in self._instances.items()
            }
            await self.storage.set("module_instances", json.dumps(instances_data))
        except Exception as e:
            self.logger.error(f"Failed to save module instances: {e}")
            raise
            
    async def load_module(self, module_id: str, tenant_id: str, settings: Dict[str, Any]) -> ModuleInstance:
        """Load a module for a tenant"""
        try:
            # Create instance ID
            instance_id = f"{module_id}_{tenant_id}_{uuid.uuid4().hex[:8]}"
            
            # Create module instance
            instance = ModuleInstance(
                instance_id=instance_id,
                module_id=module_id,
                tenant_id=tenant_id,
                enabled=True,
                settings=settings,
                status="loading",
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat()
            )
            
            # Try to load the module
            try:
                # In a real implementation, you would dynamically load the module
                # For now, we'll simulate successful loading
                await asyncio.sleep(0.1)  # Simulate loading time
                
                instance.status = "active"
                instance.updated_at = datetime.utcnow().isoformat()
                
                # Store instance
                self._instances[instance_id] = instance
                await self._save_instances()
                
                self.logger.info(f"Loaded module {module_id} for tenant {tenant_id}")
                
            except Exception as e:
                instance.status = "error"
                instance.error_message = str(e)
                instance.updated_at = datetime.utcnow().isoformat()
                
                self.logger.error(f"Failed to load module {module_id}: {e}")
                
            return instance
            
        except Exception as e:
            self.logger.error(f"Failed to create module instance for {module_id}: {e}")
            raise
            
    async def unload_module(self, instance_id: str) -> bool:
        """Unload a module instance"""
        try:
            if instance_id not in self._instances:
                self.logger.warning(f"Module instance {instance_id} not found")
                return False
                
            instance = self._instances[instance_id]
            
            # In a real implementation, you would properly unload the module
            # For now, we'll just mark it as inactive
            instance.status = "inactive"
            instance.updated_at = datetime.utcnow().isoformat()
            
            # Remove from instances
            del self._instances[instance_id]
            await self._save_instances()
            
            self.logger.info(f"Unloaded module instance {instance_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unload module instance {instance_id}: {e}")
            return False
            
    async def reload_module(self, instance_id: str) -> bool:
        """Reload a module instance"""
        try:
            if instance_id not in self._instances:
                self.logger.warning(f"Module instance {instance_id} not found")
                return False
                
            instance = self._instances[instance_id]
            
            # Unload and reload
            await self.unload_module(instance_id)
            await self.load_module(instance.module_id, instance.tenant_id, instance.settings)
            
            self.logger.info(f"Reloaded module instance {instance_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reload module instance {instance_id}: {e}")
            return False
            
    async def get_module_instance(self, instance_id: str) -> Optional[ModuleInstance]:
        """Get module instance"""
        return self._instances.get(instance_id)
        
    async def list_instances(self, tenant_id: Optional[str] = None) -> List[ModuleInstance]:
        """List module instances"""
        instances = list(self._instances.values())
        
        if tenant_id:
            instances = [i for i in instances if i.tenant_id == tenant_id]
            
        return instances
        
    async def update_module_settings(self, instance_id: str, settings: Dict[str, Any]) -> bool:
        """Update module settings"""
        try:
            if instance_id not in self._instances:
                self.logger.warning(f"Module instance {instance_id} not found")
                return False
                
            instance = self._instances[instance_id]
            instance.settings.update(settings)
            instance.updated_at = datetime.utcnow().isoformat()
            
            await self._save_instances()
            
            self.logger.info(f"Updated settings for module instance {instance_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update settings for module instance {instance_id}: {e}")
            return False


class ModuleSystemManager(ModuleManager):
    """Module manager implementation"""
    
    def __init__(self, registry: ModuleRegistry, loader: ModuleLoader, storage_backend: Any):
        """Initialize module manager"""
        self.registry = registry
        self.loader = loader
        self.storage = storage_backend
        self.logger = logging.getLogger("ModuleManager")
        
    async def start(self):
        """Start the module manager"""
        self.logger.info("Starting module manager")
        
    async def stop(self):
        """Stop the module manager"""
        self.logger.info("Stopping module manager")
        
    async def install_module(self, module_id: str, tenant_id: str, settings: Optional[Dict[str, Any]] = None) -> bool:
        """Install a module for a tenant"""
        try:
            # Check if module exists in registry
            module_info = await self.registry.get_module_info(module_id)
            if not module_info:
                self.logger.error(f"Module {module_id} not found in registry")
                return False
                
            # Check if already installed
            existing_instances = await self.loader.list_instances(tenant_id)
            for instance in existing_instances:
                if instance.module_id == module_id:
                    self.logger.warning(f"Module {module_id} already installed for tenant {tenant_id}")
                    return True
                    
            # Validate installation
            validation_errors = await self.validate_module_installation(module_id, tenant_id)
            if validation_errors:
                self.logger.error(f"Module installation validation failed: {validation_errors}")
                return False
                
            # Load module
            instance = await self.loader.load_module(module_id, tenant_id, settings or {})
            
            if instance.status == "active":
                self.logger.info(f"Successfully installed module {module_id} for tenant {tenant_id}")
                return True
            else:
                self.logger.error(f"Failed to install module {module_id}: {instance.error_message}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to install module {module_id} for tenant {tenant_id}: {e}")
            return False
            
    async def uninstall_module(self, module_id: str, tenant_id: str) -> bool:
        """Uninstall a module from a tenant"""
        try:
            # Find module instance
            instances = await self.loader.list_instances(tenant_id)
            target_instance = None
            
            for instance in instances:
                if instance.module_id == module_id:
                    target_instance = instance
                    break
                    
            if not target_instance:
                self.logger.warning(f"Module {module_id} not installed for tenant {tenant_id}")
                return True
                
            # Unload module
            success = await self.loader.unload_module(target_instance.instance_id)
            
            if success:
                self.logger.info(f"Successfully uninstalled module {module_id} from tenant {tenant_id}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to uninstall module {module_id} from tenant {tenant_id}: {e}")
            return False
            
    async def enable_module(self, module_id: str, tenant_id: str) -> bool:
        """Enable a module for a tenant"""
        try:
            # Find module instance
            instances = await self.loader.list_instances(tenant_id)
            target_instance = None
            
            for instance in instances:
                if instance.module_id == module_id:
                    target_instance = instance
                    break
                    
            if not target_instance:
                self.logger.error(f"Module {module_id} not installed for tenant {tenant_id}")
                return False
                
            # Enable module
            target_instance.enabled = True
            target_instance.updated_at = datetime.utcnow().isoformat()
            
            # Reload if needed
            if target_instance.status == "inactive":
                await self.loader.reload_module(target_instance.instance_id)
                
            self.logger.info(f"Enabled module {module_id} for tenant {tenant_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enable module {module_id} for tenant {tenant_id}: {e}")
            return False
            
    async def disable_module(self, module_id: str, tenant_id: str) -> bool:
        """Disable a module for a tenant"""
        try:
            # Find module instance
            instances = await self.loader.list_instances(tenant_id)
            target_instance = None
            
            for instance in instances:
                if instance.module_id == module_id:
                    target_instance = instance
                    break
                    
            if not target_instance:
                self.logger.error(f"Module {module_id} not installed for tenant {tenant_id}")
                return False
                
            # Disable module
            target_instance.enabled = False
            target_instance.updated_at = datetime.utcnow().isoformat()
            
            self.logger.info(f"Disabled module {module_id} for tenant {tenant_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disable module {module_id} for tenant {tenant_id}: {e}")
            return False
            
    async def get_tenant_modules(self, tenant_id: str) -> List[ModuleInstance]:
        """Get modules installed for a tenant"""
        return await self.loader.list_instances(tenant_id)
        
    async def get_module_status(self, module_id: str, tenant_id: str) -> Optional[str]:
        """Get module status for a tenant"""
        instances = await self.loader.list_instances(tenant_id)
        
        for instance in instances:
            if instance.module_id == module_id:
                return instance.status
                
        return None
        
    async def validate_module_installation(self, module_id: str, tenant_id: str) -> List[str]:
        """Validate module installation"""
        errors = []
        
        # Check if module exists
        module_info = await self.registry.get_module_info(module_id)
        if not module_info:
            errors.append(f"Module {module_id} not found in registry")
            return errors
            
        # Check dependencies
        installed_modules = [i.module_id for i in await self.loader.list_instances(tenant_id)]
        missing_deps = await self.registry.check_dependencies(module_id, installed_modules)
        if missing_deps:
            errors.extend([f"Missing dependency: {dep}" for dep in missing_deps])
            
        # Check conflicts
        conflicts = await self.registry.check_conflicts(module_id, installed_modules)
        if conflicts:
            errors.extend([f"Conflicts with: {conflict}" for conflict in conflicts])
            
        return errors
        
    async def get_module_dependencies(self, module_id: str) -> List[str]:
        """Get module dependencies"""
        module_info = await self.registry.get_module_info(module_id)
        if module_info:
            return module_info.dependencies
        return []
        
    async def resolve_dependencies(self, module_ids: List[str]) -> List[str]:
        """Resolve module dependencies"""
        resolved = []
        to_resolve = module_ids.copy()
        
        while to_resolve:
            module_id = to_resolve.pop(0)
            
            if module_id in resolved:
                continue
                
            # Get dependencies
            deps = await self.get_module_dependencies(module_id)
            
            # Add unresolved dependencies to the front
            for dep in reversed(deps):
                if dep not in resolved and dep not in to_resolve:
                    to_resolve.insert(0, dep)
                    
            resolved.append(module_id)
            
        return resolved
