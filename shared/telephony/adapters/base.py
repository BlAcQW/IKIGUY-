"""
Base Telephony Adapter

This module provides the base adapter class with common functionality for all telephony providers.
"""

import asyncio
import logging
from abc import abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import httpx
from pydantic import BaseModel

from apps.shared.telephony.interfaces import TelephonyPort, TelephonyEvent
from apps.shared.telephony.models import CallContext, ProviderSettings, CallResult, ProviderHealth


class BaseTelephonyAdapter(TelephonyPort):
    """Base class for telephony provider adapters"""
    
    def __init__(self, settings: ProviderSettings):
        """
        Initialize the adapter with provider settings
        
        Args:
            settings: Provider configuration settings
        """
        self.settings = settings
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._http_client: Optional[httpx.AsyncClient] = None
        self._active_calls: Dict[str, Dict[str, Any]] = {}
        self._event_cache: Dict[str, List[TelephonyEvent]] = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the telephony provider
        
        Returns:
            bool: True if connection successful
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the telephony provider
        
        Returns:
            bool: True if disconnection successful
        """
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """
        Check if connected to the provider
        
        Returns:
            bool: True if connected
        """
        pass
    
    async def dial(self, to: str, from_: str, **kwargs) -> str:
        """
        Initiate a call and return call ID
        
        Args:
            to: Destination phone number
            from_: Source phone number or DID
            **kwargs: Additional call parameters
            
        Returns:
            str: Unique call identifier
        """
        try:
            # Validate input parameters
            if not to or not from_:
                raise ValueError("Destination and source numbers are required")
            
            # Create call context
            context = CallContext(
                destination=to,
                source=from_,
                tenant_id=kwargs.get('tenant_id', 'default'),
                campaign_id=kwargs.get('campaign_id'),
                cost_preference=kwargs.get('cost_preference', 'balanced'),
                quality_preference=kwargs.get('quality_preference', 'balanced'),
                geographic_region=kwargs.get('geographic_region'),
                metadata=kwargs
            )
            
            # Call provider-specific implementation
            call_id = await self._dial_impl(context)
            
            # Store call information
            self._active_calls[call_id] = {
                'context': context,
                'start_time': datetime.utcnow(),
                'status': 'initiated',
                'provider': self.settings.provider_id
            }
            
            # Allow adapter to store provider-specific data
            await self._store_provider_data(call_id)
            
            self.logger.info(f"Call initiated: {call_id} from {from_} to {to}")
            return call_id
            
        except Exception as e:
            self.logger.error(f"Failed to initiate call: {e}")
            raise
    
    @abstractmethod
    async def _dial_impl(self, context: CallContext) -> str:
        """
        Provider-specific call initiation implementation
        
        Args:
            context: Call context information
            
        Returns:
            str: Unique call identifier
        """
        pass
    
    async def _store_provider_data(self, call_id: str) -> None:
        """
        Store provider-specific data after call registration
        
        Args:
            call_id: Unique call identifier
        """
        # Default implementation does nothing
        # Override in subclasses to store provider-specific data
        pass
    
    async def hangup(self, call_id: str) -> bool:
        """
        End a call
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            bool: True if call was successfully ended
        """
        try:
            if call_id not in self._active_calls:
                raise ValueError(f"Call {call_id} not found")
            
            # Call provider-specific implementation
            success = await self._hangup_impl(call_id)
            
            if success:
                # Update call status
                self._active_calls[call_id]['status'] = 'ended'
                self._active_calls[call_id]['end_time'] = datetime.utcnow()
                
                self.logger.info(f"Call ended: {call_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to end call {call_id}: {e}")
            return False
    
    @abstractmethod
    async def _hangup_impl(self, call_id: str) -> bool:
        """
        Provider-specific call termination implementation
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            bool: True if call was successfully ended
        """
        pass
    
    async def get_events(self, call_id: str) -> List[TelephonyEvent]:
        """
        Get events for a call
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            List[TelephonyEvent]: List of telephony events
        """
        try:
            # Check cache first
            if call_id in self._event_cache:
                return self._event_cache[call_id]
            
            # Call provider-specific implementation
            events = await self._get_events_impl(call_id)
            
            # Cache events
            self._event_cache[call_id] = events
            
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to get events for call {call_id}: {e}")
            return []
    
    @abstractmethod
    async def _get_events_impl(self, call_id: str) -> List[TelephonyEvent]:
        """
        Provider-specific event retrieval implementation
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            List[TelephonyEvent]: List of telephony events
        """
        pass
    
    async def get_costs(self, call_id: str) -> Dict[str, float]:
        """
        Get cost breakdown for a call
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            Dict[str, float]: Cost breakdown by component
        """
        try:
            if call_id not in self._active_calls:
                return {}
            
            # Call provider-specific implementation
            costs = await self._get_costs_impl(call_id)
            
            # Apply cost multiplier from settings
            if self.settings.cost_multiplier != 1.0:
                costs = {k: v * self.settings.cost_multiplier for k, v in costs.items()}
            
            return costs
            
        except Exception as e:
            self.logger.error(f"Failed to get costs for call {call_id}: {e}")
            return {}
    
    @abstractmethod
    async def _get_costs_impl(self, call_id: str) -> Dict[str, float]:
        """
        Provider-specific cost calculation implementation
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            Dict[str, float]: Cost breakdown by component
        """
        pass
    
    async def health_check(self) -> ProviderHealth:
        """
        Perform health check for the provider
        
        Returns:
            ProviderHealth: Provider health status
        """
        try:
            start_time = datetime.utcnow()
            
            # Perform basic connectivity test
            is_healthy = await self.is_connected()
            
            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ProviderHealth(
                provider_id=self.settings.provider_id,
                is_healthy=is_healthy,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                cost_per_minute=await self._get_cost_per_minute(),
                supported_regions=await self._get_supported_regions(),
                features=await self._get_supported_features()
            )
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return ProviderHealth(
                provider_id=self.settings.provider_id,
                is_healthy=False,
                last_check=datetime.utcnow(),
                error_rate=100.0
            )
    
    @abstractmethod
    async def _get_cost_per_minute(self) -> Optional[float]:
        """Get cost per minute for this provider"""
        pass
    
    @abstractmethod
    async def _get_supported_regions(self) -> List[str]:
        """Get list of supported geographic regions"""
        pass
    
    @abstractmethod
    async def _get_supported_features(self) -> List[str]:
        """Get list of supported features"""
        pass
    
    async def _make_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Make HTTP request with retry logic
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Request parameters
            
        Returns:
            httpx.Response: HTTP response
        """
        if not self._http_client:
            self._http_client = httpx.AsyncClient(
                timeout=self.settings.timeout_seconds,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        
        for attempt in range(self.settings.retry_attempts):
            try:
                response = await self._http_client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < self.settings.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise
            except Exception as e:
                if attempt < self.settings.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
        
        raise httpx.RequestError("Max retry attempts exceeded")
    
    def _normalize_phone_number(self, number: str) -> str:
        """
        Normalize phone number format
        
        Args:
            number: Phone number to normalize
            
        Returns:
            str: Normalized phone number
        """
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, number))
        
        # Handle different country codes
        if digits.startswith('1') and len(digits) == 11:
            # US number with country code
            return f"+{digits}"
        elif len(digits) == 10:
            # US number without country code
            return f"+1{digits}"
        elif digits.startswith('00'):
            # International format with 00
            return f"+{digits[2:]}"
        elif digits.startswith('+'):
            # Already in international format
            return digits
        else:
            # Assume it's already in the correct format
            return f"+{digits}"
    
    def _create_telephony_event(self, event_type: str, call_id: str, data: Dict[str, Any]) -> TelephonyEvent:
        """
        Create a standardized telephony event
        
        Args:
            event_type: Type of event
            call_id: Call identifier
            data: Event data
            
        Returns:
            TelephonyEvent: Standardized telephony event
        """
        return TelephonyEvent(
            event_type=event_type,
            call_id=call_id,
            provider=self.settings.provider_id,
            data=data
        )
    
    async def _emit_event(self, event: TelephonyEvent) -> None:
        """
        Emit a telephony event
        
        Args:
            event: Telephony event to emit
        """
        try:
            # Store event in cache
            if event.call_id not in self._event_cache:
                self._event_cache[event.call_id] = []
            self._event_cache[event.call_id].append(event)
            
            # Log the event
            self.logger.debug(f"Emitted event: {event.event_type} for call {event.call_id}")
            
            # TODO: Implement event callback mechanism if needed
            # if hasattr(self, 'event_callback') and self.event_callback:
            #     await self.event_callback(event)
                
        except Exception as e:
            self.logger.error(f"Error emitting event: {e}")
