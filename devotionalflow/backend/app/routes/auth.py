"""
Authentication API routes.
Handles user registration, login, logout, and token refresh.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional
from app.models.user import UserCreate, UserLogin, UserResponse, Token, UserUpdate
from app.services.auth_service import (
    create_user,
    authenticate_user,
    get_user_by_id,
    refresh_access_token,
    update_user,
)
from app.utils.auth import get_current_user
from app.models.user import TokenData
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    invite_token: Optional[str] = Query(
        None,
        description="Invitation token from admin invite (overrides role)"
    )
):
    """
    Register a new user account.

    **Request Body:**
    - email: User email address
    - password: User password (min 8 chars, must have uppercase, lowercase, digit)
    - name: User full name
    - role: "user" or "admin" (overridden by invite if token provided)

    **Query Parameters:**
    - invite_token: (optional) Invitation token from admin invite

    **Returns:**
    - access_token: JWT access token (expires in 1 hour)
    - refresh_token: JWT refresh token (expires in 30 days)
    - token_type: "bearer"
    - user: User profile data

    **Raises:**
    - 400: Email already registered, invalid invite, or email mismatch

    **Note:**
    If an invite_token is provided:
    - The email must match the invitation email
    - The role is set from the invitation (not the request)
    - The invitation is marked as accepted after signup
    """
    logger.info(f"Signup attempt for email: {user_data.email}")

    # If invite token provided, validate it
    invited_role = None
    if invite_token:
        from app.services.user_management_service import get_user_management_service

        user_mgmt_service = get_user_management_service()
        verification = await user_mgmt_service.verify_invite_token(invite_token)

        if not verification.valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verification.error or "Invalid invitation token"
            )

        # Ensure email matches invitation
        if verification.email and verification.email.lower() != user_data.email.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email must match the invitation. Expected: {verification.email}"
            )

        # Store the invited role to apply after user creation
        invited_role = verification.role
        logger.info(f"Valid invite token for {user_data.email}, role: {invited_role}")

    # Override role from invitation if provided
    if invited_role:
        user_data.role = invited_role

    user = await create_user(user_data)
    logger.info(f"User created successfully: {user.id}")

    # Mark invitation as accepted if token was used
    if invite_token:
        from app.services.user_management_service import get_user_management_service

        user_mgmt_service = get_user_management_service()
        await user_mgmt_service.mark_invite_accepted(invite_token, user.id)
        logger.info(f"Invitation marked as accepted for user: {user.id}")

    # Create tokens for new user
    from app.utils.auth import create_access_token, create_refresh_token
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user
    )


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """
    Authenticate user and return JWT tokens.

    **Request Body:**
    - email: User email address
    - password: User password

    **Returns:**
    - access_token: JWT access token (expires in 1 hour)
    - refresh_token: JWT refresh token (expires in 30 days)
    - token_type: "bearer"
    - user: User profile data

    **Raises:**
    - 401: Invalid credentials
    """
    logger.info(f"Login attempt for email: {login_data.email}")
    token = await authenticate_user(login_data)
    logger.info(f"Login successful for user: {token.user.id}")
    return token


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: TokenData = Depends(get_current_user)):
    """
    Get current authenticated user profile.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Returns:**
    - User profile data

    **Raises:**
    - 401: Invalid or expired token
    - 404: User not found
    """
    user = await get_user_by_id(current_user.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    update_data: UserUpdate,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Update current authenticated user profile.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Request Body:**
    - name: (optional) User full name
    - bio: (optional) User bio/description
    - avatar_url: (optional) Avatar image URL
    - ministry_name: (optional) Ministry name
    - ministry_website: (optional) Ministry website
    - reading_preferences: (optional) Reading preferences object

    **Returns:**
    - Updated user profile data

    **Raises:**
    - 401: Invalid or expired token
    - 404: User not found
    """
    logger.info(f"Updating profile for user: {current_user.user_id}")
    user = await update_user(current_user.user_id, update_data)
    logger.info(f"Profile updated successfully for user: {current_user.user_id}")
    return user


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.

    **Request Body:**
    - refresh_token: JWT refresh token

    **Returns:**
    - New access_token and refresh_token
    - Updated user profile

    **Raises:**
    - 401: Invalid or expired refresh token
    """
    logger.info("Token refresh attempt")
    token = await refresh_access_token(request.refresh_token)
    logger.info(f"Token refreshed for user: {token.user.id}")
    return token


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: TokenData = Depends(get_current_user)):
    """
    Logout current user.
    (In JWT-based auth, logout is handled client-side by deleting tokens.)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Returns:**
    - Success message

    **Note:**
    For JWT authentication, the client should delete the tokens.
    Server-side token blacklisting can be implemented if needed.
    """
    logger.info(f"Logout for user: {current_user.user_id}")
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
async def forgot_password(email_data: dict):
    """
    Send password reset email.

    **Request Body:**
    - email: User email address

    **Returns:**
    - Success message

    **Raises:**
    - 404: User not found
    - 500: Failed to send reset email
    """
    from app.services.auth_service import request_password_reset

    email = email_data.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )

    logger.info(f"Password reset requested for: {email}")

    try:
        result = await request_password_reset(email)
        return {"message": "Password reset email sent successfully", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request"
        )


@router.post("/change-password")
async def change_password(
    password_data: dict,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Change password for authenticated user.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Request Body:**
    - current_password: Current password for verification
    - new_password: New password (must meet security requirements)

    **Returns:**
    - Success message

    **Raises:**
    - 400: Current password incorrect or new password invalid
    - 401: Not authenticated
    """
    from app.services.auth_service import change_password as change_pwd

    current_password = password_data.get("current_password")
    new_password = password_data.get("new_password")

    if not current_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password and new password are required",
        )

    logger.info(f"Password change requested for user: {current_user.user_id}")

    try:
        result = await change_pwd(current_user.user_id, current_password, new_password)
        return {"message": "Password changed successfully", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password",
        )


@router.post("/reset-password")
async def reset_password(reset_data: dict):
    """
    Reset password with reset token.

    **Request Body:**
    - token: Password reset token from email
    - new_password: New password

    **Returns:**
    - Success message

    **Raises:**
    - 400: Invalid or expired token
    - 422: Password validation failed
    """
    from app.services.auth_service import reset_password as reset_pwd

    token = reset_data.get("token")
    new_password = reset_data.get("new_password")

    if not token or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token and new password are required"
        )

    logger.info("Password reset attempt with token")

    try:
        result = await reset_pwd(token, new_password)
        return {"message": "Password reset successfully", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )
