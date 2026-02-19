"""
API routes for school management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from typing import Optional, List

import sys
sys.path.insert(0, "/opt/kasaai/apps")

from app.core.auth import get_current_user, get_current_user_with_org, OrganizationRoleChecker
from app.models.user import UserRole
from app.models.school import (
    SchoolCreate,
    SchoolUpdate,
    SchoolResponse,
    SchoolStats
)
from app.services.school_service import SchoolService

router = APIRouter(prefix="/schools", tags=["schools"])

# Role checker for admin operations
require_admin = OrganizationRoleChecker([UserRole.ADMIN])


@router.post("/", response_model=SchoolResponse)
async def create_school(
    school_data: SchoolCreate,
    user_context: dict = Depends(require_admin)
):
    """
    Create a new school (Admin only) with organization context.

    Args:
        school_data: School creation data
        user_context: User context with organization info

    Returns:
        Created school
    """
    try:
        # Ensure school belongs to user's organization
        organization_id = user_context["organization_id"]
        if not school_data.organization_id:
            school_data.organization_id = organization_id

        school = await SchoolService.create_school(school_data)
        return SchoolResponse(
            id=school.id,
            organization_id=school.organization_id,
            name=school.name,
            short_name=school.short_name,
            school_type=school.school_type,
            website=str(school.website) if school.website else None,
            email=school.email,
            phone=school.phone,
            city=school.city,
            country=school.country,
            logo_url=school.logo_url,
            subscription_tier=school.subscription_tier,
            is_active=school.is_active,
            created_at=school.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create school: {str(e)}")


@router.get("/", response_model=List[SchoolResponse])
async def list_schools(
    skip: int = Query(0, ge=0, description="Number of schools to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of schools"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    List schools with organization filtering.

    Available to all authenticated users. Returns only schools in user's organization.

    Args:
        skip: Pagination offset
        limit: Maximum results
        is_active: Filter by active status
        user_context: User context with organization info

    Returns:
        List of schools in the user's organization
    """
    try:
        organization_id = user_context["organization_id"]

        schools = await SchoolService.list_schools(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            is_active=is_active
        )
        return [
            SchoolResponse(
                id=school.id,
                organization_id=school.organization_id,
                name=school.name,
                short_name=school.short_name,
                school_type=school.school_type,
                website=str(school.website) if school.website else None,
                email=school.email,
                phone=school.phone,
                city=school.city,
                country=school.country,
                logo_url=school.logo_url,
                subscription_tier=school.subscription_tier,
                is_active=school.is_active,
                created_at=school.created_at
            )
            for school in schools
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list schools: {str(e)}")


@router.get("/me", response_model=SchoolResponse)
async def get_my_school(
    current_user: dict = Security(get_current_user)
):
    """
    Get current user's school (for school admin users).

    Returns:
        School information
    """
    user_role = current_user.get("user_metadata", {}).get("role")

    if user_role != UserRole.SCHOOL.value:
        raise HTTPException(
            status_code=403,
            detail="Only school accounts can access this endpoint"
        )

    user_id = current_user.get("sub")
    school = await SchoolService.get_school_by_admin(user_id)

    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    return SchoolResponse(
        id=school.id,
        name=school.name,
        short_name=school.short_name,
        school_type=school.school_type,
        website=str(school.website) if school.website else None,
        email=school.email,
        phone=school.phone,
        city=school.city,
        country=school.country,
        logo_url=school.logo_url,
        subscription_tier=school.subscription_tier,
        is_active=school.is_active,
        created_at=school.created_at
    )


@router.get("/{school_id}", response_model=SchoolResponse)
async def get_school(
    school_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get school by ID with organization access control.

    Available to all authenticated users. Returns only if school is in user's organization.

    Args:
        school_id: School ID
        user_context: User context with organization info

    Returns:
        School information
    """
    organization_id = user_context["organization_id"]

    school = await SchoolService.get_school(school_id, organization_id=organization_id)

    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    return SchoolResponse(
        id=school.id,
        organization_id=school.organization_id,
        name=school.name,
        short_name=school.short_name,
        school_type=school.school_type,
        website=str(school.website) if school.website else None,
        email=school.email,
        phone=school.phone,
        city=school.city,
        country=school.country,
        logo_url=school.logo_url,
        subscription_tier=school.subscription_tier,
        is_active=school.is_active,
        created_at=school.created_at
    )


@router.get("/{school_id}/stats", response_model=SchoolStats)
async def get_school_stats(
    school_id: str,
    current_user: dict = Security(get_current_user)
):
    """
    Get statistics for a school.

    School admins can view their own stats.
    System admins can view any school's stats.

    Args:
        school_id: School ID
        current_user: Current authenticated user

    Returns:
        School statistics
    """
    user_role = current_user.get("user_metadata", {}).get("role")
    user_id = current_user.get("sub")

    # Check authorization
    if user_role == UserRole.SCHOOL.value:
        # School can only view their own stats
        school = await SchoolService.get_school_by_admin(user_id)
        if not school or school.id != school_id:
            raise HTTPException(
                status_code=403,
                detail="You can only view your own school's statistics"
            )
    elif user_role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=403,
            detail="Only school admins and system admins can view school statistics"
        )

    try:
        stats = await SchoolService.get_school_stats(school_id)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get school stats: {str(e)}")


@router.put("/{school_id}", response_model=SchoolResponse)
async def update_school(
    school_id: str,
    update_data: SchoolUpdate,
    current_user: dict = Security(get_current_user)
):
    """
    Update school information.

    School admins can update their own school.
    System admins can update any school.

    Args:
        school_id: School ID
        update_data: Update data
        current_user: Current authenticated user

    Returns:
        Updated school
    """
    user_role = current_user.get("user_metadata", {}).get("role")
    user_id = current_user.get("sub")

    # Check authorization
    if user_role == UserRole.SCHOOL.value:
        # School can only update their own info
        school = await SchoolService.get_school_by_admin(user_id)
        if not school or school.id != school_id:
            raise HTTPException(
                status_code=403,
                detail="You can only update your own school's information"
            )
    elif user_role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=403,
            detail="Only school admins and system admins can update schools"
        )

    # Update school
    success = await SchoolService.update_school(school_id, update_data)

    if not success:
        raise HTTPException(status_code=404, detail="School not found or no changes made")

    # Return updated school
    school = await SchoolService.get_school(school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    return SchoolResponse(
        id=school.id,
        name=school.name,
        short_name=school.short_name,
        school_type=school.school_type,
        website=str(school.website) if school.website else None,
        email=school.email,
        phone=school.phone,
        city=school.city,
        country=school.country,
        logo_url=school.logo_url,
        subscription_tier=school.subscription_tier,
        is_active=school.is_active,
        created_at=school.created_at
    )


@router.delete("/{school_id}")
async def delete_school(
    school_id: str,
    current_user: dict = Security(require_admin)
):
    """
    Delete school (Admin only).

    Performs soft delete by setting is_active=False.

    Args:
        school_id: School ID
        current_user: Current authenticated admin user

    Returns:
        Success message
    """
    success = await SchoolService.delete_school(school_id)

    if not success:
        raise HTTPException(status_code=404, detail="School not found")

    return {"message": "School deleted successfully"}
