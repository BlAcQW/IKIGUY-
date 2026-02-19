"""
User service for managing user profiles and data.
"""

from typing import Optional, Dict
from bson import ObjectId
from datetime import datetime
import logging

from app.core.database import get_database
from app.models.user import User

logger = logging.getLogger(__name__)


class UserService:
    """Service for user profile operations."""

    async def get_user_by_phone(self, phone: str) -> Optional[User]:
        """
        Get user by phone number.

        Args:
            phone: User's phone number

        Returns:
            User object if found, None otherwise
        """
        db = get_database()
        user_doc = await db.users.find_one({"phone": phone})

        if user_doc:
            return User(**user_doc)
        return None

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID (Supabase ID or MongoDB ID).

        Args:
            user_id: User's Supabase ID (UUID) or MongoDB ID

        Returns:
            User object if found, None otherwise
        """
        db = get_database()

        # First try to lookup by supabase_id (for JWT token lookups)
        user_doc = await db.users.find_one({"supabase_id": user_id})

        # Fallback to MongoDB _id if supabase_id lookup fails
        if not user_doc and ObjectId.is_valid(user_id):
            user_doc = await db.users.find_one({"_id": ObjectId(user_id)})

        if user_doc:
            return User(**user_doc)
        return None

    async def create_user(self, phone: str, name: str, **kwargs) -> User:
        """
        Create new user.

        Args:
            phone: User's phone number
            name: User's full name
            **kwargs: Additional user fields

        Returns:
            Created User object

        Raises:
            Exception: If user creation fails
        """
        db = get_database()

        # Check if user already exists
        existing_user = await self.get_user_by_phone(phone)
        if existing_user:
            logger.info(f"User with phone {phone} already exists")
            return existing_user

        user_data = {
            "phone": phone,
            "name": name,
            "created_at": datetime.utcnow(),
            "last_active": datetime.utcnow(),
            **kwargs
        }

        try:
            result = await db.users.insert_one(user_data)
            user_data["_id"] = result.inserted_id

            logger.info(f"Created new user: {phone}")
            return User(**user_data)

        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise Exception(f"Failed to create user: {str(e)}")

    async def create_user_direct(self, member_data: Dict) -> User:
        """
        Create a user directly with full member data.

        Used by admins to register existing church members who haven't
        gone through the first-timer flow.

        Args:
            member_data: Complete member data dictionary including:
                - phone: Required phone number
                - name/full_name: Member's name
                - branch_id: Branch assignment
                - organization_id: Organization ID
                - member_status: Should be "active_member"
                - roles: List of roles
                - And other optional fields

        Returns:
            Created User object

        Raises:
            Exception: If user creation fails
        """
        db = get_database()

        # Ensure required timestamps
        now = datetime.utcnow()
        member_data["created_at"] = member_data.get("created_at", now)
        member_data["updated_at"] = now
        member_data["last_active"] = now

        # Convert branch_id and organization_id to ObjectId if strings
        if member_data.get("branch_id") and isinstance(member_data["branch_id"], str):
            if ObjectId.is_valid(member_data["branch_id"]):
                member_data["branch_id"] = ObjectId(member_data["branch_id"])

        if member_data.get("organization_id") and isinstance(member_data["organization_id"], str):
            if ObjectId.is_valid(member_data["organization_id"]):
                member_data["organization_id"] = ObjectId(member_data["organization_id"])

        # Remove None values
        member_data = {k: v for k, v in member_data.items() if v is not None}

        try:
            result = await db.users.insert_one(member_data)
            member_data["_id"] = result.inserted_id

            logger.info(
                f"Created new member directly: {member_data.get('phone')}, "
                f"name: {member_data.get('full_name', member_data.get('name'))}"
            )
            return User(**member_data)

        except Exception as e:
            logger.error(f"Failed to create member directly: {str(e)}")
            raise Exception(f"Failed to create member: {str(e)}")

    async def update_user(self, user_id: str, update_data: Dict) -> Optional[User]:
        """
        Update user profile.

        Args:
            user_id: User's MongoDB ID
            update_data: Dictionary of fields to update

        Returns:
            Updated User object if successful, None otherwise
        """
        db = get_database()

        if not ObjectId.is_valid(user_id):
            return None

        # Remove None values and add last_active timestamp
        update_data = {k: v for k, v in update_data.items() if v is not None}
        update_data["last_active"] = datetime.utcnow()

        try:
            result = await db.users.find_one_and_update(
                {"_id": ObjectId(user_id)},
                {"$set": update_data},
                return_document=True
            )

            if result:
                logger.info(f"Updated user: {user_id}")
                return User(**result)

            return None

        except Exception as e:
            logger.error(f"Failed to update user: {str(e)}")
            raise Exception(f"Failed to update user: {str(e)}")

    async def update_last_active(self, user_id: str) -> None:
        """
        Update user's last active timestamp.

        Args:
            user_id: User's MongoDB ID
        """
        db = get_database()

        if not ObjectId.is_valid(user_id):
            return

        try:
            await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"last_active": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"Failed to update last_active: {str(e)}")

    async def assign_department(self, user_id: str, department_name: str) -> Optional[User]:
        """
        Assign user to a department (change status from interested to assigned).

        Args:
            user_id: User's MongoDB ID
            department_name: Name of the department

        Returns:
            Updated User object if successful, None otherwise
        """
        db = get_database()

        if not ObjectId.is_valid(user_id):
            return None

        try:
            # Update the specific department's status to 'assigned' and set assigned_at
            result = await db.users.find_one_and_update(
                {
                    "_id": ObjectId(user_id),
                    "departments.name": department_name
                },
                {
                    "$set": {
                        "departments.$.status": "assigned",
                        "departments.$.assigned_at": datetime.utcnow(),
                        "last_active": datetime.utcnow()
                    }
                },
                return_document=True
            )

            if result:
                logger.info(f"Assigned user {user_id} to department {department_name}")
                return User(**result)

            return None

        except Exception as e:
            logger.error(f"Failed to assign department: {str(e)}")
            raise Exception(f"Failed to assign department: {str(e)}")

    async def transition_to_member(
        self,
        user_id: str,
        branch_id: str
    ) -> Optional[User]:
        """
        Transition a visitor to an active member.

        Args:
            user_id: User's MongoDB ID
            branch_id: Branch ID to assign member to

        Returns:
            Updated User object if successful, None otherwise
        """
        db = get_database()

        if not ObjectId.is_valid(user_id):
            return None

        if not ObjectId.is_valid(branch_id):
            raise ValueError("Invalid branch_id")

        try:
            # Update member status, assign branch, update spiritual stage
            update_data = {
                "member_status": "active_member",
                "branch_id": ObjectId(branch_id),
                "last_active": datetime.utcnow(),
                "transitioned_to_member_at": datetime.utcnow()
            }

            # Update spiritual stage if still a first/second timer
            user = await self.get_user_by_id(user_id)
            if user and user.current_spiritual_stage in ["first_timer", "second_timer"]:
                update_data["current_spiritual_stage"] = "new_convert"

            result = await db.users.find_one_and_update(
                {"_id": ObjectId(user_id)},
                {"$set": update_data},
                return_document=True
            )

            if result:
                logger.info(f"Transitioned user {user_id} to member at branch {branch_id}")
                return User(**result)

            return None

        except Exception as e:
            logger.error(f"Failed to transition to member: {str(e)}")
            raise Exception(f"Failed to transition to member: {str(e)}")

    async def search_users(self, query: str, limit: int = 20) -> list[User]:
        """
        Search users by name or phone.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching User objects
        """
        db = get_database()

        try:
            # Search by name or phone (case-insensitive)
            cursor = db.users.find({
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"full_name": {"$regex": query, "$options": "i"}},
                    {"phone": {"$regex": query}}
                ]
            }).limit(limit)

            users = []
            async for doc in cursor:
                users.append(User(**doc))

            return users

        except Exception as e:
            logger.error(f"Failed to search users: {str(e)}")
            return []


# Global user service instance
user_service = UserService()
