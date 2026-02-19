"""
Zapier Integration Module

This module provides integration with Zapier for workflow automation,
app connectivity, and trigger management.
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
    ZAPIER_AVAILABLE = True
except ImportError:
    ZAPIER_AVAILABLE = False
    logging.warning("Zapier APIs not available. Install requests")

logger = logging.getLogger(__name__)


class ZapStatus(Enum):
    """Zap status values."""
    ON = "on"
    OFF = "off"
    DRAFT = "draft"


class ZapTriggerType(Enum):
    """Zap trigger types."""
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    FORM = "form"
    APP = "app"


@dataclass
class ZapierConfig:
    """Configuration for Zapier integration."""
    
    api_key: str
    """Zapier API key for authentication."""
    
    base_url: str = "https://api.zapier.com/v1"
    """Zapier API base URL."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Whether to verify SSL certificates."""


@dataclass
class Zap:
    """Zap workflow data structure."""
    
    id: str
    """Zap ID."""
    
    title: str
    """Zap title."""
    
    status: ZapStatus
    """Zap status."""
    
    trigger_type: ZapTriggerType
    """Trigger type."""
    
    trigger_app: str
    """Trigger app name."""
    
    action_app: str
    """Action app name."""
    
    created_at: datetime
    """When zap was created."""
    
    updated_at: datetime
    """When zap was last updated."""
    
    description: Optional[str] = None
    """Zap description."""
    
    last_run: Optional[datetime] = None
    """When zap was last run."""
    
    run_count: int = 0
    """Number of times zap has run."""
    
    is_public: bool = False
    """Whether zap is public."""
    
    url: Optional[str] = None
    """Zap URL."""
    
    webhook_url: Optional[str] = None
    """Webhook URL if trigger type is webhook."""


@dataclass
class ZapTask:
    """Zap task execution data structure."""
    
    id: str
    """Task ID."""
    
    zap_id: str
    """Zap ID."""
    
    status: str
    """Task status."""
    
    started_at: datetime
    """When task started."""
    
    finished_at: Optional[datetime] = None
    """When task finished."""
    
    duration_ms: Optional[int] = None
    """Task duration in milliseconds."""
    
    input_data: Dict[str, Any] = field(default_factory=dict)
    """Input data for the task."""
    
    output_data: Dict[str, Any] = field(default_factory=dict)
    """Output data from the task."""
    
    error_message: Optional[str] = None
    """Error message if task failed."""
    
    retry_count: int = 0
    """Number of retries attempted."""


@dataclass
class WebhookPayload:
    """Webhook payload data structure."""
    
    zap_id: str
    """Zap ID."""
    
    trigger_id: str
    """Trigger ID."""
    
    data: Dict[str, Any]
    """Payload data."""
    
    headers: Dict[str, str] = field(default_factory=dict)
    """Request headers."""
    
    method: str = "POST"
    """HTTP method."""
    
    timestamp: datetime = field(default_factory=datetime.now)
    """When payload was received."""


@dataclass
class ZapTemplate:
    """Zap template data structure."""
    
    id: str
    """Template ID."""
    
    title: str
    """Template title."""
    
    description: str
    """Template description."""
    
    category: str
    """Template category."""
    
    trigger_app: str
    """Trigger app."""
    
    action_app: str
    """Action app."""
    
    created_at: datetime
    """When template was created."""
    
    is_popular: bool = False
    """Whether template is popular."""
    
    usage_count: int = 0
    """Number of times template has been used."""
    
    url: Optional[str] = None
    """Template URL."""


class ZapierIntegration:
    """Zapier integration for workflow automation and app connectivity."""
    
    def __init__(self, config: ZapierConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        })
        self.session.verify = config.verify_ssl
        self.session.timeout = config.timeout
    
    async def get_zaps(self, status: Optional[ZapStatus] = None) -> List[Zap]:
        """
        Get all zaps.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of zaps
        """
        try:
            url = f"{self.config.base_url}/zaps"
            params = {}
            
            if status:
                params["status"] = status.value
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            zaps = []
            for item in response.json():
                zap = Zap(
                    id=item["id"],
                    title=item["title"],
                    description=item.get("description"),
                    status=ZapStatus(item["status"]),
                    trigger_type=ZapTriggerType(item.get("trigger_type", "app")),
                    trigger_app=item.get("trigger_app", ""),
                    action_app=item.get("action_app", ""),
                    created_at=datetime.fromisoformat(item["created_at"]),
                    updated_at=datetime.fromisoformat(item["updated_at"]),
                    last_run=datetime.fromisoformat(item["last_run"]) if item.get("last_run") else None,
                    run_count=item.get("run_count", 0),
                    is_public=item.get("is_public", False),
                    url=item.get("url"),
                    webhook_url=item.get("webhook_url")
                )
                zaps.append(zap)
            
            return zaps
            
        except Exception as e:
            self.logger.error(f"Failed to get zaps: {e}")
            raise
    
    async def get_zap(self, zap_id: str) -> Zap:
        """
        Get a specific zap by ID.
        
        Args:
            zap_id: Zap ID
            
        Returns:
            Zap details
        """
        try:
            url = f"{self.config.base_url}/zaps/{zap_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            item = response.json()
            zap = Zap(
                id=item["id"],
                title=item["title"],
                description=item.get("description"),
                status=ZapStatus(item["status"]),
                trigger_type=ZapTriggerType(item.get("trigger_type", "app")),
                trigger_app=item.get("trigger_app", ""),
                action_app=item.get("action_app", ""),
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"]),
                last_run=datetime.fromisoformat(item["last_run"]) if item.get("last_run") else None,
                run_count=item.get("run_count", 0),
                is_public=item.get("is_public", False),
                url=item.get("url"),
                webhook_url=item.get("webhook_url")
            )
            
            return zap
            
        except Exception as e:
            self.logger.error(f"Failed to get zap {zap_id}: {e}")
            raise
    
    async def create_zap(self, zap_data: Dict[str, Any]) -> Zap:
        """
        Create a new zap.
        
        Args:
            zap_data: Zap configuration data
            
        Returns:
            Created zap
        """
        try:
            url = f"{self.config.base_url}/zaps"
            response = self.session.post(url, json=zap_data)
            response.raise_for_status()
            
            item = response.json()
            zap = Zap(
                id=item["id"],
                title=item["title"],
                description=item.get("description"),
                status=ZapStatus(item["status"]),
                trigger_type=ZapTriggerType(item.get("trigger_type", "app")),
                trigger_app=item.get("trigger_app", ""),
                action_app=item.get("action_app", ""),
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"]),
                last_run=datetime.fromisoformat(item["last_run"]) if item.get("last_run") else None,
                run_count=item.get("run_count", 0),
                is_public=item.get("is_public", False),
                url=item.get("url"),
                webhook_url=item.get("webhook_url")
            )
            
            return zap
            
        except Exception as e:
            self.logger.error(f"Failed to create zap: {e}")
            raise
    
    async def update_zap(self, zap_id: str, updates: Dict[str, Any]) -> Zap:
        """
        Update an existing zap.
        
        Args:
            zap_id: Zap ID
            updates: Updates to apply
            
        Returns:
            Updated zap
        """
        try:
            url = f"{self.config.base_url}/zaps/{zap_id}"
            response = self.session.patch(url, json=updates)
            response.raise_for_status()
            
            item = response.json()
            zap = Zap(
                id=item["id"],
                title=item["title"],
                description=item.get("description"),
                status=ZapStatus(item["status"]),
                trigger_type=ZapTriggerType(item.get("trigger_type", "app")),
                trigger_app=item.get("trigger_app", ""),
                action_app=item.get("action_app", ""),
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"]),
                last_run=datetime.fromisoformat(item["last_run"]) if item.get("last_run") else None,
                run_count=item.get("run_count", 0),
                is_public=item.get("is_public", False),
                url=item.get("url"),
                webhook_url=item.get("webhook_url")
            )
            
            return zap
            
        except Exception as e:
            self.logger.error(f"Failed to update zap {zap_id}: {e}")
            raise
    
    async def delete_zap(self, zap_id: str) -> bool:
        """
        Delete a zap.
        
        Args:
            zap_id: Zap ID
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.config.base_url}/zaps/{zap_id}"
            response = self.session.delete(url)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete zap {zap_id}: {e}")
            raise
    
    async def turn_zap_on(self, zap_id: str) -> bool:
        """
        Turn a zap on.
        
        Args:
            zap_id: Zap ID
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.config.base_url}/zaps/{zap_id}/on"
            response = self.session.post(url)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to turn zap {zap_id} on: {e}")
            raise
    
    async def turn_zap_off(self, zap_id: str) -> bool:
        """
        Turn a zap off.
        
        Args:
            zap_id: Zap ID
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.config.base_url}/zaps/{zap_id}/off"
            response = self.session.post(url)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to turn zap {zap_id} off: {e}")
            raise
    
    async def get_zap_tasks(
        self,
        zap_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[ZapTask]:
        """
        Get tasks for a specific zap.
        
        Args:
            zap_id: Zap ID
            limit: Number of tasks to return
            offset: Number of tasks to skip
            
        Returns:
            List of zap tasks
        """
        try:
            url = f"{self.config.base_url}/zaps/{zap_id}/tasks"
            params = {"limit": limit, "offset": offset}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            tasks = []
            for item in response.json():
                task = ZapTask(
                    id=item["id"],
                    zap_id=item["zap_id"],
                    status=item["status"],
                    started_at=datetime.fromisoformat(item["started_at"]),
                    finished_at=datetime.fromisoformat(item["finished_at"]) if item.get("finished_at") else None,
                    duration_ms=item.get("duration_ms"),
                    input_data=item.get("input_data", {}),
                    output_data=item.get("output_data", {}),
                    error_message=item.get("error_message"),
                    retry_count=item.get("retry_count", 0)
                )
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            self.logger.error(f"Failed to get tasks for zap {zap_id}: {e}")
            raise
    
    async def get_task(self, task_id: str) -> ZapTask:
        """
        Get a specific task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task details
        """
        try:
            url = f"{self.config.base_url}/tasks/{task_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            item = response.json()
            task = ZapTask(
                id=item["id"],
                zap_id=item["zap_id"],
                status=item["status"],
                started_at=datetime.fromisoformat(item["started_at"]),
                finished_at=datetime.fromisoformat(item["finished_at"]) if item.get("finished_at") else None,
                duration_ms=item.get("duration_ms"),
                input_data=item.get("input_data", {}),
                output_data=item.get("output_data", {}),
                error_message=item.get("error_message"),
                retry_count=item.get("retry_count", 0)
            )
            
            return task
            
        except Exception as e:
            self.logger.error(f"Failed to get task {task_id}: {e}")
            raise
    
    async def retry_task(self, task_id: str) -> ZapTask:
        """
        Retry a failed task.
        
        Args:
            task_id: Task ID
            
        Returns:
            New task created for retry
        """
        try:
            url = f"{self.config.base_url}/tasks/{task_id}/retry"
            response = self.session.post(url)
            response.raise_for_status()
            
            item = response.json()
            task = ZapTask(
                id=item["id"],
                zap_id=item["zap_id"],
                status=item["status"],
                started_at=datetime.fromisoformat(item["started_at"]),
                finished_at=datetime.fromisoformat(item["finished_at"]) if item.get("finished_at") else None,
                duration_ms=item.get("duration_ms"),
                input_data=item.get("input_data", {}),
                output_data=item.get("output_data", {}),
                error_message=item.get("error_message"),
                retry_count=item.get("retry_count", 0)
            )
            
            return task
            
        except Exception as e:
            self.logger.error(f"Failed to retry task {task_id}: {e}")
            raise
    
    async def trigger_webhook(self, webhook_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger a webhook zap.
        
        Args:
            webhook_url: Webhook URL
            payload: Payload to send
            
        Returns:
            Webhook response
        """
        try:
            response = self.session.post(webhook_url, json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to trigger webhook: {e}")
            raise
    
    async def get_zap_templates(
        self,
        category: Optional[str] = None,
        app: Optional[str] = None,
        limit: int = 50
    ) -> List[ZapTemplate]:
        """
        Get zap templates.
        
        Args:
            category: Optional category filter
            app: Optional app filter
            limit: Number of templates to return
            
        Returns:
            List of zap templates
        """
        try:
            url = f"{self.config.base_url}/templates"
            params = {"limit": limit}
            
            if category:
                params["category"] = category
            if app:
                params["app"] = app
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            templates = []
            for item in response.json():
                template = ZapTemplate(
                    id=item["id"],
                    title=item["title"],
                    description=item["description"],
                    category=item["category"],
                    trigger_app=item["trigger_app"],
                    action_app=item["action_app"],
                    is_popular=item.get("is_popular", False),
                    usage_count=item.get("usage_count", 0),
                    created_at=datetime.fromisoformat(item["created_at"]),
                    url=item.get("url")
                )
                templates.append(template)
            
            return templates
            
        except Exception as e:
            self.logger.error(f"Failed to get zap templates: {e}")
            raise
    
    async def create_zap_from_template(self, template_id: str, zap_data: Dict[str, Any]) -> Zap:
        """
        Create a zap from a template.
        
        Args:
            template_id: Template ID
            zap_data: Additional zap configuration
            
        Returns:
            Created zap
        """
        try:
            url = f"{self.config.base_url}/templates/{template_id}/zaps"
            response = self.session.post(url, json=zap_data)
            response.raise_for_status()
            
            item = response.json()
            zap = Zap(
                id=item["id"],
                title=item["title"],
                description=item.get("description"),
                status=ZapStatus(item["status"]),
                trigger_type=ZapTriggerType(item.get("trigger_type", "app")),
                trigger_app=item.get("trigger_app", ""),
                action_app=item.get("action_app", ""),
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"]),
                last_run=datetime.fromisoformat(item["last_run"]) if item.get("last_run") else None,
                run_count=item.get("run_count", 0),
                is_public=item.get("is_public", False),
                url=item.get("url"),
                webhook_url=item.get("webhook_url")
            )
            
            return zap
            
        except Exception as e:
            self.logger.error(f"Failed to create zap from template {template_id}: {e}")
            raise
    
    async def get_zap_stats(self, zap_id: str) -> Dict[str, Any]:
        """
        Get statistics for a zap.
        
        Args:
            zap_id: Zap ID
            
        Returns:
            Zap statistics
        """
        try:
            url = f"{self.config.base_url}/zaps/{zap_id}/stats"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get stats for zap {zap_id}: {e}")
            raise
    
    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information.
        
        Returns:
            Account information
        """
        try:
            url = f"{self.config.base_url}/account"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get account info: {e}")
            raise
    
    async def get_apps(self) -> List[Dict[str, Any]]:
        """
        Get available apps.
        
        Returns:
            List of available apps
        """
        try:
            url = f"{self.config.base_url}/apps"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get apps: {e}")
            raise
    
    async def get_app_triggers(self, app: str) -> List[Dict[str, Any]]:
        """
        Get triggers for a specific app.
        
        Args:
            app: App name
            
        Returns:
            List of app triggers
        """
        try:
            url = f"{self.config.base_url}/apps/{app}/triggers"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get triggers for app {app}: {e}")
            raise
    
    async def get_app_actions(self, app: str) -> List[Dict[str, Any]]:
        """
        Get actions for a specific app.
        
        Args:
            app: App name
            
        Returns:
            List of app actions
        """
        try:
            url = f"{self.config.base_url}/apps/{app}/actions"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get actions for app {app}: {e}")
            raise
    
    async def test_trigger(
        self,
        zap_id: str,
        trigger_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Test a zap trigger.
        
        Args:
            zap_id: Zap ID
            trigger_data: Trigger test data
            
        Returns:
            Test results
        """
        try:
            url = f"{self.config.base_url}/zaps/{zap_id}/test/trigger"
            response = self.session.post(url, json=trigger_data)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to test trigger for zap {zap_id}: {e}")
            raise
    
    async def test_action(
        self,
        zap_id: str,
        action_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Test a zap action.
        
        Args:
            zap_id: Zap ID
            action_data: Action test data
            
        Returns:
            Test results
        """
        try:
            url = f"{self.config.base_url}/zaps/{zap_id}/test/action"
            response = self.session.post(url, json=action_data)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to test action for zap {zap_id}: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Zapier integration.
        
        Returns:
            Health check results
        """
        try:
            # Test basic connectivity
            url = f"{self.config.base_url}/account"
            response = self.session.get(url)
            response.raise_for_status()
            
            account_data = response.json()
            
            # Test zaps endpoint
            url = f"{self.config.base_url}/zaps"
            response = self.session.get(url, params={"limit": 1})
            response.raise_for_status()
            
            return {
                "status": "healthy",
                "account_email": account_data.get("email"),
                "account_type": account_data.get("account_type"),
                "api_key_valid": True,
                "zaps_accessible": True,
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_key_valid": False,
                "last_checked": datetime.now().isoformat()
            }

