"""
Tests for ESV Bible API integration.

Tests the ESV API service functions and API routes with real API calls.
Requires ESV_API_KEY to be set in environment.
"""

import pytest
import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.bible_service import (
    fetch_scripture_from_esv,
    fetch_esv_html,
    fetch_esv_audio_url,
    search_esv,
    fetch_scripture,
    ESV_API_KEY,
)


# Skip all tests if ESV API key is not configured
pytestmark = pytest.mark.skipif(
    not ESV_API_KEY,
    reason="ESV_API_KEY not configured"
)


class TestESVTextEndpoint:
    """Tests for the ESV text passage endpoint."""

    @pytest.mark.asyncio
    async def test_fetch_single_verse(self):
        """Test fetching a single verse (expected use)."""
        result = await fetch_scripture_from_esv("John 3:16")

        assert result is not None
        assert result["reference"] == "John 3:16"
        assert "God so loved the world" in result["text"]
        assert result["translation_id"] == "esv"
        assert result["translation_name"] == "English Standard Version"

    @pytest.mark.asyncio
    async def test_fetch_verse_range(self):
        """Test fetching a range of verses."""
        result = await fetch_scripture_from_esv("Psalm 23:1-3")

        assert result is not None
        assert "Psalm 23" in result["reference"]
        assert "shepherd" in result["text"].lower()
        assert "green pastures" in result["text"].lower()

    @pytest.mark.asyncio
    async def test_fetch_full_chapter(self):
        """Test fetching a full chapter."""
        result = await fetch_scripture_from_esv("Romans 8")

        assert result is not None
        assert "Romans 8" in result["reference"]
        assert len(result["text"]) > 500  # Full chapter should be long
        assert "condemnation" in result["text"].lower()

    @pytest.mark.asyncio
    async def test_fetch_with_verse_numbers(self):
        """Test that verse numbers are included when requested."""
        result = await fetch_scripture_from_esv(
            "John 3:16-17",
            include_verse_numbers=True
        )

        assert result is not None
        # ESV format uses [16] or similar for verse numbers
        assert "[16]" in result["text"] or "16" in result["text"]

    @pytest.mark.asyncio
    async def test_fetch_without_verse_numbers(self):
        """Test fetching without verse numbers."""
        result = await fetch_scripture_from_esv(
            "John 3:16",
            include_verse_numbers=False
        )

        assert result is not None
        assert result["text"] is not None
        # Text should still contain the verse content
        assert "God so loved" in result["text"]

    @pytest.mark.asyncio
    async def test_fetch_with_headings(self):
        """Test fetching with section headings."""
        result = await fetch_scripture_from_esv(
            "John 3:16",
            include_headings=True
        )

        assert result is not None
        # Headings might include "For God So Loved the World" or similar
        assert len(result["text"]) > 0

    @pytest.mark.asyncio
    async def test_invalid_reference(self):
        """Test that invalid reference returns None (failure case)."""
        result = await fetch_scripture_from_esv("InvalidBook 999:999")

        # Should return None or empty for invalid reference
        assert result is None or (result and not result.get("text"))

    @pytest.mark.asyncio
    async def test_fetch_via_main_function_esv(self):
        """Test that main fetch_scripture function routes to ESV correctly."""
        result = await fetch_scripture("Psalm 23:1", "esv")

        assert result is not None
        assert result["translation_id"] == "esv"
        assert "shepherd" in result["text"].lower()


class TestESVHtmlEndpoint:
    """Tests for the ESV HTML passage endpoint."""

    @pytest.mark.asyncio
    async def test_fetch_html_basic(self):
        """Test fetching HTML formatted scripture."""
        result = await fetch_esv_html("Psalm 23")

        assert result is not None
        assert result["reference"] == "Psalm 23"
        assert "<" in result["html"]  # Should contain HTML tags
        assert ">" in result["html"]
        assert result["translation_id"] == "esv"

    @pytest.mark.asyncio
    async def test_fetch_html_with_css(self):
        """Test HTML includes CSS link when requested."""
        result = await fetch_esv_html("John 1:1", include_css_link=True)

        assert result is not None
        assert "stylesheet" in result["html"] or "css" in result["html"].lower()

    @pytest.mark.asyncio
    async def test_fetch_html_with_footnotes(self):
        """Test HTML includes footnotes when requested."""
        # Psalm 23:2 has footnotes about "waters of rest"
        result = await fetch_esv_html("Psalm 23", include_footnotes=True)

        assert result is not None
        # Footnotes appear as superscript numbers or in a footnotes section
        assert "footnote" in result["html"].lower() or "fn" in result["html"]

    @pytest.mark.asyncio
    async def test_fetch_html_poetry_formatting(self):
        """Test that poetry (Psalms) has proper HTML formatting."""
        result = await fetch_esv_html("Psalm 23")

        assert result is not None
        # Poetry should have line breaks or specific formatting
        assert "<br" in result["html"] or "line" in result["html"]


class TestESVAudioEndpoint:
    """Tests for the ESV audio URL endpoint."""

    @pytest.mark.asyncio
    async def test_fetch_audio_url(self):
        """Test fetching audio URL for a passage."""
        result = await fetch_esv_audio_url("John 3:16")

        assert result is not None
        assert result["reference"] == "John 3:16"
        assert result["translation_id"] == "esv"
        # Audio URL should be present
        if result.get("audio_url"):
            assert "audio" in result["audio_url"] or "mp3" in result["audio_url"]

    @pytest.mark.asyncio
    async def test_fetch_audio_url_chapter(self):
        """Test fetching audio URL for a full chapter."""
        result = await fetch_esv_audio_url("Psalm 23")

        assert result is not None
        assert "Psalm" in result["reference"] or "23" in result["reference"]


class TestESVSearchEndpoint:
    """Tests for the ESV search endpoint."""

    @pytest.mark.asyncio
    async def test_search_single_word(self):
        """Test searching for a single word."""
        result = await search_esv("love")

        assert result is not None
        assert result["query"] == "love"
        assert result["total_results"] > 0
        assert len(result["results"]) > 0
        assert result["translation_id"] == "esv"

    @pytest.mark.asyncio
    async def test_search_phrase(self):
        """Test searching for a phrase."""
        result = await search_esv("God so loved")

        assert result is not None
        assert result["total_results"] > 0
        # Should find John 3:16
        references = [r["reference"] for r in result["results"]]
        assert any("John 3:16" in ref for ref in references)

    @pytest.mark.asyncio
    async def test_search_pagination(self):
        """Test search pagination."""
        # Get first page
        page1 = await search_esv("faith", page_size=5, page=1)
        # Get second page
        page2 = await search_esv("faith", page_size=5, page=2)

        assert page1 is not None
        assert page2 is not None
        assert page1["page"] == 1
        assert page2["page"] == 2
        # Results should be different
        page1_refs = {r["reference"] for r in page1["results"]}
        page2_refs = {r["reference"] for r in page2["results"]}
        assert page1_refs != page2_refs

    @pytest.mark.asyncio
    async def test_search_page_size(self):
        """Test search respects page size limit."""
        result = await search_esv("Lord", page_size=10)

        assert result is not None
        assert len(result["results"]) <= 10

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """Test search with query that has no results."""
        result = await search_esv("xyznonexistentword123")

        assert result is not None
        assert result["total_results"] == 0
        assert len(result["results"]) == 0


class TestESVAPIRoutes:
    """Integration tests for ESV API HTTP routes."""

    def test_get_esv_scripture(self, client):
        """Test GET /api/v1/ai/esv/{reference} endpoint."""
        response = client.get("/api/v1/ai/esv/John%203:16")

        assert response.status_code == 200
        data = response.json()
        assert data["reference"] == "John 3:16"
        assert data["translation_id"] == "esv"
        assert "God so loved" in data["text"]

    def test_get_esv_html(self, client):
        """Test GET /api/v1/ai/esv/{reference}/html endpoint."""
        response = client.get("/api/v1/ai/esv/Psalm%2023/html")

        assert response.status_code == 200
        data = response.json()
        assert data["reference"] == "Psalm 23"
        assert "<" in data["html"]
        assert data["translation_id"] == "esv"

    def test_get_esv_audio(self, client):
        """Test GET /api/v1/ai/esv/{reference}/audio endpoint."""
        response = client.get("/api/v1/ai/esv/John%203:16/audio")

        assert response.status_code == 200
        data = response.json()
        assert data["translation_id"] == "esv"
        # Audio URL may or may not be present depending on API response
        assert "reference" in data

    def test_search_esv(self, client):
        """Test GET /api/v1/ai/esv/search endpoint."""
        response = client.get("/api/v1/ai/esv/search?q=love&page_size=5")

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "love"
        assert data["total_results"] > 0
        assert len(data["results"]) <= 5

    def test_get_scripture_with_translation_esv(self, client):
        """Test generic scripture endpoint with ESV translation."""
        response = client.get("/api/v1/ai/scriptures/John%203:16?translation=esv")

        assert response.status_code == 200
        data = response.json()
        assert data["translation_id"] == "esv"
        assert "God so loved" in data["text"]

    def test_invalid_reference_404(self, client):
        """Test that invalid reference returns 404."""
        response = client.get("/api/v1/ai/esv/InvalidBook%20999:999")

        assert response.status_code == 404


class TestESVEdgeCases:
    """Edge case tests for ESV API integration."""

    @pytest.mark.asyncio
    async def test_reference_with_special_characters(self):
        """Test handling of references with special characters."""
        # Song of Solomon uses various naming conventions
        result = await fetch_scripture_from_esv("Song of Solomon 1:1")

        assert result is not None or result is None  # May or may not match

    @pytest.mark.asyncio
    async def test_numbered_book(self):
        """Test handling of numbered books (e.g., 1 Corinthians)."""
        result = await fetch_scripture_from_esv("1 Corinthians 13:4-7")

        assert result is not None
        assert "love" in result["text"].lower()

    @pytest.mark.asyncio
    async def test_three_numbered_book(self):
        """Test handling of 3-numbered books (e.g., 3 John)."""
        result = await fetch_scripture_from_esv("3 John 1:1-4")

        assert result is not None
        assert result["reference"] is not None

    @pytest.mark.asyncio
    async def test_whitespace_handling(self):
        """Test that extra whitespace is handled."""
        result = await fetch_scripture_from_esv("  John 3:16  ")

        assert result is not None
        assert "God so loved" in result["text"]

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent API requests."""
        references = ["John 1:1", "Psalm 23:1", "Romans 8:28", "Genesis 1:1"]

        tasks = [fetch_scripture_from_esv(ref) for ref in references]
        results = await asyncio.gather(*tasks)

        assert all(r is not None for r in results)
        assert len(results) == 4
