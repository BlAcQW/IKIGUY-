"""
Document Processing Pipeline for KasaAI Applications.

Provides a reusable background processing pipeline for documents:
- Text extraction (PDF, DOCX, TXT)
- Chunking with configurable strategies
- Topic extraction
- RAG indexing with organization scoping
- Status tracking

Author: KasaAI Team
Date: 2025-11-28
"""

import logging
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from pydantic import BaseModel

# Add shared to path
sys.path.insert(0, "/opt/kasaai/apps")

from .models import (
    BaseDocument,
    DocumentChunk,
    EmbeddingMetadata,
    ProcessingResult,
    ProcessingStatus,
)
from .topic_extractor import TopicExtractor
from .collection_naming import CollectionNaming

logger = logging.getLogger(__name__)


class ProcessingConfig(BaseModel):
    """Configuration for document processing pipeline."""

    # Chunking settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    max_chunk_size: int = 2000

    # Topic extraction
    extract_topics: bool = True
    max_topics: int = 5

    # RAG settings
    enable_rag: bool = True
    embedding_batch_size: int = 50

    # App identification
    app_name: str = "kasaai"

    # Callbacks
    on_status_change: Optional[Callable] = None


class DocumentProcessorBase(ABC):
    """
    Abstract base class for document processors.

    Implement this for app-specific processing needs.
    """

    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[BaseDocument]:
        """Fetch document by ID."""
        pass

    @abstractmethod
    async def update_status(
        self,
        document_id: str,
        status: ProcessingStatus,
        **kwargs,
    ) -> None:
        """Update document processing status."""
        pass

    @abstractmethod
    async def store_chunks(
        self,
        document_id: str,
        chunks: List[DocumentChunk],
    ) -> int:
        """Store extracted chunks."""
        pass

    @abstractmethod
    async def update_topics(
        self,
        document_id: str,
        topics: List[str],
    ) -> None:
        """Update document topics."""
        pass


class DocumentProcessingPipeline:
    """
    Reusable document processing pipeline.

    Handles the full processing flow:
    1. Fetch document
    2. Update status to PROCESSING
    3. Extract text
    4. Create chunks
    5. Extract topics (optional)
    6. Index into RAG (optional)
    7. Update status to COMPLETED

    Usage:
        # Create app-specific processor
        class MyDocProcessor(DocumentProcessorBase):
            async def get_document(self, doc_id):
                return await MyService.get(doc_id)
            # ... implement other methods

        # Create pipeline
        pipeline = DocumentProcessingPipeline(
            processor=MyDocProcessor(),
            config=ProcessingConfig(app_name="myapp")
        )

        # Process document
        result = await pipeline.process(document_id)
    """

    def __init__(
        self,
        processor: DocumentProcessorBase,
        config: ProcessingConfig,
        rag_service=None,
        document_processor=None,
    ):
        """
        Initialize processing pipeline.

        Args:
            processor: App-specific document processor
            config: Processing configuration
            rag_service: Optional RAGService instance
            document_processor: Optional DocumentProcessor instance
        """
        self.processor = processor
        self.config = config
        self._rag_service = rag_service
        self._document_processor = document_processor
        self._topic_extractor = TopicExtractor()

    @property
    def document_processor(self):
        """Lazy load document processor."""
        if self._document_processor is None:
            try:
                from shared.integration.document_processor import DocumentProcessor

                self._document_processor = DocumentProcessor(
                    chunk_size=self.config.chunk_size,
                    chunk_overlap=self.config.chunk_overlap,
                    min_chunk_size=self.config.min_chunk_size,
                    max_chunk_size=self.config.max_chunk_size,
                )
                logger.info("DocumentProcessor initialized")
            except Exception as e:
                logger.error(f"Failed to initialize DocumentProcessor: {e}")
                raise
        return self._document_processor

    @property
    def rag_service(self):
        """Lazy load RAG service."""
        if self._rag_service is None and self.config.enable_rag:
            try:
                from shared.integration.rag import create_rag_service_from_env

                self._rag_service = create_rag_service_from_env(ai_provider="gemini")
                logger.info("RAGService initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize RAGService: {e}")
        return self._rag_service

    async def process(self, document_id: str) -> ProcessingResult:
        """
        Process a document through the full pipeline.

        Args:
            document_id: Document ID to process

        Returns:
            ProcessingResult with success/failure info
        """
        start_time = datetime.utcnow()
        document = None

        try:
            # 1. Fetch document
            document = await self.processor.get_document(document_id)
            if not document:
                logger.error(f"Document not found: {document_id}")
                return ProcessingResult(
                    success=False,
                    document_id=document_id,
                    error_message="Document not found",
                )

            # 2. Update status to PROCESSING
            await self.processor.update_status(
                document_id, ProcessingStatus.PROCESSING
            )
            logger.info(f"Processing document: {document.title} ({document_id})")

            # 3. Extract text
            if not Path(document.file_path).exists():
                raise FileNotFoundError(f"File not found: {document.file_path}")

            processed_doc = await self.document_processor.process_file(
                document.file_path
            )
            logger.info(
                f"Extracted {processed_doc.total_chunks} chunks, "
                f"{processed_doc.metadata.word_count} words"
            )

            # 4. Create and store chunks
            chunks = []
            for i, chunk in enumerate(processed_doc.chunks):
                doc_chunk = DocumentChunk(
                    chunk_id=f"{document_id}_chunk_{i}",
                    document_id=document_id,
                    chunk_index=i,
                    content=chunk.content,
                    word_count=chunk.word_count,
                    char_start=chunk.char_start,
                    char_end=chunk.char_end,
                    metadata={
                        "organization_id": document.organization_id,
                        "uploaded_by": document.uploaded_by,
                    },
                )
                chunks.append(doc_chunk)

            chunks_stored = await self.processor.store_chunks(document_id, chunks)
            logger.info(f"Stored {chunks_stored} chunks")

            # 5. Extract topics (optional)
            topics_extracted = []
            if self.config.extract_topics and not document.topics:
                content_sample = "\n\n".join(
                    [c.content for c in processed_doc.chunks[:3]]
                )
                topics_extracted = await self._topic_extractor.extract_from_content(
                    content=content_sample,
                    title=document.title,
                    category=document.metadata.get("category", ""),
                    max_topics=self.config.max_topics,
                )
                if topics_extracted:
                    await self.processor.update_topics(document_id, topics_extracted)
                    logger.info(f"Extracted topics: {topics_extracted}")

            # 6. Index into RAG (optional)
            embedding_collection = None
            if self.config.enable_rag and self.rag_service:
                embedding_collection = await self._index_to_rag(
                    document, processed_doc.chunks, topics_extracted
                )

            # 7. Update status to COMPLETED
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            await self.processor.update_status(
                document_id,
                ProcessingStatus.COMPLETED,
                chunks_count=len(chunks),
                embedding_collection=embedding_collection,
                processed_at=datetime.utcnow(),
            )

            logger.info(
                f"Document processing complete: {document.title} "
                f"({processing_time:.2f}s)"
            )

            return ProcessingResult(
                success=True,
                document_id=document_id,
                chunks_count=len(chunks),
                embedding_collection=embedding_collection,
                processing_time=processing_time,
                page_count=processed_doc.metadata.page_count,
                word_count=processed_doc.metadata.word_count,
                topics_extracted=topics_extracted,
            )

        except Exception as e:
            logger.error(f"Document processing error: {str(e)}")
            import traceback

            traceback.print_exc()

            # Update status to FAILED
            if document:
                await self.processor.update_status(
                    document_id,
                    ProcessingStatus.FAILED,
                    error_message=str(e),
                )

            processing_time = (datetime.utcnow() - start_time).total_seconds()
            return ProcessingResult(
                success=False,
                document_id=document_id,
                error_message=str(e),
                processing_time=processing_time,
            )

    async def _index_to_rag(
        self,
        document: BaseDocument,
        chunks: List,
        topics: List[str],
    ) -> Optional[str]:
        """
        Index document chunks into RAG knowledge base.

        Args:
            document: Document being processed
            chunks: Extracted chunks
            topics: Extracted topics

        Returns:
            Collection name if successful
        """
        try:
            from shared.integration.rag import KnowledgeDocument

            # Build collection name
            collection_name = CollectionNaming.for_document(
                app_name=self.config.app_name,
                document_id=document.id,
                organization_id=document.organization_id,
            )

            # Create knowledge documents with metadata
            knowledge_docs = []
            for chunk in chunks:
                metadata = EmbeddingMetadata(
                    organization_id=document.organization_id,
                    document_id=document.id,
                    chunk_index=chunk.chunk_index,
                    document_type=document.file_type.value,
                    uploaded_by=document.uploaded_by,
                    topics=topics or document.topics,
                )

                doc = KnowledgeDocument(
                    title=f"{document.title} - Part {chunk.chunk_index + 1}",
                    content=chunk.content,
                    category=document.metadata.get("category", "general"),
                    source=document.file_name,
                    tags=topics or document.topics,
                    metadata=metadata.to_dict(),
                )
                knowledge_docs.append(doc)

            # Index into RAG
            result = await self.rag_service.initialize_knowledge_base(
                collection_name=collection_name,
                documents=knowledge_docs,
            )

            logger.info(
                f"Indexed {result.get('chunks_created', 0)} chunks "
                f"to collection '{collection_name}'"
            )
            return collection_name

        except Exception as e:
            logger.error(f"RAG indexing failed: {e}")
            return None

    async def process_batch(
        self,
        document_ids: List[str],
        parallel: bool = False,
    ) -> Dict[str, ProcessingResult]:
        """
        Process multiple documents.

        Args:
            document_ids: List of document IDs
            parallel: Whether to process in parallel

        Returns:
            Dictionary of document_id -> ProcessingResult
        """
        results = {}

        if parallel:
            import asyncio

            tasks = [self.process(doc_id) for doc_id in document_ids]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            for doc_id, result in zip(document_ids, batch_results):
                if isinstance(result, Exception):
                    results[doc_id] = ProcessingResult(
                        success=False,
                        document_id=doc_id,
                        error_message=str(result),
                    )
                else:
                    results[doc_id] = result
        else:
            for doc_id in document_ids:
                results[doc_id] = await self.process(doc_id)

        successful = sum(1 for r in results.values() if r.success)
        logger.info(
            f"Batch complete: {successful}/{len(document_ids)} successful"
        )
        return results

    async def reindex(self, document_id: str) -> ProcessingResult:
        """
        Re-index a document into RAG.

        Args:
            document_id: Document ID to reindex

        Returns:
            ProcessingResult
        """
        await self.processor.update_status(
            document_id, ProcessingStatus.REPROCESSING
        )
        return await self.process(document_id)


async def process_document_worker(
    document_id: str,
    processor: DocumentProcessorBase,
    config: ProcessingConfig,
) -> ProcessingResult:
    """
    Background worker function for document processing.

    Can be called from FastAPI BackgroundTasks or async workers.

    Args:
        document_id: Document ID to process
        processor: App-specific document processor
        config: Processing configuration

    Returns:
        ProcessingResult
    """
    pipeline = DocumentProcessingPipeline(processor=processor, config=config)
    return await pipeline.process(document_id)
