"""
Unit tests for Event Creation Performance.

Tests that event creation completes quickly without blocking
on RAG service initialization or other async operations.
"""

import pytest
from datetime import datetime, timedelta
import time
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from apps.eventflow.backend.app.services.event_service import EventService
from apps.eventflow.backend.app.schemas.event import EventCreate


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
        name="Test Performance Event",
        type="conference",
        date=datetime.utcnow() + timedelta(days=30),
        location="Test Location",
        num_guests=100,
        budget_min=5000,
        budget_max=10000,
        description="Testing event creation performance",
    )


class TestEventCreationPerformance:
    """Test event creation performance and timeout prevention."""

    @pytest.mark.asyncio
    async def test_create_event_completes_quickly(self, event_service, sample_event_create):
        """
        Test that event creation completes in under 1 second.

        This test ensures that the lazy initialization of RAG service
        prevents blocking during event creation.
        """
        # Arrange
        user_id = "test_user_123"
        from bson import ObjectId
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        event_service.events_collection.insert_one = AsyncMock(return_value=mock_result)

        # Act
        start_time = time.time()
        result = await event_service.create_event(user_id, sample_event_create)
        elapsed_time = time.time() - start_time

        # Assert
        assert result is not None
        assert result.name == sample_event_create.name
        # Event creation should complete in under 1 second
        # Previously this was timing out at 30 seconds
        assert elapsed_time < 1.0, f"Event creation took {elapsed_time:.2f}s, expected < 1s"

    @pytest.mark.asyncio
    async def test_ai_generator_lazy_initialization(self, event_service):
        """
        Test that AI generator doesn't block on initialization.

        The RAGTaskService should be None initially and only
        initialized when actually needed.
        """
        # Assert
        # AI generator exists but RAG task service should be lazy-initialized
        assert hasattr(event_service, 'ai_generator')
        assert event_service.ai_generator.rag_task_service is None, \
            "RAGTaskService should be None initially (lazy initialization)"

    @pytest.mark.asyncio
    async def test_multiple_events_created_quickly(self, event_service):
        """
        Test that multiple events can be created in rapid succession
        without timeout issues.
        """
        # Arrange
        from bson import ObjectId
        user_id = "test_user_123"
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        event_service.events_collection.insert_one = AsyncMock(return_value=mock_result)

        # Create multiple events
        events = [
            EventCreate(
                name=f"Event {i}",
                type="conference",
                date=datetime.utcnow() + timedelta(days=30 + i),
                location=f"Location {i}",
                num_guests=100 + i * 10,
            )
            for i in range(5)
        ]

        # Act
        start_time = time.time()
        results = []
        for event_data in events:
            result = await event_service.create_event(user_id, event_data)
            results.append(result)
        elapsed_time = time.time() - start_time

        # Assert
        assert len(results) == 5
        # Creating 5 events should take less than 2 seconds total
        assert elapsed_time < 2.0, f"Creating 5 events took {elapsed_time:.2f}s, expected < 2s"

    @pytest.mark.asyncio
    async def test_event_creation_no_db_timeout(self, event_service, sample_event_create):
        """
        Test that event creation doesn't encounter database timeouts.

        Simulates a scenario where the database operation might be slow
        but should still complete within reasonable time.
        """
        # Arrange
        user_id = "test_user_123"
        from bson import ObjectId

        # Mock insert_one with a small delay to simulate DB operation
        async def slow_insert(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms delay
            mock_result = MagicMock()
            mock_result.inserted_id = ObjectId()
            return mock_result

        import asyncio
        event_service.events_collection.insert_one = slow_insert

        # Act
        start_time = time.time()
        result = await event_service.create_event(user_id, sample_event_create)
        elapsed_time = time.time() - start_time

        # Assert
        assert result is not None
        # Even with 100ms DB delay, total should be well under 1 second
        assert elapsed_time < 1.0, f"Event creation took {elapsed_time:.2f}s with DB delay"

    @pytest.mark.asyncio
    async def test_event_service_initialization_non_blocking(self):
        """
        Test that EventService initialization itself doesn't block.

        This ensures that creating an EventService instance is fast
        and doesn't trigger any blocking operations.
        """
        # Arrange
        db = MagicMock()

        # Act
        start_time = time.time()
        service = EventService(db)
        elapsed_time = time.time() - start_time

        # Assert
        assert service is not None
        # Service initialization should be nearly instantaneous
        assert elapsed_time < 0.1, f"EventService initialization took {elapsed_time:.2f}s, expected < 0.1s"
        # AI generator should exist but not be fully initialized
        assert hasattr(service, 'ai_generator')
        assert service.ai_generator.rag_task_service is None


class TestAIGeneratorLazyLoading:
    """Test lazy loading of AI task generator components."""

    @pytest.mark.asyncio
    async def test_rag_service_lazy_initialization(self):
        """
        Test that RAG service is only initialized when explicitly called.
        """
        from apps.eventflow.backend.app.services.ai_task_generator import AITaskGenerator

        # Arrange & Act
        generator = AITaskGenerator()

        # Assert
        # RAG task service should be None until first use
        assert generator.rag_task_service is None

    @pytest.mark.asyncio
    async def test_generate_tasks_without_rag_initialization(self):
        """
        Test that tasks can be generated using templates without RAG.

        This ensures fallback templates work without requiring
        RAG service initialization.
        """
        from apps.eventflow.backend.app.services.ai_task_generator import AITaskGenerator
        from apps.eventflow.backend.app.models.event import EventInDB
        from bson import ObjectId

        # Arrange
        generator = AITaskGenerator()
        event = EventInDB(
            id=str(ObjectId()),
            name="Test Event",
            type="conference",
            date=datetime.utcnow() + timedelta(days=60),
            location="Test Location",
            num_guests=100,
            status="planning",
            organizer_id="test_user",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Act
        start_time = time.time()
        tasks = await generator.generate_tasks(event, use_ai=False)
        elapsed_time = time.time() - start_time

        # Assert
        assert len(tasks) > 0, "Should generate tasks using templates"
        assert elapsed_time < 0.5, f"Template task generation took {elapsed_time:.2f}s, expected < 0.5s"
        # RAG service should still be None (not initialized)
        assert generator.rag_task_service is None


class TestRegressionPrevention:
    """Regression tests to ensure timeout issue doesn't reoccur."""

    @pytest.mark.asyncio
    async def test_no_synchronous_blocking_in_init(self):
        """
        Test that no synchronous blocking operations occur during initialization.

        This is a regression test for the original timeout issue where
        RAGTaskService was being initialized synchronously in __init__.
        """
        from apps.eventflow.backend.app.services.ai_task_generator import AITaskGenerator

        # Act
        start_time = time.time()
        generator = AITaskGenerator()
        elapsed_time = time.time() - start_time

        # Assert
        # Initialization should be nearly instantaneous (< 100ms)
        assert elapsed_time < 0.1, \
            f"AITaskGenerator initialization took {elapsed_time:.2f}s, suggesting blocking operations"

    @pytest.mark.asyncio
    async def test_event_service_with_ai_generator_non_blocking(self):
        """
        Test that EventService with AITaskGenerator doesn't block.

        Regression test ensuring the fix for lazy initialization is working.
        """
        # Arrange
        db = MagicMock()

        # Act
        start_time = time.time()
        service = EventService(db)
        # Access ai_generator to ensure it's created
        _ = service.ai_generator
        elapsed_time = time.time() - start_time

        # Assert
        assert elapsed_time < 0.1, \
            f"EventService with AITaskGenerator took {elapsed_time:.2f}s to initialize"
        assert service.ai_generator.rag_task_service is None, \
            "RAGTaskService should not be initialized during EventService creation"
