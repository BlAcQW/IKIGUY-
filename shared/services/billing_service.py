"""
Billing and Wallet Service for Organizations
Handles wallet balance, transactions, and usage tracking
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class BillingService:
    """Service for managing organization billing, wallet, and usage"""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize billing service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.transactions_collection = db["wallet_transactions"]
        self.wallets_collection = db["organization_wallets"]
        self.usage_collection = db["usage_logs"]
        self.billing_collection = db["billing_records"]
        self.calls_collection = db["automation_calls"]
        self.configs_collection = db["automation_configs"]

    async def initialize_indexes(self):
        """Create necessary indexes for billing collections"""
        # Wallet transactions indexes
        await self.transactions_collection.create_index([("organization_id", 1)])
        await self.transactions_collection.create_index([("created_at", -1)])
        await self.transactions_collection.create_index(
            [("organization_id", 1), ("created_at", -1)]
        )

        # Wallets indexes
        await self.wallets_collection.create_index([("organization_id", 1)], unique=True)

        # Usage logs indexes
        await self.usage_collection.create_index([("organization_id", 1)])
        await self.usage_collection.create_index([("service", 1)])
        await self.usage_collection.create_index([("created_at", -1)])
        await self.usage_collection.create_index(
            [("organization_id", 1), ("service", 1), ("created_at", -1)]
        )

    async def get_wallet(self, organization_id: str) -> Dict[str, Any]:
        """
        Get or create wallet for an organization.

        Args:
            organization_id: Organization ID

        Returns:
            Wallet document with balance and metadata
        """
        wallet = await self.wallets_collection.find_one(
            {"organization_id": organization_id}
        )

        if not wallet:
            # Create new wallet
            wallet = {
                "organization_id": organization_id,
                "balance": 0.0,
                "currency": "USD",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            result = await self.wallets_collection.insert_one(wallet)
            wallet["_id"] = result.inserted_id

        # Convert ObjectId to string for JSON serialization
        wallet["id"] = str(wallet.pop("_id"))
        return wallet

    async def add_funds(
        self, organization_id: str, amount: float, description: str = "Funds added"
    ) -> Dict[str, Any]:
        """
        Add funds to organization wallet.

        Args:
            organization_id: Organization ID
            amount: Amount to add (must be positive)
            description: Transaction description

        Returns:
            Transaction document

        Raises:
            ValueError: If amount is not positive
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        # Get or create wallet
        wallet = await self.get_wallet(organization_id)

        # Create transaction
        transaction = {
            "organization_id": organization_id,
            "type": "credit",
            "amount": amount,
            "balance_after": wallet["balance"] + amount,
            "description": description,
            "created_at": datetime.utcnow(),
        }

        result = await self.transactions_collection.insert_one(transaction)
        transaction["id"] = str(result.inserted_id)
        transaction.pop("_id", None)

        # Update wallet balance
        await self.wallets_collection.update_one(
            {"organization_id": organization_id},
            {
                "$inc": {"balance": amount},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )

        return transaction

    async def deduct_funds(
        self,
        organization_id: str,
        amount: float,
        service: str,
        description: str = "Service usage",
    ) -> Dict[str, Any]:
        """
        Deduct funds from organization wallet.

        Args:
            organization_id: Organization ID
            amount: Amount to deduct (must be positive)
            service: Service name (e.g., 'tts', 'asr', 'llm')
            description: Transaction description

        Returns:
            Transaction document

        Raises:
            ValueError: If amount is not positive or insufficient balance
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        # Get wallet
        wallet = await self.get_wallet(organization_id)

        if wallet["balance"] < amount:
            raise ValueError("Insufficient balance")

        # Create transaction
        transaction = {
            "organization_id": organization_id,
            "type": "debit",
            "amount": amount,
            "service": service,
            "balance_after": wallet["balance"] - amount,
            "description": description,
            "created_at": datetime.utcnow(),
        }

        result = await self.transactions_collection.insert_one(transaction)
        transaction["id"] = str(result.inserted_id)
        transaction.pop("_id", None)

        # Update wallet balance
        await self.wallets_collection.update_one(
            {"organization_id": organization_id},
            {
                "$inc": {"balance": -amount},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )

        return transaction

    async def get_transactions(
        self,
        organization_id: str,
        limit: int = 50,
        skip: int = 0,
        transaction_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get transaction history for an organization.

        Args:
            organization_id: Organization ID
            limit: Maximum number of transactions to return
            skip: Number of transactions to skip
            transaction_type: Filter by type ('credit' or 'debit')

        Returns:
            List of transaction documents
        """
        query = {"organization_id": organization_id}
        if transaction_type:
            query["type"] = transaction_type

        cursor = (
            self.transactions_collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        transactions = []
        async for transaction in cursor:
            transaction["id"] = str(transaction.pop("_id"))
            transactions.append(transaction)

        return transactions

    async def get_usage_stats(
        self, organization_id: str, period: str = "week"
    ) -> Dict[str, Any]:
        """
        Get usage statistics for an organization.

        Args:
            organization_id: Organization ID
            period: Time period ('day', 'week', 'month', 'year')

        Returns:
            Usage statistics by service
        """
        # Calculate date range
        now = datetime.utcnow()
        if period == "day":
            start_date = now - timedelta(days=1)
        elif period == "week":
            start_date = now - timedelta(weeks=1)
        elif period == "month":
            start_date = now - timedelta(days=30)
        elif period == "year":
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(weeks=1)  # Default to week

        # Aggregate usage by service
        pipeline = [
            {
                "$match": {
                    "organization_id": organization_id,
                    "type": "debit",
                    "created_at": {"$gte": start_date},
                }
            },
            {
                "$group": {
                    "_id": "$service",
                    "total_amount": {"$sum": "$amount"},
                    "count": {"$sum": 1},
                }
            },
        ]

        cursor = self.transactions_collection.aggregate(pipeline)
        services = {}
        total_spent = 0.0

        async for service in cursor:
            service_name = service["_id"] or "other"
            amount = service["total_amount"]
            services[service_name] = {
                "amount": round(amount, 2),
                "count": service["count"],
            }
            total_spent += amount

        return {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": now.isoformat(),
            "total_spent": round(total_spent, 2),
            "services": services,
        }

    async def log_usage(
        self,
        organization_id: str,
        service: str,
        units: int,
        cost: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Log service usage and deduct funds.

        Args:
            organization_id: Organization ID
            service: Service name
            units: Number of units used
            cost: Cost of usage
            metadata: Additional metadata

        Returns:
            Usage log document
        """
        # Deduct funds
        transaction = await self.deduct_funds(
            organization_id, cost, service, f"{service} usage - {units} units"
        )

        # Create usage log
        usage_log = {
            "organization_id": organization_id,
            "service": service,
            "units": units,
            "cost": cost,
            "transaction_id": transaction["id"],
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
        }

        result = await self.usage_collection.insert_one(usage_log)
        usage_log["id"] = str(result.inserted_id)
        usage_log.pop("_id", None)

        return usage_log

    # ==================== BILLING RECORDS METHODS ====================
    # For tracking detailed VAPI automation call costs

    async def create_billing_record_from_call(
        self,
        call_doc: Dict[str, Any],
        organization_id: str,
        automation_name: str
    ) -> Optional[str]:
        """
        Create a billing record from an automation call.

        Enhanced with detailed cost breakdown for better analytics.

        Args:
            call_doc: Call document from automation_calls collection
            organization_id: Organization ID for billing
            automation_name: Name of the automation

        Returns:
            Billing record ID if created, None if already exists or no cost
        """
        try:
            import logging
            logger = logging.getLogger(__name__)

            call_id = call_doc.get("call_id")
            vapi_cost = call_doc.get("vapi_cost", 0.0)

            # Skip if no cost
            if not vapi_cost or vapi_cost <= 0:
                logger.info(f"Skipping billing for call {call_id}: no cost")
                return None

            # Check if billing record already exists for this call
            existing = await self.billing_collection.find_one({
                "metadata.call_id": call_id
            })

            if existing:
                logger.info(f"Billing record already exists for call {call_id}")
                return None

            # Calculate detailed cost breakdown
            # Reason: VAPI provides total cost but not itemized breakdown
            # We estimate based on typical composition:
            # - 40% Voice/network costs (Twilio/Vonage connectivity)
            # - 40% AI/LLM processing (GPT, Claude, etc.)
            # - 20% Phone/telephony charges (phone number rental, SMS, etc.)
            duration_seconds = call_doc.get("duration", 0)
            duration_minutes = duration_seconds / 60.0 if duration_seconds else 0

            cost_breakdown = {
                "voice_minutes": round(vapi_cost * 0.4, 4),
                "ai_processing": round(vapi_cost * 0.4, 4),
                "phone_charges": round(vapi_cost * 0.2, 4),
                "duration_minutes": round(duration_minutes, 2),
                "duration_seconds": duration_seconds
            }

            # Extract integration usage from call data if available
            integrations_used = call_doc.get("integrations_used", [])
            if not integrations_used and "tools_called" in call_doc:
                # Fallback to extracting from tools_called
                integrations_used = [tool.get("name") for tool in call_doc.get("tools_called", []) if tool.get("name")]

            # Create billing record
            from datetime import timezone
            billing_record = {
                "organization_id": organization_id,
                "service_type": "vapi",
                "amount": float(vapi_cost),
                "currency": "USD",
                "description": f"VAPI call for {automation_name}",
                "cost_breakdown": cost_breakdown,  # NEW: Detailed cost breakdown
                "metadata": {
                    "call_id": call_id,
                    "automation_id": call_doc.get("automation_id"),
                    "automation_name": automation_name,
                    "assistant_id": call_doc.get("assistant_id"),
                    "duration": duration_seconds,
                    "status": call_doc.get("status"),
                    "customer_number": call_doc.get("customer_number"),
                    "integrations_used": integrations_used  # NEW: Track integrations
                },
                "call_started_at": call_doc.get("started_at"),
                "call_ended_at": call_doc.get("ended_at"),
                "billing_period": self._get_billing_period(call_doc.get("started_at")),
                "status": "pending",  # pending, billed, paid
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }

            result = await self.billing_collection.insert_one(billing_record)
            logger.info(f"Created billing record {result.inserted_id} for call {call_id} with cost breakdown")

            return str(result.inserted_id)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating billing record from call: {e}")
            return None

    async def create_billing_records_for_automation(
        self,
        automation_id: str
    ) -> Dict[str, Any]:
        """
        Create billing records for all calls of an automation.

        Args:
            automation_id: Automation configuration ID

        Returns:
            Summary of billing records created
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            from datetime import timezone

            # Get automation config to find organization
            config = await self.configs_collection.find_one({"_id": ObjectId(automation_id)})
            if not config:
                return {
                    "success": False,
                    "error": "Automation configuration not found"
                }

            organization_id = config.get("organization_id")
            if not organization_id:
                return {
                    "success": False,
                    "error": "Automation not linked to an organization"
                }

            automation_name = config.get("automation_name", "Unknown Automation")

            # Get all calls for this automation
            cursor = self.calls_collection.find({"automation_id": automation_id})
            calls = await cursor.to_list(length=None)

            # Create billing records
            created_count = 0
            skipped_count = 0
            total_amount = 0.0

            for call in calls:
                billing_id = await self.create_billing_record_from_call(
                    call,
                    organization_id,
                    automation_name
                )

                if billing_id:
                    created_count += 1
                    total_amount += call.get("vapi_cost", 0.0)
                else:
                    skipped_count += 1

            return {
                "success": True,
                "automation_id": automation_id,
                "organization_id": organization_id,
                "total_calls": len(calls),
                "billing_records_created": created_count,
                "billing_records_skipped": skipped_count,
                "total_amount": round(total_amount, 4),
                "created_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating billing records for automation {automation_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_billing_records(
        self,
        organization_id: str,
        service_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get billing records for an organization.

        Args:
            organization_id: Organization ID
            service_type: Optional service type filter (vapi, voice, llm)
            status: Optional status filter (pending, billed, paid)
            limit: Maximum number of records to return

        Returns:
            List of billing records
        """
        try:
            import logging
            logger = logging.getLogger(__name__)

            query = {"organization_id": organization_id}

            if service_type:
                query["service_type"] = service_type

            if status:
                query["status"] = status

            cursor = self.billing_collection.find(query).sort("created_at", -1).limit(limit)
            records = await cursor.to_list(length=limit)

            # Convert ObjectId to string
            for record in records:
                record["id"] = str(record["_id"])
                del record["_id"]

            return records

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting billing records: {e}")
            return []

    async def get_billing_summary(
        self,
        organization_id: str,
        service_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get billing summary for an organization.

        Args:
            organization_id: Organization ID
            service_type: Optional service type filter

        Returns:
            Billing summary with totals by status
        """
        try:
            import logging
            logger = logging.getLogger(__name__)

            match_query = {"organization_id": organization_id}
            if service_type:
                match_query["service_type"] = service_type

            pipeline = [
                {"$match": match_query},
                {"$group": {
                    "_id": "$status",
                    "total_amount": {"$sum": "$amount"},
                    "count": {"$sum": 1}
                }}
            ]

            results = []
            async for doc in self.billing_collection.aggregate(pipeline):
                results.append(doc)

            # Format summary
            summary = {
                "organization_id": organization_id,
                "totals": {
                    "pending": 0.0,
                    "billed": 0.0,
                    "paid": 0.0,
                    "total": 0.0
                },
                "counts": {
                    "pending": 0,
                    "billed": 0,
                    "paid": 0,
                    "total": 0
                }
            }

            for result in results:
                status = result["_id"]
                amount = result["total_amount"]
                count = result["count"]

                summary["totals"][status] = round(amount, 4)
                summary["totals"]["total"] += amount
                summary["counts"][status] = count
                summary["counts"]["total"] += count

            summary["totals"]["total"] = round(summary["totals"]["total"], 4)

            return summary

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting billing summary: {e}")
            return {
                "organization_id": organization_id,
                "error": str(e)
            }

    def _get_billing_period(self, call_date: Optional[datetime]) -> str:
        """
        Get billing period (YYYY-MM) for a call date.

        Args:
            call_date: Call start date

        Returns:
            Billing period string (e.g., "2025-10")
        """
        from datetime import timezone
        if not call_date:
            call_date = datetime.now(timezone.utc)

        return call_date.strftime("%Y-%m")


# Global service instance getter
_billing_service_instance = None


def get_billing_service(db: AsyncIOMotorDatabase = None) -> BillingService:
    """
    Get billing service instance.

    Args:
        db: Database instance (required on first call)

    Returns:
        BillingService instance
    """
    global _billing_service_instance

    if _billing_service_instance is None:
        if db is None:
            raise ValueError("Database instance required on first call")
        _billing_service_instance = BillingService(db)

    return _billing_service_instance
