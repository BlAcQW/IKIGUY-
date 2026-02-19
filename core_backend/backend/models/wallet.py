"""
Wallet and Payment Transaction Models for KasaAI Core Backend.

MongoDB models for wallet management, payment transactions, and payment methods.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal
import uuid


class PaymentProvider(str, Enum):
    """Supported payment providers."""
    STRIPE = "stripe"
    FLUTTERWAVE = "flutterwave"
    MTN_MOMO = "mtn_momo"
    VODAFONE_CASH = "vodafone_cash"
    AIRTELTIGO_MONEY = "airteltigo_money"
    MPESA = "mpesa"
    PAGA = "paga"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"


class PaymentMethodType(str, Enum):
    """Types of payment methods."""
    CARD = "card"
    MOBILE_MONEY = "mobile_money"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"
    CRYPTO = "crypto"


class TransactionType(str, Enum):
    """Types of transactions."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    USAGE_CHARGE = "usage_charge"
    REFUND = "refund"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"


class TransactionStatus(str, Enum):
    """Transaction status states."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class Currency(str, Enum):
    """Supported currencies."""
    USD = "USD"
    GHS = "GHS"  # Ghana Cedi
    NGN = "NGN"  # Nigerian Naira
    KES = "KES"  # Kenyan Shilling
    ZAR = "ZAR"  # South African Rand
    EUR = "EUR"
    GBP = "GBP"


class PaymentMethod(BaseModel):
    """
    Payment method configuration for a user.

    Represents a saved payment method like a card, mobile money account,
    or bank account that a user can use for deposits.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User ID (from Supabase)")
    tenant_id: Optional[str] = Field(None, description="Tenant/organization ID")

    provider: PaymentProvider = Field(..., description="Payment provider")
    method_type: PaymentMethodType = Field(..., description="Payment method type")

    # Provider-specific data
    provider_customer_id: Optional[str] = Field(None, description="Provider's customer ID")
    provider_payment_method_id: Optional[str] = Field(None, description="Provider's payment method ID")

    # Display information
    display_name: str = Field(..., description="Display name (e.g., 'Visa ending in 4242')")
    nickname: Optional[str] = Field(None, description="User-provided nickname")

    # Method-specific details
    card_last4: Optional[str] = Field(None, description="Last 4 digits of card")
    card_brand: Optional[str] = Field(None, description="Card brand (Visa, Mastercard, etc.)")
    card_exp_month: Optional[int] = Field(None, description="Card expiration month")
    card_exp_year: Optional[int] = Field(None, description="Card expiration year")

    phone_number: Optional[str] = Field(None, description="Mobile money phone number")
    account_number: Optional[str] = Field(None, description="Bank account number")
    bank_name: Optional[str] = Field(None, description="Bank name")

    # Status and verification
    is_default: bool = Field(False, description="Default payment method")
    is_verified: bool = Field(False, description="Payment method verified")
    is_active: bool = Field(True, description="Payment method active")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = Field(None, description="Last time method was used")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "auth0|123456",
                "provider": "stripe",
                "method_type": "card",
                "display_name": "Visa ending in 4242",
                "card_last4": "4242",
                "card_brand": "visa",
                "is_default": True,
                "is_verified": True
            }
        }


class Wallet(BaseModel):
    """
    User wallet for storing funds and tracking balance.

    Each user has one wallet per currency.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User ID (from Supabase)")
    tenant_id: Optional[str] = Field(None, description="Tenant/organization ID")

    # Balance information
    balance: Decimal = Field(Decimal("0.00"), description="Current available balance")
    pending_balance: Decimal = Field(Decimal("0.00"), description="Pending balance (processing deposits)")
    reserved_balance: Decimal = Field(Decimal("0.00"), description="Reserved for pending charges")

    currency: Currency = Field(Currency.USD, description="Wallet currency")

    # Limits and settings
    auto_reload_enabled: bool = Field(False, description="Auto-reload when balance low")
    auto_reload_threshold: Decimal = Field(Decimal("10.00"), description="Balance threshold for auto-reload")
    auto_reload_amount: Decimal = Field(Decimal("50.00"), description="Amount to reload")
    auto_reload_payment_method_id: Optional[str] = Field(None, description="Payment method for auto-reload")

    # Low balance alerts
    low_balance_alert_enabled: bool = Field(True, description="Enable low balance alerts")
    low_balance_threshold: Decimal = Field(Decimal("20.00"), description="Alert threshold")

    # Status
    is_active: bool = Field(True, description="Wallet active")
    is_locked: bool = Field(False, description="Wallet locked (no withdrawals)")
    locked_reason: Optional[str] = Field(None, description="Reason for wallet lock")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_transaction_at: Optional[datetime] = Field(None, description="Last transaction timestamp")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @property
    def total_balance(self) -> Decimal:
        """Total balance including pending."""
        return self.balance + self.pending_balance

    @property
    def available_balance(self) -> Decimal:
        """Available balance after reservations."""
        return self.balance - self.reserved_balance

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "auth0|123456",
                "balance": "150.75",
                "pending_balance": "25.00",
                "currency": "USD",
                "auto_reload_enabled": True,
                "auto_reload_threshold": "10.00",
                "auto_reload_amount": "50.00"
            }
        }


class Transaction(BaseModel):
    """
    Payment transaction record.

    Records all financial transactions including deposits, withdrawals,
    usage charges, and refunds.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User ID (from Supabase)")
    tenant_id: Optional[str] = Field(None, description="Tenant/organization ID")
    wallet_id: str = Field(..., description="Associated wallet ID")

    # Transaction details
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    status: TransactionStatus = Field(TransactionStatus.PENDING, description="Transaction status")

    amount: Decimal = Field(..., description="Transaction amount")
    currency: Currency = Field(Currency.USD, description="Transaction currency")

    # Fees
    processing_fee: Decimal = Field(Decimal("0.00"), description="Processing fee charged")
    platform_fee: Decimal = Field(Decimal("0.00"), description="Platform fee")
    total_amount: Decimal = Field(..., description="Total amount (amount + fees)")

    # Payment method (for deposits/withdrawals)
    payment_method_id: Optional[str] = Field(None, description="Payment method used")
    payment_provider: Optional[PaymentProvider] = Field(None, description="Payment provider")

    # Provider transaction details
    provider_transaction_id: Optional[str] = Field(None, description="Provider's transaction ID")
    provider_reference: Optional[str] = Field(None, description="Provider reference")
    provider_response: Dict[str, Any] = Field(default_factory=dict, description="Provider response")

    # Transaction context
    description: str = Field(..., description="Transaction description")
    reference: Optional[str] = Field(None, description="External reference")

    # Related transactions (for refunds, reversals)
    related_transaction_id: Optional[str] = Field(None, description="Related transaction ID")

    # Balances before/after (for reconciliation)
    balance_before: Decimal = Field(..., description="Balance before transaction")
    balance_after: Decimal = Field(..., description="Balance after transaction")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    failed_at: Optional[datetime] = Field(None, description="Failure timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")

    # Failure information
    failure_reason: Optional[str] = Field(None, description="Failure reason")
    failure_code: Optional[str] = Field(None, description="Failure code")

    # Reconciliation
    is_reconciled: bool = Field(False, description="Transaction reconciled")
    reconciled_at: Optional[datetime] = Field(None, description="Reconciliation timestamp")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "auth0|123456",
                "wallet_id": "wallet_abc123",
                "transaction_type": "deposit",
                "status": "completed",
                "amount": "50.00",
                "currency": "USD",
                "processing_fee": "1.75",
                "total_amount": "51.75",
                "payment_provider": "stripe",
                "description": "Wallet deposit via Stripe",
                "balance_before": "100.00",
                "balance_after": "150.00"
            }
        }


class WebhookEvent(BaseModel):
    """
    Payment webhook event record.

    Records all incoming webhook events from payment providers
    for audit trail and reconciliation.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    provider: PaymentProvider = Field(..., description="Payment provider")
    event_type: str = Field(..., description="Provider event type")
    event_id: Optional[str] = Field(None, description="Provider event ID")

    # Raw webhook data
    raw_payload: Dict[str, Any] = Field(..., description="Raw webhook payload")
    headers: Dict[str, str] = Field(default_factory=dict, description="Webhook headers")

    # Processing status
    is_processed: bool = Field(False, description="Event processed")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")

    is_verified: bool = Field(False, description="Signature verified")
    verification_signature: Optional[str] = Field(None, description="Webhook signature")

    # Related entities
    transaction_id: Optional[str] = Field(None, description="Related transaction ID")
    user_id: Optional[str] = Field(None, description="Related user ID")

    # Processing result
    processing_error: Optional[str] = Field(None, description="Processing error")
    processing_attempts: int = Field(0, description="Number of processing attempts")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "stripe",
                "event_type": "payment_intent.succeeded",
                "event_id": "evt_1234567890",
                "raw_payload": {"id": "pi_123", "status": "succeeded"},
                "is_processed": True,
                "is_verified": True
            }
        }


class ProviderConfig(BaseModel):
    """
    Payment provider configuration.

    Stores API keys and settings for payment providers.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = Field(None, description="Tenant ID (for multi-tenancy)")

    provider: PaymentProvider = Field(..., description="Payment provider")
    environment: str = Field("sandbox", description="Environment (sandbox/production)")

    # API credentials (encrypted in production)
    api_key: str = Field(..., description="API key")
    secret_key: str = Field(..., description="Secret key")
    public_key: Optional[str] = Field(None, description="Public key")
    merchant_id: Optional[str] = Field(None, description="Merchant ID")

    # Webhook configuration
    webhook_url: str = Field(..., description="Webhook URL")
    webhook_secret: Optional[str] = Field(None, description="Webhook secret")

    # Provider-specific settings
    settings: Dict[str, Any] = Field(default_factory=dict, description="Provider settings")

    # Status
    is_active: bool = Field(True, description="Config active")
    is_verified: bool = Field(False, description="Config verified")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "flutterwave",
                "environment": "sandbox",
                "api_key": "FLWPUBK-xxxxx",
                "secret_key": "FLWSECK-xxxxx",
                "webhook_url": "https://api.ailabsafrica.com/webhooks/flutterwave",
                "is_active": True
            }
        }
