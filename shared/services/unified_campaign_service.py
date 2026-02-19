"""
Unified Campaign Service

Central orchestrator for multi-channel campaigns across all applications.
Handles campaign CRUD, execution, analytics, and delivery across Voice, SMS, WhatsApp, and Email.

This is the SINGLE service apps should import for complete campaign functionality.

Usage:
    from shared.services.unified_campaign_service import get_unified_campaign_service

    campaign_service = get_unified_campaign_service(db)

    # Create campaign
    campaign = await campaign_service.create_campaign(campaign_data, org_id, user_id)

    # Launch campaign
    await campaign_service.launch_campaign(campaign_id, org_id)

    # Get analytics
    analytics = await campaign_service.get_campaign_analytics(campaign_id, org_id)
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

# Import centralized models
import sys
sys.path.insert(0, '/opt/kasaai/apps')

from shared.models.campaign import (
    Campaign,
    CampaignCreate,
    CampaignUpdate,
    CampaignType,
    CampaignStatus,
    CampaignMessage,
    CampaignMessageStatus,
    CampaignFilters,
    CampaignListResponse,
    CampaignAnalytics,
    SegmentPreview,
    SegmentFilter
)

# Import delivery services
from shared.services.sms_campaign_service import SMSCampaignService
from shared.services.whatsapp_campaign_service import WhatsAppCampaignService
from shared.services.vapi_campaign_service import VapiCampaignService
from shared.services.email_campaign_service import EmailCampaignService

logger = logging.getLogger(__name__)


class UnifiedCampaignService:
    """
    Unified service for managing multi-channel marketing campaigns.

    Provides complete campaign functionality:
    - CRUD operations
    - Contact segmentation
    - Multi-channel delivery (Voice, SMS, WhatsApp, Email)
    - Analytics and reporting
    - Cost tracking
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize unified campaign service.

        Args:
            database: MongoDB database instance
        """
        self.db = database
        self.campaigns_collection = database["campaigns"]
        self.messages_collection = database["campaign_messages"]
        self.contacts_collection = database["contacts"]

        # Initialize channel-specific services
        self._init_delivery_services()

    def _init_delivery_services(self):
        """Initialize all delivery service providers."""
        try:
            self.sms_service = SMSCampaignService(db=self.db)
            logger.info("✅ SMS campaign service initialized")
        except Exception as e:
            logger.warning(f"⚠️  SMS service initialization failed: {e}")
            self.sms_service = None

        try:
            self.whatsapp_service = WhatsAppCampaignService(db=self.db)
            logger.info("✅ WhatsApp campaign service initialized")
        except Exception as e:
            logger.warning(f"⚠️  WhatsApp service initialization failed: {e}")
            self.whatsapp_service = None

        try:
            self.vapi_service = VapiCampaignService(db=self.db)
            logger.info("✅ Vapi voice campaign service initialized")
        except Exception as e:
            logger.warning(f"⚠️  Vapi service initialization failed: {e}")
            self.vapi_service = None

        try:
            self.email_service = EmailCampaignService(db=self.db)
            logger.info("✅ Email campaign service initialized")
        except Exception as e:
            logger.warning(f"⚠️  Email service initialization failed: {e}")
            self.email_service = None

    # ==================== CRUD Operations ====================

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
        campaign_id = str(ObjectId())

        campaign_dict = campaign_data.dict(exclude_none=True)
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

        # Ensure schedule_config and delivery_config have defaults if not provided
        if "schedule_config" not in campaign_dict or campaign_dict["schedule_config"] is None:
            campaign_dict["schedule_config"] = {}
        if "delivery_config" not in campaign_dict or campaign_dict["delivery_config"] is None:
            campaign_dict["delivery_config"] = {}

        await self.campaigns_collection.insert_one(campaign_dict)

        logger.info(f"Created {campaign_data.campaign_type} campaign {campaign_id} for org {organization_id}")

        return Campaign(**campaign_dict)

    def _prepare_campaign_dict(self, campaign_dict: dict) -> dict:
        """Prepare campaign dict from database for Campaign model instantiation."""
        # Ensure schedule_config and delivery_config have defaults if missing or None
        if "schedule_config" not in campaign_dict or campaign_dict["schedule_config"] is None:
            campaign_dict["schedule_config"] = {}
        if "delivery_config" not in campaign_dict or campaign_dict["delivery_config"] is None:
            campaign_dict["delivery_config"] = {}
        return campaign_dict

    async def get_campaign(
        self,
        campaign_id: str,
        organization_id: str
    ) -> Optional[Campaign]:
        """
        Get a campaign by ID.

        Args:
            campaign_id: Campaign ID
            organization_id: Organization ID

        Returns:
            Campaign or None if not found
        """
        campaign_dict = await self.campaigns_collection.find_one({
            "id": campaign_id,
            "organization_id": organization_id
        })

        if not campaign_dict:
            return None

        campaign_dict = self._prepare_campaign_dict(campaign_dict)
        return Campaign(**campaign_dict)

    async def list_campaigns(
        self,
        organization_id: str,
        filters: CampaignFilters
    ) -> CampaignListResponse:
        """
        List campaigns with filters.

        Args:
            organization_id: Organization ID
            filters: Filter criteria

        Returns:
            Campaign list response
        """
        query = {
            "organization_id": organization_id
        }

        # Apply filters
        if filters.campaign_type:
            query["campaign_type"] = filters.campaign_type.value

        if filters.status:
            query["status"] = filters.status.value

        if filters.created_after:
            query.setdefault("created_at", {})["$gte"] = filters.created_after

        if filters.created_before:
            query.setdefault("created_at", {})["$lte"] = filters.created_before

        if filters.search:
            query["name"] = {"$regex": filters.search, "$options": "i"}

        # Get total count
        total = await self.campaigns_collection.count_documents(query)

        # Get campaigns with pagination
        sort_order = -1 if filters.sort_order == "desc" else 1
        cursor = self.campaigns_collection.find(query) \
            .sort(filters.sort_by, sort_order) \
            .skip(filters.offset) \
            .limit(filters.limit)

        campaign_dicts = await cursor.to_list(length=filters.limit)
        campaigns = [Campaign(**self._prepare_campaign_dict(c)) for c in campaign_dicts]

        return CampaignListResponse(
            campaigns=campaigns,
            total=total,
            limit=filters.limit,
            offset=filters.offset,
            has_more=(filters.offset + len(campaigns)) < total
        )

    async def update_campaign(
        self,
        campaign_id: str,
        organization_id: str,
        updates: CampaignUpdate
    ) -> Optional[Campaign]:
        """
        Update a campaign.

        Args:
            campaign_id: Campaign ID
            organization_id: Organization ID
            updates: Update data

        Returns:
            Updated campaign or None if not found
        """
        # Get existing campaign
        campaign = await self.get_campaign(campaign_id, organization_id)
        if not campaign:
            return None

        # Only allow updates for draft campaigns
        if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.PAUSED]:
            raise ValueError(f"Cannot update campaign in {campaign.status} status")

        # Build update dict
        update_dict = updates.dict(exclude_unset=True)
        update_dict["updated_at"] = datetime.utcnow()

        # Update in database
        await self.campaigns_collection.update_one(
            {"id": campaign_id, "organization_id": organization_id},
            {"$set": update_dict}
        )

        return await self.get_campaign(campaign_id, organization_id)

    async def delete_campaign(
        self,
        campaign_id: str,
        organization_id: str
    ) -> bool:
        """
        Delete a campaign.

        Args:
            campaign_id: Campaign ID
            organization_id: Organization ID

        Returns:
            True if deleted
        """
        campaign = await self.get_campaign(campaign_id, organization_id)
        if not campaign:
            return False

        # Only allow deletion for draft campaigns
        if campaign.status != CampaignStatus.DRAFT:
            raise ValueError("Can only delete draft campaigns")

        # Delete campaign and its messages
        await self.campaigns_collection.delete_one({
            "id": campaign_id,
            "organization_id": organization_id
        })
        await self.messages_collection.delete_many({
            "campaign_id": campaign_id
        })

        logger.info(f"Deleted campaign {campaign_id}")
        return True

    # ==================== Segmentation ====================

    async def preview_segment(
        self,
        organization_id: str,
        segment_filter: SegmentFilter,
        campaign_type: CampaignType
    ) -> SegmentPreview:
        """
        Preview how many contacts match the segment filter.

        Args:
            organization_id: Organization ID
            segment_filter: Segment filter criteria
            campaign_type: Campaign type (for opt-out filtering)

        Returns:
            Segment preview with count and sample
        """
        # Build query from segment filter
        query = {
            "organization_id": organization_id,
            "is_deleted": False
        }

        # Apply common filters
        if segment_filter.tags:
            query["tags"] = {"$in": segment_filter.tags}

        if segment_filter.created_after:
            query.setdefault("created_at", {})["$gte"] = segment_filter.created_after

        if segment_filter.created_before:
            query.setdefault("created_at", {})["$lte"] = segment_filter.created_before

        # Channel-specific opt-out filtering
        if segment_filter.exclude_opted_out:
            channel_map = {
                CampaignType.SMS: "sms",
                CampaignType.WHATSAPP: "whatsapp",
                CampaignType.EMAIL: "email",
                CampaignType.VOICE: "voice"
            }
            channel = channel_map.get(campaign_type)
            if channel:
                query["opt_out_channels"] = {"$ne": channel}

        # Apply custom filters (app-specific)
        for key, value in segment_filter.custom_filters.items():
            query[f"custom_data.{key}"] = value

        # Get count
        contact_count = await self.contacts_collection.count_documents(query)

        # Get sample contacts (first 5)
        cursor = self.contacts_collection.find(query).limit(5)
        sample_dicts = await cursor.to_list(length=5)
        sample_contacts = [
            {
                "id": c["id"],
                "name": f"{c.get('first_name', '')} {c.get('last_name', '')}".strip(),
                "email": c.get("email"),
                "phone": c.get("phone")
            }
            for c in sample_dicts
        ]

        # Estimate cost (rough estimates)
        cost_per_message = {
            CampaignType.SMS: 0.05,  # GHS
            CampaignType.WHATSAPP: 0.08,
            CampaignType.EMAIL: 0.01,
            CampaignType.VOICE: 0.50
        }
        estimated_cost = contact_count * cost_per_message.get(campaign_type, 0.05)

        return SegmentPreview(
            contact_count=contact_count,
            estimated_cost=estimated_cost,
            sample_contacts=sample_contacts
        )

    # ==================== Campaign Execution ====================

    async def launch_campaign(
        self,
        campaign_id: str,
        organization_id: str
    ) -> Campaign:
        """
        Launch a campaign.

        Args:
            campaign_id: Campaign ID
            organization_id: Organization ID

        Returns:
            Updated campaign

        Raises:
            ValueError: If campaign cannot be launched
        """
        campaign = await self.get_campaign(campaign_id, organization_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.PAUSED]:
            raise ValueError(f"Cannot launch campaign in {campaign.status} status")

        # Delegate to channel-specific service
        if campaign.campaign_type == CampaignType.SMS:
            if not self.sms_service:
                raise ValueError("SMS service not available")
            await self._launch_sms_campaign(campaign)

        elif campaign.campaign_type == CampaignType.WHATSAPP:
            if not self.whatsapp_service:
                raise ValueError("WhatsApp service not available")
            await self._launch_whatsapp_campaign(campaign)

        elif campaign.campaign_type == CampaignType.VOICE:
            if not self.vapi_service:
                raise ValueError("Voice service not available")
            await self._launch_voice_campaign(campaign)

        elif campaign.campaign_type == CampaignType.EMAIL:
            if not self.email_service:
                raise ValueError("Email service not available")
            await self._launch_email_campaign(campaign)

        # Update campaign status
        await self.campaigns_collection.update_one(
            {"id": campaign_id},
            {
                "$set": {
                    "status": CampaignStatus.RUNNING.value,
                    "started_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        logger.info(f"Launched {campaign.campaign_type} campaign {campaign_id}")

        return await self.get_campaign(campaign_id, organization_id)

    async def pause_campaign(
        self,
        campaign_id: str,
        organization_id: str
    ) -> Campaign:
        """
        Pause a running campaign.

        Args:
            campaign_id: Campaign ID
            organization_id: Organization ID

        Returns:
            Updated campaign
        """
        campaign = await self.get_campaign(campaign_id, organization_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if campaign.status != CampaignStatus.RUNNING:
            raise ValueError("Can only pause running campaigns")

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

        logger.info(f"Paused campaign {campaign_id}")

        return await self.get_campaign(campaign_id, organization_id)

    # ==================== Channel-Specific Launches ====================

    async def _get_contacts_for_campaign(self, campaign: Campaign) -> List[Dict[str, Any]]:
        """
        Fetch contacts for a campaign based on segment filter.

        Args:
            campaign: Campaign with segment filter

        Returns:
            List of contact dictionaries
        """
        query = {"organization_id": campaign.organization_id}

        # Apply segment filters
        if campaign.segment_filter:
            segment = campaign.segment_filter

            # Tags filter
            if segment.tags:
                query["tags"] = {"$in": segment.tags}

            # Date filters
            if segment.created_after:
                query.setdefault("created_at", {})["$gte"] = segment.created_after
            if segment.created_before:
                query.setdefault("created_at", {})["$lte"] = segment.created_before

            # Last contacted filters
            if segment.last_contacted_after:
                query.setdefault("last_contacted", {})["$gte"] = segment.last_contacted_after
            if segment.last_contacted_before:
                query.setdefault("last_contacted", {})["$lte"] = segment.last_contacted_before

            # Exclude opted-out contacts
            if segment.exclude_opted_out:
                # Map campaign type to opt-out channel
                channel_map = {
                    CampaignType.SMS: "sms",
                    CampaignType.WHATSAPP: "whatsapp",
                    CampaignType.EMAIL: "email",
                    CampaignType.VOICE: "voice"
                }
                channel = channel_map.get(campaign.campaign_type)
                if channel:
                    query["opt_out_channels"] = {"$ne": channel}

            # Custom filters (app-specific)
            if segment.custom_filters:
                for key, value in segment.custom_filters.items():
                    query[f"custom_data.{key}"] = value

        # Ensure contacts have required channel info
        if campaign.campaign_type == CampaignType.EMAIL:
            query["email"] = {"$exists": True, "$ne": None, "$ne": ""}
        elif campaign.campaign_type in [CampaignType.SMS, CampaignType.VOICE]:
            query["phone"] = {"$exists": True, "$ne": None, "$ne": ""}
        elif campaign.campaign_type == CampaignType.WHATSAPP:
            query["$or"] = [
                {"whatsapp_number": {"$exists": True, "$ne": None, "$ne": ""}},
                {"phone": {"$exists": True, "$ne": None, "$ne": ""}}
            ]

        # Fetch contacts
        cursor = self.contacts_collection.find(query)
        contacts = []

        async for doc in cursor:
            # Format contact data for channel services
            contact_data = {
                "id": doc.get("id"),
                "first_name": doc.get("first_name", ""),
                "last_name": doc.get("last_name", ""),
                "name": doc.get("name") or f"{doc.get('first_name', '')} {doc.get('last_name', '')}".strip(),
                "email": doc.get("email"),
                "phone": doc.get("phone"),
                "whatsapp_number": doc.get("whatsapp_number"),
                **doc.get("custom_data", {})
            }
            contacts.append(contact_data)

        logger.info(f"Found {len(contacts)} contacts for campaign {campaign.id}")
        return contacts

    async def _launch_sms_campaign(self, campaign: Campaign):
        """
        Launch SMS campaign via SMS service.

        Args:
            campaign: Campaign to launch
        """
        logger.info(f"Launching SMS campaign {campaign.id}")

        # Fetch contacts for campaign
        contacts = await self._get_contacts_for_campaign(campaign)
        if not contacts:
            raise ValueError("No contacts found for campaign segment")

        # Prepare messages
        await self.sms_service.prepare_campaign_messages(campaign_id=campaign.id, contacts=contacts)

        # Launch via SMS service
        await self.sms_service.start_campaign(campaign_id=campaign.id)

        logger.info(f"SMS campaign {campaign.id} launched with {len(contacts)} recipients")

    async def _launch_whatsapp_campaign(self, campaign: Campaign):
        """
        Launch WhatsApp campaign via WhatsApp service.

        Args:
            campaign: Campaign to launch
        """
        logger.info(f"Launching WhatsApp campaign {campaign.id}")

        # Fetch contacts for campaign
        contacts = await self._get_contacts_for_campaign(campaign)
        if not contacts:
            raise ValueError("No contacts found for campaign segment")

        # Prepare messages
        await self.whatsapp_service.prepare_campaign_messages(campaign_id=campaign.id, contacts=contacts)

        # Launch via WhatsApp service
        await self.whatsapp_service.start_campaign(campaign_id=campaign.id)

        logger.info(f"WhatsApp campaign {campaign.id} launched with {len(contacts)} recipients")

    async def _launch_voice_campaign(self, campaign: Campaign):
        """
        Launch Voice campaign via Vapi service.

        Args:
            campaign: Campaign to launch
        """
        logger.info(f"Launching Voice campaign {campaign.id}")

        # Fetch contacts for campaign
        contacts = await self._get_contacts_for_campaign(campaign)
        if not contacts:
            raise ValueError("No contacts found for campaign segment")

        # Prepare messages
        await self.vapi_service.prepare_campaign_messages(campaign_id=campaign.id, contacts=contacts)

        # Launch via Vapi service
        await self.vapi_service.start_campaign(campaign_id=campaign.id)

        logger.info(f"Voice campaign {campaign.id} launched with {len(contacts)} recipients")

    async def _launch_email_campaign(self, campaign: Campaign):
        """
        Launch Email campaign via Email service.

        Args:
            campaign: Campaign to launch
        """
        logger.info(f"Launching Email campaign {campaign.id}")

        # Fetch contacts for campaign
        contacts = await self._get_contacts_for_campaign(campaign)
        if not contacts:
            raise ValueError("No contacts found for campaign segment")

        # Prepare messages
        await self.email_service.prepare_campaign_messages(campaign=campaign, contacts=contacts)

        # Launch via Email service
        await self.email_service.launch_campaign(campaign=campaign)

        logger.info(f"Email campaign {campaign.id} launched with {len(contacts)} recipients")

    # ==================== Analytics ====================

    async def get_campaign_analytics(
        self,
        campaign_id: str,
        organization_id: str
    ) -> Optional[CampaignAnalytics]:
        """
        Get campaign performance analytics.

        Args:
            campaign_id: Campaign ID
            organization_id: Organization ID

        Returns:
            Campaign analytics or None if not found
        """
        campaign = await self.get_campaign(campaign_id, organization_id)
        if not campaign:
            return None

        # Get message statistics
        pipeline = [
            {"$match": {"campaign_id": campaign_id}},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total_cost": {"$sum": "$cost"}
                }
            }
        ]

        status_counts = await self.messages_collection.aggregate(pipeline).to_list(length=None)

        # Count by status
        sent = 0
        delivered = 0
        opened = 0
        clicked = 0
        failed = 0
        pending = 0
        total_cost = 0.0

        for item in status_counts:
            status = item["_id"]
            count = item["count"]
            total_cost += item["total_cost"]

            if status == CampaignMessageStatus.SENT.value:
                sent += count
            elif status == CampaignMessageStatus.DELIVERED.value:
                delivered += count
            elif status == CampaignMessageStatus.OPENED.value:
                opened += count
            elif status == CampaignMessageStatus.CLICKED.value:
                clicked += count
            elif status == CampaignMessageStatus.FAILED.value:
                failed += count
            elif status == CampaignMessageStatus.PENDING.value:
                pending += count

        total_recipients = sent + delivered + opened + clicked + failed + pending

        # Calculate rates
        delivery_rate = (delivered / sent * 100) if sent > 0 else 0.0
        open_rate = (opened / delivered * 100) if delivered > 0 else 0.0
        click_rate = (clicked / opened * 100) if opened > 0 else 0.0
        failure_rate = (failed / sent * 100) if sent > 0 else 0.0

        # Calculate duration
        duration_seconds = None
        if campaign.started_at and campaign.completed_at:
            duration_seconds = (campaign.completed_at - campaign.started_at).total_seconds()

        return CampaignAnalytics(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            campaign_type=campaign.campaign_type,
            status=campaign.status,
            total_recipients=total_recipients,
            sent=sent,
            delivered=delivered,
            opened=opened,
            clicked=clicked,
            failed=failed,
            pending=pending,
            delivery_rate=round(delivery_rate, 2),
            open_rate=round(open_rate, 2),
            click_rate=round(click_rate, 2),
            failure_rate=round(failure_rate, 2),
            total_cost=total_cost,
            cost_per_delivery=round(total_cost / delivered, 2) if delivered > 0 else 0.0,
            started_at=campaign.started_at,
            completed_at=campaign.completed_at,
            duration_seconds=duration_seconds
        )


# Singleton instance
_unified_campaign_service_instance = None


def get_unified_campaign_service(db: AsyncIOMotorDatabase) -> UnifiedCampaignService:
    """Get or create unified campaign service instance."""
    global _unified_campaign_service_instance
    if _unified_campaign_service_instance is None:
        _unified_campaign_service_instance = UnifiedCampaignService(db)
    return _unified_campaign_service_instance
