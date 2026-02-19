"""
Tests for Provider Management System

This module tests the provider management system including registry, discovery,
health monitoring, failover, cost optimization, and routing.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

from ..telephony.provider_manager import (
    EnhancedProviderManager,
    ProviderSelectionStrategy,
    ProviderInfo
)
from ..telephony.interfaces import TelephonyPort, TelephonyEvent
from ..telephony.models import CallContext, ProviderHealth, ProviderSettings
from ..telephony.adapters import VapiAdapter, VonageAdapter


class TestProviderManagementSystem:
    """Test the complete provider management system"""

    @pytest.fixture
    def provider_config(self) -> Dict[str, Any]:
        """Provider configuration for testing"""
        return {
            'providers': {
                'vapi': {
                    'type': 'vapi',
                    'api_key': 'test_vapi_key',
                    'base_url': 'https://api.vapi.ai',
                    'enabled': True,
                    'priority': 1,
                    'cost_multiplier': 1.0,
                    'timeout_seconds': 30,
                    'retry_attempts': 3
                },
                'vonage': {
                    'type': 'vonage',
                    'api_key': 'test_vonage_key',
                    'api_secret': 'test_vonage_secret',
                    'base_url': 'https://api.nexmo.com',
                    'enabled': True,
                    'priority': 2,
                    'cost_multiplier': 1.2,
                    'timeout_seconds': 30,
                    'retry_attempts': 3
                },
                'telnyx': {
                    'type': 'telnyx',
                    'api_key': 'test_telnyx_key',
                    'base_url': 'https://api.telnyx.com',
                    'enabled': False,  # Disabled provider
                    'priority': 3,
                    'cost_multiplier': 0.8,
                    'timeout_seconds': 30,
                    'retry_attempts': 3
                }
            }
        }

    @pytest.fixture
    async def provider_manager(self, provider_config):
        """Provider manager instance for testing"""
        manager = EnhancedProviderManager(provider_config)
        
        # Mock adapter connections
        with patch('shared.telephony.adapters.vapi.VapiAdapter.connect', return_value=True), \
             patch('shared.telephony.adapters.vonage.VonageAdapter.connect', return_value=True):
            await manager.start()
            return manager

    @pytest.mark.asyncio
    async def test_provider_registry_and_discovery(self, provider_manager):
        """Test provider registry and discovery functionality"""
        provider_manager = await provider_manager
        # Check that providers are registered
        assert len(provider_manager.providers) == 3  # All providers are registered
        assert 'vapi' in provider_manager.providers
        assert 'vonage' in provider_manager.providers
        assert 'telnyx' in provider_manager.providers  # Disabled provider is still registered
        
        # Check that only enabled providers are available for selection
        available_providers = [
            info for info in provider_manager.providers.values()
            if info.settings.enabled and info.health.is_healthy
        ]
        assert len(available_providers) == 2  # Only enabled providers
        
        # Check provider info structure
        vapi_info = provider_manager.providers['vapi']
        assert isinstance(vapi_info, ProviderInfo)
        assert vapi_info.name == 'vapi'
        assert isinstance(vapi_info.adapter, VapiAdapter)
        assert isinstance(vapi_info.settings, ProviderSettings)
        assert isinstance(vapi_info.health, ProviderHealth)
        assert vapi_info.settings.enabled is True
        assert vapi_info.settings.priority == 1

    @pytest.mark.asyncio
    async def test_health_monitoring_and_failover(self, provider_manager):
        """Test health monitoring and failover functionality"""
        provider_manager = await provider_manager
        # Mock health checks
        with patch.object(provider_manager.providers['vapi'].adapter, 'health_check') as mock_vapi_health, \
             patch.object(provider_manager.providers['vonage'].adapter, 'health_check') as mock_vonage_health:
            
            # Set up healthy VAPI and unhealthy Vonage
            mock_vapi_health.return_value = ProviderHealth(
                provider_id='vapi',
                is_healthy=True,
                last_check=datetime.utcnow(),
                response_time_ms=100,
                error_rate=0.0
            )
            
            mock_vonage_health.return_value = ProviderHealth(
                provider_id='vonage',
                is_healthy=False,
                last_check=datetime.utcnow(),
                response_time_ms=5000,
                error_rate=50.0
            )
            
            # Test health monitoring
            health_status = await provider_manager.get_all_provider_health()
            
            assert health_status['vapi'].is_healthy is True
            assert health_status['vapi'].response_time_ms == 100
            assert health_status['vapi'].error_rate == 0.0
            
            assert health_status['vonage'].is_healthy is False
            assert health_status['vonage'].response_time_ms == 5000
            assert health_status['vonage'].error_rate == 50.0
            
            # Test provider selection with health-based strategy
            provider_manager.selection_strategy = ProviderSelectionStrategy.HEALTH_BASED
            
            context = CallContext(
                destination='+1234567890',
                source='+0987654321',
                tenant_id='test_tenant'
            )
            
            # Should select VAPI (healthy) over Vonage (unhealthy)
            selected_provider = await provider_manager.get_best_provider(context)
            assert selected_provider == provider_manager.providers['vapi'].adapter

    @pytest.mark.asyncio
    async def test_cost_comparison_and_optimization(self, provider_manager):
        """Test cost comparison and optimization functionality"""
        provider_manager = await provider_manager
        # Set up providers with different costs
        provider_manager.providers['vapi'].average_cost = 0.02  # $0.02 per minute
        provider_manager.providers['vapi'].average_quality = 0.9
        
        provider_manager.providers['vonage'].average_cost = 0.03  # $0.03 per minute
        provider_manager.providers['vonage'].average_quality = 0.8
        
        context = CallContext(
            destination='+1234567890',
            source='+0987654321',
            tenant_id='test_tenant'
        )
        
        # Test cost-based selection
        provider_manager.selection_strategy = ProviderSelectionStrategy.COST_BASED
        
        # Low cost preference should select VAPI
        context.cost_preference = "low"
        selected_provider = await provider_manager.get_best_provider(context)
        assert selected_provider == provider_manager.providers['vapi'].adapter
        
        # High cost preference should select Vonage
        context.cost_preference = "high"
        selected_provider = await provider_manager.get_best_provider(context)
        assert selected_provider == provider_manager.providers['vonage'].adapter
        
        # Balanced preference should consider quality/cost ratio
        context.cost_preference = "balanced"
        selected_provider = await provider_manager.get_best_provider(context)
        # VAPI has better quality/cost ratio (0.9/0.02 = 45) vs Vonage (0.8/0.03 = 26.7)
        assert selected_provider == provider_manager.providers['vapi'].adapter

    @pytest.mark.asyncio
    async def test_geographic_and_quality_based_routing(self, provider_manager):
        """Test geographic and quality-based routing"""
        provider_manager = await provider_manager
        # Mock provider health with geographic and quality information
        vapi_health = ProviderHealth(
            provider_id='vapi',
            is_healthy=True,
            last_check=datetime.utcnow(),
            supported_regions=['US', 'CA', 'UK'],
            cost_per_minute=0.02
        )
        provider_manager.providers['vapi'].health = vapi_health
        provider_manager.providers['vapi'].average_quality = 0.9
        
        vonage_health = ProviderHealth(
            provider_id='vonage',
            is_healthy=True,
            last_check=datetime.utcnow(),
            supported_regions=['US', 'EU', 'AU'],
            cost_per_minute=0.03
        )
        provider_manager.providers['vonage'].health = vonage_health
        provider_manager.providers['vonage'].average_quality = 0.8
        
        # Test geographic routing
        provider_manager.selection_strategy = ProviderSelectionStrategy.GEOGRAPHIC
        
        # US region - both providers support it, should select based on health
        context = CallContext(
            destination='+1234567890',
            source='+0987654321',
            tenant_id='test_tenant',
            geographic_region='US'
        )
        
        selected_provider = await provider_manager.get_best_provider(context)
        # Should select VAPI (better health score)
        assert selected_provider == provider_manager.providers['vapi'].adapter
        
        # Test quality-based routing
        provider_manager.selection_strategy = ProviderSelectionStrategy.QUALITY_BASED
        
        selected_provider = await provider_manager.get_best_provider(context)
        # Should select VAPI (higher quality: 0.9 vs 0.8)
        assert selected_provider == provider_manager.providers['vapi'].adapter

    @pytest.mark.asyncio
    async def test_round_robin_selection(self, provider_manager):
        """Test round-robin provider selection"""
        provider_manager = await provider_manager
        provider_manager.selection_strategy = ProviderSelectionStrategy.ROUND_ROBIN
        
        context = CallContext(
            destination='+1234567890',
            source='+0987654321',
            tenant_id='test_tenant'
        )
        
        # First call should select first provider
        selected1 = await provider_manager.get_best_provider(context)
        assert selected1 in [p.adapter for p in provider_manager.providers.values()]
        
        # Second call should select second provider
        selected2 = await provider_manager.get_best_provider(context)
        assert selected2 in [p.adapter for p in provider_manager.providers.values()]
        
        # Third call should cycle back to first provider
        selected3 = await provider_manager.get_best_provider(context)
        assert selected3 == selected1

    @pytest.mark.asyncio
    async def test_provider_switching(self, provider_manager):
        """Test provider switching during active calls"""
        provider_manager = await provider_manager
        # Mock call initiation
        with patch.object(provider_manager.providers['vapi'].adapter, 'dial', return_value='call_123'), \
             patch.object(provider_manager.providers['vonage'].adapter, 'dial', return_value='call_456'), \
             patch.object(provider_manager.providers['vapi'].adapter, 'hangup', return_value=True), \
             patch.object(provider_manager.providers['vonage'].adapter, 'hangup', return_value=True):
            
            # Initiate call with VAPI
            call_id = await provider_manager.dial('+1234567890', '+0987654321')
            assert call_id == 'call_123'
            assert provider_manager.active_calls[call_id] == 'vapi'
            
            # Switch to Vonage
            success = await provider_manager.switch_provider(call_id, 'vonage')
            assert success is True
            assert provider_manager.active_calls[call_id] == 'vonage'

    @pytest.mark.asyncio
    async def test_metrics_recording(self, provider_manager):
        """Test call metrics recording"""
        provider_manager = await provider_manager
        # Mock call tracking
        provider_manager.active_calls['call_123'] = 'vapi'
        
        # Record successful call
        await provider_manager.record_call_success('call_123', duration=60.0, cost=1.20, quality=0.9)
        
        vapi_info = provider_manager.providers['vapi']
        assert vapi_info.success_count == 1
        assert vapi_info.average_cost == 1.20
        assert vapi_info.average_quality == 0.9
        
        # Record failed call
        await provider_manager.record_call_failure('call_123', 'Connection timeout')
        
        assert vapi_info.failure_count == 1
        assert vapi_info.success_count == 1  # Should remain unchanged

    @pytest.mark.asyncio
    async def test_provider_health_monitoring_loop(self, provider_manager):
        """Test the health monitoring background loop"""
        provider_manager = await provider_manager
        # Mock health checks
        with patch.object(provider_manager.providers['vapi'].adapter, 'health_check') as mock_health:
            mock_health.return_value = ProviderHealth(
                provider_id='vapi',
                is_healthy=True,
                last_check=datetime.utcnow()
            )
            
            # Set a very short health check interval for testing
            provider_manager.health_check_interval = 0.01
            
            # Start health monitoring
            health_task = asyncio.create_task(provider_manager._health_monitor_loop())
            
            # Wait a bit for health check
            await asyncio.sleep(0.05)
            
            # Cancel the task
            health_task.cancel()
            try:
                await health_task
            except asyncio.CancelledError:
                pass
            
            # Verify health check was called
            mock_health.assert_called()

    @pytest.mark.asyncio
    async def test_error_handling(self, provider_manager):
        """Test error handling in provider management"""
        provider_manager = await provider_manager
        # Test with no healthy providers
        for provider_info in provider_manager.providers.values():
            provider_info.health.is_healthy = False
        
        context = CallContext(
            destination='+1234567890',
            source='+0987654321',
            tenant_id='test_tenant'
        )
        
        with pytest.raises(Exception, match="No healthy providers available"):
            await provider_manager.get_best_provider(context)
        
        # Test switching to non-existent provider
        provider_manager.active_calls['call_123'] = 'vapi'
        
        # The switch_provider method logs the error but doesn't raise it
        success = await provider_manager.switch_provider('call_123', 'nonexistent')
        assert success is False
        
        # Test switching non-existent call
        success = await provider_manager.switch_provider('nonexistent_call', 'vapi')
        assert success is False

    @pytest.mark.asyncio
    async def test_provider_management_integration(self, provider_manager):
        """Test complete provider management workflow"""
        provider_manager = await provider_manager
        # Mock all adapter methods
        with patch.object(provider_manager.providers['vapi'].adapter, 'dial', return_value='call_123'), \
             patch.object(provider_manager.providers['vapi'].adapter, 'hangup', return_value=True), \
             patch.object(provider_manager.providers['vapi'].adapter, 'get_events', return_value=[]), \
             patch.object(provider_manager.providers['vapi'].adapter, 'get_costs', return_value={'total': 1.20}):
            
            # Complete call workflow
            call_id = await provider_manager.dial('+1234567890', '+0987654321')
            assert call_id == 'call_123'
            
            events = await provider_manager.get_events(call_id)
            assert events == []
            
            costs = await provider_manager.get_costs(call_id)
            assert costs == {'total': 1.20}
            
            success = await provider_manager.hangup(call_id)
            assert success is True
            assert call_id not in provider_manager.active_calls

    @pytest.mark.asyncio
    async def test_provider_priority_and_enabled_status(self, provider_manager):
        """Test provider priority and enabled status handling"""
        provider_manager = await provider_manager
        # Check that only enabled providers are available
        available_providers = [
            info for info in provider_manager.providers.values()
            if info.settings.enabled and info.health.is_healthy
        ]
        assert len(available_providers) == 2
        
        # Test priority-based selection (if implemented)
        # This would require implementing priority-based selection strategy
        context = CallContext(
            destination='+1234567890',
            source='+0987654321',
            tenant_id='test_tenant'
        )
        
        # Should work with any strategy
        provider = await provider_manager.get_best_provider(context)
        assert provider is not None

    @pytest.mark.asyncio
    async def test_provider_manager_configuration(self, provider_config):
        """Test provider manager configuration handling"""
        # Test with invalid configuration
        invalid_config = {'providers': {'invalid': {'type': 'unknown'}}}
        
        manager = EnhancedProviderManager(invalid_config)
        
        # The manager should start but fail to register the invalid provider
        await manager.start()
        assert len(manager.providers) == 0  # No providers should be registered
        await manager.stop()
        
        # Test with valid configuration
        manager = EnhancedProviderManager(provider_config)
        
        with patch('shared.telephony.adapters.vapi.VapiAdapter.connect', return_value=True), \
             patch('shared.telephony.adapters.vonage.VonageAdapter.connect', return_value=True):
            await manager.start()
            assert len(manager.providers) == 3  # All providers are registered
            await manager.stop()


class TestProviderSelectionStrategies:
    """Test individual provider selection strategies"""

    @pytest.fixture
    def mock_providers(self):
        """Create mock providers for testing strategies"""
        providers = []
        
        # Provider 1: High quality, high cost
        provider1 = MagicMock()
        provider1.name = 'high_quality'
        provider1.average_cost = 0.05
        provider1.average_quality = 0.95
        provider1.health.response_time_ms = 50
        provider1.health.error_rate = 0.0
        provider1.success_count = 100
        provider1.failure_count = 0
        provider1.health.supported_regions = ['US', 'CA', 'UK']
        providers.append(provider1)
        
        # Provider 2: Medium quality, medium cost
        provider2 = MagicMock()
        provider2.name = 'medium_quality'
        provider2.average_cost = 0.03
        provider2.average_quality = 0.8
        provider2.health.response_time_ms = 100
        provider2.health.error_rate = 5.0
        provider2.success_count = 80
        provider2.failure_count = 5
        provider2.health.supported_regions = ['US', 'EU']
        providers.append(provider2)
        
        # Provider 3: Low quality, low cost
        provider3 = MagicMock()
        provider3.name = 'low_cost'
        provider3.average_cost = 0.01
        provider3.average_quality = 0.6
        provider3.health.response_time_ms = 200
        provider3.health.error_rate = 10.0
        provider3.success_count = 60
        provider3.failure_count = 10
        provider3.health.supported_regions = ['US']
        providers.append(provider3)
        
        return providers

    def test_health_based_selection(self, mock_providers):
        """Test health-based provider selection"""
        manager = EnhancedProviderManager({})
        
        # Provider 1 should be selected (best health score)
        selected = manager._health_based_select(mock_providers)
        assert selected.name == 'high_quality'

    def test_cost_based_selection(self, mock_providers):
        """Test cost-based provider selection"""
        manager = EnhancedProviderManager({})
        
        context = CallContext(
            destination='+1234567890',
            source='+0987654321',
            tenant_id='test_tenant'
        )
        
        # Low cost preference
        context.cost_preference = "low"
        selected = manager._cost_based_select(mock_providers, context)
        assert selected.name == 'low_cost'
        
        # High cost preference
        context.cost_preference = "high"
        selected = manager._cost_based_select(mock_providers, context)
        assert selected.name == 'high_quality'
        
        # Balanced preference
        context.cost_preference = "balanced"
        selected = manager._cost_based_select(mock_providers, context)
        # Should select based on quality/cost ratio
        # high_quality: 0.95/0.05 = 19, medium_quality: 0.8/0.03 = 26.7, low_cost: 0.6/0.01 = 60
        # So low_cost should be selected as it has the best quality/cost ratio
        assert selected.name == 'low_cost'

    def test_quality_based_selection(self, mock_providers):
        """Test quality-based provider selection"""
        manager = EnhancedProviderManager({})
        
        selected = manager._quality_based_select(mock_providers)
        assert selected.name == 'high_quality'

    def test_geographic_selection(self, mock_providers):
        """Test geographic-based provider selection"""
        manager = EnhancedProviderManager({})
        
        context = CallContext(
            destination='+1234567890',
            source='+0987654321',
            tenant_id='test_tenant',
            geographic_region='UK'
        )
        
        # Only high_quality supports UK
        selected = manager._geographic_select(mock_providers, context)
        assert selected.name == 'high_quality'
        
        # Test fallback when region not supported
        context.geographic_region = 'AU'
        selected = manager._geographic_select(mock_providers, context)
        # Should fall back to health-based selection
        assert selected.name == 'high_quality'

    def test_round_robin_selection(self, mock_providers):
        """Test round-robin provider selection"""
        manager = EnhancedProviderManager({})
        
        # First selection
        selected1 = manager._round_robin_select(mock_providers)
        assert selected1 in mock_providers
        
        # Second selection
        selected2 = manager._round_robin_select(mock_providers)
        assert selected2 in mock_providers
        
        # Third selection
        selected3 = manager._round_robin_select(mock_providers)
        assert selected3 in mock_providers
        
        # Fourth selection should cycle back
        selected4 = manager._round_robin_select(mock_providers)
        assert selected4 == selected1
