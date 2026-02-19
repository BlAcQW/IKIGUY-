"""
Audit Service.

Provides audit logging functionality for tracking all actions
on financial records (transactions, invoices, expenses).
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from app.core.database import MongoDB
from app.models.system import AuditLog, AuditLogAction

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for creating and querying audit logs.

    This service handles:
    - Creating audit log entries for all CRUD operations
    - Storing before/after state for modifications
    - Querying audit history for specific resources
    """

    def __init__(self):
        """Initialize the audit service."""
        self._db = None

    @property
    def db(self):
        """Get database connection lazily."""
        if self._db is None:
            self._db = MongoDB.get_database()
        return self._db

    async def log_action(
        self,
        action: AuditLogAction,
        resource_type: str,
        resource_id: str,
        user_id: str,
        organization_id: str,
        user_email: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Log an action to the audit trail.

        Args:
            action: The action performed (create, update, delete, etc.)
            resource_type: Type of resource (transaction, invoice, expense)
            resource_id: ID of the affected resource
            user_id: ID of the user performing the action
            organization_id: Organization ID
            user_email: Optional user email for display
            changes: Optional dict containing before/after state
            ip_address: Optional client IP address
            user_agent: Optional browser user agent
            endpoint: Optional API endpoint
            method: Optional HTTP method
            success: Whether the action succeeded
            error_message: Optional error message if failed
            metadata: Optional additional context

        Returns:
            Created AuditLog entry
        """
        audit_log = AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            method=method,
            changes=changes,
            success=success,
            error_message=error_message,
            metadata=metadata or {},
            organization_id=organization_id,
        )

        audit_dict = audit_log.model_dump()
        await self.db.audit_logs.insert_one(audit_dict)

        logger.info(
            f"Audit log: {action.value} {resource_type} {resource_id} "
            f"by user {user_id} (success={success})"
        )

        return audit_log

    async def log_delete(
        self,
        resource_type: str,
        resource_id: str,
        user_id: str,
        organization_id: str,
        deleted_data: Dict[str, Any],
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> AuditLog:
        """
        Log a deletion action with the deleted data preserved.

        Args:
            resource_type: Type of resource being deleted
            resource_id: ID of the deleted resource
            user_id: User performing the deletion
            organization_id: Organization ID
            deleted_data: Full data of the deleted resource (for recovery)
            user_email: Optional user email
            ip_address: Optional client IP
            reason: Optional reason for deletion

        Returns:
            Created AuditLog entry
        """
        changes = {
            "before": deleted_data,
            "after": None,
        }

        metadata = {}
        if reason:
            metadata["deletion_reason"] = reason

        return await self.log_action(
            action=AuditLogAction.DELETE,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            organization_id=organization_id,
            user_email=user_email,
            changes=changes,
            ip_address=ip_address,
            method="DELETE",
            metadata=metadata,
        )

    async def log_create(
        self,
        resource_type: str,
        resource_id: str,
        user_id: str,
        organization_id: str,
        created_data: Dict[str, Any],
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """
        Log a creation action.

        Args:
            resource_type: Type of resource created
            resource_id: ID of the new resource
            user_id: User who created it
            organization_id: Organization ID
            created_data: Data of the created resource
            user_email: Optional user email
            ip_address: Optional client IP

        Returns:
            Created AuditLog entry
        """
        changes = {
            "before": None,
            "after": created_data,
        }

        return await self.log_action(
            action=AuditLogAction.CREATE,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            organization_id=organization_id,
            user_email=user_email,
            changes=changes,
            ip_address=ip_address,
            method="POST",
        )

    async def log_update(
        self,
        resource_type: str,
        resource_id: str,
        user_id: str,
        organization_id: str,
        before_data: Dict[str, Any],
        after_data: Dict[str, Any],
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """
        Log an update action.

        Args:
            resource_type: Type of resource updated
            resource_id: ID of the updated resource
            user_id: User who made the update
            organization_id: Organization ID
            before_data: State before update
            after_data: State after update
            user_email: Optional user email
            ip_address: Optional client IP

        Returns:
            Created AuditLog entry
        """
        changes = {
            "before": before_data,
            "after": after_data,
        }

        return await self.log_action(
            action=AuditLogAction.UPDATE,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            organization_id=organization_id,
            user_email=user_email,
            changes=changes,
            ip_address=ip_address,
            method="PATCH",
        )

    async def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        organization_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list:
        """
        Get audit history for a specific resource.

        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
            organization_id: Organization ID
            skip: Pagination skip
            limit: Pagination limit

        Returns:
            List of audit log entries
        """
        query = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "organization_id": organization_id,
        }

        cursor = self.db.audit_logs.find(query).skip(skip).limit(limit).sort("created_at", -1)
        return await cursor.to_list(length=limit)

    async def get_deleted_resources(
        self,
        resource_type: str,
        organization_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list:
        """
        Get all deleted resources of a given type.

        Useful for viewing deletion history or potential recovery.

        Args:
            resource_type: Type of resource (transaction, invoice, expense)
            organization_id: Organization ID
            start_date: Optional filter by deletion date
            end_date: Optional filter by deletion date
            skip: Pagination skip
            limit: Pagination limit

        Returns:
            List of deletion audit logs with original data
        """
        query = {
            "action": AuditLogAction.DELETE.value,
            "resource_type": resource_type,
            "organization_id": organization_id,
        }

        if start_date or end_date:
            query["created_at"] = {}
            if start_date:
                query["created_at"]["$gte"] = start_date
            if end_date:
                query["created_at"]["$lte"] = end_date

        cursor = self.db.audit_logs.find(query).skip(skip).limit(limit).sort("created_at", -1)
        return await cursor.to_list(length=limit)

    async def get_user_actions(
        self,
        user_id: str,
        organization_id: str,
        action: Optional[AuditLogAction] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list:
        """
        Get all actions performed by a specific user.

        Args:
            user_id: User ID
            organization_id: Organization ID
            action: Optional filter by action type
            skip: Pagination skip
            limit: Pagination limit

        Returns:
            List of audit log entries for the user
        """
        query = {
            "user_id": user_id,
            "organization_id": organization_id,
        }

        if action:
            query["action"] = action.value

        cursor = self.db.audit_logs.find(query).skip(skip).limit(limit).sort("created_at", -1)
        return await cursor.to_list(length=limit)


# Singleton instance
_audit_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    """
    Get the audit service singleton.

    Returns:
        AuditService instance
    """
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
