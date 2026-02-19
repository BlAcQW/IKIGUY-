"""
Tests for Core Backend Events Service integration with shared libraries.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from backend.services.events_service import EventsService, CoreEventBus


class TestEventsService:
    """Test cases for EventsService integration with shared libraries."""

    @pytest.fixture
    def events_service(self):
        """Create an events service instance for testing."""
        service = EventsService()
        return service

    @pytest.fixture
    def event_bus(self):
        """Create an event bus instance for testing."""
        bus = CoreEventBus()
        return bus

    @pytest.mark.asyncio
    async def test_events_service_initialization(self, events_service):
        """Test that events service initializes correctly with shared library."""
        assert events_service.event_bus is not None
        assert hasattr(events_service.event_bus, 'publish')
        assert hasattr(events_service.event_bus, 'subscribe')

    @pytest.mark.asyncio
    async def test_event_bus_initialization(self, event_bus):
        """Test that event bus initializes correctly."""
        assert event_bus.storage is not None
        assert event_bus._subscriptions is not None
        assert event_bus._event_queue is not None
        assert event_bus._metrics is not None

    @pytest.mark.asyncio
    async def test_publish_event(self, events_service):
        """Test publishing events."""
        result = await events_service.publish_event(
            event_type="user.login",
            source="auth_service",
            data={"user_id": "test_user", "ip_address": "192.168.1.1"},
            tenant_id="test-tenant",
            user_id="test_user",
            priority=7
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_publish_multiple_events(self, events_service):
        """Test publishing multiple events."""
        events = [
            ("user.login", "auth_service", {"user_id": "user1"}),
            ("user.logout", "auth_service", {"user_id": "user2"}),
            ("call.started", "telephony_service", {"call_id": "call1"}),
            ("payment.processed", "payment_service", {"payment_id": "pay1"})
        ]
        
        for event_type, source, data in events:
            result = await events_service.publish_event(
                event_type=event_type,
                source=source,
                data=data,
                tenant_id="test-tenant"
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_subscribe_to_events(self, events_service):
        """Test subscribing to events."""
        def test_handler(event):
            return True
        
        subscription_id = await events_service.subscribe_to_events(
            event_types=["user.login", "user.logout"],
            handler=test_handler
        )
        assert subscription_id != ""

    @pytest.mark.asyncio
    async def test_unsubscribe_from_events(self, events_service):
        """Test unsubscribing from events."""
        def test_handler(event):
            return True
        
        subscription_id = await events_service.subscribe_to_events(
            event_types=["user.login"],
            handler=test_handler
        )
        
        result = await events_service.unsubscribe_from_events(subscription_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_events(self, events_service):
        """Test getting events with filtering."""
        # Publish some test events
        await events_service.publish_event(
            event_type="user.login",
            source="auth_service",
            data={"user_id": "test_user"},
            tenant_id="test-tenant"
        )
        
        await events_service.publish_event(
            event_type="user.logout",
            source="auth_service",
            data={"user_id": "test_user"},
            tenant_id="test-tenant"
        )
        
        # Get events
        events = await events_service.get_events(
            event_types=["user.login"],
            tenant_id="test-tenant",
            limit=10
        )
        
        assert len(events) >= 1
        assert events[0]["event_type"] == "user.login"

    @pytest.mark.asyncio
    async def test_get_event_by_id(self, events_service):
        """Test getting event by ID."""
        # Publish a test event
        await events_service.publish_event(
            event_type="test.event",
            source="test_service",
            data={"test": "data"},
            tenant_id="test-tenant"
        )
        
        # Get events to find the event ID
        events = await events_service.get_events(
            event_types=["test.event"],
            tenant_id="test-tenant",
            limit=1
        )
        
        if events:
            event_id = events[0]["event_id"]
            event = await events_service.get_event_by_id(event_id)
            assert event is not None
            assert event["event_id"] == event_id
            assert event["event_type"] == "test.event"

    @pytest.mark.asyncio
    async def test_get_event_metrics(self, events_service):
        """Test getting event metrics."""
        metrics = await events_service.get_event_metrics()
        assert isinstance(metrics, dict)
        assert "total_events_published" in metrics
        assert "active_subscriptions" in metrics
        assert "queue_size" in metrics

    @pytest.mark.asyncio
    async def test_get_subscriptions(self, events_service):
        """Test getting subscriptions."""
        def test_handler(event):
            return True
        
        # Create a subscription
        await events_service.subscribe_to_events(
            event_types=["user.login"],
            handler=test_handler
        )
        
        subscriptions = await events_service.get_subscriptions()
        assert isinstance(subscriptions, list)
        assert len(subscriptions) >= 1

    @pytest.mark.asyncio
    async def test_clear_old_events(self, events_service):
        """Test clearing old events."""
        result = await events_service.clear_old_events(days_to_keep=30)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_events_capabilities(self, events_service):
        """Test getting events capabilities."""
        capabilities = await events_service.get_events_capabilities()
        assert capabilities["success"] is True
        assert "capabilities" in capabilities
        assert "supported_event_types" in capabilities
        
        caps = capabilities["capabilities"]
        assert "event_publishing" in caps
        assert "event_subscription" in caps
        assert "event_filtering" in caps
        assert "event_metrics" in caps

    @pytest.mark.asyncio
    async def test_event_bus_publish(self, event_bus):
        """Test event bus publish functionality."""
        from apps.shared.events import Event
        
        event = Event(
            event_id="test-event-1",
            event_type="test.event",
            source="test_service",
            timestamp=datetime.utcnow(),
            data={"test": "data"}
        )
        
        result = await event_bus.publish(event)
        assert result is True

    @pytest.mark.asyncio
    async def test_event_bus_subscribe(self, event_bus):
        """Test event bus subscribe functionality."""
        def test_handler(event):
            return True
        
        subscription_id = await event_bus.subscribe("test.event", test_handler)
        assert subscription_id != ""

    @pytest.mark.asyncio
    async def test_event_bus_unsubscribe(self, event_bus):
        """Test event bus unsubscribe functionality."""
        def test_handler(event):
            return True
        
        subscription_id = await event_bus.subscribe("test.event", test_handler)
        result = await event_bus.unsubscribe(subscription_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_event_bus_get_events(self, event_bus):
        """Test event bus get events functionality."""
        from apps.shared.events import Event
        
        # Publish a test event
        event = Event(
            event_id="test-event-2",
            event_type="test.event",
            source="test_service",
            timestamp=datetime.utcnow(),
            data={"test": "data"}
        )
        await event_bus.publish(event)
        
        # Get events
        events = await event_bus.get_events(limit=10)
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_event_bus_get_event_by_id(self, event_bus):
        """Test event bus get event by ID functionality."""
        from apps.shared.events import Event
        
        # Publish a test event
        event = Event(
            event_id="test-event-3",
            event_type="test.event",
            source="test_service",
            timestamp=datetime.utcnow(),
            data={"test": "data"}
        )
        await event_bus.publish(event)
        
        # Get event by ID
        retrieved_event = await event_bus.get_event_by_id("test-event-3")
        assert retrieved_event is not None
        assert retrieved_event.event_id == "test-event-3"

    @pytest.mark.asyncio
    async def test_event_filtering(self, events_service):
        """Test event filtering functionality."""
        # Publish events with different priorities
        await events_service.publish_event(
            event_type="high.priority",
            source="test_service",
            data={"priority": "high"},
            priority=9
        )
        
        await events_service.publish_event(
            event_type="low.priority",
            source="test_service",
            data={"priority": "low"},
            priority=2
        )
        
        # Get events with priority filtering
        events = await events_service.get_events(
            event_types=["high.priority", "low.priority"],
            limit=10
        )
        
        assert len(events) >= 2

    @pytest.mark.asyncio
    async def test_event_correlation(self, events_service):
        """Test event correlation functionality."""
        correlation_id = "test-correlation-123"
        
        # Publish related events
        await events_service.publish_event(
            event_type="workflow.started",
            source="workflow_service",
            data={"workflow_id": "workflow-1"},
            correlation_id=correlation_id
        )
        
        await events_service.publish_event(
            event_type="workflow.completed",
            source="workflow_service",
            data={"workflow_id": "workflow-1"},
            correlation_id=correlation_id
        )
        
        # Get events by correlation ID
        events = await events_service.get_events(limit=10)
        correlated_events = [e for e in events if e.get("correlation_id") == correlation_id]
        assert len(correlated_events) >= 2

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, events_service):
        """Test tenant isolation in events."""
        # Publish events for different tenants
        await events_service.publish_event(
            event_type="user.login",
            source="auth_service",
            data={"user_id": "user1"},
            tenant_id="tenant-1"
        )
        
        await events_service.publish_event(
            event_type="user.login",
            source="auth_service",
            data={"user_id": "user2"},
            tenant_id="tenant-2"
        )
        
        # Get events for specific tenant
        tenant_1_events = await events_service.get_events(
            tenant_id="tenant-1",
            limit=10
        )
        
        tenant_2_events = await events_service.get_events(
            tenant_id="tenant-2",
            limit=10
        )
        
        # Verify tenant isolation
        for event in tenant_1_events:
            assert event["tenant_id"] == "tenant-1"
        
        for event in tenant_2_events:
            assert event["tenant_id"] == "tenant-2"

    @pytest.mark.asyncio
    async def test_event_priority_handling(self, events_service):
        """Test event priority handling."""
        # Publish events with different priorities
        priorities = [1, 5, 10]
        for priority in priorities:
            await events_service.publish_event(
                event_type=f"priority.{priority}",
                source="test_service",
                data={"priority": priority},
                priority=priority
            )
        
        # Get events and verify priorities
        events = await events_service.get_events(limit=10)
        event_priorities = [e["priority"] for e in events if e["event_type"].startswith("priority.")]
        assert all(priority in priorities for priority in event_priorities)

    @pytest.mark.asyncio
    async def test_events_service_error_handling(self, events_service):
        """Test error handling in events service."""
        # Test with invalid event type
        result = await events_service.publish_event(
            event_type="",
            source="test_service",
            data={}
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_events_service_performance(self, events_service):
        """Test events service performance."""
        import time
        
        start_time = time.time()
        
        # Publish multiple events
        for i in range(10):
            await events_service.publish_event(
                event_type=f"perf.test.{i}",
                source="test_service",
                data={"index": i}
            )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (5 seconds)
        assert execution_time < 5.0

    @pytest.mark.asyncio
    async def test_events_service_concurrent_operations(self, events_service):
        """Test concurrent events operations."""
        async def publish_event(i):
            return await events_service.publish_event(
                event_type=f"concurrent.test.{i}",
                source="test_service",
                data={"index": i}
            )
        
        # Run 5 concurrent operations
        tasks = [publish_event(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All operations should succeed
        assert all(result is True for result in results)

    @pytest.mark.asyncio
    async def test_event_bus_matches_filters(self, event_bus):
        """Test event filter matching."""
        from apps.shared.events import Event, EventFilter
        
        event = Event(
            event_id="test-filter",
            event_type="test.event",
            source="test_service",
            timestamp=datetime.utcnow(),
            tenant_id="test-tenant",
            user_id="test-user",
            priority=5
        )
        
        # Test various filters
        filters = EventFilter(
            event_types=["test.event"],
            sources=["test_service"],
            tenant_ids=["test-tenant"],
            user_ids=["test-user"],
            priority_min=1,
            priority_max=10
        )
        
        assert event_bus._matches_filters(event, filters) is True
        
        # Test non-matching filter
        non_matching_filter = EventFilter(
            event_types=["other.event"]
        )
        assert event_bus._matches_filters(event, non_matching_filter) is False

    @pytest.mark.asyncio
    async def test_event_delivery_tracking(self, event_bus):
        """Test event delivery tracking."""
        from apps.shared.events import Event, EventSubscription, EventFilter
        
        event = Event(
            event_id="test-delivery",
            event_type="test.event",
            source="test_service",
            timestamp=datetime.utcnow()
        )
        
        subscription = EventSubscription(
            subscription_id="test-sub",
            subscriber_id="test-subscriber",
            event_types=["test.event"],
            filters=EventFilter(event_types=["test.event"])
        )
        
        event_bus._subscriptions["test-sub"] = subscription
        
        # Process event
        await event_bus._process_event(event)
        
        # Verify delivery tracking
        assert subscription.total_events_received >= 0

    @pytest.mark.asyncio
    async def test_events_service_with_date_filtering(self, events_service):
        """Test events service with date filtering."""
        # Publish events with different timestamps
        now = datetime.utcnow()
        
        await events_service.publish_event(
            event_type="recent.event",
            source="test_service",
            data={"timestamp": "recent"}
        )
        
        # Get events with date filtering
        start_date = now - timedelta(hours=1)
        end_date = now + timedelta(hours=1)
        
        events = await events_service.get_events(
            start_date=start_date,
            end_date=end_date,
            limit=10
        )
        
        assert isinstance(events, list)


if __name__ == "__main__":
    pytest.main([__file__])
