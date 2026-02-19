"""
Author/Pastor routes for managing devotionals and dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional
from app.models.user import TokenData
from app.services.author_service import AuthorService
from app.utils.auth import get_current_admin

router = APIRouter(prefix="/author", tags=["author"])


@router.get("/dashboard/statistics", response_model=Dict[str, Any])
async def get_author_statistics(
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get personal statistics for author dashboard.

    Requires admin role.

    Returns:
        Author statistics including readers, devotionals, engagement metrics
    """
    service = AuthorService()
    try:
        statistics = await service.get_author_statistics(current_user.user_id)
        return {
            "success": True,
            "data": statistics,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch author statistics: {str(e)}",
        )


@router.get("/dashboard/recent-devotionals", response_model=Dict[str, Any])
async def get_recent_devotionals(
    limit: int = Query(5, ge=1, le=20),
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get recent devotionals for author dashboard.

    Requires admin role.

    Args:
        limit: Maximum number of devotionals to return (default: 5, max: 20)

    Returns:
        List of recent devotionals with engagement metrics
    """
    service = AuthorService()
    try:
        devotionals = await service.get_recent_devotionals(
            current_user.user_id, limit=limit
        )
        return {
            "success": True,
            "data": devotionals,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recent devotionals: {str(e)}",
        )


@router.get("/devotionals", response_model=Dict[str, Any])
async def get_devotionals_list(
    status: Optional[str] = Query(None, regex="^(published|scheduled|draft)$"),
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get paginated list of devotionals for author.

    Requires admin role.

    Args:
        status: Filter by status (published, scheduled, draft)
        search: Search by title
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)

    Returns:
        Paginated list of devotionals with engagement metrics
    """
    service = AuthorService()
    try:
        result = await service.get_devotionals_list(
            author_id=current_user.user_id,
            status=status,
            search=search,
            page=page,
            page_size=page_size,
        )
        return {
            "success": True,
            "data": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch devotionals: {str(e)}",
        )


@router.get("/analytics", response_model=Dict[str, Any])
async def get_engagement_analytics(
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get detailed engagement analytics for author.

    Requires admin role.

    Args:
        period: Time period (7d, 30d, 90d, 1y) (default: 30d)

    Returns:
        Detailed engagement analytics including daily breakdown and top devotionals
    """
    service = AuthorService()
    try:
        analytics = await service.get_engagement_analytics(
            current_user.user_id, period=period
        )
        return {
            "success": True,
            "data": analytics,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {str(e)}",
        )
