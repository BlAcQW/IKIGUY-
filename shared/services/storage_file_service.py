"""
Storage File Serving Service.

Part of the Hetzner Storage and Drive Service infrastructure.
Provides generic file serving from storage backends (Hetzner, local, etc.)
without requiring users to authenticate with the storage provider.

This service proxies files through the backend API, making them accessible
to users without exposing storage credentials.

Integrates with:
- HetznerStorageBox for cloud storage
- DriveService for file management
- Local file system for fallback
"""

import os
import logging
import tempfile
from typing import Optional, Dict, Any, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class StorageFileService:
    """
    Generic service for serving files from storage backends.
    
    Part of the Hetzner Storage and Drive Service infrastructure.
    Works with HetznerStorageBox and can be integrated with DriveService.
    
    Works with any storage backend that implements:
    - file_exists(remote_path: str) -> bool
    - download_file(remote_path: str, local_path: str) -> bool
    
    Usage with Hetzner Storage:
        from apps.shared.storage.hetzner_storage_box import get_storage
        from apps.shared.services.storage_file_service import StorageFileService
        
        storage = await get_storage(base_path="kasaai/inkwave")
        file_service = StorageFileService(
            storage_backend=storage,
            base_path="kasaai/inkwave"
        )
    
    Usage with Drive Service:
        from apps.shared.services.drive_service import DriveService
        from apps.shared.services.storage_file_service import StorageFileService
        
        drive = DriveService(db, storage=storage)
        file_service = StorageFileService(
            storage_backend=drive.storage,
            base_path="kasaai/drive"
        )
    """
    
    def __init__(
        self,
        storage_backend: Any,
        base_path: str = "",
        local_fallback_path: Optional[str] = None,
        url_generator: Optional[Callable[[str], str]] = None
    ):
        """
        Initialize storage file service.
        
        Args:
            storage_backend: Storage backend instance (HetznerStorageBox, etc.)
            base_path: Base path within storage (e.g., "kasaai/inkwave")
            local_fallback_path: Local directory path for fallback storage
            url_generator: Function to generate public URLs from file paths
        """
        self.storage_backend = storage_backend
        self.base_path = base_path.strip("/")
        self.local_fallback_path = local_fallback_path
        self.url_generator = url_generator
        # Only use local fallback if NO storage backend is configured
        # local_fallback_path should be a fallback, not the primary source
        self._use_local_fallback = storage_backend is None
        
    def _get_full_remote_path(self, relative_path: str) -> str:
        """Get full remote path including base path."""
        clean_path = relative_path.strip("/")
        if self.base_path:
            return f"{self.base_path}/{clean_path}"
        return clean_path
    
    def _get_local_path(self, relative_path: str) -> str:
        """Get local file path for fallback storage."""
        if not self.local_fallback_path:
            raise ValueError("Local fallback path not configured")
        clean_path = relative_path.strip("/")
        return os.path.join(self.local_fallback_path, clean_path)
    
    def get_public_url(self, relative_path: str, api_base_path: str = "/api/v1/storage") -> str:
        """
        Generate public URL for a file.
        
        Args:
            relative_path: Relative path to file (e.g., "books/book_123.pdf")
            api_base_path: Base path for API endpoints
            
        Returns:
            Public API URL (e.g., "/api/v1/storage/books/book_123.pdf")
        """
        if self.url_generator:
            return self.url_generator(relative_path)
        
        # Default: generate API endpoint URL
        clean_path = relative_path.strip("/")
        return f"{api_base_path}/{clean_path}"
    
    async def download_file(self, relative_path: str) -> Optional[bytes]:
        """
        Download file content from storage.

        Tries remote storage first, then falls back to local if configured.

        Args:
            relative_path: Relative path to file (e.g., "books/book_123.pdf")

        Returns:
            File bytes or None if not found
        """
        # If no storage backend, use local fallback only
        if self._use_local_fallback:
            return self._try_local_download(relative_path)

        if not self.storage_backend:
            logger.warning("No storage backend configured")
            return self._try_local_download(relative_path)

        try:
            full_remote_path = self._get_full_remote_path(relative_path)

            # Check if file exists
            if hasattr(self.storage_backend, 'file_exists'):
                if not await self.storage_backend.file_exists(full_remote_path):
                    logger.debug(f"File not found in remote: {full_remote_path}")
                    # Try local fallback
                    return self._try_local_download(relative_path)

            # Try to use download_file_content if available (more efficient)
            if hasattr(self.storage_backend, 'download_file_content'):
                content = await self.storage_backend.download_file_content(full_remote_path)
                if content is not None:
                    return content

            # Fallback to download_file (downloads to temp file)
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = tmp.name

            try:
                # Download from storage
                await self.storage_backend.download_file(full_remote_path, tmp_path)

                # Read content
                with open(tmp_path, "rb") as f:
                    content = f.read()

                return content
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"Failed to download file {relative_path} from remote: {e}")
            # Try local fallback on remote failure
            return self._try_local_download(relative_path)

    def _try_local_download(self, relative_path: str) -> Optional[bytes]:
        """Try to download from local fallback path."""
        if not self.local_fallback_path:
            return None

        local_path = self._get_local_path(relative_path)
        if os.path.exists(local_path):
            try:
                with open(local_path, "rb") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read local file {local_path}: {e}")
                return None
        return None
    
    async def file_exists(self, relative_path: str) -> bool:
        """
        Check if file exists in storage.

        Checks remote storage first, then local fallback if configured.

        Args:
            relative_path: Relative path to file

        Returns:
            True if file exists in either remote or local storage
        """
        # If no storage backend, check local only
        if self._use_local_fallback:
            return self._local_file_exists(relative_path)

        if not self.storage_backend:
            return self._local_file_exists(relative_path)

        try:
            full_remote_path = self._get_full_remote_path(relative_path)
            if hasattr(self.storage_backend, 'file_exists'):
                exists_remote = await self.storage_backend.file_exists(full_remote_path)
                if exists_remote:
                    return True
                # Check local fallback
                return self._local_file_exists(relative_path)
            return False
        except Exception as e:
            logger.error(f"Failed to check file existence {relative_path} in remote: {e}")
            # Try local fallback
            return self._local_file_exists(relative_path)

    def _local_file_exists(self, relative_path: str) -> bool:
        """Check if file exists in local fallback path."""
        if not self.local_fallback_path:
            return False
        local_path = self._get_local_path(relative_path)
        return os.path.exists(local_path)
    
    async def get_file_url(
        self,
        relative_path: str,
        api_base_path: str = "/api/v1/storage"
    ) -> Optional[str]:
        """
        Get public URL for a file if it exists.
        
        Args:
            relative_path: Relative path to file
            api_base_path: Base path for API endpoints
            
        Returns:
            Public URL or None if file doesn't exist
        """
        if await self.file_exists(relative_path):
            return self.get_public_url(relative_path, api_base_path)
        return None

