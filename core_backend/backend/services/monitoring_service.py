"""
Monitoring service that integrates shared monitoring and observability library.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
from uuid import UUID, uuid4
import logging

from apps.shared.monitoring import MonitoringEngine
from apps.shared.monitoring import (
    LogRecord, Metric, HealthCheck, Alert, TraceSpan, PerformanceBenchmark,
    LogLevel, MetricType, HealthStatus, AlertSeverity
)
from apps.shared.storage import MemoryStorageBackend

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for monitoring and observability using shared libraries."""

    def __init__(self, storage_backend=None):
        """
        Initialize the monitoring service.

        Args:
            storage_backend: Storage backend for monitoring data. Defaults to in-memory.
        """
        if storage_backend is None:
            from apps.shared.storage.interfaces import StorageConfig
            config = StorageConfig(backend_type="memory", connection_string="memory://")
            storage_backend = MemoryStorageBackend(config)
        
        self.monitoring_engine = MonitoringEngine(storage_backend)
        # Note: _ensure_initialized will be called when needed

    async def _ensure_initialized(self):
        """Ensure the monitoring engine is initialized."""
        try:
            await self.monitoring_engine.get_system_health()
        except Exception:
            # This will trigger initialization
            pass

    async def log(
        self,
        tenant_id: str,
        component: str,
        level: LogLevel,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None
    ) -> bool:
        """
        Log a message.

        Args:
            tenant_id: Tenant identifier
            component: Component name
            level: Log level
            message: Log message
            metadata: Additional metadata
            trace_id: Trace identifier
            span_id: Span identifier

        Returns:
            bool: True if log was recorded successfully
        """
        try:
            record = LogRecord(
                log_id=str(uuid4()),
                tenant_id=tenant_id,
                component=component,
                level=level,
                message=message,
                timestamp=datetime.utcnow(),
                trace_id=trace_id,
                span_id=span_id,
                metadata=metadata or {}
            )
            return await self.monitoring_engine.log(record)
        except Exception as e:
            logger.error(f"Failed to log message: {e}")
            return False

    async def record_metric(
        self,
        tenant_id: str,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.COUNTER,
        labels: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        unit: Optional[str] = None
    ) -> bool:
        """
        Record a metric.

        Args:
            tenant_id: Tenant identifier
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            labels: Metric labels
            description: Metric description
            unit: Metric unit

        Returns:
            bool: True if metric was recorded successfully
        """
        try:
            metric = Metric(
                metric_id=str(uuid4()),
                tenant_id=tenant_id,
                name=name,
                type=metric_type,
                value=value,
                timestamp=datetime.utcnow(),
                labels=labels or {},
                description=description,
                unit=unit
            )
            return await self.monitoring_engine.record_metric(metric)
        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
            return False

    async def register_health_check(
        self,
        component: str,
        name: str,
        check_func: callable
    ) -> bool:
        """
        Register a health check.

        Args:
            component: Component name
            name: Health check name
            check_func: Health check function

        Returns:
            bool: True if health check was registered successfully
        """
        try:
            return await self.monitoring_engine.register_check(component, name, check_func)
        except Exception as e:
            logger.error(f"Failed to register health check: {e}")
            return False

    async def run_health_checks(self, tenant_id: Optional[str] = None) -> List[HealthCheck]:
        """
        Run all health checks.

        Args:
            tenant_id: Tenant ID for tenant-specific checks

        Returns:
            List[HealthCheck]: List of health check results
        """
        try:
            return await self.monitoring_engine.run_health_checks(tenant_id)
        except Exception as e:
            logger.error(f"Failed to run health checks: {e}")
            return []

    async def create_alert(
        self,
        tenant_id: str,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create an alert.

        Args:
            tenant_id: Tenant identifier
            title: Alert title
            message: Alert message
            severity: Alert severity
            category: Alert category
            metadata: Additional metadata

        Returns:
            bool: True if alert was created successfully
        """
        try:
            from uuid import uuid4
            alert = Alert(
                alert_id=str(uuid4()),
                tenant_id=tenant_id,
                title=title,
                message=message,
                severity=severity,
                category=category,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            return await self.monitoring_engine.create_alert(alert)
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return False

    async def get_alerts(
        self,
        tenant_id: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        acknowledged: Optional[bool] = None,
        resolved: Optional[bool] = None,
        limit: Optional[int] = None
    ) -> List[Alert]:
        """
        Get alerts.

        Args:
            tenant_id: Tenant identifier filter
            severity: Severity filter
            acknowledged: Acknowledged filter
            resolved: Resolved filter
            limit: Maximum number of alerts to return

        Returns:
            List[Alert]: List of alerts
        """
        try:
            return await self.monitoring_engine.get_alerts(
                tenant_id, severity, acknowledged, resolved, limit
            )
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []

    async def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str
    ) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert identifier
            acknowledged_by: User who acknowledged the alert

        Returns:
            bool: True if alert was acknowledged successfully
        """
        try:
            return await self.monitoring_engine.acknowledge_alert(alert_id, acknowledged_by)
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
            return False

    async def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str
    ) -> bool:
        """
        Resolve an alert.

        Args:
            alert_id: Alert identifier
            resolved_by: User who resolved the alert

        Returns:
            bool: True if alert was resolved successfully
        """
        try:
            return await self.monitoring_engine.resolve_alert(alert_id, resolved_by)
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            return False

    async def start_span(
        self,
        name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        component: str = "unknown",
        operation: str = "unknown"
    ) -> str:
        """
        Start a distributed tracing span.

        Args:
            name: Span name
            trace_id: Trace identifier
            parent_span_id: Parent span identifier
            tenant_id: Tenant identifier
            component: Component name
            operation: Operation name

        Returns:
            str: Span identifier
        """
        try:
            return await self.monitoring_engine.start_span(
                name, trace_id, parent_span_id, tenant_id, component, operation
            )
        except Exception as e:
            logger.error(f"Failed to start span: {e}")
            return ""

    async def end_span(
        self,
        span_id: str
    ) -> bool:
        """
        End a distributed tracing span.

        Args:
            span_id: Span identifier

        Returns:
            bool: True if span was ended successfully
        """
        try:
            return await self.monitoring_engine.end_span(span_id)
        except Exception as e:
            logger.error(f"Failed to end span: {e}")
            return False

    async def add_span_tags(
        self,
        span_id: str,
        tags: Dict[str, str]
    ) -> bool:
        """
        Add tags to a span.

        Args:
            span_id: Span identifier
            tags: Tags to add

        Returns:
            bool: True if tags were added successfully
        """
        try:
            # Add each tag individually since the engine only supports single tag addition
            for key, value in tags.items():
                success = await self.monitoring_engine.add_span_tag(span_id, key, value)
                if not success:
                    return False
            return True
        except Exception as e:
            logger.error(f"Failed to add span tags: {e}")
            return False

    async def add_span_logs(
        self,
        span_id: str,
        logs: List[Dict[str, Any]]
    ) -> bool:
        """
        Add logs to a span.

        Args:
            span_id: Span identifier
            logs: Logs to add

        Returns:
            bool: True if logs were added successfully
        """
        try:
            # Add each log individually since the engine only supports single log addition
            for log in logs:
                message = log.get("message", "")
                metadata = log.get("metadata", {})
                success = await self.monitoring_engine.add_span_log(span_id, message, metadata)
                if not success:
                    return False
            return True
        except Exception as e:
            logger.error(f"Failed to add span logs: {e}")
            return False

    async def run_benchmark(
        self,
        name: str,
        operation: callable,
        iterations: int = 100,
        tenant_id: Optional[str] = None,
        component: Optional[str] = None
    ) -> Optional[PerformanceBenchmark]:
        """
        Run a performance benchmark.

        Args:
            name: Benchmark name
            operation: Operation to benchmark
            iterations: Number of iterations
            tenant_id: Tenant identifier
            component: Component name

        Returns:
            PerformanceBenchmark: Benchmark results
        """
        try:
            return await self.monitoring_engine.run_benchmark(
                name, operation, iterations, tenant_id, component
            )
        except Exception as e:
            logger.error(f"Failed to run benchmark: {e}")
            return None

    async def get_monitoring_dashboard(
        self,
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Get monitoring dashboard data.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dict[str, Any]: Dashboard data
        """
        try:
            return await self.monitoring_engine.get_monitoring_dashboard(tenant_id)
        except Exception as e:
            logger.error(f"Failed to get monitoring dashboard: {e}")
            return {}

    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get overall system health.

        Returns:
            Dict[str, Any]: System health status
        """
        try:
            return await self.monitoring_engine.get_system_health()
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {}

    async def export_logs(
        self,
        tenant_id: Optional[str] = None,
        format: str = "json"
    ) -> str:
        """
        Export logs for a tenant.

        Args:
            tenant_id: Tenant identifier
            format: Export format (json, csv)

        Returns:
            str: Exported logs
        """
        try:
            return await self.monitoring_engine.export_logs(tenant_id, format)
        except Exception as e:
            logger.error(f"Failed to export logs: {e}")
            return ""

    async def get_metrics_summary(
        self,
        tenant_id: str,
        period: str = "hour"
    ) -> Dict[str, Any]:
        """
        Get metrics summary for a tenant.

        Args:
            tenant_id: Tenant identifier
            period: Time period (minute, hour, day)

        Returns:
            Dict[str, Any]: Metrics summary
        """
        try:
            return await self.monitoring_engine.get_metrics_summary(tenant_id, period)
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {}
