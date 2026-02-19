"""
File Upload Service (Stub) for EstateFlow.

Provides local file-based upload handling. The primary upload path uses
GridFS endpoints. This stub prevents import errors in the legacy
Hetzner Storage upload router.
"""

import logging
import hashlib
import os
from datetime import datetime
from typing import Any, Dict, Optional, BinaryIO, Union

logger = logging.getLogger(__name__)


class FileValidationError(Exception):
    """Raised when file validation fails (type, size, etc.)."""
    pass


class FileUploadError(Exception):
    """Raised when file upload fails."""
    pass


class FileUploadService:
    """
    Local file upload service.

    Stores files to local filesystem via the storage service.
    Used as fallback; primary upload path is GridFS.
    """

    # Allowed image MIME types
    ALLOWED_IMAGE_TYPES = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/heic": ".heic",
        "image/heif": ".heif",
    }

    def __init__(self, storage_service=None, base_path: str = "uploads"):
        self.storage_service = storage_service
        self.base_path = base_path

    async def upload_file(
        self,
        file: Union[BinaryIO, bytes],
        filename: str,
        organization_id: str,
        file_category: str = "files",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Upload a file.

        Args:
            file: File-like object or bytes
            filename: Original filename
            organization_id: Organization ID
            file_category: Category (e.g. "property-images")
            metadata: Additional metadata

        Returns:
            Upload info dict

        Raises:
            FileValidationError: If file type not allowed
            FileUploadError: If upload fails
        """
        try:
            # Read content
            if isinstance(file, bytes):
                content = file
            else:
                content = file.read()

            # Generate path
            content_hash = hashlib.sha256(content).hexdigest()[:16]
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            file_id = f"{timestamp}_{content_hash}"
            ext = os.path.splitext(filename)[1] or ".bin"

            now = datetime.utcnow()
            remote_path = (
                f"{self.base_path}/{organization_id}/{file_category}"
                f"/{now.strftime('%Y')}/{now.strftime('%m')}/{file_id}{ext}"
            )

            # Upload via storage service if available
            if self.storage_service:
                await self.storage_service.upload_file(remote_path, content)

            return {
                "file_id": file_id,
                "filename": filename,
                "url": remote_path,
                "path": remote_path,
                "size": len(content),
                "mime_type": metadata.get("content_type", "application/octet-stream") if metadata else "application/octet-stream",
                "uploaded_at": now.isoformat() + "Z",
            }

        except FileValidationError:
            raise
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            raise FileUploadError(str(e))
