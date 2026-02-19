"""
Authentication service for EventFlow.

Handles OTP generation, verification, and JWT token management.
"""

import random
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import jwt, JWTError
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ..core.config import settings
from ..models.user import User, UserInDB


# In-memory OTP store (use Redis in production)
otp_store: Dict[str, Dict[str, any]] = {}


class AuthService:
    """Authentication service."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize auth service."""
        self.db = db
        self.users_collection = db["users"]

    async def send_otp(self, phone: str) -> bool:
        """
        Generate and send OTP to phone number.

        Args:
            phone: Phone number to send OTP to

        Returns:
            True if OTP sent successfully
        """
        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # Store OTP with expiry (5 minutes)
        otp_store[phone] = {
            "code": otp,
            "expires_at": datetime.utcnow() + timedelta(minutes=5),
            "attempts": 0,
        }

        # TODO: Integrate with SMS service (Africa's Talking, Twilio, etc.)
        print(f"📱 OTP for {phone}: {otp}")  # Development only

        return True

    async def verify_otp(self, phone: str, otp: str) -> UserInDB:
        """
        Verify OTP and return user.

        Args:
            phone: Phone number
            otp: OTP code

        Returns:
            User object

        Raises:
            HTTPException: If OTP is invalid or expired
        """
        # Check if OTP exists
        if phone not in otp_store:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP not found. Please request a new one.",
            )

        stored_otp = otp_store[phone]

        # Check if OTP expired
        if datetime.utcnow() > stored_otp["expires_at"]:
            del otp_store[phone]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP expired. Please request a new one.",
            )

        # Check attempts
        if stored_otp["attempts"] >= 3:
            del otp_store[phone]
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please request a new OTP.",
            )

        # Verify OTP
        if stored_otp["code"] != otp:
            stored_otp["attempts"] += 1
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP code.",
            )

        # OTP valid - remove from store
        del otp_store[phone]

        # Get or create user
        user = await self.get_or_create_user(phone)
        return user

    async def get_or_create_user(self, phone: str) -> UserInDB:
        """
        Get existing user or create new user.

        Args:
            phone: Phone number

        Returns:
            User object
        """
        # Check if user exists
        user_doc = await self.users_collection.find_one({"phone": phone})

        if user_doc:
            # Update last_active
            await self.users_collection.update_one(
                {"_id": user_doc["_id"]},
                {"$set": {"last_active": datetime.utcnow()}},
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

        result = await self.users_collection.insert_one(new_user.model_dump())
        user_dict = new_user.model_dump()
        user_dict["_id"] = str(result.inserted_id)

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
