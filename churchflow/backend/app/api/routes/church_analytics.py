"""
Church Analytics API Routes for ChurchFlow - Phase 7

Provides endpoints for:
- Conference analytics (registrations, attendance, engagement)
- Member engagement metrics
- Communication effectiveness
- Dashboard aggregations
- Predictive analytics

Note: This is separate from analytics.py which handles cost/wallet analytics.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import datetime

from app.api.dependencies import get_current_user
from app.core.database import get_database
from app.services.church_analytics_service import ChurchAnalyticsService
from app.models.analytics import (
    ConferenceAnalytics,
    MemberEngagementMetrics,
    CommunicationMetrics,
    ChurchDashboardMetrics,
    MetricPeriod
)

router = APIRouter(prefix="/church-analytics", tags=["Church Analytics"])


def verify_organization_access(current_user: dict = Depends(get_current_user)) -> str:
    """
    Extract and verify organization ID from current user.

    Args:
        current_user: Current authenticated user

    Returns:
        Organization ID

    Raises:
        HTTPException: If organization ID not found
    """
    organization_id = (
        current_user.get("organization_id") or
        current_user.get("user_id") or
        current_user.get("sub")
    )

    if not organization_id:
        raise HTTPException(
            status_code=403,
            detail="Organization ID not found in user context"
        )

    return organization_id


@router.get("/conference/{conference_id}", response_model=ConferenceAnalytics)
async def get_conference_analytics(
    conference_id: str,
    organization_id: str = Depends(verify_organization_access),
    db = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive analytics for a specific conference.

    Includes:
    - Registration metrics and trends
    - Attendance and check-in rates
    - Branch distribution
    - Bus usage statistics
    - Timing metrics

    Args:
        conference_id: Conference ID
        organization_id: Organization ID (from auth)
        db: Database connection
        current_user: Current authenticated user

    Returns:
        ConferenceAnalytics model

    Raises:
        HTTPException: If conference not found or access denied
    """
    try:
        analytics_service = ChurchAnalyticsService(db)
        analytics = await analytics_service.get_conference_analytics(
            conference_id=conference_id,
            organization_id=organization_id
        )
        return analytics
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conference analytics: {str(e)}"
        )


@router.get("/engagement", response_model=MemberEngagementMetrics)
async def get_member_engagement(
    period: MetricPeriod = Query(
        MetricPeriod.THIRTY_DAYS,
        description="Time period for analysis"
    ),
    start_date: Optional[datetime] = Query(
        None,
        description="Custom period start (for CUSTOM period)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="Custom period end (for CUSTOM period)"
    ),
    organization_id: str = Depends(verify_organization_access),
    db = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Get member engagement metrics for the organization.

    Includes:
    - Total, active, and inactive member counts
    - Engagement score and level
    - Repeat attendance rate
    - Top engaged members
    - Retention rate

    Args:
        period: Time period (7d, 30d, 90d, 1y, custom)
        start_date: Custom period start (required if period is CUSTOM)
        end_date: Custom period end (required if period is CUSTOM)
        organization_id: Organization ID (from auth)
        db: Database connection
        current_user: Current authenticated user

    Returns:
        MemberEngagementMetrics model

    Raises:
        HTTPException: If validation fails or error occurs
    """
    try:
        if period == MetricPeriod.CUSTOM and (not start_date or not end_date):
            raise HTTPException(
                status_code=400,
                detail="start_date and end_date required for CUSTOM period"
            )

        analytics_service = ChurchAnalyticsService(db)
        metrics = await analytics_service.get_member_engagement(
            organization_id=organization_id,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get engagement metrics: {str(e)}"
        )


@router.get("/communication", response_model=CommunicationMetrics)
async def get_communication_metrics(
    start_date: datetime = Query(..., description="Period start date"),
    end_date: datetime = Query(..., description="Period end date"),
    organization_id: str = Depends(verify_organization_access),
    db = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Get communication effectiveness metrics.

    Includes:
    - SMS delivery rates and costs
    - Email open and click rates
    - Campaign performance
    - Cost per attendee

    Args:
        start_date: Period start date
        end_date: Period end date
        organization_id: Organization ID (from auth)
        db: Database connection
        current_user: Current authenticated user

    Returns:
        CommunicationMetrics model

    Raises:
        HTTPException: If validation fails or error occurs
    """
    try:
        if start_date >= end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date must be before end_date"
            )

        analytics_service = ChurchAnalyticsService(db)
        metrics = await analytics_service.get_communication_metrics(
            organization_id=organization_id,
            period_start=start_date,
            period_end=end_date
        )
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get communication metrics: {str(e)}"
        )


@router.get("/dashboard", response_model=ChurchDashboardMetrics)
async def get_dashboard_metrics(
    period: MetricPeriod = Query(
        MetricPeriod.THIRTY_DAYS,
        description="Time period for dashboard"
    ),
    organization_id: str = Depends(verify_organization_access),
    db = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive dashboard metrics for church admin.

    Aggregates all key metrics:
    - Event and attendance metrics
    - Communication metrics (SMS/email)
    - Member engagement and retention
    - Trends vs previous period
    - AI-generated insights and alerts

    This is the primary endpoint for the admin dashboard UI.

    Args:
        period: Time period (7d, 30d, 90d, 1y)
        organization_id: Organization ID (from auth)
        db: Database connection
        current_user: Current authenticated user

    Returns:
        ChurchDashboardMetrics model with all dashboard data

    Raises:
        HTTPException: If validation fails or error occurs
    """
    try:
        analytics_service = ChurchAnalyticsService(db)
        dashboard = await analytics_service.get_dashboard_metrics(
            organization_id=organization_id,
            period=period
        )
        return dashboard
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard metrics: {str(e)}"
        )
