"""
Knowledge Base models for RAG document management.
Supports document metadata, versioning, and analytics tracking.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4
from pydantic import BaseModel, Field
from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
    ARCHIVED = "archived"


class DocumentSource(str, Enum):
    """Document source type."""
    FILE_UPLOAD = "file_upload"
    MANUAL_ENTRY = "manual_entry"
    API_IMPORT = "api_import"
    URL_SCRAPE = "url_scrape"
    INTEGRATION_SYNC = "integration_sync"
    MIGRATION = "migration"


class DocumentVersion(BaseModel):
    """Document version model for tracking changes."""

    version_id: str = Field(default_factory=lambda: str(uuid4()), description="Version ID")
    version_number: int = Field(..., description="Sequential version number")
    content: str = Field(..., description="Document content at this version")
    title: str = Field(..., description="Document title at this version")
    category: str = Field(..., description="Category at this version")
    tags: List[str] = Field(default_factory=list, description="Tags at this version")

    # Change tracking
    changed_by: Optional[str] = Field(default=None, description="User who made the change")
    change_reason: Optional[str] = Field(default=None, description="Reason for change")
    changes_summary: Optional[str] = Field(default=None, description="Summary of changes")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Version creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "version_id": "v-123e4567-e89b-12d3-a456-426614174000",
                "version_number": 2,
                "content": "Updated product documentation...",
                "title": "Product Guide v2",
                "category": "documentation",
                "tags": ["product", "guide", "v2"],
                "changed_by": "user@example.com",
                "change_reason": "Updated for new features",
                "created_at": "2025-10-14T10:30:00"
            }
        }


class DocumentMetadata(BaseModel):
    """Extended metadata for knowledge base documents."""

    # File information
    filename: Optional[str] = Field(default=None, description="Original filename")
    file_size: Optional[int] = Field(default=None, description="File size in bytes")
    file_type: Optional[str] = Field(default=None, description="MIME type")

    # Content statistics
    word_count: int = Field(default=0, description="Word count")
    character_count: int = Field(default=0, description="Character count")
    chunk_count: int = Field(default=0, description="Number of chunks created")

    # Processing information
    embedding_model: Optional[str] = Field(default=None, description="Embedding model used")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time in milliseconds")
    index_size_bytes: Optional[int] = Field(default=None, description="Index size in bytes")

    # Usage statistics
    query_count: int = Field(default=0, description="Number of times queried")
    reference_count: int = Field(default=0, description="Number of times referenced in responses")
    last_queried_at: Optional[datetime] = Field(default=None, description="Last query timestamp")

    # Quality metrics
    confidence_avg: Optional[float] = Field(default=None, description="Average confidence when referenced")
    usefulness_score: Optional[float] = Field(default=None, description="Calculated usefulness score")

    # Custom fields
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata fields")

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "product_guide.pdf",
                "file_size": 1048576,
                "file_type": "application/pdf",
                "word_count": 5000,
                "character_count": 30000,
                "chunk_count": 15,
                "embedding_model": "text-embedding-3-small",
                "processing_time_ms": 2500,
                "query_count": 150,
                "reference_count": 89,
                "confidence_avg": 0.85
            }
        }


class KnowledgeDocument(BaseModel):
    """Complete knowledge base document model for MongoDB storage."""

    # Document identification
    id: str = Field(default_factory=lambda: str(uuid4()), description="Document ID")
    company_name: str = Field(..., description="Company/organization identifier")
    collection_name: str = Field(..., description="Vector store collection name")

    # Content
    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    content: str = Field(..., min_length=10, description="Document content")
    content_hash: Optional[str] = Field(default=None, description="SHA-256 hash of content")

    # Classification
    category: str = Field(default="general", description="Document category")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    source: str = Field(default="file_upload", description="Document source (flexible string)")
    source_uri: Optional[str] = Field(default=None, description="Source URI or path")

    # Status and versioning
    status: DocumentStatus = Field(default=DocumentStatus.PENDING, description="Processing status")
    current_version: int = Field(default=1, description="Current version number")
    versions: List[DocumentVersion] = Field(default_factory=list, description="Version history")

    # Metadata
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata, description="Extended metadata")

    # Vector store information
    vector_ids: List[str] = Field(default_factory=list, description="Vector store document IDs")
    embedding_dimension: int = Field(default=1536, description="Embedding vector dimension")

    # User information
    created_by: Optional[str] = Field(default=None, description="User who created document")
    updated_by: Optional[str] = Field(default=None, description="User who last updated document")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    indexed_at: Optional[datetime] = Field(default=None, description="Indexing timestamp")

    # Flags
    is_active: bool = Field(default=True, description="Whether document is active")
    is_archived: bool = Field(default=False, description="Whether document is archived")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc-123e4567-e89b-12d3-a456-426614174000",
                "company_name": "acme_corp",
                "collection_name": "helpdesk_acme_corp",
                "title": "Product Return Policy",
                "content": "Our 30-day return policy allows customers...",
                "category": "policies",
                "tags": ["returns", "refunds", "customer-service"],
                "source": "file_upload",
                "status": "indexed",
                "current_version": 1,
                "created_at": "2025-10-14T10:00:00"
            }
        }


class DocumentCreate(BaseModel):
    """Request model for creating a document."""

    company_name: str = Field(..., description="Company identifier")
    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    content: str = Field(..., min_length=10, description="Document content")
    category: str = Field(default="general", description="Document category")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    source: str = Field(default="manual_entry", description="Document source (flexible string)")
    source_uri: Optional[str] = Field(default=None, description="Source URI")
    created_by: Optional[str] = Field(default=None, description="Creator user ID")


class DocumentUpdate(BaseModel):
    """Request model for updating a document."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=500, description="Document title")
    content: Optional[str] = Field(default=None, min_length=10, description="Document content")
    category: Optional[str] = Field(default=None, description="Document category")
    tags: Optional[List[str]] = Field(default=None, description="Document tags")
    is_active: Optional[bool] = Field(default=None, description="Active status")
    is_archived: Optional[bool] = Field(default=None, description="Archived status")
    updated_by: Optional[str] = Field(default=None, description="Updater user ID")
    change_reason: Optional[str] = Field(default=None, description="Reason for update")


class DocumentFilter(BaseModel):
    """Filter model for document queries."""

    company_name: str = Field(..., description="Company identifier")
    category: Optional[str] = Field(default=None, description="Filter by category")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags (OR)")
    status: Optional[DocumentStatus] = Field(default=None, description="Filter by status")
    source: Optional[str] = Field(default=None, description="Filter by source (flexible string)")
    search_query: Optional[str] = Field(default=None, description="Search in title and content")
    is_active: Optional[bool] = Field(default=None, description="Filter by active status")
    is_archived: Optional[bool] = Field(default=None, description="Filter by archived status")
    created_after: Optional[datetime] = Field(default=None, description="Created after date")
    created_before: Optional[datetime] = Field(default=None, description="Created before date")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


class DocumentResponse(BaseModel):
    """Response model for document operations."""

    success: bool = Field(..., description="Operation success")
    document: Optional[KnowledgeDocument] = Field(default=None, description="Document data")
    message: Optional[str] = Field(default=None, description="Response message")


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""

    success: bool = Field(..., description="Operation success")
    documents: List[KnowledgeDocument] = Field(default_factory=list, description="List of documents")
    total_count: int = Field(default=0, description="Total number of documents")
    page: int = Field(default=1, description="Current page")
    page_size: int = Field(default=20, description="Items per page")
    total_pages: int = Field(default=0, description="Total number of pages")


class BulkUpdateRequest(BaseModel):
    """Request model for bulk update operations."""

    company_name: str = Field(..., description="Company identifier")
    document_ids: List[str] = Field(..., min_length=1, description="List of document IDs to update")

    # Update operations (at least one must be provided)
    add_tags: Optional[List[str]] = Field(default=None, description="Tags to add to documents")
    remove_tags: Optional[List[str]] = Field(default=None, description="Tags to remove from documents")
    replace_tags: Optional[List[str]] = Field(default=None, description="Replace all tags with these")
    set_category: Optional[str] = Field(default=None, description="Set category for all documents")
    set_status: Optional[DocumentStatus] = Field(default=None, description="Set status for all documents")
    set_archived: Optional[bool] = Field(default=None, description="Set archived status")

    # Metadata
    updated_by: Optional[str] = Field(default=None, description="User performing update")
    update_reason: Optional[str] = Field(default=None, description="Reason for bulk update")


class BulkUpdateResponse(BaseModel):
    """Response model for bulk update operations."""

    success: bool = Field(..., description="Overall operation success")
    updated_count: int = Field(default=0, description="Number of documents updated")
    failed_count: int = Field(default=0, description="Number of updates failed")
    failed_ids: List[str] = Field(default_factory=list, description="IDs that failed to update")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    operations_performed: List[str] = Field(default_factory=list, description="List of operations performed")


class BulkDeleteRequest(BaseModel):
    """Request model for bulk delete operations."""

    company_name: str = Field(..., description="Company identifier")
    document_ids: List[str] = Field(..., min_length=1, description="List of document IDs to delete")
    deleted_by: Optional[str] = Field(default=None, description="User performing deletion")


class BulkDeleteResponse(BaseModel):
    """Response model for bulk delete operations."""

    success: bool = Field(..., description="Overall operation success")
    deleted_count: int = Field(default=0, description="Number of documents deleted")
    failed_count: int = Field(default=0, description="Number of deletions failed")
    failed_ids: List[str] = Field(default_factory=list, description="IDs that failed to delete")
    errors: List[str] = Field(default_factory=list, description="Error messages")


class CollectionDeleteRequest(BaseModel):
    """Request model for collection delete operations."""

    company_name: str = Field(..., description="Company identifier")
    delete_query_metrics: bool = Field(default=False, description="Whether to delete query metrics (default: False)")
    confirmation: str = Field(..., description="Type 'DELETE' to confirm deletion")
    deleted_by: Optional[str] = Field(default=None, description="User performing deletion")


class CollectionDeleteResponse(BaseModel):
    """Response model for collection delete operations."""

    success: bool = Field(..., description="Overall operation success")
    company_name: str = Field(..., description="Company identifier")
    collection_name: str = Field(default="", description="Collection name")
    documents_deleted: int = Field(default=0, description="Number of documents deleted")
    embeddings_deleted: int = Field(default=0, description="Number of embeddings deleted")
    query_metrics_deleted: int = Field(default=0, description="Number of query metrics deleted")
    query_metrics_cleaned: int = Field(default=0, description="Number of query metrics cleaned")
    collection_entry_deleted: bool = Field(default=False, description="Whether collection entry was deleted")
    summary: Optional[Dict[str, Any]] = Field(default=None, description="Summary statistics before deletion")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class CollectionCreate(BaseModel):
    """Request model for creating a new collection."""

    company_name: str = Field(..., min_length=1, max_length=100, description="Company identifier (will be used in collection name)")
    display_name: str = Field(..., min_length=1, max_length=200, description="Human-readable display name")
    description: Optional[str] = Field(default=None, max_length=1000, description="Collection description")
    industry: Optional[str] = Field(default=None, max_length=100, description="Industry or domain")
    default_category: str = Field(default="general", description="Default document category")
    created_by: Optional[str] = Field(default=None, description="User creating the collection")


class CollectionUpdate(BaseModel):
    """Request model for updating collection metadata."""

    display_name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="Human-readable display name")
    description: Optional[str] = Field(default=None, max_length=1000, description="Collection description")
    industry: Optional[str] = Field(default=None, max_length=100, description="Industry or domain")
    default_category: Optional[str] = Field(default=None, description="Default document category")
    updated_by: Optional[str] = Field(default=None, description="User updating the collection")


class CollectionDuplicateRequest(BaseModel):
    """Request model for duplicating a collection."""

    source_company_name: str = Field(..., description="Source collection company name")
    target_company_name: str = Field(..., description="Target collection company name")
    copy_documents: bool = Field(default=True, description="Whether to copy documents")
    created_by: Optional[str] = Field(default=None, description="User performing duplication")


class CollectionInfo(BaseModel):
    """Enhanced information about a knowledge base collection."""

    collection_id: str = Field(..., description="Collection UUID")
    name: str = Field(..., description="Collection name (helpdesk_<company_name>)")
    company_name: str = Field(..., description="Company identifier")
    display_name: str = Field(..., description="Human-readable display name")
    description: Optional[str] = Field(default=None, description="Collection description")
    industry: Optional[str] = Field(default=None, description="Industry or domain")

    # Statistics
    document_count: int = Field(default=0, description="Number of documents")
    total_chunks: int = Field(default=0, description="Total vector chunks")
    total_size_bytes: int = Field(default=0, description="Total content size in bytes")

    # Timestamps
    created_at: Optional[datetime] = Field(default=None, description="Collection creation time")
    last_updated: Optional[datetime] = Field(default=None, description="Last document update")
    last_queried: Optional[datetime] = Field(default=None, description="Last query time")

    # Usage metrics
    total_queries: int = Field(default=0, description="Total queries count")
    avg_confidence: Optional[float] = Field(default=None, description="Average confidence score")

    class Config:
        json_schema_extra = {
            "example": {
                "collection_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "helpdesk_premier_health_production",
                "company_name": "premier_health_production",
                "display_name": "Premier Health Production",
                "description": "Healthcare provider database for Ghana",
                "industry": "healthcare",
                "document_count": 403,
                "total_chunks": 452,
                "total_size_bytes": 1048576,
                "created_at": "2025-10-01T00:00:00",
                "last_updated": "2025-10-15T12:30:00",
                "total_queries": 15000,
                "avg_confidence": 0.87
            }
        }


class CollectionStatsResponse(BaseModel):
    """Detailed statistics for a collection."""

    success: bool = Field(..., description="Operation success")
    collection_info: CollectionInfo = Field(..., description="Collection information")

    # Document breakdown
    documents_by_category: Dict[str, int] = Field(default_factory=dict, description="Document count by category")
    documents_by_status: Dict[str, int] = Field(default_factory=dict, description="Document count by status")
    top_tags: List[Dict[str, int]] = Field(default_factory=list, description="Most used tags with counts")

    # Performance metrics
    avg_processing_time_ms: Optional[float] = Field(default=None, description="Average query processing time")
    cache_hit_rate: Optional[float] = Field(default=None, description="Cache hit rate percentage")

    # Top documents
    most_queried_docs: List[Dict[str, Any]] = Field(default_factory=list, description="Most queried documents")
    highest_rated_docs: List[Dict[str, Any]] = Field(default_factory=list, description="Highest rated documents")


class QueryMetric(BaseModel):
    """Model for tracking RAG query metrics."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Metric ID")
    company_name: str = Field(..., description="Company identifier")

    # Query information
    query: str = Field(..., description="User query")
    response: str = Field(..., description="Generated response")

    # Performance metrics
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence score")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")

    # Source information
    sources_used: List[str] = Field(default_factory=list, description="Documents referenced")
    num_sources: int = Field(default=0, description="Number of sources used")

    # Escalation tracking
    requires_escalation: bool = Field(default=False, description="Whether escalation needed")
    escalation_reason: Optional[str] = Field(default=None, description="Reason for escalation")

    # Context
    query_category: Optional[str] = Field(default=None, description="Query category")
    user_id: Optional[str] = Field(default=None, description="User who made query")
    session_id: Optional[str] = Field(default=None, description="Session identifier")

    # Feedback
    user_rating: Optional[int] = Field(default=None, ge=1, le=5, description="User rating 1-5")
    user_feedback: Optional[str] = Field(default=None, description="User feedback text")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Query timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "qm-123e4567-e89b-12d3-a456-426614174000",
                "company_name": "acme_corp",
                "query": "What is your return policy?",
                "response": "Our 30-day return policy allows...",
                "confidence_score": 0.92,
                "processing_time_ms": 850,
                "sources_used": ["Product Return Policy", "Customer Service Guide"],
                "num_sources": 2,
                "requires_escalation": False,
                "created_at": "2025-10-14T10:30:00"
            }
        }
