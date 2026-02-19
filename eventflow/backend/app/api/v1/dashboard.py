"""
Dashboard API routes for EventFlow.

Provides comprehensive dashboard statistics and metrics endpoints.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ...services.dashboard_service import DashboardService
from ...core.database import get_database
from ..dependencies import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
logger = logging.getLogger(__name__)


class DashboardStatsResponse(BaseModel):
    """Response model for dashboard statistics."""
    user_id: str
    organization_id: Optional[str] = None
    timestamp: str
    events: dict
    tasks: dict
    budget: dict
    timeline: dict
    activity: dict
    summary: dict


class EventDashboardResponse(BaseModel):
    """Response model for event-specific dashboard."""
    event_id: str
    event_name: Optional[str] = None
    event_type: Optional[str] = None
    event_status: Optional[str] = None
    event_date: Optional[str] = None
    days_until_event: Optional[int] = None
    location: Optional[str] = None
    num_guests: int = 0
    tasks: dict
    budget: dict
    completion: dict
    team: dict
    alerts: list


@router.get(
    "/statistics",
    response_model=DashboardStatsResponse,
    summary="Get dashboard statistics",
    description="""
    Get comprehensive dashboard statistics for the authenticated user.

    Includes:
    - Event statistics (total, by status, by type, upcoming, active, past)
    - Task statistics (total, by status, by priority, by category, overdue, completion rate)
    - Budget statistics (total budgets, cost estimates, actuals, utilization)
    - Timeline statistics (next event, upcoming events)
    - Activity statistics (recent activity counts)
    - Summary insights and priority actions
    """
)
async def get_dashboard_statistics(
    organization_id: Optional[str] = Query(None, description="Organization ID filter"),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get comprehensive dashboard statistics.

    Args:
        organization_id: Optional organization ID filter
        current_user: Current authenticated user
        db: Database instance

    Returns:
        Comprehensive dashboard statistics
    """
    try:
        # Get user ID
        user_id = current_user.get("user_id") or current_user.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        # Create dashboard service
        dashboard_service = DashboardService(db)

        # Get statistics
        stats = await dashboard_service.get_dashboard_statistics(
            user_id=user_id,
            organization_id=organization_id
        )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard statistics: {str(e)}"
        )


@router.get(
    "/events/{event_id}",
    response_model=EventDashboardResponse,
    summary="Get event dashboard",
    description="""
    Get comprehensive dashboard statistics for a specific event.

    Includes:
    - Event details and timeline
    - Task statistics and completion metrics
    - Budget tracking and utilization
    - Team composition
    - Alerts and action items
    """
)
async def get_event_dashboard(
    event_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get event-specific dashboard statistics.

    Args:
        event_id: Event ID
        current_user: Current authenticated user
        db: Database instance

    Returns:
        Event dashboard statistics
    """
    try:
        # Get user ID
        user_id = current_user.get("user_id") or current_user.get("sub")

        # Create dashboard service
        dashboard_service = DashboardService(db)

        # Get event dashboard
        dashboard = await dashboard_service.get_event_dashboard(
            event_id=event_id,
            user_id=user_id
        )

        return dashboard

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get event dashboard: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get event dashboard: {str(e)}"
        )


@router.get(
    "/health",
    summary="Dashboard service health check",
    description="Check if dashboard service is working correctly"
)
async def dashboard_health(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Health check for dashboard service.

    Returns:
        Service health status
    """
    try:
        # Try to create service and do a simple check
        dashboard_service = DashboardService(db)

        # Verify database connection
        await db.command("ping")

        return {
            "status": "healthy",
            "service": "eventflow_dashboard"
        }
    except Exception as e:
        logger.error(f"Dashboard health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "eventflow_dashboard",
            "error": str(e)
        }
