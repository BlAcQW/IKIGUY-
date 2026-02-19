"""
Core Backend Import Configuration

This module provides a unified import strategy for the Core Backend,
ensuring consistent access to shared libraries across all services.
"""

import logging

logger = logging.getLogger(__name__)

def get_shared_class(module_name: str, class_name: str):
    """
    Get a specific class from a shared module with proper error handling.
    
    Args:
        module_name: Name of the shared module (e.g., 'license', 'config')
        class_name: Name of the class to import
        
    Returns:
        The imported class
        
    Raises:
        ImportError: If the class cannot be imported
    """
    try:
        # Import from apps.shared using proper package imports
        module = __import__(f"apps.shared.{module_name}", fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Failed to import {class_name} from apps.shared.{module_name}: {e}")

# Convenience functions for commonly used shared components
def get_license_engine():
    """Get the LicenseManagementEngine class."""
    return get_shared_class("license", "LicenseManagementEngine")

def get_config_engine():
    """Get the ConfigurationEngine class."""
    return get_shared_class("config", "ConfigurationEngine")

def get_storage_backend():
    """Get the MemoryStorageBackend class."""
    return get_shared_class("storage", "MemoryStorageBackend")

def get_telephony_provider():
    """Get the ProviderManager class."""
    return get_shared_class("telephony", "ProviderManager")

def get_ai_engine():
    """Get the AIEngine class."""
    return get_shared_class("ai", "AIEngine")

def get_analytics_engine():
    """Get the AnalyticsEngine class."""
    return get_shared_class("analytics", "AnalyticsEngine")

def get_security_engine():
    """Get the SecurityEngine class."""
    return get_shared_class("security", "SecurityEngine")

def get_usage_tracker():
    """Get the UsageTracker class."""
    return get_shared_class("usage", "UsageTracker")

def get_tenant_manager():
    """Get the TenantManager class."""
    return get_shared_class("tenant", "TenantManager")

def get_events_bus():
    """Get the EventBus class."""
    return get_shared_class("events", "EventBus")

def get_monitoring_service():
    """Get the MonitoringService class."""
    return get_shared_class("monitoring", "MonitoringService")

__all__ = [
    "get_shared_class",
    "get_license_engine",
    "get_config_engine",
    "get_storage_backend",
    "get_telephony_provider",
    "get_ai_engine",
    "get_analytics_engine",
    "get_security_engine",
    "get_usage_tracker",
    "get_tenant_manager",
    "get_events_bus",
    "get_monitoring_service",
]
