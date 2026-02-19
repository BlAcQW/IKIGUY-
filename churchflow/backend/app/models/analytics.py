"""
Analytics Models for ChurchFlow

This module defines data models for church analytics, metrics, and insights.
Supports dashboard metrics, conference analytics, and engagement tracking.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class MetricPeriod(str, Enum):
    """Time period for metrics aggregation"""
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"
    NINETY_DAYS = "90d"
    ONE_YEAR = "1y"
    CUSTOM = "custom"


class EngagementLevel(str, Enum):
    """Member engagement level classification"""
    VERY_HIGH = "very_high"  # 90-100%
    HIGH = "high"            # 70-89%
    MEDIUM = "medium"        # 40-69%
    LOW = "low"              # 10-39%
    VERY_LOW = "very_low"    # 0-9%


class ConferenceAnalytics(BaseModel):
    """
    Comprehensive analytics for a conference.

    Provides insights into registration patterns, attendance,
    branch distribution, and bus usage.
    """
    conference_id: str = Field(..., description="Conference ID")
    conference_name: str = Field(..., description="Conference name")
    organization_id: str = Field(..., description="Organization ID")

    # Registration Metrics
    total_registrations: int = Field(0, description="Total registrations")
    registrations_by_day: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Daily registration breakdown [{date, count}]"
    )
    peak_registration_day: Optional[datetime] = Field(
        None, description="Day with most registrations"
    )
    peak_registration_count: Optional[int] = Field(
        None, description="Registrations on peak day"
    )

    # Attendance Metrics
    total_check_ins: int = Field(0, description="Total check-ins")
    check_in_rate: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Percentage of registrants who checked in"
    )
    session_check_ins: Dict[str, int] = Field(
        default_factory=dict,
        description="Check-ins per session {session_id: count}"
    )

    # Branch Distribution
    branch_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Registrations per branch {branch_name: count}"
    )
    top_branches: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top 5 branches by registration [{name, count}]"
    )

    # Bus Transportation
    bus_usage_rate: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Percentage requiring bus transport"
    )
    bus_route_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Usage per bus route {route_name: count}"
    )

    # Other Church Participation
    other_churches_count: int = Field(
        0, description="Number of registrations from other churches"
    )
    other_churches_percentage: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Percentage from other churches"
    )

    # Timing Metrics
    avg_registration_days_before: Optional[float] = Field(
        None, description="Average days before event that people registered"
    )
    last_minute_registrations: int = Field(
        0, description="Registrations in last 24 hours before event"
    )

    # Calculated timestamp
    calculated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When analytics were calculated"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "conference_id": "conf_123",
                "conference_name": "IMPACT 2025",
                "organization_id": "org_456",
                "total_registrations": 450,
                "total_check_ins": 380,
                "check_in_rate": 0.844,
                "bus_usage_rate": 0.35,
                "other_churches_percentage": 0.15
            }
        }


class MemberEngagementMetrics(BaseModel):
    """
    Member engagement metrics for an organization.

    Tracks member activity, engagement scores, and participation trends.
    """
    organization_id: str = Field(..., description="Organization ID")
    period: MetricPeriod = Field(..., description="Metrics period")
    period_start: datetime = Field(..., description="Period start date")
    period_end: datetime = Field(..., description="Period end date")

    # Member Counts
    total_members: int = Field(0, description="Total registered members")
    active_members: int = Field(
        0, description="Members who attended event in period"
    )
    inactive_members: int = Field(
        0, description="Members with no activity in period"
    )
    new_members: int = Field(0, description="New members added in period")

    # Engagement Metrics
    engagement_score: float = Field(
        0.0,
        ge=0.0,
        le=100.0,
        description="Overall engagement score (0-100)"
    )
    engagement_level: EngagementLevel = Field(
        EngagementLevel.MEDIUM,
        description="Engagement level classification"
    )

    # Activity Metrics
    avg_events_per_member: float = Field(
        0.0, description="Average events attended per member"
    )
    repeat_attendee_rate: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Percentage who attended multiple events"
    )

    # Top Engaged Members
    top_engaged_members: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top 10 most engaged members"
    )

    # Trends (over time)
    engagement_trends: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Engagement score over time [{date, score}]"
    )

    # Retention
    member_retention_rate: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Percentage of members who returned"
    )

    calculated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When metrics were calculated"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": "org_456",
                "period": "30d",
                "total_members": 1200,
                "active_members": 850,
                "inactive_members": 350,
                "new_members": 45,
                "engagement_score": 72.5,
                "engagement_level": "high",
                "member_retention_rate": 0.88
            }
        }


class CommunicationMetrics(BaseModel):
    """
    Communication effectiveness metrics.

    Tracks SMS and email campaign performance, delivery rates,
    and communication costs.
    """
    organization_id: str = Field(..., description="Organization ID")
    period_start: datetime = Field(..., description="Period start")
    period_end: datetime = Field(..., description="Period end")

    # SMS Metrics
    sms_sent: int = Field(0, description="Total SMS sent")
    sms_delivered: int = Field(0, description="SMS successfully delivered")
    sms_failed: int = Field(0, description="SMS delivery failures")
    sms_delivery_rate: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="SMS delivery success rate"
    )
    sms_cost_total: float = Field(0.0, ge=0.0, description="Total SMS cost")
    sms_cost_per_message: float = Field(
        0.0, ge=0.0, description="Average cost per SMS"
    )

    # Email Metrics (if email campaigns enabled)
    email_sent: int = Field(0, description="Total emails sent")
    email_delivered: int = Field(0, description="Emails delivered")
    email_opened: int = Field(0, description="Emails opened")
    email_clicked: int = Field(0, description="Links clicked")
    email_open_rate: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Email open rate"
    )
    email_click_rate: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Email click-through rate"
    )

    # Campaign Performance
    campaigns_sent: int = Field(0, description="Number of campaigns")
    avg_campaign_size: float = Field(
        0.0, description="Average recipients per campaign"
    )
    most_effective_campaign: Optional[Dict[str, Any]] = Field(
        None, description="Best performing campaign details"
    )

    # Costs and ROI
    total_communication_cost: float = Field(
        0.0, ge=0.0, description="Total communication spend"
    )
    cost_per_attendee: Optional[float] = Field(
        None, description="Communication cost per event attendee"
    )

    calculated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When metrics were calculated"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": "org_456",
                "sms_sent": 1250,
                "sms_delivered": 1198,
                "sms_delivery_rate": 0.958,
                "sms_cost_total": 37.50,
                "email_sent": 800,
                "email_open_rate": 0.42,
                "campaigns_sent": 8
            }
        }


class ChurchDashboardMetrics(BaseModel):
    """
    Comprehensive dashboard metrics for church admin.

    Aggregates all key metrics for a church organization over a period.
    This is the primary model returned to the dashboard UI.
    """
    organization_id: str = Field(..., description="Organization ID")
    organization_name: str = Field(..., description="Organization name")
    period: MetricPeriod = Field(
        MetricPeriod.THIRTY_DAYS,
        description="Metrics period"
    )
    period_start: datetime = Field(..., description="Period start date")
    period_end: datetime = Field(..., description="Period end date")

    # Event Metrics
    total_events: int = Field(0, description="Total events/conferences")
    total_attendees: int = Field(0, description="Total unique attendees")
    avg_attendance_per_event: float = Field(
        0.0, description="Average attendance per event"
    )
    upcoming_events: int = Field(0, description="Upcoming events scheduled")

    # Communication Metrics
    sms_sent: int = Field(0, description="Total SMS messages sent")
    sms_delivery_rate: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="SMS delivery success rate"
    )
    email_sent: int = Field(0, description="Total emails sent")
    email_open_rate: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Email open rate"
    )

    # Engagement Metrics
    new_members: int = Field(0, description="New members this period")
    returning_members: int = Field(
        0, description="Members who attended multiple times"
    )
    member_retention_rate: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Member retention rate"
    )
    engagement_score: float = Field(
        0.0,
        ge=0.0,
        le=100.0,
        description="Overall engagement score"
    )

    # Financial Metrics (Optional - Premium tier)
    total_giving: Optional[float] = Field(
        None, description="Total giving/donations"
    )
    avg_giving_per_member: Optional[float] = Field(
        None, description="Average giving per member"
    )
    giving_growth_rate: Optional[float] = Field(
        None, description="Giving growth rate vs previous period"
    )

    # Trends (percentage change from previous period)
    attendance_trend: float = Field(
        0.0, description="Attendance % change from previous period"
    )
    engagement_trend: float = Field(
        0.0, description="Engagement % change from previous period"
    )
    giving_trend: Optional[float] = Field(
        None, description="Giving % change from previous period"
    )
    communication_trend: float = Field(
        0.0, description="Communication volume % change"
    )

    # Insights and Alerts
    insights: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="AI-generated insights and recommendations"
    )
    alerts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Important alerts or warnings"
    )

    # Comparison with previous period
    previous_period_comparison: Optional[Dict[str, Any]] = Field(
        None, description="Comparison with previous period metrics"
    )

    calculated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When dashboard was generated"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": "org_456",
                "organization_name": "Action Chapel International",
                "period": "30d",
                "total_events": 4,
                "total_attendees": 1250,
                "avg_attendance_per_event": 312.5,
                "sms_sent": 1800,
                "sms_delivery_rate": 0.958,
                "new_members": 42,
                "engagement_score": 74.5,
                "attendance_trend": 12.3,
                "engagement_trend": 8.7
            }
        }


class AttendancePrediction(BaseModel):
    """
    ML-based attendance prediction for an upcoming event.

    Uses historical data and predictive analytics to forecast attendance.
    """
    conference_id: str = Field(..., description="Conference ID")
    organization_id: str = Field(..., description="Organization ID")

    # Prediction
    predicted_attendance: int = Field(..., description="Predicted attendance")
    confidence_interval: Dict[str, int] = Field(
        ...,
        description="Prediction confidence interval {low, high}"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Prediction confidence (0-1)"
    )

    # Factors influencing prediction
    influencing_factors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Factors affecting prediction"
    )

    # Historical comparison
    similar_events_avg: Optional[int] = Field(
        None, description="Average attendance of similar past events"
    )

    # Recommendations
    recommendations: List[str] = Field(
        default_factory=list,
        description="Action recommendations based on prediction"
    )

    predicted_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When prediction was made"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "conference_id": "conf_789",
                "organization_id": "org_456",
                "predicted_attendance": 420,
                "confidence_interval": {"low": 380, "high": 460},
                "confidence_score": 0.85,
                "similar_events_avg": 395
            }
        }


class AgeDistribution(BaseModel):
    """
    Age distribution breakdown for members.

    Groups members into age brackets for demographic analysis.
    """
    age_0_18: int = Field(0, description="Members aged 0-18")
    age_19_25: int = Field(0, description="Members aged 19-25")
    age_26_35: int = Field(0, description="Members aged 26-35")
    age_36_50: int = Field(0, description="Members aged 36-50")
    age_51_65: int = Field(0, description="Members aged 51-65")
    age_65_plus: int = Field(0, description="Members aged 65+")
    unknown: int = Field(0, description="Members with unknown age")

    class Config:
        json_schema_extra = {
            "example": {
                "age_0_18": 45,
                "age_19_25": 120,
                "age_26_35": 280,
                "age_36_50": 310,
                "age_51_65": 180,
                "age_65_plus": 65,
                "unknown": 50
            }
        }


class GenderDistribution(BaseModel):
    """
    Gender distribution for members.

    Provides breakdown of member gender demographics.
    """
    male: int = Field(0, description="Male members")
    female: int = Field(0, description="Female members")
    other: int = Field(0, description="Other gender identity")
    prefer_not_to_say: int = Field(0, description="Prefer not to disclose")
    unknown: int = Field(0, description="Gender not specified")

    class Config:
        json_schema_extra = {
            "example": {
                "male": 520,
                "female": 680,
                "other": 5,
                "prefer_not_to_say": 10,
                "unknown": 35
            }
        }


class MemberDashboardMetrics(BaseModel):
    """
    Comprehensive member dashboard metrics for admin.

    Provides detailed member statistics including demographics, activity,
    financial data, and growth trends for organizational leadership.
    """
    organization_id: str = Field(..., description="Organization ID")
    period: str = Field(..., description="Metrics period (7d, 30d, 90d, 1y)")
    period_start: datetime = Field(..., description="Period start date")
    period_end: datetime = Field(..., description="Period end date")

    # Total Counts
    total_members: int = Field(0, description="Total members in organization")
    active_members: int = Field(0, description="Members with recent activity")
    inactive_members: int = Field(0, description="Members without recent activity")
    visitors: int = Field(0, description="Visitors (not yet members)")
    alumni: int = Field(0, description="Alumni (former members)")

    # Growth Metrics
    new_members_count: int = Field(0, description="New members added in period")
    growth_rate: float = Field(
        0.0,
        description="Percentage growth vs previous period"
    )
    member_trend: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Member count over time [{date, count}]"
    )

    # Demographics
    gender_distribution: GenderDistribution = Field(
        ..., description="Gender breakdown"
    )
    age_distribution: AgeDistribution = Field(
        ..., description="Age group breakdown"
    )
    marital_status_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Marital status breakdown {status: count}"
    )

    # Activity & Engagement
    visit_frequency: Dict[str, int] = Field(
        default_factory=dict,
        description="Visit frequency breakdown {weekly, biweekly, monthly, inactive}"
    )
    average_visit_count: float = Field(
        0.0, description="Average visits per member in period"
    )
    first_timers: int = Field(0, description="First-time visitors in period")
    returning_visitors: int = Field(
        0, description="Visitors who returned in period"
    )

    # Financial Metrics
    total_donations: float = Field(0.0, ge=0.0, description="Total donations")
    total_donors: int = Field(0, description="Unique donors in period")
    average_donation: float = Field(
        0.0, ge=0.0, description="Average donation amount"
    )
    donor_percentage: float = Field(
        0.0,
        ge=0.0,
        le=100.0,
        description="Percentage of members who donate"
    )

    # Branch Distribution
    branch_distribution: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Members per branch [{branch_id, branch_name, member_count}]"
    )

    # Spiritual Journey
    spiritual_stages: Dict[str, int] = Field(
        default_factory=dict,
        description="Members by spiritual stage {stage: count}"
    )

    calculated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When metrics were calculated"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": "org_456",
                "period": "30d",
                "total_members": 1250,
                "active_members": 890,
                "inactive_members": 360,
                "visitors": 45,
                "new_members_count": 28,
                "growth_rate": 2.3,
                "total_donations": 45000.00,
                "total_donors": 420,
                "average_donation": 107.14,
                "donor_percentage": 33.6,
                "average_visit_count": 2.8,
                "first_timers": 22,
                "returning_visitors": 18
            }
        }
