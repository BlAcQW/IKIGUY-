"""
Church Analytics Service for ChurchFlow - Phase 7

This module provides comprehensive analytics and business intelligence for churches.
Leverages shared BI engine and predictive analytics from @shared/.

Focuses on:
- Conference analytics (registrations, attendance, engagement)
- Member engagement tracking
- Communication effectiveness
- Dashboard aggregations
- Predictive analytics
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

# Import shared BI and analytics engines
from shared.analytics.business_intelligence import (
    BusinessIntelligence,
    Metric,
    KPICategory,
    ChartType
)
from shared.analytics.predictive_analytics import PredictiveAnalytics

# Import local models
from app.models.analytics import (
    ConferenceAnalytics,
    MemberEngagementMetrics,
    CommunicationMetrics,
    ChurchDashboardMetrics,
    AttendancePrediction,
    MetricPeriod,
    EngagementLevel
)


class ChurchAnalyticsService:
    """
    Comprehensive analytics service for ChurchFlow.

    Provides:
    - Conference analytics and insights
    - Member engagement tracking
    - Communication effectiveness metrics
    - Dashboard aggregations
    - Predictive analytics for event planning
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize analytics service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.bi_engine = BusinessIntelligence()
        self.predictive = PredictiveAnalytics()

    async def get_conference_analytics(
        self,
        conference_id: str,
        organization_id: str
    ) -> ConferenceAnalytics:
        """
        Generate comprehensive analytics for a specific conference.

        Args:
            conference_id: Conference ID
            organization_id: Organization ID

        Returns:
            ConferenceAnalytics model with all metrics
        """
        # Fetch conference details
        conference = await self.db.conferences.find_one({
            "_id": ObjectId(conference_id),
            "organization_id": organization_id
        })

        if not conference:
            raise ValueError(f"Conference {conference_id} not found")

        # Fetch all registrations for this conference
        registrations_cursor = self.db.registrations.find({
            "conference_id": conference_id
        })
        registrations = await registrations_cursor.to_list(length=None)

        total_registrations = len(registrations)

        # Calculate registration by day
        registrations_by_day = self._group_by_day(
            registrations,
            date_field="created_at"
        )

        # Find peak registration day
        peak_day = None
        peak_count = 0
        if registrations_by_day:
            peak_day_data = max(registrations_by_day, key=lambda x: x["count"])
            peak_day = peak_day_data["date"]
            peak_count = peak_day_data["count"]

        # Calculate check-in metrics
        total_check_ins = sum(
            1 for r in registrations if r.get("checked_in", False)
        )
        check_in_rate = (
            total_check_ins / total_registrations
            if total_registrations > 0
            else 0.0
        )

        # Branch distribution
        branch_distribution = {}
        for reg in registrations:
            branch = reg.get("branch_name", "Unknown")
            branch_distribution[branch] = branch_distribution.get(branch, 0) + 1

        # Top 5 branches
        top_branches = [
            {"name": branch, "count": count}
            for branch, count in sorted(
                branch_distribution.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        ]

        # Bus usage metrics
        bus_users = sum(1 for r in registrations if r.get("needs_bus", False))
        bus_usage_rate = bus_users / total_registrations if total_registrations > 0 else 0.0

        # Bus route distribution
        bus_route_distribution = {}
        for reg in registrations:
            if reg.get("needs_bus") and reg.get("bus_route"):
                route = reg["bus_route"]
                bus_route_distribution[route] = bus_route_distribution.get(route, 0) + 1

        # Other churches participation
        other_churches_count = sum(
            1 for r in registrations if r.get("from_other_church", False)
        )
        other_churches_percentage = (
            other_churches_count / total_registrations
            if total_registrations > 0
            else 0.0
        )

        # Registration timing metrics
        conference_date = conference.get("start_date")
        if conference_date and registrations:
            days_before = [
                (conference_date - r["created_at"]).days
                for r in registrations
                if r.get("created_at")
            ]
            avg_days_before = sum(days_before) / len(days_before) if days_before else None

            # Last minute (24 hours before)
            cutoff = conference_date - timedelta(days=1)
            last_minute = sum(
                1 for r in registrations
                if r.get("created_at") and r["created_at"] >= cutoff
            )
        else:
            avg_days_before = None
            last_minute = 0

        return ConferenceAnalytics(
            conference_id=conference_id,
            conference_name=conference.get("name", "Unknown"),
            organization_id=organization_id,
            total_registrations=total_registrations,
            registrations_by_day=registrations_by_day,
            peak_registration_day=peak_day,
            peak_registration_count=peak_count,
            total_check_ins=total_check_ins,
            check_in_rate=check_in_rate,
            branch_distribution=branch_distribution,
            top_branches=top_branches,
            bus_usage_rate=bus_usage_rate,
            bus_route_distribution=bus_route_distribution,
            other_churches_count=other_churches_count,
            other_churches_percentage=other_churches_percentage,
            avg_registration_days_before=avg_days_before,
            last_minute_registrations=last_minute
        )

    async def get_member_engagement(
        self,
        organization_id: str,
        period: MetricPeriod = MetricPeriod.THIRTY_DAYS,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> MemberEngagementMetrics:
        """
        Calculate member engagement metrics for an organization.

        Args:
            organization_id: Organization ID
            period: Time period for analysis
            start_date: Custom period start (if period is CUSTOM)
            end_date: Custom period end (if period is CUSTOM)

        Returns:
            MemberEngagementMetrics model
        """
        # Calculate date range
        period_end = end_date or datetime.utcnow()
        if period == MetricPeriod.SEVEN_DAYS:
            period_start = period_end - timedelta(days=7)
        elif period == MetricPeriod.THIRTY_DAYS:
            period_start = period_end - timedelta(days=30)
        elif period == MetricPeriod.NINETY_DAYS:
            period_start = period_end - timedelta(days=90)
        elif period == MetricPeriod.ONE_YEAR:
            period_start = period_end - timedelta(days=365)
        else:  # CUSTOM
            period_start = start_date or (period_end - timedelta(days=30))

        # Get all members (unique email addresses from registrations)
        all_members_cursor = self.db.registrations.aggregate([
            {"$match": {"organization_id": organization_id}},
            {"$group": {"_id": "$email"}},
            {"$count": "total"}
        ])
        all_members_result = await all_members_cursor.to_list(length=1)
        total_members = all_members_result[0]["total"] if all_members_result else 0

        # Get active members (attended at least one event in period)
        active_cursor = self.db.registrations.aggregate([
            {
                "$match": {
                    "organization_id": organization_id,
                    "created_at": {"$gte": period_start, "$lte": period_end}
                }
            },
            {"$group": {"_id": "$email"}},
            {"$count": "total"}
        ])
        active_result = await active_cursor.to_list(length=1)
        active_members = active_result[0]["total"] if active_result else 0

        inactive_members = total_members - active_members

        # Get new members (first registration in this period)
        new_members_cursor = self.db.registrations.aggregate([
            {"$match": {"organization_id": organization_id}},
            {"$sort": {"created_at": 1}},
            {"$group": {
                "_id": "$email",
                "first_registration": {"$first": "$created_at"}
            }},
            {
                "$match": {
                    "first_registration": {"$gte": period_start, "$lte": period_end}
                }
            },
            {"$count": "total"}
        ])
        new_result = await new_members_cursor.to_list(length=1)
        new_members = new_result[0]["total"] if new_result else 0

        # Calculate engagement score (0-100)
        # Reason: Weighted formula based on activity rate and repeat attendance
        activity_rate = active_members / total_members if total_members > 0 else 0

        # Get repeat attendees (attended 2+ events in period)
        repeat_cursor = self.db.registrations.aggregate([
            {
                "$match": {
                    "organization_id": organization_id,
                    "created_at": {"$gte": period_start, "$lte": period_end}
                }
            },
            {"$group": {"_id": "$email", "event_count": {"$sum": 1}}},
            {"$match": {"event_count": {"$gte": 2}}},
            {"$count": "total"}
        ])
        repeat_result = await repeat_cursor.to_list(length=1)
        repeat_attendees = repeat_result[0]["total"] if repeat_result else 0

        repeat_rate = repeat_attendees / active_members if active_members > 0 else 0

        # Engagement score: 60% activity + 40% repeat rate
        engagement_score = (activity_rate * 60) + (repeat_rate * 40)

        # Classify engagement level
        if engagement_score >= 90:
            engagement_level = EngagementLevel.VERY_HIGH
        elif engagement_score >= 70:
            engagement_level = EngagementLevel.HIGH
        elif engagement_score >= 40:
            engagement_level = EngagementLevel.MEDIUM
        elif engagement_score >= 10:
            engagement_level = EngagementLevel.LOW
        else:
            engagement_level = EngagementLevel.VERY_LOW

        # Average events per member
        total_registrations_cursor = self.db.registrations.count_documents({
            "organization_id": organization_id,
            "created_at": {"$gte": period_start, "$lte": period_end}
        })
        total_registrations = await total_registrations_cursor
        avg_events = total_registrations / active_members if active_members > 0 else 0.0

        # Top engaged members
        top_engaged_cursor = self.db.registrations.aggregate([
            {
                "$match": {
                    "organization_id": organization_id,
                    "created_at": {"$gte": period_start, "$lte": period_end}
                }
            },
            {
                "$group": {
                    "_id": "$email",
                    "event_count": {"$sum": 1},
                    "name": {"$first": "$name"}
                }
            },
            {"$sort": {"event_count": -1}},
            {"$limit": 10}
        ])
        top_engaged = [
            {
                "email": doc["_id"],
                "name": doc.get("name", "Unknown"),
                "event_count": doc["event_count"]
            }
            async for doc in top_engaged_cursor
        ]

        # Member retention (members who returned from previous period)
        previous_period_start = period_start - (period_end - period_start)
        previous_members_cursor = self.db.registrations.aggregate([
            {
                "$match": {
                    "organization_id": organization_id,
                    "created_at": {"$gte": previous_period_start, "$lt": period_start}
                }
            },
            {"$group": {"_id": "$email"}}
        ])
        previous_members = {doc["_id"] async for doc in previous_members_cursor}

        current_members_cursor = self.db.registrations.aggregate([
            {
                "$match": {
                    "organization_id": organization_id,
                    "created_at": {"$gte": period_start, "$lte": period_end}
                }
            },
            {"$group": {"_id": "$email"}}
        ])
        current_members = {doc["_id"] async for doc in current_members_cursor}

        retained = len(previous_members & current_members)
        retention_rate = retained / len(previous_members) if previous_members else 0.0

        return MemberEngagementMetrics(
            organization_id=organization_id,
            period=period,
            period_start=period_start,
            period_end=period_end,
            total_members=total_members,
            active_members=active_members,
            inactive_members=inactive_members,
            new_members=new_members,
            engagement_score=engagement_score,
            engagement_level=engagement_level,
            avg_events_per_member=avg_events,
            repeat_attendee_rate=repeat_rate,
            top_engaged_members=top_engaged,
            member_retention_rate=retention_rate
        )

    async def get_communication_metrics(
        self,
        organization_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> CommunicationMetrics:
        """
        Calculate communication effectiveness metrics.

        Args:
            organization_id: Organization ID
            period_start: Period start date
            period_end: Period end date

        Returns:
            CommunicationMetrics model
        """
        # Fetch SMS campaigns in period
        sms_cursor = self.db.sms_campaigns.find({
            "organization_id": organization_id,
            "sent_at": {"$gte": period_start, "$lte": period_end}
        })
        sms_campaigns = await sms_cursor.to_list(length=None)

        sms_sent = sum(c.get("total_sent", 0) for c in sms_campaigns)
        sms_delivered = sum(c.get("delivered", 0) for c in sms_campaigns)
        sms_failed = sum(c.get("failed", 0) for c in sms_campaigns)
        sms_delivery_rate = sms_delivered / sms_sent if sms_sent > 0 else 0.0
        sms_cost_total = sum(c.get("cost", 0.0) for c in sms_campaigns)
        sms_cost_per_message = sms_cost_total / sms_sent if sms_sent > 0 else 0.0

        # Email metrics (if available)
        email_cursor = self.db.email_campaigns.find({
            "organization_id": organization_id,
            "sent_at": {"$gte": period_start, "$lte": period_end}
        })
        email_campaigns = await email_cursor.to_list(length=None)

        email_sent = sum(c.get("total_sent", 0) for c in email_campaigns)
        email_delivered = sum(c.get("delivered", 0) for c in email_campaigns)
        email_opened = sum(c.get("opened", 0) for c in email_campaigns)
        email_clicked = sum(c.get("clicked", 0) for c in email_campaigns)
        email_open_rate = email_opened / email_delivered if email_delivered > 0 else 0.0
        email_click_rate = email_clicked / email_delivered if email_delivered > 0 else 0.0

        # Campaign performance
        campaigns_sent = len(sms_campaigns) + len(email_campaigns)
        total_recipients = sms_sent + email_sent
        avg_campaign_size = total_recipients / campaigns_sent if campaigns_sent > 0 else 0.0

        # Most effective campaign (highest open/delivery rate)
        best_campaign = None
        if email_campaigns:
            best = max(
                email_campaigns,
                key=lambda c: c.get("opened", 0) / c.get("delivered", 1)
            )
            best_campaign = {
                "id": str(best["_id"]),
                "name": best.get("name", "Unnamed"),
                "open_rate": best.get("opened", 0) / best.get("delivered", 1)
            }

        # Total communication cost
        total_cost = sms_cost_total

        # Cost per attendee (if we have attendance data)
        registrations_count = await self.db.registrations.count_documents({
            "organization_id": organization_id,
            "created_at": {"$gte": period_start, "$lte": period_end}
        })
        cost_per_attendee = total_cost / registrations_count if registrations_count > 0 else None

        return CommunicationMetrics(
            organization_id=organization_id,
            period_start=period_start,
            period_end=period_end,
            sms_sent=sms_sent,
            sms_delivered=sms_delivered,
            sms_failed=sms_failed,
            sms_delivery_rate=sms_delivery_rate,
            sms_cost_total=sms_cost_total,
            sms_cost_per_message=sms_cost_per_message,
            email_sent=email_sent,
            email_delivered=email_delivered,
            email_opened=email_opened,
            email_clicked=email_clicked,
            email_open_rate=email_open_rate,
            email_click_rate=email_click_rate,
            campaigns_sent=campaigns_sent,
            avg_campaign_size=avg_campaign_size,
            most_effective_campaign=best_campaign,
            total_communication_cost=total_cost,
            cost_per_attendee=cost_per_attendee
        )

    async def get_dashboard_metrics(
        self,
        organization_id: str,
        period: MetricPeriod = MetricPeriod.THIRTY_DAYS
    ) -> ChurchDashboardMetrics:
        """
        Generate comprehensive dashboard metrics for church admin.

        Aggregates all key metrics into a single dashboard view.

        Args:
            organization_id: Organization ID
            period: Time period for metrics

        Returns:
            ChurchDashboardMetrics model
        """
        # Calculate date range
        period_end = datetime.utcnow()
        if period == MetricPeriod.SEVEN_DAYS:
            period_start = period_end - timedelta(days=7)
        elif period == MetricPeriod.THIRTY_DAYS:
            period_start = period_end - timedelta(days=30)
        elif period == MetricPeriod.NINETY_DAYS:
            period_start = period_end - timedelta(days=90)
        else:  # ONE_YEAR
            period_start = period_end - timedelta(days=365)

        # Get organization name
        org = await self.db.organizations.find_one({"_id": ObjectId(organization_id)})
        org_name = org.get("name", "Unknown") if org else "Unknown"

        # Get member engagement metrics
        engagement = await self.get_member_engagement(organization_id, period)

        # Get communication metrics
        comm = await self.get_communication_metrics(
            organization_id,
            period_start,
            period_end
        )

        # Event metrics
        events_cursor = self.db.conferences.find({
            "organization_id": organization_id,
            "created_at": {"$gte": period_start, "$lte": period_end}
        })
        events = await events_cursor.to_list(length=None)
        total_events = len(events)

        # Upcoming events
        upcoming_count = await self.db.conferences.count_documents({
            "organization_id": organization_id,
            "start_date": {"$gt": datetime.utcnow()}
        })

        # Total attendees (unique registrations)
        attendees_cursor = self.db.registrations.aggregate([
            {
                "$match": {
                    "organization_id": organization_id,
                    "created_at": {"$gte": period_start, "$lte": period_end}
                }
            },
            {"$group": {"_id": "$email"}},
            {"$count": "total"}
        ])
        attendees_result = await attendees_cursor.to_list(length=1)
        total_attendees = attendees_result[0]["total"] if attendees_result else 0

        avg_attendance = total_attendees / total_events if total_events > 0 else 0.0

        # Calculate trends (comparison with previous period)
        previous_start = period_start - (period_end - period_start)
        previous_attendees_cursor = self.db.registrations.aggregate([
            {
                "$match": {
                    "organization_id": organization_id,
                    "created_at": {"$gte": previous_start, "$lt": period_start}
                }
            },
            {"$group": {"_id": "$email"}},
            {"$count": "total"}
        ])
        previous_result = await previous_attendees_cursor.to_list(length=1)
        previous_attendees = previous_result[0]["total"] if previous_result else 0

        attendance_trend = (
            ((total_attendees - previous_attendees) / previous_attendees * 100)
            if previous_attendees > 0
            else 0.0
        )

        # Generate insights using BI engine
        insights = self._generate_insights(
            engagement_score=engagement.engagement_score,
            sms_delivery_rate=comm.sms_delivery_rate,
            attendance_trend=attendance_trend,
            new_members=engagement.new_members
        )

        # Generate alerts
        alerts = self._generate_alerts(
            engagement_score=engagement.engagement_score,
            sms_delivery_rate=comm.sms_delivery_rate,
            inactive_members=engagement.inactive_members
        )

        return ChurchDashboardMetrics(
            organization_id=organization_id,
            organization_name=org_name,
            period=period,
            period_start=period_start,
            period_end=period_end,
            total_events=total_events,
            total_attendees=total_attendees,
            avg_attendance_per_event=avg_attendance,
            upcoming_events=upcoming_count,
            sms_sent=comm.sms_sent,
            sms_delivery_rate=comm.sms_delivery_rate,
            email_sent=comm.email_sent,
            email_open_rate=comm.email_open_rate,
            new_members=engagement.new_members,
            returning_members=int(engagement.total_members * engagement.repeat_attendee_rate),
            member_retention_rate=engagement.member_retention_rate,
            engagement_score=engagement.engagement_score,
            attendance_trend=attendance_trend,
            engagement_trend=0.0,  # TODO: Calculate from historical data
            communication_trend=0.0,  # TODO: Calculate from historical data
            insights=insights,
            alerts=alerts
        )

    def _group_by_day(
        self,
        records: List[Dict],
        date_field: str = "created_at"
    ) -> List[Dict[str, Any]]:
        """
        Group records by day.

        Args:
            records: List of records with datetime field
            date_field: Field name containing datetime

        Returns:
            List of {date, count} dictionaries
        """
        day_counts = {}
        for record in records:
            dt = record.get(date_field)
            if dt:
                day = dt.date()
                day_counts[day] = day_counts.get(day, 0) + 1

        return [
            {"date": day, "count": count}
            for day, count in sorted(day_counts.items())
        ]

    def _generate_insights(
        self,
        engagement_score: float,
        sms_delivery_rate: float,
        attendance_trend: float,
        new_members: int
    ) -> List[Dict[str, Any]]:
        """
        Generate AI-powered insights for dashboard.

        Args:
            engagement_score: Current engagement score
            sms_delivery_rate: SMS delivery success rate
            attendance_trend: Attendance % change
            new_members: New member count

        Returns:
            List of insight dictionaries
        """
        insights = []

        if attendance_trend > 10:
            insights.append({
                "type": "positive",
                "title": "Growing Attendance",
                "message": f"Attendance increased by {attendance_trend:.1f}% compared to previous period.",
                "priority": "high"
            })
        elif attendance_trend < -10:
            insights.append({
                "type": "warning",
                "title": "Declining Attendance",
                "message": f"Attendance decreased by {abs(attendance_trend):.1f}%. Consider engagement campaigns.",
                "priority": "high"
            })

        if engagement_score >= 70:
            insights.append({
                "type": "positive",
                "title": "High Engagement",
                "message": f"Excellent engagement score of {engagement_score:.1f}%. Keep up the great work!",
                "priority": "medium"
            })
        elif engagement_score < 40:
            insights.append({
                "type": "warning",
                "title": "Low Engagement",
                "message": f"Engagement score is {engagement_score:.1f}%. Consider follow-up campaigns.",
                "priority": "high"
            })

        if new_members > 20:
            insights.append({
                "type": "positive",
                "title": "Strong Growth",
                "message": f"{new_members} new members joined this period. Ensure onboarding support.",
                "priority": "medium"
            })

        if sms_delivery_rate < 0.9:
            insights.append({
                "type": "info",
                "title": "SMS Delivery",
                "message": f"SMS delivery rate is {sms_delivery_rate*100:.1f}%. Check phone number quality.",
                "priority": "low"
            })

        return insights

    def _generate_alerts(
        self,
        engagement_score: float,
        sms_delivery_rate: float,
        inactive_members: int
    ) -> List[Dict[str, Any]]:
        """
        Generate alerts for important issues.

        Args:
            engagement_score: Current engagement score
            sms_delivery_rate: SMS delivery rate
            inactive_members: Number of inactive members

        Returns:
            List of alert dictionaries
        """
        alerts = []

        if engagement_score < 30:
            alerts.append({
                "severity": "critical",
                "title": "Critical Engagement Drop",
                "message": "Engagement is critically low. Immediate action recommended.",
                "action": "Launch re-engagement campaign"
            })

        if sms_delivery_rate < 0.85:
            alerts.append({
                "severity": "warning",
                "title": "Low SMS Delivery",
                "message": f"Only {sms_delivery_rate*100:.1f}% of SMS messages delivered successfully.",
                "action": "Review contact database quality"
            })

        if inactive_members > 100:
            alerts.append({
                "severity": "info",
                "title": "Inactive Members",
                "message": f"{inactive_members} members have not attended recent events.",
                "action": "Consider targeted outreach"
            })

        return alerts
