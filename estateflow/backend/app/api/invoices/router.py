"""
Invoice API endpoints for EstateFlow.

Provides invoice management, payment tracking, and statistics.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from io import BytesIO
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.auth import get_organization_context
from app.models.invoice import (
    Invoice,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceMarkPaid,
    InvoiceFilters,
    InvoiceListResponse,
    InvoiceStats,
)
from app.services.invoice_service import InvoiceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/invoices", tags=["invoices"])


def get_invoice_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> InvoiceService:
    """
    Dependency to get invoice service.

    Args:
        db: Database instance

    Returns:
        InvoiceService instance
    """
    return InvoiceService(db)


@router.post("", response_model=Invoice, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    org_context: Dict[str, str] = Depends(get_organization_context),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """
    Create a new invoice.

    Args:
        invoice_data: Invoice creation data
        org_context: Organization context
        invoice_service: Invoice service

    Returns:
        Created invoice

    Raises:
        HTTPException: If creation fails
    """
    try:
        invoice = await invoice_service.create_invoice(
            organization_id=org_context["organization_id"],
            user_id=org_context["user_id"],
            invoice_data=invoice_data
        )
        return invoice
    except ValueError as e:
        logger.error(f"Invalid invoice data: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating invoice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invoice"
        )


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    status_filter: str = None,
    contact_id: str = None,
    property_id: str = None,
    search: str = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    org_context: Dict[str, str] = Depends(get_organization_context),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """
    List invoices with filters.

    Args:
        status_filter: Comma-separated status values
        contact_id: Filter by contact
        property_id: Filter by property
        search: Search invoice number or contact name
        limit: Page size
        offset: Page offset
        sort_by: Sort field
        sort_order: Sort order
        org_context: Organization context
        invoice_service: Invoice service

    Returns:
        Invoice list response
    """
    try:
        # Parse status filter
        status_list = None
        if status_filter:
            from app.models.invoice import InvoiceStatus
            status_list = [InvoiceStatus(s.strip()) for s in status_filter.split(",")]

        # Build filters
        filters = InvoiceFilters(
            status=status_list,
            contact_id=contact_id,
            property_id=property_id,
            search=search,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )

        response = await invoice_service.list_invoices(
            organization_id=org_context["organization_id"],
            filters=filters
        )
        return response
    except Exception as e:
        logger.error(f"Error listing invoices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list invoices"
        )


@router.get("/stats", response_model=InvoiceStats)
async def get_invoice_stats(
    currency: str = "GHS",
    org_context: Dict[str, str] = Depends(get_organization_context),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """
    Get invoice statistics.

    Args:
        currency: Currency filter
        org_context: Organization context
        invoice_service: Invoice service

    Returns:
        Invoice statistics
    """
    try:
        stats = await invoice_service.get_stats(
            organization_id=org_context["organization_id"],
            currency=currency
        )
        return stats
    except Exception as e:
        logger.error(f"Error getting invoice stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get invoice statistics"
        )


@router.get("/{invoice_id}", response_model=Invoice)
async def get_invoice(
    invoice_id: str,
    org_context: Dict[str, str] = Depends(get_organization_context),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """
    Get invoice by ID.

    Args:
        invoice_id: Invoice ID
        org_context: Organization context
        invoice_service: Invoice service

    Returns:
        Invoice

    Raises:
        HTTPException: If invoice not found
    """
    invoice = await invoice_service.get_invoice(
        invoice_id=invoice_id,
        organization_id=org_context["organization_id"]
    )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found"
        )

    return invoice


@router.put("/{invoice_id}", response_model=Invoice)
async def update_invoice(
    invoice_id: str,
    updates: InvoiceUpdate,
    org_context: Dict[str, str] = Depends(get_organization_context),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """
    Update an invoice.

    Args:
        invoice_id: Invoice ID
        updates: Update data
        org_context: Organization context
        invoice_service: Invoice service

    Returns:
        Updated invoice

    Raises:
        HTTPException: If invoice not found or update fails
    """
    try:
        invoice = await invoice_service.update_invoice(
            invoice_id=invoice_id,
            organization_id=org_context["organization_id"],
            updates=updates
        )

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice {invoice_id} not found"
            )

        return invoice
    except ValueError as e:
        logger.error(f"Invalid update: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating invoice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update invoice"
        )


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: str,
    org_context: Dict[str, str] = Depends(get_organization_context),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """
    Delete an invoice (soft delete).

    Args:
        invoice_id: Invoice ID
        org_context: Organization context
        invoice_service: Invoice service

    Raises:
        HTTPException: If invoice not found or deletion fails
    """
    try:
        deleted = await invoice_service.delete_invoice(
            invoice_id=invoice_id,
            organization_id=org_context["organization_id"]
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice {invoice_id} not found"
            )
    except ValueError as e:
        logger.error(f"Cannot delete invoice: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting invoice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete invoice"
        )


@router.post("/{invoice_id}/mark-paid", response_model=Invoice)
async def mark_invoice_paid(
    invoice_id: str,
    payment_data: InvoiceMarkPaid,
    org_context: Dict[str, str] = Depends(get_organization_context),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """
    Mark invoice as paid.

    Args:
        invoice_id: Invoice ID
        payment_data: Payment information
        org_context: Organization context
        invoice_service: Invoice service

    Returns:
        Updated invoice

    Raises:
        HTTPException: If invoice not found
    """
    try:
        invoice = await invoice_service.mark_paid(
            invoice_id=invoice_id,
            organization_id=org_context["organization_id"],
            payment_data=payment_data
        )

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice {invoice_id} not found"
            )

        return invoice
    except Exception as e:
        logger.error(f"Error marking invoice as paid: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark invoice as paid"
        )


@router.post("/{invoice_id}/send")
async def send_invoice(
    invoice_id: str,
    org_context: Dict[str, str] = Depends(get_organization_context),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """
    Send invoice via email to customer with PDF attachment.

    Args:
        invoice_id: Invoice ID
        org_context: Organization context
        invoice_service: Invoice service

    Returns:
        Success message with send details

    Raises:
        HTTPException: If invoice not found or send fails
    """
    try:
        # Send invoice via email
        result = await invoice_service.send_invoice(
            invoice_id=invoice_id,
            organization_id=org_context["organization_id"]
        )

        if result.get("success"):
            return {
                "success": True,
                "message": f"Invoice sent successfully to customer",
                "invoice_id": invoice_id,
                "recipient": result.get("to"),
                "provider": result.get("provider")
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send invoice: {result.get('error')}"
            )

    except ValueError as e:
        logger.error(f"Invalid send request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error sending invoice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send invoice"
        )


@router.get("/{invoice_id}/download/pdf")
async def download_invoice_pdf(
    invoice_id: str,
    org_context: Dict[str, str] = Depends(get_organization_context),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """
    Download invoice as PDF.

    Args:
        invoice_id: Invoice ID
        org_context: Organization context
        invoice_service: Invoice service

    Returns:
        PDF file

    Raises:
        HTTPException: If invoice not found or PDF generation fails
    """
    try:
        # Generate PDF
        pdf_bytes = await invoice_service.generate_pdf(
            invoice_id=invoice_id,
            organization_id=org_context["organization_id"]
        )

        # Get invoice for filename
        invoice = await invoice_service.get_invoice(
            invoice_id=invoice_id,
            organization_id=org_context["organization_id"]
        )

        # Create streaming response
        pdf_stream = BytesIO(pdf_bytes)
        filename = f"{invoice.invoice_number}.pdf"

        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except ValueError as e:
        logger.error(f"Invoice not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF"
        )
