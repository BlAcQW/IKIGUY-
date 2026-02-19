#!/usr/bin/env python3
"""
Clean Invalid Phone Numbers from ChurchFlow Database

This script identifies and cleans up invalid phone numbers in the database.
Valid Ghana phone numbers:
- Start with +233 or 0
- +233 format: 12 digits total (+233XXXXXXXXX)
- 0 format: 10 digits total (0XXXXXXXXX)
- Valid mobile prefixes: 020, 023, 024, 025, 026, 027, 028, 050, 054, 055, 056, 057, 059
"""

import asyncio
import re
import sys
from typing import List, Dict
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# MongoDB connection
from urllib.parse import quote_plus
username = quote_plus("admin")
password = quote_plus("aawwER4444%")
MONGO_URI = f"mongodb://{username}:{password}@127.0.0.1:27017/churchflow?authSource=admin"

# Valid Ghana mobile prefixes
GHANA_MOBILE_PREFIXES = [
    "020", "023", "024", "025", "026", "027", "028",
    "050", "054", "055", "056", "057", "059"
]


def is_valid_ghana_phone(phone: str) -> bool:
    """
    Validate if a phone number is a valid Ghana mobile number.

    Args:
        phone: Phone number string

    Returns:
        True if valid, False otherwise
    """
    if not phone:
        return False

    # Remove spaces and hyphens
    phone = phone.replace(" ", "").replace("-", "")

    # Check for obviously invalid patterns
    # 1. Too short or too long
    if len(phone) < 9 or len(phone) > 15:
        return False

    # 2. Repeating digits (like 777777777, 55555555)
    if re.match(r'^(\d)\1+$', phone):
        return False

    # 3. Sequential test numbers
    if phone in ["12345", "123456789", "1234567890"]:
        return False

    # Validate Ghana-specific formats
    # Format 1: +233XXXXXXXXX (12 digits total)
    if phone.startswith("+233"):
        if len(phone) != 13:  # +233 + 9 digits
            return False
        number_part = phone[4:]  # Remove +233
        prefix = number_part[:3]
        return prefix in GHANA_MOBILE_PREFIXES and number_part.isdigit()

    # Format 2: 0XXXXXXXXX (10 digits total)
    elif phone.startswith("0"):
        if len(phone) != 10:
            return False
        prefix = phone[1:4]  # Get the 3 digits after 0
        return prefix in GHANA_MOBILE_PREFIXES and phone[1:].isdigit()

    # Format 3: 233XXXXXXXXX (12 digits, no +)
    elif phone.startswith("233"):
        if len(phone) != 12:
            return False
        number_part = phone[3:]  # Remove 233
        prefix = number_part[:3]
        return prefix in GHANA_MOBILE_PREFIXES and phone.isdigit()

    # Not a recognized Ghana format
    return False


async def find_invalid_phones(db):
    """Find all invalid phone numbers in the database."""
    print("\n🔍 Scanning for invalid phone numbers...\n")

    invalid_phones = []

    # Check conference registrations
    cursor = db.conference_registrations.find({
        "user_phone": {"$exists": True, "$ne": ""}
    })

    async for doc in cursor:
        phone = doc.get("user_phone", "")
        if not is_valid_ghana_phone(phone):
            invalid_phones.append({
                "collection": "conference_registrations",
                "id": str(doc["_id"]),
                "phone": phone,
                "name": doc.get("user_name", "Unknown"),
                "email": doc.get("user_email", "")
            })

    # Check users collection
    cursor = db.users.find({
        "phone": {"$exists": True, "$ne": ""}
    })

    async for doc in cursor:
        phone = doc.get("phone", "")
        if not is_valid_ghana_phone(phone):
            invalid_phones.append({
                "collection": "users",
                "id": str(doc["_id"]),
                "phone": phone,
                "name": doc.get("name", "Unknown"),
                "email": doc.get("email", "")
            })

    return invalid_phones


async def clean_invalid_phones(db, invalid_phones: List[Dict]):
    """Clean invalid phone numbers from the database."""
    print(f"\n🧹 Cleaning {len(invalid_phones)} invalid phone numbers...\n")

    cleaned_count = 0

    for entry in invalid_phones:
        try:
            if entry["collection"] == "conference_registrations":
                from bson import ObjectId
                result = await db.conference_registrations.update_one(
                    {"_id": ObjectId(entry["id"])},
                    {"$set": {
                        "user_phone": "",
                        "phone_invalid": True,
                        "phone_invalid_value": entry["phone"],
                        "phone_cleaned_at": datetime.utcnow().isoformat()
                    }}
                )
                if result.modified_count > 0:
                    cleaned_count += 1
                    print(f"✓ Cleaned: {entry['name']} ({entry['phone']})")

            elif entry["collection"] == "users":
                from bson import ObjectId
                result = await db.users.update_one(
                    {"_id": ObjectId(entry["id"])},
                    {"$set": {
                        "phone": "",
                        "phone_invalid": True,
                        "phone_invalid_value": entry["phone"],
                        "phone_cleaned_at": datetime.utcnow().isoformat()
                    }}
                )
                if result.modified_count > 0:
                    cleaned_count += 1
                    print(f"✓ Cleaned: {entry['name']} ({entry['phone']})")

        except Exception as e:
            print(f"✗ Error cleaning {entry['phone']}: {e}")

    return cleaned_count


async def clean_campaign_messages(db, campaign_id: str = None):
    """Remove failed messages with invalid phone numbers from campaigns."""
    print("\n🗑️  Cleaning up failed campaign messages...\n")

    query = {
        "status": "failed",
        "error_message": {"$regex": "No valid number"}
    }

    if campaign_id:
        query["campaign_id"] = campaign_id

    result = await db.sms_campaign_messages.delete_many(query)
    print(f"✓ Deleted {result.deleted_count} failed messages with invalid numbers")

    return result.deleted_count


async def update_campaign_progress(db, campaign_id: str):
    """Recalculate campaign progress after cleanup."""
    print("\n📊 Recalculating campaign progress...\n")

    # Count messages by status
    pipeline = [
        {"$match": {"campaign_id": campaign_id}},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }}
    ]

    status_counts = {}
    async for doc in db.sms_campaign_messages.aggregate(pipeline):
        status_counts[doc["_id"]] = doc["count"]

    total = sum(status_counts.values())
    sent = status_counts.get("sent", 0)
    failed = status_counts.get("failed", 0)
    pending = status_counts.get("pending", 0)

    # Update campaign
    await db.sms_campaigns.update_one(
        {"id": campaign_id},
        {"$set": {
            "progress.total_recipients": total,
            "progress.sent": sent,
            "progress.failed": failed,
            "progress.pending": pending,
            "updated_at": datetime.utcnow().isoformat()
        }}
    )

    print(f"✓ Campaign progress updated:")
    print(f"  Total: {total}")
    print(f"  Sent: {sent}")
    print(f"  Failed: {failed}")
    print(f"  Pending: {pending}")


async def main():
    """Main cleanup function."""
    print("=" * 60)
    print("ChurchFlow Phone Number Cleanup Script")
    print("=" * 60)

    # Connect to database
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.churchflow

    try:
        # Find invalid phones
        invalid_phones = await find_invalid_phones(db)

        if not invalid_phones:
            print("\n✅ No invalid phone numbers found!")
            return

        print(f"\n📋 Found {len(invalid_phones)} invalid phone numbers:")
        for entry in invalid_phones[:10]:  # Show first 10
            print(f"  - {entry['name']}: {entry['phone']} ({entry['collection']})")
        if len(invalid_phones) > 10:
            print(f"  ... and {len(invalid_phones) - 10} more")

        # Ask for confirmation
        print(f"\n⚠️  This will clean {len(invalid_phones)} invalid phone numbers")
        print("   (They will be cleared and marked as invalid)")
        response = input("\nProceed? (yes/no): ").strip().lower()

        if response != "yes":
            print("\n❌ Cleanup cancelled")
            return

        # Clean invalid phones
        cleaned = await clean_invalid_phones(db, invalid_phones)
        print(f"\n✅ Cleaned {cleaned} phone numbers")

        # Clean campaign messages
        deleted = await clean_campaign_messages(db)

        # Update campaign progress for the current running campaign
        campaign_id = "13a2ed46-2418-4cd3-a1e5-44945372eb24"
        await update_campaign_progress(db, campaign_id)

        print("\n" + "=" * 60)
        print("✅ Cleanup completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
