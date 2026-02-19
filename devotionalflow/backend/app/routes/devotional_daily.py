"""
Daily Devotional API routes.
Handles getting today's devotional and date-based access.
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime, date, timedelta
from app.models.devotional import DevotionalResponse
from app.db.mongodb import get_database
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_todays_devotional_impl():
    """
    Internal implementation for getting today's devotional.
    Shared by /today and /daily endpoints.
    """
    db = get_database()

    # Get today's date (start and end of day in UTC)
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())

    # Find devotional for today
    devotional_doc = await db.devotionals.find_one({
        "status": "published",
        "published_at": {
            "$gte": start_of_day,
            "$lte": end_of_day
        }
    })

    if not devotional_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No devotional scheduled for today ({today.isoformat()})"
        )

    # Increment view count
    await db.devotionals.update_one(
        {"_id": devotional_doc["_id"]},
        {"$inc": {"views_count": 1}}
    )

    # Convert to response model
    from app.services.devotional_service import devotional_dict_to_response
    return devotional_dict_to_response(devotional_doc)


@router.get("/daily", response_model=DevotionalResponse)
async def get_daily_devotional():
    """
    Get today's devotional (alias for /today endpoint).

    **Public Endpoint** - No authentication required.

    **Returns:**
    - Today's devotional if available
    - 404 if no devotional scheduled for today

    **Note:**
    - Alias for /today endpoint for better API discoverability
    - Returns devotional where published_at matches today's date
    - Timezone: UTC
    - Increments view count automatically
    """
    return await _get_todays_devotional_impl()


@router.get("/today", response_model=DevotionalResponse)
async def get_todays_devotional():
    """
    Get today's devotional based on current date.

    **Public Endpoint** - No authentication required.

    **Returns:**
    - Today's devotional if available
    - 404 if no devotional scheduled for today

    **Note:**
    - Returns devotional where published_at matches today's date
    - Timezone: UTC
    - Increments view count automatically
    """
    return await _get_todays_devotional_impl()


@router.get("/date/{date_str}", response_model=DevotionalResponse)
async def get_devotional_by_date(date_str: str):
    """
    Get devotional for a specific date.

    **Parameters:**
    - date_str: Date in YYYY-MM-DD format (e.g., "2026-01-15")

    **Returns:**
    - Devotional for the specified date
    - 404 if no devotional found for that date

    **Example:**
    - GET /api/v1/devotionals/date/2026-01-15
    """
    try:
        # Parse date string
        devotional_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

    db = get_database()

    # Get devotional for this date
    start_of_day = datetime.combine(devotional_date, datetime.min.time())
    end_of_day = datetime.combine(devotional_date, datetime.max.time())

    devotional_doc = await db.devotionals.find_one({
        "status": "published",
        "published_at": {
            "$gte": start_of_day,
            "$lte": end_of_day
        }
    })

    if not devotional_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No devotional found for {date_str}"
        )

    # Increment view count
    await db.devotionals.update_one(
        {"_id": devotional_doc["_id"]},
        {"$inc": {"views_count": 1}}
    )

    # Convert to response model
    from app.services.devotional_service import devotional_dict_to_response
    return devotional_dict_to_response(devotional_doc)


@router.get("/upcoming", response_model=list[DevotionalResponse])
async def get_upcoming_devotionals(days: int = 7):
    """
    Get upcoming devotionals for the next N days.

    **Query Parameters:**
    - days: Number of days to look ahead (default: 7, max: 30)

    **Returns:**
    - List of upcoming devotionals
    """
    if days > 30:
        days = 30

    db = get_database()

    # Get date range
    today = datetime.utcnow().date()
    end_date = today + timedelta(days=days)

    start_of_today = datetime.combine(today, datetime.min.time())
    end_of_range = datetime.combine(end_date, datetime.max.time())

    # Find devotionals in range
    cursor = db.devotionals.find({
        "status": "published",
        "published_at": {
            "$gte": start_of_today,
            "$lte": end_of_range
        }
    }).sort("published_at", 1).limit(days)

    devotionals = []
    async for devotional_doc in cursor:
        from app.services.devotional_service import devotional_dict_to_response
        devotionals.append(devotional_dict_to_response(devotional_doc))

    return devotionals


@router.get("/archive/{year}/{month}", response_model=list[DevotionalResponse])
async def get_devotionals_by_month(year: int, month: int):
    """
    Get all devotionals for a specific month.

    **Parameters:**
    - year: Year (e.g., 2026)
    - month: Month (1-12)

    **Returns:**
    - List of devotionals for that month

    **Example:**
    - GET /api/v1/devotionals/archive/2026/1 (January 2026)
    """
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12"
        )

    db = get_database()

    # Get date range for month
    first_day = datetime(year, month, 1)

    # Last day of month
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)

    # Find devotionals in month
    cursor = db.devotionals.find({
        "status": "published",
        "published_at": {
            "$gte": first_day,
            "$lte": datetime.combine(last_day.date(), datetime.max.time())
        }
    }).sort("published_at", 1)

    devotionals = []
    async for devotional_doc in cursor:
        from app.services.devotional_service import devotional_dict_to_response
        devotionals.append(devotional_dict_to_response(devotional_doc))

    return devotionals
