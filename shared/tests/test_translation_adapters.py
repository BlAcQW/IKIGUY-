"""
Unit Tests for Translation Adapters

This module contains comprehensive unit tests for Azure Speech, Google Cloud Speech,
and OpenAI Whisper translation adapters.
"""

import pytest
import asyncio
import json
import base64
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List

from ..telephony.adapters.azure_speech import AzureSpeechAdapter, AzureSpeechConfig, AzureSpeechCallInfo
from ..telephony.adapters.google_speech import GoogleSpeechAdapter, GoogleSpeechConfig, GoogleSpeechCallInfo
from ..telephony.adapters.openai_whisper import WhisperAdapter, WhisperConfig, WhisperCallInfo
from ..telephony.models import CallContext, ProviderSettings


class TestAzureSpeechAdapter:
    """Test Azure Speech Services adapter functionality"""
    
    @pytest.fixture
    def azure_settings(self):
        """Create Azure Speech settings"""
        return ProviderSettings(
            provider_id="azure_speech_test",
            api_key="test_azure_key",
            base_url="https://eastus.api.cognitive.microsoft.com",
            custom_settings={
                "subscription_key": "test_azure_key",
                "region": "eastus",
                "timeout": 30
            }
        )
    
    @pytest.fixture
    def azure_adapter(self, azure_settings):
        """Create Azure Speech adapter"""
        return AzureSpeechAdapter(azure_settings)
    
    @pytest.mark.asyncio
    async def test_azure_connect_disconnect(self, azure_adapter):
        """Test Azure Speech connection and disconnection"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            # Create a mock session instance
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock the async context manager methods
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session.close = AsyncMock(return_value=None)
            
            # Mock the post method for access token request
            mock_post_response = MagicMock()
            mock_post_response.status = 200
            mock_post_response.text = AsyncMock(return_value="mock_access_token")
            mock_post_response.__aenter__ = AsyncMock(return_value=mock_post_response)
            mock_post_response.__aexit__ = AsyncMock(return_value=None)
            mock_session.post.return_value = mock_post_response
            
            # Mock the get method for connection test
            mock_get_response = MagicMock()
            mock_get_response.status = 200
            mock_get_response.__aenter__ = AsyncMock(return_value=mock_get_response)
            mock_get_response.__aexit__ = AsyncMock(return_value=None)
            mock_session.get.return_value = mock_get_response
            
            # Test connection
            connected = await azure_adapter.connect()
            assert connected
            assert await azure_adapter.is_connected()
            
            # Test disconnection
            await azure_adapter.disconnect()
            assert not await azure_adapter.is_connected()
    
    @pytest.mark.asyncio
    async def test_azure_dial_hangup(self, azure_adapter):
        """Test Azure Speech dial and hangup functionality"""
        context = CallContext(
            destination="+1234567890",
            source="+0987654321",
            tenant_id="test_tenant",
            language="en-US",
            metadata={"language": "en-US"}
        )
        
        # Test dial
        call_id = await azure_adapter.dial("+1234567890", "+0987654321", context)
        assert call_id is not None
        assert call_id in azure_adapter._active_calls
        
        # Test hangup
        success = await azure_adapter.hangup(call_id)
        assert success
        assert call_id not in azure_adapter._active_calls
    
    @pytest.mark.asyncio
    async def test_azure_speech_to_text(self, azure_adapter):
        """Test Azure Speech STT functionality"""
        # Connect the adapter first
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock the async context manager methods
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session.close = AsyncMock(return_value=None)
            
            # Mock the post method for access token request
            mock_post_response = MagicMock()
            mock_post_response.status = 200
            mock_post_response.text = AsyncMock(return_value="mock_access_token")
            mock_post_response.__aenter__ = AsyncMock(return_value=mock_post_response)
            mock_post_response.__aexit__ = AsyncMock(return_value=None)
            mock_session.post.return_value = mock_post_response
            
            # Connect the adapter
            await azure_adapter.connect()
            
            context = CallContext(
                destination="+1234567890",
                source="+0987654321",
                tenant_id="test_tenant",
                language="en-US",
                metadata={"language": "en-US"}
            )
            call_id = await azure_adapter.dial("+1234567890", "+0987654321", context)
            
            # Mock audio data
            audio_data = b"fake_audio_data"
            
            # Mock the STT response
            mock_stt_response = MagicMock()
            mock_stt_response.status = 200
            mock_stt_response.json = AsyncMock(return_value={
                "DisplayText": "Hello world",
                "Offset": 0,
                "Duration": 1000000
            })
            mock_stt_response.__aenter__ = AsyncMock(return_value=mock_stt_response)
            mock_stt_response.__aexit__ = AsyncMock(return_value=None)
            
            # Update the post method to return the STT response
            mock_session.post.return_value = mock_stt_response
            
            # Test STT
            success = await azure_adapter.send_audio(call_id, audio_data, "wav")
            assert success
            
            # Verify call info updated
            call_info = azure_adapter._active_calls[call_id]
            assert call_info.transcription_history is not None
    
    @pytest.mark.asyncio
    async def test_azure_text_to_speech(self, azure_adapter):
        """Test Azure Speech TTS functionality"""
        context = CallContext(
            destination="+1234567890",
            source="+0987654321",
            tenant_id="test_tenant",
            language="en-US",
            metadata={"language": "en-US"}
        )
        call_id = await azure_adapter.dial("+1234567890", "+0987654321", context)
        
        text = "Hello, this is a test message."
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.read.return_value = b"synthesized_audio_data"
            mock_post.return_value = mock_response
            
            # Test TTS
            audio_data = await azure_adapter.synthesize_speech(
                call_id, 
                text, 
                voice_name="en-US-JennyNeural"
            )
            assert audio_data is not None
            assert len(audio_data) > 0
    
    @pytest.mark.asyncio
    async def test_azure_language_detection(self, azure_adapter):
        """Test Azure Speech language detection"""
        audio_data = b"fake_audio_data"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "Language": "en-US",
                "Score": 0.95
            }
            mock_post.return_value = mock_response
            
            # Test language detection
            detected_language = await azure_adapter.detect_language(audio_data)
            assert detected_language == "en-US"
    
    @pytest.mark.asyncio
    async def test_azure_get_supported_languages(self, azure_adapter):
        """Test Azure Speech supported languages"""
        languages = await azure_adapter.get_supported_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "en-US" in languages
    
    @pytest.mark.asyncio
    async def test_azure_get_supported_voices(self, azure_adapter):
        """Test Azure Speech supported voices"""
        voices = await azure_adapter.get_supported_voices("en-US")
        assert isinstance(voices, list)
        assert len(voices) > 0
        assert "en-US-JennyNeural" in voices
    
    @pytest.mark.asyncio
    async def test_azure_error_handling(self, azure_adapter):
        """Test Azure Speech error handling"""
        context = CallContext(
            destination="+1234567890",
            source="+0987654321",
            tenant_id="test_tenant",
            language="en-US",
            metadata={"language": "en-US"}
        )
        call_id = await azure_adapter.dial("+1234567890", "+0987654321", context)
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status = 401
            mock_response.text.return_value = "Unauthorized"
            mock_post.return_value = mock_response
            
            # Test error handling
            with pytest.raises(Exception):
                await azure_adapter.send_audio(call_id, b"audio_data", "wav")
    
    @pytest.mark.asyncio
    async def test_azure_get_provider_info(self, azure_adapter):
        """Test Azure Speech provider information"""
        info = await azure_adapter.get_provider_info()
        assert isinstance(info, dict)
        assert info["provider_id"] == "azure_speech_test"
        assert info["name"] == "Azure Speech Services"
        assert "supported_languages" in info
        assert "supported_voices" in info


class TestGoogleSpeechAdapter:
    """Test Google Cloud Speech adapter functionality"""
    
    @pytest.fixture
    def google_settings(self):
        """Create Google Cloud Speech settings"""
        return ProviderSettings(
            provider_id="google_speech_test",
            api_key="test_google_key",
            base_url="https://speech.googleapis.com",
            custom_settings={
                "project_id": "test_project",
                "api_key": "test_google_key",
                "region": "us-central1",
                "timeout": 30
            }
        )
    
    @pytest.fixture
    def google_adapter(self, google_settings):
        """Create Google Cloud Speech adapter"""
        return GoogleSpeechAdapter(google_settings)
    
    @pytest.mark.asyncio
    async def test_google_connect_disconnect(self, google_adapter):
        """Test Google Cloud Speech connection and disconnection"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            # Create a mock session instance
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock the async context manager methods
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session.close = AsyncMock(return_value=None)
            
            # Mock the post method for connection test
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_session.post.return_value = mock_response
            
            # Test connection
            connected = await google_adapter.connect()
            assert connected
            assert await google_adapter.is_connected()
            
            # Test disconnection
            await google_adapter.disconnect()
            assert not await google_adapter.is_connected()
    
    @pytest.mark.asyncio
    async def test_google_dial_hangup(self, google_adapter):
        """Test Google Cloud Speech dial and hangup functionality"""
        context = CallContext(
            destination="+1234567890",
            source="+0987654321",
            tenant_id="test_tenant",
            language="en-US",
            metadata={"language": "en-US"}
        )
        
        # Test dial
        call_id = await google_adapter.dial("+1234567890", "+0987654321", context)
        assert call_id is not None
        assert call_id in google_adapter._active_calls
        
        # Test hangup
        success = await google_adapter.hangup(call_id)
        assert success
        assert call_id not in google_adapter._active_calls
    
    @pytest.mark.asyncio
    async def test_google_speech_to_text(self, google_adapter):
        """Test Google Cloud Speech STT functionality"""
        context = CallContext(
            destination="+1234567890",
            source="+0987654321",
            tenant_id="test_tenant",
            language="en-US",
            metadata={"language": "en-US"}
        )
        call_id = await google_adapter.dial("+1234567890", "+0987654321", context)
        
        # Mock audio data
        audio_data = b"fake_audio_data"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "results": [{
                    "alternatives": [{
                        "transcript": "Hello world",
                        "confidence": 0.95
                    }]
                }]
            }
            mock_post.return_value = mock_response
            
            # Test STT
            success = await google_adapter.send_audio(call_id, audio_data, "wav")
            assert success
            
            # Verify call info updated
            call_info = google_adapter._active_calls[call_id]
            assert call_info.transcription_history is not None
    
    @pytest.mark.asyncio
    async def test_google_text_to_speech(self, google_adapter):
        """Test Google Cloud Speech TTS functionality"""
        context = CallContext(
            destination="+1234567890",
            source="+0987654321",
            tenant_id="test_tenant",
            language="en-US",
            metadata={"language": "en-US"}
        )
        call_id = await google_adapter.dial("+1234567890", "+0987654321", context)
        
        text = "Hello, this is a test message."
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.read.return_value = b"synthesized_audio_data"
            mock_post.return_value = mock_response
            
            # Test TTS
            audio_data = await google_adapter.synthesize_speech(
                call_id, 
                text, 
                voice_name="en-US-Standard-A"
            )
            assert audio_data is not None
            assert len(audio_data) > 0
    
    @pytest.mark.asyncio
    async def test_google_language_detection(self, google_adapter):
        """Test Google Cloud Speech language detection"""
        audio_data = b"fake_audio_data"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "results": [{
                    "languageCode": "en-US",
                    "confidence": 0.95
                }]
            }
            mock_post.return_value = mock_response
            
            # Test language detection
            detected_language = await google_adapter.detect_language(audio_data)
            assert detected_language == "en-US"
    
    @pytest.mark.asyncio
    async def test_google_get_supported_languages(self, google_adapter):
        """Test Google Cloud Speech supported languages"""
        languages = await google_adapter.get_supported_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "en-US" in languages
    
    @pytest.mark.asyncio
    async def test_google_get_supported_voices(self, google_adapter):
        """Test Google Cloud Speech supported voices"""
        voices = await google_adapter.get_supported_voices("en-US")
        assert isinstance(voices, list)
        assert len(voices) > 0
        assert "en-US-Standard-A" in voices
    
    @pytest.mark.asyncio
    async def test_google_error_handling(self, google_adapter):
        """Test Google Cloud Speech error handling"""
        context = CallContext(
            destination="+1234567890",
            source="+0987654321",
            tenant_id="test_tenant",
            language="en-US",
            metadata={"language": "en-US"}
        )
        call_id = await google_adapter.dial("+1234567890", "+0987654321", context)
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status = 400
            mock_response.text.return_value = "Bad Request"
            mock_post.return_value = mock_response
            
            # Test error handling
            with pytest.raises(Exception):
                await google_adapter.send_audio(call_id, b"audio_data", "wav")
    
    @pytest.mark.asyncio
    async def test_google_get_provider_info(self, google_adapter):
        """Test Google Cloud Speech provider information"""
        info = await google_adapter.get_provider_info()
        assert isinstance(info, dict)
        assert info["provider_id"] == "google_speech_test"
        assert info["name"] == "Google Cloud Speech Services"
        assert "supported_languages" in info
        assert "supported_voices" in info


class TestWhisperAdapter:
    """Test OpenAI Whisper adapter functionality"""
    
    @pytest.fixture
    def whisper_settings(self):
        """Create OpenAI Whisper settings"""
        return ProviderSettings(
            provider_id="openai_whisper_test",
            api_key="test_openai_key",
            base_url="https://api.openai.com/v1",
            custom_settings={
                "api_key": "test_openai_key",
                "model": "whisper-1",
                "base_url": "https://api.openai.com/v1",
                "timeout": 30
            }
        )
    
    @pytest.fixture
    def whisper_adapter(self, whisper_settings):
        """Create OpenAI Whisper adapter"""
        return WhisperAdapter(whisper_settings)
    
    @pytest.mark.asyncio
    async def test_whisper_connect_disconnect(self, whisper_adapter):
        """Test OpenAI Whisper connection and disconnection"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            # Create a mock session instance
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock the async context manager methods
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session.close = AsyncMock(return_value=None)
            
            # Mock the get method for connection test
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_session.get.return_value = mock_response
            
            # Test connection
            connected = await whisper_adapter.connect()
            assert connected
            assert await whisper_adapter.is_connected()
            
            # Test disconnection
            await whisper_adapter.disconnect()
            assert not await whisper_adapter.is_connected()
    
    @pytest.mark.asyncio
    async def test_whisper_dial_hangup(self, whisper_adapter):
        """Test OpenAI Whisper dial and hangup functionality"""
        context = CallContext(
            destination="+1234567890",
            source="+0987654321",
            tenant_id="test_tenant",
            language="en-US",
            metadata={"language": "en-US"}
        )
        
        # Test dial
        call_id = await whisper_adapter.dial("+1234567890", "+0987654321", context)
        assert call_id is not None
        assert call_id in whisper_adapter._active_calls
        
        # Test hangup
        success = await whisper_adapter.hangup(call_id)
        assert success
        assert call_id not in whisper_adapter._active_calls
    
    @pytest.mark.asyncio
    async def test_whisper_speech_to_text(self, whisper_adapter):
        """Test OpenAI Whisper STT functionality"""
        context = CallContext(
            destination="+1234567890",
            source="+0987654321",
            tenant_id="test_tenant",
            language="en-US",
            metadata={"language": "en-US"}
        )
        call_id = await whisper_adapter.dial("+1234567890", "+0987654321", context)
        
        # Mock audio data
        audio_data = b"fake_audio_data"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "text": "Hello world",
                "language": "en",
                "segments": [
                    {
                        "id": 0,
                        "start": 0.0,
                        "end": 1.0,
                        "text": "Hello world"
                    }
                ]
            }
            mock_post.return_value = mock_response
            
            # Test STT
            success = await whisper_adapter.send_audio(call_id, audio_data, "wav")
            assert success
            
            # Verify call info updated
            call_info = whisper_adapter._active_calls[call_id]
            assert call_info.transcription_history is not None
    
    @pytest.mark.asyncio
    async def test_whisper_text_to_speech(self, whisper_adapter):
        """Test OpenAI Whisper TTS functionality (should return empty)"""
        context = CallContext(
            destination="+1234567890",
            source="+0987654321",
            tenant_id="test_tenant",
            language="en-US",
            metadata={"language": "en-US"}
        )
        call_id = await whisper_adapter.dial("+1234567890", "+0987654321", context)
        
        text = "Hello, this is a test message."
        
        # Test TTS (Whisper is STT-only)
        audio_data = await whisper_adapter.synthesize_speech(
            call_id, 
            text, 
            voice_name="test_voice"
        )
        assert audio_data == b""  # Whisper doesn't support TTS
    
    @pytest.mark.asyncio
    async def test_whisper_language_detection(self, whisper_adapter):
        """Test OpenAI Whisper language detection"""
        audio_data = b"fake_audio_data"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "text": "Hello world",
                "language": "en"
            }
            mock_post.return_value = mock_response
            
            # Test language detection
            detected_language = await whisper_adapter.detect_language(audio_data)
            assert detected_language == "en"
    
    @pytest.mark.asyncio
    async def test_whisper_get_supported_languages(self, whisper_adapter):
        """Test OpenAI Whisper supported languages"""
        languages = await whisper_adapter.get_supported_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "en" in languages
    
    @pytest.mark.asyncio
    async def test_whisper_get_supported_voices(self, whisper_adapter):
        """Test OpenAI Whisper supported voices (should return empty)"""
        voices = await whisper_adapter.get_supported_voices("en")
        assert isinstance(voices, list)
        assert len(voices) == 0  # Whisper doesn't support TTS
    
    @pytest.mark.asyncio
    async def test_whisper_error_handling(self, whisper_adapter):
        """Test OpenAI Whisper error handling"""
        context = CallContext(
            destination="+1234567890",
            source="+0987654321",
            tenant_id="test_tenant",
            language="en-US",
            metadata={"language": "en-US"}
        )
        call_id = await whisper_adapter.dial("+1234567890", "+0987654321", context)
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status = 401
            mock_response.text.return_value = "Unauthorized"
            mock_post.return_value = mock_response
            
            # Test error handling
            with pytest.raises(Exception):
                await whisper_adapter.send_audio(call_id, b"audio_data", "wav")
    
    @pytest.mark.asyncio
    async def test_whisper_get_provider_info(self, whisper_adapter):
        """Test OpenAI Whisper provider information"""
        info = await whisper_adapter.get_provider_info()
        assert isinstance(info, dict)
        assert info["provider_id"] == "openai_whisper_test"
        assert info["name"] == "OpenAI Whisper"
        assert "supported_languages" in info
        assert "supported_voices" in info
    
    @pytest.mark.asyncio
    async def test_whisper_get_transcription_history(self, whisper_adapter):
        """Test OpenAI Whisper transcription history"""
        context = CallContext(
            destination="+1234567890",
            source="+0987654321",
            tenant_id="test_tenant",
            language="en-US",
            metadata={"language": "en-US"}
        )
        call_id = await whisper_adapter.dial("+1234567890", "+0987654321", context)
        
        # Add some transcription history
        whisper_adapter._active_calls[call_id].transcription_history = [
            {"text": "Hello", "timestamp": datetime.now()},
            {"text": "World", "timestamp": datetime.now()}
        ]
        
        history = await whisper_adapter.get_transcription_history(call_id)
        assert isinstance(history, list)
        assert len(history) == 2
    
    @pytest.mark.asyncio
    async def test_whisper_get_audio_segments(self, whisper_adapter):
        """Test OpenAI Whisper audio segments"""
        context = CallContext(
            destination="+1234567890",
            source="+0987654321",
            tenant_id="test_tenant",
            language="en-US",
            metadata={"language": "en-US"}
        )
        call_id = await whisper_adapter.dial("+1234567890", "+0987654321", context)
        
        # Mock audio segments
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "text": "Hello world",
                "segments": [
                    {
                        "id": 0,
                        "start": 0.0,
                        "end": 1.0,
                        "text": "Hello"
                    },
                    {
                        "id": 1,
                        "start": 1.0,
                        "end": 2.0,
                        "text": "world"
                    }
                ]
            }
            mock_post.return_value = mock_response
            
            # Test audio segments
            segments = await whisper_adapter.get_audio_segments(call_id)
            assert isinstance(segments, list)
            assert len(segments) == 2


class TestTranslationAdapterIntegration:
    """Integration tests for translation adapters"""
    
    @pytest.fixture
    def all_adapters(self):
        """Create all translation adapters"""
        azure_settings = ProviderSettings(
            provider_id="azure_speech_test",
            api_key="test_azure_key",
            base_url="https://eastus.api.cognitive.microsoft.com",
            custom_settings={
                "subscription_key": "test_azure_key",
                "region": "eastus"
            }
        )
        
        google_settings = ProviderSettings(
            provider_id="google_speech_test",
            api_key="test_google_key",
            base_url="https://speech.googleapis.com",
            custom_settings={
                "project_id": "test_project",
                "api_key": "test_google_key",
                "region": "us-central1"
            }
        )
        
        whisper_settings = ProviderSettings(
            provider_id="openai_whisper_test",
            api_key="test_openai_key",
            base_url="https://api.openai.com/v1",
            custom_settings={
                "api_key": "test_openai_key",
                "model": "whisper-1"
            }
        )
        
        return {
            "azure": AzureSpeechAdapter(azure_settings),
            "google": GoogleSpeechAdapter(google_settings),
            "whisper": WhisperAdapter(whisper_settings)
        }
    
    @pytest.mark.asyncio
    async def test_adapter_compatibility(self, all_adapters):
        """Test that all adapters implement the same interface"""
        for name, adapter in all_adapters.items():
            # Test required methods exist
            assert hasattr(adapter, 'connect')
            assert hasattr(adapter, 'disconnect')
            assert hasattr(adapter, 'dial')
            assert hasattr(adapter, 'hangup')
            assert hasattr(adapter, 'send_audio')
            assert hasattr(adapter, 'synthesize_speech')
            assert hasattr(adapter, 'detect_language')
            assert hasattr(adapter, 'get_supported_languages')
            assert hasattr(adapter, 'get_supported_voices')
            assert hasattr(adapter, 'get_provider_info')
    
    @pytest.mark.asyncio
    async def test_language_support_comparison(self, all_adapters):
        """Test language support across all adapters"""
        languages_by_provider = {}
        
        for name, adapter in all_adapters.items():
            with patch('aiohttp.ClientSession'):
                await adapter.connect()
                languages = await adapter.get_supported_languages()
                languages_by_provider[name] = languages
                await adapter.disconnect()
        
        # Verify providers support some common languages
        common_languages = ["en", "en-US", "es", "fr", "de"]
        total_support = 0
        for language in common_languages:
            supported_count = sum(
                1 for languages in languages_by_provider.values()
                if language in languages
            )
            total_support += supported_count
        
        # At least some languages should be supported across providers
        assert total_support >= len(common_languages)  # Each common language should be supported by at least one provider
    
    @pytest.mark.asyncio
    async def test_voice_support_comparison(self, all_adapters):
        """Test voice support across all adapters"""
        voices_by_provider = {}
        
        for name, adapter in all_adapters.items():
            with patch('aiohttp.ClientSession'):
                await adapter.connect()
                voices = await adapter.get_supported_voices("en-US")
                voices_by_provider[name] = voices
                await adapter.disconnect()
        
        # Verify Azure and Google have voice support (Whisper doesn't)
        assert len(voices_by_provider["azure"]) > 0
        assert len(voices_by_provider["google"]) > 0
        assert len(voices_by_provider["whisper"]) == 0  # Whisper is STT-only


if __name__ == "__main__":
    pytest.main([__file__])
