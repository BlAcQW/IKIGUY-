#!/usr/bin/env python3
"""
Sync VAPI call status for stuck campaign calls.
This script checks VAPI for the actual status of calls that are stuck in "calling" status
and updates the database accordingly.
"""

import asyncio
import httpx
import os
import sys
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/opt/kasaai/.env')

MONGODB_URL = os.getenv('MONGODB_URI', 'mongodb://admin:aawwER4444%@127.0.0.1:27017/kasaai_core?authSource=admin')
VAPI_API_KEY = os.getenv('VAPI_API_KEY', '')
VAPI_BASE_URL = "https://api.vapi.ai"

async def get_vapi_call_status(call_id: str, api_key: str) -> dict:
    """Get call status from VAPI API."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{VAPI_BASE_URL}/call/{call_id}",
                headers={"Authorization": f"Bearer {api_key}"}
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"error": "not_found", "message": "Call not found in VAPI"}
            else:
                return {"error": "api_error", "message": f"VAPI API error: {response.status_code}"}
    except Exception as e:
        return {"error": "exception", "message": str(e)}

async def sync_campaign_calls(campaign_id: str, dry_run: bool = True):
    """Sync stuck campaign calls with VAPI."""

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.kasaai_core

    print(f"Syncing calls for campaign: {campaign_id}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}\n")

    # Find stuck calls
    stuck_calls = await db.campaign_calls.find({
        "campaign_id": campaign_id,
        "status": "calling"
    }).to_list(length=None)

    print(f"Found {len(stuck_calls)} calls stuck in 'calling' status\n")

    if not stuck_calls:
        print("No stuck calls to sync!")
        return

    updates = {
        "completed": 0,
        "failed": 0,
        "no_answer": 0,
        "not_found": 0,
        "errors": 0
    }

    for i, call in enumerate(stuck_calls, 1):
        call_id = call.get('call_id')
        contact_index = call.get('contact_index', '?')
        phone = call.get('contact', {}).get('phone', 'Unknown')

        print(f"[{i}/{len(stuck_calls)}] Checking call {contact_index}: {phone}")
        print(f"  Call ID: {call_id}")

        if not call_id:
            print("  ⚠️  No call_id found, marking as failed")
            updates["failed"] += 1

            if not dry_run:
                await db.campaign_calls.update_one(
                    {"_id": call["_id"]},
                    {
                        "$set": {
                            "status": "failed",
                            "error_message": "No call_id found - call was not triggered",
                            "completed_at": datetime.now(timezone.utc)
                        }
                    }
                )
            continue

        # Check VAPI
        vapi_data = await get_vapi_call_status(call_id, VAPI_API_KEY)

        if vapi_data.get("error"):
            error_type = vapi_data["error"]
            error_msg = vapi_data["message"]
            print(f"  ❌ Error: {error_type} - {error_msg}")

            if error_type == "not_found":
                updates["not_found"] += 1
                # Call not found in VAPI, likely failed to trigger properly
                if not dry_run:
                    await db.campaign_calls.update_one(
                        {"_id": call["_id"]},
                        {
                            "$set": {
                                "status": "failed",
                                "error_message": "Call not found in VAPI system",
                                "completed_at": datetime.now(timezone.utc)
                            }
                        }
                    )
            else:
                updates["errors"] += 1
        else:
            # Got VAPI data, extract status
            vapi_status = vapi_data.get("status", "unknown")
            vapi_ended_reason = vapi_data.get("endedReason")
            duration = vapi_data.get("duration", 0)
            cost = vapi_data.get("cost", 0)

            print(f"  ✓ VAPI Status: {vapi_status}")
            if vapi_ended_reason:
                print(f"    Ended Reason: {vapi_ended_reason}")
            print(f"    Duration: {duration}s, Cost: ${cost:.4f}")

            # Map VAPI status to our status
            if vapi_status in ["ended", "completed"]:
                our_status = "completed"
                updates["completed"] += 1
            elif vapi_status in ["failed", "error"]:
                our_status = "failed"
                updates["failed"] += 1
            elif vapi_ended_reason == "voicemail":
                our_status = "no_answer"
                updates["no_answer"] += 1
            elif vapi_status in ["no-answer", "busy"]:
                our_status = "no_answer"
                updates["no_answer"] += 1
            else:
                our_status = "failed"
                updates["failed"] += 1

            if not dry_run:
                await db.campaign_calls.update_one(
                    {"_id": call["_id"]},
                    {
                        "$set": {
                            "status": our_status,
                            "duration": duration,
                            "cost": cost,
                            "completed_at": datetime.now(timezone.utc)
                        }
                    }
                )

        print()  # Blank line between calls

    # Summary
    print("\n" + "="*60)
    print("SYNC SUMMARY")
    print("="*60)
    print(f"Total calls processed: {len(stuck_calls)}")
    print(f"Completed: {updates['completed']}")
    print(f"Failed: {updates['failed']}")
    print(f"No Answer: {updates['no_answer']}")
    print(f"Not Found in VAPI: {updates['not_found']}")
    print(f"API Errors: {updates['errors']}")

    if dry_run:
        print("\n⚠️  DRY RUN - No changes were made to the database")
        print("Run with --apply to actually update the database")
    else:
        print("\n✅ Database updated successfully")

        # Update campaign progress
        print("\nUpdating campaign progress counters...")
        campaign = await db.automation_campaigns.find_one({"_id": campaign_id})
        if campaign:
            all_calls = await db.campaign_calls.find({"campaign_id": campaign_id}).to_list(length=None)

            progress_updates = {
                "progress.called": len(all_calls),
                "progress.completed": len([c for c in all_calls if c.get("completed_at")]),
                "progress.failed": len([c for c in all_calls if c.get("status") == "failed"]),
                "progress.successful": len([c for c in all_calls if c.get("status") == "completed"]),
                "progress.no_answer": len([c for c in all_calls if c.get("status") == "no_answer"]),
                "updated_at": datetime.now(timezone.utc)
            }

            await db.automation_campaigns.update_one(
                {"_id": campaign_id},
                {"$set": progress_updates}
            )

            print(f"Campaign progress updated: {progress_updates['progress.called']} calls, "
                  f"{progress_updates['progress.completed']} completed, "
                  f"{progress_updates['progress.failed']} failed")

    client.close()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sync VAPI call status for campaign calls")
    parser.add_argument("campaign_id", help="Campaign ID to sync")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry run)")

    args = parser.parse_args()

    asyncio.run(sync_campaign_calls(args.campaign_id, dry_run=not args.apply))
