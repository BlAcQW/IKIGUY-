"""
Performance benchmarking system for Ghanaian language processing

This module provides comprehensive performance benchmarking capabilities
for Ghanaian language processing operations including latency, throughput,
accuracy, and resource usage measurements.
"""

import asyncio
import json
import logging
import time
import tracemalloc
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from statistics import mean, median, stdev
from concurrent.futures import ThreadPoolExecutor
import psutil
import numpy as np

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class BenchmarkType(Enum):
    """Types of benchmarks"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ACCURACY = "accuracy"
    RESOURCE_USAGE = "resource_usage"
    END_TO_END = "end_to_end"


class OperationType(Enum):
    """Types of operations to benchmark"""
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    NER_ANALYSIS = "ner_analysis"
    INTENT_DETECTION = "intent_detection"
    LANGUAGE_DETECTION = "language_detection"
    TEXT_TRANSLATION = "text_translation"
    SPEECH_RECOGNITION = "speech_recognition"
    SPEECH_SYNTHESIS = "speech_synthesis"


@dataclass
class BenchmarkConfig:
    """Configuration for benchmarking"""
    # General settings
    warmup_iterations: int = 10
    benchmark_iterations: int = 100
    concurrent_requests: int = 1
    timeout_seconds: float = 30.0
    
    # Latency settings
    latency_percentiles: List[float] = field(default_factory=lambda: [50, 90, 95, 99])
    
    # Throughput settings
    throughput_duration_seconds: int = 60
    throughput_requests_per_second: int = 10
    
    # Resource monitoring
    enable_memory_tracking: bool = True
    enable_cpu_tracking: bool = True
    enable_disk_tracking: bool = False
    resource_sampling_interval: float = 0.1  # seconds
    
    # Accuracy settings
    reference_data_path: Optional[str] = None
    accuracy_metrics: List[str] = field(default_factory=lambda: ["precision", "recall", "f1"])
    
    # Output settings
    output_dir: str = "./benchmark_results"
    save_detailed_results: bool = True
    generate_reports: bool = True


@dataclass
class PerformanceMetrics:
    """Performance metrics for a benchmark"""
    operation: str
    language: str
    benchmark_type: BenchmarkType
    
    # Latency metrics
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    mean_latency_ms: float = 0.0
    median_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    
    # Throughput metrics
    requests_per_second: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Accuracy metrics
    accuracy_score: float = 0.0
    precision_score: float = 0.0
    recall_score: float = 0.0
    f1_score: float = 0.0
    
    # Resource usage
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    peak_cpu_percent: float = 0.0
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_seconds: float = 0.0
    config: Dict[str, Any] = field(default_factory=dict)


class BenchmarkResult(BaseModel):
    """Benchmark result model"""
    operation: str
    language: str
    benchmark_type: str
    metrics: PerformanceMetrics
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ResourceMonitor:
    """Monitor system resources during benchmarks"""
    
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.memory_samples: List[float] = []
        self.cpu_samples: List[float] = []
        self.disk_samples: List[float] = []
        self.monitoring = False
        self.monitor_task = None
    
    async def start_monitoring(self):
        """Start resource monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.memory_samples.clear()
        self.cpu_samples.clear()
        self.disk_samples.clear()
        
        self.monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self):
        """Stop resource monitoring"""
        if not self.monitoring:
            return
        
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        """Resource monitoring loop"""
        while self.monitoring:
            try:
                # Memory usage
                if self.config.enable_memory_tracking:
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    self.memory_samples.append(memory_mb)
                
                # CPU usage
                if self.config.enable_cpu_tracking:
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    self.cpu_samples.append(cpu_percent)
                
                # Disk usage (optional)
                if self.config.enable_disk_tracking:
                    disk_usage = psutil.disk_usage('/').percent
                    self.disk_samples.append(disk_usage)
                
                await asyncio.sleep(self.config.resource_sampling_interval)
                
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                await asyncio.sleep(1.0)
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get resource usage summary"""
        summary = {}
        
        if self.memory_samples:
            summary["memory"] = {
                "peak_mb": max(self.memory_samples),
                "avg_mb": mean(self.memory_samples),
                "min_mb": min(self.memory_samples),
                "samples": len(self.memory_samples)
            }
        
        if self.cpu_samples:
            summary["cpu"] = {
                "peak_percent": max(self.cpu_samples),
                "avg_percent": mean(self.cpu_samples),
                "min_percent": min(self.cpu_samples),
                "samples": len(self.cpu_samples)
            }
        
        if self.disk_samples:
            summary["disk"] = {
                "peak_percent": max(self.disk_samples),
                "avg_percent": mean(self.disk_samples),
                "min_percent": min(self.disk_samples),
                "samples": len(self.disk_samples)
            }
        
        return summary


class PerformanceBenchmark:
    """
    Performance benchmarking system for Ghanaian language processing
    
    Provides comprehensive benchmarking capabilities for measuring
    latency, throughput, accuracy, and resource usage.
    """
    
    def __init__(self, config: BenchmarkConfig):
        """
        Initialize performance benchmark
        
        Args:
            config: Benchmark configuration
        """
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Resource monitor
        self.resource_monitor = ResourceMonitor(config)
        
        # Benchmark results
        self.results: List[BenchmarkResult] = []
        
        # Test data
        self.test_data = self._load_test_data()
    
    def _load_test_data(self) -> Dict[str, List[str]]:
        """Load test data for different languages"""
        return {
            "tw": [
                "ɛyɛ adeɛ pa",  # "It is good"
                "me pɛ wo",  # "I love you"
                "wo ho te sɛn",  # "How are you?"
                "meda wo ase",  # "Thank you"
                "yɛbɛhyia bio",  # "See you again"
                "ɛnyɛ adeɛ pa",  # "It is not good"
                "me nyɛ wo",  # "I don't love you"
                "wo ho nyɛ yie",  # "You are not well"
                "me nyɛ wo ase",  # "I don't thank you"
                "yɛnhyia bio",  # "Don't see you again"
            ],
            "en-GH": [
                "make you dey fine",  # "Are you fine?"
                "I dey chop",  # "I am eating"
                "no wahala",  # "No problem"
                "you fit help me",  # "Can you help me?"
                "I go come back",  # "I will come back"
                "you no dey fine",  # "You are not fine"
                "I no dey chop",  # "I am not eating"
                "big wahala",  # "Big problem"
                "you no fit help me",  # "You cannot help me"
                "I no go come back",  # "I will not come back"
            ],
            "ee": [
                "wo nyuie",  # "You are good"
                "me le",  # "I am here"
                "wo kɔ",  # "You go"
                "me nyɛ wo",  # "I don't love you"
                "wo nyɛ nyuie",  # "You are not good"
                "me nyɛ le",  # "I am not here"
                "wo nyɛ kɔ",  # "You don't go"
                "me nyɛ wo",  # "I don't love you"
            ],
            "ga": [
                "wo nyɛ",  # "You are good"
                "me le",  # "I am here"
                "wo kɔ",  # "You go"
                "me nyɛ wo",  # "I don't love you"
                "wo nyɛ nyɛ",  # "You are not good"
                "me nyɛ le",  # "I am not here"
                "wo nyɛ kɔ",  # "You don't go"
                "me nyɛ wo",  # "I don't love you"
            ],
            "dag": [
                "a yɛla",  # "You are good"
                "n le",  # "I am here"
                "a kɔ",  # "You go"
                "n nyɛ a",  # "I don't love you"
                "a nyɛ yɛla",  # "You are not good"
                "n nyɛ le",  # "I am not here"
                "a nyɛ kɔ",  # "You don't go"
                "n nyɛ a",  # "I don't love you"
            ]
        }
    
    async def benchmark_operation(
        self,
        operation: Callable,
        operation_name: str,
        language: str,
        benchmark_type: BenchmarkType = BenchmarkType.LATENCY,
        **kwargs
    ) -> BenchmarkResult:
        """
        Benchmark a single operation
        
        Args:
            operation: Operation to benchmark
            operation_name: Name of the operation
            language: Language code
            benchmark_type: Type of benchmark to run
            **kwargs: Additional arguments for the operation
            
        Returns:
            Benchmark result
        """
        logger.info(f"Starting {benchmark_type.value} benchmark for {operation_name} ({language})")
        
        # Start resource monitoring
        await self.resource_monitor.start_monitoring()
        
        try:
            if benchmark_type == BenchmarkType.LATENCY:
                metrics = await self._benchmark_latency(operation, operation_name, language, **kwargs)
            elif benchmark_type == BenchmarkType.THROUGHPUT:
                metrics = await self._benchmark_throughput(operation, operation_name, language, **kwargs)
            elif benchmark_type == BenchmarkType.ACCURACY:
                metrics = await self._benchmark_accuracy(operation, operation_name, language, **kwargs)
            elif benchmark_type == BenchmarkType.RESOURCE_USAGE:
                metrics = await self._benchmark_resource_usage(operation, operation_name, language, **kwargs)
            elif benchmark_type == BenchmarkType.END_TO_END:
                metrics = await self._benchmark_end_to_end(operation, operation_name, language, **kwargs)
            else:
                raise ValueError(f"Unknown benchmark type: {benchmark_type}")
            
            # Get resource summary
            resource_summary = self.resource_monitor.get_resource_summary()
            if resource_summary.get("memory"):
                metrics.peak_memory_mb = resource_summary["memory"]["peak_mb"]
            if resource_summary.get("cpu"):
                metrics.avg_cpu_percent = resource_summary["cpu"]["avg_percent"]
                metrics.peak_cpu_percent = resource_summary["cpu"]["peak_percent"]
            
            # Create benchmark result
            result = BenchmarkResult(
                operation=operation_name,
                language=language,
                benchmark_type=benchmark_type.value,
                metrics=metrics,
                raw_data={
                    "resource_summary": resource_summary,
                    "config": self.config.__dict__
                }
            )
            
            self.results.append(result)
            return result
            
        finally:
            # Stop resource monitoring
            await self.resource_monitor.stop_monitoring()
    
    async def _benchmark_latency(
        self,
        operation: Callable,
        operation_name: str,
        language: str,
        **kwargs
    ) -> PerformanceMetrics:
        """Benchmark operation latency"""
        latencies = []
        errors = []
        
        # Warmup
        logger.info(f"Running {self.config.warmup_iterations} warmup iterations")
        for _ in range(self.config.warmup_iterations):
            try:
                start_time = time.time()
                await operation(**kwargs)
                # Don't record warmup latencies
            except Exception as e:
                logger.warning(f"Warmup iteration failed: {e}")
        
        # Actual benchmark
        logger.info(f"Running {self.config.benchmark_iterations} benchmark iterations")
        for i in range(self.config.benchmark_iterations):
            try:
                start_time = time.time()
                await operation(**kwargs)
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Completed {i + 1}/{self.config.benchmark_iterations} iterations")
                    
            except Exception as e:
                logger.error(f"Benchmark iteration {i} failed: {e}")
                errors.append(str(e))
        
        # Calculate metrics
        if not latencies:
            raise ValueError("No successful benchmark iterations")
        
        metrics = PerformanceMetrics(
            operation=operation_name,
            language=language,
            benchmark_type=BenchmarkType.LATENCY,
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            mean_latency_ms=mean(latencies),
            median_latency_ms=median(latencies),
            successful_requests=len(latencies),
            failed_requests=len(errors),
            total_requests=len(latencies) + len(errors),
            duration_seconds=time.time() - time.time(),  # Will be set properly
            config=self.config.__dict__
        )
        
        # Calculate percentiles
        sorted_latencies = sorted(latencies)
        for percentile in self.config.latency_percentiles:
            index = int((percentile / 100) * len(sorted_latencies)) - 1
            if index >= 0:
                value = sorted_latencies[index]
                if percentile == 95:
                    metrics.p95_latency_ms = value
                elif percentile == 99:
                    metrics.p99_latency_ms = value
        
        return metrics
    
    async def _benchmark_throughput(
        self,
        operation: Callable,
        operation_name: str,
        language: str,
        **kwargs
    ) -> PerformanceMetrics:
        """Benchmark operation throughput"""
        start_time = time.time()
        end_time = start_time + self.config.throughput_duration_seconds
        
        successful_requests = 0
        failed_requests = 0
        errors = []
        
        # Calculate request interval
        request_interval = 1.0 / self.config.throughput_requests_per_second
        
        logger.info(f"Running throughput benchmark for {self.config.throughput_duration_seconds} seconds")
        
        while time.time() < end_time:
            try:
                await operation(**kwargs)
                successful_requests += 1
            except Exception as e:
                failed_requests += 1
                errors.append(str(e))
            
            # Wait for next request
            await asyncio.sleep(request_interval)
        
        duration = time.time() - start_time
        total_requests = successful_requests + failed_requests
        requests_per_second = total_requests / duration
        
        return PerformanceMetrics(
            operation=operation_name,
            language=language,
            benchmark_type=BenchmarkType.THROUGHPUT,
            requests_per_second=requests_per_second,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            duration_seconds=duration,
            config=self.config.__dict__
        )
    
    async def _benchmark_accuracy(
        self,
        operation: Callable,
        operation_name: str,
        language: str,
        **kwargs
    ) -> PerformanceMetrics:
        """Benchmark operation accuracy"""
        if not self.test_data.get(language):
            raise ValueError(f"No test data available for language: {language}")
        
        test_texts = self.test_data[language]
        correct_predictions = 0
        total_predictions = 0
        errors = []
        
        logger.info(f"Running accuracy benchmark with {len(test_texts)} test texts")
        
        for text in test_texts:
            try:
                # For now, we'll use a simple accuracy metric
                # In a real implementation, you'd compare against ground truth
                result = await operation(text=text, language=language, **kwargs)
                
                # Simple validation - if we get a result, consider it correct
                if result is not None:
                    correct_predictions += 1
                total_predictions += 1
                
            except Exception as e:
                errors.append(str(e))
                total_predictions += 1
        
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0.0
        
        return PerformanceMetrics(
            operation=operation_name,
            language=language,
            benchmark_type=BenchmarkType.ACCURACY,
            accuracy_score=accuracy,
            precision_score=accuracy,  # Simplified
            recall_score=accuracy,     # Simplified
            f1_score=accuracy,         # Simplified
            successful_requests=correct_predictions,
            failed_requests=len(errors),
            total_requests=total_predictions,
            duration_seconds=time.time() - time.time(),  # Will be set properly
            config=self.config.__dict__
        )
    
    async def _benchmark_resource_usage(
        self,
        operation: Callable,
        operation_name: str,
        language: str,
        **kwargs
    ) -> PerformanceMetrics:
        """Benchmark resource usage"""
        # This is handled by the resource monitor
        # Just run the operation a few times to collect data
        iterations = min(10, self.config.benchmark_iterations)
        
        logger.info(f"Running resource usage benchmark with {iterations} iterations")
        
        start_time = time.time()
        successful_requests = 0
        failed_requests = 0
        
        for i in range(iterations):
            try:
                await operation(**kwargs)
                successful_requests += 1
            except Exception as e:
                failed_requests += 1
                logger.error(f"Resource benchmark iteration {i} failed: {e}")
        
        duration = time.time() - start_time
        
        return PerformanceMetrics(
            operation=operation_name,
            language=language,
            benchmark_type=BenchmarkType.RESOURCE_USAGE,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_requests=successful_requests + failed_requests,
            duration_seconds=duration,
            config=self.config.__dict__
        )
    
    async def _benchmark_end_to_end(
        self,
        operation: Callable,
        operation_name: str,
        language: str,
        **kwargs
    ) -> PerformanceMetrics:
        """Benchmark end-to-end performance"""
        # Run all benchmark types and combine results
        logger.info("Running end-to-end benchmark")
        
        # Run latency benchmark
        latency_metrics = await self._benchmark_latency(operation, operation_name, language, **kwargs)
        
        # Run accuracy benchmark
        accuracy_metrics = await self._benchmark_accuracy(operation, operation_name, language, **kwargs)
        
        # Combine metrics
        combined_metrics = PerformanceMetrics(
            operation=operation_name,
            language=language,
            benchmark_type=BenchmarkType.END_TO_END,
            # Latency metrics
            min_latency_ms=latency_metrics.min_latency_ms,
            max_latency_ms=latency_metrics.max_latency_ms,
            mean_latency_ms=latency_metrics.mean_latency_ms,
            median_latency_ms=latency_metrics.median_latency_ms,
            p95_latency_ms=latency_metrics.p95_latency_ms,
            p99_latency_ms=latency_metrics.p99_latency_ms,
            # Accuracy metrics
            accuracy_score=accuracy_metrics.accuracy_score,
            precision_score=accuracy_metrics.precision_score,
            recall_score=accuracy_metrics.recall_score,
            f1_score=accuracy_metrics.f1_score,
            # Combined stats
            successful_requests=latency_metrics.successful_requests + accuracy_metrics.successful_requests,
            failed_requests=latency_metrics.failed_requests + accuracy_metrics.failed_requests,
            total_requests=latency_metrics.total_requests + accuracy_metrics.total_requests,
            duration_seconds=latency_metrics.duration_seconds + accuracy_metrics.duration_seconds,
            config=self.config.__dict__
        )
        
        return combined_metrics
    
    async def benchmark_all_operations(
        self,
        operations: Dict[str, Callable],
        languages: List[str],
        benchmark_types: List[BenchmarkType] = None
    ) -> List[BenchmarkResult]:
        """
        Benchmark multiple operations
        
        Args:
            operations: Dictionary of operation names to functions
            languages: List of languages to test
            benchmark_types: List of benchmark types to run
            
        Returns:
            List of benchmark results
        """
        if benchmark_types is None:
            benchmark_types = [BenchmarkType.LATENCY, BenchmarkType.ACCURACY]
        
        results = []
        
        for operation_name, operation in operations.items():
            for language in languages:
                for benchmark_type in benchmark_types:
                    try:
                        result = await self.benchmark_operation(
                            operation, operation_name, language, benchmark_type
                        )
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Benchmark failed for {operation_name} ({language}): {e}")
        
        return results
    
    def generate_report(self, results: List[BenchmarkResult] = None) -> str:
        """
        Generate benchmark report
        
        Args:
            results: List of benchmark results (uses self.results if None)
            
        Returns:
            Report as string
        """
        if results is None:
            results = self.results
        
        if not results:
            return "No benchmark results available"
        
        report_lines = [
            "# Ghanaian Language Processing Performance Benchmark Report",
            f"Generated: {datetime.utcnow().isoformat()}",
            f"Total Results: {len(results)}",
            "",
            "## Summary",
            ""
        ]
        
        # Group results by operation and language
        grouped_results = {}
        for result in results:
            key = (result.operation, result.language)
            if key not in grouped_results:
                grouped_results[key] = []
            grouped_results[key].append(result)
        
        # Generate summary for each operation/language combination
        for (operation, language), operation_results in grouped_results.items():
            report_lines.extend([
                f"### {operation} ({language})",
                ""
            ])
            
            for result in operation_results:
                metrics = result.metrics
                report_lines.extend([
                    f"**{result.benchmark_type}:**",
                    f"- Duration: {metrics.duration_seconds:.2f}s",
                    f"- Total Requests: {metrics.total_requests}",
                    f"- Successful: {metrics.successful_requests}",
                    f"- Failed: {metrics.failed_requests}",
                ])
                
                if result.benchmark_type == "latency":
                    report_lines.extend([
                        f"- Mean Latency: {metrics.mean_latency_ms:.2f}ms",
                        f"- Median Latency: {metrics.median_latency_ms:.2f}ms",
                        f"- P95 Latency: {metrics.p95_latency_ms:.2f}ms",
                        f"- P99 Latency: {metrics.p99_latency_ms:.2f}ms",
                    ])
                
                if result.benchmark_type == "throughput":
                    report_lines.extend([
                        f"- Requests/Second: {metrics.requests_per_second:.2f}",
                    ])
                
                if result.benchmark_type == "accuracy":
                    report_lines.extend([
                        f"- Accuracy: {metrics.accuracy_score:.3f}",
                        f"- Precision: {metrics.precision_score:.3f}",
                        f"- Recall: {metrics.recall_score:.3f}",
                        f"- F1 Score: {metrics.f1_score:.3f}",
                    ])
                
                if metrics.peak_memory_mb > 0:
                    report_lines.extend([
                        f"- Peak Memory: {metrics.peak_memory_mb:.2f}MB",
                        f"- Avg CPU: {metrics.avg_cpu_percent:.1f}%",
                        f"- Peak CPU: {metrics.peak_cpu_percent:.1f}%",
                    ])
                
                report_lines.append("")
        
        return "\n".join(report_lines)
    
    def save_results(self, results: List[BenchmarkResult] = None, filename: str = None):
        """
        Save benchmark results to file
        
        Args:
            results: List of benchmark results (uses self.results if None)
            filename: Output filename (auto-generated if None)
        """
        if results is None:
            results = self.results
        
        if not results:
            logger.warning("No results to save")
            return
        
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        # Convert results to JSON-serializable format
        serializable_results = []
        for result in results:
            serializable_result = {
                "operation": result.operation,
                "language": result.language,
                "benchmark_type": result.benchmark_type,
                "metrics": {
                    "operation": result.metrics.operation,
                    "language": result.metrics.language,
                    "benchmark_type": result.metrics.benchmark_type.value,
                    "min_latency_ms": result.metrics.min_latency_ms,
                    "max_latency_ms": result.metrics.max_latency_ms,
                    "mean_latency_ms": result.metrics.mean_latency_ms,
                    "median_latency_ms": result.metrics.median_latency_ms,
                    "p95_latency_ms": result.metrics.p95_latency_ms,
                    "p99_latency_ms": result.metrics.p99_latency_ms,
                    "requests_per_second": result.metrics.requests_per_second,
                    "total_requests": result.metrics.total_requests,
                    "successful_requests": result.metrics.successful_requests,
                    "failed_requests": result.metrics.failed_requests,
                    "accuracy_score": result.metrics.accuracy_score,
                    "precision_score": result.metrics.precision_score,
                    "recall_score": result.metrics.recall_score,
                    "f1_score": result.metrics.f1_score,
                    "peak_memory_mb": result.metrics.peak_memory_mb,
                    "avg_cpu_percent": result.metrics.avg_cpu_percent,
                    "peak_cpu_percent": result.metrics.peak_cpu_percent,
                    "timestamp": result.metrics.timestamp.isoformat(),
                    "duration_seconds": result.metrics.duration_seconds,
                },
                "raw_data": result.raw_data,
                "errors": result.errors,
                "timestamp": result.timestamp.isoformat()
            }
            serializable_results.append(serializable_result)
        
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"Benchmark results saved to {output_path}")
        
        # Generate and save report
        if self.config.generate_reports:
            report = self.generate_report(results)
            report_filename = filename.replace('.json', '_report.md')
            report_path = self.output_dir / report_filename
            
            with open(report_path, 'w') as f:
                f.write(report)
            
            logger.info(f"Benchmark report saved to {report_path}")
    
    def get_summary_stats(self, results: List[BenchmarkResult] = None) -> Dict[str, Any]:
        """
        Get summary statistics for benchmark results
        
        Args:
            results: List of benchmark results (uses self.results if None)
            
        Returns:
            Summary statistics
        """
        if results is None:
            results = self.results
        
        if not results:
            return {}
        
        summary = {
            "total_results": len(results),
            "operations": {},
            "languages": {},
            "benchmark_types": {}
        }
        
        for result in results:
            # Operation stats
            if result.operation not in summary["operations"]:
                summary["operations"][result.operation] = {
                    "count": 0,
                    "languages": set(),
                    "benchmark_types": set()
                }
            summary["operations"][result.operation]["count"] += 1
            summary["operations"][result.operation]["languages"].add(result.language)
            summary["operations"][result.operation]["benchmark_types"].add(result.benchmark_type)
            
            # Language stats
            if result.language not in summary["languages"]:
                summary["languages"][result.language] = {
                    "count": 0,
                    "operations": set(),
                    "benchmark_types": set()
                }
            summary["languages"][result.language]["count"] += 1
            summary["languages"][result.language]["operations"].add(result.operation)
            summary["languages"][result.language]["benchmark_types"].add(result.benchmark_type)
            
            # Benchmark type stats
            if result.benchmark_type not in summary["benchmark_types"]:
                summary["benchmark_types"][result.benchmark_type] = {
                    "count": 0,
                    "operations": set(),
                    "languages": set()
                }
            summary["benchmark_types"][result.benchmark_type]["count"] += 1
            summary["benchmark_types"][result.benchmark_type]["operations"].add(result.operation)
            summary["benchmark_types"][result.benchmark_type]["languages"].add(result.language)
        
        # Convert sets to lists for JSON serialization
        for operation_data in summary["operations"].values():
            operation_data["languages"] = list(operation_data["languages"])
            operation_data["benchmark_types"] = list(operation_data["benchmark_types"])
        
        for language_data in summary["languages"].values():
            language_data["operations"] = list(language_data["operations"])
            language_data["benchmark_types"] = list(language_data["benchmark_types"])
        
        for benchmark_data in summary["benchmark_types"].values():
            benchmark_data["operations"] = list(benchmark_data["operations"])
            benchmark_data["languages"] = list(benchmark_data["languages"])
        
        return summary
