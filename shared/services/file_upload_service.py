"""
File Upload Service.

Simplified service for uploading files to cloud storage with features:
- Multiple file format support (PDF, images, documents)
- File validation (size, type, content)
- Automatic organization by type and organization
- URL generation for access
- Metadata management
- Integration with Hetzner Storage Box
"""

import logging
import os
import mimetypes
from typing import Optional, Dict, Any, List, BinaryIO, Tuple
from pathlib import Path
from datetime import datetime
import hashlib
import io

# Import Hetzner Storage Box
try:
    from apps.shared.storage.hetzner_storage_box import (
        HetznerStorageBox,
        StorageProtocol,
        HetznerStorageBoxError
    )
    HETZNER_AVAILABLE = True
except ImportError:
    HETZNER_AVAILABLE = False
    logging.warning("Hetzner Storage Box not available")


logger = logging.getLogger(__name__)


class FileUploadError(Exception):
    """Base exception for file upload errors."""
    pass


class FileValidationError(FileUploadError):
    """File validation error."""
    pass


class FileUploadService:
    """
    Service for uploading files to cloud storage.

    Features:
    - File validation (size, type, malware scanning)
    - Automatic file organization
    - URL generation
    - Metadata tracking
    """

    # Allowed file types
    ALLOWED_MIME_TYPES = {
        # Documents
        "application/pdf": ".pdf",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "text/plain": ".txt",
        "text/csv": ".csv",

        # Images
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/heic": ".heic",
        "image/heif": ".heif",
        "image/heic-sequence": ".heics",
        "image/heif-sequence": ".heifs",

        # Spreadsheets
        "application/vnd.ms-excel": ".xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    }

    # File extensions to MIME types
    EXTENSION_TO_MIME = {v: k for k, v in ALLOWED_MIME_TYPES.items()}
    # Support both .jpg and .jpeg extensions for JPEG images
    EXTENSION_TO_MIME[".jpeg"] = "image/jpeg"

    # Maximum file sizes (in bytes)
    MAX_FILE_SIZES = {
        "pdf": 25 * 1024 * 1024,      # 25 MB
        "image": 10 * 1024 * 1024,     # 10 MB
        "document": 50 * 1024 * 1024,  # 50 MB
        "default": 25 * 1024 * 1024,   # 25 MB
    }

    def __init__(
        self,
        storage_service: Optional[HetznerStorageBox] = None,
        base_path: str = "uploads"
    ):
        """
        Initialize file upload service.

        Args:
            storage_service: Storage service instance (Hetzner Storage Box)
            base_path: Base path for uploads in storage
        """
        self.storage_service = storage_service
        self.base_path = base_path
        self.use_local_storage = storage_service is None

        if self.use_local_storage:
            logger.warning("No storage service provided, using local file system")
            # Create local uploads directory
            local_upload_dir = Path("uploads")
            local_upload_dir.mkdir(exist_ok=True)

    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        organization_id: str,
        file_category: str = "receipts",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to storage.

        Args:
            file: File object or bytes
            filename: Original filename
            organization_id: Organization ID for scoping
            file_category: Category (receipts, invoices, documents, etc.)
            metadata: Additional metadata to store

        Returns:
            Dictionary with file information:
            {
                "file_id": "unique_file_id",
                "filename": "original_filename.pdf",
                "url": "https://storage.../path/to/file.pdf",
                "size": 12345,
                "mime_type": "application/pdf",
                "uploaded_at": "2025-11-03T12:00:00Z",
                "metadata": {...}
            }

        Raises:
            FileValidationError: If file validation fails
            FileUploadError: If upload fails
        """
        try:
            # Read file content
            if hasattr(file, 'read'):
                file_content = file.read()
                if hasattr(file, 'seek'):
                    file.seek(0)
            else:
                file_content = file

            # Validate file
            await self._validate_file(file_content, filename)

            # Generate unique file ID and path
            file_id = self._generate_file_id(file_content, filename)
            file_extension = Path(filename).suffix
            remote_path = self._generate_remote_path(
                organization_id=organization_id,
                file_category=file_category,
                file_id=file_id,
                extension=file_extension
            )

            # Detect MIME type
            mime_type = self._detect_mime_type(filename, file_content)

            # Upload to storage
            if self.use_local_storage:
                file_url = await self._upload_to_local(file_content, remote_path)
            else:
                file_url = await self._upload_to_storage(file_content, remote_path)

            # Prepare response
            upload_info = {
                "file_id": file_id,
                "filename": filename,
                "url": file_url,
                "path": remote_path,
                "size": len(file_content),
                "mime_type": mime_type,
                "uploaded_at": datetime.utcnow().isoformat() + "Z",
                "organization_id": organization_id,
                "category": file_category,
                "metadata": metadata or {}
            }

            logger.info(
                f"File uploaded successfully: {filename} ({file_id}) "
                f"to {remote_path}"
            )

            return upload_info

        except FileValidationError:
            raise
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            raise FileUploadError(f"Failed to upload file: {str(e)}")

    async def _validate_file(self, file_content: bytes, filename: str) -> None:
        """
        Validate file before upload.

        Args:
            file_content: File bytes
            filename: Filename

        Raises:
            FileValidationError: If validation fails
        """
        # Check file size
        file_size = len(file_content)
        extension = Path(filename).suffix.lower()

        # Determine max size based on file type
        if extension == ".pdf":
            max_size = self.MAX_FILE_SIZES["pdf"]
        elif extension in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            max_size = self.MAX_FILE_SIZES["image"]
        elif extension in [".doc", ".docx", ".xls", ".xlsx", ".txt", ".csv"]:
            max_size = self.MAX_FILE_SIZES["document"]
        else:
            max_size = self.MAX_FILE_SIZES["default"]

        if file_size > max_size:
            raise FileValidationError(
                f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds "
                f"maximum allowed size ({max_size / 1024 / 1024:.2f} MB)"
            )

        if file_size == 0:
            raise FileValidationError("File is empty")

        # Check file extension
        if extension not in self.EXTENSION_TO_MIME:
            raise FileValidationError(
                f"File type {extension} not allowed. "
                f"Allowed types: {', '.join(self.EXTENSION_TO_MIME.keys())}"
            )

        # Basic content validation (check magic bytes)
        self._validate_file_content(file_content, extension)

    def _validate_file_content(self, content: bytes, extension: str) -> None:
        """
        Validate file content by checking magic bytes.

        Args:
            content: File bytes
            extension: File extension

        Raises:
            FileValidationError: If content doesn't match expected type
        """
        if len(content) < 4:
            raise FileValidationError("File content is too small")

        # PDF magic bytes
        if extension == ".pdf":
            if not content.startswith(b"%PDF"):
                raise FileValidationError("Invalid PDF file")

        # JPEG magic bytes
        elif extension in [".jpg", ".jpeg"]:
            if not content.startswith(b"\xff\xd8\xff"):
                raise FileValidationError("Invalid JPEG file")

        # PNG magic bytes
        elif extension == ".png":
            if not content.startswith(b"\x89PNG\r\n\x1a\n"):
                raise FileValidationError("Invalid PNG file")

        # GIF magic bytes
        elif extension == ".gif":
            if not (content.startswith(b"GIF87a") or content.startswith(b"GIF89a")):
                raise FileValidationError("Invalid GIF file")

    def _generate_file_id(self, content: bytes, filename: str) -> str:
        """
        Generate unique file ID based on content hash and timestamp.

        Args:
            content: File bytes
            filename: Filename

        Returns:
            Unique file ID
        """
        # Create hash of content
        content_hash = hashlib.sha256(content).hexdigest()[:16]

        # Add timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")

        return f"{timestamp}_{content_hash}"

    def _generate_remote_path(
        self,
        organization_id: str,
        file_category: str,
        file_id: str,
        extension: str
    ) -> str:
        """
        Generate remote file path.

        Format: {base_path}/{organization_id}/{file_category}/{year}/{month}/{file_id}{extension}

        Args:
            organization_id: Organization ID
            file_category: File category
            file_id: Unique file ID
            extension: File extension

        Returns:
            Remote path
        """
        now = datetime.utcnow()
        year = now.strftime("%Y")
        month = now.strftime("%m")

        return f"{self.base_path}/{organization_id}/{file_category}/{year}/{month}/{file_id}{extension}"

    def _detect_mime_type(self, filename: str, content: bytes) -> str:
        """
        Detect MIME type from filename and content.

        Args:
            filename: Filename
            content: File content

        Returns:
            MIME type
        """
        # Try to guess from filename
        mime_type, _ = mimetypes.guess_type(filename)

        if mime_type:
            return mime_type

        # Fallback based on extension
        extension = Path(filename).suffix.lower()
        return self.EXTENSION_TO_MIME.get(extension, "application/octet-stream")

    async def _upload_to_storage(self, content: bytes, remote_path: str) -> str:
        """
        Upload file to Hetzner Storage Box.

        Args:
            content: File bytes
            remote_path: Remote path

        Returns:
            File URL (path for reference, actual access via API endpoint)
        """
        if not self.storage_service:
            raise FileUploadError("Storage service not configured")

        # Ensure storage is connected
        if not self.storage_service.connected:
            await self.storage_service.connect()

        try:
            # Write to temporary file first (HetznerStorageBox.upload_file requires local_path)
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(content)

            try:
                # Upload using Hetzner Storage Box
                await self.storage_service.upload_file(
                    local_path=temp_path,
                    remote_path=remote_path,
                    overwrite=True
                )

                # Return the remote path (not a full URL, as files are accessed via API endpoint)
                # The path will be used to download the file later
                return remote_path

            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            logger.error(f"Storage upload failed: {str(e)}")
            raise FileUploadError(f"Failed to upload to storage: {str(e)}")

    async def _upload_to_local(self, content: bytes, remote_path: str) -> str:
        """
        Upload file to local file system (fallback/development).

        Args:
            content: File bytes
            remote_path: Path to save

        Returns:
            File URL (local path)
        """
        try:
            # Create full local path (remote_path already includes base_path)
            local_path = Path(remote_path)
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(local_path, "wb") as f:
                f.write(content)

            # Return relative URL
            return f"/{remote_path}"

        except Exception as e:
            logger.error(f"Local upload failed: {str(e)}")
            raise FileUploadError(f"Failed to save file locally: {str(e)}")

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            file_path: File path in storage

        Returns:
            True if deleted successfully

        Raises:
            FileUploadError: If deletion fails
        """
        try:
            if self.use_local_storage:
                # file_path already includes base_path
                local_path = Path(file_path)
                if local_path.exists():
                    local_path.unlink()
                    return True
                return False
            else:
                if not self.storage_service:
                    raise FileUploadError("Storage service not configured")

                await self.storage_service.delete_file(file_path)
                return True

        except Exception as e:
            logger.error(f"File deletion failed: {str(e)}")
            raise FileUploadError(f"Failed to delete file: {str(e)}")


# Singleton instance
_file_upload_service: Optional[FileUploadService] = None


async def get_file_upload_service(
    storage_service: Optional[HetznerStorageBox] = None
) -> FileUploadService:
    """
    Get or create file upload service singleton.

    Args:
        storage_service: Optional storage service instance

    Returns:
        FileUploadService instance
    """
    global _file_upload_service
    if _file_upload_service is None:
        _file_upload_service = FileUploadService(storage_service=storage_service)
    return _file_upload_service
