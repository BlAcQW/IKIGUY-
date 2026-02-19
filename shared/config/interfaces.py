"""
Configuration Interfaces

This module defines abstract interfaces for configuration management.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class TenantConfig(BaseModel):
    """Tenant configuration model"""
    tenant_id: str = Field(..., description="Tenant identifier")
    name: str = Field(..., description="Tenant name")
    features: Dict[str, bool] = Field(default_factory=dict, description="Feature flags")
    providers: Dict[str, Any] = Field(default_factory=dict, description="Provider configurations")
    branding: Dict[str, Any] = Field(default_factory=dict, description="Branding configuration")
    modules: List[str] = Field(default_factory=list, description="Enabled modules")
    workflows: Dict[str, Any] = Field(default_factory=dict, description="Workflow configurations")
    settings: Dict[str, Any] = Field(default_factory=dict, description="General settings")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class ProviderConfig(BaseModel):
    """Provider configuration model"""
    primary: str = Field(..., description="Primary provider")
    fallback: Optional[str] = Field(None, description="Fallback provider")
    cost_optimization: bool = Field(True, description="Enable cost optimization")
    providers: Dict[str, Any] = Field(default_factory=dict, description="Provider settings")
    routing_rules: Dict[str, Any] = Field(default_factory=dict, description="Routing rules")
    health_check_interval: int = Field(60, description="Health check interval in seconds")


class BrandingConfig(BaseModel):
    """Branding configuration model"""
    logo_url: Optional[str] = Field(None, description="Logo URL")
    primary_color: str = Field("#1f2937", description="Primary color")
    secondary_color: str = Field("#f59e0b", description="Secondary color")
    company_name: str = Field(..., description="Company name")
    domain: Optional[str] = Field(None, description="Custom domain")
    favicon_url: Optional[str] = Field(None, description="Favicon URL")
    custom_css: Optional[str] = Field(None, description="Custom CSS")
    custom_js: Optional[str] = Field(None, description="Custom JavaScript")


class ConfigurationManager(ABC):
    """Abstract configuration manager interface"""
    
    def __init__(self, storage_backend: Any):
        """Initialize with storage backend"""
        self.storage = storage_backend
    
    @abstractmethod
    async def get_tenant_config(self, tenant_id: str) -> TenantConfig:
        """Get tenant configuration"""
        pass
    
    @abstractmethod
    async def update_tenant_config(self, tenant_id: str, config: TenantConfig) -> bool:
        """Update tenant configuration"""
        pass
    
    @abstractmethod
    async def get_feature_flag(self, tenant_id: str, feature_name: str) -> bool:
        """Get feature flag value"""
        pass
    
    @abstractmethod
    async def set_feature_flag(self, tenant_id: str, feature_name: str, value: bool) -> bool:
        """Set feature flag value"""
        pass
    
    @abstractmethod
    async def get_provider_config(self, tenant_id: str) -> ProviderConfig:
        """Get provider configuration"""
        pass
    
    @abstractmethod
    async def get_branding_config(self, tenant_id: str) -> BrandingConfig:
        """Get branding configuration"""
        pass
    
    @abstractmethod
    async def reload_config(self, tenant_id: str) -> bool:
        """Reload configuration from storage"""
        pass
    
    @abstractmethod
    async def validate_config(self, config: TenantConfig) -> List[str]:
        """Validate configuration and return errors"""
        pass


# Module System Interfaces

class ModuleInfo(BaseModel):
    """Module information model"""
    module_id: str = Field(..., description="Module identifier")
    name: str = Field(..., description="Module name")
    version: str = Field(..., description="Module version")
    description: Optional[str] = Field(None, description="Module description")
    author: Optional[str] = Field(None, description="Module author")
    license: Optional[str] = Field(None, description="Module license")
    homepage: Optional[str] = Field(None, description="Module homepage")
    repository: Optional[str] = Field(None, description="Module repository")
    dependencies: List[str] = Field(default_factory=list, description="Module dependencies")
    conflicts: List[str] = Field(default_factory=list, description="Conflicting modules")
    permissions: List[str] = Field(default_factory=list, description="Required permissions")
    features: List[str] = Field(default_factory=list, description="Provided features")
    api_endpoints: List[str] = Field(default_factory=list, description="API endpoints")
    ui_components: List[str] = Field(default_factory=list, description="UI components")
    settings_schema: Dict[str, Any] = Field(default_factory=dict, description="Settings schema")
    min_system_version: Optional[str] = Field(None, description="Minimum system version")
    max_system_version: Optional[str] = Field(None, description="Maximum system version")
    tags: List[str] = Field(default_factory=list, description="Module tags")
    category: Optional[str] = Field(None, description="Module category")


class ModuleInstance(BaseModel):
    """Module instance model"""
    instance_id: str = Field(..., description="Instance identifier")
    module_id: str = Field(..., description="Module identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    enabled: bool = Field(True, description="Whether module is enabled")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Module settings")
    status: str = Field("inactive", description="Module status: inactive, loading, active, error")
    error_message: Optional[str] = Field(None, description="Error message if status is error")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")


class ModuleRegistry(ABC):
    """Abstract module registry interface"""
    
    @abstractmethod
    async def register_module(self, module_info: ModuleInfo) -> bool:
        """Register a module in the registry"""
        pass
    
    @abstractmethod
    async def unregister_module(self, module_id: str) -> bool:
        """Unregister a module from the registry"""
        pass
    
    @abstractmethod
    async def get_module_info(self, module_id: str) -> Optional[ModuleInfo]:
        """Get module information"""
        pass
    
    @abstractmethod
    async def list_modules(self, category: Optional[str] = None, tags: Optional[List[str]] = None) -> List[ModuleInfo]:
        """List available modules"""
        pass
    
    @abstractmethod
    async def search_modules(self, query: str) -> List[ModuleInfo]:
        """Search for modules"""
        pass
    
    @abstractmethod
    async def check_dependencies(self, module_id: str, installed_modules: List[str]) -> List[str]:
        """Check module dependencies"""
        pass
    
    @abstractmethod
    async def check_conflicts(self, module_id: str, installed_modules: List[str]) -> List[str]:
        """Check module conflicts"""
        pass


class ModuleLoader(ABC):
    """Abstract module loader interface"""
    
    @abstractmethod
    async def load_module(self, module_id: str, tenant_id: str, settings: Dict[str, Any]) -> ModuleInstance:
        """Load a module for a tenant"""
        pass
    
    @abstractmethod
    async def unload_module(self, instance_id: str) -> bool:
        """Unload a module instance"""
        pass
    
    @abstractmethod
    async def reload_module(self, instance_id: str) -> bool:
        """Reload a module instance"""
        pass
    
    @abstractmethod
    async def get_module_instance(self, instance_id: str) -> Optional[ModuleInstance]:
        """Get module instance"""
        pass
    
    @abstractmethod
    async def list_instances(self, tenant_id: Optional[str] = None) -> List[ModuleInstance]:
        """List module instances"""
        pass
    
    @abstractmethod
    async def update_module_settings(self, instance_id: str, settings: Dict[str, Any]) -> bool:
        """Update module settings"""
        pass


class ModuleManager(ABC):
    """Abstract module manager interface"""
    
    @abstractmethod
    async def install_module(self, module_id: str, tenant_id: str, settings: Optional[Dict[str, Any]] = None) -> bool:
        """Install a module for a tenant"""
        pass
    
    @abstractmethod
    async def uninstall_module(self, module_id: str, tenant_id: str) -> bool:
        """Uninstall a module from a tenant"""
        pass
    
    @abstractmethod
    async def enable_module(self, module_id: str, tenant_id: str) -> bool:
        """Enable a module for a tenant"""
        pass
    
    @abstractmethod
    async def disable_module(self, module_id: str, tenant_id: str) -> bool:
        """Disable a module for a tenant"""
        pass
    
    @abstractmethod
    async def get_tenant_modules(self, tenant_id: str) -> List[ModuleInstance]:
        """Get modules installed for a tenant"""
        pass
    
    @abstractmethod
    async def get_module_status(self, module_id: str, tenant_id: str) -> Optional[str]:
        """Get module status for a tenant"""
        pass
    
    @abstractmethod
    async def validate_module_installation(self, module_id: str, tenant_id: str) -> List[str]:
        """Validate module installation"""
        pass
    
    @abstractmethod
    async def get_module_dependencies(self, module_id: str) -> List[str]:
        """Get module dependencies"""
        pass
    
    @abstractmethod
    async def resolve_dependencies(self, module_ids: List[str]) -> List[str]:
        """Resolve module dependencies"""
        pass
