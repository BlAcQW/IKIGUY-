"""
Comprehensive tests for Custom Tools Service
Tests all functionality including registration, execution, VAPI sync, and analytics
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from bson import ObjectId

from backend.services.custom_tools_service import CustomToolsService


class TestCustomToolsService:
    """Test suite for CustomToolsService functionality."""

    @pytest.fixture
    def service(self):
        """Create a CustomToolsService instance for testing."""
        service = CustomToolsService()
        return service

    @pytest.fixture
    def sample_tool_data(self):
        """Sample tool data for testing."""
        return {
            "name": "test_search_tool",
            "client_id": "test-client",
            "industry": "healthcare",
            "category": "search",
            "description": "Test search tool for healthcare providers",
            "schema": {
                "type": "function",
                "function": {
                    "name": "test_search_tool",
                    "description": "Test search tool for healthcare providers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "location": {
                                "type": "string",
                                "description": "Location filter"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            "metadata": {
                "version": "1.0.0",
                "author": "test"
            }
        }

    @pytest.fixture
    def sample_tool_file_content(self):
        """Sample Python file content for tool registration."""
        return '''
"""Test tool functions for healthcare"""

class TestHealthcareTools:
    def __init__(self):
        pass

    def search_providers(self, query: str, location: str = None):
        """Search for healthcare providers."""
        return {
            "providers": [
                {"name": "Test Hospital", "location": "Test City"}
            ],
            "total": 1
        }

    def get_specialties(self):
        """Get available medical specialties."""
        return {
            "specialties": ["Cardiology", "Pediatrics"],
            "total": 2
        }

# Tool schemas for registration
TOOL_SCHEMAS = {
    "search_providers": {
        "type": "function",
        "function": {
            "name": "search_providers",
            "description": "Search for healthcare providers",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "location": {"type": "string", "description": "Location filter"}
                },
                "required": ["query"]
            }
        }
    }
}
'''

    @pytest.mark.asyncio

    async def test_tool_registration_from_database(self, service, sample_tool_data):
        """Test registering a tool directly from database specification."""
        with patch.object(service.tools_collection, 'insert_one') as mock_insert:
            mock_insert.return_value = AsyncMock()

            result = await service.register_tool_from_database(sample_tool_data)

            assert result["success"] is True
            assert "tool_id" in result
            assert result["message"] == "Tool 'test_search_tool' registered successfully"
            mock_insert.assert_called_once()

    @pytest.mark.asyncio

    async def test_tool_registration_missing_fields(self, service):
        """Test tool registration with missing required fields."""
        incomplete_data = {
            "name": "test_tool"
            # Missing required fields: client_id, description, schema
        }

        result = await service.register_tool_from_database(incomplete_data)

        assert result["success"] is False
        assert "Missing required field" in result["error"]

    @pytest.mark.asyncio

    async def test_tool_registration_from_file(self, service, sample_tool_file_content):
        """Test registering tools from a Python file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(sample_tool_file_content)
            f.flush()

            try:
                with patch.object(service.tools_collection, 'insert_many') as mock_insert:
                    mock_insert.return_value = AsyncMock()
                    mock_insert.return_value.inserted_ids = [ObjectId(), ObjectId()]

                    result = await service.register_tool_from_file(
                        file_path=f.name,
                        client_id="test-client",
                        industry="healthcare",
                        category="search",
                        description="Test healthcare tools"
                    )

                    assert result["success"] is True
                    assert result["tools_registered"] > 0
                    assert len(result["tool_ids"]) == result["tools_registered"]
                    mock_insert.assert_called_once()
            finally:
                os.unlink(f.name)

    @pytest.mark.asyncio

    async def test_tool_registration_invalid_file(self, service):
        """Test tool registration with invalid file path."""
        result = await service.register_tool_from_file(
            file_path="/nonexistent/file.py",
            client_id="test-client",
            industry="healthcare",
            category="search"
        )

        assert result["success"] is False
        assert "Failed to register tools" in result["error"]

    @pytest.mark.asyncio

    async def test_get_tools_by_client(self, service):
        """Test retrieving tools by client ID."""
        mock_tools = [
            {
                "_id": ObjectId(),
                "name": "tool1",
                "client_id": "test-client",
                "active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]

        with patch.object(service.tools_collection, 'find') as mock_find:
            mock_cursor = AsyncMock()
            mock_cursor.to_list.return_value = mock_tools
            mock_find.return_value = mock_cursor

            result = await service.get_tools_by_client("test-client")

            assert len(result) == 1
            assert result[0]["name"] == "tool1"
            assert result[0]["client_id"] == "test-client"

    @pytest.mark.asyncio

    async def test_get_tools_by_industry(self, service):
        """Test retrieving tools by industry."""
        mock_tools = [
            {
                "_id": ObjectId(),
                "name": "healthcare_tool",
                "industry": "healthcare",
                "active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]

        with patch.object(service.tools_collection, 'find') as mock_find:
            mock_cursor = AsyncMock()
            mock_cursor.to_list.return_value = mock_tools
            mock_find.return_value = mock_cursor

            result = await service.get_tools_by_industry("healthcare")

            assert len(result) == 1
            assert result[0]["industry"] == "healthcare"

    @pytest.mark.asyncio

    async def test_get_tool_by_id(self, service):
        """Test retrieving a specific tool by ID."""
        tool_id = ObjectId()
        mock_tool = {
            "_id": tool_id,
            "name": "test_tool",
            "client_id": "test-client",
            "active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        with patch.object(service.tools_collection, 'find_one') as mock_find:
            mock_find.return_value = mock_tool

            result = await service.get_tool_by_id(str(tool_id))

            assert result is not None
            assert result["name"] == "test_tool"
            assert result["id"] == str(tool_id)

    @pytest.mark.asyncio

    async def test_get_tool_by_invalid_id(self, service):
        """Test retrieving tool with invalid ID."""
        result = await service.get_tool_by_id("invalid-id")
        assert result is None

    @pytest.mark.asyncio

    async def test_update_tool(self, service):
        """Test updating tool metadata."""
        tool_id = str(ObjectId())
        updates = {
            "description": "Updated description",
            "active": False
        }

        with patch.object(service.tools_collection, 'update_one') as mock_update:
            mock_result = AsyncMock()
            mock_result.modified_count = 1
            mock_update.return_value = mock_result

            result = await service.update_tool(tool_id, updates)

            assert result["success"] is True
            assert result["message"] == "Tool updated successfully"

    @pytest.mark.asyncio

    async def test_update_nonexistent_tool(self, service):
        """Test updating a tool that doesn't exist."""
        tool_id = str(ObjectId())
        updates = {"description": "Updated description"}

        with patch.object(service.tools_collection, 'update_one') as mock_update:
            mock_result = AsyncMock()
            mock_result.modified_count = 0
            mock_update.return_value = mock_result

            result = await service.update_tool(tool_id, updates)

            assert result["success"] is False
            assert "not found" in result["error"]

    @pytest.mark.asyncio

    async def test_deactivate_tool(self, service):
        """Test deactivating a tool."""
        tool_id = str(ObjectId())

        with patch.object(service, 'update_tool') as mock_update:
            mock_update.return_value = {"success": True, "message": "Tool updated successfully"}

            result = await service.deactivate_tool(tool_id)

            assert result["success"] is True
            mock_update.assert_called_once_with(tool_id, {"active": False})

    @pytest.mark.asyncio

    async def test_search_tools(self, service):
        """Test searching tools with text query and filters."""
        mock_tools = [
            {
                "_id": ObjectId(),
                "name": "search_tool",
                "description": "Tool for searching healthcare providers",
                "client_id": "test-client",
                "active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]

        with patch.object(service.tools_collection, 'find') as mock_find:
            mock_cursor = AsyncMock()
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.to_list.return_value = mock_tools
            mock_find.return_value = mock_cursor

            result = await service.search_tools(
                query="healthcare",
                filters={"client_id": "test-client"},
                limit=10
            )

            assert len(result) == 1
            assert "search_tool" in result[0]["name"]

    @pytest.mark.asyncio

    async def test_bulk_register_tools(self, service, sample_tool_data):
        """Test bulk registration of multiple tools."""
        tools_data = [
            sample_tool_data,
            {**sample_tool_data, "name": "second_tool"}
        ]

        with patch.object(service, 'register_tool_from_database') as mock_register:
            mock_register.side_effect = [
                {"success": True, "tool_id": "id1", "endpoint": "/endpoint1"},
                {"success": True, "tool_id": "id2", "endpoint": "/endpoint2"}
            ]

            result = await service.bulk_register_tools(
                tools_data=tools_data,
                client_id="test-client",
                source="bulk_test"
            )

            assert result["success"] is True
            assert result["total_processed"] == 2
            assert result["successful_count"] == 2
            assert result["failed_count"] == 0

    @pytest.mark.asyncio

    async def test_bulk_register_tools_with_failures(self, service, sample_tool_data):
        """Test bulk registration with some failures."""
        tools_data = [
            sample_tool_data,
            {**sample_tool_data, "name": "failing_tool"}
        ]

        with patch.object(service, 'register_tool_from_database') as mock_register:
            mock_register.side_effect = [
                {"success": True, "tool_id": "id1", "endpoint": "/endpoint1"},
                {"success": False, "error": "Registration failed"}
            ]

            result = await service.bulk_register_tools(
                tools_data=tools_data,
                client_id="test-client",
                source="bulk_test"
            )

            assert result["success"] is True
            assert result["total_processed"] == 2
            assert result["successful_count"] == 1
            assert result["failed_count"] == 1

    @pytest.mark.asyncio

    async def test_execute_tool_success(self, service):
        """Test successful tool execution."""
        tool_id = str(ObjectId())
        mock_tool = {
            "_id": ObjectId(tool_id),
            "name": "test_tool",
            "active": True,
            "source": "database",
            "code": "result = {'success': True, 'data': 'test result'}"
        }

        with patch.object(service.tools_collection, 'find_one') as mock_find:
            mock_find.return_value = mock_tool

            with patch.object(service, 'update_tool_analytics') as mock_analytics:
                mock_analytics.return_value = None

                result = await service.execute_tool(tool_id, {})

                assert result["success"] is True
                assert result["result"]["success"] is True
                assert result["tool_name"] == "test_tool"
                mock_analytics.assert_called_once()

    @pytest.mark.asyncio

    async def test_execute_tool_not_found(self, service):
        """Test tool execution when tool doesn't exist."""
        tool_id = str(ObjectId())

        with patch.object(service.tools_collection, 'find_one') as mock_find:
            mock_find.return_value = None

            result = await service.execute_tool(tool_id, {})

            assert result["success"] is False
            assert "not found" in result["error"]

    @pytest.mark.asyncio

    async def test_execute_tool_inactive(self, service):
        """Test tool execution when tool is inactive."""
        tool_id = str(ObjectId())
        mock_tool = {
            "_id": ObjectId(tool_id),
            "name": "test_tool",
            "active": False
        }

        with patch.object(service.tools_collection, 'find_one') as mock_find:
            mock_find.return_value = mock_tool

            result = await service.execute_tool(tool_id, {})

            assert result["success"] is False
            assert "inactive" in result["error"]

    @pytest.mark.asyncio

    async def test_get_tool_analytics(self, service):
        """Test retrieving tool analytics."""
        tool_id = str(ObjectId())
        mock_tool = {
            "_id": ObjectId(tool_id),
            "name": "test_tool",
            "client_id": "test-client",
            "analytics": {
                "execution_count": 5,
                "error_count": 1,
                "average_response_time": 1.5
            }
        }

        with patch.object(service.tools_collection, 'find_one') as mock_find:
            mock_find.return_value = mock_tool

            result = await service.get_tool_analytics(tool_id)

            assert result["success"] is True
            assert result["analytics"]["execution_count"] == 5
            assert result["tool_name"] == "test_tool"

    @pytest.mark.asyncio

    async def test_update_tool_analytics(self, service):
        """Test updating tool analytics after execution."""
        tool_id = str(ObjectId())
        mock_tool = {
            "_id": ObjectId(tool_id),
            "analytics": {
                "execution_count": 5,
                "average_response_time": 1.0
            }
        }

        with patch.object(service.tools_collection, 'find_one') as mock_find_one:
            mock_find_one.return_value = mock_tool

            with patch.object(service.tools_collection, 'update_one') as mock_update:
                mock_update.return_value = AsyncMock()

                await service.update_tool_analytics(tool_id, 2.0, True)

                mock_update.assert_called_once()

    @pytest.mark.asyncio

    async def test_get_client_tools_summary(self, service):
        """Test getting client tools summary statistics."""
        mock_pipeline_result = [{
            "total_tools": 10,
            "active_tools": 8,
            "total_executions": 100,
            "total_errors": 5,
            "categories": ["search", "communication"],
            "industries": ["healthcare"]
        }]

        with patch.object(service.tools_collection, 'aggregate') as mock_aggregate:
            mock_cursor = AsyncMock()
            mock_cursor.to_list.return_value = mock_pipeline_result
            mock_aggregate.return_value = mock_cursor

            result = await service.get_client_tools_summary("test-client")

            assert result["success"] is True
            assert result["summary"]["total_tools"] == 10
            assert result["summary"]["success_rate"] == 95.0

    @pytest.mark.asyncio

    async def test_get_client_tools_summary_no_tools(self, service):
        """Test getting client tools summary when no tools exist."""
        with patch.object(service.tools_collection, 'aggregate') as mock_aggregate:
            mock_cursor = AsyncMock()
            mock_cursor.to_list.return_value = []
            mock_aggregate.return_value = mock_cursor

            result = await service.get_client_tools_summary("test-client")

            assert result["success"] is True
            assert result["summary"]["total_tools"] == 0
            assert result["summary"]["success_rate"] == 0

    @patch('requests.post')
    @pytest.mark.asyncio

    async def test_vapi_tool_creation(self, mock_post, service):
        """Test creating a tool in VAPI."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "vapi-tool-id"}
        mock_post.return_value = mock_response

        tool_data = {
            "server": {"url": "https://api.example.com/tool"},
            "function": {
                "name": "test_tool",
                "description": "Test tool",
                "parameters": {"type": "object", "properties": {}}
            }
        }

        result = await service._create_vapi_tool(tool_data)

        assert result["success"] is True
        assert result["vapi_tool_id"] == "vapi-tool-id"
        mock_post.assert_called_once()

    @patch('requests.post')
    @pytest.mark.asyncio

    async def test_vapi_tool_creation_failure(self, mock_post, service):
        """Test VAPI tool creation failure."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "Bad Request"}'
        mock_post.return_value = mock_response

        tool_data = {
            "server": {"url": "https://api.example.com/tool"},
            "function": {
                "name": "test_tool",
                "description": "Test tool",
                "parameters": {"type": "object", "properties": {}}
            }
        }

        result = await service._create_vapi_tool(tool_data)

        assert result["success"] is False
        assert "VAPI API error: 400" in result["error"]

    @patch('requests.patch')
    @pytest.mark.asyncio

    async def test_vapi_tool_update(self, mock_patch, service):
        """Test updating a tool in VAPI."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response

        tool_data = {
            "server": {"url": "https://api.example.com/tool"},
            "function": {
                "name": "test_tool",
                "description": "Updated test tool",
                "parameters": {"type": "object", "properties": {}}
            }
        }

        result = await service._update_vapi_tool("vapi-tool-id", tool_data)

        assert result["success"] is True
        assert result["vapi_tool_id"] == "vapi-tool-id"
        mock_patch.assert_called_once()

    @pytest.mark.asyncio

    async def test_sync_tool_with_vapi(self, service):
        """Test syncing a tool with VAPI."""
        tool_id = str(ObjectId())
        mock_tool = {
            "_id": ObjectId(tool_id),
            "name": "test_tool",
            "description": "Test tool",
            "server_url": "https://api.example.com/tool",
            "endpoint": "/test",
            "schema": {
                "function": {
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        }

        with patch.object(service.tools_collection, 'find_one') as mock_find:
            mock_find.return_value = mock_tool

            with patch.object(service, '_create_vapi_tool') as mock_create:
                mock_create.return_value = {
                    "success": True,
                    "vapi_tool_id": "new-vapi-id"
                }

                with patch.object(service.tools_collection, 'update_one') as mock_update:
                    mock_update.return_value = AsyncMock()

                    result = await service.sync_tool_with_vapi(tool_id)

                    assert result["success"] is True
                    mock_create.assert_called_once()
                    mock_update.assert_called_once()

    @pytest.mark.asyncio

    async def test_sync_tool_with_vapi_not_found(self, service):
        """Test syncing a tool that doesn't exist."""
        tool_id = str(ObjectId())

        with patch.object(service.tools_collection, 'find_one') as mock_find:
            mock_find.return_value = None

            result = await service.sync_tool_with_vapi(tool_id)

            assert result["success"] is False
            assert "not found" in result["error"]

    @pytest.mark.asyncio

    async def test_bulk_sync_tools_with_vapi(self, service):
        """Test bulk syncing tools with VAPI."""
        mock_tools = [
            {"_id": ObjectId(), "name": "tool1"},
            {"_id": ObjectId(), "name": "tool2"}
        ]

        with patch.object(service.tools_collection, 'find') as mock_find:
            mock_cursor = AsyncMock()
            mock_cursor.to_list.return_value = mock_tools
            mock_find.return_value = mock_cursor

            with patch.object(service, 'sync_tool_with_vapi') as mock_sync:
                mock_sync.side_effect = [
                    {"success": True, "vapi_tool_id": "id1"},
                    {"success": False, "error": "Sync failed"}
                ]

                result = await service.bulk_sync_tools_with_vapi("test-client")

                assert result["success"] is True
                assert result["total_processed"] == 2
                assert result["successful_count"] == 1
                assert result["failed_count"] == 1

    @pytest.mark.asyncio

    async def test_get_vapi_sync_status(self, service):
        """Test getting VAPI sync status."""
        mock_status_counts = [
            {"_id": "synced", "count": 5},
            {"_id": "pending", "count": 2},
            {"_id": "error", "count": 1}
        ]

        with patch.object(service.tools_collection, 'aggregate') as mock_aggregate:
            mock_cursor = AsyncMock()
            mock_cursor.to_list.return_value = mock_status_counts
            mock_aggregate.return_value = mock_cursor

            result = await service.get_vapi_sync_status("test-client")

            assert result["success"] is True
            assert result["sync_status"]["synced"] == 5
            assert result["sync_status"]["pending"] == 2
            assert result["sync_status"]["error"] == 1
            assert result["total_tools"] == 8

    @pytest.mark.asyncio

    async def test_get_tools_by_vapi_assistant(self, service):
        """Test getting tools associated with a VAPI assistant."""
        assistant_id = "test-assistant-id"
        mock_tools = [
            {
                "_id": ObjectId(),
                "name": "assistant_tool",
                "vapi_metadata": {"assistant_ids": [assistant_id]},
                "active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]

        with patch.object(service.tools_collection, 'find') as mock_find:
            mock_cursor = AsyncMock()
            mock_cursor.to_list.return_value = mock_tools
            mock_find.return_value = mock_cursor

            result = await service.get_tools_by_vapi_assistant(assistant_id)

            assert len(result) == 1
            assert result[0]["name"] == "assistant_tool"

    async def test_prepare_vapi_tool_data(self, service):
        """Test preparing tool data for VAPI API."""
        tool = {
            "name": "test_tool",
            "description": "Test tool description",
            "server_url": "https://api.example.com/tool",
            "endpoint": "/test",
            "schema": {
                "function": {
                    "parameters": {
                        "type": "object",
                        "properties": {"param1": {"type": "string"}},
                        "required": ["param1"]
                    }
                }
            }
        }

        result = service._prepare_vapi_tool_data(tool)

        assert result["server"]["url"] == "https://api.example.com/tool"
        assert result["function"]["name"] == "test_tool"
        assert result["function"]["description"] == "Test tool description"
        assert result["function"]["parameters"]["type"] == "object"
        assert "param1" in result["function"]["parameters"]["properties"]

    async def test_prepare_vapi_tool_data_missing_schema(self, service):
        """Test preparing VAPI tool data when schema is incomplete."""
        tool = {
            "name": "test_tool",
            "description": "Test tool description",
            "server_url": "https://api.example.com/tool",
            "endpoint": "/test",
            "schema": {}
        }

        result = service._prepare_vapi_tool_data(tool)

        assert result["function"]["parameters"]["type"] == "object"
        assert result["function"]["parameters"]["properties"] == {}
        assert result["function"]["parameters"]["required"] == []

    def test_format_tool_response(self, service):
        """Test formatting tool data for API response."""
        tool_id = ObjectId()
        tool = {
            "_id": tool_id,
            "name": "test_tool",
            "client_id": "test-client",
            "industry": "healthcare",
            "category": "search",
            "description": "Test tool",
            "endpoint": "/test",
            "method": "POST",
            "schema": {"type": "function"},
            "active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": {"version": "1.0"},
            "vapi_tool_id": "vapi-123",
            "server_url": "https://api.example.com/test",
            "vapi_sync_status": "synced",
            "deployment_status": "active",
            "vapi_metadata": {"assistant_ids": ["assistant-1"]}
        }

        result = service._format_tool_response(tool)

        assert result["id"] == str(tool_id)
        assert result["name"] == "test_tool"
        assert result["client_id"] == "test-client"
        assert result["vapi_tool_id"] == "vapi-123"
        assert result["vapi_sync_status"] == "synced"
        assert result["deployment_status"] == "active"

    def test_format_empty_tool_response(self, service):
        """Test formatting empty tool data."""
        result = service._format_tool_response(None)
        assert result == {}

        result = service._format_tool_response({})
        assert result == {}


class TestCustomToolsServiceIntegration:
    """Integration tests for CustomToolsService with real-like scenarios."""

    @pytest.fixture
    def service(self):
        """Create a CustomToolsService instance for integration testing."""
        service = CustomToolsService()
        return service

    @pytest.mark.asyncio

    async def test_full_tool_lifecycle(self, service):
        """Test the complete lifecycle of a tool: register, execute, update, deactivate."""
        # Mock all database operations
        tool_id = str(ObjectId())

        with patch.object(service.tools_collection, 'insert_one') as mock_insert, \
             patch.object(service.tools_collection, 'find_one') as mock_find_one, \
             patch.object(service.tools_collection, 'update_one') as mock_update:

            # Setup mocks
            mock_insert.return_value = AsyncMock()

            # Register tool
            tool_data = {
                "name": "lifecycle_test_tool",
                "client_id": "test-client",
                "description": "Tool for testing lifecycle",
                "schema": {
                    "type": "function",
                    "function": {
                        "name": "lifecycle_test_tool",
                        "description": "Tool for testing lifecycle",
                        "parameters": {"type": "object", "properties": {}}
                    }
                }
            }

            register_result = await service.register_tool_from_database(tool_data)
            assert register_result["success"] is True

            # Mock tool for execution
            mock_tool = {
                "_id": ObjectId(tool_id),
                "name": "lifecycle_test_tool",
                "active": True,
                "source": "database",
                "code": "result = {'message': 'Tool executed successfully'}"
            }
            mock_find_one.return_value = mock_tool

            # Execute tool
            with patch.object(service, 'update_tool_analytics'):
                execute_result = await service.execute_tool(tool_id, {})
                assert execute_result["success"] is True

            # Update tool
            mock_update.return_value.modified_count = 1
            update_result = await service.update_tool(tool_id, {"description": "Updated description"})
            assert update_result["success"] is True

            # Deactivate tool
            deactivate_result = await service.deactivate_tool(tool_id)
            assert deactivate_result["success"] is True

    @pytest.mark.asyncio

    async def test_vapi_integration_workflow(self, service):
        """Test the complete VAPI integration workflow."""
        tool_id = str(ObjectId())
        mock_tool = {
            "_id": ObjectId(tool_id),
            "name": "vapi_test_tool",
            "description": "Tool for VAPI testing",
            "server_url": "https://api.example.com/vapi-test",
            "endpoint": "/vapi-test",
            "schema": {
                "function": {
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        }

        with patch.object(service.tools_collection, 'find_one') as mock_find, \
             patch.object(service.tools_collection, 'update_one') as mock_update, \
             patch.object(service, '_create_vapi_tool') as mock_create_vapi:

            # Setup mocks
            mock_find.return_value = mock_tool
            mock_update.return_value = AsyncMock()
            mock_create_vapi.return_value = {
                "success": True,
                "vapi_tool_id": "vapi-integration-test-id"
            }

            # Test sync
            sync_result = await service.sync_tool_with_vapi(tool_id)

            assert sync_result["success"] is True
            mock_create_vapi.assert_called_once()
            mock_update.assert_called_once()

            # Verify the prepared VAPI data structure
            prepared_data = service._prepare_vapi_tool_data(mock_tool)
            assert "server" in prepared_data
            assert "function" in prepared_data
            assert prepared_data["server"]["url"] == "https://api.example.com/vapi-test"

    @pytest.mark.asyncio

    async def test_analytics_tracking_workflow(self, service):
        """Test the analytics tracking workflow."""
        tool_id = str(ObjectId())

        with patch.object(service.tools_collection, 'find_one') as mock_find_one, \
             patch.object(service.tools_collection, 'update_one') as mock_update:

            # Mock existing tool with analytics
            mock_tool = {
                "_id": ObjectId(tool_id),
                "analytics": {
                    "execution_count": 10,
                    "average_response_time": 1.5,
                    "error_count": 2
                }
            }
            mock_find_one.return_value = mock_tool
            mock_update.return_value = AsyncMock()

            # Update analytics
            await service.update_tool_analytics(tool_id, 2.0, True)

            # Verify update was called with correct data
            mock_update.assert_called_once()
            call_args = mock_update.call_args[0]
            assert call_args[0] == {"_id": ObjectId(tool_id)}

            # Check that analytics were updated correctly
            update_data = call_args[1]["$set"]
            assert "analytics.last_executed" in update_data
            assert update_data["$inc"]["analytics.execution_count"] == 1