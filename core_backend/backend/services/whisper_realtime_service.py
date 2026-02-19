"""
Real-time Whisper ASR Service for Twi/Akan languages
Provides streaming transcription with WebSocket support
"""

import torch
import torchaudio
import numpy as np
import asyncio
import logging
from typing import Optional, Dict, List, Any, AsyncGenerator, Tuple
from datetime import datetime
import io
import base64
import json
from queue import Queue
import threading
import time

# Try to import Whisper and related libraries
try:
    import whisper
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper not installed. Install with: pip install openai-whisper faster-whisper")

try:
    import webrtcvad
    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False
    logging.warning("WebRTC VAD not installed. Install with: pip install webrtcvad")

logger = logging.getLogger(__name__)


class WhisperRealtimeService:
    """Real-time ASR service using Whisper for Twi/Akan languages"""
    
    def __init__(self, model_size: str = "base", language: str = "en", device: str = "auto"):  # Use English for now as Twi not directly supported
        """
        Initialize Whisper real-time service
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            language: Target language code (tw for Twi)
            device: Device to use (cuda, cpu, auto)
        """
        self.model_size = model_size
        self.language = language
        
        # Determine device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Initializing Whisper {model_size} on {self.device}")
        
        # Initialize models
        self.model = None
        self.faster_model = None
        self._init_models()
        
        # VAD for speech detection
        self.vad = None
        if VAD_AVAILABLE:
            self.vad = webrtcvad.Vad(2)  # Aggressiveness level 2
            
        # Audio buffer for streaming
        self.audio_buffer = []
        self.sample_rate = 16000
        
        # Streaming parameters
        self.chunk_duration = 1.0  # Process 1 second chunks
        self.silence_threshold = 0.5  # Seconds of silence to trigger processing
        self.max_buffer_duration = 30.0  # Maximum buffer duration
        
        # Processing state
        self.is_processing = False
        self.last_speech_time = time.time()
        
    def _init_models(self):
        """Initialize Whisper models"""
        if not WHISPER_AVAILABLE:
            logger.error("Whisper not available")
            return
            
        try:
            # Initialize faster-whisper for streaming
            self.faster_model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type="int8" if self.device == "cpu" else "float16"
            )
            logger.info("Faster-whisper model loaded")
            
            # Load standard Whisper for batch processing
            self.model = whisper.load_model(self.model_size, device=self.device)
            logger.info("Standard Whisper model loaded")
            
        except Exception as e:
            logger.error(f"Failed to load Whisper models: {e}")
            
    async def transcribe_audio(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Transcribe audio data
        
        Args:
            audio_data: Audio array
            sample_rate: Sample rate
            language: Language code override
            
        Returns:
            Transcription result
        """
        if not self.faster_model:
            return {
                "text": "[Model not loaded]",
                "confidence": 0.0,
                "language": language or self.language,
                "segments": []
            }
            
        try:
            # Resample if needed
            if sample_rate != self.sample_rate:
                audio_data = self._resample_audio(audio_data, sample_rate, self.sample_rate)
                
            # Use faster-whisper for transcription
            # Map Twi language codes to closest supported language
            lang = language or self.language
            if lang in ["tw", "ak", "akan", "twi"]:
                lang = None  # Let Whisper auto-detect
            
            segments, info = self.faster_model.transcribe(
                audio_data,
                language=lang,
                beam_size=5,
                best_of=5,
                temperature=0.0
            )
            
            # Process segments
            result_segments = []
            full_text = []
            
            for segment in segments:
                seg_dict = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "confidence": segment.avg_logprob
                }
                result_segments.append(seg_dict)
                full_text.append(segment.text)
                
            return {
                "text": " ".join(full_text).strip(),
                "confidence": info.language_probability if hasattr(info, 'language_probability') else 0.95,
                "language": info.language if hasattr(info, 'language') else (language or self.language),
                "segments": result_segments,
                "duration": len(audio_data) / self.sample_rate
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {
                "text": f"[Error: {str(e)}]",
                "confidence": 0.0,
                "language": language or self.language,
                "segments": []
            }
            
    async def process_audio_stream(
        self,
        audio_chunk: bytes,
        sample_rate: int = 16000,
        return_partial: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Process audio stream chunk by chunk
        
        Args:
            audio_chunk: Audio chunk bytes
            sample_rate: Sample rate
            return_partial: Return partial transcriptions
            
        Returns:
            Transcription result or None if buffering
        """
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Add to buffer
        self.audio_buffer.append(audio_array)
        
        # Check if we should process
        buffer_duration = len(np.concatenate(self.audio_buffer)) / sample_rate
        
        # Process if buffer is large enough or silence detected
        should_process = False
        
        if buffer_duration >= self.chunk_duration:
            if self._detect_silence(audio_array):
                # Silence detected, check duration
                silence_duration = time.time() - self.last_speech_time
                if silence_duration >= self.silence_threshold:
                    should_process = True
            else:
                # Speech detected
                self.last_speech_time = time.time()
                
                # Process if buffer is getting too large
                if buffer_duration >= self.max_buffer_duration:
                    should_process = True
                elif return_partial and buffer_duration >= self.chunk_duration * 2:
                    should_process = True
                    
        if should_process and not self.is_processing:
            self.is_processing = True
            
            # Concatenate buffer
            full_audio = np.concatenate(self.audio_buffer)
            
            # Clear buffer for next chunk
            self.audio_buffer = []
            
            # Transcribe
            result = await self.transcribe_audio(full_audio, sample_rate)
            
            self.is_processing = False
            
            # Add streaming metadata
            result["is_partial"] = return_partial
            result["timestamp"] = datetime.now().isoformat()
            
            return result
            
        return None
        
    def _detect_silence(self, audio_chunk: np.ndarray, threshold: float = 0.01) -> bool:
        """
        Detect if audio chunk is silence
        
        Args:
            audio_chunk: Audio array
            threshold: Energy threshold for silence
            
        Returns:
            True if silence detected
        """
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        return rms < threshold
        
    def _resample_audio(
        self,
        audio: np.ndarray,
        orig_sr: int,
        target_sr: int
    ) -> np.ndarray:
        """
        Resample audio to target sample rate
        
        Args:
            audio: Audio array
            orig_sr: Original sample rate
            target_sr: Target sample rate
            
        Returns:
            Resampled audio
        """
        if orig_sr == target_sr:
            return audio
            
        # Convert to tensor
        audio_tensor = torch.from_numpy(audio).unsqueeze(0)
        
        # Resample
        resampler = torchaudio.transforms.Resample(orig_sr, target_sr)
        resampled = resampler(audio_tensor)
        
        return resampled.squeeze(0).numpy()
        
    async def stream_transcribe(
        self,
        audio_generator: AsyncGenerator[bytes, None],
        sample_rate: int = 16000
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream transcription from audio generator
        
        Args:
            audio_generator: Async generator yielding audio chunks
            sample_rate: Sample rate
            
        Yields:
            Transcription results
        """
        self.audio_buffer = []
        self.last_speech_time = time.time()
        
        async for audio_chunk in audio_generator:
            result = await self.process_audio_stream(
                audio_chunk,
                sample_rate,
                return_partial=True
            )
            
            if result:
                yield result
                
        # Process any remaining audio
        if self.audio_buffer:
            full_audio = np.concatenate(self.audio_buffer)
            result = await self.transcribe_audio(full_audio, sample_rate)
            result["is_final"] = True
            yield result
            
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return [
            "tw",  # Twi
            "ak",  # Akan
            "ee",  # Ewe
            "gaa", # Ga
            "en",  # English (for code-switching)
        ]
        
    def reset_buffer(self):
        """Reset audio buffer for new session"""
        self.audio_buffer = []
        self.last_speech_time = time.time()
        self.is_processing = False


# Singleton service instance
_whisper_service = None


def get_whisper_service(
    model_size: str = "base",
    language: str = "tw",
    device: str = "auto"
) -> WhisperRealtimeService:
    """
    Get or create Whisper service instance
    
    Args:
        model_size: Model size
        language: Target language
        device: Device to use
        
    Returns:
        WhisperRealtimeService instance
    """
    global _whisper_service
    
    if _whisper_service is None:
        _whisper_service = WhisperRealtimeService(model_size, language, device)
        
    return _whisper_service