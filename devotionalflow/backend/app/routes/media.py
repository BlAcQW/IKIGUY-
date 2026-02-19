"""
Media upload API routes.
Handles image uploads for devotional cover images and user avatars.
Also provides Pexels stock photo search for devotional covers.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from fastapi.responses import Response
from typing import Optional
import logging
import sys
import os

# Add parent paths for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from apps.shared.storage.hetzner_storage_box import get_storage, StorageProtocol
from apps.shared.services.file_upload_service import FileUploadService, FileValidationError, FileUploadError
from app.utils.auth import get_current_user
from app.models.user import TokenData
from app.services import pexels_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Initialize file upload service (will be done once at startup)
_upload_service: Optional[FileUploadService] = None


async def get_upload_service() -> FileUploadService:
    """Get or create file upload service instance."""
    global _upload_service

    if _upload_service is None:
        # Get Hetzner storage instance
        storage = await get_storage(
            protocol=StorageProtocol.WEBDAV,
            base_path="kasaai/devotionalflow"
        )
        _upload_service = FileUploadService(
            storage_service=storage,
            base_path="media"
        )

    return _upload_service


@router.post("/upload-image", status_code=status.HTTP_200_OK)
async def upload_image(
    file: UploadFile = File(...),
    category: str = Form("devotional-covers"),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Upload an image file.

    **Supported formats:** JPG, PNG, GIF, WebP, HEIC
    **Max size:** 10 MB

    **Headers:**
    - Authorization: Bearer {access_token}

    **Form Data:**
    - file: Image file to upload
    - category: Image category (devotional-covers, avatars, etc.)

    **Returns:**
    - file_id: Unique file identifier
    - filename: Original filename
    - url: File path/URL for storage reference
    - size: File size in bytes
    - mime_type: Detected MIME type

    **Raises:**
    - 400: Invalid file (wrong type, too large, corrupt)
    - 401: Unauthorized (not logged in)
    - 500: Upload failed
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Only images are allowed. Got: {file.content_type}"
            )

        # Read file content
        file_content = await file.read()

        # Get upload service
        upload_service = await get_upload_service()

        # Upload file
        upload_info = await upload_service.upload_file(
            file=file_content,
            filename=file.filename or "image.jpg",
            organization_id="freshmanna",  # Fixed organization for devotionalflow
            file_category=category,
            metadata={
                "uploaded_by": current_user.user_id,
                "original_filename": file.filename
            }
        )

        logger.info(
            f"Image uploaded successfully: {file.filename} by user {current_user.user_id}"
        )

        return {
            "file_id": upload_info["file_id"],
            "filename": upload_info["filename"],
            "url": upload_info["url"],  # This is the path in storage
            "size": upload_info["size"],
            "mime_type": upload_info["mime_type"],
            "uploaded_at": upload_info["uploaded_at"]
        }

    except FileValidationError as e:
        logger.warning(f"File validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileUploadError as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during upload"
        )


@router.get("/image/{file_path:path}", response_class=Response)
async def get_image(
    file_path: str,
):
    """
    Retrieve an uploaded image.

    **Path Parameters:**
    - file_path: Full path to the image file

    **Returns:**
    - Image binary data with appropriate Content-Type header

    **Raises:**
    - 404: Image not found
    - 500: Failed to retrieve image
    """
    try:
        # Get upload service
        upload_service = await get_upload_service()

        # Get storage instance
        storage = upload_service.storage_service

        if not storage or not storage.connected:
            storage = await get_storage(
                protocol=StorageProtocol.WEBDAV,
                base_path="kasaai/devotionalflow"
            )

        # Download file content
        file_content = await storage.download_file_content(file_path)

        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        # Detect MIME type from file extension
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "image/jpeg"  # Default to JPEG

        return Response(
            content=file_content,
            media_type=mime_type,
            headers={
                "Cache-Control": "public, max-age=31536000",  # Cache for 1 year
                "Access-Control-Allow-Origin": "*"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve image: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve image"
        )


@router.delete("/image/{file_path:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    file_path: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Delete an uploaded image.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Path Parameters:**
    - file_path: Full path to the image file

    **Returns:**
    - 204 No Content on success

    **Raises:**
    - 401: Unauthorized
    - 404: Image not found
    - 500: Failed to delete image
    """
    try:
        # Get upload service
        upload_service = await get_upload_service()

        # Delete file
        success = await upload_service.delete_file(file_path)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        logger.info(f"Image deleted: {file_path} by user {current_user.user_id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete image: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete image"
        )


# ============================================================================
# PEXELS STOCK PHOTO ROUTES
# ============================================================================

@router.get("/pexels/search")
async def search_pexels_photos(
    query: str = Query(..., description="Search query (e.g., 'faith', 'prayer', 'nature')"),
    per_page: int = Query(20, ge=1, le=80, description="Results per page"),
    page: int = Query(1, ge=1, description="Page number"),
    orientation: Optional[str] = Query(None, description="Image orientation: landscape, portrait, or square"),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Search Pexels for stock photos to use as devotional covers.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Query Parameters:**
    - query: Search keywords (e.g., "faith", "prayer", "worship")
    - per_page: Number of results (1-80, default: 20)
    - page: Page number for pagination (default: 1)
    - orientation: Filter by orientation (landscape, portrait, square)

    **Returns:**
    - page: Current page number
    - per_page: Results per page
    - total_results: Total number of matching photos
    - next_page: URL for next page (if available)
    - photos: Array of photo objects with:
      - id: Pexels photo ID
      - width, height: Image dimensions
      - url: Pexels page URL
      - photographer: Photographer name
      - photographer_url: Photographer profile URL
      - alt: Alt text description
      - avg_color: Average color (hex)
      - src: Object with image URLs in different sizes:
        - original: Original size
        - large2x: Large (2x)
        - large: Large
        - medium: Medium
        - small: Small
        - portrait: Portrait crop
        - landscape: Landscape crop
        - tiny: Tiny thumbnail

    **Raises:**
    - 401: Unauthorized (not logged in)
    - 400: Invalid parameters
    - 500: Pexels API error

    **Attribution Required:**
    When using Pexels images, you must provide attribution to the photographer.
    """
    try:
        result = await pexels_service.search_photos(
            query=query,
            per_page=per_page,
            page=page,
            orientation=orientation
        )
        return result

    except ValueError as e:
        logger.error(f"Pexels search validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Pexels search failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search stock photos"
        )


@router.get("/pexels/curated")
async def get_curated_pexels_photos(
    per_page: int = Query(20, ge=1, le=80, description="Results per page"),
    page: int = Query(1, ge=1, description="Page number"),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get curated high-quality photos from Pexels.
    These are hand-picked photos perfect for devotional covers.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Query Parameters:**
    - per_page: Number of results (1-80, default: 20)
    - page: Page number for pagination (default: 1)

    **Returns:**
    Same format as /pexels/search

    **Raises:**
    - 401: Unauthorized (not logged in)
    - 500: Pexels API error
    """
    try:
        result = await pexels_service.get_curated_photos(
            per_page=per_page,
            page=page
        )
        return result

    except ValueError as e:
        logger.error(f"Pexels curated validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Pexels curated failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get curated photos"
        )


@router.get("/pexels/photo/{photo_id}")
async def get_pexels_photo_by_id(
    photo_id: int,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get a specific photo by ID from Pexels.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Path Parameters:**
    - photo_id: Pexels photo ID

    **Returns:**
    Photo object with same structure as search results

    **Raises:**
    - 401: Unauthorized (not logged in)
    - 404: Photo not found
    - 500: Pexels API error
    """
    try:
        photo = await pexels_service.get_photo_by_id(photo_id)

        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found"
            )

        return photo.to_dict()

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Pexels photo validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Pexels photo retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get photo"
        )
