#!/usr/bin/env python3
"""
Migrate uncommitted listening time to transactions.

This script finds all active sessions with uncommitted time (time tracked in session
but not yet recorded as a transaction) and creates transactions for that time.

This ensures:
1. Users get credit for all their listening time
2. Profile and leaderboard show the same hours
3. Old ghost sessions don't inflate profile stats
"""

import sys
import os
sys.path.insert(0, '/opt/kasaai/apps')

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import uuid
from urllib.parse import quote_plus

async def migrate_uncommitted_time():
    """Credit uncommitted time for all users."""

    # Connect to MongoDB
    password = quote_plus("aawwER4444%")
    client = AsyncIOMotorClient(f"mongodb://admin:{password}@127.0.0.1:27017/")
    db = client.inkwave

    print("=" * 80)
    print("UNCOMMITTED TIME MIGRATION")
    print("=" * 80)
    print()

    # Find all active sessions with uncommitted time
    one_hour_ago = datetime.utcnow().timestamp() * 1000 - (60 * 60 * 1000)

    sessions_cursor = db.reading_sessions.find({
        "completed_at": None,
        "$expr": {
            "$gt": [
                "$total_time_spent_minutes",
                {"$ifNull": ["$last_transaction_time", 0]}
            ]
        }
    })

    sessions = await sessions_cursor.to_list(length=None)

    print(f"Found {len(sessions)} sessions with uncommitted time\n")

    user_stats = {}  # Track stats per user
    total_uncommitted = 0
    transactions_created = 0

    for session in sessions:
        user_id = session.get("user_id")
        book_id = session.get("book_id")
        total_time = session.get("total_time_spent_minutes", 0)
        last_tx_time = session.get("last_transaction_time", 0)
        uncommitted = total_time - last_tx_time

        if uncommitted <= 0:
            continue

        # Get book title
        book = await db.books.find_one({"book_id": book_id})
        book_title = book.get("title", "Unknown Book") if book else "Unknown Book"

        # Track user stats
        if user_id not in user_stats:
            user = await db.users.find_one({"user_id": user_id})
            user_stats[user_id] = {
                "email": user.get("email", user_id) if user else user_id,
                "uncommitted_minutes": 0,
                "transactions": 0
            }

        user_stats[user_id]["uncommitted_minutes"] += uncommitted
        user_stats[user_id]["transactions"] += 1
        total_uncommitted += uncommitted

        # Create transaction for uncommitted time
        transaction_doc = {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "amount": float(uncommitted) * 0.10,
            "type": "debit",
            "description": f"Listening: {book_title} - {uncommitted:.1f} minutes (MIGRATED - FREE)",
            "metadata": {
                "service": "inkwave_listening",
                "book_id": book_id,
                "book_title": book_title,
                "duration_minutes": float(uncommitted),
                "rate_per_minute": 0.10,
                "session_id": session.get("session_id"),
                "free": True,
                "migrated": True,  # Mark as migrated
                "migration_date": datetime.utcnow()
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        await db.wallet_transactions.insert_one(transaction_doc)
        transactions_created += 1

        # Update session to mark time as committed
        await db.reading_sessions.update_one(
            {"session_id": session.get("session_id")},
            {
                "$set": {
                    "last_transaction_time": total_time,
                    "last_transaction_at": datetime.utcnow()
                }
            }
        )

    print(f"\n{'=' * 80}")
    print("MIGRATION SUMMARY")
    print(f"{'=' * 80}\n")
    print(f"Total uncommitted time migrated: {total_uncommitted:.1f} min ({total_uncommitted/60:.2f} hrs)")
    print(f"Transactions created: {transactions_created}")
    print(f"Users affected: {len(user_stats)}\n")

    # Show per-user breakdown
    print(f"{'=' * 80}")
    print("PER-USER BREAKDOWN")
    print(f"{'=' * 80}\n")

    for user_id, stats in sorted(user_stats.items(), key=lambda x: x[1]["uncommitted_minutes"], reverse=True)[:20]:
        print(f"{stats['email']}")
        print(f"  Uncommitted: {stats['uncommitted_minutes']:.1f} min ({stats['uncommitted_minutes']/60:.2f} hrs)")
        print(f"  Transactions: {stats['transactions']}")
        print()

    if len(user_stats) > 20:
        print(f"... and {len(user_stats) - 20} more users\n")

    # Update leaderboard cache for all affected users
    print(f"{'=' * 80}")
    print("UPDATING LEADERBOARD CACHE")
    print(f"{'=' * 80}\n")

    updated_count = 0
    for user_id in user_stats.keys():
        try:
            # Calculate all-time listening hours from transactions
            tx_pipeline = [
                {"$match": {"user_id": user_id, "metadata.duration_minutes": {"$exists": True}}},
                {"$group": {"_id": None, "total_minutes": {"$sum": "$metadata.duration_minutes"}}}
            ]
            tx_result = await db.wallet_transactions.aggregate(tx_pipeline).to_list(length=1)
            total_minutes = float(tx_result[0]["total_minutes"]) if tx_result and tx_result[0] else 0.0
            total_hours = total_minutes / 60.0

            # Count completed books
            books_completed = await db.reading_sessions.count_documents({
                "user_id": user_id,
                "progress_percentage": 100
            })

            # Update user's social_stats
            await db.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "social_stats.total_listening_hours": total_hours,
                        "social_stats.books_completed": books_completed,
                        "social_stats.last_stats_update": datetime.utcnow()
                    }
                }
            )

            updated_count += 1
            if updated_count % 10 == 0:
                print(f"Updated {updated_count}/{len(user_stats)} users...")
        except Exception as e:
            print(f"Error updating {user_id}: {e}")

    print(f"\nUpdated leaderboard cache for {updated_count} users\n")

    print(f"{'=' * 80}")
    print("✅ MIGRATION COMPLETE!")
    print(f"{'=' * 80}\n")

    print("Next steps:")
    print("1. Verify stats in profile and leaderboard match")
    print("2. Monitor new sessions to ensure time tracking works")
    print("3. Check a few user accounts to confirm hours are correct")
    print()

    client.close()

if __name__ == "__main__":
    asyncio.run(migrate_uncommitted_time())
