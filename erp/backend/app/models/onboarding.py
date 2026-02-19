"""
Employee Onboarding Models.

Handles employee onboarding workflows by department with customizable checklists.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel as PydanticBaseModel, Field, EmailStr
from enum import Enum

from .base import BaseModel


class OnboardingStatus(str, Enum):
    """Onboarding status enumeration."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class TaskStatus(str, Enum):
    """Task completion status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class OnboardingTask(PydanticBaseModel):
    """Individual onboarding task."""

    task_id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    category: str = Field(..., description="Task category (documents, it_setup, training, etc.)")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task completion status")
    due_date: Optional[date] = Field(None, description="Task due date")
    completed_date: Optional[datetime] = Field(None, description="When task was completed")
    completed_by: Optional[str] = Field(None, description="User ID who completed the task")
    assigned_to: Optional[str] = Field(None, description="User ID responsible for the task")
    order: int = Field(default=0, description="Display order")
    notes: Optional[str] = Field(None, description="Task notes")
    attachments: List[str] = Field(default_factory=list, description="URLs to attached documents")


class EmployeeOnboarding(BaseModel):
    """
    Employee Onboarding model.

    Tracks the onboarding process for new employees with department-specific checklists.
    """

    # Employee info
    employee_id: str = Field(..., description="Employee ID being onboarded")
    first_name: str = Field(..., description="Employee first name")
    last_name: str = Field(..., description="Employee last name")
    email: EmailStr = Field(..., description="Employee email")
    department: str = Field(..., description="Department")
    position: str = Field(..., description="Job position/title")

    # Onboarding details
    start_date: date = Field(..., description="Employee start date")
    onboarding_status: OnboardingStatus = Field(
        default=OnboardingStatus.NOT_STARTED,
        description="Overall onboarding status"
    )
    expected_completion_date: Optional[date] = Field(None, description="Expected completion date")
    actual_completion_date: Optional[datetime] = Field(None, description="Actual completion date")

    # Manager/Buddy
    manager_id: Optional[str] = Field(None, description="Manager employee ID")
    buddy_id: Optional[str] = Field(None, description="Onboarding buddy employee ID")
    hr_coordinator_id: Optional[str] = Field(None, description="HR coordinator user ID")

    # Tasks checklist (department-specific)
    tasks: List[OnboardingTask] = Field(default_factory=list, description="Onboarding tasks checklist")

    # Progress tracking
    total_tasks: int = Field(default=0, description="Total number of tasks")
    completed_tasks: int = Field(default=0, description="Number of completed tasks")
    progress_percentage: float = Field(default=0.0, description="Completion percentage")

    # Welcome kit
    welcome_kit_sent: bool = Field(default=False, description="Welcome kit sent status")
    welcome_kit_sent_date: Optional[datetime] = Field(None, description="When welcome kit was sent")
    equipment_issued: bool = Field(default=False, description="Equipment issued status")
    equipment_list: List[str] = Field(default_factory=list, description="List of issued equipment")

    # Access and accounts
    email_account_created: bool = Field(default=False, description="Email account created")
    system_access_granted: bool = Field(default=False, description="System access granted")
    access_systems: List[str] = Field(default_factory=list, description="List of granted system access")

    # Training
    training_sessions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Scheduled training sessions"
    )

    # Feedback
    day_one_feedback: Optional[str] = Field(None, description="Day 1 feedback from employee")
    week_one_feedback: Optional[str] = Field(None, description="Week 1 feedback from employee")
    month_one_feedback: Optional[str] = Field(None, description="Month 1 feedback from employee")

    # Legal documents
    nda_document_id: Optional[str] = Field(None, description="NDA legal document ID")
    nda_signed: bool = Field(default=False, description="NDA signed status")
    nda_signed_date: Optional[datetime] = Field(None, description="When NDA was signed")

    contract_document_id: Optional[str] = Field(None, description="Employment contract document ID")
    contract_signed: bool = Field(default=False, description="Contract signed status")
    contract_signed_date: Optional[datetime] = Field(None, description="When contract was signed")

    offer_letter_document_id: Optional[str] = Field(None, description="Offer letter document ID")
    offer_letter_accepted: bool = Field(default=False, description="Offer letter accepted")
    offer_letter_accepted_date: Optional[datetime] = Field(None, description="When offer was accepted")

    # Account creation tracking
    accounts_created: Dict[str, Any] = Field(
        default_factory=dict,
        description="Track which accounts have been created (email, slack, jira, crm, etc.)"
    )
    # Example: {"email": {"created": True, "created_at": "...", "username": "..."}, "slack": {...}}

    # Role-specific requirements
    role_type: Optional[str] = Field(None, description="Role type (developer, sales, marketing, finance, hr, operations)")
    required_accounts: List[str] = Field(
        default_factory=list,
        description="Required accounts for this role (e.g., ['email', 'slack', 'jira'] for dev)"
    )
    required_documents: List[str] = Field(
        default_factory=list,
        description="Required documents to review (e.g., DEV_INTERN_ONBOARDING_GUIDE.md)"
    )
    documents_reviewed: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Documents that have been reviewed with timestamps"
    )

    # Notes
    notes: Optional[str] = Field(None, description="General onboarding notes")
    special_requirements: Optional[str] = Field(None, description="Special requirements or accommodations")


class OnboardingTemplate(BaseModel):
    """
    Onboarding Template model.

    Defines department-specific onboarding checklists and workflows.
    """

    # Template details
    template_name: str = Field(..., description="Template name")
    department: str = Field(..., description="Department this template is for")
    position_type: Optional[str] = Field(None, description="Specific position type (optional)")
    description: Optional[str] = Field(None, description="Template description")

    # Tasks
    tasks: List[OnboardingTask] = Field(default_factory=list, description="Template task checklist")

    # Duration
    estimated_days: int = Field(default=30, description="Estimated onboarding duration in days")

    # Welcome kit items
    welcome_kit_items: List[str] = Field(default_factory=list, description="Standard welcome kit items")

    # Equipment
    standard_equipment: List[str] = Field(default_factory=list, description="Standard equipment to issue")

    # System access
    required_systems: List[str] = Field(default_factory=list, description="Required system access")

    # Training
    required_training: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Required training sessions"
    )

    # Status
    is_active: bool = Field(default=True, description="Template is active")


# ============================================================================
# CREATE DTOs (Data Transfer Objects for POST requests)
# ============================================================================

class OnboardingTaskCreate(PydanticBaseModel):
    """Onboarding task creation DTO."""

    task_id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    category: str = Field(..., description="Task category")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task completion status")
    due_date: Optional[date] = Field(None, description="Task due date")
    assigned_to: Optional[str] = Field(None, description="User ID responsible for the task")
    order: int = Field(default=0, description="Display order")
    notes: Optional[str] = Field(None, description="Task notes")


class EmployeeOnboardingCreate(PydanticBaseModel):
    """Employee onboarding creation DTO."""

    employee_id: str = Field(..., description="Employee ID being onboarded")
    first_name: str = Field(..., description="Employee first name")
    last_name: str = Field(..., description="Employee last name")
    email: EmailStr = Field(..., description="Employee email")
    department: str = Field(..., description="Department")
    position: str = Field(..., description="Job position/title")
    start_date: date = Field(..., description="Employee start date")
    expected_completion_date: Optional[date] = Field(None, description="Expected completion date")
    manager_id: Optional[str] = Field(None, description="Manager employee ID")
    buddy_id: Optional[str] = Field(None, description="Onboarding buddy employee ID")
    hr_coordinator_id: Optional[str] = Field(None, description="HR coordinator user ID")
    tasks: List[OnboardingTaskCreate] = Field(default_factory=list, description="Onboarding tasks")
    welcome_kit_sent: bool = Field(default=False, description="Welcome kit sent status")
    equipment_issued: bool = Field(default=False, description="Equipment issued status")
    equipment_list: List[str] = Field(default_factory=list, description="List of issued equipment")
    email_account_created: bool = Field(default=False, description="Email account created")
    system_access_granted: bool = Field(default=False, description="System access granted")
    access_systems: List[str] = Field(default_factory=list, description="List of granted system access")
    training_sessions: List[Dict[str, Any]] = Field(default_factory=list, description="Training sessions")
    role_type: Optional[str] = Field(None, description="Role type")
    required_accounts: List[str] = Field(default_factory=list, description="Required accounts for role")
    required_documents: List[str] = Field(default_factory=list, description="Required documents to review")
    notes: Optional[str] = Field(None, description="General onboarding notes")
    special_requirements: Optional[str] = Field(None, description="Special requirements")


class OnboardingTemplateCreate(PydanticBaseModel):
    """Onboarding template creation DTO."""

    template_name: str = Field(..., description="Template name")
    department: str = Field(..., description="Department this template is for")
    position_type: Optional[str] = Field(None, description="Specific position type (optional)")
    description: Optional[str] = Field(None, description="Template description")
    tasks: List[OnboardingTaskCreate] = Field(default_factory=list, description="Template task checklist")
    estimated_days: int = Field(default=30, description="Estimated onboarding duration in days")
    welcome_kit_items: List[str] = Field(default_factory=list, description="Standard welcome kit items")
    standard_equipment: List[str] = Field(default_factory=list, description="Standard equipment to issue")
    required_systems: List[str] = Field(default_factory=list, description="Required system access")
    required_training: List[Dict[str, str]] = Field(default_factory=list, description="Required training")
    is_active: bool = Field(default=True, description="Template is active")


class OnboardingTaskUpdate(PydanticBaseModel):
    """Update individual task within an onboarding."""

    status: Optional[TaskStatus] = Field(None, description="Task status")
    notes: Optional[str] = Field(None, description="Task notes")
    attachments: Optional[List[str]] = Field(None, description="Attachment URLs")


class OnboardingUpdate(PydanticBaseModel):
    """Update onboarding record."""

    onboarding_status: Optional[OnboardingStatus] = Field(None, description="Overall status")
    buddy_id: Optional[str] = Field(None, description="Onboarding buddy")
    welcome_kit_sent: Optional[bool] = Field(None, description="Welcome kit status")
    equipment_issued: Optional[bool] = Field(None, description="Equipment issued status")
    equipment_list: Optional[List[str]] = Field(None, description="Equipment list")
    email_account_created: Optional[bool] = Field(None, description="Email account status")
    system_access_granted: Optional[bool] = Field(None, description="System access status")
    access_systems: Optional[List[str]] = Field(None, description="Access systems")
    training_sessions: Optional[List[Dict[str, Any]]] = Field(None, description="Training sessions")
    day_one_feedback: Optional[str] = Field(None, description="Day 1 feedback")
    week_one_feedback: Optional[str] = Field(None, description="Week 1 feedback")
    month_one_feedback: Optional[str] = Field(None, description="Month 1 feedback")
    accounts_created: Optional[Dict[str, Any]] = Field(None, description="Account creation tracking")
    documents_reviewed: Optional[List[Dict[str, Any]]] = Field(None, description="Reviewed documents")
    notes: Optional[str] = Field(None, description="General notes")
    special_requirements: Optional[str] = Field(None, description="Special requirements")
