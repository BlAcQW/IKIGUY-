"""
Wallet Auto-Reload Task

Automatically tops up wallets when balance falls below configured threshold.
Runs every 5 minutes to check all wallets with auto_reload_enabled.

Author: KasaAI Team
Date: 2025-10-30
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from decimal import Decimal
from bson import ObjectId

logger = logging.getLogger(__name__)


async def check_and_reload_wallets() -> Dict[str, Any]:
    """
    Check all wallets with auto-reload enabled and trigger top-up if needed.

    This task:
    1. Finds all active wallets with auto_reload_enabled=True
    2. Checks if balance <= auto_reload_threshold
    3. Triggers automatic deposit using saved payment method
    4. Sends notifications on success/failure
    5. Logs all auto-reload attempts

    Run schedule: Every 5 minutes

    Returns:
        Summary of auto-reload results
    """
    try:
        logger.info("=" * 80)
        logger.info("🔄 Starting wallet auto-reload check")
        logger.info(f"⏰ Task started at: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 80)

        # Import here to avoid circular imports
        from ..database import get_database

        db = get_database()

        # Find all active wallets with auto-reload enabled
        wallets_needing_reload = await db.wallets.find({
            "status": "active",
            "auto_reload_enabled": True,
            "auto_reload_payment_method_id": {"$exists": True, "$ne": None},
            "$expr": {"$lte": ["$balance", "$auto_reload_threshold"]}
        }).to_list(length=None)

        logger.info(f"📋 Found {len(wallets_needing_reload)} wallets needing reload")

        # Track results
        total_wallets_checked = len(wallets_needing_reload)
        successful_reloads = 0
        failed_reloads = 0
        total_amount_reloaded = Decimal('0.00')
        reload_results: List[Dict[str, Any]] = []
        errors: List[Dict[str, str]] = []

        # Process each wallet
        for wallet_doc in wallets_needing_reload:
            wallet_id = wallet_doc.get("id")
            user_id = wallet_doc.get("user_id")
            current_balance = Decimal(str(wallet_doc.get("balance", 0)))
            threshold = Decimal(str(wallet_doc.get("auto_reload_threshold", 0)))
            reload_amount = Decimal(str(wallet_doc.get("auto_reload_amount", 0)))
            payment_method_id = wallet_doc.get("auto_reload_payment_method_id")
            currency = wallet_doc.get("currency", "USD")

            try:
                logger.info(f"\n{'─' * 60}")
                logger.info(f"💰 Processing wallet: {wallet_id}")
                logger.info(f"👤 User: {user_id}")
                logger.info(f"💵 Current balance: {current_balance} {currency}")
                logger.info(f"⚠️  Threshold: {threshold} {currency}")
                logger.info(f"🔄 Reload amount: {reload_amount} {currency}")

                # Validate reload amount
                if reload_amount <= 0:
                    logger.warning(f"⚠️  Invalid reload amount: {reload_amount}. Skipping.")
                    errors.append({
                        "wallet_id": wallet_id,
                        "user_id": user_id,
                        "error": f"Invalid reload amount: {reload_amount}"
                    })
                    failed_reloads += 1
                    continue

                # Get payment method details
                payment_method = await db.payment_methods.find_one({
                    "id": payment_method_id,
                    "user_id": user_id,
                    "is_active": True
                })

                if not payment_method:
                    logger.warning(f"⚠️  Payment method {payment_method_id} not found or inactive")
                    errors.append({
                        "wallet_id": wallet_id,
                        "user_id": user_id,
                        "error": f"Payment method {payment_method_id} not found or inactive"
                    })
                    failed_reloads += 1

                    # Disable auto-reload if payment method is missing
                    await db.wallets.update_one(
                        {"id": wallet_id},
                        {
                            "$set": {
                                "auto_reload_enabled": False,
                                "updated_at": datetime.now(timezone.utc)
                            }
                        }
                    )
                    logger.info(f"⚠️  Disabled auto-reload for wallet {wallet_id} due to missing payment method")
                    continue

                provider = payment_method.get("provider")
                logger.info(f"💳 Payment method: {provider} ({payment_method.get('display_name')})")

                # Import wallet service
                try:
                    from apps.shared.integration.wallet.wallet_service import WalletService
                    from apps.shared.integration.wallet.models import (
                        DepositRequest,
                        PaymentProvider,
                        Currency as WalletCurrency
                    )

                    # Initialize wallet service
                    wallet_service = WalletService(db)

                    # Register providers (simplified - in production, providers should be pre-registered)
                    # For now, we'll rely on the wallet service to handle provider routing

                    # Create deposit request
                    deposit_request = DepositRequest(
                        wallet_id=wallet_id,
                        amount=reload_amount,
                        currency=WalletCurrency(currency),
                        payment_provider=PaymentProvider(provider),
                        payment_method_id=payment_method_id,
                        description=f"Auto-reload: Balance fell below {threshold} {currency}",
                        idempotency_key=f"auto-reload-{wallet_id}-{datetime.now(timezone.utc).timestamp()}"
                    )

                    # Initiate deposit
                    result = await wallet_service.deposit(
                        wallet_id=wallet_id,
                        amount=reload_amount,
                        payment_provider=PaymentProvider(provider),
                        payment_method_id=payment_method_id,
                        description=deposit_request.description,
                        idempotency_key=deposit_request.idempotency_key
                    )

                    logger.info(f"✅ Auto-reload initiated: Transaction {result.id}")
                    logger.info(f"💰 Amount: {reload_amount} {currency}")
                    logger.info(f"📊 Status: {result.status}")

                    successful_reloads += 1
                    total_amount_reloaded += reload_amount

                    reload_results.append({
                        "wallet_id": wallet_id,
                        "user_id": user_id,
                        "transaction_id": result.id,
                        "amount": float(reload_amount),
                        "currency": currency,
                        "status": result.status,
                        "balance_before": float(current_balance),
                        "payment_method": payment_method.get("display_name")
                    })

                    # Send notification (if notification service available)
                    try:
                        from apps.shared.integration.wallet.notification_service import NotificationService
                        notification_service = NotificationService(db)

                        await notification_service.send_auto_reload_notification(
                            user_id=user_id,
                            wallet_id=wallet_id,
                            amount=reload_amount,
                            currency=currency,
                            transaction_id=result.id
                        )
                        logger.info(f"📧 Notification sent to user {user_id}")
                    except Exception as notif_error:
                        logger.warning(f"⚠️  Failed to send notification: {notif_error}")

                except ImportError as import_error:
                    logger.error(f"❌ Failed to import wallet service: {import_error}")
                    errors.append({
                        "wallet_id": wallet_id,
                        "user_id": user_id,
                        "error": f"Wallet service import error: {str(import_error)}"
                    })
                    failed_reloads += 1
                    continue

            except Exception as e:
                logger.error(f"❌ Error processing wallet {wallet_id}: {e}", exc_info=True)
                errors.append({
                    "wallet_id": wallet_id,
                    "user_id": user_id,
                    "error": str(e)
                })
                failed_reloads += 1

        # Log final summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 AUTO-RELOAD SUMMARY")
        logger.info("=" * 80)
        logger.info(f"✅ Wallets checked: {total_wallets_checked}")
        logger.info(f"✅ Successful reloads: {successful_reloads}")
        logger.info(f"⚠️  Failed reloads: {failed_reloads}")
        logger.info(f"💵 Total amount reloaded: {total_amount_reloaded}")
        logger.info(f"⏰ Task completed at: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 80)

        # Log errors if any
        if errors:
            logger.warning("\n⚠️  ERRORS ENCOUNTERED:")
            for error in errors:
                logger.warning(
                    f"  - Wallet {error['wallet_id']} ({error.get('user_id', 'unknown')}): {error['error']}"
                )

        return {
            "success": True,
            "task_name": "wallet_auto_reload",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "wallets_checked": total_wallets_checked,
                "successful_reloads": successful_reloads,
                "failed_reloads": failed_reloads,
                "total_amount_reloaded": float(total_amount_reloaded)
            },
            "results": reload_results,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"❌ Auto-reload task failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "completed_at": datetime.now(timezone.utc).isoformat()
        }


def check_and_reload_wallets_sync():
    """
    Synchronous wrapper for the async auto-reload task.

    APScheduler requires synchronous functions, so this wrapper
    creates an event loop and runs the async function.
    """
    try:
        # Create new event loop for this task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the async task
        result = loop.run_until_complete(check_and_reload_wallets())

        # Close the loop
        loop.close()

        return result

    except Exception as e:
        logger.error(f"❌ Error in auto-reload wrapper: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
