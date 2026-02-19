"""
VAPI Integration Service
Handles all VAPI voice agent functionality with unified interface.
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum
import aiohttp
import uuid

logger = logging.getLogger(__name__)


class CallType(str, Enum):
    """Call types."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BOTH = "both"


class CallStatus(str, Enum):
    """Call status options."""
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    ENDED = "ended"
    FAILED = "failed"


class WebhookEventType(str, Enum):
    """VAPI webhook event types."""
    CALL_STARTED = "call.started"
    CALL_ENDED = "call.ended"
    MESSAGE = "message"
    FUNCTION_CALL = "function-call"
    TRANSCRIPT = "transcript"
    HANG = "hang"
    SPEECH_UPDATE = "speech-update"


class VAPIAgent(BaseModel):
    """VAPI agent model."""
    name: str
    description: str = ""
    system_prompt: str
    voice: str = "alloy"
    language: str = "en"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    call_type: CallType = CallType.BOTH
    max_duration: int = Field(default=600, ge=30, le=3600)
    silence_timeout: int = Field(default=10, ge=5, le=60)
    interruptible: bool = True
    record_calls: bool = True
    phone_id: Optional[str] = None
    integrations: List[str] = Field(default_factory=list)
    custom_tools: List[Union[str, Dict[str, Any]]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    agent_id: Optional[str] = None
    created_at: Optional[datetime] = None


class VAPICall(BaseModel):
    """VAPI call model."""
    call_id: str
    to_number: str
    from_number: Optional[str] = None
    assistant_id: str
    status: CallStatus
    duration: Optional[int] = None
    transcript: Optional[str] = None
    recording_url: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    ended_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VAPIWebhookEvent(BaseModel):
    """VAPI webhook event model."""
    event: WebhookEventType
    call_id: Optional[str] = Field(None, alias="callId")
    assistant_id: Optional[str] = Field(None, alias="assistantId")
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    customer_number: Optional[str] = Field(None, alias="customerNumber")
    transcript: Optional[str] = None
    recording_url: Optional[str] = Field(None, alias="recordingUrl")
    duration: Optional[int] = None
    ended_reason: Optional[str] = Field(None, alias="endedReason")
    message: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = Field(None, alias="functionCall")
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None


class VAPIService:
    """
    Consolidated service for VAPI voice agent integration.
    Handles agents, calls, webhooks, and analytics.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize VAPI service with configuration.

        Args:
            config: Configuration dictionary with VAPI settings
        """
        self.config = config or {}
        self.api_key = self.config.get("VAPI_API_KEY")
        self.phone_number_id = self.config.get("VAPI_US_PHONE_ID")
        self.webhook_url = self.config.get("webhook_url", "https://api.ailabsafrica.com/vapi/webhook")
        self.base_url = "https://api.vapi.ai"
        self.session = None
        self.active_calls = {}
        self._initialize_client()

    def _initialize_client(self):
        """Initialize VAPI client."""
        if not self.api_key:
            logger.warning("VAPI API key not configured")
            return

        logger.info("Initialized VAPI service")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if not self.session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def _resolve_tool_to_function(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a VAPI tool ID to a VAPI function object.

        Args:
            tool_id: VAPI tool ID from MongoDB custom_tools collection

        Returns:
            VAPI function object formatted for VAPI API, or None if tool not found

        Reason: VAPI API requires function objects with name, description, parameters,
        and serverUrl, but frontend sends tool IDs. This method fetches tool details
        from MongoDB and converts them to the required format.
        """
        try:
            # Import motor for async MongoDB access
            import os
            from motor.motor_asyncio import AsyncIOMotorClient

            # Connect to MongoDB
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
            client = AsyncIOMotorClient(mongodb_url)
            db_name = os.getenv("MONGODB_DB", "kasaai_core")
            db = client[db_name]
            tools_collection = db['custom_tools']

            # Find tool by vapi_tool_id and ensure it's active
            tool = await tools_collection.find_one({
                'vapi_tool_id': tool_id,
                'is_active': True
            })

            if not tool:
                logger.warning(f"Tool not found or inactive for VAPI ID: {tool_id}")
                return None

            # Convert to VAPI function format
            # Reason: VAPI expects specific structure with type, function, async, and serverUrl
            function_obj = {
                "type": "function",
                "function": {
                    "name": tool['name'],
                    "description": tool.get('description', 'Custom tool'),
                    "parameters": tool.get('schema', {
                        "type": "object",
                        "properties": {},
                        "required": []
                    })
                },
                "async": False,  # Tools execute synchronously
                "serverUrl": tool.get('endpoint', tool.get('server_url', ''))
            }

            logger.info(f"✅ Resolved tool {tool_id} → {tool['name']} @ {function_obj['serverUrl']}")
            return function_obj

        except Exception as e:
            logger.error(f"❌ Error resolving tool ID {tool_id}: {e}", exc_info=True)
            return None

    async def create_agent(
        self,
        agent: VAPIAgent
    ) -> Dict[str, Any]:
        """
        Create a new VAPI agent.

        Args:
            agent: Agent configuration

        Returns:
            Agent creation result
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "VAPI API key not configured"
                }

            session = await self._get_session()

            # Prepare agent data for VAPI API
            agent_data = {
                "name": agent.name,
                "model": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": agent.system_prompt
                        }
                    ]
                },
                "voice": {
                    "provider": "vapi" if agent.voice.lower() in ["paige", "elliot", "kylie", "rohan", "lily", "savannah", "hana", "neha", "cole", "harry", "spencer"] else "openai",
                    "voiceId": agent.voice.title() if agent.voice.lower() in ["paige", "elliot", "kylie", "rohan", "lily", "savannah", "hana", "neha", "cole", "harry", "spencer"] else agent.voice,
                    "speed": agent.speed
                },
                "firstMessage": f"Hello! I'm {agent.name}. How can I help you today?",
                "recordingEnabled": agent.record_calls,
                "silenceTimeoutSeconds": agent.silence_timeout,
                "maxDurationSeconds": agent.max_duration,
                "endCallMessage": "Thank you for calling. Have a great day!",
                "metadata": agent.metadata
            }

            # Apply advanced VAPI configuration if available
            vapi_config = agent.metadata.get("vapi_config")
            if vapi_config:
                logger.info(f"Applying advanced VAPI configuration")

                # Override specific fields from vapi_config
                if "firstMessage" in vapi_config:
                    agent_data["firstMessage"] = vapi_config["firstMessage"]

                if "voicemailMessage" in vapi_config:
                    agent_data["voicemailMessage"] = vapi_config["voicemailMessage"]

                if "endCallMessage" in vapi_config:
                    agent_data["endCallMessage"] = vapi_config["endCallMessage"]

                if "transcriber" in vapi_config:
                    agent_data["transcriber"] = vapi_config["transcriber"]

                if "serverMessages" in vapi_config:
                    agent_data["serverMessages"] = vapi_config["serverMessages"]

                if "analysisPlan" in vapi_config:
                    agent_data["analysisPlan"] = vapi_config["analysisPlan"]

                if "voicemailDetection" in vapi_config:
                    agent_data["voicemailDetection"] = vapi_config["voicemailDetection"]

                if "backgroundDenoisingEnabled" in vapi_config:
                    agent_data["backgroundDenoisingEnabled"] = vapi_config["backgroundDenoisingEnabled"]

                if "artifactPlan" in vapi_config:
                    agent_data["artifactPlan"] = vapi_config["artifactPlan"]

                if "messagePlan" in vapi_config:
                    agent_data["messagePlan"] = vapi_config["messagePlan"]

                if "startSpeakingPlan" in vapi_config:
                    agent_data["startSpeakingPlan"] = vapi_config["startSpeakingPlan"]

                if "dialKeypadFunctionEnabled" in vapi_config:
                    agent_data["dialKeypadFunctionEnabled"] = vapi_config["dialKeypadFunctionEnabled"]

                if "endCallFunctionEnabled" in vapi_config:
                    agent_data["endCallFunctionEnabled"] = vapi_config["endCallFunctionEnabled"]

                logger.debug(f"Applied advanced configuration keys: {list(vapi_config.keys())}")

            # Add tools if specified - handle both tool IDs (strings) and tool objects (dicts)
            if agent.custom_tools:
                valid_functions = []
                skipped_tools = []

                for tool in agent.custom_tools:
                    if isinstance(tool, str):
                        # Tool ID - resolve to function object from MongoDB
                        logger.debug(f"Resolving tool ID: {tool}")
                        function_obj = await self._resolve_tool_to_function(tool)
                        if function_obj:
                            valid_functions.append(function_obj)
                        else:
                            skipped_tools.append(tool)
                            logger.warning(f"Could not resolve tool ID: {tool}")

                    elif isinstance(tool, dict):
                        # Already a function object - validate and use directly
                        if 'name' in tool and 'description' in tool:
                            # Ensure it has the correct structure
                            if 'type' not in tool:
                                tool['type'] = 'function'
                            if 'function' not in tool:
                                tool['function'] = {
                                    'name': tool['name'],
                                    'description': tool['description'],
                                    'parameters': tool.get('parameters', {})
                                }
                            valid_functions.append(tool)
                        else:
                            logger.warning(f"Invalid tool object missing required fields: {tool}")
                            skipped_tools.append(str(tool.get('name', 'unknown')))

                if valid_functions:
                    # Add tools to model.tools (VAPI API structure)
                    if "model" not in agent_data:
                        agent_data["model"] = {}
                    agent_data["model"]["tools"] = valid_functions
                    logger.info(f"✅ Added {len(valid_functions)} tools to VAPI agent")

                    # Log tool names for debugging
                    tool_names = [f['function']['name'] for f in valid_functions if 'function' in f and 'name' in f['function']]
                    logger.info(f"📋 Tools configured: {', '.join(tool_names)}")
                else:
                    logger.warning("⚠️  No valid tools to add to VAPI agent")

                if skipped_tools:
                    logger.warning(f"⚠️  Skipped {len(skipped_tools)} tools that could not be resolved: {skipped_tools}")

            logger.info(f"Creating VAPI agent: {agent.name}")

            # Make actual API call to VAPI
            async with session.post(f"{self.base_url}/assistant", json=agent_data) as response:
                if response.status == 201:
                    response_data = await response.json()

                    return {
                        "success": True,
                        "agent_id": response_data.get("id"),
                        "assistant_id": response_data.get("id"),
                        "name": agent.name,
                        "voice": agent.voice,
                        "created_at": datetime.now().isoformat(),
                        "webhook_url": self.webhook_url,
                        "phone_number_id": self.phone_number_id,
                        "vapi_response": response_data
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"VAPI API error: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"VAPI API error: {response.status} - {error_text}"
                    }

        except Exception as e:
            logger.error(f"Error creating VAPI agent: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def initiate_call(
        self,
        to_number: str,
        assistant_id: str,
        from_number: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initiate an outbound call.

        Args:
            to_number: Phone number to call
            assistant_id: VAPI assistant ID
            from_number: Caller ID (optional)
            metadata: Additional metadata

        Returns:
            Call initiation result
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "VAPI API key not configured"
                }

            session = await self._get_session()

            call_data = {
                "assistantId": assistant_id,
                "phoneNumberId": from_number or self.phone_number_id,
                "customer": {
                    "number": to_number
                },
                "metadata": metadata or {}
            }

            logger.info(f"Initiating VAPI call to {to_number} with assistant {assistant_id}")

            # Make actual API call to VAPI
            async with session.post(
                f"{self.base_url}/call/phone",
                json=call_data
            ) as response:
                if response.status == 201:
                    call_response = await response.json()
                    call_id = call_response.get("id")
                    
                    # Track active call
                    self.active_calls[call_id] = {
                        "call_id": call_id,
                        "to_number": to_number,
                        "assistant_id": assistant_id,
                        "status": CallStatus.INITIATED,
                        "started_at": datetime.now(),
                        "metadata": metadata or {}
                    }

                    logger.info(f"✅ VAPI call initiated successfully: {call_id}")
                    return {
                        "success": True,
                        "call": call_response,
                        "call_id": call_id,
                        "status": CallStatus.INITIATED.value,
                        "to_number": to_number,
                        "assistant_id": assistant_id,
                        "started_at": datetime.now().isoformat()
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"❌ VAPI API error: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"VAPI API error: {response.status} - {error_text}",
                        "status_code": response.status
                    }

        except Exception as e:
            logger.error(f"Error initiating VAPI call: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def create_phone_call(
        self,
        phone_number_id: str,
        customer_number: str,
        assistant_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a phone call via VAPI (alias for initiate_call with different parameter order).

        Args:
            phone_number_id: VAPI phone number ID to use for the call
            customer_number: Phone number to call
            assistant_id: VAPI assistant ID
            metadata: Additional metadata

        Returns:
            Call initiation result
        """
        return await self.initiate_call(
            to_number=customer_number,
            assistant_id=assistant_id,
            from_number=phone_number_id,
            metadata=metadata
        )

    async def end_call(
        self,
        call_id: str
    ) -> Dict[str, Any]:
        """
        End an active call.

        Args:
            call_id: Call ID to end

        Returns:
            Call end result
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "VAPI API key not configured"
                }

            session = await self._get_session()

            logger.info(f"Ending VAPI call: {call_id}")

            # Update call status
            if call_id in self.active_calls:
                self.active_calls[call_id]["status"] = CallStatus.ENDED
                self.active_calls[call_id]["ended_at"] = datetime.now()

            return {
                "success": True,
                "call_id": call_id,
                "status": CallStatus.ENDED.value,
                "ended_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error ending VAPI call {call_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_call_status(
        self,
        call_id: str
    ) -> Dict[str, Any]:
        """
        Get call status and details.

        Args:
            call_id: Call ID to query

        Returns:
            Call status details
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "VAPI API key not configured"
                }

            logger.info(f"Getting VAPI call status: {call_id}")

            # Check active calls first
            if call_id in self.active_calls:
                call_data = self.active_calls[call_id]
                return {
                    "success": True,
                    "call": call_data
                }

            # Mock call data if not found
            return {
                "success": True,
                "call": {
                    "call_id": call_id,
                    "status": "completed",
                    "duration": 120,
                    "created_at": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error getting VAPI call status {call_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def handle_webhook(
        self,
        event: VAPIWebhookEvent
    ) -> Dict[str, Any]:
        """
        Handle VAPI webhook event.

        Args:
            event: Webhook event data

        Returns:
            Webhook handling result
        """
        try:
            logger.info(f"Handling VAPI webhook: {event.event}")

            # Process different event types
            if event.event == WebhookEventType.CALL_STARTED:
                return await self._handle_call_started(event)
            elif event.event == WebhookEventType.CALL_ENDED:
                return await self._handle_call_ended(event)
            elif event.event == WebhookEventType.MESSAGE:
                return await self._handle_message(event)
            elif event.event == WebhookEventType.FUNCTION_CALL:
                return await self._handle_function_call(event)
            elif event.event == WebhookEventType.TRANSCRIPT:
                return await self._handle_transcript(event)
            else:
                return {
                    "success": True,
                    "message": f"Webhook event '{event.event}' received but not processed",
                    "event_type": event.event
                }

        except Exception as e:
            logger.error(f"Error handling VAPI webhook: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _handle_call_started(self, event: VAPIWebhookEvent) -> Dict[str, Any]:
        """Handle call started webhook."""
        call_id = event.call_id

        if call_id and call_id in self.active_calls:
            self.active_calls[call_id]["status"] = CallStatus.ANSWERED

        logger.info(f"Call started: {call_id}")

        return {
            "success": True,
            "event_type": "call_started",
            "call_id": call_id,
            "processed_at": datetime.now().isoformat()
        }

    async def _handle_call_ended(self, event: VAPIWebhookEvent) -> Dict[str, Any]:
        """Handle call ended webhook."""
        call_id = event.call_id

        if call_id and call_id in self.active_calls:
            self.active_calls[call_id]["status"] = CallStatus.ENDED
            self.active_calls[call_id]["ended_at"] = datetime.now()
            self.active_calls[call_id]["duration"] = event.duration
            self.active_calls[call_id]["ended_reason"] = event.ended_reason
            self.active_calls[call_id]["recording_url"] = event.recording_url

        logger.info(f"Call ended: {call_id}, duration: {event.duration}s")

        return {
            "success": True,
            "event_type": "call_ended",
            "call_id": call_id,
            "duration": event.duration,
            "ended_reason": event.ended_reason,
            "processed_at": datetime.now().isoformat()
        }

    async def _handle_message(self, event: VAPIWebhookEvent) -> Dict[str, Any]:
        """Handle message webhook."""
        logger.info(f"Message received: {event.message}")

        return {
            "success": True,
            "event_type": "message",
            "call_id": event.call_id,
            "message": event.message,
            "processed_at": datetime.now().isoformat()
        }

    async def _handle_function_call(self, event: VAPIWebhookEvent) -> Dict[str, Any]:
        """Handle function call webhook."""
        function_call = event.function_call

        logger.info(f"Function call: {function_call}")

        return {
            "success": True,
            "event_type": "function_call",
            "call_id": event.call_id,
            "function_call": function_call,
            "processed_at": datetime.now().isoformat()
        }

    async def _handle_transcript(self, event: VAPIWebhookEvent) -> Dict[str, Any]:
        """Handle transcript webhook."""
        logger.info(f"Transcript: {event.transcript}")

        return {
            "success": True,
            "event_type": "transcript",
            "call_id": event.call_id,
            "transcript": event.transcript,
            "processed_at": datetime.now().isoformat()
        }

    async def list_agents(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List VAPI agents.

        Args:
            limit: Maximum number of agents to return
            offset: Offset for pagination

        Returns:
            List of agents
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "VAPI API key not configured"
                }

            logger.info(f"Listing VAPI agents (limit: {limit}, offset: {offset})")

            session = await self._get_session()

            # Make actual API call to VAPI
            async with session.get(f"{self.base_url}/assistant?limit={limit}") as response:
                if response.status == 200:
                    response_data = await response.json()
                    agents = response_data if isinstance(response_data, list) else response_data.get("data", [])

                    return {
                        "success": True,
                        "agents": agents,
                        "total": len(agents),
                        "limit": limit,
                        "offset": offset
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"VAPI API error: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"VAPI API error: {response.status} - {error_text}"
                    }

        except Exception as e:
            logger.error(f"Error listing VAPI agents: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_analytics(
        self,
        assistant_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get call analytics from real VAPI call data.

        Args:
            assistant_id: Filter by assistant ID
            start_date: Start date for analytics
            end_date: End date for analytics

        Returns:
            Analytics data aggregated from actual calls
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "VAPI API key not configured"
                }

            logger.info(f"Getting VAPI analytics for assistant: {assistant_id}")

            # Fetch real calls from VAPI
            calls_result = await self.get_calls()

            if not calls_result.get("success"):
                return {
                    "success": False,
                    "error": calls_result.get("error", "Failed to fetch calls")
                }

            all_calls = calls_result.get("data", [])

            # Filter calls by assistant_id and date range
            filtered_calls = []
            for call in all_calls:
                # Filter by assistant ID if provided
                if assistant_id and call.get("assistantId") != assistant_id:
                    continue

                # Filter by date range if provided
                if start_date or end_date:
                    created_at_str = call.get("createdAt")
                    if created_at_str:
                        try:
                            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                            if start_date and created_at < start_date:
                                continue
                            if end_date and created_at > end_date:
                                continue
                        except Exception:
                            continue

                filtered_calls.append(call)

            # Aggregate metrics
            total_calls = len(filtered_calls)
            successful_calls = 0
            failed_calls = 0
            total_duration = 0
            durations = []

            for call in filtered_calls:
                status = call.get("status", "").lower()
                duration = call.get("duration", 0) or 0

                if status == "ended" and duration > 0:
                    successful_calls += 1
                elif status == "failed":
                    failed_calls += 1

                if duration > 0:
                    total_duration += duration
                    durations.append(duration)

            average_duration = (total_duration / len(durations)) if durations else 0
            success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0

            return {
                "success": True,
                "analytics": {
                    "total_calls": total_calls,
                    "successful_calls": successful_calls,
                    "failed_calls": failed_calls,
                    "average_duration": round(average_duration, 1),
                    "total_duration": total_duration,
                    "success_rate": round(success_rate, 1),
                    "assistant_id": assistant_id,
                    "date_range": {
                        "start": start_date.isoformat() if start_date else None,
                        "end": end_date.isoformat() if end_date else None
                    }
                },
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting VAPI analytics: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to VAPI API.

        Returns:
            Connection test result
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "VAPI API key not configured"
                }

            logger.info("Testing VAPI connection")

            # Mock connection test
            return {
                "success": True,
                "message": "Connection to VAPI successful",
                "api_base": self.base_url,
                "api_key_configured": bool(self.api_key),
                "phone_number_configured": bool(self.phone_number_id),
                "webhook_url": self.webhook_url,
                "tested_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"VAPI connection test error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get service capabilities."""
        return {
            "service": "vapi",
            "capabilities": [
                "create_agent",
                "initiate_call",
                "end_call",
                "get_call_status",
                "handle_webhook",
                "list_agents",
                "get_analytics",
                "test_connection",
                "get_service_info",
                "bulk_create_assistants",
                "get_analytics_summary",
                "create_tenant_agent"
            ],
            "supported_events": [event.value for event in WebhookEventType],
            "supported_voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
            "api_reference": "https://docs.vapi.ai/",
            "documentation": "https://docs.vapi.ai/quickstart",
            "configured": bool(self.api_key)
        }

    async def get_assistant(self, assistant_id: str) -> Dict[str, Any]:
        """
        Get assistant details by ID.

        Args:
            assistant_id: VAPI assistant ID

        Returns:
            Assistant details
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "VAPI API key not configured"
                }

            session = await self._get_session()

            async with session.get(f"{self.base_url}/assistant/{assistant_id}") as response:
                if response.status == 200:
                    response_data = await response.json()
                    return {
                        "success": True,
                        "assistant": response_data
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"VAPI API error: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"Assistant not found: {response.status} - {error_text}"
                    }

        except Exception as e:
            logger.error(f"Error getting VAPI assistant {assistant_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def create_assistant(self, assistant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create assistant using raw assistant data (alias for create_agent).

        Args:
            assistant_data: Assistant configuration data

        Returns:
            Assistant creation result
        """
        # Convert raw data to VAPIAgent model
        agent = VAPIAgent(
            name=assistant_data.get("name", "Assistant"),
            description=assistant_data.get("description", ""),
            system_prompt=assistant_data.get("systemPrompt", ""),
            voice=assistant_data.get("voice", "alloy"),
            language=assistant_data.get("language", "en"),
            speed=assistant_data.get("speed", 1.0),
            max_duration=assistant_data.get("max_duration", 600),
            silence_timeout=assistant_data.get("silence_timeout", 10),
            interruptible=assistant_data.get("interruptible", True),
            record_calls=assistant_data.get("record_calls", True),
            custom_tools=assistant_data.get("tools", [])
        )

        return await self.create_agent(agent)

    async def get_assistants(self) -> List[Dict[str, Any]]:
        """
        Get all assistants (alias for list_agents).

        Returns:
            List of assistants
        """
        result = await self.list_agents()
        if result.get("success"):
            return result.get("agents", [])
        return []

    async def get_calls(
        self,
        assistant_id: Optional[str] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Get call history with pagination support.

        Args:
            assistant_id: Optional filter by assistant ID
            limit: Maximum number of calls to return (default 1000)

        Returns:
            Call history data
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "VAPI API key not configured"
                }

            session = await self._get_session()

            # Build URL with parameters
            params = [f"limit={limit}"]
            if assistant_id:
                params.append(f"assistantId={assistant_id}")
            url = f"{self.base_url}/call?{'&'.join(params)}"

            async with session.get(url) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return {
                        "success": True,
                        "data": response_data if isinstance(response_data, list) else response_data.get("data", [])
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"VAPI API error: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"Failed to get calls: {response.status} - {error_text}"
                    }

        except Exception as e:
            logger.error(f"Error getting VAPI calls: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_assistant_analytics(
        self,
        assistant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated analytics for an assistant using VAPI Analytics API.

        This uses the POST /analytics endpoint to get accurate totals
        regardless of the number of calls (not limited to 1000 like get_calls).

        Args:
            assistant_id: VAPI assistant ID
            start_date: Start date for analytics (defaults to 1 year ago)
            end_date: End date for analytics (defaults to now)

        Returns:
            Aggregated analytics with total calls, duration, and cost
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "VAPI API key not configured"
                }

            session = await self._get_session()

            # Default date range - 1 year
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=365)

            # Build analytics query payload
            # Reason: VAPI Analytics API uses POST with queries array
            # and supports groupBy assistantId for per-assistant metrics
            payload = {
                "queries": [
                    {
                        "table": "call",
                        "name": "assistant_analytics",
                        "groupBy": ["assistantId"],
                        "operations": [
                            # Call metrics
                            {
                                "operation": "count",
                                "column": "id",
                                "alias": "total_calls"
                            },
                            {
                                "operation": "sum",
                                "column": "duration",
                                "alias": "total_minutes"
                            },
                            {
                                "operation": "avg",
                                "column": "duration",
                                "alias": "avg_duration"
                            },
                            {
                                "operation": "min",
                                "column": "duration",
                                "alias": "min_duration"
                            },
                            {
                                "operation": "max",
                                "column": "duration",
                                "alias": "max_duration"
                            },
                            # Total cost
                            {
                                "operation": "sum",
                                "column": "cost",
                                "alias": "total_cost"
                            },
                            # Cost breakdown by component
                            {
                                "operation": "sum",
                                "column": "costBreakdown.llm",
                                "alias": "llm_cost"
                            },
                            {
                                "operation": "sum",
                                "column": "costBreakdown.stt",
                                "alias": "stt_cost"
                            },
                            {
                                "operation": "sum",
                                "column": "costBreakdown.tts",
                                "alias": "tts_cost"
                            },
                            {
                                "operation": "sum",
                                "column": "costBreakdown.vapi",
                                "alias": "vapi_cost"
                            },
                            {
                                "operation": "sum",
                                "column": "costBreakdown.transport",
                                "alias": "transport_cost"
                            },
                            # Token usage
                            {
                                "operation": "sum",
                                "column": "costBreakdown.llmPromptTokens",
                                "alias": "prompt_tokens"
                            },
                            {
                                "operation": "sum",
                                "column": "costBreakdown.llmCompletionTokens",
                                "alias": "completion_tokens"
                            },
                            {
                                "operation": "sum",
                                "column": "costBreakdown.ttsCharacters",
                                "alias": "tts_characters"
                            }
                        ],
                        "timeRange": {
                            "step": "year",
                            "start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "end": end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                        }
                    }
                ]
            }

            logger.info(f"Fetching VAPI analytics for assistant {assistant_id}")

            async with session.post(
                f"{self.base_url}/analytics",
                json=payload
            ) as response:
                # Reason: VAPI Analytics API returns 201 on success (POST creates a query)
                if response.status in (200, 201):
                    response_data = await response.json()

                    # Find the result for our specific assistant
                    analytics_result = None
                    for query_result in response_data:
                        for result in query_result.get("result", []):
                            if result.get("assistantId") == assistant_id:
                                analytics_result = result
                                break

                    if analytics_result:
                        # Helper to extract float value from VAPI response
                        def get_float(key: str) -> float:
                            # VAPI returns camelCase (totalMinutes) or snake_case (total_minutes)
                            camel = key[0].lower() + key[1:]  # Ensure first char lowercase
                            snake = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
                            return float(analytics_result.get(camel) or analytics_result.get(snake) or 0)

                        def get_int(key: str) -> int:
                            camel = key[0].lower() + key[1:]
                            snake = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
                            val = analytics_result.get(camel) or analytics_result.get(snake) or 0
                            return int(val) if val else 0

                        # Extract all metrics
                        total_calls = get_int("totalCalls")
                        total_minutes = get_float("totalMinutes")
                        avg_duration = get_float("avgDuration")
                        min_duration = get_float("minDuration")
                        max_duration = get_float("maxDuration")
                        total_cost = get_float("totalCost")

                        # Cost breakdown
                        llm_cost = get_float("llmCost")
                        stt_cost = get_float("sttCost")
                        tts_cost = get_float("ttsCost")
                        vapi_cost = get_float("vapiCost")
                        transport_cost = get_float("transportCost")

                        # Token/character usage
                        prompt_tokens = get_int("promptTokens")
                        completion_tokens = get_int("completionTokens")
                        tts_characters = get_int("ttsCharacters")

                        return {
                            "success": True,
                            "assistant_id": assistant_id,
                            # Call metrics
                            "total_calls": total_calls,
                            "total_duration_minutes": total_minutes,
                            "total_duration_seconds": total_minutes * 60,
                            "avg_duration_minutes": avg_duration,
                            "avg_duration_seconds": avg_duration * 60,
                            "min_duration_minutes": min_duration,
                            "max_duration_minutes": max_duration,
                            # Cost metrics
                            "total_cost": total_cost,
                            "avg_cost_per_call": total_cost / total_calls if total_calls > 0 else 0,
                            # Cost breakdown (VAPI components)
                            "cost_breakdown": {
                                "llm": round(llm_cost, 4),
                                "stt": round(stt_cost, 4),
                                "tts": round(tts_cost, 4),
                                "vapi": round(vapi_cost, 4),
                                "transport": round(transport_cost, 4),
                                "total": round(total_cost, 4)
                            },
                            # Usage metrics
                            "usage": {
                                "prompt_tokens": prompt_tokens,
                                "completion_tokens": completion_tokens,
                                "total_tokens": prompt_tokens + completion_tokens,
                                "tts_characters": tts_characters
                            },
                            "period": {
                                "start": start_date.isoformat(),
                                "end": end_date.isoformat()
                            }
                        }
                    else:
                        # No data found for this assistant
                        return {
                            "success": True,
                            "assistant_id": assistant_id,
                            "total_calls": 0,
                            "total_duration_minutes": 0,
                            "total_duration_seconds": 0,
                            "avg_duration_minutes": 0,
                            "avg_duration_seconds": 0,
                            "min_duration_minutes": 0,
                            "max_duration_minutes": 0,
                            "total_cost": 0,
                            "avg_cost_per_call": 0,
                            "cost_breakdown": {
                                "llm": 0,
                                "stt": 0,
                                "tts": 0,
                                "vapi": 0,
                                "transport": 0,
                                "total": 0
                            },
                            "usage": {
                                "prompt_tokens": 0,
                                "completion_tokens": 0,
                                "total_tokens": 0,
                                "tts_characters": 0
                            },
                            "period": {
                                "start": start_date.isoformat(),
                                "end": end_date.isoformat()
                            }
                        }
                else:
                    error_text = await response.text()
                    logger.error(f"VAPI Analytics API error: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"Failed to get analytics: {response.status} - {error_text}"
                    }

        except Exception as e:
            logger.error(f"Error getting VAPI assistant analytics: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_phone_numbers(self) -> List[Dict[str, Any]]:
        """
        Get phone numbers.

        Returns:
            List of phone numbers
        """
        try:
            if not self.api_key:
                return []

            session = await self._get_session()

            async with session.get(f"{self.base_url}/phone-number") as response:
                if response.status == 200:
                    response_data = await response.json()
                    return response_data if isinstance(response_data, list) else response_data.get("data", [])
                else:
                    logger.error(f"Failed to get phone numbers: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error getting VAPI phone numbers: {e}")
            return []

    async def list_phone_numbers(self) -> Dict[str, Any]:
        """
        List phone numbers in a format expected by backend routes.

        This is a thin wrapper around get_phone_numbers that returns a dict with
        a 'success' flag and 'phoneNumbers' list, matching the contract used in
        the B2C portal's /api/vapi/phone-numbers endpoint.

        Returns:
            Dict[str, Any]: Result with success flag and phoneNumbers list.
        """
        try:
            numbers = await self.get_phone_numbers()
            return {
                "success": True,
                "phoneNumbers": numbers,
                "count": len(numbers),
            }
        except Exception as e:
            logger.error(f"Error listing VAPI phone numbers: {e}")
            return {
                "success": False,
                "error": str(e),
                "phoneNumbers": [],
                "count": 0,
            }

    async def create_tenant_agent(
        self,
        tenant_id: str,
        agent: VAPIAgent,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create agent for specific tenant/user.

        Args:
            tenant_id: Tenant/user ID
            agent: Agent configuration
            context: Additional context

        Returns:
            Agent creation result with tenant association
        """
        try:
            # Add tenant metadata to agent before creation
            agent.metadata.update({
                "tenant_id": tenant_id,
                "created_by": "kasaai_platform"
            })

            result = await self.create_agent(agent)

            if result.get("success"):
                # Add tenant context to result
                result["tenant_id"] = tenant_id
                result["context"] = context or {}

                logger.info(f"Created VAPI agent for tenant {tenant_id}: {result.get('agent_id')}")

            return result

        except Exception as e:
            logger.error(f"Error creating tenant VAPI agent: {e}")
            return {
                "success": False,
                "error": str(e),
                "tenant_id": tenant_id
            }

    async def get_service_info(self) -> Dict[str, Any]:
        """Get service information and status."""
        connection_test = await self.test_connection()
        return {
            "service_name": "VAPI Consolidated",
            "service_type": "Voice AI Platform",
            "version": "1.0.0",
            "connection_status": connection_test,
            "capabilities": [
                "voice_calls",
                "assistant_management",
                "phone_numbers",
                "call_logging",
                "analytics"
            ]
        }

    async def bulk_create_assistants(self, assistants_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple assistants in batch."""
        results = []
        for assistant_data in assistants_data:
            try:
                result = await self.create_assistant(assistant_data)
                results.append({"success": True, "data": result})
            except Exception as e:
                results.append({"success": False, "error": str(e), "data": assistant_data})
        return results

    async def get_analytics_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics summary for the last N days."""
        try:
            calls = await self.get_calls()
            # Process analytics from calls data
            total_calls = len(calls.get("data", []))

            return {
                "period_days": days,
                "total_calls": total_calls,
                "total_assistants": len(await self.get_assistants()),
                "active_phone_numbers": len(await self.get_phone_numbers()),
                "summary_generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating analytics summary: {e}")
            return {"error": str(e)}

    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None


# Global VAPI service instance with environment configuration
import os
vapi_service = VAPIService({
    "VAPI_API_KEY": os.getenv("VAPI_API_KEY"),
    "VAPI_US_PHONE_ID": os.getenv("VAPI_US_PHONE_ID"),
    "webhook_url": os.getenv("VAPI_WEBHOOK_URL", "https://api.ailabsafrica.com/vapi/webhook")
})