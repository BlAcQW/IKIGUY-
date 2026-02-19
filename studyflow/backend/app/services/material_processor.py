"""
Material processor for StudyFlow.

Background worker that processes uploaded materials with DocumentProcessor
and indexes them into RAG knowledge base.

Now uses shared document_processing module for:
- Topic extraction (AI-powered)
- Collection naming (organization-scoped)
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Optional

# Add shared services to path
sys.path.insert(0, "/opt/kasaai/apps")

from shared.integration.document_processor import DocumentProcessor
from shared.integration.rag import RAGService, RAGConfig, KnowledgeDocument

# Use shared document processing components
from shared.document_processing import (
    TopicExtractor,
    CollectionNaming,
    ProcessingStatus as SharedProcessingStatus,
)

from app.models.material import StudyMaterial, ProcessingStatus
from app.services.material_service import MaterialService
from app.config import settings

logger = logging.getLogger(__name__)

# Shared topic extractor instance
_topic_extractor = TopicExtractor()


class MaterialProcessor:
    """
    Background processor for study materials.

    Processes uploaded files and indexes them into RAG knowledge base.
    """

    _document_processor: Optional[DocumentProcessor] = None
    _rag_service: Optional[RAGService] = None

    @classmethod
    def get_document_processor(cls) -> DocumentProcessor:
        """
        Get or create DocumentProcessor instance.

        Returns:
            DocumentProcessor instance
        """
        if cls._document_processor is None:
            cls._document_processor = DocumentProcessor()
            logger.info("✓ DocumentProcessor initialized")

        return cls._document_processor

    @classmethod
    def get_rag_service(cls) -> RAGService:
        """
        Get or create RAG service instance.

        Returns:
            RAGService instance
        """
        if cls._rag_service is None:
            config = RAGConfig(
                postgres_host=settings.POSTGRES_HOST,
                postgres_port=settings.POSTGRES_PORT,
                postgres_user=settings.POSTGRES_USER,
                postgres_password=settings.POSTGRES_PASSWORD,
                postgres_db=settings.POSTGRES_DB,
                ai_provider=settings.AI_PROVIDER,
                api_key=settings.GEMINI_API_KEY,
                llm_model=settings.GEMINI_MODEL,
                embedding_model=settings.GEMINI_EMBEDDING_MODEL
            )

            cls._rag_service = RAGService(config)
            logger.info("✓ RAG Service initialized for material processing")

        return cls._rag_service

    @staticmethod
    async def process_material(material_id: str) -> bool:
        """
        Process a material: extract text, chunk, and index into RAG.

        Args:
            material_id: Material ID to process

        Returns:
            True if successful, False otherwise
        """
        material = None
        try:
            # Get material
            material = await MaterialService.get_material_by_id(material_id)
            if not material:
                logger.error(f"Material not found: {material_id}")
                return False

            # Update status to processing
            await MaterialService.update_processing_status(
                material_id,
                ProcessingStatus.PROCESSING
            )

            logger.info(f"Processing material: {material.title} ({material_id})")

            # Download file from storage if needed (for Hetzner storage)
            from app.services.storage_service import get_storage_service
            import tempfile
            import os
            
            storage_service = await get_storage_service()
            file_content = await storage_service.download_material_file(material.file_path)
            
            if not file_content:
                raise Exception(f"Failed to download file from storage: {material.file_path}")
            
            # Save to temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{material.file_name}") as tmp_file:
                tmp_path = tmp_file.name
                tmp_file.write(file_content)
            
            try:
                # Process document
                processor = MaterialProcessor.get_document_processor()
                processed_doc = await processor.process_file(tmp_path)
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

            logger.info(
                f"Document processed: {processed_doc.total_chunks} chunks, "
                f"{processed_doc.metadata.word_count} words"
            )

            # Extract topics from document content using AI (if topics are empty)
            # Now using shared TopicExtractor for consistency across apps
            if not material.topics or len(material.topics) == 0:
                try:
                    # Get combined content from first few chunks
                    content_sample = "\n\n".join([
                        chunk.content for chunk in processed_doc.chunks[:3]
                    ])

                    # Use shared topic extractor
                    extracted_topics = await _topic_extractor.extract_from_content(
                        content=content_sample,
                        title=material.title,
                        category=material.subject,
                        max_topics=5
                    )

                    if extracted_topics and len(extracted_topics) > 0:
                        # Update material with extracted topics
                        from app.models.material import MaterialUpdate
                        await MaterialService.update_material(
                            material_id,
                            MaterialUpdate(topics=extracted_topics)
                        )
                        material.topics = extracted_topics
                        logger.info(f"✓ Extracted topics from content: {extracted_topics}")

                except Exception as e:
                    logger.error(f"Topic extraction failed: {e}")
                    # Continue processing even if topic extraction fails

            # Create knowledge documents from chunks with organization metadata
            knowledge_docs = []
            for chunk in processed_doc.chunks:
                doc = KnowledgeDocument(
                    title=f"{material.title} - Part {chunk.chunk_index + 1}",
                    content=chunk.content,
                    category=material.subject,
                    source=material.file_name,
                    tags=material.topics,
                    metadata={
                        "organization_id": material.organization_id,  # NEW - Organization scoping
                        "material_id": material_id,
                        "grade": material.grade,
                        "school_id": material.school_id,
                        "uploaded_by": material.uploaded_by,
                        "chunk_index": chunk.chunk_index,
                        "char_start": chunk.char_start,
                        "char_end": chunk.char_end,
                        "word_count": chunk.word_count
                    }
                )
                knowledge_docs.append(doc)

            # Get organization-scoped collection name using shared utility
            collection_name = CollectionNaming.for_subject_grade(
                app_name="studyflow",
                subject=material.subject,
                grade=material.grade,
                organization_id=material.organization_id
            )

            # Index into RAG
            rag = MaterialProcessor.get_rag_service()
            result = await rag.initialize_knowledge_base(
                collection_name=collection_name,
                documents=knowledge_docs
            )

            logger.info(
                f"Material indexed: {result.get('documents_added', 0)} documents "
                f"added to collection '{collection_name}'"
            )

            # Update material status
            await MaterialService.update_processing_status(
                material_id,
                ProcessingStatus.COMPLETED,
                chunks_count=processed_doc.total_chunks,
                embedding_collection=collection_name
            )

            logger.info(f"✓ Material processing complete: {material.title}")
            return True

        except Exception as e:
            logger.error(f"Material processing error: {str(e)}")
            import traceback
            traceback.print_exc()

            # Update status to failed
            if material:
                await MaterialService.update_processing_status(
                    material_id,
                    ProcessingStatus.FAILED
                )

            return False

    @staticmethod
    async def process_materials_batch(material_ids: list[str]) -> dict:
        """
        Process multiple materials in batch.

        Args:
            material_ids: List of material IDs to process

        Returns:
            Dict with success/failure counts
        """
        results = {
            "total": len(material_ids),
            "successful": 0,
            "failed": 0
        }

        for material_id in material_ids:
            success = await MaterialProcessor.process_material(material_id)
            if success:
                results["successful"] += 1
            else:
                results["failed"] += 1

        logger.info(
            f"Batch processing complete: {results['successful']}/{results['total']} successful"
        )
        return results

    @staticmethod
    async def reindex_material(material_id: str) -> bool:
        """
        Re-index a material into RAG knowledge base.

        Useful when material metadata is updated or RAG configuration changes.

        Args:
            material_id: Material ID to reindex

        Returns:
            True if successful, False otherwise
        """
        # TODO: Delete existing embeddings first
        # Then reprocess
        return await MaterialProcessor.process_material(material_id)


async def process_material_worker(material_id: str):
    """
    Background worker function for material processing.

    Can be called from API routes or background tasks.

    Args:
        material_id: Material ID to process
    """
    await MaterialProcessor.process_material(material_id)


# Example usage for testing
if __name__ == "__main__":
    import asyncio

    async def test_processing():
        """Test material processing."""
        # This requires a material to be uploaded first
        test_material_id = "your_material_id_here"

        print(f"Processing material: {test_material_id}")
        success = await MaterialProcessor.process_material(test_material_id)

        if success:
            print("✓ Processing successful")
        else:
            print("✗ Processing failed")

    asyncio.run(test_processing())
