"""
Call Logs Models

This module provides MongoDB models for VAPI call logs, supporting both
real-time call data and post-call analytics.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4
from pydantic import BaseModel, Field
from enum import Enum


class CallStatus(str, Enum):
    """Call status enumeration."""
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"
    CANCELLED = "cancelled"


class CallDirection(str, Enum):
    """Call direction enumeration."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CallLog(BaseModel):
    """MongoDB model for call logs from vapi_calls collection."""

    # Primary identifiers
    id: str = Field(default_factory=lambda: str(uuid4()), description="MongoDB document ID")
    call_id: str = Field(..., description="Unique VAPI call identifier")

    # Assistant information
    assistant_id: Optional[str] = Field(default=None, description="VAPI assistant ID")
    assistant_name: Optional[str] = Field(default=None, description="Assistant display name")

    # Call details
    status: str = Field(default="initiated", description="Current call status")
    direction: str = Field(default="inbound", description="Call direction")

    # Phone numbers
    from_phone: Optional[str] = Field(default=None, description="Caller phone number")
    to_phone: Optional[str] = Field(default=None, description="Called phone number")

    # Timing information
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Call start timestamp")
    end_time: Optional[datetime] = Field(default=None, description="Call end timestamp")
    duration: Optional[int] = Field(default=None, description="Call duration in seconds")

    # Call content
    transcript: Optional[str] = Field(default=None, description="Full call transcript")
    summary: Optional[str] = Field(default=None, description="AI-generated call summary")

    # Analysis data
    sentiment: Optional[str] = Field(default=None, description="Overall call sentiment (positive, negative, neutral)")
    confidence_score: Optional[float] = Field(default=None, description="Confidence score for the call outcome")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords from the call")

    # Cost tracking
    cost: Optional[float] = Field(default=None, description="Call cost in USD")
    tokens_used: Optional[int] = Field(default=None, description="Total tokens consumed")

    # User context
    customer_id: Optional[str] = Field(default=None, description="Customer identifier")
    customer_phone: Optional[str] = Field(default=None, description="Customer phone number")
    organization_id: Optional[str] = Field(default=None, description="Organization ID")
    user_id: Optional[str] = Field(default=None, description="User ID who initiated/owns the call")

    # Campaign/Automation context
    automation_id: Optional[str] = Field(default=None, description="Automation config ID")
    automation_name: Optional[str] = Field(default=None, description="Automation name")
    campaign_id: Optional[str] = Field(default=None, description="Campaign ID")
    phone_id: Optional[str] = Field(default=None, description="VAPI phone number ID")

    # Call end details
    ended_reason: Optional[str] = Field(default=None, description="Why the call ended")
    recording_url: Optional[str] = Field(default=None, description="Call recording URL")

    # Integrations tracking
    integrations_used: List[str] = Field(default_factory=list, description="Tools/integrations used during call")
    tool_call_count: int = Field(default=0, description="Number of tool calls made")

    # VAPI timestamps (raw from API)
    started_at: Optional[str] = Field(default=None, description="VAPI call start timestamp")
    ended_at: Optional[str] = Field(default=None, description="VAPI call end timestamp")

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional call metadata")
    tags: List[str] = Field(default_factory=list, description="Call tags for categorization")
    messages: List[Any] = Field(default_factory=list, description="Call messages array")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Record last update timestamp")

    class Config:
        extra = "allow"  # Allow extra fields from MongoDB


class CallLogCreate(BaseModel):
    """Request model for creating a call log."""

    call_id: str = Field(..., description="Unique VAPI call identifier")
    assistant_id: str = Field(..., description="VAPI assistant ID")
    assistant_name: Optional[str] = Field(default=None, description="Assistant display name")
    status: Optional[CallStatus] = Field(default=CallStatus.INITIATED, description="Call status")
    direction: Optional[CallDirection] = Field(default=CallDirection.INBOUND, description="Call direction")
    from_phone: Optional[str] = Field(default=None, description="Caller phone number")
    to_phone: Optional[str] = Field(default=None, description="Called phone number")
    transcript: Optional[str] = Field(default=None, description="Call transcript")
    summary: Optional[str] = Field(default=None, description="Call summary")
    duration: Optional[int] = Field(default=None, description="Call duration in seconds")
    cost: Optional[float] = Field(default=None, description="Call cost")
    customer_id: Optional[str] = Field(default=None, description="Customer identifier")
    organization_id: Optional[str] = Field(default=None, description="Organization ID")
    user_id: Optional[str] = Field(default=None, description="User ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    tags: Optional[List[str]] = Field(default_factory=list, description="Call tags")


class CallLogUpdate(BaseModel):
    """Request model for updating a call log."""

    status: Optional[CallStatus] = Field(default=None, description="Updated call status")
    end_time: Optional[datetime] = Field(default=None, description="Call end time")
    duration: Optional[int] = Field(default=None, description="Call duration in seconds")
    transcript: Optional[str] = Field(default=None, description="Updated transcript")
    summary: Optional[str] = Field(default=None, description="Updated summary")
    sentiment: Optional[str] = Field(default=None, description="Call sentiment")
    confidence_score: Optional[float] = Field(default=None, description="Confidence score")
    keywords: Optional[List[str]] = Field(default=None, description="Extracted keywords")
    cost: Optional[float] = Field(default=None, description="Updated call cost")
    tokens_used: Optional[int] = Field(default=None, description="Tokens consumed")
    audio_quality: Optional[str] = Field(default=None, description="Audio quality")
    connection_quality: Optional[str] = Field(default=None, description="Connection quality")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Updated metadata")
    tags: Optional[List[str]] = Field(default=None, description="Updated tags")
    synced_to_supabase: Optional[bool] = Field(default=None, description="Supabase sync status")
    supabase_id: Optional[str] = Field(default=None, description="Supabase record ID")
    sync_error: Optional[str] = Field(default=None, description="Sync error message")


class CallLogResponse(BaseModel):
    """Response model for call log operations."""

    success: bool = Field(..., description="Operation success status")
    call_log: Optional[CallLog] = Field(default=None, description="Call log data")
    message: Optional[str] = Field(default=None, description="Response message")
    mongo_id: Optional[str] = Field(default=None, description="MongoDB document ID")
    supabase_id: Optional[str] = Field(default=None, description="Supabase record ID")


class CallLogListResponse(BaseModel):
    """Response model for call log listing."""

    success: bool = Field(..., description="Operation success status")
    call_logs: List[CallLog] = Field(default_factory=list, description="List of call logs")
    total_count: int = Field(default=0, description="Total number of call logs")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=20, description="Page size")
    total_pages: int = Field(default=0, description="Total number of pages")
    message: Optional[str] = Field(default=None, description="Response message")


class CallLogFilter(BaseModel):
    """Filter model for call log queries."""

    # Time range filters
    start_date: Optional[datetime] = Field(default=None, description="Start date filter")
    end_date: Optional[datetime] = Field(default=None, description="End date filter")

    # Status and direction filters
    status: Optional[CallStatus] = Field(default=None, description="Call status filter")
    direction: Optional[CallDirection] = Field(default=None, description="Call direction filter")

    # Assistant and user filters
    assistant_id: Optional[str] = Field(default=None, description="Assistant ID filter")
    automation_id: Optional[str] = Field(default=None, description="Automation ID filter")
    automation_name: Optional[str] = Field(default=None, description="Automation name filter")
    campaign_id: Optional[str] = Field(default=None, description="Campaign ID filter")
    user_id: Optional[str] = Field(default=None, description="User ID filter")
    organization_id: Optional[str] = Field(default=None, description="Organization ID filter")
    customer_id: Optional[str] = Field(default=None, description="Customer ID filter")

    # Phone number filters
    from_phone: Optional[str] = Field(default=None, description="From phone filter")
    to_phone: Optional[str] = Field(default=None, description="To phone filter")

    # Content filters
    keyword: Optional[str] = Field(default=None, description="Keyword search in transcript/summary")
    sentiment: Optional[str] = Field(default=None, description="Sentiment filter")
    tags: Optional[List[str]] = Field(default=None, description="Tag filters")

    # Quality filters
    min_duration: Optional[int] = Field(default=None, description="Minimum duration filter")
    max_duration: Optional[int] = Field(default=None, description="Maximum duration filter")
    min_cost: Optional[float] = Field(default=None, description="Minimum cost filter")
    max_cost: Optional[float] = Field(default=None, description="Maximum cost filter")


class CallAnalytics(BaseModel):
    """Call analytics aggregation model."""

    # Time period
    period_start: datetime = Field(..., description="Analytics period start")
    period_end: datetime = Field(..., description="Analytics period end")

    # Basic metrics
    total_calls: int = Field(default=0, description="Total number of calls")
    completed_calls: int = Field(default=0, description="Number of completed calls")
    failed_calls: int = Field(default=0, description="Number of failed calls")

    # Duration metrics
    total_duration: int = Field(default=0, description="Total call duration in seconds")
    average_duration: float = Field(default=0.0, description="Average call duration")

    # Cost metrics
    total_cost: float = Field(default=0.0, description="Total call costs")
    average_cost: float = Field(default=0.0, description="Average call cost")

    # Quality metrics
    success_rate: float = Field(default=0.0, description="Call success rate percentage")
    average_quality_score: float = Field(default=0.0, description="Average call quality score")

    # Sentiment distribution
    sentiment_distribution: Dict[str, int] = Field(default_factory=dict, description="Sentiment counts")

    # Top assistants
    top_assistants: List[Dict[str, Any]] = Field(default_factory=list, description="Top performing assistants")

    # Hourly distribution
    hourly_distribution: Dict[int, int] = Field(default_factory=dict, description="Calls by hour of day")

    # Daily trends
    daily_trends: List[Dict[str, Any]] = Field(default_factory=list, description="Daily call trends")