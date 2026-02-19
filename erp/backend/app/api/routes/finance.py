"""Finance and Accounting Routes."""

import logging
import io
import os
import tempfile
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import Response, JSONResponse, FileResponse, StreamingResponse
from pathlib import Path

from app.core.database import MongoDB
from app.models.finance import (
    Account, AccountCreate,
    Transaction, TransactionCreate,
    Invoice, InvoiceCreate,
    Expense, ExpenseCreate,
    Budget, BudgetCreate,
    AccountType,
    RecurrenceFrequency,
)
from app.services.recurring_expense_service import get_recurring_expense_service
from app.services.audit_service import get_audit_service
from apps.shared.dependencies import require_organization_access, OrganizationScoped
from apps.shared.services.organization_service import get_organization_service
from apps.shared.services.pdf_extraction_service import (
    get_pdf_extraction_service,
    PDFExtractionError
)
from apps.shared.services.file_upload_service import (
    get_file_upload_service,
    FileUploadError,
    FileValidationError
)
from apps.shared.storage.hetzner_storage_box import get_storage, StorageProtocol
from app.services.pdf_service import get_pdf_service
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/user/permissions")
async def get_user_permissions(scope: OrganizationScoped = Depends()):
    """
    Get current user's permissions in the organization.

    Returns information about what the user can do:
    - is_admin: Can manage organization and all data
    - is_approver: Has dedicated approver role
    - can_approve: Can approve expenses (admin or approver)

    Returns:
        {
            "user_id": "...",
            "email": "...",
            "organization_id": "...",
            "is_admin": bool,
            "is_approver": bool,
            "can_approve": bool
        }
    """
    user_id = scope.user.get("id") or scope.user.get("sub")
    user_email = scope.user.get("email", "")

    # Check permissions
    is_admin = await scope.check_is_admin()
    is_approver = await scope.check_is_approver()
    can_approve = await scope.check_can_approve()

    return {
        "user_id": user_id,
        "email": user_email,
        "organization_id": scope.org_id,
        "is_admin": is_admin,
        "is_approver": is_approver,
        "can_approve": can_approve
    }


@router.post("/accounts", response_model=Account, status_code=status.HTTP_201_CREATED)
async def create_account(account_create: AccountCreate, scope: OrganizationScoped = Depends()):
    """Create a new account."""
    db = MongoDB.get_database()

    account_data = Account(
        **account_create.model_dump(),
        organization_id=scope.org_id
    )

    await db.accounts.insert_one(account_data.model_dump())
    return account_data


@router.get("/accounts", response_model=List[Account])
async def list_accounts(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=1000),
    search: Optional[str] = None,
    account_type: Optional[str] = None,
):
    """List all accounts (chart of accounts)."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Search
    if search:
        query["$or"] = [
            {"account_name": {"$regex": search, "$options": "i"}},
            {"account_number": {"$regex": search, "$options": "i"}},
        ]

    # Filter
    if account_type:
        query["account_type"] = account_type

    cursor = db.accounts.find(query).skip(skip).limit(limit).sort("account_number", 1)
    accounts = await cursor.to_list(length=limit)
    return [Account(**a) for a in accounts]


@router.get("/accounts/{account_id}", response_model=Account)
async def get_account(
    account_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get account by ID."""
    db = MongoDB.get_database()
    account = await db.accounts.find_one({"id": account_id, "organization_id": org_id})

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    return Account(**account)


@router.patch("/accounts/{account_id}", response_model=Account)
async def update_account(
    account_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """Update account."""
    db = MongoDB.get_database()

    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)

    result = await db.accounts.update_one(
        {"id": account_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    account = await db.accounts.find_one({"id": account_id})
    return Account(**account)


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete account."""
    db = MongoDB.get_database()

    result = await db.accounts.update_one(
        {"id": account_id, "organization_id": org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    return None


@router.post("/transactions", response_model=Transaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(transaction_create: TransactionCreate, scope: OrganizationScoped = Depends()):
    """Create a financial transaction."""
    from datetime import datetime, date

    db = MongoDB.get_database()

    transaction_data = Transaction(
        **transaction_create.model_dump(),
        organization_id=scope.org_id
    )

    # Convert date objects to datetime for MongoDB
    transaction_dict = transaction_data.model_dump()
    for key, value in transaction_dict.items():
        if isinstance(value, date) and not isinstance(value, datetime):
            transaction_dict[key] = datetime.combine(value, datetime.min.time())

    await db.transactions.insert_one(transaction_dict)
    return transaction_data


@router.get("/transactions", response_model=List[Transaction])
async def list_transactions(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    account_id: Optional[str] = None,
    transaction_type: Optional[str] = None,
):
    """List all transactions."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Search
    if search:
        query["$or"] = [
            {"description": {"$regex": search, "$options": "i"}},
            {"reference": {"$regex": search, "$options": "i"}},
        ]

    # Filters
    if account_id:
        query["account_id"] = account_id
    if transaction_type:
        query["transaction_type"] = transaction_type

    cursor = db.transactions.find(query).skip(skip).limit(limit).sort("transaction_date", -1)
    transactions = await cursor.to_list(length=limit)
    return [Transaction(**t) for t in transactions]


@router.get("/transactions/{transaction_id}", response_model=Transaction)
async def get_transaction(
    transaction_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get transaction by ID."""
    db = MongoDB.get_database()
    transaction = await db.transactions.find_one({"id": transaction_id, "organization_id": org_id})

    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    return Transaction(**transaction)


@router.patch("/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """Update transaction."""
    db = MongoDB.get_database()

    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)

    result = await db.transactions.update_one(
        {"id": transaction_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    transaction = await db.transactions.find_one({"id": transaction_id})
    return Transaction(**transaction)


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    scope: OrganizationScoped = Depends(),
):
    """Soft delete transaction with audit trail."""
    db = MongoDB.get_database()
    audit_service = get_audit_service()

    # Get the transaction data before deletion for audit
    transaction = await db.transactions.find_one({
        "id": transaction_id,
        "organization_id": scope.org_id
    })

    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    # Soft delete
    result = await db.transactions.update_one(
        {"id": transaction_id, "organization_id": scope.org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    # Create audit log
    user_id = scope.user.get("id") or scope.user.get("sub")
    user_email = scope.user.get("email")

    await audit_service.log_delete(
        resource_type="transaction",
        resource_id=transaction_id,
        user_id=user_id,
        organization_id=scope.org_id,
        deleted_data=transaction,
        user_email=user_email,
    )

    logger.info(f"Transaction {transaction_id} deleted by user {user_id}")

    return None


@router.post("/invoices", response_model=Invoice, status_code=status.HTTP_201_CREATED)
async def create_invoice(invoice_create: InvoiceCreate, scope: OrganizationScoped = Depends()):
    """
    Create an invoice.

    Automatically creates journal entries for double-entry bookkeeping:
    - DR Accounts Receivable
    - CR Revenue
    - CR Sales Tax Payable (if applicable)
    """
    from datetime import datetime, date
    from app.services.journal_entry_service import get_journal_entry_service

    db = MongoDB.get_database()

    # Map InvoiceCreate fields to Invoice model fields
    invoice_dict = invoice_create.model_dump()

    # Fix field name mismatch: issue_date → invoice_date
    if "issue_date" in invoice_dict:
        invoice_dict["invoice_date"] = invoice_dict.pop("issue_date")

    # Calculate balance_due if not provided
    if "balance_due" not in invoice_dict:
        total = invoice_dict.get("total_amount", 0.0)
        paid = invoice_dict.get("amount_paid", 0.0)
        invoice_dict["balance_due"] = total - paid

    # Calculate amount_paid if not provided
    if "amount_paid" not in invoice_dict:
        invoice_dict["amount_paid"] = 0.0

    # Add line_items if not provided
    if "line_items" not in invoice_dict:
        invoice_dict["line_items"] = []

    invoice_data = Invoice(
        **invoice_dict,
        organization_id=scope.org_id,
        created_by=scope.user.get("id") or scope.user.get("sub")
    )

    # Convert date objects to datetime for MongoDB
    invoice_dict = invoice_data.model_dump()
    for key, value in invoice_dict.items():
        if isinstance(value, date) and not isinstance(value, datetime):
            invoice_dict[key] = datetime.combine(value, datetime.min.time())

    await db.invoices.insert_one(invoice_dict)

    # Create journal entries automatically
    try:
        journal_service = get_journal_entry_service()
        transaction_ids = await journal_service.create_invoice_entries(
            invoice_data.id,
            scope.org_id
        )
        logger.info(
            f"Created {len(transaction_ids)} journal entries for invoice {invoice_data.id}"
        )
    except Exception as e:
        logger.error(f"Failed to create journal entries for invoice {invoice_data.id}: {e}")
        # Don't fail invoice creation if journal entries fail
        # They can be created manually or via reconciliation

    return invoice_data


@router.get("/invoices", response_model=List[Invoice])
async def list_invoices(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    customer_id: Optional[str] = None,
    status_filter: Optional[str] = None,
):
    """List all invoices."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Search
    if search:
        query["$or"] = [
            {"invoice_number": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    # Filters
    if customer_id:
        query["customer_id"] = customer_id
    if status_filter:
        query["status"] = status_filter

    cursor = db.invoices.find(query).skip(skip).limit(limit).sort("invoice_date", -1)
    invoices = await cursor.to_list(length=limit)
    return [Invoice(**i) for i in invoices]


@router.get("/invoices/{invoice_id}", response_model=Invoice)
async def get_invoice(
    invoice_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get invoice by ID."""
    db = MongoDB.get_database()
    invoice = await db.invoices.find_one({"id": invoice_id, "organization_id": org_id})

    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    return Invoice(**invoice)


@router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: str,
    scope: OrganizationScoped = Depends(),
):
    """
    Download invoice as PDF.

    Generates a professional, branded PDF invoice with the organization's logo,
    colors, and payment information.
    """
    db = MongoDB.get_database()

    # Get invoice
    invoice_data = await db.invoices.find_one({
        "id": invoice_id,
        "organization_id": scope.org_id,
        "is_active": True
    })

    if not invoice_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    invoice = Invoice(**invoice_data)

    # Get organization with branding
    org_service = get_organization_service()
    organization = await org_service.get_organization(scope.org_id)

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Get customer
    customer_data = await db.customers.find_one({
        "id": invoice.customer_id,
        "organization_id": scope.org_id
    })

    if not customer_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Generate PDF
    try:
        pdf_service = get_pdf_service()
        pdf_bytes = pdf_service.generate_invoice_pdf(
            invoice=invoice,
            organization=organization,
            customer=customer_data
        )

        # Return PDF as downloadable file
        filename = f"invoice-{invoice.invoice_number}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )


@router.patch("/invoices/{invoice_id}", response_model=Invoice)
async def update_invoice(
    invoice_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """Update invoice."""
    db = MongoDB.get_database()

    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)

    result = await db.invoices.update_one(
        {"id": invoice_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    invoice = await db.invoices.find_one({"id": invoice_id})
    return Invoice(**invoice)


@router.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: str,
    scope: OrganizationScoped = Depends(),
):
    """Soft delete invoice with audit trail."""
    db = MongoDB.get_database()
    audit_service = get_audit_service()

    # Get the invoice data before deletion for audit
    invoice = await db.invoices.find_one({
        "id": invoice_id,
        "organization_id": scope.org_id
    })

    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    # Soft delete
    result = await db.invoices.update_one(
        {"id": invoice_id, "organization_id": scope.org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    # Create audit log
    user_id = scope.user.get("id") or scope.user.get("sub")
    user_email = scope.user.get("email")

    await audit_service.log_delete(
        resource_type="invoice",
        resource_id=invoice_id,
        user_id=user_id,
        organization_id=scope.org_id,
        deleted_data=invoice,
        user_email=user_email,
    )

    logger.info(f"Invoice {invoice_id} deleted by user {user_id}")

    return None


@router.post("/expenses", response_model=Expense, status_code=status.HTTP_201_CREATED)
async def create_expense(expense_create: ExpenseCreate, scope: OrganizationScoped = Depends()):
    """Create an expense."""
    from datetime import datetime, date

    db = MongoDB.get_database()

    user_id = scope.user.get("id") or scope.user.get("sub")

    expense_data = Expense(
        **expense_create.model_dump(),
        organization_id=scope.org_id,
        created_by=user_id
    )

    # Convert date objects to datetime for MongoDB
    expense_dict = expense_data.model_dump()
    for key, value in expense_dict.items():
        if isinstance(value, date) and not isinstance(value, datetime):
            expense_dict[key] = datetime.combine(value, datetime.min.time())

    await db.expenses.insert_one(expense_dict)
    return expense_data


@router.get("/expenses")
async def list_expenses(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    category: Optional[str] = None,
    status_filter: Optional[str] = None,
):
    """List all expenses with pagination."""
    from typing import Dict, Any
    
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Search
    if search:
        query["$or"] = [
            {"merchant": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    # Filters
    if category:
        query["category"] = category
    if status_filter:
        query["status"] = status_filter

    # Get total count
    total = await db.expenses.count_documents(query)

    # Get paginated results
    cursor = db.expenses.find(query).skip(skip).limit(limit).sort("expense_date", -1)
    expenses = await cursor.to_list(length=limit)
    
    return {
        "items": [Expense(**e).model_dump() for e in expenses],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/expenses/{expense_id}", response_model=Expense)
async def get_expense(
    expense_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get expense by ID."""
    db = MongoDB.get_database()
    expense = await db.expenses.find_one({"id": expense_id, "organization_id": org_id})

    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    return Expense(**expense)


@router.patch("/expenses/{expense_id}", response_model=Expense)
async def update_expense(
    expense_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """Update expense."""
    db = MongoDB.get_database()

    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)

    result = await db.expenses.update_one(
        {"id": expense_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    expense = await db.expenses.find_one({"id": expense_id})
    return Expense(**expense)


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: str,
    scope: OrganizationScoped = Depends(),
):
    """
    Soft delete expense and clean up all associated receipt files with audit trail.

    This endpoint:
    1. Retrieves the expense and its receipt files
    2. Deletes all receipt files from storage
    3. Soft-deletes the expense (sets is_active=False)
    4. Creates an audit log entry with the deleted data
    """
    db = MongoDB.get_database()
    audit_service = get_audit_service()

    # Get expense with receipts
    expense = await db.expenses.find_one({"id": expense_id, "organization_id": scope.org_id})

    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    # Delete all receipt files from storage
    receipt_urls = expense.get("receipt_urls", [])
    if receipt_urls:
        try:
            file_upload_service = await get_file_upload_service()
            for receipt_path in receipt_urls:
                try:
                    await file_upload_service.delete_file(receipt_path)
                    logger.info(f"Deleted receipt file: {receipt_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete receipt file {receipt_path}: {e}")
                    # Continue with other files even if one fails
        except Exception as e:
            logger.error(f"Error accessing file upload service: {e}")
            # Continue with soft delete even if file cleanup fails

    # Soft delete the expense
    result = await db.expenses.update_one(
        {"id": expense_id, "organization_id": scope.org_id},
        {"$set": {"is_active": False}}
    )

    # Create audit log
    user_id = scope.user.get("id") or scope.user.get("sub")
    user_email = scope.user.get("email")

    await audit_service.log_delete(
        resource_type="expense",
        resource_id=expense_id,
        user_id=user_id,
        organization_id=scope.org_id,
        deleted_data=expense,
        user_email=user_email,
    )

    logger.info(f"Expense {expense_id} deleted by user {user_id} with {len(receipt_urls)} receipt(s)")
    return None


@router.post("/expenses/{expense_id}/send-for-approval", response_model=Expense)
async def send_expense_for_approval(
    expense_id: str,
    scope: OrganizationScoped = Depends(),
):
    """
    Send expense for approval.

    Changes expense status to PENDING and notifies approvers.
    Users can send their own expenses for approval.

    Args:
        expense_id: ID of the expense to send for approval
        scope: Organization scope

    Returns:
        Updated expense object

    Raises:
        HTTPException: If expense not found or already approved
    """
    from datetime import datetime, date
    from app.models.finance import ExpenseStatus

    db = MongoDB.get_database()

    # Get expense
    expense = await db.expenses.find_one({"id": expense_id, "organization_id": scope.org_id})

    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    # Check if already approved
    if expense.get("status") == ExpenseStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expense is already approved"
        )

    # Check if already sent for approval
    if expense.get("status") == ExpenseStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expense is already pending approval"
        )

    # Update expense status to PENDING
    user_id = scope.user.get("id") or scope.user.get("sub")
    result = await db.expenses.update_one(
        {"id": expense_id},
        {
            "$set": {
                "status": ExpenseStatus.PENDING,
                "updated_by": user_id,
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    # TODO: Send notification to approver (alfred.anyan@gmail.com)
    # This will be implemented when notification system is added
    logger.info(f"Expense {expense_id} sent for approval by user {user_id}")

    # Get updated expense
    updated_expense = await db.expenses.find_one({"id": expense_id})
    return Expense(**updated_expense)


@router.post("/expenses/{expense_id}/approve", response_model=Expense)
async def approve_expense(
    expense_id: str,
    scope: OrganizationScoped = Depends(),
):
    """
    Approve an expense.

    Only users with APPROVER or ADMIN role can approve expenses.
    Users cannot approve their own expenses.

    Args:
        expense_id: ID of the expense to approve
        scope: Organization scope

    Returns:
        Updated expense object

    Raises:
        HTTPException: If user doesn't have permission, expense not found,
                      or user trying to approve their own expense
    """
    from datetime import datetime, date
    from app.models.finance import ExpenseStatus

    # Check if user has approver permissions
    await scope.require_approver()

    db = MongoDB.get_database()

    # Get expense
    expense = await db.expenses.find_one({"id": expense_id, "organization_id": scope.org_id})

    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    # Check if user is trying to approve their own expense
    user_id = scope.user.get("id") or scope.user.get("sub")
    created_by = expense.get("created_by")

    if created_by == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot approve your own expense"
        )

    # Check if already approved
    if expense.get("status") == ExpenseStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expense is already approved"
        )

    # Approve expense
    approval_date = datetime.utcnow().date()
    # For now, approver is always alfred.anyan@gmail.com
    approver_name = "alfred.anyan@gmail.com"
    result = await db.expenses.update_one(
        {"id": expense_id},
        {
            "$set": {
                "status": ExpenseStatus.APPROVED,
                "approved_by": user_id,
                "approver_name": approver_name,
                "approved_date": datetime.combine(approval_date, datetime.min.time()),
                "updated_by": user_id,
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    logger.info(f"Expense {expense_id} approved by user {user_id}")

    # Create journal entries automatically
    try:
        from app.services.journal_entry_service import get_journal_entry_service
        journal_service = get_journal_entry_service()
        transaction_ids = await journal_service.create_expense_entries(
            expense_id,
            scope.org_id
        )
        logger.info(
            f"Created {len(transaction_ids)} journal entries for expense {expense_id}"
        )
    except Exception as e:
        logger.error(f"Failed to create journal entries for expense {expense_id}: {e}")
        # Don't fail expense approval if journal entries fail
        # They can be created manually or via reconciliation

    # Get updated expense
    updated_expense = await db.expenses.find_one({"id": expense_id})
    return Expense(**updated_expense)


@router.post("/expenses/{expense_id}/reject", response_model=Expense)
async def reject_expense(
    expense_id: str,
    rejection_reason: str = Query(..., description="Reason for rejection"),
    scope: OrganizationScoped = Depends(),
):
    """
    Reject an expense.

    Only users with APPROVER or ADMIN role can reject expenses.
    Users cannot reject their own expenses.

    Args:
        expense_id: ID of the expense to reject
        rejection_reason: Reason for rejection
        scope: Organization scope

    Returns:
        Updated expense object

    Raises:
        HTTPException: If user doesn't have permission, expense not found,
                      or user trying to reject their own expense
    """
    from datetime import datetime, date
    from app.models.finance import ExpenseStatus

    # Check if user has approver permissions
    await scope.require_approver()

    db = MongoDB.get_database()

    # Get expense
    expense = await db.expenses.find_one({"id": expense_id, "organization_id": scope.org_id})

    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    # Check if user is trying to reject their own expense
    user_id = scope.user.get("id") or scope.user.get("sub")
    created_by = expense.get("created_by")

    if created_by == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot reject your own expense"
        )

    # Check if already rejected
    if expense.get("status") == ExpenseStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expense is already rejected"
        )

    # Reject expense
    # For now, approver is always alfred.anyan@gmail.com
    approver_name = "alfred.anyan@gmail.com"
    result = await db.expenses.update_one(
        {"id": expense_id},
        {
            "$set": {
                "status": ExpenseStatus.REJECTED,
                "rejection_reason": rejection_reason,
                "approved_by": user_id,  # Track who rejected it
                "approver_name": approver_name,
                "approved_date": None,  # Clear approval date
                "updated_by": user_id,
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    logger.info(f"Expense {expense_id} rejected by user {user_id}: {rejection_reason}")

    # Get updated expense
    updated_expense = await db.expenses.find_one({"id": expense_id})
    return Expense(**updated_expense)


@router.post("/expenses/{expense_id}/attach-receipt")
async def attach_receipt_to_expense(
    expense_id: str,
    file: UploadFile = File(...),
    scope: OrganizationScoped = Depends(),
):
    """
    Attach a receipt to an existing expense.

    This endpoint uploads a receipt file and attaches it to an existing expense.
    Useful for adding receipts after expense creation or from mobile devices.

    Args:
        expense_id: ID of the expense to attach receipt to
        file: Receipt file (PDF, JPEG, PNG, HEIC)
        scope: Organization scope

    Returns:
        {
            "success": True,
            "message": "Receipt attached successfully",
            "receipt_url": "path/to/receipt",
            "expense": { ... updated expense ... }
        }
    """
    db = MongoDB.get_database()

    # Check if expense exists
    expense = await db.expenses.find_one({"id": expense_id, "organization_id": scope.org_id})
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    try:
        # Validate file type
        file_ext = file.filename.lower().split('.')[-1]
        allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'heic', 'heif']

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_ext}. Supported: PDF, JPEG, PNG, HEIC"
            )

        # Read file content
        file_content = await file.read()

        # Upload file to storage
        file_upload_service = await get_file_upload_service()
        upload_info = await file_upload_service.upload_file(
            file=file_content,
            filename=file.filename,
            organization_id=scope.org_id,
            file_category="receipts",
            metadata={
                "expense_id": expense_id,
                "uploaded_by": scope.user.get("id") or scope.user.get("sub"),
                "uploaded_at": str(datetime.utcnow())
            }
        )

        # Store file metadata in MongoDB
        file_metadata = {
            "file_id": upload_info["file_id"],
            "filename": upload_info["filename"],
            "path": upload_info["path"],
            "remote_path": upload_info.get("path"),  # Path in Hetzner storage
            "url": upload_info.get("url"),
            "size": upload_info["size"],
            "mime_type": upload_info["mime_type"],
            "organization_id": scope.org_id,
            "category": "receipts",
            "storage_type": "hetzner" if not file_upload_service.use_local_storage else "local",
            "expense_id": expense_id,
            "uploaded_by": scope.user.get("id") or scope.user.get("sub"),
            "uploaded_at": datetime.utcnow(),
            "metadata": upload_info.get("metadata", {})
        }
        await db.erp_file_metadata.insert_one(file_metadata)

        # Add receipt URL to expense
        receipt_urls = expense.get("receipt_urls", [])
        receipt_urls.append(upload_info["path"])

        # Update expense
        await db.expenses.update_one(
            {"id": expense_id},
            {
                "$set": {
                    "receipt_urls": receipt_urls,
                    "updated_by": scope.user.get("id") or scope.user.get("sub")
                }
            }
        )

        logger.info(f"Receipt attached to expense {expense_id}: {upload_info['path']}")

        # Get updated expense
        updated_expense = await db.expenses.find_one({"id": expense_id})

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Receipt attached successfully",
                "receipt_url": upload_info["url"],
                "receipt_path": upload_info["path"],
                "expense": Expense(**updated_expense).model_dump(mode='json')
            }
        )

    except FileValidationError as e:
        logger.error(f"File validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileUploadError as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error attaching receipt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/expenses/{expense_id}/attach-receipts-bulk")
async def attach_receipts_bulk_to_expense(
    expense_id: str,
    files: List[UploadFile] = File(...),
    scope: OrganizationScoped = Depends(),
):
    """
    Attach multiple receipts to an existing expense in a single API call.

    This endpoint allows uploading multiple receipt files at once, which is more
    efficient than calling attach-receipt multiple times.

    Args:
        expense_id: ID of the expense to attach receipts to
        files: List of receipt files (PDF, JPEG, PNG, HEIC)
        scope: Organization scope

    Returns:
        {
            "success": True,
            "message": "3 receipts attached successfully",
            "receipts": [
                {
                    "filename": "receipt1.pdf",
                    "receipt_url": "https://...",
                    "receipt_path": "uploads/...",
                    "success": True
                },
                {
                    "filename": "receipt2.jpg",
                    "error": "File too large",
                    "success": False
                }
            ],
            "total_files": 3,
            "successful_uploads": 2,
            "failed_uploads": 1,
            "expense": { ... updated expense ... }
        }
    """
    db = MongoDB.get_database()

    # Check if expense exists
    expense = await db.expenses.find_one({"id": expense_id, "organization_id": scope.org_id})
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    # Validate that files were provided
    # FastAPI may pass files as a list or as a single item, handle both cases
    if files is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    # Ensure files is a list
    if not isinstance(files, list):
        files = [files]
    
    # Filter out None values
    files = [f for f in files if f is not None]
    
    if len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    logger.info(f"Processing {len(files)} files for expense {expense_id}")

    allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'heic', 'heif']
    uploaded_receipts = []
    successful_uploads = 0
    failed_uploads = 0
    new_receipt_urls = []

    # Get existing receipt URLs
    receipt_urls = expense.get("receipt_urls", [])

    # Process each file
    for file in files:
        result = {
            "filename": file.filename,
            "success": False
        }

        try:
            # Validate file type
            file_ext = file.filename.lower().split('.')[-1]

            if file_ext not in allowed_extensions:
                result["error"] = f"Unsupported file type: {file_ext}"
                failed_uploads += 1
                uploaded_receipts.append(result)
                continue

            # Read file content
            file_content = await file.read()

            # Check file size (10MB limit)
            if len(file_content) > 10 * 1024 * 1024:
                result["error"] = "File size exceeds 10MB limit"
                failed_uploads += 1
                uploaded_receipts.append(result)
                continue

            # Upload file to storage
            file_upload_service = await get_file_upload_service()
            upload_info = await file_upload_service.upload_file(
                file=file_content,
                filename=file.filename,
                organization_id=scope.org_id,
                file_category="receipts",
                metadata={
                    "expense_id": expense_id,
                    "uploaded_by": scope.user.get("id") or scope.user.get("sub"),
                    "uploaded_at": str(datetime.utcnow())
                }
            )

            # Store file metadata in MongoDB
            file_metadata = {
                "file_id": upload_info["file_id"],
                "filename": upload_info["filename"],
                "path": upload_info["path"],
                "remote_path": upload_info.get("path"),  # Path in Hetzner storage
                "url": upload_info.get("url"),
                "size": upload_info["size"],
                "mime_type": upload_info["mime_type"],
                "organization_id": scope.org_id,
                "category": "receipts",
                "storage_type": "hetzner" if not file_upload_service.use_local_storage else "local",
                "expense_id": expense_id,
                "uploaded_by": scope.user.get("id") or scope.user.get("sub"),
                "uploaded_at": datetime.utcnow(),
                "metadata": upload_info.get("metadata", {})
            }
            await db.erp_file_metadata.insert_one(file_metadata)

            # Add to new receipts list
            new_receipt_urls.append(upload_info["path"])

            # Mark as successful
            result["success"] = True
            result["receipt_url"] = upload_info["url"]
            result["receipt_path"] = upload_info["path"]
            successful_uploads += 1

            logger.info(f"Receipt uploaded for expense {expense_id}: {file.filename}")

        except FileValidationError as e:
            result["error"] = str(e)
            failed_uploads += 1
            logger.error(f"File validation error for {file.filename}: {str(e)}")
        except FileUploadError as e:
            result["error"] = f"Upload failed: {str(e)}"
            failed_uploads += 1
            logger.error(f"File upload error for {file.filename}: {str(e)}")
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            failed_uploads += 1
            logger.error(f"Unexpected error uploading {file.filename}: {str(e)}")

        uploaded_receipts.append(result)

    # Update expense with all successfully uploaded receipts
    if new_receipt_urls:
        receipt_urls.extend(new_receipt_urls)
        await db.expenses.update_one(
            {"id": expense_id},
            {
                "$set": {
                    "receipt_urls": receipt_urls,
                    "updated_by": scope.user.get("id") or scope.user.get("sub")
                }
            }
        )

    # Get updated expense
    updated_expense = await db.expenses.find_one({"id": expense_id})

    # Prepare response message
    total_files = len(files)
    if failed_uploads == 0:
        message = f"All {successful_uploads} receipt(s) attached successfully"
    elif successful_uploads == 0:
        message = f"Failed to attach all {total_files} receipt(s)"
    else:
        message = f"{successful_uploads} of {total_files} receipt(s) attached successfully"

    return JSONResponse(
        status_code=status.HTTP_200_OK if successful_uploads > 0 else status.HTTP_400_BAD_REQUEST,
        content={
            "success": successful_uploads > 0,
            "message": message,
            "receipts": uploaded_receipts,
            "total_files": total_files,
            "successful_uploads": successful_uploads,
            "failed_uploads": failed_uploads,
            "expense": Expense(**updated_expense).model_dump(mode='json')
        }
    )


@router.delete("/expenses/{expense_id}/receipts/{receipt_index}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense_receipt(
    expense_id: str,
    receipt_index: int,
    scope: OrganizationScoped = Depends(),
):
    """
    Delete a receipt from an expense.

    Args:
        expense_id: ID of the expense
        receipt_index: Index of receipt in the receipt_urls list
        scope: Organization scope
    """
    db = MongoDB.get_database()

    # Check if expense exists
    expense = await db.expenses.find_one({"id": expense_id, "organization_id": scope.org_id})
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    receipt_urls = expense.get("receipt_urls", [])

    if receipt_index < 0 or receipt_index >= len(receipt_urls):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")

    # Get receipt path to delete
    receipt_path = receipt_urls[receipt_index]

    # Delete from file storage
    try:
        file_upload_service = await get_file_upload_service()
        await file_upload_service.delete_file(receipt_path)
    except Exception as e:
        logger.warning(f"Failed to delete receipt file {receipt_path}: {e}")
        # Continue with database deletion even if file deletion fails

    # Remove from list
    receipt_urls.pop(receipt_index)

    # Update expense
    await db.expenses.update_one(
        {"id": expense_id},
        {
            "$set": {
                "receipt_urls": receipt_urls,
                "updated_by": scope.user.get("id") or scope.user.get("sub")
            }
        }
    )

    logger.info(f"Receipt deleted from expense {expense_id}")
    return None


@router.post("/expenses/upload-receipt", status_code=status.HTTP_200_OK)
async def upload_expense_receipt(
    file: UploadFile = File(...),
    extract_data: bool = Query(True, description="Extract expense data from receipt"),
    use_ai: bool = Query(False, description="Use AI (Gemini) for extraction (more accurate but costs ~$0.01)"),
    scope: OrganizationScoped = Depends(),
):
    """
    Upload an expense receipt (PDF or image) and optionally extract data.

    This endpoint supports both desktop and mobile workflows:
    - Desktop: Upload PDF receipts
    - Mobile: Capture photos of receipts (JPEG, PNG, HEIC)

    This endpoint:
    1. Uploads the receipt file to storage
    2. Optionally extracts expense data (merchant, date, amount, etc.)
    3. Returns the file URL and extracted data for auto-filling the expense form
    4. Frontend should show extracted data for USER CONFIRMATION before saving

    Extraction Methods:
    - Pattern matching (fast, free): Good for digital receipts and clear photos
    - AI extraction (Gemini): More accurate for all types, costs ~$0.01 per receipt

    Supported File Types:
    - PDF: Digital or scanned receipts
    - JPEG/PNG: Receipt photos from mobile devices
    - HEIC: iPhone photos (automatically converted)

    Args:
        file: Receipt file (PDF, JPEG, PNG, or HEIC)
        extract_data: Whether to extract expense data (default: True)
        use_ai: Use AI for extraction (default: False, uses pattern matching)
        scope: Organization scope dependency

    Returns:
        {
            "receipt_url": "https://storage.../path/to/receipt.jpg",
            "receipt_path": "uploads/org_abc/receipts/2025/11/...",
            "file_id": "20251103120000_a1b2c3d4",
            "file_type": "image/jpeg",  # or "application/pdf"
            "uploaded_at": "2025-11-03T12:00:00Z",
            "extracted_data": {
                "merchant": "Starbucks",
                "expense_date": "2025-11-03",  # Mapped to database field name
                "amount": 15.50,
                "tax_amount": 1.50,
                "currency": "USD",
                "category": "restaurant",
                "payment_method": "credit_card",
                "receipt_number": "ABC123",
                "confidence": 0.85,
                "extraction_method": "ai" or "pattern",
                "extraction_source": "image_ocr_ai" or "pdf_text"
            },
            "requires_confirmation": true  # Frontend should confirm before saving
        }

    Important:
        The extracted data is NOT automatically saved. Frontend must:
        1. Display extracted data to user
        2. Allow user to review/edit fields
        3. Show confidence score (warn if < 0.7)
        4. Get user confirmation
        5. Only then call POST /expenses to save
    """
    try:
        # Validate file type (PDF or images)
        file_ext = file.filename.lower().split('.')[-1]
        allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'heic', 'heif']

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_ext}. Supported types: PDF, JPEG, PNG, HEIC"
            )

        # Read file content
        file_content = await file.read()

        # Upload file to storage
        file_upload_service = await get_file_upload_service()
        upload_info = await file_upload_service.upload_file(
            file=file_content,
            filename=file.filename,
            organization_id=scope.org_id,
            file_category="receipts",
            metadata={
                "uploaded_by": scope.user.get("id") or scope.user.get("sub"),
                "uploaded_at": str(datetime.utcnow())
            }
        )

        logger.info(
            f"Receipt uploaded for organization {scope.org_id}: "
            f"{file.filename} -> {upload_info['url']}"
        )

        # Extract data if requested
        extracted_data = None
        extraction_method = None
        if extract_data:
            try:
                # Get PDF extraction service (handles both PDF and images)
                pdf_service = get_pdf_extraction_service(use_ocr=True)

                # Create BytesIO from content for extraction
                file_io = io.BytesIO(file_content)

                # Extract expense data using unified interface
                # This automatically detects file type (PDF vs image) and routes accordingly
                extraction_method = "ai" if use_ai else "pattern"
                logger.info(
                    f"Extracting data from {file.filename} using {extraction_method} method"
                )

                expense_data = await pdf_service.extract_from_file(
                    file_io,
                    filename=file.filename,
                    use_ai=use_ai,
                    llm_provider="gemini" if use_ai else None
                )

                # Convert to dict
                extracted_dict = expense_data.to_dict()

                # Map fields to database schema
                # Our database uses these field names:
                schema_mapping = {
                    "merchant": "Merchant/vendor name",
                    "expense_date": "Transaction date",
                    "amount": "Total amount",
                    "tax_amount": "Tax amount",
                    "currency": "Currency code",
                    "category": "Expense category",
                    "payment_method": "Payment method",
                    "receipt_number": "Receipt/invoice number",
                    "description": "Description/notes"
                }

                # Map extracted fields to match our database
                # Simple mapping first (rename "date" to "expense_date")
                if "date" in extracted_dict and extracted_dict["date"]:
                    extracted_dict["expense_date"] = extracted_dict.pop("date")

                # Add metadata
                extracted_dict["extraction_method"] = extraction_method
                extracted_dict["requires_review"] = extracted_dict.get("confidence", 0) < 0.7

                extracted_data = extracted_dict

                logger.info(
                    f"Extracted data from {file.filename}: "
                    f"merchant={expense_data.merchant}, "
                    f"amount={expense_data.amount}, "
                    f"confidence={expense_data.confidence}, "
                    f"method={extraction_method}"
                )

            except PDFExtractionError as e:
                logger.warning(f"PDF extraction failed for {file.filename}: {str(e)}")
                # Continue without extracted data - file is still uploaded
                extracted_data = {
                    "error": "Failed to extract data from PDF",
                    "message": str(e),
                    "confidence": 0.0,
                    "extraction_method": extraction_method or "failed",
                    "requires_review": True
                }
            except Exception as e:
                logger.error(f"Unexpected error during PDF extraction: {str(e)}")
                extracted_data = {
                    "error": "Unexpected extraction error",
                    "message": str(e),
                    "confidence": 0.0,
                    "extraction_method": extraction_method or "failed",
                    "requires_review": True
                }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "receipt_url": upload_info["url"],
                "receipt_path": upload_info["path"],
                "file_id": upload_info["file_id"],
                "file_type": upload_info.get("mime_type", "application/octet-stream"),
                "uploaded_at": upload_info["uploaded_at"],
                "extracted_data": extracted_data,
                "requires_confirmation": True,  # Always require user confirmation
                "extraction_method": extraction_method
            }
        )

    except FileValidationError as e:
        logger.error(f"File validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileUploadError as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during receipt upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


# ============================================================================
# BUDGETS
# ============================================================================

@router.post("/budgets", response_model=Budget, status_code=status.HTTP_201_CREATED)
async def create_budget(budget_create: BudgetCreate, scope: OrganizationScoped = Depends()):
    """Create a new budget."""
    from datetime import datetime, date

    db = MongoDB.get_database()

    # Calculate totals from line items
    total_revenue = sum(
        item.budgeted_amount for item in budget_create.line_items
        if item.account_type in [AccountType.REVENUE]
    )
    total_expense = sum(
        item.budgeted_amount for item in budget_create.line_items
        if item.account_type in [AccountType.EXPENSE]
    )

    # Create full Budget model with server-generated fields
    budget_data = Budget(
        **budget_create.model_dump(),
        organization_id=scope.org_id,
        total_revenue_budget=total_revenue,
        total_expense_budget=total_expense,
        total_profit_budget=total_revenue - total_expense
    )

    # Convert date objects to datetime for MongoDB
    budget_dict = budget_data.model_dump()
    for key, value in budget_dict.items():
        if isinstance(value, date) and not isinstance(value, datetime):
            budget_dict[key] = datetime.combine(value, datetime.min.time())

    await db.budgets.insert_one(budget_dict)
    return budget_data


@router.get("/budgets", response_model=List[Budget])
async def list_budgets(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    fiscal_year: Optional[int] = None,
    status_filter: Optional[str] = None,
):
    """List all budgets."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Filters
    if fiscal_year:
        query["fiscal_year"] = fiscal_year
    if status_filter:
        query["status"] = status_filter

    cursor = db.budgets.find(query).skip(skip).limit(limit).sort("period_start", -1)
    budgets = await cursor.to_list(length=limit)
    return [Budget(**b) for b in budgets]


@router.get("/budgets/{budget_id}", response_model=Budget)
async def get_budget(
    budget_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get budget by ID."""
    db = MongoDB.get_database()
    budget = await db.budgets.find_one({"id": budget_id, "organization_id": org_id})

    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    return Budget(**budget)


@router.patch("/budgets/{budget_id}", response_model=Budget)
async def update_budget(
    budget_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """Update budget."""
    db = MongoDB.get_database()

    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)

    # Recalculate totals if line_items updated
    if "line_items" in update_data:
        line_items = update_data["line_items"]
        total_revenue = sum(
            item.get("budgeted_amount", 0) for item in line_items
            if item.get("account_type") == "revenue"
        )
        total_expense = sum(
            item.get("budgeted_amount", 0) for item in line_items
            if item.get("account_type") == "expense"
        )

        update_data["total_revenue_budget"] = total_revenue
        update_data["total_expense_budget"] = total_expense
        update_data["total_profit_budget"] = total_revenue - total_expense

    result = await db.budgets.update_one(
        {"id": budget_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    budget = await db.budgets.find_one({"id": budget_id})
    return Budget(**budget)


@router.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete budget."""
    db = MongoDB.get_database()

    result = await db.budgets.update_one(
        {"id": budget_id, "organization_id": org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    return None


# ============================================================================
# RECURRING EXPENSES
# ============================================================================

@router.get("/recurring-expenses")
async def list_recurring_expenses(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True, description="Only return active recurring expenses"),
):
    """
    List all recurring expense templates.

    Returns recurring expense templates (not generated instances).
    Use the regular /expenses endpoint to see generated expense instances.

    Args:
        org_id: Organization ID
        skip: Pagination skip
        limit: Pagination limit
        active_only: Only return active recurring expenses

    Returns:
        List of recurring expense templates with total count
    """
    service = get_recurring_expense_service()
    recurring_expenses = await service.get_recurring_expenses(
        organization_id=org_id,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )

    # Get total count
    db = MongoDB.get_database()
    query = {
        "organization_id": org_id,
        "is_recurring": True,
    }
    if active_only:
        query["is_active"] = True

    total = await db.expenses.count_documents(query)

    return {
        "items": [Expense(**e).model_dump() for e in recurring_expenses],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/recurring-expenses", response_model=Expense, status_code=status.HTTP_201_CREATED)
async def create_recurring_expense(
    expense_create: ExpenseCreate,
    scope: OrganizationScoped = Depends(),
):
    """
    Create a new recurring expense template.

    This creates a recurring expense template that will automatically
    generate expense instances based on the specified frequency.

    Required fields for recurring expenses:
    - is_recurring: Must be True
    - recurrence_frequency: How often (daily, weekly, monthly, etc.)
    - recurrence_start_date: When to start generating expenses

    Optional fields:
    - recurrence_end_date: When to stop (null = indefinite)
    - recurrence_day_of_month: For monthly/quarterly/yearly (1-31)
    - recurrence_day_of_week: For weekly (0=Monday, 6=Sunday)
    - auto_approve: Automatically approve generated expenses
    - include_in_budget: Include in budget forecasting
    - budget_id: Link to a specific budget

    Args:
        expense_create: Expense creation data
        scope: Organization scope

    Returns:
        Created recurring expense template
    """
    if not expense_create.is_recurring:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="is_recurring must be True for recurring expenses. Use POST /expenses for one-time expenses."
        )

    if not expense_create.recurrence_frequency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="recurrence_frequency is required for recurring expenses"
        )

    db = MongoDB.get_database()
    user_id = scope.user.get("id") or scope.user.get("sub")

    # Calculate initial next_occurrence_date
    service = get_recurring_expense_service()
    start_date = expense_create.recurrence_start_date or date.today()

    expense_dict = expense_create.model_dump()

    # Set next occurrence to start date
    expense_dict["next_occurrence_date"] = start_date

    expense_data = Expense(
        **expense_dict,
        organization_id=scope.org_id,
        created_by=user_id,
    )

    # Convert date objects to datetime for MongoDB
    expense_dict = expense_data.model_dump()
    for key, value in expense_dict.items():
        if isinstance(value, date) and not isinstance(value, datetime):
            expense_dict[key] = datetime.combine(value, datetime.min.time())

    await db.expenses.insert_one(expense_dict)

    logger.info(
        f"Created recurring expense template: {expense_data.id} "
        f"with frequency {expense_create.recurrence_frequency}"
    )

    return expense_data


@router.get("/recurring-expenses/{expense_id}", response_model=Expense)
async def get_recurring_expense(
    expense_id: str,
    org_id: str = Depends(require_organization_access),
):
    """
    Get a recurring expense template by ID.

    Args:
        expense_id: Recurring expense ID
        org_id: Organization ID

    Returns:
        Recurring expense template
    """
    db = MongoDB.get_database()
    expense = await db.expenses.find_one({
        "id": expense_id,
        "organization_id": org_id,
        "is_recurring": True,
    })

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring expense not found"
        )

    return Expense(**expense)


@router.patch("/recurring-expenses/{expense_id}", response_model=Expense)
async def update_recurring_expense(
    expense_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """
    Update a recurring expense template.

    Changes will apply to future generated instances only.
    Already generated expenses are not affected.

    Args:
        expense_id: Recurring expense ID
        update_data: Fields to update
        scope: Organization scope

    Returns:
        Updated recurring expense template
    """
    db = MongoDB.get_database()

    # Verify it's a recurring expense
    existing = await db.expenses.find_one({
        "id": expense_id,
        "organization_id": scope.org_id,
        "is_recurring": True,
    })

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring expense not found"
        )

    # Remove protected fields
    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)
    update_data.pop("parent_recurring_id", None)  # Can't change parent

    # If frequency changes, recalculate next occurrence
    if "recurrence_frequency" in update_data or "recurrence_start_date" in update_data:
        service = get_recurring_expense_service()
        frequency = RecurrenceFrequency(
            update_data.get("recurrence_frequency") or existing.get("recurrence_frequency")
        )
        start_date = update_data.get("recurrence_start_date") or existing.get("recurrence_start_date")
        # Convert start_date to date object for comparison
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()

        # Recalculate from today or start date, whichever is later
        base_date = max(start_date or date.today(), date.today())
        update_data["next_occurrence_date"] = datetime.combine(base_date, datetime.min.time())

    # Convert dates
    for key, value in update_data.items():
        if isinstance(value, date) and not isinstance(value, datetime):
            update_data[key] = datetime.combine(value, datetime.min.time())

    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by"] = scope.user.get("id") or scope.user.get("sub")

    result = await db.expenses.update_one(
        {"id": expense_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring expense not found"
        )

    expense = await db.expenses.find_one({"id": expense_id})
    return Expense(**expense)


@router.post("/recurring-expenses/{expense_id}/pause", response_model=dict)
async def pause_recurring_expense(
    expense_id: str,
    scope: OrganizationScoped = Depends(),
):
    """
    Pause a recurring expense.

    Paused recurring expenses will not generate new instances until resumed.
    Existing generated expenses are not affected.

    Args:
        expense_id: Recurring expense ID
        scope: Organization scope

    Returns:
        Success message
    """
    service = get_recurring_expense_service()
    success = await service.pause_recurring_expense(
        expense_id=expense_id,
        organization_id=scope.org_id,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring expense not found"
        )

    logger.info(f"Paused recurring expense: {expense_id}")

    return {"message": "Recurring expense paused successfully"}


@router.post("/recurring-expenses/{expense_id}/resume", response_model=dict)
async def resume_recurring_expense(
    expense_id: str,
    resume_date: Optional[date] = Query(None, description="Date to resume from (default: today)"),
    scope: OrganizationScoped = Depends(),
):
    """
    Resume a paused recurring expense.

    Args:
        expense_id: Recurring expense ID
        resume_date: Optional date to resume from (default: today)
        scope: Organization scope

    Returns:
        Success message
    """
    service = get_recurring_expense_service()
    success = await service.resume_recurring_expense(
        expense_id=expense_id,
        organization_id=scope.org_id,
        resume_date=resume_date,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring expense not found"
        )

    logger.info(f"Resumed recurring expense: {expense_id}")

    return {"message": "Recurring expense resumed successfully"}


@router.delete("/recurring-expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring_expense(
    expense_id: str,
    delete_generated: bool = Query(False, description="Also delete all generated expense instances"),
    org_id: str = Depends(require_organization_access),
):
    """
    Delete a recurring expense template.

    By default, only the template is deleted. Generated expense instances
    are preserved for historical records.

    Args:
        expense_id: Recurring expense ID
        delete_generated: Also soft-delete generated instances
        org_id: Organization ID

    Returns:
        None
    """
    db = MongoDB.get_database()

    # Verify it's a recurring expense
    existing = await db.expenses.find_one({
        "id": expense_id,
        "organization_id": org_id,
        "is_recurring": True,
    })

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring expense not found"
        )

    # Soft delete the template
    result = await db.expenses.update_one(
        {"id": expense_id, "organization_id": org_id},
        {"$set": {"is_active": False, "is_recurring": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring expense not found"
        )

    # Optionally delete generated instances
    if delete_generated:
        await db.expenses.update_many(
            {
                "parent_recurring_id": expense_id,
                "organization_id": org_id,
            },
            {"$set": {"is_active": False}}
        )
        logger.info(f"Deleted recurring expense {expense_id} and its generated instances")
    else:
        logger.info(f"Deleted recurring expense {expense_id}")

    return None


@router.get("/recurring-expenses/{expense_id}/generated")
async def get_generated_expenses(
    expense_id: str,
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Get all expenses generated from a recurring expense template.

    Args:
        expense_id: Recurring expense template ID
        org_id: Organization ID
        skip: Pagination skip
        limit: Pagination limit

    Returns:
        List of generated expense instances
    """
    db = MongoDB.get_database()

    # Verify the template exists
    template = await db.expenses.find_one({
        "id": expense_id,
        "organization_id": org_id,
        "is_recurring": True,
    })

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring expense not found"
        )

    # Get generated instances
    query = {
        "parent_recurring_id": expense_id,
        "organization_id": org_id,
        "is_active": True,
    }

    total = await db.expenses.count_documents(query)
    cursor = db.expenses.find(query).skip(skip).limit(limit).sort("expense_date", -1)
    expenses = await cursor.to_list(length=limit)

    return {
        "items": [Expense(**e).model_dump() for e in expenses],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/recurring-expenses/process", response_model=dict)
async def process_recurring_expenses(
    target_date: Optional[date] = Query(None, description="Process for specific date (default: today)"),
    scope: OrganizationScoped = Depends(),
):
    """
    Manually trigger processing of due recurring expenses.

    This endpoint is useful for testing or manual processing.
    In production, this should be called by a scheduler/cron job.

    Args:
        target_date: Optional target date (default: today)
        scope: Organization scope

    Returns:
        List of generated expense IDs
    """
    # Check if user is admin
    is_admin = await scope.check_is_admin()
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can manually process recurring expenses"
        )

    service = get_recurring_expense_service()
    generated_ids = await service.process_recurring_expenses(
        organization_id=scope.org_id,
        target_date=target_date,
    )

    return {
        "message": f"Processed recurring expenses, generated {len(generated_ids)} instances",
        "generated_expense_ids": generated_ids,
    }


@router.get("/budgets/{budget_id}/recurring-expenses")
async def get_budget_recurring_expenses(
    budget_id: str,
    org_id: str = Depends(require_organization_access),
):
    """
    Get all recurring expenses linked to a budget.

    This helps with budget planning by showing expected recurring costs.

    Args:
        budget_id: Budget ID
        org_id: Organization ID

    Returns:
        List of recurring expenses with budget totals
    """
    service = get_recurring_expense_service()

    # Get the budget to get period dates
    db = MongoDB.get_database()
    budget = await db.budgets.find_one({
        "id": budget_id,
        "organization_id": org_id,
    })

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )

    # Get recurring expenses for this budget
    recurring_expenses = await service.get_budget_recurring_expenses(
        budget_id=budget_id,
        organization_id=org_id,
    )

    # Calculate totals for the budget period
    period_start = budget.get("period_start")
    period_end = budget.get("period_end")
    if isinstance(period_start, datetime):
        period_start = period_start.date()
    if isinstance(period_end, datetime):
        period_end = period_end.date()

    totals = await service.calculate_budget_recurring_total(
        budget_id=budget_id,
        organization_id=org_id,
        period_start=period_start,
        period_end=period_end,
    )

    return {
        "recurring_expenses": [Expense(**e).model_dump() for e in recurring_expenses],
        "projected_total": totals["total"],
        "by_category": totals["by_category"],
        "budget_period": {
            "start": str(period_start),
            "end": str(period_end),
        },
    }


@router.get("/recurring-expenses/unlinked")
async def get_unlinked_recurring_expenses(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Get all recurring expenses not linked to any budget.

    Useful for showing available recurring expenses when creating/editing a budget.

    Returns:
        List of recurring expenses without a budget_id
    """
    db = MongoDB.get_database()

    query = {
        "organization_id": org_id,
        "is_recurring": True,
        "is_active": True,
        "$or": [
            {"budget_id": None},
            {"budget_id": ""},
            {"budget_id": {"$exists": False}}
        ]
    }

    cursor = db.expenses.find(query).skip(skip).limit(limit).sort("created_at", -1)
    expenses = await cursor.to_list(length=limit)

    return [Expense(**e).model_dump() for e in expenses]


@router.post("/budgets/{budget_id}/recurring-expenses/{expense_id}")
async def link_recurring_expense_to_budget(
    budget_id: str,
    expense_id: str,
    org_id: str = Depends(require_organization_access),
):
    """
    Link a recurring expense to a budget.

    This associates the recurring expense with the budget for forecasting.

    Args:
        budget_id: Budget ID to link to
        expense_id: Recurring expense ID to link

    Returns:
        Updated expense
    """
    db = MongoDB.get_database()

    # Verify budget exists
    budget = await db.budgets.find_one({
        "id": budget_id,
        "organization_id": org_id,
        "is_active": True,
    })

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )

    # Verify expense exists and is recurring
    expense = await db.expenses.find_one({
        "id": expense_id,
        "organization_id": org_id,
        "is_recurring": True,
        "is_active": True,
    })

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring expense not found"
        )

    # Link the expense to the budget
    result = await db.expenses.update_one(
        {"id": expense_id, "organization_id": org_id},
        {
            "$set": {
                "budget_id": budget_id,
                "include_in_budget": True,
                "updated_at": datetime.utcnow(),
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to link expense to budget"
        )

    # Fetch updated expense
    updated_expense = await db.expenses.find_one({"id": expense_id})
    return Expense(**updated_expense).model_dump()


@router.delete("/budgets/{budget_id}/recurring-expenses/{expense_id}")
async def unlink_recurring_expense_from_budget(
    budget_id: str,
    expense_id: str,
    org_id: str = Depends(require_organization_access),
):
    """
    Unlink (remove) a recurring expense from a budget.

    This disassociates the recurring expense from the budget.
    The expense is not deleted, just unlinked.

    Args:
        budget_id: Budget ID
        expense_id: Recurring expense ID to unlink

    Returns:
        Success message
    """
    db = MongoDB.get_database()

    # Verify expense exists and is linked to this budget
    expense = await db.expenses.find_one({
        "id": expense_id,
        "organization_id": org_id,
        "budget_id": budget_id,
        "is_recurring": True,
        "is_active": True,
    })

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring expense not found or not linked to this budget"
        )

    # Unlink the expense from the budget
    result = await db.expenses.update_one(
        {"id": expense_id, "organization_id": org_id},
        {
            "$set": {
                "budget_id": None,
                "updated_at": datetime.utcnow(),
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to unlink expense from budget"
        )

    return {"message": "Recurring expense unlinked from budget"}


@router.patch("/budgets/{budget_id}/recurring-expenses/{expense_id}")
async def update_budget_recurring_expense(
    budget_id: str,
    expense_id: str,
    updates: dict,
    org_id: str = Depends(require_organization_access),
):
    """
    Update a recurring expense's budget-related settings.

    Allows updating amount, category, and other settings for budget forecasting.

    Args:
        budget_id: Budget ID
        expense_id: Recurring expense ID
        updates: Fields to update (amount, category, include_in_budget, etc.)

    Returns:
        Updated expense
    """
    db = MongoDB.get_database()

    # Verify expense exists and is linked to this budget
    expense = await db.expenses.find_one({
        "id": expense_id,
        "organization_id": org_id,
        "budget_id": budget_id,
        "is_recurring": True,
        "is_active": True,
    })

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring expense not found or not linked to this budget"
        )

    # Allowed fields to update for budget purposes
    allowed_fields = {
        "amount", "category", "merchant", "description",
        "include_in_budget", "recurrence_frequency",
    }

    update_data = {k: v for k, v in updates.items() if k in allowed_fields}

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )

    update_data["updated_at"] = datetime.utcnow()

    result = await db.expenses.update_one(
        {"id": expense_id, "organization_id": org_id},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update expense"
        )

    # Fetch updated expense
    updated_expense = await db.expenses.find_one({"id": expense_id})
    return Expense(**updated_expense).model_dump()


# ============================================================================
# AUDIT TRAIL
# ============================================================================

@router.get("/audit-trail")
async def get_audit_trail(
    resource_type: Optional[str] = Query(None, description="Filter by resource type (transaction, invoice, expense)"),
    action: Optional[str] = Query(None, description="Filter by action (create, update, delete)"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    org_id: str = Depends(require_organization_access),
):
    """
    Get audit trail for finance records.

    Returns a list of audit log entries for transactions, invoices, and expenses.

    Args:
        resource_type: Optional filter by type (transaction, invoice, expense)
        action: Optional filter by action (create, update, delete)
        start_date: Optional filter by date range start
        end_date: Optional filter by date range end
        skip: Pagination skip
        limit: Pagination limit
        org_id: Organization ID

    Returns:
        List of audit log entries with total count
    """
    from app.models.system import AuditLog, AuditLogAction

    db = MongoDB.get_database()

    # Build query
    query = {
        "organization_id": org_id,
        "resource_type": {"$in": ["transaction", "invoice", "expense"]},
    }

    if resource_type:
        query["resource_type"] = resource_type

    if action:
        query["action"] = action

    if start_date or end_date:
        query["created_at"] = {}
        if start_date:
            query["created_at"]["$gte"] = datetime.combine(start_date, datetime.min.time())
        if end_date:
            query["created_at"]["$lte"] = datetime.combine(end_date, datetime.max.time())

    # Get total count
    total = await db.audit_logs.count_documents(query)

    # Get audit logs
    cursor = db.audit_logs.find(query).skip(skip).limit(limit).sort("created_at", -1)
    audit_logs = await cursor.to_list(length=limit)

    # Convert to response format
    items = []
    for log in audit_logs:
        items.append({
            "id": log.get("id"),
            "action": log.get("action"),
            "resource_type": log.get("resource_type"),
            "resource_id": log.get("resource_id"),
            "user_id": log.get("user_id"),
            "user_email": log.get("user_email"),
            "changes": log.get("changes"),
            "created_at": log.get("created_at"),
            "success": log.get("success", True),
            "metadata": log.get("metadata", {}),
        })

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/audit-trail/{resource_type}/{resource_id}")
async def get_resource_audit_history(
    resource_type: str,
    resource_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    org_id: str = Depends(require_organization_access),
):
    """
    Get audit history for a specific resource.

    Args:
        resource_type: Type of resource (transaction, invoice, expense)
        resource_id: ID of the resource
        skip: Pagination skip
        limit: Pagination limit
        org_id: Organization ID

    Returns:
        List of audit log entries for the resource
    """
    if resource_type not in ["transaction", "invoice", "expense"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resource type. Must be: transaction, invoice, or expense"
        )

    audit_service = get_audit_service()
    history = await audit_service.get_resource_history(
        resource_type=resource_type,
        resource_id=resource_id,
        organization_id=org_id,
        skip=skip,
        limit=limit,
    )

    return {
        "items": history,
        "total": len(history),
        "resource_type": resource_type,
        "resource_id": resource_id,
    }


@router.get("/audit-trail/deleted")
async def get_deleted_records(
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[date] = Query(None, description="Filter by deletion date start"),
    end_date: Optional[date] = Query(None, description="Filter by deletion date end"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    org_id: str = Depends(require_organization_access),
):
    """
    Get all deleted finance records.

    Useful for viewing deletion history or potential data recovery.

    Args:
        resource_type: Optional filter by type (transaction, invoice, expense)
        start_date: Optional filter by deletion date start
        end_date: Optional filter by deletion date end
        skip: Pagination skip
        limit: Pagination limit
        org_id: Organization ID

    Returns:
        List of deleted records with original data
    """
    audit_service = get_audit_service()

    # If no specific resource type, get all financial records
    resource_types = [resource_type] if resource_type else ["transaction", "invoice", "expense"]

    all_deleted = []
    for rt in resource_types:
        deleted = await audit_service.get_deleted_resources(
            resource_type=rt,
            organization_id=org_id,
            start_date=datetime.combine(start_date, datetime.min.time()) if start_date else None,
            end_date=datetime.combine(end_date, datetime.max.time()) if end_date else None,
            skip=0,  # Get all for now, we'll paginate the combined list
            limit=1000,
        )
        all_deleted.extend(deleted)

    # Sort by created_at descending
    all_deleted.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)

    # Paginate
    paginated = all_deleted[skip:skip + limit]

    return {
        "items": paginated,
        "total": len(all_deleted),
        "skip": skip,
        "limit": limit,
    }


@router.get("/files/{file_path:path}")
async def get_file(
    file_path: str,
    scope: OrganizationScoped = Depends(),
):
    """
    Serve uploaded receipt files.

    This endpoint serves files that were uploaded via the file upload service.
    Files can be stored locally or in Hetzner cloud storage.

    Args:
        file_path: Relative path to file (e.g., "uploads/org_abc123/receipts/2025/11/file.pdf")
        scope: Organization scope (for access control)

    Returns:
        File response

    Raises:
        404: File not found
        403: Access denied (file doesn't belong to organization)
    """
    try:
        # Handle URL-encoded paths
        file_path = file_path.replace("%2F", "/").replace("%5C", "/")
        
        # If it's a full URL (cloud storage), redirect or handle differently
        if file_path.startswith("http://") or file_path.startswith("https://"):
            # For cloud storage URLs, we might need to proxy or redirect
            # For now, return 404 as we don't have direct access
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cloud storage files not directly accessible via this endpoint"
            )
        
        # Remove leading slash if present
        if file_path.startswith("/"):
            file_path = file_path[1:]
        
        # Check MongoDB for file metadata (if using Hetzner storage)
        db = MongoDB.get_database()
        # Remove "uploads/" prefix if present to get the actual path
        clean_path = file_path.replace("uploads/", "", 1) if file_path.startswith("uploads/") else file_path
        
        # Try to find file metadata in MongoDB
        file_metadata = await db.erp_file_metadata.find_one({
            "path": {"$in": [file_path, clean_path]},
            "organization_id": scope.org_id
        })
        
        # If file is in Hetzner storage, download it
        if file_metadata and file_metadata.get("storage_type") == "hetzner":
            try:
                storage = await get_storage(
                    protocol=StorageProtocol.WEBDAV,
                    base_path="kasaai/erp"
                )
                
                # Download from Hetzner to temp file
                remote_path = file_metadata.get("remote_path") or clean_path
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(clean_path).suffix)
                temp_path = temp_file.name
                temp_file.close()
                
                try:
                    await storage.download_file(
                        remote_path=remote_path,
                        local_path=temp_path,
                        overwrite=True
                    )
                    
                    # Verify organization access
                    if scope.org_id and file_metadata.get("organization_id") != scope.org_id:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Access denied: File does not belong to your organization"
                        )
                    
                    # Read file content and return as streaming response
                    # This allows us to delete the temp file immediately after reading
                    def generate():
                        try:
                            with open(temp_path, "rb") as f:
                                while True:
                                    chunk = f.read(8192)  # 8KB chunks
                                    if not chunk:
                                        break
                                    yield chunk
                        finally:
                            # Clean up temp file after streaming
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                    
                    filename = file_metadata.get("filename", Path(clean_path).name)
                    mime_type = file_metadata.get("mime_type", "application/octet-stream")
                    
                    return StreamingResponse(
                        generate(),
                        media_type=mime_type,
                        headers={
                            "Content-Disposition": f'inline; filename="{filename}"'
                        }
                    )
                except HTTPException:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise
                except Exception as e:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise
            except Exception as e:
                logger.error(f"Failed to download from Hetzner storage: {str(e)}")
                # Fall through to try local storage
        
        # Try local file system (for backward compatibility and local storage)
        backend_uploads = Path("/opt/kasaai/apps/erp/backend/uploads")
        
        # Remove "uploads/" prefix if present
        clean_path = file_path.replace("uploads/", "", 1) if file_path.startswith("uploads/") else file_path
        
        possible_paths = [
            # Backend uploads directory (most common location)
            backend_uploads / clean_path,
            # Absolute path from backend directory
            Path("/opt/kasaai/apps/erp/backend/uploads") / clean_path,
            # ERP uploads directory (from settings)
            Path(settings.UPLOAD_DIR) / file_path,
            Path(settings.UPLOAD_DIR) / clean_path,
            # Relative paths
            Path(file_path),
            Path(clean_path),
        ]
        
        full_path = None
        for path in possible_paths:
            try:
                resolved = path.resolve()
                if resolved.exists() and resolved.is_file():
                    # Security check: ensure file is within allowed directories
                    upload_dirs = [
                        Path(settings.UPLOAD_DIR).resolve(),
                        backend_uploads.resolve() if backend_uploads.exists() else None,
                        Path("/opt/kasaai/apps/erp/backend/uploads").resolve(),
                        Path("/opt/kasaai/apps/erp/uploads").resolve(),
                    ]
                    upload_dirs = [d for d in upload_dirs if d is not None]
                    
                    is_allowed = any(
                        str(resolved).startswith(str(upload_dir)) 
                        for upload_dir in upload_dirs 
                        if upload_dir.exists()
                    )
                    
                    if is_allowed:
                        full_path = resolved
                        break
            except Exception:
                continue
        
        if not full_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_path}"
            )
        
        # Verify organization access (file path should contain org_id)
        if scope.org_id and scope.org_id not in str(full_path):
            if scope.org_id not in file_path:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: File does not belong to your organization"
                )
        
        return FileResponse(full_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving file {file_path}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error serving file: {str(e)}"
        )
