"""
Material service for StudyFlow.

Handles study material uploads, processing, and management.
Uses shared Hetzner Storage Box for file storage.
"""

import os
import logging
from typing import Optional, List
from datetime import datetime
from pathlib import Path
from bson import ObjectId
from pydantic import ValidationError

from app.models.material import (
    StudyMaterial,
    MaterialCreate,
    MaterialUpdate,
    MaterialType,
    ProcessingStatus
)
from app.core.database import mongodb, COLLECTION_MATERIALS
from app.config import settings
from app.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)


class MaterialService:
    """
    Service for managing study materials.

    Handles material uploads, processing, and retrieval.
    """

    @staticmethod
    def _detect_material_type(filename: str) -> MaterialType:
        """
        Detect material type from filename extension.

        Args:
            filename: Original filename

        Returns:
            MaterialType enum
        """
        ext = filename.lower().split('.')[-1]
        type_map = {
            'pdf': MaterialType.PDF,
            'docx': MaterialType.DOCX,
            'doc': MaterialType.DOCX,
            'txt': MaterialType.TXT,
            'jpg': MaterialType.IMAGE,
            'jpeg': MaterialType.IMAGE,
            'png': MaterialType.IMAGE,
            'mp4': MaterialType.VIDEO,
            'avi': MaterialType.VIDEO,
            'mp3': MaterialType.AUDIO,
            'wav': MaterialType.AUDIO,
        }
        return type_map.get(ext, MaterialType.TXT)

    @staticmethod
    async def create_material(
        material_data: MaterialCreate,
        file_name: str,
        file_path: str,
        file_size: int,
        uploaded_by: str
    ) -> StudyMaterial:
        """
        Create a new material record.

        Args:
            material_data: Material metadata
            file_name: Original filename
            file_path: Path to stored file
            file_size: File size in bytes
            uploaded_by: User ID who uploaded

        Returns:
            Created material
        """
        # Detect file type
        file_type = MaterialService._detect_material_type(file_name)

        # Create material document
        material = StudyMaterial(
            organization_id=material_data.organization_id,  # Organization scoping
            school_id=material_data.school_id,
            title=material_data.title,
            description=material_data.description,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            subject=material_data.subject,
            topics=material_data.topics,
            grade=material_data.grade,
            uploaded_by=uploaded_by,
            status=ProcessingStatus.PENDING,
            metadata=material_data.metadata,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Insert into database
        collection = mongodb.get_collection(COLLECTION_MATERIALS)
        result = await collection.insert_one(material.dict(by_alias=True, exclude={"id"}))

        # Return material with ID
        material.id = str(result.inserted_id)
        logger.info(f"Material created: {material.id} ({material.title})")
        return material

    @staticmethod
    async def get_material_by_id(
        material_id: str,
        organization_id: Optional[str] = None
    ) -> Optional[StudyMaterial]:
        """
        Get material by ID with optional organization filtering.

        Args:
            material_id: Material ID
            organization_id: Organization ID for access control (optional)

        Returns:
            Material if found and accessible, None otherwise
        """
        # Build query with optional organization filtering
        # If organization_id is None (universal admin), no organization filter applied
        query = {"_id": ObjectId(material_id)}
        if organization_id is not None:
            query["$or"] = [
                {"organization_id": organization_id},
                {"organization_id": None},
                {"organization_id": ""}
            ]

        collection = mongodb.get_collection(COLLECTION_MATERIALS)
        material_doc = await collection.find_one(query)

        if material_doc:
            material_doc["id"] = str(material_doc.pop("_id"))

            # Fix legacy data compatibility
            # Handle missing file_name field (use title as fallback)
            if "file_name" not in material_doc and "title" in material_doc:
                material_doc["file_name"] = material_doc["title"]

            # Map old 'processed' status to 'completed'
            if material_doc.get("status") == "processed":
                material_doc["status"] = "completed"

            return StudyMaterial(**material_doc)

        logger.warning(f"Material not found or not accessible: {material_id}")
        return None

    @staticmethod
    async def update_material(
        material_id: str,
        update_data: MaterialUpdate,
        organization_id: Optional[str] = None
    ) -> Optional[StudyMaterial]:
        """
        Update material information with organization access control.

        Args:
            material_id: Material ID
            update_data: Fields to update
            organization_id: Organization ID for access control (optional)

        Returns:
            Updated material if found and accessible, None otherwise
        """
        # Get only fields that were provided
        update_dict = update_data.dict(exclude_unset=True)
        if not update_dict:
            return await MaterialService.get_material_by_id(material_id, organization_id)

        # Always update the updated_at timestamp
        update_dict["updated_at"] = datetime.utcnow()

        # Build query with organization check
        query = {"_id": ObjectId(material_id)}
        if organization_id:
            query["organization_id"] = organization_id

        # Update in database
        collection = mongodb.get_collection(COLLECTION_MATERIALS)
        result = await collection.update_one(query, {"$set": update_dict})

        if result.matched_count == 0:
            return None

        logger.info(f"Material updated: {material_id}")
        return await MaterialService.get_material_by_id(material_id, organization_id)

    @staticmethod
    async def delete_material(
        material_id: str,
        organization_id: Optional[str] = None
    ) -> bool:
        """
        Delete a material with organization access control.

        Args:
            material_id: Material ID
            organization_id: Organization ID for access control (optional)

        Returns:
            True if deleted, False otherwise
        """
        # Build query with organization check
        # Allow deletion if organization_id matches OR if material has no organization_id
        query = {"_id": ObjectId(material_id)}
        if organization_id:
            query["$or"] = [
                {"organization_id": organization_id},
                {"organization_id": None},
                {"organization_id": ""}
            ]

        # Get material to delete file
        collection = mongodb.get_collection(COLLECTION_MATERIALS)
        material_doc = await collection.find_one(query)

        if not material_doc:
            logger.warning(f"Material not found or not accessible: {material_id}")
            return False

        # Delete file from storage
        try:
            storage_path = material_doc.get("file_path", "")
            if storage_path:
                storage_service = await get_storage_service()
                await storage_service.delete_material_file(storage_path)
                logger.info(f"Deleted file from storage: {storage_path}")
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")

        # Delete from database
        result = await collection.delete_one({"_id": ObjectId(material_id)})

        logger.info(f"Material deleted: {material_id}")
        return result.deleted_count > 0

    @staticmethod
    async def list_materials(
        organization_id: Optional[str] = None,
        subject: Optional[str] = None,
        grade: Optional[int] = None,
        school_id: Optional[str] = None,
        uploaded_by: Optional[str] = None,
        status: Optional[ProcessingStatus] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[StudyMaterial]:
        """
        List materials with filtering and pagination.

        Args:
            organization_id: Filter by organization (required for scoping)
            subject: Filter by subject
            grade: Filter by grade
            school_id: Filter by school
            uploaded_by: Filter by uploader
            status: Filter by processing status
            limit: Maximum number of materials
            skip: Number to skip

        Returns:
            List of materials
        """
        # Build query with organization scope
        # If organization_id is None, fetch all materials (universal admin)
        # Otherwise, include materials with matching organization_id OR NULL (legacy compatibility)
        query = {}
        if organization_id is not None:
            query["$or"] = [
                {"organization_id": organization_id},
                {"organization_id": None},
                {"organization_id": ""}
            ]
        # If organization_id is None (universal admin), no organization filter applied

        if subject:
            query["subject"] = subject
        if grade is not None:
            query["grade"] = grade
        if school_id:
            query["school_id"] = school_id
        if uploaded_by:
            query["uploaded_by"] = uploaded_by
        if status:
            query["status"] = status.value

        # Query database
        collection = mongodb.get_collection(COLLECTION_MATERIALS)
        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)

        materials = []
        async for material_doc in cursor:
            material_doc["id"] = str(material_doc.pop("_id"))

            # Fix legacy data compatibility
            # Handle missing file_name field (use title as fallback)
            if "file_name" not in material_doc and "title" in material_doc:
                material_doc["file_name"] = material_doc["title"]

            # Map old 'processed' status to 'completed'
            if material_doc.get("status") == "processed":
                material_doc["status"] = "completed"

            # Add file_type migration for materials without this field
            if "file_type" not in material_doc:
                # Infer file_type from content_type or file_path
                # Valid MaterialType enum values: pdf, docx, txt, image, video, audio
                content_type = material_doc.get("content_type", "")
                file_path = material_doc.get("file_path", "")

                if "pdf" in content_type.lower() or file_path.endswith(".pdf"):
                    material_doc["file_type"] = "pdf"
                elif any(ext in file_path.lower() for ext in [".doc", ".docx"]):
                    material_doc["file_type"] = "docx"
                elif file_path.endswith(".txt") or "text" in content_type:
                    material_doc["file_type"] = "txt"
                elif any(ext in file_path.lower() for ext in [".jpg", ".png", ".gif", ".jpeg"]):
                    material_doc["file_type"] = "image"
                elif any(ext in file_path.lower() for ext in [".mp4", ".avi", ".mov"]):
                    material_doc["file_type"] = "video"
                elif any(ext in file_path.lower() for ext in [".mp3", ".wav", ".aac"]):
                    material_doc["file_type"] = "audio"
                else:
                    material_doc["file_type"] = "pdf"  # Default to pdf for unknown types

            # Add grade normalization for string grades
            if "grade" in material_doc:
                grade_value = material_doc["grade"]
                if isinstance(grade_value, str):
                    # Handle string grades like "Professional", "K", etc.
                    if grade_value.lower() in ["professional", "adult", "university"]:
                        material_doc["grade"] = None
                    elif grade_value.isdigit():
                        material_doc["grade"] = int(grade_value)
                    else:
                        material_doc["grade"] = None  # Invalid grade, set to None
                elif grade_value is not None and not isinstance(grade_value, int):
                    material_doc["grade"] = None

            # Remove None grades if grade is optional
            if material_doc.get("grade") is None:
                material_doc.pop("grade", None)

            # Add error handling for invalid documents
            try:
                materials.append(StudyMaterial(**material_doc))
            except ValidationError as e:
                logger.warning(
                    f"Skipping invalid material document {material_doc.get('id')}: {e}"
                )
                continue  # Skip this material and continue with others

        return materials

    @staticmethod
    async def update_processing_status(
        material_id: str,
        status: ProcessingStatus,
        chunks_count: Optional[int] = None,
        embedding_collection: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Optional[StudyMaterial]:
        """
        Update material processing status with organization access control.

        Args:
            material_id: Material ID
            status: New processing status
            chunks_count: Number of chunks extracted
            embedding_collection: RAG collection name
            organization_id: Organization ID for access control (optional)

        Returns:
            Updated material
        """
        update_dict = {
            "status": status.value,
            "updated_at": datetime.utcnow()
        }

        if status == ProcessingStatus.COMPLETED:
            update_dict["processed_at"] = datetime.utcnow()

        if chunks_count is not None:
            update_dict["chunks_count"] = chunks_count

        if embedding_collection:
            update_dict["embedding_collection"] = embedding_collection

        # Build query with organization check
        query = {"_id": ObjectId(material_id)}
        if organization_id:
            query["organization_id"] = organization_id

        collection = mongodb.get_collection(COLLECTION_MATERIALS)
        result = await collection.update_one(query, {"$set": update_dict})

        if result.matched_count == 0:
            return None

        logger.info(f"Material processing status updated: {material_id} -> {status.value}")
        return await MaterialService.get_material_by_id(material_id, organization_id)

    @staticmethod
    async def save_uploaded_file(
        file_content: bytes,
        filename: str,
        material_id: str,
        organization_id: str,
        user_id: str
    ) -> tuple[str, int]:
        """
        Save uploaded file to storage using shared Hetzner Storage Box.

        Args:
            file_content: File content bytes
            filename: Original filename
            material_id: Material ID (for unique file naming)
            organization_id: Organization ID
            user_id: User ID (for organizing files)

        Returns:
            Tuple of (storage_path, file_size)
        """
        storage_service = await get_storage_service()
        
        # Upload to Hetzner storage (or local fallback)
        storage_path = await storage_service.upload_material_file(
            file_content=file_content,
            filename=filename,
            material_id=material_id,
            organization_id=organization_id,
            user_id=user_id
        )
        
        file_size = len(file_content)
        logger.info(f"File saved to storage: {storage_path} ({file_size} bytes)")
        return storage_path, file_size
