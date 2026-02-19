#!/usr/bin/env python3
"""
OpenAI Whisper Service for Ghanaian Languages
Supports transcription and translation for Twi and other Ghanaian languages
"""

import asyncio
import logging
import whisper
import torch
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class WhisperTranscriptionResult:
    """Result from Whisper transcription."""
    text: str
    language: str
    confidence: float
    duration: float
    segments: List[Dict[str, Any]]
    task: str  # 'transcribe' or 'translate'

class WhisperService:
    """Service for OpenAI Whisper models with Ghanaian language support."""
    
    def __init__(self):
        self.models_loaded = False
        self.models = {}
        
        # Ghanaian language codes supported by Whisper
        self.ghanaian_languages = {
            "twi": "tw",  # Twi (Akan)
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
        }
        
        # Whisper model configurations
        self.whisper_config = {
            "models": ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
            "default_model": "base",
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "compute_type": "float16" if torch.cuda.is_available() else "float32"
        }
    
    async def initialize(self, model_size: str = "base"):
        """Initialize Whisper models."""
        try:
            logger.info(f"🔄 Initializing Whisper model: {model_size}")
            
            if model_size not in self.whisper_config["models"]:
                raise ValueError(f"Unsupported model size: {model_size}")
            
            # Load the specified model
            model = whisper.load_model(
                model_size, 
                device=self.whisper_config["device"],
                download_root=None
            )
            
            self.models[model_size] = model
            self.models_loaded = True
            
            logger.info(f"✅ Whisper model {model_size} initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Whisper model: {e}")
            raise
    
    async def load_multiple_models(self, model_sizes: List[str] = None):
        """Load multiple Whisper models for different use cases."""
        if model_sizes is None:
            model_sizes = ["tiny", "base", "small"]
        
        for model_size in model_sizes:
            if model_size not in self.models:
                await self.initialize(model_size)
    
    async def transcribe_audio(
        self, 
        audio_path: str, 
        language: str = "auto",
        task: str = "transcribe",
        model_size: str = "base",
        prompt: str = None
    ) -> WhisperTranscriptionResult:
        """
        Transcribe audio using Whisper model.
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'twi', 'ewe', 'ga')
            task: Task type ('transcribe' or 'translate')
            model_size: Whisper model size
            prompt: Optional prompt for better transcription
            
        Returns:
            WhisperTranscriptionResult with transcription details
        """
        try:
            if not self.models_loaded or model_size not in self.models:
                await self.initialize(model_size)
            
            model = self.models[model_size]
            options = {
                "task": task,
                "language": language if language != "auto" else None,
                "fp16": False,                 # float32 is safer cross-platform
                "verbose": False,
                "logprob_threshold": -1.0,
                "no_speech_threshold": 0.6,
                "condition_on_previous_text": True,
                "initial_prompt": prompt,
                "word_timestamps": True,
                # Safe, properly quoted punctuation sets (you can tweak these)
                "prepend_punctuations": "\"'([{",
                "append_punctuations": "\"'.。，！？：:)]}、",
            }

            
            # Configure transcription options
            
           
            
            # Set language if specified
            if language != "auto" and language in self.ghanaian_languages:
                options["language"] = self.ghanaian_languages[language]
            
            # Transcribe audio
            result = model.transcribe(audio_path, **options)
            
            # Extract segments
            segments = []
            for segment in result.get("segments", []):
                segments.append({
                    "text": segment.get("text", "").strip(),
                    "start": segment.get("start", 0),
                    "end": segment.get("end", 0),
                    "confidence": segment.get("avg_logprob", 0),
                    "words": segment.get("words", [])
                })
            
            # Calculate overall confidence
            if segments:
                confidence = np.mean([seg["confidence"] for seg in segments])
            else:
                confidence = 0.0
            
            return WhisperTranscriptionResult(
                text=result.get("text", "").strip(),
                language=result.get("language", language),
                confidence=confidence,
                duration=result.get("duration", 0),
                segments=segments,
                task=task
            )
            
        except Exception as e:
            logger.error(f"Error transcribing audio with Whisper: {e}")
            raise
    
    async def translate_audio(
        self, 
        audio_path: str, 
        target_language: str = "en",
        model_size: str = "base"
    ) -> WhisperTranscriptionResult:
        """
        Translate audio to English using Whisper model.
        
        Args:
            audio_path: Path to audio file
            target_language: Target language (usually 'en' for English)
            model_size: Whisper model size
            
        Returns:
            WhisperTranscriptionResult with translation details
        """
        return await self.transcribe_audio(
            audio_path=audio_path,
            language="auto",  # Auto-detect source language
            task="translate",
            model_size=model_size
        )
    
    async def detect_language(self, audio_path: str, model_size: str = "base") -> str:
        """
        Detect language of audio using Whisper model.
        
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
            
            # Load audio and detect language
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)
            
            # Log mel spectrogram
            mel = whisper.log_mel_spectrogram(audio).to(model.device)
            
            # Detect language
            _, probs = model.detect_language(mel)
            detected_lang = max(probs, key=probs.get)
            
            # Map to our language codes
            for code, whisper_code in self.ghanaian_languages.items():
                if whisper_code == detected_lang:
                    return code
            
            return detected_lang
            
        except Exception as e:
            logger.error(f"Error detecting language with Whisper: {e}")
            return "unknown"
    
    async def get_available_languages(self) -> List[str]:
        """Get list of languages supported by Whisper."""
        try:
            if not self.models_loaded:
                await self.initialize()
            
            model = list(self.models.values())[0]
            return list(model.cond_lm.tokenizer.languages.keys())
            
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
    ) -> List[WhisperTranscriptionResult]:
        """
        Transcribe multiple audio files in batch.
        
        Args:
            audio_files: List of audio file paths
            language: Language code
            task: Task type
            model_size: Whisper model size
            
        Returns:
            List of WhisperTranscriptionResult
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
        """Get information about a Whisper model."""
        try:
            if not self.models_loaded or model_size not in self.models:
                await self.initialize(model_size)
            
            model = self.models[model_size]
            
            return {
                "model_size": model_size,
                "device": str(model.device),
                "dtype": str(model.dtype),
                "num_parameters": sum(p.numel() for p in model.parameters()),
                "supported_languages": list(model.cond_lm.tokenizer.languages.keys()),
                "supported_tasks": ["transcribe", "translate"]
            }
            
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {}

# Global instance
whisper_service = WhisperService()
