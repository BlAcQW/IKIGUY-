"""
Performance Tests and Benchmarking

This module contains comprehensive performance tests and benchmarking for
translation adapters and provider switching system.
"""

import pytest
import asyncio
import time
import statistics
import psutil
import os
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List, Tuple
import aiohttp
import numpy as np

from ..telephony.adapters.azure_speech import AzureSpeechAdapter
from ..telephony.adapters.google_speech import GoogleSpeechAdapter
from ..telephony.adapters.openai_whisper import WhisperAdapter
from ..telephony.adapters.abena_ai import AbenaAITelephonyAdapter
from ..telephony.advanced_provider_manager import AdvancedProviderManager
from ..telephony.models import CallContext, ProviderSettings


class PerformanceBenchmark:
    """Base class for performance benchmarking"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def start_benchmark(self):
        """Start benchmarking"""
        self.start_time = time.time()
        self.results = {}
    
    def end_benchmark(self):
        """End benchmarking"""
        self.end_time = time.time()
        return self.end_time - self.start_time
    
    def record_metric(self, name: str, value: float, unit: str = "ms"):
        """Record a performance metric"""
        if name not in self.results:
            self.results[name] = []
        self.results[name].append({"value": value, "unit": unit, "timestamp": time.time()})
    
    def get_statistics(self, name: str) -> Dict[str, float]:
        """Get statistics for a metric"""
        if name not in self.results:
            return {}
        
        values = [r["value"] for r in self.results[name]]
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0,
            "p95": np.percentile(values, 95) if len(values) > 0 else 0,
            "p99": np.percentile(values, 99) if len(values) > 0 else 0
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": self.end_benchmark() if self.end_time else 0,
            "metrics": {}
        }
        
        for metric_name in self.results.keys():
            report["metrics"][metric_name] = self.get_statistics(metric_name)
        
        return report


class TestTranslationAdapterPerformance:
    """Performance tests for translation adapters"""
    
    @pytest.fixture
    def performance_benchmark(self):
        """Create performance benchmark instance"""
        return PerformanceBenchmark()
    
    @pytest.fixture
    def adapter_settings(self):
        """Create settings for all adapters"""
        return {
            "azure_speech": ProviderSettings(
                provider_id="azure_speech_perf",
                api_key="test_azure_key",
                base_url="https://eastus.api.cognitive.microsoft.com",
                custom_settings={
                    "subscription_key": "test_azure_key",
                    "region": "eastus",
                    "timeout": 30
                }
            ),
            "google_speech": ProviderSettings(
                provider_id="google_speech_perf",
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
                provider_id="openai_whisper_perf",
                api_key="test_openai_key",
                base_url="https://api.openai.com/v1",
                custom_settings={
                    "api_key": "test_openai_key",
                    "model": "whisper-1",
                    "timeout": 30
                }
            ),
            "abena_ai": ProviderSettings(
                provider_id="abena_ai_perf",
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
    def adapters(self, adapter_settings):
        """Create all adapters"""
        return {
            "azure_speech": AzureSpeechAdapter(adapter_settings["azure_speech"]),
            "google_speech": GoogleSpeechAdapter(adapter_settings["google_speech"]),
            "openai_whisper": WhisperAdapter(adapter_settings["openai_whisper"]),
            "abena_ai": AbenaAITelephonyAdapter(adapter_settings["abena_ai"])
        }
    
    @pytest.mark.asyncio
    async def test_connection_performance(self, adapters, performance_benchmark):
        """Test connection performance for all adapters"""
        performance_benchmark.start_benchmark()
        
        for name, adapter in adapters.items():
            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value = mock_session.return_value
                
                start_time = time.time()
                await adapter.connect()
                end_time = time.time()
                
                connection_time = (end_time - start_time) * 1000  # Convert to ms
                performance_benchmark.record_metric(f"{name}_connection_time", connection_time)
                
                await adapter.disconnect()
        
        total_time = performance_benchmark.end_benchmark()
        report = performance_benchmark.generate_report()
        
        # Assertions
        for name in adapters.keys():
            stats = report["metrics"][f"{name}_connection_time"]
            assert stats["mean"] < 100  # Connection should be under 100ms
            assert stats["p95"] < 200   # 95th percentile under 200ms
    
    @pytest.mark.asyncio
    async def test_stt_performance(self, adapters, performance_benchmark):
        """Test speech-to-text performance"""
        performance_benchmark.start_benchmark()
        
        # Create test audio data (1 second of audio)
        audio_data = b"fake_audio_data" * 1000  # Simulate 1KB of audio data
        context = CallContext(language="en-US")
        
        for name, adapter in adapters.items():
            with patch('aiohttp.ClientSession.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "text": "Hello world",
                    "confidence": 0.95
                }
                mock_post.return_value = mock_response
                
                # Connect adapter
                await adapter.connect()
                
                # Start call
                call_id = await adapter.dial("+1234567890", "+0987654321", context)
                
                # Measure STT performance
                start_time = time.time()
                success = await adapter.send_audio(call_id, audio_data, "wav")
                end_time = time.time()
                
                stt_time = (end_time - start_time) * 1000  # Convert to ms
                performance_benchmark.record_metric(f"{name}_stt_time", stt_time)
                
                # Cleanup
                await adapter.hangup(call_id)
                await adapter.disconnect()
        
        total_time = performance_benchmark.end_benchmark()
        report = performance_benchmark.generate_report()
        
        # Assertions
        for name in adapters.keys():
            stats = report["metrics"][f"{name}_stt_time"]
            assert stats["mean"] < 5000  # STT should be under 5 seconds
            assert stats["p95"] < 10000  # 95th percentile under 10 seconds
    
    @pytest.mark.asyncio
    async def test_tts_performance(self, adapters, performance_benchmark):
        """Test text-to-speech performance"""
        performance_benchmark.start_benchmark()
        
        text = "Hello, this is a test message for text-to-speech performance testing."
        context = CallContext(language="en-US")
        
        for name, adapter in adapters.items():
            # Skip Whisper as it doesn't support TTS
            if name == "openai_whisper":
                continue
                
            with patch('aiohttp.ClientSession.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.read.return_value = b"synthesized_audio_data"
                mock_post.return_value = mock_response
                
                # Connect adapter
                await adapter.connect()
                
                # Start call
                call_id = await adapter.dial("+1234567890", "+0987654321", context)
                
                # Measure TTS performance
                start_time = time.time()
                audio_data = await adapter.synthesize_speech(call_id, text, voice_name="test_voice")
                end_time = time.time()
                
                tts_time = (end_time - start_time) * 1000  # Convert to ms
                performance_benchmark.record_metric(f"{name}_tts_time", tts_time)
                
                # Cleanup
                await adapter.hangup(call_id)
                await adapter.disconnect()
        
        total_time = performance_benchmark.end_benchmark()
        report = performance_benchmark.generate_report()
        
        # Assertions
        for name in ["azure_speech", "google_speech", "abena_ai"]:
            stats = report["metrics"][f"{name}_tts_time"]
            assert stats["mean"] < 3000  # TTS should be under 3 seconds
            assert stats["p95"] < 6000   # 95th percentile under 6 seconds
    
    @pytest.mark.asyncio
    async def test_language_detection_performance(self, adapters, performance_benchmark):
        """Test language detection performance"""
        performance_benchmark.start_benchmark()
        
        audio_data = b"fake_audio_data" * 500
        
        for name, adapter in adapters.items():
            with patch('aiohttp.ClientSession.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "language": "en-US",
                    "confidence": 0.95
                }
                mock_post.return_value = mock_response
                
                # Connect adapter
                await adapter.connect()
                
                # Measure language detection performance
                start_time = time.time()
                detected_language = await adapter.detect_language(audio_data)
                end_time = time.time()
                
                detection_time = (end_time - start_time) * 1000  # Convert to ms
                performance_benchmark.record_metric(f"{name}_language_detection_time", detection_time)
                
                # Cleanup
                await adapter.disconnect()
        
        total_time = performance_benchmark.end_benchmark()
        report = performance_benchmark.generate_report()
        
        # Assertions
        for name in adapters.keys():
            stats = report["metrics"][f"{name}_language_detection_time"]
            assert stats["mean"] < 2000  # Language detection should be under 2 seconds
            assert stats["p95"] < 4000   # 95th percentile under 4 seconds
    
    @pytest.mark.asyncio
    async def test_concurrent_performance(self, adapters, performance_benchmark):
        """Test concurrent performance"""
        performance_benchmark.start_benchmark()
        
        audio_data = b"fake_audio_data" * 500
        context = CallContext(language="en-US")
        
        async def process_audio(adapter_name: str, adapter, audio: bytes):
            """Process audio with adapter"""
            with patch('aiohttp.ClientSession.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.json.return_value = {"text": "Hello world"}
                mock_post.return_value = mock_response
                
                await adapter.connect()
                call_id = await adapter.dial("+1234567890", "+0987654321", context)
                
                start_time = time.time()
                await adapter.send_audio(call_id, audio, "wav")
                end_time = time.time()
                
                processing_time = (end_time - start_time) * 1000
                performance_benchmark.record_metric(f"{adapter_name}_concurrent_time", processing_time)
                
                await adapter.hangup(call_id)
                await adapter.disconnect()
        
        # Run 10 concurrent operations for each adapter
        tasks = []
        for name, adapter in adapters.items():
            for i in range(10):
                task = process_audio(name, adapter, audio_data)
                tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        total_time = performance_benchmark.end_benchmark()
        report = performance_benchmark.generate_report()
        
        # Assertions
        for name in adapters.keys():
            stats = report["metrics"][f"{name}_concurrent_time"]
            assert stats["mean"] < 3000  # Concurrent processing under 3 seconds
            assert stats["p95"] < 6000   # 95th percentile under 6 seconds


class TestProviderSwitchingPerformance:
    """Performance tests for provider switching"""
    
    @pytest.fixture
    def provider_manager_config(self, adapter_settings):
        """Create provider manager configuration"""
        adapters = {
            "azure_speech": AzureSpeechAdapter(adapter_settings["azure_speech"]),
            "google_speech": GoogleSpeechAdapter(adapter_settings["google_speech"]),
            "openai_whisper": WhisperAdapter(adapter_settings["openai_whisper"]),
            "abena_ai": AbenaAITelephonyAdapter(adapter_settings["abena_ai"])
        }
        
        return {
            "providers": adapters,
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
            "max_retries": 3
        }
    
    @pytest.mark.asyncio
    async def test_provider_selection_performance(self, provider_manager_config, performance_benchmark):
        """Test provider selection performance"""
        performance_benchmark.start_benchmark()
        
        manager = AdvancedProviderManager(provider_manager_config)
        await manager.start()
        
        languages = ["en-US", "es-ES", "fr-FR", "de-DE", "it-IT", "tw", "en-GH", "ee", "ga", "dag"]
        strategies = ["quality_optimized", "cost_optimized", "geographic"]
        
        for strategy in strategies:
            for language in languages:
                start_time = time.time()
                decision = await manager.select_provider(language, strategy)
                end_time = time.time()
                
                selection_time = (end_time - start_time) * 1000  # Convert to ms
                performance_benchmark.record_metric(f"provider_selection_{strategy}", selection_time)
        
        await manager.stop()
        
        total_time = performance_benchmark.end_benchmark()
        report = performance_benchmark.generate_report()
        
        # Assertions
        for strategy in strategies:
            stats = report["metrics"][f"provider_selection_{strategy}"]
            assert stats["mean"] < 50   # Provider selection under 50ms
            assert stats["p95"] < 100   # 95th percentile under 100ms
    
    @pytest.mark.asyncio
    async def test_concurrent_provider_selection(self, provider_manager_config, performance_benchmark):
        """Test concurrent provider selection performance"""
        performance_benchmark.start_benchmark()
        
        manager = AdvancedProviderManager(provider_manager_config)
        await manager.start()
        
        async def select_provider(language: str, strategy: str):
            """Select provider and measure time"""
            start_time = time.time()
            decision = await manager.select_provider(language, strategy)
            end_time = time.time()
            
            selection_time = (end_time - start_time) * 1000
            performance_benchmark.record_metric("concurrent_provider_selection", selection_time)
            return decision
        
        # Run 100 concurrent provider selections
        tasks = []
        for i in range(100):
            language = f"lang_{i % 10}"
            strategy = ["quality_optimized", "cost_optimized", "geographic"][i % 3]
            task = select_provider(language, strategy)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        await manager.stop()
        
        total_time = performance_benchmark.end_benchmark()
        report = performance_benchmark.generate_report()
        
        # Assertions
        stats = report["metrics"]["concurrent_provider_selection"]
        assert stats["mean"] < 100   # Concurrent selection under 100ms
        assert stats["p95"] < 200    # 95th percentile under 200ms
        assert stats["count"] == 100 # All 100 selections completed
    
    @pytest.mark.asyncio
    async def test_provider_switching_latency(self, provider_manager_config, performance_benchmark):
        """Test provider switching latency"""
        performance_benchmark.start_benchmark()
        
        manager = AdvancedProviderManager(provider_manager_config)
        await manager.start()
        
        context = CallContext(language="en-US")
        
        # Start call with Azure
        call_id = await manager.providers["azure_speech"].dial("+1234567890", "+0987654321", context)
        
        # Measure switching time to different providers
        target_providers = ["google_speech", "openai_whisper", "abena_ai"]
        
        for target_provider in target_providers:
            start_time = time.time()
            new_provider = await manager.switch_provider_during_call(call_id, target_provider)
            end_time = time.time()
            
            switching_time = (end_time - start_time) * 1000
            performance_benchmark.record_metric("provider_switching_latency", switching_time)
        
        await manager.stop()
        
        total_time = performance_benchmark.end_benchmark()
        report = performance_benchmark.generate_report()
        
        # Assertions
        stats = report["metrics"]["provider_switching_latency"]
        assert stats["mean"] < 1000   # Provider switching under 1 second
        assert stats["p95"] < 2000    # 95th percentile under 2 seconds


class TestResourceUsageBenchmarking:
    """Resource usage benchmarking tests"""
    
    @pytest.fixture
    def resource_monitor(self):
        """Create resource monitor"""
        return ResourceMonitor()
    
    @pytest.mark.asyncio
    async def test_memory_usage_benchmark(self, adapters, resource_monitor):
        """Test memory usage during operations"""
        resource_monitor.start_monitoring()
        
        # Perform intensive operations
        audio_data = b"fake_audio_data" * 1000
        context = CallContext(language="en-US")
        
        for name, adapter in adapters.items():
            with patch('aiohttp.ClientSession.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.json.return_value = {"text": "Hello world"}
                mock_post.return_value = mock_response
                
                await adapter.connect()
                call_id = await adapter.dial("+1234567890", "+0987654321", context)
                
                # Perform multiple STT operations
                for i in range(10):
                    await adapter.send_audio(call_id, audio_data, "wav")
                
                await adapter.hangup(call_id)
                await adapter.disconnect()
        
        resource_monitor.stop_monitoring()
        report = resource_monitor.generate_report()
        
        # Assertions
        assert report["peak_memory_mb"] < 500  # Peak memory under 500MB
        assert report["avg_memory_mb"] < 300   # Average memory under 300MB
        assert report["memory_leak_mb"] < 50   # Memory leak under 50MB
    
    @pytest.mark.asyncio
    async def test_cpu_usage_benchmark(self, adapters, resource_monitor):
        """Test CPU usage during operations"""
        resource_monitor.start_monitoring()
        
        # Perform CPU-intensive operations
        tasks = []
        for name, adapter in adapters.items():
            with patch('aiohttp.ClientSession.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.json.return_value = {"text": "Hello world"}
                mock_post.return_value = mock_response
                
                await adapter.connect()
                
                # Create concurrent tasks
                for i in range(5):
                    task = self._cpu_intensive_operation(adapter)
                    tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        resource_monitor.stop_monitoring()
        report = resource_monitor.generate_report()
        
        # Assertions
        assert report["peak_cpu_percent"] < 80   # Peak CPU under 80%
        assert report["avg_cpu_percent"] < 50    # Average CPU under 50%
    
    async def _cpu_intensive_operation(self, adapter):
        """Perform CPU-intensive operation"""
        context = CallContext(language="en-US")
        call_id = await adapter.dial("+1234567890", "+0987654321", context)
        
        # Simulate CPU-intensive processing
        for i in range(100):
            audio_data = b"fake_audio_data" * (i + 1)
            await adapter.send_audio(call_id, audio_data, "wav")
        
        await adapter.hangup(call_id)


class ResourceMonitor:
    """Monitor system resources during testing"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.memory_samples = []
        self.cpu_samples = []
        self.start_time = None
        self.end_time = None
        self.monitoring = False
    
    def start_monitoring(self):
        """Start resource monitoring"""
        self.start_time = time.time()
        self.monitoring = True
        self.memory_samples = []
        self.cpu_samples = []
        
        # Start monitoring in background
        asyncio.create_task(self._monitor_resources())
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        self.end_time = time.time()
    
    async def _monitor_resources(self):
        """Monitor resources in background"""
        while self.monitoring:
            # Memory usage
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            self.memory_samples.append(memory_mb)
            
            # CPU usage
            cpu_percent = self.process.cpu_percent()
            self.cpu_samples.append(cpu_percent)
            
            await asyncio.sleep(0.1)  # Sample every 100ms
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate resource usage report"""
        if not self.memory_samples or not self.cpu_samples:
            return {}
        
        initial_memory = self.memory_samples[0] if self.memory_samples else 0
        final_memory = self.memory_samples[-1] if self.memory_samples else 0
        memory_leak = final_memory - initial_memory
        
        return {
            "duration_seconds": self.end_time - self.start_time if self.end_time else 0,
            "peak_memory_mb": max(self.memory_samples) if self.memory_samples else 0,
            "avg_memory_mb": statistics.mean(self.memory_samples) if self.memory_samples else 0,
            "memory_leak_mb": memory_leak,
            "peak_cpu_percent": max(self.cpu_samples) if self.cpu_samples else 0,
            "avg_cpu_percent": statistics.mean(self.cpu_samples) if self.cpu_samples else 0,
            "sample_count": len(self.memory_samples)
        }


class TestThroughputBenchmarking:
    """Throughput benchmarking tests"""
    
    @pytest.mark.asyncio
    async def test_stt_throughput(self, adapters, performance_benchmark):
        """Test STT throughput (operations per second)"""
        performance_benchmark.start_benchmark()
        
        audio_data = b"fake_audio_data" * 500
        context = CallContext(language="en-US")
        
        async def process_audio_batch(adapter_name: str, adapter, batch_size: int):
            """Process a batch of audio operations"""
            with patch('aiohttp.ClientSession.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.json.return_value = {"text": "Hello world"}
                mock_post.return_value = mock_response
                
                await adapter.connect()
                
                start_time = time.time()
                
                for i in range(batch_size):
                    call_id = await adapter.dial("+1234567890", "+0987654321", context)
                    await adapter.send_audio(call_id, audio_data, "wav")
                    await adapter.hangup(call_id)
                
                end_time = time.time()
                duration = end_time - start_time
                throughput = batch_size / duration
                
                performance_benchmark.record_metric(f"{adapter_name}_throughput", throughput, "ops/sec")
                
                await adapter.disconnect()
        
        # Test throughput with different batch sizes
        batch_sizes = [10, 50, 100]
        
        for batch_size in batch_sizes:
            tasks = []
            for name, adapter in adapters.items():
                task = process_audio_batch(name, adapter, batch_size)
                tasks.append(task)
            
            await asyncio.gather(*tasks)
        
        total_time = performance_benchmark.end_benchmark()
        report = performance_benchmark.generate_report()
        
        # Assertions
        for name in adapters.keys():
            stats = report["metrics"][f"{name}_throughput"]
            assert stats["mean"] > 1.0   # At least 1 operation per second
            assert stats["min"] > 0.5    # Minimum 0.5 operations per second
    
    @pytest.mark.asyncio
    async def test_concurrent_throughput(self, adapters, performance_benchmark):
        """Test concurrent throughput"""
        performance_benchmark.start_benchmark()
        
        audio_data = b"fake_audio_data" * 500
        context = CallContext(language="en-US")
        
        async def concurrent_operation(adapter_name: str, adapter, operation_count: int):
            """Perform concurrent operations"""
            with patch('aiohttp.ClientSession.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.json.return_value = {"text": "Hello world"}
                mock_post.return_value = mock_response
                
                await adapter.connect()
                
                start_time = time.time()
                
                # Create concurrent tasks
                tasks = []
                for i in range(operation_count):
                    task = self._single_operation(adapter, audio_data, context)
                    tasks.append(task)
                
                await asyncio.gather(*tasks)
                
                end_time = time.time()
                duration = end_time - start_time
                throughput = operation_count / duration
                
                performance_benchmark.record_metric(f"{adapter_name}_concurrent_throughput", throughput, "ops/sec")
                
                await adapter.disconnect()
        
        # Test with different concurrency levels
        concurrency_levels = [5, 10, 20]
        
        for level in concurrency_levels:
            tasks = []
            for name, adapter in adapters.items():
                task = concurrent_operation(name, adapter, level)
                tasks.append(task)
            
            await asyncio.gather(*tasks)
        
        total_time = performance_benchmark.end_benchmark()
        report = performance_benchmark.generate_report()
        
        # Assertions
        for name in adapters.keys():
            stats = report["metrics"][f"{name}_concurrent_throughput"]
            assert stats["mean"] > 2.0   # At least 2 concurrent operations per second
            assert stats["min"] > 1.0    # Minimum 1 concurrent operation per second
    
    async def _single_operation(self, adapter, audio_data: bytes, context: CallContext):
        """Perform a single operation"""
        call_id = await adapter.dial("+1234567890", "+0987654321", context)
        await adapter.send_audio(call_id, audio_data, "wav")
        await adapter.hangup(call_id)


if __name__ == "__main__":
    pytest.main([__file__])
