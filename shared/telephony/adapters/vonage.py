"""
Vonage Telephony Adapter

This module provides the Vonage telephony adapter implementation.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import httpx

from .base import BaseTelephonyAdapter
from ..models import CallContext, ProviderHealth
from ..interfaces import TelephonyEvent


class VonageAdapter(BaseTelephonyAdapter):
    """Vonage telephony provider adapter"""
    
    def __init__(self, settings):
        super().__init__(settings)
        self._connected = False
        self._api_key = settings.api_key
        self._api_secret = settings.api_secret
        self._base_url = settings.base_url.rstrip('/')
        
    async def connect(self) -> bool:
        """
        Connect to Vonage
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Test connection by making a simple API call
            params = {
                "api_key": self._api_key,
                "api_secret": self._api_secret
            }
            response = await self._make_request("GET", f"{self._base_url}/account/numbers", params=params)
            
            self._connected = True
            self.logger.info("Connected to Vonage successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Vonage: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Vonage
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            if self._http_client:
                await self._http_client.aclose()
                self._http_client = None
            
            self._connected = False
            self.logger.info("Disconnected from Vonage")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from Vonage: {e}")
            return False
    
    async def is_connected(self) -> bool:
        """
        Check if connected to Vonage
        
        Returns:
            bool: True if connected
        """
        return self._connected
    
    async def _dial_impl(self, context: CallContext) -> str:
        """
        Vonage-specific call initiation implementation
        
        Args:
            context: Call context information
            
        Returns:
            str: Unique call identifier
        """
        try:
            # Generate unique call ID
            call_id = str(uuid.uuid4())
            
            # Prepare call request for Vonage Voice API
            call_data = {
                "api_key": self._api_key,
                "api_secret": self._api_secret,
                "to": self._normalize_phone_number(context.destination),
                "from": self._normalize_phone_number(context.source),
                "answer_url": context.metadata.get('answer_url'),
                "answer_method": "POST",
                "event_url": context.metadata.get('event_url'),
                "event_method": "POST",
                "machine_detection": "continue",
                "length_timer": context.metadata.get('max_duration', 300),
                "ringing_timer": context.metadata.get('ring_timeout', 30),
                "custom": call_id  # Store our call ID in Vonage custom field
            }
            
            # Make API request to initiate call
            response = await self._make_request(
                "POST", 
                f"{self._base_url}/call/json", 
                data=call_data
            )
            
            response_data = response.json()
            
            # Check for errors
            if response_data.get('status') != '0':
                error_msg = response_data.get('error_text', 'Unknown error')
                raise Exception(f"Vonage call failed: {error_msg}")
            
            # Store Vonage call UUID temporarily
            vonage_uuid = response_data.get('call-id')
            if vonage_uuid:
                self._temp_vonage_uuid = vonage_uuid
            
            # Create initial event
            initial_event = self._create_telephony_event(
                "call_initiated",
                call_id,
                {
                    "vonage_uuid": vonage_uuid,
                    "status": "initiated",
                    "to": context.destination,
                    "from": context.source
                }
            )
            
            # Cache the event
            self._event_cache[call_id] = [initial_event]
            
            return call_id
            
        except Exception as e:
            self.logger.error(f"Vonage call initiation failed: {e}")
            raise
    
    async def _store_provider_data(self, call_id: str) -> None:
        """
        Store Vonage-specific data after call registration
        
        Args:
            call_id: Unique call identifier
        """
        if hasattr(self, '_temp_vonage_uuid') and self._temp_vonage_uuid:
            self._active_calls[call_id]['vonage_uuid'] = self._temp_vonage_uuid
            delattr(self, '_temp_vonage_uuid')
    
    async def _hangup_impl(self, call_id: str) -> bool:
        """
        Vonage-specific call termination implementation
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            bool: True if call was successfully ended
        """
        try:
            call_info = self._active_calls.get(call_id, {})
            vonage_uuid = call_info.get('vonage_uuid')
            
            if not vonage_uuid:
                self.logger.warning(f"No Vonage UUID found for {call_id}")
                return True  # Consider it successful if we don't have a Vonage UUID
            
            # Prepare hangup request
            hangup_data = {
                "api_key": self._api_key,
                "api_secret": self._api_secret,
                "uuid": vonage_uuid
            }
            
            # Make API request to end call
            await self._make_request(
                "PUT",
                f"{self._base_url}/call/{vonage_uuid}/hangup",
                data=hangup_data
            )
            
            # Create hangup event
            hangup_event = self._create_telephony_event(
                "call_ended",
                call_id,
                {
                    "vonage_uuid": vonage_uuid,
                    "reason": "user_requested"
                }
            )
            
            # Add to event cache
            if call_id in self._event_cache:
                self._event_cache[call_id].append(hangup_event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Vonage call termination failed for {call_id}: {e}")
            return False
    
    async def _get_events_impl(self, call_id: str) -> List[TelephonyEvent]:
        """
        Vonage-specific event retrieval implementation
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            List[TelephonyEvent]: List of telephony events
        """
        try:
            call_info = self._active_calls.get(call_id, {})
            vonage_uuid = call_info.get('vonage_uuid')
            
            if not vonage_uuid:
                return []
            
            # Get call details from Vonage
            params = {
                "api_key": self._api_key,
                "api_secret": self._api_secret
            }
            response = await self._make_request(
                "GET",
                f"{self._base_url}/call/{vonage_uuid}",
                params=params
            )
            
            call_data = response.json()
            
            # Convert Vonage events to standardized events
            events = []
            
            # Add call status event
            status_event = self._create_telephony_event(
                "call_status_update",
                call_id,
                {
                    "vonage_uuid": vonage_uuid,
                    "status": call_data.get('status'),
                    "duration": call_data.get('duration'),
                    "rate": call_data.get('rate'),
                    "network": call_data.get('network')
                }
            )
            events.append(status_event)
            
            # Add recording events if available
            recordings = call_data.get('recordings', [])
            for recording in recordings:
                recording_event = self._create_telephony_event(
                    "call_recording",
                    call_id,
                    {
                        "vonage_uuid": vonage_uuid,
                        "recording_url": recording.get('url'),
                        "recording_id": recording.get('id'),
                        "start_time": recording.get('start_time'),
                        "end_time": recording.get('end_time')
                    }
                )
                events.append(recording_event)
            
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to get Vonage events for call {call_id}: {e}")
            return []
    
    async def _get_costs_impl(self, call_id: str) -> Dict[str, float]:
        """
        Vonage-specific cost calculation implementation
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            Dict[str, float]: Cost breakdown by component
        """
        try:
            call_info = self._active_calls.get(call_id, {})
            vonage_uuid = call_info.get('vonage_uuid')
            
            if not vonage_uuid:
                return {}
            
            # Get call details from Vonage
            params = {
                "api_key": self._api_key,
                "api_secret": self._api_secret
            }
            response = await self._make_request(
                "GET",
                f"{self._base_url}/call/{vonage_uuid}",
                params=params
            )
            
            call_data = response.json()
            
            # Calculate costs based on Vonage pricing
            duration_minutes = call_data.get('duration', 0) / 60.0
            rate_per_minute = call_data.get('rate', 0.01)  # Default rate
            
            return {
                "voice_minutes": duration_minutes,
                "voice_cost": duration_minutes * rate_per_minute,
                "connection_fee": 0.005,  # Fixed connection fee
                "total": (duration_minutes * rate_per_minute) + 0.005
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get Vonage costs for call {call_id}: {e}")
            return {}
    
    async def _get_cost_per_minute(self) -> Optional[float]:
        """Get cost per minute for Vonage"""
        # Vonage typically charges around $0.01 per minute for voice calls
        return 0.01
    
    async def _get_supported_regions(self) -> List[str]:
        """Get list of supported geographic regions for Vonage"""
        return [
            "US", "CA", "GB", "AU", "DE", "FR", "IT", "ES", "NL", "BE",
            "SE", "NO", "DK", "FI", "CH", "AT", "IE", "NZ", "JP", "KR",
            "BR", "MX", "AR", "CL", "CO", "PE", "VE", "IN", "SG", "MY"
        ]
    
    async def _get_supported_features(self) -> List[str]:
        """Get list of supported features for Vonage"""
        return [
            "voice_calls",
            "sms",
            "call_recording",
            "text_to_speech",
            "speech_to_text",
            "number_insight",
            "verify",
            "conversations",
            "messages",
            "webhooks"
        ]
    
    async def get_call_status(self, call_id: str) -> Optional[str]:
        """
        Get current call status from Vonage
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            Optional[str]: Call status
        """
        try:
            call_info = self._active_calls.get(call_id, {})
            vonage_uuid = call_info.get('vonage_uuid')
            
            if not vonage_uuid:
                return None
            
            params = {
                "api_key": self._api_key,
                "api_secret": self._api_secret
            }
            response = await self._make_request(
                "GET",
                f"{self._base_url}/call/{vonage_uuid}",
                params=params
            )
            
            call_data = response.json()
            return call_data.get('status')
            
        except Exception as e:
            self.logger.error(f"Failed to get call status for {call_id}: {e}")
            return None
