"""
Latency Optimization Service for Voice Conversations

Implements strategies to minimize end-to-end latency in voice conversations:
1. Streaming TTS with early audio playback
2. Parallel LLM + TTS processing
3. Adaptive chunk sizing
4. Pre-buffering strategies
5. Network optimization

Target latencies:
- STT: < 500ms
- LLM: < 1000ms (with streaming)
- TTS: < 300ms (first chunk)
- Total E2E: < 2000ms
"""

import asyncio
import time
from typing import Dict, Any, Callable, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OptimizationStrategy(str, Enum):
    """Latency optimization strategies."""
    ULTRA_LOW_LATENCY = "ultra_low_latency"  # Sacrifice quality for speed
    BALANCED = "balanced"  # Balance quality and latency
    HIGH_QUALITY = "high_quality"  # Prioritize quality over latency


class LatencyOptimizer:
    """
    Optimizes voice conversation latency through various strategies.
    """

    # Optimal chunk sizes for different providers (bytes)
    CHUNK_SIZES = {
        "elevenlabs": 1024,  # Small chunks for streaming
        "openai": 4096,  # Larger chunks OK for OpenAI
        "meta_mms": 2048,
        "coqui_xtts": 2048,
        "default": 2048
    }

    # Buffer sizes (number of chunks to buffer before playback)
    BUFFER_SIZES = {
        OptimizationStrategy.ULTRA_LOW_LATENCY: 1,  # Play immediately
        OptimizationStrategy.BALANCED: 2,  # Buffer 2 chunks
        OptimizationStrategy.HIGH_QUALITY: 3,  # Buffer 3 chunks
    }

    @classmethod
    def get_chunk_size(cls, tts_provider: str) -> int:
        """
        Get optimal chunk size for a TTS provider.

        Smaller chunks = lower latency but more overhead
        Larger chunks = higher latency but more efficient

        Args:
            tts_provider: TTS provider ID

        Returns:
            Optimal chunk size in bytes
        """
        provider_lower = (tts_provider or "").lower()
        return cls.CHUNK_SIZES.get(provider_lower, cls.CHUNK_SIZES["default"])

    @classmethod
    def get_buffer_size(cls, strategy: OptimizationStrategy = OptimizationStrategy.BALANCED) -> int:
        """
        Get buffer size for a given strategy.

        Args:
            strategy: Optimization strategy

        Returns:
            Number of chunks to buffer
        """
        return cls.BUFFER_SIZES.get(strategy, 2)

    @classmethod
    def should_stream_llm(cls, llm_provider: str) -> bool:
        """
        Determine if LLM should stream responses.

        Streaming reduces perceived latency by starting TTS earlier.

        Args:
            llm_provider: LLM provider ID

        Returns:
            True if streaming is supported and beneficial
        """
        streaming_providers = {
            "openai",  # GPT models support streaming
            "anthropic",  # Claude supports streaming
            "gemini",  # Gemini supports streaming
        }

        provider_lower = (llm_provider or "").lower()
        return any(p in provider_lower for p in streaming_providers)

    @classmethod
    async def parallel_llm_tts(
        cls,
        llm_func: Callable,
        tts_func: Callable,
        on_llm_chunk: Optional[Callable] = None,
        on_tts_chunk: Optional[Callable] = None,
        min_tokens_before_tts: int = 10
    ) -> Dict[str, Any]:
        """
        Execute LLM and TTS in parallel for lowest latency.

        Strategy:
        1. Start LLM streaming
        2. As soon as we have min_tokens, start TTS for that chunk
        3. Continue streaming both in parallel
        4. Client starts playing audio as soon as first TTS chunk arrives

        Args:
            llm_func: Async function that yields LLM tokens
            tts_func: Async function that converts text to audio
            on_llm_chunk: Callback for each LLM chunk
            on_tts_chunk: Callback for each TTS audio chunk
            min_tokens_before_tts: Minimum tokens before starting TTS

        Returns:
            Dictionary with timing metrics
        """
        start_time = time.time()
        timings = {
            "llm_first_token": None,
            "tts_first_chunk": None,
            "total_time": None
        }

        llm_buffer = []
        tts_tasks = []

        try:
            # Stream LLM response
            async for token in llm_func():
                if timings["llm_first_token"] is None:
                    timings["llm_first_token"] = time.time() - start_time

                llm_buffer.append(token)

                if on_llm_chunk:
                    await on_llm_chunk(token)

                # Start TTS when we have enough tokens
                if len(llm_buffer) >= min_tokens_before_tts:
                    text_chunk = "".join(llm_buffer)
                    llm_buffer = []

                    # Start TTS task in parallel
                    tts_task = asyncio.create_task(
                        cls._process_tts_chunk(
                            tts_func,
                            text_chunk,
                            on_tts_chunk,
                            timings,
                            start_time
                        )
                    )
                    tts_tasks.append(tts_task)

            # Process remaining buffer
            if llm_buffer:
                text_chunk = "".join(llm_buffer)
                tts_task = asyncio.create_task(
                    cls._process_tts_chunk(
                        tts_func,
                        text_chunk,
                        on_tts_chunk,
                        timings,
                        start_time
                    )
                )
                tts_tasks.append(tts_task)

            # Wait for all TTS tasks to complete
            if tts_tasks:
                await asyncio.gather(*tts_tasks)

        except Exception as e:
            logger.error(f"Error in parallel LLM+TTS: {e}")

        timings["total_time"] = time.time() - start_time
        return timings

    @classmethod
    async def _process_tts_chunk(
        cls,
        tts_func: Callable,
        text: str,
        on_tts_chunk: Optional[Callable],
        timings: Dict,
        start_time: float
    ):
        """Process a single TTS chunk."""
        try:
            audio_chunks = await tts_func(text)

            for chunk in audio_chunks:
                if timings["tts_first_chunk"] is None:
                    timings["tts_first_chunk"] = time.time() - start_time

                if on_tts_chunk:
                    await on_tts_chunk(chunk)

        except Exception as e:
            logger.error(f"Error processing TTS chunk: {e}")

    @classmethod
    def get_optimization_config(
        cls,
        tts_provider: str,
        strategy: OptimizationStrategy = OptimizationStrategy.BALANCED
    ) -> Dict[str, Any]:
        """
        Get complete optimization configuration.

        Args:
            tts_provider: TTS provider ID
            strategy: Optimization strategy

        Returns:
            Dictionary with optimization settings
        """
        return {
            "chunk_size": cls.get_chunk_size(tts_provider),
            "buffer_size": cls.get_buffer_size(strategy),
            "enable_streaming": True,
            "parallel_processing": strategy != OptimizationStrategy.HIGH_QUALITY,
            "early_playback": strategy == OptimizationStrategy.ULTRA_LOW_LATENCY,
        }

    @classmethod
    def measure_latency(cls, stage_name: str):
        """
        Context manager to measure latency for a specific stage.

        Usage:
            async with LatencyOptimizer.measure_latency("stt") as timer:
                result = await transcribe_audio()
            print(f"STT took {timer.elapsed}ms")
        """
        return LatencyTimer(stage_name)


class LatencyTimer:
    """Context manager for measuring latency."""

    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.start_time = None
        self.end_time = None
        self.elapsed = None

    async def __aenter__(self):
        self.start_time = time.time()
        logger.debug(f"[Latency] {self.stage_name} started")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.elapsed = (self.end_time - self.start_time) * 1000  # Convert to ms
        logger.info(f"[Latency] {self.stage_name} completed in {self.elapsed:.2f}ms")
        return False


# Singleton instance
latency_optimizer = LatencyOptimizer()
