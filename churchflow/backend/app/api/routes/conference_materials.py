"""
Conference Materials API Routes.

Handles file upload, download, and management of conference materials.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from typing import Optional, List
from pydantic import BaseModel, Field
import os

from app.api.dependencies import get_current_user_profile, require_roles
from app.models.user import User
from app.services.conference_material_service import conference_material_service
from fastapi import Request

router = APIRouter()


# Helper to get optional current user
def get_optional_current_user(request: Request) -> Optional[User]:
    """Get current user if authenticated, else None."""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        # Try to get user, but don't fail if not authenticated
        from app.api.dependencies import get_current_user
        return get_current_user(request)
    except:
        return None


# Request/Response Models

class MaterialUpdateRequest(BaseModel):
    """Request model for updating material metadata."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    material_type: Optional[str] = Field(None, pattern="^(brochure|schedule|map|form|flyer|guide|other)$")
    is_public: Optional[bool] = None
    display_on_landing: Optional[bool] = None
    display_order: Optional[int] = Field(None, ge=0)


# Endpoints

@router.post("/conferences/{conference_id}/materials", status_code=status.HTTP_201_CREATED)
async def upload_material(
    conference_id: str,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    material_type: str = Form("other"),
    is_public: bool = Form(True),
    display_on_landing: bool = Form(False),
    display_order: int = Form(0),
    current_user: User = Depends(require_roles("admin", "coordinator"))
):
    """
    Upload a conference material.

    **Required Role**: admin or coordinator

    **Form Data**:
    - file: File to upload (PDF, DOC, XLSX, images, etc.)
    - title: Material title
    - description: Optional description
    - material_type: Type (brochure, schedule, map, form, flyer, guide, other)
    - is_public: Whether publicly accessible (default: True)
    - display_on_landing: Show on landing page (default: False)
    - display_order: Display order (default: 0)

    **Returns**: Uploaded material information
    """
    try:
        # Get organization ID
        organization_id = str(current_user.branch_id) if current_user.branch_id else "default"

        # Upload material
        material = await conference_material_service.upload_material(
            file=file,
            conference_id=conference_id,
            organization_id=organization_id,
            title=title,
            uploaded_by_user_id=str(current_user.id),
            description=description,
            material_type=material_type,
            is_public=is_public,
            display_on_landing=display_on_landing,
            display_order=display_order
        )

        return {
            "id": str(material.id),
            "title": material.title,
            "file_name": material.file_name,
            "file_size": material.file_size,
            "file_type": material.file_type,
            "material_type": material.material_type,
            "is_public": material.is_public,
            "display_on_landing": material.display_on_landing,
            "message": "Material uploaded successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload material: {str(e)}"
        )


@router.get("/conferences/{conference_id}/materials")
async def list_conference_materials(
    conference_id: str,
    public_only: bool = Query(False, description="Only public materials"),
    landing_page_only: bool = Query(False, description="Only landing page materials"),
    request: Request = None
):
    """
    List materials for a conference.

    **Query Parameters**:
    - public_only: Only return public materials
    - landing_page_only: Only return materials for landing page

    **Returns**: List of conference materials
    """
    try:
        # If not authenticated, only show public materials (force to true for public endpoints)
        public_only = True

        materials = await conference_material_service.get_conference_materials(
            conference_id=conference_id,
            public_only=public_only,
            landing_page_only=landing_page_only
        )

        materials_list = [
            {
                "id": str(material.id),
                "title": material.title,
                "description": material.description,
                "file_name": material.file_name,
                "file_size": material.file_size,
                "file_type": material.file_type,
                "material_type": material.material_type,
                "is_public": material.is_public,
                "display_on_landing": material.display_on_landing,
                "display_order": material.display_order,
                "created_at": material.created_at.isoformat(),
                "download_url": f"/api/v1/conference-materials/{material.id}/download"
            }
            for material in materials
        ]

        return {
            "materials": materials_list,
            "total": len(materials_list)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list materials: {str(e)}"
        )


@router.get("/conference-materials/{material_id}")
async def get_material(
    material_id: str,
    request: Request = None
):
    """
    Get material details.

    **Returns**: Material information
    """
    try:
        # Check if user is authenticated
        try:
            current_user = await get_current_user_profile(request) if request else None
        except:
            current_user = None

        material = await conference_material_service.get_material(material_id)

        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material not found"
            )

        # Check if user has access
        if not material.is_public and not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        return {
            "id": str(material.id),
            "conference_id": str(material.conference_id),
            "title": material.title,
            "description": material.description,
            "file_name": material.file_name,
            "file_size": material.file_size,
            "file_type": material.file_type,
            "material_type": material.material_type,
            "is_public": material.is_public,
            "display_on_landing": material.display_on_landing,
            "display_order": material.display_order,
            "created_at": material.created_at.isoformat(),
            "updated_at": material.updated_at.isoformat(),
            "download_url": f"/api/v1/conference-materials/{material.id}/download"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get material: {str(e)}"
        )


@router.api_route("/conference-materials/{material_id}/download", methods=["GET", "HEAD"])
async def download_material(
    material_id: str,
    request: Request = None
):
    """
    Download a material file.

    Supports both GET (download) and HEAD (check existence) requests.

    **Returns**: File download
    """
    try:
        material = await conference_material_service.get_material(material_id)

        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material not found"
            )

        # Only allow download of public materials without authentication
        if not material.is_public:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for private materials"
            )

        # Get file path
        file_path = conference_material_service.get_file_path(material)

        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on server"
            )

        return FileResponse(
            path=file_path,
            filename=material.file_name,
            media_type=material.file_type
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download material: {str(e)}"
        )


@router.put("/conference-materials/{material_id}")
async def update_material(
    material_id: str,
    request: MaterialUpdateRequest,
    current_user: User = Depends(require_roles("admin", "coordinator"))
):
    """
    Update material metadata.

    **Required Role**: admin or coordinator

    **Returns**: Updated material information
    """
    try:
        # Build updates dict
        updates = {}
        if request.title is not None:
            updates["title"] = request.title
        if request.description is not None:
            updates["description"] = request.description
        if request.material_type is not None:
            updates["material_type"] = request.material_type
        if request.is_public is not None:
            updates["is_public"] = request.is_public
        if request.display_on_landing is not None:
            updates["display_on_landing"] = request.display_on_landing
        if request.display_order is not None:
            updates["display_order"] = request.display_order

        if not updates:
            raise ValueError("No fields to update")

        material = await conference_material_service.update_material(
            material_id=material_id,
            updates=updates
        )

        return {
            "id": str(material.id),
            "title": material.title,
            "description": material.description,
            "material_type": material.material_type,
            "is_public": material.is_public,
            "display_on_landing": material.display_on_landing,
            "display_order": material.display_order,
            "message": "Material updated successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update material: {str(e)}"
        )


@router.delete("/conference-materials/{material_id}")
async def delete_material(
    material_id: str,
    current_user: User = Depends(require_roles("admin", "coordinator"))
):
    """
    Delete a material.

    **Required Role**: admin or coordinator

    **Returns**: Success message
    """
    try:
        await conference_material_service.delete_material(material_id)

        return {
            "message": "Material deleted successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete material: {str(e)}"
        )
