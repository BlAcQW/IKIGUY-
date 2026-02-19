"""
Analytics API routes for ChurchFlow.

Provides endpoints for tracking conference costs, organization usage, kiosk engagement, and attendance analytics.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from ...services.analytics_service import get_analytics_service, ChurchFlowAnalyticsService
from app.api.dependencies import get_current_user, require_organization_access
from app.core.database import get_database
from bson import ObjectId

router = APIRouter(prefix="/analytics", tags=["Analytics"])
logger = logging.getLogger(__name__)


class ConferenceCostsResponse(BaseModel):
    """Response model for conference costs."""
    conference_id: str
    period: dict
    total_cost: float
    kiosk: dict
    voice_calls: dict
    sms: dict
    cost_distribution: dict


class OrganizationUsageResponse(BaseModel):
    """Response model for organization usage."""
    organization_id: str
    period: dict
    total_cost: float
    total_activities: int
    unique_conferences: int
    services: dict


class KioskEngagementResponse(BaseModel):
    """Response model for kiosk engagement metrics."""
    conference_id: str
    period: dict
    total_interactions: int
    unique_members: int
    total_duration_seconds: int
    average_duration_seconds: float


@router.get(
    "/conferences/{conference_id}/costs",
    response_model=ConferenceCostsResponse,
    summary="Get conference costs",
    description="""
    Get comprehensive cost breakdown for a conference including:
    - Kiosk interactions (greetings, registrations, queries)
    - Voice calls (reminders, updates, confirmations)
    - SMS notifications
    """
)
async def get_conference_costs(
    conference_id: str,
    start_date: Optional[str] = Query(None, description="Start date (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO 8601 format)"),
    organization_id: str = Depends(require_organization_access),
    current_user: dict = Depends(get_current_user),
    analytics_service: ChurchFlowAnalyticsService = Depends(get_analytics_service)
):
    """
    Get comprehensive cost breakdown for a conference.

    Args:
        conference_id: Conference ID
        start_date: Optional start date filter (ISO 8601)
        end_date: Optional end date filter (ISO 8601)
        organization_id: Organization ID (verified from header)

    Returns:
        Conference costs breakdown
    """
    try:
        # CRITICAL: Verify conference belongs to organization
        db = get_database()
        conference = await db.conferences.find_one({
            "_id": ObjectId(conference_id),
            "organization_id": organization_id
        })

        if not conference:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Conference not in your organization"
            )

        # Parse dates if provided
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        # Get conference costs
        costs = await analytics_service.get_conference_costs(
            conference_id=conference_id,
            start_date=start_dt,
            end_date=end_dt
        )

        # Check for errors
        if "error" in costs:
            raise HTTPException(status_code=404, detail=costs["error"])

        return costs

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conference costs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conference costs: {str(e)}")


@router.get(
    "/usage",
    response_model=OrganizationUsageResponse,
    summary="Get organization usage",
    description="""
    Get usage summary for the organization across all conferences.

    Shows:
    - Total costs
    - Activity counts by service (kiosk, voice, SMS)
    - Number of conferences
    """
)
async def get_organization_usage(
    start_date: Optional[str] = Query(None, description="Start date (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO 8601 format)"),
    organization_id: str = Depends(require_organization_access),
    current_user: dict = Depends(get_current_user),
    analytics_service: ChurchFlowAnalyticsService = Depends(get_analytics_service)
):
    """
    Get organization usage summary.

    Args:
        start_date: Optional start date filter (ISO 8601)
        end_date: Optional end date filter (ISO 8601)
        organization_id: Organization ID (verified from header)

    Returns:
        Organization usage summary
    """
    try:
        # Parse dates if provided
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        # Get usage
        usage = await analytics_service.get_organization_usage(
            organization_id=organization_id,
            start_date=start_dt,
            end_date=end_dt
        )

        # Check for errors
        if "error" in usage:
            raise HTTPException(status_code=500, detail=usage["error"])

        return usage

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get organization usage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get organization usage: {str(e)}")


@router.get(
    "/conferences/{conference_id}/kiosk-engagement",
    response_model=KioskEngagementResponse,
    summary="Get kiosk engagement metrics",
    description="""
    Get detailed kiosk engagement metrics for a conference.

    Tracks:
    - Total interactions
    - Unique members who used kiosk
    - Total and average interaction duration
    """
)
async def get_kiosk_engagement(
    conference_id: str,
    start_date: Optional[str] = Query(None, description="Start date (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO 8601 format)"),
    organization_id: str = Depends(require_organization_access),
    current_user: dict = Depends(get_current_user),
    analytics_service: ChurchFlowAnalyticsService = Depends(get_analytics_service)
):
    """
    Get kiosk engagement metrics for a conference.

    Args:
        conference_id: Conference ID
        start_date: Optional start date filter (ISO 8601)
        end_date: Optional end date filter (ISO 8601)
        organization_id: Organization ID (verified from header)

    Returns:
        Kiosk engagement metrics
    """
    try:
        # CRITICAL: Verify conference belongs to organization
        db = get_database()
        conference = await db.conferences.find_one({
            "_id": ObjectId(conference_id),
            "organization_id": organization_id
        })

        if not conference:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Conference not in your organization"
            )

        # Parse dates if provided
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        # Get kiosk engagement
        engagement = await analytics_service.get_kiosk_engagement_metrics(
            conference_id=conference_id,
            start_date=start_dt,
            end_date=end_dt
        )

        # Check for errors
        if "error" in engagement:
            raise HTTPException(status_code=404, detail=engagement["error"])

        return engagement

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get kiosk engagement: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get kiosk engagement: {str(e)}")


@router.get(
    "/attendance",
    summary="Get attendance analytics",
    description="Get comprehensive attendance statistics and trends for services."
)
async def get_attendance_analytics(
    period: str = Query("30d", description="Time period: 7d, 30d, 90d, 6m, 1y"),
    branch_id: Optional[str] = Query(None, description="Filter by branch"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get attendance analytics for services.

    Args:
        period: Time period for analytics
        branch_id: Optional branch filter
        current_user: Authenticated user

    Returns:
        Comprehensive attendance statistics
    """
    db = get_database()

    # Calculate date range
    period_days = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "6m": 180,
        "1y": 365
    }
    days = period_days.get(period, 30)
    start_date = datetime.utcnow() - timedelta(days=days)

    # Build service query
    service_query = {
        "service_date": {"$gte": start_date},
        "status": {"$in": ["completed", "ongoing"]}
    }
    if branch_id and ObjectId.is_valid(branch_id):
        service_query["branch_id"] = ObjectId(branch_id)

    # Get services in period
    services = await db.services.find(service_query).to_list(length=None)
    service_ids = [s["_id"] for s in services]

    # Get attendance records
    attendance_query = {"service_id": {"$in": service_ids}}
    attendance_records = await db.session_attendance.find(attendance_query).to_list(length=None)

    # Get user IDs from attendance
    user_ids = list(set([a["user_id"] for a in attendance_records if a.get("user_id")]))

    # Get user details
    users = {}
    if user_ids:
        object_ids = [ObjectId(uid) for uid in user_ids if ObjectId.is_valid(str(uid))]
        user_docs = await db.users.find({"_id": {"$in": object_ids}}).to_list(length=None)
        users = {str(u["_id"]): u for u in user_docs}

    # Calculate statistics
    total_services = len(services)
    total_attendance = len(attendance_records)
    average_attendance = total_attendance / total_services if total_services > 0 else 0

    # Member vs Visitor breakdown
    member_count = 0
    visitor_count = 0
    first_timer_count = 0
    returning_visitor_count = 0

    for record in attendance_records:
        user_id = record.get("user_id")
        user_id_str = str(user_id) if user_id else None
        if user_id_str and user_id_str in users:
            user = users[user_id_str]
            member_status = user.get("member_status", "visitor")
            spiritual_stage = user.get("current_spiritual_stage", "unknown")

            if member_status == "active_member":
                member_count += 1
            else:
                visitor_count += 1

            if spiritual_stage == "first_timer":
                first_timer_count += 1
            elif spiritual_stage == "second_timer":
                returning_visitor_count += 1

    # Calculate growth rate (compare to previous period)
    previous_start = start_date - timedelta(days=days)
    previous_service_query = {
        "service_date": {"$gte": previous_start, "$lt": start_date},
        "status": {"$in": ["completed", "ongoing"]}
    }
    if branch_id and ObjectId.is_valid(branch_id):
        previous_service_query["branch_id"] = ObjectId(branch_id)

    previous_services = await db.services.find(previous_service_query).to_list(length=None)
    previous_service_ids = [s["_id"] for s in previous_services]
    previous_attendance = await db.session_attendance.count_documents(
        {"service_id": {"$in": previous_service_ids}}
    )

    growth_rate = 0.0
    if previous_attendance > 0:
        growth_rate = ((total_attendance - previous_attendance) / previous_attendance) * 100

    # Attendance by service type
    service_type_stats = {}
    for service in services:
        service_type = service.get("service_type", "unknown")
        if service_type not in service_type_stats:
            service_type_stats[service_type] = {"count": 0, "total_attendance": 0}

        service_type_stats[service_type]["count"] += 1
        # Count attendance for this service
        service_attendance = sum(1 for a in attendance_records if a["service_id"] == service["_id"])
        service_type_stats[service_type]["total_attendance"] += service_attendance

    attendance_by_service_type = [
        {
            "service_type": st,
            "count": data["count"],
            "avg_attendance": data["total_attendance"] / data["count"] if data["count"] > 0 else 0
        }
        for st, data in service_type_stats.items()
    ]

    # Attendance trend (weekly grouping)
    trend_data = {}
    for service in services:
        service_date = service["service_date"]
        week_start = service_date - timedelta(days=service_date.weekday())
        week_key = week_start.strftime("%Y-%m-%d")

        if week_key not in trend_data:
            trend_data[week_key] = {"total": 0, "members": 0, "visitors": 0}

        service_attendance = [a for a in attendance_records if a["service_id"] == service["_id"]]
        trend_data[week_key]["total"] += len(service_attendance)

        for record in service_attendance:
            user_id = record.get("user_id")
            user_id_str = str(user_id) if user_id else None
            if user_id_str and user_id_str in users:
                if users[user_id_str].get("member_status") == "active_member":
                    trend_data[week_key]["members"] += 1
                else:
                    trend_data[week_key]["visitors"] += 1

    attendance_trend = [
        {"date": date, **data}
        for date, data in sorted(trend_data.items())
    ]

    # Department interests
    department_stats = {}
    for user in users.values():
        departments = user.get("departments", [])
        for dept in departments:
            dept_name = dept.get("name")
            if dept_name:
                department_stats[dept_name] = department_stats.get(dept_name, 0) + 1

    department_interests = [
        {"department": dept, "count": count}
        for dept, count in sorted(department_stats.items(), key=lambda x: x[1], reverse=True)
    ][:10]  # Top 10

    # Spiritual stage breakdown
    stage_stats = {}
    for user in users.values():
        stage = user.get("current_spiritual_stage", "unknown")
        stage_stats[stage] = stage_stats.get(stage, 0) + 1

    spiritual_stage_breakdown = [
        {"stage": stage, "count": count}
        for stage, count in sorted(stage_stats.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "total_services": total_services,
        "total_attendance": total_attendance,
        "average_attendance": average_attendance,
        "member_count": member_count,
        "visitor_count": visitor_count,
        "first_timer_count": first_timer_count,
        "returning_visitor_count": returning_visitor_count,
        "growth_rate": growth_rate,
        "attendance_by_service_type": attendance_by_service_type,
        "attendance_trend": attendance_trend,
        "department_interests": department_interests,
        "spiritual_stage_breakdown": spiritual_stage_breakdown
    }


@router.get(
    "/health",
    summary="Analytics service health check",
    description="Check if analytics service is initialized and working"
)
async def analytics_health(
    analytics_service: ChurchFlowAnalyticsService = Depends(get_analytics_service)
):
    """
    Health check for analytics service.

    Returns:
        Service health status
    """
    return {
        "status": "healthy" if analytics_service.initialized else "not_initialized",
        "service": "churchflow_analytics"
    }
