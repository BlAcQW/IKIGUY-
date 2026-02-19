"""
Leadership Service.

Manages organizational structure including cell groups, zones, and departments.
Handles leadership assignments and hierarchical permission verification.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from bson import ObjectId

from app.core.database import get_database
from app.models.user import User, DepartmentAssignment
from app.models.organizational_structure import CellGroup, Zone, Department

logger = logging.getLogger(__name__)


class LeadershipService:
    """
    Service for managing church leadership and organizational structure.

    Handles:
    - Cell group creation and management
    - Zone creation and management
    - Department creation and management
    - Leadership role assignments
    - Hierarchical permission verification
    """

    def __init__(self):
        """Initialize the leadership service."""
        self.db = None

    def set_database(self, db):
        """Set the database connection."""
        self.db = db

    # ============================================
    # Cell Group Management
    # ============================================

    async def create_cell_group(
        self,
        cell_data: Dict[str, Any],
        organization_id: str,
        created_by_user_id: str
    ) -> CellGroup:
        """
        Create a new cell group.

        Args:
            cell_data: Cell group information (name, zone_id, meeting details)
            organization_id: Organization ID
            created_by_user_id: ID of user creating the cell group

        Returns:
            CellGroup: Created cell group object

        Raises:
            ValueError: If zone not found or required fields missing
            Exception: If database operation fails
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Creating cell group: {cell_data.get('name')}")

        # Validate required fields
        if not cell_data.get("name"):
            raise ValueError("Cell group name is required")

        # Verify zone exists if provided
        if cell_data.get("zone_id"):
            zone = await self.db.zones.find_one({"_id": ObjectId(cell_data["zone_id"])})
            if not zone:
                raise ValueError(f"Zone {cell_data['zone_id']} not found")

        # Create cell group document
        cell_group_doc = {
            "organization_id": ObjectId(organization_id),
            "branch_id": ObjectId(cell_data["branch_id"]) if cell_data.get("branch_id") else None,
            "zone_id": ObjectId(cell_data["zone_id"]) if cell_data.get("zone_id") else None,
            "name": cell_data["name"],
            "description": cell_data.get("description"),
            "meeting_day": cell_data.get("meeting_day"),
            "meeting_time": cell_data.get("meeting_time"),
            "meeting_location": cell_data.get("meeting_location"),
            "cell_leader_id": ObjectId(cell_data["cell_leader_id"]) if cell_data.get("cell_leader_id") else None,
            "assistant_leaders": [ObjectId(uid) for uid in cell_data.get("assistant_leaders", [])],
            "target_size": cell_data.get("target_size", 12),
            "current_member_count": 0,
            "is_full": False,
            "status": "active",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = await self.db.cell_groups.insert_one(cell_group_doc)
        cell_group_doc["_id"] = result.inserted_id
        cell_group = CellGroup(**cell_group_doc)

        # Update zone cell count if zone specified
        if cell_data.get("zone_id"):
            await self.db.zones.update_one(
                {"_id": ObjectId(cell_data["zone_id"])},
                {"$inc": {"cell_group_count": 1}}
            )

        # Assign cell leader role if leader specified
        if cell_data.get("cell_leader_id"):
            try:
                await self.assign_cell_leader(
                    user_id=cell_data["cell_leader_id"],
                    cell_group_id=str(result.inserted_id),
                    assigned_by_user_id=created_by_user_id
                )
            except Exception as e:
                logger.error(f"Failed to assign cell leader: {e}")
                # Don't fail the whole operation

        logger.info(f"Created cell group: {cell_group.id}")

        return cell_group

    async def assign_cell_leader(
        self,
        user_id: str,
        cell_group_id: str,
        assigned_by_user_id: str
    ) -> CellGroup:
        """
        Assign user as cell leader.

        Updates cell group leadership and adds "cell_leader" role to user.

        Args:
            user_id: User ID to assign as cell leader
            cell_group_id: Cell group ID
            assigned_by_user_id: ID of user making the assignment

        Returns:
            CellGroup: Updated cell group object

        Raises:
            ValueError: If user or cell group not found
            Exception: If database operation fails
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Assigning user {user_id} as cell leader for group {cell_group_id}")

        # Verify user exists
        user = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Verify cell group exists
        cell_group = await self.db.cell_groups.find_one({"_id": ObjectId(cell_group_id)})
        if not cell_group:
            raise ValueError(f"Cell group {cell_group_id} not found")

        # Update cell group leadership
        await self.db.cell_groups.update_one(
            {"_id": ObjectId(cell_group_id)},
            {
                "$set": {
                    "cell_leader_id": ObjectId(user_id),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Add cell_leader role to user if not already present
        if "cell_leader" not in (user.get("roles") or []):
            await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$addToSet": {"roles": "cell_leader"},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

        # Fetch and return updated cell group
        updated_cell_group_doc = await self.db.cell_groups.find_one({"_id": ObjectId(cell_group_id)})
        updated_cell_group = CellGroup(**updated_cell_group_doc)

        logger.info(f"Assigned cell leader successfully")

        return updated_cell_group

    async def get_cell_members(
        self,
        cell_group_id: str,
        include_visitors: bool = True,
        limit: int = 100,
        skip: int = 0
    ) -> List[User]:
        """
        Get all members assigned to a cell group.

        Args:
            cell_group_id: Cell group ID
            include_visitors: Whether to include visitors (default: True)
            limit: Maximum number of results (default: 100)
            skip: Number of results to skip for pagination (default: 0)

        Returns:
            List[User]: List of members in the cell group

        Raises:
            ValueError: If cell group not found
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Fetching members for cell group {cell_group_id}")

        # Verify cell group exists
        cell_group = await self.db.cell_groups.find_one({"_id": ObjectId(cell_group_id)})
        if not cell_group:
            raise ValueError(f"Cell group {cell_group_id} not found")

        # Build query
        query = {"cell_group_id": ObjectId(cell_group_id)}

        if not include_visitors:
            query["member_status"] = {"$ne": "visitor"}

        # Query members
        cursor = self.db.users.find(query).sort("name", 1).skip(skip).limit(limit)

        members = []
        async for doc in cursor:
            try:
                members.append(User(**doc))
            except Exception as e:
                logger.error(f"Error parsing user document: {e}")
                continue

        logger.info(f"Found {len(members)} members in cell group")

        return members

    async def get_cell_groups(
        self,
        organization_id: str,
        zone_id: Optional[str] = None,
        is_active: bool = True,
        limit: int = 100,
        skip: int = 0
    ) -> List[CellGroup]:
        """
        Get cell groups for organization.

        Args:
            organization_id: Organization ID
            zone_id: Filter by zone (optional)
            is_active: Filter by active status (default: True)
            limit: Maximum number of results (default: 100)
            skip: Number of results to skip for pagination (default: 0)

        Returns:
            List[CellGroup]: List of cell groups
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Fetching cell groups for organization {organization_id}")

        # Build query
        query = {
            "organization_id": ObjectId(organization_id),
            "is_active": is_active
        }

        if zone_id:
            query["zone_id"] = ObjectId(zone_id)

        # Query cell groups
        cursor = self.db.cell_groups.find(query).sort("name", 1).skip(skip).limit(limit)

        cell_groups = []
        async for doc in cursor:
            try:
                cell_groups.append(CellGroup(**doc))
            except Exception as e:
                logger.error(f"Error parsing cell group document: {e}")
                continue

        logger.info(f"Found {len(cell_groups)} cell groups")

        return cell_groups

    # ============================================
    # Zone Management
    # ============================================

    async def create_zone(
        self,
        zone_data: Dict[str, Any],
        organization_id: str,
        created_by_user_id: str
    ) -> Zone:
        """
        Create a new zone.

        Args:
            zone_data: Zone information (name, geographic_area, zone_leader_id)
            organization_id: Organization ID
            created_by_user_id: ID of user creating the zone

        Returns:
            Zone: Created zone object

        Raises:
            ValueError: If required fields missing
            Exception: If database operation fails
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Creating zone: {zone_data.get('name')}")

        # Validate required fields
        if not zone_data.get("name"):
            raise ValueError("Zone name is required")

        # Create zone document
        zone_doc = {
            "organization_id": ObjectId(organization_id),
            "branch_id": ObjectId(zone_data["branch_id"]) if zone_data.get("branch_id") else None,
            "name": zone_data["name"],
            "description": zone_data.get("description"),
            "geographic_area": zone_data.get("geographic_area"),
            "zone_leader_id": ObjectId(zone_data["zone_leader_id"]) if zone_data.get("zone_leader_id") else None,
            "assistant_zone_leaders": [ObjectId(uid) for uid in zone_data.get("assistant_zone_leaders", [])],
            "cell_group_count": 0,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = await self.db.zones.insert_one(zone_doc)
        zone_doc["_id"] = result.inserted_id
        zone = Zone(**zone_doc)

        # Assign zone leader role if leader specified
        if zone_data.get("zone_leader_id"):
            try:
                await self.assign_zone_leader(
                    user_id=zone_data["zone_leader_id"],
                    zone_id=str(result.inserted_id),
                    assigned_by_user_id=created_by_user_id
                )
            except Exception as e:
                logger.error(f"Failed to assign zone leader: {e}")
                # Don't fail the whole operation

        logger.info(f"Created zone: {zone.id}")

        return zone

    async def get_zones(
        self,
        organization_id: str,
        is_active: bool = True,
        limit: int = 100,
        skip: int = 0
    ) -> List[Zone]:
        """
        Get zones for organization.

        Args:
            organization_id: Organization ID
            is_active: Filter by active status (default: True)
            limit: Maximum number of results (default: 100)
            skip: Number of results to skip for pagination (default: 0)

        Returns:
            List[Zone]: List of zones
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Fetching zones for organization {organization_id}")

        # Build query
        query = {
            "organization_id": ObjectId(organization_id),
            "is_active": is_active
        }

        # Query zones
        cursor = self.db.zones.find(query).sort("name", 1).skip(skip).limit(limit)

        zones = []
        async for doc in cursor:
            try:
                zones.append(Zone(**doc))
            except Exception as e:
                logger.error(f"Error parsing zone document: {e}")
                continue

        logger.info(f"Found {len(zones)} zones")

        return zones

    async def assign_zone_leader(
        self,
        user_id: str,
        zone_id: str,
        assigned_by_user_id: str
    ) -> Zone:
        """
        Assign user as zone leader.

        Updates zone leadership and adds "zone_leader" role to user.

        Args:
            user_id: User ID to assign as zone leader
            zone_id: Zone ID
            assigned_by_user_id: ID of user making the assignment

        Returns:
            Zone: Updated zone object

        Raises:
            ValueError: If user or zone not found
            Exception: If database operation fails
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Assigning user {user_id} as zone leader for zone {zone_id}")

        # Verify user exists
        user = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Verify zone exists
        zone = await self.db.zones.find_one({"_id": ObjectId(zone_id)})
        if not zone:
            raise ValueError(f"Zone {zone_id} not found")

        # Update zone leadership
        await self.db.zones.update_one(
            {"_id": ObjectId(zone_id)},
            {
                "$set": {
                    "zone_leader_id": ObjectId(user_id),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Add zone_leader role to user if not already present
        if "zone_leader" not in (user.get("roles") or []):
            await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$addToSet": {"roles": "zone_leader"},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

        # Fetch and return updated zone
        updated_zone_doc = await self.db.zones.find_one({"_id": ObjectId(zone_id)})
        updated_zone = Zone(**updated_zone_doc)

        logger.info(f"Assigned zone leader successfully")

        return updated_zone

    async def get_zone_members(
        self,
        zone_id: str,
        include_visitors: bool = True,
        limit: int = 200,
        skip: int = 0
    ) -> List[User]:
        """
        Get all members in a zone (across all cell groups).

        Args:
            zone_id: Zone ID
            include_visitors: Whether to include visitors (default: True)
            limit: Maximum number of results (default: 200)
            skip: Number of results to skip for pagination (default: 0)

        Returns:
            List[User]: List of members in the zone

        Raises:
            ValueError: If zone not found
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Fetching members for zone {zone_id}")

        # Verify zone exists
        zone = await self.db.zones.find_one({"_id": ObjectId(zone_id)})
        if not zone:
            raise ValueError(f"Zone {zone_id} not found")

        # Build query
        query = {"zone_id": ObjectId(zone_id)}

        if not include_visitors:
            query["member_status"] = {"$ne": "visitor"}

        # Query members
        cursor = self.db.users.find(query).sort("name", 1).skip(skip).limit(limit)

        members = []
        async for doc in cursor:
            try:
                members.append(User(**doc))
            except Exception as e:
                logger.error(f"Error parsing user document: {e}")
                continue

        logger.info(f"Found {len(members)} members in zone")

        return members

    # ============================================
    # Department Management
    # ============================================

    async def create_department(
        self,
        department_data: Dict[str, Any],
        organization_id: str,
        created_by_user_id: str
    ) -> Department:
        """
        Create a new department.

        Args:
            department_data: Department information (name, type, department_head_id)
            organization_id: Organization ID
            created_by_user_id: ID of user creating the department

        Returns:
            Department: Created department object

        Raises:
            ValueError: If required fields missing
            Exception: If database operation fails
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Creating department: {department_data.get('name')}")

        # Validate required fields
        if not department_data.get("name"):
            raise ValueError("Department name is required")
        if not department_data.get("department_type"):
            raise ValueError("Department type is required")

        # Create department document
        department_doc = {
            "organization_id": ObjectId(organization_id),
            "branch_id": ObjectId(department_data["branch_id"]) if department_data.get("branch_id") else None,
            "name": department_data["name"],
            "description": department_data.get("description"),
            "department_type": department_data["department_type"],
            "department_head_id": ObjectId(department_data["department_head_id"]) if department_data.get("department_head_id") else None,
            "assistant_heads": [ObjectId(uid) for uid in department_data.get("assistant_heads", [])],
            "volunteer_count": 0,
            "leader_count": 0,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = await self.db.departments.insert_one(department_doc)
        department_doc["_id"] = result.inserted_id
        department = Department(**department_doc)

        # Assign department head role if head specified
        if department_data.get("department_head_id"):
            try:
                await self.assign_department_head(
                    user_id=department_data["department_head_id"],
                    department_id=str(result.inserted_id),
                    assigned_by_user_id=created_by_user_id
                )
            except Exception as e:
                logger.error(f"Failed to assign department head: {e}")
                # Don't fail the whole operation

        logger.info(f"Created department: {department.id}")

        return department

    async def assign_department_head(
        self,
        user_id: str,
        department_id: str,
        assigned_by_user_id: str
    ) -> Department:
        """
        Assign user as department head.

        Updates department leadership and adds "department_head" role to user.

        Args:
            user_id: User ID to assign as department head
            department_id: Department ID
            assigned_by_user_id: ID of user making the assignment

        Returns:
            Department: Updated department object

        Raises:
            ValueError: If user or department not found
            Exception: If database operation fails
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Assigning user {user_id} as department head for department {department_id}")

        # Verify user exists
        user = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Verify department exists
        department = await self.db.departments.find_one({"_id": ObjectId(department_id)})
        if not department:
            raise ValueError(f"Department {department_id} not found")

        # Update department leadership
        await self.db.departments.update_one(
            {"_id": ObjectId(department_id)},
            {
                "$set": {
                    "department_head_id": ObjectId(user_id),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Add department_head role to user if not already present
        if "department_head" not in (user.get("roles") or []):
            await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$addToSet": {"roles": "department_head"},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

        # Fetch and return updated department
        updated_department_doc = await self.db.departments.find_one({"_id": ObjectId(department_id)})
        updated_department = Department(**updated_department_doc)

        logger.info(f"Assigned department head successfully")

        return updated_department

    async def assign_volunteer_to_department(
        self,
        user_id: str,
        department_id: str,
        role: str,
        assigned_by_user_id: str
    ) -> User:
        """
        Assign volunteer to department.

        Args:
            user_id: User ID to assign
            department_id: Department ID
            role: Department role (volunteer, leader, head)
            assigned_by_user_id: ID of user making the assignment

        Returns:
            User: Updated user object

        Raises:
            ValueError: If user or department not found, or invalid role
            Exception: If database operation fails
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Assigning user {user_id} to department {department_id} as {role}")

        # Validate role
        if role not in ["volunteer", "leader", "head"]:
            raise ValueError(f"Invalid department role: {role}")

        # Verify user exists
        user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            raise ValueError(f"User {user_id} not found")

        # Verify department exists
        department = await self.db.departments.find_one({"_id": ObjectId(department_id)})
        if not department:
            raise ValueError(f"Department {department_id} not found")

        # Create department assignment
        department_assignment = {
            "department_id": ObjectId(department_id),
            "role": role,
            "joined_at": datetime.utcnow(),
            "assigned_by_user_id": ObjectId(assigned_by_user_id),
            "is_active": True
        }

        # Check if user already assigned to this department
        user = User(**user_doc)
        existing_assignment = next(
            (dept for dept in (user.departments or []) if dept.department_id == ObjectId(department_id)),
            None
        )

        if existing_assignment:
            # Update existing assignment
            await self.db.users.update_one(
                {
                    "_id": ObjectId(user_id),
                    "departments.department_id": ObjectId(department_id)
                },
                {
                    "$set": {
                        "departments.$.role": role,
                        "departments.$.is_active": True,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        else:
            # Add new assignment
            await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$push": {"departments": department_assignment},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

            # Increment department counts
            if role == "volunteer":
                await self.db.departments.update_one(
                    {"_id": ObjectId(department_id)},
                    {"$inc": {"volunteer_count": 1}}
                )
            elif role in ["leader", "head"]:
                await self.db.departments.update_one(
                    {"_id": ObjectId(department_id)},
                    {"$inc": {"leader_count": 1}}
                )

        # Fetch and return updated user
        updated_user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        updated_user = User(**updated_user_doc)

        logger.info(f"Assigned user to department successfully")

        return updated_user

    # ============================================
    # Permission Verification
    # ============================================

    async def verify_leadership_permission(
        self,
        user_id: str,
        target_user_id: str,
        action: str
    ) -> bool:
        """
        Verify hierarchical leadership permission.

        Checks if user has permission to perform action on target_user based on
        organizational hierarchy.

        Args:
            user_id: User requesting the action
            target_user_id: Target user for the action
            action: Action to perform (view, edit, assign)

        Returns:
            bool: True if permission granted, False otherwise

        Permission hierarchy:
        - Admins: All members
        - Zone leaders: All members in their zone
        - Cell leaders: Only members assigned to their cell
        - Department heads: Only volunteers in their department
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Verifying permission for user {user_id} to {action} user {target_user_id}")

        # Fetch both users
        user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        target_user_doc = await self.db.users.find_one({"_id": ObjectId(target_user_id)})

        if not user_doc or not target_user_doc:
            logger.warning("User or target user not found")
            return False

        user = User(**user_doc)
        target_user = User(**target_user_doc)

        # Admins have full access
        if "admin" in (user.roles or []):
            logger.info("Permission granted: User is admin")
            return True

        # Zone leaders: Can access all members in their zone
        if "zone_leader" in (user.roles or []):
            # Find zones where user is zone leader
            zones = await self.db.zones.find({"zone_leader_id": user.id}).to_list(length=10)
            zone_ids = [zone["_id"] for zone in zones]

            if target_user.zone_id in zone_ids:
                logger.info("Permission granted: User is zone leader for target's zone")
                return True

        # Cell leaders: Can access members in their cell
        if "cell_leader" in (user.roles or []):
            # Find cell groups where user is cell leader
            cell_groups = await self.db.cell_groups.find({"cell_leader_id": user.id}).to_list(length=10)
            cell_group_ids = [cg["_id"] for cg in cell_groups]

            if target_user.cell_group_id in cell_group_ids:
                logger.info("Permission granted: User is cell leader for target's cell group")
                return True

        # Department heads: Can access volunteers in their department
        if "department_head" in (user.roles or []):
            # Find departments where user is department head
            departments = await self.db.departments.find({"department_head_id": user.id}).to_list(length=10)
            department_ids = [dept["_id"] for dept in departments]

            # Check if target user is in any of these departments
            target_department_ids = [dept.department_id for dept in (target_user.departments or [])]
            if any(dept_id in department_ids for dept_id in target_department_ids):
                logger.info("Permission granted: User is department head for target's department")
                return True

        logger.info("Permission denied: No hierarchical relationship found")
        return False

    async def get_members_under_leadership(
        self,
        user_id: str,
        include_visitors: bool = True,
        limit: int = 200,
        skip: int = 0
    ) -> List[User]:
        """
        Get all members under a leader's oversight.

        Returns all members the leader has access to based on their role
        (cell leader, zone leader, department head).

        Args:
            user_id: Leader's user ID
            include_visitors: Whether to include visitors (default: True)
            limit: Maximum number of results (default: 200)
            skip: Number of results to skip for pagination (default: 0)

        Returns:
            List[User]: List of members under leadership
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Fetching members under leadership of user {user_id}")

        # Fetch leader
        user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            raise ValueError(f"User {user_id} not found")

        user = User(**user_doc)
        member_ids = set()

        # If zone leader, get all members in zones
        if "zone_leader" in (user.roles or []):
            zones = await self.db.zones.find({"zone_leader_id": user.id}).to_list(length=10)
            zone_ids = [zone["_id"] for zone in zones]

            cursor = self.db.users.find({"zone_id": {"$in": zone_ids}})
            async for doc in cursor:
                member_ids.add(doc["_id"])

        # If cell leader, get all members in cell groups
        if "cell_leader" in (user.roles or []):
            cell_groups = await self.db.cell_groups.find({"cell_leader_id": user.id}).to_list(length=10)
            cell_group_ids = [cg["_id"] for cg in cell_groups]

            cursor = self.db.users.find({"cell_group_id": {"$in": cell_group_ids}})
            async for doc in cursor:
                member_ids.add(doc["_id"])

        # If department head, get all volunteers in departments
        if "department_head" in (user.roles or []):
            departments = await self.db.departments.find({"department_head_id": user.id}).to_list(length=10)
            department_ids = [dept["_id"] for dept in departments]

            cursor = self.db.users.find({"departments.department_id": {"$in": department_ids}})
            async for doc in cursor:
                member_ids.add(doc["_id"])

        # Build query for final member list
        query = {"_id": {"$in": list(member_ids)}}

        if not include_visitors:
            query["member_status"] = {"$ne": "visitor"}

        # Fetch members
        cursor = self.db.users.find(query).sort("name", 1).skip(skip).limit(limit)

        members = []
        async for doc in cursor:
            try:
                members.append(User(**doc))
            except Exception as e:
                logger.error(f"Error parsing user document: {e}")
                continue

        logger.info(f"Found {len(members)} members under leadership")

        return members


# Global instance
leadership_service = LeadershipService()
