"""
Vapi API v1 Request and Response Models

These models define the public API contract for v1.
IMPORTANT: Once deployed, these models are STABLE and cannot have breaking changes.
Breaking changes require creating v2.

Stability Promise:
- Field names cannot change
- Field types cannot change
- Required fields cannot become optional (or vice versa)
- New optional fields can be added
- Response fields can be added but not removed
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class CallTypeEnum(str, Enum):
    """Call type options."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BOTH = "both"


class VoiceProvider(str, Enum):
    """Voice provider options."""
    OPENAI = "openai"
    VAPI = "vapi"


# ============================================================================
# REQUEST MODELS
# ============================================================================

class CreateAssistantRequest(BaseModel):
    """
    Request model for creating a voice assistant.

    Example:
        ```json
        {
            "name": "Sales Assistant",
            "system_prompt": "You are a helpful sales assistant...",
            "voice": "alloy",
            "language": "en",
            "speed": 1.0
        }
        ```
    """
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Assistant name (3-100 characters)"
    )
    system_prompt: str = Field(
        ...,
        min_length=10,
        description="System prompt that defines the assistant's behavior"
    )
    voice: str = Field(
        default="alloy",
        description="Voice ID (e.g., 'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer')"
    )
    language: str = Field(
        default="en",
        description="Primary language code (ISO 639-1, e.g., 'en', 'es', 'fr')"
    )
    speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Speaking speed (0.5-2.0)"
    )
    call_type: CallTypeEnum = Field(
        default=CallTypeEnum.BOTH,
        description="Type of calls this assistant handles"
    )
    max_duration: int = Field(
        default=600,
        ge=30,
        le=3600,
        description="Maximum call duration in seconds (30-3600)"
    )
    silence_timeout: int = Field(
        default=10,
        ge=5,
        le=60,
        description="Silence timeout in seconds (5-60)"
    )
    record_calls: bool = Field(
        default=True,
        description="Whether to record calls"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Custom metadata (max 10 key-value pairs)"
    )

    @validator('metadata')
    def validate_metadata(cls, v):
        """Validate metadata size."""
        if v and len(v) > 10:
            raise ValueError("metadata can have maximum 10 key-value pairs")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Customer Support Assistant",
                "system_prompt": "You are a helpful customer support assistant. Be polite and professional.",
                "voice": "alloy",
                "language": "en",
                "speed": 1.0,
                "call_type": "both",
                "max_duration": 600,
                "silence_timeout": 10,
                "record_calls": True,
                "metadata": {
                    "department": "support",
                    "created_by": "api"
                }
            }
        }


class UpdateAssistantRequest(BaseModel):
    """
    Request model for updating an assistant.
    All fields are optional - only provided fields will be updated.
    """
    name: Optional[str] = Field(
        None,
        min_length=3,
        max_length=100,
        description="Updated assistant name"
    )
    system_prompt: Optional[str] = Field(
        None,
        min_length=10,
        description="Updated system prompt"
    )
    voice: Optional[str] = Field(
        None,
        description="Updated voice ID"
    )
    language: Optional[str] = Field(
        None,
        description="Updated language code"
    )
    speed: Optional[float] = Field(
        None,
        ge=0.5,
        le=2.0,
        description="Updated speaking speed"
    )
    max_duration: Optional[int] = Field(
        None,
        ge=30,
        le=3600,
        description="Updated max duration"
    )
    silence_timeout: Optional[int] = Field(
        None,
        ge=5,
        le=60,
        description="Updated silence timeout"
    )
    record_calls: Optional[bool] = Field(
        None,
        description="Updated recording preference"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated metadata"
    )


class InitiateCallRequest(BaseModel):
    """
    Request model for initiating an outbound call.

    Example:
        ```json
        {
            "assistant_id": "asst_123abc",
            "to_number": "+14155551234",
            "from_number": "+14155559999",
            "metadata": {
                "campaign": "summer_sale",
                "customer_id": "cust_456"
            }
        }
        ```
    """
    assistant_id: str = Field(
        ...,
        description="Assistant ID to use for the call"
    )
    to_number: str = Field(
        ...,
        pattern=r'^\+[1-9]\d{1,14}$',
        description="Phone number to call (E.164 format, e.g., +14155551234)"
    )
    from_number: Optional[str] = Field(
        None,
        pattern=r'^\+[1-9]\d{1,14}$',
        description="Caller ID (E.164 format). Uses default if not provided."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Custom call metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "assistant_id": "asst_123abc",
                "to_number": "+14155551234",
                "from_number": "+14155559999",
                "metadata": {
                    "campaign": "summer_sale",
                    "customer_id": "cust_456"
                }
            }
        }


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class AssistantResponse(BaseModel):
    """
    Response model for assistant operations.

    This is the stable response format for v1.
    """
    id: str = Field(..., description="Assistant ID")
    name: str = Field(..., description="Assistant name")
    status: str = Field(..., description="Assistant status (active, inactive)")
    voice: str = Field(..., description="Voice ID")
    language: str = Field(..., description="Language code")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Custom metadata")

    @classmethod
    def from_vapi_response(cls, vapi_data: dict):
        """
        Convert VAPIService response to stable v1 API response.

        Args:
            vapi_data: Response from shared VAPIService

        Returns:
            AssistantResponse with stable v1 fields
        """
        # Extract voice ID from voice dict if present
        voice_data = vapi_data.get("voice", {})
        if isinstance(voice_data, dict):
            voice_id = voice_data.get("voiceId") or voice_data.get("model") or "alloy"
        else:
            voice_id = str(voice_data) if voice_data else "alloy"

        # Parse ISO datetime strings from Vapi API
        created_at = vapi_data.get("createdAt") or vapi_data.get("created_at")
        if isinstance(created_at, str):
            from dateutil import parser
            created_at = parser.isoparse(created_at)
        elif not created_at:
            created_at = datetime.utcnow()

        updated_at = vapi_data.get("updatedAt") or vapi_data.get("updated_at")
        if isinstance(updated_at, str):
            from dateutil import parser
            updated_at = parser.isoparse(updated_at)

        # Extract language from model or default to "en"
        model_data = vapi_data.get("model", {})
        language = "en"  # Default
        if isinstance(model_data, dict):
            # Check if language is in model metadata
            language = model_data.get("language", "en")

        return cls(
            id=vapi_data.get("id") or vapi_data.get("agent_id") or vapi_data.get("assistant_id") or "unknown",
            name=vapi_data.get("name") or "Unnamed Assistant",
            status="active",  # Vapi doesn't return status - default to active
            voice=voice_id,
            language=language,
            created_at=created_at,
            updated_at=updated_at,
            metadata=vapi_data.get("metadata")
        )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "asst_123abc",
                "name": "Sales Assistant",
                "status": "active",
                "voice": "alloy",
                "language": "en",
                "created_at": "2025-10-23T12:00:00Z",
                "updated_at": None,
                "metadata": {
                    "department": "sales"
                }
            }
        }


class CallResponse(BaseModel):
    """Response model for call operations."""
    id: str = Field(..., description="Call ID")
    assistant_id: str = Field(..., description="Assistant ID used")
    to_number: Optional[str] = Field(None, description="Recipient phone number (for outbound calls)")
    from_number: Optional[str] = Field(None, description="Caller ID used")
    status: str = Field(..., description="Call status (initiated, ringing, answered, ended, failed)")
    duration: Optional[int] = Field(None, description="Call duration in seconds")
    started_at: datetime = Field(..., description="Call start time")
    ended_at: Optional[datetime] = Field(None, description="Call end time")
    recording_url: Optional[str] = Field(None, description="Recording URL (if available)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Custom metadata")

    @classmethod
    def from_vapi_response(cls, vapi_data: dict):
        """Convert VAPIService call response to v1 API response."""
        # Parse ISO datetime strings from Vapi API
        started_at = vapi_data.get("startedAt") or vapi_data.get("started_at")
        if isinstance(started_at, str):
            from dateutil import parser
            started_at = parser.isoparse(started_at)
        elif not started_at:
            started_at = datetime.utcnow()

        ended_at = vapi_data.get("endedAt") or vapi_data.get("ended_at")
        if isinstance(ended_at, str):
            from dateutil import parser
            ended_at = parser.isoparse(ended_at)

        # Calculate duration if not provided but both start and end times exist
        duration = vapi_data.get("duration")
        if not duration and started_at and ended_at:
            # Calculate duration in seconds
            if isinstance(started_at, datetime) and isinstance(ended_at, datetime):
                duration = int((ended_at - started_at).total_seconds())

        # Extract phone numbers from customer field if present
        customer = vapi_data.get("customer", {})
        to_number = vapi_data.get("to_number") or vapi_data.get("toNumber") or customer.get("number")
        from_number = vapi_data.get("from_number") or vapi_data.get("fromNumber")

        return cls(
            id=vapi_data.get("id") or vapi_data.get("call_id") or "unknown",
            assistant_id=vapi_data.get("assistantId") or vapi_data.get("assistant_id") or "unknown",
            to_number=to_number,
            from_number=from_number,
            status=vapi_data.get("status", "unknown"),
            duration=duration,
            started_at=started_at,
            ended_at=ended_at,
            recording_url=vapi_data.get("recordingUrl") or vapi_data.get("recording_url"),
            metadata=vapi_data.get("metadata")
        )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "call_789xyz",
                "assistant_id": "asst_123abc",
                "to_number": "+14155551234",
                "from_number": "+14155559999",
                "status": "answered",
                "duration": 120,
                "started_at": "2025-10-23T12:05:00Z",
                "ended_at": "2025-10-23T12:07:00Z",
                "recording_url": "https://recordings.vapi.ai/call_789xyz.mp3",
                "metadata": {}
            }
        }


class ListAssistantsResponse(BaseModel):
    """Response model for listing assistants."""
    assistants: List[AssistantResponse] = Field(..., description="List of assistants")
    total: int = Field(..., description="Total number of assistants")
    limit: int = Field(..., description="Requested limit")
    offset: int = Field(..., description="Requested offset")

    class Config:
        json_schema_extra = {
            "example": {
                "assistants": [
                    {
                        "id": "asst_123",
                        "name": "Sales Assistant",
                        "status": "active",
                        "voice": "alloy",
                        "language": "en",
                        "created_at": "2025-10-23T12:00:00Z"
                    }
                ],
                "total": 1,
                "limit": 10,
                "offset": 0
            }
        }


class ListCallsResponse(BaseModel):
    """Response model for listing calls."""
    calls: List[CallResponse] = Field(..., description="List of calls")
    total: int = Field(..., description="Total number of calls")
    limit: int = Field(..., description="Requested limit")
    offset: int = Field(..., description="Requested offset")

    class Config:
        json_schema_extra = {
            "example": {
                "calls": [
                    {
                        "id": "call_789",
                        "assistant_id": "asst_123",
                        "to_number": "+14155551234",
                        "status": "ended",
                        "duration": 120,
                        "started_at": "2025-10-23T12:05:00Z",
                        "ended_at": "2025-10-23T12:07:00Z"
                    }
                ],
                "total": 1,
                "limit": 10,
                "offset": 0
            }
        }


# ============================================================================
# ERROR RESPONSE MODELS
# ============================================================================

class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field that caused the error (for validation errors)")


class ErrorResponse(BaseModel):
    """Standard error response for v1 API."""
    error: ErrorDetail = Field(..., description="Error details")
    request_id: str = Field(..., description="Request ID for debugging")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Assistant name must be at least 3 characters",
                    "field": "name"
                },
                "request_id": "req_abc123",
                "timestamp": "2025-10-23T12:00:00Z"
            }
        }
