"""
File Upload Service.

Handles secure file uploads for employee documents (CVs, certificates, etc.).
"""

import os
import uuid
from typing import Optional
from pathlib import Path
from fastapi import UploadFile, HTTPException, status

from app.config import settings


class FileUploadService:
    """Service for handling file uploads."""

    def __init__(self):
        """Initialize file upload service."""
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        self.allowed_extensions = settings.ALLOWED_EXTENSIONS.split(",")

        # Create upload directory if it doesn't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, file: UploadFile) -> None:
        """
        Validate uploaded file.

        Args:
            file: The uploaded file

        Raises:
            HTTPException: If file is invalid
        """
        # Check if file is provided
        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )

        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            )

    async def save_file(
        self,
        file: UploadFile,
        organization_id: str,
        employee_id: str,
        file_type: str  # 'cv' or 'certificate'
    ) -> str:
        """
        Save uploaded file to disk.

        Args:
            file: The uploaded file
            organization_id: Organization ID
            employee_id: Employee ID
            file_type: Type of file (cv or certificate)

        Returns:
            Relative path to saved file

        Raises:
            HTTPException: If save fails
        """
        # Validate file
        self.validate_file(file)

        # Create organization/employee directory structure
        org_dir = self.upload_dir / organization_id / "employees" / employee_id / file_type
        org_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = org_dir / unique_filename

        try:
            # Read and save file
            contents = await file.read()

            # Check file size
            if len(contents) > self.max_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
                )

            # Write file to disk
            with open(file_path, "wb") as f:
                f.write(contents)

            # Return relative path (from upload_dir)
            relative_path = str(file_path.relative_to(self.upload_dir))
            return relative_path

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )

    def delete_file(self, file_path: str) -> None:
        """
        Delete file from disk.

        Args:
            file_path: Relative path to file (from upload_dir)
        """
        try:
            full_path = self.upload_dir / file_path
            if full_path.exists():
                full_path.unlink()
        except Exception as e:
            # Log error but don't raise - file might already be deleted
            print(f"Failed to delete file {file_path}: {e}")

    def get_file_url(self, file_path: Optional[str]) -> Optional[str]:
        """
        Get public URL for file.

        Args:
            file_path: Relative path to file

        Returns:
            Public URL or None
        """
        if not file_path:
            return None

        # In production, this would return a URL served by nginx or a CDN
        # For now, return the API endpoint URL
        return f"/api/v1/hr/files/{file_path}"


# Create singleton instance
file_upload_service = FileUploadService()


def get_file_upload_service() -> FileUploadService:
    """Get file upload service instance."""
    return file_upload_service
