"""
Document API Router

AI-powered document generation and template management endpoints.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from io import BytesIO
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.auth import get_current_user, get_organization_context
from app.services.document_service import DocumentService
from app.models.document import (
    Document,
    DocumentTemplate,
    DocumentCreateRequest,
    DocumentUpdateRequest,
    TemplateGenerateRequest,
    DocumentListResponse,
    TemplateListResponse,
    DocumentType,
    DocumentStatus
)


router = APIRouter(prefix="/documents", tags=["documents"])


# ==================== Document Management ====================

@router.post("", response_model=Document)
async def create_document(
    request: DocumentCreateRequest,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Create a new document from template.

    **Features:**
    - Renders template with provided variables
    - Validates all required fields
    - Generates PDF/DOCX (optional)
    - Can send for e-signature immediately
    - Associates with property, contact, or booking

    **Example:**
    ```json
    {
      "template_id": "tmpl_lease_001",
      "title": "Lease Agreement - 123 Main St",
      "variables": {
        "property_address": "123 Main Street, Accra",
        "monthly_rent": 2000,
        "lease_start_date": "2025-01-01",
        "security_deposit": 4000
      },
      "parties": [
        {"role": "landlord", "name": "John Smith", "email": "john@example.com"},
        {"role": "tenant", "name": "Jane Doe", "email": "jane@example.com"}
      ],
      "generate_pdf": true
    }
    ```
    """
    document_service = DocumentService(database)

    try:
        document = await document_service.create_document(
            request=request,
            organization_id=org_context["organization_id"],
            user_id=org_context.get("user_id")
        )
        return document
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    document_type: Optional[DocumentType] = Query(None, description="Filter by document type"),
    status: Optional[DocumentStatus] = Query(None, description="Filter by status"),
    property_id: Optional[str] = Query(None, description="Filter by property"),
    contact_id: Optional[str] = Query(None, description="Filter by contact"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    List documents with optional filters.

    Supports filtering by:
    - Document type (lease, purchase, etc.)
    - Status (draft, ready, signed, etc.)
    - Associated property
    - Associated contact
    """
    document_service = DocumentService(database)

    documents, total = await document_service.list_documents(
        organization_id=org_context["organization_id"],
        document_type=document_type,
        status=status,
        property_id=property_id,
        contact_id=contact_id,
        limit=limit,
        offset=offset
    )

    return DocumentListResponse(
        documents=documents,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """Get document details by ID."""
    document_service = DocumentService(database)

    document = await document_service.get_document(
        document_id=document_id,
        organization_id=org_context["organization_id"]
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.put("/{document_id}", response_model=Document)
async def update_document(
    document_id: str,
    updates: DocumentUpdateRequest,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Update document.

    **Features:**
    - Update variables (re-renders template automatically)
    - Update parties
    - Change status
    - Maintains revision history
    - Increments version number
    """
    document_service = DocumentService(database)

    try:
        document = await document_service.update_document(
            document_id=document_id,
            updates=updates,
            organization_id=org_context["organization_id"]
        )

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return document
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """Delete document."""
    document_service = DocumentService(database)

    deleted = await document_service.delete_document(
        document_id=document_id,
        organization_id=org_context["organization_id"]
    )

    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"message": "Document deleted successfully"}


# ==================== Template Management ====================

@router.post("/templates", response_model=DocumentTemplate)
async def create_template(
    template: DocumentTemplate,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Create a new document template.

    **Template Content Format:**
    Use Jinja2 syntax for variables:
    ```html
    <h1>Lease Agreement</h1>
    <p>Property Address: {{ property_address }}</p>
    <p>Monthly Rent: ${{ monthly_rent }}</p>
    <p>Lease Term: {{ lease_start_date }} to {{ lease_end_date }}</p>
    ```

    **Variable Definitions:**
    Define each variable with type, label, and validation:
    ```json
    {
      "key": "monthly_rent",
      "label": "Monthly Rent Amount",
      "description": "Monthly rent in USD",
      "variable_type": "number",
      "required": true
    }
    ```
    """
    document_service = DocumentService(database)

    try:
        created_template = await document_service.create_template(
            template=template,
            organization_id=org_context["organization_id"]
        )
        return created_template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    document_type: Optional[DocumentType] = Query(None, description="Filter by document type"),
    is_active: bool = Query(True, description="Filter active/inactive"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    List document templates.

    Returns all templates available to the organization.
    """
    document_service = DocumentService(database)

    templates, total = await document_service.list_templates(
        organization_id=org_context["organization_id"],
        document_type=document_type,
        is_active=is_active,
        limit=limit,
        offset=offset
    )

    return TemplateListResponse(
        templates=templates,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/templates/{template_id}", response_model=DocumentTemplate)
async def get_template(
    template_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """Get template details by ID."""
    document_service = DocumentService(database)

    template = await document_service.get_template(
        template_id=template_id,
        organization_id=org_context["organization_id"]
    )

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


@router.put("/templates/{template_id}", response_model=DocumentTemplate)
async def update_template(
    template_id: str,
    updates: Dict[str, Any],
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """Update template."""
    document_service = DocumentService(database)

    try:
        template = await document_service.update_template(
            template_id=template_id,
            updates=updates,
            organization_id=org_context["organization_id"]
        )

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """Delete template (soft delete)."""
    document_service = DocumentService(database)

    deleted = await document_service.delete_template(
        template_id=template_id,
        organization_id=org_context["organization_id"]
    )

    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")

    return {"message": "Template deleted successfully"}


# ==================== AI Template Generation ====================

@router.post("/templates/generate-ai", response_model=DocumentTemplate)
async def generate_template_with_ai(
    request: TemplateGenerateRequest,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Generate a new template using AI.

    **Features:**
    - AI analyzes document type and jurisdiction
    - Generates legally appropriate content
    - Creates all necessary variables
    - Includes standard clauses
    - Customizable with specific requirements

    **Example:**
    ```json
    {
      "document_type": "lease_agreement",
      "jurisdiction": "Ghana",
      "language": "en",
      "custom_clauses": [
        "Pet policy with $500 deposit",
        "No smoking clause"
      ],
      "additional_instructions": "Make it tenant-friendly with flexible terms"
    }
    ```

    **Supported Document Types:**
    - lease_agreement
    - purchase_agreement
    - rental_application
    - offer_letter
    - and 11 more...
    """
    document_service = DocumentService(database)

    try:
        template = await document_service.generate_template_with_ai(
            request=request,
            organization_id=org_context["organization_id"],
            user_id=org_context.get("user_id")
        )
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Document Actions ====================

@router.post("/{document_id}/send-for-signature")
async def send_for_signature(
    document_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Send document for e-signature.

    TODO: Integrate with DocuSign, HelloSign, or Adobe Sign
    """
    raise HTTPException(status_code=501, detail="E-signature integration not yet implemented")


@router.get("/{document_id}/download/pdf")
async def download_pdf(
    document_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Download document as PDF.

    Generates a PDF from the rendered document content and returns it for download.
    """
    document_service = DocumentService(database)

    try:
        # Get document
        document = await document_service.get_document(
            document_id=document_id,
            organization_id=org_context["organization_id"]
        )

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Generate PDF
        pdf_bytes = await document_service.generate_pdf(
            document_id=document_id,
            organization_id=org_context["organization_id"]
        )

        # Create streaming response
        pdf_stream = BytesIO(pdf_bytes)

        # Generate filename from document title
        filename = f"{document.title.replace(' ', '_')}.pdf"

        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


@router.get("/{document_id}/download/docx")
async def download_docx(
    document_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Download document as DOCX.

    Generates a DOCX from the rendered document content and returns it for download.
    """
    document_service = DocumentService(database)

    try:
        # Get document
        document = await document_service.get_document(
            document_id=document_id,
            organization_id=org_context["organization_id"]
        )

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Generate DOCX
        docx_bytes = await document_service.generate_docx(
            document_id=document_id,
            organization_id=org_context["organization_id"]
        )

        # Create streaming response
        docx_stream = BytesIO(docx_bytes)

        # Generate filename from document title
        filename = f"{document.title.replace(' ', '_')}.docx"

        return StreamingResponse(
            docx_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate DOCX: {str(e)}")
