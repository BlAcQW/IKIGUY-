"""
Grafana Integration Module

This module provides integration with Grafana for performance monitoring,
dashboard management, and metric visualization.
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
    GRAFANA_AVAILABLE = True
except ImportError:
    GRAFANA_AVAILABLE = False
    logging.warning("Grafana APIs not available. Install requests")

logger = logging.getLogger(__name__)


class DashboardPermission(Enum):
    """Dashboard permission levels."""
    VIEW = "View"
    EDIT = "Edit"
    ADMIN = "Admin"


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GrafanaConfig:
    """Configuration for Grafana integration."""
    
    base_url: str
    """Grafana base URL (e.g., 'https://grafana.example.com')."""
    
    api_key: str
    """Grafana API key for authentication."""
    
    organization_id: Optional[int] = None
    """Organization ID (defaults to 1 if not specified)."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Whether to verify SSL certificates."""


@dataclass
class Dashboard:
    """Grafana dashboard data structure."""
    
    id: Optional[int]
    """Dashboard ID."""
    
    title: str
    """Dashboard title."""
    
    uid: str
    """Dashboard UID."""
    
    url: str
    """Dashboard URL."""
    
    folder_id: Optional[int] = None
    """Folder ID where dashboard is located."""
    
    folder_title: Optional[str] = None
    """Folder title."""
    
    tags: List[str] = field(default_factory=list)
    """Dashboard tags."""
    
    is_starred: bool = False
    """Whether dashboard is starred."""
    
    created_at: Optional[datetime] = None
    """When dashboard was created."""
    
    updated_at: Optional[datetime] = None
    """When dashboard was last updated."""
    
    version: int = 1
    """Dashboard version."""
    
    panels: List[Dict[str, Any]] = field(default_factory=list)
    """Dashboard panels."""


@dataclass
class AlertRule:
    """Grafana alert rule data structure."""
    
    name: str
    """Alert rule name."""
    
    uid: str
    """Alert rule UID."""
    
    condition: str
    """Alert condition expression."""
    
    for_duration: str
    """Duration to wait before firing alert."""
    
    severity: AlertSeverity
    """Alert severity level."""
    
    summary: str
    """Alert summary."""
    
    id: Optional[int] = None
    """Alert rule ID."""
    
    folder_uid: Optional[str] = None
    
    description: Optional[str] = None
    """Alert description."""
    
    labels: Dict[str, str] = field(default_factory=dict)
    """Alert labels."""
    
    annotations: Dict[str, str] = field(default_factory=dict)
    """Alert annotations."""
    
    is_paused: bool = False
    """Whether alert is paused."""
    
    created_at: Optional[datetime] = None
    """When alert was created."""
    
    updated_at: Optional[datetime] = None
    """When alert was last updated."""


@dataclass
class DataSource:
    """Grafana data source data structure."""
    
    id: Optional[int]
    """Data source ID."""
    
    name: str
    """Data source name."""
    
    type: str
    """Data source type (e.g., 'prometheus', 'influxdb')."""
    
    url: str
    """Data source URL."""
    
    access: str
    """Access mode ('proxy' or 'direct')."""
    
    is_default: bool = False
    """Whether this is the default data source."""
    
    json_data: Dict[str, Any] = field(default_factory=dict)
    """Additional JSON configuration."""
    
    secure_json_data: Dict[str, Any] = field(default_factory=dict)
    """Secure JSON configuration (passwords, etc.)."""
    
    created_at: Optional[datetime] = None
    """When data source was created."""
    
    updated_at: Optional[datetime] = None
    """When data source was last updated."""


@dataclass
class User:
    """Grafana user data structure."""
    
    id: int
    """User ID."""
    
    login: str
    """User login/username."""
    
    email: str
    """User email."""
    
    name: str
    """User display name."""
    
    is_admin: bool = False
    """Whether user is admin."""
    
    is_disabled: bool = False
    """Whether user is disabled."""
    
    last_seen_at: Optional[datetime] = None
    """When user was last seen."""
    
    created_at: Optional[datetime] = None
    """When user was created."""


class GrafanaIntegration:
    """Grafana integration for performance monitoring and visualization."""
    
    def __init__(self, config: GrafanaConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        })
        self.session.verify = config.verify_ssl
        self.session.timeout = config.timeout
    
    async def get_dashboards(self, folder_id: Optional[int] = None) -> List[Dashboard]:
        """
        Get all dashboards.
        
        Args:
            folder_id: Optional folder ID to filter by
            
        Returns:
            List of dashboards
        """
        try:
            url = f"{self.config.base_url}/api/search"
            params = {"type": "dash-db"}
            
            if folder_id:
                params["folderIds"] = folder_id
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            dashboards = []
            for item in response.json():
                dashboard = Dashboard(
                    id=item.get("id"),
                    title=item["title"],
                    uid=item["uid"],
                    url=item["url"],
                    folder_id=item.get("folderId"),
                    folder_title=item.get("folderTitle"),
                    tags=item.get("tags", []),
                    is_starred=item.get("isStarred", False),
                    created_at=datetime.fromisoformat(item["created"]) if item.get("created") else None,
                    updated_at=datetime.fromisoformat(item["updated"]) if item.get("updated") else None,
                    version=item.get("version", 1)
                )
                dashboards.append(dashboard)
            
            return dashboards
            
        except Exception as e:
            self.logger.error(f"Failed to get dashboards: {e}")
            raise
    
    async def get_dashboard(self, uid: str) -> Dashboard:
        """
        Get a specific dashboard by UID.
        
        Args:
            uid: Dashboard UID
            
        Returns:
            Dashboard details
        """
        try:
            url = f"{self.config.base_url}/api/dashboards/uid/{uid}"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            dashboard_data = data["dashboard"]
            meta = data["meta"]
            
            dashboard = Dashboard(
                id=dashboard_data.get("id"),
                title=dashboard_data["title"],
                uid=dashboard_data["uid"],
                url=meta["url"],
                folder_id=meta.get("folderId"),
                folder_title=meta.get("folderTitle"),
                tags=dashboard_data.get("tags", []),
                is_starred=meta.get("isStarred", False),
                created_at=datetime.fromisoformat(meta["created"]) if meta.get("created") else None,
                updated_at=datetime.fromisoformat(meta["updated"]) if meta.get("updated") else None,
                version=dashboard_data.get("version", 1),
                panels=dashboard_data.get("panels", [])
            )
            
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Failed to get dashboard {uid}: {e}")
            raise
    
    async def create_dashboard(self, dashboard: Dashboard) -> Dashboard:
        """
        Create a new dashboard.
        
        Args:
            dashboard: Dashboard to create
            
        Returns:
            Created dashboard
        """
        try:
            url = f"{self.config.base_url}/api/dashboards/db"
            
            payload = {
                "dashboard": {
                    "title": dashboard.title,
                    "uid": dashboard.uid,
                    "tags": dashboard.tags,
                    "panels": dashboard.panels
                },
                "folderId": dashboard.folder_id,
                "overwrite": False
            }
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            dashboard_data = data["dashboard"]
            meta = data["meta"]
            
            created_dashboard = Dashboard(
                id=dashboard_data.get("id"),
                title=dashboard_data["title"],
                uid=dashboard_data["uid"],
                url=meta["url"],
                folder_id=meta.get("folderId"),
                folder_title=meta.get("folderTitle"),
                tags=dashboard_data.get("tags", []),
                is_starred=meta.get("isStarred", False),
                created_at=datetime.fromisoformat(meta["created"]) if meta.get("created") else None,
                updated_at=datetime.fromisoformat(meta["updated"]) if meta.get("updated") else None,
                version=dashboard_data.get("version", 1),
                panels=dashboard_data.get("panels", [])
            )
            
            return created_dashboard
            
        except Exception as e:
            self.logger.error(f"Failed to create dashboard: {e}")
            raise
    
    async def update_dashboard(self, dashboard: Dashboard) -> Dashboard:
        """
        Update an existing dashboard.
        
        Args:
            dashboard: Dashboard to update
            
        Returns:
            Updated dashboard
        """
        try:
            url = f"{self.config.base_url}/api/dashboards/db"
            
            payload = {
                "dashboard": {
                    "id": dashboard.id,
                    "title": dashboard.title,
                    "uid": dashboard.uid,
                    "tags": dashboard.tags,
                    "panels": dashboard.panels,
                    "version": dashboard.version
                },
                "folderId": dashboard.folder_id,
                "overwrite": True
            }
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            dashboard_data = data["dashboard"]
            meta = data["meta"]
            
            updated_dashboard = Dashboard(
                id=dashboard_data.get("id"),
                title=dashboard_data["title"],
                uid=dashboard_data["uid"],
                url=meta["url"],
                folder_id=meta.get("folderId"),
                folder_title=meta.get("folderTitle"),
                tags=dashboard_data.get("tags", []),
                is_starred=meta.get("isStarred", False),
                created_at=datetime.fromisoformat(meta["created"]) if meta.get("created") else None,
                updated_at=datetime.fromisoformat(meta["updated"]) if meta.get("updated") else None,
                version=dashboard_data.get("version", 1),
                panels=dashboard_data.get("panels", [])
            )
            
            return updated_dashboard
            
        except Exception as e:
            self.logger.error(f"Failed to update dashboard: {e}")
            raise
    
    async def delete_dashboard(self, uid: str) -> bool:
        """
        Delete a dashboard.
        
        Args:
            uid: Dashboard UID
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.config.base_url}/api/dashboards/uid/{uid}"
            response = self.session.delete(url)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete dashboard {uid}: {e}")
            raise
    
    async def get_alert_rules(self, folder_uid: Optional[str] = None) -> List[AlertRule]:
        """
        Get all alert rules.
        
        Args:
            folder_uid: Optional folder UID to filter by
            
        Returns:
            List of alert rules
        """
        try:
            url = f"{self.config.base_url}/api/ruler/grafana/api/v1/rules"
            
            if folder_uid:
                url = f"{self.config.base_url}/api/ruler/grafana/api/v1/rules/{folder_uid}"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            alert_rules = []
            data = response.json()
            
            for folder_name, folder_data in data.items():
                for group_name, group_data in folder_data.items():
                    for rule in group_data.get("rules", []):
                        alert_rule = AlertRule(
                            id=rule.get("grafana_alert", {}).get("id"),
                            name=rule["alert"],
                            uid=rule.get("grafana_alert", {}).get("uid"),
                            folder_uid=folder_uid,
                            condition=rule.get("expr", ""),
                            for_duration=rule.get("for", "0s"),
                            severity=AlertSeverity(rule.get("labels", {}).get("severity", "medium")),
                            summary=rule.get("annotations", {}).get("summary", ""),
                            description=rule.get("annotations", {}).get("description"),
                            labels=rule.get("labels", {}),
                            annotations=rule.get("annotations", {}),
                            is_paused=rule.get("grafana_alert", {}).get("isPaused", False)
                        )
                        alert_rules.append(alert_rule)
            
            return alert_rules
            
        except Exception as e:
            self.logger.error(f"Failed to get alert rules: {e}")
            raise
    
    async def create_alert_rule(self, alert_rule: AlertRule) -> AlertRule:
        """
        Create a new alert rule.
        
        Args:
            alert_rule: Alert rule to create
            
        Returns:
            Created alert rule
        """
        try:
            url = f"{self.config.base_url}/api/ruler/grafana/api/v1/rules/{alert_rule.folder_uid or 'default'}"
            
            payload = {
                "default": {
                    "rules": [
                        {
                            "alert": alert_rule.name,
                            "expr": alert_rule.condition,
                            "for": alert_rule.for_duration,
                            "labels": {
                                **alert_rule.labels,
                                "severity": alert_rule.severity.value
                            },
                            "annotations": {
                                "summary": alert_rule.summary,
                                **alert_rule.annotations
                            }
                        }
                    ]
                }
            }
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            # Get the created alert rule
            created_rules = await self.get_alert_rules(alert_rule.folder_uid)
            for rule in created_rules:
                if rule.name == alert_rule.name:
                    return rule
            
            raise Exception("Failed to retrieve created alert rule")
            
        except Exception as e:
            self.logger.error(f"Failed to create alert rule: {e}")
            raise
    
    async def update_alert_rule(self, alert_rule: AlertRule) -> AlertRule:
        """
        Update an existing alert rule.
        
        Args:
            alert_rule: Alert rule to update
            
        Returns:
            Updated alert rule
        """
        try:
            # Delete existing rule
            await self.delete_alert_rule(alert_rule.uid)
            
            # Create new rule
            return await self.create_alert_rule(alert_rule)
            
        except Exception as e:
            self.logger.error(f"Failed to update alert rule: {e}")
            raise
    
    async def delete_alert_rule(self, uid: str) -> bool:
        """
        Delete an alert rule.
        
        Args:
            uid: Alert rule UID
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.config.base_url}/api/ruler/grafana/api/v1/rules/default/{uid}"
            response = self.session.delete(url)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete alert rule {uid}: {e}")
            raise
    
    async def get_data_sources(self) -> List[DataSource]:
        """
        Get all data sources.
        
        Returns:
            List of data sources
        """
        try:
            url = f"{self.config.base_url}/api/datasources"
            response = self.session.get(url)
            response.raise_for_status()
            
            data_sources = []
            for item in response.json():
                data_source = DataSource(
                    id=item.get("id"),
                    name=item["name"],
                    type=item["type"],
                    url=item["url"],
                    access=item["access"],
                    is_default=item.get("isDefault", False),
                    json_data=item.get("jsonData", {}),
                    created_at=datetime.fromisoformat(item["created"]) if item.get("created") else None,
                    updated_at=datetime.fromisoformat(item["updated"]) if item.get("updated") else None
                )
                data_sources.append(data_source)
            
            return data_sources
            
        except Exception as e:
            self.logger.error(f"Failed to get data sources: {e}")
            raise
    
    async def create_data_source(self, data_source: DataSource) -> DataSource:
        """
        Create a new data source.
        
        Args:
            data_source: Data source to create
            
        Returns:
            Created data source
        """
        try:
            url = f"{self.config.base_url}/api/datasources"
            
            payload = {
                "name": data_source.name,
                "type": data_source.type,
                "url": data_source.url,
                "access": data_source.access,
                "isDefault": data_source.is_default,
                "jsonData": data_source.json_data,
                "secureJsonData": data_source.secure_json_data
            }
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            created_data = response.json()
            created_data_source = DataSource(
                id=created_data.get("id"),
                name=created_data["name"],
                type=created_data["type"],
                url=created_data["url"],
                access=created_data["access"],
                is_default=created_data.get("isDefault", False),
                json_data=created_data.get("jsonData", {}),
                created_at=datetime.fromisoformat(created_data["created"]) if created_data.get("created") else None,
                updated_at=datetime.fromisoformat(created_data["updated"]) if created_data.get("updated") else None
            )
            
            return created_data_source
            
        except Exception as e:
            self.logger.error(f"Failed to create data source: {e}")
            raise
    
    async def get_users(self) -> List[User]:
        """
        Get all users.
        
        Returns:
            List of users
        """
        try:
            url = f"{self.config.base_url}/api/users"
            response = self.session.get(url)
            response.raise_for_status()
            
            users = []
            for item in response.json():
                user = User(
                    id=item["id"],
                    login=item["login"],
                    email=item["email"],
                    name=item["name"],
                    is_admin=item.get("isAdmin", False),
                    is_disabled=item.get("isDisabled", False),
                    last_seen_at=datetime.fromisoformat(item["lastSeenAt"]) if item.get("lastSeenAt") else None,
                    created_at=datetime.fromisoformat(item["createdAt"]) if item.get("createdAt") else None
                )
                users.append(user)
            
            return users
            
        except Exception as e:
            self.logger.error(f"Failed to get users: {e}")
            raise
    
    async def get_dashboard_permissions(self, uid: str) -> List[Dict[str, Any]]:
        """
        Get dashboard permissions.
        
        Args:
            uid: Dashboard UID
            
        Returns:
            List of permissions
        """
        try:
            url = f"{self.config.base_url}/api/dashboards/uid/{uid}/permissions"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get dashboard permissions: {e}")
            raise
    
    async def update_dashboard_permissions(
        self,
        uid: str,
        permissions: List[Dict[str, Any]]
    ) -> bool:
        """
        Update dashboard permissions.
        
        Args:
            uid: Dashboard UID
            permissions: List of permissions to set
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.config.base_url}/api/dashboards/uid/{uid}/permissions"
            response = self.session.post(url, json=permissions)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update dashboard permissions: {e}")
            raise
    
    async def get_metrics(self, data_source_uid: str, query: str) -> Dict[str, Any]:
        """
        Query metrics from a data source.
        
        Args:
            data_source_uid: Data source UID
            query: Query to execute
            
        Returns:
            Query results
        """
        try:
            url = f"{self.config.base_url}/api/datasources/proxy/{data_source_uid}/api/v1/query"
            
            params = {"query": query}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to query metrics: {e}")
            raise
    
    async def get_annotations(
        self,
        dashboard_id: Optional[int] = None,
        panel_id: Optional[int] = None,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get annotations.
        
        Args:
            dashboard_id: Optional dashboard ID filter
            panel_id: Optional panel ID filter
            from_time: Optional start time filter
            to_time: Optional end time filter
            
        Returns:
            List of annotations
        """
        try:
            url = f"{self.config.base_url}/api/annotations"
            params = {}
            
            if dashboard_id:
                params["dashboardId"] = dashboard_id
            if panel_id:
                params["panelId"] = panel_id
            if from_time:
                params["from"] = int(from_time.timestamp() * 1000)
            if to_time:
                params["to"] = int(to_time.timestamp() * 1000)
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get annotations: {e}")
            raise
    
    async def create_annotation(
        self,
        text: str,
        dashboard_id: Optional[int] = None,
        panel_id: Optional[int] = None,
        time: Optional[datetime] = None,
        time_end: Optional[datetime] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create an annotation.
        
        Args:
            text: Annotation text
            dashboard_id: Optional dashboard ID
            panel_id: Optional panel ID
            time: Optional start time
            time_end: Optional end time
            tags: Optional tags
            
        Returns:
            Created annotation
        """
        try:
            url = f"{self.config.base_url}/api/annotations"
            
            payload = {
                "text": text,
                "tags": tags or []
            }
            
            if dashboard_id:
                payload["dashboardId"] = dashboard_id
            if panel_id:
                payload["panelId"] = panel_id
            if time:
                payload["time"] = int(time.timestamp() * 1000)
            if time_end:
                payload["timeEnd"] = int(time_end.timestamp() * 1000)
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to create annotation: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Grafana integration.
        
        Returns:
            Health check results
        """
        try:
            # Test basic connectivity
            url = f"{self.config.base_url}/api/health"
            response = self.session.get(url)
            response.raise_for_status()
            
            health_data = response.json()
            
            # Test API access
            url = f"{self.config.base_url}/api/org"
            response = self.session.get(url)
            response.raise_for_status()
            
            org_data = response.json()
            
            return {
                "status": "healthy",
                "grafana_version": health_data.get("version"),
                "database": health_data.get("database"),
                "organization": org_data.get("name"),
                "organization_id": org_data.get("id"),
                "api_key_valid": True,
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

