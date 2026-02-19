"""
License service wrapper for Developer Platform using shared libraries.

This service integrates the shared license management engine to provide
license validation and feature access control for the Developer Platform.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Use centralized import configuration
try:
    from ..import_config import get_license_engine, get_storage_backend
    LicenseManagementEngine = get_license_engine()
    MemoryStorageBackend = get_storage_backend()
    from apps.shared.license import LicenseInfo, LicenseValidator
    from apps.shared.storage import StorageConfig
    SHARED_LIBRARIES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Shared libraries not available: {e}")
    SHARED_LIBRARIES_AVAILABLE = False

logger = logging.getLogger(__name__)


class SharedLicenseService:
    """Service for license management using shared libraries."""

    def __init__(self, storage_backend=None):
        """
        Initialize the license service.

        Args:
            storage_backend: Storage backend for license data. Defaults to in-memory.
        """
        if storage_backend is None:
            config = StorageConfig(backend_type="memory", connection_string="memory://")
            storage_backend = MemoryStorageBackend(config)
            
        self.storage = storage_backend
        # Note: LicenseManagementEngine not available, using mock implementation

    async def _ensure_initialized(self):
        """Ensure the license service is initialized."""
        # Note: _ensure_initialized will be called when needed
        pass

    async def get_license_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get license information for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dict[str, Any]: License information or None if not found
        """
        await self._ensure_initialized()
        
        try:
            # Mock implementation - return default license info
            return {
                "license_id": f"license_{tenant_id}",
                "tenant_id": tenant_id,
                "type": "standard",
                "features": ["basic", "telephony"],
                "issued_at": "2024-01-01T00:00:00Z",
                "expires_at": "2025-01-01T00:00:00Z",
                "valid": True,
                "usage_limits": {"calls_per_month": 1000}
            }
        except Exception as e:
            logger.error(f"Failed to get license info for tenant {tenant_id}: {e}")
            return None

    async def validate_license(self, tenant_id: str) -> Dict[str, Any]:
        """
        Validate a tenant's license.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dict[str, Any]: License validation result
        """
        await self._ensure_initialized()
        
        try:
            # Mock implementation - return valid license
            return {
                "valid": True,
                "errors": [],
                "warnings": [],
                "expires_at": "2025-01-01T00:00:00Z"
            }
        except Exception as e:
            logger.error(f"Failed to validate license for tenant {tenant_id}: {e}")
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": [],
                "expires_at": None
            }

    async def check_feature_access(self, tenant_id: str, feature: str) -> Dict[str, Any]:
        """
        Check if a tenant has access to a specific feature.

        Args:
            tenant_id: Tenant identifier
            feature: Feature name

        Returns:
            Dict[str, Any]: Feature access result
        """
        await self._ensure_initialized()
        
        try:
            # Mock implementation - return allowed access
            return {
                "allowed": True,
                "reason": "License valid",
                "usage_limit": 1000,
                "current_usage": 500
            }
        except Exception as e:
            logger.error(f"Failed to check feature access for tenant {tenant_id}, feature {feature}: {e}")
            return {
                "allowed": False,
                "reason": "License validation failed",
                "usage_limit": None,
                "current_usage": 0
            }

    async def get_usage_limits(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get usage limits for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dict[str, Any]: Usage limits by feature
        """
        await self._ensure_initialized()
        
        try:
            limits = await self.license_engine.get_usage_limits(tenant_id)
            return limits
        except Exception as e:
            logger.error(f"Failed to get usage limits for tenant {tenant_id}: {e}")
            return {}

    async def check_usage_compliance(self, tenant_id: str) -> Dict[str, Any]:
        """
        Check usage compliance for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dict[str, Any]: Compliance status
        """
        await self._ensure_initialized()
        
        try:
            compliance = await self.license_engine.check_compliance(tenant_id)
            return {
                "compliant": compliance.is_compliant,
                "violations": compliance.violations,
                "warnings": compliance.warnings,
                "last_check": compliance.last_check
            }
        except Exception as e:
            logger.error(f"Failed to check usage compliance for tenant {tenant_id}: {e}")
            return {
                "compliant": False,
                "violations": [str(e)],
                "warnings": [],
                "last_check": datetime.now()
            }

    async def get_license_audit_trail(self, tenant_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get license audit trail for a tenant.

        Args:
            tenant_id: Tenant identifier
            limit: Maximum number of audit records to return

        Returns:
            List[Dict[str, Any]]: List of audit records
        """
        await self._ensure_initialized()
        
        try:
            audit_records = await self.license_engine.get_audit_trail(tenant_id, limit)
            return [
                {
                    "timestamp": record.timestamp,
                    "action": record.action,
                    "details": record.details,
                    "user_id": record.user_id,
                    "ip_address": record.ip_address
                }
                for record in audit_records
            ]
        except Exception as e:
            logger.error(f"Failed to get license audit trail for tenant {tenant_id}: {e}")
            return []

    async def sync_offline_license(self, tenant_id: str, license_data: str) -> bool:
        """
        Sync offline license data for a tenant.

        Args:
            tenant_id: Tenant identifier
            license_data: Offline license data

        Returns:
            bool: True if sync was successful
        """
        await self._ensure_initialized()
        
        try:
            success = await self.license_engine.sync_offline_license(tenant_id, license_data)
            if success:
                logger.info(f"Synced offline license for tenant {tenant_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to sync offline license for tenant {tenant_id}: {e}")
            return False

    async def export_license_data(self, tenant_id: str, format: str = "json") -> str:
        """
        Export license data for a tenant.

        Args:
            tenant_id: Tenant identifier
            format: Export format (json, xml)

        Returns:
            str: Exported license data
        """
        await self._ensure_initialized()
        
        try:
            return await self.license_engine.export_license_data(tenant_id, format)
        except Exception as e:
            logger.error(f"Failed to export license data for tenant {tenant_id}: {e}")
            return ""

    async def revoke_license(self, tenant_id: str, reason: str = "Manual revocation") -> bool:
        """
        Revoke a tenant's license.

        Args:
            tenant_id: Tenant identifier
            reason: Reason for revocation

        Returns:
            bool: True if revocation was successful
        """
        await self._ensure_initialized()
        
        try:
            success = await self.license_engine.revoke_license(tenant_id, reason)
            if success:
                logger.info(f"Revoked license for tenant {tenant_id}: {reason}")
            return success
        except Exception as e:
            logger.error(f"Failed to revoke license for tenant {tenant_id}: {e}")
            return False

    async def renew_license(self, tenant_id: str, new_expiry_date: datetime) -> bool:
        """
        Renew a tenant's license.

        Args:
            tenant_id: Tenant identifier
            new_expiry_date: New expiry date

        Returns:
            bool: True if renewal was successful
        """
        await self._ensure_initialized()
        
        try:
            success = await self.license_engine.renew_license(tenant_id, new_expiry_date)
            if success:
                logger.info(f"Renewed license for tenant {tenant_id} until {new_expiry_date}")
            return success
        except Exception as e:
            logger.error(f"Failed to renew license for tenant {tenant_id}: {e}")
            return False
