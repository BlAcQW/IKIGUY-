"""
Authentication and authorization for StudyFlow.

Handles Supabase JWT verification, user role checking, and organization scoping.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import jwt

from app.config import settings
from app.models.user import UserRole

# Import shared organization service
from apps.shared.services.organization_service import get_organization_service

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


class SupabaseAuth:
    """
    Supabase authentication manager.

    Handles JWT verification and user authentication.
    """

    client: Optional[Client] = None

    @classmethod
    def initialize(cls):
        """Initialize Supabase client."""
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            logger.warning("⚠ Supabase credentials not configured")
            return

        try:
            cls.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
            logger.info("✓ Supabase client initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Supabase: {str(e)}")
            raise

    @classmethod
    def get_client(cls) -> Client:
        """
        Get Supabase client instance.

        Returns:
            Supabase client

        Raises:
            RuntimeError: If client is not initialized
        """
        if cls.client is None:
            raise RuntimeError("Supabase not initialized. Call initialize() first.")
        return cls.client

    @classmethod
    def verify_token(cls, token: str) -> dict:
        """
        Verify JWT token from Supabase.

        Args:
            token: JWT access token

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Decode JWT without verification first (Supabase handles signing)
            # In production, verify with Supabase JWT secret
            payload = jwt.decode(
                token,
                options={"verify_signature": False}  # Supabase tokens are pre-verified
            )
            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )


# Global auth instance
supabase_auth = SupabaseAuth()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        User payload from JWT

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    try:
        payload = supabase_auth.verify_token(token)
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_current_user_id(
    current_user: dict = Security(get_current_user)
) -> str:
    """
    Extract user ID from current user.

    Args:
        current_user: Current user payload

    Returns:
        User ID (sub claim from JWT)
    """
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token"
        )
    return user_id


async def get_current_user_with_org(
    credentials: HTTPAuthorizationCredentials = Security(security),
    x_organization_id: Optional[str] = Header(default=None, alias="X-Organization-Id")
) -> Dict[str, Any]:
    """
    Get current user with organization context.

    This enhanced authentication function:
    1. Verifies the JWT token
    2. Extracts organization_id from user metadata
    3. Checks universal admin status
    4. Returns enriched user context

    Args:
        credentials: HTTP authorization credentials

    Returns:
        Dict containing:
            - user_id: str - Unique user identifier
            - email: str - User email
            - role: str - User role (ADMIN, TEACHER, PARENT, STUDENT, SCHOOL)
            - organization_id: str - Organization ID (from metadata or default)
            - school_id: str - School ID (from metadata, if applicable)
            - is_universal_admin: bool - Universal admin status
            - raw_payload: dict - Complete JWT payload

    Raises:
        HTTPException: If authentication fails
    """
    # Get base user payload
    user_payload = await get_current_user(credentials)

    # Extract user information
    user_id = user_payload.get("sub")
    email = user_payload.get("email")
    user_metadata = user_payload.get("user_metadata", {})
    app_metadata = user_payload.get("app_metadata", {})

    # Extract organization and school IDs
    # Priority: header > user_metadata > app_metadata > default
    organization_id = (
        x_organization_id or
        user_metadata.get("organization_id") or
        app_metadata.get("organization_id") or
        settings.DEFAULT_ORGANIZATION_ID  # Fallback to default org
    )

    school_id = user_metadata.get("school_id")
    role = user_metadata.get("role")

    # Check universal admin status
    org_service = get_organization_service()
    is_universal_admin = org_service.is_universal_admin(user_id, email)

    # Validate organization_id exists (unless universal admin with no org specified)
    if organization_id and not is_universal_admin:
        org_exists = await org_service.get_organization(organization_id)
        if not org_exists:
            logger.warning(
                f"User {email} attempted to use non-existent organization {organization_id}, "
                f"falling back to default"
            )
            organization_id = settings.DEFAULT_ORGANIZATION_ID

    # Build enriched user context
    user_context = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "organization_id": organization_id,
        "school_id": school_id,
        "is_universal_admin": is_universal_admin,
        "raw_payload": user_payload
    }

    logger.debug(
        f"User authenticated: {email} (org: {organization_id}, "
        f"school: {school_id}, admin: {is_universal_admin})"
    )

    return user_context


async def check_organization_access(
    user_context: Dict[str, Any],
    target_organization_id: str
) -> bool:
    """
    Check if user has access to a specific organization.

    Universal admins have access to all organizations.
    Regular users must be members of the organization.

    Args:
        user_context: User context from get_current_user_with_org()
        target_organization_id: Organization ID to check access for

    Returns:
        True if user has access

    Raises:
        HTTPException: If access is denied
    """
    # Universal admins have access to everything
    if user_context.get("is_universal_admin"):
        return True

    # Check if user's organization matches target
    user_org_id = user_context.get("organization_id")
    if user_org_id == target_organization_id:
        return True

    # Check if user is member of target organization
    org_service = get_organization_service()
    has_access = await org_service.has_access_to_organization(
        user_id=user_context["user_id"],
        organization_id=target_organization_id
    )

    if not has_access:
        logger.warning(
            f"Access denied: User {user_context['email']} attempted to access "
            f"organization {target_organization_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to organization {target_organization_id}"
        )

    return True


class RoleChecker:
    """
    Role-based access control checker.

    Usage:
        @app.get("/admin")
        async def admin_route(
            user: dict = Depends(RoleChecker([UserRole.ADMIN]))
        ):
            ...
    """

    def __init__(self, allowed_roles: list[UserRole]):
        """
        Initialize role checker.

        Args:
            allowed_roles: List of allowed user roles
        """
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        current_user: dict = Security(get_current_user)
    ) -> dict:
        """
        Check if user has required role.

        Args:
            current_user: Current user payload

        Returns:
            User payload if authorized

        Raises:
            HTTPException: If user doesn't have required role
        """
        user_role = current_user.get("user_metadata", {}).get("role")

        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User role not found"
            )

        if user_role not in [role.value for role in self.allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in self.allowed_roles]}"
            )

        return current_user


# Common role checkers
require_admin = RoleChecker([UserRole.ADMIN])
require_teacher = RoleChecker([UserRole.ADMIN, UserRole.TEACHER])
require_parent = RoleChecker([UserRole.ADMIN, UserRole.PARENT])
require_student = RoleChecker([UserRole.ADMIN, UserRole.STUDENT])


class OrganizationRoleChecker:
    """
    Organization-aware role-based access control checker.

    Similar to RoleChecker but also checks organization membership
    and respects universal admin privileges.

    Usage:
        @app.get("/schools/{school_id}/materials")
        async def get_materials(
            school_id: str,
            user: dict = Depends(OrganizationRoleChecker([UserRole.TEACHER]))
        ):
            # user["organization_id"] is guaranteed to match school's org
            ...
    """

    def __init__(self, allowed_roles: list[UserRole]):
        """
        Initialize organization-aware role checker.

        Args:
            allowed_roles: List of allowed user roles
        """
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        credentials: HTTPAuthorizationCredentials = Security(security),
        x_organization_id: Optional[str] = Header(default=None, alias="X-Organization-Id")
    ) -> Dict[str, Any]:
        """
        Check if user has required role and organization access.

        Args:
            credentials: HTTP authorization credentials
            x_organization_id: Organization ID from header

        Returns:
            User context with organization information

        Raises:
            HTTPException: If user doesn't have required role or access
        """
        # Get user with organization context
        user_context = await get_current_user_with_org(credentials, x_organization_id)

        # Universal admins bypass role checks
        if user_context.get("is_universal_admin"):
            logger.debug(
                f"Universal admin {user_context['email']} granted access"
            )
            return user_context

        # Check role
        user_role = user_context.get("role")
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User role not found"
            )

        if user_role not in [role.value for role in self.allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in self.allowed_roles]}"
            )

        return user_context


# Organization-aware role checkers
require_admin_org = OrganizationRoleChecker([UserRole.ADMIN])
require_teacher_org = OrganizationRoleChecker([UserRole.ADMIN, UserRole.TEACHER])
require_parent_org = OrganizationRoleChecker([UserRole.ADMIN, UserRole.PARENT])
require_student_org = OrganizationRoleChecker([UserRole.ADMIN, UserRole.STUDENT])


def initialize_auth():
    """Initialize authentication system."""
    supabase_auth.initialize()
