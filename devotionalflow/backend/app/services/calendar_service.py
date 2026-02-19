"""
Calendar service for devotional scheduling and planning.
"""

from typing import List, Dict, Any
from datetime import datetime, date, timedelta
from calendar import monthrange
from bson import ObjectId
from app.db.mongodb import get_database
from app.models.calendar import (
    CalendarEvent,
    CalendarDayView,
    CalendarMonthView,
    CalendarWeekView,
    ScheduleSlot,
    BulkScheduleRequest,
    BulkScheduleResponse,
)


class CalendarService:
    """Service for calendar and scheduling operations."""

    def __init__(self):
        self.db = get_database()
        self.devotionals_collection = self.db.devotionals
        self.likes_collection = self.db.likes
        self.comments_collection = self.db.comments

    async def get_month_view(
        self, author_id: str, year: int, month: int, status_filter: str = None
    ) -> CalendarMonthView:
        """
        Get monthly calendar view for author's devotionals.

        Args:
            author_id: ID of the author
            year: Year (e.g., 2025)
            month: Month (1-12)
            status_filter: Optional status filter

        Returns:
            CalendarMonthView: Monthly calendar with devotionals
        """
        # Get first and last day of month
        first_day = date(year, month, 1)
        _, last_day_num = monthrange(year, month)
        last_day = date(year, month, last_day_num)

        # Build query
        query = {"author_id": author_id}

        if status_filter:
            query["status"] = status_filter

        # Query devotionals for the month
        # Match by published_at for published, scheduled_for for scheduled, created_at for draft
        query["$or"] = [
            {
                "status": "published",
                "published_at": {
                    "$gte": datetime.combine(first_day, datetime.min.time()),
                    "$lte": datetime.combine(last_day, datetime.max.time()),
                },
            },
            {
                "status": "scheduled",
                "scheduled_for": {
                    "$gte": datetime.combine(first_day, datetime.min.time()),
                    "$lte": datetime.combine(last_day, datetime.max.time()),
                },
            },
        ]

        devotionals = await self.devotionals_collection.find(query).to_list(length=None)

        # Group devotionals by date
        days_dict = {}
        total_published = 0
        total_scheduled = 0
        total_draft = 0

        for devotional in devotionals:
            # Determine the date for this devotional
            if devotional.get("status") == "published" and devotional.get("published_at"):
                devotional_date = devotional["published_at"].date()
            elif devotional.get("status") == "scheduled" and devotional.get("scheduled_for"):
                devotional_date = devotional["scheduled_for"].date()
            else:
                continue  # Skip drafts for now

            # Count by status
            if devotional.get("status") == "published":
                total_published += 1
            elif devotional.get("status") == "scheduled":
                total_scheduled += 1
            elif devotional.get("status") == "draft":
                total_draft += 1

            # Get engagement metrics
            devotional_id = str(devotional["_id"])
            likes_count = await self.likes_collection.count_documents(
                {"devotional_id": devotional_id}
            )
            comments_count = await self.comments_collection.count_documents(
                {"devotional_id": devotional_id}
            )

            # Create calendar event
            event = CalendarEvent(
                id=devotional_id,
                title=devotional.get("title", "Untitled"),
                date=devotional_date,
                status=devotional.get("status", "draft"),
                category=devotional.get("category"),
                views=devotional.get("views_count", 0),
                likes=likes_count,
                comments=comments_count,
            )

            # Add to day
            if devotional_date not in days_dict:
                days_dict[devotional_date] = []
            days_dict[devotional_date].append(event)

        # Build days list (all days in month)
        days = []
        current_date = first_day
        while current_date <= last_day:
            day_devotionals = days_dict.get(current_date, [])
            days.append(
                CalendarDayView(
                    date=current_date,
                    devotionals=day_devotionals,
                    total_devotionals=len(day_devotionals),
                )
            )
            current_date += timedelta(days=1)

        return CalendarMonthView(
            year=year,
            month=month,
            days=days,
            total_devotionals=len(devotionals),
            published_count=total_published,
            scheduled_count=total_scheduled,
            draft_count=total_draft,
        )

    async def get_week_view(
        self, author_id: str, week_start: date, status_filter: str = None
    ) -> CalendarWeekView:
        """
        Get weekly calendar view for author's devotionals.

        Args:
            author_id: ID of the author
            week_start: Start date of the week (Monday)
            status_filter: Optional status filter

        Returns:
            CalendarWeekView: Weekly calendar with devotionals
        """
        week_end = week_start + timedelta(days=6)

        # Build query
        query = {"author_id": author_id}

        if status_filter:
            query["status"] = status_filter

        # Query devotionals for the week
        query["$or"] = [
            {
                "status": "published",
                "published_at": {
                    "$gte": datetime.combine(week_start, datetime.min.time()),
                    "$lte": datetime.combine(week_end, datetime.max.time()),
                },
            },
            {
                "status": "scheduled",
                "scheduled_for": {
                    "$gte": datetime.combine(week_start, datetime.min.time()),
                    "$lte": datetime.combine(week_end, datetime.max.time()),
                },
            },
        ]

        devotionals = await self.devotionals_collection.find(query).to_list(length=None)

        # Group devotionals by date
        days_dict = {}
        total_published = 0
        total_scheduled = 0
        total_draft = 0

        for devotional in devotionals:
            # Determine the date
            if devotional.get("status") == "published" and devotional.get("published_at"):
                devotional_date = devotional["published_at"].date()
            elif devotional.get("status") == "scheduled" and devotional.get("scheduled_for"):
                devotional_date = devotional["scheduled_for"].date()
            else:
                continue

            # Count by status
            if devotional.get("status") == "published":
                total_published += 1
            elif devotional.get("status") == "scheduled":
                total_scheduled += 1
            elif devotional.get("status") == "draft":
                total_draft += 1

            # Get engagement metrics
            devotional_id = str(devotional["_id"])
            likes_count = await self.likes_collection.count_documents(
                {"devotional_id": devotional_id}
            )
            comments_count = await self.comments_collection.count_documents(
                {"devotional_id": devotional_id}
            )

            # Create calendar event
            event = CalendarEvent(
                id=devotional_id,
                title=devotional.get("title", "Untitled"),
                date=devotional_date,
                status=devotional.get("status", "draft"),
                category=devotional.get("category"),
                views=devotional.get("views_count", 0),
                likes=likes_count,
                comments=comments_count,
            )

            # Add to day
            if devotional_date not in days_dict:
                days_dict[devotional_date] = []
            days_dict[devotional_date].append(event)

        # Build days list (7 days)
        days = []
        current_date = week_start
        for _ in range(7):
            day_devotionals = days_dict.get(current_date, [])
            days.append(
                CalendarDayView(
                    date=current_date,
                    devotionals=day_devotionals,
                    total_devotionals=len(day_devotionals),
                )
            )
            current_date += timedelta(days=1)

        return CalendarWeekView(
            week_start=week_start,
            week_end=week_end,
            days=days,
            total_devotionals=len(devotionals),
            published_count=total_published,
            scheduled_count=total_scheduled,
            draft_count=total_draft,
        )

    async def get_available_slots(
        self, author_id: str, start_date: date, days: int = 30
    ) -> List[ScheduleSlot]:
        """
        Get available schedule slots for an author.

        Args:
            author_id: ID of the author
            start_date: Start date for checking slots
            days: Number of days to check (default: 30)

        Returns:
            List of schedule slots
        """
        end_date = start_date + timedelta(days=days - 1)

        # Get scheduled and published devotionals in range
        query = {
            "author_id": author_id,
            "$or": [
                {
                    "status": "published",
                    "published_at": {
                        "$gte": datetime.combine(start_date, datetime.min.time()),
                        "$lte": datetime.combine(end_date, datetime.max.time()),
                    },
                },
                {
                    "status": "scheduled",
                    "scheduled_for": {
                        "$gte": datetime.combine(start_date, datetime.min.time()),
                        "$lte": datetime.combine(end_date, datetime.max.time()),
                    },
                },
            ],
        }

        devotionals = await self.devotionals_collection.find(query).to_list(length=None)

        # Build date -> devotional map
        occupied_dates = {}
        for devotional in devotionals:
            if devotional.get("status") == "published" and devotional.get("published_at"):
                devotional_date = devotional["published_at"].date()
            elif devotional.get("status") == "scheduled" and devotional.get("scheduled_for"):
                devotional_date = devotional["scheduled_for"].date()
            else:
                continue

            occupied_dates[devotional_date] = {
                "id": str(devotional["_id"]),
                "title": devotional.get("title", "Untitled"),
            }

        # Build slots list
        slots = []
        current_date = start_date
        for _ in range(days):
            if current_date in occupied_dates:
                slots.append(
                    ScheduleSlot(
                        date=current_date,
                        is_available=False,
                        devotional_id=occupied_dates[current_date]["id"],
                        devotional_title=occupied_dates[current_date]["title"],
                    )
                )
            else:
                slots.append(ScheduleSlot(date=current_date, is_available=True))

            current_date += timedelta(days=1)

        return slots

    async def bulk_schedule(
        self, author_id: str, request: BulkScheduleRequest
    ) -> BulkScheduleResponse:
        """
        Bulk schedule multiple devotionals.

        Args:
            author_id: ID of the author
            request: Bulk schedule request

        Returns:
            BulkScheduleResponse: Results of bulk scheduling
        """
        scheduled_count = 0
        skipped_count = 0
        failed_count = 0
        schedule_details = []

        current_date = request.start_date

        for devotional_id in request.devotional_ids:
            # Find next available date
            while True:
                # Skip weekends if requested
                if request.skip_weekends and current_date.weekday() >= 5:  # Saturday=5, Sunday=6
                    current_date += timedelta(days=1)
                    continue

                # Check if date is available (if skip_existing is True)
                if request.skip_existing:
                    existing = await self.devotionals_collection.find_one(
                        {
                            "author_id": author_id,
                            "$or": [
                                {
                                    "status": "published",
                                    "published_at": {
                                        "$gte": datetime.combine(current_date, datetime.min.time()),
                                        "$lte": datetime.combine(current_date, datetime.max.time()),
                                    },
                                },
                                {
                                    "status": "scheduled",
                                    "scheduled_for": {
                                        "$gte": datetime.combine(current_date, datetime.min.time()),
                                        "$lte": datetime.combine(current_date, datetime.max.time()),
                                    },
                                },
                            ],
                        }
                    )

                    if existing:
                        current_date += timedelta(days=1)
                        continue

                # Date is available
                break

            # Schedule the devotional
            try:
                result = await self.devotionals_collection.update_one(
                    {"_id": ObjectId(devotional_id), "author_id": author_id},
                    {
                        "$set": {
                            "status": "scheduled",
                            "scheduled_for": datetime.combine(current_date, datetime.min.time()),
                            "updated_at": datetime.utcnow(),
                        }
                    },
                )

                if result.modified_count > 0:
                    scheduled_count += 1
                    schedule_details.append(
                        {
                            "devotional_id": devotional_id,
                            "scheduled_date": current_date.isoformat(),
                            "status": "scheduled",
                        }
                    )
                else:
                    failed_count += 1
                    schedule_details.append(
                        {
                            "devotional_id": devotional_id,
                            "status": "failed",
                            "reason": "Devotional not found or not owned by author",
                        }
                    )

            except Exception as e:
                failed_count += 1
                schedule_details.append(
                    {"devotional_id": devotional_id, "status": "failed", "reason": str(e)}
                )

            # Move to next date based on frequency
            if request.frequency == "daily":
                current_date += timedelta(days=1)
            elif request.frequency == "weekly":
                current_date += timedelta(weeks=1)
            elif request.frequency == "biweekly":
                current_date += timedelta(weeks=2)
            elif request.frequency == "monthly":
                # Add one month (handle month overflow)
                if current_date.month == 12:
                    current_date = date(current_date.year + 1, 1, current_date.day)
                else:
                    try:
                        current_date = date(
                            current_date.year, current_date.month + 1, current_date.day
                        )
                    except ValueError:
                        # Day doesn't exist in next month (e.g., Jan 31 -> Feb 31)
                        # Use last day of next month
                        if current_date.month == 12:
                            next_month = 1
                            next_year = current_date.year + 1
                        else:
                            next_month = current_date.month + 1
                            next_year = current_date.year
                        _, last_day = monthrange(next_year, next_month)
                        current_date = date(next_year, next_month, last_day)

        return BulkScheduleResponse(
            success=failed_count == 0,
            scheduled_count=scheduled_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            schedule_details=schedule_details,
        )
