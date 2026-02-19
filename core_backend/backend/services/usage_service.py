"""
Usage service that integrates shared usage tracking library.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from uuid import UUID
import logging

from usage.engine import UsageTrackingEngine
from usage.interfaces import UsageRecord
from usage.models import UsageSummary, CostBreakdown
from storage.memory import MemoryStorageBackend

logger = logging.getLogger(__name__)


class UsageService:
    """Service for managing usage tracking using shared libraries."""

    def __init__(self, storage_backend=None):
        """
        Initialize the usage service.

        Args:
            storage_backend: Storage backend for usage data. Defaults to in-memory.
        """
        if storage_backend is None:
            from storage.interfaces import StorageConfig
            config = StorageConfig(backend_type="memory", connection_string="memory://")
            storage_backend = MemoryStorageBackend(config)
        
        self.usage_engine = UsageTrackingEngine(storage_backend)
        # Note: _ensure_initialized will be called when needed

    async def _ensure_initialized(self):
        """Ensure the usage engine is initialized."""
        try:
            await self.usage_engine.get_usage_summary("test", "daily")
        except Exception:
            # This will trigger initialization
            pass

    async def record_usage(
        self,
        tenant_id: str,
        feature: str,
        quantity: int,
        unit: str = "count",
        metadata: Optional[Dict[str, Any]] = None,
        cost: Optional[float] = None,
        provider: Optional[str] = None
    ) -> bool:
        """
        Record usage for a tenant.

        Args:
            tenant_id: Tenant identifier
            feature: Feature being used
            quantity: Usage quantity
            unit: Unit of measurement
            metadata: Additional metadata
            cost: Cost associated with usage
            provider: Provider information

        Returns:
            bool: True if usage was recorded successfully
        """
        try:
            record = UsageRecord(
                tenant_id=tenant_id,
                feature=feature,
                quantity=quantity,
                unit=unit,
                timestamp=datetime.utcnow(),
                metadata=metadata or {},
                cost=cost,
                provider=provider
            )
            return await self.usage_engine.record_usage(record)
        except Exception as e:
            logger.error(f"Failed to record usage: {e}")
            return False

    async def get_usage_summary(
        self,
        tenant_id: str,
        period: str = "daily",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Optional[UsageSummary]:
        """
        Get usage summary for a tenant.

        Args:
            tenant_id: Tenant identifier
            period: Time period (daily, weekly, monthly)
            start_date: Start date for custom period
            end_date: End date for custom period

        Returns:
            UsageSummary: Usage summary data
        """
        try:
            return await self.usage_engine.get_usage_summary(
                tenant_id, period, start_date, end_date
            )
        except Exception as e:
            logger.error(f"Failed to get usage summary: {e}")
            return None

    async def get_cost_breakdown(
        self,
        tenant_id: str,
        period: str = "daily",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Optional[CostBreakdown]:
        """
        Get cost breakdown for a tenant.

        Args:
            tenant_id: Tenant identifier
            period: Time period (daily, weekly, monthly)
            start_date: Start date for custom period
            end_date: End date for custom period

        Returns:
            CostBreakdown: Cost breakdown data
        """
        try:
            return await self.usage_engine.get_cost_breakdown(
                tenant_id, period, start_date, end_date
            )
        except Exception as e:
            logger.error(f"Failed to get cost breakdown: {e}")
            return None

    async def check_usage_limits(
        self,
        tenant_id: str,
        feature: str,
        quantity: int = 1
    ) -> bool:
        """
        Check if usage is within limits.

        Args:
            tenant_id: Tenant identifier
            feature: Feature to check
            quantity: Quantity to check

        Returns:
            bool: True if within limits
        """
        try:
            return await self.usage_engine.check_usage_limits(
                tenant_id, feature, quantity
            )
        except Exception as e:
            logger.error(f"Failed to check usage limits: {e}")
            return False

    async def export_usage_data(
        self,
        tenant_id: str,
        format: str = "json",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> str:
        """
        Export usage data for a tenant.

        Args:
            tenant_id: Tenant identifier
            format: Export format (json, csv)
            start_date: Start date for export
            end_date: End date for export

        Returns:
            str: Exported data
        """
        try:
            return await self.usage_engine.export_usage_data(
                tenant_id, format, start_date, end_date
            )
        except Exception as e:
            logger.error(f"Failed to export usage data: {e}")
            return ""

    async def import_usage_data(
        self,
        tenant_id: str,
        data: str,
        format: str = "json"
    ) -> bool:
        """
        Import usage data for a tenant.

        Args:
            tenant_id: Tenant identifier
            data: Data to import
            format: Import format (json, csv)

        Returns:
            bool: True if import was successful
        """
        try:
            return await self.usage_engine.import_usage_data(
                tenant_id, data, format
            )
        except Exception as e:
            logger.error(f"Failed to import usage data: {e}")
            return False

    async def get_usage_reports(
        self,
        tenant_id: str,
        report_type: str = "summary",
        period: str = "daily",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get usage reports for a tenant.

        Args:
            tenant_id: Tenant identifier
            report_type: Type of report (summary, detailed, cost)
            period: Time period (daily, weekly, monthly)
            start_date: Start date for custom period
            end_date: End date for custom period

        Returns:
            Dict[str, Any]: Report data
        """
        try:
            return await self.usage_engine.get_usage_reports(
                tenant_id, report_type, period, start_date, end_date
            )
        except Exception as e:
            logger.error(f"Failed to get usage reports: {e}")
            return {}

    async def set_rate_limits(
        self,
        tenant_id: str,
        feature: str,
        rate_limit: int,
        window: str = "hour"
    ) -> bool:
        """
        Set rate limits for a tenant feature.

        Args:
            tenant_id: Tenant identifier
            feature: Feature to limit
            rate_limit: Rate limit value
            window: Time window (minute, hour, day)

        Returns:
            bool: True if rate limit was set successfully
        """
        try:
            return await self.usage_engine.set_rate_limits(
                tenant_id, feature, rate_limit, window
            )
        except Exception as e:
            logger.error(f"Failed to set rate limits: {e}")
            return False

    async def check_rate_limits(
        self,
        tenant_id: str,
        feature: str,
        quantity: int = 1
    ) -> bool:
        """
        Check if usage is within rate limits.

        Args:
            tenant_id: Tenant identifier
            feature: Feature to check
            quantity: Quantity to check

        Returns:
            bool: True if within rate limits
        """
        try:
            return await self.usage_engine.check_rate_limits(
                tenant_id, feature, quantity
            )
        except Exception as e:
            logger.error(f"Failed to check rate limits: {e}")
            return False

    async def get_usage(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ):
        """
        Get usage data for a tenant including automation costs.

        Args:
            tenant_id: Tenant identifier
            start_date: Start date for usage period
            end_date: End date for usage period

        Returns:
            Usage data object with all cost breakdowns
        """
        try:
            # Get usage summary
            summary = await self.get_usage_summary(
                tenant_id,
                period="custom",
                start_date=start_date.date() if start_date else None,
                end_date=end_date.date() if end_date else None
            )

            # Get cost breakdown
            cost_breakdown = await self.get_cost_breakdown(
                tenant_id,
                period="custom",
                start_date=start_date.date() if start_date else None,
                end_date=end_date.date() if end_date else None
            )

            # Create usage data object with all fields
            from types import SimpleNamespace
            usage_data = SimpleNamespace(
                tenant_id=tenant_id,
                minutes=summary.total_duration if summary else 0.0,
                messages=summary.total_calls if summary else 0,
                stt_calls=summary.metric_breakdown.get('stt_calls', 0) if summary else 0,
                tts_calls=summary.metric_breakdown.get('tts_calls', 0) if summary else 0,
                telephony_cost=cost_breakdown.telephony_cost if cost_breakdown else 0.0,
                stt_cost=cost_breakdown.feature_breakdown.get('stt', 0.0) if cost_breakdown else 0.0,
                tts_cost=cost_breakdown.feature_breakdown.get('tts', 0.0) if cost_breakdown else 0.0,
                automation_cost=cost_breakdown.feature_breakdown.get('automation', 0.0) if cost_breakdown else 0.0,
                automation_calls=summary.metric_breakdown.get('automation_calls', 0) if summary else 0,
                period=summary.period if summary else "custom",
                generated_at=datetime.utcnow()
            )

            return usage_data

        except Exception as e:
            logger.error(f"Failed to get usage data: {e}")
            # Return default usage data on error
            from types import SimpleNamespace
            return SimpleNamespace(
                tenant_id=tenant_id,
                minutes=0.0,
                messages=0,
                stt_calls=0,
                tts_calls=0,
                telephony_cost=0.0,
                stt_cost=0.0,
                tts_cost=0.0,
                automation_cost=0.0,
                automation_calls=0,
                period="custom",
                generated_at=datetime.utcnow()
            )
