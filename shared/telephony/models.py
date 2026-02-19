"""
Telephony Models

This module contains additional telephony-related data models.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from .interfaces import TelephonyEvent


class CallContext(BaseModel):
    """Context information for a call"""
    destination: str = Field(..., description="Destination phone number")
    source: str = Field(..., description="Source phone number or DID")
    tenant_id: str = Field(..., description="Tenant identifier")
    language: Optional[str] = Field(None, description="Language code for speech processing")
    campaign_id: Optional[str] = Field(None, description="Campaign identifier")
    cost_preference: str = Field("balanced", description="Cost preference: low, balanced, high")
    quality_preference: str = Field("balanced", description="Quality preference: low, balanced, high")
    geographic_region: Optional[str] = Field(None, description="Geographic region for routing")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context data")
    custom_data: Dict[str, Any] = Field(default_factory=dict, description="Custom data for provider-specific settings")


class ProviderHealth(BaseModel):
    """Provider health status information"""
    provider_id: str = Field(..., description="Provider identifier")
    is_healthy: bool = Field(..., description="Whether provider is healthy")
    last_check: datetime = Field(default_factory=datetime.utcnow, description="Last health check time")
    response_time_ms: Optional[float] = Field(None, description="Average response time in milliseconds")
    error_rate: Optional[float] = Field(None, description="Error rate percentage")
    available_capacity: Optional[int] = Field(None, description="Available call capacity")
    cost_per_minute: Optional[float] = Field(None, description="Cost per minute in USD")
    supported_regions: List[str] = Field(default_factory=list, description="Supported geographic regions")
    features: List[str] = Field(default_factory=list, description="Supported features")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProviderSettings(BaseModel):
    """Provider configuration settings"""
    provider_id: str = Field(..., description="Provider identifier")
    api_key: str = Field(..., description="API key for provider")
    api_secret: Optional[str] = Field(None, description="API secret for provider")
    base_url: str = Field(..., description="Base URL for provider API")
    timeout_seconds: int = Field(30, description="Request timeout in seconds")
    retry_attempts: int = Field(3, description="Number of retry attempts")
    enabled: bool = Field(True, description="Whether provider is enabled")
    priority: int = Field(5, description="Provider priority (1-10, higher is better)")
    cost_multiplier: float = Field(1.0, description="Cost multiplier for this provider")
    max_concurrent_calls: Optional[int] = Field(None, description="Maximum concurrent calls")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for events")
    webhook_secret: Optional[str] = Field(None, description="Webhook secret for verification")
    custom_settings: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific settings")


class CallResult(BaseModel):
    """Result of a call operation"""
    call_id: str = Field(..., description="Unique call identifier")
    success: bool = Field(..., description="Whether call was successful")
    provider: str = Field(..., description="Provider used for the call")
    duration_seconds: Optional[float] = Field(None, description="Call duration in seconds")
    cost_usd: Optional[float] = Field(None, description="Call cost in USD")
    status: str = Field(..., description="Call status")
    error_message: Optional[str] = Field(None, description="Error message if call failed")
    events: List[TelephonyEvent] = Field(default_factory=list, description="Call events")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional call data")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
