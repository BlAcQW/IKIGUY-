"""
Automated Affiliate Payouts Task

Automatically processes scheduled payouts for affiliates based on:
- Auto-payout settings (enabled, schedule, day)
- Balance thresholds
- Payout method preferences

Runs daily at 2 AM UTC to check for affiliates eligible for payout.

Author: KasaAI Team
Date: 2025-11-18
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def process_automated_payouts() -> Dict[str, Any]:
    """
    Process automated affiliate payouts.

    This task:
    1. Finds all active affiliates with auto_payout_enabled=True
    2. Checks if balance >= payout_threshold
    3. Verifies payout schedule matches today
    4. Creates payout requests for eligible affiliates
    5. Logs all payout attempts

    Run schedule: Daily at 2 AM UTC

    Returns:
        Summary of payout processing results
    """
    try:
        logger.info("=" * 80)
        logger.info("💰 Starting automated affiliate payout processing")
        logger.info(f"⏰ Task started at: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 80)

        # Import here to avoid circular imports
        from ..database import get_database
        from ..services.payout_scheduler import PayoutScheduler

        db = get_database()
        scheduler = PayoutScheduler(db)

        # Process scheduled payouts
        result = await scheduler.process_scheduled_payouts()

        # Log final summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 AUTOMATED PAYOUT SUMMARY")
        logger.info("=" * 80)
        logger.info(f"👥 Eligible affiliates: {result['total_eligible']}")
        logger.info(f"✅ Payouts created: {result['payouts_created']}")
        logger.info(f"⚠️  Payouts failed: {result['payouts_failed']}")
        logger.info(f"💵 Total amount: ${result['total_amount']}")
        logger.info(f"⏰ Task completed at: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 80)

        # Log errors if any
        if result['errors']:
            logger.warning("\n⚠️  ERRORS ENCOUNTERED:")
            for error in result['errors']:
                if 'fatal_error' in error:
                    logger.error(f"  - FATAL: {error['fatal_error']}")
                else:
                    logger.warning(
                        f"  - Affiliate {error.get('user_id', 'unknown')}: {error['error']}"
                    )

        return {
            "success": True,
            "task_name": "affiliate_payouts",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "eligible_affiliates": result['total_eligible'],
                "payouts_created": result['payouts_created'],
                "payouts_failed": result['payouts_failed'],
                "total_amount": float(result['total_amount'])
            },
            "errors": result['errors']
        }

    except Exception as e:
        logger.error(f"❌ Automated payout task failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "completed_at": datetime.now(timezone.utc).isoformat()
        }


def process_automated_payouts_sync():
    """
    Synchronous wrapper for the async payout task.

    APScheduler requires synchronous functions, so this wrapper
    creates an event loop and runs the async function.
    """
    try:
        # Create new event loop for this task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the async task
        result = loop.run_until_complete(process_automated_payouts())

        # Close the loop
        loop.close()

        return result

    except Exception as e:
        logger.error(f"❌ Error in payout task wrapper: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
