"""
Event Models

This module contains additional event-related data models.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class EventFilter(BaseModel):
    """Event filtering criteria"""
    event_types: List[str] = Field(default_factory=list, description="Event types to include")
    sources: List[str] = Field(default_factory=list, description="Event sources to include")
    tenant_ids: List[str] = Field(default_factory=list, description="Tenant IDs to include")
    user_ids: List[str] = Field(default_factory=list, description="User IDs to include")
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    priority_min: Optional[int] = Field(None, description="Minimum priority")
    priority_max: Optional[int] = Field(None, description="Maximum priority")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")
    data_filters: Dict[str, Any] = Field(default_factory=dict, description="Data field filters")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EventSubscription(BaseModel):
    """Event subscription information"""
    subscription_id: str = Field(..., description="Subscription identifier")
    subscriber_id: str = Field(..., description="Subscriber identifier")
    event_types: List[str] = Field(default_factory=list, description="Subscribed event types")
    filters: EventFilter = Field(default_factory=EventFilter, description="Subscription filters")
    callback_url: Optional[str] = Field(None, description="Webhook callback URL")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Subscription creation time")
    is_active: bool = Field(True, description="Whether subscription is active")
    last_event_received: Optional[datetime] = Field(None, description="Last event received time")
    total_events_received: int = Field(0, description="Total events received")
    error_count: int = Field(0, description="Number of delivery errors")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EventMetrics(BaseModel):
    """Event system metrics"""
    total_events_published: int = Field(0, description="Total events published")
    total_events_processed: int = Field(0, description="Total events processed")
    active_subscriptions: int = Field(0, description="Active subscriptions")
    events_per_second: float = Field(0.0, description="Events per second")
    average_processing_time_ms: float = Field(0.0, description="Average processing time in milliseconds")
    error_rate: float = Field(0.0, description="Error rate percentage")
    queue_size: int = Field(0, description="Current queue size")
    backlog_size: int = Field(0, description="Current backlog size")
    last_processed_event: Optional[datetime] = Field(None, description="Last processed event time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EventDelivery(BaseModel):
    """Event delivery information"""
    delivery_id: str = Field(..., description="Delivery identifier")
    event_id: str = Field(..., description="Event identifier")
    subscription_id: str = Field(..., description="Subscription identifier")
    status: str = Field(..., description="Delivery status: pending, delivered, failed, retrying")
    attempts: int = Field(0, description="Number of delivery attempts")
    max_attempts: int = Field(3, description="Maximum delivery attempts")
    next_retry: Optional[datetime] = Field(None, description="Next retry time")
    delivered_at: Optional[datetime] = Field(None, description="Delivery time")
    error_message: Optional[str] = Field(None, description="Error message")
    response_code: Optional[int] = Field(None, description="HTTP response code")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EventSchema(BaseModel):
    """Event schema definition"""
    event_type: str = Field(..., description="Event type")
    version: str = Field(..., description="Schema version")
    description: str = Field(..., description="Event description")
    required_fields: List[str] = Field(default_factory=list, description="Required fields")
    optional_fields: List[str] = Field(default_factory=list, description="Optional fields")
    data_schema: Dict[str, Any] = Field(default_factory=dict, description="Data schema definition")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Example events")
    deprecated: bool = Field(False, description="Whether event type is deprecated")
    replacement_event_type: Optional[str] = Field(None, description="Replacement event type")


class EventAudit(BaseModel):
    """Event audit trail"""
    audit_id: str = Field(..., description="Audit identifier")
    event_id: str = Field(..., description="Event identifier")
    action: str = Field(..., description="Audit action")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Audit timestamp")
    user_id: Optional[str] = Field(None, description="User who performed action")
    details: Dict[str, Any] = Field(default_factory=dict, description="Audit details")
    ip_address: Optional[str] = Field(None, description="IP address")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
