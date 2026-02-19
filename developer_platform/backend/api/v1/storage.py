"""
Storage API routes for Developer Platform.

Provides organization-scoped file storage using Hetzner Storage Box.
All files are isolated by organization ID for security.
"""

import logging
import os
import tempfile
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
import sys

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from apps.shared.storage.hetzner_storage_box import (
    get_storage,
    HetznerStorageBox,
    HetznerStorageBoxError,
    StorageProtocol
)
from ...middleware.api_key_auth import verify_api_key
from ...middleware.rate_limiter import get_rate_limit_dependency

router = APIRouter(prefix="/api/v1/storage", tags=["Storage"])
logger = logging.getLogger(__name__)


class FileMetadata(BaseModel):
    """File metadata model."""
    name: str
    path: str
    is_directory: bool
    size: int
    modified: Optional[str] = None


class FileListResponse(BaseModel):
    """Response model for file listing."""
    organization_id: str
    path: str
    files: List[FileMetadata]
    total: int


class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    success: bool
    filename: str
    path: str
    size: int
    url: str


class FileDeleteResponse(BaseModel):
    """Response model for file deletion."""
    success: bool
    path: str
    message: str


def get_org_base_path(organization_id: str) -> str:
    """
    Get organization-specific base path.

    Args:
        organization_id: Organization/tenant ID

    Returns:
        Base path for organization
    """
    return f"kasaai/organizations/{organization_id}"


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    summary="Upload file",
    description="""
    Upload a file to organization-scoped storage.

    All files are stored in: `/kasaai/organizations/{organization_id}/{path}`

    **Rate Limit**: 10 uploads per minute (Free tier)

    **Max File Size**: 100MB
    """
)
async def upload_file(
    file: UploadFile = File(..., description="File to upload"),
    path: str = Query(..., description="Remote path (e.g., 'documents/report.pdf')"),
    overwrite: bool = Query(False, description="Whether to overwrite existing file"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """
    Upload file to organization storage.

    Args:
        file: File to upload
        path: Remote path within organization storage
        overwrite: Whether to overwrite existing file
        api_key: API key info (from middleware)

    Returns:
        Upload confirmation with file details
    """
    try:
        organization_id = api_key.get("tenant_id")

        # Validate file size (100MB max)
        MAX_SIZE = 100 * 1024 * 1024  # 100MB
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to start

        if file_size > MAX_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: 100MB. Your file: {file_size / (1024*1024):.1f}MB"
            )

        # Get storage with organization base path
        storage = await get_storage(
            protocol=StorageProtocol.WEBDAV,
            base_path=get_org_base_path(organization_id)
        )

        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Upload to storage
            await storage.upload_file(
                local_path=tmp_path,
                remote_path=path,
                overwrite=overwrite
            )

            # Get file info
            file_info = await storage.get_file_info(path)

            # Generate URL
            file_url = f"https://{storage.host}/{storage.base_path}/{path}"

            return {
                "success": True,
                "filename": file.filename,
                "path": path,
                "size": file_info.get("size", file_size),
                "url": file_url
            }

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except HetznerStorageBoxError as e:
        logger.error(f"Storage error: {e}")
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get(
    "/download/{file_path:path}",
    summary="Download file",
    description="""
    Download a file from organization storage.

    **Rate Limit**: 20 downloads per minute (Free tier)
    """
)
async def download_file(
    file_path: str,
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """
    Download file from organization storage.

    Args:
        file_path: File path within organization storage
        api_key: API key info (from middleware)

    Returns:
        File download stream
    """
    try:
        organization_id = api_key.get("tenant_id")

        # Get storage
        storage = await get_storage(
            protocol=StorageProtocol.WEBDAV,
            base_path=get_org_base_path(organization_id)
        )

        # Check if file exists
        if not await storage.file_exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Download to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_path)[1]) as tmp:
            tmp_path = tmp.name

        try:
            await storage.download_file(
                remote_path=file_path,
                local_path=tmp_path
            )

            # Return file
            return FileResponse(
                path=tmp_path,
                filename=os.path.basename(file_path),
                media_type="application/octet-stream"
            )

        except Exception as e:
            # Clean up on error
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    except HetznerStorageBoxError as e:
        logger.error(f"Storage error: {e}")
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get(
    "/list",
    response_model=FileListResponse,
    summary="List files",
    description="""
    List files in organization storage directory.

    **Rate Limit**: 20 requests per minute (Free tier)
    """
)
async def list_files(
    path: str = Query("", description="Directory path to list (empty for root)"),
    recursive: bool = Query(False, description="List files recursively"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """
    List files in organization storage.

    Args:
        path: Directory path to list
        recursive: Whether to list recursively
        api_key: API key info (from middleware)

    Returns:
        List of files with metadata
    """
    try:
        organization_id = api_key.get("tenant_id")

        # Get storage
        storage = await get_storage(
            protocol=StorageProtocol.WEBDAV,
            base_path=get_org_base_path(organization_id)
        )

        # List files
        files = await storage.list_files(path, recursive=recursive)

        # Format response
        file_list = [
            {
                "name": f["name"],
                "path": f["path"],
                "is_directory": f["is_directory"],
                "size": f["size"],
                "modified": f.get("modified")
            }
            for f in files
        ]

        return {
            "organization_id": organization_id,
            "path": path,
            "files": file_list,
            "total": len(file_list)
        }

    except HetznerStorageBoxError as e:
        logger.error(f"Storage error: {e}")
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
    except Exception as e:
        logger.error(f"List failed: {e}")
        raise HTTPException(status_code=500, detail=f"List failed: {str(e)}")


@router.delete(
    "/{file_path:path}",
    response_model=FileDeleteResponse,
    summary="Delete file",
    description="""
    Delete a file from organization storage.

    **Rate Limit**: 10 deletes per minute (Free tier)

    **Warning**: This action cannot be undone.
    """
)
async def delete_file(
    file_path: str,
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """
    Delete file from organization storage.

    Args:
        file_path: File path within organization storage
        api_key: API key info (from middleware)

    Returns:
        Deletion confirmation
    """
    try:
        organization_id = api_key.get("tenant_id")

        # Get storage
        storage = await get_storage(
            protocol=StorageProtocol.WEBDAV,
            base_path=get_org_base_path(organization_id)
        )

        # Check if file exists
        if not await storage.file_exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Delete file
        await storage.delete_file(file_path)

        return {
            "success": True,
            "path": file_path,
            "message": "File deleted successfully"
        }

    except HetznerStorageBoxError as e:
        logger.error(f"Storage error: {e}")
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get(
    "/info/{file_path:path}",
    response_model=FileMetadata,
    summary="Get file info",
    description="""
    Get metadata for a file.

    **Rate Limit**: 20 requests per minute (Free tier)
    """
)
async def get_file_info(
    file_path: str,
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """
    Get file metadata.

    Args:
        file_path: File path within organization storage
        api_key: API key info (from middleware)

    Returns:
        File metadata
    """
    try:
        organization_id = api_key.get("tenant_id")

        # Get storage
        storage = await get_storage(
            protocol=StorageProtocol.WEBDAV,
            base_path=get_org_base_path(organization_id)
        )

        # Check if file exists
        if not await storage.file_exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Get file info
        info = await storage.get_file_info(file_path)

        return {
            "name": os.path.basename(info["path"]),
            "path": info["path"],
            "is_directory": info["is_directory"],
            "size": info["size"],
            "modified": info.get("modified")
        }

    except HetznerStorageBoxError as e:
        logger.error(f"Storage error: {e}")
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get info failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get info failed: {str(e)}")


@router.post(
    "/create-directory",
    summary="Create directory",
    description="""
    Create a directory in organization storage.

    **Rate Limit**: 10 requests per minute (Free tier)
    """
)
async def create_directory(
    path: str = Query(..., description="Directory path to create"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """
    Create directory in organization storage.

    Args:
        path: Directory path to create
        api_key: API key info (from middleware)

    Returns:
        Creation confirmation
    """
    try:
        organization_id = api_key.get("tenant_id")

        # Get storage
        storage = await get_storage(
            protocol=StorageProtocol.WEBDAV,
            base_path=get_org_base_path(organization_id)
        )

        # Create directory
        await storage.create_directory(path)

        return {
            "success": True,
            "path": path,
            "message": "Directory created successfully"
        }

    except HetznerStorageBoxError as e:
        logger.error(f"Storage error: {e}")
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
    except Exception as e:
        logger.error(f"Create directory failed: {e}")
        raise HTTPException(status_code=500, detail=f"Create directory failed: {str(e)}")
