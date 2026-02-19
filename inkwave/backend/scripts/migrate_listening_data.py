#!/usr/bin/env python3
"""
Migration script to backfill historical listening data to wallet transactions.

This script:
1. Migrates listening time from reading_sessions to wallet_transactions
2. Updates user privacy settings to new defaults (opt-in with anonymous mode)
3. Updates user listening stats (denormalized cache)
4. Is idempotent - can run multiple times safely

Usage:
    python migrate_listening_data.py [--dry-run]

Requirements:
- Run from backend directory
- MongoDB must be accessible
- Shared wallet service must be initialized
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Set

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Database
from app.services.wallet_service import InkWaveWalletService
from app.services.leaderboard_service import LeaderboardService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationStats:
    """Track migration statistics."""

    def __init__(self):
        self.sessions_processed = 0
        self.sessions_skipped = 0
        self.transactions_created = 0
        self.users_updated_privacy = 0
        self.users_updated_stats = 0
        self.errors = 0


async def check_migration_flag(db) -> bool:
    """
    Check if migration has already been run.

    Args:
        db: MongoDB database

    Returns:
        True if migration already completed
    """
    flag = await db.migration_flags.find_one({"_id": "listening_data_backfill_v1"})
    return flag is not None


async def set_migration_flag(db):
    """Set flag indicating migration completed."""
    await db.migration_flags.update_one(
        {"_id": "listening_data_backfill_v1"},
        {
            "$set": {
                "completed_at": datetime.utcnow(),
                "status": "completed"
            }
        },
        upsert=True
    )


async def get_migrated_sessions(db) -> Set[str]:
    """
    Get set of session IDs that have already been migrated.

    We track this by checking which sessions have corresponding wallet transactions.

    Args:
        db: MongoDB database

    Returns:
        Set of session IDs already migrated
    """
    migrated = set()

    # Find all wallet transactions for listening
    cursor = db.wallet_transactions.find(
        {"metadata.service": "inkwave_listening"},
        {"metadata.session_id": 1}
    )

    async for tx in cursor:
        session_id = tx.get("metadata", {}).get("session_id")
        if session_id:
            migrated.add(session_id)

    return migrated


async def backfill_listening_transactions(
    db,
    wallet_service: InkWaveWalletService,
    stats: MigrationStats,
    dry_run: bool = False
) -> List[str]:
    """
    Backfill listening time from reading_sessions to wallet_transactions.

    Args:
        db: MongoDB database
        wallet_service: Wallet service instance
        stats: Migration statistics
        dry_run: If True, don't make changes

    Returns:
        List of user IDs that had transactions created
    """
    logger.info("Starting backfill of listening transactions...")

    # Get sessions already migrated
    migrated_sessions = await get_migrated_sessions(db)
    logger.info(f"Found {len(migrated_sessions)} already migrated sessions")

    # Get all reading sessions with listening time
    sessions = await db.reading_sessions.find({
        "total_time_spent_minutes": {"$gt": 0}
    }).to_list(length=None)

    logger.info(f"Found {len(sessions)} reading sessions with listening time")

    affected_users = set()

    for session in sessions:
        session_id = session.get("session_id")

        # Skip if already migrated
        if session_id in migrated_sessions:
            stats.sessions_skipped += 1
            continue

        user_id = session.get("user_id")
        book_id = session.get("book_id")
        duration_minutes = session.get("total_time_spent_minutes", 0)
        updated_at = session.get("updated_at", datetime.utcnow())

        if not user_id or not book_id or duration_minutes <= 0:
            stats.sessions_skipped += 1
            continue

        # Get book title for description
        book = await db.books.find_one({"_id": book_id})
        book_title = book.get("title") if book else None

        if dry_run:
            logger.info(
                f"[DRY RUN] Would create transaction: user={user_id}, book={book_title}, "
                f"duration={duration_minutes}min, date={updated_at}"
            )
            stats.sessions_processed += 1
            affected_users.add(user_id)
            continue

        try:
            # Get or create wallet
            wallet = await wallet_service._get_or_create_wallet(user_id)
            if not wallet:
                logger.error(f"Failed to get/create wallet for user {user_id}")
                stats.errors += 1
                continue

            # Calculate cost: $0.10 per minute
            cost = Decimal(str(duration_minutes)) * Decimal("0.10")

            # Create description
            book_info = book_title or book_id
            description = f"Listening: {book_info} - {duration_minutes:.1f} minutes (migrated)"

            # Create wallet transaction directly through shared service
            # This preserves the created_at timestamp from the session
            # Note: allow_negative=True for historical migration (users didn't have balance requirements then)
            transaction = await wallet_service.shared_wallet.debit(
                wallet_id=wallet.id,
                amount=cost,
                description=description,
                metadata={
                    "service": "inkwave_listening",
                    "book_id": book_id,
                    "duration_minutes": duration_minutes,
                    "rate_per_minute": 0.10,
                    "session_id": session_id,  # Track for deduplication
                    "migrated": True,
                    "original_date": updated_at.isoformat()
                },
                allow_negative=True  # Changed to True for historical migration
            )

            # Update transaction created_at to match session updated_at
            if transaction:
                await db.wallet_transactions.update_one(
                    {"_id": transaction.id},
                    {"$set": {"created_at": updated_at}}
                )

                stats.transactions_created += 1
                affected_users.add(user_id)
                logger.info(
                    f"Created transaction for user {user_id}: {duration_minutes}min "
                    f"on {book_title or book_id}"
                )

        except Exception as e:
            logger.error(f"Error creating transaction for session {session_id}: {e}")
            stats.errors += 1
            continue

        stats.sessions_processed += 1

    logger.info(
        f"Backfill complete: {stats.sessions_processed} sessions processed, "
        f"{stats.transactions_created} transactions created, "
        f"{stats.sessions_skipped} skipped"
    )

    return list(affected_users)


async def update_user_privacy_settings(
    db,
    stats: MigrationStats,
    dry_run: bool = False
):
    """
    Update existing users' privacy settings to new defaults.

    Only updates users who haven't explicitly set leaderboard preferences.

    Args:
        db: MongoDB database
        stats: Migration statistics
        dry_run: If True, don't make changes
    """
    logger.info("Updating user privacy settings...")

    # Find users without explicit leaderboard settings or with old defaults
    users_to_update = await db.users.find({
        "$or": [
            {"privacy_settings.appear_in_leaderboard": {"$exists": False}},
            {"privacy_settings.appear_in_leaderboard": False},
            {"privacy_settings.leaderboard_display_mode": {"$in": [None, "opt_out"]}}
        ]
    }).to_list(length=None)

    logger.info(f"Found {len(users_to_update)} users to update")

    if dry_run:
        logger.info(f"[DRY RUN] Would update {len(users_to_update)} users' privacy settings")
        stats.users_updated_privacy = len(users_to_update)
        return

    for user in users_to_update:
        user_id = user.get("user_id")

        try:
            # Update to new defaults
            await db.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "privacy_settings.appear_in_leaderboard": True,
                        "privacy_settings.leaderboard_display_mode": "anonymous"
                    }
                }
            )

            stats.users_updated_privacy += 1

        except Exception as e:
            logger.error(f"Error updating privacy settings for user {user_id}: {e}")
            stats.errors += 1
            continue

    logger.info(f"Updated privacy settings for {stats.users_updated_privacy} users")


async def update_all_user_stats(
    db,
    leaderboard_service: LeaderboardService,
    affected_users: List[str],
    stats: MigrationStats,
    dry_run: bool = False
):
    """
    Update listening stats for all affected users.

    Args:
        db: MongoDB database
        leaderboard_service: Leaderboard service instance
        affected_users: List of user IDs with new transactions
        stats: Migration statistics
        dry_run: If True, don't make changes
    """
    logger.info(f"Updating stats for {len(affected_users)} users...")

    if dry_run:
        logger.info(f"[DRY RUN] Would update stats for {len(affected_users)} users")
        stats.users_updated_stats = len(affected_users)
        return

    for user_id in affected_users:
        try:
            await leaderboard_service.update_user_listening_stats(user_id)
            stats.users_updated_stats += 1

        except Exception as e:
            logger.error(f"Error updating stats for user {user_id}: {e}")
            stats.errors += 1
            continue

    logger.info(f"Updated stats for {stats.users_updated_stats} users")


async def run_migration(dry_run: bool = False):
    """
    Run the full migration.

    Args:
        dry_run: If True, don't make changes
    """
    print("=" * 80)
    print("INKWAVE LISTENING DATA MIGRATION")
    print("=" * 80)
    logger.info("=" * 80)
    logger.info("INKWAVE LISTENING DATA MIGRATION")
    logger.info("=" * 80)

    if dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    # Initialize database
    logger.info("Connecting to database...")
    await Database.connect()
    db = Database.get_database()
    logger.info("Database connected successfully")

    # Check if migration already completed
    logger.info("Checking migration flag...")
    if not dry_run:
        already_done = await check_migration_flag(db)
        if already_done:
            logger.warning("Migration already completed! Use --force to run again")
            response = input("Continue anyway? (yes/no): ")
            if response.lower() != "yes":
                logger.info("Migration aborted")
                return

    # Initialize services
    print("Initializing wallet service...")
    logger.info("Initializing wallet service...")
    wallet_service = InkWaveWalletService()
    print("Created wallet service instance, calling initialize...")
    await wallet_service.initialize(db=db)
    print("Wallet service initialized!")
    logger.info("Wallet service initialized")

    print("About to initialize leaderboard service...")
    logger.info("Initializing leaderboard service...")
    leaderboard_service = LeaderboardService(db)
    print("Leaderboard service initialized!")
    logger.info("Leaderboard service initialized")

    # Track statistics
    stats = MigrationStats()

    try:
        # Step 1: Backfill listening transactions
        print("\n" + "=" * 80)
        print("STEP 1: Backfill listening transactions")
        print("=" * 80)
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: Backfill listening transactions")
        logger.info("=" * 80)
        affected_users = await backfill_listening_transactions(
            db, wallet_service, stats, dry_run
        )

        # Step 2: Update user privacy settings
        print("\n" + "=" * 80)
        print("STEP 2: Update user privacy settings")
        print("=" * 80)
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: Update user privacy settings")
        logger.info("=" * 80)
        await update_user_privacy_settings(db, stats, dry_run)

        # Step 3: Update user listening stats
        print("\n" + "=" * 80)
        print("STEP 3: Update user listening stats")
        print("=" * 80)
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: Update user listening stats")
        logger.info("=" * 80)
        await update_all_user_stats(db, leaderboard_service, affected_users, stats, dry_run)

        # Set migration flag
        if not dry_run:
            await set_migration_flag(db)

        # Print final statistics
        print("\n" + "=" * 80)
        print("MIGRATION COMPLETE")
        print("=" * 80)
        print(f"Sessions processed:        {stats.sessions_processed}")
        print(f"Sessions skipped:          {stats.sessions_skipped}")
        print(f"Transactions created:      {stats.transactions_created}")
        print(f"Users privacy updated:     {stats.users_updated_privacy}")
        print(f"Users stats updated:       {stats.users_updated_stats}")
        print(f"Errors:                    {stats.errors}")
        print("=" * 80)

        logger.info("\n" + "=" * 80)
        logger.info("MIGRATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Sessions processed:        {stats.sessions_processed}")
        logger.info(f"Sessions skipped:          {stats.sessions_skipped}")
        logger.info(f"Transactions created:      {stats.transactions_created}")
        logger.info(f"Users privacy updated:     {stats.users_updated_privacy}")
        logger.info(f"Users stats updated:       {stats.users_updated_stats}")
        logger.info(f"Errors:                    {stats.errors}")
        logger.info("=" * 80)

        if dry_run:
            print("\nThis was a dry run - no changes were made")
            print("Run without --dry-run to apply changes")
            logger.info("\nThis was a dry run - no changes were made")
            logger.info("Run without --dry-run to apply changes")

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Check for dry-run flag
    dry_run = "--dry-run" in sys.argv

    # Run migration
    asyncio.run(run_migration(dry_run))
