"""
FastAPI dependencies for authentication and authorization.

Integrates with shared authentication and organization system.

Author: AI Labs Africa
Date: 2025-11-10
"""

from fastapi import Depends, HTTPException, Header, Request
from typing import Optional
import os

import logging
from apps.shared.auth.supabase_auth import verify_supabase_token
from apps.shared.services.organization_service import get_organization_service
from apps.drive.backend.app.core.database import get_database
from apps.shared.services.drive_service import get_drive_service, DriveService

logger = logging.getLogger(__name__)

# Default organization for AI Labs Ltd.
DEFAULT_ORG_ID = os.getenv("DEFAULT_ORGANIZATION_ID", "ai_labs_ltd")
DEFAULT_ORG_NAME = "AI Labs Ltd."


async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID")
) -> dict:
    """
    Get current authenticated user from Supabase token.

    Uses shared Supabase auth integration and organization system.

    Args:
        authorization: Bearer token from Authorization header
        x_organization_id: Organization ID from X-Organization-ID header

    Returns:
        Dict with user information (user_id, email, organization_id, role)

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.replace("Bearer ", "")

    try:
        # Verify token using shared auth
        user_data = await verify_supabase_token(token)

        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user_id = user_data.get("id")
        email = user_data.get("email")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user data")

        # Determine organization ID
        # Priority: 1) Header, 2) User metadata, 3) Default (AI Labs Ltd.)
        organization_id = x_organization_id

        if not organization_id:
            # Check user metadata
            metadata = user_data.get("user_metadata", {})
            organization_id = metadata.get("organization_id")

        if not organization_id:
            # Use default organization for AI Labs Ltd.
            organization_id = DEFAULT_ORG_ID
            logger.info(f"Using default organization '{DEFAULT_ORG_NAME}' for user {email}")

        # Check if user is universal admin
        universal_admins = os.getenv("UNIVERSAL_ADMIN_EMAILS", "").split(",")
        is_universal_admin = email in universal_admins

        # Determine role
        if is_universal_admin:
            role = "universal_admin"
        else:
            # Check organization membership
            db = get_database()
            org_service = get_organization_service(db)

            has_access = await org_service.has_access_to_organization(
                organization_id, user_id, email
            )

            if not has_access and not is_universal_admin:
                # User doesn't belong to this organization
                # Auto-add to default organization if it's AI Labs Ltd.
                if organization_id == DEFAULT_ORG_ID:
                    logger.info(f"Auto-adding user {email} to default organization {DEFAULT_ORG_NAME}")
                    # User will be added automatically by organization service
                else:
                    raise HTTPException(
                        status_code=403,
                        detail=f"User does not have access to organization {organization_id}"
                    )

            # Get user's role in organization
            org_user = await org_service.get_organization_user(organization_id, user_id)
            role = org_user.role.value if org_user else "user"

        return {
            "user_id": user_id,
            "email": email,
            "organization_id": organization_id,
            "role": role,
            "is_universal_admin": is_universal_admin
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        raise HTTPException(status_code=401, detail="Failed to verify token")


async def get_drive_service_instance(
    current_user: dict = Depends(get_current_user)
) -> DriveService:
    """
    Get drive service instance for current user.

    Args:
        current_user: Current authenticated user

    Returns:
        DriveService instance
    """
    db = get_database()
    organization_id = current_user.get("organization_id")

    service = await get_drive_service(db, organization_id=organization_id)
    return service


async def require_organization_access(
    current_user: dict = Depends(get_current_user)
) -> str:
    """
    Require user to have access to an organization.

    Args:
        current_user: Current authenticated user

    Returns:
        Organization ID that user has access to

    Raises:
        HTTPException: If user doesn't have organization access
    """
    organization_id = current_user.get("organization_id")

    if not organization_id:
        raise HTTPException(
            status_code=403,
            detail="User must belong to an organization to access drive"
        )

    return organization_id
