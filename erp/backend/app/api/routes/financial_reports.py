"""
Financial Reporting Routes.

Provides endpoints for generating financial reports including:
- Profit & Loss (P&L) Statements
- Balance Sheets
- Budget vs Actual comparisons
- Cash Flow Statements
"""

import logging
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from app.core.database import MongoDB
from app.models.finance import AccountType
from apps.shared.dependencies import require_organization_access

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class PLLineItem(BaseModel):
    """P&L statement line item."""
    account_id: str
    account_number: str
    account_name: str
    account_type: AccountType
    amount: float


class PLSection(BaseModel):
    """P&L statement section (revenue or expenses)."""
    section_name: str
    line_items: List[PLLineItem]
    total: float


class PLStatement(BaseModel):
    """Profit & Loss Statement."""
    organization_id: str
    period_start: date
    period_end: date
    currency: str = "USD"

    # Revenue section
    revenue: PLSection

    # Expense sections
    cost_of_goods_sold: PLSection
    operating_expenses: PLSection
    other_expenses: PLSection

    # Calculations
    gross_profit: float = Field(description="Revenue - COGS")
    operating_profit: float = Field(description="Gross Profit - Operating Expenses")
    net_profit: float = Field(description="Operating Profit - Other Expenses")

    # Metadata
    generated_at: datetime


class BalanceSheetSection(BaseModel):
    """Balance sheet section."""
    section_name: str
    line_items: List[PLLineItem]
    total: float


class BalanceSheet(BaseModel):
    """Balance Sheet."""
    organization_id: str
    as_of_date: date
    currency: str = "USD"

    # Assets
    current_assets: BalanceSheetSection
    fixed_assets: BalanceSheetSection
    other_assets: BalanceSheetSection
    total_assets: float

    # Liabilities
    current_liabilities: BalanceSheetSection
    long_term_liabilities: BalanceSheetSection
    total_liabilities: float

    # Equity
    equity: BalanceSheetSection
    total_equity: float

    # Validation
    balances: bool = Field(description="Assets = Liabilities + Equity")

    # Metadata
    generated_at: datetime


class BudgetVsActualLineItem(BaseModel):
    """Budget vs actual comparison line item."""
    account_id: str
    account_number: str
    account_name: str
    account_type: AccountType
    budgeted: float
    actual: float
    variance: float
    variance_percent: float


class BudgetVsActual(BaseModel):
    """Budget vs Actual comparison."""
    organization_id: str
    budget_id: str
    budget_name: str
    period_start: date
    period_end: date
    currency: str = "USD"

    # Revenue comparison
    revenue_items: List[BudgetVsActualLineItem]
    total_revenue_budgeted: float
    total_revenue_actual: float
    revenue_variance: float
    revenue_variance_percent: float

    # Expense comparison
    expense_items: List[BudgetVsActualLineItem]
    total_expense_budgeted: float
    total_expense_actual: float
    expense_variance: float
    expense_variance_percent: float

    # Profit comparison
    profit_budgeted: float
    profit_actual: float
    profit_variance: float
    profit_variance_percent: float

    # Metadata
    generated_at: datetime


# ============================================================================
# PROFIT & LOSS STATEMENT
# ============================================================================

@router.get("/reports/profit-loss", response_model=PLStatement)
async def generate_profit_loss_statement(
    period_start: date = Query(..., description="Start date of reporting period"),
    period_end: date = Query(..., description="End date of reporting period"),
    org_id: str = Depends(require_organization_access),
):
    """
    Generate Profit & Loss (Income) Statement.

    Aggregates revenue and expenses for a given period to calculate profit/loss.
    """
    db = MongoDB.get_database()

    # Query all active accounts
    accounts = await db.accounts.find({
        "organization_id": org_id,
        "is_active": True
    }).to_list(length=1000)

    # Create account lookup
    account_map = {acc["id"]: acc for acc in accounts}

    # Query all transactions in the period
    transactions = await db.transactions.find({
        "organization_id": org_id,
        "is_active": True,
        "transaction_date": {
            "$gte": period_start,
            "$lte": period_end
        }
    }).to_list(length=10000)

    # Aggregate by account
    account_balances = {}
    for txn in transactions:
        account_id = txn.get("account_id")
        if account_id not in account_balances:
            account_balances[account_id] = 0.0

        # Credit increases revenue/liability/equity, decreases assets/expenses
        # Debit increases assets/expenses, decreases revenue/liability/equity
        amount = txn.get("amount", 0)
        txn_type = txn.get("transaction_type")

        if account_id in account_map:
            acc_type = account_map[account_id].get("account_type")

            if acc_type == "revenue":
                # Revenue increases with credits
                account_balances[account_id] += amount if txn_type == "credit" else -amount
            elif acc_type == "expense":
                # Expenses increase with debits
                account_balances[account_id] += amount if txn_type == "debit" else -amount

    # Build line items
    revenue_items = []
    cogs_items = []
    opex_items = []
    other_expense_items = []

    for account_id, balance in account_balances.items():
        if account_id not in account_map:
            continue

        account = account_map[account_id]
        line_item = PLLineItem(
            account_id=account_id,
            account_number=account.get("account_number", ""),
            account_name=account.get("account_name", ""),
            account_type=account.get("account_type"),
            amount=balance
        )

        account_type = account.get("account_type")
        if account_type == "revenue":
            revenue_items.append(line_item)
        elif account_type == "expense":
            # Categorize expenses (simple logic - can be enhanced)
            account_name_lower = account.get("account_name", "").lower()
            if "cost of goods" in account_name_lower or "cogs" in account_name_lower:
                cogs_items.append(line_item)
            elif "operating" in account_name_lower or "opex" in account_name_lower:
                opex_items.append(line_item)
            else:
                other_expense_items.append(line_item)

    # Calculate totals
    total_revenue = sum(item.amount for item in revenue_items)
    total_cogs = sum(item.amount for item in cogs_items)
    total_opex = sum(item.amount for item in opex_items)
    total_other = sum(item.amount for item in other_expense_items)

    gross_profit = total_revenue - total_cogs
    operating_profit = gross_profit - total_opex
    net_profit = operating_profit - total_other

    # Build response
    return PLStatement(
        organization_id=org_id,
        period_start=period_start,
        period_end=period_end,
        revenue=PLSection(
            section_name="Revenue",
            line_items=revenue_items,
            total=total_revenue
        ),
        cost_of_goods_sold=PLSection(
            section_name="Cost of Goods Sold",
            line_items=cogs_items,
            total=total_cogs
        ),
        operating_expenses=PLSection(
            section_name="Operating Expenses",
            line_items=opex_items,
            total=total_opex
        ),
        other_expenses=PLSection(
            section_name="Other Expenses",
            line_items=other_expense_items,
            total=total_other
        ),
        gross_profit=gross_profit,
        operating_profit=operating_profit,
        net_profit=net_profit,
        generated_at=datetime.utcnow()
    )


# ============================================================================
# BALANCE SHEET
# ============================================================================

@router.get("/reports/balance-sheet", response_model=BalanceSheet)
async def generate_balance_sheet(
    as_of_date: date = Query(..., description="Balance sheet as of this date"),
    org_id: str = Depends(require_organization_access),
):
    """
    Generate Balance Sheet.

    Shows assets, liabilities, and equity as of a specific date.
    """
    db = MongoDB.get_database()

    # Query all active accounts
    accounts = await db.accounts.find({
        "organization_id": org_id,
        "is_active": True,
        "account_type": {"$in": ["asset", "liability", "equity"]}
    }).to_list(length=1000)

    # Create account lookup
    account_map = {acc["id"]: acc for acc in accounts}

    # Query all transactions up to the date
    transactions = await db.transactions.find({
        "organization_id": org_id,
        "is_active": True,
        "transaction_date": {"$lte": as_of_date}
    }).to_list(length=10000)

    # Aggregate by account
    account_balances = {}
    for txn in transactions:
        account_id = txn.get("account_id")
        if account_id not in account_balances:
            account_balances[account_id] = 0.0

        amount = txn.get("amount", 0)
        txn_type = txn.get("transaction_type")

        if account_id in account_map:
            acc_type = account_map[account_id].get("account_type")

            # Asset accounts increase with debits
            if acc_type == "asset":
                account_balances[account_id] += amount if txn_type == "debit" else -amount
            # Liability and equity increase with credits
            elif acc_type in ["liability", "equity"]:
                account_balances[account_id] += amount if txn_type == "credit" else -amount

    # Build line items
    current_asset_items = []
    fixed_asset_items = []
    other_asset_items = []
    current_liability_items = []
    longterm_liability_items = []
    equity_items = []

    for account_id, balance in account_balances.items():
        if account_id not in account_map:
            continue

        account = account_map[account_id]
        line_item = PLLineItem(
            account_id=account_id,
            account_number=account.get("account_number", ""),
            account_name=account.get("account_name", ""),
            account_type=account.get("account_type"),
            amount=balance
        )

        account_type = account.get("account_type")
        account_name_lower = account.get("account_name", "").lower()

        if account_type == "asset":
            if "current" in account_name_lower or "cash" in account_name_lower or "receivable" in account_name_lower:
                current_asset_items.append(line_item)
            elif "fixed" in account_name_lower or "equipment" in account_name_lower or "property" in account_name_lower:
                fixed_asset_items.append(line_item)
            else:
                other_asset_items.append(line_item)
        elif account_type == "liability":
            if "current" in account_name_lower or "payable" in account_name_lower:
                current_liability_items.append(line_item)
            else:
                longterm_liability_items.append(line_item)
        elif account_type == "equity":
            equity_items.append(line_item)

    # Calculate totals
    total_current_assets = sum(item.amount for item in current_asset_items)
    total_fixed_assets = sum(item.amount for item in fixed_asset_items)
    total_other_assets = sum(item.amount for item in other_asset_items)
    total_assets = total_current_assets + total_fixed_assets + total_other_assets

    total_current_liabilities = sum(item.amount for item in current_liability_items)
    total_longterm_liabilities = sum(item.amount for item in longterm_liability_items)
    total_liabilities = total_current_liabilities + total_longterm_liabilities

    total_equity = sum(item.amount for item in equity_items)

    # Check if balance sheet balances
    balances = abs(total_assets - (total_liabilities + total_equity)) < 0.01

    return BalanceSheet(
        organization_id=org_id,
        as_of_date=as_of_date,
        current_assets=BalanceSheetSection(
            section_name="Current Assets",
            line_items=current_asset_items,
            total=total_current_assets
        ),
        fixed_assets=BalanceSheetSection(
            section_name="Fixed Assets",
            line_items=fixed_asset_items,
            total=total_fixed_assets
        ),
        other_assets=BalanceSheetSection(
            section_name="Other Assets",
            line_items=other_asset_items,
            total=total_other_assets
        ),
        total_assets=total_assets,
        current_liabilities=BalanceSheetSection(
            section_name="Current Liabilities",
            line_items=current_liability_items,
            total=total_current_liabilities
        ),
        long_term_liabilities=BalanceSheetSection(
            section_name="Long-term Liabilities",
            line_items=longterm_liability_items,
            total=total_longterm_liabilities
        ),
        total_liabilities=total_liabilities,
        equity=BalanceSheetSection(
            section_name="Equity",
            line_items=equity_items,
            total=total_equity
        ),
        total_equity=total_equity,
        balances=balances,
        generated_at=datetime.utcnow()
    )


# ============================================================================
# BUDGET VS ACTUAL
# ============================================================================

@router.get("/reports/budget-vs-actual/{budget_id}", response_model=BudgetVsActual)
async def generate_budget_vs_actual(
    budget_id: str,
    org_id: str = Depends(require_organization_access),
):
    """
    Generate Budget vs Actual comparison report.

    Compares budgeted amounts against actual transactions for the budget period.
    """
    db = MongoDB.get_database()

    # Get budget
    budget = await db.budgets.find_one({
        "id": budget_id,
        "organization_id": org_id,
        "is_active": True
    })

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )

    period_start = budget.get("period_start")
    period_end = budget.get("period_end")

    # Query transactions in budget period
    transactions = await db.transactions.find({
        "organization_id": org_id,
        "is_active": True,
        "transaction_date": {
            "$gte": period_start,
            "$lte": period_end
        }
    }).to_list(length=10000)

    # Query accounts for account type lookup
    accounts = await db.accounts.find({
        "organization_id": org_id,
        "is_active": True
    }).to_list(length=1000)

    account_map = {acc["id"]: acc for acc in accounts}

    # Aggregate actual amounts by account
    actual_balances = {}
    for txn in transactions:
        account_id = txn.get("account_id")
        if account_id not in actual_balances:
            actual_balances[account_id] = 0.0

        amount = txn.get("amount", 0)
        txn_type = txn.get("transaction_type")

        if account_id in account_map:
            acc_type = account_map[account_id].get("account_type")

            if acc_type == "revenue":
                actual_balances[account_id] += amount if txn_type == "credit" else -amount
            elif acc_type == "expense":
                actual_balances[account_id] += amount if txn_type == "debit" else -amount

    # Build comparison line items
    revenue_items = []
    expense_items = []

    for budget_line in budget.get("line_items", []):
        account_id = budget_line.get("account_id")
        budgeted = budget_line.get("budgeted_amount", 0)
        actual = actual_balances.get(account_id, 0)
        variance = actual - budgeted
        variance_percent = (variance / budgeted * 100) if budgeted != 0 else 0

        item = BudgetVsActualLineItem(
            account_id=account_id,
            account_number=budget_line.get("account_number", ""),
            account_name=budget_line.get("account_name"),
            account_type=budget_line.get("account_type"),
            budgeted=budgeted,
            actual=actual,
            variance=variance,
            variance_percent=variance_percent
        )

        if budget_line.get("account_type") == "revenue":
            revenue_items.append(item)
        else:
            expense_items.append(item)

    # Calculate totals
    total_revenue_budgeted = sum(item.budgeted for item in revenue_items)
    total_revenue_actual = sum(item.actual for item in revenue_items)
    revenue_variance = total_revenue_actual - total_revenue_budgeted
    revenue_variance_percent = (revenue_variance / total_revenue_budgeted * 100) if total_revenue_budgeted != 0 else 0

    total_expense_budgeted = sum(item.budgeted for item in expense_items)
    total_expense_actual = sum(item.actual for item in expense_items)
    expense_variance = total_expense_actual - total_expense_budgeted
    expense_variance_percent = (expense_variance / total_expense_budgeted * 100) if total_expense_budgeted != 0 else 0

    profit_budgeted = total_revenue_budgeted - total_expense_budgeted
    profit_actual = total_revenue_actual - total_expense_actual
    profit_variance = profit_actual - profit_budgeted
    profit_variance_percent = (profit_variance / profit_budgeted * 100) if profit_budgeted != 0 else 0

    return BudgetVsActual(
        organization_id=org_id,
        budget_id=budget_id,
        budget_name=budget.get("name"),
        period_start=period_start,
        period_end=period_end,
        revenue_items=revenue_items,
        total_revenue_budgeted=total_revenue_budgeted,
        total_revenue_actual=total_revenue_actual,
        revenue_variance=revenue_variance,
        revenue_variance_percent=revenue_variance_percent,
        expense_items=expense_items,
        total_expense_budgeted=total_expense_budgeted,
        total_expense_actual=total_expense_actual,
        expense_variance=expense_variance,
        expense_variance_percent=expense_variance_percent,
        profit_budgeted=profit_budgeted,
        profit_actual=profit_actual,
        profit_variance=profit_variance,
        profit_variance_percent=profit_variance_percent,
        generated_at=datetime.utcnow()
    )
