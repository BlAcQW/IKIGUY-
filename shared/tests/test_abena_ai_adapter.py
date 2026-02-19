"""
Tests for Abena AI Telephony Adapter

This module tests the Abena AI integration for Ghanaian language support
including Twi (Akan), Ghana Pidgin English, Ewe, Ga, and Dagbani.
"""

import pytest
import asyncio
import aiohttp
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

from apps.shared.telephony.adapters.abena_ai import (
    AbenaAITelephonyAdapter,
    AbenaAIConfig,
    AbenaAICallInfo
)
from apps.shared.telephony.models import ProviderSettings
from apps.shared.telephony.interfaces import TelephonyEventType


def create_mock_context_manager(mock_response):
    """Helper function to create a properly mocked async context manager"""
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_response)
    mock_context.__aexit__ = AsyncMock(return_value=None)
    return mock_context


class TestAbenaAIConfig:
    """Test cases for AbenaAIConfig"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = AbenaAIConfig(api_key="test_key")
        
        assert config.api_key == "test_key"
        assert config.base_url == "https://api.abena.mobobi.com"
        assert config.timeout == 30
        assert config.supported_languages == ["tw", "en-GH", "ee", "ga", "dag"]
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = AbenaAIConfig(
            api_key="custom_key",
            base_url="https://custom.api.com",
            timeout=60,
            supported_languages=["tw", "en-GH"]
        )
        
        assert config.api_key == "custom_key"
        assert config.base_url == "https://custom.api.com"
        assert config.timeout == 60
        assert config.supported_languages == ["tw", "en-GH"]


class TestAbenaAICallInfo:
    """Test cases for AbenaAICallInfo"""
    
    def test_call_info_creation(self):
        """Test AbenaAICallInfo creation"""
        call_info = AbenaAICallInfo(
            call_id="test_call_123",
            language="tw",
            voice_id="default",
            session_id="session_123",
            created_at=datetime.utcnow(),
            metadata={"test": "data"}
        )
        
        assert call_info.call_id == "test_call_123"
        assert call_info.language == "tw"
        assert call_info.voice_id == "default"
        assert call_info.session_id == "session_123"
        assert call_info.metadata == {"test": "data"}


class TestAbenaAITelephonyAdapter:
    """Test cases for AbenaAITelephonyAdapter"""
    
    @pytest.fixture
    def provider_settings(self):
        """Test provider settings"""
        return ProviderSettings(
            provider_id="abena_ai",
            api_key="test_api_key",
            base_url="https://api.abena.mobobi.com",
            custom_settings={
                "api_key": "test_api_key",
                "base_url": "https://api.abena.mobobi.com",
                "timeout": 30,
                "supported_languages": ["tw", "en-GH", "ee", "ga", "dag"]
            }
        )
    
    @pytest.fixture
    def adapter(self, provider_settings):
        """Test adapter instance"""
        return AbenaAITelephonyAdapter(provider_settings)
    
    def test_adapter_initialization(self, adapter):
        """Test adapter initialization"""
        assert adapter.config.api_key == "test_api_key"
        assert adapter.config.base_url == "https://api.abena.mobobi.com"
        assert adapter.config.timeout == 30
        assert adapter.config.supported_languages == ["tw", "en-GH", "ee", "ga", "dag"]
        assert adapter._connected is False
        assert adapter._session is None
        assert adapter._active_calls == {}
    
    def test_language_patterns(self, adapter):
        """Test language detection patterns"""
        assert "tw" in adapter._language_patterns
        assert "en-GH" in adapter._language_patterns
        assert "ee" in adapter._language_patterns
        assert "ga" in adapter._language_patterns
        assert "dag" in adapter._language_patterns
        
        # Test Twi patterns
        twi_patterns = adapter._language_patterns["tw"]
        assert "ɛ" in twi_patterns
        assert "ɔ" in twi_patterns
        assert "ɛyɛ" in twi_patterns
        
        # Test Ghana Pidgin patterns
        pidgin_patterns = adapter._language_patterns["en-GH"]
        assert "make you" in pidgin_patterns
        assert "dey" in pidgin_patterns
        assert "fit" in pidgin_patterns
    
    @pytest.mark.asyncio
    async def test_connect_success(self, adapter):
        """Test successful connection"""
        mock_response = MagicMock()
        mock_response.status = 200
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Properly mock the async context manager
            mock_session.get.return_value = create_mock_context_manager(mock_response)
            
            result = await adapter.connect()
            
            assert result is True
            assert adapter._connected is True
            assert adapter._session is not None
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, adapter):
        """Test connection failure"""
        mock_response = MagicMock()
        mock_response.status = 401
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Properly mock the async context manager
            mock_session.get.return_value = create_mock_context_manager(mock_response)
            
            result = await adapter.connect()
            
            assert result is False
            assert adapter._connected is False
    
    @pytest.mark.asyncio
    async def test_connect_exception(self, adapter):
        """Test connection with exception"""
        with patch('aiohttp.ClientSession', side_effect=Exception("Connection error")):
            result = await adapter.connect()
            
            assert result is False
            assert adapter._connected is False
    
    @pytest.mark.asyncio
    async def test_disconnect_success(self, adapter):
        """Test successful disconnection"""
        # First connect
        adapter._session = AsyncMock()
        adapter._connected = True
        
        result = await adapter.disconnect()
        
        assert result is True
        assert adapter._connected is False
        assert adapter._session is None
    
    @pytest.mark.asyncio
    async def test_disconnect_exception(self, adapter):
        """Test disconnection with exception"""
        adapter._session = AsyncMock()
        adapter._session.close.side_effect = Exception("Close error")
        adapter._connected = True
        
        result = await adapter.disconnect()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_dial_success(self, adapter):
        """Test successful call initiation"""
        # Setup connection
        adapter._connected = True
        adapter._session = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"call_id": "test_call"})
        
        adapter._session.post.return_value = create_mock_context_manager(mock_response)
        
        call_id = await adapter.dial("+233123456789", from_="+233987654321", language="tw")
        
        assert call_id.startswith("abena_")
        assert call_id in adapter._active_calls
        
        call_info = adapter._active_calls[call_id]
        assert call_info.language == "tw"
        assert call_info.voice_id == "default"
        assert call_info.metadata["destination"] == "+233123456789"
    
    @pytest.mark.asyncio
    async def test_dial_unsupported_language(self, adapter):
        """Test call initiation with unsupported language"""
        adapter._connected = True
        adapter._session = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"call_id": "test_call"})
        
        adapter._session.post.return_value = create_mock_context_manager(mock_response)
        
        call_id = await adapter.dial("+233123456789", from_="+233987654321", language="unsupported")
        
        # Should fallback to Twi
        call_info = adapter._active_calls[call_id]
        assert call_info.language == "tw"
    
    @pytest.mark.asyncio
    async def test_dial_not_connected(self, adapter):
        """Test call initiation when not connected"""
        with pytest.raises(RuntimeError, match="Not connected to Abena AI"):
            await adapter.dial("+233123456789", from_="+233987654321")
    
    @pytest.mark.asyncio
    async def test_dial_api_failure(self, adapter):
        """Test call initiation with API failure"""
        adapter._connected = True
        adapter._session = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.status = 500
        
        adapter._session.post.return_value = create_mock_context_manager(mock_response)
        
        with pytest.raises(RuntimeError, match="Failed to initiate call"):
            await adapter.dial("+233123456789", from_="+233987654321")
    
    @pytest.mark.asyncio
    async def test_hangup_success(self, adapter):
        """Test successful call termination"""
        # Setup call
        call_id = "test_call_123"
        call_info = AbenaAICallInfo(
            call_id=call_id,
            language="tw",
            voice_id="default",
            session_id="session_123",
            created_at=datetime.utcnow()
        )
        adapter._active_calls[call_id] = call_info
        adapter._session = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.status = 200
        
        adapter._session.post.return_value = create_mock_context_manager(mock_response)
        
        result = await adapter.hangup(call_id)
        
        assert result is True
        assert call_id not in adapter._active_calls
    
    @pytest.mark.asyncio
    async def test_hangup_call_not_found(self, adapter):
        """Test hangup with non-existent call"""
        result = await adapter.hangup("non_existent_call")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_events_success(self, adapter):
        """Test successful event retrieval"""
        # Setup call
        call_id = "test_call_123"
        call_info = AbenaAICallInfo(
            call_id=call_id,
            language="tw",
            voice_id="default",
            session_id="session_123",
            created_at=datetime.utcnow()
        )
        adapter._active_calls[call_id] = call_info
        adapter._session = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[
            {
                "type": "call_started",
                "timestamp": "2024-01-01T12:00:00",
                "data": {"status": "connected"},
                "metadata": {"duration": 0}
            }
        ])
        
        adapter._session.get.return_value = create_mock_context_manager(mock_response)
        
        events = await adapter.get_events(call_id)
        
        assert len(events) == 1
        assert events[0].event_type == TelephonyEventType.CALL_STARTED
        assert events[0].call_id == call_id
    
    @pytest.mark.asyncio
    async def test_get_events_call_not_found(self, adapter):
        """Test event retrieval for non-existent call"""
        events = await adapter.get_events("non_existent_call")
        
        assert events == []
    
    @pytest.mark.asyncio
    async def test_get_costs_success(self, adapter):
        """Test successful cost retrieval"""
        # Setup call
        call_id = "test_call_123"
        call_info = AbenaAICallInfo(
            call_id=call_id,
            language="tw",
            voice_id="default",
            session_id="session_123",
            created_at=datetime.utcnow()
        )
        adapter._active_calls[call_id] = call_info
        adapter._session = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "total_cost": 0.50,
            "asr_cost": 0.20,
            "tts_cost": 0.25,
            "translation_cost": 0.05
        })
        
        adapter._session.get.return_value = create_mock_context_manager(mock_response)
        
        costs = await adapter.get_costs(call_id)
        
        assert costs["total_cost"] == 0.50
        assert costs["asr_cost"] == 0.20
        assert costs["tts_cost"] == 0.25
        assert costs["translation_cost"] == 0.05
    
    @pytest.mark.asyncio
    async def test_process_speech_success(self, adapter):
        """Test successful speech processing"""
        # Setup call
        call_id = "test_call_123"
        call_info = AbenaAICallInfo(
            call_id=call_id,
            language="tw",
            voice_id="default",
            session_id="session_123",
            created_at=datetime.utcnow()
        )
        adapter._active_calls[call_id] = call_info
        adapter._session = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "text": "ɛyɛ adeɛ",
            "confidence": 0.95,
            "detected_language": "tw",
            "is_final": True
        })
        
        adapter._session.post.return_value = create_mock_context_manager(mock_response)
        
        result = await adapter.process_speech(b"audio_data", call_id)
        
        assert result["text"] == "ɛyɛ adeɛ"
        assert result["confidence"] == 0.95
        assert result["language"] == "tw"
        assert result["is_final"] is True
    
    @pytest.mark.asyncio
    async def test_process_speech_call_not_found(self, adapter):
        """Test speech processing for non-existent call"""
        with pytest.raises(ValueError, match="Call non_existent_call not found"):
            await adapter.process_speech(b"audio_data", "non_existent_call")
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_success(self, adapter):
        """Test successful speech synthesis"""
        # Setup call
        call_id = "test_call_123"
        call_info = AbenaAICallInfo(
            call_id=call_id,
            language="tw",
            voice_id="default",
            session_id="session_123",
            created_at=datetime.utcnow()
        )
        adapter._active_calls[call_id] = call_info
        adapter._session = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"audio_data")
        
        adapter._session.post.return_value = create_mock_context_manager(mock_response)
        
        result = await adapter.synthesize_speech("ɛyɛ adeɛ", call_id)
        
        assert result == b"audio_data"
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_call_not_found(self, adapter):
        """Test speech synthesis for non-existent call"""
        with pytest.raises(ValueError, match="Call non_existent_call not found"):
            await adapter.synthesize_speech("text", "non_existent_call")
    
    @pytest.mark.asyncio
    async def test_translate_text_success(self, adapter):
        """Test successful text translation"""
        adapter._session = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "translated_text": "It is good"
        })
        
        adapter._session.post.return_value = create_mock_context_manager(mock_response)
        
        result = await adapter.translate_text("ɛyɛ adeɛ", "tw", "en")
        
        assert result == "It is good"
    
    @pytest.mark.asyncio
    async def test_translate_text_failure(self, adapter):
        """Test text translation failure"""
        adapter._session = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.status = 500
        
        adapter._session.post.return_value = create_mock_context_manager(mock_response)
        
        result = await adapter.translate_text("ɛyɛ adeɛ", "tw", "en")
        
        # Should return original text on failure
        assert result == "ɛyɛ adeɛ"
    
    def test_detect_language_twi(self, adapter):
        """Test Twi language detection"""
        text = "ɛyɛ adeɛ me wo kɔ baa"
        detected = adapter.detect_language(text)
        
        assert detected == "tw"
    
    def test_detect_language_pidgin(self, adapter):
        """Test Ghana Pidgin language detection"""
        text = "make you dey fit chop"
        detected = adapter.detect_language(text)
        
        assert detected == "en-GH"
    
    def test_detect_language_ewe(self, adapter):
        """Test Ewe language detection"""
        text = "wo me nye le nyuie"
        detected = adapter.detect_language(text)
        
        assert detected == "ee"
    
    def test_detect_language_ga(self, adapter):
        """Test Ga language detection"""
        text = "mi wo ye le ŋɔ"
        detected = adapter.detect_language(text)
        
        assert detected == "ga"
    
    def test_detect_language_dagbani(self, adapter):
        """Test Dagbani language detection"""
        text = "a ka ya la ŋɔ"
        detected = adapter.detect_language(text)
        
        assert detected == "dag"
    
    def test_detect_language_fallback(self, adapter):
        """Test language detection fallback"""
        text = "This is English text with no Ghanaian patterns"
        detected = adapter.detect_language(text)
        
        assert detected == "tw"  # Default fallback
    
    @pytest.mark.asyncio
    async def test_get_supported_features(self, adapter):
        """Test supported features list"""
        features = await adapter._get_supported_features()
        
        expected_features = [
            "ghanaian_languages",
            "asr",
            "tts",
            "translation",
            "language_detection",
            "voice_cloning",
            "offline_processing"
        ]
        
        assert features == expected_features
    
    def test_get_supported_languages(self, adapter):
        """Test supported languages list"""
        languages = adapter.get_supported_languages()
        
        expected_languages = ["tw", "en-GH", "ee", "ga", "dag"]
        
        assert languages == expected_languages
    
    def test_parse_events(self, adapter):
        """Test event parsing"""
        events_data = [
            {
                "type": "call_started",
                "timestamp": "2024-01-01T12:00:00",
                "data": {"status": "connected"},
                "metadata": {"duration": 0}
            },
            {
                "type": "speech_detected",
                "timestamp": "2024-01-01T12:00:01",
                "data": {"confidence": 0.8},
                "metadata": {"language": "tw"}
            },
            {
                "type": "transcription",
                "timestamp": "2024-01-01T12:00:02",
                "data": {"text": "ɛyɛ adeɛ"},
                "metadata": {"confidence": 0.95}
            }
        ]
        
        events = adapter._parse_events(events_data, "test_call_123")
        
        assert len(events) == 3
        assert events[0].event_type == TelephonyEventType.CALL_STARTED
        assert events[1].event_type == TelephonyEventType.SPEECH_DETECTED
        assert events[2].event_type == TelephonyEventType.TRANSCRIPTION
        assert all(event.call_id == "test_call_123" for event in events)
    
    def test_parse_events_unknown_type(self, adapter):
        """Test parsing events with unknown type"""
        events_data = [
            {
                "type": "unknown_event",
                "timestamp": "2024-01-01T12:00:00",
                "data": {},
                "metadata": {}
            }
        ]
        
        events = adapter._parse_events(events_data, "test_call_123")
        
        assert len(events) == 1
        assert events[0].event_type == TelephonyEventType.UNKNOWN_EVENT
