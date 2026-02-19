"""
User Profile Service.

Handles user profile and preferences management.
"""

import os
import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from fastapi import UploadFile
from pathlib import Path

from app.models.user import (
    User,
    UserInDB,
    UserProfile,
    VoicePreferences,
    InteractionPreferences,
)

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing user profiles and preferences."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize UserService.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.users_collection = db["users"]

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """
        Get user by Supabase user ID.

        Args:
            user_id: Supabase user ID

        Returns:
            UserInDB: User document or None if not found
        """
        user_doc = await self.users_collection.find_one({"user_id": user_id})

        if not user_doc:
            return None

        # Convert ObjectId to string
        if "_id" in user_doc:
            user_doc["_id"] = str(user_doc["_id"])

        return UserInDB(**user_doc)

    async def create_user(
        self,
        user_id: str,
        email: str,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> UserInDB:
        """
        Create a new user profile.

        Args:
            user_id: Supabase user ID
            email: User email
            display_name: User display name
            avatar_url: User avatar URL

        Returns:
            UserInDB: Created user document
        """
        # Create user with default profile
        user = User(
            user_id=user_id,
            email=email,
            display_name=display_name,
            avatar_url=avatar_url,
            profile=UserProfile(),
            created_at=datetime.utcnow(),
            last_active=datetime.utcnow(),
        )

        # Insert into MongoDB
        user_dict = user.model_dump(exclude={"id"})
        result = await self.users_collection.insert_one(user_dict)

        # Fetch and return created user
        user_dict["_id"] = str(result.inserted_id)
        return UserInDB(**user_dict)

    async def get_or_create_user(
        self,
        user_id: str,
        email: str,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> UserInDB:
        """
        Get user by ID, create if doesn't exist.

        Args:
            user_id: Supabase user ID
            email: User email
            display_name: User display name
            avatar_url: User avatar URL

        Returns:
            UserInDB: User document
        """
        # Try to get existing user
        user = await self.get_user_by_id(user_id)

        if user:
            # Update last active timestamp
            await self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"last_active": datetime.utcnow()}},
            )
            return user

        # Create new user
        return await self.create_user(user_id, email, display_name, avatar_url)

    async def update_user_profile(
        self, user_id: str, profile_updates: Dict[str, Any]
    ) -> Optional[UserInDB]:
        """
        Update user profile.

        Args:
            user_id: Supabase user ID
            profile_updates: Dictionary of profile fields to update

        Returns:
            UserInDB: Updated user document or None if not found
        """
        # Prepare update document
        update_doc = {}

        # Handle top-level user fields
        if "display_name" in profile_updates:
            update_doc["display_name"] = profile_updates["display_name"]
        if "avatar_url" in profile_updates:
            update_doc["avatar_url"] = profile_updates["avatar_url"]
        if "first_name" in profile_updates:
            update_doc["first_name"] = profile_updates["first_name"]
        if "last_name" in profile_updates:
            update_doc["last_name"] = profile_updates["last_name"]
        if "phone_number" in profile_updates:
            update_doc["phone_number"] = profile_updates["phone_number"]
        if "date_of_birth" in profile_updates:
            # Parse date string to datetime if provided
            date_str = profile_updates["date_of_birth"]
            if date_str:
                try:
                    # datetime is already imported at module level
                    parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
                    update_doc["date_of_birth"] = parsed_date
                except ValueError:
                    logger.warning(f"Invalid date_of_birth format: {date_str}")
            else:
                update_doc["date_of_birth"] = None

        # Handle nested profile fields
        profile_fields = [
            "preferred_voice",
            "playback_speed",
            "reading_level",
        ]

        for field in profile_fields:
            if field in profile_updates:
                update_doc[f"profile.{field}"] = profile_updates[field]

        # Handle voice preferences
        if "voice_preferences" in profile_updates:
            voice_prefs = profile_updates["voice_preferences"]
            for key, value in voice_prefs.items():
                update_doc[f"profile.voice_preferences.{key}"] = value

        # Handle interaction preferences
        if "interaction_preferences" in profile_updates:
            interaction_prefs = profile_updates["interaction_preferences"]
            for key, value in interaction_prefs.items():
                update_doc[f"profile.interaction_preferences.{key}"] = value

        # Update last active
        update_doc["last_active"] = datetime.utcnow()

        # Perform update
        result = await self.users_collection.update_one(
            {"user_id": user_id}, {"$set": update_doc}
        )

        if result.matched_count == 0:
            return None

        # Fetch and return updated user
        return await self.get_user_by_id(user_id)

    async def update_voice_preferences(
        self, user_id: str, voice_preferences: Dict[str, Any]
    ) -> Optional[UserInDB]:
        """
        Update user voice preferences.

        Args:
            user_id: Supabase user ID
            voice_preferences: Voice preferences to update

        Returns:
            UserInDB: Updated user document or None if not found
        """
        return await self.update_user_profile(
            user_id, {"voice_preferences": voice_preferences}
        )

    async def update_interaction_preferences(
        self, user_id: str, interaction_preferences: Dict[str, Any]
    ) -> Optional[UserInDB]:
        """
        Update user interaction preferences.

        Args:
            user_id: Supabase user ID
            interaction_preferences: Interaction preferences to update

        Returns:
            UserInDB: Updated user document or None if not found
        """
        return await self.update_user_profile(
            user_id, {"interaction_preferences": interaction_preferences}
        )

    async def update_reading_level(
        self, user_id: str, reading_level: str
    ) -> Optional[UserInDB]:
        """
        Update user reading level.

        Args:
            user_id: Supabase user ID
            reading_level: Reading level (beginner, intermediate, advanced)

        Returns:
            UserInDB: Updated user document or None if not found
        """
        # Validate reading level
        valid_levels = ["beginner", "intermediate", "advanced"]
        if reading_level not in valid_levels:
            raise ValueError(
                f"Invalid reading level. Must be one of: {', '.join(valid_levels)}"
            )

        return await self.update_user_profile(
            user_id, {"reading_level": reading_level}
        )

    async def upload_avatar(
        self, user_id: str, file: UploadFile, base_url: str
    ) -> Optional[str]:
        """
        Upload user avatar image.

        Args:
            user_id: Supabase user ID
            file: Uploaded image file
            base_url: Base URL for constructing avatar URL

        Returns:
            str: Avatar URL or None if upload failed

        Raises:
            ValueError: If file type or size is invalid
        """
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
        if file.content_type not in allowed_types:
            raise ValueError(
                f"Invalid file type: {file.content_type}. Allowed types: {', '.join(allowed_types)}"
            )

        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        file_content = await file.read()
        if len(file_content) > max_size:
            raise ValueError(f"File size exceeds maximum limit of 5MB")

        # Reset file pointer after reading
        await file.seek(0)

        # Generate unique filename
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"{user_id}_{uuid.uuid4()}.{file_extension}"

        # Create avatars directory if it doesn't exist
        avatars_dir = Path("static/avatars")
        avatars_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = avatars_dir / unique_filename
        try:
            with open(file_path, "wb") as f:
                f.write(file_content)

            # Construct avatar URL
            avatar_url = f"{base_url}/static/avatars/{unique_filename}"

            # Update user profile
            await self.update_user_profile(user_id, {"avatar_url": avatar_url})

            logger.info(f"Avatar uploaded successfully for user {user_id}: {avatar_url}")
            return avatar_url

        except Exception as e:
            logger.error(f"Failed to upload avatar for user {user_id}: {e}")
            # Clean up file if it was created
            if file_path.exists():
                file_path.unlink()
            raise ValueError(f"Failed to upload avatar: {str(e)}")

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get user reading statistics.

        Args:
            user_id: Supabase user ID

        Returns:
            Dict containing user statistics:
            - books_started: Number of books started
            - questions_asked: Number of questions asked
            - listening_time_minutes: Total listening time in minutes
        """
        # Query reading sessions for books started
        books_started = await self.db.reading_sessions.count_documents(
            {"user_id": user_id}
        )

        # Query interactions for questions asked
        questions_asked = await self.db.interactions.count_documents(
            {"user_id": user_id, "interaction_type": "question"}
        )

        # Calculate listening time from wallet transactions (same as leaderboard)
        # This ensures consistency between profile stats and leaderboard
        # Aggregate total duration_minutes from wallet transactions
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Calculating listening time for user_id: {user_id}")
        
        # First, check if any transactions exist for this user
        sample_tx = await self.db.wallet_transactions.find_one({
            "user_id": user_id
        })
        
        if sample_tx:
            logger.info(f"Found sample transaction for user {user_id}: {sample_tx.get('_id')}")
        else:
            # Try alternative user_id formats
            alt_samples = await self.db.wallet_transactions.find({
                "$or": [
                    {"user_id": {"$regex": user_id, "$options": "i"}},
                    {"metadata.user_id": user_id}
                ]
            }).limit(1).to_list(length=1)
            if alt_samples:
                logger.warning(f"No transactions with exact user_id {user_id}, but found alternative format")
        
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "metadata.duration_minutes": {"$exists": True}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_minutes": {"$sum": "$metadata.duration_minutes"},
                    "count": {"$sum": 1}
                }
            },
        ]

        result = await self.db.wallet_transactions.aggregate(pipeline).to_list(length=1)
        
        logger.info(f"Aggregation result for user {user_id}: {result}")
        
        # Use float to match leaderboard calculation (handles decimal minutes)
        listening_time_minutes = float(result[0]["total_minutes"]) if result and result[0] and result[0].get("total_minutes") else 0.0
        tx_count = result[0].get("count", 0) if result and result[0] else 0
        
        logger.info(f"User {user_id}: {tx_count} transactions, {listening_time_minutes:.1f} total minutes")

        # Add uncommitted time from active sessions (time not yet recorded in transactions)
        # This ensures real-time stats updates while user is listening
        active_sessions = await self.db.reading_sessions.find({
            "user_id": user_id,
            "completed_at": None  # Only active sessions
        }).to_list(length=100)

        uncommitted_minutes = 0.0
        for session in active_sessions:
            # Handle None values explicitly (key may exist with None value)
            total_time = session.get("total_time_spent_minutes") or 0
            last_transaction_time = session.get("last_transaction_time") or 0
            # Time that hasn't been recorded in a transaction yet
            session_uncommitted = total_time - last_transaction_time
            if session_uncommitted > 0:
                uncommitted_minutes += session_uncommitted
                logger.info(f"Session {session.get('session_id')}: {session_uncommitted:.1f} uncommitted minutes")

        # Add uncommitted time to total
        total_listening_minutes = listening_time_minutes + uncommitted_minutes

        logger.info(f"User {user_id}: {listening_time_minutes:.1f} committed + {uncommitted_minutes:.1f} uncommitted = {total_listening_minutes:.1f} total minutes")

        # Convert to int for return value (minutes are whole numbers in UI)
        total_listening_minutes = int(total_listening_minutes)

        return {
            "books_started": books_started,
            "questions_asked": questions_asked,
            "listening_time_minutes": total_listening_minutes,
        }

    async def delete_user(self, user_id: str) -> bool:
        """
        Delete user profile.

        Args:
            user_id: Supabase user ID

        Returns:
            bool: True if deleted, False if not found
        """
        result = await self.users_collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0

    async def initialize_indexes(self):
        """
        Initialize database indexes for users collection.

        Creates:
        - Unique index on user_id
        - Index on email
        - Index on last_active
        """
        # Create indexes
        await self.users_collection.create_index("user_id", unique=True)
        await self.users_collection.create_index("email")
        await self.users_collection.create_index("last_active")
        print("✅ User service indexes initialized")
