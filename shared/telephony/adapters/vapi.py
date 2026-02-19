"""
VAPI Telephony Adapter

This module provides the VAPI (Voice AI Platform) telephony adapter implementation.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import httpx

from .base import BaseTelephonyAdapter
from ..models import CallContext, ProviderHealth
from ..interfaces import TelephonyEvent


class VapiAdapter(BaseTelephonyAdapter):
    """VAPI telephony provider adapter"""
    
    def __init__(self, settings):
        super().__init__(settings)
        self._connected = False
        self._api_key = settings.api_key
        self._base_url = settings.base_url.rstrip('/')
        
    async def connect(self) -> bool:
        """
        Connect to VAPI
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Test connection by making a simple API call
            headers = {"Authorization": f"Bearer {self._api_key}"}
            response = await self._make_request("GET", f"{self._base_url}/assistants", headers=headers)
            
            self._connected = True
            self.logger.info("Connected to VAPI successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to VAPI: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from VAPI
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            if self._http_client:
                await self._http_client.aclose()
                self._http_client = None
            
            self._connected = False
            self.logger.info("Disconnected from VAPI")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from VAPI: {e}")
            return False
    
    async def is_connected(self) -> bool:
        """
        Check if connected to VAPI
        
        Returns:
            bool: True if connected
        """
        return self._connected
    
    async def _dial_impl(self, context: CallContext) -> str:
        """
        VAPI-specific call initiation implementation
        
        Args:
            context: Call context information
            
        Returns:
            str: Unique call identifier
        """
        try:
            # Generate unique call ID
            call_id = str(uuid.uuid4())
            
            # Prepare call request
            call_data = {
                "phoneNumberId": context.metadata.get('phone_number_id'),
                "assistantId": context.metadata.get('assistant_id'),
                "customer": {
                    "number": self._normalize_phone_number(context.destination)
                },
                "metadata": {
                    "call_id": call_id,
                    "tenant_id": context.tenant_id,
                    "campaign_id": context.campaign_id,
                    "source": context.source
                }
            }
            
            # Make API request to initiate call
            headers = {"Authorization": f"Bearer {self._api_key}"}
            response = await self._make_request(
                "POST", 
                f"{self._base_url}/calls", 
                json=call_data,
                headers=headers
            )
            
            response_data = response.json()
            
            # Store VAPI call ID temporarily
            vapi_call_id = response_data.get('id')
            if vapi_call_id:
                self._temp_vapi_call_id = vapi_call_id
            
            # Create initial event
            initial_event = self._create_telephony_event(
                "call_initiated",
                call_id,
                {
                    "vapi_call_id": vapi_call_id,
                    "status": response_data.get('status'),
                    "assistant_id": context.metadata.get('assistant_id')
                }
            )
            
            # Cache the event
            self._event_cache[call_id] = [initial_event]
            
            return call_id
            
        except Exception as e:
            self.logger.error(f"VAPI call initiation failed: {e}")
            raise
    
    async def _store_provider_data(self, call_id: str) -> None:
        """
        Store VAPI-specific data after call registration
        
        Args:
            call_id: Unique call identifier
        """
        if hasattr(self, '_temp_vapi_call_id') and self._temp_vapi_call_id:
            self._active_calls[call_id]['vapi_call_id'] = self._temp_vapi_call_id
            delattr(self, '_temp_vapi_call_id')
    
    async def _hangup_impl(self, call_id: str) -> bool:
        """
        VAPI-specific call termination implementation
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            bool: True if call was successfully ended
        """
        try:
            call_info = self._active_calls.get(call_id, {})
            vapi_call_id = call_info.get('vapi_call_id')
            
            if not vapi_call_id:
                self.logger.warning(f"No VAPI call ID found for {call_id}")
                return True  # Consider it successful if we don't have a VAPI call ID
            
            # Make API request to end call
            headers = {"Authorization": f"Bearer {self._api_key}"}
            await self._make_request(
                "POST",
                f"{self._base_url}/calls/{vapi_call_id}/end",
                headers=headers
            )
            
            # Create hangup event
            hangup_event = self._create_telephony_event(
                "call_ended",
                call_id,
                {
                    "vapi_call_id": vapi_call_id,
                    "reason": "user_requested"
                }
            )
            
            # Add to event cache
            if call_id in self._event_cache:
                self._event_cache[call_id].append(hangup_event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"VAPI call termination failed for {call_id}: {e}")
            return False
    
    async def _get_events_impl(self, call_id: str) -> List[TelephonyEvent]:
        """
        VAPI-specific event retrieval implementation
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            List[TelephonyEvent]: List of telephony events
        """
        try:
            call_info = self._active_calls.get(call_id, {})
            vapi_call_id = call_info.get('vapi_call_id')
            
            if not vapi_call_id:
                return []
            
            # Get call details from VAPI
            headers = {"Authorization": f"Bearer {self._api_key}"}
            response = await self._make_request(
                "GET",
                f"{self._base_url}/calls/{vapi_call_id}",
                headers=headers
            )
            
            call_data = response.json()
            
            # Convert VAPI events to standardized events
            events = []
            
            # Add call status event
            status_event = self._create_telephony_event(
                "call_status_update",
                call_id,
                {
                    "vapi_call_id": vapi_call_id,
                    "status": call_data.get('status'),
                    "duration": call_data.get('duration'),
                    "ended_at": call_data.get('endedAt'),
                    "started_at": call_data.get('startedAt')
                }
            )
            events.append(status_event)
            
            # Add transcript events if available
            transcript = call_data.get('transcript', [])
            for message in transcript:
                transcript_event = self._create_telephony_event(
                    "transcript_message",
                    call_id,
                    {
                        "vapi_call_id": vapi_call_id,
                        "role": message.get('role'),
                        "content": message.get('content'),
                        "timestamp": message.get('timestamp')
                    }
                )
                events.append(transcript_event)
            
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to get VAPI events for call {call_id}: {e}")
            return []
    
    async def _get_costs_impl(self, call_id: str) -> Dict[str, float]:
        """
        VAPI-specific cost calculation implementation
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            Dict[str, float]: Cost breakdown by component
        """
        try:
            call_info = self._active_calls.get(call_id, {})
            vapi_call_id = call_info.get('vapi_call_id')
            
            if not vapi_call_id:
                return {}
            
            # Get call details from VAPI
            headers = {"Authorization": f"Bearer {self._api_key}"}
            response = await self._make_request(
                "GET",
                f"{self._base_url}/calls/{vapi_call_id}",
                headers=headers
            )
            
            call_data = response.json()
            
            # Calculate costs based on VAPI pricing
            duration_minutes = call_data.get('duration', 0) / 60.0
            cost_per_minute = await self._get_cost_per_minute() or 0.02  # Default VAPI rate
            
            return {
                "voice_minutes": duration_minutes,
                "voice_cost": duration_minutes * cost_per_minute,
                "ai_processing": 0.01,  # Fixed cost for AI processing
                "total": (duration_minutes * cost_per_minute) + 0.01
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get VAPI costs for call {call_id}: {e}")
            return {}
    
    async def _get_cost_per_minute(self) -> Optional[float]:
        """Get cost per minute for VAPI"""
        # VAPI typically charges around $0.02 per minute for voice calls
        return 0.02
    
    async def _get_supported_regions(self) -> List[str]:
        """Get list of supported geographic regions for VAPI"""
        return [
            "US", "CA", "GB", "AU", "DE", "FR", "IT", "ES", "NL", "BE",
            "SE", "NO", "DK", "FI", "CH", "AT", "IE", "NZ", "JP", "KR"
        ]
    
    async def _get_supported_features(self) -> List[str]:
        """Get list of supported features for VAPI"""
        return [
            "voice_calls",
            "ai_assistant",
            "real_time_transcription",
            "sentiment_analysis",
            "call_recording",
            "webhook_events",
            "custom_assistants",
            "multi_language"
        ]
    
    async def get_call_status(self, call_id: str) -> Optional[str]:
        """
        Get current call status from VAPI
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            Optional[str]: Call status
        """
        try:
            call_info = self._active_calls.get(call_id, {})
            vapi_call_id = call_info.get('vapi_call_id')
            
            if not vapi_call_id:
                return None
            
            headers = {"Authorization": f"Bearer {self._api_key}"}
            response = await self._make_request(
                "GET",
                f"{self._base_url}/calls/{vapi_call_id}",
                headers=headers
            )
            
            call_data = response.json()
            return call_data.get('status')
            
        except Exception as e:
            self.logger.error(f"Failed to get call status for {call_id}: {e}")
            return None
