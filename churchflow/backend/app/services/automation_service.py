"""
Automation Service

Handles automated workflows and reminder sequences for ChurchFlow.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import logging

from app.models.automation import (
    AutomationWorkflow,
    ScheduledReminder,
    AutomationLog,
    AutomationType,
    ReminderStep,
    EventReminderConfig,
    ReminderTiming,
    NotificationChannel,
    AutomationStatus
)

logger = logging.getLogger(__name__)


class AutomationService:
    """
    Service for managing automated workflows and reminder sequences.

    Features:
    - Event reminder automation (7d, 3d, 1d before)
    - Member onboarding sequences
    - Post-event follow-up
    - Scheduled message delivery
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.workflows_collection = db.automation_workflows
        self.reminders_collection = db.scheduled_reminders
        self.logs_collection = db.automation_logs

    async def create_workflow(
        self,
        organization_id: str,
        user_id: str,
        automation_type: AutomationType,
        name: str,
        description: Optional[str] = None,
        event_reminder_config: Optional[EventReminderConfig] = None,
        conference_id: Optional[str] = None,
        **kwargs
    ) -> AutomationWorkflow:
        """
        Create a new automation workflow.

        Args:
            organization_id: Organization identifier
            user_id: User creating the workflow
            automation_type: Type of automation
            name: Workflow name
            description: Optional description
            event_reminder_config: Configuration for event reminders
            conference_id: Optional conference to associate with

        Returns:
            Created automation workflow
        """
        workflow = AutomationWorkflow(
            organization_id=organization_id,
            automation_type=automation_type,
            name=name,
            description=description,
            event_reminder_config=event_reminder_config,
            conference_id=conference_id,
            created_by=user_id,
            status=AutomationStatus.ACTIVE
        )

        result = await self.workflows_collection.insert_one(workflow.model_dump(by_alias=True, exclude={"id"}))
        workflow.id = str(result.inserted_id)

        # Log creation
        await self._log_event(
            workflow_id=workflow.id,
            organization_id=organization_id,
            event_type="workflow_created",
            message=f"Automation workflow '{name}' created",
            metadata={"automation_type": automation_type}
        )

        logger.info(f"Created automation workflow: {workflow.id} for organization: {organization_id}")
        return workflow

    async def create_default_event_reminder_workflow(
        self,
        organization_id: str,
        user_id: str,
        conference_id: str,
        conference_name: str
    ) -> AutomationWorkflow:
        """
        Create a default event reminder workflow with standard timing.

        Default reminders:
        - 7 days before
        - 3 days before
        - 1 day before

        Args:
            organization_id: Organization identifier
            user_id: User creating the workflow
            conference_id: Conference to send reminders for
            conference_name: Conference name for templates

        Returns:
            Created automation workflow
        """
        # Default reminder steps
        reminder_steps = [
            ReminderStep(
                timing=ReminderTiming.SEVEN_DAYS,
                days_before=7,
                channel=NotificationChannel.SMS,
                message_template=f"📅 {conference_name} is coming up next week! Get ready for an amazing time. We can't wait to see you!",
                enabled=True
            ),
            ReminderStep(
                timing=ReminderTiming.THREE_DAYS,
                days_before=3,
                channel=NotificationChannel.SMS,
                message_template=f"🎉 {conference_name} is this weekend! Don't forget to prepare your heart for a powerful encounter.",
                enabled=True
            ),
            ReminderStep(
                timing=ReminderTiming.ONE_DAY,
                days_before=1,
                channel=NotificationChannel.SMS,
                message_template=f"⏰ {conference_name} is TOMORROW! Save your QR code for quick check-in. See you soon!",
                enabled=True
            )
        ]

        config = EventReminderConfig(
            enabled=True,
            reminder_steps=reminder_steps,
            send_to_registered_only=True,
            include_qr_code=True,
            include_venue_details=True
        )

        return await self.create_workflow(
            organization_id=organization_id,
            user_id=user_id,
            automation_type=AutomationType.EVENT_REMINDER,
            name=f"Event Reminders - {conference_name}",
            description="Automated reminder sequence for conference attendees",
            event_reminder_config=config,
            conference_id=conference_id
        )

    async def schedule_conference_reminders(
        self,
        workflow_id: str,
        conference_id: str,
        organization_id: str
    ) -> List[ScheduledReminder]:
        """
        Schedule all reminder messages for a conference based on workflow config.

        Args:
            workflow_id: Automation workflow ID
            conference_id: Conference to schedule reminders for
            organization_id: Organization identifier

        Returns:
            List of scheduled reminders
        """
        # Get workflow
        workflow_doc = await self.workflows_collection.find_one({
            "_id": ObjectId(workflow_id),
            "organization_id": organization_id
        })
        if not workflow_doc:
            raise ValueError("Workflow not found")

        workflow = AutomationWorkflow(**workflow_doc)

        # Get conference
        conference_doc = await self.db.conferences.find_one({"_id": ObjectId(conference_id)})
        if not conference_doc:
            raise ValueError("Conference not found")

        conference_start = conference_doc["start_date"]

        # Get registered attendees
        registrations = await self.db.registrations.find({
            "conference_id": conference_id,
            "status": "active"
        }).to_list(length=None)

        recipient_ids = [str(reg["_id"]) for reg in registrations]
        recipient_count = len(recipient_ids)

        if recipient_count == 0:
            logger.warning(f"No registered attendees found for conference {conference_id}")
            return []

        # Schedule each reminder step
        scheduled_reminders = []
        if workflow.event_reminder_config and workflow.event_reminder_config.enabled:
            for step in workflow.event_reminder_config.reminder_steps:
                if not step.enabled:
                    continue

                # Calculate scheduled time
                days_before = step.days_before or 0
                hours_before = step.hours_before or 0
                scheduled_at = conference_start - timedelta(days=days_before, hours=hours_before)

                # Don't schedule reminders in the past
                if scheduled_at < datetime.utcnow():
                    logger.info(f"Skipping past reminder: {step.timing} for conference {conference_id}")
                    continue

                # Create scheduled reminder
                reminder = ScheduledReminder(
                    workflow_id=workflow_id,
                    organization_id=organization_id,
                    conference_id=conference_id,
                    reminder_step=step,
                    scheduled_at=scheduled_at,
                    recipient_ids=recipient_ids,
                    recipient_count=recipient_count,
                    status="pending"
                )

                result = await self.reminders_collection.insert_one(
                    reminder.model_dump(by_alias=True, exclude={"id"})
                )
                reminder.id = str(result.inserted_id)
                scheduled_reminders.append(reminder)

                logger.info(
                    f"Scheduled {step.timing} reminder for conference {conference_id} "
                    f"at {scheduled_at} for {recipient_count} recipients"
                )

        # Update workflow next execution time
        if scheduled_reminders:
            next_execution = min(r.scheduled_at for r in scheduled_reminders)
            await self.workflows_collection.update_one(
                {"_id": ObjectId(workflow_id)},
                {"$set": {"next_execution_at": next_execution, "updated_at": datetime.utcnow()}}
            )

        # Log scheduling
        await self._log_event(
            workflow_id=workflow_id,
            organization_id=organization_id,
            event_type="reminders_scheduled",
            message=f"Scheduled {len(scheduled_reminders)} reminders for conference",
            metadata={
                "conference_id": conference_id,
                "recipient_count": recipient_count,
                "reminders_count": len(scheduled_reminders)
            }
        )

        return scheduled_reminders

    async def execute_pending_reminders(self) -> Dict[str, int]:
        """
        Execute all pending reminders that are due.

        This should be called by a scheduled task (e.g., every 5-15 minutes).

        Returns:
            Dictionary with execution statistics
        """
        now = datetime.utcnow()

        # Find pending reminders due now
        pending_reminders = await self.reminders_collection.find({
            "status": "pending",
            "scheduled_at": {"$lte": now}
        }).to_list(length=None)

        executed = 0
        successful = 0
        failed = 0

        for reminder_doc in pending_reminders:
            reminder = ScheduledReminder(**reminder_doc)

            try:
                # Mark as executing
                await self.reminders_collection.update_one(
                    {"_id": ObjectId(reminder.id)},
                    {"$set": {"status": "executing", "updated_at": now}}
                )

                # Execute the reminder
                result = await self._execute_reminder(reminder)

                # Update reminder with results
                await self.reminders_collection.update_one(
                    {"_id": ObjectId(reminder.id)},
                    {
                        "$set": {
                            "status": "completed",
                            "executed_at": now,
                            "sms_campaign_id": result.get("sms_campaign_id"),
                            "sent_count": result.get("sent_count", 0),
                            "delivered_count": result.get("delivered_count", 0),
                            "failed_count": result.get("failed_count", 0),
                            "updated_at": now
                        }
                    }
                )

                # Update workflow stats
                await self.workflows_collection.update_one(
                    {"_id": ObjectId(reminder.workflow_id)},
                    {
                        "$inc": {
                            "total_executions": 1,
                            "successful_executions": 1
                        },
                        "$set": {
                            "last_execution_at": now,
                            "updated_at": now
                        }
                    }
                )

                executed += 1
                successful += 1

                logger.info(f"Successfully executed reminder {reminder.id}")

            except Exception as e:
                logger.error(f"Failed to execute reminder {reminder.id}: {str(e)}")

                # Mark as failed
                await self.reminders_collection.update_one(
                    {"_id": ObjectId(reminder.id)},
                    {
                        "$set": {
                            "status": "failed",
                            "error_message": str(e),
                            "updated_at": now
                        }
                    }
                )

                # Update workflow stats
                await self.workflows_collection.update_one(
                    {"_id": ObjectId(reminder.workflow_id)},
                    {
                        "$inc": {
                            "total_executions": 1,
                            "failed_executions": 1
                        },
                        "$set": {"updated_at": now}
                    }
                )

                executed += 1
                failed += 1

        return {
            "executed": executed,
            "successful": successful,
            "failed": failed
        }

    async def _execute_reminder(self, reminder: ScheduledReminder) -> Dict[str, Any]:
        """
        Execute a single reminder by sending messages to recipients.

        Args:
            reminder: Scheduled reminder to execute

        Returns:
            Execution results
        """
        # Get conference details
        conference = await self.db.conferences.find_one({"_id": ObjectId(reminder.conference_id)})
        if not conference:
            raise ValueError(f"Conference {reminder.conference_id} not found")

        # Get registrations
        registration_ids = [ObjectId(rid) for rid in reminder.recipient_ids]
        registrations = await self.db.registrations.find({
            "_id": {"$in": registration_ids},
            "status": "active"
        }).to_list(length=None)

        if not registrations:
            raise ValueError("No active registrations found")

        # Send via appropriate channel
        if reminder.reminder_step.channel == NotificationChannel.SMS:
            # Use SMS campaign service
            campaign_result = await self._send_sms_reminder(
                reminder=reminder,
                conference=conference,
                registrations=registrations
            )
            return campaign_result
        else:
            # Other channels not yet implemented
            raise NotImplementedError(f"Channel {reminder.reminder_step.channel} not yet supported")

    async def _send_sms_reminder(
        self,
        reminder: ScheduledReminder,
        conference: Dict[str, Any],
        registrations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send reminder via SMS using the SMS campaign service.

        Args:
            reminder: Scheduled reminder
            conference: Conference document
            registrations: List of registration documents

        Returns:
            SMS campaign result
        """
        # Prepare contacts
        contacts = []
        for reg in registrations:
            contacts.append({
                "phone": reg["phone"],
                "name": reg["name"],
                "conference": conference["name"]
            })

        # Create and execute SMS campaign
        campaign_name = f"Reminder: {conference['name']} - {reminder.reminder_step.timing}"
        message_template = reminder.reminder_step.message_template

        # Create campaign
        campaign_doc = {
            "organization_id": reminder.organization_id,
            "name": campaign_name,
            "message_template": message_template,
            "audience_type": "custom",
            "status": "prepared",
            "created_by": "automation_system",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "contacts": contacts,
            "total_contacts": len(contacts),
            "sent_count": 0,
            "delivered_count": 0,
            "failed_count": 0,
            "pending_count": len(contacts)
        }

        result = await self.db.sms_campaigns.insert_one(campaign_doc)
        campaign_id = str(result.inserted_id)

        # Start campaign using shared SMS campaign service
        import sys
        sys.path.insert(0, "/opt/kasaai/apps")
        from shared.services.sms_campaign_service import sms_campaign_service
        sms_campaign_service.set_database(self.db)
        await sms_campaign_service.start_campaign(campaign_id)

        # Get updated campaign stats
        updated_campaign = await self.db.sms_campaigns.find_one({"_id": result.inserted_id})

        return {
            "sms_campaign_id": campaign_id,
            "sent_count": updated_campaign.get("sent_count", 0),
            "delivered_count": updated_campaign.get("delivered_count", 0),
            "failed_count": updated_campaign.get("failed_count", 0)
        }

    async def get_workflow(
        self,
        workflow_id: str,
        organization_id: str
    ) -> Optional[AutomationWorkflow]:
        """Get an automation workflow by ID"""
        workflow_doc = await self.workflows_collection.find_one({
            "_id": ObjectId(workflow_id),
            "organization_id": organization_id
        })

        if not workflow_doc:
            return None

        workflow_doc["_id"] = str(workflow_doc["_id"])
        return AutomationWorkflow(**workflow_doc)

    async def list_workflows(
        self,
        organization_id: str,
        automation_type: Optional[AutomationType] = None,
        status: Optional[AutomationStatus] = None
    ) -> List[AutomationWorkflow]:
        """List automation workflows for an organization"""
        query = {"organization_id": organization_id}

        if automation_type:
            query["automation_type"] = automation_type
        if status:
            query["status"] = status

        workflows = await self.workflows_collection.find(query).to_list(length=None)

        for workflow in workflows:
            workflow["_id"] = str(workflow["_id"])

        return [AutomationWorkflow(**w) for w in workflows]

    async def get_pending_reminders_count(self, organization_id: str) -> int:
        """Get count of pending reminders"""
        return await self.reminders_collection.count_documents({
            "organization_id": organization_id,
            "status": "pending"
        })

    async def get_upcoming_reminders(
        self,
        organization_id: str,
        hours: int = 24
    ) -> List[ScheduledReminder]:
        """Get upcoming reminders within specified hours"""
        now = datetime.utcnow()
        future = now + timedelta(hours=hours)

        reminders = await self.reminders_collection.find({
            "organization_id": organization_id,
            "status": "pending",
            "scheduled_at": {
                "$gte": now,
                "$lte": future
            }
        }).to_list(length=None)

        for reminder in reminders:
            reminder["_id"] = str(reminder["_id"])

        return [ScheduledReminder(**r) for r in reminders]

    async def _log_event(
        self,
        workflow_id: str,
        organization_id: str,
        event_type: str,
        message: str,
        metadata: Dict[str, Any] = None,
        scheduled_reminder_id: Optional[str] = None
    ):
        """Log an automation event"""
        log = AutomationLog(
            workflow_id=workflow_id,
            scheduled_reminder_id=scheduled_reminder_id,
            organization_id=organization_id,
            event_type=event_type,
            message=message,
            metadata=metadata or {}
        )

        await self.logs_collection.insert_one(log.model_dump(by_alias=True, exclude={"id"}))

    async def update_workflow_status(
        self,
        workflow_id: str,
        organization_id: str,
        status: AutomationStatus
    ) -> bool:
        """Update workflow status (active/paused/cancelled)"""
        result = await self.workflows_collection.update_one(
            {"_id": ObjectId(workflow_id), "organization_id": organization_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )

        if result.modified_count > 0:
            await self._log_event(
                workflow_id=workflow_id,
                organization_id=organization_id,
                event_type="status_changed",
                message=f"Workflow status changed to {status}",
                metadata={"new_status": status}
            )
            return True
        return False

    async def delete_workflow(
        self,
        workflow_id: str,
        organization_id: str
    ) -> bool:
        """Delete an automation workflow and its scheduled reminders"""
        # Delete scheduled reminders
        await self.reminders_collection.delete_many({"workflow_id": workflow_id})

        # Delete workflow
        result = await self.workflows_collection.delete_one({
            "_id": ObjectId(workflow_id),
            "organization_id": organization_id
        })

        return result.deleted_count > 0
