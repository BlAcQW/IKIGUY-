"""
Usage Tracking System Tests

This module provides comprehensive tests for the usage tracking system.
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from usage.interfaces import UsageRecord
from usage.engine import UsageTrackingEngine
from usage.models import RateLimit


class SimpleStorageAdapter:
    """Simple in-memory storage adapter for testing"""
    
    def __init__(self):
        self.data = {}
        self.tables = {}
        
    async def create_table(self, table_name: str, schema: Dict[str, str]) -> bool:
        """Create a table"""
        self.tables[table_name] = schema
        self.data[table_name] = []
        return True
        
    async def insert(self, table_name: str, data: Dict[str, Any]) -> bool:
        """Insert data into table"""
        if table_name not in self.data:
            self.data[table_name] = []
        self.data[table_name].append(data.copy())
        return True
        
    async def select(self, table_name: str, where: Dict[str, Any] = None) -> list:
        """Select data from table"""
        if table_name not in self.data:
            return []
            
        results = self.data[table_name]
        
        if where:
            filtered_results = []
            for record in results:
                match = True
                for key, value in where.items():
                    if key in record:
                        if isinstance(value, dict):
                            # Handle range queries
                            if "gte" in value and record[key] < value["gte"]:
                                match = False
                            if "lte" in value and record[key] > value["lte"]:
                                match = False
                            if "lt" in value and record[key] >= value["lt"]:
                                match = False
                        elif record[key] != value:
                            match = False
                    else:
                        match = False
                        
                if match:
                    filtered_results.append(record)
            return filtered_results
            
        return results
        
    async def select_one(self, table_name: str, where: Dict[str, Any] = None) -> Dict[str, Any]:
        """Select one record from table"""
        results = await self.select(table_name, where)
        return results[0] if results else None
        
    async def upsert(self, table_name: str, data: Dict[str, Any]) -> bool:
        """Upsert data into table"""
        if table_name not in self.data:
            self.data[table_name] = []
            
        # Check if record exists
        for i, record in enumerate(self.data[table_name]):
            if (record.get("tenant_id") == data.get("tenant_id") and 
                record.get("service") == data.get("service")):
                self.data[table_name][i] = data.copy()
                return True
                
        # Insert new record
        self.data[table_name].append(data.copy())
        return True
        
    async def delete(self, table_name: str, where: Dict[str, Any] = None) -> int:
        """Delete data from table"""
        if table_name not in self.data:
            return 0
            
        if not where:
            deleted_count = len(self.data[table_name])
            self.data[table_name] = []
            return deleted_count
            
        deleted_count = 0
        remaining_records = []
        
        for record in self.data[table_name]:
            match = True
            for key, value in where.items():
                if key in record:
                    if isinstance(value, dict):
                        # Handle range queries
                        if "lt" in value and record[key] >= value["lt"]:
                            match = False
                    elif record[key] != value:
                        match = False
                else:
                    match = False
                    
            if match:
                deleted_count += 1
            else:
                remaining_records.append(record)
                
        self.data[table_name] = remaining_records
        return deleted_count


@pytest.fixture
def storage_backend():
    """Storage backend fixture"""
    return SimpleStorageAdapter()


@pytest.fixture
async def usage_engine(storage_backend):
    """Usage tracking engine fixture"""
    engine = UsageTrackingEngine(storage_backend)
    await engine.start()
    return engine


class TestUsageTrackingEngine:
    """Test usage tracking engine functionality"""
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, usage_engine):
        """Test usage tracking engine initialization"""
        usage_engine = await usage_engine
        assert usage_engine is not None
        assert hasattr(usage_engine, 'record_usage')
        assert hasattr(usage_engine, 'get_usage_summary')
        
    @pytest.mark.asyncio
    async def test_record_usage(self, usage_engine):
        """Test recording usage"""
        usage_engine = await usage_engine
        
        # Create usage record
        record = UsageRecord(
            tenant_id="test_tenant",
            service="telephony",
            metric="call_duration",
            value=5.5,
            cost=0.25,
            call_id="call_123",
            metadata={"provider": "vapi", "region": "us-east"}
        )
        
        # Record usage
        success = await usage_engine.record_usage(record)
        assert success is True
        
        # Verify record was stored
        records = await usage_engine.storage.select("usage_records")
        assert len(records) == 1
        assert records[0]["tenant_id"] == "test_tenant"
        assert records[0]["service"] == "telephony"
        assert records[0]["metric"] == "call_duration"
        assert float(records[0]["value"]) == 5.5
        assert float(records[0]["cost"]) == 0.25
        
    @pytest.mark.asyncio
    async def test_get_usage_summary(self, usage_engine):
        """Test getting usage summary"""
        usage_engine = await usage_engine
        
        # Record multiple usage events
        records = [
            UsageRecord(
                tenant_id="summary_tenant",
                service="telephony",
                metric="call_duration",
                value=10.0,
                cost=0.50
            ),
            UsageRecord(
                tenant_id="summary_tenant",
                service="telephony",
                metric="call_duration",
                value=15.0,
                cost=0.75
            ),
            UsageRecord(
                tenant_id="summary_tenant",
                service="ai",
                metric="api_calls",
                value=100.0,
                cost=2.00
            )
        ]
        
        for record in records:
            await usage_engine.record_usage(record)
            
        # Get usage summary
        summary = await usage_engine.get_usage_summary("summary_tenant", "daily")
        
        assert "telephony.call_duration" in summary
        assert summary["telephony.call_duration"] == 25.0
        assert "ai.api_calls" in summary
        assert summary["ai.api_calls"] == 100.0
        
    @pytest.mark.asyncio
    async def test_calculate_costs(self, usage_engine):
        """Test cost calculation"""
        usage_engine = await usage_engine
        
        # Record usage with costs
        records = [
            UsageRecord(
                tenant_id="cost_tenant",
                service="telephony",
                metric="call_duration",
                value=10.0,
                cost=0.50
            ),
            UsageRecord(
                tenant_id="cost_tenant",
                service="ai",
                metric="api_calls",
                value=100.0,
                cost=2.00
            ),
            UsageRecord(
                tenant_id="cost_tenant",
                service="storage",
                metric="data_transfer",
                value=1.0,
                cost=0.10
            )
        ]
        
        for record in records:
            await usage_engine.record_usage(record)
            
        # Calculate costs
        costs = await usage_engine.calculate_costs("cost_tenant", "daily")
        
        assert "telephony" in costs
        assert costs["telephony"] == 0.50
        assert "ai" in costs
        assert costs["ai"] == 2.00
        assert "storage" in costs
        assert costs["storage"] == 0.10
        
    @pytest.mark.asyncio
    async def test_export_usage_json(self, usage_engine):
        """Test usage export in JSON format"""
        usage_engine = await usage_engine
        
        # Record usage
        record = UsageRecord(
            tenant_id="export_tenant",
            service="telephony",
            metric="call_duration",
            value=5.5,
            cost=0.25,
            call_id="call_123"
        )
        await usage_engine.record_usage(record)
        
        # Export usage
        export_data = await usage_engine.export_usage("export_tenant", "json")
        
        # Parse JSON
        data = json.loads(export_data.decode('utf-8'))
        assert len(data) == 1
        assert data[0]["tenant_id"] == "export_tenant"
        assert data[0]["service"] == "telephony"
        assert data[0]["metric"] == "call_duration"
        assert data[0]["value"] == 5.5
        assert data[0]["cost"] == 0.25
        
    @pytest.mark.asyncio
    async def test_export_usage_csv(self, usage_engine):
        """Test usage export in CSV format"""
        usage_engine = await usage_engine
        
        # Record usage
        record = UsageRecord(
            tenant_id="export_csv_tenant",
            service="telephony",
            metric="call_duration",
            value=5.5,
            cost=0.25,
            call_id="call_123"
        )
        await usage_engine.record_usage(record)
        
        # Export usage
        export_data = await usage_engine.export_usage("export_csv_tenant", "csv")
        
        # Parse CSV
        csv_content = export_data.decode('utf-8')
        lines = csv_content.strip().split('\n')
        
        # Check header
        assert "tenant_id,timestamp,service,metric,value,cost,call_id,user_id,campaign_id" in lines[0]
        
        # Check data
        data_line = lines[1]
        assert "export_csv_tenant" in data_line
        assert "telephony" in data_line
        assert "call_duration" in data_line
        assert "5.5" in data_line
        assert "0.25" in data_line
        
    @pytest.mark.asyncio
    async def test_get_usage_by_service(self, usage_engine):
        """Test getting usage by service"""
        usage_engine = await usage_engine
        
        # Record usage for different services
        records = [
            UsageRecord(
                tenant_id="service_tenant",
                service="telephony",
                metric="call_duration",
                value=10.0,
                cost=0.50
            ),
            UsageRecord(
                tenant_id="service_tenant",
                service="ai",
                metric="api_calls",
                value=100.0,
                cost=2.00
            ),
            UsageRecord(
                tenant_id="service_tenant",
                service="telephony",
                metric="call_count",
                value=5.0,
                cost=0.25
            )
        ]
        
        for record in records:
            await usage_engine.record_usage(record)
            
        # Get telephony usage
        telephony_records = await usage_engine.get_usage_by_service("service_tenant", "telephony", "daily")
        assert len(telephony_records) == 2
        
        # Get AI usage
        ai_records = await usage_engine.get_usage_by_service("service_tenant", "ai", "daily")
        assert len(ai_records) == 1
        
    @pytest.mark.asyncio
    async def test_get_usage_by_metric(self, usage_engine):
        """Test getting usage by metric"""
        usage_engine = await usage_engine
        
        # Record usage for different metrics
        records = [
            UsageRecord(
                tenant_id="metric_tenant",
                service="telephony",
                metric="call_duration",
                value=10.0,
                cost=0.50
            ),
            UsageRecord(
                tenant_id="metric_tenant",
                service="ai",
                metric="call_duration",
                value=5.0,
                cost=0.25
            ),
            UsageRecord(
                tenant_id="metric_tenant",
                service="telephony",
                metric="call_count",
                value=5.0,
                cost=0.25
            )
        ]
        
        for record in records:
            await usage_engine.record_usage(record)
            
        # Get call_duration usage
        duration_records = await usage_engine.get_usage_by_metric("metric_tenant", "call_duration", "daily")
        assert len(duration_records) == 2
        
        # Get call_count usage
        count_records = await usage_engine.get_usage_by_metric("metric_tenant", "call_count", "daily")
        assert len(count_records) == 1
        
    @pytest.mark.asyncio
    async def test_get_total_usage(self, usage_engine):
        """Test getting total usage"""
        usage_engine = await usage_engine
        
        # Record usage
        records = [
            UsageRecord(
                tenant_id="total_tenant",
                service="telephony",
                metric="call_duration",
                value=10.0,
                cost=0.50
            ),
            UsageRecord(
                tenant_id="total_tenant",
                service="ai",
                metric="api_calls",
                value=100.0,
                cost=2.00
            )
        ]
        
        for record in records:
            await usage_engine.record_usage(record)
            
        # Get total usage
        total_usage = await usage_engine.get_total_usage("total_tenant", "daily")
        assert total_usage == 110.0
        
    @pytest.mark.asyncio
    async def test_get_total_cost(self, usage_engine):
        """Test getting total cost"""
        usage_engine = await usage_engine
        
        # Record usage with costs
        records = [
            UsageRecord(
                tenant_id="total_cost_tenant",
                service="telephony",
                metric="call_duration",
                value=10.0,
                cost=0.50
            ),
            UsageRecord(
                tenant_id="total_cost_tenant",
                service="ai",
                metric="api_calls",
                value=100.0,
                cost=2.00
            )
        ]
        
        for record in records:
            await usage_engine.record_usage(record)
            
        # Get total cost
        total_cost = await usage_engine.get_total_cost("total_cost_tenant", "daily")
        assert total_cost == 2.50
        
    @pytest.mark.asyncio
    async def test_cleanup_old_records(self, usage_engine):
        """Test cleaning up old records"""
        usage_engine = await usage_engine
        
        # Record usage with old timestamps
        old_record = UsageRecord(
            tenant_id="cleanup_tenant",
            service="telephony",
            metric="call_duration",
            value=10.0,
            cost=0.50,
            timestamp=datetime.utcnow() - timedelta(days=10)
        )
        await usage_engine.record_usage(old_record)
        
        # Record usage with recent timestamp
        recent_record = UsageRecord(
            tenant_id="cleanup_tenant",
            service="telephony",
            metric="call_duration",
            value=5.0,
            cost=0.25,
            timestamp=datetime.utcnow()
        )
        await usage_engine.record_usage(recent_record)
        
        # Verify we have 2 records
        records = await usage_engine.storage.select("usage_records")
        assert len(records) == 2
        
        # Clean up records older than 5 days
        deleted_count = await usage_engine.cleanup_old_records(5)
        assert deleted_count == 1
        
        # Verify only recent record remains
        records = await usage_engine.storage.select("usage_records")
        assert len(records) == 1
        assert float(records[0]["value"]) == 5.0
        
    @pytest.mark.asyncio
    async def test_period_calculations(self, usage_engine):
        """Test period start date calculations"""
        usage_engine = await usage_engine
        
        # Test daily period
        end_date = datetime(2023, 12, 15, 14, 30, 0)
        daily_start = usage_engine._get_period_start_date(end_date, "daily")
        assert daily_start == datetime(2023, 12, 15, 0, 0, 0)
        
        # Test weekly period
        weekly_start = usage_engine._get_period_start_date(end_date, "weekly")
        # December 15, 2023 is a Friday, so week starts on Monday (Dec 11)
        # The method should return the start of the week (00:00:00)
        expected_weekly_start = datetime(2023, 12, 11, 0, 0, 0)
        assert weekly_start == expected_weekly_start
        
        # Test monthly period
        monthly_start = usage_engine._get_period_start_date(end_date, "monthly")
        assert monthly_start == datetime(2023, 12, 1, 0, 0, 0)
        
        # Test yearly period
        yearly_start = usage_engine._get_period_start_date(end_date, "yearly")
        assert yearly_start == datetime(2023, 1, 1, 0, 0, 0)
        
    @pytest.mark.asyncio
    async def test_rate_limit_management(self, usage_engine):
        """Test rate limit management"""
        usage_engine = await usage_engine
        
        # Create a rate limit
        rate_limit = RateLimit(
            tenant_id="rate_limit_tenant",
            service="telephony",
            limit_type="calls_per_hour",
            current_usage=0,
            limit=100,
            reset_time=datetime.utcnow() + timedelta(hours=1),
            exceeded=False
        )
        
        # Save rate limit
        await usage_engine._save_rate_limit(rate_limit)
        
        # Get rate limit
        retrieved_limit = await usage_engine._get_rate_limit("rate_limit_tenant", "telephony")
        assert retrieved_limit is not None
        assert retrieved_limit.tenant_id == "rate_limit_tenant"
        assert retrieved_limit.service == "telephony"
        assert retrieved_limit.limit == 100
        
    @pytest.mark.asyncio
    async def test_error_handling(self, usage_engine):
        """Test error handling"""
        usage_engine = await usage_engine
        
        # Test invalid export format
        export_data = await usage_engine.export_usage("test_tenant", "invalid_format")
        assert export_data == b""
        
        # Test usage summary for non-existent tenant
        summary = await usage_engine.get_usage_summary("non_existent_tenant", "daily")
        assert summary == {}
        
        # Test cost calculation for non-existent tenant
        costs = await usage_engine.calculate_costs("non_existent_tenant", "daily")
        assert costs == {}
        
    @pytest.mark.asyncio
    async def test_metadata_handling(self, usage_engine):
        """Test metadata handling in usage records"""
        usage_engine = await usage_engine
        
        # Create usage record with metadata
        metadata = {
            "provider": "vapi",
            "region": "us-east",
            "call_type": "inbound",
            "duration_seconds": 330
        }
        
        record = UsageRecord(
            tenant_id="metadata_tenant",
            service="telephony",
            metric="call_duration",
            value=5.5,
            cost=0.25,
            metadata=metadata
        )
        
        # Record usage
        success = await usage_engine.record_usage(record)
        assert success is True
        
        # Verify metadata was stored
        records = await usage_engine.storage.select("usage_records")
        assert len(records) == 1
        
        stored_metadata = json.loads(records[0]["metadata"])
        assert stored_metadata["provider"] == "vapi"
        assert stored_metadata["region"] == "us-east"
        assert stored_metadata["call_type"] == "inbound"
        assert stored_metadata["duration_seconds"] == 330


class TestUsageTrackingIntegration:
    """Integration tests for usage tracking system"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, usage_engine):
        """Test complete usage tracking workflow"""
        usage_engine = await usage_engine
        
        # 1. Record multiple usage events
        records = [
            UsageRecord(
                tenant_id="workflow_tenant",
                service="telephony",
                metric="call_duration",
                value=10.0,
                cost=0.50,
                call_id="call_1"
            ),
            UsageRecord(
                tenant_id="workflow_tenant",
                service="telephony",
                metric="call_duration",
                value=15.0,
                cost=0.75,
                call_id="call_2"
            ),
            UsageRecord(
                tenant_id="workflow_tenant",
                service="ai",
                metric="api_calls",
                value=100.0,
                cost=2.00
            ),
            UsageRecord(
                tenant_id="workflow_tenant",
                service="storage",
                metric="data_transfer",
                value=1.0,
                cost=0.10
            )
        ]
        
        for record in records:
            success = await usage_engine.record_usage(record)
            assert success is True
            
        # 2. Get usage summary
        summary = await usage_engine.get_usage_summary("workflow_tenant", "daily")
        assert "telephony.call_duration" in summary
        assert summary["telephony.call_duration"] == 25.0
        assert "ai.api_calls" in summary
        assert summary["ai.api_calls"] == 100.0
        assert "storage.data_transfer" in summary
        assert summary["storage.data_transfer"] == 1.0
        
        # 3. Calculate costs
        costs = await usage_engine.calculate_costs("workflow_tenant", "daily")
        assert costs["telephony"] == 1.25
        assert costs["ai"] == 2.00
        assert costs["storage"] == 0.10
        
        # 4. Get total usage and cost
        total_usage = await usage_engine.get_total_usage("workflow_tenant", "daily")
        assert total_usage == 126.0
        
        total_cost = await usage_engine.get_total_cost("workflow_tenant", "daily")
        assert total_cost == 3.35
        
        # 5. Export usage data
        export_data = await usage_engine.export_usage("workflow_tenant", "json")
        data = json.loads(export_data.decode('utf-8'))
        assert len(data) == 4
        
        # 6. Get usage by service
        telephony_records = await usage_engine.get_usage_by_service("workflow_tenant", "telephony", "daily")
        assert len(telephony_records) == 2
        
        ai_records = await usage_engine.get_usage_by_service("workflow_tenant", "ai", "daily")
        assert len(ai_records) == 1
        
        # 7. Get usage by metric
        duration_records = await usage_engine.get_usage_by_metric("workflow_tenant", "call_duration", "daily")
        assert len(duration_records) == 2
        
        api_records = await usage_engine.get_usage_by_metric("workflow_tenant", "api_calls", "daily")
        assert len(api_records) == 1
        
        # 8. Verify all data is consistent
        all_records = await usage_engine.storage.select("usage_records")
        assert len(all_records) == 4
        
        # Verify telephony records
        telephony_stored = [r for r in all_records if r["service"] == "telephony"]
        assert len(telephony_stored) == 2
        
        # Verify AI records
        ai_stored = [r for r in all_records if r["service"] == "ai"]
        assert len(ai_stored) == 1
        
        # Verify storage records
        storage_stored = [r for r in all_records if r["service"] == "storage"]
        assert len(storage_stored) == 1
