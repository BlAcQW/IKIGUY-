"""
Voice Creation Service for Kasa AI Voice Studio
Handles voice training, cloning, and dataset management using Coqui XTTS-v2 and Hugging Face models
"""

import os
import io
import json
import asyncio
import tempfile
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

import torch
import numpy as np
import soundfile as sf
try:
    from TTS.api import TTS
    TTS_AVAILABLE = True
except ImportError:
    TTS = None
    TTS_AVAILABLE = False
from transformers import VitsModel, AutoTokenizer, pipeline
import datasets
from datasets import load_dataset
import librosa

from .storage_service import StorageService
from .config_service import ConfigService

logger = logging.getLogger(__name__)

class VoiceCreationService:
    """Service for creating, training, and managing custom voices"""
    
    def __init__(self):
        self.storage = StorageService()
        self.config = ConfigService()
        
        # Initialize TTS models
        self.xtts_model = None
        self.meta_mms_models = {}
        
        # Available datasets
        self.available_datasets = {
            "bible_tts_twi": {
                "name": "BibleTTS Twi (Asante)",
                "language": "Twi",
                "hf_id": "facebook/mms-tts-aka",
                "speakers": 2,
                "duration": "12 hours",
                "description": "High-quality Asante Twi speech from biblical text readings"
            },
            "bible_tts_akuapem": {
                "name": "BibleTTS Twi (Akuapem)",
                "language": "Twi", 
                "hf_id": "facebook/mms-tts-aka",
                "speakers": 2,
                "duration": "10 hours",
                "description": "Natural Akuapem Twi speech recordings"
            },
            "ghananlp_twi": {
                "name": "GhanaNLP Twi Corpus",
                "language": "Twi",
                "hf_id": "facebook/mms-tts-aka",
                "speakers": 15,
                "duration": "25 hours",
                "description": "Diverse Twi speech corpus from Ghana"
            },
            "meta_mms_ga": {
                "name": "Meta MMS Ga Dataset",
                "language": "Ga",
                "hf_id": "facebook/mms-tts-gaa",
                "speakers": 8,
                "duration": "18 hours",
                "description": "Ga language speech data from Meta MMS"
            },
            "meta_mms_ewe": {
                "name": "Meta MMS Ewe Dataset",
                "language": "Ewe",
                "hf_id": "facebook/mms-tts-ewe", 
                "speakers": 6,
                "duration": "15 hours",
                "description": "Ewe language TTS training data"
            },
            "common_voice_hausa": {
                "name": "Common Voice Hausa",
                "language": "Hausa",
                "hf_id": "facebook/mms-tts-hau",
                "speakers": 45,
                "duration": "32 hours", 
                "description": "Community-contributed Hausa speech recordings"
            }
        }
    
    async def initialize_models(self):
        """Initialize TTS models on first use"""
        try:
            # Initialize Coqui XTTS-v2
            if self.xtts_model is None:
                logger.info("Loading Coqui XTTS-v2 model...")
                self.xtts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
                logger.info("XTTS-v2 model loaded successfully")
        except Exception as e:
            logger.error(f"Error initializing TTS models: {e}")
            raise
    
    async def clone_voice_from_audio(
        self, 
        audio_file: bytes, 
        voice_name: str,
        language: str = "en",
        description: str = "",
        user_id: str = None
    ) -> Dict[str, Any]:
        """Clone a voice from uploaded audio file"""
        await self.initialize_models()
        
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(audio_file)
                tmp_audio_path = tmp_file.name
            
            # Validate audio
            audio_data, sample_rate = librosa.load(tmp_audio_path, sr=22050)
            duration = len(audio_data) / sample_rate
            
            if duration < 3 or duration > 30:
                raise ValueError(f"Audio duration must be 3-30 seconds, got {duration:.1f}s")
            
            # Generate voice ID
            voice_id = f"voice_{voice_name.lower().replace(' ', '_')}_{int(asyncio.get_event_loop().time())}"
            
            # Test voice cloning with sample text
            test_text = "Akwaaba! This is a test of my cloned voice speaking in both English and my native language."
            
            # Generate audio with XTTS
            cloned_audio = self.xtts_model.tts(
                text=test_text,
                speaker_wav=tmp_audio_path,
                language=language
            )
            
            # Save cloned voice reference
            voice_dir = f"voices/{voice_id}"
            await self.storage.save_file(
                f"{voice_dir}/reference.wav",
                open(tmp_audio_path, 'rb').read()
            )
            
            # Save test audio
            test_audio_buffer = io.BytesIO()
            sf.write(test_audio_buffer, cloned_audio, 22050, format='WAV')
            await self.storage.save_file(
                f"{voice_dir}/test_sample.wav",
                test_audio_buffer.getvalue()
            )
            
            # Create voice metadata
            voice_metadata = {
                "id": voice_id,
                "name": voice_name,
                "description": description,
                "language": language,
                "provider": "coqui_xtts",
                "type": "cloned",
                "user_id": user_id,
                "created_at": asyncio.get_event_loop().time(),
                "sample_rate": 22050,
                "reference_audio": f"{voice_dir}/reference.wav",
                "test_sample": f"{voice_dir}/test_sample.wav",
                "status": "ready"
            }
            
            # Save metadata
            await self.storage.save_file(
                f"{voice_dir}/metadata.json",
                json.dumps(voice_metadata, indent=2).encode()
            )
            
            # Cleanup temp file
            os.unlink(tmp_audio_path)
            
            logger.info(f"Voice cloned successfully: {voice_id}")
            return voice_metadata
            
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            if 'tmp_audio_path' in locals():
                try:
                    os.unlink(tmp_audio_path)
                except:
                    pass
            raise
    
    async def train_voice_from_dataset(
        self,
        dataset_id: str,
        voice_name: str, 
        language: str,
        training_config: Dict[str, Any],
        user_id: str = None
    ) -> Dict[str, Any]:
        """Train a voice using selected dataset"""
        
        if dataset_id not in self.available_datasets:
            raise ValueError(f"Dataset {dataset_id} not available")
        
        dataset_info = self.available_datasets[dataset_id]
        
        try:
            # Generate voice ID
            voice_id = f"voice_{voice_name.lower().replace(' ', '_')}_{int(asyncio.get_event_loop().time())}"
            voice_dir = f"voices/{voice_id}"
            
            # Create voice metadata
            voice_metadata = {
                "id": voice_id,
                "name": voice_name,
                "description": f"Custom {dataset_info['language']} voice trained on {dataset_info['name']}",
                "language": language,
                "provider": "coqui_xtts",
                "type": "trained",
                "user_id": user_id,
                "created_at": asyncio.get_event_loop().time(),
                "dataset_id": dataset_id,
                "dataset_info": dataset_info,
                "training_config": training_config,
                "status": "training",
                "training_progress": 0
            }
            
            # Save initial metadata
            await self.storage.save_file(
                f"{voice_dir}/metadata.json",
                json.dumps(voice_metadata, indent=2).encode()
            )
            
            # Start training in background
            asyncio.create_task(self._train_voice_background(voice_id, dataset_id, training_config))
            
            logger.info(f"Voice training started: {voice_id}")
            return voice_metadata
            
        except Exception as e:
            logger.error(f"Voice training setup failed: {e}")
            raise
    
    async def _train_voice_background(
        self,
        voice_id: str,
        dataset_id: str, 
        training_config: Dict[str, Any]
    ):
        """Background voice training process"""
        try:
            voice_dir = f"voices/{voice_id}"
            
            # Load dataset
            dataset_info = self.available_datasets[dataset_id]
            
            # For demo purposes, simulate training progress
            for progress in range(0, 101, 5):
                await asyncio.sleep(2)  # Simulate training time
                
                # Update progress
                metadata_bytes = await self.storage.get_file(f"{voice_dir}/metadata.json")
                metadata = json.loads(metadata_bytes.decode())
                metadata["training_progress"] = progress
                
                if progress == 100:
                    metadata["status"] = "ready"
                    # Generate test sample using Meta MMS for the language
                    await self._generate_test_sample(voice_id, dataset_info)
                
                await self.storage.save_file(
                    f"{voice_dir}/metadata.json",
                    json.dumps(metadata, indent=2).encode()
                )
                
                logger.info(f"Training progress for {voice_id}: {progress}%")
            
            logger.info(f"Voice training completed: {voice_id}")
            
        except Exception as e:
            logger.error(f"Background training failed for {voice_id}: {e}")
            # Update status to failed
            try:
                metadata_bytes = await self.storage.get_file(f"{voice_dir}/metadata.json")
                metadata = json.loads(metadata_bytes.decode())
                metadata["status"] = "failed"
                metadata["error"] = str(e)
                await self.storage.save_file(
                    f"{voice_dir}/metadata.json",
                    json.dumps(metadata, indent=2).encode()
                )
            except:
                pass
    
    async def _generate_test_sample(self, voice_id: str, dataset_info: Dict[str, Any]):
        """Generate test sample for trained voice"""
        try:
            # Load Meta MMS model for the language
            hf_model_id = dataset_info["hf_id"]
            
            if hf_model_id not in self.meta_mms_models:
                logger.info(f"Loading Meta MMS model: {hf_model_id}")
                model = VitsModel.from_pretrained(hf_model_id)
                tokenizer = AutoTokenizer.from_pretrained(hf_model_id)
                self.meta_mms_models[hf_model_id] = (model, tokenizer)
            
            model, tokenizer = self.meta_mms_models[hf_model_id]
            
            # Generate test text based on language
            test_texts = {
                "Twi": "Akwaaba! Me ho yɛ me. Ɛte sɛn?",
                "Ga": "Akwaaba! Mi yɛ mi. Ɛ tɛ sɛ?",
                "Ewe": "Woezɔ! Nye dzi nye. Aleke nèle?", 
                "Hausa": "Sannu! Ni ne ni. Yaya kake?"
            }
            
            language = dataset_info["language"]
            test_text = test_texts.get(language, "Hello, this is my custom voice.")
            
            # Generate audio
            inputs = tokenizer(test_text, return_tensors="pt")
            with torch.no_grad():
                audio = model(**inputs).waveform
            
            # Save test sample
            voice_dir = f"voices/{voice_id}"
            test_audio_buffer = io.BytesIO()
            sf.write(test_audio_buffer, audio.numpy().squeeze(), 22050, format='WAV')
            
            await self.storage.save_file(
                f"{voice_dir}/test_sample.wav",
                test_audio_buffer.getvalue()
            )
            
            logger.info(f"Test sample generated for {voice_id}")
            
        except Exception as e:
            logger.error(f"Failed to generate test sample for {voice_id}: {e}")
    
    async def synthesize_with_voice(
        self,
        voice_id: str,
        text: str,
        language: str = None
    ) -> Tuple[np.ndarray, int]:
        """Synthesize speech using a custom voice"""
        await self.initialize_models()
        
        try:
            voice_dir = f"voices/{voice_id}"
            
            # Load voice metadata
            metadata_bytes = await self.storage.get_file(f"{voice_dir}/metadata.json")
            metadata = json.loads(metadata_bytes.decode())
            
            if metadata["status"] != "ready":
                raise ValueError(f"Voice {voice_id} is not ready (status: {metadata['status']})")
            
            # Use appropriate synthesis method based on voice type
            if metadata["type"] == "cloned":
                # Use XTTS with reference audio
                reference_audio_bytes = await self.storage.get_file(metadata["reference_audio"])
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                    tmp_file.write(reference_audio_bytes)
                    reference_path = tmp_file.name
                
                # Generate audio with XTTS
                audio = self.xtts_model.tts(
                    text=text,
                    speaker_wav=reference_path,
                    language=language or metadata["language"]
                )
                
                os.unlink(reference_path)
                
            elif metadata["type"] == "trained":
                # Use Meta MMS model for trained voices
                dataset_info = metadata["dataset_info"]
                hf_model_id = dataset_info["hf_id"]
                
                if hf_model_id not in self.meta_mms_models:
                    model = VitsModel.from_pretrained(hf_model_id)
                    tokenizer = AutoTokenizer.from_pretrained(hf_model_id)
                    self.meta_mms_models[hf_model_id] = (model, tokenizer)
                
                model, tokenizer = self.meta_mms_models[hf_model_id]
                
                inputs = tokenizer(text, return_tensors="pt")
                with torch.no_grad():
                    audio = model(**inputs).waveform.numpy().squeeze()
            
            else:
                raise ValueError(f"Unknown voice type: {metadata['type']}")
            
            return audio, 22050
            
        except Exception as e:
            logger.error(f"Speech synthesis failed for voice {voice_id}: {e}")
            raise
    
    async def get_voice_info(self, voice_id: str) -> Dict[str, Any]:
        """Get voice metadata and info"""
        try:
            voice_dir = f"voices/{voice_id}"
            metadata_bytes = await self.storage.get_file(f"{voice_dir}/metadata.json")
            return json.loads(metadata_bytes.decode())
        except Exception as e:
            logger.error(f"Failed to get voice info for {voice_id}: {e}")
            raise
    
    async def list_user_voices(self, user_id: str) -> List[Dict[str, Any]]:
        """List all voices created by a user"""
        try:
            # This would need to be implemented based on your storage system
            # For now, return a placeholder
            return []
        except Exception as e:
            logger.error(f"Failed to list voices for user {user_id}: {e}")
            raise
    
    async def delete_voice(self, voice_id: str, user_id: str = None) -> bool:
        """Delete a custom voice"""
        try:
            voice_dir = f"voices/{voice_id}"
            
            # Verify ownership if user_id provided
            if user_id:
                metadata_bytes = await self.storage.get_file(f"{voice_dir}/metadata.json")
                metadata = json.loads(metadata_bytes.decode())
                if metadata.get("user_id") != user_id:
                    raise ValueError("Voice not owned by user")
            
            # Delete all voice files
            await self.storage.delete_folder(voice_dir)
            
            logger.info(f"Voice deleted: {voice_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete voice {voice_id}: {e}")
            raise
    
    def get_available_datasets(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available training datasets"""
        return self.available_datasets
    
    async def get_training_progress(self, voice_id: str) -> Dict[str, Any]:
        """Get training progress for a voice"""
        try:
            voice_dir = f"voices/{voice_id}"
            metadata_bytes = await self.storage.get_file(f"{voice_dir}/metadata.json")
            metadata = json.loads(metadata_bytes.decode())
            
            return {
                "voice_id": voice_id,
                "status": metadata.get("status", "unknown"),
                "progress": metadata.get("training_progress", 0),
                "error": metadata.get("error")
            }
            
        except Exception as e:
            logger.error(f"Failed to get training progress for {voice_id}: {e}")
            raise