"""
Tests for License Management Engine

This module provides comprehensive tests for the LicenseManagementEngine
to ensure all license management functionality works correctly.
"""

import json
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from ..license.engine import LicenseManagementEngine
from ..license.interfaces import LicenseInfo
from ..license.models import LicenseCompliance
from ..storage.interfaces import StorageBackend


class SimpleStorageAdapter:
    """Simple in-memory storage adapter for testing"""
    
    def __init__(self):
        self.tables = {}
        self.data = {}
    
    async def create_table(self, table_name: str, schema: Dict[str, str]) -> bool:
        """Create a table"""
        self.tables[table_name] = schema
        self.data[table_name] = []
        return True
    
    async def insert(self, table_name: str, data: Dict[str, Any]) -> bool:
        """Insert data into table"""
        if table_name not in self.data:
            return False
        self.data[table_name].append(data.copy())
        return True
    
    async def select(self, table_name: str, conditions: Dict[str, Any] = None) -> list:
        """Select data from table"""
        if table_name not in self.data:
            return []
        
        results = self.data[table_name]
        
        if conditions:
            filtered_results = []
            for row in results:
                match = True
                for key, value in conditions.items():
                    if isinstance(value, dict) and "$gte" in value:
                        # Handle greater than or equal condition
                        if key not in row or row[key] < value["$gte"]:
                            match = False
                            break
                    elif key not in row or row[key] != value:
                        match = False
                        break
                if match:
                    filtered_results.append(row)
            return filtered_results
        
        return results
    
    async def select_one(self, table_name: str, conditions: Dict[str, Any] = None) -> Dict[str, Any]:
        """Select one record from table"""
        results = await self.select(table_name, conditions)
        return results[0] if results else None
    
    async def update(self, table_name: str, conditions: Dict[str, Any], updates: Dict[str, Any]) -> bool:
        """Update data in table"""
        if table_name not in self.data:
            return False
        
        updated = False
        for row in self.data[table_name]:
            match = True
            for key, value in conditions.items():
                if key not in row or row[key] != value:
                    match = False
                    break
            
            if match:
                row.update(updates)
                updated = True
        
        return updated
    
    async def upsert(self, table_name: str, data: Dict[str, Any]) -> bool:
        """Upsert data into table"""
        if table_name not in self.data:
            return False
        
        # Check if record exists
        primary_key = None
        for key, value in data.items():
            if "PRIMARY KEY" in self.tables[table_name].get(key, ""):
                primary_key = key
                break
        
        if primary_key:
            # Try to update existing record
            updated = await self.update(table_name, {primary_key: data[primary_key]}, data)
            if not updated:
                # Insert new record
                return await self.insert(table_name, data)
            return True
        else:
            return await self.insert(table_name, data)
    
    async def delete(self, table_name: str, conditions: Dict[str, Any]) -> bool:
        """Delete data from table"""
        if table_name not in self.data:
            return False
        
        original_count = len(self.data[table_name])
        self.data[table_name] = [
            row for row in self.data[table_name]
            if not all(row.get(key) == value for key, value in conditions.items())
        ]
        
        return len(self.data[table_name]) < original_count


@pytest.fixture
def storage_backend():
    """Storage backend fixture"""
    return SimpleStorageAdapter()


@pytest.fixture
async def license_engine(storage_backend):
    """License engine fixture"""
    engine = LicenseManagementEngine(storage_backend)
    return engine


class TestLicenseManagementEngine:
    """Test cases for LicenseManagementEngine"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, license_engine):
        """Test license engine initialization"""
        engine = await license_engine
        
        # Call an async method to trigger initialization
        await engine.get_license_status("test_tenant")
        
        # Check that storage tables were created
        assert "licenses" in engine.storage.tables
        assert "license_usage" in engine.storage.tables
        assert "license_status" in engine.storage.tables
        assert "license_sync" in engine.storage.tables
        assert "license_audit" in engine.storage.tables
    
    @pytest.mark.asyncio
    async def test_create_license(self, license_engine):
        """Test license creation"""
        engine = await license_engine
        
        # Create a license
        license_key = await engine.create_license(
            tenant_id="test_tenant",
            license_type="standard",
            features=["voice_calls", "basic_analytics"],
            limits={"max_calls_per_month": 1000, "max_users": 5}
        )
        
        assert license_key is not None
        assert len(license_key) == 32
        
        # Verify license was created
        result = await engine.storage.select_one("licenses", {"license_key": license_key})
        assert result is not None
        assert result["tenant_id"] == "test_tenant"
        assert result["license_type"] == "standard"
    
    @pytest.mark.asyncio
    async def test_validate_license(self, license_engine):
        """Test license validation"""
        engine = await license_engine
        
        # Create a license first
        license_key = await engine.create_license(
            tenant_id="test_tenant",
            license_type="standard",
            features=["voice_calls", "basic_analytics"],
            limits={"max_calls_per_month": 1000, "max_users": 5}
        )
        
        # Validate the license
        license_info = await engine.validate_license(license_key)
        
        assert isinstance(license_info, LicenseInfo)
        assert license_info.license_key == license_key
        assert license_info.tenant_id == "test_tenant"
        assert license_info.license_type == "standard"
        assert license_info.is_active is True
        assert "voice_calls" in license_info.features
        assert "basic_analytics" in license_info.features
    
    @pytest.mark.asyncio
    async def test_validate_expired_license(self, license_engine):
        """Test validation of expired license"""
        engine = await license_engine
        
        # Create a license with past expiry date
        license_key = await engine.create_license(
            tenant_id="test_tenant",
            license_type="standard",
            features=["voice_calls"],
            limits={"max_calls_per_month": 1000},
            expiry_date=datetime.utcnow() - timedelta(days=1)
        )
        
        # Try to validate expired license
        with pytest.raises(ValueError, match="License expired"):
            await engine.validate_license(license_key)
    
    @pytest.mark.asyncio
    async def test_validate_invalid_license(self, license_engine):
        """Test validation of invalid license key"""
        engine = await license_engine
        
        with pytest.raises(ValueError, match="License key not found"):
            await engine.validate_license("INVALID_LICENSE_KEY")
    
    @pytest.mark.asyncio
    async def test_check_feature_access(self, license_engine):
        """Test feature access checking"""
        engine = await license_engine
        
        # Create a license
        await engine.create_license(
            tenant_id="test_tenant",
            license_type="standard",
            features=["voice_calls", "basic_analytics"],
            limits={"max_calls_per_month": 1000}
        )
        
        # Check feature access
        assert await engine.check_feature_access("test_tenant", "voice_calls") is True
        assert await engine.check_feature_access("test_tenant", "basic_analytics") is True
        assert await engine.check_feature_access("test_tenant", "advanced_analytics") is False
    
    @pytest.mark.asyncio
    async def test_check_feature_access_no_license(self, license_engine):
        """Test feature access check for tenant without license"""
        engine = await license_engine
        
        assert await engine.check_feature_access("no_license_tenant", "voice_calls") is False
    
    @pytest.mark.asyncio
    async def test_record_usage(self, license_engine):
        """Test usage recording"""
        engine = await license_engine
        
        # Create a license
        await engine.create_license(
            tenant_id="test_tenant",
            license_type="standard",
            features=["voice_calls"],
            limits={"voice_calls": 1000}
        )
        
        # Record usage
        success = await engine.record_usage("test_tenant", "voice_calls", 100)
        assert success is True
        
        # Verify usage was recorded
        usage_records = await engine.storage.select("license_usage", {"tenant_id": "test_tenant"})
        assert len(usage_records) == 1
        assert usage_records[0]["feature"] == "voice_calls"
        assert usage_records[0]["usage_amount"] == 100
    
    @pytest.mark.asyncio
    async def test_record_usage_exceeds_limit(self, license_engine):
        """Test usage recording that exceeds limits"""
        engine = await license_engine
        
        # Create a license with low limit
        await engine.create_license(
            tenant_id="test_tenant",
            license_type="basic",
            features=["voice_calls"],
            limits={"voice_calls": 50}
        )
        
        # Record usage within limit
        success = await engine.record_usage("test_tenant", "voice_calls", 30)
        assert success is True
        
        # Try to record usage that exceeds limit
        success = await engine.record_usage("test_tenant", "voice_calls", 30)
        assert success is False  # Should fail because 30 + 30 > 50
    
    @pytest.mark.asyncio
    async def test_check_usage_limits(self, license_engine):
        """Test usage limit checking"""
        engine = await license_engine
        
        # Create a license
        await engine.create_license(
            tenant_id="test_tenant",
            license_type="standard",
            features=["voice_calls"],
            limits={"voice_calls": 1000}
        )
        
        # Check limits
        assert await engine.check_usage_limits("test_tenant", "voice_calls", 500) is True
        assert await engine.check_usage_limits("test_tenant", "voice_calls", 1000) is True
        assert await engine.check_usage_limits("test_tenant", "voice_calls", 1001) is False
    
    @pytest.mark.asyncio
    async def test_get_remaining_quota(self, license_engine):
        """Test remaining quota calculation"""
        engine = await license_engine
        
        # Create a license
        await engine.create_license(
            tenant_id="test_tenant",
            license_type="standard",
            features=["voice_calls"],
            limits={"voice_calls": 1000}
        )
        
        # Get remaining quota before usage
        remaining = await engine.get_remaining_quota("test_tenant", "voice_calls")
        assert remaining == 1000
        
        # Record some usage
        await engine.record_usage("test_tenant", "voice_calls", 300)
        
        # Get remaining quota after usage
        remaining = await engine.get_remaining_quota("test_tenant", "voice_calls")
        assert remaining == 700
    
    @pytest.mark.asyncio
    async def test_get_license_status(self, license_engine):
        """Test license status retrieval"""
        engine = await license_engine
        
        # Create a license
        await engine.create_license(
            tenant_id="test_tenant",
            license_type="standard",
            features=["voice_calls"],
            limits={"voice_calls": 1000}
        )
        
        # Get status
        status = await engine.get_license_status("test_tenant")
        
        assert status["tenant_id"] == "test_tenant"
        assert status["status"] == "active"
        assert "last_check" in status
        assert "next_check" in status
    
    @pytest.mark.asyncio
    async def test_get_license_status_no_license(self, license_engine):
        """Test license status for tenant without license"""
        engine = await license_engine
        
        status = await engine.get_license_status("no_license_tenant")
        
        assert status["tenant_id"] == "no_license_tenant"
        assert status["status"] == "no_license"
        assert "No license found" in status["warnings"]
    
    @pytest.mark.asyncio
    async def test_sync_license(self, license_engine):
        """Test license synchronization"""
        engine = await license_engine
        
        # Create a license
        await engine.create_license(
            tenant_id="test_tenant",
            license_type="standard",
            features=["voice_calls"],
            limits={"voice_calls": 1000}
        )
        
        # Record some usage
        await engine.record_usage("test_tenant", "voice_calls", 100)
        
        # Sync license
        success = await engine.sync_license("test_tenant")
        assert success is True
        
        # Verify sync record was created
        sync_records = await engine.storage.select("license_sync", {"tenant_id": "test_tenant"})
        assert len(sync_records) == 1
        assert sync_records[0]["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_sync_license_no_license(self, license_engine):
        """Test license sync for tenant without license"""
        engine = await license_engine
        
        success = await engine.sync_license("no_license_tenant")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_revoke_license(self, license_engine):
        """Test license revocation"""
        engine = await license_engine
        
        # Create a license
        await engine.create_license(
            tenant_id="test_tenant",
            license_type="standard",
            features=["voice_calls"],
            limits={"voice_calls": 1000}
        )
        
        # Revoke license
        success = await engine.revoke_license("test_tenant")
        assert success is True
        
        # Verify license is inactive
        result = await engine.storage.select_one("licenses", {"tenant_id": "test_tenant"})
        assert result["is_active"] is False
        
        # Verify status is revoked
        status = await engine.get_license_status("test_tenant")
        assert status["status"] == "revoked"
    
    @pytest.mark.asyncio
    async def test_renew_license(self, license_engine):
        """Test license renewal"""
        engine = await license_engine
        
        # Create a license
        await engine.create_license(
            tenant_id="test_tenant",
            license_type="standard",
            features=["voice_calls"],
            limits={"voice_calls": 1000}
        )
        
        # Renew license
        new_expiry = datetime.utcnow() + timedelta(days=365)
        success = await engine.renew_license("test_tenant", new_expiry)
        assert success is True
        
        # Verify license is active
        result = await engine.storage.select_one("licenses", {"tenant_id": "test_tenant"})
        assert result["is_active"] is True
        assert result["expiry_date"] == new_expiry.isoformat()
        
        # Verify status is active
        status = await engine.get_license_status("test_tenant")
        assert status["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_get_license_compliance(self, license_engine):
        """Test license compliance checking"""
        engine = await license_engine
        
        # Create a license
        await engine.create_license(
            tenant_id="test_tenant",
            license_type="standard",
            features=["voice_calls"],
            limits={"voice_calls": 1000}
        )
        
        # Get compliance
        compliance = await engine.get_license_compliance("test_tenant")
        
        assert isinstance(compliance, LicenseCompliance)
        assert compliance.tenant_id == "test_tenant"
        assert compliance.compliance_status == "compliant"
        assert len(compliance.violations) == 0
    
    @pytest.mark.asyncio
    async def test_get_license_compliance_expired(self, license_engine):
        """Test license compliance for expired license"""
        engine = await license_engine
        
        # Create an expired license
        await engine.create_license(
            tenant_id="test_tenant",
            license_type="standard",
            features=["voice_calls"],
            limits={"voice_calls": 1000},
            expiry_date=datetime.utcnow() - timedelta(days=1)
        )
        
        # Get compliance
        compliance = await engine.get_license_compliance("test_tenant")
        
        assert compliance.compliance_status == "non_compliant"
        assert len(compliance.violations) > 0
        assert any(v["type"] == "license_expired" for v in compliance.violations)
    
    @pytest.mark.asyncio
    async def test_audit_trail(self, license_engine):
        """Test audit trail recording"""
        engine = await license_engine
        
        # Create a license (should trigger audit)
        await engine.create_license(
            tenant_id="test_tenant",
            license_type="standard",
            features=["voice_calls"],
            limits={"voice_calls": 1000}
        )
        
        # Check feature access (should trigger audit)
        await engine.check_feature_access("test_tenant", "voice_calls")
        
        # Record usage (should trigger audit)
        await engine.record_usage("test_tenant", "voice_calls", 100)
        
        # Verify audit records were created
        audit_records = await engine.storage.select("license_audit", {"tenant_id": "test_tenant"})
        assert len(audit_records) >= 3  # At least license_created, feature_access_check, usage_recorded
        
        # Check for specific audit actions
        actions = [record["action"] for record in audit_records]
        assert "license_created" in actions
        assert "feature_access_check" in actions
        assert "usage_recorded" in actions


class TestLicenseManagementIntegration:
    """Integration tests for LicenseManagementEngine"""
    
    @pytest.mark.asyncio
    async def test_full_license_workflow(self, license_engine):
        """Test complete license workflow"""
        engine = await license_engine
        
        # 1. Create a license
        license_key = await engine.create_license(
            tenant_id="integration_tenant",
            license_type="enterprise",
            features=["voice_calls", "advanced_analytics", "ai_features"],
            limits={
                "voice_calls": 10000,
                "advanced_analytics": 5000,
                "ai_features": 2000
            }
        )
        
        assert license_key is not None
        
        # 2. Validate the license
        license_info = await engine.validate_license(license_key)
        assert license_info.tenant_id == "integration_tenant"
        assert license_info.license_type == "enterprise"
        assert license_info.is_active is True
        
        # 3. Check feature access
        assert await engine.check_feature_access("integration_tenant", "voice_calls") is True
        assert await engine.check_feature_access("integration_tenant", "advanced_analytics") is True
        assert await engine.check_feature_access("integration_tenant", "ai_features") is True
        assert await engine.check_feature_access("integration_tenant", "non_existent_feature") is False
        
        # 4. Record usage for multiple features
        assert await engine.record_usage("integration_tenant", "voice_calls", 1000) is True
        assert await engine.record_usage("integration_tenant", "advanced_analytics", 500) is True
        assert await engine.record_usage("integration_tenant", "ai_features", 200) is True
        
        # 5. Check remaining quotas
        voice_remaining = await engine.get_remaining_quota("integration_tenant", "voice_calls")
        analytics_remaining = await engine.get_remaining_quota("integration_tenant", "advanced_analytics")
        ai_remaining = await engine.get_remaining_quota("integration_tenant", "ai_features")
        
        assert voice_remaining == 9000  # 10000 - 1000
        assert analytics_remaining == 4500  # 5000 - 500
        assert ai_remaining == 1800  # 2000 - 200
        
        # 6. Get license status
        status = await engine.get_license_status("integration_tenant")
        assert status["status"] == "active"
        assert status["tenant_id"] == "integration_tenant"
        
        # 7. Check compliance
        compliance = await engine.get_license_compliance("integration_tenant")
        assert compliance.compliance_status == "compliant"
        
        # 8. Sync license
        sync_success = await engine.sync_license("integration_tenant")
        assert sync_success is True
        
        # 9. Verify audit trail
        audit_records = await engine.storage.select("license_audit", {"tenant_id": "integration_tenant"})
        assert len(audit_records) >= 8  # Multiple actions should be audited
        
        # 10. Test usage limit enforcement
        # Try to use more than remaining quota
        assert await engine.record_usage("integration_tenant", "voice_calls", 10000) is False  # Exceeds limit
        
        # Verify quota is unchanged
        voice_remaining_after = await engine.get_remaining_quota("integration_tenant", "voice_calls")
        assert voice_remaining_after == voice_remaining  # Should be unchanged
    
    @pytest.mark.asyncio
    async def test_license_renewal_workflow(self, license_engine):
        """Test license renewal workflow"""
        engine = await license_engine
        
        # 1. Create a license with short expiry
        license_key = await engine.create_license(
            tenant_id="renewal_tenant",
            license_type="standard",
            features=["voice_calls"],
            limits={"voice_calls": 1000},
            expiry_date=datetime.utcnow() + timedelta(days=1)  # Expires tomorrow
        )
        
        # 2. Validate license (should work)
        license_info = await engine.validate_license(license_key)
        assert license_info.is_active is True
        
        # 3. Renew license
        new_expiry = datetime.utcnow() + timedelta(days=365)
        success = await engine.renew_license("renewal_tenant", new_expiry)
        assert success is True
        
        # 4. Validate renewed license
        renewed_info = await engine.validate_license(license_key)
        assert renewed_info.is_active is True
        assert renewed_info.expiry_date == new_expiry
        
        # 5. Check compliance
        compliance = await engine.get_license_compliance("renewal_tenant")
        assert compliance.compliance_status == "compliant"
    
    @pytest.mark.asyncio
    async def test_license_revocation_workflow(self, license_engine):
        """Test license revocation workflow"""
        engine = await license_engine
        
        # 1. Create a license
        license_key = await engine.create_license(
            tenant_id="revocation_tenant",
            license_type="standard",
            features=["voice_calls"],
            limits={"voice_calls": 1000}
        )
        
        # 2. Record some usage
        await engine.record_usage("revocation_tenant", "voice_calls", 500)
        
        # 3. Revoke license
        success = await engine.revoke_license("revocation_tenant")
        assert success is True
        
        # 4. Try to validate revoked license
        with pytest.raises(ValueError):
            await engine.validate_license(license_key)
        
        # 5. Check feature access (should be denied)
        assert await engine.check_feature_access("revocation_tenant", "voice_calls") is False
        
        # 6. Try to record usage (should fail)
        assert await engine.record_usage("revocation_tenant", "voice_calls", 100) is False
        
        # 7. Check compliance
        compliance = await engine.get_license_compliance("revocation_tenant")
        assert compliance.compliance_status == "non_compliant"
        assert any(v["type"] == "license_revoked" for v in compliance.violations)
    
    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(self, license_engine):
        """Test multi-tenant isolation"""
        engine = await license_engine
        
        # Create licenses for multiple tenants
        tenant1_key = await engine.create_license(
            tenant_id="tenant_1",
            license_type="basic",
            features=["voice_calls"],
            limits={"voice_calls": 1000}
        )
        
        tenant2_key = await engine.create_license(
            tenant_id="tenant_2",
            license_type="enterprise",
            features=["voice_calls", "advanced_analytics"],
            limits={"voice_calls": 10000, "advanced_analytics": 5000}
        )
        
        # Verify isolation - tenant 1 can't access tenant 2's features
        assert await engine.check_feature_access("tenant_1", "voice_calls") is True
        assert await engine.check_feature_access("tenant_1", "advanced_analytics") is False
        
        # Verify isolation - tenant 2 can access both features
        assert await engine.check_feature_access("tenant_2", "voice_calls") is True
        assert await engine.check_feature_access("tenant_2", "advanced_analytics") is True
        
        # Verify isolation - usage is tracked separately
        await engine.record_usage("tenant_1", "voice_calls", 500)
        await engine.record_usage("tenant_2", "voice_calls", 2000)
        
        tenant1_remaining = await engine.get_remaining_quota("tenant_1", "voice_calls")
        tenant2_remaining = await engine.get_remaining_quota("tenant_2", "voice_calls")
        
        assert tenant1_remaining == 500  # 1000 - 500
        assert tenant2_remaining == 8000  # 10000 - 2000
        
        # Verify isolation - status is separate
        tenant1_status = await engine.get_license_status("tenant_1")
        tenant2_status = await engine.get_license_status("tenant_2")
        
        assert tenant1_status["tenant_id"] == "tenant_1"
        assert tenant2_status["tenant_id"] == "tenant_2"
        assert tenant1_status != tenant2_status
