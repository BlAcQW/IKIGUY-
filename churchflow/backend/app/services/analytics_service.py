"""
Analytics Service for ChurchFlow.

Tracks usage metrics and costs for conferences, kiosk interactions,
voice calls, and SMS notifications.
"""

import logging
import os
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class ChurchFlowAnalyticsService:
    """
    Analytics service for ChurchFlow.

    Provides conference-specific analytics for kiosk usage, communication costs,
    and engagement metrics.
    """

    def __init__(self):
        """Initialize ChurchFlow analytics service."""
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.logger = logging.getLogger(__name__)
        self.initialized = False

    async def initialize(self, mongodb_uri: str, database_name: str = "kasaai_core") -> bool:
        """
        Initialize analytics service with database connection.

        Args:
            mongodb_uri: MongoDB connection URI
            database_name: Database name

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            client = AsyncIOMotorClient(mongodb_uri)
            self.db = client[database_name]
            self.initialized = True
            self.logger.info("Analytics service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize analytics service: {e}")
            return False

    async def get_conference_costs(
        self,
        conference_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive cost breakdown for a conference.

        Tracks kiosk interactions, voice calls, and SMS costs.

        Args:
            conference_id: Conference ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with conference costs
        """
        if not self.initialized:
            self.logger.warning("Analytics service not initialized")
            return {
                "conference_id": conference_id,
                "error": "Analytics service not initialized"
            }

        try:
            # Set date range if not provided
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=90)
            if not end_date:
                end_date = datetime.now(timezone.utc)

            # Query wallet transactions for this conference
            wallet_transactions = self.db["wallet_transactions"]

            # Get kiosk interaction metrics
            kiosk_pipeline = [
                {
                    "$match": {
                        "metadata.conference_id": conference_id,
                        "metadata.service": "churchflow_kiosk",
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$metadata.interaction_type",
                        "total_cost": {"$sum": "$amount"},
                        "interaction_count": {"$sum": 1},
                        "total_duration_seconds": {"$sum": "$metadata.duration_seconds"}
                    }
                }
            ]

            kiosk_results = await wallet_transactions.aggregate(kiosk_pipeline).to_list(length=100)

            # Format kiosk interactions
            kiosk_interactions = {}
            total_kiosk_cost = 0.0
            total_kiosk_count = 0
            total_kiosk_duration = 0

            for result in kiosk_results:
                interaction_type = result["_id"] or "other"
                cost = abs(float(result["total_cost"]))
                count = result["interaction_count"]
                duration = result["total_duration_seconds"]

                kiosk_interactions[interaction_type] = {
                    "cost": cost,
                    "count": count,
                    "duration_seconds": duration,
                    "average_duration": duration / count if count > 0 else 0.0
                }

                total_kiosk_cost += cost
                total_kiosk_count += count
                total_kiosk_duration += duration

            # Get voice call metrics
            voice_pipeline = [
                {
                    "$match": {
                        "metadata.conference_id": conference_id,
                        "metadata.service": "churchflow_voice",
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$metadata.purpose",
                        "total_cost": {"$sum": "$amount"},
                        "call_count": {"$sum": 1},
                        "total_duration_minutes": {"$sum": "$metadata.duration_minutes"}
                    }
                }
            ]

            voice_results = await wallet_transactions.aggregate(voice_pipeline).to_list(length=100)

            # Format voice calls
            voice_calls = {}
            total_voice_cost = 0.0
            total_voice_count = 0
            total_voice_duration = 0.0

            for result in voice_results:
                purpose = result["_id"] or "other"
                cost = abs(float(result["total_cost"]))
                count = result["call_count"]
                duration = float(result["total_duration_minutes"])

                voice_calls[purpose] = {
                    "cost": cost,
                    "count": count,
                    "duration_minutes": duration,
                    "average_duration": duration / count if count > 0 else 0.0
                }

                total_voice_cost += cost
                total_voice_count += count
                total_voice_duration += duration

            # Get SMS metrics
            sms_pipeline = [
                {
                    "$match": {
                        "metadata.conference_id": conference_id,
                        "metadata.service": "churchflow_sms",
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$metadata.purpose",
                        "total_cost": {"$sum": "$amount"},
                        "message_count": {"$sum": "$metadata.message_count"}
                    }
                }
            ]

            sms_results = await wallet_transactions.aggregate(sms_pipeline).to_list(length=100)

            # Format SMS
            sms_messages = {}
            total_sms_cost = 0.0
            total_sms_count = 0

            for result in sms_results:
                purpose = result["_id"] or "other"
                cost = abs(float(result["total_cost"]))
                count = result["message_count"]

                sms_messages[purpose] = {
                    "cost": cost,
                    "count": count
                }

                total_sms_cost += cost
                total_sms_count += count

            # Calculate totals
            total_cost = total_kiosk_cost + total_voice_cost + total_sms_cost

            return {
                "conference_id": conference_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_cost": total_cost,
                "kiosk": {
                    "total_cost": total_kiosk_cost,
                    "interaction_count": total_kiosk_count,
                    "total_duration_seconds": total_kiosk_duration,
                    "by_type": kiosk_interactions
                },
                "voice_calls": {
                    "total_cost": total_voice_cost,
                    "call_count": total_voice_count,
                    "total_duration_minutes": total_voice_duration,
                    "by_purpose": voice_calls
                },
                "sms": {
                    "total_cost": total_sms_cost,
                    "message_count": total_sms_count,
                    "by_purpose": sms_messages
                },
                "cost_distribution": {
                    "kiosk_percent": (total_kiosk_cost / total_cost * 100) if total_cost > 0 else 0.0,
                    "voice_percent": (total_voice_cost / total_cost * 100) if total_cost > 0 else 0.0,
                    "sms_percent": (total_sms_cost / total_cost * 100) if total_cost > 0 else 0.0
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to get conference costs: {e}")
            return {
                "conference_id": conference_id,
                "error": str(e)
            }

    async def get_organization_usage(
        self,
        organization_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get usage summary for an organization across all conferences.

        Args:
            organization_id: Organization ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with organization usage
        """
        if not self.initialized:
            self.logger.warning("Analytics service not initialized")
            return {
                "organization_id": organization_id,
                "error": "Analytics service not initialized"
            }

        try:
            # Set date range if not provided
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=90)
            if not end_date:
                end_date = datetime.now(timezone.utc)

            # Query wallet transactions
            wallet_transactions = self.db["wallet_transactions"]

            pipeline = [
                {
                    "$match": {
                        "user_id": organization_id,
                        "metadata.service": {"$in": ["churchflow_kiosk", "churchflow_voice", "churchflow_sms"]},
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$metadata.service",
                        "total_cost": {"$sum": "$amount"},
                        "activity_count": {"$sum": 1}
                    }
                }
            ]

            results = await wallet_transactions.aggregate(pipeline).to_list(length=100)

            # Format results
            services = {}
            total_cost = 0.0
            total_activities = 0

            for result in results:
                service = result["_id"].replace("churchflow_", "") if result["_id"] else "other"
                cost = abs(float(result["total_cost"]))
                count = result["activity_count"]

                services[service] = {
                    "cost": cost,
                    "activity_count": count
                }

                total_cost += cost
                total_activities += count

            # Get conferences count
            conferences_pipeline = [
                {
                    "$match": {
                        "user_id": organization_id,
                        "metadata.service": {"$in": ["churchflow_kiosk", "churchflow_voice", "churchflow_sms"]},
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$metadata.conference_id"
                    }
                }
            ]

            conferences_result = await wallet_transactions.aggregate(conferences_pipeline).to_list(length=1000)
            unique_conferences = len(conferences_result)

            return {
                "organization_id": organization_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_cost": total_cost,
                "total_activities": total_activities,
                "unique_conferences": unique_conferences,
                "services": services
            }

        except Exception as e:
            self.logger.error(f"Failed to get organization usage: {e}")
            return {
                "organization_id": organization_id,
                "error": str(e)
            }

    async def get_kiosk_engagement_metrics(
        self,
        conference_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get detailed kiosk engagement metrics for a conference.

        Args:
            conference_id: Conference ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with kiosk engagement metrics
        """
        if not self.initialized:
            self.logger.warning("Analytics service not initialized")
            return {
                "conference_id": conference_id,
                "error": "Analytics service not initialized"
            }

        try:
            # Set date range if not provided
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=90)
            if not end_date:
                end_date = datetime.now(timezone.utc)

            # Query wallet transactions
            wallet_transactions = self.db["wallet_transactions"]

            pipeline = [
                {
                    "$match": {
                        "metadata.conference_id": conference_id,
                        "metadata.service": "churchflow_kiosk",
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_interactions": {"$sum": 1},
                        "unique_members": {"$addToSet": "$metadata.member_name"},
                        "total_duration": {"$sum": "$metadata.duration_seconds"},
                        "avg_duration": {"$avg": "$metadata.duration_seconds"}
                    }
                }
            ]

            result = await wallet_transactions.aggregate(pipeline).to_list(length=1)

            if not result:
                return {
                    "conference_id": conference_id,
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    "total_interactions": 0,
                    "unique_members": 0,
                    "message": "No kiosk interactions found"
                }

            data = result[0]

            return {
                "conference_id": conference_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_interactions": data["total_interactions"],
                "unique_members": len([m for m in data["unique_members"] if m]),
                "total_duration_seconds": data["total_duration"],
                "average_duration_seconds": float(data["avg_duration"])
            }

        except Exception as e:
            self.logger.error(f"Failed to get kiosk engagement metrics: {e}")
            return {
                "conference_id": conference_id,
                "error": str(e)
            }


# Global service instance
_analytics_service: Optional[ChurchFlowAnalyticsService] = None


async def get_analytics_service() -> ChurchFlowAnalyticsService:
    """
    Get or create the global analytics service instance.

    Returns:
        ChurchFlowAnalyticsService instance
    """
    global _analytics_service

    if _analytics_service is None:
        _analytics_service = ChurchFlowAnalyticsService()

        # Initialize with environment variables
        mongodb_uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        await _analytics_service.initialize(mongodb_uri, database_name="kasaai_core")

    return _analytics_service
