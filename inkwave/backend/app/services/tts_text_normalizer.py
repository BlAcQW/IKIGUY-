"""
TTS Text Normalization Service.

Prepares text for professional audiobook-quality TTS narration.
Ensures punctuation controls timing/intonation but is never spoken aloud.

Key features:
- Strips decorative separators and isolated punctuation
- Converts em-dashes and ellipses to SSML pause markers
- Cleans malformed spacing and symbols
- Generates book/chapter introductions from metadata

Author: AI Labs Africa
Created: January 2, 2026
"""

import re
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class PauseLength(Enum):
    """Pause durations for TTS."""
    MICRO = 100      # Very brief hesitation
    SHORT = 250      # Comma-level pause
    MEDIUM = 500     # Sentence break
    LONG = 750       # Paragraph break
    CHAPTER = 1500   # Chapter transition


@dataclass
class NormalizedText:
    """Result of text normalization."""
    text: str
    has_ssml: bool = False
    pause_count: int = 0
    original_length: int = 0
    normalized_length: int = 0


class TTSTextNormalizer:
    """
    Normalizes text for professional TTS narration.

    Ensures:
    - Punctuation is NEVER read aloud
    - Pauses are controlled via timing, not spoken words
    - Text flows naturally like a professional narrator
    """

    # Decorative separators to remove entirely
    DECORATIVE_SEPARATORS = [
        r'^\s*[*]{3,}\s*$',           # *** or more
        r'^\s*[-]{3,}\s*$',           # --- or more
        r'^\s*[_]{3,}\s*$',           # ___ or more
        r'^\s*[=]{3,}\s*$',           # === or more
        r'^\s*[~]{3,}\s*$',           # ~~~ or more
        r'^\s*[#]{3,}\s*$',           # ### or more
        r'^\s*[─]{2,}\s*$',           # Unicode box drawing
        r'^\s*[━]{2,}\s*$',           # Heavy box drawing
        r'^\s*[—]{2,}\s*$',           # Multiple em-dashes
        r'^\s*[•]{2,}\s*$',           # Multiple bullets
        r'^\s*[\.]{4,}\s*$',          # Four or more dots
        r'^\s*[\s*•\s*]+\s*$',        # Bullet patterns
    ]

    # Isolated punctuation lines (just punctuation, nothing else)
    ISOLATED_PUNCTUATION = r'^\s*[^\w\s]{1,10}\s*$'

    # Patterns that should become pauses
    PAUSE_PATTERNS = [
        # Em-dash patterns -> medium pause
        (r'\s*—\s*', ' <break time="300ms"/> '),
        (r'\s*–\s*', ' <break time="200ms"/> '),  # En-dash
        (r'\s+[-]\s+', ' <break time="200ms"/> '),  # Spaced hyphen

        # Ellipsis -> longer pause (thinking/trailing off)
        (r'\.{3,}', ' <break time="400ms"/> '),
        (r'…', ' <break time="400ms"/> '),

        # Multiple spaces/newlines -> paragraph pause
        (r'\n\s*\n', ' <break time="600ms"/> '),

        # Colon before list/quote -> brief pause
        (r':\s*(?=[A-Z"])', ': <break time="200ms"/>'),
    ]

    # Bible book names for scripture detection
    BIBLE_BOOKS = (
        r'Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|'
        r'Samuel|Kings|Chronicles|Ezra|Nehemiah|Esther|Job|Psalms?|Proverbs|'
        r'Ecclesiastes|Song\s+of\s+Solomon|Isaiah|Jeremiah|Lamentations|Ezekiel|'
        r'Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|'
        r'Haggai|Zechariah|Malachi|'
        r'Matthew|Mark|Luke|John|Acts|Romans|Corinthians|Galatians|Ephesians|'
        r'Philippians|Colossians|Thessalonians|Timothy|Titus|Philemon|Hebrews|'
        r'James|Peter|Jude|Revelation|'
        # Common abbreviations
        r'Gen|Ex|Lev|Num|Deut|Josh|Judg|Sam|Kgs|Chr|Neh|Est|Ps|Prov|Eccl|'
        r'Isa|Jer|Lam|Ezek|Dan|Hos|Mic|Zech|Mal|'
        r'Matt|Mk|Lk|Jn|Rom|Cor|Gal|Eph|Phil|Col|Thess|Tim|Heb|Jas|Pet|Rev'
    )

    # Symbols that TTS might try to read aloud
    SPOKEN_SYMBOL_CLEANUP = [
        # Note: Scripture references (John 3:16-18, etc.) are handled separately
        # in _normalize_scripture_references() before these patterns are applied

        # Page ranges like "pages 10-20"
        (r'([Pp]ages?\s+)(\d+)-(\d+)', r'\1\2 to \3'),

        # Generic number ranges like "7-9" or "10-15" (non-scripture)
        # These are converted after scripture references are already handled
        (r'(\d+)-(\d+)', r'\1 to \2'),

        # Remove asterisks used for emphasis
        (r'\*+([^*]+)\*+', r'\1'),

        # Remove underscores used for emphasis
        (r'_+([^_]+)_+', r'\1'),

        # Remove brackets around references [1], [note], etc.
        (r'\[\d+\]', ''),
        (r'\[(?:note|ref|see|ibid)\.?\]', '', re.IGNORECASE),

        # Clean up smart quotation marks to straight quotes
        (r'[\u201c\u201d]', '"'),  # Smart double quotes
        (r'[\u2018\u2019]', "'"),  # Smart single quotes

        # Remove standalone symbols that might be read
        (r'^\s*[@#$%^&]\s*$', ''),

        # Clean currency that might be read oddly
        (r'\$(\d)', r'\1 dollars'),
        (r'\u20ac(\d)', r'\1 euros'),  # Euro sign
        (r'\u00a3(\d)', r'\1 pounds'),  # Pound sign
    ]

    # Words TTS should never say (indicates punctuation being read)
    FORBIDDEN_SPOKEN_WORDS = [
        'dash', 'dot', 'comma', 'colon', 'semicolon',
        'period', 'exclamation', 'question mark',
        'quote', 'unquote', 'open quote', 'close quote',
        'parenthesis', 'bracket', 'brace',
        'asterisk', 'ampersand', 'at sign', 'hash',
        'percent', 'caret', 'tilde', 'backslash',
        'forward slash', 'pipe', 'underscore',
    ]

    def __init__(self, use_ssml: bool = True):
        """
        Initialize normalizer.

        Args:
            use_ssml: If True, insert SSML pause tags. If False, use silence markers.
        """
        self.use_ssml = use_ssml
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for efficiency."""
        self._decorative_re = [re.compile(p, re.MULTILINE) for p in self.DECORATIVE_SEPARATORS]
        self._isolated_punct_re = re.compile(self.ISOLATED_PUNCTUATION, re.MULTILINE)

        self._pause_re = []
        for pattern, replacement in self.PAUSE_PATTERNS:
            self._pause_re.append((re.compile(pattern), replacement))

        self._symbol_re = []
        for item in self.SPOKEN_SYMBOL_CLEANUP:
            if len(item) == 2:
                pattern, replacement = item
                self._symbol_re.append((re.compile(pattern), replacement))
            else:
                pattern, replacement, flags = item
                self._symbol_re.append((re.compile(pattern, flags), replacement))

        # Compile scripture patterns
        # Pattern: BookName Chapter:VerseStart-VerseEnd (range)
        self._scripture_range_re = re.compile(
            rf'({self.BIBLE_BOOKS})\s+(\d+):(\d+)-(\d+)',
            re.IGNORECASE
        )
        # Pattern: BookName Chapter:Verse (single verse)
        self._scripture_single_re = re.compile(
            rf'({self.BIBLE_BOOKS})\s+(\d+):(\d+)(?!-)',
            re.IGNORECASE
        )

    def _normalize_scripture_references(self, text: str) -> str:
        """
        Normalize Bible scripture references for natural TTS reading.

        Converts:
        - "Psalms 37:7-9" -> "Psalms 37, verses 7 to 9"
        - "John 3:16" -> "John 3, verse 16"

        Args:
            text: Text containing scripture references

        Returns:
            Text with scripture references normalized for speech
        """
        # Handle verse ranges: "Psalms 37:7-9" -> "Psalms 37, verses 7 to 9"
        def replace_range(match):
            book = match.group(1)
            chapter = match.group(2)
            verse_start = match.group(3)
            verse_end = match.group(4)
            return f"{book} {chapter}, verses {verse_start} to {verse_end}"

        text = self._scripture_range_re.sub(replace_range, text)

        # Handle single verses: "John 3:16" -> "John 3, verse 16"
        def replace_single(match):
            book = match.group(1)
            chapter = match.group(2)
            verse = match.group(3)
            return f"{book} {chapter}, verse {verse}"

        text = self._scripture_single_re.sub(replace_single, text)

        return text

    def normalize(self, text: str) -> NormalizedText:
        """
        Normalize text for TTS narration.

        Args:
            text: Raw text to normalize

        Returns:
            NormalizedText with cleaned text and metadata
        """
        if not text:
            return NormalizedText(text="", original_length=0, normalized_length=0)

        original_length = len(text)
        pause_count = 0

        # Step 1: Remove decorative separators
        normalized = text
        for pattern in self._decorative_re:
            normalized = pattern.sub('', normalized)

        # Step 2: Remove isolated punctuation lines
        normalized = self._isolated_punct_re.sub('', normalized)

        # Step 3: Normalize scripture references (must come before symbol cleanup)
        normalized = self._normalize_scripture_references(normalized)

        # Step 4: Clean up symbols that might be spoken
        for pattern, replacement in self._symbol_re:
            normalized = pattern.sub(replacement, normalized)

        # Step 5: Convert punctuation patterns to pauses (if SSML enabled)
        if self.use_ssml:
            for pattern, replacement in self._pause_re:
                matches = pattern.findall(normalized)
                pause_count += len(matches)
                normalized = pattern.sub(replacement, normalized)
        else:
            # Without SSML, just clean up the punctuation
            for pattern, _ in self._pause_re:
                normalized = pattern.sub(' ', normalized)

        # Step 5: Clean up whitespace
        normalized = self._clean_whitespace(normalized)

        # Step 6: Final safety check - remove any remaining problematic patterns
        normalized = self._final_cleanup(normalized)

        return NormalizedText(
            text=normalized,
            has_ssml=self.use_ssml and pause_count > 0,
            pause_count=pause_count,
            original_length=original_length,
            normalized_length=len(normalized)
        )

    def _clean_whitespace(self, text: str) -> str:
        """Clean up whitespace while preserving intentional breaks."""
        # Collapse multiple spaces
        text = re.sub(r' {2,}', ' ', text)

        # Clean up around SSML tags
        text = re.sub(r'\s+(<break[^>]+/>)\s+', r' \1 ', text)

        # Remove leading/trailing whitespace per line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(line for line in lines if line)

        return text.strip()

    def _final_cleanup(self, text: str) -> str:
        """Final safety cleanup to ensure nothing problematic remains."""
        # Remove any remaining standalone special characters
        text = re.sub(r'(?<!\w)[—–-](?!\w)', '', text)

        # Remove orphaned punctuation at start of sentences
        text = re.sub(r'(?<=\s)[,;:](?=\s)', '', text)

        # Ensure sentences end cleanly
        text = re.sub(r'([.!?])\s*[.!?]+', r'\1', text)

        return text

    def generate_book_introduction(
        self,
        title: str,
        author: str,
        narrator: Optional[str] = None
    ) -> str:
        """
        Generate the opening narration for a book.

        Args:
            title: Book title
            author: Author name
            narrator: Optional narrator name

        Returns:
            Introduction text ready for TTS
        """
        # Clean the title and author
        title = self._clean_for_speech(title)
        author = self._clean_for_speech(author)

        if self.use_ssml:
            intro = f'<speak>This is "{title}" <break time="300ms"/> by {author}.'
            if narrator:
                narrator = self._clean_for_speech(narrator)
                intro += f' <break time="200ms"/> Narrated by {narrator}.'
            intro += ' <break time="800ms"/></speak>'
        else:
            intro = f'This is "{title}", by {author}.'
            if narrator:
                intro += f' Narrated by {narrator}.'

        return intro

    def generate_chapter_introduction(
        self,
        chapter_title: str,
        chapter_number: Optional[int] = None
    ) -> str:
        """
        Generate chapter opening narration.

        Args:
            chapter_title: The chapter title
            chapter_number: Optional chapter number

        Returns:
            Chapter introduction ready for TTS
        """
        chapter_title = self._clean_for_speech(chapter_title)

        # Check if title already includes chapter number
        has_chapter_prefix = bool(re.match(
            r'^(chapter|part|section)\s+(\d+|[ivxlc]+)',
            chapter_title,
            re.IGNORECASE
        ))

        if self.use_ssml:
            if has_chapter_prefix:
                intro = f'<speak>{chapter_title}. <break time="1000ms"/></speak>'
            elif chapter_number:
                intro = f'<speak>Chapter {chapter_number}: {chapter_title}. <break time="1000ms"/></speak>'
            else:
                intro = f'<speak>{chapter_title}. <break time="1000ms"/></speak>'
        else:
            if has_chapter_prefix:
                intro = f'{chapter_title}.'
            elif chapter_number:
                intro = f'Chapter {chapter_number}: {chapter_title}.'
            else:
                intro = f'{chapter_title}.'

        return intro

    def _clean_for_speech(self, text: str) -> str:
        """Clean text for direct speech (titles, names)."""
        # Remove file extensions
        text = re.sub(r'\.(pdf|epub|txt|docx?)$', '', text, flags=re.IGNORECASE)

        # Remove version indicators
        text = re.sub(r'[_\s]*(final|v\d+|draft)[\s_]*(\(\d+\))?', '', text, flags=re.IGNORECASE)

        # Clean up underscores and extra spaces
        text = text.replace('_', ' ')
        text = re.sub(r'\s+', ' ', text)

        # Remove leading numbers (like date prefixes)
        text = re.sub(r'^\d{6,8}[_\s]*', '', text)

        return text.strip()

    def prepare_chunk_for_tts(
        self,
        text: str,
        is_first_chunk: bool = False,
        is_chapter_start: bool = False,
        book_title: Optional[str] = None,
        author: Optional[str] = None,
        chapter_title: Optional[str] = None,
        chapter_number: Optional[int] = None
    ) -> str:
        """
        Prepare a chunk for TTS with optional introductions.

        This is the main entry point for preparing text for narration.

        Args:
            text: The chunk text to narrate
            is_first_chunk: If True and book info provided, add book intro
            is_chapter_start: If True and chapter info provided, add chapter intro
            book_title: Book title for introduction
            author: Author name for introduction
            chapter_title: Chapter title for introduction
            chapter_number: Chapter number for introduction

        Returns:
            Fully prepared text ready for TTS
        """
        parts = []

        # Add book introduction if this is the first chunk
        if is_first_chunk and book_title and author:
            intro = self.generate_book_introduction(book_title, author)
            parts.append(intro)

        # Add chapter introduction if this is a chapter start
        if is_chapter_start and chapter_title:
            chapter_intro = self.generate_chapter_introduction(
                chapter_title, chapter_number
            )
            parts.append(chapter_intro)

        # Normalize the main content
        normalized = self.normalize(text)
        if normalized.text:
            parts.append(normalized.text)

        # Combine with appropriate spacing
        if self.use_ssml and len(parts) > 1:
            # Wrap non-SSML parts in speak tags if needed
            result_parts = []
            for part in parts:
                if '<speak>' not in part and part.strip():
                    result_parts.append(f'<speak>{part}</speak>')
                else:
                    result_parts.append(part)
            return ' '.join(result_parts)
        else:
            return ' '.join(parts)

    def validate_output(self, text: str) -> Tuple[bool, list]:
        """
        Validate that normalized text doesn't contain spoken punctuation.

        Args:
            text: Normalized text to validate

        Returns:
            Tuple of (is_valid, list_of_problems)
        """
        problems = []
        text_lower = text.lower()

        for word in self.FORBIDDEN_SPOKEN_WORDS:
            if word in text_lower:
                problems.append(f"Contains forbidden spoken word: '{word}'")

        # Check for patterns that suggest punctuation might be read
        if re.search(r'\b(says?|reads?)\s+(the\s+)?(dash|dot|comma)', text_lower):
            problems.append("Contains phrase suggesting punctuation reading")

        return len(problems) == 0, problems


# Global instance
_normalizer: Optional[TTSTextNormalizer] = None


def get_tts_normalizer(use_ssml: bool = True) -> TTSTextNormalizer:
    """
    Get or create the TTS text normalizer.

    Args:
        use_ssml: Whether to use SSML markup for pauses

    Returns:
        TTSTextNormalizer instance
    """
    global _normalizer

    if _normalizer is None:
        _normalizer = TTSTextNormalizer(use_ssml=use_ssml)

    return _normalizer
