"""
Journal Entry Service.

Automated journal entry creation for double-entry bookkeeping.
Implements automatic GL postings from source documents (invoices, expenses, payroll, etc.).
"""

import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from bson import ObjectId

from app.core.database import MongoDB
from app.models.finance import (
    Transaction,
    TransactionType,
    AccountType,
    InvoiceStatus,
    ExpenseStatus
)

logger = logging.getLogger(__name__)


class JournalEntryService:
    """
    Automated journal entry creation from source documents.

    Implements double-entry bookkeeping rules:
    - Every transaction has equal debits and credits
    - Assets/Expenses increase with debits, decrease with credits
    - Liabilities/Equity/Revenue increase with credits, decrease with debits
    """

    def __init__(self):
        self.db = MongoDB.get_database()

    async def create_invoice_entries(
        self,
        invoice_id: str,
        organization_id: str
    ) -> List[str]:
        """
        Create journal entries when invoice is created.

        Double-entry:
        DR Accounts Receivable (Asset) - invoice.total_amount
        CR Revenue (Revenue) - invoice.subtotal
        CR Sales Tax Payable (Liability) - invoice.tax_amount

        Args:
            invoice_id: Invoice ID
            organization_id: Organization ID

        Returns:
            List of created transaction IDs

        Raises:
            ValueError: If invoice not found or invalid
        """
        # Get invoice
        invoice = await self.db.invoices.find_one({
            "id": invoice_id,
            "organization_id": organization_id
        })

        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        # Check if entries already created
        existing = await self.db.transactions.find_one({
            "reference_type": "invoice",
            "reference_id": invoice_id,
            "organization_id": organization_id,
            "is_active": True
        })

        if existing:
            logger.warning(f"Journal entries already exist for invoice {invoice_id}")
            return []

        # Get required GL accounts
        ar_account = await self._get_or_create_system_account(
            organization_id,
            "1200",
            "Accounts Receivable",
            AccountType.ASSET
        )

        revenue_account = await self._get_or_create_system_account(
            organization_id,
            "4000",
            "Sales Revenue",
            AccountType.REVENUE
        )

        sales_tax_account = await self._get_or_create_system_account(
            organization_id,
            "2100",
            "Sales Tax Payable",
            AccountType.LIABILITY
        )

        # Create transaction entries
        transaction_ids = []
        transaction_date = invoice.get("invoice_date", date.today())

        # DR Accounts Receivable
        ar_transaction = await self._create_transaction(
            organization_id=organization_id,
            account_id=ar_account["id"],
            transaction_type=TransactionType.DEBIT,
            amount=invoice["total_amount"],
            transaction_date=transaction_date,
            description=f"Invoice {invoice['invoice_number']} - {invoice.get('customer_id', 'Customer')}",
            reference_type="invoice",
            reference_id=invoice_id,
            reference_number=invoice["invoice_number"]
        )
        transaction_ids.append(ar_transaction)

        # CR Revenue
        revenue_transaction = await self._create_transaction(
            organization_id=organization_id,
            account_id=revenue_account["id"],
            transaction_type=TransactionType.CREDIT,
            amount=invoice["subtotal"],
            transaction_date=transaction_date,
            description=f"Invoice {invoice['invoice_number']} - Revenue",
            reference_type="invoice",
            reference_id=invoice_id,
            reference_number=invoice["invoice_number"]
        )
        transaction_ids.append(revenue_transaction)

        # CR Sales Tax Payable (if tax amount > 0)
        if invoice.get("tax_amount", 0) > 0:
            tax_transaction = await self._create_transaction(
                organization_id=organization_id,
                account_id=sales_tax_account["id"],
                transaction_type=TransactionType.CREDIT,
                amount=invoice["tax_amount"],
                transaction_date=transaction_date,
                description=f"Invoice {invoice['invoice_number']} - Sales Tax",
                reference_type="invoice",
                reference_id=invoice_id,
                reference_number=invoice["invoice_number"]
            )
            transaction_ids.append(tax_transaction)

        # Update account balances
        await self.update_account_balance(ar_account["id"], organization_id)
        await self.update_account_balance(revenue_account["id"], organization_id)
        if invoice.get("tax_amount", 0) > 0:
            await self.update_account_balance(sales_tax_account["id"], organization_id)

        logger.info(
            f"Created {len(transaction_ids)} journal entries for invoice {invoice_id}"
        )

        return transaction_ids

    async def create_expense_entries(
        self,
        expense_id: str,
        organization_id: str
    ) -> List[str]:
        """
        Create journal entries when expense is approved.

        Double-entry:
        DR Expense Account (Expense) - expense.amount
        CR Cash or Accounts Payable (Asset/Liability) - expense.amount

        If reimbursable:
        DR Expense Account
        CR Employee Reimbursement Payable

        Args:
            expense_id: Expense ID
            organization_id: Organization ID

        Returns:
            List of created transaction IDs
        """
        # Get expense
        expense = await self.db.expenses.find_one({
            "id": expense_id,
            "organization_id": organization_id
        })

        if not expense:
            raise ValueError(f"Expense {expense_id} not found")

        # Only create entries for approved expenses
        if expense.get("status") != ExpenseStatus.APPROVED.value:
            logger.warning(f"Expense {expense_id} not approved, skipping journal entries")
            return []

        # Check if entries already created
        existing = await self.db.transactions.find_one({
            "reference_type": "expense",
            "reference_id": expense_id,
            "organization_id": organization_id,
            "is_active": True
        })

        if existing:
            logger.warning(f"Journal entries already exist for expense {expense_id}")
            return []

        # Get expense account (use specified account or default)
        if expense.get("account_id"):
            expense_account = await self.db.accounts.find_one({
                "id": expense["account_id"],
                "organization_id": organization_id
            })
        else:
            # Default expense account
            expense_account = await self._get_or_create_system_account(
                organization_id,
                "6000",
                "General Expenses",
                AccountType.EXPENSE
            )

        # Determine credit account (Cash or AP or Employee Reimbursement)
        if expense.get("is_reimbursable", False):
            # Employee reimbursement
            credit_account = await self._get_or_create_system_account(
                organization_id,
                "2300",
                "Employee Reimbursement Payable",
                AccountType.LIABILITY
            )
        else:
            # Cash payment
            credit_account = await self._get_or_create_system_account(
                organization_id,
                "1000",
                "Cash",
                AccountType.ASSET
            )

        transaction_ids = []
        transaction_date = expense.get("expense_date", date.today())

        # DR Expense Account
        debit_transaction = await self._create_transaction(
            organization_id=organization_id,
            account_id=expense_account["id"],
            transaction_type=TransactionType.DEBIT,
            amount=expense["amount"],
            transaction_date=transaction_date,
            description=f"Expense - {expense.get('merchant', 'Unknown')} - {expense.get('category', 'General')}",
            reference_type="expense",
            reference_id=expense_id,
            reference_number=None
        )
        transaction_ids.append(debit_transaction)

        # CR Cash/AP/Employee Payable
        credit_transaction = await self._create_transaction(
            organization_id=organization_id,
            account_id=credit_account["id"],
            transaction_type=TransactionType.CREDIT,
            amount=expense["amount"],
            transaction_date=transaction_date,
            description=f"Expense payment - {expense.get('merchant', 'Unknown')}",
            reference_type="expense",
            reference_id=expense_id,
            reference_number=None
        )
        transaction_ids.append(credit_transaction)

        # Update account balances
        await self.update_account_balance(expense_account["id"], organization_id)
        await self.update_account_balance(credit_account["id"], organization_id)

        logger.info(
            f"Created {len(transaction_ids)} journal entries for expense {expense_id}"
        )

        return transaction_ids

    async def create_payment_entries(
        self,
        invoice_id: str,
        payment_amount: float,
        payment_date: date,
        organization_id: str,
        payment_method: Optional[str] = "cash"
    ) -> List[str]:
        """
        Create journal entries when payment is received on invoice.

        Double-entry:
        DR Cash (Asset) - payment.amount
        CR Accounts Receivable (Asset) - payment.amount

        Args:
            invoice_id: Invoice ID being paid
            payment_amount: Amount paid
            payment_date: Date of payment
            organization_id: Organization ID
            payment_method: Payment method (cash, check, wire, etc.)

        Returns:
            List of created transaction IDs
        """
        # Get invoice
        invoice = await self.db.invoices.find_one({
            "id": invoice_id,
            "organization_id": organization_id
        })

        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        # Get accounts
        cash_account = await self._get_or_create_system_account(
            organization_id,
            "1000",
            "Cash",
            AccountType.ASSET
        )

        ar_account = await self._get_or_create_system_account(
            organization_id,
            "1200",
            "Accounts Receivable",
            AccountType.ASSET
        )

        transaction_ids = []

        # DR Cash
        cash_transaction = await self._create_transaction(
            organization_id=organization_id,
            account_id=cash_account["id"],
            transaction_type=TransactionType.DEBIT,
            amount=payment_amount,
            transaction_date=payment_date,
            description=f"Payment received - Invoice {invoice['invoice_number']}",
            reference_type="payment",
            reference_id=invoice_id,
            reference_number=invoice["invoice_number"]
        )
        transaction_ids.append(cash_transaction)

        # CR Accounts Receivable
        ar_transaction = await self._create_transaction(
            organization_id=organization_id,
            account_id=ar_account["id"],
            transaction_type=TransactionType.CREDIT,
            amount=payment_amount,
            transaction_date=payment_date,
            description=f"Payment applied - Invoice {invoice['invoice_number']}",
            reference_type="payment",
            reference_id=invoice_id,
            reference_number=invoice["invoice_number"]
        )
        transaction_ids.append(ar_transaction)

        # Update account balances
        await self.update_account_balance(cash_account["id"], organization_id)
        await self.update_account_balance(ar_account["id"], organization_id)

        # Update invoice paid amount
        new_amount_paid = invoice.get("amount_paid", 0) + payment_amount
        new_balance_due = invoice["total_amount"] - new_amount_paid

        update_data = {
            "amount_paid": new_amount_paid,
            "balance_due": new_balance_due,
            "updated_at": datetime.utcnow()
        }

        # Update status if fully paid
        if new_balance_due <= 0:
            update_data["status"] = InvoiceStatus.PAID.value
            update_data["paid_date"] = datetime.utcnow()
        elif new_amount_paid > 0:
            update_data["status"] = InvoiceStatus.PARTIAL.value

        await self.db.invoices.update_one(
            {"id": invoice_id, "organization_id": organization_id},
            {"$set": update_data}
        )

        logger.info(
            f"Created {len(transaction_ids)} journal entries for payment on invoice {invoice_id}"
        )

        return transaction_ids

    async def update_account_balance(
        self,
        account_id: str,
        organization_id: str
    ) -> float:
        """
        Recalculate account balance from all transactions.

        For Asset/Expense accounts:
        Balance = sum(debits) - sum(credits)

        For Liability/Equity/Revenue accounts:
        Balance = sum(credits) - sum(debits)

        Args:
            account_id: Account ID
            organization_id: Organization ID

        Returns:
            New balance
        """
        # Get account
        account = await self.db.accounts.find_one({
            "id": account_id,
            "organization_id": organization_id
        })

        if not account:
            raise ValueError(f"Account {account_id} not found")

        # Get all transactions for this account
        transactions = await self.db.transactions.find({
            "account_id": account_id,
            "organization_id": organization_id,
            "is_active": True
        }).to_list(length=None)

        # Calculate debits and credits
        total_debits = sum(
            t["amount"] for t in transactions
            if t.get("transaction_type") == TransactionType.DEBIT.value
        )

        total_credits = sum(
            t["amount"] for t in transactions
            if t.get("transaction_type") == TransactionType.CREDIT.value
        )

        # Calculate balance based on account type
        account_type = account["account_type"]

        if account_type in [AccountType.ASSET.value, AccountType.EXPENSE.value]:
            # Assets and Expenses: Debits increase, Credits decrease
            new_balance = total_debits - total_credits
        else:
            # Liabilities, Equity, Revenue: Credits increase, Debits decrease
            new_balance = total_credits - total_debits

        # Update account balance
        await self.db.accounts.update_one(
            {"id": account_id, "organization_id": organization_id},
            {
                "$set": {
                    "balance": new_balance,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        logger.info(
            f"Updated account {account['account_name']} balance: "
            f"${new_balance:,.2f} (DR: ${total_debits:,.2f}, CR: ${total_credits:,.2f})"
        )

        return new_balance

    async def _create_transaction(
        self,
        organization_id: str,
        account_id: str,
        transaction_type: TransactionType,
        amount: float,
        transaction_date: date,
        description: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        reference_number: Optional[str] = None,
    ) -> str:
        """
        Create a transaction entry.

        Args:
            organization_id: Organization ID
            account_id: GL account ID
            transaction_type: DEBIT or CREDIT
            amount: Transaction amount
            transaction_date: Transaction date
            description: Description
            reference_type: Source document type (invoice, expense, etc.)
            reference_id: Source document ID
            reference_number: Document number

        Returns:
            Created transaction ID
        """
        transaction = Transaction(
            organization_id=organization_id,
            account_id=account_id,
            transaction_type=transaction_type,
            amount=amount,
            transaction_date=transaction_date,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
            reference_number=reference_number,
            currency="USD",
            is_reconciled=False
        )

        # Convert to dict for MongoDB
        transaction_dict = transaction.model_dump()

        # Convert date to datetime for MongoDB
        if isinstance(transaction_dict["transaction_date"], date):
            transaction_dict["transaction_date"] = datetime.combine(
                transaction_dict["transaction_date"],
                datetime.min.time()
            )

        await self.db.transactions.insert_one(transaction_dict)

        return transaction.id

    async def _get_or_create_system_account(
        self,
        organization_id: str,
        account_number: str,
        account_name: str,
        account_type: AccountType
    ) -> Dict:
        """
        Get existing system account or create if doesn't exist.

        Args:
            organization_id: Organization ID
            account_number: Account number
            account_name: Account name
            account_type: Account type

        Returns:
            Account document
        """
        # Try to find existing account
        account = await self.db.accounts.find_one({
            "organization_id": organization_id,
            "account_number": account_number,
            "is_active": True
        })

        if account:
            return account

        # Create new system account
        from app.models.finance import Account

        new_account = Account(
            organization_id=organization_id,
            account_number=account_number,
            account_name=account_name,
            account_type=account_type,
            description=f"System-generated {account_type.value} account",
            currency="USD",
            balance=0.0,
            is_system_account=True,
            tax_relevant=False
        )

        account_dict = new_account.model_dump()
        await self.db.accounts.insert_one(account_dict)

        logger.info(
            f"Created system account {account_number} - {account_name} for org {organization_id}"
        )

        return account_dict

    async def verify_double_entry(
        self,
        reference_type: str,
        reference_id: str,
        organization_id: str
    ) -> Tuple[bool, str]:
        """
        Verify that debits equal credits for a reference document.

        Args:
            reference_type: Document type (invoice, expense, etc.)
            reference_id: Document ID
            organization_id: Organization ID

        Returns:
            (is_valid, message)
        """
        # Get all transactions for this reference
        transactions = await self.db.transactions.find({
            "reference_type": reference_type,
            "reference_id": reference_id,
            "organization_id": organization_id,
            "is_active": True
        }).to_list(length=None)

        if not transactions:
            return False, f"No transactions found for {reference_type} {reference_id}"

        # Calculate totals
        total_debits = sum(
            t["amount"] for t in transactions
            if t.get("transaction_type") == TransactionType.DEBIT.value
        )

        total_credits = sum(
            t["amount"] for t in transactions
            if t.get("transaction_type") == TransactionType.CREDIT.value
        )

        # Check if balanced
        difference = abs(total_debits - total_credits)

        if difference < 0.01:  # Allow for tiny rounding errors
            return True, f"Balanced: DR ${total_debits:,.2f} = CR ${total_credits:,.2f}"
        else:
            return False, f"Unbalanced: DR ${total_debits:,.2f} ≠ CR ${total_credits:,.2f} (diff: ${difference:,.2f})"


# Singleton instance
_journal_entry_service = None


def get_journal_entry_service() -> JournalEntryService:
    """Get journal entry service singleton."""
    global _journal_entry_service
    if _journal_entry_service is None:
        _journal_entry_service = JournalEntryService()
    return _journal_entry_service
