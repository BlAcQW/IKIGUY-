"""
Usage Charge Service - Integrates Wallet with Automation Costs.

Automatically deducts costs from user wallet when automations run.
Integrated with analytics and cost tracking.
"""

import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from .wallet_service import WalletService
from ..models.wallet import Currency, TransactionType

logger = logging.getLogger(__name__)


class UsageChargeService:
    """
    Service for charging wallet for automation usage.

    Integrates with:
    - WalletService for balance deduction
    - AnalyticsService for cost tracking
    - Automation execution for real-time charging
    """

    def __init__(self, db: AsyncIOMotorDatabase, wallet_service: WalletService):
        """
        Initialize usage charge service.

        Args:
            db: MongoDB database
            wallet_service: Wallet service instance
        """
        self.db = db
        self.wallet_service = wallet_service
        self.analytics = db.analytics_data
        self.automations = db.automation_configs

        logger.info("Usage charge service initialized")

    async def charge_for_automation_run(
        self,
        user_id: str,
        automation_id: str,
        cost: Decimal,
        currency: Currency = Currency.USD,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Charge user wallet for automation execution.

        Args:
            user_id: User ID
            automation_id: Automation/campaign ID
            cost: Cost amount
            currency: Currency
            description: Charge description
            metadata: Additional metadata (call_id, duration, etc.)

        Returns:
            Charge result with transaction ID and balance info
        """
        try:
            # Get wallet
            wallet = await self.wallet_service.get_or_create_wallet(user_id, currency)

            # Check sufficient balance
            if wallet.available_balance < cost:
                logger.warning(f"Insufficient balance for user {user_id}: {wallet.available_balance} < {cost}")
                return {
                    "success": False,
                    "error": "insufficient_balance",
                    "message": f"Insufficient balance. Available: {wallet.available_balance}, Required: {cost}",
                    "current_balance": float(wallet.available_balance),
                    "required_amount": float(cost),
                    "shortfall": float(cost - wallet.available_balance)
                }

            # Get automation details for description
            if not description:
                automation = await self.automations.find_one({"_id": automation_id})
                automation_name = automation.get("name", "Automation") if automation else "Automation"
                description = f"Usage charge - {automation_name}"

            # Create usage charge transaction
            from ..models.wallet import Transaction, TransactionStatus

            transaction = Transaction(
                user_id=user_id,
                wallet_id=wallet.id,
                transaction_type=TransactionType.USAGE_CHARGE,
                status=TransactionStatus.PENDING,
                amount=cost,
                currency=currency,
                processing_fee=Decimal("0.00"),  # No fees for usage charges
                total_amount=cost,
                description=description,
                balance_before=wallet.balance,
                balance_after=wallet.balance - cost,
                metadata={
                    "automation_id": automation_id,
                    "charged_at": datetime.utcnow().isoformat(),
                    **(metadata or {})
                }
            )

            # Save transaction
            await self.db.transactions.insert_one(transaction.dict())

            # Deduct from wallet balance
            updated_wallet = await self.wallet_service.update_wallet_balance(
                wallet.id,
                cost,
                "usage_charge"
            )

            # Mark transaction as completed
            transaction.status = TransactionStatus.COMPLETED
            transaction.completed_at = datetime.utcnow()
            transaction.updated_at = datetime.utcnow()

            await self.db.transactions.update_one(
                {"id": transaction.id},
                {"$set": {
                    "status": TransactionStatus.COMPLETED.value,
                    "completed_at": transaction.completed_at,
                    "updated_at": transaction.updated_at
                }}
            )

            logger.info(f"Charged ${cost} from user {user_id} for automation {automation_id}")

            # Check if balance is low
            low_balance_threshold = wallet.low_balance_threshold if wallet.low_balance_alert_enabled else Decimal("0.00")
            is_low_balance = updated_wallet.available_balance < low_balance_threshold

            # Trigger auto-reload if enabled and threshold met
            should_auto_reload = (
                wallet.auto_reload_enabled and
                updated_wallet.available_balance < wallet.auto_reload_threshold
            )

            result = {
                "success": True,
                "transaction_id": transaction.id,
                "amount_charged": float(cost),
                "currency": currency.value,
                "previous_balance": float(wallet.balance),
                "new_balance": float(updated_wallet.balance),
                "available_balance": float(updated_wallet.available_balance),
                "is_low_balance": is_low_balance,
                "auto_reload_triggered": False
            }

            # Trigger auto-reload if needed
            if should_auto_reload and wallet.auto_reload_payment_method_id:
                logger.info(f"Triggering auto-reload for user {user_id}")
                reload_result = await self._trigger_auto_reload(
                    user_id,
                    wallet,
                    updated_wallet.available_balance
                )
                result["auto_reload_triggered"] = reload_result["success"]
                result["auto_reload_transaction_id"] = reload_result.get("transaction_id")

            return result

        except Exception as e:
            logger.error(f"Failed to charge user {user_id}: {str(e)}")
            return {
                "success": False,
                "error": "charge_failed",
                "message": str(e)
            }

    async def charge_for_voice_call(
        self,
        user_id: str,
        call_id: str,
        duration_seconds: int,
        cost_per_minute: Decimal,
        automation_id: Optional[str] = None,
        currency: Currency = Currency.USD
    ) -> Dict[str, Any]:
        """
        Charge for voice call based on duration.

        Args:
            user_id: User ID
            call_id: Call ID
            duration_seconds: Call duration in seconds
            cost_per_minute: Cost per minute rate
            automation_id: Associated automation ID
            currency: Currency

        Returns:
            Charge result
        """
        # Calculate cost
        duration_minutes = Decimal(duration_seconds) / Decimal("60")
        total_cost = duration_minutes * cost_per_minute

        # Round to 2 decimal places
        total_cost = total_cost.quantize(Decimal("0.01"))

        return await self.charge_for_automation_run(
            user_id=user_id,
            automation_id=automation_id or call_id,
            cost=total_cost,
            currency=currency,
            description=f"Voice call - {duration_seconds}s",
            metadata={
                "call_id": call_id,
                "duration_seconds": duration_seconds,
                "duration_minutes": float(duration_minutes),
                "cost_per_minute": float(cost_per_minute),
                "charge_type": "voice_call"
            }
        )

    async def charge_for_sms(
        self,
        user_id: str,
        message_count: int,
        cost_per_sms: Decimal,
        automation_id: Optional[str] = None,
        currency: Currency = Currency.USD
    ) -> Dict[str, Any]:
        """
        Charge for SMS messages sent.

        Args:
            user_id: User ID
            message_count: Number of messages
            cost_per_sms: Cost per SMS
            automation_id: Associated automation ID
            currency: Currency

        Returns:
            Charge result
        """
        total_cost = Decimal(message_count) * cost_per_sms

        return await self.charge_for_automation_run(
            user_id=user_id,
            automation_id=automation_id or "sms_campaign",
            cost=total_cost,
            currency=currency,
            description=f"SMS messages - {message_count} sent",
            metadata={
                "message_count": message_count,
                "cost_per_sms": float(cost_per_sms),
                "charge_type": "sms"
            }
        )

    async def charge_for_ai_usage(
        self,
        user_id: str,
        tokens_used: int,
        cost_per_token: Decimal,
        model: str,
        automation_id: Optional[str] = None,
        currency: Currency = Currency.USD
    ) -> Dict[str, Any]:
        """
        Charge for AI model usage (GPT, Claude, etc.).

        Args:
            user_id: User ID
            tokens_used: Number of tokens consumed
            cost_per_token: Cost per token
            model: Model name
            automation_id: Associated automation ID
            currency: Currency

        Returns:
            Charge result
        """
        total_cost = (Decimal(tokens_used) * cost_per_token).quantize(Decimal("0.0001"))

        return await self.charge_for_automation_run(
            user_id=user_id,
            automation_id=automation_id or "ai_usage",
            cost=total_cost,
            currency=currency,
            description=f"AI usage - {model}",
            metadata={
                "tokens_used": tokens_used,
                "cost_per_token": float(cost_per_token),
                "model": model,
                "charge_type": "ai_usage"
            }
        )

    async def get_user_usage_summary(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get usage summary for user.

        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date

        Returns:
            Usage summary with costs breakdown
        """
        from datetime import timedelta

        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Get usage transactions
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "transaction_type": TransactionType.USAGE_CHARGE.value,
                    "status": "completed",
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$metadata.charge_type",
                    "total_cost": {"$sum": "$amount"},
                    "transaction_count": {"$sum": 1}
                }
            }
        ]

        usage_breakdown = []
        total_cost = Decimal("0.00")

        async for item in self.db.transactions.aggregate(pipeline):
            cost = Decimal(str(item["total_cost"]))
            usage_breakdown.append({
                "charge_type": item["_id"] or "general",
                "total_cost": float(cost),
                "transaction_count": item["transaction_count"]
            })
            total_cost += cost

        return {
            "user_id": user_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "total_cost": float(total_cost),
            "usage_breakdown": usage_breakdown
        }

    async def _trigger_auto_reload(
        self,
        user_id: str,
        wallet,
        current_balance: Decimal
    ) -> Dict[str, Any]:
        """
        Trigger automatic wallet reload.

        Args:
            user_id: User ID
            wallet: Wallet instance
            current_balance: Current balance

        Returns:
            Reload result
        """
        try:
            # Create deposit with saved payment method
            transaction = await self.wallet_service.create_deposit(
                user_id=user_id,
                amount=wallet.auto_reload_amount,
                currency=wallet.currency,
                payment_method_id=wallet.auto_reload_payment_method_id,
                description=f"Auto-reload (triggered at ${current_balance})"
            )

            logger.info(f"Auto-reload triggered for user {user_id}: ${wallet.auto_reload_amount}")

            return {
                "success": True,
                "transaction_id": transaction.id,
                "amount": float(wallet.auto_reload_amount)
            }

        except Exception as e:
            logger.error(f"Auto-reload failed for user {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def check_balance_before_run(
        self,
        user_id: str,
        estimated_cost: Decimal,
        currency: Currency = Currency.USD
    ) -> Dict[str, Any]:
        """
        Check if user has sufficient balance before running automation.

        Args:
            user_id: User ID
            estimated_cost: Estimated cost
            currency: Currency

        Returns:
            Balance check result
        """
        try:
            wallet = await self.wallet_service.get_or_create_wallet(user_id, currency)

            has_sufficient_balance = wallet.available_balance >= estimated_cost

            return {
                "has_sufficient_balance": has_sufficient_balance,
                "current_balance": float(wallet.available_balance),
                "required_amount": float(estimated_cost),
                "shortfall": float(max(Decimal("0.00"), estimated_cost - wallet.available_balance)),
                "currency": currency.value
            }

        except Exception as e:
            logger.error(f"Balance check failed: {str(e)}")
            return {
                "has_sufficient_balance": False,
                "error": str(e)
            }
