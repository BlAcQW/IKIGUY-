"""
First Timer Management API Routes.

Handles first-time visitors and their journey toward membership.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user_profile, require_roles, get_optional_organization_id
from app.models.user import User
from app.services.first_timer_service import FirstTimerService
from app.schemas.first_timer import (
    CreateFirstTimerRequest,
    UpdateFirstTimerRequest,
    UpdateFollowUpRequest,
    ConvertToMemberRequest,
    FirstTimerResponse,
    FirstTimerListResponse,
    FirstTimerStatsResponse,
    ConvertToMemberResponse
)
from app.core.database import get_database
from bson import ObjectId

router = APIRouter()


# Helper Functions

async def get_organization_id(current_user: User) -> str:
    """
    Get organization ID for current user.

    Args:
        current_user: Current authenticated user

    Returns:
        str: Organization ID
    """
    if current_user.organization_id:
        return str(current_user.organization_id)

    # Fetch default organization from database
    db = get_database()
    org = await db.organizations.find_one({"is_active": True})
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active organization found"
        )
    return str(org["_id"])


def first_timer_to_response(first_timer) -> FirstTimerResponse:
    """
    Convert FirstTimer model to response schema.

    Args:
        first_timer: FirstTimer model instance

    Returns:
        FirstTimerResponse object
    """
    return FirstTimerResponse(
        id=str(first_timer.id),
        organization_id=str(first_timer.organization_id),
        branch_id=str(first_timer.branch_id) if first_timer.branch_id else None,
        first_name=first_timer.first_name,
        last_name=first_timer.last_name,
        full_name=first_timer.full_name,
        phone=first_timer.phone,
        email=first_timer.email,
        date_of_birth=first_timer.date_of_birth,
        gender=first_timer.gender,
        address=first_timer.address,
        visit_date=first_timer.visit_date,
        visit_type=first_timer.visit_type,
        service_attended=first_timer.service_attended,
        interest_type=first_timer.interest_type,
        wants_membership=first_timer.wants_membership,
        wants_discipleship=first_timer.wants_discipleship,
        how_heard_about_us=first_timer.how_heard_about_us,
        invited_by=first_timer.invited_by,
        follow_up_status=first_timer.follow_up_status,
        follow_up_notes=first_timer.follow_up_notes,
        assigned_to_user_id=str(first_timer.assigned_to_user_id) if first_timer.assigned_to_user_id else None,
        last_contact_date=first_timer.last_contact_date,
        next_follow_up_date=first_timer.next_follow_up_date,
        converted_to_member=first_timer.converted_to_member,
        member_id=str(first_timer.member_id) if first_timer.member_id else None,
        conversion_date=first_timer.conversion_date,
        created_by_user_id=str(first_timer.created_by_user_id),
        created_at=first_timer.created_at,
        updated_at=first_timer.updated_at,
        is_active=first_timer.is_active
    )


# API Endpoints

@router.post("/", response_model=FirstTimerResponse, status_code=status.HTTP_201_CREATED)
async def create_first_timer(
    request: CreateFirstTimerRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Create a new first timer record.

    Requires admin role.

    Args:
        request: First timer creation data
        current_user: Current authenticated admin user

    Returns:
        Created FirstTimer object

    Raises:
        HTTPException: If creation fails
    """
    try:
        db = get_database()
        service = FirstTimerService(db)

        organization_id = await get_organization_id(current_user)

        # Convert request to dict
        first_timer_data = request.model_dump(exclude_none=True)

        # Convert branch_id to ObjectId if provided
        if request.branch_id:
            first_timer_data["branch_id"] = ObjectId(request.branch_id)

        first_timer = await service.create_first_timer(
            first_timer_data=first_timer_data,
            organization_id=organization_id,
            created_by_user_id=str(current_user.id)
        )

        return first_timer_to_response(first_timer)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create first timer: {str(e)}"
        )


@router.post("/public", response_model=FirstTimerResponse, status_code=status.HTTP_201_CREATED)
async def create_public_first_timer(
    request: CreateFirstTimerRequest,
    organization_id: str = Depends(get_optional_organization_id)
):
    """
    Create a new first timer record (public endpoint, no authentication required).
    
    Allows unauthenticated users to submit their information as first-time visitors.

    Args:
        request: First timer creation data
        organization_id: Organization ID (from header or default)

    Returns:
        Created FirstTimer object

    Raises:
        HTTPException: If creation fails
    """
    try:
        db = get_database()
        service = FirstTimerService(db)

        # Convert request to dict
        first_timer_data = request.model_dump(exclude_none=True)

        # Convert branch_id to ObjectId if provided
        if request.branch_id:
            first_timer_data["branch_id"] = ObjectId(request.branch_id)

        # For public submissions, use "system" as created_by_user_id
        first_timer = await service.create_first_timer(
            first_timer_data=first_timer_data,
            organization_id=organization_id,
            created_by_user_id="system"  # Public submission uses system user
        )

        return first_timer_to_response(first_timer)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create first timer: {str(e)}"
        )


@router.get("/", response_model=FirstTimerListResponse)
async def get_first_timers(
    branch_id: Optional[str] = Query(None, description="Filter by branch"),
    interest_type: Optional[str] = Query(None, description="Filter by interest type"),
    follow_up_status: Optional[str] = Query(None, description="Filter by follow-up status"),
    converted_to_member: Optional[bool] = Query(None, description="Filter by conversion status"),
    is_active: bool = Query(True, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(require_roles("admin"))
):
    """
    Get paginated list of first timers with optional filters.

    Requires admin role.

    Args:
        branch_id: Optional branch filter
        interest_type: Optional interest type filter
        follow_up_status: Optional follow-up status filter
        converted_to_member: Optional conversion filter
        is_active: Active status filter
        page: Page number
        page_size: Items per page
        current_user: Current authenticated admin user

    Returns:
        Paginated list of first timers

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        db = get_database()
        service = FirstTimerService(db)

        organization_id = await get_organization_id(current_user)

        result = await service.get_first_timers(
            organization_id=organization_id,
            branch_id=branch_id,
            interest_type=interest_type,
            follow_up_status=follow_up_status,
            converted_to_member=converted_to_member,
            is_active=is_active,
            page=page,
            page_size=page_size
        )

        return FirstTimerListResponse(
            items=[first_timer_to_response(ft) for ft in result["items"]],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve first timers: {str(e)}"
        )


@router.get("/stats", response_model=FirstTimerStatsResponse)
async def get_first_timer_stats(
    branch_id: Optional[str] = Query(None, description="Filter by branch"),
    current_user: User = Depends(require_roles("admin"))
):
    """
    Get statistics for first timer dashboard.

    Requires admin role.

    Args:
        branch_id: Optional branch filter
        current_user: Current authenticated admin user

    Returns:
        First timer statistics

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        db = get_database()
        service = FirstTimerService(db)

        organization_id = await get_organization_id(current_user)

        stats = await service.get_first_timer_stats(
            organization_id=organization_id,
            branch_id=branch_id
        )

        return FirstTimerStatsResponse(
            total_first_timers=stats.total_first_timers,
            today=stats.today,
            this_week=stats.this_week,
            this_month=stats.this_month,
            visitors=stats.visitors,
            new_converts=stats.new_converts,
            existing_members=stats.existing_members,
            discipleship_interested=stats.discipleship_interested,
            pending_follow_up=stats.pending_follow_up,
            contacted=stats.contacted,
            in_progress=stats.in_progress,
            converted=stats.converted,
            lost=stats.lost,
            conversion_rate=stats.conversion_rate
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


@router.get("/{first_timer_id}", response_model=FirstTimerResponse)
async def get_first_timer(
    first_timer_id: str,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Get first timer by ID.

    Requires admin role.

    Args:
        first_timer_id: First timer ID
        current_user: Current authenticated admin user

    Returns:
        FirstTimer object

    Raises:
        HTTPException: If not found
    """
    try:
        db = get_database()
        service = FirstTimerService(db)

        first_timer = await service.get_first_timer_by_id(first_timer_id)

        if not first_timer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"First timer {first_timer_id} not found"
            )

        # Verify organization access
        organization_id = await get_organization_id(current_user)
        if str(first_timer.organization_id) != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        return first_timer_to_response(first_timer)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve first timer: {str(e)}"
        )


@router.put("/{first_timer_id}", response_model=FirstTimerResponse)
async def update_first_timer(
    first_timer_id: str,
    request: UpdateFirstTimerRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Update first timer record.

    Requires admin role.

    Args:
        first_timer_id: First timer ID
        request: Update data
        current_user: Current authenticated admin user

    Returns:
        Updated FirstTimer object

    Raises:
        HTTPException: If not found or update fails
    """
    try:
        db = get_database()
        service = FirstTimerService(db)

        # Verify exists and access
        first_timer = await service.get_first_timer_by_id(first_timer_id)
        if not first_timer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"First timer {first_timer_id} not found"
            )

        organization_id = await get_organization_id(current_user)
        if str(first_timer.organization_id) != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Update
        update_data = request.model_dump(exclude_none=True)
        updated = await service.update_first_timer(first_timer_id, update_data)

        return first_timer_to_response(updated)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update first timer: {str(e)}"
        )


@router.delete("/{first_timer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_first_timer(
    first_timer_id: str,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Soft delete first timer (set is_active to False).

    Requires admin role.

    Args:
        first_timer_id: First timer ID
        current_user: Current authenticated admin user

    Raises:
        HTTPException: If not found or delete fails
    """
    try:
        db = get_database()
        service = FirstTimerService(db)

        # Verify exists and access
        first_timer = await service.get_first_timer_by_id(first_timer_id)
        if not first_timer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"First timer {first_timer_id} not found"
            )

        organization_id = await get_organization_id(current_user)
        if str(first_timer.organization_id) != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Delete
        await service.delete_first_timer(first_timer_id)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete first timer: {str(e)}"
        )


class BulkDeleteRequest(BaseModel):
    """Request model for bulk delete."""

    ids: List[str] = Field(..., description="List of first timer IDs to delete", min_length=1)


@router.post("/bulk-delete")
async def bulk_delete_first_timers(
    request: BulkDeleteRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Bulk delete multiple first timers.

    Requires admin role.

    Args:
        request: List of first timer IDs to delete
        current_user: Current authenticated admin user

    Returns:
        Summary of deleted first timers
    """
    try:
        from bson import ObjectId

        db = get_database()
        organization_id = await get_organization_id(current_user)

        # Convert string IDs to ObjectIds
        object_ids = []
        for first_timer_id in request.ids:
            try:
                object_ids.append(ObjectId(first_timer_id))
            except Exception:
                pass  # Skip invalid IDs

        if not object_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid first timer IDs provided"
            )

        # Soft delete (set is_active to False) for all matching records in this organization
        result = await db.first_timers.update_many(
            {
                "_id": {"$in": object_ids},
                "organization_id": ObjectId(organization_id)
            },
            {"$set": {"is_active": False}}
        )

        return {
            "status": "success",
            "message": f"Deleted {result.modified_count} first timers",
            "deleted_count": result.modified_count,
            "requested_count": len(request.ids)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk delete first timers: {str(e)}"
        )


@router.put("/{first_timer_id}/follow-up", response_model=FirstTimerResponse)
async def update_follow_up(
    first_timer_id: str,
    request: UpdateFollowUpRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Update follow-up status and related fields.

    Requires admin role.

    Args:
        first_timer_id: First timer ID
        request: Follow-up update data
        current_user: Current authenticated admin user

    Returns:
        Updated FirstTimer object

    Raises:
        HTTPException: If not found or update fails
    """
    try:
        db = get_database()
        service = FirstTimerService(db)

        # Verify exists and access
        first_timer = await service.get_first_timer_by_id(first_timer_id)
        if not first_timer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"First timer {first_timer_id} not found"
            )

        organization_id = await get_organization_id(current_user)
        if str(first_timer.organization_id) != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Update follow-up
        updated = await service.update_follow_up_status(
            first_timer_id=first_timer_id,
            follow_up_status=request.follow_up_status,
            follow_up_notes=request.follow_up_notes,
            assigned_to_user_id=request.assigned_to_user_id,
            next_follow_up_date=request.next_follow_up_date
        )

        return first_timer_to_response(updated)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update follow-up: {str(e)}"
        )


@router.post("/{first_timer_id}/convert-to-member", response_model=ConvertToMemberResponse)
async def convert_to_member(
    first_timer_id: str,
    request: ConvertToMemberRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Convert first timer to full member (create User account).

    Requires admin role.

    Args:
        first_timer_id: First timer ID
        request: Conversion data
        current_user: Current authenticated admin user

    Returns:
        Conversion result with first timer and user info

    Raises:
        HTTPException: If not found or conversion fails
    """
    try:
        db = get_database()
        service = FirstTimerService(db)

        # Verify exists and access
        first_timer = await service.get_first_timer_by_id(first_timer_id)
        if not first_timer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"First timer {first_timer_id} not found"
            )

        organization_id = await get_organization_id(current_user)
        if str(first_timer.organization_id) != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Prepare additional user data
        additional_user_data = {
            "role": request.role or "member"
        }

        # Convert department_ids to ObjectIds if provided
        if request.department_ids:
            # Note: Department assignment logic would go here
            # For now, just pass the department_ids
            pass

        # Convert to member
        result = await service.convert_to_member(
            first_timer_id=first_timer_id,
            converted_by_user_id=str(current_user.id),
            additional_user_data=additional_user_data
        )

        return ConvertToMemberResponse(
            first_timer=first_timer_to_response(result["first_timer"]),
            user_id=str(result["user"].id),
            is_new_user=result["is_new_user"],
            message="Successfully converted first timer to member"
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert to member: {str(e)}"
        )
