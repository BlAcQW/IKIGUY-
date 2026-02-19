"""
Folder operations API routes.

Author: AI Labs Africa
Date: 2025-11-10
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List

from apps.shared.unified_logging import get_logger
from apps.shared.services.drive_service import DriveService, FileNotFoundError, PermissionDeniedError
from apps.drive.backend.app.api.dependencies import get_current_user, get_drive_service_instance
from apps.drive.backend.app.api.models.requests import CreateFolderRequest, RenameItemRequest, MoveItemRequest
from apps.drive.backend.app.api.models.responses import (
    DriveItemResponse,
    FolderContentsResponse,
    BreadcrumbItem,
    StatusResponse
)

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=DriveItemResponse)
async def create_folder(
    request: CreateFolderRequest,
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Create a new folder.

    Args:
        request: Create folder request
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        Created folder metadata
    """
    try:
        result = await drive_service.create_folder(
            name=request.name,
            parent_id=request.parent_id,
            owner_id=current_user["user_id"],
            organization_id=request.organization_id
        )
        logger.info(f"Folder created: {request.name} by user {current_user['user_id']}")
        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{folder_id}/contents", response_model=FolderContentsResponse)
async def get_folder_contents(
    folder_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str = Query("name", regex="^(name|modified_at|size|type)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Get contents of a folder.

    Args:
        folder_id: Folder ID (None for root)
        skip: Number of items to skip (pagination)
        limit: Maximum items to return
        sort_by: Field to sort by (name, modified_at, size, type)
        sort_order: Sort order (asc, desc)
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        Folder contents with pagination
    """
    try:
        # Handle root folder (folder_id == "root")
        actual_folder_id = None if folder_id == "root" else folder_id

        result = await drive_service.get_folder_contents(
            folder_id=actual_folder_id,
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"],
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return result

    except Exception as e:
        logger.error(f"Error getting folder contents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{folder_id}/breadcrumbs", response_model=List[BreadcrumbItem])
async def get_breadcrumbs(
    folder_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Get breadcrumb trail for a folder.

    Args:
        folder_id: Folder ID (None for root)
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        List of breadcrumb items
    """
    try:
        # Handle root folder
        actual_folder_id = None if folder_id == "root" else folder_id

        result = await drive_service.get_breadcrumbs(
            folder_id=actual_folder_id,
            organization_id=current_user["organization_id"]
        )
        return result

    except Exception as e:
        logger.error(f"Error getting breadcrumbs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{folder_id}/rename", response_model=DriveItemResponse)
async def rename_folder(
    folder_id: str,
    request: RenameItemRequest,
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Rename a folder.

    Args:
        folder_id: Folder ID
        request: Rename request
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        Updated folder metadata
    """
    try:
        result = await drive_service.rename_file(
            file_id=folder_id,
            new_name=request.new_name,
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"]
        )
        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error renaming folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{folder_id}/move", response_model=DriveItemResponse)
async def move_folder(
    folder_id: str,
    request: MoveItemRequest,
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Move a folder to a different parent folder.

    Args:
        folder_id: Folder ID
        request: Move request
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        Updated folder metadata
    """
    try:
        result = await drive_service.move_file(
            file_id=folder_id,
            new_parent_id=request.new_parent_id,
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"]
        )
        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error moving folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{folder_id}", response_model=StatusResponse)
async def delete_folder(
    folder_id: str,
    permanent: bool = False,
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Delete a folder (move to trash or permanent delete).

    Args:
        folder_id: Folder ID
        permanent: Whether to permanently delete (default: False)
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        Status response
    """
    try:
        result = await drive_service.delete_file(
            file_id=folder_id,
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"],
            permanent=permanent
        )
        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))
