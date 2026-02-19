"""
Event System Interfaces

This module defines the core event system interfaces used across all components.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .interfaces import EventHandler


class Event(BaseModel):
    """Event structure"""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Event type")
    source: str = Field(..., description="Event source component")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Event metadata")
    priority: int = Field(5, description="Event priority (1-10, higher is more important)")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for related events")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EventBus(ABC):
    """Event bus for publishing and subscribing to events"""
    
    def __init__(self, backend: Any):
        self.backend = backend
        self.subscribers: Dict[str, List['EventHandler']] = {}
    
    @abstractmethod
    async def publish(self, event: Event) -> bool:
        """
        Publish event to bus
        
        Args:
            event: Event to publish
            
        Returns:
            bool: True if event was published successfully
        """
        pass
    
    @abstractmethod
    async def subscribe(self, event_type: str, handler: 'EventHandler') -> str:
        """
        Subscribe to event type
        
        Args:
            event_type: Event type to subscribe to
            handler: Event handler
            
        Returns:
            str: Subscription ID
        """
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            bool: True if unsubscribed successfully
        """
        pass
    
    @abstractmethod
    async def get_events(self, filters: Dict[str, Any] = None, limit: int = 100) -> List[Event]:
        """
        Get events with optional filtering
        
        Args:
            filters: Event filters
            limit: Maximum number of events to return
            
        Returns:
            List[Event]: List of events
        """
        pass
    
    @abstractmethod
    async def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """
        Get event by ID
        
        Args:
            event_id: Event identifier
            
        Returns:
            Optional[Event]: Event if found
        """
        pass
    
    @abstractmethod
    async def get_events_by_type(self, event_type: str, limit: int = 100) -> List[Event]:
        """
        Get events by type
        
        Args:
            event_type: Event type
            limit: Maximum number of events to return
            
        Returns:
            List[Event]: List of events
        """
        pass
    
    @abstractmethod
    async def get_events_by_tenant(self, tenant_id: str, limit: int = 100) -> List[Event]:
        """
        Get events by tenant
        
        Args:
            tenant_id: Tenant identifier
            limit: Maximum number of events to return
            
        Returns:
            List[Event]: List of events
        """
        pass


class EventHandler(ABC):
    """Abstract event handler"""
    
    @abstractmethod
    async def handle(self, event: Event) -> bool:
        """
        Handle event
        
        Args:
            event: Event to handle
            
        Returns:
            bool: True if event was handled successfully
        """
        pass
    
    @abstractmethod
    async def can_handle(self, event: Event) -> bool:
        """
        Check if handler can handle event
        
        Args:
            event: Event to check
            
        Returns:
            bool: True if handler can handle event
        """
        pass
    
    @abstractmethod
    async def get_priority(self) -> int:
        """
        Get handler priority
        
        Returns:
            int: Handler priority (1-10, higher is more important)
        """
        pass
