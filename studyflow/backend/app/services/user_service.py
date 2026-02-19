"""
User service for StudyFlow.

Handles user CRUD operations and business logic.
"""

from typing import Optional, List
from datetime import datetime
from bson import ObjectId

from app.models.user import User, UserCreate, UserUpdate, UserRole
from app.core.database import mongodb, COLLECTION_USERS


class UserService:
    """
    Service for managing user operations.

    Handles user creation, retrieval, updates, and role management.
    """

    @staticmethod
    async def create_user(user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user

        Raises:
            ValueError: If user with same supabase_id already exists
        """
        # Check if user already exists
        existing = await UserService.get_user_by_supabase_id(user_data.supabase_id)
        if existing:
            raise ValueError(f"User with supabase_id {user_data.supabase_id} already exists")

        # Create user document
        user = User(
            supabase_id=user_data.supabase_id,
            email=user_data.email,
            phone=user_data.phone,
            role=user_data.role,
            full_name=user_data.full_name,
            grade=user_data.grade,
            school_id=user_data.school_id,
            parent_id=user_data.parent_id,
            subjects=user_data.subjects,
            metadata=user_data.metadata,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Insert into database
        collection = mongodb.get_collection(COLLECTION_USERS)
        result = await collection.insert_one(user.dict(by_alias=True, exclude={"id"}))

        # Return user with ID
        user.id = str(result.inserted_id)
        return user

    @staticmethod
    async def get_user_by_id(
        user_id: str,
        organization_id: Optional[str] = None
    ) -> Optional[User]:
        """
        Get user by ID with optional organization filtering.

        Args:
            user_id: User ID
            organization_id: Organization ID for access control (optional)

        Returns:
            User if found and accessible, None otherwise
        """
        collection = mongodb.get_collection(COLLECTION_USERS)

        # Build query
        query = {"_id": ObjectId(user_id)}
        if organization_id:
            query["organization_id"] = organization_id

        user_doc = await collection.find_one(query)

        if user_doc:
            user_doc["id"] = str(user_doc["_id"])
            return User(**user_doc)
        return None

    @staticmethod
    async def get_user_by_supabase_id(supabase_id: str) -> Optional[User]:
        """
        Get user by Supabase ID.

        Args:
            supabase_id: Supabase auth user ID

        Returns:
            User if found, None otherwise
        """
        collection = mongodb.get_collection(COLLECTION_USERS)
        user_doc = await collection.find_one({"supabase_id": supabase_id})

        if user_doc:
            user_doc["id"] = str(user_doc["_id"])
            return User(**user_doc)
        return None

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User if found, None otherwise
        """
        collection = mongodb.get_collection(COLLECTION_USERS)
        user_doc = await collection.find_one({"email": email})

        if user_doc:
            user_doc["id"] = str(user_doc["_id"])
            return User(**user_doc)
        return None

    @staticmethod
    async def update_user(user_id: str, update_data: UserUpdate) -> Optional[User]:
        """
        Update user information.

        Args:
            user_id: User ID
            update_data: Fields to update

        Returns:
            Updated user if found, None otherwise
        """
        # Get only fields that were provided
        update_dict = update_data.dict(exclude_unset=True)
        if not update_dict:
            # No fields to update
            return await UserService.get_user_by_id(user_id)

        # Always update the updated_at timestamp
        update_dict["updated_at"] = datetime.utcnow()

        # Update in database
        collection = mongodb.get_collection(COLLECTION_USERS)
        result = await collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_dict}
        )

        if result.matched_count == 0:
            return None

        return await UserService.get_user_by_id(user_id)

    @staticmethod
    async def link_student_to_parent(student_id: str, parent_id: str) -> bool:
        """
        Link a student to a parent account.

        Args:
            student_id: Student user ID
            parent_id: Parent user ID

        Returns:
            True if successful, False otherwise
        """
        collection = mongodb.get_collection(COLLECTION_USERS)

        # Update student with parent_id
        student_result = await collection.update_one(
            {"_id": ObjectId(student_id), "role": UserRole.STUDENT.value},
            {"$set": {"parent_id": parent_id, "updated_at": datetime.utcnow()}}
        )

        # Add student to parent's student_ids list
        parent_result = await collection.update_one(
            {"_id": ObjectId(parent_id), "role": UserRole.PARENT.value},
            {
                "$addToSet": {"student_ids": student_id},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        return student_result.modified_count > 0 and parent_result.modified_count > 0

    @staticmethod
    async def get_parent_students(parent_id: str) -> List[User]:
        """
        Get all students linked to a parent.

        Args:
            parent_id: Parent user ID

        Returns:
            List of student users
        """
        # Get parent
        parent = await UserService.get_user_by_id(parent_id)
        if not parent or parent.role != UserRole.PARENT:
            return []

        # Get all students
        collection = mongodb.get_collection(COLLECTION_USERS)
        students = []

        for student_id in parent.student_ids:
            try:
                student_doc = await collection.find_one({"_id": ObjectId(student_id)})
                if student_doc:
                    student_doc["id"] = str(student_doc["_id"])
                    students.append(User(**student_doc))
            except Exception:
                # Skip invalid student IDs
                continue

        return students

    @staticmethod
    async def deactivate_user(user_id: str) -> bool:
        """
        Deactivate a user account.

        Args:
            user_id: User ID

        Returns:
            True if successful, False otherwise
        """
        collection = mongodb.get_collection(COLLECTION_USERS)
        result = await collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )

        return result.modified_count > 0

    @staticmethod
    async def activate_user(user_id: str) -> bool:
        """
        Activate a user account.

        Args:
            user_id: User ID

        Returns:
            True if successful, False otherwise
        """
        collection = mongodb.get_collection(COLLECTION_USERS)
        result = await collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": True, "updated_at": datetime.utcnow()}}
        )

        return result.modified_count > 0

    @staticmethod
    async def get_users_by_role(
        role: UserRole,
        organization_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[User]:
        """
        Get users by role with pagination and organization filtering.

        Args:
            role: User role to filter by
            organization_id: Filter by organization (optional)
            limit: Maximum number of users to return
            skip: Number of users to skip

        Returns:
            List of users
        """
        collection = mongodb.get_collection(COLLECTION_USERS)

        # Build query
        query = {"role": role.value}
        if organization_id:
            query["organization_id"] = organization_id

        cursor = collection.find(query).skip(skip).limit(limit)

        users = []
        async for user_doc in cursor:
            user_doc["id"] = str(user_doc["_id"])
            users.append(User(**user_doc))

        return users
