"""
Voice service for EstateFlow.

Manages voice call records, configuration, and statistics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.voice import (
    VoiceCall,
    VoiceConfig,
    VoiceConfigUpdate,
    CallStats,
    CallStatus,
    CallOutcome,
)

logger = logging.getLogger(__name__)


class VoiceService:
    """Service for voice agent operations."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.calls_collection = database["voice_calls"]
        self.config_collection = database["voice_config"]

    def _convert_doc(self, doc: dict) -> dict:
        """Convert MongoDB document for Pydantic."""
        if doc and "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    async def list_calls(
        self,
        organization_id: str,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> Tuple[List[VoiceCall], int]:
        """List voice calls for an organization."""
        query: Dict[str, Any] = {"organization_id": organization_id}
        if status:
            query["status"] = status

        total = await self.calls_collection.count_documents(query)

        cursor = (
            self.calls_collection.find(query)
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )

        calls = []
        async for doc in cursor:
            calls.append(VoiceCall(**self._convert_doc(doc)))

        return calls, total

    async def get_call(
        self, call_id: str, organization_id: str
    ) -> Optional[VoiceCall]:
        """Get a single call by ID."""
        try:
            doc = await self.calls_collection.find_one(
                {"_id": ObjectId(call_id), "organization_id": organization_id}
            )
            if doc:
                return VoiceCall(**self._convert_doc(doc))
        except Exception:
            pass
        return None

    async def create_call(
        self, call_data: dict, organization_id: str
    ) -> VoiceCall:
        """Record a new voice call."""
        call_data["organization_id"] = organization_id
        call_data["created_at"] = datetime.utcnow()

        result = await self.calls_collection.insert_one(call_data)
        call_data["id"] = str(result.inserted_id)
        call_data.pop("_id", None)

        return VoiceCall(**call_data)

    async def get_stats(self, organization_id: str) -> CallStats:
        """Get voice call statistics."""
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        total = await self.calls_collection.count_documents(
            {"organization_id": organization_id}
        )
        today = await self.calls_collection.count_documents(
            {"organization_id": organization_id, "created_at": {"$gte": today_start}}
        )

        # Average duration
        pipeline = [
            {"$match": {"organization_id": organization_id, "status": "completed"}},
            {"$group": {"_id": None, "avg_duration": {"$avg": "$duration_seconds"}}},
        ]
        result = await self.calls_collection.aggregate(pipeline).to_list(1)
        avg_duration = int(result[0]["avg_duration"]) if result else 0

        # Tours scheduled
        tours = await self.calls_collection.count_documents(
            {"organization_id": organization_id, "outcome": CallOutcome.TOUR_SCHEDULED}
        )

        # Calls by outcome
        outcome_pipeline = [
            {"$match": {"organization_id": organization_id}},
            {"$group": {"_id": "$outcome", "count": {"$sum": 1}}},
        ]
        outcome_results = await self.calls_collection.aggregate(
            outcome_pipeline
        ).to_list(20)
        by_outcome = {r["_id"]: r["count"] for r in outcome_results if r["_id"]}

        # Calls by status
        status_pipeline = [
            {"$match": {"organization_id": organization_id}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        status_results = await self.calls_collection.aggregate(
            status_pipeline
        ).to_list(20)
        by_status = {r["_id"]: r["count"] for r in status_results if r["_id"]}

        completed = by_status.get("completed", 0)
        satisfaction = (completed / total * 100) if total > 0 else 0

        return CallStats(
            total_calls=total,
            calls_today=today,
            avg_duration_seconds=avg_duration,
            tours_scheduled=tours,
            satisfaction_rate=round(satisfaction, 1),
            calls_by_outcome=by_outcome,
            calls_by_status=by_status,
        )

    async def get_config(self, organization_id: str) -> VoiceConfig:
        """Get voice agent configuration."""
        doc = await self.config_collection.find_one(
            {"organization_id": organization_id}
        )
        if doc:
            doc.pop("_id", None)
            return VoiceConfig(**doc)
        return VoiceConfig(organization_id=organization_id)

    async def update_config(
        self, organization_id: str, updates: VoiceConfigUpdate
    ) -> VoiceConfig:
        """Update voice agent configuration."""
        update_data = {
            k: v for k, v in updates.model_dump().items() if v is not None
        }
        update_data["updated_at"] = datetime.utcnow()

        await self.config_collection.update_one(
            {"organization_id": organization_id},
            {"$set": update_data},
            upsert=True,
        )

        return await self.get_config(organization_id)
