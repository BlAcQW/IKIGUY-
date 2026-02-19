"""
Query Pre-computation Service for RAG.
Analyzes top query patterns and pre-computes responses for instant delivery.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class QueryPrecomputeService:
    """Service for pre-computing responses to common RAG queries."""

    def __init__(self):
        """Initialize query pre-compute service."""
        # Number of top queries to pre-compute (default: 50)
        self.precompute_limit = int(os.getenv("PRECOMPUTE_QUERY_LIMIT", "50"))

        # Minimum query count threshold for pre-computation
        # Reason: Only pre-compute queries that appear at least N times
        self.min_query_count = int(os.getenv("PRECOMPUTE_MIN_COUNT", "3"))

        # Cache TTL for pre-computed queries (24 hours)
        self.precompute_ttl = int(os.getenv("PRECOMPUTE_TTL", "86400"))

        logger.info(f"Query pre-compute service initialized (limit={self.precompute_limit}, min_count={self.min_query_count}, ttl={self.precompute_ttl}s)")

    async def precompute_top_queries(
        self,
        company_name: str,
        days: int = 7,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Pre-compute responses for top queries.

        Args:
            company_name: Company identifier
            days: Number of days to analyze for top queries (default: 7)
            force: Force re-computation even if already cached

        Returns:
            Dictionary with pre-computation results
        """
        try:
            from backend.services.tool_call_logger import tool_call_logger
            from backend.services.redis_cache_service import redis_cache_service
            from backend.services.helpdesk_rag_service import helpdesk_rag_service

            logger.info(f"🚀 Starting pre-computation for {company_name} (analyzing last {days} days)")

            # Get top query patterns from tool call logger
            top_queries = await tool_call_logger.get_top_queries(
                company_name=company_name,
                limit=self.precompute_limit,
                days=days
            )

            logger.info(f"📊 Found {len(top_queries)} top queries")

            # Filter queries that meet minimum count threshold
            queries_to_compute = [
                q for q in top_queries
                if q.total_count >= self.min_query_count
            ]

            logger.info(f"✅ {len(queries_to_compute)} queries meet threshold (min_count={self.min_query_count})")

            # Pre-compute each query
            computed_count = 0
            skipped_count = 0
            failed_count = 0
            computation_times = []

            for query_info in queries_to_compute:
                query_pattern = query_info.query_pattern

                try:
                    # Check if already cached (skip if not forced)
                    if not force:
                        cached = await redis_cache_service.get_cached_response(company_name, query_pattern)
                        if cached:
                            logger.info(f"⏭️  Skipping (already cached): '{query_pattern[:50]}'")
                            skipped_count += 1
                            continue

                    # Pre-compute the response
                    start_time = datetime.utcnow()
                    logger.info(f"🔄 Pre-computing: '{query_pattern[:50]}'")

                    result = await helpdesk_rag_service.query_knowledge_base(
                        company_name=company_name,
                        query=query_pattern
                    )

                    compute_time = (datetime.utcnow() - start_time).total_seconds()
                    computation_times.append(compute_time)

                    if result.success:
                        # Cache the pre-computed response
                        await redis_cache_service.cache_response(
                            company_name=company_name,
                            query=query_pattern,
                            response_data=result.dict(),
                            ttl=self.precompute_ttl
                        )

                        logger.info(f"✅ Pre-computed in {compute_time:.2f}s: '{query_pattern[:50]}'")
                        computed_count += 1
                    else:
                        logger.warning(f"⚠️  Failed to generate response: '{query_pattern[:50]}'")
                        failed_count += 1

                except Exception as e:
                    logger.error(f"❌ Error pre-computing query '{query_pattern[:50]}': {e}")
                    failed_count += 1

            # Calculate statistics
            avg_compute_time = sum(computation_times) / len(computation_times) if computation_times else 0
            total_time = sum(computation_times)

            result = {
                "success": True,
                "company_name": company_name,
                "analysis_period_days": days,
                "total_queries_analyzed": len(top_queries),
                "queries_meeting_threshold": len(queries_to_compute),
                "computed": computed_count,
                "skipped": skipped_count,
                "failed": failed_count,
                "avg_compute_time_seconds": round(avg_compute_time, 2),
                "total_compute_time_seconds": round(total_time, 2),
                "timestamp": datetime.utcnow().isoformat(),
                "cache_ttl_hours": self.precompute_ttl / 3600
            }

            logger.info(f"🎉 Pre-computation complete!")
            logger.info(f"   ✅ Computed: {computed_count}")
            logger.info(f"   ⏭️  Skipped: {skipped_count}")
            logger.info(f"   ❌ Failed: {failed_count}")
            logger.info(f"   ⏱️  Avg time: {avg_compute_time:.2f}s")
            logger.info(f"   🕐 Total time: {total_time:.2f}s")

            return result

        except Exception as e:
            logger.error(f"Error during pre-computation: {e}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "company_name": company_name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_precompute_status(self, company_name: str) -> Dict[str, Any]:
        """
        Get status of pre-computed queries.

        Args:
            company_name: Company identifier

        Returns:
            Status dictionary with cache statistics
        """
        try:
            from backend.services.redis_cache_service import redis_cache_service

            # Get cache statistics
            cache_stats = await redis_cache_service.get_cache_stats()

            # Get list of cached queries (from Redis)
            # Note: This is an approximation - we count all cache keys
            # In production, you might want to maintain a separate index

            status = {
                "success": True,
                "company_name": company_name,
                "cache_stats": cache_stats,
                "precompute_config": {
                    "limit": self.precompute_limit,
                    "min_query_count": self.min_query_count,
                    "ttl_seconds": self.precompute_ttl,
                    "ttl_hours": self.precompute_ttl / 3600
                },
                "timestamp": datetime.utcnow().isoformat()
            }

            return status

        except Exception as e:
            logger.error(f"Error getting pre-compute status: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def invalidate_cache(
        self,
        company_name: str,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Invalidate cached/pre-computed queries.

        Args:
            company_name: Company identifier
            query: Specific query to invalidate (if None, invalidates all)

        Returns:
            Result dictionary
        """
        try:
            from backend.services.redis_cache_service import redis_cache_service

            deleted_count = await redis_cache_service.invalidate_cache(
                company_name=company_name,
                query=query
            )

            logger.info(f"🗑️  Invalidated {deleted_count} cache entries for {company_name}")

            return {
                "success": True,
                "company_name": company_name,
                "query": query,
                "deleted_count": deleted_count,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def run_daily_precomputation(
        self,
        companies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run daily pre-computation for all active companies.

        This method is designed to be called by a cron job.

        Args:
            companies: List of company names to process (if None, processes all with recent queries)

        Returns:
            Batch pre-computation results
        """
        try:
            from backend.services.tool_call_logger import tool_call_logger

            logger.info("🕐 Starting daily pre-computation job")

            # If no companies specified, get all companies with queries in last 7 days
            if not companies:
                # Get distinct companies from recent tool calls
                from backend.services.tool_call_logger import tool_call_logger
                from datetime import datetime, timedelta

                hours = 7 * 24  # Last 7 days
                cutoff_time = datetime.utcnow() - timedelta(hours=hours)

                # Get unique companies from MongoDB
                distinct_companies = await tool_call_logger.collection.distinct(
                    "company_name",
                    {"timestamp": {"$gte": cutoff_time}}
                )

                companies = distinct_companies

            if not companies:
                logger.warning("⚠️  No active companies found for pre-computation")
                return {
                    "success": True,
                    "companies_processed": 0,
                    "total_computed": 0,
                    "message": "No active companies found"
                }

            logger.info(f"📋 Processing {len(companies)} companies: {companies}")

            # Pre-compute for each company
            results = {}
            total_computed = 0
            total_failed = 0

            for company_name in companies:
                try:
                    logger.info(f"🔄 Pre-computing for: {company_name}")

                    result = await self.precompute_top_queries(
                        company_name=company_name,
                        days=7,
                        force=False  # Skip already cached queries
                    )

                    results[company_name] = result
                    total_computed += result.get("computed", 0)
                    total_failed += result.get("failed", 0)

                except Exception as e:
                    logger.error(f"❌ Error pre-computing for {company_name}: {e}")
                    results[company_name] = {
                        "success": False,
                        "error": str(e)
                    }
                    total_failed += 1

            logger.info(f"✅ Daily job complete: {len(companies)} companies, {total_computed} queries computed")

            return {
                "success": True,
                "companies_processed": len(companies),
                "total_computed": total_computed,
                "total_failed": total_failed,
                "results": results,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Daily pre-computation job failed: {e}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global service instance
query_precompute_service = QueryPrecomputeService()
