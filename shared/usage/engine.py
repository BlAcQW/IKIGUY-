"""
Usage Tracking Engine Implementation

This module provides the core usage tracking implementation including record storage,
aggregation, cost calculation, and export functionality.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict

from .interfaces import UsageTracker, UsageRecord
from .models import UsageSummary, CostBreakdown, UsageMetrics, BillingPeriod, RateLimit


class UsageTrackingEngine(UsageTracker):
    """Usage tracking engine implementation"""
    
    def __init__(self, storage_backend: Any):
        """Initialize usage tracking engine"""
        self.storage = storage_backend
        self.logger = logging.getLogger("UsageTracker")
        self._rate_limits: Dict[str, RateLimit] = {}
        
    async def start(self):
        """Start the usage tracking engine"""
        self.logger.info("Starting usage tracking engine")
        await self._initialize_storage()
        
    async def stop(self):
        """Stop the usage tracking engine"""
        self.logger.info("Stopping usage tracking engine")
        
    async def _initialize_storage(self):
        """Initialize storage tables"""
        try:
            # Create usage records table
            usage_schema = {
                "id": "VARCHAR(255) PRIMARY KEY",
                "tenant_id": "VARCHAR(255) NOT NULL",
                "timestamp": "TIMESTAMP NOT NULL",
                "service": "VARCHAR(100) NOT NULL",
                "metric": "VARCHAR(100) NOT NULL",
                "value": "DECIMAL(15,6) NOT NULL",
                "cost": "DECIMAL(10,4) DEFAULT 0.0",
                "metadata": "TEXT",
                "call_id": "VARCHAR(255)",
                "user_id": "VARCHAR(255)",
                "campaign_id": "VARCHAR(255)"
            }
            
            await self.storage.create_table("usage_records", usage_schema)
            
            # Create usage summaries table
            summary_schema = {
                "id": "VARCHAR(255) PRIMARY KEY",
                "tenant_id": "VARCHAR(255) NOT NULL",
                "period": "VARCHAR(20) NOT NULL",
                "start_date": "TIMESTAMP NOT NULL",
                "end_date": "TIMESTAMP NOT NULL",
                "total_calls": "INTEGER DEFAULT 0",
                "total_duration": "DECIMAL(15,6) DEFAULT 0.0",
                "total_cost": "DECIMAL(10,4) DEFAULT 0.0",
                "service_breakdown": "TEXT",
                "metric_breakdown": "TEXT",
                "cost_breakdown": "TEXT"
            }
            
            await self.storage.create_table("usage_summaries", summary_schema)
            
            # Create rate limits table
            rate_limit_schema = {
                "id": "VARCHAR(255) PRIMARY KEY",
                "tenant_id": "VARCHAR(255) NOT NULL",
                "service": "VARCHAR(100) NOT NULL",
                "limit_type": "VARCHAR(50) NOT NULL",
                "current_usage": "INTEGER DEFAULT 0",
                "limit": "INTEGER NOT NULL",
                "reset_time": "TIMESTAMP NOT NULL",
                "exceeded": "BOOLEAN DEFAULT FALSE"
            }
            
            await self.storage.create_table("rate_limits", rate_limit_schema)
            
            self.logger.info("Usage tracking storage initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize usage tracking storage: {e}")
            raise
            
    async def record_usage(self, record: UsageRecord) -> bool:
        """Record usage event"""
        try:
            # Generate unique ID
            record_id = str(uuid.uuid4())
            
            # Prepare record data
            record_data = {
                "id": record_id,
                "tenant_id": record.tenant_id,
                "timestamp": record.timestamp.isoformat(),
                "service": record.service,
                "metric": record.metric,
                "value": float(record.value),
                "cost": float(record.cost),
                "metadata": json.dumps(record.metadata),
                "call_id": record.call_id,
                "user_id": record.user_id,
                "campaign_id": record.campaign_id
            }
            
            # Store record
            await self.storage.insert("usage_records", record_data)
            
            # Update rate limits
            await self._update_rate_limits(record)
            
            self.logger.debug(f"Recorded usage: {record.service}.{record.metric} = {record.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to record usage: {e}")
            return False
            
    async def _update_rate_limits(self, record: UsageRecord):
        """Update rate limits for the usage record"""
        try:
            # Get current rate limit
            rate_limit_key = f"{record.tenant_id}:{record.service}"
            rate_limit = await self._get_rate_limit(record.tenant_id, record.service)
            
            if rate_limit:
                # Check if we need to reset
                if datetime.utcnow() >= rate_limit.reset_time:
                    rate_limit.current_usage = 0
                    rate_limit.reset_time = datetime.utcnow() + timedelta(hours=1)
                    rate_limit.exceeded = False
                
                # Increment usage
                rate_limit.current_usage += 1
                rate_limit.exceeded = rate_limit.current_usage > rate_limit.limit
                
                # Update storage
                await self._save_rate_limit(rate_limit)
                
        except Exception as e:
            self.logger.error(f"Failed to update rate limits: {e}")
            
    async def _get_rate_limit(self, tenant_id: str, service: str) -> Optional[RateLimit]:
        """Get rate limit for tenant and service"""
        try:
            rate_limit_key = f"{tenant_id}:{service}"
            
            # Check cache first
            if rate_limit_key in self._rate_limits:
                return self._rate_limits[rate_limit_key]
            
            # Get from storage
            result = await self.storage.select_one(
                "rate_limits",
                where={"tenant_id": tenant_id, "service": service}
            )
            
            if result:
                rate_limit = RateLimit(
                    tenant_id=result["tenant_id"],
                    service=result["service"],
                    limit_type=result["limit_type"],
                    current_usage=result["current_usage"],
                    limit=result["limit"],
                    reset_time=datetime.fromisoformat(result["reset_time"]),
                    exceeded=result["exceeded"]
                )
                
                # Cache the rate limit
                self._rate_limits[rate_limit_key] = rate_limit
                return rate_limit
                
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get rate limit: {e}")
            return None
            
    async def _save_rate_limit(self, rate_limit: RateLimit):
        """Save rate limit to storage"""
        try:
            rate_limit_data = {
                "tenant_id": rate_limit.tenant_id,
                "service": rate_limit.service,
                "limit_type": rate_limit.limit_type,
                "current_usage": rate_limit.current_usage,
                "limit": rate_limit.limit,
                "reset_time": rate_limit.reset_time.isoformat(),
                "exceeded": rate_limit.exceeded
            }
            
            await self.storage.upsert("rate_limits", rate_limit_data)
            
        except Exception as e:
            self.logger.error(f"Failed to save rate limit: {e}")
            
    async def get_usage_summary(self, tenant_id: str, period: str) -> Dict[str, float]:
        """Get usage summary for period"""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = self._get_period_start_date(end_date, period)
            
            # Get usage records for period
            records = await self.storage.select(
                "usage_records",
                where={
                    "tenant_id": tenant_id,
                    "timestamp": {
                        "gte": start_date.isoformat(),
                        "lte": end_date.isoformat()
                    }
                }
            )
            
            # Aggregate usage
            summary = {}
            for record in records:
                metric_key = f"{record['service']}.{record['metric']}"
                if metric_key not in summary:
                    summary[metric_key] = 0.0
                summary[metric_key] += float(record['value'])
                
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get usage summary: {e}")
            return {}
            
    def _get_period_start_date(self, end_date: datetime, period: str) -> datetime:
        """Get start date for period"""
        if period == "daily":
            return end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "weekly":
            days_since_monday = end_date.weekday()
            return (end_date - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "monthly":
            return end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "yearly":
            return end_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            # Default to daily
            return end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
    async def calculate_costs(self, tenant_id: str, period: str) -> Dict[str, float]:
        """Calculate costs for period"""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = self._get_period_start_date(end_date, period)
            
            # Get usage records for period
            records = await self.storage.select(
                "usage_records",
                where={
                    "tenant_id": tenant_id,
                    "timestamp": {
                        "gte": start_date.isoformat(),
                        "lte": end_date.isoformat()
                    }
                }
            )
            
            # Calculate costs by service
            costs = {}
            for record in records:
                service = record['service']
                if service not in costs:
                    costs[service] = 0.0
                costs[service] += float(record['cost'])
                
            return costs
            
        except Exception as e:
            self.logger.error(f"Failed to calculate costs: {e}")
            return {}
            
    async def export_usage(self, tenant_id: str, format: str = "json") -> bytes:
        """Export usage data"""
        try:
            # Get all usage records for tenant
            records = await self.storage.select(
                "usage_records",
                where={"tenant_id": tenant_id}
            )
            
            # Convert to UsageRecord objects
            usage_records = []
            for record in records:
                usage_record = UsageRecord(
                    tenant_id=record["tenant_id"],
                    timestamp=datetime.fromisoformat(record["timestamp"]),
                    service=record["service"],
                    metric=record["metric"],
                    value=float(record["value"]),
                    cost=float(record["cost"]),
                    metadata=json.loads(record["metadata"]),
                    call_id=record["call_id"],
                    user_id=record["user_id"],
                    campaign_id=record["campaign_id"]
                )
                usage_records.append(usage_record)
            
            # Export in requested format
            if format == "json":
                data = [record.dict() for record in usage_records]
                return json.dumps(data, indent=2, default=str).encode('utf-8')
            elif format == "csv":
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow([
                    "tenant_id", "timestamp", "service", "metric", "value", 
                    "cost", "call_id", "user_id", "campaign_id"
                ])
                
                # Write data
                for record in usage_records:
                    writer.writerow([
                        record.tenant_id,
                        record.timestamp.isoformat(),
                        record.service,
                        record.metric,
                        record.value,
                        record.cost,
                        record.call_id or "",
                        record.user_id or "",
                        record.campaign_id or ""
                    ])
                
                return output.getvalue().encode('utf-8')
            else:
                self.logger.error(f"Unsupported export format: {format}")
                return b""
                
        except Exception as e:
            self.logger.error(f"Failed to export usage: {e}")
            return b""
            
    async def get_usage_by_service(self, tenant_id: str, service: str, period: str) -> List[UsageRecord]:
        """Get usage records by service"""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = self._get_period_start_date(end_date, period)
            
            # Get usage records
            records = await self.storage.select(
                "usage_records",
                where={
                    "tenant_id": tenant_id,
                    "service": service,
                    "timestamp": {
                        "gte": start_date.isoformat(),
                        "lte": end_date.isoformat()
                    }
                }
            )
            
            # Convert to UsageRecord objects
            usage_records = []
            for record in records:
                usage_record = UsageRecord(
                    tenant_id=record["tenant_id"],
                    timestamp=datetime.fromisoformat(record["timestamp"]),
                    service=record["service"],
                    metric=record["metric"],
                    value=float(record["value"]),
                    cost=float(record["cost"]),
                    metadata=json.loads(record["metadata"]),
                    call_id=record["call_id"],
                    user_id=record["user_id"],
                    campaign_id=record["campaign_id"]
                )
                usage_records.append(usage_record)
                
            return usage_records
            
        except Exception as e:
            self.logger.error(f"Failed to get usage by service: {e}")
            return []
            
    async def get_usage_by_metric(self, tenant_id: str, metric: str, period: str) -> List[UsageRecord]:
        """Get usage records by metric"""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = self._get_period_start_date(end_date, period)
            
            # Get usage records
            records = await self.storage.select(
                "usage_records",
                where={
                    "tenant_id": tenant_id,
                    "metric": metric,
                    "timestamp": {
                        "gte": start_date.isoformat(),
                        "lte": end_date.isoformat()
                    }
                }
            )
            
            # Convert to UsageRecord objects
            usage_records = []
            for record in records:
                usage_record = UsageRecord(
                    tenant_id=record["tenant_id"],
                    timestamp=datetime.fromisoformat(record["timestamp"]),
                    service=record["service"],
                    metric=record["metric"],
                    value=float(record["value"]),
                    cost=float(record["cost"]),
                    metadata=json.loads(record["metadata"]),
                    call_id=record["call_id"],
                    user_id=record["user_id"],
                    campaign_id=record["campaign_id"]
                )
                usage_records.append(usage_record)
                
            return usage_records
            
        except Exception as e:
            self.logger.error(f"Failed to get usage by metric: {e}")
            return []
            
    async def get_total_usage(self, tenant_id: str, period: str) -> float:
        """Get total usage value for period"""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = self._get_period_start_date(end_date, period)
            
            # Get usage records for period
            records = await self.storage.select(
                "usage_records",
                where={
                    "tenant_id": tenant_id,
                    "timestamp": {
                        "gte": start_date.isoformat(),
                        "lte": end_date.isoformat()
                    }
                }
            )
            
            # Sum total usage
            total_usage = 0.0
            for record in records:
                total_usage += float(record['value'])
                
            return total_usage
            
        except Exception as e:
            self.logger.error(f"Failed to get total usage: {e}")
            return 0.0
            
    async def get_total_cost(self, tenant_id: str, period: str) -> float:
        """Get total cost for period"""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = self._get_period_start_date(end_date, period)
            
            # Get usage records for period
            records = await self.storage.select(
                "usage_records",
                where={
                    "tenant_id": tenant_id,
                    "timestamp": {
                        "gte": start_date.isoformat(),
                        "lte": end_date.isoformat()
                    }
                }
            )
            
            # Sum total cost
            total_cost = 0.0
            for record in records:
                total_cost += float(record['cost'])
                
            return total_cost
            
        except Exception as e:
            self.logger.error(f"Failed to get total cost: {e}")
            return 0.0
            
    async def cleanup_old_records(self, days_to_keep: int) -> int:
        """Clean up old usage records"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Delete old records
            deleted_count = await self.storage.delete(
                "usage_records",
                where={
                    "timestamp": {"lt": cutoff_date.isoformat()}
                }
            )
            
            self.logger.info(f"Cleaned up {deleted_count} old usage records")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old records: {e}")
            return 0
