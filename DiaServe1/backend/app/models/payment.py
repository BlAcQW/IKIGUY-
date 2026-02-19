"""
Payment models for EstateFlow.

Handles payment processing, tracking, and reconciliation with support for
multiple payment gateways (Stripe, Flutterwave) and payment methods
(cards, mobile money, bank transfers).
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PaymentGateway(str, Enum):
    """Payment gateway providers."""
    STRIPE = "stripe"
    FLUTTERWAVE = "flutterwave"
    MANUAL = "manual"  # For cash/check payments


class PaymentMethod(str, Enum):
    """Payment method types."""
    CARD = "card"
    MOBILE_MONEY = "mobile_money"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"
    CHECK = "check"


class MobileMoneyProvider(str, Enum):
    """Mobile money providers (Ghana focus)."""
    MTN_MOMO = "mtn_momo"
    VODAFONE_CASH = "vodafone_cash"
    AIRTELTIGO_MONEY = "airteltigo_money"


class PaymentStatus(str, Enum):
    """Payment processing status."""
    PENDING = "pending"  # Initiated but not processed
    PROCESSING = "processing"  # Being processed by gateway
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Payment failed
    CANCELLED = "cancelled"  # Cancelled by user or system
    REFUNDED = "refunded"  # Refunded to customer
    PARTIALLY_REFUNDED = "partially_refunded"  # Partial refund


class PaymentPurpose(str, Enum):
    """Purpose of payment."""
    RENT = "rent"
    SECURITY_DEPOSIT = "security_deposit"
    PURCHASE = "purchase"
    COMMISSION = "commission"
    SERVICE_FEE = "service_fee"
    BOOKING_FEE = "booking_fee"
    OTHER = "other"


class CardDetails(BaseModel):
    """Credit/debit card details (stored securely by gateway)."""
    last4: str = Field(..., description="Last 4 digits of card")
    brand: str = Field(..., description="Card brand (Visa, Mastercard, etc.)")
    exp_month: int = Field(..., description="Expiry month", ge=1, le=12)
    exp_year: int = Field(..., description="Expiry year")
    country: Optional[str] = Field(None, description="Card issuing country")


class MobileMoneyDetails(BaseModel):
    """Mobile money payment details."""
    provider: MobileMoneyProvider = Field(..., description="Mobile money provider")
    phone_number: str = Field(..., description="Phone number (masked)")
    account_name: Optional[str] = Field(None, description="Account holder name")


class BankTransferDetails(BaseModel):
    """Bank transfer payment details."""
    bank_name: Optional[str] = Field(None, description="Bank name")
    account_number_last4: Optional[str] = Field(None, description="Last 4 digits of account")
    reference_number: Optional[str] = Field(None, description="Transfer reference number")


class PaymentMetadata(BaseModel):
    """Additional payment metadata."""
    invoice_id: Optional[str] = Field(None, description="Related invoice ID")
    property_id: Optional[str] = Field(None, description="Related property ID")
    booking_id: Optional[str] = Field(None, description="Related booking ID")
    contract_id: Optional[str] = Field(None, description="Related contract ID")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")


class Payment(BaseModel):
    """
    Payment record.

    Tracks all payment transactions with support for multiple gateways
    and payment methods.
    """
    id: str = Field(..., description="Payment ID (UUID)")
    organization_id: str = Field(..., description="Organization ID")

    # Payment details
    amount: float = Field(..., description="Payment amount", gt=0)
    currency: str = Field(default="GHS", description="Currency code (GHS, USD, EUR)")
    description: str = Field(..., description="Payment description")
    purpose: PaymentPurpose = Field(..., description="Payment purpose")

    # Gateway information
    gateway: PaymentGateway = Field(..., description="Payment gateway used")
    payment_method: PaymentMethod = Field(..., description="Payment method")

    # Status tracking
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, description="Payment status")

    # Gateway references
    gateway_payment_id: Optional[str] = Field(None, description="Gateway payment/transaction ID")
    gateway_customer_id: Optional[str] = Field(None, description="Gateway customer ID")
    gateway_charge_id: Optional[str] = Field(None, description="Gateway charge ID")

    # Payment method details (only store what's safe)
    card_details: Optional[CardDetails] = Field(None, description="Card details (if card payment)")
    mobile_money_details: Optional[MobileMoneyDetails] = Field(None, description="Mobile money details")
    bank_transfer_details: Optional[BankTransferDetails] = Field(None, description="Bank transfer details")

    # Customer information
    customer_id: str = Field(..., description="Customer/contact ID")
    customer_name: str = Field(..., description="Customer name")
    customer_email: Optional[str] = Field(None, description="Customer email")
    customer_phone: Optional[str] = Field(None, description="Customer phone")

    # Related records
    metadata: PaymentMetadata = Field(default_factory=PaymentMetadata, description="Additional metadata")

    # Refund tracking
    refunded_amount: float = Field(default=0.0, description="Total refunded amount", ge=0)
    refund_reason: Optional[str] = Field(None, description="Refund reason")

    # Error tracking
    error_code: Optional[str] = Field(None, description="Error code if failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    # Fees
    platform_fee: float = Field(default=0.0, description="Platform fee amount", ge=0)
    gateway_fee: float = Field(default=0.0, description="Gateway processing fee", ge=0)
    net_amount: float = Field(..., description="Net amount after fees")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Created timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Updated timestamp")
    processed_at: Optional[datetime] = Field(None, description="When payment was processed")
    completed_at: Optional[datetime] = Field(None, description="When payment completed")
    failed_at: Optional[datetime] = Field(None, description="When payment failed")
    refunded_at: Optional[datetime] = Field(None, description="When refund processed")

    # Notes
    notes: Optional[str] = Field(None, description="Internal notes")

    # Soft delete
    is_deleted: bool = Field(default=False, description="Soft delete flag")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "pay_123abc",
                "organization_id": "org_456def",
                "amount": 2500.00,
                "currency": "GHS",
                "description": "Monthly rent payment for January 2025",
                "purpose": "rent",
                "gateway": "flutterwave",
                "payment_method": "mobile_money",
                "status": "completed",
                "gateway_payment_id": "flw_123456789",
                "mobile_money_details": {
                    "provider": "mtn_momo",
                    "phone_number": "***456",
                    "account_name": "John Doe"
                },
                "customer_id": "contact_789",
                "customer_name": "John Doe",
                "customer_email": "john@example.com",
                "customer_phone": "+233244123456",
                "metadata": {
                    "invoice_id": "inv_abc123",
                    "property_id": "prop_123"
                },
                "platform_fee": 25.00,
                "gateway_fee": 50.00,
                "net_amount": 2425.00,
                "created_at": "2025-01-15T10:00:00Z",
                "completed_at": "2025-01-15T10:01:30Z"
            }
        }


class PaymentIntent(BaseModel):
    """
    Payment intent for client-side payment initialization.

    Used to securely initialize payments on the frontend.
    """
    id: str = Field(..., description="Payment intent ID")
    amount: float = Field(..., description="Payment amount")
    currency: str = Field(..., description="Currency code")
    client_secret: Optional[str] = Field(None, description="Client secret for Stripe")
    gateway: PaymentGateway = Field(..., description="Payment gateway")
    status: str = Field(default="requires_payment_method", description="Intent status")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PaymentCreate(BaseModel):
    """Request model for creating a payment."""
    amount: float = Field(..., description="Payment amount", gt=0)
    currency: str = Field(default="GHS", description="Currency code")
    description: str = Field(..., description="Payment description")
    purpose: PaymentPurpose = Field(..., description="Payment purpose")

    gateway: PaymentGateway = Field(..., description="Payment gateway to use")
    payment_method: PaymentMethod = Field(..., description="Payment method")

    # Customer info (required if not linked to existing contact)
    customer_id: Optional[str] = Field(None, description="Existing customer/contact ID")
    customer_name: Optional[str] = Field(None, description="Customer name")
    customer_email: Optional[str] = Field(None, description="Customer email")
    customer_phone: Optional[str] = Field(None, description="Customer phone")

    # Metadata
    invoice_id: Optional[str] = Field(None, description="Related invoice ID")
    property_id: Optional[str] = Field(None, description="Related property ID")
    booking_id: Optional[str] = Field(None, description="Related booking ID")
    custom_metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")

    # Mobile money specific
    mobile_money_provider: Optional[MobileMoneyProvider] = Field(None, description="Mobile money provider")
    mobile_money_phone: Optional[str] = Field(None, description="Mobile money phone number")

    # Return URLs (for redirect-based payments)
    return_url: Optional[str] = Field(None, description="Success return URL")
    cancel_url: Optional[str] = Field(None, description="Cancel return URL")


class PaymentConfirm(BaseModel):
    """Confirm payment after client-side processing."""
    payment_intent_id: Optional[str] = Field(None, description="Payment intent ID from gateway")
    gateway_payment_id: Optional[str] = Field(None, description="Gateway payment ID")
    payment_method_details: Optional[Dict[str, Any]] = Field(None, description="Payment method details")


class PaymentRefund(BaseModel):
    """Request model for refunding a payment."""
    amount: Optional[float] = Field(None, description="Refund amount (full refund if not specified)", gt=0)
    reason: str = Field(..., description="Refund reason")
    notes: Optional[str] = Field(None, description="Internal notes")


class PaymentListFilters(BaseModel):
    """Filters for listing payments."""
    status: Optional[List[PaymentStatus]] = Field(None, description="Filter by status")
    gateway: Optional[List[PaymentGateway]] = Field(None, description="Filter by gateway")
    payment_method: Optional[List[PaymentMethod]] = Field(None, description="Filter by method")
    purpose: Optional[List[PaymentPurpose]] = Field(None, description="Filter by purpose")
    customer_id: Optional[str] = Field(None, description="Filter by customer")
    property_id: Optional[str] = Field(None, description="Filter by property")
    invoice_id: Optional[str] = Field(None, description="Filter by invoice")
    from_date: Optional[datetime] = Field(None, description="Date range start")
    to_date: Optional[datetime] = Field(None, description="Date range end")
    min_amount: Optional[float] = Field(None, description="Minimum amount")
    max_amount: Optional[float] = Field(None, description="Maximum amount")
    search: Optional[str] = Field(None, description="Search customer name or description")

    # Pagination
    limit: int = Field(default=20, ge=1, le=100, description="Page size")
    offset: int = Field(default=0, ge=0, description="Page offset")

    # Sorting
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


class PaymentListResponse(BaseModel):
    """Response model for payment list."""
    payments: List[Payment] = Field(..., description="List of payments")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Page offset")
    has_more: bool = Field(..., description="More results available")


class PaymentStats(BaseModel):
    """Payment statistics."""
    total_payments: int = Field(..., description="Total number of payments")
    total_revenue: float = Field(..., description="Total revenue (completed payments)")
    pending_amount: float = Field(..., description="Total pending amount")
    failed_amount: float = Field(..., description="Total failed payment attempts")
    refunded_amount: float = Field(..., description="Total refunded amount")

    # Status counts
    completed_count: int = Field(default=0, description="Completed payments")
    pending_count: int = Field(default=0, description="Pending payments")
    failed_count: int = Field(default=0, description="Failed payments")
    refunded_count: int = Field(default=0, description="Refunded payments")

    # By payment method
    card_revenue: float = Field(default=0.0, description="Revenue from card payments")
    mobile_money_revenue: float = Field(default=0.0, description="Revenue from mobile money")
    bank_transfer_revenue: float = Field(default=0.0, description="Revenue from bank transfers")
    cash_revenue: float = Field(default=0.0, description="Revenue from cash payments")

    # Currency
    currency: str = Field(default="GHS", description="Currency")

    # Time period
    period: Optional[str] = Field(None, description="Time period (e.g., 'this_month')")


class WebhookEvent(BaseModel):
    """Payment gateway webhook event."""
    id: str = Field(..., description="Event ID")
    gateway: PaymentGateway = Field(..., description="Gateway that sent the event")
    event_type: str = Field(..., description="Event type (e.g., payment.success)")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    signature: Optional[str] = Field(None, description="Webhook signature for verification")
    received_at: datetime = Field(default_factory=datetime.utcnow, description="When event was received")
    processed: bool = Field(default=False, description="Whether event was processed")
    processed_at: Optional[datetime] = Field(None, description="When event was processed")
