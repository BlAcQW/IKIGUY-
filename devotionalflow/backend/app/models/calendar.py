"""
Calendar models for devotional scheduling and planning.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime, date


class CalendarEvent(BaseModel):
    """Model for a calendar event (devotional)."""

    id: str
    title: str
    date: date  # The date this devotional is scheduled/published
    status: Literal["published", "scheduled", "draft"]
    category: Optional[str] = None

    # Engagement metrics (for published devotionals)
    views: int = 0
    likes: int = 0
    comments: int = 0

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }


class CalendarDayView(BaseModel):
    """Model for a single day in the calendar."""

    date: date
    devotionals: List[CalendarEvent]
    total_devotionals: int

    class Config:
        json_encoders = {date: lambda v: v.isoformat()}


class CalendarMonthView(BaseModel):
    """Model for monthly calendar view."""

    year: int
    month: int  # 1-12
    days: List[CalendarDayView]

    # Monthly stats
    total_devotionals: int
    published_count: int
    scheduled_count: int
    draft_count: int

    class Config:
        json_encoders = {date: lambda v: v.isoformat()}


class CalendarWeekView(BaseModel):
    """Model for weekly calendar view."""

    week_start: date
    week_end: date
    days: List[CalendarDayView]

    # Weekly stats
    total_devotionals: int
    published_count: int
    scheduled_count: int
    draft_count: int

    class Config:
        json_encoders = {date: lambda v: v.isoformat()}


class ScheduleSlot(BaseModel):
    """Model for available/unavailable schedule slots."""

    date: date
    is_available: bool
    devotional_id: Optional[str] = None
    devotional_title: Optional[str] = None

    class Config:
        json_encoders = {date: lambda v: v.isoformat()}


class BulkScheduleRequest(BaseModel):
    """Model for bulk scheduling devotionals."""

    devotional_ids: List[str] = Field(..., min_items=1)
    start_date: date
    frequency: Literal["daily", "weekly", "biweekly", "monthly"] = "daily"
    skip_weekends: bool = False
    skip_existing: bool = True  # Skip dates that already have devotionals


class BulkScheduleResponse(BaseModel):
    """Response model for bulk scheduling."""

    success: bool
    scheduled_count: int
    skipped_count: int
    failed_count: int
    schedule_details: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class CalendarFilters(BaseModel):
    """Query parameters for calendar views."""

    year: int = Field(..., ge=2020, le=2100)
    month: Optional[int] = Field(None, ge=1, le=12)
    week: Optional[int] = Field(None, ge=1, le=53)
    status: Optional[Literal["published", "scheduled", "draft"]] = None
    category: Optional[str] = None
