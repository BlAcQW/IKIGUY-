"""
Calendar routes for devotional scheduling and planning.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from datetime import date, datetime, timedelta
from app.models.calendar import (
    CalendarMonthView,
    CalendarWeekView,
    ScheduleSlot,
    BulkScheduleRequest,
    BulkScheduleResponse,
)
from app.models.user import TokenData
from app.services.calendar_service import CalendarService
from app.utils.auth import get_current_admin

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/month", response_model=CalendarMonthView)
async def get_month_view(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    status: str = Query(None),
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get monthly calendar view of devotionals.

    Requires admin role.

    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)
        status: Optional status filter (published, scheduled, draft)

    Returns:
        Monthly calendar with devotionals grouped by date
    """
    service = CalendarService()
    try:
        return await service.get_month_view(
            current_user.user_id, year, month, status
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch month view: {str(e)}",
        )


@router.get("/week", response_model=CalendarWeekView)
async def get_week_view(
    week_start: date = Query(..., description="Start date of week (Monday)"),
    status: str = Query(None),
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get weekly calendar view of devotionals.

    Requires admin role.

    Args:
        week_start: Start date of the week (Monday)
        status: Optional status filter (published, scheduled, draft)

    Returns:
        Weekly calendar with devotionals grouped by date
    """
    service = CalendarService()
    try:
        return await service.get_week_view(
            current_user.user_id, week_start, status
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch week view: {str(e)}",
        )


@router.get("/available-slots", response_model=List[ScheduleSlot])
async def get_available_slots(
    start_date: date = Query(default_factory=date.today),
    days: int = Query(30, ge=1, le=365),
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get available schedule slots for devotionals.

    Requires admin role.

    Args:
        start_date: Start date for checking slots (default: today)
        days: Number of days to check (default: 30, max: 365)

    Returns:
        List of schedule slots indicating availability
    """
    service = CalendarService()
    try:
        return await service.get_available_slots(
            current_user.user_id, start_date, days
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch available slots: {str(e)}",
        )


@router.post("/bulk-schedule", response_model=BulkScheduleResponse)
async def bulk_schedule_devotionals(
    request: BulkScheduleRequest,
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Bulk schedule multiple devotionals.

    Requires admin role.

    Args:
        request: Bulk schedule request with devotional IDs and scheduling options

    Returns:
        Results of bulk scheduling operation
    """
    service = CalendarService()
    try:
        return await service.bulk_schedule(current_user.user_id, request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk schedule: {str(e)}",
        )


@router.get("/gaps")
async def get_schedule_gaps(
    start_date: str = Query(None),
    end_date: str = Query(None),
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get gaps in devotional schedule (dates with no scheduled devotionals).

    Requires admin role.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        List of dates with no scheduled devotionals
    """
    from app.db.mongodb import get_database
    from datetime import datetime, timedelta

    db = get_database()

    # Default to 30 days from today if not provided
    if not start_date:
        start = datetime.utcnow()
    else:
        start = datetime.fromisoformat(start_date)

    if not end_date:
        end = start + timedelta(days=30)
    else:
        end = datetime.fromisoformat(end_date)

    # Get all scheduled devotionals in date range
    devotionals = await db.devotionals.find({
        "status": {"$in": ["published", "scheduled"]},
        "scheduled_at": {"$gte": start, "$lte": end}
    }).to_list(None)

    # Get scheduled dates
    scheduled_dates = set()
    for dev in devotionals:
        if dev.get("scheduled_at"):
            scheduled_dates.add(dev["scheduled_at"].date())

    # Find gaps
    gaps = []
    current = start.date()
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    while current <= end.date():
        if current not in scheduled_dates:
            gaps.append({
                "date": current.isoformat(),
                "day_of_week": day_names[current.weekday()]
            })
        current += timedelta(days=1)

    return {"gaps": gaps}


@router.get("/upcoming")
async def get_upcoming_devotionals(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(5, ge=1, le=50),
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get upcoming scheduled devotionals.

    Requires admin role.

    Args:
        days: Number of days to look ahead (default: 7, max: 90)
        limit: Maximum number of devotionals to return (default: 5, max: 50)

    Returns:
        List of upcoming devotionals
    """
    from app.db.mongodb import get_database
    from datetime import datetime, timedelta

    db = get_database()

    start = datetime.utcnow()
    end = start + timedelta(days=days)

    devotionals = await db.devotionals.find({
        "status": {"$in": ["published", "scheduled"]},
        "scheduled_at": {"$gte": start, "$lte": end}
    }).sort("scheduled_at", 1).limit(limit).to_list(None)

    return {
        "devotionals": [
            {
                "id": str(dev["_id"]),
                "title": dev.get("title", ""),
                "scheduled_date": dev.get("scheduled_at"),
                "status": dev.get("status"),
            }
            for dev in devotionals
        ]
    }


@router.get("/devotionals")
async def get_calendar_devotionals(
    start_date: str = Query(None),
    end_date: str = Query(None),
    status: str = Query(None),
    year: int = Query(None),
    month: int = Query(None),
    week: int = Query(None),
    category: str = Query(None),
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get devotionals in calendar view format.

    Requires admin role.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        year: Year filter
        month: Month filter (1-12)
        week: Week filter
        status: Status filter (published, scheduled, draft)
        category: Category filter

    Returns:
        List of devotionals with calendar metadata
    """
    from app.db.mongodb import get_database
    from datetime import datetime, timedelta

    db = get_database()

    # Build query
    query = {}

    # Date range filter
    # Check both scheduled_at (for scheduled) and published_at (for published)
    if start_date and end_date:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        # Include end of day
        end = end.replace(hour=23, minute=59, second=59)
        query["$or"] = [
            {"scheduled_at": {"$gte": start, "$lte": end}},
            {"published_at": {"$gte": start, "$lte": end}}
        ]
    elif year and month:
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        query["$or"] = [
            {"scheduled_at": {"$gte": start, "$lt": end}},
            {"published_at": {"$gte": start, "$lt": end}}
        ]

    # Status filter
    if status:
        query["status"] = status
    else:
        query["status"] = {"$in": ["published", "scheduled", "draft"]}

    # Category filter
    if category:
        query["category"] = category

    # Fetch devotionals
    devotionals = await db.devotionals.find(query).sort("scheduled_at", 1).to_list(None)

    # Get author information
    author_ids = list(set([dev.get("author_id") for dev in devotionals if dev.get("author_id")]))
    authors = {}
    if author_ids:
        author_docs = await db.users.find({"_id": {"$in": author_ids}}).to_list(None)
        authors = {str(author["_id"]): author.get("name", "Unknown") for author in author_docs}

    # Group devotionals by series to identify series
    series_groups = {}
    standalone_devotionals = []
    
    for dev in devotionals:
        series_id = dev.get("series_id")
        if series_id:
            series_id_str = str(series_id)
            if series_id_str not in series_groups:
                series_groups[series_id_str] = {
                    "series_id": series_id_str,
                    "series_name": dev.get("series_name", "Untitled Series"),
                    "devotionals": []
                }
            series_groups[series_id_str]["devotionals"].append(dev)
        else:
            standalone_devotionals.append(dev)
    
    # Format response - include series info
    result = {
        "devotionals": [
            {
                "devotional_id": str(dev["_id"]),
                "title": dev.get("title", ""),
                "author_name": authors.get(str(dev.get("author_id")), "Unknown"),
                "status": dev.get("status", "draft"),
                "scheduled_date": (dev.get("scheduled_at") or dev.get("published_at")).isoformat() if (dev.get("scheduled_at") or dev.get("published_at")) else None,
                "category": dev.get("category"),
                "series_id": str(dev.get("series_id")) if dev.get("series_id") else None,
                "series_name": dev.get("series_name"),
                "part_number": dev.get("part_number"),
            }
            for dev in devotionals
        ],
        "series": [
            {
                "series_id": series_id,
                "series_name": group["series_name"],
                "devotionals_count": len(group["devotionals"]),
                "start_date": (lambda dates: min(dates).isoformat() if dates else None)([(d.get("scheduled_at") or d.get("published_at")) for d in group["devotionals"] if (d.get("scheduled_at") or d.get("published_at"))]),
                "end_date": (lambda dates: max(dates).isoformat() if dates else None)([(d.get("scheduled_at") or d.get("published_at")) for d in group["devotionals"] if (d.get("scheduled_at") or d.get("published_at"))]),
            }
            for series_id, group in series_groups.items()
            if len(group["devotionals"]) >= 2  # Only include series with 2+ devotionals
        ]
    }

    return result


@router.get("/stats")
async def get_calendar_stats(
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get calendar statistics.

    Requires admin role.

    Returns:
        Calendar statistics including scheduled, published, and draft counts
    """
    from app.db.mongodb import get_database
    from datetime import datetime, timedelta

    db = get_database()

    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    thirty_days_ahead = now + timedelta(days=30)

    # Get counts
    scheduled_next_30 = await db.devotionals.count_documents({
        "status": "scheduled",
        "scheduled_at": {"$gte": now, "$lte": thirty_days_ahead}
    })

    published_last_30 = await db.devotionals.count_documents({
        "status": "published",
        "published_at": {"$gte": thirty_days_ago, "$lte": now}
    })

    drafts = await db.devotionals.count_documents({"status": "draft"})

    # Calculate total published and statistics
    total_published = await db.devotionals.count_documents({"status": "published"})

    # This month count
    today = datetime.utcnow()
    month_start = datetime(today.year, today.month, 1)
    next_month_start = datetime(today.year + (1 if today.month == 12 else 0),
                                 (today.month % 12) + 1, 1)
    this_month = await db.devotionals.count_documents({
        "status": {"$in": ["published", "scheduled"]},
        "scheduled_at": {"$gte": month_start, "$lt": next_month_start}
    })

    # This week count
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)
    this_week = await db.devotionals.count_documents({
        "status": {"$in": ["published", "scheduled"]},
        "scheduled_at": {"$gte": week_start, "$lt": week_end}
    })

    # Today count
    day_start = datetime(today.year, today.month, today.day)
    day_end = day_start + timedelta(days=1)
    today_count = await db.devotionals.count_documents({
        "status": {"$in": ["published", "scheduled"]},
        "scheduled_at": {"$gte": day_start, "$lt": day_end}
    })

    # Calculate publishing streak
    # Get all published devotionals sorted by date
    published_devotionals = await db.devotionals.find(
        {"status": "published"}
    ).sort("published_at", -1).to_list(None)

    publishing_streak = 0
    current_date = datetime.utcnow().date()
    for dev in published_devotionals:
        pub_date = dev.get("published_at")
        if not pub_date:
            continue
        if isinstance(pub_date, datetime):
            pub_date = pub_date.date()

        # Check if there's a devotional for current_date
        if pub_date == current_date:
            publishing_streak += 1
            current_date -= timedelta(days=1)
        elif pub_date < current_date:
            # Gap found, break
            break

    return {
        "total_published": total_published,
        "this_month": this_month,
        "this_week": this_week,
        "today": today_count,
        "upcoming_scheduled": scheduled_next_30,
        "publishing_streak": publishing_streak,
        "scheduled_next_30_days": scheduled_next_30,
        "published_last_30_days": published_last_30,
        "drafts": drafts,
    }
