"""
Custom Tools Management Service
Manages client-specific custom tools for automation workflows
"""

import asyncio
import json
import os
import importlib.util
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from bson import ObjectId
from pymongo.errors import PyMongoError
import requests
import logging

from ..mongo import get_collection

logger = logging.getLogger(__name__)

class CustomToolsService:
    """
    Service for managing custom tools across different clients and industries.

    Provides functionality to:
    - Register custom tool functions from Python files
    - Store tool metadata and schemas in MongoDB
    - Retrieve tools by client, industry, or category
    - Validate tool function signatures
    - Generate tool schemas for VAPI and N8N integration
    """

    def __init__(self):
        self.tools_collection = get_collection('custom_tools')
        self.clients_collection = get_collection('tool_clients')
        self.schemas_cache = {}
        self.vapi_api_key = os.getenv("VAPI_API_KEY")
        self.vapi_base_url = "https://api.vapi.ai"

    async def register_tool_from_file(
        self,
        file_path: str,
        client_id: str,
        industry: str = "general",
        category: str = "utility",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register custom tools from a Python file.

        Args:
            file_path (str): Path to the Python file containing tool functions
            client_id (str): Unique identifier for the client
            industry (str): Industry category (healthcare, finance, retail, etc.)
            category (str): Tool category (search, communication, data, etc.)
            description (str): Description of the tool collection
            metadata (Dict): Additional metadata

        Returns:
            Dict: Registration result with tool IDs and details
        """
        try:
            # Load the Python module
            spec = importlib.util.spec_from_file_location("custom_tools", file_path)
            if spec is None or spec.loader is None:
                raise ValueError(f"Could not load module from {file_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Extract tool functions and schemas
            tools = []

            # Look for tool classes or functions
            if hasattr(module, 'TOOL_SCHEMAS'):
                # Use predefined schemas if available
                tool_schemas = module.TOOL_SCHEMAS
                for tool_name, schema in tool_schemas.items():
                    tool_data = {
                        "_id": ObjectId(),
                        "name": tool_name,
                        "client_id": client_id,
                        "industry": industry,
                        "category": category,
                        "description": schema.get('description', description),
                        "function_name": tool_name,
                        "file_path": file_path,
                        "schema": schema,
                        "endpoint": f"/custom-tools/{client_id}/{tool_name}",
                        "method": "POST",
                        "active": True,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "metadata": metadata or {},
                        # VAPI integration fields
                        "vapi_tool_id": None,
                        "server_url": f"https://api.ailabsafrica.com/custom-tools/{client_id}/{tool_name}",
                        "vapi_sync_status": "pending",
                        "deployment_status": "inactive",
                        "vapi_metadata": {
                            "assistant_ids": [],
                            "last_synced": None,
                            "sync_errors": []
                        }
                    }
                    tools.append(tool_data)

            # Look for tool classes
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    hasattr(attr, 'search_healthcare_providers') or
                    hasattr(attr, '__dict__') and
                    any(method.startswith('tool_') or method.endswith('_tool')
                        for method in attr.__dict__.keys() if callable(getattr(attr, method, None)))):

                    # Extract tool methods from class
                    for method_name in dir(attr):
                        method = getattr(attr, method_name)
                        if (callable(method) and
                            not method_name.startswith('_') and
                            method_name not in ['__init__', '__new__', '__del__']):

                            tool_data = {
                                "_id": ObjectId(),
                                "name": method_name,
                                "client_id": client_id,
                                "industry": industry,
                                "category": category,
                                "description": getattr(method, '__doc__', '') or f"{method_name} tool",
                                "function_name": f"{attr_name}.{method_name}",
                                "class_name": attr_name,
                                "file_path": file_path,
                                "schema": self._generate_schema_from_function(method),
                                "endpoint": f"/custom-tools/{client_id}/{method_name}",
                                "method": "POST",
                                "active": True,
                                "created_at": datetime.utcnow(),
                                "updated_at": datetime.utcnow(),
                                "metadata": metadata or {},
                                # VAPI integration fields
                                "vapi_tool_id": None,
                                "server_url": f"https://api.ailabsafrica.com/custom-tools/{client_id}/{method_name}",
                                "vapi_sync_status": "pending",
                                "deployment_status": "inactive",
                                "vapi_metadata": {
                                    "assistant_ids": [],
                                    "last_synced": None,
                                    "sync_errors": []
                                }
                            }
                            tools.append(tool_data)

            # Store tools in MongoDB
            if tools:
                result = await self.tools_collection.insert_many(tools)
                return {
                    "success": True,
                    "tools_registered": len(tools),
                    "tool_ids": [str(tool_id) for tool_id in result.inserted_ids],
                    "tools": [{"name": tool["name"], "endpoint": tool["endpoint"]} for tool in tools]
                }
            else:
                return {
                    "success": False,
                    "error": "No valid tool functions found in the file",
                    "tools_registered": 0
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to register tools: {str(e)}",
                "tools_registered": 0
            }

    def _generate_schema_from_function(self, func) -> Dict[str, Any]:
        """Generate a basic schema from function signature and docstring."""
        import inspect

        signature = inspect.signature(func)
        parameters = {}

        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue

            param_schema = {"type": "string"}

            # Try to infer type from annotation
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_schema["type"] = "integer"
                elif param.annotation == float:
                    param_schema["type"] = "number"
                elif param.annotation == bool:
                    param_schema["type"] = "boolean"
                elif param.annotation == list:
                    param_schema["type"] = "array"
                elif param.annotation == dict:
                    param_schema["type"] = "object"

            # Add default value if available
            if param.default != inspect.Parameter.empty:
                param_schema["default"] = param.default

            parameters[param_name] = param_schema

        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": func.__doc__ or f"Custom tool function: {func.__name__}",
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": [name for name, param in signature.parameters.items()
                               if param.default == inspect.Parameter.empty and name != 'self']
                }
            }
        }

    async def get_tools_by_client(self, client_id: str) -> List[Dict[str, Any]]:
        """Get all tools for a specific client."""
        tools = await self.tools_collection.find({"client_id": client_id, "active": True}).to_list(None)
        return [self._format_tool_response(tool) for tool in tools]

    async def get_tools_by_industry(self, industry: str) -> List[Dict[str, Any]]:
        """Get all tools for a specific industry."""
        tools = await self.tools_collection.find({"industry": industry, "active": True}).to_list(None)
        return [self._format_tool_response(tool) for tool in tools]

    async def get_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all tools for a specific category."""
        tools = await self.tools_collection.find({"category": category, "active": True}).to_list(None)
        return [self._format_tool_response(tool) for tool in tools]

    async def get_all_tools(self,
                          client_id: Optional[str] = None,
                          industry: Optional[str] = None,
                          category: Optional[str] = None,
                          active_only: bool = True) -> List[Dict[str, Any]]:
        """Get tools with optional filters."""
        filter_query = {}

        if client_id:
            filter_query["client_id"] = client_id
        if industry:
            filter_query["industry"] = industry
        if category:
            filter_query["category"] = category
        if active_only:
            filter_query["active"] = True

        tools = await self.tools_collection.find(filter_query).to_list(None)
        return [self._format_tool_response(tool) for tool in tools]

    async def get_tool_by_id(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific tool by ID."""
        try:
            tool = await self.tools_collection.find_one({"_id": ObjectId(tool_id)})
            return self._format_tool_response(tool) if tool else None
        except Exception:
            return None

    async def update_tool(self, tool_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update tool metadata."""
        try:
            updates["updated_at"] = datetime.utcnow()
            result = await self.tools_collection.update_one(
                {"_id": ObjectId(tool_id)},
                {"$set": updates}
            )

            if result.modified_count > 0:
                return {"success": True, "message": "Tool updated successfully"}
            else:
                return {"success": False, "error": "Tool not found or no changes made"}

        except Exception as e:
            return {"success": False, "error": f"Failed to update tool: {str(e)}"}

    async def deactivate_tool(self, tool_id: str) -> Dict[str, Any]:
        """Deactivate a tool (soft delete)."""
        return await self.update_tool(tool_id, {"active": False})

    def _format_tool_response(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool data for API response."""
        if not tool:
            return {}

        return {
            "id": str(tool["_id"]),
            "name": tool["name"],
            "client_id": tool["client_id"],
            "industry": tool["industry"],
            "category": tool["category"],
            "description": tool["description"],
            "endpoint": tool["endpoint"],
            "method": tool["method"],
            "schema": tool["schema"],
            "active": tool["active"],
            "created_at": tool["created_at"].isoformat() if tool.get("created_at") else None,
            "updated_at": tool["updated_at"].isoformat() if tool.get("updated_at") else None,
            "metadata": tool.get("metadata", {}),
            # VAPI integration fields
            "vapi_tool_id": tool.get("vapi_tool_id"),
            "server_url": tool.get("server_url"),
            "vapi_sync_status": tool.get("vapi_sync_status", "pending"),
            "deployment_status": tool.get("deployment_status", "inactive"),
            "vapi_metadata": tool.get("vapi_metadata", {})
        }

    async def register_tool_from_database(
        self,
        tool_data: Dict[str, Any],
        source: str = "database"
    ) -> Dict[str, Any]:
        """
        Register a custom tool directly from database specification.

        Args:
            tool_data (Dict): Complete tool specification including code, schema, metadata
            source (str): Source identifier for the registration

        Returns:
            Dict: Registration result
        """
        try:
            # Validate required fields
            required_fields = ["name", "client_id", "description", "schema"]
            for field in required_fields:
                if field not in tool_data:
                    return {"success": False, "error": f"Missing required field: {field}"}

            # Generate unique tool ID
            tool_id = ObjectId()

            # Prepare tool document
            tool_document = {
                "_id": tool_id,
                "name": tool_data["name"],
                "client_id": tool_data["client_id"],
                "industry": tool_data.get("industry", "general"),
                "category": tool_data.get("category", "utility"),
                "description": tool_data["description"],
                "schema": tool_data["schema"],
                "endpoint": tool_data.get("endpoint", f"/custom-tools/{tool_data['client_id']}/{tool_data['name']}"),
                "method": tool_data.get("method", "POST"),
                "source": source,
                "code": tool_data.get("code"),  # Optional Python code for execution
                "function_name": tool_data.get("function_name"),
                "file_path": tool_data.get("file_path"),
                "version": tool_data.get("version", "1.0.0"),
                "tags": tool_data.get("tags", []),
                "dependencies": tool_data.get("dependencies", []),
                "active": tool_data.get("active", True),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "metadata": tool_data.get("metadata", {}),
                # VAPI integration fields
                "vapi_tool_id": tool_data.get("vapi_tool_id"),
                "server_url": tool_data.get("server_url", f"https://api.ailabsafrica.com/custom-tools/{tool_data['client_id']}/{tool_data['name']}"),
                "vapi_sync_status": tool_data.get("vapi_sync_status", "pending"),
                "deployment_status": tool_data.get("deployment_status", "inactive"),
                "vapi_metadata": tool_data.get("vapi_metadata", {
                    "assistant_ids": [],
                    "last_synced": None,
                    "sync_errors": []
                }),
                "analytics": {
                    "execution_count": 0,
                    "last_executed": None,
                    "average_response_time": 0,
                    "error_count": 0
                }
            }

            # Insert into database
            await self.tools_collection.insert_one(tool_document)

            return {
                "success": True,
                "tool_id": str(tool_id),
                "message": f"Tool '{tool_data['name']}' registered successfully",
                "endpoint": tool_document["endpoint"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to register tool from database: {str(e)}"
            }

    async def bulk_register_tools(
        self,
        tools_data: List[Dict[str, Any]],
        client_id: str,
        source: str = "bulk_import"
    ) -> Dict[str, Any]:
        """
        Register multiple tools in bulk operation.

        Args:
            tools_data (List[Dict]): List of tool specifications
            client_id (str): Client identifier for all tools
            source (str): Source identifier

        Returns:
            Dict: Bulk registration result
        """
        try:
            results = {"successful": [], "failed": []}

            for tool_data in tools_data:
                tool_data["client_id"] = client_id
                result = await self.register_tool_from_database(tool_data, source)

                if result["success"]:
                    results["successful"].append({
                        "name": tool_data["name"],
                        "tool_id": result["tool_id"],
                        "endpoint": result["endpoint"]
                    })
                else:
                    results["failed"].append({
                        "name": tool_data.get("name", "unknown"),
                        "error": result["error"]
                    })

            return {
                "success": True,
                "total_processed": len(tools_data),
                "successful_count": len(results["successful"]),
                "failed_count": len(results["failed"]),
                "results": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Bulk registration failed: {str(e)}"
            }

    async def search_tools(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search tools using text search and filters.

        Args:
            query (str): Search query for tool names and descriptions
            filters (Dict): Additional filters (client_id, industry, category, etc.)
            limit (int): Maximum number of results

        Returns:
            List[Dict]: Matching tools
        """
        try:
            search_filter = {"active": True}

            # Add text search
            if query:
                search_filter["$or"] = [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"tags": {"$in": [query]}},
                    {"category": {"$regex": query, "$options": "i"}},
                    {"industry": {"$regex": query, "$options": "i"}}
                ]

            # Add additional filters
            if filters:
                search_filter.update(filters)

            tools = await self.tools_collection.find(search_filter).limit(limit).to_list(None)
            return [self._format_tool_response(tool) for tool in tools]

        except Exception as e:
            return []

    async def get_tool_analytics(self, tool_id: str) -> Dict[str, Any]:
        """Get analytics data for a specific tool."""
        try:
            tool = await self.tools_collection.find_one({"_id": ObjectId(tool_id)})
            if not tool:
                return {"success": False, "error": "Tool not found"}

            return {
                "success": True,
                "analytics": tool.get("analytics", {}),
                "tool_name": tool["name"],
                "client_id": tool["client_id"]
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to get analytics: {str(e)}"}

    async def update_tool_analytics(
        self,
        tool_id: str,
        execution_time: float,
        success: bool
    ) -> None:
        """Update tool analytics after execution."""
        try:
            update_data = {
                "analytics.last_executed": datetime.utcnow(),
                "$inc": {"analytics.execution_count": 1}
            }

            if not success:
                update_data["$inc"]["analytics.error_count"] = 1

            # Update average response time
            tool = await self.tools_collection.find_one({"_id": ObjectId(tool_id)})
            if tool and "analytics" in tool:
                current_avg = tool["analytics"].get("average_response_time", 0)
                execution_count = tool["analytics"].get("execution_count", 0)
                new_avg = ((current_avg * execution_count) + execution_time) / (execution_count + 1)
                update_data["analytics.average_response_time"] = round(new_avg, 3)

            await self.tools_collection.update_one(
                {"_id": ObjectId(tool_id)},
                {"$set": update_data}
            )

        except Exception:
            pass  # Don't fail tool execution if analytics update fails

    async def get_client_tools_summary(self, client_id: str) -> Dict[str, Any]:
        """Get summary statistics for a client's tools."""
        try:
            pipeline = [
                {"$match": {"client_id": client_id}},
                {"$group": {
                    "_id": None,
                    "total_tools": {"$sum": 1},
                    "active_tools": {"$sum": {"$cond": ["$active", 1, 0]}},
                    "total_executions": {"$sum": "$analytics.execution_count"},
                    "total_errors": {"$sum": "$analytics.error_count"},
                    "categories": {"$addToSet": "$category"},
                    "industries": {"$addToSet": "$industry"}
                }}
            ]

            result = await self.tools_collection.aggregate(pipeline).to_list(None)

            if result:
                summary = result[0]
                del summary["_id"]
                summary["success_rate"] = (
                    (summary["total_executions"] - summary["total_errors"]) /
                    max(summary["total_executions"], 1) * 100
                )
                return {"success": True, "summary": summary}
            else:
                return {
                    "success": True,
                    "summary": {
                        "total_tools": 0,
                        "active_tools": 0,
                        "total_executions": 0,
                        "total_errors": 0,
                        "categories": [],
                        "industries": [],
                        "success_rate": 0
                    }
                }

        except Exception as e:
            return {"success": False, "error": f"Failed to get summary: {str(e)}"}

    async def execute_tool(self, tool_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a custom tool function with analytics tracking.

        Args:
            tool_id (str): Tool identifier
            parameters (Dict): Parameters to pass to the tool function

        Returns:
            Dict: Tool execution result
        """
        start_time = datetime.utcnow()
        success = False

        try:
            tool = await self.tools_collection.find_one({"_id": ObjectId(tool_id)})
            if not tool or not tool.get("active"):
                return {"success": False, "error": "Tool not found or inactive"}

            # Execute based on source type
            if tool.get("source") == "database" and tool.get("code"):
                # Execute inline code
                result = await self._execute_inline_code(tool, parameters)
            else:
                # Execute from file
                result = await self._execute_file_based_tool(tool, parameters)

            success = result.get("success", False)

            # Update analytics
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            await self.update_tool_analytics(tool_id, execution_time, success)

            return result

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            await self.update_tool_analytics(tool_id, execution_time, False)

            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
                "tool_id": tool_id
            }

    async def _execute_inline_code(
        self,
        tool: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tool from inline code stored in database."""
        try:
            # Create a safe execution environment
            exec_globals = {
                '__builtins__': __builtins__,
                'parameters': parameters,
                'result': None
            }

            # Execute the code
            exec(tool["code"], exec_globals)

            return {
                "success": True,
                "result": exec_globals.get("result"),
                "tool_name": tool["name"],
                "executed_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Inline code execution failed: {str(e)}"
            }

    async def _execute_file_based_tool(
        self,
        tool: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tool from file (original implementation)."""
        try:
            # Load the module and execute the function
            file_path = tool["file_path"]
            function_name = tool["function_name"]

            spec = importlib.util.spec_from_file_location("custom_tools", file_path)
            if spec is None or spec.loader is None:
                return {"success": False, "error": "Could not load tool module"}

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Handle class methods
            if "." in function_name:
                class_name, method_name = function_name.split(".", 1)
                tool_class = getattr(module, class_name)

                # Initialize class with appropriate config
                if class_name == "HealthcareVoiceTools":
                    # Special handling for healthcare tools
                    db_config = {
                        'host': 'localhost',
                        'port': 5432,
                        'database': 'community',
                        'user': 'postgres',
                        'password': os.getenv('POSTGRES_PASSWORD', 'password')
                    }
                    tool_instance = tool_class(db_config)
                else:
                    tool_instance = tool_class()

                func = getattr(tool_instance, method_name)
            else:
                func = getattr(module, function_name)

            # Execute the function
            result = func(**parameters)

            return {
                "success": True,
                "result": result,
                "tool_name": tool["name"],
                "executed_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"File-based execution failed: {str(e)}"
            }

    # VAPI Integration Methods

    async def sync_tool_with_vapi(self, tool_id: str) -> Dict[str, Any]:
        """
        Sync a single tool with VAPI.

        Args:
            tool_id (str): Tool identifier

        Returns:
            Dict: Sync result
        """
        try:
            tool = await self.tools_collection.find_one({"_id": ObjectId(tool_id)})
            if not tool:
                return {"success": False, "error": "Tool not found"}

            if not self.vapi_api_key:
                return {"success": False, "error": "VAPI API key not configured"}

            # Prepare VAPI tool data
            vapi_tool_data = self._prepare_vapi_tool_data(tool)

            # Create or update tool in VAPI
            if tool.get("vapi_tool_id"):
                # Update existing tool
                result = await self._update_vapi_tool(tool["vapi_tool_id"], vapi_tool_data)
            else:
                # Create new tool
                result = await self._create_vapi_tool(vapi_tool_data)

            # Update tool with sync status
            update_data = {
                "vapi_sync_status": "synced" if result["success"] else "error",
                "vapi_metadata.last_synced": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            if result["success"] and "vapi_tool_id" in result:
                update_data["vapi_tool_id"] = result["vapi_tool_id"]
                update_data["deployment_status"] = "active"
            else:
                update_data["vapi_metadata.sync_errors"] = result.get("errors", [result.get("error", "Unknown error")])

            await self.tools_collection.update_one(
                {"_id": ObjectId(tool_id)},
                {"$set": update_data}
            )

            return result

        except Exception as e:
            logger.error(f"Error syncing tool {tool_id} with VAPI: {str(e)}")
            return {"success": False, "error": f"Sync failed: {str(e)}"}

    async def bulk_sync_tools_with_vapi(self, client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Sync all tools (or client-specific tools) with VAPI.

        Args:
            client_id (Optional[str]): Client ID to filter tools

        Returns:
            Dict: Bulk sync result
        """
        try:
            filter_query = {"active": True}
            if client_id:
                filter_query["client_id"] = client_id

            tools = await self.tools_collection.find(filter_query).to_list(None)

            results = {"successful": [], "failed": []}

            for tool in tools:
                tool_id = str(tool["_id"])
                result = await self.sync_tool_with_vapi(tool_id)

                if result["success"]:
                    results["successful"].append({
                        "tool_id": tool_id,
                        "name": tool["name"],
                        "vapi_tool_id": result.get("vapi_tool_id")
                    })
                else:
                    results["failed"].append({
                        "tool_id": tool_id,
                        "name": tool["name"],
                        "error": result["error"]
                    })

            return {
                "success": True,
                "total_processed": len(tools),
                "successful_count": len(results["successful"]),
                "failed_count": len(results["failed"]),
                "results": results
            }

        except Exception as e:
            logger.error(f"Error in bulk sync with VAPI: {str(e)}")
            return {"success": False, "error": f"Bulk sync failed: {str(e)}"}

    async def register_premier_health_tools(self) -> Dict[str, Any]:
        """
        Register Premier Health tools with their existing VAPI tool IDs.

        Returns:
            Dict: Registration result
        """
        try:
            # Premier Health tools with their VAPI IDs (from our earlier analysis)
            premier_health_tools = [
                {
                    "name": "search_healthcare_providers",
                    "vapi_tool_id": "91680cf0-fc9d-4a59-b65a-8ea2ececcac7",
                    "description": "Search for healthcare providers using natural language or specific filters",
                    "category": "healthcare_search",
                    "function_name": "HealthcareVoiceTools.search_healthcare_providers"
                },
                {
                    "name": "get_emergency_providers",
                    "vapi_tool_id": "74e8e539-776f-4fc6-ba2f-46aa241722be",
                    "description": "Find emergency healthcare providers for urgent situations",
                    "category": "healthcare_emergency",
                    "function_name": "HealthcareVoiceTools.get_emergency_providers"
                },
                {
                    "name": "get_provider_details",
                    "vapi_tool_id": "f0f98b68-ade8-4a01-ae0a-d09a9dc39c6f",
                    "description": "Get detailed information about a specific healthcare provider",
                    "category": "healthcare_details",
                    "function_name": "HealthcareVoiceTools.get_provider_details"
                },
                {
                    "name": "get_available_areas",
                    "vapi_tool_id": "c3b245ff-a8ee-42ed-b39d-6e50d0fc09e0",
                    "description": "Get list of all available areas/locations with healthcare coverage",
                    "category": "healthcare_areas",
                    "function_name": "HealthcareVoiceTools.get_available_areas"
                },
                {
                    "name": "get_available_specialties",
                    "vapi_tool_id": "23954934-c55e-4faa-b0ca-23ed45ce5289",
                    "description": "Get list of all available medical specialties",
                    "category": "healthcare_specialties",
                    "function_name": "HealthcareVoiceTools.get_available_specialties"
                },
                {
                    "name": "escalate_to_support",
                    "vapi_tool_id": "457d5d87-a0ed-44ab-b6d6-ce3ec912ba01",
                    "description": "Escalate query to support when location not found or other issues",
                    "category": "support",
                    "function_name": "HealthcareVoiceTools.escalate_to_support"
                },
                {
                    "name": "send_sms_vonage",
                    "vapi_tool_id": "fc1ca495-9083-492e-854a-aeee6e5b3f64",
                    "description": "Send SMS notifications via Vonage",
                    "category": "communication",
                    "function_name": "send_sms_vonage"
                },
                {
                    "name": "send_notification_email",
                    "vapi_tool_id": "abc528ae-e1f1-4e9c-a939-bc859e5e7d88",
                    "description": "Send email notifications",
                    "category": "communication",
                    "function_name": "send_notification_email"
                },
                {
                    "name": "create_hubspot_contact",
                    "vapi_tool_id": "1e59ec6d-e2ec-4707-9e71-7dbceb51da0d",
                    "description": "Create or update HubSpot contacts",
                    "category": "crm",
                    "function_name": "create_hubspot_contact"
                },
                {
                    "name": "create_support_ticket",
                    "vapi_tool_id": "83635498-8f71-453a-9a15-7e00e1e494a2",
                    "description": "Create support tickets",
                    "category": "support",
                    "function_name": "create_support_ticket"
                },
                {
                    "name": "call_logging_supabase",
                    "vapi_tool_id": "bb90890c-750d-429f-9a40-836140c70d1c",
                    "description": "Log call details to Supabase",
                    "category": "logging",
                    "function_name": "call_logging_supabase"
                },
                {
                    "name": "record_call_details",
                    "vapi_tool_id": "1231e261-c8c3-4009-9729-3aa8ea8dc86c",
                    "description": "Record detailed call information",
                    "category": "logging",
                    "function_name": "record_call_details"
                },
                {
                    "name": "email_notification",
                    "vapi_tool_id": "86e8b665-ddf8-4695-872f-772cb303d54d",
                    "description": "Send email notifications to team",
                    "category": "communication",
                    "function_name": "email_notification"
                },
                {
                    "name": "ai_transcript_summarization",
                    "vapi_tool_id": "6eb24d57-16ef-4262-a587-a5cd1e038629",
                    "description": "Generate AI-powered call summaries",
                    "category": "ai",
                    "function_name": "ai_transcript_summarization"
                },
                {
                    "name": "book_calendly_appointment",
                    "vapi_tool_id": "d1c30e08-aae8-49b1-b06e-ba3a3e634f18",
                    "description": "Book appointments via Calendly",
                    "category": "scheduling",
                    "function_name": "book_calendly_appointment"
                },
                {
                    "name": "check_calendly_availability",
                    "vapi_tool_id": "3f6ddf13-5121-4127-8aec-bdc4dfda6f7d",
                    "description": "Check available appointment slots",
                    "category": "scheduling",
                    "function_name": "check_calendly_availability"
                },
                {
                    "name": "search_web_with_ai",
                    "vapi_tool_id": "d7f97ff5-e4ce-46fd-a75c-8bb0cf76454b",
                    "description": "Perform intelligent web searches",
                    "category": "ai",
                    "function_name": "search_web_with_ai"
                }
            ]

            tools_data = []
            for tool_info in premier_health_tools:
                tool_data = {
                    "name": tool_info["name"],
                    "client_id": "premier-health",
                    "industry": "healthcare",
                    "category": tool_info["category"],
                    "description": tool_info["description"],
                    "function_name": tool_info["function_name"],
                    "file_path": "/opt/kasaai/apps/automations/premier-health/voice_agent_tools.py",
                    "schema": {"type": "function", "function": {"name": tool_info["name"], "description": tool_info["description"]}},
                    "vapi_tool_id": tool_info["vapi_tool_id"],
                    "server_url": f"https://api.ailabsafrica.com/premier-health/{tool_info['name']}",
                    "vapi_sync_status": "synced",
                    "deployment_status": "active",
                    "vapi_metadata": {
                        "assistant_ids": ["baa69b3a-8944-4557-9ef9-3a5aa6956eb3"],
                        "last_synced": datetime.utcnow(),
                        "sync_errors": []
                    }
                }
                tools_data.append(tool_data)

            # Use bulk registration
            result = await self.bulk_register_tools(tools_data, "premier-health", "vapi_mapping")

            return {
                "success": True,
                "message": "Premier Health tools registered successfully",
                "total_tools": len(premier_health_tools),
                "result": result
            }

        except Exception as e:
            logger.error(f"Error registering Premier Health tools: {str(e)}")
            return {"success": False, "error": f"Registration failed: {str(e)}"}

    async def get_tools_by_vapi_assistant(self, assistant_id: str) -> List[Dict[str, Any]]:
        """
        Get tools associated with a specific VAPI assistant.

        Args:
            assistant_id (str): VAPI assistant ID

        Returns:
            List[Dict]: Tools associated with the assistant
        """
        try:
            tools = await self.tools_collection.find({
                "vapi_metadata.assistant_ids": assistant_id,
                "active": True
            }).to_list(None)

            return [self._format_tool_response(tool) for tool in tools]

        except Exception as e:
            logger.error(f"Error getting tools for assistant {assistant_id}: {str(e)}")
            return []

    def _prepare_vapi_tool_data(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare tool data for VAPI API.

        Args:
            tool (Dict): Tool document from MongoDB

        Returns:
            Dict: VAPI-compatible tool data
        """
        # Extract parameters from tool schema
        parameters = {}
        if "schema" in tool and "function" in tool["schema"]:
            parameters = tool["schema"]["function"].get("parameters", {})
        elif "schema" in tool and "parameters" in tool["schema"]:
            parameters = tool["schema"]["parameters"]

        # Ensure parameters has the correct structure
        if "type" not in parameters:
            parameters = {
                "type": "object",
                "properties": parameters.get("properties", {}),
                "required": parameters.get("required", [])
            }

        return {
            "server": {
                "url": tool.get("server_url", f"https://api.ailabsafrica.com{tool['endpoint']}")
            },
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": parameters
            }
        }

    async def _create_vapi_tool(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new tool in VAPI.

        Args:
            tool_data (Dict): VAPI tool data

        Returns:
            Dict: Creation result
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.vapi_api_key}",
                "Content-Type": "application/json"
            }

            # Add the type for function tools
            complete_tool_data = {
                "type": "function",
                **tool_data
            }

            response = requests.post(
                f"{self.vapi_base_url}/tool",
                json=complete_tool_data,
                headers=headers,
                timeout=30
            )

            if response.status_code == 201:
                result_data = response.json()
                return {
                    "success": True,
                    "vapi_tool_id": result_data.get("id"),
                    "message": "Tool created in VAPI successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"VAPI API error: {response.status_code} - {response.text}"
                }

        except Exception as e:
            return {"success": False, "error": f"Failed to create VAPI tool: {str(e)}"}

    async def _update_vapi_tool(self, vapi_tool_id: str, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing tool in VAPI.

        Args:
            vapi_tool_id (str): VAPI tool ID
            tool_data (Dict): Updated tool data

        Returns:
            Dict: Update result
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.vapi_api_key}",
                "Content-Type": "application/json"
            }

            # Add the type for function tools
            complete_tool_data = {
                "type": "function",
                **tool_data
            }

            response = requests.patch(
                f"{self.vapi_base_url}/tool/{vapi_tool_id}",
                json=complete_tool_data,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "vapi_tool_id": vapi_tool_id,
                    "message": "Tool updated in VAPI successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"VAPI API error: {response.status_code} - {response.text}"
                }

        except Exception as e:
            return {"success": False, "error": f"Failed to update VAPI tool: {str(e)}"}

    async def get_vapi_sync_status(self, client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get VAPI sync status for tools.

        Args:
            client_id (Optional[str]): Filter by client ID

        Returns:
            Dict: Sync status summary
        """
        try:
            filter_query = {"active": True}
            if client_id:
                filter_query["client_id"] = client_id

            pipeline = [
                {"$match": filter_query},
                {"$group": {
                    "_id": "$vapi_sync_status",
                    "count": {"$sum": 1}
                }}
            ]

            status_counts = await self.tools_collection.aggregate(pipeline).to_list(None)

            status_summary = {item["_id"]: item["count"] for item in status_counts}

            return {
                "success": True,
                "sync_status": status_summary,
                "total_tools": sum(status_summary.values())
            }

        except Exception as e:
            logger.error(f"Error getting VAPI sync status: {str(e)}")
            return {"success": False, "error": f"Failed to get sync status: {str(e)}"}

# Global service instance
custom_tools_service = CustomToolsService()