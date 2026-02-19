"""
Centralized Organization Service for All KasaAI Apps

This service provides organization management functionality that can be used
across all KasaAI applications (ChurchFlow, EventFlow, InkWave, StudyFlow, etc.).

Features:
- Organization CRUD operations
- User membership management
- Role-based access control
- Universal admin support
- Invitation system

Usage:
    from apps.shared.services.organization_service import get_organization_service

    org_service = get_organization_service()
    organization = await org_service.create_organization(org_data, user_id, user_email)
"""

import os
import re
import secrets
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
import logging

from ..models.organization import (
    Organization, OrganizationUser, OrganizationInvitation,
    OrganizationCreate, OrganizationUpdate, OrganizationUserUpdate,
    OrganizationInviteRequest, OrganizationRole, InvitationStatus
)

logger = logging.getLogger(__name__)


class OrganizationService:
    """MongoDB-based organization service for multi-tenant apps."""

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize the organization service.

        Args:
            database: AsyncIOMotorDatabase instance
        """
        self.db = database
        self.organizations: AsyncIOMotorCollection = database["organizations"]
        self.organization_users: AsyncIOMotorCollection = database["organization_users"]
        self.organization_invitations: AsyncIOMotorCollection = database["organization_invitations"]

    async def initialize_indexes(self):
        """Create database indexes for optimal performance."""
        try:
            # Organization indexes
            await self.organizations.create_index("name", unique=True)
            await self.organizations.create_index("is_active")

            # Organization users indexes
            await self.organization_users.create_index("organization_id")
            await self.organization_users.create_index("user_id")
            await self.organization_users.create_index("email")
            await self.organization_users.create_index(
                [("organization_id", 1), ("user_id", 1)],
                unique=True
            )
            await self.organization_users.create_index("is_active")
            await self.organization_users.create_index("role")

            # Organization invitations indexes
            await self.organization_invitations.create_index("organization_id")
            await self.organization_invitations.create_index("email")
            await self.organization_invitations.create_index("invitation_token", unique=True)
            await self.organization_invitations.create_index("status")
            await self.organization_invitations.create_index("expires_at")

            logger.info("Organization service indexes created successfully")
        except Exception as e:
            # Indexes might already exist
            logger.debug(f"Index creation message: {e}")

    # Organization CRUD Operations

    async def _generate_org_name(self, display_name: str) -> str:
        """
        Generate a unique URL-safe organization name from display name.
        If the name already exists, append a numeric suffix.

        Args:
            display_name: The display name to convert

        Returns:
            A unique, lowercase, URL-safe organization name
        """
        # Convert to lowercase and replace spaces/special chars with hyphens
        base_name = re.sub(r'[^a-z0-9]+', '-', display_name.lower())
        # Remove leading/trailing hyphens
        base_name = base_name.strip('-')
        # Collapse multiple hyphens
        base_name = re.sub(r'-+', '-', base_name)

        # Check if name exists and make it unique
        name = base_name
        counter = 1

        while await self.organizations.find_one({"name": name}):
            # Name exists, try with suffix
            name = f"{base_name}-{counter}"
            counter += 1

            # Safety limit to prevent infinite loop
            if counter > 1000:
                # Use a random suffix as fallback
                import uuid
                name = f"{base_name}-{uuid.uuid4().hex[:8]}"
                break

        return name

    async def create_organization(
        self,
        org_data: OrganizationCreate,
        creator_user_id: str,
        creator_email: str
    ) -> Organization:
        """
        Create a new organization and add creator as admin.

        Args:
            org_data: Organization creation data
            creator_user_id: User ID of the creator
            creator_email: Email of the creator

        Returns:
            Organization: The created organization

        Raises:
            ValueError: If organization name already exists (when manually provided)
        """
        # Auto-generate unique name from display_name if not provided
        org_name = org_data.name if org_data.name else await self._generate_org_name(org_data.display_name)

        # Double-check uniqueness even if name was provided
        if org_data.name:
            existing = await self.organizations.find_one({"name": org_name})
            if existing:
                raise ValueError(f"Organization name '{org_name}' already exists. Please choose a different name.")

        # Create organization
        org = Organization(
            name=org_name,
            display_name=org_data.display_name,
            description=org_data.description or "",
            industry=org_data.industry or "",
            website=org_data.website or ""
        )

        # Insert organization
        await self.organizations.insert_one(org.model_dump())

        # Add creator as admin
        org_user = OrganizationUser(
            organization_id=org.id,
            user_id=creator_user_id,
            email=creator_email,
            role=OrganizationRole.ADMIN,
            display_name=creator_email.split("@")[0]
        )

        await self.organization_users.insert_one(org_user.model_dump())

        logger.info(f"Created organization {org.id} with admin user {creator_user_id}")
        return org

    async def get_organization(self, organization_id: str) -> Optional[Organization]:
        """
        Get organization by ID.

        Args:
            organization_id: Organization ID

        Returns:
            Organization or None if not found
        """
        org_dict = await self.organizations.find_one({"id": organization_id})
        if org_dict:
            return Organization(**org_dict)
        return None

    async def update_organization(
        self,
        organization_id: str,
        update_data: OrganizationUpdate
    ) -> Optional[Organization]:
        """
        Update organization.

        Args:
            organization_id: Organization ID
            update_data: Update data

        Returns:
            Updated organization or None if not found
        """
        # Build update dict (only include non-None values)
        update_dict = {
            k: v for k, v in update_data.model_dump().items()
            if v is not None
        }

        if not update_dict:
            return await self.get_organization(organization_id)

        update_dict["updated_at"] = datetime.utcnow()

        result = await self.organizations.update_one(
            {"id": organization_id},
            {"$set": update_dict}
        )

        if result.modified_count > 0:
            return await self.get_organization(organization_id)
        return None

    async def delete_organization(self, organization_id: str) -> bool:
        """
        Delete organization (soft delete by setting is_active=False).

        Args:
            organization_id: Organization ID

        Returns:
            bool: True if deleted, False if not found
        """
        result = await self.organizations.update_one(
            {"id": organization_id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def list_organizations(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = True
    ) -> List[Organization]:
        """
        List organizations.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            is_active: Filter by active status (None for all)

        Returns:
            List of organizations
        """
        filter_dict = {}
        if is_active is not None:
            filter_dict["is_active"] = is_active

        cursor = self.organizations.find(filter_dict).skip(skip).limit(limit)
        orgs = await cursor.to_list(length=limit)
        return [Organization(**org) for org in orgs]

    async def list_all_organizations(
        self,
        search: Optional[str] = None,
        industry: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 1000
    ) -> List[Organization]:
        """
        List all organizations with advanced search (universal_admin only).

        Args:
            search: Search query for name, display_name, or description
            industry: Filter by industry
            is_active: Filter by active status (None for all)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of organizations matching the filters
        """
        filter_dict = {}

        # Search across name, display_name, and description
        if search:
            filter_dict["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"display_name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]

        # Filter by industry
        if industry:
            filter_dict["industry"] = {"$regex": industry, "$options": "i"}

        # Filter by active status
        if is_active is not None:
            filter_dict["is_active"] = is_active

        cursor = self.organizations.find(filter_dict).skip(skip).limit(limit).sort("display_name", 1)
        orgs = await cursor.to_list(length=limit)
        return [Organization(**org) for org in orgs]

    # User Membership Operations

    async def add_user_to_organization(
        self,
        organization_id: str,
        user_id: str,
        email: str,
        role: OrganizationRole = OrganizationRole.USER,
        **kwargs
    ) -> OrganizationUser:
        """
        Add a user to an organization.

        Args:
            organization_id: Organization ID
            user_id: User ID
            email: User email
            role: User role
            **kwargs: Additional user fields (first_name, last_name, etc.)

        Returns:
            OrganizationUser: The created membership

        Raises:
            ValueError: If user is already a member
        """
        # Check if user is already a member
        existing = await self.organization_users.find_one({
            "organization_id": organization_id,
            "user_id": user_id
        })
        if existing:
            raise ValueError(f"User {user_id} is already a member of organization {organization_id}")

        org_user = OrganizationUser(
            organization_id=organization_id,
            user_id=user_id,
            email=email,
            role=role,
            **kwargs
        )

        await self.organization_users.insert_one(org_user.model_dump())
        logger.info(f"Added user {user_id} to organization {organization_id} with role {role}")
        return org_user

    async def get_organization_user(
        self,
        organization_id: str,
        user_id: str
    ) -> Optional[OrganizationUser]:
        """
        Get organization user membership.

        Args:
            organization_id: Organization ID
            user_id: User ID

        Returns:
            OrganizationUser or None if not found
        """
        user_dict = await self.organization_users.find_one({
            "organization_id": organization_id,
            "user_id": user_id
        })
        if user_dict:
            return OrganizationUser(**user_dict)
        return None

    async def get_organizations_for_user(self, user_id: str, user_email: Optional[str] = None) -> List[OrganizationUser]:
        """
        Get all organizations a user belongs to.

        Handles both MongoDB ObjectId and Supabase UUID user identifiers.
        Falls back to email lookup if user_id doesn't match.

        Args:
            user_id: User ID (MongoDB ObjectId or Supabase UUID)
            user_email: Optional user email for fallback lookup

        Returns:
            List of OrganizationUser memberships
        """
        from bson import ObjectId

        # Try querying by user_id first
        cursor = self.organization_users.find({"user_id": user_id, "is_active": True})
        users = await cursor.to_list(length=100)

        # If no results and email provided, try email lookup
        if not users and user_email:
            logger.debug(f"No orgs found for user_id {user_id}, trying email {user_email}")
            cursor = self.organization_users.find({"email": user_email, "is_active": True})
            users = await cursor.to_list(length=100)

        # Convert ObjectId to string for Pydantic validation
        result = []
        for user in users:
            if isinstance(user.get("organization_id"), ObjectId):
                user["organization_id"] = str(user["organization_id"])
            result.append(OrganizationUser(**user))

        return result

    async def get_users_in_organization(
        self,
        organization_id: str,
        role: Optional[OrganizationRole] = None
    ) -> List[OrganizationUser]:
        """
        Get all users in an organization.

        Args:
            organization_id: Organization ID
            role: Filter by role (optional)

        Returns:
            List of OrganizationUser memberships
        """
        filter_dict = {"organization_id": organization_id, "is_active": True}
        if role:
            filter_dict["role"] = role

        cursor = self.organization_users.find(filter_dict)
        users = await cursor.to_list(length=1000)
        return [OrganizationUser(**user) for user in users]

    async def update_organization_user(
        self,
        organization_id: str,
        user_id: str,
        update_data: OrganizationUserUpdate
    ) -> Optional[OrganizationUser]:
        """
        Update organization user membership.

        Args:
            organization_id: Organization ID
            user_id: User ID
            update_data: Update data

        Returns:
            Updated OrganizationUser or None if not found
        """
        update_dict = {
            k: v for k, v in update_data.model_dump().items()
            if v is not None
        }

        if not update_dict:
            return await self.get_organization_user(organization_id, user_id)

        update_dict["updated_at"] = datetime.utcnow()

        result = await self.organization_users.update_one(
            {"organization_id": organization_id, "user_id": user_id},
            {"$set": update_dict}
        )

        if result.modified_count > 0:
            return await self.get_organization_user(organization_id, user_id)
        return None

    async def remove_user_from_organization(
        self,
        organization_id: str,
        user_id: str
    ) -> bool:
        """
        Remove user from organization (soft delete).

        Args:
            organization_id: Organization ID
            user_id: User ID

        Returns:
            bool: True if removed, False if not found
        """
        result = await self.organization_users.update_one(
            {"organization_id": organization_id, "user_id": user_id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    # Role and Permission Checks

    def is_universal_admin(self, user_id: str, user_email: str) -> bool:
        """
        Check if user is a universal admin.

        Universal admins are defined in environment variables.

        Args:
            user_id: User ID
            user_email: User email

        Returns:
            bool: True if user is universal admin
        """
        admin_emails = os.getenv("UNIVERSAL_ADMIN_EMAILS", "").split(",")
        admin_user_ids = os.getenv("UNIVERSAL_ADMIN_USER_IDS", "").split(",")

        admin_emails = [email.strip().lower() for email in admin_emails if email.strip()]
        admin_user_ids = [uid.strip() for uid in admin_user_ids if uid.strip()]

        return (
            user_email.lower() in admin_emails or
            user_id in admin_user_ids
        )

    async def has_role(
        self,
        organization_id: str,
        user_id: str,
        required_role: OrganizationRole
    ) -> bool:
        """
        Check if user has a specific role in organization.

        Args:
            organization_id: Organization ID
            user_id: User ID
            required_role: Required role

        Returns:
            bool: True if user has the role
        """
        org_user = await self.get_organization_user(organization_id, user_id)
        if not org_user or not org_user.is_active:
            return False
        return org_user.role == required_role

    async def is_admin(self, organization_id: str, user_id: str) -> bool:
        """
        Check if user is an admin in the organization.

        Args:
            organization_id: Organization ID
            user_id: User ID

        Returns:
            bool: True if user is admin
        """
        return await self.has_role(organization_id, user_id, OrganizationRole.ADMIN)

    async def has_access_to_organization(
        self,
        organization_id: str,
        user_id: str,
        user_email: str
    ) -> bool:
        """
        Check if user has access to organization.

        Universal admins have access to all organizations.

        Args:
            organization_id: Organization ID
            user_id: User ID
            user_email: User email

        Returns:
            bool: True if user has access
        """
        # Check if universal admin
        if self.is_universal_admin(user_id, user_email):
            return True

        # Check if user is a member
        org_user = await self.get_organization_user(organization_id, user_id)
        return org_user is not None and org_user.is_active


# Factory function to create organization service

_organization_service_instance = None

def get_organization_service(database: Optional[AsyncIOMotorDatabase] = None) -> OrganizationService:
    """
    Get or create organization service instance.

    Args:
        database: Optional AsyncIOMotorDatabase instance. If not provided,
                 will use the global instance if it exists.

    Returns:
        OrganizationService: The organization service instance

    Usage:
        # In your FastAPI app startup:
        from motor.motor_asyncio import AsyncIOMotorClient
        from apps.shared.services.organization_service import get_organization_service

        client = AsyncIOMotorClient(mongodb_url)
        db = client[database_name]
        org_service = get_organization_service(db)
        await org_service.initialize_indexes()
    """
    global _organization_service_instance

    if database is not None:
        _organization_service_instance = OrganizationService(database)

    if _organization_service_instance is None:
        raise RuntimeError(
            "Organization service not initialized. "
            "Call get_organization_service(database) first."
        )

    return _organization_service_instance
