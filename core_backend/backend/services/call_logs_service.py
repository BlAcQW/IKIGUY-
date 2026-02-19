"""
Call Logs Service

MongoDB service for managing VAPI call logs with dual storage support
(MongoDB for fast queries + Supabase for analytics).
"""

from typing import List, Optional, Dict, Any, Union
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError
import os
import logging
from datetime import datetime, timedelta
from bson import ObjectId

from ..models.call_logs import (
    CallLog, CallLogCreate, CallLogUpdate, CallLogResponse,
    CallLogListResponse, CallLogFilter, CallAnalytics, CallStatus
)

logger = logging.getLogger(__name__)


class MongoDBCallLogsService:
    """MongoDB-based service for managing call logs."""

    def __init__(self):
        """Initialize the call logs service with MongoDB connection."""
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.collection: Optional[Collection] = None
        self._connect()

    def _connect(self):
        """Connect to MongoDB and set up the collection."""
        try:
            # Get MongoDB URL from environment
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin")
            database_name = os.getenv("MONGO_CORE_DATABASE", "kasaai_core")

            # Connect to MongoDB
            self.client = MongoClient(mongodb_url)
            self.db = self.client[database_name]

            # Get vapi_calls collection (contains comprehensive VAPI webhook call data)
            # Reason: vapi_calls has 5,398 records (73% with org_id) vs call_logs with 371 records
            # vapi_calls contains the actual call transcripts, summaries, and metadata from VAPI
            self.collection = self.db["vapi_calls"]

            # Create indexes for better performance
            try:
                # Index on call_id for fast lookups
                self.collection.create_index("call_id")

                # Common query indexes
                self.collection.create_index("assistant_id")
                self.collection.create_index("user_id")
                self.collection.create_index("organization_id")
                self.collection.create_index("automation_id")  # For filtering by automation
                self.collection.create_index("created_at")
                self.collection.create_index("start_time")

                # Compound indexes for common queries
                self.collection.create_index([("organization_id", ASCENDING), ("created_at", DESCENDING)])
                self.collection.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
                self.collection.create_index([("assistant_id", ASCENDING), ("status", ASCENDING)])

                # Text index for transcript search
                self.collection.create_index([("transcript", "text"), ("summary", "text")])

            except Exception as index_error:
                logger.warning(f"Could not create indexes (may already exist): {index_error}")

            logger.info(f"Connected to MongoDB for call logs service: {database_name}")

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
            self.db = None
            self.collection = None

    def is_connected(self) -> bool:
        """Check if the service is connected to MongoDB."""
        return self.client is not None and self.collection is not None

    async def create_call_log(self, call_data: CallLogCreate) -> CallLogResponse:
        """Create a new call log entry."""
        try:
            if not self.is_connected():
                return CallLogResponse(
                    success=False,
                    message="Database not connected"
                )

            # Convert to CallLog model with generated fields
            call_log = CallLog(**call_data.model_dump())

            # Convert to dict for MongoDB storage
            call_dict = call_log.model_dump()

            # Insert into MongoDB
            result = self.collection.insert_one(call_dict)

            # Update the call_log with the MongoDB _id
            call_log.id = str(result.inserted_id)

            logger.info(f"Created call log for call_id: {call_log.call_id}")

            return CallLogResponse(
                success=True,
                call_log=call_log,
                mongo_id=str(result.inserted_id),
                message="Call log created successfully"
            )

        except DuplicateKeyError:
            logger.warning(f"Call log already exists for call_id: {call_data.call_id}")
            return CallLogResponse(
                success=False,
                message=f"Call log already exists for call_id: {call_data.call_id}"
            )
        except Exception as e:
            logger.error(f"Error creating call log: {e}")
            return CallLogResponse(
                success=False,
                message=f"Error creating call log: {str(e)}"
            )

    async def update_call_log(self, call_id: str, update_data: CallLogUpdate) -> CallLogResponse:
        """Update an existing call log."""
        try:
            if not self.is_connected():
                return CallLogResponse(
                    success=False,
                    message="Database not connected"
                )

            # Prepare update data (exclude None values)
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            update_dict["updated_at"] = datetime.utcnow()

            # Update in MongoDB
            result = self.collection.update_one(
                {"call_id": call_id},
                {"$set": update_dict}
            )

            if result.matched_count == 0:
                return CallLogResponse(
                    success=False,
                    message=f"Call log not found for call_id: {call_id}"
                )

            # Retrieve updated document
            updated_doc = self.collection.find_one({"call_id": call_id})
            if updated_doc:
                updated_doc["id"] = str(updated_doc.pop("_id"))
                call_log = CallLog(**updated_doc)

                logger.info(f"Updated call log for call_id: {call_id}")

                return CallLogResponse(
                    success=True,
                    call_log=call_log,
                    message="Call log updated successfully"
                )

            return CallLogResponse(
                success=False,
                message="Could not retrieve updated call log"
            )

        except Exception as e:
            logger.error(f"Error updating call log: {e}")
            return CallLogResponse(
                success=False,
                message=f"Error updating call log: {str(e)}"
            )

    async def get_call_log(self, call_id: str) -> CallLogResponse:
        """Get a call log by call_id."""
        try:
            if not self.is_connected():
                return CallLogResponse(
                    success=False,
                    message="Database not connected"
                )

            doc = self.collection.find_one({"call_id": call_id})

            if not doc:
                return CallLogResponse(
                    success=False,
                    message=f"Call log not found for call_id: {call_id}"
                )

            # Convert MongoDB _id to id
            doc["id"] = str(doc.pop("_id"))
            call_log = CallLog(**doc)

            return CallLogResponse(
                success=True,
                call_log=call_log
            )

        except Exception as e:
            logger.error(f"Error getting call log: {e}")
            return CallLogResponse(
                success=False,
                message=f"Error getting call log: {str(e)}"
            )

    async def list_call_logs(
        self,
        filters: Optional[CallLogFilter] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: int = -1  # -1 for descending, 1 for ascending
    ) -> CallLogListResponse:
        """List call logs with optional filtering and pagination."""
        try:
            if not self.is_connected():
                return CallLogListResponse(
                    success=False,
                    message="Database not connected"
                )

            # Build query from filters
            query = {}
            logger.info(f"🔍 list_call_logs called with filters: {filters}")
            if filters:
                if filters.start_date:
                    query.setdefault("created_at", {})["$gte"] = filters.start_date
                if filters.end_date:
                    query.setdefault("created_at", {})["$lte"] = filters.end_date
                if filters.status:
                    query["status"] = filters.status.value
                if filters.direction:
                    query["direction"] = filters.direction.value
                if filters.assistant_id:
                    query["assistant_id"] = filters.assistant_id
                if filters.automation_id:
                    query["automation_id"] = filters.automation_id
                if filters.automation_name:
                    query["automation_name"] = {"$regex": filters.automation_name, "$options": "i"}
                if filters.campaign_id:
                    query["campaign_id"] = filters.campaign_id
                if filters.user_id:
                    query["user_id"] = filters.user_id
                if filters.organization_id:
                    query["organization_id"] = filters.organization_id
                if filters.customer_id:
                    query["customer_id"] = filters.customer_id
                if filters.from_phone:
                    query["from_phone"] = {"$regex": filters.from_phone, "$options": "i"}
                if filters.to_phone:
                    query["to_phone"] = {"$regex": filters.to_phone, "$options": "i"}
                if filters.keyword:
                    query["$text"] = {"$search": filters.keyword}
                if filters.sentiment:
                    query["sentiment"] = filters.sentiment
                if filters.tags:
                    query["tags"] = {"$in": filters.tags}
                if filters.min_duration is not None:
                    query.setdefault("duration", {})["$gte"] = filters.min_duration
                if filters.max_duration is not None:
                    query.setdefault("duration", {})["$lte"] = filters.max_duration
                if filters.min_cost is not None:
                    query.setdefault("cost", {})["$gte"] = filters.min_cost
                if filters.max_cost is not None:
                    query.setdefault("cost", {})["$lte"] = filters.max_cost

            # Calculate pagination
            skip = (page - 1) * page_size

            # Get total count
            logger.info(f"🔍 Query: {query}")
            total_count = self.collection.count_documents(query)
            logger.info(f"🔍 Total count: {total_count}")

            # Get paginated results
            cursor = self.collection.find(query).sort(sort_by, sort_order).skip(skip).limit(page_size)

            call_logs = []
            for doc in cursor:
                doc["id"] = str(doc.pop("_id"))
                call_logs.append(CallLog(**doc))

            total_pages = (total_count + page_size - 1) // page_size

            return CallLogListResponse(
                success=True,
                call_logs=call_logs,
                total_count=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )

        except Exception as e:
            logger.error(f"Error listing call logs: {e}")
            return CallLogListResponse(
                success=False,
                message=f"Error listing call logs: {str(e)}"
            )

    async def delete_call_log(self, call_id: str) -> CallLogResponse:
        """Delete a call log by call_id."""
        try:
            if not self.is_connected():
                return CallLogResponse(
                    success=False,
                    message="Database not connected"
                )

            result = self.collection.delete_one({"call_id": call_id})

            if result.deleted_count == 0:
                return CallLogResponse(
                    success=False,
                    message=f"Call log not found for call_id: {call_id}"
                )

            logger.info(f"Deleted call log for call_id: {call_id}")

            return CallLogResponse(
                success=True,
                message="Call log deleted successfully"
            )

        except Exception as e:
            logger.error(f"Error deleting call log: {e}")
            return CallLogResponse(
                success=False,
                message=f"Error deleting call log: {str(e)}"
            )

    async def get_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
        assistant_id: Optional[str] = None
    ) -> CallAnalytics:
        """Generate call analytics for a given time period."""
        try:
            if not self.is_connected():
                return CallAnalytics(
                    period_start=start_date,
                    period_end=end_date
                )

            # Build base query
            base_query = {
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }

            if organization_id:
                base_query["organization_id"] = organization_id
            if user_id:
                base_query["user_id"] = user_id
            if assistant_id:
                base_query["assistant_id"] = assistant_id

            # Aggregation pipeline for analytics
            pipeline = [
                {"$match": base_query},
                {
                    "$group": {
                        "_id": None,
                        "total_calls": {"$sum": 1},
                        "completed_calls": {
                            "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                        },
                        "failed_calls": {
                            "$sum": {"$cond": [{"$ne": ["$status", "completed"]}, 1, 0]}
                        },
                        "total_duration": {"$sum": "$duration"},
                        "total_cost": {"$sum": "$cost"},
                        "avg_duration": {"$avg": "$duration"},
                        "avg_cost": {"$avg": "$cost"}
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))

            if not result:
                return CallAnalytics(
                    period_start=start_date,
                    period_end=end_date
                )

            data = result[0]

            # Calculate success rate
            total_calls = data.get("total_calls", 0)
            completed_calls = data.get("completed_calls", 0)
            success_rate = (completed_calls / total_calls * 100) if total_calls > 0 else 0

            # Get sentiment distribution
            sentiment_pipeline = [
                {"$match": base_query},
                {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
            ]
            sentiment_results = list(self.collection.aggregate(sentiment_pipeline))
            sentiment_distribution = {item["_id"] or "unknown": item["count"] for item in sentiment_results}

            # Get top assistants
            assistant_pipeline = [
                {"$match": base_query},
                {"$group": {
                    "_id": "$assistant_id",
                    "assistant_name": {"$first": "$assistant_name"},
                    "call_count": {"$sum": 1},
                    "avg_duration": {"$avg": "$duration"},
                    "total_cost": {"$sum": "$cost"}
                }},
                {"$sort": {"call_count": -1}},
                {"$limit": 10}
            ]
            assistant_results = list(self.collection.aggregate(assistant_pipeline))
            top_assistants = [
                {
                    "assistant_id": item["_id"],
                    "assistant_name": item.get("assistant_name", "Unknown"),
                    "call_count": item["call_count"],
                    "avg_duration": item.get("avg_duration", 0),
                    "total_cost": item.get("total_cost", 0)
                }
                for item in assistant_results
            ]

            return CallAnalytics(
                period_start=start_date,
                period_end=end_date,
                total_calls=data.get("total_calls", 0),
                completed_calls=completed_calls,
                failed_calls=data.get("failed_calls", 0),
                total_duration=int(data.get("total_duration", 0)),
                average_duration=float(data.get("avg_duration", 0)),
                total_cost=float(data.get("total_cost", 0)),
                average_cost=float(data.get("avg_cost", 0)),
                success_rate=success_rate,
                sentiment_distribution=sentiment_distribution,
                top_assistants=top_assistants
            )

        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
            return CallAnalytics(
                period_start=start_date,
                period_end=end_date
            )


# Global service instance
call_logs_service = MongoDBCallLogsService()