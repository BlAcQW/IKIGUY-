"""
Security service that integrates shared security foundation library.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
from uuid import UUID, uuid4
import logging

from apps.shared.security import SecurityEngine, SecurityAudit, SecurityEvent, AccessControl, ComplianceRule, ComplianceViolation
from apps.shared.storage import MemoryStorageBackend

logger = logging.getLogger(__name__)


class SecurityService:
    """Service for security management using shared libraries."""

    def __init__(self, storage_backend=None):
        """
        Initialize the security service.

        Args:
            storage_backend: Storage backend for security data. Defaults to in-memory.
        """
        if storage_backend is None:
            from apps.shared.storage.interfaces import StorageConfig
            config = StorageConfig(backend_type="memory", connection_string="memory://")
            storage_backend = MemoryStorageBackend(config)
        
        self.security_engine = SecurityEngine(storage_backend)
        # Note: _ensure_initialized will be called when needed

    async def _ensure_initialized(self):
        """Ensure the security engine is initialized."""
        try:
            await self.security_engine.get_security_status()
        except Exception:
            # This will trigger initialization
            pass

    async def log_security_event(
        self,
        tenant_id: str,
        event_type: str,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        severity: str = "info"
    ) -> bool:
        """
        Log a security event.

        Args:
            tenant_id: Tenant identifier
            event_type: Type of security event
            user_id: User identifier
            resource: Resource being accessed
            action: Action performed
            metadata: Additional metadata
            severity: Event severity

        Returns:
            bool: True if event was logged successfully
        """
        try:
            event = SecurityEvent(
                event_id=str(uuid4()),
                tenant_id=tenant_id,
                event_type=event_type,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                source="security_service",
                message=f"Security event: {event_type}",
                metadata=metadata or {},
                severity=severity
            )
            return await self.security_engine.record_event(event)
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
            return False

    async def check_access_control(
        self,
        tenant_id: str,
        user_id: str,
        resource: str,
        action: str
    ) -> bool:
        """
        Check access control for a user.

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            resource: Resource being accessed
            action: Action being performed

        Returns:
            bool: True if access is allowed
        """
        try:
            return await self.security_engine.check_access_control(
                tenant_id, user_id, resource, action
            )
        except Exception as e:
            logger.error(f"Failed to check access control: {e}")
            return False

    async def grant_permission(
        self,
        tenant_id: str,
        user_id: str,
        resource: str,
        action: str,
        granted_by: str
    ) -> bool:
        """
        Grant permission to a user.

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            resource: Resource to grant access to
            action: Action to grant
            granted_by: User granting the permission

        Returns:
            bool: True if permission was granted successfully
        """
        try:
            return await self.security_engine.grant_permission(
                tenant_id, user_id, resource, action, granted_by
            )
        except Exception as e:
            logger.error(f"Failed to grant permission: {e}")
            return False

    async def revoke_permission(
        self,
        tenant_id: str,
        user_id: str,
        resource: str,
        action: str,
        revoked_by: str
    ) -> bool:
        """
        Revoke permission from a user.

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            resource: Resource to revoke access from
            action: Action to revoke
            revoked_by: User revoking the permission

        Returns:
            bool: True if permission was revoked successfully
        """
        try:
            return await self.security_engine.revoke_permission(
                tenant_id, user_id, resource, action, revoked_by
            )
        except Exception as e:
            logger.error(f"Failed to revoke permission: {e}")
            return False

    async def get_user_permissions(
        self,
        tenant_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get permissions for a user.

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier

        Returns:
            List[Dict[str, Any]]: User permissions
        """
        try:
            return await self.security_engine.get_user_permissions(tenant_id, user_id)
        except Exception as e:
            logger.error(f"Failed to get user permissions: {e}")
            return []

    async def add_compliance_rule(
        self,
        tenant_id: str,
        rule_name: str,
        rule_type: str,
        conditions: Dict[str, Any],
        actions: List[str],
        enabled: bool = True
    ) -> bool:
        """
        Add a compliance rule.

        Args:
            tenant_id: Tenant identifier
            rule_name: Rule name
            rule_type: Rule type
            conditions: Rule conditions
            actions: Actions to take when rule is triggered
            enabled: Whether the rule is enabled

        Returns:
            bool: True if rule was added successfully
        """
        try:
            rule = ComplianceRule(
                rule_id=str(UUID.uuid4()),
                tenant_id=tenant_id,
                rule_name=rule_name,
                rule_type=rule_type,
                conditions=conditions,
                actions=actions,
                enabled=enabled,
                created_at=datetime.utcnow()
            )
            return await self.security_engine.add_compliance_rule(rule)
        except Exception as e:
            logger.error(f"Failed to add compliance rule: {e}")
            return False

    async def check_compliance(
        self,
        tenant_id: str,
        data: Dict[str, Any]
    ) -> List[ComplianceViolation]:
        """
        Check compliance for data.

        Args:
            tenant_id: Tenant identifier
            data: Data to check for compliance

        Returns:
            List[ComplianceViolation]: Compliance violations found
        """
        try:
            return await self.security_engine.check_compliance(tenant_id, data)
        except Exception as e:
            logger.error(f"Failed to check compliance: {e}")
            return []

    async def get_compliance_report(
        self,
        tenant_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get compliance report for a tenant.

        Args:
            tenant_id: Tenant identifier
            start_date: Start date for report
            end_date: End date for report

        Returns:
            Dict[str, Any]: Compliance report
        """
        try:
            return await self.security_engine.get_compliance_report(
                tenant_id, start_date, end_date
            )
        except Exception as e:
            logger.error(f"Failed to get compliance report: {e}")
            return {}

    async def encrypt_data(
        self,
        data: str,
        key_id: Optional[str] = None
    ) -> str:
        """
        Encrypt data.

        Args:
            data: Data to encrypt
            key_id: Encryption key identifier

        Returns:
            str: Encrypted data
        """
        try:
            return await self.security_engine.encrypt_data(data, key_id)
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            return ""

    async def decrypt_data(
        self,
        encrypted_data: str,
        key_id: Optional[str] = None
    ) -> str:
        """
        Decrypt data.

        Args:
            encrypted_data: Encrypted data to decrypt
            key_id: Encryption key identifier

        Returns:
            str: Decrypted data
        """
        try:
            return await self.security_engine.decrypt_data(encrypted_data, key_id)
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            return ""

    async def rotate_encryption_key(
        self,
        key_id: str,
        new_key_id: Optional[str] = None
    ) -> bool:
        """
        Rotate encryption key.

        Args:
            key_id: Current key identifier
            new_key_id: New key identifier

        Returns:
            bool: True if key rotation was successful
        """
        try:
            return await self.security_engine.rotate_encryption_key(key_id, new_key_id)
        except Exception as e:
            logger.error(f"Failed to rotate encryption key: {e}")
            return False

    async def get_encryption_key_info(
        self,
        key_id: str
    ) -> Dict[str, Any]:
        """
        Get encryption key information.

        Args:
            key_id: Key identifier

        Returns:
            Dict[str, Any]: Key information
        """
        try:
            return await self.security_engine.get_key_info(key_id)
        except Exception as e:
            logger.error(f"Failed to get key info: {e}")
            return {}

    async def get_security_audit_logs(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[SecurityEvent]:
        """
        Get security audit logs.

        Args:
            tenant_id: Tenant identifier
            start_date: Start date for logs
            end_date: End date for logs
            event_type: Event type filter
            user_id: User identifier filter

        Returns:
            List[SecurityEvent]: Security audit logs
        """
        try:
            return await self.security_engine.get_security_audit_logs(
                tenant_id, start_date, end_date, event_type, user_id
            )
        except Exception as e:
            logger.error(f"Failed to get security audit logs: {e}")
            return []

    async def export_security_audit_logs(
        self,
        tenant_id: str,
        format: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Export security audit logs.

        Args:
            tenant_id: Tenant identifier
            format: Export format (json, csv)
            start_date: Start date for export
            end_date: End date for export

        Returns:
            str: Exported audit logs
        """
        try:
            return await self.security_engine.export_audit_logs(
                tenant_id, format, start_date, end_date
            )
        except Exception as e:
            logger.error(f"Failed to export audit logs: {e}")
            return ""

    async def get_security_status(self) -> Dict[str, Any]:
        """
        Get overall security status.

        Returns:
            Dict[str, Any]: Security status
        """
        try:
            return await self.security_engine.get_security_status()
        except Exception as e:
            logger.error(f"Failed to get security status: {e}")
            return {}

    async def run_security_scan(
        self,
        tenant_id: str,
        scan_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Run a security scan.

        Args:
            tenant_id: Tenant identifier
            scan_type: Type of security scan

        Returns:
            Dict[str, Any]: Security scan results
        """
        try:
            return await self.security_engine.run_security_scan(tenant_id, scan_type)
        except Exception as e:
            logger.error(f"Failed to run security scan: {e}")
            return {}
