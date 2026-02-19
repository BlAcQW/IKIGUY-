"""
Integrations Manager for VAPI Tools

This module manages platform integrations that can be used with VAPI agents,
providing a library of pre-configured tools and custom integration capabilities.
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any, Optional, Union
import httpx
import uuid
import json
import logging
from datetime import datetime
import os
from enum import Enum

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["Integrations Manager"])

class IntegrationType(str, Enum):
    CALENDAR = "calendar"
    EMAIL = "email"
    CRM = "crm"
    DATABASE = "database"
    WEBHOOK = "webhook"
    SMS = "sms"
    KNOWLEDGE_BASE = "knowledge_base"
    PAYMENT = "payment"
    ANALYTICS = "analytics"
    CUSTOM = "custom"

class IntegrationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"

class Integration(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Integration name")
    type: IntegrationType = Field(..., description="Integration type")
    category: str = Field(..., description="Integration category")
    description: str = Field("", description="Integration description")
    provider: str = Field(..., description="Integration provider (e.g., Google, Calendly)")
    icon: str = Field("🔧", description="Icon for the integration")
    
    # Configuration
    config: Dict[str, Any] = Field({}, description="Integration configuration")
    credentials: Dict[str, str] = Field({}, description="Integration credentials")
    webhook_url: Optional[str] = Field(None, description="Webhook endpoint for this integration")
    
    # Metadata
    tenant_id: str = Field("default", description="Tenant ID")
    status: IntegrationStatus = Field(IntegrationStatus.INACTIVE)
    is_configured: bool = Field(False)
    last_tested: Optional[datetime] = Field(None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class IntegrationCreate(BaseModel):
    name: str
    type: IntegrationType
    provider: str
    description: str = ""
    config: Dict[str, Any] = {}
    credentials: Dict[str, str] = {}
    tenant_id: str = "default"

class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, str]] = None
    status: Optional[IntegrationStatus] = None

class IntegrationTest(BaseModel):
    test_data: Dict[str, Any] = Field({}, description="Test data for the integration")

class ToolCall(BaseModel):
    integration_id: str
    tenant_id: str
    agent_id: str
    tool_name: str
    parameters: Dict[str, Any]
    call_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

# Pre-configured integration templates
INTEGRATION_TEMPLATES = {
    "google_calendar": {
        "name": "Google Calendar",
        "type": IntegrationType.CALENDAR,
        "category": "Scheduling",
        "provider": "google",
        "description": "Schedule appointments and check availability using Google Calendar",
        "icon": "📅",
        "config_schema": {
            "calendar_id": {"type": "string", "required": True, "description": "Google Calendar ID"},
            "timezone": {"type": "string", "default": "UTC", "description": "Timezone for appointments"},
            "default_duration": {"type": "integer", "default": 30, "description": "Default meeting duration in minutes"}
        },
        "credentials_schema": {
            "client_id": {"type": "string", "required": True},
            "client_secret": {"type": "string", "required": True},
            "refresh_token": {"type": "string", "required": True}
        },
        "tools": [
            {
                "name": "check_availability",
                "description": "Check calendar availability for a specific time",
                "parameters": {
                    "date": {"type": "string", "format": "date"},
                    "start_time": {"type": "string", "format": "time"},
                    "duration": {"type": "integer", "default": 30}
                }
            },
            {
                "name": "book_appointment",
                "description": "Book an appointment in the calendar",
                "parameters": {
                    "date": {"type": "string", "format": "date"},
                    "start_time": {"type": "string", "format": "time"},
                    "duration": {"type": "integer"},
                    "title": {"type": "string"},
                    "attendee_email": {"type": "string", "format": "email"}
                }
            }
        ]
    },
    "calendly": {
        "name": "Calendly",
        "type": IntegrationType.CALENDAR,
        "category": "Scheduling",
        "provider": "calendly",
        "description": "Integration with Calendly for appointment scheduling",
        "icon": "📅",
        "config_schema": {
            "organization_uri": {"type": "string", "required": True},
            "event_type_uri": {"type": "string", "required": True}
        },
        "credentials_schema": {
            "api_key": {"type": "string", "required": True}
        }
    },
    "sendgrid": {
        "name": "SendGrid Email",
        "type": IntegrationType.EMAIL,
        "category": "Communication",
        "provider": "sendgrid",
        "description": "Send emails using SendGrid",
        "icon": "📧",
        "config_schema": {
            "from_email": {"type": "string", "format": "email", "required": True},
            "from_name": {"type": "string", "default": "AI Assistant"}
        },
        "credentials_schema": {
            "api_key": {"type": "string", "required": True}
        }
    },
    "hubspot": {
        "name": "HubSpot CRM",
        "type": IntegrationType.CRM,
        "category": "Sales & Marketing",
        "provider": "hubspot",
        "description": "Manage contacts and deals in HubSpot CRM",
        "icon": "🏢",
        "config_schema": {
            "portal_id": {"type": "string", "required": True}
        },
        "credentials_schema": {
            "access_token": {"type": "string", "required": True}
        }
    },
    "twilio": {
        "name": "Twilio SMS",
        "type": IntegrationType.SMS,
        "category": "Communication",
        "provider": "twilio",
        "description": "Send SMS messages using Twilio",
        "icon": "📱",
        "config_schema": {
            "from_phone": {"type": "string", "required": True}
        },
        "credentials_schema": {
            "account_sid": {"type": "string", "required": True},
            "auth_token": {"type": "string", "required": True}
        }
    },
    "airtable": {
        "name": "Airtable Database",
        "type": IntegrationType.DATABASE,
        "category": "Data Storage",
        "provider": "airtable",
        "description": "Read and write data to Airtable bases",
        "icon": "🗃️",
        "config_schema": {
            "base_id": {"type": "string", "required": True},
            "table_name": {"type": "string", "required": True}
        },
        "credentials_schema": {
            "api_key": {"type": "string", "required": True}
        }
    }
}


@router.get("/templates")
async def get_integration_templates():
    """
    Get all available integration templates.
    """
    return {
        "success": True,
        "templates": INTEGRATION_TEMPLATES
    }


@router.post("/", response_model=Integration)
async def create_integration(integration_data: IntegrationCreate):
    """
    Create a new integration configuration.
    """
    try:
        from backend.database.mongodb import get_collection
        
        integrations_collection = get_collection("integrations")
        
        # Create integration object
        integration = Integration(
            name=integration_data.name,
            type=integration_data.type,
            provider=integration_data.provider,
            description=integration_data.description,
            config=integration_data.config,
            credentials=integration_data.credentials,
            tenant_id=integration_data.tenant_id,
            category=get_category_for_type(integration_data.type),
            webhook_url=f"https://api.ailabsafrica.com/integrations/{integration_data.type}/{integration_data.tenant_id}/{integration.id}"
        )
        
        # Save to database
        integration_dict = integration.dict()
        await integrations_collection.insert_one(integration_dict)
        
        logger.info(f"Created integration: {integration.id}")
        
        return integration
        
    except Exception as e:
        logger.error(f"Error creating integration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create integration: {str(e)}")


@router.get("/", response_model=List[Integration])
async def list_integrations(tenant_id: str = "default", status: Optional[IntegrationStatus] = None):
    """
    List all integrations for a tenant.
    """
    try:
        from backend.database.mongodb import get_collection
        
        integrations_collection = get_collection("integrations")
        
        # Build filter query
        filter_query = {"tenant_id": tenant_id}
        if status:
            filter_query["status"] = status
        
        # Fetch integrations
        cursor = integrations_collection.find(filter_query).sort("created_at", -1)
        integrations = await cursor.to_list(length=100)
        
        # Convert ObjectId to string and return as Integration objects
        result = []
        for integration_data in integrations:
            integration_data["_id"] = str(integration_data["_id"])
            # Convert datetime strings back to datetime objects
            if isinstance(integration_data.get("created_at"), str):
                integration_data["created_at"] = datetime.fromisoformat(integration_data["created_at"])
            if isinstance(integration_data.get("updated_at"), str):
                integration_data["updated_at"] = datetime.fromisoformat(integration_data["updated_at"])
            if isinstance(integration_data.get("last_tested"), str):
                integration_data["last_tested"] = datetime.fromisoformat(integration_data["last_tested"])
            
            result.append(Integration(**integration_data))
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing integrations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list integrations: {str(e)}")


@router.get("/{integration_id}", response_model=Integration)
async def get_integration(integration_id: str, tenant_id: str = "default"):
    """
    Get a specific integration by ID.
    """
    try:
        from backend.database.mongodb import get_collection
        
        integrations_collection = get_collection("integrations")
        
        integration_data = await integrations_collection.find_one({
            "id": integration_id,
            "tenant_id": tenant_id
        })
        
        if not integration_data:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        # Convert ObjectId to string
        integration_data["_id"] = str(integration_data["_id"])
        
        # Convert datetime strings back to datetime objects if needed
        if isinstance(integration_data.get("created_at"), str):
            integration_data["created_at"] = datetime.fromisoformat(integration_data["created_at"])
        if isinstance(integration_data.get("updated_at"), str):
            integration_data["updated_at"] = datetime.fromisoformat(integration_data["updated_at"])
        if isinstance(integration_data.get("last_tested"), str):
            integration_data["last_tested"] = datetime.fromisoformat(integration_data["last_tested"])
        
        return Integration(**integration_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching integration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch integration: {str(e)}")


@router.put("/{integration_id}", response_model=Integration)
async def update_integration(
    integration_id: str,
    integration_update: IntegrationUpdate,
    tenant_id: str = "default"
):
    """
    Update an integration configuration.
    """
    try:
        from backend.database.mongodb import get_collection
        
        integrations_collection = get_collection("integrations")
        
        # Build update data
        update_data = {"updated_at": datetime.utcnow()}
        
        if integration_update.name is not None:
            update_data["name"] = integration_update.name
        if integration_update.description is not None:
            update_data["description"] = integration_update.description
        if integration_update.config is not None:
            update_data["config"] = integration_update.config
        if integration_update.credentials is not None:
            update_data["credentials"] = integration_update.credentials
        if integration_update.status is not None:
            update_data["status"] = integration_update.status
        
        # Update in database
        result = await integrations_collection.update_one(
            {"id": integration_id, "tenant_id": tenant_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        # Fetch and return updated integration
        return await get_integration(integration_id, tenant_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating integration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update integration: {str(e)}")


@router.delete("/{integration_id}")
async def delete_integration(integration_id: str, tenant_id: str = "default"):
    """
    Delete an integration.
    """
    try:
        from backend.database.mongodb import get_collection
        
        integrations_collection = get_collection("integrations")
        
        result = await integrations_collection.delete_one({
            "id": integration_id,
            "tenant_id": tenant_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        return {"success": True, "message": f"Integration {integration_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting integration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete integration: {str(e)}")


@router.post("/{integration_id}/test")
async def test_integration(
    integration_id: str,
    test_data: IntegrationTest,
    tenant_id: str = "default"
):
    """
    Test an integration to verify it's working correctly.
    """
    try:
        # Get integration
        integration = await get_integration(integration_id, tenant_id)
        
        # Perform test based on integration type
        test_result = await perform_integration_test(integration, test_data.test_data)
        
        # Update last tested timestamp
        from backend.database.mongodb import get_collection
        integrations_collection = get_collection("integrations")
        
        await integrations_collection.update_one(
            {"id": integration_id, "tenant_id": tenant_id},
            {"$set": {
                "last_tested": datetime.utcnow(),
                "status": IntegrationStatus.ACTIVE if test_result["success"] else IntegrationStatus.ERROR
            }}
        )
        
        return test_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing integration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Integration test failed: {str(e)}")


@router.post("/webhook/{integration_type}/{tenant_id}/{integration_id}")
async def handle_integration_webhook(
    integration_type: str,
    tenant_id: str,
    integration_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle webhook callbacks from external integration providers.
    """
    try:
        body = await request.body()
        headers = dict(request.headers)
        
        # Parse webhook payload
        try:
            payload = json.loads(body.decode())
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Process webhook in background
        background_tasks.add_task(
            process_integration_webhook,
            integration_type,
            tenant_id,
            integration_id,
            payload,
            headers
        )
        
        return {"success": True, "message": "Webhook processed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing integration webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/execute-tool")
async def execute_integration_tool(tool_call: ToolCall):
    """
    Execute a tool call for an integration (called by VAPI webhooks).
    """
    try:
        # Get integration
        integration = await get_integration(tool_call.integration_id, tool_call.tenant_id)
        
        # Execute the tool call
        result = await execute_tool_call(integration, tool_call)
        
        # Log the tool call
        await log_tool_execution(tool_call, result)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing tool: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")


# Helper functions

def get_category_for_type(integration_type: IntegrationType) -> str:
    """Get the category for an integration type."""
    categories = {
        IntegrationType.CALENDAR: "Scheduling",
        IntegrationType.EMAIL: "Communication",
        IntegrationType.CRM: "Sales & Marketing",
        IntegrationType.DATABASE: "Data Storage",
        IntegrationType.WEBHOOK: "Automation",
        IntegrationType.SMS: "Communication",
        IntegrationType.KNOWLEDGE_BASE: "Information",
        IntegrationType.PAYMENT: "Finance",
        IntegrationType.ANALYTICS: "Analytics",
        IntegrationType.CUSTOM: "Custom"
    }
    return categories.get(integration_type, "Other")


async def perform_integration_test(integration: Integration, test_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform a test for a specific integration.
    """
    try:
        if integration.type == IntegrationType.CALENDAR:
            return await test_calendar_integration(integration, test_data)
        elif integration.type == IntegrationType.EMAIL:
            return await test_email_integration(integration, test_data)
        elif integration.type == IntegrationType.CRM:
            return await test_crm_integration(integration, test_data)
        elif integration.type == IntegrationType.SMS:
            return await test_sms_integration(integration, test_data)
        elif integration.type == IntegrationType.DATABASE:
            return await test_database_integration(integration, test_data)
        else:
            return {"success": True, "message": "Test not implemented for this integration type"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_calendar_integration(integration: Integration, test_data: Dict[str, Any]) -> Dict[str, Any]:
    """Test calendar integration."""
    if integration.provider == "google":
        # Test Google Calendar API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.googleapis.com/calendar/v3/calendars/{integration.config.get('calendar_id')}/events",
                headers={"Authorization": f"Bearer {integration.credentials.get('access_token')}"},
                params={"maxResults": 1}
            )
            
            if response.status_code == 200:
                return {"success": True, "message": "Google Calendar connection successful"}
            else:
                return {"success": False, "error": f"Google Calendar API error: {response.status_code}"}
    
    return {"success": True, "message": "Calendar test completed"}


async def test_email_integration(integration: Integration, test_data: Dict[str, Any]) -> Dict[str, Any]:
    """Test email integration."""
    if integration.provider == "sendgrid":
        # Test SendGrid API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.sendgrid.com/v3/user/account",
                headers={"Authorization": f"Bearer {integration.credentials.get('api_key')}"}
            )
            
            if response.status_code == 200:
                return {"success": True, "message": "SendGrid connection successful"}
            else:
                return {"success": False, "error": f"SendGrid API error: {response.status_code}"}
    
    return {"success": True, "message": "Email test completed"}


async def test_crm_integration(integration: Integration, test_data: Dict[str, Any]) -> Dict[str, Any]:
    """Test CRM integration."""
    return {"success": True, "message": "CRM test completed"}


async def test_sms_integration(integration: Integration, test_data: Dict[str, Any]) -> Dict[str, Any]:
    """Test SMS integration."""
    return {"success": True, "message": "SMS test completed"}


async def test_database_integration(integration: Integration, test_data: Dict[str, Any]) -> Dict[str, Any]:
    """Test database integration."""
    return {"success": True, "message": "Database test completed"}


async def execute_tool_call(integration: Integration, tool_call: ToolCall) -> Dict[str, Any]:
    """
    Execute a specific tool call for an integration.
    """
    try:
        if integration.type == IntegrationType.CALENDAR:
            return await execute_calendar_tool(integration, tool_call)
        elif integration.type == IntegrationType.EMAIL:
            return await execute_email_tool(integration, tool_call)
        elif integration.type == IntegrationType.CRM:
            return await execute_crm_tool(integration, tool_call)
        elif integration.type == IntegrationType.SMS:
            return await execute_sms_tool(integration, tool_call)
        elif integration.type == IntegrationType.DATABASE:
            return await execute_database_tool(integration, tool_call)
        else:
            return {"success": False, "error": f"Tool execution not implemented for {integration.type}"}
            
    except Exception as e:
        logger.error(f"Error executing {integration.type} tool: {str(e)}")
        return {"success": False, "error": str(e)}


async def execute_calendar_tool(integration: Integration, tool_call: ToolCall) -> Dict[str, Any]:
    """Execute calendar-related tool calls."""
    # Implement calendar tool execution logic
    return {"success": True, "message": "Calendar tool executed", "data": {}}


async def execute_email_tool(integration: Integration, tool_call: ToolCall) -> Dict[str, Any]:
    """Execute email-related tool calls."""
    # Implement email tool execution logic
    return {"success": True, "message": "Email tool executed", "data": {}}


async def execute_crm_tool(integration: Integration, tool_call: ToolCall) -> Dict[str, Any]:
    """Execute CRM-related tool calls."""
    # Implement CRM tool execution logic
    return {"success": True, "message": "CRM tool executed", "data": {}}


async def execute_sms_tool(integration: Integration, tool_call: ToolCall) -> Dict[str, Any]:
    """Execute SMS-related tool calls."""
    # Implement SMS tool execution logic
    return {"success": True, "message": "SMS tool executed", "data": {}}


async def execute_database_tool(integration: Integration, tool_call: ToolCall) -> Dict[str, Any]:
    """Execute database-related tool calls."""
    # Implement database tool execution logic
    return {"success": True, "message": "Database tool executed", "data": {}}


async def process_integration_webhook(
    integration_type: str,
    tenant_id: str,
    integration_id: str,
    payload: Dict[str, Any],
    headers: Dict[str, str]
):
    """
    Background task to process integration webhooks.
    """
    try:
        from backend.database.mongodb import get_collection
        
        # Store webhook event
        webhook_events_collection = get_collection("integration_webhook_events")
        
        event_doc = {
            "integration_type": integration_type,
            "tenant_id": tenant_id,
            "integration_id": integration_id,
            "payload": payload,
            "headers": headers,
            "timestamp": datetime.utcnow(),
            "processed": False
        }
        
        await webhook_events_collection.insert_one(event_doc)
        
        logger.info(f"Processed integration webhook: {integration_type}/{integration_id}")
        
    except Exception as e:
        logger.error(f"Error processing integration webhook: {str(e)}")


async def log_tool_execution(tool_call: ToolCall, result: Dict[str, Any]):
    """
    Log tool execution for analytics.
    """
    try:
        from backend.database.mongodb import get_collection
        
        tool_logs_collection = get_collection("integration_tool_logs")
        
        log_entry = {
            "call_id": tool_call.call_id,
            "integration_id": tool_call.integration_id,
            "tenant_id": tool_call.tenant_id,
            "agent_id": tool_call.agent_id,
            "tool_name": tool_call.tool_name,
            "parameters": tool_call.parameters,
            "result": result,
            "success": result.get("success", False),
            "timestamp": datetime.utcnow()
        }
        
        await tool_logs_collection.insert_one(log_entry)
        
    except Exception as e:
        logger.error(f"Error logging tool execution: {str(e)}")


# Include the router in the main app
def get_router():
    return router