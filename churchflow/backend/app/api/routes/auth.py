"""
Authentication API routes.

Endpoints for phone OTP authentication.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.schemas.auth import (
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse
)
from app.services.auth_service import auth_service
from app.api.dependencies import get_current_user_profile
from app.models.user import User

security = HTTPBearer()

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/send-otp",
    response_model=SendOTPResponse,
    status_code=status.HTTP_200_OK,
    summary="Send OTP to phone number",
    description="Send a one-time password (OTP) via SMS to the provided phone number for authentication."
)
async def send_otp(request: SendOTPRequest):
    """
    Send OTP to phone number.

    Args:
        request: SendOTPRequest containing phone number

    Returns:
        SendOTPResponse: Confirmation of OTP sent

    Raises:
        HTTPException: If OTP sending fails
    """
    try:
        result = await auth_service.send_otp(request.phone)
        return SendOTPResponse(**result)

    except Exception as e:
        logger.error(f"Error sending OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP: {str(e)}"
        )


@router.post(
    "/verify-otp",
    response_model=VerifyOTPResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify OTP and get access token",
    description="Verify the OTP code sent to the user's phone and receive a JWT access token."
)
async def verify_otp(request: VerifyOTPRequest):
    """
    Verify OTP and return access token.

    Args:
        request: VerifyOTPRequest containing phone and OTP token

    Returns:
        VerifyOTPResponse: User data and access token

    Raises:
        HTTPException: If OTP verification fails
    """
    try:
        result = await auth_service.verify_otp(request.phone, request.token)
        return VerifyOTPResponse(**result)

    except Exception as e:
        logger.error(f"Error verifying OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid OTP: {str(e)}"
        )


@router.post(
    "/exchange-token",
    response_model=VerifyOTPResponse,
    status_code=status.HTTP_200_OK,
    summary="Exchange Supabase token for backend JWT",
    description="Convert Supabase JWT token to ChurchFlow backend JWT for API access."
)
async def exchange_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Exchange Supabase JWT for backend JWT.

    This endpoint allows users who logged in with Supabase email/password
    to exchange their Supabase JWT token for a ChurchFlow backend JWT token.
    This is necessary because backend API endpoints validate signatures using
    the backend's SECRET_KEY, not Supabase's key.

    Args:
        credentials: HTTP Authorization credentials with Supabase JWT

    Returns:
        VerifyOTPResponse: Backend JWT token and user data

    Raises:
        HTTPException: If token exchange fails or Supabase token is invalid
    """
    try:
        supabase_token = credentials.credentials

        # Verify with Supabase
        from supabase import create_client
        from app.core.config import settings

        supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )

        # Get user from Supabase token
        user_response = supabase.auth.get_user(supabase_token)

        if not user_response or not user_response.user:
            raise Exception("Invalid Supabase token")

        user = user_response.user

        # Ensure user exists in users collection
        from app.services.user_service import user_service
        from app.core.database import get_database
        from datetime import datetime

        db = get_database()
        existing_user = await db.users.find_one({"supabase_id": user.id})

        if not existing_user:
            # Create user profile with default admin roles
            user_data = {
                "supabase_id": user.id,
                "email": user.email or None,
                "phone": user.phone or None,  # Use None instead of empty string
                "name": user.email.split('@')[0] if user.email else "User",
                "full_name": user.email.split('@')[0] if user.email else "User",
                "roles": ["admin", "coordinator"],  # Default roles for admin users
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_active": datetime.utcnow()
            }
            await db.users.insert_one(user_data)
            logger.info(f"Created user profile for {user.id} ({user.email})")

        # Generate backend JWT with backend's SECRET_KEY
        backend_token = auth_service._create_access_token(
            data={
                "sub": user.id,
                "email": user.email or None,
                "phone": user.phone or None
            }
        )

        logger.info(f"Token exchanged successfully for user {user.id}")

        return VerifyOTPResponse(
            success=True,
            user_id=user.id,
            phone=user.phone or "",
            access_token=backend_token,
            token_type="bearer"
        )

    except Exception as e:
        logger.error(f"Token exchange failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token exchange failed: {str(e)}"
        )


@router.get(
    "/me",
    summary="Get current user profile",
    description="Get the authenticated user's profile information including roles."
)
async def get_me(user: User = Depends(get_current_user_profile)):
    """
    Get current authenticated user's profile.

    Args:
        user: Current user from JWT token

    Returns:
        dict: User profile with id, name, phone, email, roles
    """
    return {
        "id": str(user.id),
        "name": user.name or user.full_name,
        "phone": user.phone,
        "email": user.email,
        "role": "admin" if "admin" in (user.roles or []) else "platform_admin" if "platform_admin" in (user.roles or []) else "member",
        "roles": user.roles or [],
        "branch_id": str(user.branch_id) if user.branch_id else None,
        "member_status": user.member_status
    }


@router.get(
    "/health",
    summary="Authentication service health check",
    description="Check if the authentication service is running properly."
)
async def auth_health():
    """
    Health check endpoint for auth service.

    Returns:
        dict: Health status
    """
    return {
        "service": "authentication",
        "status": "healthy",
        "provider": "supabase"
    }
