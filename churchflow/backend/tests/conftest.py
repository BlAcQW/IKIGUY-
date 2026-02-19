"""
Pytest configuration and fixtures for ChurchFlow tests.
"""

import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId

# Test database configuration
TEST_MONGODB_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow_test?authSource=admin"


@pytest.fixture(scope="function")
async def test_db():
    """
    Create test database connection and clean up before each test.

    Creates a fresh client for each test to ensure proper event loop binding.

    Yields:
        AsyncIOMotorClient database instance
    """
    # Create a new client for each test (function-scoped)
    client = AsyncIOMotorClient(TEST_MONGODB_URL)
    db = client.get_database()

    # Clean up before test (fresh state for each test)
    await db.users.delete_many({})
    await db.conferences.delete_many({})
    await db.conference_registrations.delete_many({})
    await db.conference_sessions.delete_many({})
    await db.session_attendance.delete_many({})
    await db.bus_routes.delete_many({})
    await db.bus_registrations.delete_many({})
    await db.branches.delete_many({})
    await db.organizations.delete_many({})
    await db.cell_groups.delete_many({})
    await db.zones.delete_many({})
    await db.departments.delete_many({})
    await db.journey_stages.delete_many({})
    await db.scheduled_communications.delete_many({})
    await db.donations.delete_many({})
    await db.groups.delete_many({})
    await db.subgroups.delete_many({})
    await db.first_timers.delete_many({})
    await db.announcements.delete_many({})

    yield db

    # Clean up after test
    await db.users.delete_many({})
    await db.conferences.delete_many({})
    await db.conference_registrations.delete_many({})
    await db.conference_sessions.delete_many({})
    await db.session_attendance.delete_many({})
    await db.bus_routes.delete_many({})
    await db.bus_registrations.delete_many({})
    await db.branches.delete_many({})
    await db.organizations.delete_many({})
    await db.cell_groups.delete_many({})
    await db.zones.delete_many({})
    await db.departments.delete_many({})
    await db.journey_stages.delete_many({})
    await db.scheduled_communications.delete_many({})
    await db.donations.delete_many({})
    await db.groups.delete_many({})
    await db.subgroups.delete_many({})
    await db.first_timers.delete_many({})
    await db.announcements.delete_many({})

    # Close the client
    client.close()


@pytest.fixture
async def sample_user(test_db):
    """
    Create sample user for testing.

    Args:
        test_db: Test database fixture

    Returns:
        User document with _id
    """
    user_data = {
        "name": "Test User",
        "phone": "+233200000001",
        "roles": ["member"],
        "created_at": datetime.utcnow()
    }
    result = await test_db.users.insert_one(user_data)
    user_data["_id"] = result.inserted_id
    return user_data


@pytest.fixture
async def sample_conference(test_db):
    """
    Create sample conference for testing.

    Args:
        test_db: Test database fixture

    Returns:
        Conference document with _id
    """
    conf_data = {
        "name": "Test Conference 2025",
        "description": "Test conference description",
        "start_date": datetime(2025, 12, 25),
        "end_date": datetime(2025, 12, 27),
        "venue": "Test Venue",
        "registration_open": True,
        "max_attendees": 100,
        "current_attendees": 0,
        "status": "upcoming",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.conferences.insert_one(conf_data)
    conf_data["_id"] = result.inserted_id
    return conf_data


@pytest.fixture
async def sample_session(test_db, sample_conference):
    """
    Create sample conference session for testing.

    Args:
        test_db: Test database fixture
        sample_conference: Conference fixture

    Returns:
        Session document with _id
    """
    session_data = {
        "conference_id": sample_conference["_id"],
        "name": "Opening Worship",
        "description": "Morning worship session",
        "location": "Main Auditorium",
        "day_number": 1,
        "day_label": "Day 1",
        "session_date": datetime(2025, 12, 25, 9, 0),
        "order": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.conference_sessions.insert_one(session_data)
    session_data["_id"] = result.inserted_id
    return session_data


@pytest.fixture
async def sample_registration(test_db, sample_conference):
    """
    Create sample conference registration for testing.

    Args:
        test_db: Test database fixture
        sample_conference: Conference fixture

    Returns:
        Registration document with _id
    """
    reg_data = {
        "conference_id": sample_conference["_id"],
        "user_name": "Test Attendee",
        "user_phone": "+233244123456",
        "user_email": "test@example.com",
        "registration_code": "REG-TEST12345",
        "status": "confirmed",
        "checked_in": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.conference_registrations.insert_one(reg_data)
    reg_data["_id"] = result.inserted_id
    return reg_data


@pytest.fixture
async def sample_bus_route(test_db, sample_conference):
    """
    Create sample bus route for testing.

    Args:
        test_db: Test database fixture
        sample_conference: Conference fixture

    Returns:
        Bus route document with _id
    """
    route_data = {
        "route_name": "Legon Bus #1",
        "pickup_location": "Legon Campus Gate",
        "departure_time": datetime(2025, 12, 25, 7, 0),
        "capacity": 50,
        "registered_count": 0,
        "conference_id": sample_conference["_id"],
        "driver_name": "Test Driver",
        "driver_phone": "+233200000010",
        "status": "scheduled",
        "gate_number": "Gate 1",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.bus_routes.insert_one(route_data)
    route_data["_id"] = result.inserted_id
    return route_data


@pytest.fixture
async def sample_branch(test_db):
    """
    Create sample branch for testing.

    Args:
        test_db: Test database fixture

    Returns:
        Branch document with _id
    """
    branch_data = {
        "name": "Adenta",
        "location": "Adenta, Greater Accra, Ghana",
        "region": "Greater Accra",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.branches.insert_one(branch_data)
    branch_data["_id"] = result.inserted_id
    return branch_data


@pytest.fixture
async def sample_conference_with_gps(test_db):
    """
    Create sample conference with GPS venue coordinates for testing.

    Args:
        test_db: Test database fixture

    Returns:
        Conference document with _id and venue GPS
    """
    from datetime import timedelta
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    conf_data = {
        "name": "GPS Conference 2025",
        "description": "Conference with venue GPS coordinates",
        "start_date": today,
        "end_date": today + timedelta(days=2),
        "venue": "Test Venue with GPS",
        "venue_latitude": 5.6037,  # Accra coordinates
        "venue_longitude": -0.1870,
        "venue_checkin_radius": 500,  # 500 meters radius
        "registration_open": True,
        "max_attendees": 100,
        "current_attendees": 0,
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.conferences.insert_one(conf_data)
    conf_data["_id"] = result.inserted_id
    return conf_data


@pytest.fixture
async def sample_todays_session(test_db, sample_conference_with_gps):
    """
    Create sample session scheduled for today.

    Args:
        test_db: Test database fixture
        sample_conference_with_gps: Conference with GPS fixture

    Returns:
        Session document with _id for today
    """
    from datetime import time
    today = datetime.utcnow().date()
    session_datetime = datetime.combine(today, time(hour=9, minute=0))

    session_data = {
        "conference_id": sample_conference_with_gps["_id"],
        "name": "Today's Morning Service",
        "description": "Session scheduled for today",
        "location": "Main Auditorium",
        "day_number": 1,
        "day_label": "Day 1",
        "session_date": session_datetime,
        "order": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.conference_sessions.insert_one(session_data)
    session_data["_id"] = result.inserted_id
    return session_data


@pytest.fixture
async def sample_registration_for_gps_conf(test_db, sample_conference_with_gps):
    """
    Create sample registration for GPS conference.

    Args:
        test_db: Test database fixture
        sample_conference_with_gps: Conference with GPS fixture

    Returns:
        Registration document with _id
    """
    reg_data = {
        "conference_id": sample_conference_with_gps["_id"],
        "user_name": "GPS Test Attendee",
        "user_phone": "+233244555666",
        "user_email": "gpstest@example.com",
        "registration_code": "REG-GPSTEST123",
        "status": "confirmed",
        "checked_in": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.conference_registrations.insert_one(reg_data)
    reg_data["_id"] = result.inserted_id
    return reg_data


# ============================================================
# Visitor Tracking & Discipleship System Fixtures
# ============================================================

@pytest.fixture
async def sample_organization(test_db):
    """
    Create sample organization for testing.

    Args:
        test_db: Test database fixture

    Returns:
        Organization document with _id
    """
    org_data = {
        "name": "Test Church",
        "description": "Test church for visitor tracking tests",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.organizations.insert_one(org_data)
    org_data["_id"] = result.inserted_id
    return org_data


@pytest.fixture
async def sample_zone(test_db, sample_organization):
    """
    Create sample zone for testing.

    Args:
        test_db: Test database fixture
        sample_organization: Organization fixture

    Returns:
        Zone document with _id
    """
    zone_data = {
        "organization_id": sample_organization["_id"],
        "name": "Test Zone",
        "description": "Test zone for cell groups",
        "geographic_area": "Test Area",
        "zone_leader_id": None,
        "assistant_zone_leaders": [],
        "cell_group_count": 0,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.zones.insert_one(zone_data)
    zone_data["_id"] = result.inserted_id
    return zone_data


@pytest.fixture
async def sample_cell_group(test_db, sample_organization, sample_zone):
    """
    Create sample cell group for testing.

    Args:
        test_db: Test database fixture
        sample_organization: Organization fixture
        sample_zone: Zone fixture

    Returns:
        Cell group document with _id
    """
    cell_data = {
        "organization_id": sample_organization["_id"],
        "zone_id": sample_zone["_id"],
        "name": "Test Cell Group",
        "description": "Test cell group for visitor assignment",
        "meeting_day": "Wednesday",
        "meeting_time": "19:00",
        "meeting_location": "Test Location",
        "cell_leader_id": None,
        "assistant_leaders": [],
        "target_size": 12,
        "current_member_count": 0,
        "is_full": False,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.cell_groups.insert_one(cell_data)
    cell_data["_id"] = result.inserted_id
    return cell_data


@pytest.fixture
async def sample_department(test_db, sample_organization):
    """
    Create sample department for testing.

    Args:
        test_db: Test database fixture
        sample_organization: Organization fixture

    Returns:
        Department document with _id
    """
    dept_data = {
        "organization_id": sample_organization["_id"],
        "name": "Worship Team",
        "description": "Test worship department",
        "department_type": "worship",
        "department_head_id": None,
        "assistant_heads": [],
        "volunteer_count": 0,
        "leader_count": 0,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.departments.insert_one(dept_data)
    dept_data["_id"] = result.inserted_id
    return dept_data


@pytest.fixture
async def sample_journey_stage(test_db, sample_organization):
    """
    Create sample journey stage for testing.

    Args:
        test_db: Test database fixture
        sample_organization: Organization fixture

    Returns:
        Journey stage document with _id
    """
    stage_data = {
        "organization_id": sample_organization["_id"],
        "stage_name": "first_timer",
        "stage_display_name": "First Timer",
        "journey_type": "spiritual",
        "stage_order": 1,
        "is_custom": False,
        "is_active": True,
        "auto_send_welcome": True,
        "welcome_delay_minutes": 5,
        "welcome_message_template": "Hi {{name}}! Welcome to {{church_name}}!",
        "welcome_channels": ["sms", "whatsapp"],
        "scheduled_followups": [
            {
                "delay_days": 1,
                "message_template": "Hi {{name}}! Thanks for visiting!",
                "communication_channels": ["sms"]
            }
        ],
        "description": "First-time visitor",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.journey_stages.insert_one(stage_data)
    stage_data["_id"] = result.inserted_id
    return stage_data


@pytest.fixture
async def sample_cell_leader(test_db, sample_organization):
    """
    Create sample cell leader user for testing.

    Args:
        test_db: Test database fixture
        sample_organization: Organization fixture

    Returns:
        User document with _id and cell_leader role
    """
    user_data = {
        "name": "Cell Leader",
        "full_name": "Cell Leader Test",
        "phone": "+233200000010",
        "roles": ["member", "cell_leader"],
        "branch_id": sample_organization["_id"],
        "member_status": "active_member",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.users.insert_one(user_data)
    user_data["_id"] = result.inserted_id
    return user_data


@pytest.fixture
async def sample_visitor(test_db, sample_organization):
    """
    Create sample visitor for testing.

    Args:
        test_db: Test database fixture
        sample_organization: Organization fixture

    Returns:
        User document with _id and visitor status
    """
    visitor_data = {
        "name": "Test Visitor",
        "full_name": "Test Visitor",
        "phone": "+233200000099",
        "roles": ["member"],
        "branch_id": sample_organization["_id"],
        "member_status": "visitor",
        "current_spiritual_stage": "first_timer",
        "first_visit_date": datetime.utcnow(),
        "visit_count": 1,
        "first_visit_source": "friend_referral",
        "preferred_communication_channel": "whatsapp",
        "allow_automated_communications": True,
        "stage_history": [],
        "enrichment_history": [],
        "life_events": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.users.insert_one(visitor_data)
    visitor_data["_id"] = result.inserted_id
    return visitor_data


# ==========================================
# Organization Scoping Test Fixtures
# ==========================================


@pytest.fixture
async def two_organizations(test_db):
    """
    Create two separate organizations for isolation testing.

    Args:
        test_db: Test database fixture

    Returns:
        tuple: (org_a_doc, org_b_doc)
            - org_a: Action Chapel International (real org from migration)
            - org_b: Test Competitor Church
    """
    org_a = {
        "_id": ObjectId("68fbb1cf8b6890654df914ca"),
        "name": "Action Chapel International",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    org_b = {
        "_id": ObjectId(),
        "name": "Test Competitor Church",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await test_db.organizations.insert_many([org_a, org_b])
    return org_a, org_b


@pytest.fixture
async def users_for_two_orgs(test_db, two_organizations):
    """
    Create admin users for both organizations.

    Args:
        test_db: Test database fixture
        two_organizations: Tuple of two organization documents

    Returns:
        tuple: (user_a_doc, user_b_doc)
    """
    org_a, org_b = two_organizations

    user_a = {
        "_id": ObjectId(),
        "name": "Admin A",
        "phone": "+233200000001",
        "email": "admin_a@test.com",
        "organization_id": org_a["_id"],
        "roles": ["admin"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    user_b = {
        "_id": ObjectId(),
        "name": "Admin B",
        "phone": "+233200000002",
        "email": "admin_b@test.com",
        "organization_id": org_b["_id"],
        "roles": ["admin"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await test_db.users.insert_many([user_a, user_b])
    return user_a, user_b


@pytest.fixture
async def branches_for_two_orgs(test_db, two_organizations):
    """
    Create sample branches for both organizations.

    Args:
        test_db: Test database fixture
        two_organizations: Tuple of two organization documents

    Returns:
        list: List of branch documents (2 per organization)
    """
    org_a, org_b = two_organizations

    branches = [
        # Org A branches
        {
            "_id": ObjectId(),
            "organization_id": org_a["_id"],
            "name": "Adenta Branch",
            "location": "Adenta, Accra",
            "region": "Greater Accra",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "organization_id": org_a["_id"],
            "name": "Legon Branch",
            "location": "Legon, Accra",
            "region": "Greater Accra",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        # Org B branches
        {
            "_id": ObjectId(),
            "organization_id": org_b["_id"],
            "name": "Competitor Branch 1",
            "location": "Tema, Accra",
            "region": "Greater Accra",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "organization_id": org_b["_id"],
            "name": "Competitor Branch 2",
            "location": "Kumasi",
            "region": "Ashanti",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]

    await test_db.branches.insert_many(branches)
    return branches


@pytest.fixture
async def first_timers_for_two_orgs(test_db, two_organizations):
    """
    Create sample first timers for both organizations.

    Args:
        test_db: Test database fixture
        two_organizations: Tuple of two organization documents

    Returns:
        list: List of first timer documents (2 per organization)
    """
    org_a, org_b = two_organizations

    first_timers = [
        # Org A first timers
        {
            "_id": ObjectId(),
            "organization_id": org_a["_id"],
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+233244111222",
            "email": "john.doe@test.com",
            "visit_date": datetime.utcnow(),
            "interest_type": "visitor",
            "follow_up_status": "pending",
            "converted_to_member": False,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "organization_id": org_a["_id"],
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "+233244333444",
            "email": "jane.smith@test.com",
            "visit_date": datetime.utcnow(),
            "interest_type": "visitor",
            "follow_up_status": "contacted",
            "converted_to_member": False,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        # Org B first timers
        {
            "_id": ObjectId(),
            "organization_id": org_b["_id"],
            "first_name": "Mike",
            "last_name": "Johnson",
            "phone": "+233244555666",
            "email": "mike.johnson@test.com",
            "visit_date": datetime.utcnow(),
            "interest_type": "visitor",
            "follow_up_status": "pending",
            "converted_to_member": False,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "organization_id": org_b["_id"],
            "first_name": "Sarah",
            "last_name": "Williams",
            "phone": "+233244777888",
            "email": "sarah.williams@test.com",
            "visit_date": datetime.utcnow(),
            "interest_type": "visitor",
            "follow_up_status": "pending",
            "converted_to_member": False,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]

    await test_db.first_timers.insert_many(first_timers)
    return first_timers


@pytest.fixture
async def conferences_for_two_orgs(test_db, two_organizations):
    """
    Create sample conferences for both organizations.

    Args:
        test_db: Test database fixture
        two_organizations: Tuple of two organization documents

    Returns:
        list: List of conference documents (2 per organization)
    """
    org_a, org_b = two_organizations

    conferences = [
        # Org A conferences
        {
            "_id": ObjectId(),
            "organization_id": org_a["_id"],
            "name": "Annual Conference 2025",
            "description": "Organization A Annual Conference",
            "venue": "Accra International Conference Centre",
            "start_date": datetime(2025, 6, 1),
            "end_date": datetime(2025, 6, 5),
            "registration_open": True,
            "status": "upcoming",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "organization_id": org_a["_id"],
            "name": "Youth Conference 2025",
            "description": "Organization A Youth Conference",
            "venue": "Legon Sports Stadium",
            "start_date": datetime(2025, 8, 10),
            "end_date": datetime(2025, 8, 12),
            "registration_open": True,
            "status": "upcoming",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        # Org B conferences
        {
            "_id": ObjectId(),
            "organization_id": org_b["_id"],
            "name": "Competitor Annual Conference 2025",
            "description": "Organization B Annual Conference",
            "venue": "Kumasi Convention Centre",
            "start_date": datetime(2025, 7, 1),
            "end_date": datetime(2025, 7, 3),
            "registration_open": True,
            "status": "upcoming",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "organization_id": org_b["_id"],
            "name": "Competitor Youth Conference 2025",
            "description": "Organization B Youth Conference",
            "venue": "Tema Stadium",
            "start_date": datetime(2025, 9, 5),
            "end_date": datetime(2025, 9, 7),
            "registration_open": True,
            "status": "upcoming",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]

    await test_db.conferences.insert_many(conferences)
    return conferences


@pytest.fixture
async def sessions_for_two_orgs(test_db, conferences_for_two_orgs):
    """
    Create sample sessions for conferences.

    Args:
        test_db: Test database fixture
        conferences_for_two_orgs: List of conference documents

    Returns:
        list: List of session documents (2 per conference)
    """
    sessions = []

    for conf in conferences_for_two_orgs:
        # Create 2 sessions per conference
        for day_num in [1, 2]:
            session = {
                "_id": ObjectId(),
                "conference_id": conf["_id"],
                "name": f"{conf['name']} - Day {day_num}",
                "day_number": day_num,
                "day_label": f"Day {day_num}",
                "session_date": conf["start_date"],
                "start_time": "09:00",
                "end_time": "17:00",
                "location": conf["venue"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            sessions.append(session)

    await test_db.conference_sessions.insert_many(sessions)
    return sessions


@pytest.fixture
async def registrations_for_two_orgs(test_db, conferences_for_two_orgs):
    """
    Create sample registrations for conferences.

    Args:
        test_db: Test database fixture
        conferences_for_two_orgs: List of conference documents

    Returns:
        list: List of registration documents (2 per conference)
    """
    registrations = []

    for idx, conf in enumerate(conferences_for_two_orgs):
        # Create 2 registrations per conference
        for reg_num in [1, 2]:
            registration = {
                "_id": ObjectId(),
                "conference_id": conf["_id"],
                "organization_id": conf["organization_id"],
                "user_name": f"Attendee {idx}-{reg_num}",
                "user_phone": f"+23324400{idx}{reg_num}111",
                "user_email": f"attendee{idx}{reg_num}@test.com",
                "registration_code": f"REG-{idx}{reg_num}-{conf['_id']}",
                "checked_in": False,
                "status": "confirmed",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            registrations.append(registration)

    await test_db.conference_registrations.insert_many(registrations)
    return registrations
