"""
Export Routes for ERP data.

Provides endpoints to export expenses, projects, opportunities, and employees
to CSV and Excel formats.
"""

import logging
from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
import io

from app.core.database import MongoDB
from app.services.export_service import (
    get_export_service,
    ExportFormat,
    EXPENSE_COLUMNS,
    EXPENSE_COLUMN_MAPPING,
    PROJECT_COLUMNS,
    PROJECT_COLUMN_MAPPING,
    OPPORTUNITY_COLUMNS,
    OPPORTUNITY_COLUMN_MAPPING,
    EMPLOYEE_COLUMNS,
    EMPLOYEE_COLUMN_MAPPING,
)
from apps.shared.dependencies import require_organization_access, OrganizationScoped

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_content_type(format: ExportFormat) -> str:
    """Get content type for export format."""
    if format == ExportFormat.CSV:
        return "text/csv"
    return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _get_file_extension(format: ExportFormat) -> str:
    """Get file extension for export format."""
    return format.value


@router.get("/expenses")
async def export_expenses(
    org_id: str = Depends(require_organization_access),
    format: ExportFormat = Query(ExportFormat.EXCEL, description="Export format (csv or xlsx)"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    start_date: Optional[date] = Query(None, description="Filter expenses from this date"),
    end_date: Optional[date] = Query(None, description="Filter expenses until this date"),
    employee_id: Optional[str] = Query(None, description="Filter by employee ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
):
    """
    Export expenses to CSV or Excel.

    Args:
        org_id: Organization ID (from auth).
        format: Export format (csv or xlsx).
        status_filter: Optional status filter.
        category: Optional category filter.
        start_date: Optional start date filter.
        end_date: Optional end date filter.
        employee_id: Optional employee ID filter.
        project_id: Optional project ID filter.

    Returns:
        StreamingResponse with exported file.
    """
    db = MongoDB.get_database()
    export_service = get_export_service()

    # Build query
    query = {"organization_id": org_id, "is_active": True}

    if status_filter:
        query["status"] = status_filter
    if category:
        query["category"] = category
    if employee_id:
        query["employee_id"] = employee_id
    if project_id:
        query["project_id"] = project_id
    if start_date:
        query.setdefault("expense_date", {})["$gte"] = datetime.combine(start_date, datetime.min.time())
    if end_date:
        query.setdefault("expense_date", {})["$lte"] = datetime.combine(end_date, datetime.max.time())

    # Fetch data
    cursor = db.expenses.find(query).sort("expense_date", -1)
    expenses = await cursor.to_list(length=10000)

    if not expenses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No expenses found matching the criteria"
        )

    # Export
    file_content = export_service.export(
        data=expenses,
        format=format,
        sheet_name="Expenses",
        columns=EXPENSE_COLUMNS,
        column_mapping=EXPENSE_COLUMN_MAPPING
    )

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"expenses_export_{timestamp}.{_get_file_extension(format)}"

    logger.info(f"Exported {len(expenses)} expenses to {format.value} for org {org_id}")

    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=_get_content_type(format),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/projects")
async def export_projects(
    org_id: str = Depends(require_organization_access),
    format: ExportFormat = Query(ExportFormat.EXCEL, description="Export format (csv or xlsx)"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    project_manager_id: Optional[str] = Query(None, description="Filter by project manager ID"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    start_date: Optional[date] = Query(None, description="Filter projects starting from this date"),
    end_date: Optional[date] = Query(None, description="Filter projects starting until this date"),
):
    """
    Export projects to CSV or Excel.

    Args:
        org_id: Organization ID (from auth).
        format: Export format (csv or xlsx).
        status_filter: Optional status filter.
        project_manager_id: Optional project manager ID filter.
        customer_id: Optional customer ID filter.
        start_date: Optional start date filter.
        end_date: Optional end date filter.

    Returns:
        StreamingResponse with exported file.
    """
    db = MongoDB.get_database()
    export_service = get_export_service()

    # Build query
    query = {"organization_id": org_id, "is_active": True}

    if status_filter:
        query["status"] = status_filter
    if project_manager_id:
        query["project_manager_id"] = project_manager_id
    if customer_id:
        query["customer_id"] = customer_id
    if start_date:
        query.setdefault("start_date", {})["$gte"] = datetime.combine(start_date, datetime.min.time())
    if end_date:
        query.setdefault("start_date", {})["$lte"] = datetime.combine(end_date, datetime.max.time())

    # Fetch data
    cursor = db.projects.find(query).sort("created_at", -1)
    projects = await cursor.to_list(length=10000)

    if not projects:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No projects found matching the criteria"
        )

    # Export
    file_content = export_service.export(
        data=projects,
        format=format,
        sheet_name="Projects",
        columns=PROJECT_COLUMNS,
        column_mapping=PROJECT_COLUMN_MAPPING
    )

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"projects_export_{timestamp}.{_get_file_extension(format)}"

    logger.info(f"Exported {len(projects)} projects to {format.value} for org {org_id}")

    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=_get_content_type(format),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/opportunities")
async def export_opportunities(
    org_id: str = Depends(require_organization_access),
    format: ExportFormat = Query(ExportFormat.EXCEL, description="Export format (csv or xlsx)"),
    stage: Optional[str] = Query(None, description="Filter by stage"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned user ID"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    probability_min: Optional[int] = Query(None, description="Minimum probability filter"),
    amount_min: Optional[float] = Query(None, description="Minimum amount filter"),
    start_date: Optional[date] = Query(None, description="Filter opportunities created from this date"),
    end_date: Optional[date] = Query(None, description="Filter opportunities created until this date"),
):
    """
    Export opportunities to CSV or Excel.

    Args:
        org_id: Organization ID (from auth).
        format: Export format (csv or xlsx).
        stage: Optional stage filter.
        assigned_to: Optional assigned user filter.
        customer_id: Optional customer ID filter.
        probability_min: Optional minimum probability filter.
        amount_min: Optional minimum amount filter.
        start_date: Optional start date filter.
        end_date: Optional end date filter.

    Returns:
        StreamingResponse with exported file.
    """
    db = MongoDB.get_database()
    export_service = get_export_service()

    # Build query
    query = {"organization_id": org_id, "is_active": True}

    if stage:
        query["stage"] = stage
    if assigned_to:
        query["assigned_to"] = assigned_to
    if customer_id:
        query["customer_id"] = customer_id
    if probability_min is not None:
        query.setdefault("probability", {})["$gte"] = probability_min
    if amount_min is not None:
        query.setdefault("amount", {})["$gte"] = amount_min
    if start_date:
        query.setdefault("created_at", {})["$gte"] = datetime.combine(start_date, datetime.min.time())
    if end_date:
        query.setdefault("created_at", {})["$lte"] = datetime.combine(end_date, datetime.max.time())

    # Fetch data
    cursor = db.opportunities.find(query).sort("created_at", -1)
    opportunities = await cursor.to_list(length=10000)

    if not opportunities:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No opportunities found matching the criteria"
        )

    # Export
    file_content = export_service.export(
        data=opportunities,
        format=format,
        sheet_name="Opportunities",
        columns=OPPORTUNITY_COLUMNS,
        column_mapping=OPPORTUNITY_COLUMN_MAPPING
    )

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"opportunities_export_{timestamp}.{_get_file_extension(format)}"

    logger.info(f"Exported {len(opportunities)} opportunities to {format.value} for org {org_id}")

    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=_get_content_type(format),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/employees")
async def export_employees(
    org_id: str = Depends(require_organization_access),
    format: ExportFormat = Query(ExportFormat.EXCEL, description="Export format (csv or xlsx)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    position: Optional[str] = Query(None, description="Filter by position"),
    employment_status: Optional[str] = Query(None, description="Filter by employment status"),
    employment_type: Optional[str] = Query(None, description="Filter by employment type"),
    manager_id: Optional[str] = Query(None, description="Filter by manager ID"),
    hire_date_from: Optional[date] = Query(None, description="Filter employees hired from this date"),
    hire_date_to: Optional[date] = Query(None, description="Filter employees hired until this date"),
):
    """
    Export employees to CSV or Excel.

    Args:
        org_id: Organization ID (from auth).
        format: Export format (csv or xlsx).
        department: Optional department filter.
        position: Optional position filter.
        employment_status: Optional employment status filter.
        employment_type: Optional employment type filter.
        manager_id: Optional manager ID filter.
        hire_date_from: Optional hire date from filter.
        hire_date_to: Optional hire date to filter.

    Returns:
        StreamingResponse with exported file.
    """
    db = MongoDB.get_database()
    export_service = get_export_service()

    # Build query
    query = {"organization_id": org_id, "is_active": True}

    if department:
        query["department"] = department
    if position:
        query["position"] = position
    if employment_status:
        query["employment_status"] = employment_status
    if employment_type:
        query["employment_type"] = employment_type
    if manager_id:
        query["manager_id"] = manager_id
    if hire_date_from:
        query.setdefault("hire_date", {})["$gte"] = datetime.combine(hire_date_from, datetime.min.time())
    if hire_date_to:
        query.setdefault("hire_date", {})["$lte"] = datetime.combine(hire_date_to, datetime.max.time())

    # Fetch data
    cursor = db.employees.find(query).sort("created_at", -1)
    employees = await cursor.to_list(length=10000)

    if not employees:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No employees found matching the criteria"
        )

    # Remove sensitive fields before export
    for emp in employees:
        emp.pop("email_temporary_password", None)
        emp.pop("national_id", None)

    # Export
    file_content = export_service.export(
        data=employees,
        format=format,
        sheet_name="Employees",
        columns=EMPLOYEE_COLUMNS,
        column_mapping=EMPLOYEE_COLUMN_MAPPING
    )

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"employees_export_{timestamp}.{_get_file_extension(format)}"

    logger.info(f"Exported {len(employees)} employees to {format.value} for org {org_id}")

    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=_get_content_type(format),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
