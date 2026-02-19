"""
File operations API routes.

Author: AI Labs Africa
Date: 2025-11-10
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional
import io

from apps.shared.unified_logging import get_logger, LogTimer
from apps.shared.services.drive_service import DriveService, FileNotFoundError, PermissionDeniedError
from apps.drive.backend.app.api.dependencies import get_current_user, get_drive_service_instance
from apps.drive.backend.app.api.models.requests import RenameItemRequest, MoveItemRequest
from apps.drive.backend.app.api.models.responses import DriveItemResponse, StatusResponse, ErrorResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post("/upload", response_model=DriveItemResponse)
async def upload_file(
    file: UploadFile = File(...),
    parent_id: Optional[str] = Form(None),
    organization_id: str = Form(...),
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Upload a file to the drive.

    Args:
        file: File to upload
        parent_id: Parent folder ID (optional)
        organization_id: Organization ID
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        Uploaded file metadata
    """
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        logger.info("Uploading file",
                    filename=file.filename,
                    size_bytes=file_size,
                    parent_id=parent_id,
                    user_id=current_user["user_id"],
                    organization_id=organization_id)

        # Upload file with timing
        with LogTimer(logger, "File upload",
                      filename=file.filename,
                      size_bytes=file_size):
            result = await drive_service.upload_file(
                file_content=file_content,
                filename=file.filename,
                parent_id=parent_id,
                owner_id=current_user["user_id"],
                organization_id=organization_id
            )

        logger.info("File uploaded successfully",
                    file_id=result["id"],
                    filename=file.filename,
                    user_id=current_user["user_id"])
        return result

    except Exception as e:
        logger.exception("File upload failed",
                        filename=file.filename,
                        user_id=current_user["user_id"],
                        error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}", response_model=DriveItemResponse)
async def get_file_info(
    file_id: str,
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Get file metadata.

    Args:
        file_id: File ID
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        File metadata
    """
    try:
        result = await drive_service.get_file_info(
            file_id=file_id,
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"]
        )
        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Download a file.

    Args:
        file_id: File ID
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        File content as streaming response
    """
    try:
        content, filename, mime_type = await drive_service.download_file(
            file_id=file_id,
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"]
        )

        # Create streaming response
        return StreamingResponse(
            io.BytesIO(content),
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{file_id}/rename", response_model=DriveItemResponse)
async def rename_file(
    file_id: str,
    request: RenameItemRequest,
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Rename a file.

    Args:
        file_id: File ID
        request: Rename request
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        Updated file metadata
    """
    try:
        result = await drive_service.rename_file(
            file_id=file_id,
            new_name=request.new_name,
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"]
        )
        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error renaming file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{file_id}/move", response_model=DriveItemResponse)
async def move_file(
    file_id: str,
    request: MoveItemRequest,
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Move a file to a different folder.

    Args:
        file_id: File ID
        request: Move request
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        Updated file metadata
    """
    try:
        result = await drive_service.move_file(
            file_id=file_id,
            new_parent_id=request.new_parent_id,
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"]
        )
        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error moving file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_id}", response_model=StatusResponse)
async def delete_file(
    file_id: str,
    permanent: bool = False,
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Delete a file (move to trash or permanent delete).

    Args:
        file_id: File ID
        permanent: Whether to permanently delete (default: False, move to trash)
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        Status response
    """
    try:
        result = await drive_service.delete_file(
            file_id=file_id,
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"],
            permanent=permanent
        )
        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{file_id}/star", response_model=DriveItemResponse)
async def toggle_star(
    file_id: str,
    current_user: dict = Depends(get_current_user),
    drive_service: DriveService = Depends(get_drive_service_instance)
):
    """
    Toggle star status of a file.

    Args:
        file_id: File ID
        current_user: Current authenticated user
        drive_service: Drive service instance

    Returns:
        Updated file metadata
    """
    try:
        result = await drive_service.toggle_star(
            item_id=file_id,
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"]
        )
        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error toggling star: {e}")
        raise HTTPException(status_code=500, detail=str(e))
