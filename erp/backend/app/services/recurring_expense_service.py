"""
Recurring Expense Service.

Handles creation and management of recurring expenses, including:
- Generating expense instances based on recurrence schedule
- Calculating next occurrence dates
- Linking recurring expenses to budgets
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from dateutil.relativedelta import relativedelta

from app.core.database import MongoDB
from app.models.finance import (
    Expense,
    ExpenseCreate,
    ExpenseStatus,
    RecurrenceFrequency,
)

logger = logging.getLogger(__name__)


class RecurringExpenseService:
    """
    Service for managing recurring expenses.

    This service handles:
    - Calculating next occurrence dates based on frequency
    - Generating expense instances from recurring templates
    - Linking expenses to budgets for forecasting
    - Tracking and updating recurrence state
    """

    def __init__(self):
        """Initialize the recurring expense service."""
        self._db = None

    @property
    def db(self):
        """Get database connection lazily."""
        if self._db is None:
            self._db = MongoDB.get_database()
        return self._db

    def calculate_next_occurrence(
        self,
        current_date: date,
        frequency: RecurrenceFrequency,
        day_of_month: Optional[int] = None,
        day_of_week: Optional[int] = None,
        end_date: Optional[date] = None,
    ) -> Optional[date]:
        """
        Calculate the next occurrence date based on frequency.

        Args:
            current_date: The current or last occurrence date
            frequency: Recurrence frequency (daily, weekly, monthly, etc.)
            day_of_month: Preferred day of month for monthly/yearly (1-31)
            day_of_week: Preferred day of week (0=Monday, 6=Sunday)
            end_date: Optional end date - returns None if past end date

        Returns:
            Next occurrence date, or None if recurrence has ended
        """
        next_date = None

        if frequency == RecurrenceFrequency.DAILY:
            next_date = current_date + timedelta(days=1)

        elif frequency == RecurrenceFrequency.WEEKLY:
            # Default to same day next week, or use specified day_of_week
            if day_of_week is not None:
                days_until_target = (day_of_week - current_date.weekday()) % 7
                if days_until_target == 0:
                    days_until_target = 7  # Next week if already on target day
                next_date = current_date + timedelta(days=days_until_target)
            else:
                next_date = current_date + timedelta(weeks=1)

        elif frequency == RecurrenceFrequency.BIWEEKLY:
            next_date = current_date + timedelta(weeks=2)

        elif frequency == RecurrenceFrequency.MONTHLY:
            # Use relativedelta for proper month handling
            next_date = current_date + relativedelta(months=1)
            # Adjust to preferred day of month if specified
            if day_of_month is not None:
                try:
                    # Handle months with fewer days
                    max_day = self._get_month_max_day(next_date.year, next_date.month)
                    actual_day = min(day_of_month, max_day)
                    next_date = next_date.replace(day=actual_day)
                except ValueError:
                    pass  # Keep calculated date if replacement fails

        elif frequency == RecurrenceFrequency.QUARTERLY:
            next_date = current_date + relativedelta(months=3)
            if day_of_month is not None:
                try:
                    max_day = self._get_month_max_day(next_date.year, next_date.month)
                    actual_day = min(day_of_month, max_day)
                    next_date = next_date.replace(day=actual_day)
                except ValueError:
                    pass

        elif frequency == RecurrenceFrequency.YEARLY:
            next_date = current_date + relativedelta(years=1)
            if day_of_month is not None:
                try:
                    max_day = self._get_month_max_day(next_date.year, next_date.month)
                    actual_day = min(day_of_month, max_day)
                    next_date = next_date.replace(day=actual_day)
                except ValueError:
                    pass

        # Check if past end date
        if end_date is not None and next_date is not None and next_date > end_date:
            return None

        return next_date

    def _get_month_max_day(self, year: int, month: int) -> int:
        """Get the maximum day for a given month."""
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        return (next_month - timedelta(days=1)).day

    async def generate_expense_from_template(
        self,
        template: Dict[str, Any],
        occurrence_date: date,
        organization_id: str,
        user_id: Optional[str] = None,
    ) -> Expense:
        """
        Generate a new expense instance from a recurring template.

        Args:
            template: The recurring expense template (dict from MongoDB)
            occurrence_date: The date for this expense instance
            organization_id: Organization ID
            user_id: User ID for created_by field

        Returns:
            Newly created Expense object
        """
        # Create expense data from template
        expense_data = {
            "expense_date": occurrence_date,
            "employee_id": template.get("employee_id"),
            "category": template.get("category"),
            "merchant": template.get("merchant"),
            "description": template.get("description", ""),
            "amount": template.get("amount"),
            "currency": template.get("currency", "USD"),
            "tax_amount": template.get("tax_amount", 0.0),
            "status": ExpenseStatus.APPROVED if template.get("auto_approve") else ExpenseStatus.PENDING,
            "is_reimbursable": template.get("is_reimbursable", True),
            "payable_to": template.get("payable_to"),
            "account_id": template.get("account_id"),
            "project_id": template.get("project_id"),
            "billable": template.get("billable", False),
            "notes": f"Auto-generated from recurring expense: {template.get('description', '')}",
            "is_recurring": False,  # Generated instances are not recurring themselves
            "parent_recurring_id": template.get("id"),
            "include_in_budget": template.get("include_in_budget", True),
            "budget_id": template.get("budget_id"),
            "organization_id": organization_id,
            "created_by": user_id or template.get("created_by"),
        }

        # Create expense object
        expense = Expense(**expense_data)

        # Convert date to datetime for MongoDB
        expense_dict = expense.model_dump()
        for key, value in expense_dict.items():
            if isinstance(value, date) and not isinstance(value, datetime):
                expense_dict[key] = datetime.combine(value, datetime.min.time())

        # Insert into database
        await self.db.expenses.insert_one(expense_dict)

        logger.info(
            f"Generated recurring expense instance: {expense.id} "
            f"from template {template.get('id')} for {occurrence_date}"
        )

        return expense

    async def process_recurring_expenses(
        self,
        organization_id: Optional[str] = None,
        target_date: Optional[date] = None,
    ) -> List[str]:
        """
        Process all due recurring expenses and generate instances.

        This should be called by a scheduler (e.g., daily cron job).

        Args:
            organization_id: Optional - process only for specific org
            target_date: Optional - process for specific date (default: today)

        Returns:
            List of generated expense IDs
        """
        if target_date is None:
            target_date = date.today()

        generated_ids = []

        # Build query for recurring expense templates
        query = {
            "is_active": True,
            "is_recurring": True,
            "next_occurrence_date": {"$lte": datetime.combine(target_date, datetime.min.time())},
        }

        if organization_id:
            query["organization_id"] = organization_id

        # Also check that recurrence hasn't ended
        query["$or"] = [
            {"recurrence_end_date": None},
            {"recurrence_end_date": {"$gte": datetime.combine(target_date, datetime.min.time())}},
        ]

        # Find all templates due for processing
        cursor = self.db.expenses.find(query)
        templates = await cursor.to_list(length=1000)

        logger.info(f"Found {len(templates)} recurring expense templates to process")

        for template in templates:
            try:
                # Get the next occurrence date
                next_occurrence = template.get("next_occurrence_date")
                if isinstance(next_occurrence, datetime):
                    next_occurrence = next_occurrence.date()

                # Generate expense for this occurrence
                expense = await self.generate_expense_from_template(
                    template=template,
                    occurrence_date=next_occurrence,
                    organization_id=template.get("organization_id"),
                )
                generated_ids.append(expense.id)

                # Calculate next occurrence
                frequency = RecurrenceFrequency(template.get("recurrence_frequency"))
                end_date = template.get("recurrence_end_date")
                if isinstance(end_date, datetime):
                    end_date = end_date.date()

                new_next_occurrence = self.calculate_next_occurrence(
                    current_date=next_occurrence,
                    frequency=frequency,
                    day_of_month=template.get("recurrence_day_of_month"),
                    day_of_week=template.get("recurrence_day_of_week"),
                    end_date=end_date,
                )

                # Update template with new next occurrence
                update_data = {}
                if new_next_occurrence:
                    update_data["next_occurrence_date"] = datetime.combine(
                        new_next_occurrence, datetime.min.time()
                    )
                else:
                    # Recurrence has ended - mark as inactive
                    update_data["is_recurring"] = False
                    update_data["next_occurrence_date"] = None
                    logger.info(
                        f"Recurring expense {template.get('id')} has reached end date"
                    )

                await self.db.expenses.update_one(
                    {"id": template.get("id")},
                    {"$set": update_data}
                )

            except Exception as e:
                logger.error(
                    f"Error processing recurring expense {template.get('id')}: {e}"
                )
                continue

        logger.info(f"Generated {len(generated_ids)} expense instances")
        return generated_ids

    async def get_recurring_expenses(
        self,
        organization_id: str,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get all recurring expense templates for an organization.

        Args:
            organization_id: Organization ID
            active_only: Only return active recurring expenses
            skip: Pagination skip
            limit: Pagination limit

        Returns:
            List of recurring expense templates
        """
        query = {
            "organization_id": organization_id,
            "is_recurring": True,
        }

        if active_only:
            query["is_active"] = True

        cursor = self.db.expenses.find(query).skip(skip).limit(limit).sort("created_at", -1)
        return await cursor.to_list(length=limit)

    async def get_budget_recurring_expenses(
        self,
        budget_id: str,
        organization_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get all recurring expenses linked to a specific budget.

        Args:
            budget_id: Budget ID
            organization_id: Organization ID

        Returns:
            List of recurring expenses for the budget
        """
        query = {
            "organization_id": organization_id,
            "budget_id": budget_id,
            "is_recurring": True,
            "is_active": True,
        }

        cursor = self.db.expenses.find(query)
        return await cursor.to_list(length=1000)

    async def calculate_budget_recurring_total(
        self,
        budget_id: str,
        organization_id: str,
        period_start: date,
        period_end: date,
    ) -> Dict[str, float]:
        """
        Calculate total recurring expenses for a budget period.

        This helps with budget forecasting by predicting recurring costs.

        Args:
            budget_id: Budget ID
            organization_id: Organization ID
            period_start: Budget period start date
            period_end: Budget period end date

        Returns:
            Dict with 'total' and 'by_category' breakdowns
        """
        recurring_expenses = await self.get_budget_recurring_expenses(
            budget_id=budget_id,
            organization_id=organization_id,
        )

        total = 0.0
        by_category: Dict[str, float] = {}

        for expense in recurring_expenses:
            if not expense.get("include_in_budget", True):
                continue

            # Calculate number of occurrences in the period
            frequency = RecurrenceFrequency(expense.get("recurrence_frequency"))
            amount = expense.get("amount", 0.0)

            occurrences = self._count_occurrences_in_period(
                frequency=frequency,
                period_start=period_start,
                period_end=period_end,
            )

            period_total = amount * occurrences
            total += period_total

            category = expense.get("category", "Uncategorized")
            by_category[category] = by_category.get(category, 0.0) + period_total

        return {
            "total": total,
            "by_category": by_category,
        }

    def _count_occurrences_in_period(
        self,
        frequency: RecurrenceFrequency,
        period_start: date,
        period_end: date,
    ) -> int:
        """Count how many times a recurring expense occurs in a period."""
        days = (period_end - period_start).days

        if frequency == RecurrenceFrequency.DAILY:
            return days
        elif frequency == RecurrenceFrequency.WEEKLY:
            return days // 7
        elif frequency == RecurrenceFrequency.BIWEEKLY:
            return days // 14
        elif frequency == RecurrenceFrequency.MONTHLY:
            return max(1, days // 30)
        elif frequency == RecurrenceFrequency.QUARTERLY:
            return max(1, days // 90)
        elif frequency == RecurrenceFrequency.YEARLY:
            return max(1, days // 365)

        return 1

    async def pause_recurring_expense(
        self,
        expense_id: str,
        organization_id: str,
    ) -> bool:
        """
        Pause a recurring expense (temporarily stop generating instances).

        Args:
            expense_id: Expense template ID
            organization_id: Organization ID

        Returns:
            True if successful
        """
        result = await self.db.expenses.update_one(
            {
                "id": expense_id,
                "organization_id": organization_id,
                "is_recurring": True,
            },
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.utcnow(),
                }
            }
        )

        return result.modified_count > 0

    async def resume_recurring_expense(
        self,
        expense_id: str,
        organization_id: str,
        resume_date: Optional[date] = None,
    ) -> bool:
        """
        Resume a paused recurring expense.

        Args:
            expense_id: Expense template ID
            organization_id: Organization ID
            resume_date: Optional date to resume from (default: today)

        Returns:
            True if successful
        """
        if resume_date is None:
            resume_date = date.today()

        result = await self.db.expenses.update_one(
            {
                "id": expense_id,
                "organization_id": organization_id,
                "is_recurring": True,
            },
            {
                "$set": {
                    "is_active": True,
                    "next_occurrence_date": datetime.combine(resume_date, datetime.min.time()),
                    "updated_at": datetime.utcnow(),
                }
            }
        )

        return result.modified_count > 0


# Singleton instance
_recurring_expense_service: Optional[RecurringExpenseService] = None


def get_recurring_expense_service() -> RecurringExpenseService:
    """
    Get the recurring expense service singleton.

    Returns:
        RecurringExpenseService instance
    """
    global _recurring_expense_service
    if _recurring_expense_service is None:
        _recurring_expense_service = RecurringExpenseService()
    return _recurring_expense_service
