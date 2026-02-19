#!/usr/bin/env python3
"""
Enhanced Text Processing for Twi/Akan Voice Technology
Complete Python module version (can be imported directly)
"""

import re
import unicodedata
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Optional imports - only needed for batch processing
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


class TwiNumberProcessor:
    """Convert numbers to Twi words following the Twi counting system."""
    
    def __init__(self):
        # Basic numbers 0-10
        self.units = {
            0: 'hwee', 1: 'baako', 2: 'mmienu', 3: 'mmiɛnsa',
            4: 'nnan', 5: 'nnum', 6: 'nsia', 7: 'nson',
            8: 'nwɔtwe', 9: 'nkron', 10: 'edu'
        }
        
        # Numbers 11-19 (edu + unit)
        self.teens = {
            11: 'dubaako', 12: 'dummienu', 13: 'dummiɛnsa',
            14: 'dunan', 15: 'dunum', 16: 'dunsia',
            17: 'dunson', 18: 'dunwɔtwe', 19: 'dunkron'
        }
        
        # Tens
        self.tens = {
            20: 'aduonu', 30: 'aduasa', 40: 'aduanan',
            50: 'aduonum', 60: 'aduosia', 70: 'aduɔson',
            80: 'aduɔwɔtwe', 90: 'aduɔkron'
        }
        
        # Hundreds and thousands
        self.scale = {
            100: 'ɔha', 200: 'ahannu', 300: 'ahansa', 400: 'ahanan',
            500: 'ahanum', 600: 'ahansia', 700: 'ahanson',
            800: 'ahanwɔtwe', 900: 'ahankron',
            1000: 'apem', 10000: 'mpem edu', 100000: 'mpem ɔha',
            1000000: 'ɔpepem'
        }
    
    def convert_number(self, num: int) -> str:
        """Convert integer to Twi words."""
        if num == 0:
            return self.units[0]
        
        if num < 0:
            return f"negative {self.convert_number(-num)}"
        
        # Direct lookup for basic numbers
        if num <= 10:
            return self.units[num]
        elif num <= 19:
            return self.teens[num]
        elif num in self.tens:
            return self.tens[num]
        elif num in self.scale:
            return self.scale[num]
        
        # Compound numbers
        if num < 100:
            tens = (num // 10) * 10
            units = num % 10
            if units == 0:
                return self.tens[tens]
            return f"{self.tens[tens]} ne {self.units[units]}"
        
        # Hundreds
        elif num < 1000:
            hundreds = (num // 100) * 100
            remainder = num % 100
            if remainder == 0:
                return self.scale.get(hundreds, f"{self.units[num//100]} ɔha")
            return f"{self.scale.get(hundreds, f'{self.units[num//100]} ɔha')} ne {self.convert_number(remainder)}"
        
        # Thousands
        elif num < 10000:
            thousands = num // 1000
            remainder = num % 1000
            if remainder == 0:
                return f"{self.convert_number(thousands)} apem" if thousands > 1 else "apem"
            return f"{self.convert_number(thousands)} apem ne {self.convert_number(remainder)}"
        
        # Larger numbers
        elif num < 1000000:
            ten_thousands = num // 10000
            remainder = num % 10000
            if remainder == 0:
                return f"mpem {self.convert_number(ten_thousands)}"
            return f"mpem {self.convert_number(ten_thousands)} ne {self.convert_number(remainder)}"
        
        else:
            millions = num // 1000000
            remainder = num % 1000000
            if remainder == 0:
                return f"{self.convert_number(millions)} ɔpepem"
            return f"{self.convert_number(millions)} ɔpepem ne {self.convert_number(remainder)}"
    
    def process_currency(self, text: str) -> str:
        """Convert currency amounts to Twi."""
        # Ghana Cedis
        text = re.sub(r'GH[₵¢]\s*(\d+)(?:\.(\d+))?', 
                     lambda m: self._format_currency(m, 'Ghana sidi'), text)
        
        # US Dollars
        text = re.sub(r'\$\s*(\d+)(?:\.(\d+))?',
                     lambda m: self._format_currency(m, 'Amerika dɔla'), text)
        
        return text
    
    def _format_currency(self, match, currency_name: str) -> str:
        """Helper to format currency amounts."""
        whole = int(match.group(1))
        decimal = match.group(2)
        
        result = f"{self.convert_number(whole)} {currency_name}"
        
        if decimal and int(decimal) > 0:
            result += f" ne pesewa {self.convert_number(int(decimal))}"
        
        return result
    
    def process_all_numbers(self, text: str) -> str:
        """Process all numbers in text."""
        # Process currency first
        text = self.process_currency(text)
        
        # Convert standalone numbers
        def convert_match(match):
            num = int(match.group(0))
            return self.convert_number(num)
        
        text = re.sub(r'\b\d+\b', convert_match, text)
        
        return text


class TwiPhonemeMapper:
    """Map Twi text to IPA phonemes for TTS."""
    
    def __init__(self):
        # Vowel phonemes
        self.vowels = {
            'a': 'a', 'e': 'e', 'ɛ': 'ɛ', 'i': 'i',
            'o': 'o', 'ɔ': 'ɔ', 'u': 'u',
            # Nasalized vowels
            'ã': 'ã', 'ẽ': 'ẽ', 'ɛ̃': 'ɛ̃', 'ĩ': 'ĩ',
            'õ': 'õ', 'ɔ̃': 'ɔ̃', 'ũ': 'ũ',
        }
        
        # Consonant phonemes
        self.consonants = {
            'b': 'b', 'd': 'd', 'f': 'f', 'g': 'g',
            'h': 'h', 'k': 'k', 'l': 'l', 'm': 'm',
            'n': 'n', 'p': 'p', 'r': 'r', 's': 's',
            't': 't', 'w': 'w', 'y': 'j',
            # Special consonant clusters
            'ky': 'tɕ', 'gy': 'dʑ', 'tw': 'tʷ', 'dw': 'dʷ',
            'kw': 'kʷ', 'gw': 'gʷ', 'hw': 'hʷ', 'hy': 'çʲ',
            'ny': 'ɲ', 'nw': 'nʷ',
        }
    
    def text_to_phonemes(self, text: str) -> str:
        """Convert Twi text to IPA phonemes."""
        text = text.lower()
        phonemes = []
        
        words = text.split()
        for word in words:
            phoneme_word = self.word_to_phoneme(word)
            phonemes.append(phoneme_word)
        
        return ' '.join(phonemes)
    
    def word_to_phoneme(self, word: str) -> str:
        """Convert single word to phoneme representation."""
        # Process consonant clusters first
        for cluster, phoneme in sorted(self.consonants.items(), key=lambda x: -len(x[0])):
            if len(cluster) > 1:  # Only process clusters
                word = word.replace(cluster, f'|{phoneme}|')
        
        # Process individual characters
        result = []
        i = 0
        while i < len(word):
            if word[i] == '|':
                # Extract already processed phoneme
                end = word.find('|', i + 1)
                result.append(word[i+1:end])
                i = end + 1
            elif word[i] in self.vowels:
                result.append(self.vowels[word[i]])
                i += 1
            elif word[i] in self.consonants:
                result.append(self.consonants[word[i]])
                i += 1
            else:
                result.append(word[i])
                i += 1
        
        return ''.join(result)


class TwiDateTimeProcessor:
    """Convert dates and times to Twi."""
    
    def __init__(self):
        # Days of the week
        self.days = {
            'monday': 'Dwowda',
            'tuesday': 'Benada',
            'wednesday': 'Wukuda',
            'thursday': 'Yawda',
            'friday': 'Fida',
            'saturday': 'Memeneda',
            'sunday': 'Kwesida'
        }
        
        # Months
        self.months = {
            'january': 'Ɔpɛpɔn',
            'february': 'Ɔgyefuo',
            'march': 'Ɔbenem',
            'april': 'Oforisuo',
            'may': 'Ayɛwohomumu',
            'june': 'Obubuo',
            'july': 'Ayɛwoho',
            'august': 'Difuu',
            'september': 'Fankwa',
            'october': 'Ɔbɛsɛ',
            'november': 'Ɔberɛfɛw',
            'december': 'Mfufuoɔpɛpɔn'
        }
        
        self.num_processor = TwiNumberProcessor()
    
    def process_time(self, text: str) -> str:
        """Convert time expressions to Twi."""
        # Convert HH:MM format
        def convert_time(match):
            hour = int(match.group(1))
            minute = int(match.group(2))
            
            # Determine time period
            if hour < 6:
                period = "anadwo"  # night
            elif hour < 12:
                period = "anɔpa"  # morning
            elif hour < 18:
                period = "awia"  # afternoon
            else:
                period = "anwummere"  # evening
            
            # Convert to 12-hour format
            hour_12 = hour % 12
            if hour_12 == 0:
                hour_12 = 12
            
            hour_twi = self.num_processor.convert_number(hour_12)
            
            if minute == 0:
                return f"{period} dɔn {hour_twi}"
            else:
                min_twi = self.num_processor.convert_number(minute)
                return f"{period} dɔn {hour_twi} ne simma {min_twi}"
        
        text = re.sub(r'\b(\d{1,2}):(\d{2})\b', convert_time, text)
        return text
    
    def process_date(self, text: str) -> str:
        """Convert date expressions to Twi."""
        # Handle month names
        for eng, twi in self.months.items():
            text = re.sub(f'\\b{eng}\\b', twi, text, flags=re.IGNORECASE)
        
        # Handle day names
        for eng, twi in self.days.items():
            text = re.sub(f'\\b{eng}\\b', twi, text, flags=re.IGNORECASE)
        
        return text
    
    def process_all(self, text: str) -> str:
        """Process all date and time expressions."""
        text = self.process_time(text)
        text = self.process_date(text)
        return text


class TwiAbbreviationExpander:
    """Expand abbreviations and acronyms for Twi."""
    
    def __init__(self):
        # Titles
        self.titles = {
            'Mr.': 'Owura',
            'Mrs.': 'Awura',
            'Ms.': 'Awura',
            'Dr.': 'Dokota',
            'Prof.': 'Ɔbenfo',
            'Rev.': 'Ɔsofo',
        }
        
        # Organizations
        self.organizations = {
            'NPP': 'En Pi Pi',
            'NDC': 'En Di Si',
            'GBC': 'Ghana Kasaboa Adwumakuo',
            'KNUST': 'Kwame Nkrumah Nyansapɔ ne Mfiridwuma Suapɔn',
        }
        
        # Units
        self.units = {
            'km': 'kilomita',
            'kg': 'kilogram',
            'L': 'lita',
        }
    
    def expand_all(self, text: str) -> str:
        """Expand all abbreviations in text."""
        # Expand titles
        for abbrev, expansion in self.titles.items():
            text = text.replace(abbrev, expansion)
        
        # Expand organizations
        for abbrev, expansion in self.organizations.items():
            text = re.sub(f'\\b{abbrev}\\b', expansion, text)
        
        # Expand units
        for abbrev, expansion in self.units.items():
            text = re.sub(f'(\\d+\\s*)\\b{re.escape(abbrev)}\\b', f'\\1 {expansion}', text)
        
        return text


class TwiDialectProcessor:
    """Handle dialect-specific variations in Twi."""
    
    def __init__(self, target_dialect='asante'):
        self.target_dialect = target_dialect.lower()
        
        # Dialect-specific variations
        self.dialect_variations = {
            'asante': {
                'dɛn': 'sɛn',  # what
                'wɔ he': 'wɔ hen',  # where
            },
            'akuapem': {
                'sɛn': 'dɛn',  # what
                'wɔ hen': 'wɔ he',  # where
            },
            'fante': {
                'me': 'mi',  # I/me
                'wo': 'iw',  # you
            }
        }
    
    def convert_to_dialect(self, text: str) -> str:
        """Convert text to target dialect."""
        if self.target_dialect not in self.dialect_variations:
            return text
        
        variations = self.dialect_variations[self.target_dialect]
        
        # Apply word-level replacements
        for standard, dialect in variations.items():
            text = re.sub(f'\\b{re.escape(standard)}\\b', dialect, text, flags=re.IGNORECASE)
        
        return text


class EnhancedTwiTextProcessor:
    """Complete production-ready Twi text processing pipeline."""
    
    def __init__(self, dialect='asante'):
        self.dialect = dialect
        
        # Initialize all sub-processors
        self.number_processor = TwiNumberProcessor()
        self.phoneme_mapper = TwiPhonemeMapper()
        self.datetime_processor = TwiDateTimeProcessor()
        self.abbrev_expander = TwiAbbreviationExpander()
        self.dialect_processor = TwiDialectProcessor(target_dialect=dialect)
        
        # Twi-specific characters
        self.twi_chars = {'ɛ', 'Ɛ', 'ɔ', 'Ɔ', 'ã', 'ẽ', 'ĩ', 'õ', 'ũ'}
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Handle None or empty input
        if not text:
            return ""
        # Normalize unicode
        text = unicodedata.normalize('NFC', text)
        
        # Fix common encoding issues
        replacements = {
            'è': 'ɛ', 'È': 'Ɛ',
            'ò': 'ɔ', 'Ò': 'Ɔ',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove extra spaces
        text = ' '.join(text.split())
        
        return text
    
    def process_text(self, text: str, 
                    expand_numbers=True,
                    expand_abbreviations=True,
                    process_datetime=True,
                    apply_dialect=True,
                    generate_phonemes=False) -> Dict:
        """Complete text processing pipeline."""
        
        original = text
        
        # Step 1: Clean and normalize
        text = self.clean_text(text)
        
        # Step 2: Expand abbreviations
        if expand_abbreviations:
            text = self.abbrev_expander.expand_all(text)
        
        # Step 3: Process date/time
        if process_datetime:
            text = self.datetime_processor.process_all(text)
        
        # Step 4: Convert numbers
        if expand_numbers:
            text = self.number_processor.process_all_numbers(text)
        
        # Step 5: Apply dialect
        if apply_dialect:
            text = self.dialect_processor.convert_to_dialect(text)
        
        # Step 6: Generate phonemes
        phonemes = None
        if generate_phonemes:
            phonemes = self.phoneme_mapper.text_to_phonemes(text)
        
        return {
            'original': original,
            'processed': text,
            'phonemes': phonemes,
            'dialect': self.dialect,
            'has_twi_chars': any(c in text for c in self.twi_chars),
            'word_count': len(text.split()),
            'char_count': len(text)
        }


# Example usage
if __name__ == "__main__":
    # Initialize processor
    processor = EnhancedTwiTextProcessor(dialect='asante')
    
    # Test text
    test_text = "Dr. Mensah will pay GH₵500 on Monday at 10:30."
    
    # Process
    result = processor.process_text(test_text, generate_phonemes=True)
    
    print("Original:", result['original'])
    print("Processed:", result['processed'])
    print("Phonemes:", result['phonemes'])
    print("Dialect:", result['dialect'])
    print("Has Twi chars:", result['has_twi_chars'])