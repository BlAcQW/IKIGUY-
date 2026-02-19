"""
Query Complexity Router for RAG queries.
Analyzes query complexity and routes to appropriate processing strategies.
"""

import logging
import re
from typing import Dict, Any, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class QueryComplexity(str, Enum):
    """Query complexity levels."""
    SIMPLE = "simple"  # Expected: <5s
    MODERATE = "moderate"  # Expected: 5-10s
    COMPLEX = "complex"  # Expected: 10-18s
    VERY_COMPLEX = "very_complex"  # Expected: >18s (needs optimization)


class ProcessingStrategy(str, Enum):
    """Processing strategies for different complexity levels."""
    FAST_PATH = "fast_path"  # Minimal k, skip filtering
    STANDARD_PATH = "standard_path"  # Normal processing
    OPTIMIZED_PATH = "optimized_path"  # Reduced k, aggressive timeout management
    FALLBACK_PATH = "fallback_path"  # Ultra-fast, may compromise quality


class QueryComplexityRouter:
    """Routes queries to appropriate processing strategies based on complexity."""

    def __init__(self):
        """Initialize query complexity router."""
        # Complexity indicators with weights
        self.complexity_factors = {
            "regional_filter": 5,  # +5s for regional filtering
            "plan_filter": 3,  # +3s for plan filtering
            "multiple_locations": 4,  # +4s for multi-location queries
            "community_number": 3,  # +3s for community number searches
            "market_location": 4,  # +4s for market location searches
            "list_all": 6,  # +6s for "list all" queries (high k needed)
            "very_long_query": 2,  # +2s for long queries (>100 chars)
        }

        logger.info("Query complexity router initialized")

    def analyze_query_complexity(
        self,
        query: str,
        region: Optional[str] = None,
        plan_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[QueryComplexity, int, Dict[str, Any]]:
        """
        Analyze query complexity and estimate processing time.

        Args:
            query: User query text
            region: Optional region filter
            plan_type: Optional plan type filter
            context: Additional context

        Returns:
            Tuple of (complexity_level, estimated_time_seconds, analysis_details)
        """
        complexity_score = 0
        analysis = {
            "factors": [],
            "recommendations": []
        }

        # Check for regional filter
        if region:
            complexity_score += self.complexity_factors["regional_filter"]
            analysis["factors"].append(f"Regional filter: {region} (+{self.complexity_factors['regional_filter']}s)")

        # Check for plan filter
        if plan_type:
            complexity_score += self.complexity_factors["plan_filter"]
            analysis["factors"].append(f"Plan filter: {plan_type} (+{self.complexity_factors['plan_filter']}s)")

        # Check for "list all" patterns
        list_all_patterns = [
            r"\b(list\s+all|show\s+all|find\s+all|get\s+all)\b",
            r"\b(every|each|any)\s+(provider|hospital|clinic|facility)\b"
        ]
        for pattern in list_all_patterns:
            if re.search(pattern, query.lower()):
                complexity_score += self.complexity_factors["list_all"]
                analysis["factors"].append(f"'List all' query pattern (+{self.complexity_factors['list_all']}s)")
                break

        # Check for multiple locations
        location_keywords = ["and", ",", "or", "near"]
        location_count = sum(1 for kw in location_keywords if kw in query.lower())
        if location_count >= 2:
            complexity_score += self.complexity_factors["multiple_locations"]
            analysis["factors"].append(f"Multiple locations ({location_count} indicators) (+{self.complexity_factors['multiple_locations']}s)")

        # Check for community number searches
        if re.search(r"\bcommunity\s+\d+\b", query.lower()):
            complexity_score += self.complexity_factors["community_number"]
            analysis["factors"].append(f"Community number search (+{self.complexity_factors['community_number']}s)")

        # Check for market location searches
        market_keywords = ["market", "makola", "kaneshie", "madina", "tema station"]
        if any(kw in query.lower() for kw in market_keywords):
            complexity_score += self.complexity_factors["market_location"]
            analysis["factors"].append(f"Market location search (+{self.complexity_factors['market_location']}s)")

        # Check query length
        if len(query) > 100:
            complexity_score += self.complexity_factors["very_long_query"]
            analysis["factors"].append(f"Long query ({len(query)} chars) (+{self.complexity_factors['very_long_query']}s)")

        # Base time: 2s (minimum for any RAG query)
        estimated_time = 2 + complexity_score

        # Determine complexity level
        if estimated_time < 5:
            complexity_level = QueryComplexity.SIMPLE
        elif estimated_time < 10:
            complexity_level = QueryComplexity.MODERATE
        elif estimated_time < 18:
            complexity_level = QueryComplexity.COMPLEX
        else:
            complexity_level = QueryComplexity.VERY_COMPLEX

        analysis["complexity_level"] = complexity_level
        analysis["estimated_time_seconds"] = estimated_time

        logger.info(f"🧠 Query Complexity Analysis:")
        logger.info(f"   Level: {complexity_level}")
        logger.info(f"   Estimated time: {estimated_time}s")
        logger.info(f"   Factors: {len(analysis['factors'])}")

        return complexity_level, estimated_time, analysis

    def get_processing_strategy(
        self,
        complexity: QueryComplexity,
        estimated_time: int
    ) -> Tuple[ProcessingStrategy, Dict[str, Any]]:
        """
        Get processing strategy for given complexity level.

        Args:
            complexity: Query complexity level
            estimated_time: Estimated processing time in seconds

        Returns:
            Tuple of (strategy, optimization_params)
        """
        optimization_params = {
            "timeout_budget": 18.0,  # VAPI webhook timeout minus buffer
            "skip_regeneration_threshold": 15.0,  # Skip regeneration if elapsed > 15s
        }

        if complexity == QueryComplexity.SIMPLE:
            strategy = ProcessingStrategy.FAST_PATH
            optimization_params.update({
                "max_k": 5,
                "allow_regeneration": True,
                "cache_priority": "high"
            })

        elif complexity == QueryComplexity.MODERATE:
            strategy = ProcessingStrategy.STANDARD_PATH
            optimization_params.update({
                "max_k": 10,
                "allow_regeneration": True,
                "cache_priority": "medium"
            })

        elif complexity == QueryComplexity.COMPLEX:
            strategy = ProcessingStrategy.OPTIMIZED_PATH
            optimization_params.update({
                "max_k": 15,  # Reduced from default to save time
                "allow_regeneration": False,  # Skip regeneration to save 2-3s
                "cache_priority": "high"
            })

        else:  # VERY_COMPLEX
            strategy = ProcessingStrategy.FALLBACK_PATH
            optimization_params.update({
                "max_k": 8,  # Very low k for speed
                "allow_regeneration": False,
                "cache_priority": "critical",
                "fast_response_mode": True  # Trade quality for speed
            })

        logger.info(f"📍 Processing Strategy: {strategy}")
        logger.info(f"   Max k: {optimization_params.get('max_k')}")
        logger.info(f"   Allow regeneration: {optimization_params.get('allow_regeneration')}")

        return strategy, optimization_params


# Global router instance
query_complexity_router = QueryComplexityRouter()
