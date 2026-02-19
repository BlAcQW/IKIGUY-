"""
InkWave Storage Service.

Provides cloud storage for InkWave using Hetzner Storage Box.
Handles book PDFs, cover images, and audio files.

Storage Structure on Hetzner:
    kasaai/inkwave/
    ├── books/           # PDF files
    │   └── {book_id}.pdf
    ├── covers/          # Book cover images
    │   └── {book_id}.{ext}
    ├── author_images/   # Author photos
    │   └── {author_slug}.{ext}
    └── audio/           # Generated audio chunks
        └── {book_id}/
            └── chunk_{index}.mp3

Public URL Format:
    https://{host}/kasaai/inkwave/books/{book_id}.pdf
"""

import os
import logging
import hashlib
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime
import asyncio
import sys

# Add project root to path for shared imports (consistent with main.py)
# From /opt/kasaai/apps/inkwave/backend/app/services/ -> /opt/kasaai/
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.shared.storage.hetzner_storage_box import (
    HetznerStorageBox,
    StorageProtocol,
    HetznerStorageBoxError,
    get_storage
)

logger = logging.getLogger(__name__)


class InkWaveStorageError(Exception):
    """Storage operation error."""
    pass


class InkWaveStorageService:
    """
    Storage service for InkWave book files.

    Handles:
    - PDF book uploads
    - Cover image uploads
    - Audio file uploads
    - Public URL generation
    """

    # Base path within Hetzner storage
    BASE_PATH = "kasaai/inkwave"

    # Subdirectories
    BOOKS_DIR = "books"
    COVERS_DIR = "covers"
    AUTHOR_IMAGES_DIR = "author_images"
    AUDIO_DIR = "audio"

    # Public URL base (WebDAV is accessible via HTTPS)
    PUBLIC_URL_BASE = "https://u497034-sub1.your-storagebox.de"

    def __init__(self):
        """Initialize storage service."""
        self._storage: Optional[HetznerStorageBox] = None
        self._initialized = False
        self._local_fallback = False

        # Local storage path for fallback
        self._local_path = os.getenv(
            "STORAGE_PATH",
            "/opt/kasaai/apps/inkwave/storage"
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

            # Initialize Hetzner storage
            self._storage = HetznerStorageBox(
                protocol=StorageProtocol.WEBDAV,
                base_path=self.BASE_PATH
            )
            await self._storage.connect()

            # Ensure directories exist
            await self._ensure_directories()

            self._initialized = True
            logger.info("✅ InkWave Storage Service connected to Hetzner")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to Hetzner, using local storage: {e}")
            self._local_fallback = True
            self._initialized = True
            return False

    async def _ensure_directories(self):
        """Create required directories on Hetzner storage."""
        if self._storage and self._storage.connected:
            dirs = [
                self.BOOKS_DIR,
                self.COVERS_DIR,
                self.AUTHOR_IMAGES_DIR,
                self.AUDIO_DIR
            ]
            for dir_name in dirs:
                try:
                    await self._storage.create_directory(dir_name)
                except Exception as e:
                    logger.debug(f"Directory may already exist: {dir_name} - {e}")

    def _get_public_url(self, remote_path: str) -> str:
        """
        Generate public URL for a stored file.
        
        Uses backend API endpoint instead of direct Hetzner URL
        to avoid requiring Hetzner authentication.

        Args:
            remote_path: Path within Hetzner storage

        Returns:
            Backend API URL that proxies the file
        """
        # Clean the path
        clean_path = remote_path.strip("/")
        
        # Use backend API endpoint instead of direct Hetzner URL
        # This way users don't need Hetzner credentials
        if clean_path.startswith(self.BOOKS_DIR):
            # Extract book_id from path (e.g., "books/book_123.pdf" -> "book_123")
            book_id = clean_path.replace(f"{self.BOOKS_DIR}/", "").replace(".pdf", "")
            return f"/api/v1/storage/books/{book_id}.pdf"
        elif clean_path.startswith(self.COVERS_DIR):
            # Extract book_id from path (e.g., "covers/book_123.jpg" -> "book_123")
            book_id = clean_path.replace(f"{self.COVERS_DIR}/", "").split(".")[0]
            return f"/api/v1/storage/covers/{book_id}"
        
        # Fallback to old format for other files
        return f"{self.PUBLIC_URL_BASE}/{self.BASE_PATH}/{clean_path}"

    def _get_local_path(self, relative_path: str) -> str:
        """Get local storage path."""
        return os.path.join(self._local_path, relative_path)

    async def upload_book_pdf(
        self,
        book_id: str,
        file_content: bytes,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload book PDF to storage.

        Args:
            book_id: Book identifier
            file_content: PDF file bytes
            filename: Original filename (optional)

        Returns:
            Dict with storage_path, public_url, size, checksum
        """
        if not self._initialized:
            await self.initialize()

        remote_path = f"{self.BOOKS_DIR}/{book_id}.pdf"
        checksum = hashlib.md5(file_content).hexdigest()

        if self._local_fallback:
            # Save locally
            local_path = self._get_local_path(remote_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(file_content)

            logger.info(f"📚 Saved book PDF locally: {local_path}")
            return {
                "storage_path": local_path,
                "public_url": f"/api/v1/storage/books/{book_id}.pdf",
                "size": len(file_content),
                "checksum": checksum,
                "storage_type": "local"
            }

        try:
            # Save to temp file for upload
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(file_content)
                tmp_path = tmp.name

            # Upload to Hetzner
            await self._storage.upload_file(tmp_path, remote_path)

            # Clean up temp file
            os.unlink(tmp_path)

            public_url = self._get_public_url(remote_path)
            logger.info(f"📚 Uploaded book PDF to Hetzner: {remote_path}")

            return {
                "storage_path": f"{self.BASE_PATH}/{remote_path}",
                "public_url": public_url,
                "size": len(file_content),
                "checksum": checksum,
                "storage_type": "hetzner"
            }

        except Exception as e:
            logger.error(f"❌ Failed to upload book PDF: {e}")
            raise InkWaveStorageError(f"Book upload failed: {e}")

    async def upload_cover_image(
        self,
        book_id: str,
        file_content: bytes,
        content_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """
        Upload book cover image to storage.

        Args:
            book_id: Book identifier
            file_content: Image file bytes
            content_type: MIME type of image

        Returns:
            Dict with storage_path, public_url, size
        """
        if not self._initialized:
            await self.initialize()

        # Determine extension from content type
        ext_map = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
            "image/gif": "gif"
        }
        ext = ext_map.get(content_type, "jpg")
        remote_path = f"{self.COVERS_DIR}/{book_id}.{ext}"

        if self._local_fallback:
            local_path = self._get_local_path(remote_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(file_content)

            logger.info(f"🖼️ Saved cover image locally: {local_path}")
            return {
                "storage_path": local_path,
                "public_url": f"/api/v1/storage/covers/{book_id}",
                "size": len(file_content),
                "storage_type": "local"
            }

        try:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                tmp.write(file_content)
                tmp_path = tmp.name

            await self._storage.upload_file(tmp_path, remote_path)
            os.unlink(tmp_path)

            public_url = self._get_public_url(remote_path)
            logger.info(f"🖼️ Uploaded cover image to Hetzner: {remote_path} -> {public_url}")

            return {
                "storage_path": f"{self.BASE_PATH}/{remote_path}",
                "public_url": public_url,  # This now returns /api/v1/storage/covers/{book_id}
                "size": len(file_content),
                "storage_type": "hetzner"
            }

        except Exception as e:
            logger.error(f"❌ Failed to upload cover image: {e}")
            raise InkWaveStorageError(f"Cover upload failed: {e}")

    async def upload_audio_chunk(
        self,
        book_id: str,
        chunk_index: int,
        audio_content: bytes,
        audio_format: str = "mp3"
    ) -> Dict[str, Any]:
        """
        Upload audio chunk to storage.

        Args:
            book_id: Book identifier
            chunk_index: Chunk index number
            audio_content: Audio file bytes
            audio_format: Audio format (mp3, wav)

        Returns:
            Dict with storage_path, public_url, size, duration
        """
        if not self._initialized:
            await self.initialize()

        remote_path = f"{self.AUDIO_DIR}/{book_id}/chunk_{chunk_index}.{audio_format}"

        if self._local_fallback:
            local_path = self._get_local_path(remote_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(audio_content)

            logger.info(f"🎵 Saved audio chunk locally: {local_path}")
            return {
                "storage_path": local_path,
                "public_url": f"/storage/{remote_path}",
                "size": len(audio_content),
                "storage_type": "local"
            }

        try:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as tmp:
                tmp.write(audio_content)
                tmp_path = tmp.name

            # Ensure book audio directory exists
            await self._storage.create_directory(f"{self.AUDIO_DIR}/{book_id}")
            await self._storage.upload_file(tmp_path, remote_path)
            os.unlink(tmp_path)

            public_url = self._get_public_url(remote_path)
            logger.info(f"🎵 Uploaded audio chunk to Hetzner: {remote_path}")

            return {
                "storage_path": f"{self.BASE_PATH}/{remote_path}",
                "public_url": public_url,
                "size": len(audio_content),
                "storage_type": "hetzner"
            }

        except Exception as e:
            logger.error(f"❌ Failed to upload audio chunk: {e}")
            raise InkWaveStorageError(f"Audio upload failed: {e}")

    async def delete_book_files(self, book_id: str) -> bool:
        """
        Delete all files associated with a book.

        Args:
            book_id: Book identifier

        Returns:
            True if deletion successful
        """
        if not self._initialized:
            await self.initialize()

        deleted_files = []

        # Files to delete
        files_to_delete = [
            f"{self.BOOKS_DIR}/{book_id}.pdf",
            f"{self.COVERS_DIR}/{book_id}.jpg",
            f"{self.COVERS_DIR}/{book_id}.png",
            f"{self.COVERS_DIR}/{book_id}.webp",
        ]

        if self._local_fallback:
            for file_path in files_to_delete:
                local_path = self._get_local_path(file_path)
                if os.path.exists(local_path):
                    os.unlink(local_path)
                    deleted_files.append(file_path)

            # Delete audio directory
            audio_dir = self._get_local_path(f"{self.AUDIO_DIR}/{book_id}")
            if os.path.exists(audio_dir):
                import shutil
                shutil.rmtree(audio_dir)
                deleted_files.append(f"{self.AUDIO_DIR}/{book_id}/")

        else:
            for file_path in files_to_delete:
                try:
                    if await self._storage.file_exists(file_path):
                        await self._storage.delete_file(file_path)
                        deleted_files.append(file_path)
                except Exception as e:
                    logger.debug(f"File may not exist: {file_path} - {e}")

            # Delete audio directory (list and delete all files)
            try:
                audio_path = f"{self.AUDIO_DIR}/{book_id}"
                if await self._storage.file_exists(audio_path):
                    files = await self._storage.list_files(audio_path)
                    for f in files:
                        await self._storage.delete_file(f["path"])
                    deleted_files.append(audio_path)
            except Exception as e:
                logger.debug(f"Audio directory may not exist: {e}")

        logger.info(f"🗑️ Deleted {len(deleted_files)} files for book {book_id}")
        return True

    async def get_book_pdf_url(self, book_id: str) -> Optional[str]:
        """Get public URL for book PDF (uses backend API endpoint)."""
        remote_path = f"{self.BOOKS_DIR}/{book_id}.pdf"

        if self._local_fallback:
            local_path = self._get_local_path(remote_path)
            if os.path.exists(local_path):
                return f"/api/v1/storage/books/{book_id}.pdf"
            return None

        # Check if file exists in Hetzner
        # HetznerStorageBox.file_exists() already prepends base_path internally
        if await self._storage.file_exists(remote_path):
            return self._get_public_url(remote_path)
        return None

    async def get_cover_url(self, book_id: str) -> Optional[str]:
        """Get public URL for book cover (uses backend API endpoint)."""
        for ext in ["jpg", "png", "webp"]:
            remote_path = f"{self.COVERS_DIR}/{book_id}.{ext}"

            if self._local_fallback:
                local_path = self._get_local_path(remote_path)
                if os.path.exists(local_path):
                    return f"/api/v1/storage/covers/{book_id}"
            else:
                # Check if file exists in Hetzner
                # HetznerStorageBox.file_exists() already prepends base_path internally
                if await self._storage.file_exists(remote_path):
                    return self._get_public_url(remote_path)

        return None

    async def download_book_pdf(self, book_id: str) -> Optional[bytes]:
        """
        Download book PDF file content.
        
        Args:
            book_id: Book identifier
            
        Returns:
            PDF file bytes or None if not found
        """
        if not self._initialized:
            await self.initialize()
        
        remote_path = f"{self.BOOKS_DIR}/{book_id}.pdf"
        
        if self._local_fallback:
            local_path = self._get_local_path(remote_path)
            if os.path.exists(local_path):
                with open(local_path, "rb") as f:
                    return f.read()
            return None
        
        try:
            # Download from Hetzner
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp_path = tmp.name

            # HetznerStorageBox already prepends base_path internally via _get_full_path()
            # So we only need to pass the relative path (e.g., "books/book_xxx.pdf")
            await self._storage.download_file(remote_path, tmp_path)
            
            with open(tmp_path, "rb") as f:
                content = f.read()
            
            os.unlink(tmp_path)
            return content
        except Exception as e:
            logger.error(f"Failed to download book PDF {book_id}: {e}")
            return None
    
    async def download_cover_image(self, book_id: str, ext: str = "jpg") -> Optional[bytes]:
        """
        Download book cover image content.
        
        Args:
            book_id: Book identifier
            ext: Image extension (jpg, png, webp)
            
        Returns:
            Image file bytes or None if not found
        """
        if not self._initialized:
            await self.initialize()
        
        remote_path = f"{self.COVERS_DIR}/{book_id}.{ext}"
        
        if self._local_fallback:
            local_path = self._get_local_path(remote_path)
            if os.path.exists(local_path):
                with open(local_path, "rb") as f:
                    return f.read()
            return None
        
        try:
            # Download from Hetzner
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                tmp_path = tmp.name

            # HetznerStorageBox already prepends base_path internally via _get_full_path()
            await self._storage.download_file(remote_path, tmp_path)
            
            with open(tmp_path, "rb") as f:
                content = f.read()
            
            os.unlink(tmp_path)
            return content
        except Exception as e:
            logger.debug(f"Cover image {book_id}.{ext} not found: {e}")
            return None

    async def close(self):
        """Close storage connection."""
        if self._storage:
            await self._storage.disconnect()
            self._storage = None
            self._initialized = False


# Global service instance
_storage_service: Optional[InkWaveStorageService] = None


async def get_storage_service() -> InkWaveStorageService:
    """
    Get or create storage service instance.

    Returns:
        InkWaveStorageService instance
    """
    global _storage_service

    if _storage_service is None:
        _storage_service = InkWaveStorageService()
        await _storage_service.initialize()

    return _storage_service
