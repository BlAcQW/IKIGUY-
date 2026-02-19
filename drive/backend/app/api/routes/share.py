"""
Sharing and permissions API routes.

Author: AI Labs Africa
Date: 2025-11-10
"""

from fastapi import APIRouter, Depends, HTTPException

import logging
from apps.shared.services.drive_service import DriveService, FileNotFoundError, PermissionDeniedError
from apps.drive.backend.app.api.dependencies import get_current_user, get_drive_service_instance
from apps.drive.backend.app.api.models.requests import ShareItemRequest, CreateShareLinkRequest
from apps.drive.backend.app.api.models.responses import (
    DriveItemResponse,
    ShareLinkCreatedResponse,
    StatusResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{item_id}/user", response_model=DriveItemResponse)
async def share_with_user(
    item_id: str,
    request: ShareItemRequest,
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Share an item with a user.

    Args:
        item_id: Item ID to share
        request: Share request with target user and role
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        Updated item metadata with new permissions
    """
    try:
        result = await drive_service.share_item(
            item_id=item_id,
            user_id=current_user["user_id"],
            target_user_id=request.target_user_id,
            role=request.role,
            organization_id=current_user["organization_id"]
        )
        logger.info(
            f"Item {item_id} shared with user {request.target_user_id} "
            f"by {current_user['user_id']} (role: {request.role})"
        )
        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error sharing item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{item_id}/link", response_model=ShareLinkCreatedResponse)
async def create_share_link(
    item_id: str,
    request: CreateShareLinkRequest,
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Create a public share link for an item.

    Args:
        item_id: Item ID
        request: Share link creation request
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        Share link details
    """
    try:
        result = await drive_service.create_share_link(
            item_id=item_id,
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"],
            expires_in_days=request.expires_in_days,
            is_public=request.is_public
        )
        logger.info(f"Share link created for item {item_id} by {current_user['user_id']}")
        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating share link: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{item_id}/link", response_model=StatusResponse)
async def revoke_share_link(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Revoke a share link.

    Args:
        item_id: Item ID
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        Status response
    """
    try:
        result = await drive_service.revoke_share_link(
            item_id=item_id,
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"]
        )
        logger.info(f"Share link revoked for item {item_id} by {current_user['user_id']}")
        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error revoking share link: {e}")
        raise HTTPException(status_code=500, detail=str(e))
