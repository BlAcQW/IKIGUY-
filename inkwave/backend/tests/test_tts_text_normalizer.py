"""
Tests for TTS Text Normalizer.

Verifies that text normalization produces professional audiobook-quality output:
- Punctuation is never spoken
- Decorative separators are removed
- Introductions are properly generated

Author: AI Labs Africa
Created: January 2, 2026
"""

import pytest
from app.services.tts_text_normalizer import TTSTextNormalizer, get_tts_normalizer


@pytest.fixture
def normalizer():
    """Create a normalizer instance."""
    return TTSTextNormalizer(use_ssml=False)


@pytest.fixture
def ssml_normalizer():
    """Create a normalizer with SSML enabled."""
    return TTSTextNormalizer(use_ssml=True)


class TestPunctuationRemoval:
    """Test that punctuation is never spoken."""

    def test_em_dash_removed(self, normalizer):
        """Em-dashes should become pauses, not 'dash'."""
        text = "She walked—slowly—toward the door."
        result = normalizer.normalize(text)

        # Em-dash should be removed
        assert "—" not in result.text
        # Should not contain the word "dash"
        assert "dash" not in result.text.lower()

    def test_ellipsis_removed(self, normalizer):
        """Ellipsis should become pause, not 'dot dot dot'."""
        text = "He wondered... could it be true?"
        result = normalizer.normalize(text)

        # Ellipsis should be removed
        assert "..." not in result.text
        # Should not contain the word "dot"
        assert "dot" not in result.text.lower()

    def test_en_dash_removed(self, normalizer):
        """En-dashes should be removed."""
        text = "Pages 10–20 discuss this topic."
        result = normalizer.normalize(text)

        assert "–" not in result.text

    def test_unicode_ellipsis_removed(self, normalizer):
        """Unicode ellipsis (…) should be removed."""
        text = "She hesitated… then continued."
        result = normalizer.normalize(text)

        assert "…" not in result.text


class TestScriptureReferences:
    """Test Bible scripture reference normalization."""

    def test_psalms_verse_range(self, normalizer):
        """Psalms 37:7-9 should become Psalms 37, verses 7 to 9."""
        text = "Read Psalms 37:7-9 for wisdom."
        result = normalizer.normalize(text)

        assert "Psalms 37, verses 7 to 9" in result.text
        assert "dash" not in result.text.lower()

    def test_john_verse_range(self, normalizer):
        """John 3:16-18 should become John 3, verses 16 to 18."""
        text = "John 3:16-18 tells us about love."
        result = normalizer.normalize(text)

        assert "John 3, verses 16 to 18" in result.text
        assert "dash" not in result.text.lower()

    def test_single_verse(self, normalizer):
        """John 3:16 should become John 3, verse 16."""
        text = "John 3:16 is famous."
        result = normalizer.normalize(text)

        assert "John 3, verse 16" in result.text
        assert "verses" not in result.text  # Should be singular

    def test_genesis_reference(self, normalizer):
        """Genesis 1:1-3 should be properly converted."""
        text = "Genesis 1:1-3 describes creation."
        result = normalizer.normalize(text)

        assert "Genesis 1, verses 1 to 3" in result.text

    def test_abbreviation_ps(self, normalizer):
        """Abbreviated book names like Ps should work."""
        text = "Ps 23:1-6 is comforting."
        result = normalizer.normalize(text)

        assert "Ps 23, verses 1 to 6" in result.text

    def test_multiple_references(self, normalizer):
        """Multiple scripture references in same text."""
        text = "Compare John 3:16 with Romans 8:28-30."
        result = normalizer.normalize(text)

        assert "John 3, verse 16" in result.text
        assert "Romans 8, verses 28 to 30" in result.text


class TestNumberRanges:
    """Test generic number range conversion."""

    def test_simple_number_range(self, normalizer):
        """Simple ranges like 7-9 should become 7 to 9."""
        text = "Chapters 7-9 are important."
        result = normalizer.normalize(text)

        assert "7 to 9" in result.text

    def test_page_range(self, normalizer):
        """Page ranges should be converted."""
        text = "See pages 10-20 for details."
        result = normalizer.normalize(text)

        assert "10 to 20" in result.text


class TestDecorativeSeparators:
    """Test removal of decorative section separators."""

    def test_asterisk_separator_removed(self, normalizer):
        """*** separators should be removed entirely."""
        text = "* * *"
        result = normalizer.normalize(text)
        assert result.text == ""

    def test_dash_separator_removed(self, normalizer):
        """--- separators should be removed entirely."""
        text = "---"
        result = normalizer.normalize(text)
        assert result.text == ""

    def test_underscore_separator_removed(self, normalizer):
        """___ separators should be removed entirely."""
        text = "___"
        result = normalizer.normalize(text)
        assert result.text == ""

    def test_multiple_separators(self, normalizer):
        """Multiple separator types should all be removed."""
        text = """First paragraph.

        * * *

        Second paragraph."""
        result = normalizer.normalize(text)

        assert "* * *" not in result.text
        assert "First paragraph" in result.text
        assert "Second paragraph" in result.text


class TestQuoteNormalization:
    """Test smart quote normalization."""

    def test_smart_double_quotes_normalized(self, normalizer):
        """Smart double quotes should become straight quotes."""
        text = '\u201cHello,\u201d she said.'
        result = normalizer.normalize(text)

        # Smart quotes should be converted
        assert '\u201c' not in result.text
        assert '\u201d' not in result.text
        assert '"' in result.text

    def test_smart_single_quotes_normalized(self, normalizer):
        """Smart single quotes should become apostrophes."""
        text = "It\u2019s a beautiful day."
        result = normalizer.normalize(text)

        assert '\u2019' not in result.text
        assert "'" in result.text


class TestBookIntroduction:
    """Test book introduction generation."""

    def test_basic_introduction(self, normalizer):
        """Generate basic book introduction."""
        intro = normalizer.generate_book_introduction(
            title="Don't Fight the Process",
            author="Archbishop Nicholas Duncan-Williams"
        )

        assert "Don't Fight the Process" in intro
        assert "Archbishop Nicholas Duncan-Williams" in intro
        assert intro.startswith('This is "')

    def test_introduction_with_narrator(self, normalizer):
        """Generate introduction with narrator credit."""
        intro = normalizer.generate_book_introduction(
            title="The Book",
            author="Jane Doe",
            narrator="John Smith"
        )

        assert "The Book" in intro
        assert "Jane Doe" in intro
        assert "John Smith" in intro
        assert "Narrated by" in intro

    def test_ssml_introduction(self, ssml_normalizer):
        """SSML introduction should have pause tags."""
        intro = ssml_normalizer.generate_book_introduction(
            title="The Book",
            author="Author Name"
        )

        assert "<speak>" in intro
        assert "</speak>" in intro
        assert "break time=" in intro


class TestChapterIntroduction:
    """Test chapter introduction generation."""

    def test_chapter_with_number(self, normalizer):
        """Generate chapter intro with number."""
        intro = normalizer.generate_chapter_introduction(
            chapter_title="The Beginning",
            chapter_number=1
        )

        assert "Chapter 1" in intro
        assert "The Beginning" in intro

    def test_chapter_already_has_prefix(self, normalizer):
        """Don't duplicate chapter prefix if already present."""
        intro = normalizer.generate_chapter_introduction(
            chapter_title="Chapter 5: The End"
        )

        # Should not have "Chapter 5: Chapter 5"
        assert intro.count("Chapter") == 1

    def test_ssml_chapter_introduction(self, ssml_normalizer):
        """SSML chapter intro should have pause."""
        intro = ssml_normalizer.generate_chapter_introduction(
            chapter_title="Test Chapter"
        )

        assert "<speak>" in intro
        assert "break time=" in intro


class TestFullPreparation:
    """Test full chunk preparation with introductions."""

    def test_first_chunk_with_book_intro(self, normalizer):
        """First chunk should include book introduction."""
        result = normalizer.prepare_chunk_for_tts(
            text="The story begins here.",
            is_first_chunk=True,
            book_title="My Book",
            author="Author Name"
        )

        assert 'This is "My Book"' in result
        assert "Author Name" in result
        assert "The story begins here" in result

    def test_chapter_start_with_intro(self, normalizer):
        """Chapter start should include chapter introduction."""
        result = normalizer.prepare_chunk_for_tts(
            text="Content of the chapter.",
            is_chapter_start=True,
            chapter_title="New Beginnings",
            chapter_number=2
        )

        assert "Chapter 2" in result
        assert "New Beginnings" in result

    def test_regular_chunk_no_intro(self, normalizer):
        """Regular chunk should not have introductions."""
        result = normalizer.prepare_chunk_for_tts(
            text="Just regular content here.",
            is_first_chunk=False,
            is_chapter_start=False
        )

        assert result == "Just regular content here."


class TestValidation:
    """Test output validation."""

    def test_valid_output_passes(self, normalizer):
        """Valid normalized text should pass validation."""
        text = "This is a normal sentence without any spoken punctuation."
        result = normalizer.normalize(text)

        is_valid, problems = normalizer.validate_output(result.text)
        assert is_valid
        assert len(problems) == 0

    def test_forbidden_words_fail(self, normalizer):
        """Text with forbidden spoken words should fail validation."""
        # Directly test validation (not normalization)
        is_valid, problems = normalizer.validate_output(
            "The dash in this sentence is problematic."
        )

        assert not is_valid
        assert len(problems) > 0


class TestTitleCleaning:
    """Test title cleaning for speech."""

    def test_remove_date_prefix(self, normalizer):
        """Date prefixes should be removed from titles."""
        intro = normalizer.generate_book_introduction(
            title="200313_Dont Fight the Process_final (1)",
            author="Author"
        )

        assert "200313" not in intro
        assert "_final" not in intro
        assert "(1)" not in intro


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
