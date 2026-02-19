"""
Tests for Core Backend Security Service integration with shared libraries.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from backend.services.security_service import SecurityService


class TestSecurityService:
    """Test cases for SecurityService integration with shared libraries."""

    @pytest.fixture
    def security_service(self):
        """Create a security service instance for testing."""
        service = SecurityService()
        return service

    @pytest.mark.asyncio
    async def test_security_service_initialization(self, security_service):
        """Test that security service initializes correctly with shared library."""
        assert security_service.security_engine is not None
        assert hasattr(security_service.security_engine, 'record_event')

    @pytest.mark.asyncio
    async def test_log_security_event(self, security_service):
        """Test logging security events."""
        result = await security_service.log_security_event(
            tenant_id="test-tenant",
            event_type="login",
            user_id="test-user",
            resource="/api/users",
            action="GET",
            severity="info"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_check_access_control(self, security_service):
        """Test access control checking."""
        result = await security_service.check_access_control(
            tenant_id="test-tenant",
            user_id="test-user",
            resource="/api/users",
            action="GET"
        )
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_get_security_audit(self, security_service):
        """Test getting security audit logs."""
        audit = await security_service.get_security_audit(
            tenant_id="test-tenant",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            event_types=["login", "logout"]
        )
        assert audit["success"] is True
        assert "events" in audit

    @pytest.mark.asyncio
    async def test_get_compliance_report(self, security_service):
        """Test getting compliance reports."""
        report = await security_service.get_compliance_report(
            tenant_id="test-tenant",
            compliance_framework="gdpr",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )
        assert report["success"] is True
        assert "compliance_status" in report

    @pytest.mark.asyncio
    async def test_encrypt_data(self, security_service):
        """Test data encryption."""
        data = "sensitive data"
        encrypted = await security_service.encrypt_data(data=data)
        assert encrypted != ""

    @pytest.mark.asyncio
    async def test_decrypt_data(self, security_service):
        """Test data decryption."""
        encrypted_data = "encrypted_string_here"
        decrypted = await security_service.decrypt_data(encrypted_data=encrypted_data)
        assert decrypted != ""

    @pytest.mark.asyncio
    async def test_get_security_status(self, security_service):
        """Test getting security status."""
        status = await security_service.get_security_status("test-tenant")
        assert status["success"] is True
        assert "security_metrics" in status

    @pytest.mark.asyncio
    async def test_get_security_alerts(self, security_service):
        """Test getting security alerts."""
        alerts = await security_service.get_security_alerts(
            tenant_id="test-tenant",
            severity="high",
            limit=10
        )
        assert alerts["success"] is True
        assert "alerts" in alerts

    @pytest.mark.asyncio
    async def test_create_compliance_rule(self, security_service):
        """Test creating compliance rules."""
        rule = await security_service.create_compliance_rule(
            tenant_id="test-tenant",
            rule_name="data_retention",
            rule_type="retention",
            parameters={"retention_days": 90},
            description="Data retention policy"
        )
        assert rule["success"] is True
        assert "rule_id" in rule

    @pytest.mark.asyncio
    async def test_get_compliance_rules(self, security_service):
        """Test getting compliance rules."""
        rules = await security_service.get_compliance_rules("test-tenant")
        assert rules["success"] is True
        assert "rules" in rules

    @pytest.mark.asyncio
    async def test_get_security_metrics(self, security_service):
        """Test getting security metrics."""
        metrics = await security_service.get_security_metrics(
            tenant_id="test-tenant",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )
        assert metrics["success"] is True
        assert "metrics" in metrics

    @pytest.mark.asyncio
    async def test_get_security_status(self, security_service):
        """Test getting security status."""
        status = await security_service.get_security_status()
        assert isinstance(status, dict)

    @pytest.mark.asyncio
    async def test_security_service_error_handling(self, security_service):
        """Test error handling in security service."""
        # Test with invalid tenant ID
        result = await security_service.log_security_event(
            tenant_id="",
            event_type="login"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_security_service_performance(self, security_service):
        """Test security service performance."""
        import time
        
        start_time = time.time()
        
        # Perform multiple security operations
        for i in range(10):
            await security_service.log_security_event(
                tenant_id=f"test-tenant-{i}",
                event_type="test",
                user_id=f"user-{i}"
            )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (5 seconds)
        assert execution_time < 5.0

    @pytest.mark.asyncio
    async def test_security_service_concurrent_operations(self, security_service):
        """Test concurrent security operations."""
        async def log_event(i):
            return await security_service.log_security_event(
                tenant_id=f"test-tenant-{i}",
                event_type="concurrent_test",
                user_id=f"user-{i}"
            )
        
        # Run 5 concurrent operations
        tasks = [log_event(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All operations should succeed
        assert all(result is True for result in results)
