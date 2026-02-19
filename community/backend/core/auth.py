"""
Authentication utilities for the African Language Community Platform.

Supports both real Supabase JWT validation and dev-token bypass for testing.
"""

from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import httpx
import logging
from core.config import get_settings

logger = logging.getLogger(__name__)

security = HTTPBearer()
settings = get_settings()


async def validate_supabase_token(token: str) -> Optional[dict]:
    """
    Validate a Supabase JWT token by calling the Supabase auth API.

    Args:
        token: JWT access token from Supabase

    Returns:
        User data dict if valid, None if invalid

    Raises:
        HTTPException: If token validation fails
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        logger.warning("Supabase not configured, skipping token validation")
        return None

    try:
        async with httpx.AsyncClient() as client:
            # Call Supabase to get user from token
            response = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": settings.SUPABASE_ANON_KEY,
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                user_data = response.json()
                return {
                    "id": user_data.get("id", ""),
                    "user_id": user_data.get("id", ""),
                    "email": user_data.get("email", ""),
                    "name": user_data.get("user_metadata", {}).get(
                        "name", user_data.get("email", "").split("@")[0]
                    ),
                    "role": user_data.get("role", "user"),
                    "app_metadata": user_data.get("app_metadata", {}),
                    "user_metadata": user_data.get("user_metadata", {}),
                }
            elif response.status_code == 401:
                logger.debug("Token validation failed: unauthorized")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                )
            else:
                logger.warning(
                    f"Unexpected response from Supabase: {response.status_code}"
                )
                return None

    except httpx.TimeoutException:
        logger.error("Timeout connecting to Supabase")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        )
    except httpx.RequestError as e:
        logger.error(f"Error connecting to Supabase: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Get current authenticated user from JWT token.

    Supports:
    - "dev-token" for development/testing (regular user)
    - "dev-moderator-token" for testing moderator features
    - "dev-admin-token" for testing admin features
    - Real Supabase JWT tokens for production

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        dict: User information including id, email, name, role

    Raises:
        HTTPException: If authentication fails
    """
    try:
        token = credentials.credentials

        # Dev token bypass for testing (regular user)
        if token == "dev-token":
            return {
                "id": "000000000000000000000001",
                "user_id": "000000000000000000000001",
                "email": "dev@example.com",
                "name": "Development User",
                "role": "user",
            }

        # Dev moderator token for testing moderator-only features
        if token == "dev-moderator-token":
            return {
                "id": "000000000000000000000002",
                "user_id": "000000000000000000000002",
                "email": "moderator@example.com",
                "name": "Development Moderator",
                "role": "moderator",
            }

        # Dev admin token for testing admin-only features
        if token == "dev-admin-token":
            return {
                "id": "000000000000000000000003",
                "user_id": "000000000000000000000003",
                "email": "admin@example.com",
                "name": "Development Admin",
                "role": "admin",
            }

        # Try to validate with Supabase
        user_data = await validate_supabase_token(token)
        if user_data:
            return user_data

        # If Supabase validation returns None (not configured), try JWT decode
        # This is a fallback for local development without Supabase
        try:
            # Decode without verification for development
            payload = jwt.decode(token, options={"verify_signature": False})
            return {
                "id": payload.get("sub", "unknown"),
                "user_id": payload.get("sub", "unknown"),
                "email": payload.get("email", ""),
                "name": payload.get("name", payload.get("email", "").split("@")[0]),
                "role": payload.get("role", "user"),
            }
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
            )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """
    Get current user if authenticated, otherwise return None.

    Args:
        credentials: Optional HTTP Bearer token credentials

    Returns:
        User dict if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
