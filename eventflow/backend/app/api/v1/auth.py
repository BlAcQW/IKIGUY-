"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from ...core.database import get_database
from ...schemas.auth import (
    OTPSendRequest, OTPVerifyRequest, AuthResponse, UserProfile,
    EmailLoginRequest, SupabaseAuthResponse
)
from ...services.auth_service_supabase import AuthService
from ...api.dependencies import supabase, get_current_user
from ...models.user import UserInDB


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/send-otp", status_code=status.HTTP_200_OK)
async def send_otp(
    request: OTPSendRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Send OTP to phone number.

    Args:
        request: OTP send request with phone number
        db: Database instance

    Returns:
        Success message
    """
    auth_service = AuthService(db)
    await auth_service.send_otp(request.phone)

    return {
        "message": "OTP sent successfully",
        "phone": request.phone,
    }


@router.post("/verify-otp", response_model=AuthResponse)
async def verify_otp(
    request: OTPVerifyRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Verify OTP and return access token.

    Args:
        request: OTP verification request
        db: Database instance

    Returns:
        Authentication response with token and user profile
    """
    auth_service = AuthService(db)

    # Verify OTP and get user
    user = await auth_service.verify_otp(request.phone, request.otp)

    # Create access token
    access_token = auth_service.create_access_token(user.id, user.phone)

    # Return response
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserProfile(
            id=user.id,
            phone=user.phone,
            name=user.name,
            email=user.email,
            organization=user.organization,
            pricing_tier=user.pricing_tier,
            wallet_id=user.wallet_id,
        ),
    )


@router.post("/login", response_model=SupabaseAuthResponse)
async def login_with_email(
    request: EmailLoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Login with email and password (Supabase auth).

    Args:
        request: Email login request
        db: Database instance

    Returns:
        Supabase authentication response with tokens and user profile
    """
    try:
        # Sign in with Supabase
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })

        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        supabase_user = response.user
        session = response.session

        # Get or create user in MongoDB
        user_doc = await db.users.find_one({"supabase_user_id": supabase_user.id})

        if not user_doc:
            # Create new user from Supabase
            from ...models.user import User
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

        logger.info(f"User logged in: {user.email}")

        # Return Supabase tokens
        return SupabaseAuthResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            token_type="bearer",
            user=UserProfile(
                id=user.id,
                phone=user.phone,
                name=user.name,
                email=user.email,
                organization=user.organization,
                pricing_tier=user.pricing_tier,
                wallet_id=user.wallet_id,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login failed"
        )


@router.get("/user", response_model=UserProfile)
async def get_user_profile(
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Get current user profile.

    Args:
        current_user: Current authenticated user

    Returns:
        User profile
    """
    return UserProfile(
        id=current_user.id,
        phone=current_user.phone,
        name=current_user.name,
        email=current_user.email,
        organization=current_user.organization,
        pricing_tier=current_user.pricing_tier,
        wallet_id=current_user.wallet_id,
    )
