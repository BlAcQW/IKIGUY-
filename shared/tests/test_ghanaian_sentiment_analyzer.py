"""
Unit tests for Ghanaian Language Sentiment Analysis

Tests the GhanaianSentimentAnalyzer class for comprehensive sentiment analysis
capabilities in Ghanaian languages including Twi, Ghana Pidgin, Ewe, Ga, and Dagbani.
"""

import asyncio
import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from apps.shared.ai.ghanaian_sentiment_analyzer import (
    GhanaianSentimentAnalyzer,
    GhanaianSentimentConfig,
    SentimentType,
    EmotionType,
    SentimentResult,
    EmotionResult
)


class TestGhanaianSentimentConfig:
    """Test GhanaianSentimentConfig class"""
    
    def test_config_creation(self):
        """Test creating a valid configuration"""
        config = GhanaianSentimentConfig(api_key="test_key")
        
        assert config.api_key == "test_key"
        assert config.base_url == "https://api.abena.ai/v1"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.confidence_threshold == 0.7
        assert config.enable_cultural_context is True
        assert config.enable_emotion_detection is True
        assert config.enable_intensity_scoring is True
        assert config.cache_results is True
        assert config.cache_ttl == 3600
        assert config.batch_size == 10
    
    def test_config_custom_values(self):
        """Test creating configuration with custom values"""
        config = GhanaianSentimentConfig(
            api_key="custom_key",
            base_url="https://custom.api.com",
            timeout=60,
            max_retries=5,
            confidence_threshold=0.8,
            enable_cultural_context=False,
            enable_emotion_detection=False,
            enable_intensity_scoring=False,
            cache_results=False,
            cache_ttl=1800,
            batch_size=20
        )
        
        assert config.api_key == "custom_key"
        assert config.base_url == "https://custom.api.com"
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.confidence_threshold == 0.8
        assert config.enable_cultural_context is False
        assert config.enable_emotion_detection is False
        assert config.enable_intensity_scoring is False
        assert config.cache_results is False
        assert config.cache_ttl == 1800
        assert config.batch_size == 20


class TestGhanaianSentimentAnalyzer:
    """Test GhanaianSentimentAnalyzer class"""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration"""
        return GhanaianSentimentConfig(api_key="test_key")
    
    @pytest.fixture
    def analyzer(self, config):
        """Create a test analyzer instance"""
        return GhanaianSentimentAnalyzer(config)
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock aiohttp session"""
        return MagicMock()
    
    def create_mock_context_manager(self, mock_response):
        """Helper function to create a properly mocked async context manager"""
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        return mock_context
    
    def test_initialization(self, config):
        """Test analyzer initialization"""
        analyzer = GhanaianSentimentAnalyzer(config)
        
        assert analyzer.config == config
        assert analyzer.session is None
        assert len(analyzer._cache) == 0
        assert len(analyzer._cache_timestamps) == 0
        assert "tw" in analyzer._sentiment_patterns
        assert "en-GH" in analyzer._sentiment_patterns
        assert "ee" in analyzer._sentiment_patterns
        assert "ga" in analyzer._sentiment_patterns
        assert "dag" in analyzer._sentiment_patterns
    
    @pytest.mark.asyncio
    async def test_context_manager(self, analyzer):
        """Test async context manager"""
        async with analyzer as ctx_analyzer:
            assert ctx_analyzer.session is not None
            assert isinstance(ctx_analyzer.session, MagicMock)
        
        # Session should be closed after context exit
        assert analyzer.session is None
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_empty_text(self, analyzer):
        """Test sentiment analysis with empty text"""
        result = await analyzer.analyze_sentiment("")
        
        assert result.sentiment == SentimentType.NEUTRAL
        assert result.confidence == 1.0
        assert result.intensity == 0.0
        assert result.emotions == {EmotionType.NEUTRAL: 1.0}
        assert result.language == "auto"
        assert isinstance(result.timestamp, datetime)
        assert result.context == {}
        assert result.cultural_notes == []
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_whitespace_text(self, analyzer):
        """Test sentiment analysis with whitespace-only text"""
        result = await analyzer.analyze_sentiment("   \n\t   ")
        
        assert result.sentiment == SentimentType.NEUTRAL
        assert result.confidence == 1.0
        assert result.intensity == 0.0
        assert result.emotions == {EmotionType.NEUTRAL: 1.0}
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_twi_positive(self, analyzer):
        """Test sentiment analysis with positive Twi text"""
        text = "ɛyɛ adeɛ paa"
        result = await analyzer.analyze_sentiment(text, language="tw")
        
        assert result.sentiment == SentimentType.POSITIVE
        assert result.confidence > 0.5
        assert result.intensity > 0.5
        assert result.language == "tw"
        assert len(result.cultural_notes) >= 0
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_twi_negative(self, analyzer):
        """Test sentiment analysis with negative Twi text"""
        text = "ɛnyɛ yie"
        result = await analyzer.analyze_sentiment(text, language="tw")
        
        assert result.sentiment == SentimentType.NEGATIVE
        assert result.confidence > 0.5
        assert result.language == "tw"
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_ghana_pidgin_positive(self, analyzer):
        """Test sentiment analysis with positive Ghana Pidgin text"""
        text = "make you dey good"
        result = await analyzer.analyze_sentiment(text, language="en-GH")
        
        assert result.sentiment == SentimentType.POSITIVE
        assert result.confidence > 0.5
        assert result.language == "en-GH"
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_ghana_pidgin_negative(self, analyzer):
        """Test sentiment analysis with negative Ghana Pidgin text"""
        text = "no dey good"
        result = await analyzer.analyze_sentiment(text, language="en-GH")
        
        assert result.sentiment == SentimentType.NEGATIVE
        assert result.confidence > 0.5
        assert result.language == "en-GH"
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_ewe_positive(self, analyzer):
        """Test sentiment analysis with positive Ewe text"""
        text = "nyuie nyo"
        result = await analyzer.analyze_sentiment(text, language="ee")
        
        assert result.sentiment == SentimentType.POSITIVE
        assert result.confidence > 0.5
        assert result.language == "ee"
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_ga_positive(self, analyzer):
        """Test sentiment analysis with positive Ga text"""
        text = "ŋɔ kɛ"
        result = await analyzer.analyze_sentiment(text, language="ga")
        
        assert result.sentiment == SentimentType.POSITIVE
        assert result.confidence > 0.5
        assert result.language == "ga"
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_dagbani_positive(self, analyzer):
        """Test sentiment analysis with positive Dagbani text"""
        text = "damba yili"
        result = await analyzer.analyze_sentiment(text, language="dag")
        
        assert result.sentiment == SentimentType.POSITIVE
        assert result.confidence > 0.5
        assert result.language == "dag"
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_neutral(self, analyzer):
        """Test sentiment analysis with neutral text"""
        text = "hello world"
        result = await analyzer.analyze_sentiment(text, language="en-GH")
        
        assert result.sentiment == SentimentType.NEUTRAL
        assert result.confidence == 0.5
        assert result.language == "en-GH"
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_with_context(self, analyzer):
        """Test sentiment analysis with additional context"""
        text = "ɛyɛ adeɛ"
        context = {"user_id": "123", "call_type": "customer_service"}
        result = await analyzer.analyze_sentiment(text, language="tw", context=context)
        
        assert result.sentiment == SentimentType.POSITIVE
        assert result.context == context
        assert result.language == "tw"
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_auto_language_detection(self, analyzer):
        """Test automatic language detection"""
        text = "ɛyɛ adeɛ paa"
        result = await analyzer.analyze_sentiment(text, language="auto")
        
        assert result.sentiment == SentimentType.POSITIVE
        assert result.language == "tw"  # Should detect Twi
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_auto_language_detection_ghana_pidgin(self, analyzer):
        """Test automatic language detection for Ghana Pidgin"""
        text = "make you dey good"
        result = await analyzer.analyze_sentiment(text, language="auto")
        
        assert result.sentiment == SentimentType.POSITIVE
        assert result.language == "en-GH"  # Should detect Ghana Pidgin
    
    @pytest.mark.asyncio
    async def test_analyze_emotions_empty_text(self, analyzer):
        """Test emotion analysis with empty text"""
        result = await analyzer.analyze_emotions("")
        
        assert result.primary_emotion == EmotionType.NEUTRAL
        assert result.confidence == 1.0
        assert result.emotion_scores == {EmotionType.NEUTRAL: 1.0}
        assert result.intensity == 0.0
        assert result.context == {}
    
    @pytest.mark.asyncio
    async def test_analyze_emotions_joy(self, analyzer):
        """Test emotion analysis for joy"""
        text = "ɛyɛ adeɛ paa"
        result = await analyzer.analyze_emotions(text, language="tw")
        
        assert result.primary_emotion == EmotionType.JOY
        assert result.confidence > 0.0
        assert result.intensity > 0.0
        assert result.context["language"] == "tw"
    
    @pytest.mark.asyncio
    async def test_analyze_emotions_sadness(self, analyzer):
        """Test emotion analysis for sadness"""
        text = "ɛnyɛ yie"
        result = await analyzer.analyze_emotions(text, language="tw")
        
        assert result.primary_emotion == EmotionType.SADNESS
        assert result.confidence > 0.0
        assert result.intensity > 0.0
    
    @pytest.mark.asyncio
    async def test_analyze_emotions_anger(self, analyzer):
        """Test emotion analysis for anger"""
        text = "ɛyɛ bone"
        result = await analyzer.analyze_emotions(text, language="tw")
        
        assert result.primary_emotion == EmotionType.ANGER
        assert result.confidence > 0.0
        assert result.intensity > 0.0
    
    @pytest.mark.asyncio
    async def test_analyze_emotions_fear(self, analyzer):
        """Test emotion analysis for fear"""
        text = "ɛyɛ ahokyere"
        result = await analyzer.analyze_emotions(text, language="tw")
        
        assert result.primary_emotion == EmotionType.FEAR
        assert result.confidence > 0.0
        assert result.intensity > 0.0
    
    @pytest.mark.asyncio
    async def test_analyze_emotions_surprise(self, analyzer):
        """Test emotion analysis for surprise"""
        text = "ɛfie"
        result = await analyzer.analyze_emotions(text, language="tw")
        
        assert result.primary_emotion == EmotionType.SURPRISE
        assert result.confidence > 0.0
        assert result.intensity > 0.0
    
    @pytest.mark.asyncio
    async def test_analyze_emotions_disgust(self, analyzer):
        """Test emotion analysis for disgust"""
        text = "ɛyɛ bone"
        result = await analyzer.analyze_emotions(text, language="tw")
        
        assert result.primary_emotion == EmotionType.DISGUST
        assert result.confidence > 0.0
        assert result.intensity > 0.0
    
    @pytest.mark.asyncio
    async def test_analyze_batch_empty_list(self, analyzer):
        """Test batch analysis with empty list"""
        results = await analyzer.analyze_batch([])
        assert results == []
    
    @pytest.mark.asyncio
    async def test_analyze_batch_single_item(self, analyzer):
        """Test batch analysis with single item"""
        texts = ["ɛyɛ adeɛ"]
        results = await analyzer.analyze_batch(texts, language="tw")
        
        assert len(results) == 1
        assert results[0].sentiment == SentimentType.POSITIVE
        assert results[0].language == "tw"
    
    @pytest.mark.asyncio
    async def test_analyze_batch_multiple_items(self, analyzer):
        """Test batch analysis with multiple items"""
        texts = [
            "ɛyɛ adeɛ",      # Positive Twi
            "ɛnyɛ yie",      # Negative Twi
            "make you dey good",  # Positive Ghana Pidgin
            "no dey good"    # Negative Ghana Pidgin
        ]
        results = await analyzer.analyze_batch(texts, language="auto")
        
        assert len(results) == 4
        assert results[0].sentiment == SentimentType.POSITIVE
        assert results[1].sentiment == SentimentType.NEGATIVE
        assert results[2].sentiment == SentimentType.POSITIVE
        assert results[3].sentiment == SentimentType.NEGATIVE
    
    @pytest.mark.asyncio
    async def test_analyze_batch_large_list(self, analyzer):
        """Test batch analysis with large list (exceeds batch size)"""
        texts = ["ɛyɛ adeɛ"] * 15  # 15 items, batch size is 10
        results = await analyzer.analyze_batch(texts, language="tw")
        
        assert len(results) == 15
        for result in results:
            assert result.sentiment == SentimentType.POSITIVE
            assert result.language == "tw"
    
    @pytest.mark.asyncio
    async def test_api_analysis_success(self, analyzer, mock_session):
        """Test successful API-based analysis"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "sentiment": "positive",
            "confidence": 0.85,
            "intensity": 0.7,
            "emotions": {
                "joy": 0.8,
                "sadness": 0.1,
                "anger": 0.05,
                "fear": 0.02,
                "surprise": 0.02,
                "disgust": 0.01
            },
            "cultural_notes": ["Contains respect indicators"]
        })
        
        mock_session.post.return_value = self.create_mock_context_manager(mock_response)
        analyzer.session = mock_session
        
        result = await analyzer._api_analysis("ɛyɛ adeɛ", "tw", {"test": "context"})
        
        assert result.sentiment == SentimentType.POSITIVE
        assert result.confidence == 0.85
        assert result.intensity == 0.7
        assert result.language == "tw"
        assert result.context == {"test": "context"}
        assert result.cultural_notes == ["Contains respect indicators"]
        assert EmotionType.JOY in result.emotions
        assert result.emotions[EmotionType.JOY] == 0.8
    
    @pytest.mark.asyncio
    async def test_api_analysis_failure(self, analyzer, mock_session):
        """Test API analysis failure falls back to pattern-based"""
        # Mock API failure
        mock_response = MagicMock()
        mock_response.status = 500
        
        mock_session.post.return_value = self.create_mock_context_manager(mock_response)
        analyzer.session = mock_session
        
        # Should fall back to pattern-based analysis
        result = await analyzer._perform_analysis("ɛyɛ adeɛ", "tw", {})
        
        assert result.sentiment == SentimentType.POSITIVE
        assert result.language == "tw"
    
    @pytest.mark.asyncio
    async def test_api_analysis_exception(self, analyzer, mock_session):
        """Test API analysis exception falls back to pattern-based"""
        # Mock API exception
        mock_session.post.side_effect = Exception("API Error")
        analyzer.session = mock_session
        
        # Should fall back to pattern-based analysis
        result = await analyzer._perform_analysis("ɛyɛ adeɛ", "tw", {})
        
        assert result.sentiment == SentimentType.POSITIVE
        assert result.language == "tw"
    
    @pytest.mark.asyncio
    async def test_language_detection_twi(self, analyzer):
        """Test language detection for Twi"""
        text = "ɛyɛ adeɛ paa"
        language = await analyzer._detect_language(text)
        assert language == "tw"
    
    @pytest.mark.asyncio
    async def test_language_detection_ghana_pidgin(self, analyzer):
        """Test language detection for Ghana Pidgin"""
        text = "make you dey good"
        language = await analyzer._detect_language(text)
        assert language == "en-GH"
    
    @pytest.mark.asyncio
    async def test_language_detection_ewe(self, analyzer):
        """Test language detection for Ewe"""
        text = "nyuie nyo"
        language = await analyzer._detect_language(text)
        assert language == "ee"
    
    @pytest.mark.asyncio
    async def test_language_detection_ga(self, analyzer):
        """Test language detection for Ga"""
        text = "ŋɔ kɛ"
        language = await analyzer._detect_language(text)
        assert language == "ga"
    
    @pytest.mark.asyncio
    async def test_language_detection_dagbani(self, analyzer):
        """Test language detection for Dagbani"""
        text = "damba yili"
        language = await analyzer._detect_language(text)
        assert language == "dag"
    
    @pytest.mark.asyncio
    async def test_language_detection_unknown(self, analyzer):
        """Test language detection for unknown text"""
        text = "hello world"
        language = await analyzer._detect_language(text)
        assert language == "tw"  # Default fallback
    
    def test_calculate_intensity_basic(self, analyzer):
        """Test intensity calculation"""
        text = "ɛyɛ adeɛ"
        intensifiers = ["paa", "kɛse", "fɛfɛ"]
        intensity = analyzer._calculate_intensity(text, intensifiers)
        
        assert 0.5 <= intensity <= 1.0
    
    def test_calculate_intensity_with_intensifiers(self, analyzer):
        """Test intensity calculation with intensifiers"""
        text = "ɛyɛ adeɛ paa kɛse"
        intensifiers = ["paa", "kɛse", "fɛfɛ"]
        intensity = analyzer._calculate_intensity(text, intensifiers)
        
        assert intensity > 0.5
    
    def test_calculate_intensity_with_repetition(self, analyzer):
        """Test intensity calculation with word repetition"""
        text = "ɛyɛ ɛyɛ ɛyɛ adeɛ"
        intensifiers = ["paa"]
        intensity = analyzer._calculate_intensity(text, intensifiers)
        
        assert intensity > 0.5
    
    def test_analyze_cultural_context_twi(self, analyzer):
        """Test cultural context analysis for Twi"""
        text = "ɛfie ɛna"
        notes = analyzer._analyze_cultural_context(text, "tw")
        
        assert len(notes) > 0
        assert any("respect" in note.lower() for note in notes)
        assert any("formal" in note.lower() for note in notes)
    
    def test_analyze_cultural_context_ghana_pidgin(self, analyzer):
        """Test cultural context analysis for Ghana Pidgin"""
        text = "oga madam"
        notes = analyzer._analyze_cultural_context(text, "en-GH")
        
        assert len(notes) > 0
        assert any("respect" in note.lower() for note in notes)
        assert any("formal" in note.lower() for note in notes)
    
    def test_analyze_cultural_context_no_indicators(self, analyzer):
        """Test cultural context analysis with no indicators"""
        text = "hello world"
        notes = analyzer._analyze_cultural_context(text, "en-GH")
        
        assert len(notes) == 0
    
    def test_get_supported_languages(self, analyzer):
        """Test getting supported languages"""
        languages = analyzer.get_supported_languages()
        
        expected_languages = ["tw", "en-GH", "ee", "ga", "dag"]
        assert all(lang in languages for lang in expected_languages)
    
    def test_get_analysis_features(self, analyzer):
        """Test getting analysis features"""
        features = analyzer.get_analysis_features()
        
        assert features["sentiment_analysis"] is True
        assert features["emotion_detection"] is True
        assert features["intensity_scoring"] is True
        assert features["cultural_context"] is True
        assert features["language_detection"] is True
        assert features["batch_processing"] is True
    
    def test_clear_cache(self, analyzer):
        """Test clearing the cache"""
        # Add some items to cache
        analyzer._cache["test_key"] = analyzer._create_neutral_result("tw")
        analyzer._cache_timestamps["test_key"] = datetime.utcnow()
        
        assert len(analyzer._cache) > 0
        assert len(analyzer._cache_timestamps) > 0
        
        analyzer.clear_cache()
        
        assert len(analyzer._cache) == 0
        assert len(analyzer._cache_timestamps) == 0
    
    def test_get_cache_stats_empty(self, analyzer):
        """Test getting cache statistics when empty"""
        stats = analyzer.get_cache_stats()
        
        assert stats["cache_size"] == 0
        assert stats["cache_enabled"] is True
        assert stats["cache_ttl"] == 3600
        assert stats["oldest_entry"] is None
        assert stats["newest_entry"] is None
    
    def test_get_cache_stats_with_data(self, analyzer):
        """Test getting cache statistics with data"""
        # Add some items to cache
        analyzer._cache["test_key1"] = analyzer._create_neutral_result("tw")
        analyzer._cache["test_key2"] = analyzer._create_neutral_result("en-GH")
        analyzer._cache_timestamps["test_key1"] = datetime.utcnow()
        analyzer._cache_timestamps["test_key2"] = datetime.utcnow()
        
        stats = analyzer.get_cache_stats()
        
        assert stats["cache_size"] == 2
        assert stats["cache_enabled"] is True
        assert stats["cache_ttl"] == 3600
        assert stats["oldest_entry"] is not None
        assert stats["newest_entry"] is not None
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, analyzer):
        """Test that caching works correctly"""
        text = "ɛyɛ adeɛ"
        
        # First analysis should not be cached
        result1 = await analyzer.analyze_sentiment(text, language="tw")
        assert result1.sentiment == SentimentType.POSITIVE
        
        # Second analysis should be cached
        result2 = await analyzer.analyze_sentiment(text, language="tw")
        assert result2.sentiment == SentimentType.POSITIVE
        
        # Results should be the same
        assert result1.sentiment == result2.sentiment
        assert result1.confidence == result2.confidence
    
    @pytest.mark.asyncio
    async def test_error_handling_sentiment_analysis(self, analyzer):
        """Test error handling in sentiment analysis"""
        # Mock an error in pattern-based analysis
        with patch.object(analyzer, '_pattern_based_analysis', side_effect=Exception("Test error")):
            result = await analyzer.analyze_sentiment("ɛyɛ adeɛ", language="tw")
            
            # Should return neutral result on error
            assert result.sentiment == SentimentType.NEUTRAL
            assert result.confidence == 1.0
            assert result.language == "tw"
    
    @pytest.mark.asyncio
    async def test_error_handling_emotion_analysis(self, analyzer):
        """Test error handling in emotion analysis"""
        # Mock an error in emotion analysis
        with patch.object(analyzer, '_perform_emotion_analysis', side_effect=Exception("Test error")):
            result = await analyzer.analyze_emotions("ɛyɛ adeɛ", language="tw")
            
            # Should return neutral result on error
            assert result.primary_emotion == EmotionType.NEUTRAL
            assert result.confidence == 0.0
            assert result.emotion_scores == {EmotionType.NEUTRAL: 1.0}
    
    @pytest.mark.asyncio
    async def test_batch_analysis_with_errors(self, analyzer):
        """Test batch analysis handles errors gracefully"""
        texts = ["ɛyɛ adeɛ", "invalid text", "make you dey good"]
        
        # Mock error for second text
        with patch.object(analyzer, 'analyze_sentiment', side_effect=[
            analyzer._create_neutral_result("tw"),  # First call succeeds
            Exception("Test error"),                # Second call fails
            analyzer._create_neutral_result("en-GH")  # Third call succeeds
        ]):
            results = await analyzer.analyze_batch(texts, language="auto")
            
            assert len(results) == 3
            assert results[0].sentiment == SentimentType.NEUTRAL
            assert results[1].sentiment == SentimentType.NEUTRAL  # Error fallback
            assert results[2].sentiment == SentimentType.NEUTRAL


class TestSentimentResult:
    """Test SentimentResult dataclass"""
    
    def test_sentiment_result_creation(self):
        """Test creating a SentimentResult"""
        result = SentimentResult(
            sentiment=SentimentType.POSITIVE,
            confidence=0.8,
            intensity=0.7,
            emotions={EmotionType.JOY: 0.8, EmotionType.NEUTRAL: 0.2},
            language="tw",
            timestamp=datetime.utcnow(),
            context={"test": "value"},
            cultural_notes=["Contains respect indicators"]
        )
        
        assert result.sentiment == SentimentType.POSITIVE
        assert result.confidence == 0.8
        assert result.intensity == 0.7
        assert result.language == "tw"
        assert result.context == {"test": "value"}
        assert result.cultural_notes == ["Contains respect indicators"]


class TestEmotionResult:
    """Test EmotionResult dataclass"""
    
    def test_emotion_result_creation(self):
        """Test creating an EmotionResult"""
        result = EmotionResult(
            primary_emotion=EmotionType.JOY,
            confidence=0.8,
            emotion_scores={EmotionType.JOY: 0.8, EmotionType.NEUTRAL: 0.2},
            intensity=0.7,
            context={"language": "tw"}
        )
        
        assert result.primary_emotion == EmotionType.JOY
        assert result.confidence == 0.8
        assert result.intensity == 0.7
        assert result.context == {"language": "tw"}
