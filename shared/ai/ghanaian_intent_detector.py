"""
Ghanaian Language Intent Detection Module

This module provides advanced Intent Detection capabilities specifically designed
for Ghanaian languages including Twi, Ghana Pidgin, Ewe, Ga, and Dagbani.

Features:
- Multi-language intent detection for Ghanaian languages
- Local context awareness (business, social, cultural)
- Intent confidence scoring
- Cultural sensitivity considerations
- Domain-specific intent patterns
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Intent classification types"""
    GREETING = "greeting"
    FAREWELL = "farewell"
    QUESTION = "question"
    STATEMENT = "statement"
    REQUEST = "request"
    COMPLAINT = "complaint"
    APPOINTMENT = "appointment"
    PAYMENT = "payment"
    INQUIRY = "inquiry"
    CONFIRMATION = "confirmation"
    DENIAL = "denial"
    THANKS = "thanks"
    HELP = "help"
    EMERGENCY = "emergency"
    UNKNOWN = "unknown"


class DomainType(Enum):
    """Domain classification types"""
    BUSINESS = "business"
    SOCIAL = "social"
    CULTURAL = "cultural"
    MEDICAL = "medical"
    FINANCIAL = "financial"
    EDUCATIONAL = "educational"
    GENERAL = "general"


@dataclass
class IntentResult:
    """Result of intent detection"""
    primary_intent: IntentType
    confidence: float
    domain: DomainType
    language: str
    timestamp: datetime
    context: Dict[str, any]
    alternative_intents: List[Tuple[IntentType, float]]
    cultural_notes: List[str]


class GhanaianIntentConfig(BaseModel):
    """Configuration for Ghanaian intent detection"""
    api_key: str = Field(..., description="API key for intent detection service")
    base_url: str = Field(default="https://api.abena.ai/v1", description="Base URL for API")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence threshold")
    
    # Language-specific settings
    enable_cultural_context: bool = Field(default=True, description="Enable cultural context analysis")
    enable_domain_detection: bool = Field(default=True, description="Enable domain detection")
    
    # Performance settings
    cache_results: bool = Field(default=True, description="Cache analysis results")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    batch_size: int = Field(default=10, description="Batch size for bulk analysis")


class GhanaianIntentDetector:
    """
    Advanced intent detector for Ghanaian languages
    
    Provides comprehensive intent detection with cultural context awareness
    and domain-specific patterns for Ghanaian languages.
    """
    
    def __init__(self, config: GhanaianIntentConfig):
        """
        Initialize the intent detector
        
        Args:
            config: Configuration for the intent detector
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, IntentResult] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # Ghana-specific intent patterns
        self._intent_patterns = {
            "tw": {
                "greeting": [
                    r"\b(?:ɛyɛ|yɛ|ɛnyɛ)\s+(?:adeɛ|yie|pa)\b",
                    r"\b(?:ɛfie|ɛna|ɛba)\b",
                    r"\b(?:ɛyɛ|yɛ|ɛnyɛ)\s+(?:ɛfie|ɛna|ɛba)\b"
                ],
                "farewell": [
                    r"\b(?:ɛyɛ|yɛ|ɛnyɛ)\s+(?:adeɛ|yie|pa)\s+(?:paa|kɛse)\b",
                    r"\b(?:ɛfie|ɛna|ɛba)\s+(?:paa|kɛse)\b"
                ],
                "question": [
                    r"\b(?:ɛyɛ|yɛ|ɛnyɛ)\s+(?:adeɛ|yie|pa)\s*\?\b",
                    r"\b(?:ɛfie|ɛna|ɛba)\s*\?\b",
                    r"\b(?:ɛyɛ|yɛ|ɛnyɛ)\s+(?:ɛfie|ɛna|ɛba)\s*\?\b"
                ],
                "request": [
                    r"\b(?:ɛyɛ|yɛ|ɛnyɛ)\s+(?:adeɛ|yie|pa)\s+(?:paa|kɛse)\b",
                    r"\b(?:ɛfie|ɛna|ɛba)\s+(?:paa|kɛse)\b"
                ],
                "complaint": [
                    r"\b(?:ɛnyɛ|ɛyɛ)\s+(?:yie|pa|adeɛ)\b",
                    r"\b(?:ɛyɛ)\s+(?:bone|haw|yaw|ahokyere)\b"
                ],
                "thanks": [
                    r"\b(?:ɛyɛ|yɛ|ɛnyɛ)\s+(?:adeɛ|yie|pa)\s+(?:paa|kɛse)\b",
                    r"\b(?:ɛfie|ɛna|ɛba)\s+(?:paa|kɛse)\b"
                ]
            },
            "en-GH": {
                "greeting": [
                    r"\b(?:hello|hi|good morning|good afternoon|good evening)\b",
                    r"\b(?:make you|dey|fit|chop)\s+(?:good|fine|okay)\b"
                ],
                "farewell": [
                    r"\b(?:goodbye|bye|see you|take care)\b",
                    r"\b(?:make you|dey|fit|chop)\s+(?:good|fine|okay)\s+(?:paa|kɛse)\b"
                ],
                "question": [
                    r"\b(?:what|when|where|who|why|how)\b",
                    r"\b(?:make you|dey|fit|chop)\s*\?\b"
                ],
                "request": [
                    r"\b(?:please|make you|dey|fit|chop)\b",
                    r"\b(?:can you|could you|would you)\b"
                ],
                "complaint": [
                    r"\b(?:no good|bad|wahala|trouble|problem)\b",
                    r"\b(?:no fit|no dey|no chop)\b"
                ],
                "thanks": [
                    r"\b(?:thank you|thanks|thank you very much)\b",
                    r"\b(?:make you|dey|fit|chop)\s+(?:good|fine|okay)\b"
                ]
            },
            "ee": {
                "greeting": [
                    r"\b(?:wo|me|nye|le|nyuie|nyo|kɔ)\b",
                    r"\b(?:nyuie|nyo|kɔ|le|nye|wo)\s+(?:nyuie|nyo|kɔ)\b"
                ],
                "farewell": [
                    r"\b(?:wo|me|nye|le|nyuie|nyo|kɔ)\s+(?:paa|kɛse)\b"
                ],
                "question": [
                    r"\b(?:wo|me|nye|le|nyuie|nyo|kɔ)\s*\?\b"
                ],
                "request": [
                    r"\b(?:wo|me|nye|le|nyuie|nyo|kɔ)\s+(?:paa|kɛse)\b"
                ],
                "complaint": [
                    r"\b(?:nye|le|wo)\s+(?:nyuie|nyo|kɔ)\b"
                ],
                "thanks": [
                    r"\b(?:wo|me|nye|le|nyuie|nyo|kɔ)\s+(?:paa|kɛse)\b"
                ]
            },
            "ga": {
                "greeting": [
                    r"\b(?:mi|wo|ye|le|ŋɔ|ŋɔɔ|kɛ)\b",
                    r"\b(?:ŋɔ|ŋɔɔ|kɛ|le|ye|mi|wo)\s+(?:ŋɔ|ŋɔɔ|kɛ)\b"
                ],
                "farewell": [
                    r"\b(?:mi|wo|ye|le|ŋɔ|ŋɔɔ|kɛ)\s+(?:paa|kɛse)\b"
                ],
                "question": [
                    r"\b(?:mi|wo|ye|le|ŋɔ|ŋɔɔ|kɛ)\s*\?\b"
                ],
                "request": [
                    r"\b(?:mi|wo|ye|le|ŋɔ|ŋɔɔ|kɛ)\s+(?:paa|kɛse)\b"
                ],
                "complaint": [
                    r"\b(?:le|ye|mi|wo)\s+(?:ŋɔ|ŋɔɔ|kɛ)\b"
                ],
                "thanks": [
                    r"\b(?:mi|wo|ye|le|ŋɔ|ŋɔɔ|kɛ)\s+(?:paa|kɛse)\b"
                ]
            },
            "dag": {
                "greeting": [
                    r"\b(?:ka|ya|la|ŋɔ|ŋɔɔ|kɛ|damba|yili)\b",
                    r"\b(?:damba|yili|ka|ya|la|ŋɔ|ŋɔɔ|kɛ)\s+(?:damba|yili|ka|ya|la|ŋɔ|ŋɔɔ|kɛ)\b"
                ],
                "farewell": [
                    r"\b(?:ka|ya|la|ŋɔ|ŋɔɔ|kɛ|damba|yili)\s+(?:paa|kɛse)\b"
                ],
                "question": [
                    r"\b(?:ka|ya|la|ŋɔ|ŋɔɔ|kɛ|damba|yili)\s*\?\b"
                ],
                "request": [
                    r"\b(?:ka|ya|la|ŋɔ|ŋɔɔ|kɛ|damba|yili)\s+(?:paa|kɛse)\b"
                ],
                "complaint": [
                    r"\b(?:la|ya|ka)\s+(?:damba|yili|ka|ya|la|ŋɔ|ŋɔɔ|kɛ)\b"
                ],
                "thanks": [
                    r"\b(?:ka|ya|la|ŋɔ|ŋɔɔ|kɛ|damba|yili)\s+(?:paa|kɛse)\b"
                ]
            }
        }
        
        # Domain-specific patterns
        self._domain_patterns = {
            "business": [
                "money", "payment", "price", "cost", "business", "work", "job",
                "cedi", "cedis", "GHS", "GH₵", "bank", "account", "transaction"
            ],
            "medical": [
                "sick", "ill", "pain", "doctor", "hospital", "medicine", "treatment",
                "health", "medical", "clinic", "pharmacy", "drug", "medicine"
            ],
            "financial": [
                "money", "bank", "account", "loan", "credit", "debit", "transfer",
                "payment", "withdrawal", "deposit", "balance", "statement"
            ],
            "educational": [
                "school", "university", "college", "student", "teacher", "class",
                "study", "learn", "education", "course", "exam", "test"
            ],
            "social": [
                "family", "friend", "home", "house", "marriage", "wedding",
                "party", "celebration", "visit", "meet", "talk", "chat"
            ],
            "cultural": [
                "chief", "nana", "ohene", "obaa", "tradition", "custom", "culture",
                "festival", "ceremony", "ritual", "ancestor", "spirit"
            ]
        }
        
        # Cultural context patterns
        self._cultural_patterns = {
            "respect_indicators": [
                "ɛfie", "ɛna", "ɛba", "ɛyɛ", "ɛnyɛ",  # Twi respect markers
                "oga", "madam", "sir", "ma", "pa",    # Ghana Pidgin respect
                "wo", "me", "nye", "le", "nyuie"      # Ewe respect markers
            ],
            "formality_indicators": [
                "ɛyɛ", "ɛnyɛ", "ɛfie", "ɛna",        # Twi formal markers
                "make you", "dey", "fit", "chop",     # Ghana Pidgin formal
                "wo", "me", "nye", "le"              # Ewe formal markers
            ]
        }
        
        logger.info("GhanaianIntentDetector initialized with cultural context awareness")
    
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
    
    async def detect_intent(
        self, 
        text: str, 
        language: str = "auto",
        context: Optional[Dict[str, any]] = None
    ) -> IntentResult:
        """
        Detect intent from text in Ghanaian languages
        
        Args:
            text: Text to analyze
            language: Language code (tw, en-GH, ee, ga, dag) or "auto" for detection
            context: Additional context for analysis
            
        Returns:
            IntentResult with detected intent
        """
        if not text.strip():
            return self._create_unknown_result(language or "auto")
        
        # Check cache first
        cache_key = f"{text.lower()}:{language}:{hash(str(context))}"
        if self.config.cache_results and cache_key in self._cache:
            cached_result = self._cache[cache_key]
            cache_age = (datetime.utcnow() - self._cache_timestamps[cache_key]).total_seconds()
            if cache_age < self.config.cache_ttl:
                logger.debug(f"Returning cached intent result for: {text[:50]}...")
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
            logger.error(f"Error detecting intent: {e}")
            return self._create_unknown_result(language)
    
    async def detect_intent_batch(
        self, 
        texts: List[str], 
        language: str = "auto"
    ) -> List[IntentResult]:
        """
        Detect intent from multiple texts in batch
        
        Args:
            texts: List of texts to analyze
            language: Language code or "auto" for detection
            
        Returns:
            List of IntentResult objects
        """
        if not texts:
            return []
        
        # Process in batches
        results = []
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i:i + self.config.batch_size]
            batch_results = await asyncio.gather(
                *[self.detect_intent(text, language) for text in batch],
                return_exceptions=True
            )
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch intent detection error: {result}")
                    results.append(self._create_unknown_result(language))
                else:
                    results.append(result)
        
        return results
    
    async def _perform_analysis(
        self, 
        text: str, 
        language: str, 
        context: Dict[str, any]
    ) -> IntentResult:
        """Perform the actual intent detection"""
        
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
    ) -> IntentResult:
        """Perform analysis using external API"""
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "language": language,
            "features": ["intent", "domain"],
            "context": context
        }
        
        async with self.session.post(
            f"{self.config.base_url}/intent/detect",
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
    ) -> IntentResult:
        """Perform pattern-based intent detection"""
        
        text_lower = text.lower()
        patterns = self._intent_patterns.get(language, self._intent_patterns["tw"])
        
        # Calculate intent scores
        intent_scores = {}
        for intent_type, pattern_list in patterns.items():
            score = 0
            for pattern in pattern_list:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                score += len(matches) * 0.3
            
            if score > 0:
                intent_scores[IntentType(intent_type)] = min(1.0, score)
        
        # Determine primary intent
        if intent_scores:
            primary_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
            confidence = intent_scores[primary_intent]
        else:
            primary_intent = IntentType.UNKNOWN
            confidence = 0.0
        
        # Detect domain
        domain = self._detect_domain(text_lower)
        
        # Get alternative intents
        alternative_intents = [
            (intent, score) for intent, score in intent_scores.items()
            if intent != primary_intent and score > 0.1
        ]
        alternative_intents.sort(key=lambda x: x[1], reverse=True)
        
        # Cultural context analysis
        cultural_notes = self._analyze_cultural_context(text_lower, language)
        
        return IntentResult(
            primary_intent=primary_intent,
            confidence=confidence,
            domain=domain,
            language=language,
            timestamp=datetime.utcnow(),
            context=context,
            alternative_intents=alternative_intents,
            cultural_notes=cultural_notes
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
    
    def _detect_domain(self, text: str) -> DomainType:
        """Detect the domain of the text"""
        
        domain_scores = {}
        for domain, keywords in self._domain_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                domain_scores[DomainType(domain)] = score
        
        if domain_scores:
            return max(domain_scores.items(), key=lambda x: x[1])[0]
        else:
            return DomainType.GENERAL
    
    def _analyze_cultural_context(self, text: str, language: str) -> List[str]:
        """Analyze cultural context and provide notes"""
        
        notes = []
        
        # Check for respect indicators
        respect_count = sum(1 for indicator in self._cultural_patterns["respect_indicators"] 
                           if indicator in text)
        if respect_count > 0:
            notes.append(f"Contains {respect_count} respect indicators")
        
        # Check for formality indicators
        formality_count = sum(1 for indicator in self._cultural_patterns["formality_indicators"] 
                             if indicator in text)
        if formality_count > 0:
            notes.append(f"Contains {formality_count} formality indicators")
        
        # Language-specific cultural notes
        if language == "tw":
            if "ɛfie" in text:
                notes.append("Uses formal Twi address (ɛfie)")
            if "ɛna" in text:
                notes.append("Uses respectful address (ɛna)")
        elif language == "en-GH":
            if "oga" in text:
                notes.append("Uses respectful Ghana Pidgin address (oga)")
            if "madam" in text or "sir" in text:
                notes.append("Uses formal English address")
        
        return notes
    
    def _parse_api_response(
        self, 
        data: Dict[str, any], 
        language: str, 
        context: Dict[str, any]
    ) -> IntentResult:
        """Parse API response into IntentResult"""
        
        primary_intent = IntentType(data.get("primary_intent", "unknown"))
        confidence = data.get("confidence", 0.0)
        domain = DomainType(data.get("domain", "general"))
        
        alternative_intents = []
        for alt_intent_data in data.get("alternative_intents", []):
            intent_type = IntentType(alt_intent_data.get("intent", "unknown"))
            score = alt_intent_data.get("confidence", 0.0)
            alternative_intents.append((intent_type, score))
        
        return IntentResult(
            primary_intent=primary_intent,
            confidence=confidence,
            domain=domain,
            language=language,
            timestamp=datetime.utcnow(),
            context=context,
            alternative_intents=alternative_intents,
            cultural_notes=data.get("cultural_notes", [])
        )
    
    def _create_unknown_result(self, language: str) -> IntentResult:
        """Create an unknown intent result"""
        
        return IntentResult(
            primary_intent=IntentType.UNKNOWN,
            confidence=0.0,
            domain=DomainType.GENERAL,
            language=language,
            timestamp=datetime.utcnow(),
            context={},
            alternative_intents=[],
            cultural_notes=[]
        )
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return list(self._intent_patterns.keys())
    
    def get_supported_intents(self) -> List[str]:
        """Get list of supported intent types"""
        return [intent_type.value for intent_type in IntentType]
    
    def get_supported_domains(self) -> List[str]:
        """Get list of supported domain types"""
        return [domain_type.value for domain_type in DomainType]
    
    def get_analysis_features(self) -> Dict[str, bool]:
        """Get available analysis features"""
        return {
            "intent_detection": True,
            "domain_detection": self.config.enable_domain_detection,
            "cultural_context": self.config.enable_cultural_context,
            "language_detection": True,
            "batch_processing": True
        }
    
    def clear_cache(self):
        """Clear the analysis cache"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Intent detection cache cleared")
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self._cache),
            "cache_enabled": self.config.cache_results,
            "cache_ttl": self.config.cache_ttl,
            "oldest_entry": min(self._cache_timestamps.values()) if self._cache_timestamps else None,
            "newest_entry": max(self._cache_timestamps.values()) if self._cache_timestamps else None
        }
