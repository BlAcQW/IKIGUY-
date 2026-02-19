"""
User database model.

Defines the structure and validation for user documents in MongoDB.
"""

from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, model_validator, field_validator
from pydantic_core import core_schema
from bson import ObjectId


# Valid role types for ChurchFlow
VALID_ROLES = {
    # Basic roles
    "member",
    "admin",
    "universal_admin",

    # Coordination roles
    "coordinator",
    "transport_coordinator",

    # Leadership roles (hierarchical)
    "cell_leader",
    "assistant_cell_leader",
    "zone_leader",
    "assistant_zone_leader",
    "department_head",
    "assistant_department_head",
}


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


class StageTransition(BaseModel):
    """
    Track stage changes in member journey.

    Records when a member transitions between discipleship stages,
    who made the transition, and any notes about the progression.
    """
    previous_stage: Optional[str] = None
    new_stage: str
    journey_type: str  # "spiritual", "cell", "ministry"
    transitioned_at: datetime = Field(default_factory=datetime.utcnow)
    transitioned_by_user_id: Optional[PyObjectId] = None
    notes: Optional[str] = None


class DepartmentAssignment(BaseModel):
    """
    Department membership with role.

    Tracks a member's involvement in a specific department/ministry
    including their role and who assigned them.
    """
    department_id: PyObjectId
    role: str  # "volunteer", "leader", "head"
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by_user_id: Optional[PyObjectId] = None
    is_active: bool = Field(default=True)


class SubgroupMembership(BaseModel):
    """
    Subgroup membership with assignment tracking.

    Tracks a member's involvement in a specific subgroup within a group.
    Used for flexible member categorization (e.g., age groups, service units).

    Attributes:
        group_id: Reference to parent group
        subgroup_id: Reference to specific subgroup
        joined_at: Timestamp when member was added to subgroup
        assigned_by_user_id: User who assigned this member
        is_active: Active status (True = active, False = inactive)
    """
    group_id: PyObjectId = Field(..., description="Parent group reference")
    subgroup_id: PyObjectId = Field(..., description="Subgroup reference")
    joined_at: datetime = Field(
        default_factory=datetime.utcnow, description="Join timestamp"
    )
    assigned_by_user_id: PyObjectId = Field(
        ..., description="User who made the assignment"
    )
    is_active: bool = Field(default=True, description="Active status")


class DataEnrichment(BaseModel):
    """
    Track data enrichment actions.

    Maintains audit trail of who updated member data, what changed,
    their role at the time of update, and any contextual notes.
    """
    field_name: str
    previous_value: Optional[Any] = None
    new_value: Any
    enriched_by_user_id: PyObjectId
    enriched_by_role: str  # "cell_leader", "zone_leader", "department_head", "admin"
    enriched_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class LifeEvent(BaseModel):
    """
    Significant life events.

    Records important events in a member's life that may require
    pastoral care or follow-up (births, deaths, marriages, etc.)
    """
    event_type: str  # "birth", "death", "marriage", "job_change", "relocation", "illness", "celebration"
    event_date: datetime
    description: str
    recorded_by_user_id: PyObjectId
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    requires_followup: bool = Field(default=False)
    followup_completed: bool = Field(default=False)


class User(BaseModel):
    """
    User model representing a church member with discipleship tracking.

    Attributes:
        # Identity & Authentication
        id: MongoDB document ID
        supabase_id: Supabase user ID (UUID)
        email: User's email address
        phone: User's phone number (unique identifier)
        name: User's full name (legacy field)
        full_name: User's full name

        # Roles & Permissions
        role: User's primary role (admin, coordinator, member) - legacy field
        branch_id: Reference to user's branch
        roles: List of user roles including:
            - Basic: member, admin, universal_admin
            - Coordination: coordinator, transport_coordinator
            - Leadership: cell_leader, assistant_cell_leader, zone_leader,
              assistant_zone_leader, department_head, assistant_department_head
        volunteer_roles: List of volunteer positions (e.g., 'choir', 'usher', 'media')

        # Member Status & Journey Tracking
        member_status: Overall member status (visitor, active_member, inactive_member, alumni)
        current_spiritual_stage: Current stage in spiritual journey (first_timer, new_convert, etc.)
        current_cell_stage: Current stage in cell group journey
        current_ministry_stage: Current stage in ministry/department journey

        # Leadership Assignments (Hierarchical)
        cell_group_id: Assigned cell group
        assigned_cell_leader_id: Cell leader responsible for this member
        zone_id: Zone this member belongs to
        departments: Department assignments with roles

        # Visit Tracking
        first_visit_date: Date of first visit
        visit_count: Total number of visits/check-ins
        last_visit_date: Most recent visit date
        consecutive_absences: Consecutive absences from services
        first_visit_source: How they heard about the church
        captured_by_user_id: Who initially captured this visitor

        # Journey History & Audit Trail
        stage_history: Complete history of all stage transitions
        enrichment_history: Audit trail of data updates by leaders
        life_events: Significant life events requiring pastoral care

        # Communication Preferences & Engagement
        preferred_communication_channel: Preferred channel (sms, whatsapp, voice, email)
        allow_automated_communications: Whether to send automated journey messages
        last_contact_date: Last communication sent
        sms_sent_count: Total SMS messages sent
        whatsapp_sent_count: Total WhatsApp messages sent
        calls_made_count: Total voice calls made
        calls_answered_count: Total voice calls answered

        # Extended Profile
        date_of_birth: Member's date of birth
        gender: Gender (male, female, other, prefer_not_to_say)
        occupation: Current occupation
        marital_status: Marital status (single, married, divorced, widowed)
        address: Physical address
        emergency_contact_name: Emergency contact person
        emergency_contact_phone: Emergency contact phone number

        # Timestamps
        created_at: Timestamp of user creation
        updated_at: Timestamp of last update
        last_active: Timestamp of last user activity
        profile_image_url: URL to user's profile image (optional)
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    supabase_id: Optional[str] = Field(None, description="Supabase user ID (UUID)")
    email: Optional[str] = Field(None, description="User's email address")
    phone: Optional[str] = Field(None, max_length=20, description="User's phone number (optional)")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Full name (legacy field)")
    full_name: Optional[str] = Field(None, description="User's full name")
    role: Optional[str] = Field(None, description="Primary role (admin, coordinator, member)")
    organization_id: Optional[PyObjectId] = Field(None, description="Organization this user belongs to")
    branch_id: Optional[PyObjectId] = None
    roles: Optional[List[str]] = Field(default_factory=lambda: ["member"])
    volunteer_roles: Optional[List[str]] = Field(default_factory=list)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = Field(default_factory=datetime.utcnow)
    profile_image_url: Optional[str] = None

    # Member Status & Journey Tracking
    member_status: Optional[str] = Field(
        default="visitor",
        pattern="^(visitor|active_member|inactive_member|alumni)$",
        description="Overall member status"
    )
    church_name: Optional[str] = Field(
        default=None,
        description="Church name (for visitors from other churches)"
    )
    current_spiritual_stage: Optional[str] = Field(
        default="first_timer",
        description="Current stage in spiritual journey"
    )
    current_cell_stage: Optional[str] = Field(
        default=None,
        description="Current stage in cell group journey"
    )
    current_ministry_stage: Optional[str] = Field(
        default=None,
        description="Current stage in ministry/department journey"
    )

    # Leadership Assignments (Hierarchical)
    cell_group_id: Optional[PyObjectId] = Field(
        default=None,
        description="Assigned cell group"
    )
    assigned_cell_leader_id: Optional[PyObjectId] = Field(
        default=None,
        description="Cell leader responsible for this member"
    )
    zone_id: Optional[PyObjectId] = Field(
        default=None,
        description="Zone this member belongs to"
    )
    departments: List[DepartmentAssignment] = Field(
        default_factory=list,
        description="Department assignments with roles"
    )

    # Group Memberships
    subgroup_memberships: List[SubgroupMembership] = Field(
        default_factory=list,
        description="Subgroup memberships for flexible member categorization"
    )

    # Visit Tracking
    first_visit_date: Optional[datetime] = Field(
        default=None,
        description="Date of first visit"
    )
    visit_count: int = Field(
        default=0,
        description="Total number of visits/check-ins"
    )
    last_visit_date: Optional[datetime] = Field(
        default=None,
        description="Most recent visit date"
    )
    consecutive_absences: int = Field(
        default=0,
        description="Consecutive absences from services"
    )
    first_visit_source: Optional[str] = Field(
        default=None,
        description="How they heard about the church (referral, social media, event, etc.)"
    )
    captured_by_user_id: Optional[PyObjectId] = Field(
        default=None,
        description="Who initially captured this visitor"
    )

    # Journey History & Audit Trail
    stage_history: List[StageTransition] = Field(
        default_factory=list,
        description="Complete history of all stage transitions"
    )
    enrichment_history: List[DataEnrichment] = Field(
        default_factory=list,
        description="Audit trail of data updates by leaders"
    )
    life_events: List[LifeEvent] = Field(
        default_factory=list,
        description="Significant life events requiring pastoral care"
    )

    # Communication Preferences & Engagement
    preferred_communication_channel: Optional[str] = Field(
        default="sms",
        pattern="^(sms|whatsapp|voice|email)$",
        description="Preferred communication channel"
    )
    allow_automated_communications: bool = Field(
        default=True,
        description="Whether to send automated journey messages"
    )
    last_contact_date: Optional[datetime] = Field(
        default=None,
        description="Last communication sent"
    )
    sms_sent_count: int = Field(
        default=0,
        description="Total SMS messages sent"
    )
    whatsapp_sent_count: int = Field(
        default=0,
        description="Total WhatsApp messages sent"
    )
    calls_made_count: int = Field(
        default=0,
        description="Total voice calls made"
    )
    calls_answered_count: int = Field(
        default=0,
        description="Total voice calls answered"
    )

    # Extended Profile
    date_of_birth: Optional[datetime] = Field(
        default=None,
        description="Member's date of birth"
    )
    gender: Optional[str] = Field(
        default=None,
        pattern="^(male|female|other|prefer_not_to_say)$",
        description="Gender"
    )
    occupation: Optional[str] = Field(
        default=None,
        description="Current occupation"
    )
    marital_status: Optional[str] = Field(
        default=None,
        pattern="^(single|married|divorced|widowed)$",
        description="Marital status"
    )
    address: Optional[str] = Field(
        default=None,
        description="Physical address"
    )
    emergency_contact_name: Optional[str] = Field(
        default=None,
        description="Emergency contact person"
    )
    emergency_contact_phone: Optional[str] = Field(
        default=None,
        description="Emergency contact phone number"
    )

    @model_validator(mode='before')
    @classmethod
    def populate_roles_from_role(cls, data: Any) -> Any:
        """
        Populate roles list from role field for backward compatibility.

        If the database document only has 'role' (singular) but not 'roles' (plural),
        this validator automatically creates the 'roles' list from the 'role' value.
        This ensures authorization checks work correctly with legacy user documents.
        """
        if isinstance(data, dict):
            # If roles is missing or empty, but role exists, populate roles from role
            if (not data.get('roles') or data.get('roles') == ['member']) and data.get('role'):
                data['roles'] = [data['role']]
        return data

    @field_validator('roles')
    @classmethod
    def validate_roles(cls, roles: Optional[List[str]]) -> Optional[List[str]]:
        """
        Validate that all roles are recognized role types.

        Ensures data integrity by rejecting invalid role assignments.
        Prevents typos and unauthorized role creation.

        Args:
            roles: List of role strings to validate

        Returns:
            The validated roles list

        Raises:
            ValueError: If any role is not in VALID_ROLES set
        """
        if roles:
            invalid_roles = [role for role in roles if role not in VALID_ROLES]
            if invalid_roles:
                raise ValueError(
                    f"Invalid roles: {invalid_roles}. "
                    f"Valid roles are: {sorted(VALID_ROLES)}"
                )
        return roles

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "phone": "+233244123456",
                "name": "Akosua Mensah",
                "full_name": "Akosua Mensah",
                "branch_id": "507f1f77bcf86cd799439011",
                "roles": ["member", "cell_leader", "department_head"],
                "volunteer_roles": ["choir"],
                "member_status": "active_member",
                "current_spiritual_stage": "baptized",
                "current_cell_stage": "cell_leader",
                "current_ministry_stage": "department_leader",
                "cell_group_id": "507f1f77bcf86cd799439012",
                "zone_id": "507f1f77bcf86cd799439013",
                "departments": [
                    {
                        "department_id": "507f1f77bcf86cd799439014",
                        "role": "head",
                        "joined_at": "2025-06-01T10:00:00",
                        "is_active": True
                    }
                ],
                "subgroup_memberships": [
                    {
                        "group_id": "507f1f77bcf86cd799439015",
                        "subgroup_id": "507f1f77bcf86cd799439016",
                        "joined_at": "2025-01-15T10:00:00",
                        "assigned_by_user_id": "507f1f77bcf86cd799439017",
                        "is_active": True
                    }
                ],
                "first_visit_date": "2025-01-15T10:00:00",
                "visit_count": 25,
                "preferred_communication_channel": "whatsapp",
                "allow_automated_communications": True,
                "created_at": "2025-01-15T10:00:00",
                "updated_at": "2025-10-23T10:00:00",
                "last_active": "2025-10-23T10:00:00",
                "profile_image_url": "https://example.com/profile.jpg",
            }
        }
