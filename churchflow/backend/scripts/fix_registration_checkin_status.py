"""
Migration script to fix registration check-in status.

This script updates conference_registrations.checked_in to true for all registrations
that have session attendance records but checked_in is still false.

This ensures analytics show accurate "total checked in" numbers.
"""

import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../.env'))
load_dotenv(env_path)

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import get_database
from bson import ObjectId


async def fix_registration_checkin_status():
    """
    Fix registration check-in status for registrations with session attendance.
    """
    db = get_database()

    print("Starting registration check-in status fix...")

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

    print(f"Found {len(registration_ids_with_attendance)} unique registrations with attendance")

    # Find registrations that have attendance but checked_in is false
    registrations_to_update = await db.conference_registrations.find({
        "_id": {"$in": list(registration_ids_with_attendance)},
        "$or": [
            {"checked_in": False},
            {"checked_in": {"$exists": False}}
        ]
    }).to_list(length=None)

    print(f"Found {len(registrations_to_update)} registrations that need to be updated")

    if len(registrations_to_update) == 0:
        print("No registrations need updating. All data is consistent!")
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
            print(f"  ✓ Updated {reg.get('user_name', 'Unknown')} - {reg.get('user_phone', 'No phone')}")

    print(f"\n✅ Successfully updated {updated_count} registrations")
    print(f"   Total session attendance records: {len(attendance_records)}")
    print(f"   Unique registrations with attendance: {len(registration_ids_with_attendance)}")
    print(f"   Registrations updated: {updated_count}")

    # Verify the fix
    print("\nVerifying fix...")
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


async def main():
    """Main entry point."""
    try:
        await fix_registration_checkin_status()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
