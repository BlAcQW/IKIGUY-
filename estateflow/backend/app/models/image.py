"""
Image models for EstateFlow.

This module contains Pydantic models for property images stored in GridFS.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ImageDimensions(BaseModel):
    """
    Image dimensions.

    Attributes:
        width: Image width in pixels
        height: Image height in pixels
    """
    width: int = Field(..., description="Image width in pixels", gt=0)
    height: int = Field(..., description="Image height in pixels", gt=0)


class PropertyImage(BaseModel):
    """
    Property image metadata stored in property_images collection.

    Attributes:
        id: Image metadata ID (MongoDB ObjectId as string)
        property_id: Property ObjectId reference
        organization_id: Organization ID for multi-tenancy
        file_id: GridFS file_id (ObjectId as string)
        thumbnail_file_id: GridFS thumbnail file_id (ObjectId as string)
        filename: Original filename
        mime_type: MIME type (e.g., image/jpeg)
        size: File size in bytes
        dimensions: Image dimensions (width and height)
        is_featured: Whether this is the featured/cover image
        order: Display order for property images
        uploaded_by: User ID who uploaded the image
        uploaded_at: Upload timestamp
    """
    id: Optional[str] = Field(None, alias="_id", description="Image metadata ID")
    property_id: str = Field(..., description="Property ObjectId reference")
    organization_id: str = Field(..., description="Organization ID")
    file_id: str = Field(..., description="GridFS file_id")
    thumbnail_file_id: Optional[str] = Field(None, description="GridFS thumbnail file_id")
    filename: str = Field(..., description="Original filename")
    mime_type: str = Field(..., description="MIME type")
    size: int = Field(..., description="File size in bytes", gt=0)
    dimensions: ImageDimensions = Field(..., description="Image dimensions")
    is_featured: bool = Field(False, description="Is featured/cover image")
    order: int = Field(0, description="Display order", ge=0)
    uploaded_by: str = Field(..., description="User ID who uploaded")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "property_id": "507f1f77bcf86cd799439011",
                "organization_id": "org_123",
                "file_id": "507f191e810c19729de860ea",
                "thumbnail_file_id": "507f191e810c19729de860eb",
                "filename": "villa_front.jpg",
                "mime_type": "image/jpeg",
                "size": 2457600,
                "dimensions": {"width": 1920, "height": 1080},
                "is_featured": True,
                "order": 0,
                "uploaded_by": "user_123"
            }
        }


class ImageSummary(BaseModel):
    """
    Image summary embedded in property.images_v2 array.

    Lightweight reference to image with essential display information.

    Attributes:
        image_id: property_images._id reference
        file_id: GridFS file_id for original image
        thumbnail_file_id: GridFS file_id for thumbnail
        url: API URL to access original image
        thumbnail_url: API URL to access thumbnail
        is_featured: Whether this is the featured/cover image
        order: Display order
    """
    image_id: str = Field(..., description="property_images._id reference")
    file_id: str = Field(..., description="GridFS file_id")
    thumbnail_file_id: Optional[str] = Field(None, description="Thumbnail GridFS file_id")
    url: str = Field(..., description="API URL for original image")
    thumbnail_url: Optional[str] = Field(None, description="API URL for thumbnail")
    is_featured: bool = Field(False, description="Is featured/cover image")
    order: int = Field(0, description="Display order", ge=0)

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "image_id": "507f1f77bcf86cd799439011",
                "file_id": "507f191e810c19729de860ea",
                "thumbnail_file_id": "507f191e810c19729de860eb",
                "url": "/api/v1/storage/gridfs/507f191e810c19729de860ea",
                "thumbnail_url": "/api/v1/storage/gridfs/507f191e810c19729de860eb",
                "is_featured": True,
                "order": 0
            }
        }
