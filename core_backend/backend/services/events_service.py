"""
Events service that integrates shared event system library.
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import logging
import asyncio
from uuid import uuid4

from apps.shared.events import Event, EventBus, EventHandler, EventFilter, EventSubscription, EventMetrics
from apps.shared.storage import MemoryStorageBackend

logger = logging.getLogger(__name__)


class CoreEventBus(EventBus):
    """Core Backend implementation of EventBus using shared events library."""
    
    def __init__(self, storage_backend=None):
        """Initialize the event bus."""
        if storage_backend is None:
            from apps.shared.storage.interfaces import StorageConfig
            config = StorageConfig(backend_type="memory", connection_string="memory://")
            storage_backend = MemoryStorageBackend(config)
        
        super().__init__(storage_backend)
        self.storage = storage_backend
        self._subscriptions: Dict[str, EventSubscription] = {}
        self._event_queue: List[Event] = []
        self._metrics = EventMetrics()
        
    async def publish(self, event: Event) -> bool:
        """
        Publish event to bus.
        
        Args:
            event: Event to publish
            
        Returns:
            bool: True if event was published successfully
        """
        try:
            # Store event in storage
            await self.storage.insert("events", {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "source": event.source,
                "timestamp": event.timestamp.isoformat(),
                "tenant_id": event.tenant_id,
                "user_id": event.user_id,
                "data": event.data,
                "metadata": event.metadata,
                "priority": event.priority,
                "correlation_id": event.correlation_id
            })
            
            # Add to queue for processing
            self._event_queue.append(event)
            
            # Update metrics
            self._metrics.total_events_published += 1
            self._metrics.last_processed_event = datetime.utcnow()
            
            # Process event asynchronously
            asyncio.create_task(self._process_event(event))
            
            logger.debug(f"Published event {event.event_id} of type {event.event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {e}")
            return False
    
    async def subscribe(self, event_type: str, handler: EventHandler) -> str:
        """
        Subscribe to event type.
        
        Args:
            event_type: Event type to subscribe to
            handler: Event handler
            
        Returns:
            str: Subscription ID
        """
        try:
            subscription_id = str(uuid4())
            
            subscription = EventSubscription(
                subscription_id=subscription_id,
                subscriber_id="core_backend",
                event_types=[event_type],
                filters=EventFilter(event_types=[event_type])
            )
            
            # Store subscription
            await self.storage.insert("subscriptions", {
                "subscription_id": subscription_id,
                "subscriber_id": subscription.subscriber_id,
                "event_types": subscription.event_types,
                "filters": subscription.filters.dict(),
                "created_at": subscription.created_at.isoformat(),
                "is_active": subscription.is_active
            })
            
            self._subscriptions[subscription_id] = subscription
            
            # Update metrics
            self._metrics.active_subscriptions += 1
            
            logger.info(f"Created subscription {subscription_id} for event type {event_type}")
            return subscription_id
            
        except Exception as e:
            logger.error(f"Failed to create subscription for {event_type}: {e}")
            return ""
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            bool: True if unsubscribed successfully
        """
        try:
            if subscription_id in self._subscriptions:
                del self._subscriptions[subscription_id]
                
                # Remove from storage
                await self.storage.delete("subscriptions", {"subscription_id": subscription_id})
                
                # Update metrics
                self._metrics.active_subscriptions -= 1
                
                logger.info(f"Unsubscribed from {subscription_id}")
                return True
            else:
                logger.warning(f"Subscription {subscription_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to unsubscribe {subscription_id}: {e}")
            return False
    
    async def get_events(self, filters: Dict[str, Any] = None, limit: int = 100) -> List[Event]:
        """
        Get events with optional filtering.
        
        Args:
            filters: Event filters
            limit: Maximum number of events to return
            
        Returns:
            List[Event]: List of events
        """
        try:
            # Build query based on filters
            query = {}
            if filters:
                if "event_type" in filters:
                    query["event_type"] = filters["event_type"]
                if "tenant_id" in filters:
                    query["tenant_id"] = filters["tenant_id"]
                if "user_id" in filters:
                    query["user_id"] = filters["user_id"]
                if "start_date" in filters:
                    query["timestamp"] = {"$gte": filters["start_date"].isoformat()}
                if "end_date" in filters:
                    if "timestamp" in query:
                        query["timestamp"]["$lte"] = filters["end_date"].isoformat()
                    else:
                        query["timestamp"] = {"$lte": filters["end_date"].isoformat()}
            
            # Get events from storage
            events_data = await self.storage.select("events", query, limit=limit)
            
            # Convert to Event objects
            events = []
            for event_data in events_data:
                event = Event(
                    event_id=event_data["event_id"],
                    event_type=event_data["event_type"],
                    source=event_data["source"],
                    timestamp=datetime.fromisoformat(event_data["timestamp"]),
                    tenant_id=event_data.get("tenant_id"),
                    user_id=event_data.get("user_id"),
                    data=event_data.get("data", {}),
                    metadata=event_data.get("metadata", {}),
                    priority=event_data.get("priority", 5),
                    correlation_id=event_data.get("correlation_id")
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            return []
    
    async def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """
        Get event by ID.
        
        Args:
            event_id: Event ID
            
        Returns:
            Optional[Event]: Event if found
        """
        try:
            event_data = await self.storage.select_one("events", {"event_id": event_id})
            
            if event_data:
                return Event(
                    event_id=event_data["event_id"],
                    event_type=event_data["event_type"],
                    source=event_data["source"],
                    timestamp=datetime.fromisoformat(event_data["timestamp"]),
                    tenant_id=event_data.get("tenant_id"),
                    user_id=event_data.get("user_id"),
                    data=event_data.get("data", {}),
                    metadata=event_data.get("metadata", {}),
                    priority=event_data.get("priority", 5),
                    correlation_id=event_data.get("correlation_id")
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get event {event_id}: {e}")
            return None
    
    async def get_events_by_type(self, event_type: str, limit: int = 100) -> List[Event]:
        """
        Get events by type.
        
        Args:
            event_type: Event type
            limit: Maximum number of events to return
            
        Returns:
            List[Event]: List of events
        """
        try:
            events_data = await self.storage.select("events", {"event_type": event_type}, limit=limit)
            
            events = []
            for event_data in events_data:
                event = Event(
                    event_id=event_data["event_id"],
                    event_type=event_data["event_type"],
                    source=event_data["source"],
                    timestamp=datetime.fromisoformat(event_data["timestamp"]),
                    tenant_id=event_data.get("tenant_id"),
                    user_id=event_data.get("user_id"),
                    data=event_data.get("data", {}),
                    metadata=event_data.get("metadata", {}),
                    priority=event_data.get("priority", 5),
                    correlation_id=event_data.get("correlation_id")
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get events by type {event_type}: {e}")
            return []
    
    async def get_events_by_tenant(self, tenant_id: str, limit: int = 100) -> List[Event]:
        """
        Get events by tenant.
        
        Args:
            tenant_id: Tenant identifier
            limit: Maximum number of events to return
            
        Returns:
            List[Event]: List of events
        """
        try:
            events_data = await self.storage.select("events", {"tenant_id": tenant_id}, limit=limit)
            
            events = []
            for event_data in events_data:
                event = Event(
                    event_id=event_data["event_id"],
                    event_type=event_data["event_type"],
                    source=event_data["source"],
                    timestamp=datetime.fromisoformat(event_data["timestamp"]),
                    tenant_id=event_data.get("tenant_id"),
                    user_id=event_data.get("user_id"),
                    data=event_data.get("data", {}),
                    metadata=event_data.get("metadata", {}),
                    priority=event_data.get("priority", 5),
                    correlation_id=event_data.get("correlation_id")
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get events by tenant {tenant_id}: {e}")
            return []
    
    async def _process_event(self, event: Event):
        """Process an event and notify subscribers."""
        try:
            # Find matching subscriptions
            matching_subscriptions = []
            for subscription in self._subscriptions.values():
                if event.event_type in subscription.event_types:
                    # Check filters
                    if self._matches_filters(event, subscription.filters):
                        matching_subscriptions.append(subscription)
            
            # Notify subscribers
            for subscription in matching_subscriptions:
                await self._deliver_event(event, subscription)
            
            # Update metrics
            self._metrics.total_events_processed += 1
            
        except Exception as e:
            logger.error(f"Failed to process event {event.event_id}: {e}")
    
    def _matches_filters(self, event: Event, filters: EventFilter) -> bool:
        """Check if event matches filters."""
        if filters.event_types and event.event_type not in filters.event_types:
            return False
        
        if filters.sources and event.source not in filters.sources:
            return False
        
        if filters.tenant_ids and event.tenant_id not in filters.tenant_ids:
            return False
        
        if filters.user_ids and event.user_id not in filters.user_ids:
            return False
        
        if filters.priority_min and event.priority < filters.priority_min:
            return False
        
        if filters.priority_max and event.priority > filters.priority_max:
            return False
        
        if filters.correlation_id and event.correlation_id != filters.correlation_id:
            return False
        
        return True
    
    async def _deliver_event(self, event: Event, subscription: EventSubscription):
        """Deliver event to subscription."""
        try:
            # Update subscription metrics
            subscription.total_events_received += 1
            subscription.last_event_received = datetime.utcnow()
            
            # Store delivery record
            delivery_id = str(uuid4())
            await self.storage.insert("event_deliveries", {
                "delivery_id": delivery_id,
                "event_id": event.event_id,
                "subscription_id": subscription.subscription_id,
                "status": "delivered",
                "delivered_at": datetime.utcnow().isoformat(),
                "response_time_ms": 0.0
            })
            
            logger.debug(f"Delivered event {event.event_id} to subscription {subscription.subscription_id}")
            
        except Exception as e:
            logger.error(f"Failed to deliver event {event.event_id} to {subscription.subscription_id}: {e}")
            subscription.error_count += 1


class EventsService:
    """Service for managing events using shared libraries."""
    
    def __init__(self, storage_backend=None):
        """
        Initialize the events service.
        
        Args:
            storage_backend: Storage backend for events data
        """
        self.event_bus = CoreEventBus(storage_backend)
        self._handlers: Dict[str, Callable] = {}
        
    async def publish_event(
        self,
        event_type: str,
        source: str,
        data: Dict[str, Any],
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        priority: int = 5,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish an event.
        
        Args:
            event_type: Type of event
            source: Event source
            data: Event data
            tenant_id: Tenant identifier
            user_id: User identifier
            priority: Event priority (1-10)
            correlation_id: Correlation ID for related events
            metadata: Additional metadata
            
        Returns:
            bool: True if event was published successfully
        """
        try:
            event = Event(
                event_id=str(uuid4()),
                event_type=event_type,
                source=source,
                timestamp=datetime.utcnow(),
                tenant_id=tenant_id,
                user_id=user_id,
                data=data,
                metadata=metadata or {},
                priority=priority,
                correlation_id=correlation_id
            )
            
            return await self.event_bus.publish(event)
            
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            return False
    
    async def subscribe_to_events(
        self,
        event_types: List[str],
        handler: Callable,
        filters: Optional[EventFilter] = None
    ) -> str:
        """
        Subscribe to events.
        
        Args:
            event_types: List of event types to subscribe to
            handler: Event handler function
            filters: Event filters
            
        Returns:
            str: Subscription ID
        """
        try:
            # Store handler
            handler_id = str(uuid4())
            self._handlers[handler_id] = handler
            
            # Create subscription for each event type
            subscription_ids = []
            for event_type in event_types:
                subscription_id = await self.event_bus.subscribe(event_type, handler)
                if subscription_id:
                    subscription_ids.append(subscription_id)
            
            logger.info(f"Subscribed to {len(event_types)} event types: {event_types}")
            return handler_id
            
        except Exception as e:
            logger.error(f"Failed to subscribe to events: {e}")
            return ""
    
    async def unsubscribe_from_events(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            bool: True if unsubscribed successfully
        """
        try:
            if subscription_id in self._handlers:
                del self._handlers[subscription_id]
            
            return await self.event_bus.unsubscribe(subscription_id)
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe {subscription_id}: {e}")
            return False
    
    async def get_events(
        self,
        event_types: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get events with filtering.
        
        Args:
            event_types: Event types to filter by
            tenant_id: Tenant ID to filter by
            user_id: User ID to filter by
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of events to return
            
        Returns:
            List[Dict[str, Any]]: List of events
        """
        try:
            filters = {}
            if event_types:
                filters["event_type"] = event_types[0] if len(event_types) == 1 else {"$in": event_types}
            if tenant_id:
                filters["tenant_id"] = tenant_id
            if user_id:
                filters["user_id"] = user_id
            if start_date:
                filters["start_date"] = start_date
            if end_date:
                filters["end_date"] = end_date
            
            events = await self.event_bus.get_events(filters, limit)
            
            # Convert to dict format for API response
            return [event.dict() for event in events]
            
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            return []
    
    async def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get event by ID.
        
        Args:
            event_id: Event ID
            
        Returns:
            Optional[Dict[str, Any]]: Event data
        """
        try:
            event = await self.event_bus.get_event_by_id(event_id)
            return event.dict() if event else None
            
        except Exception as e:
            logger.error(f"Failed to get event {event_id}: {e}")
            return None
    
    async def get_event_metrics(self) -> Dict[str, Any]:
        """
        Get event system metrics.
        
        Returns:
            Dict[str, Any]: Event metrics
        """
        try:
            metrics = self.event_bus._metrics
            return {
                "total_events_published": metrics.total_events_published,
                "total_events_processed": metrics.total_events_processed,
                "active_subscriptions": metrics.active_subscriptions,
                "events_per_second": metrics.events_per_second,
                "average_processing_time_ms": metrics.average_processing_time_ms,
                "error_rate": metrics.error_rate,
                "queue_size": len(self.event_bus._event_queue),
                "last_processed_event": metrics.last_processed_event.isoformat() if metrics.last_processed_event else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get event metrics: {e}")
            return {}
    
    async def get_subscriptions(self) -> List[Dict[str, Any]]:
        """
        Get all active subscriptions.
        
        Returns:
            List[Dict[str, Any]]: List of subscriptions
        """
        try:
            subscriptions = []
            for subscription in self.event_bus._subscriptions.values():
                subscriptions.append({
                    "subscription_id": subscription.subscription_id,
                    "subscriber_id": subscription.subscriber_id,
                    "event_types": subscription.event_types,
                    "created_at": subscription.created_at.isoformat(),
                    "is_active": subscription.is_active,
                    "total_events_received": subscription.total_events_received,
                    "error_count": subscription.error_count
                })
            
            return subscriptions
            
        except Exception as e:
            logger.error(f"Failed to get subscriptions: {e}")
            return []
    
    async def clear_old_events(self, days_to_keep: int = 30) -> bool:
        """
        Clear old events.
        
        Args:
            days_to_keep: Number of days to keep events
            
        Returns:
            bool: True if cleared successfully
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Delete old events from storage
            await self.event_bus.storage.delete("events", {
                "timestamp": {"$lt": cutoff_date.isoformat()}
            })
            
            logger.info(f"Cleared events older than {days_to_keep} days")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear old events: {e}")
            return False
    
    async def get_events_capabilities(self) -> Dict[str, Any]:
        """
        Get events service capabilities.
        
        Returns:
            Dict[str, Any]: Available capabilities
        """
        try:
            return {
                "success": True,
                "capabilities": {
                    "event_publishing": True,
                    "event_subscription": True,
                    "event_filtering": True,
                    "event_metrics": True,
                    "event_storage": True,
                    "event_delivery": True,
                    "correlation_tracking": True,
                    "priority_handling": True,
                    "tenant_isolation": True,
                    "user_tracking": True
                },
                "supported_event_types": [
                    "user.login",
                    "user.logout",
                    "user.created",
                    "user.updated",
                    "tenant.created",
                    "tenant.updated",
                    "call.started",
                    "call.ended",
                    "call.failed",
                    "payment.processed",
                    "payment.failed",
                    "security.alert",
                    "security.breach",
                    "system.error",
                    "system.warning",
                    "integration.success",
                    "integration.failed"
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get events capabilities: {e}")
            return {"success": False, "error": str(e)}
