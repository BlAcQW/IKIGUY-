"""
Unified Analytics Service for Cross-Service Cost Aggregation.

Aggregates costs and metrics across all services for assistants:
- VAPI call logs and costs
- Vonage phone call costs
- Twilio messaging costs
- LLM inference costs
- TTS synthesis costs
- ASR transcription costs

This service provides a single point to query all costs associated with
a VAPI assistant ID or user across all integrated services.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class UnifiedAnalyticsService:
    """
    Unified analytics service for cross-service cost aggregation.

    Provides comprehensive cost tracking and analytics across:
    - Voice AI (VAPI)
    - Phone services (Vonage, Twilio)
    - AI services (LLM, TTS, ASR)
    """

    def __init__(self, db):
        """
        Initialize unified analytics service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.analytics_collection = db.analytics_data
        self.wallet_transactions_collection = db.wallet_transactions
        self.vapi_calls_collection = db.vapi_call_logs

        logger.info("Unified Analytics Service initialized")

    async def get_assistant_costs(
        self,
        assistant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive cost breakdown for a VAPI assistant across all services.

        Args:
            assistant_id: VAPI assistant ID
            start_date: Start date for analytics (default: 30 days ago)
            end_date: End date for analytics (default: now)
            user_id: Optional user ID filter

        Returns:
            Dictionary with comprehensive cost breakdown:
            {
                "assistant_id": str,
                "period": {"start": str, "end": str},
                "total_cost": float,
                "cost_breakdown": {
                    "vapi_calls": {...},
                    "vonage_calls": {...},
                    "twilio_messages": {...},
                    "llm_inference": {...},
                    "tts_synthesis": {...},
                    "asr_transcription": {...}
                },
                "usage_metrics": {...},
                "trends": {...}
            }
        """
        try:
            # Default to last 30 days
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            logger.info(f"Getting costs for assistant {assistant_id} from {start_date} to {end_date}")

            # Get VAPI call costs
            vapi_costs = await self._get_vapi_costs(assistant_id, start_date, end_date, user_id)

            # Get Vonage call costs
            vonage_costs = await self._get_vonage_costs(assistant_id, start_date, end_date, user_id)

            # Get Twilio messaging costs
            twilio_costs = await self._get_twilio_costs(assistant_id, start_date, end_date, user_id)

            # Get LLM inference costs
            llm_costs = await self._get_llm_costs(assistant_id, start_date, end_date, user_id)

            # Get TTS synthesis costs
            tts_costs = await self._get_tts_costs(assistant_id, start_date, end_date, user_id)

            # Get ASR transcription costs
            asr_costs = await self._get_asr_costs(assistant_id, start_date, end_date, user_id)

            # Calculate total cost
            total_cost = (
                vapi_costs["total_cost"] +
                vonage_costs["total_cost"] +
                twilio_costs["total_cost"] +
                llm_costs["total_cost"] +
                tts_costs["total_cost"] +
                asr_costs["total_cost"]
            )

            # Build comprehensive response
            return {
                "assistant_id": assistant_id,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": (end_date - start_date).days
                },
                "total_cost": round(total_cost, 4),
                "currency": "USD",
                "cost_breakdown": {
                    "vapi_calls": vapi_costs,
                    "vonage_calls": vonage_costs,
                    "twilio_messages": twilio_costs,
                    "llm_inference": llm_costs,
                    "tts_synthesis": tts_costs,
                    "asr_transcription": asr_costs
                },
                "usage_metrics": {
                    "total_calls": vapi_costs["call_count"] + vonage_costs["call_count"],
                    "total_messages": twilio_costs["message_count"],
                    "total_llm_tokens": llm_costs["total_tokens"],
                    "total_tts_characters": tts_costs["total_characters"],
                    "total_asr_duration_seconds": asr_costs["total_duration_seconds"]
                },
                "cost_distribution": {
                    "vapi_percentage": round((vapi_costs["total_cost"] / total_cost * 100) if total_cost > 0 else 0, 2),
                    "vonage_percentage": round((vonage_costs["total_cost"] / total_cost * 100) if total_cost > 0 else 0, 2),
                    "twilio_percentage": round((twilio_costs["total_cost"] / total_cost * 100) if total_cost > 0 else 0, 2),
                    "llm_percentage": round((llm_costs["total_cost"] / total_cost * 100) if total_cost > 0 else 0, 2),
                    "tts_percentage": round((tts_costs["total_cost"] / total_cost * 100) if total_cost > 0 else 0, 2),
                    "asr_percentage": round((asr_costs["total_cost"] / total_cost * 100) if total_cost > 0 else 0, 2)
                },
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get assistant costs: {e}", exc_info=True)
            raise

    async def _get_vapi_costs(
        self,
        assistant_id: str,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get VAPI call costs from call logs.

        Returns:
            {
                "total_cost": float,
                "call_count": int,
                "total_duration_minutes": float,
                "avg_cost_per_call": float,
                "successful_calls": int,
                "failed_calls": int
            }
        """
        try:
            match_filter = {
                "assistant_id": assistant_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            }
            if user_id:
                match_filter["user_id"] = user_id

            # Aggregate VAPI call data
            pipeline = [
                {"$match": match_filter},
                {"$group": {
                    "_id": None,
                    "total_cost": {"$sum": "$cost"},
                    "call_count": {"$sum": 1},
                    "total_duration_seconds": {"$sum": "$duration_seconds"},
                    "successful_calls": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
                    "failed_calls": {"$sum": {"$cond": [{"$ne": ["$status", "completed"]}, 1, 0]}}
                }}
            ]

            result = await self.vapi_calls_collection.aggregate(pipeline).to_list(length=1)

            if result:
                data = result[0]
                total_duration_seconds = data.get("total_duration_seconds", 0)
                call_count = data.get("call_count", 0)

                return {
                    "total_cost": float(data.get("total_cost", 0)),
                    "call_count": call_count,
                    "total_duration_minutes": round(total_duration_seconds / 60, 2) if total_duration_seconds else 0,
                    "avg_duration_minutes": round((total_duration_seconds / 60 / call_count), 2) if call_count else 0,
                    "avg_cost_per_call": round(float(data.get("total_cost", 0)) / call_count, 4) if call_count else 0,
                    "successful_calls": data.get("successful_calls", 0),
                    "failed_calls": data.get("failed_calls", 0),
                    "success_rate": round((data.get("successful_calls", 0) / call_count * 100), 2) if call_count else 0
                }

            return {
                "total_cost": 0.0,
                "call_count": 0,
                "total_duration_minutes": 0.0,
                "avg_duration_minutes": 0.0,
                "avg_cost_per_call": 0.0,
                "successful_calls": 0,
                "failed_calls": 0,
                "success_rate": 0.0
            }

        except Exception as e:
            logger.error(f"Failed to get VAPI costs: {e}")
            return {"total_cost": 0.0, "call_count": 0, "total_duration_minutes": 0.0, "avg_cost_per_call": 0.0, "successful_calls": 0, "failed_calls": 0, "success_rate": 0.0, "avg_duration_minutes": 0.0}

    async def _get_vonage_costs(
        self,
        assistant_id: str,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get Vonage call costs from wallet transactions.

        Returns:
            {
                "total_cost": float,
                "call_count": int,
                "total_duration_minutes": float
            }
        """
        try:
            match_filter = {
                "metadata.service": "vonage",
                "metadata.assistant_id": assistant_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            }
            if user_id:
                match_filter["user_id"] = user_id

            # Aggregate Vonage transaction data
            pipeline = [
                {"$match": match_filter},
                {"$group": {
                    "_id": None,
                    "total_cost": {"$sum": "$amount"},
                    "call_count": {"$sum": 1},
                    "total_duration_seconds": {"$sum": "$metadata.duration_seconds"}
                }}
            ]

            result = await self.wallet_transactions_collection.aggregate(pipeline).to_list(length=1)

            if result:
                data = result[0]
                total_duration_seconds = data.get("total_duration_seconds", 0)

                return {
                    "total_cost": float(data.get("total_cost", 0)),
                    "call_count": data.get("call_count", 0),
                    "total_duration_minutes": round(total_duration_seconds / 60, 2) if total_duration_seconds else 0
                }

            return {
                "total_cost": 0.0,
                "call_count": 0,
                "total_duration_minutes": 0.0
            }

        except Exception as e:
            logger.error(f"Failed to get Vonage costs: {e}")
            return {"total_cost": 0.0, "call_count": 0, "total_duration_minutes": 0.0}

    async def _get_twilio_costs(
        self,
        assistant_id: str,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get Twilio messaging costs from wallet transactions.

        Returns:
            {
                "total_cost": float,
                "message_count": int
            }
        """
        try:
            match_filter = {
                "metadata.service": "twilio",
                "metadata.assistant_id": assistant_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            }
            if user_id:
                match_filter["user_id"] = user_id

            # Aggregate Twilio transaction data
            pipeline = [
                {"$match": match_filter},
                {"$group": {
                    "_id": None,
                    "total_cost": {"$sum": "$amount"},
                    "message_count": {"$sum": 1}
                }}
            ]

            result = await self.wallet_transactions_collection.aggregate(pipeline).to_list(length=1)

            if result:
                data = result[0]
                return {
                    "total_cost": float(data.get("total_cost", 0)),
                    "message_count": data.get("message_count", 0)
                }

            return {
                "total_cost": 0.0,
                "message_count": 0
            }

        except Exception as e:
            logger.error(f"Failed to get Twilio costs: {e}")
            return {"total_cost": 0.0, "message_count": 0}

    async def _get_llm_costs(
        self,
        assistant_id: str,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get LLM inference costs from wallet transactions.

        Returns:
            {
                "total_cost": float,
                "request_count": int,
                "total_tokens": int
            }
        """
        try:
            match_filter = {
                "metadata.service": "llm",
                "metadata.assistant_id": assistant_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            }
            if user_id:
                match_filter["user_id"] = user_id

            # Aggregate LLM transaction data
            pipeline = [
                {"$match": match_filter},
                {"$group": {
                    "_id": None,
                    "total_cost": {"$sum": "$amount"},
                    "request_count": {"$sum": 1},
                    "total_tokens": {"$sum": "$metadata.total_tokens"}
                }}
            ]

            result = await self.wallet_transactions_collection.aggregate(pipeline).to_list(length=1)

            if result:
                data = result[0]
                return {
                    "total_cost": float(data.get("total_cost", 0)),
                    "request_count": data.get("request_count", 0),
                    "total_tokens": data.get("total_tokens", 0)
                }

            return {
                "total_cost": 0.0,
                "request_count": 0,
                "total_tokens": 0
            }

        except Exception as e:
            logger.error(f"Failed to get LLM costs: {e}")
            return {"total_cost": 0.0, "request_count": 0, "total_tokens": 0}

    async def _get_tts_costs(
        self,
        assistant_id: str,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get TTS synthesis costs from wallet transactions.

        Returns:
            {
                "total_cost": float,
                "request_count": int,
                "total_characters": int
            }
        """
        try:
            match_filter = {
                "metadata.service": "tts",
                "metadata.assistant_id": assistant_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            }
            if user_id:
                match_filter["user_id"] = user_id

            # Aggregate TTS transaction data
            pipeline = [
                {"$match": match_filter},
                {"$group": {
                    "_id": None,
                    "total_cost": {"$sum": "$amount"},
                    "request_count": {"$sum": 1},
                    "total_characters": {"$sum": "$metadata.character_count"}
                }}
            ]

            result = await self.wallet_transactions_collection.aggregate(pipeline).to_list(length=1)

            if result:
                data = result[0]
                return {
                    "total_cost": float(data.get("total_cost", 0)),
                    "request_count": data.get("request_count", 0),
                    "total_characters": data.get("total_characters", 0)
                }

            return {
                "total_cost": 0.0,
                "request_count": 0,
                "total_characters": 0
            }

        except Exception as e:
            logger.error(f"Failed to get TTS costs: {e}")
            return {"total_cost": 0.0, "request_count": 0, "total_characters": 0}

    async def _get_asr_costs(
        self,
        assistant_id: str,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get ASR transcription costs from wallet transactions.

        Returns:
            {
                "total_cost": float,
                "request_count": int,
                "total_duration_seconds": float
            }
        """
        try:
            match_filter = {
                "metadata.service": "asr",
                "metadata.assistant_id": assistant_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            }
            if user_id:
                match_filter["user_id"] = user_id

            # Aggregate ASR transaction data
            pipeline = [
                {"$match": match_filter},
                {"$group": {
                    "_id": None,
                    "total_cost": {"$sum": "$amount"},
                    "request_count": {"$sum": 1},
                    "total_duration_seconds": {"$sum": "$metadata.audio_duration_seconds"}
                }}
            ]

            result = await self.wallet_transactions_collection.aggregate(pipeline).to_list(length=1)

            if result:
                data = result[0]
                return {
                    "total_cost": float(data.get("total_cost", 0)),
                    "request_count": data.get("request_count", 0),
                    "total_duration_seconds": data.get("total_duration_seconds", 0)
                }

            return {
                "total_cost": 0.0,
                "request_count": 0,
                "total_duration_seconds": 0
            }

        except Exception as e:
            logger.error(f"Failed to get ASR costs: {e}")
            return {"total_cost": 0.0, "request_count": 0, "total_duration_seconds": 0}


# Export the service class
__all__ = ["UnifiedAnalyticsService"]
