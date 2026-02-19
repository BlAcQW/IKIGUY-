"""
Finance and Accounting Models.

Handles accounts, transactions, invoices, and expenses.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel as PydanticBaseModel, Field
from enum import Enum

from .base import BaseModel


class AccountType(str, Enum):
    """Account type enumeration."""

    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class TransactionType(str, Enum):
    """Transaction type enumeration."""

    DEBIT = "debit"
    CREDIT = "credit"


class InvoiceStatus(str, Enum):
    """Invoice status enumeration."""

    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class ExpenseStatus(str, Enum):
    """Expense status enumeration."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REIMBURSED = "reimbursed"
    PAID = "paid"


class RecurrenceFrequency(str, Enum):
    """Recurrence frequency enumeration for recurring expenses."""

    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class Account(BaseModel):
    """
    Chart of accounts model.

    Represents accounts in the general ledger.
    """

    account_number: str = Field(..., description="Unique account number")
    account_name: str = Field(..., description="Account name")
    account_type: AccountType = Field(..., description="Account type")
    parent_account_id: Optional[str] = Field(None, description="Parent account ID for sub-accounts")
    description: Optional[str] = Field(None, description="Account description")
    currency: str = Field(default="GHC", description="Currency code")
    balance: float = Field(default=0.0, description="Current balance")
    is_system_account: bool = Field(default=False, description="System-managed account")
    tax_relevant: bool = Field(default=False, description="Relevant for tax reporting")


class Transaction(BaseModel):
    """
    Financial transaction model.

    Double-entry bookkeeping transaction.
    """

    transaction_date: date = Field(..., description="Transaction date")
    account_id: str = Field(..., description="Account ID")
    transaction_type: TransactionType = Field(..., description="Debit or credit")
    amount: float = Field(..., description="Transaction amount")
    currency: str = Field(default="GHC", description="Currency code")

    # Reference
    reference_type: Optional[str] = Field(None, description="Reference type (invoice, expense, etc.)")
    reference_id: Optional[str] = Field(None, description="Reference entity ID")
    reference_number: Optional[str] = Field(None, description="Reference/check number")

    # Details
    description: str = Field(..., description="Transaction description")
    notes: Optional[str] = Field(None, description="Additional notes")

    # Reconciliation
    is_reconciled: bool = Field(default=False, description="Reconciliation status")
    reconciled_date: Optional[date] = Field(None, description="Date reconciled")

    # Attachments
    attachment_urls: List[str] = Field(default_factory=list, description="Supporting document URLs")


class InvoiceLineItem(BaseModel):
    """Invoice line item (embedded in Invoice)."""

    description: str = Field(..., description="Item description")
    quantity: float = Field(..., description="Quantity")
    unit_price: float = Field(..., description="Unit price")
    tax_rate: float = Field(default=0.0, description="Tax rate (percentage)")
    discount: float = Field(default=0.0, description="Discount amount")
    subtotal: float = Field(..., description="Line item subtotal")


class Invoice(BaseModel):
    """
    Invoice model.

    Tracks invoices to customers.
    """

    # Invoice details
    invoice_number: str = Field(..., description="Unique invoice number")
    customer_id: str = Field(..., description="Customer ID")
    invoice_date: date = Field(..., description="Invoice date")
    due_date: date = Field(..., description="Payment due date")
    status: InvoiceStatus = Field(default=InvoiceStatus.DRAFT)

    # Line items
    line_items: List[InvoiceLineItem] = Field(default_factory=list)

    # Amounts
    subtotal: float = Field(..., description="Subtotal (before tax)")
    tax_amount: float = Field(default=0.0, description="Total tax")
    discount_amount: float = Field(default=0.0, description="Total discount")
    total_amount: float = Field(..., description="Total amount due")
    amount_paid: float = Field(default=0.0, description="Amount paid")
    balance_due: float = Field(..., description="Outstanding balance")

    # Payment
    currency: str = Field(default="GHC", description="Currency code")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    payment_method: Optional[str] = Field(None, description="Payment method")

    # Dates
    sent_date: Optional[datetime] = Field(None, description="Date invoice was sent")
    paid_date: Optional[datetime] = Field(None, description="Date fully paid")

    # Notes
    notes: Optional[str] = Field(None, description="Internal notes")
    customer_notes: Optional[str] = Field(None, description="Notes visible to customer")

    # References
    purchase_order_number: Optional[str] = Field(None, description="Customer PO number")


class Expense(BaseModel):
    """
    Expense model.

    Tracks business expenses and reimbursements.
    """

    # Expense details
    expense_date: date = Field(..., description="Date expense was incurred")
    employee_id: Optional[str] = Field(None, description="Employee ID (for reimbursements)")
    category: str = Field(..., description="Expense category")
    merchant: str = Field(..., description="Merchant/vendor name")
    description: str = Field(..., description="Expense description")

    # Amount
    amount: float = Field(..., description="Expense amount")
    currency: str = Field(default="GHC", description="Currency code")
    tax_amount: float = Field(default=0.0, description="Tax amount")

    # Status
    status: ExpenseStatus = Field(default=ExpenseStatus.PENDING)
    approved_by: Optional[str] = Field(None, description="Approver user ID")
    approver_name: Optional[str] = Field(None, description="Approver name/email")
    approved_date: Optional[date] = Field(None, description="Approval date")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason")

    # Reimbursement
    is_reimbursable: bool = Field(default=True, description="Is reimbursable to employee")
    payable_to: Optional[str] = Field(None, description="Person/entity to reimburse (for expenses paid from personal accounts)")
    reimbursed: bool = Field(default=False, description="Has been reimbursed")
    reimbursement_date: Optional[date] = Field(None, description="Reimbursement date")

    # Account
    account_id: Optional[str] = Field(None, description="General ledger account ID")

    # Project
    project_id: Optional[str] = Field(None, description="Associated project ID")
    billable: bool = Field(default=False, description="Billable to customer")

    # Receipts
    receipt_urls: List[str] = Field(default_factory=list, description="Receipt/invoice URLs")
    notes: Optional[str] = Field(None, description="Notes")

    # Recurring expense fields
    is_recurring: bool = Field(default=False, description="Is this a recurring expense")
    recurrence_frequency: Optional[RecurrenceFrequency] = Field(None, description="How often the expense recurs")
    recurrence_start_date: Optional[date] = Field(None, description="When recurring expenses start")
    recurrence_end_date: Optional[date] = Field(None, description="When recurring expenses end (null = indefinite)")
    recurrence_day_of_month: Optional[int] = Field(None, ge=1, le=31, description="Day of month for monthly recurrence")
    recurrence_day_of_week: Optional[int] = Field(None, ge=0, le=6, description="Day of week (0=Monday) for weekly recurrence")
    parent_recurring_id: Optional[str] = Field(None, description="ID of the parent recurring expense template")
    next_occurrence_date: Optional[date] = Field(None, description="Next scheduled occurrence date")
    auto_approve: bool = Field(default=False, description="Auto-approve generated recurring expenses")
    include_in_budget: bool = Field(default=True, description="Include in budget calculations")
    budget_id: Optional[str] = Field(None, description="Associated budget for this recurring expense")


class BudgetPeriod(str, Enum):
    """Budget period enumeration."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class BudgetStatus(str, Enum):
    """Budget status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class BudgetLineItem(PydanticBaseModel):
    """Budget line item (embedded in Budget)."""

    account_id: str = Field(..., description="Account ID")
    account_name: str = Field(..., description="Account name for display")
    account_type: AccountType = Field(..., description="Account type")
    budgeted_amount: float = Field(..., description="Budgeted amount")
    notes: Optional[str] = Field(None, description="Notes for this line item")


class Budget(BaseModel):
    """
    Budget model.

    Tracks budgets with periods and account allocations.
    """

    # Budget details
    name: str = Field(..., description="Budget name")
    description: Optional[str] = Field(None, description="Budget description")
    fiscal_year: int = Field(..., description="Fiscal year (e.g., 2025)")

    # Period
    period: BudgetPeriod = Field(..., description="Budget period type")
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")

    # Status
    status: BudgetStatus = Field(default=BudgetStatus.DRAFT)

    # Line items
    line_items: List[BudgetLineItem] = Field(default_factory=list, description="Budget allocations by account")

    # Totals
    total_revenue_budget: float = Field(default=0.0, description="Total budgeted revenue")
    total_expense_budget: float = Field(default=0.0, description="Total budgeted expenses")
    total_profit_budget: float = Field(default=0.0, description="Budgeted profit (revenue - expenses)")

    # Currency
    currency: str = Field(default="GHC", description="Currency code")

    # Approval
    approved_by: Optional[str] = Field(None, description="Approver user ID")
    approved_date: Optional[date] = Field(None, description="Approval date")

    # Metadata
    notes: Optional[str] = Field(None, description="Budget notes")
    tags: List[str] = Field(default_factory=list, description="Budget tags for categorization")


class BudgetCreate(PydanticBaseModel):
    """
    Budget creation model (DTO for POST requests).

    Excludes server-generated fields like id, organization_id, timestamps.
    """

    # Budget details
    name: str = Field(..., description="Budget name")
    description: Optional[str] = Field(None, description="Budget description")
    fiscal_year: int = Field(..., description="Fiscal year (e.g., 2025)")

    # Period
    period: BudgetPeriod = Field(..., description="Budget period type")
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")

    # Status
    status: BudgetStatus = Field(default=BudgetStatus.DRAFT)

    # Line items
    line_items: List[BudgetLineItem] = Field(default_factory=list, description="Budget allocations by account")

    # Currency
    currency: str = Field(default="GHC", description="Currency code")

    # Approval (optional on create)
    approved_by: Optional[str] = Field(None, description="Approver user ID")
    approved_date: Optional[date] = Field(None, description="Approval date")

    # Metadata
    notes: Optional[str] = Field(None, description="Budget notes")
    tags: List[str] = Field(default_factory=list, description="Budget tags for categorization")


class AccountCreate(PydanticBaseModel):
    """Account creation DTO (excludes server-generated fields)."""

    account_number: str = Field(..., description="Unique account number")
    account_name: str = Field(..., description="Account name")
    account_type: AccountType = Field(..., description="Account type")
    parent_account_id: Optional[str] = Field(None, description="Parent account ID for sub-accounts")
    description: Optional[str] = Field(None, description="Account description")
    currency: str = Field(default="GHC", description="Currency code")
    balance: float = Field(default=0.0, description="Current balance")
    is_system_account: bool = Field(default=False, description="System-managed account")
    tax_relevant: bool = Field(default=False, description="Relevant for tax reporting")


class TransactionCreate(PydanticBaseModel):
    """Transaction creation DTO (excludes server-generated fields)."""

    transaction_date: date = Field(..., description="Transaction date")
    account_id: str = Field(..., description="Account ID")
    transaction_type: TransactionType = Field(..., description="Debit or credit")
    amount: float = Field(..., description="Transaction amount")
    currency: str = Field(default="GHC", description="Currency code")
    category: Optional[str] = Field(None, description="Transaction category")
    description: Optional[str] = Field(None, description="Transaction description")
    reference_number: Optional[str] = Field(None, description="Reference/check number")
    related_transaction_id: Optional[str] = Field(None, description="Related transaction ID for double-entry")


class InvoiceCreate(PydanticBaseModel):
    """Invoice creation DTO (excludes server-generated fields)."""

    invoice_number: str = Field(..., description="Unique invoice number")
    customer_id: str = Field(..., description="Customer organization ID")
    issue_date: date = Field(..., description="Invoice issue date")
    due_date: date = Field(..., description="Payment due date")
    status: InvoiceStatus = Field(default=InvoiceStatus.DRAFT)
    currency: str = Field(default="GHC", description="Currency code")
    subtotal: float = Field(default=0.0, description="Subtotal before tax")
    tax_amount: float = Field(default=0.0, description="Tax amount")
    total_amount: float = Field(..., description="Total amount due")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    payment_method: Optional[str] = Field(None, description="Payment method")
    sent_date: Optional[datetime] = Field(None, description="Date invoice was sent")
    paid_date: Optional[datetime] = Field(None, description="Date fully paid")
    notes: Optional[str] = Field(None, description="Internal notes")
    customer_notes: Optional[str] = Field(None, description="Notes visible to customer")
    purchase_order_number: Optional[str] = Field(None, description="Customer PO number")


class ExpenseCreate(PydanticBaseModel):
    """Expense creation DTO (excludes server-generated fields)."""

    expense_date: date = Field(..., description="Date expense was incurred")
    employee_id: Optional[str] = Field(None, description="Employee ID (for reimbursements)")
    category: str = Field(..., description="Expense category")
    merchant: str = Field(..., description="Merchant/vendor name")
    description: str = Field(..., description="Expense description")
    amount: float = Field(..., description="Expense amount")
    currency: str = Field(default="GHC", description="Currency code")
    tax_amount: float = Field(default=0.0, description="Tax amount")
    status: ExpenseStatus = Field(default=ExpenseStatus.PENDING)
    approved_by: Optional[str] = Field(None, description="Approver user ID")
    approver_name: Optional[str] = Field(None, description="Approver name/email")
    approved_date: Optional[date] = Field(None, description="Approval date")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason")
    is_reimbursable: bool = Field(default=True, description="Is reimbursable to employee")
    payable_to: Optional[str] = Field(None, description="Person/entity to reimburse (for expenses paid from personal accounts)")
    reimbursed: bool = Field(default=False, description="Has been reimbursed")
    reimbursement_date: Optional[date] = Field(None, description="Reimbursement date")
    account_id: Optional[str] = Field(None, description="General ledger account ID")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    billable: bool = Field(default=False, description="Billable to customer")
    receipt_urls: List[str] = Field(default_factory=list, description="Receipt/invoice URLs")
    notes: Optional[str] = Field(None, description="Notes")
    # Recurring expense fields
    is_recurring: bool = Field(default=False, description="Is this a recurring expense")
    recurrence_frequency: Optional[RecurrenceFrequency] = Field(None, description="How often the expense recurs")
    recurrence_start_date: Optional[date] = Field(None, description="When recurring expenses start")
    recurrence_end_date: Optional[date] = Field(None, description="When recurring expenses end (null = indefinite)")
    recurrence_day_of_month: Optional[int] = Field(None, ge=1, le=31, description="Day of month for monthly recurrence")
    recurrence_day_of_week: Optional[int] = Field(None, ge=0, le=6, description="Day of week (0=Monday) for weekly recurrence")
    auto_approve: bool = Field(default=False, description="Auto-approve generated recurring expenses")
    include_in_budget: bool = Field(default=True, description="Include in budget calculations")
    budget_id: Optional[str] = Field(None, description="Associated budget for this recurring expense")
