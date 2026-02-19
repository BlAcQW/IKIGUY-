"""
Tests for Core Backend TelephonyService integration with shared libraries.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from backend.services.telephony_service import TelephonyService
from apps.shared.telephony import TelephonyEvent, CallContext, ProviderHealth, ProviderSettings, CallResult
from apps.shared.telephony.interfaces import TelephonyEventType


class TestTelephonyService:
    """Test cases for TelephonyService integration with shared libraries."""

    @pytest.fixture
    def telephony_service(self):
        """Create a telephony service instance for testing."""
        service = TelephonyService()
        return service

    @pytest.mark.asyncio
    async def test_telephony_service_initialization(self, telephony_service):
        """Test that telephony service initializes correctly with shared library."""
        assert telephony_service.storage is not None
        assert telephony_service.provider_manager is not None
        assert hasattr(telephony_service.provider_manager, 'register_provider')

    @pytest.mark.asyncio
    async def test_create_telephony_event(self, telephony_service):
        """Test creating telephony events."""
        call_id = "test-call-123"
        tenant_id = "test-tenant-123"
        event_type = TelephonyEventType.CALL_STARTED
        provider = "test-provider"
        data = {"duration": 30, "status": "connected"}
        
        result = await telephony_service.create_telephony_event(
            call_id=call_id,
            tenant_id=tenant_id,
            event_type=event_type.value,
            provider=provider,
            data=data
        )
        
        assert result is not None
        assert result.call_id == call_id
        assert result.event_type == event_type
        assert result.provider == provider

    @pytest.mark.asyncio
    async def test_get_call_events(self, telephony_service):
        """Test getting call events."""
        call_id = "test-call-123"
        tenant_id = "test-tenant-123"

        # Create some test events
        await telephony_service.create_telephony_event(
            call_id=call_id,
            tenant_id=tenant_id,
            event_type=TelephonyEventType.CALL_STARTED.value,
            provider="test-provider"
        )
    
        await telephony_service.create_telephony_event(
            call_id=call_id,
            tenant_id=tenant_id,
            event_type=TelephonyEventType.CALL_ENDED.value,
            provider="test-provider"
        )

        events = await telephony_service.get_call_events(call_id=call_id)
        
        assert len(events) >= 2
        assert events[0].event_type == TelephonyEventType.CALL_STARTED
        assert events[1].event_type == TelephonyEventType.CALL_ENDED

    @pytest.mark.asyncio
    async def test_create_call_context(self, telephony_service):
        """Test creating call context."""
        call_id = "test-call-123"
        tenant_id = "test-tenant-123"
        destination = "+1234567890"
        source = "+0987654321"
        
        context = await telephony_service.create_call_context(
            call_id=call_id,
            tenant_id=tenant_id,
            destination=destination,
            source=source,
            campaign_id="test-campaign",
            cost_preference="low",
            quality_preference="high"
        )
        
        assert context is not None
        assert context.call_id == call_id
        assert context.tenant_id == tenant_id
        assert context.destination == destination
        assert context.source == source

    @pytest.mark.asyncio
    async def test_get_call_context(self, telephony_service):
        """Test getting call context."""
        call_id = "test-call-123"
        tenant_id = "test-tenant-123"
        
        # Create a test context
        await telephony_service.create_call_context(
            call_id=call_id,
            tenant_id=tenant_id,
            destination="+1234567890",
            source="+0987654321"
        )
        
        context = await telephony_service.get_call_context(call_id)
        
        assert context is not None
        assert context.call_id == call_id
        assert context.tenant_id == tenant_id

    @pytest.mark.asyncio
    async def test_add_provider(self, telephony_service):
        """Test adding a telephony provider."""
        provider_id = "test-provider"
        settings = ProviderSettings(
            provider_id=provider_id,
            api_key="test-key",
            api_secret="test-secret",
            base_url="https://api.test.com",
            timeout_seconds=30,
            retry_attempts=3,
            enabled=True,
            priority=1,
            cost_multiplier=1.0,
            max_concurrent_calls=100
        )
        
        result = await telephony_service.add_provider(provider_id, settings)
        assert result is True

    @pytest.mark.asyncio
    async def test_set_provider_settings(self, telephony_service):
        """Test setting provider settings."""
        provider_id = "test-provider"

        # Set provider settings
        success = await telephony_service.set_provider_settings(
            provider_id=provider_id,
            api_key="test-key",
            api_secret="test-secret",
            base_url="https://api.test.com",
            enabled=True
        )
        
        assert success is True
        
        # Get the settings back
        settings = await telephony_service.get_provider_settings(provider_id)
        assert settings is not None
        assert settings.provider_id == provider_id
        assert settings.api_key == "test-key"
        assert settings.enabled is True

    @pytest.mark.asyncio
    async def test_initiate_call(self, telephony_service):
        """Test initiating a call."""
        tenant_id = "test-tenant-123"
        destination = "+1234567890"
        source = "+0987654321"
        
        result = await telephony_service.initiate_call(
            tenant_id=tenant_id,
            destination=destination,
            source=source
        )
        
        assert result is not None
        assert result.success is True
        assert result.call_id is not None

    @pytest.mark.asyncio
    async def test_get_call_result(self, telephony_service):
        """Test getting call result."""
        call_id = "test-call-123"
        tenant_id = "test-tenant-123"
        
        # Store a test call result
        await telephony_service.storage.insert("call_results", {
            "call_id": call_id,
            "tenant_id": tenant_id,
            "success": True,
            "provider": "test-provider",
            "duration_seconds": 60.0,
            "cost_usd": 0.05,
            "status": "completed",
            "error_message": None,
            "metadata": "{}"
        })
        
        retrieved_result = await telephony_service.get_call_result(call_id)
        
        assert retrieved_result is not None
        assert retrieved_result.call_id == call_id
        assert retrieved_result.success is True



    @pytest.mark.asyncio
    async def test_telephony_service_error_handling(self, telephony_service):
        """Test error handling in telephony service."""
        # Test with invalid call ID
        result = await telephony_service.get_call_context("invalid-call-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_telephony_service_performance(self, telephony_service):
        """Test telephony service performance."""
        import time
        
        start_time = time.time()
        
        # Test multiple operations
        for i in range(10):
            await telephony_service.create_telephony_event(
                call_id=f"call-{i}",
                tenant_id="test-tenant",
                event_type=TelephonyEventType.CALL_STARTED.value,
                provider="test-provider"
            )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (2 seconds)
        assert execution_time < 2.0

    @pytest.mark.asyncio
    async def test_telephony_service_concurrent_operations(self, telephony_service):
        """Test concurrent telephony operations."""
        async def create_event(i):
            return await telephony_service.create_telephony_event(
                call_id=f"concurrent-call-{i}",
                tenant_id="test-tenant",
                event_type=TelephonyEventType.CALL_STARTED.value,
                provider="test-provider"
            )
        
        # Run 5 concurrent operations
        tasks = [create_event(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All operations should complete
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_provider_health_monitoring(self, telephony_service):
        """Test provider health monitoring."""
        provider_id = "health-test-provider"
        
        # Add a provider
        settings = ProviderSettings(
            provider_id=provider_id,
            api_key="health-key",
            api_secret="health-secret",
            base_url="https://health-api.com",
            enabled=True
        )
        await telephony_service.add_provider(provider_id, settings)
        
        # Get health status
        health = await telephony_service.get_provider_health(provider_id)
        assert health is not None
        assert health.provider_id == provider_id

    @pytest.mark.asyncio
    async def test_call_context_metadata(self, telephony_service):
        """Test call context with metadata."""
        call_id = "metadata-call-123"
        tenant_id = "test-tenant-123"
        metadata = {
            "campaign_name": "Test Campaign",
            "customer_id": "customer-123",
            "priority": "high",
            "tags": ["test", "demo"]
        }
        
        context = await telephony_service.create_call_context(
            call_id=call_id,
            tenant_id=tenant_id,
            destination="+1234567890",
            source="+0987654321",
            metadata=metadata
        )
        
        assert context is not None
        assert context.call_id == call_id
        assert context.metadata == metadata

    @pytest.mark.asyncio
    async def test_telephony_service_initialization_with_custom_storage(self, telephony_service):
        """Test telephony service initialization with custom storage backend."""
        from apps.shared.storage import MemoryStorageBackend
        from apps.shared.storage.interfaces import StorageConfig
        
        # Create custom storage backend
        storage_config = StorageConfig(backend_type="memory", connection_string="memory://")
        custom_storage = MemoryStorageBackend(storage_config)
        
        # Create telephony service with custom storage
        custom_telephony_service = TelephonyService(storage_backend=custom_storage)
        
        assert custom_telephony_service.storage is not None
        assert custom_telephony_service.storage == custom_storage

    @pytest.mark.asyncio
    async def test_telephony_service_tenant_isolation(self, telephony_service):
        """Test tenant isolation in telephony service."""
        tenant_1 = "tenant-1"
        tenant_2 = "tenant-2"
        call_id = "shared-call-123"
        
        # Create events for different tenants
        event1 = await telephony_service.create_telephony_event(
            call_id=call_id,
            tenant_id=tenant_1,
            event_type=TelephonyEventType.CALL_STARTED.value,
            provider="provider-1"
        )
        
        event2 = await telephony_service.create_telephony_event(
            call_id=call_id,
            tenant_id=tenant_2,
            event_type=TelephonyEventType.CALL_STARTED.value,
            provider="provider-2"
        )
        
        # Get events for specific tenant
        tenant_1_events = await telephony_service.get_telephony_events(
            call_id=call_id,
            tenant_id=tenant_1
        )
        
        tenant_2_events = await telephony_service.get_telephony_events(
            call_id=call_id,
            tenant_id=tenant_2
        )
        
        # Verify tenant isolation
        for event in tenant_1_events:
            assert event["tenant_id"] == tenant_1
        
        for event in tenant_2_events:
            assert event["tenant_id"] == tenant_2

    @pytest.mark.asyncio
    async def test_telephony_service_provider_operations(self, telephony_service):
        """Test comprehensive provider operations."""
        provider_id = "comprehensive-provider"
        
        # Test adding provider
        settings = ProviderSettings(
            provider_id=provider_id,
            api_key="comprehensive-key",
            api_secret="comprehensive-secret",
            base_url="https://comprehensive-api.com",
            timeout_seconds=60,
            retry_attempts=5,
            enabled=True,
            priority=1,
            cost_multiplier=1.2,
            max_concurrent_calls=200
        )
        
        add_result = await telephony_service.add_provider(provider_id, settings)
        assert add_result is True
        
        # Test getting provider health
        health = await telephony_service.get_provider_health(provider_id)
        assert health is not None
        assert health.provider_id == provider_id
        
        # Test updating provider settings
        updated_settings = ProviderSettings(
            provider_id=provider_id,
            api_key="updated-key",
            api_secret="updated-secret",
            base_url="https://updated-api.com",
            enabled=True
        )
        
        update_result = await telephony_service.update_provider_settings(provider_id, updated_settings)
        assert update_result is True
        
        # Test removing provider
        remove_result = await telephony_service.remove_provider(provider_id)
        assert remove_result is True


if __name__ == "__main__":
    pytest.main([__file__])
