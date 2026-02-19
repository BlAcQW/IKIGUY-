"""
Prometheus Integration Module

This module provides integration with Prometheus for metrics collection,
monitoring, and alerting capabilities.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    import requests
    from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("Prometheus APIs not available. Install requests and prometheus_client")

logger = logging.getLogger(__name__)


class PrometheusMetricType(Enum):
    """Prometheus metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class PrometheusAlertSeverity(Enum):
    """Prometheus alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PrometheusConfig:
    """Configuration for Prometheus integration."""
    
    prometheus_url: str
    """Prometheus server URL."""
    
    api_key: Optional[str] = None
    """API key for authentication."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""
    
    scrape_interval: int = 15
    """Scrape interval in seconds."""
    
    retention_days: int = 15
    """Data retention period in days."""


@dataclass
class PrometheusMetric:
    """Prometheus metric data structure."""
    
    name: str
    """Metric name."""
    
    value: float
    """Metric value."""
    
    metric_type: PrometheusMetricType
    """Metric type."""
    
    labels: Dict[str, str] = field(default_factory=dict)
    """Metric labels."""
    
    timestamp: Optional[datetime] = None
    """Metric timestamp."""
    
    description: Optional[str] = None
    """Metric description."""
    
    unit: Optional[str] = None
    """Metric unit."""


@dataclass
class PrometheusQuery:
    """Prometheus query data structure."""
    
    query: str
    """PromQL query string."""
    
    start_time: Optional[datetime] = None
    """Query start time."""
    
    end_time: Optional[datetime] = None
    """Query end time."""
    
    step: Optional[str] = None
    """Query step interval."""
    
    timeout: Optional[int] = None
    """Query timeout."""


@dataclass
class PrometheusAlert:
    """Prometheus alert data structure."""
    
    name: str
    """Alert name."""
    
    severity: PrometheusAlertSeverity
    """Alert severity."""
    
    summary: str
    """Alert summary."""
    
    description: Optional[str] = None
    """Alert description."""
    
    labels: Dict[str, str] = field(default_factory=dict)
    """Alert labels."""
    
    annotations: Dict[str, str] = field(default_factory=dict)
    """Alert annotations."""
    
    active_at: Optional[datetime] = None
    """Alert activation time."""
    
    resolved_at: Optional[datetime] = None
    """Alert resolution time."""


@dataclass
class PrometheusTarget:
    """Prometheus target data structure."""
    
    url: str
    """Target URL."""
    
    labels: Dict[str, str] = field(default_factory=dict)
    """Target labels."""
    
    health: str = "up"
    """Target health status."""
    
    last_scrape: Optional[datetime] = None
    """Last scrape time."""
    
    last_error: Optional[str] = None
    """Last error message."""


class PrometheusIntegration:
    """Prometheus integration for metrics collection and monitoring."""
    
    def __init__(self, config: PrometheusConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        
        if config.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {config.api_key}"
            })
        
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        # Initialize Prometheus client registry
        self.registry = CollectorRegistry()
        self._metrics = {}
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the Prometheus API."""
        try:
            url = f"{self.config.prometheus_url}/api/v1/{endpoint}"
            
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to make {method} request to {endpoint}: {e}")
            raise
    
    def create_metric(self, name: str, metric_type: PrometheusMetricType, description: Optional[str] = None) -> Any:
        """
        Create a new Prometheus metric.
        
        Args:
            name: Metric name
            metric_type: Metric type
            description: Metric description
            
        Returns:
            Prometheus metric object
        """
        try:
            if name in self._metrics:
                return self._metrics[name]
            
            if metric_type == PrometheusMetricType.COUNTER:
                metric = Counter(name, description or name, registry=self.registry)
            elif metric_type == PrometheusMetricType.GAUGE:
                metric = Gauge(name, description or name, registry=self.registry)
            elif metric_type == PrometheusMetricType.HISTOGRAM:
                metric = Histogram(name, description or name, registry=self.registry)
            elif metric_type == PrometheusMetricType.SUMMARY:
                metric = Summary(name, description or name, registry=self.registry)
            else:
                raise ValueError(f"Unsupported metric type: {metric_type}")
            
            self._metrics[name] = metric
            return metric
            
        except Exception as e:
            self.logger.error(f"Failed to create metric {name}: {e}")
            raise
    
    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: PrometheusMetricType = PrometheusMetricType.COUNTER,
        labels: Optional[Dict[str, str]] = None,
        description: Optional[str] = None
    ) -> PrometheusMetric:
        """
        Record a metric value.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Metric type
            labels: Metric labels
            description: Metric description
            
        Returns:
            Metric data
        """
        try:
            metric = self.create_metric(name, metric_type, description)
            labels = labels or {}
            
            if metric_type == PrometheusMetricType.COUNTER:
                metric.labels(**labels).inc(value)
            elif metric_type == PrometheusMetricType.GAUGE:
                metric.labels(**labels).set(value)
            elif metric_type == PrometheusMetricType.HISTOGRAM:
                metric.labels(**labels).observe(value)
            elif metric_type == PrometheusMetricType.SUMMARY:
                metric.labels(**labels).observe(value)
            
            return PrometheusMetric(
                name=name,
                value=value,
                metric_type=metric_type,
                labels=labels,
                timestamp=datetime.now(),
                description=description
            )
            
        except Exception as e:
            self.logger.error(f"Failed to record metric {name}: {e}")
            raise
    
    async def query_metrics(self, query: PrometheusQuery) -> List[PrometheusMetric]:
        """
        Query metrics using PromQL.
        
        Args:
            query: Query configuration
            
        Returns:
            List of metric results
        """
        try:
            params = {"query": query.query}
            
            if query.start_time:
                params["start"] = query.start_time.isoformat()
            if query.end_time:
                params["end"] = query.end_time.isoformat()
            if query.step:
                params["step"] = query.step
            if query.timeout:
                params["timeout"] = query.timeout
            
            result = self._make_request("GET", "query", params)
            
            metrics = []
            if "data" in result and "result" in result["data"]:
                for item in result["data"]["result"]:
                    metric = PrometheusMetric(
                        name=item["metric"].get("__name__", ""),
                        value=float(item["value"][1]) if item["value"] else 0.0,
                        metric_type=PrometheusMetricType.GAUGE,  # Default type
                        labels={k: v for k, v in item["metric"].items() if k != "__name__"},
                        timestamp=datetime.fromtimestamp(item["value"][0]) if item["value"] else None
                    )
                    metrics.append(metric)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to query metrics: {e}")
            raise
    
    async def get_metric_series(self, match: List[str], start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get metric series data.
        
        Args:
            match: List of metric matchers
            start_time: Start time
            end_time: End time
            
        Returns:
            List of metric series
        """
        try:
            params = {"match[]": match}
            
            if start_time:
                params["start"] = start_time.isoformat()
            if end_time:
                params["end"] = end_time.isoformat()
            
            result = self._make_request("GET", "series", params)
            
            return result.get("data", [])
            
        except Exception as e:
            self.logger.error(f"Failed to get metric series: {e}")
            raise
    
    async def get_targets(self) -> List[PrometheusTarget]:
        """
        Get Prometheus targets.
        
        Returns:
            List of targets
        """
        try:
            result = self._make_request("GET", "targets")
            
            targets = []
            if "data" in result and "activeTargets" in result["data"]:
                for item in result["data"]["activeTargets"]:
                    target = PrometheusTarget(
                        url=item.get("scrapeUrl", ""),
                        labels=item.get("labels", {}),
                        health=item.get("health", "up"),
                        last_scrape=datetime.fromtimestamp(item["lastScrape"]) if item.get("lastScrape") else None,
                        last_error=item.get("lastError")
                    )
                    targets.append(target)
            
            return targets
            
        except Exception as e:
            self.logger.error(f"Failed to get targets: {e}")
            raise
    
    async def get_alerts(self) -> List[PrometheusAlert]:
        """
        Get active alerts.
        
        Returns:
            List of alerts
        """
        try:
            result = self._make_request("GET", "alerts")
            
            alerts = []
            if "data" in result and "alerts" in result["data"]:
                for item in result["data"]["alerts"]:
                    alert = PrometheusAlert(
                        name=item["labels"].get("alertname", ""),
                        severity=PrometheusAlertSeverity(item["labels"].get("severity", "info")),
                        summary=item["annotations"].get("summary", ""),
                        description=item["annotations"].get("description"),
                        labels=item.get("labels", {}),
                        annotations=item.get("annotations", {}),
                        active_at=datetime.fromtimestamp(item["activeAt"]) if item.get("activeAt") else None
                    )
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to get alerts: {e}")
            raise
    
    async def get_rules(self) -> List[Dict[str, Any]]:
        """
        Get recording and alerting rules.
        
        Returns:
            List of rules
        """
        try:
            result = self._make_request("GET", "rules")
            
            return result.get("data", {}).get("groups", [])
            
        except Exception as e:
            self.logger.error(f"Failed to get rules: {e}")
            raise
    
    async def get_config(self) -> Dict[str, Any]:
        """
        Get Prometheus configuration.
        
        Returns:
            Configuration data
        """
        try:
            result = self._make_request("GET", "status/config")
            
            return result.get("data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to get config: {e}")
            raise
    
    async def get_flags(self) -> Dict[str, Any]:
        """
        Get Prometheus command line flags.
        
        Returns:
            Flags data
        """
        try:
            result = self._make_request("GET", "status/flags")
            
            return result.get("data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to get flags: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Prometheus integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by getting targets
            targets = await self.get_targets()
            
            return {
                "status": "healthy",
                "prometheus_url": self.config.prometheus_url,
                "targets_count": len(targets),
                "metrics_count": len(self._metrics),
                "api_connectivity": "successful",
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }

