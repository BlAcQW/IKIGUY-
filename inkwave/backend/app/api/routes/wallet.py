"""
Wallet API routes for InkWave.

Provides endpoints for wallet management, balance checking, and top-ups.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime
from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel, Field

from ...services.wallet_service import get_wallet_service, InkWaveWalletService
from ...services.email_notification_service import get_email_service
from ...core.database import get_db
from apps.shared.dependencies.auth import get_current_user

router = APIRouter(prefix="/wallet", tags=["Wallet"])
logger = logging.getLogger(__name__)

# Payment records collection name
PAYMENT_RECORDS_COLLECTION = "payment_records"


class WalletBalanceResponse(BaseModel):
    """Response model for wallet balance."""
    user_id: str
    balance: float
    currency: str = "USD"


class TransactionResponse(BaseModel):
    """Response model for a single transaction."""
    id: str
    type: str
    amount: float
    description: str
    created_at: str
    metadata: dict


class TransactionListResponse(BaseModel):
    """Response model for transaction list."""
    user_id: str
    transactions: list
    total: int
    limit: int
    skip: int


class TopUpRequest(BaseModel):
    """Request model for wallet top-up."""
    amount: float = Field(..., gt=0, description="Amount to add (must be positive)")
    payment_gateway: str = Field(..., description="Payment gateway: paystack, stripe, or momo")
    payment_reference: str = Field(..., description="Payment reference/transaction ID")


class PaystackTopUpRequest(BaseModel):
    """Request model for Paystack top-up initiation."""
    amount: float = Field(..., gt=0, description="Amount to top up")
    callback_url: Optional[str] = Field(None, description="URL to redirect after payment")


class StripeTopUpRequest(BaseModel):
    """Request model for Stripe top-up initiation."""
    amount: float = Field(..., gt=0, description="Amount to top up")
    success_url: str = Field(..., description="URL to redirect after successful payment")
    cancel_url: str = Field(..., description="URL to redirect after cancelled payment")


class ExpressPayTopUpRequest(BaseModel):
    """Request model for ExpressPay top-up initiation."""
    amount: float = Field(..., gt=0, description="Amount to top up in GHS")
    redirect_url: Optional[str] = Field(None, description="URL to redirect after payment")


@router.get(
    "/balance",
    response_model=WalletBalanceResponse,
    summary="Get wallet balance",
    description="Get current wallet balance for the authenticated user"
)
async def get_balance(
    current_user: dict = Depends(get_current_user),
    wallet_service: InkWaveWalletService = Depends(get_wallet_service)
):
    """
    Get user's wallet balance.

    Returns:
        Wallet balance information
    """
    try:
        # Check if wallet service is initialized
        if not wallet_service.initialized:
            logger.warning("Wallet service not initialized")
            raise HTTPException(
                status_code=503,
                detail="Wallet service is currently unavailable. Please try again in a moment."
            )

        # Extract user_id from user dict
        user_id = current_user.get("id") or current_user.get("user_id")

        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found")

        balance = await wallet_service.get_balance(user_id)

        if balance is None:
            # Create wallet with welcome bonus if doesn't exist
            logger.info(f"Creating new wallet for user {user_id}")
            wallet = await wallet_service.create_user_wallet(user_id)
            if wallet:
                balance = wallet.balance
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Unable to access your wallet. Please contact support if this persists."
                )

        return {
            "user_id": user_id,
            "balance": float(balance),
            "currency": "USD"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get balance: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve wallet balance. Please try again later."
        )


@router.get(
    "/transactions",
    response_model=TransactionListResponse,
    summary="Get transaction history",
    description="Get transaction history for the authenticated user"
)
async def get_transactions(
    limit: int = 20,
    skip: int = 0,
    current_user: dict = Depends(get_current_user),
    wallet_service: InkWaveWalletService = Depends(get_wallet_service)
):
    """
    Get user's transaction history.

    Args:
        limit: Number of transactions to return (default: 20)
        skip: Number of transactions to skip (default: 0)

    Returns:
        Transaction history
    """
    try:
        # current_user is a dict from shared auth
        user_id = current_user.get("id") or current_user.get("user_id")

        transactions = await wallet_service.get_transactions(user_id, limit=limit, skip=skip)

        if transactions is None:
            raise HTTPException(status_code=500, detail="Failed to get transactions")

        # Format transactions
        formatted_transactions = []
        for tx in transactions:
            formatted_transactions.append({
                "id": str(tx.id),
                "type": tx.transaction_type,  # TransactionResponse has transaction_type as string
                "amount": float(tx.amount),
                "description": tx.description,
                "created_at": tx.created_at,  # Already ISO string from TransactionResponse
                "metadata": {}  # TransactionResponse doesn't include metadata
            })

        return {
            "user_id": user_id,
            "transactions": formatted_transactions,
            "total": len(formatted_transactions),
            "limit": limit,
            "skip": skip
        }

    except Exception as e:
        logger.error(f"Failed to get transactions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get transactions: {str(e)}")


@router.post(
    "/topup",
    summary="Top up wallet",
    description="Add funds to wallet after successful payment"
)
async def top_up_wallet(
    request: TopUpRequest,
    current_user: dict = Depends(get_current_user),
    wallet_service: InkWaveWalletService = Depends(get_wallet_service)
):
    """
    Top up user's wallet.

    Args:
        request: Top-up request with amount and payment details

    Returns:
        Transaction information
    """
    try:
        # current_user is a dict from shared auth
        user_id = current_user.get("id") or current_user.get("user_id")

        # Validate payment gateway
        from apps.shared.integration.wallet import PaymentGateway
        gateway_map = {
            "paystack": PaymentGateway.PAYSTACK,
            "stripe": PaymentGateway.STRIPE,
            "momo": PaymentGateway.MOMO
        }

        if request.payment_gateway.lower() not in gateway_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid payment gateway. Must be one of: {', '.join(gateway_map.keys())}"
            )

        gateway = gateway_map[request.payment_gateway.lower()]

        # Top up wallet
        transaction = await wallet_service.top_up_wallet(
            user_id=user_id,
            amount=Decimal(str(request.amount)),
            payment_gateway=gateway,
            payment_reference=request.payment_reference
        )

        if transaction is None:
            raise HTTPException(status_code=500, detail="Failed to top up wallet")

        return {
            "success": True,
            "transaction_id": str(transaction.id),
            "amount": float(transaction.amount),
            "new_balance": float(transaction.balance_after),
            "payment_reference": request.payment_reference
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to top up wallet: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to top up wallet: {str(e)}")


@router.post(
    "/topup/paystack/initiate",
    summary="Initiate Paystack top-up",
    description="Initiate a wallet top-up payment via Paystack"
)
async def initiate_paystack_topup(
    request: PaystackTopUpRequest,
    current_user: dict = Depends(get_current_user),
    wallet_service: InkWaveWalletService = Depends(get_wallet_service)
):
    """
    Initiate Paystack payment for wallet top-up.

    Returns:
        Payment URL for user to complete payment
    """
    try:
        # current_user is a dict from shared auth
        user_id = current_user.get("id") or current_user.get("user_id")
        email = current_user.get("email")

        if not email:
            raise HTTPException(status_code=400, detail="User email not found")

        result = await wallet_service.initiate_paystack_topup(
            user_id=user_id,
            amount=Decimal(str(request.amount)),
            email=email,
            callback_url=request.callback_url
        )

        if not result or not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to initiate payment")
            )

        # Create payment record for tracking
        reference = result["reference"]
        await _create_payment_record(
            reference=reference,
            user_id=user_id,
            email=email,
            amount=result["amount"],
            currency=result["currency"],
            gateway="paystack",
            wallet_id=None,  # Will be set by wallet service
        )

        return {
            "success": True,
            "payment_url": result["payment_url"],
            "reference": result["reference"],
            "amount": result["amount"],
            "currency": result["currency"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate Paystack payment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate payment: {str(e)}")


@router.post(
    "/topup/stripe/initiate",
    summary="Initiate Stripe top-up",
    description="Initiate a wallet top-up payment via Stripe"
)
async def initiate_stripe_topup(
    request: StripeTopUpRequest,
    current_user: dict = Depends(get_current_user),
    wallet_service: InkWaveWalletService = Depends(get_wallet_service)
):
    """
    Initiate Stripe payment for wallet top-up.

    Returns:
        Payment URL for user to complete payment
    """
    try:
        # current_user is a dict from shared auth
        user_id = current_user.get("id") or current_user.get("user_id")

        result = await wallet_service.initiate_stripe_topup(
            user_id=user_id,
            amount=Decimal(str(request.amount)),
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )

        if not result or not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to initiate payment")
            )

        return {
            "success": True,
            "payment_url": result["payment_url"],
            "reference": result["reference"],
            "amount": result["amount"],
            "currency": result["currency"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate Stripe payment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate payment: {str(e)}")


@router.get(
    "/topup/paystack/verify/{reference}",
    summary="Verify Paystack payment",
    description="Verify Paystack payment and credit wallet"
)
async def verify_paystack_payment(
    reference: str,
    wallet_service: InkWaveWalletService = Depends(get_wallet_service)
):
    """
    Verify Paystack payment and credit wallet if successful.

    Args:
        reference: Payment reference to verify

    Returns:
        Verification result
    """
    try:
        result = await wallet_service.verify_paystack_payment(reference)

        if not result or not result.get("success"):
            # Send failed payment email if we have customer info
            payment_data = result.get("payment_data", {})
            customer_email = payment_data.get("customer_email")
            if customer_email:
                email_service = get_email_service()
                asyncio.create_task(
                    email_service.send_payment_failed(
                        to_email=customer_email,
                        customer_name=customer_email.split("@")[0],
                        amount=payment_data.get("amount", 0),
                        currency=payment_data.get("currency", "GHS"),
                        reason=result.get("error", "Payment not completed"),
                        reference=reference,
                        payment_method="Paystack",
                    )
                )
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Payment verification failed")
            )

        # Payment successful - update payment record status
        await _update_payment_status(reference, "completed")

        # Send confirmation emails
        payment_data = result.get("payment_data", {})
        customer_email = payment_data.get("customer_email")
        user_id = payment_data.get("user_id")
        amount_ghs = payment_data.get("amount_ghs", 0)  # Use GHS amount for display
        currency = payment_data.get("currency", "GHS")

        if customer_email and user_id:
            try:
                email_service = get_email_service()
                # Get current balance after top-up
                balance = await wallet_service.get_balance(user_id)
                customer_name = customer_email.split("@")[0]

                # Send user confirmation email (use GHS for display)
                asyncio.create_task(
                    email_service.send_wallet_topup_success(
                        to_email=customer_email,
                        customer_name=customer_name,
                        amount=amount_ghs,
                        currency=currency,
                        new_balance=float(balance) if balance else 0,
                        reference=reference,
                        payment_method="Paystack",
                    )
                )
                logger.info(f"Wallet top-up email scheduled for {customer_email}")

                # Send admin notification email
                asyncio.create_task(
                    email_service.send_admin_payment_notification(
                        user_email=customer_email,
                        user_name=customer_name,
                        amount=amount_ghs,
                        currency=currency,
                        reference=reference,
                        payment_method="Paystack",
                    )
                )
                logger.info(f"Admin payment notification scheduled for Paystack payment")
            except Exception as email_error:
                # Don't fail the payment verification if email fails
                logger.error(f"Failed to send Paystack confirmation email: {email_error}")

        return {
            "success": True,
            "message": "Payment verified and wallet credited",
            "payment_data": result.get("payment_data")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify Paystack payment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Payment verification failed: {str(e)}")


@router.post(
    "/topup/expresspay/initiate",
    summary="Initiate ExpressPay top-up",
    description="Initiate a wallet top-up payment via ExpressPay (Ghana only, GHS)"
)
async def initiate_expresspay_topup(
    request: ExpressPayTopUpRequest,
    current_user: dict = Depends(get_current_user),
    wallet_service: InkWaveWalletService = Depends(get_wallet_service)
):
    """
    Initiate ExpressPay payment for wallet top-up.

    ExpressPay only supports Ghana Cedis (GHS) and is optimized
    for local Ghanaian payment methods including mobile money.

    Returns:
        Payment URL for user to complete payment
    """
    try:
        # current_user is a dict from shared auth
        user_id = current_user.get("id") or current_user.get("user_id")
        email = current_user.get("email")

        if not email:
            raise HTTPException(status_code=400, detail="User email not found")

        result = await wallet_service.initiate_expresspay_topup(
            user_id=user_id,
            amount=Decimal(str(request.amount)),
            email=email,
            callback_url=request.redirect_url
        )

        if not result or not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to initiate ExpressPay payment")
            )

        return {
            "success": True,
            "payment_url": result["payment_url"],
            "token": result["token"],
            "amount": result["amount"],
            "currency": result["currency"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate ExpressPay payment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate payment: {str(e)}")


@router.get(
    "/topup/expresspay/verify/{token}",
    summary="Verify ExpressPay payment",
    description="Verify ExpressPay payment and credit wallet"
)
async def verify_expresspay_payment(
    token: str,
    wallet_service: InkWaveWalletService = Depends(get_wallet_service)
):
    """
    Verify ExpressPay payment and credit wallet if successful.

    Args:
        token: ExpressPay payment token to verify

    Returns:
        Verification result with payment status
    """
    try:
        result = await wallet_service.verify_expresspay_payment(token)

        if not result:
            raise HTTPException(
                status_code=400,
                detail="Payment verification failed"
            )

        # Handle pending status for mobile money
        if result.get("status") == "pending":
            return {
                "success": False,
                "status": "pending",
                "message": result.get("error", "Payment is still being processed"),
                "payment_data": result.get("payment_data")
            }

        if not result.get("success"):
            # ExpressPay failed - we don't have email in this case, so just log
            logger.warning(
                f"ExpressPay payment failed: {result.get('error')} - token: {token}"
            )
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Payment verification failed")
            )

        # Payment successful - send confirmation emails
        payment_data = result.get("payment_data", {})
        user_id = payment_data.get("user_id")
        amount = payment_data.get("amount", 0)
        currency = payment_data.get("currency", "GHS")

        if user_id:
            try:
                # Try to get user email from Supabase or database
                from apps.shared.dependencies.auth import get_supabase_client
                supabase = get_supabase_client()
                user_response = supabase.auth.admin.get_user_by_id(user_id)

                if user_response and hasattr(user_response, 'user') and user_response.user:
                    customer_email = user_response.user.email
                    customer_name = user_response.user.user_metadata.get(
                        "full_name",
                        customer_email.split("@")[0] if customer_email else "Customer"
                    )

                    if customer_email:
                        email_service = get_email_service()
                        # Get current balance after top-up
                        balance = await wallet_service.get_balance(user_id)

                        # Send user confirmation email
                        asyncio.create_task(
                            email_service.send_wallet_topup_success(
                                to_email=customer_email,
                                customer_name=customer_name,
                                amount=amount,
                                currency=currency,
                                new_balance=float(balance) if balance else 0,
                                reference=token,
                                payment_method="ExpressPay",
                            )
                        )
                        logger.info(f"Wallet top-up email scheduled for {customer_email}")

                        # Send admin notification email
                        asyncio.create_task(
                            email_service.send_admin_payment_notification(
                                user_email=customer_email,
                                user_name=customer_name,
                                amount=amount,
                                currency=currency,
                                reference=token,
                                payment_method="ExpressPay",
                            )
                        )
                        logger.info(f"Admin payment notification scheduled for ExpressPay payment")
            except Exception as email_error:
                # Don't fail the payment verification if email fails
                logger.error(f"Failed to send ExpressPay confirmation email: {email_error}")

        return {
            "success": True,
            "message": "Payment verified and wallet credited",
            "payment_data": result.get("payment_data")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify ExpressPay payment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Payment verification failed: {str(e)}")


@router.post(
    "/webhooks/stripe",
    summary="Stripe webhook handler",
    description="Handle Stripe payment completion webhooks",
    include_in_schema=False  # Hide from public API docs
)
async def stripe_webhook(
    request: dict,
    wallet_service: InkWaveWalletService = Depends(get_wallet_service)
):
    """
    Handle Stripe webhook events.

    Processes checkout.session.completed events to credit user wallets
    after successful payments.

    Args:
        request: Stripe webhook event payload

    Returns:
        Success confirmation
    """
    try:
        event_type = request.get("type")

        if event_type == "checkout.session.completed":
            session = request.get("data", {}).get("object", {})
            metadata = session.get("metadata", {})

            wallet_id = metadata.get("wallet_id")
            reference = metadata.get("reference")

            if not wallet_id or not reference:
                logger.warning("Stripe webhook missing metadata")
                return {"status": "ignored", "reason": "missing_metadata"}

            # Get amount from session
            amount_in_cents = session.get("amount_total", 0)
            amount = Decimal(amount_in_cents) / 100

            # Credit wallet using shared wallet service
            if wallet_service.shared_wallet:
                await wallet_service.shared_wallet.credit(
                    wallet_id=wallet_id,
                    amount=amount,
                    description="Wallet top-up via Stripe",
                    reference=reference,
                    idempotency_key=reference,
                    metadata={
                        "gateway": "stripe",
                        "session_id": session.get("id"),
                        "payment_status": session.get("payment_status")
                    }
                )

                logger.info(f"Stripe webhook: Credited {amount} to wallet {wallet_id}")
                return {"status": "success", "wallet_id": wallet_id, "amount": float(amount)}

        return {"status": "ignored", "event_type": event_type}

    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Webhook processing failed: {str(e)}")


@router.get(
    "/health",
    summary="Wallet service health check",
    description="Check if wallet service is initialized and working"
)
async def wallet_health(
    wallet_service: InkWaveWalletService = Depends(get_wallet_service)
):
    """
    Health check for wallet service.

    Returns:
        Service health status
    """
    return {
        "status": "healthy" if wallet_service.initialized else "not_initialized",
        "service": "inkwave_wallet"
    }


# =============================================================================
# Payment Records Management (MongoDB-backed for persistence across restarts)
# =============================================================================

async def _create_payment_record(
    reference: str,
    user_id: str,
    email: str,
    amount: float,
    currency: str,
    gateway: str,
    wallet_id: str = None,
) -> dict:
    """
    Create a payment record in MongoDB for tracking.

    Uses upsert with reference as unique key to prevent duplicates.

    Args:
        reference: Unique payment reference
        user_id: User ID
        email: User email
        amount: Payment amount
        currency: Currency code
        gateway: Payment gateway name
        wallet_id: Wallet ID

    Returns:
        Payment record dict
    """
    db = get_db()
    record = {
        "reference": reference,
        "user_id": user_id,
        "email": email,
        "amount": amount,
        "currency": currency,
        "gateway": gateway,
        "wallet_id": wallet_id,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "verified_at": None,
        "error": None,
    }

    # Upsert to handle race conditions (if record already exists, return it)
    result = await db[PAYMENT_RECORDS_COLLECTION].find_one_and_update(
        {"reference": reference},
        {"$setOnInsert": record},
        upsert=True,
        return_document=True
    )

    logger.info(f"Created payment record: {reference} for user {user_id}")
    return result


async def _get_payment_record(reference: str) -> Optional[dict]:
    """
    Get payment record by reference from MongoDB.

    Args:
        reference: Payment reference

    Returns:
        Payment record dict or None
    """
    db = get_db()
    return await db[PAYMENT_RECORDS_COLLECTION].find_one({"reference": reference})


async def _update_payment_status(
    reference: str,
    status: str,
    error: str = None,
) -> Optional[dict]:
    """
    Update payment record status atomically in MongoDB.

    Args:
        reference: Payment reference
        status: New status (pending, completed, failed)
        error: Error message if failed

    Returns:
        Updated record or None
    """
    db = get_db()

    update_fields = {"status": status}
    if status == "completed":
        update_fields["verified_at"] = datetime.utcnow()
    if error:
        update_fields["error"] = error

    result = await db[PAYMENT_RECORDS_COLLECTION].find_one_and_update(
        {"reference": reference},
        {"$set": update_fields},
        return_document=True
    )

    if result:
        logger.info(f"Updated payment record {reference}: status={status}")
    return result


# =============================================================================
# Paystack Webhook Handler
# =============================================================================

def _verify_paystack_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify Paystack webhook signature using HMAC SHA512.

    Args:
        payload: Raw request body bytes
        signature: Signature from x-paystack-signature header
        secret: Paystack webhook secret

    Returns:
        True if signature is valid
    """
    if not signature or not secret:
        return False

    computed = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha512
    ).hexdigest()

    return hmac.compare_digest(computed, signature)


@router.post(
    "/webhooks/paystack",
    summary="Paystack webhook handler",
    description="Handle Paystack payment completion webhooks",
    include_in_schema=False
)
async def paystack_webhook(
    request: Request,
    wallet_service: InkWaveWalletService = Depends(get_wallet_service)
):
    """
    Handle Paystack webhook events.

    Processes charge.success events to credit user wallets after successful payments.
    Validates HMAC SHA512 signature for security.

    Returns:
        Success confirmation
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        signature = request.headers.get("x-paystack-signature", "")

        # Verify signature
        webhook_secret = os.getenv("PAYSTACK_WEBHOOK_SECRET")
        if webhook_secret:
            if not _verify_paystack_signature(body, signature, webhook_secret):
                logger.warning("Paystack webhook: Invalid signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        else:
            logger.warning("PAYSTACK_WEBHOOK_SECRET not configured - skipping signature verification")

        # Parse payload
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            logger.error("Paystack webhook: Invalid JSON payload")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        event_type = payload.get("event")
        data = payload.get("data", {})

        logger.info(f"Paystack webhook received: event={event_type}")

        if event_type == "charge.success":
            reference = data.get("reference")
            if not reference:
                logger.warning("Paystack webhook: Missing reference")
                return {"status": "ignored", "reason": "missing_reference"}

            # Check if already processed (idempotency)
            existing_record = await _get_payment_record(reference)
            if existing_record and existing_record.get("status") == "completed":
                logger.info(f"Paystack webhook: Payment {reference} already processed")
                return {"status": "already_processed", "reference": reference}

            # Extract payment details
            metadata = data.get("metadata", {}) or {}
            user_id = metadata.get("user_id")
            wallet_id = metadata.get("wallet_id")
            customer = data.get("customer", {}) or {}
            customer_email = customer.get("email")

            if not user_id or not wallet_id:
                logger.error(f"Paystack webhook: Missing user_id or wallet_id in metadata for {reference}")
                return {"status": "ignored", "reason": "missing_metadata"}

            # Get amount (Paystack sends in kobo for NGN, pesewas for GHS)
            amount_minor = data.get("amount", 0)
            currency = data.get("currency", "GHS")
            # Convert from minor units (pesewas) to major units (GHS)
            amount_ghs = Decimal(str(amount_minor)) / 100

            # Calculate credits granted and USD equivalent
            # Pricing model: 100 credits = $1 = GH₵1 (simplified)
            # User pays GH₵X → gets X*100 credits → wallet stores $X
            credits_granted = float(amount_ghs) * 100  # For display/logging
            usd_amount = amount_ghs  # Wallet stores USD (GH₵1 ≈ $1 in credits model)

            logger.info(
                f"Payment {reference}: amount_from_paystack={amount_minor} pesewas, "
                f"amount_GHS={amount_ghs}, credits_granted={credits_granted}, "
                f"usd_to_credit={usd_amount}"
            )

            # Credit wallet with USD equivalent (wallet stores balance in USD)
            # The billing system charges: cost = credits / 100 (in USD)
            # So wallet balance must be in USD for billing math to work
            try:
                if wallet_service.shared_wallet:
                    await wallet_service.shared_wallet.credit(
                        wallet_id=wallet_id,
                        amount=usd_amount,
                        description=f"Wallet top-up via Paystack ({reference}) - GH₵{amount_ghs}",
                        reference=reference,
                        idempotency_key=reference,
                        metadata={
                            "service": "inkwave_topup",
                            "payment_gateway": "paystack",
                            "payment_reference": reference,
                            "webhook_event": event_type,
                            "customer_email": customer_email,
                            "channel": data.get("channel"),
                            "paid_at": data.get("paid_at"),
                            "amount_ghs": float(amount_ghs),
                            "usd_credited": float(usd_amount),
                            "credits_granted": credits_granted,
                        }
                    )

                    # Update payment record
                    await _update_payment_status(reference, "completed")

                    # Get updated balance for logging
                    balance_after = await wallet_service.get_balance(user_id)
                    logger.info(
                        f"Paystack webhook: Credited ${usd_amount} ({credits_granted} credits, GH₵{amount_ghs}) "
                        f"to wallet {wallet_id}, balance_after=${balance_after}"
                    )

                    # Send confirmation emails
                    if customer_email:
                        try:
                            email_service = get_email_service()
                            customer_name = customer_email.split("@")[0]

                            # Send user confirmation (use GHS amount for display)
                            asyncio.create_task(
                                email_service.send_wallet_topup_success(
                                    to_email=customer_email,
                                    customer_name=customer_name,
                                    amount=float(amount_ghs),
                                    currency=currency,
                                    new_balance=float(balance_after) if balance_after else 0,
                                    reference=reference,
                                    payment_method="Paystack",
                                )
                            )

                            # Send admin notification
                            asyncio.create_task(
                                email_service.send_admin_payment_notification(
                                    user_email=customer_email,
                                    user_name=customer_name,
                                    amount=float(amount_ghs),
                                    currency=currency,
                                    reference=reference,
                                    payment_method="Paystack",
                                )
                            )
                            logger.info(f"Paystack webhook: Emails scheduled for {customer_email}")
                        except Exception as email_error:
                            logger.error(f"Paystack webhook: Email error - {email_error}")

                    return {
                        "status": "success",
                        "reference": reference,
                        "amount_ghs": float(amount_ghs),
                        "usd_credited": float(usd_amount),
                        "credits_granted": credits_granted,
                        "currency": currency,
                    }

            except Exception as credit_error:
                logger.error(f"Paystack webhook: Credit error - {credit_error}")
                await _update_payment_status(reference, "failed", str(credit_error))
                raise HTTPException(status_code=500, detail=f"Credit failed: {credit_error}")

        elif event_type == "charge.failed":
            reference = data.get("reference")
            if reference:
                await _update_payment_status(reference, "failed", "Payment failed at gateway")
                logger.info(f"Paystack webhook: Payment {reference} failed")
            return {"status": "recorded", "event": event_type}

        return {"status": "ignored", "event": event_type}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Paystack webhook error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


# =============================================================================
# Payment Status Endpoint
# =============================================================================

@router.get(
    "/payment/status/{reference}",
    summary="Get payment status",
    description="Get the status of a payment by reference"
)
async def get_payment_status(
    reference: str,
    wallet_service: InkWaveWalletService = Depends(get_wallet_service)
):
    """
    Get payment status for frontend polling.

    If local status is 'pending', checks with Paystack and triggers
    verification if payment completed.

    Args:
        reference: Payment reference

    Returns:
        Payment status information
    """
    # First check our database records
    record = await _get_payment_record(reference)

    if record:
        # If still pending, check with Paystack to see if payment completed
        if record["status"] == "pending":
            try:
                # Verify with Paystack
                result = await wallet_service.verify_paystack_payment(reference)
                if result and result.get("success"):
                    # Payment completed - update record
                    await _update_payment_status(reference, "completed")
                    record["status"] = "completed"
                    record["verified_at"] = datetime.utcnow().isoformat()
                    logger.info(f"Payment {reference} verified during status check")
            except Exception as e:
                # Log but don't fail - might just be pending at Paystack too
                logger.debug(f"Payment {reference} not yet verified: {e}")

        # Convert datetime objects to ISO strings for JSON response
        created_at = record.get("created_at")
        verified_at = record.get("verified_at")

        return {
            "reference": record["reference"],
            "status": record["status"],
            "amount": record["amount"],
            "currency": record["currency"],
            "created_at": created_at.isoformat() if hasattr(created_at, 'isoformat') else created_at,
            "verified_at": verified_at.isoformat() if hasattr(verified_at, 'isoformat') else verified_at,
            "error": record.get("error"),
        }

    # If not in local records, check with Paystack directly
    try:
        paystack = wallet_service._get_paystack_provider()
        if paystack:
            tx_status = await paystack.get_transaction_status(reference)
            status = tx_status.get("status", "unknown")

            # Map Paystack status to our status
            if status == "success":
                return {
                    "reference": reference,
                    "status": "completed",
                    "amount": float(tx_status.get("amount", 0)),
                    "currency": tx_status.get("currency", "GHS"),
                    "created_at": None,
                    "verified_at": tx_status.get("paid_at"),
                    "error": None,
                }
            elif status == "failed":
                return {
                    "reference": reference,
                    "status": "failed",
                    "amount": 0,
                    "currency": "GHS",
                    "created_at": None,
                    "verified_at": None,
                    "error": "Payment failed",
                }
            else:
                return {
                    "reference": reference,
                    "status": "pending",
                    "amount": 0,
                    "currency": "GHS",
                    "created_at": None,
                    "verified_at": None,
                    "error": None,
                }
    except Exception as e:
        logger.error(f"Failed to check payment status: {e}")

    # Not found
    raise HTTPException(status_code=404, detail="Payment not found")
