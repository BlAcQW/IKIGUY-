#!/usr/bin/env python3
"""
Enhanced Twi Text Processor
High-quality text preprocessing for Twi language with comprehensive linguistic support.

Features:
- Comprehensive Twi number conversion
- Advanced text normalization
- Cultural context preservation
- Dialect-aware processing
- Quality assessment and validation
"""

import re
import unicodedata
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class TwiLinguisticFeatures:
    """Twi-specific linguistic features and patterns."""
    
    # Twi-specific characters
    twi_vowels: Set[str] = frozenset({'a', 'e', 'ɛ', 'i', 'o', 'ɔ', 'u'})
    twi_special_chars: Set[str] = frozenset({'ɛ', 'Ɛ', 'ɔ', 'Ɔ', 'ã', 'ẽ', 'ĩ', 'õ', 'ũ'})
    
    # Common Twi prefixes and suffixes
    common_prefixes: Set[str] = frozenset({'a', 'o', 'ɔ', 'me', 'wo', 'ɛ', 're', 'be'})
    common_suffixes: Set[str] = frozenset({'e', 'ɛ', 'i', 'o', 'ɔ', 'u', 'a', 'foɔ', 'nom'})
    
    # Tone markers (though not always written)
    tone_markers: Set[str] = frozenset({'́', '̀', '̂', '̌', '̄'})
    
    # Common Twi words for validation
    common_words: Set[str] = frozenset({
        'wo', 'me', 'ɔ', 'yɛ', 'ne', 'wɔ', 'na', 'sɛ', 'mu', 'ho', 'no', 'de', 'a', 'ɛ',
        'baako', 'mmienu', 'mmiɛnsa', 'nnan', 'nnum', 'nsia', 'nson', 'nwɔtwe', 'nkron',
        'akye', 'maakye', 'adwo', 'anadwo', 'ɔkyena', 'nnɛ', 'nante', 'yie', 'ase', 'paa',
        'kasa', 'dwom', 'nsɛm', 'amoa', 'ɔman', 'fie', 'sukuu', 'adwuma', 'aduane'
    })

class TwiNumberProcessor:
    """Advanced Twi number conversion system."""
    
    def __init__(self):
        # Basic numbers 0-10
        self.units = {
            0: 'hwee', 1: 'baako', 2: 'mmienu', 3: 'mmiɛnsa',
            4: 'nnan', 5: 'nnum', 6: 'nsia', 7: 'nson',
            8: 'nwɔtwe', 9: 'nkron', 10: 'edu'
        }
        
        # Numbers 11-19
        self.teens = {
            11: 'dubaako', 12: 'dummienu', 13: 'dummiɛnsa',
            14: 'dunan', 15: 'dunum', 16: 'dunsia',
            17: 'dunson', 18: 'dunwɔtwe', 19: 'dunkron'
        }
        
        # Tens 20-90
        self.tens = {
            20: 'aduonu', 30: 'aduasa', 40: 'aduanan',
            50: 'aduonum', 60: 'aduosia', 70: 'aduɔson',
            80: 'aduɔwɔtwe', 90: 'aduɔkron'
        }
        
        # Scale units
        self.scale = {
            100: 'ɔha', 1000: 'apem', 1000000: 'ɔpepem'
        }
        
        # Ordinal numbers
        self.ordinals = {
            1: 'deɛ ɛdi kan', 2: 'deɛ ɛtɔ so mmienu', 3: 'deɛ ɛtɔ so mmiɛnsa',
            4: 'deɛ ɛtɔ so nnan', 5: 'deɛ ɛtɔ so nnum'
        }
    
    def convert_number(self, num: int, ordinal: bool = False) -> str:
        """Convert integer to Twi words."""
        if ordinal and num in self.ordinals:
            return self.ordinals[num]
        
        if num == 0:
            return self.units[0]
        
        if num < 0:
            return f"negative {self.convert_number(-num)}"
        
        # Handle basic numbers
        if num <= 10:
            return self.units[num]
        elif num <= 19:
            return self.teens[num]
        elif num in self.tens:
            return self.tens[num]
        elif num < 100:
            tens_digit = (num // 10) * 10
            units_digit = num % 10
            return f"{self.tens[tens_digit]} {self.units[units_digit]}"
        elif num == 100:
            return self.scale[100]
        elif num < 1000:
            hundreds = num // 100
            remainder = num % 100
            result = f"{self.units[hundreds]} {self.scale[100]}"
            if remainder > 0:
                result += f" {self.convert_number(remainder)}"
            return result
        elif num == 1000:
            return self.scale[1000]
        elif num < 1000000:
            thousands = num // 1000
            remainder = num % 1000
            result = f"{self.convert_number(thousands)} {self.scale[1000]}"
            if remainder > 0:
                result += f" {self.convert_number(remainder)}"
            return result
        else:
            # For very large numbers, use a simplified approach
            return str(num)  # Fallback to digits for now
    
    def convert_decimal(self, decimal_str: str) -> str:
        """Convert decimal numbers to Twi."""
        if '.' not in decimal_str:
            return self.convert_number(int(decimal_str))
        
        integer_part, decimal_part = decimal_str.split('.')
        integer_twi = self.convert_number(int(integer_part))
        
        # Convert decimal digits individually
        decimal_twi = ' '.join(self.units[int(d)] for d in decimal_part)
        
        return f"{integer_twi} ne {decimal_twi}"
    
    def process_all_numbers(self, text: str) -> str:
        """Process all numbers in text to Twi words."""
        def convert_match(match):
            num_str = match.group(0)
            
            # Handle decimals
            if '.' in num_str:
                return self.convert_decimal(num_str)
            
            # Handle ordinals (1st, 2nd, etc.)
            if re.search(r'\d+(st|nd|rd|th)', num_str):
                num = int(re.search(r'\d+', num_str).group())
                return self.convert_number(num, ordinal=True)
            
            # Regular numbers
            num = int(num_str)
            return self.convert_number(num)
        
        # Match decimal numbers, ordinals, and regular numbers
        pattern = r'\b\d+(?:\.\d+)?(?:st|nd|rd|th)?\b'
        text = re.sub(pattern, convert_match, text)
        return text

class TwiTextNormalizer:
    """Advanced text normalization for Twi."""
    
    def __init__(self):
        self.linguistic_features = TwiLinguisticFeatures()
        
        # Common encoding fixes
        self.encoding_fixes = {
            'è': 'ɛ', 'È': 'Ɛ', 'e`': 'ɛ', 'E`': 'Ɛ',
            'ò': 'ɔ', 'Ò': 'Ɔ', 'o`': 'ɔ', 'O`': 'Ɔ',
            'â': 'ã', 'Â': 'Ã', 'ê': 'ẽ', 'Ê': 'Ẽ',
            'î': 'ĩ', 'Î': 'Ĩ', 'ô': 'õ', 'Ô': 'Õ',
            'û': 'ũ', 'Û': 'Ũ'
        }
        
        # Common abbreviations
        self.abbreviations = {
            'Dr.': 'Dɔkta', 'Mr.': 'Owura', 'Mrs.': 'Awuraa',
            'Prof.': 'Profesa', 'Rev.': 'Osofoɔ',
            'vs.': 'ne', 'etc.': 'ne nea ɛkeka ho',
            '&': 'ne', '+': 'ne'
        }
        
        # Time and date expressions
        self.time_expressions = {
            'am': 'anɔpa', 'pm': 'anwummer',
            'AM': 'anɔpa', 'PM': 'anwummer'
        }
    
    def normalize_encoding(self, text: str) -> str:
        """Fix common encoding issues."""
        # Apply Unicode normalization first
        text = unicodedata.normalize('NFC', text)
        
        # Fix common encoding problems
        for old, new in self.encoding_fixes.items():
            text = text.replace(old, new)
        
        return text
    
    def normalize_abbreviations(self, text: str) -> str:
        """Expand common abbreviations."""
        for abbrev, expansion in self.abbreviations.items():
            # Use word boundaries to avoid partial replacements
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            text = re.sub(pattern, expansion, text, flags=re.IGNORECASE)
        
        return text
    
    def normalize_punctuation(self, text: str) -> str:
        """Normalize punctuation marks."""
        # Normalize quotes
        text = re.sub(r'[\u201c\u201d]', '"', text)
        text = re.sub(r'[\u2018\u2019]', "'", text)
        
        # Normalize dashes
        text = re.sub(r'[–—]', '-', text)
        
        # Clean up multiple punctuation
        text = re.sub(r'([.!?]){2,}', r'\1', text)
        text = re.sub(r'([,;:]){2,}', r'\1', text)
        
        # Add spaces around punctuation if missing
        text = re.sub(r'([.!?])([A-ZƐƆ])', r'\1 \2', text)
        
        return text
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace."""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.!?,:;])', r'\1', text)
        text = re.sub(r'([.!?])\s*([A-ZƐƆ])', r'\1 \2', text)
        
        return text
    
    def normalize_case(self, text: str, preserve_proper_nouns: bool = True) -> str:
        """Normalize text case while preserving proper nouns."""
        if not preserve_proper_nouns:
            return text.lower()
        
        # Split into sentences
        sentences = re.split(r'([.!?]+)', text)
        normalized_sentences = []
        
        for i, sentence in enumerate(sentences):
            if i % 2 == 0:  # Actual sentence content
                # Capitalize first word of sentence
                words = sentence.strip().split()
                if words:
                    words[0] = words[0].capitalize()
                    
                    # Keep proper nouns capitalized (heuristic approach)
                    for j, word in enumerate(words[1:], 1):
                        # If word starts with capital and is not a common Twi word
                        if (word and word[0].isupper() and 
                            word.lower() not in self.linguistic_features.common_words):
                            continue  # Keep capitalized
                        else:
                            words[j] = word.lower()
                    
                normalized_sentences.append(' '.join(words))
            else:
                normalized_sentences.append(sentence)  # Punctuation
        
        return ''.join(normalized_sentences)

class TwiTextQualityAssessor:
    """Assess the quality of Twi text."""
    
    def __init__(self):
        self.linguistic_features = TwiLinguisticFeatures()
        
        # Quality indicators
        self.positive_indicators = {
            'twi_characters': 2.0,      # Contains ɛ, ɔ
            'common_words': 1.5,        # Contains common Twi words
            'proper_length': 1.0,       # Appropriate length
            'punctuation': 0.5,         # Has proper punctuation
            'capitalization': 0.5       # Proper capitalization
        }
        
        self.negative_indicators = {
            'excessive_english': -2.0,   # Too much English
            'encoding_issues': -1.5,     # Encoding problems
            'excessive_punctuation': -1.0,  # Too much punctuation
            'too_short': -2.0,          # Very short
            'too_long': -1.0,           # Excessively long
            'no_vowels': -3.0           # Missing vowels (corruption)
        }
    
    def assess_quality(self, text: str) -> Dict[str, float]:
        """Assess text quality and return detailed scores."""
        if not text or len(text.strip()) == 0:
            return {
                'overall_score': 0.0,
                'length_score': 0.0,
                'linguistic_score': 0.0,
                'encoding_score': 0.0,
                'structure_score': 0.0,
                'issues': ['empty_text']
            }
        
        text = text.strip()
        issues = []
        
        # Length assessment
        length_score = self._assess_length(text, issues)
        
        # Linguistic content assessment
        linguistic_score = self._assess_linguistic_content(text, issues)
        
        # Encoding quality assessment
        encoding_score = self._assess_encoding_quality(text, issues)
        
        # Structure assessment
        structure_score = self._assess_structure(text, issues)
        
        # Overall score (weighted average)
        overall_score = (
            length_score * 0.2 +
            linguistic_score * 0.4 +
            encoding_score * 0.2 +
            structure_score * 0.2
        )
        
        return {
            'overall_score': max(0.0, min(10.0, overall_score)),
            'length_score': length_score,
            'linguistic_score': linguistic_score,
            'encoding_score': encoding_score,
            'structure_score': structure_score,
            'issues': issues
        }
    
    def _assess_length(self, text: str, issues: List[str]) -> float:
        """Assess text length appropriateness."""
        char_count = len(text)
        word_count = len(text.split())
        
        if char_count < 5:
            issues.append('too_short')
            return 1.0
        elif char_count > 500:
            issues.append('too_long')
            return 6.0
        elif 10 <= char_count <= 200:
            return 8.0
        elif 5 <= char_count < 10 or 200 < char_count <= 500:
            return 6.0
        else:
            return 7.0
    
    def _assess_linguistic_content(self, text: str, issues: List[str]) -> float:
        """Assess linguistic content quality."""
        text_lower = text.lower()
        score = 5.0
        
        # Check for Twi-specific characters
        if any(char in text for char in self.linguistic_features.twi_special_chars):
            score += self.positive_indicators['twi_characters']
        
        # Check for common Twi words
        words = text_lower.split()
        twi_word_count = sum(1 for word in words if word in self.linguistic_features.common_words)
        if twi_word_count > 0:
            score += self.positive_indicators['common_words'] * min(twi_word_count / len(words), 1.0)
        
        # Check for excessive English
        english_indicators = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for']
        english_count = sum(1 for word in words if word in english_indicators)
        if english_count / len(words) > 0.3:  # More than 30% English
            issues.append('excessive_english')
            score += self.negative_indicators['excessive_english']
        
        # Check for vowels (corruption indicator)
        if not any(char in text_lower for char in 'aeiouɛɔ'):
            issues.append('no_vowels')
            score += self.negative_indicators['no_vowels']
        
        return max(1.0, min(10.0, score))
    
    def _assess_encoding_quality(self, text: str, issues: List[str]) -> float:
        """Assess encoding quality."""
        score = 8.0
        
        # Check for common encoding issues
        encoding_issues = ['Ã', 'â', 'Â', 'ê', 'Ê', 'î', 'Î', 'ô', 'Ô', 'û', 'Û']
        if any(issue in text for issue in encoding_issues):
            issues.append('encoding_issues')
            score += self.negative_indicators['encoding_issues']
        
        # Check for control characters
        if any(ord(char) < 32 and char not in '\n\r\t' for char in text):
            issues.append('control_characters')
            score -= 2.0
        
        return max(1.0, min(10.0, score))
    
    def _assess_structure(self, text: str, issues: List[str]) -> float:
        """Assess text structure quality."""
        score = 6.0
        
        # Check punctuation
        if re.search(r'[.!?]', text):
            score += self.positive_indicators['punctuation']
        
        # Check capitalization
        if re.search(r'^[A-ZƐƆ]', text):
            score += self.positive_indicators['capitalization']
        
        # Check excessive punctuation
        punctuation_density = len(re.findall(r'[.!?,;:]', text)) / len(text)
        if punctuation_density > 0.1:  # More than 10% punctuation
            issues.append('excessive_punctuation')
            score += self.negative_indicators['excessive_punctuation']
        
        return max(1.0, min(10.0, score))

class EnhancedTwiTextProcessor:
    """Complete high-quality Twi text processing pipeline."""
    
    def __init__(self, dialect: str = 'asante', preserve_formatting: bool = True):
        self.dialect = dialect
        self.preserve_formatting = preserve_formatting
        
        # Initialize components
        self.number_processor = TwiNumberProcessor()
        self.normalizer = TwiTextNormalizer()
        self.quality_assessor = TwiTextQualityAssessor()
        self.linguistic_features = TwiLinguisticFeatures()
        
        logger.info(f"Enhanced Twi text processor initialized for {dialect} dialect")
    
    def process_text(self, text: str, expand_numbers: bool = True, 
                    assess_quality: bool = True, normalize_case: bool = True) -> Dict:
        """Complete text processing pipeline with comprehensive analysis."""
        if not text:
            return self._empty_result()
        
        original_text = text
        processing_log = []
        
        # Step 1: Initial cleanup
        text = text.strip()
        if not text:
            return self._empty_result(original_text)
        
        # Step 2: Encoding normalization
        text = self.normalizer.normalize_encoding(text)
        processing_log.append('encoding_normalized')
        
        # Step 3: Abbreviation expansion
        text = self.normalizer.normalize_abbreviations(text)
        processing_log.append('abbreviations_expanded')
        
        # Step 4: Number processing
        if expand_numbers:
            text = self.number_processor.process_all_numbers(text)
            processing_log.append('numbers_converted')
        
        # Step 5: Punctuation normalization
        text = self.normalizer.normalize_punctuation(text)
        processing_log.append('punctuation_normalized')
        
        # Step 6: Case normalization
        if normalize_case:
            text = self.normalizer.normalize_case(text, preserve_proper_nouns=True)
            processing_log.append('case_normalized')
        
        # Step 7: Whitespace cleanup
        text = self.normalizer.normalize_whitespace(text)
        processing_log.append('whitespace_normalized')
        
        # Step 8: Quality assessment
        quality_analysis = None
        if assess_quality:
            quality_analysis = self.quality_assessor.assess_quality(text)
            processing_log.append('quality_assessed')
        
        # Step 9: Linguistic analysis
        linguistic_analysis = self._analyze_linguistic_features(text)
        processing_log.append('linguistic_analyzed')
        
        # Compile results
        result = {
            'original': original_text,
            'processed': text,
            'dialect': self.dialect,
            'char_count': len(text),
            'word_count': len(text.split()),
            'has_twi_chars': linguistic_analysis['has_twi_chars'],
            'twi_char_count': linguistic_analysis['twi_char_count'],
            'common_twi_words': linguistic_analysis['common_twi_words'],
            'estimated_twi_content': linguistic_analysis['estimated_twi_content'],
            'processing_log': processing_log,
            'changes_made': original_text.strip() != text
        }
        
        if quality_analysis:
            result['quality'] = quality_analysis
        
        return result
    
    def _analyze_linguistic_features(self, text: str) -> Dict:
        """Analyze linguistic features of the text."""
        text_lower = text.lower()
        words = text_lower.split()
        
        # Count Twi-specific characters
        twi_chars = [char for char in text if char in self.linguistic_features.twi_special_chars]
        
        # Count common Twi words
        common_words = [word for word in words if word in self.linguistic_features.common_words]
        
        # Estimate Twi content percentage
        twi_indicators = len(twi_chars) + len(common_words) * 2
        total_indicators = len(text) + len(words)
        estimated_twi_content = min(1.0, twi_indicators / total_indicators) if total_indicators > 0 else 0.0
        
        return {
            'has_twi_chars': len(twi_chars) > 0,
            'twi_char_count': len(twi_chars),
            'common_twi_words': len(common_words),
            'estimated_twi_content': estimated_twi_content,
            'unique_twi_chars': list(set(twi_chars)),
            'found_common_words': common_words
        }
    
    def _empty_result(self, original: str = '') -> Dict:
        """Return result structure for empty/invalid text."""
        return {
            'original': original,
            'processed': '',
            'dialect': self.dialect,
            'char_count': 0,
            'word_count': 0,
            'has_twi_chars': False,
            'twi_char_count': 0,
            'common_twi_words': 0,
            'estimated_twi_content': 0.0,
            'processing_log': ['empty_input'],
            'changes_made': False,
            'quality': {
                'overall_score': 0.0,
                'length_score': 0.0,
                'linguistic_score': 0.0,
                'encoding_score': 0.0,
                'structure_score': 0.0,
                'issues': ['empty_text']
            }
        }
    
    def batch_process_texts(self, texts: List[str], **kwargs) -> List[Dict]:
        """Process multiple texts efficiently."""
        results = []
        
        for i, text in enumerate(texts):
            try:
                result = self.process_text(text, **kwargs)
                results.append(result)
                
                # Log progress for large batches
                if i > 0 and i % 1000 == 0:
                    logger.info(f"Processed {i}/{len(texts)} texts")
                    
            except Exception as e:
                logger.error(f"Failed to process text {i}: {e}")
                results.append(self._empty_result(text))
        
        return results
    
    def get_processing_statistics(self, results: List[Dict]) -> Dict:
        """Get processing statistics from batch results."""
        if not results:
            return {'total': 0, 'processed': 0, 'success_rate': 0.0}
        
        total = len(results)
        processed = sum(1 for r in results if r['processed'])
        high_quality = sum(1 for r in results if r.get('quality', {}).get('overall_score', 0) >= 7.0)
        
        return {
            'total_texts': total,
            'successfully_processed': processed,
            'high_quality_texts': high_quality,
            'success_rate': processed / total if total > 0 else 0.0,
            'quality_rate': high_quality / total if total > 0 else 0.0,
            'average_length': sum(r['char_count'] for r in results) / total if total > 0 else 0.0,
            'twi_content_rate': sum(1 for r in results if r['has_twi_chars']) / total if total > 0 else 0.0
        }

# Test function for validation
def test_enhanced_processor():
    """Test the enhanced text processor."""
    processor = EnhancedTwiTextProcessor()
    
    test_texts = [
        "Wo ho te sɛn? Me ho yɛ.",
        "Me ma wo akye 5 berɛ wɔ ɔkyena anɔpa no.",
        "Dr. Kwame ne Prof. Ama baa sukuu no mu",
        "Ɛyɛ 23.5 degrees wɔ Accra mu nnɛ",
        "Me pɛ sɛ menya 1st prize wɔ competition yi mu"
    ]
    
    print("🧪 Testing Enhanced Twi Text Processor")
    print("=" * 50)
    
    for i, text in enumerate(test_texts, 1):
        result = processor.process_text(text)
        print(f"\nTest {i}:")
        print(f"  Original: {result['original']}")
        print(f"  Processed: {result['processed']}")
        print(f"  Quality: {result['quality']['overall_score']:.1f}/10")
        print(f"  Changes: {result['changes_made']}")
        print(f"  Twi content: {result['estimated_twi_content']:.1%}")
    
    print("\n✅ Testing complete!")

if __name__ == "__main__":
    test_enhanced_processor()

print("[SUCCESS] Enhanced Twi Text Processor loaded successfully!")