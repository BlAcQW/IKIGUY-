"""
Storage Service (Stub) for EstateFlow.

Replaces Hetzner Storage Box integration with a local file-based
storage for development. The storage router already has a GridFS
endpoint which is the primary storage mechanism.
"""

import logging
from typing import Optional
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class StorageProtocol(str, Enum):
    """Storage protocol options (kept for API compatibility)."""
    WEBDAV = "webdav"
    SFTP = "sftp"
    LOCAL = "local"


class HetznerStorageBox:
    """
    Stub storage client.

    The primary storage mechanism is MongoDB GridFS (served via
    /api/v1/storage/gridfs/{file_id}). This class exists only to
    prevent import errors in the legacy storage router endpoint.
    """

    def __init__(
        self,
        protocol: StorageProtocol = StorageProtocol.LOCAL,
        base_path: str = "storage",
    ):
        self.protocol = protocol
        self.base_path = Path(base_path)
        self.connected = False
        logger.info("Storage service initialized (local stub mode - use GridFS endpoints instead)")

    async def connect(self):
        """Simulate connection (no-op for local mode)."""
        self.connected = True
        logger.info("Storage service connected (stub)")

    async def download_file_content(self, file_path: str) -> Optional[bytes]:
        """
        Download file content from local storage.

        Falls back to None if file not found, which triggers a 404 in the router.
        """
        full_path = self.base_path / file_path
        if full_path.exists():
            return full_path.read_bytes()

        logger.warning(f"File not found in local storage: {file_path}")
        return None

    async def upload_file(self, file_path: str, content: bytes) -> bool:
        """Upload file to local storage."""
        full_path = self.base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return True
