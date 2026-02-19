"""
Member Migration Service.

One-time migration service to convert existing conference registrants
to member/visitor profiles based on branch_id vs church_name.
"""

from datetime import datetime
from typing import Dict, Optional
from bson import ObjectId
import logging

from app.core.database import get_database
from app.models.user import User

logger = logging.getLogger(__name__)


class MemberMigrationService:
    """Service for migrating conference registrants to member/visitor profiles."""

    def __init__(self):
        """Initialize migration service."""
        self.db = None

    def _get_db(self):
        """Get database instance (lazy initialization)."""
        if self.db is None:
            self.db = get_database()
        return self.db

    async def migrate_conference_registrants_to_profiles(
        self,
        dry_run: bool = False
    ) -> Dict:
        """
        Migrate existing conference registrants to member/visitor profiles.

        Logic:
        1. Query all conference_registrations
        2. For each registration:
           a. Check if User already exists (by phone or email)
           b. If registration.branch_id exists and is ObjectId:
              - Create/update User with member_status="active_member"
              - Set branch_id = registration.branch_id
           c. Else if registration.church_name exists:
              - Create/update User with member_status="visitor"
              - Store church_name in metadata or custom field
           d. Copy fields: name, phone, email, emergency_contact
           e. Set first_visit_date = registration.created_at
           f. Set visit_count = 1 (or increment if exists)
        3. Return migration stats: members_created, visitors_created, duplicates_merged

        Args:
            dry_run: If True, only simulate migration without writing to database

        Returns:
            dict: Migration statistics
        """
        logger.info(f"Starting conference registrant migration (dry_run={dry_run})...")

        stats = {
            "total_registrations": 0,
            "members_created": 0,
            "members_updated": 0,
            "visitors_created": 0,
            "visitors_updated": 0,
            "placeholder_phones": 0,
            "errors": 0,
            "error_details": []
        }

        try:
            db = self._get_db()

            # Query all conference registrations
            registrations_cursor = db.conference_registrations.find({
                "status": {"$ne": "cancelled"}
            })

            registrations = await registrations_cursor.to_list(length=None)
            stats["total_registrations"] = len(registrations)

            logger.info(f"Found {stats['total_registrations']} registrations to process")

            for registration in registrations:
                try:
                    await self._process_registration(registration, stats, dry_run)
                except Exception as e:
                    stats["errors"] += 1
                    error_msg = f"Error processing registration {registration.get('_id')}: {str(e)}"
                    logger.error(error_msg)
                    stats["error_details"].append(error_msg)
                    continue

            logger.info(f"Migration completed. Stats: {stats}")

            return stats

        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            raise

    async def _process_registration(
        self,
        registration: Dict,
        stats: Dict,
        dry_run: bool
    ) -> None:
        """
        Process a single conference registration.

        Args:
            registration: Registration document
            stats: Statistics dictionary to update
            dry_run: Whether this is a dry run
        """
        # Extract registration data
        user_phone = registration.get("user_phone")
        user_name = registration.get("user_name")
        user_email = registration.get("user_email")
        branch_id = registration.get("branch_id")
        church_name = registration.get("church_name")
        emergency_contact = registration.get("emergency_contact")
        created_at = registration.get("created_at")
        organization_id = registration.get("organization_id")
        registration_id = registration.get("_id")

        # Handle missing phone - use placeholder
        if not user_phone:
            # Generate placeholder phone from registration ID
            phone = f"+233999{str(registration_id)[-7:]}"  # Use last 7 chars of registration ID
            stats["placeholder_phones"] += 1
            logger.debug(f"No phone for registration {registration_id} - using placeholder: {phone}")
        else:
            # Normalize phone number (already in +233 format in the DB)
            phone = user_phone.strip()

        # Determine if this is a member or visitor
        # Default to visitor if no branch_id or church_name specified
        is_member = branch_id is not None and isinstance(branch_id, ObjectId)

        # If no branch_id, treat as visitor (even if no church_name)
        is_visitor = not is_member

        # Check if user already exists
        db = self._get_db()
        existing_user = await db.users.find_one({
            "$or": [
                {"phone": phone},
                {"email": user_email} if user_email else {}
            ]
        })

        if existing_user:
            # Update existing user
            await self._update_existing_user(
                existing_user,
                registration,
                is_member,
                stats,
                dry_run
            )
        else:
            # Create new user profile
            await self._create_new_user(
                phone,
                user_name,
                user_email,
                branch_id,
                church_name,
                emergency_contact,
                created_at,
                organization_id,
                is_member,
                stats,
                dry_run
            )

    async def _update_existing_user(
        self,
        existing_user: Dict,
        registration: Dict,
        is_member: bool,
        stats: Dict,
        dry_run: bool
    ) -> None:
        """
        Update an existing user profile with registration data.

        Args:
            existing_user: Existing user document
            registration: Registration document
            is_member: Whether this is a member (vs visitor)
            stats: Statistics dictionary to update
            dry_run: Whether this is a dry run
        """
        update_fields = {}

        # Update member status if not already set
        current_status = existing_user.get("member_status")
        if not current_status or current_status == "visitor":
            if is_member:
                update_fields["member_status"] = "active_member"
                if registration.get("branch_id"):
                    update_fields["branch_id"] = registration["branch_id"]
            else:
                update_fields["member_status"] = "visitor"
                if registration.get("church_name") and not existing_user.get("church_name"):
                    update_fields["church_name"] = registration["church_name"]

        # Update organization_id if not set
        if not existing_user.get("organization_id") and registration.get("organization_id"):
            update_fields["organization_id"] = registration["organization_id"]

        # Update first_visit_date if not set
        if not existing_user.get("first_visit_date") and registration.get("created_at"):
            update_fields["first_visit_date"] = registration["created_at"]

        # Increment visit_count
        current_count = existing_user.get("visit_count", 0)
        update_fields["visit_count"] = current_count + 1

        # Update emergency contact if not set
        if not existing_user.get("emergency_contact_phone") and registration.get("emergency_contact"):
            update_fields["emergency_contact_phone"] = registration["emergency_contact"]

        # Update name if not set
        if not existing_user.get("full_name") and registration.get("user_name"):
            update_fields["full_name"] = registration["user_name"]
            update_fields["name"] = registration["user_name"]  # Legacy field

        # Update email if not set
        if not existing_user.get("email") and registration.get("user_email"):
            update_fields["email"] = registration["user_email"]

        # Only update if there are changes
        if update_fields:
            update_fields["updated_at"] = datetime.utcnow()

            if not dry_run:
                db = self._get_db()
                await db.users.update_one(
                    {"_id": existing_user["_id"]},
                    {"$set": update_fields}
                )

            if is_member:
                stats["members_updated"] += 1
            else:
                stats["visitors_updated"] += 1

            logger.debug(
                f"Updated user {existing_user['_id']} "
                f"({'member' if is_member else 'visitor'}) "
                f"with fields: {list(update_fields.keys())}"
            )

    async def _create_new_user(
        self,
        phone: str,
        user_name: Optional[str],
        user_email: Optional[str],
        branch_id: Optional[ObjectId],
        church_name: Optional[str],
        emergency_contact: Optional[str],
        created_at: Optional[datetime],
        organization_id: Optional[str],
        is_member: bool,
        stats: Dict,
        dry_run: bool
    ) -> None:
        """
        Create a new user profile from registration data.

        Args:
            phone: User phone number
            user_name: User name
            user_email: User email
            branch_id: Branch ObjectId (for members)
            church_name: Church name (for visitors)
            emergency_contact: Emergency contact phone
            created_at: Registration creation timestamp
            organization_id: Organization ID
            is_member: Whether this is a member (vs visitor)
            stats: Statistics dictionary to update
            dry_run: Whether this is a dry run
        """
        user_data = {
            "phone": phone,
            "name": user_name,
            "full_name": user_name,
            "email": user_email,
            "member_status": "active_member" if is_member else "visitor",
            "current_spiritual_stage": "first_timer",
            "branch_id": branch_id if is_member else None,
            "church_name": church_name if not is_member else None,
            "organization_id": organization_id,
            "first_visit_date": created_at or datetime.utcnow(),
            "visit_count": 1,
            "last_visit_date": created_at or datetime.utcnow(),
            "emergency_contact_phone": emergency_contact,
            "roles": ["member"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_active": datetime.utcnow()
        }

        if not dry_run:
            # Create user using User model validation
            try:
                db = self._get_db()
                user = User(**user_data)
                user_dict = user.model_dump(by_alias=True, exclude_none=True)

                # Remove _id if None
                if user_dict.get("_id") is None:
                    user_dict.pop("_id", None)

                result = await db.users.insert_one(user_dict)

                logger.debug(
                    f"Created new user {result.inserted_id} "
                    f"({'member' if is_member else 'visitor'}) "
                    f"from registration (phone: {phone})"
                )

            except Exception as e:
                logger.error(f"Failed to create user for phone {phone}: {str(e)}")
                raise

        if is_member:
            stats["members_created"] += 1
        else:
            stats["visitors_created"] += 1

    async def get_migration_preview(self) -> Dict:
        """
        Get a preview of what the migration would do without making changes.

        Returns:
            dict: Preview statistics showing what would be migrated
        """
        return await self.migrate_conference_registrants_to_profiles(dry_run=True)


# Singleton instance
member_migration_service = MemberMigrationService()
