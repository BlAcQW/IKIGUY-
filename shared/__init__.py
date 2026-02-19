"""
KasaAI Shared Libraries

This package contains shared libraries used across the KasaAI platform.
"""

import os
import sys
from pathlib import Path


# Get the project root directory
def get_project_root():
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

    # Last resort: assume we're in the shared directory
    return current_file.parent


# Add project root to Python path if not already there
project_root = get_project_root()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Re-export commonly used classes for convenience
from .telephony import TelephonyEvent, TelephonyPort, ProviderManager
from .config import TenantConfig, ProviderConfig, BrandingConfig, ConfigurationManager
from .usage import UsageRecord, UsageTracker
from .license import LicenseInfo, LicenseValidator
from .events import Event, EventBus, EventHandler
__all__ = [
    "TelephonyEvent",
    "TelephonyPort",
    "ProviderManager",
    "TenantConfig",
    "ProviderConfig",
    "BrandingConfig",
    "ConfigurationManager",
    "UsageRecord",
    "UsageTracker",
    "LicenseInfo",
    "LicenseValidator",
    "Event",
    "EventBus",
    "EventHandler",
]
