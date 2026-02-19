"""
API dependencies for authentication and authorization.
"""

from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
import logging

from app.services.auth_service import auth_service
from app.services.user_service import user_service
from app.models.user import User
from app.utils.header_utils import decode_organization_id

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, str]:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization credentials

    Returns:
        dict: Token payload with user_id and phone

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        token = credentials.credentials
        payload = auth_service.decode_token(token)

        # Update last active timestamp
        await user_service.update_last_active(payload["sub"])

        return payload

    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_profile(
    current_user: Dict[str, str] = Depends(get_current_user)
) -> User:
    """
    Get current user's full profile from database.

    Args:
        current_user: Current user token payload

    Returns:
        User: User model with full profile data

    Raises:
        HTTPException: If user profile not found
    """
    logger.info(f"[get_current_user_profile] Loading profile for user_id: {current_user.get('sub')}")
    user = await user_service.get_user_by_id(current_user["sub"])

    if not user:
        logger.error(f"[get_current_user_profile] User profile not found for user_id: {current_user.get('sub')}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    logger.info(f"[get_current_user_profile] Loaded user: {user.id}, roles: {user.roles}")
    return user


def require_roles(*allowed_roles: str):
    """
    Dependency factory that checks if user has required roles.

    Creates a dependency that verifies the current user has at least one
    of the specified roles. Used for role-based access control on endpoints.

    Args:
        *allowed_roles: One or more role names (e.g., 'admin', 'coordinator')

    Returns:
        Dependency function that returns user profile if authorized

    Raises:
        HTTPException: 403 if user doesn't have required role

    Example:
        @router.post("/buses/routes")
        async def create_route(user: User = Depends(require_roles("admin", "coordinator"))):
            # Only admins and coordinators can access this
            pass
    """
    async def check_roles(user: User = Depends(get_current_user_profile)) -> User:
        """Check if user has one of the required roles."""
        if not user.roles:
            logger.warning(f"User {user.id} has no roles assigned")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: No roles assigned to user"
            )

        # Check if user has any of the allowed roles
        user_role_set = set(user.roles)
        allowed_role_set = set(allowed_roles)

        if not user_role_set.intersection(allowed_role_set):
            logger.warning(
                f"User {user.id} with roles {user.roles} attempted to access "
                f"endpoint requiring roles {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires one of these roles: {', '.join(allowed_roles)}"
            )

        return user

    return check_roles


async def require_organization_access(
    request: Request,
    user: Dict[str, str] = Depends(get_current_user),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID")
) -> str:
    """
    Require user to have access to the organization specified in X-Organization-ID header.

    ChurchFlow-specific version that uses ChurchFlow's auth system.
    Automatically decodes base64-encoded organization IDs from headers.

    Args:
        request: FastAPI request
        user: Current authenticated user
        x_organization_id: Organization ID from header (may be base64-encoded)

    Returns:
        str: Organization ID (validated and decoded)

    Raises:
        HTTPException: If organization ID not provided or user doesn't have access
    """
    # Decode organization ID (supports both encoded and plain values)
    organization_id = decode_organization_id(x_organization_id)

    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Organization-ID header is required"
        )

    # Import here to avoid circular dependency
    from apps.shared.services.organization_service import get_organization_service

    org_service = get_organization_service()
    user_id = user.get("sub") or user.get("id")
    user_email = user.get("email")

    # Check if universal admin
    if org_service.is_universal_admin(user_id, user_email):
        return organization_id

    # Check if user has access to this organization
    user_orgs = await org_service.get_organizations_for_user(user_id)
    org_ids = [org.organization_id for org in user_orgs]

    if organization_id not in org_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: You don't have access to organization {organization_id}"
        )

    return organization_id


async def get_optional_organization_id(
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID")
) -> str:
    """
    Get organization ID from header or default organization.

    For public endpoints that don't require authentication but need organization context.
    If no organization ID is provided in header, returns the default organization ID.
    Automatically decodes base64-encoded organization IDs from headers.

    Args:
        x_organization_id: Organization ID from header (optional, may be base64-encoded)

    Returns:
        str: Organization ID (from header or default, decoded)
    """
    # Decode organization ID if provided
    decoded_org_id = decode_organization_id(x_organization_id)

    if decoded_org_id:
        return decoded_org_id

    # Import here to avoid circular dependency
    from apps.shared.services.organization_service import get_organization_service
    from app.core.database import get_database

    org_service = get_organization_service()

    # Try to get default organization
    db = get_database()
    default_org = await db.organizations.find_one({"name": "ai-labs-ltd"})

    if default_org:
        return str(default_org["_id"])

    # If no default found, get first organization
    first_org = await db.organizations.find_one({})
    if first_org:
        return str(first_org["_id"])

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="No organizations found in system"
    )


async def require_admin(user: User = Depends(get_current_user_profile)) -> User:
    """
    Dependency that requires admin or universal_admin role.

    Convenience function for endpoints that require admin access only.
    Allows both organization admins and universal admins.

    Args:
        user: Current user profile

    Returns:
        User: User profile if admin or universal_admin

    Raises:
        HTTPException: 403 if user is not an admin

    Example:
        @router.delete("/buses/routes/{id}")
        async def delete_route(id: str, user: User = Depends(require_admin)):
            # Only admins can delete
            pass
    """
    allowed_roles = {"admin", "universal_admin"}
    user_roles = set(user.roles) if user.roles else set()

    if not user_roles.intersection(allowed_roles):
        logger.warning(f"Non-admin user {user.id} attempted admin-only action")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Admin or Universal Admin role required"
        )
    return user


async def require_coordinator_or_admin(user: User = Depends(get_current_user_profile)) -> User:
    """
    Dependency that requires coordinator or admin role.

    Allows both transport coordinators and admins to access the endpoint.
    This is the most common authorization level for bus management.

    Args:
        user: Current user profile

    Returns:
        User: User profile if coordinator or admin

    Raises:
        HTTPException: 403 if user is neither coordinator nor admin

    Example:
        @router.post("/buses/routes")
        async def create_route(user: User = Depends(require_coordinator_or_admin)):
            # Coordinators and admins can create routes
            pass
    """
    logger.info(f"[require_coordinator_or_admin] Checking user: {user.id}, roles: {user.roles}")
    allowed_roles = {"admin", "coordinator", "transport_coordinator"}
    user_roles = set(user.roles) if user.roles else set()

    if not user_roles.intersection(allowed_roles):
        logger.warning(
            f"User {user.id} with roles {user.roles} attempted coordinator/admin action - DENIED"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Coordinator or Admin role required"
        )
    logger.info(f"[require_coordinator_or_admin] User {user.id} authorized with roles {user.roles}")
    return user


# ============================================
# Hierarchical Permission Dependencies
# (Visitor Tracking & Discipleship System)
# ============================================

async def require_cell_leader_or_above(user: User = Depends(get_current_user_profile)) -> User:
    """
    Dependency that requires cell_leader, zone_leader, or admin role.

    Used for operations that require at least cell leader level access.
    Supports hierarchical permission structure where higher roles
    (zone_leader, admin) automatically have access.

    Args:
        user: Current user profile

    Returns:
        User: User profile if authorized

    Raises:
        HTTPException: 403 if user doesn't have sufficient permissions

    Example:
        @router.get("/members/list")
        async def list_members(user: User = Depends(require_cell_leader_or_above)):
            # Cell leaders, zone leaders, and admins can access
            pass
    """
    allowed_roles = {"cell_leader", "zone_leader", "admin"}
    user_roles = set(user.roles) if user.roles else set()

    if not user_roles.intersection(allowed_roles):
        logger.warning(
            f"User {user.id} with roles {user.roles} attempted cell-leader-or-above action - DENIED"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cell Leader or above required"
        )

    return user


async def require_zone_leader_or_above(user: User = Depends(get_current_user_profile)) -> User:
    """
    Dependency that requires zone_leader or admin role.

    Used for operations that require at least zone leader level access.

    Args:
        user: Current user profile

    Returns:
        User: User profile if authorized

    Raises:
        HTTPException: 403 if user doesn't have sufficient permissions

    Example:
        @router.post("/cell-groups")
        async def create_cell_group(user: User = Depends(require_zone_leader_or_above)):
            # Zone leaders and admins can create cell groups
            pass
    """
    allowed_roles = {"zone_leader", "admin"}
    user_roles = set(user.roles) if user.roles else set()

    if not user_roles.intersection(allowed_roles):
        logger.warning(
            f"User {user.id} with roles {user.roles} attempted zone-leader-or-above action - DENIED"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Zone Leader or Admin required"
        )

    return user


async def verify_member_access(
    target_user_id: str,
    current_user: User = Depends(get_current_user_profile)
) -> bool:
    """
    Verify that current user has permission to access target member.

    Implements hierarchical permission verification:
    - Admins: Can access all members
    - Zone leaders: Can access all members in their zone(s)
    - Cell leaders: Can access only members assigned to their cell group(s)
    - Department heads: Can access only volunteers in their department(s)

    Args:
        target_user_id: ID of member to access
        current_user: Current user making the request

    Returns:
        bool: True if access granted

    Raises:
        HTTPException: 403 if access denied

    Example:
        @router.get("/members/{user_id}/details")
        async def get_member_details(
            user_id: str,
            current_user: User = Depends(get_current_user_profile)
        ):
            # Verify access before returning details
            await verify_member_access(user_id, current_user)
            # ... return member details
    """
    from app.services.leadership_service import leadership_service

    # Check permission
    has_permission = await leadership_service.verify_leadership_permission(
        user_id=str(current_user.id),
        target_user_id=target_user_id,
        action="view"
    )

    if not has_permission:
        logger.warning(
            f"User {current_user.id} denied access to member {target_user_id} - "
            f"no hierarchical relationship"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't have permission to access this member"
        )

    return True
