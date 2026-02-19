"""
Make (Integromat) Integration Module

This module provides integration with Make (formerly Integromat) for workflow automation,
process orchestration, and scenario management.
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
    MAKE_AVAILABLE = True
except ImportError:
    MAKE_AVAILABLE = False
    logging.warning("Make APIs not available. Install requests")

logger = logging.getLogger(__name__)


class MakeScenarioStatus(Enum):
    """Make scenario status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"


class MakeExecutionStatus(Enum):
    """Make execution status."""
    SUCCESS = "success"
    ERROR = "error"
    RUNNING = "running"
    WAITING = "waiting"
    CANCELED = "canceled"
    TIMEOUT = "timeout"


@dataclass
class MakeConfig:
    """Configuration for Make integration."""
    
    api_token: str
    """Make API token."""
    
    base_url: str = "https://eu1.make.com/api/v2"
    """Make API base URL."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    max_retries: int = 3
    """Maximum retry attempts."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""


@dataclass
class MakeScenario:
    """Make scenario data structure."""
    
    id: int
    """Scenario ID."""
    
    name: str
    """Scenario name."""
    
    status: MakeScenarioStatus
    """Scenario status."""
    
    flow: Dict[str, Any]
    """Scenario flow definition."""
    
    connections: List[Dict[str, Any]]
    """Scenario connections."""
    
    settings: Dict[str, Any]
    """Scenario settings."""
    
    tags: List[str] = field(default_factory=list)
    """Scenario tags."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""
    
    last_run: Optional[datetime] = None
    """Last run timestamp."""
    
    runs_count: int = 0
    """Total runs count."""


@dataclass
class MakeExecution:
    """Make execution data structure."""
    
    id: int
    """Execution ID."""
    
    scenario_id: int
    """Scenario ID."""
    
    status: MakeExecutionStatus
    """Execution status."""
    
    data: List[Dict[str, Any]]
    """Execution data."""
    
    started_at: Optional[datetime] = None
    """Start timestamp."""
    
    finished_at: Optional[datetime] = None
    """Finish timestamp."""
    
    duration: Optional[int] = None
    """Execution duration in seconds."""
    
    error_message: Optional[str] = None
    """Error message if failed."""


@dataclass
class MakeConnection:
    """Make connection data structure."""
    
    id: int
    """Connection ID."""
    
    name: str
    """Connection name."""
    
    app: str
    """App name."""
    
    status: str
    """Connection status."""
    
    settings: Dict[str, Any]
    """Connection settings."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


class MakeIntegration:
    """Make integration for workflow automation and process orchestration."""
    
    def __init__(self, config: MakeConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        self.session.headers.update({
            "Authorization": f"Token {config.api_token}",
            "Content-Type": "application/json"
        })
    
    async def get_scenarios(self, limit: int = 100) -> List[MakeScenario]:
        """
        Get all scenarios.
        
        Args:
            limit: Number of scenarios to return
            
        Returns:
            List of scenarios
        """
        try:
            url = f"{self.config.base_url}/scenarios"
            params = {"limit": limit}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            scenarios_data = response.json()
            scenarios = []
            
            for scenario_data in scenarios_data:
                scenario = MakeScenario(
                    id=scenario_data["id"],
                    name=scenario_data["name"],
                    status=MakeScenarioStatus(scenario_data["status"]),
                    flow=scenario_data.get("flow", {}),
                    connections=scenario_data.get("connections", []),
                    settings=scenario_data.get("settings", {}),
                    tags=scenario_data.get("tags", []),
                    created_at=datetime.fromisoformat(scenario_data["createdAt"].replace("Z", "+00:00")) if scenario_data.get("createdAt") else None,
                    updated_at=datetime.fromisoformat(scenario_data["updatedAt"].replace("Z", "+00:00")) if scenario_data.get("updatedAt") else None,
                    last_run=datetime.fromisoformat(scenario_data["lastRun"].replace("Z", "+00:00")) if scenario_data.get("lastRun") else None,
                    runs_count=scenario_data.get("runsCount", 0)
                )
                scenarios.append(scenario)
            
            return scenarios
            
        except Exception as e:
            self.logger.error(f"Failed to get scenarios: {e}")
            raise
    
    async def get_scenario(self, scenario_id: int) -> MakeScenario:
        """
        Get a specific scenario.
        
        Args:
            scenario_id: Scenario ID
            
        Returns:
            Scenario data
        """
        try:
            url = f"{self.config.base_url}/scenarios/{scenario_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            scenario_data = response.json()
            
            return MakeScenario(
                id=scenario_data["id"],
                name=scenario_data["name"],
                status=MakeScenarioStatus(scenario_data["status"]),
                flow=scenario_data.get("flow", {}),
                connections=scenario_data.get("connections", []),
                settings=scenario_data.get("settings", {}),
                tags=scenario_data.get("tags", []),
                created_at=datetime.fromisoformat(scenario_data["createdAt"].replace("Z", "+00:00")) if scenario_data.get("createdAt") else None,
                updated_at=datetime.fromisoformat(scenario_data["updatedAt"].replace("Z", "+00:00")) if scenario_data.get("updatedAt") else None,
                last_run=datetime.fromisoformat(scenario_data["lastRun"].replace("Z", "+00:00")) if scenario_data.get("lastRun") else None,
                runs_count=scenario_data.get("runsCount", 0)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get scenario: {e}")
            raise
    
    async def create_scenario(
        self,
        name: str,
        flow: Dict[str, Any],
        connections: Optional[List[Dict[str, Any]]] = None,
        settings: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> MakeScenario:
        """
        Create a new scenario.
        
        Args:
            name: Scenario name
            flow: Scenario flow definition
            connections: Scenario connections
            settings: Scenario settings
            tags: Scenario tags
            
        Returns:
            Created scenario
        """
        try:
            url = f"{self.config.base_url}/scenarios"
            
            data = {
                "name": name,
                "flow": flow
            }
            
            if connections:
                data["connections"] = connections
            if settings:
                data["settings"] = settings
            if tags:
                data["tags"] = tags
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            scenario_data = response.json()
            
            return MakeScenario(
                id=scenario_data["id"],
                name=scenario_data["name"],
                status=MakeScenarioStatus(scenario_data["status"]),
                flow=scenario_data.get("flow", {}),
                connections=scenario_data.get("connections", []),
                settings=scenario_data.get("settings", {}),
                tags=scenario_data.get("tags", []),
                created_at=datetime.fromisoformat(scenario_data["createdAt"].replace("Z", "+00:00")) if scenario_data.get("createdAt") else None,
                updated_at=datetime.fromisoformat(scenario_data["updatedAt"].replace("Z", "+00:00")) if scenario_data.get("updatedAt") else None,
                last_run=datetime.fromisoformat(scenario_data["lastRun"].replace("Z", "+00:00")) if scenario_data.get("lastRun") else None,
                runs_count=scenario_data.get("runsCount", 0)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create scenario: {e}")
            raise
    
    async def update_scenario(
        self,
        scenario_id: int,
        name: Optional[str] = None,
        flow: Optional[Dict[str, Any]] = None,
        connections: Optional[List[Dict[str, Any]]] = None,
        settings: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> MakeScenario:
        """
        Update a scenario.
        
        Args:
            scenario_id: Scenario ID
            name: New scenario name
            flow: New scenario flow
            connections: New scenario connections
            settings: New scenario settings
            tags: New scenario tags
            
        Returns:
            Updated scenario
        """
        try:
            url = f"{self.config.base_url}/scenarios/{scenario_id}"
            
            data = {}
            if name:
                data["name"] = name
            if flow:
                data["flow"] = flow
            if connections:
                data["connections"] = connections
            if settings:
                data["settings"] = settings
            if tags:
                data["tags"] = tags
            
            response = self.session.put(url, json=data)
            response.raise_for_status()
            
            scenario_data = response.json()
            
            return MakeScenario(
                id=scenario_data["id"],
                name=scenario_data["name"],
                status=MakeScenarioStatus(scenario_data["status"]),
                flow=scenario_data.get("flow", {}),
                connections=scenario_data.get("connections", []),
                settings=scenario_data.get("settings", {}),
                tags=scenario_data.get("tags", []),
                created_at=datetime.fromisoformat(scenario_data["createdAt"].replace("Z", "+00:00")) if scenario_data.get("createdAt") else None,
                updated_at=datetime.fromisoformat(scenario_data["updatedAt"].replace("Z", "+00:00")) if scenario_data.get("updatedAt") else None,
                last_run=datetime.fromisoformat(scenario_data["lastRun"].replace("Z", "+00:00")) if scenario_data.get("lastRun") else None,
                runs_count=scenario_data.get("runsCount", 0)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update scenario: {e}")
            raise
    
    async def delete_scenario(self, scenario_id: int) -> bool:
        """
        Delete a scenario.
        
        Args:
            scenario_id: Scenario ID
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.config.base_url}/scenarios/{scenario_id}"
            response = self.session.delete(url)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete scenario: {e}")
            return False
    
    async def activate_scenario(self, scenario_id: int) -> bool:
        """
        Activate a scenario.
        
        Args:
            scenario_id: Scenario ID
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.config.base_url}/scenarios/{scenario_id}/activate"
            response = self.session.post(url)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to activate scenario: {e}")
            return False
    
    async def deactivate_scenario(self, scenario_id: int) -> bool:
        """
        Deactivate a scenario.
        
        Args:
            scenario_id: Scenario ID
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.config.base_url}/scenarios/{scenario_id}/deactivate"
            response = self.session.post(url)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deactivate scenario: {e}")
            return False
    
    async def run_scenario(
        self,
        scenario_id: int,
        data: Optional[Dict[str, Any]] = None
    ) -> MakeExecution:
        """
        Run a scenario.
        
        Args:
            scenario_id: Scenario ID
            data: Input data
            
        Returns:
            Execution data
        """
        try:
            url = f"{self.config.base_url}/scenarios/{scenario_id}/run"
            
            payload = {}
            if data:
                payload["data"] = data
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            execution_data = response.json()
            
            return MakeExecution(
                id=execution_data["id"],
                scenario_id=execution_data["scenarioId"],
                status=MakeExecutionStatus(execution_data["status"]),
                data=execution_data.get("data", []),
                started_at=datetime.fromisoformat(execution_data["startedAt"].replace("Z", "+00:00")) if execution_data.get("startedAt") else None,
                finished_at=datetime.fromisoformat(execution_data["finishedAt"].replace("Z", "+00:00")) if execution_data.get("finishedAt") else None,
                duration=execution_data.get("duration"),
                error_message=execution_data.get("errorMessage")
            )
            
        except Exception as e:
            self.logger.error(f"Failed to run scenario: {e}")
            raise
    
    async def get_executions(
        self,
        scenario_id: Optional[int] = None,
        limit: int = 50,
        status: Optional[MakeExecutionStatus] = None
    ) -> List[MakeExecution]:
        """
        Get executions.
        
        Args:
            scenario_id: Filter by scenario ID
            limit: Number of executions to return
            status: Filter by execution status
            
        Returns:
            List of executions
        """
        try:
            url = f"{self.config.base_url}/executions"
            
            params = {"limit": limit}
            if scenario_id:
                params["scenarioId"] = scenario_id
            if status:
                params["status"] = status.value
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            executions_data = response.json()
            executions = []
            
            for execution_data in executions_data:
                execution = MakeExecution(
                    id=execution_data["id"],
                    scenario_id=execution_data["scenarioId"],
                    status=MakeExecutionStatus(execution_data["status"]),
                    data=execution_data.get("data", []),
                    started_at=datetime.fromisoformat(execution_data["startedAt"].replace("Z", "+00:00")) if execution_data.get("startedAt") else None,
                    finished_at=datetime.fromisoformat(execution_data["finishedAt"].replace("Z", "+00:00")) if execution_data.get("finishedAt") else None,
                    duration=execution_data.get("duration"),
                    error_message=execution_data.get("errorMessage")
                )
                executions.append(execution)
            
            return executions
            
        except Exception as e:
            self.logger.error(f"Failed to get executions: {e}")
            raise
    
    async def get_execution(self, execution_id: int) -> MakeExecution:
        """
        Get a specific execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Execution data
        """
        try:
            url = f"{self.config.base_url}/executions/{execution_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            execution_data = response.json()
            
            return MakeExecution(
                id=execution_data["id"],
                scenario_id=execution_data["scenarioId"],
                status=MakeExecutionStatus(execution_data["status"]),
                data=execution_data.get("data", []),
                started_at=datetime.fromisoformat(execution_data["startedAt"].replace("Z", "+00:00")) if execution_data.get("startedAt") else None,
                finished_at=datetime.fromisoformat(execution_data["finishedAt"].replace("Z", "+00:00")) if execution_data.get("finishedAt") else None,
                duration=execution_data.get("duration"),
                error_message=execution_data.get("errorMessage")
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get execution: {e}")
            raise
    
    async def get_connections(self) -> List[MakeConnection]:
        """
        Get all connections.
        
        Returns:
            List of connections
        """
        try:
            url = f"{self.config.base_url}/connections"
            response = self.session.get(url)
            response.raise_for_status()
            
            connections_data = response.json()
            connections = []
            
            for connection_data in connections_data:
                connection = MakeConnection(
                    id=connection_data["id"],
                    name=connection_data["name"],
                    app=connection_data["app"],
                    status=connection_data["status"],
                    settings=connection_data.get("settings", {}),
                    created_at=datetime.fromisoformat(connection_data["createdAt"].replace("Z", "+00:00")) if connection_data.get("createdAt") else None,
                    updated_at=datetime.fromisoformat(connection_data["updatedAt"].replace("Z", "+00:00")) if connection_data.get("updatedAt") else None
                )
                connections.append(connection)
            
            return connections
            
        except Exception as e:
            self.logger.error(f"Failed to get connections: {e}")
            raise
    
    async def create_connection(
        self,
        name: str,
        app: str,
        settings: Dict[str, Any]
    ) -> MakeConnection:
        """
        Create a connection.
        
        Args:
            name: Connection name
            app: App name
            settings: Connection settings
            
        Returns:
            Created connection
        """
        try:
            url = f"{self.config.base_url}/connections"
            
            data = {
                "name": name,
                "app": app,
                "settings": settings
            }
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            connection_data = response.json()
            
            return MakeConnection(
                id=connection_data["id"],
                name=connection_data["name"],
                app=connection_data["app"],
                status=connection_data["status"],
                settings=connection_data.get("settings", {}),
                created_at=datetime.fromisoformat(connection_data["createdAt"].replace("Z", "+00:00")) if connection_data.get("createdAt") else None,
                updated_at=datetime.fromisoformat(connection_data["updatedAt"].replace("Z", "+00:00")) if connection_data.get("updatedAt") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create connection: {e}")
            raise
    
    async def delete_connection(self, connection_id: int) -> bool:
        """
        Delete a connection.
        
        Args:
            connection_id: Connection ID
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.config.base_url}/connections/{connection_id}"
            response = self.session.delete(url)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete connection: {e}")
            return False
    
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
    
    async def get_app_modules(self, app_name: str) -> List[Dict[str, Any]]:
        """
        Get app modules.
        
        Args:
            app_name: App name
            
        Returns:
            List of app modules
        """
        try:
            url = f"{self.config.base_url}/apps/{app_name}/modules"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get app modules: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Make integration.
        
        Returns:
            Health check results
        """
        try:
            # Test basic connectivity by getting scenarios
            scenarios = await self.get_scenarios(limit=1)
            
            # Test connections
            connections = await self.get_connections()
            
            return {
                "status": "healthy",
                "base_url": self.config.base_url,
                "scenarios_count": len(scenarios),
                "connections_count": len(connections),
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

