"""
Payment analytics service for comprehensive payment reminder campaign analytics.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import random

class PaymentMetrics(BaseModel):
    """Payment reminder campaign metrics."""
    total_calls: int = 0
    successful_calls: int = 0
    right_party_contacts: int = 0
    payments_collected: int = 0
    payment_plans_arranged: int = 0
    settlements_negotiated: int = 0
    disputes_raised: int = 0
    escalations: int = 0
    total_recovered: float = 0.0
    avg_recovery_amount: float = 0.0
    collection_rate: float = 0.0
    success_rate: float = 0.0
    compliance_score: float = 100.0

class ComplianceMetrics(BaseModel):
    """FDCPA/TCPA compliance metrics."""
    fdcpa_violations: int = 0
    tcpa_violations: int = 0
    call_time_violations: int = 0
    proper_disclosures: int = 0
    cease_desist_requests: int = 0
    disputes_processed: int = 0
    validation_notices_sent: int = 0
    compliance_rate: float = 100.0

class PerformanceMetrics(BaseModel):
    """Performance and efficiency metrics."""
    avg_call_duration: float = 0.0
    first_call_resolution_rate: float = 0.0
    payment_plan_success_rate: float = 0.0
    settlement_acceptance_rate: float = 0.0
    customer_satisfaction: float = 0.0
    agent_productivity: float = 0.0

class PaymentAnalytics(BaseModel):
    """Comprehensive payment analytics."""
    campaign_id: str
    period_start: datetime
    period_end: datetime
    payment_metrics: PaymentMetrics
    compliance_metrics: ComplianceMetrics
    performance_metrics: PerformanceMetrics
    trends: Dict[str, Any] = {}
    insights: List[str] = []

class PaymentAnalyticsService:
    """Service for payment reminder analytics."""

    def __init__(self):
        self.base_url = "https://analytics.ailabsafrica.com"

    async def get_comprehensive_analytics(
        self,
        campaign_id: str,
        period_days: int = 7
    ) -> PaymentAnalytics:
        """
        Get comprehensive payment analytics for a campaign.

        Args:
            campaign_id: Payment reminder campaign ID
            period_days: Number of days for analytics period

        Returns:
            Comprehensive payment analytics
        """
        try:
            period_end = datetime.utcnow()
            period_start = period_end - timedelta(days=period_days)

            # Generate mock analytics data
            payment_metrics = self._generate_payment_metrics(period_days)
            compliance_metrics = self._generate_compliance_metrics(period_days)
            performance_metrics = self._generate_performance_metrics(period_days)
            trends = self._generate_trends(period_days)
            insights = self._generate_insights(payment_metrics, compliance_metrics, performance_metrics)

            return PaymentAnalytics(
                campaign_id=campaign_id,
                period_start=period_start,
                period_end=period_end,
                payment_metrics=payment_metrics,
                compliance_metrics=compliance_metrics,
                performance_metrics=performance_metrics,
                trends=trends,
                insights=insights
            )

        except Exception as e:
            # Return default analytics on error
            return PaymentAnalytics(
                campaign_id=campaign_id,
                period_start=datetime.utcnow() - timedelta(days=period_days),
                period_end=datetime.utcnow(),
                payment_metrics=PaymentMetrics(),
                compliance_metrics=ComplianceMetrics(),
                performance_metrics=PerformanceMetrics()
            )

    def _generate_payment_metrics(self, period_days: int) -> PaymentMetrics:
        """Generate payment metrics based on period."""
        base_calls = period_days * 20  # ~20 calls per day
        total_calls = random.randint(int(base_calls * 0.8), int(base_calls * 1.2))
        successful_calls = int(total_calls * random.uniform(0.75, 0.90))
        right_party_contacts = int(successful_calls * random.uniform(0.80, 0.95))
        payments_collected = int(right_party_contacts * random.uniform(0.45, 0.65))
        payment_plans_arranged = int(right_party_contacts * random.uniform(0.20, 0.35))
        settlements_negotiated = int(right_party_contacts * random.uniform(0.10, 0.20))
        disputes_raised = int(total_calls * random.uniform(0.05, 0.12))
        escalations = int(total_calls * random.uniform(0.08, 0.15))

        # Calculate financial metrics
        avg_recovery = random.uniform(250, 800)
        total_recovered = (payments_collected + payment_plans_arranged * 0.7) * avg_recovery
        collection_rate = (payments_collected / total_calls * 100) if total_calls > 0 else 0
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0

        return PaymentMetrics(
            total_calls=total_calls,
            successful_calls=successful_calls,
            right_party_contacts=right_party_contacts,
            payments_collected=payments_collected,
            payment_plans_arranged=payment_plans_arranged,
            settlements_negotiated=settlements_negotiated,
            disputes_raised=disputes_raised,
            escalations=escalations,
            total_recovered=round(total_recovered, 2),
            avg_recovery_amount=round(avg_recovery, 2),
            collection_rate=round(collection_rate, 1),
            success_rate=round(success_rate, 1),
            compliance_score=random.uniform(95.0, 100.0)
        )

    def _generate_compliance_metrics(self, period_days: int) -> ComplianceMetrics:
        """Generate compliance metrics."""
        base_calls = period_days * 20
        total_calls = random.randint(int(base_calls * 0.8), int(base_calls * 1.2))

        fdcpa_violations = random.randint(0, max(1, total_calls // 200))
        tcpa_violations = random.randint(0, max(1, total_calls // 300))
        call_time_violations = random.randint(0, max(1, total_calls // 150))
        proper_disclosures = total_calls - random.randint(0, 2)
        cease_desist_requests = random.randint(0, max(1, total_calls // 50))
        disputes_processed = random.randint(0, max(1, total_calls // 25))
        validation_notices_sent = random.randint(0, max(1, total_calls // 30))

        total_violations = fdcpa_violations + tcpa_violations + call_time_violations
        compliance_rate = ((total_calls - total_violations) / total_calls * 100) if total_calls > 0 else 100

        return ComplianceMetrics(
            fdcpa_violations=fdcpa_violations,
            tcpa_violations=tcpa_violations,
            call_time_violations=call_time_violations,
            proper_disclosures=proper_disclosures,
            cease_desist_requests=cease_desist_requests,
            disputes_processed=disputes_processed,
            validation_notices_sent=validation_notices_sent,
            compliance_rate=round(compliance_rate, 1)
        )

    def _generate_performance_metrics(self, period_days: int) -> PerformanceMetrics:
        """Generate performance metrics."""
        return PerformanceMetrics(
            avg_call_duration=round(random.uniform(4.5, 8.2), 1),
            first_call_resolution_rate=round(random.uniform(35.0, 55.0), 1),
            payment_plan_success_rate=round(random.uniform(75.0, 90.0), 1),
            settlement_acceptance_rate=round(random.uniform(60.0, 80.0), 1),
            customer_satisfaction=round(random.uniform(3.2, 4.1), 1),
            agent_productivity=round(random.uniform(80.0, 95.0), 1)
        )

    def _generate_trends(self, period_days: int) -> Dict[str, Any]:
        """Generate trend data."""
        days = min(period_days, 30)  # Limit to 30 days for trends

        # Generate daily trends
        daily_calls = [random.randint(15, 35) for _ in range(days)]
        daily_collections = [random.randint(8, 20) for _ in range(days)]
        daily_compliance = [random.uniform(95.0, 100.0) for _ in range(days)]

        return {
            "daily_calls": daily_calls,
            "daily_collections": daily_collections,
            "daily_compliance_scores": daily_compliance,
            "collection_rate_trend": [round(c/call*100, 1) for c, call in zip(daily_collections, daily_calls)],
            "payment_method_distribution": {
                "credit_card": random.randint(40, 60),
                "ach_transfer": random.randint(25, 40),
                "debit_card": random.randint(10, 25),
                "check_by_phone": random.randint(5, 15)
            },
            "time_of_day_performance": {
                "morning": {"calls": random.randint(20, 40), "success_rate": random.uniform(65, 80)},
                "afternoon": {"calls": random.randint(30, 50), "success_rate": random.uniform(70, 85)},
                "evening": {"calls": random.randint(25, 45), "success_rate": random.uniform(60, 75)}
            }
        }

    def _generate_insights(
        self,
        payment_metrics: PaymentMetrics,
        compliance_metrics: ComplianceMetrics,
        performance_metrics: PerformanceMetrics
    ) -> List[str]:
        """Generate actionable insights."""
        insights = []

        # Collection rate insights
        if payment_metrics.collection_rate > 50:
            insights.append("🎯 Excellent collection rate! Consider expanding campaign reach.")
        elif payment_metrics.collection_rate > 35:
            insights.append("📈 Good collection performance. Focus on payment plan optimization.")
        else:
            insights.append("⚠️ Collection rate below target. Review customer segmentation and scripts.")

        # Compliance insights
        if compliance_metrics.compliance_rate > 98:
            insights.append("✅ Outstanding compliance record maintained.")
        elif compliance_metrics.compliance_rate > 95:
            insights.append("📋 Good compliance performance. Monitor for improvement opportunities.")
        else:
            insights.append("🚨 Compliance attention needed. Review training and monitoring procedures.")

        # Performance insights
        if performance_metrics.avg_call_duration > 7:
            insights.append("⏱️ Call duration high. Consider script optimization for efficiency.")

        if performance_metrics.customer_satisfaction > 3.8:
            insights.append("😊 High customer satisfaction scores indicate professional approach.")
        elif performance_metrics.customer_satisfaction < 3.0:
            insights.append("😟 Customer satisfaction needs attention. Review call approach and training.")

        # Payment plan insights
        if performance_metrics.payment_plan_success_rate > 85:
            insights.append("💪 Payment plans performing well. Consider promoting to more customers.")

        # Settlement insights
        if payment_metrics.settlements_negotiated > payment_metrics.total_calls * 0.15:
            insights.append("🤝 High settlement activity. Ensure proper authorization procedures.")

        return insights

    async def get_real_time_metrics(self, campaign_id: str) -> Dict[str, Any]:
        """Get real-time metrics for dashboard."""
        try:
            # Generate real-time mock data
            current_hour_calls = random.randint(5, 15)
            current_hour_collections = random.randint(2, 8)
            active_calls = random.randint(0, 5)

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "current_hour": {
                    "calls_made": current_hour_calls,
                    "collections": current_hour_collections,
                    "success_rate": round((current_hour_collections / current_hour_calls * 100) if current_hour_calls > 0 else 0, 1)
                },
                "active_now": {
                    "active_calls": active_calls,
                    "agents_online": random.randint(3, 8),
                    "queue_size": random.randint(0, 12)
                },
                "today_totals": {
                    "calls": random.randint(80, 150),
                    "collections": random.randint(35, 70),
                    "amount_collected": round(random.uniform(15000, 45000), 2),
                    "compliance_score": round(random.uniform(96.0, 100.0), 1)
                },
                "alerts": self._generate_alerts()
            }

        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def _generate_alerts(self) -> List[Dict[str, Any]]:
        """Generate system alerts."""
        alerts = []

        # Random alert generation
        if random.random() < 0.1:  # 10% chance of compliance alert
            alerts.append({
                "type": "compliance",
                "severity": "warning",
                "message": "Customer requested cease and desist - update campaign exclusions",
                "timestamp": datetime.utcnow().isoformat()
            })

        if random.random() < 0.05:  # 5% chance of system alert
            alerts.append({
                "type": "system",
                "severity": "info",
                "message": "Payment processing integration running normally",
                "timestamp": datetime.utcnow().isoformat()
            })

        if random.random() < 0.15:  # 15% chance of performance alert
            alerts.append({
                "type": "performance",
                "severity": "success",
                "message": "Collection rate above target for current period",
                "timestamp": datetime.utcnow().isoformat()
            })

        return alerts

    async def get_campaign_comparison(
        self,
        campaign_ids: List[str],
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Compare multiple payment campaigns."""
        try:
            comparisons = {}

            for campaign_id in campaign_ids:
                analytics = await self.get_comprehensive_analytics(campaign_id, period_days)
                comparisons[campaign_id] = {
                    "collection_rate": analytics.payment_metrics.collection_rate,
                    "compliance_score": analytics.compliance_metrics.compliance_rate,
                    "total_recovered": analytics.payment_metrics.total_recovered,
                    "customer_satisfaction": analytics.performance_metrics.customer_satisfaction
                }

            # Calculate benchmarks
            if comparisons:
                all_collection_rates = [c["collection_rate"] for c in comparisons.values()]
                all_compliance_scores = [c["compliance_score"] for c in comparisons.values()]

                benchmarks = {
                    "avg_collection_rate": round(sum(all_collection_rates) / len(all_collection_rates), 1),
                    "avg_compliance_score": round(sum(all_compliance_scores) / len(all_compliance_scores), 1),
                    "best_performer": max(comparisons.keys(), key=lambda k: comparisons[k]["collection_rate"]),
                    "most_compliant": max(comparisons.keys(), key=lambda k: comparisons[k]["compliance_score"])
                }

                return {
                    "campaigns": comparisons,
                    "benchmarks": benchmarks,
                    "period_days": period_days
                }

            return {"campaigns": {}, "benchmarks": {}}

        except Exception as e:
            return {"error": str(e)}

    async def get_compliance_dashboard(self, campaign_id: str) -> Dict[str, Any]:
        """Get compliance-focused dashboard data."""
        try:
            # Generate compliance-focused metrics
            return {
                "campaign_id": campaign_id,
                "compliance_overview": {
                    "overall_score": round(random.uniform(96.0, 100.0), 1),
                    "fdcpa_compliance": round(random.uniform(98.0, 100.0), 1),
                    "tcpa_compliance": round(random.uniform(95.0, 100.0), 1),
                    "call_time_compliance": round(random.uniform(97.0, 100.0), 1)
                },
                "recent_violations": {
                    "total": random.randint(0, 3),
                    "fdcpa": random.randint(0, 1),
                    "tcpa": random.randint(0, 2),
                    "call_time": random.randint(0, 1)
                },
                "customer_rights": {
                    "validation_notices_sent": random.randint(5, 25),
                    "disputes_processed": random.randint(2, 15),
                    "cease_desist_honored": random.randint(0, 8),
                    "opt_out_requests": random.randint(1, 10)
                },
                "monitoring_alerts": self._generate_compliance_alerts(),
                "next_audit_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
            }

        except Exception as e:
            return {"error": str(e)}

    def _generate_compliance_alerts(self) -> List[Dict[str, Any]]:
        """Generate compliance-specific alerts."""
        alerts = []

        if random.random() < 0.1:
            alerts.append({
                "type": "validation_request",
                "message": "Customer disputed debt - validation notice required",
                "priority": "high",
                "timestamp": datetime.utcnow().isoformat()
            })

        if random.random() < 0.05:
            alerts.append({
                "type": "cease_desist",
                "message": "Customer requested to cease communication",
                "priority": "critical",
                "timestamp": datetime.utcnow().isoformat()
            })

        if random.random() < 0.15:
            alerts.append({
                "type": "call_frequency",
                "message": "Customer call frequency approaching limit",
                "priority": "medium",
                "timestamp": datetime.utcnow().isoformat()
            })

        return alerts

# Service instance
payment_analytics_service = PaymentAnalyticsService()