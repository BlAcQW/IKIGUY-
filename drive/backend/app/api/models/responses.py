"""
Response models for Drive API.

Author: AI Labs Africa
Date: 2025-11-10
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class PermissionResponse(BaseModel):
    """Permission details."""
    user_id: str
    role: str
    granted_at: datetime
    granted_by: str


class ShareLinkResponse(BaseModel):
    """Share link details."""
    token: str
    created_at: datetime
    created_by: str
    expires_at: Optional[datetime]
    is_public: bool


class DriveItemResponse(BaseModel):
    """Drive item (file or folder) response."""
    id: str
    name: str
    type: str  # "file" or "folder"
    parent_id: Optional[str]
    size: int
    mime_type: Optional[str]
    created_at: str
    modified_at: str
    owner_id: Optional[str]
    is_starred: bool
    is_deleted: bool
    permissions: List[Dict[str, Any]]
    share_link: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]


class FolderContentsResponse(BaseModel):
    """Folder contents response."""
    items: List[DriveItemResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


class BreadcrumbItem(BaseModel):
    """Breadcrumb item."""
    id: Optional[str]
    name: str


class SearchResultsResponse(BaseModel):
    """Search results response."""
    items: List[DriveItemResponse]
    total: int
    skip: int
    limit: int
    query: str


class ShareLinkCreatedResponse(BaseModel):
    """Response for share link creation."""
    item_id: str
    share_token: str
    expires_at: Optional[datetime]
    is_public: bool


class StatusResponse(BaseModel):
    """Generic status response."""
    status: str
    message: Optional[str] = None
    item_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
