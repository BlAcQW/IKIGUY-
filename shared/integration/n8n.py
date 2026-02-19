"""
n8n Integration Module

This module provides integration with n8n for workflow automation,
orchestration, and process management.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    import requests
    N8N_AVAILABLE = True
except ImportError:
    N8N_AVAILABLE = False
    logging.warning("n8n APIs not available. Install requests")

logger = logging.getLogger(__name__)


class N8NWorkflowStatus(Enum):
    """n8n workflow status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    RUNNING = "running"
    STOPPED = "stopped"


class N8NExecutionStatus(Enum):
    """n8n execution status."""
    SUCCESS = "success"
    ERROR = "error"
    RUNNING = "running"
    WAITING = "waiting"
    CANCELED = "canceled"


@dataclass
class N8NConfig:
    """Configuration for n8n integration."""
    
    base_url: str
    """n8n base URL."""
    
    api_key: Optional[str] = None
    """n8n API key."""
    
    username: Optional[str] = None
    """n8n username."""
    
    password: Optional[str] = None
    """n8n password."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""
    
    max_retries: int = 3
    """Maximum retry attempts."""


@dataclass
class N8NWorkflow:
    """n8n workflow data structure."""
    
    id: str
    """Workflow ID."""
    
    name: str
    """Workflow name."""
    
    active: bool
    """Whether workflow is active."""
    
    nodes: List[Dict[str, Any]]
    """Workflow nodes."""
    
    connections: Dict[str, Any]
    """Node connections."""
    
    settings: Dict[str, Any]
    """Workflow settings."""
    
    static_data: Optional[Dict[str, Any]] = None
    """Static data."""
    
    tags: List[str] = field(default_factory=list)
    """Workflow tags."""
    
    version_id: Optional[str] = None
    """Version ID."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class N8NExecution:
    """n8n execution data structure."""
    
    id: str
    """Execution ID."""
    
    workflow_id: str
    """Workflow ID."""
    
    status: N8NExecutionStatus
    """Execution status."""
    
    data: List[Dict[str, Any]]
    """Execution data."""
    
    finished: bool = False
    """Whether execution is finished."""
    
    mode: str = "manual"
    """Execution mode."""
    
    started_at: Optional[datetime] = None
    """Start timestamp."""
    
    stopped_at: Optional[datetime] = None
    """Stop timestamp."""
    
    retry_of: Optional[str] = None
    """Retry of execution ID."""
    
    wait_till: Optional[datetime] = None
    """Wait until timestamp."""


@dataclass
class N8NWebhook:
    """n8n webhook data structure."""
    
    path: str
    """Webhook path."""
    
    http_method: str
    """HTTP method."""
    
    node: str
    """Node name."""
    
    workflow_id: str
    """Workflow ID."""
    
    authentication: Optional[str] = None
    """Authentication method."""
    
    response_mode: str = "responseNode"
    """Response mode."""


class N8NIntegration:
    """n8n integration for workflow automation and orchestration."""
    
    def __init__(self, config: N8NConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        
        # Set up authentication
        if config.api_key:
            self.session.headers.update({
                "X-N8N-API-KEY": config.api_key
            })
        elif config.username and config.password:
            self.session.auth = (config.username, config.password)
    
    async def get_workflows(self) -> List[N8NWorkflow]:
        """
        Get all workflows.
        
        Returns:
            List of workflows
        """
        try:
            url = f"{self.config.base_url}/api/v1/workflows"
            response = self.session.get(url)
            response.raise_for_status()

            workflows_data = response.json()

            # Handle n8n API response format: {"data": [...]}
            if isinstance(workflows_data, dict) and 'data' in workflows_data:
                workflows_data = workflows_data['data']

            workflows = []

            for workflow_data in workflows_data:
                workflow = N8NWorkflow(
                    id=workflow_data["id"],
                    name=workflow_data["name"],
                    active=workflow_data.get("active", False),
                    nodes=workflow_data.get("nodes", []),
                    connections=workflow_data.get("connections", {}),
                    settings=workflow_data.get("settings", {}),
                    static_data=workflow_data.get("staticData"),
                    tags=workflow_data.get("tags", []),
                    version_id=workflow_data.get("versionId"),
                    created_at=datetime.fromisoformat(workflow_data["createdAt"].replace("Z", "+00:00")) if workflow_data.get("createdAt") else None,
                    updated_at=datetime.fromisoformat(workflow_data["updatedAt"].replace("Z", "+00:00")) if workflow_data.get("updatedAt") else None
                )
                workflows.append(workflow)
            
            return workflows
            
        except Exception as e:
            self.logger.error(f"Failed to get workflows: {e}")
            raise
    
    async def get_workflow(self, workflow_id: str) -> N8NWorkflow:
        """
        Get a specific workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow data
        """
        try:
            url = f"{self.config.base_url}/api/v1/workflows/{workflow_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            workflow_data = response.json()
            
            return N8NWorkflow(
                id=workflow_data["id"],
                name=workflow_data["name"],
                active=workflow_data.get("active", False),
                nodes=workflow_data.get("nodes", []),
                connections=workflow_data.get("connections", {}),
                settings=workflow_data.get("settings", {}),
                static_data=workflow_data.get("staticData"),
                tags=workflow_data.get("tags", []),
                version_id=workflow_data.get("versionId"),
                created_at=datetime.fromisoformat(workflow_data["createdAt"].replace("Z", "+00:00")) if workflow_data.get("createdAt") else None,
                updated_at=datetime.fromisoformat(workflow_data["updatedAt"].replace("Z", "+00:00")) if workflow_data.get("updatedAt") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get workflow: {e}")
            raise
    
    async def create_workflow(
        self,
        name: str,
        nodes: List[Dict[str, Any]],
        connections: Dict[str, Any],
        settings: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> N8NWorkflow:
        """
        Create a new workflow.
        
        Args:
            name: Workflow name
            nodes: Workflow nodes
            connections: Node connections
            settings: Workflow settings
            tags: Workflow tags
            
        Returns:
            Created workflow
        """
        try:
            url = f"{self.config.base_url}/api/v1/workflows"
            
            data = {
                "name": name,
                "nodes": nodes,
                "connections": connections
            }
            
            if settings:
                data["settings"] = settings
            if tags:
                data["tags"] = tags
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            workflow_data = response.json()
            
            return N8NWorkflow(
                id=workflow_data["id"],
                name=workflow_data["name"],
                active=workflow_data.get("active", False),
                nodes=workflow_data.get("nodes", []),
                connections=workflow_data.get("connections", {}),
                settings=workflow_data.get("settings", {}),
                static_data=workflow_data.get("staticData"),
                tags=workflow_data.get("tags", []),
                version_id=workflow_data.get("versionId"),
                created_at=datetime.fromisoformat(workflow_data["createdAt"].replace("Z", "+00:00")) if workflow_data.get("createdAt") else None,
                updated_at=datetime.fromisoformat(workflow_data["updatedAt"].replace("Z", "+00:00")) if workflow_data.get("updatedAt") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create workflow: {e}")
            raise
    
    async def update_workflow(
        self,
        workflow_id: str,
        name: Optional[str] = None,
        nodes: Optional[List[Dict[str, Any]]] = None,
        connections: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> N8NWorkflow:
        """
        Update a workflow.
        
        Args:
            workflow_id: Workflow ID
            name: New workflow name
            nodes: New workflow nodes
            connections: New node connections
            settings: New workflow settings
            tags: New workflow tags
            
        Returns:
            Updated workflow
        """
        try:
            url = f"{self.config.base_url}/api/v1/workflows/{workflow_id}"
            
            data = {}
            if name:
                data["name"] = name
            if nodes:
                data["nodes"] = nodes
            if connections:
                data["connections"] = connections
            if settings:
                data["settings"] = settings
            if tags:
                data["tags"] = tags
            
            response = self.session.put(url, json=data)
            response.raise_for_status()
            
            workflow_data = response.json()
            
            return N8NWorkflow(
                id=workflow_data["id"],
                name=workflow_data["name"],
                active=workflow_data.get("active", False),
                nodes=workflow_data.get("nodes", []),
                connections=workflow_data.get("connections", {}),
                settings=workflow_data.get("settings", {}),
                static_data=workflow_data.get("staticData"),
                tags=workflow_data.get("tags", []),
                version_id=workflow_data.get("versionId"),
                created_at=datetime.fromisoformat(workflow_data["createdAt"].replace("Z", "+00:00")) if workflow_data.get("createdAt") else None,
                updated_at=datetime.fromisoformat(workflow_data["updatedAt"].replace("Z", "+00:00")) if workflow_data.get("updatedAt") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update workflow: {e}")
            raise
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.config.base_url}/api/v1/workflows/{workflow_id}"
            response = self.session.delete(url)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete workflow: {e}")
            return False
    
    async def activate_workflow(self, workflow_id: str) -> bool:
        """
        Activate a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.config.base_url}/api/v1/workflows/{workflow_id}/activate"
            response = self.session.post(url)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to activate workflow: {e}")
            return False
    
    async def deactivate_workflow(self, workflow_id: str) -> bool:
        """
        Deactivate a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.config.base_url}/api/v1/workflows/{workflow_id}/deactivate"
            response = self.session.post(url)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deactivate workflow: {e}")
            return False
    
    async def trigger_workflow(
        self,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> N8NExecution:
        """
        Trigger a workflow.
        
        Args:
            workflow_id: Workflow ID
            data: Input data
            
        Returns:
            Execution data
        """
        try:
            url = f"{self.config.base_url}/api/v1/workflows/{workflow_id}/trigger"
            
            payload = {}
            if data:
                payload["data"] = data
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            execution_data = response.json()
            
            return N8NExecution(
                id=execution_data["id"],
                workflow_id=execution_data["workflowId"],
                status=N8NExecutionStatus(execution_data["status"]),
                data=execution_data.get("data", []),
                started_at=datetime.fromisoformat(execution_data["startedAt"].replace("Z", "+00:00")) if execution_data.get("startedAt") else None,
                stopped_at=datetime.fromisoformat(execution_data["stoppedAt"].replace("Z", "+00:00")) if execution_data.get("stoppedAt") else None,
                finished=execution_data.get("finished", False),
                mode=execution_data.get("mode", "manual"),
                retry_of=execution_data.get("retryOf"),
                wait_till=datetime.fromisoformat(execution_data["waitTill"].replace("Z", "+00:00")) if execution_data.get("waitTill") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to trigger workflow: {e}")
            raise
    
    async def get_executions(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 50,
        status: Optional[N8NExecutionStatus] = None
    ) -> List[N8NExecution]:
        """
        Get executions.
        
        Args:
            workflow_id: Filter by workflow ID
            limit: Number of executions to return
            status: Filter by execution status
            
        Returns:
            List of executions
        """
        try:
            url = f"{self.config.base_url}/api/v1/executions"
            
            params = {"limit": limit}
            if workflow_id:
                params["workflowId"] = workflow_id
            if status:
                params["status"] = status.value
            
            response = self.session.get(url, params=params)
            response.raise_for_status()

            executions_data = response.json()

            # Handle n8n API response format: {"data": [...]}
            if isinstance(executions_data, dict) and 'data' in executions_data:
                executions_data = executions_data['data']

            executions = []

            for execution_data in executions_data:
                execution = N8NExecution(
                    id=execution_data["id"],
                    workflow_id=execution_data["workflowId"],
                    status=N8NExecutionStatus(execution_data["status"]),
                    data=execution_data.get("data", []),
                    started_at=datetime.fromisoformat(execution_data["startedAt"].replace("Z", "+00:00")) if execution_data.get("startedAt") else None,
                    stopped_at=datetime.fromisoformat(execution_data["stoppedAt"].replace("Z", "+00:00")) if execution_data.get("stoppedAt") else None,
                    finished=execution_data.get("finished", False),
                    mode=execution_data.get("mode", "manual"),
                    retry_of=execution_data.get("retryOf"),
                    wait_till=datetime.fromisoformat(execution_data["waitTill"].replace("Z", "+00:00")) if execution_data.get("waitTill") else None
                )
                executions.append(execution)
            
            return executions
            
        except Exception as e:
            self.logger.error(f"Failed to get executions: {e}")
            raise
    
    async def get_execution(self, execution_id: str) -> N8NExecution:
        """
        Get a specific execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Execution data
        """
        try:
            url = f"{self.config.base_url}/api/v1/executions/{execution_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            execution_data = response.json()
            
            return N8NExecution(
                id=execution_data["id"],
                workflow_id=execution_data["workflowId"],
                status=N8NExecutionStatus(execution_data["status"]),
                data=execution_data.get("data", []),
                started_at=datetime.fromisoformat(execution_data["startedAt"].replace("Z", "+00:00")) if execution_data.get("startedAt") else None,
                stopped_at=datetime.fromisoformat(execution_data["stoppedAt"].replace("Z", "+00:00")) if execution_data.get("stoppedAt") else None,
                finished=execution_data.get("finished", False),
                mode=execution_data.get("mode", "manual"),
                retry_of=execution_data.get("retryOf"),
                wait_till=datetime.fromisoformat(execution_data["waitTill"].replace("Z", "+00:00")) if execution_data.get("waitTill") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get execution: {e}")
            raise
    
    async def delete_execution(self, execution_id: str) -> bool:
        """
        Delete an execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.config.base_url}/api/v1/executions/{execution_id}"
            response = self.session.delete(url)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete execution: {e}")
            return False
    
    async def get_webhooks(self) -> List[N8NWebhook]:
        """
        Get all webhooks.
        
        Returns:
            List of webhooks
        """
        try:
            url = f"{self.config.base_url}/api/v1/webhooks"
            response = self.session.get(url)
            response.raise_for_status()

            webhooks_data = response.json()

            # Handle n8n API response format: {"data": [...]}
            if isinstance(webhooks_data, dict) and 'data' in webhooks_data:
                webhooks_data = webhooks_data['data']

            webhooks = []

            for webhook_data in webhooks_data:
                webhook = N8NWebhook(
                    path=webhook_data["path"],
                    http_method=webhook_data["httpMethod"],
                    node=webhook_data["node"],
                    workflow_id=webhook_data["workflowId"],
                    authentication=webhook_data.get("authentication"),
                    response_mode=webhook_data.get("responseMode", "responseNode")
                )
                webhooks.append(webhook)
            
            return webhooks
            
        except Exception as e:
            self.logger.error(f"Failed to get webhooks: {e}")
            raise
    
    async def create_webhook(
        self,
        path: str,
        http_method: str,
        node: str,
        workflow_id: str,
        authentication: Optional[str] = None,
        response_mode: str = "responseNode"
    ) -> N8NWebhook:
        """
        Create a webhook.
        
        Args:
            path: Webhook path
            http_method: HTTP method
            node: Node name
            workflow_id: Workflow ID
            authentication: Authentication method
            response_mode: Response mode
            
        Returns:
            Created webhook
        """
        try:
            url = f"{self.config.base_url}/api/v1/webhooks"
            
            data = {
                "path": path,
                "httpMethod": http_method,
                "node": node,
                "workflowId": workflow_id,
                "responseMode": response_mode
            }
            
            if authentication:
                data["authentication"] = authentication
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            webhook_data = response.json()
            
            return N8NWebhook(
                path=webhook_data["path"],
                http_method=webhook_data["httpMethod"],
                node=webhook_data["node"],
                workflow_id=webhook_data["workflowId"],
                authentication=webhook_data.get("authentication"),
                response_mode=webhook_data.get("responseMode", "responseNode")
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create webhook: {e}")
            raise
    
    async def delete_webhook(self, webhook_path: str) -> bool:
        """
        Delete a webhook.
        
        Args:
            webhook_path: Webhook path
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.config.base_url}/api/v1/webhooks/{webhook_path}"
            response = self.session.delete(url)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete webhook: {e}")
            return False
    
    async def get_health(self) -> Dict[str, Any]:
        """
        Get n8n health status.
        
        Returns:
            Health status
        """
        try:
            url = f"{self.config.base_url}/healthz"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get health status: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the n8n integration.
        
        Returns:
            Health check results
        """
        try:
            # Test basic connectivity
            health_status = await self.get_health()
            
            # Test workflow listing
            workflows = await self.get_workflows()
            
            return {
                "status": "healthy",
                "base_url": self.config.base_url,
                "health_status": health_status,
                "workflows_count": len(workflows),
                "api_connectivity": "successful",
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }

