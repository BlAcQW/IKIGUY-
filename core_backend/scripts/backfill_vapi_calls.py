#!/usr/bin/env python3
"""
Backfill missing data in vapi_calls collection.

This script:
1. Finds vapi_calls records with missing duration, cost, ended_reason, status
2. First tries to get data from automation_calls (which has backfilled data)
3. Falls back to VAPI API if not in automation_calls
4. Updates vapi_calls with complete data

Run: python3 scripts/backfill_vapi_calls.py [--dry-run] [--limit N] [--rate-limit N]
"""
import asyncio
import argparse
import sys
import httpx
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.mongo import get_collection

# VAPI API configuration
VAPI_API_URL = "https://api.vapi.ai/call"
VAPI_API_KEY = os.getenv("VAPI_API_KEY")


async def fetch_from_vapi_api(call_id: str) -> Optional[Dict[str, Any]]:
    """Fetch call data from VAPI API."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{VAPI_API_URL}/{call_id}",
                headers={"Authorization": f"Bearer {VAPI_API_KEY}"}
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                return None
    except Exception:
        return None


async def backfill_vapi_calls(
    dry_run: bool = False,
    limit: Optional[int] = None,
    rate_limit: int = 10
):
    """
    Backfill missing data in vapi_calls collection.
    """
    vapi_collection = get_collection("vapi_calls")
    automation_collection = get_collection("automation_calls")

    # Find vapi_calls with missing data
    query = {
        "$or": [
            {"duration": {"$exists": False}},
            {"duration": None},
            {"duration": 0},
            {"cost": {"$exists": False}},
            {"cost": None},
            {"ended_reason": {"$exists": False}},
            {"ended_reason": None},
            {"status": {"$exists": False}},
            {"status": None}
        ],
        "call_id": {"$exists": True, "$ne": None, "$ne": ""}
    }

    total_count = await vapi_collection.count_documents(query)
    print(f"\n📊 Found {total_count} vapi_calls records needing backfill")

    if total_count == 0:
        print("✅ No records need backfilling!")
        return

    cursor_limit = limit if limit else total_count
    print(f"🔄 Processing {cursor_limit} records{'...' if limit and limit < total_count else ''}")
    print(f"⏱️  Rate limit: {rate_limit} requests/second for VAPI API")

    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    else:
        print("✏️  LIVE MODE - Database will be updated\n")

    cursor = vapi_collection.find(query).limit(cursor_limit)

    updated_count = 0
    from_automation = 0
    from_vapi_api = 0
    not_found_count = 0
    skipped_count = 0

    request_interval = 1.0 / rate_limit

    async for vapi_doc in cursor:
        call_id = vapi_doc.get("call_id")

        # First, try to get data from automation_calls
        auto_doc = await automation_collection.find_one({"call_id": call_id})

        updates = {}

        if auto_doc:
            # Get data from automation_calls
            if auto_doc.get("duration") is not None:
                updates["duration"] = auto_doc["duration"]
            if auto_doc.get("vapi_cost") is not None:
                updates["cost"] = auto_doc["vapi_cost"]
            if auto_doc.get("ended_reason"):
                updates["ended_reason"] = auto_doc["ended_reason"]
            if auto_doc.get("status"):
                updates["status"] = auto_doc["status"]
            if auto_doc.get("started_at"):
                updates["started_at"] = auto_doc["started_at"]
            if auto_doc.get("ended_at"):
                updates["ended_at"] = auto_doc["ended_at"]
            if auto_doc.get("assistant_id"):
                updates["assistant_id"] = auto_doc["assistant_id"]

            if updates:
                from_automation += 1
                source = "automation_calls"
        else:
            # Fall back to VAPI API
            vapi_data = await fetch_from_vapi_api(call_id)

            if vapi_data:
                # Calculate duration from timestamps
                started_at = vapi_data.get("startedAt")
                ended_at = vapi_data.get("endedAt")

                if started_at and ended_at:
                    try:
                        from dateutil import parser
                        start = parser.parse(started_at) if isinstance(started_at, str) else started_at
                        end = parser.parse(ended_at) if isinstance(ended_at, str) else ended_at
                        updates["duration"] = int((end - start).total_seconds())
                    except:
                        pass

                if vapi_data.get("cost") is not None:
                    updates["cost"] = vapi_data["cost"]
                if vapi_data.get("endedReason"):
                    updates["ended_reason"] = vapi_data["endedReason"]
                    updates["status"] = vapi_data["endedReason"]
                if started_at:
                    updates["started_at"] = started_at
                if ended_at:
                    updates["ended_at"] = ended_at
                if vapi_data.get("assistantId"):
                    updates["assistant_id"] = vapi_data["assistantId"]

                if updates:
                    from_vapi_api += 1
                    source = "VAPI API"
                    await asyncio.sleep(request_interval)  # Rate limiting
            else:
                not_found_count += 1
                continue

        # Skip if no updates
        if not updates:
            skipped_count += 1
            continue

        # Update record
        if dry_run:
            update_summary = ", ".join([f"{k}={v}" for k, v in list(updates.items())[:3]])
            if len(updates) > 3:
                update_summary += f", +{len(updates)-3} more"
            print(f"   {call_id}: Would update from {source}: {update_summary}")
        else:
            try:
                result = await vapi_collection.update_one(
                    {"call_id": call_id},
                    {"$set": updates}
                )

                if result.modified_count > 0:
                    update_summary = ", ".join([f"{k}" for k in list(updates.keys())[:3]])
                    if len(updates) > 3:
                        update_summary += f", +{len(updates)-3} more"
                    print(f"✅ {call_id}: Updated from {source}: {update_summary}")
                    updated_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                print(f"❌ {call_id}: Failed - {e}")

    # Summary
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"Total processed: {cursor_limit}")
    print(f"✅ Successfully updated: {updated_count}")
    print(f"   - From automation_calls: {from_automation}")
    print(f"   - From VAPI API: {from_vapi_api}")
    print(f"⚠️  Skipped: {skipped_count}")
    print(f"🔍 Not found: {not_found_count}")

    if dry_run:
        print(f"\n💡 This was a dry run. Use without --dry-run to apply changes.")
    else:
        print(f"\n✅ Database updated successfully!")

    # Verify
    vapi_with_duration = await vapi_collection.count_documents({"duration": {"$gt": 0}})
    vapi_with_cost = await vapi_collection.count_documents({"cost": {"$gt": 0}})
    vapi_with_ended_reason = await vapi_collection.count_documents({"ended_reason": {"$exists": True, "$ne": None}})

    print(f"\n📊 vapi_calls after backfill:")
    print(f"  With duration > 0: {vapi_with_duration}")
    print(f"  With cost > 0: {vapi_with_cost}")
    print(f"  With ended_reason: {vapi_with_ended_reason}")


async def main():
    """Parse arguments and run backfill."""
    parser = argparse.ArgumentParser(
        description="Backfill vapi_calls from automation_calls and VAPI API"
    )
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--limit", type=int, default=None, help="Max records to process")
    parser.add_argument("--rate-limit", type=int, default=10, help="VAPI API requests/sec")

    args = parser.parse_args()

    if not VAPI_API_KEY:
        print("❌ Error: VAPI_API_KEY not configured")
        sys.exit(1)

    try:
        await backfill_vapi_calls(
            dry_run=args.dry_run,
            limit=args.limit,
            rate_limit=args.rate_limit
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
