"""
Authentication service for EventFlow using Supabase Auth.

Handles phone OTP authentication via Supabase and JWT token management.
"""

from typing import Optional, Dict
from supabase import create_client, Client
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import logging

from ..core.config import settings
from ..models.user import User, UserInDB

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service using Supabase OTP."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize auth service with MongoDB and Supabase."""
        self.db = db
        self.users_collection = db["users"]
        self._supabase: Optional[Client] = None

    @property
    def supabase(self) -> Client:
        """
        Get Supabase client, creating it if necessary.

        Returns:
            Client: Supabase client instance
        """
        if self._supabase is None:
            self._supabase = create_client(
                settings.supabase_url,
                settings.supabase_service_role_key
            )
        return self._supabase

    async def send_otp(self, phone: str) -> Dict[str, any]:
        """
        Send OTP code to phone number via Supabase Auth.

        Args:
            phone: Phone number in E.164 format (e.g., +233201234567)

        Returns:
            dict: Response with success status

        Raises:
            HTTPException: If OTP sending fails
        """
        try:
            logger.info(f"Sending OTP to {phone} via Supabase")

            response = self.supabase.auth.sign_in_with_otp({
                "phone": phone,
                "options": {
                    "should_create_user": True
                }
            })

            logger.info(f"OTP sent successfully to {phone}")

            return {
                "success": True,
                "message": "OTP sent successfully",
                "phone": phone
            }

        except Exception as e:
            logger.error(f"Failed to send OTP to {phone}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send OTP: {str(e)}"
            )

    async def verify_otp(self, phone: str, otp: str) -> UserInDB:
        """
        Verify OTP code via Supabase and return user.

        Args:
            phone: Phone number in E.164 format
            otp: OTP code received by user

        Returns:
            User object

        Raises:
            HTTPException: If OTP is invalid or expired
        """
        try:
            logger.info(f"Verifying OTP for {phone}")

            # Verify OTP with Supabase
            response = self.supabase.auth.verify_otp({
                "phone": phone,
                "token": otp,
                "type": "sms"
            })

            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired OTP code",
                )

            supabase_user = response.user
            logger.info(f"OTP verified successfully for {phone}")

            # Get or create user in MongoDB
            user = await self.get_or_create_user(phone, supabase_user.id)
            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to verify OTP for {phone}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP code",
            )

    async def get_or_create_user(self, phone: str, supabase_user_id: str) -> UserInDB:
        """
        Get existing user or create new user.

        Args:
            phone: Phone number
            supabase_user_id: Supabase user ID

        Returns:
            User object
        """
        # Check if user exists by phone
        user_doc = await self.users_collection.find_one({"phone": phone})

        if user_doc:
            # Update last_active and supabase_user_id
            await self.users_collection.update_one(
                {"_id": user_doc["_id"]},
                {
                    "$set": {
                        "last_active": datetime.utcnow(),
                        "supabase_user_id": supabase_user_id
                    }
                },
            )
            user_doc["_id"] = str(user_doc["_id"])
            return UserInDB(**user_doc)

        # Create new user
        new_user = User(
            phone=phone,
            name=f"User {phone[-4:]}",  # Default name
            pricing_tier="free",
            roles=["organizer"],
        )

        user_dict = new_user.model_dump()
        user_dict["supabase_user_id"] = supabase_user_id

        result = await self.users_collection.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)

        logger.info(f"Created new user: {phone}")
        return UserInDB(**user_dict)

    def create_access_token(self, user_id: str, phone: str) -> str:
        """
        Create JWT access token.

        Args:
            user_id: User ID
            phone: Phone number

        Returns:
            JWT token string
        """
        expires = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

        to_encode = {
            "sub": user_id,
            "phone": phone,
            "exp": expires,
        }

        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify JWT token.

        Args:
            token: JWT token string

        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            return payload
        except JWTError:
            return None

    async def get_current_user(self, user_id: str) -> Optional[UserInDB]:
        """
        Get current user by ID.

        Args:
            user_id: User ID

        Returns:
            User object or None
        """
        try:
            user_doc = await self.users_collection.find_one(
                {"_id": ObjectId(user_id)}
            )

            if user_doc:
                user_doc["_id"] = str(user_doc["_id"])
                return UserInDB(**user_doc)
            return None
        except Exception:
            return None
