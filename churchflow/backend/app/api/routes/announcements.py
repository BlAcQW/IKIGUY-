"""
Announcement Management API Routes.

Handles announcements for landing page display.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
from fastapi.responses import FileResponse, Response
from typing import List, Optional
from datetime import datetime
import os
import logging

from app.api.dependencies import get_current_user_profile, require_roles
from app.models.user import User
from app.services.announcement_service import AnnouncementService
from app.schemas.announcement import (
    CreateAnnouncementRequest,
    UpdateAnnouncementRequest,
    AnnouncementResponse,
    AnnouncementListResponse
)
from app.core.database import get_database
from bson import ObjectId

router = APIRouter()
logger = logging.getLogger(__name__)

# Storage configuration
STORAGE_BASE_PATH = "storage/announcements"
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp"
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


async def get_organization_id(current_user: User) -> str:
    """
    Get organization ID for current user.

    Args:
        current_user: Current authenticated user

    Returns:
        str: Organization ID
    """
    if current_user.organization_id:
        return str(current_user.organization_id)

    # Fetch default organization from database
    db = get_database()
    org = await db.organizations.find_one({"is_active": True})
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active organization found"
        )
    return str(org["_id"])


def announcement_to_response(announcement) -> AnnouncementResponse:
    """
    Convert announcement document to response model.

    Args:
        announcement: Announcement document from database

    Returns:
        AnnouncementResponse object
    """
    return AnnouncementResponse(
        id=str(announcement["_id"]),
        organization_id=str(announcement["organization_id"]),
        title=announcement["title"],
        description=announcement.get("description"),
        image_url=announcement.get("image_url"),
        cta_text=announcement.get("cta_text"),
        cta_link=announcement.get("cta_link"),
        event_id=str(announcement["event_id"]) if announcement.get("event_id") else None,
        is_active=announcement.get("is_active", True),
        is_hero=announcement.get("is_hero", False),
        display_order=announcement.get("display_order", 0),
        start_date=announcement.get("start_date"),
        end_date=announcement.get("end_date"),
        created_by_user_id=str(announcement["created_by_user_id"]),
        created_at=announcement["created_at"],
        updated_at=announcement["updated_at"]
    )


# API Endpoints

@router.post("/", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    request: CreateAnnouncementRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Create a new announcement.

    Requires admin role.

    Args:
        request: Announcement creation data
        current_user: Current authenticated admin user

    Returns:
        Created Announcement object

    Raises:
        HTTPException: If creation fails
    """
    try:
        db = get_database()
        service = AnnouncementService(db)

        organization_id = await get_organization_id(current_user)

        # Convert request to dict
        announcement_data = request.model_dump(exclude_none=True)

        announcement = await service.create_announcement(
            announcement_data=announcement_data,
            organization_id=organization_id,
            created_by_user_id=str(current_user.id)
        )

        # Convert to response
        announcement_dict = announcement.model_dump(by_alias=True)
        return announcement_to_response(announcement_dict)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create announcement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create announcement: {str(e)}"
        )


@router.post("/upload-image", status_code=status.HTTP_200_OK)
async def upload_announcement_image(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles("admin"))
):
    """
    Upload an image for an announcement.

    Args:
        file: Image file to upload
        current_user: Current authenticated admin user

    Returns:
        Dictionary with image_url
    """
    try:
        # Validate file type
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not allowed. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Validate file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size {file_size} exceeds maximum {MAX_FILE_SIZE}"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )

        # Create storage directory if it doesn't exist
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        storage_path = os.path.join(base_dir, STORAGE_BASE_PATH)
        os.makedirs(storage_path, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = file.filename.replace(" ", "-").replace("/", "-")
        unique_filename = f"{timestamp}_{safe_filename}"
        file_path = os.path.join(storage_path, unique_filename)

        # Save file
        try:
            with open(file_path, "wb") as f:
                f.write(content)
            logger.info(f"Saved announcement image to: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )

        # Return URL pointing to the API endpoint that serves the image
        image_url = f"/api/v1/announcements/image/{unique_filename}"

        return {"image_url": image_url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )


@router.get("/image/{filename}")
async def get_announcement_image(filename: str):
    """
    Serve announcement image files.
    
    Public endpoint - no authentication required for images.
    
    Args:
        filename: Name of the image file
        
    Returns:
        Image file response with CORS headers
    """
    try:
        # Get storage path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        storage_path = os.path.join(base_dir, STORAGE_BASE_PATH)
        file_path = os.path.join(storage_path, filename)
        
        # Security: prevent path traversal
        if not os.path.abspath(file_path).startswith(os.path.abspath(storage_path)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )
        
        # Determine content type from extension
        content_type = "image/jpeg"
        if filename.lower().endswith('.png'):
            content_type = "image/png"
        elif filename.lower().endswith('.gif'):
            content_type = "image/gif"
        elif filename.lower().endswith('.webp'):
            content_type = "image/webp"
        
        # Read file content
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        # Return response with CORS headers
        return Response(
            content=file_content,
            media_type=content_type,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Cache-Control": "public, max-age=31536000",  # Cache for 1 year
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to serve image"
        )


@router.get("/", response_model=AnnouncementListResponse)
async def list_announcements(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    include_past: bool = Query(False, description="Include past announcements"),
    current_user: User = Depends(require_roles("admin"))
):
    """
    List announcements for the organization.

    Requires admin role.

    Args:
        is_active: Optional filter by active status
        include_past: Whether to include past announcements
        current_user: Current authenticated admin user

    Returns:
        List of announcements
    """
    try:
        db = get_database()
        service = AnnouncementService(db)

        organization_id = await get_organization_id(current_user)

        announcements = await service.list_announcements(
            organization_id=organization_id,
            is_active=is_active,
            include_past=include_past
        )

        announcements_dict = [a.model_dump(by_alias=True) for a in announcements]
        announcements_response = [announcement_to_response(a) for a in announcements_dict]

        return AnnouncementListResponse(
            announcements=announcements_response,
            total=len(announcements_response)
        )

    except Exception as e:
        logger.error(f"Failed to list announcements: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list announcements: {str(e)}"
        )


@router.get("/public", response_model=AnnouncementListResponse)
async def get_public_announcements(
    organization_id: Optional[str] = Query(None, description="Organization ID (optional)")
):
    """
    Get active announcements for public landing page.

    No authentication required.

    Args:
        organization_id: Optional organization ID (if not provided, uses default)

    Returns:
        List of active announcements
    """
    try:
        db = get_database()
        service = AnnouncementService(db)

        # If organization_id not provided, get default
        if not organization_id:
            org = await db.organizations.find_one({"is_active": True})
            if not org:
                return AnnouncementListResponse(announcements=[], total=0)
            organization_id = str(org["_id"])

        announcements = await service.get_public_announcements(organization_id=organization_id)

        announcements_dict = [a.model_dump(by_alias=True) for a in announcements]
        announcements_response = [announcement_to_response(a) for a in announcements_dict]

        return AnnouncementListResponse(
            announcements=announcements_response,
            total=len(announcements_response)
        )

    except Exception as e:
        logger.error(f"Failed to get public announcements: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get public announcements: {str(e)}"
        )


@router.get("/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(
    announcement_id: str,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Get announcement by ID.

    Requires admin role.

    Args:
        announcement_id: Announcement ID
        current_user: Current authenticated admin user

    Returns:
        Announcement object

    Raises:
        HTTPException: If announcement not found
    """
    try:
        db = get_database()
        service = AnnouncementService(db)

        organization_id = await get_organization_id(current_user)

        announcement = await service.get_announcement(
            announcement_id=announcement_id,
            organization_id=organization_id
        )

        if not announcement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Announcement not found"
            )

        announcement_dict = announcement.model_dump(by_alias=True)
        return announcement_to_response(announcement_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get announcement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get announcement: {str(e)}"
        )


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    announcement_id: str,
    request: UpdateAnnouncementRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Update an announcement.

    Requires admin role.

    Args:
        announcement_id: Announcement ID
        request: Update data
        current_user: Current authenticated admin user

    Returns:
        Updated Announcement object

    Raises:
        HTTPException: If update fails
    """
    try:
        db = get_database()
        service = AnnouncementService(db)

        organization_id = await get_organization_id(current_user)

        update_data = request.model_dump(exclude_none=True)

        announcement = await service.update_announcement(
            announcement_id=announcement_id,
            organization_id=organization_id,
            update_data=update_data
        )

        if not announcement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Announcement not found"
            )

        announcement_dict = announcement.model_dump(by_alias=True)
        return announcement_to_response(announcement_dict)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update announcement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update announcement: {str(e)}"
        )


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    announcement_id: str,
    hard_delete: bool = Query(False, description="Permanently delete (default: soft delete)"),
    current_user: User = Depends(require_roles("admin"))
):
    """
    Delete an announcement.

    Requires admin role.

    Args:
        announcement_id: Announcement ID
        hard_delete: Whether to permanently delete (default: soft delete)
        current_user: Current authenticated admin user

    Raises:
        HTTPException: If deletion fails
    """
    try:
        db = get_database()
        service = AnnouncementService(db)

        organization_id = await get_organization_id(current_user)

        if hard_delete:
            deleted = await service.hard_delete_announcement(
                announcement_id=announcement_id,
                organization_id=organization_id
            )
        else:
            deleted = await service.delete_announcement(
                announcement_id=announcement_id,
                organization_id=organization_id
            )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Announcement not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete announcement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete announcement: {str(e)}"
        )

