"""
API Key Authentication Middleware

Supports authentication via API keys in addition to JWT tokens.

Created: 2025-10-27
Sprint 5: Analytics & Ecosystem (Phase 8)
"""

from fastapi import Header, HTTPException, Depends
from typing import Optional
import logging

from ..services.api_key_service import get_api_key_service, APIKeyService

logger = logging.getLogger(__name__)


async def verify_api_key(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
) -> Optional[dict]:
    """
    Verify API key from either Authorization header or X-API-Key header.

    Supports two formats:
    1. Authorization: Bearer kas_...
    2. X-API-Key: kas_...

    Args:
        authorization: Authorization header (Bearer token or API key)
        x_api_key: X-API-Key header

    Returns:
        Optional[dict]: User info if API key is valid, None otherwise
    """
    api_key = None

    # Check X-API-Key header first
    if x_api_key and x_api_key.startswith("kas_"):
        api_key = x_api_key

    # Check Authorization header
    elif authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1].startswith("kas_"):
            api_key = parts[1]

    # If no API key found, return None (will fall back to JWT)
    if not api_key:
        return None

    # Verify API key
    try:
        service = await get_api_key_service()
        api_key_data = await service.verify_api_key(api_key)

        if not api_key_data:
            logger.warning(f"Invalid API key: {api_key[:15]}...")
            return None

        # Return user info in JWT-compatible format
        return {
            "id": api_key_data.user_id,
            "api_key_id": api_key_data.id,
            "api_key_name": api_key_data.name,
            "scopes": api_key_data.scopes,
            "rate_limit": api_key_data.rate_limit,
            "auth_method": "api_key"
        }

    except Exception as e:
        logger.error(f"Error verifying API key: {e}")
        return None


async def get_current_user_with_api_key(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
) -> dict:
    """
    Get current user from either JWT token or API key.

    This is a combined authentication method that tries:
    1. API key authentication
    2. Falls back to JWT token authentication

    Args:
        authorization: Authorization header
        x_api_key: X-API-Key header

    Returns:
        dict: User info

    Raises:
        HTTPException: If neither authentication method succeeds
    """
    # Try API key first
    user = await verify_api_key(authorization, x_api_key)

    if user:
        logger.debug(f"Authenticated via API key: {user['api_key_name']}")
        return user

    # Fall back to JWT (import here to avoid circular dependency)
    from ..auth import get_current_user_mongo

    try:
        # This will check JWT token
        jwt_user = await get_current_user_mongo(authorization=authorization)
        jwt_user["auth_method"] = "jwt"
        return jwt_user
    except HTTPException:
        # Neither API key nor JWT worked
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials. Provide either a valid JWT token or API key."
        )


def require_scope(required_scope: str):
    """
    Dependency to check if user has required scope.

    For API key authentication, checks the scopes list.
    For JWT authentication, allows all scopes (full access).

    Args:
        required_scope: Required scope (e.g., "tts:synthesize")

    Returns:
        Dependency function
    """
    async def check_scope(user: dict = Depends(get_current_user_with_api_key)):
        # JWT users have full access
        if user.get("auth_method") == "jwt":
            return user

        # API key users must have the required scope
        scopes = user.get("scopes", [])
        if required_scope not in scopes:
            raise HTTPException(
                status_code=403,
                detail=f"This API key does not have the required scope: {required_scope}"
            )

        return user

    return check_scope
