"""
Automation Schemas

Pydantic schemas for automation API requests and responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.automation import (
    AutomationType,
    ReminderTiming,
    NotificationChannel,
    AutomationStatus,
    ReminderStep,
    EventReminderConfig,
    MemberOnboardingConfig
)


class CreateAutomationWorkflowRequest(BaseModel):
    """Request to create a new automation workflow"""
    automation_type: AutomationType
    name: str
    description: Optional[str] = None

    # Configuration based on type
    event_reminder_config: Optional[EventReminderConfig] = None
    member_onboarding_config: Optional[MemberOnboardingConfig] = None

    # Targeting
    conference_id: Optional[str] = None
    branch_id: Optional[str] = None

    class Config:
        use_enum_values = True


class UpdateAutomationWorkflowRequest(BaseModel):
    """Request to update an existing automation workflow"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[AutomationStatus] = None

    # Configuration updates
    event_reminder_config: Optional[EventReminderConfig] = None
    member_onboarding_config: Optional[MemberOnboardingConfig] = None

    class Config:
        use_enum_values = True


class AutomationWorkflowResponse(BaseModel):
    """Response for automation workflow"""
    id: str = Field(..., alias="_id")
    organization_id: str
    automation_type: str
    name: str
    description: Optional[str] = None

    # Configuration
    event_reminder_config: Optional[EventReminderConfig] = None
    member_onboarding_config: Optional[MemberOnboardingConfig] = None

    # Targeting
    conference_id: Optional[str] = None
    branch_id: Optional[str] = None

    # Status
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: str

    # Execution stats
    total_executions: int
    successful_executions: int
    failed_executions: int
    last_execution_at: Optional[datetime] = None
    next_execution_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class ScheduledReminderResponse(BaseModel):
    """Response for scheduled reminder"""
    id: str = Field(..., alias="_id")
    workflow_id: str
    organization_id: str
    conference_id: str

    # Reminder details
    reminder_step: ReminderStep
    scheduled_at: datetime

    # Recipients
    recipient_count: int

    # Status
    status: str
    executed_at: Optional[datetime] = None

    # Results
    sms_campaign_id: Optional[str] = None
    sent_count: int
    delivered_count: int
    failed_count: int
    error_message: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class CreateReminderStepRequest(BaseModel):
    """Request to create/update a reminder step"""
    timing: ReminderTiming
    days_before: Optional[int] = None
    hours_before: Optional[int] = None
    channel: NotificationChannel
    message_template: str
    enabled: bool = True

    class Config:
        use_enum_values = True


class AutomationDashboardResponse(BaseModel):
    """Dashboard statistics for automation"""
    total_workflows: int
    active_workflows: int
    paused_workflows: int

    # Scheduled reminders
    pending_reminders: int
    upcoming_reminders_24h: int

    # Execution stats
    total_executions_30d: int
    successful_executions_30d: int
    failed_executions_30d: int
    success_rate: float  # 0.0 to 1.0

    # Recent activity
    recent_workflows: List[AutomationWorkflowResponse]
    upcoming_reminders: List[ScheduledReminderResponse]


class ExecuteWorkflowRequest(BaseModel):
    """Request to manually execute a workflow"""
    workflow_id: str
    conference_id: Optional[str] = None  # Required for event reminder workflows
    test_mode: bool = False  # If true, only sends to admin/creator


class BulkScheduleRemindersRequest(BaseModel):
    """Request to bulk schedule reminders for a conference"""
    conference_id: str
    workflow_id: Optional[str] = None  # Use existing workflow or create default
