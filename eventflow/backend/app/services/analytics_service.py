"""
Analytics Service for EventFlow.

Integrates with UnifiedAnalyticsService to provide event-specific cost tracking
and usage analytics across all services (VAPI, voice calls, SMS, etc.).
"""

import logging
import os
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from apps.shared.services.unified_analytics_service import UnifiedAnalyticsService
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class EventFlowAnalyticsService:
    """
    Analytics service for EventFlow.

    Provides event-specific analytics by leveraging the UnifiedAnalyticsService
    to aggregate costs from VAPI, Vonage, Twilio, and other services.
    """

    def __init__(self):
        """Initialize EventFlow analytics service."""
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.unified_analytics: Optional[UnifiedAnalyticsService] = None
        self.logger = logging.getLogger(__name__)
        self.initialized = False

    async def initialize(self, mongodb_uri: str, database_name: str = "kasaai_core") -> bool:
        """
        Initialize analytics service with database connection.

        Args:
            mongodb_uri: MongoDB connection URI
            database_name: Database name (default: kasaai_core for unified analytics)

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            client = AsyncIOMotorClient(mongodb_uri)
            self.db = client[database_name]
            self.unified_analytics = UnifiedAnalyticsService(self.db)
            self.initialized = True
            self.logger.info("Analytics service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize analytics service: {e}")
            return False

    async def get_event_costs(
        self,
        event_id: str,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive cost breakdown for an event.

        Aggregates costs from all assistants associated with the event.

        Args:
            event_id: Event ID
            user_id: Optional user ID filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with event costs breakdown
        """
        if not self.initialized:
            self.logger.warning("Analytics service not initialized")
            return {
                "event_id": event_id,
                "error": "Analytics service not initialized"
            }

        try:
            # Get event details to find associated assistants
            events_collection = self.db["events"]
            event = await events_collection.find_one({"_id": event_id})

            if not event:
                return {
                    "event_id": event_id,
                    "error": "Event not found"
                }

            # Get all assistant IDs associated with this event
            assistant_ids = event.get("assistant_ids", [])

            if not assistant_ids:
                return {
                    "event_id": event_id,
                    "event_name": event.get("name"),
                    "total_cost": 0.0,
                    "message": "No assistants associated with this event"
                }

            # Set date range if not provided
            if not start_date:
                start_date = event.get("created_at", datetime.now(timezone.utc) - timedelta(days=30))
            if not end_date:
                end_date = datetime.now(timezone.utc)

            # Aggregate costs from all assistants
            total_cost = 0.0
            assistants_breakdown = {}

            for assistant_id in assistant_ids:
                try:
                    costs = await self.unified_analytics.get_assistant_costs(
                        assistant_id=assistant_id,
                        start_date=start_date,
                        end_date=end_date,
                        user_id=user_id
                    )

                    total_cost += costs.get("total_cost", 0.0)
                    assistants_breakdown[assistant_id] = costs
                except Exception as e:
                    self.logger.error(f"Failed to get costs for assistant {assistant_id}: {e}")
                    assistants_breakdown[assistant_id] = {
                        "error": str(e)
                    }

            # Calculate combined metrics
            combined_metrics = self._combine_assistant_metrics(assistants_breakdown)

            return {
                "event_id": event_id,
                "event_name": event.get("name"),
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_cost": total_cost,
                "assistants_count": len(assistant_ids),
                "assistants_breakdown": assistants_breakdown,
                "combined_metrics": combined_metrics
            }

        except Exception as e:
            self.logger.error(f"Failed to get event costs: {e}")
            return {
                "event_id": event_id,
                "error": str(e)
            }

    async def get_user_usage_summary(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get usage summary for a user across all events.

        Args:
            user_id: User ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with user usage summary
        """
        if not self.initialized:
            self.logger.warning("Analytics service not initialized")
            return {
                "user_id": user_id,
                "error": "Analytics service not initialized"
            }

        try:
            # Set date range if not provided
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)

            # Query wallet transactions for this user
            wallet_transactions = self.db["wallet_transactions"]

            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$metadata.service",
                        "total_cost": {"$sum": "$amount"},
                        "transaction_count": {"$sum": 1}
                    }
                }
            ]

            results = await wallet_transactions.aggregate(pipeline).to_list(length=100)

            # Format results
            services = {}
            total_cost = 0.0
            total_transactions = 0

            for result in results:
                service = result["_id"] or "other"
                cost = abs(float(result["total_cost"]))
                count = result["transaction_count"]

                services[service] = {
                    "cost": cost,
                    "transaction_count": count
                }

                total_cost += cost
                total_transactions += count

            return {
                "user_id": user_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_cost": total_cost,
                "total_transactions": total_transactions,
                "services": services
            }

        except Exception as e:
            self.logger.error(f"Failed to get user usage summary: {e}")
            return {
                "user_id": user_id,
                "error": str(e)
            }

    async def get_task_communication_costs(
        self,
        task_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get communication costs for a specific task.

        Tracks costs for voice calls, SMS, and WhatsApp messages related to task follow-ups.

        Args:
            task_id: Task ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with task communication costs
        """
        if not self.initialized:
            self.logger.warning("Analytics service not initialized")
            return {
                "task_id": task_id,
                "error": "Analytics service not initialized"
            }

        try:
            # Set date range if not provided
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)

            # Query wallet transactions for this task
            wallet_transactions = self.db["wallet_transactions"]

            pipeline = [
                {
                    "$match": {
                        "metadata.task_id": task_id,
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$metadata.service",
                        "total_cost": {"$sum": "$amount"},
                        "communication_count": {"$sum": 1}
                    }
                }
            ]

            results = await wallet_transactions.aggregate(pipeline).to_list(length=100)

            # Format results
            services = {}
            total_cost = 0.0
            total_communications = 0

            for result in results:
                service = result["_id"] or "other"
                cost = abs(float(result["total_cost"]))
                count = result["communication_count"]

                services[service] = {
                    "cost": cost,
                    "communication_count": count
                }

                total_cost += cost
                total_communications += count

            return {
                "task_id": task_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_cost": total_cost,
                "total_communications": total_communications,
                "services": services
            }

        except Exception as e:
            self.logger.error(f"Failed to get task communication costs: {e}")
            return {
                "task_id": task_id,
                "error": str(e)
            }

    def _combine_assistant_metrics(self, assistants_breakdown: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine metrics from multiple assistants.

        Args:
            assistants_breakdown: Dictionary of assistant costs

        Returns:
            Combined metrics dictionary
        """
        combined = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_duration_minutes": 0.0,
            "vapi_cost": 0.0,
            "vonage_cost": 0.0,
            "twilio_cost": 0.0,
            "llm_cost": 0.0,
            "tts_cost": 0.0,
            "asr_cost": 0.0
        }

        for assistant_id, costs in assistants_breakdown.items():
            if "error" in costs:
                continue

            # Usage metrics
            usage_metrics = costs.get("usage_metrics", {})
            combined["total_calls"] += usage_metrics.get("total_calls", 0)
            combined["successful_calls"] += usage_metrics.get("successful_calls", 0)
            combined["failed_calls"] += usage_metrics.get("failed_calls", 0)
            combined["total_duration_minutes"] += usage_metrics.get("total_call_duration_minutes", 0.0)

            # Cost breakdown
            cost_breakdown = costs.get("cost_breakdown", {})
            combined["vapi_cost"] += cost_breakdown.get("vapi_calls", {}).get("total_cost", 0.0)
            combined["vonage_cost"] += cost_breakdown.get("vonage_calls", {}).get("total_cost", 0.0)
            combined["twilio_cost"] += cost_breakdown.get("twilio", {}).get("total_cost", 0.0)
            combined["llm_cost"] += cost_breakdown.get("llm", {}).get("total_cost", 0.0)
            combined["tts_cost"] += cost_breakdown.get("tts", {}).get("total_cost", 0.0)
            combined["asr_cost"] += cost_breakdown.get("asr", {}).get("total_cost", 0.0)

        # Calculate success rate
        if combined["total_calls"] > 0:
            combined["success_rate"] = combined["successful_calls"] / combined["total_calls"]
        else:
            combined["success_rate"] = 0.0

        # Calculate average duration
        if combined["total_calls"] > 0:
            combined["average_duration_minutes"] = combined["total_duration_minutes"] / combined["total_calls"]
        else:
            combined["average_duration_minutes"] = 0.0

        return combined


# Global service instance
_analytics_service: Optional[EventFlowAnalyticsService] = None


async def get_analytics_service() -> EventFlowAnalyticsService:
    """
    Get or create the global analytics service instance.

    Returns:
        EventFlowAnalyticsService instance
    """
    global _analytics_service

    if _analytics_service is None:
        _analytics_service = EventFlowAnalyticsService()

        # Initialize with environment variables
        mongodb_uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        await _analytics_service.initialize(mongodb_uri, database_name="kasaai_core")

    return _analytics_service
