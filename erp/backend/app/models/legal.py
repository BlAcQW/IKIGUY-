"""
Legal Document Models.

Handles NDAs, contracts, and electronic signatures.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel as PydanticBaseModel, Field, EmailStr
from enum import Enum

from .base import BaseModel


class DocumentType(str, Enum):
    """Document type enumeration."""

    NDA = "nda"
    EMPLOYMENT_CONTRACT = "employment_contract"
    CONSULTANT_AGREEMENT = "consultant_agreement"
    OFFER_LETTER = "offer_letter"
    OTHER = "other"


class DocumentStatus(str, Enum):
    """Document status enumeration."""

    DRAFT = "draft"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"
    EXPIRED = "expired"
    REVOKED = "revoked"


class SignatureType(str, Enum):
    """Signature type enumeration."""

    ELECTRONIC = "electronic"
    DIGITAL = "digital"
    WET_INK = "wet_ink"


class LegalDocument(BaseModel):
    """
    Legal Document model.

    Represents legal documents like NDAs and contracts with electronic signature capability.
    """

    # Document details
    document_type: DocumentType = Field(..., description="Type of document")
    title: str = Field(..., description="Document title")
    description: Optional[str] = Field(None, description="Document description")
    version: str = Field(default="1.0", description="Document version")

    # Content
    template_path: Optional[str] = Field(None, description="Path to document template")
    content: str = Field(..., description="Document content (markdown or HTML)")

    # Variables for template substitution
    variables: Dict[str, Any] = Field(default_factory=dict, description="Template variables")

    # Parties
    employee_id: Optional[str] = Field(None, description="Employee ID (if applicable)")
    employee_name: str = Field(..., description="Employee/signer name")
    employee_email: EmailStr = Field(..., description="Employee/signer email")
    company_representative: Optional[str] = Field(None, description="Company representative name")

    # Status
    status: DocumentStatus = Field(default=DocumentStatus.DRAFT, description="Document status")

    # Signature details
    signature_required: bool = Field(default=True, description="Whether signature is required")
    signature_type: SignatureType = Field(default=SignatureType.ELECTRONIC, description="Type of signature")
    signature_data: Optional[str] = Field(None, description="Base64 encoded signature image or data")
    signature_ip_address: Optional[str] = Field(None, description="IP address at signing")
    signature_user_agent: Optional[str] = Field(None, description="User agent at signing")
    signature_timestamp: Optional[datetime] = Field(None, description="When document was signed")
    signed_by_user_id: Optional[str] = Field(None, description="User ID who signed")

    # Document file
    signed_document_url: Optional[str] = Field(None, description="URL to signed PDF")
    original_document_url: Optional[str] = Field(None, description="URL to original document")

    # Expiration
    expires_at: Optional[datetime] = Field(None, description="Document expiration date")

    # Reminders
    reminder_sent: bool = Field(default=False, description="Whether reminder has been sent")
    reminder_count: int = Field(default=0, description="Number of reminders sent")
    last_reminder_sent: Optional[datetime] = Field(None, description="When last reminder was sent")

    # Metadata
    effective_date: Optional[datetime] = Field(None, description="When document becomes effective")
    signed_date: Optional[datetime] = Field(None, description="Date document was signed")
    notes: Optional[str] = Field(None, description="Additional notes")
    tags: List[str] = Field(default_factory=list, description="Document tags")


class DocumentSignature(BaseModel):
    """
    Document Signature model.

    Tracks individual signatures on documents (for multi-party agreements).
    """

    document_id: str = Field(..., description="Legal document ID")

    # Signer details
    signer_type: str = Field(..., description="Type of signer (employee, company, witness)")
    signer_name: str = Field(..., description="Full name of signer")
    signer_email: EmailStr = Field(..., description="Email of signer")
    signer_title: Optional[str] = Field(None, description="Job title or capacity")

    # Signature
    signature_data: str = Field(..., description="Base64 encoded signature")
    signature_type: SignatureType = Field(default=SignatureType.ELECTRONIC)

    # Audit trail
    signed_at: datetime = Field(default_factory=datetime.utcnow, description="Signature timestamp")
    ip_address: Optional[str] = Field(None, description="IP address at signing")
    user_agent: Optional[str] = Field(None, description="Browser user agent")
    geolocation: Optional[Dict[str, Any]] = Field(None, description="Geographic location data")

    # Consent
    consent_text: str = Field(..., description="Text that was consented to")
    consent_checkboxes: Dict[str, bool] = Field(default_factory=dict, description="Checkbox consents")

    # Verification
    verification_code: Optional[str] = Field(None, description="Email/SMS verification code")
    verified: bool = Field(default=False, description="Whether signature was verified")


# ============================================================================
# CREATE DTOs (Data Transfer Objects for POST requests)
# ============================================================================

class LegalDocumentCreate(PydanticBaseModel):
    """Legal document creation DTO."""

    document_type: DocumentType = Field(..., description="Type of document")
    title: str = Field(..., description="Document title")
    description: Optional[str] = Field(None, description="Document description")
    version: str = Field(default="1.0", description="Document version")
    template_path: Optional[str] = Field(None, description="Path to document template")
    content: str = Field(..., description="Document content (markdown or HTML)")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Template variables")
    employee_id: Optional[str] = Field(None, description="Employee ID (if applicable)")
    employee_name: str = Field(..., description="Employee/signer name")
    employee_email: EmailStr = Field(..., description="Employee/signer email")
    company_representative: Optional[str] = Field(None, description="Company representative name")
    status: DocumentStatus = Field(default=DocumentStatus.DRAFT, description="Document status")
    signature_required: bool = Field(default=True, description="Whether signature is required")
    signature_type: SignatureType = Field(default=SignatureType.ELECTRONIC, description="Type of signature")
    expires_at: Optional[datetime] = Field(None, description="Document expiration date")
    effective_date: Optional[datetime] = Field(None, description="When document becomes effective")
    notes: Optional[str] = Field(None, description="Additional notes")
    tags: List[str] = Field(default_factory=list, description="Document tags")


class DocumentSignatureCreate(PydanticBaseModel):
    """Document signature creation DTO."""

    document_id: str = Field(..., description="Legal document ID")
    signer_type: str = Field(..., description="Type of signer (employee, company, witness)")
    signer_name: str = Field(..., description="Full name of signer")
    signer_email: EmailStr = Field(..., description="Email of signer")
    signer_title: Optional[str] = Field(None, description="Job title or capacity")
    signature_data: str = Field(..., description="Base64 encoded signature")
    signature_type: SignatureType = Field(default=SignatureType.ELECTRONIC)
    ip_address: Optional[str] = Field(None, description="IP address at signing")
    user_agent: Optional[str] = Field(None, description="Browser user agent")
    geolocation: Optional[Dict[str, Any]] = Field(None, description="Geographic location data")
    consent_text: str = Field(..., description="Text that was consented to")
    consent_checkboxes: Dict[str, bool] = Field(default_factory=dict, description="Checkbox consents")
    verification_code: Optional[str] = Field(None, description="Email/SMS verification code")


class SignDocumentRequest(PydanticBaseModel):
    """Request to sign a document."""

    signature_data: str = Field(..., description="Base64 encoded signature image")
    ip_address: Optional[str] = Field(None, description="IP address of signer")
    user_agent: Optional[str] = Field(None, description="Browser user agent")
    consent_acknowledged: bool = Field(..., description="User acknowledged consent")
    consents: Dict[str, bool] = Field(default_factory=dict, description="Individual consent items")


class LegalDocumentUpdate(PydanticBaseModel):
    """Legal document update DTO."""

    title: Optional[str] = Field(None, description="Document title")
    description: Optional[str] = Field(None, description="Document description")
    content: Optional[str] = Field(None, description="Document content")
    status: Optional[DocumentStatus] = Field(None, description="Document status")
    notes: Optional[str] = Field(None, description="Additional notes")
    tags: Optional[List[str]] = Field(None, description="Document tags")
