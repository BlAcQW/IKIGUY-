"""
Embedding Service for InkWave.

Provides real vector embeddings using Gemini text-embedding-004 and stores them in pgvector.
Enables semantic search for book Q&A functionality.

Now supports:
- Organization-scoped embeddings for multi-tenancy
- Integration with shared document_processing module
"""

import os
import sys
import logging
import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import asyncpg
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Add shared services to path
sys.path.insert(0, '/opt/kasaai/apps')

from shared.document_processing import EmbeddingMetadata, QueryFilter

from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating and storing book embeddings.

    Uses Gemini text-embedding-004 for 768-dimensional embeddings
    and PostgreSQL pgvector for efficient similarity search.
    """

    # Embedding dimension for text-embedding-004
    EMBEDDING_DIM = 768

    def __init__(self):
        """Initialize embedding service."""
        self._embeddings = None
        self._pg_pool: Optional[asyncpg.Pool] = None
        self._initialized = False

        # PostgreSQL connection settings
        self.postgres_host = os.getenv("POSTGRES_SERVER", "localhost")
        self.postgres_port = os.getenv("POSTGRES_PORT", "5432")
        self.postgres_user = os.getenv("POSTGRES_USER", "postgres")
        self.postgres_password = os.getenv("POSTGRES_PASSWORD")
        self.postgres_db = os.getenv("POSTGRES_DB_CORE", "kasaai_core")

        # Gemini API key
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        if not self.gemini_api_key:
            logger.warning("GEMINI_API_KEY not set - embeddings will not work")

    @property
    def embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """
        Lazy initialization of Gemini embeddings.

        Returns:
            GoogleGenerativeAIEmbeddings instance
        """
        if self._embeddings is None:
            self._embeddings = GoogleGenerativeAIEmbeddings(
                google_api_key=self.gemini_api_key,
                model="models/text-embedding-004"
            )
            logger.info("Initialized Gemini text-embedding-004")
        return self._embeddings

    async def initialize(self):
        """
        Initialize PostgreSQL connection pool and ensure table exists.

        Raises:
            Exception: If initialization fails
        """
        if self._initialized:
            return

        try:
            # Create connection pool with SSL disabled for localhost
            # Reason: Local PostgreSQL doesn't require SSL and the default SSL key path doesn't exist
            dsn = f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            self._pg_pool = await asyncpg.create_pool(
                dsn,
                min_size=2,
                max_size=10,
                ssl=False  # Disable SSL for local connection
            )

            # Ensure pgvector extension and table exist
            await self._ensure_table_exists()

            self._initialized = True
            logger.info("Embedding service initialized with pgvector")

        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            raise

    async def _ensure_table_exists(self):
        """
        Create pgvector extension and embeddings table if they don't exist.
        """
        async with self._pg_pool.acquire() as conn:
            # Create pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Create embeddings table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS inkwave_book_embeddings (
                    id SERIAL PRIMARY KEY,
                    book_id VARCHAR(255) NOT NULL,
                    chunk_id VARCHAR(255) NOT NULL UNIQUE,
                    chunk_index INT NOT NULL,
                    chapter_id INT,
                    embedding VECTOR(768) NOT NULL,
                    text_preview VARCHAR(500),
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_inkwave_embeddings_book_id
                ON inkwave_book_embeddings(book_id)
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_inkwave_embeddings_chunk_id
                ON inkwave_book_embeddings(chunk_id)
            """)

            # Create IVFFlat index for similarity search (if enough rows)
            # Reason: IVFFlat is faster for large datasets but requires lists parameter
            try:
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_inkwave_embeddings_vector
                    ON inkwave_book_embeddings
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                """)
            except Exception as e:
                # IVFFlat may fail if not enough rows, use HNSW instead
                logger.warning(f"IVFFlat index creation failed, trying HNSW: {e}")
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_inkwave_embeddings_vector_hnsw
                    ON inkwave_book_embeddings
                    USING hnsw (embedding vector_cosine_ops)
                """)

            logger.info("pgvector table and indexes created")

    async def generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for text chunks using Gemini API.

        Args:
            texts: List of text strings to embed
            batch_size: Number of texts to process per batch

        Returns:
            List of 768-dimensional embedding vectors

        Raises:
            ValueError: If texts is empty
            Exception: If embedding generation fails
        """
        if not texts:
            return []

        if not self._initialized:
            await self.initialize()

        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(texts))
            batch_texts = texts[start_idx:end_idx]

            try:
                # Generate embeddings using LangChain
                batch_embeddings = await asyncio.to_thread(
                    self.embeddings.embed_documents,
                    batch_texts
                )
                all_embeddings.extend(batch_embeddings)

                logger.info(f"Generated embeddings for batch {batch_idx + 1}/{total_batches} ({len(batch_texts)} texts)")

                # Small delay to avoid rate limiting
                if batch_idx < total_batches - 1:
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Embedding generation failed for batch {batch_idx}: {e}")
                raise

        logger.info(f"Generated {len(all_embeddings)} embeddings total")
        return all_embeddings

    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a single query text.

        Args:
            query: Query text

        Returns:
            768-dimensional embedding vector
        """
        if not self._initialized:
            await self.initialize()

        embedding = await asyncio.to_thread(
            self.embeddings.embed_query,
            query
        )
        return embedding

    async def store_embeddings(
        self,
        book_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        organization_id: Optional[str] = None,
        uploaded_by: Optional[str] = None,
        topics: Optional[List[str]] = None
    ) -> int:
        """
        Store book chunk embeddings in pgvector with organization metadata.

        Args:
            book_id: Book identifier
            chunks: List of chunk dictionaries with chunk_index, text, etc.
            embeddings: List of embedding vectors
            organization_id: Organization ID for multi-tenancy filtering
            uploaded_by: User ID who uploaded the book
            topics: List of topics for the book

        Returns:
            Number of embeddings stored

        Raises:
            ValueError: If chunks and embeddings length mismatch
        """
        if len(chunks) != len(embeddings):
            raise ValueError(f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) length mismatch")

        if not self._initialized:
            await self.initialize()

        stored_count = 0
        async with self._pg_pool.acquire() as conn:
            for chunk, embedding in zip(chunks, embeddings):
                chunk_index = chunk.get("chunk_index", 0)
                chunk_id = f"{book_id}_chunk_{chunk_index}"
                text = chunk.get("text", "")
                chapter_id = chunk.get("chapter_id")

                # Build metadata using shared EmbeddingMetadata
                metadata = EmbeddingMetadata(
                    organization_id=organization_id,
                    document_id=book_id,
                    chunk_index=chunk_index,
                    document_type="book",
                    uploaded_by=uploaded_by or "",
                    topics=topics or []
                )

                try:
                    # Convert embedding list to string format for pgvector
                    embedding_str = "[" + ",".join(map(str, embedding)) + "]"

                    # Upsert embedding with metadata (insert or update on conflict)
                    await conn.execute("""
                        INSERT INTO inkwave_book_embeddings
                        (book_id, chunk_id, chunk_index, chapter_id, embedding, text_preview, metadata, updated_at)
                        VALUES ($1, $2, $3, $4, $5::vector, $6, $7::jsonb, NOW())
                        ON CONFLICT (chunk_id) DO UPDATE SET
                            embedding = EXCLUDED.embedding,
                            text_preview = EXCLUDED.text_preview,
                            metadata = EXCLUDED.metadata,
                            updated_at = NOW()
                    """, book_id, chunk_id, chunk_index, chapter_id,
                        embedding_str, text[:500], json.dumps(metadata.to_dict()))

                    stored_count += 1

                except Exception as e:
                    logger.error(f"Failed to store embedding for chunk {chunk_id}: {e}")

        logger.info(f"Stored {stored_count} embeddings for book {book_id}")
        return stored_count

    async def similarity_search(
        self,
        book_id: str,
        query: str,
        k: int = 5,
        threshold: float = 0.5,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find semantically similar chunks using cosine similarity.

        Args:
            book_id: Book identifier to search within
            query: Query text
            k: Number of results to return
            threshold: Minimum similarity threshold (0-1)
            organization_id: Optional organization filter for multi-tenancy

        Returns:
            List of similar chunks with scores
        """
        if not self._initialized:
            await self.initialize()

        logger.warning(f"[EMBEDDING DEBUG] similarity_search called: book_id={book_id}, query='{query[:50]}...', k={k}, threshold={threshold}, org_id={organization_id}")

        # Generate query embedding
        query_embedding = await self.generate_query_embedding(query)
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        results = []
        async with self._pg_pool.acquire() as conn:
            # Build query with optional organization filter
            if organization_id:
                # Filter by organization_id in metadata JSONB
                rows = await conn.fetch("""
                    SELECT
                        chunk_id,
                        chunk_index,
                        chapter_id,
                        text_preview,
                        metadata,
                        1 - (embedding <=> $1::vector) as similarity
                    FROM inkwave_book_embeddings
                    WHERE book_id = $2
                        AND 1 - (embedding <=> $1::vector) >= $3
                        AND (metadata->>'organization_id' = $5 OR metadata->>'organization_id' IS NULL)
                    ORDER BY embedding <=> $1::vector
                    LIMIT $4
                """, embedding_str, book_id, threshold, k, organization_id)
            else:
                # No organization filter
                rows = await conn.fetch("""
                    SELECT
                        chunk_id,
                        chunk_index,
                        chapter_id,
                        text_preview,
                        metadata,
                        1 - (embedding <=> $1::vector) as similarity
                    FROM inkwave_book_embeddings
                    WHERE book_id = $2
                        AND 1 - (embedding <=> $1::vector) >= $3
                    ORDER BY embedding <=> $1::vector
                    LIMIT $4
                """, embedding_str, book_id, threshold, k)

            for row in rows:
                results.append({
                    "chunk_id": row["chunk_id"],
                    "chunk_index": row["chunk_index"],
                    "chapter_id": row["chapter_id"],
                    "text_preview": row["text_preview"],
                    "similarity": float(row["similarity"]),
                    "metadata": row.get("metadata", {})
                })

        logger.warning(f"[EMBEDDING DEBUG] Found {len(results)} similar chunks for book {book_id} (threshold={threshold})")
        if results:
            logger.warning(f"[EMBEDDING DEBUG] Top similarity score: {results[0]['similarity']:.3f}")
        return results

    async def get_similar_chunks_with_text(
        self,
        book_id: str,
        query: str,
        k: int = 5,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Find similar chunks and retrieve full text from MongoDB.

        Args:
            book_id: Book identifier
            query: Query text
            k: Number of results
            threshold: Minimum similarity

        Returns:
            List of chunks with full text and similarity scores
        """
        # Get similar chunk IDs from pgvector
        similar = await self.similarity_search(book_id, query, k, threshold)

        if not similar:
            return []

        # Get full text from MongoDB
        db = get_db()
        chunk_indices = [s["chunk_index"] for s in similar]

        chunks_map = {}
        cursor = db.book_chunks.find({
            "book_id": book_id,
            "chunk_index": {"$in": chunk_indices}
        })

        async for doc in cursor:
            chunks_map[doc["chunk_index"]] = doc["text"]

        # Combine results
        results = []
        for s in similar:
            chunk_index = s["chunk_index"]
            results.append({
                "chunk_index": chunk_index,
                "chunk_id": s["chunk_id"],
                "chapter_id": s["chapter_id"],
                "text": chunks_map.get(chunk_index, s["text_preview"]),
                "similarity": s["similarity"]
            })

        return results

    async def delete_book_embeddings(self, book_id: str) -> int:
        """
        Delete all embeddings for a book.

        Args:
            book_id: Book identifier

        Returns:
            Number of embeddings deleted
        """
        if not self._initialized:
            await self.initialize()

        async with self._pg_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM inkwave_book_embeddings WHERE book_id = $1",
                book_id
            )
            # Parse "DELETE X" to get count
            count = int(result.split()[-1]) if result else 0

        logger.info(f"Deleted {count} embeddings for book {book_id}")
        return count

    async def get_embedding_stats(self, book_id: str) -> Dict[str, Any]:
        """
        Get embedding statistics for a book.

        Args:
            book_id: Book identifier

        Returns:
            Statistics dictionary
        """
        if not self._initialized:
            await self.initialize()

        async with self._pg_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT
                    COUNT(*) as count,
                    MIN(created_at) as first_created,
                    MAX(updated_at) as last_updated
                FROM inkwave_book_embeddings
                WHERE book_id = $1
            """, book_id)

            return {
                "book_id": book_id,
                "embedding_count": row["count"] if row else 0,
                "first_created": row["first_created"].isoformat() if row and row["first_created"] else None,
                "last_updated": row["last_updated"].isoformat() if row and row["last_updated"] else None,
                "embedding_dimension": self.EMBEDDING_DIM,
                "model": "text-embedding-004"
            }

    async def close(self):
        """Close the connection pool."""
        if self._pg_pool:
            await self._pg_pool.close()
            self._pg_pool = None
            self._initialized = False
            logger.info("Embedding service connection pool closed")


# Global service instance
_embedding_service: Optional[EmbeddingService] = None


async def get_embedding_service() -> EmbeddingService:
    """
    Get or create embedding service instance.

    Returns:
        EmbeddingService instance
    """
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService()
        await _embedding_service.initialize()

    return _embedding_service
