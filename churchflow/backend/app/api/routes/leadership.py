"""
Leadership & Organizational Structure API Routes.

Handles cell groups, zones, and departments management with
hierarchical leadership assignments.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.api.dependencies import get_current_user_profile, require_roles
from app.models.user import User
from app.services.leadership_service import leadership_service
from app.services.visitor_service import visitor_service
from app.core.database import get_database
from bson import ObjectId

router = APIRouter()


# Helper Functions

async def get_organization_id(current_user: User) -> str:
    """
    Get organization ID for current user.

    If user has branch_id, use that as organization_id.
    Otherwise, fetch the default organization ID from database.

    Args:
        current_user: Current authenticated user

    Returns:
        str: Organization ID
    """
    if current_user.branch_id:
        return str(current_user.branch_id)

    # Fetch default organization from database
    db = get_database()
    default_org = await db.organizations.find_one({"name": "ai-labs-ltd"})

    if default_org:
        return str(default_org["_id"])

    # Fallback: create a valid ObjectId from "default" string
    # This should not happen in production if default org is properly initialized
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Default organization not found"
    )


# Request/Response Models

class CreateCellGroupRequest(BaseModel):
    """Request model for creating cell group."""

    name: str = Field(..., min_length=1, description="Cell group name")
    description: Optional[str] = None
    branch_id: Optional[str] = None
    zone_id: Optional[str] = None
    cell_leader_id: Optional[str] = None
    assistant_leaders: List[str] = Field(default_factory=list)
    meeting_day: Optional[str] = None
    meeting_time: Optional[str] = None
    meeting_location: Optional[str] = None
    target_size: int = Field(default=12, ge=1, le=50)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Adenta Fellowship Group",
                "description": "Cell group for Adenta area members",
                "zone_id": "507f1f77bcf86cd799439011",
                "cell_leader_id": "507f1f77bcf86cd799439012",
                "meeting_day": "Wednesday",
                "meeting_time": "18:00",
                "meeting_location": "Leader's home",
                "target_size": 12
            }
        }


class CreateZoneRequest(BaseModel):
    """Request model for creating zone."""

    name: str = Field(..., min_length=1, description="Zone name")
    description: Optional[str] = None
    branch_id: Optional[str] = None
    geographic_area: Optional[str] = None
    zone_leader_id: Optional[str] = None
    assistant_zone_leaders: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Greater Accra Zone",
                "description": "Zone covering Greater Accra region",
                "geographic_area": "Accra, Tema, Kasoa",
                "zone_leader_id": "507f1f77bcf86cd799439011"
            }
        }


class CreateDepartmentRequest(BaseModel):
    """Request model for creating department."""

    name: str = Field(..., min_length=1, description="Department name")
    description: Optional[str] = None
    branch_id: Optional[str] = None
    department_type: str = Field(..., pattern="^(worship|hospitality|media|children|youth|admin|outreach)$")
    department_head_id: Optional[str] = None
    assistant_heads: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Worship Team",
                "description": "Praise and worship ministry",
                "department_type": "worship",
                "department_head_id": "507f1f77bcf86cd799439011"
            }
        }


class AssignMemberRequest(BaseModel):
    """Request model for assigning member to cell group."""

    user_id: str = Field(..., description="User ID to assign")


class AssignVolunteerRequest(BaseModel):
    """Request model for assigning volunteer to department."""

    user_id: str = Field(..., description="User ID to assign")
    role: str = Field(..., pattern="^(volunteer|leader|head)$", description="Department role")


# Cell Group Endpoints

@router.post("/cell-groups", status_code=status.HTTP_201_CREATED)
async def create_cell_group(
    request: CreateCellGroupRequest,
    current_user: User = Depends(require_roles("admin", "zone_leader"))
):
    """
    Create new cell group.

    **Required Role**: admin or zone_leader

    **Returns**: Created cell group
    """
    try:
        # Get organization ID
        organization_id = await get_organization_id(current_user)

        # Create cell group
        cell_group = await leadership_service.create_cell_group(
            cell_data=request.dict(),
            organization_id=organization_id,
            created_by_user_id=str(current_user.id)
        )

        return {
            "id": str(cell_group.id),
            "name": cell_group.name,
            "zone_id": str(cell_group.zone_id) if cell_group.zone_id else None,
            "cell_leader_id": str(cell_group.cell_leader_id) if cell_group.cell_leader_id else None,
            "current_member_count": cell_group.current_member_count,
            "target_size": cell_group.target_size,
            "status": cell_group.status,
            "message": "Cell group created successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create cell group: {str(e)}"
        )


@router.get("/cell-groups")
async def list_cell_groups(
    zone_id: Optional[str] = Query(None, description="Filter by zone"),
    is_active: bool = Query(True, description="Filter by active status"),
    limit: int = Query(default=100, ge=1, le=500),
    skip: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user_profile)
):
    """
    List cell groups.

    **Query Parameters**:
    - zone_id: Filter by zone (optional)
    - is_active: Filter by active status (default: True)
    - limit: Maximum results (default: 100, max: 500)
    - skip: Results to skip (default: 0)

    **Returns**: List of cell groups
    """
    try:
        # Get organization ID
        organization_id = await get_organization_id(current_user)

        # Fetch cell groups
        cell_groups = await leadership_service.get_cell_groups(
            organization_id=organization_id,
            zone_id=zone_id,
            is_active=is_active,
            limit=limit,
            skip=skip
        )

        # Convert to response format
        groups_list = [
            {
                "id": str(group.id),
                "name": group.name,
                "description": group.description,
                "zone_id": str(group.zone_id) if group.zone_id else None,
                "cell_leader_id": str(group.cell_leader_id) if group.cell_leader_id else None,
                "current_member_count": group.current_member_count,
                "target_size": group.target_size,
                "is_full": group.is_full,
                "status": group.status,
                "meeting_day": group.meeting_day,
                "meeting_time": group.meeting_time,
                "meeting_location": group.meeting_location
            }
            for group in cell_groups
        ]

        return {
            "cell_groups": groups_list,
            "total": len(groups_list),
            "limit": limit,
            "skip": skip
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list cell groups: {str(e)}"
        )


@router.get("/cell-groups/{cell_group_id}/members")
async def get_cell_group_members(
    cell_group_id: str,
    include_visitors: bool = Query(True, description="Include visitors"),
    limit: int = Query(default=100, ge=1, le=500),
    skip: int = Query(default=0, ge=0),
    current_user: User = Depends(require_roles("admin", "coordinator", "cell_leader", "zone_leader"))
):
    """
    Get members in a cell group.

    **Required Role**: admin, coordinator, cell_leader, or zone_leader

    **Returns**: List of cell group members
    """
    try:
        # Get cell members
        members = await leadership_service.get_cell_members(
            cell_group_id=cell_group_id,
            include_visitors=include_visitors,
            limit=limit,
            skip=skip
        )

        # Convert to response format
        members_list = [
            {
                "id": str(member.id),
                "phone": member.phone,
                "name": member.full_name or member.name,
                "email": member.email,
                "member_status": member.member_status,
                "current_spiritual_stage": member.current_spiritual_stage,
                "visit_count": member.visit_count,
                "last_visit_date": member.last_visit_date.isoformat() if member.last_visit_date else None
            }
            for member in members
        ]

        return {
            "cell_group_id": cell_group_id,
            "members": members_list,
            "total": len(members_list),
            "limit": limit,
            "skip": skip
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cell group members: {str(e)}"
        )


@router.post("/cell-groups/{cell_group_id}/assign-member")
async def assign_member_to_cell_group(
    cell_group_id: str,
    request: AssignMemberRequest,
    current_user: User = Depends(require_roles("admin", "zone_leader"))
):
    """
    Assign member to cell group.

    **Required Role**: admin or zone_leader

    **Returns**: Updated user
    """
    try:
        # Assign to cell group
        user = await visitor_service.assign_to_cell_group(
            user_id=request.user_id,
            cell_group_id=cell_group_id,
            assigned_by_user_id=str(current_user.id)
        )

        return {
            "id": str(user.id),
            "name": user.full_name or user.name,
            "cell_group_id": str(user.cell_group_id),
            "assigned_cell_leader_id": str(user.assigned_cell_leader_id) if user.assigned_cell_leader_id else None,
            "message": "Member assigned to cell group successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign member: {str(e)}"
        )


@router.post("/cell-groups/{cell_group_id}/assign-leader")
async def assign_cell_leader(
    cell_group_id: str,
    request: AssignMemberRequest,
    current_user: User = Depends(require_roles("admin", "zone_leader"))
):
    """
    Assign cell leader to cell group.

    **Required Role**: admin or zone_leader

    **Returns**: Updated cell group
    """
    try:
        # Assign cell leader
        cell_group = await leadership_service.assign_cell_leader(
            user_id=request.user_id,
            cell_group_id=cell_group_id,
            assigned_by_user_id=str(current_user.id)
        )

        return {
            "id": str(cell_group.id),
            "name": cell_group.name,
            "cell_leader_id": str(cell_group.cell_leader_id),
            "message": "Cell leader assigned successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign cell leader: {str(e)}"
        )


# Zone Endpoints

@router.post("/zones", status_code=status.HTTP_201_CREATED)
async def create_zone(
    request: CreateZoneRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Create new zone.

    **Required Role**: admin

    **Returns**: Created zone
    """
    try:
        # Get organization ID
        organization_id = await get_organization_id(current_user)

        # Create zone
        zone = await leadership_service.create_zone(
            zone_data=request.dict(),
            organization_id=organization_id,
            created_by_user_id=str(current_user.id)
        )

        return {
            "id": str(zone.id),
            "name": zone.name,
            "geographic_area": zone.geographic_area,
            "zone_leader_id": str(zone.zone_leader_id) if zone.zone_leader_id else None,
            "cell_group_count": zone.cell_group_count,
            "message": "Zone created successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create zone: {str(e)}"
        )


@router.get("/zones")
async def list_zones(
    is_active: bool = Query(True, description="Filter by active status"),
    limit: int = Query(default=100, ge=1, le=500),
    skip: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user_profile)
):
    """
    List zones.

    **Query Parameters**:
    - is_active: Filter by active status (default: True)
    - limit: Maximum results (default: 100, max: 500)
    - skip: Results to skip (default: 0)

    **Returns**: List of zones
    """
    try:
        # Get organization ID
        organization_id = await get_organization_id(current_user)

        # Fetch zones
        zones = await leadership_service.get_zones(
            organization_id=organization_id,
            is_active=is_active,
            limit=limit,
            skip=skip
        )

        # Convert to response format
        zones_list = [
            {
                "id": str(zone.id),
                "name": zone.name,
                "description": zone.description,
                "geographic_area": zone.geographic_area,
                "zone_leader_id": str(zone.zone_leader_id) if zone.zone_leader_id else None,
                "cell_group_count": zone.cell_group_count,
                "is_active": zone.is_active
            }
            for zone in zones
        ]

        return {
            "zones": zones_list,
            "total": len(zones_list),
            "limit": limit,
            "skip": skip
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list zones: {str(e)}"
        )


@router.post("/zones/{zone_id}/assign-leader")
async def assign_zone_leader(
    zone_id: str,
    request: AssignMemberRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Assign zone leader.

    **Required Role**: admin

    **Returns**: Updated zone
    """
    try:
        # Assign zone leader
        zone = await leadership_service.assign_zone_leader(
            user_id=request.user_id,
            zone_id=zone_id,
            assigned_by_user_id=str(current_user.id)
        )

        return {
            "id": str(zone.id),
            "name": zone.name,
            "zone_leader_id": str(zone.zone_leader_id),
            "message": "Zone leader assigned successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign zone leader: {str(e)}"
        )


@router.get("/zones/{zone_id}/members")
async def get_zone_members(
    zone_id: str,
    include_visitors: bool = Query(True, description="Include visitors"),
    limit: int = Query(default=200, ge=1, le=500),
    skip: int = Query(default=0, ge=0),
    current_user: User = Depends(require_roles("admin", "zone_leader"))
):
    """
    Get all members in a zone.

    **Required Role**: admin or zone_leader

    **Returns**: List of zone members
    """
    try:
        # Get zone members
        members = await leadership_service.get_zone_members(
            zone_id=zone_id,
            include_visitors=include_visitors,
            limit=limit,
            skip=skip
        )

        # Convert to response format
        members_list = [
            {
                "id": str(member.id),
                "phone": member.phone,
                "name": member.full_name or member.name,
                "email": member.email,
                "member_status": member.member_status,
                "current_spiritual_stage": member.current_spiritual_stage,
                "cell_group_id": str(member.cell_group_id) if member.cell_group_id else None
            }
            for member in members
        ]

        return {
            "zone_id": zone_id,
            "members": members_list,
            "total": len(members_list),
            "limit": limit,
            "skip": skip
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get zone members: {str(e)}"
        )


# Department Endpoints

@router.post("/departments", status_code=status.HTTP_201_CREATED)
async def create_department(
    request: CreateDepartmentRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Create new department.

    **Required Role**: admin

    **Returns**: Created department
    """
    try:
        # Get organization ID
        organization_id = await get_organization_id(current_user)

        # Create department
        department = await leadership_service.create_department(
            department_data=request.dict(),
            organization_id=organization_id,
            created_by_user_id=str(current_user.id)
        )

        return {
            "id": str(department.id),
            "name": department.name,
            "department_type": department.department_type,
            "department_head_id": str(department.department_head_id) if department.department_head_id else None,
            "volunteer_count": department.volunteer_count,
            "leader_count": department.leader_count,
            "message": "Department created successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create department: {str(e)}"
        )


@router.post("/departments/{department_id}/assign-head")
async def assign_department_head(
    department_id: str,
    request: AssignMemberRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Assign department head.

    **Required Role**: admin

    **Returns**: Updated department
    """
    try:
        # Assign department head
        department = await leadership_service.assign_department_head(
            user_id=request.user_id,
            department_id=department_id,
            assigned_by_user_id=str(current_user.id)
        )

        return {
            "id": str(department.id),
            "name": department.name,
            "department_head_id": str(department.department_head_id),
            "message": "Department head assigned successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign department head: {str(e)}"
        )


@router.post("/departments/{department_id}/assign-volunteer")
async def assign_volunteer_to_department(
    department_id: str,
    request: AssignVolunteerRequest,
    current_user: User = Depends(require_roles("admin", "department_head"))
):
    """
    Assign volunteer to department.

    **Required Role**: admin or department_head

    **Returns**: Updated user
    """
    try:
        # Assign volunteer
        user = await leadership_service.assign_volunteer_to_department(
            user_id=request.user_id,
            department_id=department_id,
            role=request.role,
            assigned_by_user_id=str(current_user.id)
        )

        return {
            "id": str(user.id),
            "name": user.full_name or user.name,
            "department_id": department_id,
            "role": request.role,
            "message": "Volunteer assigned to department successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign volunteer: {str(e)}"
        )
