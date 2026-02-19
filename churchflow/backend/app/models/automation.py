"""
Automation Models

Defines data models for automated workflows and reminder sequences in ChurchFlow.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class AutomationType(str, Enum):
    """Types of automation workflows"""
    EVENT_REMINDER = "event_reminder"
    MEMBER_ONBOARDING = "member_onboarding"
    POST_EVENT_FOLLOWUP = "post_event_followup"
    VOLUNTEER_RECRUITMENT = "volunteer_recruitment"
    GIVING_CAMPAIGN = "giving_campaign"


class ReminderTiming(str, Enum):
    """Reminder schedule options"""
    SEVEN_DAYS = "7_days_before"
    THREE_DAYS = "3_days_before"
    ONE_DAY = "1_day_before"
    MORNING_OF = "morning_of"
    CUSTOM = "custom"


class NotificationChannel(str, Enum):
    """Communication channels for automation"""
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    WHATSAPP = "whatsapp"


class AutomationStatus(str, Enum):
    """Status of automation workflow"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ReminderStep(BaseModel):
    """Individual reminder step in a sequence"""
    timing: ReminderTiming
    days_before: Optional[int] = None  # For custom timing
    hours_before: Optional[int] = None  # For more precise custom timing
    channel: NotificationChannel
    message_template: str
    enabled: bool = True

    # Execution tracking
    scheduled_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    status: Optional[str] = None  # pending, sent, failed
    recipients_count: Optional[int] = None
    success_count: Optional[int] = None
    failure_count: Optional[int] = None

    class Config:
        use_enum_values = True


class EventReminderConfig(BaseModel):
    """Configuration for event reminder automation"""
    enabled: bool = True
    reminder_steps: List[ReminderStep] = Field(default_factory=list)
    send_to_registered_only: bool = True
    include_qr_code: bool = True
    include_venue_details: bool = True

    class Config:
        use_enum_values = True


class MemberOnboardingConfig(BaseModel):
    """Configuration for new member onboarding automation"""
    enabled: bool = False
    welcome_delay_hours: int = 1  # Send welcome message 1 hour after registration
    follow_up_intervals: List[int] = [3, 7, 14]  # Days after welcome
    message_templates: List[str] = Field(default_factory=list)
    assign_to_cell_group: bool = False

    class Config:
        use_enum_values = True


class AutomationWorkflow(BaseModel):
    """Main automation workflow configuration"""
    id: Optional[str] = Field(None, alias="_id")
    organization_id: str
    automation_type: AutomationType
    name: str
    description: Optional[str] = None

    # Configuration based on type
    event_reminder_config: Optional[EventReminderConfig] = None
    member_onboarding_config: Optional[MemberOnboardingConfig] = None

    # Targeting
    conference_id: Optional[str] = None  # For event-specific automation
    branch_id: Optional[str] = None  # For branch-specific automation

    # Status
    status: AutomationStatus = AutomationStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # User ID

    # Execution tracking
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    last_execution_at: Optional[datetime] = None
    next_execution_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        use_enum_values = True


class ScheduledReminder(BaseModel):
    """Individual scheduled reminder instance"""
    id: Optional[str] = Field(None, alias="_id")
    workflow_id: str
    organization_id: str
    conference_id: str

    # Reminder details
    reminder_step: ReminderStep
    scheduled_at: datetime

    # Recipients
    recipient_ids: List[str] = Field(default_factory=list)  # Registration IDs
    recipient_count: int = 0

    # Status
    status: str = "pending"  # pending, executing, completed, failed
    executed_at: Optional[datetime] = None

    # Results
    sms_campaign_id: Optional[str] = None  # Link to SMS campaign if sent via SMS
    sent_count: int = 0
    delivered_count: int = 0
    failed_count: int = 0
    error_message: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        use_enum_values = True


class AutomationLog(BaseModel):
    """Audit log for automation executions"""
    id: Optional[str] = Field(None, alias="_id")
    workflow_id: str
    scheduled_reminder_id: Optional[str] = None
    organization_id: str

    # Event details
    event_type: str  # reminder_sent, workflow_started, workflow_completed, error
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
