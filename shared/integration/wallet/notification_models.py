"""
Notification Models for Wallet System

This module defines notification-related models for wallet transactions,
security alerts, and user notification preferences.

Author: KasaAI Team
Date: 2025-10-27
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    """Types of wallet notifications."""

    # Transaction notifications
    TRANSACTION_COMPLETED = "transaction_completed"
    DEPOSIT_COMPLETED = "deposit_completed"
    WITHDRAWAL_COMPLETED = "withdrawal_completed"
    TRANSACTION_FAILED = "transaction_failed"
    TRANSACTION_PENDING = "transaction_pending"

    # Payment method notifications
    PAYMENT_METHOD_ADDED = "payment_method_added"
    PAYMENT_METHOD_REMOVED = "payment_method_removed"
    PAYMENT_METHOD_UPDATED = "payment_method_updated"
    PAYMENT_METHOD_FAILED = "payment_method_failed"

    # Balance notifications
    LOW_BALANCE_ALERT = "low_balance_alert"
    AUTO_RELOAD_TRIGGERED = "auto_reload_triggered"
    AUTO_RELOAD_FAILED = "auto_reload_failed"
    BALANCE_THRESHOLD_REACHED = "balance_threshold_reached"

    # Security notifications
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_ALERT = "security_alert"
    LARGE_TRANSACTION_ALERT = "large_transaction_alert"
    MULTIPLE_FAILED_ATTEMPTS = "multiple_failed_attempts"

    # Reporting notifications
    WEEKLY_SUMMARY = "weekly_summary"
    MONTHLY_SUMMARY = "monthly_summary"
    TRANSACTION_REPORT = "transaction_report"

    # System notifications
    MAINTENANCE_ALERT = "maintenance_alert"
    SERVICE_UPDATE = "service_update"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"  # For future mobile app support
    IN_APP = "in_app"  # For in-app notifications


class NotificationStatus(str, Enum):
    """Status of notification delivery."""

    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    CANCELLED = "cancelled"


class NotificationFrequency(str, Enum):
    """Notification delivery frequency."""

    REAL_TIME = "real_time"
    DAILY_DIGEST = "daily_digest"
    WEEKLY_DIGEST = "weekly_digest"
    MONTHLY_DIGEST = "monthly_digest"
    DISABLED = "disabled"


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationPreference(BaseModel):
    """User's notification preferences."""

    user_id: str
    wallet_id: Optional[str] = None

    # Channel preferences
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = False
    in_app_enabled: bool = True

    # Category preferences
    transaction_notifications: bool = True
    security_notifications: bool = True
    balance_notifications: bool = True
    payment_method_notifications: bool = True
    marketing_notifications: bool = False

    # Frequency preferences
    notification_frequency: NotificationFrequency = NotificationFrequency.REAL_TIME
    digest_time: Optional[str] = "09:00"  # HH:MM format for digest delivery

    # Contact information
    email: Optional[str] = None
    phone_number: Optional[str] = None

    # Advanced preferences
    minimum_transaction_amount: Optional[float] = None  # Only notify for transactions above this amount
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = "22:00"  # HH:MM format
    quiet_hours_end: Optional[str] = "07:00"  # HH:MM format

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Notification(BaseModel):
    """Individual notification record."""

    id: str
    user_id: str
    wallet_id: Optional[str] = None

    # Notification details
    type: NotificationType
    channel: NotificationChannel
    priority: NotificationPriority = NotificationPriority.NORMAL

    # Content
    subject: str
    message: str
    html_message: Optional[str] = None
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None

    # Delivery tracking
    status: NotificationStatus = NotificationStatus.PENDING
    provider: Optional[str] = None  # email provider (resend, sendgrid) or SMS provider (twilio)
    provider_message_id: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    queued_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Related data
    transaction_id: Optional[str] = None
    payment_method_id: Optional[str] = None

    # Metadata
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NotificationTemplate(BaseModel):
    """Notification email/SMS template."""

    id: str
    name: str
    notification_type: NotificationType
    channel: NotificationChannel

    # Template content
    subject_template: str
    message_template: str
    html_template: Optional[str] = None

    # Template variables
    required_variables: List[str] = Field(default_factory=list)
    optional_variables: List[str] = Field(default_factory=list)

    # Configuration
    enabled: bool = True
    provider_specific_template_id: Optional[str] = None  # For provider-specific templates

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NotificationBatch(BaseModel):
    """Batch notification for digest delivery."""

    id: str
    user_id: str
    batch_type: str  # "daily_digest", "weekly_digest", "monthly_digest"

    # Batch content
    notifications: List[Notification] = Field(default_factory=list)
    summary_stats: Optional[Dict[str, Any]] = None

    # Delivery status
    status: NotificationStatus = NotificationStatus.PENDING
    scheduled_for: datetime
    sent_at: Optional[datetime] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NotificationStats(BaseModel):
    """Statistics for notification delivery."""

    user_id: str
    wallet_id: Optional[str] = None
    period_start: datetime
    period_end: datetime

    # Delivery stats
    total_sent: int = 0
    total_delivered: int = 0
    total_failed: int = 0
    total_bounced: int = 0

    # Channel stats
    email_sent: int = 0
    sms_sent: int = 0
    push_sent: int = 0
    in_app_sent: int = 0

    # Type stats
    transaction_notifications: int = 0
    security_notifications: int = 0
    balance_notifications: int = 0
    payment_method_notifications: int = 0

    # Performance
    average_delivery_time_seconds: Optional[float] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
