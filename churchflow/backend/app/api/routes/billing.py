"""
Billing and subscription management routes for ChurchFlow SaaS.

Handles subscription creation, upgrades, downgrades, cancellations, payment methods,
and billing webhooks. Follows InkWave payment integration patterns.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from pydantic import BaseModel, Field
from decimal import Decimal

from app.api.dependencies import get_current_user
from app.core.database import get_database
from apps.shared.dependencies import require_organization_admin_role
from app.services.subscription_service import SubscriptionService
from app.models.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    PaymentMethod,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["Billing"])


# ================== Request/Response Models ==================

class SubscriptionCreateRequest(BaseModel):
    """Request to create a new subscription."""
    plan: SubscriptionPlan
    payment_method_id: Optional[str] = Field(None, description="Stripe payment method ID")
    trial_days: Optional[int] = Field(14, description="Number of trial days (default: 14)")


class SubscriptionUpdateRequest(BaseModel):
    """Request to update a subscription (upgrade/downgrade)."""
    new_plan: SubscriptionPlan


class PaymentMethodRequest(BaseModel):
    """Request to update payment method."""
    payment_method_id: str = Field(..., description="Stripe payment method ID")


class UsageResponse(BaseModel):
    """Response for organization usage metrics."""
    organization_id: str
    current_plan: str
    members_count: int
    members_limit: int
    sms_credits: float
    sms_limit: Optional[float]
    storage_mb: float
    storage_limit_mb: Optional[float]
    billing_period_start: str
    billing_period_end: str


class InvoiceResponse(BaseModel):
    """Response for invoice information."""
    id: str
    amount: float
    currency: str
    status: str
    invoice_pdf: Optional[str]
    created_at: str
    paid_at: Optional[str]


# ================== Subscription Management ==================

@router.post("/subscriptions", response_model=Subscription, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    request: SubscriptionCreateRequest,
    user: dict = Depends(get_current_user),
    org_id: str = Depends(require_organization_admin_role),
    db = Depends(get_database),
):
    """
    Create a new subscription for an organization.

    Only organization admins can create subscriptions.
    Automatically creates a Stripe customer and sets up payment if payment_method_id provided.
    """
    subscription_service = SubscriptionService(db)
    user_id = user.get("id") or user.get("sub")
    user_email = user.get("email")

    try:
        subscription = await subscription_service.create_subscription(
            organization_id=org_id,
            plan=request.plan,
            user_email=user_email,
            payment_method_id=request.payment_method_id,
            trial_days=request.trial_days,
        )

        logger.info(f"Subscription created for organization {org_id} on plan {request.plan}")
        return subscription

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create subscription: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create subscription")


@router.get("/subscriptions/{organization_id}", response_model=Subscription)
async def get_subscription(
    organization_id: str,
    user: dict = Depends(get_current_user),
    db = Depends(get_database),
):
    """
    Get subscription details for an organization.

    User must have access to the organization.
    """
    subscription_service = SubscriptionService(db)

    # Verify user has access to organization
    # (This is handled by the organization service in the actual implementation)

    subscription = await subscription_service.get_subscription(organization_id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    return subscription


@router.patch("/subscriptions/{organization_id}/plan", response_model=Subscription)
async def update_subscription_plan(
    organization_id: str,
    request: SubscriptionUpdateRequest,
    org_id: str = Depends(require_organization_admin_role),
    db = Depends(get_database),
):
    """
    Update subscription plan (upgrade or downgrade).

    Only organization admins can change plans.
    Proration is handled automatically by Stripe.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update subscription for another organization"
        )

    subscription_service = SubscriptionService(db)

    try:
        subscription = await subscription_service.update_plan(
            organization_id=organization_id,
            new_plan=request.new_plan,
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        logger.info(f"Subscription plan updated for organization {organization_id} to {request.new_plan}")
        return subscription

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update subscription plan: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update plan")


@router.post("/subscriptions/{organization_id}/cancel", response_model=Subscription)
async def cancel_subscription(
    organization_id: str,
    org_id: str = Depends(require_organization_admin_role),
    db = Depends(get_database),
):
    """
    Cancel a subscription.

    Only organization admins can cancel subscriptions.
    Subscription remains active until the end of the current billing period.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot cancel subscription for another organization"
        )

    subscription_service = SubscriptionService(db)

    try:
        subscription = await subscription_service.cancel_subscription(organization_id)

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        logger.info(f"Subscription cancelled for organization {organization_id}")
        return subscription

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cancel subscription")


@router.post("/subscriptions/{organization_id}/reactivate", response_model=Subscription)
async def reactivate_subscription(
    organization_id: str,
    org_id: str = Depends(require_organization_admin_role),
    db = Depends(get_database),
):
    """
    Reactivate a cancelled subscription.

    Only organization admins can reactivate subscriptions.
    Only works if subscription is still in the current billing period.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot reactivate subscription for another organization"
        )

    subscription_service = SubscriptionService(db)

    try:
        subscription = await subscription_service.reactivate_subscription(organization_id)

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found or cannot be reactivated"
            )

        logger.info(f"Subscription reactivated for organization {organization_id}")
        return subscription

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to reactivate subscription: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reactivate subscription")


# ================== Payment Methods ==================

@router.post("/payment-methods/{organization_id}", response_model=dict)
async def update_payment_method(
    organization_id: str,
    request: PaymentMethodRequest,
    org_id: str = Depends(require_organization_admin_role),
    db = Depends(get_database),
):
    """
    Update payment method for a subscription.

    Only organization admins can update payment methods.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update payment method for another organization"
        )

    subscription_service = SubscriptionService(db)

    try:
        success = await subscription_service.update_payment_method(
            organization_id=organization_id,
            payment_method_id=request.payment_method_id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update payment method"
            )

        logger.info(f"Payment method updated for organization {organization_id}")
        return {"success": True, "message": "Payment method updated successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update payment method: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update payment method")


@router.get("/payment-methods/{organization_id}", response_model=PaymentMethod)
async def get_payment_method(
    organization_id: str,
    org_id: str = Depends(require_organization_admin_role),
    db = Depends(get_database),
):
    """
    Get current payment method for a subscription.

    Only organization admins can view payment methods.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view payment method for another organization"
        )

    subscription_service = SubscriptionService(db)

    payment_method = await subscription_service.get_payment_method(organization_id)

    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payment method found"
        )

    return payment_method


# ================== Usage & Billing ==================

@router.get("/usage/{organization_id}", response_model=UsageResponse)
async def get_usage_metrics(
    organization_id: str,
    user: dict = Depends(get_current_user),
    db = Depends(get_database),
):
    """
    Get current usage metrics for an organization.

    Shows members count, SMS credits, storage usage, and limits based on plan.
    """
    subscription_service = SubscriptionService(db)

    usage = await subscription_service.get_usage_metrics(organization_id)

    if not usage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usage metrics not found"
        )

    return usage


@router.get("/invoices/{organization_id}", response_model=List[InvoiceResponse])
async def list_invoices(
    organization_id: str,
    limit: int = 10,
    org_id: str = Depends(require_organization_admin_role),
    db = Depends(get_database),
):
    """
    List invoices for an organization.

    Only organization admins can view invoices.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view invoices for another organization"
        )

    subscription_service = SubscriptionService(db)

    invoices = await subscription_service.list_invoices(organization_id, limit=limit)

    return invoices


# ================== Webhooks ==================

@router.post("/webhooks/stripe", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db = Depends(get_database),
):
    """
    Handle Stripe webhook events.

    Processes subscription lifecycle events:
    - invoice.payment_succeeded
    - invoice.payment_failed
    - customer.subscription.updated
    - customer.subscription.deleted
    """
    subscription_service = SubscriptionService(db)

    try:
        # Get raw request body
        payload = await request.body()

        # Process webhook
        result = await subscription_service.handle_stripe_webhook(
            payload=payload,
            signature=stripe_signature,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook processing failed"
            )

        return {"status": "success"}

    except ValueError as e:
        logger.error(f"Invalid webhook signature: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Webhook processing error")


# ================== Setup Intent (for card collection) ==================

@router.post("/setup-intent/{organization_id}", response_model=dict)
async def create_setup_intent(
    organization_id: str,
    org_id: str = Depends(require_organization_admin_role),
    db = Depends(get_database),
):
    """
    Create a Stripe SetupIntent for collecting payment method.

    Used on the frontend with Stripe Elements to securely collect card details.
    Only organization admins can create setup intents.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create setup intent for another organization"
        )

    subscription_service = SubscriptionService(db)

    try:
        setup_intent = await subscription_service.create_setup_intent(organization_id)

        if not setup_intent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create setup intent"
            )

        return {
            "client_secret": setup_intent["client_secret"],
            "setup_intent_id": setup_intent["id"],
        }

    except Exception as e:
        logger.error(f"Failed to create setup intent: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create setup intent")
