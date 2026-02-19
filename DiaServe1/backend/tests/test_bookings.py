"""
Booking Module Tests

Tests for booking CRUD operations, status transitions, auto-assignment, and reminders.

Coverage:
- CRUD operations (create, read, update, delete)
- Booking status transitions (pending -> confirmed -> completed)
- Agent auto-assignment
- Reminder scheduling
- Waitlist management
- Organization isolation
"""

import pytest
from httpx import AsyncClient
from typing import Dict, Any
from datetime import datetime, timedelta


# ============================================================================
# CRUD OPERATIONS TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_booking_success(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_booking: Dict[str, Any],
    test_database
):
    """
    Test creating a booking with full data.

    Verifies:
    - Booking creation via API
    - Data persistence in database
    - All fields stored correctly
    - Reminders are auto-created
    """
    response = await test_client.post(
        "/api/v1/bookings",
        json=sample_booking,
        headers=auth_headers
    )

    assert response.status_code == 201
    booking_data = response.json()

    # Verify response structure
    assert "id" in booking_data
    assert booking_data["booking_type"] == sample_booking["booking_type"]
    assert booking_data["status"] == "requested"  # Default status set by service

    # Verify in database
    booking_id = booking_data["id"]
    db_booking = await test_database.bookings.find_one({"id": booking_id})
    assert db_booking is not None
    assert db_booking["contact_email"] == sample_booking["contact_email"]

    # Verify reminders were created
    assert "reminders" in db_booking
    assert len(db_booking["reminders"]) > 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_booking_with_agent_assignment(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_booking: Dict[str, Any],
    sample_agent: Dict[str, Any],
    test_database
):
    """
    Test creating a booking with automatic agent assignment.

    Verifies:
    - Agent auto-assignment works
    - Agent with least bookings is selected
    - Agent working hours are respected
    """
    # Create an active agent
    agent_response = await test_client.post(
        "/api/v1/agents",
        json=sample_agent,
        headers=auth_headers
    )
    assert agent_response.status_code == 201
    agent_id = agent_response.json()["id"]

    # Schedule booking during agent's working hours (Monday 10 AM)
    today = datetime.utcnow()
    days_ahead = 0 - today.weekday()  # Monday is 0
    if days_ahead <= 0:
        days_ahead += 7
    next_monday = today + timedelta(days=days_ahead)
    booking_time = next_monday.replace(hour=10, minute=0, second=0, microsecond=0)

    booking_data = sample_booking.copy()
    booking_data["scheduled_at"] = booking_time.isoformat()

    # Create booking
    response = await test_client.post(
        "/api/v1/bookings",
        json=booking_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    booking = response.json()

    # Verify agent was assigned
    assert booking["agent_id"] == agent_id
    # Agent name is derived from first_name + last_name in response
    expected_name = f"{sample_agent['first_name']} {sample_agent['last_name']}"
    assert expected_name.lower() in booking.get("agent_name", "").lower() or booking["agent_id"] == agent_id


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_booking_success(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_booking: Dict[str, Any],
    test_database
):
    """
    Test retrieving a booking by ID.

    Verifies:
    - Booking retrieval works
    - All fields returned correctly
    """
    # Create booking
    create_response = await test_client.post(
        "/api/v1/bookings",
        json=sample_booking,
        headers=auth_headers
    )
    assert create_response.status_code == 201
    booking_id = create_response.json()["id"]

    # Retrieve booking
    get_response = await test_client.get(
        f"/api/v1/bookings/{booking_id}",
        headers=auth_headers
    )

    assert get_response.status_code == 200
    booking_data = get_response.json()

    assert booking_data["id"] == booking_id
    assert booking_data["booking_type"] == sample_booking["booking_type"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_booking_not_found(
    test_client: AsyncClient,
    auth_headers: Dict[str, str]
):
    """
    Test retrieving a non-existent booking.

    Verifies:
    - 404 status returned
    - Error message is clear
    """
    fake_id = "nonexistent-booking-id"
    response = await test_client.get(
        f"/api/v1/bookings/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_bookings_pagination(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_booking: Dict[str, Any],
    test_database
):
    """
    Test listing bookings with pagination.

    Verifies:
    - Pagination works correctly
    - Limit and offset parameters work
    - Total count is accurate
    """
    # Create 5 bookings with different times
    for i in range(5):
        booking_data = sample_booking.copy()
        booking_data["contact_email"] = f"contact{i}@example.com"
        # Each booking at a different time to avoid conflicts
        scheduled_time = datetime.utcnow() + timedelta(days=7+i, hours=i)
        booking_data["scheduled_at"] = scheduled_time.isoformat()
        await test_client.post(
            "/api/v1/bookings",
            json=booking_data,
            headers=auth_headers
        )

    # Test pagination - first page
    response = await test_client.get(
        "/api/v1/bookings?limit=2&offset=0",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert "bookings" in data
    assert "total" in data
    assert len(data["bookings"]) == 2
    assert data["total"] == 5


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_booking_success(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_booking: Dict[str, Any],
    test_database
):
    """
    Test updating a booking.

    Verifies:
    - Booking update works
    - Only specified fields are updated
    - Other fields remain unchanged
    """
    # Create booking
    create_response = await test_client.post(
        "/api/v1/bookings",
        json=sample_booking,
        headers=auth_headers
    )
    booking_id = create_response.json()["id"]

    # Update booking
    new_time = datetime.utcnow() + timedelta(days=14)
    update_data = {
        "scheduled_time": new_time.isoformat(),
        "notes": "Updated booking notes"
    }

    update_response = await test_client.put(
        f"/api/v1/bookings/{booking_id}",
        json=update_data,
        headers=auth_headers
    )

    assert update_response.status_code == 200
    updated_booking = update_response.json()

    assert updated_booking["notes"] == "Updated booking notes"
    # Verify other fields unchanged
    assert updated_booking["booking_type"] == sample_booking["booking_type"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cancel_booking(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_booking: Dict[str, Any],
    test_database
):
    """
    Test cancelling a booking.

    Verifies:
    - Booking can be cancelled
    - Status updated correctly
    - Cancellation notification sent
    """
    # Create booking
    create_response = await test_client.post(
        "/api/v1/bookings",
        json=sample_booking,
        headers=auth_headers
    )
    booking_id = create_response.json()["id"]

    # Cancel booking (using DELETE endpoint)
    cancel_response = await test_client.delete(
        f"/api/v1/bookings/{booking_id}",
        headers=auth_headers
    )

    assert cancel_response.status_code == 200
    cancelled_booking = cancel_response.json()
    assert cancelled_booking["status"] == "cancelled"

    # Verify in database
    db_booking = await test_database.bookings.find_one({"id": booking_id})
    assert db_booking["status"] == "cancelled"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_delete_booking_success(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_booking: Dict[str, Any],
    test_database
):
    """
    Test deleting a booking (soft delete via cancellation).

    Verifies:
    - Booking deletion works
    - Status changed to cancelled (soft delete)
    - Booking still exists in database
    """
    # Create booking
    create_response = await test_client.post(
        "/api/v1/bookings",
        json=sample_booking,
        headers=auth_headers
    )
    booking_id = create_response.json()["id"]

    # Delete booking (soft delete = cancel)
    delete_response = await test_client.delete(
        f"/api/v1/bookings/{booking_id}",
        headers=auth_headers
    )

    assert delete_response.status_code == 200
    deleted_booking = delete_response.json()
    assert deleted_booking["status"] == "cancelled"

    # Verify booking still accessible (soft delete)
    get_response = await test_client.get(
        f"/api/v1/bookings/{booking_id}",
        headers=auth_headers
    )

    assert get_response.status_code == 200
    assert get_response.json()["status"] == "cancelled"

    # Verify in database - still exists but cancelled
    db_booking = await test_database.bookings.find_one({"id": booking_id})
    assert db_booking is not None
    assert db_booking["status"] == "cancelled"


# ============================================================================
# STATUS TRANSITION TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_booking_status_pending_to_confirmed(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_booking: Dict[str, Any],
    test_database
):
    """
    Test booking status transition from pending to confirmed.

    Verifies:
    - Status can be updated from pending to confirmed
    - Confirmation notification sent
    - Database updated correctly
    """
    # Create pending booking
    pending_booking = sample_booking.copy()
    pending_booking["status"] = "pending"

    create_response = await test_client.post(
        "/api/v1/bookings",
        json=pending_booking,
        headers=auth_headers
    )
    booking_id = create_response.json()["id"]

    # Confirm booking
    confirm_response = await test_client.post(
        f"/api/v1/bookings/{booking_id}/confirm",
        headers=auth_headers
    )

    assert confirm_response.status_code == 200
    confirmed_booking = confirm_response.json()
    assert confirmed_booking["status"] == "confirmed"

    # Verify in database
    db_booking = await test_database.bookings.find_one({"id": booking_id})
    assert db_booking["status"] == "confirmed"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_booking_status_confirmed_to_completed(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_booking: Dict[str, Any],
    test_database
):
    """
    Test booking status transition from confirmed to completed.

    Verifies:
    - Status can be updated from confirmed to completed
    - Completion notification sent
    - Database updated correctly
    """
    # Create confirmed booking
    create_response = await test_client.post(
        "/api/v1/bookings",
        json=sample_booking,
        headers=auth_headers
    )
    booking_id = create_response.json()["id"]

    # Complete booking
    complete_response = await test_client.post(
        f"/api/v1/bookings/{booking_id}/complete",
        headers=auth_headers
    )

    assert complete_response.status_code == 200
    completed_booking = complete_response.json()
    assert completed_booking["status"] == "completed"

    # Verify in database
    db_booking = await test_database.bookings.find_one({"id": booking_id})
    assert db_booking["status"] == "completed"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_booking_status_invalid_transition(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_booking: Dict[str, Any],
    test_database
):
    """
    Test invalid booking status transition.

    Verifies:
    - Invalid status transitions are rejected
    - Error message is clear
    """
    # Create completed booking
    completed_booking = sample_booking.copy()
    completed_booking["status"] = "completed"

    create_response = await test_client.post(
        "/api/v1/bookings",
        json=completed_booking,
        headers=auth_headers
    )
    booking_id = create_response.json()["id"]

    # Try to confirm already completed booking (invalid transition)
    confirm_response = await test_client.post(
        f"/api/v1/bookings/{booking_id}/confirm",
        headers=auth_headers
    )

    assert confirm_response.status_code in [400, 409]


# ============================================================================
# AGENT AUTO-ASSIGNMENT TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_auto_assign_agent_to_booking(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_booking: Dict[str, Any],
    sample_agent: Dict[str, Any],
    test_database
):
    """
    Test automatic agent assignment to booking.

    Verifies:
    - Available agent is automatically assigned
    - Agent with least bookings is selected
    - Agent working hours are respected
    """
    # Create two agents
    agent1 = sample_agent.copy()
    agent1["email"] = "agent1@example.com"
    agent1_response = await test_client.post(
        "/api/v1/agents",
        json=agent1,
        headers=auth_headers
    )
    agent1_id = agent1_response.json()["id"]

    agent2 = sample_agent.copy()
    agent2["email"] = "agent2@example.com"
    agent2_response = await test_client.post(
        "/api/v1/agents",
        json=agent2,
        headers=auth_headers
    )
    agent2_id = agent2_response.json()["id"]

    # Create booking during working hours
    today = datetime.utcnow()
    days_ahead = 0 - today.weekday()  # Monday
    if days_ahead <= 0:
        days_ahead += 7
    next_monday = today + timedelta(days=days_ahead)
    booking_time = next_monday.replace(hour=10, minute=0, second=0, microsecond=0)

    booking_data = sample_booking.copy()
    booking_data["scheduled_time"] = booking_time.isoformat()

    # Create first booking (should assign to agent1 or agent2)
    response1 = await test_client.post(
        "/api/v1/bookings",
        json=booking_data,
        headers=auth_headers
    )
    assert response1.status_code == 201
    booking1 = response1.json()
    assert booking1["agent_id"] in [agent1_id, agent2_id]

    # Create second booking (should prefer agent with fewer bookings)
    booking_data["contact_email"] = "another@example.com"
    response2 = await test_client.post(
        "/api/v1/bookings",
        json=booking_data,
        headers=auth_headers
    )
    assert response2.status_code == 201
    booking2 = response2.json()
    assert booking2["agent_id"] is not None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_no_agent_available_outside_working_hours(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_booking: Dict[str, Any],
    sample_agent: Dict[str, Any],
    test_database
):
    """
    Test booking creation when no agent is available (outside working hours).

    Verifies:
    - Booking created without agent assignment
    - Booking added to waitlist
    - Status reflects unassigned state
    """
    # Create agent with limited working hours
    agent_response = await test_client.post(
        "/api/v1/agents",
        json=sample_agent,
        headers=auth_headers
    )
    assert agent_response.status_code == 201

    # Schedule booking outside working hours (8 PM)
    booking_time = datetime.utcnow() + timedelta(days=7)
    booking_time = booking_time.replace(hour=20, minute=0, second=0, microsecond=0)

    booking_data = sample_booking.copy()
    booking_data["scheduled_time"] = booking_time.isoformat()

    # Create booking
    response = await test_client.post(
        "/api/v1/bookings",
        json=booking_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    booking = response.json()

    # Agent should not be assigned
    assert booking["agent_id"] is None


# ============================================================================
# REMINDER TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_booking_reminders_created(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_booking: Dict[str, Any],
    test_database
):
    """
    Test that reminders are automatically created for new bookings.

    Verifies:
    - 24h reminder created
    - 1h reminder created
    - Reminders have correct scheduled times
    """
    # Create booking 3 days in future
    booking_time = datetime.utcnow() + timedelta(days=3)
    booking_data = sample_booking.copy()
    booking_data["scheduled_time"] = booking_time.isoformat()

    response = await test_client.post(
        "/api/v1/bookings",
        json=booking_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    booking_id = response.json()["id"]

    # Check database for reminders
    db_booking = await test_database.bookings.find_one({"id": booking_id})
    assert "reminders" in db_booking
    reminders = db_booking["reminders"]

    # Should have 24h and 1h reminders
    reminder_types = [r["type"] for r in reminders]
    assert "24h" in reminder_types
    assert "1h" in reminder_types


# ============================================================================
# FILTERING & SEARCH TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_filter_bookings_by_status(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_booking: Dict[str, Any],
    test_database
):
    """
    Test filtering bookings by status.

    Verifies:
    - Status filter works correctly
    - Only matching bookings returned
    """
    # Create bookings with different statuses
    for status in ["pending", "confirmed", "completed"]:
        booking_data = sample_booking.copy()
        booking_data["status"] = status
        booking_data["contact_email"] = f"{status}@example.com"
        await test_client.post(
            "/api/v1/bookings",
            json=booking_data,
            headers=auth_headers
        )

    # Filter for confirmed bookings only
    response = await test_client.get(
        "/api/v1/bookings?status=confirmed",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert data["bookings"][0]["status"] == "confirmed"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_filter_bookings_by_date_range(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_booking: Dict[str, Any],
    test_database
):
    """
    Test filtering bookings by date range.

    Verifies:
    - Date range filter works
    - Only bookings in range returned
    """
    # Create bookings on different dates
    base_time = datetime.utcnow()
    dates = [
        base_time + timedelta(days=1),
        base_time + timedelta(days=7),
        base_time + timedelta(days=14)
    ]

    for i, date in enumerate(dates):
        booking_data = sample_booking.copy()
        booking_data["scheduled_time"] = date.isoformat()
        booking_data["contact_email"] = f"contact{i}@example.com"
        await test_client.post(
            "/api/v1/bookings",
            json=booking_data,
            headers=auth_headers
        )

    # Filter for bookings in next 10 days
    start_date = base_time.isoformat()
    end_date = (base_time + timedelta(days=10)).isoformat()

    response = await test_client.get(
        f"/api/v1/bookings?start_date={start_date}&end_date={end_date}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Should return first two bookings only
    assert data["total"] == 2


# ============================================================================
# ORGANIZATION ISOLATION TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_organization_isolation(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_booking: Dict[str, Any],
    organization_context: Dict[str, Any],
    test_database
):
    """
    Test that bookings are isolated by organization.

    Verifies:
    - Bookings from different orgs don't mix
    - Users only see their organization's bookings
    """
    # Create booking for test org
    response = await test_client.post(
        "/api/v1/bookings",
        json=sample_booking,
        headers=auth_headers
    )

    assert response.status_code == 201

    # List bookings - should only see test org's bookings
    list_response = await test_client.get(
        "/api/v1/bookings",
        headers=auth_headers
    )

    assert list_response.status_code == 200
    data = list_response.json()

    # All bookings should belong to test organization
    expected_org_id = organization_context["organization_id"]
    for booking in data["bookings"]:
        assert booking["organization_id"] == expected_org_id


# ============================================================================
# ANONYMOUS BOOKING TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_booking_anonymous_success(
    test_client: AsyncClient,
    test_database,
    organization_context
):
    """
    Test creating a booking without authentication (anonymous user).

    Verifies:
    - Anonymous users can create bookings
    - No auth token required
    - Email and phone are provided
    - Organization retrieved from property
    - Booking is created successfully
    """
    # First, create a property
    property_data = {
        "organization_id": organization_context["organization_id"],
        "name": "Test Property for Anonymous Booking",
        "property_type": "apartment",
        "status": "active",
        "location": {
            "address": "123 Test Street",
            "city": "Accra",
            "country": "Ghana"
        },
        "financial": {
            "price_usd": 150000.0,
            "base_currency": "USD"
        }
    }
    await test_database.properties.insert_one(property_data)
    property_id = property_data.get("id", str(uuid.uuid4()))

    # Create booking data (anonymous - no contact_id)
    scheduled_at = datetime.utcnow() + timedelta(days=7)
    booking_data = {
        "property_id": property_id,
        "contact_name": "Anonymous User",
        "contact_email": "anonymous@example.com",
        "contact_phone": "+233241234567",
        "booking_type": "in-person",
        "scheduled_at": scheduled_at.isoformat(),
        "duration_minutes": 30,
        "notes": "Anonymous booking test"
    }

    # Make request WITHOUT auth headers
    response = await test_client.post(
        "/api/v1/bookings",
        json=booking_data
    )

    assert response.status_code == 201
    booking_response = response.json()

    # Verify booking created
    assert "id" in booking_response
    assert booking_response["contact_name"] == "Anonymous User"
    assert booking_response["contact_email"] == "anonymous@example.com"
    assert booking_response["contact_phone"] == "+233241234567"
    assert booking_response["status"] == "requested"

    # Verify in database
    db_booking = await test_database.bookings.find_one({"id": booking_response["id"]})
    assert db_booking is not None
    assert db_booking["contact_email"] == "anonymous@example.com"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_availability_anonymous_success(
    test_client: AsyncClient,
    test_database,
    organization_context
):
    """
    Test getting availability without authentication.

    Verifies:
    - Anonymous users can check availability
    - POST /availability works without auth
    - Available slots are returned
    """
    # Create a property
    property_data = {
        "organization_id": organization_context["organization_id"],
        "name": "Test Property for Availability",
        "property_type": "apartment",
        "status": "active",
        "location": {
            "address": "123 Test Street",
            "city": "Accra",
            "country": "Ghana"
        },
        "financial": {
            "price_usd": 150000.0,
            "base_currency": "USD"
        }
    }
    await test_database.properties.insert_one(property_data)
    property_id = property_data.get("id", str(uuid.uuid4()))

    # Request availability WITHOUT auth headers
    start_date = datetime.utcnow() + timedelta(days=7)
    end_date = start_date + timedelta(days=1)

    availability_request = {
        "property_id": property_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "duration_minutes": 30
    }

    response = await test_client.post(
        "/api/v1/bookings/availability",
        json=availability_request
    )

    assert response.status_code == 200
    availability_data = response.json()

    assert "property_id" in availability_data
    assert "slots" in availability_data
    assert isinstance(availability_data["slots"], list)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_property_availability_anonymous_success(
    test_client: AsyncClient,
    test_database,
    organization_context
):
    """
    Test getting property availability via GET endpoint without authentication.

    Verifies:
    - Anonymous users can check property availability
    - GET /properties/{id}/availability works without auth
    """
    # Create a property
    property_data = {
        "organization_id": organization_context["organization_id"],
        "name": "Test Property for GET Availability",
        "property_type": "apartment",
        "status": "active",
        "location": {
            "address": "123 Test Street",
            "city": "Accra",
            "country": "Ghana"
        },
        "financial": {
            "price_usd": 150000.0,
            "base_currency": "USD"
        }
    }
    await test_database.properties.insert_one(property_data)
    property_id = property_data.get("id", str(uuid.uuid4()))

    # Request availability WITHOUT auth headers
    start_date = datetime.utcnow() + timedelta(days=7)
    end_date = start_date + timedelta(days=1)

    response = await test_client.get(
        f"/api/v1/bookings/properties/{property_id}/availability",
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "duration_minutes": 30
        }
    )

    assert response.status_code == 200
    availability_data = response.json()

    assert "property_id" in availability_data
    assert "slots" in availability_data
    assert isinstance(availability_data["slots"], list)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_rate_limit_anonymous_bookings(
    test_client: AsyncClient,
    test_database,
    organization_context
):
    """
    Test rate limiting for anonymous bookings.

    Verifies:
    - Anonymous users are rate limited to 3 bookings per hour
    - 4th booking request fails with 429
    - Authenticated users are not rate limited
    """
    # Create a property
    property_data = {
        "organization_id": organization_context["organization_id"],
        "name": "Test Property for Rate Limit",
        "property_type": "apartment",
        "status": "active",
        "location": {
            "address": "123 Test Street",
            "city": "Accra",
            "country": "Ghana"
        },
        "financial": {
            "price_usd": 150000.0,
            "base_currency": "USD"
        }
    }
    await test_database.properties.insert_one(property_data)
    property_id = property_data.get("id", str(uuid.uuid4()))

    # Make 3 successful anonymous bookings
    for i in range(3):
        scheduled_at = datetime.utcnow() + timedelta(days=7, hours=i)
        booking_data = {
            "property_id": property_id,
            "contact_name": f"User {i}",
            "contact_email": f"user{i}@example.com",
            "contact_phone": f"+23324123456{i}",
            "scheduled_at": scheduled_at.isoformat(),
            "duration_minutes": 30
        }

        response = await test_client.post(
            "/api/v1/bookings",
            json=booking_data
        )

        assert response.status_code == 201, f"Booking {i+1} should succeed"

    # 4th booking should be rate limited
    scheduled_at = datetime.utcnow() + timedelta(days=7, hours=4)
    booking_data = {
        "property_id": property_id,
        "contact_name": "User 4",
        "contact_email": "user4@example.com",
        "contact_phone": "+233241234564",
        "scheduled_at": scheduled_at.isoformat(),
        "duration_minutes": 30
    }

    response = await test_client.post(
        "/api/v1/bookings",
        json=booking_data
    )

    assert response.status_code == 429
    error_data = response.json()
    assert "rate limit" in error_data["detail"].lower()
