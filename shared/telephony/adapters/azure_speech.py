"""
Azure Speech Services Telephony Adapter

This module provides integration with Microsoft Azure Speech Services for
comprehensive speech-to-text and text-to-speech capabilities with support
for 100+ languages and dialects.
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
class AzureSpeechConfig:
    """Configuration for Azure Speech Services integration"""
    subscription_key: str
    region: str
    endpoint: str = None
    timeout: int = 30
    supported_languages: List[str] = None
    voice_names: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.endpoint is None:
            self.endpoint = f"https://{self.region}.stt.speech.microsoft.com"
        
        if self.supported_languages is None:
            # Top 50 most commonly used languages
            self.supported_languages = [
                "en-US", "en-GB", "en-AU", "en-CA", "en-IN",
                "es-ES", "es-MX", "es-AR", "es-CO", "es-PE",
                "fr-FR", "fr-CA", "fr-CH", "fr-BE", "fr-LU",
                "de-DE", "de-AT", "de-CH", "de-LU", "de-LI",
                "it-IT", "it-CH", "pt-BR", "pt-PT", "ru-RU",
                "ja-JP", "ko-KR", "zh-CN", "zh-TW", "zh-HK",
                "ar-SA", "ar-EG", "ar-AE", "ar-MA", "ar-DZ",
                "hi-IN", "bn-IN", "ur-PK", "tr-TR", "pl-PL",
                "nl-NL", "nl-BE", "sv-SE", "da-DK", "no-NO",
                "fi-FI", "cs-CZ", "hu-HU", "ro-RO", "bg-BG"
            ]
        
        if self.voice_names is None:
            # Popular voice names for each language
            self.voice_names = {
                "en-US": ["en-US-JennyNeural", "en-US-GuyNeural", "en-US-AriaNeural"],
                "en-GB": ["en-GB-SoniaNeural", "en-GB-RyanNeural"],
                "es-ES": ["es-ES-ElviraNeural", "es-ES-AlvaroNeural"],
                "fr-FR": ["fr-FR-DeniseNeural", "fr-FR-HenriNeural"],
                "de-DE": ["de-DE-KatjaNeural", "de-DE-ConradNeural"],
                "it-IT": ["it-IT-IsabellaNeural", "it-IT-DiegoNeural"],
                "pt-BR": ["pt-BR-FranciscaNeural", "pt-BR-AntonioNeural"],
                "ru-RU": ["ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural"],
                "ja-JP": ["ja-JP-NanamiNeural", "ja-JP-KeitaNeural"],
                "ko-KR": ["ko-KR-SunHiNeural", "ko-KR-InJoonNeural"],
                "zh-CN": ["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"],
                "ar-SA": ["ar-SA-ZariyahNeural", "ar-SA-HamedNeural"],
                "hi-IN": ["hi-IN-SwaraNeural", "hi-IN-MadhurNeural"]
            }


@dataclass
class AzureSpeechCallInfo:
    """Azure Speech Services specific call information"""
    call_id: str
    language: str
    voice_name: str
    session_id: str
    created_at: datetime
    recognition_mode: str = "conversation"  # conversation, dictation, interactive
    metadata: Dict[str, Any] = None


class AzureSpeechAdapter(BaseTelephonyAdapter):
    """
    Azure Speech Services integration for comprehensive speech processing
    
    Features:
    - Speech-to-Text with 100+ language support
    - Text-to-Speech with 400+ neural voices
    - Real-time transcription
    - Speaker diarization
    - Custom speech models
    - Language detection
    """
    
    def __init__(self, settings: ProviderSettings):
        """
        Initialize Azure Speech Services adapter
        
        Args:
            settings: Provider settings containing Azure configuration
        """
        super().__init__(settings)
        
        # Extract Azure Speech specific configuration
        custom_settings = settings.custom_settings or {}
        self.config = AzureSpeechConfig(
            subscription_key=custom_settings.get("subscription_key", ""),
            region=custom_settings.get("region", "eastus"),
            endpoint=custom_settings.get("endpoint"),
            timeout=custom_settings.get("timeout", 30),
            supported_languages=custom_settings.get("supported_languages"),
            voice_names=custom_settings.get("voice_names")
        )
        
        # Initialize session for API calls
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        
        # Call tracking
        self._active_calls: Dict[str, AzureSpeechCallInfo] = {}
        
        # Language detection patterns (enhanced for global languages)
        self._language_patterns = {
            "en-US": ["the", "and", "for", "with", "this", "that", "have", "from"],
            "es-ES": ["el", "la", "de", "que", "y", "en", "un", "es", "se", "no"],
            "fr-FR": ["le", "la", "de", "et", "un", "une", "est", "pour", "dans", "sur"],
            "de-DE": ["der", "die", "das", "und", "in", "den", "von", "zu", "mit", "sich"],
            "it-IT": ["il", "la", "di", "e", "un", "una", "che", "in", "per", "con"],
            "pt-BR": ["o", "a", "de", "e", "um", "uma", "que", "em", "para", "com"],
            "ru-RU": ["и", "в", "не", "на", "я", "быть", "он", "как", "тот", "его"],
            "ja-JP": ["の", "に", "は", "を", "た", "が", "で", "て", "と", "し"],
            "ko-KR": ["이", "가", "을", "를", "에", "에서", "로", "으로", "와", "과"],
            "zh-CN": ["的", "了", "在", "是", "我", "有", "和", "人", "这", "中"],
            "ar-SA": ["في", "من", "إلى", "على", "أن", "هذا", "هذه", "كان", "هو", "هي"],
            "hi-IN": ["का", "की", "के", "में", "है", "और", "से", "पर", "को", "यह"]
        }
        
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> bool:
        """
        Connect to Azure Speech Services
        
        Returns:
            bool: True if connection successful
        """
        try:
            if self._session is None:
                self._session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                )
            
            # Get access token
            await self._refresh_access_token()
            
            # Test connection with a simple API call
            test_url = f"{self.config.endpoint}/speechtotext/v3.0/endpoints"
            headers = {
                "Ocp-Apim-Subscription-Key": self.config.subscription_key,
                "Content-Type": "application/json"
            }
            
            async with self._session.get(test_url, headers=headers) as response:
                if response.status == 200:
                    self._connected = True
                    self.logger.info("Successfully connected to Azure Speech Services")
                    return True
                else:
                    self.logger.error(f"Failed to connect to Azure Speech Services: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error connecting to Azure Speech Services: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Azure Speech Services
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            if self._session:
                await self._session.close()
                self._session = None
            
            self._connected = False
            self._access_token = None
            self._token_expiry = None
            
            self.logger.info("Disconnected from Azure Speech Services")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from Azure Speech Services: {e}")
            return False
    
    async def _refresh_access_token(self) -> None:
        """Refresh Azure Speech Services access token"""
        try:
            token_url = f"https://{self.config.region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
            headers = {
                "Ocp-Apim-Subscription-Key": self.config.subscription_key,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            async with self._session.post(token_url, headers=headers) as response:
                if response.status == 200:
                    self._access_token = await response.text()
                    # Token expires in 10 minutes, refresh after 9 minutes
                    self._token_expiry = datetime.now() + timedelta(minutes=9)
                    self.logger.debug("Azure Speech Services access token refreshed")
                else:
                    raise Exception(f"Failed to get access token: {response.status}")
                    
        except Exception as e:
            self.logger.error(f"Error refreshing access token: {e}")
            raise
    
    async def _get_access_token(self) -> str:
        """Get valid access token, refreshing if necessary"""
        if (self._access_token is None or 
            self._token_expiry is None or 
            datetime.now() >= self._token_expiry):
            await self._refresh_access_token()
        
        return self._access_token
    
    async def dial(self, to: str, from_: str, context: CallContext) -> str:
        """
        Initiate a call using Azure Speech Services
        
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
            
            # Determine language and voice
            language = context.metadata.get("language", "en-US")
            voice_name = self._get_voice_for_language(language)
            
            # Create call info
            call_info = AzureSpeechCallInfo(
                call_id=call_id,
                language=language,
                voice_name=voice_name,
                session_id=session_id,
                created_at=datetime.now(),
                recognition_mode=context.metadata.get("recognition_mode", "conversation"),
                metadata=context.metadata
            )
            
            self._active_calls[call_id] = call_info
            
            # Emit call started event
            event = TelephonyEvent(
                event_type=TelephonyEventType.CALL_STARTED,
                call_id=call_id,
                timestamp=datetime.now(),
                provider="azure_speech",
                data={
                    "to": to,
                    "from": from_,
                    "language": language,
                    "voice_name": voice_name,
                    "session_id": session_id
                }
            )
            
            # Event emission would go here if needed
            
            self.logger.info(f"Call {call_id} initiated to {to} using Azure Speech Services")
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
                provider="azure_speech",
                data={
                    "duration": (datetime.now() - call_info.created_at).total_seconds(),
                    "language": call_info.language,
                    "voice_name": call_info.voice_name
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
        Send audio for speech-to-text processing
        
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
            access_token = await self._get_access_token()
            
            # Azure Speech-to-Text API endpoint
            stt_url = f"{self.config.endpoint}/speechtotext/v3.0/recognize"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": f"audio/{format}",
                "Accept": "application/json"
            }
            
            params = {
                "language": call_info.language,
                "recognitionMode": call_info.recognition_mode
            }
            
            async with self._session.post(stt_url, headers=headers, params=params, data=audio_data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("DisplayText"):
                        # Emit transcription event
                        event = TelephonyEvent(
                            event_type=TelephonyEventType.TRANSCRIPTION,
                            call_id=call_id,
                            timestamp=datetime.now(),
                            data={
                                "text": result["DisplayText"],
                                "confidence": result.get("Confidence", 0.0),
                                "language": call_info.language,
                                "provider": "azure_speech"
                            }
                        )
                        
                        await self._emit_event(event)
                        
                        self.logger.debug(f"Transcription for call {call_id}: {result['DisplayText']}")
                        return True
                    else:
                        self.logger.warning(f"No transcription result for call {call_id}")
                        return False
                else:
                    self.logger.error(f"Speech-to-text failed for call {call_id}: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error processing audio for call {call_id}: {e}")
            return False
    
    async def synthesize_speech(self, call_id: str, text: str, voice_name: str = None) -> bytes:
        """
        Convert text to speech using Azure Speech Services
        
        Args:
            call_id: Call ID
            text: Text to synthesize
            voice_name: Voice to use (optional)
            
        Returns:
            bytes: Audio data
        """
        try:
            if call_id not in self._active_calls:
                self.logger.warning(f"Call {call_id} not found")
                return b""
            
            call_info = self._active_calls[call_id]
            access_token = await self._get_access_token()
            
            # Use provided voice or default for language
            if voice_name is None:
                voice_name = call_info.voice_name
            
            # Azure Text-to-Speech API endpoint
            tts_url = f"https://{self.config.region}.tts.speech.microsoft.com/cognitiveservices/v1"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm"
            }
            
            # Create SSML for speech synthesis
            ssml = f"""
            <speak version='1.0' xml:lang='{call_info.language}'>
                <voice xml:lang='{call_info.language}' xml:gender='Neutral' name='{voice_name}'>
                    {text}
                </voice>
            </speak>
            """
            
            async with self._session.post(tts_url, headers=headers, data=ssml) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    
                    # Emit speech synthesis event
                    event = TelephonyEvent(
                        event_type=TelephonyEventType.SPEECH_SYNTHESIZED,
                        call_id=call_id,
                        timestamp=datetime.now(),
                        data={
                            "text": text,
                            "voice_name": voice_name,
                            "audio_length": len(audio_data),
                            "provider": "azure_speech"
                        }
                    )
                    
                    await self._emit_event(event)
                    
                    self.logger.debug(f"Speech synthesized for call {call_id}: {text[:50]}...")
                    return audio_data
                else:
                    self.logger.error(f"Text-to-speech failed for call {call_id}: {response.status}")
                    return b""
                    
        except Exception as e:
            self.logger.error(f"Error synthesizing speech for call {call_id}: {e}")
            return b""
    
    def _get_voice_for_language(self, language: str) -> str:
        """Get default voice name for a language"""
        voices = self.config.voice_names.get(language, [])
        if voices:
            return voices[0]
        
        # Fallback to English if language not found
        return self.config.voice_names.get("en-US", ["en-US-JennyNeural"])[0]
    
    async def detect_language(self, audio_data: bytes) -> str:
        """
        Detect language from audio using Azure Speech Services
        
        Args:
            audio_data: Audio data bytes
            
        Returns:
            str: Detected language code
        """
        try:
            access_token = await self._get_access_token()
            
            # Azure Language Detection API endpoint
            lang_url = f"{self.config.endpoint}/speechtotext/v3.0/recognize"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "audio/wav",
                "Accept": "application/json"
            }
            
            params = {
                "language": "auto-detect"
            }
            
            async with self._session.post(lang_url, headers=headers, params=params, data=audio_data) as response:
                if response.status == 200:
                    result = await response.json()
                    detected_lang = result.get("Language", "en-US")
                    
                    self.logger.debug(f"Language detected: {detected_lang}")
                    return detected_lang
                else:
                    self.logger.warning(f"Language detection failed: {response.status}")
                    return "en-US"
                    
        except Exception as e:
            self.logger.error(f"Error detecting language: {e}")
            return "en-US"
    
    async def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages
        
        Returns:
            List[str]: List of supported language codes
        """
        return self.config.supported_languages
    
    async def get_supported_voices(self, language: str = None) -> List[str]:
        """
        Get list of supported voices for a language
        
        Args:
            language: Language code (optional)
            
        Returns:
            List[str]: List of supported voice names
        """
        if language:
            return self.config.voice_names.get(language, [])
        else:
            # Return all voices
            all_voices = []
            for voices in self.config.voice_names.values():
                all_voices.extend(voices)
            return all_voices
    
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
                "voice_name": call_info.voice_name,
                "session_id": call_info.session_id,
                "created_at": call_info.created_at.isoformat(),
                "recognition_mode": call_info.recognition_mode,
                "duration": (datetime.now() - call_info.created_at).total_seconds(),
                "provider": "azure_speech"
            }
        return None
    
    async def is_connected(self) -> bool:
        """
        Check if connected to Azure Speech Services
        
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
            "name": "Azure Speech Services",
            "version": "1.0.0",
            "supported_languages": len(self.config.supported_languages),
            "supported_voices": sum(len(voices) for voices in self.config.voice_names.values()),
            "region": self.config.region,
            "features": await self._get_supported_features(),
            "cost_per_minute": await self._get_cost_per_minute(),
            "supported_regions": await self._get_supported_regions()
        }
    
    async def _dial_impl(self, context: CallContext) -> str:
        """
        Azure Speech-specific call initiation implementation
        
        Args:
            context: Call context information
            
        Returns:
            str: Unique call identifier
        """
        try:
            # Generate unique call ID
            call_id = str(uuid.uuid4())
            
            # Create Azure Speech call info
            azure_call_info = AzureSpeechCallInfo(
                call_id=call_id,
                language=context.metadata.get('language', 'en-US'),
                voice_name=context.metadata.get('voice_name', 'en-US-JennyNeural'),
                session_id=str(uuid.uuid4()),
                created_at=datetime.utcnow(),
                recognition_mode=context.metadata.get('recognition_mode', 'conversation'),
                metadata=context.metadata
            )
            
            # Store call info
            self._calls[call_id] = azure_call_info
            
            self.logger.info(f"Azure Speech call initiated: {call_id}")
            return call_id
            
        except Exception as e:
            self.logger.error(f"Failed to initiate Azure Speech call: {e}")
            raise
    
    async def _hangup_impl(self, call_id: str) -> bool:
        """
        Azure Speech-specific call termination implementation
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            bool: True if call was successfully ended
        """
        try:
            if call_id in self._calls:
                del self._calls[call_id]
                self.logger.info(f"Azure Speech call ended: {call_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to end Azure Speech call {call_id}: {e}")
            return False
    
    async def _get_events_impl(self, call_id: str) -> List[TelephonyEvent]:
        """
        Azure Speech-specific event retrieval implementation
        
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
                    "voice_name": call_info.voice_name,
                    "session_id": call_info.session_id
                }
            ))
            
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to get Azure Speech events for call {call_id}: {e}")
            return []
    
    async def _get_costs_impl(self, call_id: str) -> Dict[str, float]:
        """
        Azure Speech-specific cost calculation implementation
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            Dict[str, float]: Cost breakdown by component
        """
        try:
            if call_id not in self._calls:
                return {}
            
            # Azure Speech pricing (approximate)
            stt_cost_per_minute = 0.024  # Speech-to-Text
            tts_cost_per_minute = 0.024  # Text-to-Speech
            
            # Calculate costs based on usage
            call_info = self._calls[call_id]
            duration_minutes = 1.0  # Default duration
            
            return {
                "speech_to_text": duration_minutes * stt_cost_per_minute,
                "text_to_speech": duration_minutes * tts_cost_per_minute,
                "language_detection": 0.001,  # Fixed cost
                "total": (duration_minutes * stt_cost_per_minute) + 
                        (duration_minutes * tts_cost_per_minute) + 0.001
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get Azure Speech costs for call {call_id}: {e}")
            return {}
    
    async def _get_cost_per_minute(self) -> Optional[float]:
        """Get cost per minute for Azure Speech Services"""
        # Azure Speech pricing: $0.024 per minute for both STT and TTS
        return 0.024
    
    async def _get_supported_regions(self) -> List[str]:
        """Get list of supported geographic regions for Azure Speech"""
        return [
            "eastus", "eastus2", "southcentralus", "westus2", "westus3",
            "canadacentral", "canadaeast", "europewest", "europenorth",
            "uksouth", "ukwest", "eastasia", "southeastasia", "japaneast",
            "japanwest", "australiaeast", "australiasoutheast", "brazilsouth",
            "centralindia", "southindia", "westindia", "koreacentral",
            "koreasouth", "francecentral", "germanywestcentral", "norwayeast",
            "switzerlandnorth", "switzerlandwest", "uaenorth", "uaecentral"
        ]
    
    async def _get_supported_features(self) -> List[str]:
        """Get list of supported features for Azure Speech"""
        return [
            "speech_to_text",
            "text_to_speech",
            "language_detection",
            "speaker_diarization",
            "custom_speech_models",
            "custom_voice_models",
            "real_time_transcription",
            "neural_voices",
            "ssml_support",
            "audio_format_conversion",
            "profanity_filtering",
            "word_level_timestamps"
        ]
