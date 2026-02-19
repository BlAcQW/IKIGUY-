"""
Hetzner Storage Box integration service for African Language Community Platform.

This module provides a backward-compatible wrapper around the shared HetznerStorageBox
service, handling file uploads, downloads, and management for datasets, models, and notebooks.

Uses shared library: @shared/storage/hetzner_storage_box.py
"""

import os
import sys
import hashlib
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from urllib.parse import quote
import logging

# Add shared library to path
sys.path.insert(0, '/opt/kasaai/apps')

from shared.storage.hetzner_storage_box import (
    HetznerStorageBox,
    StorageProtocol,
    HetznerStorageBoxError,
    get_storage
)

logger = logging.getLogger(__name__)


class HetznerStorageService:
    """
    Backward-compatible wrapper around shared HetznerStorageBox.

    Provides synchronous interface for legacy code while using the shared
    async storage implementation internally.

    Storage structure:
    /african-languages/
    ├── datasets/{language_code}/{type}/{uuid}/v{version}/
    ├── models/{model_type}/{uuid}/v{version}/
    ├── notebooks/{language_code}/{uuid}/v{version}/
    └── user-uploads/{user_id}/{upload_uuid}/
    """

    def __init__(
        self,
        host: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        private_key_path: Optional[str] = None,
        port: int = 23,
        base_path: str = "/african-languages",
        protocol: StorageProtocol = StorageProtocol.SFTP
    ):
        """
        Initialize Hetzner Storage Box connection.

        Args:
            host: Hetzner Storage Box hostname (default: from env HETZNER_STORAGE_HOST)
            username: Storage Box username (default: from env HETZNER_STORAGE_USERNAME)
            password: Storage Box password (default: from env HETZNER_STORAGE_PASSWORD)
            private_key_path: Path to SSH private key (alternative to password)
            port: SFTP port (default 23 for Hetzner)
            base_path: Base directory for all language resources
            protocol: Protocol to use (SFTP or WEBDAV)
        """
        self.host = host or os.getenv("HETZNER_STORAGE_HOST", "u497034-sub1.your-storagebox.de")
        self.username = username or os.getenv("HETZNER_STORAGE_USERNAME", "u497034-sub1")
        self.password = password or os.getenv("HETZNER_STORAGE_PASSWORD")
        self.private_key_path = private_key_path
        self.port = port
        self.base_path = base_path.strip("/")
        self.protocol = protocol

        # Initialize the shared storage client
        self._storage: Optional[HetznerStorageBox] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _get_storage(self) -> HetznerStorageBox:
        """Get or create the shared storage instance."""
        if self._storage is None:
            self._storage = HetznerStorageBox(
                username=self.username,
                password=self.password,
                host=self.host,
                protocol=self.protocol,
                base_path=self.base_path
            )
        return self._storage

    def _run_async(self, coro):
        """Run async coroutine in sync context."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create a new loop for nested calls
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result()
            return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(coro)

    def connect(self):
        """Establish connection to Hetzner Storage Box."""
        storage = self._get_storage()
        if not storage.connected:
            self._run_async(storage.connect())
        logger.info(f"Connected to Hetzner Storage Box: {self.host}")

    def disconnect(self):
        """Close connection."""
        if self._storage and self._storage.connected:
            self._run_async(self._storage.disconnect())
        logger.info("Disconnected from Hetzner Storage Box")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def _get_full_path(self, relative_path: str) -> str:
        """Convert relative path to full storage path."""
        return f"/{self.base_path}/{relative_path.lstrip('/')}"

    def upload_file(
        self,
        local_file_path_or_bytes: Any,
        remote_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        compute_checksum: bool = True
    ) -> Dict[str, Any]:
        """
        Upload file to Hetzner Storage Box.

        Args:
            local_file_path_or_bytes: Path to local file OR bytes content
            remote_path: Relative path on storage
            metadata: Optional metadata to store alongside file
            compute_checksum: Whether to compute SHA256 checksum

        Returns:
            Dict with upload details (path, size, checksum, etc.)
        """
        storage = self._get_storage()
        if not storage.connected:
            self.connect()

        # Handle bytes input (for backward compatibility)
        if isinstance(local_file_path_or_bytes, bytes):
            return self.upload_from_bytes(local_file_path_or_bytes, remote_path, metadata)

        local_file_path = local_file_path_or_bytes

        # Compute checksum if requested
        checksum = None
        if compute_checksum:
            checksum = self._compute_file_checksum(local_file_path)

        # Get file size
        file_size = os.path.getsize(local_file_path)

        try:
            self._run_async(storage.upload_file(
                local_path=local_file_path,
                remote_path=remote_path,
                overwrite=True
            ))

            logger.info(f"Uploaded file: {local_file_path} -> {remote_path}")

            # Store metadata if provided
            if metadata:
                metadata_content = self._serialize_metadata({
                    **metadata,
                    "uploaded_at": datetime.utcnow().isoformat(),
                    "file_size": file_size,
                    "checksum": checksum
                })
                metadata_path = f"{remote_path}.meta.json"
                self._write_metadata(metadata_path, metadata_content)

            return {
                "success": True,
                "remote_path": remote_path,
                "full_path": self._get_full_path(remote_path),
                "file_size": file_size,
                "checksum": checksum,
                "uploaded_at": datetime.utcnow()
            }

        except HetznerStorageBoxError as e:
            logger.error(f"Failed to upload file {local_file_path}: {e}")
            raise

    def upload_from_bytes(
        self,
        file_content: bytes,
        remote_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload file from bytes to Hetzner Storage Box.

        Args:
            file_content: File content as bytes
            remote_path: Relative path on storage
            metadata: Optional metadata

        Returns:
            Dict with upload details
        """
        import tempfile

        storage = self._get_storage()
        if not storage.connected:
            self.connect()

        # Compute checksum
        checksum = hashlib.sha256(file_content).hexdigest()
        file_size = len(file_content)

        # Write bytes to temp file and upload
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        try:
            self._run_async(storage.upload_file(
                local_path=tmp_path,
                remote_path=remote_path,
                overwrite=True
            ))

            logger.info(f"Uploaded bytes to: {remote_path}")

            # Store metadata if provided
            if metadata:
                metadata_content = self._serialize_metadata({
                    **metadata,
                    "uploaded_at": datetime.utcnow().isoformat(),
                    "file_size": file_size,
                    "checksum": checksum
                })
                metadata_path = f"{remote_path}.meta.json"
                self._write_metadata(metadata_path, metadata_content)

            return {
                "success": True,
                "remote_path": remote_path,
                "full_path": self._get_full_path(remote_path),
                "file_size": file_size,
                "checksum": checksum,
                "uploaded_at": datetime.utcnow()
            }

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def _write_metadata(self, path: str, content: str):
        """Write metadata file to storage."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            storage = self._get_storage()
            self._run_async(storage.upload_file(
                local_path=tmp_path,
                remote_path=path,
                overwrite=True
            ))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def download_file(
        self,
        remote_path: str,
        local_file_path: str,
        verify_checksum: bool = False
    ) -> Dict[str, Any]:
        """
        Download file from Hetzner Storage Box.

        Args:
            remote_path: Relative path on storage
            local_file_path: Local destination path
            verify_checksum: Whether to verify checksum after download

        Returns:
            Dict with download details
        """
        storage = self._get_storage()
        if not storage.connected:
            self.connect()

        try:
            # Ensure local directory exists
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            self._run_async(storage.download_file(
                remote_path=remote_path,
                local_path=local_file_path,
                overwrite=True
            ))

            logger.info(f"Downloaded file: {remote_path} -> {local_file_path}")

            file_size = os.path.getsize(local_file_path)

            return {
                "success": True,
                "local_path": local_file_path,
                "file_size": file_size,
                "downloaded_at": datetime.utcnow()
            }

        except HetznerStorageBoxError as e:
            logger.error(f"Failed to download file {remote_path}: {e}")
            raise

    def download_to_bytes(self, remote_path: str) -> bytes:
        """
        Download file as bytes.

        Args:
            remote_path: Relative path on storage

        Returns:
            File content as bytes
        """
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            self.download_file(remote_path, tmp_path)
            with open(tmp_path, 'rb') as f:
                return f.read()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def list_files(
        self,
        remote_path: str,
        recursive: bool = False,
        file_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List files in directory.

        Args:
            remote_path: Relative directory path
            recursive: Whether to list recursively
            file_filter: File extension filter (e.g., '.wav')

        Returns:
            List of file info dicts
        """
        storage = self._get_storage()
        if not storage.connected:
            self.connect()

        try:
            files = self._run_async(storage.list_files(
                remote_path=remote_path,
                recursive=recursive
            ))

            # Apply file filter if provided
            if file_filter:
                files = [f for f in files if f.get('name', '').endswith(file_filter)]

            # Convert to expected format
            result = []
            for f in files:
                if not f.get('is_directory', False):
                    result.append({
                        "path": f.get('path', '').lstrip('/'),
                        "filename": f.get('name', ''),
                        "size": f.get('size', 0),
                        "modified_at": f.get('modified')
                    })

            return result

        except HetznerStorageBoxError as e:
            logger.error(f"Failed to list files in {remote_path}: {e}")
            raise

    def delete_file(self, remote_path: str) -> bool:
        """
        Delete file from storage.

        Args:
            remote_path: Relative path to file

        Returns:
            True if successful
        """
        storage = self._get_storage()
        if not storage.connected:
            self.connect()

        try:
            self._run_async(storage.delete_file(remote_path))
            logger.info(f"Deleted file: {remote_path}")

            # Also delete metadata file if exists
            try:
                self._run_async(storage.delete_file(f"{remote_path}.meta.json"))
            except Exception:
                pass  # Metadata file might not exist

            return True

        except HetznerStorageBoxError as e:
            logger.error(f"Failed to delete file {remote_path}: {e}")
            raise

    def get_file_metadata(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata.

        Args:
            remote_path: Relative path to file

        Returns:
            Metadata dict or None if not found
        """
        try:
            metadata_content = self.download_to_bytes(f"{remote_path}.meta.json")
            return self._deserialize_metadata(metadata_content.decode('utf-8'))
        except Exception:
            return None

    def file_exists(self, remote_path: str) -> bool:
        """
        Check if file exists.

        Args:
            remote_path: Relative path to file

        Returns:
            True if file exists
        """
        storage = self._get_storage()
        if not storage.connected:
            self.connect()

        return self._run_async(storage.file_exists(remote_path))

    def verify_integrity(self, remote_path: str, expected_checksum: str) -> bool:
        """
        Verify file integrity using checksum.

        Args:
            remote_path: Relative path to file
            expected_checksum: Expected SHA256 checksum

        Returns:
            True if checksum matches
        """
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            self.download_file(remote_path, tmp_path)
            actual_checksum = self._compute_file_checksum(tmp_path)
            return actual_checksum == expected_checksum
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def generate_download_url(
        self,
        remote_path: str,
        expiry_hours: int = 1
    ) -> str:
        """
        Generate download URL for file.

        Note: Hetzner Storage Box supports WebDAV access.
        This creates a WebDAV URL (requires authentication).

        Args:
            remote_path: Relative path to file
            expiry_hours: URL expiry time in hours (informational)

        Returns:
            WebDAV URL for download
        """
        # Use configured WebDAV URL or construct from host
        webdav_host = os.getenv("HETZNER_WEBDAV_URL", f"https://{self.host}")
        encoded_path = quote(f"/{self.base_path}/{remote_path.lstrip('/')}")
        return f"{webdav_host}{encoded_path}"

    @staticmethod
    def _compute_file_checksum(file_path: str) -> str:
        """Compute SHA256 checksum of file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def _serialize_metadata(metadata: Dict[str, Any]) -> str:
        """Serialize metadata to JSON string."""
        import json
        return json.dumps(metadata, indent=2, default=str)

    @staticmethod
    def _deserialize_metadata(content: str) -> Dict[str, Any]:
        """Deserialize metadata from JSON string."""
        import json
        return json.loads(content)


# Factory function for backward compatibility
def get_storage_service() -> HetznerStorageService:
    """
    Get configured Hetzner Storage Service instance.

    Environment variables:
    - HETZNER_STORAGE_HOST
    - HETZNER_STORAGE_USERNAME
    - HETZNER_STORAGE_PASSWORD
    - HETZNER_STORAGE_PORT (default: 23)
    - HETZNER_STORAGE_BASE_PATH (default: /african-languages)
    """
    return HetznerStorageService(
        host=os.getenv("HETZNER_STORAGE_HOST"),
        username=os.getenv("HETZNER_STORAGE_USERNAME"),
        password=os.getenv("HETZNER_STORAGE_PASSWORD"),
        port=int(os.getenv("HETZNER_STORAGE_PORT", "23")),
        base_path=os.getenv("HETZNER_STORAGE_BASE_PATH", "/african-languages")
    )


# Async helper for FastAPI routes
async def get_async_storage() -> HetznerStorageBox:
    """
    Get async storage instance for FastAPI routes.

    Returns:
        Connected HetznerStorageBox instance
    """
    return await get_storage(
        protocol=StorageProtocol.SFTP,
        base_path=os.getenv("HETZNER_STORAGE_BASE_PATH", "african-languages")
    )
