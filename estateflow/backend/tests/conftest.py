"""
Pytest configuration and fixtures for EstateFlow tests.

Provides:
- Database connection fixtures
- Test client fixtures
- Authentication fixtures
- Sample data fixtures
- Cleanup utilities
"""

import asyncio
import os
import sys
from typing import AsyncGenerator, Dict, Any
from datetime import datetime, timedelta
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient
from faker import Faker

# Add backend to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.database import MongoDB
from app.config import settings

# Initialize Faker for test data generation
fake = Faker()

# Test database name
TEST_DATABASE_NAME = "estateflow_test"

# Test organization ID (consistent across all tests)
TEST_ORG_ID = "test-org-" + str(uuid.uuid4())


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the test session.

    Ensures async tests can run properly.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_mongo_client():
    """
    Create a MongoDB client for testing.

    Uses the same connection settings as production but with test database.
    """
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    yield client
    client.close()


@pytest_asyncio.fixture(scope="function")
async def test_database(test_mongo_client):
    """
    Provide a clean test database for each test.

    Creates a fresh database before each test and drops it after.
    Ensures test isolation.
    """
    db = test_mongo_client[TEST_DATABASE_NAME]

    # Create indexes for test database (same as production)
    await create_test_indexes(db)

    yield db

    # Cleanup: Drop all collections after test
    collection_names = await db.list_collection_names()
    for collection_name in collection_names:
        await db[collection_name].drop()


async def create_test_indexes(db):
    """
    Create database indexes for test database.

    Mirrors production indexes for realistic testing.
    """
    # Properties indexes
    await db.properties.create_index([("organization_id", 1), ("status", 1)])
    await db.properties.create_index([("financial.price_usd", 1)])
    await db.properties.create_index([("location.city", 1)])
    await db.properties.create_index([("property_type", 1)])
    await db.properties.create_index([("created_at", -1)])
    await db.properties.create_index([("name", "text"), ("description", "text")])

    # Bookings indexes
    await db.bookings.create_index([("property_id", 1)])
    await db.bookings.create_index([("contact_id", 1)])
    await db.bookings.create_index([("status", 1)])
    await db.bookings.create_index([("scheduled_time", 1)])
    await db.bookings.create_index([("agent_id", 1)])
    await db.bookings.create_index([("organization_id", 1)])

    # Agents indexes
    await db.agents.create_index([("organization_id", 1), ("is_active", 1)])
    await db.agents.create_index([("email", 1)])

    # Campaigns indexes
    await db.campaigns.create_index([("organization_id", 1), ("status", 1)])
    await db.campaigns.create_index([("campaign_type", 1)])

    # Contacts indexes
    await db.contacts.create_index([("organization_id", 1)])
    await db.contacts.create_index([("email", 1)])
    await db.contacts.create_index([("phone", 1)])

    # Booking action logs indexes
    await db.booking_action_logs.create_index([("booking_id", 1)])
    await db.booking_action_logs.create_index([("organization_id", 1), ("timestamp", -1)])
    await db.booking_action_logs.create_index([("admin_email", 1)])


@pytest_asyncio.fixture(scope="function")
async def test_client(test_database, organization_context) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP client for API testing.

    Uses FastAPI TestClient for making API requests.
    Automatically handles app lifespan.
    """
    from app.core.database import get_database
    from app.core.auth import get_current_user, get_organization_context, get_optional_user

    # Mock user for authentication with organization info
    mock_user = {
        "id": "test-user-id",
        "email": "test@example.com",
        "role": "authenticated",
        "organization_id": organization_context["organization_id"],  # Top level for booking router
        "app_metadata": {
            "organization_id": organization_context["organization_id"]
        },
        "user_metadata": {}
    }

    # Override database dependency to use test database
    async def override_get_db():
        return test_database

    # Override auth dependency to return mock user
    async def override_get_current_user():
        return mock_user

    # Override optional auth dependency to return mock user
    async def override_get_optional_user():
        return mock_user

    # Override organization context dependency
    async def override_get_org_context():
        return organization_context

    # Override all dependencies
    app.dependency_overrides[get_database] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_optional_user] = override_get_optional_user
    app.dependency_overrides[get_organization_context] = override_get_org_context

    # Create async client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """
    Provide authentication headers for API requests.

    Uses a test JWT token for Supabase auth.
    In real tests, this would be a valid token from Supabase.
    For now, we use a mock token.
    """
    # TODO: Generate real Supabase JWT token for integration tests
    # For unit tests, we mock the auth dependency
    return {
        "Authorization": f"Bearer test-jwt-token-{uuid.uuid4()}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def organization_context() -> Dict[str, Any]:
    """
    Provide organization context for multi-tenant tests.

    Returns organization ID and metadata.
    """
    return {
        "organization_id": TEST_ORG_ID,
        "organization_name": "Test Organization",
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_property(organization_context) -> Dict[str, Any]:
    """
    Provide sample property data for testing.

    Realistic property with all fields populated.
    """
    return {
        "organization_id": organization_context["organization_id"],
        "name": fake.company() + " Residence",
        "description": fake.text(max_nb_chars=200),
        "property_type": "apartment",
        "status": "active",
        "location": {
            "address": fake.street_address(),
            "city": fake.city(),
            "state": fake.state(),
            "zip_code": fake.postcode(),
            "country": "Ghana",
            "latitude": float(fake.latitude()),
            "longitude": float(fake.longitude()),
            "neighborhood": fake.city_suffix() + " District"
        },
        "neighborhood_data": {
            "schools": [
                {
                    "name": "Lincoln Community School",
                    "type": "elementary",
                    "distance_km": 1.2,
                    "rating": 9.0
                }
            ],
            "amenities": [
                {
                    "name": "MaxMart",
                    "category": "grocery",
                    "distance_km": 0.8
                }
            ],
            "safety_rating": 8.5,
            "walkability_score": 75,
            "transit_score": 80
        },
        "features": {
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 1500,
            "lot_size": 2000,
            "year_built": 2020,
            "parking_spaces": 2,
            "pool": True,
            "garden": True,
            "balcony": True,
            "pet_policy": "allowed",
            "pet_deposit": 500.0,
            "furnished": False,
            "elevator": True,
            "air_conditioning": True,
            "heating": True,
            "fireplace": False,
            "security": True,
            "gym": False,
            "storage": True
        },
        "financial": {
            "price_usd": 250000.0,
            "base_currency": "USD",
            "hoa_fees_monthly": 200.0,
            "property_tax_annual": 3000.0,
            "insurance_estimate_annual": 1200.0
        },
        "images": [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg"
        ],
        "video_url": "https://youtube.com/watch?v=example",
        "virtual_tour_url": "https://matterport.com/example",
        "agent_id": None,
        "agent_name": None
    }


@pytest.fixture
def sample_property_minimal(organization_context) -> Dict[str, Any]:
    """
    Provide minimal property data for testing required fields only.
    """
    return {
        "organization_id": organization_context["organization_id"],
        "name": "Minimal Property",
        "description": "A minimal property for testing",
        "property_type": "house",
        "status": "active",
        "location": {
            "address": "123 Test Street",
            "city": "Accra",
            "country": "Ghana"
        },
        "features": {
            "bedrooms": 2,
            "bathrooms": 1,
            "sqft": 1000
        },
        "financial": {
            "price_usd": 150000.0,
            "base_currency": "USD"
        }
    }


@pytest.fixture
def sample_contact(organization_context) -> Dict[str, Any]:
    """
    Provide sample contact data for testing.
    """
    return {
        "organization_id": organization_context["organization_id"],
        "name": fake.name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "property_type_preferences": ["apartment", "villa"],
        "location_preferences": ["Accra", "Kumasi"],
        "budget_min": 100000.0,
        "budget_max": 500000.0,
        "interest_status": "warm",
        "lead_status": "new",
        "tags": ["investor", "first-time-buyer"],
        "opt_out_channels": []
    }


@pytest.fixture
def sample_agent(organization_context) -> Dict[str, Any]:
    """
    Provide sample agent data for testing.
    """
    full_name = fake.name().split(" ", 1)
    first_name = full_name[0]
    last_name = full_name[1] if len(full_name) > 1 else "Doe"

    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": fake.email(),
        "phone": fake.phone_number(),
        "specializations": ["residential", "commercial"],
        "working_hours": {
            "monday": {"start": "09:00", "end": "17:00", "available": True},
            "tuesday": {"start": "09:00", "end": "17:00", "available": True},
            "wednesday": {"start": "09:00", "end": "17:00", "available": True},
            "thursday": {"start": "09:00", "end": "17:00", "available": True},
            "friday": {"start": "09:00", "end": "17:00", "available": True}
        },
        "max_bookings_per_day": 5,
        "timezone": "UTC",
        "languages": ["English"]
    }


@pytest.fixture
def sample_booking(organization_context) -> Dict[str, Any]:
    """
    Provide sample booking data for testing.
    """
    scheduled_at = datetime.utcnow() + timedelta(days=7)
    return {
        "property_id": "test-property-id",
        "contact_id": "test-contact-id",
        "contact_name": "Test Contact",
        "contact_email": "test@example.com",
        "contact_phone": "+1234567890",
        "booking_type": "in-person",
        "scheduled_at": scheduled_at.isoformat(),
        "duration_minutes": 60,
        "notes": "Test booking for property tour"
    }


@pytest.fixture
def sample_campaign(organization_context) -> Dict[str, Any]:
    """
    Provide sample campaign data for testing.
    """
    return {
        "organization_id": organization_context["organization_id"],
        "name": "Test SMS Campaign",
        "campaign_type": "sms",
        "status": "draft",
        "message_template": {
            "text": "Hello {name}, we have a new property for you!",
            "variables": ["name"]
        },
        "segment_filter": {
            "property_types": ["apartment"],
            "min_budget": 100000,
            "max_budget": 500000
        },
        "schedule_config": {
            "type": "immediate"
        }
    }


@pytest.fixture
def sample_document_template(organization_context) -> Dict[str, Any]:
    """
    Provide sample document template data for testing.
    """
    return {
        "organization_id": organization_context["organization_id"],
        "name": "Test Lease Agreement",
        "document_type": "lease_agreement",
        "template_content": """
LEASE AGREEMENT

This lease agreement is made on {{ current_date }} between:

Landlord: {{ landlord_name }}
Tenant: {{ tenant_name }}

Property Address: {{ property_address }}

Monthly Rent: ${{ monthly_rent }}

Lease Term: {{ lease_term_months }} months

Signatures:
_______________________
Landlord

_______________________
Tenant
        """,
        "variables": [
            {
                "name": "landlord_name",
                "type": "string",
                "required": True,
                "description": "Name of the property owner"
            },
            {
                "name": "tenant_name",
                "type": "string",
                "required": True,
                "description": "Name of the tenant"
            },
            {
                "name": "property_address",
                "type": "string",
                "required": True,
                "description": "Full property address"
            },
            {
                "name": "monthly_rent",
                "type": "number",
                "required": True,
                "description": "Monthly rent amount"
            },
            {
                "name": "lease_term_months",
                "type": "number",
                "required": True,
                "description": "Lease duration in months"
            }
        ],
        "is_default": False,
        "version": 1
    }


@pytest_asyncio.fixture(scope="function")
async def cleanup(test_database):
    """
    Cleanup fixture that runs after each test.

    Ensures database is clean for next test.
    """
    yield

    # Drop all test collections
    collection_names = await test_database.list_collection_names()
    for collection_name in collection_names:
        if not collection_name.startswith("system."):
            await test_database[collection_name].drop()


@pytest.fixture
def notification_service(test_database):
    """
    Provide notification service instance for testing.

    Args:
        test_database: Test database fixture

    Returns:
        BookingNotificationService instance
    """
    from app.services.notification_service import BookingNotificationService

    # Test email configuration (won't actually send emails)
    email_config = {
        "default_provider": "smtp",
        "providers": {
            "smtp": {
                "smtp_server": "localhost",
                "smtp_port": 1025,
                "username": "test",
                "password": "test",
                "use_tls": False,
                "from_email": "test@example.com"
            }
        }
    }

    return BookingNotificationService(test_database, email_config)


# Pytest configuration
def pytest_configure(config):
    """
    Configure pytest markers.
    """
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


# Async test configuration
pytest_plugins = ('pytest_asyncio',)
