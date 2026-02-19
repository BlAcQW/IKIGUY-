"""
Storage Backends

This package contains storage backend implementations for the shared libraries.
Includes Hetzner Storage Box integration and file serving capabilities.
"""

from .interfaces import StorageBackend, StorageConfig
from .postgres import PostgresStorageBackend
from .redis import RedisStorageBackend
from .memory import MemoryStorageBackend

# Import Hetzner storage components
try:
    from .hetzner_storage_box import (
        HetznerStorageBox,
        StorageProtocol,
        HetznerStorageBoxError,
        get_storage
    )
    HETZNER_AVAILABLE = True
except ImportError:
    HETZNER_AVAILABLE = False
    HetznerStorageBox = None
    StorageProtocol = None
    HetznerStorageBoxError = None
    get_storage = None

# Import file serving service
try:
    from ..services.storage_file_service import StorageFileService
    FILE_SERVICE_AVAILABLE = True
except ImportError:
    FILE_SERVICE_AVAILABLE = False
    StorageFileService = None

__all__ = [
    "StorageBackend",
    "StorageConfig", 
    "PostgresStorageBackend",
    "RedisStorageBackend",
    "MemoryStorageBackend",
]

# Add Hetzner exports if available
if HETZNER_AVAILABLE:
    __all__.extend([
        "HetznerStorageBox",
        "StorageProtocol",
        "HetznerStorageBoxError",
        "get_storage",
    ])

# Add file service export if available
if FILE_SERVICE_AVAILABLE:
    __all__.append("StorageFileService")
