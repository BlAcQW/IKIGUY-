"""
Streaming TTS Service using Parler-TTS

Provides real-time text-to-speech synthesis with streaming output
to reduce perceived latency in voice conversations.

Based on HuggingFace speech-to-speech best practices:
- Uses Parler-TTS for high-quality streaming synthesis
- Sentence-level chunking for immediate audio output
- torch.compile optimization for 20-30% speedup
- Async generator pattern for efficient streaming

Usage:
    from apps.shared.integration.ai_services import StreamingTTSService

    tts = StreamingTTSService()
    async for audio_chunk in tts.stream_tts(
        text="Hello, how can I help you today?",
        voice_description="A friendly female voice"
    ):
        # Send audio_chunk to client
        await websocket.send(audio_chunk)
"""

try:
    import torch
except ImportError:
    torch = None  # Make torch optional
import numpy as np
import logging
import re
from typing import AsyncGenerator, Optional
from threading import Thread
import asyncio

logger = logging.getLogger(__name__)


class StreamingTTSService:
    """
    Streaming TTS using Parler-TTS for low-latency voice synthesis.

    Features:
    - Sentence-level streaming (user hears audio immediately)
    - torch.compile optimization
    - Async generator pattern
    - Reusable across all apps
    """

    def __init__(
        self,
        model_name: str = "parler-tts/parler-tts-mini-v1",
        device: str = "cuda" if (torch and torch.cuda.is_available()) else "cpu",
        compile_model: bool = True
    ):
        """
        Initialize Streaming TTS Service.

        Args:
            model_name: Parler-TTS model to use
            device: Device to run model on (cuda/cpu)
            compile_model: Whether to use torch.compile for speedup
        """
        self.device = device
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.compile_model = compile_model

        logger.info(f"🎙️  Initializing StreamingTTSService on {device}")
        self._load_model()

    def _load_model(self):
        """Load Parler-TTS model and tokenizer."""
        try:
            from parler_tts import ParlerTTSForConditionalGeneration, ParlerTTSStreamer
            from transformers import AutoTokenizer

            logger.info(f"📦 Loading Parler-TTS model: {self.model_name}")

            # Load model
            self.model = ParlerTTSForConditionalGeneration.from_pretrained(
                self.model_name
            ).to(self.device)

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            # Get model's native sample rate from config
            self.model_sample_rate = getattr(self.model.config.audio_encoder, 'sampling_rate', 44100)
            logger.info(f"🎵 Model native sample rate: {self.model_sample_rate} Hz")

            # torch.compile optimization (20-30% speedup)
            if self.compile_model and self.device == "cuda":
                logger.info("🚀 Compiling Parler-TTS model with torch.compile...")
                self.model = torch.compile(
                    self.model,
                    mode="reduce-overhead"  # Options: reduce-overhead, default, max-autotune
                )

            logger.info("✅ Parler-TTS model loaded successfully")

        except ImportError as e:
            logger.error(f"❌ Failed to import Parler-TTS: {e}")
            logger.error("Install with: pip install parler-tts")
            raise

        except Exception as e:
            logger.error(f"❌ Failed to load Parler-TTS model: {e}")
            raise

    def _split_into_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences for streaming.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        # Filter out empty strings
        sentences = [s.strip() for s in sentences if s.strip()]

        # If no sentence boundaries found, split by length
        if len(sentences) == 0 or (len(sentences) == 1 and len(sentences[0]) > 200):
            # Split long text into chunks
            words = text.split()
            sentences = []
            current = []
            for word in words:
                current.append(word)
                if len(' '.join(current)) > 100:
                    sentences.append(' '.join(current))
                    current = []
            if current:
                sentences.append(' '.join(current))

        logger.debug(f"📝 Split text into {len(sentences)} sentences")
        return sentences

    async def stream_tts(
        self,
        text: str,
        voice_description: str = "A clear, neutral voice",
        sample_rate: int = 16000
    ) -> AsyncGenerator[np.ndarray, None]:
        """
        Stream TTS audio in real-time, sentence by sentence.

        Args:
            text: Text to synthesize
            voice_description: Description of voice for Parler-TTS
            sample_rate: Output sample rate

        Yields:
            Audio chunks as numpy arrays (float32, [-1, 1] range)
        """
        if not text or not text.strip():
            logger.warning("⚠️  Empty text provided, skipping TTS")
            return

        logger.info(f"🎵 Starting streaming TTS: {len(text)} chars, {text[:50]}...")

        # Split into sentences for streaming
        sentences = self._split_into_sentences(text)

        for i, sentence in enumerate(sentences):
            logger.debug(f"🔊 Synthesizing sentence {i+1}/{len(sentences)}: {sentence[:50]}...")

            try:
                # Synthesize sentence
                audio = await self._synthesize_sentence(
                    sentence,
                    voice_description,
                    sample_rate
                )

                if audio is not None and len(audio) > 0:
                    yield audio
                    logger.debug(f"✅ Sentence {i+1} complete: {len(audio)} samples")

            except Exception as e:
                logger.error(f"❌ Error synthesizing sentence {i+1}: {e}")
                # Continue with next sentence instead of failing completely
                continue

        logger.info(f"🎉 Streaming TTS complete: {len(sentences)} sentences")

    async def _synthesize_sentence(
        self,
        text: str,
        voice_description: str,
        sample_rate: int = 16000
    ) -> Optional[np.ndarray]:
        """
        Synthesize a single sentence.

        Args:
            text: Sentence to synthesize
            voice_description: Voice description
            sample_rate: Output sample rate

        Returns:
            Audio as numpy array or None on error
        """
        try:
            # Tokenize
            input_ids = self.tokenizer(
                voice_description,
                return_tensors="pt"
            ).input_ids.to(self.device)

            prompt_input_ids = self.tokenizer(
                text,
                return_tensors="pt"
            ).input_ids.to(self.device)

            # Generate audio (blocking operation, run in thread pool)
            loop = asyncio.get_event_loop()
            audio = await loop.run_in_executor(
                None,
                self._generate_audio_sync,
                input_ids,
                prompt_input_ids
            )

            # Convert to numpy float32 in [-1, 1] range
            if torch and isinstance(audio, torch.Tensor):
                audio = audio.cpu().numpy()

            # Ensure float32 and normalized
            audio = audio.astype(np.float32)
            if audio.max() > 1.0:
                audio = audio / 32768.0  # Convert from int16 range

            return audio

        except Exception as e:
            logger.error(f"❌ Error in sentence synthesis: {e}")
            return None

    def _generate_audio_sync(self, input_ids, prompt_input_ids):
        """Synchronous audio generation (called in thread pool)."""
        if not torch:
            raise RuntimeError("torch is required for TTS generation but is not installed")

        with torch.no_grad():
            generation = self.model.generate(
                input_ids=input_ids,
                prompt_input_ids=prompt_input_ids,
                max_new_tokens=1000,
                do_sample=True,
                temperature=1.0
            )
            # Get audio from generation output
            audio = generation.squeeze(0)
            return audio

    def get_native_sample_rate(self) -> int:
        """
        Get the model's native sample rate.

        Returns:
            Sample rate in Hz (e.g., 44100)
        """
        return getattr(self, 'model_sample_rate', 44100)

    def get_voice_descriptions(self) -> dict[str, str]:
        """
        Get available voice descriptions for Parler-TTS.

        Returns:
            Dictionary of voice names to descriptions
        """
        return {
            "neutral": "A clear, neutral voice",
            "friendly_female": "A friendly female voice with a warm tone",
            "professional_male": "A professional male voice with clear pronunciation",
            "enthusiastic": "An enthusiastic, energetic voice",
            "calm": "A calm, soothing voice",
            "fast": "A quick-paced voice",
            "slow": "A slow, deliberate voice",
        }

    def cleanup(self):
        """Cleanup resources."""
        if self.model is not None:
            del self.model
            self.model = None

        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None

        if torch and torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info("🧹 StreamingTTSService cleaned up")


# Singleton instance for reuse across requests
_streaming_tts_instance: Optional[StreamingTTSService] = None


def get_streaming_tts_service(
    model_name: str = "parler-tts/parler-tts-mini-v1",
    device: str = "cuda" if (torch and torch.cuda.is_available()) else "cpu"
) -> StreamingTTSService:
    """
    Get or create singleton StreamingTTSService instance.

    Args:
        model_name: Parler-TTS model to use
        device: Device to run on

    Returns:
        StreamingTTSService instance
    """
    global _streaming_tts_instance

    if _streaming_tts_instance is None:
        logger.info("🎙️  Creating new StreamingTTSService instance")
        _streaming_tts_instance = StreamingTTSService(
            model_name=model_name,
            device=device
        )

    return _streaming_tts_instance


__all__ = [
    'StreamingTTSService',
    'get_streaming_tts_service'
]
