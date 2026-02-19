"""
Integration Tests for Provider Switching

This module contains comprehensive integration tests for provider switching,
routing strategies, failover mechanisms, and performance optimization.
"""

import pytest
import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List

from ..telephony.adapters.azure_speech import AzureSpeechAdapter
from ..telephony.adapters.google_speech import GoogleSpeechAdapter
from ..telephony.adapters.openai_whisper import WhisperAdapter
from ..telephony.adapters.abena_ai import AbenaAITelephonyAdapter
from ..telephony.advanced_provider_manager import AdvancedProviderManager
from ..telephony.models import CallContext, ProviderSettings, ProviderDecision


class TestProviderSwitchingIntegration:
    """Integration tests for provider switching functionality"""
    
    @pytest.fixture
    def provider_settings(self):
        """Create settings for all providers"""
        return {
            "azure_speech": ProviderSettings(
                provider_id="azure_speech",
                api_key="test_azure_key",
                base_url="https://eastus.api.cognitive.microsoft.com",
                custom_settings={
                    "subscription_key": "test_azure_key",
                    "region": "eastus",
                    "timeout": 30
                }
            ),
            "google_speech": ProviderSettings(
                provider_id="google_speech",
                api_key="test_google_key",
                base_url="https://speech.googleapis.com",
                custom_settings={
                    "project_id": "test_project",
                    "api_key": "test_google_key",
                    "region": "us-central1",
                    "timeout": 30
                }
            ),
            "openai_whisper": ProviderSettings(
                provider_id="openai_whisper",
                api_key="test_openai_key",
                base_url="https://api.openai.com/v1",
                custom_settings={
                    "api_key": "test_openai_key",
                    "model": "whisper-1",
                    "timeout": 30
                }
            ),
            "abena_ai": ProviderSettings(
                provider_id="abena_ai",
                api_key="test_abena_key",
                base_url="https://api.abena.mobobi.com",
                custom_settings={
                    "api_key": "test_abena_key",
                    "base_url": "https://api.abena.mobobi.com",
                    "timeout": 30
                }
            )
        }
    
    @pytest.fixture
    def provider_adapters(self, provider_settings):
        """Create all provider adapters"""
        return {
            "azure_speech": AzureSpeechAdapter(provider_settings["azure_speech"]),
            "google_speech": GoogleSpeechAdapter(provider_settings["google_speech"]),
            "openai_whisper": WhisperAdapter(provider_settings["openai_whisper"]),
            "abena_ai": AbenaAITelephonyAdapter(provider_settings["abena_ai"])
        }
    
    @pytest.fixture
    def provider_manager_config(self, provider_adapters):
        """Create provider manager configuration"""
        return {
            "providers": provider_adapters,
            "routing_strategies": {
                "quality_optimized": {
                    "priority_order": ["azure_speech", "google_speech", "openai_whisper", "abena_ai"],
                    "quality_threshold": 0.8
                },
                "cost_optimized": {
                    "priority_order": ["openai_whisper", "abena_ai", "google_speech", "azure_speech"],
                    "cost_threshold": 0.02
                },
                "geographic": {
                    "ghanaian_languages": ["tw", "en-GH", "ee", "ga", "dag"],
                    "ghanaian_priority": ["abena_ai", "openai_whisper", "azure_speech"],
                    "global_priority": ["azure_speech", "google_speech", "openai_whisper"]
                }
            },
            "health_check_interval": 30,
            "max_retries": 3,
            "fallback_providers": {
                "azure_speech": "google_speech",
                "google_speech": "openai_whisper",
                "openai_whisper": "abena_ai",
                "abena_ai": "azure_speech"
            }
        }
    
    @pytest.fixture
    async def provider_manager(self, provider_manager_config):
        """Create and start provider manager"""
        manager = AdvancedProviderManager(provider_manager_config)
        await manager.start()
        yield manager
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_quality_optimized_routing(self, provider_manager):
        """Test quality-optimized provider routing"""
        # Test with English language
        decision = await provider_manager.select_provider("en-US", "quality_optimized")
        assert decision.provider_id == "azure_speech"
        assert decision.strategy == "quality_optimized"
        assert decision.confidence > 0.8
        
        # Test with Spanish language
        decision = await provider_manager.select_provider("es-ES", "quality_optimized")
        assert decision.provider_id in ["azure_speech", "google_speech"]
        assert decision.strategy == "quality_optimized"
    
    @pytest.mark.asyncio
    async def test_cost_optimized_routing(self, provider_manager):
        """Test cost-optimized provider routing"""
        # Test with English language
        decision = await provider_manager.select_provider("en-US", "cost_optimized")
        assert decision.provider_id == "openai_whisper"
        assert decision.strategy == "cost_optimized"
        assert decision.cost_per_minute <= 0.02
        
        # Test with Spanish language
        decision = await provider_manager.select_provider("es-ES", "cost_optimized")
        assert decision.provider_id in ["openai_whisper", "abena_ai"]
        assert decision.strategy == "cost_optimized"
    
    @pytest.mark.asyncio
    async def test_geographic_routing(self, provider_manager):
        """Test geographic provider routing"""
        # Test Ghanaian languages
        ghanaian_languages = ["tw", "en-GH", "ee", "ga", "dag"]
        for language in ghanaian_languages:
            decision = await provider_manager.select_provider(language, "geographic")
            assert decision.provider_id in ["abena_ai", "openai_whisper", "azure_speech"]
            assert decision.strategy == "geographic"
        
        # Test global languages
        global_languages = ["en-US", "es-ES", "fr-FR", "de-DE", "it-IT"]
        for language in global_languages:
            decision = await provider_manager.select_provider(language, "geographic")
            assert decision.provider_id in ["azure_speech", "google_speech", "openai_whisper"]
            assert decision.strategy == "geographic"
    
    @pytest.mark.asyncio
    async def test_provider_failover(self, provider_manager):
        """Test provider failover mechanism"""
        # Mock Azure provider failure
        with patch.object(provider_manager.providers["azure_speech"], 'is_connected', return_value=False):
            # Test failover to Google
            decision = await provider_manager.select_provider("en-US", "quality_optimized")
            assert decision.provider_id == "google_speech"
            assert decision.fallback_reason == "azure_speech_unavailable"
        
        # Mock multiple provider failures
        with patch.object(provider_manager.providers["azure_speech"], 'is_connected', return_value=False), \
             patch.object(provider_manager.providers["google_speech"], 'is_connected', return_value=False):
            # Test failover to Whisper
            decision = await provider_manager.select_provider("en-US", "quality_optimized")
            assert decision.provider_id == "openai_whisper"
            assert decision.fallback_reason == "multiple_providers_unavailable"
    
    @pytest.mark.asyncio
    async def test_language_specific_routing(self, provider_manager):
        """Test language-specific provider routing"""
        # Test Ghanaian language routing
        decision = await provider_manager.select_provider("tw", "geographic")
        assert decision.provider_id == "abena_ai"
        
        # Test English routing
        decision = await provider_manager.select_provider("en-US", "quality_optimized")
        assert decision.provider_id == "azure_speech"
        
        # Test Spanish routing
        decision = await provider_manager.select_provider("es-ES", "quality_optimized")
        assert decision.provider_id in ["azure_speech", "google_speech"]
    
    @pytest.mark.asyncio
    async def test_provider_health_monitoring(self, provider_manager):
        """Test provider health monitoring"""
        # Mock health check
        with patch.object(provider_manager, '_check_provider_health') as mock_health:
            mock_health.return_value = {
                "azure_speech": True,
                "google_speech": False,
                "openai_whisper": True,
                "abena_ai": True
            }
            
            # Test routing with health status
            decision = await provider_manager.select_provider("en-US", "quality_optimized")
            assert decision.provider_id == "azure_speech"  # Should skip Google due to health issue
    
    @pytest.mark.asyncio
    async def test_cost_tracking_and_optimization(self, provider_manager):
        """Test cost tracking and optimization"""
        # Mock cost tracking
        provider_manager.cost_tracker = {
            "azure_speech": {"total_cost": 10.0, "minutes": 400},
            "google_speech": {"total_cost": 8.0, "minutes": 400},
            "openai_whisper": {"total_cost": 2.0, "minutes": 400},
            "abena_ai": {"total_cost": 5.0, "minutes": 400}
        }
        
        # Test cost-optimized routing
        decision = await provider_manager.select_provider("en-US", "cost_optimized")
        assert decision.provider_id == "openai_whisper"  # Lowest cost per minute
        
        # Test budget limit enforcement
        provider_manager.monthly_budget = 5.0
        decision = await provider_manager.select_provider("en-US", "cost_optimized")
        assert decision.provider_id in ["openai_whisper", "abena_ai"]  # Within budget
    
    @pytest.mark.asyncio
    async def test_performance_optimization(self, provider_manager):
        """Test performance optimization"""
        # Mock performance metrics
        provider_manager.performance_metrics = {
            "azure_speech": {"avg_response_time": 1.2, "success_rate": 0.98},
            "google_speech": {"avg_response_time": 1.5, "success_rate": 0.95},
            "openai_whisper": {"avg_response_time": 2.0, "success_rate": 0.92},
            "abena_ai": {"avg_response_time": 1.8, "success_rate": 0.94}
        }
        
        # Test performance-optimized routing
        decision = await provider_manager.select_provider("en-US", "quality_optimized")
        assert decision.provider_id == "azure_speech"  # Best performance metrics
    
    @pytest.mark.asyncio
    async def test_concurrent_provider_selection(self, provider_manager):
        """Test concurrent provider selection"""
        # Test multiple concurrent requests
        tasks = []
        for i in range(10):
            task = provider_manager.select_provider("en-US", "quality_optimized")
            tasks.append(task)
        
        decisions = await asyncio.gather(*tasks)
        
        # Verify all decisions are valid
        for decision in decisions:
            assert decision.provider_id in provider_manager.providers.keys()
            assert decision.strategy == "quality_optimized"
    
    @pytest.mark.asyncio
    async def test_provider_switching_during_call(self, provider_manager):
        """Test provider switching during an active call"""
        # Start call with Azure
        context = CallContext(language="en-US")
        call_id = await provider_manager.providers["azure_speech"].dial("+1234567890", "+0987654321", context)
        
        # Mock Azure failure during call
        with patch.object(provider_manager.providers["azure_speech"], 'send_audio', side_effect=Exception("Azure failed")):
            # Attempt to switch provider during call
            new_provider = await provider_manager.switch_provider_during_call(call_id, "google_speech")
            assert new_provider == "google_speech"
            
            # Verify call transferred to new provider
            assert call_id in provider_manager.providers["google_speech"]._calls
    
    @pytest.mark.asyncio
    async def test_load_balancing(self, provider_manager):
        """Test load balancing across providers"""
        # Mock current load
        provider_manager.current_load = {
            "azure_speech": 0.8,  # 80% load
            "google_speech": 0.3,  # 30% load
            "openai_whisper": 0.5,  # 50% load
            "abena_ai": 0.2  # 20% load
        }
        
        # Test load-balanced routing
        decision = await provider_manager.select_provider("en-US", "load_balanced")
        assert decision.provider_id == "abena_ai"  # Lowest load
    
    @pytest.mark.asyncio
    async def test_quality_degradation_handling(self, provider_manager):
        """Test handling of quality degradation"""
        # Mock quality degradation
        provider_manager.quality_metrics = {
            "azure_speech": {"accuracy": 0.95, "latency": 1.2},
            "google_speech": {"accuracy": 0.92, "latency": 1.5},
            "openai_whisper": {"accuracy": 0.88, "latency": 2.0},
            "abena_ai": {"accuracy": 0.90, "latency": 1.8}
        }
        
        # Test quality threshold enforcement
        decision = await provider_manager.select_provider("en-US", "quality_optimized")
        assert decision.provider_id in ["azure_speech", "google_speech"]  # Above quality threshold
    
    @pytest.mark.asyncio
    async def test_emergency_fallback(self, provider_manager):
        """Test emergency fallback mechanisms"""
        # Mock all primary providers failing
        with patch.object(provider_manager.providers["azure_speech"], 'is_connected', return_value=False), \
             patch.object(provider_manager.providers["google_speech"], 'is_connected', return_value=False), \
             patch.object(provider_manager.providers["openai_whisper"], 'is_connected', return_value=False):
            
            # Test emergency fallback to Abena AI
            decision = await provider_manager.select_provider("en-US", "quality_optimized")
            assert decision.provider_id == "abena_ai"
            assert decision.emergency_fallback == True
    
    @pytest.mark.asyncio
    async def test_provider_metrics_collection(self, provider_manager):
        """Test provider metrics collection"""
        # Mock metrics collection
        with patch.object(provider_manager, '_collect_provider_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "azure_speech": {
                    "response_time": 1.2,
                    "success_rate": 0.98,
                    "cost_per_minute": 0.024,
                    "language_support": 100
                },
                "google_speech": {
                    "response_time": 1.5,
                    "success_rate": 0.95,
                    "cost_per_minute": 0.022,
                    "language_support": 120
                }
            }
            
            # Test metrics-based routing
            decision = await provider_manager.select_provider("en-US", "quality_optimized")
            assert decision.provider_id == "azure_speech"  # Better metrics
    
    @pytest.mark.asyncio
    async def test_dynamic_routing_updates(self, provider_manager):
        """Test dynamic routing strategy updates"""
        # Update routing strategy dynamically
        new_strategy = {
            "priority_order": ["google_speech", "azure_speech", "openai_whisper", "abena_ai"],
            "quality_threshold": 0.9
        }
        
        await provider_manager.update_routing_strategy("quality_optimized", new_strategy)
        
        # Test updated routing
        decision = await provider_manager.select_provider("en-US", "quality_optimized")
        assert decision.provider_id == "google_speech"  # New priority order
    
    @pytest.mark.asyncio
    async def test_provider_removal_and_addition(self, provider_manager):
        """Test dynamic provider removal and addition"""
        # Remove Azure provider
        await provider_manager.remove_provider("azure_speech")
        assert "azure_speech" not in provider_manager.providers
        
        # Test routing without Azure
        decision = await provider_manager.select_provider("en-US", "quality_optimized")
        assert decision.provider_id == "google_speech"  # Next in priority
        
        # Add new provider
        new_provider_settings = ProviderSettings(
            provider_id="new_provider",
            name="New Provider",
            custom_settings={"api_key": "test_key"}
        )
        
        with patch('shared.telephony.adapters.base.BaseTelephonyAdapter') as mock_adapter:
            await provider_manager.add_provider("new_provider", mock_adapter(new_provider_settings))
            assert "new_provider" in provider_manager.providers


class TestProviderSwitchingPerformance:
    """Performance tests for provider switching"""
    
    @pytest.fixture
    async def performance_manager(self, provider_manager_config):
        """Create provider manager for performance testing"""
        manager = AdvancedProviderManager(provider_manager_config)
        await manager.start()
        yield manager
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_provider_selection_performance(self, performance_manager):
        """Test provider selection performance"""
        start_time = time.time()
        
        # Perform 100 provider selections
        for _ in range(100):
            await performance_manager.select_provider("en-US", "quality_optimized")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 100 selections in under 5 seconds
        assert total_time < 5.0
        assert total_time / 100 < 0.05  # Average time per selection under 50ms
    
    @pytest.mark.asyncio
    async def test_concurrent_selection_performance(self, performance_manager):
        """Test concurrent provider selection performance"""
        start_time = time.time()
        
        # Perform 50 concurrent selections
        tasks = []
        for _ in range(50):
            task = performance_manager.select_provider("en-US", "quality_optimized")
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 50 concurrent selections in under 2 seconds
        assert total_time < 2.0
    
    @pytest.mark.asyncio
    async def test_provider_switching_latency(self, performance_manager):
        """Test provider switching latency"""
        # Start call
        context = CallContext(language="en-US")
        call_id = await performance_manager.providers["azure_speech"].dial("+1234567890", "+0987654321", context)
        
        # Measure switching time
        start_time = time.time()
        await performance_manager.switch_provider_during_call(call_id, "google_speech")
        end_time = time.time()
        
        switching_time = end_time - start_time
        
        # Should switch providers in under 1 second
        assert switching_time < 1.0
    
    @pytest.mark.asyncio
    async def test_health_check_performance(self, performance_manager):
        """Test health check performance"""
        start_time = time.time()
        
        # Perform health checks for all providers
        for _ in range(10):
            await performance_manager._check_all_provider_health()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 10 health check rounds in under 3 seconds
        assert total_time < 3.0
    
    @pytest.mark.asyncio
    async def test_metrics_collection_performance(self, performance_manager):
        """Test metrics collection performance"""
        start_time = time.time()
        
        # Collect metrics for all providers
        for _ in range(20):
            await performance_manager._collect_all_provider_metrics()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 20 metric collection rounds in under 4 seconds
        assert total_time < 4.0


class TestProviderSwitchingStress:
    """Stress tests for provider switching"""
    
    @pytest.fixture
    async def stress_manager(self, provider_manager_config):
        """Create provider manager for stress testing"""
        manager = AdvancedProviderManager(provider_manager_config)
        await manager.start()
        yield manager
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_high_concurrency_stress(self, stress_manager):
        """Test high concurrency stress"""
        # Simulate 1000 concurrent requests
        tasks = []
        for i in range(1000):
            task = stress_manager.select_provider(f"lang_{i % 10}", "quality_optimized")
            tasks.append(task)
        
        # Should handle all requests without errors
        decisions = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful decisions
        successful_decisions = [d for d in decisions if isinstance(d, ProviderDecision)]
        assert len(successful_decisions) >= 950  # At least 95% success rate
    
    @pytest.mark.asyncio
    async def test_provider_failure_stress(self, stress_manager):
        """Test stress under provider failures"""
        # Mock multiple provider failures
        with patch.object(stress_manager.providers["azure_speech"], 'is_connected', return_value=False), \
             patch.object(stress_manager.providers["google_speech"], 'is_connected', return_value=False):
            
            # Attempt 100 selections with limited providers
            tasks = []
            for _ in range(100):
                task = stress_manager.select_provider("en-US", "quality_optimized")
                tasks.append(task)
            
            decisions = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Should still provide decisions (using remaining providers)
            successful_decisions = [d for d in decisions if isinstance(d, ProviderDecision)]
            assert len(successful_decisions) >= 90  # At least 90% success rate
    
    @pytest.mark.asyncio
    async def test_memory_usage_stress(self, stress_manager):
        """Test memory usage under stress"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform intensive operations
        for _ in range(1000):
            await stress_manager.select_provider("en-US", "quality_optimized")
            await stress_manager._check_all_provider_health()
            await stress_manager._collect_all_provider_metrics()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024  # 100MB in bytes


if __name__ == "__main__":
    pytest.main([__file__])
