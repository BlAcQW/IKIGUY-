"""
Unified Wallet Data Models

This module provides comprehensive data models for the wallet system,
combining the best features from both previous implementations:

From Core Backend:
- Advanced balance tracking (pending, reserved, available)
- Multi-tenancy support (tenant_id)
- Payment method management
- Provider configuration
- Webhook event logging
- Processing fees tracking

From Shared Library:
- Idempotency support
- Low balance alerting
- Decimal precision for all amounts
- Refund tracking
- Better validation

New Additions:
- Retry count tracking
- Enhanced metadata
- Improved type safety
- Better documentation

Author: KasaAI Team
Date: 2025-10-27
"""

import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


# ============================================================================
# ENUMS
# ============================================================================

class Currency(str, Enum):
    """Supported currencies."""

    GHS = "GHS"  # Ghanaian Cedi
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound
    NGN = "NGN"  # Nigerian Naira
    KES = "KES"  # Kenyan Shilling
    ZAR = "ZAR"  # South African Rand


class TransactionType(str, Enum):
    """
    Transaction types.

    DEPOSIT: Money added to wallet (from external source)
    WITHDRAWAL: Money removed from wallet (to external destination)
    USAGE_CHARGE: Money deducted for service usage
    REFUND: Money returned to wallet
    REVERSAL: Transaction reversal/cancellation
    CREDIT: Alias for deposit (for backwards compatibility)
    DEBIT: Alias for usage_charge (for backwards compatibility)
    """

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    USAGE_CHARGE = "usage_charge"
    REFUND = "refund"
    REVERSAL = "reversal"
    CREDIT = "credit"  # Alias
    DEBIT = "debit"    # Alias


class TransactionStatus(str, Enum):
    """Transaction status."""

    PENDING = "pending"        # Transaction created, not yet processing
    PROCESSING = "processing"  # Payment being processed by provider
    COMPLETED = "completed"    # Successfully completed
    FAILED = "failed"         # Failed permanently
    REVERSED = "reversed"     # Reversed/cancelled


class PaymentProvider(str, Enum):
    """Supported payment providers."""

    STRIPE = "stripe"
    FLUTTERWAVE = "flutterwave"
    PAYSTACK = "paystack"
    EXPRESSPAY = "expresspay"  # ExpressPay (Ghana)
    MTN_MOMO = "mtn_momo"
    VODAFONE_CASH = "vodafone_cash"
    AIRTELTIGO_MONEY = "airteltigo_money"
    MPESA = "mpesa"
    MANUAL = "manual"  # Manual/admin credit


# Backward compatibility alias for existing apps
PaymentGateway = PaymentProvider


class PaymentMethodType(str, Enum):
    """Payment method types."""

    CARD = "card"
    MOBILE_MONEY = "mobile_money"
    BANK_ACCOUNT = "bank_account"
    DIGITAL_WALLET = "digital_wallet"


class WalletStatus(str, Enum):
    """Wallet status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


# ============================================================================
# CORE MODELS
# ============================================================================

class Wallet(BaseModel):
    """
    Wallet model - unified from both implementations.

    Features:
    - Advanced balance tracking (pending, reserved, available)
    - Multi-currency support
    - Low balance alerting
    - Multi-tenancy support
    - Decimal precision for all amounts

    Example:
        wallet = Wallet(
            user_id="user123",
            currency=Currency.GHS,
            balance=Decimal("100.00")
        )
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    tenant_id: Optional[str] = None  # For multi-tenant applications

    # Balance tracking
    balance: Decimal = Decimal('0.00')  # Confirmed available balance
    pending_balance: Decimal = Decimal('0.00')  # Funds being processed
    reserved_balance: Decimal = Decimal('0.00')  # Funds held for pending operations

    currency: Currency = Currency.GHS
    status: WalletStatus = WalletStatus.ACTIVE

    # Alerts
    low_balance_threshold: Decimal = Decimal('10.00')
    low_balance_alert_enabled: bool = True
    last_low_balance_alert_at: Optional[datetime] = None

    # Auto-reload settings (from core_backend)
    auto_reload_enabled: bool = False
    auto_reload_threshold: Decimal = Decimal('0.00')  # Trigger reload when balance drops below
    auto_reload_amount: Decimal = Decimal('0.00')  # Amount to reload
    auto_reload_payment_method_id: Optional[str] = None  # Payment method to use for auto-reload

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_transaction_at: Optional[datetime] = None

    @validator("balance", "pending_balance", "reserved_balance", "low_balance_threshold", "auto_reload_threshold", "auto_reload_amount")
    def balance_precision(cls, v):
        """Ensure 2 decimal places and non-negative."""
        if v < 0:
            raise ValueError("Balance cannot be negative")
        return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @property
    def available_balance(self) -> Decimal:
        """
        Balance available for transactions.

        Excludes reserved funds that are held for pending operations.
        """
        return self.balance - self.reserved_balance

    @property
    def total_balance(self) -> Decimal:
        """
        Total balance including pending funds.

        Includes funds that are being processed but not yet confirmed.
        """
        return self.balance + self.pending_balance

    @property
    def is_low_balance(self) -> bool:
        """Check if available balance is below threshold."""
        return self.available_balance < self.low_balance_threshold

    def dict(self, *args, **kwargs):
        """Convert to dict with proper JSON encoding."""
        d = super().dict(*args, **kwargs)
        # Convert Decimal to float for JSON serialization
        for key in ['balance', 'pending_balance', 'reserved_balance', 'low_balance_threshold', 'auto_reload_threshold', 'auto_reload_amount']:
            if isinstance(d.get(key), Decimal):
                d[key] = float(d[key])
        return d

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class Transaction(BaseModel):
    """
    Transaction model - unified from both implementations.

    Features:
    - Full balance reconciliation (before/after)
    - Processing fee tracking
    - Provider integration details
    - Idempotency support
    - Retry tracking
    - Failure tracking

    Example:
        transaction = Transaction(
            wallet_id="wallet123",
            user_id="user123",
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("50.00"),
            currency=Currency.GHS,
            processing_fee=Decimal("1.50"),
            total_amount=Decimal("51.50"),
            balance_before=Decimal("100.00"),
            balance_after=Decimal("150.00"),
            description="Wallet top-up"
        )
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wallet_id: str
    user_id: str  # Denormalized for easy querying
    tenant_id: Optional[str] = None

    # Transaction details
    transaction_type: TransactionType
    status: TransactionStatus = TransactionStatus.PENDING
    amount: Decimal
    currency: Currency

    # Fees (from core backend)
    processing_fee: Decimal = Decimal('0.00')
    total_amount: Decimal  # amount + processing_fee

    # Balance reconciliation (from shared library)
    balance_before: Decimal
    balance_after: Decimal

    # Payment details (from core backend)
    payment_method_id: Optional[str] = None
    payment_provider: Optional[PaymentProvider] = None
    provider_transaction_id: Optional[str] = None
    provider_response: Dict[str, Any] = Field(default_factory=dict)

    # Idempotency & references (from shared library)
    idempotency_key: Optional[str] = None  # For duplicate prevention
    reference: Optional[str] = None  # External reference
    description: str

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    # Failure tracking (from core backend)
    failure_reason: Optional[str] = None
    retry_count: int = 0  # New: track retries

    # Refund tracking (from shared library)
    refunded_from: Optional[str] = None  # Original transaction ID if this is a refund
    refund_amount: Optional[Decimal] = None  # Amount refunded

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("amount", "total_amount")
    def amount_positive(cls, v):
        """Ensure amount is positive."""
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @validator("processing_fee")
    def processing_fee_non_negative(cls, v):
        """Ensure processing_fee is non-negative (can be 0)."""
        if v < 0:
            raise ValueError("Processing fee cannot be negative")
        return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @validator("balance_before", "balance_after")
    def balance_precision(cls, v):
        """Ensure balance has 2 decimal places."""
        return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def dict(self, *args, **kwargs):
        """Convert to dict with proper JSON encoding."""
        d = super().dict(*args, **kwargs)
        # Convert Decimal to float for JSON serialization
        decimal_fields = ['amount', 'processing_fee', 'total_amount', 'balance_before', 'balance_after']
        if d.get('refund_amount'):
            decimal_fields.append('refund_amount')

        for key in decimal_fields:
            if isinstance(d.get(key), Decimal):
                d[key] = float(d[key])
        return d

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class PaymentMethod(BaseModel):
    """
    Payment method model (from core backend).

    Stores user's payment methods (cards, mobile money, bank accounts).

    Example:
        # Card
        method = PaymentMethod(
            user_id="user123",
            provider=PaymentProvider.STRIPE,
            method_type=PaymentMethodType.CARD,
            display_name="Visa •••• 4242",
            card_last4="4242",
            card_brand="visa"
        )

        # Mobile Money
        method = PaymentMethod(
            user_id="user123",
            provider=PaymentProvider.MTN_MOMO,
            method_type=PaymentMethodType.MOBILE_MONEY,
            display_name="MTN +233****3456",
            phone_number="+233201234567",
            phone_number_masked="+233****3456",
            network="MTN"
        )
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    tenant_id: Optional[str] = None

    # Provider details
    provider: PaymentProvider
    method_type: PaymentMethodType

    # Display info
    display_name: str  # e.g., "Visa •••• 4242" or "MTN +233****3456"
    nickname: Optional[str] = None  # User-defined nickname for this payment method

    # Provider IDs
    provider_payment_method_id: Optional[str] = None  # e.g., Stripe pm_xxx
    provider_customer_id: Optional[str] = None  # e.g., Stripe cus_xxx

    # Card-specific fields
    card_last4: Optional[str] = None
    card_brand: Optional[str] = None  # visa, mastercard, amex, etc.
    card_exp_month: Optional[int] = None
    card_exp_year: Optional[int] = None
    card_fingerprint: Optional[str] = None  # Unique card identifier

    # Mobile money-specific fields
    phone_number: Optional[str] = None
    phone_number_masked: Optional[str] = None  # +233****3456
    network: Optional[str] = None  # MTN, Vodafone, AirtelTigo

    # Bank account-specific fields
    bank_name: Optional[str] = None
    account_last4: Optional[str] = None
    account_holder_name: Optional[str] = None

    # Status
    is_active: bool = True
    is_default: bool = False
    is_verified: bool = False

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None

    @validator("phone_number_masked", pre=True, always=True)
    def mask_phone_number(cls, v, values):
        """Auto-generate masked phone number if not provided."""
        if v is None and 'phone_number' in values and values['phone_number']:
            phone = values['phone_number']
            if len(phone) > 8:
                # Mask middle digits: +233****3456
                return f"{phone[:4]}****{phone[-4:]}"
            return phone
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProviderConfig(BaseModel):
    """
    Payment provider configuration (from core backend).

    Stores provider credentials, webhook secrets, and fee configuration.

    Example:
        config = ProviderConfig(
            provider=PaymentProvider.STRIPE,
            secret_key="sk_live_xxx",
            webhook_secret="whsec_xxx",
            fee_config={
                "percent": 2.9,
                "fixed": 0.30,
                "currency": "USD",
                "cap": 10.00
            },
            is_active=True
        )
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: PaymentProvider

    # API credentials
    api_key: Optional[str] = None  # Public key for some providers
    secret_key: str  # Required - private API key
    webhook_secret: Optional[str] = None  # For webhook verification

    # URLs
    webhook_url: Optional[str] = None  # Our webhook endpoint
    redirect_url: Optional[str] = None  # User redirect after payment

    # Fee configuration (moved from hardcoded to database)
    fee_config: Dict[str, Any] = Field(default_factory=dict)
    # Example: {
    #     "percent": 2.9,    # Percentage fee
    #     "fixed": 0.30,     # Fixed fee amount
    #     "currency": "USD", # Fee currency
    #     "cap": 10.00       # Maximum fee (optional)
    # }

    # Settings
    is_active: bool = True
    is_test_mode: bool = False  # Sandbox vs production
    settings: Dict[str, Any] = Field(default_factory=dict)  # Provider-specific settings

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookEvent(BaseModel):
    """
    Webhook event log (from core backend).

    Stores all webhook events received from payment providers for audit trail.

    Example:
        event = WebhookEvent(
            provider=PaymentProvider.STRIPE,
            event_type="payment_intent.succeeded",
            event_id="evt_xxx",
            raw_payload={"type": "payment_intent.succeeded", ...},
            verification_signature="sig_xxx",
            is_verified=True
        )
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: PaymentProvider

    # Event details
    event_type: Optional[str] = None  # e.g., "payment_intent.succeeded"
    event_id: Optional[str] = None  # Provider's event ID
    raw_payload: Dict[str, Any]  # Full webhook payload
    headers: Dict[str, str] = Field(default_factory=dict)  # Request headers

    # Verification
    verification_signature: Optional[str] = None  # Signature from webhook
    is_verified: bool = False  # Whether signature was verified

    # Processing
    is_processed: bool = False  # Whether we've processed this webhook
    processing_attempts: int = 0  # Number of processing attempts
    processing_error: Optional[str] = None  # Error message if processing failed
    transaction_id: Optional[str] = None  # Linked transaction ID

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None  # For retry queue

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaymentInitiationResult(BaseModel):
    """
    Result of payment initiation.

    Returned by provider when initiating a payment.

    Example:
        result = PaymentInitiationResult(
            success=True,
            payment_url="https://checkout.stripe.com/...",
            reference="pi_xxx",
            amount=Decimal("50.00"),
            currency=Currency.USD,
            gateway=PaymentProvider.STRIPE,
            metadata={"client_secret": "pi_xxx_secret_xxx"}
        )
    """

    success: bool
    payment_url: Optional[str] = None  # URL for user to complete payment
    reference: str  # Provider's transaction reference
    amount: Decimal
    currency: Currency
    gateway: PaymentProvider
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None  # Error message if success=False

    def dict(self, *args, **kwargs):
        """Convert to dict with proper JSON encoding."""
        d = super().dict(*args, **kwargs)
        if isinstance(d.get('amount'), Decimal):
            d['amount'] = float(d['amount'])
        return d

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


# ============================================================================
# REQUEST/RESPONSE MODELS (For API validation)
# ============================================================================

class DepositRequest(BaseModel):
    """Request model for creating a deposit."""

    amount: Decimal
    currency: Currency = Currency.USD
    payment_method_id: str
    description: Optional[str] = "Wallet deposit"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("amount")
    def amount_positive(cls, v):
        """Ensure amount is positive."""
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class WithdrawalRequest(BaseModel):
    """Request model for creating a withdrawal."""

    amount: Decimal
    currency: Currency = Currency.USD
    payment_method_id: str
    description: Optional[str] = "Wallet withdrawal"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("amount")
    def amount_positive(cls, v):
        """Ensure amount is positive."""
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class RefundRequest(BaseModel):
    """Request model for refunding a transaction."""

    transaction_id: str
    amount: Optional[Decimal] = None  # None = full refund
    reason: str

    @validator("amount")
    def amount_positive(cls, v):
        """Ensure amount is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("Amount must be positive")
        if v is not None:
            return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return v


class WalletBalanceResponse(BaseModel):
    """Response model for wallet balance."""

    wallet_id: str
    balance: float
    pending_balance: float
    reserved_balance: float
    available_balance: float
    total_balance: float
    currency: str
    is_low_balance: bool
    low_balance_threshold: float
    last_transaction_at: Optional[str] = None


class TransactionResponse(BaseModel):
    """Response model for a single transaction."""

    id: str
    transaction_type: str
    status: str
    amount: float
    currency: str
    processing_fee: float
    total_amount: float
    description: str
    created_at: str
    completed_at: Optional[str] = None
    failed_at: Optional[str] = None
    failure_reason: Optional[str] = None
    payment_provider: Optional[str] = None


class TransactionListResponse(BaseModel):
    """Response model for transaction list."""

    transactions: List[TransactionResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class PaymentMethodResponse(BaseModel):
    """Response model for a payment method."""

    id: str
    provider: str
    method_type: str
    display_name: str
    is_default: bool
    is_verified: bool
    last_used_at: Optional[str] = None

    # Card details (if applicable)
    card_last4: Optional[str] = None
    card_brand: Optional[str] = None
    card_exp_month: Optional[int] = None
    card_exp_year: Optional[int] = None

    # Mobile money details (if applicable)
    phone_number_masked: Optional[str] = None
    network: Optional[str] = None


class PaymentMethodListResponse(BaseModel):
    """Response model for payment method list."""

    payment_methods: List[PaymentMethodResponse]
    default_method_id: Optional[str] = None
