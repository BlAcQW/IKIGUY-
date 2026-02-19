"""
Unit tests for booking availability fix.

This test suite validates the fix for the critical bug where all booking slots
showed as "booked" when no agents existed in the database.

The bug was in booking_service.py line 366:
    available=is_available and agent_id is not None

The fix changed it to:
    available=is_available

This ensures slot availability depends ONLY on booking conflicts,
not on agent availability.
"""

import pytest
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.booking_service import BookingService
from app.services.agent_service import AgentService
from app.models.booking import BookingCreate, BookingStatus
from app.core.config import settings


@pytest.fixture
async def db_client():
    """Create test database client."""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[f"{settings.MONGODB_DB_NAME}_test"]
    yield db
    # Cleanup
    await client.drop_database(f"{settings.MONGODB_DB_NAME}_test")
    client.close()


@pytest.fixture
async def booking_service(db_client):
    """Create booking service instance."""
    return BookingService(db_client)


@pytest.fixture
async def agent_service(db_client):
    """Create agent service instance."""
    return AgentService(db_client)


class TestBookingAvailabilityNoAgents:
    """Test slot availability when NO agents exist (main bug fix validation)."""

    @pytest.mark.asyncio
    async def test_slots_available_with_no_agents_and_no_bookings(
        self, booking_service, db_client
    ):
        """
        CRITICAL TEST: Slots should be available when no agents exist and no bookings.

        This is the main bug that was reported: all slots showing as "booked"
        when there are no actual bookings.
        """
        # Ensure no agents exist
        agents_count = await db_client.agents.count_documents({})
        assert agents_count == 0, "Test requires no agents in database"

        # Ensure no bookings exist
        bookings_count = await db_client.bookings.count_documents({})
        assert bookings_count == 0, "Test requires no bookings in database"

        # Get available slots for tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        property_id = "test_property_123"

        slots = await booking_service.get_available_slots(
            property_id=property_id,
            date=tomorrow.date(),
            duration_minutes=30,
            organization_id="test_org_123"
        )

        # All slots should be available
        assert len(slots) > 0, "Should return slots"
        available_slots = [s for s in slots if s.available]
        assert len(available_slots) > 0, "Should have available slots even with no agents"

        # Verify slot properties
        for slot in available_slots:
            assert slot.available is True, "Slot should be available"
            assert slot.reason is None, "Available slots should have no reason"
            # agent_id can be None when no agents exist

    @pytest.mark.asyncio
    async def test_booking_creation_without_agents(self, booking_service, db_client):
        """
        Test that bookings can be created when no agents exist.

        The system is designed to support anonymous/agent-less bookings.
        """
        # Ensure no agents exist
        agents_count = await db_client.agents.count_documents({})
        assert agents_count == 0, "Test requires no agents in database"

        # Create a booking
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=30)

        booking_data = BookingCreate(
            property_id="test_property_123",
            user_id="test_user_456",
            scheduled_at=start_time,
            end_time=end_time,
            status=BookingStatus.PENDING,
            contact_name="Test User",
            contact_email="test@example.com",
            contact_phone="+1234567890",
            notes="Test booking without agents",
            organization_id="test_org_123"
        )

        booking = await booking_service.create_booking(booking_data)

        assert booking is not None, "Booking should be created"
        assert booking.id is not None, "Booking should have an ID"
        assert booking.agent_id is None, "Booking should have no agent when none exist"
        assert booking.status == BookingStatus.PENDING, "Booking should be pending"

        # Verify booking is in database
        db_booking = await db_client.bookings.find_one({"_id": booking.id})
        assert db_booking is not None, "Booking should exist in database"


class TestBookingAvailabilityWithAgents:
    """Test slot availability when agents exist."""

    @pytest.mark.asyncio
    async def test_slots_available_with_free_agents(
        self, booking_service, agent_service, db_client
    ):
        """Test that slots are available when agents exist and are free."""
        # Create a test agent
        agent_data = {
            "name": "Test Agent",
            "email": "agent@example.com",
            "phone": "+1234567890",
            "specializations": ["residential"],
            "max_daily_bookings": 5,
            "organization_id": "test_org_123"
        }
        await db_client.agents.insert_one(agent_data)

        # Get available slots
        tomorrow = datetime.now() + timedelta(days=1)
        slots = await booking_service.get_available_slots(
            property_id="test_property_123",
            date=tomorrow.date(),
            duration_minutes=30,
            organization_id="test_org_123"
        )

        # Should have available slots
        assert len(slots) > 0, "Should return slots"
        available_slots = [s for s in slots if s.available]
        assert len(available_slots) > 0, "Should have available slots with free agents"

        # Some slots should have agent assigned
        slots_with_agents = [s for s in available_slots if s.agent_id is not None]
        assert len(slots_with_agents) > 0, "Some slots should have agent assigned"

    @pytest.mark.asyncio
    async def test_slots_unavailable_when_booked(
        self, booking_service, db_client
    ):
        """Test that slots show as unavailable when actually booked."""
        # Create a booking for tomorrow at 10 AM
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=30)

        booking_data = {
            "property_id": "test_property_123",
            "user_id": "test_user_456",
            "scheduled_at": start_time,
            "end_time": end_time,
            "status": "confirmed",
            "contact_name": "Test User",
            "contact_email": "test@example.com",
            "organization_id": "test_org_123"
        }
        await db_client.bookings.insert_one(booking_data)

        # Get available slots for that day
        slots = await booking_service.get_available_slots(
            property_id="test_property_123",
            date=tomorrow.date(),
            duration_minutes=30,
            organization_id="test_org_123"
        )

        # Find the 10 AM slot
        target_slot = None
        for slot in slots:
            if slot.start_time.hour == 10 and slot.start_time.minute == 0:
                target_slot = slot
                break

        assert target_slot is not None, "Should find 10 AM slot"
        assert target_slot.available is False, "10 AM slot should be unavailable"
        assert target_slot.reason == "Time slot already booked", "Should have booking reason"

    @pytest.mark.asyncio
    async def test_agent_auto_assignment_when_available(
        self, booking_service, db_client
    ):
        """Test that agents are auto-assigned when available."""
        # Create a test agent
        agent_data = {
            "name": "Test Agent",
            "email": "agent@example.com",
            "phone": "+1234567890",
            "specializations": ["residential"],
            "max_daily_bookings": 5,
            "organization_id": "test_org_123"
        }
        result = await db_client.agents.insert_one(agent_data)
        agent_id = str(result.inserted_id)

        # Create a booking
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=30)

        booking_data = BookingCreate(
            property_id="test_property_123",
            user_id="test_user_456",
            scheduled_at=start_time,
            end_time=end_time,
            status=BookingStatus.PENDING,
            contact_name="Test User",
            contact_email="test@example.com",
            organization_id="test_org_123"
        )

        booking = await booking_service.create_booking(booking_data)

        # Agent should be auto-assigned
        assert booking.agent_id is not None, "Agent should be auto-assigned when available"
        assert booking.agent_id == agent_id, "Should assign the available agent"


class TestBookingAvailabilityMixedScenarios:
    """Test slot availability in mixed scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_bookings_with_and_without_agents(
        self, booking_service, db_client
    ):
        """Test that availability is correctly calculated with mixed bookings."""
        # Create one agent
        agent_data = {
            "name": "Test Agent",
            "email": "agent@example.com",
            "phone": "+1234567890",
            "specializations": ["residential"],
            "max_daily_bookings": 5,
            "organization_id": "test_org_123"
        }
        result = await db_client.agents.insert_one(agent_data)
        agent_id = str(result.inserted_id)

        # Create booking WITH agent at 10 AM
        tomorrow = datetime.now() + timedelta(days=1)
        booking1 = {
            "property_id": "test_property_123",
            "user_id": "test_user_1",
            "scheduled_at": tomorrow.replace(hour=10, minute=0, second=0, microsecond=0),
            "end_time": tomorrow.replace(hour=10, minute=30, second=0, microsecond=0),
            "status": "confirmed",
            "agent_id": agent_id,
            "contact_name": "User 1",
            "contact_email": "user1@example.com",
            "organization_id": "test_org_123"
        }
        await db_client.bookings.insert_one(booking1)

        # Create booking WITHOUT agent at 11 AM
        booking2 = {
            "property_id": "test_property_123",
            "user_id": "test_user_2",
            "scheduled_at": tomorrow.replace(hour=11, minute=0, second=0, microsecond=0),
            "end_time": tomorrow.replace(hour=11, minute=30, second=0, microsecond=0),
            "status": "confirmed",
            "agent_id": None,
            "contact_name": "User 2",
            "contact_email": "user2@example.com",
            "organization_id": "test_org_123"
        }
        await db_client.bookings.insert_one(booking2)

        # Get available slots
        slots = await booking_service.get_available_slots(
            property_id="test_property_123",
            date=tomorrow.date(),
            duration_minutes=30,
            organization_id="test_org_123"
        )

        # Both 10 AM and 11 AM should be unavailable
        slot_10am = None
        slot_11am = None

        for slot in slots:
            if slot.start_time.hour == 10 and slot.start_time.minute == 0:
                slot_10am = slot
            if slot.start_time.hour == 11 and slot.start_time.minute == 0:
                slot_11am = slot

        assert slot_10am is not None, "Should find 10 AM slot"
        assert slot_10am.available is False, "10 AM should be unavailable (booked with agent)"

        assert slot_11am is not None, "Should find 11 AM slot"
        assert slot_11am.available is False, "11 AM should be unavailable (booked without agent)"

        # Other slots should be available
        available_slots = [s for s in slots if s.available]
        assert len(available_slots) > 0, "Should have other available slots"

    @pytest.mark.asyncio
    async def test_agent_workload_respected(self, booking_service, db_client):
        """Test that agent workload limits are respected."""
        # Create agent with max 2 daily bookings
        agent_data = {
            "name": "Busy Agent",
            "email": "busy@example.com",
            "phone": "+1234567890",
            "specializations": ["residential"],
            "max_daily_bookings": 2,
            "organization_id": "test_org_123"
        }
        result = await db_client.agents.insert_one(agent_data)
        agent_id = str(result.inserted_id)

        # Create 2 bookings for this agent tomorrow
        tomorrow = datetime.now() + timedelta(days=1)

        for hour in [10, 11]:
            booking = {
                "property_id": "test_property_123",
                "user_id": f"test_user_{hour}",
                "scheduled_at": tomorrow.replace(hour=hour, minute=0, second=0, microsecond=0),
                "end_time": tomorrow.replace(hour=hour, minute=30, second=0, microsecond=0),
                "status": "confirmed",
                "agent_id": agent_id,
                "contact_name": f"User {hour}",
                "contact_email": f"user{hour}@example.com",
                "organization_id": "test_org_123"
            }
            await db_client.bookings.insert_one(booking)

        # Get available slots - agent should be at capacity
        slots = await booking_service.get_available_slots(
            property_id="test_property_123",
            date=tomorrow.date(),
            duration_minutes=30,
            organization_id="test_org_123"
        )

        # Slots at 10 and 11 should be unavailable
        unavailable_count = sum(1 for s in slots if not s.available)
        assert unavailable_count >= 2, "At least 2 slots should be unavailable"

        # Other available slots should not have this agent assigned
        # (since agent is at max capacity)
        available_with_this_agent = [
            s for s in slots
            if s.available and s.agent_id == agent_id
        ]
        assert len(available_with_this_agent) == 0, \
            "Agent at max capacity should not be assigned to new slots"
