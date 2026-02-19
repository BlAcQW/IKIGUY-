"""
Custom Tools Management API Routes
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging

from ..services.custom_tools_service import custom_tools_service
from ..auth import get_current_user_mongo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/custom-tools", tags=["custom-tools"])

class ToolRegistrationRequest(BaseModel):
    file_path: str
    client_id: str
    industry: str = "general"
    category: str = "utility"
    description: str = ""
    metadata: Optional[Dict[str, Any]] = None

@router.post("/register")
async def register_tools(
    request: ToolRegistrationRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Register custom tools from a Python file."""
    try:
        result = await custom_tools_service.register_tool_from_file(
            file_path=request.file_path,
            client_id=request.client_id,
            industry=request.industry,
            category=request.category,
            description=request.description,
            metadata=request.metadata
        )

        if result["success"]:
            return {
                "message": f"Successfully registered {result['tools_registered']} tools",
                "tools": result["tools"],
                "tool_ids": result["tool_ids"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        logger.error(f"Tool registration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to register tools: {str(e)}")

@router.get("/")
async def get_tools(
    client_id: Optional[str] = None,
    industry: Optional[str] = None,
    category: Optional[str] = None,
    active_only: bool = True,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Get custom tools with optional filters."""
    try:
        tools = await custom_tools_service.get_all_tools(
            client_id=client_id,
            industry=industry,
            category=category,
            active_only=active_only
        )

        # Ensure tools is always a list
        if not isinstance(tools, list):
            tools = []

        # Extract unique categories
        categories = list(set(tool.get('category', 'utility') for tool in tools if isinstance(tool, dict)))

        return {
            "success": True,
            "tools": tools,
            "total": len(tools),
            "categories": categories,
            "count": len(tools),  # Backwards compatibility
            "filters": {
                "client_id": client_id,
                "industry": industry,
                "category": category,
                "active_only": active_only
            }
        }

    except Exception as e:
        logger.error(f"Failed to get tools: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tools: {str(e)}")

@router.post("/init/premier-health")
async def init_premier_health_tools(current_user: dict = Depends(get_current_user_mongo)):
    """Initialize Premier Health custom tools."""
    try:
        result = await custom_tools_service.register_tool_from_file(
            file_path="/opt/kasaai/apps/automations/premier-health/voice_agent_tools.py",
            client_id="premier-health",
            industry="healthcare",
            category="provider_search",
            description="Healthcare provider search and location tools for Premier Health Insurance",
            metadata={
                "company": "Premier Health Insurance Ghana",
                "contact": "info@premierhealthinsurance.org",
                "regions": ["Accra", "Koforidua", "Sunyani", "Kumasi", "Takoradi", "Cape Coast", "Techiman"]
            }
        )

        return {
            "message": "Premier Health tools initialized",
            "result": result
        }

    except Exception as e:
        logger.error(f"Failed to initialize Premier Health tools: {e}")
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")

@router.post("/init-rag-tools")
async def init_rag_tools(current_user: dict = Depends(get_current_user_mongo)):
    """
    Initialize Premier Health and Ghana Tourism RAG tools in MongoDB.

    This registers the RAG tools so they appear in the custom tools UI and are
    properly integrated with tool call logging.
    """
    try:
        import subprocess
        import sys

        # Run the registration script
        script_path = "/opt/kasaai/apps/automations/examples/register_rag_tools_mongodb.py"
        python_path = sys.executable

        logger.info(f"Running RAG tools registration script: {script_path}")

        result = subprocess.run(
            [python_path, script_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            logger.info("RAG tools registered successfully")
            return {
                "success": True,
                "message": "Premier Health and Ghana Tourism RAG tools registered successfully",
                "output": result.stdout
            }
        else:
            logger.error(f"RAG tools registration failed: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Registration failed: {result.stderr}"
            )

    except subprocess.TimeoutExpired:
        logger.error("RAG tools registration timed out")
        raise HTTPException(status_code=500, detail="Registration timed out after 30 seconds")
    except Exception as e:
        logger.error(f"Failed to initialize RAG tools: {e}")
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")

@router.post("/execute/{tool_id}")
async def execute_tool(
    tool_id: str,
    parameters: Dict[str, Any],
    current_user: dict = Depends(get_current_user_mongo)
):
    """Execute a custom tool by ID with provided parameters."""
    try:
        result = await custom_tools_service.execute_tool(tool_id, parameters)

        if result["success"]:
            return {
                "success": True,
                "result": result["result"],
                "tool_name": result["tool_name"],
                "executed_at": result["executed_at"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

@router.post("/{client_id}/{tool_name}")
async def execute_tool_by_name(
    client_id: str,
    tool_name: str,
    parameters: Dict[str, Any],
    current_user: dict = Depends(get_current_user_mongo)
):
    """Execute a custom tool by client ID and tool name."""
    try:
        # Find the tool by client_id and tool name
        tools = await custom_tools_service.get_all_tools(client_id=client_id)
        matching_tool = None

        for tool in tools:
            if tool["name"] == tool_name:
                matching_tool = tool
                break

        if not matching_tool:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found for client '{client_id}'"
            )

        # Execute the tool
        result = await custom_tools_service.execute_tool(matching_tool["id"], parameters)

        if result["success"]:
            return {
                "success": True,
                "result": result["result"],
                "tool_name": result["tool_name"],
                "executed_at": result["executed_at"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

# Database-driven tool registration endpoints
class DatabaseToolRegistrationRequest(BaseModel):
    name: str
    description: str
    schema: Dict[str, Any]
    client_id: str
    industry: str = "general"
    category: str = "utility"
    version: str = "1.0.0"
    tags: List[str] = []
    dependencies: List[str] = []
    code: Optional[str] = None
    endpoint: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    # VAPI integration fields
    vapi_tool_id: Optional[str] = None
    server_url: Optional[str] = None
    vapi_sync_status: Optional[str] = "pending"
    deployment_status: Optional[str] = "inactive"

class BulkToolRegistrationRequest(BaseModel):
    tools: List[DatabaseToolRegistrationRequest]
    client_id: str
    source: str = "bulk_import"

@router.post("/db/register")
async def register_tool_from_database(
    request: DatabaseToolRegistrationRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Register a custom tool directly in the database."""
    try:
        result = await custom_tools_service.register_tool_from_database(
            tool_data=request.dict(),
            source="database"
        )

        if result["success"]:
            return {
                "message": result["message"],
                "tool_id": result["tool_id"],
                "endpoint": result["endpoint"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        logger.error(f"Database tool registration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to register tool: {str(e)}")

@router.post("/db/bulk-register")
async def bulk_register_tools(
    request: BulkToolRegistrationRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Register multiple tools in bulk operation."""
    try:
        tools_data = [tool.dict() for tool in request.tools]
        result = await custom_tools_service.bulk_register_tools(
            tools_data=tools_data,
            client_id=request.client_id,
            source=request.source
        )

        if result["success"]:
            return {
                "message": f"Bulk registration completed",
                "total_processed": result["total_processed"],
                "successful_count": result["successful_count"],
                "failed_count": result["failed_count"],
                "results": result["results"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        logger.error(f"Bulk tool registration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk register tools: {str(e)}")

@router.get("/search")
async def search_tools(
    query: str,
    client_id: Optional[str] = None,
    industry: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Search tools using text search and filters."""
    try:
        filters = {}
        if client_id:
            filters["client_id"] = client_id
        if industry:
            filters["industry"] = industry
        if category:
            filters["category"] = category

        tools = await custom_tools_service.search_tools(
            query=query,
            filters=filters,
            limit=limit
        )

        return {
            "tools": tools,
            "count": len(tools),
            "query": query,
            "filters": filters
        }

    except Exception as e:
        logger.error(f"Tool search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search tools: {str(e)}")

@router.get("/analytics/{tool_id}")
async def get_tool_analytics(
    tool_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Get analytics data for a specific tool."""
    try:
        result = await custom_tools_service.get_tool_analytics(tool_id)

        if result["success"]:
            return {
                "analytics": result["analytics"],
                "tool_name": result["tool_name"],
                "client_id": result["client_id"]
            }
        else:
            raise HTTPException(status_code=404, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/summary/{client_id}")
async def get_client_tools_summary(
    client_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Get summary statistics for a client's tools."""
    try:
        result = await custom_tools_service.get_client_tools_summary(client_id)

        if result["success"]:
            return {
                "client_id": client_id,
                "summary": result["summary"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get client summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

@router.put("/{tool_id}")
async def update_tool(
    tool_id: str,
    updates: Dict[str, Any],
    current_user: dict = Depends(get_current_user_mongo)
):
    """Update tool metadata and configuration."""
    try:
        result = await custom_tools_service.update_tool(tool_id, updates)

        if result["success"]:
            return {"message": result["message"]}
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update tool: {str(e)}")

@router.delete("/{tool_id}")
async def deactivate_tool(
    tool_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Deactivate a tool (soft delete)."""
    try:
        result = await custom_tools_service.deactivate_tool(tool_id)

        if result["success"]:
            return {"message": "Tool deactivated successfully"}
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool deactivation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to deactivate tool: {str(e)}")

# VAPI Integration Endpoints

@router.post("/{tool_id}/sync-vapi")
async def sync_tool_with_vapi(
    tool_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Sync a specific tool with VAPI."""
    try:
        result = await custom_tools_service.sync_tool_with_vapi(tool_id)

        if result["success"]:
            return {
                "message": "Tool synced with VAPI successfully",
                "vapi_tool_id": result.get("vapi_tool_id"),
                "sync_status": "synced"
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"VAPI sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync with VAPI: {str(e)}")

@router.post("/bulk-sync-vapi")
async def bulk_sync_tools_with_vapi(
    client_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Bulk sync tools with VAPI."""
    try:
        result = await custom_tools_service.bulk_sync_tools_with_vapi(client_id)

        if result["success"]:
            return {
                "message": "Bulk sync completed",
                "total_processed": result["total_processed"],
                "successful_count": result["successful_count"],
                "failed_count": result["failed_count"],
                "results": result["results"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk VAPI sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk sync with VAPI: {str(e)}")

@router.get("/vapi-sync-status")
async def get_vapi_sync_status(
    client_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Get VAPI sync status for tools."""
    try:
        result = await custom_tools_service.get_vapi_sync_status(client_id)

        if result["success"]:
            return {
                "sync_status": result["sync_status"],
                "total_tools": result["total_tools"],
                "client_id": client_id
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get VAPI sync status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")

@router.post("/register-premier-health")
async def register_premier_health_tools(
    current_user: dict = Depends(get_current_user_mongo)
):
    """Register Premier Health tools with existing VAPI tool IDs."""
    try:
        result = await custom_tools_service.register_premier_health_tools()

        if result["success"]:
            return {
                "message": result["message"],
                "total_tools": result["total_tools"],
                "registration_result": result["result"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Premier Health tool registration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to register Premier Health tools: {str(e)}")

@router.get("/vapi-assistant/{assistant_id}")
async def get_tools_by_vapi_assistant(
    assistant_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Get tools associated with a specific VAPI assistant."""
    try:
        tools = await custom_tools_service.get_tools_by_vapi_assistant(assistant_id)

        return {
            "assistant_id": assistant_id,
            "tools": tools,
            "count": len(tools)
        }

    except Exception as e:
        logger.error(f"Failed to get tools for assistant {assistant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tools for assistant: {str(e)}")

# This dynamic route must come LAST to avoid catching specific routes above
@router.get("/{tool_id}")
async def get_tool_by_id(
    tool_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Get a specific custom tool by ID."""
    try:
        tool = await custom_tools_service.get_tool_by_id(tool_id)

        if tool:
            return {
                "success": True,
                "tool": tool
            }
        else:
            raise HTTPException(status_code=404, detail=f"Tool with ID '{tool_id}' not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool by ID: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tool: {str(e)}")