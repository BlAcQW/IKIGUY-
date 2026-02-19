"""
Test suite for Core Backend License Service.

This module contains comprehensive tests for the License Service integration
with the shared license management library.
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from backend.services.license_service import LicenseService
from apps.shared.license import LicenseInfo, LicenseFeatures, LicenseLimits, LicenseStatus


class TestLicenseService:
    """Test suite for License Service."""

    @pytest.fixture
    def license_service(self):
        """Create a license service instance for testing."""
        service = LicenseService()
        return service

    @pytest.mark.asyncio
    async def test_license_service_initialization(self, license_service):
        """Test license service initialization."""
        assert license_service is not None
        assert hasattr(license_service, 'license_engine')
        assert license_service.license_engine is not None

    @pytest.mark.asyncio
    async def test_create_license(self, license_service):
        """Test creating a new license."""
        tenant_id = "test-tenant-123"
        license_key = "test-license-key"
        features = {"voice_calls": True, "basic_analytics": True}
        limits = {"max_calls_per_month": 1000, "max_users": 5}
        expiry_date = date.today() + timedelta(days=365)

        result = await license_service.create_license(
            tenant_id=tenant_id,
            license_key=license_key,
            features=features,
            limits=limits,
            expiry_date=expiry_date
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_validate_license(self, license_service):
        """Test license validation."""
        tenant_id = "test-tenant-123"
        license_key = "test-license-key"

        # First create a license to validate
        await license_service.create_license(
            tenant_id=tenant_id,
            license_key=license_key,
            features={"voice_calls": True},
            limits={"max_calls_per_month": 1000}
        )

        # Then validate it
        result = await license_service.validate_license(
            tenant_id=tenant_id,
            license_key=license_key
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_license_info(self, license_service):
        """Test getting license information."""
        tenant_id = "test-tenant-123"

        # First create a license
        await license_service.create_license(
            tenant_id=tenant_id,
            license_key="test-key",
            features={"voice_calls": True},
            limits={"max_calls_per_month": 1000}
        )

        # Then get license info
        result = await license_service.get_license_info(tenant_id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_check_feature_access(self, license_service):
        """Test checking feature access."""
        tenant_id = "test-tenant-123"
        feature = "voice_calls"

        # First create a license with the feature
        await license_service.create_license(
            tenant_id=tenant_id,
            license_key="test-key",
            features={"voice_calls": True},
            limits={"max_calls_per_month": 1000}
        )

        # Check feature access
        result = await license_service.check_feature_access(tenant_id, feature)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_usage_limits(self, license_service):
        """Test checking usage limits."""
        tenant_id = "test-tenant-123"
        feature = "voice_calls"
        quantity = 10

        # First create a license
        await license_service.create_license(
            tenant_id=tenant_id,
            license_key="test-key",
            features={"voice_calls": True},
            limits={"max_calls_per_month": 1000}
        )

        # Check usage limits
        result = await license_service.check_usage_limits(tenant_id, feature, quantity)

        assert result is True

    @pytest.mark.asyncio
    async def test_revoke_license(self, license_service):
        """Test revoking a license."""
        tenant_id = "test-tenant-123"

        # First create a license
        await license_service.create_license(
            tenant_id=tenant_id,
            license_key="test-key",
            features={"voice_calls": True},
            limits={"max_calls_per_month": 1000}
        )

        # Then revoke it
        result = await license_service.revoke_license(tenant_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_renew_license(self, license_service):
        """Test renewing a license."""
        tenant_id = "test-tenant-123"
        new_expiry_date = date.today() + timedelta(days=730)

        # First create a license
        await license_service.create_license(
            tenant_id=tenant_id,
            license_key="test-key",
            features={"voice_calls": True},
            limits={"max_calls_per_month": 1000}
        )

        # Then renew it
        result = await license_service.renew_license(tenant_id, new_expiry_date)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_license_compliance(self, license_service):
        """Test getting license compliance status."""
        tenant_id = "test-tenant-123"

        # First create a license
        await license_service.create_license(
            tenant_id=tenant_id,
            license_key="test-key",
            features={"voice_calls": True},
            limits={"max_calls_per_month": 1000}
        )

        # Get compliance status
        result = await license_service.get_license_compliance(tenant_id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_sync_license_data(self, license_service):
        """Test syncing license data."""
        tenant_id = "test-tenant-123"
        sync_data = {"license_key": "test-key", "features": ["voice_calls"]}

        result = await license_service.sync_license_data(tenant_id, sync_data)

        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_export_license_data(self, license_service):
        """Test exporting license data."""
        tenant_id = "test-tenant-123"

        # First create a license
        await license_service.create_license(
            tenant_id=tenant_id,
            license_key="test-key",
            features={"voice_calls": True},
            limits={"max_calls_per_month": 1000}
        )

        # Export license data
        result = await license_service.export_license_data(tenant_id, "json")

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_import_license_data(self, license_service):
        """Test importing license data."""
        tenant_id = "test-tenant-123"
        data = '{"license_key": "test-key", "features": ["voice_calls"]}'

        result = await license_service.import_license_data(tenant_id, data, "json")

        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_get_license_audit_trail(self, license_service):
        """Test getting license audit trail."""
        tenant_id = "test-tenant-123"
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        # First create a license to generate audit data
        await license_service.create_license(
            tenant_id=tenant_id,
            license_key="test-key",
            features={"voice_calls": True},
            limits={"max_calls_per_month": 1000}
        )

        # Get audit trail
        result = await license_service.get_license_audit_trail(
            tenant_id, start_date, end_date
        )

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_license_service_error_handling(self, license_service):
        """Test error handling in license service."""
        # Test with invalid tenant ID
        result = await license_service.get_license_info("invalid-tenant-id")
        assert result is None

        # Test feature access with no license
        result = await license_service.check_feature_access("invalid-tenant-id", "voice_calls")
        assert result is False

    @pytest.mark.asyncio
    async def test_license_service_performance(self, license_service):
        """Test license service performance."""
        import time

        start_time = time.time()

        # Test multiple operations
        tenant_id = "test-tenant-123"
        
        await license_service.create_license(
            tenant_id=tenant_id,
            license_key="test-key",
            features={"voice_calls": True},
            limits={"max_calls_per_month": 1000}
        )
        
        await license_service.get_license_info(tenant_id)
        await license_service.check_feature_access(tenant_id, "voice_calls")
        await license_service.check_usage_limits(tenant_id, "voice_calls", 10)

        end_time = time.time()
        execution_time = end_time - start_time

        # Performance should be reasonable (less than 1 second for basic operations)
        assert execution_time < 1.0

    @pytest.mark.asyncio
    async def test_license_service_concurrent_operations(self, license_service):
        """Test concurrent license operations."""
        import asyncio

        tenant_ids = [f"tenant-{i}" for i in range(5)]

        # Create multiple licenses concurrently
        tasks = []
        for tenant_id in tenant_ids:
            task = license_service.create_license(
                tenant_id=tenant_id,
                license_key=f"key-{tenant_id}",
                features={"voice_calls": True},
                limits={"max_calls_per_month": 1000}
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All operations should succeed
        for result in results:
            assert not isinstance(result, Exception)

    @pytest.mark.asyncio
    async def test_license_service_tenant_isolation(self, license_service):
        """Test tenant isolation in license service."""
        tenant1_id = "tenant-1"
        tenant2_id = "tenant-2"

        # Create licenses for different tenants
        await license_service.create_license(
            tenant_id=tenant1_id,
            license_key="key-1",
            features={"voice_calls": True},
            limits={"max_calls_per_month": 1000}
        )

        await license_service.create_license(
            tenant_id=tenant2_id,
            license_key="key-2",
            features={"advanced_analytics": True},
            limits={"max_calls_per_month": 2000}
        )

        # Check that tenants can only access their own licenses
        tenant1_info = await license_service.get_license_info(tenant1_id)
        tenant2_info = await license_service.get_license_info(tenant2_id)

        assert tenant1_info is not None
        assert tenant2_info is not None

        # Check feature access isolation
        assert await license_service.check_feature_access(tenant1_id, "voice_calls") is True
        assert await license_service.check_feature_access(tenant1_id, "advanced_analytics") is False
        assert await license_service.check_feature_access(tenant2_id, "advanced_analytics") is True
        assert await license_service.check_feature_access(tenant2_id, "voice_calls") is False
