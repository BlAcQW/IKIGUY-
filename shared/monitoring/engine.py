"""
Monitoring and Observability Engine

This module implements the comprehensive monitoring and observability system,
including logging, metrics, health checks, alerts, tracing, and performance benchmarking.
"""

import asyncio
import json
import statistics
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
import csv
import io

from .interfaces import (
    Logger, MetricsCollector, HealthChecker, AlertManager, Tracer,
    PerformanceBenchmarker, MonitoringManager,
    LogRecord, Metric, HealthCheck, Alert, TraceSpan, PerformanceBenchmark,
    LogLevel, MetricType, HealthStatus, AlertSeverity
)


class MonitoringEngine(Logger, MetricsCollector, HealthChecker, AlertManager, 
                      Tracer, PerformanceBenchmarker, MonitoringManager):
    """
    Comprehensive monitoring and observability engine implementation.
    
    This engine provides centralized logging, metrics collection, health checks,
    alerting, distributed tracing, performance benchmarking, and monitoring
    dashboard functionality.
    """
    
    def __init__(self, storage_backend):
        """
        Initialize the monitoring engine.
        
        Args:
            storage_backend: Storage backend for persisting monitoring data
        """
        self.storage = storage_backend
        self.health_checks: Dict[str, Dict[str, Callable]] = {}
        self.active_spans: Dict[str, TraceSpan] = {}
        self.active_traces: Dict[str, List[str]] = {}
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure monitoring tables are initialized"""
        if not self._initialized:
            await self._initialize_storage()
            self._initialized = True
    
    async def _initialize_storage(self):
        """Initialize storage tables for monitoring data"""
        # Logs table
        await self.storage.create_table("logs", {
            "log_id": "TEXT PRIMARY KEY",
            "tenant_id": "TEXT",
            "component": "TEXT",
            "level": "TEXT",
            "message": "TEXT",
            "timestamp": "TEXT",
            "trace_id": "TEXT",
            "span_id": "TEXT",
            "metadata": "TEXT",
            "user_id": "TEXT",
            "session_id": "TEXT"
        })
        
        # Metrics table
        await self.storage.create_table("metrics", {
            "metric_id": "TEXT PRIMARY KEY",
            "tenant_id": "TEXT",
            "name": "TEXT",
            "type": "TEXT",
            "value": "REAL",
            "timestamp": "TEXT",
            "labels": "TEXT",
            "description": "TEXT",
            "unit": "TEXT"
        })
        
        # Health checks table
        await self.storage.create_table("health_checks", {
            "check_id": "TEXT PRIMARY KEY",
            "tenant_id": "TEXT",
            "component": "TEXT",
            "name": "TEXT",
            "status": "TEXT",
            "timestamp": "TEXT",
            "response_time": "REAL",
            "details": "TEXT",
            "error_message": "TEXT"
        })
        
        # Alerts table
        await self.storage.create_table("alerts", {
            "alert_id": "TEXT PRIMARY KEY",
            "tenant_id": "TEXT",
            "title": "TEXT",
            "message": "TEXT",
            "severity": "TEXT",
            "category": "TEXT",
            "timestamp": "TEXT",
            "acknowledged": "BOOLEAN",
            "acknowledged_by": "TEXT",
            "acknowledged_at": "TEXT",
            "resolved": "BOOLEAN",
            "resolved_by": "TEXT",
            "resolved_at": "TEXT",
            "metadata": "TEXT"
        })
        
        # Trace spans table
        await self.storage.create_table("trace_spans", {
            "span_id": "TEXT PRIMARY KEY",
            "trace_id": "TEXT",
            "tenant_id": "TEXT",
            "name": "TEXT",
            "start_time": "TEXT",
            "end_time": "TEXT",
            "duration": "REAL",
            "parent_span_id": "TEXT",
            "component": "TEXT",
            "operation": "TEXT",
            "tags": "TEXT",
            "logs": "TEXT"
        })
        
        # Performance benchmarks table
        await self.storage.create_table("performance_benchmarks", {
            "benchmark_id": "TEXT PRIMARY KEY",
            "tenant_id": "TEXT",
            "name": "TEXT",
            "component": "TEXT",
            "operation": "TEXT",
            "start_time": "TEXT",
            "end_time": "TEXT",
            "duration": "REAL",
            "iterations": "INTEGER",
            "avg_duration": "REAL",
            "min_duration": "REAL",
            "max_duration": "REAL",
            "p95_duration": "REAL",
            "p99_duration": "REAL",
            "success_rate": "REAL",
            "metadata": "TEXT"
        })
        
        # Monitoring settings table
        await self.storage.create_table("monitoring_settings", {
            "tenant_id": "TEXT PRIMARY KEY",
            "settings": "TEXT",
            "updated_at": "TEXT"
        })
    
    # Logger Implementation
    
    async def log(self, record: LogRecord) -> bool:
        """
        Log a record.
        
        Args:
            record: LogRecord to log
            
        Returns:
            bool: True if successful, False otherwise
        """
        await self._ensure_initialized()
        
        try:
            await self.storage.insert("logs", {
                "log_id": record.log_id,
                "tenant_id": record.tenant_id,
                "component": record.component,
                "level": record.level.value,
                "message": record.message,
                "timestamp": record.timestamp.isoformat(),
                "trace_id": record.trace_id,
                "span_id": record.span_id,
                "metadata": json.dumps(record.metadata),
                "user_id": record.user_id,
                "session_id": record.session_id
            })
            return True
        except Exception as e:
            # Fallback to console logging if storage fails
            print(f"Failed to log to storage: {e}")
            return False
    
    async def get_logs(self, tenant_id: Optional[str] = None,
                      component: Optional[str] = None,
                      level: Optional[LogLevel] = None,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None,
                      limit: int = 100) -> List[LogRecord]:
        """
        Get logs with filters.
        
        Args:
            tenant_id: Filter by tenant ID
            component: Filter by component
            level: Filter by log level
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of logs to return
            
        Returns:
            List[LogRecord]: List of log records
        """
        await self._ensure_initialized()
        
        filters = {}
        if tenant_id:
            filters["tenant_id"] = tenant_id
        if component:
            filters["component"] = component
        if level:
            filters["level"] = level.value
        if start_time:
            filters["timestamp"] = {"$gte": start_time.isoformat()}
        if end_time:
            filters["timestamp"] = {"$lte": end_time.isoformat()}
        
        results = await self.storage.query("logs", filters, limit=limit)
        
        logs = []
        for result in results:
            log = LogRecord(
                log_id=result["log_id"],
                tenant_id=result.get("tenant_id"),
                component=result["component"],
                level=LogLevel(result["level"]),
                message=result["message"],
                timestamp=datetime.fromisoformat(result["timestamp"]),
                trace_id=result.get("trace_id"),
                span_id=result.get("span_id"),
                metadata=json.loads(result.get("metadata", "{}")),
                user_id=result.get("user_id"),
                session_id=result.get("session_id")
            )
            logs.append(log)
        
        return logs
    
    async def export_logs(self, tenant_id: Optional[str] = None,
                         format: str = "json") -> str:
        """
        Export logs in specified format.
        
        Args:
            tenant_id: Filter by tenant ID
            format: Export format (json, csv)
            
        Returns:
            str: Exported logs
        """
        logs = await self.get_logs(tenant_id=tenant_id, limit=1000)
        
        if format.lower() == "json":
            # Convert datetime objects to ISO format strings for JSON serialization
            log_dicts = []
            for log in logs:
                log_dict = log.dict()
                log_dict["timestamp"] = log_dict["timestamp"].isoformat()
                log_dicts.append(log_dict)
            return json.dumps(log_dicts, indent=2)
        
        elif format.lower() == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "log_id", "tenant_id", "component", "level", "message",
                "timestamp", "trace_id", "span_id", "user_id", "session_id"
            ])
            
            # Write data
            for log in logs:
                writer.writerow([
                    log.log_id, log.tenant_id, log.component, log.level.value,
                    log.message, log.timestamp.isoformat(), log.trace_id,
                    log.span_id, log.user_id, log.session_id
                ])
            
            return output.getvalue()
        
        else:
            return ""
    
    # MetricsCollector Implementation
    
    async def record_metric(self, metric: Metric) -> bool:
        """
        Record a metric.
        
        Args:
            metric: Metric to record
            
        Returns:
            bool: True if successful, False otherwise
        """
        await self._ensure_initialized()
        
        try:
            await self.storage.insert("metrics", {
                "metric_id": metric.metric_id,
                "tenant_id": metric.tenant_id,
                "name": metric.name,
                "type": metric.type.value,
                "value": metric.value,
                "timestamp": metric.timestamp.isoformat(),
                "labels": json.dumps(metric.labels),
                "description": metric.description,
                "unit": metric.unit
            })
            return True
        except Exception as e:
            print(f"Failed to record metric: {e}")
            return False
    
    async def get_metrics(self, tenant_id: Optional[str] = None,
                         name: Optional[str] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> List[Metric]:
        """
        Get metrics with filters.
        
        Args:
            tenant_id: Filter by tenant ID
            name: Filter by metric name
            start_time: Filter by start time
            end_time: Filter by end time
            
        Returns:
            List[Metric]: List of metrics
        """
        await self._ensure_initialized()
        
        filters = {}
        if tenant_id:
            filters["tenant_id"] = tenant_id
        if name:
            filters["name"] = name
        if start_time:
            filters["timestamp"] = {"$gte": start_time.isoformat()}
        if end_time:
            filters["timestamp"] = {"$lte": end_time.isoformat()}
        
        results = await self.storage.query("metrics", filters)
        
        metrics = []
        for result in results:
            metric = Metric(
                metric_id=result["metric_id"],
                tenant_id=result.get("tenant_id"),
                name=result["name"],
                type=MetricType(result["type"]),
                value=result["value"],
                timestamp=datetime.fromisoformat(result["timestamp"]),
                labels=json.loads(result.get("labels", "{}")),
                description=result.get("description"),
                unit=result.get("unit")
            )
            metrics.append(metric)
        
        return metrics
    
    async def get_metric_summary(self, tenant_id: Optional[str] = None,
                                name: Optional[str] = None,
                                period: str = "1h") -> Dict[str, Any]:
        """
        Get metric summary for a period.
        
        Args:
            tenant_id: Filter by tenant ID
            name: Filter by metric name
            period: Time period (e.g., "1h", "24h", "7d")
            
        Returns:
            Dict[str, Any]: Metric summary
        """
        # Calculate time range based on period
        end_time = datetime.utcnow()
        if period == "1h":
            start_time = end_time - timedelta(hours=1)
        elif period == "24h":
            start_time = end_time - timedelta(days=1)
        elif period == "7d":
            start_time = end_time - timedelta(days=7)
        else:
            start_time = end_time - timedelta(hours=1)  # Default to 1 hour
        
        metrics = await self.get_metrics(tenant_id=tenant_id, name=name,
                                       start_time=start_time, end_time=end_time)
        
        if not metrics:
            return {
                "count": 0,
                "min_value": 0,
                "max_value": 0,
                "avg_value": 0,
                "total_value": 0
            }
        
        values = [m.value for m in metrics]
        return {
            "count": len(metrics),
            "min_value": min(values),
            "max_value": max(values),
            "avg_value": sum(values) / len(values),
            "total_value": sum(values)
        }
    
    # HealthChecker Implementation
    
    async def register_check(self, component: str, name: str,
                           check_func: Callable) -> bool:
        """
        Register a health check.
        
        Args:
            component: Component name
            name: Health check name
            check_func: Health check function
            
        Returns:
            bool: True if successful, False otherwise
        """
        if component not in self.health_checks:
            self.health_checks[component] = {}
        
        self.health_checks[component][name] = check_func
        return True
    
    async def run_health_checks(self, tenant_id: Optional[str] = None) -> List[HealthCheck]:
        """
        Run all health checks.
        
        Args:
            tenant_id: Tenant ID for tenant-specific checks
            
        Returns:
            List[HealthCheck]: List of health check results
        """
        await self._ensure_initialized()
        
        checks = []
        for component, component_checks in self.health_checks.items():
            for name, check_func in component_checks.items():
                check_id = str(uuid.uuid4())
                start_time = time.time()
                
                try:
                    # Run the health check
                    if asyncio.iscoroutinefunction(check_func):
                        result = await check_func(tenant_id)
                    else:
                        result = check_func(tenant_id)
                    
                    response_time = time.time() - start_time
                    
                    if result is True or (isinstance(result, dict) and result.get("status") == "healthy"):
                        status = HealthStatus.HEALTHY
                        error_message = None
                        details = result if isinstance(result, dict) else {}
                    else:
                        status = HealthStatus.UNHEALTHY
                        error_message = str(result) if result else "Health check failed"
                        details = result if isinstance(result, dict) else {}
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    status = HealthStatus.UNHEALTHY
                    error_message = str(e)
                    details = {"exception": str(e)}
                
                health_check = HealthCheck(
                    check_id=check_id,
                    tenant_id=tenant_id,
                    component=component,
                    name=name,
                    status=status,
                    timestamp=datetime.utcnow(),
                    response_time=response_time,
                    details=details,
                    error_message=error_message
                )
                
                # Store the health check result
                await self.storage.insert("health_checks", {
                    "check_id": health_check.check_id,
                    "tenant_id": health_check.tenant_id,
                    "component": health_check.component,
                    "name": health_check.name,
                    "status": health_check.status.value,
                    "timestamp": health_check.timestamp.isoformat(),
                    "response_time": health_check.response_time,
                    "details": json.dumps(health_check.details),
                    "error_message": health_check.error_message
                })
                
                checks.append(health_check)
        
        return checks
    
    async def get_health_status(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get overall health status.
        
        Args:
            tenant_id: Tenant ID for tenant-specific status
            
        Returns:
            Dict[str, Any]: Overall health status
        """
        await self._ensure_initialized()
        
        # Run current health checks
        current_checks = await self.run_health_checks(tenant_id)
        
        # Get recent health checks from storage
        filters = {}
        if tenant_id:
            filters["tenant_id"] = tenant_id
        
        recent_checks = await self.storage.query("health_checks", filters, limit=100)
        
        # Calculate overall status
        healthy_count = sum(1 for check in current_checks if check.status == HealthStatus.HEALTHY)
        total_count = len(current_checks)
        
        if total_count == 0:
            overall_status = HealthStatus.HEALTHY
        elif healthy_count == total_count:
            overall_status = HealthStatus.HEALTHY
        elif healthy_count > total_count * 0.5:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNHEALTHY
        
        return {
            "overall_status": overall_status.value,
            "healthy_checks": healthy_count,
            "total_checks": total_count,
            "health_percentage": (healthy_count / total_count * 100) if total_count > 0 else 100,
            "current_checks": [check.dict() for check in current_checks],
            "recent_checks": len(recent_checks)
        }
    
    # AlertManager Implementation
    
    async def create_alert(self, alert: Alert) -> bool:
        """
        Create an alert.
        
        Args:
            alert: Alert to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        await self._ensure_initialized()
        
        try:
            await self.storage.insert("alerts", {
                "alert_id": alert.alert_id,
                "tenant_id": alert.tenant_id,
                "title": alert.title,
                "message": alert.message,
                "severity": alert.severity.value,
                "category": alert.category,
                "timestamp": alert.timestamp.isoformat(),
                "acknowledged": alert.acknowledged,
                "acknowledged_by": alert.acknowledged_by,
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                "resolved": alert.resolved,
                "resolved_by": alert.resolved_by,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                "metadata": json.dumps(alert.metadata)
            })
            return True
        except Exception as e:
            print(f"Failed to create alert: {e}")
            return False
    
    async def get_alerts(self, tenant_id: Optional[str] = None,
                        severity: Optional[AlertSeverity] = None,
                        acknowledged: Optional[bool] = None,
                        resolved: Optional[bool] = None,
                        limit: int = None) -> List[Alert]:
        """
        Get alerts with filters.
        
        Args:
            tenant_id: Filter by tenant ID
            severity: Filter by severity
            acknowledged: Filter by acknowledged status
            resolved: Filter by resolved status
            
        Returns:
            List[Alert]: List of alerts
        """
        await self._ensure_initialized()
        
        filters = {}
        if tenant_id:
            filters["tenant_id"] = tenant_id
        if severity:
            filters["severity"] = severity.value
        if acknowledged is not None:
            filters["acknowledged"] = acknowledged
        if resolved is not None:
            filters["resolved"] = resolved
        
        results = await self.storage.query("alerts", filters, limit=limit)
        
        alerts = []
        for result in results:
            alert = Alert(
                alert_id=result["alert_id"],
                tenant_id=result.get("tenant_id"),
                title=result["title"],
                message=result["message"],
                severity=AlertSeverity(result["severity"]),
                category=result["category"],
                timestamp=datetime.fromisoformat(result["timestamp"]),
                acknowledged=result["acknowledged"],
                acknowledged_by=result.get("acknowledged_by"),
                acknowledged_at=datetime.fromisoformat(result["acknowledged_at"]) if result.get("acknowledged_at") else None,
                resolved=result["resolved"],
                resolved_by=result.get("resolved_by"),
                resolved_at=datetime.fromisoformat(result["resolved_at"]) if result.get("resolved_at") else None,
                metadata=json.loads(result.get("metadata", "{}"))
            )
            alerts.append(alert)
        
        return alerts
    
    async def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert ID to acknowledge
            user_id: User ID acknowledging the alert
            
        Returns:
            bool: True if successful, False otherwise
        """
        await self._ensure_initialized()
        
        try:
            await self.storage.update("alerts", alert_id, {
                "acknowledged": True,
                "acknowledged_by": user_id,
                "acknowledged_at": datetime.utcnow().isoformat()
            })
            return True
        except Exception as e:
            print(f"Failed to acknowledge alert: {e}")
            return False
    
    async def resolve_alert(self, alert_id: str, user_id: str) -> bool:
        """
        Resolve an alert.
        
        Args:
            alert_id: Alert ID to resolve
            user_id: User ID resolving the alert
            
        Returns:
            bool: True if successful, False otherwise
        """
        await self._ensure_initialized()
        
        try:
            await self.storage.update("alerts", alert_id, {
                "resolved": True,
                "resolved_by": user_id,
                "resolved_at": datetime.utcnow().isoformat()
            })
            return True
        except Exception as e:
            print(f"Failed to resolve alert: {e}")
            return False
    
    # Tracer Implementation
    
    async def start_span(self, name: str, trace_id: Optional[str] = None,
                        parent_span_id: Optional[str] = None,
                        tenant_id: Optional[str] = None,
                        component: str = "unknown",
                        operation: str = "unknown") -> str:
        """
        Start a new span.
        
        Args:
            name: Span name
            trace_id: Trace ID (generated if not provided)
            parent_span_id: Parent span ID
            tenant_id: Tenant ID
            component: Component name
            operation: Operation name
            
        Returns:
            str: Span ID
        """
        await self._ensure_initialized()
        
        if not trace_id:
            trace_id = str(uuid.uuid4())
        
        span_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        span = TraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            tenant_id=tenant_id,
            name=name,
            start_time=start_time,
            component=component,
            operation=operation
        )
        
        # Store active span
        self.active_spans[span_id] = span
        
        # Track trace
        if trace_id not in self.active_traces:
            self.active_traces[trace_id] = []
        self.active_traces[trace_id].append(span_id)
        
        return span_id
    
    async def end_span(self, span_id: str) -> bool:
        """
        End a span.
        
        Args:
            span_id: Span ID to end
            
        Returns:
            bool: True if successful, False otherwise
        """
        if span_id not in self.active_spans:
            return False
        
        span = self.active_spans[span_id]
        end_time = datetime.utcnow()
        duration = (end_time - span.start_time).total_seconds()
        
        # Update span
        span.end_time = end_time
        span.duration = duration
        
        # Store span in database
        try:
            await self.storage.insert("trace_spans", {
                "span_id": span.span_id,
                "trace_id": span.trace_id,
                "tenant_id": span.tenant_id,
                "name": span.name,
                "start_time": span.start_time.isoformat(),
                "end_time": span.end_time.isoformat(),
                "duration": span.duration,
                "parent_span_id": span.parent_span_id,
                "component": span.component,
                "operation": span.operation,
                "tags": json.dumps(span.tags),
                "logs": json.dumps(span.logs)
            })
        except Exception as e:
            print(f"Failed to store span: {e}")
        
        # Remove from active spans
        del self.active_spans[span_id]
        
        return True
    
    async def add_span_tag(self, span_id: str, key: str, value: str) -> bool:
        """
        Add a tag to a span.
        
        Args:
            span_id: Span ID
            key: Tag key
            value: Tag value
            
        Returns:
            bool: True if successful, False otherwise
        """
        if span_id not in self.active_spans:
            return False
        
        self.active_spans[span_id].tags[key] = value
        return True
    
    async def add_span_log(self, span_id: str, message: str,
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a log to a span.
        
        Args:
            span_id: Span ID
            message: Log message
            metadata: Additional metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        if span_id not in self.active_spans:
            return False
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "metadata": metadata or {}
        }
        
        self.active_spans[span_id].logs.append(log_entry)
        return True
    
    async def get_trace(self, trace_id: str) -> List[TraceSpan]:
        """
        Get all spans for a trace.
        
        Args:
            trace_id: Trace ID
            
        Returns:
            List[TraceSpan]: List of spans in the trace
        """
        await self._ensure_initialized()
        
        results = await self.storage.query("trace_spans", {"trace_id": trace_id})
        
        spans = []
        for result in results:
            span = TraceSpan(
                span_id=result["span_id"],
                trace_id=result["trace_id"],
                tenant_id=result.get("tenant_id"),
                name=result["name"],
                start_time=datetime.fromisoformat(result["start_time"]),
                end_time=datetime.fromisoformat(result["end_time"]) if result.get("end_time") else None,
                duration=result.get("duration"),
                parent_span_id=result.get("parent_span_id"),
                component=result["component"],
                operation=result["operation"],
                tags=json.loads(result.get("tags", "{}")),
                logs=json.loads(result.get("logs", "[]"))
            )
            spans.append(span)
        
        return spans
    
    # PerformanceBenchmarker Implementation
    
    async def run_benchmark(self, name: str, operation: Callable,
                           iterations: int = 100,
                           tenant_id: Optional[str] = None,
                           component: str = "unknown") -> PerformanceBenchmark:
        """
        Run a performance benchmark.
        
        Args:
            name: Benchmark name
            operation: Operation to benchmark
            iterations: Number of iterations
            tenant_id: Tenant ID
            component: Component name
            
        Returns:
            PerformanceBenchmark: Benchmark results
        """
        await self._ensure_initialized()
        
        benchmark_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        durations = []
        success_count = 0
        
        for i in range(iterations):
            try:
                iter_start = time.time()
                
                if asyncio.iscoroutinefunction(operation):
                    await operation()
                else:
                    operation()
                
                iter_duration = time.time() - iter_start
                durations.append(iter_duration)
                success_count += 1
                
            except Exception as e:
                # Log failed iteration but continue
                print(f"Benchmark iteration {i} failed: {e}")
        
        end_time = datetime.utcnow()
        total_duration = (end_time - start_time).total_seconds()
        
        if durations:
            avg_duration = statistics.mean(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            
            # Calculate percentiles
            sorted_durations = sorted(durations)
            p95_index = int(len(sorted_durations) * 0.95)
            p99_index = int(len(sorted_durations) * 0.99)
            
            p95_duration = sorted_durations[p95_index] if p95_index < len(sorted_durations) else max_duration
            p99_duration = sorted_durations[p99_index] if p99_index < len(sorted_durations) else max_duration
        else:
            avg_duration = min_duration = max_duration = p95_duration = p99_duration = 0
        
        success_rate = (success_count / iterations * 100) if iterations > 0 else 0
        
        benchmark = PerformanceBenchmark(
            benchmark_id=benchmark_id,
            tenant_id=tenant_id,
            name=name,
            component=component,
            operation=operation.__name__ if hasattr(operation, '__name__') else "unknown",
            start_time=start_time,
            end_time=end_time,
            duration=total_duration,
            iterations=iterations,
            avg_duration=avg_duration,
            min_duration=min_duration,
            max_duration=max_duration,
            p95_duration=p95_duration,
            p99_duration=p99_duration,
            success_rate=success_rate
        )
        
        # Store benchmark result
        try:
            await self.storage.insert("performance_benchmarks", {
                "benchmark_id": benchmark.benchmark_id,
                "tenant_id": benchmark.tenant_id,
                "name": benchmark.name,
                "component": benchmark.component,
                "operation": benchmark.operation,
                "start_time": benchmark.start_time.isoformat(),
                "end_time": benchmark.end_time.isoformat(),
                "duration": benchmark.duration,
                "iterations": benchmark.iterations,
                "avg_duration": benchmark.avg_duration,
                "min_duration": benchmark.min_duration,
                "max_duration": benchmark.max_duration,
                "p95_duration": benchmark.p95_duration,
                "p99_duration": benchmark.p99_duration,
                "success_rate": benchmark.success_rate,
                "metadata": json.dumps(benchmark.metadata)
            })
        except Exception as e:
            print(f"Failed to store benchmark: {e}")
        
        return benchmark
    
    async def get_benchmarks(self, tenant_id: Optional[str] = None,
                           component: Optional[str] = None,
                           name: Optional[str] = None) -> List[PerformanceBenchmark]:
        """
        Get benchmarks with filters.
        
        Args:
            tenant_id: Filter by tenant ID
            component: Filter by component
            name: Filter by benchmark name
            
        Returns:
            List[PerformanceBenchmark]: List of benchmarks
        """
        await self._ensure_initialized()
        
        filters = {}
        if tenant_id:
            filters["tenant_id"] = tenant_id
        if component:
            filters["component"] = component
        if name:
            filters["name"] = name
        
        results = await self.storage.query("performance_benchmarks", filters)
        
        benchmarks = []
        for result in results:
            benchmark = PerformanceBenchmark(
                benchmark_id=result["benchmark_id"],
                tenant_id=result.get("tenant_id"),
                name=result["name"],
                component=result["component"],
                operation=result["operation"],
                start_time=datetime.fromisoformat(result["start_time"]),
                end_time=datetime.fromisoformat(result["end_time"]) if result.get("end_time") else None,
                duration=result.get("duration"),
                iterations=result["iterations"],
                avg_duration=result.get("avg_duration"),
                min_duration=result.get("min_duration"),
                max_duration=result.get("max_duration"),
                p95_duration=result.get("p95_duration"),
                p99_duration=result.get("p99_duration"),
                success_rate=result.get("success_rate"),
                metadata=json.loads(result.get("metadata", "{}"))
            )
            benchmarks.append(benchmark)
        
        return benchmarks
    
    async def get_benchmark_summary(self, tenant_id: Optional[str] = None,
                                   component: Optional[str] = None) -> Dict[str, Any]:
        """
        Get benchmark summary.
        
        Args:
            tenant_id: Filter by tenant ID
            component: Filter by component
            
        Returns:
            Dict[str, Any]: Benchmark summary
        """
        benchmarks = await self.get_benchmarks(tenant_id=tenant_id, component=component)
        
        if not benchmarks:
            return {
                "total_benchmarks": 0,
                "avg_success_rate": 0,
                "avg_duration": 0,
                "components": []
            }
        
        avg_success_rate = statistics.mean([b.success_rate for b in benchmarks if b.success_rate])
        avg_duration = statistics.mean([b.duration for b in benchmarks if b.duration])
        
        components = list(set([b.component for b in benchmarks]))
        
        return {
            "total_benchmarks": len(benchmarks),
            "avg_success_rate": avg_success_rate,
            "avg_duration": avg_duration,
            "components": components
        }
    
    # MonitoringManager Implementation
    
    async def initialize_monitoring(self, tenant_id: str) -> bool:
        """
        Initialize monitoring for a tenant.
        
        Args:
            tenant_id: Tenant ID to initialize monitoring for
            
        Returns:
            bool: True if successful, False otherwise
        """
        await self._ensure_initialized()
        
        try:
            # Initialize default monitoring settings
            default_settings = {
                "log_retention_days": 30,
                "metrics_retention_days": 90,
                "alert_channels": [],
                "health_check_interval": 60,
                "performance_monitoring": True
            }
            
            await self.storage.upsert("monitoring_settings", {
                "tenant_id": tenant_id,
                "settings": json.dumps(default_settings),
                "updated_at": datetime.utcnow().isoformat()
            })
            
            return True
        except Exception as e:
            print(f"Failed to initialize monitoring for tenant {tenant_id}: {e}")
            return False
    
    async def get_monitoring_dashboard(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get monitoring dashboard data.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Dict[str, Any]: Dashboard data
        """
        await self._ensure_initialized()
        
        # Get recent logs
        recent_logs = await self.get_logs(tenant_id=tenant_id, limit=50)
        
        # Get recent metrics
        recent_metrics = await self.get_metrics(tenant_id=tenant_id)
        
        # Get health status
        health_status = await self.get_health_status(tenant_id)
        
        # Get recent alerts
        recent_alerts = await self.get_alerts(tenant_id=tenant_id, limit=20)
        
        # Get benchmark summary
        benchmark_summary = await self.get_benchmark_summary(tenant_id=tenant_id)
        
        # Calculate log level distribution
        log_levels = {}
        for log in recent_logs:
            level = log.level.value
            log_levels[level] = log_levels.get(level, 0) + 1
        
        # Calculate alert severity distribution
        alert_severities = {}
        for alert in recent_alerts:
            severity = alert.severity.value
            alert_severities[severity] = alert_severities.get(severity, 0) + 1
        
        return {
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "health_status": health_status,
            "log_summary": {
                "total_logs": len(recent_logs),
                "log_levels": log_levels
            },
            "metrics_summary": {
                "total_metrics": len(recent_metrics),
                "metric_types": list(set([m.type.value for m in recent_metrics]))
            },
            "alerts_summary": {
                "total_alerts": len(recent_alerts),
                "unacknowledged_alerts": len([a for a in recent_alerts if not a.acknowledged]),
                "unresolved_alerts": len([a for a in recent_alerts if not a.resolved]),
                "alert_severities": alert_severities
            },
            "performance_summary": benchmark_summary,
            "recent_logs": [log.dict() for log in recent_logs[:10]],
            "recent_alerts": [alert.dict() for alert in recent_alerts[:5]]
        }
    
    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get overall system health.
        
        Args:
            None
            
        Returns:
            Dict[str, Any]: Overall system health
        """
        await self._ensure_initialized()
        
        # Get system-wide health status
        health_status = await self.get_health_status()
        
        # Get recent system alerts
        system_alerts = await self.get_alerts(limit=50)
        
        # Get system metrics summary
        system_metrics = await self.get_metrics()
        
        # Get system benchmark summary
        system_benchmarks = await self.get_benchmark_summary()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": health_status,
            "total_alerts": len(system_alerts),
            "critical_alerts": len([a for a in system_alerts if a.severity == AlertSeverity.CRITICAL]),
            "total_metrics": len(system_metrics),
            "performance_summary": system_benchmarks,
            "active_traces": len(self.active_traces),
            "active_spans": len(self.active_spans)
        }
    
    async def export_monitoring_data(self, tenant_id: str,
                                   format: str = "json") -> str:
        """
        Export monitoring data.
        
        Args:
            tenant_id: Tenant ID
            format: Export format (json, csv)
            
        Returns:
            str: Exported monitoring data
        """
        await self._ensure_initialized()
        
        # Collect all monitoring data for the tenant
        logs = await self.get_logs(tenant_id=tenant_id, limit=1000)
        metrics = await self.get_metrics(tenant_id=tenant_id)
        health_checks = await self.storage.query("health_checks", {"tenant_id": tenant_id})
        alerts = await self.get_alerts(tenant_id=tenant_id)
        benchmarks = await self.get_benchmarks(tenant_id=tenant_id)
        
        monitoring_data = {
            "tenant_id": tenant_id,
            "export_timestamp": datetime.utcnow().isoformat(),
            "logs": [log.dict() for log in logs],
            "metrics": [metric.dict() for metric in metrics],
            "health_checks": health_checks,
            "alerts": [alert.dict() for alert in alerts],
            "benchmarks": [benchmark.dict() for benchmark in benchmarks]
        }
        
        if format.lower() == "json":
            # Convert datetime objects to ISO format strings for JSON serialization
            def convert_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: convert_datetime(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_datetime(item) for item in obj]
                else:
                    return obj
            
            monitoring_data = convert_datetime(monitoring_data)
            return json.dumps(monitoring_data, indent=2)
        
        elif format.lower() == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write logs
            writer.writerow(["LOGS"])
            writer.writerow(["log_id", "level", "message", "timestamp", "component"])
            for log in logs:
                writer.writerow([log.log_id, log.level.value, log.message, 
                               log.timestamp.isoformat(), log.component])
            
            writer.writerow([])
            writer.writerow(["ALERTS"])
            writer.writerow(["alert_id", "severity", "title", "timestamp", "acknowledged", "resolved"])
            for alert in alerts:
                writer.writerow([alert.alert_id, alert.severity.value, alert.title,
                               alert.timestamp.isoformat(), alert.acknowledged, alert.resolved])
            
            return output.getvalue()
        
        else:
            return ""
