"""
Wallet API endpoints.

Integrates with shared wallet service from apps/shared/integration/wallet.py
"""

from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...core.database import get_database
from ...models.user import UserInDB
from ...schemas.wallet import WalletResponse, TopUpRequest, TopUpResponse
from ...api.dependencies import get_current_user
from ...services.wallet_service import EventFlowWalletService
from ...core.config import settings

router = APIRouter(prefix="/wallet", tags=["Wallet"])

# Global wallet service instance (initialized at app startup)
_wallet_service_instance: Optional[EventFlowWalletService] = None


async def get_wallet_service() -> EventFlowWalletService:
    """Get or initialize wallet service."""
    global _wallet_service_instance
    if _wallet_service_instance is None:
        _wallet_service_instance = EventFlowWalletService()
        # Initialize with MongoDB URI from settings
        await _wallet_service_instance.initialize(
            mongodb_uri=settings.mongodb_url,
            database_name="kasaai_wallets"
        )
    return _wallet_service_instance


@router.get("/balance", response_model=WalletResponse)
async def get_wallet_balance(
    current_user: UserInDB = Depends(get_current_user),
    wallet_service: EventFlowWalletService = Depends(get_wallet_service),
):
    """
    Get wallet balance for current user.

    Returns:
        Current wallet balance and details
    """
    if not current_user.wallet_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found for user"
        )

    balance = await wallet_service.get_user_balance(current_user.wallet_id)

    if balance is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve wallet balance"
        )

    return WalletResponse(
        wallet_id=current_user.wallet_id,
        balance=float(balance),
        currency="GHS",
        user_id=current_user.id,
    )


@router.post("/top-up", response_model=TopUpResponse)
async def initiate_top_up(
    request: TopUpRequest,
    current_user: UserInDB = Depends(get_current_user),
    wallet_service: EventFlowWalletService = Depends(get_wallet_service),
):
    """
    Initiate wallet top-up via Paystack.

    Args:
        request: Top-up request with amount

    Returns:
        Payment URL and reference for completing payment
    """
    if not current_user.wallet_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found for user"
        )

    # Initiate top-up with Paystack
    from apps.shared.integration.wallet import PaymentGateway

    result = await wallet_service.topup_wallet(
        wallet_id=current_user.wallet_id,
        amount=Decimal(str(request.amount)),
        gateway=PaymentGateway.PAYSTACK,
        payment_metadata={
            "email": current_user.email or f"{current_user.phone}@eventflow.local",
            "callback_url": "https://eventflow.ailabsafrica.com/wallet/payment-callback"
        }
    )

    if not result or not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate payment"
        )

    return TopUpResponse(
        payment_url=result.get("payment_url", ""),
        reference=result.get("reference", ""),
    )


@router.get("/transactions")
async def get_wallet_transactions(
    event_id: Optional[str] = Query(None, description="Filter by event ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_user),
    wallet_service: EventFlowWalletService = Depends(get_wallet_service),
):
    """
    Get wallet transaction history.

    Args:
        event_id: Optional event ID to filter transactions
        page: Page number
        page_size: Page size

    Returns:
        List of transactions with pagination
    """
    if not current_user.wallet_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found for user"
        )

    # For now, return empty list
    # TODO: Implement transaction history retrieval from shared wallet service
    return {
        "data": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
        "message": "Transaction history feature coming soon"
    }


@router.get("/events/{event_id}/spending")
async def get_event_spending(
    event_id: str,
    current_user: UserInDB = Depends(get_current_user),
    wallet_service: EventFlowWalletService = Depends(get_wallet_service),
):
    """
    Get total spending for a specific event.

    Args:
        event_id: Event ID

    Returns:
        Spending breakdown by service
    """
    if not current_user.wallet_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found for user"
        )

    spending = await wallet_service.get_event_spending(
        wallet_id=current_user.wallet_id,
        event_id=event_id
    )

    return spending
