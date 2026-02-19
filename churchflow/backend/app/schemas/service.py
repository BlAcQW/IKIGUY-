"""
Church service request/response schemas.

This module defines Pydantic schemas for church service API
requests and responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ServiceResponse(BaseModel):
    """
    Service response schema.

    Returns:
        Service details with all fields
    """

    id: str = Field(..., description="Service ID")
    service_type: str = Field(..., description="Type of service")
    branch_id: str = Field(..., description="Branch ID")
    organization_id: str = Field(..., description="Organization ID")

    sermon_title: Optional[str] = Field(None, description="Sermon title")
    series_name: Optional[str] = Field(None, description="Sermon series name")
    scripture_reference: Optional[str] = Field(None, description="Bible passage reference")
    speaker: Optional[str] = Field(None, description="Speaker/preacher name")

    sermon_recording_url: Optional[str] = Field(None, description="Recording URL")
    sermon_notes_url: Optional[str] = Field(None, description="Sermon notes URL")
    livestream_link: Optional[str] = Field(None, description="Livestream URL")

    service_date: datetime = Field(..., description="Service date")
    start_time: str = Field(..., description="Start time (HH:MM)")
    end_time: str = Field(..., description="End time (HH:MM)")

    status: str = Field(..., description="Service status")
    expected_attendance: Optional[int] = Field(None, description="Expected attendance")
    actual_attendance: int = Field(0, description="Actual attendance from check-ins")

    qr_code: Optional[str] = Field(None, description="QR code for check-in")
    venue_checkin_radius: int = Field(1000, description="Check-in radius in meters")

    is_recurring: bool = Field(False, description="Is part of recurring series")
    recurrence_rule: Optional[Dict[str, Any]] = Field(None, description="Recurrence pattern")

    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")


class CreateServiceRequest(BaseModel):
    """
    Request schema for creating a service.

    Args:
        service_type: Type of service (required)
        branch_id: Branch ID (required)
        organization_id: Organization ID (required)
        sermon_title: Sermon title (optional)
        series_name: Sermon series name (optional)
        scripture_reference: Bible passage (optional)
        speaker: Speaker name (optional)
        sermon_recording_url: Recording URL (optional)
        sermon_notes_url: Notes URL (optional)
        livestream_link: Livestream URL (optional)
        service_date: Service date (required)
        start_time: Start time in HH:MM (required)
        end_time: End time in HH:MM (required)
        status: Service status (optional, default: "upcoming")
        expected_attendance: Expected number of attendees (optional)
    """

    service_type: str = Field(
        ...,
        pattern="^(sunday_8am|sunday_10am|midweek|special)$",
        description="Type of service"
    )
    branch_id: str = Field(..., description="Branch ID")
    organization_id: str = Field(..., description="Organization ID")

    sermon_title: Optional[str] = Field(
        None,
        max_length=300,
        description="Sermon title"
    )
    series_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Sermon series name"
    )
    scripture_reference: Optional[str] = Field(
        None,
        max_length=200,
        description="Bible passage reference"
    )
    speaker: Optional[str] = Field(
        None,
        max_length=200,
        description="Speaker/preacher name"
    )

    sermon_recording_url: Optional[str] = Field(None, description="Recording URL")
    sermon_notes_url: Optional[str] = Field(None, description="Sermon notes URL")
    livestream_link: Optional[str] = Field(None, description="Livestream URL")

    service_date: datetime = Field(..., description="Service date")
    start_time: str = Field(
        ...,
        pattern="^([01]\\d|2[0-3]):([0-5]\\d)$",
        description="Start time in HH:MM format"
    )
    end_time: str = Field(
        ...,
        pattern="^([01]\\d|2[0-3]):([0-5]\\d)$",
        description="End time in HH:MM format"
    )

    status: str = Field(
        default="upcoming",
        pattern="^(upcoming|ongoing|completed|cancelled)$",
        description="Service status"
    )
    expected_attendance: Optional[int] = Field(
        None,
        ge=0,
        description="Expected attendance"
    )
    venue_checkin_radius: int = Field(
        default=1000,
        ge=50,
        le=5000,
        description="Check-in radius in meters"
    )


class UpdateServiceRequest(BaseModel):
    """
    Request schema for updating a service.

    All fields are optional for partial updates.
    """

    sermon_title: Optional[str] = Field(
        None,
        max_length=300,
        description="Sermon title"
    )
    series_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Sermon series name"
    )
    scripture_reference: Optional[str] = Field(
        None,
        max_length=200,
        description="Bible passage reference"
    )
    speaker: Optional[str] = Field(
        None,
        max_length=200,
        description="Speaker/preacher name"
    )

    sermon_recording_url: Optional[str] = Field(None, description="Recording URL")
    sermon_notes_url: Optional[str] = Field(None, description="Sermon notes URL")
    livestream_link: Optional[str] = Field(None, description="Livestream URL")

    service_date: Optional[datetime] = Field(None, description="Service date")
    start_time: Optional[str] = Field(
        None,
        pattern="^([01]\\d|2[0-3]):([0-5]\\d)$",
        description="Start time in HH:MM format"
    )
    end_time: Optional[str] = Field(
        None,
        pattern="^([01]\\d|2[0-3]):([0-5]\\d)$",
        description="End time in HH:MM format"
    )

    status: Optional[str] = Field(
        None,
        pattern="^(upcoming|ongoing|completed|cancelled)$",
        description="Service status"
    )
    expected_attendance: Optional[int] = Field(
        None,
        ge=0,
        description="Expected attendance"
    )
    venue_checkin_radius: Optional[int] = Field(
        None,
        ge=50,
        le=5000,
        description="Check-in radius in meters"
    )


class GenerateRecurringServicesRequest(BaseModel):
    """
    Request schema for generating recurring services.

    Args:
        branch_id: Branch ID (required)
        organization_id: Organization ID (required)
        weeks_ahead: Number of weeks to generate (default: 8)
    """

    branch_id: str = Field(..., description="Branch ID")
    organization_id: str = Field(..., description="Organization ID")
    weeks_ahead: int = Field(
        default=8,
        ge=1,
        le=52,
        description="Number of weeks to generate ahead"
    )


class GenerateRecurringServicesResponse(BaseModel):
    """
    Response schema for recurring service generation.

    Returns:
        Statistics about generated services
    """

    success: bool = Field(..., description="Whether generation succeeded")
    message: str = Field(..., description="Result message")
    stats: Dict[str, int] = Field(..., description="Generation statistics by type")


class ServiceListResponse(BaseModel):
    """
    Response schema for listing services.

    Returns:
        List of services with total count
    """

    services: List[ServiceResponse] = Field(..., description="List of services")
    total: int = Field(..., description="Total number of services")


class ServiceAttendanceSummary(BaseModel):
    """
    Service attendance summary schema.

    Returns:
        Attendance statistics for a service
    """

    service_id: str = Field(..., description="Service ID")
    total_attendees: int = Field(0, description="Total attendees")
    members: int = Field(0, description="Number of members")
    visitors: int = Field(0, description="Number of visitors")
    first_timers: int = Field(0, description="Number of first-timers")


class AttendeeInfo(BaseModel):
    """
    Individual attendee information.

    Returns:
        Details about a single attendee
    """

    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="Attendee name")
    phone: Optional[str] = Field(None, description="Phone number")
    member_status: str = Field(..., description="Member status")
    current_spiritual_stage: Optional[str] = Field(None, description="Spiritual stage")
    checked_in_at: datetime = Field(..., description="Check-in timestamp")
    check_in_method: str = Field(..., description="Check-in method")


class ServiceAttendanceDetailResponse(BaseModel):
    """
    Detailed service attendance response.

    Returns:
        Summary stats and full attendee list
    """

    service_id: str = Field(..., description="Service ID")
    summary: ServiceAttendanceSummary = Field(..., description="Summary statistics")
    attendees: List[AttendeeInfo] = Field(..., description="List of attendees")
