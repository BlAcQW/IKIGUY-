"""
User management service for DevotionalFlow.

Handles platform invitations and user CRUD operations.
Provides business logic for invite creation, verification, and user management.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import HTTPException, status
import secrets
import logging

from app.db.mongodb import get_database
from app.models.platform_invite import (
    PlatformInviteCreate,
    PlatformInviteInDB,
    PlatformInviteResponse,
    PlatformInviteListResponse,
    PlatformInviteVerifyResponse,
    PlatformInviteStats,
)
from app.models.user import UserStatsResponse
from app.services.platform_email_service import send_invite_email

logger = logging.getLogger(__name__)

# Constants
INVITE_EXPIRY_DAYS = 7
PLATFORM_INVITES_COLLECTION = "platform_invites"


class UserManagementService:
    """
    Service for managing platform users and invitations.

    Provides methods for:
    - Creating and managing platform invitations
    - Verifying invitation tokens
    - User CRUD operations (extending AdminService)
    """

    def __init__(self):
        """Initialize the service with database connection."""
        self.db = get_database()
        self.invites_collection = self.db[PLATFORM_INVITES_COLLECTION]
        self.users_collection = self.db.users

    async def initialize_indexes(self) -> None:
        """
        Create database indexes for platform invitations.

        Should be called during application startup.
        """
        try:
            await self.invites_collection.create_index("email")
            await self.invites_collection.create_index("token", unique=True)
            await self.invites_collection.create_index("status")
            await self.invites_collection.create_index("invited_by_id")
            await self.invites_collection.create_index("expires_at")
            await self.invites_collection.create_index(
                [("email", 1), ("status", 1)]
            )
            logger.info("Platform invite indexes initialized successfully")
        except Exception as e:
            logger.error(f"Failed to create platform invite indexes: {e}")

    # ============ Invitation CRUD ============

    async def create_invite(
        self,
        invite_data: PlatformInviteCreate,
        invited_by_id: str,
        invited_by_name: str,
        invited_by_email: str
    ) -> PlatformInviteResponse:
        """
        Create a platform invitation and send email.

        Args:
            invite_data: Invitation details (email, role, message)
            invited_by_id: Admin user ID creating the invite
            invited_by_name: Admin user display name
            invited_by_email: Admin user email

        Returns:
            PlatformInviteResponse: Created invitation

        Raises:
            HTTPException: If user already exists or pending invite exists
        """
        email_lower = invite_data.email.lower()

        # Check if user already exists
        existing_user = await self.users_collection.find_one(
            {"email": {"$regex": f"^{email_lower}$", "$options": "i"}}
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {invite_data.email} already exists"
            )

        # Check for existing pending invite
        existing_invite = await self.invites_collection.find_one({
            "email": {"$regex": f"^{email_lower}$", "$options": "i"},
            "status": "pending"
        })
        if existing_invite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Pending invitation already exists for {invite_data.email}. Use resend instead."
            )

        # Create invite document
        invite_token = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        expires_at = now + timedelta(days=INVITE_EXPIRY_DAYS)

        invite_doc = {
            "email": email_lower,
            "role": invite_data.role,
            "status": "pending",
            "token": invite_token,
            "invited_by_id": invited_by_id,
            "invited_by_name": invited_by_name,
            "invited_by_email": invited_by_email,
            "message": invite_data.message,
            "invited_at": now,
            "expires_at": expires_at,
            "accepted_at": None,
            "accepted_by_user_id": None,
            "last_email_sent_at": now,
            "email_count": 1
        }

        result = await self.invites_collection.insert_one(invite_doc)
        invite_id = str(result.inserted_id)

        # Send invitation email
        email_result = await send_invite_email(
            to_email=invite_data.email,
            inviter_name=invited_by_name,
            invite_token=invite_token,
            role=invite_data.role,
            custom_message=invite_data.message,
            expires_at=expires_at,
            is_resend=False
        )

        if not email_result.get("success"):
            logger.warning(
                f"Invite created but email failed for {invite_data.email}: "
                f"{email_result.get('error')}"
            )

        logger.info(
            f"Platform invite created for {invite_data.email} by {invited_by_name} "
            f"(role: {invite_data.role})"
        )

        return PlatformInviteResponse(
            id=invite_id,
            email=email_lower,
            role=invite_data.role,
            status="pending",
            invited_by_name=invited_by_name,
            invited_by_email=invited_by_email,
            message=invite_data.message,
            invited_at=now,
            expires_at=expires_at,
            accepted_at=None,
            email_count=1
        )

    async def list_invites(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        search: Optional[str] = None
    ) -> PlatformInviteListResponse:
        """
        List platform invitations with pagination and filters.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            status_filter: Filter by status (pending, accepted, revoked, expired)
            search: Search by email

        Returns:
            PlatformInviteListResponse: Paginated list of invitations
        """
        query: Dict[str, Any] = {}

        if status_filter:
            query["status"] = status_filter

        if search:
            query["email"] = {"$regex": search, "$options": "i"}

        # Count total matching documents
        total = await self.invites_collection.count_documents(query)

        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        # Get invites sorted by invited_at (newest first)
        cursor = (
            self.invites_collection.find(query)
            .sort("invited_at", -1)
            .skip(skip)
            .limit(page_size)
        )

        invites = []
        async for doc in cursor:
            invites.append(PlatformInviteResponse(
                id=str(doc["_id"]),
                email=doc["email"],
                role=doc["role"],
                status=doc["status"],
                invited_by_name=doc["invited_by_name"],
                invited_by_email=doc["invited_by_email"],
                message=doc.get("message"),
                invited_at=doc["invited_at"],
                expires_at=doc["expires_at"],
                accepted_at=doc.get("accepted_at"),
                email_count=doc.get("email_count", 1)
            ))

        return PlatformInviteListResponse(
            invites=invites,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    async def get_invite_by_id(
        self,
        invite_id: str
    ) -> Optional[PlatformInviteResponse]:
        """
        Get a specific invitation by ID.

        Args:
            invite_id: MongoDB ObjectId as string

        Returns:
            PlatformInviteResponse or None if not found
        """
        if not ObjectId.is_valid(invite_id):
            return None

        doc = await self.invites_collection.find_one({"_id": ObjectId(invite_id)})
        if not doc:
            return None

        return PlatformInviteResponse(
            id=str(doc["_id"]),
            email=doc["email"],
            role=doc["role"],
            status=doc["status"],
            invited_by_name=doc["invited_by_name"],
            invited_by_email=doc["invited_by_email"],
            message=doc.get("message"),
            invited_at=doc["invited_at"],
            expires_at=doc["expires_at"],
            accepted_at=doc.get("accepted_at"),
            email_count=doc.get("email_count", 1)
        )

    async def verify_invite_token(self, token: str) -> PlatformInviteVerifyResponse:
        """
        Verify an invitation token (called from signup page).

        This is a public endpoint - no authentication required.

        Args:
            token: Invitation token from signup URL

        Returns:
            PlatformInviteVerifyResponse: Verification result with email/role if valid
        """
        doc = await self.invites_collection.find_one({"token": token})

        if not doc:
            return PlatformInviteVerifyResponse(
                valid=False,
                error="Invitation not found or invalid"
            )

        # Check if expired
        if doc["expires_at"] < datetime.utcnow():
            # Update status to expired
            await self.invites_collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"status": "expired"}}
            )
            return PlatformInviteVerifyResponse(
                valid=False,
                error="This invitation has expired. Please contact the administrator for a new invitation."
            )

        # Check if already used or revoked
        if doc["status"] != "pending":
            status_messages = {
                "accepted": "This invitation has already been used.",
                "revoked": "This invitation has been revoked.",
                "expired": "This invitation has expired."
            }
            return PlatformInviteVerifyResponse(
                valid=False,
                error=status_messages.get(doc["status"], f"Invitation status: {doc['status']}")
            )

        return PlatformInviteVerifyResponse(
            valid=True,
            email=doc["email"],
            role=doc["role"],
            invited_by_name=doc["invited_by_name"],
            message=doc.get("message"),
            expires_at=doc["expires_at"]
        )

    async def mark_invite_accepted(
        self,
        token: str,
        user_id: str
    ) -> bool:
        """
        Mark an invitation as accepted after user signup.

        Called from auth service after successful registration with invite token.

        Args:
            token: Invitation token
            user_id: ID of the newly created user

        Returns:
            bool: True if marked successfully, False otherwise
        """
        result = await self.invites_collection.update_one(
            {"token": token, "status": "pending"},
            {
                "$set": {
                    "status": "accepted",
                    "accepted_at": datetime.utcnow(),
                    "accepted_by_user_id": user_id
                }
            }
        )

        if result.modified_count > 0:
            logger.info(f"Platform invite marked as accepted (user: {user_id})")
            return True

        return False

    async def resend_invite(
        self,
        invite_id: str,
        resender_name: str
    ) -> Dict[str, Any]:
        """
        Resend invitation email and extend expiry.

        Args:
            invite_id: Invitation ID
            resender_name: Name of admin resending

        Returns:
            Dict with success status and message

        Raises:
            HTTPException: If invite not found or not in pending status
        """
        if not ObjectId.is_valid(invite_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid invitation ID"
            )

        doc = await self.invites_collection.find_one({"_id": ObjectId(invite_id)})
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )

        if doc["status"] != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot resend invitation with status: {doc['status']}"
            )

        # Extend expiry
        new_expires = datetime.utcnow() + timedelta(days=INVITE_EXPIRY_DAYS)

        # Send reminder email
        email_result = await send_invite_email(
            to_email=doc["email"],
            inviter_name=resender_name,
            invite_token=doc["token"],
            role=doc["role"],
            custom_message=doc.get("message"),
            expires_at=new_expires,
            is_resend=True
        )

        if email_result.get("success"):
            # Update invite document
            await self.invites_collection.update_one(
                {"_id": ObjectId(invite_id)},
                {
                    "$set": {
                        "expires_at": new_expires,
                        "last_email_sent_at": datetime.utcnow()
                    },
                    "$inc": {"email_count": 1}
                }
            )
            logger.info(f"Platform invite resent to {doc['email']}")
            return {
                "success": True,
                "message": f"Invitation resent to {doc['email']}"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to send email: {email_result.get('error')}"
            }

    async def revoke_invite(self, invite_id: str) -> Dict[str, Any]:
        """
        Revoke a pending invitation.

        Args:
            invite_id: Invitation ID

        Returns:
            Dict with success status

        Raises:
            HTTPException: If invite not found or not in pending status
        """
        if not ObjectId.is_valid(invite_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid invitation ID"
            )

        result = await self.invites_collection.update_one(
            {"_id": ObjectId(invite_id), "status": "pending"},
            {"$set": {"status": "revoked"}}
        )

        if result.modified_count > 0:
            logger.info(f"Platform invite {invite_id} revoked")
            return {"success": True, "message": "Invitation revoked successfully"}

        # Check if invite exists but wrong status
        doc = await self.invites_collection.find_one({"_id": ObjectId(invite_id)})
        if doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot revoke invitation with status: {doc['status']}"
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    async def expire_old_invites(self) -> int:
        """
        Mark expired invitations as expired.

        Should be run periodically (e.g., daily via cron or scheduled task).

        Returns:
            int: Number of invitations marked as expired
        """
        result = await self.invites_collection.update_many(
            {
                "status": "pending",
                "expires_at": {"$lt": datetime.utcnow()}
            },
            {"$set": {"status": "expired"}}
        )

        if result.modified_count > 0:
            logger.info(f"Expired {result.modified_count} platform invitations")

        return result.modified_count

    async def get_invite_stats(self) -> PlatformInviteStats:
        """
        Get statistics about platform invitations.

        Returns:
            PlatformInviteStats: Invitation statistics
        """
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ]

        status_counts = {}
        async for doc in self.invites_collection.aggregate(pipeline):
            status_counts[doc["_id"]] = doc["count"]

        total = sum(status_counts.values())
        pending = status_counts.get("pending", 0)
        accepted = status_counts.get("accepted", 0)
        expired = status_counts.get("expired", 0)
        revoked = status_counts.get("revoked", 0)

        # Count invites this week
        week_ago = datetime.utcnow() - timedelta(days=7)
        invites_this_week = await self.invites_collection.count_documents({
            "invited_at": {"$gte": week_ago}
        })

        # Calculate acceptance rate
        acceptance_rate = (accepted / total * 100) if total > 0 else 0.0

        return PlatformInviteStats(
            total_invites=total,
            pending_invites=pending,
            accepted_invites=accepted,
            expired_invites=expired,
            revoked_invites=revoked,
            invites_this_week=invites_this_week,
            acceptance_rate=round(acceptance_rate, 1)
        )

    # ============ User Detail (extending AdminService) ============

    async def get_user_by_id(self, user_id: str) -> Optional[UserStatsResponse]:
        """
        Get detailed user information by ID.

        Includes devotional count and activity stats.

        Args:
            user_id: User's MongoDB ObjectId as string

        Returns:
            UserStatsResponse or None if not found
        """
        if not ObjectId.is_valid(user_id):
            return None

        user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return None

        # Count user's devotionals
        devotionals_count = await self.db.devotionals.count_documents(
            {"author_id": str(user["_id"])}
        )

        return UserStatsResponse(
            id=str(user["_id"]),
            email=user["email"],
            name=user.get("name", ""),
            role=user.get("role", "user"),
            avatar_url=user.get("avatar_url"),
            is_active=user.get("is_active", True),
            is_suspended=user.get("is_suspended", False),
            last_active=user.get("last_active"),
            created_at=user.get("created_at"),
            devotionals_count=devotionals_count
        )


# Singleton instance
_user_management_service: Optional[UserManagementService] = None


def get_user_management_service() -> UserManagementService:
    """
    Get user management service singleton instance.

    Returns:
        UserManagementService: Service instance
    """
    global _user_management_service
    if _user_management_service is None:
        _user_management_service = UserManagementService()
    return _user_management_service
