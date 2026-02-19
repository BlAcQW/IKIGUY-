"""
Specialized Premium Collection Monitoring Service

Extends the automation monitoring service with insurance-specific
premium collection analytics, compliance tracking, and customer retention metrics.
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


class PremiumCollectionMetrics(BaseModel):
    """Premium collection-specific metrics model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    automation_id: str
    campaign_id: Optional[str] = None
    tenant_id: str

    # Collection details
    policy_number: str
    customer_id: str
    collection_amount: float
    collection_status: str = Field(..., pattern="^(scheduled|contacted|payment_plan|paid|failed|hardship)$")

    # Call metrics
    call_duration: Optional[float] = None  # seconds
    call_sentiment: Optional[float] = Field(None, ge=0, le=1)  # sentiment score
    empathy_score: Optional[float] = Field(None, ge=0, le=1)  # empathy rating
    collection_approach: Optional[str] = None  # compassionate, standard, firm

    # Payment metrics
    payment_method: Optional[str] = None
    payment_plan_created: bool = False
    payment_plan_duration: Optional[int] = None  # months
    immediate_payment: bool = False
    payment_amount: Optional[float] = None

    # Customer experience
    customer_satisfaction: Optional[int] = Field(None, ge=1, le=10)
    hardship_assessment: Optional[Dict[str, Any]] = None
    assistance_offered: List[str] = Field(default_factory=list)
    customer_retained: bool = True

    # Compliance tracking
    fdcpa_compliant: bool = True
    tcpa_compliant: bool = True
    call_recording_consent: bool = False
    compliance_violations: List[str] = Field(default_factory=list)

    # Performance metrics
    collection_success_rate: Optional[float] = Field(None, ge=0, le=1)
    time_to_resolution: Optional[float] = None  # hours
    follow_up_required: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CollectionAnalytics(BaseModel):
    """Aggregated collection analytics model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    period_start: datetime
    period_end: datetime

    # Collection performance
    total_collection_attempts: int = 0
    successful_collections: int = 0
    payment_plans_created: int = 0
    hardship_cases: int = 0
    failed_collections: int = 0

    # Financial metrics
    total_amount_attempted: float = 0.0
    total_amount_collected: float = 0.0
    average_collection_amount: float = 0.0
    collection_rate: float = Field(ge=0, le=1)

    # Customer experience
    average_customer_satisfaction: float = 0.0
    customer_retention_rate: float = Field(ge=0, le=1)
    average_empathy_score: float = Field(ge=0, le=1)

    # Compliance metrics
    compliance_rate: float = Field(ge=0, le=1)
    compliance_violations: int = 0

    # Efficiency metrics
    average_call_duration: float = 0.0  # seconds
    average_resolution_time: float = 0.0  # hours
    first_call_resolution_rate: float = Field(ge=0, le=1)

    generated_at: datetime = Field(default_factory=datetime.utcnow)


class PremiumCollectionMonitoringService(AutomationMonitoringService):
    """Specialized monitoring service for premium collection automation."""

    def __init__(self):
        super().__init__()
        self.collection_name = "premium_collection_metrics"
        self.analytics_collection_name = "collection_analytics"

    async def record_collection_metrics(self, collection_data: Dict[str, Any]) -> str:
        """Record premium collection-specific metrics with compliance tracking."""
        try:
            # Flatten nested data structure if needed
            flattened_data = self._flatten_collection_data(collection_data)

            # Calculate derived metrics
            flattened_data = self._calculate_collection_metrics(flattened_data)

            # Ensure compliance validation
            flattened_data = self._validate_compliance(flattened_data)

            # Create collection metrics record
            collection_metrics = PremiumCollectionMetrics(**flattened_data)

            # Store in database
            collection = get_collection(self.collection_name)
            result = await collection.insert_one(collection_metrics.model_dump())

            # Update real-time analytics
            await self._update_collection_analytics(collection_metrics)

            logger.info(f"Recorded collection metrics: {result.inserted_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error recording collection metrics: {str(e)}")
            raise

    def _calculate_collection_metrics(self, collection_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate derived collection metrics."""
        # Calculate empathy score based on call content
        collection_data["empathy_score"] = self._calculate_empathy_score(collection_data)

        # Calculate collection success rate
        collection_data["collection_success_rate"] = self._calculate_success_rate(collection_data)

        # Determine if customer was retained
        collection_data["customer_retained"] = self._assess_customer_retention(collection_data)

        # Calculate time to resolution
        if collection_data.get("call_start_time") and collection_data.get("resolution_time"):
            start_time = datetime.fromisoformat(collection_data["call_start_time"])
            resolution_time = datetime.fromisoformat(collection_data["resolution_time"])
            collection_data["time_to_resolution"] = (resolution_time - start_time).total_seconds() / 3600

        return collection_data

    def _calculate_empathy_score(self, collection_data: Dict[str, Any]) -> float:
        """Calculate empathy score based on interaction data."""
        empathy_score = 0.5  # Base score

        # Positive empathy indicators
        if collection_data.get("hardship_assessment"):
            empathy_score += 0.3

        if "payment_plan" in collection_data.get("assistance_offered", []):
            empathy_score += 0.2

        if collection_data.get("call_sentiment", 0.5) > 0.6:
            empathy_score += 0.2

        # Negative empathy indicators
        compliance_violations = collection_data.get("compliance_violations", [])
        if "aggressive_language" in compliance_violations:
            empathy_score -= 0.4
        if "threats_made" in compliance_violations:
            empathy_score -= 0.5

        return max(0.0, min(1.0, empathy_score))

    def _calculate_success_rate(self, collection_data: Dict[str, Any]) -> float:
        """Calculate collection success rate."""
        status = collection_data.get("collection_status", "failed")

        if status == "paid":
            return 1.0
        elif status == "payment_plan":
            return 0.8
        elif status == "hardship":
            return 0.6  # Partial success - customer engagement maintained
        elif status == "contacted":
            return 0.3
        else:
            return 0.0

    def _assess_customer_retention(self, collection_data: Dict[str, Any]) -> bool:
        """Assess if customer relationship was maintained."""
        # Customer retained if they didn't cancel their policy
        status = collection_data.get("collection_status", "failed")
        satisfaction = collection_data.get("customer_satisfaction", 5)

        if status in ["paid", "payment_plan", "hardship"] and satisfaction >= 6:
            return True
        elif status == "failed" and satisfaction < 4:
            return False
        else:
            return True  # Default to retained unless clear indication otherwise

    def _validate_compliance(self, collection_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate compliance with debt collection regulations."""
        violations = []

        # FDCPA compliance checks
        if collection_data.get("call_time"):
            call_time = datetime.fromisoformat(collection_data["call_time"])
            hour = call_time.hour
            if hour < 8 or hour > 21:  # Outside 8 AM - 9 PM
                violations.append("fdcpa_time_violation")
                collection_data["fdcpa_compliant"] = False

        # TCPA compliance checks
        if not collection_data.get("consent_obtained", False):
            violations.append("tcpa_consent_missing")
            collection_data["tcpa_compliant"] = False

        # Language compliance
        if collection_data.get("threatening_language", False):
            violations.append("threatening_language")
            collection_data["fdcpa_compliant"] = False

        collection_data["compliance_violations"] = violations

        return collection_data

    async def _update_collection_analytics(self, collection_metrics: PremiumCollectionMetrics):
        """Update real-time collection analytics."""
        try:
            collection = get_collection(self.analytics_collection_name)

            # Get current period analytics
            today = datetime.utcnow().date()
            period_start = datetime.combine(today, datetime.min.time())
            period_end = datetime.combine(today, datetime.max.time())

            # Update or create analytics record
            await collection.update_one(
                {
                    "tenant_id": collection_metrics.tenant_id,
                    "period_start": {"$gte": period_start},
                    "period_end": {"$lte": period_end}
                },
                {
                    "$inc": {
                        "total_collection_attempts": 1,
                        f"{collection_metrics.collection_status}_collections": 1,
                        "total_amount_attempted": collection_metrics.collection_amount
                    },
                    "$set": {
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error updating collection analytics: {str(e)}")

    async def get_collection_analytics(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[CollectionAnalytics]:
        """Get aggregated collection analytics for a period."""
        try:
            # Get collection metrics for the period
            metrics = await self.get_collection_metrics(tenant_id, start_date, end_date, limit=10000)

            if not metrics:
                return None

            # Calculate analytics
            total_attempts = len(metrics)
            successful = len([m for m in metrics if m.collection_status in ["paid", "payment_plan"]])
            payment_plans = len([m for m in metrics if m.payment_plan_created])
            hardship_cases = len([m for m in metrics if m.collection_status == "hardship"])
            failed = len([m for m in metrics if m.collection_status == "failed"])

            # Financial metrics
            total_attempted = sum(m.collection_amount for m in metrics)
            total_collected = sum(m.payment_amount for m in metrics if m.payment_amount)
            avg_amount = total_attempted / total_attempts if total_attempts > 0 else 0
            collection_rate = successful / total_attempts if total_attempts > 0 else 0

            # Customer experience metrics
            satisfaction_scores = [m.customer_satisfaction for m in metrics if m.customer_satisfaction]
            avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0

            empathy_scores = [m.empathy_score for m in metrics if m.empathy_score]
            avg_empathy = sum(empathy_scores) / len(empathy_scores) if empathy_scores else 0

            retention_rate = len([m for m in metrics if m.customer_retained]) / total_attempts if total_attempts > 0 else 0

            # Compliance metrics
            compliant_calls = len([m for m in metrics if m.fdcpa_compliant and m.tcpa_compliant])
            compliance_rate = compliant_calls / total_attempts if total_attempts > 0 else 0
            total_violations = sum(len(m.compliance_violations) for m in metrics)

            # Efficiency metrics
            call_durations = [m.call_duration for m in metrics if m.call_duration]
            avg_call_duration = sum(call_durations) / len(call_durations) if call_durations else 0

            resolution_times = [m.time_to_resolution for m in metrics if m.time_to_resolution]
            avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0

            first_call_resolutions = len([m for m in metrics if m.collection_status in ["paid", "payment_plan"] and not m.follow_up_required])
            first_call_rate = first_call_resolutions / total_attempts if total_attempts > 0 else 0

            analytics = CollectionAnalytics(
                tenant_id=tenant_id,
                period_start=start_date,
                period_end=end_date,
                total_collection_attempts=total_attempts,
                successful_collections=successful,
                payment_plans_created=payment_plans,
                hardship_cases=hardship_cases,
                failed_collections=failed,
                total_amount_attempted=total_attempted,
                total_amount_collected=total_collected,
                average_collection_amount=avg_amount,
                collection_rate=collection_rate,
                average_customer_satisfaction=avg_satisfaction,
                customer_retention_rate=retention_rate,
                average_empathy_score=avg_empathy,
                compliance_rate=compliance_rate,
                compliance_violations=total_violations,
                average_call_duration=avg_call_duration,
                average_resolution_time=avg_resolution_time,
                first_call_resolution_rate=first_call_rate
            )

            return analytics

        except Exception as e:
            logger.error(f"Error calculating collection analytics: {str(e)}")
            return None

    async def get_collection_metrics(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
        policy_number: Optional[str] = None,
        collection_status: Optional[str] = None,
        limit: int = 100
    ) -> List[PremiumCollectionMetrics]:
        """Retrieve collection metrics with filtering."""
        try:
            collection = get_collection(self.collection_name)

            # Build query
            query = {
                "tenant_id": tenant_id,
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }

            if policy_number:
                query["policy_number"] = policy_number

            if collection_status:
                query["collection_status"] = collection_status

            # Execute query
            cursor = collection.find(query).sort("created_at", -1).limit(limit)
            results = await cursor.to_list(length=limit)

            return [PremiumCollectionMetrics(**result) for result in results]

        except Exception as e:
            logger.error(f"Error retrieving collection metrics: {str(e)}")
            return []

    async def generate_compliance_report(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate comprehensive compliance report."""
        try:
            metrics = await self.get_collection_metrics(tenant_id, start_date, end_date, limit=10000)

            if not metrics:
                return {"error": "No data available for the specified period"}

            # Compliance analysis
            total_calls = len(metrics)
            fdcpa_violations = [m for m in metrics if not m.fdcpa_compliant]
            tcpa_violations = [m for m in metrics if not m.tcpa_compliant]

            violation_types = {}
            for metric in metrics:
                for violation in metric.compliance_violations:
                    violation_types[violation] = violation_types.get(violation, 0) + 1

            report = {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "compliance_summary": {
                    "total_calls": total_calls,
                    "fdcpa_compliant_calls": total_calls - len(fdcpa_violations),
                    "tcpa_compliant_calls": total_calls - len(tcpa_violations),
                    "overall_compliance_rate": f"{((total_calls - len(fdcpa_violations) - len(tcpa_violations)) / (total_calls * 2) * 100):.1f}%" if total_calls > 0 else "0%"
                },
                "violation_analysis": {
                    "fdcpa_violations": len(fdcpa_violations),
                    "tcpa_violations": len(tcpa_violations),
                    "violation_types": violation_types
                },
                "recommendations": self._generate_compliance_recommendations(violation_types, total_calls),
                "generated_at": datetime.utcnow().isoformat()
            }

            return report

        except Exception as e:
            logger.error(f"Error generating compliance report: {str(e)}")
            return {"error": f"Failed to generate report: {str(e)}"}

    def _generate_compliance_recommendations(
        self,
        violation_types: Dict[str, int],
        total_calls: int
    ) -> List[str]:
        """Generate actionable compliance recommendations."""
        recommendations = []

        # Time violation recommendations
        if violation_types.get("fdcpa_time_violation", 0) > 0:
            recommendations.append("Implement automatic call time restrictions (8 AM - 9 PM local time)")

        # Consent recommendations
        if violation_types.get("tcpa_consent_missing", 0) > 0:
            recommendations.append("Enhance consent verification process before call recording")

        # Language recommendations
        if violation_types.get("threatening_language", 0) > 0:
            recommendations.append("Provide additional training on empathetic collection techniques")
            recommendations.append("Implement real-time language monitoring and alerts")

        # Overall compliance rate
        total_violations = sum(violation_types.values())
        violation_rate = total_violations / total_calls if total_calls > 0 else 0

        if violation_rate > 0.05:  # > 5% violation rate
            recommendations.append("Conduct comprehensive compliance training for all agents")
            recommendations.append("Implement pre-call compliance checklists")

        return recommendations

    def _flatten_collection_data(self, collection_data: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested collection data structure to match PremiumCollectionMetrics model."""
        flattened = {}

        # Extract collection details
        if "collection" in collection_data:
            coll = collection_data["collection"]
            flattened["policy_number"] = coll.get("policy_number")
            flattened["collection_amount"] = coll.get("amount", 0.0)
            flattened["collection_status"] = coll.get("status", "scheduled")

        # Extract customer details
        if "customer" in collection_data:
            customer = collection_data["customer"]
            flattened["customer_id"] = customer.get("id")
            flattened["customer_satisfaction"] = customer.get("satisfaction_score")

        # Extract call details
        if "call" in collection_data:
            call = collection_data["call"]
            flattened["call_duration"] = call.get("duration_seconds")
            flattened["call_sentiment"] = call.get("sentiment_score")
            flattened["call_recording_consent"] = call.get("recording_consent", False)

        # Extract payment details
        if "payment" in collection_data:
            payment = collection_data["payment"]
            flattened["payment_method"] = payment.get("method")
            flattened["payment_amount"] = payment.get("amount")
            flattened["immediate_payment"] = payment.get("immediate", False)

        # Extract metadata
        if "metadata" in collection_data:
            meta = collection_data["metadata"]
            flattened["tenant_id"] = meta.get("tenantId")
            flattened["automation_id"] = meta.get("automationId")
            flattened["campaign_id"] = meta.get("campaignId")

        # Copy any already flat fields
        for key, value in collection_data.items():
            if key not in ["collection", "customer", "call", "payment", "metadata"] and key not in flattened:
                flattened[key] = value

        return flattened