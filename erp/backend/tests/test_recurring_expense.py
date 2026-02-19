"""
Unit tests for Recurring Expense functionality.

Tests cover:
- RecurringExpenseService methods
- Date calculations for various frequencies
- API endpoints for CRUD operations
- Budget integration
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from dateutil.relativedelta import relativedelta

from app.services.recurring_expense_service import (
    RecurringExpenseService,
    get_recurring_expense_service,
)
from app.models.finance import RecurrenceFrequency, ExpenseStatus


class TestRecurringExpenseService:
    """Tests for RecurringExpenseService."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance for each test."""
        return RecurringExpenseService()

    # ========================================================================
    # calculate_next_occurrence tests
    # ========================================================================

    def test_calculate_next_occurrence_daily(self, service):
        """Test daily recurrence calculation."""
        current = date(2025, 11, 26)
        next_date = service.calculate_next_occurrence(
            current_date=current,
            frequency=RecurrenceFrequency.DAILY,
        )
        assert next_date == date(2025, 11, 27)

    def test_calculate_next_occurrence_weekly(self, service):
        """Test weekly recurrence without specific day."""
        current = date(2025, 11, 26)  # Wednesday
        next_date = service.calculate_next_occurrence(
            current_date=current,
            frequency=RecurrenceFrequency.WEEKLY,
        )
        assert next_date == date(2025, 12, 3)  # Next Wednesday

    def test_calculate_next_occurrence_weekly_with_day(self, service):
        """Test weekly recurrence with specific day of week."""
        current = date(2025, 11, 26)  # Wednesday (2)
        next_date = service.calculate_next_occurrence(
            current_date=current,
            frequency=RecurrenceFrequency.WEEKLY,
            day_of_week=0,  # Monday
        )
        assert next_date == date(2025, 12, 1)  # Next Monday

    def test_calculate_next_occurrence_biweekly(self, service):
        """Test biweekly recurrence calculation."""
        current = date(2025, 11, 26)
        next_date = service.calculate_next_occurrence(
            current_date=current,
            frequency=RecurrenceFrequency.BIWEEKLY,
        )
        assert next_date == date(2025, 12, 10)

    def test_calculate_next_occurrence_monthly(self, service):
        """Test monthly recurrence calculation."""
        current = date(2025, 11, 26)
        next_date = service.calculate_next_occurrence(
            current_date=current,
            frequency=RecurrenceFrequency.MONTHLY,
        )
        assert next_date == date(2025, 12, 26)

    def test_calculate_next_occurrence_monthly_with_day(self, service):
        """Test monthly recurrence with specific day of month."""
        current = date(2025, 11, 26)
        next_date = service.calculate_next_occurrence(
            current_date=current,
            frequency=RecurrenceFrequency.MONTHLY,
            day_of_month=15,
        )
        # December 15th
        assert next_date == date(2025, 12, 15)

    def test_calculate_next_occurrence_monthly_end_of_month(self, service):
        """Test monthly recurrence handles months with fewer days."""
        # January 31 -> February should go to Feb 28 (or 29 in leap year)
        current = date(2025, 1, 31)
        next_date = service.calculate_next_occurrence(
            current_date=current,
            frequency=RecurrenceFrequency.MONTHLY,
            day_of_month=31,
        )
        # February 2025 has 28 days
        assert next_date == date(2025, 2, 28)

    def test_calculate_next_occurrence_quarterly(self, service):
        """Test quarterly recurrence calculation."""
        current = date(2025, 11, 26)
        next_date = service.calculate_next_occurrence(
            current_date=current,
            frequency=RecurrenceFrequency.QUARTERLY,
        )
        assert next_date == date(2026, 2, 26)

    def test_calculate_next_occurrence_yearly(self, service):
        """Test yearly recurrence calculation."""
        current = date(2025, 11, 26)
        next_date = service.calculate_next_occurrence(
            current_date=current,
            frequency=RecurrenceFrequency.YEARLY,
        )
        assert next_date == date(2026, 11, 26)

    def test_calculate_next_occurrence_with_end_date_not_exceeded(self, service):
        """Test recurrence respects end date when not exceeded."""
        current = date(2025, 11, 26)
        end_date = date(2025, 12, 31)
        next_date = service.calculate_next_occurrence(
            current_date=current,
            frequency=RecurrenceFrequency.MONTHLY,
            end_date=end_date,
        )
        assert next_date == date(2025, 12, 26)

    def test_calculate_next_occurrence_with_end_date_exceeded(self, service):
        """Test recurrence returns None when end date exceeded."""
        current = date(2025, 12, 26)
        end_date = date(2025, 12, 31)
        next_date = service.calculate_next_occurrence(
            current_date=current,
            frequency=RecurrenceFrequency.MONTHLY,
            end_date=end_date,
        )
        assert next_date is None

    # ========================================================================
    # _get_month_max_day tests
    # ========================================================================

    def test_get_month_max_day_january(self, service):
        """Test max day for January (31 days)."""
        assert service._get_month_max_day(2025, 1) == 31

    def test_get_month_max_day_february_normal(self, service):
        """Test max day for February in non-leap year."""
        assert service._get_month_max_day(2025, 2) == 28

    def test_get_month_max_day_february_leap(self, service):
        """Test max day for February in leap year."""
        assert service._get_month_max_day(2024, 2) == 29

    def test_get_month_max_day_april(self, service):
        """Test max day for April (30 days)."""
        assert service._get_month_max_day(2025, 4) == 30

    # ========================================================================
    # _count_occurrences_in_period tests
    # ========================================================================

    def test_count_occurrences_daily(self, service):
        """Test counting daily occurrences in a period."""
        start = date(2025, 11, 1)
        end = date(2025, 11, 30)
        count = service._count_occurrences_in_period(
            frequency=RecurrenceFrequency.DAILY,
            period_start=start,
            period_end=end,
        )
        assert count == 29  # 30 days - 1

    def test_count_occurrences_weekly(self, service):
        """Test counting weekly occurrences in a period."""
        start = date(2025, 11, 1)
        end = date(2025, 11, 30)
        count = service._count_occurrences_in_period(
            frequency=RecurrenceFrequency.WEEKLY,
            period_start=start,
            period_end=end,
        )
        assert count == 4  # ~4 weeks

    def test_count_occurrences_monthly(self, service):
        """Test counting monthly occurrences in a period."""
        start = date(2025, 1, 1)
        end = date(2025, 12, 31)
        count = service._count_occurrences_in_period(
            frequency=RecurrenceFrequency.MONTHLY,
            period_start=start,
            period_end=end,
        )
        assert count == 12  # ~12 months


class TestRecurringExpenseServiceAsync:
    """Async tests for RecurringExpenseService."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        return RecurringExpenseService()

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        mock = MagicMock()
        mock.expenses = MagicMock()
        mock.budgets = MagicMock()
        return mock

    @pytest.mark.asyncio
    async def test_generate_expense_from_template(self, service, mock_db):
        """Test generating an expense from a recurring template."""
        with patch.object(service, '_db', mock_db):
            mock_db.expenses.insert_one = AsyncMock()

            template = {
                "id": "template-123",
                "merchant": "AWS",
                "category": "software",
                "description": "Monthly cloud hosting",
                "amount": 100.00,
                "currency": "USD",
                "tax_amount": 10.00,
                "auto_approve": True,
                "include_in_budget": True,
                "created_by": "user-123",
            }

            expense = await service.generate_expense_from_template(
                template=template,
                occurrence_date=date(2025, 11, 26),
                organization_id="org-123",
            )

            assert expense.merchant == "AWS"
            assert expense.category == "software"
            assert expense.amount == 100.00
            assert expense.status == ExpenseStatus.APPROVED  # auto_approve = True
            assert expense.parent_recurring_id == "template-123"
            assert expense.is_recurring == False  # Generated instances are not recurring
            mock_db.expenses.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recurring_expenses(self, service, mock_db):
        """Test fetching recurring expenses."""
        with patch.object(service, '_db', mock_db):
            mock_cursor = MagicMock()
            mock_cursor.skip.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=[
                {"id": "1", "merchant": "AWS", "is_recurring": True},
                {"id": "2", "merchant": "Google", "is_recurring": True},
            ])
            mock_db.expenses.find.return_value = mock_cursor

            expenses = await service.get_recurring_expenses(
                organization_id="org-123",
                active_only=True,
            )

            assert len(expenses) == 2
            mock_db.expenses.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_pause_recurring_expense(self, service, mock_db):
        """Test pausing a recurring expense."""
        with patch.object(service, '_db', mock_db):
            mock_db.expenses.update_one = AsyncMock(
                return_value=MagicMock(modified_count=1)
            )

            success = await service.pause_recurring_expense(
                expense_id="expense-123",
                organization_id="org-123",
            )

            assert success is True
            mock_db.expenses.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_pause_recurring_expense_not_found(self, service, mock_db):
        """Test pausing a non-existent recurring expense."""
        with patch.object(service, '_db', mock_db):
            mock_db.expenses.update_one = AsyncMock(
                return_value=MagicMock(modified_count=0)
            )

            success = await service.pause_recurring_expense(
                expense_id="nonexistent",
                organization_id="org-123",
            )

            assert success is False

    @pytest.mark.asyncio
    async def test_resume_recurring_expense(self, service, mock_db):
        """Test resuming a paused recurring expense."""
        with patch.object(service, '_db', mock_db):
            mock_db.expenses.update_one = AsyncMock(
                return_value=MagicMock(modified_count=1)
            )

            success = await service.resume_recurring_expense(
                expense_id="expense-123",
                organization_id="org-123",
                resume_date=date(2025, 12, 1),
            )

            assert success is True
            mock_db.expenses.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_budget_recurring_total(self, service, mock_db):
        """Test calculating total recurring expenses for a budget period."""
        with patch.object(service, '_db', mock_db):
            mock_cursor = MagicMock()
            mock_cursor.to_list = AsyncMock(return_value=[
                {
                    "id": "1",
                    "category": "software",
                    "amount": 100.00,
                    "recurrence_frequency": "monthly",
                    "include_in_budget": True,
                },
                {
                    "id": "2",
                    "category": "utilities",
                    "amount": 50.00,
                    "recurrence_frequency": "monthly",
                    "include_in_budget": True,
                },
            ])
            mock_db.expenses.find.return_value = mock_cursor

            totals = await service.calculate_budget_recurring_total(
                budget_id="budget-123",
                organization_id="org-123",
                period_start=date(2025, 1, 1),
                period_end=date(2025, 12, 31),
            )

            assert totals["total"] == 1800.0  # (100 + 50) * 12 months
            assert "software" in totals["by_category"]
            assert "utilities" in totals["by_category"]


class TestRecurringExpenseServiceSingleton:
    """Test the singleton pattern for the service."""

    def test_get_recurring_expense_service_returns_same_instance(self):
        """Test that get_recurring_expense_service returns the same instance."""
        service1 = get_recurring_expense_service()
        service2 = get_recurring_expense_service()
        assert service1 is service2

    def test_service_instance_type(self):
        """Test that the returned instance is correct type."""
        service = get_recurring_expense_service()
        assert isinstance(service, RecurringExpenseService)


class TestRecurrenceFrequencyEnum:
    """Tests for RecurrenceFrequency enum."""

    def test_all_frequencies_defined(self):
        """Test all expected frequencies are defined."""
        expected = ["daily", "weekly", "biweekly", "monthly", "quarterly", "yearly"]
        actual = [f.value for f in RecurrenceFrequency]
        assert set(expected) == set(actual)

    def test_frequency_values(self):
        """Test individual frequency values."""
        assert RecurrenceFrequency.DAILY.value == "daily"
        assert RecurrenceFrequency.WEEKLY.value == "weekly"
        assert RecurrenceFrequency.BIWEEKLY.value == "biweekly"
        assert RecurrenceFrequency.MONTHLY.value == "monthly"
        assert RecurrenceFrequency.QUARTERLY.value == "quarterly"
        assert RecurrenceFrequency.YEARLY.value == "yearly"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
