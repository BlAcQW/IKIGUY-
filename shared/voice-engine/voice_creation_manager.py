"""
Voice Creation Manager for Kasa AI Voice Studio
Shared service for voice creation and management across applications
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Import from core backend if available
try:
    import sys
    sys.path.append('/opt/kasaai/apps/core_backend')
    from backend.services.voice_creation_service import VoiceCreationService
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False

logger = logging.getLogger(__name__)

class VoiceCreationManager:
    """Shared manager for voice creation operations"""
    
    def __init__(self):
        self.backend_service = None
        if BACKEND_AVAILABLE:
            self.backend_service = VoiceCreationService()
    
    async def initialize(self):
        """Initialize voice creation services"""
        if self.backend_service:
            await self.backend_service.initialize_models()
        else:
            logger.warning("Backend voice creation service not available")
    
    async def clone_voice_from_audio(
        self, 
        audio_file: bytes, 
        voice_name: str,
        language: str = "en",
        description: str = "",
        user_id: str = None
    ) -> Dict[str, Any]:
        """Clone voice from audio file"""
        if not self.backend_service:
            raise Exception("Voice creation service not available")
        
        return await self.backend_service.clone_voice_from_audio(
            audio_file=audio_file,
            voice_name=voice_name,
            language=language,
            description=description,
            user_id=user_id
        )
    
    async def train_voice_from_dataset(
        self,
        dataset_id: str,
        voice_name: str,
        language: str,
        training_config: Dict[str, Any],
        user_id: str = None
    ) -> Dict[str, Any]:
        """Train voice from dataset"""
        if not self.backend_service:
            raise Exception("Voice creation service not available")
        
        return await self.backend_service.train_voice_from_dataset(
            dataset_id=dataset_id,
            voice_name=voice_name,
            language=language,
            training_config=training_config,
            user_id=user_id
        )
    
    async def synthesize_with_voice(
        self,
        voice_id: str,
        text: str,
        language: str = None
    ) -> Tuple[Any, int]:
        """Synthesize speech with custom voice"""
        if not self.backend_service:
            raise Exception("Voice creation service not available")
        
        return await self.backend_service.synthesize_with_voice(
            voice_id=voice_id,
            text=text,
            language=language
        )
    
    def get_available_datasets(self) -> Dict[str, Dict[str, Any]]:
        """Get available training datasets"""
        if not self.backend_service:
            # Return default datasets if backend not available
            return {
                "bible_tts_twi": {
                    "name": "BibleTTS Twi (Asante)",
                    "language": "Twi",
                    "speakers": 2,
                    "duration": "12 hours",
                    "description": "High-quality Asante Twi speech from biblical text readings",
                    "source": "BibleTTS Research Project"
                },
                "ghananlp_twi": {
                    "name": "GhanaNLP Twi Corpus", 
                    "language": "Twi",
                    "speakers": 15,
                    "duration": "25 hours",
                    "description": "Diverse Twi speech corpus from Ghana",
                    "source": "GhanaNLP"
                },
                "meta_mms_ga": {
                    "name": "Meta MMS Ga Dataset",
                    "language": "Ga", 
                    "speakers": 8,
                    "duration": "18 hours",
                    "description": "Ga language speech data from Meta MMS",
                    "source": "Meta AI"
                },
                "meta_mms_ewe": {
                    "name": "Meta MMS Ewe Dataset",
                    "language": "Ewe",
                    "speakers": 6,
                    "duration": "15 hours", 
                    "description": "Ewe language TTS training data",
                    "source": "Meta AI"
                },
                "common_voice_hausa": {
                    "name": "Common Voice Hausa",
                    "language": "Hausa",
                    "speakers": 45,
                    "duration": "32 hours",
                    "description": "Community-contributed Hausa speech recordings",
                    "source": "Mozilla Common Voice"
                }
            }
        
        return self.backend_service.get_available_datasets()
    
    async def get_training_progress(self, voice_id: str) -> Dict[str, Any]:
        """Get training progress for a voice"""
        if not self.backend_service:
            # Return mock progress for demo
            return {
                "voice_id": voice_id,
                "status": "ready",
                "progress": 100,
                "error": None
            }
        
        return await self.backend_service.get_training_progress(voice_id)
    
    async def get_voice_info(self, voice_id: str) -> Dict[str, Any]:
        """Get voice metadata"""
        if not self.backend_service:
            raise Exception("Voice creation service not available")
        
        return await self.backend_service.get_voice_info(voice_id)
    
    async def delete_voice(self, voice_id: str, user_id: str = None) -> bool:
        """Delete a custom voice"""
        if not self.backend_service:
            raise Exception("Voice creation service not available")
        
        return await self.backend_service.delete_voice(voice_id, user_id)
    
    async def list_user_voices(self, user_id: str) -> List[Dict[str, Any]]:
        """List user's custom voices"""
        if not self.backend_service:
            return []
        
        return await self.backend_service.list_user_voices(user_id)

# Global instance
voice_creation_manager = VoiceCreationManager()

# Async initialization
async def initialize_voice_creation():
    """Initialize the voice creation manager"""
    try:
        await voice_creation_manager.initialize()
        logger.info("Voice creation manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize voice creation manager: {e}")

# Helper functions for easy import
async def clone_voice(audio_file: bytes, voice_name: str, **kwargs) -> Dict[str, Any]:
    """Helper function to clone voice"""
    return await voice_creation_manager.clone_voice_from_audio(audio_file, voice_name, **kwargs)

async def train_voice(dataset_id: str, voice_name: str, language: str, training_config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Helper function to train voice"""
    return await voice_creation_manager.train_voice_from_dataset(dataset_id, voice_name, language, training_config, **kwargs)

def get_datasets() -> Dict[str, Dict[str, Any]]:
    """Helper function to get available datasets"""
    return voice_creation_manager.get_available_datasets()

async def synthesize_speech(voice_id: str, text: str, language: str = None) -> Tuple[Any, int]:
    """Helper function to synthesize speech"""
    return await voice_creation_manager.synthesize_with_voice(voice_id, text, language)