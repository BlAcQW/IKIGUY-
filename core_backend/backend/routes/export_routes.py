"""
Export Routes for Analytics Data

API endpoints for exporting profit margin analytics data in various formats.
Supports CSV and PDF exports with filtering options.
"""
from fastapi import APIRouter, Query, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import Optional, List
import io
import logging

from apps.core_backend.backend.auth import get_current_user_mongo
from apps.core_backend.backend.middleware.organization_context import (
    get_organization_context,
    validate_organization_access
)
from apps.core_backend.backend.mongo import get_database
from apps.shared.services.export_service import get_export_service
from apps.shared.services.pdf_report_service import get_pdf_report_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/csv")
async def export_analytics_csv(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    providers: Optional[str] = Query(None, description="Comma-separated list of providers"),
    include_summary: bool = Query(True, description="Include summary section"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Export profit margin analytics data to CSV format.

    Requires admin role. Now properly scoped to organization. Requires authentication.

    Args:
        start_date: Start date for filtering (ISO format)
        end_date: End date for filtering (ISO format)
        providers: Comma-separated list of providers to include
        include_summary: Whether to include summary statistics

    Returns:
        CSV file download
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Check admin role
        user_role = current_user.get("role", "user")
        if user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")

        logger.info(f"Exporting CSV for organization={org_id}, user={current_user.get('id')}")

        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        # Parse providers
        provider_list = None
        if providers:
            provider_list = [p.strip() for p in providers.split(",")]

        # Get export service
        db = get_database()
        export_service = get_export_service(db)

        # Generate CSV with organization scope
        csv_content = await export_service.export_to_csv(
            start_date=start_dt,
            end_date=end_dt,
            providers=provider_list,
            include_summary=include_summary,
            tenant_id=org_id  # Scope to organization
        )

        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"profit_margin_analytics_{timestamp}.csv"

        logger.info(f"CSV export successful for organization={org_id}")

        # Return as streaming response
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid date format for organization={org_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to export CSV for organization={org_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate CSV export")


@router.get("/pdf")
async def export_analytics_pdf(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    providers: Optional[str] = Query(None, description="Comma-separated list of providers"),
    include_details: bool = Query(True, description="Include detailed transactions"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Export profit margin analytics data to PDF format.

    Requires admin role. Now properly scoped to organization. Requires authentication.

    Args:
        start_date: Start date for filtering (ISO format)
        end_date: End date for filtering (ISO format)
        providers: Comma-separated list of providers to include
        include_details: Whether to include detailed transaction list

    Returns:
        PDF file download
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Check admin role
        user_role = current_user.get("role", "user")
        if user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")

        logger.info(f"Exporting PDF for organization={org_id}, user={current_user.get('id')}")

        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        # Parse providers
        provider_list = None
        if providers:
            provider_list = [p.strip() for p in providers.split(",")]

        # Get PDF service
        db = get_database()
        pdf_service = get_pdf_report_service(db)

        # Generate PDF with organization scope
        pdf_content = await pdf_service.generate_pdf_report(
            start_date=start_dt,
            end_date=end_dt,
            providers=provider_list,
            tenant_id=org_id,  # Scope to organization
            include_details=include_details
        )

        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"profit_margin_report_{timestamp}.pdf"

        logger.info(f"PDF export successful for organization={org_id}")

        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid date format for organization={org_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to export PDF for organization={org_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")


@router.get("/preview")
async def get_export_preview(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    providers: Optional[str] = Query(None, description="Comma-separated list of providers"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get a preview of what will be exported.

    Provides statistics about the data that would be exported with the given filters.

    Now properly scoped to organization. Requires authentication.

    Returns:
        JSON with preview information
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Check admin role
        user_role = current_user.get("role", "user")
        if user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")

        logger.info(f"Getting export preview for organization={org_id}, user={current_user.get('id')}")

        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        # Parse providers
        provider_list = None
        if providers:
            provider_list = [p.strip() for p in providers.split(",")]

        # Get export service
        db = get_database()
        export_service = get_export_service(db)

        # Get preview with organization scope
        preview = await export_service.get_export_preview(
            start_date=start_dt,
            end_date=end_dt,
            providers=provider_list,
            tenant_id=org_id  # Scope to organization
        )

        logger.info(f"Export preview retrieved for organization={org_id}")

        return {
            "success": True,
            "preview": preview
        }

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid date format for organization={org_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to get export preview for organization={org_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get export preview")
