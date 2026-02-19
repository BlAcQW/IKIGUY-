"""
Unit tests for Embedding Service.

Tests embedding generation, storage, and similarity search using real data.
"""

import pytest
import asyncio
import uuid
from datetime import datetime

import sys
sys.path.insert(0, '/opt/kasaai/apps/shared')

from app.services.embedding_service import (
    EmbeddingService,
    get_embedding_service,
)


@pytest.fixture
def embedding_service():
    """Create embedding service instance."""
    return EmbeddingService()


@pytest.fixture
def test_book_id():
    """Generate unique test book ID."""
    return f"test_book_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def sample_chunks():
    """Sample text chunks for testing."""
    return [
        {"chunk_index": 0, "text": "The sun rose over the mountains, casting golden light across the valley.", "chapter_id": "ch1"},
        {"chunk_index": 1, "text": "She walked through the forest, listening to birds singing in the trees.", "chapter_id": "ch1"},
        {"chunk_index": 2, "text": "The old library held thousands of ancient books, their pages yellowed with age.", "chapter_id": "ch2"},
        {"chunk_index": 3, "text": "Technology has transformed how we communicate with each other.", "chapter_id": "ch3"},
        {"chunk_index": 4, "text": "The recipe called for fresh ingredients from the local market.", "chapter_id": "ch4"},
    ]


class TestEmbeddingGeneration:
    """Tests for embedding generation."""

    @pytest.mark.asyncio
    async def test_generate_single_embedding(self, embedding_service):
        """Test generating embedding for single text."""
        texts = ["Hello, this is a test sentence."]
        embeddings = await embedding_service.generate_embeddings(texts)

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 768  # Gemini text-embedding-004 dimension
        assert all(isinstance(v, float) for v in embeddings[0])

    @pytest.mark.asyncio
    async def test_generate_batch_embeddings(self, embedding_service, sample_chunks):
        """Test generating embeddings for multiple texts."""
        texts = [c["text"] for c in sample_chunks]
        embeddings = await embedding_service.generate_embeddings(texts)

        assert len(embeddings) == len(texts)
        for emb in embeddings:
            assert len(emb) == 768
            assert all(isinstance(v, float) for v in emb)

    @pytest.mark.asyncio
    async def test_embedding_consistency(self, embedding_service):
        """Test that same text produces similar embeddings."""
        text = "The quick brown fox jumps over the lazy dog."
        emb1 = await embedding_service.generate_embeddings([text])
        emb2 = await embedding_service.generate_embeddings([text])

        # Embeddings should be identical or very similar
        diff = sum(abs(a - b) for a, b in zip(emb1[0], emb2[0]))
        assert diff < 0.01  # Very small difference

    @pytest.mark.asyncio
    async def test_empty_text_handling(self, embedding_service):
        """Test handling of empty text."""
        with pytest.raises(Exception):
            await embedding_service.generate_embeddings([""])


class TestEmbeddingStorage:
    """Tests for embedding storage in pgvector."""

    @pytest.mark.asyncio
    async def test_store_and_retrieve_embeddings(
        self, embedding_service, test_book_id, sample_chunks
    ):
        """Test storing embeddings and retrieving stats."""
        # Generate embeddings
        texts = [c["text"] for c in sample_chunks]
        embeddings = await embedding_service.generate_embeddings(texts)

        # Store in pgvector
        stored_count = await embedding_service.store_embeddings(
            book_id=test_book_id,
            chunks=sample_chunks,
            embeddings=embeddings
        )

        assert stored_count == len(sample_chunks)

        # Verify stats
        stats = await embedding_service.get_embedding_stats(test_book_id)
        assert stats["embedding_count"] == len(sample_chunks)
        assert stats["book_id"] == test_book_id

        # Cleanup
        await embedding_service.delete_book_embeddings(test_book_id)

    @pytest.mark.asyncio
    async def test_delete_book_embeddings(
        self, embedding_service, test_book_id, sample_chunks
    ):
        """Test deleting all embeddings for a book."""
        # Store embeddings
        texts = [c["text"] for c in sample_chunks]
        embeddings = await embedding_service.generate_embeddings(texts)
        await embedding_service.store_embeddings(
            book_id=test_book_id,
            chunks=sample_chunks,
            embeddings=embeddings
        )

        # Verify stored
        stats = await embedding_service.get_embedding_stats(test_book_id)
        assert stats["embedding_count"] > 0

        # Delete
        deleted = await embedding_service.delete_book_embeddings(test_book_id)
        assert deleted > 0

        # Verify deleted
        stats = await embedding_service.get_embedding_stats(test_book_id)
        assert stats["embedding_count"] == 0


class TestSimilaritySearch:
    """Tests for semantic similarity search."""

    @pytest.mark.asyncio
    async def test_similarity_search_basic(
        self, embedding_service, test_book_id, sample_chunks
    ):
        """Test basic similarity search."""
        # Store embeddings
        texts = [c["text"] for c in sample_chunks]
        embeddings = await embedding_service.generate_embeddings(texts)
        await embedding_service.store_embeddings(
            book_id=test_book_id,
            chunks=sample_chunks,
            embeddings=embeddings
        )

        # Search for nature-related content
        results = await embedding_service.similarity_search(
            book_id=test_book_id,
            query="nature and trees",
            k=3
        )

        assert len(results) > 0
        assert len(results) <= 3

        # Results should have required fields
        for r in results:
            assert "chunk_index" in r
            assert "similarity" in r
            assert 0 <= r["similarity"] <= 1

        # Cleanup
        await embedding_service.delete_book_embeddings(test_book_id)

    @pytest.mark.asyncio
    async def test_similarity_search_with_text(
        self, embedding_service, test_book_id, sample_chunks
    ):
        """Test similarity search returns text content."""
        # Store embeddings
        texts = [c["text"] for c in sample_chunks]
        embeddings = await embedding_service.generate_embeddings(texts)
        await embedding_service.store_embeddings(
            book_id=test_book_id,
            chunks=sample_chunks,
            embeddings=embeddings
        )

        # Search with text retrieval
        results = await embedding_service.get_similar_chunks_with_text(
            book_id=test_book_id,
            query="library and books",
            k=2
        )

        assert len(results) > 0
        for r in results:
            assert "text" in r
            assert len(r["text"]) > 0

        # Cleanup
        await embedding_service.delete_book_embeddings(test_book_id)

    @pytest.mark.asyncio
    async def test_similarity_threshold(
        self, embedding_service, test_book_id, sample_chunks
    ):
        """Test similarity search respects threshold."""
        # Store embeddings
        texts = [c["text"] for c in sample_chunks]
        embeddings = await embedding_service.generate_embeddings(texts)
        await embedding_service.store_embeddings(
            book_id=test_book_id,
            chunks=sample_chunks,
            embeddings=embeddings
        )

        # Search with high threshold
        results_high = await embedding_service.similarity_search(
            book_id=test_book_id,
            query="completely unrelated quantum physics",
            k=5,
            threshold=0.8
        )

        # Search with low threshold
        results_low = await embedding_service.similarity_search(
            book_id=test_book_id,
            query="completely unrelated quantum physics",
            k=5,
            threshold=0.1
        )

        # High threshold should return fewer or equal results
        assert len(results_high) <= len(results_low)

        # Cleanup
        await embedding_service.delete_book_embeddings(test_book_id)

    @pytest.mark.asyncio
    async def test_no_results_for_nonexistent_book(self, embedding_service):
        """Test search returns empty for non-existent book."""
        results = await embedding_service.similarity_search(
            book_id="nonexistent_book_12345",
            query="test query",
            k=5
        )

        assert len(results) == 0


class TestServiceSingleton:
    """Tests for service singleton pattern."""

    @pytest.mark.asyncio
    async def test_get_embedding_service_returns_same_instance(self):
        """Test that get_embedding_service returns singleton."""
        service1 = await get_embedding_service()
        service2 = await get_embedding_service()

        assert service1 is service2
