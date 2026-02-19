#!/usr/bin/env python3
"""
Clean up duplicate records in vapi_calls collection.

For each call_id with duplicates:
1. Keep the LAST record with the most complete data (end-of-call webhook)
2. Delete all EARLIER duplicate records (mid-call partial saves)

Run: python3 scripts/cleanup_duplicate_vapi_calls.py [--dry-run] [--limit N]
"""
import asyncio
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.mongo import get_collection


def score_record_completeness(record: Dict[str, Any]) -> int:
    """
    Score a record based on data completeness.
    Higher score = more complete data.

    Args:
        record: MongoDB document

    Returns:
        int: Completeness score
    """
    score = 0

    # Critical fields (10 points each)
    if record.get("duration") and record.get("duration") > 0:
        score += 10
    if record.get("call_duration") and record.get("call_duration") > 0:
        score += 10
    if record.get("cost") and record.get("cost") > 0:
        score += 10
    if record.get("vapi_cost") and record.get("vapi_cost") > 0:
        score += 10

    # Important fields (5 points each)
    if record.get("status") and record.get("status") not in [None, ""]:
        score += 5
    if record.get("ended_reason") and record.get("ended_reason") not in [None, ""]:
        score += 5
    if record.get("started_at"):
        score += 5
    if record.get("ended_at"):
        score += 5

    # Basic fields (1 point each)
    if record.get("from_phone"):
        score += 1
    if record.get("to_phone"):
        score += 1
    if record.get("assistant_id"):
        score += 1

    return score


def get_record_timestamp(record: Dict[str, Any]) -> datetime:
    """
    Get the timestamp of a record for sorting.
    Uses created_at if available, otherwise uses MongoDB _id timestamp.

    Args:
        record: MongoDB document

    Returns:
        datetime: Record timestamp
    """
    # Try created_at field first
    if record.get("created_at"):
        try:
            from dateutil import parser
            return parser.parse(record["created_at"]) if isinstance(record["created_at"], str) else record["created_at"]
        except:
            pass

    # Fall back to ObjectId timestamp (embedded in _id)
    if record.get("_id"):
        return record["_id"].generation_time

    # Last resort - epoch
    return datetime.fromtimestamp(0)


async def cleanup_duplicates(dry_run: bool = False, limit: int = None):
    """
    Clean up duplicate records in vapi_calls collection.

    Args:
        dry_run: If True, only show what would be deleted
        limit: Maximum number of duplicate call_ids to process
    """
    vapi_calls = get_collection("vapi_calls")

    # Find all call_ids with duplicates
    pipeline = [
        {"$group": {
            "_id": "$call_id",
            "count": {"$sum": 1},
            "ids": {"$push": "$_id"}
        }},
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}}
    ]

    if limit:
        pipeline.append({"$limit": limit})

    duplicates = await vapi_calls.aggregate(pipeline).to_list(None)

    print(f"\n📊 Found {len(duplicates)} call_ids with duplicate records")

    if not duplicates:
        print("✅ No duplicates to clean up!")
        return

    if dry_run:
        print("🔍 DRY RUN MODE - No deletions will be performed\n")
    else:
        print("⚠️  LIVE MODE - Duplicates will be deleted\n")

    total_records_to_delete = 0
    total_records_kept = 0

    for dup in duplicates:
        call_id = dup["_id"]
        count = dup["count"]

        # Fetch all records for this call_id
        records = await vapi_calls.find({"call_id": call_id}).to_list(count)

        # Score each record and get timestamp
        scored_records = [
            (record, score_record_completeness(record), get_record_timestamp(record))
            for record in records
        ]

        # Sort by:
        # 1. Completeness score (highest first)
        # 2. Timestamp (latest first) - breaks ties and ensures we keep the end-of-call record
        scored_records.sort(key=lambda x: (x[1], x[2]), reverse=True)

        # Keep the highest scoring, latest record (the end-of-call webhook)
        best_record = scored_records[0][0]
        best_score = scored_records[0][1]
        best_timestamp = scored_records[0][2]
        records_to_delete = [r[0] for r in scored_records[1:]]

        print(f"\n📞 call_id: {call_id}")
        print(f"   Total duplicates: {count}")
        print(f"   Keeping: {best_record['_id']}")
        print(f"      - Score: {best_score}")
        print(f"      - Timestamp: {best_timestamp}")
        print(f"      - Duration: {best_record.get('duration')}")
        print(f"      - Cost: {best_record.get('cost')}")
        print(f"      - Status: {best_record.get('status')}")
        print(f"   Deleting: {len(records_to_delete)} earlier records")

        if dry_run:
            for rec, score, timestamp in scored_records[1:4]:  # Show first 3 to be deleted
                print(f"      - {rec['_id']}")
                print(f"         Score: {score}, Timestamp: {timestamp}")
                print(f"         Duration: {rec.get('duration')}, Cost: {rec.get('cost')}, Status: {rec.get('status')}")
            if len(records_to_delete) > 3:
                print(f"      ... and {len(records_to_delete) - 3} more")
        else:
            # Delete duplicate records
            ids_to_delete = [r["_id"] for r in records_to_delete]
            result = await vapi_calls.delete_many({"_id": {"$in": ids_to_delete}})
            print(f"   ✅ Deleted {result.deleted_count} duplicate records")
            total_records_to_delete += result.deleted_count
            total_records_kept += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"Call IDs with duplicates: {len(duplicates)}")
    print(f"✅ Records kept: {total_records_kept if not dry_run else len(duplicates)}")
    print(f"🗑️  Records deleted: {total_records_to_delete if not dry_run else sum(d['count'] - 1 for d in duplicates)}")

    if dry_run:
        print(f"\n💡 This was a dry run. Use without --dry-run to delete duplicates.")
    else:
        print(f"\n✅ Cleanup complete!")

        # Verify
        remaining_duplicates = await vapi_calls.aggregate([
            {"$group": {
                "_id": "$call_id",
                "count": {"$sum": 1}
            }},
            {"$match": {"count": {"$gt": 1}}},
            {"$count": "total"}
        ]).to_list(1)

        if remaining_duplicates:
            print(f"⚠️  Warning: {remaining_duplicates[0]['total']} call_ids still have duplicates")
        else:
            print(f"✅ All duplicates cleaned up!")


async def main():
    """Parse arguments and run cleanup."""
    parser = argparse.ArgumentParser(
        description="Clean up duplicate records in vapi_calls collection"
    )
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--limit", type=int, default=None, help="Max call_ids to process")

    args = parser.parse_args()

    try:
        await cleanup_duplicates(
            dry_run=args.dry_run,
            limit=args.limit
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
