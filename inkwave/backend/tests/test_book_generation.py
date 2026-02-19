"""
Tests for book generation and audio duration.

This module tests:
1. Demo book generation
2. Word count verification
3. Audio duration estimates
4. Content validation
"""

import pytest
import os
import PyPDF2
from pathlib import Path


class TestBookGeneration:
    """Test book generation functionality."""

    @pytest.fixture
    def demo_book_path(self):
        """Get path to demo book."""
        return Path(__file__).parent.parent / "test_books" / "binding_the_strong_man_demo.pdf"

    def test_demo_book_exists(self, demo_book_path):
        """
        Test that demo book file exists.

        Args:
            demo_book_path: Path to demo book PDF

        Expected:
            File should exist
        """
        assert demo_book_path.exists(), "Demo book PDF should exist"

    def test_demo_book_word_count(self, demo_book_path):
        """
        Test that demo book has sufficient word count for 5+ minutes of audio.

        Args:
            demo_book_path: Path to demo book PDF

        Expected:
            Word count should be at least 750 words (5 min at 150 wpm)
        """
        with open(demo_book_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            total_text = ""
            for page in pdf_reader.pages:
                total_text += page.extract_text()

            words = total_text.split()
            word_count = len(words)

            # For 5+ minutes of audio at 150 words/min, we need at least 750 words
            # But we want significantly more for quality testing
            assert word_count >= 3000, f"Book should have at least 3000 words for adequate testing, got {word_count}"

    def test_demo_book_audio_duration(self, demo_book_path):
        """
        Test that demo book has sufficient content for 5+ minutes per chapter.

        Args:
            demo_book_path: Path to demo book PDF

        Expected:
            Total duration should be at least 20 minutes (5 min × 4 chapters)
        """
        with open(demo_book_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            total_text = ""
            for page in pdf_reader.pages:
                total_text += page.extract_text()

            words = total_text.split()
            word_count = len(words)

            # Estimate duration at 150 words per minute
            duration_minutes = word_count / 150

            # Should have at least 20 minutes total (5 min × 4 chapters)
            assert duration_minutes >= 20, f"Book should provide at least 20 minutes of audio, got {duration_minutes:.1f}"

    def test_demo_book_page_count(self, demo_book_path):
        """
        Test that demo book has reasonable page count.

        Args:
            demo_book_path: Path to demo book PDF

        Expected:
            Should have at least 10 pages
        """
        with open(demo_book_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            page_count = len(pdf_reader.pages)

            assert page_count >= 10, f"Book should have at least 10 pages, got {page_count}"

    def test_demo_book_content_quality(self, demo_book_path):
        """
        Test that demo book has quality content.

        Args:
            demo_book_path: Path to demo book PDF

        Expected:
            Should have chapters and meaningful content
        """
        with open(demo_book_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            total_text = ""
            for page in pdf_reader.pages:
                total_text += page.extract_text()

            # Check for chapter markers
            assert "Chapter 1" in total_text, "Should contain Chapter 1"
            assert "Chapter 2" in total_text, "Should contain Chapter 2"
            assert "Chapter 3" in total_text, "Should contain Chapter 3"
            assert "Chapter 4" in total_text, "Should contain Chapter 4"

            # Check for biblical references
            assert "Ephesians" in total_text, "Should contain biblical references"
            assert "Matthew" in total_text, "Should contain biblical references"

    def test_demo_book_file_size(self, demo_book_path):
        """
        Test that demo book has reasonable file size.

        Args:
            demo_book_path: Path to demo book PDF

        Expected:
            File size should be reasonable (not too small or too large)
        """
        file_size = os.path.getsize(demo_book_path)
        file_size_kb = file_size / 1024

        # Should be at least 15 KB for substantial content
        assert file_size_kb >= 15, f"File size should be at least 15 KB, got {file_size_kb:.2f} KB"

        # Should not be excessively large (> 1 MB)
        assert file_size_kb <= 1024, f"File size should not exceed 1 MB, got {file_size_kb:.2f} KB"

    def test_words_per_chapter_estimate(self, demo_book_path):
        """
        Test that each chapter has sufficient words for 5+ minutes.

        Args:
            demo_book_path: Path to demo book PDF

        Expected:
            Average words per chapter should be at least 750 (5 min at 150 wpm)
        """
        with open(demo_book_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            total_text = ""
            for page in pdf_reader.pages:
                total_text += page.extract_text()

            words = total_text.split()
            word_count = len(words)

            # Estimate with 4 chapters
            avg_words_per_chapter = word_count / 4

            # Each chapter should average at least 750 words for 5 minutes
            assert avg_words_per_chapter >= 750, \
                f"Average words per chapter should be at least 750 for 5+ min audio, got {avg_words_per_chapter:.0f}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
