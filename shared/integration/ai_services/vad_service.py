"""
Real-time Voice Activity Detection using Silero VAD

Provides enterprise-grade VAD for continuous voice conversation systems.
Processes raw PCM audio chunks and detects speech/silence with minimal latency.

Features:
- Silero VAD model (< 1ms per 30ms chunk)
- Configurable speech/silence thresholds
- Smart endpointing for natural conversation flow
- Session management for multi-turn conversations
- State tracking across utterances

Usage:
    >>> from shared.integration.ai_services.vad_service import VADSession
    >>> session = VADSession("user-123")
    >>> session.start_listening()
    >>> is_speech, complete, audio = session.process_chunk(pcm_samples)
    >>> if complete:
    >>>     # Utterance finished, transcribe audio
    >>>     transcription = await stt_service.transcribe(audio)
"""

try:
    import torch
    TORCH_AVAILABLE = torch is not None and hasattr(torch, 'hub')
except ImportError:
    torch = None
    TORCH_AVAILABLE = False
import numpy as np
from typing import Tuple, Optional, Dict, Any
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class VoiceActivityDetector:
    """
    Server-side VAD using Silero model.

    Processes 16kHz mono PCM chunks and maintains conversation state.
    Designed for continuous streaming with automatic utterance segmentation.

    Attributes:
        sample_rate: Audio sample rate (default 16000 Hz)
        threshold: Speech probability threshold 0-1 (default 0.5)
        min_speech_duration_ms: Minimum speech before considering "started"
        min_silence_duration_ms: Silence needed to end utterance
        speech_pad_ms: Padding around speech segments
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        threshold: float = 0.5,  # Speech probability threshold (0-1)
        min_speech_duration_ms: int = 250,  # Minimum speech before considering "started"
        min_silence_duration_ms: int = 1500,  # Silence needed to end utterance
        speech_pad_ms: int = 100,  # Padding around speech segments
        max_utterance_duration_s: int = 30  # Maximum utterance duration before forcing completion
    ):
        """
        Initialize VAD with Silero model.

        Args:
            sample_rate: Audio sample rate in Hz
            threshold: Speech detection threshold (0-1), higher = more conservative
            min_speech_duration_ms: Min speech duration to consider utterance started
            min_silence_duration_ms: Silence duration to trigger utterance end
            speech_pad_ms: Padding before/after speech segments
            max_utterance_duration_s: Max duration before forcing completion

        Raises:
            ImportError: If torch is not available
        """
        # Check torch availability before proceeding
        if not TORCH_AVAILABLE:
            raise ImportError(
                "PyTorch is required for Silero VAD. "
                "Install with: pip install torch"
            )

        self.sample_rate = sample_rate
        self.threshold = threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.min_silence_duration_ms = min_silence_duration_ms
        self.speech_pad_ms = speech_pad_ms
        self.max_utterance_duration_s = max_utterance_duration_s

        # Load Silero VAD model
        logger.info("📦 Loading Silero VAD model...")
        try:
            self.model, self.utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False  # Use PyTorch version for better accuracy
            )
            self.model.eval()

            # 🚀 torch.compile optimization (HF best practice: 20-30% speedup)
            if torch.cuda.is_available():
                logger.info("🚀 Compiling VAD model with torch.compile for 20-30% speedup...")
                self.model = torch.compile(
                    self.model,
                    mode="reduce-overhead"  # Optimized for repeated inference
                )

            logger.info(f"✅ Silero VAD model loaded (threshold={threshold}, min_silence={min_silence_duration_ms}ms)")
        except Exception as e:
            logger.error(f"❌ Failed to load Silero VAD model: {e}")
            raise

        # State tracking
        self.reset()

    def reset(self):
        """Reset VAD state for new conversation turn."""
        self.is_speaking = False
        self.speech_start_time = None
        self.silence_start_time = None
        self.accumulated_pcm = []
        self.total_samples = 0
        self.start_timestamp = datetime.now()
        logger.debug("🔄 VAD state reset")

    def _run_vad_on_window(self, audio_window: np.ndarray) -> float:
        """
        Run Silero VAD on a properly-sized window.

        Silero requires exactly 512 samples for 16kHz or 256 for 8kHz.

        Args:
            audio_window: Exactly 512 samples (16kHz) or 256 samples (8kHz)

        Returns:
            Speech probability (0-1)
        """
        # Silero VAD window size
        window_size = 512 if self.sample_rate == 16000 else 256

        if len(audio_window) != window_size:
            logger.warning(
                f"⚠️  Audio window has {len(audio_window)} samples, "
                f"expected {window_size} for {self.sample_rate}Hz. Padding/truncating."
            )
            if len(audio_window) < window_size:
                # Pad with zeros
                audio_window = np.pad(
                    audio_window,
                    (0, window_size - len(audio_window)),
                    mode='constant'
                )
            else:
                # Truncate
                audio_window = audio_window[:window_size]

        # Convert to torch tensor
        if isinstance(audio_window, np.ndarray):
            audio_tensor = torch.from_numpy(audio_window)
        else:
            audio_tensor = audio_window

        # Ensure correct dtype
        if audio_tensor.dtype != torch.float32:
            audio_tensor = audio_tensor.float()

        # Run VAD inference
        try:
            with torch.no_grad():
                speech_prob = self.model(audio_tensor, self.sample_rate).item()
        except Exception as e:
            logger.error(f"❌ VAD inference error: {e}")
            # Fallback: assume silence on error
            speech_prob = 0.0

        return speech_prob

    def process_chunk(
        self,
        pcm_chunk: np.ndarray  # Float32 array, 16kHz mono
    ) -> Tuple[bool, bool, Optional[np.ndarray]]:
        """
        Process a PCM chunk and update VAD state.

        Silero VAD requires exactly 512 samples (30ms @ 16kHz) per inference.
        This method splits large chunks into 512-sample windows, processes each,
        and aggregates results.

        Args:
            pcm_chunk: Float32 PCM samples, normalized to [-1.0, 1.0], any length

        Returns:
            Tuple of (is_speech, utterance_complete, complete_audio)
            - is_speech: True if ANY window in chunk contains speech
            - utterance_complete: True if silence detected, utterance is complete
            - complete_audio: Complete accumulated PCM if utterance_complete, else None
        """
        # Silero requires 512 samples (30ms) at 16kHz or 256 at 8kHz
        window_size = 512 if self.sample_rate == 16000 else 256

        # Split chunk into 512-sample windows
        num_windows = len(pcm_chunk) // window_size
        remainder = len(pcm_chunk) % window_size

        # Process each window and aggregate speech probabilities
        speech_probs = []

        for i in range(num_windows):
            window_start = i * window_size
            window_end = window_start + window_size
            window = pcm_chunk[window_start:window_end]

            prob = self._run_vad_on_window(window)
            speech_probs.append(prob)

        # Process remainder if exists (pad to window_size)
        if remainder > 0:
            window = pcm_chunk[-remainder:]
            prob = self._run_vad_on_window(window)  # Will be padded inside
            speech_probs.append(prob)

        # If no windows were processed (chunk too small), process as-is
        if len(speech_probs) == 0:
            prob = self._run_vad_on_window(pcm_chunk)
            speech_probs.append(prob)

        # Aggregate: Consider speech if ANY window exceeds threshold
        max_speech_prob = max(speech_probs)
        avg_speech_prob = sum(speech_probs) / len(speech_probs)
        is_speech = max_speech_prob >= self.threshold

        chunk_duration_ms = len(pcm_chunk) / self.sample_rate * 1000

        logger.debug(
            f"🎤 VAD: max_prob={max_speech_prob:.3f}, avg_prob={avg_speech_prob:.3f}, "
            f"is_speech={is_speech}, windows={len(speech_probs)}, "
            f"chunk_ms={chunk_duration_ms:.0f}, total_samples={self.total_samples}"
        )

        # Accumulate chunk
        self.accumulated_pcm.append(pcm_chunk if isinstance(pcm_chunk, np.ndarray) else pcm_chunk.numpy())
        self.total_samples += len(pcm_chunk)

        # Check max duration timeout
        elapsed_seconds = (datetime.now() - self.start_timestamp).total_seconds()
        if elapsed_seconds >= self.max_utterance_duration_s:
            logger.warning(
                f"⏰ Max utterance duration ({self.max_utterance_duration_s}s) reached, "
                f"forcing completion"
            )
            complete_audio = np.concatenate(self.accumulated_pcm) if self.accumulated_pcm else None
            self.reset()
            return False, True, complete_audio

        # State machine for speech/silence detection
        if is_speech:
            # Speech detected
            if not self.is_speaking:
                # Speech started
                self.is_speaking = True
                self.speech_start_time = self.total_samples / self.sample_rate
                logger.info(f"🗣️  Speech STARTED at {self.speech_start_time:.2f}s (prob={speech_prob:.3f})")

            # Reset silence counter when speech detected
            self.silence_start_time = None

        else:
            # Silence detected
            if self.is_speaking:
                # We were speaking, now silent
                if self.silence_start_time is None:
                    # First silence chunk after speech
                    self.silence_start_time = self.total_samples / self.sample_rate
                    logger.debug(f"🔇 Silence started at {self.silence_start_time:.2f}s (prob={speech_prob:.3f})")

                # Check if silence duration exceeds threshold
                current_time = self.total_samples / self.sample_rate
                silence_duration_ms = (current_time - self.silence_start_time) * 1000

                if silence_duration_ms >= self.min_silence_duration_ms:
                    # Utterance complete!
                    speech_duration_ms = (self.silence_start_time - self.speech_start_time) * 1000
                    logger.info(
                        f"✅ Utterance COMPLETE: "
                        f"speech={speech_duration_ms:.0f}ms, "
                        f"silence={silence_duration_ms:.0f}ms, "
                        f"total_samples={self.total_samples}, "
                        f"total_duration={(current_time):.2f}s"
                    )

                    # Combine accumulated PCM
                    complete_audio = np.concatenate(self.accumulated_pcm)

                    # Reset state for next utterance
                    self.reset()

                    return False, True, complete_audio

        # Continue accumulating
        return is_speech, False, None

    def force_complete(self) -> Optional[np.ndarray]:
        """
        Force completion of current utterance (e.g., timeout, user stop).

        Returns:
            Accumulated PCM audio or None if no audio accumulated
        """
        if len(self.accumulated_pcm) == 0:
            logger.debug("⚠️  Force complete called but no audio accumulated")
            return None

        total_duration = self.total_samples / self.sample_rate
        logger.info(
            f"⏹️  Force completing utterance: "
            f"{self.total_samples} samples, "
            f"{total_duration:.2f}s duration"
        )
        complete_audio = np.concatenate(self.accumulated_pcm)
        self.reset()
        return complete_audio

    def get_state(self) -> Dict[str, Any]:
        """
        Get current VAD state for debugging/monitoring.

        Returns:
            Dictionary with current state information
        """
        elapsed_seconds = (datetime.now() - self.start_timestamp).total_seconds()
        return {
            "is_speaking": self.is_speaking,
            "total_samples": self.total_samples,
            "total_duration_s": self.total_samples / self.sample_rate,
            "elapsed_realtime_s": elapsed_seconds,
            "speech_start_time": self.speech_start_time,
            "silence_start_time": self.silence_start_time,
            "accumulated_chunks": len(self.accumulated_pcm),
            "threshold": self.threshold,
            "min_silence_ms": self.min_silence_duration_ms
        }


class VADSession:
    """
    Manages a VAD session for a WebSocket conversation.

    Handles multiple conversation turns, maintaining state between
    user utterances and assistant responses.

    Usage:
        >>> session = VADSession("user-123")
        >>> session.start_listening()
        >>> is_speech, complete, audio = session.process_chunk(pcm_data)
        >>> if complete:
        >>>     # Process complete utterance
        >>>     transcription = await stt(audio)
        >>>     session.stop_listening()  # Stop while assistant speaks
        >>> # After assistant responds:
        >>> session.start_listening()  # Resume for next turn
    """

    def __init__(
        self,
        session_id: str,
        threshold: float = 0.5,
        min_silence_duration_ms: int = 1500,
        max_utterance_duration_s: int = 30
    ):
        """
        Initialize VAD session.

        Args:
            session_id: Unique identifier for this session
            threshold: Speech detection threshold (0-1)
            min_silence_duration_ms: Silence duration to end utterance
            max_utterance_duration_s: Max duration before forcing completion
        """
        self.session_id = session_id
        self.vad = VoiceActivityDetector(
            threshold=threshold,
            min_silence_duration_ms=min_silence_duration_ms,
            max_utterance_duration_s=max_utterance_duration_s
        )
        self.turn_count = 0
        self.created_at = datetime.now()
        self.is_listening = False
        logger.info(
            f"📞 VAD session created: {session_id} "
            f"(threshold={threshold}, min_silence={min_silence_duration_ms}ms)"
        )

    def start_listening(self):
        """Start a new listening turn."""
        self.vad.reset()
        self.turn_count += 1
        self.is_listening = True
        logger.info(f"🎤 Session {self.session_id}: Turn #{self.turn_count} started")

    def process_chunk(
        self,
        pcm_chunk: np.ndarray
    ) -> Tuple[bool, bool, Optional[np.ndarray]]:
        """
        Process PCM chunk and return VAD results.

        Args:
            pcm_chunk: Float32 PCM samples, 16kHz mono

        Returns:
            Tuple of (is_speech, utterance_complete, complete_audio)
        """
        if not self.is_listening:
            logger.warning(f"⚠️  Session {self.session_id}: process_chunk called but not listening")
            return False, False, None

        return self.vad.process_chunk(pcm_chunk)

    def stop_listening(self) -> Optional[np.ndarray]:
        """
        Stop listening and return any accumulated audio.

        Returns:
            Accumulated PCM audio or None
        """
        self.is_listening = False
        logger.info(f"⏹️  Session {self.session_id}: Stopped listening")
        return self.vad.force_complete()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get session statistics for monitoring.

        Returns:
            Dictionary with session stats
        """
        session_duration = (datetime.now() - self.created_at).total_seconds()
        vad_state = self.vad.get_state()

        return {
            "session_id": self.session_id,
            "turn_count": self.turn_count,
            "is_listening": self.is_listening,
            "session_duration_s": session_duration,
            "created_at": self.created_at.isoformat(),
            "vad_state": vad_state
        }

    def cleanup(self):
        """Cleanup resources."""
        logger.info(
            f"🧹 VAD session cleanup: {self.session_id} "
            f"(turns={self.turn_count}, duration={((datetime.now() - self.created_at).total_seconds()):.1f}s)"
        )
        self.vad = None


# Convenience functions for quick usage

def create_vad_session(
    session_id: Optional[str] = None,
    **kwargs
) -> VADSession:
    """
    Create a new VAD session with optional custom parameters.

    Args:
        session_id: Optional session ID (auto-generated if not provided)
        **kwargs: Additional parameters for VADSession

    Returns:
        Initialized VADSession
    """
    if session_id is None:
        session_id = f"vad-{uuid.uuid4().hex[:8]}"

    return VADSession(session_id, **kwargs)


def process_pcm_stream(
    pcm_stream: np.ndarray,
    sample_rate: int = 16000,
    threshold: float = 0.5,
    min_silence_duration_ms: int = 1500
) -> list:
    """
    Process a complete PCM stream and extract all utterances.

    Useful for batch processing of recorded audio files.

    Args:
        pcm_stream: Complete audio as Float32 array
        sample_rate: Sample rate (default 16000)
        threshold: Speech detection threshold
        min_silence_duration_ms: Silence duration to segment

    Returns:
        List of (start_sample, end_sample, audio_segment) tuples
    """
    vad = VoiceActivityDetector(
        sample_rate=sample_rate,
        threshold=threshold,
        min_silence_duration_ms=min_silence_duration_ms
    )

    utterances = []
    chunk_size = int(sample_rate * 0.5)  # 500ms chunks

    for i in range(0, len(pcm_stream), chunk_size):
        chunk = pcm_stream[i:i + chunk_size]
        is_speech, complete, audio = vad.process_chunk(chunk)

        if complete and audio is not None:
            # Calculate start/end samples for this utterance
            start_sample = i + chunk_size - len(audio)
            end_sample = i + chunk_size
            utterances.append((start_sample, end_sample, audio))
            vad.reset()  # Reset for next utterance

    # Handle any remaining audio
    remaining = vad.force_complete()
    if remaining is not None and len(remaining) > 0:
        start_sample = len(pcm_stream) - len(remaining)
        end_sample = len(pcm_stream)
        utterances.append((start_sample, end_sample, remaining))

    logger.info(f"📊 Extracted {len(utterances)} utterances from stream")
    return utterances


__all__ = [
    'VoiceActivityDetector',
    'VADSession',
    'create_vad_session',
    'process_pcm_stream'
]
