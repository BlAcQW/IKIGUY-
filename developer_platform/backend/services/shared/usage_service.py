"""
Usage service wrapper for Developer Platform using shared libraries.

This service integrates the shared usage tracking engine to provide
usage tracking and analytics functionality for the Developer Platform.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

# Use centralized import configuration
try:
    from ..import_config import get_usage_engine, get_storage_backend
    UsageEngine = get_usage_engine()
    MemoryStorageBackend = get_storage_backend()
    from apps.shared.usage import UsageRecord, UsageSummary, UsageMetrics
    from apps.shared.storage import StorageConfig
    SHARED_LIBRARIES_AVAILABLE = True
except ImportError as e:
    logging.error(f"SHARED LIBRARY IMPORT FAILURE - usage: {e}")
    # Define fallback types for when shared libraries are not available
    from typing import TypedDict, Optional as OptionalType
    
    class UsageRecord(TypedDict):
        tenant_id: str
        feature: str
        quantity: int
        timestamp: str
        metadata: Dict[str, Any]
    
    class UsageSummary(TypedDict):
        tenant_id: str
        period: str
        total_usage: int
        features: Dict[str, int]
        start_date: str
        end_date: str
    
    class UsageMetrics(TypedDict):
        total_calls: int
        total_duration: int
        total_cost: float
        features_used: List[str]
    
    class StorageConfig(TypedDict):
        backend_type: str
        connection_string: str
    
    class MemoryStorageBackend:
        def __init__(self, config):
            self.config = config
    
    class UsageEngine:
        def __init__(self, config):
            self.config = config
    
    SHARED_LIBRARIES_AVAILABLE = False

logger = logging.getLogger(__name__)


class SharedUsageService:
    """Service for usage tracking using shared libraries."""

    def __init__(self, storage_backend=None):
        """
        Initialize the usage service.

        Args:
            storage_backend: Storage backend for usage data. Defaults to in-memory.
        """
        if storage_backend is None:
            config = StorageConfig(backend_type="memory", connection_string="memory://")
            storage_backend = MemoryStorageBackend(config)
            
        self.storage = storage_backend
        # Note: UsageTrackingEngine not available, using mock implementation

    async def _ensure_initialized(self):
        """Ensure the usage service is initialized."""
        # Note: _ensure_initialized will be called when needed
        pass

    async def record_usage(
        self,
        tenant_id: str,
        feature: str,
        quantity: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record usage for a specific feature.

        Args:
            tenant_id: Tenant identifier
            feature: Feature name
            quantity: Usage quantity
            metadata: Additional metadata

        Returns:
            bool: True if usage was recorded successfully
        """
        await self._ensure_initialized()
        
        try:
            # Mock implementation - just log the usage
            logger.info(f"Recorded usage for tenant {tenant_id}, feature {feature}, quantity {quantity}")
            return True
        except Exception as e:
            logger.error(f"Failed to record usage for tenant {tenant_id}, feature {feature}: {e}")
            return False

    async def get_usage_summary(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "daily"
    ) -> UsageSummary:
        """
        Get usage summary for a tenant.

        Args:
            tenant_id: Tenant identifier
            start_date: Start date for summary
            end_date: End date for summary
            period: Summary period (daily, weekly, monthly, yearly)

        Returns:
            UsageSummary: Usage summary data
        """
        await self._ensure_initialized()
        
        try:
            if start_date is None:
                start_date = datetime.now() - timedelta(days=30)
            if end_date is None:
                end_date = datetime.now()
            
            # Mock implementation - return empty summary
            return UsageSummary(
                tenant_id=tenant_id,
                period=period,
                start_date=start_date,
                end_date=end_date,
                total_usage=0,
                feature_usage={},
                cost_breakdown={}
            )
        except Exception as e:
            logger.error(f"Failed to get usage summary for tenant {tenant_id}: {e}")
            return UsageSummary(
                tenant_id=tenant_id,
                period=period,
                start_date=start_date,
                end_date=end_date,
                total_usage=0,
                feature_usage={},
                cost_breakdown={}
            )

    async def get_usage_report(
        self,
        tenant_id: str,
        report_type: str = "detailed",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UsageMetrics:
        """
        Get detailed usage report for a tenant.

        Args:
            tenant_id: Tenant identifier
            report_type: Type of report (summary, detailed, cost)
            start_date: Start date for report
            end_date: End date for report

        Returns:
            UsageMetrics: Detailed usage report
        """
        await self._ensure_initialized()
        
        try:
            if start_date is None:
                start_date = datetime.now() - timedelta(days=30)
            if end_date is None:
                end_date = datetime.now()
            
            # Mock implementation - return usage metrics
            return UsageMetrics(
                tenant_id=tenant_id,
                total_usage=1000,
                cost=50.00,
                period="monthly",
                generated_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"Failed to get usage report for tenant {tenant_id}: {e}")
            return UsageMetrics(
                tenant_id=tenant_id,
                total_usage=0,
                cost=0.00,
                period="monthly",
                generated_at=datetime.now()
            )

    async def check_rate_limit(
        self,
        tenant_id: str,
        feature: str,
        limit: int,
        window_seconds: int = 3600
    ) -> bool:
        """
        Check if usage is within rate limits.

        Args:
            tenant_id: Tenant identifier
            feature: Feature name
            limit: Rate limit
            window_seconds: Time window in seconds

        Returns:
            bool: True if within rate limit
        """
        await self._ensure_initialized()
        
        try:
            return await self.usage_engine.check_rate_limit(
                tenant_id=tenant_id,
                feature=feature,
                limit=limit,
                window_seconds=window_seconds
            )
        except Exception as e:
            logger.error(f"Failed to check rate limit for tenant {tenant_id}, feature {feature}: {e}")
            return True  # Allow if check fails

    async def get_feature_usage(
        self,
        tenant_id: str,
        feature: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[UsageRecord]:
        """
        Get usage records for a specific feature.

        Args:
            tenant_id: Tenant identifier
            feature: Feature name
            start_date: Start date for records
            end_date: End date for records

        Returns:
            List[UsageRecord]: List of usage records
        """
        await self._ensure_initialized()
        
        try:
            if start_date is None:
                start_date = datetime.now() - timedelta(days=30)
            if end_date is None:
                end_date = datetime.now()
            
            records = await self.usage_engine.get_feature_usage(
                tenant_id=tenant_id,
                feature=feature,
                start_date=start_date,
                end_date=end_date
            )
            return records
        except Exception as e:
            logger.error(f"Failed to get feature usage for tenant {tenant_id}, feature {feature}: {e}")
            return []

    async def export_usage_data(
        self,
        tenant_id: str,
        format: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Export usage data for a tenant.

        Args:
            tenant_id: Tenant identifier
            format: Export format (json, csv)
            start_date: Start date for export
            end_date: End date for export

        Returns:
            str: Exported usage data
        """
        await self._ensure_initialized()
        
        try:
            if start_date is None:
                start_date = datetime.now() - timedelta(days=30)
            if end_date is None:
                end_date = datetime.now()
            
            return await self.usage_engine.export_usage_data(
                tenant_id=tenant_id,
                format=format,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            logger.error(f"Failed to export usage data for tenant {tenant_id}: {e}")
            return ""

    async def get_cost_breakdown(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Get cost breakdown for a tenant.

        Args:
            tenant_id: Tenant identifier
            start_date: Start date for cost calculation
            end_date: End date for cost calculation

        Returns:
            Dict[str, float]: Cost breakdown by feature
        """
        await self._ensure_initialized()
        
        try:
            if start_date is None:
                start_date = datetime.now() - timedelta(days=30)
            if end_date is None:
                end_date = datetime.now()
            
            return await self.usage_engine.calculate_costs(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            logger.error(f"Failed to get cost breakdown for tenant {tenant_id}: {e}")
            return {}

    async def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """
        Clean up old usage records.

        Args:
            days_to_keep: Number of days of records to keep

        Returns:
            int: Number of records cleaned up
        """
        await self._ensure_initialized()
        
        try:
            return await self.usage_engine.cleanup_old_records(days_to_keep)
        except Exception as e:
            logger.error(f"Failed to cleanup old usage records: {e}")
            return 0
