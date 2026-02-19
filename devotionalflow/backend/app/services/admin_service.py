"""
Admin service for managing users and platform statistics.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from app.db.mongodb import get_database
from app.models.user import (
    UserStatsResponse,
    UserListResponse,
    UserListFilters,
    UserRoleUpdate,
    UserStatusUpdate,
)


class AdminService:
    """Service for admin operations."""

    def __init__(self):
        self.db = get_database()
        self.users_collection = self.db.users
        self.devotionals_collection = self.db.devotionals
        self.comments_collection = self.db.comments
        self.likes_collection = self.db.likes

    async def get_platform_statistics(self) -> Dict[str, Any]:
        """
        Get platform-wide statistics for admin dashboard.

        Returns:
            Dict[str, Any]: Platform statistics including user counts, devotional counts, etc.
        """
        # Count total users
        total_users = await self.users_collection.count_documents({})

        # Count active users (users who are not suspended and are regular users)
        active_users = await self.users_collection.count_documents(
            {"role": "user", "is_suspended": False}
        )

        # Count authors (users who have created at least one devotional)
        authors_pipeline = [
            {"$group": {"_id": "$author_id"}},
            {"$count": "total"}
        ]
        authors_result = await self.devotionals_collection.aggregate(authors_pipeline).to_list(1)
        authors_count = authors_result[0]["total"] if authors_result else 0

        # Count total devotionals
        total_devotionals = await self.devotionals_collection.count_documents({})

        # Count published devotionals
        published_devotionals = await self.devotionals_collection.count_documents(
            {"status": "published"}
        )

        # Count scheduled devotionals
        scheduled_devotionals = await self.devotionals_collection.count_documents(
            {"status": "scheduled"}
        )

        # Count draft devotionals
        draft_devotionals = await self.devotionals_collection.count_documents(
            {"status": "draft"}
        )

        # Get recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        new_users_last_7_days = await self.users_collection.count_documents(
            {"created_at": {"$gte": seven_days_ago}}
        )

        new_devotionals_last_7_days = await self.devotionals_collection.count_documents(
            {"created_at": {"$gte": seven_days_ago}}
        )

        # Get total engagement (likes + comments)
        total_likes = await self.likes_collection.count_documents({})
        total_comments = await self.comments_collection.count_documents({})

        # Calculate total views (sum of all view counts from devotionals)
        total_views = 0
        view_pipeline = [
            {"$group": {"_id": None, "total": {"$sum": "$view_count"}}}
        ]
        view_result = await self.devotionals_collection.aggregate(view_pipeline).to_list(1)
        if view_result:
            total_views = view_result[0].get("total", 0)

        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_authors": authors_count,
            "total_devotionals": total_devotionals,
            "published_devotionals": published_devotionals,
            "scheduled_devotionals": scheduled_devotionals,
            "draft_devotionals": draft_devotionals,
            "new_users_last_7_days": new_users_last_7_days,
            "new_users_this_month": new_users_last_7_days,  # Alias for frontend compatibility
            "new_devotionals_last_7_days": new_devotionals_last_7_days,
            "new_devotionals_this_month": new_devotionals_last_7_days,  # Alias for frontend compatibility
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_views": total_views,
            "total_engagement": total_likes + total_comments,
        }

    async def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent platform activity for admin dashboard.

        Args:
            limit: Maximum number of activities to return

        Returns:
            List[Dict[str, Any]]: List of recent activities
        """
        activities = []

        # Get recent users (last 5)
        recent_users = (
            await self.users_collection.find()
            .sort("created_at", -1)
            .limit(5)
            .to_list(length=5)
        )

        for user in recent_users:
            activities.append(
                {
                    "type": "user_joined",
                    "user_name": user.get("name"),
                    "user_email": user.get("email"),
                    "user_role": user.get("role"),
                    "timestamp": user.get("created_at"),
                }
            )

        # Get recent devotionals (last 5)
        recent_devotionals = (
            await self.devotionals_collection.find()
            .sort("created_at", -1)
            .limit(5)
            .to_list(length=5)
        )

        for devotional in recent_devotionals:
            # Get author info
            author = await self.users_collection.find_one(
                {"_id": ObjectId(devotional.get("author_id"))}
            )

            activities.append(
                {
                    "type": "devotional_published",
                    "devotional_title": devotional.get("title"),
                    "author_name": author.get("name") if author else "Unknown",
                    "status": devotional.get("status"),
                    "timestamp": devotional.get("created_at"),
                }
            )

        # Sort all activities by timestamp
        activities.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)

        return activities[:limit]

    async def get_users_list(
        self, filters: UserListFilters
    ) -> UserListResponse:
        """
        Get paginated list of users with filters.

        Args:
            filters: Filter parameters for users list

        Returns:
            UserListResponse: Paginated list of users
        """
        # Build query filter
        query = {}

        if filters.role:
            query["role"] = filters.role

        if filters.is_suspended is not None:
            query["is_suspended"] = filters.is_suspended

        if filters.search:
            # Search by name or email (case-insensitive)
            query["$or"] = [
                {"name": {"$regex": filters.search, "$options": "i"}},
                {"email": {"$regex": filters.search, "$options": "i"}},
            ]

        # Count total matching documents
        total = await self.users_collection.count_documents(query)

        # Calculate pagination
        skip = (filters.page - 1) * filters.page_size
        total_pages = (total + filters.page_size - 1) // filters.page_size

        # Sort configuration
        sort_direction = 1 if filters.sort_order == "asc" else -1

        # Get users with pagination
        users_cursor = (
            self.users_collection.find(query)
            .sort(filters.sort_by, sort_direction)
            .skip(skip)
            .limit(filters.page_size)
        )

        users = await users_cursor.to_list(length=filters.page_size)

        # Convert to UserStatsResponse with devotional counts
        user_stats_list = []
        for user in users:
            # Count devotionals for all users (any user can be an author)
            devotionals_count = await self.devotionals_collection.count_documents(
                {"author_id": str(user["_id"])}
            )

            user_stats_list.append(
                UserStatsResponse(
                    id=str(user["_id"]),
                    email=user["email"],
                    name=user["name"],
                    role=user["role"],
                    avatar_url=user.get("avatar_url"),
                    is_active=user.get("is_active", True),
                    is_suspended=user.get("is_suspended", False),
                    last_active=user.get("last_active"),
                    created_at=user["created_at"],
                    devotionals_count=devotionals_count,
                )
            )

        return UserListResponse(
            users=user_stats_list,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )

    async def update_user_role(
        self, user_id: str, role_update: UserRoleUpdate
    ) -> Dict[str, Any]:
        """
        Update user role (admin only).

        Args:
            user_id: ID of the user to update
            role_update: New role data

        Returns:
            Dict[str, Any]: Update result

        Raises:
            ValueError: If user not found
        """
        # Check if user exists
        user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")

        # Update role
        result = await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "role": role_update.role,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        return {
            "success": result.modified_count > 0,
            "message": f"User role updated to {role_update.role}",
        }

    async def update_user_status(
        self, user_id: str, status_update: UserStatusUpdate
    ) -> Dict[str, Any]:
        """
        Update user status (suspend/activate).

        Args:
            user_id: ID of the user to update
            status_update: New status data

        Returns:
            Dict[str, Any]: Update result

        Raises:
            ValueError: If user not found
        """
        # Check if user exists
        user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")

        # Update status
        result = await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "is_suspended": status_update.is_suspended,
                    "is_active": not status_update.is_suspended,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        status_text = "suspended" if status_update.is_suspended else "activated"
        return {
            "success": result.modified_count > 0,
            "message": f"User {status_text} successfully",
        }

    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        """
        Delete user and all associated data.

        Args:
            user_id: ID of the user to delete

        Returns:
            Dict[str, Any]: Deletion result

        Raises:
            ValueError: If user not found
        """
        # Check if user exists
        user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")

        # Delete user's devotionals (any user can be an author)
        await self.devotionals_collection.delete_many({"author_id": user_id})

        # Delete user's comments
        await self.comments_collection.delete_many({"user_id": user_id})

        # Delete user's likes
        await self.likes_collection.delete_many({"user_id": user_id})

        # Delete user
        result = await self.users_collection.delete_one({"_id": ObjectId(user_id)})

        return {
            "success": result.deleted_count > 0,
            "message": "User and associated data deleted successfully",
        }
