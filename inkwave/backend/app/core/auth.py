"""
Authentication utilities.

Supabase JWT token validation and user authentication.
"""

import logging
from typing import Optional
from fastapi import Header, HTTPException, status
from supabase import create_client, Client

from app.core.config import settings
from app.models.user import User, UserInDB
from app.core.database import get_db

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        User model

    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token with Supabase
    try:
        logger.debug(f"Validating token: {token[:20]}...")
        response = supabase.auth.get_user(token)

        if not response.user:
            logger.warning("Token validation failed: No user in response")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        supabase_user = response.user
        logger.debug(f"Token validated successfully for user: {supabase_user.email}")

        # Get or create user in MongoDB
        db = get_db()
        user_doc = await db.users.find_one({"user_id": supabase_user.id})

        if not user_doc:
            # Create new user
            new_user = User(
                user_id=supabase_user.id,
                email=supabase_user.email,
                display_name=supabase_user.user_metadata.get("display_name"),
                avatar_url=supabase_user.user_metadata.get("avatar_url"),
            )
            # Use exclude_none=True to omit username field instead of including it as None
            # This allows sparse unique index to work correctly (missing field != null value)
            await db.users.insert_one(new_user.model_dump(exclude_none=True))
            user_doc = await db.users.find_one({"user_id": supabase_user.id})
            logger.info(f"Created new user: {supabase_user.email}")

        # Convert to User model
        user_doc["_id"] = str(user_doc["_id"])
        user = UserInDB(**user_doc)

        logger.debug(f"Authenticated user: {user.email}")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication failed for token {token[:20]}...: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )


async def get_current_admin_user(
    current_user: User = Header(None, alias="authorization")
) -> User:
    """
    Get current admin user.

    Requires admin role in user profile.

    Args:
        current_user: Current authenticated user

    Returns:
        Admin user model

    Raises:
        HTTPException: If user is not admin
    """
    # Get authenticated user
    user = await get_current_user(current_user)

    # Check if user is admin
    if not user.is_admin:
        logger.warning(f"Non-admin user attempted admin access: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return user


async def create_admin_user(user_id: str) -> bool:
    """
    Grant admin access to a user.

    Args:
        user_id: User ID to make admin

    Returns:
        True if successful
    """
    db = get_db()

    result = await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"is_admin": True}}
    )

    if result.modified_count > 0:
        logger.info(f"Granted admin access to user: {user_id}")
        return True

    return False


async def revoke_admin_user(user_id: str) -> bool:
    """
    Revoke admin access from a user.

    Args:
        user_id: User ID to revoke admin

    Returns:
        True if successful
    """
    db = get_db()

    result = await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"is_admin": False}}
    )

    if result.modified_count > 0:
        logger.info(f"Revoked admin access from user: {user_id}")
        return True

    return False


async def get_current_author_or_admin(
    authorization: Optional[str] = Header(None)
) -> User:
    """
    Get current user with author or admin privileges.

    Requires AUTHOR, ADMIN, or SUPERADMIN role to upload books.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        User with upload privileges

    Raises:
        HTTPException: If user doesn't have upload privileges
    """
    # Get authenticated user
    user = await get_current_user(authorization)

    # Check if user can upload books (AUTHOR, ADMIN, SUPERADMIN roles)
    if not user.can_upload_books:
        logger.warning(f"User without upload privileges attempted book upload: {user.email} (role: {user.role})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Author or admin access required to upload books. Please contact support for author access.",
        )

    return user


async def verify_token(token: str) -> dict:
    """
    Verify a JWT token and return user data.

    Used by WebSocket handlers that receive token as query parameter.

    Args:
        token: JWT token string

    Returns:
        Dictionary with user data (sub, email, role, etc.)

    Raises:
        Exception: If token is invalid or expired
    """
    try:
        logger.debug(f"Verifying token: {token[:20]}...")
        response = supabase.auth.get_user(token)

        if not response.user:
            raise Exception("Invalid or expired token")

        user = response.user
        logger.debug(f"Token verified for user: {user.email}")

        return {
            "sub": user.id,
            "email": user.email,
            "role": user.role if hasattr(user, 'role') else "authenticated",
            "user_metadata": user.user_metadata
        }

    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        raise
