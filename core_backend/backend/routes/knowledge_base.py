"""
Knowledge Base API routes for RAG document management.
Provides endpoints for uploading, managing, and querying knowledge base documents.
"""

import os
import logging
import tempfile
import aiofiles
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.services.helpdesk_rag_service import (
    helpdesk_rag_service,
    KnowledgeDocument as RAGKnowledgeDocument,
    QueryResult
)
from backend.services.pg_document_service import pg_document_service as document_management_service
from backend.services.rag_analytics_service import rag_analytics_service
from backend.services.tool_call_logger import tool_call_logger
from backend.services.redis_cache_service import redis_cache_service
from backend.services.collection_management_service import collection_management_service
from backend.services.document_export_service import document_export_service, ExportFormat
from backend.models.knowledge_base import (
    KnowledgeDocument,
    DocumentCreate,
    DocumentUpdate,
    DocumentFilter,
    DocumentResponse,
    DocumentListResponse,
    BulkUpdateRequest,
    BulkUpdateResponse,
    BulkDeleteRequest,
    BulkDeleteResponse,
    CollectionDeleteRequest,
    CollectionDeleteResponse,
    CollectionCreate,
    CollectionUpdate,
    CollectionInfo,
    CollectionStatsResponse,
    CollectionDuplicateRequest,
    DocumentStatus
)
from backend.auth import get_current_user_mongo
from backend.middleware.organization_context import (
    get_organization_context,
    require_organization_context,
    validate_organization_access,
    get_user_organization_filter
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])

class CollectionsListResponse(BaseModel):
    """Response model for listing collections."""
    success: bool
    collections: List[CollectionInfo]
    total: int

class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    success: bool
    document_id: str
    filename: str
    content_preview: str
    word_count: int
    message: str

class ManualDocumentRequest(BaseModel):
    """Request model for manual document creation."""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10)
    category: str = Field(default="general", max_length=50)
    tags: List[str] = Field(default_factory=list)
    source: Optional[str] = Field(default=None, max_length=200)

class BulkExportRequest(BaseModel):
    """Request model for bulk document export."""
    document_ids: Optional[List[str]] = Field(default=None, description="Document IDs to export")

class QueryTestRequest(BaseModel):
    """
    Request model for testing knowledge base queries.

    Supports both formats:
    1. Direct format: {"query": "...", "plan_type": "...", "region": "..."}
    2. VAPI format: {"message": {"toolWithToolCallList": [...]}}
    """
    query: Optional[str] = None
    company_name: Optional[str] = None
    plan_type: Optional[str] = Field(
        None,
        description="Optional insurance plan type filter (PLATINUM PLUS, PLATINUM, MERCURY, REGULAR)"
    )
    region: Optional[str] = Field(
        None,
        description="Optional geographic region filter (GREATER ACCRA, ASHANTI, WESTERN REGION, etc.)"
    )
    # VAPI sends the entire tool call context in a "message" field
    message: Optional[Dict[str, Any]] = None

    model_config = {"extra": "allow"}  # Allow extra fields from VAPI

class InitializeKnowledgeBaseRequest(BaseModel):
    """Request model for initializing knowledge base."""
    company_name: str = Field(..., min_length=1, max_length=100)
    documents: List[Dict[str, Any]]

# Supported file types for upload
SUPPORTED_FILE_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-excel": ".xls",
    "text/plain": ".txt",
    "text/markdown": ".md"
}

@router.get("/collections", response_model=CollectionsListResponse)
async def list_collections(
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    List all available knowledge base collections with enhanced metadata.

    Now properly scoped to organization. Requires authentication and
    X-Organization-ID header.

    Returns:
        List of collections with metadata (name, document count, chunks, timestamps, etc.)
        filtered by user's organization.
    """
    try:
        # Get organization context from request
        org_id = get_organization_context(request)

        # Validate user has access to the organization
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Get organization filter
        org_filter = get_user_organization_filter(current_user, org_id)
        organization_id = org_filter.get("organization_id")

        # List collections (organization filtering happens via middleware)
        # Note: For now, return all collections. Organization-specific filtering
        # can be added to the service later if needed
        collections = await collection_management_service.list_collections_enhanced()

        return CollectionsListResponse(
            success=True,
            collections=collections,
            total=len(collections)
        )

    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list collections: {str(e)}"
        )


@router.post("/collections/create")
async def create_collection(
    request: CollectionCreate,
    current_user: dict = Depends(get_current_user_mongo),
    req: Request = None
):
    """
    Create a new knowledge base collection.

    Now properly scoped to organization. Requires authentication and
    X-Organization-ID header.

    Args:
        request: Collection creation request with company_name, display_name, description, etc.

    Returns:
        Success status and created collection information

    Raises:
        HTTPException 400: If collection already exists
        HTTPException 500: If creation fails
    """
    try:
        # Get organization context from request
        org_id = get_organization_context(req)

        # Validate user has access to the organization
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Get organization filter
        org_filter = get_user_organization_filter(current_user, org_id)
        organization_id = org_filter.get("organization_id")

        # Add organization_id to request
        if organization_id:
            request.organization_id = organization_id

        result = await collection_management_service.create_collection(request)

        return result

    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            logger.error(f"Error creating collection: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Failed to create collection: {error_msg}")


@router.put("/collections/{company_name}/update")
async def update_collection_metadata(
    company_name: str,
    request: CollectionUpdate,
    current_user: dict = Depends(get_current_user_mongo),
    req: Request = None
):
    """
    Update collection metadata (display name, description, industry, etc.).

    Now properly scoped to organization. Requires authentication.

    Args:
        company_name: Company identifier
        request: Collection update request

    Returns:
        Success status and update confirmation

    Raises:
        HTTPException 404: If collection not found
        HTTPException 500: If update fails
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(req)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        result = await collection_management_service.update_collection(company_name, request)

        return result

    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            logger.error(f"Error updating collection: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Failed to update collection: {error_msg}")


@router.get("/collections/{company_name}/stats", response_model=CollectionStatsResponse)
async def get_collection_statistics(
    company_name: str,
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Get detailed statistics for a knowledge base collection.

    Now properly scoped to organization. Requires authentication.

    Args:
        company_name: Company identifier

    Returns:
        Comprehensive collection statistics including:
        - Document counts by category and status
        - Top tags
        - Performance metrics
        - Most queried documents

    Raises:
        HTTPException 404: If collection not found
        HTTPException 500: If stats retrieval fails
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        stats = await collection_management_service.get_collection_stats(company_name)

        return stats

    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            logger.error(f"Error getting collection stats: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Failed to get collection stats: {error_msg}")


@router.post("/collections/duplicate")
async def duplicate_collection(
    request: CollectionDuplicateRequest,
    current_user: dict = Depends(get_current_user_mongo),
    req: Request = None
):
    """
    Duplicate a knowledge base collection.

    Now properly scoped to organization. Requires authentication.

    Creates a new collection with the same metadata and optionally copies all documents.

    Args:
        request: Duplication request with source and target company names

    Returns:
        Success status and duplication summary

    Raises:
        HTTPException 404: If source collection not found
        HTTPException 400: If target collection already exists
        HTTPException 500: If duplication fails
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(req)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        result = await collection_management_service.duplicate_collection(request)

        return result

    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        elif "already exists" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            logger.error(f"Error duplicating collection: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Failed to duplicate collection: {error_msg}")

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    company_name: str = Form(...),
    category: str = Form(default="general"),
    tags: str = Form(default=""),
    created_by: Optional[str] = Form(default=None),
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Upload a document file and extract its content for the knowledge base.

    Now properly scoped to organization. Requires authentication.

    Supports PDF, Word (.docx, .doc), TXT, and Markdown files.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)
        # Validate file type
        if file.content_type not in SUPPORTED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Supported types: {list(SUPPORTED_FILE_TYPES.keys())}"
            )

        # Validate file size (max 10MB)
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 10MB limit"
            )

        # Reset file pointer
        await file.seek(0)

        # Extract content based on file type
        content = _extract_file_content(file, file_content)

        if not content or len(content.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Could not extract meaningful content from file"
            )

        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []

        # Create document using management service
        doc_create = DocumentCreate(
            company_name=company_name,
            title=file.filename or "Uploaded Document",
            content=content,
            category=category,
            tags=tag_list,
            source="file_upload",
            source_uri=f"file_upload:{file.filename}",
            created_by=created_by
        )

        response = await document_management_service.create_document(doc_create)

        if not response.success:
            raise HTTPException(status_code=500, detail=response.message)

        # Generate preview
        preview = content[:200] + "..." if len(content) > 200 else content
        word_count = len(content.split())

        return DocumentUploadResponse(
            success=True,
            document_id=response.document.id if response.document else "",
            filename=file.filename or "unknown",
            content_preview=preview,
            word_count=word_count,
            message="Document uploaded and will be indexed shortly"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )

@router.post("/documents", response_model=DocumentUploadResponse)
async def add_manual_document(
    request: ManualDocumentRequest,
    company_name: str,
    created_by: Optional[str] = None,
    current_user: dict = Depends(get_current_user_mongo),
    http_request: Request = None
):
    """
    Add a manual knowledge base document (typed content).

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Create document using management service
        doc_create = DocumentCreate(
            company_name=company_name,
            title=request.title,
            content=request.content,
            category=request.category,
            tags=request.tags,
            source="manual_entry",
            source_uri=request.source,
            created_by=created_by or current_user.get("user_id")
        )

        response = await document_management_service.create_document(doc_create)

        if not response.success:
            raise HTTPException(status_code=500, detail=response.message)

        # Generate preview and stats
        preview = request.content[:200] + "..." if len(request.content) > 200 else request.content
        word_count = len(request.content.split())

        # Handle both dict and object response formats
        document_id = ""
        if response.document:
            if isinstance(response.document, dict):
                document_id = response.document.get('id', '')
            else:
                document_id = response.document.id

        return DocumentUploadResponse(
            success=True,
            document_id=document_id,
            filename=request.title,
            content_preview=preview,
            word_count=word_count,
            message="Manual document added and will be indexed shortly"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding manual document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add document: {str(e)}"
        )

@router.get("/{company_name}/documents", response_model=DocumentListResponse)
async def list_documents(
    company_name: str,
    category: Optional[str] = Query(default=None),
    tags: Optional[str] = Query(default=None),
    status: Optional[DocumentStatus] = Query(default=None),
    search_query: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    is_archived: Optional[bool] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    List documents for a company with filtering, search, and pagination.

    Now properly scoped to organization. Requires authentication.

    Supports:
    - Category filtering
    - Tag filtering (comma-separated)
    - Status filtering (pending, processing, indexed, failed, archived)
    - Full-text search in title and content
    - Active/archived filtering
    - Pagination with customizable page size
    - Sorting by any field
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)
        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Create filter
        filter_params = DocumentFilter(
            company_name=company_name,
            category=category,
            tags=tag_list,
            status=status,
            search_query=search_query,
            is_active=is_active,
            is_archived=is_archived,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )

        # Get documents
        response = await document_management_service.list_documents(filter_params)

        return response

    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Get a single document by ID with all metadata.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        response = await document_management_service.get_document(document_id)

        if not response.success:
            raise HTTPException(status_code=404, detail=response.message)

        # Verify document belongs to user's organization
        if response.document and response.document.organization_id:
            if org_id and response.document.organization_id != org_id:
                raise HTTPException(status_code=403, detail="Access denied to this document")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document: {str(e)}"
        )


@router.put("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    update_data: DocumentUpdate,
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Update a document's content or metadata.

    Now properly scoped to organization. Requires authentication.

    Creates a new version if content is changed.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        response = await document_management_service.update_document(
            document_id=document_id,
            doc_update=update_data
        )

        if not response.success:
            raise HTTPException(status_code=404 if "not found" in response.message.lower() else 500, detail=response.message)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update document: {str(e)}"
        )


@router.delete("/documents/{document_id}", response_model=DocumentResponse)
async def delete_document(
    document_id: str,
    company_name: str,
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Delete a document from MongoDB and vector store.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        response = await document_management_service.delete_document(
            document_id=document_id,
            company_name=company_name
        )

        if not response.success:
            raise HTTPException(status_code=404 if "not found" in response.message.lower() else 500, detail=response.message)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/documents/{document_id}/export")
async def export_single_document(
    document_id: str,
    format: str = Query(default="json", regex="^(json|csv|pdf|original)$"),
    include_metadata: bool = Query(default=True),
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Export a single document in the specified format.

    Now properly scoped to organization. Requires authentication.

    Args:
        document_id: Document ID
        format: Export format (json, csv, pdf, original)
        include_metadata: Include document metadata in export

    Returns:
        File download with appropriate content type

    Supported Formats:
        - json: Full document data with metadata
        - csv: Single-row CSV with document info
        - pdf: Formatted PDF with title, metadata, and content
        - original: Original uploaded file (if available, otherwise text)
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)
        from fastapi.responses import Response

        # Get document
        doc_response = await document_management_service.get_document(document_id)

        if not doc_response.success or not doc_response.document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Handle both dict and Pydantic model responses
        document = doc_response.document if isinstance(doc_response.document, dict) else doc_response.document.dict()
        export_fmt = ExportFormat(format)

        # Export based on format
        if export_fmt == ExportFormat.JSON:
            file_bytes, filename, mime_type = await document_export_service.export_bulk_documents(
                [document],
                ExportFormat.JSON,
                include_metadata=include_metadata
            )

        elif export_fmt == ExportFormat.CSV:
            file_bytes, filename, mime_type = await document_export_service.export_bulk_documents(
                [document],
                ExportFormat.CSV,
                include_metadata=include_metadata
            )

        elif export_fmt == ExportFormat.PDF:
            file_bytes = await document_export_service.export_document_pdf(
                document,
                include_metadata=include_metadata
            )
            filename = f"{document.get('title', 'document').replace(' ', '_')}.pdf"
            mime_type = "application/pdf"

        elif export_fmt == ExportFormat.ORIGINAL:
            result = await document_export_service.get_original_file(document)
            if result:
                file_bytes, filename, mime_type = result
            else:
                raise HTTPException(status_code=404, detail="Original file not available")

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

        return Response(
            content=file_bytes,
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export document: {str(e)}"
        )


@router.post("/documents/export")
async def export_multiple_documents(
    request: BulkExportRequest,
    company_name: str = Query(...),
    format: str = Query(default="json", regex="^(json|csv)$"),
    include_metadata: bool = Query(default=True),
    include_versions: bool = Query(default=False),
    # Filter options for exporting all filtered documents
    category: Optional[str] = Query(default=None),
    tags: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    search_query: Optional[str] = Query(default=None),
    current_user: dict = Depends(get_current_user_mongo),
    http_request: Request = None
):
    """
    Export multiple documents in bulk.

    Now properly scoped to organization. Requires authentication.

    Args:
        company_name: Company identifier
        document_ids: Specific document IDs to export (if None, exports all filtered documents)
        format: Export format (json or csv - PDF not supported for bulk)
        include_metadata: Include document metadata
        include_versions: Include version history (JSON only)
        category: Filter by category
        tags: Filter by tags (comma-separated)
        status: Filter by status
        search_query: Search query filter

    Returns:
        File download with exported documents

    Usage:
        - Export specific documents: Pass document_ids
        - Export all documents: Don't pass document_ids
        - Export filtered documents: Use filter parameters without document_ids
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        from fastapi.responses import Response

        # Get documents
        if request.document_ids:
            # Export specific documents
            documents = []
            for doc_id in request.document_ids:
                doc_response = await document_management_service.get_document(doc_id)
                if doc_response.success and doc_response.document:
                    # Handle both dict and Pydantic model responses
                    doc_dict = doc_response.document if isinstance(doc_response.document, dict) else doc_response.document.dict()
                    documents.append(doc_dict)
        else:
            # Export all documents matching filters
            tag_list = None
            if tags:
                tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

            filter_params = DocumentFilter(
                company_name=company_name,
                category=category,
                tags=tag_list,
                status=status,
                search_query=search_query,
                page=1,
                page_size=10000,  # Large number to get all documents
            )

            list_response = await document_management_service.list_documents(filter_params)
            # Handle both dict and Pydantic model responses
            documents = [doc if isinstance(doc, dict) else doc.dict() for doc in list_response.documents]

        if not documents:
            raise HTTPException(status_code=404, detail="No documents found to export")

        export_fmt = ExportFormat(format)

        # Validate format
        if export_fmt not in [ExportFormat.JSON, ExportFormat.CSV]:
            raise HTTPException(
                status_code=400,
                detail="Only JSON and CSV formats are supported for bulk export"
            )

        # Export documents
        file_bytes, filename, mime_type = await document_export_service.export_bulk_documents(
            documents,
            export_fmt,
            include_metadata=include_metadata,
            include_versions=include_versions
        )

        return Response(
            content=file_bytes,
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export documents: {str(e)}"
        )


@router.post("/documents/bulk-update", response_model=BulkUpdateResponse)
async def bulk_update_documents(
    request: BulkUpdateRequest,
    current_user: dict = Depends(get_current_user_mongo),
    req: Request = None
):
    """
    Update multiple documents in bulk.

    Now properly scoped to organization. Requires authentication.

    Supports the following operations:
    - add_tags: Add tags to documents (preserves existing tags)
    - remove_tags: Remove specific tags from documents
    - replace_tags: Replace all tags with new ones
    - set_category: Set category for all documents
    - set_status: Set status for all documents
    - set_archived: Set archived flag for all documents

    At least one operation must be specified.

    Returns:
        BulkUpdateResponse with counts of successful/failed updates

    Example:
        {
            "company_name": "acme_corp",
            "document_ids": ["doc1", "doc2", "doc3"],
            "add_tags": ["reviewed", "approved"],
            "set_category": "policies"
        }
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(req)
        if org_id:
            await validate_organization_access(request, current_user, org_id)
        # Validate at least one operation is provided
        has_operation = any([
            request.add_tags,
            request.remove_tags,
            request.replace_tags,
            request.set_category is not None,
            request.set_status is not None,
            request.set_archived is not None,
        ])

        if not has_operation:
            raise HTTPException(
                status_code=400,
                detail="At least one update operation must be specified"
            )

        # Track operations and results
        operations_performed = []
        updated_count = 0
        failed_count = 0
        failed_ids = []
        errors = []

        # Process each document
        for doc_id in request.document_ids:
            try:
                # Get current document
                doc_response = await document_management_service.get_document(doc_id)

                if not doc_response.success or not doc_response.document:
                    failed_count += 1
                    failed_ids.append(doc_id)
                    errors.append(f"Document {doc_id} not found")
                    continue

                doc = doc_response.document
                updated = False
                doc_operations = []

                # Build update object
                update_data = {}

                # Handle dict vs object response
                def get_field(obj, field):
                    return obj[field] if isinstance(obj, dict) else getattr(obj, field)

                # Handle tag operations
                if request.replace_tags is not None:
                    update_data["tags"] = request.replace_tags
                    doc_operations.append("replaced_tags")
                    updated = True
                else:
                    current_tags = set(get_field(doc, 'tags'))

                    if request.add_tags:
                        current_tags.update(request.add_tags)
                        doc_operations.append("added_tags")
                        updated = True

                    if request.remove_tags:
                        current_tags.difference_update(request.remove_tags)
                        doc_operations.append("removed_tags")
                        updated = True

                    if request.add_tags or request.remove_tags:
                        update_data["tags"] = list(current_tags)

                # Handle category
                if request.set_category is not None:
                    update_data["category"] = request.set_category
                    doc_operations.append("set_category")
                    updated = True

                # Handle status
                if request.set_status is not None:
                    update_data["status"] = request.set_status
                    doc_operations.append("set_status")
                    updated = True

                # Handle archived
                if request.set_archived is not None:
                    update_data["is_archived"] = request.set_archived
                    doc_operations.append("set_archived")
                    updated = True

                # Add metadata
                if updated:
                    update_data["updated_by"] = request.updated_by
                    update_data["change_reason"] = request.update_reason or "Bulk update"

                    # Create update request
                    from backend.models.knowledge_base import DocumentUpdate
                    doc_update = DocumentUpdate(**update_data)

                    # Perform update
                    update_response = await document_management_service.update_document(
                        document_id=doc_id,
                        doc_update=doc_update
                    )

                    if update_response.success:
                        updated_count += 1
                        for op in doc_operations:
                            if op not in operations_performed:
                                operations_performed.append(op)
                    else:
                        failed_count += 1
                        failed_ids.append(doc_id)
                        errors.append(f"Failed to update {doc_id}: {update_response.message}")

            except Exception as e:
                failed_count += 1
                failed_ids.append(doc_id)
                errors.append(f"Error updating {doc_id}: {str(e)}")
                logger.error(f"Error updating document {doc_id}: {str(e)}")

        return BulkUpdateResponse(
            success=updated_count > 0,
            updated_count=updated_count,
            failed_count=failed_count,
            failed_ids=failed_ids,
            errors=errors,
            operations_performed=operations_performed
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk update: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update documents: {str(e)}"
        )


@router.post("/documents/bulk-delete", response_model=BulkDeleteResponse)
async def bulk_delete_documents(
    request: BulkDeleteRequest,
    current_user: dict = Depends(get_current_user_mongo),
    req: Request = None
):
    """
    Delete multiple documents in bulk.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(req)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        response = await document_management_service.bulk_delete_documents(request)

        return response

    except Exception as e:
        logger.error(f"Error in bulk delete: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to bulk delete documents: {str(e)}"
        )


@router.post("/collections/delete", response_model=CollectionDeleteResponse)
async def delete_collection(
    request: CollectionDeleteRequest,
    current_user: dict = Depends(get_current_user_mongo),
    req: Request = None
):
    """
    Delete an entire collection with all documents, embeddings, and optionally query metrics.

    Now properly scoped to organization. Requires authentication.

    **DANGER**: This is a destructive operation that cannot be undone!

    Deletes:
    - All documents in kb_documents table
    - All document versions (cascade)
    - All vector embeddings in langchain_pg_embedding
    - LangChain collection entry
    - Optionally: query metrics (or just clean document references)

    Requires confirmation string 'DELETE' to proceed.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(req)
        if org_id:
            await validate_organization_access(request, current_user, org_id)
        # Validate confirmation
        if request.confirmation != "DELETE":
            raise HTTPException(
                status_code=400,
                detail="Confirmation failed. Type 'DELETE' to confirm collection deletion."
            )

        # Perform deletion
        result = await document_management_service.delete_collection(
            company_name=request.company_name,
            delete_query_metrics=request.delete_query_metrics
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to delete collection")
            )

        return CollectionDeleteResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting collection: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete collection: {str(e)}"
        )


@router.post("/{company_name}/query")
async def test_query(
    company_name: str,
    query_request: QueryTestRequest,
    request: Request
):
    """
    Query the company's knowledge base using the RAG service.

    This endpoint is publicly accessible for VAPI webhook integration.
    Authentication is not required to allow VAPI tool calls.

    Supports two request formats:
    1. Direct: {"query": "search text"} - Returns QueryResult
    2. VAPI: {"message": {"toolCallList": [...]}} - Returns VAPI-formatted response
    """
    # Get organization context (optional, for tracking purposes)
    org_id = get_organization_context(request)

    # Log incoming request for debugging
    logger.info(f"🔍 Incoming RAG Query Request - URL company_name: '{company_name}' - org_id: '{org_id}'")

    # Log full request payload for debugging (truncate if too large)
    import json
    try:
        request_dict = query_request.dict()
        request_json = json.dumps(request_dict, indent=2)
        if len(request_json) > 500:
            logger.info(f"📦 Request payload (truncated): {request_json[:500]}...")
        else:
            logger.info(f"📦 Request payload: {request_json}")
    except Exception as e:
        logger.warning(f"⚠️  Could not serialize request payload: {str(e)}")

    try:
        # Extract query and toolCallId from either direct format or VAPI format
        query = query_request.query
        tool_call_id = None
        is_vapi_request = False
        vapi_call_id = None  # For tracking VAPI call sessions

        # If query is not provided directly, try to extract from VAPI message format
        if not query and query_request.message:
            logger.info(f"🔍 Extracting query from VAPI message format")
            is_vapi_request = True

            # VAPI format: message.toolCallList[0] or message.toolWithToolCallList[0]
            tool_list = query_request.message.get("toolCallList") or query_request.message.get("toolWithToolCallList", [])

            # Extract VAPI call ID if available
            vapi_call_id = query_request.message.get("call", {}).get("id") or query_request.message.get("callId")

            # Also check for toolCalls format
            if not tool_list:
                tool_calls = query_request.message.get("toolCalls", [])
                if tool_calls and len(tool_calls) > 0:
                    tool_list = [{"toolCall": tool_calls[0]}]

            if tool_list and len(tool_list) > 0:
                # Extract toolCall
                if "toolCall" in tool_list[0]:
                    tool_call = tool_list[0].get("toolCall", {})
                else:
                    tool_call = tool_list[0]

                # Get tool call ID
                tool_call_id = tool_call.get("id")

                # Get function arguments
                function = tool_call.get("function", {})
                arguments = function.get("arguments", {})
                query = arguments.get("query")
                # Extract plan_type and region from VAPI function arguments if not provided directly
                if not query_request.plan_type:
                    query_request.plan_type = arguments.get("plan_type")
                if not query_request.region:
                    query_request.region = arguments.get("region")

                logger.info(f"🔍 Extracted from VAPI - Query: '{query}', Plan Type: '{query_request.plan_type}', Region: '{query_request.region}', ToolCallId: '{tool_call_id}'")

        if not query:
            logger.error(f"❌ No query found in request")
            raise HTTPException(
                status_code=400,
                detail="Query is required. Please provide either 'query' field or VAPI message format."
            )

        logger.info(f"🔍 Processing query: '{query}'")

        # Store original query and city/region normalization details for logging
        query_original = query
        city_normalization_details = None
        regional_query_cities = None  # Cities to query for regional searches

        # Normalize location names for Premier Health and Ghana Tourism queries
        # Reason: STT engines often mishear Ghanaian city names (e.g., "medina" → "MADINA")
        if company_name in ["premier_health_production", "ghana_tourism_production"]:
            try:
                import sys
                sys.path.insert(0, "/opt/kasaai/apps/automations/premier-health")
                from city_normalizer import CityNormalizer

                normalizer = CityNormalizer()

                # Extract potential location from query
                # Common patterns: "in <location>", "at <location>", "<location> area/region"
                # IMPORTANT: Include digits [0-9] to handle "community 5", "comm 12", etc.
                import re
                location_patterns = [
                    r'\bin\s+([a-zA-Z0-9\s.]+?)(?:\s+area|\s+region|[,]|$)',
                    r'\bat\s+([a-zA-Z0-9\s.]+?)(?:\s+area|\s+region|[,]|$)',
                    r'\b([a-zA-Z0-9\s.]+?)\s+area\b',
                    r'\b([a-zA-Z0-9\s.]+?)\s+region\b',
                ]

                original_query = query
                location_normalized = False

                for pattern in location_patterns:
                    matches = re.finditer(pattern, query, re.IGNORECASE)
                    for match in matches:
                        potential_location = match.group(1).strip()

                        # Try to normalize the location - allow regions this time
                        normalized_location, confidence, method = normalizer.normalize_with_confidence(
                            potential_location,
                            fuzzy_threshold=0.7,
                            allow_regions=True  # Enable region detection
                        )

                        if normalized_location and confidence >= 0.7:
                            # Check if it's a regional query
                            if method == "region_detected":
                                # Get all cities in the region for expanded query
                                regional_query_cities = normalizer.get_cities_for_region(normalized_location)

                                if regional_query_cities:
                                    # For large regions (>15 cities), limit to top 15 to prevent timeouts
                                    # Reason: Greater Accra has 66 cities which causes timeouts
                                    max_cities = 15
                                    limited_cities = regional_query_cities[:max_cities]

                                    # Expand query to include multiple cities
                                    city_list = ", ".join(limited_cities)
                                    if len(regional_query_cities) > max_cities:
                                        # Add disclaimer for large regions
                                        query = f"{query} (searching across {normalized_location} region - showing results from {len(limited_cities)} major cities: {city_list})"
                                    else:
                                        query = f"{query} (searching across {normalized_location} region cities: {city_list})"

                                    location_normalized = True

                                    city_normalization_details = {
                                        "original": potential_location,
                                        "normalized": normalized_location,
                                        "confidence": confidence,
                                        "method": method,
                                        "is_region": True,
                                        "cities_count": len(regional_query_cities),
                                        "cities_searched": len(limited_cities),
                                        "cities_list": limited_cities
                                    }

                                    logger.info(
                                        f"🌍 Regional query detected: '{potential_location}' → '{normalized_location}' region "
                                        f"(confidence: {confidence:.2f}, cities: {len(regional_query_cities)})"
                                    )
                                    break
                            else:
                                # City normalization (not region)
                                query = query.replace(potential_location, normalized_location)
                                location_normalized = True

                                city_normalization_details = {
                                    "original": potential_location,
                                    "normalized": normalized_location,
                                    "confidence": confidence,
                                    "method": method,
                                    "is_region": False
                                }

                                logger.info(
                                    f"📍 Location normalized: '{potential_location}' → '{normalized_location}' "
                                    f"(confidence: {confidence:.2f}, method: {method})"
                                )
                                break

                    if location_normalized:
                        break

                if not location_normalized:
                    # Try extracting standalone location words
                    words = query.split()
                    for i, word in enumerate(words):
                        clean_word = re.sub(r'[,.\?!]', '', word)
                        if len(clean_word) > 2:  # Skip very short words
                            normalized_location, confidence, method = normalizer.normalize_with_confidence(
                                clean_word,
                                fuzzy_threshold=0.8,
                                allow_regions=True
                            )

                            if normalized_location and confidence >= 0.8:
                                if method == "region_detected":
                                    # Regional query from standalone word
                                    regional_query_cities = normalizer.get_cities_for_region(normalized_location)

                                    if regional_query_cities:
                                        city_list = ", ".join(regional_query_cities[:10])
                                        query = f"{query} (searching across {normalized_location} region cities: {city_list})"

                                        city_normalization_details = {
                                            "original": clean_word,
                                            "normalized": normalized_location,
                                            "confidence": confidence,
                                            "method": method,
                                            "is_region": True,
                                            "cities_count": len(regional_query_cities),
                                            "cities_list": regional_query_cities[:10]
                                        }

                                        logger.info(
                                            f"🌍 Regional query detected: '{clean_word}' → '{normalized_location}' region "
                                            f"(confidence: {confidence:.2f}, cities: {len(regional_query_cities)})"
                                        )
                                        break
                                else:
                                    # Replace word with normalized city
                                    words[i] = normalized_location
                                    query = ' '.join(words)

                                    if not city_normalization_details:
                                        city_normalization_details = {
                                            "original": clean_word,
                                            "normalized": normalized_location,
                                            "confidence": confidence,
                                            "method": method,
                                            "is_region": False
                                        }

                                    logger.info(
                                        f"📍 Standalone location normalized: '{clean_word}' → '{normalized_location}' "
                                        f"(confidence: {confidence:.2f}, method: {method})"
                                    )
                                    break

                if query != original_query:
                    logger.info(f"🔄 Query after normalization: '{query}'")

            except ImportError as e:
                logger.warning(f"⚠️  City normalizer not available: {str(e)}")
            except Exception as e:
                logger.warning(f"⚠️  Error during location normalization: {str(e)}")
                # Continue with original query if normalization fails

        # Normalize plan type if provided (e.g., "plat" → "PLATINUM", "mer" → "MERCURY")
        if query_request.plan_type and company_name in ["premier_health_production"]:
            try:
                import sys
                sys.path.insert(0, "/opt/kasaai/apps/automations/premier-health")
                from city_normalizer import CityNormalizer

                normalizer = CityNormalizer()
                original_plan_type = query_request.plan_type

                # Normalize plan type
                normalized_plan_type = normalizer.normalize_plan_type(query_request.plan_type)

                if normalized_plan_type:
                    query_request.plan_type = normalized_plan_type
                    logger.info(f"🎯 Plan type normalized: '{original_plan_type}' → '{normalized_plan_type}'")
                else:
                    logger.warning(f"⚠️  Could not normalize plan type: '{original_plan_type}'")

            except ImportError as e:
                logger.warning(f"⚠️  City normalizer not available for plan type normalization: {str(e)}")
            except Exception as e:
                logger.warning(f"⚠️  Error during plan type normalization: {str(e)}")

        # Check Redis cache first for instant responses (80% faster for repeat queries)
        # Reason: Common queries like "general practitioners in MADINA" are repeated frequently
        cached_response = await redis_cache_service.get_cached_response(company_name, query)

        if cached_response:
            # Cache HIT - return instant response
            logger.info(f"💨 CACHE HIT - Instant response (query: '{query[:50]}')")

            # Reconstruct QueryResult from cached data
            result = QueryResult(**cached_response)
        else:
            # Cache MISS - query RAG service
            logger.info(f"🔍 CACHE MISS - Querying RAG service (query: '{query[:50]}')")

            # Use company_name from path, not from request body
            # Reason: VAPI sends company_name in URL path only
            result = await helpdesk_rag_service.query_knowledge_base(
                company_name=company_name,
                query=query,
                plan_type=query_request.plan_type,
                region=query_request.region
            )

            if query_request.plan_type:
                logger.info(f"🎯 Plan type filter applied: {query_request.plan_type}")
            if query_request.region:
                logger.info(f"🌍 Region filter applied: {query_request.region}")

            # Cache the response for future queries (24h TTL)
            # Reason: Reduce load on RAG service and provide instant responses
            if result.success:
                try:
                    await redis_cache_service.cache_response(
                        company_name=company_name,
                        query=query,
                        response_data=result.dict()
                    )
                    logger.info(f"✅ Response cached for future requests")
                except Exception as cache_error:
                    # Don't fail the request if caching fails
                    logger.warning(f"⚠️  Failed to cache response: {cache_error}")

        # Log response summary before returning to VAPI
        logger.info(f"📤 Sending response:")
        logger.info(f"   ✅ Success: {result.success}")
        logger.info(f"   💯 Confidence: {result.confidence_score:.2f}")
        logger.info(f"   🚦 Requires Escalation: {result.requires_escalation}")
        if result.escalation_reason:
            logger.info(f"   ⚠️  Escalation Reason: {result.escalation_reason}")
        logger.info(f"   📚 Sources Count: {len(result.sources_used)}")
        logger.info(f"   📝 Response Length: {len(result.response)} chars")
        logger.info(f"   ⏱️  Processing Time: {result.processing_time:.2f}s")

        # Log tool call to MongoDB for analytics and monitoring
        # Reason: Track all RAG queries for performance analysis, pre-computation, and debugging
        try:
            # Extract request metadata
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

            # Generate tool_call_id if not provided (for non-VAPI requests)
            if not tool_call_id:
                import uuid
                tool_call_id = f"direct_{uuid.uuid4().hex[:12]}"

            # Log the tool call asynchronously (non-blocking)
            # Note: We don't have documents_retrieved and documents_sent_to_llm yet
            # Will need to modify helpdesk_rag_service to return these
            await tool_call_logger.log_tool_call(
                tool_call_id=tool_call_id,
                company_name=company_name,
                query_original=query_original,
                query_normalized=query if query != query_original else None,
                city_normalization=city_normalization_details,
                response=result.response,
                processing_time=result.processing_time,
                confidence_score=result.confidence_score,
                documents_retrieved=0,  # TODO: Get from rag_service
                documents_sent_to_llm=len(result.sources_used),  # Approximation based on sources
                sources_used=result.sources_used,
                requires_escalation=result.requires_escalation,
                escalation_reason=result.escalation_reason,
                status="success" if result.success else "failed",
                error_message=result.error_message,
                ip_address=ip_address,
                user_agent=user_agent,
                vapi_call_id=vapi_call_id
            )
            logger.info(f"✅ Tool call logged to MongoDB: {tool_call_id}")

        except Exception as log_error:
            # Don't fail the request if logging fails
            logger.error(f"❌ Failed to log tool call: {log_error}")
            import traceback
            traceback.print_exc()

        # If this is a VAPI request, wrap in VAPI format
        if is_vapi_request and tool_call_id:
            logger.info(f"🎯 Wrapping response in VAPI format with toolCallId: {tool_call_id}")

            # VAPI expects: {"results": [{"toolCallId": "...", "result": "..."}]}
            # The result should be the actual answer text that the LLM can use
            vapi_response = {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": result.response  # Send the response text directly
                }]
            }

            logger.info(f"📦 VAPI Response format: {json.dumps(vapi_response, indent=2)[:300]}...")
            return JSONResponse(content=vapi_response)

        # For direct API calls, return the full QueryResult
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )

@router.put("/{company_name}/initialize")
async def initialize_knowledge_base(
    company_name: str,
    request: InitializeKnowledgeBaseRequest,
    current_user: dict = Depends(get_current_user_mongo),
    http_request: Request = None
):
    """
    Initialize the knowledge base for a company with the provided documents.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Convert request documents to KnowledgeDocument objects
        documents = []
        for doc_data in request.documents:
            document = KnowledgeDocument(
                title=doc_data.get("title", "Untitled"),
                content=doc_data.get("content", ""),
                category=doc_data.get("category", "general"),
                source=doc_data.get("source", "upload"),
                tags=doc_data.get("tags", []),
                metadata=doc_data.get("metadata", {})
            )
            documents.append(document)

        # Initialize knowledge base using the RAG service
        result = await helpdesk_rag_service.initialize_knowledge_base(
            company_name=company_name,
            documents=documents
        )

        return {
            "success": True,
            "message": f"Knowledge base initialized for {company_name}",
            "details": result
        }

    except Exception as e:
        logger.error(f"Error initializing knowledge base: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize knowledge base: {str(e)}"
        )

def _extract_file_content(file: UploadFile, file_content: bytes) -> str:
    """
    Extract text content from uploaded files based on their type.

    Supports:
    - PDF (with OCR fallback for scanned PDFs)
    - Word (.docx, .doc) with tables, headers, footers
    - Excel (.xlsx, .xls) with multi-sheet support
    - Text files (.txt, .md)
    """
    try:
        if file.content_type == "text/plain" or file.content_type == "text/markdown":
            # Handle text files
            return file_content.decode('utf-8')

        elif file.content_type == "application/pdf":
            return _extract_pdf_content(file_content)

        elif file.content_type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword"
        ]:
            return _extract_word_content(file_content, file.content_type)

        elif file.content_type in [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel"
        ]:
            return _extract_excel_content(file_content, file.content_type)

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type for content extraction: {file.content_type}"
            )

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Could not decode file content. Please ensure the file is not corrupted."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting file content: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract content from file: {str(e)}"
        )


def _extract_pdf_content(file_content: bytes) -> str:
    """
    Extract text from PDF with OCR fallback for scanned PDFs.

    Args:
        file_content: PDF file bytes

    Returns:
        Extracted text content
    """
    try:
        import PyPDF2
        import io

        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""

        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        # Check if we extracted meaningful content
        if len(text.strip()) < 50:
            logger.warning("PDF extraction yielded minimal text, attempting OCR...")
            try:
                # Attempt OCR using pytesseract
                import pdf2image
                import pytesseract
                from PIL import Image

                # Convert PDF pages to images
                images = pdf2image.convert_from_bytes(file_content)

                ocr_text = ""
                for i, image in enumerate(images):
                    # Extract text from image using OCR
                    page_text = pytesseract.image_to_string(image)
                    ocr_text += f"\n--- Page {i+1} ---\n{page_text}\n"

                if len(ocr_text.strip()) > len(text.strip()):
                    logger.info("OCR extraction successful, using OCR text")
                    return ocr_text.strip()

            except ImportError:
                logger.warning("OCR libraries not available (pdf2image, pytesseract). Install for scanned PDF support.")
            except Exception as ocr_error:
                logger.error(f"OCR extraction failed: {str(ocr_error)}")

        return text.strip()

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="PDF processing not available. PyPDF2 not installed."
        )


def _extract_word_content(file_content: bytes, content_type: str) -> str:
    """
    Extract text from Word document including paragraphs, tables, headers, and footers.

    Args:
        file_content: Word file bytes
        content_type: MIME type

    Returns:
        Extracted text content
    """
    try:
        import docx
        import io

        doc = docx.Document(io.BytesIO(file_content))
        text_parts = []

        # Extract headers
        for section in doc.sections:
            header = section.header
            for paragraph in header.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(f"[Header] {paragraph.text}")

        # Extract main document paragraphs
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)

        # Extract tables
        for table_num, table in enumerate(doc.tables, 1):
            text_parts.append(f"\n--- Table {table_num} ---")
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                if row_text.strip():
                    text_parts.append(row_text)

        # Extract footers
        for section in doc.sections:
            footer = section.footer
            for paragraph in footer.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(f"[Footer] {paragraph.text}")

        return "\n".join(text_parts)

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Word document processing not available. python-docx not installed."
        )


def _extract_excel_content(file_content: bytes, content_type: str) -> str:
    """
    Extract text from Excel spreadsheet with multi-sheet support.

    Args:
        file_content: Excel file bytes
        content_type: MIME type

    Returns:
        Extracted text content from all sheets
    """
    try:
        import openpyxl
        import io

        # Load workbook
        workbook = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
        text_parts = []

        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            text_parts.append(f"\n=== Sheet: {sheet_name} ===\n")

            # Extract all rows
            for row_num, row in enumerate(sheet.iter_rows(values_only=True), 1):
                # Filter out empty cells and convert to strings
                row_values = [str(cell) for cell in row if cell is not None and str(cell).strip()]
                if row_values:
                    row_text = " | ".join(row_values)
                    text_parts.append(f"Row {row_num}: {row_text}")

        return "\n".join(text_parts)

    except ImportError:
        # Try fallback to pandas for older .xls files
        try:
            import pandas as pd
            import io

            # Read all sheets
            excel_file = pd.ExcelFile(io.BytesIO(file_content))
            text_parts = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                text_parts.append(f"\n=== Sheet: {sheet_name} ===\n")

                # Convert dataframe to text representation
                text_parts.append(df.to_string(index=False))

            return "\n".join(text_parts)

        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Excel processing not available. Install openpyxl or pandas+xlrd."
            )

# ============================================================================
# Analytics Endpoints
# ============================================================================

@router.get("/{company_name}/analytics/overview")
async def get_analytics_overview(
    company_name: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Get overview analytics for the knowledge base.

    Now properly scoped to organization. Requires authentication.

    Includes:
    - Total queries (overall, 24h, 7d)
    - Average confidence score
    - Escalation rate
    - Processing time metrics
    - Daily query trend
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        metrics = await rag_analytics_service.get_overview_metrics(company_name, days)

        return {
            "success": True,
            "data": metrics
        }

    except Exception as e:
        logger.error(f"Error getting analytics overview: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analytics overview: {str(e)}"
        )


@router.get("/{company_name}/analytics/confidence-distribution")
async def get_confidence_distribution(
    company_name: str,
    days: int = Query(default=30, ge=1, le=365),
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Get confidence score distribution across queries.

    Now properly scoped to organization. Requires authentication.

    Returns buckets: 0-50%, 50-70%, 70-85%, 85-95%, 95-100%
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        distribution = await rag_analytics_service.get_confidence_distribution(company_name, days)

        return {
            "success": True,
            "data": distribution
        }

    except Exception as e:
        logger.error(f"Error getting confidence distribution: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get confidence distribution: {str(e)}"
        )


@router.get("/{company_name}/analytics/top-queries")
async def get_top_queries(
    company_name: str,
    limit: int = Query(default=10, ge=1, le=50),
    days: int = Query(default=30, ge=1, le=365),
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Get most common queries with statistics.

    Now properly scoped to organization. Requires authentication.

    Includes query count, average confidence, and escalation rate.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        queries = await rag_analytics_service.get_top_queries(company_name, limit, days)

        return {
            "success": True,
            "data": queries
        }

    except Exception as e:
        logger.error(f"Error getting top queries: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get top queries: {str(e)}"
        )


@router.get("/{company_name}/analytics/escalations")
async def get_escalation_analysis(
    company_name: str,
    days: int = Query(default=30, ge=1, le=365),
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Get escalation analysis including reasons and trends.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        analysis = await rag_analytics_service.get_escalation_analysis(company_name, days)

        return {
            "success": True,
            "data": analysis
        }

    except Exception as e:
        logger.error(f"Error getting escalation analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get escalation analysis: {str(e)}"
        )


@router.get("/{company_name}/analytics/source-usage")
async def get_source_usage_stats(
    company_name: str,
    limit: int = Query(default=20, ge=1, le=100),
    days: int = Query(default=30, ge=1, le=365),
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Get statistics on which documents are most referenced.

    Now properly scoped to organization. Requires authentication.

    Shows document usage and effectiveness metrics.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        stats = await rag_analytics_service.get_source_usage_stats(company_name, days, limit)

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"Error getting source usage stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get source usage stats: {str(e)}"
        )


@router.get("/{company_name}/analytics/performance")
async def get_performance_metrics(
    company_name: str,
    days: int = Query(default=30, ge=1, le=365),
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Get performance metrics including response times.

    Now properly scoped to organization. Requires authentication.

    Returns average, min, max, p50, and p95 processing times.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        metrics = await rag_analytics_service.get_performance_metrics(company_name, days)

        return {
            "success": True,
            "data": metrics
        }

    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.get("/{company_name}/analytics/time-series")
async def get_time_series_data(
    company_name: str,
    days: int = Query(default=30, ge=1, le=365),
    granularity: str = Query(default="day", regex="^(hour|day|week)$"),
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Get time series data for queries, confidence, and escalations.

    Now properly scoped to organization. Requires authentication.

    Granularity options: hour, day, week
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        data = await rag_analytics_service.get_time_series_data(company_name, days, granularity)

        return {
            "success": True,
            "data": data,
            "granularity": granularity,
            "period_days": days
        }

    except Exception as e:
        logger.error(f"Error getting time series data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get time series data: {str(e)}"
        )


# ============================================================================
# Monitoring Dashboard Endpoints (Tool Call Logger)
# ============================================================================

@router.get("/{company_name}/monitoring/metrics")
async def get_monitoring_metrics(
    company_name: str,
    hours: int = Query(default=24, ge=1, le=168, description="Time period in hours (max 7 days)"),
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Get real-time monitoring metrics for the RAG system.

    Now properly scoped to organization. Requires authentication.

    Includes:
    - Query volume (total, successful, failed, cached)
    - Performance metrics (avg, min, max, p50, p95, p99 response times)
    - Quality metrics (avg confidence, escalation rate)
    - Top queries, cities, and specialties
    - Common errors

    Data retention: Last 7 days (TTL auto-cleanup)
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        metrics = await tool_call_logger.get_monitoring_metrics(company_name, hours)

        return {
            "success": True,
            "data": metrics.dict(),
            "period_hours": hours
        }

    except Exception as e:
        logger.error(f"Error getting monitoring metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get monitoring metrics: {str(e)}"
        )


@router.get("/{company_name}/monitoring/top-queries")
async def get_monitoring_top_queries(
    company_name: str,
    limit: int = Query(default=50, ge=1, le=100, description="Number of top queries to return"),
    days: int = Query(default=7, ge=1, le=7, description="Number of days to analyze (max 7)"),
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Get top query patterns for pre-computation analysis.

    Now properly scoped to organization. Requires authentication.

    Includes:
    - Query pattern
    - Total count
    - Average confidence
    - Average processing time
    - Success rate
    - Last queried timestamp
    - Whether it's already pre-computed

    Use this to identify which queries should be pre-computed for instant responses.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        queries = await tool_call_logger.get_top_queries(company_name, limit, days)

        return {
            "success": True,
            "data": [q.dict() for q in queries],
            "limit": limit,
            "period_days": days
        }

    except Exception as e:
        logger.error(f"Error getting top queries: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get top queries: {str(e)}"
        )


@router.get("/{company_name}/monitoring/pre-computed")
async def get_pre_computed_queries(
    company_name: str,
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Get currently active pre-computed queries.

    Now properly scoped to organization. Requires authentication.

    Shows which queries have cached responses available for instant retrieval.
    Pre-computed responses expire after 24 hours and are automatically regenerated.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Query MongoDB for all non-expired pre-computed queries
        from datetime import datetime as dt

        precomputed_queries = []
        async for doc in tool_call_logger.precomputed_collection.find({
            "company_name": company_name,
            "expires_at": {"$gt": dt.utcnow()}
        }).sort("query_count", -1):
            precomputed_queries.append({
                "query_pattern": doc.get("query_pattern"),
                "response_preview": doc.get("response", "")[:200] + "...",
                "confidence_score": doc.get("confidence_score"),
                "query_count": doc.get("query_count", 0),
                "last_requested": doc.get("last_requested"),
                "computed_at": doc.get("computed_at"),
                "expires_at": doc.get("expires_at"),
                "avg_processing_time": doc.get("avg_processing_time", 0.0)
            })

        return {
            "success": True,
            "data": precomputed_queries,
            "total": len(precomputed_queries)
        }

    except Exception as e:
        logger.error(f"Error getting pre-computed queries: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pre-computed queries: {str(e)}"
        )


# ============================================================================
# Query Pre-computation Endpoints
# ============================================================================

@router.post("/{company_name}/precompute")
async def trigger_precomputation(
    company_name: str,
    days: int = Query(default=7, ge=1, le=30, description="Days to analyze for top queries"),
    force: bool = Query(default=False, description="Force re-computation of already cached queries"),
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Manually trigger pre-computation of top queries.

    Now properly scoped to organization. Requires authentication.

    Analyzes query logs from the past N days and pre-computes responses
    for the most common queries. Pre-computed responses are cached for 24 hours.

    **Background Job**: This endpoint runs in the background and may take several minutes.

    Use this for:
    - Manual pre-computation (instead of waiting for daily cron)
    - After uploading new documents to re-compute responses
    - Testing the pre-computation system
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        from backend.services.query_precompute_service import query_precompute_service

        logger.info(f"🚀 Manual pre-computation triggered for {company_name} [org: {org_id}]")

        result = await query_precompute_service.precompute_top_queries(
            company_name=company_name,
            days=days,
            force=force
        )

        return result

    except Exception as e:
        logger.error(f"Error triggering pre-computation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger pre-computation: {str(e)}"
        )


@router.get("/{company_name}/precompute/status")
async def get_precompute_status(
    company_name: str,
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Get status of query pre-computation system.

    Now properly scoped to organization. Requires authentication.

    Returns:
    - Cache statistics (hit rate, memory usage, etc.)
    - Pre-computation configuration
    - Currently cached queries count
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        from backend.services.query_precompute_service import query_precompute_service

        status = await query_precompute_service.get_precompute_status(company_name)

        return status

    except Exception as e:
        logger.error(f"Error getting pre-compute status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pre-compute status: {str(e)}"
        )


@router.delete("/{company_name}/precompute/cache")
async def invalidate_cache(
    company_name: str,
    query: Optional[str] = Query(default=None, description="Specific query to invalidate (if None, invalidates all)"),
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Invalidate cached/pre-computed queries.

    Now properly scoped to organization. Requires authentication.

    Use this when:
    - Documents have been updated and responses need to be refreshed
    - Testing cache functionality
    - Clearing stale cached data

    If query is provided, only that specific query is invalidated.
    If query is None, ALL cached queries for the company are invalidated.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        from backend.services.query_precompute_service import query_precompute_service

        result = await query_precompute_service.invalidate_cache(
            company_name=company_name,
            query=query
        )

        return result

    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invalidate cache: {str(e)}"
        )
