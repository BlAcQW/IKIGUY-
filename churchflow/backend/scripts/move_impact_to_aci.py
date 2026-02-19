"""
Script to move IMPACT 2025 conference to Action Chapel International organization.

The IMPACT 2025 conference is organized by Action Chapel International,
so it should belong to their organization, not a separate one.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# MongoDB connection string (password properly URL-encoded)
MONGODB_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow?authSource=admin"

# IDs
IMPACT_2025_CONFERENCE_ID = ObjectId("68fbc116ca541168d5ea195e")
OLD_ORG_ID = "8eac859d-9459-4bd2-a690-041ad2ba573d"  # IMPACT 2025 Organization (to be removed)
ACI_ORG_ID = ObjectId("6917151c7ebf023dc2ba26b0")  # Action Chapel International (active)
ACI_ORG_ID_STR = "6917151c7ebf023dc2ba26b0"


async def move_impact_to_aci():
    """Move IMPACT 2025 conference and all related data to Action Chapel International."""

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()

    print("="*70)
    print("Moving IMPACT 2025 Conference to Action Chapel International")
    print("="*70)
    print()

    # Get ACI organization
    aci_org = await db.organizations.find_one({"_id": ACI_ORG_ID})
    if not aci_org:
        print("❌ Error: Action Chapel International organization not found!")
        client.close()
        return

    print(f"✓ Target Organization: {aci_org.get('display_name', aci_org.get('name'))}")
    print(f"  ID: {ACI_ORG_ID}")
    print()

    # Get current conference data
    conference = await db.conferences.find_one({"_id": IMPACT_2025_CONFERENCE_ID})
    if not conference:
        print("❌ Error: IMPACT 2025 conference not found!")
        client.close()
        return

    print(f"✓ Conference: {conference.get('name')}")
    print(f"  Current Org ID: {conference.get('organization_id')}")
    print()

    # Count affected records
    reg_count = await db.conference_registrations.count_documents({
        "conference_id": IMPACT_2025_CONFERENCE_ID
    })

    session_count = await db.conference_sessions.count_documents({
        "conference_id": IMPACT_2025_CONFERENCE_ID
    })

    attendance_count = await db.session_attendance.count_documents({
        "conference_id": IMPACT_2025_CONFERENCE_ID
    })

    print("Records to be updated:")
    print(f"  Registrations: {reg_count}")
    print(f"  Sessions: {session_count}")
    print(f"  Session Attendance: {attendance_count}")
    print()

    print("Starting migration...")
    print()

    # 1. Update conference
    result = await db.conferences.update_one(
        {"_id": IMPACT_2025_CONFERENCE_ID},
        {"$set": {"organization_id": ACI_ORG_ID_STR}}
    )
    print(f"✓ Updated conference: {result.modified_count} record(s)")

    # 2. Update registrations
    result = await db.conference_registrations.update_many(
        {"conference_id": IMPACT_2025_CONFERENCE_ID},
        {"$set": {"organization_id": ACI_ORG_ID_STR}}
    )
    print(f"✓ Updated registrations: {result.modified_count} record(s)")

    # 3. Update sessions (they might have organization_id)
    result = await db.conference_sessions.update_many(
        {"conference_id": IMPACT_2025_CONFERENCE_ID},
        {"$set": {"organization_id": ACI_ORG_ID_STR}}
    )
    print(f"✓ Updated sessions: {result.modified_count} record(s)")

    print()
    print("Verifying migration...")
    print()

    # Verify conference
    conf_check = await db.conferences.find_one({"_id": IMPACT_2025_CONFERENCE_ID})
    print(f"✓ Conference org_id: {conf_check.get('organization_id')}")

    # Verify registrations
    reg_check = await db.conference_registrations.count_documents({
        "conference_id": IMPACT_2025_CONFERENCE_ID,
        "organization_id": ACI_ORG_ID_STR
    })
    print(f"✓ Registrations with ACI org_id: {reg_check}/{reg_count}")

    # Verify sessions
    session_check = await db.conference_sessions.count_documents({
        "conference_id": IMPACT_2025_CONFERENCE_ID,
        "organization_id": ACI_ORG_ID_STR
    })
    print(f"✓ Sessions with ACI org_id: {session_check}/{session_count}")

    print()
    print("="*70)
    print("✅ Migration Complete!")
    print("="*70)
    print()
    print(f"IMPACT 2025 conference now belongs to: {aci_org.get('display_name', aci_org.get('name'))}")
    print(f"Organization ID: {ACI_ORG_ID}")
    print()
    print("Summary:")
    print(f"  Conference: Moved")
    print(f"  Registrations: {reg_check} moved")
    print(f"  Sessions: {session_check} moved")
    print(f"  Session Attendance: {attendance_count} (automatically linked via conference)")
    print()

    # Clean up the old IMPACT 2025 Organization
    print("Cleaning up old IMPACT 2025 Organization...")
    old_org = await db.organizations.find_one({"_id": OLD_ORG_ID})
    if old_org:
        # Check if it has any other data
        other_conferences = await db.conferences.count_documents({"organization_id": OLD_ORG_ID})
        if other_conferences == 0:
            # Safe to delete
            await db.organizations.delete_one({"_id": OLD_ORG_ID})
            print(f"✓ Deleted old 'IMPACT 2025 Organization' (no other data)")
        else:
            print(f"⚠️  Kept old organization (has {other_conferences} other conferences)")
    else:
        print("  (Old organization already removed)")

    print()
    print("="*70)

    client.close()


if __name__ == "__main__":
    asyncio.run(move_impact_to_aci())
