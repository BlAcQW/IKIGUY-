"""
Member Analytics Service for ChurchFlow

This module provides comprehensive member statistics and analytics for church admin.
Focuses on member demographics, activity, financial metrics, and growth trends.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

# Import local models
from app.models.analytics import (
    MemberDashboardMetrics,
    AgeDistribution,
    GenderDistribution
)

logger = logging.getLogger(__name__)


class MemberAnalyticsService:
    """
    Comprehensive member analytics service for ChurchFlow.

    Provides detailed member statistics including demographics, activity,
    financial data, and growth trends.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize member analytics service.

        Args:
            db: MongoDB database instance
        """
        self.db = db

    async def get_member_dashboard_stats(
        self,
        organization_id: str,
        period: str = "30d",
        branch_id: Optional[str] = None
    ) -> MemberDashboardMetrics:
        """
        Get comprehensive member dashboard statistics.

        Args:
            organization_id: Organization ID
            period: Time period (7d, 30d, 90d, 1y)
            branch_id: Optional branch filter

        Returns:
            MemberDashboardMetrics with all statistics

        Raises:
            ValueError: If invalid period or organization not found
        """
        logger.info(
            f"[get_member_dashboard_stats] org_id={organization_id}, "
            f"period={period}, branch_id={branch_id}"
        )

        # Calculate date range
        period_end = datetime.utcnow()
        period_start = self._calculate_period_start(period, period_end)

        # Convert organization_id to ObjectId for proper MongoDB querying
        try:
            org_id_obj = ObjectId(organization_id)
        except Exception:
            org_id_obj = organization_id  # Fallback to string if conversion fails

        # Build base filter with ObjectId
        base_filter: Dict[str, Any] = {"organization_id": org_id_obj}
        if branch_id:
            try:
                base_filter["branch_id"] = ObjectId(branch_id)
            except Exception:
                base_filter["branch_id"] = branch_id

        # Get all member counts by status
        member_counts = await self._get_member_counts_by_status(base_filter)

        # Get age distribution
        age_distribution = await self._get_age_distribution(base_filter)

        # Get gender distribution
        gender_distribution = await self._get_gender_distribution(base_filter)

        # Get marital status distribution
        marital_distribution = await self._get_marital_status_distribution(base_filter)

        # Get visit frequency analysis
        visit_frequency = await self._get_visit_frequency(
            base_filter, period_start, period_end
        )

        # Get average visit count
        average_visit_count = await self._get_average_visit_count(
            base_filter, period_start, period_end
        )

        # Get first timers and returning visitors
        visitor_stats = await self._get_visitor_stats(
            base_filter, period_start, period_end
        )

        # Get spiritual stages distribution
        spiritual_stages = await self._get_spiritual_stages(base_filter)

        # Get branch distribution
        branch_distribution = await self._get_branch_distribution(org_id_obj)

        # Get financial metrics
        financial_metrics = await self._get_financial_metrics(
            org_id_obj, period_start, period_end, branch_id
        )

        # Get growth metrics
        growth_metrics = await self._get_growth_metrics(
            org_id_obj, period, period_start, period_end, branch_id
        )

        # Get member trend data
        member_trend = await self._get_member_trend(
            org_id_obj, period_start, period_end, branch_id
        )

        # Calculate donor percentage
        total_members = member_counts.get("total_members", 0)
        donor_percentage = (
            (financial_metrics["total_donors"] / total_members * 100)
            if total_members > 0 else 0.0
        )

        # Build response
        metrics = MemberDashboardMetrics(
            organization_id=organization_id,
            period=period,
            period_start=period_start,
            period_end=period_end,
            # Total counts
            total_members=member_counts.get("total_members", 0),
            active_members=member_counts.get("active_members", 0),
            inactive_members=member_counts.get("inactive_members", 0),
            visitors=member_counts.get("visitors", 0),
            alumni=member_counts.get("alumni", 0),
            # Growth
            new_members_count=growth_metrics["new_members_count"],
            growth_rate=growth_metrics["growth_rate"],
            member_trend=member_trend,
            # Demographics
            gender_distribution=gender_distribution,
            age_distribution=age_distribution,
            marital_status_distribution=marital_distribution,
            # Activity
            visit_frequency=visit_frequency,
            average_visit_count=average_visit_count,
            first_timers=visitor_stats["first_timers"],
            returning_visitors=visitor_stats["returning_visitors"],
            # Financial
            total_donations=financial_metrics["total_donations"],
            total_donors=financial_metrics["total_donors"],
            average_donation=financial_metrics["average_donation"],
            donor_percentage=donor_percentage,
            # Branch
            branch_distribution=branch_distribution,
            # Spiritual
            spiritual_stages=spiritual_stages,
            calculated_at=datetime.utcnow()
        )

        logger.info(
            f"[get_member_dashboard_stats] Completed: "
            f"total_members={metrics.total_members}, "
            f"active={metrics.active_members}, "
            f"donors={metrics.total_donors}"
        )

        return metrics

    def _calculate_period_start(self, period: str, period_end: datetime) -> datetime:
        """Calculate period start date based on period string."""
        period_map = {
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
            "90d": timedelta(days=90),
            "1y": timedelta(days=365)
        }

        if period not in period_map:
            raise ValueError(f"Invalid period: {period}")

        return period_end - period_map[period]

    async def _get_member_counts_by_status(
        self, base_filter: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Get member counts by status.

        Args:
            base_filter: Base MongoDB filter

        Returns:
            Dict with counts by status
        """
        pipeline = [
            {"$match": base_filter},
            {
                "$group": {
                    "_id": "$member_status",
                    "count": {"$sum": 1}
                }
            }
        ]

        results = await self.db.users.aggregate(pipeline).to_list(length=None)

        counts = {
            "total_members": 0,
            "active_members": 0,
            "inactive_members": 0,
            "visitors": 0,
            "alumni": 0
        }

        for result in results:
            status = result["_id"]
            count = result["count"]

            if status == "active_member":
                counts["active_members"] = count
            elif status == "inactive_member":
                counts["inactive_members"] = count
            elif status == "visitor":
                counts["visitors"] = count
            elif status == "alumni":
                counts["alumni"] = count

        # Total members = ALL users (active + inactive + visitors + alumni)
        counts["total_members"] = (
            counts["active_members"] +
            counts["inactive_members"] +
            counts["visitors"] +
            counts["alumni"]
        )

        return counts

    async def _get_age_distribution(
        self, base_filter: Dict[str, Any]
    ) -> AgeDistribution:
        """
        Calculate age distribution from date_of_birth.

        Args:
            base_filter: Base MongoDB filter

        Returns:
            AgeDistribution model
        """
        # Get members with date_of_birth
        pipeline = [
            {"$match": {**base_filter, "date_of_birth": {"$ne": None}}},
            {
                "$project": {
                    "age": {
                        "$divide": [
                            {"$subtract": [datetime.utcnow(), "$date_of_birth"]},
                            31557600000  # milliseconds in a year
                        ]
                    }
                }
            },
            {
                "$bucket": {
                    "groupBy": "$age",
                    "boundaries": [0, 18, 25, 35, 50, 65, 150],
                    "default": "out_of_range",
                    "output": {
                        "count": {"$sum": 1}
                    }
                }
            }
        ]

        results = await self.db.users.aggregate(pipeline).to_list(length=None)

        # Map boundaries to age groups
        age_groups = {
            0: "age_0_18",
            18: "age_19_25",
            25: "age_26_35",
            35: "age_36_50",
            50: "age_51_65",
            65: "age_65_plus"
        }

        distribution = {
            "age_0_18": 0,
            "age_19_25": 0,
            "age_26_35": 0,
            "age_36_50": 0,
            "age_51_65": 0,
            "age_65_plus": 0,
            "unknown": 0
        }

        for result in results:
            age_group_key = age_groups.get(result["_id"], "unknown")
            distribution[age_group_key] = result["count"]

        # Count members with no date_of_birth
        unknown_count = await self.db.users.count_documents({
            **base_filter,
            "date_of_birth": None
        })
        distribution["unknown"] = unknown_count

        return AgeDistribution(**distribution)

    async def _get_gender_distribution(
        self, base_filter: Dict[str, Any]
    ) -> GenderDistribution:
        """
        Get gender distribution.

        Args:
            base_filter: Base MongoDB filter

        Returns:
            GenderDistribution model
        """
        pipeline = [
            {"$match": base_filter},
            {
                "$group": {
                    "_id": "$gender",
                    "count": {"$sum": 1}
                }
            }
        ]

        results = await self.db.users.aggregate(pipeline).to_list(length=None)

        distribution = {
            "male": 0,
            "female": 0,
            "other": 0,
            "prefer_not_to_say": 0,
            "unknown": 0
        }

        for result in results:
            gender = result["_id"]
            count = result["count"]

            if gender in ["male", "Male", "M", "m"]:
                distribution["male"] += count
            elif gender in ["female", "Female", "F", "f"]:
                distribution["female"] += count
            elif gender == "prefer_not_to_say":
                distribution["prefer_not_to_say"] += count
            elif gender == "other":
                distribution["other"] += count
            else:
                distribution["unknown"] += count

        return GenderDistribution(**distribution)

    async def _get_marital_status_distribution(
        self, base_filter: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Get marital status distribution.

        Args:
            base_filter: Base MongoDB filter

        Returns:
            Dict with marital status counts
        """
        pipeline = [
            {"$match": base_filter},
            {
                "$group": {
                    "_id": "$marital_status",
                    "count": {"$sum": 1}
                }
            }
        ]

        results = await self.db.users.aggregate(pipeline).to_list(length=None)

        distribution = {}
        for result in results:
            status = result["_id"] or "unknown"
            distribution[status] = result["count"]

        return distribution

    async def _get_visit_frequency(
        self,
        base_filter: Dict[str, Any],
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, int]:
        """
        Analyze visit frequency patterns.

        Args:
            base_filter: Base MongoDB filter
            period_start: Period start date
            period_end: Period end date

        Returns:
            Dict with frequency breakdown
        """
        # For simplicity, we'll categorize based on visit_count
        # In production, you might want to calculate visits within the period
        pipeline = [
            {"$match": base_filter},
            {
                "$project": {
                    "visit_count": 1,
                    "last_visit_date": 1,
                    "frequency_category": {
                        "$switch": {
                            "branches": [
                                {
                                    "case": {
                                        "$and": [
                                            {"$gte": ["$visit_count", 4]},
                                            {"$gte": ["$last_visit_date", period_start]}
                                        ]
                                    },
                                    "then": "weekly"
                                },
                                {
                                    "case": {
                                        "$and": [
                                            {"$gte": ["$visit_count", 2]},
                                            {"$gte": ["$last_visit_date", period_start]}
                                        ]
                                    },
                                    "then": "biweekly"
                                },
                                {
                                    "case": {
                                        "$and": [
                                            {"$gte": ["$visit_count", 1]},
                                            {"$gte": ["$last_visit_date", period_start]}
                                        ]
                                    },
                                    "then": "monthly"
                                }
                            ],
                            "default": "inactive"
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": "$frequency_category",
                    "count": {"$sum": 1}
                }
            }
        ]

        results = await self.db.users.aggregate(pipeline).to_list(length=None)

        frequency = {
            "weekly": 0,
            "biweekly": 0,
            "monthly": 0,
            "inactive": 0
        }

        for result in results:
            category = result["_id"]
            if category in frequency:
                frequency[category] = result["count"]

        return frequency

    async def _get_average_visit_count(
        self,
        base_filter: Dict[str, Any],
        period_start: datetime,
        period_end: datetime
    ) -> float:
        """
        Calculate average visit count for members.

        Args:
            base_filter: Base MongoDB filter
            period_start: Period start date
            period_end: Period end date

        Returns:
            Average visit count
        """
        pipeline = [
            {"$match": base_filter},
            {
                "$group": {
                    "_id": None,
                    "avg_visits": {"$avg": "$visit_count"}
                }
            }
        ]

        results = await self.db.users.aggregate(pipeline).to_list(length=1)

        if results and results[0].get("avg_visits"):
            return round(results[0]["avg_visits"], 2)

        return 0.0

    async def _get_visitor_stats(
        self,
        base_filter: Dict[str, Any],
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, int]:
        """
        Get first-time and returning visitor stats.

        Args:
            base_filter: Base MongoDB filter
            period_start: Period start date
            period_end: Period end date

        Returns:
            Dict with visitor statistics
        """
        # First timers: first_visit_date in period
        first_timers = await self.db.users.count_documents({
            **base_filter,
            "first_visit_date": {"$gte": period_start, "$lte": period_end},
            "visit_count": 1
        })

        # Returning visitors: first_visit_date before period, visited in period
        returning_visitors = await self.db.users.count_documents({
            **base_filter,
            "first_visit_date": {"$lt": period_start},
            "last_visit_date": {"$gte": period_start, "$lte": period_end},
            "visit_count": {"$gte": 2}
        })

        return {
            "first_timers": first_timers,
            "returning_visitors": returning_visitors
        }

    async def _get_spiritual_stages(
        self, base_filter: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Get spiritual stage distribution.

        Args:
            base_filter: Base MongoDB filter

        Returns:
            Dict with spiritual stage counts
        """
        pipeline = [
            {"$match": base_filter},
            {
                "$group": {
                    "_id": "$current_spiritual_stage",
                    "count": {"$sum": 1}
                }
            }
        ]

        results = await self.db.users.aggregate(pipeline).to_list(length=None)

        stages = {}
        for result in results:
            stage = result["_id"] or "unknown"
            stages[stage] = result["count"]

        return stages

    async def _get_branch_distribution(
        self, organization_id: Any
    ) -> List[Dict[str, Any]]:
        """
        Get member distribution by branch.

        Args:
            organization_id: Organization ID (ObjectId or string)

        Returns:
            List of branch distribution data
        """
        pipeline = [
            {"$match": {"organization_id": organization_id}},
            {
                "$group": {
                    "_id": "$branch_id",
                    "member_count": {"$sum": 1}
                }
            },
            {
                "$lookup": {
                    "from": "branches",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "branch_info"
                }
            },
            {
                "$project": {
                    "branch_id": {"$toString": "$_id"},
                    "branch_name": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$branch_info.name", 0]},
                            "Unknown Branch"
                        ]
                    },
                    "member_count": 1
                }
            },
            {"$sort": {"member_count": -1}}
        ]

        results = await self.db.users.aggregate(pipeline).to_list(length=None)

        return [
            {
                "branch_id": r["branch_id"],
                "branch_name": r["branch_name"],
                "member_count": r["member_count"]
            }
            for r in results
        ]

    async def _get_financial_metrics(
        self,
        organization_id: Any,
        period_start: datetime,
        period_end: datetime,
        branch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get financial metrics from donations.

        Args:
            organization_id: Organization ID (ObjectId or string)
            period_start: Period start date
            period_end: Period end date
            branch_id: Optional branch filter

        Returns:
            Dict with financial metrics
        """
        match_filter: Dict[str, Any] = {
            "organization_id": organization_id,
            "status": "completed",
            "created_at": {"$gte": period_start, "$lte": period_end}
        }

        # Note: donations might not have branch_id, link through donor
        # For now, we'll aggregate all donations for the organization

        pipeline = [
            {"$match": match_filter},
            {
                "$group": {
                    "_id": None,
                    "total_amount": {"$sum": "$amount"},
                    "unique_donors": {"$addToSet": "$donor_id"},
                    "donation_count": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "total_amount": 1,
                    "donor_count": {"$size": "$unique_donors"},
                    "donation_count": 1,
                    "average_donation": {
                        "$cond": {
                            "if": {"$gt": ["$donation_count", 0]},
                            "then": {"$divide": ["$total_amount", "$donation_count"]},
                            "else": 0
                        }
                    }
                }
            }
        ]

        results = await self.db.donations.aggregate(pipeline).to_list(length=1)

        if results:
            result = results[0]
            return {
                "total_donations": round(result.get("total_amount", 0), 2),
                "total_donors": result.get("donor_count", 0),
                "average_donation": round(result.get("average_donation", 0), 2)
            }

        return {
            "total_donations": 0.0,
            "total_donors": 0,
            "average_donation": 0.0
        }

    async def _get_growth_metrics(
        self,
        organization_id: Any,
        period: str,
        period_start: datetime,
        period_end: datetime,
        branch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate growth metrics comparing current vs previous period.

        Args:
            organization_id: Organization ID (ObjectId or string)
            period: Period string
            period_start: Current period start
            period_end: Current period end
            branch_id: Optional branch filter

        Returns:
            Dict with growth metrics
        """
        base_filter: Dict[str, Any] = {"organization_id": organization_id}
        if branch_id:
            try:
                base_filter["branch_id"] = ObjectId(branch_id)
            except Exception:
                base_filter["branch_id"] = branch_id

        # Count new members in current period
        new_members_count = await self.db.users.count_documents({
            **base_filter,
            "created_at": {"$gte": period_start, "$lte": period_end}
        })

        # Count total members at end of current period
        current_total = await self.db.users.count_documents({
            **base_filter,
            "created_at": {"$lte": period_end}
        })

        # Calculate previous period
        period_duration = period_end - period_start
        previous_period_start = period_start - period_duration
        previous_period_end = period_start

        # Count total members at end of previous period
        previous_total = await self.db.users.count_documents({
            **base_filter,
            "created_at": {"$lte": previous_period_end}
        })

        # Calculate growth rate
        if previous_total > 0:
            growth_rate = ((current_total - previous_total) / previous_total) * 100
        else:
            growth_rate = 100.0 if current_total > 0 else 0.0

        return {
            "new_members_count": new_members_count,
            "growth_rate": round(growth_rate, 2)
        }

    async def _get_member_trend(
        self,
        organization_id: Any,
        period_start: datetime,
        period_end: datetime,
        branch_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get member count trend over time.

        Args:
            organization_id: Organization ID (ObjectId or string)
            period_start: Period start date
            period_end: Period end date
            branch_id: Optional branch filter

        Returns:
            List of trend data points
        """
        # For simplicity, we'll group by day
        # In production, you might want to adjust granularity based on period

        base_filter: Dict[str, Any] = {"organization_id": organization_id}
        if branch_id:
            try:
                base_filter["branch_id"] = ObjectId(branch_id)
            except Exception:
                base_filter["branch_id"] = branch_id

        pipeline = [
            {"$match": {**base_filter, "created_at": {"$lte": period_end}}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}},
            {"$limit": 30}  # Last 30 data points
        ]

        results = await self.db.users.aggregate(pipeline).to_list(length=None)

        # Convert to cumulative counts
        cumulative_count = 0
        trend_data = []

        for result in results:
            cumulative_count += result["count"]
            trend_data.append({
                "date": result["_id"],
                "count": cumulative_count
            })

        return trend_data


# Singleton instance
_service: Optional[MemberAnalyticsService] = None


def get_member_analytics_service(db: AsyncIOMotorDatabase) -> MemberAnalyticsService:
    """
    Get member analytics service instance.

    Args:
        db: MongoDB database instance

    Returns:
        MemberAnalyticsService instance
    """
    return MemberAnalyticsService(db)
