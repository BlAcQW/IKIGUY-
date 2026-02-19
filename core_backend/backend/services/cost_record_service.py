"""
Cost Record Service

Service for managing cost records in MongoDB (INTERNAL ONLY).

Author: KasaAI Team
Date: 2025-10-27
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal
import logging

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING

from ..models.cost_record import CostRecordModel, COST_RECORDS_COLLECTION
from apps.shared.integration.internal_cost_tracker import ActualCost

logger = logging.getLogger(__name__)


class CostRecordService:
    """
    Service for managing cost records in MongoDB.

    IMPORTANT: This is INTERNAL ONLY. Never expose to end users.
    """

    def __init__(self, mongodb_client: AsyncIOMotorClient, database_name: str = "kasaai_core"):
        """
        Initialize cost record service.

        Args:
            mongodb_client: MongoDB async client
            database_name: Database name
        """
        self.client = mongodb_client
        self.db = self.client[database_name]
        self.collection = self.db[COST_RECORDS_COLLECTION]

    async def save_cost_record(self, cost: ActualCost) -> str:
        """
        Save a cost record to database.

        Args:
            cost: ActualCost object from cost tracker

        Returns:
            ID of inserted record
        """
        try:
            record = {
                "timestamp": cost.timestamp,
                "provider": cost.provider.value,
                "cost_type": cost.cost_type.value,
                "quantity": float(cost.quantity),
                "unit": cost.unit,
                "unit_cost": float(cost.unit_cost),
                "total_cost": float(cost.total_cost),
                "total_cost_ghs": float(cost.total_cost),  # Already in GHS
                "currency": cost.currency,
                "customer_charge": float(cost.customer_charge) if cost.customer_charge else None,
                "profit_margin": float(cost.profit_margin) if cost.profit_margin else None,
                "profit_margin_percentage": (
                    float((cost.profit_margin / cost.customer_charge * 100))
                    if cost.profit_margin and cost.customer_charge
                    else None
                ),
                "tenant_id": cost.tenant_id,
                "user_id": cost.user_id,
                "call_id": cost.call_id,
                "transaction_id": cost.transaction_id,
                "metadata": cost.metadata,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = await self.collection.insert_one(record)
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error saving cost record: {e}")
            raise

    async def get_cost_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tenant_id: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get cost summary with filters.

        Args:
            start_date: Start date for filter
            end_date: End date for filter
            tenant_id: Filter by tenant
            provider: Filter by provider

        Returns:
            Summary with revenue, costs, profit, margins
        """
        # Build query
        query = {}

        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date

        if tenant_id:
            query["tenant_id"] = tenant_id

        if provider:
            query["provider"] = provider

        # Aggregate results
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": "$customer_charge"},
                    "total_costs": {"$sum": "$total_cost_ghs"},
                    "total_profit": {"$sum": "$profit_margin"},
                    "transaction_count": {"$sum": 1},
                    "providers": {"$addToSet": "$provider"},
                    "tenants": {"$addToSet": "$tenant_id"}
                }
            }
        ]

        result = await self.collection.aggregate(pipeline).to_list(length=1)

        if not result:
            return {
                "total_revenue": 0.0,
                "total_costs": 0.0,
                "total_profit": 0.0,
                "profit_margin_percentage": 0.0,
                "transaction_count": 0,
                "providers": [],
                "tenant_count": 0
            }

        data = result[0]
        revenue = data.get("total_revenue", 0.0) or 0.0
        costs = data.get("total_costs", 0.0) or 0.0
        profit = data.get("total_profit", 0.0) or 0.0

        margin_pct = (profit / revenue * 100) if revenue > 0 else 0.0

        return {
            "total_revenue": revenue,
            "total_costs": costs,
            "total_profit": profit,
            "profit_margin_percentage": margin_pct,
            "transaction_count": data.get("transaction_count", 0),
            "providers": data.get("providers", []),
            "tenant_count": len([t for t in data.get("tenants", []) if t])
        }

    async def get_cost_breakdown_by_provider(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get cost breakdown grouped by provider.

        Args:
            start_date: Start date for filter
            end_date: End date for filter

        Returns:
            List of provider summaries
        """
        query = {}

        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date

        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": "$provider",
                    "total_revenue": {"$sum": "$customer_charge"},
                    "total_costs": {"$sum": "$total_cost_ghs"},
                    "total_profit": {"$sum": "$profit_margin"},
                    "transaction_count": {"$sum": 1}
                }
            },
            {"$sort": {"total_revenue": -1}}
        ]

        results = await self.collection.aggregate(pipeline).to_list(length=100)

        breakdown = []
        for item in results:
            revenue = item.get("total_revenue", 0.0) or 0.0
            costs = item.get("total_costs", 0.0) or 0.0
            profit = item.get("total_profit", 0.0) or 0.0
            margin_pct = (profit / revenue * 100) if revenue > 0 else 0.0

            breakdown.append({
                "provider": item["_id"],
                "total_revenue": revenue,
                "total_costs": costs,
                "total_profit": profit,
                "profit_margin_percentage": margin_pct,
                "transaction_count": item.get("transaction_count", 0)
            })

        return breakdown

    async def get_recent_records(
        self,
        limit: int = 100,
        skip: int = 0,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent cost records.

        Args:
            limit: Max number of records
            skip: Number to skip (pagination)
            tenant_id: Filter by tenant

        Returns:
            List of cost records
        """
        query = {}
        if tenant_id:
            query["tenant_id"] = tenant_id

        cursor = self.collection.find(query).sort("timestamp", DESCENDING).skip(skip).limit(limit)
        records = await cursor.to_list(length=limit)

        # Convert ObjectId to string
        for record in records:
            if "_id" in record:
                record["_id"] = str(record["_id"])

        return records

    async def delete_old_records(self, days_to_keep: int = 90) -> int:
        """
        Delete cost records older than specified days.

        Args:
            days_to_keep: Number of days to keep (default: 90)

        Returns:
            Number of deleted records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        result = await self.collection.delete_many({"timestamp": {"$lt": cutoff_date}})
        return result.deleted_count


# Singleton instance
_cost_record_service: Optional[CostRecordService] = None


def get_cost_record_service(
    mongodb_client: AsyncIOMotorClient,
    database_name: str = "kasaai_core"
) -> CostRecordService:
    """Get or create cost record service instance."""
    global _cost_record_service

    if _cost_record_service is None:
        _cost_record_service = CostRecordService(mongodb_client, database_name)

    return _cost_record_service
