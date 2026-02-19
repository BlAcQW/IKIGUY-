"""
Integration Models for ChurchFlow

Defines data models for external service integrations including:
- Google Calendar sync configuration
- Zapier webhook configuration
- Email campaign settings
- Integration status tracking
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr, HttpUrl
from enum import Enum


class IntegrationType(str, Enum):
    """Type of external integration."""
    GOOGLE_CALENDAR = "google_calendar"
    ZAPIER = "zapier"
    EMAIL_CAMPAIGN = "email_campaign"
    STRIPE_BILLING = "stripe_billing"


class IntegrationStatus(str, Enum):
    """Status of an integration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING_AUTH = "pending_auth"


class WebhookEventType(str, Enum):
    """Types of events that trigger webhooks."""
    CONFERENCE_CREATED = "conference.created"
    CONFERENCE_UPDATED = "conference.updated"
    CONFERENCE_DELETED = "conference.deleted"
    REGISTRATION_CREATED = "registration.created"
    REGISTRATION_UPDATED = "registration.updated"
    REGISTRATION_CHECKED_IN = "registration.checked_in"
    PAYMENT_RECEIVED = "payment.received"
    SMS_SENT = "sms.sent"
    EMAIL_SENT = "email.sent"


class GoogleCalendarConfig(BaseModel):
    """Google Calendar integration configuration."""
    calendar_id: str = Field("primary", description="Google Calendar ID")
    credentials_json: Optional[Dict[str, Any]] = Field(None, description="Service account credentials")
    auto_sync_events: bool = Field(True, description="Automatically sync new events")
    two_way_sync: bool = Field(False, description="Enable two-way sync")
    sync_interval_minutes: int = Field(30, ge=5, le=1440, description="Sync interval (5-1440 minutes)")
    include_registration_count: bool = Field(True, description="Include registration count in event description")

    class Config:
        json_schema_extra = {
            "example": {
                "calendar_id": "primary",
                "auto_sync_events": True,
                "two_way_sync": False,
                "sync_interval_minutes": 30,
                "include_registration_count": True
            }
        }


class ZapierWebhookConfig(BaseModel):
    """Zapier webhook integration configuration."""
    webhook_url: HttpUrl = Field(..., description="Zapier webhook URL")
    enabled_events: List[WebhookEventType] = Field(
        default_factory=list,
        description="Events that trigger this webhook"
    )
    secret_key: Optional[str] = Field(None, description="Secret key for webhook verification")
    retry_on_failure: bool = Field(True, description="Retry failed webhook calls")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")
    timeout_seconds: int = Field(30, ge=5, le=120, description="Request timeout")

    class Config:
        json_schema_extra = {
            "example": {
                "webhook_url": "https://hooks.zapier.com/hooks/catch/123456/abcdef/",
                "enabled_events": ["registration.created", "registration.checked_in"],
                "retry_on_failure": True,
                "max_retries": 3,
                "timeout_seconds": 30
            }
        }


class EmailCampaignConfig(BaseModel):
    """Email campaign integration configuration."""
    smtp_host: Optional[str] = Field(None, description="SMTP server host")
    smtp_port: Optional[int] = Field(587, description="SMTP server port")
    smtp_username: Optional[str] = Field(None, description="SMTP username")
    smtp_password: Optional[str] = Field(None, description="SMTP password (encrypted)")
    from_email: EmailStr = Field(..., description="Default from email address")
    from_name: str = Field(..., description="Default from name")
    use_sendgrid: bool = Field(False, description="Use SendGrid API instead of SMTP")
    sendgrid_api_key: Optional[str] = Field(None, description="SendGrid API key")
    track_opens: bool = Field(True, description="Track email opens")
    track_clicks: bool = Field(True, description="Track link clicks")

    class Config:
        json_schema_extra = {
            "example": {
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "from_email": "church@example.com",
                "from_name": "Church Admin",
                "track_opens": True,
                "track_clicks": True
            }
        }


class IntegrationConfig(BaseModel):
    """Complete integration configuration for an organization."""
    id: Optional[str] = Field(None, description="MongoDB _id")
    organization_id: str = Field(..., description="Organization ID")
    integration_type: IntegrationType = Field(..., description="Type of integration")
    status: IntegrationStatus = Field(IntegrationStatus.INACTIVE, description="Integration status")

    # Integration-specific configs (only one should be populated)
    google_calendar: Optional[GoogleCalendarConfig] = None
    zapier_webhook: Optional[ZapierWebhookConfig] = None
    email_campaign: Optional[EmailCampaignConfig] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_sync_at: Optional[datetime] = Field(None, description="Last successful sync timestamp")
    error_message: Optional[str] = Field(None, description="Last error message if status is ERROR")
    sync_count: int = Field(0, description="Total number of successful syncs")

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": "org_123",
                "integration_type": "google_calendar",
                "status": "active",
                "google_calendar": {
                    "calendar_id": "primary",
                    "auto_sync_events": True
                }
            }
        }


class CalendarEventMapping(BaseModel):
    """Mapping between ChurchFlow conference and Google Calendar event."""
    id: Optional[str] = Field(None, description="MongoDB _id")
    organization_id: str = Field(..., description="Organization ID")
    conference_id: str = Field(..., description="ChurchFlow conference ID")
    google_event_id: str = Field(..., description="Google Calendar event ID")
    google_calendar_id: str = Field(..., description="Google Calendar ID")
    last_synced_at: datetime = Field(default_factory=datetime.utcnow)
    conference_updated_at: datetime = Field(..., description="Conference last update time")

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": "org_123",
                "conference_id": "conf_456",
                "google_event_id": "evt_789",
                "google_calendar_id": "primary"
            }
        }


class WebhookDelivery(BaseModel):
    """Record of a webhook delivery attempt."""
    id: Optional[str] = Field(None, description="MongoDB _id")
    organization_id: str = Field(..., description="Organization ID")
    webhook_url: str = Field(..., description="Webhook URL")
    event_type: WebhookEventType = Field(..., description="Event type")
    payload: Dict[str, Any] = Field(..., description="Webhook payload")

    # Delivery status
    success: bool = Field(False, description="Whether delivery succeeded")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    response_body: Optional[str] = Field(None, description="Response body")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    # Retry tracking
    attempt_number: int = Field(1, description="Attempt number (1 = first try)")
    max_attempts: int = Field(3, description="Maximum attempts allowed")
    next_retry_at: Optional[datetime] = Field(None, description="Next retry time")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = Field(None, description="Successful delivery time")

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": "org_123",
                "webhook_url": "https://hooks.zapier.com/hooks/catch/123/abc/",
                "event_type": "registration.created",
                "payload": {"registration_id": "reg_789"},
                "success": True,
                "status_code": 200
            }
        }


class IntegrationHealth(BaseModel):
    """Health status of an integration."""
    integration_type: IntegrationType
    status: IntegrationStatus
    last_sync_at: Optional[datetime] = None
    error_message: Optional[str] = None
    success_rate: float = Field(0.0, ge=0.0, le=1.0, description="Success rate (0-1)")
    total_syncs: int = Field(0, description="Total sync attempts")
    successful_syncs: int = Field(0, description="Successful syncs")
    failed_syncs: int = Field(0, description="Failed syncs")

    class Config:
        json_schema_extra = {
            "example": {
                "integration_type": "google_calendar",
                "status": "active",
                "last_sync_at": "2025-12-05T10:00:00Z",
                "success_rate": 0.95,
                "total_syncs": 100,
                "successful_syncs": 95,
                "failed_syncs": 5
            }
        }


class IntegrationDashboard(BaseModel):
    """Dashboard showing all integrations for an organization."""
    organization_id: str
    organization_name: str
    integrations: List[IntegrationHealth] = Field(default_factory=list)
    total_active_integrations: int = 0
    total_inactive_integrations: int = 0
    total_error_integrations: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": "org_123",
                "organization_name": "First Baptist Church",
                "integrations": [],
                "total_active_integrations": 2,
                "total_inactive_integrations": 1,
                "total_error_integrations": 0
            }
        }
