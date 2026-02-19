"""
Content moderation routes for flagging and reviewing content.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional
from app.models.moderation import (
    FlagContent,
    ModerationAction,
    ModerationQueueResponse,
    ModerationQueueFilters,
    ModerationStats,
)
from app.models.user import TokenData
from app.services.moderation_service import ModerationService
from app.utils.auth import get_current_user, get_current_admin

router = APIRouter(prefix="/moderation", tags=["moderation"])


@router.post("/flag", response_model=Dict[str, Any])
async def flag_content(
    flag_data: FlagContent,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Flag content for moderation.

    Any authenticated user can flag content.

    Args:
        flag_data: Content flag data

    Returns:
        Flag ID and success message
    """
    service = ModerationService()
    try:
        result = await service.flag_content(flag_data, current_user.user_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to flag content: {str(e)}",
        )


@router.get("/queue", response_model=Dict[str, Any])
async def get_moderation_queue(
    status_filter: Optional[str] = Query(None, alias="status"),
    content_type: Optional[str] = None,
    reason_category: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get moderation queue with filters.

    Requires admin role.

    Args:
        status_filter: Filter by status (pending, reviewed, dismissed, action_taken)
        content_type: Filter by content type (devotional, comment)
        reason_category: Filter by reason category
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)
        sort_by: Field to sort by (default: created_at)
        sort_order: Sort order asc/desc (default: desc)

    Returns:
        Paginated list of flagged content
    """
    service = ModerationService()

    # Create filters
    filters = ModerationQueueFilters(
        status=status_filter,
        content_type=content_type,
        reason_category=reason_category,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    try:
        return await service.get_moderation_queue(filters)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch moderation queue: {str(e)}",
        )


@router.get("/stats", response_model=ModerationStats)
async def get_moderation_stats(
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get moderation statistics.

    Requires admin role.

    Returns:
        Statistics about flagged content
    """
    service = ModerationService()
    try:
        return await service.get_moderation_stats()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch moderation stats: {str(e)}",
        )


@router.get("/flags/{flag_id}", response_model=Dict[str, Any])
async def get_flag_details(
    flag_id: str,
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get detailed information about a specific flag.

    Requires admin role.

    Args:
        flag_id: ID of the flag

    Returns:
        Flag details including full content and moderation history
    """
    service = ModerationService()
    try:
        return await service.get_flag_details(flag_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch flag details: {str(e)}",
        )


@router.post("/flags/{flag_id}/moderate", response_model=Dict[str, Any])
async def moderate_content(
    flag_id: str,
    action: ModerationAction,
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Take moderation action on flagged content.

    Requires admin role.

    Args:
        flag_id: ID of the flag
        action: Moderation action to take

    Returns:
        Success message
    """
    service = ModerationService()
    try:
        result = await service.moderate_content(flag_id, action, current_user.user_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to moderate content: {str(e)}",
        )
