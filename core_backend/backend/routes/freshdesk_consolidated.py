"""
Consolidated Freshdesk Routes
Uses the unified Freshdesk service for all helpdesk operations.
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
import json
from datetime import datetime
import logging

from ..auth import get_current_user_mongo
from ..services.freshdesk_consolidated_service import freshdesk_consolidated_service
from apps.shared.integration.freshdesk import FreshdeskTicket, FreshdeskContact

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/freshdesk-consolidated", tags=["Freshdesk Consolidated"])

# Request models that extend the shared models
class FreshdeskTicketCreateRequest(BaseModel):
    """Request model for creating Freshdesk tickets."""
    subject: str = Field(..., description="Ticket subject")
    description: str = Field(..., description="Ticket description")
    requester_email: str = Field(..., description="Requester email")
    requester_name: Optional[str] = Field(None, description="Requester name")
    priority: int = Field(1, description="Priority level (1-4)")
    status: int = Field(2, description="Ticket status")
    source: int = Field(7, description="Ticket source")
    type: Optional[str] = Field("Question", description="Ticket type")
    tags: List[str] = Field([], description="Ticket tags")
    custom_fields: Dict[str, Any] = Field({}, description="Custom fields")
    tenant_id: str = Field("default", description="Tenant identifier")


class FreshdeskContactCreateRequest(BaseModel):
    """Request model for creating Freshdesk contacts."""
    name: str = Field(..., description="Contact name")
    email: str = Field(..., description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    company_id: Optional[int] = Field(None, description="Company ID")
    description: Optional[str] = Field(None, description="Contact description")
    tenant_id: str = Field("default", description="Tenant identifier")


@router.post("/tickets", response_model=Dict[str, Any])
async def create_freshdesk_ticket(
    ticket_request: FreshdeskTicketCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Create a new Freshdesk ticket using the consolidated service.

    This endpoint delegates to the unified Freshdesk service for:
    - Ticket creation and assignment
    - Contact management
    - Webhook setup
    """
    try:
        # Convert request to FreshdeskTicket model
        ticket = FreshdeskTicket(
            subject=ticket_request.subject,
            description=ticket_request.description,
            email=ticket_request.requester_email,
            priority=ticket_request.priority,
            status=ticket_request.status,
            source=ticket_request.source,
            type=ticket_request.type,
            tags=ticket_request.tags,
            custom_fields=ticket_request.custom_fields
        )

        # Use tenant-specific ticket creation
        result = await freshdesk_consolidated_service.create_tenant_ticket(
            tenant_id=ticket_request.tenant_id,
            ticket=ticket,
            context={
                "created_by": current_user.get("user_id"),
                "created_at": datetime.now().isoformat()
            }
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return {
            "success": True,
            "ticket": result,
            "message": "Freshdesk ticket created successfully via consolidated service"
        }

    except Exception as e:
        logger.error(f"Error creating Freshdesk ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tickets", response_model=Dict[str, Any])
async def list_freshdesk_tickets(
    tenant_id: str = "default",
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    List Freshdesk tickets for a tenant using the consolidated service.
    """
    try:
        filters = {}
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority

        result = await freshdesk_consolidated_service.get_tenant_tickets(
            tenant_id=tenant_id,
            filters=filters,
            limit=limit,
            offset=offset
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result

    except Exception as e:
        logger.error(f"Error listing Freshdesk tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tickets/{ticket_id}", response_model=Dict[str, Any])
async def get_freshdesk_ticket(
    ticket_id: int,
    tenant_id: str = "default",
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get a specific Freshdesk ticket using the consolidated service.
    """
    try:
        result = await freshdesk_consolidated_service.get_ticket(ticket_id)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        # Add tenant info
        result["tenant_id"] = tenant_id
        return result

    except Exception as e:
        logger.error(f"Error getting Freshdesk ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tickets/{ticket_id}", response_model=Dict[str, Any])
async def update_freshdesk_ticket(
    ticket_id: int,
    update_data: Dict[str, Any],
    tenant_id: str = "default",
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Update a Freshdesk ticket using the consolidated service.
    """
    try:
        result = await freshdesk_consolidated_service.update_ticket(ticket_id, update_data)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        # Add tenant info
        result["tenant_id"] = tenant_id
        return result

    except Exception as e:
        logger.error(f"Error updating Freshdesk ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contacts", response_model=Dict[str, Any])
async def create_freshdesk_contact(
    contact_request: FreshdeskContactCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Create a new Freshdesk contact using the consolidated service.
    """
    try:
        # Convert request to FreshdeskContact model
        contact = FreshdeskContact(
            name=contact_request.name,
            email=contact_request.email,
            phone=contact_request.phone,
            company_id=contact_request.company_id,
            description=contact_request.description
        )

        result = await freshdesk_consolidated_service.create_contact(contact)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        # Add tenant info
        result["tenant_id"] = contact_request.tenant_id
        return {
            "success": True,
            "contact": result,
            "message": "Freshdesk contact created successfully via consolidated service"
        }

    except Exception as e:
        logger.error(f"Error creating Freshdesk contact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhooks/{tenant_id}", response_model=Dict[str, Any])
async def handle_freshdesk_webhook(
    tenant_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle Freshdesk webhooks using the consolidated service.
    """
    try:
        # Get raw body for webhook processing
        body = await request.body()
        headers = dict(request.headers)

        # Parse webhook event
        webhook_data = json.loads(body.decode())

        # Process webhook through consolidated service
        result = await freshdesk_consolidated_service.handle_tenant_webhook(
            tenant_id=tenant_id,
            webhook_data=webhook_data,
            context={
                "headers": headers,
                "received_at": datetime.now().isoformat()
            }
        )

        if not result.get("success"):
            logger.error(f"Webhook processing failed: {result.get('error')}")
            return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        logger.error(f"Error handling Freshdesk webhook: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.get("/analytics/{tenant_id}", response_model=Dict[str, Any])
async def get_freshdesk_analytics(
    tenant_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get Freshdesk analytics for a tenant using the consolidated service.
    """
    try:
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        result = await freshdesk_consolidated_service.get_tenant_analytics(
            tenant_id=tenant_id,
            start_date=start_dt,
            end_date=end_dt
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result

    except Exception as e:
        logger.error(f"Error getting Freshdesk analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities", response_model=Dict[str, Any])
async def get_freshdesk_capabilities():
    """
    Get Freshdesk service capabilities.
    """
    try:
        capabilities = freshdesk_consolidated_service.get_extended_capabilities()
        return {
            "success": True,
            "capabilities": capabilities,
            "service_version": "consolidated",
            "consolidation_status": "active"
        }

    except Exception as e:
        logger.error(f"Error getting Freshdesk capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=Dict[str, Any])
async def freshdesk_health_check():
    """
    Health check for the consolidated Freshdesk service.
    """
    try:
        # health_check is async in the shared integration
        result = await freshdesk_consolidated_service.health_check()

        # Wrap synchronous result in async-compatible format
        if isinstance(result, dict):
            return {
                "success": True,
                "service": "freshdesk_consolidated",
                "status": "healthy" if result.get("status") == "healthy" else "degraded",
                "connection_test": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "service": "freshdesk_consolidated",
                "status": "healthy",
                "connection_test": {"status": "ok"},
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Freshdesk health check failed: {e}")
        return {
            "success": False,
            "service": "freshdesk_consolidated",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }