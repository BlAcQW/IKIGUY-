"""Tests for n8n workflow service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
import httpx

from backend.services.n8n_workflow_service import N8nWorkflowService
from backend.models import Campaign


@pytest.fixture
def n8n_service():
    """Create n8n service instance for testing."""
    return N8nWorkflowService(
        n8n_api_url="https://test.n8n.com/api/v1",
        n8n_api_key="test-key"
    )


@pytest.fixture
def sample_campaign():
    """Create sample campaign for testing."""
    campaign_data = {
        "id": uuid4(),
        "name": "Test Campaign",
        "description": "Test campaign for n8n integration",
        "tenant_id": uuid4(),
        "status": "draft",
        "category": "marketing"
    }
    return Campaign(**campaign_data)


@pytest.fixture
def sample_template():
    """Create sample n8n template data."""
    return {
        "id": 6213,
        "name": "Customer Reactivation Template",
        "description": "Reactivate dormant customers",
        "nodes": [
            {
                "id": "webhook-1",
                "type": "n8n-nodes-base.webhook",
                "name": "Webhook Trigger",
                "position": [0, 0],
                "parameters": {"path": "customer-webhook"}
            },
            {
                "id": "sheets-1",
                "type": "n8n-nodes-base.googleSheets",
                "name": "Google Sheets",
                "position": [200, 0],
                "parameters": {}
            }
        ],
        "connections": {
            "Webhook Trigger": {
                "main": [[{"node": "Google Sheets", "type": "main", "index": 0}]]
            }
        },
        "metadata": {
            "complexity": "complex",
            "estimated_setup_minutes": 30
        }
    }


class TestN8nWorkflowService:
    """Test cases for N8nWorkflowService."""

    @pytest.mark.asyncio
    async def test_get_template_from_repository_success(self, n8n_service, sample_template):
        """Test successful template fetch from repository."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"template": sample_template}

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await n8n_service.get_template_from_repository(6213)

            assert result == sample_template
            mock_client.return_value.__aenter__.return_value.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_template_from_repository_not_found(self, n8n_service):
        """Test template not found scenario."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await n8n_service.get_template_from_repository(99999)

            assert result is None

    @pytest.mark.asyncio
    async def test_create_workflow_from_template_success(self, n8n_service, sample_campaign, sample_template):
        """Test successful workflow creation from template."""
        mock_template_response = MagicMock()
        mock_template_response.status_code = 200
        mock_template_response.json.return_value = {"template": sample_template}

        mock_workflow_response = MagicMock()
        mock_workflow_response.status_code = 201
        mock_workflow_response.json.return_value = {"id": "workflow-123"}

        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = mock_client.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(side_effect=[mock_template_response, mock_workflow_response])

            result = await n8n_service.create_workflow_from_template(6213, sample_campaign)

            assert result == "workflow-123"
            assert mock_client_instance.post.call_count == 2

    @pytest.mark.asyncio
    async def test_create_workflow_from_template_template_not_found(self, n8n_service, sample_campaign):
        """Test workflow creation fails when template not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await n8n_service.create_workflow_from_template(99999, sample_campaign)

            assert result is None

    @pytest.mark.asyncio
    async def test_activate_workflow_success(self, n8n_service):
        """Test successful workflow activation."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.patch = AsyncMock(return_value=mock_response)

            result = await n8n_service.activate_workflow("workflow-123")

            assert result is True

    @pytest.mark.asyncio
    async def test_activate_workflow_failure(self, n8n_service):
        """Test workflow activation failure."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.patch = AsyncMock(return_value=mock_response)

            result = await n8n_service.activate_workflow("invalid-workflow")

            assert result is False

    @pytest.mark.asyncio
    async def test_deactivate_workflow_success(self, n8n_service):
        """Test successful workflow deactivation."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.patch = AsyncMock(return_value=mock_response)

            result = await n8n_service.deactivate_workflow("workflow-123")

            assert result is True

    @pytest.mark.asyncio
    async def test_get_workflow_webhooks(self, n8n_service):
        """Test extracting webhook URLs from workflow."""
        workflow_data = {
            "id": "workflow-123",
            "name": "Test Workflow",
            "nodes": [
                {
                    "type": "n8n-nodes-base.webhook",
                    "parameters": {"path": "test-webhook"}
                },
                {
                    "type": "n8n-nodes-base.webhook",
                    "parameters": {"path": "another-webhook"}
                },
                {
                    "type": "n8n-nodes-base.googleSheets",
                    "parameters": {}
                }
            ]
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = workflow_data

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await n8n_service.get_workflow_webhooks("workflow-123")

            expected_webhooks = [
                "https://test.n8n.com/webhook/test-webhook",
                "https://test.n8n.com/webhook/another-webhook"
            ]
            assert result == expected_webhooks

    @pytest.mark.asyncio
    async def test_trigger_workflow_success(self, n8n_service):
        """Test successful workflow trigger."""
        trigger_data = {"campaign_id": "test-campaign", "action": "start"}
        execution_result = {"executionId": "exec-123", "status": "success"}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = execution_result

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await n8n_service.trigger_workflow("workflow-123", trigger_data)

            assert result == execution_result

    @pytest.mark.asyncio
    async def test_trigger_workflow_failure(self, n8n_service):
        """Test workflow trigger failure."""
        mock_response = MagicMock()
        mock_response.status_code = 400

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await n8n_service.trigger_workflow("workflow-123", {})

            assert result is None

    @pytest.mark.asyncio
    async def test_delete_workflow_success(self, n8n_service):
        """Test successful workflow deletion."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.delete = AsyncMock(return_value=mock_response)

            result = await n8n_service.delete_workflow("workflow-123")

            assert result is True

    def test_customize_workflow_for_campaign(self, n8n_service, sample_campaign, sample_template):
        """Test workflow customization for specific campaign."""
        result = n8n_service._customize_workflow_for_campaign(sample_template, sample_campaign)

        # Check workflow name includes campaign name
        assert sample_campaign.name in result["name"]

        # Check campaign tags are added
        expected_tags = [
            {"name": f"campaign-{sample_campaign.id}"},
            {"name": f"template-{sample_template['id']}"},
            {"name": sample_campaign.category}
        ]
        assert result["tags"] == expected_tags

        # Check webhook path customization
        webhook_node = next(
            (node for node in result["nodes"] if node["type"] == "n8n-nodes-base.webhook"),
            None
        )
        assert webhook_node is not None
        assert webhook_node["parameters"]["path"] == f"campaign-{sample_campaign.id}-webhook"

        # Check Google Sheets node customization
        sheets_node = next(
            (node for node in result["nodes"] if node["type"] == "n8n-nodes-base.googleSheets"),
            None
        )
        assert sheets_node is not None
        assert sheets_node["parameters"]["campaignId"] == str(sample_campaign.id)
        assert sheets_node["parameters"]["campaignName"] == sample_campaign.name

    def test_extract_webhook_urls(self, n8n_service):
        """Test webhook URL extraction from workflow."""
        workflow = {
            "nodes": [
                {
                    "type": "n8n-nodes-base.webhook",
                    "parameters": {"path": "webhook1"}
                },
                {
                    "type": "n8n-nodes-base.webhook",
                    "parameters": {"path": "webhook2"}
                },
                {
                    "type": "other-node",
                    "parameters": {}
                }
            ]
        }

        result = n8n_service._extract_webhook_urls(workflow)

        expected = [
            "https://test.n8n.com/webhook/webhook1",
            "https://test.n8n.com/webhook/webhook2"
        ]
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_workflow_status_success(self, n8n_service):
        """Test successful workflow status retrieval."""
        workflow_data = {
            "id": "workflow-123",
            "name": "Test Workflow",
            "active": True,
            "nodes": [
                {
                    "type": "n8n-nodes-base.webhook",
                    "parameters": {"path": "test-webhook"}
                }
            ],
            "updatedAt": "2025-01-01T00:00:00Z",
            "createdAt": "2025-01-01T00:00:00Z"
        }

        executions_data = {
            "data": [
                {"id": "exec-1", "status": "success"},
                {"id": "exec-2", "status": "running"}
            ]
        }

        mock_workflow_response = MagicMock()
        mock_workflow_response.status_code = 200
        mock_workflow_response.json.return_value = workflow_data

        mock_executions_response = MagicMock()
        mock_executions_response.status_code = 200
        mock_executions_response.json.return_value = executions_data

        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = mock_client.return_value.__aenter__.return_value
            mock_client_instance.get = AsyncMock(side_effect=[mock_workflow_response, mock_executions_response])

            result = await n8n_service.get_workflow_status("workflow-123")

            assert result["id"] == "workflow-123"
            assert result["name"] == "Test Workflow"
            assert result["active"] is True
            assert len(result["webhooks"]) == 1
            assert len(result["recent_executions"]) == 2

    @pytest.mark.asyncio
    async def test_network_error_handling(self, n8n_service):
        """Test handling of network errors."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.RequestError("Network error")
            )

            result = await n8n_service.get_template_from_repository(6213)

            assert result is None