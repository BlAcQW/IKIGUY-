"""
User Invitation Service.

Handles user invitation business logic including:
- Creating and sending invitations
- Validating invitation tokens
- Processing invitation acceptances
- Automatic affiliate registration with inviter's referral code
- Email notifications

Author: KasaAI Team
Date: 2025-11-23
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException

from ..models.invitation import (
    UserInvitation,
    InviteUserRequest,
    AcceptInvitationRequest,
    InvitationStatus,
    InvitationListResponse,
    USER_INVITATIONS_COLLECTION,
)
from ..services.auth_service import get_auth_service
from ..services.affiliate_service import AffiliateService
from ..models import SignupRequest

logger = logging.getLogger(__name__)


class InvitationService:
    """
    User invitation service.

    Manages user invitations with automatic affiliate registration.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize invitation service.

        Args:
            db: MongoDB database connection
        """
        self.db = db
        self.invitations_collection = db[USER_INVITATIONS_COLLECTION]
        self.users_collection = db.users
        self.affiliate_service = AffiliateService(db)

    async def create_invitation(
        self,
        request: InviteUserRequest,
        inviter_user_id: str,
        inviter_email: str,
        inviter_name: str,
    ) -> UserInvitation:
        """
        Create a new user invitation.

        Args:
            request: Invitation request data
            inviter_user_id: User ID of person creating invitation
            inviter_email: Email of person creating invitation
            inviter_name: Name of person creating invitation

        Returns:
            Created invitation

        Raises:
            HTTPException: If user already exists or already has pending invitation
        """
        # Check if user already exists
        auth_service = await get_auth_service()
        existing_user = await auth_service.users_collection.find_one(
            {"email": request.email.lower()}
        )
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail=f"User with email {request.email} already exists"
            )

        # Check if there's already a pending invitation
        existing_invitation = await self.invitations_collection.find_one({
            "email": request.email.lower(),
            "status": InvitationStatus.PENDING
        })
        if existing_invitation:
            raise HTTPException(
                status_code=400,
                detail=f"Pending invitation already exists for {request.email}"
            )

        # Get inviter's affiliate referral code (if they have one)
        inviter_referral_code = None
        try:
            affiliate_profile = await self.affiliate_service.profiles_collection.find_one(
                {"user_id": inviter_user_id}
            )
            if affiliate_profile:
                inviter_referral_code = affiliate_profile.get("referral_code")
                logger.info(
                    f"Inviter {inviter_email} has referral code: {inviter_referral_code}"
                )
        except Exception as e:
            logger.warning(f"Could not fetch inviter's referral code: {e}")

        # Create invitation
        invitation = UserInvitation(
            email=request.email,
            invited_by_user_id=inviter_user_id,
            invited_by_email=inviter_email,
            invited_by_name=inviter_name,
            inviter_referral_code=inviter_referral_code,
            role=request.role,
            organization_id=request.organization_id,
            message=request.message,
        )

        # Save to database
        await self.invitations_collection.insert_one(invitation.model_dump())

        logger.info(
            f"Created invitation for {request.email} by {inviter_email} "
            f"(referral_code: {inviter_referral_code})"
        )

        # Send invitation email if requested
        if request.send_email:
            try:
                await self._send_invitation_email(invitation)
            except Exception as e:
                logger.error(f"Failed to send invitation email: {e}")
                # Don't fail the invitation creation if email fails

        return invitation

    async def get_invitation_by_token(self, token: str) -> Optional[UserInvitation]:
        """
        Get invitation by token.

        Args:
            token: Invitation token

        Returns:
            Invitation if found, None otherwise
        """
        invitation_doc = await self.invitations_collection.find_one({"token": token})
        if not invitation_doc:
            return None

        return UserInvitation(**invitation_doc)

    async def get_invitations(
        self,
        inviter_user_id: Optional[str] = None,
        status: Optional[InvitationStatus] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> InvitationListResponse:
        """
        Get list of invitations with filters.

        Args:
            inviter_user_id: Filter by inviter user ID
            status: Filter by status
            limit: Maximum number of results
            skip: Number of results to skip

        Returns:
            Invitation list response with statistics
        """
        # Build query
        query = {}
        if inviter_user_id:
            query["invited_by_user_id"] = inviter_user_id
        if status:
            query["status"] = status

        # Get total count
        total = await self.invitations_collection.count_documents(query)

        # Get invitations
        cursor = self.invitations_collection.find(query).sort(
            "created_at", -1
        ).skip(skip).limit(limit)
        invitations = await cursor.to_list(length=limit)

        # Get status counts
        pending = await self.invitations_collection.count_documents({
            **query,
            "status": InvitationStatus.PENDING
        })
        accepted = await self.invitations_collection.count_documents({
            **query,
            "status": InvitationStatus.ACCEPTED
        })
        expired = await self.invitations_collection.count_documents({
            **query,
            "status": InvitationStatus.EXPIRED
        })
        cancelled = await self.invitations_collection.count_documents({
            **query,
            "status": InvitationStatus.CANCELLED
        })

        return InvitationListResponse(
            invitations=invitations,
            total=total,
            pending=pending,
            accepted=accepted,
            expired=expired,
            cancelled=cancelled,
        )

    async def accept_invitation(
        self,
        token: str,
        request: AcceptInvitationRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Accept an invitation and create user account.

        Automatically registers user as affiliate with inviter's referral code.

        Args:
            token: Invitation token
            request: Acceptance request data
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Dict with user info and tokens

        Raises:
            HTTPException: If invitation invalid, expired, or already used
        """
        # Get invitation
        invitation = await self.get_invitation_by_token(token)
        if not invitation:
            raise HTTPException(
                status_code=404,
                detail="Invitation not found or invalid token"
            )

        # Check if invitation is valid
        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Invitation is {invitation.status}"
            )

        if invitation.is_expired:
            # Mark as expired
            await self.invitations_collection.update_one(
                {"token": token},
                {"$set": {"status": InvitationStatus.EXPIRED}}
            )
            raise HTTPException(
                status_code=400,
                detail="Invitation has expired"
            )

        # Create user account
        auth_service = await get_auth_service()
        signup_data = SignupRequest(
            email=invitation.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            role=invitation.role,
        )

        try:
            # Create user
            auth_response = await auth_service.signup(signup_data)
            user_id = auth_response.user.id
            organization_id = auth_response.user.primary_organization_id

            logger.info(
                f"Created user account {invitation.email} (ID: {user_id}) "
                f"from invitation by {invitation.invited_by_email}"
            )

            # Automatically register as affiliate with inviter's referral code
            if invitation.inviter_referral_code:
                try:
                    affiliate_profile = await self.affiliate_service.join_program(
                        user_id=user_id,
                        organization_id=organization_id,
                        upline_referral_code=invitation.inviter_referral_code,
                    )
                    logger.info(
                        f"Auto-registered {invitation.email} as affiliate "
                        f"with upline code {invitation.inviter_referral_code} "
                        f"(new code: {affiliate_profile.referral_code})"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to auto-register affiliate for {invitation.email}: {e}"
                    )
                    # Don't fail user creation if affiliate registration fails

            # Update invitation status
            await self.invitations_collection.update_one(
                {"token": token},
                {
                    "$set": {
                        "status": InvitationStatus.ACCEPTED,
                        "accepted_at": datetime.utcnow(),
                        "accepted_user_id": user_id,
                        "accepted_ip_address": ip_address,
                        "accepted_user_agent": user_agent,
                    }
                }
            )

            logger.info(f"Invitation accepted: {invitation.email}")

            return {
                "success": True,
                "message": "Account created successfully",
                "user": {
                    "id": user_id,
                    "email": auth_response.user.email,
                    "name": f"{request.first_name} {request.last_name}",
                    "role": invitation.role,
                },
                "tokens": {
                    "access_token": auth_response.access_token,
                    "refresh_token": auth_response.refresh_token,
                },
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error accepting invitation: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create account: {str(e)}"
            )

    async def cancel_invitation(self, invitation_id: str) -> bool:
        """
        Cancel a pending invitation.

        Args:
            invitation_id: Invitation ID to cancel

        Returns:
            True if cancelled, False if not found or already processed
        """
        result = await self.invitations_collection.update_one(
            {
                "id": invitation_id,
                "status": InvitationStatus.PENDING
            },
            {
                "$set": {
                    "status": InvitationStatus.CANCELLED,
                    "cancelled_at": datetime.utcnow(),
                }
            }
        )

        if result.modified_count > 0:
            logger.info(f"Cancelled invitation {invitation_id}")
            return True

        return False

    async def resend_invitation(self, invitation_id: str) -> bool:
        """
        Resend invitation email.

        Args:
            invitation_id: Invitation ID to resend

        Returns:
            True if sent, False if not found or invalid

        Raises:
            HTTPException: If invitation is not pending
        """
        invitation_doc = await self.invitations_collection.find_one({"id": invitation_id})
        if not invitation_doc:
            return False

        invitation = UserInvitation(**invitation_doc)

        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail="Can only resend pending invitations"
            )

        if invitation.is_expired:
            raise HTTPException(
                status_code=400,
                detail="Invitation has expired"
            )

        try:
            await self._send_invitation_email(invitation)
            logger.info(f"Resent invitation email to {invitation.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to resend invitation email: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to send invitation email"
            )

    async def _send_invitation_email(self, invitation: UserInvitation) -> None:
        """
        Send invitation email to user.

        Args:
            invitation: Invitation to send email for

        Raises:
            Exception: If email sending fails
        """
        # TODO: Implement email sending with proper email service
        # For now, just log the invitation details

        invitation_url = f"https://kasaai.ailabsafrica.com/accept-invitation?token={invitation.token}"

        logger.info(
            f"\n{'='*60}\n"
            f"INVITATION EMAIL\n"
            f"{'='*60}\n"
            f"To: {invitation.email}\n"
            f"From: {invitation.invited_by_name} <{invitation.invited_by_email}>\n"
            f"Subject: You're invited to join KasaAI\n\n"
            f"Message: {invitation.message or 'No message'}\n\n"
            f"Invitation URL: {invitation_url}\n"
            f"Expires: {invitation.expires_at}\n"
            f"{'='*60}\n"
        )

        # TODO: Replace with actual email service
        # await email_service.send(
        #     to=invitation.email,
        #     subject="You're invited to join KasaAI",
        #     template="invitation",
        #     data={
        #         "inviter_name": invitation.invited_by_name,
        #         "invitation_url": invitation_url,
        #         "message": invitation.message,
        #         "expires_at": invitation.expires_at,
        #     }
        # )

    async def mark_expired_invitations(self) -> int:
        """
        Mark expired invitations as expired.

        This should be called periodically (e.g., daily cron job).

        Returns:
            Number of invitations marked as expired
        """
        result = await self.invitations_collection.update_many(
            {
                "status": InvitationStatus.PENDING,
                "expires_at": {"$lt": datetime.utcnow()}
            },
            {
                "$set": {"status": InvitationStatus.EXPIRED}
            }
        )

        if result.modified_count > 0:
            logger.info(f"Marked {result.modified_count} invitations as expired")

        return result.modified_count


# Global service instance (will be initialized in main.py)
_invitation_service: Optional[InvitationService] = None


async def get_invitation_service() -> InvitationService:
    """Get invitation service instance."""
    global _invitation_service
    if _invitation_service is None:
        from ..mongo import get_database
        db = get_database()
        _invitation_service = InvitationService(db)
    return _invitation_service
