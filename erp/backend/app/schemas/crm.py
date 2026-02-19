"""
CRM Request/Response Schemas.

Separate schemas for create/update operations that don't require
auto-generated fields like organization_id, created_at, etc.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr

from app.models.crm import (
    CustomerType,
    LeadStatus,
    OpportunityStage,
)


# Customer Schemas
class CustomerCreate(BaseModel):
    """Schema for creating a customer."""

    customer_type: CustomerType = Field(default=CustomerType.INDIVIDUAL)
    # Individual customers
    first_name: Optional[str] = Field(None, description="First name (for individuals)")
    last_name: Optional[str] = Field(None, description="Last name (for individuals)")
    # Business customers
    company_name: Optional[str] = Field(None, description="Company name (for businesses)")
    tax_id: Optional[str] = Field(None, description="Tax ID / VAT number")
    # Contact info
    email: EmailStr = Field(..., description="Primary email")
    phone: Optional[str] = Field(None, description="Primary phone")
    website: Optional[str] = Field(None, description="Website URL")
    # Address
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    # Business info
    industry: Optional[str] = Field(None, description="Industry sector")
    annual_revenue: Optional[float] = Field(None, description="Annual revenue")
    employee_count: Optional[int] = Field(None, description="Number of employees")
    # Relationship
    account_manager: Optional[str] = Field(None, description="Account manager user ID")
    tags: List[str] = Field(default_factory=list, description="Customer tags")
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class CustomerUpdate(BaseModel):
    """Schema for updating a customer."""

    customer_type: Optional[CustomerType] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    tax_id: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    annual_revenue: Optional[float] = None
    employee_count: Optional[int] = None
    account_manager: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


# Lead Schemas
class LeadCreate(BaseModel):
    """Schema for creating a lead."""

    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    company: Optional[str] = Field(None, description="Company name")
    job_title: Optional[str] = Field(None, description="Job title")
    status: LeadStatus = Field(default=LeadStatus.NEW)
    source: str = Field(..., description="How the lead was acquired (e.g., Website, Referral, LinkedIn)")
    assigned_to: Optional[str] = Field(None, description="Sales rep user ID")
    notes: Optional[str] = Field(None, description="Additional notes")
    score: Optional[int] = Field(None, ge=0, le=100, description="Lead score (0-100)")


class LeadUpdate(BaseModel):
    """Schema for updating a lead."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    status: Optional[LeadStatus] = None
    source: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    score: Optional[int] = Field(None, ge=0, le=100)
    # Activity tracking fields (Phase 2.5)
    follow_up_date: Optional[datetime] = None
    last_contacted: Optional[datetime] = None
    next_action: Optional[str] = None
    last_activity_id: Optional[str] = None
    activity_count: Optional[int] = None


# Opportunity Schemas
class OpportunityCreate(BaseModel):
    """Schema for creating an opportunity."""

    name: str = Field(..., description="Opportunity name")
    customer_id: Optional[str] = Field(None, description="Customer ID (if existing customer)")
    lead_id: Optional[str] = Field(None, description="Lead ID (if from lead)")
    amount: float = Field(..., description="Expected deal value")
    stage: OpportunityStage = Field(default=OpportunityStage.PROSPECTING)
    probability: int = Field(default=10, ge=0, le=100, description="Win probability (0-100%)")
    expected_close_date: Optional[datetime] = Field(None, description="Expected close date")
    assigned_to: str = Field(..., description="Sales rep user ID")
    description: Optional[str] = Field(None, description="Opportunity description")
    competitors: List[str] = Field(default_factory=list, description="Competing companies")
    next_step: Optional[str] = Field(None, description="Next action to take")


class OpportunityUpdate(BaseModel):
    """Schema for updating an opportunity."""

    name: Optional[str] = None
    customer_id: Optional[str] = None
    lead_id: Optional[str] = None
    amount: Optional[float] = None
    stage: Optional[OpportunityStage] = None
    probability: Optional[int] = Field(None, ge=0, le=100)
    expected_close_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    description: Optional[str] = None
    competitors: Optional[List[str]] = None
    next_step: Optional[str] = None
    loss_reason: Optional[str] = None
    # Activity tracking fields (Phase 2.5)
    next_step_date: Optional[datetime] = None
    last_activity_date: Optional[datetime] = None
    last_activity_id: Optional[str] = None
    activity_count: Optional[int] = None
    stage_entered_date: Optional[datetime] = None


# Contact Schemas
class ContactCreate(BaseModel):
    """Schema for creating a contact."""

    customer_id: str = Field(..., description="Associated customer ID")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    mobile: Optional[str] = Field(None, description="Mobile number")
    job_title: Optional[str] = Field(None, description="Job title")
    department: Optional[str] = Field(None, description="Department")
    is_primary: bool = Field(default=False, description="Is primary contact")
    notes: Optional[str] = Field(None, description="Notes")


class ContactUpdate(BaseModel):
    """Schema for updating a contact."""

    customer_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None


# Bulk Import Schemas
class ContactImportRow(BaseModel):
    """Schema for a single contact import row (minimal data)."""

    phone: Optional[str] = Field(None, description="Phone number")
    mobile: Optional[str] = Field(None, description="Mobile number")
    email: Optional[str] = Field(None, description="Email")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    company: Optional[str] = Field(None, description="Company name")
    job_title: Optional[str] = Field(None, description="Job title")
    notes: Optional[str] = Field(None, description="Notes")


class ContactBulkImportRequest(BaseModel):
    """Schema for bulk contact import request."""

    contacts: List[ContactImportRow] = Field(..., description="List of contacts to import")
    customer_name: Optional[str] = Field(
        default="Imported Contacts",
        description="Customer name for all imported contacts (creates new customer if needed)"
    )
    skip_duplicates: bool = Field(
        default=True,
        description="Skip contacts with duplicate phone numbers"
    )


class ContactBulkImportResult(BaseModel):
    """Schema for bulk import result."""

    total_rows: int = Field(..., description="Total rows in import")
    successful: int = Field(..., description="Successfully imported contacts")
    failed: int = Field(..., description="Failed imports")
    skipped: int = Field(..., description="Skipped duplicates")
    customer_id: str = Field(..., description="Customer ID that contacts were associated with")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Error details")
    created_contact_ids: List[str] = Field(default_factory=list, description="IDs of created contacts")


# Conversion Schemas

class LeadToOpportunityConversion(BaseModel):
    """Schema for converting a lead to an opportunity."""

    opportunity_name: str = Field(..., description="Deal name")
    amount: float = Field(..., description="Expected deal value")
    probability: int = Field(default=25, ge=0, le=100, description="Win probability (0-100%)")
    stage: OpportunityStage = Field(default=OpportunityStage.PROSPECTING)
    expected_close_date: Optional[datetime] = Field(None, description="Expected close date")
    description: Optional[str] = Field(None, description="Opportunity description")
    competitors: List[str] = Field(default_factory=list, description="Competing companies")
    next_step: Optional[str] = Field(None, description="Next action to take")
    keep_lead_active: bool = Field(default=False, description="Keep lead active after conversion")


class LeadToCustomerConversion(BaseModel):
    """Schema for converting a lead to a customer."""

    customer_type: CustomerType = Field(default=CustomerType.INDIVIDUAL)
    company_name: Optional[str] = Field(None, description="Company name (if business)")
    create_contact: bool = Field(default=True, description="Create contact record from lead")
    account_manager: Optional[str] = Field(None, description="Account manager user ID")
    tags: List[str] = Field(default_factory=list, description="Customer tags")


class OpportunityToCustomerConversion(BaseModel):
    """Schema for converting an opportunity to a customer."""

    create_new_customer: bool = Field(default=True, description="Create new customer or use existing")
    existing_customer_id: Optional[str] = Field(None, description="Existing customer ID to link")
    customer_type: CustomerType = Field(default=CustomerType.BUSINESS)
    account_manager: Optional[str] = Field(None, description="Account manager user ID")
    create_invoice: bool = Field(default=True, description="Create invoice from opportunity amount")
    invoice_due_days: int = Field(default=30, description="Invoice due in N days")
    invoice_notes: Optional[str] = Field(None, description="Invoice notes")
    create_project: bool = Field(default=False, description="Create project for this customer")
    project_name: Optional[str] = Field(None, description="Project name if creating")


class ConversionResponse(BaseModel):
    """Generic conversion response with created entities."""

    success: bool
    message: str
    lead_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    customer_id: Optional[str] = None
    contact_id: Optional[str] = None
    invoice_id: Optional[str] = None
    project_id: Optional[str] = None


class MarkWonRequest(BaseModel):
    """Schema for marking opportunity as won and triggering conversion workflow."""

    closed_date: Optional[datetime] = Field(None, description="Actual close date (defaults to now)")
    create_customer: bool = Field(default=True, description="Create customer from opportunity")
    existing_customer_id: Optional[str] = Field(None, description="Link to existing customer instead")
    customer_type: CustomerType = Field(default=CustomerType.BUSINESS)
    account_manager: Optional[str] = Field(None, description="Account manager user ID")
    create_invoice: bool = Field(default=True, description="Create invoice from opportunity amount")
    invoice_due_days: int = Field(default=30, description="Invoice due in N days")
    invoice_notes: Optional[str] = Field(None, description="Invoice notes")
    create_project: bool = Field(default=False, description="Create project for this customer")
    project_name: Optional[str] = Field(None, description="Project name if creating")


# Activity Schemas

class ActivityCreate(BaseModel):
    """Schema for creating an activity."""

    entity_type: str = Field(..., description="Type of entity (lead, customer, opportunity, contact)")
    entity_id: str = Field(..., description="ID of the entity this activity is related to")
    activity_type: str = Field(..., description="Type of activity")
    subject: str = Field(..., description="Activity subject/title")
    description: Optional[str] = Field(None, description="Detailed description")
    activity_date: Optional[datetime] = Field(None, description="When activity occurred (defaults to now)")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")
    call_outcome: Optional[str] = Field(None, description="Outcome of call")
    call_notes: Optional[str] = Field(None, description="Notes from call")
    email_subject: Optional[str] = Field(None, description="Email subject")
    email_sent: Optional[bool] = Field(None, description="True if sent, False if received")
    meeting_location: Optional[str] = Field(None, description="Meeting location")
    attendees: List[str] = Field(default_factory=list, description="Attendees")
    requires_follow_up: bool = Field(default=False, description="Requires follow-up")
    follow_up_date: Optional[datetime] = Field(None, description="When to follow up")
    attachments: List[str] = Field(default_factory=list, description="Attachments")
    related_activity_ids: List[str] = Field(default_factory=list, description="Related activities")
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class ActivityUpdate(BaseModel):
    """Schema for updating an activity."""

    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    activity_type: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    activity_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    call_outcome: Optional[str] = None
    call_notes: Optional[str] = None
    email_subject: Optional[str] = None
    email_sent: Optional[bool] = None
    meeting_location: Optional[str] = None
    attendees: Optional[List[str]] = None
    requires_follow_up: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    attachments: Optional[List[str]] = None
    related_activity_ids: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class ActivityStats(BaseModel):
    """Activity statistics response."""

    total_activities: int
    activities_by_type: Dict[str, int]
    activities_this_week: int
    activities_this_month: int
    pending_follow_ups: int
    completed_follow_ups: int
    top_performers: List[Dict[str, Any]]  # Top users by activity count


# Task Schemas

class CRMTaskCreate(BaseModel):
    """Schema for creating a CRM task."""

    entity_type: Optional[str] = Field(None, description="Type of entity (lead, customer, opportunity, contact)")
    entity_id: Optional[str] = Field(None, description="ID of the entity this task is related to")
    title: str = Field(..., description="Task title/subject")
    description: Optional[str] = Field(None, description="Detailed task description")
    priority: str = Field(default="medium", description="Task priority (low, medium, high, urgent)")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    reminder_date: Optional[datetime] = Field(None, description="When to send reminder")
    assigned_to: str = Field(..., description="User ID task is assigned to")
    estimated_hours: Optional[float] = Field(None, description="Estimated hours to complete")
    tags: List[str] = Field(default_factory=list, description="Task tags")
    related_activity_id: Optional[str] = Field(None, description="Related activity ID")
    related_task_ids: List[str] = Field(default_factory=list, description="Related task IDs")
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class CRMTaskUpdate(BaseModel):
    """Schema for updating a CRM task."""

    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    reminder_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    tags: Optional[List[str]] = None
    related_activity_id: Optional[str] = None
    related_task_ids: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class CRMTaskStats(BaseModel):
    """Task statistics response."""

    total_tasks: int
    tasks_by_status: Dict[str, int]
    tasks_by_priority: Dict[str, int]
    overdue_tasks: int
    due_today: int
    due_this_week: int
    completed_this_week: int
    completed_this_month: int
    average_completion_time_hours: Optional[float]
    top_assignees: List[Dict[str, Any]]  # Top users by task count
