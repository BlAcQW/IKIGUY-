#!/usr/bin/env python3
"""
Backfill missing cost and ended_reason data from VAPI API.

This script:
1. Finds all calls with missing or zero cost/ended_reason
2. Fetches complete call data from VAPI API
3. Updates database with cost, ended_reason, and other missing fields

Run: python3 scripts/backfill_vapi_data.py [--dry-run] [--limit N] [--rate-limit N]
"""
import asyncio
import argparse
import sys
import httpx
import os
from datetime import datetime
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


async def fetch_call_from_vapi(call_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch complete call data from VAPI API.

    Args:
        call_id: VAPI call ID

    Returns:
        Call data dict or None if fetch fails
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{VAPI_API_URL}/{call_id}",
                headers={"Authorization": f"Bearer {VAPI_API_KEY}"}
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None  # Call not found in VAPI
            else:
                print(f"⚠️  VAPI API error {response.status_code} for {call_id}")
                return None
    except Exception as e:
        print(f"⚠️  Failed to fetch {call_id} from VAPI: {e}")
        return None


async def backfill_vapi_data(
    dry_run: bool = False,
    limit: Optional[int] = None,
    rate_limit: int = 10
):
    """
    Backfill missing cost and ended_reason data from VAPI API.

    Args:
        dry_run: If True, only print what would be done without updating DB
        limit: Maximum number of records to process (None = all)
        rate_limit: Max requests per second to VAPI API
    """
    collection = get_collection("automation_calls")

    # Find calls that need backfilling:
    # - Missing ended_reason (ended_reason is null or missing)
    # - OR cost is 0 but duration > 0 (likely missing cost data)
    query = {
        "$or": [
            {"ended_reason": None},
            {"ended_reason": {"$exists": False}},
            {"vapi_cost": 0, "duration": {"$gt": 0}}
        ],
        "ended_at": {"$exists": True, "$ne": None}  # Only completed calls
    }

    # Count total records matching criteria
    total_count = await collection.count_documents(query)
    print(f"\n📊 Found {total_count} calls needing backfill from VAPI API")

    if total_count == 0:
        print("✅ No records need backfilling!")
        return

    # Apply limit if specified
    cursor_limit = limit if limit else total_count
    print(f"🔄 Processing {cursor_limit} records{'...' if limit and limit < total_count else ''}")
    print(f"⏱️  Rate limit: {rate_limit} requests/second")

    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    else:
        print("✏️  LIVE MODE - Database will be updated\n")

    # Process records
    cursor = collection.find(query).limit(cursor_limit)

    updated_count = 0
    failed_count = 0
    skipped_count = 0
    not_found_count = 0

    # Rate limiting
    request_interval = 1.0 / rate_limit

    async for record in cursor:
        call_id = record.get("call_id", "unknown")
        current_cost = record.get("vapi_cost", 0)
        current_reason = record.get("ended_reason")
        current_duration = record.get("duration", 0)

        # Fetch from VAPI API
        vapi_data = await fetch_call_from_vapi(call_id)

        if vapi_data is None:
            not_found_count += 1
            continue

        # Extract data from VAPI response
        updates = {}

        # Get cost
        vapi_cost = vapi_data.get("cost", 0)
        if vapi_cost != current_cost:
            updates["vapi_cost"] = vapi_cost

        # Get ended_reason
        ended_reason = vapi_data.get("endedReason")
        if ended_reason and ended_reason != current_reason:
            updates["ended_reason"] = ended_reason

        # Get timestamps (in case they're missing or incorrect)
        started_at = vapi_data.get("startedAt")
        ended_at = vapi_data.get("endedAt")
        if started_at:
            updates["started_at"] = started_at
        if ended_at:
            updates["ended_at"] = ended_at

        # Skip if no updates needed
        if not updates:
            skipped_count += 1
            continue

        # Update record
        if dry_run:
            update_summary = ", ".join([f"{k}={v}" for k, v in updates.items()])
            print(f"   {call_id}: Would update {update_summary}")
        else:
            try:
                result = await collection.update_one(
                    {"_id": record["_id"]},
                    {"$set": updates}
                )

                if result.modified_count > 0:
                    update_summary = ", ".join([f"{k}={v}" for k, v in updates.items()])
                    print(f"✅ {call_id}: Updated {update_summary}")
                    updated_count += 1
                else:
                    print(f"⚠️  {call_id}: No changes made")
                    skipped_count += 1
            except Exception as e:
                print(f"❌ {call_id}: Failed to update - {e}")
                failed_count += 1

        # Rate limiting
        await asyncio.sleep(request_interval)

    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"Total records processed: {cursor_limit}")
    print(f"✅ Successfully updated: {updated_count}")
    print(f"⚠️  Skipped (no changes): {skipped_count}")
    print(f"🔍 Not found in VAPI: {not_found_count}")
    print(f"❌ Failed: {failed_count}")

    if dry_run:
        print(f"\n💡 This was a dry run. Use without --dry-run to apply changes.")
    else:
        print(f"\n✅ Database updated successfully!")

    # Verify results
    remaining_nulls = await collection.count_documents({
        "$or": [
            {"ended_reason": None},
            {"ended_reason": {"$exists": False}}
        ]
    })
    remaining_zero_cost = await collection.count_documents({
        "vapi_cost": 0,
        "duration": {"$gt": 0}
    })
    print(f"\n📊 Remaining calls with ended_reason=null: {remaining_nulls}")
    print(f"📊 Remaining calls with cost=0 but duration>0: {remaining_zero_cost}")


async def main():
    """Parse arguments and run backfill."""
    parser = argparse.ArgumentParser(
        description="Backfill cost and ended_reason from VAPI API"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of records to process (default: all)"
    )
    parser.add_argument(
        "--rate-limit",
        type=int,
        default=10,
        help="Max requests per second to VAPI API (default: 10)"
    )

    args = parser.parse_args()

    if not VAPI_API_KEY:
        print("❌ Error: VAPI_API_KEY not configured")
        sys.exit(1)

    try:
        await backfill_vapi_data(
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
