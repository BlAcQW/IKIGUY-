"""
Campaign models for automation-based calling campaigns.

This module defines models for managing audience-based calling campaigns
that are linked to automation configurations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class CampaignConfig(BaseModel):
    """Configuration for campaign execution."""

    call_delay_seconds: int = Field(
        default=30,
        description="Delay between individual calls in seconds"
    )
    batch_interval_seconds: int = Field(
        default=10,
        description="Interval delay between batches of concurrent calls in seconds"
    )
    max_retries: int = Field(
        default=2,
        description="Maximum retry attempts for failed calls"
    )
    retry_on_no_answer: bool = Field(
        default=True,
        description="Whether to retry when no answer"
    )
    max_concurrent_calls: int = Field(
        default=1,
        description="Maximum number of concurrent calls"
    )
    start_time: Optional[str] = Field(
        default=None,
        description="Daily start time (HH:MM format in UTC) - campaign will resume at this time. Example: '09:00'"
    )
    pause_time: Optional[str] = Field(
        default=None,
        description="Daily pause time (HH:MM format in UTC) - campaign will pause at this time. Example: '18:00'"
    )
    auto_start: Optional[bool] = Field(
        default=False,
        description="Auto-start campaign at start_time when creating. If true and start_time is set, campaign will start automatically at that time."
    )
    use_asterisk: bool = Field(
        default=False,
        description="Use Asterisk for calls instead of VAPI. When enabled, calls go through our Asterisk server with local TTS/ASR/LLM providers."
    )


class CampaignProgress(BaseModel):
    """Progress tracking for campaign execution."""

    total_contacts: int = Field(default=0, description="Total number of contacts")
    triggered: int = Field(default=0, description="Number of calls triggered (initiated)")
    completed: int = Field(default=0, description="Number of calls completed (finished)")
    called: int = Field(default=0, description="Number of contacts called")
    successful: int = Field(default=0, description="Number of successful calls")
    failed: int = Field(default=0, description="Number of failed calls")
    no_answer: int = Field(default=0, description="Number of no-answer calls")
    pending: int = Field(default=0, description="Number of pending calls")
    conversion_count: int = Field(default=0, description="Number of conversions")
    current_contact_index: int = Field(default=0, description="Current position in contact list")

    @property
    def conversion_rate(self) -> float:
        """Calculate conversion rate percentage."""
        if self.called == 0:
            return 0.0
        return (self.conversion_count / self.called) * 100

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.called == 0:
            return 0.0
        return (self.successful / self.called) * 100

    @property
    def progress_percentage(self) -> float:
        """Calculate overall progress percentage."""
        if self.total_contacts == 0:
            return 0.0
        return (self.called / self.total_contacts) * 100


class AutomationCampaign(BaseModel):
    """
    Automation campaign model linking an automation to an audience for sequential calling.

    This model tracks the execution state of a campaign including progress,
    configuration, and timing information.
    """

    id: Optional[str] = Field(default=None, description="Campaign ID")
    automation_id: str = Field(..., description="Linked automation configuration ID")
    automation_name: Optional[str] = Field(None, description="Automation name (cached)")
    audience_id: str = Field(..., description="Linked audience ID")
    audience_name: Optional[str] = Field(None, description="Audience name (cached)")
    phone_id: Optional[str] = Field(None, description="VAPI phone number ID to use for calls")
    user_id: str = Field(..., description="User who created the campaign")
    organization_id: Optional[str] = Field(None, description="Organization ID")

    status: str = Field(
        default="pending",
        description="Campaign status: pending, running, paused, completed, failed"
    )

    progress: CampaignProgress = Field(
        default_factory=CampaignProgress,
        description="Campaign progress tracking"
    )

    config: CampaignConfig = Field(
        default_factory=CampaignConfig,
        description="Campaign configuration"
    )

    # Recently called numbers for real-time display (last 20 numbers)
    recently_called_numbers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Recently called phone numbers with timestamps for real-time display"
    )

    # Analytics
    total_cost: float = Field(default=0.0, description="Total cost of all calls (VAPI + phone costs)")
    total_vapi_cost_usd: float = Field(default=0.0, description="Total VAPI platform cost in USD")
    total_phone_cost_ghc: float = Field(default=0.0, description="Total phone billing cost in GHC")
    avg_call_duration: float = Field(default=0.0, description="Average call duration in seconds")

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    started_at: Optional[datetime] = Field(None, description="Campaign start timestamp")
    paused_at: Optional[datetime] = Field(None, description="Last pause timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    # Error tracking
    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class CampaignContact(BaseModel):
    """Contact information for campaign call."""

    phone: str = Field(..., description="Phone number")
    name: Optional[str] = Field(None, description="Contact name")
    email: Optional[str] = Field(None, description="Contact email")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class CallObjection(BaseModel):
    """Objection extracted from call transcript."""

    category: str = Field(..., description="Objection category: price, timing, interest, information")
    text: str = Field(..., description="Objection text/keyword")
    context: Optional[str] = Field(None, description="Surrounding context from transcript")
    confidence: float = Field(default=1.0, description="Confidence score (0-1)")


class CallOutcome(BaseModel):
    """Detailed outcome analysis of a call."""

    outcome: str = Field(
        ...,
        description="Call outcome: converted, objection, no_answer, error, neutral"
    )
    conversion_signals: int = Field(
        default=0,
        description="Number of positive conversion signals detected"
    )
    objections: List[CallObjection] = Field(
        default_factory=list,
        description="List of objections detected"
    )
    sentiment: Optional[str] = Field(
        None,
        description="Overall sentiment: positive, negative, neutral, mixed"
    )
    confidence: float = Field(
        default=0.0,
        description="Confidence in outcome assessment (0-1)"
    )


class CampaignCall(BaseModel):
    """
    Individual call record within a campaign.

    Tracks the details and outcome of each call made as part of a campaign.
    """

    id: Optional[str] = Field(default=None, description="Call record ID")
    campaign_id: str = Field(..., description="Parent campaign ID")
    automation_id: str = Field(..., description="Automation configuration ID")

    # Contact information
    contact: CampaignContact = Field(..., description="Contact being called")
    contact_index: int = Field(..., description="Position in campaign contact list")

    # Call details
    call_id: Optional[str] = Field(None, description="VAPI call ID or Asterisk uniqueid")
    phone_id: Optional[str] = Field(None, description="Phone number ID used for this call")
    assistant_id: Optional[str] = Field(None, description="VAPI assistant ID used for this call")
    use_asterisk: bool = Field(default=False, description="Whether this call used Asterisk instead of VAPI")
    status: str = Field(
        default="pending",
        description="Call status: pending, calling, completed, failed, no_answer"
    )

    # Outcome analysis
    outcome: Optional[CallOutcome] = Field(None, description="Call outcome analysis")

    # Call metrics
    duration: Optional[int] = Field(None, description="Call duration in seconds")
    cost: Optional[float] = Field(None, description="Call cost")

    # Call content
    transcript: Optional[str] = Field(None, description="Call transcript")
    ai_summary: Optional[str] = Field(None, description="AI-generated summary")
    recording_url: Optional[str] = Field(None, description="Call recording URL")

    # Retry tracking
    attempt_number: int = Field(default=1, description="Attempt number (for retries)")
    max_attempts: int = Field(default=3, description="Maximum retry attempts")
    retry_reason: Optional[str] = Field(None, description="Reason for retry")

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    called_at: Optional[datetime] = Field(None, description="Call initiation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Call completion timestamp")

    # Error tracking
    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class CampaignCreateRequest(BaseModel):
    """Request model for creating a campaign."""

    automation_id: str = Field(..., description="Automation configuration ID")
    audience_id: str = Field(..., description="Audience ID to call")
    phone_id: Optional[str] = Field(None, description="VAPI phone number ID to use for calls")
    config: Optional[CampaignConfig] = Field(
        None,
        description="Campaign configuration (optional, uses defaults if not provided)"
    )


class CampaignStatusResponse(BaseModel):
    """Response model for campaign status."""

    campaign: AutomationCampaign
    current_contact: Optional[CampaignContact] = None
    next_contact: Optional[CampaignContact] = None
    estimated_completion: Optional[datetime] = None
    estimated_total_cost: Optional[float] = None


class CampaignAnalyticsResponse(BaseModel):
    """Response model for campaign analytics."""

    campaign_id: str
    automation_name: str
    audience_name: str

    # Progress metrics
    progress: CampaignProgress

    # Outcome distribution
    outcome_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Distribution of call outcomes"
    )

    # Top objections
    top_objections: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most common objections with counts"
    )

    # Sentiment distribution
    sentiment_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Distribution of sentiment"
    )

    # Cost metrics
    total_cost: float
    cost_per_call: float
    cost_per_conversion: Optional[float] = None

    # Time metrics
    avg_call_duration: float
    campaign_duration: Optional[float] = None  # In seconds

    # Timeline data for charts
    timeline_data: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Timeline data for visualization"
    )

    # Recent calls
    recent_calls: List[CampaignCall] = Field(
        default_factory=list,
        description="Recent call records"
    )

    # Metadata
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Analytics generation timestamp"
    )


class CampaignListResponse(BaseModel):
    """Response model for listing campaigns."""

    campaigns: List[AutomationCampaign]
    total: int
    page: int = 1
    per_page: int = 20
