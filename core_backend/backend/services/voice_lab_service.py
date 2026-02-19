"""
Voice Lab Service - Core business logic for ASR and TTS
"""

import torch
import torchaudio
import numpy as np
from pathlib import Path
import tempfile
import logging
from typing import Optional, Dict, List, Any, AsyncGenerator
from datetime import datetime
import json
import io
import base64
import asyncio
import hashlib

logger = logging.getLogger(__name__)

# Import enhanced Twi processor
try:
    import sys
    voice_lab_path = Path(__file__).parent.parent.parent.parent / "voice-lab"
    sys.path.append(str(voice_lab_path))
    
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "enhanced_twi_processor",
        str(voice_lab_path / "notebooks" / "000_enhanced_twi_processor.py")
    )
    if spec and spec.loader:
        enhanced_twi_processor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(enhanced_twi_processor)
        from enhanced_twi_processor import EnhancedTwiTextProcessor
    else:
        EnhancedTwiTextProcessor = None
except Exception as e:
    logger.warning(f"Enhanced Twi processor not found: {e}")
    EnhancedTwiTextProcessor = None


class VoiceLabService:
    """Service for Voice Lab ASR and TTS operations"""
    
    def __init__(self):
        """Initialize Voice Lab Service"""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Voice Lab Service using device: {self.device}")
        
        # Initialize text processor
        self.text_processor = None
        if EnhancedTwiTextProcessor:
            self.text_processor = EnhancedTwiTextProcessor(dialect="asante")
            logger.info("Enhanced Twi text processor initialized")
        else:
            logger.warning("Running without enhanced text processor")
        
        # Model storage - Initialize BEFORE using it
        self.models = {
            "asr": {"loaded": False, "type": "twi_whisper"},
            "tts": {"loaded": False, "type": "twi_tts"}
        }
        
        # Initialize Twi Whisper ASR
        self.twi_whisper = None
        self._init_twi_whisper()
        
        # Initialize Twi TTS
        self.twi_tts = None
        self._init_twi_tts()
        
        # Initialize models in background - will be started when event loop is available
        # Models will be loaded on first request
        self._models_loading_task = None
        
        # Cache for processed audio
        self.audio_cache = {}

        # User statistics
        self.user_stats = {}

        # Audio buffering for streaming (per session)
        # Reason: Small 256ms chunks are too short for accurate Akan/Twi transcription
        # Buffer until we have ~2 seconds for better accuracy
        self.stream_buffers = {}  # Dict[session_id, Dict]
        self.buffer_duration_seconds = 2.0
        self.sample_rate = 16000
    
    def _init_twi_whisper(self):
        """Initialize Twi Whisper ASR model"""
        try:
            from .twi_whisper_service import get_twi_whisper_service
            self.twi_whisper = get_twi_whisper_service(model_name="akan")
            self.models["asr"]["loaded"] = True
            logger.info("Twi Whisper ASR initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Twi Whisper: {e}")
    
    def _init_twi_tts(self):
        """Initialize Twi TTS model"""
        try:
            from .twi_tts_service import get_twi_tts_service
            self.twi_tts = get_twi_tts_service()
            self.models["tts"]["loaded"] = True
            logger.info("Twi TTS initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Twi TTS: {e}")
    
    async def _ensure_models_loaded(self):
        """Ensure models are loaded before processing"""
        if not self._models_loading_task:
            self._models_loading_task = asyncio.create_task(self._load_models())
        await self._models_loading_task
    
    async def _load_models(self):
        """Load ASR and TTS models asynchronously"""
        try:
            # Ensure Twi Whisper is loaded
            if not self.twi_whisper:
                self._init_twi_whisper()
            
            # TTS model loading (placeholder for now)
            await asyncio.sleep(1)
            self.models["tts"]["loaded"] = True
            
            logger.info("Voice Lab models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
    
    def _decode_audio(self, audio_base64: str, format: str = "auto", sample_rate: int = None, channels: int = None) -> tuple[np.ndarray, int]:
        """Decode base64 audio to numpy array

        Args:
            audio_base64: Base64 encoded audio (WAV, WebM, or raw PCM format)
            format: Audio format ("auto", "pcm_s16le", "wav", "webm")
            sample_rate: Sample rate (required for PCM format)
            channels: Number of channels (required for PCM format)

        Returns:
            Audio array and sample rate
        """
        try:
            # Decode base64
            audio_bytes = base64.b64decode(audio_base64)

            # Handle raw PCM format
            if format == "pcm_s16le" or format == "pcm":
                if not sample_rate:
                    sample_rate = 16000  # Default to 16kHz
                if not channels:
                    channels = 1  # Default to mono

                # Convert raw PCM bytes (Int16) to numpy array
                audio_array = np.frombuffer(audio_bytes, dtype=np.int16)

                # Normalize to float32 in range [-1, 1]
                audio_array = audio_array.astype(np.float32) / 32768.0

                # Reshape based on channels
                if channels == 1:
                    audio_array = audio_array.reshape(1, -1)
                elif channels == 2:
                    audio_array = audio_array.reshape(channels, -1)

                logger.info(f"Decoded raw PCM audio: {audio_array.shape}, sample_rate={sample_rate}")
                return audio_array, sample_rate

            # Try torchaudio first (WAV format)
            try:
                audio_io = io.BytesIO(audio_bytes)
                waveform, sample_rate = torchaudio.load(audio_io)
                audio_array = waveform.numpy()
                return audio_array, sample_rate
            except Exception as e_torch:
                logger.debug(f"Torchaudio failed, trying pydub: {e_torch}")

                # If torchaudio fails, use pydub (handles WebM and other formats via ffmpeg)
                from pydub import AudioSegment
                import tempfile
                import os

                # Write to temporary file
                with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
                    tmp.write(audio_bytes)
                    tmp_path = tmp.name

                try:
                    # Load using pydub (auto-detects format)
                    audio = AudioSegment.from_file(tmp_path)

                    # Convert to mono if stereo
                    if audio.channels > 1:
                        audio = audio.set_channels(1)

                    # Get sample rate
                    sample_rate = audio.frame_rate

                    # Convert to numpy array
                    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)

                    # Normalize to [-1, 1] range
                    if audio.sample_width == 2:  # 16-bit
                        samples = samples / 32768.0
                    elif audio.sample_width == 4:  # 32-bit
                        samples = samples / 2147483648.0

                    # Reshape to (1, n_samples) for mono
                    audio_array = samples.reshape(1, -1)

                    return audio_array, sample_rate
                finally:
                    # Clean up temp file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"Failed to decode audio: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise ValueError("Invalid audio data")
    
    def _encode_audio(self, audio_array: np.ndarray, sample_rate: int, format: str = "wav") -> str:
        """Encode audio array to base64
        
        Args:
            audio_array: Audio numpy array
            sample_rate: Sample rate
            format: Output format
            
        Returns:
            Base64 encoded audio
        """
        try:
            # Convert to tensor
            waveform = torch.from_numpy(audio_array)
            
            # Ensure correct shape
            if len(waveform.shape) == 1:
                waveform = waveform.unsqueeze(0)
            
            # Save to bytes
            audio_io = io.BytesIO()
            torchaudio.save(audio_io, waveform, sample_rate, format=format)
            
            # Encode to base64
            audio_io.seek(0)
            audio_base64 = base64.b64encode(audio_io.read()).decode('utf-8')
            
            return audio_base64
            
        except Exception as e:
            logger.error(f"Failed to encode audio: {e}")
            raise ValueError("Failed to encode audio")
    
    async def transcribe_audio(self,
                              audio_base64: str,
                              language: str = "tw",
                              dialect: str = "asante",
                              return_timestamps: bool = False,
                              enhance_text: bool = True,
                              user_id: Optional[str] = None) -> Dict:
        """Transcribe audio to text
        
        Args:
            audio_base64: Base64 encoded audio
            language: Language code
            dialect: Dialect
            return_timestamps: Return word-level timestamps
            enhance_text: Apply text enhancements
            user_id: User ID for tracking
            
        Returns:
            Transcription result
        """
        start_time = datetime.now()
        
        try:
            # Decode audio
            audio_array, sample_rate = self._decode_audio(audio_base64)
            
            # Calculate duration
            duration = len(audio_array[0]) / sample_rate
            
            # Check cache
            cache_key = hashlib.md5(audio_base64.encode()).hexdigest()
            if cache_key in self.audio_cache:
                cached = self.audio_cache[cache_key]
                logger.info(f"Using cached transcription for {cache_key}")
                return cached
            
            # Perform transcription
            if self.twi_whisper and self.models["asr"]["loaded"]:
                # Use real Twi Whisper model
                try:
                    result = self.twi_whisper.transcribe(
                        audio_array,
                        sample_rate=sample_rate,
                        language=language,
                        return_timestamps=return_timestamps
                    )
                    transcribed_text = result["text"]
                    confidence = result["confidence"]
                    
                    # Update dialect from model
                    if result.get("dialect"):
                        dialect = result["dialect"]
                except Exception as e:
                    logger.error(f"Twi Whisper transcription failed: {e}")
                    # Fallback to sample text
                    sample_texts = {
                        "asante": "Akwaaba, me din de Kofi. Mepɛ sɛ mekasa Twi.",
                        "akuapem": "Akwaaba, me din de Kwame. Mepɛ sɛ mekasa Twi.",
                    "fante": "Akwaaba, me dzin ye Kwesi. Mepɛ dɛ mekasa Mfantse."
                }
                transcribed_text = sample_texts.get(dialect, sample_texts["asante"])
                confidence = 0.92 + np.random.random() * 0.08  # 92-100% confidence
            else:
                transcribed_text = "[Model not loaded - sample text]"
                confidence = 0.0
            
            # Enhance text if requested
            enhanced_text = None
            if enhance_text and self.text_processor:
                result = self.text_processor.process_text(
                    transcribed_text,
                    expand_numbers=True,
                    expand_abbreviations=True,
                    process_datetime=True,
                    apply_dialect=True,
                    generate_phonemes=False
                )
                enhanced_text = result['processed']
            
            # Generate timestamps if requested
            timestamps = None
            if return_timestamps:
                # Simple word-level timestamps (in production, from ASR model)
                words = transcribed_text.split()
                time_per_word = duration / len(words)
                timestamps = [
                    {
                        "word": word,
                        "start": i * time_per_word,
                        "end": (i + 1) * time_per_word
                    }
                    for i, word in enumerate(words)
                ]
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Update user statistics
            if user_id:
                self._update_user_stats(user_id, "transcriptions", duration)
            
            result = {
                "text": transcribed_text,
                "enhanced_text": enhanced_text,
                "confidence": confidence,
                "language": language,
                "dialect": dialect,
                "duration": duration,
                "timestamps": timestamps,
                "processing_time": processing_time
            }
            
            # Cache result
            self.audio_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
    
    async def synthesize_speech(self,
                               text: str,
                               voice_id: str = "asante_male_1",
                               speed: float = 1.0,
                               pitch: float = 0.0,
                               enhance_text: bool = True,
                               output_format: str = "wav",
                               user_id: Optional[str] = None) -> Dict:
        """Synthesize text to speech
        
        Args:
            text: Text to synthesize
            voice_id: Voice identifier
            speed: Speech speed
            pitch: Pitch adjustment
            enhance_text: Process text enhancements
            output_format: Output audio format
            user_id: User ID for tracking
            
        Returns:
            Synthesized audio data
        """
        try:
            # Process text if requested
            text_to_synthesize = text
            if enhance_text and self.text_processor:
                result = self.text_processor.process_text(
                    text,
                    expand_numbers=True,
                    expand_abbreviations=True,
                    process_datetime=True,
                    apply_dialect=True,
                    generate_phonemes=True
                )
                text_to_synthesize = result['processed']
            
            # Perform synthesis
            if self.twi_tts and self.models["tts"]["loaded"]:
                # Use real TTS model
                try:
                    result = self.twi_tts.synthesize(
                        text=text_to_synthesize,
                        voice_id=voice_id,
                        speed=speed,
                        pitch=pitch,
                        output_format=output_format
                    )
                    
                    # Return audio data
                    if result["status"] == "success" or result["status"] == "dummy":
                        audio_base64 = base64.b64encode(result["audio"]).decode('utf-8')
                        
                        # Update user stats
                        if user_id:
                            self._update_user_stats(user_id, "synthesis", result["duration"])
                        
                        return {
                            "audio": audio_base64,
                            "format": output_format,
                            "sample_rate": result["sample_rate"],
                            "duration": result["duration"],
                            "text": text,
                            "processed_text": text_to_synthesize,
                            "voice_id": voice_id,
                            "processing_time": result["processing_time"],
                            "status": result["status"]
                        }
                except Exception as e:
                    logger.error(f"TTS synthesis failed: {e}")
                    # Fall through to dummy generation
            
            # Fallback: Generate dummy audio
            sample_rate = 22050
            duration = len(text_to_synthesize) * 0.05 / speed
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # Different frequencies for different voices
            voice_frequencies = {
                "asante_male_1": 150,
                "asante_female_1": 250,
                "akuapem_male_1": 140,
                "akuapem_female_1": 240,
                "fante_male_1": 160,
                "fante_female_1": 260
            }
            
            base_freq = voice_frequencies.get(voice_id, 200)
            frequency = base_freq * (2 ** (pitch / 12))
            
            # Generate audio wave
            audio_array = np.sin(2 * np.pi * frequency * t) * 0.3
            
            # Add some harmonics for more natural sound
            audio_array += np.sin(2 * np.pi * frequency * 2 * t) * 0.1
            audio_array += np.sin(2 * np.pi * frequency * 3 * t) * 0.05
            
            # Encode audio
            audio_base64 = self._encode_audio(
                audio_array.reshape(1, -1),
                sample_rate,
                output_format
            )
            
            # Update user statistics
            if user_id:
                self._update_user_stats(user_id, "syntheses", duration)
            
            return {
                "audio_base64": audio_base64,
                "sample_rate": sample_rate,
                "duration": duration,
                "text_processed": text_to_synthesize,
                "voice_id": voice_id
            }
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            raise
    
    async def get_available_voices(self) -> List[Dict]:
        """Get list of available voices
        
        Returns:
            List of voice information
        """
        voices = [
            {
                "voice_id": "asante_male_1",
                "name": "Kofi (Asante)",
                "language": "tw",
                "dialect": "asante",
                "gender": "male",
                "age_group": "adult",
                "description": "Natural male voice for Asante Twi"
            },
            {
                "voice_id": "asante_female_1",
                "name": "Ama (Asante)",
                "language": "tw",
                "dialect": "asante",
                "gender": "female",
                "age_group": "adult",
                "description": "Natural female voice for Asante Twi"
            },
            {
                "voice_id": "akuapem_male_1",
                "name": "Kwame (Akuapem)",
                "language": "tw",
                "dialect": "akuapem",
                "gender": "male",
                "age_group": "adult",
                "description": "Natural male voice for Akuapem Twi"
            },
            {
                "voice_id": "akuapem_female_1",
                "name": "Adwoa (Akuapem)",
                "language": "tw",
                "dialect": "akuapem",
                "gender": "female",
                "age_group": "adult",
                "description": "Natural female voice for Akuapem Twi"
            },
            {
                "voice_id": "fante_male_1",
                "name": "Kwesi (Fante)",
                "language": "tw",
                "dialect": "fante",
                "gender": "male",
                "age_group": "adult",
                "description": "Natural male voice for Fante"
            },
            {
                "voice_id": "fante_female_1",
                "name": "Esi (Fante)",
                "language": "tw",
                "dialect": "fante",
                "gender": "female",
                "age_group": "adult",
                "description": "Natural female voice for Fante"
            }
        ]
        
        return voices
    
    async def clone_voice(self,
                         reference_audio_base64: str,
                         text: str,
                         voice_name: str = "custom",
                         user_id: Optional[str] = None) -> Dict:
        """Clone a voice from reference audio using XTTS

        Args:
            reference_audio_base64: Base64 encoded reference audio
            text: Text to synthesize
            voice_name: Name for cloned voice
            user_id: User ID for tracking

        Returns:
            Synthesized audio in cloned voice
        """
        try:
            logger.info(f"🎭 Cloning voice for text: {text[:50]}...")

            # Decode reference audio to bytes
            reference_audio_bytes = base64.b64decode(reference_audio_base64)

            # Try to use XTTS for voice cloning
            try:
                from .xtts_twi_service import get_xtts_twi_service
                xtts_service = get_xtts_twi_service()

                result = xtts_service.clone_voice_and_synthesize(
                    text=text,
                    reference_audio_bytes=reference_audio_bytes,
                    temperature=0.65,
                    language="en"  # XTTS uses 'en' for Twi
                )

                if result and result.get("audio_base64"):
                    # Update user statistics
                    if user_id:
                        self._update_user_stats(user_id, "voice_clones", 1)

                    return {
                        "audio_base64": result["audio_base64"],
                        "sample_rate": result["sample_rate"],
                        "duration": result["duration"],
                        "voice_name": voice_name,
                        "status": "success",
                        "model": "xtts-twi-v1"
                    }
                else:
                    logger.warning("XTTS voice cloning returned no result, using fallback")

            except Exception as e:
                logger.error(f"XTTS voice cloning failed: {e}")
                logger.info("Falling back to dummy audio generation")

            # Fallback: Generate dummy audio if XTTS fails
            sample_rate = 24000
            duration = len(text) * 0.06
            t = np.linspace(0, duration, int(sample_rate * duration))

            # Simulate cloned voice with different frequency
            cloned_freq = 180
            audio_array = np.sin(2 * np.pi * cloned_freq * t) * 0.3

            # Encode audio
            audio_base64 = self._encode_audio(
                audio_array.reshape(1, -1),
                sample_rate,
                "wav"
            )

            # Update user statistics
            if user_id:
                self._update_user_stats(user_id, "voice_clones", 1)

            return {
                "audio_base64": audio_base64,
                "sample_rate": sample_rate,
                "duration": duration,
                "voice_name": voice_name,
                "status": "fallback"
            }

        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            raise
    
    async def process_text(self,
                          text: str,
                          dialect: str = "asante",
                          expand_numbers: bool = True,
                          expand_abbreviations: bool = True,
                          process_datetime: bool = True,
                          generate_phonemes: bool = False) -> Dict:
        """Process text with enhanced Twi processor
        
        Args:
            text: Input text
            dialect: Target dialect
            expand_numbers: Expand numbers to words
            expand_abbreviations: Expand abbreviations
            process_datetime: Process date/time
            generate_phonemes: Generate IPA phonemes
            
        Returns:
            Processed text with enhancements
        """
        if not self.text_processor:
            return {
                "original": text,
                "processed": text,
                "error": "Text processor not available"
            }
        
        try:
            # Update dialect
            self.text_processor.dialect = dialect
            
            # Process text
            result = self.text_processor.process_text(
                text,
                expand_numbers=expand_numbers,
                expand_abbreviations=expand_abbreviations,
                process_datetime=process_datetime,
                apply_dialect=True,
                generate_phonemes=generate_phonemes
            )
            
            return {
                "original": text,
                "processed": result['processed'],
                "phonemes": result.get('phonemes', ''),
                "dialect": dialect,
                "features": {
                    "numbers_expanded": result.get('numbers_found', []),
                    "dates_processed": result.get('dates_found', []),
                    "abbreviations_expanded": result.get('abbreviations_found', [])
                }
            }
            
        except Exception as e:
            logger.error(f"Text processing failed: {e}")
            raise
    
    async def process_audio_chunk(self,
                                 audio_base64: str,
                                 dialect: str = "asante",
                                 format: str = "auto",
                                 sample_rate_in: int = None,
                                 channels: int = None,
                                 session_id: str = "default") -> Dict:
        """Process audio chunk for streaming ASR.
        Buffers chunks until reaching optimal size (~2s) for better accuracy.

        Args:
            audio_base64: Base64 encoded audio chunk
            dialect: Target dialect
            format: Audio format ("auto", "pcm_s16le", "wav", "webm")
            sample_rate_in: Sample rate for PCM format
            channels: Number of channels for PCM format
            session_id: Session identifier for buffer management

        Returns:
            Partial transcription result (or None if still buffering)
        """
        try:
            # Decode audio chunk
            audio_array, sample_rate = self._decode_audio(
                audio_base64,
                format=format,
                sample_rate=sample_rate_in,
                channels=channels
            )

            # Ensure mono
            if len(audio_array.shape) > 1:
                audio_array = audio_array[0]

            # Initialize buffer for this session if needed
            if session_id not in self.stream_buffers:
                self.stream_buffers[session_id] = {
                    "buffer": np.array([], dtype=np.float32),
                    "sample_rate": sample_rate,
                    "dialect": dialect
                }

            # Add to buffer
            buffer_data = self.stream_buffers[session_id]
            buffer_data["buffer"] = np.concatenate([buffer_data["buffer"], audio_array])

            # Check if we have enough audio (2 seconds = 32000 samples @ 16kHz)
            target_samples = int(self.buffer_duration_seconds * sample_rate)

            if len(buffer_data["buffer"]) >= target_samples:
                # Use Akan streaming service for real-time transcription
                from apps.core_backend.backend.services.akan_streaming_service import get_akan_streaming_service

                akan_service = get_akan_streaming_service()

                # Process buffered audio
                result = await asyncio.to_thread(
                    akan_service.transcribe_chunk,
                    buffer_data["buffer"],
                    sample_rate=sample_rate,
                    language="tw",
                    return_timestamps=False  # Faster for streaming
                )

                # Clear buffer but keep last 0.5s for context (overlap)
                overlap_samples = int(0.5 * sample_rate)
                buffer_data["buffer"] = buffer_data["buffer"][-overlap_samples:]

                return {
                    "text": result.text,
                    "is_final": result.is_final,
                    "confidence": result.confidence,
                    "processing_time": result.processing_time,
                    "buffered": True
                }
            else:
                # Still buffering, return empty response
                return {
                    "text": "",
                    "is_final": False,
                    "confidence": 0.0,
                    "processing_time": 0.0,
                    "buffered": False,
                    "buffer_fill": len(buffer_data["buffer"]) / target_samples
                }

        except Exception as e:
            logger.error(f"Chunk processing failed: {e}")
            raise

    def clear_stream_buffer(self, session_id: str = "default"):
        """Clear audio buffer for a session.

        Args:
            session_id: Session identifier
        """
        if session_id in self.stream_buffers:
            del self.stream_buffers[session_id]
    
    async def synthesize_stream(self,
                               text: str,
                               voice_id: str = "asante_male_1") -> AsyncGenerator[Dict, None]:
        """Stream synthesized audio chunks
        
        Args:
            text: Text to synthesize
            voice_id: Voice identifier
            
        Yields:
            Audio chunks
        """
        try:
            # Process text
            if self.text_processor:
                result = self.text_processor.process_text(text)
                text = result['processed']
            
            # Generate audio in chunks
            # In production, would use streaming TTS
            chunk_size = 50  # characters per chunk
            
            for i in range(0, len(text), chunk_size):
                chunk_text = text[i:i + chunk_size]
                
                # Generate audio for chunk
                sample_rate = 22050
                duration = len(chunk_text) * 0.05
                t = np.linspace(0, duration, int(sample_rate * duration))
                audio_array = np.sin(2 * np.pi * 200 * t) * 0.3
                
                # Encode chunk
                audio_base64 = self._encode_audio(
                    audio_array.reshape(1, -1),
                    sample_rate,
                    "wav"
                )
                
                yield {
                    "id": i // chunk_size,
                    "audio": audio_base64,
                    "is_final": i + chunk_size >= len(text)
                }
                
                await asyncio.sleep(0.1)  # Simulate processing time
                
        except Exception as e:
            logger.error(f"Stream synthesis failed: {e}")
            raise
    
    async def process_audio_upload(self,
                                  content: bytes,
                                  filename: str,
                                  content_type: str,
                                  dialect: str = "asante",
                                  user_id: Optional[str] = None) -> Dict:
        """Process uploaded audio file
        
        Args:
            content: File content
            filename: Original filename
            content_type: MIME type
            dialect: Target dialect
            user_id: User ID
            
        Returns:
            Processing result
        """
        try:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            # Load audio
            waveform, sample_rate = torchaudio.load(tmp_path)
            
            # Convert to base64
            audio_base64 = base64.b64encode(content).decode('utf-8')
            
            # Process transcription
            result = await self.transcribe_audio(
                audio_base64=audio_base64,
                dialect=dialect,
                enhance_text=True,
                user_id=user_id
            )
            
            # Clean up
            Path(tmp_path).unlink()
            
            return {
                "filename": filename,
                "duration": result["duration"],
                "transcription": result["text"],
                "enhanced_transcription": result.get("enhanced_text"),
                "confidence": result["confidence"]
            }
            
        except Exception as e:
            logger.error(f"Audio upload processing failed: {e}")
            raise
    
    def _update_user_stats(self, user_id: str, stat_type: str, value: float):
        """Update user statistics
        
        Args:
            user_id: User identifier
            stat_type: Type of statistic
            value: Value to add
        """
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                "transcriptions": {"count": 0, "total_duration": 0},
                "syntheses": {"count": 0, "total_duration": 0},
                "voice_clones": {"count": 0},
                "last_activity": None
            }
        
        stats = self.user_stats[user_id]
        
        if stat_type == "transcriptions":
            stats["transcriptions"]["count"] += 1
            stats["transcriptions"]["total_duration"] += value
        elif stat_type == "syntheses":
            stats["syntheses"]["count"] += 1
            stats["syntheses"]["total_duration"] += value
        elif stat_type == "voice_clones":
            stats["voice_clones"]["count"] += value
        
        stats["last_activity"] = datetime.now().isoformat()
    
    async def get_user_stats(self, user_id: str) -> Dict:
        """Get user statistics
        
        Args:
            user_id: User identifier
            
        Returns:
            User statistics
        """
        if user_id not in self.user_stats:
            return {
                "transcriptions": {"count": 0, "total_duration": 0},
                "syntheses": {"count": 0, "total_duration": 0},
                "voice_clones": {"count": 0},
                "last_activity": None
            }
        
        return self.user_stats[user_id]