"""
Organization Management Routes for StudyFlow.

Provides comprehensive organization management for multi-tenant platform:
- Organization CRUD operations
- Member management (add/remove users)
- Organization statistics and analytics
- Universal admin capabilities

Author: KasaAI
Updated: 2025-11-07
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from pydantic import BaseModel
import logging
import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../..")))

from apps.shared.models import Organization, OrganizationCreate, OrganizationUpdate, OrganizationUser
from apps.shared.services.organization_service import get_organization_service
from app.core.auth import get_current_user_with_org
from app.models.user import UserRole
from app.core.database import mongodb

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/organizations", tags=["Organizations"])


# ============================================================================
# Request/Response Models
# ============================================================================

class AddMemberRequest(BaseModel):
    """Request to add a member to an organization."""
    user_email: str
    role: str = "member"  # member, admin, owner


class OrganizationStats(BaseModel):
    """Organization statistics."""
    organization_id: str
    name: str
    total_users: int
    total_students: int
    total_teachers: int
    total_schools: int
    total_materials: int
    total_sessions: int
    active_sessions_today: int
    total_questions_asked: int
    created_at: str


@router.post("", response_model=Organization, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Create a new organization.

    Any authenticated user can create an organization and becomes its owner.

    Args:
        org_data: Organization creation data
        user_context: Current user context

    Returns:
        Created organization
    """
    try:
        org_service = get_organization_service()
        user_id = user_context["user_id"]
        user_email = user_context.get("email", "")

        organization = await org_service.create_organization(
            org_data, user_id, user_email
        )

        logger.info(
            f"Organization created: {organization.id} ({organization.name}) "
            f"by user {user_email}"
        )

        return organization

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating organization: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization"
        )


@router.get("", response_model=List[dict])
async def list_organizations(
    user_context: dict = Depends(get_current_user_with_org),
    include_all: bool = Query(False, description="Include all orgs (universal admin only)")
):
    """
    List organizations.

    Regular users see organizations they belong to.
    Universal admins can see all organizations with include_all=true.

    Args:
        user_context: Current user context
        include_all: If true, list all organizations (universal admin only)

    Returns:
        List of organizations with user's role
    """
    try:
        org_service = get_organization_service()
        user_id = user_context["user_id"]
        user_email = user_context.get("email", "")

        # Check if universal admin requesting all orgs
        if include_all:
            if not org_service.is_universal_admin(user_id, user_email):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only universal admins can list all organizations"
                )

            # Return all organizations for universal admin
            all_orgs = await org_service.list_all_organizations()
            return [{
                "organization": org.model_dump(),
                "role": "universal_admin",
                "joined_at": None
            } for org in all_orgs]

        # Return user's organizations
        user_orgs = await org_service.get_organizations_for_user(user_id)

        organizations = []
        for user_org in user_orgs:
            org = await org_service.get_organization(user_org.organization_id)
            if org:
                organizations.append({
                    "organization": org.model_dump(),
                    "role": user_org.role.value,
                    "joined_at": user_org.joined_at.isoformat() if user_org.joined_at else None,
                })

        return organizations

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing organizations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list organizations"
        )


@router.get("/{organization_id}", response_model=Organization)
async def get_organization(
    organization_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get organization details.

    User must be a member of the organization or a universal admin.

    Args:
        organization_id: Organization ID
        user_context: Current user context

    Returns:
        Organization details
    """
    try:
        org_service = get_organization_service()
        user_id = user_context["user_id"]
        user_email = user_context.get("email", "")

        # Check access
        has_access = await org_service.has_access_to_organization(
            organization_id, user_id, user_email
        )

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )

        org = await org_service.get_organization(organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        return org

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get organization"
        )


@router.put("/{organization_id}", response_model=Organization)
async def update_organization(
    organization_id: str,
    update_data: OrganizationUpdate,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Update organization details.

    Only organization owners/admins or universal admins can update.

    Args:
        organization_id: Organization ID
        update_data: Fields to update
        user_context: Current user context

    Returns:
        Updated organization
    """
    try:
        org_service = get_organization_service()
        user_id = user_context["user_id"]
        user_email = user_context.get("email", "")

        # Check if user has admin access to organization
        user_org = await org_service.get_user_organization(organization_id, user_id)
        is_universal_admin = org_service.is_universal_admin(user_id, user_email)

        if not user_org and not is_universal_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )

        if user_org and user_org.role.value not in ["owner", "admin"] and not is_universal_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organization owners/admins can update organization"
            )

        # Update organization
        updated_org = await org_service.update_organization(organization_id, update_data)

        if not updated_org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        logger.info(f"Organization updated: {organization_id} by {user_email}")

        return updated_org

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization"
        )


@router.get("/{organization_id}/stats", response_model=OrganizationStats)
async def get_organization_stats(
    organization_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get organization statistics and analytics.

    User must be a member or universal admin.

    Args:
        organization_id: Organization ID
        user_context: Current user context

    Returns:
        Organization statistics
    """
    try:
        org_service = get_organization_service()
        user_id = user_context["user_id"]
        user_email = user_context.get("email", "")

        # Check access
        has_access = await org_service.has_access_to_organization(
            organization_id, user_id, user_email
        )

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )

        # Get organization details
        org = await org_service.get_organization(organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        # Gather statistics from MongoDB
        db = mongodb.get_database()

        # Count users
        users_collection = db.get_collection("users")
        total_users = await users_collection.count_documents({"organization_id": organization_id})
        total_students = await users_collection.count_documents({
            "organization_id": organization_id,
            "role": UserRole.STUDENT.value
        })
        total_teachers = await users_collection.count_documents({
            "organization_id": organization_id,
            "role": UserRole.TEACHER.value
        })

        # Count schools
        schools_collection = db.get_collection("schools")
        total_schools = await schools_collection.count_documents({"organization_id": organization_id})

        # Count materials
        materials_collection = db.get_collection("materials")
        total_materials = await materials_collection.count_documents({"organization_id": organization_id})

        # Count sessions
        sessions_collection = db.get_collection("sessions")
        total_sessions = await sessions_collection.count_documents({"organization_id": organization_id})

        # Count today's active sessions
        from datetime import datetime, timedelta
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        active_sessions_today = await sessions_collection.count_documents({
            "organization_id": organization_id,
            "started_at": {"$gte": today_start}
        })

        # Count questions
        questions_collection = db.get_collection("questions")
        total_questions = await questions_collection.count_documents({"organization_id": organization_id})

        stats = OrganizationStats(
            organization_id=organization_id,
            name=org.name,
            total_users=total_users,
            total_students=total_students,
            total_teachers=total_teachers,
            total_schools=total_schools,
            total_materials=total_materials,
            total_sessions=total_sessions,
            active_sessions_today=active_sessions_today,
            total_questions_asked=total_questions,
            created_at=org.created_at.isoformat() if org.created_at else ""
        )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get organization statistics"
        )


@router.post("/{organization_id}/members", status_code=status.HTTP_201_CREATED)
async def add_organization_member(
    organization_id: str,
    member_request: AddMemberRequest,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Add a member to the organization.

    Only organization owners/admins or universal admins can add members.

    Args:
        organization_id: Organization ID
        member_request: Member details (email, role)
        user_context: Current user context

    Returns:
        Success message
    """
    try:
        org_service = get_organization_service()
        user_id = user_context["user_id"]
        user_email = user_context.get("email", "")

        # Check if user has admin access
        user_org = await org_service.get_user_organization(organization_id, user_id)
        is_universal_admin = org_service.is_universal_admin(user_id, user_email)

        if not user_org and not is_universal_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )

        if user_org and user_org.role.value not in ["owner", "admin"] and not is_universal_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organization owners/admins can add members"
            )

        # Add member to organization
        await org_service.add_user_to_organization(
            organization_id,
            member_request.user_email,
            member_request.role
        )

        logger.info(
            f"Member added: {member_request.user_email} to org {organization_id} "
            f"with role {member_request.role} by {user_email}"
        )

        return {
            "message": "Member added successfully",
            "organization_id": organization_id,
            "member_email": member_request.user_email,
            "role": member_request.role
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding member: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add member"
        )


@router.delete("/{organization_id}/members/{user_email}")
async def remove_organization_member(
    organization_id: str,
    user_email: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Remove a member from the organization.

    Only organization owners/admins or universal admins can remove members.
    Cannot remove the last owner.

    Args:
        organization_id: Organization ID
        user_email: Email of user to remove
        user_context: Current user context

    Returns:
        Success message
    """
    try:
        org_service = get_organization_service()
        user_id = user_context["user_id"]
        current_user_email = user_context.get("email", "")

        # Check if user has admin access
        user_org = await org_service.get_user_organization(organization_id, user_id)
        is_universal_admin = org_service.is_universal_admin(user_id, current_user_email)

        if not user_org and not is_universal_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )

        if user_org and user_org.role.value not in ["owner", "admin"] and not is_universal_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organization owners/admins can remove members"
            )

        # Remove member from organization
        await org_service.remove_user_from_organization(organization_id, user_email)

        logger.info(
            f"Member removed: {user_email} from org {organization_id} "
            f"by {current_user_email}"
        )

        return {
            "message": "Member removed successfully",
            "organization_id": organization_id,
            "member_email": user_email
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing member: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove member"
        )


@router.get("/{organization_id}/users", response_model=List[OrganizationUser])
async def list_organization_users(
    organization_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    List all users in the organization.

    User must be a member or universal admin.

    Args:
        organization_id: Organization ID
        user_context: Current user context

    Returns:
        List of OrganizationUser objects with full details (email, role, is_active, etc.)
    """
    try:
        org_service = get_organization_service()
        user_id = user_context["user_id"]
        user_email = user_context.get("email", "")

        # Check access
        has_access = await org_service.has_access_to_organization(
            organization_id, user_id, user_email
        )

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )

        # Get users - returns full OrganizationUser objects
        users = await org_service.get_users_in_organization(organization_id)
        return users

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )
