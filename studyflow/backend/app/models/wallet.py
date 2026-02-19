"""
Wallet and transaction models for StudyFlow.

Tracks parent wallets, credits, debits, and payment history.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class TransactionType(str, Enum):
    """Transaction type."""
    CREDIT = "credit"
    DEBIT = "debit"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"


class TransactionStatus(str, Enum):
    """Transaction status."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class PaymentMethod(str, Enum):
    """Payment method."""
    PAYSTACK = "paystack"
    FLUTTERWAVE = "flutterwave"
    MTN_MOMO = "mtn_momo"
    VODAFONE_CASH = "vodafone_cash"
    AIRTELTIGO_MONEY = "airteltigo_money"
    BANK_TRANSFER = "bank_transfer"
    MANUAL = "manual"


class Transaction(BaseModel):
    """
    Transaction model for wallet operations.

    Attributes:
        id: MongoDB ObjectId as string
        organization_id: Organization ID for multi-tenancy
        wallet_id: Wallet ID
        user_id: User ID (parent)
        type: Transaction type
        status: Transaction status
        amount: Transaction amount in GHS
        balance_before: Balance before transaction
        balance_after: Balance after transaction
        description: Transaction description
        reference: External payment reference
        payment_method: Payment method used
        metadata: Additional transaction data
        created_at: Transaction timestamp
        completed_at: Completion timestamp
    """
    id: Optional[str] = Field(default=None, alias="_id")
    organization_id: str
    wallet_id: str
    user_id: str
    type: TransactionType
    status: TransactionStatus = TransactionStatus.PENDING

    amount: float
    balance_before: float
    balance_after: float

    description: str
    reference: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None

    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class Wallet(BaseModel):
    """
    Wallet model for parent accounts.

    Attributes:
        id: MongoDB ObjectId as string
        organization_id: Organization ID for multi-tenancy
        user_id: Parent user ID
        balance: Current balance in GHS
        currency: Currency code
        total_credited: Total amount credited
        total_debited: Total amount debited
        last_transaction_at: Last transaction timestamp
        is_active: Wallet active status
        metadata: Additional wallet data
        created_at: Wallet creation timestamp
        updated_at: Last update timestamp
    """
    id: Optional[str] = Field(default=None, alias="_id")
    organization_id: str
    user_id: str
    balance: float = 0.0
    currency: str = "GHS"

    total_credited: float = 0.0
    total_debited: float = 0.0

    last_transaction_at: Optional[datetime] = None
    is_active: bool = True

    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class WalletCreate(BaseModel):
    """
    Schema for creating a new wallet.

    Attributes:
        organization_id: Organization ID for multi-tenancy
        user_id: Parent user ID
        initial_balance: Initial balance (optional)
    """
    organization_id: str
    user_id: str
    initial_balance: float = 0.0
    metadata: dict = Field(default_factory=dict)


class WalletResponse(BaseModel):
    """
    Wallet response model for API responses.
    """
    id: str
    organization_id: str
    user_id: str
    balance: float
    currency: str
    is_active: bool
    created_at: datetime

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TransactionCreate(BaseModel):
    """
    Schema for creating a transaction.

    Attributes:
        wallet_id: Wallet ID
        type: Transaction type
        amount: Transaction amount
        description: Transaction description
        payment_method: Payment method
        reference: External reference
    """
    wallet_id: str
    type: TransactionType
    amount: float
    description: str
    payment_method: Optional[PaymentMethod] = None
    reference: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class TransactionResponse(BaseModel):
    """
    Transaction response model for API responses.
    """
    id: str
    organization_id: str
    wallet_id: str
    user_id: str
    type: TransactionType
    status: TransactionStatus
    amount: float
    balance_after: float
    description: str
    reference: Optional[str]
    payment_method: Optional[PaymentMethod]
    created_at: datetime

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaymentInitiation(BaseModel):
    """
    Schema for initiating a payment (top-up).

    Attributes:
        wallet_id: Wallet ID
        amount: Amount to top up
        payment_method: Payment method
        callback_url: Callback URL for payment confirmation
    """
    wallet_id: str
    amount: float
    payment_method: PaymentMethod
    callback_url: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class PaymentConfirmation(BaseModel):
    """
    Schema for confirming a payment.

    Sent by payment gateway webhook.
    """
    reference: str
    status: str  # success, failed, cancelled
    amount: float
    payment_method: PaymentMethod
    metadata: dict = Field(default_factory=dict)


class WalletSummary(BaseModel):
    """
    Wallet summary for analytics.

    Used for parent dashboard and reports.
    """
    wallet_id: str
    user_id: str
    current_balance: float
    total_spent_this_month: float
    total_spent_lifetime: float
    transaction_count_this_month: int
    top_spending_subject: Optional[str] = None
    average_session_cost: float = 0.0
    low_balance_alert: bool = False
    period_start: datetime
    period_end: datetime

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
