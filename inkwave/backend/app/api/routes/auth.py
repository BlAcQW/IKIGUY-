"""
Authentication Routes.

User signup and login endpoints.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from supabase import create_client

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# Initialize Supabase clients
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
supabase_admin = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


class SignupRequest(BaseModel):
    """Signup request model."""

    email: EmailStr
    password: str
    first_name: Optional[str] = None  # Optional first name
    last_name: Optional[str] = None  # Optional last name
    phone_number: Optional[str] = None  # Optional phone number
    date_of_birth: Optional[str] = None  # Optional date of birth (YYYY-MM-DD format)
    invitation_token: Optional[str] = None  # Token from book invitation link


class SignupResponse(BaseModel):
    """Signup response model."""

    success: bool
    message: str
    user: Dict[str, Any] | None = None
    session: Dict[str, Any] | None = None
    invitation_redeemed: bool = False
    library_book: Dict[str, Any] | None = None  # Book added from invitation


class LoginRequest(BaseModel):
    """Login request model."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response model."""

    success: bool
    message: str
    user: Dict[str, Any] | None = None
    session: Dict[str, Any] | None = None


@router.post("/signup", response_model=SignupResponse)
async def signup(request: SignupRequest) -> SignupResponse:
    """
    Sign up a new user.

    Creates user in Supabase and initializes profile in MongoDB.

    Args:
        request: Signup credentials

    Returns:
        SignupResponse with user and session data

    Raises:
        HTTPException: If signup fails
    """
    try:
        logger.info(f"Attempting signup for email: {request.email}")

        # Use admin client to create user without email confirmation
        # This bypasses the email confirmation requirement
        admin_response = supabase_admin.auth.admin.create_user({
            "email": request.email,
            "password": request.password,
            "email_confirm": True,  # Auto-confirm email
        })

        if not admin_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user. Email may already be in use.",
            )

        user_id = admin_response.user.id
        email = admin_response.user.email

        logger.info(f"Supabase user created with auto-confirmed email: {user_id}")

        # Now sign in the user to get a proper session
        signin_response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })

        session_data = None
        if signin_response.session:
            session_data = {
                "access_token": signin_response.session.access_token,
                "refresh_token": signin_response.session.refresh_token,
            }
            logger.info(f"User signed in successfully with session: {user_id}")
        else:
            logger.warning(f"User created but couldn't get session for {request.email}")

        # Create user profile in MongoDB
        db = get_db()

        # Check if user already exists in MongoDB
        existing_user = await db.users.find_one({"user_id": user_id})

        if not existing_user:
            # Parse date_of_birth if provided
            parsed_date_of_birth = None
            if request.date_of_birth:
                try:
                    from datetime import datetime
                    parsed_date_of_birth = datetime.strptime(request.date_of_birth, "%Y-%m-%d")
                except ValueError:
                    logger.warning(f"Invalid date_of_birth format: {request.date_of_birth}")

            # Generate display name from first/last name if provided, otherwise use email
            display_name = email.split("@")[0]
            if request.first_name and request.last_name:
                display_name = f"{request.first_name} {request.last_name}"
            elif request.first_name:
                display_name = request.first_name

            new_user = User(
                user_id=user_id,
                email=email,
                display_name=display_name,
                first_name=request.first_name,
                last_name=request.last_name,
                phone_number=request.phone_number,
                date_of_birth=parsed_date_of_birth,
            )
            # Use exclude_none=True to omit username field instead of including it as None
            # This allows sparse unique index to work correctly (missing field != null value)
            await db.users.insert_one(new_user.model_dump(exclude_none=True))
            logger.info(f"MongoDB user profile created: {email}")

            # Initialize wallet with free trial credits
            try:
                from app.services.wallet_service import get_wallet_service
                from decimal import Decimal
                from app.config.constants import FREE_TRIAL_CREDITS

                wallet_service = await get_wallet_service(db=db)

                if wallet_service and wallet_service.initialized:
                    # Create wallet for new user
                    # FREE_TRIAL_CREDITS is in cents (200 = $2), convert to Decimal dollars
                    welcome_bonus = Decimal(FREE_TRIAL_CREDITS) / Decimal("100")

                    wallet = await wallet_service.create_user_wallet(
                        user_id=user_id,
                        welcome_bonus=welcome_bonus
                    )

                    if wallet:
                        # Credit the welcome bonus
                        await wallet_service.shared_wallet.credit(
                            wallet_id=wallet.id,
                            amount=welcome_bonus,
                            description="Welcome bonus - Free trial credits",
                            metadata={"type": "signup_bonus", "user_id": user_id}
                        )
                        logger.info(f"Wallet created with ${welcome_bonus} (FREE_TRIAL_CREDITS={FREE_TRIAL_CREDITS}) for user: {email}")
                    else:
                        logger.warning(f"Failed to create wallet for {email}")
            except Exception as e:
                logger.warning(f"Failed to initialize wallet for {email}: {e}")
                # Don't fail signup if wallet creation fails

        # Handle invitation token if provided
        invitation_redeemed = False
        library_book = None

        if request.invitation_token:
            try:
                from app.services.book_invitation_service import book_invitation_service
                result = await book_invitation_service.redeem_invitation(
                    invitation_id=request.invitation_token,
                    user_id=user_id,
                    user_email=email
                )
                if result.get("success"):
                    invitation_redeemed = True
                    library_book = {
                        "book_id": result.get("book_id"),
                        "book_title": result.get("book_title"),
                        "book_cover_url": result.get("book_cover_url")
                    }
                    logger.info(f"Invitation redeemed for user {email}: book {result.get('book_id')}")
            except ValueError as e:
                # Log but don't fail signup if invitation redemption fails
                logger.warning(f"Invitation redemption failed for {email}: {e}")
            except Exception as e:
                logger.warning(f"Invitation redemption error for {email}: {e}")

        # Send Slack notification for new signup
        try:
            from app.services.slack_notification_service import slack_notification_service
            await slack_notification_service.notify_new_signup(
                email=email,
                user_id=user_id,
                invitation_redeemed=invitation_redeemed,
                book_title=library_book.get("book_title") if library_book else None
            )
        except Exception as e:
            # Don't fail signup if Slack notification fails
            logger.warning(f"Failed to send Slack notification: {e}")

        # Return user and session data
        message = "Account created successfully! Welcome to InkWave 🎉"
        if invitation_redeemed and library_book:
            message = f"Account created! '{library_book['book_title']}' has been added to your library 📚"

        return SignupResponse(
            success=True,
            message=message,
            user={
                "id": admin_response.user.id,
                "email": admin_response.user.email,
                "created_at": str(admin_response.user.created_at) if admin_response.user.created_at else None,
            },
            session=session_data,
            invitation_redeemed=invitation_redeemed,
            library_book=library_book,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}",
        )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """
    Log in an existing user.

    Args:
        request: Login credentials

    Returns:
        LoginResponse with user and session data

    Raises:
        HTTPException: If login fails
    """
    try:
        logger.info(f"Attempting login for email: {request.email}")

        # Sign in with Supabase
        response = supabase.auth.sign_in_with_password(
            {
                "email": request.email,
                "password": request.password,
            }
        )

        if response.user is None or response.session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        logger.info(f"User logged in: {response.user.email}")

        return LoginResponse(
            success=True,
            message="Logged in successfully",
            user={
                "id": response.user.id,
                "email": response.user.email,
            },
            session={
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
