"""
Dashboard statistics API endpoints.

Provides aggregated statistics for the admin dashboard including
registered members count and today's check-in count.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

from app.core.database import get_database
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response schema."""

    total_registered: int = Field(..., description="Total unique registered members")
    checked_in_today: int = Field(..., description="Unique attendees checked in today")
    total_conferences: int = Field(..., description="Total number of conferences")
    active_bus_routes: int = Field(..., description="Number of active bus routes")
    registrations_today: int = Field(0, description="New registrations today")
    sessions_today: int = Field(0, description="Number of sessions scheduled today")


class ConferenceStatsResponse(BaseModel):
    """Per-conference statistics response schema."""

    conference_id: str = Field(..., description="Conference ID")
    conference_name: str = Field(..., description="Conference name")
    total_registered: int = Field(..., description="Total registrations for this conference")
    checked_in_today: int = Field(..., description="Unique check-ins today for this conference")
    total_sessions: int = Field(..., description="Total sessions in this conference")


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="Get dashboard statistics",
    description="Get aggregated statistics for the admin dashboard."
)
async def get_dashboard_stats(
    conference_id: Optional[str] = Query(None, description="Filter by conference ID")
):
    """
    Get dashboard statistics.

    Returns:
        DashboardStatsResponse with counts for registered members,
        today's check-ins, conferences, and bus routes.
    """
    db = get_database()

    try:
        # Get today's date range (UTC)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        # Build base filter for conference-specific queries
        conf_filter = {}
        if conference_id:
            from bson import ObjectId
            if ObjectId.is_valid(conference_id):
                conf_filter["conference_id"] = ObjectId(conference_id)

        # Count total unique registered members (by phone number)
        registration_filter = {"status": "confirmed"}
        if conf_filter:
            registration_filter.update(conf_filter)

        # Use aggregation to count unique phone numbers
        unique_members_pipeline = [
            {"$match": registration_filter},
            {"$group": {"_id": "$user_phone"}},
            {"$count": "total"}
        ]
        unique_result = await db.conference_registrations.aggregate(unique_members_pipeline).to_list(length=1)
        total_registered = unique_result[0]["total"] if unique_result else 0

        # Count unique attendees checked in today
        attendance_filter = {
            "checked_in_at": {"$gte": today_start, "$lt": today_end}
        }
        if conf_filter:
            attendance_filter.update(conf_filter)

        # Use aggregation to count unique registrations checked in today
        checkin_pipeline = [
            {"$match": attendance_filter},
            {"$group": {"_id": "$registration_id"}},
            {"$count": "total"}
        ]
        checkin_result = await db.session_attendance.aggregate(checkin_pipeline).to_list(length=1)
        checked_in_today = checkin_result[0]["total"] if checkin_result else 0

        # Count total conferences
        total_conferences = await db.conferences.count_documents({})

        # Count active bus routes
        active_bus_routes = await db.bus_routes.count_documents({"status": "active"})

        # Count new registrations today
        registrations_today_filter = {
            "status": "confirmed",
            "registered_at": {"$gte": today_start, "$lt": today_end}
        }
        if conf_filter:
            registrations_today_filter.update(conf_filter)
        registrations_today = await db.conference_registrations.count_documents(registrations_today_filter)

        # Count sessions scheduled for today
        sessions_filter = {
            "session_date": {"$gte": today_start, "$lt": today_end}
        }
        if conf_filter:
            sessions_filter.update(conf_filter)
        sessions_today = await db.conference_sessions.count_documents(sessions_filter)

        return DashboardStatsResponse(
            total_registered=total_registered,
            checked_in_today=checked_in_today,
            total_conferences=total_conferences,
            active_bus_routes=active_bus_routes,
            registrations_today=registrations_today,
            sessions_today=sessions_today
        )

    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard stats: {str(e)}"
        )


@router.get(
    "/stats/conference/{conference_id}",
    response_model=ConferenceStatsResponse,
    summary="Get conference-specific statistics",
    description="Get statistics for a specific conference."
)
async def get_conference_stats(conference_id: str):
    """
    Get statistics for a specific conference.

    Args:
        conference_id: Conference ID to get stats for

    Returns:
        ConferenceStatsResponse with conference-specific counts.
    """
    db = get_database()

    try:
        from bson import ObjectId

        if not ObjectId.is_valid(conference_id):
            raise HTTPException(status_code=400, detail="Invalid conference ID")

        conf_oid = ObjectId(conference_id)

        # Get conference details
        conference = await db.conferences.find_one({"_id": conf_oid})
        if not conference:
            raise HTTPException(status_code=404, detail="Conference not found")

        # Get today's date range (UTC)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        # Count registrations for this conference
        total_registered = await db.conference_registrations.count_documents({
            "conference_id": conf_oid,
            "status": "confirmed"
        })

        # Count unique check-ins today for this conference
        checkin_pipeline = [
            {
                "$match": {
                    "conference_id": conf_oid,
                    "checked_in_at": {"$gte": today_start, "$lt": today_end}
                }
            },
            {"$group": {"_id": "$registration_id"}},
            {"$count": "total"}
        ]
        checkin_result = await db.session_attendance.aggregate(checkin_pipeline).to_list(length=1)
        checked_in_today = checkin_result[0]["total"] if checkin_result else 0

        # Count sessions in this conference
        total_sessions = await db.conference_sessions.count_documents({
            "conference_id": conf_oid
        })

        return ConferenceStatsResponse(
            conference_id=conference_id,
            conference_name=conference.get("name", "Unknown"),
            total_registered=total_registered,
            checked_in_today=checked_in_today,
            total_sessions=total_sessions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conference stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conference stats: {str(e)}"
        )
