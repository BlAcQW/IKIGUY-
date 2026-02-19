"""
Authentication API Router.

Provides login, signup, and user management endpoints.
"""

import logging
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.core.database import get_database
from app.core.auth import (
    authenticate_user,
    create_user,
    create_access_token,
    get_current_user,
    get_user_by_email,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


# Request/Response Models
class LoginRequest(BaseModel):
    """Login request body."""
    email: EmailStr
    password: str


class SignUpRequest(BaseModel):
    """Sign up request body."""
    email: EmailStr
    password: str
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserResponse(BaseModel):
    """User response."""
    id: str
    email: str
    first_name: str
    last_name: str
    role: str


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Authenticate user and return access token.
    
    Args:
        request: Login credentials
        db: Database instance
        
    Returns:
        Access token and user info
    """
    user = await authenticate_user(db, request.email, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["_id"]), "email": user["email"]},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": str(user["_id"]),
            "email": user["email"],
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "role": user.get("role", "user"),
        }
    )


@router.post("/signup", response_model=TokenResponse)
async def signup(
    request: SignUpRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Register a new user and return access token.
    
    Args:
        request: Sign up details
        db: Database instance
        
    Returns:
        Access token and user info
    """
    # Check if user already exists
    existing = await get_user_by_email(db, request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    try:
        # Create new user
        user = await create_user(
            db,
            email=request.email,
            password=request.password,
            first_name=request.first_name or "",
            last_name=request.last_name or "",
            role="user"
        )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user["_id"]), "email": user["email"]},
            expires_delta=access_token_expires
        )
        
        logger.info(f"New user registered: {user['email']}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": str(user["_id"]),
                "email": user["email"],
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "role": user.get("role", "user"),
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current authenticated user info.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User info
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        first_name=current_user.get("first_name", ""),
        last_name=current_user.get("last_name", ""),
        role=current_user.get("role", "user")
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: dict = Depends(get_current_user)
):
    """
    Logout current user.
    
    Note: With JWT, logout is handled client-side by removing the token.
    This endpoint is provided for API completeness.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user['email']}")
    return MessageResponse(message="Successfully logged out")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Refresh access token.
    
    Args:
        current_user: Current authenticated user
        db: Database instance
        
    Returns:
        New access token
    """
    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user["id"], "email": current_user["email"]},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": current_user["id"],
            "email": current_user["email"],
            "first_name": current_user.get("first_name", ""),
            "last_name": current_user.get("last_name", ""),
            "role": current_user.get("role", "user"),
        }
    )
