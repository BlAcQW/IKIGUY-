"""
Vapi Voice Campaign Service

This service handles Vapi voice campaign operations including:
- Campaign creation, management, and execution
- Bulk voice call orchestration with Vapi
- Concurrency management and rate limiting
- Campaign analytics and call tracking
- Integration with Vapi assistants
"""

import asyncio
import logging
import uuid
import httpx
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class VapiCampaignStatus(Enum):
    """Vapi campaign status types."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VapiCallStatus(Enum):
    """Individual Vapi call status."""
    PENDING = "pending"
    CALLING = "calling"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"


@dataclass
class VapiCampaignConfig:
    """Configuration for Vapi campaign execution."""

    max_concurrent_calls: int = 3
    """Maximum number of concurrent calls (Vapi limit is typically 5)."""

    call_delay_seconds: int = 30
    """Delay between initiating calls in seconds."""

    max_retries: int = 2
    """Maximum retry attempts for failed calls."""

    retry_on_no_answer: bool = True
    """Whether to retry calls that receive no answer."""

    retry_delay_hours: int = 2
    """Hours to wait before retrying a failed call."""

    scheduled_time: Optional[datetime] = None
    """Scheduled time to start campaign (None for immediate)."""

    assistant_id: Optional[str] = None
    """Vapi assistant ID to use for calls."""

    phone_number_id: Optional[str] = None
    """Vapi phone number ID to use for outbound calls."""


@dataclass
class VapiCampaignProgress:
    """Progress tracking for Vapi campaign."""

    total_contacts: int = 0
    triggered: int = 0
    called: int = 0
    completed: int = 0
    successful: int = 0
    failed: int = 0
    pending: int = 0
    no_answer: int = 0

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_contacts == 0:
            return 0.0
        return (self.called / self.total_contacts) * 100

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.called == 0:
            return 0.0
        return (self.successful / self.called) * 100


@dataclass
class VapiCampaign:
    """Vapi voice campaign data structure."""

    id: str
    name: str
    organization_id: str
    user_id: str

    # Assistant configuration
    assistant_id: str
    assistant_name: Optional[str] = None
    phone_number_id: Optional[str] = None

    # Campaign configuration
    status: VapiCampaignStatus = VapiCampaignStatus.DRAFT
    config: VapiCampaignConfig = field(default_factory=VapiCampaignConfig)
    progress: VapiCampaignProgress = field(default_factory=VapiCampaignProgress)

    # Cost tracking
    total_cost_usd: float = 0.0
    avg_call_duration: float = 0.0

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Error tracking
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "assistant_id": self.assistant_id,
            "assistant_name": self.assistant_name,
            "phone_number_id": self.phone_number_id,
            "status": self.status.value,
            "config": {
                "max_concurrent_calls": self.config.max_concurrent_calls,
                "call_delay_seconds": self.config.call_delay_seconds,
                "max_retries": self.config.max_retries,
                "retry_on_no_answer": self.config.retry_on_no_answer,
                "retry_delay_hours": self.config.retry_delay_hours,
                "scheduled_time": self.config.scheduled_time.isoformat() if self.config.scheduled_time else None,
                "assistant_id": self.config.assistant_id,
                "phone_number_id": self.config.phone_number_id
            },
            "progress": {
                "total_contacts": self.progress.total_contacts,
                "triggered": self.progress.triggered,
                "called": self.progress.called,
                "completed": self.progress.completed,
                "successful": self.progress.successful,
                "failed": self.progress.failed,
                "pending": self.progress.pending,
                "no_answer": self.progress.no_answer
            },
            "total_cost_usd": self.total_cost_usd,
            "avg_call_duration": self.avg_call_duration,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VapiCampaign":
        """Create from dictionary."""
        config_data = data.get("config", {})
        progress_data = data.get("progress", {})

        config = VapiCampaignConfig(
            max_concurrent_calls=config_data.get("max_concurrent_calls", 3),
            call_delay_seconds=config_data.get("call_delay_seconds", 30),
            max_retries=config_data.get("max_retries", 2),
            retry_on_no_answer=config_data.get("retry_on_no_answer", True),
            retry_delay_hours=config_data.get("retry_delay_hours", 2),
            scheduled_time=datetime.fromisoformat(config_data["scheduled_time"]) if config_data.get("scheduled_time") else None,
            assistant_id=config_data.get("assistant_id"),
            phone_number_id=config_data.get("phone_number_id")
        )

        progress = VapiCampaignProgress(
            total_contacts=progress_data.get("total_contacts", 0),
            triggered=progress_data.get("triggered", 0),
            called=progress_data.get("called", 0),
            completed=progress_data.get("completed", 0),
            successful=progress_data.get("successful", 0),
            failed=progress_data.get("failed", 0),
            pending=progress_data.get("pending", 0),
            no_answer=progress_data.get("no_answer", 0)
        )

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            organization_id=data.get("organization_id", ""),
            user_id=data.get("user_id", ""),
            assistant_id=data.get("assistant_id", ""),
            assistant_name=data.get("assistant_name"),
            phone_number_id=data.get("phone_number_id"),
            status=VapiCampaignStatus(data.get("status", "draft")),
            config=config,
            progress=progress,
            total_cost_usd=data.get("total_cost_usd", 0.0),
            avg_call_duration=data.get("avg_call_duration", 0.0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error_message=data.get("error_message")
        )


class VapiCampaignService:
    """
    Service for managing Vapi voice campaigns.

    Handles campaign creation, execution, and analytics.
    """

    def __init__(self, db=None):
        """
        Initialize Vapi campaign service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.vapi_api_key = os.getenv("VAPI_API_KEY")
        self.vapi_base_url = "https://api.vapi.ai"

        # Running campaigns tracker
        self._running_campaigns: Dict[str, asyncio.Task] = {}

    def set_database(self, db):
        """Set the database instance."""
        self.db = db

    async def create_campaign(
        self,
        name: str,
        organization_id: str,
        user_id: str,
        assistant_id: str,
        phone_number_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> VapiCampaign:
        """
        Create a new Vapi campaign.

        Args:
            name: Campaign name
            organization_id: Organization ID
            user_id: User ID who created the campaign
            assistant_id: Vapi assistant ID
            phone_number_id: Vapi phone number ID (optional)
            config: Optional campaign configuration

        Returns:
            Created campaign
        """
        campaign_id = str(uuid.uuid4())

        # Create configuration
        campaign_config = VapiCampaignConfig(**(config or {}))
        campaign_config.assistant_id = assistant_id
        campaign_config.phone_number_id = phone_number_id

        # Create campaign
        campaign = VapiCampaign(
            id=campaign_id,
            name=name,
            organization_id=organization_id,
            user_id=user_id,
            assistant_id=assistant_id,
            phone_number_id=phone_number_id,
            config=campaign_config
        )

        # Save to database
        if self.db:
            campaigns_collection = self.db["vapi_campaigns"]
            await campaigns_collection.insert_one(campaign.to_dict())

        self.logger.info(f"Created Vapi campaign {campaign_id} for organization {organization_id}")

        return campaign

    async def get_campaign(self, campaign_id: str) -> Optional[VapiCampaign]:
        """
        Get campaign by ID.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign or None if not found
        """
        if not self.db:
            return None

        campaigns_collection = self.db["vapi_campaigns"]
        campaign_doc = await campaigns_collection.find_one({"id": campaign_id})

        if not campaign_doc:
            return None

        campaign_doc.pop("_id", None)
        return VapiCampaign.from_dict(campaign_doc)

    async def initiate_vapi_call(
        self,
        phone_number: str,
        assistant_id: str,
        phone_number_id: Optional[str] = None,
        customer_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initiate a single Vapi call.

        Args:
            phone_number: Phone number to call
            assistant_id: Vapi assistant ID
            phone_number_id: Vapi phone number ID (optional)
            customer_data: Additional customer data to pass to assistant

        Returns:
            Vapi call response data
        """
        if not self.vapi_api_key:
            raise ValueError("VAPI_API_KEY not configured")

        headers = {
            "Authorization": f"Bearer {self.vapi_api_key}",
            "Content-Type": "application/json"
        }

        # Prepare call request
        call_request = {
            "assistantId": assistant_id,
            "customer": {
                "number": phone_number
            }
        }

        # Add phone number ID if provided
        if phone_number_id:
            call_request["phoneNumberId"] = phone_number_id

        # Add customer metadata if provided
        if customer_data:
            call_request["customer"]["extension"] = customer_data

        # Make API request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.vapi_base_url}/call",
                headers=headers,
                json=call_request,
                timeout=30.0
            )

            if response.status_code == 201:
                return response.json()
            else:
                error_msg = f"Vapi call failed: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                raise Exception(error_msg)

    async def start_campaign(
        self,
        campaign_id: str,
        contacts: List[Dict[str, Any]]
    ) -> bool:
        """
        Start executing a Vapi campaign.

        Args:
            campaign_id: Campaign ID
            contacts: List of contacts with phone numbers

        Returns:
            True if started successfully
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")

        if campaign.status not in [VapiCampaignStatus.DRAFT, VapiCampaignStatus.PAUSED]:
            raise ValueError(f"Cannot start campaign with status: {campaign.status.value}")

        # Update campaign status
        if self.db:
            campaigns_collection = self.db["vapi_campaigns"]
            await campaigns_collection.update_one(
                {"id": campaign_id},
                {
                    "$set": {
                        "status": VapiCampaignStatus.RUNNING.value,
                        "started_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "progress.total_contacts": len(contacts)
                    }
                }
            )

        # Start campaign execution in background
        task = asyncio.create_task(self._execute_campaign(campaign_id, contacts, campaign))
        self._running_campaigns[campaign_id] = task

        self.logger.info(f"Started Vapi campaign {campaign_id} with {len(contacts)} contacts")

        return True

    async def _execute_campaign(
        self,
        campaign_id: str,
        contacts: List[Dict[str, Any]],
        campaign: VapiCampaign
    ):
        """
        Execute campaign calls with concurrency management.

        Args:
            campaign_id: Campaign ID
            contacts: List of contacts to call
            campaign: Campaign object
        """
        try:
            max_concurrent = campaign.config.max_concurrent_calls
            call_delay = campaign.config.call_delay_seconds

            # Process contacts in batches
            for i in range(0, len(contacts), max_concurrent):
                batch = contacts[i:i + max_concurrent]

                # Execute batch concurrently
                tasks = [
                    self._make_single_call(campaign_id, contact, campaign)
                    for contact in batch
                ]

                await asyncio.gather(*tasks, return_exceptions=True)

                # Delay before next batch
                if i + max_concurrent < len(contacts):
                    await asyncio.sleep(call_delay)

            # Mark campaign as completed
            if self.db:
                campaigns_collection = self.db["vapi_campaigns"]
                await campaigns_collection.update_one(
                    {"id": campaign_id},
                    {
                        "$set": {
                            "status": VapiCampaignStatus.COMPLETED.value,
                            "completed_at": datetime.utcnow().isoformat(),
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    }
                )

            self.logger.info(f"Completed Vapi campaign {campaign_id}")

        except Exception as e:
            self.logger.error(f"Error executing campaign {campaign_id}: {str(e)}")

            # Mark campaign as failed
            if self.db:
                campaigns_collection = self.db["vapi_campaigns"]
                await campaigns_collection.update_one(
                    {"id": campaign_id},
                    {
                        "$set": {
                            "status": VapiCampaignStatus.FAILED.value,
                            "error_message": str(e),
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    }
                )
        finally:
            # Remove from running campaigns
            self._running_campaigns.pop(campaign_id, None)

    async def _make_single_call(
        self,
        campaign_id: str,
        contact: Dict[str, Any],
        campaign: VapiCampaign
    ):
        """
        Make a single call to a contact.

        Args:
            campaign_id: Campaign ID
            contact: Contact data
            campaign: Campaign object
        """
        try:
            phone = contact.get("phone")
            if not phone:
                self.logger.warning(f"No phone number for contact: {contact.get('id')}")
                return

            # Initiate Vapi call
            call_result = await self.initiate_vapi_call(
                phone_number=phone,
                assistant_id=campaign.assistant_id,
                phone_number_id=campaign.phone_number_id,
                customer_data=contact.get("data", {})
            )

            # Update progress
            if self.db:
                campaigns_collection = self.db["vapi_campaigns"]
                await campaigns_collection.update_one(
                    {"id": campaign_id},
                    {
                        "$inc": {
                            "progress.called": 1,
                            "progress.triggered": 1
                        },
                        "$set": {
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    }
                )

            self.logger.info(f"Call initiated for campaign {campaign_id}: {call_result.get('id')}")

        except Exception as e:
            self.logger.error(f"Error making call for campaign {campaign_id}: {str(e)}")

            # Update failed count
            if self.db:
                campaigns_collection = self.db["vapi_campaigns"]
                await campaigns_collection.update_one(
                    {"id": campaign_id},
                    {
                        "$inc": {"progress.failed": 1},
                        "$set": {"updated_at": datetime.utcnow().isoformat()}
                    }
                )

    async def pause_campaign(self, campaign_id: str) -> VapiCampaign:
        """
        Pause a running campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            Updated campaign
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")

        if campaign.status != VapiCampaignStatus.RUNNING:
            raise ValueError(f"Cannot pause campaign with status: {campaign.status.value}")

        # Cancel running task
        task = self._running_campaigns.get(campaign_id)
        if task:
            task.cancel()
            self._running_campaigns.pop(campaign_id, None)

        # Update status
        if self.db:
            campaigns_collection = self.db["vapi_campaigns"]
            await campaigns_collection.update_one(
                {"id": campaign_id},
                {
                    "$set": {
                        "status": VapiCampaignStatus.PAUSED.value,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                }
            )

        return await self.get_campaign(campaign_id)


# Global service instance
vapi_campaign_service = VapiCampaignService()
