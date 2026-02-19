"""
Storage File Serving Routes.

Part of the Hetzner Storage and Drive Service infrastructure.
Generic FastAPI routes for serving files from storage backends
without requiring users to authenticate with the storage provider.

Works with:
- HetznerStorageBox for direct file serving
- DriveService for managed file serving with permissions

Usage with Hetzner Storage:
    from apps.shared.storage.hetzner_storage_box import get_storage
    from apps.shared.services.storage_file_service import StorageFileService
    from apps.shared.routes.storage_routes import create_storage_router
    
    storage = await get_storage(base_path="kasaai/inkwave")
    file_service = StorageFileService(storage_backend=storage, base_path="kasaai/inkwave")
    storage_router = create_storage_router(file_service, prefix="/api/v1/storage")
    app.include_router(storage_router)

Usage with Drive Service:
    from apps.shared.services.drive_service import DriveService
    from apps.shared.services.storage_file_service import StorageFileService
    from apps.shared.routes.storage_routes import create_storage_router
    
    drive = DriveService(db, storage=storage)
    file_service = StorageFileService(storage_backend=drive.storage, base_path="kasaai/drive")
    storage_router = create_storage_router(file_service, prefix="/api/v1/storage")
    app.include_router(storage_router)
"""

from fastapi import APIRouter, HTTPException, Response
from typing import Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)


def create_storage_router(
    storage_service: Any,
    prefix: str = "/api/v1/storage",
    tags: list = None
) -> APIRouter:
    """
    Create a FastAPI router for serving files from storage.
    
    Args:
        storage_service: StorageFileService instance
        prefix: API route prefix
        tags: OpenAPI tags for the router
        
    Returns:
        FastAPI router with file serving endpoints
    """
    if tags is None:
        tags = ["storage"]
    
    router = APIRouter(prefix=prefix, tags=tags)
    
    @router.get("/{file_path:path}")
    async def serve_file(file_path: str):
        """
        Serve file from storage.
        
        Proxies files from storage backend (Hetzner, local, etc.)
        without requiring user authentication with the storage provider.
        
        Args:
            file_path: Path to file (e.g., "books/book_123.pdf" or "covers/book_123")
            
        Returns:
            File content with appropriate headers
        """
        try:
            # Download file content
            file_content = await storage_service.download_file(file_path)
            
            if not file_content:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Determine content type from file extension
            content_type = _get_content_type(file_path)
            
            # Determine cache duration based on file type
            cache_control = _get_cache_control(file_path)
            
            return Response(
                content=file_content,
                media_type=content_type,
                headers={
                    "Content-Disposition": f'inline; filename="{_get_filename(file_path)}"',
                    "Cache-Control": cache_control,
                }
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to serve file {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to serve file: {str(e)}")
    
    return router


def _get_content_type(file_path: str) -> str:
    """Determine content type from file extension."""
    ext = file_path.lower().split(".")[-1] if "." in file_path else ""
    
    content_types = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "mp4": "video/mp4",
        "txt": "text/plain",
        "json": "application/json",
        "xml": "application/xml",
        "html": "text/html",
        "css": "text/css",
        "js": "application/javascript",
    }
    
    return content_types.get(ext, "application/octet-stream")


def _get_cache_control(file_path: str) -> str:
    """Get cache control header based on file type."""
    ext = file_path.lower().split(".")[-1] if "." in file_path else ""
    
    # Images and static assets can be cached longer
    if ext in ["jpg", "jpeg", "png", "webp", "gif", "css", "js"]:
        return "public, max-age=86400"  # 24 hours
    
    # Audio/video files
    if ext in ["mp3", "wav", "mp4"]:
        return "public, max-age=3600"  # 1 hour
    
    # PDFs and documents
    if ext in ["pdf", "txt", "json", "xml"]:
        return "public, max-age=3600"  # 1 hour
    
    # Default: short cache
    return "public, max-age=300"  # 5 minutes


def _get_filename(file_path: str) -> str:
    """Extract filename from path."""
    return file_path.split("/")[-1]

