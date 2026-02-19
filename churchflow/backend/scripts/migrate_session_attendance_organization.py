"""
Database migration script to add organization_id to session_attendance records.

This script:
1. Finds session attendance records linked to conferences
2. Adds organization_id from the conference to each record
3. Handles orphaned records (conference doesn't exist)
4. Provides detailed reporting

Run: python apps/churchflow/backend/scripts/migrate_session_attendance_organization.py
"""

import asyncio
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection string (password properly URL-encoded)
MONGODB_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow?authSource=admin"


async def migrate_session_attendance():
    """Add organization_id to all session attendance records based on their conference."""

    print("\n" + "=" * 80)
    print("SESSION ATTENDANCE ORGANIZATION MIGRATION")
    print("=" * 80)

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()

    # Count total session attendance records
    total_records = await db.session_attendance.count_documents({})
    records_with_org = await db.session_attendance.count_documents({"organization_id": {"$exists": True, "$ne": None}})
    records_without_org = await db.session_attendance.count_documents({"organization_id": {"$exists": False}}) + \
                          await db.session_attendance.count_documents({"organization_id": None})

    print(f"\n📊 Current State:")
    print(f"   Total session attendance records: {total_records}")
    print(f"   ✅ With organization_id: {records_with_org}")
    print(f"   ❌ Without organization_id: {records_without_org}")

    if records_without_org == 0:
        print("\n✅ All session attendance records already have organization_id!")
        client.close()
        return

    print(f"\n🔄 Processing {records_without_org} session attendance records...")
    print(f"   Using batch update for efficiency...")

    # Get distinct conference IDs from session attendance
    pipeline = [
        {"$match": {"$or": [{"organization_id": {"$exists": False}}, {"organization_id": None}]}},
        {"$group": {"_id": "$conference_id"}},
        {"$limit": 100}
    ]

    conference_ids = await db.session_attendance.aggregate(pipeline).to_list(length=100)
    unique_conference_ids = [item["_id"] for item in conference_ids if item["_id"]]

    print(f"   Found {len(unique_conference_ids)} unique conferences in attendance records")

    updated_count = 0
    orphaned_count = 0
    error_count = 0

    for conference_id in unique_conference_ids:
        try:
            # Get conference to find organization_id
            # Reason: Session attendance is tied to conferences, organization comes from conference
            conference = await db.conferences.find_one(
                {"_id": conference_id},
                {"_id": 1, "name": 1, "organization_id": 1}
            )

            if not conference:
                orphaned = await db.session_attendance.count_documents({"conference_id": conference_id})
                print(f"   ⚠️  {orphaned} records reference non-existent conference {conference_id}")
                orphaned_count += orphaned
                continue

            organization_id = conference.get("organization_id")

            if not organization_id:
                orphaned = await db.session_attendance.count_documents({"conference_id": conference_id})
                print(f"   ⚠️  Conference '{conference.get('name')}' has no organization_id ({orphaned} records)")
                orphaned_count += orphaned
                continue

            # Batch update all session attendance records for this conference
            result = await db.session_attendance.update_many(
                {
                    "conference_id": conference_id,
                    "$or": [
                        {"organization_id": {"$exists": False}},
                        {"organization_id": None}
                    ]
                },
                {
                    "$set": {
                        "organization_id": organization_id,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            if result.modified_count > 0:
                print(f"   ✅ Updated {result.modified_count} records for '{conference.get('name', 'Unknown')}' → org: {organization_id}")
                updated_count += result.modified_count
            else:
                print(f"   ℹ️  No updates needed for conference '{conference.get('name', 'Unknown')}'")

        except Exception as e:
            print(f"   ❌ Error updating records for conference {conference_id}: {str(e)}")
            error_count += 1

    # Final verification
    print(f"\n📊 Migration Results:")
    print(f"   ✅ Successfully updated: {updated_count}")
    print(f"   ⚠️  Orphaned records (no valid conference): {orphaned_count}")
    print(f"   ❌ Errors: {error_count}")

    # Verify final state
    final_with_org = await db.session_attendance.count_documents({"organization_id": {"$exists": True, "$ne": None}})
    final_without_org = await db.session_attendance.count_documents({"organization_id": {"$exists": False}}) + \
                        await db.session_attendance.count_documents({"organization_id": None})

    print(f"\n📊 Final State:")
    print(f"   Total session attendance records: {total_records}")
    print(f"   ✅ With organization_id: {final_with_org}")
    print(f"   ❌ Without organization_id: {final_without_org}")

    print("\n" + "=" * 80)
    print("✅ Migration Complete!")
    print("=" * 80 + "\n")

    client.close()


if __name__ == "__main__":
    asyncio.run(migrate_session_attendance())
