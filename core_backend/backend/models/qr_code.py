"""
QR Code MongoDB models for KasaAI Core Backend.

This module provides models for storing and managing user-generated QR codes.
"""

from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId


class QRCodeDocument(BaseModel):
    """MongoDB document model for QR codes."""

    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str = Field(..., description="User who created the QR code")
    organization_id: str = Field(..., description="Organization the QR code belongs to")

    # QR Code data
    name: str = Field(..., description="Display name for the QR code")
    url: str = Field(..., description="URL encoded in the QR code")

    # Customization
    fill_color: str = Field(default="#000000", description="Foreground color (hex)")
    back_color: str = Field(default="#FFFFFF", description="Background color (hex)")
    has_logo: bool = Field(default=False, description="Whether QR code has an embedded logo")
    logo_filename: Optional[str] = Field(default=None, description="Filename of logo if used")

    # File information
    file_size: int = Field(..., description="File size in bytes")
    image_format: str = Field(default="png", description="Image format (png, jpeg, webp)")
    size: int = Field(default=500, description="Image dimensions in pixels")

    # Storage
    storage_path: Optional[str] = Field(default=None, description="Path to stored QR code file")
    data_url: Optional[str] = Field(default=None, description="Base64 data URL (for preview)")

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    download_count: int = Field(default=0, description="Number of times downloaded")
    last_downloaded_at: Optional[datetime] = None

    # Tags and categorization
    tags: List[str] = Field(default_factory=list, description="User-defined tags")
    category: Optional[str] = Field(default=None, description="Category (e.g., marketing, product, event)")
    notes: Optional[str] = Field(default=None, description="User notes")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "user_id": "00000000-0000-0000-0000-000000000001",
                "organization_id": "org_123456",
                "name": "Product Launch QR",
                "url": "https://ailabsafrica.com/products/new",
                "fill_color": "#1A1D2E",
                "back_color": "#FFFFFF",
                "has_logo": True,
                "logo_filename": "brand_logo.png",
                "file_size": 15360,
                "image_format": "png",
                "size": 500,
                "tags": ["marketing", "product", "launch"],
                "category": "marketing",
                "notes": "QR code for new product launch campaign"
            }
        }


class QRCodeCreate(BaseModel):
    """Model for creating a new QR code."""

    name: str = Field(..., description="Display name for the QR code", min_length=1, max_length=200)
    url: str = Field(..., description="URL to encode", min_length=1, max_length=2000)
    fill_color: str = Field(default="#000000", description="Foreground color (hex)")
    back_color: str = Field(default="#FFFFFF", description="Background color (hex)")
    size: int = Field(default=500, ge=100, le=2000, description="Image size in pixels")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    category: Optional[str] = Field(default=None, description="Category")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Notes")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Website QR Code",
                "url": "https://ailabsafrica.com",
                "fill_color": "#1A1D2E",
                "back_color": "#F5F5F5",
                "size": 500,
                "tags": ["website", "homepage"],
                "category": "marketing",
                "notes": "Main website QR code for print materials"
            }
        }


class QRCodeUpdate(BaseModel):
    """Model for updating an existing QR code."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    tags: Optional[List[str]] = Field(default=None)
    category: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated QR Code Name",
                "tags": ["updated", "tag1", "tag2"],
                "category": "event",
                "notes": "Updated notes"
            }
        }


class QRCodeResponse(BaseModel):
    """Response model for QR code operations."""

    id: str = Field(..., description="QR code ID")
    user_id: str
    organization_id: str
    name: str
    url: str
    fill_color: str
    back_color: str
    has_logo: bool
    logo_filename: Optional[str]
    file_size: int
    image_format: str
    size: int
    storage_path: Optional[str]
    data_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    download_count: int
    last_downloaded_at: Optional[datetime]
    tags: List[str]
    category: Optional[str]
    notes: Optional[str]

    @property
    def size_kb(self) -> float:
        """Get file size in KB."""
        return self.file_size / 1024

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "user_id": "00000000-0000-0000-0000-000000000001",
                "organization_id": "org_123456",
                "name": "Product QR Code",
                "url": "https://ailabsafrica.com/products",
                "fill_color": "#1A1D2E",
                "back_color": "#FFFFFF",
                "has_logo": True,
                "logo_filename": "logo.png",
                "file_size": 15360,
                "image_format": "png",
                "size": 500,
                "storage_path": "/storage/qr_codes/507f1f77bcf86cd799439011.png",
                "data_url": "data:image/png;base64,iVBORw0KG...",
                "created_at": "2025-11-09T10:30:00Z",
                "updated_at": "2025-11-09T10:30:00Z",
                "download_count": 5,
                "last_downloaded_at": "2025-11-09T11:00:00Z",
                "tags": ["product", "marketing"],
                "category": "marketing",
                "notes": "For product catalog"
            }
        }


class QRCodeListResponse(BaseModel):
    """Response model for listing QR codes."""

    qr_codes: List[QRCodeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        json_schema_extra = {
            "example": {
                "qr_codes": [],
                "total": 25,
                "page": 1,
                "page_size": 20,
                "total_pages": 2
            }
        }
