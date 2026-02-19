"""
MongoDB database connection and utilities.

This module provides async MongoDB client setup and database access.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global MongoDB client and database instances
mongodb_client: Optional[AsyncIOMotorClient] = None
mongodb: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongodb() -> None:
    """
    Connect to MongoDB database.

    Creates a connection pool and initializes the global database instance.
    Should be called on application startup.
    """
    global mongodb_client, mongodb

    try:
        logger.info(f"Connecting to MongoDB at {settings.mongodb_url}")
        mongodb_client = AsyncIOMotorClient(
            settings.mongodb_url,
            maxPoolSize=10,
            minPoolSize=1,
        )

        # Ping to verify connection
        await mongodb_client.admin.command("ping")

        mongodb = mongodb_client[settings.mongodb_db_name]

        logger.info(f"Successfully connected to MongoDB database: {settings.mongodb_db_name}")

    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongodb_connection() -> None:
    """
    Close MongoDB database connection.

    Should be called on application shutdown to gracefully close
    the connection pool.
    """
    global mongodb_client

    if mongodb_client:
        logger.info("Closing MongoDB connection")
        mongodb_client.close()
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """
    Get MongoDB database instance.

    Returns:
        AsyncIOMotorDatabase: The MongoDB database instance

    Raises:
        RuntimeError: If database is not initialized
    """
    if mongodb is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongodb() first.")
    return mongodb


async def init_indexes() -> None:
    """
    Initialize database indexes for optimal query performance.

    Creates indexes on commonly queried fields across all collections.
    Should be called after database connection is established.
    """
    db = get_database()

    logger.info("Initializing database indexes...")

    # Drop old problematic index if it exists
    try:
        await db.bus_registrations.drop_index("user_id_1_conference_id_1")
        logger.info("Dropped old index: user_id_1_conference_id_1")
    except Exception as e:
        if "index not found" not in str(e).lower():
            logger.warning(f"Could not drop index user_id_1_conference_id_1: {e}")

    # Users collection indexes
    await db.users.create_index("phone", unique=True)
    await db.users.create_index("branch_id")
    await db.users.create_index("roles")
    await db.users.create_index("created_at")

    # Branches collection indexes
    await db.branches.create_index("name", unique=True)

    # Conferences collection indexes
    await db.conferences.create_index("start_date")
    await db.conferences.create_index("end_date")
    await db.conferences.create_index("registration_open")

    # Bus routes collection indexes
    await db.bus_routes.create_index("conference_id")
    await db.bus_routes.create_index("pickup_location")
    await db.bus_routes.create_index("departure_time")
    await db.bus_routes.create_index("status")

    # Bus registrations collection indexes
    await db.bus_registrations.create_index("user_id")
    await db.bus_registrations.create_index("bus_route_id")
    await db.bus_registrations.create_index("conference_id")
    await db.bus_registrations.create_index("user_phone")
    await db.bus_registrations.create_index("registration_code", unique=True)
    await db.bus_registrations.create_index(
        [("user_phone", 1), ("conference_id", 1)],
        unique=True,
        partialFilterExpression={"user_phone": {"$type": "string"}}
    )  # Reason: Prevent duplicate anonymous bookings per phone+conference (only when phone exists)

    # Conference registrations collection indexes
    # Note: QR codes are generated on-demand, not stored in database
    await db.conference_registrations.create_index("conference_id")
    await db.conference_registrations.create_index("user_id")

    # CRITICAL: Unique index on registration_code for fast check-in lookups
    try:
        await db.conference_registrations.create_index(
            "registration_code",
            unique=True,
            background=True
        )
    except Exception as e:
        # Index may already exist - skip if it does
        if "already exists" not in str(e).lower():
            logger.warning(f"Could not create registration_code index: {e}")
        else:
            logger.info("registration_code index already exists - skipping")
    await db.conference_registrations.create_index(
        [("user_id", 1), ("conference_id", 1)],
        unique=True,
        partialFilterExpression={"user_id": {"$type": "string"}}
    )  # Reason: Prevent duplicate registrations per user+conference (only when user_id exists and is a string)
    await db.conference_registrations.create_index(
        [("user_phone", 1), ("conference_id", 1)],
        unique=True,
        partialFilterExpression={"user_phone": {"$type": "string"}}
    )  # Reason: Prevent duplicate registrations per phone+conference (only when phone exists and is a string)
    await db.conference_registrations.create_index(
        "qr_code",
        unique=True,
        partialFilterExpression={"qr_code": {"$type": "string"}}
    )  # Reason: Ensure unique QR codes when generated (only when qr_code exists and is a string)

    # Speakers collection indexes
    await db.speakers.create_index("conference_id")

    # Notification logs collection indexes
    await db.notification_logs.create_index("user_id")
    await db.notification_logs.create_index("sent_at")
    await db.notification_logs.create_index("channel")
    await db.notification_logs.create_index("delivered")

    # Bus updates collection indexes
    await db.bus_updates.create_index("bus_route_id")
    await db.bus_updates.create_index("sent_at")

    # Session attendance collection indexes
    await db.session_attendance.create_index("session_id")
    await db.session_attendance.create_index("service_id")  # For church service check-ins
    await db.session_attendance.create_index("registration_id")
    await db.session_attendance.create_index("conference_id")
    await db.session_attendance.create_index("checked_in_at")

    # Drop old session attendance unique index if it exists (without partialFilterExpression)
    try:
        await db.session_attendance.drop_index("session_id_1_registration_id_1")
        logger.info("Dropped old index: session_id_1_registration_id_1")
    except Exception as e:
        if "index not found" not in str(e).lower():
            logger.warning(f"Could not drop index session_id_1_registration_id_1: {e}")

    # Create new unique index with partialFilterExpression for session check-ins
    await db.session_attendance.create_index(
        [("session_id", 1), ("registration_id", 1)],
        unique=True,
        partialFilterExpression={"session_id": {"$type": "objectId"}},
        name="session_attendance_session_unique"
    )  # Reason: Prevent duplicate check-ins to the same session

    # Create unique index for service check-ins
    await db.session_attendance.create_index(
        [("service_id", 1), ("registration_id", 1)],
        unique=True,
        partialFilterExpression={"service_id": {"$type": "objectId"}},
        name="session_attendance_service_unique"
    )  # Reason: Prevent duplicate check-ins to the same service

    # Services collection indexes
    await db.services.create_index([("service_date", -1)])  # Recent services first
    await db.services.create_index([("branch_id", 1), ("service_date", -1)])  # Services by branch
    await db.services.create_index("status")
    await db.services.create_index([("service_type", 1), ("service_date", -1)])  # Services by type
    await db.services.create_index(
        "qr_code",
        unique=True,
        sparse=True
    )  # Reason: Ensure unique QR codes for service check-in

    # ============================================
    # Discipleship Tracking System Indexes
    # ============================================

    # Users collection - visitor/discipleship tracking indexes
    await db.users.create_index([("organization_id", 1), ("member_status", 1)])
    await db.users.create_index([("organization_id", 1), ("current_spiritual_stage", 1)])
    await db.users.create_index([("organization_id", 1), ("current_cell_stage", 1)])
    await db.users.create_index([("organization_id", 1), ("current_ministry_stage", 1)])
    await db.users.create_index("cell_group_id")
    await db.users.create_index("zone_id")
    await db.users.create_index("assigned_cell_leader_id")
    await db.users.create_index("first_visit_date")
    await db.users.create_index([("organization_id", 1), ("first_visit_date", 1)])  # For recent visitors query

    # Cell groups collection indexes
    await db.cell_groups.create_index([("organization_id", 1), ("is_active", 1)])
    await db.cell_groups.create_index("zone_id")
    await db.cell_groups.create_index("cell_leader_id")
    await db.cell_groups.create_index([("organization_id", 1), ("zone_id", 1)])  # For zone filtering
    await db.cell_groups.create_index([("organization_id", 1), ("status", 1)])

    # Zones collection indexes
    await db.zones.create_index([("organization_id", 1), ("is_active", 1)])
    await db.zones.create_index("zone_leader_id")
    await db.zones.create_index([("organization_id", 1), ("branch_id", 1)])

    # Departments collection indexes
    await db.departments.create_index([("organization_id", 1), ("is_active", 1)])
    await db.departments.create_index("department_head_id")
    await db.departments.create_index([("organization_id", 1), ("department_type", 1)])
    await db.departments.create_index([("organization_id", 1), ("branch_id", 1)])

    # Journey stages collection indexes
    await db.journey_stages.create_index(
        [("organization_id", 1), ("journey_type", 1), ("stage_order", 1)]
    )
    await db.journey_stages.create_index([("organization_id", 1), ("is_active", 1)])
    await db.journey_stages.create_index(
        [("organization_id", 1), ("stage_name", 1)],
        unique=True
    )  # Reason: Prevent duplicate stage names within organization

    # Scheduled communications collection indexes
    await db.scheduled_communications.create_index([("scheduled_for", 1), ("status", 1)])
    await db.scheduled_communications.create_index([("organization_id", 1), ("user_id", 1)])
    await db.scheduled_communications.create_index([("organization_id", 1), ("status", 1)])
    await db.scheduled_communications.create_index("deduplication_key")
    await db.scheduled_communications.create_index([("status", 1), ("next_retry_at", 1)])  # For retry processing

    logger.info("Database indexes initialized successfully")
