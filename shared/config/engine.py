"""
Configuration Engine

This module provides a comprehensive configuration engine with tenant configuration,
feature flags, configuration inheritance, and dynamic loading capabilities.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Union
from pathlib import Path
import yaml
import hashlib
from dataclasses import asdict

from .interfaces import ConfigurationManager, TenantConfig, ProviderConfig, BrandingConfig
from .models import FeatureFlags, ModuleConfig, WorkflowConfig, SystemConfig


class ConfigurationEngine(ConfigurationManager):
    """Comprehensive configuration engine with inheritance and dynamic loading"""
    
    def __init__(self, storage_backend: Any, config_path: Optional[str] = None):
        """
        Initialize the configuration engine
        
        Args:
            storage_backend: Storage backend for configuration persistence
            config_path: Path to configuration files (optional)
        """
        super().__init__(storage_backend)
        self.logger = logging.getLogger("ConfigurationEngine")
        self.config_path = Path(config_path) if config_path else Path("./config")
        self._cache: Dict[str, TenantConfig] = {}
        self._cache_ttl: Dict[str, datetime] = {}
        self._cache_duration = timedelta(minutes=5)  # 5 minutes cache
        self._default_config: Optional[TenantConfig] = None
        self._system_config: Optional[SystemConfig] = None
        self._feature_flags: Dict[str, Dict[str, bool]] = {}
        self._config_watchers: Dict[str, List[callable]] = {}
        self._reload_task: Optional[asyncio.Task] = None
        self._validation_schemas: Dict[str, Dict] = {}
        self._config_hashes: Dict[str, str] = {}
        
    async def start(self):
        """Start the configuration engine"""
        self.logger.info("Starting configuration engine")
        
        # Load default configuration
        await self._load_default_config()
        
        # Load system configuration
        await self._load_system_config()
        
        # Load feature flags
        await self._load_feature_flags()
        
        # Load validation schemas
        await self._load_validation_schemas()
        
        # Start configuration watcher
        self._reload_task = asyncio.create_task(self._config_watcher_loop())
        
    async def stop(self):
        """Stop the configuration engine"""
        self.logger.info("Stopping configuration engine")
        
        if self._reload_task:
            self._reload_task.cancel()
            try:
                await self._reload_task
            except asyncio.CancelledError:
                pass
        
        # Clear cache
        self._cache.clear()
        self._cache_ttl.clear()
    
    async def _load_default_config(self):
        """Load default configuration from file"""
        try:
            default_config_path = self.config_path / "default.yaml"
            if default_config_path.exists():
                with open(default_config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    self._default_config = TenantConfig(**config_data)
                    self.logger.info("Loaded default configuration")
            else:
                # Create default configuration
                self._default_config = TenantConfig(
                    tenant_id="default",
                    name="Default Configuration",
                    features={
                        "multi_language": True,
                        "real_time_transcription": True,
                        "call_recording": True,
                        "webhook_support": True,
                        "custom_branding": True
                    },
                    providers={},
                    branding={
                        "primary_color": "#1f2937",
                        "secondary_color": "#f59e0b",
                        "company_name": "KasaAI"
                    },
                    modules=[],
                    workflows={},
                    settings={}
                )
                self.logger.info("Created default configuration")
        except Exception as e:
            self.logger.error(f"Failed to load default configuration: {e}")
            raise
    
    async def _load_system_config(self):
        """Load system configuration from file"""
        try:
            system_config_path = self.config_path / "system.yaml"
            if system_config_path.exists():
                with open(system_config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    self._system_config = SystemConfig(**config_data)
                    self.logger.info("Loaded system configuration")
            else:
                # Create default system configuration
                self._system_config = SystemConfig(
                    system_id="kasaai",
                    environment="production",
                    debug_mode=False,
                    log_level="info",
                    max_concurrent_calls=1000,
                    max_call_duration=3600,
                    data_retention_days=90,
                    backup_enabled=True,
                    backup_interval_hours=24,
                    monitoring_enabled=True,
                    alerting_enabled=True,
                    maintenance_window={},
                    security_settings={},
                    performance_settings={}
                )
                self.logger.info("Created system configuration")
        except Exception as e:
            self.logger.error(f"Failed to load system configuration: {e}")
            raise
    
    async def _load_feature_flags(self):
        """Load feature flags from storage"""
        try:
            feature_flags_data = await self.storage.get("feature_flags")
            if feature_flags_data:
                if isinstance(feature_flags_data, str):
                    feature_flags_data = json.loads(feature_flags_data)
                self._feature_flags = feature_flags_data
                self.logger.info("Loaded feature flags")
            else:
                # Create default feature flags
                self._feature_flags = {
                    "global": {
                        "advanced_analytics": False,
                        "ai_powered_features": False,
                        "multi_provider_support": True,
                        "on_premise_deployment": False,
                        "mobile_money_integration": False
                    }
                }
                await self._save_feature_flags()
                self.logger.info("Created default feature flags")
        except Exception as e:
            self.logger.error(f"Failed to load feature flags: {e}")
            raise
    
    async def _load_validation_schemas(self):
        """Load validation schemas for configuration validation"""
        try:
            schemas_path = self.config_path / "schemas"
            if schemas_path.exists():
                for schema_file in schemas_path.glob("*.json"):
                    schema_name = schema_file.stem
                    with open(schema_file, 'r') as f:
                        self._validation_schemas[schema_name] = json.load(f)
                self.logger.info(f"Loaded {len(self._validation_schemas)} validation schemas")
            else:
                # Create default validation schemas
                self._validation_schemas = {
                    "tenant_config": {
                        "type": "object",
                        "properties": {
                            "tenant_id": {"type": "string"},
                            "name": {"type": "string"},
                            "features": {"type": "object"},
                            "providers": {"type": "object"},
                            "branding": {"type": "object"},
                            "modules": {"type": "array"},
                            "workflows": {"type": "object"},
                            "settings": {"type": "object"}
                        },
                        "required": ["tenant_id", "name"]
                    }
                }
                self.logger.info("Created default validation schemas")
        except Exception as e:
            self.logger.error(f"Failed to load validation schemas: {e}")
            raise
    
    async def _save_feature_flags(self):
        """Save feature flags to storage"""
        try:
            await self.storage.set("feature_flags", json.dumps(self._feature_flags))
        except Exception as e:
            self.logger.error(f"Failed to save feature flags: {e}")
            raise
    
    async def get_tenant_config(self, tenant_id: str) -> TenantConfig:
        """
        Get tenant configuration with inheritance
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            TenantConfig: Tenant configuration with inheritance applied
        """
        # Check cache first
        if tenant_id in self._cache:
            if datetime.utcnow() < self._cache_ttl[tenant_id]:
                return self._cache[tenant_id]
            else:
                # Cache expired, remove it
                del self._cache[tenant_id]
                del self._cache_ttl[tenant_id]
        
        try:
            # Load from storage
            config_data = await self.storage.get(f"tenant_config:{tenant_id}")
            
            if config_data:
                # Parse stored configuration
                if isinstance(config_data, str):
                    config_data = json.loads(config_data)
                
                tenant_config = TenantConfig(**config_data)
            else:
                # Create new tenant configuration with inheritance
                tenant_config = await self._create_tenant_config(tenant_id)
            
            # Apply inheritance
            tenant_config = await self._apply_inheritance(tenant_config)
            
            # Apply feature flags
            tenant_config = await self._apply_feature_flags(tenant_config)
            
            # Validate configuration
            validation_errors = await self._validate_config(tenant_config)
            if validation_errors:
                self.logger.warning(f"Configuration validation errors for {tenant_id}: {validation_errors}")
            
            # Cache the result
            self._cache[tenant_id] = tenant_config
            self._cache_ttl[tenant_id] = datetime.utcnow() + self._cache_duration
            
            return tenant_config
            
        except Exception as e:
            self.logger.error(f"Failed to get tenant config for {tenant_id}: {e}")
            # Return default configuration as fallback
            return self._default_config or TenantConfig(
                tenant_id=tenant_id,
                name=f"Tenant {tenant_id}",
                features={},
                providers={},
                branding={},
                modules=[],
                workflows={},
                settings={}
            )
    
    async def _create_tenant_config(self, tenant_id: str) -> TenantConfig:
        """Create new tenant configuration with default inheritance"""
        if not self._default_config:
            raise ValueError("Default configuration not loaded")
        
        # Create new config based on default
        new_config = TenantConfig(
            tenant_id=tenant_id,
            name=f"Tenant {tenant_id}",
            features=self._default_config.features.copy(),
            providers=self._default_config.providers.copy(),
            branding=self._default_config.branding.copy(),
            modules=self._default_config.modules.copy(),
            workflows=self._default_config.workflows.copy(),
            settings=self._default_config.settings.copy()
        )
        
        # Save to storage
        await self.update_tenant_config(tenant_id, new_config)
        
        return new_config
    
    async def _apply_inheritance(self, config: TenantConfig) -> TenantConfig:
        """Apply configuration inheritance from parent configurations"""
        if not self._default_config:
            return config
        
        # Merge with default configuration
        merged_config = TenantConfig(
            tenant_id=config.tenant_id,
            name=config.name,
            features={**self._default_config.features, **config.features},
            providers={**self._default_config.providers, **config.providers},
            branding={**self._default_config.branding, **config.branding},
            modules=[*self._default_config.modules, *config.modules],
            workflows={**self._default_config.workflows, **config.workflows},
            settings={**self._default_config.settings, **config.settings}
        )
        
        return merged_config
    
    async def _apply_feature_flags(self, config: TenantConfig) -> TenantConfig:
        """Apply feature flags to configuration"""
        # Get tenant-specific feature flags
        tenant_flags = self._feature_flags.get(config.tenant_id, {})
        global_flags = self._feature_flags.get("global", {})
        
        # Apply feature flags to features
        for flag_name, flag_value in {**global_flags, **tenant_flags}.items():
            if flag_name in config.features:
                config.features[flag_name] = flag_value
        
        return config
    
    async def _validate_config(self, config: TenantConfig) -> List[str]:
        """Validate configuration against schemas"""
        errors = []
        
        try:
            # Basic validation
            if not config.tenant_id:
                errors.append("tenant_id is required")
            
            if not config.name:
                errors.append("name is required")
            
            # Schema validation if available
            if "tenant_config" in self._validation_schemas:
                schema = self._validation_schemas["tenant_config"]
                # In a real implementation, you would use a JSON schema validator
                # For now, we'll do basic validation
                pass
            
            # Business rule validation
            if config.settings.get("max_concurrent_calls", 0) > 10000:
                errors.append("max_concurrent_calls cannot exceed 10000")
            
            if config.settings.get("data_retention_days", 0) > 365:
                errors.append("data_retention_days cannot exceed 365")
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return errors
    
    async def update_tenant_config(self, tenant_id: str, config: TenantConfig) -> bool:
        """
        Update tenant configuration
        
        Args:
            tenant_id: Tenant identifier
            config: Updated configuration
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Validate configuration
            validation_errors = await self._validate_config(config)
            if validation_errors:
                raise ValueError(f"Configuration validation failed: {validation_errors}")
            
            # Calculate configuration hash
            config_hash = self._calculate_config_hash(config)
            
            # Check if configuration has changed
            if tenant_id in self._config_hashes and self._config_hashes[tenant_id] == config_hash:
                self.logger.info(f"Configuration for {tenant_id} unchanged, skipping update")
                return True
            
            # Save to storage
            config_data = json.dumps(config.dict())
            await self.storage.set(f"tenant_config:{tenant_id}", config_data)
            
            # Update hash
            self._config_hashes[tenant_id] = config_hash
            
            # Clear cache
            if tenant_id in self._cache:
                del self._cache[tenant_id]
            if tenant_id in self._cache_ttl:
                del self._cache_ttl[tenant_id]
            
            # Notify watchers
            await self._notify_config_watchers(tenant_id, config)
            
            self.logger.info(f"Updated configuration for tenant {tenant_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update tenant config for {tenant_id}: {e}")
            return False
    
    def _calculate_config_hash(self, config: TenantConfig) -> str:
        """Calculate hash of configuration for change detection"""
        config_dict = config.dict()
        config_str = json.dumps(config_dict, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()
    
    async def get_feature_flag(self, tenant_id: str, feature_name: str) -> bool:
        """
        Get feature flag value for tenant
        
        Args:
            tenant_id: Tenant identifier
            feature_name: Feature flag name
            
        Returns:
            bool: Feature flag value
        """
        # Check tenant-specific flags first
        tenant_flags = self._feature_flags.get(tenant_id, {})
        if feature_name in tenant_flags:
            return tenant_flags[feature_name]
        
        # Fall back to global flags
        global_flags = self._feature_flags.get("global", {})
        return global_flags.get(feature_name, False)
    
    async def set_feature_flag(self, tenant_id: str, feature_name: str, value: bool) -> bool:
        """
        Set feature flag value for tenant
        
        Args:
            tenant_id: Tenant identifier
            feature_name: Feature flag name
            value: Feature flag value
            
        Returns:
            bool: True if update was successful
        """
        try:
            if tenant_id not in self._feature_flags:
                self._feature_flags[tenant_id] = {}
            
            self._feature_flags[tenant_id][feature_name] = value
            
            # Save to storage
            await self._save_feature_flags()
            
            # Clear cache for affected tenants
            if tenant_id in self._cache:
                del self._cache[tenant_id]
            if tenant_id in self._cache_ttl:
                del self._cache_ttl[tenant_id]
            
            self.logger.info(f"Set feature flag {feature_name}={value} for tenant {tenant_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set feature flag for {tenant_id}: {e}")
            return False
    
    async def get_all_feature_flags(self, tenant_id: str) -> Dict[str, bool]:
        """
        Get all feature flags for tenant
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Dict[str, bool]: All feature flags for tenant
        """
        tenant_flags = self._feature_flags.get(tenant_id, {})
        global_flags = self._feature_flags.get("global", {})
        
        # Merge tenant and global flags (tenant flags take precedence)
        all_flags = {**global_flags, **tenant_flags}
        return all_flags
    
    async def export_config(self, tenant_id: str, format: str = "json") -> str:
        """
        Export tenant configuration
        
        Args:
            tenant_id: Tenant identifier
            format: Export format (json, yaml)
            
        Returns:
            str: Exported configuration
        """
        try:
            config = await self.get_tenant_config(tenant_id)
            
            if format == "json":
                config_dict = config.dict()
                return json.dumps(config_dict, indent=2, default=str)
            elif format == "yaml":
                config_dict = config.dict()
                return yaml.dump(config_dict, default_flow_style=False, sort_keys=False)
            else:
                self.logger.error(f"Unsupported export format: {format}")
                return ""
                
        except Exception as e:
            self.logger.error(f"Failed to export config for {tenant_id}: {e}")
            return ""
    
    async def import_config(self, tenant_id: str, config_data: Union[str, bytes], format: str = "json") -> bool:
        """
        Import tenant configuration
        
        Args:
            tenant_id: Tenant identifier
            config_data: Configuration data
            format: Import format (json, yaml, yml)
            
        Returns:
            bool: True if import was successful
        """
        try:
            # Parse configuration data
            if format.lower() == "json":
                if isinstance(config_data, bytes):
                    config_data = config_data.decode('utf-8')
                config_dict = json.loads(config_data)
            elif format.lower() in ["yaml", "yml"]:
                if isinstance(config_data, str):
                    config_data = config_data.encode('utf-8')
                config_dict = yaml.safe_load(config_data)
            else:
                raise ValueError(f"Unsupported import format: {format}")
            
            # Update tenant_id to match target tenant
            config_dict["tenant_id"] = tenant_id
            
            # Create configuration object
            config = TenantConfig(**config_dict)
            
            # Update configuration
            return await self.update_tenant_config(tenant_id, config)
            
        except Exception as e:
            self.logger.error(f"Failed to import config for {tenant_id}: {e}")
            return False
    
    async def get_config_summary(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get configuration summary for tenant
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Dict[str, Any]: Configuration summary
        """
        try:
            config = await self.get_tenant_config(tenant_id)
            feature_flags = await self.get_all_feature_flags(tenant_id)
            
            return {
                "tenant_id": config.tenant_id,
                "name": config.name,
                "features_count": len(config.features),
                "providers_count": len(config.providers),
                "modules_count": len(config.modules),
                "workflows_count": len(config.workflows),
                "feature_flags_count": len(feature_flags),
                "last_updated": self._cache_ttl.get(tenant_id, datetime.utcnow()).isoformat(),
                "cache_status": "cached" if tenant_id in self._cache else "not_cached"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get config summary for {tenant_id}: {e}")
            return {}
    
    async def add_config_watcher(self, tenant_id: str, callback: callable):
        """
        Add configuration watcher for tenant
        
        Args:
            tenant_id: Tenant identifier
            callback: Callback function to call when configuration changes
        """
        if tenant_id not in self._config_watchers:
            self._config_watchers[tenant_id] = []
        
        if callback not in self._config_watchers[tenant_id]:
            self._config_watchers[tenant_id].append(callback)
            self.logger.info(f"Added config watcher for tenant {tenant_id}")
    
    async def remove_config_watcher(self, tenant_id: str, callback: callable):
        """
        Remove configuration watcher for tenant
        
        Args:
            tenant_id: Tenant identifier
            callback: Callback function to remove
        """
        if tenant_id in self._config_watchers:
            if callback in self._config_watchers[tenant_id]:
                self._config_watchers[tenant_id].remove(callback)
                self.logger.info(f"Removed config watcher for tenant {tenant_id}")
    
    async def _notify_config_watchers(self, tenant_id: str, config: TenantConfig):
        """Notify all watchers of configuration changes"""
        if tenant_id in self._config_watchers:
            for callback in self._config_watchers[tenant_id]:
                try:
                    await callback(tenant_id, config)
                except Exception as e:
                    self.logger.error(f"Error in config watcher callback: {e}")
    
    async def _config_watcher_loop(self):
        """Background loop for configuration watching"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Check for configuration file changes
                await self._check_config_file_changes()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in config watcher loop: {e}")
    
    async def _check_config_file_changes(self):
        """Check for changes in configuration files"""
        try:
            # Check default config file
            default_config_path = self.config_path / "default.yaml"
            if default_config_path.exists():
                # In a real implementation, you would check file modification time
                # and reload if changed
                pass
            
            # Check system config file
            system_config_path = self.config_path / "system.yaml"
            if system_config_path.exists():
                # In a real implementation, you would check file modification time
                # and reload if changed
                pass
                
        except Exception as e:
            self.logger.error(f"Error checking config file changes: {e}")
    
    async def get_system_config(self) -> Optional[SystemConfig]:
        """Get system configuration"""
        return self._system_config
    
    async def update_system_config(self, config: SystemConfig) -> bool:
        """
        Update system configuration
        
        Args:
            config: Updated system configuration
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Save to file
            system_config_path = self.config_path / "system.yaml"
            system_config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(system_config_path, 'w') as f:
                yaml.dump(config.dict(), f, default_flow_style=False)
            
            # Update in memory
            self._system_config = config
            
            self.logger.info("Updated system configuration")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update system config: {e}")
            return False
    
    async def clear_cache(self, tenant_id: Optional[str] = None):
        """
        Clear configuration cache
        
        Args:
            tenant_id: Specific tenant to clear cache for, or None for all
        """
        if tenant_id:
            if tenant_id in self._cache:
                del self._cache[tenant_id]
            if tenant_id in self._cache_ttl:
                del self._cache_ttl[tenant_id]
            self.logger.info(f"Cleared cache for tenant {tenant_id}")
        else:
            self._cache.clear()
            self._cache_ttl.clear()
            self.logger.info("Cleared all configuration cache")
    
    async def get_config_statistics(self) -> Dict[str, Any]:
        """
        Get configuration engine statistics
        
        Returns:
            Dict[str, Any]: Configuration engine statistics
        """
        return {
            "cached_tenants": len(self._cache),
            "total_watchers": sum(len(watchers) for watchers in self._config_watchers.values()),
            "feature_flags_tenants": len(self._validation_schemas),
            "validation_schemas": len(self._validation_schemas),
            "cache_hit_ratio": self._calculate_cache_hit_ratio(),
            "uptime": self._get_uptime()
        }
    
    def _calculate_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio (simplified implementation)"""
        # In a real implementation, you would track cache hits and misses
        return 0.85  # Placeholder
    
    def _get_uptime(self) -> str:
        """Get engine uptime (simplified implementation)"""
        # In a real implementation, you would track start time
        return "00:05:30"  # Placeholder
    
    async def get_provider_config(self, tenant_id: str) -> ProviderConfig:
        """
        Get provider configuration for tenant
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            ProviderConfig: Provider configuration
        """
        try:
            config = await self.get_tenant_config(tenant_id)
            
            # Extract provider configuration from tenant config
            provider_data = config.providers.get("provider_config", {})
            
            return ProviderConfig(
                primary=provider_data.get("primary", "vapi"),
                fallback=provider_data.get("fallback"),
                cost_optimization=provider_data.get("cost_optimization", True),
                providers=provider_data.get("providers", {}),
                routing_rules=provider_data.get("routing_rules", {}),
                health_check_interval=provider_data.get("health_check_interval", 60)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get provider config for {tenant_id}: {e}")
            # Return default provider configuration
            return ProviderConfig(
                primary="vapi",
                fallback="vonage",
                cost_optimization=True,
                providers={},
                routing_rules={},
                health_check_interval=60
            )
    
    async def get_branding_config(self, tenant_id: str) -> BrandingConfig:
        """
        Get branding configuration for tenant
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            BrandingConfig: Branding configuration
        """
        try:
            config = await self.get_tenant_config(tenant_id)
            
            # Extract branding configuration from tenant config
            branding_data = config.branding
            
            return BrandingConfig(
                logo_url=branding_data.get("logo_url"),
                primary_color=branding_data.get("primary_color", "#1f2937"),
                secondary_color=branding_data.get("secondary_color", "#f59e0b"),
                company_name=branding_data.get("company_name", f"Tenant {tenant_id}"),
                domain=branding_data.get("domain"),
                favicon_url=branding_data.get("favicon_url"),
                custom_css=branding_data.get("custom_css"),
                custom_js=branding_data.get("custom_js")
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get branding config for {tenant_id}: {e}")
            # Return default branding configuration
            return BrandingConfig(
                logo_url=None,
                primary_color="#1f2937",
                secondary_color="#f59e0b",
                company_name=f"Tenant {tenant_id}",
                domain=None,
                favicon_url=None,
                custom_css=None,
                custom_js=None
            )
    
    async def reload_config(self, tenant_id: str) -> bool:
        """
        Reload configuration from storage
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            bool: True if reload was successful
        """
        try:
            # Remove from cache to force reload
            if tenant_id in self._cache:
                del self._cache[tenant_id]
            if tenant_id in self._cache_ttl:
                del self._cache_ttl[tenant_id]
            
            # Reload configuration
            await self.get_tenant_config(tenant_id)
            
            self.logger.info(f"Reloaded configuration for tenant {tenant_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reload config for {tenant_id}: {e}")
            return False
    
    async def validate_config(self, config: TenantConfig) -> List[str]:
        """
        Validate configuration and return errors
        
        Args:
            config: Configuration to validate
            
        Returns:
            List[str]: List of validation errors
        """
        return await self._validate_config(config)

