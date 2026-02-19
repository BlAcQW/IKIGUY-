"""
Storage File Serving Router.

Serves files uploaded to Hetzner Storage Box without requiring direct authentication.
"""

from fastapi import APIRouter, HTTPException, Response
from typing import Optional
import logging

from apps.shared.storage.hetzner_storage_box import HetznerStorageBox, StorageProtocol
from app.services.gridfs_storage_service import GridFSImageService

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_storage_service() -> HetznerStorageBox:
    """Get or create Hetzner Storage Box service."""
    storage = HetznerStorageBox(
        protocol=StorageProtocol.WEBDAV,
        base_path="kasaai/estateflow"
    )
    if not storage.connected:
        await storage.connect()
    return storage


def get_content_type(file_path: str) -> str:
    """Determine content type from file extension."""
    ext = file_path.lower().split(".")[-1] if "." in file_path else ""

    content_types = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
        "heic": "image/heic",
        "heif": "image/heif",
        "mp4": "video/mp4",
        "mov": "video/quicktime",
        "avi": "video/x-msvideo",
        "webm": "video/webm",
        "txt": "text/plain",
        "json": "application/json",
    }

    return content_types.get(ext, "application/octet-stream")


def get_cache_control(file_path: str) -> str:
    """Get cache control header based on file type."""
    ext = file_path.lower().split(".")[-1] if "." in file_path else ""

    # Images can be cached longer
    if ext in ["jpg", "jpeg", "png", "webp", "gif", "heic", "heif"]:
        return "public, max-age=86400"  # 24 hours

    # Videos
    if ext in ["mp4", "mov", "avi", "webm"]:
        return "public, max-age=3600"  # 1 hour

    # PDFs and documents
    if ext in ["pdf", "txt", "json"]:
        return "public, max-age=3600"  # 1 hour

    # Default: short cache
    return "public, max-age=300"  # 5 minutes


@router.get("/gridfs/{file_id}")
async def serve_gridfs_image(file_id: str):
    """
    Serve image from MongoDB GridFS.

    Streams images stored in GridFS directly to the client. This endpoint is
    public (no authentication required) to allow easy embedding in HTML and
    property listings.

    Args:
        file_id: GridFS ObjectId of the image (original or thumbnail)

    Returns:
        Image content with appropriate headers and caching

    Raises:
        HTTPException: If image not found or invalid file_id
    """
    try:
        # Initialize GridFS service
        service = GridFSImageService()

        # Get image from GridFS
        image_data, mime_type = await service.get_image(file_id)

        # Get filename from file_id (for content-disposition header)
        filename = f"image_{file_id}"

        return Response(
            content=image_data,
            media_type=mime_type,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Cache-Control": "public, max-age=86400, immutable",  # 24 hours, immutable
                "X-Content-Type-Options": "nosniff",  # Security header
            }
        )

    except FileNotFoundError:
        logger.warning(f"GridFS image not found: {file_id}")
        raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        logger.error(f"Failed to serve GridFS image {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to serve image")


@router.get("/{file_path:path}")
async def serve_file(file_path: str):
    """
    Serve file from Hetzner Storage (legacy endpoint).

    Proxies files from storage without requiring user authentication with the storage provider.

    Args:
        file_path: Path to file (e.g., "properties/org_id/property-images/2025/12/file.jpg")

    Returns:
        File content with appropriate headers
    """
    try:
        # Get storage service
        storage = await get_storage_service()

        # Download file content
        file_content = await storage.download_file_content(file_path)

        if not file_content:
            raise HTTPException(status_code=404, detail="File not found")

        # Determine content type
        content_type = get_content_type(file_path)

        # Determine cache duration
        cache_control = get_cache_control(file_path)

        # Get filename
        filename = file_path.split("/")[-1]

        return Response(
            content=file_content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Cache-Control": cache_control,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve file {file_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to serve file: {str(e)}")
