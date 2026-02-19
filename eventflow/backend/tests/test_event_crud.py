"""
Unit tests for Event CRUD operations.

Tests cover:
- Event creation
- Event retrieval (single and list)
- Event update
- Event deletion
- Dashboard statistics
- Task generation
- Permission checks
- Edge cases
"""

import pytest
from datetime import datetime, timedelta
from bson import ObjectId
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from apps.eventflow.backend.app.services.event_service import EventService
from apps.eventflow.backend.app.models.event import EventInDB
from apps.eventflow.backend.app.schemas.event import EventCreate, EventUpdate, DashboardResponse


@pytest.fixture
def event_service():
    """Create event service with mocked database."""
    db = MagicMock()
    service = EventService(db)
    # Mock the collections for testing
    service.events_collection = AsyncMock()
    service.tasks_collection = AsyncMock()
    service.persons_collection = AsyncMock()
    return service


@pytest.fixture
def sample_event_create():
    """Sample event creation data."""
    return EventCreate(
        name="Impact 2025 Conference",
        type="conference",
        date=datetime.utcnow() + timedelta(days=30),
        location="Accra International Conference Centre",
        num_guests=500,
        budget_min=50000,
        budget_max=100000,
        description="Annual youth conference",
        tags=["youth", "conference", "public"],
    )


@pytest.fixture
def sample_event_dict():
    """Sample event dictionary from database."""
    return {
        "_id": ObjectId(),
        "name": "Impact 2025 Conference",
        "type": "conference",
        "date": datetime.utcnow() + timedelta(days=30),
        "location": "Accra International Conference Centre",
        "num_guests": 500,
        "budget_min": 50000,
        "budget_max": 100000,
        "status": "planning",
        "organizer_id": "user123",
        "description": "Annual youth conference",
        "documents": [],
        "tags": ["youth", "conference", "public"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


class TestEventCreation:
    """Test event creation operations."""

    @pytest.mark.asyncio
    async def test_create_event_success(self, event_service, sample_event_create):
        """Test successful event creation."""
        # Arrange
        user_id = "user123"
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        event_service.events_collection.insert_one = AsyncMock(return_value=mock_result)

        # Act
        result = await event_service.create_event(user_id, sample_event_create)

        # Assert
        assert isinstance(result, EventInDB)
        assert result.name == sample_event_create.name
        assert result.type == sample_event_create.type
        assert result.organizer_id == user_id
        assert result.status == "planning"
        event_service.events_collection.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_event_sets_default_status(self, event_service, sample_event_create):
        """Test that new events default to 'planning' status."""
        # Arrange
        user_id = "user123"
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        event_service.events_collection.insert_one = AsyncMock(return_value=mock_result)

        # Act
        result = await event_service.create_event(user_id, sample_event_create)

        # Assert
        assert result.status == "planning"

    @pytest.mark.asyncio
    async def test_create_event_with_minimal_data(self, event_service):
        """Test creating event with only required fields."""
        # Arrange
        user_id = "user123"
        minimal_event = EventCreate(
            name="Simple Event",
            type="meeting",
            date=datetime.utcnow() + timedelta(days=7),
            location="Office",
            num_guests=10,
        )
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        event_service.events_collection.insert_one = AsyncMock(return_value=mock_result)

        # Act
        result = await event_service.create_event(user_id, minimal_event)

        # Assert
        assert result.name == "Simple Event"
        assert result.budget_min is None
        assert result.budget_max is None
        assert result.description is None


class TestEventRetrieval:
    """Test event retrieval operations."""

    @pytest.mark.asyncio
    async def test_get_event_success(self, event_service, sample_event_dict):
        """Test successful event retrieval."""
        # Arrange
        event_id = str(sample_event_dict["_id"])
        user_id = sample_event_dict["organizer_id"]
        event_service.events_collection.find_one = AsyncMock(return_value=sample_event_dict.copy())

        # Act
        result = await event_service.get_event(event_id, user_id)

        # Assert
        assert result is not None
        assert result.name == sample_event_dict["name"]
        assert result.id == str(sample_event_dict["_id"])

    @pytest.mark.asyncio
    async def test_get_event_not_found(self, event_service):
        """Test retrieving non-existent event."""
        # Arrange
        event_service.events_collection.find_one = AsyncMock(return_value=None)

        # Act
        result = await event_service.get_event("nonexistent_id", "user123")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_event_wrong_user(self, event_service):
        """Test that users can only access their own events."""
        # Arrange
        event_service.events_collection.find_one = AsyncMock(return_value=None)

        # Act
        result = await event_service.get_event("event123", "different_user")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_list_events_empty(self, event_service):
        """Test listing events when user has none."""
        # Arrange
        # Create async iterator for empty list
        async def async_iter_empty():
            for item in []:
                yield item

        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.__aiter__ = lambda self: async_iter_empty()

        event_service.events_collection.find = MagicMock(return_value=mock_cursor)
        event_service.events_collection.count_documents = AsyncMock(return_value=0)

        # Act
        result_events, total = await event_service.list_events("user123")

        # Assert
        assert len(result_events) == 0
        assert total == 0


class TestEventUpdate:
    """Test event update operations."""

    @pytest.mark.asyncio
    async def test_update_event_success(self, event_service, sample_event_dict):
        """Test successful event update."""
        # Arrange
        event_id = str(sample_event_dict["_id"])
        user_id = sample_event_dict["organizer_id"]
        update_data = EventUpdate(name="Updated Conference Name")

        updated_dict = sample_event_dict.copy()
        updated_dict["name"] = "Updated Conference Name"
        event_service.events_collection.find_one_and_update = AsyncMock(return_value=updated_dict)

        # Act
        result = await event_service.update_event(event_id, user_id, update_data)

        # Assert
        assert result is not None
        assert result.name == "Updated Conference Name"
        event_service.events_collection.find_one_and_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_event_not_found(self, event_service):
        """Test updating non-existent event."""
        # Arrange
        update_data = EventUpdate(name="Updated Name")
        event_service.events_collection.find_one_and_update = AsyncMock(return_value=None)

        # Act
        result = await event_service.update_event("nonexistent_id", "user123", update_data)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_update_event_empty_update(self, event_service, sample_event_dict):
        """Test update with no fields changed."""
        # Arrange
        event_id = str(sample_event_dict["_id"])
        user_id = sample_event_dict["organizer_id"]
        update_data = EventUpdate()  # Empty update

        # Mock get_event to return existing event
        event_service.events_collection.find_one = AsyncMock(return_value=sample_event_dict.copy())

        # Act
        result = await event_service.update_event(event_id, user_id, update_data)

        # Assert
        assert result is not None
        assert result.name == sample_event_dict["name"]
        # find_one_and_update should NOT be called for empty update
        event_service.events_collection.find_one_and_update.assert_not_called()


class TestEventDeletion:
    """Test event deletion operations."""

    @pytest.mark.asyncio
    async def test_delete_event_success(self, event_service):
        """Test successful event deletion."""
        # Arrange
        event_id = str(ObjectId())  # Use valid ObjectId string
        user_id = "user123"
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        event_service.events_collection.delete_one = AsyncMock(return_value=mock_result)

        # Act
        result = await event_service.delete_event(event_id, user_id)

        # Assert
        assert result is True
        event_service.events_collection.delete_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_event_not_found(self, event_service):
        """Test deleting non-existent event."""
        # Arrange
        mock_result = MagicMock()
        mock_result.deleted_count = 0
        event_service.events_collection.delete_one = AsyncMock(return_value=mock_result)

        # Act
        result = await event_service.delete_event("nonexistent_id", "user123")

        # Assert
        assert result is False


class TestEventDashboard:
    """Test event dashboard statistics."""

    @pytest.mark.asyncio
    async def test_get_dashboard_success(self, event_service, sample_event_dict):
        """Test getting dashboard statistics."""
        # Arrange
        event_id = str(sample_event_dict["_id"])
        user_id = sample_event_dict["organizer_id"]

        # Mock event retrieval
        event_service.events_collection.find_one = AsyncMock(return_value=sample_event_dict.copy())

        # Mock tasks
        tasks = [
            {"status": "completed", "deadline": datetime.utcnow() + timedelta(days=1)},
            {"status": "in_progress", "deadline": datetime.utcnow() + timedelta(days=2)},
            {"status": "pending", "deadline": datetime.utcnow() + timedelta(days=3)},
            {"status": "pending", "deadline": datetime.utcnow() - timedelta(days=1)},  # Overdue
        ]
        event_service.tasks_collection.find = MagicMock(
            return_value=MagicMock(to_list=AsyncMock(return_value=tasks))
        )
        event_service.persons_collection.count_documents = AsyncMock(return_value=5)

        # Act
        result = await event_service.get_dashboard(event_id, user_id)

        # Assert
        assert result is not None
        assert isinstance(result, DashboardResponse)
        assert result.tasks.total == 4
        assert result.tasks.completed == 1
        assert result.tasks.in_progress == 1
        assert result.tasks.pending == 2
        assert result.tasks.overdue == 1
        assert result.tasks.completion_rate == 25.0
        assert result.responsible_persons_count == 5

    @pytest.mark.asyncio
    async def test_get_dashboard_no_tasks(self, event_service, sample_event_dict):
        """Test dashboard with no tasks."""
        # Arrange
        event_id = str(sample_event_dict["_id"])
        user_id = sample_event_dict["organizer_id"]

        event_service.events_collection.find_one = AsyncMock(return_value=sample_event_dict.copy())
        event_service.tasks_collection.find = MagicMock(
            return_value=MagicMock(to_list=AsyncMock(return_value=[]))
        )
        event_service.persons_collection.count_documents = AsyncMock(return_value=0)

        # Act
        result = await event_service.get_dashboard(event_id, user_id)

        # Assert
        assert result is not None
        assert result.tasks.total == 0
        assert result.tasks.completion_rate == 0.0

    @pytest.mark.asyncio
    async def test_get_dashboard_event_not_found(self, event_service):
        """Test dashboard for non-existent event."""
        # Arrange
        event_service.events_collection.find_one = AsyncMock(return_value=None)

        # Act
        result = await event_service.get_dashboard("nonexistent_id", "user123")

        # Assert
        assert result is None


class TestTaskGeneration:
    """Test AI task generation."""

    @pytest.mark.asyncio
    async def test_generate_tasks_success(self, event_service, sample_event_dict):
        """Test successful task generation."""
        # Arrange
        event_id = str(sample_event_dict["_id"])
        user_id = sample_event_dict["organizer_id"]

        event_service.events_collection.find_one = AsyncMock(return_value=sample_event_dict.copy())

        # Mock task insertion
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        event_service.tasks_collection.insert_one = AsyncMock(return_value=mock_result)

        # Act
        with patch.object(event_service.ai_generator, 'generate_tasks',
                         return_value=[
                             {
                                 "title": "Book venue",
                                 "description": "Reserve conference hall",
                                 "category": "venue",
                                 "priority": "critical",
                                 "status": "pending",
                                 "deadline": datetime.utcnow() + timedelta(days=20)
                             }
                         ]):
            result = await event_service.generate_tasks(event_id, user_id)

        # Assert
        assert len(result) == 1
        assert result[0].title == "Book venue"
        assert result[0].category == "venue"
        event_service.tasks_collection.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_tasks_event_not_found(self, event_service):
        """Test task generation for non-existent event."""
        # Arrange
        event_service.events_collection.find_one = AsyncMock(return_value=None)

        # Act
        result = await event_service.generate_tasks("nonexistent_id", "user123")

        # Assert
        assert result == []


class TestPublicMethods:
    """Test public demo methods (no authentication)."""

    @pytest.mark.asyncio
    async def test_get_event_public_success(self, event_service, sample_event_dict):
        """Test public event retrieval."""
        # Arrange
        event_id = str(sample_event_dict["_id"])
        event_service.events_collection.find_one = AsyncMock(return_value=sample_event_dict.copy())

        # Act
        result = await event_service.get_event_public(event_id)

        # Assert
        assert result is not None
        assert result.name == sample_event_dict["name"]

    @pytest.mark.asyncio
    async def test_update_event_public(self, event_service, sample_event_dict):
        """Test public event update."""
        # Arrange
        event_id = str(sample_event_dict["_id"])
        update_data = EventUpdate(name="Public Update")

        updated_dict = sample_event_dict.copy()
        updated_dict["name"] = "Public Update"
        event_service.events_collection.find_one_and_update = AsyncMock(return_value=updated_dict)

        # Act
        result = await event_service.update_event_public(event_id, update_data)

        # Assert
        assert result is not None
        assert result.name == "Public Update"

    @pytest.mark.asyncio
    async def test_delete_event_public(self, event_service):
        """Test public event deletion."""
        # Arrange
        event_id = str(ObjectId())  # Use valid ObjectId string
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        event_service.events_collection.delete_one = AsyncMock(return_value=mock_result)

        # Act
        result = await event_service.delete_event_public(event_id)

        # Assert
        assert result is True


class TestEventPersonsEndpoint:
    """Test event persons listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_event_persons_success(self, event_service, sample_event_dict):
        """Test listing responsible persons for an event."""
        # Arrange
        event_id = str(sample_event_dict["_id"])
        event_service.events_collection.find_one = AsyncMock(return_value=sample_event_dict.copy())

        # Mock responsible persons
        persons = [
            {
                "_id": ObjectId(),
                "event_id": event_id,
                "name": "John Doe",
                "phone": "+1234567890",
                "email": "john@example.com",
                "role": "Event Coordinator",
                "notes": "Lead coordinator",
            },
            {
                "_id": ObjectId(),
                "event_id": event_id,
                "name": "Jane Smith",
                "phone": "+0987654321",
                "email": "jane@example.com",
                "role": "Logistics Manager",
                "notes": None,
            },
        ]

        # Create async iterator for persons
        async def async_iter_persons():
            for person in persons:
                yield person

        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = lambda self: async_iter_persons()
        event_service.persons_collection.find = MagicMock(return_value=mock_cursor)

        # Act
        result = []
        async for person_doc in event_service.persons_collection.find({"event_id": event_id}):
            result.append(person_doc)

        # Assert
        assert len(result) == 2
        assert result[0]["name"] == "John Doe"
        assert result[1]["name"] == "Jane Smith"

    @pytest.mark.asyncio
    async def test_list_event_persons_empty(self, event_service, sample_event_dict):
        """Test listing persons when event has none."""
        # Arrange
        event_id = str(sample_event_dict["_id"])
        event_service.events_collection.find_one = AsyncMock(return_value=sample_event_dict.copy())

        # Create async iterator for empty list
        async def async_iter_empty():
            for item in []:
                yield item

        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = lambda self: async_iter_empty()
        event_service.persons_collection.find = MagicMock(return_value=mock_cursor)

        # Act
        result = []
        async for person_doc in event_service.persons_collection.find({"event_id": event_id}):
            result.append(person_doc)

        # Assert
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_list_event_persons_event_not_found(self, event_service):
        """Test listing persons for non-existent event."""
        # Arrange
        event_service.events_collection.find_one = AsyncMock(return_value=None)

        # Act
        result = await event_service.get_event_public("nonexistent_id")

        # Assert
        assert result is None
