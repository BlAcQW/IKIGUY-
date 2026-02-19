"""
Authentication Dependencies for Organization-Scoped Applications

Provides reusable FastAPI dependencies for authentication and authorization
that work with the organization system.

Usage:
    from fastapi import Depends, APIRouter
    from apps.shared.dependencies.auth import get_current_user, require_organization_access

    router = APIRouter()

    @router.get("/events")
    async def get_events(
        user: dict = Depends(get_current_user),
        org_id: str = Depends(require_organization_access)
    ):
        # User is authenticated and has access to org_id
        pass
"""

from fastapi import Depends, HTTPException, Request, status
from typing import Dict, Any, Optional
import logging

from ..middleware.organization_context import (
    get_organization_context,
    require_organization_context,
    validate_organization_access,
    require_organization_admin as check_organization_admin
)

# Import standardized Supabase auth
from ..auth.supabase_auth import (
    get_current_user as supabase_get_current_user,
    get_current_user_optional as supabase_get_current_user_optional,
)

logger = logging.getLogger(__name__)


# Use Supabase auth as the default implementation
get_current_user = supabase_get_current_user
get_current_user_optional = supabase_get_current_user_optional


async def require_organization_access(
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user),
    org_id: str = Depends(require_organization_context)
) -> str:
    """
    Require user to have access to the organization in context.

    Validates:
    1. User is authenticated
    2. Organization ID is provided in X-Organization-ID header
    3. User has access to the organization (is a member or universal admin)

    Args:
        request: FastAPI request object
        user: Current authenticated user (injected)
        org_id: Organization ID from header (injected)

    Returns:
        str: Organization ID (validated)

    Raises:
        HTTPException: If user doesn't have access (403)

    Usage:
        ```python
        @router.get("/events")
        async def get_events(
            org_id: str = Depends(require_organization_access),
            user: dict = Depends(get_current_user)
        ):
            # User is guaranteed to have access to org_id
            # Fetch events for this organization
            pass
        ```
    """
    # Validate organization access
    has_access = await validate_organization_access(request, user, org_id)

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: You don't have access to organization {org_id}"
        )

    return org_id


async def require_organization_admin_role(
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user),
    org_id: str = Depends(require_organization_access)
) -> str:
    """
    Require user to be an admin in the organization.

    Validates:
    1. User is authenticated
    2. User has access to organization
    3. User has admin role in organization

    Args:
        request: FastAPI request object
        user: Current authenticated user (injected)
        org_id: Organization ID (injected and validated)

    Returns:
        str: Organization ID

    Raises:
        HTTPException: If user is not an admin (403)

    Usage:
        ```python
        @router.delete("/events/{event_id}")
        async def delete_event(
            event_id: str,
            org_id: str = Depends(require_organization_admin_role)
        ):
            # Only organization admins can reach here
            # Delete event...
            pass
        ```
    """
    await check_organization_admin(request, user, org_id)
    return org_id


async def get_organization_context_optional(
    request: Request,
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
) -> Optional[str]:
    """
    Get organization context if provided and user has access.

    Does not require organization or authentication.
    Validates access if both org and user are present.

    Args:
        request: FastAPI request object
        user: Current user if authenticated (injected)

    Returns:
        Organization ID if provided and validated, None otherwise

    Usage:
        ```python
        @router.get("/items")
        async def get_items(
            org_id: Optional[str] = Depends(get_organization_context_optional)
        ):
            if org_id:
                # Return organization-specific items
                pass
            else:
                # Return global/public items
                pass
        ```
    """
    org_id = get_organization_context(request)

    if not org_id:
        return None

    if not user:
        # Org ID provided but user not authenticated
        return None

    # Validate access
    has_access = await validate_organization_access(request, user, org_id)
    if not has_access:
        return None

    return org_id


class OrganizationScoped:
    """
    Dependency class for organization-scoped operations.

    Provides a convenient way to get both user and validated org ID.

    Usage:
        ```python
        from fastapi import Depends

        @router.get("/events")
        async def get_events(
            scope: OrganizationScoped = Depends()
        ):
            # scope.org_id is validated
            # scope.user is authenticated
            # scope.is_admin indicates if user is admin
            pass
        ```
    """

    def __init__(
        self,
        request: Request,
        user: Dict[str, Any] = Depends(get_current_user),
        org_id: str = Depends(require_organization_access)
    ):
        self.request = request
        self.user = user
        self.org_id = org_id
        self._is_admin: Optional[bool] = None
        self._is_approver: Optional[bool] = None
        self._can_approve: Optional[bool] = None

    async def check_is_admin(self) -> bool:
        """
        Check if user is admin in the organization.

        Cached after first call.

        Returns:
            bool: True if user is admin
        """
        if self._is_admin is None:
            from ..services.organization_service import get_organization_service

            org_service = get_organization_service()
            user_id = self.user.get("id") or self.user.get("sub")
            user_email = self.user.get("email", "")

            # Universal admins are considered admins everywhere
            if org_service.is_universal_admin(user_id, user_email):
                self._is_admin = True
            else:
                self._is_admin = await org_service.is_admin(self.org_id, user_id)

        return self._is_admin

    async def require_admin(self):
        """
        Require user to be admin. Raises 403 if not.

        Raises:
            HTTPException: If user is not admin
        """
        is_admin = await self.check_is_admin()
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required for this operation"
            )

    async def check_is_approver(self) -> bool:
        """
        Check if user has approver role in the organization.

        Cached after first call.

        Returns:
            bool: True if user has approver role
        """
        if self._is_approver is None:
            from ..services.organization_service import get_organization_service
            from ..models.organization import OrganizationRole

            org_service = get_organization_service()
            user_id = self.user.get("id") or self.user.get("sub")

            self._is_approver = await org_service.has_role(
                self.org_id, user_id, OrganizationRole.APPROVER
            )

        return self._is_approver

    async def check_can_approve(self) -> bool:
        """
        Check if user can approve expenses (ADMIN, APPROVER, or UNIVERSAL_ADMIN).

        Cached after first call.

        Returns:
            bool: True if user can approve expenses
        """
        if self._can_approve is None:
            from ..services.organization_service import get_organization_service

            org_service = get_organization_service()
            user_id = self.user.get("id") or self.user.get("sub")
            user_email = self.user.get("email", "")

            # Check if universal admin
            if org_service.is_universal_admin(user_id, user_email):
                self._can_approve = True
            else:
                # Check if admin or approver
                is_admin = await self.check_is_admin()
                is_approver = await self.check_is_approver()
                self._can_approve = is_admin or is_approver

        return self._can_approve

    async def require_approver(self):
        """
        Require user to have approval permissions (ADMIN, APPROVER, or UNIVERSAL_ADMIN).
        Raises 403 if not.

        Raises:
            HTTPException: If user cannot approve
        """
        can_approve = await self.check_can_approve()
        if not can_approve:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Approver or Admin role required for this operation"
            )
