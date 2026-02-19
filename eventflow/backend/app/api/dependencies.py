"""
API dependencies for authentication and authorization.
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from supabase import create_client, Client

from ..core.database import get_database
from ..core.config import settings
from ..services.auth_service_supabase import AuthService
from ..models.user import UserInDB, User


logger = logging.getLogger(__name__)
security = HTTPBearer()

# Initialize Supabase client
supabase: Client = create_client(settings.supabase_url, settings.supabase_anon_key)


async def get_current_user_phone(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> UserInDB:
    """
    Get current authenticated user from phone OTP JWT token.

    Args:
        credentials: HTTP bearer token
        db: Database instance

    Returns:
        Current user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    auth_service = AuthService(db)

    # Verify token
    payload = auth_service.verify_token(credentials.credentials)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await auth_service.get_current_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_supabase(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> UserInDB:
    """
    Get current authenticated user from Supabase JWT token.

    Args:
        credentials: HTTP bearer token
        db: Database instance

    Returns:
        Current user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Verify token with Supabase
    try:
        response = supabase.auth.get_user(token)
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired Supabase token",
            )

        supabase_user = response.user

        # Get or create user in MongoDB
        user_doc = await db.users.find_one({"supabase_user_id": supabase_user.id})

        if not user_doc:
            # Create new user from Supabase
            new_user = User(
                supabase_user_id=supabase_user.id,
                email=supabase_user.email,
                name=supabase_user.user_metadata.get("full_name") or supabase_user.email.split("@")[0],
                phone=supabase_user.phone or "",
                auth_method="email",
            )
            await db.users.insert_one(new_user.model_dump())
            user_doc = await db.users.find_one({"supabase_user_id": supabase_user.id})
            logger.info(f"Created new user from Supabase: {supabase_user.email}")

        # Convert to UserInDB model
        user_doc["_id"] = str(user_doc["_id"])
        user = UserInDB(**user_doc)

        logger.debug(f"Authenticated Supabase user: {user.email}")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Supabase authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase authentication failed",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> UserInDB:
    """
    Get current authenticated user (supports both phone OTP and Supabase auth).

    Tries Supabase auth first, falls back to phone OTP auth.

    Args:
        credentials: HTTP bearer token
        db: Database instance

    Returns:
        Current user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Try Supabase auth first
    try:
        response = supabase.auth.get_user(token)
        if response.user:
            # Token is a valid Supabase token
            return await get_current_user_supabase(credentials, db)
    except Exception:
        pass  # Not a Supabase token, try phone auth

    # Fall back to phone OTP auth
    return await get_current_user_phone(credentials, db)
