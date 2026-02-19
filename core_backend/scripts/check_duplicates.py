#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.mongo import get_collection

async def main():
    vapi_calls = get_collection("vapi_calls")

    # Find duplicate call_ids
    pipeline = [
        {"$group": {
            "_id": "$call_id",
            "count": {"$sum": 1},
            "ids": {"$push": "$_id"}
        }},
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]

    duplicates = await vapi_calls.aggregate(pipeline).to_list(10)

    print(f"Found {len(duplicates)} call_ids with duplicates (showing top 10)")
    for dup in duplicates:
        call_id = dup['_id']
        count = dup['count']
        print(f"\ncall_id: {call_id} has {count} records")

        # Get all records for this call_id
        records = await vapi_calls.find({"call_id": call_id}).to_list(count)
        for i, rec in enumerate(records, 1):
            print(f"  Record {i}: duration={rec.get('duration')}, cost={rec.get('cost')}, status={rec.get('status')}")

    # Count total duplicates
    all_dups = await vapi_calls.aggregate([
        {"$group": {
            "_id": "$call_id",
            "count": {"$sum": 1}
        }},
        {"$match": {"count": {"$gt": 1}}},
        {"$count": "total"}
    ]).to_list(1)

    if all_dups:
        print(f"\nTotal call_ids with duplicates: {all_dups[0]['total']}")

if __name__ == "__main__":
    asyncio.run(main())
