"""
Voice call models for EstateFlow.

Pydantic models for voice agent calls, configuration, and statistics.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CallStatus(str, Enum):
    QUEUED = "queued"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    CANCELLED = "cancelled"


class CallDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CallOutcome(str, Enum):
    TOUR_SCHEDULED = "tour_scheduled"
    INFORMATION_PROVIDED = "information_provided"
    TRANSFERRED = "transferred"
    CALLBACK_REQUESTED = "callback_requested"
    VOICEMAIL = "voicemail"
    NO_OUTCOME = "no_outcome"


class VoiceCall(BaseModel):
    id: str = ""
    organization_id: str = ""
    caller_name: str = "Unknown"
    caller_phone: str = ""
    direction: CallDirection = CallDirection.INBOUND
    status: CallStatus = CallStatus.COMPLETED
    outcome: CallOutcome = CallOutcome.NO_OUTCOME
    duration_seconds: int = 0
    property_id: Optional[str] = None
    property_name: Optional[str] = None
    assistant_id: Optional[str] = None
    transcript: Optional[str] = None
    recording_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None


class VoiceConfig(BaseModel):
    organization_id: str = ""
    is_active: bool = False
    assistant_id: Optional[str] = None
    phone_number: Optional[str] = None
    greeting_message: str = "Hello! Thank you for calling. How can I help you with your property inquiry?"
    transfer_phone: Optional[str] = None
    working_hours_start: str = "09:00"
    working_hours_end: str = "17:00"
    after_hours_message: str = "We are currently closed. Please leave a message and we'll call you back."
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VoiceConfigUpdate(BaseModel):
    is_active: Optional[bool] = None
    assistant_id: Optional[str] = None
    phone_number: Optional[str] = None
    greeting_message: Optional[str] = None
    transfer_phone: Optional[str] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    after_hours_message: Optional[str] = None


class CallStats(BaseModel):
    total_calls: int = 0
    calls_today: int = 0
    avg_duration_seconds: int = 0
    tours_scheduled: int = 0
    satisfaction_rate: float = 0.0
    calls_by_outcome: Dict[str, int] = Field(default_factory=dict)
    calls_by_status: Dict[str, int] = Field(default_factory=dict)


class CallListResponse(BaseModel):
    calls: List[VoiceCall]
    total: int
    limit: int
    offset: int
