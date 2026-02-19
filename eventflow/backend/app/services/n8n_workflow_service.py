"""
n8n Workflow Service for EventFlow.

Integrates with shared n8n service to manage notification workflows.
"""

import logging
import os
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from apps.shared.integration.n8n import (
    N8NIntegration,
    N8NConfig,
    N8NWorkflow,
    N8NExecution,
    N8NExecutionStatus,
)

logger = logging.getLogger(__name__)


class EventFlowN8NService:
    """
    n8n workflow service for EventFlow.

    Manages multi-channel notification workflows:
    - Task reminders (SMS/WhatsApp/Email)
    - Deadline notifications
    - Task escalations
    - Daily summaries
    - Event check-in confirmations
    """

    def __init__(self):
        """Initialize EventFlow n8n service."""
        self.n8n_integration: Optional[N8NIntegration] = None
        self.logger = logging.getLogger(__name__)
        self.initialized = False
        self.workflow_ids: Dict[str, str] = {}

    async def initialize(
        self,
        n8n_base_url: Optional[str] = None,
        n8n_api_key: Optional[str] = None
    ) -> bool:
        """
        Initialize n8n service.

        Args:
            n8n_base_url: n8n instance URL (uses env var if not provided)
            n8n_api_key: n8n API key (uses env var if not provided)

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Get config from env if not provided
            base_url = n8n_base_url or os.getenv("N8N_BASE_URL")
            api_key = n8n_api_key or os.getenv("N8N_API_KEY")

            if not base_url:
                self.logger.warning("n8n base URL not configured")
                return False

            # Initialize n8n integration
            config = N8NConfig(
                base_url=base_url,
                api_key=api_key,
                timeout=30,
                verify_ssl=True
            )

            self.n8n_integration = N8NIntegration(config)

            # Discover existing workflows
            await self._discover_workflows()

            self.initialized = True
            self.logger.info("n8n service initialized successfully")

            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize n8n service: {e}")
            return False

    async def _discover_workflows(self) -> None:
        """Discover existing EventFlow workflows in n8n."""
        try:
            if not self.n8n_integration:
                return

            workflows = await self.n8n_integration.get_workflows()

            # Map workflow names to IDs
            for workflow in workflows:
                if workflow.name.startswith("EventFlow -"):
                    workflow_key = workflow.name.replace("EventFlow - ", "").lower().replace(" ", "_")
                    self.workflow_ids[workflow_key] = workflow.id
                    self.logger.info(f"Discovered workflow: {workflow.name} ({workflow.id})")

        except Exception as e:
            self.logger.warning(f"Failed to discover workflows: {e}")

    async def send_task_reminder(
        self,
        task_id: str,
        event_id: str,
        task_title: str,
        task_deadline: datetime,
        responsible_person_name: str,
        responsible_person_phone: str,
        responsible_person_email: Optional[str] = None,
        channels: List[str] = None
    ) -> Dict[str, Any]:
        """
        Send task reminder via multiple channels.

        Args:
            task_id: Task ID
            event_id: Event ID
            task_title: Task title
            task_deadline: Task deadline
            responsible_person_name: Responsible person's name
            responsible_person_phone: Phone number for SMS/WhatsApp
            responsible_person_email: Email address (optional)
            channels: List of channels to use (sms, whatsapp, email)

        Returns:
            Execution result
        """
        if not self.initialized or not self.n8n_integration:
            return {
                "success": False,
                "error": "n8n service not initialized"
            }

        try:
            # Default to SMS if no channels specified
            if not channels:
                channels = ["sms"]

            # Get days until deadline
            days_until = (task_deadline - datetime.utcnow()).days

            # Prepare workflow data
            workflow_data = {
                "task_id": task_id,
                "event_id": event_id,
                "task_title": task_title,
                "task_deadline": task_deadline.isoformat(),
                "days_until_deadline": days_until,
                "responsible_person": {
                    "name": responsible_person_name,
                    "phone": responsible_person_phone,
                    "email": responsible_person_email
                },
                "channels": channels,
                "message": self._format_task_reminder_message(
                    task_title,
                    task_deadline,
                    responsible_person_name,
                    days_until
                )
            }

            # Check if task reminder workflow exists
            workflow_id = self.workflow_ids.get("task_reminder")

            if not workflow_id:
                self.logger.warning("Task reminder workflow not found, creating placeholder")
                return {
                    "success": False,
                    "error": "Task reminder workflow not configured in n8n"
                }

            # Trigger workflow
            self.logger.info(f"Sending task reminder for task {task_id} via {channels}")
            execution = await self.n8n_integration.trigger_workflow(
                workflow_id=workflow_id,
                data=workflow_data
            )

            return {
                "success": True,
                "execution_id": execution.id,
                "status": execution.status.value,
                "channels": channels,
                "message": "Task reminder sent"
            }

        except Exception as e:
            self.logger.error(f"Failed to send task reminder: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def send_deadline_alert(
        self,
        task_id: str,
        event_id: str,
        task_title: str,
        task_deadline: datetime,
        responsible_person_name: str,
        responsible_person_phone: str,
        urgency: str = "high"
    ) -> Dict[str, Any]:
        """
        Send urgent deadline alert.

        Args:
            task_id: Task ID
            event_id: Event ID
            task_title: Task title
            task_deadline: Task deadline
            responsible_person_name: Responsible person's name
            responsible_person_phone: Phone number
            urgency: Urgency level (low, medium, high, critical)

        Returns:
            Execution result
        """
        if not self.initialized or not self.n8n_integration:
            return {
                "success": False,
                "error": "n8n service not initialized"
            }

        try:
            hours_until = (task_deadline - datetime.utcnow()).total_seconds() / 3600

            workflow_data = {
                "task_id": task_id,
                "event_id": event_id,
                "task_title": task_title,
                "task_deadline": task_deadline.isoformat(),
                "hours_until_deadline": hours_until,
                "responsible_person": {
                    "name": responsible_person_name,
                    "phone": responsible_person_phone
                },
                "urgency": urgency,
                "message": self._format_deadline_alert_message(
                    task_title,
                    task_deadline,
                    responsible_person_name,
                    hours_until
                )
            }

            workflow_id = self.workflow_ids.get("deadline_alert")

            if not workflow_id:
                return {
                    "success": False,
                    "error": "Deadline alert workflow not configured"
                }

            execution = await self.n8n_integration.trigger_workflow(
                workflow_id=workflow_id,
                data=workflow_data
            )

            return {
                "success": True,
                "execution_id": execution.id,
                "status": execution.status.value,
                "urgency": urgency
            }

        except Exception as e:
            self.logger.error(f"Failed to send deadline alert: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def send_task_escalation(
        self,
        task_id: str,
        event_id: str,
        task_title: str,
        responsible_person_name: str,
        organizer_phone: str,
        organizer_email: Optional[str] = None,
        escalation_reason: str = "Task overdue"
    ) -> Dict[str, Any]:
        """
        Send task escalation to event organizer.

        Args:
            task_id: Task ID
            event_id: Event ID
            task_title: Task title
            responsible_person_name: Responsible person's name
            organizer_phone: Organizer phone number
            organizer_email: Organizer email
            escalation_reason: Reason for escalation

        Returns:
            Execution result
        """
        if not self.initialized or not self.n8n_integration:
            return {
                "success": False,
                "error": "n8n service not initialized"
            }

        try:
            workflow_data = {
                "task_id": task_id,
                "event_id": event_id,
                "task_title": task_title,
                "responsible_person_name": responsible_person_name,
                "organizer": {
                    "phone": organizer_phone,
                    "email": organizer_email
                },
                "escalation_reason": escalation_reason,
                "escalated_at": datetime.utcnow().isoformat(),
                "message": self._format_escalation_message(
                    task_title,
                    responsible_person_name,
                    escalation_reason
                )
            }

            workflow_id = self.workflow_ids.get("task_escalation")

            if not workflow_id:
                return {
                    "success": False,
                    "error": "Task escalation workflow not configured"
                }

            execution = await self.n8n_integration.trigger_workflow(
                workflow_id=workflow_id,
                data=workflow_data
            )

            return {
                "success": True,
                "execution_id": execution.id,
                "status": execution.status.value
            }

        except Exception as e:
            self.logger.error(f"Failed to send task escalation: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def send_daily_summary(
        self,
        event_id: str,
        event_name: str,
        organizer_phone: str,
        organizer_email: Optional[str] = None,
        summary_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Send daily summary to event organizer.

        Args:
            event_id: Event ID
            event_name: Event name
            organizer_phone: Organizer phone number
            organizer_email: Organizer email
            summary_data: Summary data (tasks completed, pending, overdue, etc.)

        Returns:
            Execution result
        """
        if not self.initialized or not self.n8n_integration:
            return {
                "success": False,
                "error": "n8n service not initialized"
            }

        try:
            workflow_data = {
                "event_id": event_id,
                "event_name": event_name,
                "organizer": {
                    "phone": organizer_phone,
                    "email": organizer_email
                },
                "summary": summary_data or {},
                "generated_at": datetime.utcnow().isoformat(),
                "message": self._format_daily_summary_message(
                    event_name,
                    summary_data or {}
                )
            }

            workflow_id = self.workflow_ids.get("daily_summary")

            if not workflow_id:
                return {
                    "success": False,
                    "error": "Daily summary workflow not configured"
                }

            execution = await self.n8n_integration.trigger_workflow(
                workflow_id=workflow_id,
                data=workflow_data
            )

            return {
                "success": True,
                "execution_id": execution.id,
                "status": execution.status.value
            }

        except Exception as e:
            self.logger.error(f"Failed to send daily summary: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _format_task_reminder_message(
        self,
        task_title: str,
        deadline: datetime,
        person_name: str,
        days_until: int
    ) -> str:
        """Format task reminder message."""
        deadline_str = deadline.strftime("%B %d, %Y")

        if days_until == 0:
            urgency = "TODAY"
        elif days_until == 1:
            urgency = "TOMORROW"
        elif days_until < 7:
            urgency = f"in {days_until} days"
        else:
            urgency = f"on {deadline_str}"

        return f"""Hi {person_name},

This is a reminder about your task:

📋 {task_title}
⏰ Due: {urgency}

Please update the task status or contact the event organizer if you need any support.

EventFlow - Making Event Planning Easier"""

    def _format_deadline_alert_message(
        self,
        task_title: str,
        deadline: datetime,
        person_name: str,
        hours_until: float
    ) -> str:
        """Format deadline alert message."""
        if hours_until < 1:
            urgency = "URGENT - Less than 1 hour remaining!"
        elif hours_until < 24:
            urgency = f"URGENT - {int(hours_until)} hours remaining!"
        else:
            days = int(hours_until / 24)
            urgency = f"{days} day{'s' if days > 1 else ''} remaining"

        return f"""🚨 DEADLINE ALERT 🚨

Hi {person_name},

Your task deadline is approaching:

📋 {task_title}
⏰ {urgency}

Please complete this task as soon as possible or contact the organizer.

EventFlow"""

    def _format_escalation_message(
        self,
        task_title: str,
        person_name: str,
        reason: str
    ) -> str:
        """Format escalation message."""
        return f"""⚠️ Task Escalation Alert

Task: {task_title}
Assigned to: {person_name}
Reason: {reason}

This task requires your attention. Please follow up with the responsible person.

EventFlow"""

    def _format_daily_summary_message(
        self,
        event_name: str,
        summary: Dict[str, Any]
    ) -> str:
        """Format daily summary message."""
        total = summary.get("total_tasks", 0)
        completed = summary.get("completed_tasks", 0)
        pending = summary.get("pending_tasks", 0)
        overdue = summary.get("overdue_tasks", 0)

        return f"""📊 Daily Event Summary

Event: {event_name}

Tasks Overview:
✅ Completed: {completed}
⏳ Pending: {pending}
🚨 Overdue: {overdue}
📝 Total: {total}

{"⚠️ Attention needed: You have overdue tasks!" if overdue > 0 else "✨ Great progress!"}

EventFlow - Your Event Planning Assistant"""

    async def get_workflow_status(self, workflow_name: str) -> Dict[str, Any]:
        """
        Get status of a workflow.

        Args:
            workflow_name: Workflow name (e.g., "task_reminder")

        Returns:
            Workflow status
        """
        if not self.initialized or not self.n8n_integration:
            return {
                "success": False,
                "error": "n8n service not initialized"
            }

        try:
            workflow_id = self.workflow_ids.get(workflow_name)

            if not workflow_id:
                return {
                    "success": False,
                    "error": f"Workflow '{workflow_name}' not found"
                }

            workflow = await self.n8n_integration.get_workflow(workflow_id)

            return {
                "success": True,
                "workflow": {
                    "id": workflow.id,
                    "name": workflow.name,
                    "active": workflow.active,
                    "tags": workflow.tags,
                    "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
                    "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to get workflow status: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def list_workflows(self) -> Dict[str, Any]:
        """
        List all EventFlow workflows.

        Returns:
            List of workflows
        """
        if not self.initialized or not self.n8n_integration:
            return {
                "success": False,
                "error": "n8n service not initialized"
            }

        try:
            workflows = await self.n8n_integration.get_workflows()

            eventflow_workflows = [
                {
                    "id": w.id,
                    "name": w.name,
                    "active": w.active,
                    "tags": w.tags,
                    "created_at": w.created_at.isoformat() if w.created_at else None
                }
                for w in workflows
                if w.name.startswith("EventFlow -")
            ]

            return {
                "success": True,
                "workflows": eventflow_workflows,
                "total": len(eventflow_workflows)
            }

        except Exception as e:
            self.logger.error(f"Failed to list workflows: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_execution_history(
        self,
        workflow_name: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get workflow execution history.

        Args:
            workflow_name: Filter by workflow name (optional)
            limit: Number of executions to return

        Returns:
            Execution history
        """
        if not self.initialized or not self.n8n_integration:
            return {
                "success": False,
                "error": "n8n service not initialized"
            }

        try:
            workflow_id = None
            if workflow_name:
                workflow_id = self.workflow_ids.get(workflow_name)

            executions = await self.n8n_integration.get_executions(
                workflow_id=workflow_id,
                limit=limit
            )

            execution_list = [
                {
                    "id": e.id,
                    "workflow_id": e.workflow_id,
                    "status": e.status.value,
                    "started_at": e.started_at.isoformat() if e.started_at else None,
                    "stopped_at": e.stopped_at.isoformat() if e.stopped_at else None,
                    "finished": e.finished
                }
                for e in executions
            ]

            return {
                "success": True,
                "executions": execution_list,
                "total": len(execution_list)
            }

        except Exception as e:
            self.logger.error(f"Failed to get execution history: {e}")
            return {
                "success": False,
                "error": str(e)
            }
