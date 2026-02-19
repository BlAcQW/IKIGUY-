"""
Document Management Service for RAG Knowledge Base.
Handles CRUD operations, versioning, and metadata management using MongoDB.
"""

import os
import logging
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
import asyncio

from backend.models.knowledge_base import (
    KnowledgeDocument,
    DocumentCreate,
    DocumentUpdate,
    DocumentFilter,
    DocumentVersion,
    DocumentMetadata,
    DocumentStatus,
    DocumentSource,
    DocumentResponse,
    DocumentListResponse,
    BulkDeleteRequest,
    BulkDeleteResponse
)
from backend.services.helpdesk_rag_service import helpdesk_rag_service

logger = logging.getLogger(__name__)


class DocumentManagementService:
    """Service for managing knowledge base documents in MongoDB."""

    def __init__(self):
        """Initialize the document management service."""
        # MongoDB connection
        mongodb_url = os.getenv("MONGODB_URL")
        if not mongodb_url:
            raise ValueError("MONGODB_URL environment variable is required")

        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.mongodb_url = mongodb_url
        self.db_name = os.getenv("MONGODB_DB_NAME", "kasaai_core")

        # Collections
        self.documents_collection_name = "kb_documents"
        self.metrics_collection_name = "rag_query_metrics"

    async def _ensure_connection(self):
        """Ensure MongoDB connection is established."""
        if self.client is None:
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.db = self.client[self.db_name]

            # Create indexes
            await self._create_indexes()
            logger.info("MongoDB connection established for document management")

    async def _create_indexes(self):
        """Create MongoDB indexes for efficient queries."""
        try:
            documents_collection = self.db[self.documents_collection_name]

            # Indexes for documents collection
            await documents_collection.create_index([("company_name", ASCENDING)])
            await documents_collection.create_index([("status", ASCENDING)])
            await documents_collection.create_index([("category", ASCENDING)])
            await documents_collection.create_index([("tags", ASCENDING)])
            await documents_collection.create_index([("created_at", DESCENDING)])
            await documents_collection.create_index([("updated_at", DESCENDING)])
            await documents_collection.create_index([("company_name", ASCENDING), ("status", ASCENDING)])

            # Text index for search
            await documents_collection.create_index([("title", "text"), ("content", "text")])

            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")

    @staticmethod
    def _calculate_content_hash(content: str) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @staticmethod
    def _get_collection_name(company_name: str) -> str:
        """Get sanitized collection name for company."""
        return f"helpdesk_{company_name.lower().replace(' ', '_').replace('-', '_')}"

    async def create_document(self, doc_create: DocumentCreate) -> DocumentResponse:
        """
        Create a new document in MongoDB and index it in the vector store.

        Args:
            doc_create: Document creation request

        Returns:
            DocumentResponse with created document
        """
        try:
            await self._ensure_connection()

            # Create document object
            collection_name = self._get_collection_name(doc_create.company_name)
            content_hash = self._calculate_content_hash(doc_create.content)

            metadata = DocumentMetadata(
                word_count=len(doc_create.content.split()),
                character_count=len(doc_create.content)
            )

            document = KnowledgeDocument(
                company_name=doc_create.company_name,
                collection_name=collection_name,
                title=doc_create.title,
                content=doc_create.content,
                content_hash=content_hash,
                category=doc_create.category,
                tags=doc_create.tags,
                source=doc_create.source,
                source_uri=doc_create.source_uri,
                status=DocumentStatus.PENDING,
                metadata=metadata,
                created_by=doc_create.created_by
            )

            # Save to MongoDB
            documents_collection = self.db[self.documents_collection_name]
            result = await documents_collection.insert_one(document.model_dump(by_alias=True))

            logger.info(f"Document created in MongoDB: {document.id} for {doc_create.company_name}")

            # Index in vector store (async background task)
            asyncio.create_task(self._index_document_async(document))

            return DocumentResponse(
                success=True,
                document=document,
                message="Document created successfully"
            )

        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            return DocumentResponse(
                success=False,
                message=f"Failed to create document: {str(e)}"
            )

    async def _index_document_async(self, document: KnowledgeDocument):
        """
        Index document in vector store asynchronously.

        Args:
            document: Document to index
        """
        try:
            # Update status to processing
            await self.update_document_status(document.id, DocumentStatus.PROCESSING)

            # Convert to helpdesk RAG service format
            from backend.services.helpdesk_rag_service import KnowledgeDocument as RAGDocument

            rag_doc = RAGDocument(
                id=document.id,
                title=document.title,
                content=document.content,
                category=document.category,
                source=document.source_uri or str(document.source),
                tags=document.tags,
                metadata={
                    "document_id": document.id,
                    "created_at": document.created_at.isoformat(),
                    "word_count": document.metadata.word_count
                }
            )

            # Index in vector store and get vector IDs
            result = await helpdesk_rag_service.update_knowledge_base(
                company_name=document.company_name,
                documents=[rag_doc]
            )

            # Extract vector IDs from result if available
            vector_ids = result.get("vector_ids", [])

            # Update status to indexed with vector IDs
            await self._update_document_vectors(
                document.id,
                vector_ids=vector_ids,
                indexed_at=datetime.utcnow(),
                chunk_count=result.get("chunks_updated", 0)
            )

            logger.info(f"Document indexed successfully: {document.id} with {len(vector_ids)} vectors")

        except Exception as e:
            logger.error(f"Error indexing document {document.id}: {str(e)}")
            # Update status to failed
            await self.update_document_status(document.id, DocumentStatus.FAILED)

    async def update_document_status(
        self,
        document_id: str,
        status: DocumentStatus,
        indexed_at: Optional[datetime] = None,
        chunk_count: Optional[int] = None
    ):
        """
        Update document status.

        Args:
            document_id: Document ID
            status: New status
            indexed_at: Indexing timestamp
            chunk_count: Number of chunks created
        """
        try:
            await self._ensure_connection()
            documents_collection = self.db[self.documents_collection_name]

            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }

            if indexed_at:
                update_data["indexed_at"] = indexed_at

            if chunk_count is not None:
                update_data["metadata.chunk_count"] = chunk_count

            await documents_collection.update_one(
                {"id": document_id},
                {"$set": update_data}
            )

        except Exception as e:
            logger.error(f"Error updating document status: {str(e)}")

    async def _update_document_vectors(
        self,
        document_id: str,
        vector_ids: List[str],
        indexed_at: datetime,
        chunk_count: int
    ):
        """
        Update document with vector IDs after indexing.

        Args:
            document_id: Document ID
            vector_ids: List of vector IDs created in PGVector
            indexed_at: Indexing timestamp
            chunk_count: Number of chunks created
        """
        try:
            await self._ensure_connection()
            documents_collection = self.db[self.documents_collection_name]

            update_data = {
                "status": DocumentStatus.INDEXED,
                "vector_ids": vector_ids,
                "indexed_at": indexed_at,
                "metadata.chunk_count": chunk_count,
                "updated_at": datetime.utcnow()
            }

            await documents_collection.update_one(
                {"id": document_id},
                {"$set": update_data}
            )

            logger.info(f"Updated document {document_id} with {len(vector_ids)} vector IDs")

        except Exception as e:
            logger.error(f"Error updating document vectors: {str(e)}")

    async def get_document(self, document_id: str) -> DocumentResponse:
        """
        Get a single document by ID.

        Args:
            document_id: Document ID

        Returns:
            DocumentResponse with document data
        """
        try:
            await self._ensure_connection()
            documents_collection = self.db[self.documents_collection_name]

            doc_dict = await documents_collection.find_one({"id": document_id})

            if not doc_dict:
                return DocumentResponse(
                    success=False,
                    message=f"Document {document_id} not found"
                )

            document = KnowledgeDocument(**doc_dict)

            return DocumentResponse(
                success=True,
                document=document,
                message="Document retrieved successfully"
            )

        except Exception as e:
            logger.error(f"Error retrieving document: {str(e)}")
            return DocumentResponse(
                success=False,
                message=f"Failed to retrieve document: {str(e)}"
            )

    async def list_documents(self, filter_params: DocumentFilter) -> DocumentListResponse:
        """
        List documents with filtering, search, and pagination.

        Args:
            filter_params: Filter and pagination parameters

        Returns:
            DocumentListResponse with documents and metadata
        """
        try:
            await self._ensure_connection()
            documents_collection = self.db[self.documents_collection_name]

            # Build query
            query = {"company_name": filter_params.company_name}

            if filter_params.category:
                query["category"] = filter_params.category

            if filter_params.tags:
                query["tags"] = {"$in": filter_params.tags}

            if filter_params.status:
                query["status"] = filter_params.status

            if filter_params.source:
                query["source"] = filter_params.source

            if filter_params.is_active is not None:
                query["is_active"] = filter_params.is_active

            if filter_params.is_archived is not None:
                query["is_archived"] = filter_params.is_archived

            if filter_params.created_after:
                query["created_at"] = {"$gte": filter_params.created_after}

            if filter_params.created_before:
                if "created_at" in query:
                    query["created_at"]["$lte"] = filter_params.created_before
                else:
                    query["created_at"] = {"$lte": filter_params.created_before}

            # Text search
            if filter_params.search_query:
                query["$text"] = {"$search": filter_params.search_query}

            # Count total
            total_count = await documents_collection.count_documents(query)

            # Calculate pagination
            skip = (filter_params.page - 1) * filter_params.page_size
            total_pages = (total_count + filter_params.page_size - 1) // filter_params.page_size

            # Sort
            sort_order = ASCENDING if filter_params.sort_order == "asc" else DESCENDING
            sort_field = filter_params.sort_by

            # Query documents
            cursor = documents_collection.find(query).sort(sort_field, sort_order).skip(skip).limit(filter_params.page_size)

            documents = []
            async for doc_dict in cursor:
                doc = KnowledgeDocument(**doc_dict)
                documents.append(doc.model_dump(mode='json'))

            return DocumentListResponse(
                success=True,
                documents=documents,
                total_count=total_count,
                page=filter_params.page,
                page_size=filter_params.page_size,
                total_pages=total_pages
            )

        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return DocumentListResponse(
                success=False,
                documents=[],
                total_count=0,
                page=filter_params.page,
                page_size=filter_params.page_size,
                total_pages=0
            )

    async def update_document(
        self,
        document_id: str,
        doc_update: DocumentUpdate
    ) -> DocumentResponse:
        """
        Update a document and create a new version.

        Args:
            document_id: Document ID
            doc_update: Update data

        Returns:
            DocumentResponse with updated document
        """
        try:
            await self._ensure_connection()
            documents_collection = self.db[self.documents_collection_name]

            # Get existing document
            existing_doc_dict = await documents_collection.find_one({"id": document_id})
            if not existing_doc_dict:
                return DocumentResponse(
                    success=False,
                    message=f"Document {document_id} not found"
                )

            existing_doc = KnowledgeDocument(**existing_doc_dict)

            # Create version from current state
            version = DocumentVersion(
                version_number=existing_doc.current_version,
                content=existing_doc.content,
                title=existing_doc.title,
                category=existing_doc.category,
                tags=existing_doc.tags,
                changed_by=doc_update.updated_by,
                change_reason=doc_update.change_reason
            )

            # Prepare update data
            update_data = {"updated_at": datetime.utcnow()}

            if doc_update.title is not None:
                update_data["title"] = doc_update.title

            if doc_update.content is not None:
                update_data["content"] = doc_update.content
                update_data["content_hash"] = self._calculate_content_hash(doc_update.content)
                update_data["status"] = DocumentStatus.PENDING  # Needs re-indexing
                update_data["metadata.word_count"] = len(doc_update.content.split())
                update_data["metadata.character_count"] = len(doc_update.content)

            if doc_update.category is not None:
                update_data["category"] = doc_update.category

            if doc_update.tags is not None:
                update_data["tags"] = doc_update.tags

            if doc_update.is_active is not None:
                update_data["is_active"] = doc_update.is_active

            if doc_update.is_archived is not None:
                update_data["is_archived"] = doc_update.is_archived

            if doc_update.updated_by:
                update_data["updated_by"] = doc_update.updated_by

            # Increment version if content changed
            if doc_update.content is not None:
                update_data["current_version"] = existing_doc.current_version + 1

            # Update document and add version
            await documents_collection.update_one(
                {"id": document_id},
                {
                    "$set": update_data,
                    "$push": {"versions": version.model_dump(by_alias=True)}
                }
            )

            # Get updated document
            updated_doc_dict = await documents_collection.find_one({"id": document_id})
            updated_doc = KnowledgeDocument(**updated_doc_dict)

            # Re-index if content changed
            if doc_update.content is not None:
                asyncio.create_task(self._index_document_async(updated_doc))

            return DocumentResponse(
                success=True,
                document=updated_doc,
                message="Document updated successfully"
            )

        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            return DocumentResponse(
                success=False,
                message=f"Failed to update document: {str(e)}"
            )

    async def delete_document(
        self,
        document_id: str,
        company_name: str
    ) -> DocumentResponse:
        """
        Delete a document from MongoDB and vector store.

        Args:
            document_id: Document ID
            company_name: Company identifier

        Returns:
            DocumentResponse with deletion status
        """
        try:
            await self._ensure_connection()
            documents_collection = self.db[self.documents_collection_name]

            # Get document
            doc_dict = await documents_collection.find_one({"id": document_id})
            if not doc_dict:
                return DocumentResponse(
                    success=False,
                    message=f"Document {document_id} not found"
                )

            document = KnowledgeDocument(**doc_dict)

            # Delete vectors from vector store using document metadata
            try:
                await self._delete_document_vectors(document)
                logger.info(f"Deleted {len(document.vector_ids)} vectors for document {document_id}")
            except Exception as vec_error:
                # Log error but continue with MongoDB deletion
                logger.error(f"Error deleting vectors for document {document_id}: {str(vec_error)}")

            # Delete from MongoDB
            await documents_collection.delete_one({"id": document_id})

            return DocumentResponse(
                success=True,
                message="Document and associated vectors deleted successfully"
            )

        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return DocumentResponse(
                success=False,
                message=f"Failed to delete document: {str(e)}"
            )

    async def _delete_document_vectors(self, document: KnowledgeDocument):
        """
        Delete vectors from PGVector for a document.

        Args:
            document: Document with vector IDs to delete
        """
        try:
            # Get vectorstore from RAG service
            vectorstore = await helpdesk_rag_service._get_vectorstore(document.company_name)

            # Delete documents by metadata filter (doc_id)
            # PGVector uses metadata filtering for deletion
            # Reason: LangChain PGVector doesn't support direct ID deletion,
            # so we filter by the document_id in metadata
            if hasattr(vectorstore, 'delete'):
                # Try to delete using metadata filter
                await asyncio.to_thread(
                    vectorstore.delete,
                    filter={"doc_id": document.id}
                )
                logger.info(f"Deleted vectors for document {document.id} using metadata filter")
            else:
                # Fallback: Log that vectors couldn't be deleted
                logger.warning(
                    f"Vector store doesn't support deletion. "
                    f"Manual cleanup may be needed for document {document.id}"
                )

        except Exception as e:
            logger.error(f"Error deleting vectors for document {document.id}: {str(e)}")
            raise

    async def bulk_delete_documents(
        self,
        bulk_delete: BulkDeleteRequest
    ) -> BulkDeleteResponse:
        """
        Delete multiple documents in bulk.

        Args:
            bulk_delete: Bulk delete request

        Returns:
            BulkDeleteResponse with results
        """
        try:
            await self._ensure_connection()

            deleted_count = 0
            failed_count = 0
            failed_ids = []
            errors = []

            for doc_id in bulk_delete.document_ids:
                try:
                    response = await self.delete_document(doc_id, bulk_delete.company_name)
                    if response.success:
                        deleted_count += 1
                    else:
                        failed_count += 1
                        failed_ids.append(doc_id)
                        errors.append(f"{doc_id}: {response.message}")
                except Exception as e:
                    failed_count += 1
                    failed_ids.append(doc_id)
                    errors.append(f"{doc_id}: {str(e)}")

            return BulkDeleteResponse(
                success=failed_count == 0,
                deleted_count=deleted_count,
                failed_count=failed_count,
                failed_ids=failed_ids,
                errors=errors
            )

        except Exception as e:
            logger.error(f"Error in bulk delete: {str(e)}")
            return BulkDeleteResponse(
                success=False,
                deleted_count=0,
                failed_count=len(bulk_delete.document_ids),
                failed_ids=bulk_delete.document_ids,
                errors=[str(e)]
            )


# Global service instance
document_management_service = DocumentManagementService()
