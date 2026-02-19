"""
OpenAI Whisper Telephony Adapter

This module provides integration with OpenAI Whisper for speech-to-text processing
with support for 99+ languages and excellent performance for low-resource languages.
"""

import asyncio
import logging
import aiohttp
import json
import base64
import hashlib
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid

from .base import BaseTelephonyAdapter
from ..interfaces import TelephonyEvent, TelephonyEventType
from ..models import ProviderSettings, CallContext


@dataclass
class WhisperConfig:
    """Configuration for OpenAI Whisper integration"""
    api_key: str
    model: str = "whisper-1"
    base_url: str = "https://api.openai.com/v1"
    timeout: int = 30
    supported_languages: List[str] = None
    response_format: str = "verbose_json"  # json, text, srt, verbose_json, vtt
    
    def __post_init__(self):
        if self.supported_languages is None:
            # Whisper supports 99+ languages
            self.supported_languages = [
                # Major languages
                "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
                "ar", "hi", "bn", "ur", "tr", "pl", "nl", "sv", "da", "no",
                "fi", "cs", "hu", "ro", "bg", "hr", "sk", "sl", "et", "lv",
                "lt", "mt", "el", "he", "th", "vi", "id", "ms", "tl", "ta",
                "te", "kn", "ml", "gu", "pa", "or", "as", "ne", "si", "my",
                "km", "lo", "ka", "hy", "az", "be", "bs", "ca", "cy", "eu",
                "fa", "gl", "is", "mk", "mn", "mr", "nb", "nn", "oc", "ps",
                "sq", "sr", "sw", "tg", "tk", "uk", "uz", "yi", "zu",
                # Regional variants
                "en-US", "en-GB", "en-AU", "en-CA", "en-IN", "en-IE", "en-ZA",
                "es-ES", "es-MX", "es-AR", "es-CO", "es-PE", "es-VE", "es-CL",
                "fr-FR", "fr-CA", "fr-CH", "fr-BE", "fr-LU", "fr-MA", "fr-DZ",
                "de-DE", "de-AT", "de-CH", "de-LU", "de-LI", "de-BE",
                "it-IT", "it-CH", "it-SM", "pt-BR", "pt-PT", "pt-AO", "pt-MZ",
                "ru-RU", "ru-UA", "ru-KZ", "ru-BY", "ja-JP", "ko-KR",
                "zh-CN", "zh-TW", "zh-HK", "zh-SG", "ar-SA", "ar-EG", "ar-AE",
                "ar-MA", "ar-DZ", "ar-TN", "ar-LY", "ar-IQ", "ar-SY", "ar-LB",
                "hi-IN", "bn-IN", "ur-PK", "tr-TR", "pl-PL", "nl-NL", "nl-BE",
                "sv-SE", "da-DK", "no-NO", "fi-FI", "cs-CZ", "hu-HU", "ro-RO",
                "bg-BG", "hr-HR", "sk-SK", "sl-SI", "et-EE", "lv-LV", "lt-LT",
                "mt-MT", "el-GR", "he-IL", "th-TH", "vi-VN", "id-ID", "ms-MY",
                "tl-PH", "ta-IN", "te-IN", "kn-IN", "ml-IN", "gu-IN", "pa-IN",
                "or-IN", "as-IN", "ne-NP", "si-LK", "my-MM", "km-KH", "lo-LA"
            ]


@dataclass
class WhisperCallInfo:
    """OpenAI Whisper specific call information"""
    call_id: str
    language: str
    model: str
    session_id: str
    created_at: datetime
    transcription_history: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None


class WhisperAdapter(BaseTelephonyAdapter):
    """
    OpenAI Whisper integration for speech-to-text processing
    
    Features:
    - Speech-to-Text with 99+ language support
    - Excellent performance for low-resource languages
    - Automatic language detection
    - Timestamp and confidence information
    - Support for various audio formats
    - Real-time transcription capabilities
    """
    
    def __init__(self, settings: ProviderSettings):
        """
        Initialize OpenAI Whisper adapter
        
        Args:
            settings: Provider settings containing OpenAI configuration
        """
        super().__init__(settings)
        
        # Extract OpenAI Whisper specific configuration
        custom_settings = settings.custom_settings or {}
        self.config = WhisperConfig(
            api_key=custom_settings.get("api_key", ""),
            model=custom_settings.get("model", "whisper-1"),
            base_url=custom_settings.get("base_url", "https://api.openai.com/v1"),
            timeout=custom_settings.get("timeout", 30),
            supported_languages=custom_settings.get("supported_languages"),
            response_format=custom_settings.get("response_format", "verbose_json")
        )
        
        # Initialize session for API calls
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        
        # Call tracking
        self._active_calls: Dict[str, WhisperCallInfo] = {}
        
        # Language detection patterns (Whisper is excellent at auto-detection)
        self._language_patterns = {
            "en": ["the", "and", "for", "with", "this", "that", "have", "from", "they", "said"],
            "es": ["el", "la", "de", "que", "y", "en", "un", "es", "se", "no", "te", "lo"],
            "fr": ["le", "la", "de", "et", "un", "une", "est", "pour", "dans", "sur", "avec", "son"],
            "de": ["der", "die", "das", "und", "in", "den", "von", "zu", "mit", "sich", "auf", "für"],
            "it": ["il", "la", "di", "e", "un", "una", "che", "in", "per", "con", "su", "tra"],
            "pt": ["o", "a", "de", "e", "um", "uma", "que", "em", "para", "com", "do", "da"],
            "ru": ["и", "в", "не", "на", "я", "быть", "он", "как", "тот", "его", "от", "за"],
            "ja": ["の", "に", "は", "を", "た", "が", "で", "て", "と", "し", "から", "まで"],
            "ko": ["이", "가", "을", "를", "에", "에서", "로", "으로", "와", "과", "의", "도"],
            "zh": ["的", "了", "在", "是", "我", "有", "和", "人", "这", "中", "大", "为"],
            "ar": ["في", "من", "إلى", "على", "أن", "هذا", "هذه", "كان", "هو", "هي", "مع", "عن"],
            "hi": ["का", "की", "के", "में", "है", "और", "से", "पर", "को", "यह", "वह", "कि"]
        }
        
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> bool:
        """
        Connect to OpenAI Whisper API
        
        Returns:
            bool: True if connection successful
        """
        try:
            if self._session is None:
                self._session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                )
            
            # Test connection with a simple API call
            test_url = f"{self.config.base_url}/models"
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            async with self._session.get(test_url, headers=headers) as response:
                if response.status == 200:
                    self._connected = True
                    self.logger.info("Successfully connected to OpenAI Whisper API")
                    return True
                else:
                    self.logger.error(f"Failed to connect to OpenAI Whisper API: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error connecting to OpenAI Whisper API: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from OpenAI Whisper API
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            if self._session:
                await self._session.close()
                self._session = None
            
            self._connected = False
            
            self.logger.info("Disconnected from OpenAI Whisper API")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from OpenAI Whisper API: {e}")
            return False
    
    async def dial(self, to: str, from_: str, context: CallContext) -> str:
        """
        Initiate a call using OpenAI Whisper
        
        Args:
            to: Destination number
            from_: Source number
            context: Call context
            
        Returns:
            str: Call ID
        """
        try:
            call_id = str(uuid.uuid4())
            session_id = str(uuid.uuid4())
            
            # Determine language (Whisper can auto-detect)
            language = context.language or "auto"
            
            # Create call info
            call_info = WhisperCallInfo(
                call_id=call_id,
                language=language,
                model=self.config.model,
                session_id=session_id,
                created_at=datetime.now(),
                transcription_history=[],
                metadata=context.custom_data
            )
            
            self._active_calls[call_id] = call_info
            
            # Emit call started event
            event = TelephonyEvent(
                event_type=TelephonyEventType.CALL_STARTED,
                call_id=call_id,
                timestamp=datetime.now(),
                provider="openai_whisper",
                data={
                    "to": to,
                    "from": from_,
                    "language": language,
                    "model": self.config.model,
                    "session_id": session_id
                }
            )
            
            await self._emit_event(event)
            
            self.logger.info(f"Call {call_id} initiated to {to} using OpenAI Whisper")
            return call_id
            
        except Exception as e:
            self.logger.error(f"Error initiating call: {e}")
            raise
    
    async def hangup(self, call_id: str) -> bool:
        """
        End a call
        
        Args:
            call_id: Call ID to end
            
        Returns:
            bool: True if call ended successfully
        """
        try:
            if call_id not in self._active_calls:
                self.logger.warning(f"Call {call_id} not found")
                return False
            
            call_info = self._active_calls[call_id]
            
            # Emit call ended event
            event = TelephonyEvent(
                event_type=TelephonyEventType.CALL_ENDED,
                call_id=call_id,
                timestamp=datetime.now(),
                provider="openai_whisper",
                data={
                    "duration": (datetime.now() - call_info.created_at).total_seconds(),
                    "language": call_info.language,
                    "model": call_info.model,
                    "transcription_count": len(call_info.transcription_history)
                }
            )
            
            await self._emit_event(event)
            
            # Remove from active calls
            del self._active_calls[call_id]
            
            self.logger.info(f"Call {call_id} ended")
            return True
            
        except Exception as e:
            self.logger.error(f"Error ending call {call_id}: {e}")
            return False
    
    async def send_audio(self, call_id: str, audio_data: bytes, format: str = "wav") -> bool:
        """
        Send audio for speech-to-text processing using OpenAI Whisper
        
        Args:
            call_id: Call ID
            audio_data: Audio data bytes
            format: Audio format (wav, mp3, etc.)
            
        Returns:
            bool: True if audio processed successfully
        """
        try:
            if call_id not in self._active_calls:
                self.logger.warning(f"Call {call_id} not found")
                return False
            
            call_info = self._active_calls[call_id]
            
            # OpenAI Whisper API endpoint
            whisper_url = f"{self.config.base_url}/audio/transcriptions"
            
            headers = {
                "Authorization": f"Bearer {self.config.api_key}"
            }
            
            # Prepare form data
            data = aiohttp.FormData()
            data.add_field('file', audio_data, filename=f'audio.{format}', content_type=f'audio/{format}')
            data.add_field('model', self.config.model)
            data.add_field('response_format', self.config.response_format)
            
            # Add language if specified (auto-detect if not specified)
            if call_info.language != "auto":
                data.add_field('language', call_info.language)
            
            # Add optional parameters
            data.add_field('temperature', '0.0')  # Deterministic output
            data.add_field('prompt', 'This is a phone conversation.')  # Context prompt
            
            async with self._session.post(whisper_url, headers=headers, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if self.config.response_format == "verbose_json":
                        # Handle verbose JSON response
                        if result.get("text"):
                            transcript = result["text"]
                            confidence = result.get("confidence", 0.0)
                            detected_language = result.get("language", call_info.language)
                            
                            # Update call info with detected language
                            if call_info.language == "auto":
                                call_info.language = detected_language
                            
                            # Store transcription in history
                            transcription_entry = {
                                "text": transcript,
                                "confidence": confidence,
                                "language": detected_language,
                                "timestamp": datetime.now().isoformat(),
                                "segments": result.get("segments", [])
                            }
                            call_info.transcription_history.append(transcription_entry)
                            
                            # Emit transcription event
                            event = TelephonyEvent(
                                event_type=TelephonyEventType.TRANSCRIPTION,
                                call_id=call_id,
                                timestamp=datetime.now(),
                                data={
                                    "text": transcript,
                                    "confidence": confidence,
                                    "language": detected_language,
                                    "segments": result.get("segments", []),
                                    "provider": "openai_whisper"
                                }
                            )
                            
                            await self._emit_event(event)
                            
                            self.logger.debug(f"Transcription for call {call_id}: {transcript}")
                            return True
                        else:
                            self.logger.warning(f"No transcription result for call {call_id}")
                            return False
                    else:
                        # Handle simple text response
                        transcript = result.get("text", "")
                        if transcript:
                            # Store transcription in history
                            transcription_entry = {
                                "text": transcript,
                                "confidence": 0.0,  # Not available in simple format
                                "language": call_info.language,
                                "timestamp": datetime.now().isoformat(),
                                "segments": []
                            }
                            call_info.transcription_history.append(transcription_entry)
                            
                            # Emit transcription event
                            event = TelephonyEvent(
                                event_type=TelephonyEventType.TRANSCRIPTION,
                                call_id=call_id,
                                timestamp=datetime.now(),
                                data={
                                    "text": transcript,
                                    "confidence": 0.0,
                                    "language": call_info.language,
                                    "segments": [],
                                    "provider": "openai_whisper"
                                }
                            )
                            
                            await self._emit_event(event)
                            
                            self.logger.debug(f"Transcription for call {call_id}: {transcript}")
                            return True
                        else:
                            self.logger.warning(f"No transcription result for call {call_id}")
                            return False
                else:
                    error_text = await response.text()
                    self.logger.error(f"Whisper API failed for call {call_id}: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error processing audio for call {call_id}: {e}")
            return False
    
    async def synthesize_speech(self, call_id: str, text: str, voice_name: str = None) -> bytes:
        """
        Note: OpenAI Whisper is speech-to-text only. This method returns empty bytes.
        For text-to-speech, use Azure Speech Services or Google Cloud TTS.
        
        Args:
            call_id: Call ID
            text: Text to synthesize
            voice_name: Voice to use (not applicable for Whisper)
            
        Returns:
            bytes: Empty bytes (Whisper doesn't support TTS)
        """
        self.logger.warning("OpenAI Whisper does not support text-to-speech. Use Azure Speech Services or Google Cloud TTS for TTS functionality.")
        return b""
    
    async def detect_language(self, audio_data: bytes) -> str:
        """
        Detect language from audio using OpenAI Whisper
        
        Args:
            audio_data: Audio data bytes
            
        Returns:
            str: Detected language code
        """
        try:
            # Use Whisper API to detect language
            whisper_url = f"{self.config.base_url}/audio/transcriptions"
            
            headers = {
                "Authorization": f"Bearer {self.config.api_key}"
            }
            
            # Prepare form data for language detection
            data = aiohttp.FormData()
            data.add_field('file', audio_data, filename='audio.wav', content_type='audio/wav')
            data.add_field('model', self.config.model)
            data.add_field('response_format', 'verbose_json')
            data.add_field('language', 'auto')  # Force auto-detection
            
            async with self._session.post(whisper_url, headers=headers, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    detected_language = result.get("language", "en")
                    
                    self.logger.debug(f"Language detected by Whisper: {detected_language}")
                    return detected_language
                else:
                    self.logger.warning(f"Language detection failed: {response.status}")
                    return "en"
                    
        except Exception as e:
            self.logger.error(f"Error detecting language: {e}")
            return "en"
    
    async def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages
        
        Returns:
            List[str]: List of supported language codes
        """
        return self.config.supported_languages
    
    async def get_supported_voices(self, language: str = None) -> List[str]:
        """
        Get list of supported voices (not applicable for Whisper)
        
        Args:
            language: Language code (not applicable for Whisper)
            
        Returns:
            List[str]: Empty list (Whisper doesn't support TTS)
        """
        return []  # Whisper doesn't support text-to-speech
    
    async def get_call_info(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a call
        
        Args:
            call_id: Call ID
            
        Returns:
            Optional[Dict[str, Any]]: Call information
        """
        if call_id in self._active_calls:
            call_info = self._active_calls[call_id]
            return {
                "call_id": call_info.call_id,
                "language": call_info.language,
                "model": call_info.model,
                "session_id": call_info.session_id,
                "created_at": call_info.created_at.isoformat(),
                "transcription_count": len(call_info.transcription_history),
                "duration": (datetime.now() - call_info.created_at).total_seconds(),
                "provider": "openai_whisper"
            }
        return None
    
    async def is_connected(self) -> bool:
        """
        Check if connected to OpenAI Whisper API
        
        Returns:
            bool: True if connected
        """
        return self._connected
    
    async def get_provider_info(self) -> Dict[str, Any]:
        """
        Get provider information
        
        Returns:
            Dict[str, Any]: Provider information
        """
        return {
            "provider_id": self.settings.provider_id,
            "name": "OpenAI Whisper",
            "version": "1.0.0",
            "supported_languages": len(self.config.supported_languages),
            "supported_voices": 0,  # Whisper doesn't support TTS
            "model": self.config.model,
            "features": await self._get_supported_features(),
            "cost_per_minute": await self._get_cost_per_minute(),
            "supported_regions": await self._get_supported_regions()
        }
    
    async def _dial_impl(self, context: CallContext) -> str:
        """
        Whisper-specific call initiation implementation
        
        Args:
            context: Call context information
            
        Returns:
            str: Unique call identifier
        """
        try:
            # Generate unique call ID
            call_id = str(uuid.uuid4())
            
            # Create Whisper call info
            whisper_call_info = WhisperCallInfo(
                call_id=call_id,
                language=context.metadata.get('language', 'en'),
                model=self.config.model,
                session_id=str(uuid.uuid4()),
                created_at=datetime.utcnow(),
                transcription_history=[],
                metadata=context.metadata
            )
            
            # Store call info
            self._calls[call_id] = whisper_call_info
            
            self.logger.info(f"Whisper call initiated: {call_id}")
            return call_id
            
        except Exception as e:
            self.logger.error(f"Failed to initiate Whisper call: {e}")
            raise
    
    async def _hangup_impl(self, call_id: str) -> bool:
        """
        Whisper-specific call termination implementation
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            bool: True if call was successfully ended
        """
        try:
            if call_id in self._calls:
                del self._calls[call_id]
                self.logger.info(f"Whisper call ended: {call_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to end Whisper call {call_id}: {e}")
            return False
    
    async def _get_events_impl(self, call_id: str) -> List[TelephonyEvent]:
        """
        Whisper-specific event retrieval implementation
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            List[TelephonyEvent]: List of telephony events
        """
        try:
            if call_id not in self._calls:
                return []
            
            # Return events for the call
            events = []
            call_info = self._calls[call_id]
            
            # Add call start event
            events.append(self._create_telephony_event(
                "call_started",
                call_id,
                {
                    "language": call_info.language,
                    "model": call_info.model,
                    "session_id": call_info.session_id
                }
            ))
            
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to get Whisper events for call {call_id}: {e}")
            return []
    
    async def _get_costs_impl(self, call_id: str) -> Dict[str, float]:
        """
        Whisper-specific cost calculation implementation
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            Dict[str, float]: Cost breakdown by component
        """
        try:
            if call_id not in self._calls:
                return {}
            
            # Whisper pricing (approximate)
            stt_cost_per_minute = 0.006  # Speech-to-Text
            
            # Calculate costs based on usage
            call_info = self._calls[call_id]
            duration_minutes = 1.0  # Default duration
            
            return {
                "speech_to_text": duration_minutes * stt_cost_per_minute,
                "language_detection": 0.0005,  # Fixed cost
                "total": (duration_minutes * stt_cost_per_minute) + 0.0005
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get Whisper costs for call {call_id}: {e}")
            return {}
    
    async def _get_cost_per_minute(self) -> Optional[float]:
        """Get cost per minute for OpenAI Whisper"""
        # Whisper pricing: $0.006 per minute for STT
        return 0.006
    
    async def _get_supported_regions(self) -> List[str]:
        """Get list of supported geographic regions for Whisper"""
        return [
            "global"  # Whisper is available globally
        ]
    
    async def _get_supported_features(self) -> List[str]:
        """Get list of supported features for Whisper"""
        return [
            "speech_to_text",
            "language_detection",
            "automatic_punctuation",
            "timestamp_information",
            "confidence_scoring",
            "low_resource_language_support",
            "real_time_transcription",
            "context_prompts",
            "audio_format_conversion"
        ]
    
    async def get_transcription_history(self, call_id: str) -> List[Dict[str, Any]]:
        """
        Get transcription history for a call
        
        Args:
            call_id: Call ID
            
        Returns:
            List[Dict[str, Any]]: Transcription history
        """
        if call_id in self._active_calls:
            return self._active_calls[call_id].transcription_history
        return []
    
    async def get_audio_segments(self, call_id: str) -> List[Dict[str, Any]]:
        """
        Get detailed audio segments for a call
        
        Args:
            call_id: Call ID
            
        Returns:
            List[Dict[str, Any]]: Audio segments with timestamps
        """
        if call_id in self._active_calls:
            call_info = self._active_calls[call_id]
            segments = []
            for transcription in call_info.transcription_history:
                segments.extend(transcription.get("segments", []))
            return segments
        return []
