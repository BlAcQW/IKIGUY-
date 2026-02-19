"""
Telephony Interfaces

This module defines the core telephony interfaces used across all components.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class TelephonyEventType(Enum):
    """Telephony event types"""
    CALL_STARTED = "call_started"
    CALL_ENDED = "call_ended"
    CALL_ANSWERED = "call_answered"
    CALL_RINGING = "call_ringing"
    DTMF_RECEIVED = "dtmf_received"
    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    CONFERENCE_JOINED = "conference_joined"
    CONFERENCE_LEFT = "conference_left"
    CALL_TRANSFERRED = "call_transferred"
    ERROR_OCCURRED = "error_occurred"
    SPEECH_DETECTED = "speech_detected"
    SPEECH_ENDED = "speech_ended"
    TRANSCRIPTION = "transcription"
    UNKNOWN_EVENT = "unknown_event"


class TelephonyEvent(BaseModel):
    """Standard telephony event structure"""
    event_type: TelephonyEventType = Field(..., description="Type of telephony event")
    call_id: str = Field(..., description="Unique call identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    provider: str = Field(..., description="Telephony provider name")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TelephonyPort(ABC):
    """Abstract interface for telephony operations"""
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def hangup(self, call_id: str) -> bool:
        """
        End a call
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            bool: True if call was successfully ended
        """
        pass
    
    @abstractmethod
    async def get_events(self, call_id: str) -> List[TelephonyEvent]:
        """
        Get events for a call
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            List[TelephonyEvent]: List of telephony events
        """
        pass
    
    @abstractmethod
    async def get_costs(self, call_id: str) -> Dict[str, float]:
        """
        Get cost breakdown for a call
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            Dict[str, float]: Cost breakdown by component
        """
        pass


class ProviderManager:
    """Provider management and switching logic"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers: Dict[str, TelephonyPort] = {}
        self.health_status: Dict[str, bool] = {}
    
    async def get_best_provider(self, context: Dict[str, Any]) -> TelephonyPort:
        """
        Select best provider based on rules and context
        
        Args:
            context: Call context including destination, cost preferences, etc.
            
        Returns:
            TelephonyPort: Best available provider
        """
        # Implementation will be added based on provider selection logic
        pass
    
    async def switch_provider(self, call_id: str, new_provider: str) -> bool:
        """
        Switch provider for active call
        
        Args:
            call_id: Unique call identifier
            new_provider: Name of new provider to switch to
            
        Returns:
            bool: True if provider switch was successful
        """
        # Implementation will be added based on provider switching logic
        pass
    
    async def get_provider_health(self, provider_id: str) -> Dict[str, Any]:
        """
        Get provider health status
        
        Args:
            provider_id: Provider identifier
            
        Returns:
            Dict[str, Any]: Provider health information
        """
        # Implementation will be added based on health monitoring logic
        pass
    
    async def register_provider(self, name: str, provider: TelephonyPort) -> None:
        """
        Register a telephony provider
        
        Args:
            name: Provider name
            provider: TelephonyPort implementation
        """
        self.providers[name] = provider
        self.health_status[name] = True
    
    async def unregister_provider(self, name: str) -> None:
        """
        Unregister a telephony provider
        
        Args:
            name: Provider name
        """
        if name in self.providers:
            del self.providers[name]
        if name in self.health_status:
            del self.health_status[name]
