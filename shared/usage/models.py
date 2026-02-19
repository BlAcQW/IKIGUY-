"""
Usage Models

This module contains additional usage-related data models.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class UsageSummary(BaseModel):
    """Usage summary for a period"""
    tenant_id: str = Field(..., description="Tenant identifier")
    period: str = Field(..., description="Time period")
    start_date: datetime = Field(..., description="Period start date")
    end_date: datetime = Field(..., description="Period end date")
    total_calls: int = Field(0, description="Total number of calls")
    total_duration: float = Field(0.0, description="Total call duration in minutes")
    total_cost: float = Field(0.0, description="Total cost in USD")
    service_breakdown: Dict[str, float] = Field(default_factory=dict, description="Usage by service")
    metric_breakdown: Dict[str, float] = Field(default_factory=dict, description="Usage by metric")
    cost_breakdown: Dict[str, float] = Field(default_factory=dict, description="Cost by service")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CostBreakdown(BaseModel):
    """Cost breakdown for a period"""
    tenant_id: str = Field(..., description="Tenant identifier")
    period: str = Field(..., description="Time period")
    total_cost: float = Field(0.0, description="Total cost in USD")
    telephony_cost: float = Field(0.0, description="Telephony costs")
    ai_cost: float = Field(0.0, description="AI/ML service costs")
    storage_cost: float = Field(0.0, description="Storage costs")
    api_cost: float = Field(0.0, description="API usage costs")
    support_cost: float = Field(0.0, description="Support costs")
    other_costs: float = Field(0.0, description="Other costs")
    provider_breakdown: Dict[str, float] = Field(default_factory=dict, description="Costs by provider")
    feature_breakdown: Dict[str, float] = Field(default_factory=dict, description="Costs by feature")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UsageMetrics(BaseModel):
    """Usage metrics for monitoring"""
    tenant_id: str = Field(..., description="Tenant identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")
    active_calls: int = Field(0, description="Number of active calls")
    concurrent_calls: int = Field(0, description="Maximum concurrent calls")
    call_success_rate: float = Field(0.0, description="Call success rate percentage")
    average_call_duration: float = Field(0.0, description="Average call duration in minutes")
    total_api_requests: int = Field(0, description="Total API requests")
    api_success_rate: float = Field(0.0, description="API success rate percentage")
    storage_used_gb: float = Field(0.0, description="Storage used in GB")
    bandwidth_used_gb: float = Field(0.0, description="Bandwidth used in GB")
    error_count: int = Field(0, description="Number of errors")
    warning_count: int = Field(0, description="Number of warnings")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BillingPeriod(BaseModel):
    """Billing period information"""
    tenant_id: str = Field(..., description="Tenant identifier")
    period_id: str = Field(..., description="Billing period identifier")
    start_date: datetime = Field(..., description="Period start date")
    end_date: datetime = Field(..., description="Period end date")
    status: str = Field("active", description="Billing status: active, closed, paid")
    total_amount: float = Field(0.0, description="Total amount in USD")
    currency: str = Field("USD", description="Billing currency")
    invoice_number: Optional[str] = Field(None, description="Invoice number")
    payment_status: str = Field("pending", description="Payment status: pending, paid, overdue")
    due_date: Optional[datetime] = Field(None, description="Payment due date")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RateLimit(BaseModel):
    """Rate limiting information"""
    tenant_id: str = Field(..., description="Tenant identifier")
    service: str = Field(..., description="Service name")
    limit_type: str = Field(..., description="Limit type: requests_per_minute, calls_per_hour, etc.")
    current_usage: int = Field(0, description="Current usage count")
    limit: int = Field(..., description="Usage limit")
    reset_time: datetime = Field(..., description="When the limit resets")
    exceeded: bool = Field(False, description="Whether limit is exceeded")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
