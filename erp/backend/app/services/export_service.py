"""
Export Service for ERP data.

Provides functionality to export data to CSV and Excel formats.
"""

import io
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Literal
from enum import Enum

import pandas as pd

logger = logging.getLogger(__name__)


class ExportFormat(str, Enum):
    """Export format enumeration."""
    CSV = "csv"
    EXCEL = "xlsx"


class ExportService:
    """
    Service for exporting ERP data to various formats.

    Supports CSV and Excel exports with customizable column selection.
    """

    def __init__(self):
        """Initialize export service."""
        pass

    def _serialize_value(self, value: Any) -> Any:
        """
        Serialize value for export.

        Args:
            value: Value to serialize.

        Returns:
            Serialized value suitable for export.
        """
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, list):
            if all(isinstance(item, str) for item in value):
                return ", ".join(value)
            return str(value)
        if isinstance(value, dict):
            return str(value)
        return value

    def _prepare_dataframe(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        column_mapping: Optional[Dict[str, str]] = None
    ) -> pd.DataFrame:
        """
        Prepare DataFrame from data for export.

        Args:
            data: List of dictionaries containing data.
            columns: Optional list of columns to include.
            column_mapping: Optional mapping of field names to display names.

        Returns:
            Prepared DataFrame.
        """
        if not data:
            return pd.DataFrame()

        # Serialize all values
        serialized_data = []
        for item in data:
            serialized_item = {
                k: self._serialize_value(v) for k, v in item.items()
            }
            serialized_data.append(serialized_item)

        df = pd.DataFrame(serialized_data)

        # Select specific columns if provided
        if columns:
            available_cols = [c for c in columns if c in df.columns]
            df = df[available_cols]

        # Rename columns if mapping provided
        if column_mapping:
            df = df.rename(columns=column_mapping)

        return df

    def export_to_csv(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        column_mapping: Optional[Dict[str, str]] = None
    ) -> bytes:
        """
        Export data to CSV format.

        Args:
            data: List of dictionaries containing data.
            columns: Optional list of columns to include.
            column_mapping: Optional mapping of field names to display names.

        Returns:
            CSV file content as bytes.
        """
        df = self._prepare_dataframe(data, columns, column_mapping)
        output = io.BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        return output.getvalue()

    def export_to_excel(
        self,
        data: List[Dict[str, Any]],
        sheet_name: str = "Data",
        columns: Optional[List[str]] = None,
        column_mapping: Optional[Dict[str, str]] = None
    ) -> bytes:
        """
        Export data to Excel format.

        Args:
            data: List of dictionaries containing data.
            sheet_name: Name of the Excel sheet.
            columns: Optional list of columns to include.
            column_mapping: Optional mapping of field names to display names.

        Returns:
            Excel file content as bytes.
        """
        df = self._prepare_dataframe(data, columns, column_mapping)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        output.seek(0)
        return output.getvalue()

    def export(
        self,
        data: List[Dict[str, Any]],
        format: ExportFormat,
        sheet_name: str = "Data",
        columns: Optional[List[str]] = None,
        column_mapping: Optional[Dict[str, str]] = None
    ) -> bytes:
        """
        Export data to specified format.

        Args:
            data: List of dictionaries containing data.
            format: Export format (csv or xlsx).
            sheet_name: Name of the Excel sheet (only for Excel).
            columns: Optional list of columns to include.
            column_mapping: Optional mapping of field names to display names.

        Returns:
            File content as bytes.
        """
        if format == ExportFormat.CSV:
            return self.export_to_csv(data, columns, column_mapping)
        elif format == ExportFormat.EXCEL:
            return self.export_to_excel(data, sheet_name, columns, column_mapping)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Default column configurations for each entity type
EXPENSE_COLUMNS = [
    "id", "expense_date", "category", "merchant", "description",
    "amount", "currency", "tax_amount", "status", "employee_id",
    "approved_by", "approver_name", "approved_date", "rejection_reason",
    "is_reimbursable", "payable_to", "reimbursed", "reimbursement_date",
    "project_id", "billable", "notes", "is_recurring", "recurrence_frequency",
    "created_at"
]

EXPENSE_COLUMN_MAPPING = {
    "id": "ID",
    "expense_date": "Date",
    "category": "Category",
    "merchant": "Merchant",
    "description": "Description",
    "amount": "Amount",
    "currency": "Currency",
    "tax_amount": "Tax Amount",
    "status": "Status",
    "employee_id": "Employee ID",
    "approved_by": "Approved By",
    "approver_name": "Approver Name",
    "approved_date": "Approval Date",
    "rejection_reason": "Rejection Reason",
    "is_reimbursable": "Reimbursable",
    "payable_to": "Payable To",
    "reimbursed": "Reimbursed",
    "reimbursement_date": "Reimbursement Date",
    "project_id": "Project ID",
    "billable": "Billable",
    "notes": "Notes",
    "is_recurring": "Recurring",
    "recurrence_frequency": "Recurrence Frequency",
    "created_at": "Created At"
}

PROJECT_COLUMNS = [
    "id", "project_code", "project_name", "description", "status",
    "start_date", "end_date", "actual_start_date", "actual_end_date",
    "project_manager_id", "customer_id", "budget", "actual_cost", "currency",
    "progress_percentage", "total_hours_estimated", "total_hours_actual",
    "is_billable", "billing_rate", "tags", "created_at"
]

PROJECT_COLUMN_MAPPING = {
    "id": "ID",
    "project_code": "Project Code",
    "project_name": "Project Name",
    "description": "Description",
    "status": "Status",
    "start_date": "Start Date",
    "end_date": "End Date",
    "actual_start_date": "Actual Start Date",
    "actual_end_date": "Actual End Date",
    "project_manager_id": "Project Manager ID",
    "customer_id": "Customer ID",
    "budget": "Budget",
    "actual_cost": "Actual Cost",
    "currency": "Currency",
    "progress_percentage": "Progress (%)",
    "total_hours_estimated": "Estimated Hours",
    "total_hours_actual": "Actual Hours",
    "is_billable": "Billable",
    "billing_rate": "Billing Rate",
    "tags": "Tags",
    "created_at": "Created At"
}

OPPORTUNITY_COLUMNS = [
    "id", "name", "customer_id", "lead_id", "amount", "stage",
    "probability", "expected_close_date", "closed_date", "assigned_to",
    "description", "competitors", "next_step", "loss_reason",
    "next_step_date", "last_activity_date", "activity_count",
    "stage_entered_date", "created_at"
]

OPPORTUNITY_COLUMN_MAPPING = {
    "id": "ID",
    "name": "Opportunity Name",
    "customer_id": "Customer ID",
    "lead_id": "Lead ID",
    "amount": "Amount",
    "stage": "Stage",
    "probability": "Probability (%)",
    "expected_close_date": "Expected Close Date",
    "closed_date": "Closed Date",
    "assigned_to": "Assigned To",
    "description": "Description",
    "competitors": "Competitors",
    "next_step": "Next Step",
    "loss_reason": "Loss Reason",
    "next_step_date": "Next Step Date",
    "last_activity_date": "Last Activity Date",
    "activity_count": "Activity Count",
    "stage_entered_date": "Stage Entered Date",
    "created_at": "Created At"
}

EMPLOYEE_COLUMNS = [
    "id", "employee_id", "first_name", "last_name", "email", "phone",
    "date_of_birth", "national_id", "street_address", "city", "state",
    "postal_code", "country", "employment_status", "employment_type",
    "department", "position", "manager_id", "hire_date", "termination_date",
    "salary", "currency", "pay_frequency", "performance_rating",
    "last_review_date", "next_review_date", "tags", "created_at"
]

EMPLOYEE_COLUMN_MAPPING = {
    "id": "ID",
    "employee_id": "Employee ID",
    "first_name": "First Name",
    "last_name": "Last Name",
    "email": "Email",
    "phone": "Phone",
    "date_of_birth": "Date of Birth",
    "national_id": "National ID",
    "street_address": "Street Address",
    "city": "City",
    "state": "State",
    "postal_code": "Postal Code",
    "country": "Country",
    "employment_status": "Employment Status",
    "employment_type": "Employment Type",
    "department": "Department",
    "position": "Position",
    "manager_id": "Manager ID",
    "hire_date": "Hire Date",
    "termination_date": "Termination Date",
    "salary": "Salary",
    "currency": "Currency",
    "pay_frequency": "Pay Frequency",
    "performance_rating": "Performance Rating",
    "last_review_date": "Last Review Date",
    "next_review_date": "Next Review Date",
    "tags": "Tags",
    "created_at": "Created At"
}


# Singleton instance
_export_service: Optional[ExportService] = None


def get_export_service() -> ExportService:
    """
    Get export service singleton instance.

    Returns:
        ExportService instance.
    """
    global _export_service
    if _export_service is None:
        _export_service = ExportService()
    return _export_service
