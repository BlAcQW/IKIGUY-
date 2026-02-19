#!/usr/bin/env python3
"""
Meta MMS (Massively Multilingual Speech) Service
Supports over 1,100 languages including Ghanaian languages like Twi
"""

import asyncio
import logging
import torch
import torchaudio
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import requests
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MMSTranscriptionResult:
    """Result from MMS transcription."""
    text: str
    language: str
    confidence: float
    duration: float
    segments: List[Dict[str, Any]]

@dataclass
class MMSTTSResult:
    """Result from MMS text-to-speech."""
    audio_path: str
    duration: float
    language: str
    text: str

class MetaMMSService:
    """Service for Meta's Massively Multilingual Speech (MMS) models."""
    
    def __init__(self):
        self.models_loaded = False
        self.asr_model = None
        self.tts_model = None
        self.lid_model = None
        
        # Ghanaian language codes supported by MMS
        # Maps our language names to MMS TTS model identifiers
        self.ghanaian_languages = {
            "tw": "aka",  # Twi shortcode (backward compatibility)
            "twi": "aka",  # Twi (Akan) - MMS uses 'aka' for Akan
            "asante_twi": "aka",  # Asante Twi
            "akuapem_twi": "aka",  # Akuapem Twi
            "ewe": "ewe",  # Ewe
            "ga": "gaa",   # Ga
            "dagbani": "dag",  # Dagbani
            "hausa": "hau",  # Hausa
            "yoruba": "yor",  # Yoruba
            "igbo": "ibo",  # Igbo
            "swahili": "swh",  # Swahili
            "english": "eng",  # English
            "en": "eng",  # English
            "eng": "eng",  # English MMS code
        }

        # MMS model configurations
        self.mms_config = {
            "asr_model": "facebook/mms-1b-all",
            "lid_model": "facebook/mms-lid-126",
            "device": "cuda" if torch.cuda.is_available() else "cpu"
        }

        # Cache for loaded TTS models (language_code -> model dict)
        self.tts_models = {}
    
    async def initialize(self):
        """Initialize MMS models (ASR and LID only, TTS loaded on-demand)."""
        try:
            logger.info("🔄 Initializing Meta MMS models...")

            # Check if required packages are installed
            try:
                import torch
                import transformers
                import torchaudio
            except ImportError as e:
                logger.error(f"❌ Meta MMS dependencies not installed: {e}")
                logger.error("📝 Meta MMS requires: pip install torch transformers torchaudio")
                raise RuntimeError(f"Meta MMS dependencies not available: {e}")

            # Load ASR model for speech recognition
            self.asr_model = await self._load_asr_model()

            # Load Language Identification model
            self.lid_model = await self._load_lid_model()

            # TTS models are loaded on-demand per language
            logger.info("ℹ️ TTS models will be loaded on-demand per language")

            self.models_loaded = True
            logger.info("✅ Meta MMS models initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize MMS models: {e}")
            self.models_loaded = False
    
    async def _load_asr_model(self):
        """Load MMS ASR model."""
        try:
            from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
            
            model_name = self.mms_config["asr_model"]
            device = self.mms_config["device"]
            
            logger.info(f"Loading MMS ASR model: {model_name}")
            
            processor = Wav2Vec2Processor.from_pretrained(model_name)
            model = Wav2Vec2ForCTC.from_pretrained(model_name)
            model = model.to(device)
            
            return {"model": model, "processor": processor}
            
        except ImportError as e:
            logger.error(f"transformers not installed: {e}")
            raise RuntimeError(f"Failed to load model: {e}")
    
    async def _load_tts_model(self, language_code: str):
        """
        Load MMS TTS model for specific language.

        Args:
            language_code: MMS language code (e.g., 'aka', 'eng', 'ewe')

        Returns:
            Dictionary with model and tokenizer
        """
        try:
            from transformers import VitsTokenizer, VitsModel

            model_name = f"facebook/mms-tts-{language_code}"
            device = self.mms_config["device"]

            logger.info(f"Loading MMS TTS model: {model_name}")

            tokenizer = VitsTokenizer.from_pretrained(model_name)
            model = VitsModel.from_pretrained(model_name)
            model = model.to(device)

            return {"model": model, "tokenizer": tokenizer, "language_code": language_code}

        except Exception as e:
            logger.error(f"Failed to load TTS model for {language_code}: {e}")
            raise RuntimeError(f"Failed to load TTS model: {e}")
    
    async def _load_lid_model(self):
        """Load MMS Language Identification model."""
        try:
            from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
            
            model_name = self.mms_config["lid_model"]
            device = self.mms_config["device"]
            
            logger.info(f"Loading MMS LID model: {model_name}")
            
            feature_extractor = AutoFeatureExtractor.from_pretrained(model_name)
            model = AutoModelForAudioClassification.from_pretrained(model_name)
            model = model.to(device)
            
            return {"model": model, "feature_extractor": feature_extractor}
            
        except ImportError as e:
            logger.error(f"transformers not installed: {e}")
            raise RuntimeError(f"Failed to load model: {e}")
    
    async def transcribe_audio(
        self, 
        audio_path: str, 
        language: str = "auto",
        task: str = "transcribe"
    ) -> MMSTranscriptionResult:
        """
        Transcribe audio using MMS ASR model.
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'twi', 'ewe', 'ga')
            task: Task type ('transcribe' or 'translate')
            
        Returns:
            MMSTranscriptionResult with transcription details
        """
        try:
            if not self.models_loaded:
                raise RuntimeError("Meta MMS models not initialized. Please ensure all dependencies are installed.")
            
            if not self.asr_model:
                raise RuntimeError("MMS ASR model not loaded")
            
            # Load and preprocess audio
            waveform, sample_rate = torchaudio.load(audio_path)
            
            # Resample if necessary (MMS expects 16kHz)
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                waveform = resampler(waveform)
                sample_rate = 16000
            
            # Convert to mono if stereo
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # Prepare input for model
            processor = self.asr_model["processor"]
            model = self.asr_model["model"]
            
            # Set language if specified
            if language != "auto" and language in self.ghanaian_languages:
                lang_code = self.ghanaian_languages[language]
                # Try to set prefix tokens if method exists (varies by transformers version)
                try:
                    if hasattr(processor.tokenizer, 'set_prefix_tokens'):
                        processor.tokenizer.set_prefix_tokens(lang_code)
                    elif hasattr(processor.tokenizer, 'set_target_lang'):
                        processor.tokenizer.set_target_lang(lang_code)
                except Exception as e:
                    logger.warning(f"Could not set language prefix: {e}")
            
            # Process audio
            inputs = processor(
                waveform.squeeze().numpy(), 
                sampling_rate=sample_rate, 
                return_tensors="pt"
            )
            
            # Move to device
            device = self.mms_config["device"]
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Generate transcription
            with torch.no_grad():
                logits = model(**inputs).logits
                predicted_ids = torch.argmax(logits, dim=-1)
                transcription = processor.batch_decode(predicted_ids)[0]
            
            # Calculate confidence (simplified)
            confidence = torch.softmax(logits, dim=-1).max().item()
            
            # Calculate duration
            duration = waveform.shape[1] / sample_rate
            
            return MMSTranscriptionResult(
                text=transcription,
                language=language if language != "auto" else "detected",
                confidence=confidence,
                duration=duration,
                segments=[{"text": transcription, "start": 0, "end": duration}]
            )
            
        except Exception as e:
            logger.error(f"Error transcribing audio with MMS: {e}")
            raise
    
    async def synthesize_speech(
        self,
        text: str,
        language: str,
        voice_id: Optional[str] = None
    ) -> MMSTTSResult:
        """
        Synthesize speech using MMS TTS model.

        Args:
            text: Text to synthesize
            language: Language code (e.g., 'twi', 'ewe', 'ga', 'en')
            voice_id: Optional voice identifier (not used for MMS)

        Returns:
            MMSTTSResult with audio details
        """
        try:
            import scipy.io.wavfile
            from pathlib import Path

            if not self.models_loaded:
                raise RuntimeError("Meta MMS models not initialized. Please ensure all dependencies are installed.")

            # Validate and get language code
            if language.lower() not in self.ghanaian_languages:
                raise ValueError(f"Unsupported language: {language}. Supported: {list(self.ghanaian_languages.keys())}")

            lang_code = self.ghanaian_languages[language.lower()]

            # Load TTS model for this language if not cached
            if lang_code not in self.tts_models:
                logger.info(f"Loading TTS model for language: {lang_code}")
                self.tts_models[lang_code] = await self._load_tts_model(lang_code)

            tts_model_dict = self.tts_models[lang_code]
            tokenizer = tts_model_dict["tokenizer"]
            model = tts_model_dict["model"]

            # Tokenize text (VITS tokenizer handles normalization)
            inputs = tokenizer(text=text, return_tensors="pt")

            # Move to device
            device = self.mms_config["device"]
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # Generate speech waveform
            with torch.no_grad():
                outputs = model(**inputs)
                waveform = outputs.waveform[0].cpu().numpy()

            # Save audio file
            audio_dir = Path("/tmp/mms_tts_audio")
            audio_dir.mkdir(exist_ok=True)
            audio_path = str(audio_dir / f"mms_tts_{language}_{hash(text)}.wav")

            # Save waveform as WAV file
            scipy.io.wavfile.write(
                audio_path,
                rate=model.config.sampling_rate,
                data=waveform
            )

            # Calculate duration
            duration = len(waveform) / model.config.sampling_rate

            logger.info(f"✅ Synthesized {duration:.2f}s of speech for language: {language}")

            return MMSTTSResult(
                audio_path=audio_path,
                duration=duration,
                language=language,
                text=text
            )

        except Exception as e:
            logger.error(f"Error synthesizing speech with MMS: {e}")
            raise

    async def stream_synthesize(
        self,
        text: str,
        language: str,
        voice_id: Optional[str] = None
    ):
        """
        Stream synthesized speech sentence-by-sentence using MMS TTS model.

        Args:
            text: Text to synthesize
            language: Language code (e.g., 'twi', 'ewe', 'ga', 'en')
            voice_id: Optional voice identifier (not used for MMS)

        Yields:
            bytes: WAV audio chunks for each sentence
        """
        try:
            import scipy.io.wavfile
            import io
            import re

            if not self.models_loaded:
                raise RuntimeError("Meta MMS models not initialized. Please ensure all dependencies are installed.")

            # Validate and get language code
            if language.lower() not in self.ghanaian_languages:
                raise ValueError(f"Unsupported language: {language}. Supported: {list(self.ghanaian_languages.keys())}")

            lang_code = self.ghanaian_languages[language.lower()]

            # Load TTS model for this language if not cached
            if lang_code not in self.tts_models:
                logger.info(f"Loading TTS model for language: {lang_code}")
                self.tts_models[lang_code] = await self._load_tts_model(lang_code)

            tts_model_dict = self.tts_models[lang_code]
            tokenizer = tts_model_dict["tokenizer"]
            model = tts_model_dict["model"]
            sample_rate = model.config.sampling_rate

            # Split text into sentences for streaming
            sentences = re.split(r'([.!?]+\s*)', text)
            sentences = [''.join(sentences[i:i+2]).strip() for i in range(0, len(sentences), 2) if sentences[i].strip()]

            if not sentences:
                sentences = [text]

            logger.info(f"[MMS STREAM] Streaming {len(sentences)} sentence(s) for language {language}")

            device = self.mms_config["device"]

            for i, sentence in enumerate(sentences):
                if not sentence.strip():
                    continue

                logger.info(f"[MMS STREAM] Processing sentence {i+1}/{len(sentences)}: '{sentence[:30]}...'")

                # Tokenize sentence
                inputs = tokenizer(text=sentence, return_tensors="pt")

                # Move to device
                inputs = {k: v.to(device) for k, v in inputs.items()}

                # Generate speech waveform
                with torch.no_grad():
                    outputs = model(**inputs)
                    waveform = outputs.waveform[0].cpu().numpy()

                # Convert to WAV bytes
                wav_io = io.BytesIO()
                scipy.io.wavfile.write(wav_io, rate=sample_rate, data=waveform)
                wav_bytes = wav_io.getvalue()

                logger.info(f"[MMS STREAM] Yielding chunk {i+1}: {len(wav_bytes)} bytes")
                yield wav_bytes

            logger.info(f"[MMS STREAM] Completed: {len(sentences)} chunks sent")

        except Exception as e:
            logger.error(f"[MMS STREAM] Error: {e}")
            raise
    
    async def detect_language(self, audio_path: str) -> str:
        """
        Detect language of audio using MMS LID model.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Detected language code
        """
        try:
            if not self.models_loaded or not self.lid_model:
                raise RuntimeError("MMS models not initialized")
            
            # Load and preprocess audio
            waveform, sample_rate = torchaudio.load(audio_path)
            
            # Resample if necessary
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                waveform = resampler(waveform)
                sample_rate = 16000
            
            # Convert to mono if stereo
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # Prepare input
            feature_extractor = self.lid_model["feature_extractor"]
            model = self.lid_model["model"]
            
            inputs = feature_extractor(
                waveform.squeeze().numpy(), 
                sampling_rate=sample_rate, 
                return_tensors="pt"
            )
            
            # Move to device
            device = self.mms_config["device"]
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Predict language
            with torch.no_grad():
                outputs = model(**inputs)
                predictions = torch.softmax(outputs.logits, dim=-1)
                predicted_lang_id = torch.argmax(predictions, dim=-1).item()
            
            # Get language name from model config
            lang_name = model.config.id2label[predicted_lang_id]
            
            # Map to our language codes
            for code, mms_code in self.ghanaian_languages.items():
                if mms_code in lang_name.lower():
                    return code
            
            return "unknown"
            
        except Exception as e:
            logger.error(f"Error detecting language with MMS: {e}")
            return "unknown"
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported Ghanaian languages."""
        return list(self.ghanaian_languages.keys())
    
    def get_language_code(self, language: str) -> Optional[str]:
        """Get MMS language code for given language."""
        return self.ghanaian_languages.get(language.lower())

# Global instance
mms_service = MetaMMSService()
