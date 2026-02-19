"""
Automation Deployment Tracking Service

Comprehensive tracking service for deployed automations including VAPI agents,
N8N workflows, integrations, and custom tools. Provides real-time status
monitoring and deployment analytics.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass
import uuid

from ..mongo import get_collection


logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    """Deployment status levels."""
    PENDING = "pending"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    STOPPED = "stopped"
    UPDATING = "updating"


class ComponentType(Enum):
    """Types of automation components that can be deployed."""
    VAPI_AGENT = "vapi_agent"
    N8N_WORKFLOW = "n8n_workflow"
    INTEGRATION = "integration"
    CUSTOM_TOOL = "custom_tool"
    DEMO_PAGE = "demo_page"


@dataclass
class DeploymentComponent:
    """Represents a deployed automation component."""
    component_id: str
    component_type: ComponentType
    automation_id: str
    organization_id: str
    status: DeploymentStatus
    config: Dict[str, Any]
    deployment_info: Dict[str, Any]
    deployed_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "component_id": self.component_id,
            "component_type": self.component_type.value,
            "automation_id": self.automation_id,
            "organization_id": self.organization_id,
            "status": self.status.value,
            "config": self.config,
            "deployment_info": self.deployment_info,
            "deployed_at": self.deployed_at,
            "last_activity": self.last_activity,
            "error_message": self.error_message,
            "metadata": self.metadata or {}
        }


class AutomationDeploymentTrackingService:
    """Service for tracking automation deployments and component status."""

    def __init__(self):
        self.automations_collection = get_collection("automation_configs")
        self.deployments_collection = get_collection("automation_deployments")
        self.components_collection = get_collection("deployed_components")
        self.activity_log_collection = get_collection("deployment_activity_log")

    async def track_automation_deployment(
        self,
        automation_id: str,
        organization_id: str,
        deployment_config: Dict[str, Any],
        initiated_by: str = "system"
    ) -> Dict[str, Any]:
        """Track the start of an automation deployment."""
        try:
            deployment_doc = {
                "deployment_id": str(uuid.uuid4()),
                "automation_id": automation_id,
                "organization_id": organization_id,
                "status": DeploymentStatus.DEPLOYING.value,
                "deployment_config": deployment_config,
                "initiated_by": initiated_by,
                "started_at": datetime.now(timezone.utc),
                "components": [],
                "progress": 0,
                "current_stage": "initialization",
                "logs": []
            }

            self.deployments_collection.insert_one(deployment_doc)

            # Log activity
            await self._log_activity(
                automation_id=automation_id,
                action="deployment_started",
                details={"initiated_by": initiated_by},
                organization_id=organization_id
            )

            return {
                "success": True,
                "deployment_id": deployment_doc["deployment_id"],
                "status": deployment_doc["status"]
            }

        except Exception as e:
            logger.error(f"Error tracking automation deployment: {str(e)}")
            return {"success": False, "error": str(e)}

    async def register_deployed_component(
        self,
        automation_id: str,
        component_type: ComponentType,
        component_config: Dict[str, Any],
        deployment_info: Dict[str, Any],
        organization_id: str
    ) -> Dict[str, Any]:
        """Register a successfully deployed component."""
        try:
            component_id = str(uuid.uuid4())

            component = DeploymentComponent(
                component_id=component_id,
                component_type=component_type,
                automation_id=automation_id,
                organization_id=organization_id,
                status=DeploymentStatus.DEPLOYED,
                config=component_config,
                deployment_info=deployment_info,
                deployed_at=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc)
            )

            # Store component
            self.components_collection.insert_one(component.to_dict())

            # Update automation config with component info
            update_fields = {}
            if component_type == ComponentType.VAPI_AGENT:
                update_fields["vapiAgent.assistantId"] = deployment_info.get("assistant_id")
                update_fields["vapiAgent.phoneNumberId"] = deployment_info.get("phone_number_id")
            elif component_type == ComponentType.N8N_WORKFLOW:
                update_fields["n8nWorkflow.workflowId"] = deployment_info.get("workflow_id")
                update_fields["n8nWorkflow.webhookUrl"] = deployment_info.get("webhook_url")

            if update_fields:
                self.automations_collection.update_one(
                    {"id": automation_id},
                    {"$set": update_fields}
                )

            # Log activity
            await self._log_activity(
                automation_id=automation_id,
                action="component_deployed",
                details={
                    "component_type": component_type.value,
                    "component_id": component_id,
                    "deployment_info": deployment_info
                },
                organization_id=organization_id
            )

            # Register with health monitoring if available
            try:
                from .automation_health_service import AutomationHealthService, ComponentType as HealthComponentType
                health_service = AutomationHealthService()

                # Map component types
                health_component_type = None
                if component_type == ComponentType.VAPI_AGENT:
                    health_component_type = HealthComponentType.VAPI_AGENT
                elif component_type == ComponentType.N8N_WORKFLOW:
                    health_component_type = HealthComponentType.N8N_WORKFLOW
                elif component_type == ComponentType.INTEGRATION:
                    health_component_type = HealthComponentType.INTEGRATION
                elif component_type == ComponentType.CUSTOM_TOOL:
                    health_component_type = HealthComponentType.CUSTOM_TOOL

                if health_component_type:
                    await health_service.register_component(
                        component_id=component_id,
                        component_type=health_component_type,
                        automation_id=automation_id,
                        organization_id=organization_id,
                        metadata={
                            f"{component_type.value}_config": component_config,
                            "deployment_info": deployment_info
                        }
                    )
            except ImportError:
                # Health monitoring service not available
                pass

            return {
                "success": True,
                "component_id": component_id,
                "status": DeploymentStatus.DEPLOYED.value
            }

        except Exception as e:
            logger.error(f"Error registering deployed component: {str(e)}")
            return {"success": False, "error": str(e)}

    async def update_component_status(
        self,
        component_id: str,
        status: DeploymentStatus,
        error_message: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Update the status of a deployed component."""
        try:
            update_fields = {
                "status": status.value,
                "last_activity": datetime.now(timezone.utc)
            }

            if error_message:
                update_fields["error_message"] = error_message

            if metadata:
                update_fields["metadata"] = metadata

            # Update component
            result = self.components_collection.update_one(
                {"component_id": component_id},
                {"$set": update_fields}
            )

            if result.matched_count == 0:
                return {"success": False, "error": "Component not found"}

            # Get component info for logging
            component = self.components_collection.find_one({"component_id": component_id})
            if component:
                await self._log_activity(
                    automation_id=component["automation_id"],
                    action="component_status_updated",
                    details={
                        "component_id": component_id,
                        "new_status": status.value,
                        "error_message": error_message
                    },
                    organization_id=component["organization_id"]
                )

            return {"success": True, "component_id": component_id}

        except Exception as e:
            logger.error(f"Error updating component status: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_automation_deployment_status(self, automation_id: str) -> Dict[str, Any]:
        """Get comprehensive deployment status for an automation."""
        try:
            # Get automation config
            automation = self.automations_collection.find_one({"id": automation_id})
            if not automation:
                return {"error": "Automation not found"}

            # Get deployed components
            components = list(self.components_collection.find({"automation_id": automation_id}))

            # Calculate overall status
            if not components:
                overall_status = "not_deployed"
            else:
                component_statuses = [c["status"] for c in components]
                if all(s == "deployed" for s in component_statuses):
                    overall_status = "deployed"
                elif any(s == "failed" for s in component_statuses):
                    overall_status = "failed"
                elif any(s == "deploying" for s in component_statuses):
                    overall_status = "deploying"
                else:
                    overall_status = "partial"

            # Get deployment history
            deployment_history = list(self.deployments_collection.find(
                {"automation_id": automation_id}
            ).sort("started_at", -1).limit(5))

            # Get recent activity
            recent_activity = list(self.activity_log_collection.find(
                {"automation_id": automation_id}
            ).sort("timestamp", -1).limit(10))

            # Calculate metrics
            metrics = {
                "total_components": len(components),
                "deployed_components": len([c for c in components if c["status"] == "deployed"]),
                "failed_components": len([c for c in components if c["status"] == "failed"]),
                "last_deployment": deployment_history[0]["started_at"] if deployment_history else None,
                "uptime_hours": 0  # Calculate based on deployment time
            }

            if deployment_history and deployment_history[0].get("started_at"):
                deployment_time = deployment_history[0]["started_at"]
                uptime_delta = datetime.now(timezone.utc) - deployment_time
                metrics["uptime_hours"] = round(uptime_delta.total_seconds() / 3600, 1)

            return {
                "automation_id": automation_id,
                "automation_name": automation.get("automationName", "Unknown"),
                "overall_status": overall_status,
                "automation_status": automation.get("status", "unknown"),
                "components": [
                    {
                        "component_id": c["component_id"],
                        "component_type": c["component_type"],
                        "status": c["status"],
                        "deployed_at": c.get("deployed_at"),
                        "last_activity": c.get("last_activity"),
                        "error_message": c.get("error_message"),
                        "deployment_info": c.get("deployment_info", {})
                    }
                    for c in components
                ],
                "metrics": metrics,
                "deployment_history": [
                    {
                        "deployment_id": d["deployment_id"],
                        "status": d["status"],
                        "started_at": d["started_at"],
                        "initiated_by": d.get("initiated_by", "unknown")
                    }
                    for d in deployment_history
                ],
                "recent_activity": [
                    {
                        "action": a["action"],
                        "timestamp": a["timestamp"],
                        "details": a.get("details", {})
                    }
                    for a in recent_activity
                ]
            }

        except Exception as e:
            logger.error(f"Error getting automation deployment status: {str(e)}")
            return {"error": str(e)}

    async def get_vapi_agent_deployments(self, organization_id: str = None) -> List[Dict[str, Any]]:
        """Get all deployed VAPI agents with their status."""
        try:
            query_filter = {"component_type": ComponentType.VAPI_AGENT.value}
            if organization_id:
                query_filter["organization_id"] = organization_id

            vapi_components = list(self.components_collection.find(query_filter))

            deployments = []
            for component in vapi_components:
                # Get automation info
                automation = self.automations_collection.find_one({"id": component["automation_id"]})

                deployment_info = {
                    "component_id": component["component_id"],
                    "automation_id": component["automation_id"],
                    "automation_name": automation.get("automationName", "Unknown") if automation else "Unknown",
                    "assistant_id": component["deployment_info"].get("assistant_id"),
                    "phone_number_id": component["deployment_info"].get("phone_number_id"),
                    "status": component["status"],
                    "deployed_at": component.get("deployed_at"),
                    "last_activity": component.get("last_activity"),
                    "error_message": component.get("error_message"),
                    "config": component.get("config", {}),
                    "organization_id": component["organization_id"]
                }
                deployments.append(deployment_info)

            return deployments

        except Exception as e:
            logger.error(f"Error getting VAPI agent deployments: {str(e)}")
            return []

    async def get_n8n_workflow_deployments(self, organization_id: str = None) -> List[Dict[str, Any]]:
        """Get all deployed N8N workflows with their status."""
        try:
            query_filter = {"component_type": ComponentType.N8N_WORKFLOW.value}
            if organization_id:
                query_filter["organization_id"] = organization_id

            n8n_components = list(self.components_collection.find(query_filter))

            deployments = []
            for component in n8n_components:
                # Get automation info
                automation = self.automations_collection.find_one({"id": component["automation_id"]})

                deployment_info = {
                    "component_id": component["component_id"],
                    "automation_id": component["automation_id"],
                    "automation_name": automation.get("automationName", "Unknown") if automation else "Unknown",
                    "workflow_id": component["deployment_info"].get("workflow_id"),
                    "workflow_name": component["deployment_info"].get("workflow_name"),
                    "webhook_url": component["deployment_info"].get("webhook_url"),
                    "status": component["status"],
                    "deployed_at": component.get("deployed_at"),
                    "last_activity": component.get("last_activity"),
                    "error_message": component.get("error_message"),
                    "config": component.get("config", {}),
                    "organization_id": component["organization_id"]
                }
                deployments.append(deployment_info)

            return deployments

        except Exception as e:
            logger.error(f"Error getting N8N workflow deployments: {str(e)}")
            return []

    async def get_tenant_deployment_summary(self, organization_id: str) -> Dict[str, Any]:
        """Get deployment summary for a tenant."""
        try:
            # Get all automations for tenant
            automations = list(self.automations_collection.find({"userId": organization_id}))

            # Get all components for tenant
            components = list(self.components_collection.find({"organization_id": organization_id}))

            # Calculate statistics
            total_automations = len(automations)
            deployed_automations = len([a for a in automations if a.get("status") == "deployed"])
            total_components = len(components)
            active_components = len([c for c in components if c["status"] == "deployed"])
            failed_components = len([c for c in components if c["status"] == "failed"])

            # Component breakdown
            component_breakdown = {}
            for component in components:
                comp_type = component["component_type"]
                if comp_type not in component_breakdown:
                    component_breakdown[comp_type] = {"total": 0, "deployed": 0, "failed": 0}

                component_breakdown[comp_type]["total"] += 1
                if component["status"] == "deployed":
                    component_breakdown[comp_type]["deployed"] += 1
                elif component["status"] == "failed":
                    component_breakdown[comp_type]["failed"] += 1

            # Recent activity
            recent_activity = list(self.activity_log_collection.find(
                {"organization_id": organization_id}
            ).sort("timestamp", -1).limit(20))

            return {
                "organization_id": organization_id,
                "summary": {
                    "total_automations": total_automations,
                    "deployed_automations": deployed_automations,
                    "total_components": total_components,
                    "active_components": active_components,
                    "failed_components": failed_components,
                    "success_rate": round((active_components / total_components * 100) if total_components > 0 else 0, 1)
                },
                "component_breakdown": component_breakdown,
                "recent_activity": [
                    {
                        "action": a["action"],
                        "automation_id": a.get("automation_id"),
                        "timestamp": a["timestamp"],
                        "details": a.get("details", {})
                    }
                    for a in recent_activity
                ]
            }

        except Exception as e:
            logger.error(f"Error getting tenant deployment summary: {str(e)}")
            return {"error": str(e)}

    async def _log_activity(
        self,
        automation_id: str,
        action: str,
        details: Dict[str, Any],
        organization_id: str
    ) -> None:
        """Log deployment activity."""
        try:
            activity_doc = {
                "activity_id": str(uuid.uuid4()),
                "automation_id": automation_id,
                "organization_id": organization_id,
                "action": action,
                "details": details,
                "timestamp": datetime.now(timezone.utc)
            }

            self.activity_log_collection.insert_one(activity_doc)

            # Clean up old activity logs (keep last 30 days)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            self.activity_log_collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })

        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")

    async def stop_automation_deployment(self, automation_id: str, stopped_by: str = "user") -> Dict[str, Any]:
        """Stop a deployed automation and all its components."""
        try:
            # Update automation status
            self.automations_collection.update_one(
                {"id": automation_id},
                {"$set": {"status": "stopped", "updatedAt": datetime.now(timezone.utc)}}
            )

            # Update all components to stopped
            self.components_collection.update_many(
                {"automation_id": automation_id},
                {"$set": {
                    "status": DeploymentStatus.STOPPED.value,
                    "last_activity": datetime.now(timezone.utc)
                }}
            )

            # Get automation info for logging
            automation = self.automations_collection.find_one({"id": automation_id})
            organization_id = automation.get("userId") if automation else "unknown"

            # Log activity
            await self._log_activity(
                automation_id=automation_id,
                action="automation_stopped",
                details={"stopped_by": stopped_by},
                organization_id=organization_id
            )

            return {"success": True, "automation_id": automation_id}

        except Exception as e:
            logger.error(f"Error stopping automation deployment: {str(e)}")
            return {"success": False, "error": str(e)}

    async def restart_automation_deployment(self, automation_id: str, restarted_by: str = "user") -> Dict[str, Any]:
        """Restart a stopped automation deployment."""
        try:
            # Update automation status
            self.automations_collection.update_one(
                {"id": automation_id},
                {"$set": {"status": "deployed", "updatedAt": datetime.now(timezone.utc)}}
            )

            # Update all stopped components to deployed
            self.components_collection.update_many(
                {
                    "automation_id": automation_id,
                    "status": DeploymentStatus.STOPPED.value
                },
                {"$set": {
                    "status": DeploymentStatus.DEPLOYED.value,
                    "last_activity": datetime.now(timezone.utc)
                }}
            )

            # Get automation info for logging
            automation = self.automations_collection.find_one({"id": automation_id})
            organization_id = automation.get("userId") if automation else "unknown"

            # Log activity
            await self._log_activity(
                automation_id=automation_id,
                action="automation_restarted",
                details={"restarted_by": restarted_by},
                organization_id=organization_id
            )

            return {"success": True, "automation_id": automation_id}

        except Exception as e:
            logger.error(f"Error restarting automation deployment: {str(e)}")
            return {"success": False, "error": str(e)}