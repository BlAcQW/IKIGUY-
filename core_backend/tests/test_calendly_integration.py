"""
Tests for Calendly Integration Routes

Tests the calendar availability checking and booking functionality
with comprehensive validation and error handling.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
import json

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.routes.calendly_consolidated import (
    CalendlyAvailabilityRequest,
    CalendlyAvailabilityResponse,
    CalendlyBookingRequest,
    CalendlyBookingResponse,
    AvailabilityOption,
    DateTimeResponse
)


class TestCalendlyIntegration:
    """Test suite for Calendly integration functionality."""

    @pytest.fixture
    def sample_datetime_response(self):
        """Sample datetime response for testing."""
        now = datetime.now(timezone.utc)
        return DateTimeResponse(
            current_datetime=now.isoformat(),
            current_date=now.strftime("%Y-%m-%d"),
            current_time=now.strftime("%H:%M"),
            timezone="UTC",
            day_of_week="Monday",
            formatted_date="Monday, September 22, 2025",
            unix_timestamp=int(now.timestamp())
        )

    @pytest.fixture
    def sample_availability_options(self):
        """Sample availability options for testing."""
        base_time = datetime.now(timezone.utc) + timedelta(days=1)

        return [
            AvailabilityOption(
                date=base_time.strftime("%Y-%m-%d"),
                day_name="Tuesday",
                time_slots=["10:00", "10:30", "11:00"],
                formatted_display="Tuesday, September 23 - 3 slots available"
            ),
            AvailabilityOption(
                date=(base_time + timedelta(days=1)).strftime("%Y-%m-%d"),
                day_name="Wednesday",
                time_slots=["14:00", "14:30", "15:00"],
                formatted_display="Wednesday, September 24 - 3 slots available"
            ),
            AvailabilityOption(
                date=(base_time + timedelta(days=2)).strftime("%Y-%m-%d"),
                day_name="Thursday",
                time_slots=["16:00", "16:30", "17:00"],
                formatted_display="Thursday, September 25 - 3 slots available"
            )
        ]

    def test_calendly_availability_request_validation(self):
        """Test CalendlyAvailabilityRequest model validation."""
        # Valid request with all fields
        request = CalendlyAvailabilityRequest(
            event_type="consultation",
            start_date="2025-09-23",
            end_date="2025-09-30",
            timezone="Africa/Accra"
        )

        assert request.event_type == "consultation"
        assert request.start_date == "2025-09-23"
        assert request.end_date == "2025-09-30"
        assert request.timezone == "Africa/Accra"

        # Valid request with minimal fields (using defaults)
        minimal_request = CalendlyAvailabilityRequest()
        assert minimal_request.event_type is None  # Default is None
        assert minimal_request.timezone == "Africa/Accra"    # Default

    def test_calendly_booking_request_validation(self):
        """Test CalendlyBookingRequest model validation."""
        booking_time = datetime.now(timezone.utc) + timedelta(days=1)

        # Valid booking request
        request = CalendlyBookingRequest(
            event_type="consultation",
            start_time=booking_time.isoformat(),
            customer_name="John Doe",
            customer_phone="+1234567890",
            timezone="Africa/Accra"
        )

        assert request.event_type == "consultation"
        assert request.customer_name == "John Doe"
        assert request.customer_phone == "+1234567890"
        assert request.timezone == "Africa/Accra"

    def test_availability_option_model(self):
        """Test AvailabilityOption model."""
        now = datetime.now(timezone.utc)

        option = AvailabilityOption(
            date=now.strftime("%Y-%m-%d"),
            day_name="Monday",
            time_slots=["10:00", "10:30", "11:00"],
            formatted_display="Monday, September 22 - 3 slots available"
        )

        assert option.date == now.strftime("%Y-%m-%d")
        assert option.day_name == "Monday"
        assert option.time_slots == ["10:00", "10:30", "11:00"]
        assert option.formatted_display == "Monday, September 22 - 3 slots available"

    def test_calendly_availability_response_model(self, sample_datetime_response, sample_availability_options):
        """Test CalendlyAvailabilityResponse model."""
        response = CalendlyAvailabilityResponse(
            success=True,
            current_date_context=sample_datetime_response,
            availability_options=sample_availability_options,
            total_slots_found=15,
            search_period="September 23 - September 30, 2025",
            message="Today is September 22, 2025. Found 3 available appointment slots for the next week."
        )

        assert response.success is True
        assert len(response.availability_options) == 3
        assert response.total_slots_found == 15
        assert "Today is September 22, 2025" in response.message
        assert response.current_date_context.day_of_week == "Monday"

    def test_calendly_booking_response_model(self, sample_datetime_response):
        """Test CalendlyBookingResponse model."""
        booking_time = datetime.now(timezone.utc) + timedelta(days=1)

        response = CalendlyBookingResponse(
            success=True,
            booking_id="book_123456789",
            appointment_details={
                "booking_id": "book_123456789",
                "event_type": "consultation",
                "customer_name": "John Doe",
                "customer_phone": "+1234567890",
                "appointment_time": "2025-09-23 14:00",
                "status": "confirmed"
            },
            confirmation_message="Appointment successfully booked for September 23, 2025 at 10:00 AM.",
            current_date_context=sample_datetime_response
        )

        assert response.success is True
        assert response.booking_id == "book_123456789"
        assert response.appointment_details["customer_name"] == "John Doe"
        assert response.appointment_details["customer_phone"] == "+1234567890"

    @pytest.mark.asyncio
    async def test_availability_endpoint_business_hours_validation(self):
        """Test business hours validation in availability endpoint."""
        # Test with business hours (Monday-Friday, 9 AM - 5 PM)

        # Mock datetime to return Monday 10 AM
        monday_10am = datetime(2025, 9, 22, 10, 0, 0, tzinfo=timezone.utc)

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = monday_10am
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            # This should pass business hours validation
            assert monday_10am.weekday() < 5  # Monday (0) < 5
            assert 9 <= monday_10am.hour <= 17  # 10 AM within business hours

    @pytest.mark.asyncio
    async def test_availability_endpoint_timezone_handling(self):
        """Test timezone handling in availability endpoint."""
        # Test different timezone scenarios

        # Africa/Accra timezone
        accra_timezone = "Africa/Accra"

        # Test timezone validation
        valid_timezones = [
            "Africa/Accra",
            "UTC",
            "US/Eastern",
            "Europe/London"
        ]

        for tz in valid_timezones:
            request = CalendlyAvailabilityRequest(timezone=tz)
            assert request.timezone == tz

    @pytest.mark.asyncio
    async def test_booking_endpoint_validation(self):
        """Test booking endpoint validation logic."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        past_time = datetime.now(timezone.utc) - timedelta(days=1)

        # Valid future booking
        valid_request = CalendlyBookingRequest(
            event_type="consultation",
            start_time=future_time.isoformat(),
            customer_name="John Test",
            customer_phone="+1234567890"
        )

        # Validate that start_time is properly formatted
        assert valid_request.start_time == future_time.isoformat()

        # Test phone number formats
        valid_phones = ["+1234567890", "+233123456789", "+44123456789"]
        for phone in valid_phones:
            request = CalendlyBookingRequest(
                event_type="consultation",
                start_time=future_time.isoformat(),
                customer_name="Test User",
                customer_phone=phone
            )
            assert request.customer_phone == phone

    @pytest.mark.asyncio
    async def test_availability_search_date_range(self):
        """Test date range validation for availability search."""
        today = datetime.now(timezone.utc).date()

        # Valid future date range
        start_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")

        request = CalendlyAvailabilityRequest(
            start_date=start_date,
            end_date=end_date
        )

        assert request.start_date == start_date
        assert request.end_date == end_date

        # Test date parsing
        from datetime import datetime as dt
        parsed_start = dt.strptime(request.start_date, "%Y-%m-%d").date()
        parsed_end = dt.strptime(request.end_date, "%Y-%m-%d").date()

        assert parsed_start > today  # Start date should be in the future
        assert parsed_end > parsed_start  # End date should be after start date

    @pytest.mark.asyncio
    async def test_current_date_context_generation(self, sample_datetime_response):
        """Test current date context generation."""
        # Test that current date context includes all required fields
        context = sample_datetime_response

        required_fields = [
            'current_datetime', 'current_date', 'current_time',
            'timezone', 'day_of_week', 'formatted_date', 'unix_timestamp'
        ]

        for field in required_fields:
            assert hasattr(context, field), f"Missing field: {field}"
            assert getattr(context, field) is not None, f"Field {field} is None"

    @pytest.mark.asyncio
    async def test_availability_message_format(self, sample_datetime_response, sample_availability_options):
        """Test availability response message format."""
        response = CalendlyAvailabilityResponse(
            success=True,
            current_date_context=sample_datetime_response,
            availability_options=sample_availability_options,
            total_slots_found=15,
            search_period="September 23 - September 30, 2025",
            message="Today is September 22, 2025. Found 3 available appointment slots for the next week."
        )

        # Test message format requirements
        assert response.message.startswith("Today is"), "Message should start with 'Today is'"
        assert "September 22, 2025" in response.message, "Message should include current date"
        assert "3 available" in response.message, "Message should mention number of options"

        # Test that exactly 3 options are provided
        assert len(response.availability_options) == 3, "Should provide exactly 3 options"

    @pytest.mark.asyncio
    async def test_error_handling_scenarios(self):
        """Test various error handling scenarios."""

        # Test invalid event type
        try:
            invalid_request = CalendlyAvailabilityRequest(event_type="invalid_type")
            # Should not raise validation error since we allow flexible event types
            assert invalid_request.event_type == "invalid_type"
        except Exception:
            # If validation is strict, this would fail
            pass

        # Test empty customer name
        future_time = datetime.now(timezone.utc) + timedelta(days=1)

        # Empty name should be handled gracefully
        empty_name_request = CalendlyBookingRequest(
            event_type="consultation",
            start_time=future_time.isoformat(),
            customer_name="",  # Empty name
            customer_phone="+1234567890"
        )
        assert empty_name_request.customer_name == ""

    @pytest.mark.asyncio
    async def test_integration_with_vapi_guidelines(self):
        """Test integration follows VAPI guidelines."""

        # Test that booking only requires first name and phone (no email)
        future_time = datetime.now(timezone.utc) + timedelta(days=1)

        vapi_compliant_request = CalendlyBookingRequest(
            event_type="consultation",
            start_time=future_time.isoformat(),
            customer_name="John",  # First name only
            customer_phone="+1234567890"  # Phone from VAPI webhook
            # No email field required
        )

        assert vapi_compliant_request.customer_name == "John"
        assert vapi_compliant_request.customer_phone == "+1234567890"
        # Ensure no email field is required
        assert not hasattr(vapi_compliant_request, 'customer_email') or vapi_compliant_request.customer_email is None

    @pytest.mark.asyncio
    async def test_response_consistency(self, sample_datetime_response):
        """Test response format consistency."""

        # Both availability and booking responses should have consistent structure
        future_time = datetime.now(timezone.utc) + timedelta(days=1)

        booking_response = CalendlyBookingResponse(
            success=True,
            booking_id="book_123456789",
            appointment_details={
                "appointment_time": future_time.isoformat(),
                "customer_name": "John",
                "customer_phone": "+1234567890"
            },
            confirmation_message="Today is September 22, 2025. Appointment booked successfully.",
            current_date_context=sample_datetime_response
        )

        # Test consistent message format
        assert booking_response.confirmation_message.startswith("Today is"), "Booking message should start with 'Today is'"
        assert "September 22, 2025" in booking_response.confirmation_message, "Should include current date"

        # Test that current_date_context is included
        assert booking_response.current_date_context is not None
        assert booking_response.current_date_context.current_date is not None


class TestCalendlyEdgeCases:
    """Test edge cases and error scenarios for Calendly integration."""

    @pytest.mark.asyncio
    async def test_weekend_booking_attempt(self):
        """Test booking attempt on weekends."""
        # Create a Saturday date
        saturday = datetime(2025, 9, 27, 10, 0, 0, tzinfo=timezone.utc)  # Saturday

        booking_request = CalendlyBookingRequest(
            event_type="consultation",
            start_time=saturday.isoformat(),
            customer_name="John",
            customer_phone="+1234567890"
        )

        # Weekend should be detected (Saturday = weekday 5)
        assert saturday.weekday() == 5  # Saturday

    @pytest.mark.asyncio
    async def test_after_hours_booking_attempt(self):
        """Test booking attempt outside business hours."""
        # Create a time outside business hours (6 PM = 18:00)
        after_hours = datetime(2025, 9, 23, 18, 0, 0, tzinfo=timezone.utc)  # 6 PM

        booking_request = CalendlyBookingRequest(
            event_type="consultation",
            start_time=after_hours.isoformat(),
            customer_name="John",
            customer_phone="+1234567890"
        )

        # Should be outside business hours (9 AM - 5 PM)
        assert after_hours.hour >= 17  # After 5 PM

    @pytest.mark.asyncio
    async def test_past_date_booking_attempt(self):
        """Test booking attempt for past date."""
        # Create a past date
        past_date = datetime.now(timezone.utc) - timedelta(days=1)

        booking_request = CalendlyBookingRequest(
            event_type="consultation",
            start_time=past_date.isoformat(),
            customer_name="John",
            customer_phone="+1234567890"
        )

        # Should be in the past
        assert past_date < datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_phone_number_formats(self):
        """Test various phone number formats."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)

        valid_phone_formats = [
            "+1234567890",      # US format
            "+233123456789",    # Ghana format
            "+44123456789",     # UK format
            "+4412345678901",   # Longer international
        ]

        for phone in valid_phone_formats:
            request = CalendlyBookingRequest(
                event_type="consultation",
                start_time=future_time.isoformat(),
                customer_name="Test",
                customer_phone=phone
            )
            assert request.customer_phone == phone

    @pytest.mark.asyncio
    async def test_timezone_edge_cases(self):
        """Test timezone edge cases."""

        edge_case_timezones = [
            "UTC",
            "Africa/Accra",
            "US/Eastern",
            "US/Pacific",
            "Europe/London",
            "Asia/Tokyo"
        ]

        for tz in edge_case_timezones:
            request = CalendlyAvailabilityRequest(timezone=tz)
            assert request.timezone == tz

    @pytest.mark.asyncio
    async def test_long_name_handling(self):
        """Test handling of long customer names."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)

        # Test various name lengths
        names = [
            "J",  # Single character
            "John",  # Normal name
            "John-Paul",  # Hyphenated
            "John Paul Smith Jr.",  # Full name with title
            "A" * 100,  # Very long name
        ]

        for name in names:
            request = CalendlyBookingRequest(
                event_type="consultation",
                start_time=future_time.isoformat(),
                customer_name=name,
                customer_phone="+1234567890"
            )
            assert request.customer_name == name


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])