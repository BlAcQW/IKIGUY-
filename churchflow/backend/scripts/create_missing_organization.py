"""
Script to create the missing organization for IMPACT 2025 conference.

This organization record was referenced but never created in the database.
Organization ID: 8eac859d-9459-4bd2-a690-041ad2ba573d
"""

import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection string (password properly URL-encoded)
MONGODB_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow?authSource=admin"

# The missing organization ID
MISSING_ORG_ID = "8eac859d-9459-4bd2-a690-041ad2ba573d"


async def create_missing_organization():
    """Create the missing organization record."""

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()

    print("Connected to MongoDB")
    print(f"Creating organization with ID: {MISSING_ORG_ID}\n")

    # Check if organization already exists
    existing = await db.organizations.find_one({"_id": MISSING_ORG_ID})
    if existing:
        print("⚠️  Organization already exists!")
        print(f"Name: {existing.get('name')}")
        print(f"Display Name: {existing.get('display_name')}")
        client.close()
        return

    # Organization data based on IMPACT 2025 conference context
    organization_doc = {
        "_id": MISSING_ORG_ID,
        "name": "impact-2025-organization",
        "display_name": "IMPACT 2025 Organization",
        "slug": "impact-2025-organization",
        "description": "Organization for IMPACT 2025 - Eight days of divine impartation with a dynamic lineup of speakers.",
        "contact_info": {
            "phone": "+233302764505",
            "email": "info@impact2025.org",
            "address": "Accra, Ghana",
            "website": "https://impact2025.org"
        },
        "settings": {
            "enable_bus_management": True,
            "enable_qr_checkin": True,
            "enable_conference_registration": True,
            "enable_notifications": True
        },
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "metadata": {
            "conference": "IMPACT 2025",
            "year": 2025,
            "created_by_script": True,
            "reason": "Missing organization record for existing conference data"
        }
    }

    # Insert organization
    result = await db.organizations.insert_one(organization_doc)

    print("✅ Organization created successfully!")
    print(f"   ID: {result.inserted_id}")
    print(f"   Name: {organization_doc['name']}")
    print(f"   Display Name: {organization_doc['display_name']}")
    print()

    # Verify the creation
    print("Verifying creation...")

    # Check conference references
    conference = await db.conferences.find_one({"organization_id": MISSING_ORG_ID})
    if conference:
        print(f"   ✓ Conference found: {conference.get('name')}")

    # Check registration references
    reg_count = await db.conference_registrations.count_documents({"organization_id": MISSING_ORG_ID})
    print(f"   ✓ Registrations referencing this org: {reg_count}")

    # Check session attendance references
    attendance_count = await db.session_attendance.count_documents({"conference_id": conference["_id"]}) if conference else 0
    print(f"   ✓ Session attendance records: {attendance_count}")

    print()
    print("="*60)
    print("✅ Organization successfully created and linked!")
    print("="*60)
    print(f"   Organization ID: {MISSING_ORG_ID}")
    print(f"   Conference: IMPACT 2025")
    print(f"   Total Registrations: {reg_count}")
    print(f"   Total Session Attendance: {attendance_count}")
    print("="*60)

    client.close()


if __name__ == "__main__":
    asyncio.run(create_missing_organization())
