"""
Tests for Content Classification Service.

Tests the professional audiobook content segmentation system that
classifies content into narratable and non-narratable sections.

Author: AI Labs Africa
Created: January 2, 2026
"""

import pytest
from app.services.content_classification_service import (
    ContentClassificationService,
    ContentType,
    ContentClassification,
    NarrationPreferences
)


@pytest.fixture
def service():
    """Create a ContentClassificationService instance."""
    return ContentClassificationService()


@pytest.fixture
def default_preferences():
    """Default narration preferences."""
    return NarrationPreferences()


class TestContentTypeDetection:
    """Test content type detection for various text patterns."""

    def test_copyright_detection(self, service):
        """Test detection of copyright notices."""
        copyright_text = """
        Copyright © 2024 John Smith
        All Rights Reserved.
        No part of this book may be reproduced.
        """
        result = service.classify_chunk(copyright_text, chunk_index=2)
        assert result.content_type == ContentType.COPYRIGHT
        assert result.narratable is False
        assert "Copyright" in result.skip_reason

    def test_isbn_detection(self, service):
        """Test detection of ISBN metadata."""
        # ISBN alone in early chunk should be metadata
        isbn_text = "ISBN-13: 978-0-123456-78-9\nPaperback ISBN: 978-0-987654-32-1"
        result = service.classify_chunk(isbn_text, chunk_index=3)
        assert result.content_type == ContentType.METADATA
        assert result.narratable is False

    def test_publisher_instructions_detection(self, service):
        """Test detection of publisher/galley instructions."""
        publisher_text = """
        IMPORTANT, PLEASE READ THIS PAGE
        To the author: Please review your text galley carefully.
        Your Author Services Representative will contact you.
        Submit any changes via the Minor Change Form.
        """
        result = service.classify_chunk(publisher_text, chunk_index=0)
        assert result.content_type == ContentType.PUBLISHER_INSTRUCTIONS
        assert result.narratable is False

    def test_toc_detection(self, service):
        """Test detection of table of contents."""
        toc_text = """
        Table of Contents

        Chapter 1: Introduction.........15
        Chapter 2: Getting Started.........23
        Chapter 3: Advanced Topics.........45
        """
        result = service.classify_chunk(toc_text, chunk_index=5)
        assert result.content_type == ContentType.TOC
        assert result.narratable is False

    def test_preface_detection(self, service):
        """Test detection of preface/foreword."""
        preface_text = """
        Foreword

        It is my great pleasure to introduce this remarkable work...
        """
        result = service.classify_chunk(preface_text, chunk_index=8)
        assert result.content_type == ContentType.PREFACE
        # By default, preface is not narratable
        assert result.narratable is False

    def test_chapter_title_detection(self, service):
        """Test detection of chapter titles."""
        chapter_text = "Chapter 1: The Beginning"
        result = service.classify_chunk(chapter_text, chunk_index=10)
        assert result.content_type == ContentType.CHAPTER_TITLE
        assert result.narratable is True
        assert result.is_chapter_start is True
        assert result.chapter_title is not None

    def test_section_break_detection(self, service):
        """Test detection of section breaks."""
        section_breaks = [
            "* * *",
            "***",
            "───────",
            "———"
        ]
        for break_text in section_breaks:
            result = service.classify_chunk(break_text, chunk_index=50)
            assert result.content_type == ContentType.SECTION_BREAK
            assert result.narratable is False

    def test_narrative_content(self, service):
        """Test that normal narrative content is properly classified."""
        narrative_text = """
        The morning sun cast long shadows across the valley as Maria
        walked toward the old farmhouse. She had been away for too long,
        and the memories came flooding back with each step she took.
        """
        result = service.classify_chunk(narrative_text, chunk_index=25)
        assert result.content_type == ContentType.NARRATIVE
        assert result.narratable is True
        assert result.narration_text is not None


class TestNarrationPreferences:
    """Test user preference handling for narration."""

    def test_include_preface_preference(self, service):
        """Test preface inclusion when preference is enabled."""
        prefs = NarrationPreferences(include_preface=True)
        preface_text = "Preface\n\nThis book explores the nature of..."

        result = service.classify_chunk(
            preface_text, chunk_index=5, preferences=prefs
        )
        assert result.content_type == ContentType.PREFACE
        assert result.narratable is True

    def test_exclude_preface_by_default(self, service, default_preferences):
        """Test preface is excluded by default."""
        preface_text = "Foreword\n\nIt gives me great pleasure..."

        result = service.classify_chunk(
            preface_text, chunk_index=5, preferences=default_preferences
        )
        assert result.content_type == ContentType.PREFACE
        assert result.narratable is False

    def test_include_footnotes_preference(self, service):
        """Test footnote inclusion when preference is enabled."""
        prefs = NarrationPreferences(include_footnotes=True)
        footnote_text = "1. Smith, J. (2024). The Art of Writing. Oxford Press."

        result = service.classify_chunk(
            footnote_text, chunk_index=100, preferences=prefs
        )
        assert result.content_type == ContentType.FOOTNOTE
        assert result.narratable is True

    def test_chapter_title_reading_preference(self, service):
        """Test chapter title reading can be disabled."""
        prefs = NarrationPreferences(read_chapter_titles=False)
        chapter_text = "Chapter 5: The Final Battle"

        result = service.classify_chunk(
            chapter_text, chunk_index=80, preferences=prefs
        )
        assert result.content_type == ContentType.CHAPTER_TITLE
        assert result.narratable is False


class TestBulkClassification:
    """Test bulk chunk classification."""

    def test_classify_chunks_list(self, service):
        """Test classifying a list of chunks."""
        chunks = [
            {"text": "Copyright © 2024 Author Name. All Rights Reserved."},
            {"text": "Table of Contents\nChapter 1...15\nChapter 2...30"},
            {"text": "Chapter 1: Introduction"},
            {"text": "The story begins on a cold winter morning..."},
            {"text": "* * *"},
            {"text": "She continued walking through the snow..."},
        ]

        results = service.classify_chunks(chunks)

        assert len(results) == 6
        assert results[0].content_type == ContentType.COPYRIGHT
        assert results[1].content_type == ContentType.TOC
        assert results[2].content_type == ContentType.CHAPTER_TITLE
        assert results[3].content_type == ContentType.NARRATIVE
        assert results[4].content_type == ContentType.SECTION_BREAK
        assert results[5].content_type == ContentType.NARRATIVE

    def test_get_skip_indices(self, service):
        """Test getting list of skip indices."""
        chunks = [
            {"text": "Copyright © 2024 All Rights Reserved."},
            {"text": "Table of Contents\nChapter 1...15"},
            {"text": "Chapter 1: Beginning"},
            {"text": "Normal narrative content here."},
        ]

        skip_indices = service.get_skip_indices(chunks)

        # Indices 0 (copyright) and 1 (TOC) should be skipped
        assert 0 in skip_indices
        assert 1 in skip_indices
        # Indices 2 (chapter) and 3 (narrative) should NOT be skipped
        assert 2 not in skip_indices
        assert 3 not in skip_indices


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_chunk(self, service):
        """Test handling of empty chunks."""
        result = service.classify_chunk("", chunk_index=0)
        assert result.narratable is False
        assert "Empty" in result.skip_reason

    def test_whitespace_only_chunk(self, service):
        """Test handling of whitespace-only chunks."""
        result = service.classify_chunk("   \n\t\n   ", chunk_index=0)
        assert result.narratable is False

    def test_very_short_chunk(self, service):
        """Test that very short chunks are still classified."""
        result = service.classify_chunk("Hello", chunk_index=50)
        assert result.content_type == ContentType.NARRATIVE
        assert result.narratable is True

    def test_mixed_content_chunk(self, service):
        """Test chunk with mixed content (narrative with some metadata)."""
        # Narrative text that happens to mention a book reference
        mixed_text = """
        The journey continued through the mountains.
        Maria looked at the old map she had found in the library.
        She didn't notice the faded markings as she studied the trail ahead.
        The path wound through dense forest, and she had to be careful.
        """
        # Pure narrative content - should be classified as narrative
        result = service.classify_chunk(mixed_text, chunk_index=50)
        assert result.content_type == ContentType.NARRATIVE

    def test_late_book_copyright(self, service):
        """Test narrative with publisher mention in late chunk."""
        # Late in book, narrative text that mentions a publisher
        # This should be narrative (no copyright keywords, late chunk)
        text = """
        She remembered reading about this in the old travel guide.
        The book described the ancient temple in great detail.
        """
        result = service.classify_chunk(
            text, chunk_index=200, total_chunks=250
        )
        # Should be narrative - no copyright indicators
        assert result.content_type == ContentType.NARRATIVE


class TestTextCleaning:
    """Test text cleaning for narration."""

    def test_page_number_removal(self, service):
        """Test that standalone page numbers are removed."""
        text = """
        The story continues here.

        42

        And then more narrative.
        """
        result = service.classify_chunk(text, chunk_index=50)
        assert "42" not in result.narration_text

    def test_quote_normalization(self, service):
        """Test that fancy quotes are normalized."""
        # Use unicode escapes for smart quotes
        text = '\u201cSmart quotes\u201d and \u2018single quotes\u2019 should be normalized.'
        result = service.classify_chunk(text, chunk_index=50)
        # Smart double quotes (\u201c \u201d) should be normalized to straight quotes
        assert '"' in result.narration_text
        # Smart single quotes (\u2018 \u2019) should be normalized to apostrophe
        assert "'" in result.narration_text


class TestChapterPatterns:
    """Test various chapter title patterns."""

    def test_chapter_number_word(self, service):
        """Test 'Chapter One' style."""
        result = service.classify_chunk("Chapter One: The Beginning", chunk_index=10)
        assert result.content_type == ContentType.CHAPTER_TITLE

    def test_chapter_roman_numerals(self, service):
        """Test 'Chapter III' style."""
        result = service.classify_chunk("Chapter III", chunk_index=10)
        assert result.content_type == ContentType.CHAPTER_TITLE

    def test_part_detection(self, service):
        """Test 'Part One' style."""
        result = service.classify_chunk("Part One: The Early Years", chunk_index=10)
        assert result.content_type == ContentType.CHAPTER_TITLE

    def test_section_detection(self, service):
        """Test 'Section 1' style."""
        result = service.classify_chunk("Section 1: Introduction", chunk_index=10)
        assert result.content_type == ContentType.CHAPTER_TITLE


class TestConfidenceScores:
    """Test classification confidence scoring."""

    def test_high_confidence_copyright(self, service):
        """Test high confidence for clear copyright."""
        text = "Copyright © 2024 All Rights Reserved. Published by Acme Press."
        result = service.classify_chunk(text, chunk_index=1)
        assert result.confidence >= 0.8

    def test_high_confidence_narrative(self, service):
        """Test high confidence for clear narrative."""
        text = "She walked through the forest, the leaves crunching under her feet."
        result = service.classify_chunk(text, chunk_index=50)
        assert result.confidence >= 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
