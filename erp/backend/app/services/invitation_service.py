"""
Organization Invitation Service for ERP.

Handles invitation workflow for adding users to organizations.
Integrated from ChurchFlow's invitation system.
Includes email notification functionality using unified email service.
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.invitation import Invitation, InvitationCreate, InvitationAccept
from app.core.database import MongoDB

# Import unified email service from shared
sys.path.insert(0, "/opt/kasaai/apps")
try:
    from shared.services.unified_email_service import get_email_service
    EMAIL_SERVICE_AVAILABLE = True
except ImportError:
    EMAIL_SERVICE_AVAILABLE = False
    get_email_service = None

logger = logging.getLogger(__name__)

# Base URL for invitation links
ERP_BASE_URL = os.getenv("ERP_FRONTEND_URL", "https://erp.ailabsafrica.com")


class InvitationService:
    """Service for managing organization invitations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.organization_invitations
        self.org_collection = db.organizations
        self._email_service = None

    @property
    def email_service(self):
        """Get email service lazily."""
        if self._email_service is None and EMAIL_SERVICE_AVAILABLE:
            self._email_service = get_email_service()
        return self._email_service

    async def initialize_indexes(self):
        """Create database indexes for invitations."""
        await self.collection.create_index("organization_id")
        await self.collection.create_index("email")
        await self.collection.create_index("token", unique=True)
        await self.collection.create_index("status")
        await self.collection.create_index([("organization_id", 1), ("status", 1)])
        await self.collection.create_index("expires_at")
        logger.info("✅ Invitation indexes initialized")

    async def _get_organization_name(self, organization_id: str) -> str:
        """Get organization name by ID."""
        try:
            org = await self.org_collection.find_one({"_id": ObjectId(organization_id)})
            if org:
                return org.get("name", "the organization")
            return "the organization"
        except Exception:
            return "the organization"

    def _generate_invitation_email_html(
        self,
        invitee_name: str,
        inviter_email: str,
        organization_name: str,
        role: str,
        invitation_token: str,
        custom_message: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> str:
        """
        Generate HTML email content for invitation.

        Args:
            invitee_name: Name of the person being invited
            inviter_email: Email of the person sending invitation
            organization_name: Name of the organization
            role: Role being assigned
            invitation_token: Unique token for accepting invitation
            custom_message: Optional custom message from inviter
            expires_at: Expiration datetime

        Returns:
            HTML email content
        """
        invitation_link = f"{ERP_BASE_URL}/accept-invitation?token={invitation_token}"
        expires_str = expires_at.strftime("%B %d, %Y") if expires_at else "7 days"

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>You're Invited to Join {organization_name}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; max-width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); border-radius: 12px 12px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">
                                KasaAI ERP
                            </h1>
                            <p style="margin: 10px 0 0; color: #bfdbfe; font-size: 14px;">
                                Enterprise Resource Planning
                            </p>
                        </td>
                    </tr>

                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px; color: #1e293b; font-size: 22px; font-weight: 600;">
                                You've Been Invited! 🎉
                            </h2>

                            <p style="margin: 0 0 20px; color: #475569; font-size: 16px; line-height: 1.6;">
                                Hello{f' {invitee_name}' if invitee_name else ''},
                            </p>

                            <p style="margin: 0 0 20px; color: #475569; font-size: 16px; line-height: 1.6;">
                                <strong>{inviter_email}</strong> has invited you to join
                                <strong>{organization_name}</strong> on KasaAI ERP as a{' an' if role.lower().startswith(('a', 'e', 'i', 'o', 'u')) else ''}
                                <strong style="color: #2563eb;">{role.title()}</strong>.
                            </p>

                            {f'''
                            <div style="margin: 20px 0; padding: 15px 20px; background-color: #f1f5f9; border-left: 4px solid #2563eb; border-radius: 0 8px 8px 0;">
                                <p style="margin: 0; color: #475569; font-size: 14px; font-style: italic;">
                                    "{custom_message}"
                                </p>
                            </div>
                            ''' if custom_message else ''}

                            <!-- CTA Button -->
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{invitation_link}"
                                   style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);">
                                    Accept Invitation
                                </a>
                            </div>

                            <p style="margin: 20px 0 0; color: #64748b; font-size: 14px; text-align: center;">
                                This invitation expires on <strong>{expires_str}</strong>
                            </p>

                            <!-- Alternative Link -->
                            <div style="margin: 30px 0 0; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                                <p style="margin: 0; color: #64748b; font-size: 13px;">
                                    If the button doesn't work, copy and paste this link into your browser:
                                </p>
                                <p style="margin: 10px 0 0; word-break: break-all;">
                                    <a href="{invitation_link}" style="color: #2563eb; font-size: 13px;">
                                        {invitation_link}
                                    </a>
                                </p>
                            </div>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; background-color: #f8fafc; border-radius: 0 0 12px 12px; text-align: center;">
                            <p style="margin: 0; color: #94a3b8; font-size: 12px;">
                                This email was sent by KasaAI ERP. If you didn't expect this invitation,
                                you can safely ignore this email.
                            </p>
                            <p style="margin: 10px 0 0; color: #94a3b8; font-size: 12px;">
                                © {datetime.now().year} AI Labs Africa. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    async def send_invitation_email(
        self,
        invitation: Invitation,
        organization_name: str
    ) -> Dict[str, Any]:
        """
        Send invitation email to the invitee.

        Args:
            invitation: The invitation object
            organization_name: Name of the organization

        Returns:
            Dict with success status and details
        """
        if not EMAIL_SERVICE_AVAILABLE or not self.email_service:
            logger.warning("Email service not available. Invitation email not sent.")
            return {
                "success": False,
                "error": "Email service not available",
                "invitation_id": str(invitation.id)
            }

        try:
            # Generate email content
            html_body = self._generate_invitation_email_html(
                invitee_name=invitation.display_name or "",
                inviter_email=invitation.invited_by_email,
                organization_name=organization_name,
                role=invitation.role,
                invitation_token=invitation.token,
                custom_message=invitation.message,
                expires_at=invitation.expires_at
            )

            plain_body = f"""
You've been invited to join {organization_name} on KasaAI ERP!

{invitation.invited_by_email} has invited you to join as a {invitation.role}.

{f'Message: "{invitation.message}"' if invitation.message else ''}

Accept your invitation here:
{ERP_BASE_URL}/accept-invitation?token={invitation.token}

This invitation expires on {invitation.expires_at.strftime('%B %d, %Y') if invitation.expires_at else 'in 7 days'}.

If you didn't expect this invitation, you can safely ignore this email.
"""

            result = await self.email_service.send_email(
                to=invitation.email,
                subject=f"You're invited to join {organization_name} on KasaAI ERP",
                body=plain_body,
                html_body=html_body,
                from_name="KasaAI ERP"
            )

            if result.get("success"):
                logger.info(f"✅ Invitation email sent to {invitation.email}")
                # Update invitation with email sent status
                await self.collection.update_one(
                    {"_id": invitation.id},
                    {"$set": {
                        "email_sent": True,
                        "email_sent_at": datetime.utcnow(),
                        "email_message_id": result.get("message_id")
                    }}
                )
            else:
                logger.error(f"❌ Failed to send invitation email: {result.get('error')}")

            return result

        except Exception as e:
            logger.error(f"❌ Error sending invitation email: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "invitation_id": str(invitation.id)
            }

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
        # Check if invitation already exists
        existing = await self.collection.find_one({
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
        result = await self.collection.insert_one(invitation.model_dump(by_alias=True, exclude={"id"}))

        invitation.id = result.inserted_id
        logger.info(f"Created invitation {invitation.id} for {email} to organization {organization_id}")

        # Send invitation email
        organization_name = await self._get_organization_name(organization_id)
        email_result = await self.send_invitation_email(invitation, organization_name)

        if not email_result.get("success"):
            logger.warning(
                f"Invitation created but email failed to send: {email_result.get('error')}"
            )

        return invitation

    async def get_invitation_by_token(self, token: str) -> Optional[Invitation]:
        """
        Get invitation by token.

        Args:
            token: Invitation token

        Returns:
            Invitation if found, None otherwise
        """
        doc = await self.collection.find_one({"token": token})
        return Invitation(**doc) if doc else None

    async def get_invitation_by_id(self, invitation_id: str) -> Optional[Invitation]:
        """
        Get invitation by ID.

        Args:
            invitation_id: Invitation ID

        Returns:
            Invitation if found, None otherwise
        """
        if not ObjectId.is_valid(invitation_id):
            return None

        doc = await self.collection.find_one({"_id": ObjectId(invitation_id)})
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
        query = {"organization_id": organization_id}
        if status:
            query["status"] = status

        cursor = self.collection.find(query).sort("invited_at", -1)
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
        invitation = await self.get_invitation_by_token(token)

        if not invitation:
            raise ValueError("Invitation not found")

        if invitation.status != "pending":
            raise ValueError(f"Invitation is {invitation.status}, cannot accept")

        if invitation.expires_at < datetime.utcnow():
            # Mark as expired
            await self.collection.update_one(
                {"_id": invitation.id},
                {"$set": {"status": "expired"}}
            )
            raise ValueError("Invitation has expired")

        # Update invitation
        result = await self.collection.update_one(
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
        if not ObjectId.is_valid(invitation_id):
            return False

        result = await self.collection.update_one(
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
        result = await self.collection.update_many(
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

    async def resend_invitation_email(self, invitation_id: str) -> Dict[str, Any]:
        """
        Resend invitation email for an existing pending invitation.

        Args:
            invitation_id: Invitation ID

        Returns:
            Dict with success status and details

        Raises:
            ValueError: If invitation not found or not pending
        """
        invitation = await self.get_invitation_by_id(invitation_id)

        if not invitation:
            raise ValueError("Invitation not found")

        if invitation.status != "pending":
            raise ValueError(f"Cannot resend email for {invitation.status} invitation")

        if invitation.expires_at < datetime.utcnow():
            await self.collection.update_one(
                {"_id": invitation.id},
                {"$set": {"status": "expired"}}
            )
            raise ValueError("Invitation has expired")

        organization_name = await self._get_organization_name(invitation.organization_id)
        result = await self.send_invitation_email(invitation, organization_name)

        return result


def get_invitation_service(db: Optional[AsyncIOMotorDatabase] = None) -> InvitationService:
    """
    Get invitation service instance.

    Args:
        db: Database instance (optional, uses default if not provided)

    Returns:
        InvitationService instance
    """
    if db is None:
        db = MongoDB.get_database()

    return InvitationService(db)
