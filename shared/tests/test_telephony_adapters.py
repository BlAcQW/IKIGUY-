"""
Tests for Telephony Adapters

This module contains tests for the telephony adapter framework.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from ..telephony.adapters.base import BaseTelephonyAdapter
from ..telephony.adapters.vapi import VapiAdapter
from ..telephony.adapters.vonage import VonageAdapter
from ..telephony.provider_manager import EnhancedProviderManager, ProviderSelectionStrategy
from ..telephony.models import CallContext, ProviderSettings, ProviderHealth
from ..telephony.interfaces import TelephonyEvent


class TestBaseTelephonyAdapter:
    """Test base telephony adapter functionality"""
    
    @pytest.mark.asyncio
    async def test_phone_number_normalization(self):
        """Test phone number normalization"""
        # Create a mock adapter using VapiAdapter instead of abstract base
        settings = ProviderSettings(
            provider_id="test",
            api_key="test_key",
            base_url="https://test.com"
        )
        
        adapter = VapiAdapter(settings)
        
        # Test various phone number formats
        test_cases = [
            ("1234567890", "+11234567890"),  # US 10-digit
            ("11234567890", "+11234567890"),  # US 11-digit
            ("+11234567890", "+11234567890"),  # Already international
            ("0011234567890", "+11234567890"),  # 00 format
            ("+44 20 7946 0958", "+442079460958"),  # UK format
        ]
        
        for input_num, expected in test_cases:
            result = adapter._normalize_phone_number(input_num)
            assert result == expected
    
    @pytest.mark.asyncio
    async def test_telephony_event_creation(self):
        """Test telephony event creation"""
        settings = ProviderSettings(
            provider_id="test",
            api_key="test_key",
            base_url="https://test.com"
        )
        
        adapter = VapiAdapter(settings)
        
        event = adapter._create_telephony_event(
            "test_event",
            "call_123",
            {"test_data": "value"}
        )
        
        assert isinstance(event, TelephonyEvent)
        assert event.event_type == "test_event"
        assert event.call_id == "call_123"
        assert event.provider == "test"
        assert event.data["test_data"] == "value"


class TestVapiAdapter:
    """Test VAPI adapter functionality"""
    
    @pytest.fixture
    def vapi_settings(self):
        """Create VAPI settings"""
        return ProviderSettings(
            provider_id="vapi_test",
            api_key="test_vapi_key",
            base_url="https://api.vapi.ai"
        )
    
    @pytest.fixture
    def vapi_adapter(self, vapi_settings):
        """Create VAPI adapter"""
        return VapiAdapter(vapi_settings)
    
    @pytest.mark.asyncio
    async def test_vapi_connect_disconnect(self, vapi_adapter):
        """Test VAPI connection and disconnection"""
        with patch('httpx.AsyncClient.request') as mock_request:
            mock_response = MagicMock()
            mock_response.json.return_value = {"assistants": []}
            mock_request.return_value = mock_response
            
            # Test connection
            connected = await vapi_adapter.connect()
            assert connected
            assert await vapi_adapter.is_connected()
            
            # Test disconnection
            disconnected = await vapi_adapter.disconnect()
            assert disconnected
            assert not await vapi_adapter.is_connected()
    
    @pytest.mark.asyncio
    async def test_vapi_dial(self, vapi_adapter):
        """Test VAPI call initiation"""
        with patch('httpx.AsyncClient.request') as mock_request:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "id": "vapi_call_123",
                "status": "initiated"
            }
            mock_request.return_value = mock_response
            
            # Connect first
            await vapi_adapter.connect()
            
            # Test dial
            call_id = await vapi_adapter.dial(
                to="+1234567890",
                from_="+0987654321",
                assistant_id="assistant_123",
                phone_number_id="phone_123"
            )
            
            assert call_id is not None
            assert call_id in vapi_adapter._active_calls
    
    @pytest.mark.asyncio
    async def test_vapi_health_check(self, vapi_adapter):
        """Test VAPI health check"""
        with patch.object(vapi_adapter, 'is_connected', return_value=True):
            health = await vapi_adapter.health_check()
            
            assert isinstance(health, ProviderHealth)
            assert health.provider_id == "vapi_test"
            assert health.is_healthy
            assert health.cost_per_minute == 0.02


class TestVonageAdapter:
    """Test Vonage adapter functionality"""
    
    @pytest.fixture
    def vonage_settings(self):
        """Create Vonage settings"""
        return ProviderSettings(
            provider_id="vonage_test",
            api_key="test_vonage_key",
            api_secret="test_vonage_secret",
            base_url="https://api.nexmo.com"
        )
    
    @pytest.fixture
    def vonage_adapter(self, vonage_settings):
        """Create Vonage adapter"""
        return VonageAdapter(vonage_settings)
    
    @pytest.mark.asyncio
    async def test_vonage_connect_disconnect(self, vonage_adapter):
        """Test Vonage connection and disconnection"""
        with patch('httpx.AsyncClient.request') as mock_request:
            mock_response = MagicMock()
            mock_response.json.return_value = {"numbers": []}
            mock_request.return_value = mock_response
            
            # Test connection
            connected = await vonage_adapter.connect()
            assert connected
            assert await vonage_adapter.is_connected()
            
            # Test disconnection
            disconnected = await vonage_adapter.disconnect()
            assert disconnected
            assert not await vonage_adapter.is_connected()
    
    @pytest.mark.asyncio
    async def test_vonage_dial(self, vonage_adapter):
        """Test Vonage call initiation"""
        with patch('httpx.AsyncClient.request') as mock_request:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "status": "0",
                "call-id": "vonage_call_123"
            }
            mock_request.return_value = mock_response
            
            # Connect first
            await vonage_adapter.connect()
            
            # Test dial
            call_id = await vonage_adapter.dial(
                to="+1234567890",
                from_="+0987654321",
                answer_url="https://test.com/answer",
                event_url="https://test.com/events"
            )
            
            assert call_id is not None
            assert call_id in vonage_adapter._active_calls


class TestEnhancedProviderManager:
    """Test enhanced provider manager functionality"""
    
    @pytest.fixture
    def provider_config(self):
        """Create provider configuration"""
        return {
            "providers": {
                "vapi": {
                    "type": "vapi",
                    "api_key": "test_vapi_key",
                    "base_url": "https://api.vapi.ai",
                    "enabled": True,
                    "priority": 8
                },
                "vonage": {
                    "type": "vonage",
                    "api_key": "test_vonage_key",
                    "api_secret": "test_vonage_secret",
                    "base_url": "https://api.nexmo.com",
                    "enabled": True,
                    "priority": 6
                }
            }
        }
    
    @pytest.fixture
    async def provider_manager(self, provider_config):
        """Create provider manager"""
        manager = EnhancedProviderManager(provider_config)
        
        # Mock the adapter creation to avoid actual API calls
        with patch('shared.telephony.adapters.vapi.VapiAdapter.connect', return_value=True), \
             patch('shared.telephony.adapters.vonage.VonageAdapter.connect', return_value=True):
            await manager.start()
            return manager
    
    @pytest.mark.asyncio
    async def test_provider_manager_initialization(self, provider_manager):
        """Test provider manager initialization"""
        provider_manager = await provider_manager
        assert len(provider_manager.providers) == 2
        assert "vapi" in provider_manager.providers
        assert "vonage" in provider_manager.providers
        
        # Check that providers are healthy
        for provider_info in provider_manager.providers.values():
            assert provider_info.settings.enabled
            assert provider_info.health.is_healthy
    
    @pytest.mark.asyncio
    async def test_provider_selection_strategies(self, provider_manager):
        """Test different provider selection strategies"""
        provider_manager = await provider_manager
        context = CallContext(
            destination="+1234567890",
            source="+0987654321",
            tenant_id="test_tenant",
            cost_preference="balanced",
            quality_preference="balanced"
        )
        
        # Test health-based selection
        provider_manager.selection_strategy = ProviderSelectionStrategy.HEALTH_BASED
        provider = await provider_manager.get_best_provider(context)
        assert provider is not None
        
        # Test round-robin selection
        provider_manager.selection_strategy = ProviderSelectionStrategy.ROUND_ROBIN
        provider = await provider_manager.get_best_provider(context)
        assert provider is not None
    
    @pytest.mark.asyncio
    async def test_provider_health_monitoring(self, provider_manager):
        """Test provider health monitoring"""
        provider_manager = await provider_manager
        health_status = await provider_manager.get_all_provider_health()
        
        assert len(health_status) == 2
        for provider_name, health in health_status.items():
            assert isinstance(health, ProviderHealth)
            assert health.provider_id == provider_name
    
    @pytest.mark.asyncio
    async def test_call_lifecycle(self, provider_manager):
        """Test complete call lifecycle"""
        provider_manager = await provider_manager
        # Mock the dial method to avoid actual API calls
        with patch.object(provider_manager.providers["vapi"].adapter, 'dial') as mock_dial:
            mock_dial.return_value = "test_call_123"
            
            # Initiate call
            call_id = await provider_manager.dial(
                to="+1234567890",
                from_="+0987654321",
                tenant_id="test_tenant"
            )
            
            assert call_id == "test_call_123"
            assert call_id in provider_manager.active_calls
            
            # Mock hangup
            with patch.object(provider_manager.providers["vapi"].adapter, 'hangup', return_value=True):
                success = await provider_manager.hangup(call_id)
                assert success
                assert call_id not in provider_manager.active_calls
    
    @pytest.mark.asyncio
    async def test_provider_switching(self, provider_manager):
        """Test provider switching during calls"""
        provider_manager = await provider_manager
        # Mock call initiation
        with patch.object(provider_manager.providers["vapi"].adapter, 'dial') as mock_dial:
            mock_dial.return_value = "test_call_123"
            
            call_id = await provider_manager.dial(
                to="+1234567890",
                from_="+0987654321"
            )
            
            # Mock hangup for old provider and dial for new provider
            with patch.object(provider_manager.providers["vapi"].adapter, 'hangup', return_value=True), \
                 patch.object(provider_manager.providers["vonage"].adapter, 'dial', return_value="test_call_123"):
                
                success = await provider_manager.switch_provider(call_id, "vonage")
                assert success
                assert provider_manager.active_calls[call_id] == "vonage"
    
    @pytest.mark.asyncio
    async def test_metrics_recording(self, provider_manager):
        """Test call metrics recording"""
        provider_manager = await provider_manager
        # Add a test call
        provider_manager.active_calls["test_call_123"] = "vapi"
        
        # Record success
        await provider_manager.record_call_success(
            "test_call_123",
            duration=120.0,
            cost=2.40,
            quality=0.9
        )
        
        provider_info = provider_manager.providers["vapi"]
        assert provider_info.success_count == 1
        assert provider_info.average_cost == 2.40
        assert provider_info.average_quality == 0.9
        
        # Record failure
        await provider_manager.record_call_failure(
            "test_call_123",
            "Connection timeout"
        )
        
        assert provider_info.failure_count == 1


class TestTelephonyAdapterCompatibility:
    """Test that all adapters implement the required interface"""
    
    @pytest.mark.parametrize("adapter_class", [
        VapiAdapter,
        VonageAdapter,
        # TelnyxAdapter,  # Not fully implemented yet
        # SipAdapter,     # Not fully implemented yet
    ])
    def test_adapter_interface_compliance(self, adapter_class):
        """Test that adapters implement required interface"""
        settings = ProviderSettings(
            provider_id="test",
            api_key="test_key",
            base_url="https://test.com"
        )
        
        adapter = adapter_class(settings)
        
        # Check required methods exist
        required_methods = [
            'connect', 'disconnect', 'is_connected',
            'dial', 'hangup', 'get_events', 'get_costs',
            'health_check'
        ]
        
        for method in required_methods:
            assert hasattr(adapter, method), f"Missing method: {method}"
    
    @pytest.mark.asyncio
    async def test_adapter_context_manager(self):
        """Test adapter context manager functionality"""
        settings = ProviderSettings(
            provider_id="test",
            api_key="test_key",
            base_url="https://test.com"
        )
        
        with patch('shared.telephony.adapters.vapi.VapiAdapter.connect', return_value=True), \
             patch('shared.telephony.adapters.vapi.VapiAdapter.disconnect', return_value=True):
            
            async with VapiAdapter(settings) as adapter:
                # Mock the _connected attribute to True since connect() was called
                adapter._connected = True
                assert await adapter.is_connected()


if __name__ == "__main__":
    pytest.main([__file__])
