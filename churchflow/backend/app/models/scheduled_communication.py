"""
Scheduled Communication Model.

Defines pending automated communications in the message queue,
including welcome messages, follow-ups, and stage transition notifications.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from pydantic_core import core_schema
from bson import ObjectId


class PyObjectId(ObjectId):
    """
    Custom ObjectId type for Pydantic models (Pydantic v2 compatible).

    Allows Pydantic to validate and serialize MongoDB ObjectIds.
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        """Pydantic v2 core schema for ObjectId validation."""
        return core_schema.with_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x), return_schema=core_schema.str_schema()
            ),
        )

    @classmethod
    def _validate(cls, v, _info):
        """Validate and convert value to ObjectId."""
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError(f"Invalid ObjectId: {v}")


class ScheduledCommunication(BaseModel):
    """
    Scheduled communication in the message queue.

    Represents a pending automated message to be sent to a member
    at a specific time via one or more communication channels.

    Attributes:
        id: MongoDB document ID
        organization_id: Reference to parent organization
        user_id: Recipient user ID

        # Context
        stage_id: Journey stage that triggered this communication
        followup_type: Type of follow-up (welcome, day_1, day_3, stage_transition)

        # Scheduling
        scheduled_for: When to send this communication
        channels: Communication channels to use (sms, whatsapp, voice, email)

        # Message Content
        message_template: Message template with {{variables}}
        template_variables: Values for template variables

        # Status Tracking
        status: Current status (pending, sent, failed, cancelled)
        sent_at: When the communication was actually sent
        campaign_ids: Campaign IDs for each channel {"sms": "campaign_123"}
        error_message: Error details if failed

        # Deduplication
        deduplication_key: Key to prevent duplicate messages

        # Metadata
        created_at: Timestamp of creation
        created_by_user_id: User who triggered this communication
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    organization_id: PyObjectId = Field(..., description="Parent organization")
    user_id: PyObjectId = Field(..., description="Recipient user ID")

    # Context
    stage_id: Optional[PyObjectId] = Field(
        default=None,
        description="Journey stage that triggered this"
    )
    followup_type: str = Field(
        ...,
        pattern="^(welcome|day_1|day_3|day_7|day_14|day_30|stage_transition|manual)$",
        description="Type of follow-up"
    )

    # Scheduling
    scheduled_for: datetime = Field(
        ...,
        description="When to send this communication"
    )
    channels: List[str] = Field(
        default_factory=lambda: ["sms"],
        description="Channels to use (sms, whatsapp, voice, email)"
    )

    # Message Content
    message_template: str = Field(
        ...,
        min_length=1,
        description="Message template with {{variables}}"
    )
    template_variables: Dict[str, str] = Field(
        default_factory=dict,
        description="Values for template variables (name, church_name, etc.)"
    )

    # Status Tracking
    status: str = Field(
        default="pending",
        pattern="^(pending|sent|failed|cancelled)$",
        description="Current status"
    )
    sent_at: Optional[datetime] = Field(
        default=None,
        description="When actually sent"
    )
    campaign_ids: Dict[str, str] = Field(
        default_factory=dict,
        description="Campaign IDs per channel (sms: campaign_id)"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if failed"
    )

    # Deduplication
    deduplication_key: Optional[str] = Field(
        default=None,
        description="Key to prevent duplicate messages (user_id_followup_type)"
    )

    # Retry Logic
    retry_count: int = Field(
        default=0,
        ge=0,
        description="Number of retry attempts"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum retry attempts"
    )
    next_retry_at: Optional[datetime] = Field(
        default=None,
        description="When to retry if failed"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_user_id: Optional[PyObjectId] = Field(
        default=None,
        description="User who triggered this communication"
    )

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "organization_id": "507f1f77bcf86cd799439011",
                "user_id": "507f1f77bcf86cd799439012",
                "stage_id": "507f1f77bcf86cd799439013",
                "followup_type": "day_3",
                "scheduled_for": "2025-12-06T10:00:00",
                "channels": ["whatsapp", "sms"],
                "message_template": "Hi {{name}}! We'd love to invite you to join a cell group in {{area}}.",
                "template_variables": {
                    "name": "Akosua Mensah",
                    "area": "Adenta",
                    "church_name": "Victory Church",
                    "cell_leader_name": "Pastor Kwame"
                },
                "status": "pending",
                "deduplication_key": "507f1f77bcf86cd799439012_day_3",
                "retry_count": 0,
                "max_retries": 3
            }
        }
