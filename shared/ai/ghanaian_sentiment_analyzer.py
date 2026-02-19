"""
Ghanaian Language Sentiment Analysis Module

This module provides advanced sentiment analysis capabilities specifically designed
for Ghanaian languages including Twi, Ghana Pidgin, Ewe, Ga, and Dagbani.

Features:
- Multi-language sentiment analysis
- Emotion detection (joy, sadness, anger, fear, surprise, disgust)
- Sentiment intensity scoring
- Context-aware analysis
- Cultural sensitivity considerations
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SentimentType(Enum):
    """Sentiment classification types"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class EmotionType(Enum):
    """Emotion classification types"""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"


@dataclass
class SentimentResult:
    """Result of sentiment analysis"""
    sentiment: SentimentType
    confidence: float
    intensity: float  # 0.0 to 1.0
    emotions: Dict[EmotionType, float]
    language: str
    timestamp: datetime
    context: Dict[str, any]
    cultural_notes: List[str]


@dataclass
class EmotionResult:
    """Result of emotion analysis"""
    primary_emotion: EmotionType
    confidence: float
    emotion_scores: Dict[EmotionType, float]
    intensity: float
    context: Dict[str, any]


class GhanaianSentimentConfig(BaseModel):
    """Configuration for Ghanaian sentiment analysis"""
    api_key: str = Field(..., description="API key for sentiment analysis service")
    base_url: str = Field(default="https://api.abena.ai/v1", description="Base URL for API")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence threshold")
    
    # Language-specific settings
    enable_cultural_context: bool = Field(default=True, description="Enable cultural context analysis")
    enable_emotion_detection: bool = Field(default=True, description="Enable emotion detection")
    enable_intensity_scoring: bool = Field(default=True, description="Enable intensity scoring")
    
    # Performance settings
    cache_results: bool = Field(default=True, description="Cache analysis results")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    batch_size: int = Field(default=10, description="Batch size for bulk analysis")


class GhanaianSentimentAnalyzer:
    """
    Advanced sentiment analyzer for Ghanaian languages
    
    Provides comprehensive sentiment analysis with cultural context awareness,
    emotion detection, and intensity scoring for Ghanaian languages.
    """
    
    def __init__(self, config: GhanaianSentimentConfig):
        """
        Initialize the sentiment analyzer
        
        Args:
            config: Configuration for the sentiment analyzer
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, SentimentResult] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # Language-specific sentiment patterns
        self._sentiment_patterns = {
            "tw": {
                "positive": [
                    "ɛyɛ", "yɛ", "pa", "nyɛ", "kɛse", "fɛfɛ", "yie", "paa",
                    "ɛyɛ adeɛ", "ɛyɛ yie", "ɛyɛ pa", "ɛyɛ kɛse"
                ],
                "negative": [
                    "nyɛ", "ɛnyɛ", "ɛnyɛ yie", "ɛnyɛ pa", "ɛnyɛ adeɛ",
                    "ɛyɛ bone", "ɛyɛ haw", "ɛyɛ yaw", "ɛyɛ ahokyere"
                ],
                "intensifiers": [
                    "paa", "kɛse", "fɛfɛ", "yie", "bone", "haw", "yaw"
                ]
            },
            "en-GH": {
                "positive": [
                    "good", "fine", "okay", "nice", "great", "excellent",
                    "make you", "dey", "fit", "chop", "wahala", "naija"
                ],
                "negative": [
                    "bad", "no good", "wahala", "trouble", "problem",
                    "no fit", "no dey", "no chop", "suffering"
                ],
                "intensifiers": [
                    "very", "too", "so", "really", "well", "bad"
                ]
            },
            "ee": {
                "positive": [
                    "nyuie", "nyo", "kɔ", "le", "nye", "wo"
                ],
                "negative": [
                    "nye", "le", "wo", "kɔ", "nyuie", "nyo"
                ],
                "intensifiers": [
                    "nyuie", "nyo", "kɔ", "le"
                ]
            },
            "ga": {
                "positive": [
                    "ŋɔ", "ŋɔɔ", "kɛ", "le", "ye", "mi"
                ],
                "negative": [
                    "ŋɔ", "ŋɔɔ", "kɛ", "le", "ye", "mi"
                ],
                "intensifiers": [
                    "ŋɔ", "ŋɔɔ", "kɛ", "le"
                ]
            },
            "dag": {
                "positive": [
                    "damba", "yili", "ka", "ya", "la", "ŋɔ"
                ],
                "negative": [
                    "damba", "yili", "ka", "ya", "la", "ŋɔ"
                ],
                "intensifiers": [
                    "damba", "yili", "ka", "ya"
                ]
            }
        }
        
        # Cultural context patterns
        self._cultural_patterns = {
            "respect_indicators": [
                "ɛfie", "ɛna", "ɛfɛ", "ɛyɛ", "ɛnyɛ",  # Twi respect markers
                "oga", "madam", "sir", "ma", "pa",    # Ghana Pidgin respect
                "wo", "me", "nye", "le", "nyuie"      # Ewe respect markers
            ],
            "formality_indicators": [
                "ɛyɛ", "ɛnyɛ", "ɛfie", "ɛna",        # Twi formal markers
                "make you", "dey", "fit", "chop",     # Ghana Pidgin formal
                "wo", "me", "nye", "le"              # Ewe formal markers
            ]
        }
        
        logger.info("GhanaianSentimentAnalyzer initialized with cultural context awareness")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def analyze_sentiment(
        self, 
        text: str, 
        language: str = "auto",
        context: Optional[Dict[str, any]] = None
    ) -> SentimentResult:
        """
        Analyze sentiment of text in Ghanaian languages
        
        Args:
            text: Text to analyze
            language: Language code (tw, en-GH, ee, ga, dag) or "auto" for detection
            context: Additional context for analysis
            
        Returns:
            SentimentResult with comprehensive analysis
        """
        if not text.strip():
            return self._create_neutral_result(language or "auto")
        
        # Check cache first
        cache_key = f"{text.lower()}:{language}:{hash(str(context))}"
        if self.config.cache_results and cache_key in self._cache:
            cached_result = self._cache[cache_key]
            cache_age = (datetime.utcnow() - self._cache_timestamps[cache_key]).total_seconds()
            if cache_age < self.config.cache_ttl:
                logger.debug(f"Returning cached sentiment result for: {text[:50]}...")
                return cached_result
        
        # Auto-detect language if needed
        if language == "auto":
            language = await self._detect_language(text)
        
        # Perform analysis
        try:
            result = await self._perform_analysis(text, language, context or {})
            
            # Cache result
            if self.config.cache_results:
                self._cache[cache_key] = result
                self._cache_timestamps[cache_key] = datetime.utcnow()
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return self._create_neutral_result(language)
    
    async def analyze_emotions(
        self, 
        text: str, 
        language: str = "auto"
    ) -> EmotionResult:
        """
        Analyze emotions in Ghanaian language text
        
        Args:
            text: Text to analyze
            language: Language code or "auto" for detection
            
        Returns:
            EmotionResult with emotion analysis
        """
        if not text.strip():
            return EmotionResult(
                primary_emotion=EmotionType.NEUTRAL,
                confidence=1.0,
                emotion_scores={EmotionType.NEUTRAL: 1.0},
                intensity=0.0,
                context={}
            )
        
        # Auto-detect language if needed
        if language == "auto":
            language = await self._detect_language(text)
        
        try:
            return await self._perform_emotion_analysis(text, language)
        except Exception as e:
            logger.error(f"Error analyzing emotions: {e}")
            return EmotionResult(
                primary_emotion=EmotionType.NEUTRAL,
                confidence=0.0,
                emotion_scores={EmotionType.NEUTRAL: 1.0},
                intensity=0.0,
                context={}
            )
    
    async def analyze_batch(
        self, 
        texts: List[str], 
        language: str = "auto"
    ) -> List[SentimentResult]:
        """
        Analyze sentiment for multiple texts in batch
        
        Args:
            texts: List of texts to analyze
            language: Language code or "auto" for detection
            
        Returns:
            List of SentimentResult objects
        """
        if not texts:
            return []
        
        # Process in batches
        results = []
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i:i + self.config.batch_size]
            batch_results = await asyncio.gather(
                *[self.analyze_sentiment(text, language) for text in batch],
                return_exceptions=True
            )
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch analysis error: {result}")
                    results.append(self._create_neutral_result(language))
                else:
                    results.append(result)
        
        return results
    
    async def _perform_analysis(
        self, 
        text: str, 
        language: str, 
        context: Dict[str, any]
    ) -> SentimentResult:
        """Perform the actual sentiment analysis"""
        
        # Try API-based analysis first
        try:
            if self.session:
                return await self._api_analysis(text, language, context)
        except Exception as e:
            logger.warning(f"API analysis failed, falling back to pattern-based: {e}")
        
        # Fall back to pattern-based analysis
        return await self._pattern_based_analysis(text, language, context)
    
    async def _api_analysis(
        self, 
        text: str, 
        language: str, 
        context: Dict[str, any]
    ) -> SentimentResult:
        """Perform analysis using external API"""
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "language": language,
            "features": ["sentiment", "emotions", "intensity"],
            "context": context
        }
        
        async with self.session.post(
            f"{self.config.base_url}/sentiment/analyze",
            headers=headers,
            json=payload
        ) as response:
            if response.status == 200:
                data = await response.json()
                return self._parse_api_response(data, language, context)
            else:
                raise Exception(f"API request failed: {response.status}")
    
    async def _pattern_based_analysis(
        self, 
        text: str, 
        language: str, 
        context: Dict[str, any]
    ) -> SentimentResult:
        """Perform pattern-based sentiment analysis"""
        
        text_lower = text.lower()
        patterns = self._sentiment_patterns.get(language, self._sentiment_patterns["tw"])
        
        # Count positive and negative patterns
        positive_count = sum(1 for pattern in patterns["positive"] if pattern in text_lower)
        negative_count = sum(1 for pattern in patterns["negative"] if pattern in text_lower)
        
        # Calculate intensity based on intensifiers
        intensity = self._calculate_intensity(text_lower, patterns.get("intensifiers", []))
        
        # Determine sentiment
        if positive_count > negative_count:
            sentiment = SentimentType.POSITIVE
            confidence = min(0.9, 0.5 + (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count:
            sentiment = SentimentType.NEGATIVE
            confidence = min(0.9, 0.5 + (negative_count - positive_count) * 0.1)
        else:
            sentiment = SentimentType.NEUTRAL
            confidence = 0.5
        
        # Analyze emotions
        emotions = await self._analyze_emotions_pattern(text_lower, language)
        
        # Cultural context analysis
        cultural_notes = self._analyze_cultural_context(text_lower, language)
        
        return SentimentResult(
            sentiment=sentiment,
            confidence=confidence,
            intensity=intensity,
            emotions=emotions,
            language=language,
            timestamp=datetime.utcnow(),
            context=context,
            cultural_notes=cultural_notes
        )
    
    async def _perform_emotion_analysis(self, text: str, language: str) -> EmotionResult:
        """Perform emotion analysis"""
        
        text_lower = text.lower()
        
        # Emotion patterns for Ghanaian languages
        emotion_patterns = {
            "joy": [
                "ɛyɛ", "yɛ", "pa", "nyɛ", "kɛse", "fɛfɛ", "yie",  # Twi
                "good", "fine", "nice", "great", "excellent",      # Ghana Pidgin
                "nyuie", "nyo", "kɔ", "le"                        # Ewe
            ],
            "sadness": [
                "ɛnyɛ", "ɛnyɛ yie", "ɛnyɛ pa", "ɛnyɛ adeɛ",      # Twi
                "bad", "no good", "sad", "cry", "suffering",      # Ghana Pidgin
                "nye", "le", "wo"                                 # Ewe
            ],
            "anger": [
                "ɛyɛ bone", "ɛyɛ haw", "ɛyɛ yaw", "ɛyɛ ahokyere", # Twi
                "angry", "mad", "furious", "rage", "hate",        # Ghana Pidgin
                "kɔ", "le", "nye"                                 # Ewe
            ],
            "fear": [
                "ɛyɛ ahokyere", "ɛyɛ haw", "ɛyɛ yaw",            # Twi
                "fear", "scared", "afraid", "terror", "panic",    # Ghana Pidgin
                "wo", "le", "nye"                                 # Ewe
            ],
            "surprise": [
                "ɛyɛ", "ɛnyɛ", "ɛfie", "ɛna",                    # Twi
                "wow", "amazing", "incredible", "unbelievable",   # Ghana Pidgin
                "wo", "me", "nye"                                 # Ewe
            ],
            "disgust": [
                "ɛyɛ bone", "ɛyɛ haw", "ɛyɛ yaw",                # Twi
                "disgust", "nasty", "gross", "yuck", "eww",      # Ghana Pidgin
                "nye", "le", "wo"                                 # Ewe
            ]
        }
        
        # Calculate emotion scores
        emotion_scores = {}
        for emotion, patterns in emotion_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text_lower)
            emotion_scores[EmotionType(emotion)] = min(1.0, score * 0.2)
        
        # Ensure neutral is always present
        emotion_scores[EmotionType.NEUTRAL] = max(0.1, 1.0 - sum(emotion_scores.values()))
        
        # Find primary emotion
        primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
        confidence = emotion_scores[primary_emotion]
        
        # Calculate intensity
        intensity = sum(emotion_scores.values()) / len(emotion_scores)
        
        return EmotionResult(
            primary_emotion=primary_emotion,
            confidence=confidence,
            emotion_scores=emotion_scores,
            intensity=intensity,
            context={"language": language}
        )
    
    async def _detect_language(self, text: str) -> str:
        """Detect the language of the text"""
        
        text_lower = text.lower()
        
        # Language detection patterns
        language_patterns = {
            "tw": ["ɛ", "ɔ", "ɛyɛ", "yɛ", "kɔ", "baa", "me", "wo", "ɔno", "saa"],
            "en-GH": ["make you", "dey", "fit", "chop", "wahala", "naija", "oga"],
            "ee": ["wo", "me", "nye", "le", "nyuie", "nyo", "kɔ"],
            "ga": ["mi", "wo", "ye", "le", "ŋɔ", "ŋɔɔ", "kɛ"],
            "dag": ["ka", "ya", "la", "ŋɔ", "ŋɔɔ", "kɛ", "damba", "yili"]
        }
        
        scores = {}
        for lang, patterns in language_patterns.items():
            scores[lang] = sum(1 for pattern in patterns if pattern in text_lower)
        
        # Return language with highest score, default to Twi
        return max(scores.items(), key=lambda x: x[1])[0] if any(scores.values()) else "tw"
    
    def _calculate_intensity(self, text: str, intensifiers: List[str]) -> float:
        """Calculate sentiment intensity based on intensifiers"""
        
        intensity = 0.5  # Base intensity
        
        # Count intensifiers
        intensifier_count = sum(1 for intensifier in intensifiers if intensifier in text)
        
        # Adjust intensity based on intensifiers
        if intensifier_count > 0:
            intensity = min(1.0, 0.5 + (intensifier_count * 0.1))
        
        # Check for repetition (common in Ghanaian languages)
        words = text.split()
        if len(words) > 2:
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            
            max_repetition = max(word_counts.values())
            if max_repetition > 2:
                intensity = min(1.0, intensity + 0.2)
        
        return intensity
    
    async def _analyze_emotions_pattern(self, text: str, language: str) -> Dict[EmotionType, float]:
        """Analyze emotions using pattern matching"""
        
        emotion_result = await self._perform_emotion_analysis(text, language)
        return emotion_result.emotion_scores
    
    def _analyze_cultural_context(self, text: str, language: str) -> List[str]:
        """Analyze cultural context and provide notes"""
        
        notes = []
        text_lower = text.lower()
        
        # Check for respect indicators
        respect_count = sum(1 for indicator in self._cultural_patterns["respect_indicators"] 
                           if indicator in text_lower)
        if respect_count > 0:
            notes.append(f"Contains {respect_count} respect indicators")
        
        # Check for formality indicators
        formality_count = sum(1 for indicator in self._cultural_patterns["formality_indicators"] 
                             if indicator in text_lower)
        if formality_count > 0:
            notes.append(f"Contains {formality_count} formality indicators")
        
        # Language-specific cultural notes
        if language == "tw":
            if "ɛfie" in text_lower:
                notes.append("Uses formal Twi address (ɛfie)")
            if "ɛna" in text_lower:
                notes.append("Uses respectful address (ɛna)")
        elif language == "en-GH":
            if "oga" in text_lower:
                notes.append("Uses respectful Ghana Pidgin address (oga)")
            if "madam" in text_lower or "sir" in text_lower:
                notes.append("Uses formal English address")
        
        return notes
    
    def _parse_api_response(
        self, 
        data: Dict[str, any], 
        language: str, 
        context: Dict[str, any]
    ) -> SentimentResult:
        """Parse API response into SentimentResult"""
        
        return SentimentResult(
            sentiment=SentimentType(data.get("sentiment", "neutral")),
            confidence=data.get("confidence", 0.5),
            intensity=data.get("intensity", 0.5),
            emotions={
                EmotionType(emotion): score 
                for emotion, score in data.get("emotions", {}).items()
            },
            language=language,
            timestamp=datetime.utcnow(),
            context=context,
            cultural_notes=data.get("cultural_notes", [])
        )
    
    def _create_neutral_result(self, language: str) -> SentimentResult:
        """Create a neutral sentiment result"""
        
        return SentimentResult(
            sentiment=SentimentType.NEUTRAL,
            confidence=1.0,
            intensity=0.0,
            emotions={EmotionType.NEUTRAL: 1.0},
            language=language,
            timestamp=datetime.utcnow(),
            context={},
            cultural_notes=[]
        )
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return list(self._sentiment_patterns.keys())
    
    def get_analysis_features(self) -> Dict[str, bool]:
        """Get available analysis features"""
        return {
            "sentiment_analysis": True,
            "emotion_detection": self.config.enable_emotion_detection,
            "intensity_scoring": self.config.enable_intensity_scoring,
            "cultural_context": self.config.enable_cultural_context,
            "language_detection": True,
            "batch_processing": True
        }
    
    def clear_cache(self):
        """Clear the analysis cache"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Sentiment analysis cache cleared")
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self._cache),
            "cache_enabled": self.config.cache_results,
            "cache_ttl": self.config.cache_ttl,
            "oldest_entry": min(self._cache_timestamps.values()) if self._cache_timestamps else None,
            "newest_entry": max(self._cache_timestamps.values()) if self._cache_timestamps else None
        }
