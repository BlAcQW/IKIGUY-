"""
Monitoring and Observability Interfaces

This module defines the abstract interfaces and data models for the monitoring
and observability system, including logging, metrics, health checks, and alerts.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """Log levels for monitoring"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class HealthStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LogRecord(BaseModel):
    """Log record model"""
    log_id: str = Field(..., description="Unique log identifier")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    component: str = Field(..., description="Component name")
    level: LogLevel = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Log timestamp")
    trace_id: Optional[str] = Field(None, description="Trace identifier")
    span_id: Optional[str] = Field(None, description="Span identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")


class Metric(BaseModel):
    """Metric model"""
    metric_id: str = Field(..., description="Unique metric identifier")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    name: str = Field(..., description="Metric name")
    type: MetricType = Field(..., description="Metric type")
    value: Union[int, float] = Field(..., description="Metric value")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metric timestamp")
    labels: Dict[str, str] = Field(default_factory=dict, description="Metric labels")
    description: Optional[str] = Field(None, description="Metric description")
    unit: Optional[str] = Field(None, description="Metric unit")


class HealthCheck(BaseModel):
    """Health check model"""
    check_id: str = Field(..., description="Unique health check identifier")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    component: str = Field(..., description="Component name")
    name: str = Field(..., description="Health check name")
    status: HealthStatus = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    response_time: Optional[float] = Field(None, description="Response time in seconds")
    details: Dict[str, Any] = Field(default_factory=dict, description="Check details")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class Alert(BaseModel):
    """Alert model"""
    alert_id: str = Field(..., description="Unique alert identifier")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    severity: AlertSeverity = Field(..., description="Alert severity")
    category: str = Field(..., description="Alert category")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Alert timestamp")
    acknowledged: bool = Field(default=False, description="Whether alert is acknowledged")
    acknowledged_by: Optional[str] = Field(None, description="User who acknowledged")
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledgment timestamp")
    resolved: bool = Field(default=False, description="Whether alert is resolved")
    resolved_by: Optional[str] = Field(None, description="User who resolved")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TraceSpan(BaseModel):
    """Trace span model"""
    span_id: str = Field(..., description="Unique span identifier")
    trace_id: str = Field(..., description="Trace identifier")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    name: str = Field(..., description="Span name")
    start_time: datetime = Field(..., description="Span start time")
    end_time: Optional[datetime] = Field(None, description="Span end time")
    duration: Optional[float] = Field(None, description="Span duration in seconds")
    parent_span_id: Optional[str] = Field(None, description="Parent span identifier")
    component: str = Field(..., description="Component name")
    operation: str = Field(..., description="Operation name")
    tags: Dict[str, str] = Field(default_factory=dict, description="Span tags")
    logs: List[Dict[str, Any]] = Field(default_factory=list, description="Span logs")


class PerformanceBenchmark(BaseModel):
    """Performance benchmark model"""
    benchmark_id: str = Field(..., description="Unique benchmark identifier")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    name: str = Field(..., description="Benchmark name")
    component: str = Field(..., description="Component name")
    operation: str = Field(..., description="Operation name")
    start_time: datetime = Field(..., description="Benchmark start time")
    end_time: Optional[datetime] = Field(None, description="Benchmark end time")
    duration: Optional[float] = Field(None, description="Benchmark duration in seconds")
    iterations: int = Field(..., description="Number of iterations")
    avg_duration: Optional[float] = Field(None, description="Average duration")
    min_duration: Optional[float] = Field(None, description="Minimum duration")
    max_duration: Optional[float] = Field(None, description="Maximum duration")
    p95_duration: Optional[float] = Field(None, description="95th percentile duration")
    p99_duration: Optional[float] = Field(None, description="99th percentile duration")
    success_rate: Optional[float] = Field(None, description="Success rate percentage")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# Abstract Base Classes

class Logger(ABC):
    """Abstract logger interface"""
    
    @abstractmethod
    async def log(self, record: LogRecord) -> bool:
        """Log a record"""
        pass
    
    @abstractmethod
    async def get_logs(self, tenant_id: Optional[str] = None, 
                      component: Optional[str] = None,
                      level: Optional[LogLevel] = None,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None,
                      limit: int = 100) -> List[LogRecord]:
        """Get logs with filters"""
        pass
    
    @abstractmethod
    async def export_logs(self, tenant_id: Optional[str] = None,
                         format: str = "json") -> str:
        """Export logs in specified format"""
        pass


class MetricsCollector(ABC):
    """Abstract metrics collector interface"""
    
    @abstractmethod
    async def record_metric(self, metric: Metric) -> bool:
        """Record a metric"""
        pass
    
    @abstractmethod
    async def get_metrics(self, tenant_id: Optional[str] = None,
                         name: Optional[str] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> List[Metric]:
        """Get metrics with filters"""
        pass
    
    @abstractmethod
    async def get_metric_summary(self, tenant_id: Optional[str] = None,
                                name: Optional[str] = None,
                                period: str = "1h") -> Dict[str, Any]:
        """Get metric summary for a period"""
        pass


class HealthChecker(ABC):
    """Abstract health checker interface"""
    
    @abstractmethod
    async def register_check(self, component: str, name: str, 
                           check_func: callable) -> bool:
        """Register a health check"""
        pass
    
    @abstractmethod
    async def run_health_checks(self, tenant_id: Optional[str] = None) -> List[HealthCheck]:
        """Run all health checks"""
        pass
    
    @abstractmethod
    async def get_health_status(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get overall health status"""
        pass


class AlertManager(ABC):
    """Abstract alert manager interface"""
    
    @abstractmethod
    async def create_alert(self, alert: Alert) -> bool:
        """Create an alert"""
        pass
    
    @abstractmethod
    async def get_alerts(self, tenant_id: Optional[str] = None,
                        severity: Optional[AlertSeverity] = None,
                        acknowledged: Optional[bool] = None,
                        resolved: Optional[bool] = None) -> List[Alert]:
        """Get alerts with filters"""
        pass
    
    @abstractmethod
    async def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acknowledge an alert"""
        pass
    
    @abstractmethod
    async def resolve_alert(self, alert_id: str, user_id: str) -> bool:
        """Resolve an alert"""
        pass


class Tracer(ABC):
    """Abstract tracer interface"""
    
    @abstractmethod
    async def start_span(self, name: str, trace_id: Optional[str] = None,
                        parent_span_id: Optional[str] = None,
                        tenant_id: Optional[str] = None,
                        component: str = "unknown",
                        operation: str = "unknown") -> str:
        """Start a new span"""
        pass
    
    @abstractmethod
    async def end_span(self, span_id: str) -> bool:
        """End a span"""
        pass
    
    @abstractmethod
    async def add_span_tag(self, span_id: str, key: str, value: str) -> bool:
        """Add a tag to a span"""
        pass
    
    @abstractmethod
    async def add_span_log(self, span_id: str, message: str, 
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add a log to a span"""
        pass
    
    @abstractmethod
    async def get_trace(self, trace_id: str) -> List[TraceSpan]:
        """Get all spans for a trace"""
        pass


class PerformanceBenchmarker(ABC):
    """Abstract performance benchmarker interface"""
    
    @abstractmethod
    async def run_benchmark(self, name: str, operation: callable,
                           iterations: int = 100,
                           tenant_id: Optional[str] = None,
                           component: str = "unknown") -> PerformanceBenchmark:
        """Run a performance benchmark"""
        pass
    
    @abstractmethod
    async def get_benchmarks(self, tenant_id: Optional[str] = None,
                           component: Optional[str] = None,
                           name: Optional[str] = None) -> List[PerformanceBenchmark]:
        """Get benchmarks with filters"""
        pass
    
    @abstractmethod
    async def get_benchmark_summary(self, tenant_id: Optional[str] = None,
                                   component: Optional[str] = None) -> Dict[str, Any]:
        """Get benchmark summary"""
        pass


class MonitoringManager(ABC):
    """Abstract monitoring manager interface"""
    
    @abstractmethod
    async def initialize_monitoring(self, tenant_id: str) -> bool:
        """Initialize monitoring for a tenant"""
        pass
    
    @abstractmethod
    async def get_monitoring_dashboard(self, tenant_id: str) -> Dict[str, Any]:
        """Get monitoring dashboard data"""
        pass
    
    @abstractmethod
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        pass
    
    @abstractmethod
    async def export_monitoring_data(self, tenant_id: str,
                                   format: str = "json") -> str:
        """Export monitoring data"""
        pass
