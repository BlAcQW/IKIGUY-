"""
Script to fix missing organization_id in conference registrations.

Many registrations for IMPACT 2025 are missing the organization_id field.
This script will update them to reference the correct organization.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# MongoDB connection string (password properly URL-encoded)
MONGODB_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow?authSource=admin"

# Conference and organization IDs
IMPACT_2025_CONFERENCE_ID = ObjectId("68fbc116ca541168d5ea195e")
IMPACT_2025_ORG_ID = "8eac859d-9459-4bd2-a690-041ad2ba573d"


async def fix_missing_organization_ids():
    """Update registrations missing organization_id."""

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()

    print("Connected to MongoDB")
    print(f"Fixing registrations for IMPACT 2025 conference\n")

    # Count registrations without organization_id
    missing_count = await db.conference_registrations.count_documents({
        "conference_id": IMPACT_2025_CONFERENCE_ID,
        "organization_id": {"$exists": False}
    })

    print(f"Found {missing_count} registrations missing organization_id")

    if missing_count == 0:
        print("✅ No registrations need updating!")
        client.close()
        return

    # Update all registrations
    result = await db.conference_registrations.update_many(
        {
            "conference_id": IMPACT_2025_CONFERENCE_ID,
            "organization_id": {"$exists": False}
        },
        {
            "$set": {
                "organization_id": IMPACT_2025_ORG_ID
            }
        }
    )

    print(f"\n✅ Successfully updated {result.modified_count} registrations")

    # Verify the fix
    print("\nVerifying fix...")
    remaining_without_org = await db.conference_registrations.count_documents({
        "conference_id": IMPACT_2025_CONFERENCE_ID,
        "organization_id": {"$exists": False}
    })

    total_with_org = await db.conference_registrations.count_documents({
        "conference_id": IMPACT_2025_CONFERENCE_ID,
        "organization_id": IMPACT_2025_ORG_ID
    })

    total_for_conference = await db.conference_registrations.count_documents({
        "conference_id": IMPACT_2025_CONFERENCE_ID
    })

    print(f"   Total registrations for IMPACT 2025: {total_for_conference}")
    print(f"   Registrations with organization_id: {total_with_org}")
    print(f"   Registrations still missing org_id: {remaining_without_org}")

    if remaining_without_org == 0:
        print("\n✅ All registrations now have organization_id!")
    else:
        print(f"\n⚠️  Warning: {remaining_without_org} registrations still missing organization_id")

    print("\n" + "="*60)
    print("✅ Fix complete!")
    print("="*60)

    client.close()


if __name__ == "__main__":
    asyncio.run(fix_missing_organization_ids())
