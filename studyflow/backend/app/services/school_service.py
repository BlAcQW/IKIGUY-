"""
School service for StudyFlow.

Handles school management, statistics, and operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId

import sys
sys.path.insert(0, "/opt/kasaai/apps")

from app.core.database import mongodb
from app.models.school import (
    School,
    SchoolCreate,
    SchoolUpdate,
    SchoolStats,
    SubscriptionTier
)


class SchoolService:
    """Service for managing schools."""

    @staticmethod
    async def create_school(school_data: SchoolCreate) -> School:
        """
        Create a new school.

        Args:
            school_data: School creation data

        Returns:
            Created school
        """
        collection = mongodb.get_collection("schools")

        # Check if school with same name exists
        existing = await collection.find_one({"name": school_data.name})
        if existing:
            raise ValueError(f"School with name '{school_data.name}' already exists")

        # Create school document
        school_dict = school_data.dict()
        school_dict["created_at"] = datetime.utcnow()
        school_dict["updated_at"] = datetime.utcnow()
        school_dict["is_active"] = True

        result = await collection.insert_one(school_dict)

        # Retrieve and return created school
        created_school = await collection.find_one({"_id": result.inserted_id})
        if created_school:
            created_school["_id"] = str(created_school["_id"])
            return School(**created_school)

        raise ValueError("Failed to create school")

    @staticmethod
    async def get_school(
        school_id: str,
        organization_id: Optional[str] = None
    ) -> Optional[School]:
        """
        Get school by ID with optional organization filtering.

        Args:
            school_id: School ID
            organization_id: Organization ID for access control (optional)

        Returns:
            School if found and accessible, None otherwise
        """
        collection = mongodb.get_collection("schools")

        # Build query
        query = {"_id": ObjectId(school_id)}
        if organization_id:
            query["organization_id"] = organization_id

        school = await collection.find_one(query)
        if school:
            school["_id"] = str(school["_id"])
            return School(**school)

        return None

    @staticmethod
    async def get_school_by_admin(admin_user_id: str) -> Optional[School]:
        """
        Get school by admin user ID.

        Args:
            admin_user_id: Admin Supabase user ID

        Returns:
            School if found, None otherwise
        """
        collection = mongodb.get_collection("schools")

        school = await collection.find_one({"admin_user_id": admin_user_id})
        if school:
            school["_id"] = str(school["_id"])
            return School(**school)

        return None

    @staticmethod
    async def list_schools(
        organization_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[School]:
        """
        List schools with organization filtering.

        Args:
            organization_id: Filter by organization (optional)
            skip: Number of schools to skip
            limit: Maximum number of schools to return
            is_active: Filter by active status

        Returns:
            List of schools
        """
        collection = mongodb.get_collection("schools")

        query = {}
        if organization_id:
            query["organization_id"] = organization_id
        if is_active is not None:
            query["is_active"] = is_active

        cursor = collection.find(query).skip(skip).limit(limit).sort("name", 1)
        schools = []

        async for school_doc in cursor:
            school_doc["_id"] = str(school_doc["_id"])
            schools.append(School(**school_doc))

        return schools

    @staticmethod
    async def update_school(school_id: str, update_data: SchoolUpdate) -> bool:
        """
        Update school information.

        Args:
            school_id: School ID
            update_data: Update data

        Returns:
            True if successful, False otherwise
        """
        collection = mongodb.get_collection("schools")

        update_dict = {
            k: v for k, v in update_data.dict(exclude_unset=True).items()
            if v is not None
        }

        if not update_dict:
            return True

        update_dict["updated_at"] = datetime.utcnow()

        result = await collection.update_one(
            {"_id": ObjectId(school_id)},
            {"$set": update_dict}
        )

        return result.modified_count > 0

    @staticmethod
    async def delete_school(school_id: str) -> bool:
        """
        Delete school (soft delete by setting is_active=False).

        Args:
            school_id: School ID

        Returns:
            True if successful, False otherwise
        """
        collection = mongodb.get_collection("schools")

        result = await collection.update_one(
            {"_id": ObjectId(school_id)},
            {"$set": {
                "is_active": False,
                "updated_at": datetime.utcnow()
            }}
        )

        return result.modified_count > 0

    @staticmethod
    async def get_school_stats(school_id: str) -> SchoolStats:
        """
        Get statistics for a school.

        Args:
            school_id: School ID

        Returns:
            School statistics
        """
        # Get school info
        school = await SchoolService.get_school(school_id)
        if not school:
            raise ValueError(f"School not found: {school_id}")

        users_collection = mongodb.get_collection("users")
        materials_collection = mongodb.get_collection("materials")

        # Count students
        total_students = await users_collection.count_documents({
            "school_id": school_id,
            "role": "student",
            "is_active": True
        })

        # Count teachers
        total_teachers = await users_collection.count_documents({
            "school_id": school_id,
            "role": "teacher",
            "is_active": True
        })

        # Count materials
        total_materials = await materials_collection.count_documents({
            "school_id": school_id
        })

        # Materials by subject
        materials_by_subject = {}
        pipeline = [
            {"$match": {"school_id": school_id}},
            {"$group": {
                "_id": "$subject",
                "count": {"$sum": 1}
            }}
        ]
        async for doc in materials_collection.aggregate(pipeline):
            materials_by_subject[doc["_id"]] = doc["count"]

        # Students by grade
        students_by_grade = {}
        pipeline = [
            {"$match": {"school_id": school_id, "role": "student", "is_active": True}},
            {"$group": {
                "_id": "$grade",
                "count": {"$sum": 1}
            }}
        ]
        async for doc in users_collection.aggregate(pipeline):
            grade = doc["_id"]
            if grade:
                students_by_grade[f"Grade {grade}"] = doc["count"]

        # Last activity (most recent material upload)
        last_material = await materials_collection.find_one(
            {"school_id": school_id},
            sort=[("created_at", -1)]
        )
        last_activity = last_material["created_at"] if last_material else None

        return SchoolStats(
            school_id=school_id,
            school_name=school.name,
            total_students=total_students,
            total_materials=total_materials,
            total_teachers=total_teachers,
            materials_by_subject=materials_by_subject,
            students_by_grade=students_by_grade,
            last_activity=last_activity
        )

    @staticmethod
    async def check_material_limit(school_id: str) -> bool:
        """
        Check if school has reached material upload limit.

        Args:
            school_id: School ID

        Returns:
            True if under limit, False if limit reached
        """
        school = await SchoolService.get_school(school_id)
        if not school:
            return False

        materials_collection = mongodb.get_collection("materials")
        current_count = await materials_collection.count_documents({
            "school_id": school_id
        })

        return current_count < school.max_materials

    @staticmethod
    async def check_student_limit(school_id: str) -> bool:
        """
        Check if school has reached student limit.

        Args:
            school_id: School ID

        Returns:
            True if under limit, False if limit reached
        """
        school = await SchoolService.get_school(school_id)
        if not school:
            return False

        users_collection = mongodb.get_collection("users")
        current_count = await users_collection.count_documents({
            "school_id": school_id,
            "role": "student",
            "is_active": True
        })

        return current_count < school.max_students
