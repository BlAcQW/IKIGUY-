"""
Content Classification Service for InkWave.

Professional audiobook content segmentation system that classifies book content
into narratable and non-narratable sections, comparable to Libby and Audible.

Content Types:
- NARRATIVE: Main story content (narratable)
- CHAPTER_TITLE: Chapter headers (narratable, read once)
- SECTION_BREAK: Scene transitions (silent pause)
- FRONT_MATTER: Title page, dedication, acknowledgments
- COPYRIGHT: Copyright notices, legal text
- TOC: Table of contents
- METADATA: ISBN, publisher info
- PREFACE: Foreword, preface, editor notes
- FOOTNOTE: Footnotes and endnotes
- REFERENCE: Bibliography, references, index
- APPENDIX: Appendix material

Author: AI Labs Africa
Created: January 2, 2026
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Content type classification for book chunks."""

    # Narratable content types
    NARRATIVE = "narrative"           # Main story/content - always narrated
    CHAPTER_TITLE = "chapter_title"   # Chapter headers - read once, cleanly

    # Non-narratable by default (can be toggled)
    SECTION_BREAK = "section_break"   # Scene breaks (***) - silent pause
    FRONT_MATTER = "front_matter"     # Title page, dedication
    PREFACE = "preface"               # Foreword, preface, editor notes
    FOOTNOTE = "footnote"             # Footnotes and endnotes
    APPENDIX = "appendix"             # Appendix material

    # Never narratable
    COPYRIGHT = "copyright"           # Copyright notices, legal text
    TOC = "toc"                       # Table of contents
    METADATA = "metadata"             # ISBN, publisher info, edition notes
    REFERENCE = "reference"           # Bibliography, references, index
    PUBLISHER_INSTRUCTIONS = "publisher_instructions"  # Galley/review instructions


class ContentClassification(BaseModel):
    """Classification result for a text chunk."""

    content_type: ContentType = Field(
        default=ContentType.NARRATIVE,
        description="Classified content type"
    )
    narratable: bool = Field(
        default=True,
        description="Whether this chunk should be narrated"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Classification confidence (0.0-1.0)"
    )
    narration_text: Optional[str] = Field(
        default=None,
        description="Cleaned text for narration (may differ from original)"
    )
    skip_reason: Optional[str] = Field(
        default=None,
        description="Reason for skipping narration (if narratable=False)"
    )
    is_chapter_start: bool = Field(
        default=False,
        description="True if this chunk starts a new chapter"
    )
    chapter_title: Optional[str] = Field(
        default=None,
        description="Clean chapter title if detected"
    )


class NarrationPreferences(BaseModel):
    """User preferences for narration content."""

    include_preface: bool = Field(
        default=False,
        description="Include preface, foreword, and editor notes"
    )
    include_footnotes: bool = Field(
        default=False,
        description="Include footnotes and endnotes"
    )
    include_appendix: bool = Field(
        default=False,
        description="Include appendix material"
    )
    include_front_matter: bool = Field(
        default=False,
        description="Include title page, dedication, acknowledgments"
    )
    read_chapter_titles: bool = Field(
        default=True,
        description="Read chapter titles aloud"
    )
    pause_at_section_breaks: float = Field(
        default=1.5,
        ge=0.0,
        le=5.0,
        description="Pause duration in seconds at section breaks"
    )


class ContentClassificationService:
    """
    Service for classifying book content for professional narration.

    Uses pattern matching and heuristics to identify content types,
    with conservative defaults that prioritize narrative content.

    Design Philosophy:
    - When in doubt, classify as NARRATIVE (better to read than skip)
    - Front matter detection is aggressive (first 10 chunks)
    - Copyright/legal detection is strict
    - Chapter titles are extracted cleanly for single reading

    Example:
        >>> service = ContentClassificationService()
        >>> result = service.classify_chunk(
        ...     "Copyright © 2024 All Rights Reserved...",
        ...     chunk_index=2
        ... )
        >>> print(result.content_type)  # ContentType.COPYRIGHT
        >>> print(result.narratable)    # False
    """

    # Patterns for content type detection
    # Order matters - more specific patterns checked first

    COPYRIGHT_PATTERNS = [
        r'copyright\s*[©®]\s*\d{4}',
        r'all\s+rights\s+reserved',
        r'no\s+part\s+of\s+this\s+(?:book|publication)',
        r'reproduced\s+in\s+any\s+form',
        r'permission\s+of\s+the\s+publisher',
        r'printed\s+in\s+(?:the\s+)?(?:united\s+states|usa|uk|nigeria)',
        r'library\s+of\s+congress',
        r'published\s+by\s+[\w\s]+(?:press|publishing|publishers)',
        r'first\s+(?:edition|printing|published)',
        r'goshen\s+publishers',
        r'xulon\s+press',
        r'westbow\s+press',
        r'cover\s+design\s+by',
    ]

    ISBN_PATTERNS = [
        r'isbn[\s:-]*[\d-]{10,17}',
        r'(?:hardcover|paperback|ebook)[\s:]*isbn',
        r'(?:international\s+standard\s+book\s+number)',
    ]

    TOC_PATTERNS = [
        r'^(?:table\s+of\s+)?contents?\s*$',
        r'^contents?\s*$',
        r'chapter\s+\d+[\.:\s]+.+\.{3,}\s*\d+',  # Chapter 1: Title.........15
        r'part\s+(?:one|two|three|i+)\s+\.{3,}',
        r'^\s*\d+\.\s+.+\.{3,}\s*\d+\s*$',       # 1. Title..........12
    ]

    PUBLISHER_INSTRUCTION_PATTERNS = [
        r'please\s+read\s+this\s+page',
        r'text\s+galley',
        r'author\s+services\s+representative',
        r'minor\s+change\s+form',
        r'major\s+changes',
        r'production\s+schedule',
        r'review\s+your\s+galley',
        r'to\s+the\s+author\s*:',
        r'for\s+any\s+future\s+submissions',
        r'manual\s+returns',
    ]

    PREFACE_PATTERNS = [
        r'^(?:fore)?word\s*$',
        r'^preface\s*$',
        r'^introduction\s*$',
        r"^author['\u2019]?s?\s+note\s*$",
        r"^editor['\u2019]?s?\s+note\s*$",
        r'^a\s+note\s+from\s+the\s+author',
        r'^about\s+this\s+book',
    ]

    FRONT_MATTER_PATTERNS = [
        r'^dedication\s*$',
        r'^acknowledgments?\s*$',
        r'^epigraph\s*$',
        r'^for\s+(?:my|all|those|everyone)',  # Dedication starts
        r'^this\s+book\s+is\s+dedicated',
    ]

    REFERENCE_PATTERNS = [
        r'^(?:selected\s+)?bibliography\s*$',
        r'^references?\s*$',
        r'^(?:end)?notes?\s*$',
        r'^index\s*$',
        r'^works?\s+cited\s*$',
        r'^further\s+reading\s*$',
        r'^\d+\.\s+[\w\s]+,\s+\d{4}\.',  # Bibliography entry pattern
    ]

    APPENDIX_PATTERNS = [
        r'^appendix\s*[a-z]?\s*[:\-]?',
        r'^supplement(?:ary)?\s+material',
        r'^additional\s+resources',
    ]

    FOOTNOTE_PATTERNS = [
        r'^\s*\d+\s*[\.\)]\s+',           # 1. or 1)
        r'^\s*\*+\s+',                     # * or ** prefix
        r'^\s*†\s+',                       # Dagger prefix
        r'^\s*‡\s+',                       # Double dagger
    ]

    CHAPTER_PATTERNS = [
        # "Chapter 1", "CHAPTER ONE", "Chapter 1: Title"
        (
            r'^(?:chapter|part|section)\s+'
            r'(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|'
            r'eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|'
            r'eighteen|nineteen|twenty|'
            r'i{1,3}|iv|v|vi{1,3}|ix|x|xi{1,3}|xiv|xv)'
            r'\s*[:\-]?\s*(.*)$'
        ),
        # "CHAPTER 1" all caps
        r'^CHAPTER\s+\d+\s*[:\-]?\s*.*$',
        # Roman numerals standalone: "I", "II", "III"
        r'^[IVXLC]+\s*$',
    ]

    SECTION_BREAK_PATTERNS = [
        r'^\s*\*\s*\*\s*\*\s*$',           # * * *
        r'^\s*\*{3,}\s*$',                  # ***
        r'^\s*─{3,}\s*$',                   # ───
        r'^\s*—{3,}\s*$',                   # ———
        r'^\s*-{3,}\s*$',                   # ---
        r'^\s*~{3,}\s*$',                   # ~~~
        r'^\s*[●•◆◇■□]{1,5}\s*$',           # Decorative bullets
        r'^\s*#\s*$',                       # Single hash (Markdown-style)
    ]

    def __init__(self):
        """Initialize content classification service."""
        # Compile regex patterns for efficiency
        self._copyright_re = [re.compile(p, re.IGNORECASE) for p in self.COPYRIGHT_PATTERNS]
        self._isbn_re = [re.compile(p, re.IGNORECASE) for p in self.ISBN_PATTERNS]
        self._toc_re = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.TOC_PATTERNS]
        self._publisher_re = [re.compile(p, re.IGNORECASE) for p in self.PUBLISHER_INSTRUCTION_PATTERNS]
        self._preface_re = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.PREFACE_PATTERNS]
        self._front_matter_re = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.FRONT_MATTER_PATTERNS]
        self._reference_re = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.REFERENCE_PATTERNS]
        self._appendix_re = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.APPENDIX_PATTERNS]
        self._footnote_re = [re.compile(p, re.MULTILINE) for p in self.FOOTNOTE_PATTERNS]
        self._chapter_re = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.CHAPTER_PATTERNS]
        self._section_break_re = [re.compile(p) for p in self.SECTION_BREAK_PATTERNS]

        logger.info("ContentClassificationService initialized")

    def classify_chunk(
        self,
        text: str,
        chunk_index: int,
        total_chunks: int = 0,
        book_title: str = "",
        preferences: Optional[NarrationPreferences] = None
    ) -> ContentClassification:
        """
        Classify a text chunk for narration.

        Args:
            text: The text content to classify
            chunk_index: Index of this chunk (0-based)
            total_chunks: Total number of chunks in book
            book_title: Book title for context
            preferences: User narration preferences

        Returns:
            ContentClassification with type, narratability, and clean text
        """
        if not text or not text.strip():
            return ContentClassification(
                content_type=ContentType.NARRATIVE,
                narratable=False,
                confidence=1.0,
                skip_reason="Empty chunk"
            )

        text_stripped = text.strip()
        text_lower = text_stripped.lower()

        # Use default preferences if not provided
        prefs = preferences or NarrationPreferences()

        # === Phase 1: Check for never-narratable content ===

        # File/document metadata (very early chunks with filename patterns)
        if self._is_file_metadata(text_stripped, chunk_index):
            return ContentClassification(
                content_type=ContentType.METADATA,
                narratable=False,
                confidence=0.95,
                skip_reason="File/document metadata"
            )

        # Publisher instructions (highest priority - always skip)
        if self._is_publisher_instructions(text_lower):
            return ContentClassification(
                content_type=ContentType.PUBLISHER_INSTRUCTIONS,
                narratable=False,
                confidence=0.95,
                skip_reason="Publisher/review instructions"
            )

        # Copyright and legal text
        if self._is_copyright(text_lower, chunk_index):
            return ContentClassification(
                content_type=ContentType.COPYRIGHT,
                narratable=False,
                confidence=0.9,
                skip_reason="Copyright notice"
            )

        # ISBN and metadata
        if self._is_metadata(text_lower):
            return ContentClassification(
                content_type=ContentType.METADATA,
                narratable=False,
                confidence=0.9,
                skip_reason="ISBN/publication metadata"
            )

        # Table of contents
        if self._is_toc(text_stripped, text_lower, chunk_index):
            return ContentClassification(
                content_type=ContentType.TOC,
                narratable=False,
                confidence=0.85,
                skip_reason="Table of contents"
            )

        # References and index (usually at end)
        if self._is_reference(text_lower, chunk_index, total_chunks):
            return ContentClassification(
                content_type=ContentType.REFERENCE,
                narratable=False,
                confidence=0.85,
                skip_reason="Reference section"
            )

        # === Phase 2: Check for optionally-narratable content ===

        # Section breaks (special handling - silent pause)
        if self._is_section_break(text_stripped):
            return ContentClassification(
                content_type=ContentType.SECTION_BREAK,
                narratable=False,  # Rendered as pause, not read
                confidence=1.0,
                skip_reason="Section break (pause inserted)"
            )

        # Preface/foreword
        if self._is_preface(text_lower, chunk_index):
            return ContentClassification(
                content_type=ContentType.PREFACE,
                narratable=prefs.include_preface,
                confidence=0.8,
                narration_text=text_stripped if prefs.include_preface else None,
                skip_reason=None if prefs.include_preface else "Preface excluded by preference"
            )

        # Front matter (dedication, acknowledgments)
        if self._is_front_matter(text_lower, chunk_index):
            return ContentClassification(
                content_type=ContentType.FRONT_MATTER,
                narratable=prefs.include_front_matter,
                confidence=0.8,
                narration_text=text_stripped if prefs.include_front_matter else None,
                skip_reason=None if prefs.include_front_matter else "Front matter excluded by preference"
            )

        # Appendix
        if self._is_appendix(text_lower, chunk_index, total_chunks):
            return ContentClassification(
                content_type=ContentType.APPENDIX,
                narratable=prefs.include_appendix,
                confidence=0.8,
                narration_text=text_stripped if prefs.include_appendix else None,
                skip_reason=None if prefs.include_appendix else "Appendix excluded by preference"
            )

        # Footnotes (detected by formatting)
        if self._is_footnote(text_stripped, chunk_index):
            return ContentClassification(
                content_type=ContentType.FOOTNOTE,
                narratable=prefs.include_footnotes,
                confidence=0.7,
                narration_text=text_stripped if prefs.include_footnotes else None,
                skip_reason=None if prefs.include_footnotes else "Footnote excluded by preference"
            )

        # === Phase 3: Check for chapter titles ===

        chapter_match = self._extract_chapter_title(text_stripped)
        if chapter_match:
            chapter_title = chapter_match
            return ContentClassification(
                content_type=ContentType.CHAPTER_TITLE,
                narratable=prefs.read_chapter_titles,
                confidence=0.9,
                narration_text=chapter_title if prefs.read_chapter_titles else None,
                is_chapter_start=True,
                chapter_title=chapter_title,
                skip_reason=None if prefs.read_chapter_titles else "Chapter title reading disabled"
            )

        # === Phase 4: Default to narrative content ===

        # Clean the text for narration
        narration_text = self._clean_for_narration(text_stripped)

        return ContentClassification(
            content_type=ContentType.NARRATIVE,
            narratable=True,
            confidence=1.0,
            narration_text=narration_text
        )

    def classify_chunks(
        self,
        chunks: List[Dict],
        book_title: str = "",
        preferences: Optional[NarrationPreferences] = None
    ) -> List[ContentClassification]:
        """
        Classify all chunks in a book.

        Args:
            chunks: List of chunk dicts with 'text' key
            book_title: Book title for context
            preferences: User narration preferences

        Returns:
            List of ContentClassification for each chunk
        """
        total_chunks = len(chunks)
        classifications = []

        for i, chunk in enumerate(chunks):
            text = chunk.get('text', '') or chunk.get('content', '') or str(chunk)
            classification = self.classify_chunk(
                text=text,
                chunk_index=i,
                total_chunks=total_chunks,
                book_title=book_title,
                preferences=preferences
            )
            classifications.append(classification)

        # Post-processing: Mark chapter title readings
        self._mark_chapter_title_readings(classifications)

        return classifications

    def _is_file_metadata(self, text: str, chunk_index: int) -> bool:
        """
        Check if text is file/document metadata (filename, PDF metadata).

        Detects patterns like:
        - Date prefixes: "200313_Title_final (1)"
        - File extensions: "document.pdf by Author"
        - Very short chunks at the start that look like filenames

        Args:
            text: Original text (not lowercased)
            chunk_index: Position in book

        Returns:
            True if this appears to be file metadata
        """
        # Only check first 3 chunks
        if chunk_index > 2:
            return False

        # Very short text (under 100 chars) at start is suspicious
        if len(text) < 100:
            # Date prefix pattern (YYMMDD_ or YYYYMMDD_)
            if re.match(r'^\d{6,8}_', text):
                return True

            # Filename patterns
            if re.search(r'\.(pdf|epub|docx?|txt)\s+(by\s+|$)', text, re.IGNORECASE):
                return True

            # Pattern: "Title_final (1)" or similar version indicators
            if re.search(r'_final\s*\(\d+\)', text, re.IGNORECASE):
                return True

            # Very short with "by Author" at end (often extracted from filename)
            if re.match(r'^[^.]{10,60}\s+by\s+\w+', text) and len(text) < 80:
                return True

        return False

    def _is_publisher_instructions(self, text_lower: str) -> bool:
        """Check if text is publisher/galley instructions."""
        matches = sum(1 for pattern in self._publisher_re if pattern.search(text_lower))
        return matches >= 2  # At least 2 indicators

    def _is_copyright(self, text_lower: str, chunk_index: int) -> bool:
        """Check if text is copyright/legal notice."""
        # More aggressive in early chunks (first 15)
        threshold = 1 if chunk_index < 15 else 2

        matches = sum(1 for pattern in self._copyright_re if pattern.search(text_lower))
        return matches >= threshold

    def _is_metadata(self, text_lower: str) -> bool:
        """Check if text is ISBN/publication metadata."""
        for pattern in self._isbn_re:
            if pattern.search(text_lower):
                return True
        return False

    def _is_toc(self, text: str, text_lower: str, chunk_index: int) -> bool:
        """Check if text is table of contents."""
        # Only check early chunks (first 20)
        if chunk_index > 20:
            return False

        # Explicit "Table of Contents" or "Contents"
        if 'table of contents' in text_lower or text_lower.strip() == 'contents':
            return True

        # Check for TOC patterns
        for pattern in self._toc_re:
            if pattern.search(text):
                return True

        # Heuristic: Lots of dots + page numbers
        dots_count = text.count('...')
        if dots_count > 5 and len(text) < 2000:
            # Check for page number patterns at line ends
            page_numbers = re.findall(r'\.{3,}\s*\d+\s*$', text, re.MULTILINE)
            if len(page_numbers) >= 3:
                return True

        return False

    def _is_reference(self, text_lower: str, chunk_index: int, total_chunks: int) -> bool:
        """Check if text is reference/bibliography section."""
        # Only check late chunks (last 20% of book)
        if total_chunks > 0 and chunk_index < total_chunks * 0.8:
            return False

        for pattern in self._reference_re:
            if pattern.search(text_lower):
                return True
        return False

    def _is_section_break(self, text: str) -> bool:
        """Check if text is a section break marker."""
        # Must be very short
        if len(text.strip()) > 20:
            return False

        for pattern in self._section_break_re:
            if pattern.match(text.strip()):
                return True
        return False

    def _is_preface(self, text_lower: str, chunk_index: int) -> bool:
        """Check if text is preface/foreword content."""
        # Only check early chunks (first 30)
        if chunk_index > 30:
            return False

        for pattern in self._preface_re:
            if pattern.search(text_lower):
                return True
        return False

    def _is_front_matter(self, text_lower: str, chunk_index: int) -> bool:
        """Check if text is front matter (dedication, acknowledgments)."""
        # Only check very early chunks (first 10)
        if chunk_index > 10:
            return False

        for pattern in self._front_matter_re:
            if pattern.search(text_lower):
                return True
        return False

    def _is_appendix(self, text_lower: str, chunk_index: int, total_chunks: int) -> bool:
        """Check if text is appendix material."""
        # Only check late chunks (last 30% of book)
        if total_chunks > 0 and chunk_index < total_chunks * 0.7:
            return False

        for pattern in self._appendix_re:
            if pattern.search(text_lower):
                return True
        return False

    def _is_footnote(self, text: str, chunk_index: int) -> bool:
        """Check if text is a footnote."""
        # Footnotes are usually short
        if len(text) > 500:
            return False

        for pattern in self._footnote_re:
            if pattern.match(text):
                return True
        return False

    def _extract_chapter_title(self, text: str) -> Optional[str]:
        """Extract clean chapter title from text if present."""
        lines = text.strip().split('\n')

        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if not line:
                continue

            for pattern in self._chapter_re:
                match = pattern.match(line)
                if match:
                    # Clean up the title
                    title = line
                    # Remove excessive whitespace
                    title = re.sub(r'\s+', ' ', title)
                    # Limit length
                    if len(title) > 100:
                        title = title[:100].rsplit(' ', 1)[0]
                    return title

        return None

    def _clean_for_narration(self, text: str) -> str:
        """
        Clean text for optimal TTS narration.

        - Removes page numbers
        - Normalizes whitespace
        - Handles common abbreviations
        - Removes formatting artifacts
        """
        cleaned = text

        # Remove standalone page numbers
        cleaned = re.sub(r'^\s*\d+\s*$', '', cleaned, flags=re.MULTILINE)

        # Remove page number headers/footers
        cleaned = re.sub(r'\n\s*\d+\s*\n', '\n', cleaned)

        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # Remove common formatting artifacts
        cleaned = re.sub(r'\s*\|\s*', ' ', cleaned)  # Pipe characters

        # Clean up smart quotes - normalize to straight ASCII quotes
        cleaned = cleaned.replace('\u201c', '"').replace('\u201d', '"')  # Left/right double
        cleaned = cleaned.replace('\u2018', "'").replace('\u2019', "'")  # Left/right single

        return cleaned.strip()

    def _mark_chapter_title_readings(self, classifications: List[ContentClassification]) -> None:
        """
        Post-process to ensure chapter titles are only read once per chapter.

        Modifies classifications in-place.
        """
        current_chapter = None

        for i, classification in enumerate(classifications):
            if classification.content_type == ContentType.CHAPTER_TITLE:
                if classification.chapter_title == current_chapter:
                    # Already read this chapter title, skip it
                    classification.narratable = False
                    classification.skip_reason = "Chapter title already read"
                else:
                    current_chapter = classification.chapter_title

    def get_narratable_chunks(
        self,
        chunks: List[Dict],
        book_title: str = "",
        preferences: Optional[NarrationPreferences] = None
    ) -> List[Tuple[int, str, ContentClassification]]:
        """
        Get only the narratable chunks with their indices.

        Args:
            chunks: List of chunk dicts
            book_title: Book title
            preferences: Narration preferences

        Returns:
            List of (chunk_index, narration_text, classification) tuples
        """
        classifications = self.classify_chunks(chunks, book_title, preferences)

        narratable = []
        for i, (chunk, classification) in enumerate(zip(chunks, classifications)):
            if classification.narratable:
                text = classification.narration_text or chunk.get('text', '')
                narratable.append((i, text, classification))

        return narratable

    def get_skip_indices(
        self,
        chunks: List[Dict],
        book_title: str = "",
        preferences: Optional[NarrationPreferences] = None
    ) -> List[int]:
        """
        Get indices of chunks to skip during narration.

        Args:
            chunks: List of chunk dicts
            book_title: Book title
            preferences: Narration preferences

        Returns:
            List of chunk indices to skip
        """
        classifications = self.classify_chunks(chunks, book_title, preferences)

        return [
            i for i, classification in enumerate(classifications)
            if not classification.narratable
        ]


# Global service instance
_content_classification_service: Optional[ContentClassificationService] = None


def get_content_classification_service() -> ContentClassificationService:
    """
    Get or create content classification service instance.

    Returns:
        ContentClassificationService instance
    """
    global _content_classification_service

    if _content_classification_service is None:
        _content_classification_service = ContentClassificationService()

    return _content_classification_service
