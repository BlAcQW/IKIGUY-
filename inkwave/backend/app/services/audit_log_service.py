"""
Audit log service for tracking admin actions and book visibility changes.

Provides methods for logging actions and querying audit trails.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.audit_log import AuditLog, AuditAction, AuditLogInDB


class AuditLogService:
    """Service for managing audit logs."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize audit log service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.audit_logs

    async def log_action(
        self,
        action: AuditAction,
        entity_id: str,
        actor_id: str,
        actor_email: str,
        actor_role: str,
        reason: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        entity_type: str = "book"
    ) -> str:
        """
        Create an audit log entry.

        Args:
            action: Type of action performed
            entity_id: ID of affected entity (book_id)
            actor_id: User ID performing the action
            actor_email: Email of user performing the action
            actor_role: Role of user (admin, superadmin, author, user)
            reason: Optional reason for the action
            changes: Optional dict of field changes {field: {before: X, after: Y}}
            metadata: Optional additional metadata
            entity_type: Type of entity (default: "book")

        Returns:
            audit_id: ID of created audit log entry
        """
        audit_id = f"audit_{uuid.uuid4().hex[:16]}"

        audit_log = AuditLog(
            audit_id=audit_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role=actor_role,
            reason=reason,
            changes=changes or {},
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )

        await self.collection.insert_one(audit_log.dict())

        return audit_id

    async def get_book_audit_trail(
        self,
        book_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogInDB]:
        """
        Get audit trail for a specific book.

        Args:
            book_id: Book ID to get audit trail for
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of audit log entries, sorted by date (newest first)
        """
        query = {"entity_id": book_id, "entity_type": "book"}

        cursor = self.collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        logs = await cursor.to_list(length=limit)

        return [AuditLogInDB.from_mongo(log) for log in logs]

    async def get_admin_activity(
        self,
        admin_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogInDB]:
        """
        Get admin activity logs with optional filters.

        Args:
            admin_id: Optional filter by admin user_id
            action: Optional filter by action type
            start_date: Optional filter by start date
            end_date: Optional filter by end date
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of audit log entries, sorted by date (newest first)
        """
        query: Dict[str, Any] = {"entity_type": "book"}

        if admin_id:
            query["actor_id"] = admin_id

        if action:
            query["action"] = action.value

        if start_date or end_date:
            date_filter: Dict[str, Any] = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query["created_at"] = date_filter

        cursor = self.collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        logs = await cursor.to_list(length=limit)

        return [AuditLogInDB.from_mongo(log) for log in logs]

    async def get_total_count(
        self,
        book_id: Optional[str] = None,
        admin_id: Optional[str] = None,
        action: Optional[AuditAction] = None
    ) -> int:
        """
        Get total count of audit logs matching filters.

        Args:
            book_id: Optional filter by book_id
            admin_id: Optional filter by admin user_id
            action: Optional filter by action type

        Returns:
            Total count of matching audit logs
        """
        query: Dict[str, Any] = {"entity_type": "book"}

        if book_id:
            query["entity_id"] = book_id

        if admin_id:
            query["actor_id"] = admin_id

        if action:
            query["action"] = action.value

        return await self.collection.count_documents(query)


async def get_audit_log_service(db: AsyncIOMotorDatabase) -> AuditLogService:
    """
    Get audit log service instance.

    Args:
        db: MongoDB database instance

    Returns:
        AuditLogService instance
    """
    return AuditLogService(db)
