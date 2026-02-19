"""
HR (Human Resources) Models.

Handles employees, payroll, benefits, and recruitment.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel as PydanticBaseModel, Field, EmailStr
from enum import Enum

from .base import BaseModel


class EmploymentStatus(str, Enum):
    """Employment status enumeration."""

    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"
    RETIRED = "retired"


class EmploymentType(str, Enum):
    """Employment type enumeration."""

    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"


class RecruitmentStatus(str, Enum):
    """Recruitment status enumeration."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    FILLED = "filled"
    CANCELLED = "cancelled"


class Employee(BaseModel):
    """
    Employee model.

    Central record for employee information.
    """

    # Personal info
    employee_id: str = Field(..., description="Unique employee identifier")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: EmailStr = Field(..., description="Work email")
    phone: Optional[str] = Field(None, description="Phone number")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    national_id: Optional[str] = Field(None, description="National ID / SSN")

    # Address
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    # Employment details
    employment_status: EmploymentStatus = Field(default=EmploymentStatus.ACTIVE)
    employment_type: EmploymentType = Field(default=EmploymentType.FULL_TIME)
    department: str = Field(..., description="Department")
    position: str = Field(..., description="Job position/title")
    manager_id: Optional[str] = Field(None, description="Manager employee ID")
    hire_date: date = Field(..., description="Date of hire")
    termination_date: Optional[date] = Field(None, description="Termination date")

    # Compensation
    salary: float = Field(..., description="Annual salary")
    currency: str = Field(default="USD", description="Currency code")
    pay_frequency: str = Field(default="monthly", description="Pay frequency")

    # Performance
    performance_rating: Optional[float] = Field(None, ge=0, le=5, description="Performance rating (0-5)")
    last_review_date: Optional[date] = Field(None, description="Last performance review")
    next_review_date: Optional[date] = Field(None, description="Next performance review")

    # Emergency contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None

    # Email account tracking
    email_account_created: bool = Field(default=False, description="Email account creation status")
    email_account_created_at: Optional[datetime] = Field(None, description="When email account was created")
    email_account_status: str = Field(default="pending", description="Email account status: pending|active|disabled|failed")
    email_temporary_password: Optional[str] = Field(None, description="Temporary password (cleared after first use)")

    # Document attachments
    cv_url: Optional[str] = Field(None, description="URL/path to employee CV")
    certificates: List[Dict[str, str]] = Field(default_factory=list, description="List of certificates with name and URL")

    # Metadata
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class Payroll(BaseModel):
    """
    Payroll record model.

    Tracks salary payments and deductions.
    """

    employee_id: str = Field(..., description="Employee ID")
    pay_period_start: date = Field(..., description="Pay period start date")
    pay_period_end: date = Field(..., description="Pay period end date")
    pay_date: date = Field(..., description="Payment date")

    # Earnings
    base_salary: float = Field(..., description="Base salary for period")
    overtime_pay: float = Field(default=0.0, description="Overtime payment")
    bonuses: float = Field(default=0.0, description="Bonuses")
    commissions: float = Field(default=0.0, description="Commissions")
    other_earnings: float = Field(default=0.0, description="Other earnings")
    gross_pay: float = Field(..., description="Total gross pay")

    # Deductions
    tax_deductions: float = Field(default=0.0, description="Tax deductions")
    insurance_deductions: float = Field(default=0.0, description="Insurance deductions")
    retirement_deductions: float = Field(default=0.0, description="Retirement contributions")
    other_deductions: float = Field(default=0.0, description="Other deductions")
    total_deductions: float = Field(..., description="Total deductions")

    # Net pay
    net_pay: float = Field(..., description="Net pay (gross - deductions)")

    # Payment info
    payment_method: str = Field(default="bank_transfer", description="Payment method")
    payment_reference: Optional[str] = Field(None, description="Payment reference/transaction ID")

    notes: Optional[str] = Field(None, description="Notes")


class Benefit(BaseModel):
    """
    Employee benefit model.

    Tracks benefits like health insurance, retirement plans, etc.
    """

    name: str = Field(..., description="Benefit name")
    benefit_type: str = Field(..., description="Benefit type (health, dental, retirement, etc.)")
    description: Optional[str] = Field(None, description="Benefit description")

    # Eligibility
    eligible_employment_types: List[EmploymentType] = Field(
        default_factory=lambda: [EmploymentType.FULL_TIME]
    )
    waiting_period_days: int = Field(default=0, description="Waiting period in days")

    # Cost
    employer_cost: float = Field(default=0.0, description="Employer monthly cost")
    employee_cost: float = Field(default=0.0, description="Employee monthly cost")

    # Provider
    provider_name: Optional[str] = Field(None, description="Benefit provider")
    provider_contact: Optional[str] = Field(None, description="Provider contact info")

    # Enrollment
    enrolled_employees: List[str] = Field(default_factory=list, description="List of enrolled employee IDs")


class Recruitment(BaseModel):
    """
    Job opening / recruitment model.

    Tracks open positions and hiring process.
    """

    job_title: str = Field(..., description="Job title")
    department: str = Field(..., description="Department")
    employment_type: EmploymentType = Field(..., description="Employment type")

    # Job details
    description: str = Field(..., description="Job description")
    requirements: List[str] = Field(default_factory=list, description="Job requirements")
    responsibilities: List[str] = Field(default_factory=list, description="Responsibilities")

    # Compensation
    salary_min: Optional[float] = Field(None, description="Minimum salary")
    salary_max: Optional[float] = Field(None, description="Maximum salary")
    currency: str = Field(default="USD", description="Currency code")

    # Recruitment
    status: RecruitmentStatus = Field(default=RecruitmentStatus.OPEN)
    posted_date: date = Field(default_factory=date.today)
    closing_date: Optional[date] = Field(None, description="Application closing date")
    hiring_manager_id: str = Field(..., description="Hiring manager employee ID")

    # Tracking
    applications_count: int = Field(default=0, description="Number of applications")
    interviews_scheduled: int = Field(default=0, description="Interviews scheduled")
    offers_made: int = Field(default=0, description="Offers made")

    # Filled
    filled_date: Optional[date] = Field(None, description="Date position was filled")


# ============================================================================
# CREATE DTOs (Data Transfer Objects for POST requests)
# ============================================================================

class EmployeeCreate(PydanticBaseModel):
    """Employee creation DTO (excludes server-generated fields)."""

    # employee_id is auto-generated by the backend
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: EmailStr = Field(..., description="Work email")
    phone: Optional[str] = Field(None, description="Phone number")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    national_id: Optional[str] = Field(None, description="National ID / SSN")
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    employment_status: EmploymentStatus = Field(default=EmploymentStatus.ACTIVE)
    employment_type: EmploymentType = Field(default=EmploymentType.FULL_TIME)
    department: str = Field(..., description="Department")
    position: str = Field(..., description="Job position/title")
    manager_id: Optional[str] = Field(None, description="Manager employee ID")
    hire_date: date = Field(..., description="Date of hire")
    termination_date: Optional[date] = Field(None, description="Termination date")
    salary: float = Field(..., description="Annual salary")
    currency: str = Field(default="USD", description="Currency code")
    pay_frequency: str = Field(default="monthly", description="Pay frequency")
    performance_rating: Optional[float] = Field(None, ge=0, le=5, description="Performance rating (0-5)")
    last_review_date: Optional[date] = Field(None, description="Last performance review")
    next_review_date: Optional[date] = Field(None, description="Next performance review")
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    cv_url: Optional[str] = Field(None, description="URL/path to employee CV")
    certificates: List[Dict[str, str]] = Field(default_factory=list, description="List of certificates with name and URL")
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class PayrollCreate(PydanticBaseModel):
    """Payroll creation DTO (excludes server-generated fields)."""

    employee_id: str = Field(..., description="Employee ID")
    pay_period_start: date = Field(..., description="Pay period start date")
    pay_period_end: date = Field(..., description="Pay period end date")
    pay_date: date = Field(..., description="Payment date")
    base_salary: float = Field(..., description="Base salary for period")
    overtime_pay: float = Field(default=0.0, description="Overtime payment")
    bonuses: float = Field(default=0.0, description="Bonuses")
    commissions: float = Field(default=0.0, description="Commissions")
    other_earnings: float = Field(default=0.0, description="Other earnings")
    gross_pay: float = Field(..., description="Total gross pay")
    tax_deductions: float = Field(default=0.0, description="Tax deductions")
    insurance_deductions: float = Field(default=0.0, description="Insurance deductions")
    retirement_deductions: float = Field(default=0.0, description="Retirement contributions")
    other_deductions: float = Field(default=0.0, description="Other deductions")
    total_deductions: float = Field(..., description="Total deductions")
    net_pay: float = Field(..., description="Net pay (gross - deductions)")
    payment_method: str = Field(default="bank_transfer", description="Payment method")
    payment_reference: Optional[str] = Field(None, description="Payment reference/transaction ID")
    notes: Optional[str] = Field(None, description="Notes")


class BenefitCreate(PydanticBaseModel):
    """Benefit creation DTO (excludes server-generated fields)."""

    name: str = Field(..., description="Benefit name")
    benefit_type: str = Field(..., description="Benefit type (health, dental, retirement, etc.)")
    description: Optional[str] = Field(None, description="Benefit description")
    eligible_employment_types: List[EmploymentType] = Field(
        default_factory=lambda: [EmploymentType.FULL_TIME]
    )
    waiting_period_days: int = Field(default=0, description="Waiting period in days")
    employer_cost: float = Field(default=0.0, description="Employer monthly cost")
    employee_cost: float = Field(default=0.0, description="Employee monthly cost")
    provider_name: Optional[str] = Field(None, description="Benefit provider")
    provider_contact: Optional[str] = Field(None, description="Provider contact info")
    enrolled_employees: List[str] = Field(default_factory=list, description="List of enrolled employee IDs")


class RecruitmentCreate(PydanticBaseModel):
    """Recruitment creation DTO (excludes server-generated fields)."""

    job_title: str = Field(..., description="Job title")
    department: str = Field(..., description="Department")
    employment_type: EmploymentType = Field(..., description="Employment type")
    description: str = Field(..., description="Job description")
    requirements: List[str] = Field(default_factory=list, description="Job requirements")
    responsibilities: List[str] = Field(default_factory=list, description="Responsibilities")
    salary_min: Optional[float] = Field(None, description="Minimum salary")
    salary_max: Optional[float] = Field(None, description="Maximum salary")
    currency: str = Field(default="USD", description="Currency code")
    status: RecruitmentStatus = Field(default=RecruitmentStatus.OPEN)
    posted_date: date = Field(default_factory=date.today)
    closing_date: Optional[date] = Field(None, description="Application closing date")
    hiring_manager_id: str = Field(..., description="Hiring manager employee ID")
    applications_count: int = Field(default=0, description="Number of applications")
    interviews_scheduled: int = Field(default=0, description="Interviews scheduled")
    offers_made: int = Field(default=0, description="Offers made")
    filled_date: Optional[date] = Field(None, description="Date position was filled")
