"""
Call Logs Management Routes

This module provides comprehensive call logging, retrieval, and analysis
capabilities for VAPI interactions and automation monitoring.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from bson import ObjectId

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..auth import get_current_user_mongo
from ..mongo import get_database
from ..models.shared_models import StandardResponse
from ..middleware.organization_context import (
    get_organization_context,
    validate_organization_access
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/call-logs", tags=["Call Logs"])

# Models
class CallLogEntry(BaseModel):
    """Call log entry model with backward compatibility for MongoDB schema."""
    id: str = Field(..., description="Unique call log ID")
    call_id: str = Field(..., description="VAPI call ID")
    assistant_id: Optional[str] = Field(None, description="VAPI assistant ID")
    assistant_name: Optional[str] = Field(None, description="Assistant name")
    status: str = Field(default="unknown", description="Call status: completed, failed, missed, etc.")
    direction: str = Field(default="inbound", description="Call direction: inbound, outbound")
    from_phone: Optional[str] = Field(None, description="From phone number")
    to_phone: Optional[str] = Field(None, description="To phone number")
    start_time: Optional[datetime] = Field(None, description="Call start time")
    end_time: Optional[datetime] = Field(None, description="Call end time")
    duration: Optional[int] = Field(None, description="Call duration in seconds")
    ended_reason: Optional[str] = Field(None, description="Reason call ended (customer-busy, customer-ended-call, etc.)")
    transcript: Optional[str] = Field(None, description="Call transcript")
    summary: Optional[str] = Field(None, description="Call summary")
    sentiment: Optional[str] = Field(None, description="Sentiment analysis")
    confidence_score: Optional[float] = Field(None, description="Confidence score")
    keywords: List[str] = Field(default_factory=list, description="Keywords extracted")
    cost: Optional[float] = Field(None, description="Call cost in USD")
    tokens_used: Optional[int] = Field(None, description="Tokens used")
    customer_id: Optional[str] = Field(None, description="Customer ID")
    organization_id: Optional[str] = Field(None, description="Organization ID")
    user_id: Optional[str] = Field(None, description="User ID")
    vapi_data: Dict[str, Any] = Field(default_factory=dict, description="VAPI data")
    audio_quality: Optional[str] = Field(None, description="Audio quality")
    connection_quality: Optional[str] = Field(None, description="Connection quality")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: List[str] = Field(default_factory=list, description="Tags")
    created_at: Optional[datetime] = Field(None, description="Call timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    synced_to_supabase: Optional[bool] = Field(None, description="Synced to Supabase")
    supabase_id: Optional[str] = Field(None, description="Supabase ID")
    sync_error: Optional[str] = Field(None, description="Sync error")

class CallLogFilters(BaseModel):
    """Filters for call log queries matching actual MongoDB schema."""
    assistant_id: Optional[str] = Field(None, description="Filter by assistant ID")
    automation_id: Optional[str] = Field(None, description="Filter by automation ID")
    status: Optional[str] = Field(None, description="Filter by call status")
    direction: Optional[str] = Field(None, description="Filter by call direction")
    from_phone: Optional[str] = Field(None, description="Filter by from phone number")
    to_phone: Optional[str] = Field(None, description="Filter by to phone number")
    customer_id: Optional[str] = Field(None, description="Filter by customer ID")
    start_date: Optional[datetime] = Field(None, description="Start date for date range filter")
    end_date: Optional[datetime] = Field(None, description="End date for date range filter")
    min_duration: Optional[int] = Field(None, description="Minimum call duration filter")
    max_duration: Optional[int] = Field(None, description="Maximum call duration filter")
    min_cost: Optional[float] = Field(None, description="Minimum cost filter")
    max_cost: Optional[float] = Field(None, description="Maximum cost filter")
    has_transcript: Optional[bool] = Field(None, description="Filter calls with/without transcript")
    sentiment: Optional[str] = Field(None, description="Filter by sentiment")

class CallLogStats(BaseModel):
    """Call log statistics model."""
    total_calls: int = Field(..., description="Total number of calls")
    successful_calls: int = Field(..., description="Number of successful calls")
    failed_calls: int = Field(..., description="Number of failed calls")
    total_duration: float = Field(..., description="Total call duration in seconds")
    total_cost: float = Field(..., description="Total cost in USD")
    avg_duration: float = Field(..., description="Average call duration")
    avg_cost: float = Field(..., description="Average call cost")
    avg_sentiment: Optional[float] = Field(None, description="Average sentiment score")
    success_rate: float = Field(..., description="Success rate percentage")
    total_tool_calls: int = Field(..., description="Total number of tool calls")
    unique_assistants: int = Field(..., description="Number of unique assistants")
    unique_phone_numbers: int = Field(..., description="Number of unique phone numbers")
    date_range: Dict[str, datetime] = Field(..., description="Date range of the data")

class ToolCallAnalysis(BaseModel):
    """Tool call analysis model."""
    tool_name: str = Field(..., description="Tool name")
    total_calls: int = Field(..., description="Total times this tool was called")
    success_rate: float = Field(..., description="Success rate for this tool")
    avg_execution_time: Optional[float] = Field(None, description="Average execution time")
    error_rate: float = Field(..., description="Error rate for this tool")
    common_errors: List[str] = Field(..., description="Most common error messages")

class CallLogService:
    """Service for call log management."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        # Use vapi_calls collection as the primary source of call data
        self.call_logs_collection = db.vapi_calls
        self.assistants_collection = db.assistants
        self.tool_calls_collection = db.tool_calls

    async def create_call_log(self, call_data: Dict[str, Any]) -> str:
        """Create a new call log entry."""
        try:
            call_log = {
                "_id": ObjectId(),
                "id": call_data.get("id", str(ObjectId())),
                "call_id": call_data.get("call_id"),
                "assistant_id": call_data.get("assistant_id"),
                "assistant_name": call_data.get("assistant_name"),
                "status": call_data.get("status", "unknown"),
                "direction": call_data.get("direction", "inbound"),
                "from_phone": call_data.get("from_phone"),
                "to_phone": call_data.get("to_phone"),
                "start_time": call_data.get("start_time"),
                "end_time": call_data.get("end_time"),
                "duration": call_data.get("duration"),
                "cost": call_data.get("cost"),
                "transcript": call_data.get("transcript"),
                "summary": call_data.get("summary"),
                "sentiment": call_data.get("sentiment"),
                "sentiment_score": call_data.get("sentiment_score"),
                "tool_calls": call_data.get("tool_calls", []),
                "webhook_data": call_data.get("webhook_data"),
                "metadata": call_data.get("metadata", {}),
                "customer_id": call_data.get("customer_id"),
                "created_at": call_data.get("created_at", datetime.now(timezone.utc)),
                "updated_at": datetime.now(timezone.utc)
            }

            result = await self.call_logs_collection.insert_one(call_log)
            logger.info(f"Created call log: {result.inserted_id}")

            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to create call log: {e}")
            raise

    async def get_call_logs(
        self,
        filters: CallLogFilters,
        page: int = 1,
        per_page: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get call logs with filtering and pagination.

        Args:
            filters: Call log filters
            page: Page number
            per_page: Results per page
            sort_by: Sort field
            sort_order: Sort direction (asc/desc)
            organization_id: Organization ID for filtering

        Returns:
            Dictionary with logs and pagination info
        """
        try:
            # Build query from filters with organization scope
            query = {} if not organization_id else {"organization_id": organization_id}

            if filters.assistant_id:
                query["assistant_id"] = filters.assistant_id
            if filters.automation_id:
                query["automation_id"] = filters.automation_id
            if filters.status:
                query["status"] = filters.status
            if filters.direction:
                query["direction"] = filters.direction
            if filters.from_phone:
                query["from_phone"] = filters.from_phone
            if filters.to_phone:
                query["to_phone"] = filters.to_phone
            if filters.customer_id:
                query["customer_id"] = filters.customer_id

            # Date range filter
            if filters.start_date or filters.end_date:
                date_filter = {}
                if filters.start_date:
                    date_filter["$gte"] = filters.start_date
                if filters.end_date:
                    date_filter["$lte"] = filters.end_date
                query["start_time"] = date_filter

            # Duration filters
            if filters.min_duration is not None or filters.max_duration is not None:
                duration_filter = {}
                if filters.min_duration is not None:
                    duration_filter["$gte"] = filters.min_duration
                if filters.max_duration is not None:
                    duration_filter["$lte"] = filters.max_duration
                query["duration"] = duration_filter

            # Cost filters
            if filters.min_cost is not None or filters.max_cost is not None:
                cost_filter = {}
                if filters.min_cost is not None:
                    cost_filter["$gte"] = filters.min_cost
                if filters.max_cost is not None:
                    cost_filter["$lte"] = filters.max_cost
                query["cost"] = cost_filter

            # Boolean filters
            if filters.has_transcript is not None:
                if filters.has_transcript:
                    query["transcript"] = {"$ne": None, "$ne": ""}
                else:
                    query["$or"] = [{"transcript": None}, {"transcript": ""}]

            # Sentiment filter
            if filters.sentiment:
                query["sentiment"] = filters.sentiment

            # Calculate pagination
            offset = (page - 1) * per_page

            # Get total count
            total_count = await self.call_logs_collection.count_documents(query)

            # Determine sort direction
            sort_direction = -1 if sort_order.lower() == "desc" else 1

            # Get logs
            cursor = self.call_logs_collection.find(query).sort(sort_by, sort_direction).skip(offset).limit(per_page)
            logs = []

            async for doc in cursor:
                # Convert MongoDB document to CallLogEntry with proper field mapping
                try:
                    # Ensure required fields have defaults
                    # Handle both vapi_calls and call_logs schema
                    call_log_data = {
                        "id": str(doc["_id"]),
                        "call_id": doc.get("call_id", doc.get("id", str(doc["_id"]))),
                        "assistant_id": doc.get("assistant_id"),
                        "assistant_name": doc.get("assistant_name"),
                        "status": doc.get("status", doc.get("call_status", "unknown")),
                        "direction": doc.get("direction", "outbound"),  # vapi_calls are mostly outbound
                        "from_phone": doc.get("from_phone", doc.get("customer_phone", doc.get("phone_number"))),
                        "to_phone": doc.get("to_phone", doc.get("customer_phone")),
                        "start_time": doc.get("start_time", doc.get("created_at")),
                        "end_time": doc.get("end_time"),
                        "duration": int(doc["duration"]) if doc.get("duration") is not None else (
                            int(doc["call_duration"]) if doc.get("call_duration") is not None else None
                        ),
                        "ended_reason": doc.get("ended_reason"),
                        "transcript": doc.get("transcript"),
                        "summary": doc.get("summary"),
                        "sentiment": doc.get("sentiment"),
                        "confidence_score": doc.get("confidence_score", doc.get("sentiment_score")),
                        "keywords": doc.get("keywords", []),
                        "cost": doc.get("cost", doc.get("vapi_cost", doc.get("vonage_cost"))),  # Support multiple cost field names
                        "tokens_used": doc.get("tokens_used"),
                        "customer_id": doc.get("customer_id"),
                        "organization_id": doc.get("organization_id"),
                        "user_id": doc.get("user_id"),
                        "vapi_data": doc.get("vapi_data", doc.get("metadata", {}).get("vapi_call_data", {})),
                        "audio_quality": doc.get("audio_quality"),
                        "connection_quality": doc.get("connection_quality"),
                        "metadata": doc.get("metadata", {}),
                        "tags": doc.get("tags", []),
                        "created_at": doc.get("created_at", doc.get("start_time", datetime.now(timezone.utc))),
                        "updated_at": doc.get("updated_at", doc.get("processed_at")),
                        "synced_to_supabase": doc.get("synced_to_supabase"),
                        "supabase_id": doc.get("supabase_id"),
                        "sync_error": doc.get("sync_error")
                    }

                    logs.append(CallLogEntry(**call_log_data))
                except Exception as e:
                    logger.warning(f"Failed to convert document {doc.get('_id')} to CallLogEntry: {e}")
                    # Skip this document and continue with others
                    continue

            # Fetch assistant names for all logs
            unique_assistant_ids = list(set(
                log.assistant_id for log in logs if log.assistant_id
            ))

            assistant_names = {}
            if unique_assistant_ids:
                # Fetch assistants in one query
                assistants_cursor = self.assistants_collection.find(
                    {"id": {"$in": unique_assistant_ids}},
                    {"id": 1, "name": 1}
                )
                async for assistant in assistants_cursor:
                    assistant_names[assistant["id"]] = assistant.get("name", "Unknown")

            # Update logs with assistant names
            for log in logs:
                if log.assistant_id and log.assistant_id in assistant_names:
                    log.assistant_name = assistant_names[log.assistant_id]

            return {
                "logs": logs,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total_count,
                    "pages": (total_count + per_page - 1) // per_page
                }
            }

        except Exception as e:
            logger.error(f"Failed to get call logs: {e}")
            raise

    async def get_call_log_stats(self, filters: CallLogFilters, organization_id: Optional[str] = None) -> CallLogStats:
        """
        Get aggregated statistics for call logs.

        Args:
            filters: Call log filters
            organization_id: Organization ID for filtering

        Returns:
            CallLogStats with aggregated statistics
        """
        try:
            # Build query from filters (reuse logic from get_call_logs)
            query = self._build_query_from_filters(filters, organization_id)

            # Aggregation pipeline for statistics
            pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": None,
                        "total_calls": {"$sum": 1},
                        "successful_calls": {
                            "$sum": {"$cond": [{"$in": ["$status", ["completed", "success"]]}, 1, 0]}
                        },
                        "failed_calls": {
                            "$sum": {"$cond": [{"$in": ["$status", ["failed", "error"]]}, 1, 0]}
                        },
                        "total_duration": {"$sum": {"$ifNull": ["$duration", 0]}},
                        "total_cost": {"$sum": {"$ifNull": ["$cost", 0]}},
                        "avg_sentiment": {"$avg": "$sentiment_score"},
                        "total_tool_calls": {"$sum": {"$size": {"$ifNull": ["$tool_calls", []]}}},
                        "unique_assistants": {"$addToSet": "$assistant_id"},
                        "unique_phone_numbers": {"$addToSet": "$from_phone"},
                        "min_date": {"$min": "$start_time"},
                        "max_date": {"$max": "$start_time"}
                    }
                }
            ]

            result = await self.call_logs_collection.aggregate(pipeline).to_list(1)

            if not result:
                # Return empty stats if no data
                return CallLogStats(
                    total_calls=0,
                    successful_calls=0,
                    failed_calls=0,
                    total_duration=0.0,
                    total_cost=0.0,
                    avg_duration=0.0,
                    avg_cost=0.0,
                    success_rate=0.0,
                    total_tool_calls=0,
                    unique_assistants=0,
                    unique_phone_numbers=0,
                    date_range={"start": datetime.now(timezone.utc), "end": datetime.now(timezone.utc)}
                )

            stats_data = result[0]

            # Calculate derived metrics
            total_calls = stats_data["total_calls"]
            successful_calls = stats_data["successful_calls"]
            total_duration = stats_data["total_duration"]
            total_cost = stats_data["total_cost"]

            avg_duration = total_duration / total_calls if total_calls > 0 else 0.0
            avg_cost = total_cost / total_calls if total_calls > 0 else 0.0
            success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0.0

            return CallLogStats(
                total_calls=total_calls,
                successful_calls=successful_calls,
                failed_calls=stats_data["failed_calls"],
                total_duration=total_duration,
                total_cost=total_cost,
                avg_duration=avg_duration,
                avg_cost=avg_cost,
                avg_sentiment=stats_data.get("avg_sentiment"),
                success_rate=success_rate,
                total_tool_calls=stats_data["total_tool_calls"],
                unique_assistants=len(stats_data["unique_assistants"]),
                unique_phone_numbers=len(stats_data["unique_phone_numbers"]),
                date_range={
                    "start": stats_data.get("min_date", datetime.now(timezone.utc)),
                    "end": stats_data.get("max_date", datetime.now(timezone.utc))
                }
            )

        except Exception as e:
            logger.error(f"Failed to get call log stats: {e}")
            raise

    async def get_tool_call_analysis(self, filters: CallLogFilters, organization_id: Optional[str] = None) -> List[ToolCallAnalysis]:
        """
        Get analysis of tool call performance.

        Args:
            filters: Call log filters
            organization_id: Organization ID for filtering

        Returns:
            List of ToolCallAnalysis objects
        """
        try:
            query = self._build_query_from_filters(filters, organization_id)

            # Aggregation pipeline for tool call analysis
            pipeline = [
                {"$match": query},
                {"$unwind": {"path": "$tool_calls", "preserveNullAndEmptyArrays": False}},
                {
                    "$group": {
                        "_id": "$tool_calls.tool_name",
                        "total_calls": {"$sum": 1},
                        "successful_calls": {
                            "$sum": {"$cond": [{"$eq": ["$tool_calls.success", True]}, 1, 0]}
                        },
                        "avg_execution_time": {"$avg": "$tool_calls.execution_time"},
                        "errors": {"$push": {"$cond": [{"$eq": ["$tool_calls.success", False]}, "$tool_calls.error", None]}}
                    }
                },
                {
                    "$project": {
                        "tool_name": "$_id",
                        "total_calls": 1,
                        "success_rate": {
                            "$multiply": [{"$divide": ["$successful_calls", "$total_calls"]}, 100]
                        },
                        "avg_execution_time": 1,
                        "error_rate": {
                            "$multiply": [{"$divide": [{"$subtract": ["$total_calls", "$successful_calls"]}, "$total_calls"]}, 100]
                        },
                        "common_errors": {
                            "$slice": [
                                {"$setIntersection": ["$errors", "$errors"]},
                                5
                            ]
                        }
                    }
                },
                {"$sort": {"total_calls": -1}}
            ]

            results = await self.call_logs_collection.aggregate(pipeline).to_list(None)

            analysis = []
            for result in results:
                analysis.append(ToolCallAnalysis(
                    tool_name=result["tool_name"],
                    total_calls=result["total_calls"],
                    success_rate=result["success_rate"],
                    avg_execution_time=result.get("avg_execution_time"),
                    error_rate=result["error_rate"],
                    common_errors=[error for error in result["common_errors"] if error is not None]
                ))

            return analysis

        except Exception as e:
            logger.error(f"Failed to get tool call analysis: {e}")
            raise

    def _build_query_from_filters(self, filters: CallLogFilters, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Build MongoDB query from filters.

        Args:
            filters: Call log filters
            organization_id: Organization ID for scoping queries

        Returns:
            MongoDB query dictionary
        """
        query = {}

        # Organization filter - CRITICAL for multi-tenant isolation
        if organization_id:
            query["organization_id"] = organization_id

        if filters.assistant_id:
            query["assistant_id"] = filters.assistant_id
        if filters.automation_id:
            query["automation_id"] = filters.automation_id
        if filters.status:
            query["status"] = filters.status
        if filters.direction:
            query["direction"] = filters.direction
        if filters.from_phone:
            query["from_phone"] = filters.from_phone
        if filters.to_phone:
            query["to_phone"] = filters.to_phone
        if filters.customer_id:
            query["customer_id"] = filters.customer_id

        # Date range filter
        if filters.start_date or filters.end_date:
            date_filter = {}
            if filters.start_date:
                date_filter["$gte"] = filters.start_date
            if filters.end_date:
                date_filter["$lte"] = filters.end_date
            query["start_time"] = date_filter

        return query

    async def update_call_log(self, log_id: str, update_data: Dict[str, Any], organization_id: Optional[str] = None) -> bool:
        """
        Update an existing call log.

        Args:
            log_id: Call log ID
            update_data: Update data dictionary
            organization_id: Organization ID for ownership verification

        Returns:
            True if updated successfully
        """
        try:
            update_data["updated_at"] = datetime.now(timezone.utc)

            # Build query with organization filter for ownership verification
            query = {"_id": ObjectId(log_id)}
            if organization_id:
                query["organization_id"] = organization_id

            result = await self.call_logs_collection.update_one(
                query,
                {"$set": update_data}
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Failed to update call log: {e}")
            raise

    async def delete_call_log(self, log_id: str, organization_id: Optional[str] = None) -> bool:
        """
        Delete a call log.

        Args:
            log_id: Call log ID
            organization_id: Organization ID for ownership verification

        Returns:
            True if deleted successfully
        """
        try:
            # Build query with organization filter for ownership verification
            query = {"_id": ObjectId(log_id)}
            if organization_id:
                query["organization_id"] = organization_id

            result = await self.call_logs_collection.delete_one(query)
            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"Failed to delete call log: {e}")
            raise

# Routes
@router.post("/", response_model=StandardResponse[str])
async def create_call_log(
    request: Request,
    call_data: Dict[str, Any],
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Create a new call log entry.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Use organization_id from context with fallback
        organization_id = org_id or current_user.get("organization_id")

        # Ensure call_data includes organization_id
        if organization_id and "organization_id" not in call_data:
            call_data["organization_id"] = organization_id

        logger.info(f"Creating call log for organization: {organization_id}")

        service = CallLogService(db)
        log_id = await service.create_call_log(call_data)

        return StandardResponse(
            success=True,
            data=log_id,
            message="Call log created successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create call log: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
async def get_call_logs(
    request: Request,
    assistant_id: Optional[str] = Query(None),
    automation_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    direction: Optional[str] = Query(None),
    from_phone: Optional[str] = Query(None),
    to_phone: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    has_transcript: Optional[bool] = Query(None),
    sentiment: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    sort_by: str = Query("created_at"),  # vapi_calls uses created_at, not start_time
    sort_order: str = Query("desc"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get call logs with filtering and pagination.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Use organization_id from context with fallback
        organization_id = org_id or current_user.get("organization_id")

        logger.info(f"Listing call logs for organization: {organization_id}")

        service = CallLogService(db)

        filters = CallLogFilters(
            assistant_id=assistant_id,
            automation_id=automation_id,  # Handle automation_id as separate filter
            status=status,
            direction=direction,
            from_phone=from_phone,
            to_phone=to_phone,
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date,
            has_transcript=has_transcript,
            sentiment=sentiment
        )

        result = await service.get_call_logs(filters, page, per_page, sort_by, sort_order, organization_id)

        return {
            "logs": result["logs"],
            "pagination": result["pagination"],
            "message": f"Retrieved {len(result['logs'])} call logs"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get call logs: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stats", response_model=StandardResponse[CallLogStats])
async def get_call_log_stats(
    request: Request,
    assistant_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    direction: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get aggregated statistics for call logs.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Use organization_id from context with fallback
        organization_id = org_id or current_user.get("organization_id")

        logger.info(f"Getting call log stats for organization: {organization_id}")

        service = CallLogService(db)

        filters = CallLogFilters(
            assistant_id=assistant_id,
            status=status,
            direction=direction,
            start_date=start_date,
            end_date=end_date
        )

        stats = await service.get_call_log_stats(filters, organization_id)

        return StandardResponse(
            success=True,
            data=stats,
            message="Call log statistics retrieved"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get call log stats: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tool-analysis", response_model=StandardResponse[List[ToolCallAnalysis]])
async def get_tool_call_analysis(
    request: Request,
    assistant_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get analysis of tool call performance.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Use organization_id from context with fallback
        organization_id = org_id or current_user.get("organization_id")

        logger.info(f"Getting tool call analysis for organization: {organization_id}")

        service = CallLogService(db)

        filters = CallLogFilters(
            assistant_id=assistant_id,
            status=status,
            start_date=start_date,
            end_date=end_date
        )

        analysis = await service.get_tool_call_analysis(filters, organization_id)

        return StandardResponse(
            success=True,
            data=analysis,
            message=f"Tool call analysis for {len(analysis)} tools"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool call analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{log_id}", response_model=StandardResponse[bool])
async def update_call_log(
    request: Request,
    log_id: str,
    update_data: Dict[str, Any],
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Update an existing call log.

    Now properly scoped to organization. Requires authentication and ownership.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Use organization_id from context with fallback
        organization_id = org_id or current_user.get("organization_id")

        logger.info(f"Updating call log {log_id} for organization: {organization_id}")

        service = CallLogService(db)
        success = await service.update_call_log(log_id, update_data, organization_id)

        if not success:
            raise HTTPException(status_code=404, detail="Call log not found or access denied")

        return StandardResponse(
            success=True,
            data=True,
            message="Call log updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update call log: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{log_id}", response_model=StandardResponse[bool])
async def delete_call_log(
    request: Request,
    log_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Delete a call log.

    Now properly scoped to organization. Requires authentication and ownership.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Use organization_id from context with fallback
        organization_id = org_id or current_user.get("organization_id")

        logger.info(f"Deleting call log {log_id} for organization: {organization_id}")

        service = CallLogService(db)
        success = await service.delete_call_log(log_id, organization_id)

        if not success:
            raise HTTPException(status_code=404, detail="Call log not found or access denied")

        return StandardResponse(
            success=True,
            data=True,
            message="Call log deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete call log: {e}")
        raise HTTPException(status_code=400, detail=str(e))