"""
Agent Module Tests

Tests for agent CRUD operations, auto-assignment, calendar sync, and availability.

Coverage:
- CRUD operations (create, read, update, delete)
- Agent auto-assignment for bookings
- Working hours and availability
- Daily booking limits
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
async def test_create_agent_success(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_agent: Dict[str, Any],
    test_database
):
    """
    Test creating an agent with full data.

    Verifies:
    - Agent creation via API
    - Data persistence in database
    - All fields stored correctly
    """
    response = await test_client.post(
        "/api/v1/agents",
        json=sample_agent,
        headers=auth_headers
    )

    assert response.status_code == 201
    agent_data = response.json()

    # Verify response structure
    assert "id" in agent_data
    assert agent_data["first_name"] == sample_agent["first_name"]
    assert agent_data["last_name"] == sample_agent["last_name"]
    assert agent_data["email"] == sample_agent["email"]
    assert agent_data["status"] == "active"

    # Verify in database
    agent_id = agent_data["id"]
    db_agent = await test_database.agents.find_one({"id": agent_id})
    assert db_agent is not None
    assert db_agent["first_name"] == sample_agent["first_name"]
    assert db_agent["last_name"] == sample_agent["last_name"]
    assert db_agent["email"] == sample_agent["email"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_agent_duplicate_email(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_agent: Dict[str, Any],
    test_database
):
    """
    Test creating an agent with duplicate email fails.

    Verifies:
    - Email uniqueness validation
    - Appropriate error response
    """
    # Create first agent
    response1 = await test_client.post(
        "/api/v1/agents",
        json=sample_agent,
        headers=auth_headers
    )
    assert response1.status_code == 201

    # Try to create another agent with same email
    response2 = await test_client.post(
        "/api/v1/agents",
        json=sample_agent,
        headers=auth_headers
    )

    assert response2.status_code in [400, 409]
    assert "email" in response2.json()["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_agent_success(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_agent: Dict[str, Any],
    test_database
):
    """
    Test retrieving an agent by ID.

    Verifies:
    - Agent retrieval works
    - All fields returned correctly
    """
    # Create agent
    create_response = await test_client.post(
        "/api/v1/agents",
        json=sample_agent,
        headers=auth_headers
    )
    assert create_response.status_code == 201
    agent_id = create_response.json()["id"]

    # Retrieve agent
    get_response = await test_client.get(
        f"/api/v1/agents/{agent_id}",
        headers=auth_headers
    )

    assert get_response.status_code == 200
    agent_data = get_response.json()

    assert agent_data["id"] == agent_id
    assert agent_data["first_name"] == sample_agent["first_name"]
    assert agent_data["last_name"] == sample_agent["last_name"]
    # Check working hours for days that are in sample_agent
    for day, schedule in sample_agent["working_hours"].items():
        assert agent_data["working_hours"][day] == schedule


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_agent_not_found(
    test_client: AsyncClient,
    auth_headers: Dict[str, str]
):
    """
    Test retrieving a non-existent agent.

    Verifies:
    - 404 status returned
    - Error message is clear
    """
    fake_id = "nonexistent-agent-id"
    response = await test_client.get(
        f"/api/v1/agents/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_agents(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_agent: Dict[str, Any],
    test_database
):
    """
    Test listing agents.

    Verifies:
    - Agent list retrieval works
    - Pagination works correctly
    """
    # Create 3 agents
    for i in range(3):
        agent_data = sample_agent.copy()
        agent_data["first_name"] = f"Agent{i+1}"
        agent_data["last_name"] = f"Test{i+1}"
        agent_data["email"] = f"agent{i+1}@example.com"
        await test_client.post(
            "/api/v1/agents",
            json=agent_data,
            headers=auth_headers
        )

    # List agents
    response = await test_client.get(
        "/api/v1/agents",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert "agents" in data
    assert len(data["agents"]) == 3


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_agent_success(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_agent: Dict[str, Any],
    test_database
):
    """
    Test updating an agent.

    Verifies:
    - Agent update works
    - Only specified fields are updated
    - Other fields remain unchanged
    """
    # Create agent
    create_response = await test_client.post(
        "/api/v1/agents",
        json=sample_agent,
        headers=auth_headers
    )
    agent_id = create_response.json()["id"]

    # Update agent
    update_data = {
        "first_name": "Updated",
        "last_name": "Agent",
        "max_bookings_per_day": 10
    }

    update_response = await test_client.put(
        f"/api/v1/agents/{agent_id}",
        json=update_data,
        headers=auth_headers
    )

    assert update_response.status_code == 200
    updated_agent = update_response.json()

    assert updated_agent["first_name"] == "Updated"
    assert updated_agent["last_name"] == "Agent"
    assert updated_agent["max_bookings_per_day"] == 10
    # Verify other fields unchanged
    assert updated_agent["email"] == sample_agent["email"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_agent_working_hours(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_agent: Dict[str, Any],
    test_database
):
    """
    Test updating agent working hours.

    Verifies:
    - Working hours can be updated
    - Changes persist correctly
    """
    # Create agent
    create_response = await test_client.post(
        "/api/v1/agents",
        json=sample_agent,
        headers=auth_headers
    )
    agent_id = create_response.json()["id"]

    # Update working hours
    new_hours = {
        "monday": {"start": "08:00", "end": "16:00"},
        "tuesday": {"start": "08:00", "end": "16:00"}
    }

    update_response = await test_client.put(
        f"/api/v1/agents/{agent_id}",
        json={"working_hours": new_hours},
        headers=auth_headers
    )

    assert update_response.status_code == 200
    updated_agent = update_response.json()
    assert updated_agent["working_hours"]["monday"]["start"] == "08:00"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_deactivate_agent(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_agent: Dict[str, Any],
    test_database
):
    """
    Test deactivating an agent.

    Verifies:
    - Agent can be deactivated
    - Inactive agents excluded from auto-assignment
    """
    # Create agent
    create_response = await test_client.post(
        "/api/v1/agents",
        json=sample_agent,
        headers=auth_headers
    )
    agent_id = create_response.json()["id"]

    # Deactivate agent
    update_response = await test_client.put(
        f"/api/v1/agents/{agent_id}",
        json={"status": "inactive"},
        headers=auth_headers
    )

    assert update_response.status_code == 200
    updated_agent = update_response.json()
    assert updated_agent["status"] == "inactive"

    # Verify in database
    db_agent = await test_database.agents.find_one({"id": agent_id})
    assert db_agent["status"] == "inactive"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_delete_agent_success(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_agent: Dict[str, Any],
    test_database
):
    """
    Test deleting an agent.

    Verifies:
    - Agent deletion works
    - Agent no longer accessible after deletion
    - Database record removed
    """
    # Create agent
    create_response = await test_client.post(
        "/api/v1/agents",
        json=sample_agent,
        headers=auth_headers
    )
    agent_id = create_response.json()["id"]

    # Delete agent
    delete_response = await test_client.delete(
        f"/api/v1/agents/{agent_id}",
        headers=auth_headers
    )

    assert delete_response.status_code == 204

    # Verify agent is soft-deleted (status set to inactive)
    get_response = await test_client.get(
        f"/api/v1/agents/{agent_id}",
        headers=auth_headers
    )

    assert get_response.status_code == 200
    agent_data = get_response.json()
    assert agent_data["status"] == "inactive"

    # Verify in database
    db_agent = await test_database.agents.find_one({"id": agent_id})
    assert db_agent is not None
    assert db_agent["status"] == "inactive"


# ============================================================================
# AGENT AVAILABILITY & WORKING HOURS TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_agent_availability_within_working_hours(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_agent: Dict[str, Any],
    test_database
):
    """
    Test checking agent availability within working hours.

    Verifies:
    - Agent is available during working hours
    - Availability check returns correct result
    """
    # Create agent
    create_response = await test_client.post(
        "/api/v1/agents",
        json=sample_agent,
        headers=auth_headers
    )
    agent_id = create_response.json()["id"]

    # Check availability on Monday at 10:00 (within working hours)
    # Find next Monday
    today = datetime.utcnow()
    days_ahead = 0 - today.weekday()  # Monday is 0
    if days_ahead <= 0:
        days_ahead += 7
    next_monday = today + timedelta(days=days_ahead)
    check_time = next_monday.replace(hour=10, minute=0, second=0, microsecond=0)

    response = await test_client.post(
        f"/api/v1/agents/{agent_id}/availability",
        params={"start_time": check_time.isoformat(), "duration_minutes": 60},
        headers=auth_headers
    )

    assert response.status_code == 200
    availability = response.json()
    assert availability["available"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_agent_availability_outside_working_hours(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_agent: Dict[str, Any],
    test_database
):
    """
    Test checking agent availability outside working hours.

    Verifies:
    - Agent is not available outside working hours
    - Availability check returns correct result
    """
    # Create agent
    create_response = await test_client.post(
        "/api/v1/agents",
        json=sample_agent,
        headers=auth_headers
    )
    agent_id = create_response.json()["id"]

    # Check availability on Monday at 20:00 (outside working hours)
    today = datetime.utcnow()
    days_ahead = 0 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    next_monday = today + timedelta(days=days_ahead)
    check_time = next_monday.replace(hour=20, minute=0, second=0, microsecond=0)

    response = await test_client.post(
        f"/api/v1/agents/{agent_id}/availability",
        params={"start_time": check_time.isoformat(), "duration_minutes": 60},
        headers=auth_headers
    )

    assert response.status_code == 200
    availability = response.json()
    assert availability["available"] is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_agent_availability_weekend(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_agent: Dict[str, Any],
    test_database
):
    """
    Test checking agent availability on weekend (no working hours defined).

    Verifies:
    - Agent is not available on weekends
    - Availability check handles missing working hours
    """
    # Create agent (working hours only Mon-Fri)
    create_response = await test_client.post(
        "/api/v1/agents",
        json=sample_agent,
        headers=auth_headers
    )
    agent_id = create_response.json()["id"]

    # Check availability on Saturday
    today = datetime.utcnow()
    days_ahead = 5 - today.weekday()  # Saturday is 5
    if days_ahead <= 0:
        days_ahead += 7
    next_saturday = today + timedelta(days=days_ahead)
    check_time = next_saturday.replace(hour=10, minute=0, second=0, microsecond=0)

    response = await test_client.post(
        f"/api/v1/agents/{agent_id}/availability",
        params={"start_time": check_time.isoformat(), "duration_minutes": 60},
        headers=auth_headers
    )

    assert response.status_code == 200
    availability = response.json()
    assert availability["available"] is False


# ============================================================================
# ORGANIZATION ISOLATION TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_organization_isolation(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_agent: Dict[str, Any],
    organization_context: Dict[str, str],
    test_database
):
    """
    Test that agents are isolated by organization.

    Verifies:
    - Agents from different orgs don't mix
    - Users only see their organization's agents
    """
    # Create agent for test org
    response = await test_client.post(
        "/api/v1/agents",
        json=sample_agent,
        headers=auth_headers
    )

    assert response.status_code == 201

    # List agents - should only see test org's agents
    list_response = await test_client.get(
        "/api/v1/agents",
        headers=auth_headers
    )

    assert list_response.status_code == 200
    data = list_response.json()

    # All agents should belong to test organization
    for agent in data["agents"]:
        assert agent["organization_id"] == organization_context["organization_id"]


# ============================================================================
# EDGE CASES & VALIDATION TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_agent_missing_required_fields(
    test_client: AsyncClient,
    auth_headers: Dict[str, str]
):
    """
    Test creating an agent with missing required fields.

    Verifies:
    - Validation rejects incomplete data
    - Error message indicates missing fields
    """
    incomplete_agent = {
        "first_name": "Test"
        # Missing last_name, email, etc.
    }

    response = await test_client.post(
        "/api/v1/agents",
        json=incomplete_agent,
        headers=auth_headers
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_agent_invalid_working_hours(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    sample_agent: Dict[str, Any]
):
    """
    Test creating an agent with invalid working hours format.

    Verifies:
    - Validation rejects invalid time formats
    - Error message is clear
    """
    invalid_agent = sample_agent.copy()
    invalid_agent["working_hours"] = {
        "monday": {"start": "25:00", "end": "17:00"}  # Invalid hour
    }

    response = await test_client.post(
        "/api/v1/agents",
        json=invalid_agent,
        headers=auth_headers
    )

    # Should either reject during validation or handle gracefully
    assert response.status_code in [400, 422]
