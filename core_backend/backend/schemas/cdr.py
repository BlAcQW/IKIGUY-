"""
CDR (Call Detail Record) Schemas

Pydantic models for CDR statistics API responses.
These provide type safety, validation, and automatic OpenAPI documentation.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class CallDirection(str, Enum):
    """Call direction enumeration."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CallDisposition(str, Enum):
    """Call disposition/status enumeration."""
    ANSWERED = "ANSWERED"
    NO_ANSWER = "NO ANSWER"
    BUSY = "BUSY"
    FAILED = "FAILED"
    CONGESTION = "CONGESTION"


class CallSummary(BaseModel):
    """Summary statistics for calls."""
    total_calls: int = Field(default=0, ge=0, description="Total number of calls")
    total_minutes: float = Field(default=0, ge=0, description="Total call duration in minutes")
    total_cost: float = Field(default=0, ge=0, description="Total cost in GHC")

    class Config:
        json_schema_extra = {
            "example": {
                "total_calls": 150,
                "total_minutes": 245.5,
                "total_cost": 36.83
            }
        }


class CallBreakdown(BaseModel):
    """Breakdown of calls by phone number."""
    number: str = Field(..., description="Phone number")
    direction: CallDirection = Field(..., description="Call direction (inbound/outbound)")
    call_count: int = Field(default=0, ge=0, description="Number of calls")
    total_minutes: float = Field(default=0, ge=0, description="Total duration in minutes")
    total_cost: float = Field(default=0, ge=0, description="Total cost in GHC")
    last_call: Optional[datetime] = Field(default=None, description="Timestamp of last call")

    class Config:
        json_schema_extra = {
            "example": {
                "number": "+233241234567",
                "direction": "outbound",
                "call_count": 5,
                "total_minutes": 12.5,
                "total_cost": 1.88,
                "last_call": "2025-11-28T15:30:00"
            }
        }


class DailyUsage(BaseModel):
    """Daily call usage statistics."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    call_count: int = Field(default=0, ge=0, description="Number of calls")
    total_minutes: float = Field(default=0, ge=0, description="Total duration in minutes")
    total_cost: float = Field(default=0, ge=0, description="Total cost in GHC")

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-11-28",
                "call_count": 10,
                "total_minutes": 25.5,
                "total_cost": 3.83
            }
        }


class RecentCall(BaseModel):
    """Individual call record."""
    call_id: str = Field(..., description="Unique call identifier")
    source: str = Field(..., description="Caller phone number")
    destination: str = Field(..., description="Called phone number")
    direction: CallDirection = Field(..., description="Call direction relative to the phone")
    duration_seconds: int = Field(default=0, ge=0, description="Call duration in seconds")
    disposition: str = Field(..., description="Call status/disposition")
    cost: float = Field(default=0, ge=0, description="Call cost in GHC")
    timestamp: datetime = Field(..., description="Call start timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "call_id": "1732807823.123",
                "source": "+233241234567",
                "destination": "+233308047916",
                "direction": "inbound",
                "duration_seconds": 120,
                "disposition": "ANSWERED",
                "cost": 0.30,
                "timestamp": "2025-11-28T15:30:23"
            }
        }


class CDRStatsResponse(BaseModel):
    """
    Complete CDR statistics response for a phone number.

    Contains summary statistics, breakdowns by caller/called numbers,
    daily usage trends, and recent call history.
    """
    success: bool = Field(default=True, description="Request success status")
    phone_number: str = Field(..., description="Phone number for these stats")
    phone_id: str = Field(..., description="Internal phone ID")
    period_days: int = Field(..., ge=1, le=365, description="Number of days included in stats")

    # Statistics
    summary: CallSummary = Field(..., description="Overall call statistics")
    outbound_calls: List[CallBreakdown] = Field(
        default_factory=list,
        description="Breakdown of outbound calls by destination"
    )
    inbound_calls: List[CallBreakdown] = Field(
        default_factory=list,
        description="Breakdown of inbound calls by source"
    )
    daily_usage: List[DailyUsage] = Field(
        default_factory=list,
        description="Daily usage breakdown"
    )
    recent_calls: List[RecentCall] = Field(
        default_factory=list,
        description="Recent call records"
    )

    # Pagination info for recent_calls
    recent_calls_total: int = Field(default=0, ge=0, description="Total number of calls in period")
    recent_calls_page: int = Field(default=1, ge=1, description="Current page number")
    recent_calls_per_page: int = Field(default=20, ge=1, le=100, description="Calls per page")

    # Account info
    credit_balance: float = Field(default=0, ge=0, description="Current credit balance in GHC")
    remaining_minutes: float = Field(default=0, ge=0, description="Estimated remaining minutes")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "phone_number": "+233308047916",
                "phone_id": "vapi_123456",
                "period_days": 30,
                "summary": {
                    "total_calls": 150,
                    "total_minutes": 245.5,
                    "total_cost": 36.83
                },
                "outbound_calls": [],
                "inbound_calls": [],
                "daily_usage": [],
                "recent_calls": [],
                "recent_calls_total": 150,
                "recent_calls_page": 1,
                "recent_calls_per_page": 20,
                "credit_balance": 100.0,
                "remaining_minutes": 666.67
            }
        }


class CDRStatsRequest(BaseModel):
    """Request parameters for CDR stats (used for validation)."""
    days: int = Field(default=30, ge=1, le=365, description="Number of days to include")
    page: int = Field(default=1, ge=1, description="Page number for recent calls")
    per_page: int = Field(default=20, ge=1, le=100, description="Results per page")
    include_unanswered: bool = Field(
        default=False,
        description="Include unanswered calls in statistics"
    )


class AllPhonesStatsResponse(BaseModel):
    """CDR statistics for all managed phone numbers."""
    success: bool = Field(default=True)
    period_days: int = Field(..., ge=1, le=365)
    total_phones: int = Field(default=0, ge=0)
    aggregate_summary: CallSummary = Field(..., description="Combined stats for all phones")
    phones: List[CDRStatsResponse] = Field(default_factory=list)
