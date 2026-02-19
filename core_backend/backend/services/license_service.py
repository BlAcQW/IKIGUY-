"""
License service that integrates shared license management library.
"""

import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from uuid import UUID
import json
import logging

# Use centralized import configuration
from .import_config import get_license_engine, get_storage_backend
LicenseManagementEngine = get_license_engine()
MemoryStorageBackend = get_storage_backend()
from apps.shared.license import LicenseInfo, LicenseFeatures, LicenseLimits, LicenseStatus

logger = logging.getLogger(__name__)


class LicenseService:
    """Service for managing licenses using shared libraries."""

    def __init__(self, storage_backend=None):
        """
        Initialize the license service.

        Args:
            storage_backend: Storage backend for license data. Defaults to in-memory.
        """
        if storage_backend is None:
            from apps.shared.storage.interfaces import StorageConfig
            config = StorageConfig(backend_type="memory", connection_string="memory://")
            storage_backend = MemoryStorageBackend(config)
        
        self.license_engine = LicenseManagementEngine(storage_backend)
        # Note: _ensure_initialized will be called when needed

    async def _ensure_initialized(self):
        """Ensure the license engine is initialized."""
        try:
            await self.license_engine.get_license_status("test")
        except Exception:
            # This will trigger initialization
            pass

    async def create_license(
        self,
        tenant_id: str,
        license_key: str,
        features: Dict[str, bool],
        limits: Dict[str, int],
        expiry_date: Optional[date] = None,
        license_type: str = "standard",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a new license for a tenant.

        Args:
            tenant_id: Tenant identifier
            license_key: License key
            features: Features enabled for this license
            limits: Usage limits for this license
            expiry_date: License expiry date
            license_type: License type (basic, standard, enterprise, industry)
            metadata: Additional metadata

        Returns:
            bool: True if license was created successfully
        """
        try:
            # Convert features dict to list of enabled features
            enabled_features = [feature for feature, enabled in features.items() if enabled]
            
            # Convert date to datetime if provided
            expiry_datetime = None
            if expiry_date:
                expiry_datetime = datetime.combine(expiry_date, datetime.min.time())
            
            # If a specific license key is provided, we need to create the license manually
            # since the engine always generates a new key
            if license_key:
                # Create license record manually with the provided key
                await self.license_engine.storage.insert("licenses", {
                    "license_key": license_key,
                    "tenant_id": tenant_id,
                    "license_type": license_type,
                    "features": json.dumps(enabled_features),
                    "limits": json.dumps(limits),
                    "issued_date": datetime.utcnow().isoformat(),
                    "expiry_date": expiry_datetime.isoformat() if expiry_datetime else (datetime.utcnow() + timedelta(days=365)).isoformat(),
                    "is_active": True,
                    "max_users": limits.get("max_users", 1),
                    "max_calls_per_month": limits.get("max_calls_per_month", 1000),
                    "max_storage_gb": limits.get("max_storage_gb", 10),
                    "support_level": "basic",
                    "customizations": "{}"
                })
                
                # Initialize status record
                await self.license_engine._update_license_status(tenant_id, "active")
                
                return True
            else:
                # Use the engine's create_license method to generate a key
                license_key_generated = await self.license_engine.create_license(
                    tenant_id=tenant_id,
                    license_type=license_type,
                    features=enabled_features,
                    limits=limits,
                    expiry_date=expiry_datetime
                )
                return license_key_generated is not None
        except Exception as e:
            logger.error(f"Failed to create license: {e}")
            return False

    async def validate_license(
        self,
        tenant_id: str,
        license_key: str
    ) -> Optional[LicenseInfo]:
        """
        Validate a license for a tenant.

        Args:
            tenant_id: Tenant identifier
            license_key: License key to validate

        Returns:
            LicenseInfo: License information if valid
        """
        try:
            return await self.license_engine.validate_license(license_key)
        except Exception as e:
            logger.error(f"Failed to validate license: {e}")
            return None

    async def get_license_info(
        self,
        tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get license information for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dict[str, Any]: License information or None if no license found
        """
        try:
            status = await self.license_engine.get_license_status(tenant_id)
            # Return None if no license found
            if status.get("status") == "no_license":
                return None
            return status
        except Exception as e:
            logger.error(f"Failed to get license info: {e}")
            return None

    async def check_feature_access(
        self,
        tenant_id: str,
        feature: str
    ) -> bool:
        """
        Check if a tenant has access to a feature.

        Args:
            tenant_id: Tenant identifier
            feature: Feature to check

        Returns:
            bool: True if feature is accessible
        """
        try:
            return await self.license_engine.check_feature_access(tenant_id, feature)
        except Exception as e:
            logger.error(f"Failed to check feature access: {e}")
            return False

    async def check_usage_limits(
        self,
        tenant_id: str,
        feature: str,
        quantity: int = 1
    ) -> bool:
        """
        Check if usage is within license limits.

        Args:
            tenant_id: Tenant identifier
            feature: Feature to check
            quantity: Quantity to check

        Returns:
            bool: True if within limits
        """
        try:
            return await self.license_engine.check_usage_limits(tenant_id, feature, quantity)
        except Exception as e:
            logger.error(f"Failed to check usage limits: {e}")
            return False

    async def revoke_license(
        self,
        tenant_id: str,
        reason: str = "Manual revocation"
    ) -> bool:
        """
        Revoke a license for a tenant.

        Args:
            tenant_id: Tenant identifier
            reason: Reason for revocation

        Returns:
            bool: True if license was revoked successfully
        """
        try:
            return await self.license_engine.revoke_license(tenant_id)
        except Exception as e:
            logger.error(f"Failed to revoke license: {e}")
            return False

    async def renew_license(
        self,
        tenant_id: str,
        new_expiry_date: date
    ) -> bool:
        """
        Renew a license for a tenant.

        Args:
            tenant_id: Tenant identifier
            new_expiry_date: New expiry date

        Returns:
            bool: True if license was renewed successfully
        """
        try:
            return await self.license_engine.renew_license(tenant_id, new_expiry_date)
        except Exception as e:
            logger.error(f"Failed to renew license: {e}")
            return False

    async def get_license_compliance(
        self,
        tenant_id: str
    ) -> Optional[LicenseStatus]:
        """
        Get license compliance status for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            LicenseStatus: License compliance status
        """
        try:
            return await self.license_engine.get_license_compliance(tenant_id)
        except Exception as e:
            logger.error(f"Failed to get license compliance: {e}")
            return None

    async def sync_license_data(
        self,
        tenant_id: str,
        sync_data: Dict[str, Any]
    ) -> bool:
        """
        Sync license data for offline deployments.

        Args:
            tenant_id: Tenant identifier
            sync_data: License sync data

        Returns:
            bool: True if sync was successful
        """
        try:
            return await self.license_engine.sync_license_data(tenant_id, sync_data)
        except Exception as e:
            logger.error(f"Failed to sync license data: {e}")
            return False

    async def export_license_data(
        self,
        tenant_id: str,
        format: str = "json"
    ) -> str:
        """
        Export license data for a tenant.

        Args:
            tenant_id: Tenant identifier
            format: Export format (json, yaml)

        Returns:
            str: Exported license data
        """
        try:
            return await self.license_engine.export_license_data(tenant_id, format)
        except Exception as e:
            logger.error(f"Failed to export license data: {e}")
            return ""

    async def import_license_data(
        self,
        tenant_id: str,
        data: str,
        format: str = "json"
    ) -> bool:
        """
        Import license data for a tenant.

        Args:
            tenant_id: Tenant identifier
            data: License data to import
            format: Import format (json, yaml)

        Returns:
            bool: True if import was successful
        """
        try:
            return await self.license_engine.import_license_data(tenant_id, data, format)
        except Exception as e:
            logger.error(f"Failed to import license data: {e}")
            return False

    async def get_license_audit_trail(
        self,
        tenant_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get license audit trail for a tenant.

        Args:
            tenant_id: Tenant identifier
            start_date: Start date for audit trail
            end_date: End date for audit trail

        Returns:
            List[Dict[str, Any]]: Audit trail entries
        """
        try:
            return await self.license_engine.get_license_audit_trail(
                tenant_id, start_date, end_date
            )
        except Exception as e:
            logger.error(f"Failed to get license audit trail: {e}")
            return []
