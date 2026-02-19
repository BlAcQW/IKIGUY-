"""
Admin routes for managing users and platform.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.models.user import (
    UserListResponse,
    UserListFilters,
    UserRoleUpdate,
    UserStatusUpdate,
    TokenData,
)
from app.services.admin_service import AdminService
from app.utils.auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


# ============ Dashboard Routes ============

@router.get("/dashboard/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get admin dashboard statistics.

    This endpoint provides comprehensive statistics for the admin dashboard
    including user counts, devotional counts, and engagement metrics.

    Requires admin role.

    Returns:
        Dashboard statistics object
    """
    service = AdminService()
    try:
        statistics = await service.get_platform_statistics()
        return statistics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard stats: {str(e)}",
        )


@router.get("/dashboard/recent-activity", response_model=Dict[str, Any])
async def get_dashboard_recent_activity(
    limit: int = 10,
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get recent activity for admin dashboard.

    Returns a list of recent platform activities including new users,
    new devotionals, and engagement actions.

    Requires admin role.

    Args:
        limit: Maximum number of activities to return (default: 10)

    Returns:
        List of recent activities
    """
    service = AdminService()
    try:
        activities = await service.get_recent_activity(limit=limit)
        return {"activities": activities}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recent activity: {str(e)}",
        )


# ============ Legacy Routes (Deprecated) ============

@router.get("/statistics", response_model=Dict[str, Any])
async def get_platform_statistics(
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get platform-wide statistics for admin dashboard.

    Requires admin role.

    Returns:
        Platform statistics including user counts, devotional counts, engagement metrics
    """
    service = AdminService()
    try:
        statistics = await service.get_platform_statistics()
        return {
            "success": True,
            "data": statistics,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch statistics: {str(e)}",
        )


@router.get("/activity", response_model=Dict[str, Any])
async def get_recent_activity(
    limit: int = 10,
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get recent platform activity for admin dashboard.

    Requires admin role.

    Args:
        limit: Maximum number of activities to return (default: 10)

    Returns:
        List of recent activities
    """
    service = AdminService()
    try:
        activities = await service.get_recent_activity(limit=limit)
        return {
            "success": True,
            "data": activities,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch activity: {str(e)}",
        )


@router.get("/users", response_model=UserListResponse)
async def get_users_list(
    role: str = None,
    is_suspended: bool = None,
    search: str = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get paginated list of users with filters.

    Requires admin role.

    Args:
        role: Filter by role (user, admin)
        is_suspended: Filter by suspension status
        search: Search by name or email
        page: Page number (default: 1)
        page_size: Items per page (default: 20)
        sort_by: Field to sort by (default: created_at)
        sort_order: Sort order asc/desc (default: desc)

    Returns:
        Paginated list of users with statistics
    """
    service = AdminService()

    # Validate filters
    filters = UserListFilters(
        role=role,
        is_suspended=is_suspended,
        search=search,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    try:
        return await service.get_users_list(filters)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}",
        )


@router.patch("/users/{user_id}/role", response_model=Dict[str, Any])
async def update_user_role(
    user_id: str,
    role_update: UserRoleUpdate,
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Update user role.

    Requires admin role.

    Args:
        user_id: ID of the user to update
        role_update: New role data

    Returns:
        Update result
    """
    service = AdminService()

    try:
        result = await service.update_user_role(user_id, role_update)
        return {
            "success": True,
            "message": result["message"],
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user role: {str(e)}",
        )


@router.patch("/users/{user_id}/status", response_model=Dict[str, Any])
async def update_user_status(
    user_id: str,
    status_update: UserStatusUpdate,
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Update user status (suspend/activate).

    Requires admin role.

    Args:
        user_id: ID of the user to update
        status_update: New status data

    Returns:
        Update result
    """
    service = AdminService()

    try:
        result = await service.update_user_status(user_id, status_update)
        return {
            "success": True,
            "message": result["message"],
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user status: {str(e)}",
        )


@router.delete("/users/{user_id}", response_model=Dict[str, Any])
async def delete_user(
    user_id: str,
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Delete user and all associated data.

    Requires admin role.

    WARNING: This action cannot be undone.

    Args:
        user_id: ID of the user to delete

    Returns:
        Deletion result
    """
    service = AdminService()

    try:
        result = await service.delete_user(user_id)
        return {
            "success": True,
            "message": result["message"],
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}",
        )
