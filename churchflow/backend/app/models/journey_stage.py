"""
Journey Stage Models.

Defines discipleship journey stages with automation configurations including:
- Journey stages for spiritual, cell, and ministry pathways
- Scheduled follow-up communications
- Automation triggers for welcome messages and stage transitions
"""

from datetime import datetime
from typing import List, Optional, Any
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


class ScheduledFollowup(BaseModel):
    """
    Scheduled follow-up communication configuration.

    Defines automated follow-up messages to be sent at specific
    intervals after a member reaches this journey stage.

    Attributes:
        delay_days: Number of days after stage entry to send message
        message_template: Template with {{variables}} for personalization
        communication_channels: Channels to use (sms, whatsapp, voice, email)
        requires_action: Whether this follow-up requires leader action
        action_description: Description of action required (if any)
    """

    delay_days: int = Field(
        ...,
        ge=0,
        description="Days after stage entry to send (0 = immediate)"
    )
    message_template: str = Field(
        ...,
        min_length=1,
        description="Message template with {{name}}, {{church_name}}, etc."
    )
    communication_channels: List[str] = Field(
        default_factory=lambda: ["sms"],
        description="Channels: sms, whatsapp, voice, email"
    )
    requires_action: bool = Field(
        default=False,
        description="Whether leader action is required"
    )
    action_description: Optional[str] = Field(
        default=None,
        description="Description of required action"
    )


class JourneyStage(BaseModel):
    """
    Define journey stages with automation triggers.

    Supports predefined and custom stages for spiritual, cell, and
    ministry journeys. Each stage can have automated welcome messages
    and scheduled follow-ups.

    Attributes:
        id: MongoDB document ID
        organization_id: Reference to parent organization
        stage_name: Internal stage identifier (e.g., "first_timer")
        stage_display_name: User-friendly display name
        journey_type: Type of journey (spiritual, cell, ministry)
        stage_order: Sequential order within journey (1, 2, 3, ...)
        is_custom: Whether this is a custom stage (vs. predefined)
        is_active: Whether this stage is currently active

        # Automation Configuration
        auto_send_welcome: Whether to auto-send welcome on stage entry
        welcome_delay_minutes: Minutes to wait before sending welcome
        welcome_message_template: Template for welcome message
        welcome_channels: Channels for welcome (sms, whatsapp, voice)
        scheduled_followups: List of scheduled follow-up configs

        # Auto-advancement
        auto_advance_enabled: Whether to auto-advance to next stage
        auto_advance_after_days: Days before auto-advancing
        next_stage_id: Next stage to advance to

        # Metadata
        description: Stage description
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
        created_by_user_id: User who created this stage
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    organization_id: PyObjectId = Field(..., description="Parent organization")

    # Stage Definition
    stage_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Internal identifier (first_timer, new_convert, etc.)"
    )
    stage_display_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="User-friendly display name"
    )
    journey_type: str = Field(
        ...,
        pattern="^(spiritual|cell|ministry)$",
        description="Journey type"
    )
    stage_order: int = Field(
        ...,
        ge=1,
        description="Sequential order (1 = first stage)"
    )
    is_custom: bool = Field(
        default=False,
        description="Custom stage vs. predefined"
    )
    is_active: bool = Field(
        default=True,
        description="Whether currently active"
    )

    # Welcome Automation
    auto_send_welcome: bool = Field(
        default=True,
        description="Auto-send welcome on stage entry"
    )
    welcome_delay_minutes: int = Field(
        default=5,
        ge=0,
        le=1440,  # Max 24 hours
        description="Minutes to wait before sending (0-1440)"
    )
    welcome_message_template: Optional[str] = Field(
        default=None,
        description="Welcome message template with {{variables}}"
    )
    welcome_channels: List[str] = Field(
        default_factory=lambda: ["sms"],
        description="Welcome channels (sms, whatsapp, voice, email)"
    )

    # Scheduled Follow-ups
    scheduled_followups: List[ScheduledFollowup] = Field(
        default_factory=list,
        description="Scheduled follow-up configurations"
    )

    # Auto-advancement Configuration
    auto_advance_enabled: bool = Field(
        default=False,
        description="Whether to auto-advance to next stage"
    )
    auto_advance_after_days: Optional[int] = Field(
        default=None,
        ge=1,
        description="Days before auto-advancing"
    )
    next_stage_id: Optional[PyObjectId] = Field(
        default=None,
        description="Next stage to advance to"
    )

    # Metadata
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Stage description"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_user_id: Optional[PyObjectId] = Field(
        default=None,
        description="User who created this stage"
    )

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "organization_id": "507f1f77bcf86cd799439011",
                "stage_name": "first_timer",
                "stage_display_name": "First Time Visitor",
                "journey_type": "spiritual",
                "stage_order": 1,
                "is_custom": False,
                "is_active": True,
                "auto_send_welcome": True,
                "welcome_delay_minutes": 5,
                "welcome_message_template": "Welcome {{name}}! We're so glad you joined us at {{church_name}} today!",
                "welcome_channels": ["sms", "whatsapp"],
                "scheduled_followups": [
                    {
                        "delay_days": 1,
                        "message_template": "Hi {{name}}, it was great having you yesterday! How was your experience?",
                        "communication_channels": ["whatsapp"]
                    },
                    {
                        "delay_days": 3,
                        "message_template": "Hello {{name}}! We'd love to invite you to join a cell group in your area.",
                        "communication_channels": ["voice", "sms"]
                    },
                    {
                        "delay_days": 7,
                        "message_template": "We hope to see you again this Sunday at {{church_name}}!",
                        "communication_channels": ["sms"]
                    }
                ],
                "description": "First-time visitor to the church"
            }
        }
