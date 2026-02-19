"""
Model caching and fallback service for TTS models.
Handles local model caching, preloading, and intelligent fallbacks.
"""

import logging
import os
import json
import hashlib
import asyncio
import pickle
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import torch
import numpy as np

# Optional imports - comment out if not available
try:
    from transformers import VitsModel, AutoTokenizer
    VITS_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    VITS_AVAILABLE = False
    VitsModel = None
    AutoTokenizer = None

try:
    from speechbrain.inference.TTS import Tacotron2
    from speechbrain.inference.vocoders import HIFIGAN
    SPEECHBRAIN_AVAILABLE = True
except ImportError:
    SPEECHBRAIN_AVAILABLE = False
    Tacotron2 = None
    HIFIGAN = None

from .storage_service import StorageService

logger = logging.getLogger(__name__)

class ModelCacheService:
    """
    Service for managing TTS model caching and fallback strategies.
    """
    
    def __init__(self, cache_dir: str = "/opt/kasaai/voice_models_cache"):
        """
        Initialize model cache service.
        
        Args:
            cache_dir: Directory to store cached models
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.storage_service = StorageService()
        
        # Model cache
        self.loaded_models = {}
        self.model_metadata = {}
        
        # Threading for async model loading
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Model configurations with fallback hierarchy
        self.model_configs = {
            # Primary models (best quality)
            "meta_mms_twi": {
                "model_id": "facebook/mms-tts-aka",
                "type": "meta_mms",
                "language": "twi",
                "quality": "high",
                "priority": 1,
                "fallbacks": ["kokoro_multilingual", "echo_service"]
            },
            "meta_mms_ewe": {
                "model_id": "facebook/mms-tts-ewe", 
                "type": "meta_mms",
                "language": "ewe",
                "quality": "high",
                "priority": 1,
                "fallbacks": ["meta_mms_twi", "echo_service"]
            },
            "meta_mms_hausa": {
                "model_id": "facebook/mms-tts-hau",
                "type": "meta_mms", 
                "language": "hausa",
                "quality": "high",
                "priority": 1,
                "fallbacks": ["meta_mms_twi", "echo_service"]
            },
            
            # Secondary models (good quality, fast)
            "kokoro_multilingual": {
                "model_id": "speechbrain/tts-tacotron2-ljspeech",
                "type": "speechbrain",
                "language": "en",
                "quality": "medium", 
                "priority": 2,
                "fallbacks": ["echo_service"]
            },
            
            # Fallback service (always works)
            "echo_service": {
                "model_id": "echo",
                "type": "echo",
                "language": "any",
                "quality": "low",
                "priority": 3,
                "fallbacks": []
            }
        }
        
        # Task for preloading high-priority models (will be created when event loop is available)
        self._preload_task = None
    
    async def start_preload_task(self):
        """Start the preload task if not already started."""
        if self._preload_task is None:
            try:
                self._preload_task = asyncio.create_task(self._preload_models())
            except RuntimeError:
                # No event loop available yet, will try again later
                pass
    
    async def _preload_models(self):
        """Preload high-priority models in background."""
        
        try:
            logger.info("Preloading high-priority TTS models...")
            
            # Preload Twi model (highest priority for KasaAI)
            await self.load_model("meta_mms_twi")
            
            logger.info("✅ Model preloading completed")
            
        except Exception as e:
            logger.error(f"Model preloading failed: {e}")
    
    async def load_model(self, model_key: str) -> bool:
        """
        Load a model into memory cache.
        
        Args:
            model_key: Key identifying the model to load
            
        Returns:
            True if model loaded successfully
        """
        
        if model_key in self.loaded_models:
            logger.debug(f"Model {model_key} already loaded")
            return True
        
        config = self.model_configs.get(model_key)
        if not config:
            logger.error(f"Unknown model key: {model_key}")
            return False
        
        try:
            logger.info(f"Loading model: {model_key}")
            start_time = time.time()
            
            if config["type"] == "meta_mms":
                model, tokenizer = await self._load_meta_mms_model(config["model_id"])
                
            elif config["type"] == "speechbrain":
                model, tokenizer = await self._load_speechbrain_model(config["model_id"])
                
            elif config["type"] == "echo":
                model, tokenizer = self._load_echo_model()
                
            else:
                raise ValueError(f"Unknown model type: {config['type']}")
            
            # Cache the loaded model
            self.loaded_models[model_key] = {
                "model": model,
                "tokenizer": tokenizer,
                "config": config,
                "loaded_at": time.time(),
                "usage_count": 0
            }
            
            load_time = time.time() - start_time
            logger.info(f"✅ Model {model_key} loaded in {load_time:.2f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model_key}: {e}")
            return False
    
    async def _load_meta_mms_model(self, model_id: str) -> Tuple[Any, Any]:
        """Load Meta MMS model."""
        
        def _load_sync():
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = VitsModel.from_pretrained(model_id)
            return model, tokenizer
        
        # Load in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        model, tokenizer = await loop.run_in_executor(self.executor, _load_sync)
        
        return model, tokenizer
    
    async def _load_speechbrain_model(self, model_id: str) -> Tuple[Any, Any]:
        """Load SpeechBrain model."""
        
        def _load_sync():
            # For now, return a simple mock
            # In production, would load actual SpeechBrain TTS
            return {"type": "speechbrain", "model_id": model_id}, None
        
        loop = asyncio.get_event_loop()
        model, tokenizer = await loop.run_in_executor(self.executor, _load_sync)
        
        return model, tokenizer
    
    def _load_echo_model(self) -> Tuple[Any, Any]:
        """Load echo fallback model (always succeeds)."""
        
        echo_model = {
            "type": "echo",
            "description": "Fallback echo service - always works"
        }
        
        return echo_model, None
    
    async def synthesize_with_fallback(
        self, 
        text: str, 
        preferred_language: str = "twi",
        voice_quality: str = "high"
    ) -> Dict[str, Any]:
        """
        Synthesize speech with automatic fallback strategy.
        
        Args:
            text: Text to synthesize
            preferred_language: Preferred language for synthesis
            voice_quality: Desired quality level (high, medium, low)
            
        Returns:
            Synthesis result with model used and audio data
        """
        
        # Select best model for language and quality
        model_key = self._select_best_model(preferred_language, voice_quality)
        
        # Try synthesis with fallbacks
        return await self._synthesize_with_retries(text, model_key)
    
    def _select_best_model(self, language: str, quality: str) -> str:
        """Select best model based on language and quality preferences."""
        
        # Language-specific model selection
        language_models = {
            "twi": "meta_mms_twi",
            "aka": "meta_mms_twi", 
            "ewe": "meta_mms_ewe",
            "hausa": "meta_mms_hausa",
            "en": "kokoro_multilingual"
        }
        
        preferred_model = language_models.get(language.lower(), "meta_mms_twi")
        
        # Check if preferred model is available
        if preferred_model in self.model_configs:
            return preferred_model
        
        # Fallback to first available model
        return list(self.model_configs.keys())[0]
    
    async def _synthesize_with_retries(self, text: str, model_key: str) -> Dict[str, Any]:
        """Synthesize with automatic retries and fallbacks."""
        
        attempted_models = []
        
        while model_key and model_key not in attempted_models:
            attempted_models.append(model_key)
            
            try:
                # Ensure model is loaded
                if not await self.load_model(model_key):
                    raise Exception(f"Failed to load model {model_key}")
                
                # Perform synthesis
                result = await self._synthesize_with_model(text, model_key)
                
                # Update usage statistics
                if model_key in self.loaded_models:
                    self.loaded_models[model_key]["usage_count"] += 1
                
                result["model_used"] = model_key
                result["fallback_attempts"] = len(attempted_models) - 1
                
                logger.info(f"✅ Synthesis successful with {model_key}")
                return result
                
            except Exception as e:
                logger.warning(f"Synthesis failed with {model_key}: {e}")
                
                # Get next fallback model
                config = self.model_configs.get(model_key, {})
                fallbacks = config.get("fallbacks", [])
                
                if fallbacks:
                    model_key = fallbacks[0]
                    logger.info(f"Falling back to {model_key}")
                else:
                    model_key = None
        
        # All models failed
        logger.error(f"All synthesis attempts failed for text: {text[:50]}...")
        return {
            "success": False,
            "error": "All synthesis methods failed",
            "attempted_models": attempted_models,
            "audio_samples": [],
            "sample_rate": 22050
        }
    
    async def _synthesize_with_model(self, text: str, model_key: str) -> Dict[str, Any]:
        """Synthesize speech with a specific model."""
        
        if model_key not in self.loaded_models:
            raise Exception(f"Model {model_key} not loaded")
        
        model_data = self.loaded_models[model_key]
        model = model_data["model"]
        tokenizer = model_data["tokenizer"]
        config = model_data["config"]
        
        if config["type"] == "meta_mms":
            return await self._synthesize_meta_mms(text, model, tokenizer)
            
        elif config["type"] == "speechbrain":
            return await self._synthesize_speechbrain(text, model)
            
        elif config["type"] == "echo":
            return self._synthesize_echo(text)
            
        else:
            raise Exception(f"Unknown model type: {config['type']}")
    
    async def _synthesize_meta_mms(self, text: str, model: Any, tokenizer: Any) -> Dict[str, Any]:
        """Synthesize with Meta MMS model."""
        
        def _synthesize_sync():
            inputs = tokenizer(text, return_tensors="pt")
            
            with torch.no_grad():
                audio = model(**inputs).waveform
            
            # Convert to numpy array and then list for JSON serialization
            audio_np = audio.squeeze().numpy()
            return audio_np.tolist()
        
        loop = asyncio.get_event_loop()
        audio_samples = await loop.run_in_executor(self.executor, _synthesize_sync)
        
        return {
            "success": True,
            "audio_samples": audio_samples,
            "sample_rate": 16000,
            "text": text,
            "model_type": "meta_mms"
        }
    
    async def _synthesize_speechbrain(self, text: str, model: Any) -> Dict[str, Any]:
        """Synthesize with SpeechBrain model."""
        
        # Mock implementation for now
        duration = len(text) * 0.08  # Estimate duration
        sample_rate = 22050
        samples = int(duration * sample_rate)
        
        # Generate simple sine wave as mock audio
        t = np.linspace(0, duration, samples)
        audio = np.sin(2 * np.pi * 440 * t) * 0.3  # 440 Hz tone
        
        return {
            "success": True,
            "audio_samples": audio.tolist(),
            "sample_rate": sample_rate,
            "text": text,
            "model_type": "speechbrain"
        }
    
    def _synthesize_echo(self, text: str) -> Dict[str, Any]:
        """Echo fallback - always succeeds with mock audio."""
        
        # Generate simple mock audio based on text length
        duration = max(1.0, len(text) * 0.05)  # Minimum 1 second
        sample_rate = 22050
        samples = int(duration * sample_rate)
        
        # Generate audio that "says" the length of the text
        frequency = 200 + len(text) * 2  # Variable frequency based on text length
        t = np.linspace(0, duration, samples)
        audio = np.sin(2 * np.pi * frequency * t) * np.exp(-t / duration) * 0.2
        
        return {
            "success": True,
            "audio_samples": audio.tolist(),
            "sample_rate": sample_rate,
            "text": f"Echo: {text}",
            "model_type": "echo",
            "note": "Fallback echo service"
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get caching statistics."""
        
        stats = {
            "loaded_models": len(self.loaded_models),
            "cache_directory": str(self.cache_dir),
            "models": {}
        }
        
        for key, data in self.loaded_models.items():
            stats["models"][key] = {
                "loaded_at": data["loaded_at"],
                "usage_count": data["usage_count"],
                "config": data["config"]
            }
        
        return stats
    
    async def clear_cache(self, model_key: Optional[str] = None):
        """Clear model cache."""
        
        if model_key:
            if model_key in self.loaded_models:
                del self.loaded_models[model_key]
                logger.info(f"Cleared cache for {model_key}")
        else:
            self.loaded_models.clear()
            logger.info("Cleared all model cache")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models."""
        
        return {
            "available_models": self.model_configs,
            "loaded_models": list(self.loaded_models.keys()),
            "cache_stats": self.get_cache_stats()
        }

# Global service instance
model_cache_service = ModelCacheService()