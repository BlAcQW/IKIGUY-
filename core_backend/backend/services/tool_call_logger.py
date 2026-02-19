"""
Tool Call Logger Service.
Logs all RAG knowledge base queries to MongoDB for analytics and monitoring.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError

from backend.models.tool_call_log import (
    ToolCallLog,
    ToolCallStatus,
    CityNormalization,
    PreComputedQuery,
    MonitoringMetrics,
    QueryAnalytics
)

logger = logging.getLogger(__name__)


class ToolCallLoggerService:
    """
    Service for logging and analyzing tool calls.

    Features:
    - Automatic logging of all RAG queries
    - 7-day data retention (TTL index)
    - Real-time analytics
    - Pre-computed query management
    """

    def __init__(self):
        """Initialize MongoDB connection."""
        mongodb_url = os.getenv("MONGODB_URL")
        if not mongodb_url:
            raise ValueError("MONGODB_URL environment variable is required")

        self.client: AsyncIOMotorClient = AsyncIOMotorClient(mongodb_url)
        self.db: AsyncIOMotorDatabase = self.client.kasaai_core
        self.tool_calls_collection = self.db.tool_call_logs
        self.precomputed_collection = self.db.precomputed_queries

        logger.info("✅ ToolCallLoggerService initialized")

    async def ensure_indexes(self):
        """
        Create indexes for optimal query performance and automatic cleanup.

        Indexes:
        - TTL index on created_at (7 days retention)
        - Index on company_name + created_at (for analytics)
        - Index on query patterns (for pre-compute)
        - Index on tool_call_id (for lookups)
        """
        try:
            # TTL index - auto-delete after 7 days
            await self.tool_calls_collection.create_index(
                "created_at",
                expireAfterSeconds=7 * 24 * 60 * 60,  # 7 days
                name="ttl_created_at"
            )

            # Analytics indexes
            await self.tool_calls_collection.create_index(
                [("company_name", ASCENDING), ("created_at", DESCENDING)],
                name="company_created"
            )

            await self.tool_calls_collection.create_index(
                [("tool_call_id", ASCENDING)],
                unique=True,
                name="tool_call_id_unique"
            )

            await self.tool_calls_collection.create_index(
                [("query_normalized", ASCENDING)],
                name="query_normalized"
            )

            # Pre-computed queries indexes
            await self.precomputed_collection.create_index(
                [("company_name", ASCENDING), ("query_pattern", ASCENDING)],
                unique=True,
                name="company_query_unique"
            )

            await self.precomputed_collection.create_index(
                "expires_at",
                expireAfterSeconds=0,  # Delete when expires_at is reached
                name="ttl_expires_at"
            )

            logger.info("✅ Tool call logger indexes created")

        except Exception as e:
            logger.error(f"❌ Error creating indexes: {e}")

    async def log_tool_call(
        self,
        tool_call_id: str,
        company_name: str,
        query_original: str,
        response: str,
        processing_time: float,
        confidence_score: float,
        documents_retrieved: int,
        documents_sent_to_llm: int,
        sources_used: List[str],
        requires_escalation: bool = False,
        escalation_reason: Optional[str] = None,
        query_normalized: Optional[str] = None,
        city_normalization: Optional[Dict[str, Any]] = None,
        status: ToolCallStatus = ToolCallStatus.SUCCESS,
        error_message: Optional[str] = None,
        is_cached: bool = False,
        cache_key: Optional[str] = None,
        retrieval_time: Optional[float] = None,
        llm_time: Optional[float] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        vapi_call_id: Optional[str] = None
    ) -> bool:
        """
        Log a tool call to MongoDB.

        Args:
            tool_call_id: VAPI tool call ID
            company_name: Company/knowledge base name
            query_original: Original user query
            response: Generated response
            processing_time: Total processing time in seconds
            confidence_score: RAG confidence score
            documents_retrieved: Number of docs retrieved from vector store
            documents_sent_to_llm: Number of docs actually sent to LLM
            sources_used: List of source document titles
            requires_escalation: Whether query requires human escalation
            escalation_reason: Reason for escalation
            query_normalized: Query after city normalization
            city_normalization: City normalization details
            status: Query status
            error_message: Error message if failed
            is_cached: Was response from cache?
            cache_key: Cache key if applicable
            retrieval_time: Vector retrieval time
            llm_time: LLM generation time
            ip_address: Client IP
            user_agent: Client user agent
            vapi_call_id: VAPI call ID

        Returns:
            bool: True if logged successfully
        """
        try:
            # Parse city normalization
            city_norm_obj = None
            if city_normalization:
                city_norm_obj = CityNormalization(**city_normalization)

            # Create log entry
            log_entry = ToolCallLog(
                tool_call_id=tool_call_id,
                company_name=company_name,
                query_original=query_original,
                query_normalized=query_normalized or query_original,
                city_normalization=city_norm_obj,
                response=response,
                response_length=len(response),
                status=status,
                error_message=error_message,
                processing_time=processing_time,
                retrieval_time=retrieval_time,
                llm_time=llm_time,
                documents_retrieved=documents_retrieved,
                documents_sent_to_llm=documents_sent_to_llm,
                confidence_score=confidence_score,
                requires_escalation=requires_escalation,
                escalation_reason=escalation_reason,
                sources_used=sources_used,
                ip_address=ip_address,
                user_agent=user_agent,
                vapi_call_id=vapi_call_id,
                is_cached=is_cached,
                cache_key=cache_key,
                created_at=datetime.utcnow()
            )

            # Insert to MongoDB
            await self.tool_calls_collection.insert_one(
                log_entry.dict(by_alias=True, exclude={"id"})
            )

            logger.debug(f"✅ Logged tool call: {tool_call_id}")
            return True

        except DuplicateKeyError:
            logger.warning(f"⚠️  Duplicate tool_call_id: {tool_call_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Error logging tool call: {e}")
            return False

    async def get_pre_computed_response(
        self,
        company_name: str,
        query_pattern: str
    ) -> Optional[PreComputedQuery]:
        """
        Get pre-computed response for a query pattern.

        Args:
            company_name: Company name
            query_pattern: Normalized query pattern

        Returns:
            PreComputedQuery if found and not expired, None otherwise
        """
        try:
            result = await self.precomputed_collection.find_one({
                "company_name": company_name,
                "query_pattern": query_pattern,
                "expires_at": {"$gt": datetime.utcnow()}
            })

            if result:
                # Update last_requested timestamp
                await self.precomputed_collection.update_one(
                    {"_id": result["_id"]},
                    {
                        "$set": {"last_requested": datetime.utcnow()},
                        "$inc": {"query_count": 1}
                    }
                )

                return PreComputedQuery(**result)

            return None

        except Exception as e:
            logger.error(f"❌ Error getting pre-computed response: {e}")
            return None

    async def save_pre_computed_response(
        self,
        company_name: str,
        query_pattern: str,
        response: str,
        confidence_score: float,
        sources_used: List[str],
        avg_processing_time: float = 0.0,
        ttl_hours: int = 24
    ) -> bool:
        """
        Save a pre-computed response.

        Args:
            company_name: Company name
            query_pattern: Query pattern
            response: Pre-computed response
            confidence_score: Confidence score
            sources_used: Source documents
            avg_processing_time: Average processing time before pre-compute
            ttl_hours: Time to live in hours

        Returns:
            bool: True if saved successfully
        """
        try:
            precomputed = PreComputedQuery(
                company_name=company_name,
                query_pattern=query_pattern,
                response=response,
                confidence_score=confidence_score,
                sources_used=sources_used,
                avg_processing_time=avg_processing_time,
                computed_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=ttl_hours)
            )

            # Upsert (insert or update)
            await self.precomputed_collection.update_one(
                {
                    "company_name": company_name,
                    "query_pattern": query_pattern
                },
                {"$set": precomputed.dict(by_alias=True, exclude={"id"})},
                upsert=True
            )

            logger.info(f"✅ Saved pre-computed response for: {query_pattern}")
            return True

        except Exception as e:
            logger.error(f"❌ Error saving pre-computed response: {e}")
            return False

    async def get_top_queries(
        self,
        company_name: str,
        limit: int = 50,
        days: int = 7
    ) -> List[QueryAnalytics]:
        """
        Get top query patterns for pre-computation.

        Args:
            company_name: Company name
            limit: Number of top queries to return
            days: Number of days to analyze

        Returns:
            List of query analytics
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            pipeline = [
                {
                    "$match": {
                        "company_name": company_name,
                        "created_at": {"$gte": since_date},
                        "status": ToolCallStatus.SUCCESS
                    }
                },
                {
                    "$group": {
                        "_id": "$query_normalized",
                        "count": {"$sum": 1},
                        "avg_confidence": {"$avg": "$confidence_score"},
                        "avg_processing_time": {"$avg": "$processing_time"},
                        "success_count": {
                            "$sum": {
                                "$cond": [{"$eq": ["$status", "success"]}, 1, 0]
                            }
                        },
                        "last_queried": {"$max": "$created_at"}
                    }
                },
                {
                    "$project": {
                        "query_pattern": "$_id",
                        "total_count": "$count",
                        "avg_confidence": "$avg_confidence",
                        "avg_processing_time": "$avg_processing_time",
                        "success_rate": {
                            "$divide": ["$success_count", "$count"]
                        },
                        "last_queried": "$last_queried"
                    }
                },
                {"$sort": {"total_count": -1}},
                {"$limit": limit}
            ]

            results = []
            async for doc in self.tool_calls_collection.aggregate(pipeline):
                # Check if already pre-computed
                is_precomputed = await self.precomputed_collection.count_documents({
                    "company_name": company_name,
                    "query_pattern": doc["query_pattern"],
                    "expires_at": {"$gt": datetime.utcnow()}
                }) > 0

                results.append(QueryAnalytics(
                    query_pattern=doc["query_pattern"],
                    total_count=doc["total_count"],
                    avg_confidence=doc["avg_confidence"],
                    avg_processing_time=doc["avg_processing_time"],
                    success_rate=doc["success_rate"],
                    last_queried=doc["last_queried"],
                    is_pre_computed=is_precomputed
                ))

            return results

        except Exception as e:
            logger.error(f"❌ Error getting top queries: {e}")
            return []

    async def get_monitoring_metrics(
        self,
        company_name: str,
        hours: int = 24
    ) -> MonitoringMetrics:
        """
        Get real-time monitoring metrics.

        Args:
            company_name: Company name
            hours: Time period in hours

        Returns:
            MonitoringMetrics
        """
        try:
            period_start = datetime.utcnow() - timedelta(hours=hours)
            period_end = datetime.utcnow()

            # Query volume
            total_queries = await self.tool_calls_collection.count_documents({
                "company_name": company_name,
                "created_at": {"$gte": period_start}
            })

            successful_queries = await self.tool_calls_collection.count_documents({
                "company_name": company_name,
                "created_at": {"$gte": period_start},
                "status": ToolCallStatus.SUCCESS
            })

            failed_queries = total_queries - successful_queries

            cached_responses = await self.tool_calls_collection.count_documents({
                "company_name": company_name,
                "created_at": {"$gte": period_start},
                "is_cached": True
            })

            # Performance metrics
            perf_pipeline = [
                {
                    "$match": {
                        "company_name": company_name,
                        "created_at": {"$gte": period_start},
                        "status": ToolCallStatus.SUCCESS
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "avg_time": {"$avg": "$processing_time"},
                        "min_time": {"$min": "$processing_time"},
                        "max_time": {"$max": "$processing_time"},
                        "times": {"$push": "$processing_time"},
                        "avg_confidence": {"$avg": "$confidence_score"},
                        "escalations": {
                            "$sum": {
                                "$cond": ["$requires_escalation", 1, 0]
                            }
                        }
                    }
                }
            ]

            perf_result = await self.tool_calls_collection.aggregate(perf_pipeline).to_list(1)

            if perf_result:
                perf = perf_result[0]
                times = sorted(perf.get("times", []))
                p50_idx = int(len(times) * 0.50)
                p95_idx = int(len(times) * 0.95)
                p99_idx = int(len(times) * 0.99)

                avg_response_time = perf.get("avg_time", 0.0)
                min_response_time = perf.get("min_time", 0.0)
                max_response_time = perf.get("max_time", 0.0)
                p50_response_time = times[p50_idx] if times else 0.0
                p95_response_time = times[p95_idx] if times else 0.0
                p99_response_time = times[p99_idx] if times else 0.0
                avg_confidence = perf.get("avg_confidence", 0.0)
                escalation_count = perf.get("escalations", 0)
                escalation_rate = escalation_count / total_queries if total_queries > 0 else 0.0
            else:
                avg_response_time = min_response_time = max_response_time = 0.0
                p50_response_time = p95_response_time = p99_response_time = 0.0
                avg_confidence = escalation_rate = 0.0

            # Top queries
            top_queries_result = await self.get_top_queries(company_name, limit=10, days=hours//24 or 1)
            top_queries = [
                {
                    "query": q.query_pattern,
                    "count": q.total_count,
                    "avg_time": q.avg_processing_time
                }
                for q in top_queries_result
            ]

            return MonitoringMetrics(
                period_start=period_start,
                period_end=period_end,
                total_queries=total_queries,
                successful_queries=successful_queries,
                failed_queries=failed_queries,
                cached_responses=cached_responses,
                avg_response_time=avg_response_time,
                min_response_time=min_response_time,
                max_response_time=max_response_time,
                p50_response_time=p50_response_time,
                p95_response_time=p95_response_time,
                p99_response_time=p99_response_time,
                avg_confidence=avg_confidence,
                escalation_rate=escalation_rate,
                top_queries=top_queries,
                top_cities=[],  # Can implement later
                top_specialties=[],  # Can implement later
                error_count=failed_queries,
                common_errors=[]  # Can implement later
            )

        except Exception as e:
            logger.error(f"❌ Error getting monitoring metrics: {e}")
            return MonitoringMetrics(
                period_start=period_start,
                period_end=period_end
            )


# Global instance
tool_call_logger = ToolCallLoggerService()
