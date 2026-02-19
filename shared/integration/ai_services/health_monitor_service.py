"""
Health Monitor Service

Provides scheduled health monitoring for AI service providers.
Tracks provider availability, response times, and alerts on failures.

Usage:
    from apps.shared.integration.ai_services import HealthMonitorService, ProviderRegistry

    registry = ProviderRegistry()
    monitor = HealthMonitorService(registry)

    # Start monitoring
    await monitor.start()

    # Get health report
    report = await monitor.get_health_report()
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
import aiohttp

from .ai_provider_service import AIProvider, ProviderStatus
from .provider_registry import ProviderRegistry

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    provider_id: str
    timestamp: datetime
    status: ProviderStatus
    response_time_ms: Optional[float]
    healthy: bool
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderHealthMetrics:
    """Aggregated health metrics for a provider."""
    provider_id: str
    total_checks: int = 0
    successful_checks: int = 0
    failed_checks: int = 0
    average_response_time_ms: Optional[float] = None
    last_check: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    uptime_percentage: float = 0.0
    consecutive_failures: int = 0


class HealthMonitorService:
    """
    Service for monitoring health of AI providers.

    Features:
    - Scheduled health checks
    - Aggregated metrics
    - Alert callbacks on failures
    - Historical tracking
    """

    def __init__(
        self,
        registry: ProviderRegistry,
        check_interval: int = 60,  # seconds
        timeout: int = 5,  # seconds
        max_history: int = 1000,  # number of results to keep
    ):
        """
        Initialize health monitor service.

        Args:
            registry: Provider registry to monitor
            check_interval: Seconds between health checks
            timeout: Timeout for health check requests
            max_history: Maximum health check results to keep
        """
        self.registry = registry
        self.check_interval = check_interval
        self.timeout = timeout
        self.max_history = max_history

        self._monitor_task: Optional[asyncio.Task] = None
        self._health_history: List[HealthCheckResult] = []
        self._metrics: Dict[str, ProviderHealthMetrics] = {}
        self._alert_callbacks: List[Callable] = []
        self._running = False

        logger.info(
            f"Initialized health monitor (interval: {check_interval}s, "
            f"timeout: {timeout}s)"
        )

    def register_alert_callback(
        self,
        callback: Callable[[AIProvider, HealthCheckResult], None],
    ) -> None:
        """
        Register a callback for health alerts.

        Callback is called when a provider fails health check or recovers.

        Args:
            callback: Async function taking (provider, result)
        """
        self._alert_callbacks.append(callback)
        logger.info(f"Registered alert callback: {callback.__name__}")

    async def check_provider_health(
        self,
        provider: AIProvider,
    ) -> HealthCheckResult:
        """
        Check health of a single provider.

        Args:
            provider: Provider to check

        Returns:
            HealthCheckResult with check details
        """
        start_time = datetime.now()

        try:
            async with aiohttp.ClientSession() as session:
                # Handle different providers differently
                headers = {}
                health_url = f"{provider.endpoint}/health"

                # Ollama uses /api/tags endpoint
                if 'ollama' in provider.endpoint.lower():
                    health_url = f"{provider.endpoint}/api/tags"

                if provider.requires_api_key:
                    import os
                    api_key_env = provider.api_key_env or 'OPENAI_API_KEY'
                    api_key = os.getenv(api_key_env)
                    if api_key:
                        headers['Authorization'] = f'Bearer {api_key}'
                        # OpenAI uses /v1/models endpoint for health check
                        if 'openai' in provider.id.lower() or 'api.openai.com' in provider.endpoint:
                            health_url = f"{provider.endpoint}/v1/models"
                        # Groq uses /v1/models endpoint for health check
                        elif 'groq' in provider.id.lower() or 'api.groq.com' in provider.endpoint:
                            health_url = f"{provider.endpoint}/v1/models"

                async with session.get(
                    health_url,
                    headers=headers if headers else None,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    elapsed = (datetime.now() - start_time).total_seconds() * 1000

                    if response.status == 200:
                        try:
                            data = await response.json()
                        except Exception:
                            data = {}

                        return HealthCheckResult(
                            provider_id=provider.id,
                            timestamp=datetime.now(),
                            status=ProviderStatus.ONLINE,
                            response_time_ms=elapsed,
                            healthy=data.get("status") == "healthy" or True,
                            details=data,
                        )
                    else:
                        return HealthCheckResult(
                            provider_id=provider.id,
                            timestamp=datetime.now(),
                            status=ProviderStatus.DEGRADED,
                            response_time_ms=elapsed,
                            healthy=False,
                            error=f"HTTP {response.status}",
                        )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                provider_id=provider.id,
                timestamp=datetime.now(),
                status=ProviderStatus.OFFLINE,
                response_time_ms=None,
                healthy=False,
                error="Timeout",
            )
        except Exception as e:
            logger.error(f"Health check failed for {provider.id}: {e}")
            return HealthCheckResult(
                provider_id=provider.id,
                timestamp=datetime.now(),
                status=ProviderStatus.OFFLINE,
                response_time_ms=None,
                healthy=False,
                error=str(e),
            )

    async def check_all_providers(self) -> List[HealthCheckResult]:
        """
        Check health of all registered providers.

        Returns:
            List of health check results
        """
        providers = self.registry.get_all_providers()

        if not providers:
            logger.warning("No providers to check")
            return []

        logger.info(f"Checking health of {len(providers)} providers")

        # Run all health checks concurrently
        tasks = [
            self.check_provider_health(provider)
            for provider in providers.values()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Health check exception: {result}")
            else:
                valid_results.append(result)
                self._update_metrics(result)
                self._update_provider_status(result)
                await self._trigger_alerts(result)

        # Store in history
        self._health_history.extend(valid_results)

        # Trim history if needed
        if len(self._health_history) > self.max_history:
            self._health_history = self._health_history[-self.max_history:]

        return valid_results

    def _update_metrics(self, result: HealthCheckResult) -> None:
        """Update aggregated metrics for a provider."""
        if result.provider_id not in self._metrics:
            self._metrics[result.provider_id] = ProviderHealthMetrics(
                provider_id=result.provider_id
            )

        metrics = self._metrics[result.provider_id]
        metrics.total_checks += 1
        metrics.last_check = result.timestamp

        if result.healthy:
            metrics.successful_checks += 1
            metrics.last_success = result.timestamp
            metrics.consecutive_failures = 0
        else:
            metrics.failed_checks += 1
            metrics.last_failure = result.timestamp
            metrics.consecutive_failures += 1

        # Calculate uptime percentage
        if metrics.total_checks > 0:
            metrics.uptime_percentage = (
                metrics.successful_checks / metrics.total_checks
            ) * 100

        # Calculate average response time (only from successful checks)
        if result.response_time_ms is not None:
            if metrics.average_response_time_ms is None:
                metrics.average_response_time_ms = result.response_time_ms
            else:
                # Moving average
                metrics.average_response_time_ms = (
                    metrics.average_response_time_ms * 0.8 +
                    result.response_time_ms * 0.2
                )

    def _update_provider_status(self, result: HealthCheckResult) -> None:
        """Update provider status in registry based on health check."""
        provider = self.registry.get_provider(result.provider_id)
        if provider:
            old_status = provider.status
            provider.status = result.status
            provider.responseTime = result.response_time_ms
            provider.lastChecked = result.timestamp

            if old_status != result.status:
                old_val = old_status.value if hasattr(old_status, 'value') else old_status
                new_val = result.status.value if hasattr(result.status, 'value') else result.status
                logger.info(
                    f"Provider {result.provider_id} status changed: "
                    f"{old_val} → {new_val}"
                )

    async def _trigger_alerts(self, result: HealthCheckResult) -> None:
        """Trigger alert callbacks if needed."""
        metrics = self._metrics.get(result.provider_id)
        if not metrics:
            return

        provider = self.registry.get_provider(result.provider_id)
        if not provider:
            return

        # Alert on first failure or recovery
        should_alert = False

        if not result.healthy and metrics.consecutive_failures == 1:
            # First failure
            should_alert = True
            logger.warning(f"Provider {result.provider_id} is now unhealthy")

        elif result.healthy and metrics.consecutive_failures == 0:
            # Just recovered (check if previous was failure)
            if metrics.failed_checks > 0:
                should_alert = True
                logger.info(f"Provider {result.provider_id} has recovered")

        if should_alert:
            for callback in self._alert_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(provider, result)
                    else:
                        callback(provider, result)
                except Exception as e:
                    logger.error(f"Alert callback error: {e}")

    async def start(self) -> None:
        """Start automated health monitoring."""
        if self._running:
            logger.warning("Health monitor already running")
            return

        async def _monitor_loop():
            """Background monitoring loop."""
            while self._running:
                try:
                    await self.check_all_providers()
                    await asyncio.sleep(self.check_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Monitor loop error: {e}")
                    await asyncio.sleep(self.check_interval)

        self._running = True
        self._monitor_task = asyncio.create_task(_monitor_loop())
        logger.info(f"Started health monitoring (interval: {self.check_interval}s)")

    async def stop(self) -> None:
        """Stop automated health monitoring."""
        if not self._running:
            return

        self._running = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        logger.info("Stopped health monitoring")

    def get_metrics(
        self,
        provider_id: Optional[str] = None,
    ) -> Dict[str, ProviderHealthMetrics]:
        """
        Get health metrics.

        Args:
            provider_id: Optional provider ID to filter

        Returns:
            Dict mapping provider IDs to metrics
        """
        if provider_id:
            metrics = self._metrics.get(provider_id)
            return {provider_id: metrics} if metrics else {}

        return self._metrics.copy()

    def get_health_history(
        self,
        provider_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[HealthCheckResult]:
        """
        Get health check history.

        Args:
            provider_id: Optional provider ID to filter
            since: Optional datetime to filter results after
            limit: Optional limit on number of results

        Returns:
            List of health check results
        """
        results = self._health_history

        if provider_id:
            results = [r for r in results if r.provider_id == provider_id]

        if since:
            results = [r for r in results if r.timestamp >= since]

        if limit:
            results = results[-limit:]

        return results

    async def get_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report.

        Returns:
            Dict with health status of all providers
        """
        providers = self.registry.get_all_providers()

        report = {
            "timestamp": datetime.now(),
            "total_providers": len(providers),
            "providers": {},
            "summary": {
                "online": 0,
                "offline": 0,
                "degraded": 0,
            },
        }

        for provider_id, provider in providers.items():
            metrics = self._metrics.get(provider_id)

            provider_report = {
                "id": provider_id,
                "name": provider.name,
                "status": (
                    provider.status.value
                    if hasattr(provider.status, "value")
                    else provider.status
                ),
                "type": (
                    provider.provider_type.value
                    if hasattr(provider.provider_type, "value")
                    else provider.provider_type
                ),
                "endpoint": provider.endpoint,
                "last_checked": provider.lastChecked,
                "response_time_ms": provider.responseTime,
            }

            if metrics:
                provider_report.update({
                    "uptime_percentage": metrics.uptime_percentage,
                    "total_checks": metrics.total_checks,
                    "consecutive_failures": metrics.consecutive_failures,
                    "average_response_time_ms": metrics.average_response_time_ms,
                })

            report["providers"][provider_id] = provider_report

            # Update summary
            if provider.status == ProviderStatus.ONLINE:
                report["summary"]["online"] += 1
            elif provider.status == ProviderStatus.OFFLINE:
                report["summary"]["offline"] += 1
            else:
                report["summary"]["degraded"] += 1

        return report

    def clear_history(self) -> None:
        """Clear health check history."""
        self._health_history.clear()
        logger.info("Cleared health check history")

    def reset_metrics(self, provider_id: Optional[str] = None) -> None:
        """
        Reset metrics.

        Args:
            provider_id: Optional provider ID to reset, or all if None
        """
        if provider_id:
            if provider_id in self._metrics:
                del self._metrics[provider_id]
                logger.info(f"Reset metrics for {provider_id}")
        else:
            self._metrics.clear()
            logger.info("Reset all metrics")
