"""
First Timer Model.

Represents first-time visitors and their journey toward membership.
This is the main entry point for capturing visitor data.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.no_info_plain_validator_function(cls.validate),
        ])

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        return {"type": "string"}


class FirstTimer(BaseModel):
    """
    First Timer model - main entry point for visitor data.

    Tracks first-time visitors and their interest in membership,
    discipleship, or just visiting.
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    organization_id: PyObjectId = Field(..., description="Organization reference")
    branch_id: Optional[PyObjectId] = Field(None, description="Specific branch (optional)")

    # Personal Information
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    full_name: str = Field(..., description="Full name (auto-generated)")
    phone: str = Field(..., description="Phone number (primary contact)")
    email: Optional[EmailStr] = Field(None, description="Email address")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    gender: Optional[Literal["male", "female", "other"]] = Field(None, description="Gender")
    address: Optional[str] = Field(None, max_length=500, description="Home address")

    # Visit Information
    visit_date: datetime = Field(default_factory=datetime.utcnow, description="Date of visit")
    visit_type: Literal["first_time", "returning"] = Field(
        default="first_time",
        description="First time or returning visitor"
    )
    service_attended: Optional[str] = Field(None, description="Service/event attended")

    # Interest & Intent
    interest_type: Literal["visitor", "new_convert", "existing_member", "discipleship"] = Field(
        ...,
        description="Type of interest: visitor (just visiting), new_convert (wants membership), existing_member (returning member), discipleship (wants classes)"
    )
    wants_membership: bool = Field(default=False, description="Interested in becoming a member")
    wants_discipleship: bool = Field(default=False, description="Interested in discipleship classes")

    # Discovery
    how_heard_about_us: Optional[str] = Field(
        None,
        description="How they heard about the church (friend, social media, etc.)"
    )
    invited_by: Optional[str] = Field(None, description="Name of person who invited them")

    # Follow-up Management
    follow_up_status: Literal["pending", "contacted", "in_progress", "converted", "lost"] = Field(
        default="pending",
        description="Follow-up status"
    )
    follow_up_notes: Optional[str] = Field(None, description="Follow-up notes and comments")
    assigned_to_user_id: Optional[PyObjectId] = Field(None, description="User assigned for follow-up")
    last_contact_date: Optional[datetime] = Field(None, description="Last time contacted")
    next_follow_up_date: Optional[datetime] = Field(None, description="Next scheduled follow-up")

    # Conversion Tracking
    converted_to_member: bool = Field(default=False, description="Converted to full member")
    member_id: Optional[PyObjectId] = Field(None, description="User ID if converted to member")
    conversion_date: Optional[datetime] = Field(None, description="Date converted to member")

    # Metadata
    created_by_user_id: PyObjectId = Field(..., description="User who created this record")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    is_active: bool = Field(default=True, description="Active status")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "phone": "+233244123456",
                "email": "john.doe@example.com",
                "gender": "male",
                "visit_date": "2025-12-15T10:00:00",
                "interest_type": "new_convert",
                "wants_membership": True,
                "wants_discipleship": True,
                "service_attended": "Sunday Service",
                "how_heard_about_us": "Friend invitation",
                "follow_up_status": "pending"
            }
        }


class FirstTimerStats(BaseModel):
    """
    Statistics for First Timer Dashboard.
    """

    total_first_timers: int = Field(default=0, description="Total first timers (all time)")
    this_month: int = Field(default=0, description="First timers this month")
    this_week: int = Field(default=0, description="First timers this week")
    today: int = Field(default=0, description="First timers today")

    # By interest type
    visitors: int = Field(default=0, description="Just visitors")
    new_converts: int = Field(default=0, description="Want to become members")
    existing_members: int = Field(default=0, description="Returning members")
    discipleship_interested: int = Field(default=0, description="Interested in discipleship")

    # Follow-up status
    pending_follow_up: int = Field(default=0, description="Pending follow-up")
    contacted: int = Field(default=0, description="Already contacted")
    in_progress: int = Field(default=0, description="Follow-up in progress")
    converted: int = Field(default=0, description="Converted to members")
    lost: int = Field(default=0, description="Lost to follow-up")

    # Conversion rate
    conversion_rate: float = Field(default=0.0, description="Percentage converted to members")

    class Config:
        json_schema_extra = {
            "example": {
                "total_first_timers": 150,
                "this_month": 25,
                "this_week": 8,
                "today": 2,
                "visitors": 50,
                "new_converts": 75,
                "existing_members": 20,
                "discipleship_interested": 5,
                "pending_follow_up": 30,
                "contacted": 60,
                "converted": 45,
                "conversion_rate": 30.0
            }
        }
