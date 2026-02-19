"""
Group and Subgroup database models.

Defines the structure and validation for group and subgroup documents in MongoDB.
Groups allow categorization of members with nested subgroups that can be
configured for single-select or multi-select membership.
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator
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


class Group(BaseModel):
    """
    Group model for member categorization.

    Groups are organization-wide categories (e.g., "Age Tribes", "Service Units")
    that contain subgroups for more specific member classification.

    Attributes:
        id: MongoDB document ID
        organization_id: Reference to parent organization
        name: Group name (e.g., "Age Tribes", "Departments")
        description: Optional description of the group's purpose
        created_by_user_id: User who created this group
        created_at: Timestamp of group creation
        updated_at: Timestamp of last update
        is_active: Soft delete flag (True = active, False = deleted)
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    organization_id: PyObjectId = Field(
        ..., description="Organization this group belongs to"
    )
    name: str = Field(
        ..., min_length=1, max_length=200, description="Group name"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Group description"
    )
    created_by_user_id: PyObjectId = Field(
        ..., description="User who created this group"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    is_active: bool = Field(default=True, description="Active status (soft delete)")

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "organization_id": "507f1f77bcf86cd799439011",
                "name": "Age Tribes",
                "description": "Member grouping by birth month",
                "created_by_user_id": "507f1f77bcf86cd799439012",
                "created_at": "2025-12-14T10:00:00",
                "updated_at": "2025-12-14T10:00:00",
                "is_active": True,
            }
        }


class Subgroup(BaseModel):
    """
    Subgroup model for specific member classification within a group.

    Subgroups are nested under groups and can be configured for either
    single-select (member can only be in ONE subgroup) or multi-select
    (member can be in MULTIPLE subgroups) within the parent group.

    Attributes:
        id: MongoDB document ID
        group_id: Reference to parent group
        organization_id: Reference to organization (denormalized for efficient queries)
        name: Subgroup name (e.g., "January Born", "Choir", "Ushering")
        description: Optional description of the subgroup
        selection_mode: "single" or "multi" - determines membership constraints
        member_count: Current number of members in this subgroup
        created_at: Timestamp of subgroup creation
        updated_at: Timestamp of last update
        is_active: Soft delete flag (True = active, False = deleted)

    Selection Modes:
        - "single": Member can only be in ONE subgroup within this group
          (e.g., January Born OR February Born, not both)
        - "multi": Member can be in MULTIPLE subgroups within this group
          (e.g., Choir AND Ushering AND Prayer)
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    group_id: PyObjectId = Field(..., description="Parent group reference")
    organization_id: PyObjectId = Field(
        ..., description="Organization (denormalized)"
    )
    name: str = Field(
        ..., min_length=1, max_length=200, description="Subgroup name"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Subgroup description"
    )
    selection_mode: str = Field(
        ...,
        pattern="^(single|multi)$",
        description="Membership mode: 'single' or 'multi'",
    )
    member_count: int = Field(
        default=0, ge=0, description="Number of members in this subgroup"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    is_active: bool = Field(default=True, description="Active status (soft delete)")

    @field_validator("selection_mode")
    @classmethod
    def validate_selection_mode(cls, mode: str) -> str:
        """
        Validate selection_mode is either 'single' or 'multi'.

        Args:
            mode: Selection mode string

        Returns:
            The validated selection mode

        Raises:
            ValueError: If mode is not 'single' or 'multi'
        """
        if mode not in ["single", "multi"]:
            raise ValueError("selection_mode must be 'single' or 'multi'")
        return mode

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "group_id": "507f1f77bcf86cd799439011",
                "organization_id": "507f1f77bcf86cd799439012",
                "name": "January Born",
                "description": "Members born in January",
                "selection_mode": "single",
                "member_count": 45,
                "created_at": "2025-12-14T10:00:00",
                "updated_at": "2025-12-14T10:00:00",
                "is_active": True,
            }
        }
