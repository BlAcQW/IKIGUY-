"""
Authentication service for African Language Community Platform.

Handles user authentication, registration, profile management, and Supabase integration.
"""

from supabase import create_client, Client
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import jwt
import logging

from models.user_models import User, UserCreate, UserUpdate, UserProfile, UserAuth, UserLevel
from database import get_database
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthService:
    """
    Authentication service handling user management and Supabase integration.

    Manages user registration, authentication, profile updates, and token handling.
    """

    def __init__(self):
        """Initialize Supabase client and database connection."""
        if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
            self.supabase: Client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
        else:
            logger.warning("Supabase credentials not configured")
            self.supabase = None

        self.db = None

    async def _get_db(self):
        """Get database connection lazily."""
        if self.db is None:
            self.db = get_database()
        return self.db

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user account.

        Args:
            user_data: User registration data

        Returns:
            User: Created user object

        Raises:
            Exception: If user creation fails
        """
        try:
            db = await self._get_db()

            # Create user in Supabase first
            supabase_result = None
            if self.supabase:
                try:
                    supabase_result = self.supabase.auth.sign_up({
                        "email": user_data.email,
                        "password": "temporary_password",  # Will be set via email link
                        "options": {
                            "data": {
                                "full_name": user_data.full_name,
                                "username": user_data.username
                            }
                        }
                    })
                except Exception as e:
                    logger.error(f"Supabase user creation failed: {str(e)}")

            # Create user document in MongoDB
            user_doc = {
                "supabase_id": supabase_result.user.id if supabase_result else str(ObjectId()),
                "email": user_data.email,
                "username": user_data.username,
                "full_name": user_data.full_name,
                "bio": user_data.bio,
                "location": user_data.location,
                "languages_spoken": user_data.languages_spoken,
                "language_expertise": user_data.language_expertise,
                "level": UserLevel.NEWCOMER,
                "total_points": 0,
                "level_points": 0,
                "achievements": [],
                "badges": [],
                "validator_qualifications": [],
                "verified_languages": [],
                "permissions": ["submit", "comment"],
                "can_validate": False,
                "can_moderate": False,
                "can_create_proposals": False,
                "contributions_count": 0,
                "validations_count": 0,
                "quality_rating": 0.0,
                "reputation_score": 0,
                "is_active": True,
                "is_verified": False,
                "email_verified": supabase_result.user.email_confirmed_at is not None if supabase_result else False,
                "phone_verified": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_activity": datetime.utcnow()
            }

            result = await db.users.insert_one(user_doc)
            user_doc["_id"] = result.inserted_id

            return User(**user_doc)

        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            raise

    async def authenticate_user(self, email: str, password: str) -> Optional[UserAuth]:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            UserAuth: Authentication result with user data and tokens
        """
        try:
            # Authenticate with Supabase
            if not self.supabase:
                raise Exception("Supabase not configured")

            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if not auth_response.user:
                return None

            # Get user from MongoDB
            user = await self.get_user_by_supabase_id(auth_response.user.id)
            if not user:
                # Create user if doesn't exist in MongoDB
                user_data = UserCreate(
                    email=email,
                    full_name=auth_response.user.user_metadata.get("full_name"),
                    username=auth_response.user.user_metadata.get("username")
                )
                user = await self.create_user(user_data)

            # Update last login
            await self._update_last_login(user.id)

            return UserAuth(
                user=user,
                access_token=auth_response.session.access_token,
                refresh_token=auth_response.session.refresh_token,
                expires_at=datetime.fromtimestamp(auth_response.session.expires_at)
            )

        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return None

    async def get_current_user(self, access_token: str) -> Optional[User]:
        """
        Get current user from JWT access token.

        Args:
            access_token: JWT access token

        Returns:
            User: Current user or None if invalid token
        """
        try:
            if not self.supabase:
                # Fallback: decode JWT manually
                payload = jwt.decode(
                    access_token,
                    settings.SECRET_KEY,
                    algorithms=["HS256"]
                )
                supabase_id = payload.get("sub")
            else:
                # Verify token with Supabase
                user_response = self.supabase.auth.get_user(access_token)
                if not user_response.user:
                    return None
                supabase_id = user_response.user.id

            # Get user from MongoDB
            user = await self.get_user_by_supabase_id(supabase_id)
            if user:
                await self._update_last_activity(user.id)

            return user

        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User email

        Returns:
            User: User object or None if not found
        """
        try:
            db = await self._get_db()
            user_doc = await db.users.find_one({"email": email})
            return User(**user_doc) if user_doc else None

        except Exception as e:
            logger.error(f"Failed to get user by email: {str(e)}")
            return None

    async def get_user_by_supabase_id(self, supabase_id: str) -> Optional[User]:
        """
        Get user by Supabase ID.

        Args:
            supabase_id: Supabase user ID

        Returns:
            User: User object or None if not found
        """
        try:
            db = await self._get_db()
            user_doc = await db.users.find_one({"supabase_id": supabase_id})
            return User(**user_doc) if user_doc else None

        except Exception as e:
            logger.error(f"Failed to get user by Supabase ID: {str(e)}")
            return None

    async def update_user_profile(self, user_id: ObjectId, updates: UserUpdate) -> User:
        """
        Update user profile information.

        Args:
            user_id: User ID to update
            updates: Profile updates

        Returns:
            User: Updated user object
        """
        try:
            db = await self._get_db()

            # Prepare update data
            update_data = {}
            for field, value in updates.dict(exclude_unset=True).items():
                if value is not None:
                    update_data[field] = value

            update_data["updated_at"] = datetime.utcnow()

            # Update in MongoDB
            await db.users.update_one(
                {"_id": user_id},
                {"$set": update_data}
            )

            # Return updated user
            user_doc = await db.users.find_one({"_id": user_id})
            return User(**user_doc)

        except Exception as e:
            logger.error(f"Profile update failed: {str(e)}")
            raise

    async def get_public_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get public profile of a user.

        Args:
            user_id: User ID

        Returns:
            UserProfile: Public profile data
        """
        try:
            db = await self._get_db()
            user_doc = await db.users.find_one({"_id": ObjectId(user_id)})

            if not user_doc:
                return None

            return UserProfile(
                id=str(user_doc["_id"]),
                username=user_doc.get("username"),
                full_name=user_doc.get("full_name"),
                avatar_url=user_doc.get("avatar_url"),
                bio=user_doc.get("bio"),
                location=user_doc.get("location"),
                level=user_doc["level"],
                total_points=user_doc["total_points"],
                achievements=user_doc["achievements"],
                badges=user_doc["badges"],
                verified_languages=user_doc["verified_languages"],
                contributions_count=user_doc["contributions_count"],
                validations_count=user_doc["validations_count"],
                quality_rating=user_doc["quality_rating"],
                reputation_score=user_doc["reputation_score"],
                member_since=user_doc["created_at"]
            )

        except Exception as e:
            logger.error(f"Failed to get public profile: {str(e)}")
            return None

    async def logout_user(self, user_id: ObjectId):
        """
        Logout user and invalidate session.

        Args:
            user_id: User ID to logout
        """
        try:
            # Update last activity
            await self._update_last_activity(user_id)

            # If using Supabase, could invalidate session there as well
            if self.supabase:
                self.supabase.auth.sign_out()

        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            raise

    async def refresh_token(self, refresh_token: str) -> Optional[UserAuth]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            UserAuth: New authentication data
        """
        try:
            if not self.supabase:
                raise Exception("Supabase not configured")

            # Refresh token with Supabase
            refresh_response = self.supabase.auth.refresh_session(refresh_token)

            if not refresh_response.user:
                return None

            # Get user from MongoDB
            user = await self.get_user_by_supabase_id(refresh_response.user.id)
            if not user:
                return None

            return UserAuth(
                user=user,
                access_token=refresh_response.session.access_token,
                refresh_token=refresh_response.session.refresh_token,
                expires_at=datetime.fromtimestamp(refresh_response.session.expires_at)
            )

        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return None

    async def delete_user_account(self, user_id: ObjectId):
        """
        Delete user account and all associated data.

        Args:
            user_id: User ID to delete
        """
        try:
            db = await self._get_db()

            # Get user first
            user = await db.users.find_one({"_id": user_id})
            if not user:
                return

            # Delete from Supabase (if configured)
            if self.supabase and user.get("supabase_id"):
                try:
                    # Note: Supabase admin API would be needed for user deletion
                    pass
                except Exception as e:
                    logger.warning(f"Failed to delete from Supabase: {str(e)}")

            # Delete user from MongoDB
            await db.users.delete_one({"_id": user_id})

            # TODO: Handle cascade deletion of user's contributions, validations, etc.

        except Exception as e:
            logger.error(f"Account deletion failed: {str(e)}")
            raise

    async def _update_last_login(self, user_id: ObjectId):
        """Update user's last login timestamp."""
        try:
            db = await self._get_db()
            await db.users.update_one(
                {"_id": user_id},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"Failed to update last login: {str(e)}")

    async def _update_last_activity(self, user_id: ObjectId):
        """Update user's last activity timestamp."""
        try:
            db = await self._get_db()
            await db.users.update_one(
                {"_id": user_id},
                {"$set": {"last_activity": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"Failed to update last activity: {str(e)}")