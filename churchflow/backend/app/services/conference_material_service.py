"""
Conference Material Service.

Handles file uploads, downloads, and management of conference materials.
"""

import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from fastapi import UploadFile

from app.core.database import get_database
from app.models.conference_material import ConferenceMaterial

logger = logging.getLogger(__name__)

# Storage configuration
STORAGE_BASE_PATH = "storage/conference_materials"
ALLOWED_FILE_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/jpeg",
    "image/png",
    "image/gif",
    "text/plain"
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class ConferenceMaterialService:
    """
    Service for managing conference materials.

    Handles:
    - File uploads with validation
    - File downloads
    - Material metadata management
    - Public/private access control
    """

    def __init__(self):
        """Initialize the service."""
        self.db = None
        self.storage_path = None

    def set_database(self, db):
        """Set the database connection."""
        self.db = db

    def set_storage_path(self, path: str):
        """Set the storage base path."""
        self.storage_path = path
        os.makedirs(path, exist_ok=True)

    async def upload_material(
        self,
        file: UploadFile,
        conference_id: str,
        organization_id: str,
        title: str,
        uploaded_by_user_id: str,
        description: Optional[str] = None,
        material_type: str = "other",
        is_public: bool = True,
        display_on_landing: bool = False,
        display_order: int = 0
    ) -> ConferenceMaterial:
        """
        Upload a new conference material.

        Args:
            file: Uploaded file
            conference_id: Conference ID
            organization_id: Organization ID
            title: Material title
            uploaded_by_user_id: User ID who uploaded
            description: Optional description
            material_type: Type of material
            is_public: Whether material is public
            display_on_landing: Whether to display on landing page
            display_order: Display order

        Returns:
            ConferenceMaterial: Created material object

        Raises:
            ValueError: If file validation fails
            Exception: If upload fails
        """
        if self.db is None:
            self.db = get_database()

        if self.storage_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.storage_path = os.path.join(base_dir, STORAGE_BASE_PATH)
            os.makedirs(self.storage_path, exist_ok=True)

        logger.info(f"Uploading material: {title} for conference {conference_id}")

        # Validate file type
        if file.content_type not in ALLOWED_FILE_TYPES:
            raise ValueError(f"File type {file.content_type} not allowed")

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Validate file size
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"File size {file_size} exceeds maximum {MAX_FILE_SIZE}")

        if file_size == 0:
            raise ValueError("File is empty")

        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = file.filename.replace(" ", "-").replace("/", "-")
        unique_filename = f"{conference_id}_{timestamp}_{safe_filename}"
        file_path = os.path.join(self.storage_path, unique_filename)

        # Save file
        try:
            with open(file_path, "wb") as f:
                f.write(content)
            logger.info(f"Saved file to: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise Exception(f"Failed to save file: {str(e)}")

        # Create database record
        material_doc = {
            "conference_id": ObjectId(conference_id),
            "organization_id": ObjectId(organization_id),
            "title": title,
            "description": description,
            "file_name": file.filename,
            "file_path": unique_filename,  # Store relative path
            "file_size": file_size,
            "file_type": file.content_type,
            "material_type": material_type,
            "is_public": is_public,
            "display_on_landing": display_on_landing,
            "display_order": display_order,
            "uploaded_by": ObjectId(uploaded_by_user_id),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = await self.db.conference_materials.insert_one(material_doc)
        material_doc["_id"] = result.inserted_id

        logger.info(f"Created material: {result.inserted_id}")

        return ConferenceMaterial(**material_doc)

    async def get_material(self, material_id: str) -> Optional[ConferenceMaterial]:
        """
        Get material by ID.

        Args:
            material_id: Material ID

        Returns:
            ConferenceMaterial or None if not found
        """
        if self.db is None:
            self.db = get_database()

        material = await self.db.conference_materials.find_one(
            {"_id": ObjectId(material_id)}
        )

        if not material:
            return None

        return ConferenceMaterial(**material)

    async def get_conference_materials(
        self,
        conference_id: str,
        public_only: bool = False,
        landing_page_only: bool = False
    ) -> List[ConferenceMaterial]:
        """
        Get all materials for a conference.

        Args:
            conference_id: Conference ID
            public_only: Only return public materials
            landing_page_only: Only return materials marked for landing page

        Returns:
            List of materials
        """
        if self.db is None:
            self.db = get_database()

        query = {"conference_id": ObjectId(conference_id)}

        if public_only:
            query["is_public"] = True

        if landing_page_only:
            query["display_on_landing"] = True

        cursor = self.db.conference_materials.find(query).sort([
            ("display_order", 1),
            ("created_at", -1)
        ])

        materials = []
        async for doc in cursor:
            materials.append(ConferenceMaterial(**doc))

        return materials

    async def update_material(
        self,
        material_id: str,
        updates: Dict[str, Any]
    ) -> ConferenceMaterial:
        """
        Update material metadata.

        Args:
            material_id: Material ID
            updates: Fields to update

        Returns:
            Updated material

        Raises:
            ValueError: If material not found
        """
        if self.db is None:
            self.db = get_database()

        # Don't allow updating file_path or file_name
        updates.pop("file_path", None)
        updates.pop("file_name", None)
        updates.pop("file_size", None)
        updates.pop("file_type", None)

        updates["updated_at"] = datetime.utcnow()

        result = await self.db.conference_materials.find_one_and_update(
            {"_id": ObjectId(material_id)},
            {"$set": updates},
            return_document=True
        )

        if not result:
            raise ValueError(f"Material {material_id} not found")

        logger.info(f"Updated material: {material_id}")

        return ConferenceMaterial(**result)

    async def delete_material(self, material_id: str) -> bool:
        """
        Delete material and its file.

        Args:
            material_id: Material ID

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If material not found
        """
        if self.db is None:
            self.db = get_database()

        if self.storage_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.storage_path = os.path.join(base_dir, STORAGE_BASE_PATH)

        # Get material to find file path
        material = await self.db.conference_materials.find_one(
            {"_id": ObjectId(material_id)}
        )

        if not material:
            raise ValueError(f"Material {material_id} not found")

        # Delete file
        file_path = os.path.join(self.storage_path, material["file_path"])
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            # Continue with database deletion even if file deletion fails

        # Delete database record
        await self.db.conference_materials.delete_one({"_id": ObjectId(material_id)})

        logger.info(f"Deleted material: {material_id}")

        return True

    def get_file_path(self, material: ConferenceMaterial) -> str:
        """
        Get absolute file path for a material.

        Args:
            material: Material object

        Returns:
            Absolute file path
        """
        if self.storage_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.storage_path = os.path.join(base_dir, STORAGE_BASE_PATH)

        return os.path.join(self.storage_path, material.file_path)


# Global service instance
conference_material_service = ConferenceMaterialService()
