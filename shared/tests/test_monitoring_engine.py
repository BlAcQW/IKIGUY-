"""
Tests for Monitoring and Observability Engine

This module provides comprehensive tests for the monitoring engine,
covering logging, metrics, health checks, alerts, tracing, and performance benchmarking.
"""

import asyncio
import json
import pytest
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

from ..monitoring.engine import MonitoringEngine
from ..monitoring.interfaces import (
    LogRecord, Metric, HealthCheck, Alert, TraceSpan, PerformanceBenchmark,
    LogLevel, MetricType, HealthStatus, AlertSeverity
)


class SimpleStorageAdapter:
    """Simple in-memory storage adapter for testing"""
    
    def __init__(self):
        self.tables = {}
        self.schemas = {}
    
    async def create_table(self, table_name: str, schema: Dict[str, str]):
        """Create a table with the given schema"""
        self.tables[table_name] = []
        self.schemas[table_name] = schema
    
    async def insert(self, table_name: str, data: Dict[str, Any]):
        """Insert data into a table"""
        if table_name not in self.tables:
            await self.create_table(table_name, {})
        
        # Add a unique ID if not present
        if "id" not in data and any("PRIMARY KEY" in col for col in self.schemas.get(table_name, {}).values()):
            for col, schema in self.schemas.get(table_name, {}).items():
                if "PRIMARY KEY" in schema:
                    if col not in data:
                        data[col] = str(uuid.uuid4())
                    break
        
        self.tables[table_name].append(data.copy())
    
    async def select(self, table_name: str, filters: Dict[str, Any] = None, limit: int = None):
        """Select data from a table with filters"""
        if table_name not in self.tables:
            return []
        
        results = self.tables[table_name].copy()
        
        if filters:
            filtered_results = []
            for row in results:
                match = True
                for key, value in filters.items():
                    if key not in row:
                        match = False
                        break
                    
                    if isinstance(value, dict) and "$gte" in value:
                        # Handle greater than or equal condition
                        if key not in row or row[key] < value["$gte"]:
                            match = False
                            break
                    elif isinstance(value, dict) and "$lte" in value:
                        # Handle less than or equal condition
                        if key not in row or row[key] > value["$lte"]:
                            match = False
                            break
                    elif row[key] != value:
                        match = False
                        break
                
                if match:
                    filtered_results.append(row)
            
            results = filtered_results
        
        if limit:
            results = results[:limit]
        
        return results
    
    async def select_one(self, table_name: str, filters: Dict[str, Any] = None):
        """Select one record from a table"""
        results = await self.select(table_name, filters, limit=1)
        return results[0] if results else None
    
    async def upsert(self, table_name: str, data: Dict[str, Any]):
        """Upsert data into a table"""
        if table_name not in self.tables:
            await self.create_table(table_name, {})
        
        # Check if record exists based on primary key
        schema = self.schemas.get(table_name, {})
        primary_key = None
        for col, col_schema in schema.items():
            if "PRIMARY KEY" in col_schema:
                primary_key = col
                break
        
        if primary_key and primary_key in data:
            # Try to update existing record
            for i, row in enumerate(self.tables[table_name]):
                if row.get(primary_key) == data[primary_key]:
                    self.tables[table_name][i].update(data)
                    return
        
        # Insert new record
        await self.insert(table_name, data)


@pytest.fixture
def storage_backend():
    """Storage backend fixture"""
    return SimpleStorageAdapter()


@pytest.fixture
def monitoring_engine(storage_backend):
    """Monitoring engine fixture"""
    return MonitoringEngine(storage_backend)


class TestMonitoringEngine:
    """Test cases for MonitoringEngine"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, monitoring_engine):
        """Test monitoring engine initialization"""
        # Trigger initialization
        await monitoring_engine.get_system_health()
        
        # Verify tables are created
        assert "logs" in monitoring_engine.storage.tables
        assert "metrics" in monitoring_engine.storage.tables
        assert "health_checks" in monitoring_engine.storage.tables
        assert "alerts" in monitoring_engine.storage.tables
        assert "trace_spans" in monitoring_engine.storage.tables
        assert "performance_benchmarks" in monitoring_engine.storage.tables
        assert "monitoring_settings" in monitoring_engine.storage.tables
    
    # Logger Tests
    
    @pytest.mark.asyncio
    async def test_log_record(self, monitoring_engine):
        """Test logging a record"""
        log_record = LogRecord(
            log_id=str(uuid.uuid4()),
            tenant_id="test_tenant",
            component="test_component",
            level=LogLevel.INFO,
            message="Test log message",
            user_id="test_user"
        )
        
        result = await monitoring_engine.log(log_record)
        assert result is True
        
        # Verify log was stored
        logs = await monitoring_engine.get_logs(tenant_id="test_tenant")
        assert len(logs) == 1
        assert logs[0].message == "Test log message"
        assert logs[0].level == LogLevel.INFO
    
    @pytest.mark.asyncio
    async def test_get_logs_with_filters(self, monitoring_engine):
        """Test getting logs with various filters"""
        # Create test logs
        log1 = LogRecord(
            log_id=str(uuid.uuid4()),
            tenant_id="test_tenant",
            component="component1",
            level=LogLevel.INFO,
            message="Info message"
        )
        
        log2 = LogRecord(
            log_id=str(uuid.uuid4()),
            tenant_id="test_tenant",
            component="component2",
            level=LogLevel.ERROR,
            message="Error message"
        )
        
        await monitoring_engine.log(log1)
        await monitoring_engine.log(log2)
        
        # Test component filter
        logs = await monitoring_engine.get_logs(component="component1")
        assert len(logs) == 1
        assert logs[0].component == "component1"
        
        # Test level filter
        logs = await monitoring_engine.get_logs(level=LogLevel.ERROR)
        assert len(logs) == 1
        assert logs[0].level == LogLevel.ERROR
    
    @pytest.mark.asyncio
    async def test_export_logs(self, monitoring_engine):
        """Test exporting logs"""
        # Create test log
        log_record = LogRecord(
            log_id=str(uuid.uuid4()),
            tenant_id="test_tenant",
            component="test_component",
            level=LogLevel.INFO,
            message="Test export message"
        )
        await monitoring_engine.log(log_record)
        
        # Test JSON export
        json_export = await monitoring_engine.export_logs(tenant_id="test_tenant", format="json")
        assert json_export
        data = json.loads(json_export)
        assert len(data) == 1
        assert data[0]["message"] == "Test export message"
        
        # Test CSV export
        csv_export = await monitoring_engine.export_logs(tenant_id="test_tenant", format="csv")
        assert csv_export
        assert "Test export message" in csv_export
    
    # Metrics Tests
    
    @pytest.mark.asyncio
    async def test_record_metric(self, monitoring_engine):
        """Test recording a metric"""
        metric = Metric(
            metric_id=str(uuid.uuid4()),
            tenant_id="test_tenant",
            name="test_metric",
            type=MetricType.COUNTER,
            value=42,
            description="Test metric"
        )
        
        result = await monitoring_engine.record_metric(metric)
        assert result is True
        
        # Verify metric was stored
        metrics = await monitoring_engine.get_metrics(tenant_id="test_tenant")
        assert len(metrics) == 1
        assert metrics[0].name == "test_metric"
        assert metrics[0].value == 42
    
    @pytest.mark.asyncio
    async def test_get_metric_summary(self, monitoring_engine):
        """Test getting metric summary"""
        # Create test metrics
        for i in range(5):
            metric = Metric(
                metric_id=str(uuid.uuid4()),
                tenant_id="test_tenant",
                name="test_metric",
                type=MetricType.GAUGE,
                value=i + 1
            )
            await monitoring_engine.record_metric(metric)
        
        summary = await monitoring_engine.get_metric_summary(tenant_id="test_tenant", name="test_metric")
        assert summary["count"] == 5
        assert summary["min_value"] == 1
        assert summary["max_value"] == 5
        assert summary["avg_value"] == 3.0
    
    # Health Check Tests
    
    @pytest.mark.asyncio
    async def test_register_health_check(self, monitoring_engine):
        """Test registering a health check"""
        async def test_check(tenant_id):
            return True
        
        result = await monitoring_engine.register_check("test_component", "test_check", test_check)
        assert result is True
        assert "test_component" in monitoring_engine.health_checks
        assert "test_check" in monitoring_engine.health_checks["test_component"]
    
    @pytest.mark.asyncio
    async def test_run_health_checks(self, monitoring_engine):
        """Test running health checks"""
        # Register a healthy check
        async def healthy_check(tenant_id):
            return True
        
        # Register an unhealthy check
        async def unhealthy_check(tenant_id):
            return False
        
        await monitoring_engine.register_check("test_component", "healthy_check", healthy_check)
        await monitoring_engine.register_check("test_component", "unhealthy_check", unhealthy_check)
        
        checks = await monitoring_engine.run_health_checks("test_tenant")
        assert len(checks) == 2
        
        healthy_checks = [c for c in checks if c.status == HealthStatus.HEALTHY]
        unhealthy_checks = [c for c in checks if c.status == HealthStatus.UNHEALTHY]
        
        assert len(healthy_checks) == 1
        assert len(unhealthy_checks) == 1
    
    @pytest.mark.asyncio
    async def test_get_health_status(self, monitoring_engine):
        """Test getting health status"""
        # Register checks
        async def healthy_check(tenant_id):
            return True
        
        async def unhealthy_check(tenant_id):
            return False
        
        await monitoring_engine.register_check("test_component", "healthy_check", healthy_check)
        await monitoring_engine.register_check("test_component", "unhealthy_check", unhealthy_check)
        
        status = await monitoring_engine.get_health_status("test_tenant")
        assert "overall_status" in status
        assert "healthy_checks" in status
        assert "total_checks" in status
        assert status["total_checks"] == 2
    
    # Alert Tests
    
    @pytest.mark.asyncio
    async def test_create_alert(self, monitoring_engine):
        """Test creating an alert"""
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            tenant_id="test_tenant",
            title="Test Alert",
            message="Test alert message",
            severity=AlertSeverity.HIGH,
            category="test"
        )
        
        result = await monitoring_engine.create_alert(alert)
        assert result is True
        
        # Verify alert was stored
        alerts = await monitoring_engine.get_alerts(tenant_id="test_tenant")
        assert len(alerts) == 1
        assert alerts[0].title == "Test Alert"
        assert alerts[0].severity == AlertSeverity.HIGH
    
    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, monitoring_engine):
        """Test acknowledging an alert"""
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            tenant_id="test_tenant",
            title="Test Alert",
            message="Test alert message",
            severity=AlertSeverity.MEDIUM,
            category="test"
        )
        await monitoring_engine.create_alert(alert)
        
        result = await monitoring_engine.acknowledge_alert(alert.alert_id, "test_user")
        assert result is True
        
        # Verify alert was acknowledged
        alerts = await monitoring_engine.get_alerts(tenant_id="test_tenant")
        assert len(alerts) == 1
        assert alerts[0].acknowledged is True
        assert alerts[0].acknowledged_by == "test_user"
    
    @pytest.mark.asyncio
    async def test_resolve_alert(self, monitoring_engine):
        """Test resolving an alert"""
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            tenant_id="test_tenant",
            title="Test Alert",
            message="Test alert message",
            severity=AlertSeverity.LOW,
            category="test"
        )
        await monitoring_engine.create_alert(alert)
        
        result = await monitoring_engine.resolve_alert(alert.alert_id, "test_user")
        assert result is True
        
        # Verify alert was resolved
        alerts = await monitoring_engine.get_alerts(tenant_id="test_tenant")
        assert len(alerts) == 1
        assert alerts[0].resolved is True
        assert alerts[0].resolved_by == "test_user"
    
    # Tracing Tests
    
    @pytest.mark.asyncio
    async def test_start_end_span(self, monitoring_engine):
        """Test starting and ending a span"""
        span_id = await monitoring_engine.start_span(
            name="test_span",
            tenant_id="test_tenant",
            component="test_component",
            operation="test_operation"
        )
        
        assert span_id in monitoring_engine.active_spans
        
        # Add some tags and logs
        await monitoring_engine.add_span_tag(span_id, "test_tag", "test_value")
        await monitoring_engine.add_span_log(span_id, "Test log message")
        
        result = await monitoring_engine.end_span(span_id)
        assert result is True
        
        # Verify span was removed from active spans
        assert span_id not in monitoring_engine.active_spans
    
    @pytest.mark.asyncio
    async def test_get_trace(self, monitoring_engine):
        """Test getting a trace"""
        trace_id = str(uuid.uuid4())
        
        # Create spans in a trace
        span1_id = await monitoring_engine.start_span(
            name="parent_span",
            trace_id=trace_id,
            tenant_id="test_tenant",
            component="test_component"
        )
        
        span2_id = await monitoring_engine.start_span(
            name="child_span",
            trace_id=trace_id,
            parent_span_id=span1_id,
            tenant_id="test_tenant",
            component="test_component"
        )
        
        await monitoring_engine.end_span(span1_id)
        await monitoring_engine.end_span(span2_id)
        
        # Get the trace
        spans = await monitoring_engine.get_trace(trace_id)
        assert len(spans) == 2
        
        span_names = [span.name for span in spans]
        assert "parent_span" in span_names
        assert "child_span" in span_names
    
    # Performance Benchmark Tests
    
    @pytest.mark.asyncio
    async def test_run_benchmark(self, monitoring_engine):
        """Test running a performance benchmark"""
        async def test_operation():
            await asyncio.sleep(0.01)  # Simulate some work
            return "success"
        
        benchmark = await monitoring_engine.run_benchmark(
            name="test_benchmark",
            operation=test_operation,
            iterations=5,
            tenant_id="test_tenant",
            component="test_component"
        )
        
        assert benchmark.name == "test_benchmark"
        assert benchmark.iterations == 5
        assert benchmark.success_rate == 100.0
        assert benchmark.avg_duration > 0
    
    @pytest.mark.asyncio
    async def test_get_benchmarks(self, monitoring_engine):
        """Test getting benchmarks"""
        async def test_operation():
            await asyncio.sleep(0.01)
        
        # Run a benchmark
        await monitoring_engine.run_benchmark(
            name="test_benchmark",
            operation=test_operation,
            iterations=3,
            tenant_id="test_tenant",
            component="test_component"
        )
        
        benchmarks = await monitoring_engine.get_benchmarks(tenant_id="test_tenant")
        assert len(benchmarks) == 1
        assert benchmarks[0].name == "test_benchmark"
    
    @pytest.mark.asyncio
    async def test_get_benchmark_summary(self, monitoring_engine):
        """Test getting benchmark summary"""
        async def test_operation():
            await asyncio.sleep(0.01)
        
        # Run benchmarks
        await monitoring_engine.run_benchmark(
            name="benchmark1",
            operation=test_operation,
            iterations=3,
            tenant_id="test_tenant",
            component="component1"
        )
        
        await monitoring_engine.run_benchmark(
            name="benchmark2",
            operation=test_operation,
            iterations=3,
            tenant_id="test_tenant",
            component="component2"
        )
        
        summary = await monitoring_engine.get_benchmark_summary(tenant_id="test_tenant")
        assert summary["total_benchmarks"] == 2
        assert "component1" in summary["components"]
        assert "component2" in summary["components"]
    
    # Monitoring Manager Tests
    
    @pytest.mark.asyncio
    async def test_initialize_monitoring(self, monitoring_engine):
        """Test initializing monitoring for a tenant"""
        result = await monitoring_engine.initialize_monitoring("test_tenant")
        assert result is True
        
        # Verify settings were created
        settings = await monitoring_engine.storage.select_one(
            "monitoring_settings", {"tenant_id": "test_tenant"}
        )
        assert settings is not None
        assert "settings" in settings
    
    @pytest.mark.asyncio
    async def test_get_monitoring_dashboard(self, monitoring_engine):
        """Test getting monitoring dashboard"""
        # Initialize monitoring
        await monitoring_engine.initialize_monitoring("test_tenant")
        
        # Create some test data
        log_record = LogRecord(
            log_id=str(uuid.uuid4()),
            tenant_id="test_tenant",
            component="test_component",
            level=LogLevel.INFO,
            message="Dashboard test log"
        )
        await monitoring_engine.log(log_record)
        
        metric = Metric(
            metric_id=str(uuid.uuid4()),
            tenant_id="test_tenant",
            name="dashboard_metric",
            type=MetricType.COUNTER,
            value=100
        )
        await monitoring_engine.record_metric(metric)
        
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            tenant_id="test_tenant",
            title="Dashboard Alert",
            message="Test alert for dashboard",
            severity=AlertSeverity.MEDIUM,
            category="test"
        )
        await monitoring_engine.create_alert(alert)
        
        # Get dashboard
        dashboard = await monitoring_engine.get_monitoring_dashboard("test_tenant")
        
        assert dashboard["tenant_id"] == "test_tenant"
        assert "health_status" in dashboard
        assert "log_summary" in dashboard
        assert "metrics_summary" in dashboard
        assert "alerts_summary" in dashboard
        assert "performance_summary" in dashboard
    
    @pytest.mark.asyncio
    async def test_get_system_health(self, monitoring_engine):
        """Test getting system health"""
        health = await monitoring_engine.get_system_health()
        
        assert "timestamp" in health
        assert "overall_health" in health
        assert "total_alerts" in health
        assert "critical_alerts" in health
        assert "total_metrics" in health
        assert "performance_summary" in health
        assert "active_traces" in health
        assert "active_spans" in health
    
    @pytest.mark.asyncio
    async def test_export_monitoring_data(self, monitoring_engine):
        """Test exporting monitoring data"""
        # Initialize monitoring and create test data
        await monitoring_engine.initialize_monitoring("test_tenant")
        
        log_record = LogRecord(
            log_id=str(uuid.uuid4()),
            tenant_id="test_tenant",
            component="test_component",
            level=LogLevel.INFO,
            message="Export test log"
        )
        await monitoring_engine.log(log_record)
        
        # Test JSON export
        json_export = await monitoring_engine.export_monitoring_data("test_tenant", format="json")
        assert json_export
        data = json.loads(json_export)
        assert data["tenant_id"] == "test_tenant"
        assert "logs" in data
        assert "metrics" in data
        assert "alerts" in data
        assert "benchmarks" in data
        
        # Test CSV export
        csv_export = await monitoring_engine.export_monitoring_data("test_tenant", format="csv")
        assert csv_export
        assert "Export test log" in csv_export


class TestMonitoringEngineIntegration:
    """Integration tests for MonitoringEngine"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, monitoring_engine):
        """Test a complete monitoring workflow"""
        # Initialize monitoring
        await monitoring_engine.initialize_monitoring("test_tenant")
        
        # Start a trace
        trace_id = str(uuid.uuid4())
        span_id = await monitoring_engine.start_span(
            name="workflow_span",
            trace_id=trace_id,
            tenant_id="test_tenant",
            component="workflow_component"
        )
        
        # Log some events
        log_record = LogRecord(
            log_id=str(uuid.uuid4()),
            tenant_id="test_tenant",
            component="workflow_component",
            level=LogLevel.INFO,
            message="Workflow started",
            trace_id=trace_id,
            span_id=span_id
        )
        await monitoring_engine.log(log_record)
        
        # Record metrics
        metric = Metric(
            metric_id=str(uuid.uuid4()),
            tenant_id="test_tenant",
            name="workflow_metric",
            type=MetricType.COUNTER,
            value=1,
            labels={"workflow": "test"}
        )
        await monitoring_engine.record_metric(metric)
        
        # Create an alert
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            tenant_id="test_tenant",
            title="Workflow Alert",
            message="Workflow completed with warnings",
            severity=AlertSeverity.MEDIUM,
            category="workflow"
        )
        await monitoring_engine.create_alert(alert)
        
        # End the span
        await monitoring_engine.end_span(span_id)
        
        # Verify all data is accessible
        logs = await monitoring_engine.get_logs(tenant_id="test_tenant")
        assert len(logs) == 1
        
        metrics = await monitoring_engine.get_metrics(tenant_id="test_tenant")
        assert len(metrics) == 1
        
        alerts = await monitoring_engine.get_alerts(tenant_id="test_tenant")
        assert len(alerts) == 1
        
        spans = await monitoring_engine.get_trace(trace_id)
        assert len(spans) == 1
        
        # Get dashboard
        dashboard = await monitoring_engine.get_monitoring_dashboard("test_tenant")
        assert dashboard["log_summary"]["total_logs"] == 1
        assert dashboard["metrics_summary"]["total_metrics"] == 1
        assert dashboard["alerts_summary"]["total_alerts"] == 1
    
    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(self, monitoring_engine):
        """Test multi-tenant isolation"""
        # Initialize monitoring for two tenants
        await monitoring_engine.initialize_monitoring("tenant1")
        await monitoring_engine.initialize_monitoring("tenant2")
        
        # Create data for tenant1
        log1 = LogRecord(
            log_id=str(uuid.uuid4()),
            tenant_id="tenant1",
            component="test_component",
            level=LogLevel.INFO,
            message="Tenant 1 log"
        )
        await monitoring_engine.log(log1)
        
        metric1 = Metric(
            metric_id=str(uuid.uuid4()),
            tenant_id="tenant1",
            name="test_metric",
            type=MetricType.COUNTER,
            value=100
        )
        await monitoring_engine.record_metric(metric1)
        
        # Create data for tenant2
        log2 = LogRecord(
            log_id=str(uuid.uuid4()),
            tenant_id="tenant2",
            component="test_component",
            level=LogLevel.INFO,
            message="Tenant 2 log"
        )
        await monitoring_engine.log(log2)
        
        metric2 = Metric(
            metric_id=str(uuid.uuid4()),
            tenant_id="tenant2",
            name="test_metric",
            type=MetricType.COUNTER,
            value=200
        )
        await monitoring_engine.record_metric(metric2)
        
        # Verify isolation
        tenant1_logs = await monitoring_engine.get_logs(tenant_id="tenant1")
        tenant2_logs = await monitoring_engine.get_logs(tenant_id="tenant2")
        
        assert len(tenant1_logs) == 1
        assert len(tenant2_logs) == 1
        assert tenant1_logs[0].message == "Tenant 1 log"
        assert tenant2_logs[0].message == "Tenant 2 log"
        
        tenant1_metrics = await monitoring_engine.get_metrics(tenant_id="tenant1")
        tenant2_metrics = await monitoring_engine.get_metrics(tenant_id="tenant2")
        
        assert len(tenant1_metrics) == 1
        assert len(tenant2_metrics) == 1
        assert tenant1_metrics[0].value == 100
        assert tenant2_metrics[0].value == 200
    
    @pytest.mark.asyncio
    async def test_error_handling(self, monitoring_engine):
        """Test error handling in monitoring operations"""
        # Test logging with invalid data (should not crash)
        invalid_log = LogRecord(
            log_id=str(uuid.uuid4()),
            tenant_id="test_tenant",
            component="test_component",
            level=LogLevel.ERROR,
            message="Test error log"
        )
        
        # This should not raise an exception
        result = await monitoring_engine.log(invalid_log)
        assert result is True
        
        # Test health check with exception
        async def failing_check(tenant_id):
            raise Exception("Health check failed")
        
        await monitoring_engine.register_check("test_component", "failing_check", failing_check)
        
        checks = await monitoring_engine.run_health_checks("test_tenant")
        assert len(checks) == 1
        assert checks[0].status == HealthStatus.UNHEALTHY
        assert checks[0].error_message == "Health check failed"
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self, monitoring_engine):
        """Test performance monitoring capabilities"""
        # Run a benchmark
        async def slow_operation():
            await asyncio.sleep(0.05)
        
        async def fast_operation():
            await asyncio.sleep(0.01)
        
        # Run benchmarks
        slow_benchmark = await monitoring_engine.run_benchmark(
            name="slow_operation",
            operation=slow_operation,
            iterations=3,
            tenant_id="test_tenant"
        )
        
        fast_benchmark = await monitoring_engine.run_benchmark(
            name="fast_operation",
            operation=fast_operation,
            iterations=3,
            tenant_id="test_tenant"
        )
        
        # Verify performance differences are captured
        assert slow_benchmark.avg_duration > fast_benchmark.avg_duration
        assert slow_benchmark.success_rate == 100.0
        assert fast_benchmark.success_rate == 100.0
        
        # Get benchmark summary
        summary = await monitoring_engine.get_benchmark_summary(tenant_id="test_tenant")
        assert summary["total_benchmarks"] == 2
        assert summary["avg_success_rate"] == 100.0
