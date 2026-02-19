"""
Google Calendar Service for webhook integrations.
Provides actual calendar entry creation and availability checking.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CalendarBookingRequest:
    """Calendar booking request data."""
    customer_name: str
    customer_email: str
    appointment_date: str  # YYYY-MM-DD
    appointment_time: str  # HH:MM
    duration_minutes: int = 30
    meeting_type: str = "consultation"
    notes: str = ""
    timezone: str = "UTC"

@dataclass
class CalendarAvailabilityRequest:
    """Calendar availability check request."""
    date: str  # YYYY-MM-DD
    duration_minutes: int = 30
    meeting_type: str = "consultation"
    timezone: str = "UTC"

class GoogleCalendarWebhookService:
    """Google Calendar service for webhook integrations."""

    def __init__(self):
        """Initialize Google Calendar service."""
        self.calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
        self.credentials_path = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH")
        self.credentials_json = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_JSON")
        self.service_account_email = os.getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL")

        # Business hours configuration
        self.business_hours_start = 9  # 9 AM
        self.business_hours_end = 17   # 5 PM
        self.slot_duration = 30        # 30 minutes

        logger.info(f"Google Calendar service initialized - Calendar ID: {self.calendar_id}")

    def _is_configured(self) -> bool:
        """Check if Google Calendar is properly configured."""
        return bool(self.credentials_path or self.credentials_json)

    async def _get_calendar_service(self):
        """Get Google Calendar service instance."""
        if not self._is_configured():
            raise ValueError("Google Calendar credentials not configured")

        try:
            # Import Google Calendar integration
            import sys
            import os
            sys.path.append('/opt/kasaai/apps/shared')

            from integration.google_workspace import (
                GoogleCalendarIntegration,
                GoogleCalendarConfig,
                GoogleWorkspaceAuth,
                GoogleWorkspaceConfig
            )

            # Parse credentials JSON if provided as string
            credentials_json_data = None
            if self.credentials_json:
                import json
                credentials_json_data = json.loads(self.credentials_json)

            # Create configuration with automatic credential loading from environment
            calendar_config = GoogleCalendarConfig(
                calendar_id=self.calendar_id,
                credentials_path=self.credentials_path,
                credentials_json=credentials_json_data
            )

            workspace_config = GoogleWorkspaceConfig(
                calendar=calendar_config,
                service_account_email=self.service_account_email
            )

            # Create auth and calendar service
            auth = GoogleWorkspaceAuth(workspace_config)
            calendar_service = GoogleCalendarIntegration(calendar_config, auth)

            return calendar_service

        except ImportError as e:
            logger.error(f"Google APIs not available: {e}")
            raise ValueError("Google Calendar integration not available. Install google-api-python-client")
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar service: {e}")
            raise

    async def create_calendar_event(self, booking_request: CalendarBookingRequest) -> Dict[str, Any]:
        """
        Create an actual calendar event.

        Args:
            booking_request: Calendar booking details

        Returns:
            Dict with success status and event details
        """
        try:
            if not self._is_configured():
                return {
                    "success": False,
                    "error": "Google Calendar not configured",
                    "requires_setup": True
                }

            calendar_service = await self._get_calendar_service()

            # Parse datetime
            appointment_datetime = datetime.strptime(
                f"{booking_request.appointment_date} {booking_request.appointment_time}",
                "%Y-%m-%d %H:%M"
            )
            end_datetime = appointment_datetime + timedelta(minutes=booking_request.duration_minutes)

            # Create event data
            event_data = {
                'summary': f"{booking_request.meeting_type.title()} with {booking_request.customer_name}",
                'description': f"""
Meeting Type: {booking_request.meeting_type}
Duration: {booking_request.duration_minutes} minutes
Customer: {booking_request.customer_name}
Email: {booking_request.customer_email}
Notes: {booking_request.notes}

Created via VAPI Voice Assistant
                """.strip(),
                'start': {
                    'dateTime': appointment_datetime.isoformat(),
                    'timeZone': booking_request.timezone,
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': booking_request.timezone,
                },
                'attendees': [
                    {
                        'email': booking_request.customer_email,
                        'displayName': booking_request.customer_name
                    }
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 15},       # 15 minutes before
                    ],
                },
                'conferenceData': {
                    'createRequest': {
                        'requestId': f"vapi-{appointment_datetime.strftime('%Y%m%d%H%M')}-{booking_request.customer_name[:10]}",
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                }
            }

            # Create the event
            created_event = await calendar_service.create_event(
                calendar_id=self.calendar_id,
                event_data=event_data
            )

            logger.info(f"✅ Google Calendar event created: {created_event.get('id')} for {booking_request.customer_name}")

            return {
                "success": True,
                "event_id": created_event.get('id'),
                "event_link": created_event.get('htmlLink'),
                "calendar_entry_created": True,
                "meeting_link": created_event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri'),
                "event_details": {
                    "summary": created_event.get('summary'),
                    "start_time": created_event.get('start', {}).get('dateTime'),
                    "end_time": created_event.get('end', {}).get('dateTime'),
                    "attendees": [att.get('email') for att in created_event.get('attendees', [])]
                }
            }

        except Exception as e:
            logger.error(f"❌ Failed to create Google Calendar event: {e}")
            return {
                "success": False,
                "error": str(e),
                "calendar_entry_created": False
            }

    async def check_availability(self, availability_request: CalendarAvailabilityRequest) -> Dict[str, Any]:
        """
        Check calendar availability for a specific date.

        Args:
            availability_request: Availability check details

        Returns:
            Dict with available time slots
        """
        try:
            if not self._is_configured():
                # Return mock availability if not configured
                return {
                    "success": True,
                    "date": availability_request.date,
                    "available_times": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"],
                    "timezone": availability_request.timezone,
                    "duration": availability_request.duration_minutes,
                    "source": "mock_availability",
                    "note": "Google Calendar not configured - showing mock availability"
                }

            calendar_service = await self._get_calendar_service()

            # Define date range for the requested date
            start_date = datetime.strptime(availability_request.date, "%Y-%m-%d")
            start_datetime = start_date.replace(hour=self.business_hours_start, minute=0, second=0)
            end_datetime = start_date.replace(hour=self.business_hours_end, minute=0, second=0)

            # Get existing events for the day
            existing_events = await calendar_service.list_events(
                calendar_id=self.calendar_id,
                time_min=start_datetime,
                time_max=end_datetime,
                max_results=50
            )

            # Generate available time slots
            available_slots = []
            current_time = start_datetime

            while current_time < end_datetime:
                slot_end = current_time + timedelta(minutes=availability_request.duration_minutes)

                # Check if this slot conflicts with existing events
                is_available = True

                for event in existing_events:
                    event_start = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')))
                    event_end = datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date')))

                    # Check for overlap
                    if (current_time < event_end and slot_end > event_start):
                        is_available = False
                        break

                if is_available:
                    available_slots.append(current_time.strftime('%H:%M'))

                # Move to next slot
                current_time += timedelta(minutes=self.slot_duration)

            logger.info(f"📅 Google Calendar availability check for {availability_request.date}: {len(available_slots)} slots")

            return {
                "success": True,
                "date": availability_request.date,
                "available_times": available_slots[:6],  # Limit to 6 slots for voice response
                "timezone": availability_request.timezone,
                "duration": availability_request.duration_minutes,
                "source": "google_calendar",
                "total_slots_found": len(available_slots)
            }

        except Exception as e:
            logger.error(f"❌ Failed to check Google Calendar availability: {e}")
            return {
                "success": False,
                "error": str(e),
                "date": availability_request.date
            }

# Service instance
_google_calendar_service = None

def get_google_calendar_service() -> GoogleCalendarWebhookService:
    """Get or create Google Calendar service instance."""
    global _google_calendar_service
    if _google_calendar_service is None:
        _google_calendar_service = GoogleCalendarWebhookService()
    return _google_calendar_service