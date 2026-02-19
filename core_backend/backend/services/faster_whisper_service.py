#!/usr/bin/env python3
"""
Faster Whisper Service for Ghanaian Languages
Uses faster-whisper library for improved performance
Supports transcription and translation for Twi and other Ghanaian languages
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json
from dataclasses import dataclass
import numpy as np
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

@dataclass
class FasterWhisperTranscriptionResult:
    """Result from Faster Whisper transcription."""
    text: str
    language: str
    confidence: float
    duration: float
    segments: List[Dict[str, Any]]
    task: str  # 'transcribe' or 'translate'

class FasterWhisperService:
    """Service for Faster Whisper models with Ghanaian language support."""
    
    def __init__(self):
        self.models_loaded = False
        self.models = {}

        # Ghanaian language codes supported by Whisper
        self.ghanaian_languages = {
            "twi": "tw",  # Twi (Akan)
            "tw": "tw",   # Twi alias
            "asante_twi": "tw",  # Asante Twi
            "akuapem_twi": "tw",  # Akuapem Twi
            "ewe": "ee",  # Ewe
            "ga": "ga",    # Ga
            "dagbani": "dag",  # Dagbani
            "hausa": "ha",  # Hausa
            "yoruba": "yo",  # Yoruba
            "igbo": "ig",  # Igbo
            "swahili": "sw",  # Swahili
            "english": "en",  # English
            "en": "en",   # English alias
            "auto": "auto"  # Auto-detect
        }

        # Akan Whisper model (Gift Mark) - best for Twi with 92.9% accuracy
        self.akan_model_path = "/opt/kasaai/apps/voice-lab/models/akan_whisper"
        self.akan_model = None
        self.akan_processor = None

        # Faster Whisper model configurations
        self.whisper_config = {
            "models": ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
            "default_model": "base",
            "device": "cpu",  # Use CPU - CUDA driver version issue
            "compute_type": "int8"  # Use int8 for CPU performance
        }
    
    async def initialize(self, model_size: str = "base"):
        """Initialize Faster Whisper models."""
        try:
            logger.info(f"🔄 Initializing Faster Whisper model: {model_size}")
            
            if model_size not in self.whisper_config["models"]:
                raise ValueError(f"Unsupported model size: {model_size}")
            
            # Load the specified model using faster-whisper
            model = WhisperModel(
                model_size_or_path=model_size,
                device=self.whisper_config["device"],
                compute_type=self.whisper_config["compute_type"]
            )
            
            self.models[model_size] = model
            self.models_loaded = True
            
            logger.info(f"✅ Faster Whisper model {model_size} initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Faster Whisper model: {e}")
            raise
    
    async def initialize_akan_model(self):
        """Initialize Gift Mark Akan Whisper model for Twi transcription."""
        try:
            logger.info(f"🔄 Initializing Gift Mark Akan Whisper model...")

            from transformers import WhisperProcessor, WhisperForConditionalGeneration
            import os

            if not os.path.exists(self.akan_model_path):
                logger.warning(f"⚠️ Akan model not found at {self.akan_model_path}")
                return False

            # Load Akan Whisper model
            self.akan_processor = WhisperProcessor.from_pretrained(self.akan_model_path)
            self.akan_model = WhisperForConditionalGeneration.from_pretrained(self.akan_model_path)

            # 🚀 torch.compile optimization (HF best practice: 20-30% speedup)
            import torch
            if torch.cuda.is_available():
                logger.info("🚀 Compiling Akan Whisper model with torch.compile for 20-30% speedup...")
                self.akan_model = torch.compile(
                    self.akan_model,
                    mode="reduce-overhead"  # Optimized for repeated inference
                )

            logger.info(f"✅ Akan Whisper model initialized (92.9% accuracy on Twi)")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Akan model: {e}")
            return False

    async def load_multiple_models(self, model_sizes: List[str] = None):
        """Load multiple Faster Whisper models for different use cases."""
        if model_sizes is None:
            model_sizes = ["tiny", "base", "small"]

        for model_size in model_sizes:
            if model_size not in self.models:
                await self.initialize(model_size)

        # Also load Akan model for Twi support
        if not self.akan_model:
            await self.initialize_akan_model()
    
    async def transcribe_with_akan_model(self, audio_path: str) -> FasterWhisperTranscriptionResult:
        """
        Transcribe audio using the Gift Mark Akan Whisper model (92.9% accuracy).
        Optimized for Twi/Akan languages.
        """
        try:
            import torch
            import librosa

            if not self.akan_model or not self.akan_processor:
                logger.info("🔄 Loading Akan model on-demand...")
                success = await self.initialize_akan_model()
                if not success:
                    raise Exception("Failed to load Akan model")

            logger.info(f"🎤 Transcribing with Akan Whisper model: {audio_path}")

            # Load audio with librosa
            audio, sr = librosa.load(audio_path, sr=16000)

            # Limit to 30 seconds
            max_duration = 30
            if len(audio) > max_duration * 16000:
                audio = audio[:max_duration * 16000]

            # Process audio
            inputs = self.akan_processor(audio, sampling_rate=16000, return_tensors="pt")

            # Generate transcription
            with torch.no_grad():
                predicted_ids = self.akan_model.generate(inputs.input_features)

            # Decode
            transcription = self.akan_processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

            logger.info(f"✅ Akan transcription: '{transcription[:100]}...'")

            # Return in standard format
            return FasterWhisperTranscriptionResult(
                text=transcription,
                language="tw",  # Twi/Akan
                confidence=0.929,  # Model's reported accuracy
                duration=len(audio) / 16000.0,
                segments=[{
                    "text": transcription,
                    "start": 0.0,
                    "end": len(audio) / 16000.0,
                    "confidence": 0.929
                }],
                task="transcribe"
            )

        except Exception as e:
            logger.error(f"❌ Error in Akan transcription: {e}")
            raise

    async def transcribe_audio(
        self,
        audio_path: str,
        language: str = "auto",
        task: str = "transcribe",
        model_size: str = "base",
        prompt: str = None
    ) -> FasterWhisperTranscriptionResult:
        """
        Transcribe audio using appropriate Whisper model.
        Uses Gift Mark Akan model for Twi, Faster Whisper for others.

        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'twi', 'ewe', 'ga', 'auto')
            task: Task type ('transcribe' or 'translate')
            model_size: Whisper model size
            prompt: Optional prompt for better transcription

        Returns:
            FasterWhisperTranscriptionResult with transcription details
        """
        try:
            # Use Akan model for Twi/Akan languages
            if language.lower() in ['twi', 'tw', 'akan']:
                logger.info("🎯 Using Gift Mark Akan model for Twi transcription")
                return await self.transcribe_with_akan_model(audio_path)

            # Use Faster Whisper for other languages
            if not self.models_loaded or model_size not in self.models:
                await self.initialize(model_size)

            model = self.models[model_size]
            
            # Configure transcription options for faster-whisper
            options = {
                "task": task,
                "language": language if language != "auto" else None,
                "initial_prompt": prompt,
                "word_timestamps": True,
                "vad_filter": True,
                "vad_parameters": {
                    "min_silence_duration_ms": 500,
                    "speech_pad_ms": 400
                }
            }
            
            # Set language if specified
            if language != "auto" and language in self.ghanaian_languages:
                options["language"] = self.ghanaian_languages[language]
            
            # Transcribe audio using faster-whisper
            segments, info = model.transcribe(audio_path, **options)
            
            # Extract text and segments
            text = ""
            segments_list = []
            total_confidence = 0.0
            segment_count = 0
            
            for segment in segments:
                segment_text = segment.text.strip()
                text += segment_text + " "
                
                segment_data = {
                    "text": segment_text,
                    "start": segment.start,
                    "end": segment.end,
                    "confidence": segment.avg_logprob if hasattr(segment, 'avg_logprob') else 0.0,
                    "words": []
                }
                
                # Add word-level timestamps if available
                if hasattr(segment, 'words') and segment.words:
                    for word in segment.words:
                        segment_data["words"].append({
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                            "probability": word.probability
                        })
                
                segments_list.append(segment_data)
                total_confidence += segment_data["confidence"]
                segment_count += 1
            
            # Calculate overall confidence
            confidence = total_confidence / segment_count if segment_count > 0 else 0.0
            
            return FasterWhisperTranscriptionResult(
                text=text.strip(),
                language=info.language if hasattr(info, 'language') else language,
                confidence=confidence,
                duration=info.duration if hasattr(info, 'duration') else 0.0,
                segments=segments_list,
                task=task
            )
            
        except Exception as e:
            logger.error(f"Error transcribing audio with Faster Whisper: {e}")
            raise
    
    async def translate_audio(
        self, 
        audio_path: str, 
        target_language: str = "en",
        model_size: str = "base"
    ) -> FasterWhisperTranscriptionResult:
        """
        Translate audio to English using Faster Whisper model.
        
        Args:
            audio_path: Path to audio file
            target_language: Target language (usually 'en' for English)
            model_size: Whisper model size
            
        Returns:
            FasterWhisperTranscriptionResult with translation details
        """
        return await self.transcribe_audio(
            audio_path=audio_path,
            language="auto",  # Auto-detect source language
            task="translate",
            model_size=model_size
        )
    
    async def detect_language(self, audio_path: str, model_size: str = "base") -> str:
        """
        Detect language of audio using Faster Whisper model.
        
        Args:
            audio_path: Path to audio file
            model_size: Whisper model size
            
        Returns:
            Detected language code
        """
        try:
            if not self.models_loaded or model_size not in self.models:
                await self.initialize(model_size)
            
            model = self.models[model_size]
            
            # Use faster-whisper's language detection
            segments, info = model.transcribe(audio_path, task="transcribe", language=None)
            
            # Get detected language
            detected_lang = info.language if hasattr(info, 'language') else "unknown"
            
            # Map to our language codes
            for code, whisper_code in self.ghanaian_languages.items():
                if whisper_code == detected_lang:
                    return code
            
            return detected_lang
            
        except Exception as e:
            logger.error(f"Error detecting language with Faster Whisper: {e}")
            return "unknown"
    
    async def get_available_languages(self) -> List[str]:
        """Get list of languages supported by Faster Whisper."""
        try:
            if not self.models_loaded:
                await self.initialize()
            
            # faster-whisper doesn't expose languages directly, so we return common ones
            common_languages = [
                "en", "es", "fr", "de", "it", "pt", "pl", "ru", "ja", "ko", "zh", "ar",
                "tw", "ee", "ga", "dag", "ha", "yo", "ig", "sw"
            ]
            return common_languages
            
        except Exception as e:
            logger.error(f"Error getting available languages: {e}")
            return []
    
    def get_supported_ghanaian_languages(self) -> List[str]:
        """Get list of supported Ghanaian languages."""
        return list(self.ghanaian_languages.keys())
    
    def get_language_code(self, language: str) -> Optional[str]:
        """Get Whisper language code for given language."""
        return self.ghanaian_languages.get(language.lower())
    
    async def batch_transcribe(
        self, 
        audio_files: List[str], 
        language: str = "auto",
        task: str = "transcribe",
        model_size: str = "base"
    ) -> List[FasterWhisperTranscriptionResult]:
        """
        Transcribe multiple audio files in batch.
        
        Args:
            audio_files: List of audio file paths
            language: Language code
            task: Task type
            model_size: Whisper model size
            
        Returns:
            List of FasterWhisperTranscriptionResult
        """
        results = []
        for audio_file in audio_files:
            try:
                result = await self.transcribe_audio(
                    audio_path=audio_file,
                    language=language,
                    task=task,
                    model_size=model_size
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error transcribing {audio_file}: {e}")
                results.append(None)
        
        return results
    
    async def get_model_info(self, model_size: str = "base") -> Dict[str, Any]:
        """Get information about a Faster Whisper model."""
        try:
            if not self.models_loaded or model_size not in self.models:
                await self.initialize(model_size)
            
            model = self.models[model_size]
            
            return {
                "model_size": model_size,
                "device": str(model.device) if hasattr(model, 'device') else "auto",
                "compute_type": self.whisper_config["compute_type"],
                "supported_languages": await self.get_available_languages(),
                "supported_tasks": ["transcribe", "translate"],
                "library": "faster-whisper"
            }
            
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {}

# Global instance
_faster_whisper_service = None


def get_faster_whisper_service() -> FasterWhisperService:
    """
    Get singleton FasterWhisperService instance.

    Returns:
        FasterWhisperService: The FasterWhisper service
    """
    global _faster_whisper_service
    if _faster_whisper_service is None:
        _faster_whisper_service = FasterWhisperService()
    return _faster_whisper_service


# Legacy global instance for backward compatibility
faster_whisper_service = get_faster_whisper_service()
