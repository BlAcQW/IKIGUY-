"""Organization service for managing organizations, users, and invitations in MongoDB."""

import os
import re
import secrets
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from ..models import (
    Organization, OrganizationUser, OrganizationInvitation,
    OrganizationCreate, OrganizationUpdate, OrganizationUserUpdate,
    OrganizationInviteRequest, OrganizationRole, InvitationStatus
)


class MongoDBOrganizationService:
    """MongoDB-based organization service."""

    def __init__(self):
        """Initialize the organization service."""
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.organizations: Optional[Collection] = None
        self.organization_users: Optional[Collection] = None
        self.organization_invitations: Optional[Collection] = None
        self._connect()

    def _connect(self):
        """Connect to MongoDB."""
        try:
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
            database_name = os.getenv("MONGO_CORE_DATABASE", "kasaai_core")

            self.client = MongoClient(mongodb_url)
            self.db = self.client[database_name]
            self.organizations = self.db["organizations"]
            self.organization_users = self.db["organization_users"]
            self.organization_invitations = self.db["organization_invitations"]

            # Create indexes
            try:
                # Organization indexes
                self.organizations.create_index("name", unique=True)
                self.organizations.create_index("is_active")

                # Organization users indexes
                self.organization_users.create_index("organization_id")
                self.organization_users.create_index("user_id")
                self.organization_users.create_index("email")
                self.organization_users.create_index([("organization_id", 1), ("user_id", 1)], unique=True)
                self.organization_users.create_index("is_active")

                # Organization invitations indexes
                self.organization_invitations.create_index("organization_id")
                self.organization_invitations.create_index("email")
                self.organization_invitations.create_index("invitation_token", unique=True)
                self.organization_invitations.create_index("status")
                self.organization_invitations.create_index("expires_at")

            except Exception as e:
                # Indexes might already exist
                pass

        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    # Organization CRUD Operations
    def _generate_org_name(self, display_name: str) -> str:
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

        while self.organizations.find_one({"name": name}):
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

    def create_organization(self, org_data: OrganizationCreate, creator_user_id: str, creator_email: str) -> Organization:
        """Create a new organization and add creator as owner.

        Args:
            org_data: Organization creation data.
            creator_user_id: User ID of the creator (from Supabase).
            creator_email: Email of the creator.

        Returns:
            Organization: The created organization.
        """
        # Auto-generate unique name from display_name if not provided
        org_name = org_data.name if org_data.name else self._generate_org_name(org_data.display_name)

        # Double-check uniqueness even if name was provided
        if org_data.name:
            existing = self.organizations.find_one({"name": org_name})
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
        result = self.organizations.insert_one(org.model_dump())

        # Add creator as owner
        org_user = OrganizationUser(
            organization_id=org.id,
            user_id=creator_user_id,
            email=creator_email,
            role=OrganizationRole.OWNER,
            display_name=creator_email.split("@")[0]  # Use email prefix as display name
        )

        self.organization_users.insert_one(org_user.model_dump())

        return org

    def get_organization(self, org_id: str) -> Optional[Organization]:
        """Get an organization by ID.

        Args:
            org_id: Organization ID.

        Returns:
            Organization: The organization if found, None otherwise.
        """
        doc = self.organizations.find_one({"id": org_id})
        return Organization(**doc) if doc else None

    def get_organizations_for_user(self, user_id: str) -> List[Organization]:
        """Get all organizations for a user.

        Args:
            user_id: User ID.

        Returns:
            List[Organization]: List of organizations the user belongs to.
        """
        # Check if user is a universal admin - if so, return all organizations
        if self.is_universal_admin(user_id):
            return self.get_all_organizations_for_universal_admin()

        # Get organization IDs where user is a member
        user_memberships = self.organization_users.find({
            "user_id": user_id,
            "is_active": True
        })

        org_ids = [membership["organization_id"] for membership in user_memberships if membership["organization_id"] != "*"]

        # Get organizations
        orgs = self.organizations.find({
            "id": {"$in": org_ids},
            "is_active": True
        })

        return [Organization(**doc) for doc in orgs]

    def get_user_organization_memberships(self, user_id: str, user_email: str = "") -> List[Dict]:
        """Get user's organization memberships with role and organization details.

        Args:
            user_id: User ID.
            user_email: User email.

        Returns:
            List[Dict]: List of membership dictionaries with organization details and role.
        """
        from bson import ObjectId

        # Get memberships from organization_memberships collection
        memberships = list(self.db["organization_memberships"].find({
            "$or": [
                {"user_id": user_id},
                {"email": user_email}
            ],
            "is_active": True
        }))

        result = []
        for mem in memberships:
            # Get organization details
            org_doc = self.organizations.find_one({"_id": mem["organization_id"]})
            if org_doc:
                # Convert ObjectId to string for JSON serialization
                mem_dict = {
                    "id": str(mem["_id"]),
                    "organization_id": mem["organization_id"],
                    "user_id": mem["user_id"],
                    "email": mem["email"],
                    "role": mem["role"],
                    "is_active": mem.get("is_active", True),
                    "joined_at": mem.get("joined_at", mem.get("created_at", "")),
                    "organization": Organization(**org_doc).model_dump()
                }
                result.append(mem_dict)

        return result

    def update_organization(self, org_id: str, update_data: OrganizationUpdate) -> Optional[Organization]:
        """Update an organization.

        Args:
            org_id: Organization ID.
            update_data: Update data.

        Returns:
            Organization: Updated organization if found, None otherwise.
        """
        # Prepare update data
        update_dict = {}
        for field, value in update_data.model_dump(exclude_unset=True).items():
            if value is not None:
                update_dict[field] = value

        if not update_dict:
            return self.get_organization(org_id)

        update_dict["updated_at"] = datetime.utcnow()

        # Update organization
        result = self.organizations.update_one(
            {"id": org_id},
            {"$set": update_dict}
        )

        if result.modified_count > 0:
            return self.get_organization(org_id)
        return None

    def delete_organization(self, org_id: str) -> bool:
        """Delete an organization (soft delete).

        Args:
            org_id: Organization ID.

        Returns:
            bool: True if deleted, False otherwise.
        """
        result = self.organizations.update_one(
            {"id": org_id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    # User Management
    def get_organization_users(self, org_id: str) -> List[OrganizationUser]:
        """Get all users in an organization.

        Args:
            org_id: Organization ID.

        Returns:
            List[OrganizationUser]: List of organization users.
        """
        users = self.organization_users.find({
            "organization_id": org_id,
            "is_active": True
        })
        return [OrganizationUser(**doc) for doc in users]

    def get_user_in_organization(self, org_id: str, user_id: str) -> Optional[OrganizationUser]:
        """Get a user's membership in an organization.

        Args:
            org_id: Organization ID.
            user_id: User ID.

        Returns:
            OrganizationUser: User membership if found, None otherwise.
        """
        doc = self.organization_users.find_one({
            "organization_id": org_id,
            "user_id": user_id,
            "is_active": True
        })
        return OrganizationUser(**doc) if doc else None

    def update_organization_user(self, org_id: str, user_id: str, update_data: OrganizationUserUpdate) -> Optional[OrganizationUser]:
        """Update a user's role/permissions in organization.

        Args:
            org_id: Organization ID.
            user_id: User ID.
            update_data: Update data.

        Returns:
            OrganizationUser: Updated user if found, None otherwise.
        """
        # Prepare update data
        update_dict = {}
        for field, value in update_data.model_dump(exclude_unset=True).items():
            if value is not None:
                update_dict[field] = value

        if not update_dict:
            return self.get_user_in_organization(org_id, user_id)

        update_dict["updated_at"] = datetime.utcnow()

        # Update user
        result = self.organization_users.update_one(
            {"organization_id": org_id, "user_id": user_id},
            {"$set": update_dict}
        )

        if result.modified_count > 0:
            return self.get_user_in_organization(org_id, user_id)
        return None

    def remove_user_from_organization(self, org_id: str, user_id: str) -> bool:
        """Remove a user from an organization.

        Args:
            org_id: Organization ID.
            user_id: User ID.

        Returns:
            bool: True if removed, False otherwise.
        """
        result = self.organization_users.update_one(
            {"organization_id": org_id, "user_id": user_id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def is_universal_admin(self, user_id: str, user_email: str = None) -> bool:
        """Check if a user is a universal admin.

        Args:
            user_id: User ID to check.
            user_email: Optional user email to check as fallback.

        Returns:
            bool: True if user is a universal admin, False otherwise.
        """
        # First check if user has is_universal_admin field set to True
        user_doc = self.db["users"].find_one({"_id": user_id})
        if user_doc and user_doc.get("is_universal_admin"):
            return True

        # Also check by email if provided
        if user_email:
            user_doc_by_email = self.db["users"].find_one({"email": user_email})
            if user_doc_by_email and user_doc_by_email.get("is_universal_admin"):
                return True

        # Check if user has universal admin role by user_id
        universal_admin = self.organization_users.find_one({
            "user_id": user_id,
            "role": OrganizationRole.UNIVERSAL_ADMIN,
            "is_active": True
        })

        if universal_admin is not None:
            return True

        # Fallback: check by email if provided (for users with multiple IDs)
        if user_email:
            universal_admin_by_email = self.organization_users.find_one({
                "email": user_email,
                "role": OrganizationRole.UNIVERSAL_ADMIN,
                "is_active": True
            })
            return universal_admin_by_email is not None

        return False

    def add_universal_admin(self, user_id: str, user_email: str) -> bool:
        """Add universal admin role to a user.

        Args:
            user_id: User ID.
            user_email: User email.

        Returns:
            bool: True if added successfully, False otherwise.
        """
        # Check if user already has active universal admin role
        if self.is_universal_admin(user_id, user_email):
            return True

        # Check if an inactive universal admin entry already exists
        existing_entry = self.organization_users.find_one({
            "user_id": user_id,
            "role": OrganizationRole.UNIVERSAL_ADMIN,
            "organization_id": "*"
        })

        if existing_entry:
            # Reactivate existing entry
            result = self.organization_users.update_one(
                {
                    "user_id": user_id,
                    "role": OrganizationRole.UNIVERSAL_ADMIN,
                    "organization_id": "*"
                },
                {
                    "$set": {
                        "is_active": True,
                        "email": user_email,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        else:
            # Create a new organization user entry for universal admin
            universal_admin_user = OrganizationUser(
                organization_id="*",  # Special org ID for universal admin
                user_id=user_id,
                email=user_email,
                role=OrganizationRole.UNIVERSAL_ADMIN,
                display_name=user_email.split("@")[0]
            )

            # Insert universal admin user
            try:
                self.organization_users.insert_one(universal_admin_user.model_dump())
                return True
            except Exception as e:
                print(f"Failed to add universal admin: {e}")
                return False

    def remove_universal_admin(self, user_id: str) -> bool:
        """Remove universal admin role from a user.

        Args:
            user_id: User ID.

        Returns:
            bool: True if removed successfully, False otherwise.
        """
        result = self.organization_users.update_one(
            {
                "user_id": user_id,
                "role": OrganizationRole.UNIVERSAL_ADMIN,
                "organization_id": "*"
            },
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def get_all_organizations_for_universal_admin(
        self,
        search: Optional[str] = None,
        industry: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 1000
    ) -> List[Organization]:
        """Get all organizations with advanced search for universal admin access.

        Args:
            search: Search query for name, display_name, or description
            industry: Filter by industry
            is_active: Filter by active status (None for all)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Organization]: List of organizations matching the filters
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
        else:
            # Default to active organizations if no filter specified
            filter_dict["is_active"] = True

        orgs = self.organizations.find(filter_dict).skip(skip).limit(limit).sort("display_name", 1)
        return [Organization(**doc) for doc in orgs]

    def check_user_permission(self, org_id: str, user_id: str, permission: str) -> bool:
        """Check if a user has a specific permission in an organization.

        Args:
            org_id: Organization ID.
            user_id: User ID.
            permission: Permission to check.

        Returns:
            bool: True if user has permission, False otherwise.
        """
        # First check if user is a universal admin
        if self.is_universal_admin(user_id):
            return True

        user = self.get_user_in_organization(org_id, user_id)
        if not user:
            return False

        # Check role-based permissions
        role_permissions = {
            OrganizationRole.UNIVERSAL_ADMIN: ["*"],  # All permissions across all organizations
            OrganizationRole.OWNER: ["*"],  # All permissions
            OrganizationRole.ADMIN: [
                "manage_users", "manage_settings", "manage_campaigns",
                "view_analytics", "manage_integrations"
            ],
            OrganizationRole.MANAGER: [
                "manage_campaigns", "view_analytics", "view_users"
            ],
            OrganizationRole.MEMBER: [
                "view_campaigns", "create_campaigns"
            ],
            OrganizationRole.VIEWER: [
                "view_campaigns", "view_analytics"
            ]
        }

        user_role_permissions = role_permissions.get(user.role, [])

        # Check if user has permission through role or specific permissions
        return (
            "*" in user_role_permissions or
            permission in user_role_permissions or
            user.permissions.get(permission, False)
        )

    # Invitation System
    def create_invitation(self, org_id: str, invite_data: OrganizationInviteRequest, inviter_user_id: str, inviter_email: str) -> OrganizationInvitation:
        """Create an invitation to join an organization.

        Args:
            org_id: Organization ID.
            invite_data: Invitation data.
            inviter_user_id: User ID of the inviter.
            inviter_email: Email of the inviter.

        Returns:
            OrganizationInvitation: The created invitation.
        """
        # Generate unique invitation token
        invitation_token = secrets.token_urlsafe(32)

        # Set expiry (7 days from now)
        expires_at = datetime.utcnow() + timedelta(days=7)

        invitation = OrganizationInvitation(
            organization_id=org_id,
            email=invite_data.email,
            role=invite_data.role,
            invited_by_user_id=inviter_user_id,
            invited_by_email=inviter_email,
            invitation_token=invitation_token,
            expires_at=expires_at
        )

        # Insert invitation
        self.organization_invitations.insert_one(invitation.model_dump())

        return invitation

    def get_invitation_by_token(self, token: str) -> Optional[OrganizationInvitation]:
        """Get an invitation by token.

        Args:
            token: Invitation token.

        Returns:
            OrganizationInvitation: Invitation if found, None otherwise.
        """
        doc = self.organization_invitations.find_one({"invitation_token": token})
        return OrganizationInvitation(**doc) if doc else None

    def get_organization_invitations(self, org_id: str) -> List[OrganizationInvitation]:
        """Get all invitations for an organization.

        Args:
            org_id: Organization ID.

        Returns:
            List[OrganizationInvitation]: List of invitations.
        """
        invitations = self.organization_invitations.find({"organization_id": org_id})
        return [OrganizationInvitation(**doc) for doc in invitations]

    def accept_invitation(self, token: str, user_id: str, user_email: str) -> Optional[OrganizationUser]:
        """Accept an invitation and add user to organization.

        Args:
            token: Invitation token.
            user_id: User ID accepting the invitation.
            user_email: User email.

        Returns:
            OrganizationUser: Created organization user if successful, None otherwise.
        """
        # Get invitation
        invitation = self.get_invitation_by_token(token)
        if not invitation or invitation.status != InvitationStatus.PENDING:
            return None

        # Check if invitation is expired
        if invitation.expires_at < datetime.utcnow():
            # Mark as expired
            self.organization_invitations.update_one(
                {"invitation_token": token},
                {"$set": {"status": InvitationStatus.EXPIRED, "updated_at": datetime.utcnow()}}
            )
            return None

        # Check if email matches
        if invitation.email.lower() != user_email.lower():
            return None

        # Check if user is already in organization
        existing_user = self.get_user_in_organization(invitation.organization_id, user_id)
        if existing_user:
            return None

        # Create organization user
        org_user = OrganizationUser(
            organization_id=invitation.organization_id,
            user_id=user_id,
            email=user_email,
            role=invitation.role,
            display_name=user_email.split("@")[0]
        )

        # Insert organization user
        self.organization_users.insert_one(org_user.model_dump())

        # Mark invitation as accepted
        self.organization_invitations.update_one(
            {"invitation_token": token},
            {
                "$set": {
                    "status": InvitationStatus.ACCEPTED,
                    "responded_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return org_user

    def decline_invitation(self, token: str, message: str = "") -> bool:
        """Decline an invitation.

        Args:
            token: Invitation token.
            message: Optional decline message.

        Returns:
            bool: True if declined successfully, False otherwise.
        """
        result = self.organization_invitations.update_one(
            {
                "invitation_token": token,
                "status": InvitationStatus.PENDING
            },
            {
                "$set": {
                    "status": InvitationStatus.DECLINED,
                    "responded_at": datetime.utcnow(),
                    "response_message": message,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0

    def cancel_invitation(self, invitation_id: str) -> bool:
        """Cancel a pending invitation.

        Args:
            invitation_id: Invitation ID.

        Returns:
            bool: True if cancelled, False otherwise.
        """
        result = self.organization_invitations.delete_one({
            "id": invitation_id,
            "status": InvitationStatus.PENDING
        })
        return result.deleted_count > 0

    # Style Settings
    def update_organization_style_settings(self, org_id: str, style_settings: Dict[str, Any]) -> Optional[Organization]:
        """Update organization style settings.

        Args:
            org_id: Organization ID.
            style_settings: Style settings to update.

        Returns:
            Organization: Updated organization if successful, None otherwise.
        """
        result = self.organizations.update_one(
            {"id": org_id},
            {
                "$set": {
                    "style_settings": style_settings,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:
            return self.get_organization(org_id)
        return None


# Global service instance
organization_service = MongoDBOrganizationService()