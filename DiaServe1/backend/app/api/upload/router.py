"""
Property Media Upload Router.

Handles file uploads (images and videos) for properties using Hetzner Storage Box.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List, Optional
import logging
from pydantic import BaseModel

from app.core.auth import get_current_user, get_organization_context
from app.integration.storage_service import HetznerStorageBox, StorageProtocol
from app.integration.file_upload_service import FileUploadService, FileValidationError, FileUploadError
from app.services.gridfs_storage_service import GridFSImageService

logger = logging.getLogger(__name__)

router = APIRouter()


class UploadResponse(BaseModel):
    """Response model for file upload."""
    file_id: str
    filename: str
    url: str
    path: str
    size: int
    mime_type: str
    uploaded_at: str


class GridFSUploadResponse(BaseModel):
    """Response model for GridFS image upload."""
    image_id: str
    file_id: str
    thumbnail_file_id: str
    filename: str
    url: str
    thumbnail_url: str
    size: int
    width: int
    height: int
    mime_type: str
    uploaded_at: str


# Initialize storage service
async def get_storage_service() -> HetznerStorageBox:
    """Get or create Hetzner Storage Box service."""
    storage = HetznerStorageBox(
        protocol=StorageProtocol.WEBDAV,
        base_path="kasaai/estateflow"
    )
    if not storage.connected:
        await storage.connect()
    return storage


async def get_upload_service() -> FileUploadService:
    """Get file upload service with Hetzner Storage."""
    storage = await get_storage_service()
    return FileUploadService(
        storage_service=storage,
        base_path="properties"
    )


# Extend allowed MIME types for videos
ALLOWED_VIDEO_TYPES = {
    "video/mp4": ".mp4",
    "video/mpeg": ".mpeg",
    "video/quicktime": ".mov",
    "video/x-msvideo": ".avi",
    "video/webm": ".webm",
}

# Maximum file sizes
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB


@router.post("/images", response_model=UploadResponse)
async def upload_property_image(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    org_context: dict = Depends(get_organization_context),
):
    """
    Upload a property image.

    Supported formats: JPEG, PNG, GIF, WebP
    Max size: 10 MB

    Args:
        file: Image file to upload
        user: Current user (from auth)
        org_context: Organization context

    Returns:
        Upload information including file URL

    Raises:
        HTTPException: If validation or upload fails
    """
    try:
        user_id = user.get("id", user.get("sub"))
        organization_id = org_context.get("organization_id")

        # Validate file size
        file_content = await file.read()
        if len(file_content) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Image size ({len(file_content) / 1024 / 1024:.2f} MB) exceeds maximum allowed size (10 MB)"
            )

        # Reset file pointer
        await file.seek(0)

        # Get upload service
        upload_service = await get_upload_service()

        # Upload file
        upload_info = await upload_service.upload_file(
            file=file.file,
            filename=file.filename,
            organization_id=organization_id,
            file_category="property-images",
            metadata={
                "uploaded_by": user_id,
                "content_type": file.content_type,
            }
        )

        logger.info(f"Image uploaded successfully: {file.filename} by user {user_id}")

        return UploadResponse(**upload_info)

    except FileValidationError as e:
        logger.warning(f"Image validation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except FileUploadError as e:
        logger.error(f"Image upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during image upload: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.post("/videos", response_model=UploadResponse)
async def upload_property_video(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    org_context: dict = Depends(get_organization_context),
):
    """
    Upload a property video.

    Supported formats: MP4, MOV, AVI, WebM
    Max size: 100 MB

    Args:
        file: Video file to upload
        user: Current user (from auth)
        org_context: Organization context

    Returns:
        Upload information including file URL

    Raises:
        HTTPException: If validation or upload fails
    """
    try:
        user_id = user.get("id", user.get("sub"))
        organization_id = org_context.get("organization_id")

        # Validate file type
        if file.content_type not in ALLOWED_VIDEO_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported video format. Allowed: {', '.join(ALLOWED_VIDEO_TYPES.values())}"
            )

        # Validate file size
        file_content = await file.read()
        if len(file_content) > MAX_VIDEO_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Video size ({len(file_content) / 1024 / 1024:.2f} MB) exceeds maximum allowed size (100 MB)"
            )

        # Reset file pointer
        await file.seek(0)

        # Get storage service directly (FileUploadService doesn't support video types by default)
        storage = await get_storage_service()

        # Generate file path
        from datetime import datetime
        import hashlib

        content_hash = hashlib.sha256(file_content).hexdigest()[:16]
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        file_id = f"{timestamp}_{content_hash}"
        extension = file.filename.split(".")[-1] if "." in file.filename else "mp4"

        now = datetime.utcnow()
        year = now.strftime("%Y")
        month = now.strftime("%m")

        remote_path = f"properties/{organization_id}/property-videos/{year}/{month}/{file_id}.{extension}"

        # Save to temp file and upload
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as temp_file:
            temp_path = temp_file.name
            temp_file.write(file_content)

        try:
            # Upload to Hetzner Storage
            await storage.upload_file(
                local_path=temp_path,
                remote_path=remote_path,
                overwrite=True
            )

            upload_info = {
                "file_id": file_id,
                "filename": file.filename,
                "url": remote_path,
                "path": remote_path,
                "size": len(file_content),
                "mime_type": file.content_type,
                "uploaded_at": datetime.utcnow().isoformat() + "Z",
            }

            logger.info(f"Video uploaded successfully: {file.filename} by user {user_id}")

            return UploadResponse(**upload_info)

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during video upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/batch", response_model=List[UploadResponse])
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    user: dict = Depends(get_current_user),
    org_context: dict = Depends(get_organization_context),
):
    """
    Upload multiple images at once.

    Args:
        files: List of files to upload
        user: Current user (from auth)
        org_context: Organization context

    Returns:
        List of upload information for each file

    Raises:
        HTTPException: If any upload fails
    """
    user_id = user.get("id", user.get("sub"))
    organization_id = org_context.get("organization_id")

    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 files allowed per batch upload")

    upload_results = []
    upload_service = await get_upload_service()

    for file in files:
        try:
            # Validate file size
            file_content = await file.read()
            if len(file_content) > MAX_IMAGE_SIZE:
                logger.warning(f"File {file.filename} exceeds size limit, skipping")
                continue

            # Reset file pointer
            await file.seek(0)

            # Upload file - pass bytes directly since we already read the file
            upload_info = await upload_service.upload_file(
                file=file_content,
                filename=file.filename,
                organization_id=organization_id,
                file_category="property-images",
                metadata={
                    "uploaded_by": user_id,
                    "content_type": file.content_type,
                }
            )

            upload_results.append(UploadResponse(**upload_info))

        except Exception as e:
            logger.error(f"Failed to upload {file.filename}: {str(e)}")
            # Continue with other files
            continue

    if not upload_results:
        raise HTTPException(status_code=400, detail="No files were successfully uploaded")

    logger.info(f"Batch upload completed: {len(upload_results)}/{len(files)} files uploaded")

    return upload_results


# ===============================================================================
# GridFS Upload Endpoints (New MongoDB-based storage)
# ===============================================================================


@router.post("/images/gridfs", response_model=GridFSUploadResponse)
async def upload_property_image_gridfs(
    file: UploadFile = File(...),
    property_id: Optional[str] = None,
    is_featured: bool = False,
    user: dict = Depends(get_current_user),
    org_context: dict = Depends(get_organization_context),
):
    """
    Upload property image to MongoDB GridFS with thumbnail generation.

    This endpoint stores images directly in MongoDB using GridFS, eliminating
    the need for external storage services. Automatically generates 300x300
    thumbnails for better performance in property listings.

    Supported formats: JPEG, PNG, WebP, HEIC
    Max size: 10 MB

    Args:
        file: Image file to upload
        property_id: Optional property ID to associate image with
        is_featured: Whether this is the featured/cover image
        user: Current user (from auth)
        org_context: Organization context

    Returns:
        Upload information with thumbnail URLs and image metadata

    Raises:
        HTTPException: If validation or upload fails
    """
    try:
        user_id = user.get("id", user.get("sub"))
        organization_id = org_context.get("organization_id")

        # Validate file size
        file_content = await file.read()
        if len(file_content) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Image size ({len(file_content) / 1024 / 1024:.2f} MB) exceeds maximum allowed size (10 MB)"
            )

        # Initialize GridFS service
        service = GridFSImageService()

        # Upload to GridFS with thumbnail generation
        property_image = await service.upload_image(
            image_data=file_content,
            filename=file.filename,
            property_id=property_id or "temp",  # Use "temp" for unassociated images
            organization_id=organization_id,
            user_id=user_id,
            mime_type=file.content_type,
            is_featured=is_featured
        )

        logger.info(
            f"Image uploaded to GridFS: {file.filename} by user {user_id} "
            f"(image_id={property_image.id}, file_id={property_image.file_id})"
        )

        return GridFSUploadResponse(
            image_id=property_image.id,
            file_id=property_image.file_id,
            thumbnail_file_id=property_image.thumbnail_file_id,
            filename=property_image.filename,
            url=f"/api/v1/storage/gridfs/{property_image.file_id}",
            thumbnail_url=f"/api/v1/storage/gridfs/{property_image.thumbnail_file_id}",
            size=property_image.size,
            width=property_image.dimensions.width,
            height=property_image.dimensions.height,
            mime_type=property_image.mime_type,
            uploaded_at=property_image.uploaded_at.isoformat() + "Z"
        )

    except ValueError as e:
        logger.warning(f"Image validation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during GridFS image upload: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during upload")


@router.post("/images/batch/gridfs", response_model=List[GridFSUploadResponse])
async def upload_multiple_images_gridfs(
    files: List[UploadFile] = File(...),
    property_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
    org_context: dict = Depends(get_organization_context),
):
    """
    Upload multiple images to GridFS at once.

    Batch upload endpoint for efficient multi-image uploads. Each image is
    processed independently, so partial success is possible if some images fail.

    Max files per batch: 20
    Supported formats: JPEG, PNG, WebP, HEIC
    Max size per image: 10 MB

    Args:
        files: List of image files to upload
        property_id: Optional property ID to associate images with
        user: Current user (from auth)
        org_context: Organization context

    Returns:
        List of upload information for successfully uploaded images

    Raises:
        HTTPException: If no files uploaded successfully or validation fails
    """
    user_id = user.get("id", user.get("sub"))
    organization_id = org_context.get("organization_id")

    if len(files) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 files allowed per batch upload"
        )

    upload_results = []
    service = GridFSImageService()

    for file in files:
        try:
            # Validate file size
            file_content = await file.read()
            if len(file_content) > MAX_IMAGE_SIZE:
                logger.warning(
                    f"File {file.filename} exceeds size limit "
                    f"({len(file_content) / 1024 / 1024:.2f} MB > 10 MB), skipping"
                )
                continue

            # Upload to GridFS
            property_image = await service.upload_image(
                image_data=file_content,
                filename=file.filename,
                property_id=property_id or "temp",
                organization_id=organization_id,
                user_id=user_id,
                mime_type=file.content_type,
                is_featured=False  # Don't auto-set featured in batch uploads
            )

            upload_results.append(GridFSUploadResponse(
                image_id=property_image.id,
                file_id=property_image.file_id,
                thumbnail_file_id=property_image.thumbnail_file_id,
                filename=property_image.filename,
                url=f"/api/v1/storage/gridfs/{property_image.file_id}",
                thumbnail_url=f"/api/v1/storage/gridfs/{property_image.thumbnail_file_id}",
                size=property_image.size,
                width=property_image.dimensions.width,
                height=property_image.dimensions.height,
                mime_type=property_image.mime_type,
                uploaded_at=property_image.uploaded_at.isoformat() + "Z"
            ))

        except Exception as e:
            logger.error(f"Failed to upload {file.filename}: {str(e)}")
            # Continue with other files
            continue

    if not upload_results:
        raise HTTPException(
            status_code=400,
            detail="No files were successfully uploaded. Check file formats and sizes."
        )

    logger.info(
        f"GridFS batch upload completed: {len(upload_results)}/{len(files)} files uploaded by user {user_id}"
    )

    return upload_results
