"""
Tests for Automation Orchestration Service Monitoring and Health Checks
Tests the real monitoring functionality with VAPI and n8n MCP/API tools.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
import httpx

import sys
import os
sys.path.append('.')

from backend.services.automation_orchestration_service import (
    AutomationOrchestrationService,
    AutomationConfig,
    AutomationStatus,
    DeploymentStage
)


class TestAutomationMonitoring:
    """Test suite for automation monitoring and health checks."""

    @pytest.fixture
    def orchestration_service(self):
        """Create automation orchestration service instance."""
        service = AutomationOrchestrationService()
        # Mock the database connections for testing
        service.configs_collection = Mock()
        service.templates_collection = Mock()
        return service

    @pytest.fixture
    def sample_deployed_config(self):
        """Create sample deployed automation config."""
        return AutomationConfig(
            id="config_123",
            user_id="user_456",
            template_id="template_789",
            automation_name="Test Healthcare Automation",
            config={
                "vapiAgent": {
                    "systemPrompt": "You are a healthcare assistant.",
                    "voiceSettings": {"voice": "alloy"}
                },
                "n8nWorkflow": {
                    "workflowName": "Healthcare Workflow"
                }
            },
            status=AutomationStatus.DEPLOYED,
            deployment_info={
                "vapi_assistant_id": "assistant_12345",
                "n8n_workflow_id": "workflow_67890",
                "webhook_urls": {
                    "VAPI Webhook Trigger": "https://n8n.example.com/webhook/healthcare-test"
                },
                "deployed_at": datetime.now(timezone.utc).isoformat()
            },
            created_at=datetime.now(timezone.utc),
            deployed_at=datetime.now(timezone.utc)
        )

    @pytest.mark.asyncio
    async def test_check_automation_health_all_healthy(self, orchestration_service, sample_deployed_config):
        """Test health check when all components are healthy."""
        # Mock VAPI service health check
        mock_vapi_service = Mock()
        mock_vapi_service.get_assistant = AsyncMock(return_value={
            "success": True,
            "assistant": {
                "id": "assistant_12345",
                "name": "Test Healthcare Assistant",
                "model": {"provider": "openai", "model": "gpt-4"}
            }
        })
        orchestration_service.vapi_service = mock_vapi_service

        # Mock N8N service and workflow status check
        orchestration_service.n8n_service = Mock()
        orchestration_service.n8n_service.n8n_api_url = "https://n8n.example.com"
        orchestration_service.n8n_service.headers = {"Authorization": "Bearer test"}

        with patch.object(orchestration_service, '_check_n8n_workflow_status') as mock_n8n_check:
            mock_n8n_check.return_value = {
                "accessible": True,
                "active": True,
                "name": "Healthcare Workflow"
            }

            result = await orchestration_service._check_automation_health(sample_deployed_config)

            assert result["overall"] == "healthy"
            assert "vapi" in result["components"]
            assert "n8n" in result["components"]
            assert result["components"]["vapi"]["status"] == "healthy"
            assert result["components"]["n8n"]["status"] == "healthy"
            assert result["components"]["vapi"]["assistant_id"] == "assistant_12345"
            assert result["components"]["n8n"]["workflow_id"] == "workflow_67890"

    @pytest.mark.asyncio
    async def test_check_automation_health_vapi_unhealthy(self, orchestration_service, sample_deployed_config):
        """Test health check when VAPI component is unhealthy."""
        # Mock VAPI service health check failure
        mock_vapi_service = Mock()
        mock_vapi_service.get_assistant = AsyncMock(return_value={
            "success": False,
            "error": "Assistant not found"
        })
        orchestration_service.vapi_service = mock_vapi_service

        # Mock N8N service healthy
        orchestration_service.n8n_service = Mock()
        with patch.object(orchestration_service, '_check_n8n_workflow_status') as mock_n8n_check:
            mock_n8n_check.return_value = {
                "accessible": True,
                "active": True
            }

            result = await orchestration_service._check_automation_health(sample_deployed_config)

            assert result["overall"] == "degraded"
            assert result["components"]["vapi"]["status"] == "unhealthy"
            assert result["components"]["n8n"]["status"] == "healthy"
            assert "Assistant not found" in result["components"]["vapi"]["error"]

    @pytest.mark.asyncio
    async def test_check_automation_health_n8n_unhealthy(self, orchestration_service, sample_deployed_config):
        """Test health check when n8n component is unhealthy."""
        # Mock VAPI service healthy
        mock_vapi_service = Mock()
        mock_vapi_service.get_assistant = AsyncMock(return_value={
            "success": True,
            "assistant": {"id": "assistant_12345", "name": "Test Assistant"}
        })
        orchestration_service.vapi_service = mock_vapi_service

        # Mock N8N service unhealthy
        orchestration_service.n8n_service = Mock()
        with patch.object(orchestration_service, '_check_n8n_workflow_status') as mock_n8n_check:
            mock_n8n_check.return_value = {
                "accessible": False,
                "error": "Workflow not found"
            }

            result = await orchestration_service._check_automation_health(sample_deployed_config)

            assert result["overall"] == "degraded"
            assert result["components"]["vapi"]["status"] == "healthy"
            assert result["components"]["n8n"]["status"] == "unhealthy"
            assert "Workflow not found" in result["components"]["n8n"]["error"]

    @pytest.mark.asyncio
    async def test_check_n8n_workflow_status_success(self, orchestration_service):
        """Test n8n workflow status check with successful response."""
        workflow_id = "workflow_12345"
        webhook_urls = {"VAPI Webhook Trigger": "https://n8n.example.com/webhook/test"}

        mock_workflow_data = {
            "id": workflow_id,
            "name": "Test Workflow",
            "active": True,
            "nodes": [
                {"type": "n8n-nodes-base.webhook", "name": "Webhook Trigger"}
            ]
        }

        with patch('httpx.AsyncClient') as mock_client:
            # Mock workflow API response
            mock_workflow_response = Mock()
            mock_workflow_response.status_code = 200
            mock_workflow_response.json.return_value = mock_workflow_data

            # Mock webhook test response
            mock_webhook_response = Mock()
            mock_webhook_response.status_code = 405  # Method Not Allowed is expected

            mock_client.return_value.__aenter__.return_value.get.side_effect = [
                mock_workflow_response,  # First call for workflow
                mock_webhook_response    # Second call for webhook test
            ]

            orchestration_service.n8n_service = Mock()
            orchestration_service.n8n_service.n8n_api_url = "https://n8n.example.com"
            orchestration_service.n8n_service.headers = {"Authorization": "Bearer test"}

            result = await orchestration_service._check_n8n_workflow_status(workflow_id, webhook_urls)

            assert result["accessible"] is True
            assert result["active"] is True
            assert result["name"] == "Test Workflow"
            assert "webhook_status" in result
            assert result["webhook_status"]["VAPI Webhook Trigger"]["accessible"] is True

    @pytest.mark.asyncio
    async def test_check_n8n_workflow_status_not_found(self, orchestration_service):
        """Test n8n workflow status check when workflow not found."""
        workflow_id = "nonexistent_workflow"
        webhook_urls = {}

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 404

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            orchestration_service.n8n_service = Mock()
            orchestration_service.n8n_service.n8n_api_url = "https://n8n.example.com"
            orchestration_service.n8n_service.headers = {"Authorization": "Bearer test"}

            result = await orchestration_service._check_n8n_workflow_status(workflow_id, webhook_urls)

            assert result["accessible"] is False
            assert "Workflow not found" in result["error"]

    @pytest.mark.asyncio
    async def test_test_vapi_assistant_success(self, orchestration_service):
        """Test VAPI assistant test functionality."""
        assistant_id = "assistant_12345"

        mock_vapi_service = Mock()
        mock_vapi_service.get_assistant = AsyncMock(return_value={
            "success": True,
            "assistant": {
                "id": assistant_id,
                "name": "Test Healthcare Assistant",
                "model": {"provider": "openai", "model": "gpt-4"},
                "voice": {"provider": "openai", "voiceId": "alloy"}
            }
        })
        orchestration_service.vapi_service = mock_vapi_service

        result = await orchestration_service.testVAPIAssistant(assistant_id)

        assert result["success"] is True
        assert result["assistant_id"] == assistant_id
        assert result["assistant_name"] == "Test Healthcare Assistant"
        assert "model" in result
        assert "voice" in result
        assert "tested_at" in result

    @pytest.mark.asyncio
    async def test_test_vapi_assistant_failure(self, orchestration_service):
        """Test VAPI assistant test when assistant not accessible."""
        assistant_id = "nonexistent_assistant"

        mock_vapi_service = Mock()
        mock_vapi_service.get_assistant = AsyncMock(return_value={
            "success": False,
            "error": "Assistant not found"
        })
        orchestration_service.vapi_service = mock_vapi_service

        result = await orchestration_service.testVAPIAssistant(assistant_id)

        assert result["success"] is False
        assert result["assistant_id"] == assistant_id
        assert "Assistant not found" in result["error"]

    @pytest.mark.asyncio
    async def test_test_vapi_assistant_no_service(self, orchestration_service):
        """Test VAPI assistant test when service not available."""
        orchestration_service.vapi_service = None

        result = await orchestration_service.testVAPIAssistant("assistant_123")

        assert result["success"] is False
        assert result["error"] == "VAPI service not available"

    @pytest.mark.asyncio
    async def test_test_n8n_workflow_success(self, orchestration_service):
        """Test n8n workflow test functionality."""
        workflow_id = "workflow_12345"

        mock_workflow_data = {
            "id": workflow_id,
            "name": "Test Healthcare Workflow",
            "active": True,
            "nodes": [
                {"type": "n8n-nodes-base.webhook", "name": "Webhook1"},
                {"type": "n8n-nodes-base.set", "name": "Set Data"},
                {"type": "n8n-nodes-base.webhook", "name": "Webhook2"}
            ]
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_workflow_data

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            orchestration_service.n8n_service = Mock()
            orchestration_service.n8n_service.n8n_api_url = "https://n8n.example.com"
            orchestration_service.n8n_service.headers = {"Authorization": "Bearer test"}

            result = await orchestration_service.testN8NWorkflow(workflow_id)

            assert result["success"] is True
            assert result["workflow_id"] == workflow_id
            assert result["workflow_name"] == "Test Healthcare Workflow"
            assert result["active"] is True
            assert result["node_count"] == 3
            assert result["webhook_count"] == 2
            assert "tested_at" in result

    @pytest.mark.asyncio
    async def test_test_n8n_workflow_failure(self, orchestration_service):
        """Test n8n workflow test when workflow not accessible."""
        workflow_id = "nonexistent_workflow"

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 404

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            orchestration_service.n8n_service = Mock()
            orchestration_service.n8n_service.n8n_api_url = "https://n8n.example.com"
            orchestration_service.n8n_service.headers = {"Authorization": "Bearer test"}

            result = await orchestration_service.testN8NWorkflow(workflow_id)

            assert result["success"] is False
            assert result["workflow_id"] == workflow_id
            assert "Workflow not accessible" in result["error"]

    @pytest.mark.asyncio
    async def test_test_n8n_workflow_no_service(self, orchestration_service):
        """Test n8n workflow test when service not available."""
        orchestration_service.n8n_service = None

        result = await orchestration_service.testN8NWorkflow("workflow_123")

        assert result["success"] is False
        assert result["error"] == "N8N service not available"

    @pytest.mark.asyncio
    async def test_get_configuration_status_deployed(self, orchestration_service, sample_deployed_config):
        """Test getting configuration status for deployed automation."""
        config_id = "config_123"

        # Mock the get_config method
        with patch.object(orchestration_service, 'get_config') as mock_get_config, \
             patch.object(orchestration_service, '_check_automation_health') as mock_health_check, \
             patch.object(orchestration_service, '_get_automation_metrics') as mock_metrics:

            mock_get_config.return_value = sample_deployed_config

            mock_health_check.return_value = {
                "overall": "healthy",
                "components": {
                    "vapi": {"status": "healthy"},
                    "n8n": {"status": "healthy"}
                }
            }

            mock_metrics.return_value = {
                "calls_today": 15,
                "success_rate": 95.2,
                "avg_response_time": 1.8
            }

            result = await orchestration_service.get_configuration_status(config_id)

            assert result is not None
            assert result["config_id"] == config_id
            assert result["status"] == "deployed"
            assert result["automation_name"] == "Test Healthcare Automation"
            assert "health" in result
            assert "metrics" in result
            assert result["health"]["overall"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_configuration_status_not_found(self, orchestration_service):
        """Test getting configuration status for non-existent config."""
        config_id = "nonexistent_config"

        with patch.object(orchestration_service, 'get_config') as mock_get_config:
            mock_get_config.return_value = None

            result = await orchestration_service.get_configuration_status(config_id)

            assert result is None

    @pytest.mark.asyncio
    async def test_health_check_comprehensive_flow(self, orchestration_service, sample_deployed_config):
        """Test comprehensive health check flow including error recovery."""
        # Simulate VAPI service initially failing, then recovering
        mock_vapi_service = Mock()
        call_count = 0

        async def mock_get_assistant(assistant_id):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"success": False, "error": "Network timeout"}
            else:
                return {
                    "success": True,
                    "assistant": {"id": assistant_id, "name": "Recovered Assistant"}
                }

        mock_vapi_service.get_assistant = mock_get_assistant
        orchestration_service.vapi_service = mock_vapi_service
        orchestration_service.n8n_service = Mock()

        with patch.object(orchestration_service, '_check_n8n_workflow_status') as mock_n8n_check:
            mock_n8n_check.return_value = {"accessible": True, "active": True}

            # First health check - VAPI fails
            result1 = await orchestration_service._check_automation_health(sample_deployed_config)
            assert result1["overall"] == "degraded"
            assert result1["components"]["vapi"]["status"] == "unhealthy"

            # Second health check - VAPI recovers
            result2 = await orchestration_service._check_automation_health(sample_deployed_config)
            assert result2["overall"] == "healthy"
            assert result2["components"]["vapi"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_monitoring_with_webhook_connectivity(self, orchestration_service):
        """Test monitoring including webhook connectivity checks."""
        workflow_id = "workflow_test"
        webhook_urls = {
            "VAPI Webhook": "https://n8n.example.com/webhook/test1",
            "API Webhook": "https://n8n.example.com/webhook/test2"
        }

        with patch('httpx.AsyncClient') as mock_client:
            # Mock workflow exists
            mock_workflow_response = Mock()
            mock_workflow_response.status_code = 200
            mock_workflow_response.json.return_value = {
                "id": workflow_id,
                "name": "Test Workflow",
                "active": True
            }

            # Mock webhook responses - one accessible, one not
            mock_webhook_responses = [
                Mock(status_code=405),  # First webhook accessible
                Mock(status_code=500)   # Second webhook error
            ]

            mock_client.return_value.__aenter__.return_value.get.side_effect = [
                mock_workflow_response,
                mock_webhook_responses[0],
                mock_webhook_responses[1]
            ]

            orchestration_service.n8n_service = Mock()
            orchestration_service.n8n_service.n8n_api_url = "https://n8n.example.com"
            orchestration_service.n8n_service.headers = {"Authorization": "Bearer test"}

            result = await orchestration_service._check_n8n_workflow_status(workflow_id, webhook_urls)

            assert result["accessible"] is True
            assert "webhook_status" in result
            assert result["webhook_status"]["VAPI Webhook"]["accessible"] is True
            assert result["webhook_status"]["API Webhook"]["accessible"] is False


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])