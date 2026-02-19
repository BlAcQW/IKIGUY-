"""
CRM (Customer Relationship Management) Models.

Handles customers, leads, opportunities, and contacts.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field, EmailStr
from enum import Enum

from .base import BaseModel


class LeadStatus(str, Enum):
    """Lead status enumeration."""

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    CONVERTED = "converted"


class LeadSource(str, Enum):
    """Lead source enumeration."""

    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    EMAIL_CAMPAIGN = "email_campaign"
    COLD_CALL = "cold_call"
    EVENT = "event"
    OTHER = "other"


class OpportunityStage(str, Enum):
    """Opportunity stage enumeration."""

    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class CustomerType(str, Enum):
    """Customer type enumeration."""

    INDIVIDUAL = "individual"
    BUSINESS = "business"
    GOVERNMENT = "government"


class Lead(BaseModel):
    """
    Lead model for potential customers.

    Tracks prospects before they become customers.
    """

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
    converted_at: Optional[datetime] = Field(None, description="When lead was converted")
    converted_to_customer_id: Optional[str] = Field(None, description="Customer ID after conversion")

    # Activity tracking integration (Phase 2.5)
    follow_up_date: Optional[datetime] = Field(None, description="Next scheduled follow-up")
    last_contacted: Optional[datetime] = Field(None, description="Last contact timestamp")
    next_action: Optional[str] = Field(None, description="Next action to take")
    last_activity_id: Optional[str] = Field(None, description="Most recent activity ID")
    activity_count: int = Field(default=0, description="Total activities logged")


class Customer(BaseModel):
    """
    Customer model for active customers.

    Central record for all customer information.
    """

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
    customer_since: datetime = Field(default_factory=datetime.utcnow)
    lifetime_value: float = Field(default=0.0, description="Total lifetime value")
    tags: List[str] = Field(default_factory=list, description="Customer tags")
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class Contact(BaseModel):
    """
    Contact model for individuals at customer organizations.

    Links individuals to customers (many contacts per customer).
    """

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


class Opportunity(BaseModel):
    """
    Sales opportunity model.

    Tracks potential deals and sales pipeline.
    """

    name: str = Field(..., description="Opportunity name")
    customer_id: Optional[str] = Field(None, description="Customer ID (if existing customer)")
    lead_id: Optional[str] = Field(None, description="Lead ID (if from lead)")
    amount: float = Field(..., description="Expected deal value")
    stage: OpportunityStage = Field(default=OpportunityStage.PROSPECTING)
    probability: int = Field(default=10, ge=0, le=100, description="Win probability (0-100%)")
    expected_close_date: Optional[datetime] = Field(None, description="Expected close date")
    closed_date: Optional[datetime] = Field(None, description="Actual close date")
    assigned_to: str = Field(..., description="Sales rep user ID")
    description: Optional[str] = Field(None, description="Opportunity description")
    competitors: List[str] = Field(default_factory=list, description="Competing companies")
    next_step: Optional[str] = Field(None, description="Next action to take")
    loss_reason: Optional[str] = Field(None, description="Reason for losing (if closed_lost)")

    # Activity tracking integration (Phase 2.5)
    next_step_date: Optional[datetime] = Field(None, description="When next step should be completed")
    last_activity_date: Optional[datetime] = Field(None, description="Last activity timestamp")
    last_activity_id: Optional[str] = Field(None, description="Most recent activity ID")
    activity_count: int = Field(default=0, description="Total activities logged")
    stage_entered_date: Optional[datetime] = Field(None, description="When current stage was entered")


class ActivityType(str, Enum):
    """Activity type enumeration."""

    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    NOTE = "note"
    TASK = "task"
    DEMO = "demo"
    PROPOSAL = "proposal"
    FOLLOW_UP = "follow_up"
    OTHER = "other"


class ActivityEntityType(str, Enum):
    """Entity types that can have activities."""

    LEAD = "lead"
    CUSTOMER = "customer"
    OPPORTUNITY = "opportunity"
    CONTACT = "contact"


class Activity(BaseModel):
    """
    Activity tracking model for CRM entities.

    Tracks all interactions with leads, customers, opportunities, and contacts.
    Supports calls, emails, meetings, notes, and other activities.
    """

    # Entity linking
    entity_type: ActivityEntityType = Field(..., description="Type of entity (lead, customer, opportunity, contact)")
    entity_id: str = Field(..., description="ID of the entity this activity is related to")

    # Activity details
    activity_type: ActivityType = Field(..., description="Type of activity")
    subject: str = Field(..., description="Activity subject/title")
    description: Optional[str] = Field(None, description="Detailed description of the activity")

    # User tracking
    performed_by: str = Field(..., description="User ID who performed this activity")

    # Timing
    activity_date: datetime = Field(default_factory=datetime.utcnow, description="When activity occurred")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes (for calls/meetings)")

    # Call specifics
    call_outcome: Optional[str] = Field(None, description="Outcome of call (answered, voicemail, no_answer, etc.)")
    call_notes: Optional[str] = Field(None, description="Notes from the call")

    # Email specifics
    email_subject: Optional[str] = Field(None, description="Email subject line")
    email_sent: Optional[bool] = Field(None, description="True if email was sent, False if received")

    # Meeting specifics
    meeting_location: Optional[str] = Field(None, description="Meeting location or video link")
    attendees: List[str] = Field(default_factory=list, description="List of attendee names or IDs")

    # Follow-up tracking
    requires_follow_up: bool = Field(default=False, description="Whether this activity requires follow-up")
    follow_up_date: Optional[datetime] = Field(None, description="When to follow up")
    follow_up_completed: bool = Field(default=False, description="Whether follow-up was completed")
    follow_up_completed_at: Optional[datetime] = Field(None, description="When follow-up was completed")

    # Attachments and links
    attachments: List[str] = Field(default_factory=list, description="File paths or URLs to attachments")
    related_activity_ids: List[str] = Field(default_factory=list, description="Related activity IDs (e.g., follow-up to a previous activity)")

    # Custom fields for flexibility
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Additional custom data")


class TaskPriority(str, Enum):
    """Task priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """Task status enumeration."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CRMTask(BaseModel):
    """
    CRM Task/Todo model.

    Manages tasks and todos related to CRM entities (leads, customers, opportunities, contacts).
    Supports priority levels, scheduling, assignment, and status tracking.
    """

    # Entity linking
    entity_type: Optional[ActivityEntityType] = Field(None, description="Type of entity (lead, customer, opportunity, contact)")
    entity_id: Optional[str] = Field(None, description="ID of the entity this task is related to")

    # Task details
    title: str = Field(..., description="Task title/subject")
    description: Optional[str] = Field(None, description="Detailed task description")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority level")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="Task status")

    # Scheduling
    due_date: Optional[datetime] = Field(None, description="Task due date")
    reminder_date: Optional[datetime] = Field(None, description="When to send reminder")
    start_date: Optional[datetime] = Field(None, description="When task was started")
    completed_date: Optional[datetime] = Field(None, description="When task was completed")

    # Assignment
    assigned_to: str = Field(..., description="User ID task is assigned to")
    assigned_by: Optional[str] = Field(None, description="User ID who assigned the task")

    # Related data
    related_activity_id: Optional[str] = Field(None, description="Related activity ID")
    related_task_ids: List[str] = Field(default_factory=list, description="Related task IDs (dependencies)")

    # Task metadata
    estimated_hours: Optional[float] = Field(None, description="Estimated hours to complete")
    actual_hours: Optional[float] = Field(None, description="Actual hours spent")
    tags: List[str] = Field(default_factory=list, description="Task tags")

    # Custom fields
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Additional custom data")
