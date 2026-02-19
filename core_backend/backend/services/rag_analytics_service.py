"""
RAG Analytics Service for tracking and analyzing query performance.
Provides insights into knowledge base usage, query effectiveness, and escalation patterns.
"""

import os
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from collections import defaultdict

from backend.models.knowledge_base import QueryMetric

logger = logging.getLogger(__name__)


class RAGAnalyticsService:
    """Service for RAG query analytics and metrics tracking."""

    def __init__(self):
        """Initialize the analytics service."""
        # MongoDB connection
        mongodb_url = os.getenv("MONGODB_URL")
        if not mongodb_url:
            raise ValueError("MONGODB_URL environment variable is required")

        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.mongodb_url = mongodb_url
        self.db_name = os.getenv("MONGODB_DB_NAME", "kasaai_core")

        # Collection name
        self.metrics_collection_name = "rag_query_metrics"

    async def _ensure_connection(self):
        """Ensure MongoDB connection is established."""
        if self.client is None:
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.db = self.client[self.db_name]

            # Create indexes
            await self._create_indexes()
            logger.info("MongoDB connection established for RAG analytics")

    async def _create_indexes(self):
        """Create MongoDB indexes for efficient queries."""
        try:
            metrics_collection = self.db[self.metrics_collection_name]

            # Indexes for metrics collection
            await metrics_collection.create_index([("company_name", ASCENDING)])
            await metrics_collection.create_index([("created_at", DESCENDING)])
            await metrics_collection.create_index([("confidence_score", ASCENDING)])
            await metrics_collection.create_index([("requires_escalation", ASCENDING)])
            await metrics_collection.create_index([("company_name", ASCENDING), ("created_at", DESCENDING)])

            # Text index for query search
            await metrics_collection.create_index([("query", "text")])

            logger.info("RAG analytics indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating analytics indexes: {str(e)}")

    async def track_query(self, metric: QueryMetric) -> bool:
        """
        Track a RAG query for analytics.

        Args:
            metric: Query metric to track

        Returns:
            Success status
        """
        try:
            await self._ensure_connection()
            metrics_collection = self.db[self.metrics_collection_name]

            await metrics_collection.insert_one(metric.model_dump(by_alias=True))

            logger.info(f"Query tracked for analytics: {metric.company_name}")
            return True

        except Exception as e:
            logger.error(f"Error tracking query: {str(e)}")
            return False

    async def get_overview_metrics(
        self,
        company_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get overview metrics for dashboard.

        Args:
            company_name: Company identifier
            days: Number of days to analyze

        Returns:
            Dictionary with overview metrics
        """
        try:
            await self._ensure_connection()
            metrics_collection = self.db[self.metrics_collection_name]

            start_date = datetime.utcnow() - timedelta(days=days)

            # Query for the time period
            query = {
                "company_name": company_name,
                "created_at": {"$gte": start_date}
            }

            # Total queries
            total_queries = await metrics_collection.count_documents(query)

            # Escalated queries
            escalation_query = {**query, "requires_escalation": True}
            escalated_queries = await metrics_collection.count_documents(escalation_query)

            # Average confidence score
            pipeline = [
                {"$match": query},
                {"$group": {
                    "_id": None,
                    "avg_confidence": {"$avg": "$confidence_score"},
                    "avg_processing_time": {"$avg": "$processing_time_ms"},
                    "total_sources": {"$sum": "$num_sources"}
                }}
            ]

            cursor = metrics_collection.aggregate(pipeline)
            stats = await cursor.to_list(length=1)

            avg_confidence = stats[0].get("avg_confidence", 0) if stats else 0
            avg_processing_time = stats[0].get("avg_processing_time", 0) if stats else 0
            avg_sources = stats[0].get("total_sources", 0) / max(total_queries, 1) if stats else 0

            # Calculate rates
            success_rate = (total_queries - escalated_queries) / max(total_queries, 1) if total_queries > 0 else 0
            escalation_rate = escalated_queries / max(total_queries, 1) if total_queries > 0 else 0

            # Queries by day for trend
            daily_pipeline = [
                {"$match": query},
                {"$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id": 1}},
                {"$limit": days}
            ]

            cursor = metrics_collection.aggregate(daily_pipeline)
            daily_queries = await cursor.to_list(length=days)

            return {
                "total_queries": total_queries,
                "total_queries_24h": await self._get_queries_in_period(company_name, hours=24),
                "total_queries_7d": await self._get_queries_in_period(company_name, days=7),
                "escalated_queries": escalated_queries,
                "success_rate": round(success_rate * 100, 2),
                "escalation_rate": round(escalation_rate * 100, 2),
                "avg_confidence_score": round(avg_confidence, 3),
                "avg_processing_time_ms": round(avg_processing_time, 2),
                "avg_sources_per_query": round(avg_sources, 2),
                "daily_query_trend": [
                    {"date": item["_id"], "count": item["count"]}
                    for item in daily_queries
                ],
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting overview metrics: {str(e)}")
            return {}

    async def _get_queries_in_period(
        self,
        company_name: str,
        hours: Optional[int] = None,
        days: Optional[int] = None
    ) -> int:
        """
        Get query count for a specific time period.

        Args:
            company_name: Company identifier
            hours: Hours to look back
            days: Days to look back

        Returns:
            Query count
        """
        try:
            await self._ensure_connection()
            metrics_collection = self.db[self.metrics_collection_name]

            if hours:
                start_date = datetime.utcnow() - timedelta(hours=hours)
            elif days:
                start_date = datetime.utcnow() - timedelta(days=days)
            else:
                return 0

            query = {
                "company_name": company_name,
                "created_at": {"$gte": start_date}
            }

            return await metrics_collection.count_documents(query)

        except Exception as e:
            logger.error(f"Error getting period queries: {str(e)}")
            return 0

    async def get_confidence_distribution(
        self,
        company_name: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get confidence score distribution.

        Args:
            company_name: Company identifier
            days: Number of days to analyze

        Returns:
            List of buckets with counts
        """
        try:
            await self._ensure_connection()
            metrics_collection = self.db[self.metrics_collection_name]

            start_date = datetime.utcnow() - timedelta(days=days)

            # Create buckets: 0-0.5, 0.5-0.7, 0.7-0.85, 0.85-0.95, 0.95-1.0
            pipeline = [
                {"$match": {
                    "company_name": company_name,
                    "created_at": {"$gte": start_date}
                }},
                {"$bucket": {
                    "groupBy": "$confidence_score",
                    "boundaries": [0, 0.5, 0.7, 0.85, 0.95, 1.0],
                    "default": "Other",
                    "output": {
                        "count": {"$sum": 1}
                    }
                }}
            ]

            cursor = metrics_collection.aggregate(pipeline)
            buckets = await cursor.to_list(length=10)

            # Format results
            labels = ["0-50%", "50-70%", "70-85%", "85-95%", "95-100%"]
            result = []

            for i, bucket in enumerate(buckets):
                if i < len(labels):
                    result.append({
                        "range": labels[i],
                        "count": bucket["count"],
                        "min": bucket["_id"],
                        "max": [0.5, 0.7, 0.85, 0.95, 1.0][i]
                    })

            return result

        except Exception as e:
            logger.error(f"Error getting confidence distribution: {str(e)}")
            return []

    async def get_top_queries(
        self,
        company_name: str,
        limit: int = 10,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get most common queries.

        Args:
            company_name: Company identifier
            limit: Number of top queries to return
            days: Number of days to analyze

        Returns:
            List of queries with counts
        """
        try:
            await self._ensure_connection()
            metrics_collection = self.db[self.metrics_collection_name]

            start_date = datetime.utcnow() - timedelta(days=days)

            pipeline = [
                {"$match": {
                    "company_name": company_name,
                    "created_at": {"$gte": start_date}
                }},
                {"$group": {
                    "_id": "$query",
                    "count": {"$sum": 1},
                    "avg_confidence": {"$avg": "$confidence_score"},
                    "escalation_count": {
                        "$sum": {"$cond": ["$requires_escalation", 1, 0]}
                    }
                }},
                {"$sort": {"count": -1}},
                {"$limit": limit}
            ]

            cursor = metrics_collection.aggregate(pipeline)
            queries = await cursor.to_list(length=limit)

            return [
                {
                    "query": item["_id"],
                    "count": item["count"],
                    "avg_confidence": round(item["avg_confidence"], 3),
                    "escalation_count": item["escalation_count"],
                    "escalation_rate": round(item["escalation_count"] / item["count"] * 100, 2)
                }
                for item in queries
            ]

        except Exception as e:
            logger.error(f"Error getting top queries: {str(e)}")
            return []

    async def get_escalation_analysis(
        self,
        company_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze escalation patterns and reasons.

        Args:
            company_name: Company identifier
            days: Number of days to analyze

        Returns:
            Escalation analysis data
        """
        try:
            await self._ensure_connection()
            metrics_collection = self.db[self.metrics_collection_name]

            start_date = datetime.utcnow() - timedelta(days=days)

            query = {
                "company_name": company_name,
                "created_at": {"$gte": start_date},
                "requires_escalation": True
            }

            # Total escalations
            total_escalations = await metrics_collection.count_documents(query)

            # Escalation reasons
            reason_pipeline = [
                {"$match": query},
                {"$group": {
                    "_id": "$escalation_reason",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}}
            ]

            cursor = metrics_collection.aggregate(reason_pipeline)
            reasons = await cursor.to_list(length=20)

            # Escalation trend by day
            daily_pipeline = [
                {"$match": query},
                {"$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id": 1}}
            ]

            cursor = metrics_collection.aggregate(daily_pipeline)
            daily_escalations = await cursor.to_list(length=days)

            return {
                "total_escalations": total_escalations,
                "escalation_reasons": [
                    {"reason": item["_id"], "count": item["count"]}
                    for item in reasons
                ],
                "daily_escalation_trend": [
                    {"date": item["_id"], "count": item["count"]}
                    for item in daily_escalations
                ],
                "period_days": days
            }

        except Exception as e:
            logger.error(f"Error getting escalation analysis: {str(e)}")
            return {}

    async def get_source_usage_stats(
        self,
        company_name: str,
        days: int = 30,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get statistics on which documents are most referenced.

        Args:
            company_name: Company identifier
            days: Number of days to analyze
            limit: Number of top sources to return

        Returns:
            List of sources with usage stats
        """
        try:
            await self._ensure_connection()
            metrics_collection = self.db[self.metrics_collection_name]

            start_date = datetime.utcnow() - timedelta(days=days)

            # Unwind sources array and group
            pipeline = [
                {"$match": {
                    "company_name": company_name,
                    "created_at": {"$gte": start_date}
                }},
                {"$unwind": "$sources_used"},
                {"$group": {
                    "_id": "$sources_used",
                    "reference_count": {"$sum": 1},
                    "avg_confidence": {"$avg": "$confidence_score"}
                }},
                {"$sort": {"reference_count": -1}},
                {"$limit": limit}
            ]

            cursor = metrics_collection.aggregate(pipeline)
            sources = await cursor.to_list(length=limit)

            return [
                {
                    "source": item["_id"],
                    "reference_count": item["reference_count"],
                    "avg_confidence": round(item["avg_confidence"], 3)
                }
                for item in sources
            ]

        except Exception as e:
            logger.error(f"Error getting source usage stats: {str(e)}")
            return []

    async def get_performance_metrics(
        self,
        company_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get performance metrics (response times, etc.).

        Args:
            company_name: Company identifier
            days: Number of days to analyze

        Returns:
            Performance metrics
        """
        try:
            await self._ensure_connection()
            metrics_collection = self.db[self.metrics_collection_name]

            start_date = datetime.utcnow() - timedelta(days=days)

            pipeline = [
                {"$match": {
                    "company_name": company_name,
                    "created_at": {"$gte": start_date}
                }},
                {"$group": {
                    "_id": None,
                    "avg_processing_time": {"$avg": "$processing_time_ms"},
                    "min_processing_time": {"$min": "$processing_time_ms"},
                    "max_processing_time": {"$max": "$processing_time_ms"},
                    "p50_processing_time": {
                        "$percentile": {
                            "input": "$processing_time_ms",
                            "p": [0.5],
                            "method": "approximate"
                        }
                    },
                    "p95_processing_time": {
                        "$percentile": {
                            "input": "$processing_time_ms",
                            "p": [0.95],
                            "method": "approximate"
                        }
                    }
                }}
            ]

            cursor = metrics_collection.aggregate(pipeline)
            stats = await cursor.to_list(length=1)

            if not stats:
                return {}

            result = stats[0]

            return {
                "avg_processing_time_ms": round(result.get("avg_processing_time", 0), 2),
                "min_processing_time_ms": round(result.get("min_processing_time", 0), 2),
                "max_processing_time_ms": round(result.get("max_processing_time", 0), 2),
                "p50_processing_time_ms": round(result.get("p50_processing_time", [0])[0], 2) if result.get("p50_processing_time") else 0,
                "p95_processing_time_ms": round(result.get("p95_processing_time", [0])[0], 2) if result.get("p95_processing_time") else 0,
                "period_days": days
            }

        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {}

    async def get_time_series_data(
        self,
        company_name: str,
        days: int = 30,
        granularity: str = "day"
    ) -> List[Dict[str, Any]]:
        """
        Get time series data for queries, confidence, escalations.

        Args:
            company_name: Company identifier
            days: Number of days to analyze
            granularity: Time granularity (hour, day, week)

        Returns:
            Time series data points
        """
        try:
            await self._ensure_connection()
            metrics_collection = self.db[self.metrics_collection_name]

            start_date = datetime.utcnow() - timedelta(days=days)

            # Determine date format based on granularity
            date_format = {
                "hour": "%Y-%m-%d %H:00",
                "day": "%Y-%m-%d",
                "week": "%Y-W%V"
            }.get(granularity, "%Y-%m-%d")

            pipeline = [
                {"$match": {
                    "company_name": company_name,
                    "created_at": {"$gte": start_date}
                }},
                {"$group": {
                    "_id": {
                        "$dateToString": {
                            "format": date_format,
                            "date": "$created_at"
                        }
                    },
                    "query_count": {"$sum": 1},
                    "avg_confidence": {"$avg": "$confidence_score"},
                    "escalation_count": {
                        "$sum": {"$cond": ["$requires_escalation", 1, 0]}
                    },
                    "avg_processing_time": {"$avg": "$processing_time_ms"}
                }},
                {"$sort": {"_id": 1}}
            ]

            cursor = metrics_collection.aggregate(pipeline)
            time_series = await cursor.to_list(length=days * 24 if granularity == "hour" else days)

            return [
                {
                    "timestamp": item["_id"],
                    "query_count": item["query_count"],
                    "avg_confidence": round(item["avg_confidence"], 3),
                    "escalation_count": item["escalation_count"],
                    "escalation_rate": round(item["escalation_count"] / item["query_count"] * 100, 2),
                    "avg_processing_time_ms": round(item["avg_processing_time"], 2)
                }
                for item in time_series
            ]

        except Exception as e:
            logger.error(f"Error getting time series data: {str(e)}")
            return []


# Global service instance
rag_analytics_service = RAGAnalyticsService()
