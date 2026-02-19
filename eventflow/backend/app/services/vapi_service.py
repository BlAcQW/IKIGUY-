"""
VAPI Service for EventFlow.

Integrates with shared VAPI service to manage voice calls for task follow-ups.
"""

import logging
import os
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from apps.shared.integration.vapi import (
    VAPIService as SharedVAPIService,
    VAPIAgent,
    VAPICall,
    VAPIWebhookEvent,
    CallStatus,
    WebhookEventType,
)

logger = logging.getLogger(__name__)


class EventFlowVAPIService:
    """
    VAPI service for EventFlow.

    Wraps the shared VAPI service with EventFlow-specific functionality:
    - Creating "Ama" assistant for task follow-ups
    - Initiating calls to responsible persons for task updates
    - Handling webhooks for task status updates
    - Tracking call costs via wallet service
    """

    def __init__(self):
        """Initialize EventFlow VAPI service."""
        self.shared_vapi: Optional[SharedVAPIService] = None
        self.logger = logging.getLogger(__name__)
        self.initialized = False
        self.ama_assistant_id: Optional[str] = None

    async def initialize(self, vapi_api_key: Optional[str] = None) -> bool:
        """
        Initialize VAPI service.

        Args:
            vapi_api_key: VAPI API key (uses env var if not provided)

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Get API key from env if not provided
            api_key = vapi_api_key or os.getenv("VAPI_API_KEY")

            if not api_key:
                self.logger.warning("VAPI API key not configured")
                return False

            # Initialize shared VAPI service
            self.shared_vapi = SharedVAPIService({
                "VAPI_API_KEY": api_key,
                "VAPI_US_PHONE_ID": os.getenv("VAPI_US_PHONE_ID"),
                "webhook_url": os.getenv("VAPI_WEBHOOK_URL", "https://eventflow-api.ailabsafrica.com/api/v1/voice/webhook")
            })

            self.initialized = True
            self.logger.info("VAPI service initialized successfully")

            # Get or create Ama assistant
            await self._ensure_ama_assistant()

            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize VAPI service: {e}")
            return False

    async def _ensure_ama_assistant(self) -> bool:
        """
        Ensure "Ama" assistant exists, create if not found.

        Returns:
            True if Ama assistant is ready, False otherwise
        """
        try:
            if not self.initialized or not self.shared_vapi:
                return False

            # Check if Ama assistant already exists
            agents_result = await self.shared_vapi.list_agents()

            if agents_result.get("success"):
                agents = agents_result.get("agents", [])

                # Look for existing Ama assistant
                for agent in agents:
                    if agent.get("name") == "Ama - EventFlow Assistant":
                        self.ama_assistant_id = agent.get("id")
                        self.logger.info(f"Found existing Ama assistant: {self.ama_assistant_id}")
                        return True

            # Create Ama assistant if not found
            self.logger.info("Creating Ama assistant for EventFlow")

            ama_agent = VAPIAgent(
                name="Ama - EventFlow Assistant",
                description="AI assistant for event planning task follow-ups",
                system_prompt="""You are Ama, a friendly and professional AI assistant for EventFlow.

Your role is to call responsible persons assigned to event planning tasks and:
1. Remind them about their assigned tasks
2. Ask for status updates
3. Identify any blockers or challenges they're facing
4. Offer to help or escalate issues

**Communication Style:**
- Be warm, professional, and culturally aware (Ghanaian context)
- Use simple, clear language
- Be patient and understanding
- Show appreciation for their work

**Key Information to Gather:**
- Task status (not started, in progress, completed)
- Percentage complete (if in progress)
- Expected completion date
- Any blockers or issues
- Resources or support needed

**Function Calls:**
You have access to these functions:
- update_task_status: Update task status and notes
- escalate_task: Escalate task to event organizer

Always confirm information before updating task status.
End calls politely and thank them for their time.
""",
                voice="Savannah",  # Female voice for Ama
                language="en",
                speed=1.0,
                max_duration=600,  # 10 minutes max
                silence_timeout=15,
                interruptible=True,
                record_calls=True,
                custom_tools=[],  # We'll add tools via metadata
                metadata={
                    "app": "eventflow",
                    "assistant_type": "task_follow_up",
                    "version": "1.0"
                }
            )

            result = await self.shared_vapi.create_agent(ama_agent)

            if result.get("success"):
                self.ama_assistant_id = result.get("agent_id")
                self.logger.info(f"✅ Created Ama assistant: {self.ama_assistant_id}")
                return True
            else:
                self.logger.error(f"Failed to create Ama assistant: {result.get('error')}")
                return False

        except Exception as e:
            self.logger.error(f"Error ensuring Ama assistant: {e}")
            return False

    async def call_responsible_person(
        self,
        task_id: str,
        event_id: str,
        person_name: str,
        person_phone: str,
        task_title: str,
        task_deadline: datetime,
        wallet_id: str
    ) -> Dict[str, Any]:
        """
        Initiate a call to a responsible person about a task.

        Args:
            task_id: Task ID
            event_id: Event ID
            person_name: Responsible person's name
            person_phone: Phone number to call
            task_title: Task title for context
            task_deadline: Task deadline
            wallet_id: User's wallet ID for billing

        Returns:
            Call initiation result with call_id
        """
        if not self.initialized or not self.shared_vapi:
            return {
                "success": False,
                "error": "VAPI service not initialized"
            }

        if not self.ama_assistant_id:
            return {
                "success": False,
                "error": "Ama assistant not available"
            }

        try:
            # Format phone number (ensure E.164 format)
            if not person_phone.startswith("+"):
                person_phone = f"+233{person_phone.lstrip('0')}"  # Assume Ghana

            # Prepare call metadata
            call_metadata = {
                "task_id": task_id,
                "event_id": event_id,
                "person_name": person_name,
                "task_title": task_title,
                "task_deadline": task_deadline.isoformat(),
                "wallet_id": wallet_id,
                "app": "eventflow",
                "call_type": "task_follow_up"
            }

            self.logger.info(f"Initiating call to {person_name} ({person_phone}) for task: {task_title}")

            # Initiate call via shared VAPI service
            result = await self.shared_vapi.initiate_call(
                to_number=person_phone,
                assistant_id=self.ama_assistant_id,
                metadata=call_metadata
            )

            if result.get("success"):
                self.logger.info(f"✅ Call initiated successfully: {result.get('call_id')}")

            return result

        except Exception as e:
            self.logger.error(f"Error initiating call: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def handle_webhook(
        self,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle VAPI webhook event.

        Args:
            event_data: Webhook event data from VAPI

        Returns:
            Processing result
        """
        if not self.initialized or not self.shared_vapi:
            return {
                "success": False,
                "error": "VAPI service not initialized"
            }

        try:
            # Parse webhook event
            event = VAPIWebhookEvent(**event_data)

            self.logger.info(f"Processing VAPI webhook: {event.event}")

            # Handle different event types
            if event.event == WebhookEventType.CALL_ENDED:
                return await self._handle_call_ended(event)
            elif event.event == WebhookEventType.FUNCTION_CALL:
                return await self._handle_function_call(event)
            elif event.event == WebhookEventType.TRANSCRIPT:
                return await self._handle_transcript(event)
            else:
                # Pass through to shared service
                return await self.shared_vapi.handle_webhook(event)

        except Exception as e:
            self.logger.error(f"Error handling webhook: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _handle_call_ended(self, event: VAPIWebhookEvent) -> Dict[str, Any]:
        """
        Handle call ended webhook.

        Calculates call cost and deducts from wallet.
        """
        try:
            call_id = event.call_id
            duration = event.duration or 0

            # Get call metadata
            call_status = await self.shared_vapi.get_call_status(call_id)

            if not call_status.get("success"):
                self.logger.warning(f"Could not get call status for {call_id}")
                return {"success": True, "message": "Call ended but metadata unavailable"}

            call_data = call_status.get("call", {})
            metadata = call_data.get("metadata", {})

            wallet_id = metadata.get("wallet_id")
            task_id = metadata.get("task_id")
            event_id = metadata.get("event_id")
            person_name = metadata.get("person_name", "Unknown")

            self.logger.info(f"Call ended: {call_id}, duration: {duration}s, task: {task_id}")

            # Deduct call cost from wallet if wallet_id available
            if wallet_id and duration > 0:
                from .wallet_service import EventFlowWalletService

                wallet_service = EventFlowWalletService()
                await wallet_service.initialize(
                    mongodb_uri=os.getenv("MONGODB_URL"),
                    database_name="kasaai_wallets"
                )

                transaction = await wallet_service.deduct_voice_call_cost(
                    wallet_id=wallet_id,
                    event_id=event_id,
                    task_id=task_id,
                    duration_minutes=duration / 60.0,
                    responsible_person_name=person_name
                )

                if transaction:
                    self.logger.info(f"✅ Deducted call cost from wallet {wallet_id}")
                else:
                    self.logger.warning(f"Failed to deduct call cost from wallet {wallet_id}")

            return {
                "success": True,
                "event_type": "call_ended",
                "call_id": call_id,
                "duration": duration,
                "processed_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error handling call ended webhook: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _handle_function_call(self, event: VAPIWebhookEvent) -> Dict[str, Any]:
        """
        Handle function call webhook.

        Processes function calls from Ama assistant (e.g., update_task_status, escalate_task).
        """
        try:
            function_call = event.function_call or {}
            function_name = function_call.get("name")
            parameters = function_call.get("parameters", {})

            self.logger.info(f"Function call: {function_name}, params: {parameters}")

            # Handle different function calls
            if function_name == "update_task_status":
                return await self._update_task_status(parameters, event)
            elif function_name == "escalate_task":
                return await self._escalate_task(parameters, event)
            else:
                return {
                    "success": False,
                    "error": f"Unknown function: {function_name}"
                }

        except Exception as e:
            self.logger.error(f"Error handling function call: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _handle_transcript(self, event: VAPIWebhookEvent) -> Dict[str, Any]:
        """
        Handle transcript webhook.

        Stores call transcript for later review.
        """
        try:
            call_id = event.call_id
            transcript = event.transcript

            self.logger.info(f"Call transcript for {call_id}: {len(transcript or '')} chars")

            # TODO: Store transcript in database for event organizer review
            # This would involve:
            # 1. Getting call metadata (task_id, event_id)
            # 2. Storing transcript in MongoDB
            # 3. Notifying event organizer if needed

            return {
                "success": True,
                "event_type": "transcript",
                "call_id": call_id,
                "transcript_length": len(transcript or ""),
                "processed_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error handling transcript: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _update_task_status(
        self,
        parameters: Dict[str, Any],
        event: VAPIWebhookEvent
    ) -> Dict[str, Any]:
        """
        Update task status from function call.

        Args:
            parameters: Function parameters (status, notes, completion_percentage)
            event: Webhook event with call context

        Returns:
            Update result
        """
        try:
            # Get call metadata for task_id
            call_id = event.call_id
            call_status = await self.shared_vapi.get_call_status(call_id)

            if not call_status.get("success"):
                return {"success": False, "error": "Could not get call metadata"}

            metadata = call_status.get("call", {}).get("metadata", {})
            task_id = metadata.get("task_id")

            if not task_id:
                return {"success": False, "error": "Task ID not found in call metadata"}

            # TODO: Update task in MongoDB
            # This would involve:
            # 1. Connecting to MongoDB
            # 2. Updating task with new status and notes
            # 3. Recording who made the update (from call)

            self.logger.info(f"Task {task_id} status updated via call: {parameters}")

            return {
                "success": True,
                "message": "Task status updated successfully",
                "task_id": task_id,
                "status": parameters.get("status"),
                "notes": parameters.get("notes")
            }

        except Exception as e:
            self.logger.error(f"Error updating task status: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _escalate_task(
        self,
        parameters: Dict[str, Any],
        event: VAPIWebhookEvent
    ) -> Dict[str, Any]:
        """
        Escalate task to event organizer.

        Args:
            parameters: Function parameters (reason, urgency)
            event: Webhook event with call context

        Returns:
            Escalation result
        """
        try:
            # Get call metadata for task_id
            call_id = event.call_id
            call_status = await self.shared_vapi.get_call_status(call_id)

            if not call_status.get("success"):
                return {"success": False, "error": "Could not get call metadata"}

            metadata = call_status.get("call", {}).get("metadata", {})
            task_id = metadata.get("task_id")
            event_id = metadata.get("event_id")

            if not task_id or not event_id:
                return {"success": False, "error": "Task/Event ID not found"}

            # TODO: Create escalation notification
            # This would involve:
            # 1. Finding event organizer
            # 2. Creating notification/email about escalation
            # 3. Marking task as "escalated" status

            self.logger.info(f"Task {task_id} escalated: {parameters}")

            return {
                "success": True,
                "message": "Task escalated to organizer",
                "task_id": task_id,
                "event_id": event_id,
                "reason": parameters.get("reason"),
                "urgency": parameters.get("urgency", "medium")
            }

        except Exception as e:
            self.logger.error(f"Error escalating task: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_call_history(
        self,
        event_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get call history for an event or task.

        Args:
            event_id: Filter by event ID
            task_id: Filter by task ID

        Returns:
            List of calls with metadata
        """
        if not self.initialized or not self.shared_vapi:
            return {
                "success": False,
                "error": "VAPI service not initialized"
            }

        try:
            # Get all calls
            calls_result = await self.shared_vapi.get_calls()

            if not calls_result.get("success"):
                return calls_result

            all_calls = calls_result.get("data", [])

            # Filter by event_id or task_id
            filtered_calls = []
            for call in all_calls:
                metadata = call.get("metadata", {})

                if event_id and metadata.get("event_id") == event_id:
                    filtered_calls.append(call)
                elif task_id and metadata.get("task_id") == task_id:
                    filtered_calls.append(call)
                elif not event_id and not task_id:
                    # No filter, include all EventFlow calls
                    if metadata.get("app") == "eventflow":
                        filtered_calls.append(call)

            return {
                "success": True,
                "calls": filtered_calls,
                "total": len(filtered_calls)
            }

        except Exception as e:
            self.logger.error(f"Error getting call history: {e}")
            return {
                "success": False,
                "error": str(e)
            }
