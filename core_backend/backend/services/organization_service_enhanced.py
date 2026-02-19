"""Enhanced MongoDB-based organization service with comprehensive error handling."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import logging

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, ConnectionFailure

from ..models import (
    Organization, OrganizationCreate, OrganizationUpdate,
    OrganizationUser, OrganizationUserUpdate, OrganizationRole,
    OrganizationInvitation, OrganizationInviteRequest
)
from ..utils.error_handling import (
    handle_organization_errors, handle_database_errors, OrganizationError,
    DatabaseError, ValidationError, ErrorCode, ValidationHelper, ErrorRecovery
)
from ..database import get_mongo_connection

logger = logging.getLogger(__name__)


class EnhancedOrganizationService:
    """Enhanced MongoDB-based organization service with comprehensive error handling."""

    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.organizations: Optional[Collection] = None
        self.organization_users: Optional[Collection] = None
        self.organization_invitations: Optional[Collection] = None
        self._connect()

    @handle_database_errors
    def _connect(self):
        """Connect to MongoDB with enhanced error handling."""
        try:
            mongo_config = get_mongo_connection()
            self.client = MongoClient(
                mongo_config["url"],
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                retryWrites=True
            )

            # Test connection
            self.client.admin.command('ping')

            db = self.client[mongo_config["database"]]
            self.organizations = db.organizations
            self.organization_users = db.organization_users
            self.organization_invitations = db.organization_invitations

            # Create indexes with error handling
            self._create_indexes()

            logger.info("Successfully connected to MongoDB for organization service")

        except ConnectionFailure as e:
            raise DatabaseError(
                message="Failed to connect to MongoDB",
                error_code=ErrorCode.DB_CONNECTION_ERROR,
                status_code=503,
                original_error=e
            )
        except Exception as e:
            raise DatabaseError(
                message="Database initialization failed",
                error_code=ErrorCode.DB_OPERATION_FAILED,
                status_code=500,
                original_error=e
            )

    def _create_indexes(self):
        """Create database indexes with error handling."""
        try:
            # Organization indexes
            self.organizations.create_index("id", unique=True)
            self.organizations.create_index("name")
            self.organizations.create_index("is_active")
            self.organizations.create_index("created_at")

            # Organization users indexes
            self.organization_users.create_index("organization_id")
            self.organization_users.create_index("user_id")
            self.organization_users.create_index("email")
            self.organization_users.create_index([("organization_id", 1), ("user_id", 1)], unique=True)
            self.organization_users.create_index("is_active")
            self.organization_users.create_index("role")

            # Organization invitations indexes
            self.organization_invitations.create_index("organization_id")
            self.organization_invitations.create_index("email")
            self.organization_invitations.create_index("invitation_token", unique=True)
            self.organization_invitations.create_index("status")
            self.organization_invitations.create_index("expires_at")

        except Exception as e:
            logger.warning(f"Some indexes might already exist: {e}")

    @handle_organization_errors
    @handle_database_errors
    def create_organization(
        self,
        org_data: OrganizationCreate,
        creator_user_id: str,
        creator_email: str
    ) -> Organization:
        """
        Create a new organization with enhanced validation and error handling.

        Args:
            org_data: Organization creation data
            creator_user_id: User ID of the creator
            creator_email: Email of the creator

        Returns:
            Organization: The created organization

        Raises:
            OrganizationError: If organization creation fails
            ValidationError: If data validation fails
        """
        try:
            # Enhanced validation
            ValidationHelper.validate_organization_name(org_data.name)
            ValidationHelper.validate_email(creator_email)

            # Check if organization name already exists
            existing_org = self.organizations.find_one({
                "name": {"$regex": f"^{org_data.name}$", "$options": "i"},
                "is_active": True
            })

            if existing_org:
                raise OrganizationError(
                    message=f"Organization with name '{org_data.name}' already exists",
                    error_code=ErrorCode.ORG_ALREADY_EXISTS,
                    status_code=409,
                    details={"organization_name": org_data.name}
                )

            # Create organization
            organization = Organization(
                name=org_data.name.strip(),
                display_name=org_data.display_name or org_data.name.strip(),
                description=org_data.description or "",
                industry=org_data.industry or "",
                website=org_data.website or "",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                is_active=True
            )

            # Insert organization with error handling
            try:
                result = self.organizations.insert_one(organization.model_dump())
                if not result.inserted_id:
                    raise OrganizationError(
                        message="Failed to create organization",
                        error_code=ErrorCode.DB_OPERATION_FAILED,
                        status_code=500
                    )
            except DuplicateKeyError:
                raise OrganizationError(
                    message="Organization already exists",
                    error_code=ErrorCode.ORG_ALREADY_EXISTS,
                    status_code=409
                )

            # Add creator as owner
            org_user = OrganizationUser(
                organization_id=organization.id,
                user_id=creator_user_id,
                email=creator_email,
                role=OrganizationRole.OWNER,
                display_name=creator_email.split("@")[0],
                is_active=True,
                joined_at=datetime.now(timezone.utc),
                permissions={}  # Default permissions
            )

            try:
                self.organization_users.insert_one(org_user.model_dump())
            except Exception as e:
                # Rollback organization creation
                self.organizations.delete_one({"id": organization.id})
                raise OrganizationError(
                    message="Failed to assign owner role",
                    error_code=ErrorCode.DB_OPERATION_FAILED,
                    status_code=500,
                    original_error=e
                )

            logger.info(f"Organization '{organization.name}' created successfully by {creator_email}")
            return organization

        except (OrganizationError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating organization: {str(e)}")
            raise OrganizationError(
                message="Organization creation failed due to an internal error",
                error_code=ErrorCode.INTERNAL_ERROR,
                status_code=500,
                original_error=e
            )

    @handle_organization_errors
    @handle_database_errors
    def get_organization(self, org_id: str) -> Optional[Organization]:
        """
        Get an organization by ID with enhanced error handling.

        Args:
            org_id: Organization ID

        Returns:
            Organization: The organization if found, None otherwise

        Raises:
            OrganizationError: If operation fails
        """
        try:
            if not org_id or not isinstance(org_id, str):
                raise ValidationError(
                    message="Valid organization ID is required",
                    error_code=ErrorCode.VALIDATION_FAILED,
                    status_code=400
                )

            doc = self.organizations.find_one({
                "id": org_id,
                "is_active": True
            })

            return Organization(**doc) if doc else None

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving organization {org_id}: {str(e)}")
            raise OrganizationError(
                message="Failed to retrieve organization",
                error_code=ErrorCode.DB_OPERATION_FAILED,
                status_code=500,
                original_error=e
            )

    @handle_organization_errors
    @handle_database_errors
    def get_organizations_for_user(self, user_id: str) -> List[Organization]:
        """
        Get all organizations for a user with enhanced error handling.

        Args:
            user_id: User ID

        Returns:
            List[Organization]: List of organizations the user belongs to

        Raises:
            OrganizationError: If operation fails
        """
        try:
            if not user_id or not isinstance(user_id, str):
                raise ValidationError(
                    message="Valid user ID is required",
                    error_code=ErrorCode.VALIDATION_FAILED,
                    status_code=400
                )

            # Check if user is a universal admin
            if self.is_universal_admin(user_id):
                return self.get_all_organizations_for_universal_admin()

            # Get organization IDs where user is a member
            user_memberships = list(self.organization_users.find({
                "user_id": user_id,
                "is_active": True
            }))

            if not user_memberships:
                return []

            org_ids = [
                membership["organization_id"]
                for membership in user_memberships
                if membership["organization_id"] != "*"  # Exclude universal admin marker
            ]

            if not org_ids:
                return []

            # Get organizations
            orgs = list(self.organizations.find({
                "id": {"$in": org_ids},
                "is_active": True
            }))

            return [Organization(**doc) for doc in orgs]

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving organizations for user {user_id}: {str(e)}")
            raise OrganizationError(
                message="Failed to retrieve user organizations",
                error_code=ErrorCode.DB_OPERATION_FAILED,
                status_code=500,
                original_error=e
            )

    @handle_organization_errors
    @handle_database_errors
    def update_organization(
        self,
        org_id: str,
        update_data: OrganizationUpdate
    ) -> Optional[Organization]:
        """
        Update an organization with enhanced validation and error handling.

        Args:
            org_id: Organization ID
            update_data: Update data

        Returns:
            Organization: Updated organization if found, None otherwise

        Raises:
            OrganizationError: If update fails
        """
        try:
            if not org_id or not isinstance(org_id, str):
                raise ValidationError(
                    message="Valid organization ID is required",
                    error_code=ErrorCode.VALIDATION_FAILED,
                    status_code=400
                )

            # Validate update data
            update_dict = {}
            for field, value in update_data.model_dump(exclude_unset=True).items():
                if value is not None:
                    # Validate specific fields
                    if field == "name" and value:
                        ValidationHelper.validate_organization_name(value)
                        # Check for name conflicts
                        existing_org = self.organizations.find_one({
                            "name": {"$regex": f"^{value}$", "$options": "i"},
                            "id": {"$ne": org_id},
                            "is_active": True
                        })
                        if existing_org:
                            raise OrganizationError(
                                message=f"Organization name '{value}' is already taken",
                                error_code=ErrorCode.ORG_ALREADY_EXISTS,
                                status_code=409
                            )

                    update_dict[field] = value

            if not update_dict:
                return self.get_organization(org_id)

            update_dict["updated_at"] = datetime.now(timezone.utc)

            # Update organization
            result = self.organizations.update_one(
                {"id": org_id, "is_active": True},
                {"$set": update_dict}
            )

            if result.matched_count == 0:
                raise OrganizationError(
                    message="Organization not found",
                    error_code=ErrorCode.ORG_NOT_FOUND,
                    status_code=404
                )

            if result.modified_count > 0:
                logger.info(f"Organization {org_id} updated successfully")
                return self.get_organization(org_id)

            return self.get_organization(org_id)

        except (OrganizationError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error updating organization {org_id}: {str(e)}")
            raise OrganizationError(
                message="Organization update failed",
                error_code=ErrorCode.DB_OPERATION_FAILED,
                status_code=500,
                original_error=e
            )

    @handle_organization_errors
    @handle_database_errors
    def delete_organization(self, org_id: str, deleting_user_id: str) -> bool:
        """
        Delete an organization (soft delete) with enhanced validation.

        Args:
            org_id: Organization ID
            deleting_user_id: ID of user performing deletion

        Returns:
            bool: True if deleted, False otherwise

        Raises:
            OrganizationError: If deletion fails or user lacks permission
        """
        try:
            if not org_id or not deleting_user_id:
                raise ValidationError(
                    message="Organization ID and user ID are required",
                    error_code=ErrorCode.VALIDATION_FAILED,
                    status_code=400
                )

            # Check if user has permission to delete (must be owner or universal admin)
            if not self.is_universal_admin(deleting_user_id):
                user_membership = self.get_user_in_organization(org_id, deleting_user_id)
                if not user_membership or user_membership.role != OrganizationRole.OWNER:
                    raise OrganizationError(
                        message="Only organization owners can delete organizations",
                        error_code=ErrorCode.ORG_ACCESS_DENIED,
                        status_code=403
                    )

            # Check if this is the last active organization for any users
            active_members = list(self.organization_users.find({
                "organization_id": org_id,
                "is_active": True
            }))

            for member in active_members:
                user_org_count = self.organization_users.count_documents({
                    "user_id": member["user_id"],
                    "is_active": True,
                    "organization_id": {"$ne": "*"}  # Exclude universal admin
                })

                if user_org_count <= 1:
                    raise OrganizationError(
                        message="Cannot delete organization as it would leave some users without any organization",
                        error_code=ErrorCode.ORG_CANNOT_DELETE_LAST_OWNER,
                        status_code=409,
                        details={"affected_users": [member["email"]]}
                    )

            # Soft delete organization
            result = self.organizations.update_one(
                {"id": org_id, "is_active": True},
                {
                    "$set": {
                        "is_active": False,
                        "deleted_at": datetime.now(timezone.utc),
                        "deleted_by": deleting_user_id,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.modified_count > 0:
                # Deactivate all memberships
                self.organization_users.update_many(
                    {"organization_id": org_id},
                    {
                        "$set": {
                            "is_active": False,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )

                # Cancel pending invitations
                self.organization_invitations.update_many(
                    {"organization_id": org_id, "status": "pending"},
                    {
                        "$set": {
                            "status": "cancelled",
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )

                logger.info(f"Organization {org_id} deleted successfully by user {deleting_user_id}")
                return True

            return False

        except (OrganizationError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error deleting organization {org_id}: {str(e)}")
            raise OrganizationError(
                message="Organization deletion failed",
                error_code=ErrorCode.DB_OPERATION_FAILED,
                status_code=500,
                original_error=e
            )

    @handle_organization_errors
    @handle_database_errors
    def check_user_permission(self, org_id: str, user_id: str, permission: str) -> bool:
        """
        Check if a user has a specific permission in an organization with enhanced validation.

        Args:
            org_id: Organization ID
            user_id: User ID
            permission: Permission to check

        Returns:
            bool: True if user has permission, False otherwise
        """
        try:
            if not all([org_id, user_id, permission]):
                return False

            # First check if user is a universal admin
            if self.is_universal_admin(user_id):
                return True

            user = self.get_user_in_organization(org_id, user_id)
            if not user or not user.is_active:
                return False

            # Enhanced role-based permissions
            role_permissions = {
                OrganizationRole.UNIVERSAL_ADMIN: ["*"],  # All permissions across all organizations
                OrganizationRole.OWNER: ["*"],  # All permissions
                OrganizationRole.ADMIN: [
                    "manage_users", "manage_settings", "manage_campaigns",
                    "view_analytics", "manage_integrations", "manage_billing",
                    "view_users", "create_campaigns", "view_campaigns"
                ],
                OrganizationRole.MANAGER: [
                    "manage_campaigns", "view_analytics", "view_users",
                    "create_campaigns", "view_campaigns"
                ],
                OrganizationRole.MEMBER: [
                    "view_campaigns", "create_campaigns", "view_basic_analytics"
                ],
                OrganizationRole.VIEWER: [
                    "view_campaigns", "view_basic_analytics"
                ]
            }

            user_role_permissions = role_permissions.get(user.role, [])

            # Check if user has permission through role or specific permissions
            has_permission = (
                "*" in user_role_permissions or
                permission in user_role_permissions or
                user.permissions.get(permission, False)
            )

            return has_permission

        except Exception as e:
            logger.error(f"Error checking permission {permission} for user {user_id} in org {org_id}: {str(e)}")
            return False

    @handle_organization_errors
    def is_universal_admin(self, user_id: str) -> bool:
        """
        Check if a user is a universal admin with enhanced validation.

        Args:
            user_id: User ID

        Returns:
            bool: True if user is universal admin, False otherwise
        """
        try:
            if not user_id:
                return False

            admin_doc = self.organization_users.find_one({
                "user_id": user_id,
                "role": OrganizationRole.UNIVERSAL_ADMIN,
                "organization_id": "*",
                "is_active": True
            })

            return admin_doc is not None

        except Exception as e:
            logger.error(f"Error checking universal admin status for user {user_id}: {str(e)}")
            return False

    def get_user_in_organization(self, org_id: str, user_id: str) -> Optional[OrganizationUser]:
        """Get a user's membership in an organization."""
        try:
            doc = self.organization_users.find_one({
                "organization_id": org_id,
                "user_id": user_id,
                "is_active": True
            })
            return OrganizationUser(**doc) if doc else None
        except Exception as e:
            logger.error(f"Error getting user {user_id} in organization {org_id}: {str(e)}")
            return None

    def get_all_organizations_for_universal_admin(self) -> List[Organization]:
        """Get all active organizations for universal admin access."""
        try:
            orgs = list(self.organizations.find({"is_active": True}))
            return [Organization(**doc) for doc in orgs]
        except Exception as e:
            logger.error(f"Error getting all organizations for universal admin: {str(e)}")
            return []


# Create global instance
organization_service_enhanced = EnhancedOrganizationService()