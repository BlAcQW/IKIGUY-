"""
Group Service.

Manages group and subgroup operations including creation, updates, and member assignments.
Implements critical single-select vs multi-select logic for subgroup memberships.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from bson import ObjectId

from app.core.database import get_database
from app.models.user import User
from app.models.groups import Group, Subgroup

logger = logging.getLogger(__name__)


class GroupService:
    """
    Service for managing groups and subgroups.

    Handles:
    - Group CRUD operations
    - Subgroup CRUD operations
    - Member assignment to subgroups
    - Single-select vs multi-select enforcement
    - Member count tracking
    """

    def __init__(self):
        """Initialize the group service."""
        self.db = None

    def set_database(self, db):
        """Set the database connection."""
        self.db = db

    # ============================================================================
    # GROUP CRUD OPERATIONS
    # ============================================================================

    async def create_group(
        self,
        group_data: Dict[str, Any],
        organization_id: str,
        created_by_user_id: str
    ) -> Group:
        """
        Create a new group.

        Args:
            group_data: Group information (name, description)
            organization_id: Organization ID
            created_by_user_id: ID of user creating the group

        Returns:
            Group: Created group object

        Raises:
            ValueError: If required fields missing
            Exception: If database operation fails
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Creating group: {group_data.get('name')}")

        # Validate required fields
        if not group_data.get("name"):
            raise ValueError("Group name is required")

        # Create group document
        group_doc = {
            "organization_id": ObjectId(organization_id),
            "name": group_data["name"],
            "description": group_data.get("description"),
            "created_by_user_id": ObjectId(created_by_user_id),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
        }

        result = await self.db.groups.insert_one(group_doc)
        group_doc["_id"] = result.inserted_id

        logger.info(f"Created group: {result.inserted_id}")
        return Group(**group_doc)

    async def get_groups(
        self,
        organization_id: str,
        is_active: bool = True,
        limit: int = 100,
        skip: int = 0
    ) -> List[Group]:
        """
        Get groups for an organization.

        Args:
            organization_id: Organization ID
            is_active: Filter by active status (default: True)
            limit: Maximum number of groups to return
            skip: Number of groups to skip (pagination)

        Returns:
            List[Group]: List of groups
        """
        if self.db is None:
            self.db = get_database()

        query = {"organization_id": ObjectId(organization_id)}
        if is_active is not None:
            query["is_active"] = is_active

        cursor = self.db.groups.find(query).limit(limit).skip(skip).sort("name", 1)
        groups = []
        async for doc in cursor:
            groups.append(Group(**doc))

        return groups

    async def get_group(self, group_id: str) -> Optional[Group]:
        """
        Get a group by ID.

        Args:
            group_id: Group ID

        Returns:
            Group or None if not found
        """
        if self.db is None:
            self.db = get_database()

        doc = await self.db.groups.find_one({"_id": ObjectId(group_id)})
        return Group(**doc) if doc else None

    async def update_group(
        self,
        group_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Group]:
        """
        Update a group.

        Args:
            group_id: Group ID
            update_data: Fields to update

        Returns:
            Updated Group or None if not found
        """
        if self.db is None:
            self.db = get_database()

        update_data["updated_at"] = datetime.utcnow()

        result = await self.db.groups.find_one_and_update(
            {"_id": ObjectId(group_id)},
            {"$set": update_data},
            return_document=True
        )

        return Group(**result) if result else None

    async def delete_group(self, group_id: str) -> bool:
        """
        Soft delete a group.

        Args:
            group_id: Group ID

        Returns:
            True if successful
        """
        if self.db is None:
            self.db = get_database()

        result = await self.db.groups.update_one(
            {"_id": ObjectId(group_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )

        return result.modified_count > 0

    # ============================================================================
    # SUBGROUP CRUD OPERATIONS
    # ============================================================================

    async def create_subgroup(
        self,
        group_id: str,
        subgroup_data: Dict[str, Any],
        organization_id: str
    ) -> Subgroup:
        """
        Create a new subgroup.

        Args:
            group_id: Parent group ID
            subgroup_data: Subgroup information (name, description, selection_mode)
            organization_id: Organization ID

        Returns:
            Subgroup: Created subgroup object

        Raises:
            ValueError: If group not found or required fields missing
        """
        if self.db is None:
            self.db = get_database()

        # Verify group exists
        group = await self.db.groups.find_one({"_id": ObjectId(group_id)})
        if not group:
            raise ValueError(f"Group {group_id} not found")

        # Validate required fields
        if not subgroup_data.get("name"):
            raise ValueError("Subgroup name is required")
        if not subgroup_data.get("selection_mode"):
            raise ValueError("Selection mode is required")
        if subgroup_data["selection_mode"] not in ["single", "multi"]:
            raise ValueError("Selection mode must be 'single' or 'multi'")

        # Create subgroup document
        subgroup_doc = {
            "group_id": ObjectId(group_id),
            "organization_id": ObjectId(organization_id),
            "name": subgroup_data["name"],
            "description": subgroup_data.get("description"),
            "selection_mode": subgroup_data["selection_mode"],
            "member_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
        }

        result = await self.db.subgroups.insert_one(subgroup_doc)
        subgroup_doc["_id"] = result.inserted_id

        logger.info(f"Created subgroup: {result.inserted_id}")
        return Subgroup(**subgroup_doc)

    async def get_subgroups(
        self,
        group_id: str,
        is_active: bool = True,
        limit: int = 100,
        skip: int = 0
    ) -> List[Subgroup]:
        """
        Get subgroups for a group.

        Args:
            group_id: Group ID
            is_active: Filter by active status
            limit: Maximum number of subgroups
            skip: Number of subgroups to skip

        Returns:
            List[Subgroup]: List of subgroups
        """
        if self.db is None:
            self.db = get_database()

        query = {"group_id": ObjectId(group_id)}
        if is_active is not None:
            query["is_active"] = is_active

        cursor = self.db.subgroups.find(query).limit(limit).skip(skip).sort("name", 1)
        subgroups = []
        async for doc in cursor:
            subgroups.append(Subgroup(**doc))

        return subgroups

    async def get_subgroup(self, subgroup_id: str) -> Optional[Subgroup]:
        """Get a subgroup by ID."""
        if self.db is None:
            self.db = get_database()

        doc = await self.db.subgroups.find_one({"_id": ObjectId(subgroup_id)})
        return Subgroup(**doc) if doc else None

    async def update_subgroup(
        self,
        subgroup_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Subgroup]:
        """Update a subgroup."""
        if self.db is None:
            self.db = get_database()

        update_data["updated_at"] = datetime.utcnow()

        result = await self.db.subgroups.find_one_and_update(
            {"_id": ObjectId(subgroup_id)},
            {"$set": update_data},
            return_document=True
        )

        return Subgroup(**result) if result else None

    async def delete_subgroup(self, subgroup_id: str) -> bool:
        """Soft delete a subgroup."""
        if self.db is None:
            self.db = get_database()

        result = await self.db.subgroups.update_one(
            {"_id": ObjectId(subgroup_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )

        return result.modified_count > 0

    # ============================================================================
    # MEMBER ASSIGNMENT - CRITICAL LOGIC
    # ============================================================================

    async def assign_member_to_subgroup(
        self,
        user_id: str,
        subgroup_id: str,
        assigned_by_user_id: str
    ) -> User:
        """
        Assign a member to a subgroup.

        CRITICAL LOGIC: Enforces single-select constraint automatically.
        If subgroup is single-select mode, removes member from other subgroups
        in the same parent group before adding to new subgroup.

        Args:
            user_id: User ID to assign
            subgroup_id: Subgroup ID to assign to
            assigned_by_user_id: User ID of admin making assignment

        Returns:
            Updated User object

        Raises:
            ValueError: If user or subgroup not found
        """
        if self.db is None:
            self.db = get_database()

        # Verify user exists
        user = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Verify subgroup exists
        subgroup = await self.db.subgroups.find_one({"_id": ObjectId(subgroup_id)})
        if not subgroup:
            raise ValueError(f"Subgroup {subgroup_id} not found")

        # Check if member already in this subgroup
        existing_membership = None
        if user.get("subgroup_memberships"):
            for membership in user["subgroup_memberships"]:
                if membership["subgroup_id"] == ObjectId(subgroup_id) and membership.get("is_active", True):
                    existing_membership = membership
                    break

        if existing_membership:
            logger.info(f"User {user_id} already in subgroup {subgroup_id}")
            return User(**user)

        # CRITICAL: If single-select mode, remove from other subgroups in same group
        if subgroup["selection_mode"] == "single":
            # Find and remove existing subgroup memberships for this group
            old_subgroups_to_decrement = []

            if user.get("subgroup_memberships"):
                for membership in user["subgroup_memberships"]:
                    if membership["group_id"] == subgroup["group_id"] and membership.get("is_active", True):
                        old_subgroups_to_decrement.append(membership["subgroup_id"])

            # Remove old memberships
            if old_subgroups_to_decrement:
                await self.db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$pull": {
                            "subgroup_memberships": {
                                "group_id": subgroup["group_id"],
                                "subgroup_id": {"$in": old_subgroups_to_decrement}
                            }
                        }
                    }
                )

                # Decrement member counts for old subgroups
                for old_subgroup_id in old_subgroups_to_decrement:
                    await self.db.subgroups.update_one(
                        {"_id": old_subgroup_id},
                        {"$inc": {"member_count": -1}}
                    )
                    logger.info(f"Removed user {user_id} from subgroup {old_subgroup_id} (single-select)")

        # Add new membership
        membership = {
            "group_id": subgroup["group_id"],
            "subgroup_id": ObjectId(subgroup_id),
            "joined_at": datetime.utcnow(),
            "assigned_by_user_id": ObjectId(assigned_by_user_id),
            "is_active": True
        }

        await self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"subgroup_memberships": membership}}
        )

        # Increment member count
        await self.db.subgroups.update_one(
            {"_id": ObjectId(subgroup_id)},
            {"$inc": {"member_count": 1}}
        )

        logger.info(f"Assigned user {user_id} to subgroup {subgroup_id}")

        # Return updated user
        updated_user = await self.db.users.find_one({"_id": ObjectId(user_id)})
        return User(**updated_user)

    async def remove_member_from_subgroup(
        self,
        user_id: str,
        subgroup_id: str
    ) -> User:
        """
        Remove a member from a subgroup.

        Args:
            user_id: User ID
            subgroup_id: Subgroup ID

        Returns:
            Updated User object
        """
        if self.db is None:
            self.db = get_database()

        # Remove membership
        result = await self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$pull": {
                    "subgroup_memberships": {
                        "subgroup_id": ObjectId(subgroup_id)
                    }
                }
            }
        )

        if result.modified_count > 0:
            # Decrement member count
            await self.db.subgroups.update_one(
                {"_id": ObjectId(subgroup_id)},
                {"$inc": {"member_count": -1}}
            )
            logger.info(f"Removed user {user_id} from subgroup {subgroup_id}")

        # Return updated user
        updated_user = await self.db.users.find_one({"_id": ObjectId(user_id)})
        return User(**updated_user)

    async def get_subgroup_members(
        self,
        subgroup_id: str,
        limit: int = 100,
        skip: int = 0
    ) -> List[User]:
        """
        Get all members in a subgroup.

        Args:
            subgroup_id: Subgroup ID
            limit: Maximum number of members
            skip: Number of members to skip

        Returns:
            List[User]: List of members
        """
        if self.db is None:
            self.db = get_database()

        cursor = self.db.users.find(
            {"subgroup_memberships.subgroup_id": ObjectId(subgroup_id)}
        ).limit(limit).skip(skip)

        members = []
        async for doc in cursor:
            members.append(User(**doc))

        return members

    async def get_member_subgroups(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all subgroups a member belongs to, enriched with group/subgroup names.

        Args:
            user_id: User ID

        Returns:
            List of enriched membership data
        """
        if self.db is None:
            self.db = get_database()

        user = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user or not user.get("subgroup_memberships"):
            return []

        enriched_memberships = []

        for membership in user["subgroup_memberships"]:
            if not membership.get("is_active", True):
                continue

            # Get group info
            group = await self.db.groups.find_one({"_id": membership["group_id"]})
            # Get subgroup info
            subgroup = await self.db.subgroups.find_one({"_id": membership["subgroup_id"]})

            if group and subgroup:
                enriched_memberships.append({
                    "group_id": str(membership["group_id"]),
                    "group_name": group["name"],
                    "subgroup_id": str(membership["subgroup_id"]),
                    "subgroup_name": subgroup["name"],
                    "selection_mode": subgroup["selection_mode"],
                    "joined_at": membership["joined_at"],
                    "is_active": membership.get("is_active", True)
                })

        return enriched_memberships
