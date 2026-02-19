"""
Organization Context Middleware

Extracts organization context from request headers and validates user access.
Attaches organization information to the request state for use in route handlers.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class OrganizationContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and validate organization context from requests.

    Reads the X-Organization-ID header and validates that the authenticated user
    has access to the specified organization. Attaches organization info to request.state
    for use in route handlers.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request and attach organization context.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response from the next handler
        """
        # Get organization ID from header
        org_id = request.headers.get('X-Organization-ID')

        # Attach to request state (may be None)
        request.state.organization_id = org_id
        request.state.organization_validated = False

        # Skip validation for certain paths
        skip_paths = [
            '/auth/',
            '/health',
            '/docs',
            '/openapi.json',
            '/api/admin/check-access'  # Don't validate org for admin check
        ]

        should_skip = any(request.url.path.startswith(path) for path in skip_paths)

        if should_skip or not org_id:
            # No org context needed or not provided - proceed
            response = await call_next(request)
            return response

        # Validate organization access (done in route handlers via dependency injection)
        # We just attach the org_id here and let routes validate as needed
        logger.debug(f"Request to {request.url.path} with org_id: {org_id}")

        response = await call_next(request)
        return response


def get_organization_context(request: Request) -> Optional[str]:
    """
    Extract organization ID from request state.

    Args:
        request: FastAPI request object

    Returns:
        Organization ID if present, None otherwise

    Usage:
        ```python
        from fastapi import Depends

        @router.get("/items")
        async def get_items(org_id: str = Depends(get_organization_context)):
            # org_id contains the current organization ID
            pass
        ```
    """
    return getattr(request.state, 'organization_id', None)


def require_organization_context(request: Request) -> str:
    """
    Require organization context in request.
    Raises 400 if X-Organization-ID header is missing.

    Args:
        request: FastAPI request object

    Returns:
        Organization ID

    Raises:
        HTTPException: If organization context is not provided

    Usage:
        ```python
        from fastapi import Depends

        @router.get("/items")
        async def get_items(org_id: str = Depends(require_organization_context)):
            # org_id is guaranteed to exist
            pass
        ```
    """
    org_id = getattr(request.state, 'organization_id', None)

    if not org_id:
        raise HTTPException(
            status_code=400,
            detail="Organization context required. Please provide X-Organization-ID header."
        )

    return org_id


async def validate_organization_access(
    request: Request,
    user: dict,
    organization_id: str
) -> bool:
    """
    Validate that a user has access to a specific organization.

    Args:
        request: FastAPI request object
        user: Current authenticated user
        organization_id: Organization ID to check access for

    Returns:
        True if user has access, False otherwise

    Note:
        Universal admins have access to all organizations.
    """
    # Import here to avoid circular dependency
    from ..services.organization_service import organization_service

    # Check if user is universal admin
    user_id = user.get("id") or user.get("sub") or user.get("tenant_id")
    user_email = user.get("email", "")
    is_universal_admin = organization_service.is_universal_admin(user_id, user_email)

    if is_universal_admin:
        logger.debug(f"Universal admin {user_id} accessing organization {organization_id}")
        return True

    # Check if user is a member of the organization
    try:
        user_orgs = organization_service.get_organizations_for_user(user_id)
        org_ids = [org.organization_id for org in user_orgs]

        has_access = organization_id in org_ids

        if not has_access:
            logger.warning(
                f"User {user_id} attempted to access organization {organization_id} "
                f"without membership. User orgs: {org_ids}"
            )

        return has_access
    except Exception as e:
        logger.error(f"Error validating organization access: {e}")
        return False


def get_user_organization_filter(user: dict, provided_org_id: Optional[str] = None) -> dict:
    """
    Build MongoDB filter for organization-scoped queries.

    Args:
        user: Current authenticated user
        provided_org_id: Organization ID from request context (optional)

    Returns:
        MongoDB filter dict with organization constraints

    Usage:
        ```python
        org_filter = get_user_organization_filter(current_user, org_id)
        # org_filter might be: {"organization_id": "org-123"}

        # Use in query:
        query = {**org_filter, "status": "active"}
        results = await collection.find(query).to_list(length=100)
        ```
    """
    # Import here to avoid circular dependency
    from ..services.organization_service import organization_service

    user_id = user.get("id") or user.get("sub") or user.get("tenant_id")
    user_email = user.get("email", "")
    is_universal_admin = organization_service.is_universal_admin(user_id, user_email)

    # Universal admins can specify any org, or see all if not specified
    if is_universal_admin:
        if provided_org_id:
            return {"organization_id": provided_org_id}
        else:
            # No filter - universal admin sees all
            return {}

    # Regular users - constrain to their organizations
    try:
        user_orgs = organization_service.get_organizations_for_user(user_id)
        org_ids = [org.organization_id for org in user_orgs]

        if provided_org_id:
            # Validate user has access to requested org
            if provided_org_id not in org_ids:
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied: You don't have access to organization {provided_org_id}"
                )
            return {"organization_id": provided_org_id}
        else:
            # Return filter for all user's organizations
            if len(org_ids) == 1:
                return {"organization_id": org_ids[0]}
            elif len(org_ids) > 1:
                return {"organization_id": {"$in": org_ids}}
            else:
                # User has no organizations - return impossible filter
                return {"organization_id": None}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building organization filter: {e}")
        # Fallback to user_id filtering
        return {"user_id": user_id}
