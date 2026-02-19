"""
Usage metrics model for tracking organization resource usage.

Tracks member count, SMS credits, storage, and other usage metrics
to enforce subscription plan limits.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UsageMetrics(BaseModel):
    """
    Usage metrics for an organization.

    Tracks current usage against subscription limits.

    Attributes:
        organization_id: Organization ID
        member_count: Current active member count
        sms_credits_used: SMS credits used this billing period
        sms_credits_remaining: SMS credits remaining
        storage_used_mb: Storage used in megabytes
        events_count: Number of events this billing period
        check_ins_count: Number of check-ins this billing period
        period_start: Current billing period start
        period_end: Current billing period end
        last_calculated: Last time metrics were calculated
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    organization_id: str = Field(..., description="Organization ID")
    member_count: int = Field(default=0, description="Active member count")
    sms_credits_used: int = Field(default=0, description="SMS credits used")
    sms_credits_remaining: int = Field(default=100, description="SMS credits remaining")
    storage_used_mb: float = Field(default=0.0, description="Storage used (MB)")
    events_count: int = Field(default=0, description="Events created this period")
    check_ins_count: int = Field(default=0, description="Check-ins this period")
    period_start: datetime = Field(default_factory=datetime.utcnow, description="Period start")
    period_end: datetime = Field(default_factory=datetime.utcnow, description="Period end")
    last_calculated: datetime = Field(default_factory=datetime.utcnow, description="Last calculation time")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "organization_id": "org_123",
                "member_count": 45,
                "sms_credits_used": 32,
                "sms_credits_remaining": 68,
                "storage_used_mb": 125.5,
                "events_count": 3,
                "check_ins_count": 150,
                "period_start": "2025-01-01T00:00:00",
                "period_end": "2025-02-01T00:00:00"
            }
        }


class UsageMetricsResponse(BaseModel):
    """
    Response schema for usage metrics.

    Includes usage data plus limits from subscription plan.
    """
    organization_id: str
    member_count: int
    member_limit: int
    member_limit_reached: bool
    sms_credits_used: int
    sms_credits_remaining: int
    sms_credits_limit: int
    storage_used_mb: float
    events_count: int
    check_ins_count: int
    period_start: datetime
    period_end: datetime
    last_calculated: datetime


class BillingEvent(BaseModel):
    """
    Billing event for audit log.

    Records billing-related events for compliance and debugging.

    Attributes:
        organization_id: Organization ID
        event_type: Type of billing event
        stripe_event_id: Stripe event ID (if from webhook)
        description: Event description
        metadata: Additional event data
        created_at: Event timestamp
    """
    organization_id: str = Field(..., description="Organization ID")
    event_type: str = Field(..., description="Event type (e.g., subscription.created)")
    stripe_event_id: Optional[str] = Field(None, description="Stripe event ID")
    description: str = Field(..., description="Event description")
    metadata: dict = Field(default_factory=dict, description="Additional event data")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "organization_id": "org_123",
                "event_type": "subscription.created",
                "stripe_event_id": "evt_ABC123",
                "description": "Subscription created for Standard plan",
                "metadata": {
                    "plan": "standard",
                    "amount": 49.00
                }
            }
        }
