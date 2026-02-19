"""
Standardized Supabase Authentication for All KasaAI Apps

This module provides a centralized Supabase authentication implementation
that all KasaAI applications should use.

Supabase Instance: https://supabase.ailabsafrica.com (or configured URL)

Usage:
    from apps.shared.auth.supabase_auth import get_current_user, get_current_user_optional

    @router.get("/protected")
    async def protected_route(user: dict = Depends(get_current_user)):
        return {"user_id": user["id"], "email": user["email"]}
"""

import os
import logging
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status, Request
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Initialize Supabase client
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client instance.

    Returns:
        Client: Supabase client

    Raises:
        RuntimeError: If Supabase credentials not configured
    """
    global _supabase_client

    if _supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise RuntimeError(
                "Supabase credentials not configured. "
                "Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables."
            )

        _supabase_client = create_client(supabase_url, supabase_key)
        logger.info(f"Initialized Supabase client: {supabase_url}")

    return _supabase_client


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Get current authenticated user from Supabase JWT token.

    This is the standard authentication function that should be used
    across all KasaAI applications.

    Skips authentication for OPTIONS requests (CORS preflight).

    Args:
        request: FastAPI request object
        authorization: Authorization header with Bearer token

    Returns:
        dict: User information with keys:
            - id: User ID from Supabase
            - sub: User ID (alias for id)
            - email: User email
            - user_metadata: Additional user metadata
            - app_metadata: App-specific metadata

    Raises:
        HTTPException: If token is invalid or user not found

    Example:
        ```python
        from fastapi import Depends
        from apps.shared.auth.supabase_auth import get_current_user

        @router.get("/profile")
        async def get_profile(user: dict = Depends(get_current_user)):
            return {"user_id": user["id"], "email": user["email"]}
        ```
    """
    # Skip authentication for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return {
            "id": "preflight",
            "sub": "preflight",
            "user_id": "preflight",
            "email": "preflight@example.com",
            "user_metadata": {},
            "app_metadata": {},
        }
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split(maxsplit=1)
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme. Use 'Bearer <token>'",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token with Supabase
    try:
        supabase = get_supabase_client()
        response = supabase.auth.get_user(token)

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        supabase_user = response.user

        # Return standardized user dict
        user_dict = {
            "id": supabase_user.id,
            "sub": supabase_user.id,  # JWT standard claim
            "user_id": supabase_user.id,  # For compatibility
            "email": supabase_user.email or "",
            "phone": getattr(supabase_user, "phone", ""),
            "user_metadata": supabase_user.user_metadata or {},
            "app_metadata": supabase_user.app_metadata or {},
            "created_at": str(supabase_user.created_at) if supabase_user.created_at else None,
        }

        # Extract common fields from user_metadata
        metadata = supabase_user.user_metadata or {}
        user_dict["display_name"] = metadata.get("display_name") or metadata.get("full_name") or ""
        user_dict["avatar_url"] = metadata.get("avatar_url") or ""
        user_dict["first_name"] = metadata.get("first_name") or ""
        user_dict["last_name"] = metadata.get("last_name") or ""

        logger.debug(f"Authenticated user: {user_dict['email']} ({user_dict['id']})")
        return user_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed. Please check your credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    request: Request,
    authorization: Optional[str] = Header(None)
) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated, None otherwise.

    Useful for endpoints that work differently for authenticated vs anonymous users.

    Args:
        request: FastAPI request object
        authorization: Authorization header with Bearer token

    Returns:
        dict: User dict if authenticated, None otherwise

    Example:
        ```python
        from fastapi import Depends
        from apps.shared.auth.supabase_auth import get_current_user_optional

        @router.get("/content")
        async def get_content(user: Optional[dict] = Depends(get_current_user_optional)):
            if user:
                # Return personalized content
                return {"content": f"Hello {user['email']}"}
            else:
                # Return public content
                return {"content": "Hello guest"}
        ```
    """
    if not authorization:
        return None

    try:
        return await get_current_user(request, authorization)
    except HTTPException:
        return None


async def verify_supabase_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify Supabase JWT token and return user info.

    Low-level function for token verification without FastAPI dependencies.

    Args:
        token: JWT token string (without "Bearer " prefix)

    Returns:
        dict: User information if valid, None if invalid

    Example:
        ```python
        user = await verify_supabase_token(token)
        if user:
            print(f"Valid token for {user['email']}")
        else:
            print("Invalid token")
        ```
    """
    try:
        supabase = get_supabase_client()
        response = supabase.auth.get_user(token)

        if not response.user:
            return None

        supabase_user = response.user
        return {
            "id": supabase_user.id,
            "sub": supabase_user.id,
            "email": supabase_user.email or "",
            "user_metadata": supabase_user.user_metadata or {},
        }
    except Exception as e:
        logger.debug(f"Token verification failed: {e}")
        return None


# Export for backward compatibility
__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "get_supabase_client",
    "verify_supabase_token",
]
