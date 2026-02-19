"""
Mixpanel Integration Module

This module provides integration with Mixpanel for advanced analytics,
user behavior tracking, and event analysis.
"""

import asyncio
import json
import logging
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    import requests
    MIXPANEL_AVAILABLE = True
except ImportError:
    MIXPANEL_AVAILABLE = False
    logging.warning("Mixpanel APIs not available. Install requests")

logger = logging.getLogger(__name__)


class MixpanelEventType(Enum):
    """Mixpanel event types."""
    TRACK = "track"
    IDENTIFY = "identify"
    ALIAS = "alias"
    SET = "set"
    SET_ONCE = "set_once"
    INCREMENT = "increment"
    APPEND = "append"
    UNION = "union"
    REMOVE = "remove"
    DELETE = "delete"


@dataclass
class MixpanelConfig:
    """Configuration for Mixpanel integration."""
    
    project_token: str
    """Mixpanel project token."""
    
    api_secret: str
    """Mixpanel API secret."""
    
    api_base_url: str = "https://api.mixpanel.com"
    """Mixpanel API base URL."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    batch_size: int = 50
    """Batch size for events."""
    
    enable_debug: bool = False
    """Enable debug mode."""


@dataclass
class MixpanelEvent:
    """Mixpanel event data structure."""
    
    event: str
    """Event name."""
    
    properties: Dict[str, Any]
    """Event properties."""
    
    distinct_id: Optional[str] = None
    """Distinct user ID."""
    
    time: Optional[datetime] = None
    """Event timestamp."""
    
    token: Optional[str] = None
    """Project token."""
    
    insert_id: Optional[str] = None
    """Insert ID for deduplication."""


@dataclass
class MixpanelUser:
    """Mixpanel user data structure."""
    
    distinct_id: str
    """Distinct user ID."""
    
    properties: Dict[str, Any]
    """User properties."""
    
    token: Optional[str] = None
    """Project token."""
    
    time: Optional[datetime] = None
    """Event timestamp."""


@dataclass
class MixpanelProfile:
    """Mixpanel profile data structure."""
    
    distinct_id: str
    """Distinct user ID."""
    
    properties: Dict[str, Any]
    """Profile properties."""
    
    token: Optional[str] = None
    """Project token."""
    
    time: Optional[datetime] = None
    """Event timestamp."""
    
    operation: str = "$set"
    """Profile operation ($set, $set_once, $add, $append, etc.)."""


@dataclass
class MixpanelFunnel:
    """Mixpanel funnel data structure."""
    
    funnel_id: int
    """Funnel ID."""
    
    name: str
    """Funnel name."""
    
    steps: List[Dict[str, Any]]
    """Funnel steps."""
    
    date_from: datetime
    """Start date."""
    
    date_to: datetime
    """End date."""
    
    interval: int = 1
    """Interval in days."""
    
    unit: str = "day"
    """Time unit."""


@dataclass
class MixpanelRetention:
    """Mixpanel retention data structure."""
    
    event: str
    """Event name."""
    
    date_from: datetime
    """Start date."""
    
    date_to: datetime
    """End date."""
    
    interval: int = 1
    """Interval in days."""
    
    unit: str = "day"
    """Time unit."""
    
    born_event: Optional[str] = None
    """Born event for cohort analysis."""


class MixpanelIntegration:
    """Mixpanel integration for advanced analytics and user behavior tracking."""
    
    def __init__(self, config: MixpanelConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def _get_timestamp(self, dt: Optional[datetime] = None) -> int:
        """Get timestamp for Mixpanel."""
        if dt is None:
            dt = datetime.now()
        return int(dt.timestamp())
    
    def _generate_insert_id(self, event: str, distinct_id: str, timestamp: int) -> str:
        """Generate insert ID for deduplication."""
        data = f"{event}_{distinct_id}_{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()
    
    async def track_event(
        self,
        event: str,
        distinct_id: str,
        properties: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        insert_id: Optional[str] = None
    ) -> bool:
        """
        Track an event.
        
        Args:
            event: Event name
            distinct_id: Distinct user ID
            properties: Event properties
            timestamp: Event timestamp
            insert_id: Insert ID for deduplication
            
        Returns:
            True if successful
        """
        try:
            if properties is None:
                properties = {}
            
            timestamp_int = self._get_timestamp(timestamp)
            
            if insert_id is None:
                insert_id = self._generate_insert_id(event, distinct_id, timestamp_int)
            
            event_data = {
                "event": event,
                "properties": {
                    "distinct_id": distinct_id,
                    "token": self.config.project_token,
                    "time": timestamp_int,
                    "insert_id": insert_id,
                    **properties
                }
            }
            
            url = f"{self.config.api_base_url}/track"
            response = self.session.post(url, json=event_data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") == 1:
                self.logger.info(f"Successfully tracked event: {event}")
                return True
            else:
                self.logger.error(f"Failed to track event: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to track event: {e}")
            return False
    
    async def track_batch_events(self, events: List[MixpanelEvent]) -> bool:
        """
        Track multiple events in batch.
        
        Args:
            events: List of events to track
            
        Returns:
            True if successful
        """
        try:
            # Process events in batches
            for i in range(0, len(events), self.config.batch_size):
                batch = events[i:i + self.config.batch_size]
                
                batch_data = []
                for event in batch:
                    timestamp_int = self._get_timestamp(event.time)
                    
                    if event.insert_id is None:
                        event.insert_id = self._generate_insert_id(
                            event.event, event.distinct_id or "unknown", timestamp_int
                        )
                    
                    event_data = {
                        "event": event.event,
                        "properties": {
                            "distinct_id": event.distinct_id or "unknown",
                            "token": event.token or self.config.project_token,
                            "time": timestamp_int,
                            "insert_id": event.insert_id,
                            **event.properties
                        }
                    }
                    batch_data.append(event_data)
                
                url = f"{self.config.api_base_url}/track"
                response = self.session.post(url, json=batch_data)
                response.raise_for_status()
                
                result = response.json()
                if result.get("status") != 1:
                    self.logger.error(f"Failed to track batch events: {result}")
                    return False
            
            self.logger.info(f"Successfully tracked {len(events)} events")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to track batch events: {e}")
            return False
    
    async def identify_user(
        self,
        distinct_id: str,
        properties: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Identify a user.
        
        Args:
            distinct_id: Distinct user ID
            properties: User properties
            timestamp: Event timestamp
            
        Returns:
            True if successful
        """
        try:
            if properties is None:
                properties = {}
            
            timestamp_int = self._get_timestamp(timestamp)
            
            event_data = {
                "$set": {
                    "distinct_id": distinct_id,
                    "token": self.config.project_token,
                    "time": timestamp_int,
                    **properties
                }
            }
            
            url = f"{self.config.api_base_url}/engage"
            response = self.session.post(url, json=event_data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") == 1:
                self.logger.info(f"Successfully identified user: {distinct_id}")
                return True
            else:
                self.logger.error(f"Failed to identify user: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to identify user: {e}")
            return False
    
    async def set_user_property(
        self,
        distinct_id: str,
        property_name: str,
        property_value: Any,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Set a user property.
        
        Args:
            distinct_id: Distinct user ID
            property_name: Property name
            property_value: Property value
            timestamp: Event timestamp
            
        Returns:
            True if successful
        """
        try:
            timestamp_int = self._get_timestamp(timestamp)
            
            event_data = {
                "$set": {
                    "distinct_id": distinct_id,
                    "token": self.config.project_token,
                    "time": timestamp_int,
                    property_name: property_value
                }
            }
            
            url = f"{self.config.api_base_url}/engage"
            response = self.session.post(url, json=event_data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") == 1:
                self.logger.info(f"Successfully set property {property_name} for user {distinct_id}")
                return True
            else:
                self.logger.error(f"Failed to set property: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to set property: {e}")
            return False
    
    async def increment_user_property(
        self,
        distinct_id: str,
        property_name: str,
        increment_value: Union[int, float] = 1,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Increment a user property.
        
        Args:
            distinct_id: Distinct user ID
            property_name: Property name
            increment_value: Value to increment by
            timestamp: Event timestamp
            
        Returns:
            True if successful
        """
        try:
            timestamp_int = self._get_timestamp(timestamp)
            
            event_data = {
                "$add": {
                    "distinct_id": distinct_id,
                    "token": self.config.project_token,
                    "time": timestamp_int,
                    property_name: increment_value
                }
            }
            
            url = f"{self.config.api_base_url}/engage"
            response = self.session.post(url, json=event_data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") == 1:
                self.logger.info(f"Successfully incremented property {property_name} for user {distinct_id}")
                return True
            else:
                self.logger.error(f"Failed to increment property: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to increment property: {e}")
            return False
    
    async def get_funnel_data(
        self,
        funnel_id: int,
        date_from: datetime,
        date_to: datetime,
        interval: int = 1,
        unit: str = "day"
    ) -> Dict[str, Any]:
        """
        Get funnel data.
        
        Args:
            funnel_id: Funnel ID
            date_from: Start date
            date_to: End date
            interval: Interval in days
            unit: Time unit
            
        Returns:
            Funnel data
        """
        try:
            url = f"{self.config.api_base_url}/funnels"
            
            params = {
                "funnel_id": funnel_id,
                "from_date": date_from.strftime("%Y-%m-%d"),
                "to_date": date_to.strftime("%Y-%m-%d"),
                "interval": interval,
                "unit": unit,
                "api_key": self.config.project_token
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get funnel data: {e}")
            raise
    
    async def get_retention_data(
        self,
        event: str,
        date_from: datetime,
        date_to: datetime,
        interval: int = 1,
        unit: str = "day",
        born_event: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get retention data.
        
        Args:
            event: Event name
            date_from: Start date
            date_to: End date
            interval: Interval in days
            unit: Time unit
            born_event: Born event for cohort analysis
            
        Returns:
            Retention data
        """
        try:
            url = f"{self.config.api_base_url}/retention"
            
            params = {
                "event": event,
                "from_date": date_from.strftime("%Y-%m-%d"),
                "to_date": date_to.strftime("%Y-%m-%d"),
                "interval": interval,
                "unit": unit,
                "api_key": self.config.project_token
            }
            
            if born_event:
                params["born_event"] = born_event
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get retention data: {e}")
            raise
    
    async def get_top_events(
        self,
        date_from: datetime,
        date_to: datetime,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get top events.
        
        Args:
            date_from: Start date
            date_to: End date
            limit: Number of events to return
            
        Returns:
            Top events data
        """
        try:
            url = f"{self.config.api_base_url}/events/top"
            
            params = {
                "from_date": date_from.strftime("%Y-%m-%d"),
                "to_date": date_to.strftime("%Y-%m-%d"),
                "limit": limit,
                "api_key": self.config.project_token
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get top events: {e}")
            raise
    
    async def get_event_properties(
        self,
        event: str,
        date_from: datetime,
        date_to: datetime,
        property_name: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get event properties.
        
        Args:
            event: Event name
            date_from: Start date
            date_to: End date
            property_name: Property name
            limit: Number of values to return
            
        Returns:
            Event properties data
        """
        try:
            url = f"{self.config.api_base_url}/events/properties/top"
            
            params = {
                "event": event,
                "from_date": date_from.strftime("%Y-%m-%d"),
                "to_date": date_to.strftime("%Y-%m-%d"),
                "name": property_name,
                "limit": limit,
                "api_key": self.config.project_token
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get event properties: {e}")
            raise
    
    async def get_user_profile(self, distinct_id: str) -> Dict[str, Any]:
        """
        Get user profile.
        
        Args:
            distinct_id: Distinct user ID
            
        Returns:
            User profile data
        """
        try:
            url = f"{self.config.api_base_url}/engage"
            
            params = {
                "distinct_id": distinct_id,
                "api_key": self.config.project_token
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get user profile: {e}")
            raise
    
    async def export_events(
        self,
        date_from: datetime,
        date_to: datetime,
        event: Optional[str] = None,
        where: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Export events.
        
        Args:
            date_from: Start date
            date_to: End date
            event: Event name filter
            where: Where clause filter
            
        Returns:
            List of events
        """
        try:
            url = f"{self.config.api_base_url}/export"
            
            params = {
                "from_date": date_from.strftime("%Y-%m-%d"),
                "to_date": date_to.strftime("%Y-%m-%d"),
                "api_key": self.config.project_token
            }
            
            if event:
                params["event"] = event
            if where:
                params["where"] = where
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # Parse JSONL response
            events = []
            for line in response.text.strip().split('\n'):
                if line:
                    events.append(json.loads(line))
            
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to export events: {e}")
            raise
    
    async def create_funnel(
        self,
        name: str,
        steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a funnel.
        
        Args:
            name: Funnel name
            steps: Funnel steps
            
        Returns:
            Created funnel data
        """
        try:
            url = f"{self.config.api_base_url}/funnels/create"
            
            data = {
                "name": name,
                "steps": steps,
                "api_key": self.config.project_token
            }
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to create funnel: {e}")
            raise
    
    async def list_funnels(self) -> List[Dict[str, Any]]:
        """
        List all funnels.
        
        Returns:
            List of funnels
        """
        try:
            url = f"{self.config.api_base_url}/funnels/list"
            
            params = {
                "api_key": self.config.project_token
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to list funnels: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Mixpanel integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by getting top events for today
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            
            top_events = await self.get_top_events(yesterday, today, limit=1)
            
            return {
                "status": "healthy",
                "project_token": self.config.project_token,
                "api_connectivity": "successful",
                "top_events_available": len(top_events.get("data", [])) > 0,
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }

