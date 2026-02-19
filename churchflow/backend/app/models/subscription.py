"""
Subscription model for ChurchFlow SaaS billing.

This module defines the subscription data model for managing
church organization subscriptions with Stripe.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class SubscriptionPlan(str, Enum):
    """
    Subscription plan tiers.

    - FREE: Up to 100 members, basic features
    - STANDARD: Up to 500 members, includes giving & volunteers
    - PREMIUM: Unlimited members, all features + AI analytics
    """
    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"


class SubscriptionStatus(str, Enum):
    """
    Subscription status from Stripe.

    States align with Stripe subscription statuses.
    """
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"


class Subscription(BaseModel):
    """
    Subscription model for church organizations.

    Attributes:
        organization_id: Church organization ID
        stripe_customer_id: Stripe customer ID
        stripe_subscription_id: Stripe subscription ID (None for free plan)
        plan: Current subscription plan
        status: Subscription status
        current_period_start: Current billing period start
        current_period_end: Current billing period end
        cancel_at_period_end: Whether subscription cancels at period end
        trial_end: Trial period end date (if applicable)
        created_at: Subscription creation timestamp
        updated_at: Last update timestamp
    """
    organization_id: str = Field(..., description="Organization/church ID")
    stripe_customer_id: Optional[str] = Field(None, description="Stripe customer ID")
    stripe_subscription_id: Optional[str] = Field(None, description="Stripe subscription ID")
    plan: SubscriptionPlan = Field(default=SubscriptionPlan.FREE, description="Subscription plan")
    status: SubscriptionStatus = Field(default=SubscriptionStatus.ACTIVE, description="Subscription status")
    current_period_start: Optional[datetime] = Field(None, description="Billing period start")
    current_period_end: Optional[datetime] = Field(None, description="Billing period end")
    cancel_at_period_end: bool = Field(default=False, description="Cancel at period end flag")
    trial_end: Optional[datetime] = Field(None, description="Trial end date")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "organization_id": "org_123",
                "stripe_customer_id": "cus_ABC123",
                "stripe_subscription_id": "sub_XYZ789",
                "plan": "standard",
                "status": "active",
                "current_period_start": "2025-01-01T00:00:00",
                "current_period_end": "2025-02-01T00:00:00",
                "cancel_at_period_end": False,
                "trial_end": None
            }
        }


class SubscriptionCreate(BaseModel):
    """
    Schema for creating a new subscription.

    Attributes:
        organization_id: Organization ID
        plan: Subscription plan to create
        payment_method_id: Stripe payment method ID (required for paid plans)
    """
    organization_id: str
    plan: SubscriptionPlan
    payment_method_id: Optional[str] = Field(None, description="Stripe payment method ID")


class SubscriptionUpdate(BaseModel):
    """
    Schema for updating subscription (upgrade/downgrade).

    Attributes:
        plan: New subscription plan
    """
    plan: SubscriptionPlan


class SubscriptionResponse(BaseModel):
    """
    Response schema for subscription data.

    Includes subscription details plus plan limits.
    """
    organization_id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    trial_end: Optional[datetime]
    member_limit: int
    sms_credits_monthly: int
    features: dict


# Plan limits and features
PLAN_LIMITS = {
    SubscriptionPlan.FREE: {
        "member_limit": 100,
        "sms_credits_monthly": 100,
        "features": {
            "events": True,
            "check_in": True,
            "basic_sms": True,
            "visitor_tracking": True,
            "giving": False,
            "volunteers": False,
            "ai_analytics": False,
            "priority_support": False,
            "custom_branding": False,
        }
    },
    SubscriptionPlan.STANDARD: {
        "member_limit": 500,
        "sms_credits_monthly": 500,
        "features": {
            "events": True,
            "check_in": True,
            "basic_sms": True,
            "visitor_tracking": True,
            "giving": True,
            "volunteers": True,
            "ai_analytics": False,
            "priority_support": False,
            "custom_branding": True,
        }
    },
    SubscriptionPlan.PREMIUM: {
        "member_limit": -1,  # Unlimited
        "sms_credits_monthly": 2000,
        "features": {
            "events": True,
            "check_in": True,
            "basic_sms": True,
            "visitor_tracking": True,
            "giving": True,
            "volunteers": True,
            "ai_analytics": True,
            "priority_support": True,
            "custom_branding": True,
        }
    }
}

# Stripe price IDs (to be set up in Stripe dashboard)
STRIPE_PRICE_IDS = {
    SubscriptionPlan.STANDARD: "price_standard_monthly",  # $49/month
    SubscriptionPlan.PREMIUM: "price_premium_monthly",    # $99/month
}


class PaymentMethod(BaseModel):
    """
    Payment method details (Stripe).

    Attributes:
        id: Stripe payment method ID
        type: Payment method type (card, etc.)
        card_brand: Card brand (visa, mastercard, etc.)
        card_last4: Last 4 digits of card
        card_exp_month: Card expiration month
        card_exp_year: Card expiration year
    """
    id: str
    type: str
    card_brand: Optional[str] = None
    card_last4: Optional[str] = None
    card_exp_month: Optional[int] = None
    card_exp_year: Optional[int] = None
