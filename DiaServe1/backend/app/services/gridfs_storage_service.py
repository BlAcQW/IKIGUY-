"""
GridFS Storage Service for Property Images.

Handles image uploads, thumbnail generation, and metadata management using MongoDB GridFS.
"""

import logging
from typing import Optional, Tuple, List
from datetime import datetime
from io import BytesIO
from bson import ObjectId

from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from PIL import Image

from app.core.database import MongoDB
from app.models.image import PropertyImage, ImageDimensions

logger = logging.getLogger(__name__)


class GridFSImageService:
    """
    Service for managing property images in GridFS.

    Provides methods for uploading, retrieving, and deleting images with automatic
    thumbnail generation and metadata tracking.
    """

    # Thumbnail configuration
    THUMBNAIL_SIZE = (300, 300)  # Square thumbnail for property listings

    # Supported image formats
    SUPPORTED_FORMATS = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/heic",
        "image/heif"
    }

    def __init__(self):
        """Initialize GridFS image service."""
        self.bucket: AsyncIOMotorGridFSBucket = MongoDB.get_gridfs_bucket()
        self.db = MongoDB.get_db()

    async def upload_image(
        self,
        image_data: bytes,
        filename: str,
        property_id: str,
        organization_id: str,
        user_id: str,
        mime_type: str,
        is_featured: bool = False,
        order: Optional[int] = None
    ) -> PropertyImage:
        """
        Upload image to GridFS with thumbnail generation.

        Args:
            image_data: Image binary data
            filename: Original filename
            property_id: Property ObjectId as string
            organization_id: Organization ID
            user_id: User ID who uploaded
            mime_type: MIME type (e.g., image/jpeg)
            is_featured: Whether this is the featured image
            order: Display order (auto-assigned if None)

        Returns:
            PropertyImage: Image metadata model with file references

        Raises:
            ValueError: If image is invalid or format unsupported
        """
        # Validate MIME type
        if mime_type not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported image format: {mime_type}. Allowed: {', '.join(self.SUPPORTED_FORMATS)}")

        # Load and validate image
        try:
            img = Image.open(BytesIO(image_data))
            width, height = img.size

            # Convert HEIC/HEIF to JPEG for broader compatibility
            if mime_type in ["image/heic", "image/heif"]:
                img = img.convert("RGB")
                mime_type = "image/jpeg"
                # Update filename extension
                if "." in filename:
                    filename = filename.rsplit(".", 1)[0] + ".jpg"
                else:
                    filename = filename + ".jpg"
                # Convert image_data to JPEG
                output = BytesIO()
                img.save(output, format="JPEG", quality=95)
                image_data = output.getvalue()

        except Exception as e:
            logger.error(f"Invalid image file: {str(e)}")
            raise ValueError(f"Invalid image file: {str(e)}")

        # Generate thumbnail
        try:
            thumbnail_data = await self._generate_thumbnail(img, mime_type)
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {str(e)}")
            raise ValueError(f"Failed to generate thumbnail: {str(e)}")

        # Upload original image to GridFS
        try:
            file_id = await self.bucket.upload_from_stream(
                filename,
                image_data,
                metadata={
                    "property_id": property_id,
                    "organization_id": organization_id,
                    "uploaded_by": user_id,
                    "mime_type": mime_type,
                    "image_type": "original",
                    "width": width,
                    "height": height
                }
            )
            logger.info(f"Uploaded original image to GridFS: {filename} (file_id={file_id})")
        except Exception as e:
            logger.error(f"Failed to upload image to GridFS: {str(e)}")
            raise ValueError(f"Failed to upload image: {str(e)}")

        # Upload thumbnail to GridFS
        try:
            thumbnail_filename = f"thumb_{filename}"
            thumbnail_file_id = await self.bucket.upload_from_stream(
                thumbnail_filename,
                thumbnail_data,
                metadata={
                    "property_id": property_id,
                    "organization_id": organization_id,
                    "uploaded_by": user_id,
                    "mime_type": mime_type,
                    "image_type": "thumbnail",
                    "original_file_id": str(file_id)
                }
            )
            logger.info(f"Uploaded thumbnail to GridFS: {thumbnail_filename} (file_id={thumbnail_file_id})")
        except Exception as e:
            # If thumbnail upload fails, delete the original and raise error
            logger.error(f"Failed to upload thumbnail, cleaning up: {str(e)}")
            await self.bucket.delete(file_id)
            raise ValueError(f"Failed to upload thumbnail: {str(e)}")

        # Auto-assign order if not provided
        if order is None:
            order = await self._get_next_order(property_id)

        # Create image metadata document
        property_image = PropertyImage(
            property_id=property_id,
            organization_id=organization_id,
            file_id=str(file_id),
            thumbnail_file_id=str(thumbnail_file_id),
            filename=filename,
            mime_type=mime_type,
            size=len(image_data),
            dimensions=ImageDimensions(width=width, height=height),
            is_featured=is_featured,
            order=order,
            uploaded_by=user_id,
            uploaded_at=datetime.utcnow()
        )

        # Insert metadata into property_images collection
        try:
            result = await self.db.property_images.insert_one(
                property_image.model_dump(by_alias=True, exclude={"id"})
            )
            property_image.id = str(result.inserted_id)
            logger.info(f"Saved image metadata: image_id={property_image.id}")
        except Exception as e:
            # If metadata save fails, delete GridFS files and raise error
            logger.error(f"Failed to save image metadata, cleaning up: {str(e)}")
            await self.bucket.delete(file_id)
            await self.bucket.delete(thumbnail_file_id)
            raise ValueError(f"Failed to save image metadata: {str(e)}")

        return property_image

    async def _generate_thumbnail(self, img: Image.Image, mime_type: str) -> bytes:
        """
        Generate thumbnail from PIL Image.

        Creates a 300x300 square thumbnail with center crop.

        Args:
            img: PIL Image object
            mime_type: Output MIME type

        Returns:
            bytes: Thumbnail image data
        """
        # Create a copy to avoid modifying original
        thumb = img.copy()

        # Apply EXIF orientation if present
        try:
            from PIL import ImageOps
            thumb = ImageOps.exif_transpose(thumb)
        except Exception:
            pass  # If EXIF processing fails, continue without it

        # Resize maintaining aspect ratio
        thumb.thumbnail(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

        # Crop to square from center
        width, height = thumb.size
        if width != height:
            size = min(width, height)
            left = (width - size) // 2
            top = (height - size) // 2
            thumb = thumb.crop((left, top, left + size, top + size))

        # Convert to bytes
        output = BytesIO()
        format_map = {
            "image/jpeg": "JPEG",
            "image/png": "PNG",
            "image/webp": "WEBP"
        }
        img_format = format_map.get(mime_type, "JPEG")

        # Save with compression
        if img_format == "JPEG":
            # Convert RGBA to RGB for JPEG
            if thumb.mode == "RGBA":
                background = Image.new("RGB", thumb.size, (255, 255, 255))
                background.paste(thumb, mask=thumb.split()[3])  # Use alpha channel as mask
                thumb = background
            thumb.save(output, format=img_format, quality=85, optimize=True)
        elif img_format == "PNG":
            thumb.save(output, format=img_format, optimize=True)
        elif img_format == "WEBP":
            thumb.save(output, format=img_format, quality=85, method=4)

        return output.getvalue()

    async def _get_next_order(self, property_id: str) -> int:
        """
        Get next order number for property images.

        Args:
            property_id: Property ObjectId as string

        Returns:
            int: Next order number
        """
        result = await self.db.property_images.find_one(
            {"property_id": property_id},
            sort=[("order", -1)]
        )
        return (result["order"] + 1) if result else 0

    async def get_image(self, file_id: str) -> Tuple[bytes, str]:
        """
        Get image from GridFS.

        Args:
            file_id: GridFS file ObjectId as string

        Returns:
            Tuple[bytes, str]: (image_data, mime_type)

        Raises:
            FileNotFoundError: If file not found in GridFS
        """
        try:
            grid_out = await self.bucket.open_download_stream(ObjectId(file_id))
            image_data = await grid_out.read()
            mime_type = grid_out.metadata.get("mime_type", "application/octet-stream")
            return image_data, mime_type
        except Exception as e:
            logger.error(f"Failed to retrieve image {file_id}: {str(e)}")
            raise FileNotFoundError(f"Image not found: {file_id}")

    async def delete_image(self, image_id: str) -> bool:
        """
        Delete image and its thumbnail from GridFS.

        Args:
            image_id: property_images._id (not GridFS file_id)

        Returns:
            bool: True if deleted successfully

        Raises:
            ValueError: If image_id is invalid
        """
        try:
            # Get image metadata
            image_doc = await self.db.property_images.find_one(
                {"_id": ObjectId(image_id)}
            )

            if not image_doc:
                logger.warning(f"Image metadata not found: {image_id}")
                return False

            # Delete original from GridFS
            try:
                await self.bucket.delete(ObjectId(image_doc["file_id"]))
                logger.info(f"Deleted original image from GridFS: {image_doc['file_id']}")
            except Exception as e:
                logger.error(f"Failed to delete original image: {str(e)}")

            # Delete thumbnail from GridFS
            if image_doc.get("thumbnail_file_id"):
                try:
                    await self.bucket.delete(ObjectId(image_doc["thumbnail_file_id"]))
                    logger.info(f"Deleted thumbnail from GridFS: {image_doc['thumbnail_file_id']}")
                except Exception as e:
                    logger.error(f"Failed to delete thumbnail: {str(e)}")

            # Delete metadata document
            await self.db.property_images.delete_one({"_id": ObjectId(image_id)})
            logger.info(f"Deleted image metadata: {image_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to delete image {image_id}: {str(e)}")
            raise ValueError(f"Failed to delete image: {str(e)}")

    async def get_property_images(self, property_id: str) -> List[PropertyImage]:
        """
        Get all images for a property.

        Args:
            property_id: Property ObjectId as string

        Returns:
            List[PropertyImage]: List of image metadata sorted by order
        """
        cursor = self.db.property_images.find(
            {"property_id": property_id}
        ).sort("order", 1)

        images = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            images.append(PropertyImage(**doc))

        return images

    async def update_image_order(self, image_id: str, new_order: int) -> bool:
        """
        Update image display order.

        Args:
            image_id: property_images._id
            new_order: New order number

        Returns:
            bool: True if updated successfully
        """
        result = await self.db.property_images.update_one(
            {"_id": ObjectId(image_id)},
            {"$set": {"order": new_order}}
        )
        return result.modified_count > 0

    async def set_featured_image(self, property_id: str, image_id: str) -> bool:
        """
        Set an image as the featured image for a property.

        Unsets any existing featured image first.

        Args:
            property_id: Property ObjectId as string
            image_id: property_images._id to set as featured

        Returns:
            bool: True if updated successfully
        """
        # Unset current featured image
        await self.db.property_images.update_many(
            {"property_id": property_id, "is_featured": True},
            {"$set": {"is_featured": False}}
        )

        # Set new featured image
        result = await self.db.property_images.update_one(
            {"_id": ObjectId(image_id), "property_id": property_id},
            {"$set": {"is_featured": True}}
        )

        return result.modified_count > 0
