"""
Semantic Cache Service for RAG Queries.
Uses semantic similarity to match similar queries and return cached responses.
This handles query variations like "doctors in Kumasi" vs "find doctors in Kumasi city".
"""

import os
import logging
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
from datetime import timedelta
import redis.asyncio as aioredis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class SemanticCacheService:
    """
    Service for semantically caching RAG query results.

    Uses embeddings to match similar queries even if worded differently.
    Example: "hospitals in Kumasi" matches "find hospitals Kumasi city"
    """

    def __init__(self):
        """Initialize semantic cache service."""
        # Redis connection parameters
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = int(os.getenv("REDIS_DB", "1"))  # Use DB 1 for semantic cache
        self.redis_password = os.getenv("REDIS_PASSWORD")

        # Semantic similarity threshold (0.0-1.0)
        # Reason: Queries with >85% similarity are considered equivalent
        self.similarity_threshold = float(os.getenv("SEMANTIC_CACHE_THRESHOLD", "0.85"))

        # Cache TTL (24 hours)
        self.cache_ttl = int(os.getenv("SEMANTIC_CACHE_TTL", "86400"))

        # Redis client (lazy initialization)
        self._redis: Optional[Redis] = None

        # Embeddings model (lazy initialization)
        self._embeddings = None

        logger.info(f"Semantic cache service initialized (threshold={self.similarity_threshold}, ttl={self.cache_ttl}s)")

    async def _get_redis(self) -> Redis:
        """
        Get or create Redis client connection.

        Returns:
            Redis client instance
        """
        if self._redis is None:
            try:
                self._redis = await aioredis.from_url(
                    f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}",
                    password=self.redis_password,
                    encoding="utf-8",
                    decode_responses=False,  # Store binary embeddings
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0
                )
                # Test connection
                await self._redis.ping()
                logger.info("✅ Semantic cache Redis connection established")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Redis for semantic cache: {e}")
                raise

        return self._redis

    @property
    def embeddings(self):
        """Lazy initialization of embeddings model."""
        if self._embeddings is None:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                gemini_api_key = os.getenv("GEMINI_API_KEY")

                if not gemini_api_key:
                    raise ValueError("GEMINI_API_KEY required for semantic caching")

                self._embeddings = GoogleGenerativeAIEmbeddings(
                    google_api_key=gemini_api_key,
                    model="models/text-embedding-004"
                )
                logger.info("✅ Semantic cache embeddings initialized")
            except Exception as e:
                logger.error(f"Failed to initialize embeddings: {e}")
                raise

        return self._embeddings

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First embedding vector
            vec2: Second embedding vector

        Returns:
            Similarity score (0.0-1.0)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    async def get_semantic_cached_response(
        self,
        company_name: str,
        query: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response using semantic similarity.

        Finds the most similar cached query and returns its response
        if similarity > threshold.

        Args:
            company_name: Company identifier
            query: Query string

        Returns:
            Cached response dict or None if no similar query found
        """
        try:
            import json

            redis = await self._get_redis()

            # Get query embedding
            query_embedding = await self.embeddings.aembed_query(query)
            query_vec = np.array(query_embedding)

            # Scan all cached queries for this company
            pattern = f"semantic:{company_name}:*"
            cursor = 0
            best_match = None
            best_similarity = 0.0

            while True:
                cursor, keys = await redis.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )

                for key in keys:
                    # Get stored embedding
                    stored_data = await redis.hgetall(key)

                    if not stored_data or b'embedding' not in stored_data:
                        continue

                    # Deserialize embedding
                    stored_embedding = np.frombuffer(stored_data[b'embedding'], dtype=np.float32)

                    # Calculate similarity
                    similarity = self._cosine_similarity(query_vec, stored_embedding)

                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = {
                            'key': key,
                            'response': json.loads(stored_data[b'response'].decode('utf-8')),
                            'original_query': stored_data[b'query'].decode('utf-8')
                        }

                if cursor == 0:
                    break

            # Return best match if above threshold
            if best_match and best_similarity >= self.similarity_threshold:
                logger.info(f"🎯 Semantic cache HIT: similarity={best_similarity:.3f}, "
                          f"query='{query[:50]}', matched='{best_match['original_query'][:50]}'")
                return best_match['response']
            else:
                logger.info(f"❌ Semantic cache MISS: best_similarity={best_similarity:.3f}, "
                          f"threshold={self.similarity_threshold}")
                return None

        except Exception as e:
            logger.error(f"Error in semantic cache lookup: {e}")
            return None

    async def cache_semantic_response(
        self,
        company_name: str,
        query: str,
        response_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache a query response with semantic indexing.

        Args:
            company_name: Company identifier
            query: Query string
            response_data: Response data to cache
            ttl: Time to live in seconds

        Returns:
            True if cached successfully
        """
        try:
            import json
            import hashlib

            redis = await self._get_redis()

            # Generate cache key
            query_hash = hashlib.sha256(f"{company_name}:{query}".encode()).hexdigest()[:16]
            cache_key = f"semantic:{company_name}:{query_hash}"

            # Get query embedding
            query_embedding = await self.embeddings.aembed_query(query)
            embedding_bytes = np.array(query_embedding, dtype=np.float32).tobytes()

            # Store in Redis hash
            cache_ttl = ttl if ttl is not None else self.cache_ttl

            await redis.hset(
                cache_key,
                mapping={
                    'query': query,
                    'embedding': embedding_bytes,
                    'response': json.dumps(response_data)
                }
            )

            await redis.expire(cache_key, cache_ttl)

            logger.info(f"✅ Semantic cached: '{query[:50]}' (ttl={cache_ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Error caching semantic response: {e}")
            return False

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            logger.info("Semantic cache Redis connection closed")
            self._redis = None


# Global service instance
semantic_cache_service = SemanticCacheService()
