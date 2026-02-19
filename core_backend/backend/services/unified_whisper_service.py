#!/usr/bin/env python3
"""
Unified Whisper Service for Ghanaian Languages
Can switch between OpenAI Whisper and Faster Whisper implementations
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class UnifiedWhisperTranscriptionResult:
    """Unified result from Whisper transcription."""
    text: str
    language: str
    confidence: float
    duration: float
    segments: List[Dict[str, Any]]
    task: str  # 'transcribe' or 'translate'
    implementation: str  # 'openai_whisper' or 'faster_whisper'

class UnifiedWhisperService:
    """Unified service that can switch between Whisper implementations."""
    
    def __init__(self, use_faster_whisper: bool = None, use_api: bool = None):
        """
        Initialize the unified whisper service.
        
        Args:
            use_faster_whisper: Whether to use faster-whisper (deprecated, use use_api instead)
            use_api: Whether to use RunPod API (default: True). If False, uses local faster_whisper_service
        """
        # Check if we should use API (default: True to use RunPod service)
        if use_api is None:
            use_api = os.getenv("WHISPER_USE_API", "true").lower() == "true"
        
        self.use_api = use_api
        self.use_faster_whisper = use_faster_whisper  # Keep for backward compatibility
        
        # Use API client by default (RunPod service at whisper.ailabsafrica.com)
        if self.use_api:
            try:
                from .whisper_api_client import get_whisper_api_client
                self.service = get_whisper_api_client(default_model="base")
                self.implementation = "faster_whisper_api"
                logger.info("✅ Using Faster Whisper API (RunPod service at whisper.ailabsafrica.com)")
            except Exception as e:
                logger.warning(f"Whisper API not available: {e}, falling back to local Faster Whisper")
                from .faster_whisper_service import faster_whisper_service
                self.service = faster_whisper_service
                self.implementation = "faster_whisper"
        else:
            # Use local faster_whisper_service
            if self.use_faster_whisper is None:
                # Check environment variable
                implementation = os.getenv("WHISPER_IMPLEMENTATION", "faster_whisper").lower()
                self.use_faster_whisper = implementation == "faster_whisper"
            
            if self.use_faster_whisper:
                try:
                    from .faster_whisper_service import faster_whisper_service
                    self.service = faster_whisper_service
                    self.implementation = "faster_whisper"
                    logger.info("✅ Using local Faster Whisper implementation")
                except ImportError as e:
                    logger.warning(f"Faster Whisper not available: {e}, falling back to OpenAI Whisper")
                    from .whisper_service import whisper_service
                    self.service = whisper_service
                    self.implementation = "openai_whisper"
            else:
                try:
                    from .whisper_service import whisper_service
                    self.service = whisper_service
                    self.implementation = "openai_whisper"
                    logger.info("✅ Using OpenAI Whisper implementation")
                except ImportError as e:
                    logger.warning(f"OpenAI Whisper not available: {e}, falling back to Faster Whisper")
                    from .faster_whisper_service import faster_whisper_service
                    self.service = faster_whisper_service
                    self.implementation = "faster_whisper"
    
    async def initialize(self, model_size: str = "base"):
        """Initialize the selected Whisper model."""
        # API client doesn't need initialization, but we can call it for compatibility
        if hasattr(self.service, 'initialize'):
            await self.service.initialize(model_size)
        else:
            # API client - no initialization needed
            logger.debug(f"API client doesn't require initialization for model {model_size}")
    
    async def load_multiple_models(self, model_sizes: List[str] = None):
        """Load multiple Whisper models."""
        # API client doesn't need model loading, but we can call it for compatibility
        if hasattr(self.service, 'load_multiple_models'):
            await self.service.load_multiple_models(model_sizes)
        else:
            # API client - models are managed by the service
            logger.debug("API client doesn't require model loading")
    
    async def transcribe_audio(
        self, 
        audio_path: str, 
        language: str = "auto",
        task: str = "transcribe",
        model_size: str = "base",
        prompt: str = None
    ) -> UnifiedWhisperTranscriptionResult:
        """
        Transcribe audio using the selected Whisper implementation.
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'twi', 'ewe', 'ga')
            task: Task type ('transcribe' or 'translate')
            model_size: Whisper model size
            prompt: Optional prompt for better transcription
            
        Returns:
            UnifiedWhisperTranscriptionResult with transcription details
        """
        try:
            # Call the appropriate service
            if self.implementation == "faster_whisper_api":
                # API client returns WhisperTranscriptionResult (same format)
                from .whisper_api_client import WhisperTranscriptionResult
                result = await self.service.transcribe_audio(
                    audio_path=audio_path,
                    language=language,
                    task=task,
                    model_size=model_size,
                    prompt=prompt
                )
                # Convert to unified format
                return UnifiedWhisperTranscriptionResult(
                    text=result.text,
                    language=result.language,
                    confidence=result.confidence,
                    duration=result.duration,
                    segments=result.segments,
                    task=result.task,
                    implementation=self.implementation
                )
            elif self.implementation == "faster_whisper":
                from .faster_whisper_service import FasterWhisperTranscriptionResult
                result = await self.service.transcribe_audio(
                    audio_path=audio_path,
                    language=language,
                    task=task,
                    model_size=model_size,
                    prompt=prompt
                )
                # Convert to unified format
                return UnifiedWhisperTranscriptionResult(
                    text=result.text,
                    language=result.language,
                    confidence=result.confidence,
                    duration=result.duration,
                    segments=result.segments,
                    task=result.task,
                    implementation=self.implementation
                )
            else:
                from .whisper_service import WhisperTranscriptionResult
                result = await self.service.transcribe_audio(
                    audio_path=audio_path,
                    language=language,
                    task=task,
                    model_size=model_size,
                    prompt=prompt
                )
                # Convert to unified format
                return UnifiedWhisperTranscriptionResult(
                    text=result.text,
                    language=result.language,
                    confidence=result.confidence,
                    duration=result.duration,
                    segments=result.segments,
                    task=result.task,
                    implementation=self.implementation
                )
                
        except Exception as e:
            logger.error(f"Error transcribing audio with {self.implementation}: {e}")
            raise
    
    async def translate_audio(
        self, 
        audio_path: str, 
        target_language: str = "en",
        model_size: str = "base"
    ) -> UnifiedWhisperTranscriptionResult:
        """
        Translate audio to English using the selected Whisper implementation.
        
        Args:
            audio_path: Path to audio file
            target_language: Target language (usually 'en' for English)
            model_size: Whisper model size
            
        Returns:
            UnifiedWhisperTranscriptionResult with translation details
        """
        return await self.transcribe_audio(
            audio_path=audio_path,
            language="auto",  # Auto-detect source language
            task="translate",
            model_size=model_size
        )
    
    async def detect_language(self, audio_path: str, model_size: str = "base") -> str:
        """
        Detect language of audio using the selected Whisper implementation.
        
        Args:
            audio_path: Path to audio file
            model_size: Whisper model size
            
        Returns:
            Detected language code
        """
        # For API client, we can transcribe with auto-detect and return the detected language
        if self.implementation == "faster_whisper_api":
            result = await self.service.transcribe_audio(
                audio_path=audio_path,
                language="auto",
                task="transcribe",
                model_size=model_size
            )
            return result.language
        else:
            return await self.service.detect_language(audio_path, model_size)
    
    async def get_available_languages(self) -> List[str]:
        """Get list of languages supported by the selected implementation."""
        if hasattr(self.service, 'get_available_languages'):
            return await self.service.get_available_languages()
        else:
            # Return common languages for API client
            return ["en", "es", "fr", "de", "it", "pt", "pl", "ru", "ja", "ko", "zh", "ar",
                    "tw", "ee", "ga", "dag", "ha", "yo", "ig", "sw"]
    
    def get_supported_ghanaian_languages(self) -> List[str]:
        """Get list of supported Ghanaian languages."""
        if hasattr(self.service, 'get_supported_ghanaian_languages'):
            return self.service.get_supported_ghanaian_languages()
        else:
            # Return Ghanaian languages supported by the API
            return ["twi", "tw", "asante_twi", "akuapem_twi", "ewe", "ga", "dagbani", 
                    "hausa", "yoruba", "igbo", "swahili", "english", "en", "auto"]
    
    def get_language_code(self, language: str) -> Optional[str]:
        """Get Whisper language code for given language."""
        if hasattr(self.service, 'get_language_code'):
            return self.service.get_language_code(language)
        else:
            # Map for API client
            ghanaian_languages = {
                "twi": "tw", "tw": "tw", "asante_twi": "tw", "akuapem_twi": "tw",
                "ewe": "ee", "ga": "ga", "dagbani": "dag", "hausa": "ha",
                "yoruba": "yo", "igbo": "ig", "swahili": "sw", "english": "en",
                "en": "en", "auto": "auto"
            }
            return ghanaian_languages.get(language.lower())
    
    async def batch_transcribe(
        self, 
        audio_files: List[str], 
        language: str = "auto",
        task: str = "transcribe",
        model_size: str = "base"
    ) -> List[UnifiedWhisperTranscriptionResult]:
        """
        Transcribe multiple audio files in batch.
        
        Args:
            audio_files: List of audio file paths
            language: Language code
            task: Task type
            model_size: Whisper model size
            
        Returns:
            List of UnifiedWhisperTranscriptionResult
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
        """Get information about the selected Whisper model."""
        info = await self.service.get_model_info(model_size)
        info["implementation"] = self.implementation
        return info
    
    def get_implementation_info(self) -> Dict[str, Any]:
        """Get information about the current implementation."""
        return {
            "implementation": self.implementation,
            "use_faster_whisper": self.use_faster_whisper,
            "environment_variable": os.getenv("WHISPER_IMPLEMENTATION", "faster_whisper")
        }

# Global instance - uses environment variable WHISPER_IMPLEMENTATION to determine implementation
unified_whisper_service = UnifiedWhisperService()
