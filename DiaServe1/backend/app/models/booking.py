"""
Booking Data Models

Handles property tour bookings, viewing appointments, and calendar management.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class BookingType(str, Enum):
    """Type of property viewing"""
    IN_PERSON = "in-person"
    VIRTUAL = "virtual"


class BookingStatus(str, Enum):
    """Booking lifecycle status"""
    REQUESTED = "requested"  # Initial booking request
    CONFIRMED = "confirmed"  # Agent confirmed
    RESCHEDULED = "rescheduled"  # Date/time changed
    COMPLETED = "completed"  # Tour completed
    CANCELLED = "cancelled"  # Cancelled by either party
    NO_SHOW = "no-show"  # Customer didn't show up


class ReminderStatus(str, Enum):
    """Reminder sending status"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Reminder(BaseModel):
    """Automated booking reminder"""
    type: str = Field(..., description="Reminder type: 24h, 1h, post-tour")
    scheduled_at: datetime = Field(..., description="When to send reminder")
    sent_at: Optional[datetime] = Field(None, description="When reminder was sent")
    status: ReminderStatus = Field(ReminderStatus.PENDING, description="Reminder status")
    channel: str = Field(..., description="Notification channel: email, sms, whatsapp")
    message_id: Optional[str] = Field(None, description="External message ID if sent")


class Booking(BaseModel):
    """Property viewing booking"""
    id: str = Field(..., description="Unique booking ID")
    organization_id: str = Field(..., description="Organization ID")
    property_id: str = Field(..., description="Property being viewed")
    property_name: Optional[str] = Field(None, description="Resolved property name (populated at read time)")
    contact_id: str = Field(..., description="Contact/lead who booked")
    agent_id: Optional[str] = Field(None, description="Assigned agent ID")

    # Scheduling
    scheduled_at: datetime = Field(..., description="Tour date and time")
    duration_minutes: int = Field(default=30, description="Tour duration in minutes")
    booking_type: BookingType = Field(default=BookingType.IN_PERSON, description="Tour type")

    # Status
    status: BookingStatus = Field(default=BookingStatus.REQUESTED, description="Booking status")

    # Contact information (in case contact not in system)
    contact_name: str = Field(..., description="Contact name")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")

    # Additional info
    notes: Optional[str] = Field(None, description="Special requests or notes")
    internal_notes: Optional[str] = Field(None, description="Internal agent notes")

    # Virtual tour details
    meeting_link: Optional[str] = Field(None, description="Virtual meeting link (Zoom, Google Meet)")
    meeting_id: Optional[str] = Field(None, description="Virtual meeting ID")
    meeting_password: Optional[str] = Field(None, description="Virtual meeting password")

    # Reminders
    reminders: List[Reminder] = Field(default_factory=list, description="Scheduled reminders")

    # Feedback
    rating: Optional[int] = Field(None, ge=1, le=5, description="Customer rating (1-5)")
    feedback: Optional[str] = Field(None, description="Customer feedback after tour")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Created timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Updated timestamp")
    confirmed_at: Optional[datetime] = Field(None, description="When booking was confirmed")
    completed_at: Optional[datetime] = Field(None, description="When tour was completed")
    cancelled_at: Optional[datetime] = Field(None, description="When booking was cancelled")

    # Admin audit trail
    admin_override: Optional[bool] = Field(default=False, description="Whether admin overrode availability")
    admin_override_reason: Optional[str] = Field(None, description="Reason for availability override")
    reassigned_by: Optional[str] = Field(None, description="Admin email who reassigned agent")
    reassigned_at: Optional[datetime] = Field(None, description="When agent was reassigned")
    manually_created_by: Optional[str] = Field(None, description="Admin email who manually created booking")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "booking_abc123",
                "organization_id": "org_xyz789",
                "property_id": "prop_123",
                "contact_id": "contact_456",
                "agent_id": "agent_789",
                "scheduled_at": "2025-12-10T14:00:00Z",
                "duration_minutes": 30,
                "booking_type": "in-person",
                "status": "confirmed",
                "contact_name": "John Doe",
                "contact_email": "john@example.com",
                "contact_phone": "+233244123456",
                "notes": "Interested in the master bedroom size",
                "created_at": "2025-12-07T10:00:00Z",
                "updated_at": "2025-12-07T10:00:00Z"
            }
        }


class BookingCreate(BaseModel):
    """Create booking request"""
    property_id: str = Field(..., description="Property to view")
    contact_id: Optional[str] = Field(None, description="Contact ID if exists in system")
    scheduled_at: datetime = Field(..., description="Requested date and time")
    duration_minutes: int = Field(default=30, ge=15, le=180, description="Duration (15-180 minutes)")
    booking_type: BookingType = Field(default=BookingType.IN_PERSON, description="Tour type")

    # Required if contact_id not provided
    contact_name: str = Field(..., description="Contact name")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")

    notes: Optional[str] = Field(None, description="Special requests")

    class Config:
        json_schema_extra = {
            "example": {
                "property_id": "prop_123",
                "scheduled_at": "2025-12-10T14:00:00Z",
                "duration_minutes": 30,
                "booking_type": "in-person",
                "contact_name": "John Doe",
                "contact_email": "john@example.com",
                "contact_phone": "+233244123456",
                "notes": "Would like to see the backyard"
            }
        }


class BookingUpdate(BaseModel):
    """Update booking"""
    scheduled_at: Optional[datetime] = Field(None, description="Reschedule to new time")
    duration_minutes: Optional[int] = Field(None, ge=15, le=180, description="Update duration")
    status: Optional[BookingStatus] = Field(None, description="Update status")
    agent_id: Optional[str] = Field(None, description="Reassign agent")
    notes: Optional[str] = Field(None, description="Update notes")
    internal_notes: Optional[str] = Field(None, description="Update internal notes")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Customer rating")
    feedback: Optional[str] = Field(None, description="Customer feedback")
    meeting_link: Optional[str] = Field(None, description="Virtual meeting link")


class AvailabilitySlot(BaseModel):
    """Available time slot for booking"""
    start_time: datetime = Field(..., description="Slot start time")
    end_time: datetime = Field(..., description="Slot end time")
    available: bool = Field(..., description="Whether slot is available")
    agent_id: Optional[str] = Field(None, description="Available agent ID")
    reason: Optional[str] = Field(None, description="Why unavailable (if applicable)")


class AvailabilityRequest(BaseModel):
    """Request for available booking slots"""
    property_id: str = Field(..., description="Property ID")
    start_date: datetime = Field(..., description="Start of date range")
    end_date: datetime = Field(..., description="End of date range")
    duration_minutes: int = Field(default=30, description="Desired duration")


class AvailabilityResponse(BaseModel):
    """Available time slots response"""
    property_id: str = Field(..., description="Property ID")
    slots: List[AvailabilitySlot] = Field(..., description="Available slots")


class BookingListResponse(BaseModel):
    """Paginated booking list"""
    bookings: List[Booking] = Field(..., description="List of bookings")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Page offset")


class AgentAvailability(BaseModel):
    """Agent working hours and availability settings"""
    agent_id: str = Field(..., description="Agent ID")
    organization_id: str = Field(..., description="Organization ID")

    # Working hours (per day of week)
    monday: Optional[dict] = Field(None, description="{'start': '09:00', 'end': '17:00'}")
    tuesday: Optional[dict] = Field(None, description="Working hours")
    wednesday: Optional[dict] = Field(None, description="Working hours")
    thursday: Optional[dict] = Field(None, description="Working hours")
    friday: Optional[dict] = Field(None, description="Working hours")
    saturday: Optional[dict] = Field(None, description="Working hours")
    sunday: Optional[dict] = Field(None, description="Working hours")

    # Time zone
    timezone: str = Field(default="UTC", description="Agent timezone")

    # Buffer between bookings
    buffer_minutes: int = Field(default=15, description="Buffer time between bookings")

    # Maximum bookings per day
    max_bookings_per_day: int = Field(default=10, description="Max daily bookings")

    # Calendar sync
    google_calendar_id: Optional[str] = Field(None, description="Google Calendar ID")
    outlook_calendar_id: Optional[str] = Field(None, description="Outlook Calendar ID")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WaitlistEntry(BaseModel):
    """Waitlist for fully booked properties"""
    id: str = Field(..., description="Waitlist entry ID")
    property_id: str = Field(..., description="Property ID")
    contact_id: Optional[str] = Field(None, description="Contact ID")
    contact_name: str = Field(..., description="Contact name")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")
    preferred_dates: List[datetime] = Field(..., description="Preferred viewing dates")
    notified: bool = Field(default=False, description="Whether notified of opening")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== Admin Booking Management Models ====================


class BookingActionLog(BaseModel):
    """Audit trail for admin actions on bookings"""
    id: str = Field(..., description="Log entry ID")
    booking_id: str = Field(..., description="Related booking ID")
    organization_id: str = Field(..., description="Organization ID")
    action_type: str = Field(..., description="Action type: bulk_approve, bulk_reject, bulk_cancel, override_availability, reassign_agent, manual_create")
    admin_email: str = Field(..., description="Email of admin who performed action")
    admin_id: str = Field(..., description="ID of admin who performed action")
    details: Dict[str, Any] = Field(default_factory=dict, description="Action-specific details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When action occurred")


class BulkBookingAction(BaseModel):
    """Bulk action request for admin operations"""
    booking_ids: List[str] = Field(..., min_length=1, max_length=100, description="List of booking IDs (max 100)")
    action: str = Field(..., description="Action to perform: approve, reject, cancel")
    reason: Optional[str] = Field(None, description="Reason for bulk action")

    class Config:
        json_schema_extra = {
            "example": {
                "booking_ids": ["booking_123", "booking_456", "booking_789"],
                "action": "approve",
                "reason": "Bulk approval of verified customers"
            }
        }


class BulkBookingResponse(BaseModel):
    """Response from bulk booking operation"""
    success_count: int = Field(..., description="Number of successfully processed bookings")
    failed_count: int = Field(..., description="Number of failed bookings")
    failed_bookings: List[Dict[str, str]] = Field(default_factory=list, description="List of failed bookings with reasons: [{id, reason}]")
    message: str = Field(..., description="Summary message")

    class Config:
        json_schema_extra = {
            "example": {
                "success_count": 8,
                "failed_count": 2,
                "failed_bookings": [
                    {"id": "booking_123", "reason": "Booking not found"},
                    {"id": "booking_456", "reason": "Invalid status transition"}
                ],
                "message": "Successfully updated 8 booking(s), 2 failed"
            }
        }
