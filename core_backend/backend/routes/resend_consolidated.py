"""
Resend Consolidated Routes - FastAPI endpoints for email operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr, Field

from ..auth import get_current_user_mongo
from ..services.resend_consolidated_service import get_resend_service

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../shared"))

from integration.resend import (
    ResendEmail,
    ResendContact,
    ResendDomain,
    ResendResponse,
)


router = APIRouter(prefix="/resend", tags=["resend", "email"])


# Request/Response Models
class ResendEmailRequest(BaseModel):
    """Request model for sending email."""
    tenant_id: str = Field(..., description="Tenant identifier")
    from_: EmailStr = Field(..., alias="from", description="Sender email address")
    to: List[EmailStr] = Field(..., description="Recipient email addresses")
    subject: str = Field(..., description="Email subject")
    html: Optional[str] = Field(None, description="HTML email content")
    text: Optional[str] = Field(None, description="Plain text email content")
    tags: Optional[List[str]] = Field(None, description="Email tags for tracking")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom email headers")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Email attachments")
    reply_to: Optional[EmailStr] = Field(None, description="Reply-to email address")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for tracking")


class ResendBatchEmailRequest(BaseModel):
    """Request model for sending batch emails."""
    tenant_id: str = Field(..., description="Tenant identifier")
    emails: List[ResendEmailRequest] = Field(..., description="List of emails to send")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for tracking")


class ResendDomainRequest(BaseModel):
    """Request model for domain operations."""
    tenant_id: str = Field(..., description="Tenant identifier")
    name: str = Field(..., description="Domain name")
    region: Optional[str] = Field(None, description="Domain region")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for tracking")


class ResendContactRequest(BaseModel):
    """Request model for contact operations."""
    tenant_id: str = Field(..., description="Tenant identifier")
    audience_id: str = Field(..., description="Audience identifier")
    contacts: List[Dict[str, Any]] = Field(..., description="List of contacts")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for tracking")


class ResendAnalyticsRequest(BaseModel):
    """Request model for analytics."""
    tenant_id: str = Field(..., description="Tenant identifier")
    start_date: Optional[datetime] = Field(None, description="Start date for analytics")
    end_date: Optional[datetime] = Field(None, description="End date for analytics")


# Email Routes
@router.post("/email/send", response_model=Dict[str, Any])
async def send_email(
    email_request: ResendEmailRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Send a single email via Resend.

    Args:
        email_request (ResendEmailRequest): Email data to send
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Response from email sending operation
    """
    try:
        resend_service = await get_resend_service()

        # Create ResendEmail object
        email = ResendEmail(
            from_=email_request.from_,
            to=email_request.to,
            subject=email_request.subject,
            html=email_request.html,
            text=email_request.text,
            tags=email_request.tags,
            headers=email_request.headers,
            attachments=email_request.attachments,
            reply_to=email_request.reply_to
        )

        # Send email with tenant context
        result = await resend_service.send_tenant_email(
            tenant_id=email_request.tenant_id,
            email=email,
            context=email_request.context
        )

        return {
            "success": result.success,
            "email_id": result.email_id,
            "data": result.data,
            "message": result.message or "Email sent successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.post("/email/batch", response_model=Dict[str, Any])
async def send_batch_emails(
    batch_request: ResendBatchEmailRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Send multiple emails in a batch via Resend.

    Args:
        batch_request (ResendBatchEmailRequest): Batch email data to send
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Response from batch email operation
    """
    try:
        resend_service = await get_resend_service()

        # Convert request emails to ResendEmail objects
        emails = []
        for email_req in batch_request.emails:
            email = ResendEmail(
                from_=email_req.from_,
                to=email_req.to,
                subject=email_req.subject,
                html=email_req.html,
                text=email_req.text,
                tags=email_req.tags,
                headers=email_req.headers,
                attachments=email_req.attachments,
                reply_to=email_req.reply_to
            )
            emails.append(email)

        # Create batch - just use emails list directly since ResendBatchEmail doesn't exist

        # Send batch with tenant context
        result = await resend_service.send_tenant_batch_emails(
            tenant_id=batch_request.tenant_id,
            emails=emails,
            context=batch_request.context
        )

        return {
            "success": result.success,
            "batch_id": result.email_id,
            "data": result.data,
            "message": result.message or "Batch emails sent successfully",
            "email_count": len(emails)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send batch emails: {str(e)}")


# Domain Routes
@router.post("/domain/add", response_model=Dict[str, Any])
async def add_domain(
    domain_request: ResendDomainRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Add a domain to Resend.

    Args:
        domain_request (ResendDomainRequest): Domain data to add
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Response from domain addition operation
    """
    try:
        resend_service = await get_resend_service()

        # Create ResendDomain object
        domain = ResendDomain(
            name=domain_request.name,
            region=domain_request.region
        )

        # Add domain with tenant context
        result = await resend_service.manage_tenant_domain(
            tenant_id=domain_request.tenant_id,
            domain=domain,
            operation="add",
            context=domain_request.context
        )

        return {
            "success": result.success,
            "domain": domain_request.name,
            "data": result.data,
            "message": result.message or "Domain added successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add domain: {str(e)}")


@router.post("/domain/verify", response_model=Dict[str, Any])
async def verify_domain(
    domain_request: ResendDomainRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Verify a domain in Resend.

    Args:
        domain_request (ResendDomainRequest): Domain data to verify
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Response from domain verification operation
    """
    try:
        resend_service = await get_resend_service()

        # Create ResendDomain object
        domain = ResendDomain(
            name=domain_request.name,
            region=domain_request.region
        )

        # Verify domain with tenant context
        result = await resend_service.manage_tenant_domain(
            tenant_id=domain_request.tenant_id,
            domain=domain,
            operation="verify",
            context=domain_request.context
        )

        return {
            "success": result.success,
            "domain": domain_request.name,
            "data": result.data,
            "message": result.message or "Domain verification initiated"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify domain: {str(e)}")


@router.delete("/domain/{domain_name}", response_model=Dict[str, Any])
async def remove_domain(
    domain_name: str,
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Remove a domain from Resend.

    Args:
        domain_name (str): Name of domain to remove
        tenant_id (str): Tenant identifier
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Response from domain removal operation
    """
    try:
        resend_service = await get_resend_service()

        # Create ResendDomain object
        domain = ResendDomain(name=domain_name)

        # Remove domain with tenant context
        result = await resend_service.manage_tenant_domain(
            tenant_id=tenant_id,
            domain=domain,
            operation="remove"
        )

        return {
            "success": result.success,
            "domain": domain_name,
            "data": result.data,
            "message": result.message or "Domain removed successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove domain: {str(e)}")


# Contact Routes
@router.post("/contacts/add", response_model=Dict[str, Any])
async def add_contacts(
    contact_request: ResendContactRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Add contacts to an audience.

    Args:
        contact_request (ResendContactRequest): Contact data to add
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Response from contact addition operation
    """
    try:
        resend_service = await get_resend_service()

        # Convert request contacts to ResendContact objects
        contacts = [ResendContact(**contact_data) for contact_data in contact_request.contacts]

        # Add contacts with tenant context
        result = await resend_service.manage_tenant_contacts(
            tenant_id=contact_request.tenant_id,
            audience_id=contact_request.audience_id,
            contacts=contacts,
            operation="add",
            context=contact_request.context
        )

        return {
            "success": result.success,
            "audience_id": contact_request.audience_id,
            "data": result.data,
            "message": result.message or "Contacts added successfully",
            "contact_count": len(contacts)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add contacts: {str(e)}")


@router.post("/contacts/remove", response_model=Dict[str, Any])
async def remove_contacts(
    contact_request: ResendContactRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Remove contacts from an audience.

    Args:
        contact_request (ResendContactRequest): Contact data to remove
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Response from contact removal operation
    """
    try:
        resend_service = await get_resend_service()

        # Convert request contacts to ResendContact objects
        contacts = [ResendContact(**contact_data) for contact_data in contact_request.contacts]

        # Remove contacts with tenant context
        result = await resend_service.manage_tenant_contacts(
            tenant_id=contact_request.tenant_id,
            audience_id=contact_request.audience_id,
            contacts=contacts,
            operation="remove",
            context=contact_request.context
        )

        return {
            "success": result.success,
            "audience_id": contact_request.audience_id,
            "data": result.data,
            "message": result.message or "Contacts removed successfully",
            "contact_count": len(contacts)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove contacts: {str(e)}")


# Analytics Routes
@router.get("/analytics", response_model=Dict[str, Any])
async def get_analytics(
    tenant_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get Resend analytics for a tenant.

    Args:
        tenant_id (str): Tenant identifier
        start_date (Optional[datetime]): Start date for analytics
        end_date (Optional[datetime]): End date for analytics
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Analytics data for the tenant
    """
    try:
        resend_service = await get_resend_service()

        analytics_data = await resend_service.get_tenant_analytics(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )

        return {
            "success": True,
            "tenant_id": tenant_id,
            "analytics": analytics_data,
            "message": "Analytics retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


# Health and Capabilities Routes
@router.get("/health", response_model=Dict[str, Any])
async def health_check(current_user: Dict[str, Any] = Depends(get_current_user_mongo)):
    """
    Check Resend service health.

    Args:
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Health status of Resend service
    """
    try:
        resend_service = await get_resend_service()
        health_status = await resend_service.health_check()

        return {
            "service": "resend",
            "status": "healthy" if health_status.get("connected") else "unhealthy",
            "connected": health_status.get("connected", False),
            "capabilities": health_status.get("capabilities", []),
            "message": "Resend service health check completed"
        }

    except Exception as e:
        return {
            "service": "resend",
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
            "message": "Resend service health check failed"
        }


@router.get("/capabilities", response_model=Dict[str, Any])
async def get_capabilities(current_user: Dict[str, Any] = Depends(get_current_user_mongo)):
    """
    Get Resend service capabilities.

    Args:
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Available capabilities of Resend service
    """
    try:
        resend_service = await get_resend_service()
        capabilities = await resend_service.get_capabilities()

        return {
            "service": "resend",
            "capabilities": capabilities,
            "mcp_enabled": True,
            "supported_operations": [
                "send_email",
                "send_batch_emails",
                "add_domain",
                "verify_domain",
                "remove_domain",
                "add_contacts",
                "remove_contacts",
                "get_analytics"
            ],
            "message": "Resend service capabilities retrieved successfully"
        }

    except Exception as e:
        return {
            "service": "resend",
            "capabilities": [],
            "error": str(e),
            "message": "Failed to get Resend service capabilities"
        }