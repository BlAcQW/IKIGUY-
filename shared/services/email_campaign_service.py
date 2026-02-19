"""
Email Campaign Service

This service handles email campaign operations including:
- Campaign creation, management, and execution
- Template processing with HTML support
- Bulk email sending with rate limiting
- Campaign analytics and tracking
- Integration with UnifiedEmailService
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from shared.models.campaign import (
    Campaign,
    CampaignMessage,
    CampaignMessageStatus,
    CampaignStatus,
    CampaignType,
)
from shared.services.unified_email_service import get_email_service

logger = logging.getLogger(__name__)


class EmailCampaignService:
    """
    Service for managing email campaigns.

    Handles campaign execution with HTML templates, personalization,
    rate limiting, and analytics tracking.
    """

    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        """
        Initialize Email campaign service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.email_service = get_email_service()

        # Running campaigns tracker
        self._running_campaigns: Dict[str, asyncio.Task] = {}

    def set_database(self, db: AsyncIOMotorDatabase):
        """Set the database instance."""
        self.db = db

    async def prepare_campaign_messages(
        self,
        campaign: Campaign,
        contacts: List[Dict[str, Any]]
    ) -> int:
        """
        Prepare email campaign messages from contact list.

        Args:
            campaign: Campaign object
            contacts: List of contact dictionaries with email, name, etc.

        Returns:
            Number of messages prepared
        """
        if self.db is None:
            raise ValueError("Database not initialized")

        # Delete existing pending messages to avoid duplicates
        messages_collection = self.db["campaign_messages"]
        delete_result = await messages_collection.delete_many({
            "campaign_id": campaign.id,
            "status": CampaignMessageStatus.PENDING.value
        })
        if delete_result.deleted_count > 0:
            self.logger.info(f"Deleted {delete_result.deleted_count} existing pending messages for campaign {campaign.id}")

        messages = []
        seen_emails = set()  # Track unique emails to avoid duplicates

        for contact in contacts:
            email = contact.get("email", "")
            if not email:
                continue

            # Skip if we've already processed this email
            if email in seen_emails:
                self.logger.debug(f"Skipping duplicate email: {email}")
                continue

            seen_emails.add(email)

            # Render message content from template
            rendered_content = self._render_email_template(campaign, contact)

            msg = CampaignMessage(
                id=str(uuid.uuid4()),
                campaign_id=campaign.id,
                organization_id=campaign.organization_id,
                contact_id=contact.get("id", str(uuid.uuid4())),
                recipient_email=email,
                recipient_name=contact.get("name") or f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
                recipient_phone=contact.get("phone"),
                rendered_content=rendered_content,
                status=CampaignMessageStatus.PENDING
            )
            messages.append(msg.dict())

        if messages:
            await messages_collection.insert_many(messages)
            self.logger.info(f"Prepared {len(messages)} email messages for campaign {campaign.id}")

        return len(messages)

    def _render_email_template(self, campaign: Campaign, contact: Dict[str, Any]) -> str:
        """
        Render email template with contact data.

        Args:
            campaign: Campaign with message template
            contact: Contact data for personalization

        Returns:
            Rendered HTML content
        """
        # Get template content
        html_content = campaign.message_template.html_content or ""
        text_content = campaign.message_template.text_content or ""

        # Simple variable substitution
        # Supports {{variable}} syntax
        data = {
            "first_name": contact.get("first_name", ""),
            "last_name": contact.get("last_name", ""),
            "name": contact.get("name") or f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
            "email": contact.get("email", ""),
            "phone": contact.get("phone", ""),
            **contact.get("custom_data", {})
        }

        # Replace variables in HTML content
        for key, value in data.items():
            html_content = html_content.replace(f"{{{{{key}}}}}", str(value))
            text_content = text_content.replace(f"{{{{{key}}}}}", str(value))

        return html_content or text_content

    async def launch_campaign(self, campaign: Campaign) -> bool:
        """
        Launch an email campaign.

        Args:
            campaign: Campaign to launch

        Returns:
            True if launched successfully
        """
        if campaign.id in self._running_campaigns:
            self.logger.warning(f"Campaign {campaign.id} is already running")
            return True

        # Start execution task
        task = asyncio.create_task(self._execute_campaign(campaign.id))
        self._running_campaigns[campaign.id] = task

        self.logger.info(f"Launched email campaign: {campaign.id}")
        return True

    async def pause_campaign(self, campaign_id: str) -> bool:
        """
        Pause a running campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            True if paused successfully
        """
        if campaign_id in self._running_campaigns:
            self._running_campaigns[campaign_id].cancel()
            del self._running_campaigns[campaign_id]
            self.logger.info(f"Paused email campaign: {campaign_id}")
            return True
        return False

    async def _execute_campaign(self, campaign_id: str):
        """
        Execute campaign sending.

        Args:
            campaign_id: Campaign ID
        """
        try:
            if self.db is None:
                raise ValueError("Database not initialized")

            # Get campaign
            campaigns_collection = self.db["campaigns"]
            campaign_doc = await campaigns_collection.find_one({"id": campaign_id})
            if not campaign_doc:
                raise ValueError(f"Campaign not found: {campaign_id}")

            campaign = Campaign(**campaign_doc)

            # Get pending messages
            messages_collection = self.db["campaign_messages"]
            cursor = messages_collection.find({
                "campaign_id": campaign_id,
                "status": CampaignMessageStatus.PENDING.value
            })

            # Calculate delay for rate limiting
            rate_per_second = campaign.delivery_config.rate_per_second
            delay = 1.0 / rate_per_second if rate_per_second > 0 else 1.0

            sent_count = 0
            failed_count = 0
            delivered_count = 0
            total_cost = 0.0

            async for msg_doc in cursor:
                try:
                    message = CampaignMessage(**msg_doc)

                    # Get subject and content
                    subject = campaign.message_template.subject or "Newsletter"
                    html_body = message.rendered_content
                    text_body = campaign.message_template.text_version

                    # Send email
                    result = await self.email_service.send_email(
                        to=message.recipient_email,
                        subject=subject,
                        body=text_body or "",
                        html_body=html_body,
                        from_email=None,  # Uses default from config
                        from_name=None
                    )

                    if result.get("success"):
                        # Update message status
                        await messages_collection.update_one(
                            {"id": message.id},
                            {"$set": {
                                "status": CampaignMessageStatus.SENT.value,
                                "sent_at": datetime.utcnow().isoformat(),
                                "external_message_id": result.get("message_id"),
                                "metadata.provider": result.get("provider")
                            }}
                        )
                        sent_count += 1
                        delivered_count += 1  # For email, sent = delivered

                        # Email cost is typically free or very low
                        # Can be configured based on provider
                        cost = 0.0
                        total_cost += cost

                    else:
                        # Handle failure
                        error_msg = result.get("error", "Unknown error")
                        await messages_collection.update_one(
                            {"id": message.id},
                            {"$set": {
                                "status": CampaignMessageStatus.FAILED.value,
                                "failed_at": datetime.utcnow().isoformat(),
                                "error_message": error_msg
                            },
                            "$inc": {"attempts": 1}}
                        )
                        failed_count += 1

                        self.logger.warning(
                            f"Email failed for {message.recipient_email}: {error_msg}"
                        )

                    # Update campaign progress
                    await campaigns_collection.update_one(
                        {"id": campaign_id},
                        {"$set": {
                            "sent_count": sent_count,
                            "delivered_count": delivered_count,
                            "failed_count": failed_count,
                            "total_cost": total_cost,
                            "updated_at": datetime.utcnow().isoformat()
                        }}
                    )

                    # Rate limiting
                    await asyncio.sleep(delay)

                except asyncio.CancelledError:
                    self.logger.info(f"Campaign {campaign_id} execution cancelled")
                    return
                except Exception as e:
                    self.logger.error(f"Error sending email message: {e}")
                    failed_count += 1

            # Campaign completed
            await campaigns_collection.update_one(
                {"id": campaign_id},
                {"$set": {
                    "status": CampaignStatus.COMPLETED.value,
                    "completed_at": datetime.utcnow().isoformat(),
                    "sent_count": sent_count,
                    "delivered_count": delivered_count,
                    "failed_count": failed_count,
                    "total_cost": total_cost
                }}
            )

            self.logger.info(f"Campaign {campaign_id} completed: {sent_count} sent, {failed_count} failed")

        except asyncio.CancelledError:
            self.logger.info(f"Campaign {campaign_id} execution cancelled")
        except Exception as e:
            self.logger.error(f"Campaign execution error: {e}")
            if self.db is not None:
                await self.db["campaigns"].update_one(
                    {"id": campaign_id},
                    {"$set": {
                        "status": CampaignStatus.FAILED.value,
                        "updated_at": datetime.utcnow().isoformat()
                    }}
                )
        finally:
            if campaign_id in self._running_campaigns:
                del self._running_campaigns[campaign_id]

    async def get_campaign_messages(
        self,
        campaign_id: str,
        status: Optional[CampaignMessageStatus] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[CampaignMessage]:
        """
        Get messages for a campaign.

        Args:
            campaign_id: Campaign ID
            status: Optional status filter
            limit: Maximum messages to return
            skip: Number to skip

        Returns:
            List of CampaignMessage objects
        """
        if self.db is None:
            return []

        collection = self.db["campaign_messages"]

        query = {"campaign_id": campaign_id}
        if status:
            query["status"] = status.value

        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        messages = []

        async for doc in cursor:
            messages.append(CampaignMessage(**doc))

        return messages


# Create singleton instance
_email_campaign_service_instance: Optional[EmailCampaignService] = None


def get_email_campaign_service() -> EmailCampaignService:
    """
    Get the global email campaign service instance.

    Returns:
        EmailCampaignService: Email campaign service
    """
    global _email_campaign_service_instance

    if _email_campaign_service_instance is None:
        _email_campaign_service_instance = EmailCampaignService()

    return _email_campaign_service_instance
