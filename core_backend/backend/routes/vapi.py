"""
VAPI Integration Routes

This module provides API endpoints for VAPI voice agent integration,
including agent creation, webhook handling, and analytics.
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import httpx
import uuid
import json
from datetime import datetime
import logging
import os
from ..auth import get_current_user_mongo
from ..mongo import get_collection
from ..services.vapi_service import vapi_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vapi", tags=["VAPI Integration"])

# Pydantic models for request/response
class VapiAgentCreate(BaseModel):
    name: str = Field(..., description="Agent name")
    description: str = Field("", description="Agent description")
    agent_type: str = Field(..., description="Type of agent (helpdesk, sales, etc.)")
    system_prompt: str = Field(..., description="System prompt for the agent")
    
    # VAPI specific settings
    vapi_phone_id: str = Field("", description="VAPI phone number ID")
    call_type: str = Field("both", description="Call type: inbound, outbound, or both")
    
    # Voice settings
    voice: str = Field("alloy", description="Voice to use")
    language: str = Field("en", description="Primary language")
    speed: float = Field(1.0, description="Speaking speed")
    
    # Tool integrations
    integrations: List[str] = Field([], description="Selected platform integrations")
    custom_tools: List[Dict[str, str]] = Field([], description="Custom webhook tools")
    
    # Advanced settings
    max_duration: int = Field(600, description="Maximum call duration in seconds")
    silence_timeout: int = Field(10, description="Silence timeout in seconds")
    interruptible: bool = Field(True, description="Allow interruptions")
    record_calls: bool = Field(True, description="Record calls")
    
    # Webhook settings
    webhook_url: Optional[str] = Field(None, description="Webhook URL for callbacks")
    enable_webhooks: bool = Field(True, description="Enable webhook callbacks")
    
    # Metadata
    tenant_id: str = Field("default", description="Tenant ID")
    created_with: str = Field("kasaai_platform", description="Creation source")


class WebhookEvent(BaseModel):
    event_type: str = Field(..., description="Type of webhook event")
    call_id: str = Field(..., description="Unique call identifier")
    assistant_id: str = Field(..., description="Assistant identifier")
    data: Dict[str, Any] = Field({}, description="Event data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SystemPromptGenerate(BaseModel):
    website_url: str = Field(..., description="Website URL to analyze")
    agent_type: str = Field(..., description="Type of agent to create")
    language: str = Field("en", description="Primary language for the prompt")


# VAPI configuration from environment variables
import os
VAPI_CONFIG = {
    "api_url": os.getenv("VAPI_BASE_URL", "https://api.vapi.ai"),
    "api_key": os.getenv("VAPI_API_KEY"),
    "webhook_secret": os.getenv("VAPI_WEBHOOK_SECRET", "default-webhook-secret")
}


@router.post("/agents", response_model=Dict[str, Any])
async def create_vapi_agent(agent_data: VapiAgentCreate):
    """
    Create a new VAPI agent with the specified configuration.

    This endpoint:
    1. Creates the agent configuration in our database
    2. Creates the corresponding VAPI assistant
    3. Sets up webhook URLs
    4. Configures integrations and tools
    """
    # Feature flag for consolidated service (set to True to use new service)
    USE_CONSOLIDATED_SERVICE = os.getenv("VAPI_USE_CONSOLIDATED", "false").lower() == "true"

    if USE_CONSOLIDATED_SERVICE:
        # Use new consolidated VAPI service
        return await create_vapi_agent_consolidated(agent_data)

    # Legacy implementation (existing code)
    try:
        # Generate unique IDs
        agent_id = str(uuid.uuid4())
        webhook_url = f"https://api.ailabsafrica.com/vapi/webhooks/{agent_data.tenant_id}/{agent_id}"
        
        # Prepare VAPI assistant configuration
        vapi_assistant_config = {
            "name": agent_data.name,
            "model": {
                "provider": "openai",
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "system",
                        "content": agent_data.system_prompt
                    }
                ]
            },
            "voice": {
                "provider": "openai",
                "voiceId": agent_data.voice,
                "speed": agent_data.speed
            },
            "firstMessage": f"Hello! I'm {agent_data.name}. How can I help you today?",
            "recordingEnabled": agent_data.record_calls,
            "endCallMessage": "Thank you for calling. Have a great day!",
            "endCallPhrases": ["goodbye", "end call", "hang up"],
            "maxDurationSeconds": agent_data.max_duration,
            "silenceTimeoutSeconds": agent_data.silence_timeout,
            "responseDelaySeconds": 0.4,
            "interruptible": agent_data.interruptible,
            "numWordsToInterruptAssistant": 2,
            "backgroundSound": "office",
            "backchannelingEnabled": True,
            "backgroundDenoisingEnabled": True,
            "modelOutputInMessagesEnabled": True
        }
        
        # Add phone configuration if provided
        if agent_data.vapi_phone_id:
            vapi_assistant_config["phoneNumberId"] = agent_data.vapi_phone_id
        
        # Add webhook configuration
        if agent_data.enable_webhooks and agent_data.webhook_url:
            vapi_assistant_config["serverUrl"] = agent_data.webhook_url
            vapi_assistant_config["serverUrlSecret"] = VAPI_CONFIG["webhook_secret"]
        
        # Add tools based on selected integrations
        tools = []
        
        # Convert platform integrations to VAPI tools
        for integration_id in agent_data.integrations:
            tool_config = await convert_integration_to_vapi_tool(integration_id, agent_data.tenant_id)
            if tool_config:
                tools.append(tool_config)
        
        # Add custom tools
        for custom_tool in agent_data.custom_tools:
            tools.append({
                "type": "function",
                "function": {
                    "name": custom_tool["name"],
                    "description": custom_tool["description"],
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                "server": {
                    "url": custom_tool["webhook_url"],
                    "method": "POST"
                }
            })
        
        if tools:
            vapi_assistant_config["model"]["tools"] = tools
        
        # Create VAPI assistant
        vapi_assistant = await create_vapi_assistant(vapi_assistant_config)
        
        # Store agent configuration in our database
        agent_record = {
            "id": agent_id,
            "name": agent_data.name,
            "description": agent_data.description,
            "agent_type": agent_data.agent_type,
            "system_prompt": agent_data.system_prompt,
            "vapi_assistant_id": vapi_assistant.get("id"),
            "vapi_phone_id": agent_data.vapi_phone_id,
            "call_type": agent_data.call_type,
            "voice_settings": {
                "voice": agent_data.voice,
                "language": agent_data.language,
                "speed": agent_data.speed
            },
            "integrations": agent_data.integrations,
            "custom_tools": agent_data.custom_tools,
            "advanced_settings": {
                "max_duration": agent_data.max_duration,
                "silence_timeout": agent_data.silence_timeout,
                "interruptible": agent_data.interruptible,
                "record_calls": agent_data.record_calls
            },
            "webhook_settings": {
                "webhook_url": webhook_url,
                "enable_webhooks": agent_data.enable_webhooks
            },
            "tenant_id": agent_data.tenant_id,
            "created_with": agent_data.created_with,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        # Save to MongoDB
        from backend.database.mongodb import get_collection
        
        agents_collection = get_collection("vapi_agents")
        await agents_collection.insert_one(agent_record)
        
        logger.info(f"Created VAPI agent: {agent_record['id']}")
        
        return {
            "success": True,
            "agent": agent_record,
            "vapi_assistant_id": vapi_assistant.get("id"),
            "webhook_url": webhook_url,
            "message": f"VAPI agent '{agent_data.name}' created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating VAPI agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create VAPI agent: {str(e)}")


async def create_vapi_agent_consolidated(agent_data: VapiAgentCreate) -> Dict[str, Any]:
    """
    Create VAPI agent using the consolidated service.
    Maintains compatibility with existing API contract.
    """
    try:
        # Import the shared VAPI models
        from apps.shared.integration.vapi import VAPIAgent

        # Convert legacy request to new VAPIAgent model
        agent = VAPIAgent(
            name=agent_data.name,
            description=agent_data.description,
            system_prompt=agent_data.system_prompt,
            voice=agent_data.voice,
            language=agent_data.language,
            speed=agent_data.speed,
            max_duration=agent_data.max_duration,
            silence_timeout=agent_data.silence_timeout,
            interruptible=agent_data.interruptible,
            record_calls=agent_data.record_calls,
            integrations=agent_data.integrations,
            custom_tools=agent_data.custom_tools
        )

        # Use consolidated service for tenant-specific agent creation
        result = await vapi_service.create_tenant_agent(
            tenant_id=getattr(agent_data, 'tenant_id', 'default'),
            agent=agent,
            context={
                "source": "legacy_api",
                "agent_type": getattr(agent_data, 'agent_type', 'general'),
                "created_at": datetime.now().isoformat()
            }
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        # Transform response to match legacy API contract
        return {
            "success": True,
            "agent": {
                "id": result.get("agent_id"),
                "name": agent_data.name,
                "description": agent_data.description,
                "agent_type": getattr(agent_data, 'agent_type', 'general'),
                "tenant_id": getattr(agent_data, 'tenant_id', 'default'),
                "created_at": result.get("created_at"),
                "status": "active"
            },
            "vapi_assistant_id": result.get("agent_id"),
            "webhook_url": result.get("webhook_url", f"https://api.ailabsafrica.com/vapi/webhooks/{getattr(agent_data, 'tenant_id', 'default')}/{result.get('agent_id')}"),
            "message": f"VAPI agent '{agent_data.name}' created successfully via consolidated service"
        }

    except Exception as e:
        logger.error(f"Error creating VAPI agent via consolidated service: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create VAPI agent: {str(e)}")


@router.post("/webhooks/{tenant_id}/{agent_id}")
async def handle_vapi_webhook(
    tenant_id: str,
    agent_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle webhook callbacks from VAPI for call events and analytics.
    
    This endpoint processes:
    - Call start/end events
    - Call analytics and metrics
    - Usage and cost tracking
    - Integration tool calls
    """
    try:
        # Get request body
        body = await request.body()
        headers = dict(request.headers)
        
        # Parse webhook payload
        try:
            payload = json.loads(body.decode())
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Validate webhook signature
        if VAPI_CONFIG["webhook_secret"]:
            await validate_vapi_webhook_signature(body, headers)
        
        # Process the webhook event
        event_type = payload.get("type", "unknown")
        call_id = payload.get("call", {}).get("id", "")
        
        # Create webhook event record
        webhook_event = WebhookEvent(
            event_type=event_type,
            call_id=call_id,
            assistant_id=agent_id,
            data=payload
        )
        
        # Process in background
        background_tasks.add_task(
            process_vapi_webhook_event,
            tenant_id,
            agent_id,
            webhook_event
        )
        
        logger.info(f"Received VAPI webhook: {event_type} for agent {agent_id}")
        
        return {"success": True, "message": "Webhook processed"}
        
    except Exception as e:
        logger.error(f"Error processing VAPI webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.get("/agents/{agent_id}/analytics")
async def get_agent_analytics(agent_id: str, tenant_id: str = "default", days: int = 30):
    """
    Get analytics and usage statistics for a VAPI agent.

    Enhanced to use actual billing_records and automation_calls data.

    Returns:
    - Call volume and duration statistics
    - Success/failure rates
    - Cost and usage metrics with detailed breakdown
    - Integration tool usage
    """
    try:
        from datetime import datetime, timedelta
        from ..mongo import get_database
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../shared"))
        from apps.shared.services.billing_service import get_billing_service

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get database
        db = get_database()
        billing_service = get_billing_service(db)

        # Query billing_records for this agent
        billing_records = await billing_service.billing_collection.find({
            "metadata.assistant_id": agent_id,
            "call_started_at": {"$gte": start_date, "$lte": end_date}
        }).to_list(length=None)

        # Also query automation_calls for additional details
        calls_collection = db["automation_calls"]
        automation_calls = await calls_collection.find({
            "assistant_id": agent_id,
            "started_at": {"$gte": start_date, "$lte": end_date}
        }).to_list(length=None)

        # Merge data - prefer billing_records but supplement with automation_calls
        call_map = {call.get("call_id"): call for call in automation_calls}

        # Calculate metrics
        total_calls = len(billing_records) if billing_records else len(automation_calls)

        if billing_records:
            successful_calls = len([r for r in billing_records
                                   if r.get("metadata", {}).get("status") in ["ended", "completed"]])
            failed_calls = total_calls - successful_calls

            total_duration = sum(r.get("metadata", {}).get("duration", 0) for r in billing_records)
            avg_duration = total_duration / total_calls if total_calls > 0 else 0

            # Calculate costs with breakdown
            total_cost = sum(r.get("amount", 0) for r in billing_records)

            # Check if we have detailed cost breakdown in metadata
            has_breakdown = any(r.get("cost_breakdown") for r in billing_records)

            if has_breakdown:
                # Aggregate actual cost breakdowns
                voice_cost = sum(r.get("cost_breakdown", {}).get("voice_minutes", 0) for r in billing_records)
                ai_cost = sum(r.get("cost_breakdown", {}).get("ai_processing", 0) for r in billing_records)
                phone_cost = sum(r.get("cost_breakdown", {}).get("phone_charges", 0) for r in billing_records)
            else:
                # Use estimated breakdown (typical VAPI call composition)
                voice_cost = total_cost * 0.4
                ai_cost = total_cost * 0.4
                phone_cost = total_cost * 0.2

            # Track integration usage from metadata
            integration_usage = {}
            for record in billing_records:
                integrations = record.get("metadata", {}).get("integrations_used", [])
                for integration in integrations:
                    integration_usage[integration] = integration_usage.get(integration, 0) + 1

        elif automation_calls:
            # Fallback to automation_calls data
            successful_calls = len([c for c in automation_calls
                                   if c.get("status") in ["ended", "completed"]])
            failed_calls = total_calls - successful_calls

            total_duration = sum(c.get("duration", 0) for c in automation_calls)
            avg_duration = total_duration / total_calls if total_calls > 0 else 0

            total_cost = sum(c.get("vapi_cost", 0) for c in automation_calls)
            voice_cost = total_cost * 0.4
            ai_cost = total_cost * 0.4
            phone_cost = total_cost * 0.2

            integration_usage = {}
        else:
            # No data available
            successful_calls = 0
            failed_calls = 0
            total_duration = 0
            avg_duration = 0
            total_cost = 0
            voice_cost = 0
            ai_cost = 0
            phone_cost = 0
            integration_usage = {}

        # Construct response matching VapiAnalyticsDashboard expectations
        analytics = {
            "agent_id": agent_id,
            "tenant_id": tenant_id,
            "period": f"last_{days}_days",
            "calls": {
                "total": total_calls,
                "successful": successful_calls,
                "failed": failed_calls,
                "average_duration": int(avg_duration),
                "total_duration": int(total_duration)
            },
            "costs": {
                "total": round(total_cost, 4),
                "breakdown": {
                    "voice_minutes": round(voice_cost, 4),
                    "ai_processing": round(ai_cost, 4),
                    "phone_charges": round(phone_cost, 4)
                }
            },
            "integration_usage": integration_usage,
            "quality_metrics": {
                "completion_rate": round(successful_calls / total_calls, 2) if total_calls > 0 else 0,
                "success_rate": round(successful_calls / total_calls, 2) if total_calls > 0 else 0
            }
        }

        logger.info(f"Agent analytics for {agent_id}: {total_calls} calls, ${total_cost:.4f} total cost")

        return analytics

    except Exception as e:
        logger.error(f"Error fetching agent analytics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")


async def create_vapi_tool(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a VAPI tool using the VAPI API.
    """
    if not VAPI_CONFIG["api_key"]:
        logger.warning("VAPI API key not configured, using mock response")
        return {
            "id": str(uuid.uuid4()),
            "name": config.get("function", {}).get("name"),
            "status": "active",
            "created_at": datetime.utcnow().isoformat()
        }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{VAPI_CONFIG['api_url']}/tool",
                headers={
                    "Authorization": f"Bearer {VAPI_CONFIG['api_key']}",
                    "Content-Type": "application/json"
                },
                json=config,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating VAPI tool: {str(e)}")
            # Return mock response as fallback
            return {
                "id": str(uuid.uuid4()),
                "name": config.get("function", {}).get("name"),
                "status": "error",
                "created_at": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error creating VAPI tool: {str(e)}")
            return {
                "id": str(uuid.uuid4()),
                "name": config.get("function", {}).get("name"),
                "status": "error",
                "created_at": datetime.utcnow().isoformat(),
                "error": str(e)
            }


async def create_vapi_assistant(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a VAPI assistant using the VAPI API.
    """
    if not VAPI_CONFIG["api_key"]:
        logger.warning("VAPI API key not configured, using mock response")
        return {
            "id": str(uuid.uuid4()),
            "name": config.get("name"),
            "status": "active",
            "created_at": datetime.utcnow().isoformat()
        }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{VAPI_CONFIG['api_url']}/assistant",
                headers={
                    "Authorization": f"Bearer {VAPI_CONFIG['api_key']}",
                    "Content-Type": "application/json"
                },
                json=config,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating VAPI assistant: {str(e)}")
            # Return mock response as fallback
            return {
                "id": str(uuid.uuid4()),
                "name": config.get("name"),
                "status": "error",
                "created_at": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error creating VAPI assistant: {str(e)}")
            return {
                "id": str(uuid.uuid4()),
                "name": config.get("name"),
                "status": "error",
                "created_at": datetime.utcnow().isoformat(),
                "error": str(e)
            }


async def convert_integration_to_vapi_tool(integration_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
    """
    Convert a platform integration to a VAPI tool configuration.
    
    This function maps our platform integrations to VAPI-compatible tool definitions.
    """
    # Integration mapping
    integration_tools = {
        "calendar": {
            "type": "function",
            "function": {
                "name": "check_calendar_availability",
                "description": "Check calendar availability and book appointments",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "Date to check (YYYY-MM-DD)"},
                        "time": {"type": "string", "description": "Preferred time (HH:MM)"},
                        "duration": {"type": "integer", "description": "Duration in minutes"}
                    },
                    "required": ["date", "time"]
                }
            },
            "server": {
                "url": f"https://api.ailabsafrica.com/integrations/calendar/{tenant_id}/availability",
                "method": "POST"
            }
        },
        "email": {
            "type": "function",
            "function": {
                "name": "send_email",
                "description": "Send emails to customers or leads",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email address"},
                        "subject": {"type": "string", "description": "Email subject"},
                        "body": {"type": "string", "description": "Email content"}
                    },
                    "required": ["to", "subject", "body"]
                }
            },
            "server": {
                "url": f"https://api.ailabsafrica.com/integrations/email/{tenant_id}/send",
                "method": "POST"
            }
        },
        "database": {
            "type": "function",
            "function": {
                "name": "query_customer_data",
                "description": "Query customer database for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Database query or customer identifier"},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Fields to retrieve"}
                    },
                    "required": ["query"]
                }
            },
            "server": {
                "url": f"https://api.ailabsafrica.com/integrations/database/{tenant_id}/query",
                "method": "POST"
            }
        },
        "crm": {
            "type": "function",
            "function": {
                "name": "update_lead_status",
                "description": "Update lead status and add notes in CRM",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lead_id": {"type": "string", "description": "Lead identifier"},
                        "status": {"type": "string", "description": "New lead status"},
                        "notes": {"type": "string", "description": "Notes to add"}
                    },
                    "required": ["lead_id", "status"]
                }
            },
            "server": {
                "url": f"https://api.ailabsafrica.com/integrations/crm/{tenant_id}/leads/update",
                "method": "POST"
            }
        }
    }
    
    return integration_tools.get(integration_id)


async def process_vapi_webhook_event(tenant_id: str, agent_id: str, event: WebhookEvent):
    """
    Background task to process VAPI webhook events.

    This function handles:
    - Call analytics storage
    - Usage tracking
    - Integration tool call logging
    - Cost calculation
    - Monitoring service integration
    """
    try:
        from backend.database.mongodb import get_collection
        from backend.services.automation_monitoring_service import AutomationMonitoringService

        # Store event in database
        events_collection = get_collection("vapi_webhook_events")
        event_doc = {
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "event_type": event.event_type,
            "call_id": event.call_id,
            "assistant_id": event.assistant_id,
            "data": event.data,
            "timestamp": event.timestamp,
            "processed_at": datetime.utcnow()
        }
        await events_collection.insert_one(event_doc)

        # Update analytics based on event type
        if event.event_type in ["call-start", "call-end", "call-completed"]:
            await update_call_analytics(tenant_id, agent_id, event)

        # Record VAPI call metrics in monitoring service for call-end events
        if event.event_type in ["call-end", "call-completed"]:
            monitoring_service = AutomationMonitoringService()

            call_data = event.data.get("call", {})

            # Extract relevant metrics
            call_metrics_data = {
                "automation_id": agent_id,  # Use agent_id as automation_id
                "campaign_id": call_data.get("metadata", {}).get("campaign_id"),
                "tenant_id": tenant_id,
                "call_duration": call_data.get("duration", 0),
                "call_status": event.event_type.replace("call-", ""),
                "cost": call_data.get("cost"),
                "metadata": {
                    "call_id": event.call_id,
                    "assistant_id": event.assistant_id,
                    "webhook_data": event.data
                }
            }

            # Extract transcript for sentiment analysis if available
            if "transcript" in call_data:
                call_metrics_data["transcript"] = call_data["transcript"]

            try:
                await monitoring_service.record_vapi_call_metrics(call_metrics_data)
                logger.info(f"Recorded VAPI call metrics for call {event.call_id}")
            except Exception as e:
                logger.error(f"Failed to record VAPI call metrics: {str(e)}")

        # Process tool calls if present
        if "toolCalls" in event.data:
            await process_tool_calls(tenant_id, agent_id, event.data["toolCalls"])

        logger.info(f"Processed webhook event: {event.event_type} for agent {agent_id}")

    except Exception as e:
        logger.error(f"Error processing webhook event: {str(e)}")


async def update_call_analytics(tenant_id: str, agent_id: str, event: WebhookEvent):
    """
    Update call analytics based on webhook events.
    """
    try:
        from backend.database.mongodb import get_collection
        
        analytics_collection = get_collection("vapi_analytics")
        
        # Create or update analytics record
        analytics_filter = {"agent_id": agent_id, "tenant_id": tenant_id, "date": datetime.utcnow().date().isoformat()}
        
        update_data = {"$inc": {}}
        
        if event.event_type == "call-start":
            update_data["$inc"]["calls.total"] = 1
            update_data["$inc"]["calls.started"] = 1
        elif event.event_type == "call-end":
            call_data = event.data.get("call", {})
            duration = call_data.get("durationSeconds", 0)
            cost = call_data.get("cost", 0)
            
            update_data["$inc"]["calls.completed"] = 1
            update_data["$inc"]["calls.total_duration"] = duration
            update_data["$inc"]["costs.total"] = cost
        
        if update_data["$inc"]:
            await analytics_collection.update_one(
                analytics_filter,
                update_data,
                upsert=True
            )
            
    except Exception as e:
        logger.error(f"Error updating analytics: {str(e)}")


async def process_tool_calls(tenant_id: str, agent_id: str, tool_calls: List[Dict[str, Any]]):
    """
    Process and log tool calls from VAPI webhooks.
    """
    try:
        from backend.database.mongodb import get_collection
        
        tool_calls_collection = get_collection("vapi_tool_calls")
        
        for tool_call in tool_calls:
            tool_doc = {
                "tenant_id": tenant_id,
                "agent_id": agent_id,
                "tool_call_id": tool_call.get("id"),
                "tool_name": tool_call.get("function", {}).get("name"),
                "tool_arguments": tool_call.get("function", {}).get("arguments"),
                "timestamp": datetime.utcnow()
            }
            await tool_calls_collection.insert_one(tool_doc)
            
    except Exception as e:
        logger.error(f"Error processing tool calls: {str(e)}")


async def validate_vapi_webhook_signature(body: bytes, headers: Dict[str, str]):
    """
    Validate VAPI webhook signature for security.
    """
    import hmac
    import hashlib
    
    signature = headers.get("x-vapi-signature")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")
    
    expected_signature = hmac.new(
        VAPI_CONFIG["webhook_secret"].encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


@router.get("/agents")
async def list_vapi_agents(tenant_id: str = "default", limit: int = 50, offset: int = 0):
    """
    List all VAPI agents for a tenant.
    """
    try:
        from backend.database.mongodb import get_collection
        
        agents_collection = get_collection("vapi_agents")
        
        # Build query filter
        filter_query = {"tenant_id": tenant_id, "status": "active"}
        
        # Get total count
        total = await agents_collection.count_documents(filter_query)
        
        # Get agents with pagination
        cursor = agents_collection.find(filter_query).skip(offset).limit(limit).sort("created_at", -1)
        agents = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string for JSON serialization
        for agent in agents:
            agent["_id"] = str(agent["_id"])
        
        return {
            "success": True,
            "agents": agents,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing VAPI agents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list agents")


@router.get("/agents/{agent_id}")
async def get_vapi_agent(agent_id: str, tenant_id: str = "default"):
    """
    Get a specific VAPI agent by ID.
    """
    try:
        from backend.database.mongodb import get_collection
        
        agents_collection = get_collection("vapi_agents")
        
        agent = await agents_collection.find_one({
            "id": agent_id,
            "tenant_id": tenant_id
        })
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Convert ObjectId to string
        agent["_id"] = str(agent["_id"])
        
        return {"success": True, "agent": agent}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching VAPI agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch agent")


@router.put("/agents/{agent_id}")
async def update_vapi_agent(agent_id: str, agent_data: VapiAgentCreate, tenant_id: str = "default"):
    """
    Update a VAPI agent configuration.
    """
    try:
        from backend.database.mongodb import get_collection
        
        agents_collection = get_collection("vapi_agents")
        
        # Update the agent record
        update_data = {
            "name": agent_data.name,
            "description": agent_data.description,
            "system_prompt": agent_data.system_prompt,
            "voice_settings": {
                "voice": agent_data.voice,
                "language": agent_data.language,
                "speed": agent_data.speed
            },
            "integrations": agent_data.integrations,
            "custom_tools": agent_data.custom_tools,
            "advanced_settings": {
                "max_duration": agent_data.max_duration,
                "silence_timeout": agent_data.silence_timeout,
                "interruptible": agent_data.interruptible,
                "record_calls": agent_data.record_calls
            },
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = await agents_collection.update_one(
            {"id": agent_id, "tenant_id": tenant_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # TODO: Update VAPI assistant configuration
        
        return {
            "success": True,
            "message": f"Agent {agent_id} updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating VAPI agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update agent")


@router.delete("/agents/{agent_id}")
async def delete_vapi_agent(agent_id: str, tenant_id: str = "default"):
    """
    Delete a VAPI agent.
    """
    try:
        from backend.database.mongodb import get_collection
        
        agents_collection = get_collection("vapi_agents")
        
        # Soft delete - mark as inactive
        result = await agents_collection.update_one(
            {"id": agent_id, "tenant_id": tenant_id},
            {"$set": {"status": "deleted", "deleted_at": datetime.utcnow().isoformat()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # TODO: Delete VAPI assistant
        
        return {
            "success": True,
            "message": f"Agent {agent_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting VAPI agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete agent")


@router.post("/upload-file")
async def upload_file_to_vapi(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Upload a file to VAPI for knowledge base integration.
    
    Supports PDF, Word, TXT, CSV, Markdown, JSON, and XML files.
    Maximum file size: 300KB as recommended by VAPI.
    """
    try:
        # Validate file type
        supported_types = [
            'application/pdf',
            'application/msword', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'text/csv',
            'text/markdown',
            'application/json',
            'text/xml',
            'application/xml'
        ]
        
        if file.content_type not in supported_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file.content_type}. Supported types: PDF, Word, TXT, CSV, Markdown, JSON, XML"
            )
        
        # Validate file size (300KB limit as per VAPI recommendation)
        file_content = await file.read()
        if len(file_content) > 300 * 1024:  # 300KB
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 300KB limit. Please use a smaller file."
            )
        
        # Prepare the file for VAPI upload
        vapi_api_key = os.getenv("VAPI_API_KEY")
        if not vapi_api_key:
            raise HTTPException(status_code=500, detail="VAPI API key not configured")
        
        # Create a new upload file object with the content
        files = {
            'file': (file.filename, file_content, file.content_type)
        }
        
        # Upload to VAPI
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.vapi.ai/file",
                headers={
                    "Authorization": f"Bearer {vapi_api_key}"
                },
                files=files,
                timeout=30.0
            )
        
        if not response.is_success:
            logger.error(f"VAPI file upload failed: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"VAPI upload failed: {response.text}"
            )
        
        vapi_file_data = response.json()
        
        # Store file metadata in our database
        files_collection = get_collection("vapi_files")
        
        file_record = {
            "id": str(uuid.uuid4()),
            "vapi_file_id": vapi_file_data.get("id"),
            "tenant_id": current_user.get("tenant_id", "default"),
            "user_id": current_user.get("sub"),
            "original_name": file.filename,
            "content_type": file.content_type,
            "file_size": len(file_content),
            "vapi_metadata": vapi_file_data,
            "upload_status": "completed",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        files_collection.insert_one(file_record)
        
        return {
            "success": True,
            "file_id": file_record["id"],
            "vapi_file_id": vapi_file_data.get("id"),
            "filename": file.filename,
            "size": len(file_content),
            "status": "uploaded",
            "url": vapi_file_data.get("url"),
            "metadata": vapi_file_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file to VAPI: {str(e)}")
        raise HTTPException(status_code=500, detail="File upload failed")


@router.get("/files")
async def list_uploaded_files(current_user: dict = Depends(get_current_user_mongo)):
    """
    List all files uploaded by the current user for VAPI knowledge bases.
    """
    try:
        files_collection = get_collection("vapi_files")
        
        files = list(files_collection.find(
            {
                "tenant_id": current_user.get("tenant_id", "default"),
                "upload_status": "completed"
            },
            {
                "vapi_metadata.url": 0  # Don't return full URLs for security
            }
        ).sort("created_at", -1))
        
        # Convert MongoDB _id to string and clean up
        for file_record in files:
            file_record["_id"] = str(file_record["_id"])
        
        return {
            "success": True,
            "files": files
        }
        
    except Exception as e:
        logger.error(f"Error listing VAPI files: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list files")


@router.delete("/files/{file_id}")
async def delete_uploaded_file(
    file_id: str, 
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Delete an uploaded file from both our database and VAPI.
    """
    try:
        files_collection = get_collection("vapi_files")
        
        # Find the file record
        file_record = files_collection.find_one({
            "id": file_id,
            "tenant_id": current_user.get("tenant_id", "default")
        })
        
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete from our database
        files_collection.delete_one({"id": file_id})
        
        # TODO: Delete from VAPI if they provide a deletion endpoint
        # Currently VAPI doesn't seem to have a file deletion endpoint
        
        return {
            "success": True,
            "message": f"File {file_record['original_name']} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting VAPI file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete file")


@router.get("/integrations/available")
async def get_available_integrations(current_user: dict = Depends(get_current_user_mongo)):
    """
    Get available integrations for the current user's account.
    
    Returns only integrations that are activated for the user's account,
    rather than showing all possible integrations.
    """
    try:
        tenant_id = current_user.get("tenant_id", "default")
        
        # Check which integrations are activated for this tenant
        integrations_collection = get_collection("account_integrations")
        
        # Get activated integrations for this tenant
        activated_integrations = list(integrations_collection.find({
            "tenant_id": tenant_id,
            "status": "active"
        }))
        
        available_integrations = []
        
        for integration in activated_integrations:
            integration_id = integration["integration_id"]
            integration_name = integration["name"]
            
            # Map to our predefined integration categories
            integration_config = {
                "id": integration_id,
                "name": integration_name,
                "category": get_integration_category(integration_id),
                "description": get_integration_description(integration_id),
                "is_configured": True,
                "icon": get_integration_icon(integration_id),
                "capabilities": get_integration_capabilities(integration_id)
            }
            
            available_integrations.append(integration_config)
        
        # If no integrations are activated, provide default/demo integrations
        if not available_integrations:
            available_integrations = get_default_integrations()
        
        return {
            "success": True,
            "integrations": available_integrations,
            "total": len(available_integrations)
        }
        
    except Exception as e:
        logger.error(f"Error fetching available integrations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch integrations")


def get_integration_category(integration_id: str) -> str:
    """Map integration ID to category."""
    category_mapping = {
        "google_calendar": "productivity",
        "outlook_calendar": "productivity", 
        "calendly": "productivity",
        "sendgrid": "communication",
        "mailgun": "communication",
        "twilio": "communication",
        "hubspot": "crm",
        "salesforce": "crm",
        "pipedrive": "crm",
        "airtable": "database",
        "notion": "database",
        "google_sheets": "database",
        "stripe": "payment",
        "paypal": "payment",
        "slack": "communication",
        "discord": "communication",
        "zapier": "automation",
        "make": "automation"
    }
    return category_mapping.get(integration_id, "other")


def get_integration_description(integration_id: str) -> str:
    """Get description for integration."""
    descriptions = {
        "google_calendar": "Schedule appointments and check availability",
        "outlook_calendar": "Microsoft Outlook calendar integration",
        "calendly": "Automated scheduling and booking",
        "sendgrid": "Send transactional and marketing emails",
        "mailgun": "Email delivery and validation service",
        "twilio": "SMS and voice communication",
        "hubspot": "CRM and marketing automation",
        "salesforce": "Enterprise CRM platform",
        "pipedrive": "Sales pipeline management",
        "airtable": "Database and project management", 
        "notion": "All-in-one workspace",
        "google_sheets": "Spreadsheet data management",
        "stripe": "Payment processing and billing",
        "paypal": "Online payments and invoicing",
        "slack": "Team messaging and collaboration",
        "discord": "Community and voice chat",
        "zapier": "App integration and automation",
        "make": "Visual automation platform"
    }
    return descriptions.get(integration_id, "Third-party service integration")


def get_integration_icon(integration_id: str) -> str:
    """Get icon for integration."""
    icons = {
        "google_calendar": "📅",
        "outlook_calendar": "📅", 
        "calendly": "📅",
        "sendgrid": "📧",
        "mailgun": "📧",
        "twilio": "📱",
        "hubspot": "🎯",
        "salesforce": "🎯",
        "pipedrive": "🎯",
        "airtable": "📊", 
        "notion": "📝",
        "google_sheets": "📊",
        "stripe": "💳",
        "paypal": "💳",
        "slack": "💬",
        "discord": "💬",
        "zapier": "🔗",
        "make": "🔗"
    }
    return icons.get(integration_id, "🔧")


def get_integration_capabilities(integration_id: str) -> List[str]:
    """Get capabilities for integration."""
    capabilities = {
        "google_calendar": ["schedule_appointments", "check_availability", "send_reminders"],
        "outlook_calendar": ["schedule_appointments", "check_availability", "send_reminders"],
        "calendly": ["automated_booking", "availability_checking", "meeting_links"],
        "sendgrid": ["send_emails", "email_templates", "delivery_tracking"],
        "mailgun": ["send_emails", "email_validation", "analytics"],
        "twilio": ["send_sms", "make_calls", "verify_phone"],
        "hubspot": ["manage_contacts", "track_deals", "send_emails", "create_tasks"],
        "salesforce": ["manage_leads", "update_opportunities", "create_cases"],
        "pipedrive": ["manage_deals", "track_activities", "update_contacts"],
        "airtable": ["query_data", "create_records", "update_records"],
        "notion": ["create_pages", "query_database", "update_properties"],
        "google_sheets": ["read_data", "write_data", "create_sheets"],
        "stripe": ["process_payments", "create_invoices", "check_subscriptions"],
        "paypal": ["process_payments", "create_invoices", "send_money"],
        "slack": ["send_messages", "create_channels", "post_updates"],
        "discord": ["send_messages", "manage_roles", "create_invites"],
        "zapier": ["trigger_workflows", "pass_data", "connect_apps"],
        "make": ["run_scenarios", "process_data", "integrate_services"]
    }
    return capabilities.get(integration_id, ["basic_integration"])


class TemplateAgentCreate(BaseModel):
    template_id: str = Field(..., description="Automation template ID")
    tenant_id: str = Field(..., description="Tenant ID")
    automation_id: str = Field(..., description="Deployed automation ID")
    customization: Optional[Dict[str, Any]] = Field({}, description="Custom agent configuration")


@router.post("/agents/from-template", response_model=Dict[str, Any])
async def create_agent_from_template(agent_data: TemplateAgentCreate, current_user = Depends(get_current_user_mongo)):
    """
    Create a VAPI agent from an automation template with auto-configured webhooks.

    This endpoint:
    1. Loads the automation template configuration
    2. Generates VAPI agent using VAPIAgentGenerator service
    3. Creates VAPI assistant with template-specific functions
    4. Auto-configures webhooks to trigger automation workflows
    5. Stores complete agent and webhook configuration
    """
    try:
        # Import the template and generator services
        from apps.b2c_portal.src.config.automation_templates import AUTOMATION_TEMPLATES
        from apps.b2c_portal.src.services.VAPIAgentGenerator import VAPIAgentGenerator

        # Find the template
        template = None
        for tmpl in AUTOMATION_TEMPLATES:
            if tmpl["id"] == agent_data.template_id:
                template = tmpl
                break

        if not template:
            raise HTTPException(status_code=404, detail=f"Template {agent_data.template_id} not found")

        if not template.get("vapiConfig", {}).get("voiceAgentEnabled", False):
            raise HTTPException(status_code=400, detail=f"Template {agent_data.template_id} does not support voice agents")

        # Generate VAPI agent configuration using the service
        vapi_agent_config = VAPIAgentGenerator.generateVAPIAgent(
            template,
            agent_data.tenant_id,
            agent_data.customization
        )

        # Validate the generated configuration
        validation_result = VAPIAgentGenerator.validateVAPIAgent(vapi_agent_config)
        if not validation_result["valid"]:
            logger.error(f"Generated VAPI agent configuration is invalid: {validation_result['errors']}")
            raise HTTPException(status_code=400, detail=f"Invalid agent configuration: {', '.join(validation_result['errors'])}")

        # First, create tools in VAPI
        tool_ids = []
        if vapi_agent_config["functions"]:
            for func in vapi_agent_config["functions"]:
                tool_config = {
                    "type": "function",
                    "function": {
                        "name": func["name"],
                        "description": func["description"],
                        "parameters": func["parameters"]
                    },
                    "server": {
                        "url": vapi_agent_config["serverUrl"],
                        "secret": vapi_agent_config["serverUrlSecret"]
                    },
                    "async": True
                }

                # Create tool in VAPI
                tool_response = await create_vapi_tool(tool_config)
                tool_ids.append(tool_response.get("id"))

        # Create VAPI assistant with the generated configuration
        vapi_assistant_config = {
            "name": vapi_agent_config["name"],
            "model": {
                "provider": vapi_agent_config["model"]["provider"],
                "model": vapi_agent_config["model"]["model"],
                "temperature": vapi_agent_config["model"]["temperature"],
                "messages": [
                    {
                        "role": "system",
                        "content": vapi_agent_config["model"]["systemPrompt"]
                    }
                ]
            },
            "voice": vapi_agent_config["voice"],
            "firstMessage": vapi_agent_config["firstMessage"],
            "endCallMessage": vapi_agent_config["endCallMessage"],
            "maxDurationSeconds": vapi_agent_config["maxDuration"],
            "silenceTimeoutSeconds": vapi_agent_config["silenceTimeout"],
            "server": {
                "url": vapi_agent_config["serverUrl"],
                "secret": vapi_agent_config["serverUrlSecret"]
            },
            "serverMessages": [
                "end-of-call-report",
                "function-call",
                "tool-calls"
            ],
            "recordingEnabled": vapi_agent_config["recordingEnabled"],
            "transcriber": {
                "provider": "deepgram",
                "model": "nova-2-general"
            }
        }

        # Add tool IDs to model if we have functions
        if tool_ids:
            vapi_assistant_config["model"]["toolIds"] = tool_ids

        # Create VAPI assistant
        vapi_assistant = await create_vapi_assistant(vapi_assistant_config)

        # Generate unique agent ID
        agent_id = str(uuid.uuid4())

        # Store complete agent configuration
        agent_record = {
            "id": agent_id,
            "name": vapi_agent_config["name"],
            "template_id": agent_data.template_id,
            "automation_id": agent_data.automation_id,
            "tenant_id": agent_data.tenant_id,
            "vapi_assistant_id": vapi_assistant.get("id"),
            "agent_type": "template_generated",
            "system_prompt": vapi_agent_config["model"]["systemPrompt"],
            "voice_settings": vapi_agent_config["voice"],
            "conversation_settings": {
                "firstMessage": vapi_agent_config["firstMessage"],
                "endCallMessage": vapi_agent_config["endCallMessage"],
                "maxDuration": vapi_agent_config["maxDuration"],
                "silenceTimeout": vapi_agent_config["silenceTimeout"],
                "interruptible": vapi_agent_config["interruptible"]
            },
            "recording_settings": {
                "recordingEnabled": vapi_agent_config["recordingEnabled"],
                "transcriptionEnabled": vapi_agent_config["transcriptionEnabled"]
            },
            "webhook_settings": {
                "serverUrl": vapi_agent_config["serverUrl"],
                "serverUrlSecret": vapi_agent_config["serverUrlSecret"],
                "webhookEndpoint": f"/vapi/webhooks/{agent_data.tenant_id}/{agent_data.template_id}/{agent_id}"
            },
            "functions": vapi_agent_config["functions"],
            "metadata": vapi_agent_config["metadata"],
            "customization": agent_data.customization,
            "validation_result": validation_result,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }

        # Save to MongoDB
        agents_collection = get_collection("vapi_agents")
        await agents_collection.insert_one(agent_record)

        # Create webhook configuration record for automation integration
        webhook_record = {
            "id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "automation_id": agent_data.automation_id,
            "template_id": agent_data.template_id,
            "tenant_id": agent_data.tenant_id,
            "webhook_url": vapi_agent_config["serverUrl"],
            "webhook_secret": vapi_agent_config["serverUrlSecret"],
            "function_mappings": {func["name"]: func.get("workflowStepId") for func in vapi_agent_config["functions"] if func.get("workflowStepId")},
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }

        webhooks_collection = get_collection("vapi_webhooks")
        await webhooks_collection.insert_one(webhook_record)

        logger.info(f"Created template-based VAPI agent: {agent_id} from template: {agent_data.template_id}")

        return {
            "success": True,
            "agent": agent_record,
            "webhook_config": webhook_record,
            "vapi_assistant_id": vapi_assistant.get("id"),
            "validation_warnings": validation_result.get("warnings", []),
            "message": f"VAPI agent created successfully from template '{template['name']}'"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating VAPI agent from template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create VAPI agent from template: {str(e)}")


@router.post("/webhooks/{tenant_id}/{template_id}/{agent_id}")
async def handle_template_vapi_webhook(
    tenant_id: str,
    template_id: str,
    agent_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle webhook callbacks from VAPI for template-based agents.

    This endpoint:
    - Processes function calls from voice agents
    - Triggers corresponding automation workflow steps
    - Handles call events and analytics
    - Manages integration tool calls
    """
    try:
        # Get request body and headers
        body = await request.body()
        headers = dict(request.headers)
        webhook_data = json.loads(body) if body else {}

        # Validate webhook secret
        webhook_secret = headers.get("x-vapi-secret")
        stored_webhook = await get_collection("vapi_webhooks").find_one({
            "agent_id": agent_id,
            "template_id": template_id,
            "tenant_id": tenant_id
        })

        if not stored_webhook or stored_webhook.get("webhook_secret") != webhook_secret:
            logger.warning(f"Invalid webhook secret for agent {agent_id}")
            raise HTTPException(status_code=401, detail="Invalid webhook secret")

        event_type = webhook_data.get("type")
        logger.info(f"Received VAPI webhook: {event_type} for agent {agent_id}")

        # Handle different event types
        if event_type == "function-call":
            # Process function call and trigger automation workflow
            await process_function_call(webhook_data, stored_webhook, background_tasks)

        elif event_type == "call-start":
            # Log call start
            await log_call_event(agent_id, "call_started", webhook_data)

        elif event_type == "call-end":
            # Log call end and analytics
            await log_call_event(agent_id, "call_ended", webhook_data)
            await process_call_analytics(agent_id, webhook_data, background_tasks)

        elif event_type == "transcript":
            # Store transcript data
            await store_transcript(agent_id, webhook_data)

        return {"success": True, "message": "Webhook processed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing template VAPI webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


async def process_function_call(webhook_data: Dict[str, Any], webhook_config: Dict[str, Any], background_tasks: BackgroundTasks):
    """Process function call from VAPI and trigger automation workflow step."""
    function_call = webhook_data.get("functionCall", {})
    function_name = function_call.get("name")
    function_parameters = function_call.get("parameters", {})

    # Get workflow step mapping
    function_mappings = webhook_config.get("function_mappings", {})
    workflow_step_id = function_mappings.get(function_name)

    if not workflow_step_id:
        logger.warning(f"No workflow step mapping found for function: {function_name}")
        return {"error": "Function not mapped to workflow step"}

    # Add background task to trigger automation workflow
    background_tasks.add_task(
        trigger_automation_workflow_step,
        webhook_config["automation_id"],
        workflow_step_id,
        function_parameters,
        webhook_data.get("call", {})
    )

    return {"success": True, "message": f"Function {function_name} processed"}


async def trigger_automation_workflow_step(automation_id: str, step_id: str, parameters: Dict[str, Any], call_context: Dict[str, Any]):
    """Trigger a specific step in an automation workflow."""
    try:
        # This would integrate with n8n or your automation engine
        # For now, we'll log the trigger and store it for processing

        execution_record = {
            "id": str(uuid.uuid4()),
            "automation_id": automation_id,
            "step_id": step_id,
            "trigger_source": "vapi_function_call",
            "parameters": parameters,
            "call_context": call_context,
            "triggered_at": datetime.utcnow().isoformat(),
            "status": "triggered"
        }

        executions_collection = get_collection("automation_executions")
        await executions_collection.insert_one(execution_record)

        logger.info(f"Triggered automation step {step_id} for automation {automation_id}")

    except Exception as e:
        logger.error(f"Error triggering automation workflow step: {str(e)}")


async def log_call_event(agent_id: str, event_type: str, event_data: Dict[str, Any]):
    """Log call events for analytics and monitoring."""
    try:
        event_record = {
            "id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        events_collection = get_collection("vapi_call_events")
        await events_collection.insert_one(event_record)

    except Exception as e:
        logger.error(f"Error logging call event: {str(e)}")


async def process_call_analytics(agent_id: str, call_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """Process call analytics data in the background."""
    try:
        analytics_record = {
            "id": str(uuid.uuid4()),
            "agent_id": call_data.get("assistant", {}).get("id"),
            "call_id": call_data.get("id"),
            "call_duration": call_data.get("endedAt", 0) - call_data.get("startedAt", 0) if call_data.get("endedAt") and call_data.get("startedAt") else 0,
            "cost": call_data.get("cost"),
            "transcript": call_data.get("transcript"),
            "summary": call_data.get("summary"),
            "analysis": call_data.get("analysis"),
            "processed_at": datetime.utcnow().isoformat()
        }

        analytics_collection = get_collection("vapi_analytics")
        await analytics_collection.insert_one(analytics_record)

    except Exception as e:
        logger.error(f"Error processing call analytics: {str(e)}")


async def store_transcript(agent_id: str, transcript_data: Dict[str, Any]):
    """Store call transcript data."""
    try:
        transcript_record = {
            "id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "call_id": transcript_data.get("call", {}).get("id"),
            "transcript": transcript_data.get("transcript"),
            "timestamp": datetime.utcnow().isoformat()
        }

        transcripts_collection = get_collection("vapi_transcripts")
        await transcripts_collection.insert_one(transcript_record)

    except Exception as e:
        logger.error(f"Error storing transcript: {str(e)}")


def get_default_integrations() -> List[Dict[str, Any]]:
    """Return default integrations when none are activated."""
    return [
        {
            "id": "calendar_basic",
            "name": "Basic Calendar",
            "category": "productivity",
            "description": "Basic calendar functionality for scheduling",
            "is_configured": False,
            "icon": "📅",
            "capabilities": ["schedule_appointments"]
        },
        {
            "id": "email_basic", 
            "name": "Basic Email",
            "category": "communication",
            "description": "Basic email sending functionality",
            "is_configured": False,
            "icon": "📧",
            "capabilities": ["send_emails"]
        }
    ]


@router.get("/phone-numbers")
async def get_vapi_phone_numbers(
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get list of available VAPI phone numbers.

    Returns:
        List of phone numbers with their IDs and metadata
    """
    try:
        # Import VAPI service
        import sys
        sys.path.append('/opt/kasaai/apps/shared')
        from integration.vapi import vapi_service

        # Fetch phone numbers from VAPI
        result = await vapi_service.list_phone_numbers()

        if result.get("success"):
            phone_numbers = result.get("phoneNumbers", [])

            # Format response
            formatted_numbers = []
            for phone in phone_numbers:
                formatted_numbers.append({
                    "id": phone.get("id"),
                    "number": phone.get("number"),
                    "name": phone.get("name"),
                    "provider": phone.get("provider"),
                    "assistantId": phone.get("assistantId")
                })

            return formatted_numbers
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to fetch phone numbers from VAPI")
            )

    except Exception as e:
        logger.error(f"Error fetching phone numbers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch phone numbers: {str(e)}"
        )


# Include the router in the main app
def get_router():
    return router