"""
System Models.

Handles integrations, workflows, and audit logs.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel as PydanticBaseModel, Field
from enum import Enum

from .base import BaseModel


class IntegrationStatus(str, Enum):
    """Integration status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class WorkflowStatus(str, Enum):
    """Workflow status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


class AuditLogAction(str, Enum):
    """Audit log action enumeration."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"


class Integration(BaseModel):
    """
    Integration model.

    Third-party integrations and API connections.
    """

    # Integration details
    name: str = Field(..., description="Integration name")
    integration_type: str = Field(..., description="Integration type (accounting, crm, hr, etc.)")
    provider: str = Field(..., description="Provider name (QuickBooks, Salesforce, etc.)")
    description: Optional[str] = Field(None, description="Integration description")

    # Status
    status: IntegrationStatus = Field(default=IntegrationStatus.PENDING)
    last_sync: Optional[datetime] = Field(None, description="Last sync timestamp")
    next_sync: Optional[datetime] = Field(None, description="Next scheduled sync")

    # Configuration
    config: Dict[str, Any] = Field(default_factory=dict, description="Integration configuration")
    credentials: Dict[str, Any] = Field(default_factory=dict, description="Encrypted credentials")
    api_endpoint: Optional[str] = Field(None, description="API endpoint URL")

    # Sync settings
    auto_sync: bool = Field(default=False, description="Auto-sync enabled")
    sync_frequency: Optional[str] = Field(None, description="Sync frequency (hourly, daily, etc.)")
    sync_direction: str = Field(default="bidirectional", description="Sync direction")

    # Data mapping
    field_mappings: Dict[str, str] = Field(default_factory=dict, description="Field mappings")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Sync filters")

    # Monitoring
    success_count: int = Field(default=0, description="Successful sync count")
    error_count: int = Field(default=0, description="Error count")
    last_error: Optional[str] = Field(None, description="Last error message")


class Workflow(BaseModel):
    """
    Workflow automation model.

    Automated workflows and business processes.
    """

    # Workflow details
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)

    # Trigger
    trigger_type: str = Field(..., description="Trigger type (schedule, event, manual)")
    trigger_config: Dict[str, Any] = Field(default_factory=dict, description="Trigger configuration")

    # Actions
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Workflow actions")

    # Conditions
    conditions: List[Dict[str, Any]] = Field(default_factory=list, description="Execution conditions")

    # Execution
    last_execution: Optional[datetime] = Field(None, description="Last execution timestamp")
    execution_count: int = Field(default=0, description="Total execution count")
    success_count: int = Field(default=0, description="Successful execution count")
    failure_count: int = Field(default=0, description="Failed execution count")

    # Schedule (if trigger_type is schedule)
    schedule_cron: Optional[str] = Field(None, description="Cron expression for scheduling")
    next_execution: Optional[datetime] = Field(None, description="Next scheduled execution")

    # Notifications
    notify_on_success: bool = Field(default=False, description="Send notification on success")
    notify_on_failure: bool = Field(default=True, description="Send notification on failure")
    notification_recipients: List[str] = Field(default_factory=list, description="Notification recipients")


class AuditLog(BaseModel):
    """
    Audit log model.

    Tracks all actions for compliance and security.
    """

    # Action details
    action: AuditLogAction = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Resource type (customer, invoice, etc.)")
    resource_id: Optional[str] = Field(None, description="Resource ID")

    # User
    user_id: str = Field(..., description="User who performed action")
    user_email: Optional[str] = Field(None, description="User email")

    # Request details
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    endpoint: Optional[str] = Field(None, description="API endpoint")
    method: Optional[str] = Field(None, description="HTTP method")

    # Changes
    changes: Optional[Dict[str, Any]] = Field(None, description="Changed fields (before/after)")

    # Metadata
    success: bool = Field(default=True, description="Action succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Note: Override created_by since audit logs track who did what
    # created_by is not needed in audit logs


class Department(BaseModel):
    """
    Department model.

    Organization-wide department structure for grouping employees.
    """

    # Department details
    name: str = Field(..., description="Department name")
    code: str = Field(..., description="Unique department code")
    description: Optional[str] = Field(None, description="Department description")

    # Hierarchy
    parent_department_id: Optional[str] = Field(None, description="Parent department ID for sub-departments")
    head_employee_id: Optional[str] = Field(None, description="Department head employee ID")

    # Budget
    budget_amount: Optional[float] = Field(None, description="Annual budget allocation")
    currency: str = Field(default="GHS", description="Currency code")
    cost_center_id: Optional[str] = Field(None, description="Associated cost center ID")

    # Tracking
    employee_count: int = Field(default=0, description="Number of employees in department")
    is_active: bool = Field(default=True, description="Department is active")


class CostCenter(BaseModel):
    """
    Cost center model.

    Tracks budgets and expenses by organizational unit.
    """

    # Cost center details
    name: str = Field(..., description="Cost center name")
    code: str = Field(..., description="Unique cost center code")
    description: Optional[str] = Field(None, description="Cost center description")
    cost_center_type: str = Field(..., description="Type (department, project, location, etc.)")

    # Budget
    budget_amount: float = Field(default=0.0, description="Allocated budget")
    actual_spend: float = Field(default=0.0, description="Actual spending to date")
    currency: str = Field(default="USD", description="Currency code")

    # Management
    manager_employee_id: Optional[str] = Field(None, description="Responsible manager employee ID")
    department_id: Optional[str] = Field(None, description="Associated department ID")

    # Period
    fiscal_year: int = Field(..., description="Fiscal year")
    period_start: Optional[datetime] = Field(None, description="Budget period start")
    period_end: Optional[datetime] = Field(None, description="Budget period end")

    # Status
    is_active: bool = Field(default=True, description="Cost center is active")


# ============================================================================
# CREATE DTOs (Data Transfer Objects for POST requests)
# ============================================================================

class DepartmentCreate(PydanticBaseModel):
    """Department creation DTO (excludes server-generated fields)."""

    name: str = Field(..., description="Department name")
    code: Optional[str] = Field(None, description="Department code (auto-generated if not provided)")
    description: Optional[str] = Field(None, description="Department description")
    parent_department_id: Optional[str] = Field(None, description="Parent department ID for sub-departments")
    head_employee_id: Optional[str] = Field(None, description="Department head employee ID")
    budget_amount: Optional[float] = Field(None, description="Annual budget allocation")
    currency: str = Field(default="GHS", description="Currency code")
    cost_center_id: Optional[str] = Field(None, description="Associated cost center ID")
    employee_count: int = Field(default=0, description="Number of employees in department")
    is_active: bool = Field(default=True, description="Department is active")


class CostCenterCreate(PydanticBaseModel):
    """Cost center creation DTO (excludes server-generated fields)."""

    name: str = Field(..., description="Cost center name")
    code: str = Field(..., description="Unique cost center code")
    description: Optional[str] = Field(None, description="Cost center description")
    cost_center_type: str = Field(..., description="Type (department, project, location, etc.)")
    budget_amount: float = Field(default=0.0, description="Allocated budget")
    actual_spend: float = Field(default=0.0, description="Actual spending to date")
    currency: str = Field(default="USD", description="Currency code")
    manager_employee_id: Optional[str] = Field(None, description="Responsible manager employee ID")
    department_id: Optional[str] = Field(None, description="Associated department ID")
    fiscal_year: int = Field(..., description="Fiscal year")
    period_start: Optional[datetime] = Field(None, description="Budget period start")
    period_end: Optional[datetime] = Field(None, description="Budget period end")
    is_active: bool = Field(default=True, description="Cost center is active")
