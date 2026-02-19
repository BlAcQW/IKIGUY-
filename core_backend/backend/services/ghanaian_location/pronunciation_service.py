"""
Pronunciation Service for Ghanaian Location Names

Optimizes TTS output for clear pronunciation of Ghanaian place names
using SSML markup, phonetic guidance, and context-aware speech adjustments.
"""

import logging
from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass

from .database.models import GhanaianLocation, PronunciationGuide, LanguageContext
from .database.repositories import LocationRepository

logger = logging.getLogger(__name__)


@dataclass
class PronunciationResult:
    """Result from pronunciation processing"""
    original_text: str
    optimized_text: str
    ssml_markup: Optional[str] = None
    phonetic_spelling: Optional[str] = None
    speech_rate: float = 1.0
    difficulty_score: float = 0.5
    alternatives: List[str] = None


class PronunciationService:
    """
    Service for optimizing TTS pronunciation of Ghanaian location names

    Provides:
    - SSML markup generation for clear pronunciation
    - Phonetic spelling alternatives
    - Speech rate optimization for difficult names
    - Context-aware pronunciation adjustments
    - Alternative descriptions for very difficult names
    """

    def __init__(self, repository: LocationRepository):
        self.repository = repository

        # Pronunciation difficulty patterns (0.0 = easy, 1.0 = very difficult)
        self.difficulty_patterns = {
            # Very difficult sounds for English TTS
            r'DZ': 0.9,      # Dzorwulu
            r'NY': 0.8,      # Nyamekye
            r'KW': 0.7,      # Kwabenya
            r'GB': 0.9,      # Gbegbeyise
            r'TSH': 0.8,     # Some Ewe names
            r'NG': 0.6,      # Ngleshie

            # Moderately difficult
            r'KO.*LE': 0.7,  # Kokomlemle
            r'MA.*BI': 0.6,  # Maamobi
            r'A.*BRA': 0.5,  # Adabraka

            # Length-based difficulty
            r'.{12,}': 0.7,  # Very long names
            r'.{10,11}': 0.6, # Long names
            r'.{8,9}': 0.4,  # Medium names
        }

        # SSML phoneme mappings for common Ghanaian sounds
        self.ssml_phonemes = {
            'DZ': '<phoneme alphabet="ipa" ph="d͡z">DZ</phoneme>',
            'NY': '<phoneme alphabet="ipa" ph="nj">NY</phoneme>',
            'KW': '<phoneme alphabet="ipa" ph="kw">KW</phoneme>',
            'NG': '<phoneme alphabet="ipa" ph="ŋ">NG</phoneme>',

            # Specific location phonemes
            'DZORWULU': '<phoneme alphabet="ipa" ph="d͡zoɾwulu">Dzorwulu</phoneme>',
            'KOKOMLEMLE': '<phoneme alphabet="ipa" ph="kokomlɛmle">Kokomlemle</phoneme>',
            'NYAMEKYE': '<phoneme alphabet="ipa" ph="njamɛkje">Nyamekye</phoneme>',
            'MAAMOBI': '<phoneme alphabet="ipa" ph="maːmobi">Maamobi</phoneme>',
        }

        # Speech rate adjustments based on difficulty
        self.speech_rates = {
            0.9: 0.7,   # Very difficult -> 70% speed
            0.8: 0.8,   # Difficult -> 80% speed
            0.7: 0.85,  # Moderately difficult -> 85% speed
            0.6: 0.9,   # Somewhat difficult -> 90% speed
            0.5: 0.95,  # Slightly difficult -> 95% speed
        }

        # Alternative descriptions for very difficult names
        self.location_descriptions = {
            'DZORWULU': ['the Dzorwulu area', 'near Roman Ridge', 'Zor-wu-lu area'],
            'KOKOMLEMLE': ['the Kokomlemle area', 'Koko-lemle area', 'near Achimota'],
            'NYAMEKYE': ['the Nyamekye area', 'Nia-mek-ye area', 'near Lapaz'],
            'MAAMOBI': ['the Maamobi area', 'Ma-mo-bi area', 'near Nima'],
            'ABELENKPE': ['the Abelenkpe area', 'Abel-en-kpe area', 'near Dzorwulu'],
        }

        # Syllable break patterns for difficult names
        self.syllable_patterns = {
            'DZORWULU': ['Dzor', 'wu', 'lu'],
            'KOKOMLEMLE': ['Ko', 'kom', 'lem', 'le'],
            'NYAMEKYE': ['Nya', 'me', 'kye'],
            'MAAMOBI': ['Maa', 'mo', 'bi'],
            'ABELENKPE': ['Abel', 'en', 'kpe'],
            'ADABRAKA': ['Ada', 'bra', 'ka'],
            'KWABENYA': ['Kwa', 'ben', 'ya'],
        }

    async def optimize_for_tts(self, location_name: str, context: str = 'general',
                              language: LanguageContext = LanguageContext.ENGLISH) -> PronunciationResult:
        """
        Optimize location name for TTS pronunciation

        Args:
            location_name: The location name to optimize
            context: Context for pronunciation (healthcare, general, etc.)
            language: Target language for TTS

        Returns:
            PronunciationResult with optimized pronunciation
        """
        try:
            # Get existing pronunciation guide from database
            guide = await self.repository.get_pronunciation_guide(location_name, language)

            if guide:
                # Use existing guide
                return PronunciationResult(
                    original_text=location_name,
                    optimized_text=guide.alternative_descriptions[0] if guide.alternative_descriptions else location_name,
                    ssml_markup=guide.ssml_markup,
                    phonetic_spelling=guide.phonetic_spelling,
                    speech_rate=guide.recommended_speech_rate,
                    difficulty_score=guide.difficulty_score,
                    alternatives=guide.alternative_descriptions
                )
            else:
                # Generate pronunciation optimization
                return await self._generate_pronunciation(location_name, context, language)

        except Exception as e:
            logger.error(f"Failed to optimize pronunciation for '{location_name}': {e}")
            return PronunciationResult(
                original_text=location_name,
                optimized_text=location_name,
                difficulty_score=0.5
            )

    async def _generate_pronunciation(self, location_name: str, context: str,
                                    language: LanguageContext) -> PronunciationResult:
        """Generate pronunciation optimization for a location name"""

        # Calculate difficulty score
        difficulty = self._calculate_difficulty_score(location_name)

        # Generate SSML markup
        ssml_markup = self._generate_ssml(location_name, difficulty)

        # Generate phonetic spelling
        phonetic_spelling = self._generate_phonetic_spelling(location_name)

        # Determine optimal speech rate
        speech_rate = self._get_optimal_speech_rate(difficulty)

        # Generate alternative descriptions
        alternatives = self._generate_alternatives(location_name, context)

        # Choose optimized text based on difficulty
        if difficulty > 0.8:
            # Very difficult - use alternative description
            optimized_text = alternatives[0] if alternatives else phonetic_spelling or location_name
        elif difficulty > 0.6:
            # Difficult - use phonetic spelling
            optimized_text = phonetic_spelling or location_name
        else:
            # Manageable - use original with possible breaks
            optimized_text = self._add_pronunciation_breaks(location_name)

        return PronunciationResult(
            original_text=location_name,
            optimized_text=optimized_text,
            ssml_markup=ssml_markup,
            phonetic_spelling=phonetic_spelling,
            speech_rate=speech_rate,
            difficulty_score=difficulty,
            alternatives=alternatives
        )

    def _calculate_difficulty_score(self, location_name: str) -> float:
        """Calculate pronunciation difficulty score for a location name"""
        name_upper = location_name.upper()
        max_score = 0.0

        for pattern, score in self.difficulty_patterns.items():
            if re.search(pattern, name_upper):
                max_score = max(max_score, score)

        # Additional factors
        # Vowel clusters increase difficulty
        vowel_clusters = len(re.findall(r'[AEIOU]{2,}', name_upper))
        max_score += vowel_clusters * 0.1

        # Consonant clusters increase difficulty
        consonant_clusters = len(re.findall(r'[BCDFGHJKLMNPQRSTVWXYZ]{3,}', name_upper))
        max_score += consonant_clusters * 0.15

        return min(1.0, max_score)

    def _generate_ssml(self, location_name: str, difficulty: float) -> str:
        """Generate SSML markup for pronunciation"""
        name_upper = location_name.upper()

        # Check for direct phoneme mapping
        if name_upper in self.ssml_phonemes:
            return self.ssml_phonemes[name_upper]

        # Check for partial phoneme patterns
        ssml_text = location_name
        for pattern, phoneme in self.ssml_phonemes.items():
            if pattern in name_upper and len(pattern) <= 3:  # Only replace short patterns
                ssml_text = ssml_text.replace(pattern.title(), phoneme)

        # Add prosody control for difficult names
        if difficulty > 0.7:
            speech_rate = self._get_optimal_speech_rate(difficulty)
            ssml_text = f'<prosody rate="{speech_rate:.1f}">{ssml_text}</prosody>'

        # Add pauses for very difficult names
        if difficulty > 0.8:
            syllables = self._get_syllable_breaks(name_upper)
            if syllables and len(syllables) > 1:
                ssml_text = '<break time="0.2s"/>'.join(syllables)
                ssml_text = f'<prosody rate="0.8">{ssml_text}</prosody>'

        return f'<speak>{ssml_text}</speak>'

    def _generate_phonetic_spelling(self, location_name: str) -> Optional[str]:
        """Generate human-readable phonetic spelling"""
        name_upper = location_name.upper()

        # Check for pre-defined phonetic spellings
        phonetic_mappings = {
            'DZORWULU': 'ZOR-wu-lu',
            'KOKOMLEMLE': 'KO-kom-lem-le',
            'NYAMEKYE': 'NYA-me-kye',
            'MAAMOBI': 'MA-mo-bi',
            'ABELENKPE': 'A-bel-en-kpe',
            'ADABRAKA': 'A-da-bra-ka',
            'KWABENYA': 'KWA-ben-ya',
            'ASYLUM DOWN': 'A-sy-lum Down',
        }

        if name_upper in phonetic_mappings:
            return phonetic_mappings[name_upper]

        # Generate phonetic spelling based on syllable patterns
        syllables = self._get_syllable_breaks(name_upper)
        if syllables and len(syllables) > 1:
            return '-'.join(syllables)

        return None

    def _get_syllable_breaks(self, location_name: str) -> List[str]:
        """Get syllable breaks for a location name"""
        name_upper = location_name.upper()

        if name_upper in self.syllable_patterns:
            return self.syllable_patterns[name_upper]

        # Simple syllable detection (not perfect but functional)
        # This is a basic implementation - could be enhanced with NLP libraries
        syllables = []
        current_syllable = ""

        vowels = set('AEIOU')
        prev_was_vowel = False

        for i, char in enumerate(name_upper):
            current_is_vowel = char in vowels

            if current_is_vowel and prev_was_vowel:
                # Double vowel - keep together
                current_syllable += char
            elif current_is_vowel and not prev_was_vowel:
                # Consonant to vowel - potential syllable boundary
                if len(current_syllable) > 2:  # Don't break very short syllables
                    syllables.append(current_syllable[:-1])
                    current_syllable = current_syllable[-1] + char
                else:
                    current_syllable += char
            else:
                current_syllable += char

            prev_was_vowel = current_is_vowel

        if current_syllable:
            syllables.append(current_syllable)

        return syllables if len(syllables) > 1 else []

    def _get_optimal_speech_rate(self, difficulty: float) -> float:
        """Get optimal speech rate based on difficulty"""
        for threshold, rate in sorted(self.speech_rates.items(), reverse=True):
            if difficulty >= threshold:
                return rate
        return 1.0  # Normal speed for easy names

    def _generate_alternatives(self, location_name: str, context: str) -> List[str]:
        """Generate alternative descriptions for difficult names"""
        name_upper = location_name.upper()
        alternatives = []

        # Check for pre-defined alternatives
        if name_upper in self.location_descriptions:
            alternatives.extend(self.location_descriptions[name_upper])

        # Generate context-specific alternatives
        if context == 'healthcare':
            alternatives.extend([
                f"the {location_name} medical area",
                f"healthcare facilities in {location_name}",
                f"providers near {location_name}"
            ])

        # Generate phonetic alternatives
        phonetic = self._generate_phonetic_spelling(location_name)
        if phonetic:
            alternatives.append(f"{phonetic} area")

        # Remove duplicates and limit
        seen = set()
        unique_alternatives = []
        for alt in alternatives:
            if alt.lower() not in seen:
                unique_alternatives.append(alt)
                seen.add(alt.lower())

        return unique_alternatives[:5]  # Limit to top 5

    def _add_pronunciation_breaks(self, location_name: str) -> str:
        """Add pronunciation breaks for moderately difficult names"""
        name_upper = location_name.upper()

        # Add breaks before difficult consonant clusters
        difficult_patterns = [
            ('DZ', 'D-Z'),
            ('NY', 'N-Y'),
            ('KW', 'K-W'),
            ('TSH', 'T-SH'),
        ]

        result = location_name
        for pattern, replacement in difficult_patterns:
            result = result.replace(pattern, replacement)

        return result

    async def create_pronunciation_guide(self, location_name: str,
                                       phonetic_spelling: str = None,
                                       ipa_notation: str = None,
                                       ssml_markup: str = None,
                                       difficulty_score: float = None) -> bool:
        """
        Create a new pronunciation guide in the database

        Args:
            location_name: Location name
            phonetic_spelling: Human-readable phonetic spelling
            ipa_notation: International Phonetic Alphabet notation
            ssml_markup: SSML markup for TTS
            difficulty_score: Pronunciation difficulty (0.0-1.0)

        Returns:
            True if created successfully
        """
        try:
            # Generate missing components
            if difficulty_score is None:
                difficulty_score = self._calculate_difficulty_score(location_name)

            if ssml_markup is None:
                ssml_markup = self._generate_ssml(location_name, difficulty_score)

            if phonetic_spelling is None:
                phonetic_spelling = self._generate_phonetic_spelling(location_name)

            # Create pronunciation guide
            guide = PronunciationGuide(
                location_name=location_name.upper(),
                language=LanguageContext.ENGLISH,
                phonetic_spelling=phonetic_spelling,
                ipa_notation=ipa_notation,
                ssml_markup=ssml_markup,
                difficulty_score=difficulty_score,
                recommended_speech_rate=self._get_optimal_speech_rate(difficulty_score),
                alternative_descriptions=self._generate_alternatives(location_name, 'general')
            )

            await self.repository.create_pronunciation_guide(guide)
            logger.info(f"✅ Created pronunciation guide for: {location_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create pronunciation guide for '{location_name}': {e}")
            return False

    async def optimize_response_text(self, response_text: str, context: str = 'general') -> str:
        """
        Optimize entire response text for pronunciation

        Args:
            response_text: Full response text containing location names
            context: Response context

        Returns:
            Optimized response text with pronunciation improvements
        """
        try:
            # Find location names in the text (simple pattern matching)
            # This could be enhanced with NER or more sophisticated pattern matching
            location_patterns = [
                r'\b[A-Z][A-Z\s/&-]+\b',  # All caps patterns like "ACCRA CENTRAL / TUDU"
                r'\b(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+area\b',  # "the Madina area"
            ]

            optimized_text = response_text

            for pattern in location_patterns:
                matches = re.finditer(pattern, response_text)
                for match in matches:
                    location_name = match.group().strip()

                    # Skip common English words
                    if location_name.lower() in ['the', 'area', 'near', 'and', 'or']:
                        continue

                    # Optimize this location name
                    result = await self.optimize_for_tts(location_name, context)

                    # Replace if optimization provides a better alternative
                    if result.difficulty_score > 0.6 and result.optimized_text != location_name:
                        optimized_text = optimized_text.replace(location_name, result.optimized_text)

            return optimized_text

        except Exception as e:
            logger.error(f"Failed to optimize response text: {e}")
            return response_text  # Return original on error