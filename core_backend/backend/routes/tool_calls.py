"""
Tool Call Logs API Routes.
Provides endpoints for viewing and analyzing tool call logs from MongoDB.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel, Field

from backend.services.tool_call_logger import tool_call_logger
from backend.models.tool_call_log import ToolCallLog, ToolCallStatus

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tool-calls",
    tags=["tool-calls"],
    responses={404: {"description": "Not found"}}
)


class ToolCallLogResponse(BaseModel):
    """Response model for tool call log."""
    id: str
    tool_call_id: str
    company_name: str
    query_original: str
    query_normalized: Optional[str] = None
    response: str
    response_length: int
    status: str
    error_message: Optional[str] = None
    processing_time: float
    retrieval_time: Optional[float] = None
    llm_time: Optional[float] = None
    documents_retrieved: int
    documents_sent_to_llm: int
    confidence_score: float
    requires_escalation: bool
    escalation_reason: Optional[str] = None
    sources_used: List[str]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    vapi_call_id: Optional[str] = None
    created_at: datetime
    is_cached: bool
    cache_key: Optional[str] = None
    city_normalization: Optional[dict] = None


class ToolCallLogsListResponse(BaseModel):
    """Response model for paginated tool call logs list."""
    success: bool = True
    logs: List[ToolCallLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ToolStatsResponse(BaseModel):
    """Response model for tool statistics."""
    success: bool = True
    tool_name: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    success_rate: float
    avg_processing_time: float
    avg_confidence_score: float
    total_escalations: int
    escalation_rate: float
    avg_cached_response_time: float
    cache_hit_rate: float
    most_recent_call: Optional[datetime] = None
    oldest_call: Optional[datetime] = None


@router.get("/logs", response_model=ToolCallLogsListResponse)
async def get_tool_call_logs(
    company_name: Optional[str] = Query(None, description="Filter by company name"),
    automation_id: Optional[str] = Query(None, description="Filter by automation ID (via VAPI call ID)"),
    status: Optional[ToolCallStatus] = Query(None, description="Filter by status"),
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in query text")
):
    """
    Get paginated list of tool call logs with optional filters.

    Args:
        company_name: Filter by company/knowledge base name
        automation_id: Filter by automation (matches vapi_call_id)
        status: Filter by call status
        days: Number of days to look back (default 7, max 30)
        page: Page number (1-indexed)
        page_size: Items per page (max 100)
        search: Search term for query text

    Returns:
        Paginated list of tool call logs
    """
    try:
        since_date = datetime.utcnow() - timedelta(days=days)

        # Build query filter
        query_filter = {"created_at": {"$gte": since_date}}

        if company_name:
            query_filter["company_name"] = company_name

        if automation_id:
            query_filter["vapi_call_id"] = automation_id

        if status:
            query_filter["status"] = status.value

        if search:
            query_filter["$or"] = [
                {"query_original": {"$regex": search, "$options": "i"}},
                {"query_normalized": {"$regex": search, "$options": "i"}},
                {"response": {"$regex": search, "$options": "i"}}
            ]

        # Get total count
        total = await tool_call_logger.tool_calls_collection.count_documents(query_filter)

        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size

        # Fetch logs
        cursor = tool_call_logger.tool_calls_collection.find(query_filter).sort("created_at", -1).skip(skip).limit(page_size)

        logs = []
        async for doc in cursor:
            logs.append(ToolCallLogResponse(
                id=str(doc.get("_id", "")),
                tool_call_id=doc.get("tool_call_id", ""),
                company_name=doc.get("company_name", ""),
                query_original=doc.get("query_original", ""),
                query_normalized=doc.get("query_normalized"),
                response=doc.get("response", ""),
                response_length=doc.get("response_length", 0),
                status=doc.get("status", ""),
                error_message=doc.get("error_message"),
                processing_time=doc.get("processing_time", 0.0),
                retrieval_time=doc.get("retrieval_time"),
                llm_time=doc.get("llm_time"),
                documents_retrieved=doc.get("documents_retrieved", 0),
                documents_sent_to_llm=doc.get("documents_sent_to_llm", 0),
                confidence_score=doc.get("confidence_score", 0.0),
                requires_escalation=doc.get("requires_escalation", False),
                escalation_reason=doc.get("escalation_reason"),
                sources_used=doc.get("sources_used", []),
                ip_address=doc.get("ip_address"),
                user_agent=doc.get("user_agent"),
                vapi_call_id=doc.get("vapi_call_id"),
                created_at=doc.get("created_at", datetime.utcnow()),
                is_cached=doc.get("is_cached", False),
                cache_key=doc.get("cache_key"),
                city_normalization=doc.get("city_normalization")
            ))

        return ToolCallLogsListResponse(
            logs=logs,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except Exception as e:
        logger.error(f"❌ Error fetching tool call logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/{log_id}", response_model=ToolCallLogResponse)
async def get_tool_call_log_detail(log_id: str):
    """
    Get detailed information about a specific tool call log.

    Args:
        log_id: Tool call log ID (MongoDB _id)

    Returns:
        Detailed tool call log
    """
    try:
        from bson import ObjectId

        doc = await tool_call_logger.tool_calls_collection.find_one({"_id": ObjectId(log_id)})

        if not doc:
            raise HTTPException(status_code=404, detail=f"Tool call log {log_id} not found")

        return ToolCallLogResponse(
            id=str(doc.get("_id", "")),
            tool_call_id=doc.get("tool_call_id", ""),
            company_name=doc.get("company_name", ""),
            query_original=doc.get("query_original", ""),
            query_normalized=doc.get("query_normalized"),
            response=doc.get("response", ""),
            response_length=doc.get("response_length", 0),
            status=doc.get("status", ""),
            error_message=doc.get("error_message"),
            processing_time=doc.get("processing_time", 0.0),
            retrieval_time=doc.get("retrieval_time"),
            llm_time=doc.get("llm_time"),
            documents_retrieved=doc.get("documents_retrieved", 0),
            documents_sent_to_llm=doc.get("documents_sent_to_llm", 0),
            confidence_score=doc.get("confidence_score", 0.0),
            requires_escalation=doc.get("requires_escalation", False),
            escalation_reason=doc.get("escalation_reason"),
            sources_used=doc.get("sources_used", []),
            ip_address=doc.get("ip_address"),
            user_agent=doc.get("user_agent"),
            vapi_call_id=doc.get("vapi_call_id"),
            created_at=doc.get("created_at", datetime.utcnow()),
            is_cached=doc.get("is_cached", False),
            cache_key=doc.get("cache_key"),
            city_normalization=doc.get("city_normalization")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching tool call log detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{company_name}", response_model=ToolStatsResponse)
async def get_tool_stats(
    company_name: str,
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze")
):
    """
    Get statistics for a specific tool/company.

    Args:
        company_name: Company/knowledge base name (e.g., "premier_health_production")
        days: Number of days to analyze (default 30, max 90)

    Returns:
        Tool statistics including call counts, success rates, performance metrics
    """
    try:
        since_date = datetime.utcnow() - timedelta(days=days)

        # Aggregation pipeline for statistics
        pipeline = [
            {
                "$match": {
                    "company_name": company_name,
                    "created_at": {"$gte": since_date}
                }
            },
            {
                "$facet": {
                    # Overall stats
                    "overall": [
                        {
                            "$group": {
                                "_id": None,
                                "total_calls": {"$sum": 1},
                                "successful_calls": {
                                    "$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}
                                },
                                "failed_calls": {
                                    "$sum": {"$cond": [{"$ne": ["$status", "success"]}, 1, 0]}
                                },
                                "avg_processing_time": {"$avg": "$processing_time"},
                                "avg_confidence": {"$avg": "$confidence_score"},
                                "total_escalations": {
                                    "$sum": {"$cond": ["$requires_escalation", 1, 0]}
                                },
                                "cached_calls": {
                                    "$sum": {"$cond": ["$is_cached", 1, 0]}
                                },
                                "avg_cached_time": {
                                    "$avg": {
                                        "$cond": ["$is_cached", "$processing_time", None]
                                    }
                                }
                            }
                        }
                    ],
                    # Date range
                    "date_range": [
                        {
                            "$group": {
                                "_id": None,
                                "oldest": {"$min": "$created_at"},
                                "newest": {"$max": "$created_at"}
                            }
                        }
                    ]
                }
            }
        ]

        results = await tool_call_logger.tool_calls_collection.aggregate(pipeline).to_list(1)

        if not results or not results[0].get("overall"):
            return ToolStatsResponse(
                tool_name=company_name,
                total_calls=0,
                successful_calls=0,
                failed_calls=0,
                success_rate=0.0,
                avg_processing_time=0.0,
                avg_confidence_score=0.0,
                total_escalations=0,
                escalation_rate=0.0,
                avg_cached_response_time=0.0,
                cache_hit_rate=0.0
            )

        stats = results[0]["overall"][0] if results[0]["overall"] else {}
        date_range = results[0]["date_range"][0] if results[0]["date_range"] else {}

        total_calls = stats.get("total_calls", 0)
        successful_calls = stats.get("successful_calls", 0)
        failed_calls = stats.get("failed_calls", 0)
        total_escalations = stats.get("total_escalations", 0)
        cached_calls = stats.get("cached_calls", 0)

        return ToolStatsResponse(
            tool_name=company_name,
            total_calls=total_calls,
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            success_rate=(successful_calls / total_calls * 100) if total_calls > 0 else 0.0,
            avg_processing_time=stats.get("avg_processing_time", 0.0),
            avg_confidence_score=stats.get("avg_confidence", 0.0),
            total_escalations=total_escalations,
            escalation_rate=(total_escalations / total_calls * 100) if total_calls > 0 else 0.0,
            avg_cached_response_time=stats.get("avg_cached_time", 0.0) or 0.0,
            cache_hit_rate=(cached_calls / total_calls * 100) if total_calls > 0 else 0.0,
            most_recent_call=date_range.get("newest"),
            oldest_call=date_range.get("oldest")
        )

    except Exception as e:
        logger.error(f"❌ Error getting tool stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/automation/{automation_id}/logs", response_model=ToolCallLogsListResponse)
async def get_automation_tool_logs(
    automation_id: str,
    days: int = Query(30, ge=1, le=90, description="Number of days to look back"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page")
):
    """
    Get all tool call logs for a specific automation.

    Args:
        automation_id: Automation ID (matches vapi_call_id in logs)
        days: Number of days to look back
        page: Page number
        page_size: Items per page

    Returns:
        Paginated list of tool call logs for the automation
    """
    # Reason: Reuse the main logs endpoint with automation filter
    return await get_tool_call_logs(
        automation_id=automation_id,
        days=days,
        page=page,
        page_size=page_size
    )
