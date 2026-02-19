#!/usr/bin/env python3
"""
Simple migration script to backfill listening data - NO WALLET SERVICE.

Since InkWave is free, we just insert transaction records directly
for leaderboard tracking purposes only.
"""

import asyncio
import sys
import os
from datetime import datetime
from bson import ObjectId

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Database
from app.services.leaderboard_service import LeaderboardService

print("=" * 80)
print("INKWAVE LISTENING DATA MIGRATION (SIMPLE)")
print("=" * 80)
print("Since InkWave is FREE, we're just inserting transaction records")
print("for leaderboard tracking - no actual wallet debits.\n")


async def main():
    """Run simple migration."""

    # Connect to database
    print("Connecting to database...")
    await Database.connect()
    db = Database.get_database()
    print("✓ Connected\n")

    # Check if already migrated
    existing_count = await db.wallet_transactions.count_documents({
        "metadata.service": "inkwave_listening",
        "metadata.migrated": True
    })

    if existing_count > 0:
        print(f"⚠ Found {existing_count} existing migrated transactions")
        response = input("Delete and re-migrate? (yes/no): ")
        if response.lower() == "yes":
            result = await db.wallet_transactions.delete_many({
                "metadata.service": "inkwave_listening",
                "metadata.migrated": True
            })
            print(f"✓ Deleted {result.deleted_count} old migrations\n")
        else:
            print("Migration aborted.")
            return

    # Get all reading sessions with listening time
    print("Fetching reading sessions with listening time...")
    sessions = await db.reading_sessions.find({
        "total_time_spent_minutes": {"$gt": 0}
    }).to_list(length=None)

    print(f"✓ Found {len(sessions)} sessions to migrate\n")

    if len(sessions) == 0:
        print("No sessions to migrate. Exiting.")
        return

    # Confirm
    print(f"This will create {len(sessions)} transaction records.")
    response = input("Continue? (yes/no): ")
    if response.lower() != "yes":
        print("Migration aborted.")
        return

    print("\nMigrating...")
    print("-" * 80)

    transactions_created = 0
    users_affected = set()
    errors = 0

    for session in sessions:
        session_id = session.get("session_id")
        user_id = session.get("user_id")
        book_id = session.get("book_id")
        duration_minutes = session.get("total_time_spent_minutes", 0)
        updated_at = session.get("updated_at", datetime.utcnow())

        if not user_id or not book_id or duration_minutes <= 0:
            continue

        try:
            # Get book title
            book = await db.books.find_one({"_id": book_id})
            book_title = book.get("title") if book else "Unknown Book"

            # Create transaction document directly
            transaction_doc = {
                "_id": str(ObjectId()),
                "user_id": user_id,
                "amount": float(duration_minutes) * 0.10,  # $0.10 per minute (not charged, just for reference)
                "type": "debit",
                "description": f"Listening: {book_title} - {duration_minutes} minutes (migrated - FREE)",
                "metadata": {
                    "service": "inkwave_listening",
                    "book_id": book_id,
                    "book_title": book_title,
                    "duration_minutes": float(duration_minutes),
                    "rate_per_minute": 0.10,
                    "session_id": session_id,
                    "migrated": True,
                    "free": True,  # Mark as free
                    "original_date": updated_at.isoformat()
                },
                "created_at": updated_at,  # Preserve original timestamp
                "updated_at": updated_at
            }

            # Insert directly
            await db.wallet_transactions.insert_one(transaction_doc)

            transactions_created += 1
            users_affected.add(user_id)

            if transactions_created % 10 == 0:
                print(f"  Migrated {transactions_created}/{len(sessions)} sessions...")

        except Exception as e:
            print(f"  ✗ Error migrating session {session_id}: {e}")
            errors += 1

    print(f"\n✓ Created {transactions_created} transaction records")
    print(f"✓ Affected {len(users_affected)} users")
    if errors > 0:
        print(f"⚠ {errors} errors")

    # Update user privacy settings
    print("\nUpdating user privacy settings...")
    result = await db.users.update_many(
        {
            "$or": [
                {"privacy_settings.appear_in_leaderboard": {"$exists": False}},
                {"privacy_settings.appear_in_leaderboard": False}
            ]
        },
        {
            "$set": {
                "privacy_settings.appear_in_leaderboard": True,
                "privacy_settings.leaderboard_display_mode": "anonymous"
            }
        }
    )
    print(f"✓ Updated {result.modified_count} users to opt-in with anonymous mode")

    # Update user stats
    print("\nUpdating user listening stats...")
    leaderboard_service = LeaderboardService(db)

    stats_updated = 0
    for user_id in users_affected:
        try:
            await leaderboard_service.update_user_listening_stats(user_id)
            stats_updated += 1
            if stats_updated % 10 == 0:
                print(f"  Updated {stats_updated}/{len(users_affected)} users...")
        except Exception as e:
            print(f"  ✗ Error updating stats for {user_id}: {e}")

    print(f"✓ Updated stats for {stats_updated} users")

    # Final summary
    print("\n" + "=" * 80)
    print("MIGRATION COMPLETE!")
    print("=" * 80)
    print(f"Sessions migrated:      {transactions_created}")
    print(f"Users affected:         {len(users_affected)}")
    print(f"Privacy settings updated: {result.modified_count}")
    print(f"Stats updated:          {stats_updated}")
    print(f"Errors:                 {errors}")
    print("=" * 80)
    print("\nLeaderboard should now show historical listening data!")
    print("Check: https://inkwave-api.ailabsafrica.com/api/v1/leaderboard?period=all_time&limit=10")


if __name__ == "__main__":
    asyncio.run(main())
