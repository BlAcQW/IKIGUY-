"""
Usage tracking service for StudyFlow.

Tracks usage metrics and calculates costs using the shared UsageCalculator.
Supports multiple pricing tiers and provides comprehensive usage analytics.
"""

import sys
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal

# Add shared services to path
sys.path.insert(0, "/opt/kasaai/apps")

from shared.integration.usage_calculator import (
    UsageCalculator,
    PricingTier,
    ServiceType,
    Currency,
    UsageMetric,
    CostBreakdown
)

from app.core.database import mongodb
from bson import ObjectId

logger = logging.getLogger(__name__)

# MongoDB collections
COLLECTION_USAGE_METRICS = "usage_metrics"
COLLECTION_USER_TIERS = "user_pricing_tiers"


class UsageService:
    """
    Service for tracking usage and calculating costs in StudyFlow.

    Integrates with shared UsageCalculator for cost calculations and provides
    analytics for students, parents, and admins.
    """

    @staticmethod
    def get_calculator(tier: PricingTier = PricingTier.BASIC) -> UsageCalculator:
        """
        Get a usage calculator for a specific tier.

        Args:
            tier: Pricing tier

        Returns:
            UsageCalculator instance
        """
        return UsageCalculator(tier=tier)

    @staticmethod
    async def get_user_tier(user_id: str) -> PricingTier:
        """
        Get pricing tier for a user.

        Args:
            user_id: User ID

        Returns:
            User's pricing tier (defaults to BASIC if not set)
        """
        collection = mongodb.get_collection(COLLECTION_USER_TIERS)
        tier_doc = await collection.find_one({"user_id": user_id})

        if tier_doc and "tier" in tier_doc:
            try:
                return PricingTier(tier_doc["tier"])
            except ValueError:
                logger.warning(f"Invalid tier for user {user_id}: {tier_doc['tier']}")
                return PricingTier.BASIC

        return PricingTier.BASIC

    @staticmethod
    async def set_user_tier(user_id: str, tier: PricingTier) -> bool:
        """
        Set pricing tier for a user.

        Args:
            user_id: User ID
            tier: Pricing tier to set

        Returns:
            True if successful
        """
        collection = mongodb.get_collection(COLLECTION_USER_TIERS)

        await collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "tier": tier.value,
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "user_id": user_id,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )

        logger.info(f"Set pricing tier for user {user_id}: {tier.value}")
        return True

    @staticmethod
    async def track_rag_usage(
        user_id: str,
        session_id: str,
        question_id: str,
        input_tokens: int,
        output_tokens: int,
        num_queries: int = 1,
        provider: str = "gemini",
        model: str = "gemini-2.5-flash",
        subject: Optional[str] = None,
        topic: Optional[str] = None
    ) -> UsageMetric:
        """
        Track RAG query usage and calculate cost.

        Args:
            user_id: User ID (student or parent)
            session_id: Study session ID
            question_id: Question ID
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            num_queries: Number of queries (default 1)
            provider: AI provider (gemini, openai, anthropic)
            model: Model name
            subject: Subject (optional)
            topic: Topic (optional)

        Returns:
            UsageMetric with cost details
        """
        # Get user's pricing tier
        tier = await UsageService.get_user_tier(user_id)

        # Create calculator
        calculator = UsageService.get_calculator(tier)

        # Calculate cost
        metric = calculator.calculate_rag_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            num_queries=num_queries,
            provider=provider,
            model=model
        )

        # Add StudyFlow-specific metadata
        metric.metadata.update({
            "user_id": user_id,
            "session_id": session_id,
            "question_id": question_id,
            "subject": subject,
            "topic": topic
        })

        # Save to database
        await UsageService._save_metric(metric)

        logger.info(
            f"RAG usage tracked: {user_id} - {input_tokens + output_tokens} tokens - "
            f"{metric.total_cost} {metric.currency}"
        )

        return metric

    @staticmethod
    async def track_document_processing(
        user_id: str,
        material_id: str,
        num_pages: int,
        file_size_mb: float,
        document_type: str = "pdf"
    ) -> UsageMetric:
        """
        Track document processing usage.

        Args:
            user_id: User ID
            material_id: Material ID
            num_pages: Number of pages processed
            file_size_mb: File size in MB
            document_type: Document type (pdf, docx, txt)

        Returns:
            UsageMetric with cost details
        """
        # Get user's pricing tier
        tier = await UsageService.get_user_tier(user_id)

        # Create calculator
        calculator = UsageService.get_calculator(tier)

        # Calculate cost
        metric = calculator.calculate_document_processing_cost(
            num_pages=num_pages,
            file_size_mb=file_size_mb,
            document_type=document_type
        )

        # Add StudyFlow-specific metadata
        metric.metadata.update({
            "user_id": user_id,
            "material_id": material_id
        })

        # Save to database
        await UsageService._save_metric(metric)

        logger.info(
            f"Document processing tracked: {user_id} - {num_pages} pages - "
            f"{metric.total_cost} {metric.currency}"
        )

        return metric

    @staticmethod
    async def _save_metric(metric: UsageMetric) -> str:
        """
        Save usage metric to database.

        Args:
            metric: UsageMetric to save

        Returns:
            Inserted metric ID
        """
        collection = mongodb.get_collection(COLLECTION_USAGE_METRICS)

        metric_dict = metric.dict()
        metric_dict["service_type"] = metric.service_type.value
        metric_dict["currency"] = metric.currency.value

        result = await collection.insert_one(metric_dict)
        return str(result.inserted_id)

    @staticmethod
    async def get_user_usage(
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        service_type: Optional[ServiceType] = None
    ) -> List[UsageMetric]:
        """
        Get usage metrics for a user.

        Args:
            user_id: User ID
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            service_type: Service type filter (optional)

        Returns:
            List of usage metrics
        """
        collection = mongodb.get_collection(COLLECTION_USAGE_METRICS)

        # Build query
        query = {"metadata.user_id": user_id}

        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date

        if service_type:
            query["service_type"] = service_type.value

        # Fetch metrics
        cursor = collection.find(query).sort("timestamp", -1)

        metrics = []
        async for metric_doc in cursor:
            try:
                # Convert back to enum
                metric_doc["service_type"] = ServiceType(metric_doc["service_type"])
                metric_doc["currency"] = Currency(metric_doc["currency"])

                metrics.append(UsageMetric(**metric_doc))
            except Exception as e:
                logger.error(f"Error parsing metric: {str(e)}")
                continue

        return metrics

    @staticmethod
    async def get_usage_summary(
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get usage summary for a user.

        Args:
            user_id: User ID
            start_date: Start date filter (optional)
            end_date: End date filter (optional)

        Returns:
            Usage summary with totals and breakdowns
        """
        # Get metrics
        metrics = await UsageService.get_user_usage(user_id, start_date, end_date)

        if not metrics:
            return {
                "user_id": user_id,
                "total_cost": 0.0,
                "currency": Currency.GHS.value,
                "total_queries": 0,
                "total_tokens": 0,
                "metrics_count": 0,
                "by_service": {},
                "by_subject": {},
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }

        # Calculate totals
        total_cost = sum(m.total_cost for m in metrics)
        currency = metrics[0].currency

        # Count by service type
        by_service: Dict[str, Dict[str, Any]] = {}
        for metric in metrics:
            service = metric.service_type.value
            if service not in by_service:
                by_service[service] = {
                    "count": 0,
                    "total_cost": Decimal('0.00'),
                    "total_quantity": Decimal('0.00')
                }

            by_service[service]["count"] += 1
            by_service[service]["total_cost"] += metric.total_cost
            by_service[service]["total_quantity"] += metric.quantity

        # Convert to float for JSON
        for service in by_service:
            by_service[service]["total_cost"] = float(by_service[service]["total_cost"])
            by_service[service]["total_quantity"] = float(by_service[service]["total_quantity"])

        # Count by subject (for RAG queries)
        by_subject: Dict[str, Dict[str, Any]] = {}
        for metric in metrics:
            if metric.service_type == ServiceType.RAG_QUERY:
                subject = metric.metadata.get("subject", "Unknown")
                if subject not in by_subject:
                    by_subject[subject] = {
                        "queries": 0,
                        "total_cost": Decimal('0.00'),
                        "total_tokens": 0
                    }

                by_subject[subject]["queries"] += 1
                by_subject[subject]["total_cost"] += metric.total_cost
                by_subject[subject]["total_tokens"] += int(metric.quantity)

        # Convert to float for JSON
        for subject in by_subject:
            by_subject[subject]["total_cost"] = float(by_subject[subject]["total_cost"])

        # Count totals for RAG
        total_queries = sum(s["queries"] for s in by_subject.values())
        total_tokens = sum(s["total_tokens"] for s in by_subject.values())

        return {
            "user_id": user_id,
            "total_cost": float(total_cost),
            "currency": currency.value,
            "total_queries": total_queries,
            "total_tokens": total_tokens,
            "metrics_count": len(metrics),
            "by_service": by_service,
            "by_subject": by_subject,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }

    @staticmethod
    async def get_cost_estimate(
        tier: PricingTier,
        input_tokens: int,
        output_tokens: int,
        num_queries: int = 1
    ) -> Dict[str, Any]:
        """
        Get cost estimate for RAG queries.

        Args:
            tier: Pricing tier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            num_queries: Number of queries

        Returns:
            Cost estimate details
        """
        calculator = UsageService.get_calculator(tier)

        metric = calculator.calculate_rag_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            num_queries=num_queries
        )

        return {
            "tier": tier.value,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "num_queries": num_queries,
            "estimated_cost": float(metric.total_cost),
            "currency": metric.currency.value,
            "cost_breakdown": {
                "input_cost": float(metric.metadata["input_cost"]),
                "output_cost": float(metric.metadata["output_cost"]),
                "base_cost": float(metric.metadata["base_cost"])
            }
        }

    @staticmethod
    async def get_admin_analytics(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get system-wide usage analytics for admins.

        Args:
            start_date: Start date filter (optional, defaults to 30 days ago)
            end_date: End date filter (optional, defaults to now)

        Returns:
            Admin analytics with system-wide stats
        """
        # Default to last 30 days
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        collection = mongodb.get_collection(COLLECTION_USAGE_METRICS)

        # Build query
        query = {
            "timestamp": {
                "$gte": start_date,
                "$lte": end_date
            }
        }

        # Aggregate statistics
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": None,
                    "total_cost": {"$sum": "$total_cost"},
                    "total_metrics": {"$sum": 1},
                    "unique_users": {"$addToSet": "$metadata.user_id"},
                    "by_service": {
                        "$push": {
                            "service": "$service_type",
                            "cost": "$total_cost",
                            "quantity": "$quantity"
                        }
                    }
                }
            }
        ]

        result = await collection.aggregate(pipeline).to_list(length=1)

        if not result:
            return {
                "total_cost": 0.0,
                "total_metrics": 0,
                "unique_users": 0,
                "by_service": {},
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }

        data = result[0]

        # Group by service type
        by_service: Dict[str, Dict[str, Any]] = {}
        for item in data["by_service"]:
            service = item["service"]
            if service not in by_service:
                by_service[service] = {
                    "count": 0,
                    "total_cost": 0.0,
                    "total_quantity": 0.0
                }

            by_service[service]["count"] += 1
            by_service[service]["total_cost"] += float(item["cost"])
            by_service[service]["total_quantity"] += float(item["quantity"])

        return {
            "total_cost": float(data.get("total_cost", 0)),
            "total_metrics": data.get("total_metrics", 0),
            "unique_users": len(data.get("unique_users", [])),
            "by_service": by_service,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
