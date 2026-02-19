"""
Billing Sync Scheduled Task

Automatically syncs VAPI automation calls and creates billing records.
Runs daily at midnight UTC to ensure all calls are billed.

Author: KasaAI Team
Date: 2025-10-30
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from bson import ObjectId

logger = logging.getLogger(__name__)


async def sync_and_bill_all_automations() -> Dict[str, Any]:
    """
    Daily task to sync calls from VAPI and create billing records.

    This task:
    1. Finds all active automations with organization IDs
    2. Syncs call data from VAPI for each automation
    3. Creates billing records for new calls
    4. Logs summary of billing created

    Run schedule: Daily at 00:00 UTC

    Returns:
        Summary of sync and billing results
    """
    try:
        logger.info("=" * 80)
        logger.info("🔄 Starting automated billing sync task")
        logger.info(f"⏰ Task started at: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 80)

        # Import here to avoid circular imports
        from ..database import get_database
        from ..services.automation_analytics_service import get_analytics_service
        from apps.shared.services.billing_service import get_billing_service

        db = get_database()
        analytics_service = await get_analytics_service(db)
        billing_service = get_billing_service(db)

        # Get all active automations with organization links
        configs = await db.automation_configs.find({
            "status": "active",
            "organization_id": {"$exists": True, "$ne": None}
        }).to_list(length=None)

        logger.info(f"📋 Found {len(configs)} active automations to process")

        # Track overall results
        total_calls_synced = 0
        total_billing_records_created = 0
        total_amount_billed = 0.0
        automation_results: List[Dict[str, Any]] = []
        errors: List[Dict[str, str]] = []

        # Process each automation
        for config in configs:
            config_id = str(config["_id"])
            automation_name = config.get("automation_name", "Unknown")
            organization_id = config.get("organization_id")

            try:
                logger.info(f"\n{'─' * 60}")
                logger.info(f"🤖 Processing: {automation_name} (ID: {config_id})")
                logger.info(f"🏢 Organization: {organization_id}")

                # Step 1: Sync calls from VAPI
                sync_result = await analytics_service.sync_automation_calls(config_id)

                if not sync_result.get("success"):
                    error_msg = sync_result.get("error", "Unknown error")
                    logger.warning(f"⚠️  Sync failed for {automation_name}: {error_msg}")
                    errors.append({
                        "automation_id": config_id,
                        "automation_name": automation_name,
                        "step": "sync",
                        "error": error_msg
                    })
                    continue

                calls_synced = sync_result.get("calls_synced", 0)
                total_calls_synced += calls_synced
                logger.info(f"✅ Synced {calls_synced} calls from VAPI")

                # Step 2: Create billing records for new calls
                billing_result = await billing_service.create_billing_records_for_automation(config_id)

                if not billing_result.get("success"):
                    error_msg = billing_result.get("error", "Unknown error")
                    logger.warning(f"⚠️  Billing failed for {automation_name}: {error_msg}")
                    errors.append({
                        "automation_id": config_id,
                        "automation_name": automation_name,
                        "step": "billing",
                        "error": error_msg
                    })
                    continue

                records_created = billing_result.get("billing_records_created", 0)
                records_skipped = billing_result.get("billing_records_skipped", 0)
                amount = billing_result.get("total_amount", 0.0)

                total_billing_records_created += records_created
                total_amount_billed += amount

                logger.info(f"💰 Created {records_created} billing records (${amount:.4f})")
                if records_skipped > 0:
                    logger.info(f"⏭️  Skipped {records_skipped} records (duplicates or zero-cost)")

                automation_results.append({
                    "automation_id": config_id,
                    "automation_name": automation_name,
                    "organization_id": organization_id,
                    "calls_synced": calls_synced,
                    "billing_records_created": records_created,
                    "billing_records_skipped": records_skipped,
                    "amount_billed": round(amount, 4)
                })

            except Exception as e:
                logger.error(f"❌ Error processing {automation_name}: {e}", exc_info=True)
                errors.append({
                    "automation_id": config_id,
                    "automation_name": automation_name,
                    "step": "unknown",
                    "error": str(e)
                })

        # Log final summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 BILLING SYNC SUMMARY")
        logger.info("=" * 80)
        logger.info(f"✅ Automations processed: {len(configs)}")
        logger.info(f"✅ Automations successful: {len(automation_results)}")
        logger.info(f"⚠️  Automations with errors: {len(errors)}")
        logger.info(f"📞 Total calls synced: {total_calls_synced}")
        logger.info(f"📝 Total billing records created: {total_billing_records_created}")
        logger.info(f"💵 Total amount billed: ${total_amount_billed:.4f}")
        logger.info(f"⏰ Task completed at: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 80)

        # Log errors if any
        if errors:
            logger.warning("\n⚠️  ERRORS ENCOUNTERED:")
            for error in errors:
                logger.warning(
                    f"  - {error['automation_name']} ({error['step']}): {error['error']}"
                )

        return {
            "success": True,
            "task_name": "billing_sync",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "automations_processed": len(configs),
                "automations_successful": len(automation_results),
                "automations_with_errors": len(errors),
                "total_calls_synced": total_calls_synced,
                "total_billing_records_created": total_billing_records_created,
                "total_amount_billed": round(total_amount_billed, 4)
            },
            "results": automation_results,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"❌ Billing sync task failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "completed_at": datetime.now(timezone.utc).isoformat()
        }


def sync_and_bill_all_automations_sync():
    """
    Synchronous wrapper for the async billing sync task.

    APScheduler requires synchronous functions, so this wrapper
    creates an event loop and runs the async function.
    """
    try:
        # Create new event loop for this task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the async task
        result = loop.run_until_complete(sync_and_bill_all_automations())

        # Close the loop
        loop.close()

        return result

    except Exception as e:
        logger.error(f"❌ Error in sync wrapper: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
