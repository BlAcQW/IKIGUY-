"""
Payment models for InkWave.

Handles saved cards and payment transactions.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class PaymentGateway(str, Enum):
    """Supported payment gateways."""

    EXPRESSPAY = "expresspay"
    PAYSTACK = "paystack"
    STRIPE = "stripe"
    MOMO = "momo"


class PaymentStatus(str, Enum):
    """Payment transaction status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class SavedCard(BaseModel):
    """Model for saved payment card."""

    id: Optional[str] = Field(None, description="Card ID (MongoDB ObjectId)")
    user_id: str = Field(..., description="User ID who owns the card")
    gateway: PaymentGateway = Field(..., description="Payment gateway")
    token: str = Field(..., description="Card token from gateway")
    last4: str = Field(..., description="Last 4 digits of card")
    card_type: Optional[str] = Field(None, description="Card type (Visa, Mastercard, etc)")
    expiry_month: str = Field(..., description="Expiry month (MM)")
    expiry_year: str = Field(..., description="Expiry year (YY)")
    is_default: bool = Field(default=False, description="Is default payment method")
    is_active: bool = Field(default=True, description="Card is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional card data")

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class PaymentTransaction(BaseModel):
    """Model for payment transaction."""

    id: Optional[str] = Field(None, description="Transaction ID (MongoDB ObjectId)")
    user_id: str = Field(..., description="User who made payment")
    order_id: str = Field(..., description="Unique order ID")
    gateway: PaymentGateway = Field(..., description="Payment gateway used")
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    amount: float = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="GHS", description="Currency code")

    # Payment details
    payment_reference: Optional[str] = Field(None, description="Gateway payment reference")
    transaction_id: Optional[str] = Field(None, description="Gateway transaction ID")
    payment_method: Optional[str] = Field(None, description="Payment method used")

    # Card details (if paid with saved card)
    saved_card_id: Optional[str] = Field(None, description="ID of saved card used")
    card_last4: Optional[str] = Field(None, description="Last 4 of card used")

    # Order details
    order_type: str = Field(..., description="Type of order (book_purchase, wallet_topup, etc)")
    order_desc: str = Field(..., description="Order description")
    order_items: Optional[list] = Field(default=None, description="Items in order")

    # Status tracking
    initiated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None, description="When payment completed")
    failed_at: Optional[datetime] = Field(None, description="When payment failed")

    # Additional data
    customer_email: Optional[str] = Field(None, description="Customer email")
    customer_name: Optional[str] = Field(None, description="Customer name")
    redirect_url: Optional[str] = Field(None, description="Return URL after payment")

    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional transaction data")

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}


# API Request/Response Schemas

class SaveCardRequest(BaseModel):
    """Request to save a new card."""

    card_number: str = Field(..., description="Card number")
    card_expiry_month: str = Field(..., pattern="^(0[1-9]|1[0-2])$", description="MM")
    card_expiry_year: str = Field(..., pattern="^[0-9]{2}$", description="YY")
    card_cvv: str = Field(..., pattern="^[0-9]{3,4}$", description="CVV")
    set_as_default: bool = Field(default=False, description="Set as default card")


class SavedCardResponse(BaseModel):
    """Response for saved card."""

    id: str
    last4: str
    card_type: Optional[str]
    expiry_month: str
    expiry_year: str
    is_default: bool
    created_at: str


class BookPurchaseRequest(BaseModel):
    """Request to purchase a book."""

    book_id: str = Field(..., description="Book ID to purchase")
    use_saved_card: bool = Field(default=False, description="Use saved card")
    saved_card_id: Optional[str] = Field(None, description="ID of saved card to use")
    save_card: bool = Field(default=False, description="Save card for future use")
    redirect_url: Optional[str] = Field(None, description="URL to redirect after payment")


class PaymentInitiateResponse(BaseModel):
    """Response when payment is initiated."""

    success: bool
    order_id: str
    payment_url: Optional[str] = Field(None, description="URL to complete payment")
    requires_redirect: bool = Field(default=True, description="Whether user needs to be redirected")
    transaction_id: Optional[str] = None
    message: Optional[str] = None


class PaymentVerifyResponse(BaseModel):
    """Response for payment verification."""

    success: bool
    paid: bool
    transaction_id: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    order_id: Optional[str] = None
    message: Optional[str] = None
