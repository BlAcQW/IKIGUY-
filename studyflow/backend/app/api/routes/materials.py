"""
Materials routes for StudyFlow.

Handles study material uploads and management.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, Response

from app.models.material import (
    StudyMaterial,
    MaterialCreate,
    MaterialUpdate,
    MaterialResponse,
    ProcessingStatus
)
from app.models.user import UserRole
from app.services.material_service import MaterialService
from app.services.material_processor import process_material_worker
from app.core.auth import get_current_user_with_org, OrganizationRoleChecker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/materials", tags=["Materials"])

# Only teachers and admins can upload materials
require_teacher_or_admin = OrganizationRoleChecker([UserRole.ADMIN, UserRole.TEACHER])


@router.post("/upload", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def upload_material(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    subject: str = Form(...),
    description: Optional[str] = Form(None),
    topics: Optional[str] = Form(None),  # Comma-separated
    grade: Optional[int] = Form(None),
    school_id: Optional[str] = Form(None),
    user_context: dict = Depends(require_teacher_or_admin)
):
    """
    Upload a new study material.

    Accepts PDF, DOCX, TXT, and other document types.
    Files are processed in the background for RAG indexing.

    Args:
        file: Uploaded file
        title: Material title
        subject: Subject area
        description: Material description
        topics: Comma-separated list of topics
        grade: Grade level
        school_id: School ID
        user_context: User context with organization info

    Returns:
        Created material

    Raises:
        HTTPException: If upload fails or user not authorized
    """
    try:
        # Extract user and organization info from context
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        # Read file content
        file_content = await file.read()

        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file"
            )

        # Parse topics
        topics_list = [t.strip() for t in topics.split(",")] if topics else []

        # Create material record first to get material ID
        material_data = MaterialCreate(
            organization_id=organization_id,
            school_id=school_id,
            title=title,
            description=description,
            subject=subject,
            topics=topics_list,
            grade=grade
        )

        # Generate temporary material ID for storage path
        from bson import ObjectId
        temp_material_id = str(ObjectId())

        # Save file to storage (using shared Hetzner Storage Box)
        file_path, file_size = await MaterialService.save_uploaded_file(
            file_content,
            file.filename or "untitled",
            temp_material_id,
            organization_id,
            user_id
        )

        # Create material record with storage path
        material = await MaterialService.create_material(
            material_data=material_data,
            file_name=file.filename or "untitled",
            file_path=file_path,
            file_size=file_size,
            uploaded_by=user_id
        )

        logger.info(f"Material uploaded: {material.id} by user {user_id}")

        # Trigger background processing with DocumentProcessor and RAG
        background_tasks.add_task(process_material_worker, material.id)
        logger.info(f"Background processing queued for material: {material.id}")

        return MaterialResponse(
            id=material.id,
            organization_id=material.organization_id,
            school_id=material.school_id,
            title=material.title,
            description=material.description,
            file_name=material.file_name,
            file_size=material.file_size,
            file_type=material.file_type,
            subject=material.subject,
            topics=material.topics,
            grade=material.grade,
            uploaded_by=material.uploaded_by,
            status=material.status,
            chunks_count=material.chunks_count,
            created_at=material.created_at,
            processed_at=material.processed_at
        )

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload material: {str(e)}"
        )


@router.get("/", response_model=List[MaterialResponse])
async def list_materials(
    subject: Optional[str] = None,
    grade: Optional[int] = None,
    school_id: Optional[str] = None,
    status: Optional[ProcessingStatus] = None,
    limit: int = 50,
    skip: int = 0,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    List study materials with filtering.

    Args:
        subject: Filter by subject
        grade: Filter by grade
        school_id: Filter by school
        status: Filter by processing status
        limit: Maximum materials to return
        skip: Number to skip (pagination)
        user_context: User context with organization info

    Returns:
        List of materials
    """
    # Extract organization_id from user context
    # Universal admins can see all materials (no organization filter)
    is_universal_admin = user_context.get("is_universal_admin", False)
    organization_id = None if is_universal_admin else user_context["organization_id"]

    materials = await MaterialService.list_materials(
        organization_id=organization_id,
        subject=subject,
        grade=grade,
        school_id=school_id,
        status=status,
        limit=limit,
        skip=skip
    )

    return [
        MaterialResponse(
            id=m.id,
            organization_id=m.organization_id,
            school_id=m.school_id,
            title=m.title,
            description=m.description,
            file_name=m.file_name,
            file_size=m.file_size,
            file_type=m.file_type,
            subject=m.subject,
            topics=m.topics,
            grade=m.grade,
            uploaded_by=m.uploaded_by,
            status=m.status,
            chunks_count=m.chunks_count,
            created_at=m.created_at,
            processed_at=m.processed_at
        )
        for m in materials
    ]


@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get material by ID with organization access control.

    Args:
        material_id: Material ID
        user_context: User context with organization info

    Returns:
        Material details

    Raises:
        HTTPException: If material not found or not accessible
    """
    # Universal admins can access any material (no organization filter)
    is_universal_admin = user_context.get("is_universal_admin", False)
    organization_id = None if is_universal_admin else user_context["organization_id"]

    material = await MaterialService.get_material_by_id(
        material_id,
        organization_id=organization_id
    )

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    return MaterialResponse(
        id=material.id,
        organization_id=material.organization_id,
        school_id=material.school_id,
        title=material.title,
        description=material.description,
        file_name=material.file_name,
        file_size=material.file_size,
        file_type=material.file_type,
        subject=material.subject,
        topics=material.topics,
        grade=material.grade,
        uploaded_by=material.uploaded_by,
        status=material.status,
        chunks_count=material.chunks_count,
        created_at=material.created_at,
        processed_at=material.processed_at
    )


@router.put("/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: str,
    update_data: MaterialUpdate,
    user_context: dict = Depends(require_teacher_or_admin)
):
    """
    Update material information.

    Only teachers and admins can update materials.

    Args:
        material_id: Material ID
        update_data: Fields to update
        user_context: User context with organization info

    Returns:
        Updated material

    Raises:
        HTTPException: If material not found or update fails
    """
    # Universal admins can update any material (no organization filter)
    is_universal_admin = user_context.get("is_universal_admin", False)
    organization_id = None if is_universal_admin else user_context["organization_id"]
    user_id = user_context["user_id"]

    material = await MaterialService.update_material(
        material_id,
        update_data,
        organization_id=organization_id
    )

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    logger.info(f"Material updated: {material_id} by user {user_id}")

    return MaterialResponse(
        id=material.id,
        organization_id=material.organization_id,
        school_id=material.school_id,
        title=material.title,
        description=material.description,
        file_name=material.file_name,
        file_size=material.file_size,
        file_type=material.file_type,
        subject=material.subject,
        topics=material.topics,
        grade=material.grade,
        uploaded_by=material.uploaded_by,
        status=material.status,
        chunks_count=material.chunks_count,
        created_at=material.created_at,
        processed_at=material.processed_at
    )


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(
    material_id: str,
    user_context: dict = Depends(require_teacher_or_admin)
):
    """
    Delete a material.

    Only teachers and admins can delete materials.

    Args:
        material_id: Material ID
        user_context: User context with organization info

    Raises:
        HTTPException: If material not found or deletion fails
    """
    # Universal admins can delete any material (no organization filter)
    is_universal_admin = user_context.get("is_universal_admin", False)
    organization_id = None if is_universal_admin else user_context["organization_id"]

    success = await MaterialService.delete_material(
        material_id,
        organization_id=organization_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    user_id = user_context["user_id"]
    logger.info(f"Material deleted: {material_id} by user {user_id}")
    return None


@router.get("/{material_id}/download")
async def download_material(
    material_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Download material file with organization access control.

    Uses shared storage service to serve files from Hetzner storage.

    Args:
        material_id: Material ID
        user_context: User context with organization info

    Returns:
        File response

    Raises:
        HTTPException: If material or file not found
    """
    # Universal admins can download any material (no organization filter)
    is_universal_admin = user_context.get("is_universal_admin", False)
    organization_id = None if is_universal_admin else user_context["organization_id"]
    user_id = user_context["user_id"]

    material = await MaterialService.get_material_by_id(
        material_id,
        organization_id=organization_id
    )

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    # Download file from storage (Hetzner or local fallback)
    from app.services.storage_service import get_storage_service
    storage_service = await get_storage_service()
    file_content = await storage_service.download_material_file(material.file_path)

    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    logger.info(f"Material downloaded: {material_id} by user {user_id}")

    # Determine content type
    from mimetypes import guess_type
    content_type, _ = guess_type(material.file_name)
    if not content_type:
        content_type = "application/octet-stream"

    return Response(
        content=file_content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{material.file_name}"',
            "Cache-Control": "public, max-age=3600",
        }
    )
