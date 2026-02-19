"""
SMS Campaign Service

This service handles SMS campaign operations including:
- Campaign creation, management, and execution
- Template processing with placeholder substitution
- Bulk SMS sending with rate limiting
- Campaign analytics and tracking
"""

import asyncio
import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Import Slack notifier for failure notifications
try:
    from .slack_notifier import get_slack_notifier
    SLACK_NOTIFICATIONS_ENABLED = True
except ImportError:
    SLACK_NOTIFICATIONS_ENABLED = False
    logger.warning("Slack notifier not available - notifications disabled")


class SMSCampaignStatus(Enum):
    """SMS campaign status types."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SMSMessageStatus(Enum):
    """Individual SMS message status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


@dataclass
class SMSTemplate:
    """SMS message template with placeholder support."""

    id: str
    name: str
    content: str
    placeholders: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Extract placeholders from content."""
        # Find all placeholders in format {{placeholder_name}}
        self.placeholders = re.findall(r'\{\{(\w+)\}\}', self.content)

    def render(self, data: Dict[str, str]) -> str:
        """
        Render template with provided data.

        Args:
            data: Dictionary mapping placeholder names to values

        Returns:
            Rendered message with placeholders replaced
        """
        message = self.content
        for placeholder in self.placeholders:
            value = data.get(placeholder, "")
            message = message.replace(f"{{{{{placeholder}}}}}", str(value))
        return message


@dataclass
class SMSCampaignConfig:
    """Configuration for SMS campaign execution."""

    send_rate_per_second: float = 1.0
    """Rate at which to send SMS messages (messages per second)."""

    batch_size: int = 100
    """Number of messages to process in each batch."""

    retry_failed: bool = True
    """Whether to retry failed messages."""

    max_retries: int = 2
    """Maximum retry attempts for failed messages."""

    retry_delay_seconds: int = 60
    """Delay between retry attempts in seconds."""

    scheduled_time: Optional[datetime] = None
    """Scheduled time to start campaign (None for immediate)."""

    sender_id: Optional[str] = None
    """Sender ID or phone number for SMS."""


@dataclass
class SMSCampaignProgress:
    """Progress tracking for SMS campaign."""

    total_recipients: int = 0
    sent: int = 0
    delivered: int = 0
    failed: int = 0
    pending: int = 0

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_recipients == 0:
            return 0.0
        return ((self.sent + self.failed) / self.total_recipients) * 100

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        total_processed = self.sent + self.failed
        if total_processed == 0:
            return 0.0
        return (self.sent / total_processed) * 100


@dataclass
class SMSCampaign:
    """SMS campaign data structure."""

    id: str
    name: str
    organization_id: str
    user_id: str

    template_id: Optional[str] = None
    template_content: str = ""
    audience_id: Optional[str] = None

    status: SMSCampaignStatus = SMSCampaignStatus.DRAFT
    config: SMSCampaignConfig = field(default_factory=SMSCampaignConfig)
    progress: SMSCampaignProgress = field(default_factory=SMSCampaignProgress)

    # Cost tracking
    total_cost: float = 0.0
    cost_per_sms: float = 0.0

    # Historical tracking (persists across restarts)
    total_messages_sent_all_time: int = 0
    total_cost_all_time: float = 0.0
    total_runs: int = 0

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Error tracking
    error_message: Optional[str] = None

    # Provider info
    sms_provider: str = "twilio"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "template_id": self.template_id,
            "template_content": self.template_content,
            "audience_id": self.audience_id,
            "status": self.status.value,
            "config": {
                "send_rate_per_second": self.config.send_rate_per_second,
                "batch_size": self.config.batch_size,
                "retry_failed": self.config.retry_failed,
                "max_retries": self.config.max_retries,
                "retry_delay_seconds": self.config.retry_delay_seconds,
                "scheduled_time": self.config.scheduled_time.isoformat() if self.config.scheduled_time else None,
                "sender_id": self.config.sender_id
            },
            "progress": {
                "total_recipients": self.progress.total_recipients,
                "sent": self.progress.sent,
                "delivered": self.progress.delivered,
                "failed": self.progress.failed,
                "pending": self.progress.pending
            },
            "total_cost": self.total_cost,
            "cost_per_sms": self.cost_per_sms,
            "total_messages_sent_all_time": self.total_messages_sent_all_time,
            "total_cost_all_time": self.total_cost_all_time,
            "total_runs": self.total_runs,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "sms_provider": self.sms_provider
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SMSCampaign":
        """Create from dictionary."""
        config_data = data.get("config", {})
        progress_data = data.get("progress", {})

        config = SMSCampaignConfig(
            send_rate_per_second=config_data.get("send_rate_per_second", 1.0),
            batch_size=config_data.get("batch_size", 100),
            retry_failed=config_data.get("retry_failed", True),
            max_retries=config_data.get("max_retries", 2),
            retry_delay_seconds=config_data.get("retry_delay_seconds", 60),
            scheduled_time=datetime.fromisoformat(config_data["scheduled_time"]) if config_data.get("scheduled_time") else None,
            sender_id=config_data.get("sender_id")
        )

        progress = SMSCampaignProgress(
            total_recipients=progress_data.get("total_recipients", 0),
            sent=progress_data.get("sent", 0),
            delivered=progress_data.get("delivered", 0),
            failed=progress_data.get("failed", 0),
            pending=progress_data.get("pending", 0)
        )

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            organization_id=data.get("organization_id", ""),
            user_id=data.get("user_id", ""),
            template_id=data.get("template_id"),
            template_content=data.get("template_content", ""),
            audience_id=data.get("audience_id"),
            status=SMSCampaignStatus(data.get("status", "draft")),
            config=config,
            progress=progress,
            total_cost=data.get("total_cost", 0.0),
            cost_per_sms=data.get("cost_per_sms", 0.0),
            total_messages_sent_all_time=data.get("total_messages_sent_all_time", 0),
            total_cost_all_time=data.get("total_cost_all_time", 0.0),
            total_runs=data.get("total_runs", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error_message=data.get("error_message"),
            sms_provider=data.get("sms_provider", "twilio")
        )


@dataclass
class SMSCampaignMessage:
    """Individual message in an SMS campaign."""

    id: str
    campaign_id: str
    recipient_phone: str
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    recipient_data: Dict[str, Any] = field(default_factory=dict)

    message_content: str = ""
    status: SMSMessageStatus = SMSMessageStatus.PENDING

    provider_message_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    error_message: Optional[str] = None
    retry_count: int = 0
    cost: float = 0.0

    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "recipient_phone": self.recipient_phone,
            "recipient_name": self.recipient_name,
            "recipient_email": self.recipient_email,
            "recipient_data": self.recipient_data,
            "message_content": self.message_content,
            "status": self.status.value,
            "provider_message_id": self.provider_message_id,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "cost": self.cost,
            "created_at": self.created_at.isoformat()
        }


class SMSCampaignService:
    """
    Service for managing SMS campaigns.

    Handles campaign creation, execution, and analytics.
    """

    def __init__(self, db=None, sms_provider=None):
        """
        Initialize SMS campaign service.

        Args:
            db: MongoDB database instance
            sms_provider: SMS provider instance (from integration/sms.py)
        """
        self.db = db
        self.sms_provider = sms_provider
        self.logger = logging.getLogger(__name__)

        # Running campaigns tracker
        self._running_campaigns: Dict[str, asyncio.Task] = {}

    def set_database(self, db):
        """Set the database instance."""
        self.db = db

    def set_sms_provider(self, provider):
        """Set the SMS provider instance."""
        self.sms_provider = provider

    async def create_campaign(
        self,
        name: str,
        organization_id: str,
        user_id: str,
        template_content: str,
        audience_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        sms_provider: str = "twilio"
    ) -> SMSCampaign:
        """
        Create a new SMS campaign.

        Args:
            name: Campaign name
            organization_id: Organization ID
            user_id: User ID who created the campaign
            template_content: Message template with placeholders
            audience_id: Optional audience ID
            config: Optional campaign configuration
            sms_provider: SMS provider to use

        Returns:
            Created SMSCampaign
        """
        campaign_id = str(uuid.uuid4())

        campaign_config = SMSCampaignConfig()
        if config:
            campaign_config.send_rate_per_second = config.get("send_rate_per_second", 1.0)
            campaign_config.batch_size = config.get("batch_size", 100)
            campaign_config.retry_failed = config.get("retry_failed", True)
            campaign_config.max_retries = config.get("max_retries", 2)
            campaign_config.sender_id = config.get("sender_id")
            if config.get("scheduled_time"):
                campaign_config.scheduled_time = datetime.fromisoformat(config["scheduled_time"])

        campaign = SMSCampaign(
            id=campaign_id,
            name=name,
            organization_id=organization_id,
            user_id=user_id,
            template_content=template_content,
            audience_id=audience_id,
            config=campaign_config,
            sms_provider=sms_provider
        )

        # Save to database
        if self.db is not None:
            collection = self.db["sms_campaigns"]
            await collection.insert_one(campaign.to_dict())

        self.logger.info(f"Created SMS campaign: {campaign_id}")
        return campaign

    async def get_campaign(self, campaign_id: str) -> Optional[SMSCampaign]:
        """
        Get a campaign by ID.

        Args:
            campaign_id: Campaign ID

        Returns:
            SMSCampaign or None
        """
        if self.db is None:
            return None

        collection = self.db["sms_campaigns"]
        data = await collection.find_one({"id": campaign_id})

        if data:
            return SMSCampaign.from_dict(data)
        return None

    async def list_campaigns(
        self,
        organization_id: str,
        status: Optional[SMSCampaignStatus] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[SMSCampaign]:
        """
        List campaigns for an organization.

        Args:
            organization_id: Organization ID
            status: Optional status filter
            limit: Maximum campaigns to return
            skip: Number of campaigns to skip

        Returns:
            List of SMSCampaign objects
        """
        if self.db is None:
            return []

        collection = self.db["sms_campaigns"]

        query = {"organization_id": organization_id}
        if status:
            query["status"] = status.value

        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        campaigns = []

        async for doc in cursor:
            campaigns.append(SMSCampaign.from_dict(doc))

        return campaigns

    async def update_campaign(
        self,
        campaign_id: str,
        updates: Dict[str, Any]
    ) -> Optional[SMSCampaign]:
        """
        Update a campaign.

        Args:
            campaign_id: Campaign ID
            updates: Dictionary of fields to update

        Returns:
            Updated SMSCampaign or None
        """
        if self.db is None:
            return None

        collection = self.db["sms_campaigns"]

        updates["updated_at"] = datetime.utcnow().isoformat()

        await collection.update_one(
            {"id": campaign_id},
            {"$set": updates}
        )

        return await self.get_campaign(campaign_id)

    async def delete_campaign(self, campaign_id: str) -> bool:
        """
        Delete a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            True if deleted successfully
        """
        if self.db is None:
            return False

        # Stop if running
        if campaign_id in self._running_campaigns:
            self._running_campaigns[campaign_id].cancel()
            del self._running_campaigns[campaign_id]

        collection = self.db["sms_campaigns"]
        result = await collection.delete_one({"id": campaign_id})

        # Also delete messages
        messages_collection = self.db["sms_campaign_messages"]
        await messages_collection.delete_many({"campaign_id": campaign_id})

        return result.deleted_count > 0

    async def archive_campaign_messages(self, campaign_id: str) -> int:
        """
        Archive existing campaign messages to preserve history.

        Moves all messages from sms_campaign_messages to sms_campaign_messages_archive.

        Args:
            campaign_id: Campaign ID

        Returns:
            Number of messages archived
        """
        if self.db is None:
            return 0

        messages_collection = self.db["sms_campaign_messages"]
        archive_collection = self.db["sms_campaign_messages_archive"]

        # Fetch all existing messages for this campaign
        existing_messages = []
        cursor = messages_collection.find({"campaign_id": campaign_id})
        async for msg in cursor:
            # Add archive metadata
            msg["archived_at"] = datetime.utcnow()
            existing_messages.append(msg)

        # Insert into archive
        if existing_messages:
            await archive_collection.insert_many(existing_messages)

            # Delete from active collection
            result = await messages_collection.delete_many({"campaign_id": campaign_id})

            self.logger.info(f"Archived {len(existing_messages)} messages for campaign {campaign_id}")
            return result.deleted_count

        return 0

    async def prepare_campaign_messages(
        self,
        campaign_id: str,
        contacts: List[Dict[str, Any]]
    ) -> int:
        """
        Prepare campaign messages from contact list.

        Deletes any existing pending messages for the campaign before creating new ones
        to avoid duplicates if prepare is called multiple times.

        Args:
            campaign_id: Campaign ID
            contacts: List of contact dictionaries with phone, name, etc.

        Returns:
            Number of messages prepared
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")

        # Delete existing pending messages to avoid duplicates
        if self.db is not None:
            messages_collection = self.db["sms_campaign_messages"]
            delete_result = await messages_collection.delete_many({
                "campaign_id": campaign_id,
                "status": SMSMessageStatus.PENDING.value
            })
            if delete_result.deleted_count > 0:
                self.logger.info(f"Deleted {delete_result.deleted_count} existing pending messages for campaign {campaign_id}")

        template = SMSTemplate(
            id=campaign.template_id or "inline",
            name="Campaign Template",
            content=campaign.template_content
        )

        messages = []
        seen_phones = set()  # Track unique phone numbers to avoid duplicates

        for contact in contacts:
            phone = contact.get("phone", "")
            if not phone:
                continue

            # Skip if we've already processed this phone number
            if phone in seen_phones:
                self.logger.debug(f"Skipping duplicate phone number: {phone}")
                continue

            seen_phones.add(phone)

            # Render message with contact data
            message_content = template.render(contact)

            msg = SMSCampaignMessage(
                id=str(uuid.uuid4()),
                campaign_id=campaign_id,
                recipient_phone=phone,
                recipient_name=contact.get("name"),
                recipient_email=contact.get("email"),
                recipient_data=contact,
                message_content=message_content
            )
            messages.append(msg.to_dict())

        if self.db is not None and messages:
            collection = self.db["sms_campaign_messages"]
            await collection.insert_many(messages)

            # Update campaign progress
            await self.update_campaign(campaign_id, {
                "progress.total_recipients": len(messages),
                "progress.pending": len(messages)
            })

        self.logger.info(f"Prepared {len(messages)} messages for campaign {campaign_id}")
        return len(messages)

    async def start_campaign(self, campaign_id: str, force_resume: bool = False) -> bool:
        """
        Start executing a campaign.

        Args:
            campaign_id: Campaign ID
            force_resume: If True, restart even if status is "running" (for server restarts)

        Returns:
            True if started successfully
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")

        # Check if campaign is already running with an active task
        if campaign.status == SMSCampaignStatus.RUNNING:
            if campaign_id in self._running_campaigns and not force_resume:
                self.logger.warning(f"Campaign {campaign_id} is already running with active task")
                return True
            elif force_resume:
                self.logger.info(f"Force resuming campaign {campaign_id}")
            else:
                # Status is running but no task exists - restart it
                self.logger.info(f"Campaign {campaign_id} status is running but no task found - restarting")

        if campaign.status not in [SMSCampaignStatus.DRAFT, SMSCampaignStatus.PAUSED, SMSCampaignStatus.RUNNING]:
            raise ValueError(f"Cannot start campaign with status: {campaign.status.value}")

        # Update status if not already running
        if campaign.status != SMSCampaignStatus.RUNNING:
            await self.update_campaign(campaign_id, {
                "status": SMSCampaignStatus.RUNNING.value,
                "started_at": datetime.utcnow().isoformat()
            })

        # Start execution task
        task = asyncio.create_task(self._execute_campaign(campaign_id))
        self._running_campaigns[campaign_id] = task

        self.logger.info(f"Started SMS campaign: {campaign_id}")
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

        await self.update_campaign(campaign_id, {
            "status": SMSCampaignStatus.PAUSED.value
        })

        self.logger.info(f"Paused SMS campaign: {campaign_id}")
        return True

    async def cancel_campaign(self, campaign_id: str) -> bool:
        """
        Cancel a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            True if cancelled successfully
        """
        if campaign_id in self._running_campaigns:
            self._running_campaigns[campaign_id].cancel()
            del self._running_campaigns[campaign_id]

        await self.update_campaign(campaign_id, {
            "status": SMSCampaignStatus.CANCELLED.value
        })

        self.logger.info(f"Cancelled SMS campaign: {campaign_id}")
        return True

    async def retry_failed_messages(self, campaign_id: str) -> Dict[str, Any]:
        """
        Retry all failed messages in a campaign.

        This resets failed messages to pending status so they can be retried
        when the campaign is started/resumed.

        Args:
            campaign_id: Campaign ID

        Returns:
            Dictionary with retry statistics
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")

        if self.db is None:
            raise ValueError("Database not initialized")

        messages_collection = self.db["sms_campaign_messages"]

        # Find all failed messages
        failed_messages = await messages_collection.count_documents({
            "campaign_id": campaign_id,
            "status": SMSMessageStatus.FAILED.value
        })

        if failed_messages == 0:
            logger.info(f"No failed messages to retry for campaign {campaign_id}")
            return {
                "success": True,
                "retried_count": 0,
                "message": "No failed messages to retry"
            }

        # Reset failed messages to pending
        result = await messages_collection.update_many(
            {
                "campaign_id": campaign_id,
                "status": SMSMessageStatus.FAILED.value
            },
            {
                "$set": {
                    "status": SMSMessageStatus.PENDING.value,
                    "error_message": None,
                    "failed_at": None
                },
                "$inc": {
                    "retry_count": 1
                }
            }
        )

        # Update campaign progress
        await self.update_campaign(campaign_id, {
            "progress.failed": campaign.progress.failed - failed_messages,
            "progress.pending": campaign.progress.pending + failed_messages
        })

        logger.info(f"Reset {result.modified_count} failed messages to pending for campaign {campaign_id}")

        return {
            "success": True,
            "retried_count": result.modified_count,
            "message": f"Reset {result.modified_count} failed messages to pending"
        }

    async def _fetch_contacts_for_campaign(
        self,
        campaign_id: str,
        audience_id: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch contacts for a campaign, respecting excluded phone numbers.

        This is a helper method used by rerun_campaign to validate contacts exist
        before modifying campaign state.

        Args:
            campaign_id: Campaign ID
            audience_id: Audience ID to fetch contacts from

        Returns:
            List of contact dictionaries ready for message preparation

        Raises:
            ValueError: If database is not initialized
        """
        if self.db is None:
            raise ValueError("Database not initialized")

        # Fetch excluded phone numbers from campaign document
        # (not in dataclass but stored by frontend)
        campaigns_collection = self.db["sms_campaigns"]
        campaign_doc = await campaigns_collection.find_one({"id": campaign_id})
        excluded_phones = set(campaign_doc.get("excluded_phone_numbers", []) if campaign_doc else [])

        # Fetch contacts from audience
        collection = self.db["audience_contacts"]
        cursor = collection.find({"audience_id": audience_id})

        contacts = []
        async for contact in cursor:
            phone = contact.get("phone", "")
            # Skip excluded numbers and empty phones
            if phone and phone not in excluded_phones:
                contacts.append({
                    "phone": phone,
                    "name": contact.get("name", ""),
                    "email": contact.get("email", ""),
                    **contact.get("metadata", {})
                })

        return contacts

    async def rerun_campaign(self, campaign_id: str) -> bool:
        """
        Rerun a completed or failed campaign.

        This method:
        1. Validates campaign status and pre-flight checks (NO state changes yet)
        2. Archives old messages
        3. Prepares new messages
        4. Resets campaign to draft status (AFTER successful preparation)
        5. Starts the campaign

        Args:
            campaign_id: Campaign ID

        Returns:
            True if rerun successfully

        Raises:
            ValueError: If campaign is not in completed/failed/cancelled status,
                       or if database is not initialized,
                       or if no audience/contacts exist
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")

        # Status validation
        if campaign.status not in [SMSCampaignStatus.COMPLETED, SMSCampaignStatus.FAILED, SMSCampaignStatus.CANCELLED]:
            raise ValueError(f"Cannot rerun campaign with status: {campaign.status.value}. Only completed, failed, or cancelled campaigns can be rerun.")

        # Pre-flight validation: Check database
        if self.db is None:
            raise ValueError("Database not initialized")

        # Pre-flight validation: Check audience exists
        if not campaign.audience_id:
            raise ValueError(f"Campaign has no audience. Cannot restart without an audience.")

        self.logger.info(f"Rerunning campaign: {campaign_id}")

        # Pre-flight validation: Fetch and validate contacts BEFORE any state changes
        contacts = await self._fetch_contacts_for_campaign(campaign_id, campaign.audience_id)
        if not contacts or len(contacts) == 0:
            raise ValueError(f"No contacts found in audience. Ensure the audience has contacts before restarting.")

        self.logger.info(f"Pre-flight validation passed: {len(contacts)} contacts found")

        # Archive old messages before resetting
        archived_count = await self.archive_campaign_messages(campaign_id)
        self.logger.info(f"Archived {archived_count} old messages for campaign {campaign_id}")

        # Update historical counters before resetting
        new_total_sent = campaign.total_messages_sent_all_time + campaign.progress.sent
        new_total_cost = campaign.total_cost_all_time + campaign.total_cost
        new_total_runs = campaign.total_runs + 1

        # Prepare messages BEFORE changing status to DRAFT
        # This ensures we only change status if preparation succeeds
        await self.prepare_campaign_messages(campaign_id, contacts)
        self.logger.info(f"Prepared {len(contacts)} messages for campaign {campaign_id}")

        # NOW reset campaign to draft with updated progress
        # At this point, we know contacts exist and messages are prepared
        await self.update_campaign(campaign_id, {
            "status": SMSCampaignStatus.DRAFT.value,
            "progress.total_recipients": len(contacts),
            "progress.sent": 0,
            "progress.failed": 0,
            "progress.pending": len(contacts),
            "total_cost": 0.0,
            "total_messages_sent_all_time": new_total_sent,
            "total_cost_all_time": new_total_cost,
            "total_runs": new_total_runs,
            "started_at": None,
            "completed_at": None
        })

        # Finally start the campaign
        await self.start_campaign(campaign_id)

        self.logger.info(f"Successfully rerun campaign: {campaign_id} with {len(contacts)} messages")
        return True

    async def _execute_campaign(self, campaign_id: str):
        """
        Execute campaign sending with real-time SSE updates.

        Args:
            campaign_id: Campaign ID
        """
        try:
            # Import SSE publisher for real-time updates
            from shared.services.sse_publisher import sse_publisher

            campaign = await self.get_campaign(campaign_id)
            if not campaign or self.sms_provider is None or self.db is None:
                return

            messages_collection = self.db["sms_campaign_messages"]

            # Get pending messages
            cursor = messages_collection.find({
                "campaign_id": campaign_id,
                "status": SMSMessageStatus.PENDING.value
            })

            delay = 1.0 / campaign.config.send_rate_per_second
            sent_count = campaign.progress.sent
            failed_count = campaign.progress.failed
            total_cost = campaign.total_cost
            delivered_count = campaign.progress.delivered
            message_counter = 0  # Track messages for SSE batching

            async for msg_doc in cursor:
                try:
                    # Send SMS
                    result = await self.sms_provider.send_sms(
                        to=msg_doc["recipient_phone"],
                        message=msg_doc["message_content"],
                        from_number=campaign.config.sender_id
                    )

                    if result.get("success"):
                        # Update message status
                        await messages_collection.update_one(
                            {"id": msg_doc["id"]},
                            {"$set": {
                                "status": SMSMessageStatus.SENT.value,
                                "sent_at": datetime.utcnow().isoformat(),
                                "provider_message_id": result.get("message_id"),
                                "cost": result.get("price", 0)
                            }}
                        )
                        sent_count += 1
                        total_cost += result.get("price", 0)
                    else:
                        # Handle failure
                        error_msg = result.get("error", "Unknown error")
                        await messages_collection.update_one(
                            {"id": msg_doc["id"]},
                            {"$set": {
                                "status": SMSMessageStatus.FAILED.value,
                                "failed_at": datetime.utcnow().isoformat(),
                                "error_message": error_msg
                            }}
                        )
                        failed_count += 1

                        # Log the failure
                        logger.warning(
                            f"SMS failed for {msg_doc.get('recipient_name', msg_doc.get('recipient_phone'))}: {error_msg}"
                        )

                        # Send Slack notification for SMS failure
                        if SLACK_NOTIFICATIONS_ENABLED:
                            try:
                                slack = get_slack_notifier()
                                success = await slack.notify_sms_failure(
                                    campaign_id=campaign_id,
                                    campaign_name=campaign.name,
                                    error_message=error_msg,
                                    organization_id=campaign.organization_id,
                                    recipient_phone=msg_doc.get("recipient_phone"),
                                    provider=campaign.sms_provider
                                )
                                if success:
                                    logger.info(f"Slack notification sent for failed SMS to {msg_doc.get('recipient_phone')}")
                                else:
                                    logger.error(f"Slack notification failed to send for {msg_doc.get('recipient_phone')}")
                            except Exception as slack_error:
                                logger.error(f"Failed to send Slack notification: {slack_error}", exc_info=True)

                    # Update campaign progress periodically
                    await self.update_campaign(campaign_id, {
                        "progress.sent": sent_count,
                        "progress.failed": failed_count,
                        "progress.pending": campaign.progress.total_recipients - sent_count - failed_count,
                        "total_cost": total_cost
                    })

                    # Publish SSE update every 10 messages (configurable)
                    message_counter += 1
                    if message_counter % 10 == 0:
                        await sse_publisher.publish(
                            campaign_id,
                            "sms_progress",
                            {
                                "id": campaign_id,
                                "campaign_id": campaign_id,
                                "status": campaign.status.value,
                                "progress": {
                                    "total_recipients": campaign.progress.total_recipients,
                                    "sent": sent_count,
                                    "delivered": delivered_count,
                                    "failed": failed_count,
                                    "pending": campaign.progress.total_recipients - sent_count - failed_count
                                },
                                "total_cost": total_cost
                            }
                        )

                    # Rate limiting
                    await asyncio.sleep(delay)

                except asyncio.CancelledError:
                    self.logger.info(f"Campaign {campaign_id} execution cancelled")
                    return
                except Exception as e:
                    self.logger.error(f"Error sending message: {e}")
                    failed_count += 1

            # Campaign completed
            await self.update_campaign(campaign_id, {
                "status": SMSCampaignStatus.COMPLETED.value,
                "completed_at": datetime.utcnow().isoformat(),
                "progress.sent": sent_count,
                "progress.failed": failed_count,
                "progress.pending": 0,
                "total_cost": total_cost
            })

            # Publish final SSE update
            await sse_publisher.publish(
                campaign_id,
                "sms_progress",
                {
                    "id": campaign_id,
                    "campaign_id": campaign_id,
                    "status": SMSCampaignStatus.COMPLETED.value,
                    "progress": {
                        "total_recipients": campaign.progress.total_recipients,
                        "sent": sent_count,
                        "delivered": delivered_count,
                        "failed": failed_count,
                        "pending": 0
                    },
                    "total_cost": total_cost
                }
            )

            # Cleanup SSE subscribers
            await sse_publisher.cleanup_campaign(campaign_id)

            self.logger.info(f"Campaign {campaign_id} completed: {sent_count} sent, {failed_count} failed")

        except asyncio.CancelledError:
            self.logger.info(f"Campaign {campaign_id} execution cancelled")
            # Cleanup SSE on cancellation
            await sse_publisher.cleanup_campaign(campaign_id)
        except Exception as e:
            self.logger.error(f"Campaign execution error: {e}")
            await self.update_campaign(campaign_id, {
                "status": SMSCampaignStatus.FAILED.value,
                "error_message": str(e)
            })

            # Send Slack notification for campaign failure
            if SLACK_NOTIFICATIONS_ENABLED:
                try:
                    slack = get_slack_notifier()
                    success = await slack.notify_sms_failure(
                        campaign_id=campaign_id,
                        campaign_name=campaign.name,
                        error_message=f"Campaign execution failed: {str(e)}",
                        organization_id=campaign.organization_id,
                        provider=campaign.sms_provider
                    )
                    if success:
                        logger.info(f"Slack notification sent for campaign failure: {campaign_id}")
                    else:
                        logger.error(f"Slack notification failed for campaign: {campaign_id}")
                except Exception as slack_error:
                    logger.error(f"Failed to send Slack notification: {slack_error}", exc_info=True)

            # Publish error event (include progress to prevent frontend crashes)
            await sse_publisher.publish(
                campaign_id,
                "campaign_error",
                {
                    "id": campaign_id,
                    "campaign_id": campaign_id,
                    "status": SMSCampaignStatus.FAILED.value,
                    "progress": {
                        "total_recipients": campaign.progress.total_recipients,
                        "sent": campaign.progress.sent,
                        "delivered": campaign.progress.delivered,
                        "failed": campaign.progress.failed,
                        "pending": campaign.progress.pending
                    },
                    "total_cost": campaign.total_cost,
                    "error_message": str(e)
                }
            )

            # Cleanup SSE subscribers
            await sse_publisher.cleanup_campaign(campaign_id)
        finally:
            if campaign_id in self._running_campaigns:
                del self._running_campaigns[campaign_id]

    async def get_campaign_messages(
        self,
        campaign_id: str,
        status: Optional[SMSMessageStatus] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a campaign.

        Args:
            campaign_id: Campaign ID
            status: Optional status filter
            limit: Maximum messages to return
            skip: Number to skip

        Returns:
            List of message dictionaries
        """
        if self.db is None:
            return []

        collection = self.db["sms_campaign_messages"]

        query = {"campaign_id": campaign_id}
        if status:
            query["status"] = status.value

        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        messages = []

        async for doc in cursor:
            messages.append(doc)

        return messages

    async def get_campaign_analytics(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get analytics for a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            Analytics dictionary
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return {}

        return {
            "campaign_id": campaign_id,
            "name": campaign.name,
            "status": campaign.status.value,
            "progress": {
                "total": campaign.progress.total_recipients,
                "sent": campaign.progress.sent,
                "delivered": campaign.progress.delivered,
                "failed": campaign.progress.failed,
                "pending": campaign.progress.pending,
                "progress_percentage": campaign.progress.progress_percentage,
                "success_rate": campaign.progress.success_rate
            },
            "cost": {
                "total": campaign.total_cost,
                "per_sms": campaign.cost_per_sms if campaign.progress.sent > 0 else 0,
                "average": campaign.total_cost / campaign.progress.sent if campaign.progress.sent > 0 else 0
            },
            "timing": {
                "created_at": campaign.created_at.isoformat(),
                "started_at": campaign.started_at.isoformat() if campaign.started_at else None,
                "completed_at": campaign.completed_at.isoformat() if campaign.completed_at else None,
                "duration_seconds": (campaign.completed_at - campaign.started_at).total_seconds() if campaign.started_at and campaign.completed_at else None
            }
        }


# Create singleton instance
sms_campaign_service = SMSCampaignService()
