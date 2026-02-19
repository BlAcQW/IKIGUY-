"""
Database module re-export.

Re-exports database functions from app.core.database for convenience.
"""

from app.core.database import (
    get_database,
    connect_to_mongodb,
    close_mongodb_connection,
    init_indexes,
    mongodb_client
)

__all__ = [
    "get_database",
    "connect_to_mongodb",
    "close_mongodb_connection",
    "init_indexes",
    "mongodb_client"
]
