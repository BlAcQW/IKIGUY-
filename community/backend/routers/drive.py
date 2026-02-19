"""
Drive Router for African Language Community Platform.

Provides Google Drive-like file management API endpoints with:
- File upload, download, delete, rename
- Folder management
- Search and navigation
- Sharing and permissions
- Statistics

Uses: services/drive_service.py -> shared/storage/hetzner_storage_box.py
"""

import os
from datetime import datetime
from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
import io

from core.auth import get_current_user
from database import get_database
from services.drive_service import (
    CommunityDriveService,
    CommunityDriveError,
    FileNotFoundError as DriveFileNotFoundError,
    PermissionDeniedError,
    get_community_drive_service
)

router = APIRouter(prefix="/drive", tags=["drive"])


# ==================== PYDANTIC MODELS ====================

class DriveItemResponse(BaseModel):
    """Response model for drive items (files/folders)."""
    id: str
    name: str
    type: str  # "file" or "folder"
    path: Optional[str] = None
    parent_id: Optional[str] = None
    language_code: Optional[str] = None
    category: Optional[str] = None
    size: int = 0
    mime_type: Optional[str] = None
    description: str = ""
    tags: List[str] = []
    license: Optional[str] = None
    download_count: int = 0
    view_count: int = 0
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    owner_id: Optional[str] = None
    is_starred: bool = False
    is_public: bool = False
    is_deleted: bool = False

    class Config:
        from_attributes = True


class DriveListResponse(BaseModel):
    """Response model for listing drive items."""
    items: List[DriveItemResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


class DriveSearchResponse(BaseModel):
    """Response model for search results."""
    items: List[DriveItemResponse]
    total: int
    skip: int
    limit: int
    query: str


class BreadcrumbItem(BaseModel):
    """Breadcrumb navigation item."""
    id: Optional[str]
    name: str


class DriveStatsResponse(BaseModel):
    """Response model for storage statistics."""
    total_files: int
    total_size_bytes: int
    total_size_mb: float
    total_downloads: int
    by_category: dict


class FolderCreateRequest(BaseModel):
    """Request model for creating a folder."""
    name: str = Field(..., min_length=1, max_length=255)
    language_code: str
    category: str = "resource"
    parent_id: Optional[str] = None
    description: str = ""


class FileRenameRequest(BaseModel):
    """Request model for renaming a file."""
    new_name: str = Field(..., min_length=1, max_length=255)


# ==================== DEPENDENCY ====================

async def get_drive_service(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> CommunityDriveService:
    """Get drive service dependency."""
    return await get_community_drive_service(db)


# ==================== FILE ENDPOINTS ====================

@router.post("/upload", response_model=DriveItemResponse)
async def upload_file(
    file: UploadFile = File(...),
    language_code: str = Form(...),
    category: str = Form("resource"),
    description: str = Form(""),
    tags: Optional[str] = Form(None),
    license: str = Form("CC-BY-4.0"),
    parent_id: Optional[str] = Form(None),
    drive_service: CommunityDriveService = Depends(get_drive_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a file to the community drive.

    Args:
        file: File to upload
        language_code: Language code for organization
        category: File category (audio, text, model, notebook, resource)
        description: File description
        tags: Comma-separated tags
        license: File license (default: CC-BY-4.0)
        parent_id: Parent folder ID (optional)
        drive_service: Drive service
        current_user: Authenticated user

    Returns:
        DriveItemResponse: Uploaded file metadata
    """
    try:
        # Read file content
        file_content = await file.read()

        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []

        # Upload file
        result = await drive_service.upload_file(
            file_content=file_content,
            filename=file.filename,
            owner_id=current_user["id"],
            language_code=language_code,
            category=category,
            description=description,
            tags=tag_list,
            parent_id=parent_id,
            license=license
        )

        return DriveItemResponse(**result)

    except CommunityDriveError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/files/{file_id}", response_model=DriveItemResponse)
async def get_file_info(
    file_id: str,
    drive_service: CommunityDriveService = Depends(get_drive_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Get file information and metadata.

    Args:
        file_id: File ID
        drive_service: Drive service
        current_user: Authenticated user

    Returns:
        DriveItemResponse: File metadata
    """
    try:
        result = await drive_service.get_file_info(
            file_id=file_id,
            user_id=current_user["id"],
            increment_views=True
        )
        return DriveItemResponse(**result)

    except DriveFileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: str,
    drive_service: CommunityDriveService = Depends(get_drive_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Download a file.

    Args:
        file_id: File ID
        drive_service: Drive service
        current_user: Authenticated user

    Returns:
        StreamingResponse: File content
    """
    try:
        content, filename, mime_type = await drive_service.download_file(
            file_id=file_id,
            user_id=current_user["id"]
        )

        return StreamingResponse(
            io.BytesIO(content),
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(content))
            }
        )

    except DriveFileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    permanent: bool = Query(False, description="Permanently delete"),
    drive_service: CommunityDriveService = Depends(get_drive_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a file (move to trash or permanent delete).

    Args:
        file_id: File ID
        permanent: If True, permanently delete
        drive_service: Drive service
        current_user: Authenticated user

    Returns:
        dict: Deletion status
    """
    try:
        result = await drive_service.delete_file(
            file_id=file_id,
            user_id=current_user["id"],
            permanent=permanent
        )
        return result

    except DriveFileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )


@router.patch("/files/{file_id}/rename")
async def rename_file(
    file_id: str,
    request: FileRenameRequest,
    drive_service: CommunityDriveService = Depends(get_drive_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Rename a file.

    Args:
        file_id: File ID
        request: Rename request with new name
        drive_service: Drive service
        current_user: Authenticated user

    Returns:
        DriveItemResponse: Updated file metadata
    """
    try:
        result = await drive_service.rename_file(
            file_id=file_id,
            new_name=request.new_name,
            user_id=current_user["id"]
        )
        return DriveItemResponse(**result)

    except DriveFileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )


@router.post("/files/{file_id}/star")
async def toggle_star(
    file_id: str,
    drive_service: CommunityDriveService = Depends(get_drive_service),
    current_user: dict = Depends(get_current_user),
):
    """Toggle star status of a file."""
    try:
        result = await drive_service.toggle_star(
            file_id=file_id,
            user_id=current_user["id"]
        )
        return DriveItemResponse(**result)

    except DriveFileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )


@router.post("/files/{file_id}/public")
async def toggle_public(
    file_id: str,
    drive_service: CommunityDriveService = Depends(get_drive_service),
    current_user: dict = Depends(get_current_user),
):
    """Toggle public visibility of a file."""
    try:
        result = await drive_service.toggle_public(
            file_id=file_id,
            user_id=current_user["id"]
        )
        return DriveItemResponse(**result)

    except DriveFileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )


# ==================== FOLDER ENDPOINTS ====================

@router.post("/folders", response_model=DriveItemResponse)
async def create_folder(
    request: FolderCreateRequest,
    drive_service: CommunityDriveService = Depends(get_drive_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new folder.

    Args:
        request: Folder creation request
        drive_service: Drive service
        current_user: Authenticated user

    Returns:
        DriveItemResponse: Created folder metadata
    """
    try:
        result = await drive_service.create_folder(
            name=request.name,
            owner_id=current_user["id"],
            language_code=request.language_code,
            category=request.category,
            parent_id=request.parent_id,
            description=request.description
        )
        return DriveItemResponse(**result)

    except DriveFileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent folder not found"
        )
    except CommunityDriveError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/folders", response_model=DriveListResponse)
async def list_folder_contents(
    folder_id: Optional[str] = Query(None, description="Folder ID (None for root)"),
    language_code: Optional[str] = Query(None, description="Filter by language"),
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    sort_by: str = Query("name", description="Sort field"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    drive_service: CommunityDriveService = Depends(get_drive_service),
    current_user: dict = Depends(get_current_user),
):
    """
    List folder contents.

    Args:
        folder_id: Folder ID (None for root)
        language_code: Filter by language
        category: Filter by category
        skip: Pagination skip
        limit: Pagination limit
        sort_by: Sort field
        sort_order: Sort order
        drive_service: Drive service
        current_user: Authenticated user

    Returns:
        DriveListResponse: List of items with pagination
    """
    result = await drive_service.get_folder_contents(
        folder_id=folder_id,
        user_id=current_user["id"],
        language_code=language_code,
        category=category,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return DriveListResponse(**result)


@router.get("/breadcrumbs", response_model=List[BreadcrumbItem])
async def get_breadcrumbs(
    folder_id: Optional[str] = Query(None, description="Current folder ID"),
    language_code: Optional[str] = Query(None, description="Language context"),
    drive_service: CommunityDriveService = Depends(get_drive_service),
):
    """
    Get breadcrumb navigation trail.

    Args:
        folder_id: Current folder ID
        language_code: Language context
        drive_service: Drive service

    Returns:
        List[BreadcrumbItem]: Breadcrumb trail
    """
    result = await drive_service.get_breadcrumbs(
        folder_id=folder_id,
        language_code=language_code
    )
    return [BreadcrumbItem(**item) for item in result]


# ==================== SEARCH ENDPOINTS ====================

@router.get("/search", response_model=DriveSearchResponse)
async def search_files(
    q: str = Query(..., min_length=1, description="Search query"),
    language_code: Optional[str] = Query(None, description="Filter by language"),
    category: Optional[str] = Query(None, description="Filter by category"),
    file_type: Optional[str] = Query(None, description="Filter by type (file/folder)"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    drive_service: CommunityDriveService = Depends(get_drive_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Search files and folders.

    Args:
        q: Search query
        language_code: Filter by language
        category: Filter by category
        file_type: Filter by type
        tags: Filter by tags
        skip: Pagination skip
        limit: Pagination limit
        drive_service: Drive service
        current_user: Authenticated user

    Returns:
        DriveSearchResponse: Search results
    """
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else None

    result = await drive_service.search_files(
        query=q,
        user_id=current_user["id"],
        language_code=language_code,
        category=category,
        file_type=file_type,
        tags=tag_list,
        skip=skip,
        limit=limit
    )

    return DriveSearchResponse(**result)


# ==================== USER-SPECIFIC ENDPOINTS ====================

@router.get("/my-files", response_model=DriveListResponse)
async def get_my_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    drive_service: CommunityDriveService = Depends(get_drive_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Get current user's files.

    Returns:
        DriveListResponse: User's files with pagination
    """
    result = await drive_service.get_user_files(
        user_id=current_user["id"],
        skip=skip,
        limit=limit
    )
    return DriveListResponse(**result)


@router.get("/recent", response_model=List[DriveItemResponse])
async def get_recent_files(
    limit: int = Query(20, ge=1, le=100),
    drive_service: CommunityDriveService = Depends(get_drive_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Get recently accessed files.

    Returns:
        List[DriveItemResponse]: Recent files
    """
    result = await drive_service.get_recent_files(
        user_id=current_user["id"],
        limit=limit
    )
    return [DriveItemResponse(**item) for item in result]


# ==================== LANGUAGE-SPECIFIC ENDPOINTS ====================

@router.get("/languages/{language_code}/files", response_model=List[DriveItemResponse])
async def get_language_files(
    language_code: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=200),
    drive_service: CommunityDriveService = Depends(get_drive_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Get files for a specific language.

    Args:
        language_code: Language code
        category: Filter by category
        limit: Max files to return

    Returns:
        List[DriveItemResponse]: Files for the language
    """
    result = await drive_service.get_files_by_language(
        language_code=language_code,
        user_id=current_user["id"],
        category=category,
        limit=limit
    )
    return [DriveItemResponse(**item) for item in result]


# ==================== STATISTICS ENDPOINTS ====================

@router.get("/stats", response_model=DriveStatsResponse)
async def get_storage_stats(
    language_code: Optional[str] = Query(None, description="Filter by language"),
    drive_service: CommunityDriveService = Depends(get_drive_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Get storage statistics.

    Args:
        language_code: Filter by language (optional)

    Returns:
        DriveStatsResponse: Storage statistics
    """
    result = await drive_service.get_storage_stats(
        user_id=current_user["id"],
        language_code=language_code
    )
    return DriveStatsResponse(**result)


@router.get("/stats/global", response_model=DriveStatsResponse)
async def get_global_stats(
    language_code: Optional[str] = Query(None, description="Filter by language"),
    drive_service: CommunityDriveService = Depends(get_drive_service),
):
    """
    Get global storage statistics (public endpoint).

    Returns:
        DriveStatsResponse: Global storage statistics
    """
    result = await drive_service.get_storage_stats(
        language_code=language_code
    )
    return DriveStatsResponse(**result)
