"""
Project Management Models.

Handles projects, tasks, resources, and time tracking.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel as PydanticBaseModel, Field
from enum import Enum

from .base import BaseModel


class ProjectStatus(str, Enum):
    """Project status enumeration."""

    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """Task status enumeration."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Project(BaseModel):
    """
    Project model.

    Central record for projects.
    """

    # Basic info
    project_name: str = Field(..., description="Project name")
    project_code: str = Field(..., description="Unique project code")
    description: Optional[str] = Field(None, description="Project description")
    status: ProjectStatus = Field(default=ProjectStatus.PLANNING)

    # Dates
    start_date: date = Field(..., description="Project start date")
    end_date: Optional[date] = Field(None, description="Project end date (optional for planning phase)")
    actual_start_date: Optional[date] = Field(None, description="Actual start date")
    actual_end_date: Optional[date] = Field(None, description="Actual end date")

    # People
    project_manager_id: str = Field(..., description="Project manager employee ID")
    customer_id: Optional[str] = Field(None, description="Customer ID (if client project)")
    team_members: List[str] = Field(default_factory=list, description="Team member employee IDs")

    # Budget
    budget: float = Field(default=0.0, description="Project budget")
    actual_cost: float = Field(default=0.0, description="Actual cost incurred")
    currency: str = Field(default="GHS", description="Currency code")

    # Progress
    progress_percentage: float = Field(default=0.0, ge=0, le=100, description="Completion percentage")
    total_hours_estimated: float = Field(default=0.0, description="Estimated hours")
    total_hours_actual: float = Field(default=0.0, description="Actual hours logged")

    # Billing
    is_billable: bool = Field(default=False, description="Is billable to customer")
    billing_rate: Optional[float] = Field(None, description="Hourly billing rate")

    # Metadata
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    # Attachments
    attachments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of file attachments (documents, images, recordings, etc.)"
    )


class Task(BaseModel):
    """
    Task model.

    Individual tasks within projects.
    """

    # Task details
    project_id: str = Field(..., description="Project ID")
    task_name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    status: TaskStatus = Field(default=TaskStatus.TODO)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)

    # Assignment
    assigned_to: Optional[str] = Field(None, description="Assigned employee ID")
    assigned_by: Optional[str] = Field(None, description="Assigner user ID")

    # Dates
    start_date: Optional[date] = Field(None, description="Task start date")
    due_date: Optional[date] = Field(None, description="Task due date")
    completed_date: Optional[datetime] = Field(None, description="Completion date")

    # Effort
    estimated_hours: float = Field(default=0.0, description="Estimated hours")
    actual_hours: float = Field(default=0.0, description="Actual hours logged")

    # Dependencies
    parent_task_id: Optional[str] = Field(None, description="Parent task ID")
    dependencies: List[str] = Field(default_factory=list, description="Task IDs this depends on")

    # Progress
    progress_percentage: float = Field(default=0.0, ge=0, le=100, description="Completion percentage")

    # Attachments
    attachment_urls: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class Resource(BaseModel):
    """
    Resource model.

    Tracks resource allocation to projects.
    """

    # Resource details
    employee_id: str = Field(..., description="Employee ID")
    project_id: str = Field(..., description="Project ID")

    # Allocation
    allocation_percentage: float = Field(..., ge=0, le=100, description="Percentage allocated (0-100)")
    start_date: date = Field(..., description="Allocation start date")
    end_date: date = Field(..., description="Allocation end date")

    # Role
    role: str = Field(..., description="Role on project")
    hourly_rate: Optional[float] = Field(None, description="Hourly rate for this resource")

    # Cost
    total_cost: float = Field(default=0.0, description="Total cost for this allocation")

    notes: Optional[str] = Field(None, description="Notes")


class Timesheet(BaseModel):
    """
    Timesheet model.

    Time tracking for employees on projects/tasks.
    """

    # Employee and project
    employee_id: str = Field(..., description="Employee ID")
    project_id: str = Field(..., description="Project ID")
    task_id: Optional[str] = Field(None, description="Task ID (optional)")

    # Time
    work_date: date = Field(..., description="Date of work")
    hours: float = Field(..., description="Hours worked")
    description: Optional[str] = Field(None, description="Work description")

    # Billing
    is_billable: bool = Field(default=False, description="Is billable")
    billing_rate: Optional[float] = Field(None, description="Billing rate")
    amount: Optional[float] = Field(None, description="Billable amount")

    # Approval
    is_approved: bool = Field(default=False, description="Is approved")
    approved_by: Optional[str] = Field(None, description="Approver user ID")
    approved_date: Optional[datetime] = Field(None, description="Approval date")

    # Invoicing
    is_invoiced: bool = Field(default=False, description="Has been invoiced")
    invoice_id: Optional[str] = Field(None, description="Invoice ID")


# Request/Response models that don't require organization_id from client
class ProjectCreate(PydanticBaseModel):
    """Project creation request model."""

    project_name: str = Field(..., description="Project name")
    project_code: Optional[str] = Field(None, description="Project code (auto-generated if not provided)")
    description: Optional[str] = Field(None, description="Project description")
    status: ProjectStatus = Field(default=ProjectStatus.PLANNING)

    start_date: date = Field(..., description="Project start date")
    end_date: Optional[date] = Field(None, description="Project end date (optional for planning phase)")
    actual_start_date: Optional[date] = Field(None, description="Actual start date")
    actual_end_date: Optional[date] = Field(None, description="Actual end date")

    project_manager_id: str = Field(..., description="Project manager employee ID")
    customer_id: Optional[str] = Field(None, description="Customer ID (if client project)")
    team_members: List[str] = Field(default_factory=list, description="Team member employee IDs")

    budget: float = Field(default=0.0, description="Project budget")
    actual_cost: float = Field(default=0.0, description="Actual cost incurred")
    currency: str = Field(default="GHS", description="Currency code")

    progress_percentage: float = Field(default=0.0, ge=0, le=100, description="Completion percentage")
    total_hours_estimated: float = Field(default=0.0, description="Estimated hours")
    total_hours_actual: float = Field(default=0.0, description="Actual hours logged")

    is_billable: bool = Field(default=False, description="Is billable to customer")
    billing_rate: Optional[float] = Field(None, description="Hourly billing rate")

    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class TaskCreate(PydanticBaseModel):
    """Task creation request model."""

    project_id: str = Field(..., description="Project ID")
    task_name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    status: TaskStatus = Field(default=TaskStatus.TODO)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)

    assigned_to: Optional[str] = Field(None, description="Assigned employee ID")
    assigned_by: Optional[str] = Field(None, description="Assigner user ID")

    start_date: Optional[date] = Field(None, description="Task start date")
    due_date: Optional[date] = Field(None, description="Task due date")
    completed_date: Optional[datetime] = Field(None, description="Completion date")

    estimated_hours: float = Field(default=0.0, description="Estimated hours")
    actual_hours: float = Field(default=0.0, description="Actual hours logged")

    parent_task_id: Optional[str] = Field(None, description="Parent task ID")
    dependencies: List[str] = Field(default_factory=list, description="Task IDs this depends on")

    progress_percentage: float = Field(default=0.0, ge=0, le=100, description="Completion percentage")

    attachment_urls: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class ResourceCreate(PydanticBaseModel):
    """Resource creation request model."""

    employee_id: str = Field(..., description="Employee ID")
    project_id: str = Field(..., description="Project ID")
    allocation_percentage: float = Field(..., ge=0, le=100, description="Percentage allocated (0-100)")
    start_date: date = Field(..., description="Allocation start date")
    end_date: date = Field(..., description="Allocation end date")
    role: str = Field(..., description="Role on project")
    hourly_rate: Optional[float] = Field(None, description="Hourly rate for this resource")
    total_cost: float = Field(default=0.0, description="Total cost for this allocation")
    notes: Optional[str] = Field(None, description="Notes")


class TimesheetCreate(PydanticBaseModel):
    """Timesheet creation request model."""

    employee_id: str = Field(..., description="Employee ID")
    project_id: str = Field(..., description="Project ID")
    task_id: Optional[str] = Field(None, description="Task ID (optional)")
    work_date: date = Field(..., description="Date of work")
    hours: float = Field(..., description="Hours worked")
    description: Optional[str] = Field(None, description="Work description")
    is_billable: bool = Field(default=False, description="Is billable")
    billing_rate: Optional[float] = Field(None, description="Billing rate")
    amount: Optional[float] = Field(None, description="Billable amount")
    is_approved: bool = Field(default=False, description="Is approved")
    approved_by: Optional[str] = Field(None, description="Approver user ID")
    approved_date: Optional[datetime] = Field(None, description="Approval date")
    is_invoiced: bool = Field(default=False, description="Has been invoiced")
    invoice_id: Optional[str] = Field(None, description="Invoice ID")
