"""
Shared Billing Routes for Organization Wallet and Usage
Can be included in any KasaAI app
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Import will be adjusted per app
# from app.api.dependencies import get_current_user
# from apps.shared.services.billing_service import get_billing_service


class AddFundsRequest(BaseModel):
    """Request to add funds to wallet"""

    amount: float = Field(..., gt=0, description="Amount to add (must be positive)")
    description: str = Field(
        default="Funds added", description="Transaction description"
    )


class TransactionResponse(BaseModel):
    """Transaction response"""

    id: str
    organization_id: str
    type: str  # 'credit' or 'debit'
    amount: float
    balance_after: float
    description: str
    service: Optional[str] = None
    created_at: datetime


class WalletResponse(BaseModel):
    """Wallet response"""

    id: str
    organization_id: str
    balance: float
    currency: str
    created_at: datetime
    updated_at: datetime


class UsageStatsResponse(BaseModel):
    """Usage statistics response"""

    period: str
    start_date: str
    end_date: str
    total_spent: float
    services: Dict[str, Dict[str, Any]]


def create_billing_router(get_current_user_func, get_billing_service_func) -> APIRouter:
    """
    Create billing router with dependency injection.

    Args:
        get_current_user_func: Function to get current user
        get_billing_service_func: Function to get billing service

    Returns:
        Configured APIRouter

    Example:
        from app.api.dependencies import get_current_user
        from apps.shared.services.billing_service import get_billing_service
        router = create_billing_router(get_current_user, get_billing_service)
        app.include_router(router, prefix="/api/v1/organizations/{organization_id}")
    """
    router = APIRouter(tags=["Billing"])

    @router.get("/wallet", response_model=WalletResponse)
    async def get_wallet(
        organization_id: str,
        user: dict = Depends(get_current_user_func),
    ):
        """
        Get wallet for organization.

        Returns wallet balance and metadata.
        """
        billing_service = get_billing_service_func()

        # TODO: Verify user has access to this organization
        # This should check organization membership

        try:
            wallet = await billing_service.get_wallet(organization_id)
            return wallet
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/wallet/add-funds", response_model=TransactionResponse)
    async def add_funds(
        organization_id: str,
        request: AddFundsRequest,
        user: dict = Depends(get_current_user_func),
    ):
        """
        Add funds to organization wallet.

        Creates a credit transaction and increases wallet balance.
        """
        billing_service = get_billing_service_func()

        # TODO: Verify user has admin access to this organization

        try:
            transaction = await billing_service.add_funds(
                organization_id, request.amount, request.description
            )
            return transaction
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/transactions", response_model=List[TransactionResponse])
    async def get_transactions(
        organization_id: str,
        user: dict = Depends(get_current_user_func),
        limit: int = Query(50, ge=1, le=100),
        skip: int = Query(0, ge=0),
        type: Optional[str] = Query(None, regex="^(credit|debit)$"),
    ):
        """
        Get transaction history for organization.

        Returns list of credit and debit transactions.
        """
        billing_service = get_billing_service_func()

        # TODO: Verify user has access to this organization

        try:
            transactions = await billing_service.get_transactions(
                organization_id, limit=limit, skip=skip, transaction_type=type
            )
            return transactions
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/usage", response_model=UsageStatsResponse)
    async def get_usage_stats(
        organization_id: str,
        user: dict = Depends(get_current_user_func),
        period: str = Query("week", regex="^(day|week|month|year)$"),
    ):
        """
        Get usage statistics for organization.

        Returns spending by service for the specified time period.
        """
        billing_service = get_billing_service_func()

        # TODO: Verify user has access to this organization

        try:
            stats = await billing_service.get_usage_stats(organization_id, period)
            return stats
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
