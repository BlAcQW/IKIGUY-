"""
Conference session request/response schemas.

This module defines Pydantic schemas for conference session API
requests and responses.
"""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator


class SessionResponse(BaseModel):
    """
    Conference session response schema.

    Returns:
        Session details with all fields
    """

    id: str = Field(..., description="Session ID")
    conference_id: str = Field(..., description="Parent conference ID")
    name: str = Field(..., description="Session name")
    description: Optional[str] = Field(None, description="Session description")
    location: Optional[str] = Field(None, description="Session location/room")
    day_number: int = Field(..., description="Day number (1, 2, 3...)")
    day_label: str = Field(..., description="Day label (e.g., 'Day 1')")
    session_date: datetime = Field(..., description="Session date")
    start_time: Optional[str] = Field(None, description="Session start time (HH:MM format)")
    end_time: Optional[str] = Field(None, description="Session end time (HH:MM format)")
    order: int = Field(..., description="Display order within day")
    sms_confirmation_enabled: bool = Field(False, description="Whether SMS confirmation is enabled for check-ins")
    sms_confirmation_template: Optional[str] = Field(None, description="SMS template for check-in confirmations")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    attendance_count: Optional[int] = Field(None, description="Number of attendees checked in")


class CreateSessionRequest(BaseModel):
    """
    Request schema for creating a conference session.

    Args:
        name: Session name (required)
        description: Session description (optional)
        location: Session location/room (optional)
        day_number: Day number within conference (required)
        day_label: Custom day label (required)
        session_date: Specific date for session (required)
        order: Display order within day (optional, default 0)
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Session name"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Session description"
    )
    location: Optional[str] = Field(
        None,
        max_length=200,
        description="Session location/room"
    )
    day_number: int = Field(
        ...,
        ge=1,
        description="Day number (1, 2, 3...)"
    )
    day_label: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Day label (e.g., 'Day 1', 'Opening Day')"
    )
    session_date: datetime = Field(
        ...,
        description="Session date (must be within conference dates)"
    )
    start_time: Optional[str] = Field(
        None,
        description="Session start time in HH:MM format (e.g., '09:00')"
    )
    end_time: Optional[str] = Field(
        None,
        description="Session end time in HH:MM format (e.g., '10:00')"
    )
    order: int = Field(
        default=0,
        ge=0,
        description="Display order within the day"
    )
    sms_confirmation_enabled: bool = Field(
        default=False,
        description="Whether to send SMS confirmations on check-in"
    )
    sms_confirmation_template: Optional[str] = Field(
        None,
        max_length=160,
        description="SMS template for check-in confirmations"
    )


class UpdateSessionRequest(BaseModel):
    """
    Request schema for updating a conference session.

    All fields are optional for partial updates.

    Args:
        name: Session name
        description: Session description
        location: Session location/room
        day_number: Day number within conference
        day_label: Custom day label
        session_date: Specific date for session
        order: Display order within day
    """

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Session name"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Session description"
    )
    location: Optional[str] = Field(
        None,
        max_length=200,
        description="Session location/room"
    )
    day_number: Optional[int] = Field(
        None,
        ge=1,
        description="Day number (1, 2, 3...)"
    )
    day_label: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Day label (e.g., 'Day 1', 'Opening Day')"
    )
    session_date: Optional[datetime] = Field(
        None,
        description="Session date (must be within conference dates)"
    )
    start_time: Optional[str] = Field(
        None,
        description="Session start time in HH:MM format (e.g., '09:00')"
    )
    end_time: Optional[str] = Field(
        None,
        description="Session end time in HH:MM format (e.g., '10:00')"
    )
    order: Optional[int] = Field(
        None,
        ge=0,
        description="Display order within the day"
    )
    sms_confirmation_enabled: Optional[bool] = Field(
        None,
        description="Whether to send SMS confirmations on check-in"
    )
    sms_confirmation_template: Optional[str] = Field(
        None,
        max_length=160,
        description="SMS template for check-in confirmations"
    )


class SessionListResponse(BaseModel):
    """
    Response schema for listing sessions.

    Returns:
        List of sessions with pagination info
    """

    sessions: List[SessionResponse] = Field(
        ...,
        description="List of sessions"
    )
    total: int = Field(..., description="Total number of sessions")
    conference_id: str = Field(..., description="Parent conference ID")


class SessionsByDayResponse(BaseModel):
    """
    Response schema for sessions grouped by day.

    Returns:
        Sessions organized by day number for easy display
    """

    conference_id: str = Field(..., description="Parent conference ID")
    sessions_by_day: Dict[str, List[SessionResponse]] = Field(
        ...,
        description="Sessions grouped by day number (key: day_number as string)"
    )
    total_days: int = Field(..., description="Total number of days")
    total_sessions: int = Field(..., description="Total number of sessions")


class ConferenceDayInfo(BaseModel):
    """
    Conference day information schema.

    Represents a single day within a conference with helper fields.
    """

    day_number: int = Field(..., description="Day number (1, 2, 3...)")
    day_label: str = Field(..., description="Suggested day label")
    date: str = Field(..., description="Date in ISO format (YYYY-MM-DD)")
    date_display: str = Field(..., description="Human-readable date (e.g., 'November 15, 2025')")


class ConferenceDaysResponse(BaseModel):
    """
    Response schema for conference days.

    Returns:
        List of all days within the conference date range
    """

    conference_id: str = Field(..., description="Conference ID")
    days: List[ConferenceDayInfo] = Field(..., description="List of conference days")
    total_days: int = Field(..., description="Total number of days")
