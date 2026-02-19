"""n8n Workflow Integration Service."""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx
from pydantic import BaseModel, Field

from ..models import Campaign, CampaignCreate

logger = logging.getLogger(__name__)


class N8nWorkflowConfig(BaseModel):
    """n8n workflow configuration model."""

    template_id: Optional[int] = Field(default=None, description="n8n template ID")
    workflow_id: Optional[str] = Field(default=None, description="Created workflow ID")
    workflow_name: str = Field(..., description="Workflow name")
    enabled: bool = Field(default=False, description="Whether workflow is enabled")
    webhook_urls: List[str] = Field(default_factory=list, description="Webhook URLs for triggers")
    endpoints: List[str] = Field(default_factory=list, description="Available endpoints")


class N8nWorkflowService:
    """Service for managing n8n workflow integrations."""

    def __init__(self, n8n_api_url: str, n8n_api_key: str):
        """Initialize the n8n workflow service.

        Args:
            n8n_api_url: n8n instance API URL
            n8n_api_key: n8n API key for authentication
        """
        self.n8n_api_url = n8n_api_url.rstrip('/')
        self.n8n_api_key = n8n_api_key
        self.headers = {
            'X-N8N-API-KEY': n8n_api_key,
            'Content-Type': 'application/json'
        }

    async def get_template_from_repository(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Fetch template from n8n repository via MCP.

        Args:
            template_id: Template ID from n8n repository

        Returns:
            Template data or None if not found
        """
        try:
            async with httpx.AsyncClient() as client:
                # Use MCP server to get template
                response = await client.post(
                    f"{self.n8n_api_url}/mcp/get_template",
                    json={
                        "templateId": template_id,
                        "mode": "full"
                    },
                    headers=self.headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get('template')

                logger.error(f"Failed to fetch template {template_id}: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching template {template_id}: {e}")
            return None

    async def create_workflow_from_template(
        self,
        template_id: int,
        campaign: Campaign
    ) -> Optional[str]:
        """Create a workflow from an n8n template.

        Args:
            template_id: Template ID from n8n repository
            campaign: Campaign object for customization

        Returns:
            Created workflow ID or None if failed
        """
        try:
            # Get template from repository
            template = await self.get_template_from_repository(template_id)
            if not template:
                logger.error(f"Template {template_id} not found")
                return None

            # Customize workflow for the campaign
            workflow_data = self._customize_workflow_for_campaign(template, campaign)

            # Create workflow in n8n instance
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.n8n_api_url}/api/v1/workflows",
                    json=workflow_data,
                    headers=self.headers,
                    timeout=60.0
                )

                if response.status_code == 201:
                    workflow = response.json()
                    logger.info(f"Created workflow {workflow['id']} for campaign {campaign.id}")
                    return workflow['id']

                logger.error(f"Failed to create workflow: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error creating workflow from template {template_id}: {e}")
            return None

    async def activate_workflow(self, workflow_id: str) -> bool:
        """Activate a workflow.

        Args:
            workflow_id: Workflow ID to activate

        Returns:
            True if activated successfully
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.n8n_api_url}/api/v1/workflows/{workflow_id}/activate",
                    headers=self.headers,
                    timeout=30.0
                )

                return response.status_code == 200

        except Exception as e:
            logger.error(f"Error activating workflow {workflow_id}: {e}")
            return False

    async def deactivate_workflow(self, workflow_id: str) -> bool:
        """Deactivate a workflow.

        Args:
            workflow_id: Workflow ID to deactivate

        Returns:
            True if deactivated successfully
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.n8n_api_url}/api/v1/workflows/{workflow_id}/deactivate",
                    headers=self.headers,
                    timeout=30.0
                )

                return response.status_code == 200

        except Exception as e:
            logger.error(f"Error deactivating workflow {workflow_id}: {e}")
            return False

    async def get_workflow_webhooks(self, workflow_id: str) -> List[str]:
        """Get webhook URLs for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            List of webhook URLs
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.n8n_api_url}/api/v1/workflows/{workflow_id}",
                    headers=self.headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    workflow = response.json()
                    return self._extract_webhook_urls(workflow)

                return []

        except Exception as e:
            logger.error(f"Error getting workflow webhooks {workflow_id}: {e}")
            return []

    async def trigger_workflow(
        self,
        workflow_id: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Trigger a workflow execution.

        Args:
            workflow_id: Workflow ID to trigger
            data: Data to pass to the workflow

        Returns:
            Execution result or None if failed
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.n8n_api_url}/api/v1/workflows/{workflow_id}/execute",
                    json=data,
                    headers=self.headers,
                    timeout=120.0
                )

                if response.status_code == 200:
                    return response.json()

                logger.error(f"Failed to trigger workflow {workflow_id}: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error triggering workflow {workflow_id}: {e}")
            return None

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow.

        Args:
            workflow_id: Workflow ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.n8n_api_url}/api/v1/workflows/{workflow_id}",
                    headers=self.headers,
                    timeout=30.0
                )

                return response.status_code == 200

        except Exception as e:
            logger.error(f"Error deleting workflow {workflow_id}: {e}")
            return False

    def _customize_workflow_for_campaign(
        self,
        template: Dict[str, Any],
        campaign: Campaign
    ) -> Dict[str, Any]:
        """Customize workflow template for specific campaign.

        Args:
            template: Template data from repository
            campaign: Campaign object

        Returns:
            Customized workflow data
        """
        workflow_name = f"{template.get('name', 'Campaign Workflow')} - {campaign.name}"

        # Base workflow structure
        workflow_data = {
            "name": workflow_name,
            "nodes": template.get("nodes", []),
            "connections": template.get("connections", {}),
            "active": False,  # Start inactive
            "settings": {
                "executionOrder": "v1",
                "saveDataErrorExecution": "all",
                "saveDataSuccessExecution": "all",
                "saveManualExecutions": True,
                "saveExecutionProgress": True
            },
            "tags": [
                {"name": f"campaign-{campaign.id}"},
                {"name": f"template-{template.get('id', '')}"},
                {"name": campaign.category or "general"}
            ]
        }

        # Customize nodes with campaign-specific data
        for node in workflow_data["nodes"]:
            if node.get("type") == "n8n-nodes-base.googleSheets":
                # Update Google Sheets nodes with campaign data
                if "parameters" not in node:
                    node["parameters"] = {}
                node["parameters"]["campaignId"] = str(campaign.id)
                node["parameters"]["campaignName"] = campaign.name

            elif node.get("type") == "n8n-nodes-base.webhook":
                # Update webhook nodes with campaign-specific paths
                if "parameters" not in node:
                    node["parameters"] = {}
                node["parameters"]["path"] = f"campaign-{campaign.id}-webhook"

            elif node.get("type") in ["n8n-nodes-base.twilio", "n8n-nodes-base.emailSend"]:
                # Update messaging nodes with campaign context
                if "parameters" not in node:
                    node["parameters"] = {}
                node["parameters"]["campaignContext"] = {
                    "id": str(campaign.id),
                    "name": campaign.name,
                    "category": campaign.category
                }

        return workflow_data

    def _extract_webhook_urls(self, workflow: Dict[str, Any]) -> List[str]:
        """Extract webhook URLs from workflow definition.

        Args:
            workflow: Workflow data

        Returns:
            List of webhook URLs
        """
        webhooks = []
        base_url = self.n8n_api_url.replace('/api/v1', '')

        for node in workflow.get("nodes", []):
            if node.get("type") == "n8n-nodes-base.webhook":
                path = node.get("parameters", {}).get("path", "")
                if path:
                    webhook_url = f"{base_url}/webhook/{path}"
                    webhooks.append(webhook_url)

        return webhooks

    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status and execution history.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow status data
        """
        try:
            async with httpx.AsyncClient() as client:
                # Get workflow details
                workflow_response = await client.get(
                    f"{self.n8n_api_url}/api/v1/workflows/{workflow_id}",
                    headers=self.headers,
                    timeout=30.0
                )

                if workflow_response.status_code != 200:
                    return None

                workflow = workflow_response.json()

                # Get recent executions
                executions_response = await client.get(
                    f"{self.n8n_api_url}/api/v1/executions",
                    params={"workflowId": workflow_id, "limit": 10},
                    headers=self.headers,
                    timeout=30.0
                )

                executions = []
                if executions_response.status_code == 200:
                    executions = executions_response.json().get("data", [])

                return {
                    "id": workflow["id"],
                    "name": workflow["name"],
                    "active": workflow["active"],
                    "webhooks": self._extract_webhook_urls(workflow),
                    "recent_executions": executions,
                    "updated_at": workflow.get("updatedAt"),
                    "created_at": workflow.get("createdAt")
                }

        except Exception as e:
            logger.error(f"Error getting workflow status {workflow_id}: {e}")
            return None