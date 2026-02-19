"""
Wallet Analytics Service.

Provides comprehensive analytics and insights for wallet operations including:
- Transaction volume metrics (daily/weekly/monthly)
- Revenue by payment provider
- User spending patterns
- Fraud detection statistics
- Low balance user identification
- Performance metrics

Author: KasaAI Team
Date: 2025-11-23
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class MetricPeriod(str, Enum):
    """Metric aggregation period."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    ALL_TIME = "all_time"


class WalletAnalyticsService:
    """
    Service for wallet analytics and reporting.

    Provides insights into transaction patterns, revenue, user behavior,
    and system health metrics.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize wallet analytics service.

        Args:
            database: MongoDB database connection
        """
        self.db = database
        self.wallets_collection = database.wallets
        self.transactions_collection = database.transactions
        self.fraud_alerts_collection = database.fraud_alerts
        self.logger = logging.getLogger(__name__)

    async def get_transaction_volume(
        self,
        period: MetricPeriod = MetricPeriod.DAILY,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get transaction volume metrics for a period.

        Args:
            period: Aggregation period
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            tenant_id: Optional tenant filter

        Returns:
            Dictionary with transaction volume metrics
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        query = {
            "created_at": {"$gte": start_date, "$lte": end_date},
            "status": "completed"
        }
        if tenant_id:
            query["tenant_id"] = tenant_id

        # Aggregate transactions
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": "$type",
                    "count": {"$sum": 1},
                    "total_amount": {"$sum": "$amount"}
                }
            }
        ]

        results = await self.transactions_collection.aggregate(pipeline).to_list(None)

        # Process results
        metrics = {
            "period": period.value,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_transactions": 0,
            "total_volume": Decimal("0.00"),
            "by_type": {}
        }

        for result in results:
            txn_type = result["_id"]
            count = result["count"]
            amount = Decimal(str(result["total_amount"]))

            metrics["total_transactions"] += count
            metrics["total_volume"] += amount
            metrics["by_type"][txn_type] = {
                "count": count,
                "total_amount": str(amount),
                "average_amount": str(amount / count) if count > 0 else "0.00"
            }

        metrics["total_volume"] = str(metrics["total_volume"])
        return metrics

    async def get_revenue_by_provider(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get revenue breakdown by payment provider.

        Args:
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            tenant_id: Optional tenant filter

        Returns:
            Dictionary with revenue by provider
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        query = {
            "created_at": {"$gte": start_date, "$lte": end_date},
            "status": "completed",
            "type": "credit"  # Only count deposits as revenue
        }
        if tenant_id:
            query["tenant_id"] = tenant_id

        # Aggregate by provider
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": "$metadata.payment_gateway",
                    "count": {"$sum": 1},
                    "total_revenue": {"$sum": "$amount"}
                }
            },
            {"$sort": {"total_revenue": -1}}
        ]

        results = await self.transactions_collection.aggregate(pipeline).to_list(None)

        # Process results
        metrics = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_revenue": Decimal("0.00"),
            "total_deposits": 0,
            "by_provider": []
        }

        for result in results:
            provider = result["_id"] or "unknown"
            count = result["count"]
            revenue = Decimal(str(result["total_revenue"]))

            metrics["total_revenue"] += revenue
            metrics["total_deposits"] += count
            metrics["by_provider"].append({
                "provider": provider,
                "deposit_count": count,
                "total_revenue": str(revenue),
                "average_deposit": str(revenue / count) if count > 0 else "0.00"
            })

        metrics["total_revenue"] = str(metrics["total_revenue"])
        return metrics

    async def get_user_spending_patterns(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get user spending patterns and statistics.

        Args:
            user_id: Optional specific user ID
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            limit: Maximum number of users to analyze

        Returns:
            Dictionary with user spending patterns
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        query = {
            "created_at": {"$gte": start_date, "$lte": end_date},
            "status": "completed",
            "type": "debit"
        }
        if user_id:
            query["user_id"] = user_id

        # Aggregate by user
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": "$user_id",
                    "transaction_count": {"$sum": 1},
                    "total_spent": {"$sum": "$amount"},
                    "services_used": {"$addToSet": "$metadata.service"}
                }
            },
            {"$sort": {"total_spent": -1}},
            {"$limit": limit}
        ]

        results = await self.transactions_collection.aggregate(pipeline).to_list(None)

        # Process results
        users = []
        total_users = len(results)
        total_spending = Decimal("0.00")

        for result in results:
            user_id = result["_id"]
            count = result["transaction_count"]
            spent = Decimal(str(result["total_spent"]))
            services = result.get("services_used", [])

            total_spending += spent
            users.append({
                "user_id": user_id,
                "transaction_count": count,
                "total_spent": str(spent),
                "average_transaction": str(spent / count) if count > 0 else "0.00",
                "services_used": [s for s in services if s]
            })

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_users": total_users,
            "total_spending": str(total_spending),
            "average_spending_per_user": str(total_spending / total_users) if total_users > 0 else "0.00",
            "users": users
        }

    async def get_fraud_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get fraud detection statistics.

        Args:
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            tenant_id: Optional tenant filter

        Returns:
            Dictionary with fraud statistics
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        query = {
            "created_at": {"$gte": start_date, "$lte": end_date}
        }
        if tenant_id:
            query["tenant_id"] = tenant_id

        # Get fraud alerts
        alerts = await self.fraud_alerts_collection.find(query).to_list(None)

        # Aggregate by severity
        by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        by_type = {}
        blocked_count = 0
        total_amount_blocked = Decimal("0.00")

        for alert in alerts:
            severity = alert.get("severity", "low")
            by_severity[severity] = by_severity.get(severity, 0) + 1

            alert_type = alert.get("alert_type", "unknown")
            by_type[alert_type] = by_type.get(alert_type, 0) + 1

            if alert.get("action_taken") == "blocked":
                blocked_count += 1
                total_amount_blocked += Decimal(str(alert.get("amount", 0)))

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_alerts": len(alerts),
            "blocked_transactions": blocked_count,
            "total_amount_blocked": str(total_amount_blocked),
            "by_severity": by_severity,
            "by_type": by_type
        }

    async def get_low_balance_users(
        self,
        threshold: Decimal = Decimal("10.00"),
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Identify users with low wallet balance.

        Args:
            threshold: Balance threshold (default: 10.00)
            tenant_id: Optional tenant filter

        Returns:
            List of users with low balance
        """
        query = {
            "balance": {"$lt": float(threshold)},
            "is_active": True
        }
        if tenant_id:
            query["tenant_id"] = tenant_id

        wallets = await self.wallets_collection.find(query).to_list(None)

        low_balance_users = []
        for wallet in wallets:
            low_balance_users.append({
                "user_id": wallet.get("user_id"),
                "wallet_id": str(wallet["_id"]),
                "balance": str(Decimal(str(wallet.get("balance", 0)))),
                "currency": wallet.get("currency", "USD"),
                "last_transaction_at": wallet.get("last_transaction_at", {}).isoformat() if wallet.get("last_transaction_at") else None
            })

        return low_balance_users

    async def get_system_health_metrics(
        self,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get overall system health metrics.

        Args:
            tenant_id: Optional tenant filter

        Returns:
            Dictionary with system health metrics
        """
        query = {}
        if tenant_id:
            query["tenant_id"] = tenant_id

        # Count active wallets
        active_wallets = await self.wallets_collection.count_documents({
            **query,
            "is_active": True
        })

        # Count suspended wallets
        suspended_wallets = await self.wallets_collection.count_documents({
            **query,
            "status": "suspended"
        })

        # Get total system balance
        pipeline = [
            {"$match": {**query, "is_active": True}},
            {"$group": {"_id": None, "total_balance": {"$sum": "$balance"}}}
        ]
        balance_result = await self.wallets_collection.aggregate(pipeline).to_list(None)
        total_balance = Decimal(str(balance_result[0]["total_balance"])) if balance_result else Decimal("0.00")

        # Get transaction success rate (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        total_txns = await self.transactions_collection.count_documents({
            **query,
            "created_at": {"$gte": yesterday}
        })
        successful_txns = await self.transactions_collection.count_documents({
            **query,
            "created_at": {"$gte": yesterday},
            "status": "completed"
        })

        success_rate = (successful_txns / total_txns * 100) if total_txns > 0 else 0

        return {
            "active_wallets": active_wallets,
            "suspended_wallets": suspended_wallets,
            "total_system_balance": str(total_balance),
            "transactions_last_24h": total_txns,
            "successful_transactions": successful_txns,
            "success_rate_percent": round(success_rate, 2),
            "checked_at": datetime.utcnow().isoformat()
        }

    async def get_dashboard_summary(
        self,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard summary with all key metrics.

        Args:
            tenant_id: Optional tenant filter

        Returns:
            Dictionary with dashboard summary
        """
        # Get all metrics in parallel
        yesterday = datetime.utcnow() - timedelta(days=1)
        last_30_days = datetime.utcnow() - timedelta(days=30)

        # Execute all queries
        volume_24h = await self.get_transaction_volume(
            period=MetricPeriod.DAILY,
            start_date=yesterday,
            tenant_id=tenant_id
        )

        volume_30d = await self.get_transaction_volume(
            period=MetricPeriod.MONTHLY,
            start_date=last_30_days,
            tenant_id=tenant_id
        )

        revenue = await self.get_revenue_by_provider(
            start_date=last_30_days,
            tenant_id=tenant_id
        )

        fraud = await self.get_fraud_statistics(
            start_date=last_30_days,
            tenant_id=tenant_id
        )

        health = await self.get_system_health_metrics(tenant_id=tenant_id)

        low_balance = await self.get_low_balance_users(tenant_id=tenant_id)

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "tenant_id": tenant_id,
            "transaction_volume_24h": volume_24h,
            "transaction_volume_30d": volume_30d,
            "revenue_30d": revenue,
            "fraud_statistics_30d": fraud,
            "system_health": health,
            "low_balance_users": {
                "count": len(low_balance),
                "users": low_balance[:10]  # Top 10 only
            }
        }
