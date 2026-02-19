"""
Wallet API routes for ChurchFlow.

Provides endpoints for organization wallet management, balance checking, and top-ups.
"""

import logging
from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ...services.wallet_service import get_wallet_service, ChurchFlowWalletService
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/wallet", tags=["Wallet"])
logger = logging.getLogger(__name__)


class WalletBalanceResponse(BaseModel):
    """Response model for wallet balance."""
    organization_id: str
    balance: float
    currency: str = "GHS"


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
    organization_id: str
    transactions: list
    total: int
    limit: int
    skip: int


class TopUpRequest(BaseModel):
    """Request model for wallet top-up."""
    amount: float = Field(..., gt=0, description="Amount to add (must be positive)")
    payment_gateway: str = Field(..., description="Payment gateway: paystack, stripe, or momo")
    payment_reference: str = Field(..., description="Payment reference/transaction ID")


@router.get(
    "/balance",
    response_model=WalletBalanceResponse,
    summary="Get wallet balance",
    description="Get current wallet balance for the organization"
)
async def get_balance(
    current_user: dict = Depends(get_current_user),
    wallet_service: ChurchFlowWalletService = Depends(get_wallet_service)
):
    """
    Get organization's wallet balance.

    Returns:
        Wallet balance information
    """
    try:
        organization_id = current_user.get("organization_id") or current_user.get("user_id") or current_user.get("sub")

        balance = await wallet_service.get_balance(organization_id)

        if balance is None:
            raise HTTPException(status_code=500, detail="Failed to get wallet balance")

        return {
            "organization_id": organization_id,
            "balance": float(balance),
            "currency": "GHS"
        }

    except Exception as e:
        logger.error(f"Failed to get balance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get balance: {str(e)}")


@router.get(
    "/transactions",
    response_model=TransactionListResponse,
    summary="Get transaction history",
    description="Get transaction history for the organization"
)
async def get_transactions(
    limit: int = 20,
    skip: int = 0,
    current_user: dict = Depends(get_current_user),
    wallet_service: ChurchFlowWalletService = Depends(get_wallet_service)
):
    """
    Get organization's transaction history.

    Args:
        limit: Number of transactions to return (default: 20)
        skip: Number of transactions to skip (default: 0)

    Returns:
        Transaction history
    """
    try:
        organization_id = current_user.get("organization_id") or current_user.get("user_id") or current_user.get("sub")

        transactions = await wallet_service.get_transactions(organization_id, limit=limit, skip=skip)

        if transactions is None:
            raise HTTPException(status_code=500, detail="Failed to get transactions")

        # Format transactions
        formatted_transactions = []
        for tx in transactions:
            formatted_transactions.append({
                "id": str(tx.id),
                "type": tx.type.value,
                "amount": float(tx.amount),
                "description": tx.description,
                "created_at": tx.created_at.isoformat(),
                "metadata": tx.metadata or {}
            })

        return {
            "organization_id": organization_id,
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
    description="Add funds to organization wallet after successful payment"
)
async def top_up_wallet(
    request: TopUpRequest,
    current_user: dict = Depends(get_current_user),
    wallet_service: ChurchFlowWalletService = Depends(get_wallet_service)
):
    """
    Top up organization's wallet.

    Args:
        request: Top-up request with amount and payment details

    Returns:
        Transaction information
    """
    try:
        organization_id = current_user.get("organization_id") or current_user.get("user_id") or current_user.get("sub")

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
            organization_id=organization_id,
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


@router.get(
    "/health",
    summary="Wallet service health check",
    description="Check if wallet service is initialized and working"
)
async def wallet_health(
    wallet_service: ChurchFlowWalletService = Depends(get_wallet_service)
):
    """
    Health check for wallet service.

    Returns:
        Service health status
    """
    return {
        "status": "healthy" if wallet_service.initialized else "not_initialized",
        "service": "churchflow_wallet"
    }
