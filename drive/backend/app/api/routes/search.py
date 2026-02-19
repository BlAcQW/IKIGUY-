"""
Search and filter API routes.

Author: AI Labs Africa
Date: 2025-11-10
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime

import logging
from apps.shared.services.drive_service import DriveService
from apps.drive.backend.app.api.dependencies import get_current_user, get_drive_service_instance
from apps.drive.backend.app.api.models.responses import SearchResultsResponse, DriveItemResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=SearchResultsResponse)
async def search_files(
    q: str = Query(..., min_length=1, description="Search query"),
    file_type: Optional[str] = Query(None, regex="^(folder|document|image|video|audio)$"),
    owner_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Search files and folders.

    Args:
        q: Search query string
        file_type: Filter by type (folder, document, image, video, audio)
        owner_id: Filter by owner
        date_from: Filter by modified date (from)
        date_to: Filter by modified date (to)
        skip: Pagination offset
        limit: Pagination limit
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        Search results with pagination
    """
    try:
        result = await drive_service.search_files(
            query=q,
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"],
            file_type=file_type,
            owner_id=owner_id,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit
        )
        return result

    except Exception as e:
        logger.error(f"Error searching files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent", response_model=List[DriveItemResponse])
async def get_recent_files(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Get recently modified files.

    Args:
        limit: Maximum number of files to return
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        List of recent files
    """
    try:
        result = await drive_service.get_recent_files(
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"],
            limit=limit
        )
        return result

    except Exception as e:
        logger.error(f"Error getting recent files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/starred", response_model=List[DriveItemResponse])
async def get_starred_items(
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Get starred items for current user.

    Args:
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        List of starred items
    """
    try:
        result = await drive_service.get_starred_items(
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"]
        )
        return result

    except Exception as e:
        logger.error(f"Error getting starred items: {e}")
        raise HTTPException(status_code=500, detail=str(e))
