"""
WhatsApp Campaign Service

This service handles WhatsApp campaign operations including:
- Campaign creation, management, and execution
- Template processing with WhatsApp Business API
- Bulk WhatsApp message sending with rate limiting
- Media and interactive button support
- Campaign analytics and delivery tracking
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


class WhatsAppCampaignStatus(Enum):
    """WhatsApp campaign status types."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WhatsAppMessageStatus(Enum):
    """Individual WhatsApp message status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


@dataclass
class WhatsAppTemplate:
    """WhatsApp Business API template with placeholder support."""

    id: str
    name: str
    language: str
    category: str
    status: str  # APPROVED, PENDING, REJECTED, DISABLED
    components: List[Dict[str, Any]] = field(default_factory=list)
    placeholders: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def extract_placeholders(self):
        """Extract placeholders from template components."""
        placeholders = []
        for component in self.components:
            if component.get("type") == "BODY":
                text = component.get("text", "")
                # WhatsApp uses {{1}}, {{2}} format
                placeholders.extend(re.findall(r'\{\{(\d+)\}\}', text))
        self.placeholders = placeholders


@dataclass
class WhatsAppCampaignConfig:
    """Configuration for WhatsApp campaign execution."""

    send_rate_per_second: float = 1.0
    """Rate at which to send WhatsApp messages (messages per second)."""

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

    # WhatsApp-specific configuration
    template_id: Optional[str] = None
    """WhatsApp template ID."""

    template_name: Optional[str] = None
    """WhatsApp template name."""

    enable_media: bool = False
    """Enable media attachments."""

    media_url: Optional[str] = None
    """Media URL (if enable_media is True)."""

    media_type: Optional[str] = None
    """Media type: image, video, audio, document."""

    media_caption: Optional[str] = None
    """Media caption."""

    enable_buttons: bool = False
    """Enable interactive buttons."""

    buttons: List[Dict[str, Any]] = field(default_factory=list)
    """Interactive buttons configuration."""

    phone_number_id: str = ""
    """WhatsApp Business phone number ID."""


@dataclass
class WhatsAppCampaignProgress:
    """Progress tracking for WhatsApp campaign."""

    total_recipients: int = 0
    sent: int = 0
    delivered: int = 0
    read: int = 0
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

    @property
    def delivery_rate(self) -> float:
        """Calculate delivery rate percentage."""
        if self.sent == 0:
            return 0.0
        return (self.delivered / self.sent) * 100

    @property
    def read_rate(self) -> float:
        """Calculate read rate percentage."""
        if self.delivered == 0:
            return 0.0
        return (self.read / self.delivered) * 100


@dataclass
class WhatsAppCampaign:
    """WhatsApp campaign data structure."""

    id: str
    name: str
    organization_id: str
    user_id: str

    template_id: Optional[str] = None
    template_name: Optional[str] = None
    template_content: str = ""
    audience_id: Optional[str] = None

    status: WhatsAppCampaignStatus = WhatsAppCampaignStatus.DRAFT
    config: WhatsAppCampaignConfig = field(default_factory=WhatsAppCampaignConfig)
    progress: WhatsAppCampaignProgress = field(default_factory=WhatsAppCampaignProgress)

    # Cost tracking
    total_cost: float = 0.0
    cost_per_message: float = 0.0055  # Default WhatsApp Business API cost

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Error tracking
    error_message: Optional[str] = None

    # WhatsApp-specific
    whatsapp_business_account_id: str = ""
    phone_number_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "template_id": self.template_id,
            "template_name": self.template_name,
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
                "template_id": self.config.template_id,
                "template_name": self.config.template_name,
                "enable_media": self.config.enable_media,
                "media_url": self.config.media_url,
                "media_type": self.config.media_type,
                "media_caption": self.config.media_caption,
                "enable_buttons": self.config.enable_buttons,
                "buttons": self.config.buttons,
                "phone_number_id": self.config.phone_number_id
            },
            "progress": {
                "total_recipients": self.progress.total_recipients,
                "sent": self.progress.sent,
                "delivered": self.progress.delivered,
                "read": self.progress.read,
                "failed": self.progress.failed,
                "pending": self.progress.pending
            },
            "total_cost": self.total_cost,
            "cost_per_message": self.cost_per_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "whatsapp_business_account_id": self.whatsapp_business_account_id,
            "phone_number_id": self.phone_number_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WhatsAppCampaign":
        """Create from dictionary."""
        config_data = data.get("config", {})
        progress_data = data.get("progress", {})

        config = WhatsAppCampaignConfig(
            send_rate_per_second=config_data.get("send_rate_per_second", 1.0),
            batch_size=config_data.get("batch_size", 100),
            retry_failed=config_data.get("retry_failed", True),
            max_retries=config_data.get("max_retries", 2),
            retry_delay_seconds=config_data.get("retry_delay_seconds", 60),
            scheduled_time=datetime.fromisoformat(config_data["scheduled_time"]) if config_data.get("scheduled_time") else None,
            template_id=config_data.get("template_id"),
            template_name=config_data.get("template_name"),
            enable_media=config_data.get("enable_media", False),
            media_url=config_data.get("media_url"),
            media_type=config_data.get("media_type"),
            media_caption=config_data.get("media_caption"),
            enable_buttons=config_data.get("enable_buttons", False),
            buttons=config_data.get("buttons", []),
            phone_number_id=config_data.get("phone_number_id", "")
        )

        progress = WhatsAppCampaignProgress(
            total_recipients=progress_data.get("total_recipients", 0),
            sent=progress_data.get("sent", 0),
            delivered=progress_data.get("delivered", 0),
            read=progress_data.get("read", 0),
            failed=progress_data.get("failed", 0),
            pending=progress_data.get("pending", 0)
        )

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            organization_id=data.get("organization_id", ""),
            user_id=data.get("user_id", ""),
            template_id=data.get("template_id"),
            template_name=data.get("template_name"),
            template_content=data.get("template_content", ""),
            audience_id=data.get("audience_id"),
            status=WhatsAppCampaignStatus(data.get("status", "draft")),
            config=config,
            progress=progress,
            total_cost=data.get("total_cost", 0.0),
            cost_per_message=data.get("cost_per_message", 0.0055),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error_message=data.get("error_message"),
            whatsapp_business_account_id=data.get("whatsapp_business_account_id", ""),
            phone_number_id=data.get("phone_number_id", "")
        )


@dataclass
class WhatsAppCampaignMessage:
    """Individual message in a WhatsApp campaign."""

    id: str
    campaign_id: str
    recipient_phone: str
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    recipient_data: Dict[str, Any] = field(default_factory=dict)

    message_content: str = ""
    template_name: Optional[str] = None
    template_variables: Dict[str, Any] = field(default_factory=dict)

    status: WhatsAppMessageStatus = WhatsAppMessageStatus.PENDING

    # WhatsApp-specific
    provider_message_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    # Media
    media_url: Optional[str] = None
    media_id: Optional[str] = None
    media_caption: Optional[str] = None

    # Buttons
    buttons: List[Dict[str, Any]] = field(default_factory=list)

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
            "template_name": self.template_name,
            "template_variables": self.template_variables,
            "status": self.status.value,
            "provider_message_id": self.provider_message_id,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "media_url": self.media_url,
            "media_id": self.media_id,
            "media_caption": self.media_caption,
            "buttons": self.buttons,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "cost": self.cost,
            "created_at": self.created_at.isoformat()
        }


class WhatsAppCampaignService:
    """
    Service for managing WhatsApp campaigns.

    Handles campaign creation, execution, template management, and analytics.
    Uses WhatsApp Business API for sending messages.
    """

    def __init__(self, db=None, whatsapp_provider=None):
        """
        Initialize WhatsApp campaign service.

        Args:
            db: MongoDB database instance
            whatsapp_provider: WhatsApp Business API provider instance
        """
        self.db = db
        self.whatsapp_provider = whatsapp_provider
        self.logger = logging.getLogger(__name__)

        # Running campaigns tracker
        self._running_campaigns: Dict[str, asyncio.Task] = {}

    def set_database(self, db):
        """Set the database instance."""
        self.db = db

    def set_whatsapp_provider(self, provider):
        """Set the WhatsApp provider instance."""
        self.whatsapp_provider = provider

    async def create_campaign(
        self,
        name: str,
        organization_id: str,
        user_id: str,
        template_name: str,
        audience_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        phone_number_id: Optional[str] = None
    ) -> WhatsAppCampaign:
        """
        Create a new WhatsApp campaign.

        Args:
            name: Campaign name
            organization_id: Organization ID
            user_id: User ID who created the campaign
            template_name: WhatsApp template name
            audience_id: Optional audience ID
            config: Optional campaign configuration
            phone_number_id: WhatsApp Business phone number ID

        Returns:
            Created WhatsAppCampaign
        """
        campaign_id = str(uuid.uuid4())

        campaign_config = WhatsAppCampaignConfig()
        if config:
            campaign_config.send_rate_per_second = config.get("send_rate_per_second", 1.0)
            campaign_config.batch_size = config.get("batch_size", 100)
            campaign_config.retry_failed = config.get("retry_failed", True)
            campaign_config.max_retries = config.get("max_retries", 2)
            campaign_config.template_name = config.get("template_name", template_name)
            campaign_config.enable_media = config.get("enable_media", False)
            campaign_config.media_url = config.get("media_url")
            campaign_config.media_type = config.get("media_type")
            campaign_config.media_caption = config.get("media_caption")
            campaign_config.enable_buttons = config.get("enable_buttons", False)
            campaign_config.buttons = config.get("buttons", [])
            campaign_config.phone_number_id = phone_number_id or config.get("phone_number_id", "")
            if config.get("scheduled_time"):
                campaign_config.scheduled_time = datetime.fromisoformat(config["scheduled_time"])

        campaign = WhatsAppCampaign(
            id=campaign_id,
            name=name,
            organization_id=organization_id,
            user_id=user_id,
            template_name=template_name,
            audience_id=audience_id,
            config=campaign_config,
            phone_number_id=phone_number_id or ""
        )

        # Save to database
        if self.db is not None:
            collection = self.db["whatsapp_campaigns"]
            await collection.insert_one(campaign.to_dict())

        self.logger.info(f"Created WhatsApp campaign: {campaign_id}")
        return campaign

    async def get_campaign(self, campaign_id: str) -> Optional[WhatsAppCampaign]:
        """
        Get a campaign by ID.

        Args:
            campaign_id: Campaign ID

        Returns:
            WhatsAppCampaign or None
        """
        if self.db is None:
            return None

        collection = self.db["whatsapp_campaigns"]
        data = await collection.find_one({"id": campaign_id})

        if data:
            return WhatsAppCampaign.from_dict(data)
        return None

    async def list_campaigns(
        self,
        organization_id: str,
        status: Optional[WhatsAppCampaignStatus] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[WhatsAppCampaign]:
        """
        List campaigns for an organization.

        Args:
            organization_id: Organization ID
            status: Optional status filter
            limit: Maximum campaigns to return
            skip: Number of campaigns to skip

        Returns:
            List of WhatsAppCampaign objects
        """
        if self.db is None:
            return []

        collection = self.db["whatsapp_campaigns"]

        query = {"organization_id": organization_id}
        if status:
            query["status"] = status.value

        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        campaigns = []

        async for doc in cursor:
            campaigns.append(WhatsAppCampaign.from_dict(doc))

        return campaigns

    async def update_campaign(
        self,
        campaign_id: str,
        updates: Dict[str, Any]
    ) -> Optional[WhatsAppCampaign]:
        """
        Update a campaign.

        Args:
            campaign_id: Campaign ID
            updates: Dictionary of fields to update

        Returns:
            Updated WhatsAppCampaign or None
        """
        if self.db is None:
            return None

        collection = self.db["whatsapp_campaigns"]

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

        collection = self.db["whatsapp_campaigns"]
        result = await collection.delete_one({"id": campaign_id})

        # Also delete messages
        messages_collection = self.db["whatsapp_campaign_messages"]
        await messages_collection.delete_many({"campaign_id": campaign_id})

        return result.deleted_count > 0

    async def get_templates(self) -> List[WhatsAppTemplate]:
        """
        Get WhatsApp templates from cache or API.

        Returns:
            List of WhatsAppTemplate objects
        """
        if self.db is None:
            return []

        # Try to get from cache first
        collection = self.db["whatsapp_templates"]
        cursor = collection.find({"status": "APPROVED"})
        templates = []

        async for doc in cursor:
            template = WhatsAppTemplate(
                id=doc.get("id", ""),
                name=doc.get("name", ""),
                language=doc.get("language", "en"),
                category=doc.get("category", ""),
                status=doc.get("status", ""),
                components=doc.get("components", [])
            )
            template.extract_placeholders()
            templates.append(template)

        return templates

    async def sync_templates(self) -> int:
        """
        Sync templates from WhatsApp Business API to local cache.

        Returns:
            Number of templates synced
        """
        if self.whatsapp_provider is None or self.db is None:
            return 0

        try:
            # Get templates from WhatsApp Business API
            templates = await self.whatsapp_provider.get_templates()

            collection = self.db["whatsapp_templates"]

            # Update cache
            for template in templates:
                template_dict = {
                    "id": template.name,  # Use name as ID
                    "name": template.name,
                    "language": template.language,
                    "category": template.category,
                    "status": template.status.value if hasattr(template.status, 'value') else template.status,
                    "components": template.components,
                    "updated_at": datetime.utcnow().isoformat()
                }

                await collection.update_one(
                    {"id": template.name},
                    {"$set": template_dict},
                    upsert=True
                )

            self.logger.info(f"Synced {len(templates)} WhatsApp templates")
            return len(templates)

        except Exception as e:
            self.logger.error(f"Failed to sync templates: {e}")
            return 0

    async def prepare_campaign_messages(
        self,
        campaign_id: str,
        contacts: List[Dict[str, Any]]
    ) -> int:
        """
        Prepare campaign messages from contact list.

        Args:
            campaign_id: Campaign ID
            contacts: List of contact dictionaries with phone, name, etc.

        Returns:
            Number of messages prepared
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")

        messages = []
        for contact in contacts:
            phone = contact.get("phone", "")
            if not phone:
                continue

            # Prepare template variables from contact data
            template_variables = {
                "name": contact.get("name", ""),
                "email": contact.get("email", ""),
                **contact.get("custom_fields", {})
            }

            msg = WhatsAppCampaignMessage(
                id=str(uuid.uuid4()),
                campaign_id=campaign_id,
                recipient_phone=phone,
                recipient_name=contact.get("name"),
                recipient_email=contact.get("email"),
                recipient_data=contact,
                template_name=campaign.template_name,
                template_variables=template_variables,
                media_url=campaign.config.media_url,
                media_caption=campaign.config.media_caption,
                buttons=campaign.config.buttons
            )
            messages.append(msg.to_dict())

        if self.db is not None and messages:
            collection = self.db["whatsapp_campaign_messages"]
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
            force_resume: If True, restart even if status is "running"

        Returns:
            True if started successfully
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")

        # Check if campaign is already running
        if campaign.status == WhatsAppCampaignStatus.RUNNING:
            if campaign_id in self._running_campaigns and not force_resume:
                self.logger.warning(f"Campaign {campaign_id} is already running")
                return True
            elif force_resume:
                self.logger.info(f"Force resuming campaign {campaign_id}")
            else:
                self.logger.info(f"Campaign {campaign_id} status is running but no task found - restarting")

        if campaign.status not in [WhatsAppCampaignStatus.DRAFT, WhatsAppCampaignStatus.PAUSED, WhatsAppCampaignStatus.RUNNING]:
            raise ValueError(f"Cannot start campaign with status: {campaign.status.value}")

        # Update status if not already running
        if campaign.status != WhatsAppCampaignStatus.RUNNING:
            await self.update_campaign(campaign_id, {
                "status": WhatsAppCampaignStatus.RUNNING.value,
                "started_at": datetime.utcnow().isoformat()
            })

        # Start execution task
        task = asyncio.create_task(self._execute_campaign(campaign_id))
        self._running_campaigns[campaign_id] = task

        self.logger.info(f"Started WhatsApp campaign: {campaign_id}")
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
            "status": WhatsAppCampaignStatus.PAUSED.value
        })

        self.logger.info(f"Paused WhatsApp campaign: {campaign_id}")
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
            "status": WhatsAppCampaignStatus.CANCELLED.value
        })

        self.logger.info(f"Cancelled WhatsApp campaign: {campaign_id}")
        return True

    async def _execute_campaign(self, campaign_id: str):
        """
        Execute campaign sending.

        Args:
            campaign_id: Campaign ID
        """
        try:
            campaign = await self.get_campaign(campaign_id)
            if not campaign or self.whatsapp_provider is None or self.db is None:
                return

            messages_collection = self.db["whatsapp_campaign_messages"]

            # Get pending messages
            cursor = messages_collection.find({
                "campaign_id": campaign_id,
                "status": WhatsAppMessageStatus.PENDING.value
            })

            delay = 1.0 / campaign.config.send_rate_per_second
            sent_count = campaign.progress.sent
            failed_count = campaign.progress.failed
            total_cost = campaign.total_cost

            async for msg_doc in cursor:
                try:
                    # Prepare template components
                    components = []
                    if msg_doc.get("template_variables"):
                        body_params = []
                        for key, value in msg_doc["template_variables"].items():
                            body_params.append({
                                "type": "text",
                                "text": str(value)
                            })

                        if body_params:
                            components.append({
                                "type": "body",
                                "parameters": body_params
                            })

                    # Get template from cache
                    template_name = msg_doc.get("template_name", campaign.template_name)
                    templates = await self.get_templates()
                    template = next((t for t in templates if t.name == template_name), None)

                    if not template:
                        self.logger.warning(f"Template {template_name} not found in cache")
                        # Mark as failed
                        await messages_collection.update_one(
                            {"id": msg_doc["id"]},
                            {"$set": {
                                "status": WhatsAppMessageStatus.FAILED.value,
                                "failed_at": datetime.utcnow().isoformat(),
                                "error_message": f"Template {template_name} not found"
                            }}
                        )
                        failed_count += 1
                        continue

                    # Send WhatsApp message using template
                    result = await self.whatsapp_provider.send_template_message(
                        to_number=msg_doc["recipient_phone"],
                        template=template,
                        components=components
                    )

                    # Calculate cost (base + media if applicable)
                    message_cost = campaign.cost_per_message
                    if msg_doc.get("media_url"):
                        message_cost += 0.0100  # Additional cost for media

                    # Update message status
                    await messages_collection.update_one(
                        {"id": msg_doc["id"]},
                        {"$set": {
                            "status": WhatsAppMessageStatus.SENT.value,
                            "sent_at": datetime.utcnow().isoformat(),
                            "provider_message_id": result.id if result else None,
                            "cost": message_cost
                        }}
                    )
                    sent_count += 1
                    total_cost += message_cost

                    # Update campaign progress periodically
                    await self.update_campaign(campaign_id, {
                        "progress.sent": sent_count,
                        "progress.failed": failed_count,
                        "progress.pending": campaign.progress.total_recipients - sent_count - failed_count,
                        "total_cost": total_cost
                    })

                    # Rate limiting
                    await asyncio.sleep(delay)

                except asyncio.CancelledError:
                    self.logger.info(f"Campaign {campaign_id} execution cancelled")
                    return
                except Exception as e:
                    self.logger.error(f"Error sending WhatsApp message: {e}")
                    # Mark as failed
                    await messages_collection.update_one(
                        {"id": msg_doc["id"]},
                        {"$set": {
                            "status": WhatsAppMessageStatus.FAILED.value,
                            "failed_at": datetime.utcnow().isoformat(),
                            "error_message": str(e)
                        }}
                    )
                    failed_count += 1

            # Campaign completed
            await self.update_campaign(campaign_id, {
                "status": WhatsAppCampaignStatus.COMPLETED.value,
                "completed_at": datetime.utcnow().isoformat(),
                "progress.sent": sent_count,
                "progress.failed": failed_count,
                "progress.pending": 0,
                "total_cost": total_cost
            })

            self.logger.info(f"Campaign {campaign_id} completed: {sent_count} sent, {failed_count} failed")

        except asyncio.CancelledError:
            self.logger.info(f"Campaign {campaign_id} execution cancelled")
        except Exception as e:
            self.logger.error(f"Campaign execution error: {e}")
            await self.update_campaign(campaign_id, {
                "status": WhatsAppCampaignStatus.FAILED.value,
                "error_message": str(e)
            })
        finally:
            if campaign_id in self._running_campaigns:
                del self._running_campaigns[campaign_id]

    async def process_delivery_status(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Process WhatsApp delivery status webhook.

        Args:
            webhook_data: Webhook data from WhatsApp Business API

        Returns:
            True if processed successfully
        """
        if self.db is None:
            return False

        try:
            # Extract status update from webhook
            entry = webhook_data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            statuses = value.get("statuses", [])

            if not statuses:
                return True

            messages_collection = self.db["whatsapp_campaign_messages"]

            for status in statuses:
                message_id = status.get("id")
                status_value = status.get("status")
                timestamp = status.get("timestamp")

                if not message_id or not status_value:
                    continue

                # Find message by provider_message_id
                msg = await messages_collection.find_one({"provider_message_id": message_id})
                if not msg:
                    continue

                # Update message status
                update_data = {}

                if status_value == "delivered":
                    update_data["status"] = WhatsAppMessageStatus.DELIVERED.value
                    update_data["delivered_at"] = datetime.utcnow().isoformat()

                    # Update campaign progress
                    campaign = await self.get_campaign(msg["campaign_id"])
                    if campaign:
                        await self.update_campaign(msg["campaign_id"], {
                            "progress.delivered": campaign.progress.delivered + 1
                        })

                elif status_value == "read":
                    update_data["status"] = WhatsAppMessageStatus.READ.value
                    update_data["read_at"] = datetime.utcnow().isoformat()

                    # Update campaign progress
                    campaign = await self.get_campaign(msg["campaign_id"])
                    if campaign:
                        await self.update_campaign(msg["campaign_id"], {
                            "progress.read": campaign.progress.read + 1
                        })

                elif status_value == "failed":
                    update_data["status"] = WhatsAppMessageStatus.FAILED.value
                    update_data["failed_at"] = datetime.utcnow().isoformat()
                    update_data["error_message"] = status.get("errors", [{}])[0].get("message", "Unknown error")

                if update_data:
                    await messages_collection.update_one(
                        {"id": msg["id"]},
                        {"$set": update_data}
                    )

            return True

        except Exception as e:
            self.logger.error(f"Failed to process delivery status: {e}")
            return False

    async def get_campaign_messages(
        self,
        campaign_id: str,
        status: Optional[WhatsAppMessageStatus] = None,
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

        collection = self.db["whatsapp_campaign_messages"]

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
                "read": campaign.progress.read,
                "failed": campaign.progress.failed,
                "pending": campaign.progress.pending,
                "progress_percentage": campaign.progress.progress_percentage,
                "success_rate": campaign.progress.success_rate,
                "delivery_rate": campaign.progress.delivery_rate,
                "read_rate": campaign.progress.read_rate
            },
            "cost": {
                "total": campaign.total_cost,
                "per_message": campaign.cost_per_message,
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
whatsapp_campaign_service = WhatsAppCampaignService()
