"""
Test suite for Core Backend Monitoring Service.

This module contains comprehensive tests for the Monitoring Service integration
with the shared monitoring and observability library.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from backend.services.monitoring_service import MonitoringService
from apps.shared.monitoring import (
    LogRecord, Metric, HealthCheck, Alert, TraceSpan, PerformanceBenchmark,
    LogLevel, MetricType, HealthStatus, AlertSeverity
)


class TestMonitoringService:
    """Test suite for Monitoring Service."""

    @pytest.fixture
    def monitoring_service(self):
        """Create a monitoring service instance for testing."""
        service = MonitoringService()
        return service

    @pytest.mark.asyncio
    async def test_monitoring_service_initialization(self, monitoring_service):
        """Test monitoring service initialization."""
        assert monitoring_service is not None
        assert hasattr(monitoring_service, 'monitoring_engine')
        assert monitoring_service.monitoring_engine is not None

    @pytest.mark.asyncio
    async def test_log_message(self, monitoring_service):
        """Test logging a message."""
        tenant_id = "test-tenant-123"
        component = "test-component"
        level = LogLevel.INFO
        message = "Test log message"
        metadata = {"test_key": "test_value"}

        result = await monitoring_service.log(
            tenant_id=tenant_id,
            component=component,
            level=level,
            message=message,
            metadata=metadata
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_record_metric(self, monitoring_service):
        """Test recording a metric."""
        tenant_id = "test-tenant-123"
        name = "test_metric"
        value = 42.5
        metric_type = MetricType.COUNTER
        labels = {"environment": "test"}
        description = "Test metric"
        unit = "requests"

        result = await monitoring_service.record_metric(
            tenant_id=tenant_id,
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels,
            description=description,
            unit=unit
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_register_health_check(self, monitoring_service):
        """Test registering a health check."""
        component = "test-component"
        name = "test-health-check"
        
        async def check_func():
            return {"status": "healthy", "message": "All systems operational"}

        result = await monitoring_service.register_health_check(
            component=component,
            name=name,
            check_func=check_func
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_run_health_checks(self, monitoring_service):
        """Test running health checks."""
        result = await monitoring_service.run_health_checks()

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_create_alert(self, monitoring_service):
        """Test creating an alert."""
        tenant_id = "test-tenant-123"
        title = "Test Alert"
        message = "This is a test alert"
        severity = AlertSeverity.MEDIUM
        category = "test"
        metadata = {"source": "test"}

        result = await monitoring_service.create_alert(
            tenant_id=tenant_id,
            title=title,
            message=message,
            severity=severity,
            category=category,
            metadata=metadata
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_alerts(self, monitoring_service):
        """Test getting alerts."""
        # First create an alert
        await monitoring_service.create_alert(
            tenant_id="test-tenant-123",
            title="Test Alert",
            message="Test message",
            severity=AlertSeverity.LOW
        )

        # Then get alerts
        alerts = await monitoring_service.get_alerts(
            tenant_id="test-tenant-123",
            limit=10
        )

        assert isinstance(alerts, list)

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, monitoring_service):
        """Test acknowledging an alert."""
        # First create an alert
        await monitoring_service.create_alert(
            tenant_id="test-tenant-123",
            title="Test Alert",
            message="Test message"
        )

        # Get the alert ID (this would normally come from the created alert)
        alerts = await monitoring_service.get_alerts(tenant_id="test-tenant-123")
        if alerts:
            alert_id = alerts[0].alert_id
            result = await monitoring_service.acknowledge_alert(
                alert_id=alert_id,
                acknowledged_by="test-user"
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_resolve_alert(self, monitoring_service):
        """Test resolving an alert."""
        # First create an alert
        await monitoring_service.create_alert(
            tenant_id="test-tenant-123",
            title="Test Alert",
            message="Test message"
        )

        # Get the alert ID (this would normally come from the created alert)
        alerts = await monitoring_service.get_alerts(tenant_id="test-tenant-123")
        if alerts:
            alert_id = alerts[0].alert_id
            result = await monitoring_service.resolve_alert(
                alert_id=alert_id,
                resolved_by="test-user"
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_start_span(self, monitoring_service):
        """Test starting a distributed tracing span."""
        name = "test-span"
        trace_id = "test-trace-123"
        tenant_id = "test-tenant-123"
        component = "test-component"
        operation = "test-operation"

        span_id = await monitoring_service.start_span(
            name=name,
            trace_id=trace_id,
            tenant_id=tenant_id,
            component=component,
            operation=operation
        )

        assert isinstance(span_id, str)
        assert len(span_id) > 0

    @pytest.mark.asyncio
    async def test_end_span(self, monitoring_service):
        """Test ending a distributed tracing span."""
        # First start a span
        span_id = await monitoring_service.start_span("test-span")

        # Then end it
        result = await monitoring_service.end_span(span_id=span_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_add_span_tags(self, monitoring_service):
        """Test adding tags to a span."""
        # First start a span
        span_id = await monitoring_service.start_span("test-span")

        # Then add tags
        tags = {"environment": "test", "version": "1.0.0"}
        result = await monitoring_service.add_span_tags(
            span_id=span_id,
            tags=tags
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_add_span_logs(self, monitoring_service):
        """Test adding logs to a span."""
        # First start a span
        span_id = await monitoring_service.start_span("test-span")

        # Then add logs
        logs = [
            {"message": "Test log 1", "level": "info"},
            {"message": "Test log 2", "level": "error"}
        ]
        result = await monitoring_service.add_span_logs(
            span_id=span_id,
            logs=logs
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_run_benchmark(self, monitoring_service):
        """Test running a performance benchmark."""
        name = "test-benchmark"
        tenant_id = "test-tenant-123"
        component = "test-component"

        async def test_operation():
            # Simulate some work
            import asyncio
            await asyncio.sleep(0.001)
            return "test result"

        result = await monitoring_service.run_benchmark(
            name=name,
            operation=test_operation,
            iterations=10,
            tenant_id=tenant_id,
            component=component
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_monitoring_dashboard(self, monitoring_service):
        """Test getting monitoring dashboard data."""
        tenant_id = "test-tenant-123"

        # Create some test data first
        await monitoring_service.log(
            tenant_id=tenant_id,
            component="test",
            level=LogLevel.INFO,
            message="Test log"
        )

        await monitoring_service.record_metric(
            tenant_id=tenant_id,
            name="test_metric",
            value=100.0
        )

        result = await monitoring_service.get_monitoring_dashboard(tenant_id)

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_system_health(self, monitoring_service):
        """Test getting system health."""
        result = await monitoring_service.get_system_health()

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_export_logs(self, monitoring_service):
        """Test exporting logs."""
        tenant_id = "test-tenant-123"

        # Create some test logs first
        await monitoring_service.log(
            tenant_id=tenant_id,
            component="test",
            level=LogLevel.INFO,
            message="Test log 1"
        )

        await monitoring_service.log(
            tenant_id=tenant_id,
            component="test",
            level=LogLevel.ERROR,
            message="Test log 2"
        )

        # Export logs
        result = await monitoring_service.export_logs(
            tenant_id=tenant_id,
            format="json"
        )

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_get_metrics_summary(self, monitoring_service):
        """Test getting metrics summary."""
        tenant_id = "test-tenant-123"

        # Create some test metrics first
        await monitoring_service.record_metric(
            tenant_id=tenant_id,
            name="requests_per_second",
            value=100.0
        )

        await monitoring_service.record_metric(
            tenant_id=tenant_id,
            name="error_rate",
            value=0.01
        )

        result = await monitoring_service.get_metrics_summary(
            tenant_id=tenant_id,
            period="hour"
        )

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_monitoring_service_error_handling(self, monitoring_service):
        """Test error handling in monitoring service."""
        # Test with invalid parameters
        result = await monitoring_service.log(
            tenant_id="",
            component="",
            level=LogLevel.INFO,
            message=""
        )

        # Should handle gracefully
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_monitoring_service_performance(self, monitoring_service):
        """Test monitoring service performance."""
        import time

        start_time = time.time()

        # Test multiple operations
        tenant_id = "test-tenant-123"
        
        # Log multiple messages
        for i in range(10):
            await monitoring_service.log(
                tenant_id=tenant_id,
                component="test",
                level=LogLevel.INFO,
                message=f"Test log {i}"
            )

        # Record multiple metrics
        for i in range(10):
            await monitoring_service.record_metric(
                tenant_id=tenant_id,
                name=f"metric_{i}",
                value=float(i)
            )

        end_time = time.time()
        execution_time = end_time - start_time

        # Performance should be reasonable (less than 2 seconds for 20 operations)
        assert execution_time < 2.0

    @pytest.mark.asyncio
    async def test_monitoring_service_concurrent_operations(self, monitoring_service):
        """Test concurrent monitoring operations."""
        import asyncio

        tenant_id = "test-tenant-123"

        # Create concurrent logging tasks
        async def log_message(i):
            return await monitoring_service.log(
                tenant_id=tenant_id,
                component="test",
                level=LogLevel.INFO,
                message=f"Concurrent log {i}"
            )

        # Create concurrent metric recording tasks
        async def record_metric(i):
            return await monitoring_service.record_metric(
                tenant_id=tenant_id,
                name=f"concurrent_metric_{i}",
                value=float(i)
            )

        # Run 10 concurrent operations
        tasks = []
        for i in range(5):
            tasks.append(log_message(i))
            tasks.append(record_metric(i))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All operations should succeed
        for result in results:
            assert not isinstance(result, Exception)

    @pytest.mark.asyncio
    async def test_monitoring_service_tenant_isolation(self, monitoring_service):
        """Test tenant isolation in monitoring service."""
        tenant1_id = "tenant-1"
        tenant2_id = "tenant-2"

        # Create logs for different tenants
        await monitoring_service.log(
            tenant_id=tenant1_id,
            component="test",
            level=LogLevel.INFO,
            message="Tenant 1 log"
        )

        await monitoring_service.log(
            tenant_id=tenant2_id,
            component="test",
            level=LogLevel.INFO,
            message="Tenant 2 log"
        )

        # Create metrics for different tenants
        await monitoring_service.record_metric(
            tenant_id=tenant1_id,
            name="tenant1_metric",
            value=100.0
        )

        await monitoring_service.record_metric(
            tenant_id=tenant2_id,
            name="tenant2_metric",
            value=200.0
        )

        # Export logs for each tenant
        tenant1_logs = await monitoring_service.export_logs(tenant1_id, "json")
        tenant2_logs = await monitoring_service.export_logs(tenant2_id, "json")

        # Verify tenant isolation
        assert "Tenant 1 log" in tenant1_logs
        assert "Tenant 2 log" in tenant2_logs
        assert "Tenant 1 log" not in tenant2_logs
        assert "Tenant 2 log" not in tenant1_logs
