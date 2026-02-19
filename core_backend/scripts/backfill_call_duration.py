#!/usr/bin/env python3
"""
Backfill missing duration data in automation_calls collection.

This script:
1. Finds all calls with duration=null but having started_at and ended_at timestamps
2. Calculates duration from timestamps
3. Updates the database with calculated duration

Run: python3 scripts/backfill_call_duration.py [--dry-run] [--limit N]
"""
import asyncio
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.mongo import get_collection
from dateutil import parser


async def calculate_duration(started_at, ended_at) -> Optional[int]:
    """
    Calculate duration in seconds from timestamps.

    Args:
        started_at: Start timestamp (datetime or ISO string)
        ended_at: End timestamp (datetime or ISO string)

    Returns:
        Duration in seconds, or None if calculation fails
    """
    try:
        # Parse timestamps if they're strings
        start_time = parser.parse(started_at) if isinstance(started_at, str) else started_at
        end_time = parser.parse(ended_at) if isinstance(ended_at, str) else ended_at

        # Calculate duration
        duration = int((end_time - start_time).total_seconds())

        return duration if duration >= 0 else None
    except Exception as e:
        return None


async def backfill_durations(dry_run: bool = False, limit: Optional[int] = None):
    """
    Backfill missing duration data.

    Args:
        dry_run: If True, only print what would be done without updating DB
        limit: Maximum number of records to process (None = all)
    """
    collection = get_collection("automation_calls")

    # Find calls with duration=null OR duration=0 but having timestamps
    # Reason: Some calls were saved with duration=0 instead of null when timestamps exist
    query = {
        "$or": [
            {"duration": None},
            {"duration": 0}
        ],
        "started_at": {"$exists": True, "$ne": None},
        "ended_at": {"$exists": True, "$ne": None}
    }

    # Count total records matching criteria
    total_count = await collection.count_documents(query)
    print(f"\n📊 Found {total_count} calls with duration=null or duration=0 but having timestamps")

    if total_count == 0:
        print("✅ No records need backfilling!")
        return

    # Apply limit if specified
    cursor_limit = limit if limit else total_count
    print(f"🔄 Processing {cursor_limit} records{'...' if limit and limit < total_count else ''}")

    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    else:
        print("✏️  LIVE MODE - Database will be updated\n")

    # Process records
    cursor = collection.find(query).limit(cursor_limit)

    updated_count = 0
    failed_count = 0
    skipped_count = 0

    async for record in cursor:
        call_id = record.get("call_id", "unknown")
        started_at = record.get("started_at")
        ended_at = record.get("ended_at")
        current_duration = record.get("duration")

        # Calculate duration
        calculated_duration = await calculate_duration(started_at, ended_at)

        if calculated_duration is None:
            print(f"⚠️  {call_id}: Failed to calculate duration")
            failed_count += 1
            continue

        if calculated_duration < 0:
            print(f"⚠️  {call_id}: Invalid duration ({calculated_duration}s) - skipping")
            skipped_count += 1
            continue

        # Skip if duration is already correct
        if current_duration == calculated_duration:
            skipped_count += 1
            continue

        # Update record
        if dry_run:
            print(f"   {call_id}: Would update duration from {current_duration} to {calculated_duration}s")
        else:
            try:
                result = await collection.update_one(
                    {"_id": record["_id"]},
                    {"$set": {"duration": calculated_duration}}
                )

                if result.modified_count > 0:
                    print(f"✅ {call_id}: Updated duration from {current_duration} to {calculated_duration}s")
                    updated_count += 1
                else:
                    print(f"⚠️  {call_id}: No changes made")
                    skipped_count += 1
            except Exception as e:
                print(f"❌ {call_id}: Failed to update - {e}")
                failed_count += 1

    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"Total records processed: {cursor_limit}")
    print(f"✅ Successfully updated: {updated_count}")
    print(f"⚠️  Skipped: {skipped_count}")
    print(f"❌ Failed: {failed_count}")

    if dry_run:
        print(f"\n💡 This was a dry run. Use without --dry-run to apply changes.")
    else:
        print(f"\n✅ Database updated successfully!")

    # Verify results
    remaining_nulls = await collection.count_documents({"duration": None})
    remaining_zeros_needing_update = await collection.count_documents({
        "duration": 0,
        "started_at": {"$exists": True, "$ne": None},
        "ended_at": {"$exists": True, "$ne": None},
        "$expr": {"$ne": ["$started_at", "$ended_at"]}  # Timestamps differ
    })
    print(f"\n📊 Remaining calls with duration=null: {remaining_nulls}")
    print(f"📊 Remaining calls with duration=0 but different timestamps: {remaining_zeros_needing_update}")


async def main():
    """Parse arguments and run backfill."""
    parser = argparse.ArgumentParser(
        description="Backfill missing duration data in automation_calls"
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

    args = parser.parse_args()

    try:
        await backfill_durations(dry_run=args.dry_run, limit=args.limit)
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
