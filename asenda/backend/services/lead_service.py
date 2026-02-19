"""
Lead management service for Asenda.ai
"""

import logging
from datetime import datetime
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from ..models.lead import (
    Lead,
    LeadCreate,
    LeadSource,
    LeadStatus,
    DemoRequest,
    MeetingSchedule,
    NewsletterSubscribe,
)
from .email_service import EmailService

logger = logging.getLogger(__name__)


class LeadService:
    """Service for managing leads."""

    def __init__(
        self,
        mongo_uri: str,
        database_name: str = "asenda",
        email_service: Optional[EmailService] = None,
    ):
        """
        Initialize the lead service.

        Args:
            mongo_uri: MongoDB connection URI
            database_name: Name of the database
            email_service: Email service instance for sending confirmations
        """
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db = self.client[database_name]
        self.leads_collection = self.db["leads"]
        self.newsletter_collection = self.db["newsletter_subscribers"]
        self.email_service = email_service

    async def create_lead(self, lead_data: LeadCreate) -> str:
        """
        Create a new lead from contact form.

        Args:
            lead_data: Lead creation data

        Returns:
            str: ID of the created lead
        """
        lead = Lead(
            name=lead_data.name,
            email=lead_data.email,
            company=lead_data.company,
            phone=lead_data.phone,
            message=lead_data.message,
            source=lead_data.source,
            services_interested=lead_data.services_interested,
            company_size=lead_data.company_size,
            industry=lead_data.industry,
        )

        lead_dict = lead.model_dump(exclude={"id"})
        result = await self.leads_collection.insert_one(lead_dict)
        lead_id = str(result.inserted_id)

        # Send confirmation email
        if self.email_service:
            email_sent = self.email_service.send_contact_confirmation(
                to_email=lead_data.email,
                name=lead_data.name,
                message=lead_data.message,
            )
            if email_sent:
                await self.leads_collection.update_one(
                    {"_id": result.inserted_id},
                    {"$set": {"email_sent": True}}
                )
            # Send internal notification
            self.email_service.send_internal_notification(
                lead_type="contact",
                lead_data=lead_dict,
            )

        logger.info(f"Created lead {lead_id} from contact form")
        return lead_id

    async def create_demo_request(self, demo_data: DemoRequest) -> str:
        """
        Create a new demo request.

        Args:
            demo_data: Demo request data

        Returns:
            str: ID of the created lead
        """
        lead = Lead(
            name=demo_data.name,
            email=demo_data.email,
            company=demo_data.company,
            phone=demo_data.phone,
            job_title=demo_data.job_title,
            company_size=demo_data.company_size,
            use_case=demo_data.use_case,
            preferred_date=demo_data.preferred_date,
            preferred_time=demo_data.preferred_time,
            timezone=demo_data.timezone,
            source=LeadSource.DEMO_REQUEST,
            status=LeadStatus.NEW,
        )

        lead_dict = lead.model_dump(exclude={"id"})
        result = await self.leads_collection.insert_one(lead_dict)
        lead_id = str(result.inserted_id)

        # Send confirmation email
        if self.email_service:
            email_sent = self.email_service.send_demo_confirmation(
                to_email=demo_data.email,
                name=demo_data.name,
                company=demo_data.company,
                preferred_date=demo_data.preferred_date,
                preferred_time=demo_data.preferred_time,
            )
            if email_sent:
                await self.leads_collection.update_one(
                    {"_id": result.inserted_id},
                    {"$set": {"email_sent": True}}
                )
            # Send internal notification
            self.email_service.send_internal_notification(
                lead_type="demo_request",
                lead_data=lead_dict,
            )

        logger.info(f"Created demo request {lead_id}")
        return lead_id

    async def create_meeting_schedule(self, meeting_data: MeetingSchedule) -> str:
        """
        Create a new meeting schedule request.

        Args:
            meeting_data: Meeting schedule data

        Returns:
            str: ID of the created lead
        """
        lead = Lead(
            name=meeting_data.name,
            email=meeting_data.email,
            company=meeting_data.company,
            phone=meeting_data.phone,
            meeting_type=meeting_data.meeting_type,
            timezone=meeting_data.timezone,
            notes=meeting_data.notes,
            source=LeadSource.MEETING_SCHEDULE,
            status=LeadStatus.NEW,
        )

        # Handle preferred datetime
        if meeting_data.preferred_datetime:
            lead.preferred_date = meeting_data.preferred_datetime.strftime("%Y-%m-%d")
            lead.preferred_time = meeting_data.preferred_datetime.strftime("%H:%M")

        lead_dict = lead.model_dump(exclude={"id"})
        result = await self.leads_collection.insert_one(lead_dict)
        lead_id = str(result.inserted_id)

        # Send confirmation email
        if self.email_service:
            datetime_str = None
            if meeting_data.preferred_datetime:
                datetime_str = meeting_data.preferred_datetime.strftime("%B %d, %Y at %I:%M %p")

            email_sent = self.email_service.send_meeting_confirmation(
                to_email=meeting_data.email,
                name=meeting_data.name,
                meeting_type=meeting_data.meeting_type,
                preferred_datetime=datetime_str,
            )
            if email_sent:
                await self.leads_collection.update_one(
                    {"_id": result.inserted_id},
                    {"$set": {"email_sent": True}}
                )
            # Send internal notification
            self.email_service.send_internal_notification(
                lead_type="meeting_schedule",
                lead_data=lead_dict,
            )

        logger.info(f"Created meeting schedule {lead_id}")
        return lead_id

    async def subscribe_newsletter(self, subscribe_data: NewsletterSubscribe) -> str:
        """
        Subscribe to newsletter.

        Args:
            subscribe_data: Newsletter subscription data

        Returns:
            str: ID of the subscription or existing subscription
        """
        # Check if already subscribed
        existing = await self.newsletter_collection.find_one(
            {"email": subscribe_data.email}
        )
        if existing:
            return str(existing["_id"])

        subscription = {
            "email": subscribe_data.email,
            "name": subscribe_data.name,
            "subscribed_at": datetime.utcnow(),
            "active": True,
        }

        result = await self.newsletter_collection.insert_one(subscription)
        subscription_id = str(result.inserted_id)

        # Also create a lead record
        lead = Lead(
            name=subscribe_data.name or "Newsletter Subscriber",
            email=subscribe_data.email,
            source=LeadSource.NEWSLETTER,
            status=LeadStatus.NEW,
        )
        lead_dict = lead.model_dump(exclude={"id"})
        await self.leads_collection.insert_one(lead_dict)

        # Send welcome email
        if self.email_service:
            self.email_service.send_newsletter_welcome(
                to_email=subscribe_data.email,
                name=subscribe_data.name,
            )

        logger.info(f"Newsletter subscription created: {subscription_id}")
        return subscription_id

    async def get_lead(self, lead_id: str) -> Optional[Lead]:
        """
        Get a lead by ID.

        Args:
            lead_id: Lead ID

        Returns:
            Lead object or None if not found
        """
        try:
            doc = await self.leads_collection.find_one({"_id": ObjectId(lead_id)})
            if doc:
                doc["id"] = str(doc.pop("_id"))
                return Lead(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting lead {lead_id}: {str(e)}")
            return None

    async def get_leads(
        self,
        source: Optional[LeadSource] = None,
        status: Optional[LeadStatus] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> List[Lead]:
        """
        Get leads with optional filtering.

        Args:
            source: Filter by lead source
            status: Filter by lead status
            limit: Maximum number of leads to return
            skip: Number of leads to skip

        Returns:
            List of Lead objects
        """
        query = {}
        if source:
            query["source"] = source.value
        if status:
            query["status"] = status.value

        cursor = self.leads_collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        leads = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            leads.append(Lead(**doc))
        return leads

    async def update_lead_status(
        self,
        lead_id: str,
        status: LeadStatus,
    ) -> bool:
        """
        Update lead status.

        Args:
            lead_id: Lead ID
            status: New status

        Returns:
            bool: True if updated successfully
        """
        try:
            result = await self.leads_collection.update_one(
                {"_id": ObjectId(lead_id)},
                {
                    "$set": {
                        "status": status.value,
                        "updated_at": datetime.utcnow(),
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating lead {lead_id}: {str(e)}")
            return False
