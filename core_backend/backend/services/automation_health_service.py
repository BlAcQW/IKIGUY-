"""
Automation Health Monitoring Service

Provides real-time health monitoring for automation components including
VAPI, N8N workflows, integrations, and custom tools.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import aiohttp
import json

from ..mongo import get_collection


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels for automation components."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """Types of automation components to monitor."""
    VAPI_AGENT = "vapi_agent"
    N8N_WORKFLOW = "n8n_workflow"
    INTEGRATION = "integration"
    CUSTOM_TOOL = "custom_tool"
    AUTOMATION = "automation"


class HealthCheck:
    """Represents a health check result for a component."""

    def __init__(
        self,
        component_id: str,
        component_type: ComponentType,
        status: HealthStatus,
        response_time: float = None,
        error_message: str = None,
        metadata: Dict[str, Any] = None,
        checked_at: datetime = None
    ):
        self.component_id = component_id
        self.component_type = component_type
        self.status = status
        self.response_time = response_time
        self.error_message = error_message
        self.metadata = metadata or {}
        self.checked_at = checked_at or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "component_id": self.component_id,
            "component_type": self.component_type.value,
            "status": self.status.value,
            "response_time": self.response_time,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "checked_at": self.checked_at
        }


class AutomationHealthService:
    """Service for monitoring automation component health in real-time."""

    def __init__(self):
        self.health_collection = get_collection("automation_health")
        self.components_collection = get_collection("monitored_components")
        self.health_history_collection = get_collection("health_history")

        # Health check intervals (in seconds)
        self.check_intervals = {
            ComponentType.VAPI_AGENT: 30,
            ComponentType.N8N_WORKFLOW: 60,
            ComponentType.INTEGRATION: 120,
            ComponentType.CUSTOM_TOOL: 180,
            ComponentType.AUTOMATION: 60
        }

        # Health thresholds
        self.response_time_thresholds = {
            ComponentType.VAPI_AGENT: {"warning": 1.0, "critical": 3.0},
            ComponentType.N8N_WORKFLOW: {"warning": 5.0, "critical": 15.0},
            ComponentType.INTEGRATION: {"warning": 2.0, "critical": 10.0},
            ComponentType.CUSTOM_TOOL: {"warning": 3.0, "critical": 10.0},
            ComponentType.AUTOMATION: {"warning": 5.0, "critical": 20.0}
        }

        self._monitoring_active = False
        self._monitor_task = None

    async def register_component(
        self,
        component_id: str,
        component_type: ComponentType,
        automation_id: str,
        tenant_id: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Register a component for health monitoring."""
        try:
            component_doc = {
                "component_id": component_id,
                "component_type": component_type.value,
                "automation_id": automation_id,
                "tenant_id": tenant_id,
                "metadata": metadata or {},
                "status": HealthStatus.UNKNOWN.value,
                "registered_at": datetime.now(timezone.utc),
                "last_checked": None,
                "check_enabled": True
            }

            # Upsert component
            self.components_collection.replace_one(
                {"component_id": component_id},
                component_doc,
                upsert=True
            )

            logger.info(f"Registered component {component_id} for monitoring")
            return {"success": True, "component_id": component_id}

        except Exception as e:
            logger.error(f"Error registering component {component_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def check_vapi_agent_health(self, component_id: str, metadata: Dict[str, Any]) -> HealthCheck:
        """Check health of a VAPI agent."""
        start_time = datetime.now(timezone.utc)

        try:
            # Get VAPI configuration from metadata
            vapi_config = metadata.get("vapi_config", {})
            agent_id = vapi_config.get("agent_id")

            if not agent_id:
                return HealthCheck(
                    component_id=component_id,
                    component_type=ComponentType.VAPI_AGENT,
                    status=HealthStatus.CRITICAL,
                    error_message="No VAPI agent ID configured"
                )

            # Check VAPI agent status via API
            # This would integrate with the actual VAPI service
            async with aiohttp.ClientSession() as session:
                # Mock VAPI health check - replace with actual VAPI API call
                try:
                    # Simulate API call
                    await asyncio.sleep(0.1)  # Simulate network delay

                    # Calculate response time
                    response_time = (datetime.now(timezone.utc) - start_time).total_seconds()

                    # Determine status based on response time
                    thresholds = self.response_time_thresholds[ComponentType.VAPI_AGENT]
                    if response_time >= thresholds["critical"]:
                        status = HealthStatus.CRITICAL
                    elif response_time >= thresholds["warning"]:
                        status = HealthStatus.WARNING
                    else:
                        status = HealthStatus.HEALTHY

                    return HealthCheck(
                        component_id=component_id,
                        component_type=ComponentType.VAPI_AGENT,
                        status=status,
                        response_time=response_time,
                        metadata={
                            "agent_id": agent_id,
                            "last_activity": datetime.now(timezone.utc).isoformat()
                        }
                    )

                except Exception as api_error:
                    return HealthCheck(
                        component_id=component_id,
                        component_type=ComponentType.VAPI_AGENT,
                        status=HealthStatus.CRITICAL,
                        error_message=f"VAPI API error: {str(api_error)}"
                    )

        except Exception as e:
            return HealthCheck(
                component_id=component_id,
                component_type=ComponentType.VAPI_AGENT,
                status=HealthStatus.CRITICAL,
                error_message=f"Health check failed: {str(e)}"
            )

    async def check_n8n_workflow_health(self, component_id: str, metadata: Dict[str, Any]) -> HealthCheck:
        """Check health of an N8N workflow."""
        start_time = datetime.now(timezone.utc)

        try:
            # Get N8N configuration from metadata
            n8n_config = metadata.get("n8n_config", {})
            workflow_id = n8n_config.get("workflow_id")
            n8n_url = n8n_config.get("base_url", "http://localhost:5678")

            if not workflow_id:
                return HealthCheck(
                    component_id=component_id,
                    component_type=ComponentType.N8N_WORKFLOW,
                    status=HealthStatus.CRITICAL,
                    error_message="No N8N workflow ID configured"
                )

            # Check N8N workflow status
            async with aiohttp.ClientSession() as session:
                try:
                    # Check workflow status via N8N API
                    headers = {
                        "Content-Type": "application/json"
                    }

                    # Add authentication if available
                    api_key = n8n_config.get("api_key")
                    if api_key:
                        headers["Authorization"] = f"Bearer {api_key}"

                    # Mock N8N health check - replace with actual N8N API call
                    await asyncio.sleep(0.2)  # Simulate network delay

                    response_time = (datetime.now(timezone.utc) - start_time).total_seconds()

                    # Determine status based on response time
                    thresholds = self.response_time_thresholds[ComponentType.N8N_WORKFLOW]
                    if response_time >= thresholds["critical"]:
                        status = HealthStatus.CRITICAL
                    elif response_time >= thresholds["warning"]:
                        status = HealthStatus.WARNING
                    else:
                        status = HealthStatus.HEALTHY

                    return HealthCheck(
                        component_id=component_id,
                        component_type=ComponentType.N8N_WORKFLOW,
                        status=status,
                        response_time=response_time,
                        metadata={
                            "workflow_id": workflow_id,
                            "last_execution": datetime.now(timezone.utc).isoformat(),
                            "n8n_url": n8n_url
                        }
                    )

                except Exception as api_error:
                    return HealthCheck(
                        component_id=component_id,
                        component_type=ComponentType.N8N_WORKFLOW,
                        status=HealthStatus.CRITICAL,
                        error_message=f"N8N API error: {str(api_error)}"
                    )

        except Exception as e:
            return HealthCheck(
                component_id=component_id,
                component_type=ComponentType.N8N_WORKFLOW,
                status=HealthStatus.CRITICAL,
                error_message=f"Health check failed: {str(e)}"
            )

    async def check_integration_health(self, component_id: str, metadata: Dict[str, Any]) -> HealthCheck:
        """Check health of an integration."""
        start_time = datetime.now(timezone.utc)

        try:
            # Get integration configuration from metadata
            integration_config = metadata.get("integration_config", {})
            integration_name = integration_config.get("name")
            service_url = integration_config.get("service_url")

            if not integration_name:
                return HealthCheck(
                    component_id=component_id,
                    component_type=ComponentType.INTEGRATION,
                    status=HealthStatus.CRITICAL,
                    error_message="No integration name configured"
                )

            # Check integration health
            if service_url:
                # Check external service health
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(service_url, timeout=5) as response:
                            response_time = (datetime.now(timezone.utc) - start_time).total_seconds()

                            if response.status == 200:
                                status = HealthStatus.HEALTHY
                            elif response.status in [429, 503]:
                                status = HealthStatus.WARNING
                            else:
                                status = HealthStatus.CRITICAL

                            return HealthCheck(
                                component_id=component_id,
                                component_type=ComponentType.INTEGRATION,
                                status=status,
                                response_time=response_time,
                                metadata={
                                    "integration_name": integration_name,
                                    "service_url": service_url,
                                    "status_code": response.status
                                }
                            )

                    except asyncio.TimeoutError:
                        return HealthCheck(
                            component_id=component_id,
                            component_type=ComponentType.INTEGRATION,
                            status=HealthStatus.CRITICAL,
                            error_message="Integration service timeout"
                        )
                    except Exception as api_error:
                        return HealthCheck(
                            component_id=component_id,
                            component_type=ComponentType.INTEGRATION,
                            status=HealthStatus.CRITICAL,
                            error_message=f"Integration error: {str(api_error)}"
                        )
            else:
                # For integrations without external URLs, assume healthy
                return HealthCheck(
                    component_id=component_id,
                    component_type=ComponentType.INTEGRATION,
                    status=HealthStatus.HEALTHY,
                    response_time=0.0,
                    metadata={"integration_name": integration_name}
                )

        except Exception as e:
            return HealthCheck(
                component_id=component_id,
                component_type=ComponentType.INTEGRATION,
                status=HealthStatus.CRITICAL,
                error_message=f"Health check failed: {str(e)}"
            )

    async def check_custom_tool_health(self, component_id: str, metadata: Dict[str, Any]) -> HealthCheck:
        """Check health of a custom tool."""
        start_time = datetime.now(timezone.utc)

        try:
            # Get custom tool configuration from metadata
            tool_config = metadata.get("tool_config", {})
            tool_name = tool_config.get("name")
            endpoint = tool_config.get("endpoint")

            if not tool_name:
                return HealthCheck(
                    component_id=component_id,
                    component_type=ComponentType.CUSTOM_TOOL,
                    status=HealthStatus.CRITICAL,
                    error_message="No custom tool name configured"
                )

            # Check custom tool health via endpoint
            if endpoint:
                try:
                    async with aiohttp.ClientSession() as session:
                        # Test tool endpoint with minimal request
                        test_data = {"test": True}
                        async with session.post(endpoint, json=test_data, timeout=5) as response:
                            response_time = (datetime.now(timezone.utc) - start_time).total_seconds()

                            # Determine status based on response
                            if response.status == 200:
                                status = HealthStatus.HEALTHY
                            elif response.status in [400, 422]:  # Bad request but service is up
                                status = HealthStatus.WARNING
                            else:
                                status = HealthStatus.CRITICAL

                            return HealthCheck(
                                component_id=component_id,
                                component_type=ComponentType.CUSTOM_TOOL,
                                status=status,
                                response_time=response_time,
                                metadata={
                                    "tool_name": tool_name,
                                    "endpoint": endpoint,
                                    "status_code": response.status
                                }
                            )

                except asyncio.TimeoutError:
                    return HealthCheck(
                        component_id=component_id,
                        component_type=ComponentType.CUSTOM_TOOL,
                        status=HealthStatus.CRITICAL,
                        error_message="Custom tool endpoint timeout"
                    )
                except Exception as api_error:
                    return HealthCheck(
                        component_id=component_id,
                        component_type=ComponentType.CUSTOM_TOOL,
                        status=HealthStatus.CRITICAL,
                        error_message=f"Custom tool error: {str(api_error)}"
                    )
            else:
                # For tools without endpoints, assume healthy
                return HealthCheck(
                    component_id=component_id,
                    component_type=ComponentType.CUSTOM_TOOL,
                    status=HealthStatus.HEALTHY,
                    response_time=0.0,
                    metadata={"tool_name": tool_name}
                )

        except Exception as e:
            return HealthCheck(
                component_id=component_id,
                component_type=ComponentType.CUSTOM_TOOL,
                status=HealthStatus.CRITICAL,
                error_message=f"Health check failed: {str(e)}"
            )

    async def perform_health_check(self, component_id: str) -> Optional[HealthCheck]:
        """Perform health check for a specific component."""
        try:
            # Get component configuration
            component = self.components_collection.find_one({"component_id": component_id})
            if not component:
                logger.error(f"Component {component_id} not found in monitoring registry")
                return None

            component_type = ComponentType(component["component_type"])
            metadata = component.get("metadata", {})

            # Perform appropriate health check based on component type
            if component_type == ComponentType.VAPI_AGENT:
                health_check = await self.check_vapi_agent_health(component_id, metadata)
            elif component_type == ComponentType.N8N_WORKFLOW:
                health_check = await self.check_n8n_workflow_health(component_id, metadata)
            elif component_type == ComponentType.INTEGRATION:
                health_check = await self.check_integration_health(component_id, metadata)
            elif component_type == ComponentType.CUSTOM_TOOL:
                health_check = await self.check_custom_tool_health(component_id, metadata)
            else:
                logger.error(f"Unknown component type: {component_type}")
                return None

            # Store health check result
            await self.store_health_check(health_check)

            # Update component status
            self.components_collection.update_one(
                {"component_id": component_id},
                {
                    "$set": {
                        "status": health_check.status.value,
                        "last_checked": health_check.checked_at,
                        "last_response_time": health_check.response_time,
                        "last_error": health_check.error_message
                    }
                }
            )

            return health_check

        except Exception as e:
            logger.error(f"Error performing health check for {component_id}: {str(e)}")
            return None

    async def store_health_check(self, health_check: HealthCheck) -> None:
        """Store health check result in database."""
        try:
            # Store current health status
            health_doc = health_check.to_dict()
            self.health_collection.replace_one(
                {"component_id": health_check.component_id},
                health_doc,
                upsert=True
            )

            # Store in health history for analytics
            history_doc = health_doc.copy()
            history_doc["_id"] = None  # Let MongoDB generate new ID
            self.health_history_collection.insert_one(history_doc)

            # Clean up old history (keep last 7 days)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
            self.health_history_collection.delete_many({
                "checked_at": {"$lt": cutoff_date}
            })

        except Exception as e:
            logger.error(f"Error storing health check: {str(e)}")

    async def get_automation_health_status(self, automation_id: str) -> Dict[str, Any]:
        """Get overall health status for an automation."""
        try:
            # Get all components for this automation
            components = list(self.components_collection.find({
                "automation_id": automation_id,
                "check_enabled": True
            }))

            if not components:
                return {
                    "automation_id": automation_id,
                    "overall_status": HealthStatus.UNKNOWN.value,
                    "components": [],
                    "summary": {"healthy": 0, "warning": 0, "critical": 0, "unknown": 0}
                }

            # Get current health status for each component
            component_health = []
            status_counts = {"healthy": 0, "warning": 0, "critical": 0, "unknown": 0}

            for component in components:
                component_id = component["component_id"]
                health_doc = self.health_collection.find_one({"component_id": component_id})

                if health_doc:
                    status = health_doc["status"]
                    component_health.append({
                        "component_id": component_id,
                        "component_type": component["component_type"],
                        "status": status,
                        "last_checked": health_doc.get("checked_at"),
                        "response_time": health_doc.get("response_time"),
                        "error_message": health_doc.get("error_message")
                    })
                    status_counts[status] += 1
                else:
                    component_health.append({
                        "component_id": component_id,
                        "component_type": component["component_type"],
                        "status": HealthStatus.UNKNOWN.value,
                        "last_checked": None,
                        "response_time": None,
                        "error_message": "No health data available"
                    })
                    status_counts["unknown"] += 1

            # Determine overall status
            if status_counts["critical"] > 0:
                overall_status = HealthStatus.CRITICAL.value
            elif status_counts["warning"] > 0:
                overall_status = HealthStatus.WARNING.value
            elif status_counts["healthy"] > 0:
                overall_status = HealthStatus.HEALTHY.value
            else:
                overall_status = HealthStatus.UNKNOWN.value

            return {
                "automation_id": automation_id,
                "overall_status": overall_status,
                "components": component_health,
                "summary": status_counts,
                "total_components": len(components),
                "health_score": self._calculate_health_score(status_counts),
                "last_updated": datetime.now(timezone.utc)
            }

        except Exception as e:
            logger.error(f"Error getting automation health status: {str(e)}")
            return {
                "automation_id": automation_id,
                "overall_status": HealthStatus.UNKNOWN.value,
                "error": str(e)
            }

    def _calculate_health_score(self, status_counts: Dict[str, int]) -> float:
        """Calculate overall health score (0-100) based on component statuses."""
        total = sum(status_counts.values())
        if total == 0:
            return 0.0

        # Weighted scoring: healthy=1.0, warning=0.6, critical=0.0, unknown=0.3
        score = (
            status_counts["healthy"] * 1.0 +
            status_counts["warning"] * 0.6 +
            status_counts["critical"] * 0.0 +
            status_counts["unknown"] * 0.3
        ) / total

        return round(score * 100, 1)

    async def start_monitoring(self) -> None:
        """Start continuous health monitoring."""
        if self._monitoring_active:
            logger.info("Health monitoring already active")
            return

        self._monitoring_active = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Started automation health monitoring")

    async def stop_monitoring(self) -> None:
        """Stop continuous health monitoring."""
        self._monitoring_active = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped automation health monitoring")

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring_active:
            try:
                # Get all enabled components
                components = list(self.components_collection.find({"check_enabled": True}))

                # Group components by check interval
                check_groups = {}
                for component in components:
                    component_type = ComponentType(component["component_type"])
                    interval = self.check_intervals.get(component_type, 60)

                    # Check if component needs health check
                    last_checked = component.get("last_checked")
                    if last_checked:
                        time_since_check = (datetime.now(timezone.utc) - last_checked).total_seconds()
                        if time_since_check < interval:
                            continue  # Skip this component for now

                    if interval not in check_groups:
                        check_groups[interval] = []
                    check_groups[interval].append(component["component_id"])

                # Perform health checks
                for interval, component_ids in check_groups.items():
                    if component_ids:
                        # Run health checks concurrently for components with same interval
                        tasks = [self.perform_health_check(cid) for cid in component_ids]
                        await asyncio.gather(*tasks, return_exceptions=True)

                # Wait before next monitoring cycle
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(30)

    async def get_health_metrics(
        self,
        automation_id: str = None,
        tenant_id: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """Get health metrics and analytics."""
        try:
            # Build query filters
            query_filter = {}
            if automation_id:
                # Get components for this automation
                components = list(self.components_collection.find({"automation_id": automation_id}))
                component_ids = [c["component_id"] for c in components]
                query_filter["component_id"] = {"$in": component_ids}

            if tenant_id:
                # Get components for this tenant
                components = list(self.components_collection.find({"tenant_id": tenant_id}))
                component_ids = [c["component_id"] for c in components]
                if "component_id" in query_filter:
                    # Intersect with existing filter
                    existing_ids = set(query_filter["component_id"]["$in"])
                    new_ids = set(component_ids)
                    query_filter["component_id"]["$in"] = list(existing_ids.intersection(new_ids))
                else:
                    query_filter["component_id"] = {"$in": component_ids}

            # Add date filters
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                query_filter["checked_at"] = date_filter

            # Get health metrics from history
            pipeline = [
                {"$match": query_filter},
                {"$group": {
                    "_id": {
                        "component_type": "$component_type",
                        "status": "$status",
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$checked_at"}}
                    },
                    "count": {"$sum": 1},
                    "avg_response_time": {"$avg": "$response_time"}
                }},
                {"$group": {
                    "_id": "$_id.date",
                    "metrics": {
                        "$push": {
                            "component_type": "$_id.component_type",
                            "status": "$_id.status",
                            "count": "$count",
                            "avg_response_time": "$avg_response_time"
                        }
                    }
                }},
                {"$sort": {"_id": 1}}
            ]

            results = list(self.health_history_collection.aggregate(pipeline))

            # Get current status summary
            current_query = {"component_id": {"$in": query_filter.get("component_id", {}).get("$in", [])}} if query_filter.get("component_id") else {}
            current_status = list(self.health_collection.find(current_query))

            status_summary = {"healthy": 0, "warning": 0, "critical": 0, "unknown": 0}
            for status_doc in current_status:
                status = status_doc.get("status", "unknown")
                status_summary[status] = status_summary.get(status, 0) + 1

            return {
                "metrics_by_date": results,
                "current_status_summary": status_summary,
                "total_components": len(current_status),
                "health_score": self._calculate_health_score(status_summary),
                "query_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            }

        except Exception as e:
            logger.error(f"Error getting health metrics: {str(e)}")
            return {"error": str(e)}