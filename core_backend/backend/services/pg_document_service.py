"""
PostgreSQL-based Document Management Service for RAG Knowledge Base.
Uses PostgreSQL as single source of truth for both metadata and vectors.
"""

import os
import logging
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import ThreadedConnectionPool

from backend.models.knowledge_base import (
    KnowledgeDocument,
    DocumentCreate,
    DocumentUpdate,
    DocumentFilter,
    DocumentMetadata,
    DocumentStatus,
    DocumentResponse,
    DocumentListResponse,
    BulkDeleteRequest,
    BulkDeleteResponse
)

logger = logging.getLogger(__name__)


class PostgreSQLDocumentService:
    """
    Service for managing knowledge base documents in PostgreSQL.
    Replaces MongoDB with PostgreSQL as the single source of truth.
    """

    def __init__(self):
        """Initialize the PostgreSQL document service."""
        # Connection parameters
        self.pg_user = os.getenv('POSTGRES_USER', 'postgres')
        self.pg_password = os.getenv('POSTGRES_PASSWORD', 'aawwER444444')
        self.pg_server = os.getenv('POSTGRES_SERVER', 'localhost')
        self.pg_port = os.getenv('POSTGRES_PORT', '5432')
        self.pg_database = os.getenv('POSTGRES_DB_CORE', 'kasaai_core')

        # Connection pool
        self.pool = None
        self._init_connection_pool()

    def _init_connection_pool(self):
        """Initialize PostgreSQL connection pool."""
        try:
            conn_string = (
                f"host={self.pg_server} "
                f"port={self.pg_port} "
                f"dbname={self.pg_database} "
                f"user={self.pg_user} "
                f"password={self.pg_password}"
            )

            self.pool = ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                dsn=conn_string
            )
            logger.info("PostgreSQL connection pool initialized for document management")
        except Exception as e:
            logger.error(f"Error creating connection pool: {str(e)}")
            raise

    def get_connection(self):
        """Get a connection from the pool."""
        return self.pool.getconn()

    def return_connection(self, conn):
        """Return a connection to the pool."""
        self.pool.putconn(conn)

    @staticmethod
    def _calculate_content_hash(content: str) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @staticmethod
    def _get_collection_name(company_name: str) -> str:
        """Get sanitized collection name for company."""
        return f"helpdesk_{company_name.lower().replace(' ', '_').replace('-', '_')}"

    def _row_to_document(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert PostgreSQL row to document dict."""
        # Build metadata
        metadata = row.get('metadata', {})
        if isinstance(metadata, str):
            import json
            metadata = json.loads(metadata)

        doc_metadata = DocumentMetadata(
            word_count=metadata.get('word_count', 0),
            character_count=metadata.get('character_count', 0),
            chunk_count=metadata.get('chunk_count', 1),
            chunk_index=metadata.get('chunk_index', 0)
        )

        # Build document
        document = {
            'id': row['document_id'],
            'document_id': row['document_id'],
            'company_name': row['company_name'],
            'collection_name': row['collection_name'],
            'title': row['title'],
            'content': row['content'],
            'content_hash': row.get('content_hash'),
            'category': row['category'],
            'tags': row.get('tags', []),
            'status': row['status'],
            'source': row['source'],
            'source_uri': row.get('source_uri'),
            'created_at': row['created_at'].isoformat() if row.get('created_at') else None,
            'updated_at': row['updated_at'].isoformat() if row.get('updated_at') else None,
            'indexed_at': row['indexed_at'].isoformat() if row.get('indexed_at') else None,
            'metadata': doc_metadata.dict(),
            'vector_ids': row.get('vector_ids', []),
            'is_active': row.get('is_active', True),
            'is_archived': row.get('is_archived', False),
            'current_version': row.get('current_version', 1),
            'created_by': row.get('created_by'),
            'updated_by': row.get('updated_by'),
        }

        return document

    async def create_document(self, doc_create: DocumentCreate) -> DocumentResponse:
        """
        Create a new document in PostgreSQL and index it in the vector store.

        Args:
            doc_create: Document creation request

        Returns:
            DocumentResponse with created document
        """
        import asyncio
        from uuid import uuid4

        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Create document object
            collection_name = self._get_collection_name(doc_create.company_name)
            content_hash = self._calculate_content_hash(doc_create.content)
            document_id = str(uuid4())

            # Calculate metadata
            word_count = len(doc_create.content.split())
            character_count = len(doc_create.content)

            metadata = {
                'word_count': word_count,
                'character_count': character_count,
                'chunk_count': 0
            }

            # Insert document
            insert_query = """
                INSERT INTO kb_documents (
                    document_id, company_name, collection_name, title, content,
                    content_hash, category, tags, source, source_uri, status,
                    metadata, is_active, is_archived, current_version, created_by,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                RETURNING *
            """

            cursor.execute(insert_query, (
                document_id,
                doc_create.company_name,
                collection_name,
                doc_create.title,
                doc_create.content,
                content_hash,
                doc_create.category,
                doc_create.tags,
                doc_create.source,
                doc_create.source_uri,
                DocumentStatus.PENDING.value,
                Json(metadata),
                True,  # is_active
                False,  # is_archived
                1,  # current_version
                doc_create.created_by
            ))

            row = cursor.fetchone()
            conn.commit()
            cursor.close()

            logger.info(f"Document created in PostgreSQL: {document_id} for {doc_create.company_name}")

            # Convert row to document dict
            document_dict = self._row_to_document(row)

            # Index in vector store (async background task)
            asyncio.create_task(self._index_document_async(document_id, doc_create.company_name))

            # Return response without strict validation
            return DocumentResponse.model_construct(
                success=True,
                document=document_dict,
                message="Document created successfully"
            )

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error creating document: {str(e)}")
            return DocumentResponse(
                success=False,
                message=f"Failed to create document: {str(e)}"
            )
        finally:
            if conn:
                self.return_connection(conn)

    async def _index_document_async(self, document_id: str, company_name: str):
        """
        Index document in vector store asynchronously.

        Args:
            document_id: Document ID to index
            company_name: Company identifier
        """
        try:
            # Update status to processing
            await self.update_document_status(document_id, DocumentStatus.PROCESSING)

            # Get document
            doc_response = await self.get_document(document_id)
            if not doc_response.success:
                logger.error(f"Failed to get document {document_id} for indexing")
                return

            document = doc_response.document
            if isinstance(document, dict):
                # Convert dict to proper format for RAG service
                from backend.services.helpdesk_rag_service import KnowledgeDocument as RAGDocument

                rag_doc = RAGDocument(
                    id=document.get('id'),
                    title=document.get('title'),
                    content=document.get('content'),
                    category=document.get('category'),
                    source=document.get('source_uri') or document.get('source'),
                    tags=document.get('tags', []),
                    metadata={
                        "document_id": document.get('id'),
                        "created_at": document.get('created_at'),
                        "word_count": document.get('metadata', {}).get('word_count', 0)
                    }
                )

                # Index in vector store using helpdesk_rag_service
                from backend.services.helpdesk_rag_service import helpdesk_rag_service

                result = await helpdesk_rag_service.update_knowledge_base(
                    company_name=company_name,
                    documents=[rag_doc]
                )

                # Extract vector IDs from result
                vector_ids = result.get("vector_ids", [])
                chunk_count = result.get("chunks_updated", 0)

                # Update document with vector IDs and status
                await self._update_document_vectors(
                    document_id=document_id,
                    vector_ids=vector_ids,
                    chunk_count=chunk_count
                )

                logger.info(f"Document indexed successfully: {document_id} with {len(vector_ids)} vectors")

        except Exception as e:
            logger.error(f"Error indexing document {document_id}: {str(e)}")
            # Update status to failed
            await self.update_document_status(document_id, DocumentStatus.FAILED)

    async def update_document_status(
        self,
        document_id: str,
        status: DocumentStatus
    ):
        """
        Update document status.

        Args:
            document_id: Document ID
            status: New status
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE kb_documents
                SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE document_id = %s
                """,
                (status.value, document_id)
            )

            conn.commit()
            cursor.close()
            logger.info(f"Updated document {document_id} status to {status.value}")

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error updating document status: {str(e)}")
        finally:
            if conn:
                self.return_connection(conn)

    async def _update_document_vectors(
        self,
        document_id: str,
        vector_ids: List[str],
        chunk_count: int
    ):
        """
        Update document with vector IDs after indexing.

        Args:
            document_id: Document ID
            vector_ids: List of vector IDs created in PGVector
            chunk_count: Number of chunks created
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Update metadata with chunk_count
            cursor.execute(
                """
                UPDATE kb_documents
                SET
                    status = %s,
                    vector_ids = %s,
                    indexed_at = CURRENT_TIMESTAMP,
                    metadata = jsonb_set(metadata, '{chunk_count}', %s::text::jsonb),
                    updated_at = CURRENT_TIMESTAMP
                WHERE document_id = %s
                """,
                (
                    DocumentStatus.INDEXED.value,
                    vector_ids,
                    str(chunk_count),
                    document_id
                )
            )

            conn.commit()
            cursor.close()
            logger.info(f"Updated document {document_id} with {len(vector_ids)} vector IDs")

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error updating document vectors: {str(e)}")
        finally:
            if conn:
                self.return_connection(conn)

    async def list_documents(self, filter_params: DocumentFilter) -> DocumentListResponse:
        """
        List documents with filtering, search, and pagination.

        Args:
            filter_params: Filter and pagination parameters

        Returns:
            DocumentListResponse with documents and metadata
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Build WHERE clause
            where_clauses = ["company_name = %s"]
            params = [filter_params.company_name]

            if filter_params.category:
                where_clauses.append("category = %s")
                params.append(filter_params.category)

            if filter_params.tags:
                where_clauses.append("tags && %s")
                params.append(filter_params.tags)

            if filter_params.status:
                where_clauses.append("status = %s")
                params.append(filter_params.status.value if hasattr(filter_params.status, 'value') else filter_params.status)

            if filter_params.source:
                where_clauses.append("source = %s")
                params.append(filter_params.source)

            if filter_params.is_active is not None:
                where_clauses.append("is_active = %s")
                params.append(filter_params.is_active)

            if filter_params.is_archived is not None:
                where_clauses.append("is_archived = %s")
                params.append(filter_params.is_archived)

            if filter_params.created_after:
                where_clauses.append("created_at >= %s")
                params.append(filter_params.created_after)

            if filter_params.created_before:
                where_clauses.append("created_at <= %s")
                params.append(filter_params.created_before)

            # Full-text search
            if filter_params.search_query:
                where_clauses.append(
                    "to_tsvector('english', title || ' ' || content) @@ plainto_tsquery('english', %s)"
                )
                params.append(filter_params.search_query)

            where_clause = " AND ".join(where_clauses)

            # Count total
            count_query = f"SELECT COUNT(*) as total FROM kb_documents WHERE {where_clause}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()['total']

            # Calculate pagination
            skip = (filter_params.page - 1) * filter_params.page_size
            total_pages = (total_count + filter_params.page_size - 1) // filter_params.page_size

            # Sort
            sort_order = "ASC" if filter_params.sort_order == "asc" else "DESC"
            sort_field = filter_params.sort_by

            # Query documents
            query = f"""
                SELECT * FROM kb_documents
                WHERE {where_clause}
                ORDER BY {sort_field} {sort_order}
                LIMIT %s OFFSET %s
            """
            params.extend([filter_params.page_size, skip])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            documents = [self._row_to_document(row) for row in rows]

            cursor.close()

            # Return response without Pydantic validation
            # Reason: Database may have flexible source values not in enum
            return DocumentListResponse.model_construct(
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
                total_pages=0,
                message=f"Failed to list documents: {str(e)}"
            )
        finally:
            if conn:
                self.return_connection(conn)

    async def get_document(self, document_id: str) -> DocumentResponse:
        """
        Get a single document by ID.

        Args:
            document_id: Document ID

        Returns:
            DocumentResponse with document data
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = "SELECT * FROM kb_documents WHERE document_id = %s"
            cursor.execute(query, (document_id,))
            row = cursor.fetchone()

            cursor.close()

            if not row:
                return DocumentResponse(
                    success=False,
                    message=f"Document {document_id} not found"
                )

            document = self._row_to_document(row)

            # Return response without strict validation for flexible source field
            return DocumentResponse.model_construct(
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
        finally:
            if conn:
                self.return_connection(conn)

    async def update_document(
        self,
        document_id: str,
        doc_update: "DocumentUpdate"
    ) -> DocumentResponse:
        """
        Update a document's metadata and/or content.

        Args:
            document_id: Document ID to update
            doc_update: DocumentUpdate with fields to update

        Returns:
            DocumentResponse with updated document
        """
        import asyncio
        conn = None
        try:
            # Get existing document first
            existing_doc_response = await self.get_document(document_id)
            if not existing_doc_response.success:
                return existing_doc_response

            existing_doc = existing_doc_response.document
            company_name = existing_doc['company_name'] if isinstance(existing_doc, dict) else existing_doc.company_name

            # Build update query
            update_fields = []
            params = []

            if doc_update.title is not None:
                update_fields.append("title = %s")
                params.append(doc_update.title)

            if doc_update.content is not None:
                update_fields.append("content = %s")
                params.append(doc_update.content)
                update_fields.append("content_hash = %s")
                params.append(self._calculate_content_hash(doc_update.content))

            if doc_update.category is not None:
                update_fields.append("category = %s")
                params.append(doc_update.category)

            if doc_update.tags is not None:
                update_fields.append("tags = %s")
                params.append(doc_update.tags)  # PostgreSQL text[] array, not JSONB

            if doc_update.is_active is not None:
                update_fields.append("is_active = %s")
                params.append(doc_update.is_active)

            if doc_update.is_archived is not None:
                update_fields.append("is_archived = %s")
                params.append(doc_update.is_archived)

            if doc_update.updated_by is not None:
                update_fields.append("updated_by = %s")
                params.append(doc_update.updated_by)

            # Always update timestamp
            update_fields.append("updated_at = NOW()")

            if not update_fields:
                return DocumentResponse(
                    success=False,
                    message="No fields to update"
                )

            # Add document_id parameter
            params.append(document_id)

            # Execute update
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = f"""
                UPDATE kb_documents
                SET {', '.join(update_fields)}
                WHERE document_id = %s
                RETURNING *
            """

            cursor.execute(query, params)
            row = cursor.fetchone()
            conn.commit()
            cursor.close()

            if not row:
                return DocumentResponse(
                    success=False,
                    message=f"Document {document_id} not found"
                )

            # If content was updated, re-index
            if doc_update.content is not None:
                asyncio.create_task(self._index_document_async(document_id, company_name))

            document = self._row_to_document(row)

            return DocumentResponse.model_construct(
                success=True,
                document=document,
                message="Document updated successfully"
            )

        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            if conn:
                conn.rollback()
            return DocumentResponse(
                success=False,
                message=f"Failed to update document: {str(e)}"
            )
        finally:
            if conn:
                self.return_connection(conn)

    async def delete_document(
        self,
        document_id: str,
        company_name: str
    ) -> DocumentResponse:
        """
        Delete a document from PostgreSQL and vector store.

        Args:
            document_id: Document ID
            company_name: Company identifier

        Returns:
            DocumentResponse with deletion status
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get document first
            cursor.execute(
                "SELECT * FROM kb_documents WHERE document_id = %s",
                (document_id,)
            )
            row = cursor.fetchone()

            if not row:
                cursor.close()
                return DocumentResponse(
                    success=False,
                    message=f"Document {document_id} not found"
                )

            # Delete embeddings from langchain_pg_embedding
            # Reason: Clean up associated vectors
            embeddings_deleted = 0
            try:
                cursor.execute(
                    """
                    DELETE FROM langchain_pg_embedding
                    WHERE cmetadata->>'doc_id' = %s
                    """,
                    (document_id,)
                )
                embeddings_deleted = cursor.rowcount
                logger.info(f"Deleted {embeddings_deleted} embeddings for document {document_id}")
            except Exception as vec_error:
                logger.error(f"Error deleting embeddings: {str(vec_error)}")

            # Delete query metrics references
            # Reason: Clean up orphaned document references in analytics
            metrics_updated = 0
            try:
                cursor.execute(
                    """
                    UPDATE kb_query_metrics
                    SET document_ids = array_remove(document_ids, %s)
                    WHERE %s = ANY(document_ids)
                    """,
                    (document_id, document_id)
                )
                metrics_updated = cursor.rowcount
                if metrics_updated > 0:
                    logger.info(f"Updated {metrics_updated} query metrics for document {document_id}")
            except Exception as metric_error:
                logger.error(f"Error updating query metrics: {str(metric_error)}")

            # Delete from kb_documents
            cursor.execute(
                "DELETE FROM kb_documents WHERE document_id = %s",
                (document_id,)
            )

            conn.commit()
            cursor.close()

            return DocumentResponse(
                success=True,
                message="Document and associated vectors deleted successfully"
            )

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error deleting document: {str(e)}")
            return DocumentResponse(
                success=False,
                message=f"Failed to delete document: {str(e)}"
            )
        finally:
            if conn:
                self.return_connection(conn)

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

    async def delete_collection(
        self,
        company_name: str,
        delete_query_metrics: bool = False
    ) -> Dict[str, Any]:
        """
        Delete an entire collection with all documents and embeddings.

        Args:
            company_name: Company identifier
            delete_query_metrics: Whether to delete associated query metrics (default: False)

        Returns:
            Dictionary with deletion statistics
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            collection_name = self._get_collection_name(company_name)

            # Count documents before deletion
            cursor.execute(
                "SELECT COUNT(*) as count FROM kb_documents WHERE company_name = %s",
                (company_name,)
            )
            docs_count = cursor.fetchone()['count']

            # Count embeddings before deletion
            cursor.execute(
                """
                SELECT COUNT(*) as count FROM langchain_pg_embedding e
                JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                WHERE c.name = %s
                """,
                (collection_name,)
            )
            embeddings_count = cursor.fetchone()['count']

            # Count query metrics
            cursor.execute(
                "SELECT COUNT(*) as count FROM kb_query_metrics WHERE company_name = %s",
                (company_name,)
            )
            metrics_count = cursor.fetchone()['count']

            # Delete embeddings from langchain_pg_embedding
            # Reason: Clean up all vector embeddings for this collection
            cursor.execute(
                """
                DELETE FROM langchain_pg_embedding
                WHERE collection_id IN (
                    SELECT uuid FROM langchain_pg_collection WHERE name = %s
                )
                """,
                (collection_name,)
            )
            embeddings_deleted = cursor.rowcount
            logger.info(f"Deleted {embeddings_deleted} embeddings from collection {collection_name}")

            # Delete from kb_documents (versions cascade automatically)
            cursor.execute(
                "DELETE FROM kb_documents WHERE company_name = %s",
                (company_name,)
            )
            docs_deleted = cursor.rowcount
            logger.info(f"Deleted {docs_deleted} documents for company {company_name}")

            # Optionally delete query metrics
            metrics_deleted = 0
            if delete_query_metrics:
                cursor.execute(
                    "DELETE FROM kb_query_metrics WHERE company_name = %s",
                    (company_name,)
                )
                metrics_deleted = cursor.rowcount
                logger.info(f"Deleted {metrics_deleted} query metrics for company {company_name}")
            else:
                # Clean up document_ids references in metrics
                cursor.execute(
                    """
                    UPDATE kb_query_metrics
                    SET document_ids = ARRAY[]::text[]
                    WHERE company_name = %s AND array_length(document_ids, 1) > 0
                    """,
                    (company_name,)
                )
                metrics_updated = cursor.rowcount
                logger.info(f"Cleaned {metrics_updated} query metrics references for company {company_name}")

            # Delete LangChain collection entry
            cursor.execute(
                "DELETE FROM langchain_pg_collection WHERE name = %s",
                (collection_name,)
            )
            collection_deleted = cursor.rowcount

            conn.commit()
            cursor.close()

            return {
                "success": True,
                "company_name": company_name,
                "collection_name": collection_name,
                "documents_deleted": docs_deleted,
                "embeddings_deleted": embeddings_deleted,
                "query_metrics_deleted": metrics_deleted if delete_query_metrics else 0,
                "query_metrics_cleaned": metrics_updated if not delete_query_metrics else 0,
                "collection_entry_deleted": collection_deleted > 0,
                "summary": {
                    "documents_before": docs_count,
                    "embeddings_before": embeddings_count,
                    "query_metrics_before": metrics_count
                }
            }

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error deleting collection: {str(e)}")
            return {
                "success": False,
                "company_name": company_name,
                "error": str(e)
            }
        finally:
            if conn:
                self.return_connection(conn)


# Global service instance
pg_document_service = PostgreSQLDocumentService()
