"""
Authentication routes for African Language Community Platform.

Handles user registration, login, profile management, and Supabase integration.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from pydantic import BaseModel

from models.user_models import User, UserCreate, UserUpdate, UserProfile, UserAuth
from models.responses import DataResponse, BaseResponse
from services.mongodb_auth_service import MongoDBAuthService
from core.config import get_settings

router = APIRouter()
security = HTTPBearer()
settings = get_settings()
auth_service = MongoDBAuthService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: JWT token from Authorization header

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/register", response_model=DataResponse)
async def register_user(user_data: UserCreate):
    """
    Register a new user in the platform.

    Creates a new user account with basic profile information and
    initializes community participation settings.

    Args:
        user_data: User registration information

    Returns:
        DataResponse: Created user data with initial settings
    """
    try:
        # Check if user already exists
        existing_user = await auth_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )

        # Create new user
        new_user = await auth_service.create_user(user_data)

        return DataResponse(
            data=new_user,
            message="User registered successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


class LoginRequest(BaseModel):
    """Login request model."""
    email: str
    password: str

@router.post("/login", response_model=UserAuth)
async def login_user(login_data: LoginRequest):
    """
    Authenticate user and return access token.

    Args:
        login_data: Login credentials (email and password)

    Returns:
        UserAuth: User data with access token
    """
    try:
        auth_result = await auth_service.authenticate_user(
            login_data.email,
            login_data.password
        )
        if not auth_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        return auth_result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/profile", response_model=DataResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile information.

    Args:
        current_user: Authenticated user from token

    Returns:
        DataResponse: User profile data
    """
    return DataResponse(
        data=current_user,
        message="Profile retrieved successfully"
    )


@router.put("/profile", response_model=DataResponse)
async def update_user_profile(
    profile_updates: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update current user's profile information.

    Args:
        profile_updates: Profile fields to update
        current_user: Authenticated user from token

    Returns:
        DataResponse: Updated user profile
    """
    try:
        updated_user = await auth_service.update_user_profile(current_user.id, profile_updates)

        return DataResponse(
            data=updated_user,
            message="Profile updated successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}"
        )


@router.get("/profile/{user_id}", response_model=DataResponse)
async def get_public_profile(user_id: str):
    """
    Get public profile of any user.

    Args:
        user_id: ID of user to retrieve

    Returns:
        DataResponse: Public profile data
    """
    try:
        user_profile = await auth_service.get_public_profile(user_id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return DataResponse(
            data=user_profile,
            message="Public profile retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile: {str(e)}"
        )


@router.post("/logout", response_model=BaseResponse)
async def logout_user(current_user: User = Depends(get_current_user)):
    """
    Logout current user and invalidate tokens.

    Args:
        current_user: Authenticated user from token

    Returns:
        BaseResponse: Logout confirmation
    """
    try:
        await auth_service.logout_user(current_user.id)

        return BaseResponse(message="Logged out successfully")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.post("/refresh-token", response_model=UserAuth)
async def refresh_access_token(refresh_token: str):
    """
    Refresh access token using refresh token.

    Args:
        refresh_token: Valid refresh token

    Returns:
        UserAuth: New access token and user data
    """
    try:
        auth_result = await auth_service.refresh_token(refresh_token)
        if not auth_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        return auth_result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.delete("/account", response_model=BaseResponse)
async def delete_user_account(current_user: User = Depends(get_current_user)):
    """
    Delete current user's account and all associated data.

    Args:
        current_user: Authenticated user from token

    Returns:
        BaseResponse: Deletion confirmation
    """
    try:
        await auth_service.delete_user_account(current_user.id)

        return BaseResponse(message="Account deleted successfully")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account deletion failed: {str(e)}"
        )


@router.get("/statistics", response_model=DataResponse)
async def get_user_statistics(current_user: User = Depends(get_current_user)):
    """
    Get current user's contribution statistics.

    Args:
        current_user: Authenticated user from token

    Returns:
        DataResponse: User statistics including submissions, validations, points, etc.
    """
    try:
        stats = await auth_service.get_user_statistics(current_user.id)

        return DataResponse(
            data=stats,
            message="User statistics retrieved successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


@router.get("/activities", response_model=DataResponse)
async def get_user_activities(
    current_user: User = Depends(get_current_user),
    page: int = 1,
    limit: int = 20
):
    """
    Get current user's recent activity feed.

    Args:
        current_user: Authenticated user from token
        page: Page number
        limit: Items per page

    Returns:
        DataResponse: List of recent user activities
    """
    try:
        activities = await auth_service.get_user_activities(
            current_user.id,
            skip=(page - 1) * limit,
            limit=limit
        )

        return DataResponse(
            data=activities,
            message="User activities retrieved successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activities: {str(e)}"
        )


@router.put("/goals", response_model=DataResponse)
async def update_user_goals(
    goals: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Update current user's weekly goals.

    Args:
        goals: Weekly goals configuration
        current_user: Authenticated user from token

    Returns:
        DataResponse: Updated goals
    """
    try:
        updated_goals = await auth_service.update_user_goals(current_user.id, goals)

        return DataResponse(
            data=updated_goals,
            message="Weekly goals updated successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update goals: {str(e)}"
        )