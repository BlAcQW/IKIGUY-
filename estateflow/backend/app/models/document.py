"""
Document Data Models

AI-powered document generation for real estate contracts, agreements,
and legal documents.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Types of documents that can be generated"""
    LEASE_AGREEMENT = "lease_agreement"
    PURCHASE_AGREEMENT = "purchase_agreement"
    RENTAL_APPLICATION = "rental_application"
    PROPERTY_DISCLOSURE = "property_disclosure"
    OFFER_LETTER = "offer_letter"
    COUNTER_OFFER = "counter_offer"
    ADDENDUM = "addendum"
    TENANT_SCREENING = "tenant_screening"
    EVICTION_NOTICE = "eviction_notice"
    LEASE_RENEWAL = "lease_renewal"
    MOVE_IN_CHECKLIST = "move_in_checklist"
    MOVE_OUT_CHECKLIST = "move_out_checklist"
    MAINTENANCE_REQUEST = "maintenance_request"
    RENT_RECEIPT = "rent_receipt"
    SECURITY_DEPOSIT_RETURN = "security_deposit_return"


class DocumentStatus(str, Enum):
    """Document lifecycle status"""
    DRAFT = "draft"  # Being edited
    PENDING_REVIEW = "pending_review"  # Awaiting review
    READY = "ready"  # Ready for signature
    SENT = "sent"  # Sent to parties
    SIGNED = "signed"  # Fully executed
    EXPIRED = "expired"  # Expired before signing
    CANCELLED = "cancelled"  # Cancelled


class SignatureStatus(str, Enum):
    """Signature status for e-signing"""
    PENDING = "pending"
    SIGNED = "signed"
    DECLINED = "declined"


class DocumentFormat(str, Enum):
    """Output format for generated documents"""
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    MARKDOWN = "markdown"


class Party(BaseModel):
    """
    Party involved in the document.

    Could be landlord, tenant, buyer, seller, agent, etc.
    """
    role: str = Field(..., description="Party role (landlord, tenant, buyer, seller, agent)")
    name: str = Field(..., description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Physical address")

    # Signature
    signature_required: bool = Field(True, description="Whether signature is required")
    signature_status: SignatureStatus = Field(SignatureStatus.PENDING, description="Signature status")
    signed_at: Optional[datetime] = Field(None, description="When signed")
    signature_data: Optional[str] = Field(None, description="Signature image data (base64)")


class DocumentVariable(BaseModel):
    """
    Variable in document template.

    Templates use Jinja2 syntax with variables.
    """
    key: str = Field(..., description="Variable key")
    label: str = Field(..., description="Human-readable label")
    description: Optional[str] = Field(None, description="Help text")
    variable_type: str = Field("text", description="Type: text, number, date, boolean, select")
    required: bool = Field(True, description="Whether required")
    default_value: Optional[Any] = Field(None, description="Default value")
    options: Optional[List[str]] = Field(None, description="Options for select type")
    validation_regex: Optional[str] = Field(None, description="Validation regex")


class DocumentTemplate(BaseModel):
    """
    Document template with Jinja2 content.

    Templates are organization-specific and can be customized.
    """
    id: str = Field(..., description="Template ID")
    organization_id: str = Field(..., description="Organization ID")

    # Template info
    name: str = Field(..., description="Template name")
    document_type: DocumentType = Field(..., description="Document type")
    description: Optional[str] = Field(None, description="Template description")

    # Content
    template_content: str = Field(..., description="Jinja2 template content (HTML or Markdown)")
    variables: List[DocumentVariable] = Field(default_factory=list, description="Template variables")

    # Metadata
    language: str = Field("en", description="Template language")
    jurisdiction: Optional[str] = Field(None, description="Legal jurisdiction (e.g., 'Ghana', 'California')")
    version: str = Field("1.0", description="Template version")

    # Status
    is_active: bool = Field(True, description="Whether template is active")
    is_default: bool = Field(False, description="Whether this is the default template for this type")

    # AI generation
    ai_generated: bool = Field(False, description="Whether template was AI-generated")
    ai_prompt: Optional[str] = Field(None, description="Prompt used for AI generation")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Created timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Updated timestamp")
    created_by: Optional[str] = Field(None, description="User ID who created")


class Document(BaseModel):
    """
    Generated document instance.

    Created from template with filled variables.
    """
    id: str = Field(..., description="Document ID")
    organization_id: str = Field(..., description="Organization ID")

    # Template reference
    template_id: str = Field(..., description="Template used")
    document_type: DocumentType = Field(..., description="Document type")

    # Document info
    title: str = Field(..., description="Document title")
    description: Optional[str] = Field(None, description="Document description")

    # Parties
    parties: List[Party] = Field(default_factory=list, description="Parties involved")

    # Content
    variables: Dict[str, Any] = Field(..., description="Filled variable values")
    rendered_content: Optional[str] = Field(None, description="Rendered HTML/Markdown content")

    # Files
    pdf_url: Optional[str] = Field(None, description="Generated PDF URL")
    docx_url: Optional[str] = Field(None, description="Generated DOCX URL")

    # Status
    status: DocumentStatus = Field(DocumentStatus.DRAFT, description="Document status")

    # Associations
    property_id: Optional[str] = Field(None, description="Associated property ID")
    contact_id: Optional[str] = Field(None, description="Associated contact ID")
    booking_id: Optional[str] = Field(None, description="Associated booking ID")

    # E-signature
    signature_request_id: Optional[str] = Field(None, description="DocuSign/HelloSign request ID")
    all_signed: bool = Field(False, description="Whether all parties have signed")
    fully_executed_at: Optional[datetime] = Field(None, description="When fully executed")

    # Expiration
    expires_at: Optional[datetime] = Field(None, description="Expiration date")

    # Audit trail
    version: int = Field(1, description="Document version")
    revision_history: List[Dict[str, Any]] = Field(default_factory=list, description="Change history")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Created timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Updated timestamp")
    created_by: Optional[str] = Field(None, description="User ID who created")


class DocumentCreateRequest(BaseModel):
    """
    Request to create a new document from template.
    """
    template_id: str = Field(..., description="Template to use")
    title: str = Field(..., description="Document title")
    description: Optional[str] = Field(None, description="Document description")

    # Variables
    variables: Dict[str, Any] = Field(..., description="Variable values")

    # Parties
    parties: List[Party] = Field(default_factory=list, description="Parties involved")

    # Associations
    property_id: Optional[str] = Field(None, description="Associated property")
    contact_id: Optional[str] = Field(None, description="Associated contact")
    booking_id: Optional[str] = Field(None, description="Associated booking")

    # Output format
    generate_pdf: bool = Field(True, description="Generate PDF")
    generate_docx: bool = Field(False, description="Generate DOCX")

    # E-signature
    send_for_signature: bool = Field(False, description="Send for e-signature immediately")

    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "tmpl_lease_001",
                "title": "Lease Agreement - 123 Main St",
                "variables": {
                    "property_address": "123 Main Street, Accra",
                    "monthly_rent": 2000,
                    "lease_start_date": "2025-01-01",
                    "lease_end_date": "2026-01-01",
                    "security_deposit": 4000
                },
                "parties": [
                    {
                        "role": "landlord",
                        "name": "John Smith",
                        "email": "john@example.com"
                    },
                    {
                        "role": "tenant",
                        "name": "Jane Doe",
                        "email": "jane@example.com"
                    }
                ],
                "generate_pdf": True,
                "send_for_signature": False
            }
        }


class DocumentUpdateRequest(BaseModel):
    """
    Request to update document.
    """
    title: Optional[str] = Field(None, description="Update title")
    description: Optional[str] = Field(None, description="Update description")
    variables: Optional[Dict[str, Any]] = Field(None, description="Update variables")
    parties: Optional[List[Party]] = Field(None, description="Update parties")
    status: Optional[DocumentStatus] = Field(None, description="Update status")


class TemplateGenerateRequest(BaseModel):
    """
    Request to AI-generate a new template.
    """
    document_type: DocumentType = Field(..., description="Document type to generate")
    jurisdiction: str = Field("Ghana", description="Legal jurisdiction")
    language: str = Field("en", description="Template language")

    # Customization
    custom_clauses: Optional[List[str]] = Field(None, description="Custom clauses to include")
    exclude_clauses: Optional[List[str]] = Field(None, description="Standard clauses to exclude")

    # AI prompt
    additional_instructions: Optional[str] = Field(None, description="Additional instructions for AI")

    class Config:
        json_schema_extra = {
            "example": {
                "document_type": "lease_agreement",
                "jurisdiction": "Ghana",
                "language": "en",
                "custom_clauses": ["Pet policy with $500 deposit", "No smoking clause"],
                "additional_instructions": "Make it tenant-friendly with flexible terms"
            }
        }


class DocumentListResponse(BaseModel):
    """
    Paginated document list response.
    """
    documents: List[Document] = Field(..., description="List of documents")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Page offset")


class TemplateListResponse(BaseModel):
    """
    Paginated template list response.
    """
    templates: List[DocumentTemplate] = Field(..., description="List of templates")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Page offset")
