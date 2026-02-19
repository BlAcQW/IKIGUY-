"""
Monitoring service wrapper for Developer Platform using shared libraries.

This service integrates the shared monitoring and observability engine to provide
logging, metrics, and health monitoring for the Developer Platform.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Use centralized import configuration
try:
    from ..import_config import get_monitoring_engine, get_storage_backend
    MonitoringEngine = get_monitoring_engine()
    MemoryStorageBackend = get_storage_backend()
    from apps.shared.monitoring import LogRecord, Metric, HealthCheck, Alert
    from apps.shared.storage import StorageConfig
    SHARED_LIBRARIES_AVAILABLE = True
except ImportError as e:
    logging.error(f"SHARED LIBRARY IMPORT FAILURE - monitoring: {e}")
    # Define fallback types for when shared libraries are not available
    from typing import TypedDict, Optional as OptionalType
    
    class LogRecord(TypedDict):
        timestamp: str
        level: str
        message: str
        tenant_id: str
        data: Dict[str, Any]
    
    class Metric(TypedDict):
        name: str
        value: float
        timestamp: str
        tenant_id: str
        tags: Dict[str, str]
    
    class HealthCheck(TypedDict):
        service: str
        status: str
        timestamp: str
        details: Dict[str, Any]
    
    class Alert(TypedDict):
        alert_id: str
        severity: str
        message: str
        timestamp: str
        tenant_id: str
    
    class StorageConfig(TypedDict):
        backend_type: str
        connection_string: str
    
    class MemoryStorageBackend:
        def __init__(self, config):
            self.config = config
    
    class MonitoringEngine:
        def __init__(self, config):
            self.config = config
    
    SHARED_LIBRARIES_AVAILABLE = False

logger = logging.getLogger(__name__)


class SharedMonitoringService:
    """Service for monitoring and observability using shared libraries."""

    def __init__(self, storage_backend=None):
        """
        Initialize the monitoring service.

        Args:
            storage_backend: Storage backend for monitoring data. Defaults to in-memory.
        """
        if storage_backend is None:
            config = StorageConfig(backend_type="memory", connection_string="memory://")
            storage_backend = MemoryStorageBackend(config)
            
        self.storage = storage_backend
        # Note: MonitoringEngine not available, using mock implementation

    async def _ensure_initialized(self):
        """Ensure the monitoring service is initialized."""
        # Note: _ensure_initialized will be called when needed
        pass

    async def log_event(
        self,
        event_type: str,
        tenant_id: str,
        data: Optional[Dict[str, Any]] = None,
        level: str = "info"
    ) -> bool:
        """
        Log an event using the shared monitoring library.

        Args:
            event_type: Type of event
            tenant_id: Tenant identifier
            data: Event data
            level: Log level (debug, info, warning, error, critical)

        Returns:
            bool: True if event was logged successfully
        """
        await self._ensure_initialized()
        
        try:
            # Mock implementation - just log the event
            logger.info(f"Logged event {event_type} for tenant {tenant_id} with level {level}")
            return True
        except Exception as e:
            logger.error(f"Failed to log event {event_type} for tenant {tenant_id}: {e}")
            return False

    async def record_metric(
        self,
        metric_name: str,
        value: float,
        tenant_id: str,
        tags: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Record a metric using the shared monitoring library.

        Args:
            metric_name: Name of the metric
            value: Metric value
            tenant_id: Tenant identifier
            tags: Additional tags

        Returns:
            bool: True if metric was recorded successfully
        """
        await self._ensure_initialized()
        
        try:
            metric = Metric(
                name=metric_name,
                value=value,
                timestamp=datetime.now(),
                tenant_id=tenant_id,
                tags=tags or {},
                source="developer_platform"
            )
            
            success = await self.monitoring_engine.record_metric(metric)
            if success:
                logger.debug(f"Recorded metric {metric_name} for tenant {tenant_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to record metric {metric_name} for tenant {tenant_id}: {e}")
            return False

    async def get_health_status(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get health status for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dict[str, Any]: Health status information
        """
        await self._ensure_initialized()
        
        try:
            health_status = await self.monitoring_engine.get_health_status(tenant_id)
            return {
                "status": "healthy" if health_status.is_healthy else "unhealthy",
                "checks": health_status.checks,
                "last_check": health_status.last_check,
                "errors": health_status.errors,
                "warnings": health_status.warnings
            }
        except Exception as e:
            logger.error(f"Failed to get health status for tenant {tenant_id}: {e}")
            return {
                "status": "unhealthy",
                "checks": {},
                "errors": [str(e)],
                "warnings": []
            }

    async def get_metrics(
        self,
        tenant_id: str,
        metric_names: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Metric]:
        """
        Get metrics for a tenant.

        Args:
            tenant_id: Tenant identifier
            metric_names: List of metric names to retrieve
            start_time: Start time for metrics
            end_time: End time for metrics

        Returns:
            List[Metric]: List of metrics
        """
        await self._ensure_initialized()
        
        try:
            metrics = await self.monitoring_engine.get_metrics(
                tenant_id=tenant_id,
                metric_names=metric_names,
                start_time=start_time,
                end_time=end_time
            )
            return metrics
        except Exception as e:
            logger.error(f"Failed to get metrics for tenant {tenant_id}: {e}")
            return []

    async def get_logs(
        self,
        tenant_id: str,
        event_types: Optional[List[str]] = None,
        levels: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[LogRecord]:
        """
        Get logs for a tenant.

        Args:
            tenant_id: Tenant identifier
            event_types: List of event types to filter by
            levels: List of log levels to filter by
            start_time: Start time for logs
            end_time: End time for logs
            limit: Maximum number of logs to return

        Returns:
            List[LogRecord]: List of log entries
        """
        await self._ensure_initialized()
        
        try:
            # Mock implementation - return empty list
            return []
        except Exception as e:
            logger.error(f"Failed to get logs for tenant {tenant_id}: {e}")
            return []

    async def create_alert(
        self,
        alert_type: str,
        tenant_id: str,
        message: str,
        severity: str = "medium",
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create an alert using the shared monitoring library.

        Args:
            alert_type: Type of alert
            tenant_id: Tenant identifier
            message: Alert message
            severity: Alert severity (low, medium, high, critical)
            data: Additional alert data

        Returns:
            bool: True if alert was created successfully
        """
        await self._ensure_initialized()
        
        try:
            alert = Alert(
                alert_type=alert_type,
                tenant_id=tenant_id,
                message=message,
                severity=severity,
                timestamp=datetime.now(),
                data=data or {},
                source="developer_platform"
            )
            
            success = await self.monitoring_engine.create_alert(alert)
            if success:
                logger.info(f"Created alert {alert_type} for tenant {tenant_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to create alert {alert_type} for tenant {tenant_id}: {e}")
            return False

    async def get_alerts(
        self,
        tenant_id: str,
        alert_types: Optional[List[str]] = None,
        severity_levels: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Alert]:
        """
        Get alerts for a tenant.

        Args:
            tenant_id: Tenant identifier
            alert_types: List of alert types to filter by
            severity_levels: List of severity levels to filter by
            start_time: Start time for alerts
            end_time: End time for alerts
            limit: Maximum number of alerts to return

        Returns:
            List[Alert]: List of alerts
        """
        await self._ensure_initialized()
        
        try:
            alerts = await self.monitoring_engine.get_alerts(
                tenant_id=tenant_id,
                alert_types=alert_types,
                severity_levels=severity_levels,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            return alerts
        except Exception as e:
            logger.error(f"Failed to get alerts for tenant {tenant_id}: {e}")
            return []

    async def get_performance_metrics(
        self,
        tenant_id: str,
        metric_type: str = "api",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics for a tenant.

        Args:
            tenant_id: Tenant identifier
            metric_type: Type of performance metrics
            start_time: Start time for metrics
            end_time: End time for metrics

        Returns:
            Dict[str, Any]: Performance metrics
        """
        await self._ensure_initialized()
        
        try:
            metrics = await self.monitoring_engine.get_performance_metrics(
                tenant_id=tenant_id,
                metric_type=metric_type,
                start_time=start_time,
                end_time=end_time
            )
            return metrics
        except Exception as e:
            logger.error(f"Failed to get performance metrics for tenant {tenant_id}: {e}")
            return {}

    async def run_health_check(self, tenant_id: str) -> HealthCheck:
        """
        Run a health check for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            HealthCheck: Health check result
        """
        await self._ensure_initialized()
        
        try:
            health_check = await self.monitoring_engine.run_health_check(tenant_id)
            return health_check
        except Exception as e:
            logger.error(f"Failed to run health check for tenant {tenant_id}: {e}")
            return HealthCheck(
                tenant_id=tenant_id,
                is_healthy=False,
                checks={},
                errors=[str(e)],
                timestamp=datetime.now()
            )

    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status.

        Returns:
            Dict[str, Any]: System status information
        """
        await self._ensure_initialized()
        
        try:
            status = await self.monitoring_engine.get_system_status()
            return {
                "status": "healthy" if status.is_healthy else "unhealthy",
                "components": status.components,
                "last_check": status.last_check,
                "errors": status.errors,
                "warnings": status.warnings
            }
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                "status": "unhealthy",
                "components": {},
                "errors": [str(e)],
                "warnings": []
            }
