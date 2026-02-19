"""
Enhanced Appointment Booking Voice Agent Tools
AI-powered appointment booking featuring intelligent calendar management, availability optimization,
automated confirmations, and comprehensive scheduling analytics.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
import asyncio
import logging
from enum import Enum
import pytz

# Database and API imports
from pymongo import MongoClient
from bson import ObjectId
import httpx
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppointmentType(str, Enum):
    CONSULTATION = "consultation"
    DEMO = "demo"
    MEETING = "meeting"
    SERVICE_APPOINTMENT = "service_appointment"
    FOLLOW_UP = "follow_up"
    GROUP_SESSION = "group_session"

class MeetingLocation(str, Enum):
    IN_PERSON = "in_person"
    VIDEO_CALL = "video_call"
    PHONE_CALL = "phone_call"
    CUSTOMER_LOCATION = "customer_location"

class RescheduleReason(str, Enum):
    CUSTOMER_REQUEST = "customer_request"
    TEAM_CONFLICT = "team_conflict"
    EMERGENCY = "emergency"
    OPTIMIZATION = "optimization"
    TECHNICAL_ISSUE = "technical_issue"

class CancellationReason(str, Enum):
    CUSTOMER_REQUEST = "customer_request"
    TEAM_UNAVAILABLE = "team_unavailable"
    EMERGENCY = "emergency"
    NO_SHOW = "no_show"
    TECHNICAL_ISSUE = "technical_issue"
    WEATHER = "weather"

class InitiatedBy(str, Enum):
    CUSTOMER = "customer"
    TEAM = "team"
    SYSTEM = "system"

class ConfirmationType(str, Enum):
    INITIAL_BOOKING = "initial_booking"
    RESCHEDULE_UPDATE = "reschedule_update"
    REMINDER = "reminder"
    PREPARATION_MATERIALS = "preparation_materials"

class ReminderType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PHONE_CALL = "phone_call"
    APP_NOTIFICATION = "app_notification"

class TimeBefore(str, Enum):
    HOURS_24 = "24_hours"
    HOURS_2 = "2_hours"
    MINUTES_30 = "30_minutes"
    WEEK_1 = "1_week"
    DAYS_3 = "3_days"

class ReminderFrequency(str, Enum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    FREQUENT = "frequent"

class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class CustomerFlexibility(str, Enum):
    VERY_FLEXIBLE = "very_flexible"
    SOMEWHAT_FLEXIBLE = "somewhat_flexible"
    SPECIFIC_REQUIREMENTS = "specific_requirements"

class GroupAppointmentType(str, Enum):
    GROUP_CONSULTATION = "group_consultation"
    TEAM_DEMO = "team_demo"
    MULTI_EXPERT_SESSION = "multi_expert_session"
    TRAINING_SESSION = "training_session"

# Database connection
mongo_client = MongoClient(os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017"))
db = mongo_client.kasaai_appointment_booking

class AppointmentBookingTools:
    """Comprehensive appointment booking voice agent tools."""

    def __init__(self):
        self.google_calendar_service = self._init_google_calendar_service()
        self.kasaai_api_key = os.getenv("KASAAI_API_KEY")
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.twilio_api_key = os.getenv("TWILIO_API_KEY")
        self.zoom_api_key = os.getenv("ZOOM_API_KEY")

    async def check_availability(
        self,
        appointment_type: AppointmentType,
        duration_minutes: int,
        preferred_dates: Optional[List[str]] = None,
        preferred_times: Optional[List[str]] = None,
        team_member_preference: Optional[str] = None,
        time_zone: str = "UTC",
        urgent_booking: bool = False
    ) -> Dict[str, Any]:
        """
        Check real-time calendar availability across team members and appointment types.

        Args:
            appointment_type: Type of appointment to schedule
            duration_minutes: Required appointment duration in minutes
            preferred_dates: Customer preferred dates (YYYY-MM-DD format)
            preferred_times: Customer preferred time ranges
            team_member_preference: Specific team member requested or "any_available"
            time_zone: Customer time zone
            urgent_booking: Whether this is an urgent/priority booking

        Returns:
            Dict containing available time slots and team member availability
        """
        try:
            logger.info(f"Checking availability for {appointment_type} appointment")

            # Get timezone object
            customer_tz = pytz.timezone(time_zone)

            # Set default date range if none provided
            if not preferred_dates:
                today = datetime.now(customer_tz).date()
                preferred_dates = [
                    (today + timedelta(days=i)).isoformat()
                    for i in range(1, 15)  # Next 2 weeks
                ]

            availability_check = {
                "appointment_type": appointment_type,
                "duration_minutes": duration_minutes,
                "time_zone": time_zone,
                "urgent_booking": urgent_booking,
                "available_slots": [],
                "team_availability": {},
                "total_slots_found": 0
            }

            # Get team members based on appointment type
            team_members = await self._get_available_team_members(
                appointment_type,
                team_member_preference
            )

            # Check availability for each date
            for date_str in preferred_dates[:7]:  # Limit to first week for performance
                date_obj = datetime.fromisoformat(date_str).date()

                # Skip past dates
                if date_obj <= datetime.now(customer_tz).date():
                    continue

                # Get available slots for this date
                daily_slots = await self._get_daily_availability(
                    date_obj,
                    duration_minutes,
                    team_members,
                    preferred_times,
                    customer_tz,
                    urgent_booking
                )

                if daily_slots:
                    availability_check["available_slots"].extend(daily_slots)

            # Sort slots by date and time
            availability_check["available_slots"].sort(
                key=lambda x: x["start_datetime"]
            )

            # Limit results for better user experience
            availability_check["available_slots"] = availability_check["available_slots"][:20]
            availability_check["total_slots_found"] = len(availability_check["available_slots"])

            # Add team member availability summary
            availability_check["team_availability"] = {
                tm["id"]: {
                    "name": tm["name"],
                    "specialty": tm.get("specialty"),
                    "available_slots": len([
                        slot for slot in availability_check["available_slots"]
                        if slot["team_member_id"] == tm["id"]
                    ])
                }
                for tm in team_members
            }

            # Store availability check for analytics
            db.availability_checks.insert_one({
                "timestamp": datetime.utcnow(),
                "appointment_type": appointment_type,
                "duration_minutes": duration_minutes,
                "slots_found": availability_check["total_slots_found"],
                "team_members_checked": len(team_members),
                "urgent_booking": urgent_booking
            })

            logger.info(f"Found {availability_check['total_slots_found']} available slots")
            return availability_check

        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return {"error": str(e), "available_slots": [], "total_slots_found": 0}

    async def book_appointment(
        self,
        appointment_type: AppointmentType,
        scheduled_datetime: str,
        duration_minutes: int,
        customer_name: str,
        customer_email: str,
        team_member_id: Optional[str] = None,
        customer_phone: Optional[str] = None,
        appointment_notes: Optional[str] = None,
        meeting_location: MeetingLocation = MeetingLocation.VIDEO_CALL,
        send_calendar_invite: bool = True
    ) -> Dict[str, Any]:
        """
        Schedule new appointments with automatic calendar integration.

        Args:
            appointment_type: Type of appointment being scheduled
            scheduled_datetime: Selected appointment date and time (ISO format)
            duration_minutes: Appointment duration in minutes
            customer_name: Customer full name
            customer_email: Customer email address for confirmation
            team_member_id: ID of assigned team member
            customer_phone: Customer phone number
            appointment_notes: Special requirements or notes
            meeting_location: How the appointment will be conducted
            send_calendar_invite: Whether to send calendar invitation

        Returns:
            Dict containing booking confirmation and appointment details
        """
        try:
            logger.info(f"Booking {appointment_type} appointment for {customer_name}")

            # Parse scheduled datetime
            appointment_datetime = datetime.fromisoformat(scheduled_datetime.replace('Z', '+00:00'))
            end_datetime = appointment_datetime + timedelta(minutes=duration_minutes)

            # Auto-assign team member if not specified
            if not team_member_id:
                team_member = await self._auto_assign_team_member(
                    appointment_type,
                    appointment_datetime
                )
                team_member_id = team_member["id"] if team_member else None

            if not team_member_id:
                return {
                    "error": "No team member available for the selected time",
                    "success": False
                }

            # Create appointment record
            appointment_data = {
                "appointment_id": str(ObjectId()),
                "appointment_type": appointment_type,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "customer_phone": customer_phone,
                "team_member_id": team_member_id,
                "scheduled_datetime": appointment_datetime,
                "end_datetime": end_datetime,
                "duration_minutes": duration_minutes,
                "meeting_location": meeting_location,
                "appointment_notes": appointment_notes,
                "status": "confirmed",
                "created_date": datetime.utcnow(),
                "created_by": "voice_agent"
            }

            # Check for conflicts
            conflict_check = await self._check_appointment_conflicts(
                team_member_id,
                appointment_datetime,
                end_datetime
            )

            if conflict_check["has_conflicts"]:
                return {
                    "error": "Scheduling conflict detected",
                    "conflicts": conflict_check["conflicts"],
                    "success": False
                }

            # Store appointment in database
            result = db.appointments.insert_one(appointment_data.copy())
            appointment_data["_id"] = str(result.inserted_id)

            # Create calendar event
            calendar_result = await self._create_calendar_event(appointment_data)
            appointment_data["calendar_event_id"] = calendar_result.get("event_id")

            # Generate meeting details based on location
            if meeting_location == MeetingLocation.VIDEO_CALL:
                meeting_details = await self._create_video_meeting(appointment_data)
                appointment_data["meeting_link"] = meeting_details.get("join_url")
                appointment_data["meeting_id"] = meeting_details.get("meeting_id")

            # Send confirmation if requested
            if send_calendar_invite:
                confirmation_result = await self.send_confirmation(
                    appointment_data["appointment_id"],
                    ConfirmationType.INITIAL_BOOKING,
                    include_calendar_invite=True,
                    include_preparation_guide=True
                )
                appointment_data["confirmation_sent"] = confirmation_result.get("success", False)

            # Set up default reminders
            await self.set_appointment_reminders(
                appointment_data["appointment_id"],
                [
                    {
                        "time_before": TimeBefore.HOURS_24,
                        "reminder_type": ReminderType.EMAIL,
                        "include_preparation": True
                    },
                    {
                        "time_before": TimeBefore.HOURS_2,
                        "reminder_type": ReminderType.SMS,
                        "include_preparation": False
                    }
                ]
            )

            logger.info(f"Appointment booked successfully: {appointment_data['appointment_id']}")
            return {
                "success": True,
                "appointment_id": appointment_data["appointment_id"],
                "scheduled_datetime": scheduled_datetime,
                "team_member_name": await self._get_team_member_name(team_member_id),
                "meeting_link": appointment_data.get("meeting_link"),
                "calendar_event_id": appointment_data.get("calendar_event_id"),
                "confirmation_message": f"Perfect! I've scheduled your {appointment_type.replace('_', ' ')} for {appointment_datetime.strftime('%B %d, %Y at %I:%M %p')}. You'll receive a confirmation email with all the details."
            }

        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            return {"error": str(e), "success": False}

    async def reschedule_appointment(
        self,
        appointment_id: str,
        new_datetime: str,
        reschedule_reason: RescheduleReason,
        new_duration_minutes: Optional[int] = None,
        notify_customer: bool = True,
        apology_message: Optional[str] = None,
        compensation_offered: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Modify existing appointments and send update notifications.

        Args:
            appointment_id: Existing appointment identifier
            new_datetime: New appointment date and time (ISO format)
            reschedule_reason: Reason for rescheduling
            new_duration_minutes: New appointment duration if different
            notify_customer: Whether to send rescheduling notification
            apology_message: Optional apology message for customer
            compensation_offered: Any compensation offered for inconvenience

        Returns:
            Dict containing rescheduling confirmation
        """
        try:
            logger.info(f"Rescheduling appointment {appointment_id}")

            # Get existing appointment
            appointment = db.appointments.find_one({"appointment_id": appointment_id})
            if not appointment:
                return {"error": "Appointment not found", "success": False}

            # Parse new datetime
            new_appointment_datetime = datetime.fromisoformat(new_datetime.replace('Z', '+00:00'))
            duration = new_duration_minutes or appointment["duration_minutes"]
            new_end_datetime = new_appointment_datetime + timedelta(minutes=duration)

            # Check for conflicts at new time
            conflict_check = await self._check_appointment_conflicts(
                appointment["team_member_id"],
                new_appointment_datetime,
                new_end_datetime,
                exclude_appointment_id=appointment_id
            )

            if conflict_check["has_conflicts"]:
                return {
                    "error": "Scheduling conflict at new time",
                    "conflicts": conflict_check["conflicts"],
                    "success": False
                }

            # Store original appointment details for history
            reschedule_history = {
                "appointment_id": appointment_id,
                "original_datetime": appointment["scheduled_datetime"],
                "new_datetime": new_appointment_datetime,
                "reschedule_reason": reschedule_reason,
                "reschedule_date": datetime.utcnow(),
                "initiated_by": "voice_agent",
                "apology_message": apology_message,
                "compensation_offered": compensation_offered
            }

            db.reschedule_history.insert_one(reschedule_history)

            # Update appointment
            update_data = {
                "scheduled_datetime": new_appointment_datetime,
                "end_datetime": new_end_datetime,
                "duration_minutes": duration,
                "last_modified": datetime.utcnow(),
                "status": "rescheduled"
            }

            db.appointments.update_one(
                {"appointment_id": appointment_id},
                {"$set": update_data}
            )

            # Update calendar event
            if appointment.get("calendar_event_id"):
                await self._update_calendar_event(
                    appointment["calendar_event_id"],
                    new_appointment_datetime,
                    new_end_datetime,
                    f"RESCHEDULED: {appointment['appointment_type']} - {appointment['customer_name']}"
                )

            # Send notification if requested
            if notify_customer:
                notification_result = await self.send_confirmation(
                    appointment_id,
                    ConfirmationType.RESCHEDULE_UPDATE,
                    custom_message=apology_message
                )

            logger.info(f"Appointment {appointment_id} rescheduled successfully")
            return {
                "success": True,
                "appointment_id": appointment_id,
                "original_datetime": appointment["scheduled_datetime"].isoformat(),
                "new_datetime": new_datetime,
                "reschedule_reason": reschedule_reason,
                "notification_sent": notify_customer,
                "confirmation_message": f"Your appointment has been rescheduled to {new_appointment_datetime.strftime('%B %d, %Y at %I:%M %p')}. You'll receive an updated calendar invitation."
            }

        except Exception as e:
            logger.error(f"Error rescheduling appointment: {e}")
            return {"error": str(e), "success": False}

    async def cancel_appointment(
        self,
        appointment_id: str,
        cancellation_reason: CancellationReason,
        initiated_by: InitiatedBy,
        refund_required: bool = False,
        reschedule_offered: bool = True,
        notify_waiting_list: bool = True,
        cancellation_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel appointments and manage cancellation processes.

        Args:
            appointment_id: Appointment identifier to cancel
            cancellation_reason: Reason for cancellation
            initiated_by: Who initiated the cancellation
            refund_required: Whether a refund needs to be processed
            reschedule_offered: Whether to offer rescheduling options
            notify_waiting_list: Whether to notify waiting list
            cancellation_notes: Additional notes about cancellation

        Returns:
            Dict containing cancellation confirmation
        """
        try:
            logger.info(f"Cancelling appointment {appointment_id}")

            # Get appointment
            appointment = db.appointments.find_one({"appointment_id": appointment_id})
            if not appointment:
                return {"error": "Appointment not found", "success": False}

            # Create cancellation record
            cancellation_data = {
                "appointment_id": appointment_id,
                "customer_name": appointment["customer_name"],
                "customer_email": appointment["customer_email"],
                "scheduled_datetime": appointment["scheduled_datetime"],
                "cancellation_reason": cancellation_reason,
                "initiated_by": initiated_by,
                "cancellation_date": datetime.utcnow(),
                "refund_required": refund_required,
                "reschedule_offered": reschedule_offered,
                "cancellation_notes": cancellation_notes
            }

            db.cancellations.insert_one(cancellation_data)

            # Update appointment status
            db.appointments.update_one(
                {"appointment_id": appointment_id},
                {
                    "$set": {
                        "status": "cancelled",
                        "cancellation_date": datetime.utcnow(),
                        "cancellation_reason": cancellation_reason
                    }
                }
            )

            # Cancel calendar event
            if appointment.get("calendar_event_id"):
                await self._cancel_calendar_event(appointment["calendar_event_id"])

            # Process refund if required
            refund_result = None
            if refund_required:
                refund_result = await self._process_refund(appointment)

            # Notify waiting list if requested
            waiting_list_notifications = []
            if notify_waiting_list:
                waiting_list_notifications = await self._notify_waiting_list(
                    appointment["scheduled_datetime"],
                    appointment["duration_minutes"],
                    appointment["team_member_id"]
                )

            # Send cancellation notification
            cancellation_notification = await self._send_cancellation_notification(
                appointment,
                cancellation_reason,
                reschedule_offered,
                cancellation_notes
            )

            logger.info(f"Appointment {appointment_id} cancelled successfully")
            return {
                "success": True,
                "appointment_id": appointment_id,
                "cancellation_reason": cancellation_reason,
                "refund_processed": refund_result.get("success", False) if refund_required else False,
                "waiting_list_notified": len(waiting_list_notifications),
                "reschedule_offered": reschedule_offered,
                "confirmation_message": f"Your appointment has been cancelled. {'A refund will be processed within 3-5 business days.' if refund_required else ''} {'We\'d be happy to help you reschedule when you\'re ready.' if reschedule_offered else ''}"
            }

        except Exception as e:
            logger.error(f"Error cancelling appointment: {e}")
            return {"error": str(e), "success": False}

    async def send_confirmation(
        self,
        appointment_id: str,
        confirmation_type: ConfirmationType,
        include_calendar_invite: bool = False,
        include_preparation_guide: bool = False,
        include_location_details: bool = False,
        custom_message: Optional[str] = None,
        send_via: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send appointment confirmations and materials to customers.

        Args:
            appointment_id: Appointment identifier
            confirmation_type: Type of confirmation being sent
            include_calendar_invite: Include calendar invitation file
            include_preparation_guide: Include preparation instructions
            include_location_details: Include meeting location details
            custom_message: Additional personalized message
            send_via: Channels to send confirmation through

        Returns:
            Dict containing confirmation sending results
        """
        try:
            logger.info(f"Sending confirmation for appointment {appointment_id}")

            # Get appointment details
            appointment = db.appointments.find_one({"appointment_id": appointment_id})
            if not appointment:
                return {"error": "Appointment not found", "success": False}

            # Default to email if no channels specified
            if not send_via:
                send_via = ["email"]

            confirmation_data = {
                "appointment_id": appointment_id,
                "confirmation_type": confirmation_type,
                "sent_via": send_via,
                "sent_date": datetime.utcnow(),
                "delivery_status": {}
            }

            # Prepare confirmation content
            confirmation_content = await self._prepare_confirmation_content(
                appointment,
                confirmation_type,
                include_preparation_guide,
                include_location_details,
                custom_message
            )

            # Send via each requested channel
            for channel in send_via:
                try:
                    if channel == "email":
                        result = await self._send_email_confirmation(
                            appointment,
                            confirmation_content,
                            include_calendar_invite
                        )
                    elif channel == "sms":
                        result = await self._send_sms_confirmation(
                            appointment,
                            confirmation_content
                        )
                    elif channel == "phone_call":
                        result = await self._send_phone_confirmation(
                            appointment,
                            confirmation_content
                        )
                    else:
                        result = {"success": False, "error": f"Unsupported channel: {channel}"}

                    confirmation_data["delivery_status"][channel] = result

                except Exception as channel_error:
                    logger.error(f"Error sending via {channel}: {channel_error}")
                    confirmation_data["delivery_status"][channel] = {
                        "success": False,
                        "error": str(channel_error)
                    }

            # Store confirmation record
            db.confirmations.insert_one(confirmation_data)

            # Check overall success
            successful_channels = [
                channel for channel, status in confirmation_data["delivery_status"].items()
                if status.get("success", False)
            ]

            logger.info(f"Confirmation sent via {len(successful_channels)} channels")
            return {
                "success": len(successful_channels) > 0,
                "sent_via": successful_channels,
                "failed_channels": [
                    channel for channel in send_via
                    if channel not in successful_channels
                ],
                "confirmation_message": f"Confirmation sent successfully via {', '.join(successful_channels)}."
            }

        except Exception as e:
            logger.error(f"Error sending confirmation: {e}")
            return {"error": str(e), "success": False}

    # Helper methods

    async def _get_available_team_members(
        self,
        appointment_type: AppointmentType,
        preference: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Get team members available for specific appointment types."""
        if preference and preference != "any_available":
            # Get specific team member
            team_member = db.team_members.find_one({"id": preference, "active": True})
            return [team_member] if team_member else []

        # Get all team members qualified for this appointment type
        return list(db.team_members.find({
            "active": True,
            "appointment_types": {"$in": [appointment_type, "all"]}
        }))

    async def _get_daily_availability(
        self,
        date: datetime.date,
        duration_minutes: int,
        team_members: List[Dict],
        preferred_times: Optional[List[str]],
        timezone: pytz.timezone,
        urgent: bool
    ) -> List[Dict[str, Any]]:
        """Get available time slots for a specific date."""
        slots = []

        for team_member in team_members:
            # Get team member's working hours
            working_hours = team_member.get("working_hours", {})
            day_of_week = date.strftime("%A").lower()

            if day_of_week not in working_hours:
                continue

            day_schedule = working_hours[day_of_week]
            if not day_schedule.get("available", True):
                continue

            start_time = datetime.strptime(day_schedule.get("start", "09:00"), "%H:%M").time()
            end_time = datetime.strptime(day_schedule.get("end", "17:00"), "%H:%M").time()

            # Generate time slots
            current_datetime = datetime.combine(date, start_time)
            end_datetime = datetime.combine(date, end_time)

            while current_datetime + timedelta(minutes=duration_minutes) <= end_datetime:
                slot_end = current_datetime + timedelta(minutes=duration_minutes)

                # Check if slot is available (no conflicts)
                if await self._is_slot_available(team_member["id"], current_datetime, slot_end):
                    slots.append({
                        "start_datetime": current_datetime.isoformat(),
                        "end_datetime": slot_end.isoformat(),
                        "team_member_id": team_member["id"],
                        "team_member_name": team_member["name"],
                        "duration_minutes": duration_minutes
                    })

                # Move to next slot (15-minute intervals)
                current_datetime += timedelta(minutes=15)

        return slots

    async def _is_slot_available(
        self,
        team_member_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """Check if a time slot is available for a team member."""
        conflicts = db.appointments.find({
            "team_member_id": team_member_id,
            "status": {"$in": ["confirmed", "rescheduled"]},
            "$or": [
                {
                    "scheduled_datetime": {"$lt": end_time},
                    "end_datetime": {"$gt": start_time}
                }
            ]
        })

        return conflicts.count() == 0

# Initialize tools instance
appointment_booking_tools = AppointmentBookingTools()