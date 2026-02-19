"""
Group Management API Routes.

Handles groups, subgroups, and member assignments with admin-only access control.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime

from app.api.dependencies import get_current_user_profile, require_roles
from app.models.user import User
from app.services.group_service import GroupService
from app.schemas.groups import (
    CreateGroupRequest,
    UpdateGroupRequest,
    GroupResponse,
    CreateSubgroupRequest,
    UpdateSubgroupRequest,
    SubgroupResponse,
    AssignMemberToSubgroupRequest,
    RemoveMemberFromSubgroupRequest,
    SubgroupMemberResponse,
    MemberSubgroupResponse,
    GroupWithSubgroupsResponse
)
from app.core.database import get_database
from bson import ObjectId

router = APIRouter()
group_service = GroupService()


# Helper Functions

async def get_organization_id(current_user: User) -> str:
    """
    Get organization ID for current user.

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

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Default organization not found"
    )


# ============================================================================
# GROUP ENDPOINTS
# ============================================================================


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    request: CreateGroupRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Create a new group (admin only).

    Args:
        request: Group creation data
        current_user: Authenticated admin user

    Returns:
        GroupResponse: Created group data

    Raises:
        HTTPException: If creation fails
    """
    try:
        org_id = await get_organization_id(current_user)
        group_service.set_database(get_database())

        group = await group_service.create_group(
            group_data=request.model_dump(exclude_unset=True),
            organization_id=org_id,
            created_by_user_id=str(current_user.id)
        )

        # Get subgroup count
        subgroups = await group_service.get_subgroups(group_id=str(group.id))

        return GroupResponse(
            id=str(group.id),
            organization_id=str(group.organization_id),
            name=group.name,
            description=group.description,
            created_by_user_id=str(group.created_by_user_id),
            created_at=group.created_at,
            updated_at=group.updated_at,
            is_active=group.is_active,
            subgroup_count=len(subgroups)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create group: {str(e)}"
        )


@router.get("", response_model=List[GroupResponse])
async def list_groups(
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(require_roles("admin"))
):
    """
    List all groups for the organization (admin only).

    Args:
        is_active: Filter by active status
        limit: Maximum number of groups to return
        skip: Number of groups to skip (pagination)
        current_user: Authenticated admin user

    Returns:
        List[GroupResponse]: List of groups
    """
    try:
        org_id = await get_organization_id(current_user)
        group_service.set_database(get_database())

        groups = await group_service.get_groups(
            organization_id=org_id,
            is_active=is_active,
            limit=limit,
            skip=skip
        )

        results = []
        for group in groups:
            subgroups = await group_service.get_subgroups(group_id=str(group.id))
            results.append(GroupResponse(
                id=str(group.id),
                organization_id=str(group.organization_id),
                name=group.name,
                description=group.description,
                created_by_user_id=str(group.created_by_user_id),
                created_at=group.created_at,
                updated_at=group.updated_at,
                is_active=group.is_active,
                subgroup_count=len(subgroups)
            ))

        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch groups: {str(e)}"
        )


@router.get("/{group_id}", response_model=GroupWithSubgroupsResponse)
async def get_group(
    group_id: str,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Get a group by ID with its subgroups (admin only).

    Args:
        group_id: Group ID
        current_user: Authenticated admin user

    Returns:
        GroupWithSubgroupsResponse: Group with subgroups
    """
    try:
        group_service.set_database(get_database())
        group = await group_service.get_group(group_id=group_id)

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group {group_id} not found"
            )

        subgroups = await group_service.get_subgroups(group_id=group_id)
        subgroup_responses = [
            SubgroupResponse(
                id=str(sg.id),
                group_id=str(sg.group_id),
                organization_id=str(sg.organization_id),
                name=sg.name,
                description=sg.description,
                selection_mode=sg.selection_mode,
                member_count=sg.member_count,
                created_at=sg.created_at,
                updated_at=sg.updated_at,
                is_active=sg.is_active
            ) for sg in subgroups
        ]

        return GroupWithSubgroupsResponse(
            id=str(group.id),
            organization_id=str(group.organization_id),
            name=group.name,
            description=group.description,
            created_by_user_id=str(group.created_by_user_id),
            created_at=group.created_at,
            updated_at=group.updated_at,
            is_active=group.is_active,
            subgroups=subgroup_responses
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch group: {str(e)}"
        )


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: str,
    request: UpdateGroupRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Update a group (admin only).

    Args:
        group_id: Group ID
        request: Update data
        current_user: Authenticated admin user

    Returns:
        GroupResponse: Updated group
    """
    try:
        group_service.set_database(get_database())
        group = await group_service.update_group(
            group_id=group_id,
            update_data=request.model_dump(exclude_unset=True)
        )

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group {group_id} not found"
            )

        subgroups = await group_service.get_subgroups(group_id=group_id)

        return GroupResponse(
            id=str(group.id),
            organization_id=str(group.organization_id),
            name=group.name,
            description=group.description,
            created_by_user_id=str(group.created_by_user_id),
            created_at=group.created_at,
            updated_at=group.updated_at,
            is_active=group.is_active,
            subgroup_count=len(subgroups)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update group: {str(e)}"
        )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: str,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Soft delete a group (admin only).

    Args:
        group_id: Group ID
        current_user: Authenticated admin user
    """
    try:
        group_service.set_database(get_database())
        success = await group_service.delete_group(group_id=group_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group {group_id} not found"
            )

        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete group: {str(e)}"
        )


# ============================================================================
# SUBGROUP ENDPOINTS
# ============================================================================


@router.post("/{group_id}/subgroups", response_model=SubgroupResponse, status_code=status.HTTP_201_CREATED)
async def create_subgroup(
    group_id: str,
    request: CreateSubgroupRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Create a new subgroup under a group (admin only).

    Args:
        group_id: Parent group ID
        request: Subgroup creation data
        current_user: Authenticated admin user

    Returns:
        SubgroupResponse: Created subgroup
    """
    try:
        org_id = await get_organization_id(current_user)
        group_service.set_database(get_database())

        subgroup = await group_service.create_subgroup(
            group_id=group_id,
            subgroup_data=request.model_dump(exclude_unset=True),
            organization_id=org_id
        )

        return SubgroupResponse(
            id=str(subgroup.id),
            group_id=str(subgroup.group_id),
            organization_id=str(subgroup.organization_id),
            name=subgroup.name,
            description=subgroup.description,
            selection_mode=subgroup.selection_mode,
            member_count=subgroup.member_count,
            created_at=subgroup.created_at,
            updated_at=subgroup.updated_at,
            is_active=subgroup.is_active
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subgroup: {str(e)}"
        )


@router.get("/{group_id}/subgroups", response_model=List[SubgroupResponse])
async def list_subgroups(
    group_id: str,
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(require_roles("admin"))
):
    """
    List all subgroups for a group (admin only).

    Args:
        group_id: Group ID
        is_active: Filter by active status
        limit: Maximum number of subgroups
        skip: Number to skip (pagination)
        current_user: Authenticated admin user

    Returns:
        List[SubgroupResponse]: List of subgroups
    """
    try:
        group_service.set_database(get_database())
        subgroups = await group_service.get_subgroups(
            group_id=group_id,
            is_active=is_active,
            limit=limit,
            skip=skip
        )

        return [
            SubgroupResponse(
                id=str(sg.id),
                group_id=str(sg.group_id),
                organization_id=str(sg.organization_id),
                name=sg.name,
                description=sg.description,
                selection_mode=sg.selection_mode,
                member_count=sg.member_count,
                created_at=sg.created_at,
                updated_at=sg.updated_at,
                is_active=sg.is_active
            ) for sg in subgroups
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch subgroups: {str(e)}"
        )


@router.put("/subgroups/{subgroup_id}", response_model=SubgroupResponse)
async def update_subgroup(
    subgroup_id: str,
    request: UpdateSubgroupRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Update a subgroup (admin only).

    Args:
        subgroup_id: Subgroup ID
        request: Update data
        current_user: Authenticated admin user

    Returns:
        SubgroupResponse: Updated subgroup
    """
    try:
        group_service.set_database(get_database())
        subgroup = await group_service.update_subgroup(
            subgroup_id=subgroup_id,
            update_data=request.model_dump(exclude_unset=True)
        )

        if not subgroup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subgroup {subgroup_id} not found"
            )

        return SubgroupResponse(
            id=str(subgroup.id),
            group_id=str(subgroup.group_id),
            organization_id=str(subgroup.organization_id),
            name=subgroup.name,
            description=subgroup.description,
            selection_mode=subgroup.selection_mode,
            member_count=subgroup.member_count,
            created_at=subgroup.created_at,
            updated_at=subgroup.updated_at,
            is_active=subgroup.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update subgroup: {str(e)}"
        )


@router.delete("/subgroups/{subgroup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subgroup(
    subgroup_id: str,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Soft delete a subgroup (admin only).

    Args:
        subgroup_id: Subgroup ID
        current_user: Authenticated admin user
    """
    try:
        group_service.set_database(get_database())
        success = await group_service.delete_subgroup(subgroup_id=subgroup_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subgroup {subgroup_id} not found"
            )

        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete subgroup: {str(e)}"
        )


# ============================================================================
# MEMBER ASSIGNMENT ENDPOINTS
# ============================================================================


@router.post("/subgroups/{subgroup_id}/assign-member", status_code=status.HTTP_200_OK)
async def assign_member_to_subgroup(
    subgroup_id: str,
    request: AssignMemberToSubgroupRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Assign a member to a subgroup (admin only).

    Automatically enforces single-select constraint if applicable.

    Args:
        subgroup_id: Subgroup ID
        request: Assignment request with user_id
        current_user: Authenticated admin user

    Returns:
        Success message
    """
    try:
        group_service.set_database(get_database())
        await group_service.assign_member_to_subgroup(
            user_id=request.user_id,
            subgroup_id=subgroup_id,
            assigned_by_user_id=str(current_user.id)
        )

        return {"message": "Member assigned successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign member: {str(e)}"
        )


@router.post("/subgroups/{subgroup_id}/remove-member", status_code=status.HTTP_200_OK)
async def remove_member_from_subgroup(
    subgroup_id: str,
    request: RemoveMemberFromSubgroupRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Remove a member from a subgroup (admin only).

    Args:
        subgroup_id: Subgroup ID
        request: Removal request with user_id
        current_user: Authenticated admin user

    Returns:
        Success message
    """
    try:
        group_service.set_database(get_database())
        await group_service.remove_member_from_subgroup(
            user_id=request.user_id,
            subgroup_id=subgroup_id
        )

        return {"message": "Member removed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove member: {str(e)}"
        )


@router.get("/subgroups/{subgroup_id}/members", response_model=List[SubgroupMemberResponse])
async def get_subgroup_members(
    subgroup_id: str,
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(require_roles("admin"))
):
    """
    Get all members in a subgroup (admin only).

    Args:
        subgroup_id: Subgroup ID
        limit: Maximum number of members
        skip: Number to skip (pagination)
        current_user: Authenticated admin user

    Returns:
        List[SubgroupMemberResponse]: List of members
    """
    try:
        group_service.set_database(get_database())
        members = await group_service.get_subgroup_members(
            subgroup_id=subgroup_id,
            limit=limit,
            skip=skip
        )

        results = []
        for member in members:
            # Find this subgroup's membership data
            membership = next(
                (m for m in member.subgroup_memberships if str(m.subgroup_id) == subgroup_id),
                None
            )

            results.append(SubgroupMemberResponse(
                id=str(member.id),
                name=member.name,
                full_name=member.full_name,
                phone=member.phone,
                email=member.email,
                joined_at=membership.joined_at if membership else datetime.utcnow(),
                assigned_by_user_id=str(membership.assigned_by_user_id) if membership else ""
            ))

        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch members: {str(e)}"
        )


@router.get("/members/{user_id}/subgroups", response_model=List[MemberSubgroupResponse])
async def get_member_subgroups(
    user_id: str,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Get all subgroups a member belongs to (admin only).

    Returns enriched data with group and subgroup names.

    Args:
        user_id: User ID
        current_user: Authenticated admin user

    Returns:
        List[MemberSubgroupResponse]: Enriched membership data
    """
    try:
        group_service.set_database(get_database())
        memberships = await group_service.get_member_subgroups(user_id=user_id)

        return [
            MemberSubgroupResponse(
                group_id=m["group_id"],
                group_name=m["group_name"],
                subgroup_id=m["subgroup_id"],
                subgroup_name=m["subgroup_name"],
                selection_mode=m["selection_mode"],
                joined_at=m["joined_at"],
                is_active=m["is_active"]
            ) for m in memberships
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch member subgroups: {str(e)}"
        )
