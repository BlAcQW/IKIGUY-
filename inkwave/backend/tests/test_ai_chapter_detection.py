"""
Test AI Chapter Detection Service.

Tests for AI-enhanced chapter detection using Gemini.
Tests both the AI detection and regex fallback behavior.

Author: AI Labs Africa
Created: November 30, 2025
"""

import pytest
import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, '/opt/kasaai/apps')


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Sample text chunks for testing
STANDARD_CHAPTER_CHUNKS = [
    {"content": "Introduction\n\nThis is the introduction to the book."},
    {"content": "Chapter 1: The Beginning\n\nIt all started on a rainy day in London."},
    {"content": "The story continues with more interesting developments."},
    {"content": "Chapter 2: The Journey\n\nOur heroes set off on their adventure."},
    {"content": "They traveled through mountains and valleys."},
    {"content": "Chapter 3: The Challenge\n\nA great obstacle appeared before them."},
    {"content": "They had to overcome many difficulties."},
    {"content": "Chapter 4: The Resolution\n\nFinally, they found the answer."},
    {"content": "The conclusion was satisfying for all."},
]

NON_STANDARD_CHAPTER_CHUNKS = [
    {"content": "PROLOGUE\n\nBefore the main story begins..."},
    {"content": "The Dawn of Change\n\nA new era was beginning."},
    {"content": "More content about the changing world."},
    {"content": "Into the Unknown\n\nVenturing beyond familiar boundaries."},
    {"content": "The adventure deepens."},
    {"content": "INTERLUDE: A Moment of Reflection\n\nPausing to consider what had passed."},
    {"content": "Reflections continue."},
    {"content": "The Final Stand\n\nEverything came down to this moment."},
    {"content": "EPILOGUE\n\nAfter all was said and done..."},
]

SINGLE_CHAPTER_CHUNKS = [
    {"content": "This is a book with no chapter headings."},
    {"content": "It continues as one long narrative."},
    {"content": "More content without breaks."},
    {"content": "Still more content."},
    {"content": "The story ends here."},
]


class TestRegexChapterDetection:
    """Test regex-based chapter detection."""

    @pytest.mark.asyncio
    async def test_detect_standard_chapters(self):
        """Test detecting standard chapter formats."""
        from app.services.ai_chapter_detection_service import AIChapterDetectionService

        service = AIChapterDetectionService()
        chapters = service._detect_chapters_regex(STANDARD_CHAPTER_CHUNKS)

        assert len(chapters) == 4
        assert chapters[0]["title"] == "Chapter 1: The Beginning"
        assert chapters[0]["chunk_index"] == 1
        assert chapters[0]["confidence"] == "high"

    @pytest.mark.asyncio
    async def test_detect_chapters_with_roman_numerals(self):
        """Test detecting chapters with Roman numeral formats."""
        from app.services.ai_chapter_detection_service import AIChapterDetectionService

        roman_chunks = [
            {"content": "Part I\n\nThe first part of the story."},
            {"content": "Content of part one."},
            {"content": "Part II: The Continuation\n\nThe story continues."},
            {"content": "More content."},
            {"content": "Part III\n\nThe final part."},
        ]

        service = AIChapterDetectionService()
        chapters = service._detect_chapters_regex(roman_chunks)

        assert len(chapters) == 3
        assert "Part I" in chapters[0]["title"]
        assert "Part II" in chapters[1]["title"]
        assert "Part III" in chapters[2]["title"]

    @pytest.mark.asyncio
    async def test_detect_section_format(self):
        """Test detecting Section format chapters."""
        from app.services.ai_chapter_detection_service import AIChapterDetectionService

        section_chunks = [
            {"content": "Section 1: Introduction\n\nIntroducing the topic."},
            {"content": "More introduction content."},
            {"content": "Section 2: Main Discussion\n\nThe core content."},
            {"content": "Discussion continues."},
        ]

        service = AIChapterDetectionService()
        chapters = service._detect_chapters_regex(section_chunks)

        assert len(chapters) == 2
        assert "Section 1" in chapters[0]["title"]
        assert "Section 2" in chapters[1]["title"]

    @pytest.mark.asyncio
    async def test_skip_toc_entries(self):
        """Test that table of contents entries are skipped."""
        from app.services.ai_chapter_detection_service import AIChapterDetectionService

        toc_chunks = [
            {"content": "Table of Contents\n\nChapter 1..............5\nChapter 2..............15\nChapter 3..............25"},
            {"content": "Chapter 1: The Real Chapter\n\nActual content starts here."},
            {"content": "More content."},
        ]

        service = AIChapterDetectionService()
        chapters = service._detect_chapters_regex(toc_chunks)

        # Should only detect the real chapter, not TOC entries
        assert len(chapters) == 1
        assert chapters[0]["title"] == "Chapter 1: The Real Chapter"
        assert chapters[0]["chunk_index"] == 1

    @pytest.mark.asyncio
    async def test_no_chapters_detected(self):
        """Test behavior when no chapters are detected."""
        from app.services.ai_chapter_detection_service import AIChapterDetectionService

        service = AIChapterDetectionService()
        chapters = service._detect_chapters_regex(SINGLE_CHAPTER_CHUNKS)

        # Should return empty list when no chapters found
        assert len(chapters) == 0

    @pytest.mark.asyncio
    async def test_case_insensitive_detection(self):
        """Test case-insensitive chapter detection."""
        from app.services.ai_chapter_detection_service import AIChapterDetectionService

        mixed_case_chunks = [
            {"content": "CHAPTER ONE\n\nAll caps chapter."},
            {"content": "Content."},
            {"content": "chapter two: lowercase\n\nLowercase chapter."},
            {"content": "More content."},
            {"content": "ChApTeR Three\n\nMixed case chapter."},
        ]

        service = AIChapterDetectionService()
        chapters = service._detect_chapters_regex(mixed_case_chunks)

        assert len(chapters) == 3


class TestAIChapterDetectionAvailability:
    """Test AI service availability check."""

    @pytest.mark.asyncio
    async def test_service_availability(self):
        """Test checking if AI service is available."""
        from app.services.ai_chapter_detection_service import AIChapterDetectionService

        service = AIChapterDetectionService()
        is_available = service.is_available()

        # Should return boolean based on Gemini configuration
        assert isinstance(is_available, bool)


class TestDetectChaptersWithFallback:
    """Test the hybrid detection with fallback."""

    @pytest.mark.asyncio
    async def test_fallback_uses_regex_when_ai_disabled(self):
        """Test that regex is used when AI is disabled."""
        from app.services.ai_chapter_detection_service import AIChapterDetectionService

        service = AIChapterDetectionService()
        chapters = await service.detect_chapters_with_fallback(
            chunks=STANDARD_CHAPTER_CHUNKS,
            book_title="Test Book",
            use_ai=False
        )

        assert len(chapters) == 4
        assert chapters[0]["title"] == "Chapter 1: The Beginning"

    @pytest.mark.asyncio
    async def test_fallback_returns_regex_when_multiple_found(self):
        """Test that regex results are returned when multiple chapters found."""
        from app.services.ai_chapter_detection_service import AIChapterDetectionService

        service = AIChapterDetectionService()

        # First check regex detection
        regex_chapters = service._detect_chapters_regex(STANDARD_CHAPTER_CHUNKS)
        assert len(regex_chapters) > 1

        # With use_ai=True but regex finds >1 chapters, should return regex results
        chapters = await service.detect_chapters_with_fallback(
            chunks=STANDARD_CHAPTER_CHUNKS,
            book_title="Test Book",
            use_ai=True
        )

        # Should return the regex results since they found multiple chapters
        assert len(chapters) >= 4


class TestAIResponseParsing:
    """Test AI response parsing."""

    @pytest.mark.asyncio
    async def test_parse_valid_json_response(self):
        """Test parsing valid JSON response from AI."""
        from app.services.ai_chapter_detection_service import AIChapterDetectionService

        service = AIChapterDetectionService()

        valid_response = '''
        {
            "chapters": [
                {"chunk_index": 0, "title": "Prologue", "confidence": "high"},
                {"chunk_index": 3, "title": "Chapter 1: The Beginning", "confidence": "high"}
            ]
        }
        '''

        chapters = service._parse_ai_response(valid_response)

        assert len(chapters) == 2
        assert chapters[0]["chunk_index"] == 0
        assert chapters[0]["title"] == "Prologue"
        assert chapters[1]["chunk_index"] == 3

    @pytest.mark.asyncio
    async def test_parse_json_with_markdown_wrapper(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        from app.services.ai_chapter_detection_service import AIChapterDetectionService

        service = AIChapterDetectionService()

        markdown_response = '''```json
        {
            "chapters": [
                {"chunk_index": 0, "title": "Introduction", "confidence": "medium"}
            ]
        }
        ```'''

        chapters = service._parse_ai_response(markdown_response)

        assert len(chapters) == 1
        assert chapters[0]["title"] == "Introduction"

    @pytest.mark.asyncio
    async def test_parse_empty_chapters_response(self):
        """Test parsing response with no chapters."""
        from app.services.ai_chapter_detection_service import AIChapterDetectionService

        service = AIChapterDetectionService()

        empty_response = '{"chapters": []}'
        chapters = service._parse_ai_response(empty_response)

        assert len(chapters) == 0

    @pytest.mark.asyncio
    async def test_parse_invalid_json_response(self):
        """Test handling of invalid JSON response."""
        from app.services.ai_chapter_detection_service import AIChapterDetectionService

        service = AIChapterDetectionService()

        invalid_response = "This is not valid JSON at all"
        chapters = service._parse_ai_response(invalid_response)

        # Should return empty list on parse failure
        assert len(chapters) == 0

    @pytest.mark.asyncio
    async def test_parse_response_with_missing_fields(self):
        """Test handling of response with missing required fields."""
        from app.services.ai_chapter_detection_service import AIChapterDetectionService

        service = AIChapterDetectionService()

        incomplete_response = '''
        {
            "chapters": [
                {"chunk_index": 0},
                {"title": "No Index"},
                {"chunk_index": 2, "title": "Complete", "confidence": "high"}
            ]
        }
        '''

        chapters = service._parse_ai_response(incomplete_response)

        # Should only return valid chapter entries
        assert len(chapters) == 1
        assert chapters[0]["title"] == "Complete"

    @pytest.mark.asyncio
    async def test_chapter_title_truncation(self):
        """Test that long chapter titles are truncated."""
        from app.services.ai_chapter_detection_service import AIChapterDetectionService

        service = AIChapterDetectionService()

        long_title = "A" * 200  # 200 character title
        response = f'{{"chapters": [{{"chunk_index": 0, "title": "{long_title}"}}]}}'

        chapters = service._parse_ai_response(response)

        assert len(chapters) == 1
        assert len(chapters[0]["title"]) == 100  # Should be truncated to 100


class TestPromptBuilding:
    """Test prompt building for AI."""

    @pytest.mark.asyncio
    async def test_build_detection_prompt(self):
        """Test that detection prompt is properly formatted."""
        from app.services.ai_chapter_detection_service import AIChapterDetectionService

        service = AIChapterDetectionService()

        chunk_texts = [
            "[CHUNK 0]\nIntroduction content here...",
            "[CHUNK 1]\nChapter 1: The Beginning..."
        ]

        prompt = service._build_detection_prompt(chunk_texts, "My Test Book")

        assert "My Test Book" in prompt
        assert "[CHUNK 0]" in prompt
        assert "[CHUNK 1]" in prompt
        assert "JSON" in prompt
        assert "chapters" in prompt

    @pytest.mark.asyncio
    async def test_prompt_includes_instructions(self):
        """Test that prompt includes detection instructions."""
        from app.services.ai_chapter_detection_service import AIChapterDetectionService

        service = AIChapterDetectionService()

        chunk_texts = ["[CHUNK 0]\nSample text"]
        prompt = service._build_detection_prompt(chunk_texts, "Test")

        # Should include various chapter format instructions
        assert "Chapter" in prompt
        assert "Part" in prompt
        assert "confidence" in prompt.lower()


class TestServiceSingleton:
    """Test service singleton pattern."""

    @pytest.mark.asyncio
    async def test_get_service_returns_same_instance(self):
        """Test that get_ai_chapter_detection_service returns same instance."""
        from app.services.ai_chapter_detection_service import (
            get_ai_chapter_detection_service,
            _ai_chapter_service
        )

        # Reset global instance
        import app.services.ai_chapter_detection_service as module
        module._ai_chapter_service = None

        service1 = await get_ai_chapter_detection_service()
        service2 = await get_ai_chapter_detection_service()

        assert service1 is service2


class TestIntegrationWithBookProcessingService:
    """Test integration with book processing service."""

    @pytest.mark.asyncio
    async def test_convert_ai_chapters_to_book_chapters(self):
        """Test converting AI detection results to BookChapter objects."""
        from app.services.book_processing_service import BookProcessingService

        service = BookProcessingService()

        ai_chapters = [
            {"chunk_index": 0, "title": "Introduction", "confidence": "high"},
            {"chunk_index": 3, "title": "Chapter 1", "confidence": "high"},
            {"chunk_index": 6, "title": "Chapter 2", "confidence": "medium"},
        ]

        # Create mock chunks
        chunks = [{"content": f"Chunk {i} content " * 20} for i in range(10)]

        book_chapters = service._convert_ai_chapters_to_book_chapters(ai_chapters, chunks)

        assert len(book_chapters) == 3
        assert book_chapters[0].title == "Introduction"
        assert book_chapters[0].id == "ch_1"
        assert book_chapters[0].order == 1
        assert book_chapters[0].start_chunk_id == 0
        assert book_chapters[0].end_chunk_id == 2  # Before next chapter

        assert book_chapters[1].title == "Chapter 1"
        assert book_chapters[1].start_chunk_id == 3
        assert book_chapters[1].end_chunk_id == 5

        assert book_chapters[2].title == "Chapter 2"
        assert book_chapters[2].start_chunk_id == 6
        assert book_chapters[2].end_chunk_id == 9  # Last chunk

    @pytest.mark.asyncio
    async def test_convert_empty_ai_chapters(self):
        """Test converting empty AI results."""
        from app.services.book_processing_service import BookProcessingService

        service = BookProcessingService()

        # Empty AI results with chunks should create default chapter
        chunks = [{"content": "Some content"} for _ in range(5)]
        book_chapters = service._convert_ai_chapters_to_book_chapters([], chunks)

        assert len(book_chapters) == 1
        assert book_chapters[0].title == "Full Book"
        assert book_chapters[0].start_chunk_id == 0
        assert book_chapters[0].end_chunk_id == 4

    @pytest.mark.asyncio
    async def test_word_count_calculation(self):
        """Test that word counts are calculated correctly."""
        from app.services.book_processing_service import BookProcessingService

        service = BookProcessingService()

        ai_chapters = [
            {"chunk_index": 0, "title": "Chapter 1", "confidence": "high"},
        ]

        # Create chunks with known word counts
        chunks = [
            {"content": "one two three four five"},  # 5 words
            {"content": "six seven eight nine ten"},  # 5 words
            {"content": "eleven twelve thirteen"},  # 3 words
        ]

        book_chapters = service._convert_ai_chapters_to_book_chapters(ai_chapters, chunks)

        assert len(book_chapters) == 1
        assert book_chapters[0].word_count == 13  # Total words


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
