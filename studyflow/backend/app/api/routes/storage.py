"""
Storage file serving routes for StudyFlow.

Uses the shared storage file service from @shared to serve files
from Hetzner storage without requiring users to authenticate.

This is part of the Hetzner Storage Box and Drive Service integration.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import logging
import sys
import os

# Add shared to path
sys.path.insert(0, '/opt/kasaai/apps')

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
        StorageFileService instance configured for StudyFlow
    """
    global _storage_file_service
    
    if _storage_file_service is None:
        # Get Hetzner storage backend
        hetzner_storage = await get_storage(base_path="kasaai/studyflow")
        
        # Local fallback path
        local_fallback = os.getenv(
            "STORAGE_PATH",
            "/opt/kasaai/apps/studyflow/storage"
        )
        
        # Create URL generator for StudyFlow-specific paths
        def url_generator(relative_path: str) -> str:
            """Generate StudyFlow-specific API URLs."""
            if relative_path.startswith("materials/"):
                # Extract material ID from path like: materials/{org}/{user}/{material_id}_{filename}
                parts = relative_path.split("/")
                if len(parts) >= 4:
                    filename_part = parts[-1]
                    # Extract material_id from filename (format: {material_id}_{filename})
                    material_id = filename_part.split("_", 1)[0] if "_" in filename_part else filename_part
                    return f"/api/v1/storage/materials/{material_id}"
            return f"/api/v1/storage/{relative_path}"
        
        _storage_file_service = StorageFileService(
            storage_backend=hetzner_storage,
            base_path="kasaai/studyflow",
            local_fallback_path=local_fallback,
            url_generator=url_generator
        )
    
    return _storage_file_service


# Create router using shared storage routes
async def create_studyflow_storage_router() -> APIRouter:
    """
    Create storage router for StudyFlow using shared storage routes.
    
    Returns:
        FastAPI router for file serving
    """
    storage_service = await get_storage_file_service()
    return create_storage_router(
        storage_service=storage_service,
        prefix="/api/v1/storage",
        tags=["storage", "studyflow"]
    )




