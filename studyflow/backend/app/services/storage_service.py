"""
StudyFlow Storage Service.

Provides cloud storage for StudyFlow using shared Hetzner Storage Box.
Handles study material file uploads and downloads.

Storage Structure on Hetzner:
    kasaai/studyflow/
    ├── materials/        # Study material files
    │   └── {organization_id}/
    │       └── {user_id}/
    │           └── {material_id}_{filename}

Public URL Format (via API proxy):
    /api/v1/storage/materials/{material_id}
"""

import os
import logging
from typing import Optional
from pathlib import Path
from datetime import datetime

# Add shared to path
import sys
sys.path.insert(0, '/opt/kasaai/apps')

from apps.shared.storage.hetzner_storage_box import (
    HetznerStorageBox,
    HetznerStorageBoxError,
    get_storage
)

logger = logging.getLogger(__name__)


class StudyFlowStorageError(Exception):
    """Storage operation error."""
    pass


class StudyFlowStorageService:
    """
    Storage service for StudyFlow material files.
    
    Uses shared Hetzner Storage Box for cloud storage.
    """

    # Base path within Hetzner storage
    BASE_PATH = "kasaai/studyflow"

    # Subdirectories
    MATERIALS_DIR = "materials"

    def __init__(self):
        """Initialize storage service."""
        self._storage: Optional[HetznerStorageBox] = None
        self._initialized = False
        self._local_fallback = False

        # Local storage path for fallback
        self._local_path = os.getenv(
            "STORAGE_PATH",
            "/opt/kasaai/apps/studyflow/storage"
        )

    async def initialize(self) -> bool:
        """
        Initialize connection to Hetzner Storage Box.
        
        Returns:
            True if connected successfully, False if falling back to local
        """
        if self._initialized:
            return not self._local_fallback

        try:
            # Check if Hetzner credentials are configured
            password = os.getenv("HETZNER_STORAGE_PASSWORD")
            if not password:
                logger.warning("HETZNER_STORAGE_PASSWORD not set, using local storage")
                self._local_fallback = True
                self._initialized = True
                return False

            # Initialize Hetzner storage using shared service
            self._storage = await get_storage(base_path=self.BASE_PATH)
            await self._storage.connect()
            
            self._initialized = True
            self._local_fallback = False
            logger.info("✅ Connected to Hetzner Storage Box for StudyFlow")
            return True

        except Exception as e:
            logger.warning(f"Failed to connect to Hetzner Storage: {e}. Using local storage.")
            self._local_fallback = True
            self._initialized = True
            return False

    async def upload_material_file(
        self,
        file_content: bytes,
        filename: str,
        material_id: str,
        organization_id: str,
        user_id: str
    ) -> str:
        """
        Upload material file to storage.
        
        Args:
            file_content: File content bytes
            filename: Original filename
            material_id: Material ID
            organization_id: Organization ID
            user_id: User ID who uploaded
            
        Returns:
            Storage path (relative to base_path)
            
        Raises:
            StudyFlowStorageError: If upload fails
        """
        if not self._initialized:
            await self.initialize()

        # Generate storage path
        # Format: materials/{organization_id}/{user_id}/{material_id}_{filename}
        safe_filename = self._sanitize_filename(filename)
        storage_path = f"{self.MATERIALS_DIR}/{organization_id}/{user_id}/{material_id}_{safe_filename}"

        try:
            if self._local_fallback:
                # Save to local storage
                local_dir = Path(self._local_path) / self.MATERIALS_DIR / organization_id / user_id
                local_dir.mkdir(parents=True, exist_ok=True)
                local_file = local_dir / f"{material_id}_{safe_filename}"
                local_file.write_bytes(file_content)
                logger.info(f"File saved locally: {local_file}")
                return storage_path
            else:
                # Upload to Hetzner
                await self._storage.upload_file(
                    file_content=file_content,
                    remote_path=storage_path
                )
                logger.info(f"File uploaded to Hetzner: {storage_path}")
                return storage_path

        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise StudyFlowStorageError(f"Upload failed: {e}")

    async def download_material_file(self, storage_path: str) -> Optional[bytes]:
        """
        Download material file from storage.
        
        Args:
            storage_path: Storage path (relative to base_path)
            
        Returns:
            File content as bytes, or None if not found
        """
        if not self._initialized:
            await self.initialize()

        try:
            if self._local_fallback:
                # Read from local storage
                local_file = Path(self._local_path) / storage_path
                if not local_file.exists():
                    return None
                return local_file.read_bytes()
            else:
                # Download from Hetzner
                return await self._storage.download_file_content(storage_path)

        except Exception as e:
            logger.error(f"Failed to download file {storage_path}: {e}")
            return None

    async def delete_material_file(self, storage_path: str) -> bool:
        """
        Delete material file from storage.
        
        Args:
            storage_path: Storage path (relative to base_path)
            
        Returns:
            True if deleted successfully
        """
        if not self._initialized:
            await self.initialize()

        try:
            if self._local_fallback:
                # Delete from local storage
                local_file = Path(self._local_path) / storage_path
                if local_file.exists():
                    local_file.unlink()
                    logger.info(f"File deleted locally: {local_file}")
                return True
            else:
                # Delete from Hetzner
                await self._storage.delete_file(storage_path)
                logger.info(f"File deleted from Hetzner: {storage_path}")
                return True

        except Exception as e:
            logger.error(f"Failed to delete file {storage_path}: {e}")
            return False

    def get_public_url(self, material_id: str) -> str:
        """
        Get public URL for material file (via API proxy).
        
        Args:
            material_id: Material ID
            
        Returns:
            Public URL for accessing the file
        """
        # Use API proxy endpoint (no Hetzner auth required)
        return f"/api/v1/storage/materials/{material_id}"

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to remove dangerous characters."""
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        safe_name = filename
        for char in dangerous_chars:
            safe_name = safe_name.replace(char, '_')
        return safe_name.strip()


# Global instance
_storage_service_instance: Optional[StudyFlowStorageService] = None


async def get_storage_service() -> StudyFlowStorageService:
    """
    Get or create storage service instance.
    
    Returns:
        Initialized StudyFlowStorageService
    """
    global _storage_service_instance
    
    if _storage_service_instance is None:
        _storage_service_instance = StudyFlowStorageService()
        await _storage_service_instance.initialize()
    
    return _storage_service_instance




