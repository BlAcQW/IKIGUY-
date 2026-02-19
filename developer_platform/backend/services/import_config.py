"""
Developer Platform Import Configuration

This module provides a unified import strategy for the Developer Platform,
ensuring consistent access to shared libraries across all services.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Global tracking for import failures
IMPORT_FAILURES = {
    "shared_libraries": {},
    "last_check": None,
    "failure_count": 0
}

def log_import_failure(module_name: str, error: Exception, context: str = ""):
    """
    Log import failures for monitoring and alerting.
    
    Args:
        module_name: Name of the module that failed to import
        error: The import error that occurred
        context: Additional context about where the import was attempted
    """
    global IMPORT_FAILURES
    
    failure_info = {
        "module": module_name,
        "error": str(error),
        "error_type": type(error).__name__,
        "timestamp": datetime.utcnow().isoformat(),
        "context": context
    }
    
    IMPORT_FAILURES["shared_libraries"][module_name] = failure_info
    IMPORT_FAILURES["last_check"] = datetime.utcnow().isoformat()
    IMPORT_FAILURES["failure_count"] += 1
    
    # Log with high severity for monitoring
    logger.error(f"SHARED LIBRARY IMPORT FAILURE: {module_name} - {error}")
    logger.error(f"Context: {context}")
    
    # Log to a dedicated file for monitoring
    try:
        with open("/tmp/kasaai_import_failures.log", "a") as f:
            f.write(f"{datetime.utcnow().isoformat()} - {json.dumps(failure_info)}\n")
    except Exception as e:
        logger.error(f"Failed to write to import failure log: {e}")

def get_import_failures():
    """Get current import failure status."""
    return IMPORT_FAILURES.copy()

def clear_import_failures():
    """Clear import failure tracking (useful for testing)."""
    global IMPORT_FAILURES
    IMPORT_FAILURES = {
        "shared_libraries": {},
        "last_check": None,
        "failure_count": 0
    }

def get_project_root() -> Path:
    """Get the absolute path to the KasaAI project root."""
    # Start from the current file location
    current_file = Path(__file__)
    
    # Navigate up to find the project root (where shared/ and apps/ directories are)
    for parent in current_file.parents:
        if (parent / "shared").exists() and (parent / "apps").exists():
            return parent
    
    # Fallback: use environment variable
    env_root = os.getenv("KASAAI_PROJECT_ROOT")
    if env_root:
        return Path(env_root)
    
    # Last resort: assume we're in the developer platform services directory
    return current_file.parent.parent.parent.parent

def ensure_shared_libraries_available():
    """Ensure shared libraries are available in the Python path."""
    project_root = get_project_root()
    
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.debug(f"Added project root to sys.path: {project_root}")

def get_shared_class(module_name: str, class_name: str):
    """
    Get a specific class from a shared module with proper error handling.
    
    Args:
        module_name: Name of the shared module (e.g., 'ai', 'analytics')
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
        error_msg = f"Failed to import {class_name} from apps.shared.{module_name}: {e}"
        log_import_failure(f"apps.shared.{module_name}.{class_name}", e, f"get_shared_class({module_name}, {class_name})")
        raise ImportError(error_msg)

# Convenience functions for commonly used shared components
def get_ai_engine():
    """Get the GhanaianModelFineTuner class."""
    return get_shared_class("ai", "GhanaianModelFineTuner")

def get_analytics_engine():
    """Get the BusinessIntelligence class."""
    return get_shared_class("analytics", "BusinessIntelligence")

def get_security_engine():
    """Get the SecurityEngine class."""
    return get_shared_class("security", "SecurityEngine")

def get_storage_backend():
    """Get the MemoryStorageBackend class."""
    return get_shared_class("storage", "MemoryStorageBackend")

def get_config_manager():
    """Get the ConfigManager class."""
    return get_shared_class("config", "ConfigManager")

def get_config_engine():
    """Get the ConfigurationEngine class."""
    return get_shared_class("config", "ConfigurationEngine")

def get_license_engine():
    """Get the LicenseManagementEngine class."""
    return get_shared_class("license", "LicenseManagementEngine")

def get_telephony_provider():
    """Get the TelephonyProvider class."""
    return get_shared_class("telephony", "TelephonyProvider")

def get_telephony_engine():
    """Get the TelephonyEngine class."""
    return get_shared_class("telephony", "TelephonyEngine")

def get_usage_engine():
    """Get the UsageEngine class."""
    return get_shared_class("usage", "UsageEngine")

def get_usage_tracker():
    """Get the UsageTracker class."""
    return get_shared_class("usage", "UsageTracker")

def get_monitoring_engine():
    """Get the MonitoringEngine class."""
    return get_shared_class("monitoring", "MonitoringEngine")

def get_module_engine():
    """Get the ModuleEngine class."""
    return get_shared_class("modules", "ModuleEngine")

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
    "get_ai_engine",
    "get_analytics_engine",
    "get_security_engine",
    "get_storage_backend",
    "get_config_manager",
    "get_license_engine",
    "get_telephony_provider",
    "get_usage_tracker",
    "get_tenant_manager",
    "get_events_bus",
    "get_monitoring_service",
]
