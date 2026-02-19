"""
Invoice models for EstateFlow.

Handles invoice generation, payment tracking, and billing.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class InvoiceStatus(str, Enum):
    """Invoice status enumeration."""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Payment method enumeration."""
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    MOBILE_MONEY = "mobile_money"
    CHECK = "check"
    OTHER = "other"


class InvoiceLineItem(BaseModel):
    """Invoice line item."""
    description: str = Field(..., description="Item description")
    quantity: float = Field(default=1.0, description="Quantity")
    unit_price: float = Field(..., description="Unit price")
    amount: float = Field(default=0.0, description="Line total (quantity * unit_price, auto-calculated)")
    tax_rate: float = Field(default=0.0, description="Tax rate percentage")
    tax_amount: float = Field(default=0.0, description="Tax amount (auto-calculated)")


class Invoice(BaseModel):
    """
    Invoice model for database storage.

    Supports organization-specific invoice numbering, tax rates, and payment tracking.
    """

    id: str = Field(..., description="Invoice ID (UUID)")
    organization_id: str = Field(..., description="Organization ID")

    # Invoice Numbering
    invoice_number: str = Field(..., description="Invoice number (e.g., DIA-1001)")
    invoice_date: datetime = Field(default_factory=datetime.utcnow, description="Invoice date")
    due_date: datetime = Field(..., description="Payment due date")

    # Customer Information
    contact_id: str = Field(..., description="Contact/Customer ID")
    contact_name: str = Field(..., description="Customer name")
    contact_email: Optional[str] = Field(default="", description="Customer email")
    contact_phone: Optional[str] = Field(default="", description="Customer phone")
    contact_address: Optional[str] = Field(default="", description="Customer address")

    # Related Property (optional)
    property_id: Optional[str] = Field(default=None, description="Related property ID")
    property_name: Optional[str] = Field(default="", description="Property name")

    # Line Items
    line_items: List[InvoiceLineItem] = Field(..., description="Invoice line items")

    # Amounts
    subtotal: float = Field(..., description="Subtotal (before tax)")
    tax_amount: float = Field(..., description="Total tax amount")
    total_amount: float = Field(..., description="Total amount (including tax)")

    # Currency
    currency: str = Field(default="GHS", description="Invoice currency")

    # Payment
    status: InvoiceStatus = Field(default=InvoiceStatus.DRAFT, description="Invoice status")
    payment_method: Optional[PaymentMethod] = Field(default=None, description="Payment method")
    paid_date: Optional[datetime] = Field(default=None, description="Payment date")
    paid_amount: float = Field(default=0.0, description="Amount paid")

    # Notes
    notes: Optional[str] = Field(default="", description="Internal notes")
    terms: Optional[str] = Field(default="", description="Terms and conditions")

    # Metadata
    created_by: str = Field(..., description="User ID who created invoice")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = Field(default=None, description="Date sent to customer")

    # Soft delete
    is_deleted: bool = Field(default=False, description="Soft delete flag")
    deleted_at: Optional[datetime] = Field(default=None, description="Deletion timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "inv_123abc",
                "organization_id": "org_456def",
                "invoice_number": "DIA-1001",
                "invoice_date": "2025-01-15T10:00:00Z",
                "due_date": "2025-02-14T23:59:59Z",
                "contact_id": "contact_789ghi",
                "contact_name": "John Doe",
                "contact_email": "john@example.com",
                "contact_phone": "+233 XX XXX XXXX",
                "property_id": "prop_123",
                "property_name": "Luxury Apartment",
                "line_items": [
                    {
                        "description": "Monthly Rent - January 2025",
                        "quantity": 1.0,
                        "unit_price": 2500.00,
                        "amount": 2500.00,
                        "tax_rate": 12.5,
                        "tax_amount": 312.50
                    }
                ],
                "subtotal": 2500.00,
                "tax_amount": 312.50,
                "total_amount": 2812.50,
                "currency": "GHS",
                "status": "sent",
                "notes": "Thank you for your business!",
                "created_by": "user_123",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z"
            }
        }


class InvoiceCreate(BaseModel):
    """Request model for creating an invoice."""

    contact_id: str = Field(..., description="Contact/Customer ID")
    property_id: Optional[str] = Field(default=None, description="Related property ID")
    due_date: datetime = Field(..., description="Payment due date")
    line_items: List[InvoiceLineItem] = Field(..., min_length=1, description="Invoice line items")
    currency: str = Field(default="GHS", description="Invoice currency")
    notes: Optional[str] = Field(default="", description="Internal notes")
    terms: Optional[str] = Field(default="", description="Terms and conditions")


class InvoiceUpdate(BaseModel):
    """Request model for updating an invoice."""

    due_date: Optional[datetime] = Field(default=None, description="Payment due date")
    line_items: Optional[List[InvoiceLineItem]] = Field(default=None, description="Invoice line items")
    notes: Optional[str] = Field(default=None, description="Internal notes")
    terms: Optional[str] = Field(default=None, description="Terms and conditions")
    status: Optional[InvoiceStatus] = Field(default=None, description="Invoice status")


class InvoiceMarkPaid(BaseModel):
    """Request model for marking invoice as paid."""

    payment_method: PaymentMethod = Field(..., description="Payment method used")
    paid_amount: float = Field(..., description="Amount paid")
    paid_date: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Payment date")
    notes: Optional[str] = Field(default="", description="Payment notes")


class InvoiceFilters(BaseModel):
    """Filters for listing invoices."""

    status: Optional[List[InvoiceStatus]] = Field(default=None, description="Filter by status")
    contact_id: Optional[str] = Field(default=None, description="Filter by contact")
    property_id: Optional[str] = Field(default=None, description="Filter by property")
    from_date: Optional[datetime] = Field(default=None, description="Filter by date range (start)")
    to_date: Optional[datetime] = Field(default=None, description="Filter by date range (end)")
    min_amount: Optional[float] = Field(default=None, description="Minimum total amount")
    max_amount: Optional[float] = Field(default=None, description="Maximum total amount")
    search: Optional[str] = Field(default=None, description="Search invoice number or contact name")

    # Pagination
    limit: int = Field(default=20, ge=1, le=100, description="Page size")
    offset: int = Field(default=0, ge=0, description="Page offset")

    # Sorting
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


class InvoiceListResponse(BaseModel):
    """Response model for invoice list."""

    invoices: List[Invoice] = Field(..., description="List of invoices")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Page offset")
    has_more: bool = Field(..., description="More results available")


class InvoiceStats(BaseModel):
    """Invoice statistics."""

    total_invoices: int = Field(..., description="Total number of invoices")
    total_revenue: float = Field(..., description="Total revenue (all paid invoices)")
    pending_amount: float = Field(..., description="Total pending amount")
    overdue_amount: float = Field(..., description="Total overdue amount")

    # Status counts
    draft_count: int = Field(default=0, description="Number of draft invoices")
    sent_count: int = Field(default=0, description="Number of sent invoices")
    paid_count: int = Field(default=0, description="Number of paid invoices")
    overdue_count: int = Field(default=0, description="Number of overdue invoices")

    # Currency
    currency: str = Field(default="GHS", description="Currency")

    # Time period
    period: Optional[str] = Field(default=None, description="Time period (e.g., 'this_month')")
