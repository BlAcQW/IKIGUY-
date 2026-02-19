"""
Campaign Event Definitions

This module defines standard event types and data structures for campaign
real-time updates via SSE (Server-Sent Events).

Event Types:
- SMS Campaigns: sms_progress, sms_status_change
- Voice Campaigns: voice_progress, call_completed, voice_status_change
- WhatsApp Campaigns: whatsapp_progress, whatsapp_status_change
- General: campaign_completed, campaign_error

Usage Example:
    from shared.services.campaign_events import (
        SMSProgressEvent,
        VoiceProgressEvent,
        create_sms_progress_event
    )

    # Create an event
    event = create_sms_progress_event(
        campaign_id="abc123",
        total=100,
        sent=50,
        failed=2
    )

    # Publish via SSE
    await sse_publisher.publish(
        event.campaign_id,
        event.event_type,
        event.to_dict()
    )
"""

from typing import Dict, Any, Optional, Literal
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


# ==================== Event Type Constants ====================

class EventType(str, Enum):
    """Standard event types for campaigns"""
    # SMS Events
    SMS_PROGRESS = "sms_progress"
    SMS_STATUS_CHANGE = "sms_status_change"
    SMS_MESSAGE_SENT = "sms_message_sent"
    SMS_MESSAGE_FAILED = "sms_message_failed"

    # Voice Events
    VOICE_PROGRESS = "voice_progress"
    VOICE_STATUS_CHANGE = "voice_status_change"
    CALL_COMPLETED = "call_completed"
    CALL_FAILED = "call_failed"
    CALL_STARTED = "call_started"

    # WhatsApp Events
    WHATSAPP_PROGRESS = "whatsapp_progress"
    WHATSAPP_STATUS_CHANGE = "whatsapp_status_change"
    WHATSAPP_MESSAGE_SENT = "whatsapp_message_sent"

    # General Events
    CAMPAIGN_COMPLETED = "campaign_completed"
    CAMPAIGN_ERROR = "campaign_error"
    AUDIENCE_PROCESSING = "audience_processing"
    INITIAL = "initial"


class CampaignStatus(str, Enum):
    """Campaign status values"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ==================== Base Event ====================

@dataclass
class BaseCampaignEvent:
    """Base class for all campaign events"""
    campaign_id: str
    event_type: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


# ==================== SMS Campaign Events ====================

@dataclass
class SMSProgressEvent(BaseCampaignEvent):
    """SMS campaign progress update event"""
    event_type: str = EventType.SMS_PROGRESS
    timestamp: str = ""

    # Progress data
    total_recipients: int = 0
    sent: int = 0
    delivered: int = 0
    failed: int = 0
    pending: int = 0

    # Cost
    total_cost: float = 0.0

    # Status
    status: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class SMSStatusChangeEvent(BaseCampaignEvent):
    """SMS campaign status change event"""
    event_type: str = EventType.SMS_STATUS_CHANGE
    timestamp: str = ""

    old_status: str
    new_status: str
    reason: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class SMSMessageSentEvent(BaseCampaignEvent):
    """Individual SMS message sent event"""
    event_type: str = EventType.SMS_MESSAGE_SENT
    timestamp: str = ""

    message_id: str
    recipient_name: str
    recipient_phone: str
    cost: float

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


# ==================== Voice Campaign Events ====================

@dataclass
class VoiceProgressEvent(BaseCampaignEvent):
    """Voice campaign progress update event"""
    event_type: str = EventType.VOICE_PROGRESS
    timestamp: str = ""

    # Progress data
    calls_made: int = 0
    calls_total: int = 0
    success_count: int = 0
    failed_count: int = 0
    in_progress_count: int = 0

    # Metrics
    success_rate: float = 0.0
    avg_duration: float = 0.0

    # Cost
    current_cost: float = 0.0

    # Status
    status: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

        # Calculate success rate if not provided
        if self.calls_made > 0 and self.success_rate == 0.0:
            self.success_rate = round((self.success_count / self.calls_made) * 100, 2)


@dataclass
class CallCompletedEvent(BaseCampaignEvent):
    """Individual call completed event"""
    event_type: str = EventType.CALL_COMPLETED
    timestamp: str = ""

    # Call info
    call_id: str
    contact_name: str
    phone_number: str

    # Call metrics
    duration: int  # seconds
    status: Literal["success", "failed"]

    # Optional data
    transcript_available: bool = False
    summary: Optional[str] = None
    cost: float = 0.0
    error_message: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class CallStartedEvent(BaseCampaignEvent):
    """Call started event"""
    event_type: str = EventType.CALL_STARTED
    timestamp: str = ""

    call_id: str
    contact_name: str
    phone_number: str

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class VoiceStatusChangeEvent(BaseCampaignEvent):
    """Voice campaign status change event"""
    event_type: str = EventType.VOICE_STATUS_CHANGE
    timestamp: str = ""

    old_status: str
    new_status: str
    reason: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


# ==================== WhatsApp Campaign Events ====================

@dataclass
class WhatsAppProgressEvent(BaseCampaignEvent):
    """WhatsApp campaign progress update event"""
    event_type: str = EventType.WHATSAPP_PROGRESS
    timestamp: str = ""

    # Progress data
    total_recipients: int = 0
    sent: int = 0
    delivered: int = 0
    read: int = 0
    failed: int = 0
    pending: int = 0

    # Cost
    total_cost: float = 0.0

    # Status
    status: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


# ==================== General Events ====================

@dataclass
class CampaignCompletedEvent(BaseCampaignEvent):
    """Campaign completion event"""
    event_type: str = EventType.CAMPAIGN_COMPLETED
    timestamp: str = ""

    message: str = "Campaign completed successfully"
    final_stats: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class CampaignErrorEvent(BaseCampaignEvent):
    """Campaign error event"""
    event_type: str = EventType.CAMPAIGN_ERROR
    timestamp: str = ""

    error_message: str
    error_type: Optional[str] = None
    recoverable: bool = False

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class AudienceProcessingEvent(BaseCampaignEvent):
    """Audience processing progress event"""
    event_type: str = EventType.AUDIENCE_PROCESSING
    timestamp: str = ""

    phase: str  # "loading", "filtering", "building_queue", "complete"
    contacts_discovered: int = 0
    contacts_filtered: int = 0
    queue_size: int = 0
    message: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


# ==================== Helper Functions ====================

def create_sms_progress_event(
    campaign_id: str,
    total: int,
    sent: int,
    delivered: int = 0,
    failed: int = 0,
    pending: int = 0,
    total_cost: float = 0.0,
    status: Optional[str] = None
) -> SMSProgressEvent:
    """
    Create an SMS progress event.

    Args:
        campaign_id: Campaign ID
        total: Total recipients
        sent: Messages sent
        delivered: Messages delivered
        failed: Messages failed
        pending: Messages pending
        total_cost: Total cost
        status: Campaign status

    Returns:
        SMSProgressEvent instance
    """
    return SMSProgressEvent(
        campaign_id=campaign_id,
        total_recipients=total,
        sent=sent,
        delivered=delivered,
        failed=failed,
        pending=pending,
        total_cost=total_cost,
        status=status
    )


def create_voice_progress_event(
    campaign_id: str,
    calls_made: int,
    calls_total: int,
    success_count: int = 0,
    failed_count: int = 0,
    current_cost: float = 0.0,
    status: Optional[str] = None
) -> VoiceProgressEvent:
    """
    Create a voice progress event.

    Args:
        campaign_id: Campaign ID
        calls_made: Total calls made
        calls_total: Total calls to make
        success_count: Successful calls
        failed_count: Failed calls
        current_cost: Current cost
        status: Campaign status

    Returns:
        VoiceProgressEvent instance
    """
    return VoiceProgressEvent(
        campaign_id=campaign_id,
        calls_made=calls_made,
        calls_total=calls_total,
        success_count=success_count,
        failed_count=failed_count,
        current_cost=current_cost,
        status=status
    )


def create_call_completed_event(
    campaign_id: str,
    call_id: str,
    contact_name: str,
    phone_number: str,
    duration: int,
    status: Literal["success", "failed"],
    transcript_available: bool = False,
    summary: Optional[str] = None,
    cost: float = 0.0,
    error_message: Optional[str] = None
) -> CallCompletedEvent:
    """
    Create a call completed event.

    Args:
        campaign_id: Campaign ID
        call_id: Unique call ID
        contact_name: Contact name
        phone_number: Phone number
        duration: Call duration in seconds
        status: Call status
        transcript_available: Whether transcript is available
        summary: Optional call summary
        cost: Call cost
        error_message: Optional error message

    Returns:
        CallCompletedEvent instance
    """
    return CallCompletedEvent(
        campaign_id=campaign_id,
        call_id=call_id,
        contact_name=contact_name,
        phone_number=phone_number,
        duration=duration,
        status=status,
        transcript_available=transcript_available,
        summary=summary,
        cost=cost,
        error_message=error_message
    )
