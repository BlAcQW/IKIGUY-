"""
Insurance Customer Service Monitoring Service

Specialized service for monitoring insurance customer service automation,
fraud detection, SLA tracking, and regulatory compliance.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
import httpx
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel, Field

from .automation_monitoring_service import AutomationMonitoringService
from ..mongo import get_collection

logger = logging.getLogger(__name__)


class InsuranceServiceMetrics(BaseModel):
    """Insurance customer service-specific metrics model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    automation_id: str
    campaign_id: Optional[str] = None
    tenant_id: str

    # Service request details
    service_request_id: str
    customer_id: str
    policy_number: str
    inquiry_type: str  # claims, billing, policy_changes, coverage_questions
    service_category: str  # customer_service, claims, underwriting, billing

    # Call metrics
    call_duration: Optional[float] = None  # seconds
    call_sentiment: Optional[float] = Field(None, ge=0, le=1)
    customer_satisfaction: Optional[int] = Field(None, ge=1, le=10)
    agent_performance: Optional[float] = Field(None, ge=0, le=1)

    # Resolution metrics
    resolution_status: str = Field(..., pattern="^(resolved|escalated|pending|transferred)$")
    first_call_resolution: bool = False
    resolution_time: Optional[float] = None  # minutes
    escalation_level: int = Field(default=0, ge=0, le=3)

    # Fraud detection
    fraud_risk_score: Optional[float] = Field(None, ge=0, le=1)
    fraud_indicators: List[str] = Field(default_factory=list)
    fraud_investigation_triggered: bool = False

    # SLA compliance
    sla_target_time: Optional[float] = None  # minutes
    sla_met: bool = True
    response_time: Optional[float] = None  # minutes to first response

    # Quality metrics
    call_quality_score: Optional[float] = Field(None, ge=0, le=1)
    compliance_score: Optional[float] = Field(None, ge=0, le=1)
    professional_score: Optional[float] = Field(None, ge=0, le=1)

    # Routing efficiency
    routing_accuracy: Optional[float] = Field(None, ge=0, le=1)
    transfers_required: int = Field(default=0, ge=0)
    routing_time: Optional[float] = None  # seconds

    # Cost metrics
    handling_cost: Optional[float] = None
    resolution_cost: Optional[float] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ServiceLevelMetrics(BaseModel):
    """Service level agreement metrics."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    period_start: datetime
    period_end: datetime

    # Response time SLAs
    average_response_time: float = 0.0  # minutes
    sla_response_target: float = 2.0  # minutes
    response_sla_compliance: float = Field(ge=0, le=1)

    # Resolution time SLAs
    average_resolution_time: float = 0.0  # minutes
    sla_resolution_target: float = 15.0  # minutes
    resolution_sla_compliance: float = Field(ge=0, le=1)

    # Quality SLAs
    average_customer_satisfaction: float = 0.0
    satisfaction_target: float = 8.0
    satisfaction_sla_compliance: float = Field(ge=0, le=1)

    # Efficiency metrics
    first_call_resolution_rate: float = Field(ge=0, le=1)
    transfer_rate: float = Field(ge=0, le=1)
    escalation_rate: float = Field(ge=0, le=1)

    # Overall SLA score
    overall_sla_score: float = Field(ge=0, le=100)
    sla_grade: str = Field(..., pattern="^(A|B|C|D|F)$")

    generated_at: datetime = Field(default_factory=datetime.utcnow)


class FraudDetectionMetrics(BaseModel):
    """Fraud detection metrics for insurance claims and inquiries."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    period_start: datetime
    period_end: datetime

    # Detection metrics
    total_inquiries_analyzed: int = 0
    fraud_alerts_generated: int = 0
    confirmed_fraud_cases: int = 0
    false_positive_rate: float = Field(ge=0, le=1)
    detection_accuracy: float = Field(ge=0, le=1)

    # Risk distribution
    low_risk_cases: int = 0
    medium_risk_cases: int = 0
    high_risk_cases: int = 0
    critical_risk_cases: int = 0

    # Financial impact
    potential_fraud_amount: float = 0.0
    prevented_fraud_amount: float = 0.0
    investigation_costs: float = 0.0

    # Response metrics
    average_investigation_time: float = 0.0  # hours
    cases_referred_to_siu: int = 0  # Special Investigation Unit

    generated_at: datetime = Field(default_factory=datetime.utcnow)


class InsuranceCustomerServiceMonitoringService(AutomationMonitoringService):
    """Specialized monitoring service for insurance customer service automation."""

    def __init__(self):
        super().__init__()
        self.service_metrics_collection = "insurance_service_metrics"
        self.sla_metrics_collection = "service_level_metrics"
        self.fraud_metrics_collection = "fraud_detection_metrics"

    async def record_service_metrics(self, service_data: Dict[str, Any]) -> str:
        """Record insurance customer service-specific metrics."""
        try:
            # Flatten nested data structure if needed
            flattened_data = self._flatten_service_data(service_data)

            # Calculate derived metrics
            flattened_data = self._calculate_service_metrics(flattened_data)

            # Assess fraud risk
            flattened_data = await self._assess_fraud_risk(flattened_data)

            # Check SLA compliance
            flattened_data = self._check_sla_compliance(flattened_data)

            # Create service metrics record
            service_metrics = InsuranceServiceMetrics(**flattened_data)

            # Store in database
            collection = get_collection(self.service_metrics_collection)
            result = await collection.insert_one(service_metrics.model_dump())

            # Update real-time analytics
            await self._update_service_analytics(service_metrics)

            # Check for fraud alerts
            if service_metrics.fraud_investigation_triggered:
                await self._trigger_fraud_investigation(service_metrics)

            logger.info(f"Recorded insurance service metrics: {result.inserted_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error recording service metrics: {str(e)}")
            raise

    def _calculate_service_metrics(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate derived service metrics."""
        # Calculate resolution time if available
        if service_data.get("call_start_time") and service_data.get("resolution_time"):
            start_time = datetime.fromisoformat(service_data["call_start_time"])
            resolution_time = datetime.fromisoformat(service_data["resolution_time"])
            service_data["resolution_time"] = (resolution_time - start_time).total_seconds() / 60

        # Calculate agent performance score
        service_data["agent_performance"] = self._calculate_agent_performance(service_data)

        # Calculate call quality score
        service_data["call_quality_score"] = self._calculate_call_quality(service_data)

        # Calculate routing accuracy
        service_data["routing_accuracy"] = self._calculate_routing_accuracy(service_data)

        # Determine first call resolution
        service_data["first_call_resolution"] = (
            service_data.get("resolution_status") == "resolved" and
            service_data.get("transfers_required", 0) == 0 and
            service_data.get("escalation_level", 0) == 0
        )

        return service_data

    def _calculate_agent_performance(self, service_data: Dict[str, Any]) -> float:
        """Calculate agent performance score based on multiple factors."""
        performance_score = 0.5  # Base score

        # Customer satisfaction impact
        satisfaction = service_data.get("customer_satisfaction", 5)
        if satisfaction >= 9:
            performance_score += 0.3
        elif satisfaction >= 7:
            performance_score += 0.2
        elif satisfaction >= 5:
            performance_score += 0.1
        else:
            performance_score -= 0.2

        # Resolution efficiency
        if service_data.get("first_call_resolution", False):
            performance_score += 0.2

        # Call duration efficiency
        call_duration = service_data.get("call_duration", 600)  # Default 10 minutes
        if call_duration < 300:  # < 5 minutes
            performance_score += 0.1
        elif call_duration > 1200:  # > 20 minutes
            performance_score -= 0.1

        # Professional score
        professional_score = service_data.get("professional_score", 0.8)
        performance_score += (professional_score - 0.5) * 0.2

        return max(0.0, min(1.0, performance_score))

    def _calculate_call_quality(self, service_data: Dict[str, Any]) -> float:
        """Calculate overall call quality score."""
        quality_factors = []

        # Sentiment score
        if service_data.get("call_sentiment"):
            quality_factors.append(service_data["call_sentiment"])

        # Professional score
        if service_data.get("professional_score"):
            quality_factors.append(service_data["professional_score"])

        # Compliance score
        if service_data.get("compliance_score"):
            quality_factors.append(service_data["compliance_score"])

        # Customer satisfaction (normalized to 0-1)
        if service_data.get("customer_satisfaction"):
            satisfaction_normalized = (service_data["customer_satisfaction"] - 1) / 9
            quality_factors.append(satisfaction_normalized)

        return sum(quality_factors) / len(quality_factors) if quality_factors else 0.5

    def _calculate_routing_accuracy(self, service_data: Dict[str, Any]) -> float:
        """Calculate routing accuracy based on transfers and escalations."""
        base_accuracy = 1.0

        # Penalize for transfers
        transfers = service_data.get("transfers_required", 0)
        base_accuracy -= transfers * 0.2

        # Penalize for escalations
        escalations = service_data.get("escalation_level", 0)
        base_accuracy -= escalations * 0.3

        # Bonus for correct department routing
        inquiry_type = service_data.get("inquiry_type", "")
        service_category = service_data.get("service_category", "")
        if self._is_correct_routing(inquiry_type, service_category):
            base_accuracy += 0.1

        return max(0.0, min(1.0, base_accuracy))

    def _is_correct_routing(self, inquiry_type: str, service_category: str) -> bool:
        """Check if inquiry was routed to the correct department."""
        correct_routing = {
            "claims": "claims",
            "billing": "billing",
            "policy_changes": "underwriting",
            "coverage_questions": "customer_service"
        }
        return correct_routing.get(inquiry_type) == service_category

    async def _assess_fraud_risk(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess fraud risk based on inquiry patterns and customer data."""
        fraud_score = 0.0
        fraud_indicators = []

        # Customer behavior indicators
        if service_data.get("recent_policy_changes", 0) > 2:
            fraud_score += 0.2
            fraud_indicators.append("multiple_recent_policy_changes")

        # Claim patterns
        if service_data.get("inquiry_type") == "claims":
            recent_claims = service_data.get("recent_claims_count", 0)
            if recent_claims > 3:
                fraud_score += 0.3
                fraud_indicators.append("high_claim_frequency")

            claim_amount = service_data.get("claim_amount", 0)
            if claim_amount > 50000:  # High value claims
                fraud_score += 0.2
                fraud_indicators.append("high_value_claim")

        # Communication patterns
        call_sentiment = service_data.get("call_sentiment", 0.5)
        if call_sentiment < 0.3:  # Very negative sentiment
            fraud_score += 0.1
            fraud_indicators.append("suspicious_communication_pattern")

        # Geographic indicators
        if service_data.get("call_location_mismatch", False):
            fraud_score += 0.25
            fraud_indicators.append("location_inconsistency")

        # Time-based indicators
        call_time = service_data.get("call_time", datetime.now())
        if isinstance(call_time, str):
            call_time = datetime.fromisoformat(call_time)
        if call_time.hour < 6 or call_time.hour > 22:  # Unusual hours
            fraud_score += 0.1
            fraud_indicators.append("unusual_call_time")

        # Set fraud risk level
        if fraud_score > 0.7:
            risk_level = "critical"
            investigation_triggered = True
        elif fraud_score > 0.5:
            risk_level = "high"
            investigation_triggered = False
        elif fraud_score > 0.3:
            risk_level = "medium"
            investigation_triggered = False
        else:
            risk_level = "low"
            investigation_triggered = False

        service_data["fraud_risk_score"] = min(fraud_score, 1.0)
        service_data["fraud_indicators"] = fraud_indicators
        service_data["fraud_investigation_triggered"] = investigation_triggered

        return service_data

    def _check_sla_compliance(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check SLA compliance for response and resolution times."""
        # Default SLA targets (can be configured per tenant)
        response_sla = service_data.get("sla_response_target", 2.0)  # 2 minutes
        resolution_sla = service_data.get("sla_resolution_target", 15.0)  # 15 minutes

        # Check response time SLA
        response_time = service_data.get("response_time", 0)
        if response_time <= response_sla:
            response_sla_met = True
        else:
            response_sla_met = False

        # Check resolution time SLA
        resolution_time = service_data.get("resolution_time", 0)
        if resolution_time <= resolution_sla:
            resolution_sla_met = True
        else:
            resolution_sla_met = False

        # Overall SLA compliance
        service_data["sla_met"] = response_sla_met and resolution_sla_met

        return service_data

    async def _trigger_fraud_investigation(self, service_metrics: InsuranceServiceMetrics):
        """Trigger fraud investigation workflow for high-risk cases."""
        try:
            # Create fraud investigation record
            investigation_data = {
                "service_request_id": service_metrics.service_request_id,
                "customer_id": service_metrics.customer_id,
                "policy_number": service_metrics.policy_number,
                "fraud_score": service_metrics.fraud_risk_score,
                "fraud_indicators": service_metrics.fraud_indicators,
                "investigation_status": "initiated",
                "created_at": datetime.utcnow()
            }

            fraud_collection = get_collection("fraud_investigations")
            await fraud_collection.insert_one(investigation_data)

            # Send alert to fraud team (in production, would integrate with alerting system)
            logger.warning(f"Fraud investigation triggered for customer {service_metrics.customer_id}")

        except Exception as e:
            logger.error(f"Error triggering fraud investigation: {str(e)}")

    async def _update_service_analytics(self, service_metrics: InsuranceServiceMetrics):
        """Update real-time service analytics."""
        try:
            collection = get_collection(self.service_metrics_collection + "_daily")

            # Get current day metrics
            today = datetime.utcnow().date()
            period_start = datetime.combine(today, datetime.min.time())
            period_end = datetime.combine(today, datetime.max.time())

            # Update or create analytics record
            await collection.update_one(
                {
                    "tenant_id": service_metrics.tenant_id,
                    "period_start": {"$gte": period_start},
                    "period_end": {"$lte": period_end}
                },
                {
                    "$inc": {
                        "total_service_requests": 1,
                        f"{service_metrics.inquiry_type}_requests": 1,
                        "first_call_resolutions": 1 if service_metrics.first_call_resolution else 0,
                        "fraud_alerts": 1 if service_metrics.fraud_investigation_triggered else 0
                    },
                    "$push": {
                        "satisfaction_scores": service_metrics.customer_satisfaction,
                        "resolution_times": service_metrics.resolution_time
                    },
                    "$set": {
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error updating service analytics: {str(e)}")

    async def get_sla_dashboard(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get comprehensive SLA compliance dashboard."""
        try:
            # Get service metrics for the period
            metrics = await self._get_service_metrics(tenant_id, start_date, end_date)

            if not metrics:
                return {"error": "No data available for the specified period"}

            # Calculate SLA metrics
            total_requests = len(metrics)

            # Response time analysis
            response_times = [m.get("response_time", 0) for m in metrics if m.get("response_time")]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            response_sla_met = len([t for t in response_times if t <= 2.0])
            response_sla_rate = (response_sla_met / len(response_times) * 100) if response_times else 100

            # Resolution time analysis
            resolution_times = [m.get("resolution_time", 0) for m in metrics if m.get("resolution_time")]
            avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
            resolution_sla_met = len([t for t in resolution_times if t <= 15.0])
            resolution_sla_rate = (resolution_sla_met / len(resolution_times) * 100) if resolution_times else 100

            # Customer satisfaction analysis
            satisfaction_scores = [m.get("customer_satisfaction", 0) for m in metrics if m.get("customer_satisfaction")]
            avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
            satisfaction_target_met = len([s for s in satisfaction_scores if s >= 8])
            satisfaction_sla_rate = (satisfaction_target_met / len(satisfaction_scores) * 100) if satisfaction_scores else 100

            # Efficiency metrics
            first_call_resolutions = len([m for m in metrics if m.get("first_call_resolution", False)])
            fcr_rate = (first_call_resolutions / total_requests * 100) if total_requests > 0 else 0

            transfers = sum(m.get("transfers_required", 0) for m in metrics)
            transfer_rate = (transfers / total_requests * 100) if total_requests > 0 else 0

            escalations = len([m for m in metrics if m.get("escalation_level", 0) > 0])
            escalation_rate = (escalations / total_requests * 100) if total_requests > 0 else 0

            # Overall SLA score calculation
            sla_components = [response_sla_rate, resolution_sla_rate, satisfaction_sla_rate]
            overall_sla_score = sum(sla_components) / len(sla_components)

            # SLA grade
            if overall_sla_score >= 95:
                sla_grade = "A"
            elif overall_sla_score >= 90:
                sla_grade = "B"
            elif overall_sla_score >= 80:
                sla_grade = "C"
            elif overall_sla_score >= 70:
                sla_grade = "D"
            else:
                sla_grade = "F"

            dashboard = {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "sla_overview": {
                    "overall_score": f"{overall_sla_score:.1f}%",
                    "sla_grade": sla_grade,
                    "total_requests": total_requests
                },
                "response_metrics": {
                    "average_response_time": f"{avg_response_time:.1f} minutes",
                    "sla_compliance": f"{response_sla_rate:.1f}%",
                    "sla_target": "2.0 minutes"
                },
                "resolution_metrics": {
                    "average_resolution_time": f"{avg_resolution_time:.1f} minutes",
                    "sla_compliance": f"{resolution_sla_rate:.1f}%",
                    "sla_target": "15.0 minutes"
                },
                "satisfaction_metrics": {
                    "average_satisfaction": f"{avg_satisfaction:.1f}/10",
                    "sla_compliance": f"{satisfaction_sla_rate:.1f}%",
                    "sla_target": "8.0/10"
                },
                "efficiency_metrics": {
                    "first_call_resolution_rate": f"{fcr_rate:.1f}%",
                    "transfer_rate": f"{transfer_rate:.1f}%",
                    "escalation_rate": f"{escalation_rate:.1f}%"
                },
                "recommendations": self._generate_sla_recommendations(
                    response_sla_rate, resolution_sla_rate, satisfaction_sla_rate, fcr_rate
                ),
                "generated_at": datetime.utcnow().isoformat()
            }

            return dashboard

        except Exception as e:
            logger.error(f"Error generating SLA dashboard: {str(e)}")
            return {"error": f"Failed to generate dashboard: {str(e)}"}

    async def _get_service_metrics(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get service metrics for period."""
        try:
            collection = get_collection(self.service_metrics_collection)
            query = {
                "tenant_id": tenant_id,
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }

            cursor = collection.find(query).sort("created_at", -1)
            return await cursor.to_list(length=10000)

        except Exception as e:
            logger.error(f"Error retrieving service metrics: {str(e)}")
            return []

    def _generate_sla_recommendations(
        self,
        response_sla_rate: float,
        resolution_sla_rate: float,
        satisfaction_sla_rate: float,
        fcr_rate: float
    ) -> List[str]:
        """Generate actionable SLA improvement recommendations."""
        recommendations = []

        # Response time recommendations
        if response_sla_rate < 90:
            recommendations.append("Optimize call routing to reduce response times")
            recommendations.append("Consider increasing agent capacity during peak hours")

        # Resolution time recommendations
        if resolution_sla_rate < 85:
            recommendations.append("Implement better knowledge management systems")
            recommendations.append("Provide additional training on common issue resolution")

        # Satisfaction recommendations
        if satisfaction_sla_rate < 90:
            recommendations.append("Focus on agent soft skills training")
            recommendations.append("Implement proactive customer follow-up procedures")

        # First call resolution recommendations
        if fcr_rate < 80:
            recommendations.append("Improve agent access to customer information")
            recommendations.append("Enhance intelligent routing to match inquiries with specialized agents")

        return recommendations

    def _flatten_service_data(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested service data structure to match InsuranceServiceMetrics model."""
        flattened = {}

        # Extract service request details
        if "service_request" in service_data:
            request = service_data["service_request"]
            flattened["service_request_id"] = request.get("id")
            flattened["inquiry_type"] = request.get("type")
            flattened["service_category"] = request.get("category")

        # Extract customer details
        if "customer" in service_data:
            customer = service_data["customer"]
            flattened["customer_id"] = customer.get("id")
            flattened["policy_number"] = customer.get("policy_number")

        # Extract call details
        if "call" in service_data:
            call = service_data["call"]
            flattened["call_duration"] = call.get("duration_seconds")
            flattened["call_sentiment"] = call.get("sentiment_score")
            flattened["customer_satisfaction"] = call.get("satisfaction_score")

        # Extract metadata
        if "metadata" in service_data:
            meta = service_data["metadata"]
            flattened["tenant_id"] = meta.get("tenantId")
            flattened["automation_id"] = meta.get("automationId")
            flattened["campaign_id"] = meta.get("campaignId")

        # Copy any already flat fields
        for key, value in service_data.items():
            if key not in ["service_request", "customer", "call", "metadata"] and key not in flattened:
                flattened[key] = value

        return flattened