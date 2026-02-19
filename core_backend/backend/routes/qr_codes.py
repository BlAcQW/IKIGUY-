"""
QR Code API endpoints.

This module provides REST API endpoints for QR code generation and management.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    File,
    UploadFile,
    Form,
    Query,
    Request
)
from fastapi.responses import Response, StreamingResponse
import io
import json

from ..mongo import get_database
from ..models.qr_code import (
    QRCodeCreate,
    QRCodeUpdate,
    QRCodeResponse,
    QRCodeListResponse
)
from ..models.shared_models import StandardResponse
from ..services.qr_code_service import QRCodeService
from ..middleware.organization_context import get_user_organization_filter
from ..auth import get_current_user_mongo
from apps.shared.services.qr_service import (
    QRCodeService as SharedQRCodeService,
    QRCodeConfig,
    LogoConfig
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qr-codes", tags=["qr_codes"])


def get_qr_service(request: Request = None) -> QRCodeService:
    """
    Dependency to get QR code service.

    Args:
        request: FastAPI request object

    Returns:
        QR code service instance
    """
    db = get_database()
    return QRCodeService(db)


def get_shared_qr_service() -> SharedQRCodeService:
    """
    Dependency to get shared QR code generation service.

    Returns:
        Shared QR code service instance
    """
    return SharedQRCodeService()


@router.post("/", response_model=StandardResponse[QRCodeResponse])
async def create_qr_code(
    name: str = Form(..., description="Display name for QR code"),
    url: str = Form(..., description="URL to encode"),
    fill_color: str = Form(default="#000000", description="Foreground color (hex)"),
    back_color: str = Form(default="#FFFFFF", description="Background color (hex)"),
    size: int = Form(default=500, ge=100, le=2000, description="Image size in pixels"),
    tags: Optional[str] = Form(default=None, description="Comma-separated tags"),
    category: Optional[str] = Form(default=None, description="Category"),
    notes: Optional[str] = Form(default=None, description="Notes"),
    logo: Optional[UploadFile] = File(default=None, description="Optional logo file"),
    request: Request = None,
    current_user: dict = Depends(get_current_user_mongo),
    qr_service: QRCodeService = Depends(get_qr_service),
    shared_qr_service: SharedQRCodeService = Depends(get_shared_qr_service)
):
    """
    Create a new QR code.

    Args:
        name: Display name
        url: URL to encode
        fill_color: Foreground color in hex
        back_color: Background color in hex
        size: Image size in pixels
        tags: Comma-separated tags
        category: Category
        notes: Notes
        logo: Optional logo file
        request: FastAPI request
        current_user: Authenticated user
        qr_service: QR code service
        shared_qr_service: Shared QR code service

    Returns:
        Created QR code response
    """
    try:
        # Get user info from authenticated user
        user_id = current_user.get("id") or current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")

        # Get organization filter
        org_id = request.headers.get('X-Organization-ID') if request else None
        org_filter = get_user_organization_filter(current_user, org_id)
        organization_id = org_filter.get("organization_id", "default")

        # Parse tags
        tag_list = [t.strip() for t in tags.split(",")] if tags else []

        # Create QR code configuration
        config = QRCodeConfig(
            name=name,
            fill_color=fill_color,
            back_color=back_color,
            size=size
        )

        # Handle logo if provided
        has_logo = False
        logo_filename = None
        if logo:
            # Read logo data
            logo_data = await logo.read()
            logo_config = LogoConfig(
                logo_data=logo_data,
                size_ratio=0.3,
                border_width=10,
                border_radius=10
            )

            # Generate QR code with logo
            result = await shared_qr_service.generate_qr_code_with_logo(
                url=url,
                config=config,
                logo_config=logo_config
            )
            has_logo = True
            logo_filename = logo.filename
        else:
            # Generate QR code without logo
            result = await shared_qr_service.generate_qr_code(
                url=url,
                config=config
            )

        # Create QR code data
        qr_data = QRCodeCreate(
            name=name,
            url=url,
            fill_color=fill_color,
            back_color=back_color,
            size=size,
            tags=tag_list,
            category=category,
            notes=notes
        )

        # Save to database
        qr_code = await qr_service.create_qr_code(
            user_id=user_id,
            organization_id=organization_id,
            data=qr_data,
            image_data=result.image_data,
            data_url=result.data_url,
            has_logo=has_logo,
            logo_filename=logo_filename
        )

        logger.info(f"Created QR code: {qr_code.id} for user: {user_id}")

        return StandardResponse(
            success=True,
            message="QR code created successfully",
            data=qr_code
        )

    except Exception as e:
        logger.error(f"Error creating QR code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=StandardResponse[QRCodeListResponse])
async def list_qr_codes(
    category: Optional[str] = Query(default=None, description="Filter by category"),
    tags: Optional[str] = Query(default=None, description="Comma-separated tags to filter"),
    search: Optional[str] = Query(default=None, description="Search in name, notes, and URL"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query(default="created_at", description="Sort field"),
    sort_order: str = Query(default="desc", description="Sort order (asc/desc)"),
    request: Request = None,
    current_user: dict = Depends(get_current_user_mongo),
    qr_service: QRCodeService = Depends(get_qr_service)
):
    """
    List QR codes with filtering and pagination.

    Args:
        category: Filter by category
        tags: Comma-separated tags
        search: Search term
        page: Page number
        page_size: Items per page
        sort_by: Sort field
        sort_order: Sort order
        request: FastAPI request
        current_user: Authenticated user
        qr_service: QR code service

    Returns:
        Paginated list of QR codes
    """
    try:
        # Get user info from authenticated user
        user_id = current_user.get("id") or current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")

        # Get organization filter
        org_id = request.headers.get('X-Organization-ID') if request else None
        org_filter = get_user_organization_filter(current_user, org_id)
        organization_id = org_filter.get("organization_id")

        # Parse tags
        tag_list = [t.strip() for t in tags.split(",")] if tags else None

        # List QR codes
        result = await qr_service.list_qr_codes(
            user_id=user_id,
            organization_id=organization_id,
            category=category,
            tags=tag_list,
            search=search,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return StandardResponse(
            success=True,
            message=f"Found {result.total} QR codes",
            data=result
        )

    except Exception as e:
        logger.error(f"Error listing QR codes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# NOTE: Static routes like /statistics/user MUST be defined BEFORE parameterized routes like /{qr_code_id}
@router.get("/statistics/user", response_model=StandardResponse[Dict[str, Any]])
async def get_user_statistics(
    request: Request = None,
    current_user: dict = Depends(get_current_user_mongo),
    qr_service: QRCodeService = Depends(get_qr_service)
):
    """
    Get statistics for the current user's QR codes.

    Args:
        request: FastAPI request
        current_user: Authenticated user
        qr_service: QR code service

    Returns:
        Statistics dictionary
    """
    try:
        # Get user info from authenticated user
        user_id = current_user.get("id") or current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")

        # Get organization filter
        org_id = request.headers.get('X-Organization-ID') if request else None
        org_filter = get_user_organization_filter(current_user, org_id)
        organization_id = org_filter.get("organization_id")

        # Get statistics
        stats = await qr_service.get_user_statistics(
            user_id=user_id,
            organization_id=organization_id
        )

        return StandardResponse(
            success=True,
            message="Statistics retrieved successfully",
            data=stats
        )

    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{qr_code_id}", response_model=StandardResponse[QRCodeResponse])
async def get_qr_code(
    qr_code_id: str,
    request: Request = None,
    current_user: dict = Depends(get_current_user_mongo),
    qr_service: QRCodeService = Depends(get_qr_service)
):
    """
    Get a QR code by ID.

    Args:
        qr_code_id: QR code ID
        request: FastAPI request
        current_user: Authenticated user
        qr_service: QR code service

    Returns:
        QR code response
    """
    try:
        # Get user info from authenticated user
        user_id = current_user.get("id") or current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")

        # Get organization filter
        org_id = request.headers.get('X-Organization-ID') if request else None
        org_filter = get_user_organization_filter(current_user, org_id)
        organization_id = org_filter.get("organization_id")

        # Get QR code
        qr_code = await qr_service.get_qr_code(
            qr_code_id=qr_code_id,
            user_id=user_id,
            organization_id=organization_id
        )

        if not qr_code:
            raise HTTPException(status_code=404, detail="QR code not found")

        return StandardResponse(
            success=True,
            message="QR code retrieved successfully",
            data=qr_code
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting QR code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{qr_code_id}", response_model=StandardResponse[QRCodeResponse])
async def update_qr_code(
    qr_code_id: str,
    data: QRCodeUpdate,
    request: Request = None,
    current_user: dict = Depends(get_current_user_mongo),
    qr_service: QRCodeService = Depends(get_qr_service)
):
    """
    Update a QR code (metadata only, not the QR image itself).

    Args:
        qr_code_id: QR code ID
        data: Update data
        request: FastAPI request
        current_user: Authenticated user
        qr_service: QR code service

    Returns:
        Updated QR code response
    """
    try:
        # Get user info from authenticated user
        user_id = current_user.get("id") or current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")

        # Get organization filter
        org_id = request.headers.get('X-Organization-ID') if request else None
        org_filter = get_user_organization_filter(current_user, org_id)
        organization_id = org_filter.get("organization_id")

        # Update QR code
        qr_code = await qr_service.update_qr_code(
            qr_code_id=qr_code_id,
            data=data,
            user_id=user_id,
            organization_id=organization_id
        )

        if not qr_code:
            raise HTTPException(status_code=404, detail="QR code not found")

        logger.info(f"Updated QR code: {qr_code_id}")

        return StandardResponse(
            success=True,
            message="QR code updated successfully",
            data=qr_code
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating QR code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{qr_code_id}", response_model=StandardResponse[Dict[str, str]])
async def delete_qr_code(
    qr_code_id: str,
    request: Request = None,
    current_user: dict = Depends(get_current_user_mongo),
    qr_service: QRCodeService = Depends(get_qr_service)
):
    """
    Delete a QR code.

    Args:
        qr_code_id: QR code ID
        request: FastAPI request
        current_user: Authenticated user
        qr_service: QR code service

    Returns:
        Success response
    """
    try:
        # Get user info from authenticated user
        user_id = current_user.get("id") or current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")

        # Get organization filter
        org_id = request.headers.get('X-Organization-ID') if request else None
        org_filter = get_user_organization_filter(current_user, org_id)
        organization_id = org_filter.get("organization_id")

        # Delete QR code
        deleted = await qr_service.delete_qr_code(
            qr_code_id=qr_code_id,
            user_id=user_id,
            organization_id=organization_id
        )

        if not deleted:
            raise HTTPException(status_code=404, detail="QR code not found")

        logger.info(f"Deleted QR code: {qr_code_id}")

        return StandardResponse(
            success=True,
            message="QR code deleted successfully",
            data={"id": qr_code_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting QR code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{qr_code_id}/download")
async def download_qr_code(
    qr_code_id: str,
    request: Request = None,
    current_user: dict = Depends(get_current_user_mongo),
    qr_service: QRCodeService = Depends(get_qr_service)
):
    """
    Download a QR code image.

    Args:
        qr_code_id: QR code ID
        request: FastAPI request
        current_user: Authenticated user
        qr_service: QR code service

    Returns:
        QR code image file
    """
    try:
        # Get user info from authenticated user
        user_id = current_user.get("id") or current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")

        # Get organization filter
        org_id = request.headers.get('X-Organization-ID') if request else None
        org_filter = get_user_organization_filter(current_user, org_id)
        organization_id = org_filter.get("organization_id")

        # Get QR code
        qr_code = await qr_service.get_qr_code(
            qr_code_id=qr_code_id,
            user_id=user_id,
            organization_id=organization_id
        )

        if not qr_code:
            raise HTTPException(status_code=404, detail="QR code not found")

        # Increment download count
        await qr_service.increment_download_count(qr_code_id)

        # Extract image data from data URL
        if not qr_code.data_url:
            raise HTTPException(status_code=500, detail="QR code image data not available")

        import base64
        # data:image/png;base64,iVBORw0KG...
        data_url_parts = qr_code.data_url.split(",", 1)
        if len(data_url_parts) != 2:
            raise HTTPException(status_code=500, detail="Invalid data URL format")

        image_data = base64.b64decode(data_url_parts[1])

        # Return image file
        filename = f"{qr_code.name.replace(' ', '_')}.{qr_code.image_format}"
        return Response(
            content=image_data,
            media_type=f"image/{qr_code.image_format}",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading QR code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-delete", response_model=StandardResponse[Dict[str, int]])
async def bulk_delete_qr_codes(
    qr_code_ids: List[str],
    request: Request = None,
    current_user: dict = Depends(get_current_user_mongo),
    qr_service: QRCodeService = Depends(get_qr_service)
):
    """
    Delete multiple QR codes.

    Args:
        qr_code_ids: List of QR code IDs
        request: FastAPI request
        current_user: Authenticated user
        qr_service: QR code service

    Returns:
        Number of deleted QR codes
    """
    try:
        # Get user info from authenticated user
        user_id = current_user.get("id") or current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")

        # Get organization filter
        org_id = request.headers.get('X-Organization-ID') if request else None
        org_filter = get_user_organization_filter(current_user, org_id)
        organization_id = org_filter.get("organization_id")

        # Bulk delete
        deleted_count = await qr_service.bulk_delete(
            qr_code_ids=qr_code_ids,
            user_id=user_id,
            organization_id=organization_id
        )

        logger.info(f"Bulk deleted {deleted_count} QR codes")

        return StandardResponse(
            success=True,
            message=f"Deleted {deleted_count} QR codes",
            data={"deleted_count": deleted_count}
        )

    except Exception as e:
        logger.error(f"Error bulk deleting QR codes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
