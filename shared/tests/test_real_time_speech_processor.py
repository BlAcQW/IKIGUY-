"""
Tests for Real-time Speech Processor

This module contains comprehensive tests for the real-time speech processor implementation.
"""

import pytest
import asyncio
import numpy as np
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from apps.shared.speech.real_time_processor import (
    RealTimeSpeechProcessor,
    SpeechEventType,
    EmotionType,
    SentimentType,
    SpeechEvent,
    VoiceActivityResult,
    EmotionResult,
    SentimentResult,
    ASRResult,
    TTSRequest,
    TTSResult
)


class TestRealTimeSpeechProcessor:
    """Test cases for real-time speech processor"""
    
    @pytest.fixture
    def config(self) -> Dict[str, Any]:
        """Create configuration for testing"""
        return {
            'vad_threshold': 0.5,
            'vad_frame_duration': 30,
            'silence_threshold': 0.3,
            'min_speech_duration': 100,
            'barge_in_threshold': 0.7,
            'sample_rate': 16000,
            'chunk_size': 1024
        }
    
    @pytest.fixture
    def speech_processor(self, config) -> RealTimeSpeechProcessor:
        """Create speech processor instance for testing"""
        return RealTimeSpeechProcessor(config)
    
    @pytest.fixture
    def call_id(self) -> str:
        """Create call ID for testing"""
        return "test_call_123"
    
    @pytest.fixture
    def audio_chunk(self) -> bytes:
        """Create test audio chunk"""
        # Generate test audio data (sine wave)
        sample_rate = 16000
        duration = 0.1  # 100ms
        frequency = 440  # A4 note
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio = np.sin(2 * np.pi * frequency * t) * 0.5
        return (audio * 32767).astype(np.int16).tobytes()
    
    @pytest.mark.asyncio
    async def test_speech_processor_initialization(self, speech_processor):
        """Test speech processor initialization"""
        assert speech_processor.vad_threshold == 0.5
        assert speech_processor.sample_rate == 16000
        assert speech_processor.chunk_size == 1024
        assert speech_processor.active_calls == {}
        assert speech_processor.event_callbacks == {}
    
    @pytest.mark.asyncio
    async def test_start_call_processing(self, speech_processor, call_id):
        """Test starting call processing"""
        success = await speech_processor.start_call_processing(call_id)
        
        assert success is True
        assert call_id in speech_processor.active_calls
        
        call_state = speech_processor.active_calls[call_id]
        assert 'vad_state' in call_state
        assert 'asr_state' in call_state
        assert 'tts_state' in call_state
        assert 'emotion_state' in call_state
        assert 'sentiment_state' in call_state
        assert 'barge_in_state' in call_state
        assert 'start_time' in call_state
    
    @pytest.mark.asyncio
    async def test_stop_call_processing(self, speech_processor, call_id):
        """Test stopping call processing"""
        # Start processing first
        await speech_processor.start_call_processing(call_id)
        
        # Stop processing
        success = await speech_processor.stop_call_processing(call_id)
        
        assert success is True
        assert call_id not in speech_processor.active_calls
    
    @pytest.mark.asyncio
    async def test_stop_call_processing_not_found(self, speech_processor, call_id):
        """Test stopping call processing for non-existent call"""
        success = await speech_processor.stop_call_processing(call_id)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_process_audio_chunk_no_call(self, speech_processor, audio_chunk):
        """Test processing audio chunk for non-existent call"""
        events = await speech_processor.process_audio_chunk("non_existent_call", audio_chunk)
        assert events == []
    
    @pytest.mark.asyncio
    async def test_detect_voice_activity(self, speech_processor, call_id):
        """Test voice activity detection"""
        # Start call processing
        await speech_processor.start_call_processing(call_id)
        call_state = speech_processor.active_calls[call_id]
        
        # Create test audio with speech
        speech_audio = np.random.normal(0, 0.8, 1024).astype(np.float32)
        
        # Test speech detection
        result = await speech_processor._detect_voice_activity(speech_audio, call_state)
        
        assert result is not None
        assert isinstance(result, VoiceActivityResult)
        assert result.is_speech is True
        assert result.confidence > 0.0
        assert result.energy_level > 0.0
        assert result.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_detect_voice_activity_silence(self, speech_processor, call_id):
        """Test voice activity detection for silence"""
        # Start call processing
        await speech_processor.start_call_processing(call_id)
        call_state = speech_processor.active_calls[call_id]
        
        # Create test audio with silence
        silence_audio = np.random.normal(0, 0.1, 1024).astype(np.float32)
        
        # Test silence detection
        result = await speech_processor._detect_voice_activity(silence_audio, call_state)
        
        assert result is not None
        assert isinstance(result, VoiceActivityResult)
        assert result.is_speech is False
        assert result.confidence > 0.0
        assert result.energy_level > 0.0
    
    @pytest.mark.asyncio
    async def test_process_vad_result_speech_start(self, speech_processor, call_id):
        """Test processing VAD result for speech start"""
        # Start call processing
        await speech_processor.start_call_processing(call_id)
        call_state = speech_processor.active_calls[call_id]
        
        # Create VAD result for speech start
        vad_result = VoiceActivityResult(
            is_speech=True,
            confidence=0.8,
            energy_level=0.6,
            duration_ms=100.0,
            timestamp=datetime.utcnow()
        )
        
        # Process VAD result
        events = await speech_processor._process_vad_result(call_id, vad_result, call_state)
        
        assert len(events) == 1
        event = events[0]
        assert event.event_type == SpeechEventType.SPEECH_START
        assert event.call_id == call_id
        assert event.confidence == 0.8
        assert event.data['energy_level'] == 0.6
        
        # Check state update
        assert call_state['vad_state']['is_speaking'] is True
        assert call_state['vad_state']['speech_start_time'] == vad_result.timestamp
    
    @pytest.mark.asyncio
    async def test_process_vad_result_speech_end(self, speech_processor, call_id):
        """Test processing VAD result for speech end"""
        # Start call processing
        await speech_processor.start_call_processing(call_id)
        call_state = speech_processor.active_calls[call_id]
        
        # Set up speech state with enough duration
        call_state['vad_state']['is_speaking'] = True
        call_state['vad_state']['speech_start_time'] = datetime.utcnow() - timedelta(milliseconds=200)  # Ensure duration > min_speech_duration
        
        # Create VAD result for speech end
        vad_result = VoiceActivityResult(
            is_speech=False,
            confidence=0.9,
            energy_level=0.1,
            duration_ms=100.0,
            timestamp=datetime.utcnow()
        )
        
        # Process VAD result
        events = await speech_processor._process_vad_result(call_id, vad_result, call_state)
        
        assert len(events) == 1
        event = events[0]
        assert event.event_type == SpeechEventType.SPEECH_END
        assert event.call_id == call_id
        assert event.confidence == 0.9
        
        # Check state update
        assert call_state['vad_state']['is_speaking'] is False
        assert call_state['vad_state']['silence_start_time'] == vad_result.timestamp
    
    @pytest.mark.asyncio
    async def test_detect_emotion(self, speech_processor, call_id):
        """Test emotion detection"""
        # Start call processing
        await speech_processor.start_call_processing(call_id)
        call_state = speech_processor.active_calls[call_id]
        
        # Create test audio with high energy (excited emotion)
        excited_audio = np.random.normal(0, 0.9, 1024).astype(np.float32)
        
        # Test emotion detection
        result = await speech_processor._detect_emotion(excited_audio, call_state)
        
        assert result is not None
        assert isinstance(result, EmotionResult)
        assert result.emotion == EmotionType.EXCITED
        assert result.confidence > 0.0
        assert result.intensity > 0.0
        assert result.timestamp is not None
        assert 'energy' in result.features
        
        # Check state update
        assert call_state['emotion_state']['current_emotion'] == EmotionType.EXCITED
        assert len(call_state['emotion_state']['emotion_history']) == 1
    
    @pytest.mark.asyncio
    async def test_detect_barge_in(self, speech_processor, call_id):
        """Test barge-in detection"""
        # Start call processing
        await speech_processor.start_call_processing(call_id)
        call_state = speech_processor.active_calls[call_id]
        
        # Set TTS as speaking
        call_state['tts_state']['is_speaking'] = True
        
        # Create test audio with very high energy (barge-in)
        barge_in_audio = np.random.normal(0, 1.0, 1024).astype(np.float32)
        
        # Test barge-in detection
        detected = await speech_processor._detect_barge_in(barge_in_audio, call_state)
        
        assert detected is True
        assert call_state['barge_in_state']['detected'] is True
        assert call_state['barge_in_state']['last_detection'] is not None
    
    @pytest.mark.asyncio
    async def test_detect_barge_in_no_tts(self, speech_processor, call_id):
        """Test barge-in detection when TTS is not speaking"""
        # Start call processing
        await speech_processor.start_call_processing(call_id)
        call_state = speech_processor.active_calls[call_id]
        
        # TTS is not speaking
        call_state['tts_state']['is_speaking'] = False
        
        # Create test audio with high energy
        audio = np.random.normal(0, 0.8, 1024).astype(np.float32)
        
        # Test barge-in detection (should not detect when TTS is not speaking)
        detected = await speech_processor._detect_barge_in(audio, call_state)
        
        # This test depends on the implementation - if barge-in is only checked when TTS is speaking,
        # then this should return False or the method should not be called
        # For now, we'll assume it returns False when TTS is not speaking
        assert detected is False
    
    @pytest.mark.asyncio
    async def test_synthesize_speech(self, speech_processor, call_id):
        """Test speech synthesis"""
        # Start call processing
        await speech_processor.start_call_processing(call_id)
        
        # Create TTS request
        tts_request = TTSRequest(
            text="Hello, this is a test message",
            voice_id="test_voice",
            speed=1.0,
            pitch=1.0,
            volume=1.0,
            language="en-US"
        )
        
        # Test speech synthesis
        result = await speech_processor.synthesize_speech(call_id, tts_request)
        
        assert result is not None
        assert isinstance(result, TTSResult)
        assert result.audio_data is not None
        assert len(result.audio_data) > 0
        assert result.duration_ms > 0
        assert result.voice_id == "test_voice"
        assert result.text == "Hello, this is a test message"
        assert result.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_no_call(self, speech_processor):
        """Test speech synthesis for non-existent call"""
        tts_request = TTSRequest(
            text="Hello, this is a test message",
            voice_id="test_voice"
        )
        
        result = await speech_processor.synthesize_speech("non_existent_call", tts_request)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_positive(self, speech_processor, call_id):
        """Test sentiment analysis for positive text"""
        # Start call processing
        await speech_processor.start_call_processing(call_id)
        
        # Test positive sentiment
        text = "I love this product, it's excellent and wonderful!"
        result = await speech_processor.analyze_sentiment(call_id, text)
        
        assert result is not None
        assert isinstance(result, SentimentResult)
        assert result.sentiment == SentimentType.POSITIVE
        assert result.confidence > 0.0
        assert result.score > 0.0
        assert result.timestamp is not None
        assert len(result.keywords) > 0
        
        # Check state update
        call_state = speech_processor.active_calls[call_id]
        assert call_state['sentiment_state']['current_sentiment'] == SentimentType.POSITIVE
        assert len(call_state['sentiment_state']['sentiment_history']) == 1
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_negative(self, speech_processor, call_id):
        """Test sentiment analysis for negative text"""
        # Start call processing
        await speech_processor.start_call_processing(call_id)
        
        # Test negative sentiment
        text = "I hate this product, it's terrible and awful!"
        result = await speech_processor.analyze_sentiment(call_id, text)
        
        assert result is not None
        assert isinstance(result, SentimentResult)
        assert result.sentiment == SentimentType.NEGATIVE
        assert result.confidence > 0.0
        assert result.score < 0.0
        assert result.timestamp is not None
        assert len(result.keywords) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_neutral(self, speech_processor, call_id):
        """Test sentiment analysis for neutral text"""
        # Start call processing
        await speech_processor.start_call_processing(call_id)
        
        # Test neutral sentiment
        text = "This is a neutral message without strong emotions."
        result = await speech_processor.analyze_sentiment(call_id, text)
        
        assert result is not None
        assert isinstance(result, SentimentResult)
        assert result.sentiment == SentimentType.NEUTRAL
        assert result.confidence >= 0.0
        assert result.score == 0.0
        assert result.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_event_callback_registration(self, speech_processor, call_id):
        """Test event callback registration"""
        # Register callback
        callback_called = False
        callback_data = None
        
        async def test_callback(event):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = event
        
        speech_processor.register_event_callback(call_id, test_callback)
        
        # Emit test event
        test_event = SpeechEvent(
            event_type=SpeechEventType.SPEECH_START,
            timestamp=datetime.utcnow(),
            call_id=call_id,
            data={'test': 'data'},
            confidence=0.8
        )
        
        await speech_processor._emit_event(call_id, test_event)
        
        assert callback_called is True
        assert callback_data == test_event
    
    @pytest.mark.asyncio
    async def test_event_callback_unregistration(self, speech_processor, call_id):
        """Test event callback unregistration"""
        # Register callback
        callback_called = False
        
        async def test_callback(event):
            nonlocal callback_called
            callback_called = True
        
        speech_processor.register_event_callback(call_id, test_callback)
        
        # Unregister callback
        speech_processor.unregister_event_callback(call_id, test_callback)
        
        # Emit test event
        test_event = SpeechEvent(
            event_type=SpeechEventType.SPEECH_START,
            timestamp=datetime.utcnow(),
            call_id=call_id,
            data={'test': 'data'},
            confidence=0.8
        )
        
        await speech_processor._emit_event(call_id, test_event)
        
        assert callback_called is False
    
    @pytest.mark.asyncio
    async def test_get_call_analytics(self, speech_processor, call_id):
        """Test call analytics retrieval"""
        # Start call processing
        await speech_processor.start_call_processing(call_id)
        
        # Add some test data
        call_state = speech_processor.active_calls[call_id]
        
        # Add emotion history
        call_state['emotion_state']['emotion_history'].append({
            'emotion': EmotionType.HAPPY,
            'timestamp': datetime.utcnow(),
            'confidence': 0.8
        })
        
        # Add sentiment history
        call_state['sentiment_state']['sentiment_history'].append({
            'sentiment': SentimentType.POSITIVE,
            'score': 0.7,
            'timestamp': datetime.utcnow()
        })
        
        # Add ASR results
        call_state['asr_state']['final_results'].append(
            ASRResult(
                text="Test ASR result",
                confidence=0.9,
                is_final=True,
                timestamp=datetime.utcnow(),
                start_time=time.time(),
                end_time=time.time() + 0.1
            )
        )
        
        # Get analytics
        analytics = await speech_processor.get_call_analytics(call_id)
        
        assert analytics is not None
        assert analytics['call_id'] == call_id
        assert 'start_time' in analytics
        assert 'duration' in analytics
        assert 'vad_stats' in analytics
        assert 'emotion_stats' in analytics
        assert 'sentiment_stats' in analytics
        assert 'barge_in_stats' in analytics
        assert 'tts_stats' in analytics
        
        # Check specific values
        assert analytics['emotion_stats']['dominant_emotion'] == 'happy'
        assert analytics['emotion_stats']['emotion_changes'] == 1
        assert analytics['sentiment_stats']['average_score'] == 0.7
        assert analytics['vad_stats']['speech_segments'] == 1
    
    @pytest.mark.asyncio
    async def test_get_call_analytics_no_call(self, speech_processor):
        """Test call analytics for non-existent call"""
        analytics = await speech_processor.get_call_analytics("non_existent_call")
        assert analytics == {}
    
    @pytest.mark.asyncio
    async def test_create_speech_event(self, speech_processor, call_id):
        """Test speech event creation"""
        event = speech_processor._create_speech_event(
            SpeechEventType.EMOTION_DETECTED,
            call_id,
            {'emotion': 'happy', 'confidence': 0.8},
            0.8
        )
        
        assert isinstance(event, SpeechEvent)
        assert event.event_type == SpeechEventType.EMOTION_DETECTED
        assert event.call_id == call_id
        assert event.confidence == 0.8
        assert event.data['emotion'] == 'happy'
        assert event.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_process_audio_chunk_with_events(self, speech_processor, call_id, audio_chunk):
        """Test processing audio chunk that generates events"""
        # Start call processing
        await speech_processor.start_call_processing(call_id)
        
        # Create high-energy audio (should trigger speech detection)
        high_energy_audio = (np.random.normal(0, 0.8, 1024) * 32767).astype(np.int16).tobytes()
        
        # Process audio chunk
        events = await speech_processor.process_audio_chunk(call_id, high_energy_audio)
        
        # Should generate speech start event
        assert len(events) > 0
        
        # Check for speech start event
        speech_start_events = [e for e in events if e.event_type == SpeechEventType.SPEECH_START]
        assert len(speech_start_events) > 0
        
        # Check for emotion detection event
        emotion_events = [e for e in events if e.event_type == SpeechEventType.EMOTION_DETECTED]
        # Note: Emotion detection depends on AI availability, so this might be empty
    
    @pytest.mark.asyncio
    async def test_tts_queue_processing(self, speech_processor, call_id):
        """Test TTS queue processing"""
        # Start call processing
        await speech_processor.start_call_processing(call_id)
        
        # Create first TTS request
        tts_request1 = TTSRequest(
            text="First message",
            voice_id="test_voice"
        )
        
        # Create second TTS request
        tts_request2 = TTSRequest(
            text="Second message",
            voice_id="test_voice"
        )
        
        # Start first synthesis (should be processed immediately)
        result1 = await speech_processor.synthesize_speech(call_id, tts_request1)
        assert result1 is not None
        
        # Start second synthesis (should be queued and processed after first)
        result2 = await speech_processor.synthesize_speech(call_id, tts_request2)
        assert result2 is not None
        
        # Check that both were processed
        call_state = speech_processor.active_calls[call_id]
        assert len(call_state['tts_state']['queue']) == 0
    
    @pytest.mark.asyncio
    async def test_stop_tts(self, speech_processor, call_id):
        """Test stopping TTS"""
        # Start call processing
        await speech_processor.start_call_processing(call_id)
        
        # Set TTS as speaking
        call_state = speech_processor.active_calls[call_id]
        call_state['tts_state']['is_speaking'] = True
        call_state['tts_state']['current_text'] = "Test message"
        call_state['tts_state']['queue'].append(TTSRequest(text="Queued message", voice_id="test"))
        
        # Stop TTS
        success = await speech_processor._stop_tts(call_id)
        
        assert success is True
        assert call_state['tts_state']['is_speaking'] is False
        assert call_state['tts_state']['current_text'] is None
        assert len(call_state['tts_state']['queue']) == 0
    
    @pytest.mark.asyncio
    async def test_stop_tts_no_call(self, speech_processor):
        """Test stopping TTS for non-existent call"""
        success = await speech_processor._stop_tts("non_existent_call")
        assert success is False


class TestSpeechEventTypes:
    """Test cases for speech event types"""
    
    def test_speech_event_types(self):
        """Test speech event type enum values"""
        assert SpeechEventType.SPEECH_START.value == "speech_start"
        assert SpeechEventType.SPEECH_END.value == "speech_end"
        assert SpeechEventType.EMOTION_DETECTED.value == "emotion_detected"
        assert SpeechEventType.BARGE_IN_DETECTED.value == "barge_in_detected"
        assert SpeechEventType.ASR_RESULT.value == "asr_result"
        assert SpeechEventType.TTS_START.value == "tts_start"
        assert SpeechEventType.TTS_END.value == "tts_end"


class TestEmotionTypes:
    """Test cases for emotion types"""
    
    def test_emotion_types(self):
        """Test emotion type enum values"""
        assert EmotionType.HAPPY.value == "happy"
        assert EmotionType.SAD.value == "sad"
        assert EmotionType.ANGRY.value == "angry"
        assert EmotionType.NEUTRAL.value == "neutral"
        assert EmotionType.EXCITED.value == "excited"
        assert EmotionType.FRUSTRATED.value == "frustrated"
        assert EmotionType.CONFUSED.value == "confused"
        assert EmotionType.SURPRISED.value == "surprised"


class TestSentimentTypes:
    """Test cases for sentiment types"""
    
    def test_sentiment_types(self):
        """Test sentiment type enum values"""
        assert SentimentType.POSITIVE.value == "positive"
        assert SentimentType.NEGATIVE.value == "negative"
        assert SentimentType.NEUTRAL.value == "neutral"


class TestDataClasses:
    """Test cases for data classes"""
    
    def test_speech_event_creation(self):
        """Test SpeechEvent creation"""
        event = SpeechEvent(
            event_type=SpeechEventType.SPEECH_START,
            timestamp=datetime.utcnow(),
            call_id="test_call",
            data={'test': 'data'},
            confidence=0.8
        )
        
        assert event.event_type == SpeechEventType.SPEECH_START
        assert event.call_id == "test_call"
        assert event.data['test'] == 'data'
        assert event.confidence == 0.8
    
    def test_voice_activity_result_creation(self):
        """Test VoiceActivityResult creation"""
        result = VoiceActivityResult(
            is_speech=True,
            confidence=0.9,
            energy_level=0.7,
            duration_ms=100.0,
            timestamp=datetime.utcnow()
        )
        
        assert result.is_speech is True
        assert result.confidence == 0.9
        assert result.energy_level == 0.7
        assert result.duration_ms == 100.0
    
    def test_emotion_result_creation(self):
        """Test EmotionResult creation"""
        result = EmotionResult(
            emotion=EmotionType.HAPPY,
            confidence=0.8,
            intensity=0.6,
            timestamp=datetime.utcnow(),
            features={'energy': 0.6}
        )
        
        assert result.emotion == EmotionType.HAPPY
        assert result.confidence == 0.8
        assert result.intensity == 0.6
        assert result.features['energy'] == 0.6
    
    def test_sentiment_result_creation(self):
        """Test SentimentResult creation"""
        result = SentimentResult(
            sentiment=SentimentType.POSITIVE,
            confidence=0.9,
            score=0.7,
            timestamp=datetime.utcnow(),
            keywords=['good', 'great']
        )
        
        assert result.sentiment == SentimentType.POSITIVE
        assert result.confidence == 0.9
        assert result.score == 0.7
        assert result.keywords == ['good', 'great']
    
    def test_asr_result_creation(self):
        """Test ASRResult creation"""
        result = ASRResult(
            text="Hello world",
            confidence=0.95,
            is_final=True,
            timestamp=datetime.utcnow(),
            start_time=time.time(),
            end_time=time.time() + 0.1,
            alternatives=["Hello", "Hi"]
        )
        
        assert result.text == "Hello world"
        assert result.confidence == 0.95
        assert result.is_final is True
        assert result.alternatives == ["Hello", "Hi"]
    
    def test_tts_request_creation(self):
        """Test TTSRequest creation"""
        request = TTSRequest(
            text="Hello world",
            voice_id="test_voice",
            speed=1.2,
            pitch=1.1,
            volume=0.9,
            language="en-US",
            emotion=EmotionType.HAPPY
        )
        
        assert request.text == "Hello world"
        assert request.voice_id == "test_voice"
        assert request.speed == 1.2
        assert request.pitch == 1.1
        assert request.volume == 0.9
        assert request.language == "en-US"
        assert request.emotion == EmotionType.HAPPY
    
    def test_tts_result_creation(self):
        """Test TTSResult creation"""
        result = TTSResult(
            audio_data=b"test_audio_data",
            duration_ms=500.0,
            timestamp=datetime.utcnow(),
            voice_id="test_voice",
            text="Hello world"
        )
        
        assert result.audio_data == b"test_audio_data"
        assert result.duration_ms == 500.0
        assert result.voice_id == "test_voice"
        assert result.text == "Hello world"


if __name__ == "__main__":
    pytest.main([__file__])
