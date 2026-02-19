"""
Wallet routes for StudyFlow.

Handles wallet management, transactions, and payments.
"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request

from app.models.wallet import (
    WalletResponse,
    TransactionResponse,
    TransactionType,
    PaymentMethod,
    PaymentInitiation,
    WalletSummary
)
from app.models.user import UserRole
from app.services.wallet_service import WalletService
from app.services.user_service import UserService
from app.core.auth import get_current_user, get_current_user_with_org, OrganizationRoleChecker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wallet", tags=["Wallet"])

# Role checker for parents
require_parent = OrganizationRoleChecker([UserRole.PARENT])


@router.get("/me", response_model=WalletResponse)
async def get_my_wallet(
    user_context: dict = Depends(require_parent)
):
    """
    Get current parent's wallet with organization context.

    Creates wallet if it doesn't exist.

    Args:
        user_context: User context with organization info

    Returns:
        Wallet information
    """
    user_id = user_context["user_id"]
    organization_id = user_context["organization_id"]

    wallet = await WalletService.get_or_create_wallet(user_id, organization_id=organization_id)

    return WalletResponse(
        id=wallet.id,
        organization_id=wallet.organization_id,
        user_id=wallet.user_id,
        balance=wallet.balance,
        currency=wallet.currency,
        is_active=wallet.is_active,
        created_at=wallet.created_at
    )


@router.post("/top-up")
async def initiate_top_up(
    payment_data: PaymentInitiation,
    user_context: dict = Depends(require_parent)
):
    """
    Initiate wallet top-up with organization access control.

    Creates payment link via payment gateway.

    Args:
        payment_data: Payment details
        user_context: User context with organization info

    Returns:
        Payment authorization URL and reference

    Raises:
        HTTPException: If payment initiation fails
    """
    user_id = user_context["user_id"]
    organization_id = user_context["organization_id"]

    # Verify user owns this wallet and it's in their organization
    wallet = await WalletService.get_wallet_by_id(payment_data.wallet_id, organization_id=organization_id)
    if not wallet or wallet.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only top up your own wallet"
        )

    try:
        result = await WalletService.initiate_payment(
            wallet_id=payment_data.wallet_id,
            amount=payment_data.amount,
            payment_method=payment_data.payment_method,
            callback_url=payment_data.callback_url
        )

        logger.info(f"Payment initiated: {result.get('reference')} for wallet {payment_data.wallet_id}")

        return {
            "status": "success",
            "message": "Payment initiated successfully",
            "authorization_url": result.get("authorization_url"),
            "reference": result.get("reference"),
            "access_code": result.get("access_code")
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Payment initiation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate payment"
        )


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transaction_history(
    wallet_id: str,
    limit: int = 50,
    skip: int = 0,
    transaction_type: Optional[TransactionType] = None,
    user_context: dict = Depends(require_parent)
):
    """
    Get transaction history with organization access control.

    Args:
        wallet_id: Wallet ID
        limit: Maximum transactions to return
        skip: Number to skip (pagination)
        transaction_type: Filter by type
        user_context: User context with organization info

    Returns:
        List of transactions

    Raises:
        HTTPException: If unauthorized or wallet not found
    """
    user_id = user_context["user_id"]
    organization_id = user_context["organization_id"]

    # Verify user owns this wallet and it's in their organization
    wallet = await WalletService.get_wallet_by_id(wallet_id, organization_id=organization_id)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )

    if wallet.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own wallet transactions"
        )

    transactions = await WalletService.get_transaction_history(
        wallet_id=wallet_id,
        limit=limit,
        skip=skip,
        transaction_type=transaction_type
    )

    return [
        TransactionResponse(
            id=t.id,
            wallet_id=t.wallet_id,
            user_id=t.user_id,
            type=t.type,
            status=t.status,
            amount=t.amount,
            balance_after=t.balance_after,
            description=t.description,
            reference=t.reference,
            payment_method=t.payment_method,
            created_at=t.created_at
        )
        for t in transactions
    ]


@router.get("/summary", response_model=WalletSummary)
async def get_wallet_summary(
    wallet_id: str,
    period_days: int = 30,
    user_context: dict = Depends(require_parent)
):
    """
    Get wallet spending summary with organization context.

    Provides analytics on spending patterns.

    Args:
        wallet_id: Wallet ID
        period_days: Number of days to include
        user_context: User context with organization info

    Returns:
        Wallet summary with stats

    Raises:
        HTTPException: If unauthorized or wallet not found
    """
    user_id = user_context["user_id"]
    organization_id = user_context["organization_id"]

    # Verify user owns this wallet and it's in their organization
    wallet = await WalletService.get_wallet_by_id(wallet_id, organization_id=organization_id)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )

    if wallet.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own wallet summary"
        )

    try:
        summary = await WalletService.get_wallet_summary(
            wallet_id=wallet_id,
            period_days=period_days
        )
        return summary

    except Exception as e:
        logger.error(f"Error generating wallet summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate wallet summary"
        )


@router.get("/balance")
async def check_balance(
    current_user: dict = Depends(get_current_user)
):
    """
    Check current wallet balance.

    Quick endpoint for balance checks. Available to all authenticated users.

    Args:
        current_user: Current authenticated user

    Returns:
        Current balance and currency
    """
    user_id = current_user.get("sub") or current_user.get("id")
    organization_id = current_user.get("organization_id")

    wallet = await WalletService.get_or_create_wallet(user_id, organization_id=organization_id)

    return {
        "wallet_id": wallet.id,
        "balance": wallet.balance,
        "currency": wallet.currency,
        "low_balance_alert": wallet.balance < 10.0
    }


@router.post("/payment/callback")
async def payment_callback(request: Request):
    """
    Payment gateway webhook callback.

    Handles payment confirmations from payment gateway.

    Args:
        request: FastAPI request with webhook data

    Returns:
        Acknowledgment response
    """
    try:
        # Get webhook data
        data = await request.json()
        reference = data.get("reference")

        if not reference:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing payment reference"
            )

        # Verify payment
        verified = await WalletService.verify_payment(reference)

        if verified:
            logger.info(f"Payment callback processed: {reference}")
            return {
                "status": "success",
                "message": "Payment verified successfully"
            }
        else:
            logger.warning(f"Payment verification failed: {reference}")
            return {
                "status": "failed",
                "message": "Payment verification failed"
            }

    except Exception as e:
        logger.error(f"Payment callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process payment callback"
        )


@router.post("/admin/credit")
async def admin_credit_wallet(
    wallet_id: str,
    amount: float,
    description: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Admin endpoint to credit wallet.

    For manual top-ups and adjustments.

    Args:
        wallet_id: Wallet ID
        amount: Amount to credit
        description: Transaction description
        current_user: Current user (must be admin)

    Returns:
        Transaction details

    Raises:
        HTTPException: If unauthorized or operation fails
    """
    # Check admin role
    user_role = current_user.get("user_metadata", {}).get("role")
    if user_role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    try:
        transaction = await WalletService.credit_wallet(
            wallet_id=wallet_id,
            amount=amount,
            description=description,
            payment_method=PaymentMethod.MANUAL,
            reference=f"ADMIN-{datetime.utcnow().timestamp()}"
        )

        logger.info(f"Admin credited wallet {wallet_id}: {amount} GHS")

        return {
            "status": "success",
            "transaction_id": transaction.id,
            "amount": transaction.amount,
            "balance_after": transaction.balance_after
        }

    except Exception as e:
        logger.error(f"Admin credit error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/low-balance-alerts")
async def get_low_balance_alerts(
    threshold: float = 10.0,
    current_user: dict = Depends(get_current_user)
):
    """
    Get users with low wallet balance.

    Admin endpoint for monitoring.

    Args:
        threshold: Balance threshold
        current_user: Current user (must be admin)

    Returns:
        List of user IDs with low balance

    Raises:
        HTTPException: If unauthorized
    """
    # Check admin role
    user_role = current_user.get("user_metadata", {}).get("role")
    if user_role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    user_ids = await WalletService.get_low_balance_users(threshold)

    return {
        "threshold": threshold,
        "count": len(user_ids),
        "user_ids": user_ids
    }
