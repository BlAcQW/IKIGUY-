"""
Authentication utilities.

Handles Supabase authentication and user verification.
"""

import logging
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from typing import Optional, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()
supabase_client: Optional[Client] = None


async def initialize_auth():
    """
    Initialize authentication.

    Creates Supabase client for auth operations.
    """
    global supabase_client
    try:
        supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        logger.info("Supabase authentication initialized")
    except Exception as e:
        logger.error(f"Failed to initialize authentication: {str(e)}")
        raise


def get_supabase() -> Client:
    """
    Get Supabase client.

    Returns:
        Supabase client instance

    Raises:
        RuntimeError: If Supabase not initialized
    """
    if supabase_client is None:
        raise RuntimeError("Supabase client not initialized")
    return supabase_client


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get current authenticated user.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        User information dictionary

    Raises:
        HTTPException: If authentication fails
    """
    try:
        supabase = get_supabase()
        token = credentials.credentials

        # Verify JWT token with Supabase
        response = supabase.auth.get_user(token)

        if not response or not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        # Extract user data
        user_data = {
            "id": response.user.id,
            "sub": response.user.id,  # JWT standard claim
            "email": response.user.email,
            "role": response.user.user_metadata.get("role", "user")
        }

        # Add organization_id from user metadata if available
        if "organization_id" in response.user.user_metadata:
            user_data["organization_id"] = response.user.user_metadata["organization_id"]

        return user_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated, None otherwise.

    Args:
        credentials: Optional HTTP authorization credentials

    Returns:
        User information dictionary or None
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def get_organization_context(
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Get organization context from authenticated user.

    Args:
        request: FastAPI request object
        user: Current authenticated user

    Returns:
        Organization context dictionary with organization_id

    Notes:
        If user doesn't have an organization_id in metadata,
        uses their user ID as the organization_id (single-user org).

        Admin users can override organization by sending X-Organization-Id header.
    """
    # Get organization_id from user metadata, or use user ID as org ID
    organization_id = user.get("organization_id") or user.get("id") or user.get("sub")

    # Allow admin users to override organization via header
    if user.get("role") == "admin":
        override_org_id = request.headers.get("x-organization-id")
        if override_org_id:
            logger.info(f"Admin user {user.get('email')} switched to organization {override_org_id}")
            organization_id = override_org_id

    return {
        "organization_id": organization_id,
        "user_id": user.get("id") or user.get("sub")
    }


async def get_optional_organization_context(
    request: Request,
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
) -> Optional[Dict[str, str]]:
    """
    Get organization context from user if authenticated, None otherwise.

    Args:
        request: FastAPI request object
        user: Optional current authenticated user

    Returns:
        Organization context dictionary or None
    """
    if not user:
        return None

    # Get organization_id from user metadata, or use user ID as org ID
    organization_id = user.get("organization_id") or user.get("id") or user.get("sub")

    # Allow admin users to override organization via header
    if user.get("role") == "admin":
        override_org_id = request.headers.get("x-organization-id")
        if override_org_id:
            logger.info(f"Admin user {user.get('email')} switched to organization {override_org_id}")
            organization_id = override_org_id

    return {
        "organization_id": organization_id,
        "user_id": user.get("id") or user.get("sub")
    }
