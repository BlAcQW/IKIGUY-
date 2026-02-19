"""Legal Document Routes - NDA, Contracts, E-Signatures."""

import logging
import secrets
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import FileResponse
from datetime import datetime, timedelta
from pathlib import Path

from app.core.database import MongoDB
from app.models.legal import (
    LegalDocument,
    LegalDocumentCreate,
    DocumentSignature,
    DocumentSignatureCreate,
    SignDocumentRequest,
    LegalDocumentUpdate,
    DocumentType,
    DocumentStatus,
    SignatureType,
)
from apps.shared.dependencies import require_organization_access, OrganizationScoped

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# LEGAL DOCUMENTS CRUD (Authenticated - HR Use)
# ============================================================================

@router.post("/documents", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_legal_document(
    document_create: LegalDocumentCreate,
    scope: OrganizationScoped = Depends()
):
    """
    Create a new legal document (NDA, contract, etc.).

    Used by HR to create documents for employees.
    """
    db = MongoDB.get_database()

    # Generate unique signing token
    signing_token = secrets.token_urlsafe(32)

    document_data = LegalDocument(
        **document_create.model_dump(),
        organization_id=scope.org_id,
        created_by=scope.user.get("id") or scope.user.get("sub")
    )

    document_dict = document_data.model_dump()
    document_dict["signing_token"] = signing_token
    document_dict["signing_link"] = f"/legal/sign/{signing_token}"

    await db.legal_documents.insert_one(document_dict)
    logger.info(f"Legal document created: {document_data.document_type} for {document_data.employee_name}")

    return document_dict


@router.get("/documents", response_model=List[Dict[str, Any]])
async def list_legal_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    document_type: Optional[DocumentType] = Query(None),
    status: Optional[DocumentStatus] = Query(None),
    employee_id: Optional[str] = Query(None),
    scope: OrganizationScoped = Depends()
):
    """List all legal documents for the organization."""
    db = MongoDB.get_database()

    query = {"organization_id": scope.org_id}
    if document_type:
        query["document_type"] = document_type
    if status:
        query["status"] = status
    if employee_id:
        query["employee_id"] = employee_id

    cursor = db.legal_documents.find(query).skip(skip).limit(limit).sort("created_at", -1)
    documents = await cursor.to_list(length=limit)

    return documents


@router.get("/documents/{document_id}", response_model=Dict[str, Any])
async def get_legal_document(document_id: str, scope: OrganizationScoped = Depends()):
    """Get a specific legal document."""
    db = MongoDB.get_database()

    document = await db.legal_documents.find_one({
        "id": document_id,
        "organization_id": scope.org_id
    })

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.patch("/documents/{document_id}", response_model=Dict[str, Any])
async def update_legal_document(
    document_id: str,
    document_update: LegalDocumentUpdate,
    scope: OrganizationScoped = Depends()
):
    """Update a legal document."""
    db = MongoDB.get_database()

    update_data = document_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by"] = scope.user.get("id") or scope.user.get("sub")

    result = await db.legal_documents.update_one(
        {"id": document_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")

    updated_document = await db.legal_documents.find_one({
        "id": document_id,
        "organization_id": scope.org_id
    })

    return updated_document


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_legal_document(document_id: str, scope: OrganizationScoped = Depends()):
    """Delete a legal document."""
    db = MongoDB.get_database()

    result = await db.legal_documents.delete_one({
        "id": document_id,
        "organization_id": scope.org_id
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")


# ============================================================================
# PUBLIC SIGNING ENDPOINTS (No Authentication Required)
# ============================================================================

@router.get("/sign/{signing_token}", response_model=Dict[str, Any])
async def get_document_for_signing(signing_token: str):
    """
    Public endpoint - Get document to sign (no authentication required).

    This is the endpoint the new hire will access via email link.
    """
    db = MongoDB.get_database()

    document = await db.legal_documents.find_one({
        "signing_token": signing_token
    })

    if not document:
        raise HTTPException(status_code=404, detail="Document not found or link expired")

    if document.get("status") == DocumentStatus.SIGNED:
        raise HTTPException(status_code=400, detail="Document already signed")

    if document.get("expires_at"):
        if datetime.fromisoformat(str(document["expires_at"])) < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Signing link has expired")

    # Return document without sensitive organization data
    return {
        "id": document["id"],
        "document_type": document["document_type"],
        "title": document["title"],
        "content": document["content"],
        "employee_name": document["employee_name"],
        "employee_email": document["employee_email"],
        "company_representative": document.get("company_representative"),
        "effective_date": document.get("effective_date"),
        "status": document["status"]
    }


@router.post("/sign/{signing_token}", response_model=Dict[str, Any])
async def sign_document(
    signing_token: str,
    sign_request: SignDocumentRequest,
    request: Request
):
    """
    Public endpoint - Submit electronic signature (no authentication required).

    Captures signature, IP address, user agent, and updates document status.
    """
    db = MongoDB.get_database()

    # Get document
    document = await db.legal_documents.find_one({
        "signing_token": signing_token
    })

    if not document:
        raise HTTPException(status_code=404, detail="Document not found or link expired")

    if document.get("status") == DocumentStatus.SIGNED:
        raise HTTPException(status_code=400, detail="Document already signed")

    if document.get("expires_at"):
        if datetime.fromisoformat(str(document["expires_at"])) < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Signing link has expired")

    if not sign_request.consent_acknowledged:
        raise HTTPException(status_code=400, detail="Must acknowledge consent to sign")

    # Capture signature details
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")

    now = datetime.utcnow()

    # Update document with signature
    update_data = {
        "status": DocumentStatus.SIGNED,
        "signature_data": sign_request.signature_data,
        "signature_ip_address": client_ip,
        "signature_user_agent": user_agent,
        "signature_timestamp": now,
        "signed_date": now,
        "updated_at": now
    }

    await db.legal_documents.update_one(
        {"id": document["id"]},
        {"$set": update_data}
    )

    # Create signature record for audit trail
    signature_record = DocumentSignature(
        document_id=document["id"],
        signer_type="employee",
        signer_name=document["employee_name"],
        signer_email=document["employee_email"],
        signer_title=document.get("position"),
        signature_data=sign_request.signature_data,
        signature_type=SignatureType.ELECTRONIC,
        signed_at=now,
        ip_address=client_ip,
        user_agent=user_agent,
        consent_text="I have read and agree to the terms of this agreement",
        consent_checkboxes=sign_request.consents,
        verified=True,
        organization_id=document["organization_id"],
        created_by=document["employee_id"] or document["employee_email"]
    )

    await db.document_signatures.insert_one(signature_record.model_dump())

    # Update employee onboarding record if linked
    if document.get("employee_id"):
        onboarding_update = {}
        task_id_to_complete = None

        if document["document_type"] == DocumentType.NDA:
            onboarding_update = {
                "nda_document_id": document["id"],
                "nda_signed": True,
                "nda_signed_date": now
            }
            task_id_to_complete = "all_1"  # Sign NDA electronically
        elif document["document_type"] == DocumentType.EMPLOYMENT_CONTRACT:
            onboarding_update = {
                "contract_document_id": document["id"],
                "contract_signed": True,
                "contract_signed_date": now
            }
            task_id_to_complete = "all_2"  # Sign employment contract
        elif document["document_type"] == DocumentType.OFFER_LETTER:
            onboarding_update = {
                "offer_letter_document_id": document["id"],
                "offer_letter_accepted": True,
                "offer_letter_accepted_date": now
            }

        if onboarding_update:
            # Get onboarding record to update task
            onboarding_record = await db.employee_onboarding.find_one({
                "employee_id": document["employee_id"],
                "organization_id": document["organization_id"]
            })

            if onboarding_record and task_id_to_complete:
                # Update task status in tasks array
                tasks = onboarding_record.get("tasks", [])
                for task in tasks:
                    if task.get("task_id") == task_id_to_complete:
                        task["status"] = "completed"
                        task["completed_date"] = now
                        task["completed_by"] = document["employee_email"]
                        break

                # Recalculate progress
                total_tasks = len(tasks)
                completed_tasks = sum(1 for t in tasks if t.get("status") == "completed")
                progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

                # Update onboarding status if all tasks completed
                onboarding_status = onboarding_record.get("onboarding_status")
                if completed_tasks == total_tasks:
                    onboarding_status = "completed"
                elif completed_tasks > 0:
                    onboarding_status = "in_progress"

                # Update database with task completion and recalculated progress
                onboarding_update.update({
                    "tasks": tasks,
                    "completed_tasks": completed_tasks,
                    "progress_percentage": progress_percentage,
                    "onboarding_status": onboarding_status
                })

            await db.employee_onboarding.update_one(
                {
                    "employee_id": document["employee_id"],
                    "organization_id": document["organization_id"]
                },
                {"$set": onboarding_update}
            )
            logger.info(f"Updated onboarding record and task checklist for {document['employee_id']}")

    # TODO: Send email notification to HR that document was signed
    # await send_document_signed_notification(document)

    logger.info(f"Document {document['id']} signed by {document['employee_name']} from IP {client_ip}")

    return {
        "message": "Document signed successfully",
        "document_id": document["id"],
        "signed_at": now.isoformat(),
        "status": "signed"
    }


# ============================================================================
# DOCUMENT GENERATION ENDPOINTS
# ============================================================================

@router.post("/generate-nda", response_model=Dict[str, Any])
async def generate_nda_from_template(
    employee_name: str,
    employee_email: str,
    employee_id: str,
    position: str,
    start_date: str,
    scope: OrganizationScoped = Depends()
):
    """
    Generate NDA from template with employee details and organization letterhead.

    Creates a personalized NDA with company logo and address, returns signing link.
    """
    db = MongoDB.get_database()

    # Get organization details for letterhead
    organization = await db.organizations.find_one({"id": scope.org_id})
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Read NDA template
    nda_template_path = Path("/opt/kasaai/apps/shared/legal/NDA_Employee_AILabs_Africa.md")

    if not nda_template_path.exists():
        raise HTTPException(status_code=500, detail="NDA template not found")

    nda_content = nda_template_path.read_text()

    # Build organization letterhead
    org_name = organization.get("display_name", organization.get("name", ""))
    org_logo_url = organization.get("logo_url", "")

    # Get organization address (use billing_address if available, fallback to legacy address)
    billing_address = organization.get("billing_address", {})
    if billing_address:
        address_parts = [
            billing_address.get("street", ""),
            billing_address.get("street2", ""),
            billing_address.get("city", ""),
            billing_address.get("state", ""),
            billing_address.get("postal_code", ""),
            billing_address.get("country", "")
        ]
        org_address = "\n".join([part for part in address_parts if part])
    else:
        org_address = organization.get("address", "")

    org_phone = organization.get("phone", "")
    org_email = organization.get("email", "")

    # Create letterhead
    letterhead = f"""# {org_name}

"""

    if org_logo_url:
        letterhead += f"![{org_name} Logo]({org_logo_url})\n\n"

    if org_address:
        letterhead += f"{org_address}\n"
    if org_phone:
        letterhead += f"Phone: {org_phone}\n"
    if org_email:
        letterhead += f"Email: {org_email}\n"

    letterhead += "\n---\n\n"

    # Prepend letterhead to NDA content
    nda_content = letterhead + nda_content

    # Replace placeholders
    nda_content = nda_content.replace("[EMPLOYEE NAME]", employee_name.upper())
    nda_content = nda_content.replace("[JOB TITLE]", position)
    nda_content = nda_content.replace("_________________", start_date)
    nda_content = nda_content.replace("[COMPANY NAME]", org_name)

    # Generate signing token
    signing_token = secrets.token_urlsafe(32)

    # Create document
    document = LegalDocument(
        document_type=DocumentType.NDA,
        title=f"Employee NDA - {employee_name}",
        description="Employee Non-Disclosure and Confidentiality Agreement",
        template_path=str(nda_template_path),
        content=nda_content,
        employee_id=employee_id,
        employee_name=employee_name,
        employee_email=employee_email,
        status=DocumentStatus.PENDING_SIGNATURE,
        signature_required=True,
        signature_type=SignatureType.ELECTRONIC,
        effective_date=datetime.fromisoformat(start_date) if start_date else datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30),  # 30 day expiry
        organization_id=scope.org_id,
        created_by=scope.user.get("id") or scope.user.get("sub")
    )

    document_dict = document.model_dump()
    document_dict["signing_token"] = signing_token
    document_dict["signing_link"] = f"/api/v1/legal/sign/{signing_token}"
    document_dict["full_signing_url"] = f"https://erp-api.ailabsafrica.com/api/v1/legal/sign/{signing_token}"

    await db.legal_documents.insert_one(document_dict)

    logger.info(f"Generated NDA for {employee_name} ({employee_id})")

    # TODO: Send email with signing link
    # await send_nda_signing_email(employee_email, signing_token, employee_name)

    return {
        "document_id": document.id,
        "signing_token": signing_token,
        "signing_link": document_dict["signing_link"],
        "full_signing_url": document_dict["full_signing_url"],
        "expires_at": document.expires_at.isoformat() if document.expires_at else None,
        "message": f"NDA generated successfully. Send signing link to {employee_email}"
    }


@router.get("/documents/employee/{employee_id}", response_model=List[Dict[str, Any]])
async def get_employee_documents(employee_id: str, scope: OrganizationScoped = Depends()):
    """Get all legal documents for a specific employee."""
    db = MongoDB.get_database()

    documents = await db.legal_documents.find({
        "employee_id": employee_id,
        "organization_id": scope.org_id
    }).sort("created_at", -1).to_list(length=100)

    return documents


@router.post("/documents/{document_id}/resend", response_model=Dict[str, Any])
async def resend_signing_link(document_id: str, scope: OrganizationScoped = Depends()):
    """
    Resend signing link to employee.

    Generates new token and sends email.
    """
    db = MongoDB.get_database()

    document = await db.legal_documents.find_one({
        "id": document_id,
        "organization_id": scope.org_id
    })

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.get("status") == DocumentStatus.SIGNED:
        raise HTTPException(status_code=400, detail="Document already signed")

    # Generate new token
    new_token = secrets.token_urlsafe(32)
    new_expiry = datetime.utcnow() + timedelta(days=30)

    await db.legal_documents.update_one(
        {"id": document_id},
        {
            "$set": {
                "signing_token": new_token,
                "expires_at": new_expiry,
                "reminder_count": document.get("reminder_count", 0) + 1,
                "last_reminder_sent": datetime.utcnow()
            }
        }
    )

    # TODO: Send email
    # await send_nda_signing_email(document["employee_email"], new_token, document["employee_name"])

    logger.info(f"Resent signing link for document {document_id}")

    return {
        "message": "Signing link resent successfully",
        "signing_link": f"/api/v1/legal/sign/{new_token}",
        "full_signing_url": f"https://erp-api.ailabsafrica.com/api/v1/legal/sign/{new_token}",
        "expires_at": new_expiry.isoformat()
    }


@router.get("/documents/{document_id}/status", response_model=Dict[str, Any])
async def check_document_status(document_id: str, scope: OrganizationScoped = Depends()):
    """
    Check if a document has been signed.

    Useful for HR to check status without viewing full document.
    """
    db = MongoDB.get_database()

    document = await db.legal_documents.find_one({
        "id": document_id,
        "organization_id": scope.org_id
    })

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document_id": document["id"],
        "employee_name": document["employee_name"],
        "employee_email": document["employee_email"],
        "document_type": document["document_type"],
        "status": document["status"],
        "signed": document["status"] == DocumentStatus.SIGNED,
        "signed_date": document.get("signed_date"),
        "created_at": document.get("created_at"),
        "expires_at": document.get("expires_at")
    }
