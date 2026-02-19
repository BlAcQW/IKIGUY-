"""
Comprehensive Automation Health Monitoring Service

Monitors automation health, VAPI call metrics, n8n workflow performance,
and campaign analytics with real-time alerts and detailed reporting.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID
import httpx
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel, Field
from decimal import Decimal

from ..mongo import get_collection
from .vonage_cost_monitoring_service import get_vonage_cost_service, VonageCostRecord

logger = logging.getLogger(__name__)

class AutomationHealth(BaseModel):
    """Automation health status model."""
    automation_id: str
    template_id: str
    organization_id: str  # Reason: Changed from organization_id for multi-org support
    status: str = Field(..., pattern="^(healthy|warning|critical|inactive)$")
    last_execution: Optional[datetime] = None
    success_rate: float = Field(ge=0, le=1)
    error_count: int = Field(ge=0)
    total_executions: int = Field(ge=0)
    avg_execution_time: float = Field(ge=0)
    issues: List[str] = []
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class VAPICallMetrics(BaseModel):
    """VAPI call metrics model."""
    agent_id: str
    call_id: str
    organization_id: str  # Reason: Changed from organization_id for multi-org support
    automation_id: Optional[str] = None

    # Call details
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: str = Field(..., pattern="^(in_progress|completed|failed|abandoned)$")

    # Performance metrics
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=10)
    intent_accuracy: Optional[float] = Field(None, ge=0, le=1)
    response_time_avg: Optional[float] = Field(None, ge=0)

    # Cost tracking
    cost_breakdown: Dict[str, float] = {}
    total_cost: float = Field(ge=0)

    # Vonage cost tracking
    vonage_transaction_id: Optional[str] = None
    vonage_cost_record: Optional[Dict[str, Any]] = None  # Store as dict for MongoDB compatibility
    estimated_vonage_cost: Optional[float] = None
    actual_vonage_cost: Optional[float] = None

    # Function calls
    functions_called: List[str] = Field(default_factory=list)
    workflow_triggers: int = Field(default=0, ge=0)

    # Quality metrics
    interruptions_count: int = Field(default=0, ge=0)
    silence_duration: float = Field(default=0.0, ge=0)
    transcript_length: int = Field(default=0, ge=0)

class CampaignPerformance(BaseModel):
    """Campaign performance metrics model."""
    campaign_id: str
    template_id: str
    organization_id: str  # Reason: Changed from organization_id for multi-org support

    # Performance metrics
    total_calls: int = Field(ge=0)
    successful_calls: int = Field(ge=0)
    failed_calls: int = Field(ge=0)
    abandoned_calls: int = Field(ge=0)

    # Conversion metrics
    conversions: int = Field(ge=0)
    conversion_rate: float = Field(ge=0, le=1)
    avg_call_duration: float = Field(ge=0)

    # Cost metrics
    total_cost: float = Field(ge=0)
    cost_per_call: float = Field(ge=0)
    cost_per_conversion: Optional[float] = Field(None, ge=0)

    # Quality metrics
    avg_satisfaction: Optional[float] = Field(None, ge=1, le=10)
    avg_sentiment: Optional[float] = Field(None, ge=-1, le=1)

    # Time periods
    period_start: datetime
    period_end: datetime
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AutomationMonitoringService:
    """Service for monitoring automation health and performance."""

    def __init__(self):
        self.health_collection: AsyncIOMotorCollection = get_collection("automation_health")
        self.metrics_collection: AsyncIOMotorCollection = get_collection("vapi_call_metrics")
        self.campaign_performance_collection: AsyncIOMotorCollection = get_collection("campaign_performance")
        self.alerts_collection: AsyncIOMotorCollection = get_collection("monitoring_alerts")

        # Health check thresholds
        self.success_rate_threshold = 0.85  # 85% success rate minimum
        self.error_count_threshold = 10     # 10 errors per hour maximum
        self.response_time_threshold = 5.0  # 5 seconds maximum response time

    async def record_vapi_call_metrics(self, call_data: Dict[str, Any]) -> str:
        """Record VAPI call metrics from webhook data with integrated Vonage cost tracking."""
        try:
            # Integrate Vonage cost tracking
            vonage_cost_record = None
            estimated_vonage_cost = None
            actual_vonage_cost = None
            vonage_transaction_id = None

            # Track Vonage costs if call has completed
            if call_data.get("endedAt") and call_data.get("durationSeconds"):
                try:
                    vonage_service = await get_vonage_cost_service()

                    # Extract phone number from call data
                    phone_number = call_data.get("call", {}).get("phoneNumber") or call_data.get("phoneNumber")

                    if phone_number and call_data.get("durationSeconds"):
                        # Track VAPI call cost with Vonage
                        vonage_cost_record = await vonage_service.track_vapi_call_cost(
                            vapi_call_id=call_data.get("call", {}).get("id"),
                            phone_number=phone_number,
                            duration=call_data.get("durationSeconds")
                        )

                        if vonage_cost_record:
                            estimated_vonage_cost = float(vonage_cost_record.cost_amount)
                            vonage_transaction_id = vonage_cost_record.transaction_id
                            logger.info(f"Tracked Vonage cost for VAPI call {call_data.get('call', {}).get('id')}: ${estimated_vonage_cost}")

                except Exception as e:
                    logger.error(f"Error tracking Vonage costs: {str(e)}")

            # Extract metrics from VAPI webhook payload
            call_metrics = VAPICallMetrics(
                agent_id=call_data.get("assistant", {}).get("id"),
                call_id=call_data.get("call", {}).get("id"),
                organization_id=call_data.get("metadata", {}).get("tenantId", "default"),
                automation_id=call_data.get("metadata", {}).get("automationId"),
                started_at=datetime.fromisoformat(call_data.get("startedAt", datetime.utcnow().isoformat())),
                ended_at=datetime.fromisoformat(call_data.get("endedAt")) if call_data.get("endedAt") else None,
                duration_seconds=call_data.get("durationSeconds"),
                status="completed" if call_data.get("endedAt") else "in_progress",
                sentiment_score=self._extract_sentiment_score(call_data),
                satisfaction_rating=self._extract_satisfaction_rating(call_data),
                intent_accuracy=self._calculate_intent_accuracy(call_data),
                response_time_avg=self._calculate_avg_response_time(call_data),
                cost_breakdown=call_data.get("costBreakdown", {}),
                total_cost=call_data.get("cost", 0),
                # Vonage cost integration
                vonage_transaction_id=vonage_transaction_id,
                vonage_cost_record=vonage_cost_record.dict() if vonage_cost_record else None,
                estimated_vonage_cost=estimated_vonage_cost,
                actual_vonage_cost=actual_vonage_cost,
                functions_called=self._extract_function_calls(call_data),
                workflow_triggers=len(call_data.get("toolCalls", [])),
                interruptions_count=call_data.get("interruptionsCount", 0),
                silence_duration=call_data.get("silenceDuration", 0),
                transcript_length=len(call_data.get("transcript", ""))
            )

            # Store metrics
            result = await self.metrics_collection.insert_one(call_metrics.dict())

            # Update automation health based on this call
            if call_metrics.automation_id:
                await self._update_automation_health(call_metrics)

            # Check for alerts
            await self._check_call_quality_alerts(call_metrics)

            logger.info(f"Recorded VAPI call metrics for call {call_metrics.call_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error recording VAPI call metrics: {str(e)}")
            raise

    async def update_automation_health(self, automation_id: str, organization_id: str) -> AutomationHealth:
        """Update automation health status based on recent activity."""
        try:
            # Get recent executions (last 24 hours)
            since = datetime.utcnow() - timedelta(hours=24)

            # Query recent calls for this automation
            calls_cursor = self.metrics_collection.find({
                "automation_id": automation_id,
                "organization_id": organization_id,
                "started_at": {"$gte": since}
            })
            calls = await calls_cursor.to_list(length=None)

            if not calls:
                # No recent activity
                health_status = AutomationHealth(
                    automation_id=automation_id,
                    template_id="unknown",
                    organization_id=organization_id,
                    status="inactive",
                    success_rate=0.0,
                    error_count=0,
                    total_executions=0,
                    avg_execution_time=0.0,
                    issues=["No recent activity in the last 24 hours"]
                )
            else:
                # Calculate health metrics
                total_calls = len(calls)
                successful_calls = len([c for c in calls if c.get("status") == "completed"])
                failed_calls = len([c for c in calls if c.get("status") == "failed"])

                success_rate = successful_calls / total_calls if total_calls > 0 else 0
                avg_duration = sum(c.get("duration_seconds", 0) for c in calls) / total_calls if total_calls > 0 else 0

                # Determine status and issues
                issues = []
                if success_rate < self.success_rate_threshold:
                    issues.append(f"Low success rate: {success_rate:.1%}")
                if failed_calls > self.error_count_threshold:
                    issues.append(f"High error count: {failed_calls} failures")
                if avg_duration > self.response_time_threshold:
                    issues.append(f"Slow response times: {avg_duration:.1f}s average")

                # Determine overall status
                if not issues:
                    status = "healthy"
                elif len(issues) == 1 or success_rate > 0.7:
                    status = "warning"
                else:
                    status = "critical"

                health_status = AutomationHealth(
                    automation_id=automation_id,
                    template_id=calls[0].get("template_id", "unknown"),
                    organization_id=organization_id,
                    status=status,
                    last_execution=max(c.get("started_at") for c in calls) if calls else None,
                    success_rate=success_rate,
                    error_count=failed_calls,
                    total_executions=total_calls,
                    avg_execution_time=avg_duration,
                    issues=issues
                )

            # Upsert health record
            await self.health_collection.replace_one(
                {"automation_id": automation_id, "organization_id": organization_id},
                health_status.dict(),
                upsert=True
            )

            # Send alerts if critical
            if health_status.status == "critical":
                await self._send_health_alert(health_status)

            return health_status

        except Exception as e:
            logger.error(f"Error updating automation health: {str(e)}")
            raise

    async def get_campaign_performance(self, campaign_id: str, organization_id: str,
                                     period_start: datetime, period_end: datetime) -> CampaignPerformance:
        """Get comprehensive campaign performance metrics."""
        try:
            # Query calls for this campaign in the time period
            calls_cursor = self.metrics_collection.find({
                "organization_id": organization_id,
                "started_at": {"$gte": period_start, "$lte": period_end}
            })
            calls = await calls_cursor.to_list(length=None)

            # Filter by campaign_id if we have that metadata
            campaign_calls = [c for c in calls if c.get("campaign_id") == campaign_id]

            if not campaign_calls:
                # Return empty metrics
                return CampaignPerformance(
                    campaign_id=campaign_id,
                    template_id="unknown",
                    organization_id=organization_id,
                    period_start=period_start,
                    period_end=period_end
                )

            # Calculate performance metrics
            total_calls = len(campaign_calls)
            successful_calls = len([c for c in campaign_calls if c.get("status") == "completed"])
            failed_calls = len([c for c in campaign_calls if c.get("status") == "failed"])
            abandoned_calls = len([c for c in campaign_calls if c.get("status") == "abandoned"])

            # Calculate conversions (calls with positive sentiment and high satisfaction)
            conversions = len([
                c for c in campaign_calls
                if c.get("sentiment_score", 0) > 0.3 and c.get("satisfaction_rating", 0) > 7
            ])

            conversion_rate = conversions / total_calls if total_calls > 0 else 0
            avg_call_duration = sum(c.get("duration_seconds", 0) for c in campaign_calls) / total_calls if total_calls > 0 else 0

            # Calculate costs
            total_cost = sum(c.get("total_cost", 0) for c in campaign_calls)
            cost_per_call = total_cost / total_calls if total_calls > 0 else 0
            cost_per_conversion = total_cost / conversions if conversions > 0 else None

            # Calculate quality metrics
            satisfaction_scores = [c.get("satisfaction_rating") for c in campaign_calls if c.get("satisfaction_rating")]
            sentiment_scores = [c.get("sentiment_score") for c in campaign_calls if c.get("sentiment_score")]

            avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else None
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else None

            performance = CampaignPerformance(
                campaign_id=campaign_id,
                template_id=campaign_calls[0].get("template_id", "unknown"),
                organization_id=organization_id,
                total_calls=total_calls,
                successful_calls=successful_calls,
                failed_calls=failed_calls,
                abandoned_calls=abandoned_calls,
                conversions=conversions,
                conversion_rate=conversion_rate,
                avg_call_duration=avg_call_duration,
                total_cost=total_cost,
                cost_per_call=cost_per_call,
                cost_per_conversion=cost_per_conversion,
                avg_satisfaction=avg_satisfaction,
                avg_sentiment=avg_sentiment,
                period_start=period_start,
                period_end=period_end
            )

            # Store performance record
            await self.campaign_performance_collection.replace_one(
                {
                    "campaign_id": campaign_id,
                    "organization_id": organization_id,
                    "period_start": period_start,
                    "period_end": period_end
                },
                performance.dict(),
                upsert=True
            )

            return performance

        except Exception as e:
            logger.error(f"Error calculating campaign performance: {str(e)}")
            raise

    async def get_automation_health_dashboard(self, organization_id: str) -> Dict[str, Any]:
        """Get comprehensive automation health dashboard data."""
        try:
            # Get all automation health records for tenant
            health_cursor = self.health_collection.find({"organization_id": organization_id})
            health_records = await health_cursor.to_list(length=None)

            # Aggregate health statistics
            total_automations = len(health_records)
            healthy_count = len([h for h in health_records if h.get("status") == "healthy"])
            warning_count = len([h for h in health_records if h.get("status") == "warning"])
            critical_count = len([h for h in health_records if h.get("status") == "critical"])
            inactive_count = len([h for h in health_records if h.get("status") == "inactive"])

            # Calculate overall health score
            health_score = (healthy_count * 1.0 + warning_count * 0.7 + critical_count * 0.3) / total_automations if total_automations > 0 else 0

            # Get recent metrics (last 24 hours)
            since = datetime.utcnow() - timedelta(hours=24)
            recent_calls = await self.metrics_collection.count_documents({
                "organization_id": organization_id,
                "started_at": {"$gte": since}
            })

            # Get cost summary for last 24 hours
            cost_pipeline = [
                {"$match": {"organization_id": organization_id, "started_at": {"$gte": since}}},
                {"$group": {"_id": None, "total_cost": {"$sum": "$total_cost"}}}
            ]
            cost_result = await self.metrics_collection.aggregate(cost_pipeline).to_list(length=1)
            total_cost_24h = cost_result[0]["total_cost"] if cost_result else 0

            # Get top issues
            all_issues = []
            for health in health_records:
                all_issues.extend(health.get("issues", []))

            issue_counts = {}
            for issue in all_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1

            top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]

            return {
                "overview": {
                    "total_automations": total_automations,
                    "health_score": health_score,
                    "healthy_count": healthy_count,
                    "warning_count": warning_count,
                    "critical_count": critical_count,
                    "inactive_count": inactive_count
                },
                "recent_activity": {
                    "calls_24h": recent_calls,
                    "cost_24h": total_cost_24h
                },
                "top_issues": [{"issue": issue, "count": count} for issue, count in top_issues],
                "automations": health_records,
                "updated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting automation health dashboard: {str(e)}")
            raise

    def _extract_sentiment_score(self, call_data: Dict[str, Any]) -> Optional[float]:
        """Extract sentiment score from call data."""
        analysis = call_data.get("analysis", {})
        structured_data = analysis.get("structuredData", {})

        # Try to extract sentiment from structured data
        sentiment = structured_data.get("sentiment", "")
        if isinstance(sentiment, str):
            if "positive" in sentiment.lower():
                return 0.7
            elif "negative" in sentiment.lower():
                return -0.7
            elif "neutral" in sentiment.lower():
                return 0.0

        return None

    def _extract_satisfaction_rating(self, call_data: Dict[str, Any]) -> Optional[int]:
        """Extract satisfaction rating from call data."""
        analysis = call_data.get("analysis", {})
        structured_data = analysis.get("structuredData", {})

        # Try to extract score from structured data
        score = structured_data.get("score")
        if isinstance(score, (int, float)) and 1 <= score <= 10:
            return int(score)

        return None

    def _calculate_intent_accuracy(self, call_data: Dict[str, Any]) -> Optional[float]:
        """Calculate intent recognition accuracy."""
        # This would be based on successful function calls vs total user inputs
        tool_calls = call_data.get("toolCalls", [])
        messages = call_data.get("messages", [])
        user_messages = [m for m in messages if m.get("role") == "user"]

        if not user_messages:
            return None

        # Simple heuristic: successful tool calls / user messages
        successful_calls = len([tc for tc in tool_calls if tc.get("status") == "success"])
        return min(successful_calls / len(user_messages), 1.0)

    def _calculate_avg_response_time(self, call_data: Dict[str, Any]) -> Optional[float]:
        """Calculate average response time."""
        messages = call_data.get("messages", [])
        response_times = []

        for i in range(1, len(messages)):
            prev_msg = messages[i-1]
            curr_msg = messages[i]

            if (prev_msg.get("role") == "user" and curr_msg.get("role") == "assistant"):
                prev_time = prev_msg.get("time", 0)
                curr_time = curr_msg.get("time", 0)
                if curr_time > prev_time:
                    response_times.append((curr_time - prev_time) / 1000)  # Convert to seconds

        return sum(response_times) / len(response_times) if response_times else None

    def _extract_function_calls(self, call_data: Dict[str, Any]) -> List[str]:
        """Extract function names that were called."""
        tool_calls = call_data.get("toolCalls", [])
        return [tc.get("function", {}).get("name") for tc in tool_calls if tc.get("function", {}).get("name")]

    async def _update_automation_health(self, call_metrics: VAPICallMetrics):
        """Update automation health based on a single call."""
        if not call_metrics.automation_id:
            return

        await self.update_automation_health(call_metrics.automation_id, call_metrics.organization_id)

    async def _check_call_quality_alerts(self, call_metrics: VAPICallMetrics):
        """Check if call quality warrants an alert."""
        alerts = []

        # Check for poor sentiment
        if call_metrics.sentiment_score and call_metrics.sentiment_score < -0.5:
            alerts.append({
                "type": "poor_sentiment",
                "severity": "warning",
                "message": f"Call {call_metrics.call_id} had very negative sentiment: {call_metrics.sentiment_score:.2f}"
            })

        # Check for low satisfaction
        if call_metrics.satisfaction_rating and call_metrics.satisfaction_rating < 3:
            alerts.append({
                "type": "low_satisfaction",
                "severity": "warning",
                "message": f"Call {call_metrics.call_id} had low satisfaction rating: {call_metrics.satisfaction_rating}/10"
            })

        # Check for high cost
        if call_metrics.total_cost > 1.0:  # $1 threshold
            alerts.append({
                "type": "high_cost",
                "severity": "info",
                "message": f"Call {call_metrics.call_id} had high cost: ${call_metrics.total_cost:.2f}"
            })

        # Store alerts
        for alert in alerts:
            alert.update({
                "call_id": call_metrics.call_id,
                "agent_id": call_metrics.agent_id,
                "organization_id": call_metrics.organization_id,
                "created_at": datetime.utcnow()
            })
            await self.alerts_collection.insert_one(alert)

    async def _send_health_alert(self, health_status: AutomationHealth):
        """Send alert for critical automation health."""
        alert = {
            "type": "automation_health_critical",
            "severity": "critical",
            "automation_id": health_status.automation_id,
            "organization_id": health_status.organization_id,
            "message": f"Automation {health_status.automation_id} is in critical state",
            "details": {
                "success_rate": health_status.success_rate,
                "error_count": health_status.error_count,
                "issues": health_status.issues
            },
            "created_at": datetime.utcnow()
        }

        await self.alerts_collection.insert_one(alert)
        logger.warning(f"Critical health alert for automation {health_status.automation_id}: {health_status.issues}")

    async def get_vapi_call_metrics(self, organization_id: str, start_date: datetime, end_date: datetime,
                                   automation_id: Optional[str] = None, campaign_id: Optional[str] = None,
                                   limit: int = 100) -> List[VAPICallMetrics]:
        """Get VAPI call metrics with filtering options."""
        try:
            # For now, return empty list to verify authentication is working
            # TODO: Implement actual database query once authentication is confirmed
            return []

        except Exception as e:
            logger.error(f"Error getting VAPI call metrics: {str(e)}")
            raise

    async def get_automation_health(self, organization_id: str, automation_id: Optional[str] = None,
                                   campaign_id: Optional[str] = None, status: Optional[str] = None) -> List[AutomationHealth]:
        """Get automation health records with filtering options."""
        try:
            # For now, return empty list to verify authentication is working
            # TODO: Implement actual database query once authentication is confirmed
            return []

        except Exception as e:
            logger.error(f"Error getting automation health: {str(e)}")
            raise

    async def get_campaign_performance(self, organization_id: str, campaign_id: Optional[str] = None,
                                     start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[CampaignPerformance]:
        """Get campaign performance records with filtering options."""
        try:
            # For now, return empty list to verify authentication is working
            # TODO: Implement actual database query once authentication is confirmed
            return []

        except Exception as e:
            logger.error(f"Error getting campaign performance: {str(e)}")
            raise

    async def update_automation_health_from_api(self, health_data: Dict[str, Any]) -> str:
        """Update automation health from API request data."""
        try:
            # Create AutomationHealth object
            health_status = AutomationHealth(
                automation_id=health_data["automation_id"],
                template_id=health_data.get("template_id", "unknown"),
                organization_id=health_data["organization_id"],
                status=health_data["status"],
                last_execution=health_data.get("last_execution"),
                success_rate=health_data["success_rate"],
                error_count=health_data["error_count"],
                total_executions=health_data.get("total_executions", 0),
                avg_execution_time=health_data.get("avg_execution_time", 0.0),
                issues=health_data.get("issues", [])
            )

            # Upsert health record
            result = await self.health_collection.replace_one(
                {"automation_id": health_status.automation_id, "organization_id": health_status.organization_id},
                health_status.dict(),
                upsert=True
            )

            # Send alerts if critical
            if health_status.status == "critical":
                await self._send_health_alert(health_status)

            return str(result.upserted_id) if result.upserted_id else "updated"

        except Exception as e:
            logger.error(f"Error updating automation health: {str(e)}")
            raise

    async def update_vonage_costs_from_api(self, start_date: datetime, end_date: datetime) -> int:
        """Update actual Vonage costs from Vonage API for recorded calls."""
        try:
            vonage_service = await get_vonage_cost_service()

            # Fetch actual costs from Vonage API
            actual_costs = await vonage_service.fetch_vonage_costs(start_date, end_date)

            updated_count = 0
            for cost_record in actual_costs:
                # Try to match with existing call metrics by transaction ID or VAPI call ID
                query = {}
                if cost_record.vapi_call_id:
                    query["call_id"] = cost_record.vapi_call_id
                elif cost_record.transaction_id:
                    query["vonage_transaction_id"] = cost_record.transaction_id

                if query:
                    # Update call metrics with actual cost
                    update_result = await self.metrics_collection.update_one(
                        query,
                        {
                            "$set": {
                                "actual_vonage_cost": float(cost_record.cost_amount),
                                "vonage_cost_record": cost_record.dict(),
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )

                    if update_result.modified_count > 0:
                        updated_count += 1
                        logger.info(f"Updated actual Vonage cost for call {cost_record.vapi_call_id}: ${cost_record.cost_amount}")

            logger.info(f"Updated {updated_count} call records with actual Vonage costs")
            return updated_count

        except Exception as e:
            logger.error(f"Error updating Vonage costs from API: {str(e)}")
            raise

    async def get_cost_summary_with_vonage(self, organization_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get comprehensive cost summary including Vonage costs."""
        try:
            # Get VAPI call metrics for the period
            calls_cursor = self.metrics_collection.find({
                "organization_id": organization_id,
                "started_at": {"$gte": start_date, "$lte": end_date}
            })
            calls = await calls_cursor.to_list(length=None)

            # Calculate cost metrics
            total_vapi_cost = sum(call.get("total_cost", 0) for call in calls)
            total_estimated_vonage_cost = sum(call.get("estimated_vonage_cost", 0) for call in calls if call.get("estimated_vonage_cost"))
            total_actual_vonage_cost = sum(call.get("actual_vonage_cost", 0) for call in calls if call.get("actual_vonage_cost"))

            # Use actual costs where available, otherwise use estimates
            total_vonage_cost = total_actual_vonage_cost if total_actual_vonage_cost > 0 else total_estimated_vonage_cost

            # Get Vonage service for additional cost analysis
            vonage_service = await get_vonage_cost_service()
            vonage_summary = await vonage_service.get_cost_summary(start_date, end_date, include_estimates=True)

            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "vapi_costs": {
                    "total_vapi_cost": total_vapi_cost,
                    "total_calls": len(calls)
                },
                "vonage_costs": {
                    "total_vonage_cost": total_vonage_cost,
                    "estimated_costs": total_estimated_vonage_cost,
                    "actual_costs": total_actual_vonage_cost,
                    "has_actual_data": total_actual_vonage_cost > 0,
                    "cost_breakdown": vonage_summary.cost_breakdown
                },
                "combined_metrics": {
                    "total_cost": total_vapi_cost + total_vonage_cost,
                    "cost_per_call": (total_vapi_cost + total_vonage_cost) / len(calls) if calls else 0,
                    "vonage_percentage": (total_vonage_cost / (total_vapi_cost + total_vonage_cost)) * 100 if (total_vapi_cost + total_vonage_cost) > 0 else 0
                },
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating cost summary: {str(e)}")
            raise

    async def get_high_cost_calls(self, organization_id: str, cost_threshold: float = 1.0, limit: int = 50) -> List[Dict[str, Any]]:
        """Get calls with high costs for analysis."""
        try:
            # Query calls with high total costs (VAPI + Vonage)
            pipeline = [
                {
                    "$match": {
                        "organization_id": organization_id,
                        "$expr": {
                            "$gt": [
                                {
                                    "$add": [
                                        "$total_cost",
                                        {"$ifNull": ["$actual_vonage_cost", {"$ifNull": ["$estimated_vonage_cost", 0]}]}
                                    ]
                                },
                                cost_threshold
                            ]
                        }
                    }
                },
                {
                    "$addFields": {
                        "combined_cost": {
                            "$add": [
                                "$total_cost",
                                {"$ifNull": ["$actual_vonage_cost", {"$ifNull": ["$estimated_vonage_cost", 0]}]}
                            ]
                        }
                    }
                },
                {"$sort": {"combined_cost": -1}},
                {"$limit": limit}
            ]

            high_cost_calls = await self.metrics_collection.aggregate(pipeline).to_list(length=None)

            logger.info(f"Found {len(high_cost_calls)} high-cost calls above ${cost_threshold}")
            return high_cost_calls

        except Exception as e:
            logger.error(f"Error getting high-cost calls: {str(e)}")
            raise

# Global service instance
automation_monitoring_service = AutomationMonitoringService()