#!/usr/bin/env python3
"""
Supabase MCP Server
Provides MCP interface for Supabase operations including database, auth, storage, and edge functions.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
)

from .supabase import SupabaseIntegration, SupabaseConfig

logger = logging.getLogger(__name__)

class SupabaseMCPServer:
    """MCP Server for Supabase operations."""

    def __init__(self):
        self.server = Server("supabase-mcp")
        self.supabase: Optional[SupabaseIntegration] = None
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP server handlers."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available Supabase tools."""
            return [
                Tool(
                    name="supabase_health_check",
                    description="Check Supabase connection health and status",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="supabase_insert",
                    description="Insert data into a Supabase table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table": {"type": "string", "description": "Table name"},
                            "data": {"type": "object", "description": "Data to insert"},
                            "upsert": {"type": "boolean", "description": "Whether to upsert", "default": False}
                        },
                        "required": ["table", "data"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="supabase_select",
                    description="Select data from a Supabase table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table": {"type": "string", "description": "Table name"},
                            "columns": {"type": "string", "description": "Columns to select", "default": "*"},
                            "filters": {"type": "object", "description": "Filter conditions"},
                            "order_by": {"type": "string", "description": "Order by column"},
                            "limit": {"type": "integer", "description": "Limit results"},
                            "offset": {"type": "integer", "description": "Offset for pagination"}
                        },
                        "required": ["table"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="supabase_update",
                    description="Update data in a Supabase table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table": {"type": "string", "description": "Table name"},
                            "data": {"type": "object", "description": "Data to update"},
                            "filters": {"type": "object", "description": "Filter conditions"}
                        },
                        "required": ["table", "data", "filters"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="supabase_delete",
                    description="Delete data from a Supabase table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table": {"type": "string", "description": "Table name"},
                            "filters": {"type": "object", "description": "Filter conditions"}
                        },
                        "required": ["table", "filters"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="supabase_execute_sql",
                    description="Execute raw SQL query (requires service role)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "SQL query to execute"}
                        },
                        "required": ["query"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="supabase_create_table",
                    description="Create a new table (requires service role)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {"type": "string", "description": "Name of the table to create"},
                            "columns": {"type": "array", "description": "Array of column definitions"},
                            "primary_key": {"type": "string", "description": "Primary key column", "default": "id"}
                        },
                        "required": ["table_name", "columns"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="supabase_list_tables",
                    description="List all tables in the database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "schema": {"type": "string", "description": "Database schema", "default": "public"}
                        },
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="supabase_auth_sign_up",
                    description="Sign up a new user",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "email": {"type": "string", "description": "User email"},
                            "password": {"type": "string", "description": "User password"},
                            "user_metadata": {"type": "object", "description": "Additional user metadata"}
                        },
                        "required": ["email", "password"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="supabase_auth_sign_in",
                    description="Sign in a user",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "email": {"type": "string", "description": "User email"},
                            "password": {"type": "string", "description": "User password"}
                        },
                        "required": ["email", "password"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="supabase_storage_upload",
                    description="Upload file to Supabase storage",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "bucket": {"type": "string", "description": "Storage bucket name"},
                            "path": {"type": "string", "description": "File path in bucket"},
                            "file_data": {"type": "string", "description": "Base64 encoded file data"},
                            "content_type": {"type": "string", "description": "File content type"}
                        },
                        "required": ["bucket", "path", "file_data"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="supabase_storage_list",
                    description="List files in storage bucket",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "bucket": {"type": "string", "description": "Storage bucket name"},
                            "path": {"type": "string", "description": "Path prefix", "default": ""},
                            "limit": {"type": "integer", "description": "Maximum files", "default": 100}
                        },
                        "required": ["bucket"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="supabase_invoke_function",
                    description="Invoke a Supabase edge function",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "function_name": {"type": "string", "description": "Function name"},
                            "payload": {"type": "object", "description": "Function payload"},
                            "headers": {"type": "object", "description": "Additional headers"}
                        },
                        "required": ["function_name"],
                        "additionalProperties": False
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls."""

            if not self.supabase:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="Error: Supabase not initialized. Please check configuration."
                    )]
                )

            try:
                if request.name == "supabase_health_check":
                    result = await self.supabase.health_check()
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    )

                elif request.name == "supabase_insert":
                    args = request.arguments or {}
                    result = await self.supabase.insert(
                        table=args["table"],
                        data=args["data"],
                        upsert=args.get("upsert", False)
                    )
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=json.dumps({
                                "success": not bool(result.error),
                                "data": result.data,
                                "count": result.count,
                                "error": result.error
                            }, indent=2)
                        )]
                    )

                elif request.name == "supabase_select":
                    args = request.arguments or {}
                    result = await self.supabase.select(
                        table=args["table"],
                        columns=args.get("columns", "*"),
                        filters=args.get("filters"),
                        order_by=args.get("order_by"),
                        limit=args.get("limit"),
                        offset=args.get("offset")
                    )
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=json.dumps({
                                "success": not bool(result.error),
                                "data": result.data,
                                "count": result.count,
                                "error": result.error
                            }, indent=2)
                        )]
                    )

                elif request.name == "supabase_update":
                    args = request.arguments or {}
                    result = await self.supabase.update(
                        table=args["table"],
                        data=args["data"],
                        filters=args["filters"]
                    )
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=json.dumps({
                                "success": not bool(result.error),
                                "data": result.data,
                                "count": result.count,
                                "error": result.error
                            }, indent=2)
                        )]
                    )

                elif request.name == "supabase_delete":
                    args = request.arguments or {}
                    result = await self.supabase.delete(
                        table=args["table"],
                        filters=args["filters"]
                    )
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=json.dumps({
                                "success": not bool(result.error),
                                "data": result.data,
                                "count": result.count,
                                "error": result.error
                            }, indent=2)
                        )]
                    )

                elif request.name == "supabase_execute_sql":
                    if not self.supabase.admin_client:
                        return CallToolResult(
                            content=[TextContent(
                                type="text",
                                text=json.dumps({
                                    "success": False,
                                    "error": "Service role key required for SQL execution"
                                }, indent=2)
                            )]
                        )

                    args = request.arguments or {}
                    # Use admin client for direct SQL execution
                    try:
                        response = self.supabase.admin_client.rpc('exec_sql', {
                            'sql': args["query"]
                        }).execute()

                        return CallToolResult(
                            content=[TextContent(
                                type="text",
                                text=json.dumps({
                                    "success": True,
                                    "result": response.data
                                }, indent=2)
                            )]
                        )
                    except Exception as e:
                        return CallToolResult(
                            content=[TextContent(
                                type="text",
                                text=json.dumps({
                                    "success": False,
                                    "error": str(e)
                                }, indent=2)
                            )]
                        )

                elif request.name == "supabase_create_table":
                    if not self.supabase.admin_client:
                        return CallToolResult(
                            content=[TextContent(
                                type="text",
                                text=json.dumps({
                                    "success": False,
                                    "error": "Service role key required for table creation"
                                }, indent=2)
                            )]
                        )

                    args = request.arguments or {}
                    table_name = args["table_name"]
                    columns = args["columns"]
                    primary_key = args.get("primary_key", "id")

                    # Build CREATE TABLE SQL
                    column_defs = []
                    for col in columns:
                        if isinstance(col, str):
                            column_defs.append(col)
                        elif isinstance(col, dict):
                            name = col.get("name")
                            col_type = col.get("type", "TEXT")
                            constraints = col.get("constraints", "")
                            column_defs.append(f"{name} {col_type} {constraints}".strip())

                    if primary_key and primary_key not in [col.split()[0] for col in column_defs]:
                        column_defs.insert(0, f"{primary_key} UUID DEFAULT gen_random_uuid() PRIMARY KEY")

                    create_sql = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        {', '.join(column_defs)}
                    );
                    """

                    try:
                        response = self.supabase.admin_client.rpc('exec_sql', {
                            'sql': create_sql
                        }).execute()

                        return CallToolResult(
                            content=[TextContent(
                                type="text",
                                text=json.dumps({
                                    "success": True,
                                    "table_name": table_name,
                                    "sql": create_sql.strip(),
                                    "result": response.data
                                }, indent=2)
                            )]
                        )
                    except Exception as e:
                        return CallToolResult(
                            content=[TextContent(
                                type="text",
                                text=json.dumps({
                                    "success": False,
                                    "error": str(e),
                                    "sql": create_sql.strip()
                                }, indent=2)
                            )]
                        )

                elif request.name == "supabase_list_tables":
                    args = request.arguments or {}
                    schema = args.get("schema", "public")

                    # Query to list tables
                    list_sql = f"""
                    SELECT table_name, table_type
                    FROM information_schema.tables
                    WHERE table_schema = '{schema}'
                    ORDER BY table_name;
                    """

                    try:
                        response = await self.supabase.select(
                            table="information_schema.tables",
                            columns="table_name,table_type",
                            filters={"table_schema": schema}
                        )

                        return CallToolResult(
                            content=[TextContent(
                                type="text",
                                text=json.dumps({
                                    "success": not bool(response.error),
                                    "schema": schema,
                                    "tables": response.data,
                                    "count": response.count,
                                    "error": response.error
                                }, indent=2)
                            )]
                        )
                    except Exception as e:
                        return CallToolResult(
                            content=[TextContent(
                                type="text",
                                text=json.dumps({
                                    "success": False,
                                    "error": str(e)
                                }, indent=2)
                            )]
                        )

                elif request.name == "supabase_auth_sign_up":
                    args = request.arguments or {}
                    result = await self.supabase.sign_up(
                        email=args["email"],
                        password=args["password"],
                        user_metadata=args.get("user_metadata")
                    )

                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=json.dumps({
                                "success": not bool(result.error),
                                "user": result.user.__dict__ if result.user else None,
                                "session": result.session,
                                "error": result.error
                            }, indent=2, default=str)
                        )]
                    )

                elif request.name == "supabase_auth_sign_in":
                    args = request.arguments or {}
                    result = await self.supabase.sign_in(
                        email=args["email"],
                        password=args["password"]
                    )

                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=json.dumps({
                                "success": not bool(result.error),
                                "user": result.user.__dict__ if result.user else None,
                                "session": result.session,
                                "error": result.error
                            }, indent=2, default=str)
                        )]
                    )

                elif request.name == "supabase_storage_upload":
                    import base64
                    args = request.arguments or {}

                    # Decode base64 file data
                    file_data = base64.b64decode(args["file_data"])

                    result = await self.supabase.upload_file(
                        bucket=args["bucket"],
                        path=args["path"],
                        file_data=file_data,
                        content_type=args.get("content_type")
                    )

                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=json.dumps({
                                "success": not bool(result.error),
                                "path": result.path,
                                "id": result.id,
                                "fullPath": result.fullPath,
                                "error": result.error
                            }, indent=2)
                        )]
                    )

                elif request.name == "supabase_storage_list":
                    args = request.arguments or {}
                    result = await self.supabase.list_files(
                        bucket=args["bucket"],
                        path=args.get("path", ""),
                        limit=args.get("limit", 100)
                    )

                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=json.dumps({
                                "success": True,
                                "files": result,
                                "count": len(result)
                            }, indent=2)
                        )]
                    )

                elif request.name == "supabase_invoke_function":
                    args = request.arguments or {}
                    result = await self.supabase.invoke_function(
                        function_name=args["function_name"],
                        payload=args.get("payload"),
                        headers=args.get("headers")
                    )

                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=json.dumps({
                                "success": "error" not in result,
                                "result": result
                            }, indent=2)
                        )]
                    )

                else:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"Unknown tool: {request.name}"
                        )]
                    )

            except Exception as e:
                logger.error(f"Error in tool call {request.name}: {e}")
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": str(e)
                        }, indent=2)
                    )]
                )

    async def initialize(self, options: InitializationOptions):
        """Initialize the Supabase connection."""
        # Get configuration from environment variables
        url = os.getenv("DEMO_SUPABASE_URL")
        anon_key = os.getenv("DEMO_SUPABASE_ANON_KEY")
        service_role_key = os.getenv("DEMO_SUPABASE_SUPABASE_KEY")

        if not url or not anon_key:
            logger.error("Missing required Supabase environment variables")
            return

        config = SupabaseConfig(
            url=url,
            anon_key=anon_key,
            service_role_key=service_role_key
        )

        self.supabase = SupabaseIntegration(config)
        logger.info("Supabase MCP server initialized")

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="supabase-mcp",
                    server_version="1.0.0",
                    capabilities={}
                )
            )

async def main():
    """Main entry point for the MCP server."""
    server = SupabaseMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())