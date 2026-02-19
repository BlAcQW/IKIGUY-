"""
Integration test script for session time fields and registration update API endpoints.

Tests the complete CRUD cycle for sessions with time fields and registration updates
using real API calls and real data in the database.

This script tests:
1. Session CRUD with start_time and end_time fields
2. Registration UPDATE operations for all editable fields
3. SessionDetail GET endpoint
4. Data persistence and retrieval

Usage:
    python scripts/test_session_registration_api_crud.py
"""

import requests
import json
from datetime import datetime, timedelta
from bson import ObjectId


# API Configuration
API_BASE_URL = "https://churchflow-api.ailabsafrica.com/api/v1"
# For local testing, use:
# API_BASE_URL = "http://localhost:30030/api/v1"

# Test credentials - use actual test credentials
# This will need a valid token for authenticated endpoints
TEST_TOKEN = None  # Will be set if available from login


def print_test_header(test_name):
    """Print formatted test header."""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")


def print_result(success, message, data=None):
    """Print formatted test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if data and not success:  # Only print data on failure for debugging
        print(f"Data: {json.dumps(data, indent=2, default=str)}")


def get_headers(with_auth=False):
    """Get request headers."""
    headers = {"Content-Type": "application/json"}
    if with_auth and TEST_TOKEN:
        headers["Authorization"] = f"Bearer {TEST_TOKEN}"
    return headers


def test_create_conference():
    """Create a test conference for testing."""
    print_test_header("Create Test Conference")

    start_date = datetime.now() + timedelta(days=30)
    end_date = start_date + timedelta(days=2)

    data = {
        "name": f"API Test Conference {datetime.now().strftime('%Y%m%d%H%M%S')}",
        "description": "Test conference for API CRUD tests",
        "venue": "Test Venue",
        "venue_latitude": 5.6037,
        "venue_longitude": -0.1870,
        "venue_checkin_radius": 1000,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "registration_open": True,
        "self_checkin_enabled": True,
        "max_attendees": 100
    }

    response = requests.post(
        f"{API_BASE_URL}/conferences",
        headers=get_headers(with_auth=True),
        json=data
    )

    if response.status_code == 201:
        conference = response.json()
        print_result(True, f"Conference created: {conference['id']}")
        return conference
    else:
        print_result(False, f"Failed to create conference: {response.status_code}", response.json())
        return None


def test_session_crud_with_time_fields(conference_id):
    """Test complete CRUD cycle for sessions with time fields."""

    # TEST 1: Create session with time fields
    print_test_header("Create Session with Time Fields")

    session_date = datetime.now() + timedelta(days=30)
    create_data = {
        "name": "Morning Worship with Times",
        "description": "Test session with start and end times",
        "location": "Main Auditorium",
        "day_number": 1,
        "day_label": "Day 1 - Opening",
        "session_date": session_date.isoformat(),
        "start_time": "09:00",
        "end_time": "11:30",
        "order": 1,
        "sms_confirmation_enabled": True,
        "sms_confirmation_template": "Hi {name}, you're checked in to {session_name}!"
    }

    response = requests.post(
        f"{API_BASE_URL}/conferences/{conference_id}/sessions",
        headers=get_headers(with_auth=True),
        json=create_data
    )

    if response.status_code != 201:
        print_result(False, f"Failed to create session: {response.status_code}", response.json())
        return None

    session = response.json()
    session_id = session["id"]

    # Verify time fields are present
    has_times = "start_time" in session and "end_time" in session
    print_result(
        has_times and session["start_time"] == "09:00" and session["end_time"] == "11:30",
        f"Session created with time fields: {session_id}"
    )

    # TEST 2: Retrieve session and verify time fields
    print_test_header("Retrieve Session with Time Fields")

    response = requests.get(
        f"{API_BASE_URL}/conferences/{conference_id}/sessions/{session_id}",
        headers=get_headers()
    )

    if response.status_code != 200:
        print_result(False, f"Failed to retrieve session: {response.status_code}", response.json())
        return None

    retrieved = response.json()
    times_match = (
        retrieved.get("start_time") == "09:00" and
        retrieved.get("end_time") == "11:30"
    )
    print_result(times_match, "Session retrieved with correct time fields")

    # TEST 3: Update session time fields
    print_test_header("Update Session Time Fields")

    update_data = {
        "start_time": "10:00",
        "end_time": "12:00"
    }

    response = requests.put(
        f"{API_BASE_URL}/conferences/{conference_id}/sessions/{session_id}",
        headers=get_headers(with_auth=True),
        json=update_data
    )

    if response.status_code != 200:
        print_result(False, f"Failed to update session: {response.status_code}", response.json())
        return None

    updated = response.json()
    times_updated = (
        updated.get("start_time") == "10:00" and
        updated.get("end_time") == "12:00"
    )
    print_result(times_updated, "Session time fields updated successfully")

    # TEST 4: List sessions and verify times included
    print_test_header("List Sessions with Time Fields")

    response = requests.get(
        f"{API_BASE_URL}/conferences/{conference_id}/sessions",
        headers=get_headers()
    )

    if response.status_code != 200:
        print_result(False, f"Failed to list sessions: {response.status_code}", response.json())
        return None

    sessions_list = response.json()
    found_session = next(
        (s for s in sessions_list.get("sessions", []) if s["id"] == session_id),
        None
    )

    if found_session:
        has_correct_times = (
            found_session.get("start_time") == "10:00" and
            found_session.get("end_time") == "12:00"
        )
        print_result(has_correct_times, "Session in list has correct time fields")
    else:
        print_result(False, "Session not found in list")

    # TEST 5: Create session without time fields (backwards compatibility)
    print_test_header("Create Session without Time Fields (Backwards Compatibility)")

    create_data_no_times = {
        "name": "Evening Session No Times",
        "description": "Test backwards compatibility",
        "location": "Chapel",
        "day_number": 1,
        "day_label": "Day 1",
        "session_date": session_date.isoformat(),
        "order": 2
    }

    response = requests.post(
        f"{API_BASE_URL}/conferences/{conference_id}/sessions",
        headers=get_headers(with_auth=True),
        json=create_data_no_times
    )

    if response.status_code == 201:
        session_no_times = response.json()
        # Should not have time fields or they should be null
        compatible = (
            session_no_times.get("start_time") is None and
            session_no_times.get("end_time") is None
        )
        print_result(compatible, "Session created without time fields (backwards compatible)")
    else:
        print_result(False, f"Failed to create session without times: {response.status_code}", response.json())

    # TEST 6: Delete session
    print_test_header("Delete Session")

    response = requests.delete(
        f"{API_BASE_URL}/conferences/{conference_id}/sessions/{session_id}",
        headers=get_headers(with_auth=True)
    )

    deleted = response.status_code == 204
    print_result(deleted, f"Session deleted: {session_id}")

    # Verify deletion
    response = requests.get(
        f"{API_BASE_URL}/conferences/{conference_id}/sessions/{session_id}",
        headers=get_headers()
    )

    not_found = response.status_code == 404
    print_result(not_found, "Verified session is deleted (404)")

    return session_no_times["id"] if 'session_no_times' in locals() else None


def test_registration_update_crud(conference_id):
    """Test complete CRUD cycle for registration updates."""

    # TEST 1: Create a registration first
    print_test_header("Create Test Registration")

    reg_data = {
        "user_name": "Original Test User",
        "user_phone": "+233244123456",
        "user_email": "original@test.com",
        "church_name": "Original Church",
        "special_needs": "Original special needs"
    }

    response = requests.post(
        f"{API_BASE_URL}/conferences/{conference_id}/register",
        headers=get_headers(),
        json=reg_data
    )

    if response.status_code != 201:
        print_result(False, f"Failed to create registration: {response.status_code}", response.json())
        return None

    registration = response.json()
    reg_id = registration["id"]
    print_result(True, f"Registration created: {reg_id}")

    # TEST 2: Update registration name
    print_test_header("Update Registration Name")

    update_data = {"user_name": "Updated Test User"}

    response = requests.put(
        f"{API_BASE_URL}/registrations/{reg_id}",
        headers=get_headers(with_auth=True),
        json=update_data
    )

    if response.status_code != 200:
        print_result(False, f"Failed to update name: {response.status_code}", response.json())
    else:
        updated = response.json()
        name_updated = updated["user_name"] == "Updated Test User"
        print_result(name_updated, "Registration name updated")

    # TEST 3: Update registration phone
    print_test_header("Update Registration Phone")

    update_data = {"user_phone": "0201234567"}  # Local format

    response = requests.put(
        f"{API_BASE_URL}/registrations/{reg_id}",
        headers=get_headers(with_auth=True),
        json=update_data
    )

    if response.status_code != 200:
        print_result(False, f"Failed to update phone: {response.status_code}", response.json())
    else:
        updated = response.json()
        # Phone should be normalized to +233201234567
        phone_updated = updated["user_phone"] == "+233201234567"
        print_result(phone_updated, "Registration phone updated and normalized")

    # TEST 4: Update registration email
    print_test_header("Update Registration Email")

    update_data = {"user_email": "updated@test.com"}

    response = requests.put(
        f"{API_BASE_URL}/registrations/{reg_id}",
        headers=get_headers(with_auth=True),
        json=update_data
    )

    if response.status_code != 200:
        print_result(False, f"Failed to update email: {response.status_code}", response.json())
    else:
        updated = response.json()
        email_updated = updated.get("user_email") == "updated@test.com"
        print_result(email_updated, "Registration email updated")

    # TEST 5: Update church name and special needs
    print_test_header("Update Church Name and Special Needs")

    update_data = {
        "church_name": "Updated Church Name",
        "special_needs": "Updated special needs: Wheelchair access"
    }

    response = requests.put(
        f"{API_BASE_URL}/registrations/{reg_id}",
        headers=get_headers(with_auth=True),
        json=update_data
    )

    if response.status_code != 200:
        print_result(False, f"Failed to update fields: {response.status_code}", response.json())
    else:
        updated = response.json()
        fields_updated = (
            updated.get("church_name") == "Updated Church Name" and
            updated.get("special_needs") == "Updated special needs: Wheelchair access"
        )
        print_result(fields_updated, "Church name and special needs updated")

    # TEST 6: Update multiple fields at once
    print_test_header("Update Multiple Registration Fields")

    update_data = {
        "user_name": "Final Updated Name",
        "user_phone": "0244555666",
        "user_email": "final@test.com",
        "church_name": "Final Church",
        "special_needs": "Final needs"
    }

    response = requests.put(
        f"{API_BASE_URL}/registrations/{reg_id}",
        headers=get_headers(with_auth=True),
        json=update_data
    )

    if response.status_code != 200:
        print_result(False, f"Failed to update multiple fields: {response.status_code}", response.json())
    else:
        updated = response.json()
        all_updated = (
            updated["user_name"] == "Final Updated Name" and
            updated["user_phone"] == "+233244555666" and
            updated.get("user_email") == "final@test.com" and
            updated.get("church_name") == "Final Church" and
            updated.get("special_needs") == "Final needs"
        )
        print_result(all_updated, "Multiple fields updated simultaneously")

    # TEST 7: Retrieve registration and verify all updates persisted
    print_test_header("Verify Registration Updates Persisted")

    response = requests.get(
        f"{API_BASE_URL}/registrations/{reg_id}",
        headers=get_headers()
    )

    if response.status_code != 200:
        print_result(False, f"Failed to retrieve registration: {response.status_code}", response.json())
    else:
        retrieved = response.json()
        all_persisted = (
            retrieved["user_name"] == "Final Updated Name" and
            retrieved["user_phone"] == "+233244555666" and
            retrieved.get("user_email") == "final@test.com" and
            retrieved.get("church_name") == "Final Church" and
            retrieved.get("special_needs") == "Final needs"
        )
        print_result(all_persisted, "All updates persisted correctly")

    return reg_id


def main():
    """Run all integration tests."""
    print("\n" + "="*80)
    print("ChurchFlow API Integration Tests - Session Time Fields & Registration Updates")
    print("="*80)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Note: These tests require authentication
    # In production, you would first authenticate and get a token
    print("\n⚠️  NOTE: These tests require authentication for write operations")
    print("Update TEST_TOKEN variable with a valid admin token to run full tests\n")

    # Create test conference
    conference = test_create_conference()

    if not conference:
        print("\n❌ Failed to create test conference. Aborting tests.")
        return

    conference_id = conference["id"]

    try:
        # Test session CRUD with time fields
        print("\n" + "="*80)
        print("SESSION TIME FIELDS TESTS")
        print("="*80)
        test_session_crud_with_time_fields(conference_id)

        # Test registration update CRUD
        print("\n" + "="*80)
        print("REGISTRATION UPDATE TESTS")
        print("="*80)
        test_registration_update_crud(conference_id)

    except Exception as e:
        print(f"\n❌ Test execution error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print(f"Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print("\n✅ All test categories executed")
    print("Review output above for individual test results")


if __name__ == "__main__":
    main()
