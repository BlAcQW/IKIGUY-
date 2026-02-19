"""
Organization Invitation Service for ChurchFlow.

Handles invitation workflow for adding users to organizations.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from bson import ObjectId

from app.models.invitation import Invitation, InvitationCreate, InvitationAccept
from app.core.database import get_database

logger = logging.getLogger(__name__)


class InvitationService:
    """Service for managing organization invitations."""

    def __init__(self):
        self.db = None
        self.collection = None

    def _ensure_db(self):
        """Ensure database connection is established."""
        if self.db is None:
            self.db = get_database()
            self.collection = self.db.organization_invitations
        return self.collection

    async def initialize_indexes(self):
        """Create database indexes for invitations."""
        collection = self._ensure_db()
        await collection.create_index("organization_id")
        await collection.create_index("email")
        await collection.create_index("token", unique=True)
        await collection.create_index("status")
        await collection.create_index([("organization_id", 1), ("status", 1)])
        await collection.create_index("expires_at")
        logger.info("✅ Invitation indexes initialized")

    async def create_invitation(
        self,
        organization_id: str,
        email: str,
        role: str,
        invited_by: str,
        invited_by_email: str,
        display_name: Optional[str] = None,
        message: Optional[str] = None
    ) -> Invitation:
        """
        Create a new organization invitation.

        Args:
            organization_id: Organization ID
            email: Invitee email address
            role: Role to assign (admin or user)
            invited_by: User ID of inviter
            invited_by_email: Email of inviter
            display_name: Optional display name for invitee
            message: Optional custom message

        Returns:
            Created invitation

        Raises:
            ValueError: If invitation already exists or email is invalid
        """
        collection = self._ensure_db()

        # Check if invitation already exists
        existing = await collection.find_one({
            "organization_id": organization_id,
            "email": email,
            "status": "pending"
        })

        if existing:
            raise ValueError(f"Pending invitation already exists for {email}")

        # Create invitation
        invitation_data = {
            "organization_id": organization_id,
            "email": email,
            "role": role,
            "status": "pending",
            "invited_by": invited_by,
            "invited_by_email": invited_by_email,
            "display_name": display_name,
            "message": message,
            "invited_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7)
        }

        invitation = Invitation(**invitation_data)
        result = await collection.insert_one(invitation.model_dump(by_alias=True, exclude={"id"}))

        invitation.id = result.inserted_id
        logger.info(f"Created invitation {invitation.id} for {email} to organization {organization_id}")

        return invitation

    async def get_invitation_by_token(self, token: str) -> Optional[Invitation]:
        """
        Get invitation by token.

        Args:
            token: Invitation token

        Returns:
            Invitation if found, None otherwise
        """
        collection = self._ensure_db()
        doc = await collection.find_one({"token": token})
        return Invitation(**doc) if doc else None

    async def get_invitation_by_id(self, invitation_id: str) -> Optional[Invitation]:
        """
        Get invitation by ID.

        Args:
            invitation_id: Invitation ID

        Returns:
            Invitation if found, None otherwise
        """
        collection = self._ensure_db()

        if not ObjectId.is_valid(invitation_id):
            return None

        doc = await collection.find_one({"_id": ObjectId(invitation_id)})
        return Invitation(**doc) if doc else None

    async def list_invitations(
        self,
        organization_id: str,
        status: Optional[str] = "pending"
    ) -> List[Invitation]:
        """
        List invitations for an organization.

        Args:
            organization_id: Organization ID
            status: Filter by status (pending, accepted, cancelled, expired)

        Returns:
            List of invitations
        """
        collection = self._ensure_db()

        query = {"organization_id": organization_id}
        if status:
            query["status"] = status

        cursor = collection.find(query).sort("invited_at", -1)
        invitations = []

        async for doc in cursor:
            invitations.append(Invitation(**doc))

        return invitations

    async def accept_invitation(
        self,
        token: str,
        user_id: str,
        display_name: str
    ) -> Optional[Invitation]:
        """
        Accept an invitation.

        Args:
            token: Invitation token
            user_id: User ID accepting the invitation
            display_name: Display name of user

        Returns:
            Updated invitation if successful, None otherwise

        Raises:
            ValueError: If invitation is invalid or expired
        """
        collection = self._ensure_db()
        invitation = await self.get_invitation_by_token(token)

        if not invitation:
            raise ValueError("Invitation not found")

        if invitation.status != "pending":
            raise ValueError(f"Invitation is {invitation.status}, cannot accept")

        if invitation.expires_at < datetime.utcnow():
            # Mark as expired
            await collection.update_one(
                {"_id": invitation.id},
                {"$set": {"status": "expired"}}
            )
            raise ValueError("Invitation has expired")

        # Update invitation
        result = await collection.update_one(
            {"_id": invitation.id},
            {
                "$set": {
                    "status": "accepted",
                    "accepted_at": datetime.utcnow(),
                    "accepted_by": user_id
                }
            }
        )

        if result.modified_count == 0:
            return None

        logger.info(f"Invitation {invitation.id} accepted by user {user_id}")

        # Return updated invitation
        return await self.get_invitation_by_id(str(invitation.id))

    async def cancel_invitation(self, invitation_id: str) -> bool:
        """
        Cancel a pending invitation.

        Args:
            invitation_id: Invitation ID

        Returns:
            True if cancelled, False otherwise
        """
        collection = self._ensure_db()

        if not ObjectId.is_valid(invitation_id):
            return False

        result = await collection.update_one(
            {"_id": ObjectId(invitation_id), "status": "pending"},
            {"$set": {"status": "cancelled"}}
        )

        if result.modified_count > 0:
            logger.info(f"Invitation {invitation_id} cancelled")
            return True

        return False

    async def expire_old_invitations(self):
        """
        Mark expired invitations as expired.

        Should be run periodically (e.g., daily cron job).

        Returns:
            Number of invitations expired
        """
        collection = self._ensure_db()

        result = await collection.update_many(
            {
                "status": "pending",
                "expires_at": {"$lt": datetime.utcnow()}
            },
            {"$set": {"status": "expired"}}
        )

        count = result.modified_count
        if count > 0:
            logger.info(f"Expired {count} old invitations")

        return count


def get_invitation_service() -> InvitationService:
    """
    Get invitation service instance.

    Returns:
        InvitationService instance
    """
    return InvitationService()
