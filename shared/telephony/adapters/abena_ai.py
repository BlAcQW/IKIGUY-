"""
Abena AI Telephony Adapter

This module provides integration with Abena AI for Ghanaian language support
including Twi (Akan), Ghana Pidgin English, Ewe, Ga, and Dagbani.
"""

import asyncio
import logging
import aiohttp
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

from .base import BaseTelephonyAdapter
from ..interfaces import TelephonyEvent, TelephonyEventType
from ..models import ProviderSettings, CallContext


@dataclass
class AbenaAIConfig:
    """Configuration for Abena AI integration"""
    api_key: str
    base_url: str = "https://api.abena.mobobi.com"
    timeout: int = 30
    supported_languages: List[str] = None
    
    def __post_init__(self):
        if self.supported_languages is None:
            self.supported_languages = ["tw", "en-GH", "ee", "ga", "dag"]


@dataclass
class AbenaAICallInfo:
    """Abena AI specific call information"""
    call_id: str
    language: str
    voice_id: str
    session_id: str
    created_at: datetime
    metadata: Dict[str, Any] = None


class AbenaAITelephonyAdapter(BaseTelephonyAdapter):
    """
    Abena AI integration for Ghanaian language support
    
    Supports:
    - Twi (Akan) - Akuapem and Asante dialects
    - Ghana Pidgin English
    - Ewe
    - Ga
    - Dagbani
    """
    
    def __init__(self, settings: ProviderSettings):
        """
        Initialize Abena AI adapter
        
        Args:
            settings: Provider settings containing Abena AI configuration
        """
        super().__init__(settings)
        
        # Extract Abena AI specific configuration
        custom_settings = settings.custom_settings or {}
        self.config = AbenaAIConfig(
            api_key=custom_settings.get("api_key", ""),
            base_url=custom_settings.get("base_url", "https://api.abena.mobobi.com"),
            timeout=custom_settings.get("timeout", 30),
            supported_languages=custom_settings.get("supported_languages", ["tw", "en-GH", "ee", "ga", "dag"])
        )
        
        # Initialize session for API calls
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        
        # Call tracking
        self._active_calls: Dict[str, AbenaAICallInfo] = {}
        
        # Language detection patterns
        self._language_patterns = {
            "tw": ["ɛ", "ɔ", "ɛyɛ", "yɛ", "kɔ", "baa", "me", "wo", "ɔno", "saa"],
            "en-GH": ["make you", "dey", "fit", "chop", "wahala", "naija", "oga"],
            "ee": ["wo", "me", "nye", "le", "nyuie", "nyo", "kɔ"],
            "ga": ["mi", "wo", "ye", "le", "ŋɔ", "ŋɔɔ", "kɛ"],
            "dag": ["ka", "ya", "la", "ŋɔ", "ŋɔɔ", "kɛ", "damba", "yili"]
        }
        
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> bool:
        """
        Connect to Abena AI services
        
        Returns:
            bool: True if connection successful
        """
        try:
            if self._session is None:
                self._session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                    headers={
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json"
                    }
                )
            
            # Test connection with a simple API call
            async with self._session.get(f"{self.config.base_url}/health") as response:
                if response.status == 200:
                    self._connected = True
                    self.logger.info("Successfully connected to Abena AI")
                    return True
                else:
                    self.logger.error(f"Failed to connect to Abena AI: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error connecting to Abena AI: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Abena AI services
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            if self._session:
                await self._session.close()
                self._session = None
            
            self._connected = False
            self.logger.info("Disconnected from Abena AI")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from Abena AI: {e}")
            return False
    

    

    

    

    
    async def process_speech(self, audio_chunk: bytes, call_id: str) -> Dict[str, Any]:
        """
        Process speech using Abena AI ASR
        
        Args:
            audio_chunk: Audio data to process
            call_id: Call ID for context
            
        Returns:
            Dict[str, Any]: ASR results
        """
        if call_id not in self._active_calls:
            raise ValueError(f"Call {call_id} not found")
        
        call_info = self._active_calls[call_id]
        
        try:
            # Send audio to Abena AI for processing
            data = aiohttp.FormData()
            data.add_field('audio', audio_chunk, filename='audio.wav')
            data.add_field('session_id', call_info.session_id)
            data.add_field('language', call_info.language)
            
            async with self._session.post(
                f"{self.config.base_url}/asr/process",
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "text": result.get("text", ""),
                        "confidence": result.get("confidence", 0.0),
                        "language": result.get("detected_language", call_info.language),
                        "is_final": result.get("is_final", False)
                    }
                else:
                    self.logger.error(f"ASR processing failed: {response.status}")
                    return {"text": "", "confidence": 0.0, "language": call_info.language, "is_final": False}
                    
        except Exception as e:
            self.logger.error(f"Error processing speech: {e}")
            return {"text": "", "confidence": 0.0, "language": call_info.language, "is_final": False}
    
    async def synthesize_speech(self, text: str, call_id: str, 
                               voice_id: str = None) -> bytes:
        """
        Synthesize speech using Abena AI TTS
        
        Args:
            text: Text to synthesize
            call_id: Call ID for context
            voice_id: Voice ID to use (optional)
            
        Returns:
            bytes: Audio data
        """
        if call_id not in self._active_calls:
            raise ValueError(f"Call {call_id} not found")
        
        call_info = self._active_calls[call_id]
        if voice_id is None:
            voice_id = call_info.voice_id
        
        try:
            # Send text to Abena AI for synthesis
            tts_data = {
                "text": text,
                "session_id": call_info.session_id,
                "language": call_info.language,
                "voice_id": voice_id
            }
            
            async with self._session.post(
                f"{self.config.base_url}/tts/synthesize",
                json=tts_data
            ) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    return audio_data
                else:
                    self.logger.error(f"TTS synthesis failed: {response.status}")
                    return b""
                    
        except Exception as e:
            self.logger.error(f"Error synthesizing speech: {e}")
            return b""
    
    async def translate_text(self, text: str, source_lang: str, 
                           target_lang: str) -> str:
        """
        Translate text between languages
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            str: Translated text
        """
        try:
            # Send translation request to Abena AI
            translation_data = {
                "text": text,
                "source_language": source_lang,
                "target_language": target_lang
            }
            
            async with self._session.post(
                f"{self.config.base_url}/translate",
                json=translation_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("translated_text", text)
                else:
                    self.logger.error(f"Translation failed: {response.status}")
                    return text
                    
        except Exception as e:
            self.logger.error(f"Error translating text: {e}")
            return text
    
    def detect_language(self, text: str) -> str:
        """
        Detect the most likely Ghanaian language from text
        
        Args:
            text: Text to analyze
            
        Returns:
            str: Detected language code
        """
        text_lower = text.lower()
        language_scores = {}
        
        for lang, patterns in self._language_patterns.items():
            score = sum(1 for pattern in patterns if pattern.lower() in text_lower)
            language_scores[lang] = score
        
        # Return language with highest score, fallback to Twi
        if language_scores:
            detected_lang = max(language_scores, key=language_scores.get)
            if language_scores[detected_lang] > 0:
                return detected_lang
        
        return "tw"  # Default to Twi
    

    
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages
        
        Returns:
            List[str]: List of supported language codes
        """
        return self.config.supported_languages.copy()
    
    async def is_connected(self) -> bool:
        """
        Check if connected to the provider
        
        Returns:
            bool: True if connected
        """
        return self._connected
    
    async def _dial_impl(self, context: CallContext) -> str:
        """
        Provider-specific call initiation implementation
        
        Args:
            context: Call context information
            
        Returns:
            str: Unique call identifier
        """
        if not self._connected:
            raise RuntimeError("Not connected to Abena AI")
        
        # Use the existing dial method logic
        language = context.metadata.get("language", "tw")
        voice_id = context.metadata.get("voice_id", "default")
        
        if language not in self.config.supported_languages:
            self.logger.warning(f"Language {language} not supported, falling back to 'tw'")
            language = "tw"
        
        call_id = f"abena_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{context.destination}"
        
        # Create call session
        call_info = AbenaAICallInfo(
            call_id=call_id,
            language=language,
            voice_id=voice_id,
            session_id=f"session_{call_id}",
            created_at=datetime.utcnow(),
            metadata={
                "destination": context.destination,
                "caller_id": context.source,
                "language": language,
                "voice_id": voice_id
            }
        )
        
        self._active_calls[call_id] = call_info
        
        # Initialize call session with Abena AI
        try:
            session_data = {
                "session_id": call_info.session_id,
                "language": language,
                "voice_id": voice_id,
                "destination": context.destination,
                "caller_id": context.source
            }
            
            async with self._session.post(
                f"{self.config.base_url}/calls/initiate",
                json=session_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info(f"Call initiated: {call_id}")
                    return call_id
                else:
                    del self._active_calls[call_id]
                    raise RuntimeError(f"Failed to initiate call: {response.status}")
                    
        except Exception as e:
            if call_id in self._active_calls:
                del self._active_calls[call_id]
            self.logger.error(f"Error initiating call: {e}")
            raise
    
    async def _hangup_impl(self, call_id: str) -> bool:
        """
        Provider-specific call termination implementation
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            bool: True if call was successfully ended
        """
        if call_id not in self._active_calls:
            self.logger.warning(f"Call {call_id} not found")
            return False
        
        try:
            call_info = self._active_calls[call_id]
            
            # End call session with Abena AI
            async with self._session.post(
                f"{self.config.base_url}/calls/end",
                json={"session_id": call_info.session_id}
            ) as response:
                if response.status == 200:
                    del self._active_calls[call_id]
                    self.logger.info(f"Call ended: {call_id}")
                    return True
                else:
                    self.logger.error(f"Failed to end call: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error ending call: {e}")
            return False
    
    async def _get_events_impl(self, call_id: str) -> List[TelephonyEvent]:
        """
        Provider-specific event retrieval implementation
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            List[TelephonyEvent]: List of telephony events
        """
        if call_id not in self._active_calls:
            return []
        
        try:
            call_info = self._active_calls[call_id]
            
            # Get events from Abena AI
            async with self._session.get(
                f"{self.config.base_url}/calls/events",
                params={"session_id": call_info.session_id}
            ) as response:
                if response.status == 200:
                    events_data = await response.json()
                    return self._parse_events(events_data, call_id)
                else:
                    self.logger.error(f"Failed to get events: {response.status}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error getting events: {e}")
            return []
    
    async def _get_costs_impl(self, call_id: str) -> Dict[str, float]:
        """
        Provider-specific cost calculation implementation
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            Dict[str, float]: Cost breakdown by component
        """
        if call_id not in self._active_calls:
            return {}
        
        try:
            call_info = self._active_calls[call_id]
            
            # Get costs from Abena AI
            async with self._session.get(
                f"{self.config.base_url}/calls/costs",
                params={"session_id": call_info.session_id}
            ) as response:
                if response.status == 200:
                    costs_data = await response.json()
                    return {
                        "total_cost": costs_data.get("total_cost", 0.0),
                        "asr_cost": costs_data.get("asr_cost", 0.0),
                        "tts_cost": costs_data.get("tts_cost", 0.0),
                        "translation_cost": costs_data.get("translation_cost", 0.0)
                    }
                else:
                    self.logger.error(f"Failed to get costs: {response.status}")
                    return {}
                    
        except Exception as e:
            self.logger.error(f"Error getting costs: {e}")
            return {}
    
    async def _get_cost_per_minute(self) -> Optional[float]:
        """Get cost per minute for this provider"""
        # Default cost for Abena AI (this would be configurable)
        return 0.05  # $0.05 per minute
    
    async def _get_supported_regions(self) -> List[str]:
        """Get list of supported geographic regions"""
        return ["GH", "NG", "KE", "ZA", "EG"]  # Ghana, Nigeria, Kenya, South Africa, Egypt
    
    async def _get_supported_features(self) -> List[str]:
        """Get list of supported features"""
        return [
            "ghanaian_languages",
            "asr",
            "tts",
            "translation",
            "language_detection",
            "voice_cloning",
            "offline_processing"
        ]
    
    def _parse_events(self, events_data: List[Dict], call_id: str) -> List[TelephonyEvent]:
        """
        Parse Abena AI events into TelephonyEvent objects
        
        Args:
            events_data: Raw events data from Abena AI
            call_id: Call ID for context
            
        Returns:
            List[TelephonyEvent]: Parsed telephony events
        """
        events = []
        
        for event_data in events_data:
            event_type = event_data.get("type", "unknown")
            
            # Map Abena AI event types to TelephonyEventType
            if event_type == "call_started":
                telephony_event_type = TelephonyEventType.CALL_STARTED
            elif event_type == "call_ended":
                telephony_event_type = TelephonyEventType.CALL_ENDED
            elif event_type == "speech_detected":
                telephony_event_type = TelephonyEventType.SPEECH_DETECTED
            elif event_type == "speech_ended":
                telephony_event_type = TelephonyEventType.SPEECH_ENDED
            elif event_type == "transcription":
                telephony_event_type = TelephonyEventType.TRANSCRIPTION
            else:
                telephony_event_type = TelephonyEventType.UNKNOWN_EVENT
            
            event = TelephonyEvent(
                event_type=telephony_event_type,
                call_id=call_id,
                provider=self.settings.provider_id,
                timestamp=datetime.fromisoformat(event_data.get("timestamp", datetime.utcnow().isoformat())),
                data=event_data.get("data", {}),
                metadata=event_data.get("metadata", {})
            )
            events.append(event)
        
        return events
