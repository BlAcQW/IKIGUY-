"""
Member Analytics API Routes

Provides admin-only endpoints for comprehensive member statistics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
import logging

from app.api.dependencies import require_admin, require_organization_access
from app.core.database import get_database
from app.models.user import User
from app.models.analytics import MemberDashboardMetrics
from app.services.member_analytics_service import get_member_analytics_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/dashboard",
    response_model=MemberDashboardMetrics,
    summary="Get Member Dashboard Statistics",
    description="Get comprehensive member statistics for admin dashboard (admin only)",
    responses={
        200: {
            "description": "Successfully retrieved member statistics",
            "content": {
                "application/json": {
                    "example": {
                        "organization_id": "org_456",
                        "period": "30d",
                        "total_members": 1250,
                        "active_members": 890,
                        "inactive_members": 360,
                        "visitors": 45,
                        "new_members_count": 28,
                        "growth_rate": 2.3,
                        "total_donations": 45000.00,
                        "total_donors": 420,
                        "average_donation": 107.14
                    }
                }
            }
        },
        403: {"description": "Access denied - Admin role required"},
        400: {"description": "Invalid parameters"}
    }
)
async def get_member_dashboard(
    period: str = Query(
        "30d",
        pattern="^(7d|30d|90d|1y)$",
        description="Time period for metrics (7d, 30d, 90d, 1y)"
    ),
    branch_id: Optional[str] = Query(
        None,
        description="Optional branch ID to filter statistics"
    ),
    organization_id: str = Depends(require_organization_access),
    current_user: User = Depends(require_admin)
):
    """
    Get comprehensive member dashboard statistics (Admin only).

    This endpoint provides detailed member analytics including:
    - Member counts by status (active, inactive, visitors, alumni)
    - Growth metrics (new members, growth rate, trends)
    - Demographics (age distribution, gender, marital status)
    - Activity metrics (visit frequency, engagement)
    - Financial metrics (donations, donors, averages)
    - Branch distribution
    - Spiritual journey stages

    **Access:** Admin or Universal Admin role required

    **Parameters:**
    - period: Time period for analysis (7d, 30d, 90d, 1y)
    - branch_id: Optional branch filter
    - X-Organization-ID: Organization ID (header)

    **Returns:**
    - MemberDashboardMetrics with all statistics
    """
    logger.info(
        f"[get_member_dashboard] user={current_user.id}, "
        f"org={organization_id}, period={period}, branch={branch_id}"
    )

    try:
        # Get database connection
        db = get_database()

        # Get service instance
        service = get_member_analytics_service(db)

        # Get member dashboard statistics
        metrics = await service.get_member_dashboard_stats(
            organization_id=organization_id,
            period=period,
            branch_id=branch_id
        )

        logger.info(
            f"[get_member_dashboard] Success: "
            f"total_members={metrics.total_members}, "
            f"active={metrics.active_members}, "
            f"donors={metrics.total_donors}"
        )

        return metrics

    except ValueError as e:
        logger.error(f"[get_member_dashboard] ValueError: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(
            f"[get_member_dashboard] Unexpected error: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating member statistics"
        )


@router.get(
    "/health",
    summary="Member Analytics Service Health Check",
    description="Check if member analytics service is operational"
)
async def health_check():
    """
    Health check endpoint for member analytics service.

    Returns:
        Dict with service status
    """
    return {
        "service": "member_analytics",
        "status": "healthy",
        "message": "Member analytics service is operational"
    }
