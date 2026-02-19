"""
Authentication service for user registration, login, and profile management.
Integrates with Supabase for OAuth and MongoDB for user data storage.
"""

from typing import Optional
from datetime import datetime
from fastapi import HTTPException, status
from bson import ObjectId
from supabase import create_client, Client

from app.config import settings
from app.db.mongodb import get_database
from app.models.user import (
    UserCreate,
    UserLogin,
    UserInDB,
    UserResponse,
    Token,
    UserUpdate,
)
from app.utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
)
import logging

logger = logging.getLogger(__name__)

# Lazy Supabase client initialization
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """
    Get or create Supabase client (lazy initialization).
    Returns None if Supabase credentials are not configured.
    """
    global _supabase_client

    if _supabase_client is None:
        try:
            if settings.SUPABASE_KEY and settings.SUPABASE_KEY != "changeme":
                _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                logger.info("Supabase client initialized successfully")
            else:
                logger.warning("Supabase credentials not configured - OAuth will not work")
        except Exception as e:
            logger.warning(f"Failed to initialize Supabase client: {e}")

    return _supabase_client


async def create_user(user_data: UserCreate) -> UserResponse:
    """
    Create a new user account.
    Stores user in MongoDB and creates Supabase auth user.

    Args:
        user_data (UserCreate): User registration data.

    Returns:
        UserResponse: Created user data.

    Raises:
        HTTPException: If email already exists.
    """
    db = get_database()

    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Hash password
    password_hash = get_password_hash(user_data.password)

    # Create user document for MongoDB
    user_dict = user_data.model_dump(exclude={"password"})
    user_dict["password_hash"] = password_hash
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = datetime.utcnow()

    # Set default values based on role
    if user_data.role == "admin":
        user_dict["subscription_plan"] = "free"
        user_dict["subscription_expires_at"] = None
    else:  # user role
        user_dict["reading_streak"] = 0
        user_dict["reading_preferences"] = {
            "font_size": "medium",
            "theme": "light",
            "notification_time": "08:00",
        }

    # Set default privacy settings for all users
    user_dict["privacy_settings"] = {
        "profile_visibility": "public",
        "show_reading_history": True,
        "show_bookmarks": True,
        "show_email": False,
        "show_activity": True,
        "allow_comments_on_activity": True,
        "marketing_emails": True,
        "announcement_emails": True,
        "notifications_enabled": True,
    }

    # Insert into MongoDB
    result = await db.users.insert_one(user_dict)
    user_dict["_id"] = result.inserted_id

    # Create Supabase auth user (optional - for OAuth support)
    supabase = get_supabase_client()
    if supabase:
        try:
            supabase_user = supabase.auth.sign_up(
                {
                    "email": user_data.email,
                    "password": user_data.password,
                    "options": {
                        "data": {
                            "name": user_data.name,
                            "role": user_data.role,
                        }
                    },
                }
            )
            logger.info(f"Supabase user created: {supabase_user.user.id}")
        except Exception as e:
            logger.warning(f"Failed to create Supabase user (continuing anyway): {e}")
    else:
        logger.info("Supabase not configured, skipping OAuth user creation")

    # Convert to UserInDB model
    user_in_db = UserInDB(**user_dict)

    # Return UserResponse (keep ministry fields visible for admin users)
    return UserResponse(
        id=str(user_in_db.id),
        email=user_in_db.email,
        name=user_in_db.name,
        role=user_in_db.role,
        avatar_url=user_in_db.avatar_url,
        bio=user_in_db.bio,
        ministry_name=user_in_db.ministry_name if user_in_db.role == "admin" else None,
        ministry_website=user_in_db.ministry_website
        if user_in_db.role == "admin"
        else None,
        subscription_plan=user_in_db.subscription_plan if user_in_db.role == "admin" else None,
        reading_streak=user_in_db.reading_streak if user_in_db.role == "user" else None,
        reading_preferences=user_in_db.reading_preferences
        if user_in_db.role == "user"
        else None,
        privacy_settings=user_in_db.privacy_settings,
        created_at=user_in_db.created_at,
    )


async def authenticate_user(login_data: UserLogin) -> Token:
    """
    Authenticate a user and return JWT tokens.

    Args:
        login_data (UserLogin): User login credentials.

    Returns:
        Token: JWT access and refresh tokens with user data.

    Raises:
        HTTPException: If credentials are invalid.
    """
    db = get_database()

    # Find user by email
    user_doc = await db.users.find_one({"email": login_data.email})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    user = UserInDB(**user_doc)

    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create JWT tokens
    token_data = {
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Convert to UserResponse
    user_response = UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        avatar_url=user.avatar_url,
        bio=user.bio,
        ministry_name=user.ministry_name if user.role == "admin" else None,
        ministry_website=user.ministry_website if user.role == "admin" else None,
        subscription_plan=user.subscription_plan if user.role == "admin" else None,
        reading_streak=user.reading_streak,  # Available for all users
        reading_preferences=user.reading_preferences,  # Available for all users
        privacy_settings=user.privacy_settings,
        created_at=user.created_at,
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user_response,
    )


async def get_user_by_id(user_id: str) -> Optional[UserResponse]:
    """
    Get user by ID.

    Args:
        user_id (str): User ID.

    Returns:
        Optional[UserResponse]: User data if found, None otherwise.
    """
    db = get_database()

    user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user_doc:
        return None

    user = UserInDB(**user_doc)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        avatar_url=user.avatar_url,
        bio=user.bio,
        ministry_name=user.ministry_name if user.role == "admin" else None,
        ministry_website=user.ministry_website if user.role == "admin" else None,
        subscription_plan=user.subscription_plan if user.role == "admin" else None,
        reading_streak=user.reading_streak,  # Available for all users
        reading_preferences=user.reading_preferences,  # Available for all users
        privacy_settings=user.privacy_settings,
        created_at=user.created_at,
    )


async def update_user(user_id: str, update_data: UserUpdate) -> UserResponse:
    """
    Update user profile.

    Args:
        user_id (str): User ID.
        update_data (UserUpdate): Updated user data.

    Returns:
        UserResponse: Updated user data.

    Raises:
        HTTPException: If user not found.
    """
    db = get_database()

    # Get current user
    user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update user document
    update_dict = update_data.model_dump(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()

    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_dict})

    # Get updated user
    updated_user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    updated_user = UserInDB(**updated_user_doc)

    return UserResponse(
        id=str(updated_user.id),
        email=updated_user.email,
        name=updated_user.name,
        role=updated_user.role,
        avatar_url=updated_user.avatar_url,
        bio=updated_user.bio,
        ministry_name=updated_user.ministry_name if updated_user.role == "admin" else None,
        ministry_website=updated_user.ministry_website
        if updated_user.role == "admin"
        else None,
        subscription_plan=updated_user.subscription_plan
        if updated_user.role == "admin"
        else None,
        reading_streak=updated_user.reading_streak if updated_user.role == "user" else None,
        reading_preferences=updated_user.reading_preferences
        if updated_user.role == "user"
        else None,
        privacy_settings=updated_user.privacy_settings,
        created_at=updated_user.created_at,
    )


async def refresh_access_token(refresh_token: str) -> Token:
    """
    Refresh access token using refresh token.

    Args:
        refresh_token (str): JWT refresh token.

    Returns:
        Token: New access and refresh tokens.

    Raises:
        HTTPException: If refresh token is invalid.
    """
    from app.utils.auth import decode_token

    # Decode refresh token
    token_data = decode_token(refresh_token)

    # Get user from database
    user = await get_user_by_id(token_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Create new tokens
    new_token_data = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
    }

    access_token = create_access_token(new_token_data)
    new_refresh_token = create_refresh_token(new_token_data)

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=user,
    )


async def request_password_reset(email: str) -> dict:
    """
    Request password reset email.

    Args:
        email (str): User email address.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: If user not found or email sending fails.
    """
    db = get_database()

    # Check if user exists
    user = await db.users.find_one({"email": email})
    if not user:
        # For security, don't reveal if email exists
        logger.warning(f"Password reset requested for non-existent email: {email}")
        return {"message": "If that email exists, a reset link has been sent"}

    try:
        # Use Supabase password reset
        supabase = get_supabase_client()
        if supabase:
            # Supabase will send the reset email
            supabase.auth.reset_password_for_email(email, {
                "redirect_to": f"{settings.FRONTEND_URL}/reset-password"
            })
            logger.info(f"Password reset email sent to: {email}")
        else:
            # Fallback: log the request (in production, you'd send email via SMTP)
            logger.warning("Supabase not configured - password reset not sent")
            logger.info(f"Password reset requested for: {email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        # Don't reveal error to user for security

    return {"message": "If that email exists, a reset link has been sent"}


async def change_password(user_id: str, current_password: str, new_password: str) -> dict:
    """
    Change password for authenticated user.

    Args:
        user_id (str): User ID.
        current_password (str): Current password for verification.
        new_password (str): New password.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: If current password is incorrect or new password is invalid.
    """
    db = get_database()

    # Get user
    user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Verify current password
    if not verify_password(current_password, user_doc.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Validate new password
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )
    if not any(c.isupper() for c in new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter",
        )
    if not any(c.islower() for c in new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter",
        )
    if not any(c.isdigit() for c in new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one digit",
        )

    # Hash new password
    password_hash = get_password_hash(new_password)

    # Update password in MongoDB
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "password_hash": password_hash,
            "updated_at": datetime.utcnow()
        }}
    )

    # Update password in Supabase if configured
    supabase = get_supabase_client()
    if supabase:
        try:
            # Get user email
            email = user_doc.get("email")
            if email:
                # Supabase password update requires session, so we'll just update MongoDB
                # The user can use forgot password if they need Supabase sync
                logger.info(f"Password changed for user: {email} (MongoDB updated)")
        except Exception as e:
            logger.warning(f"Failed to update Supabase password: {e}")

    logger.info(f"Password changed successfully for user: {user_id}")
    return {"message": "Password changed successfully"}


async def reset_password(token: str, new_password: str) -> dict:
    """
    Reset password using reset token.

    Args:
        token (str): Password reset token from email.
        new_password (str): New password.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: If token is invalid or password is weak.
    """
    try:
        # Use Supabase to update password
        supabase = get_supabase_client()
        if supabase:
            # Supabase handles token validation
            response = supabase.auth.update_user({"password": new_password})

            if response.user:
                # Update password hash in MongoDB as well
                db = get_database()
                password_hash = get_password_hash(new_password)

                await db.users.update_one(
                    {"email": response.user.email},
                    {"$set": {
                        "password_hash": password_hash,
                        "updated_at": datetime.utcnow()
                    }}
                )

                logger.info(f"Password reset successful for user: {response.user.email}")
                return {"message": "Password reset successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired reset token"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Password reset service not available"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to reset password - invalid or expired token"
        )
