"""
Group and Subgroup request/response schemas.

Defines Pydantic models for API requests and responses for the group management system.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# GROUP SCHEMAS
# ============================================================================


class CreateGroupRequest(BaseModel):
    """Request schema for creating a new group."""

    name: str = Field(..., min_length=1, max_length=200, description="Group name")
    description: Optional[str] = Field(
        None, max_length=1000, description="Group description"
    )


class UpdateGroupRequest(BaseModel):
    """Request schema for updating an existing group."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=200, description="Group name"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Group description"
    )
    is_active: Optional[bool] = Field(None, description="Active status")


class GroupResponse(BaseModel):
    """Response schema for group data."""

    id: str = Field(..., description="Group ID")
    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    created_by_user_id: str = Field(..., description="Creator user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_active: bool = Field(..., description="Active status")
    subgroup_count: Optional[int] = Field(0, description="Number of subgroups")


# ============================================================================
# SUBGROUP SCHEMAS
# ============================================================================


class CreateSubgroupRequest(BaseModel):
    """Request schema for creating a new subgroup."""

    name: str = Field(..., min_length=1, max_length=200, description="Subgroup name")
    description: Optional[str] = Field(
        None, max_length=1000, description="Subgroup description"
    )
    selection_mode: str = Field(
        ...,
        pattern="^(single|multi)$",
        description="Selection mode: 'single' or 'multi'",
    )


class UpdateSubgroupRequest(BaseModel):
    """Request schema for updating an existing subgroup."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=200, description="Subgroup name"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Subgroup description"
    )
    selection_mode: Optional[str] = Field(
        None, pattern="^(single|multi)$", description="Selection mode"
    )
    is_active: Optional[bool] = Field(None, description="Active status")


class SubgroupResponse(BaseModel):
    """Response schema for subgroup data."""

    id: str = Field(..., description="Subgroup ID")
    group_id: str = Field(..., description="Parent group ID")
    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Subgroup name")
    description: Optional[str] = Field(None, description="Subgroup description")
    selection_mode: str = Field(..., description="Selection mode: 'single' or 'multi'")
    member_count: int = Field(..., description="Number of members in this subgroup")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_active: bool = Field(..., description="Active status")


# ============================================================================
# MEMBER ASSIGNMENT SCHEMAS
# ============================================================================


class AssignMemberToSubgroupRequest(BaseModel):
    """Request schema for assigning a member to a subgroup."""

    user_id: str = Field(..., description="User ID to assign")


class RemoveMemberFromSubgroupRequest(BaseModel):
    """Request schema for removing a member from a subgroup."""

    user_id: str = Field(..., description="User ID to remove")


class SubgroupMemberResponse(BaseModel):
    """Response schema for member in a subgroup."""

    id: str = Field(..., description="User ID")
    name: Optional[str] = Field(None, description="User name")
    full_name: Optional[str] = Field(None, description="Full name")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    joined_at: datetime = Field(..., description="When joined this subgroup")
    assigned_by_user_id: str = Field(..., description="Who assigned this member")


class MemberSubgroupResponse(BaseModel):
    """Response schema for a member's subgroup membership."""

    group_id: str = Field(..., description="Group ID")
    group_name: str = Field(..., description="Group name")
    subgroup_id: str = Field(..., description="Subgroup ID")
    subgroup_name: str = Field(..., description="Subgroup name")
    selection_mode: str = Field(..., description="Selection mode: 'single' or 'multi'")
    joined_at: datetime = Field(..., description="Join timestamp")
    is_active: bool = Field(..., description="Active status")


class GroupWithSubgroupsResponse(BaseModel):
    """Response schema for group with its subgroups."""

    id: str = Field(..., description="Group ID")
    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    created_by_user_id: str = Field(..., description="Creator user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_active: bool = Field(..., description="Active status")
    subgroups: List[SubgroupResponse] = Field(
        default_factory=list, description="Subgroups in this group"
    )
