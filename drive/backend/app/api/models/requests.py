"""
Request models for Drive API.

Author: AI Labs Africa
Date: 2025-11-10
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FileUploadRequest(BaseModel):
    """Request model for file upload."""
    parent_id: Optional[str] = Field(None, description="Parent folder ID")
    organization_id: str = Field(..., description="Organization ID")


class CreateFolderRequest(BaseModel):
    """Request model for creating a folder."""
    name: str = Field(..., min_length=1, max_length=255, description="Folder name")
    parent_id: Optional[str] = Field(None, description="Parent folder ID")
    organization_id: str = Field(..., description="Organization ID")


class RenameItemRequest(BaseModel):
    """Request model for renaming an item."""
    new_name: str = Field(..., min_length=1, max_length=255, description="New name")


class MoveItemRequest(BaseModel):
    """Request model for moving an item."""
    new_parent_id: Optional[str] = Field(None, description="New parent folder ID")


class ShareItemRequest(BaseModel):
    """Request model for sharing an item with a user."""
    target_user_id: str = Field(..., description="User ID to share with")
    role: str = Field("view", description="Permission role: view, comment, edit, manage")


class CreateShareLinkRequest(BaseModel):
    """Request model for creating a public share link."""
    expires_in_days: Optional[int] = Field(None, gt=0, description="Link expiry in days")
    is_public: bool = Field(True, description="Whether link allows public access")


class SearchRequest(BaseModel):
    """Request model for searching files."""
    query: str = Field(..., min_length=1, description="Search query")
    file_type: Optional[str] = Field(None, description="Filter by type: folder, document, image, video, audio")
    owner_id: Optional[str] = Field(None, description="Filter by owner")
    date_from: Optional[datetime] = Field(None, description="Filter by modified date (from)")
    date_to: Optional[datetime] = Field(None, description="Filter by modified date (to)")
    skip: int = Field(0, ge=0, description="Pagination offset")
    limit: int = Field(50, ge=1, le=100, description="Pagination limit")
