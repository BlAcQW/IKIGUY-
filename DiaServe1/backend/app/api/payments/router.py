"""
Payments API Router.

Handles payment processing endpoints for multiple gateways
(Stripe, Flutterwave) and payment methods.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Header
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.auth import get_current_user, get_organization_context
from app.services.payment_service import PaymentService
from app.models.payment import (
    Payment,
    PaymentCreate,
    PaymentIntent,
    PaymentConfirm,
    PaymentRefund,
    PaymentListFilters,
    PaymentListResponse,
    PaymentStats,
    WebhookEvent,
    PaymentGateway,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments")


@router.post("", response_model=Payment, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    organization_id: str = Depends(get_organization_context)
):
    """
    Create a new payment.

    Creates a payment record and prepares it for processing.
    Use `/payments/{payment_id}/intent` to initialize payment with gateway.

    Args:
        payment_data: Payment creation data
        database: Database connection
        current_user: Authenticated user
        organization_id: Organization ID from context

    Returns:
        Created payment record

    Raises:
        HTTPException: If validation fails
    """
    try:
        service = PaymentService(database)
        payment = await service.create_payment(
            organization_id=organization_id,
            payment_data=payment_data,
            user_id=current_user["id"]
        )
        return payment

    except ValueError as e:
        logger.error(f"Payment creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment"
        )


@router.post("/{payment_id}/intent", response_model=PaymentIntent)
async def create_payment_intent(
    payment_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    organization_id: str = Depends(get_organization_context)
):
    """
    Create payment intent for client-side payment initialization.

    Initializes payment with the gateway (Stripe PaymentIntent or Flutterwave payment link).
    The client should use the returned client_secret to complete payment on frontend.

    Args:
        payment_id: Payment ID
        database: Database connection
        current_user: Authenticated user
        organization_id: Organization ID

    Returns:
        Payment intent with client_secret

    Raises:
        HTTPException: If payment not found or gateway error
    """
    try:
        service = PaymentService(database)
        intent = await service.create_payment_intent(payment_id, organization_id)
        return intent

    except ValueError as e:
        logger.error(f"Failed to create payment intent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating intent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize payment"
        )


@router.post("/{payment_id}/confirm", response_model=Payment)
async def confirm_payment(
    payment_id: str,
    confirm_data: PaymentConfirm = None,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    organization_id: str = Depends(get_organization_context)
):
    """
    Confirm payment after gateway processing.

    Called after successful payment on frontend to verify and complete the payment.
    This endpoint verifies the payment with the gateway and updates status.

    Args:
        payment_id: Payment ID
        confirm_data: Optional confirmation data from gateway
        database: Database connection
        current_user: Authenticated user
        organization_id: Organization ID

    Returns:
        Updated payment with completed status

    Raises:
        HTTPException: If confirmation fails
    """
    try:
        service = PaymentService(database)
        payment = await service.confirm_payment(
            payment_id=payment_id,
            organization_id=organization_id,
            confirm_data=confirm_data
        )
        return payment

    except ValueError as e:
        logger.error(f"Payment confirmation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error confirming payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm payment"
        )


@router.get("/{payment_id}", response_model=Payment)
async def get_payment(
    payment_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    organization_id: str = Depends(get_organization_context)
):
    """
    Get payment by ID.

    Retrieves detailed information about a specific payment.

    Args:
        payment_id: Payment ID
        database: Database connection
        current_user: Authenticated user
        organization_id: Organization ID

    Returns:
        Payment details

    Raises:
        HTTPException: If payment not found
    """
    service = PaymentService(database)
    payment = await service.get_payment(payment_id, organization_id)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found"
        )

    return payment


@router.get("", response_model=PaymentListResponse)
async def list_payments(
    status: str = None,
    gateway: str = None,
    payment_method: str = None,
    customer_id: str = None,
    property_id: str = None,
    invoice_id: str = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    organization_id: str = Depends(get_organization_context)
):
    """
    List payments with filters.

    Retrieves paginated list of payments with optional filters.

    Args:
        status: Filter by payment status
        gateway: Filter by payment gateway
        payment_method: Filter by payment method
        customer_id: Filter by customer
        property_id: Filter by property
        invoice_id: Filter by invoice
        limit: Page size (max 100)
        offset: Page offset
        sort_by: Sort field
        sort_order: Sort order (asc/desc)
        database: Database connection
        current_user: Authenticated user
        organization_id: Organization ID

    Returns:
        Paginated list of payments

    Raises:
        HTTPException: If query fails
    """
    try:
        # Parse filters
        filters = PaymentListFilters(
            status=[status] if status else None,
            gateway=[gateway] if gateway else None,
            payment_method=[payment_method] if payment_method else None,
            customer_id=customer_id,
            property_id=property_id,
            invoice_id=invoice_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )

        service = PaymentService(database)
        result = await service.list_payments(organization_id, filters)
        return result

    except Exception as e:
        logger.error(f"Failed to list payments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payments"
        )


@router.post("/{payment_id}/refund", response_model=Payment)
async def refund_payment(
    payment_id: str,
    refund_data: PaymentRefund,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    organization_id: str = Depends(get_organization_context)
):
    """
    Refund a payment (full or partial).

    Processes a refund through the payment gateway and updates the payment record.
    Refunds can be partial (specify amount) or full (omit amount).

    Args:
        payment_id: Payment ID to refund
        refund_data: Refund details (amount, reason)
        database: Database connection
        current_user: Authenticated user
        organization_id: Organization ID

    Returns:
        Updated payment with refund information

    Raises:
        HTTPException: If refund fails or payment not eligible
    """
    try:
        service = PaymentService(database)
        payment = await service.refund_payment(
            payment_id=payment_id,
            organization_id=organization_id,
            refund_data=refund_data
        )
        return payment

    except ValueError as e:
        logger.error(f"Refund failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error processing refund: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process refund"
        )


@router.get("/stats/overview", response_model=PaymentStats)
async def get_payment_stats(
    currency: str = "GHS",
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    organization_id: str = Depends(get_organization_context)
):
    """
    Get payment statistics.

    Retrieves aggregated payment statistics including revenue, status counts,
    and breakdown by payment method.

    Args:
        currency: Currency filter (default: GHS)
        database: Database connection
        current_user: Authenticated user
        organization_id: Organization ID

    Returns:
        Payment statistics

    Raises:
        HTTPException: If stats retrieval fails
    """
    try:
        service = PaymentService(database)
        stats = await service.get_stats(organization_id, currency)
        return stats

    except Exception as e:
        logger.error(f"Failed to get payment stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


# Webhook endpoints (no authentication required - verified by signature)
@router.post("/webhooks/stripe", include_in_schema=False)
async def stripe_webhook(
    request_body: Dict[str, Any],
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    database: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Handle Stripe webhook events.

    Processes webhook events from Stripe for payment status updates.
    Signature verification is performed for security.

    Args:
        request_body: Webhook payload
        stripe_signature: Stripe webhook signature
        database: Database connection

    Returns:
        Success response

    Raises:
        HTTPException: If webhook processing fails
    """
    try:
        # Create webhook event
        webhook_event = WebhookEvent(
            id=str(request_body.get("id", "")),
            gateway=PaymentGateway.STRIPE,
            event_type=request_body.get("type", ""),
            payload=request_body,
            signature=stripe_signature
        )

        service = PaymentService(database)
        result = await service.handle_webhook(webhook_event)

        return {"received": True, "status": result.get("status")}

    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook processing failed"
        )


@router.post("/webhooks/flutterwave", include_in_schema=False)
async def flutterwave_webhook(
    request_body: Dict[str, Any],
    verif_hash: str = Header(None, alias="verif-hash"),
    database: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Handle Flutterwave webhook events.

    Processes webhook events from Flutterwave for payment status updates.
    Hash verification is performed for security.

    Args:
        request_body: Webhook payload
        verif_hash: Flutterwave verification hash
        database: Database connection

    Returns:
        Success response

    Raises:
        HTTPException: If webhook processing fails
    """
    try:
        # Create webhook event
        webhook_event = WebhookEvent(
            id=str(request_body.get("id", "")),
            gateway=PaymentGateway.FLUTTERWAVE,
            event_type=request_body.get("event", ""),
            payload=request_body.get("data", {}),
            signature=verif_hash
        )

        service = PaymentService(database)
        result = await service.handle_webhook(webhook_event)

        return {"status": "success", "message": "Webhook processed"}

    except Exception as e:
        logger.error(f"Flutterwave webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook processing failed"
        )
