"""
Storage file serving routes.

Uses the shared storage file service from @shared to serve files
from Hetzner storage without requiring users to authenticate.

This is part of the Hetzner Storage Box and Drive Service integration.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import logging
import sys
import os
from pathlib import Path

# Add project root to path for shared imports (consistent with main.py)
# From /opt/kasaai/apps/inkwave/backend/app/api/routes/ -> /opt/kasaai/
project_root = Path(__file__).parent.parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.shared.routes.storage_routes import create_storage_router
from apps.shared.services.storage_file_service import StorageFileService
from apps.shared.storage.hetzner_storage_box import get_storage

logger = logging.getLogger(__name__)

# Global storage file service instance
_storage_file_service: Optional[StorageFileService] = None


async def get_storage_file_service() -> StorageFileService:
    """
    Get or create storage file service instance.

    Returns:
        StorageFileService instance configured for InkWave
    """
    global _storage_file_service

    if _storage_file_service is None:
        # Get Hetzner storage backend (with base_path already set)
        # Note: HetznerStorageBox already handles the base_path internally
        hetzner_storage = await get_storage(base_path="kasaai/inkwave")

        # Local fallback path
        local_fallback = os.getenv(
            "STORAGE_PATH",
            "/opt/kasaai/apps/inkwave/storage"
        )

        # Create URL generator for InkWave-specific paths
        def url_generator(relative_path: str) -> str:
            """Generate InkWave-specific API URLs."""
            if relative_path.startswith("books/"):
                book_id = relative_path.replace("books/", "").replace(".pdf", "")
                return f"/api/v1/storage/books/{book_id}.pdf"
            elif relative_path.startswith("covers/"):
                book_id = relative_path.replace("covers/", "").split(".")[0]
                return f"/api/v1/storage/covers/{book_id}"
            return f"/api/v1/storage/{relative_path}"

        # Note: Don't set base_path here because HetznerStorageBox already
        # has base_path="kasaai/inkwave" set. Setting it in both places
        # would result in double-prefixed paths like:
        # /kasaai/inkwave/kasaai/inkwave/covers/...
        _storage_file_service = StorageFileService(
            storage_backend=hetzner_storage,
            base_path="",  # Empty - HetznerStorageBox handles base_path
            local_fallback_path=local_fallback,
            url_generator=url_generator
        )

    return _storage_file_service


# Create router using shared storage routes
async def create_inkwave_storage_router() -> APIRouter:
    """
    Create storage router for InkWave using shared storage routes.
    
    Returns:
        FastAPI router for file serving
    """
    storage_service = await get_storage_file_service()
    return create_storage_router(
        storage_service=storage_service,
        prefix="/api/v1/storage",
        tags=["storage", "inkwave"]
    )


# For backward compatibility, create router at module level
# Note: This will be initialized when the module is imported
router = None

