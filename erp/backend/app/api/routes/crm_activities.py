"""
CRM Activity Tracking Routes.

Handles activity logging and tracking for CRM entities (leads, customers, opportunities, contacts).
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.database import MongoDB
from app.models.crm import Activity, ActivityType, ActivityEntityType
from app.schemas.crm import ActivityCreate, ActivityUpdate, ActivityStats
from apps.shared.dependencies import require_organization_access, OrganizationScoped

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/activities", response_model=Activity, status_code=status.HTTP_201_CREATED)
async def create_activity(
    activity_data: ActivityCreate,
    scope: OrganizationScoped = Depends(),
):
    """
    Log a new activity.

    Activities track all interactions with CRM entities:
    - Calls, emails, meetings
    - Notes and follow-ups
    - Demos and proposals

    Example request:
    ```json
    {
      "entity_type": "lead",
      "entity_id": "lead_12345",
      "activity_type": "call",
      "subject": "Discovery call",
      "description": "Discussed requirements for enterprise plan",
      "duration_minutes": 30,
      "call_outcome": "answered",
      "requires_follow_up": true,
      "follow_up_date": "2025-11-20T10:00:00"
    }
    ```
    """
    db = MongoDB.get_database()

    # Create activity with organization and user context
    activity = Activity(
        **activity_data.model_dump(),
        organization_id=scope.org_id,
        performed_by=scope.user.get("id") or scope.user.get("sub"),
    )

    await db.activities.insert_one(activity.model_dump())
    logger.info(f"Activity {activity.id} logged for {activity_data.entity_type} {activity_data.entity_id}")
    return activity


@router.get("/activities", response_model=List[Activity])
async def list_activities(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    activity_type: Optional[str] = None,
    performed_by: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    requires_follow_up: Optional[bool] = None,
):
    """
    List activities with filters.

    Supports filtering by:
    - entity_type and entity_id (e.g., all activities for a specific lead)
    - activity_type (e.g., only calls)
    - performed_by (user ID)
    - date range (start_date, end_date)
    - requires_follow_up (pending follow-ups)
    """
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Apply filters
    if entity_type:
        query["entity_type"] = entity_type
    if entity_id:
        query["entity_id"] = entity_id
    if activity_type:
        query["activity_type"] = activity_type
    if performed_by:
        query["performed_by"] = performed_by
    if requires_follow_up is not None:
        query["requires_follow_up"] = requires_follow_up
    if start_date:
        query.setdefault("activity_date", {})["$gte"] = start_date
    if end_date:
        query.setdefault("activity_date", {})["$lte"] = end_date

    cursor = db.activities.find(query).skip(skip).limit(limit).sort("activity_date", -1)
    activities = await cursor.to_list(length=limit)
    return [Activity(**a) for a in activities]


@router.get("/activities/{activity_id}", response_model=Activity)
async def get_activity(
    activity_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get activity details by ID."""
    db = MongoDB.get_database()
    activity = await db.activities.find_one({"id": activity_id, "organization_id": org_id})

    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    return Activity(**activity)


@router.patch("/activities/{activity_id}", response_model=Activity)
async def update_activity(
    activity_id: str,
    update_data: ActivityUpdate,
    scope: OrganizationScoped = Depends(),
):
    """Update an activity."""
    db = MongoDB.get_database()

    # Only include fields that were actually set
    update_dict = update_data.model_dump(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()
    update_dict["updated_by"] = scope.user.get("id") or scope.user.get("sub")

    result = await db.activities.update_one(
        {"id": activity_id, "organization_id": scope.org_id},
        {"$set": update_dict}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    activity = await db.activities.find_one({"id": activity_id})
    return Activity(**activity)


@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete an activity."""
    db = MongoDB.get_database()

    result = await db.activities.update_one(
        {"id": activity_id, "organization_id": org_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    return None


@router.get("/activities/timeline/{entity_type}/{entity_id}", response_model=List[Activity])
async def get_entity_timeline(
    entity_type: str,
    entity_id: str,
    org_id: str = Depends(require_organization_access),
    limit: int = Query(50, ge=1, le=500),
):
    """
    Get full activity timeline for an entity.

    Returns all activities for a specific lead, customer, opportunity, or contact,
    sorted by date (most recent first).

    Useful for displaying a complete interaction history.
    """
    db = MongoDB.get_database()

    query = {
        "organization_id": org_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "is_active": True
    }

    cursor = db.activities.find(query).limit(limit).sort("activity_date", -1)
    activities = await cursor.to_list(length=limit)
    return [Activity(**a) for a in activities]


@router.get("/activities/upcoming-follow-ups", response_model=List[Activity])
async def get_upcoming_follow_ups(
    org_id: str = Depends(require_organization_access),
    days_ahead: int = Query(7, ge=1, le=90, description="Number of days to look ahead"),
    assigned_to: Optional[str] = Query(None, description="Filter by user ID"),
):
    """
    Get upcoming follow-ups.

    Returns activities that require follow-up within the next N days.
    Excludes follow-ups that are already completed.

    Useful for dashboards and task lists.
    """
    db = MongoDB.get_database()

    now = datetime.utcnow()
    future_date = now + timedelta(days=days_ahead)

    query = {
        "organization_id": org_id,
        "is_active": True,
        "requires_follow_up": True,
        "follow_up_completed": False,
        "follow_up_date": {
            "$gte": now,
            "$lte": future_date
        }
    }

    if assigned_to:
        query["performed_by"] = assigned_to

    cursor = db.activities.find(query).sort("follow_up_date", 1).limit(100)
    activities = await cursor.to_list(length=100)
    return [Activity(**a) for a in activities]


@router.patch("/activities/{activity_id}/complete-follow-up", response_model=Activity)
async def complete_follow_up(
    activity_id: str,
    scope: OrganizationScoped = Depends(),
):
    """
    Mark follow-up as completed.

    Updates the activity to indicate the follow-up was done.
    Records completion timestamp.
    """
    db = MongoDB.get_database()

    result = await db.activities.update_one(
        {"id": activity_id, "organization_id": scope.org_id},
        {
            "$set": {
                "follow_up_completed": True,
                "follow_up_completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "updated_by": scope.user.get("id") or scope.user.get("sub")
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    activity = await db.activities.find_one({"id": activity_id})
    return Activity(**activity)


@router.get("/activities/stats", response_model=ActivityStats)
async def get_activity_stats(
    org_id: str = Depends(require_organization_access),
):
    """
    Get activity statistics.

    Returns:
    - Total activity count
    - Activities by type (calls, emails, meetings, etc.)
    - Activities this week/month
    - Pending and completed follow-ups
    - Top performers by activity count
    """
    db = MongoDB.get_database()

    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Total activities
    total_activities = await db.activities.count_documents({
        "organization_id": org_id,
        "is_active": True
    })

    # Activities by type
    pipeline = [
        {"$match": {"organization_id": org_id, "is_active": True}},
        {"$group": {"_id": "$activity_type", "count": {"$sum": 1}}}
    ]
    activities_by_type_cursor = db.activities.aggregate(pipeline)
    activities_by_type_list = await activities_by_type_cursor.to_list(length=20)
    activities_by_type = {item["_id"]: item["count"] for item in activities_by_type_list}

    # Activities this week
    activities_this_week = await db.activities.count_documents({
        "organization_id": org_id,
        "is_active": True,
        "activity_date": {"$gte": week_ago}
    })

    # Activities this month
    activities_this_month = await db.activities.count_documents({
        "organization_id": org_id,
        "is_active": True,
        "activity_date": {"$gte": month_ago}
    })

    # Pending follow-ups
    pending_follow_ups = await db.activities.count_documents({
        "organization_id": org_id,
        "is_active": True,
        "requires_follow_up": True,
        "follow_up_completed": False,
        "follow_up_date": {"$lte": now}
    })

    # Completed follow-ups
    completed_follow_ups = await db.activities.count_documents({
        "organization_id": org_id,
        "is_active": True,
        "follow_up_completed": True
    })

    # Top performers
    pipeline = [
        {"$match": {"organization_id": org_id, "is_active": True}},
        {"$group": {"_id": "$performed_by", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_performers_cursor = db.activities.aggregate(pipeline)
    top_performers_list = await top_performers_cursor.to_list(length=10)
    top_performers = [
        {"user_id": item["_id"], "activity_count": item["count"]}
        for item in top_performers_list
    ]

    return ActivityStats(
        total_activities=total_activities,
        activities_by_type=activities_by_type,
        activities_this_week=activities_this_week,
        activities_this_month=activities_this_month,
        pending_follow_ups=pending_follow_ups,
        completed_follow_ups=completed_follow_ups,
        top_performers=top_performers
    )
