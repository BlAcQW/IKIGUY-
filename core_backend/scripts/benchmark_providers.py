#!/usr/bin/env python3
"""
Voice Agent Provider Performance Benchmark
Measures latency, throughput, and quality for all providers.

Usage:
    python3 scripts/benchmark_providers.py
    python3 scripts/benchmark_providers.py --provider llm
    python3 scripts/benchmark_providers.py --provider tts
    python3 scripts/benchmark_providers.py --provider asr
"""

import asyncio
import time
import argparse
import json
from typing import Dict, List, Any
from datetime import datetime
import numpy as np

# Add parent directory to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.unified_llm_service import unified_llm_service
from apps.shared.integration.ai_services import get_unified_tts_service, TTSModel
from backend.services.unified_asr_service import get_unified_asr_service, ASRModel


class ProviderBenchmark:
    """Benchmark suite for voice agent providers."""

    def __init__(self):
        self.results: Dict[str, List[Dict[str, Any]]] = {
            "llm": [],
            "tts": [],
            "asr": []
        }

    async def benchmark_llm_providers(self):
        """Benchmark all LLM providers."""
        print("\n" + "="*60)
        print("🧠 LLM PROVIDER BENCHMARKS")
        print("="*60)

        providers = [
            ("gemini", "gemini-2.5-flash"),
            ("openai", "gpt-4o-mini"),
            ("anthropic", "claude-3-5-sonnet-20241022"),
            ("ollama", "llama3.2:3b"),
        ]

        test_messages = [
            {"role": "user", "content": "What is the capital of Ghana?"}
        ]

        for provider, model in providers:
            print(f"\n🔍 Testing {provider}/{model}...")

            try:
                # Warm-up run
                await unified_llm_service.chat_completion(
                    messages=test_messages,
                    provider=provider,
                    model=model,
                    temperature=0.7,
                    max_tokens=50
                )

                # Benchmark runs
                latencies = []
                for i in range(3):
                    start = time.time()
                    response = await unified_llm_service.chat_completion(
                        messages=test_messages,
                        provider=provider,
                        model=model,
                        temperature=0.7,
                        max_tokens=50
                    )
                    latency = time.time() - start
                    latencies.append(latency)

                    print(f"   Run {i+1}: {latency:.2f}s")

                avg_latency = sum(latencies) / len(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)

                result = {
                    "provider": provider,
                    "model": model,
                    "avg_latency": avg_latency,
                    "min_latency": min_latency,
                    "max_latency": max_latency,
                    "response_length": len(response.get("content", "")),
                    "status": "success"
                }

                self.results["llm"].append(result)

                print(f"   ✅ Average: {avg_latency:.2f}s (min: {min_latency:.2f}s, max: {max_latency:.2f}s)")
                print(f"   📝 Response: {response.get('content', '')[:80]}...")

            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                self.results["llm"].append({
                    "provider": provider,
                    "model": model,
                    "status": "error",
                    "error": str(e)
                })

    async def benchmark_tts_providers(self):
        """Benchmark all TTS providers."""
        print("\n" + "="*60)
        print("🎙️ TTS PROVIDER BENCHMARKS")
        print("="*60)

        tts_service = get_unified_tts_service()

        models = [
            (TTSModel.AKAN_MMS, "tw"),
            (TTSModel.META_MMS_TTS, "en"),
            (TTSModel.MELOTTS, "en"),
            (TTSModel.OPENVOICE, "en"),
            (TTSModel.F5_TTS, "en"),
        ]

        test_text = "Hello, this is a test of the text to speech system."

        for model, language in models:
            print(f"\n🔍 Testing {model.value}...")

            try:
                # Benchmark runs
                latencies = []
                audio_sizes = []

                for i in range(3):
                    start = time.time()
                    result = tts_service.synthesize(
                        text=test_text,
                        model=model,
                        voice_id="default",
                        language=language,
                        speed=1.0
                    )
                    latency = time.time() - start
                    latencies.append(latency)
                    audio_sizes.append(len(result.audio_base64))

                    print(f"   Run {i+1}: {latency:.2f}s ({len(result.audio_base64)} bytes)")

                avg_latency = sum(latencies) / len(latencies)
                avg_size = sum(audio_sizes) / len(audio_sizes)

                benchmark_result = {
                    "model": model.value,
                    "language": language,
                    "avg_latency": avg_latency,
                    "min_latency": min(latencies),
                    "max_latency": max(latencies),
                    "avg_audio_size": avg_size,
                    "sample_rate": result.sample_rate,
                    "duration": result.duration,
                    "status": "success"
                }

                self.results["tts"].append(benchmark_result)

                print(f"   ✅ Average: {avg_latency:.2f}s")
                print(f"   📊 Audio: {avg_size:.0f} bytes, {result.sample_rate}Hz, {result.duration:.2f}s")

            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                self.results["tts"].append({
                    "model": model.value,
                    "status": "error",
                    "error": str(e)
                })

    async def benchmark_asr_providers(self):
        """Benchmark all ASR providers."""
        print("\n" + "="*60)
        print("🎤 ASR PROVIDER BENCHMARKS")
        print("="*60)

        asr_service = get_unified_asr_service()

        models = [
            ASRModel.AKAN_WHISPER,
            ASRModel.FASTER_WHISPER,
            ASRModel.WHISPER_LARGE_V3,
            ASRModel.META_MMS,
        ]

        # Generate 1 second of silence as test audio
        sample_rate = 16000
        test_audio = np.zeros(sample_rate, dtype=np.float32)

        for model in models:
            print(f"\n🔍 Testing {model.value}...")

            try:
                # Benchmark runs
                latencies = []

                for i in range(3):
                    start = time.time()
                    result = await asr_service.transcribe(
                        audio_data=test_audio,
                        sample_rate=sample_rate,
                        model=model,
                        language="en",
                        return_timestamps=False
                    )
                    latency = time.time() - start
                    latencies.append(latency)

                    print(f"   Run {i+1}: {latency:.2f}s (confidence: {result.confidence:.2f})")

                avg_latency = sum(latencies) / len(latencies)

                benchmark_result = {
                    "model": model.value,
                    "avg_latency": avg_latency,
                    "min_latency": min(latencies),
                    "max_latency": max(latencies),
                    "accuracy": asr_service.MODEL_CONFIGS[model].accuracy,
                    "status": "success"
                }

                self.results["asr"].append(benchmark_result)

                print(f"   ✅ Average: {avg_latency:.2f}s")
                print(f"   📊 Accuracy: {asr_service.MODEL_CONFIGS[model].accuracy}")

            except Exception as e:
                print(f"   ❌ Error (skipping): {str(e)}")
                self.results["asr"].append({
                    "model": model.value,
                    "status": "error",
                    "error": str(e)
                })

    def generate_report(self):
        """Generate benchmark report."""
        print("\n" + "="*60)
        print("📊 BENCHMARK SUMMARY")
        print("="*60)

        # LLM Summary
        if self.results["llm"]:
            print("\n🧠 LLM Providers:")
            print("   " + "-"*56)
            print(f"   {'Provider/Model':<35} {'Latency':<15} {'Status'}")
            print("   " + "-"*56)

            for result in self.results["llm"]:
                if result["status"] == "success":
                    name = f"{result['provider']}/{result['model']}"
                    latency = f"{result['avg_latency']:.2f}s"
                    print(f"   {name:<35} {latency:<15} ✅")
                else:
                    name = f"{result['provider']}/{result['model']}"
                    print(f"   {name:<35} {'N/A':<15} ❌")

        # TTS Summary
        if self.results["tts"]:
            print("\n🎙️ TTS Providers:")
            print("   " + "-"*56)
            print(f"   {'Model':<35} {'Latency':<15} {'Status'}")
            print("   " + "-"*56)

            for result in self.results["tts"]:
                if result["status"] == "success":
                    latency = f"{result['avg_latency']:.2f}s"
                    print(f"   {result['model']:<35} {latency:<15} ✅")
                else:
                    print(f"   {result['model']:<35} {'N/A':<15} ❌")

        # ASR Summary
        if self.results["asr"]:
            print("\n🎤 ASR Providers:")
            print("   " + "-"*56)
            print(f"   {'Model':<35} {'Latency':<15} {'Status'}")
            print("   " + "-"*56)

            for result in self.results["asr"]:
                if result["status"] == "success":
                    latency = f"{result['avg_latency']:.2f}s"
                    print(f"   {result['model']:<35} {latency:<15} ✅")
                else:
                    print(f"   {result['model']:<35} {'N/A':<15} ❌")

        # Recommendations
        print("\n💡 RECOMMENDATIONS")
        print("="*60)

        # Find fastest LLM
        llm_success = [r for r in self.results["llm"] if r["status"] == "success"]
        if llm_success:
            fastest_llm = min(llm_success, key=lambda x: x["avg_latency"])
            print(f"\n🏆 Fastest LLM: {fastest_llm['provider']}/{fastest_llm['model']}")
            print(f"   Latency: {fastest_llm['avg_latency']:.2f}s")

        # Find fastest TTS
        tts_success = [r for r in self.results["tts"] if r["status"] == "success"]
        if tts_success:
            fastest_tts = min(tts_success, key=lambda x: x["avg_latency"])
            print(f"\n🏆 Fastest TTS: {fastest_tts['model']}")
            print(f"   Latency: {fastest_tts['avg_latency']:.2f}s")

        # Find fastest ASR
        asr_success = [r for r in self.results["asr"] if r["status"] == "success"]
        if asr_success:
            fastest_asr = min(asr_success, key=lambda x: x["avg_latency"])
            print(f"\n🏆 Fastest ASR: {fastest_asr['model']}")
            print(f"   Latency: {fastest_asr['avg_latency']:.2f}s")

        print("\n" + "="*60)

    def save_report(self, filename: str = "benchmark_results.json"):
        """Save benchmark results to JSON file."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "results": self.results
        }

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Results saved to: {filename}")


async def main():
    parser = argparse.ArgumentParser(description="Benchmark voice agent providers")
    parser.add_argument(
        "--provider",
        choices=["llm", "tts", "asr", "all"],
        default="all",
        help="Which providers to benchmark"
    )
    parser.add_argument(
        "--output",
        default="benchmark_results.json",
        help="Output file for results"
    )

    args = parser.parse_args()

    benchmark = ProviderBenchmark()

    if args.provider in ["llm", "all"]:
        await benchmark.benchmark_llm_providers()

    if args.provider in ["tts", "all"]:
        await benchmark.benchmark_tts_providers()

    if args.provider in ["asr", "all"]:
        await benchmark.benchmark_asr_providers()

    benchmark.generate_report()
    benchmark.save_report(args.output)


if __name__ == "__main__":
    asyncio.run(main())
