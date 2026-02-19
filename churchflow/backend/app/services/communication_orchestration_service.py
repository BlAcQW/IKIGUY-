"""
Communication Orchestration Service.

Coordinates multi-channel automated communications including SMS, WhatsApp,
and voice calls for visitor tracking and discipleship journeys.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from bson import ObjectId

from app.core.database import get_database
from app.models.user import User
from app.models.scheduled_communication import ScheduledCommunication

logger = logging.getLogger(__name__)


class CommunicationOrchestrationService:
    """
    Service for orchestrating multi-channel communications.

    Handles:
    - Sending scheduled communications via SMS, WhatsApp, Voice
    - Template rendering with personalization
    - Deduplication to prevent spam
    - Engagement metrics tracking
    - Integration with existing campaign services
    """

    def __init__(self):
        """Initialize the communication orchestration service."""
        self.db = None
        self.sms_campaign_service = None
        self.whatsapp_campaign_service = None
        self.vapi_service = None

    def set_database(self, db):
        """Set the database connection."""
        self.db = db

    def set_services(self, sms_service=None, whatsapp_service=None, vapi_service=None):
        """
        Set communication service instances.

        Args:
            sms_service: SMS campaign service instance
            whatsapp_service: WhatsApp campaign service instance
            vapi_service: VAPI voice service instance
        """
        self.sms_campaign_service = sms_service
        self.whatsapp_campaign_service = whatsapp_service
        self.vapi_service = vapi_service

    async def send_scheduled_communication(
        self,
        scheduled_comm: ScheduledCommunication
    ) -> Dict[str, Any]:
        """
        Send a scheduled communication via configured channels.

        Routes to appropriate service (SMS, WhatsApp, Voice) based on
        the channels specified in the scheduled communication.

        Args:
            scheduled_comm: Scheduled communication object

        Returns:
            dict: Result with status and details

        Raises:
            Exception: If all channels fail
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Sending scheduled communication {scheduled_comm.id} via {scheduled_comm.channels}")

        try:
            # Fetch user
            user_doc = await self.db.users.find_one({"_id": scheduled_comm.user_id})
            if not user_doc:
                raise ValueError(f"User {scheduled_comm.user_id} not found")

            user = User(**user_doc)

            # Check if user allows automated communications
            if not user.allow_automated_communications:
                logger.info(f"User {user.id} has opted out of automated communications")
                return {
                    "status": "skipped",
                    "reason": "User opted out of automated communications"
                }

            # Check deduplication
            is_duplicate = await self.check_deduplication(
                user_id=str(user.id),
                message_type=scheduled_comm.followup_type,
                hours=24
            )

            if is_duplicate:
                logger.info(f"Duplicate communication detected for user {user.id}")
                return {
                    "status": "skipped",
                    "reason": "Duplicate within 24 hours"
                }

            # Render message template
            message = self.render_template(
                scheduled_comm.message_template,
                scheduled_comm.template_variables
            )

            # Send via each channel
            campaign_ids = {}
            errors = []

            for channel in scheduled_comm.channels:
                try:
                    if channel == "sms":
                        campaign_id = await self.send_via_sms(
                            user=user,
                            message=message,
                            organization_id=str(scheduled_comm.organization_id)
                        )
                        campaign_ids["sms"] = campaign_id
                    elif channel == "whatsapp":
                        campaign_id = await self.send_via_whatsapp(
                            user=user,
                            message=message,
                            organization_id=str(scheduled_comm.organization_id)
                        )
                        campaign_ids["whatsapp"] = campaign_id
                    elif channel == "voice":
                        call_id = await self.send_via_voice(
                            user=user,
                            script=message,
                            organization_id=str(scheduled_comm.organization_id)
                        )
                        campaign_ids["voice"] = call_id
                    else:
                        logger.warning(f"Unknown channel: {channel}")

                except Exception as e:
                    logger.error(f"Failed to send via {channel}: {e}")
                    errors.append({"channel": channel, "error": str(e)})

            # Update user engagement metrics
            await self._update_engagement_metrics(user.id, scheduled_comm.channels)

            if campaign_ids:
                return {
                    "status": "success",
                    "campaign_ids": campaign_ids,
                    "channels_sent": list(campaign_ids.keys()),
                    "errors": errors if errors else None
                }
            else:
                return {
                    "status": "failed",
                    "error": "All channels failed",
                    "errors": errors
                }

        except Exception as e:
            logger.error(f"Error sending scheduled communication: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    async def send_via_sms(
        self,
        user: User,
        message: str,
        organization_id: str
    ) -> str:
        """
        Send SMS using existing SMS campaign service.

        Args:
            user: User to send to
            message: Message content
            organization_id: Organization ID

        Returns:
            str: Campaign ID

        Raises:
            Exception: If SMS sending fails
        """
        logger.info(f"Sending SMS to {user.phone}")

        # Initialize SMS campaign service if needed
        if not self.sms_campaign_service:
            from shared.services.sms_campaign_service import sms_campaign_service
            self.sms_campaign_service = sms_campaign_service
            self.sms_campaign_service.set_database(self.db)

            # Set SMS provider
            from shared.integration.sms import sms_client
            self.sms_campaign_service.set_sms_provider(sms_client)

        # Create campaign
        campaign = await self.sms_campaign_service.create_campaign(
            name=f"Auto: {user.phone} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            organization_id=organization_id,
            user_id=str(user.id),
            template_content=message,
            config={
                "send_rate_per_second": 1.0
            }
        )

        # Add contact to campaign
        await self.sms_campaign_service.add_contact_to_campaign(
            campaign_id=campaign.id,
            phone_number=user.phone,
            contact_data={
                "name": user.full_name or user.name,
                "user_id": str(user.id)
            }
        )

        # Send campaign
        await self.sms_campaign_service.send_campaign(campaign_id=campaign.id)

        logger.info(f"SMS campaign {campaign.id} sent successfully")

        return campaign.id

    async def send_via_whatsapp(
        self,
        user: User,
        message: str,
        organization_id: str
    ) -> str:
        """
        Send WhatsApp using existing WhatsApp campaign service.

        Args:
            user: User to send to
            message: Message content
            organization_id: Organization ID

        Returns:
            str: Campaign ID

        Raises:
            Exception: If WhatsApp sending fails
        """
        logger.info(f"Sending WhatsApp to {user.phone}")

        # Initialize WhatsApp campaign service if needed
        if not self.whatsapp_campaign_service:
            from shared.services.whatsapp_campaign_service import whatsapp_campaign_service
            self.whatsapp_campaign_service = whatsapp_campaign_service
            self.whatsapp_campaign_service.set_database(self.db)

            # Set WhatsApp provider
            from shared.integration.whatsapp_business import whatsapp_business_client
            self.whatsapp_campaign_service.set_whatsapp_provider(whatsapp_business_client)

        # Create campaign
        campaign = await self.whatsapp_campaign_service.create_campaign(
            name=f"Auto: {user.phone} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            organization_id=organization_id,
            user_id=str(user.id),
            template_content=message,
            config={
                "send_rate_per_second": 1.0
            }
        )

        # Add contact to campaign
        await self.whatsapp_campaign_service.add_contact_to_campaign(
            campaign_id=campaign.id,
            phone_number=user.phone,
            contact_data={
                "name": user.full_name or user.name,
                "user_id": str(user.id)
            }
        )

        # Send campaign
        await self.whatsapp_campaign_service.send_campaign(campaign_id=campaign.id)

        logger.info(f"WhatsApp campaign {campaign.id} sent successfully")

        return campaign.id

    async def send_via_voice(
        self,
        user: User,
        script: str,
        organization_id: str,
        assistant_id: Optional[str] = None
    ) -> str:
        """
        Send voice call using VAPI.

        Args:
            user: User to call
            script: Voice script/prompt
            organization_id: Organization ID
            assistant_id: Optional VAPI assistant ID (will create default if not provided)

        Returns:
            str: Call ID

        Raises:
            Exception: If voice call initiation fails
        """
        logger.info(f"Initiating voice call to {user.phone}")

        # Initialize VAPI service if needed
        if not self.vapi_service:
            from shared.integration.vapi import VAPIService
            from app.core.config import settings

            vapi_config = {
                "VAPI_API_KEY": settings.vapi_api_key,
                "VAPI_US_PHONE_ID": settings.vapi_phone_number_id
            }
            self.vapi_service = VAPIService(config=vapi_config)

        # Get or create assistant for discipleship calls
        if not assistant_id:
            assistant_id = await self._get_or_create_discipleship_assistant(script)

        # Initiate call
        result = await self.vapi_service.initiate_call(
            to_number=user.phone,
            assistant_id=assistant_id,
            metadata={
                "user_id": str(user.id),
                "organization_id": organization_id,
                "call_type": "discipleship",
                "script": script
            }
        )

        if not result.get("success"):
            raise Exception(f"VAPI call failed: {result.get('error')}")

        call_id = result.get("call_id")
        logger.info(f"Voice call {call_id} initiated successfully")

        return call_id

    async def _get_or_create_discipleship_assistant(self, script: str) -> str:
        """
        Get or create VAPI assistant for discipleship calls.

        Args:
            script: Voice script

        Returns:
            str: Assistant ID
        """
        # Check if discipleship assistant exists
        if self.db is None:
            self.db = get_database()

        assistant_doc = await self.db.vapi_assistants.find_one({
            "name": "ChurchFlow Discipleship Assistant"
        })

        if assistant_doc:
            return assistant_doc["assistant_id"]

        # Create new assistant
        from shared.integration.vapi import VAPIAgent

        agent = VAPIAgent(
            name="ChurchFlow Discipleship Assistant",
            description="Assistant for discipleship and pastoral care calls",
            system_prompt=f"""You are a friendly church discipleship assistant. Your role is to:
1. Welcome members warmly
2. Share important information about church events and groups
3. Invite them to participate in church activities
4. Answer basic questions about the church
5. Provide encouragement and support

{script}

Keep calls brief (2-3 minutes), be warm and genuine, and always be respectful.""",
            voice="alloy",
            language="en",
            speed=1.0,
            max_duration=300,  # 5 minutes max
            interruptible=True,
            record_calls=True
        )

        # Create assistant via VAPI API
        result = await self.vapi_service.create_assistant(agent)

        if not result.get("success"):
            raise Exception(f"Failed to create VAPI assistant: {result.get('error')}")

        assistant_id = result.get("assistant_id")

        # Save to database
        await self.db.vapi_assistants.insert_one({
            "name": "ChurchFlow Discipleship Assistant",
            "assistant_id": assistant_id,
            "created_at": datetime.utcnow()
        })

        return assistant_id

    def render_template(self, template: str, variables: Dict[str, str]) -> str:
        """
        Render message template with variables.

        Replaces {{variable}} placeholders with actual values.

        Args:
            template: Message template with {{placeholders}}
            variables: Dictionary of variable values

        Returns:
            str: Rendered message

        Example:
            template = "Hi {{name}}! Welcome to {{church_name}}."
            variables = {"name": "John", "church_name": "Victory Church"}
            Result: "Hi John! Welcome to Victory Church."
        """
        message = template

        # Find all placeholders
        placeholders = re.findall(r'\{\{(\w+)\}\}', template)

        # Replace each placeholder
        for placeholder in placeholders:
            value = variables.get(placeholder, "")
            message = message.replace(f"{{{{{placeholder}}}}}", str(value))

        return message

    async def check_deduplication(
        self,
        user_id: str,
        message_type: str,
        hours: int = 24
    ) -> bool:
        """
        Check if similar message was sent recently.

        Prevents duplicate messages within time window.

        Args:
            user_id: User ID
            message_type: Type of message (welcome, day_1, etc.)
            hours: Time window in hours (default: 24)

        Returns:
            bool: True if duplicate found, False otherwise
        """
        if self.db is None:
            self.db = get_database()

        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # Check for recent messages
        recent_comm = await self.db.scheduled_communications.find_one({
            "user_id": ObjectId(user_id),
            "followup_type": message_type,
            "sent_at": {"$gte": cutoff_time},
            "status": "sent"
        })

        return recent_comm is not None

    async def _update_engagement_metrics(
        self,
        user_id: ObjectId,
        channels: List[str]
    ):
        """
        Update user engagement metrics.

        Tracks count of SMS, WhatsApp, and voice calls sent.

        Args:
            user_id: User ID
            channels: List of channels used
        """
        if self.db is None:
            self.db = get_database()

        # Build update document
        update_data = {"updated_at": datetime.utcnow()}

        if "sms" in channels:
            update_data["sms_sent_count"] = 1  # Will be incremented
        if "whatsapp" in channels:
            update_data["whatsapp_sent_count"] = 1
        if "voice" in channels:
            update_data["calls_made_count"] = 1

        # Increment metrics
        await self.db.users.update_one(
            {"_id": user_id},
            {
                "$inc": {
                    "sms_sent_count": 1 if "sms" in channels else 0,
                    "whatsapp_sent_count": 1 if "whatsapp" in channels else 0,
                    "calls_made_count": 1 if "voice" in channels else 0
                },
                "$set": {"last_contact_date": datetime.utcnow()}
            }
        )

    async def send_bulk_communication(
        self,
        user_ids: List[str],
        message_template: str,
        template_variables: Dict[str, str],
        channels: List[str],
        organization_id: str,
        created_by_user_id: str
    ) -> Dict[str, Any]:
        """
        Send bulk communication to multiple users.

        Creates scheduled communications for immediate sending.

        Args:
            user_ids: List of user IDs
            message_template: Message template
            template_variables: Base template variables (will be personalized per user)
            channels: Communication channels to use
            organization_id: Organization ID
            created_by_user_id: ID of user creating the communication

        Returns:
            dict: Summary with success/failure counts
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Sending bulk communication to {len(user_ids)} users via {channels}")

        success_count = 0
        failure_count = 0
        errors = []

        for user_id in user_ids:
            try:
                # Fetch user for personalization
                user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
                if not user_doc:
                    failure_count += 1
                    errors.append({"user_id": user_id, "error": "User not found"})
                    continue

                user = User(**user_doc)

                # Personalize template variables
                personalized_vars = template_variables.copy()
                personalized_vars["name"] = user.full_name or user.name or "Friend"

                # Create scheduled communication
                scheduled_comm = ScheduledCommunication(
                    organization_id=ObjectId(organization_id),
                    user_id=ObjectId(user_id),
                    followup_type="manual",
                    scheduled_for=datetime.utcnow(),  # Send immediately
                    channels=channels,
                    message_template=message_template,
                    template_variables=personalized_vars,
                    status="pending",
                    created_by_user_id=ObjectId(created_by_user_id)
                )

                # Save to database
                result = await self.db.scheduled_communications.insert_one(
                    scheduled_comm.dict(by_alias=True, exclude={"id"})
                )

                # Send immediately
                scheduled_comm.id = result.inserted_id
                await self.send_scheduled_communication(scheduled_comm)

                success_count += 1

            except Exception as e:
                failure_count += 1
                errors.append({"user_id": user_id, "error": str(e)})
                logger.error(f"Failed to send to user {user_id}: {e}")

        summary = {
            "total": len(user_ids),
            "success": success_count,
            "failure": failure_count,
            "errors": errors if errors else None
        }

        logger.info(f"Bulk communication complete: {success_count} success, {failure_count} failure")

        return summary


# Global instance
communication_orchestration_service = CommunicationOrchestrationService()
