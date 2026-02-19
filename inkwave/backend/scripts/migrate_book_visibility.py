"""
Database migration script for book visibility and access control system.

This script:
1. Adds visibility, is_hidden, and is_deleted fields to existing books
2. Sets default values: visibility="private", is_hidden=False, is_deleted=False
3. Creates indexes for efficient querying
4. Creates indexes for audit logs collection

Run with: python scripts/migrate_book_visibility.py
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import get_db, Database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_database():
    """Initialize database connection."""
    await Database.connect()
    logger.info("Database connected")


async def close_database():
    """Close database connection."""
    await Database.disconnect()
    logger.info("Database disconnected")


async def migrate_books():
    """
    Migrate existing books to add visibility control fields.

    Sets all existing books to:
    - visibility: "private" (safe default)
    - is_hidden: False
    - is_deleted: False
    """
    db = get_db()

    logger.info("Starting book visibility migration...")

    # Get all books
    books_cursor = db.books.find({})
    books = await books_cursor.to_list(length=10000)

    logger.info(f"Found {len(books)} books to migrate")

    migrated_count = 0
    skipped_count = 0

    for book in books:
        book_id = book.get("book_id")

        # Check if already migrated (has visibility field)
        if "visibility" in book:
            logger.debug(f"Skipping {book_id} - already migrated")
            skipped_count += 1
            continue

        # Update book with new fields
        update_result = await db.books.update_one(
            {"book_id": book_id},
            {
                "$set": {
                    "visibility": "private",
                    "visibility_changed_at": None,
                    "visibility_changed_by": None,
                    "is_hidden": False,
                    "hidden_by": None,
                    "hidden_by_email": None,
                    "hidden_at": None,
                    "hidden_reason": None,
                    "is_deleted": False,
                    "deleted_by": None,
                    "deleted_by_email": None,
                    "deleted_at": None,
                    "deletion_reason": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if update_result.modified_count > 0:
            migrated_count += 1
            logger.info(f"Migrated book: {book_id} ({book.get('title')})")
        else:
            logger.warning(f"Failed to migrate book: {book_id}")

    logger.info(f"Migration complete: {migrated_count} migrated, {skipped_count} skipped")
    return migrated_count, skipped_count


async def create_indexes():
    """
    Create indexes for efficient querying.

    Creates indexes for:
    - Books: visibility, is_hidden, is_deleted, compound indexes
    - Audit logs: entity_id, action, actor_id with created_at
    """
    db = get_db()

    logger.info("Creating indexes...")

    # Books collection indexes
    try:
        # Single field indexes
        await db.books.create_index("visibility")
        logger.info("Created index: visibility")

        await db.books.create_index("is_hidden")
        logger.info("Created index: is_hidden")

        await db.books.create_index("is_deleted")
        logger.info("Created index: is_deleted")

        # Compound indexes for common queries
        await db.books.create_index([("uploaded_by", 1), ("visibility", 1)])
        logger.info("Created index: (uploaded_by, visibility)")

        await db.books.create_index([("visibility", 1), ("is_hidden", 1), ("is_deleted", 1)])
        logger.info("Created index: (visibility, is_hidden, is_deleted)")

        await db.books.create_index([("is_hidden", 1), ("hidden_at", -1)])
        logger.info("Created index: (is_hidden, hidden_at)")

    except Exception as e:
        logger.warning(f"Some book indexes may already exist: {e}")

    # Audit logs collection indexes
    try:
        await db.audit_logs.create_index([("entity_id", 1), ("created_at", -1)])
        logger.info("Created index: audit_logs (entity_id, created_at)")

        await db.audit_logs.create_index([("action", 1), ("created_at", -1)])
        logger.info("Created index: audit_logs (action, created_at)")

        await db.audit_logs.create_index([("actor_id", 1), ("created_at", -1)])
        logger.info("Created index: audit_logs (actor_id, created_at)")

    except Exception as e:
        logger.warning(f"Some audit log indexes may already exist: {e}")

    logger.info("Indexes created successfully")


async def verify_migration():
    """
    Verify migration was successful.

    Checks:
    - All books have visibility field
    - All books have is_hidden and is_deleted fields
    - Indexes exist
    """
    db = get_db()

    logger.info("Verifying migration...")

    # Check if all books have required fields
    total_books = await db.books.count_documents({})
    books_with_visibility = await db.books.count_documents({"visibility": {"$exists": True}})
    books_with_is_hidden = await db.books.count_documents({"is_hidden": {"$exists": True}})
    books_with_is_deleted = await db.books.count_documents({"is_deleted": {"$exists": True}})

    logger.info(f"Total books: {total_books}")
    logger.info(f"Books with visibility: {books_with_visibility}")
    logger.info(f"Books with is_hidden: {books_with_is_hidden}")
    logger.info(f"Books with is_deleted: {books_with_is_deleted}")

    if total_books == books_with_visibility == books_with_is_hidden == books_with_is_deleted:
        logger.info("✓ All books have required fields")
    else:
        logger.error("✗ Some books are missing required fields")
        return False

    # Check indexes
    indexes = await db.books.list_indexes().to_list(length=50)
    index_names = [idx.get("name") for idx in indexes]

    logger.info(f"Found {len(indexes)} indexes on books collection")

    required_indexes = ["visibility_1", "is_hidden_1", "is_deleted_1"]
    for required in required_indexes:
        if required in index_names:
            logger.info(f"✓ Index {required} exists")
        else:
            logger.warning(f"✗ Index {required} not found")

    # Check audit logs collection exists
    audit_log_count = await db.audit_logs.count_documents({})
    logger.info(f"Audit logs collection exists with {audit_log_count} documents")

    logger.info("Verification complete")
    return True


async def rollback_migration():
    """
    Rollback migration by removing visibility control fields.

    WARNING: This will remove all visibility settings and audit logs!
    Only use if you need to undo the migration completely.
    """
    logger.warning("ROLLBACK: This will remove all visibility control fields!")
    logger.warning("Press Ctrl+C within 5 seconds to cancel...")

    try:
        await asyncio.sleep(5)
    except KeyboardInterrupt:
        logger.info("Rollback cancelled")
        return

    db = get_db()

    logger.info("Starting rollback...")

    # Remove fields from all books
    result = await db.books.update_many(
        {},
        {
            "$unset": {
                "visibility": "",
                "visibility_changed_at": "",
                "visibility_changed_by": "",
                "is_hidden": "",
                "hidden_by": "",
                "hidden_by_email": "",
                "hidden_at": "",
                "hidden_reason": "",
                "is_deleted": "",
                "deleted_by": "",
                "deleted_by_email": "",
                "deleted_at": "",
                "deletion_reason": ""
            }
        }
    )

    logger.info(f"Removed fields from {result.modified_count} books")

    # Drop indexes
    try:
        await db.books.drop_index("visibility_1")
        await db.books.drop_index("is_hidden_1")
        await db.books.drop_index("is_deleted_1")
        await db.books.drop_index("uploaded_by_1_visibility_1")
        await db.books.drop_index("visibility_1_is_hidden_1_is_deleted_1")
        await db.books.drop_index("is_hidden_1_hidden_at_-1")
        logger.info("Dropped indexes")
    except Exception as e:
        logger.warning(f"Some indexes may not exist: {e}")

    logger.warning("Rollback complete - visibility control removed")


async def main():
    """
    Main migration function.

    Usage:
        python scripts/migrate_book_visibility.py           # Run migration
        python scripts/migrate_book_visibility.py verify    # Verify migration
        python scripts/migrate_book_visibility.py rollback  # Rollback migration
    """
    import sys

    command = sys.argv[1] if len(sys.argv) > 1 else "migrate"

    # Initialize database connection
    await init_database()

    try:
        if command == "migrate":
            logger.info("=== Book Visibility Migration ===")
            logger.info("This will add visibility control fields to all books")
            logger.info("All existing books will be set to 'private' by default")
            logger.info("")

            # Run migration
            migrated, skipped = await migrate_books()

            # Create indexes
            await create_indexes()

            # Verify
            success = await verify_migration()

            if success:
                logger.info("")
                logger.info("=== Migration Complete ===")
                logger.info(f"✓ Migrated {migrated} books")
                logger.info(f"✓ Skipped {skipped} books (already migrated)")
                logger.info(f"✓ Indexes created")
                logger.info("")
                logger.info("Next steps:")
                logger.info("1. Restart the InkWave backend service")
                logger.info("2. Test the visibility features")
                logger.info("3. Authors can now change visibility to 'public' for their books")
            else:
                logger.error("Migration verification failed - please check the logs")
                sys.exit(1)

        elif command == "verify":
            logger.info("=== Verifying Migration ===")
            success = await verify_migration()
            if success:
                logger.info("✓ Migration verified successfully")
            else:
                logger.error("✗ Migration verification failed")
                sys.exit(1)

        elif command == "rollback":
            logger.warning("=== Rolling Back Migration ===")
            await rollback_migration()

        else:
            logger.error(f"Unknown command: {command}")
            logger.info("Usage: python scripts/migrate_book_visibility.py [migrate|verify|rollback]")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        await close_database()
        sys.exit(1)
    finally:
        # Always close database connection
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
