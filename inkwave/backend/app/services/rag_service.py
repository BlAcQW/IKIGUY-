"""
RAG Service for InkWave.

Leverages shared services for maximum reusability:
- Uses shared LLMProviderService for LLM with billing
- Uses shared RAGService for semantic search and retrieval
- Uses app-specific EmbeddingService for book embeddings
- Wraps shared services with book-specific logic

This design allows easy replication in other apps by:
1. Using shared/integration/rag.py for semantic search
2. Using shared/services/llm_provider_service.py for generation
3. Adding app-specific logic in a thin wrapper layer
"""

import logging
import sys
import os
from typing import List, Dict, Any, Optional

# Add shared services to path
sys.path.append('/opt/kasaai/apps/shared')

from services.llm_provider_service import (
    LLMProviderService,
    ChatRequest,
    ChatMessage
)
from integration.rag import RAGService as SharedRAGService, RAGConfig, KnowledgeDocument
from app.core.config import settings
from app.core.database import get_db
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG (Retrieval-Augmented Generation) service for InkWave.

    Leverages shared services for maximum reusability:
    - Shared LLMProviderService: LLM generation with automatic billing
    - Shared RAGService: Semantic search and retrieval (optional, for future use)
    - App-specific EmbeddingService: Book-specific embedding storage

    This design allows easy replication in other apps by reusing shared components.
    """

    def __init__(self, enable_billing: bool = True):
        """
        Initialize RAG service.

        Args:
            enable_billing: Enable automatic wallet billing
        """
        self.llm_service = None
        self.shared_rag_service = None  # Optional: for future use of shared RAG
        self.enable_billing = enable_billing
        self._initialized = False
        # Default to Gemini 2.0 Flash Exp (free tier) for cost efficiency
        self.default_model = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash-exp')

    async def initialize(self):
        """
        Initialize shared services.

        Raises:
            Exception: If initialization fails
        """
        if self._initialized:
            return

        try:
            # Initialize unified LLM service with billing (shared service)
            self.llm_service = LLMProviderService(enable_billing=self.enable_billing)
            await self.llm_service.initialize()

            # Optional: Initialize shared RAG service for semantic search
            # Currently using app-specific EmbeddingService, but can migrate to shared RAG
            # if we want to use LangChain's full RAG pipeline
            try:
                rag_config = RAGConfig(
                    postgres_host=os.getenv("POSTGRES_SERVER", "localhost"),
                    postgres_port=os.getenv("POSTGRES_PORT", "5432"),
                    postgres_user=os.getenv("POSTGRES_USER", "postgres"),
                    postgres_password=os.getenv("POSTGRES_PASSWORD"),
                    postgres_db=os.getenv("POSTGRES_DB_CORE", "kasaai_core"),
                    ai_provider="gemini",
                    api_key=os.getenv("GEMINI_API_KEY"),
                    embedding_model="text-embedding-004",
                    llm_model=self.default_model,
                    retrieval_k=getattr(settings, 'RAG_RETRIEVAL_K', 5),
                    similarity_threshold=getattr(settings, 'RAG_CONFIDENCE_THRESHOLD', 0.5),
                    confidence_threshold=0.5,
                    temperature=getattr(settings, 'RAG_TEMPERATURE', 0.7)
                )
                self.shared_rag_service = SharedRAGService(config=rag_config)
                logger.info("✅ Shared RAG service available (for future use)")
            except Exception as rag_error:
                logger.warning(f"Shared RAG service not available (using app-specific): {rag_error}")

            self._initialized = True
            logger.info(f"✅ RAG Service initialized with shared LLMProviderService (model: {self.default_model})")
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG service: {e}")
            raise

    async def query_book_stream(
        self,
        book_id: str,
        question: str,
        context_chunks: Optional[List[str]] = None,
        user_profile: Optional[Dict[str, Any]] = None,
        llm_provider: str = "gemini",
        llm_model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ):
        """
        Ask a question about a book using RAG with streaming response.

        Args:
            book_id: Book identifier
            question: User's question
            context_chunks: Optional context from current reading position
            user_profile: Optional user profile for personalization
            llm_provider: LLM provider ID (gemini, openai, anthropic, etc.)
            llm_model: Specific model to use (optional, uses provider default)
            system_prompt: Custom system prompt (optional, uses default)
            temperature: Generation temperature (0.0-1.0)

        Yields:
            Text chunks as they are generated

        Raises:
            ValueError: If service not initialized
        """
        logger.warning(f"[RAG STREAM] Starting query_book_stream for book {book_id}, question: {question[:100]}")

        if not self._initialized:
            await self.initialize()
            logger.warning(f"[RAG STREAM] Initialized RAG service")

        # Use semantic search to find relevant chunks
        book_chunks = []
        try:
            logger.warning(f"[RAG DEBUG] Attempting semantic search for book {book_id}")
            embedding_service = await get_embedding_service()
            logger.warning(f"[RAG DEBUG] Embedding service initialized")
            book_chunks = await embedding_service.get_similar_chunks_with_text(
                book_id=book_id,
                query=question,
                k=getattr(settings, 'RAG_RETRIEVAL_K', 5),
                threshold=getattr(settings, 'RAG_CONFIDENCE_THRESHOLD', 0.5)
            )
            logger.warning(f"[RAG DEBUG] Semantic search found {len(book_chunks)} relevant chunks for book {book_id}")
        except Exception as e:
            logger.error(f"[RAG DEBUG] Semantic search failed, falling back to simple query: {e}", exc_info=True)
            # Fallback to simple MongoDB query if embeddings not available
            db = get_db()
            book_chunks = []
            cursor = db.book_chunks.find({"book_id": book_id}).limit(10)
            logger.warning(f"[RAG DEBUG] Fallback MongoDB query for book {book_id}")
            async for doc in cursor:
                book_chunks.append({
                    "chunk_index": doc["chunk_index"],
                    "text": doc["text"],
                    "chapter_id": doc.get("chapter_id"),
                    "similarity": 0.5  # Default similarity for fallback
                })
            logger.warning(f"[RAG DEBUG] Fallback MongoDB found {len(book_chunks)} chunks")

        if not book_chunks:
            logger.warning(f"No chunks found for book: {book_id}")
            yield "I don't have enough information about this book to answer your question."
            return

        # Build context from semantically relevant chunks (already sorted by similarity)
        context_text = "\n\n".join([chunk["text"] for chunk in book_chunks])

        # Build personalized system prompt (use custom or default)
        if not system_prompt:
            system_prompt = self._build_system_prompt(user_profile)

        # Build user prompt with context
        user_prompt = f"""
Book Context:
{context_text}

Current Reading Position:
{' '.join(context_chunks or [])}

Question: {question}

Please provide a clear, informative answer based on the book content. If the answer requires information not in the context, say so clearly.
        """

        # Stream response using LLMProviderService (supports multiple providers)
        try:
            # Determine model ID based on provider
            if not llm_model:
                # Use provider defaults
                model_map = {
                    "gemini": "gemini-2.5-flash",
                    "openai": "gpt-4o-mini",
                    "anthropic": "claude-3-5-sonnet-20241022",
                    "ollama": "llama3.2:3b"
                }
                llm_model = model_map.get(llm_provider, self.default_model)

            # Build chat request with streaming
            chat_request = ChatRequest(
                model_id=llm_model,
                messages=[
                    ChatMessage(role="system", content=system_prompt),
                    ChatMessage(role="user", content=user_prompt)
                ],
                temperature=temperature,
                max_tokens=1000,
                stream=True
            )

            # Get user ID for billing
            user_id = user_profile.get("user_id", "anonymous") if user_profile else "anonymous"

            # Stream response from LLM with automatic billing
            logger.warning(f"RAG query: book={book_id}, provider={llm_provider}, model={llm_model}, user={user_id}")

            async for chunk in self.llm_service.chat_stream(
                user_id=user_id,
                request=chat_request
            ):
                if chunk.content:
                    yield chunk.content

            logger.warning(f"RAG streaming completed: book={book_id}, provider={llm_provider}")

        except Exception as e:
            logger.error(f"RAG streaming query failed: {e}")
            yield f"Sorry, I encountered an error: {str(e)}"

    async def query_book(
        self,
        book_id: str,
        question: str,
        context_chunks: Optional[List[str]] = None,
        user_profile: Optional[Dict[str, Any]] = None,
        llm_provider: str = "gemini",
        llm_model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Ask a question about a book using RAG.

        Args:
            book_id: Book identifier
            question: User's question
            context_chunks: Optional context from current reading position
            user_profile: Optional user profile for personalization
            llm_provider: LLM provider ID (gemini, openai, anthropic, etc.)
            llm_model: Specific model to use (optional, uses provider default)
            system_prompt: Custom system prompt (optional, uses default)
            temperature: Generation temperature (0.0-1.0)

        Returns:
            {
                "answer": str,
                "confidence": float,
                "sources": List[Dict],
                "tokens_used": int,
                "cost": float,
                "model_used": str
            }

        Raises:
            ValueError: If service not initialized
        """
        if not self._initialized:
            await self.initialize()

        # Use semantic search to find relevant chunks
        try:
            logger.info(f"[RAG DEBUG QUERY] Attempting semantic search for book {book_id}")
            embedding_service = await get_embedding_service()
            logger.info(f"[RAG DEBUG QUERY] Embedding service initialized")
            book_chunks = await embedding_service.get_similar_chunks_with_text(
                book_id=book_id,
                query=question,
                k=getattr(settings, 'RAG_RETRIEVAL_K', 5),
                threshold=getattr(settings, 'RAG_CONFIDENCE_THRESHOLD', 0.5)
            )
            logger.info(f"[RAG DEBUG QUERY] Semantic search found {len(book_chunks)} relevant chunks for query")
        except Exception as e:
            logger.error(f"[RAG DEBUG QUERY] Semantic search failed, falling back to simple query: {e}", exc_info=True)
            # Fallback to simple MongoDB query if embeddings not available
            db = get_db()
            book_chunks = []
            cursor = db.book_chunks.find({"book_id": book_id}).limit(10)
            logger.info(f"[RAG DEBUG QUERY] Fallback MongoDB query for book {book_id}")
            async for doc in cursor:
                book_chunks.append({
                    "chunk_index": doc["chunk_index"],
                    "text": doc["text"],
                    "chapter_id": doc.get("chapter_id"),
                    "similarity": 0.5  # Default similarity for fallback
                })
            logger.info(f"[RAG DEBUG QUERY] Fallback MongoDB found {len(book_chunks)} chunks")

        if not book_chunks:
            logger.warning(f"No chunks found for book: {book_id}")
            return {
                "answer": "I don't have enough information about this book to answer your question.",
                "confidence": 0.0,
                "sources": [],
                "tokens_used": 0
            }

        # Build context from semantically relevant chunks
        context_text = "\n\n".join([chunk["text"] for chunk in book_chunks])

        # Build personalized system prompt (use custom or default)
        if not system_prompt:
            system_prompt = self._build_system_prompt(user_profile)

        # Build user prompt with context
        user_prompt = f"""
Book Context:
{context_text}

Current Reading Position:
{' '.join(context_chunks or [])}

Question: {question}

Please provide a clear, informative answer based on the book content. If the answer requires information not in the context, say so clearly.
        """

        # Query LLM using unified service
        try:
            # Determine model ID based on provider
            if not llm_model:
                # Use provider defaults
                model_map = {
                    "gemini": "gemini-2.5-flash",
                    "openai": "gpt-4o-mini",
                    "anthropic": "claude-3-5-sonnet-20241022",
                    "ollama": "llama3.2:3b"
                }
                llm_model = model_map.get(llm_provider, self.default_model)

            # Get user ID for billing
            user_id = user_profile.get("user_id", "anonymous") if user_profile else "anonymous"

            # Use unified LLMProviderService (includes billing and monitoring)
            logger.info(f"RAG query: book={book_id}, provider={llm_provider}, model={llm_model}, user={user_id}")

            response = await self.llm_service.chat(
                user_id=user_id,
                request=ChatRequest(
                    model_id=llm_model,
                    messages=[
                        ChatMessage(role="system", content=system_prompt),
                        ChatMessage(role="user", content=user_prompt)
                    ],
                    temperature=temperature,
                    max_tokens=1000
                ),
                skip_billing=False  # Enable billing for RAG queries
            )

            # Extract answer and metadata
            answer = response.message

            # Get actual token usage from response
            tokens_used = response.usage['total_tokens']
            cost = response.cost

            # Calculate confidence based on response quality
            confidence = 0.8 if len(answer) > 50 else 0.5

            # Log usage for monitoring
            logger.info(f"RAG query: {tokens_used} tokens, ${cost:.6f}, model={llm_model}, provider={llm_provider}")

            # Return result
            return {
                "answer": answer,
                "confidence": confidence,
                "sources": [{"chunk_index": c["chunk_index"]} for c in book_chunks[:3]],
                "tokens_used": tokens_used,
                "cost": cost,
                "model_used": llm_model,
                "provider_used": llm_provider
            }

        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            raise

    def _build_system_prompt(self, user_profile: Optional[Dict[str, Any]] = None) -> str:
        """
        Build personalized system prompt.

        Args:
            user_profile: User profile with preferences

        Returns:
            System prompt string
        """
        base_prompt = """You are an intelligent audiobook companion for InkWave.
Your role is to help readers understand and engage with books through conversation.

Guidelines:
- Provide clear, accurate answers based on the book content
- Adapt your explanations to the user's reading level
- Reference specific passages when relevant
- Be conversational but informative
- If you don't know something, say so honestly
- Never reveal spoilers beyond the user's current position"""

        if user_profile:
            reading_level = user_profile.get("reading_level", "intermediate")
            explanation_depth = user_profile.get("explanation_depth", "detailed")

            base_prompt += f"\n\nUser Preferences:\n- Reading level: {reading_level}\n- Explanation style: {explanation_depth}"

        return base_prompt

    async def generate_embeddings(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Generate embeddings for text chunks using Gemini text-embedding-004.

        Uses the EmbeddingService which provides real 768-dimensional vectors
        via Google's Gemini Embedding API.

        Args:
            texts: List of text strings

        Returns:
            List of 768-dimensional embedding vectors

        Raises:
            ValueError: If service not initialized
            Exception: If embedding generation fails
        """
        if not self._initialized:
            await self.initialize()

        if not texts:
            return []

        try:
            embedding_service = await get_embedding_service()
            embeddings = await embedding_service.generate_embeddings(texts)

            logger.info(f"Generated {len(embeddings)} real embeddings using Gemini text-embedding-004")
            return embeddings

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise


# Global RAG service instance
_rag_service: Optional[RAGService] = None


async def get_rag_service() -> RAGService:
    """
    Get or create RAG service instance.

    Returns:
        RAG service instance
    """
    global _rag_service

    if _rag_service is None:
        _rag_service = RAGService()
        await _rag_service.initialize()

    return _rag_service
