"""
Simple migration script to fix registration check-in status using direct MongoDB connection.
"""

import asyncio
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# MongoDB connection string (password properly URL-encoded)
MONGODB_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow?authSource=admin"


async def fix_registration_checkin_status():
    """Fix registration check-in status for registrations with session attendance."""

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()

    print("Connected to MongoDB")
    print("Starting registration check-in status fix...\n")

    # Get all session attendance records
    attendance_records = await db.session_attendance.find({}).to_list(length=None)
    print(f"Found {len(attendance_records)} session attendance records")

    # Get unique registration IDs from attendance
    registration_ids_with_attendance = set()
    first_checkin_map = {}  # Map registration_id -> earliest check-in time

    for record in attendance_records:
        reg_id = record.get("registration_id")
        if reg_id:
            registration_ids_with_attendance.add(reg_id)

            # Track earliest check-in time
            checked_in_at = record.get("checked_in_at")
            if checked_in_at:
                if reg_id not in first_checkin_map or checked_in_at < first_checkin_map[reg_id]:
                    first_checkin_map[reg_id] = checked_in_at

    print(f"Found {len(registration_ids_with_attendance)} unique registrations with attendance\n")

    # Find registrations that have attendance but checked_in is false
    registrations_to_update = await db.conference_registrations.find({
        "_id": {"$in": list(registration_ids_with_attendance)},
        "$or": [
            {"checked_in": False},
            {"checked_in": {"$exists": False}}
        ]
    }).to_list(length=None)

    print(f"Found {len(registrations_to_update)} registrations that need to be updated\n")

    if len(registrations_to_update) == 0:
        print("✅ No registrations need updating. All data is consistent!")
        client.close()
        return

    # Update registrations
    updated_count = 0
    for reg in registrations_to_update:
        reg_id = reg["_id"]
        first_checkin = first_checkin_map.get(reg_id, datetime.utcnow())

        result = await db.conference_registrations.update_one(
            {"_id": reg_id},
            {
                "$set": {
                    "checked_in": True,
                    "first_check_in_at": first_checkin
                }
            }
        )

        if result.modified_count > 0:
            updated_count += 1
            conf_name = reg.get("conference_name", "Unknown")
            user_name = reg.get("user_name", "Unknown")
            user_phone = reg.get("user_phone", "No phone")
            print(f"  ✓ Updated {user_name} - {user_phone} ({conf_name})")

    print(f"\n{'='*60}")
    print(f"✅ Migration Complete!")
    print(f"{'='*60}")
    print(f"   Total session attendance records: {len(attendance_records)}")
    print(f"   Unique registrations with attendance: {len(registration_ids_with_attendance)}")
    print(f"   Registrations updated: {updated_count}")
    print(f"{'='*60}\n")

    # Verify the fix
    print("Verifying fix...")
    remaining_inconsistent = await db.conference_registrations.count_documents({
        "_id": {"$in": list(registration_ids_with_attendance)},
        "$or": [
            {"checked_in": False},
            {"checked_in": {"$exists": False}}
        ]
    })

    if remaining_inconsistent == 0:
        print("✅ All registrations with attendance are now marked as checked_in!")
    else:
        print(f"⚠️  Warning: {remaining_inconsistent} registrations still inconsistent")

    client.close()


if __name__ == "__main__":
    asyncio.run(fix_registration_checkin_status())
