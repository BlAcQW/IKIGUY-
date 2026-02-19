"""
Tests for Advanced Provider Manager

This module contains comprehensive tests for the advanced provider manager implementation.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from apps.shared.telephony.advanced_provider_manager import (
    AdvancedProviderManager,
    RoutingStrategy,
    ProviderQuality,
    ProviderMetrics,
    RoutingDecision
)
from apps.shared.telephony.models import CallContext, ProviderSettings
from apps.shared.telephony.interfaces import TelephonyPort


class MockProvider(TelephonyPort):
    """Mock telephony provider for testing"""
    
    def __init__(self, provider_id: str, cost_per_minute: float = 0.01, regions: list = None):
        self.provider_id = provider_id
        self.cost_per_minute = cost_per_minute
        self.regions = regions or ["US", "CA"]
        self.connected = True
        self.healthy = True
    
    async def dial(self, to: str, from_: str, **kwargs) -> str:
        return f"call_{self.provider_id}_{to}"
    
    async def hangup(self, call_id: str) -> bool:
        return True
    
    async def get_events(self, call_id: str):
        return []
    
    async def get_costs(self, call_id: str):
        return {"total_cost": self.cost_per_minute}
    
    async def connect(self) -> bool:
        return self.connected
    
    async def disconnect(self) -> bool:
        return True
    
    async def is_connected(self) -> bool:
        return self.connected
    
    async def health_check(self):
        from apps.shared.telephony.models import ProviderHealth
        return ProviderHealth(
            provider_id=self.provider_id,
            is_healthy=self.healthy,
            last_check=datetime.utcnow(),
            response_time_ms=100,
            cost_per_minute=self.cost_per_minute,
            supported_regions=self.regions,
            features=["voice_calls"]
        )


class TestAdvancedProviderManager:
    """Test cases for advanced provider manager"""
    
    @pytest.fixture
    def config(self) -> Dict[str, Any]:
        """Create configuration for testing"""
        return {
            'health_check_interval': 5,  # Short interval for testing
            'metrics_window': 300,  # 5 minutes for testing
            'min_success_rate': 0.95,
            'max_response_time': 2000,
            'cost_weight': 0.3,
            'quality_weight': 0.4,
            'geographic_weight': 0.3
        }
    
    @pytest.fixture
    def provider_manager(self, config) -> AdvancedProviderManager:
        """Create provider manager instance for testing"""
        return AdvancedProviderManager(config)
    
    @pytest.fixture
    def mock_providers(self):
        """Create mock providers for testing"""
        providers = {
            'vapi': MockProvider('vapi', cost_per_minute=0.02, regions=["US", "CA", "GB"]),
            'vonage': MockProvider('vonage', cost_per_minute=0.015, regions=["US", "CA"]),
            'sip': MockProvider('sip', cost_per_minute=0.005, regions=["US", "CA", "GB", "AU"])
        }
        return providers
    
    @pytest.fixture
    def call_context(self) -> CallContext:
        """Create call context for testing"""
        return CallContext(
            destination="+1234567890",
            source="+0987654321",
            tenant_id="test_tenant",
            campaign_id="test_campaign",
            cost_preference="balanced",
            quality_preference="balanced",
            geographic_region="global",
            metadata={"test": "data"}
        )
    
    @pytest.mark.asyncio
    async def test_provider_manager_initialization(self, provider_manager):
        """Test provider manager initialization"""
        assert provider_manager.providers == {}
        assert provider_manager.health_status == {}
        assert provider_manager.metrics == {}
        assert provider_manager.active_calls == {}
        assert len(provider_manager.call_history) == 0
    
    @pytest.mark.asyncio
    async def test_register_provider(self, provider_manager, mock_providers):
        """Test provider registration"""
        provider = mock_providers['vapi']
        
        await provider_manager.register_provider('vapi', provider)
        
        assert 'vapi' in provider_manager.providers
        assert provider_manager.providers['vapi'] == provider
        assert provider_manager.health_status['vapi'] is True
        assert 'vapi' in provider_manager.metrics
        
        metrics = provider_manager.metrics['vapi']
        assert metrics.provider_id == 'vapi'
        assert metrics.success_rate == 1.0
        assert metrics.cost_per_minute == 0.0
        assert metrics.call_count == 0
    
    @pytest.mark.asyncio
    async def test_unregister_provider(self, provider_manager, mock_providers):
        """Test provider unregistration"""
        provider = mock_providers['vapi']
        await provider_manager.register_provider('vapi', provider)
        
        await provider_manager.unregister_provider('vapi')
        
        assert 'vapi' not in provider_manager.providers
        assert 'vapi' not in provider_manager.health_status
        assert 'vapi' not in provider_manager.metrics
    
    @pytest.mark.asyncio
    async def test_get_best_provider_cost_optimized(self, provider_manager, mock_providers, call_context):
        """Test cost-optimized provider selection"""
        # Register providers
        for name, provider in mock_providers.items():
            await provider_manager.register_provider(name, provider)
        
        # Update metrics to simulate different costs
        provider_manager.metrics['vapi'].cost_per_minute = 0.02
        provider_manager.metrics['vonage'].cost_per_minute = 0.015
        provider_manager.metrics['sip'].cost_per_minute = 0.005
        
        # Set cost preference to minimal
        call_context.cost_preference = 'minimal'
        call_context.quality_preference = 'minimal'
        
        decision = await provider_manager.get_best_provider(call_context)
        
        assert decision.strategy == RoutingStrategy.COST_OPTIMIZED
        assert decision.provider_id == 'sip'  # Should select lowest cost
        assert decision.confidence > 0.5
        assert "Cost-optimized routing" in decision.reasoning
    
    @pytest.mark.asyncio
    async def test_get_best_provider_quality_optimized(self, provider_manager, mock_providers, call_context):
        """Test quality-optimized provider selection"""
        # Register providers
        for name, provider in mock_providers.items():
            await provider_manager.register_provider(name, provider)
        
        # Update metrics to simulate different quality levels
        provider_manager.metrics['vapi'].success_rate = 0.99
        provider_manager.metrics['vapi'].average_response_time = 100
        provider_manager.metrics['vonage'].success_rate = 0.97
        provider_manager.metrics['vonage'].average_response_time = 200
        provider_manager.metrics['sip'].success_rate = 0.95
        provider_manager.metrics['sip'].average_response_time = 500
        
        # Set quality preference to maximum
        call_context.quality_preference = 'maximum'
        call_context.cost_preference = 'maximum'
        
        decision = await provider_manager.get_best_provider(call_context)
        
        assert decision.strategy == RoutingStrategy.QUALITY_OPTIMIZED
        assert decision.provider_id == 'vapi'  # Should select highest quality
        assert decision.confidence > 0.5
        assert "Quality-optimized routing" in decision.reasoning
    
    @pytest.mark.asyncio
    async def test_get_best_provider_geographic(self, provider_manager, mock_providers, call_context):
        """Test geographic provider selection"""
        # Register providers
        for name, provider in mock_providers.items():
            await provider_manager.register_provider(name, provider)
        
        # Update geographic coverage
        provider_manager.metrics['vapi'].geographic_coverage = ["US", "CA", "GB"]
        provider_manager.metrics['vonage'].geographic_coverage = ["US", "CA"]
        provider_manager.metrics['sip'].geographic_coverage = ["US", "CA", "GB", "AU"]
        
        # Set specific geographic region
        call_context.geographic_region = "AU"
        
        decision = await provider_manager.get_best_provider(call_context)
        
        assert decision.strategy == RoutingStrategy.GEOGRAPHIC
        assert decision.provider_id == 'sip'  # Should select provider supporting AU
        assert decision.confidence > 0.5
        assert "Geographic routing" in decision.reasoning
        assert "Supports region: AU" in decision.reasoning
    
    @pytest.mark.asyncio
    async def test_get_best_provider_balanced(self, provider_manager, mock_providers, call_context):
        """Test balanced provider selection"""
        # Register providers
        for name, provider in mock_providers.items():
            await provider_manager.register_provider(name, provider)
        
        # Update metrics for balanced selection
        provider_manager.metrics['vapi'].success_rate = 0.98
        provider_manager.metrics['vapi'].cost_per_minute = 0.02
        provider_manager.metrics['vonage'].success_rate = 0.96
        provider_manager.metrics['vonage'].cost_per_minute = 0.015
        provider_manager.metrics['sip'].success_rate = 0.94
        provider_manager.metrics['sip'].cost_per_minute = 0.005
        
        # Use balanced preferences
        call_context.cost_preference = 'balanced'
        call_context.quality_preference = 'balanced'
        
        decision = await provider_manager.get_best_provider(call_context)
        
        assert decision.strategy == RoutingStrategy.BALANCED
        assert decision.confidence > 0.5
        assert "Balanced routing" in decision.reasoning
    
    @pytest.mark.asyncio
    async def test_get_best_provider_no_healthy_providers(self, provider_manager, call_context):
        """Test provider selection when no healthy providers are available"""
        with pytest.raises(ValueError, match="No healthy providers available"):
            await provider_manager.get_best_provider(call_context)
    
    @pytest.mark.asyncio
    async def test_get_best_provider_fallback(self, provider_manager, mock_providers, call_context):
        """Test provider selection fallback when calculation fails"""
        # Register providers
        for name, provider in mock_providers.items():
            await provider_manager.register_provider(name, provider)
        
        # Mock calculation failure
        with patch.object(provider_manager, '_calculate_provider_scores', side_effect=Exception("Calculation failed")):
            decision = await provider_manager.get_best_provider(call_context)
            
            assert decision.strategy == RoutingStrategy.FAILOVER
            assert decision.provider_id in mock_providers.keys()
            assert "Fallback due to error" in decision.reasoning
    
    @pytest.mark.asyncio
    async def test_switch_provider_success(self, provider_manager, mock_providers):
        """Test successful provider switching"""
        # Register providers
        for name, provider in mock_providers.items():
            await provider_manager.register_provider(name, provider)
        
        # Add active call
        call_id = "test_call_123"
        provider_manager.active_calls[call_id] = {
            'provider_id': 'vapi',
            'start_time': datetime.utcnow(),
            'status': 'active'
        }
        
        # Switch provider
        success = await provider_manager.switch_provider(call_id, 'vonage', "Quality issues")
        
        assert success is True
        assert provider_manager.active_calls[call_id]['provider_id'] == 'vonage'
        assert provider_manager.active_calls[call_id]['provider_switches'] == 1
        assert len(provider_manager.active_calls[call_id]['switch_history']) == 1
        
        switch_record = provider_manager.active_calls[call_id]['switch_history'][0]
        assert switch_record['from_provider'] == 'vapi'
        assert switch_record['to_provider'] == 'vonage'
        assert switch_record['reason'] == "Quality issues"
    
    @pytest.mark.asyncio
    async def test_switch_provider_call_not_found(self, provider_manager, mock_providers):
        """Test provider switching with non-existent call"""
        # Register providers
        for name, provider in mock_providers.items():
            await provider_manager.register_provider(name, provider)
        
        success = await provider_manager.switch_provider("non_existent_call", 'vonage')
        assert success is False
    
    @pytest.mark.asyncio
    async def test_switch_provider_provider_not_found(self, provider_manager, mock_providers):
        """Test provider switching with non-existent provider"""
        # Register providers
        for name, provider in mock_providers.items():
            await provider_manager.register_provider(name, provider)
        
        # Add active call
        call_id = "test_call_123"
        provider_manager.active_calls[call_id] = {
            'provider_id': 'vapi',
            'start_time': datetime.utcnow(),
            'status': 'active'
        }
        
        success = await provider_manager.switch_provider(call_id, 'non_existent_provider')
        assert success is False
    
    @pytest.mark.asyncio
    async def test_get_provider_health(self, provider_manager, mock_providers):
        """Test provider health retrieval"""
        # Register provider
        provider = mock_providers['vapi']
        await provider_manager.register_provider('vapi', provider)
        
        # Update metrics
        provider_manager.metrics['vapi'].success_rate = 0.98
        provider_manager.metrics['vapi'].average_response_time = 150
        provider_manager.metrics['vapi'].error_rate = 0.02
        provider_manager.metrics['vapi'].uptime_percentage = 99.5
        provider_manager.metrics['vapi'].call_count = 100
        provider_manager.metrics['vapi'].total_duration = 3600.0
        
        health_data = await provider_manager.get_provider_health('vapi')
        
        assert health_data['provider_id'] == 'vapi'
        assert health_data['is_healthy'] is True
        assert 'response_time_ms' in health_data
        assert 'cost_per_minute' in health_data
        assert 'supported_regions' in health_data
        assert 'features' in health_data
        assert 'metrics' in health_data
        
        metrics = health_data['metrics']
        assert metrics['success_rate'] == 0.98
        assert metrics['average_response_time'] == 150
        assert metrics['error_rate'] == 0.02
        assert metrics['uptime_percentage'] == 99.5
        assert metrics['call_count'] == 100
        assert metrics['total_duration'] == 3600.0
    
    @pytest.mark.asyncio
    async def test_get_provider_health_not_found(self, provider_manager):
        """Test provider health retrieval for non-existent provider"""
        health_data = await provider_manager.get_provider_health('non_existent')
        assert 'error' in health_data
        assert health_data['error'] == 'Provider not found'
    
    @pytest.mark.asyncio
    async def test_get_routing_analytics(self, provider_manager, mock_providers):
        """Test routing analytics retrieval"""
        # Register providers
        for name, provider in mock_providers.items():
            await provider_manager.register_provider(name, provider)
        
        # Add some call history
        provider_manager.call_history.extend([
            {
                'call_id': 'call_1',
                'provider_id': 'vapi',
                'status': 'completed',
                'duration': 120.0,
                'response_time': 100,
                'start_time': datetime.utcnow() - timedelta(minutes=5),
                'end_time': datetime.utcnow() - timedelta(minutes=3),
                'routing_strategy': 'cost_optimized',
                'provider_switches': 0
            },
            {
                'call_id': 'call_2',
                'provider_id': 'vonage',
                'status': 'completed',
                'duration': 180.0,
                'response_time': 150,
                'start_time': datetime.utcnow() - timedelta(minutes=10),
                'end_time': datetime.utcnow() - timedelta(minutes=7),
                'routing_strategy': 'quality_optimized',
                'provider_switches': 1
            },
            {
                'call_id': 'call_3',
                'provider_id': 'sip',
                'status': 'failed',
                'duration': 30.0,
                'response_time': 200,
                'start_time': datetime.utcnow() - timedelta(minutes=15),
                'end_time': datetime.utcnow() - timedelta(minutes=14, seconds=30),
                'routing_strategy': 'geographic',
                'provider_switches': 0
            }
        ])
        
        # Add active calls
        provider_manager.active_calls['active_call_1'] = {'provider_id': 'vapi'}
        provider_manager.active_calls['active_call_2'] = {'provider_id': 'vonage'}
        
        analytics = await provider_manager.get_routing_analytics()
        
        assert analytics['total_calls'] == 3
        assert analytics['active_calls'] == 2
        assert analytics['switch_events'] == 1
        assert analytics['average_call_duration'] == 110.0  # (120 + 180 + 30) / 3
        
        # Check routing decisions
        assert analytics['routing_decisions']['cost_optimized'] == 1
        assert analytics['routing_decisions']['quality_optimized'] == 1
        assert analytics['routing_decisions']['geographic'] == 1
        
        # Check success rates
        assert analytics['success_rate_by_provider']['vapi'] == 1.0  # 1/1 completed
        assert analytics['success_rate_by_provider']['vonage'] == 1.0  # 1/1 completed
        assert analytics['success_rate_by_provider']['sip'] == 0.0  # 0/1 completed
    
    @pytest.mark.asyncio
    async def test_record_call_result(self, provider_manager, mock_providers):
        """Test call result recording"""
        # Register provider
        provider = mock_providers['vapi']
        await provider_manager.register_provider('vapi', provider)
        
        # Record call result
        provider_manager.record_call_result(
            call_id='test_call_123',
            provider_id='vapi',
            status='completed',
            duration=120.0,
            response_time=100.0
        )
        
        # Check call history
        assert len(provider_manager.call_history) == 1
        call_record = provider_manager.call_history[0]
        assert call_record['call_id'] == 'test_call_123'
        assert call_record['provider_id'] == 'vapi'
        assert call_record['status'] == 'completed'
        assert call_record['duration'] == 120.0
        assert call_record['response_time'] == 100.0
        
        # Check metrics update
        metrics = provider_manager.metrics['vapi']
        assert metrics.call_count == 1
        assert metrics.total_duration == 120.0
    
    @pytest.mark.asyncio
    async def test_calculate_quality_level(self, provider_manager):
        """Test quality level calculation"""
        # Test excellent quality
        metrics = ProviderMetrics(
            provider_id='test',
            success_rate=0.99,
            average_response_time=400,
            cost_per_minute=0.01,
            error_rate=0.01,
            uptime_percentage=99.9,
            last_updated=datetime.utcnow(),
            call_count=100,
            total_duration=3600.0,
            geographic_coverage=[],
            supported_features=[]
        )
        quality = provider_manager._calculate_quality_level(metrics)
        assert quality == ProviderQuality.EXCELLENT
        
        # Test good quality
        metrics.success_rate = 0.96
        metrics.average_response_time = 800
        quality = provider_manager._calculate_quality_level(metrics)
        assert quality == ProviderQuality.GOOD
        
        # Test fair quality
        metrics.success_rate = 0.92
        metrics.average_response_time = 1500
        quality = provider_manager._calculate_quality_level(metrics)
        assert quality == ProviderQuality.FAIR
        
        # Test poor quality
        metrics.success_rate = 0.85
        metrics.average_response_time = 2500
        quality = provider_manager._calculate_quality_level(metrics)
        assert quality == ProviderQuality.POOR
    
    @pytest.mark.asyncio
    async def test_determine_routing_strategy(self, provider_manager, call_context):
        """Test routing strategy determination"""
        # Test cost optimized
        call_context.cost_preference = 'minimal'
        call_context.quality_preference = 'minimal'
        strategy = provider_manager._determine_routing_strategy(call_context)
        assert strategy == RoutingStrategy.COST_OPTIMIZED
        
        # Test quality optimized
        call_context.cost_preference = 'maximum'
        call_context.quality_preference = 'maximum'
        strategy = provider_manager._determine_routing_strategy(call_context)
        assert strategy == RoutingStrategy.QUALITY_OPTIMIZED
        
        # Test geographic
        call_context.geographic_region = 'AU'
        strategy = provider_manager._determine_routing_strategy(call_context)
        assert strategy == RoutingStrategy.GEOGRAPHIC
        
        # Test balanced
        call_context.cost_preference = 'balanced'
        call_context.quality_preference = 'balanced'
        call_context.geographic_region = 'global'
        strategy = provider_manager._determine_routing_strategy(call_context)
        assert strategy == RoutingStrategy.BALANCED
    
    @pytest.mark.asyncio
    async def test_start_and_stop(self, provider_manager):
        """Test provider manager start and stop"""
        # Start manager
        await provider_manager.start()
        assert provider_manager._health_check_task is not None
        assert provider_manager._metrics_update_task is not None
        
        # Stop manager
        await provider_manager.stop()
        # Give tasks time to cancel
        await asyncio.sleep(0.1)
        assert provider_manager._health_check_task.done()
        assert provider_manager._metrics_update_task.done()


class TestProviderMetrics:
    """Test cases for ProviderMetrics dataclass"""
    
    def test_provider_metrics_creation(self):
        """Test ProviderMetrics creation"""
        metrics = ProviderMetrics(
            provider_id='test_provider',
            success_rate=0.98,
            average_response_time=150.0,
            cost_per_minute=0.015,
            error_rate=0.02,
            uptime_percentage=99.5,
            last_updated=datetime.utcnow(),
            call_count=100,
            total_duration=3600.0,
            geographic_coverage=['US', 'CA'],
            supported_features=['voice_calls', 'sms']
        )
        
        assert metrics.provider_id == 'test_provider'
        assert metrics.success_rate == 0.98
        assert metrics.average_response_time == 150.0
        assert metrics.cost_per_minute == 0.015
        assert metrics.error_rate == 0.02
        assert metrics.uptime_percentage == 99.5
        assert metrics.call_count == 100
        assert metrics.total_duration == 3600.0
        assert metrics.geographic_coverage == ['US', 'CA']
        assert metrics.supported_features == ['voice_calls', 'sms']


class TestRoutingDecision:
    """Test cases for RoutingDecision dataclass"""
    
    def test_routing_decision_creation(self):
        """Test RoutingDecision creation"""
        decision = RoutingDecision(
            provider_id='vapi',
            strategy=RoutingStrategy.QUALITY_OPTIMIZED,
            confidence=0.95,
            reasoning='Quality-optimized routing selected vapi; Success rate: 98.0%; Response time: 100ms',
            estimated_cost=0.02,
            estimated_quality=ProviderQuality.EXCELLENT
        )
        
        assert decision.provider_id == 'vapi'
        assert decision.strategy == RoutingStrategy.QUALITY_OPTIMIZED
        assert decision.confidence == 0.95
        assert 'Quality-optimized routing' in decision.reasoning
        assert decision.estimated_cost == 0.02
        assert decision.estimated_quality == ProviderQuality.EXCELLENT


if __name__ == "__main__":
    pytest.main([__file__])
