"""
Comprehensive Analytics Service for Automations, Campaigns, and Costs.

Provides detailed analytics for all integrations including VAPI, N8N, Vonage,
automation health monitoring, and cost tracking.
"""

import asyncio
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from ..mongo import get_collection
from .cost_record_service import CostRecordService

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Comprehensive analytics service for automations and integrations."""

    def __init__(self):
        """Initialize analytics service with full functionality."""
        self.enabled = True
        self.base_url = "https://api.ailabsafrica.com"

        # Collections
        self.analytics_collection = get_collection("analytics_data")
        self.automations_collection = get_collection("automation_configs")
        self.campaigns_collection = get_collection("campaigns")
        self.health_collection = get_collection("automation_health")

        logger.info("Analytics service initialized with full functionality")

    async def record_operation(self, analytics_data: Dict[str, Any]) -> None:
        """
        Record analytics data for operations with MongoDB persistence.

        Args:
            analytics_data: Operation data to record
        """
        try:
            record = {
                "timestamp": datetime.utcnow(),
                "operation": analytics_data.get("operation"),
                "service": analytics_data.get("service"),
                "automation_id": analytics_data.get("automation_id"),
                "success": analytics_data.get("success", False),
                "duration_ms": analytics_data.get("duration_ms", 0),
                "cost": analytics_data.get("cost", 0.0),
                "user_id": analytics_data.get("user_id"),
                "tenant_id": analytics_data.get("tenant_id"),
                "metadata": analytics_data.get("metadata", {}),
                "error": analytics_data.get("error"),
                "response_time": analytics_data.get("response_time", 0)
            }

            self.analytics_collection.insert_one(record)
            logger.debug(f"Analytics recorded: {analytics_data.get('operation')} - {analytics_data.get('success')}")

        except Exception as e:
            logger.error(f"Failed to record analytics: {str(e)}")

    async def get_automation_analytics(
        self,
        automation_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive automation analytics.

        Args:
            automation_id: Specific automation ID or None for all
            start_date: Start date for analytics period
            end_date: End date for analytics period

        Returns:
            Comprehensive automation analytics
        """
        try:
            # Default to last 30 days if no dates provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # Build aggregation pipeline
            match_filter = {
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
            if automation_id:
                match_filter["automation_id"] = automation_id

            pipeline = [
                {"$match": match_filter},
                {"$group": {
                    "_id": "$automation_id",
                    "total_operations": {"$sum": 1},
                    "successful_operations": {"$sum": {"$cond": ["$success", 1, 0]}},
                    "total_cost": {"$sum": "$cost"},
                    "avg_duration": {"$avg": "$duration_ms"},
                    "avg_response_time": {"$avg": "$response_time"},
                    "services_used": {"$addToSet": "$service"},
                    "last_operation": {"$max": "$timestamp"},
                    "error_count": {"$sum": {"$cond": ["$success", 0, 1]}}
                }},
                {"$sort": {"total_operations": -1}}
            ]

            results = list(self.analytics_collection.aggregate(pipeline))

            # Enrich with automation details
            enriched_results = []
            for result in results:
                automation_id = result["_id"]
                if automation_id:
                    automation = self.automations_collection.find_one({"_id": automation_id})
                    if automation:
                        result["automation_name"] = automation.get("automationName", "Unknown")
                        result["template_id"] = automation.get("templateId")
                        result["status"] = automation.get("status")
                        result["created_at"] = automation.get("createdAt")

                # Calculate success rate
                result["success_rate"] = (
                    result["successful_operations"] / result["total_operations"] * 100
                    if result["total_operations"] > 0 else 0
                )

                enriched_results.append(result)

            return {
                "automation_analytics": enriched_results,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "summary": {
                    "total_automations": len(enriched_results),
                    "total_operations": sum(r["total_operations"] for r in enriched_results),
                    "total_cost": sum(r["total_cost"] for r in enriched_results),
                    "avg_success_rate": (
                        sum(r["success_rate"] for r in enriched_results) / len(enriched_results)
                        if enriched_results else 0
                    )
                }
            }

        except Exception as e:
            logger.error(f"Failed to get automation analytics: {str(e)}")
            return {"error": str(e)}

    async def get_vapi_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get VAPI call analytics.

        Args:
            start_date: Start date for analytics
            end_date: End date for analytics

        Returns:
            VAPI analytics data
        """
        try:
            # Default to last 7 days for VAPI data
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=7)

            # Try to get VAPI data from MCP service
            from ...mcp import get_mcp_manager

            analytics_data = {
                "service": "vapi",
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "calls": {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "average_duration": 0,
                    "total_cost": 0,
                    "success_rate": 0
                },
                "assistants": [],
                "phone_numbers": [],
                "cost_breakdown": {
                    "voice_cost": 0,
                    "llm_cost": 0,
                    "total_cost": 0
                }
            }

            # Get calls from our analytics collection
            match_filter = {
                "timestamp": {"$gte": start_date, "$lte": end_date},
                "service": "vapi"
            }

            calls_data = list(self.analytics_collection.find(match_filter))

            if calls_data:
                analytics_data["calls"]["total_calls"] = len(calls_data)
                analytics_data["calls"]["successful_calls"] = len([c for c in calls_data if c.get("success")])
                analytics_data["calls"]["failed_calls"] = len([c for c in calls_data if not c.get("success")])
                analytics_data["calls"]["total_cost"] = sum(c.get("cost", 0) for c in calls_data)
                analytics_data["calls"]["average_duration"] = (
                    sum(c.get("duration_ms", 0) for c in calls_data) / len(calls_data)
                    if calls_data else 0
                )
                analytics_data["calls"]["success_rate"] = (
                    analytics_data["calls"]["successful_calls"] / analytics_data["calls"]["total_calls"] * 100
                    if analytics_data["calls"]["total_calls"] > 0 else 0
                )

            return analytics_data

        except Exception as e:
            logger.error(f"Failed to get VAPI analytics: {str(e)}")
            return {"error": str(e), "service": "vapi"}

    async def get_n8n_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get N8N workflow analytics.

        Args:
            start_date: Start date for analytics
            end_date: End date for analytics

        Returns:
            N8N analytics data
        """
        try:
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=7)

            analytics_data = {
                "service": "n8n",
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "workflows": {
                    "total_workflows": 0,
                    "active_workflows": 0,
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                    "success_rate": 0
                },
                "execution_details": [],
                "performance": {
                    "avg_execution_time": 0,
                    "fastest_execution": 0,
                    "slowest_execution": 0
                }
            }

            # Get N8N data from our analytics collection
            match_filter = {
                "timestamp": {"$gte": start_date, "$lte": end_date},
                "service": "n8n"
            }

            n8n_data = list(self.analytics_collection.find(match_filter))

            if n8n_data:
                analytics_data["workflows"]["total_executions"] = len(n8n_data)
                analytics_data["workflows"]["successful_executions"] = len([e for e in n8n_data if e.get("success")])
                analytics_data["workflows"]["failed_executions"] = len([e for e in n8n_data if not e.get("success")])
                analytics_data["workflows"]["success_rate"] = (
                    analytics_data["workflows"]["successful_executions"] / analytics_data["workflows"]["total_executions"] * 100
                    if analytics_data["workflows"]["total_executions"] > 0 else 0
                )

                durations = [e.get("duration_ms", 0) for e in n8n_data if e.get("duration_ms")]
                if durations:
                    analytics_data["performance"]["avg_execution_time"] = sum(durations) / len(durations)
                    analytics_data["performance"]["fastest_execution"] = min(durations)
                    analytics_data["performance"]["slowest_execution"] = max(durations)

            return analytics_data

        except Exception as e:
            logger.error(f"Failed to get N8N analytics: {str(e)}")
            return {"error": str(e), "service": "n8n"}

    async def get_cost_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "service"
    ) -> Dict[str, Any]:
        """
        Get comprehensive cost analytics across all services.

        Args:
            start_date: Start date for analytics
            end_date: End date for analytics
            group_by: How to group costs (service, automation, tenant)

        Returns:
            Cost analytics data
        """
        try:
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # Build aggregation pipeline for cost analysis
            match_filter = {
                "timestamp": {"$gte": start_date, "$lte": end_date},
                "cost": {"$exists": True, "$gt": 0}
            }

            group_field = f"${group_by}"
            pipeline = [
                {"$match": match_filter},
                {"$group": {
                    "_id": group_field,
                    "total_cost": {"$sum": "$cost"},
                    "operation_count": {"$sum": 1},
                    "avg_cost_per_operation": {"$avg": "$cost"},
                    "max_cost": {"$max": "$cost"},
                    "min_cost": {"$min": "$cost"}
                }},
                {"$sort": {"total_cost": -1}}
            ]

            cost_breakdown = list(self.analytics_collection.aggregate(pipeline))

            # Calculate totals
            total_cost = sum(item["total_cost"] for item in cost_breakdown)
            total_operations = sum(item["operation_count"] for item in cost_breakdown)

            # Daily cost trend
            daily_pipeline = [
                {"$match": match_filter},
                {"$group": {
                    "_id": {
                        "year": {"$year": "$timestamp"},
                        "month": {"$month": "$timestamp"},
                        "day": {"$dayOfMonth": "$timestamp"}
                    },
                    "daily_cost": {"$sum": "$cost"},
                    "daily_operations": {"$sum": 1}
                }},
                {"$sort": {"_id": 1}}
            ]

            daily_costs = list(self.analytics_collection.aggregate(daily_pipeline))

            return {
                "cost_analytics": {
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    "summary": {
                        "total_cost": total_cost,
                        "total_operations": total_operations,
                        "average_cost_per_operation": total_cost / total_operations if total_operations > 0 else 0,
                        "cost_by_" + group_by: cost_breakdown
                    },
                    "trends": {
                        "daily_costs": daily_costs
                    }
                }
            }

        except Exception as e:
            logger.error(f"Failed to get cost analytics: {str(e)}")
            return {"error": str(e)}

    async def get_profit_margin_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tenant_id: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get profit margin analytics from internal cost tracking (ADMIN ONLY).

        This shows actual costs paid to providers vs. what we charged customers.

        Args:
            start_date: Start date for analytics
            end_date: End date for analytics
            tenant_id: Filter by tenant
            provider: Filter by provider

        Returns:
            Profit margin analytics with revenue, costs, profit, and margins
        """
        try:
            from ..mongo import get_database
            db = get_database()
            cost_service = CostRecordService(db.client, db.name)

            # Get cost summary
            summary = await cost_service.get_cost_summary(
                start_date=start_date,
                end_date=end_date,
                tenant_id=tenant_id,
                provider=provider
            )

            # Get provider breakdown
            breakdown = await cost_service.get_cost_breakdown_by_provider(
                start_date=start_date,
                end_date=end_date
            )

            return {
                "profit_analytics": {
                    "period": {
                        "start_date": start_date.isoformat() if start_date else None,
                        "end_date": end_date.isoformat() if end_date else None
                    },
                    "summary": summary,
                    "breakdown_by_provider": breakdown,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Failed to get profit margin analytics: {str(e)}")
            return {"error": str(e), "profit_analytics": None}

    async def get_automation_health_status(self, automation_id: str) -> Dict[str, Any]:
        """
        Get real-time health status for a specific automation.

        Args:
            automation_id: Automation configuration ID

        Returns:
            Health status with all components
        """
        try:
            health_data = {
                "automation_id": automation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "overall_health": "unknown",
                "health_score": 0,
                "components": {
                    "automation": {"status": "unknown", "details": {}},
                    "vapi": {"status": "unknown", "details": {}},
                    "n8n": {"status": "unknown", "details": {}},
                    "integrations": {"status": "unknown", "details": {}},
                    "custom_tools": {"status": "unknown", "details": {}}
                },
                "last_activity": None,
                "recommendations": []
            }

            # Get automation details
            automation = self.automations_collection.find_one({"_id": automation_id})
            if not automation:
                health_data["components"]["automation"]["status"] = "not_found"
                return health_data

            health_data["components"]["automation"]["status"] = "healthy"
            health_data["components"]["automation"]["details"] = {
                "deployment_status": automation.get("status"),
                "automation_name": automation.get("automationName"),
                "template_id": automation.get("templateId"),
                "vapi_configured": bool(automation.get("vapiAgent")),
                "n8n_configured": bool(automation.get("n8nWorkflow"))
            }

            # Check recent activity
            recent_activity = self.analytics_collection.find_one(
                {"automation_id": automation_id},
                sort=[("timestamp", -1)]
            )
            if recent_activity:
                health_data["last_activity"] = recent_activity["timestamp"].isoformat()

            # Get VAPI health
            vapi_config = automation.get("vapiAgent", {})
            if vapi_config:
                health_data["components"]["vapi"]["status"] = "configured"
                health_data["components"]["vapi"]["details"] = {
                    "system_prompt_configured": bool(vapi_config.get("systemPrompt")),
                    "voice_settings_configured": bool(vapi_config.get("voiceSettings")),
                    "tools_count": len(vapi_config.get("tools", []))
                }

            # Get N8N health
            n8n_config = automation.get("n8nWorkflow", {})
            if n8n_config:
                health_data["components"]["n8n"]["status"] = "configured"
                health_data["components"]["n8n"]["details"] = {
                    "workflow_name": n8n_config.get("workflowName"),
                    "endpoints_configured": len(n8n_config.get("endpoints", {}))
                }

            # Get integrations health
            integrations = automation.get("integrations", {})
            enabled_integrations = [k for k, v in integrations.items() if v.get("enabled", False)]
            health_data["components"]["integrations"]["status"] = "healthy" if enabled_integrations else "none_enabled"
            health_data["components"]["integrations"]["details"] = {
                "total_integrations": len(integrations),
                "enabled_integrations": len(enabled_integrations),
                "integration_names": enabled_integrations
            }

            # Get custom tools health
            custom_tools = automation.get("customTools", {})
            if custom_tools.get("enabled", False):
                selected_tools = custom_tools.get("selectedTools", [])
                health_data["components"]["custom_tools"]["status"] = "enabled"
                health_data["components"]["custom_tools"]["details"] = {
                    "tools_count": len(selected_tools),
                    "tool_names": selected_tools
                }
            else:
                health_data["components"]["custom_tools"]["status"] = "disabled"

            # Calculate overall health score
            component_scores = []
            for component, data in health_data["components"].items():
                if data["status"] == "healthy" or data["status"] == "configured" or data["status"] == "enabled":
                    component_scores.append(100)
                elif data["status"] == "disabled" or data["status"] == "none_enabled":
                    component_scores.append(50)
                else:
                    component_scores.append(0)

            health_data["health_score"] = sum(component_scores) / len(component_scores) if component_scores else 0

            # Determine overall health
            if health_data["health_score"] >= 80:
                health_data["overall_health"] = "healthy"
            elif health_data["health_score"] >= 60:
                health_data["overall_health"] = "warning"
            else:
                health_data["overall_health"] = "critical"

            # Generate recommendations
            if health_data["components"]["vapi"]["status"] != "configured":
                health_data["recommendations"].append("Configure VAPI voice agent settings")
            if health_data["components"]["n8n"]["status"] != "configured":
                health_data["recommendations"].append("Set up N8N workflow automation")
            if health_data["components"]["integrations"]["status"] == "none_enabled":
                health_data["recommendations"].append("Enable at least one integration service")

            # Store health status
            health_record = {
                **health_data,
                "timestamp": datetime.utcnow()
            }
            self.health_collection.replace_one(
                {"automation_id": automation_id},
                health_record,
                upsert=True
            )

            return health_data

        except Exception as e:
            logger.error(f"Failed to get automation health: {str(e)}")
            return {
                "automation_id": automation_id,
                "error": str(e),
                "overall_health": "error"
            }

    async def get_tenant_analytics(
        self,
        tenant_id: str,
        service: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific tenant.

        Args:
            tenant_id: Tenant identifier
            service: Service name
            start_date: Start date for analytics
            end_date: End date for analytics

        Returns:
            Analytics data dictionary
        """
        try:
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            match_filter = {
                "tenant_id": tenant_id,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
            if service != "all":
                match_filter["service"] = service

            pipeline = [
                {"$match": match_filter},
                {"$group": {
                    "_id": "$service",
                    "operations_count": {"$sum": 1},
                    "successful_operations": {"$sum": {"$cond": ["$success", 1, 0]}},
                    "total_cost": {"$sum": "$cost"},
                    "avg_duration": {"$avg": "$duration_ms"},
                    "avg_response_time": {"$avg": "$response_time"}
                }}
            ]

            results = list(self.analytics_collection.aggregate(pipeline))

            return {
                "tenant_id": tenant_id,
                "service": service,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "service_breakdown": results,
                "summary": {
                    "total_operations": sum(r["operations_count"] for r in results),
                    "total_cost": sum(r["total_cost"] for r in results),
                    "overall_success_rate": (
                        sum(r["successful_operations"] for r in results) /
                        sum(r["operations_count"] for r in results) * 100
                        if any(r["operations_count"] for r in results) else 0
                    )
                }
            }

        except Exception as e:
            logger.error(f"Failed to get tenant analytics: {str(e)}")
            return {"error": str(e)}

    async def get_service_metrics(self, service: str) -> Dict[str, Any]:
        """
        Get overall metrics for a service.

        Args:
            service: Service name

        Returns:
            Service metrics dictionary
        """
        try:
            # Get metrics for the last 24 hours
            start_time = datetime.utcnow() - timedelta(hours=24)

            match_filter = {
                "service": service,
                "timestamp": {"$gte": start_time}
            }

            pipeline = [
                {"$match": match_filter},
                {"$group": {
                    "_id": None,
                    "total_operations": {"$sum": 1},
                    "successful_operations": {"$sum": {"$cond": ["$success", 1, 0]}},
                    "total_cost": {"$sum": "$cost"},
                    "avg_response_time": {"$avg": "$response_time"},
                    "avg_duration": {"$avg": "$duration_ms"}
                }}
            ]

            result = list(self.analytics_collection.aggregate(pipeline))

            if result:
                data = result[0]
                success_rate = (
                    data["successful_operations"] / data["total_operations"] * 100
                    if data["total_operations"] > 0 else 0
                )
                error_rate = 100 - success_rate

                return {
                    "service": service,
                    "period": "last_24_hours",
                    "total_operations": data["total_operations"],
                    "success_rate": success_rate,
                    "error_rate": error_rate,
                    "average_response_time": data["avg_response_time"] or 0,
                    "average_duration": data["avg_duration"] or 0,
                    "total_cost": data["total_cost"] or 0
                }
            else:
                return {
                    "service": service,
                    "period": "last_24_hours",
                    "total_operations": 0,
                    "success_rate": 0.0,
                    "error_rate": 0.0,
                    "average_response_time": 0.0,
                    "average_duration": 0.0,
                    "total_cost": 0.0,
                    "message": f"No operations recorded for {service} in the last 24 hours"
                }

        except Exception as e:
            logger.error(f"Failed to get service metrics: {str(e)}")
            return {"error": str(e)}


# Create singleton instance
analytics_service = AnalyticsService()