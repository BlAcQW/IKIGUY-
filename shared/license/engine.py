"""
License Management Engine

This module implements the core license management engine that provides
license validation, feature access control, usage tracking, and offline sync.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

from .interfaces import LicenseValidator, LicenseInfo
from .models import (
    LicenseFeatures, LicenseLimits, LicenseStatus,
    LicenseSync, LicenseAudit, LicenseCompliance
)
from ..storage.interfaces import StorageBackend

logger = logging.getLogger(__name__)


class LicenseManagementEngine(LicenseValidator):
    """
    License management engine implementation
    
    Provides comprehensive license validation, feature access control,
    usage tracking, and offline synchronization capabilities.
    """
    
    def __init__(self, storage_backend: StorageBackend):
        """
        Initialize license management engine
        
        Args:
            storage_backend: Storage backend for license data
        """
        super().__init__(storage_backend)
        # Note: _initialize_storage will be called when first async method is called
        
        # Default license configurations
        self._default_features = LicenseFeatures(
            basic_features=["voice_calls", "basic_analytics"],
            standard_features=["voice_calls", "basic_analytics", "advanced_analytics", "custom_branding"],
            enterprise_features=["voice_calls", "basic_analytics", "advanced_analytics", "custom_branding", 
                               "ai_features", "custom_integrations", "priority_support"],
            industry_features=["voice_calls", "basic_analytics", "advanced_analytics", "custom_branding",
                             "ai_features", "custom_integrations", "priority_support", "compliance_tools",
                             "industry_specific_features"]
        )
        
        self._default_limits = LicenseLimits(
            basic_limits={"max_calls_per_month": 1000, "max_users": 5, "max_storage_gb": 10},
            standard_limits={"max_calls_per_month": 10000, "max_users": 25, "max_storage_gb": 100},
            enterprise_limits={"max_calls_per_month": 100000, "max_users": 100, "max_storage_gb": 1000},
            industry_limits={"max_calls_per_month": 1000000, "max_users": 500, "max_storage_gb": 10000}
        )
    
    async def _initialize_storage(self) -> None:
        """Initialize storage tables for license management"""
        try:
            # Create license tables
            await self.storage.create_table("licenses", {
                "license_key": "TEXT PRIMARY KEY",
                "tenant_id": "TEXT",
                "license_type": "TEXT",
                "features": "TEXT",  # JSON string
                "limits": "TEXT",    # JSON string
                "issued_date": "TEXT",
                "expiry_date": "TEXT",
                "is_active": "BOOLEAN",
                "max_users": "INTEGER",
                "max_calls_per_month": "INTEGER",
                "max_storage_gb": "INTEGER",
                "support_level": "TEXT",
                "customizations": "TEXT"  # JSON string
            })
            
            await self.storage.create_table("license_usage", {
                "id": "TEXT PRIMARY KEY",
                "tenant_id": "TEXT",
                "feature": "TEXT",
                "usage_date": "TEXT",
                "usage_amount": "INTEGER",
                "recorded_at": "TEXT"
            })
            
            await self.storage.create_table("license_status", {
                "tenant_id": "TEXT PRIMARY KEY",
                "license_key": "TEXT",
                "status": "TEXT",
                "last_check": "TEXT",
                "next_check": "TEXT",
                "usage_summary": "TEXT",  # JSON string
                "limit_summary": "TEXT",  # JSON string
                "warnings": "TEXT",       # JSON string
                "errors": "TEXT"          # JSON string
            })
            
            await self.storage.create_table("license_sync", {
                "sync_id": "TEXT PRIMARY KEY",
                "tenant_id": "TEXT",
                "sync_type": "TEXT",
                "status": "TEXT",
                "started_at": "TEXT",
                "completed_at": "TEXT",
                "data_synced": "TEXT",    # JSON string
                "errors": "TEXT"          # JSON string
            })
            
            await self.storage.create_table("license_audit", {
                "audit_id": "TEXT PRIMARY KEY",
                "tenant_id": "TEXT",
                "action": "TEXT",
                "timestamp": "TEXT",
                "user_id": "TEXT",
                "details": "TEXT",        # JSON string
                "ip_address": "TEXT",
                "user_agent": "TEXT"
            })
            
            logger.info("License management storage initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize license storage: {str(e)}")
            raise
    
    async def _ensure_initialized(self) -> None:
        """Ensure storage is initialized"""
        if not await self.storage.table_exists("licenses"):
            await self._initialize_storage()
    
    async def validate_license(self, license_key: str) -> LicenseInfo:
        """
        Validate license and return license info
        
        Args:
            license_key: License key to validate
            
        Returns:
            LicenseInfo: License information
            
        Raises:
            ValueError: If license key is invalid or expired
        """
        await self._ensure_initialized()
        
        try:
            # Retrieve license from storage
            results = await self.storage.query(
                "licenses", 
                {"license_key": license_key}
            )
            
            if not results:
                raise ValueError(f"License key not found: {license_key}")
            
            result = results[0]  # Get the first (and should be only) result
            
            # Parse license data
            license_data = dict(result)
            features = json.loads(license_data.get("features", "[]"))
            limits = json.loads(license_data.get("limits", "{}"))
            customizations = json.loads(license_data.get("customizations", "{}"))
            
            # Create LicenseInfo object
            license_info = LicenseInfo(
                license_key=license_data["license_key"],
                tenant_id=license_data["tenant_id"],
                license_type=license_data["license_type"],
                features=features,
                limits=limits,
                issued_date=datetime.fromisoformat(license_data["issued_date"]),
                expiry_date=datetime.fromisoformat(license_data["expiry_date"]) if license_data.get("expiry_date") else None,
                is_active=license_data["is_active"],
                max_users=license_data["max_users"],
                max_calls_per_month=license_data["max_calls_per_month"],
                max_storage_gb=license_data["max_storage_gb"],
                support_level=license_data["support_level"],
                customizations=customizations
            )
            
            # Check if license is expired
            if license_info.expiry_date and datetime.utcnow() > license_info.expiry_date:
                license_info.is_active = False
                await self._update_license_status(license_info.tenant_id, "expired")
                raise ValueError(f"License expired on {license_info.expiry_date}")
            
            # Check if license is revoked
            if not license_info.is_active:
                await self._update_license_status(license_info.tenant_id, "revoked")
                raise ValueError(f"License is not active for tenant {license_info.tenant_id}")
            
            # Update last check time
            await self._update_license_status(license_info.tenant_id, "active")
            
            logger.info(f"License validated successfully for tenant: {license_info.tenant_id}")
            return license_info
            
        except Exception as e:
            logger.error(f"License validation failed: {str(e)}")
            raise
    
    async def check_feature_access(self, tenant_id: str, feature: str) -> bool:
        """
        Check if tenant has access to feature
        
        Args:
            tenant_id: Tenant identifier
            feature: Feature name
            
        Returns:
            bool: True if feature is accessible
        """
        await self._ensure_initialized()
        
        try:
            # Get tenant's license
            results = await self.storage.query(
                "licenses",
                {"tenant_id": tenant_id}
            )
            
            if not results:
                logger.warning(f"No license found for tenant: {tenant_id}")
                return False
            
            result = results[0]  # Get the first (and should be only) result
            
            license_data = dict(result)
            
            # Check if license is active
            if not license_data.get("is_active", False):
                logger.warning(f"License is not active for tenant: {tenant_id}")
                return False
            
            features = json.loads(license_data.get("features", "[]"))
            
            # Check if feature is in license
            has_access = feature in features
            
            # Log access check
            await self._audit_action(
                tenant_id=tenant_id,
                action="feature_access_check",
                details={"feature": feature, "has_access": has_access}
            )
            
            logger.info(f"Feature access check for {feature}: {has_access} (tenant: {tenant_id})")
            return has_access
            
        except Exception as e:
            logger.error(f"Feature access check failed: {str(e)}")
            return False
    
    async def record_usage(self, tenant_id: str, feature: str, usage: int) -> bool:
        """
        Record feature usage for license tracking
        
        Args:
            tenant_id: Tenant identifier
            feature: Feature name
            usage: Usage amount
            
        Returns:
            bool: True if usage was recorded successfully
        """
        await self._ensure_initialized()
        
        try:
            # Check if license is active and feature is accessible
            if not await self.check_feature_access(tenant_id, feature):
                logger.warning(f"Feature access denied for tenant {tenant_id}, feature {feature}")
                return False
            
            # Check if usage is within limits
            if not await self.check_usage_limits(tenant_id, feature, usage):
                logger.warning(f"Usage limit exceeded for tenant {tenant_id}, feature {feature}")
                return False
            
            # Record usage
            usage_id = str(uuid4())
            await self.storage.insert("license_usage", {
                "id": usage_id,
                "tenant_id": tenant_id,
                "feature": feature,
                "usage_date": datetime.utcnow().isoformat(),
                "usage_amount": usage,
                "recorded_at": datetime.utcnow().isoformat()
            })
            
            # Update usage summary
            await self._update_usage_summary(tenant_id, feature, usage)
            
            # Audit usage recording
            await self._audit_action(
                tenant_id=tenant_id,
                action="usage_recorded",
                details={"feature": feature, "usage": usage}
            )
            
            logger.info(f"Usage recorded for tenant {tenant_id}, feature {feature}: {usage}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record usage: {str(e)}")
            return False
    
    async def sync_license(self, tenant_id: str) -> bool:
        """
        Sync license with on-premise deployment
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            bool: True if sync was successful
        """
        await self._ensure_initialized()
        
        try:
            sync_id = str(uuid4())
            
            # Create sync record
            await self.storage.insert("license_sync", {
                "sync_id": sync_id,
                "tenant_id": tenant_id,
                "sync_type": "full",
                "status": "in_progress",
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": None,
                "data_synced": "{}",
                "errors": "[]"
            })
            
            # Get license data
            license_results = await self.storage.query(
                "licenses",
                {"tenant_id": tenant_id}
            )
            
            if not license_results:
                await self._update_sync_status(sync_id, "failed", ["License not found"])
                return False
            
            license_result = license_results[0]  # Get the first result
            
            # Get usage data
            usage_result = await self.storage.query(
                "license_usage",
                {"tenant_id": tenant_id}
            )
            
            # Get status data
            status_results = await self.storage.query(
                "license_status",
                {"tenant_id": tenant_id}
            )
            status_result = status_results[0] if status_results else None
            
            # Prepare sync data
            sync_data = {
                "license": dict(license_result) if license_result else None,
                "usage": [dict(usage) for usage in usage_result] if usage_result else [],
                "status": dict(status_result) if status_result else None,
                "sync_timestamp": datetime.utcnow().isoformat()
            }
            
            # Update sync record
            await self.storage.update("license_sync", 
                {"sync_id": sync_id},
                {
                    "status": "completed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "data_synced": json.dumps(sync_data),
                    "errors": "[]"
                }
            )
            
            # Audit sync operation
            await self._audit_action(
                tenant_id=tenant_id,
                action="license_sync",
                details={"sync_id": sync_id, "sync_type": "full"}
            )
            
            logger.info(f"License sync completed for tenant: {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"License sync failed: {str(e)}")
            if 'sync_id' in locals():
                await self._update_sync_status(sync_id, "failed", [str(e)])
            return False
    
    async def get_license_status(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get current license status
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Dict[str, Any]: License status information
        """
        await self._ensure_initialized()
        
        try:
            # Get license status
            results = await self.storage.query(
                "license_status",
                {"tenant_id": tenant_id}
            )
            
            if not results:
                return {
                    "tenant_id": tenant_id,
                    "status": "no_license",
                    "last_check": None,
                    "next_check": None,
                    "usage_summary": {},
                    "limit_summary": {},
                    "warnings": ["No license found"],
                    "errors": []
                }
            
            result = results[0]  # Get the first result
            status_data = dict(result)
            
            return {
                "tenant_id": status_data["tenant_id"],
                "license_key": status_data["license_key"],
                "status": status_data["status"],
                "last_check": status_data["last_check"],
                "next_check": status_data["next_check"],
                "usage_summary": json.loads(status_data.get("usage_summary", "{}")),
                "limit_summary": json.loads(status_data.get("limit_summary", "{}")),
                "warnings": json.loads(status_data.get("warnings", "[]")),
                "errors": json.loads(status_data.get("errors", "[]"))
            }
            
        except Exception as e:
            logger.error(f"Failed to get license status: {str(e)}")
            return {
                "tenant_id": tenant_id,
                "status": "error",
                "last_check": None,
                "next_check": None,
                "usage_summary": {},
                "limit_summary": {},
                "warnings": [],
                "errors": [str(e)]
            }
    
    async def check_usage_limits(self, tenant_id: str, feature: str, requested_usage: int) -> bool:
        """
        Check if usage is within limits
        
        Args:
            tenant_id: Tenant identifier
            feature: Feature name
            requested_usage: Requested usage amount
            
        Returns:
            bool: True if usage is within limits
        """
        await self._ensure_initialized()
        
        try:
            # Get license limits
            results = await self.storage.query(
                "licenses",
                {"tenant_id": tenant_id}
            )
            
            if not results:
                return False
            
            result = results[0]  # Get the first result
            
            license_data = dict(result)
            limits = json.loads(license_data.get("limits", "{}"))
            
            # Get current usage for this month
            current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            usage_result = await self.storage.query(
                "license_usage",
                {"tenant_id": tenant_id, "feature": feature}
            )
            
            # Filter by date in code since MemoryStorageBackend doesn't support complex filters
            current_month_str = current_month.isoformat()
            usage_result = [usage for usage in usage_result if usage.get("usage_date", "") >= current_month_str]
            
            current_usage = sum(usage["usage_amount"] for usage in usage_result) if usage_result else 0
            total_usage = current_usage + requested_usage
            
            # Check against limits - if no specific limit for this feature, allow unlimited
            feature_limit = limits.get(feature, -1)  # -1 means unlimited
            if feature_limit > 0 and total_usage > feature_limit:
                logger.warning(f"Usage limit exceeded for {feature}: {total_usage} > {feature_limit}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Usage limit check failed: {str(e)}")
            return False
    
    async def get_remaining_quota(self, tenant_id: str, feature: str) -> int:
        """
        Get remaining quota for feature
        
        Args:
            tenant_id: Tenant identifier
            feature: Feature name
            
        Returns:
            int: Remaining quota
        """
        await self._ensure_initialized()
        
        try:
            # Get license limits
            results = await self.storage.query(
                "licenses",
                {"tenant_id": tenant_id},
                limit=1
            )
            result = results[0] if results else None
            
            if not result:
                return 0
            
            license_data = dict(result)
            limits = json.loads(license_data.get("limits", "{}"))
            feature_limit = limits.get(feature, 0)
            
            if feature_limit == 0:
                return -1  # Unlimited
            
            # Get current usage for this month
            current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            usage_result = await self.storage.query(
                "license_usage",
                {"tenant_id": tenant_id, "feature": feature}
            )
            
            # Filter by date in code since MemoryStorageBackend doesn't support complex filters
            current_month_str = current_month.isoformat()
            usage_result = [usage for usage in usage_result if usage.get("usage_date", "") >= current_month_str]
            
            current_usage = sum(usage["usage_amount"] for usage in usage_result) if usage_result else 0
            remaining = max(0, feature_limit - current_usage)
            
            return remaining
            
        except Exception as e:
            logger.error(f"Failed to get remaining quota: {str(e)}")
            return 0
    
    async def revoke_license(self, tenant_id: str) -> bool:
        """
        Revoke license for tenant
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            bool: True if license was revoked successfully
        """
        await self._ensure_initialized()
        
        try:
            # Update license status
            await self.storage.update("licenses",
                {"tenant_id": tenant_id},
                {"is_active": False}
            )
            
            # Update status record
            await self._update_license_status(tenant_id, "revoked")
            
            # Audit revocation
            await self._audit_action(
                tenant_id=tenant_id,
                action="license_revoked",
                details={"revoked_at": datetime.utcnow().isoformat()}
            )
            
            logger.info(f"License revoked for tenant: {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke license: {str(e)}")
            return False
    
    async def renew_license(self, tenant_id: str, new_expiry_date: datetime) -> bool:
        """
        Renew license for tenant
        
        Args:
            tenant_id: Tenant identifier
            new_expiry_date: New expiry date
            
        Returns:
            bool: True if license was renewed successfully
        """
        await self._ensure_initialized()
        
        try:
            # Update license expiry date
            await self.storage.update("licenses",
                {"tenant_id": tenant_id},
                {
                    "expiry_date": new_expiry_date.isoformat(),
                    "is_active": True
                }
            )
            
            # Update status record
            await self._update_license_status(tenant_id, "active")
            
            # Audit renewal
            await self._audit_action(
                tenant_id=tenant_id,
                action="license_renewed",
                details={"new_expiry_date": new_expiry_date.isoformat()}
            )
            
            logger.info(f"License renewed for tenant: {tenant_id}, expires: {new_expiry_date}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to renew license: {str(e)}")
            return False
    
    async def _update_license_status(self, tenant_id: str, status: str) -> None:
        """Update license status record"""
        try:
            next_check = datetime.utcnow() + timedelta(hours=24)
            
            # Check if status record exists
            existing = await self.storage.query("license_status", {"tenant_id": tenant_id}, limit=1)
            status_data = {
                "tenant_id": tenant_id,
                "license_key": "",  # Will be updated if available
                "status": status,
                "last_check": datetime.utcnow().isoformat(),
                "next_check": next_check.isoformat(),
                "usage_summary": "{}",
                "limit_summary": "{}",
                "warnings": "[]",
                "errors": "[]"
            }
            
            if existing:
                # Update existing record
                await self.storage.update("license_status", tenant_id, status_data)
            else:
                # Insert new record
                await self.storage.insert("license_status", status_data)
            
        except Exception as e:
            logger.error(f"Failed to update license status: {str(e)}")
    
    async def _update_usage_summary(self, tenant_id: str, feature: str, usage: int) -> None:
        """Update usage summary for tenant"""
        try:
            # Get current status
            results = await self.storage.query(
                "license_status",
                {"tenant_id": tenant_id},
                limit=1
            )
            result = results[0] if results else None
            
            if result:
                status_data = dict(result)
                usage_summary = json.loads(status_data.get("usage_summary", "{}"))
                usage_summary[feature] = usage_summary.get(feature, 0) + usage
                
                await self.storage.update("license_status",
                    {"tenant_id": tenant_id},
                    {"usage_summary": json.dumps(usage_summary)}
                )
            
        except Exception as e:
            logger.error(f"Failed to update usage summary: {str(e)}")
    
    async def _update_sync_status(self, sync_id: str, status: str, errors: List[str]) -> None:
        """Update sync status"""
        try:
            await self.storage.update("license_sync",
                {"sync_id": sync_id},
                {
                    "status": status,
                    "completed_at": datetime.utcnow().isoformat(),
                    "errors": json.dumps(errors)
                }
            )
        except Exception as e:
            logger.error(f"Failed to update sync status: {str(e)}")
    
    async def _audit_action(self, tenant_id: str, action: str, details: Dict[str, Any], 
                           user_id: Optional[str] = None) -> None:
        """Record audit trail"""
        try:
            audit_id = str(uuid4())
            await self.storage.insert("license_audit", {
                "audit_id": audit_id,
                "tenant_id": tenant_id,
                "action": action,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id or "",
                "details": json.dumps(details),
                "ip_address": "",
                "user_agent": ""
            })
        except Exception as e:
            logger.error(f"Failed to record audit: {str(e)}")
    
    async def create_license(self, tenant_id: str, license_type: str, 
                           features: List[str], limits: Dict[str, int],
                           expiry_date: Optional[datetime] = None) -> str:
        """
        Create a new license for a tenant
        
        Args:
            tenant_id: Tenant identifier
            license_type: License type (basic, standard, enterprise, industry)
            features: List of enabled features
            limits: Usage limits dictionary
            expiry_date: License expiry date
            
        Returns:
            str: Generated license key
        """
        await self._ensure_initialized()
        
        try:
            # Generate license key
            license_key = self._generate_license_key(tenant_id, license_type)
            
            # Set default expiry if not provided
            if not expiry_date:
                expiry_date = datetime.utcnow() + timedelta(days=365)
            
            # Create license record
            await self.storage.insert("licenses", {
                "license_key": license_key,
                "tenant_id": tenant_id,
                "license_type": license_type,
                "features": json.dumps(features),
                "limits": json.dumps(limits),
                "issued_date": datetime.utcnow().isoformat(),
                "expiry_date": expiry_date.isoformat(),
                "is_active": True,
                "max_users": limits.get("max_users", 1),
                "max_calls_per_month": limits.get("max_calls_per_month", 1000),
                "max_storage_gb": limits.get("max_storage_gb", 10),
                "support_level": "basic",
                "customizations": "{}"
            })
            
            # Initialize status record
            await self._update_license_status(tenant_id, "active")
            
            # Audit license creation
            await self._audit_action(
                tenant_id=tenant_id,
                action="license_created",
                details={
                    "license_key": license_key,
                    "license_type": license_type,
                    "features": features,
                    "limits": limits,
                    "expiry_date": expiry_date.isoformat()
                }
            )
            
            logger.info(f"License created for tenant: {tenant_id}, key: {license_key}")
            return license_key
            
        except Exception as e:
            logger.error(f"Failed to create license: {str(e)}")
            raise
    
    def _generate_license_key(self, tenant_id: str, license_type: str) -> str:
        """Generate a unique license key"""
        timestamp = datetime.utcnow().isoformat()
        data = f"{tenant_id}:{license_type}:{timestamp}"
        hash_obj = hashlib.sha256(data.encode())
        return hash_obj.hexdigest()[:32].upper()
    
    async def get_license_compliance(self, tenant_id: str) -> LicenseCompliance:
        """
        Get license compliance information
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            LicenseCompliance: Compliance information
        """
        await self._ensure_initialized()
        
        try:
            # Get license status
            status = await self.get_license_status(tenant_id)
            
            violations = []
            recommendations = []
            
            # Check for violations
            if status["status"] == "expired":
                violations.append({
                    "type": "license_expired",
                    "severity": "critical",
                    "message": "License has expired"
                })
                recommendations.append("Renew license immediately")
            
            if status["status"] == "revoked":
                violations.append({
                    "type": "license_revoked",
                    "severity": "critical",
                    "message": "License has been revoked"
                })
                recommendations.append("Contact support for license reactivation")
            
            # Check for expired license by checking the actual license record
            if status["status"] == "active":
                license_results = await self.storage.query("licenses", {"tenant_id": tenant_id}, limit=1)
                license_result = license_results[0] if license_results else None
                if license_result:
                    license_data = dict(license_result)
                    if license_data.get("expiry_date"):
                        expiry_date = datetime.fromisoformat(license_data["expiry_date"])
                        if datetime.utcnow() > expiry_date:
                            violations.append({
                                "type": "license_expired",
                                "severity": "critical",
                                "message": "License has expired"
                            })
                            recommendations.append("Renew license immediately")
            
            # Check usage violations
            usage_summary = status.get("usage_summary", {})
            limit_summary = status.get("limit_summary", {})
            
            for feature, usage in usage_summary.items():
                limit = limit_summary.get(feature, 0)
                if limit > 0 and usage > limit:
                    violations.append({
                        "type": "usage_limit_exceeded",
                        "severity": "warning",
                        "message": f"Usage limit exceeded for {feature}: {usage}/{limit}"
                    })
                    recommendations.append(f"Reduce usage of {feature} or upgrade license")
            
            # Determine compliance status
            if any(v["severity"] == "critical" for v in violations):
                compliance_status = "non_compliant"
            elif violations:
                compliance_status = "warning"
            else:
                compliance_status = "compliant"
            
            return LicenseCompliance(
                tenant_id=tenant_id,
                compliance_status=compliance_status,
                last_check=datetime.utcnow(),
                violations=violations,
                recommendations=recommendations,
                auto_remediation=False,
                grace_period_days=7
            )
            
        except Exception as e:
            logger.error(f"Failed to get compliance: {str(e)}")
            return LicenseCompliance(
                tenant_id=tenant_id,
                compliance_status="error",
                last_check=datetime.utcnow(),
                violations=[],
                recommendations=["Contact support for compliance check"],
                auto_remediation=False,
                grace_period_days=7
            )
