"""
User profile API routes.

Endpoints for managing user profiles.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging

from app.schemas.user import UserResponse, CreateProfileRequest, UpdateProfileRequest
from app.services.user_service import user_service
from app.api.dependencies import get_current_user, get_current_user_profile, require_admin, require_organization_access
from app.models.user import User
from app.utils.header_utils import decode_organization_id

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response models
class DepartmentAssignmentRequest(BaseModel):
    """Request model for department assignment."""
    department_name: str
    action: str = "assign"  # assign or unassign


class TransitionToMemberRequest(BaseModel):
    """Request model for visitor to member transition."""
    branch_id: str


class SearchUsersResponse(BaseModel):
    """Response model for user search."""
    results: list[UserResponse]
    total: int


class RegisterExistingMemberRequest(BaseModel):
    """Request model for registering an existing church member."""
    full_name: str = Field(..., min_length=2, max_length=100, description="Member's full name")
    phone: str = Field(..., min_length=10, max_length=20, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    branch_id: str = Field(..., description="Branch ID the member belongs to")
    gender: Optional[str] = Field(None, pattern="^(male|female|other|prefer_not_to_say)$")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    address: Optional[str] = Field(None, description="Physical address")
    occupation: Optional[str] = Field(None, description="Occupation")
    marital_status: Optional[str] = Field(None, pattern="^(single|married|divorced|widowed)$")
    roles: List[str] = Field(default=["member"], description="Roles to assign")
    volunteer_roles: List[str] = Field(default_factory=list, description="Volunteer positions")
    group_ids: List[str] = Field(default_factory=list, description="Group IDs to assign")
    subgroup_ids: List[str] = Field(default_factory=list, description="Subgroup IDs to assign")


class RegisterExistingMemberResponse(BaseModel):
    """Response model for member registration."""
    id: str
    full_name: str
    phone: str
    email: Optional[str] = None
    branch_id: str
    member_status: str
    roles: List[str]
    created_at: datetime
    message: str


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get the authenticated user's profile information."
)
async def get_my_profile(current_user: User = Depends(get_current_user_profile)):
    """
    Get current user's profile.

    Args:
        current_user: Authenticated user from token

    Returns:
        UserResponse: User profile data
    """
    return UserResponse(
        id=str(current_user.id),
        phone=current_user.phone,
        name=current_user.name,
        branch_id=str(current_user.branch_id) if current_user.branch_id else None,
        roles=current_user.roles,
        volunteer_roles=current_user.volunteer_roles,
        created_at=current_user.created_at,
        last_active=current_user.last_active,
        profile_image_url=current_user.profile_image_url
    )


@router.post(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user profile",
    description="Create a new user profile after OTP verification."
)
async def create_my_profile(
    request: CreateProfileRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create user profile.

    Args:
        request: Profile creation data
        current_user: Authenticated user from token

    Returns:
        UserResponse: Created user profile

    Raises:
        HTTPException: If profile creation fails
    """
    try:
        # Check if user already exists
        existing_user = await user_service.get_user_by_phone(current_user["phone"])

        if existing_user:
            # Update existing profile instead
            user = await user_service.update_user(
                str(existing_user.id),
                request.model_dump(exclude_none=True)
            )
        else:
            # Create new user
            user = await user_service.create_user(
                phone=current_user["phone"],
                name=request.name,
                branch_id=request.branch_id,
                volunteer_roles=request.volunteer_roles or []
            )

        return UserResponse(
            id=str(user.id),
            phone=user.phone,
            name=user.name,
            branch_id=str(user.branch_id) if user.branch_id else None,
            roles=user.roles,
            volunteer_roles=user.volunteer_roles,
            created_at=user.created_at,
            last_active=user.last_active,
            profile_image_url=user.profile_image_url
        )

    except Exception as e:
        logger.error(f"Failed to create profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create profile: {str(e)}"
        )


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update user profile",
    description="Update the authenticated user's profile information."
)
async def update_my_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user_profile)
):
    """
    Update user profile.

    Args:
        request: Profile update data
        current_user: Authenticated user

    Returns:
        UserResponse: Updated user profile

    Raises:
        HTTPException: If update fails
    """
    try:
        update_data = request.model_dump(exclude_none=True)

        user = await user_service.update_user(str(current_user.id), update_data)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserResponse(
            id=str(user.id),
            phone=user.phone,
            name=user.name,
            branch_id=str(user.branch_id) if user.branch_id else None,
            roles=user.roles,
            volunteer_roles=user.volunteer_roles,
            created_at=user.created_at,
            last_active=user.last_active,
            profile_image_url=user.profile_image_url
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.get(
    "/search",
    response_model=SearchUsersResponse,
    summary="Search users",
    description="Search users by name or phone number."
)
async def search_users(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user_profile)
):
    """
    Search users by name or phone.

    Args:
        q: Search query
        limit: Maximum number of results
        current_user: Authenticated user

    Returns:
        SearchUsersResponse: List of matching users
    """
    try:
        users = await user_service.search_users(q, limit)

        results = [
            UserResponse(
                id=str(u.id),
                phone=u.phone,
                name=u.name,
                full_name=getattr(u, 'full_name', u.name),
                email=getattr(u, 'email', None),
                member_status=getattr(u, 'member_status', 'visitor'),
                branch_id=str(u.branch_id) if u.branch_id else None,
                roles=u.roles,
                volunteer_roles=u.volunteer_roles,
                created_at=u.created_at,
                last_active=u.last_active,
                profile_image_url=u.profile_image_url
            )
            for u in users
        ]

        return SearchUsersResponse(
            results=results,
            total=len(results)
        )

    except Exception as e:
        logger.error(f"Failed to search users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search users: {str(e)}"
        )


@router.put(
    "/{user_id}/departments",
    response_model=UserResponse,
    summary="Assign department to user",
    description="Assign or unassign a user to/from a department."
)
async def assign_department(
    user_id: str,
    request: DepartmentAssignmentRequest,
    current_user: User = Depends(get_current_user_profile)
):
    """
    Assign user to a department.

    Args:
        user_id: User's MongoDB ID
        request: Department assignment request
        current_user: Authenticated user (must be admin)

    Returns:
        UserResponse: Updated user profile

    Raises:
        HTTPException: If assignment fails
    """
    # TODO: Add admin role check
    # if "admin" not in current_user.roles:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Only admins can assign departments"
    #     )

    try:
        if request.action == "assign":
            user = await user_service.assign_department(user_id, request.department_name)
        else:
            # TODO: Implement unassign logic if needed
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unassign action not yet implemented"
            )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or department not in interests"
            )

        return UserResponse(
            id=str(user.id),
            phone=user.phone,
            name=user.name,
            branch_id=str(user.branch_id) if user.branch_id else None,
            roles=user.roles,
            volunteer_roles=user.volunteer_roles,
            created_at=user.created_at,
            last_active=user.last_active,
            profile_image_url=user.profile_image_url
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign department: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign department: {str(e)}"
        )


@router.post(
    "/{user_id}/transition-to-member",
    response_model=UserResponse,
    summary="Transition visitor to member",
    description="Convert a visitor to an active member with branch assignment."
)
async def transition_to_member(
    user_id: str,
    request: TransitionToMemberRequest,
    current_user: User = Depends(get_current_user_profile)
):
    """
    Transition a visitor to an active member.

    Args:
        user_id: User's MongoDB ID
        request: Transition request with branch_id
        current_user: Authenticated user (must be admin)

    Returns:
        UserResponse: Updated user profile

    Raises:
        HTTPException: If transition fails
    """
    # TODO: Add admin role check
    # if "admin" not in current_user.roles:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Only admins can transition visitors to members"
    #     )

    try:
        user = await user_service.transition_to_member(user_id, request.branch_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserResponse(
            id=str(user.id),
            phone=user.phone,
            name=user.name,
            branch_id=str(user.branch_id) if user.branch_id else None,
            roles=user.roles,
            volunteer_roles=user.volunteer_roles,
            created_at=user.created_at,
            last_active=user.last_active,
            profile_image_url=user.profile_image_url
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to transition to member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to transition to member: {str(e)}"
        )


@router.post(
    "/register-existing-member",
    response_model=RegisterExistingMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register an existing church member",
    description="Admin endpoint to register existing church members who are not yet in the system."
)
async def register_existing_member(
    request: RegisterExistingMemberRequest,
    organization_id: str = Depends(require_organization_access),
    current_user: User = Depends(require_admin)
):
    """
    Register an existing church member directly.

    This endpoint allows admins to add existing church members who have not
    gone through the first-timer flow. Useful for bulk member registration
    or adding established members from other databases.

    Args:
        request: Member registration data
        organization_id: Organization ID from header
        current_user: Authenticated admin user

    Returns:
        RegisterExistingMemberResponse: Created member details

    Raises:
        HTTPException: If registration fails or phone already exists
    """
    logger.info(
        f"[register_existing_member] Admin {current_user.id} registering member: "
        f"{request.full_name}, phone: {request.phone}"
    )

    try:
        # Check if phone number already exists
        existing_user = await user_service.get_user_by_phone(request.phone)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A member with phone number {request.phone} already exists"
            )

        # Create the member directly as an active member
        member_data = {
            "phone": request.phone,
            "name": request.full_name,
            "full_name": request.full_name,
            "email": request.email,
            "branch_id": request.branch_id,
            "organization_id": organization_id,
            "gender": request.gender,
            "date_of_birth": request.date_of_birth,
            "address": request.address,
            "occupation": request.occupation,
            "marital_status": request.marital_status,
            "roles": request.roles if request.roles else ["member"],
            "volunteer_roles": request.volunteer_roles or [],
            "subgroup_memberships": [
                {
                    "group_id": group_id,
                    "subgroup_id": subgroup_id,
                    "joined_at": datetime.utcnow(),
                    "assigned_by_user_id": str(current_user.id),
                    "is_active": True
                }
                for subgroup_id in request.subgroup_ids
                for group_id in request.group_ids[:1]  # Each subgroup linked to first matching group
            ] if request.subgroup_ids else [],
            "member_status": "active_member",
            "current_spiritual_stage": "established_member",
            "first_visit_date": datetime.utcnow(),
            "visit_count": 1,
            "captured_by_user_id": str(current_user.id),
        }

        # Use user service to create the member
        user = await user_service.create_user_direct(member_data)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create member"
            )

        logger.info(
            f"[register_existing_member] Successfully registered member: "
            f"{user.id}, {request.full_name}"
        )

        return RegisterExistingMemberResponse(
            id=str(user.id),
            full_name=user.full_name or user.name,
            phone=user.phone,
            email=user.email,
            branch_id=str(user.branch_id) if user.branch_id else request.branch_id,
            member_status=user.member_status or "active_member",
            roles=user.roles,
            created_at=user.created_at,
            message=f"Successfully registered {request.full_name} as an active member"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[register_existing_member] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register member: {str(e)}"
        )
