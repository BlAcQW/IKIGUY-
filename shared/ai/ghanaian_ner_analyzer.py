"""
Ghanaian Language Named Entity Recognition (NER) Module

This module provides advanced Named Entity Recognition capabilities specifically designed
for Ghanaian languages including Twi, Ghana Pidgin, Ewe, Ga, and Dagbani.

Features:
- Multi-language NER for Ghanaian languages
- Entity types: PERSON, LOCATION, ORGANIZATION, CURRENCY, DATE, TIME
- Cultural context awareness
- Ghana-specific entity patterns
- Confidence scoring
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


class EntityType(Enum):
    """Named entity types"""
    PERSON = "PERSON"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"
    CURRENCY = "CURRENCY"
    DATE = "DATE"
    TIME = "TIME"
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    UNKNOWN = "UNKNOWN"


@dataclass
class Entity:
    """Named entity found in text"""
    text: str
    entity_type: EntityType
    start_pos: int
    end_pos: int
    confidence: float
    language: str
    metadata: Dict[str, any]


@dataclass
class NERResult:
    """Result of NER analysis"""
    entities: List[Entity]
    text: str
    language: str
    timestamp: datetime
    confidence: float
    context: Dict[str, any]


class GhanaianNERConfig(BaseModel):
    """Configuration for Ghanaian NER analysis"""
    api_key: str = Field(..., description="API key for NER service")
    base_url: str = Field(default="https://api.abena.ai/v1", description="Base URL for API")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence threshold")
    
    # Language-specific settings
    enable_cultural_context: bool = Field(default=True, description="Enable cultural context analysis")
    enable_ghana_specific_entities: bool = Field(default=True, description="Enable Ghana-specific entity detection")
    
    # Performance settings
    cache_results: bool = Field(default=True, description="Cache analysis results")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    batch_size: int = Field(default=10, description="Batch size for bulk analysis")


class GhanaianNERAnalyzer:
    """
    Advanced NER analyzer for Ghanaian languages
    
    Provides comprehensive Named Entity Recognition with cultural context awareness
    and Ghana-specific entity patterns for Ghanaian languages.
    """
    
    def __init__(self, config: GhanaianNERConfig):
        """
        Initialize the NER analyzer
        
        Args:
            config: Configuration for the NER analyzer
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, NERResult] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # Ghana-specific entity patterns
        self._entity_patterns = {
            "tw": {
                "PERSON": [
                    r"\b(?:Nana|Ohene|Obaa|Akwasi|Kwame|Kwesi|Kofi|Kwaku|Yaw|Kwabena|Kwadwo|Kwaku|Yaa|Abena|Akua|Adwoa|Akosua|Ama|Efua|Esi)\b",
                    r"\b(?:ɛfie|ɛna|ɛba|ɛyɛ|ɛnyɛ)\s+[A-Z][a-z]+\b"
                ],
                "LOCATION": [
                    r"\b(?:Kumasi|Accra|Tamale|Sekondi|Cape Coast|Tema|Ashanti|Greater Accra|Northern|Western|Eastern|Central|Upper East|Upper West|Volta|Bono|Ahafo|Savannah|North East|Oti|Western North)\b",
                    r"\b(?:ɛfie|ɛna|ɛba|ɛyɛ|ɛnyɛ)\s+(?:Kumasi|Accra|Tamale)\b"
                ],
                "ORGANIZATION": [
                    r"\b(?:Ghana|Ghanaian|ɛfie|ɛna|ɛba|ɛyɛ|ɛnyɛ)\s+(?:Government|Bank|University|Hospital|School|Company|Corporation)\b"
                ],
                "CURRENCY": [
                    r"\b(?:cedi|cedis|GHS|GH₵)\b",
                    r"\b\d+\s+(?:cedi|cedis)\b"
                ],
                "PHONE": [
                    r"\b(?:\+233|233)\s*\d{9}\b",
                    r"\b0\d{9}\b"
                ]
            },
            "en-GH": {
                "PERSON": [
                    r"\b(?:Nana|Ohene|Obaa|Akwasi|Kwame|Kwesi|Kofi|Kwaku|Yaw|Kwabena|Kwadwo|Kwaku|Yaa|Abena|Akua|Adwoa|Akosua|Ama|Efua|Esi)\b",
                    r"\b(?:Mr\.|Mrs\.|Miss|Dr\.|Prof\.|Chief|Nana|Ohene)\s+[A-Z][a-z]+\b"
                ],
                "LOCATION": [
                    r"\b(?:Kumasi|Accra|Tamale|Sekondi|Cape Coast|Tema|Ashanti|Greater Accra|Northern|Western|Eastern|Central|Upper East|Upper West|Volta|Bono|Ahafo|Savannah|North East|Oti|Western North)\b",
                    r"\b(?:in|at|to|from)\s+(?:Kumasi|Accra|Tamale)\b"
                ],
                "ORGANIZATION": [
                    r"\b(?:Ghana|Ghanaian)\s+(?:Government|Bank|University|Hospital|School|Company|Corporation)\b",
                    r"\b(?:Bank of Ghana|Ghana Revenue Authority|Ghana Police Service|Ghana Armed Forces)\b"
                ],
                "CURRENCY": [
                    r"\b(?:cedi|cedis|GHS|GH₵)\b",
                    r"\b\d+\s+(?:cedi|cedis)\b"
                ],
                "PHONE": [
                    r"\b(?:\+233|233)\s*\d{9}\b",
                    r"\b0\d{9}\b"
                ]
            },
            "ee": {
                "PERSON": [
                    r"\b(?:wo|me|nye|le|nyuie|nyo|kɔ)\s+[A-Z][a-z]+\b"
                ],
                "LOCATION": [
                    r"\b(?:Kumasi|Accra|Tamale|Sekondi|Cape Coast|Tema)\b",
                    r"\b(?:wo|me|nye|le|nyuie|nyo|kɔ)\s+(?:Kumasi|Accra|Tamale)\b"
                ],
                "ORGANIZATION": [
                    r"\b(?:wo|me|nye|le|nyuie|nyo|kɔ)\s+(?:Government|Bank|University|Hospital|School)\b"
                ],
                "CURRENCY": [
                    r"\b(?:cedi|cedis|GHS|GH₵)\b",
                    r"\b\d+\s+(?:cedi|cedis)\b"
                ],
                "PHONE": [
                    r"\b(?:\+233|233)\s*\d{9}\b",
                    r"\b0\d{9}\b"
                ]
            },
            "ga": {
                "PERSON": [
                    r"\b(?:mi|wo|ye|le|ŋɔ|ŋɔɔ|kɛ)\s+[A-Z][a-z]+\b"
                ],
                "LOCATION": [
                    r"\b(?:Kumasi|Accra|Tamale|Sekondi|Cape Coast|Tema)\b",
                    r"\b(?:mi|wo|ye|le|ŋɔ|ŋɔɔ|kɛ)\s+(?:Kumasi|Accra|Tamale)\b"
                ],
                "ORGANIZATION": [
                    r"\b(?:mi|wo|ye|le|ŋɔ|ŋɔɔ|kɛ)\s+(?:Government|Bank|University|Hospital|School)\b"
                ],
                "CURRENCY": [
                    r"\b(?:cedi|cedis|GHS|GH₵)\b",
                    r"\b\d+\s+(?:cedi|cedis)\b"
                ],
                "PHONE": [
                    r"\b(?:\+233|233)\s*\d{9}\b",
                    r"\b0\d{9}\b"
                ]
            },
            "dag": {
                "PERSON": [
                    r"\b(?:ka|ya|la|ŋɔ|ŋɔɔ|kɛ|damba|yili)\s+[A-Z][a-z]+\b"
                ],
                "LOCATION": [
                    r"\b(?:Kumasi|Accra|Tamale|Sekondi|Cape Coast|Tema)\b",
                    r"\b(?:ka|ya|la|ŋɔ|ŋɔɔ|kɛ|damba|yili)\s+(?:Kumasi|Accra|Tamale)\b"
                ],
                "ORGANIZATION": [
                    r"\b(?:ka|ya|la|ŋɔ|ŋɔɔ|kɛ|damba|yili)\s+(?:Government|Bank|University|Hospital|School)\b"
                ],
                "CURRENCY": [
                    r"\b(?:cedi|cedis|GHS|GH₵)\b",
                    r"\b\d+\s+(?:cedi|cedis)\b"
                ],
                "PHONE": [
                    r"\b(?:\+233|233)\s*\d{9}\b",
                    r"\b0\d{9}\b"
                ]
            }
        }
        
        # Ghana-specific cultural patterns
        self._cultural_patterns = {
            "titles": [
                "Nana", "Ohene", "Obaa", "Chief", "Queen Mother", "King",
                "Mr.", "Mrs.", "Miss", "Dr.", "Prof.", "Reverend", "Pastor"
            ],
            "regions": [
                "Ashanti", "Greater Accra", "Northern", "Western", "Eastern",
                "Central", "Upper East", "Upper West", "Volta", "Bono", "Ahafo",
                "Savannah", "North East", "Oti", "Western North"
            ],
            "cities": [
                "Kumasi", "Accra", "Tamale", "Sekondi", "Cape Coast", "Tema",
                "Koforidua", "Sunyani", "Ho", "Bolgatanga", "Wa", "Damongo"
            ],
            "organizations": [
                "Bank of Ghana", "Ghana Revenue Authority", "Ghana Police Service",
                "Ghana Armed Forces", "Ghana Education Service", "Ghana Health Service"
            ]
        }
        
        logger.info("GhanaianNERAnalyzer initialized with cultural context awareness")
    
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
    
    async def extract_entities(
        self, 
        text: str, 
        language: str = "auto",
        context: Optional[Dict[str, any]] = None
    ) -> NERResult:
        """
        Extract named entities from text in Ghanaian languages
        
        Args:
            text: Text to analyze
            language: Language code (tw, en-GH, ee, ga, dag) or "auto" for detection
            context: Additional context for analysis
            
        Returns:
            NERResult with extracted entities
        """
        if not text.strip():
            return self._create_empty_result(language or "auto")
        
        # Check cache first
        cache_key = f"{text.lower()}:{language}:{hash(str(context))}"
        if self.config.cache_results and cache_key in self._cache:
            cached_result = self._cache[cache_key]
            cache_age = (datetime.utcnow() - self._cache_timestamps[cache_key]).total_seconds()
            if cache_age < self.config.cache_ttl:
                logger.debug(f"Returning cached NER result for: {text[:50]}...")
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
            logger.error(f"Error extracting entities: {e}")
            return self._create_empty_result(language)
    
    async def extract_entities_batch(
        self, 
        texts: List[str], 
        language: str = "auto"
    ) -> List[NERResult]:
        """
        Extract entities from multiple texts in batch
        
        Args:
            texts: List of texts to analyze
            language: Language code or "auto" for detection
            
        Returns:
            List of NERResult objects
        """
        if not texts:
            return []
        
        # Process in batches
        results = []
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i:i + self.config.batch_size]
            batch_results = await asyncio.gather(
                *[self.extract_entities(text, language) for text in batch],
                return_exceptions=True
            )
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch NER error: {result}")
                    results.append(self._create_empty_result(language))
                else:
                    results.append(result)
        
        return results
    
    async def _perform_analysis(
        self, 
        text: str, 
        language: str, 
        context: Dict[str, any]
    ) -> NERResult:
        """Perform the actual NER analysis"""
        
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
    ) -> NERResult:
        """Perform analysis using external API"""
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "language": language,
            "features": ["ner", "entities"],
            "context": context
        }
        
        async with self.session.post(
            f"{self.config.base_url}/ner/extract",
            headers=headers,
            json=payload
        ) as response:
            if response.status == 200:
                data = await response.json()
                return self._parse_api_response(data, text, language, context)
            else:
                raise Exception(f"API request failed: {response.status}")
    
    async def _pattern_based_analysis(
        self, 
        text: str, 
        language: str, 
        context: Dict[str, any]
    ) -> NERResult:
        """Perform pattern-based NER analysis"""
        
        entities = []
        patterns = self._entity_patterns.get(language, self._entity_patterns["tw"])
        
        # Extract entities using patterns
        for entity_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity = Entity(
                        text=match.group(),
                        entity_type=EntityType(entity_type),
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=self._calculate_confidence(match.group(), entity_type, language),
                        language=language,
                        metadata=self._extract_metadata(match.group(), entity_type, language)
                    )
                    entities.append(entity)
        
        # Remove overlapping entities (keep the one with higher confidence)
        entities = self._remove_overlapping_entities(entities)
        
        # Calculate overall confidence
        overall_confidence = sum(entity.confidence for entity in entities) / max(len(entities), 1)
        
        return NERResult(
            entities=entities,
            text=text,
            language=language,
            timestamp=datetime.utcnow(),
            confidence=overall_confidence,
            context=context
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
    
    def _calculate_confidence(self, entity_text: str, entity_type: str, language: str) -> float:
        """Calculate confidence score for an entity"""
        
        base_confidence = 0.7
        
        # Boost confidence for Ghana-specific entities
        if entity_type == "PERSON":
            if any(title in entity_text for title in self._cultural_patterns["titles"]):
                base_confidence += 0.2
        elif entity_type == "LOCATION":
            if any(city in entity_text for city in self._cultural_patterns["cities"]):
                base_confidence += 0.2
            if any(region in entity_text for region in self._cultural_patterns["regions"]):
                base_confidence += 0.15
        elif entity_type == "ORGANIZATION":
            if any(org in entity_text for org in self._cultural_patterns["organizations"]):
                base_confidence += 0.2
        
        # Boost confidence for proper capitalization
        if entity_text[0].isupper():
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _extract_metadata(self, entity_text: str, entity_type: str, language: str) -> Dict[str, any]:
        """Extract metadata for an entity"""
        
        metadata = {
            "entity_type": entity_type,
            "language": language,
            "length": len(entity_text)
        }
        
        if entity_type == "PERSON":
            metadata["title"] = self._extract_title(entity_text)
            metadata["is_ghanaian_name"] = self._is_ghanaian_name(entity_text)
        elif entity_type == "LOCATION":
            metadata["is_city"] = entity_text in self._cultural_patterns["cities"]
            metadata["is_region"] = entity_text in self._cultural_patterns["regions"]
        elif entity_type == "CURRENCY":
            metadata["currency_code"] = "GHS"
            metadata["currency_name"] = "Ghanaian Cedi"
        elif entity_type == "PHONE":
            metadata["country_code"] = "+233"
            metadata["is_mobile"] = entity_text.startswith("0") or "+233" in entity_text
        
        return metadata
    
    def _extract_title(self, entity_text: str) -> Optional[str]:
        """Extract title from person entity"""
        
        for title in self._cultural_patterns["titles"]:
            if entity_text.startswith(title):
                return title
        
        return None
    
    def _is_ghanaian_name(self, entity_text: str) -> bool:
        """Check if entity is a Ghanaian name"""
        
        ghanaian_names = [
            "Akwasi", "Kwame", "Kwesi", "Kofi", "Kwaku", "Yaw", "Kwabena", "Kwadwo",
            "Yaa", "Abena", "Akua", "Adwoa", "Akosua", "Ama", "Efua", "Esi"
        ]
        
        return any(name in entity_text for name in ghanaian_names)
    
    def _remove_overlapping_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove overlapping entities, keeping the one with higher confidence"""
        
        if not entities:
            return entities
        
        # Sort by confidence (descending) and start position
        entities.sort(key=lambda x: (-x.confidence, x.start_pos))
        
        filtered_entities = []
        for entity in entities:
            # Check if this entity overlaps with any already accepted entity
            overlaps = False
            for accepted in filtered_entities:
                if (entity.start_pos < accepted.end_pos and 
                    entity.end_pos > accepted.start_pos):
                    overlaps = True
                    break
            
            if not overlaps:
                filtered_entities.append(entity)
        
        # Sort by start position for final order
        filtered_entities.sort(key=lambda x: x.start_pos)
        return filtered_entities
    
    def _parse_api_response(
        self, 
        data: Dict[str, any], 
        text: str, 
        language: str, 
        context: Dict[str, any]
    ) -> NERResult:
        """Parse API response into NERResult"""
        
        entities = []
        for entity_data in data.get("entities", []):
            entity = Entity(
                text=entity_data.get("text", ""),
                entity_type=EntityType(entity_data.get("type", "UNKNOWN")),
                start_pos=entity_data.get("start", 0),
                end_pos=entity_data.get("end", 0),
                confidence=entity_data.get("confidence", 0.5),
                language=language,
                metadata=entity_data.get("metadata", {})
            )
            entities.append(entity)
        
        return NERResult(
            entities=entities,
            text=text,
            language=language,
            timestamp=datetime.utcnow(),
            confidence=data.get("confidence", 0.5),
            context=context
        )
    
    def _create_empty_result(self, language: str) -> NERResult:
        """Create an empty NER result"""
        
        return NERResult(
            entities=[],
            text="",
            language=language,
            timestamp=datetime.utcnow(),
            confidence=0.0,
            context={}
        )
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return list(self._entity_patterns.keys())
    
    def get_supported_entity_types(self) -> List[str]:
        """Get list of supported entity types"""
        return [entity_type.value for entity_type in EntityType]
    
    def get_analysis_features(self) -> Dict[str, bool]:
        """Get available analysis features"""
        return {
            "ner_analysis": True,
            "cultural_context": self.config.enable_cultural_context,
            "ghana_specific_entities": self.config.enable_ghana_specific_entities,
            "language_detection": True,
            "batch_processing": True
        }
    
    def clear_cache(self):
        """Clear the analysis cache"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("NER analysis cache cleared")
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self._cache),
            "cache_enabled": self.config.cache_results,
            "cache_ttl": self.config.cache_ttl,
            "oldest_entry": min(self._cache_timestamps.values()) if self._cache_timestamps else None,
            "newest_entry": max(self._cache_timestamps.values()) if self._cache_timestamps else None
        }
