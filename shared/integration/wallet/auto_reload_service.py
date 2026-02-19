"""
Automated Wallet Reload Service.

Automatically reloads user wallets when balance falls below threshold
by charging saved payment methods.

Features:
- Trigger reload when balance below threshold
- Charge saved payment method automatically
- Send notification on auto-reload success/failure
- Configurable per wallet
- Safety limits to prevent excessive reloads

Author: KasaAI Team
Date: 2025-11-23
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorDatabase

from .models import Wallet, PaymentMethod
from .wallet_service import WalletService
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class AutoReloadService:
    """
    Service for automated wallet reloading.

    Monitors wallet balances and automatically reloads when they fall
    below configured thresholds using saved payment methods.
    """

    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        wallet_service: WalletService,
        notification_service: Optional[NotificationService] = None
    ):
        """
        Initialize auto-reload service.

        Args:
            database: MongoDB database connection
            wallet_service: Wallet service for processing payments
            notification_service: Optional notification service
        """
        self.db = database
        self.wallet_service = wallet_service
        self.notification_service = notification_service
        self.wallets_collection = database.wallets
        self.payment_methods_collection = database.payment_methods
        self.auto_reload_logs_collection = database.auto_reload_logs
        self.logger = logging.getLogger(__name__)

        # Safety limits
        self.MAX_RELOADS_PER_DAY = 5  # Maximum reloads per wallet per day
        self.MIN_RELOAD_INTERVAL_HOURS = 1  # Minimum time between reloads

    async def check_and_reload_wallet(
        self,
        wallet_id: str,
        force: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Check if wallet needs reload and trigger if necessary.

        Args:
            wallet_id: Wallet ID to check
            force: Force reload even if not below threshold (for testing)

        Returns:
            Dictionary with reload result or None if no reload needed
        """
        try:
            # Get wallet
            wallet_doc = await self.wallets_collection.find_one({"_id": wallet_id})
            if not wallet_doc:
                self.logger.error(f"Wallet not found: {wallet_id}")
                return None

            # Check if auto-reload enabled
            if not wallet_doc.get("auto_reload_enabled", False):
                return None

            balance = Decimal(str(wallet_doc.get("balance", 0)))
            threshold = Decimal(str(wallet_doc.get("auto_reload_threshold", 0)))
            reload_amount = Decimal(str(wallet_doc.get("auto_reload_amount", 0)))
            payment_method_id = wallet_doc.get("auto_reload_payment_method_id")

            # Check if reload needed
            if not force and balance >= threshold:
                return None

            # Validate configuration
            if reload_amount <= 0:
                self.logger.warning(f"Invalid reload amount for wallet {wallet_id}: {reload_amount}")
                return None

            if not payment_method_id:
                self.logger.warning(f"No payment method configured for wallet {wallet_id}")
                return None

            # Check safety limits
            if not await self._check_safety_limits(wallet_id):
                self.logger.warning(f"Safety limits exceeded for wallet {wallet_id}")
                return {
                    "success": False,
                    "reason": "safety_limits_exceeded",
                    "message": "Too many reload attempts. Please reload manually."
                }

            # Get payment method
            payment_method = await self.payment_methods_collection.find_one({
                "_id": payment_method_id,
                "wallet_id": wallet_id,
                "is_active": True
            })

            if not payment_method:
                self.logger.error(f"Payment method not found or inactive: {payment_method_id}")
                return {
                    "success": False,
                    "reason": "payment_method_unavailable",
                    "message": "Saved payment method not available"
                }

            # Initiate reload
            result = await self._process_reload(
                wallet_id=wallet_id,
                amount=reload_amount,
                payment_method=payment_method,
                triggered_by="auto_reload"
            )

            # Log reload attempt
            await self._log_reload_attempt(
                wallet_id=wallet_id,
                amount=reload_amount,
                success=result["success"],
                details=result
            )

            # Send notification
            if self.notification_service:
                await self._send_reload_notification(
                    wallet_id=wallet_id,
                    user_id=wallet_doc.get("user_id"),
                    amount=reload_amount,
                    success=result["success"],
                    details=result
                )

            return result

        except Exception as e:
            self.logger.error(f"Error checking/reloading wallet {wallet_id}: {e}")
            return {
                "success": False,
                "reason": "error",
                "message": str(e)
            }

    async def _check_safety_limits(self, wallet_id: str) -> bool:
        """
        Check if wallet hasn't exceeded safety limits for auto-reload.

        Args:
            wallet_id: Wallet ID

        Returns:
            True if within safety limits, False otherwise
        """
        # Check reloads in last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_reloads = await self.auto_reload_logs_collection.count_documents({
            "wallet_id": wallet_id,
            "created_at": {"$gte": yesterday},
            "success": True
        })

        if recent_reloads >= self.MAX_RELOADS_PER_DAY:
            self.logger.warning(
                f"Wallet {wallet_id} exceeded daily reload limit: {recent_reloads}/{self.MAX_RELOADS_PER_DAY}"
            )
            return False

        # Check minimum interval between reloads
        min_interval_ago = datetime.utcnow() - timedelta(hours=self.MIN_RELOAD_INTERVAL_HOURS)
        last_reload = await self.auto_reload_logs_collection.find_one(
            {
                "wallet_id": wallet_id,
                "created_at": {"$gte": min_interval_ago},
                "success": True
            },
            sort=[("created_at", -1)]
        )

        if last_reload:
            self.logger.warning(
                f"Wallet {wallet_id} reloaded too recently: {last_reload.get('created_at')}"
            )
            return False

        return True

    async def _process_reload(
        self,
        wallet_id: str,
        amount: Decimal,
        payment_method: Dict[str, Any],
        triggered_by: str = "auto_reload"
    ) -> Dict[str, Any]:
        """
        Process the actual reload transaction.

        Args:
            wallet_id: Wallet ID
            amount: Amount to reload
            payment_method: Payment method document
            triggered_by: Trigger source

        Returns:
            Dictionary with reload result
        """
        try:
            provider = payment_method.get("provider", "unknown")
            provider_payment_method_id = payment_method.get("provider_payment_method_id")

            # Use wallet service to process payment
            # This will use the appropriate provider to charge the saved payment method
            result = await self.wallet_service.charge_saved_payment_method(
                wallet_id=wallet_id,
                amount=amount,
                payment_method_id=str(payment_method["_id"]),
                description=f"Auto-reload: {amount}",
                metadata={
                    "triggered_by": triggered_by,
                    "auto_reload": True
                }
            )

            return {
                "success": result.get("success", False),
                "transaction_id": result.get("transaction_id"),
                "provider": provider,
                "amount": str(amount),
                "reason": "auto_reload_triggered",
                "details": result
            }

        except Exception as e:
            self.logger.error(f"Error processing reload for wallet {wallet_id}: {e}")
            return {
                "success": False,
                "reason": "processing_error",
                "message": str(e)
            }

    async def _log_reload_attempt(
        self,
        wallet_id: str,
        amount: Decimal,
        success: bool,
        details: Dict[str, Any]
    ):
        """
        Log auto-reload attempt.

        Args:
            wallet_id: Wallet ID
            amount: Reload amount
            success: Whether reload succeeded
            details: Additional details
        """
        log_entry = {
            "wallet_id": wallet_id,
            "amount": float(amount),
            "success": success,
            "details": details,
            "created_at": datetime.utcnow()
        }

        await self.auto_reload_logs_collection.insert_one(log_entry)

    async def _send_reload_notification(
        self,
        wallet_id: str,
        user_id: str,
        amount: Decimal,
        success: bool,
        details: Dict[str, Any]
    ):
        """
        Send notification about auto-reload.

        Args:
            wallet_id: Wallet ID
            user_id: User ID
            amount: Reload amount
            success: Whether reload succeeded
            details: Additional details
        """
        if not self.notification_service:
            return

        try:
            if success:
                # Success notification
                await self.notification_service.send_email(
                    to_email=user_id,  # Assuming user_id is email or will be resolved
                    subject="Wallet Auto-Reload Successful",
                    template="auto_reload_success",
                    context={
                        "amount": str(amount),
                        "wallet_id": wallet_id,
                        "transaction_id": details.get("transaction_id"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            else:
                # Failure notification
                await self.notification_service.send_email(
                    to_email=user_id,
                    subject="Wallet Auto-Reload Failed",
                    template="auto_reload_failed",
                    context={
                        "amount": str(amount),
                        "wallet_id": wallet_id,
                        "reason": details.get("reason", "Unknown"),
                        "message": details.get("message", "Please reload manually"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

        except Exception as e:
            self.logger.error(f"Error sending reload notification: {e}")

    async def check_all_wallets(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check all wallets for auto-reload needs.

        Typically called by a scheduled job (cron).

        Args:
            tenant_id: Optional tenant filter

        Returns:
            Dictionary with summary of reload attempts
        """
        query = {
            "auto_reload_enabled": True,
            "is_active": True
        }
        if tenant_id:
            query["tenant_id"] = tenant_id

        wallets = await self.wallets_collection.find(query).to_list(None)

        summary = {
            "checked": len(wallets),
            "reloaded": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }

        self.logger.info(f"Checking {len(wallets)} wallets for auto-reload")

        for wallet in wallets:
            wallet_id = str(wallet["_id"])

            result = await self.check_and_reload_wallet(wallet_id)

            if result is None:
                summary["skipped"] += 1
            elif result.get("success"):
                summary["reloaded"] += 1
            else:
                summary["failed"] += 1
                summary["errors"].append({
                    "wallet_id": wallet_id,
                    "reason": result.get("reason"),
                    "message": result.get("message")
                })

        self.logger.info(
            f"Auto-reload check complete: {summary['reloaded']} reloaded, "
            f"{summary['failed']} failed, {summary['skipped']} skipped"
        )

        return summary

    async def enable_auto_reload(
        self,
        wallet_id: str,
        threshold: Decimal,
        reload_amount: Decimal,
        payment_method_id: str
    ) -> bool:
        """
        Enable auto-reload for a wallet.

        Args:
            wallet_id: Wallet ID
            threshold: Balance threshold to trigger reload
            reload_amount: Amount to reload
            payment_method_id: Payment method to use

        Returns:
            True if enabled successfully
        """
        try:
            # Validate payment method exists and is active
            payment_method = await self.payment_methods_collection.find_one({
                "_id": payment_method_id,
                "wallet_id": wallet_id,
                "is_active": True
            })

            if not payment_method:
                self.logger.error(f"Invalid payment method: {payment_method_id}")
                return False

            # Update wallet
            result = await self.wallets_collection.update_one(
                {"_id": wallet_id},
                {
                    "$set": {
                        "auto_reload_enabled": True,
                        "auto_reload_threshold": float(threshold),
                        "auto_reload_amount": float(reload_amount),
                        "auto_reload_payment_method_id": payment_method_id,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            if result.modified_count > 0:
                self.logger.info(f"Auto-reload enabled for wallet {wallet_id}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error enabling auto-reload for wallet {wallet_id}: {e}")
            return False

    async def disable_auto_reload(self, wallet_id: str) -> bool:
        """
        Disable auto-reload for a wallet.

        Args:
            wallet_id: Wallet ID

        Returns:
            True if disabled successfully
        """
        try:
            result = await self.wallets_collection.update_one(
                {"_id": wallet_id},
                {
                    "$set": {
                        "auto_reload_enabled": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            if result.modified_count > 0:
                self.logger.info(f"Auto-reload disabled for wallet {wallet_id}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error disabling auto-reload for wallet {wallet_id}: {e}")
            return False
