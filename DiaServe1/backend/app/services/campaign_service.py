"""
Campaign Service for EstateFlow.

Unified campaign management across all channels (Voice, SMS, WhatsApp, Email).
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import asyncio

from app.models.campaign import (
    Campaign,
    CampaignCreate,
    CampaignUpdate,
    CampaignType,
    CampaignStatus,
    CampaignMessage,
    CampaignMessageStatus,
    SegmentFilter
)
from app.services.contact_service import ContactService
from app.integration.email_service import EmailService
from app.integration.arkesel_client import ArkeselClient
from app.integration.whatsapp_client import WhatsAppClient
from app.integration.vapi_client import VapiClient

logger = logging.getLogger(__name__)


class CampaignService:
    """Service for managing multi-channel campaigns."""

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize campaign service.

        Args:
            database: MongoDB database instance
        """
        self.db = database
        self.campaigns_collection = database["campaigns"]
        self.messages_collection = database["campaign_messages"]
        self.contact_service = ContactService(database)

        # Initialize standalone delivery services
        self.sms_service = ArkeselClient()
        self.whatsapp_service = WhatsAppClient()
        self.email_service = EmailService()
        self.vapi_service = VapiClient()

        configured = []
        if self.sms_service.is_configured():
            configured.append("SMS/Arkesel")
        if self.whatsapp_service.is_configured():
            configured.append("WhatsApp")
        if self.vapi_service.is_configured():
            configured.append("Vapi/Voice")
        configured.append("Email/SMTP")  # Always available (logs to console if not configured)

        logger.info(f"Campaign service initialized. Delivery channels: {', '.join(configured) or 'none'}")

    async def create_campaign(
        self,
        campaign_data: CampaignCreate,
        organization_id: str,
        user_id: str
    ) -> Campaign:
        """
        Create a new campaign.

        Args:
            campaign_data: Campaign creation data
            organization_id: Organization ID
            user_id: User ID creating the campaign

        Returns:
            Created campaign
        """
        from bson import ObjectId

        # Generate ID
        campaign_id = str(ObjectId())

        # Build campaign document
        campaign_dict = campaign_data.dict()

        # Ensure schedule_config is a dict, not None
        if campaign_dict.get("schedule_config") is None:
            campaign_dict["schedule_config"] = {}

        campaign_dict.update({
            "id": campaign_id,
            "organization_id": organization_id,
            "user_id": user_id,
            "status": CampaignStatus.DRAFT.value,
            "target_count": 0,
            "sent_count": 0,
            "delivered_count": 0,
            "opened_count": 0,
            "clicked_count": 0,
            "failed_count": 0,
            "total_cost": 0.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "started_at": None,
            "completed_at": None,
            "external_campaign_id": None
        })

        # Insert into database
        await self.campaigns_collection.insert_one(campaign_dict)

        logger.info(f"Created {campaign_data.campaign_type} campaign {campaign_id} for organization {organization_id}")

        return Campaign(**campaign_dict)

    async def get_campaign(
        self,
        campaign_id: str,
        organization_id: str
    ) -> Optional[Campaign]:
        """
        Get a campaign by ID.

        Args:
            campaign_id: Campaign ID
            organization_id: Organization ID for access control

        Returns:
            Campaign if found, None otherwise
        """
        campaign_doc = await self.campaigns_collection.find_one({
            "id": campaign_id,
            "organization_id": organization_id
        })

        if not campaign_doc:
            return None

        # Remove MongoDB _id
        campaign_doc.pop("_id", None)

        return Campaign(**campaign_doc)

    async def list_campaigns(
        self,
        organization_id: str,
        campaign_type: Optional[CampaignType] = None,
        status: Optional[CampaignStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Campaign], int]:
        """
        List campaigns for an organization.

        Args:
            organization_id: Organization ID
            campaign_type: Optional filter by campaign type
            status: Optional filter by status
            limit: Maximum number of campaigns to return
            offset: Number of campaigns to skip

        Returns:
            Tuple of (campaigns list, total count)
        """
        # Build query
        query = {"organization_id": organization_id}

        if campaign_type:
            query["campaign_type"] = campaign_type.value

        if status:
            query["status"] = status.value

        # Get total count
        total = await self.campaigns_collection.count_documents(query)

        # Get campaigns with pagination
        cursor = self.campaigns_collection.find(query).skip(offset).limit(limit).sort("created_at", -1)
        campaigns_docs = await cursor.to_list(length=limit)

        campaigns = []
        for doc in campaigns_docs:
            doc.pop("_id", None)
            campaigns.append(Campaign(**doc))

        return campaigns, total

    async def update_campaign(
        self,
        campaign_id: str,
        updates: CampaignUpdate,
        organization_id: str
    ) -> Optional[Campaign]:
        """
        Update a campaign (DRAFT only).

        Args:
            campaign_id: Campaign ID
            updates: Update data
            organization_id: Organization ID for access control

        Returns:
            Updated campaign if found, None otherwise

        Raises:
            ValueError: If campaign is not in DRAFT status
        """
        # Check campaign status
        campaign = await self.get_campaign(campaign_id, organization_id)
        if not campaign:
            return None

        if campaign.status != CampaignStatus.DRAFT:
            raise ValueError(f"Cannot update campaign in {campaign.status} status. Only DRAFT campaigns can be updated.")

        # Build update document
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow()

        # Update in database
        await self.campaigns_collection.update_one(
            {"id": campaign_id, "organization_id": organization_id},
            {"$set": update_dict}
        )

        # Return updated campaign
        return await self.get_campaign(campaign_id, organization_id)

    async def delete_campaign(
        self,
        campaign_id: str,
        organization_id: str
    ) -> bool:
        """
        Delete a campaign (DRAFT only).

        Args:
            campaign_id: Campaign ID
            organization_id: Organization ID for access control

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If campaign is not in DRAFT status
        """
        # Check campaign status
        campaign = await self.get_campaign(campaign_id, organization_id)
        if not campaign:
            return False

        if campaign.status != CampaignStatus.DRAFT:
            raise ValueError(f"Cannot delete campaign in {campaign.status} status. Only DRAFT campaigns can be deleted.")

        # Delete campaign
        result = await self.campaigns_collection.delete_one({
            "id": campaign_id,
            "organization_id": organization_id
        })

        # Delete associated messages
        await self.messages_collection.delete_many({
            "campaign_id": campaign_id,
            "organization_id": organization_id
        })

        return result.deleted_count > 0

    async def preview_segment(
        self,
        segment_filter: SegmentFilter,
        organization_id: str,
        campaign_type: CampaignType
    ) -> Dict[str, Any]:
        """
        Preview contacts that would be targeted by a segment filter.

        Args:
            segment_filter: Filter criteria
            organization_id: Organization ID
            campaign_type: Campaign type for opt-out filtering

        Returns:
            Dictionary with contact count, sample contacts, and estimated cost
        """
        # Get all matching contacts
        contacts = await self.contact_service.apply_segment_filter(
            segment_filter=segment_filter,
            organization_id=organization_id,
            campaign_type=campaign_type,
            limit=None
        )

        # Get sample (first 10)
        sample_contacts = contacts[:10]

        # Calculate estimated cost
        contact_count = len(contacts)
        estimated_cost = self._estimate_campaign_cost(campaign_type, contact_count)

        return {
            "contact_count": contact_count,
            "sample_contacts": sample_contacts,
            "estimated_cost": estimated_cost
        }

    def _estimate_campaign_cost(
        self,
        campaign_type: CampaignType,
        contact_count: int
    ) -> float:
        """
        Estimate campaign cost based on type and contact count.

        Args:
            campaign_type: Campaign type
            contact_count: Number of contacts

        Returns:
            Estimated cost in USD
        """
        # Cost per message (estimates)
        cost_per_message = {
            CampaignType.SMS: 0.05,  # ~GHS 0.05 per SMS
            CampaignType.WHATSAPP: 0.10,  # ~GHS 0.10 per WhatsApp
            CampaignType.VOICE: 0.52,  # TTS (~$0.50) + Call (~$0.02/min)
            CampaignType.EMAIL: 0.01  # ~GHS 0.01 per email
        }

        return cost_per_message.get(campaign_type, 0.0) * contact_count

    async def launch_campaign(
        self,
        campaign_id: str,
        organization_id: str
    ) -> Campaign:
        """
        Launch a campaign.

        Args:
            campaign_id: Campaign ID
            organization_id: Organization ID for access control

        Returns:
            Updated campaign

        Raises:
            ValueError: If campaign cannot be launched
        """
        # Get campaign
        campaign = await self.get_campaign(campaign_id, organization_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Validate status
        if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.PAUSED]:
            raise ValueError(f"Cannot launch campaign in {campaign.status} status")

        # Get target contacts
        if campaign.segment_filter:
            contacts = await self.contact_service.apply_segment_filter(
                segment_filter=campaign.segment_filter,
                organization_id=organization_id,
                campaign_type=campaign.campaign_type,
                limit=None
            )
        else:
            # All contacts
            contacts, _ = await self.contact_service.list_contacts(
                organization_id=organization_id,
                limit=10000  # Max limit
            )

        if not contacts:
            raise ValueError("No contacts match the campaign criteria")

        # Update campaign with target count
        await self.campaigns_collection.update_one(
            {"id": campaign_id},
            {
                "$set": {
                    "target_count": len(contacts),
                    "status": CampaignStatus.RUNNING.value,
                    "started_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Dispatch to appropriate channel
        if campaign.campaign_type == CampaignType.SMS:
            await self._launch_sms_campaign(campaign, contacts, organization_id)
        elif campaign.campaign_type == CampaignType.WHATSAPP:
            await self._launch_whatsapp_campaign(campaign, contacts, organization_id)
        elif campaign.campaign_type == CampaignType.VOICE:
            await self._launch_voice_campaign(campaign, contacts, organization_id)
        elif campaign.campaign_type == CampaignType.EMAIL:
            await self._launch_email_campaign(campaign, contacts, organization_id)

        # Return updated campaign
        return await self.get_campaign(campaign_id, organization_id)

    async def _launch_sms_campaign(
        self,
        campaign: Campaign,
        contacts: List,
        organization_id: str
    ):
        """Launch SMS campaign using Arkesel."""
        logger.info(f"Launching SMS campaign {campaign.id} with {len(contacts)} contacts")

        recipients = []
        for contact in contacts:
            if contact.phone:
                recipients.append({
                    "phone": contact.phone,
                    "name": contact.name or "Customer"
                })

        if not recipients:
            logger.warning(f"No valid phone numbers found for campaign {campaign.id}")
            return

        message_template = campaign.message_template.text_content or ""
        result = await self.sms_service.send_bulk_sms(recipients, message_template)

        await self.campaigns_collection.update_one(
            {"id": campaign.id},
            {
                "$set": {
                    "sent_count": result["sent"],
                    "failed_count": result["failed"],
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"SMS campaign {campaign.id}: {result['sent']} sent, {result['failed']} failed")

    async def _launch_whatsapp_campaign(
        self,
        campaign: Campaign,
        contacts: List,
        organization_id: str
    ):
        """Launch WhatsApp campaign."""
        logger.info(f"Launching WhatsApp campaign {campaign.id} with {len(contacts)} contacts")

        recipients = []
        for contact in contacts:
            if contact.phone:
                recipients.append({
                    "phone": contact.phone,
                    "name": contact.name or "Customer"
                })

        if not recipients:
            logger.warning(f"No valid phone numbers found for WhatsApp campaign {campaign.id}")
            return

        message_template = campaign.message_template.text_content or ""
        result = await self.whatsapp_service.send_bulk_messages(recipients, message_template)

        await self.campaigns_collection.update_one(
            {"id": campaign.id},
            {
                "$set": {
                    "sent_count": result["sent"],
                    "failed_count": result["failed"],
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"WhatsApp campaign {campaign.id}: {result['sent']} sent, {result['failed']} failed")

    async def _launch_voice_campaign(
        self,
        campaign: Campaign,
        contacts: List,
        organization_id: str
    ):
        """Launch Voice campaign using Vapi."""
        logger.info(f"Launching Voice campaign {campaign.id} with {len(contacts)} contacts")

        vapi_assistant_id = campaign.message_template.voice_id
        if not vapi_assistant_id:
            raise ValueError("Vapi assistant ID required for voice campaigns")

        recipients = []
        for contact in contacts:
            if contact.phone:
                recipients.append({
                    "phone": contact.phone,
                    "name": contact.name or "Customer",
                    "data": {
                        "contact_id": contact.id,
                        "property_type_preferences": contact.property_type_preferences or [],
                        "location_preferences": contact.location_preferences or []
                    }
                })

        if not recipients:
            logger.warning(f"No valid phone numbers found for voice campaign {campaign.id}")
            return

        result = await self.vapi_service.make_bulk_calls(recipients, vapi_assistant_id)

        await self.campaigns_collection.update_one(
            {"id": campaign.id},
            {
                "$set": {
                    "sent_count": result["initiated"],
                    "failed_count": result["failed"],
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"Voice campaign {campaign.id}: {result['initiated']} initiated, {result['failed']} failed")

    async def _launch_email_campaign(
        self,
        campaign: Campaign,
        contacts: List,
        organization_id: str
    ):
        """Launch Email campaign via SMTP."""
        logger.info(f"Launching Email campaign {campaign.id} with {len(contacts)} contacts")

        recipients = []
        for contact in contacts:
            if contact.email:
                recipients.append({
                    "email": contact.email,
                    "name": contact.name or "Customer"
                })

        if not recipients:
            logger.warning(f"No valid email addresses found for campaign {campaign.id}")
            return

        subject = campaign.message_template.subject or campaign.name
        html_body = campaign.message_template.html_content
        text_body = campaign.message_template.text_content or ""

        if not html_body and text_body:
            html_body = f"<html><body><p>{text_body}</p></body></html>"

        sent_count = 0
        failed_count = 0

        for recipient in recipients:
            try:
                personalized_subject = subject.replace("{{name}}", recipient["name"])
                personalized_body = (html_body or text_body).replace("{{name}}", recipient["name"])

                result = await self.email_service.send_email(
                    to=recipient["email"],
                    subject=personalized_subject,
                    body=text_body.replace("{{name}}", recipient["name"]),
                    html_body=personalized_body if html_body else None
                )

                if result.get("success"):
                    sent_count += 1
                else:
                    failed_count += 1

                await asyncio.sleep(0.1)
            except Exception as e:
                failed_count += 1
                logger.error(f"Email error to {recipient['email']}: {e}")

        await self.campaigns_collection.update_one(
            {"id": campaign.id},
            {
                "$set": {
                    "sent_count": sent_count,
                    "failed_count": failed_count,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"Email campaign {campaign.id}: {sent_count} sent, {failed_count} failed")

    async def pause_campaign(
        self,
        campaign_id: str,
        organization_id: str
    ) -> Campaign:
        """
        Pause a running campaign.

        Args:
            campaign_id: Campaign ID
            organization_id: Organization ID for access control

        Returns:
            Updated campaign

        Raises:
            ValueError: If campaign cannot be paused
        """
        campaign = await self.get_campaign(campaign_id, organization_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if campaign.status != CampaignStatus.RUNNING:
            raise ValueError(f"Cannot pause campaign in {campaign.status} status")

        # Update status
        await self.campaigns_collection.update_one(
            {"id": campaign_id},
            {
                "$set": {
                    "status": CampaignStatus.PAUSED.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return await self.get_campaign(campaign_id, organization_id)

    async def get_campaign_analytics(
        self,
        campaign_id: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Get campaign analytics.

        Args:
            campaign_id: Campaign ID
            organization_id: Organization ID for access control

        Returns:
            Analytics data
        """
        campaign = await self.get_campaign(campaign_id, organization_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Get message statistics
        pipeline = [
            {"$match": {"campaign_id": campaign_id, "organization_id": organization_id}},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ]

        message_stats = {}
        async for doc in self.messages_collection.aggregate(pipeline):
            message_stats[doc["_id"]] = doc["count"]

        # Calculate metrics
        total_sent = campaign.sent_count
        delivery_rate = (campaign.delivered_count / total_sent * 100) if total_sent > 0 else 0
        failure_rate = (campaign.failed_count / total_sent * 100) if total_sent > 0 else 0

        return {
            "campaign_id": campaign_id,
            "status": campaign.status,
            "target_count": campaign.target_count,
            "sent_count": campaign.sent_count,
            "delivered_count": campaign.delivered_count,
            "opened_count": campaign.opened_count,
            "clicked_count": campaign.clicked_count,
            "failed_count": campaign.failed_count,
            "total_cost": campaign.total_cost,
            "delivery_rate": round(delivery_rate, 2),
            "failure_rate": round(failure_rate, 2),
            "message_stats": message_stats,
            "started_at": campaign.started_at,
            "completed_at": campaign.completed_at
        }
