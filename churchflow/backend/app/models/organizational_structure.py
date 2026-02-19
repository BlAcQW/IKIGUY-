"""
Organizational Structure Models.

Defines hierarchical leadership structures for the church including:
- Cell Groups: Small groups for discipleship and fellowship
- Zones: Geographic/organizational groupings of cell groups
- Departments: Ministry departments (worship, hospitality, media, etc.)
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


class CellGroup(BaseModel):
    """
    Small group for discipleship and fellowship.

    Cell groups are the primary unit of member care and discipleship,
    typically consisting of 8-12 members who meet regularly for
    Bible study, prayer, and fellowship.

    Attributes:
        id: MongoDB document ID
        organization_id: Reference to parent organization
        branch_id: Reference to church branch (if multi-site)
        zone_id: Reference to parent zone
        name: Cell group name
        description: Brief description of the cell group
        meeting_day: Day of week for meetings (e.g., "Monday")
        meeting_time: Time of meetings (e.g., "19:00")
        meeting_location: Physical location or address
        meeting_location_coordinates: GPS coordinates {lat, lng}
        cell_leader_id: Reference to cell leader user
        assistant_leaders: List of assistant leader user IDs
        target_size: Ideal cell group size (default: 12)
        current_member_count: Current number of members
        is_full: Whether cell group is at capacity
        is_active: Whether cell group is currently active
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    organization_id: PyObjectId = Field(..., description="Parent organization")
    branch_id: Optional[PyObjectId] = Field(default=None, description="Church branch")
    zone_id: Optional[PyObjectId] = Field(default=None, description="Parent zone")

    # Basic Information
    name: str = Field(..., min_length=1, max_length=200, description="Cell group name")
    description: Optional[str] = Field(default=None, max_length=1000)

    # Meeting Details
    meeting_day: Optional[str] = Field(
        default=None,
        description="Day of week (Monday, Tuesday, etc.)"
    )
    meeting_time: Optional[str] = Field(
        default=None,
        description="Meeting time (e.g., 19:00)"
    )
    meeting_location: Optional[str] = Field(
        default=None,
        description="Physical location or address"
    )
    meeting_location_coordinates: Optional[dict] = Field(
        default=None,
        description="GPS coordinates {lat: float, lng: float}"
    )

    # Leadership
    cell_leader_id: Optional[PyObjectId] = Field(
        default=None,
        description="Cell leader user ID"
    )
    assistant_leaders: List[PyObjectId] = Field(
        default_factory=list,
        description="Assistant leader user IDs"
    )

    # Capacity Management
    target_size: Optional[int] = Field(
        default=12,
        ge=1,
        le=50,
        description="Ideal cell group size"
    )
    current_member_count: int = Field(
        default=0,
        ge=0,
        description="Current number of members"
    )
    is_full: bool = Field(
        default=False,
        description="Whether at capacity"
    )

    # Status
    is_active: bool = Field(
        default=True,
        description="Whether currently active"
    )
    status: str = Field(
        default="active",
        pattern="^(active|inactive|forming|dissolved)$",
        description="Cell group status"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "organization_id": "507f1f77bcf86cd799439011",
                "branch_id": "507f1f77bcf86cd799439012",
                "zone_id": "507f1f77bcf86cd799439013",
                "name": "Victory Cell - Adenta",
                "description": "Cell group meeting in Adenta area",
                "meeting_day": "Wednesday",
                "meeting_time": "19:00",
                "meeting_location": "123 Main Street, Adenta",
                "cell_leader_id": "507f1f77bcf86cd799439014",
                "target_size": 12,
                "current_member_count": 8,
                "is_full": False,
                "is_active": True,
                "status": "active"
            }
        }


class Zone(BaseModel):
    """
    Geographic or organizational grouping of cell groups.

    Zones provide mid-level leadership structure, with zone leaders
    overseeing multiple cell groups in a geographic area or
    organizational division.

    Attributes:
        id: MongoDB document ID
        organization_id: Reference to parent organization
        branch_id: Reference to church branch (if multi-site)
        name: Zone name
        description: Brief description
        geographic_area: Geographic area covered (e.g., "East Accra")
        zone_leader_id: Reference to zone leader user
        assistant_zone_leaders: List of assistant zone leader user IDs
        cell_group_count: Number of cell groups in this zone
        is_active: Whether zone is currently active
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    organization_id: PyObjectId = Field(..., description="Parent organization")
    branch_id: Optional[PyObjectId] = Field(default=None, description="Church branch")

    # Basic Information
    name: str = Field(..., min_length=1, max_length=200, description="Zone name")
    description: Optional[str] = Field(default=None, max_length=1000)
    geographic_area: Optional[str] = Field(
        default=None,
        description="Geographic area covered (e.g., 'East Accra', 'Tema Region')"
    )

    # Leadership
    zone_leader_id: Optional[PyObjectId] = Field(
        default=None,
        description="Zone leader user ID"
    )
    assistant_zone_leaders: List[PyObjectId] = Field(
        default_factory=list,
        description="Assistant zone leader user IDs"
    )

    # Metrics
    cell_group_count: int = Field(
        default=0,
        ge=0,
        description="Number of cell groups in this zone"
    )

    # Status
    is_active: bool = Field(
        default=True,
        description="Whether currently active"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "organization_id": "507f1f77bcf86cd799439011",
                "branch_id": "507f1f77bcf86cd799439012",
                "name": "East Accra Zone",
                "description": "Zone covering eastern Accra communities",
                "geographic_area": "East Accra (Adenta, Madina, Ashongman)",
                "zone_leader_id": "507f1f77bcf86cd799439015",
                "cell_group_count": 5,
                "is_active": True
            }
        }


class Department(BaseModel):
    """
    Ministry department (e.g., Choir, Ushering, Media, Children's Ministry).

    Departments organize volunteer service and ministry activities,
    with each department having a head and team of volunteers.

    Attributes:
        id: MongoDB document ID
        organization_id: Reference to parent organization
        branch_id: Reference to church branch (if multi-site)
        name: Department name
        description: Brief description
        department_type: Type of department (worship, hospitality, media, etc.)
        department_head_id: Reference to department head user
        assistant_heads: List of assistant head user IDs
        volunteer_count: Number of volunteers in department
        leader_count: Number of leaders in department
        requires_training: Whether volunteers need training
        training_description: Description of required training
        is_active: Whether department is currently active
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    organization_id: PyObjectId = Field(..., description="Parent organization")
    branch_id: Optional[PyObjectId] = Field(default=None, description="Church branch")

    # Basic Information
    name: str = Field(..., min_length=1, max_length=200, description="Department name")
    description: Optional[str] = Field(default=None, max_length=1000)
    department_type: str = Field(
        ...,
        description="Department category: worship, hospitality, media, children, youth, admin, outreach, etc."
    )

    # Leadership
    department_head_id: Optional[PyObjectId] = Field(
        default=None,
        description="Department head user ID"
    )
    assistant_heads: List[PyObjectId] = Field(
        default_factory=list,
        description="Assistant head user IDs"
    )

    # Member Counts
    volunteer_count: int = Field(
        default=0,
        ge=0,
        description="Number of volunteers"
    )
    leader_count: int = Field(
        default=0,
        ge=0,
        description="Number of leaders"
    )

    # Training Requirements
    requires_training: bool = Field(
        default=False,
        description="Whether volunteers need training"
    )
    training_description: Optional[str] = Field(
        default=None,
        description="Description of required training"
    )

    # Status
    is_active: bool = Field(
        default=True,
        description="Whether currently active"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "organization_id": "507f1f77bcf86cd799439011",
                "branch_id": "507f1f77bcf86cd799439012",
                "name": "Worship Team",
                "description": "Leads congregational worship during services",
                "department_type": "worship",
                "department_head_id": "507f1f77bcf86cd799439016",
                "volunteer_count": 25,
                "leader_count": 5,
                "requires_training": True,
                "training_description": "Musical proficiency and worship leading basics",
                "is_active": True
            }
        }
