"""
Tests for N8N Integration Service
Tests CRUD operations, health checks, and error handling for N8N workflows.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import httpx
from datetime import datetime
import json

import sys
import os
sys.path.append('.')

from backend.services.n8n_service import N8NService, N8nWorkflowConfig


class TestN8NService:
    """Test suite for N8N service operations."""

    @pytest.fixture
    def n8n_service(self):
        """Create N8N service instance with test configuration."""
        return N8NService(
            n8n_api_url="https://test-n8n.example.com",
            n8n_api_key="test_n8n_api_key_12345"
        )

    @pytest.fixture
    def sample_workflow_data(self):
        """Create sample workflow data for testing."""
        return {
            "name": "Test Healthcare Workflow",
            "nodes": [
                {
                    "id": "webhook-trigger",
                    "name": "VAPI Webhook Trigger",
                    "type": "n8n-nodes-base.webhook",
                    "typeVersion": 1,
                    "position": [100, 200],
                    "parameters": {
                        "path": "healthcare-test",
                        "httpMethod": "POST",
                        "responseMode": "responseNode"
                    }
                },
                {
                    "id": "extract-data",
                    "name": "Extract Call Data",
                    "type": "n8n-nodes-base.set",
                    "typeVersion": 1,
                    "position": [300, 200],
                    "parameters": {
                        "values": {
                            "string": [
                                {
                                    "name": "caller_id",
                                    "value": "={{ $json.customerNumber }}"
                                }
                            ]
                        }
                    }
                }
            ],
            "connections": {
                "VAPI Webhook Trigger": {
                    "main": [
                        [
                            {
                                "node": "Extract Call Data",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                }
            },
            "settings": {
                "executionOrder": "v1",
                "saveDataErrorExecution": "all",
                "saveDataSuccessExecution": "all",
                "saveExecutionProgress": True,
                "saveManualExecutions": True,
                "timezone": "UTC"
            }
        }

    @pytest.mark.asyncio
    async def test_create_workflow_success(self, n8n_service, sample_workflow_data):
        """Test successful workflow creation."""
        mock_response_data = {
            "id": "workflow_12345",
            "name": "Test Healthcare Workflow",
            "active": False,
            "createdAt": "2025-09-19T20:00:00Z"
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = mock_response_data

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await n8n_service.create_workflow(sample_workflow_data)

            assert result["success"] is True
            assert result["id"] == "workflow_12345"
            assert result["name"] == "Test Healthcare Workflow"
            assert result["active"] is False
            assert "webhook_urls" in result

    @pytest.mark.asyncio
    async def test_create_workflow_api_error(self, n8n_service, sample_workflow_data):
        """Test workflow creation with API error."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Invalid workflow configuration"

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await n8n_service.create_workflow(sample_workflow_data)

            assert result["success"] is False
            assert "API error: 400" in result["error"]

    @pytest.mark.asyncio
    async def test_create_workflow_with_mcp_tools_fallback(self, n8n_service, sample_workflow_data):
        """Test workflow creation with MCP tools fallback."""
        with patch.object(n8n_service, '_extract_webhook_urls') as mock_extract:
            mock_extract.return_value = {"VAPI Webhook Trigger": "https://test-n8n.example.com/webhook/healthcare-test"}

            # Mock MCP tools not available, should fallback to direct API call
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.status_code = 201
                mock_response.json.return_value = {
                    "id": "workflow_mcp_test",
                    "name": "Test Healthcare Workflow",
                    "active": False
                }

                mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

                result = await n8n_service.create_workflow(sample_workflow_data)

                assert result["success"] is True
                assert result["id"] == "workflow_mcp_test"
                assert "webhook_urls" in result

    @pytest.mark.asyncio
    async def test_stop_workflow_success(self, n8n_service):
        """Test successful workflow deactivation."""
        workflow_id = "workflow_12345"

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200

            mock_client.return_value.__aenter__.return_value.patch.return_value = mock_response

            result = await n8n_service.stop_workflow(workflow_id)

            assert result is True

    @pytest.mark.asyncio
    async def test_stop_workflow_failure(self, n8n_service):
        """Test workflow deactivation failure."""
        workflow_id = "nonexistent_workflow"

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 404

            mock_client.return_value.__aenter__.return_value.patch.return_value = mock_response

            result = await n8n_service.stop_workflow(workflow_id)

            assert result is False

    @pytest.mark.asyncio
    async def test_activate_workflow_success(self, n8n_service):
        """Test successful workflow activation."""
        workflow_id = "workflow_12345"

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200

            mock_client.return_value.__aenter__.return_value.patch.return_value = mock_response

            result = await n8n_service.activate_workflow(workflow_id)

            assert result is True

    @pytest.mark.asyncio
    async def test_trigger_workflow_success(self, n8n_service):
        """Test successful workflow trigger."""
        workflow_id = "workflow_12345"
        trigger_data = {
            "customerNumber": "+1234567890",
            "assistantId": "assistant_123",
            "type": "inbound"
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "executionId": "execution_12345"
            }

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await n8n_service.trigger_workflow(workflow_id, trigger_data)

            assert result["success"] is True
            assert result["executionId"] == "execution_12345"

    def test_extract_webhook_urls(self, n8n_service, sample_workflow_data):
        """Test webhook URL extraction from workflow."""
        workflow_id = "workflow_test"

        result = n8n_service._extract_webhook_urls(sample_workflow_data, workflow_id)

        assert "VAPI Webhook Trigger" in result
        assert "healthcare-test" in result["VAPI Webhook Trigger"]

    def test_extract_webhook_urls_no_webhooks(self, n8n_service):
        """Test webhook URL extraction with no webhook nodes."""
        workflow_data = {
            "nodes": [
                {
                    "name": "Regular Node",
                    "type": "n8n-nodes-base.set",
                    "parameters": {}
                }
            ]
        }
        workflow_id = "workflow_test"

        result = n8n_service._extract_webhook_urls(workflow_data, workflow_id)

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_workflow_template_success(self, n8n_service):
        """Test successful workflow template search."""
        with patch.object(n8n_service, 'find_matching_workflow') as mock_find:
            mock_find.return_value = {
                "id": "template_123",
                "name": "Healthcare Template",
                "nodes": [],
                "connections": {}
            }

            result = await n8n_service.search_workflow_template(
                template_name="healthcare",
                description="Provider search automation",
                category="healthcare"
            )

            assert result["success"] is True
            assert result["workflow"]["id"] == "template_123"

    @pytest.mark.asyncio
    async def test_search_workflow_template_not_found(self, n8n_service):
        """Test workflow template search when not found."""
        with patch.object(n8n_service, 'find_matching_workflow') as mock_find:
            mock_find.return_value = None

            result = await n8n_service.search_workflow_template(
                template_name="nonexistent",
                description="",
                category=""
            )

            assert result["success"] is False
            assert "No suitable workflow template found" in result["message"]

    @pytest.mark.asyncio
    async def test_search_workflow_template_no_name(self, n8n_service):
        """Test workflow template search without template name."""
        result = await n8n_service.search_workflow_template(
            template_name="",
            description="Test",
            category="test"
        )

        assert result["success"] is False
        assert "Template name is required" in result["message"]

    @pytest.mark.asyncio
    async def test_create_workflow_from_template_success(self, n8n_service):
        """Test creating workflow from template."""
        template_id = 1234
        campaign_data = {
            "id": "campaign_123",
            "name": "Test Campaign",
            "type": "healthcare"
        }

        mock_template = {
            "id": template_id,
            "name": "Healthcare Template",
            "nodes": [
                {
                    "name": "Webhook",
                    "type": "n8n-nodes-base.webhook",
                    "parameters": {"path": "template-webhook"}
                }
            ],
            "connections": {}
        }

        with patch.object(n8n_service, 'get_template_from_repository') as mock_get_template, \
             patch.object(n8n_service, 'customize_workflow_for_campaign') as mock_customize, \
             patch('httpx.AsyncClient') as mock_client:

            mock_get_template.return_value = mock_template
            mock_customize.return_value = {
                "name": "Customized Healthcare Workflow",
                "nodes": mock_template["nodes"],
                "connections": mock_template["connections"]
            }

            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": "workflow_from_template"}

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await n8n_service.create_workflow_from_template(template_id, campaign_data)

            assert result == "workflow_from_template"

    @pytest.mark.asyncio
    async def test_create_workflow_from_template_not_found(self, n8n_service):
        """Test creating workflow from non-existent template."""
        template_id = 9999
        campaign_data = {"id": "campaign_123"}

        with patch.object(n8n_service, 'get_template_from_repository') as mock_get_template:
            mock_get_template.return_value = None

            result = await n8n_service.create_workflow_from_template(template_id, campaign_data)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_template_from_repository_success(self, n8n_service):
        """Test successful template retrieval from repository."""
        template_id = 1234

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "template": {
                    "id": template_id,
                    "name": "Test Template",
                    "nodes": [],
                    "connections": {}
                }
            }

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await n8n_service.get_template_from_repository(template_id)

            assert result is not None
            assert result["id"] == template_id
            assert result["name"] == "Test Template"

    @pytest.mark.asyncio
    async def test_get_template_from_repository_not_found(self, n8n_service):
        """Test template retrieval when not found."""
        template_id = 9999

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 404

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await n8n_service.get_template_from_repository(template_id)

            assert result is None

    @pytest.mark.asyncio
    async def test_workflow_health_check_comprehensive(self, n8n_service, sample_workflow_data):
        """Test comprehensive health check of N8N workflow operations."""
        # Test workflow creation
        with patch('httpx.AsyncClient') as mock_client:
            # Mock successful workflow creation
            mock_create_response = Mock()
            mock_create_response.status_code = 201
            mock_create_response.json.return_value = {
                "id": "health_check_workflow",
                "name": "Health Check Workflow",
                "active": False
            }

            # Mock successful workflow activation
            mock_activate_response = Mock()
            mock_activate_response.status_code = 200

            # Mock successful workflow stop
            mock_stop_response = Mock()
            mock_stop_response.status_code = 200

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_create_response
            mock_client.return_value.__aenter__.return_value.patch.return_value = mock_activate_response

            # Health check sequence
            create_result = await n8n_service.create_workflow(sample_workflow_data)
            assert create_result["success"] is True

            workflow_id = create_result["id"]

            activate_result = await n8n_service.activate_workflow(workflow_id)
            assert activate_result is True

            # Reset mock for stop operation
            mock_client.return_value.__aenter__.return_value.patch.return_value = mock_stop_response

            stop_result = await n8n_service.stop_workflow(workflow_id)
            assert stop_result is True

    @pytest.mark.asyncio
    async def test_workflow_webhook_connectivity(self, n8n_service, sample_workflow_data):
        """Test webhook connectivity after workflow creation."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": "webhook_test_workflow",
                "name": "Webhook Test Workflow",
                "active": True
            }

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await n8n_service.create_workflow(sample_workflow_data)

            assert result["success"] is True
            assert "webhook_urls" in result

            # Verify webhook URLs are properly formatted
            webhook_urls = result["webhook_urls"]
            if webhook_urls:
                for node_name, webhook_url in webhook_urls.items():
                    assert webhook_url.startswith("https://")
                    assert "webhook" in webhook_url

    def test_n8n_workflow_config_model(self):
        """Test N8nWorkflowConfig model validation."""
        config = N8nWorkflowConfig(
            workflow_name="Test Workflow",
            enabled=True,
            webhook_urls=["https://example.com/webhook1"],
            endpoints=["https://example.com/endpoint1"]
        )

        assert config.workflow_name == "Test Workflow"
        assert config.enabled is True
        assert len(config.webhook_urls) == 1
        assert config.template_id is None

    @pytest.mark.asyncio
    async def test_error_handling_and_logging(self, n8n_service, sample_workflow_data):
        """Test error handling and logging in various scenarios."""
        # Test network error
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Network error")

            result = await n8n_service.create_workflow(sample_workflow_data)

            assert result["success"] is False
            assert "Network error" in result["error"]

    def test_service_configuration(self):
        """Test N8N service configuration and initialization."""
        service = N8NService(
            n8n_api_url="https://custom-n8n.example.com",
            n8n_api_key="custom_api_key"
        )

        assert service.n8n_api_url == "https://custom-n8n.example.com"
        assert service.n8n_api_key == "custom_api_key"
        assert "X-N8N-API-KEY" in service.headers
        assert "Authorization" in service.headers

    def test_default_configuration(self):
        """Test N8N service with default configuration."""
        service = N8NService()

        assert service.n8n_api_url == "https://automate.inspirecreations.it.com"
        assert service.n8n_api_key is not None
        assert len(service.headers) >= 3  # API key, Authorization, Content-Type


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])