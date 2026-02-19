"""
Wallet schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class WalletResponse(BaseModel):
    """Wallet response schema."""

    wallet_id: str
    balance: float
    currency: str = "GHS"
    user_id: str


class TopUpRequest(BaseModel):
    """Top-up request schema."""

    amount: float = Field(..., description="Amount to top up", gt=0)
    payment_method: str = Field(default="paystack", description="Payment method")
    callback_url: Optional[str] = Field(None, description="Callback URL after payment")


class TopUpResponse(BaseModel):
    """Top-up response schema."""

    payment_url: str = Field(..., description="Paystack payment URL")
    reference: str = Field(..., description="Payment reference")


class TransactionResponse(BaseModel):
    """Transaction response schema."""

    id: str
    wallet_id: str
    type: str  # "credit" or "debit"
    amount: float
    description: str
    balance_after: float
    timestamp: datetime
    metadata: Optional[dict] = None
