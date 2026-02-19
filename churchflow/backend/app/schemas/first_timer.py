"""
First Timer API Schemas.

Request and response models for first timer endpoints.
"""

from datetime import datetime
from typing import Optional, Literal, List
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId


# Request Schemas

class CreateFirstTimerRequest(BaseModel):
    """Request schema for creating a first timer."""

    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    phone: str = Field(..., description="Phone number (primary contact)")
    email: Optional[EmailStr] = Field(None, description="Email address")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    gender: Optional[Literal["male", "female", "other"]] = Field(None, description="Gender")
    address: Optional[str] = Field(None, max_length=500, description="Home address")

    # Visit Information
    branch_id: Optional[str] = Field(None, description="Specific branch (optional)")
    visit_date: Optional[datetime] = Field(None, description="Date of visit (defaults to now)")
    visit_type: Literal["first_time", "returning"] = Field(
        default="first_time",
        description="First time or returning visitor"
    )
    service_attended: Optional[str] = Field(None, description="Service/event attended")

    # Interest & Intent
    interest_type: Literal["visitor", "new_convert", "existing_member", "discipleship"] = Field(
        ...,
        description="Type of interest: visitor, new_convert, existing_member, discipleship"
    )
    wants_membership: bool = Field(default=False, description="Interested in becoming a member")
    wants_discipleship: bool = Field(default=False, description="Interested in discipleship classes")

    # Discovery
    how_heard_about_us: Optional[str] = Field(None, description="How they heard about the church")
    invited_by: Optional[str] = Field(None, description="Name of person who invited them")

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+233244123456",
                "email": "john.doe@example.com",
                "gender": "male",
                "interest_type": "new_convert",
                "wants_membership": True,
                "wants_discipleship": True,
                "service_attended": "Sunday Service",
                "how_heard_about_us": "Friend invitation"
            }
        }


class UpdateFirstTimerRequest(BaseModel):
    """Request schema for updating a first timer."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None)
    email: Optional[EmailStr] = Field(None)
    date_of_birth: Optional[datetime] = Field(None)
    gender: Optional[Literal["male", "female", "other"]] = Field(None)
    address: Optional[str] = Field(None, max_length=500)
    visit_date: Optional[datetime] = Field(None)
    visit_type: Optional[Literal["first_time", "returning"]] = Field(None)
    service_attended: Optional[str] = Field(None)
    interest_type: Optional[Literal["visitor", "new_convert", "existing_member", "discipleship"]] = Field(None)
    wants_membership: Optional[bool] = Field(None)
    wants_discipleship: Optional[bool] = Field(None)
    how_heard_about_us: Optional[str] = Field(None)
    invited_by: Optional[str] = Field(None)

    class Config:
        json_schema_extra = {
            "example": {
                "phone": "+233244123456",
                "email": "updated.email@example.com"
            }
        }


class UpdateFollowUpRequest(BaseModel):
    """Request schema for updating follow-up status."""

    follow_up_status: Literal["pending", "contacted", "in_progress", "converted", "lost"] = Field(
        ...,
        description="Follow-up status"
    )
    follow_up_notes: Optional[str] = Field(None, description="Follow-up notes and comments")
    assigned_to_user_id: Optional[str] = Field(None, description="User assigned for follow-up")
    next_follow_up_date: Optional[datetime] = Field(None, description="Next scheduled follow-up")

    class Config:
        json_schema_extra = {
            "example": {
                "follow_up_status": "contacted",
                "follow_up_notes": "Called and scheduled visit for Sunday",
                "next_follow_up_date": "2025-12-22T10:00:00"
            }
        }


class ConvertToMemberRequest(BaseModel):
    """Request schema for converting first timer to member."""

    role: Optional[str] = Field(default="member", description="User role (defaults to 'member')")
    department_ids: Optional[List[str]] = Field(default_factory=list, description="Department IDs to assign")

    class Config:
        json_schema_extra = {
            "example": {
                "role": "member",
                "department_ids": ["67890abcdef123456"]
            }
        }


# Response Schemas

class FirstTimerResponse(BaseModel):
    """Response schema for first timer."""

    id: str = Field(..., description="First timer ID")
    organization_id: str = Field(..., description="Organization ID")
    branch_id: Optional[str] = Field(None, description="Branch ID")

    # Personal Information
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    full_name: str = Field(..., description="Full name")
    phone: str = Field(..., description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, description="Gender")
    address: Optional[str] = Field(None, description="Home address")

    # Visit Information
    visit_date: datetime = Field(..., description="Date of visit")
    visit_type: str = Field(..., description="Visit type")
    service_attended: Optional[str] = Field(None, description="Service attended")

    # Interest & Intent
    interest_type: str = Field(..., description="Interest type")
    wants_membership: bool = Field(..., description="Wants membership")
    wants_discipleship: bool = Field(..., description="Wants discipleship")

    # Discovery
    how_heard_about_us: Optional[str] = Field(None, description="How they heard about us")
    invited_by: Optional[str] = Field(None, description="Invited by")

    # Follow-up
    follow_up_status: str = Field(..., description="Follow-up status")
    follow_up_notes: Optional[str] = Field(None, description="Follow-up notes")
    assigned_to_user_id: Optional[str] = Field(None, description="Assigned to user ID")
    last_contact_date: Optional[datetime] = Field(None, description="Last contact date")
    next_follow_up_date: Optional[datetime] = Field(None, description="Next follow-up date")

    # Conversion
    converted_to_member: bool = Field(..., description="Converted to member")
    member_id: Optional[str] = Field(None, description="Member user ID")
    conversion_date: Optional[datetime] = Field(None, description="Conversion date")

    # Metadata
    created_by_user_id: str = Field(..., description="Created by user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_active: bool = Field(..., description="Active status")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "67890abcdef123456",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "phone": "+233244123456",
                "email": "john.doe@example.com",
                "interest_type": "new_convert",
                "follow_up_status": "pending"
            }
        }


class FirstTimerListResponse(BaseModel):
    """Response schema for paginated first timer list."""

    items: List[FirstTimerResponse] = Field(..., description="List of first timers")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }


class FirstTimerStatsResponse(BaseModel):
    """Response schema for first timer statistics."""

    total_first_timers: int = Field(..., description="Total first timers")
    today: int = Field(..., description="First timers today")
    this_week: int = Field(..., description="First timers this week")
    this_month: int = Field(..., description="First timers this month")
    visitors: int = Field(..., description="Just visitors")
    new_converts: int = Field(..., description="Want to become members")
    existing_members: int = Field(..., description="Returning members")
    discipleship_interested: int = Field(..., description="Interested in discipleship")
    pending_follow_up: int = Field(..., description="Pending follow-up")
    contacted: int = Field(..., description="Already contacted")
    in_progress: int = Field(..., description="Follow-up in progress")
    converted: int = Field(..., description="Converted to members")
    lost: int = Field(..., description="Lost to follow-up")
    conversion_rate: float = Field(..., description="Percentage converted to members")

    class Config:
        json_schema_extra = {
            "example": {
                "total_first_timers": 150,
                "this_month": 25,
                "this_week": 8,
                "today": 2,
                "visitors": 50,
                "new_converts": 75,
                "converted": 45,
                "conversion_rate": 30.0
            }
        }


class ConvertToMemberResponse(BaseModel):
    """Response schema for convert to member operation."""

    first_timer: FirstTimerResponse = Field(..., description="Updated first timer")
    user_id: str = Field(..., description="Created/linked user ID")
    is_new_user: bool = Field(..., description="Whether a new user was created")
    message: str = Field(..., description="Success message")

    class Config:
        json_schema_extra = {
            "example": {
                "first_timer": {},
                "user_id": "67890abcdef123456",
                "is_new_user": True,
                "message": "Successfully converted first timer to member"
            }
        }
