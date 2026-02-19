#!/usr/bin/env python3
"""
Add MongoDB indexes for faster search queries on conference_registrations collection.

This script creates text indexes on frequently searched fields to improve
search performance from O(n) table scan to O(log n) index lookup.
"""

import os
from pymongo import MongoClient, TEXT, ASCENDING

def add_search_indexes():
    """
    Add indexes to conference_registrations collection for faster searches.

    Creates:
    1. Text index on user_name, user_email, registration_code for full-text search
    2. Regular index on user_phone for exact/prefix matching
    3. Compound index on conference_id + created_at for filtered pagination
    """
    mongodb_url = os.getenv(
        "MONGODB_URL",
        "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow?authSource=admin"
    )

    client = MongoClient(mongodb_url)
    db = client.churchflow
    collection = db.conference_registrations

    print("🔍 Adding search indexes to conference_registrations collection...")

    # Get existing indexes
    existing_indexes = list(collection.list_indexes())
    existing_index_names = [idx['name'] for idx in existing_indexes]

    print(f"\n📋 Existing indexes: {existing_index_names}")

    # 1. Text index for full-text search on user_name, user_email, registration_code
    # Reason: Enables fast case-insensitive text search across multiple fields
    if 'text_search_idx' not in existing_index_names:
        print("\n✨ Creating text index for user_name, user_email, registration_code...")
        collection.create_index(
            [
                ("user_name", TEXT),
                ("user_email", TEXT),
                ("registration_code", TEXT)
            ],
            name="text_search_idx"
        )
        print("✅ Text index created")
    else:
        print("\n⏭️  Text index already exists")

    # 2. Regular index on user_phone for phone number searches
    # Reason: Text indexes don't work well for phone numbers, use regular index
    if 'user_phone_idx' not in existing_index_names:
        print("\n✨ Creating index on user_phone...")
        collection.create_index([("user_phone", ASCENDING)], name="user_phone_idx")
        print("✅ Phone index created")
    else:
        print("\n⏭️  Phone index already exists")

    # 3. Compound index on conference_id + created_at for filtered pagination
    # Reason: Most queries filter by conference and sort by created_at
    if 'conference_created_idx' not in existing_index_names:
        print("\n✨ Creating compound index on conference_id + created_at...")
        collection.create_index(
            [("conference_id", ASCENDING), ("created_at", -1)],
            name="conference_created_idx"
        )
        print("✅ Compound index created")
    else:
        print("\n⏭️  Compound index already exists")

    # 4. Index on status for status filtering
    if 'status_idx' not in existing_index_names:
        print("\n✨ Creating index on status...")
        collection.create_index([("status", ASCENDING)], name="status_idx")
        print("✅ Status index created")
    else:
        print("\n⏭️  Status index already exists")

    # 5. Index on checked_in for check-in filtering
    if 'checked_in_idx' not in existing_index_names:
        print("\n✨ Creating index on checked_in...")
        collection.create_index([("checked_in", ASCENDING)], name="checked_in_idx")
        print("✅ Checked-in index created")
    else:
        print("\n⏭️  Checked-in index already exists")

    # Show final index list
    print("\n📊 Final indexes:")
    for idx in collection.list_indexes():
        print(f"  - {idx['name']}: {idx.get('key', {})}")

    print("\n🎉 Index creation complete!")

    # Show collection stats
    stats = db.command("collstats", "conference_registrations")
    print(f"\n📈 Collection stats:")
    print(f"  - Documents: {stats['count']:,}")
    print(f"  - Total index size: {stats.get('totalIndexSize', 0) / 1024:.2f} KB")
    print(f"  - Number of indexes: {stats.get('nindexes', 0)}")

if __name__ == "__main__":
    add_search_indexes()
