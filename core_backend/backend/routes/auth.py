"""MongoDB-based authentication API routes."""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any

from ..models import (
    SignupRequest, SigninRequest, AuthResponse, RefreshTokenRequest,
    PasswordResetRequest, PasswordResetConfirmRequest
)
from ..services.auth_service import get_auth_service, AuthService


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/signup", response_model=AuthResponse)
async def signup(
    signup_data: SignupRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account.

    Creates a new user account, automatically creates an organization for the user,
    and returns authentication tokens.
    """
    try:
        response = await auth_service.signup(signup_data, request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@router.post("/signin", response_model=AuthResponse)
async def signin(
    signin_data: SigninRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Sign in with email and password.

    Authenticates user credentials and returns access tokens.
    """
    try:
        response = await auth_service.signin(signin_data, request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signin failed: {str(e)}")


@router.post("/signout")
async def signout(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Sign out and invalidate session.

    Invalidates all active sessions for the user.
    """
    try:
        authorization = request.headers.get("authorization", "")
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")

        token = authorization.replace("Bearer ", "")
        response = await auth_service.signout(token)
        return response
    except HTTPException:
        raise
    except Exception as e:
        # Return success even on error for security
        return {"success": True, "message": "Signed out successfully"}


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token.

    Generates new access and refresh tokens using a valid refresh token.
    """
    try:
        response = await auth_service.refresh_token(refresh_data.refresh_token)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")


@router.get("/me")
async def get_current_user(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get current user information.

    Returns the current user's profile data from the JWT token.
    """
    try:
        authorization = request.headers.get("authorization", "")
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")

        token = authorization.replace("Bearer ", "")
        user_data = await auth_service.get_current_user(token)
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")


@router.post("/password/reset")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Request password reset email.

    Initiates password reset process for the given email address.
    Note: This is a placeholder - actual email sending needs to be implemented.
    """
    try:
        # TODO: Implement password reset email sending
        # For now, just return success
        return {
            "success": True,
            "message": "Password reset instructions sent to your email"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")


@router.post("/password/confirm")
async def confirm_password_reset(
    confirm_data: PasswordResetConfirmRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Confirm password reset with token.

    Resets password using the reset token from email.
    Note: This is a placeholder - actual password reset logic needs to be implemented.
    """
    try:
        # TODO: Implement password reset confirmation
        # For now, just return success
        return {
            "success": True,
            "message": "Password reset successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset confirmation failed: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Authentication service health check.

    Returns the status of the authentication service.
    """
    return {
        "status": "healthy",
        "service": "mongodb_authentication",
        "features": [
            "email_password_auth",
            "jwt_tokens",
            "session_management",
            "organization_creation",
            "password_reset"
        ]
    }