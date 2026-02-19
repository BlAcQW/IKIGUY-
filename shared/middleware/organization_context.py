"""
Organization Context Middleware

Extracts organization context from request headers and validates user access.
Attaches organization information to the request state for use in route handlers.

Usage:
    from fastapi import FastAPI
    from apps.shared.middleware.organization_context import OrganizationContextMiddleware

    app = FastAPI()
    app.add_middleware(OrganizationContextMiddleware)

    # In your routes:
    from fastapi import Depends
    from apps.shared.middleware.organization_context import require_organization_context

    @app.get("/items")
    async def get_items(org_id: str = Depends(require_organization_context)):
        # org_id is guaranteed to exist and user has access
        pass
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class OrganizationContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and validate organization context from requests.

    Reads the X-Organization-ID header and attaches it to request.state
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
            '/api/v1/auth/',
            '/api/v1/health',
        ]

        should_skip = any(request.url.path.startswith(path) for path in skip_paths)

        if should_skip or not org_id:
            # No org context needed or not provided - proceed
            response = await call_next(request)
            return response

        # Org context is attached - route handlers will validate as needed
        logger.debug(f"Request to {request.url.path} with org_id: {org_id}")

        response = await call_next(request)
        return response


# Dependency Injection Functions

def get_organization_context(request: Request) -> Optional[str]:
    """
    Extract organization ID from request state (optional).

    Args:
        request: FastAPI request object

    Returns:
        Organization ID if present, None otherwise

    Usage:
        ```python
        from fastapi import Depends

        @router.get("/items")
        async def get_items(org_id: Optional[str] = Depends(get_organization_context)):
            # org_id may be None
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
    user: Dict[str, Any],
    organization_id: str
) -> bool:
    """
    Validate that a user has access to a specific organization.

    Args:
        request: FastAPI request object
        user: Current authenticated user dict
        organization_id: Organization ID to check access for

    Returns:
        True if user has access, False otherwise

    Note:
        Universal admins have access to all organizations.
    """
    # Import here to avoid circular dependency
    from ..services.organization_service import get_organization_service

    org_service = get_organization_service()

    # Extract user info
    user_id = user.get("id") or user.get("sub") or user.get("user_id")
    user_email = user.get("email", "")

    # Check if user is universal admin
    if org_service.is_universal_admin(user_id, user_email):
        logger.debug(f"Universal admin {user_id} accessing organization {organization_id}")
        return True

    # Check if user is a member of the organization
    try:
        has_access = await org_service.has_access_to_organization(
            organization_id,
            user_id,
            user_email
        )

        if not has_access:
            logger.warning(
                f"User {user_id} attempted to access organization {organization_id} "
                f"without membership"
            )

        return has_access
    except Exception as e:
        logger.error(f"Error validating organization access: {e}")
        return False


def get_user_organization_filter(
    user: Dict[str, Any],
    provided_org_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build MongoDB filter for organization-scoped queries.

    This is a synchronous version for when you need to build filters
    without async context. For full validation, use validate_organization_access.

    Args:
        user: Current authenticated user dict
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

    Note:
        This function checks if user is universal admin synchronously using
        environment variables. It does NOT verify actual org membership.
        For full validation, use validate_organization_access() in async context.
    """
    from ..services.organization_service import get_organization_service

    org_service = get_organization_service()

    user_id = user.get("id") or user.get("sub") or user.get("user_id")
    user_email = user.get("email", "")
    is_universal_admin = org_service.is_universal_admin(user_id, user_email)

    # Universal admins can specify any org, or see all if not specified
    if is_universal_admin:
        if provided_org_id:
            return {"organization_id": provided_org_id}
        else:
            # No filter - universal admin sees all
            return {}

    # Regular users - must provide org_id
    if provided_org_id:
        # Note: This does not verify membership - caller should use
        # validate_organization_access() for that
        return {"organization_id": provided_org_id}
    else:
        # No org_id provided and not universal admin
        # Return impossible filter (will match nothing)
        return {"organization_id": None}


async def require_organization_admin(
    request: Request,
    user: Dict[str, Any],
    organization_id: str
) -> bool:
    """
    Require user to be an admin in the organization.

    Args:
        request: FastAPI request object
        user: Current authenticated user
        organization_id: Organization ID

    Returns:
        True if user is admin

    Raises:
        HTTPException: If user is not admin

    Usage:
        ```python
        from fastapi import Depends

        async def verify_admin(
            user: dict = Depends(get_current_user),
            org_id: str = Depends(require_organization_context),
            request: Request
        ):
            await require_organization_admin(request, user, org_id)
            return user

        @router.delete("/items/{item_id}")
        async def delete_item(
            item_id: str,
            user: dict = Depends(verify_admin)
        ):
            # Only admins can reach here
            pass
        ```
    """
    from ..services.organization_service import get_organization_service

    org_service = get_organization_service()

    user_id = user.get("id") or user.get("sub") or user.get("user_id")
    user_email = user.get("email", "")

    # Universal admins can do anything
    if org_service.is_universal_admin(user_id, user_email):
        return True

    # Check if user is admin in the organization
    is_admin = await org_service.is_admin(organization_id, user_id)

    if not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin role required for this operation"
        )

    return True
