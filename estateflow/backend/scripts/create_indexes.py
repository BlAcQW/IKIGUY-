"""
MongoDB index creation script for EstateFlow.

Creates all necessary indexes for optimal query performance.
Run this after initial deployment or when indexes change.

Usage:
    python scripts/create_indexes.py
"""

import asyncio
import sys
import os
import logging

# Add parent directory to path for app imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_property_indexes(db):
    """
    Create indexes for properties collection.

    Indexes optimize:
    - Organization filtering (multi-tenancy)
    - Status filtering
    - Price range queries
    - Location searches
    - Property type filtering
    - Date sorting
    - Full-text search on name and description
    """
    collection = db["properties"]

    logger.info("Creating indexes for 'properties' collection...")

    # 1. Organization + Status compound index (most common filter)
    await collection.create_index(
        [("organization_id", 1), ("status", 1)],
        name="org_status_idx"
    )
    logger.info("✓ Created org_status_idx")

    # 2. Price index for price range queries
    await collection.create_index(
        [("financial.price_usd", 1)],
        name="price_idx"
    )
    logger.info("✓ Created price_idx")

    # 3. City index for location filtering
    await collection.create_index(
        [("location.city", 1)],
        name="city_idx"
    )
    logger.info("✓ Created city_idx")

    # 4. Property type index
    await collection.create_index(
        [("property_type", 1)],
        name="property_type_idx"
    )
    logger.info("✓ Created property_type_idx")

    # 5. Created date index for sorting by newest
    await collection.create_index(
        [("created_at", -1)],
        name="created_at_idx"
    )
    logger.info("✓ Created created_at_idx")

    # 6. Full-text search index on name and description
    await collection.create_index(
        [("name", "text"), ("description", "text")],
        name="text_search_idx",
        default_language="english"
    )
    logger.info("✓ Created text_search_idx for full-text search")

    # 7. Compound index for organization + property_type + status
    await collection.create_index(
        [("organization_id", 1), ("property_type", 1), ("status", 1)],
        name="org_type_status_idx"
    )
    logger.info("✓ Created org_type_status_idx")

    # 8. Neighborhood index for location filtering
    await collection.create_index(
        [("location.neighborhood", 1)],
        name="neighborhood_idx"
    )
    logger.info("✓ Created neighborhood_idx")

    # 9. Pet policy index for filtering pet-friendly properties
    await collection.create_index(
        [("features.pet_policy", 1)],
        name="pet_policy_idx"
    )
    logger.info("✓ Created pet_policy_idx")

    # 10. Bedrooms index for filtering by bedroom count
    await collection.create_index(
        [("features.bedrooms", 1)],
        name="bedrooms_idx"
    )
    logger.info("✓ Created bedrooms_idx")

    # 11. Compound index for common filter combinations
    # (org + price range + bedrooms + status)
    await collection.create_index(
        [
            ("organization_id", 1),
            ("financial.price_usd", 1),
            ("features.bedrooms", 1),
            ("status", 1)
        ],
        name="org_price_beds_status_idx"
    )
    logger.info("✓ Created org_price_beds_status_idx")

    logger.info(f"✓ All property indexes created successfully")


async def create_exchange_rate_indexes(db):
    """
    Create indexes for exchange_rates collection.

    Indexes optimize:
    - Finding latest rates by base currency
    - TTL for cache expiration
    """
    collection = db["exchange_rates"]

    logger.info("Creating indexes for 'exchange_rates' collection...")

    # 1. Base currency + timestamp index for finding latest rates
    await collection.create_index(
        [("base_currency", 1), ("last_updated", -1)],
        name="base_currency_timestamp_idx"
    )
    logger.info("✓ Created base_currency_timestamp_idx")

    # 2. TTL index to auto-delete old rate entries after 7 days
    # Reason: Keep cache history for 7 days for audit/debugging
    await collection.create_index(
        [("last_updated", 1)],
        name="ttl_idx",
        expireAfterSeconds=7 * 24 * 60 * 60  # 7 days
    )
    logger.info("✓ Created ttl_idx (7-day expiration)")

    logger.info(f"✓ All exchange_rates indexes created successfully")


async def create_invoice_indexes(db):
    """
    Create indexes for invoices collection.

    Indexes optimize:
    - Organization filtering (multi-tenancy)
    - Status filtering
    - Contact and property filtering
    - Date range queries
    - Invoice number lookup
    """
    collection = db["invoices"]

    logger.info("Creating indexes for 'invoices' collection...")

    # 1. Organization + Status compound index (most common filter)
    await collection.create_index(
        [("organization_id", 1), ("status", 1)],
        name="org_status_idx"
    )
    logger.info("✓ Created org_status_idx")

    # 2. Invoice number unique index for fast lookup
    await collection.create_index(
        [("invoice_number", 1)],
        name="invoice_number_idx",
        unique=True
    )
    logger.info("✓ Created invoice_number_idx (unique)")

    # 3. Contact ID index for customer invoice history
    await collection.create_index(
        [("contact_id", 1), ("created_at", -1)],
        name="contact_date_idx"
    )
    logger.info("✓ Created contact_date_idx")

    # 4. Property ID index for property-related invoices
    await collection.create_index(
        [("property_id", 1)],
        name="property_idx"
    )
    logger.info("✓ Created property_idx")

    # 5. Created date index for sorting by newest
    await collection.create_index(
        [("created_at", -1)],
        name="created_at_idx"
    )
    logger.info("✓ Created created_at_idx")

    # 6. Due date index for overdue invoice queries
    await collection.create_index(
        [("due_date", 1), ("status", 1)],
        name="due_date_status_idx"
    )
    logger.info("✓ Created due_date_status_idx")

    # 7. Organization + Created date for org invoice history
    await collection.create_index(
        [("organization_id", 1), ("created_at", -1)],
        name="org_created_idx"
    )
    logger.info("✓ Created org_created_idx")

    # 8. Soft delete filtering
    await collection.create_index(
        [("is_deleted", 1)],
        name="is_deleted_idx"
    )
    logger.info("✓ Created is_deleted_idx")

    logger.info(f"✓ All invoice indexes created successfully")


async def create_booking_action_log_indexes(db):
    """
    Create indexes for booking_action_logs collection.

    Indexes optimize:
    - Audit trail queries by booking ID
    - Organization filtering (multi-tenancy)
    - Admin action history
    - Timestamp sorting
    """
    collection = db["booking_action_logs"]

    logger.info("Creating indexes for 'booking_action_logs' collection...")

    # 1. Booking ID index for audit trail lookup
    await collection.create_index(
        [("booking_id", 1)],
        name="booking_id_idx"
    )
    logger.info("✓ Created booking_id_idx")

    # 2. Organization + Timestamp compound index for org-wide audit queries
    await collection.create_index(
        [("organization_id", 1), ("timestamp", -1)],
        name="org_timestamp_idx"
    )
    logger.info("✓ Created org_timestamp_idx")

    # 3. Admin email index for admin activity tracking
    await collection.create_index(
        [("admin_email", 1)],
        name="admin_email_idx"
    )
    logger.info("✓ Created admin_email_idx")

    logger.info(f"✓ All booking_action_logs indexes created successfully")


async def list_indexes(db):
    """
    List all indexes in properties, exchange_rates, invoices, and booking_action_logs collections.
    """
    logger.info("\n" + "="*60)
    logger.info("Current indexes:")
    logger.info("="*60)

    # Properties collection indexes
    logger.info("\nProperties collection:")
    property_indexes = await db["properties"].index_information()
    for idx_name, idx_info in property_indexes.items():
        logger.info(f"  - {idx_name}: {idx_info.get('key')}")

    # Exchange rates collection indexes
    logger.info("\nExchange Rates collection:")
    rate_indexes = await db["exchange_rates"].index_information()
    for idx_name, idx_info in rate_indexes.items():
        logger.info(f"  - {idx_name}: {idx_info.get('key')}")

    # Invoices collection indexes
    logger.info("\nInvoices collection:")
    invoice_indexes = await db["invoices"].index_information()
    for idx_name, idx_info in invoice_indexes.items():
        logger.info(f"  - {idx_name}: {idx_info.get('key')}")

    # Booking action logs collection indexes
    logger.info("\nBooking Action Logs collection:")
    booking_log_indexes = await db["booking_action_logs"].index_information()
    for idx_name, idx_info in booking_log_indexes.items():
        logger.info(f"  - {idx_name}: {idx_info.get('key')}")

    logger.info("="*60 + "\n")


async def main():
    """Main function to create all indexes."""
    logger.info("Starting MongoDB index creation for EstateFlow...")
    logger.info(f"Database: {settings.MONGODB_URL}")

    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client["estateflow"]

        # Test connection
        await db.command("ping")
        logger.info("✓ Connected to MongoDB")

        # Create indexes
        await create_property_indexes(db)
        await create_exchange_rate_indexes(db)
        await create_invoice_indexes(db)
        await create_booking_action_log_indexes(db)

        # List all indexes
        await list_indexes(db)

        logger.info("✓ All indexes created successfully!")

        # Close connection
        client.close()

    except Exception as e:
        logger.error(f"Error creating indexes: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
