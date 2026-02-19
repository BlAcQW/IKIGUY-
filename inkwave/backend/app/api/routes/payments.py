"""
Payment API routes for InkWave.

Handles book purchases, saved cards, and payment verification using ExpressPay.
"""

import asyncio
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Depends, Header, Request

from ...core.auth import get_current_user
from ...services.payment_service import get_payment_service, InkWavePaymentService
from ...services.email_notification_service import get_email_service
from ...models.payment import (
    SaveCardRequest,
    SavedCardResponse,
    BookPurchaseRequest,
    PaymentInitiateResponse,
    PaymentVerifyResponse,
)

router = APIRouter(prefix="/payments", tags=["Payments"])
logger = logging.getLogger(__name__)


@router.post(
    "/cards/save",
    summary="Save payment card",
    description="Save a card for future payments using ExpressPay tokenization"
)
async def save_card(
    request: SaveCardRequest,
    current_user: dict = Depends(get_current_user),
    payment_service: InkWavePaymentService = Depends(get_payment_service)
):
    """
    Save a payment card for future use.

    The card is tokenized securely using ExpressPay.
    Card details are never stored - only the secure token.

    Args:
        request: Card details to save

    Returns:
        Saved card information
    """
    try:
        user_id = current_user.user_id
        email = current_user.email
        name = getattr(current_user, "full_name", current_user.email)

        if not email:
            raise HTTPException(status_code=400, detail="User email required")

        result = await payment_service.save_card(
            user_id=user_id,
            card_request=request,
            customer_email=email,
            customer_name=name,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to save card")
            )

        return {
            "success": True,
            "card_id": result["card_id"],
            "last4": result["last4"],
            "card_type": result.get("card_type"),
            "message": "Card saved successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save card: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save card: {str(e)}"
        )


@router.get(
    "/cards",
    response_model=List[SavedCardResponse],
    summary="Get saved cards",
    description="Get all saved payment cards for the authenticated user"
)
async def get_saved_cards(
    current_user: dict = Depends(get_current_user),
    payment_service: InkWavePaymentService = Depends(get_payment_service)
):
    """
    Get user's saved payment cards.

    Returns:
        List of saved cards
    """
    try:
        user_id = current_user.user_id
        cards = await payment_service.get_saved_cards(user_id)

        return [
            SavedCardResponse(
                id=str(card.id),
                last4=card.last4,
                card_type=card.card_type,
                expiry_month=card.expiry_month,
                expiry_year=card.expiry_year,
                is_default=card.is_default,
                created_at=card.created_at.isoformat(),
            )
            for card in cards
        ]

    except Exception as e:
        logger.error(f"Failed to get saved cards: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get saved cards: {str(e)}"
        )


@router.delete(
    "/cards/{card_id}",
    summary="Delete saved card",
    description="Delete a saved payment card"
)
async def delete_saved_card(
    card_id: str,
    current_user: dict = Depends(get_current_user),
    payment_service: InkWavePaymentService = Depends(get_payment_service)
):
    """
    Delete a saved payment card.

    Args:
        card_id: Card ID to delete

    Returns:
        Deletion confirmation
    """
    try:
        user_id = current_user.user_id
        success = await payment_service.delete_saved_card(user_id, card_id)

        if not success:
            raise HTTPException(status_code=404, detail="Card not found")

        return {"success": True, "message": "Card deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete card: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete card: {str(e)}"
        )


@router.post(
    "/books/purchase",
    response_model=PaymentInitiateResponse,
    summary="Purchase a book",
    description="Purchase a book using ExpressPay (new card or saved card)"
)
async def purchase_book(
    request: BookPurchaseRequest,
    current_user: dict = Depends(get_current_user),
    payment_service: InkWavePaymentService = Depends(get_payment_service)
):
    """
    Purchase a book.

    Can use either:
    - A saved card (use_saved_card=true, saved_card_id=<id>)
    - A new card (payment URL will be returned for checkout)

    Args:
        request: Purchase request

    Returns:
        Payment initiation response
    """
    try:
        user_id = current_user.user_id
        email = current_user.email
        name = getattr(current_user, "full_name", current_user.email)

        if not email:
            raise HTTPException(status_code=400, detail="User email required")

        result = await payment_service.purchase_book(
            user_id=user_id,
            request=request,
            customer_email=email,
            customer_name=name,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Purchase failed")
            )

        return PaymentInitiateResponse(
            success=True,
            order_id=result["order_id"],
            payment_url=result.get("payment_url"),
            requires_redirect=result.get("requires_redirect", True),
            transaction_id=result.get("transaction_id"),
            message=result.get("message", "Payment initiated successfully"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to purchase book: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Purchase failed: {str(e)}"
        )


@router.get(
    "/verify/{order_id}",
    response_model=PaymentVerifyResponse,
    summary="Verify payment",
    description="Verify payment status after user completes payment"
)
async def verify_payment(
    order_id: str,
    token: str,
    payment_service: InkWavePaymentService = Depends(get_payment_service)
):
    """
    Verify payment status.

    Called after user completes payment to verify status
    and credit their account.

    Args:
        order_id: Order ID to verify
        token: Payment token from ExpressPay

    Returns:
        Payment verification result
    """
    try:
        result = await payment_service.verify_payment(order_id, token)

        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Verification failed")
            )

        return PaymentVerifyResponse(
            success=True,
            paid=result.get("paid", False),
            transaction_id=result.get("transaction_id"),
            amount=result.get("amount"),
            currency=result.get("currency", "GHS"),
            order_id=order_id,
            message="Payment verified successfully" if result.get("paid") else "Payment not completed",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify payment: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}"
        )


@router.get(
    "/callback",
    summary="Payment callback",
    description="Handle ExpressPay redirect after payment completion"
)
async def payment_callback(
    request: Request,
    payment_service: InkWavePaymentService = Depends(get_payment_service)
):
    """
    Handle ExpressPay redirect callback after payment.

    ExpressPay redirects to this endpoint after the user completes payment.
    This endpoint verifies the payment and returns detailed status.

    Query Parameters (from ExpressPay):
        - order-id: The order ID
        - token: The payment token
        - result: Payment result (1=success, 2=declined, 3=error, 4=pending)

    Returns:
        Detailed payment status with transaction information
    """
    try:
        # Get query parameters from ExpressPay redirect
        params = dict(request.query_params)
        order_id = params.get("order-id")
        token = params.get("token")
        expresspay_result = params.get("result")

        logger.info(f"Payment callback received: order_id={order_id}, result={expresspay_result}")

        if not order_id or not token:
            logger.warning(f"Payment callback missing parameters: {params}")
            return {
                "success": False,
                "status": "error",
                "message": "Missing required parameters (order-id or token)",
                "redirect_url": "/wallet?payment=error&reason=missing_params"
            }

        # Verify payment with ExpressPay
        result = await payment_service.verify_payment(order_id, token)

        if result.get("success") and result.get("paid"):
            # Payment successful
            transaction = await payment_service.get_transaction(order_id)

            response_data = {
                "success": True,
                "status": "completed",
                "message": "Payment completed successfully!",
                "transaction": {
                    "order_id": order_id,
                    "transaction_id": result.get("transaction_id"),
                    "amount": result.get("amount"),
                    "currency": result.get("currency", "GHS"),
                    "payment_method": result.get("payment_method"),
                    "date_processed": result.get("date_processed"),
                    "card_last4": result.get("card_last4"),
                    "card_type": result.get("card_type"),
                    "status_message": result.get("status_message", "Payment successful"),
                },
                "redirect_url": f"/wallet?payment=success&order_id={order_id}&amount={result.get('amount')}&tx_id={result.get('transaction_id')}"
            }

            logger.info(f"Payment successful for order {order_id}: {result.get('transaction_id')}")

            # Send payment confirmation email asynchronously
            if transaction and transaction.customer_email:
                try:
                    email_service = get_email_service()
                    asyncio.create_task(
                        email_service.send_payment_confirmation(
                            to_email=transaction.customer_email,
                            customer_name=transaction.customer_name or "Customer",
                            amount=result.get("amount") or transaction.amount,
                            currency=result.get("currency", "GHS"),
                            order_id=order_id,
                            transaction_id=result.get("transaction_id") or "N/A",
                            item_description=transaction.order_desc or "InkWave Purchase",
                            payment_method=result.get("payment_method"),
                            card_last4=result.get("card_last4"),
                        )
                    )
                    logger.info(f"Payment confirmation email queued for {transaction.customer_email}")
                except Exception as email_err:
                    logger.error(f"Failed to queue payment confirmation email: {email_err}")

            return response_data

        elif result.get("success") and not result.get("paid"):
            # Payment not successful (declined, error, or pending)
            status_code = result.get("status_code", 0)
            status_message = result.get("status_message", "Payment not completed")

            status_map = {
                2: "declined",
                3: "error",
                4: "pending",
            }
            status = status_map.get(status_code, "failed")

            response_data = {
                "success": False,
                "status": status,
                "message": status_message,
                "order_id": order_id,
                "status_code": status_code,
                "redirect_url": f"/wallet?payment={status}&order_id={order_id}&reason={status_message}"
            }

            logger.warning(f"Payment {status} for order {order_id}: {status_message}")
            return response_data

        else:
            # Verification failed
            error_message = result.get("error", "Payment verification failed")

            return {
                "success": False,
                "status": "error",
                "message": error_message,
                "order_id": order_id,
                "error_type": result.get("error_type", "verification_error"),
                "redirect_url": f"/wallet?payment=error&order_id={order_id}&reason={error_message}"
            }

    except Exception as e:
        logger.error(f"Payment callback error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "status": "error",
            "message": f"Callback processing failed: {str(e)}",
            "redirect_url": "/wallet?payment=error&reason=callback_error"
        }


@router.post(
    "/webhook/expresspay",
    summary="ExpressPay webhook",
    description="Handle payment notifications from ExpressPay",
    include_in_schema=False  # Hide from public docs
)
async def expresspay_webhook(
    request: Request,
    signature: str = Header(None, alias="X-ExpressPay-Signature"),
    payment_service: InkWavePaymentService = Depends(get_payment_service)
):
    """
    Handle ExpressPay webhook notifications.

    Processes payment completion notifications from ExpressPay.

    Args:
        request: Webhook request
        signature: Webhook signature header

    Returns:
        Acknowledgment with detailed status
    """
    try:
        # Get webhook payload
        payload = await request.json()
        logger.info(f"ExpressPay webhook received: {payload}")

        # Verify signature
        if not payment_service.expresspay:
            logger.error("ExpressPay not configured for webhook")
            return {"status": "error", "message": "Service not configured"}

        if signature:
            is_valid = payment_service.expresspay.verify_webhook(payload, signature)
            if not is_valid:
                logger.error("Invalid webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")

        # Extract webhook data
        order_id = payload.get("order-id")
        token = payload.get("token")
        result = payload.get("result")  # 1 = success, 2 = declined, 3 = error, 4 = pending
        result_code = payload.get("result-code", result)

        if not order_id or not token:
            logger.warning(f"Webhook missing required fields: {payload}")
            return {"status": "ignored", "message": "Missing fields"}

        # Get transaction
        transaction = await payment_service.get_transaction(order_id)
        if not transaction:
            logger.warning(f"Transaction not found: {order_id}")
            return {"status": "ignored", "message": "Transaction not found"}

        # Map result codes to status
        status_map = {
            1: "completed",
            2: "declined",
            3: "error",
            4: "pending",
        }
        payment_status = status_map.get(result_code, "failed")

        # Update transaction based on result
        if result == 1:  # Payment successful
            # Verify and get full details from ExpressPay
            verify_result = await payment_service.verify_payment(order_id, token)

            # Store comprehensive payment details
            await payment_service.payment_transactions.update_one(
                {"order_id": order_id},
                {
                    "$set": {
                        "status": "completed",
                        "transaction_id": payload.get("transaction-id") or verify_result.get("transaction_id"),
                        "payment_method": payload.get("payment-method") or verify_result.get("payment_method"),
                        "card_last4": payload.get("card-number", "")[-4:] if payload.get("card-number") else None,
                        "card_type": payload.get("card-type"),
                        "amount_paid": payload.get("amount") or verify_result.get("amount"),
                        "currency": payload.get("currency", "GHS"),
                        "completed_at": datetime.utcnow(),
                        "webhook_received_at": datetime.utcnow(),
                        "expresspay_response": payload,
                    }
                }
            )
            logger.info(f"Webhook: Payment completed for {order_id} - TX: {payload.get('transaction-id')}")

            # Send payment confirmation email asynchronously
            if transaction and transaction.customer_email:
                try:
                    email_service = get_email_service()
                    asyncio.create_task(
                        email_service.send_payment_confirmation(
                            to_email=transaction.customer_email,
                            customer_name=transaction.customer_name or "Customer",
                            amount=payload.get("amount") or verify_result.get("amount") or transaction.amount,
                            currency=payload.get("currency", "GHS"),
                            order_id=order_id,
                            transaction_id=payload.get("transaction-id") or verify_result.get("transaction_id") or "N/A",
                            item_description=transaction.order_desc or "InkWave Purchase",
                            payment_method=payload.get("payment-method") or verify_result.get("payment_method"),
                            card_last4=payload.get("card-number", "")[-4:] if payload.get("card-number") else None,
                        )
                    )
                    logger.info(f"Webhook: Payment confirmation email queued for {transaction.customer_email}")
                except Exception as email_err:
                    logger.error(f"Webhook: Failed to queue payment confirmation email: {email_err}")

            return {
                "status": "success",
                "order_id": order_id,
                "transaction_id": payload.get("transaction-id"),
                "message": "Payment recorded successfully"
            }
        else:
            # Payment failed/declined/pending
            error_message = payload.get("message", f"Payment {payment_status}")

            await payment_service.payment_transactions.update_one(
                {"order_id": order_id},
                {
                    "$set": {
                        "status": payment_status,
                        "error_message": error_message,
                        "error_code": result_code,
                        "failed_at": datetime.utcnow() if payment_status in ["failed", "declined", "error"] else None,
                        "webhook_received_at": datetime.utcnow(),
                        "expresspay_response": payload,
                    }
                }
            )
            logger.info(f"Webhook: Payment {payment_status} for {order_id}: {error_message}")
            return {
                "status": payment_status,
                "order_id": order_id,
                "message": error_message
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.get(
    "/transaction/{order_id}",
    summary="Get transaction",
    description="Get payment transaction details"
)
async def get_transaction(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    payment_service: InkWavePaymentService = Depends(get_payment_service)
):
    """
    Get payment transaction details.

    Args:
        order_id: Order ID

    Returns:
        Transaction details
    """
    try:
        transaction = await payment_service.get_transaction(order_id)

        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Verify user owns this transaction
        if transaction.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return {
            "order_id": transaction.order_id,
            "status": transaction.status,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "order_type": transaction.order_type,
            "order_desc": transaction.order_desc,
            "initiated_at": transaction.initiated_at.isoformat(),
            "completed_at": transaction.completed_at.isoformat() if transaction.completed_at else None,
            "payment_method": transaction.payment_method,
            "card_last4": transaction.card_last4,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get transaction: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get transaction: {str(e)}"
        )
