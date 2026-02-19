"""
QR Code Service for CRUD operations.

This module provides business logic for managing QR codes in MongoDB.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models.qr_code import (
    QRCodeDocument,
    QRCodeCreate,
    QRCodeUpdate,
    QRCodeResponse,
    QRCodeListResponse
)

logger = logging.getLogger(__name__)


class QRCodeService:
    """Service for managing QR codes in MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize QR code service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.qr_codes

    async def create_qr_code(
        self,
        user_id: str,
        organization_id: str,
        data: QRCodeCreate,
        image_data: bytes,
        data_url: str,
        has_logo: bool = False,
        logo_filename: Optional[str] = None,
        storage_path: Optional[str] = None
    ) -> QRCodeResponse:
        """
        Create a new QR code document.

        Args:
            user_id: User creating the QR code
            organization_id: Organization ID
            data: QR code creation data
            image_data: Generated QR code image bytes
            data_url: Base64 data URL
            has_logo: Whether QR code has logo
            logo_filename: Filename of logo if used
            storage_path: Path where file is stored

        Returns:
            Created QR code response
        """
        # Create document
        qr_doc = QRCodeDocument(
            user_id=user_id,
            organization_id=organization_id,
            name=data.name,
            url=data.url,
            fill_color=data.fill_color,
            back_color=data.back_color,
            has_logo=has_logo,
            logo_filename=logo_filename,
            file_size=len(image_data),
            image_format="png",
            size=data.size,
            storage_path=storage_path,
            data_url=data_url,
            tags=data.tags,
            category=data.category,
            notes=data.notes,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            download_count=0
        )

        # Insert into MongoDB
        doc_dict = qr_doc.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(doc_dict)

        # Return response - use model_dump without alias to get 'id' field
        qr_doc.id = str(result.inserted_id)
        response_dict = qr_doc.model_dump(by_alias=False)
        response_dict["id"] = str(result.inserted_id)
        return QRCodeResponse(**response_dict)

    async def get_qr_code(
        self,
        qr_code_id: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Optional[QRCodeResponse]:
        """
        Get a QR code by ID.

        Args:
            qr_code_id: QR code ID
            user_id: Optional user ID for authorization
            organization_id: Optional organization ID for multi-tenancy

        Returns:
            QR code response or None if not found
        """
        # Build query
        query: Dict[str, Any] = {"_id": ObjectId(qr_code_id)}

        if user_id:
            query["user_id"] = user_id
        if organization_id:
            query["organization_id"] = organization_id

        # Find document
        doc = await self.collection.find_one(query)

        if not doc:
            return None

        # Convert to response
        doc["id"] = str(doc["_id"])
        return QRCodeResponse(**doc)

    async def list_qr_codes(
        self,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> QRCodeListResponse:
        """
        List QR codes with filtering and pagination.

        Args:
            user_id: Filter by user ID
            organization_id: Filter by organization ID
            category: Filter by category
            tags: Filter by tags (any match)
            search: Search in name and notes
            page: Page number (1-indexed)
            page_size: Number of items per page
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)

        Returns:
            Paginated list of QR codes
        """
        # Build query
        query: Dict[str, Any] = {}

        if user_id:
            query["user_id"] = user_id
        if organization_id:
            query["organization_id"] = organization_id
        if category:
            query["category"] = category
        if tags:
            query["tags"] = {"$in": tags}
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"notes": {"$regex": search, "$options": "i"}},
                {"url": {"$regex": search, "$options": "i"}}
            ]

        # Count total
        total = await self.collection.count_documents(query)

        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size

        # Sort
        sort_direction = -1 if sort_order == "desc" else 1
        sort_spec = [(sort_by, sort_direction)]

        # Find documents
        cursor = self.collection.find(query).sort(sort_spec).skip(skip).limit(page_size)
        docs = await cursor.to_list(length=page_size)

        # Convert to responses
        qr_codes = []
        for doc in docs:
            doc["id"] = str(doc["_id"])
            qr_codes.append(QRCodeResponse(**doc))

        return QRCodeListResponse(
            qr_codes=qr_codes,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    async def update_qr_code(
        self,
        qr_code_id: str,
        data: QRCodeUpdate,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Optional[QRCodeResponse]:
        """
        Update a QR code.

        Args:
            qr_code_id: QR code ID
            data: Update data
            user_id: Optional user ID for authorization
            organization_id: Optional organization ID for multi-tenancy

        Returns:
            Updated QR code or None if not found
        """
        # Build query
        query: Dict[str, Any] = {"_id": ObjectId(qr_code_id)}

        if user_id:
            query["user_id"] = user_id
        if organization_id:
            query["organization_id"] = organization_id

        # Build update
        update_dict = data.dict(exclude_none=True)
        if not update_dict:
            # No updates provided
            return await self.get_qr_code(qr_code_id, user_id, organization_id)

        update_dict["updated_at"] = datetime.now(timezone.utc)

        # Update document
        result = await self.collection.find_one_and_update(
            query,
            {"$set": update_dict},
            return_document=True
        )

        if not result:
            return None

        # Convert to response
        result["id"] = str(result["_id"])
        return QRCodeResponse(**result)

    async def delete_qr_code(
        self,
        qr_code_id: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> bool:
        """
        Delete a QR code.

        Args:
            qr_code_id: QR code ID
            user_id: Optional user ID for authorization
            organization_id: Optional organization ID for multi-tenancy

        Returns:
            True if deleted, False if not found
        """
        # Build query
        query: Dict[str, Any] = {"_id": ObjectId(qr_code_id)}

        if user_id:
            query["user_id"] = user_id
        if organization_id:
            query["organization_id"] = organization_id

        # Delete document
        result = await self.collection.delete_one(query)

        return result.deleted_count > 0

    async def increment_download_count(
        self,
        qr_code_id: str
    ) -> Optional[QRCodeResponse]:
        """
        Increment download count for a QR code.

        Args:
            qr_code_id: QR code ID

        Returns:
            Updated QR code or None if not found
        """
        # Update document
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(qr_code_id)},
            {
                "$inc": {"download_count": 1},
                "$set": {"last_downloaded_at": datetime.now(timezone.utc)}
            },
            return_document=True
        )

        if not result:
            return None

        # Convert to response
        result["id"] = str(result["_id"])
        return QRCodeResponse(**result)

    async def get_user_statistics(
        self,
        user_id: str,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics for a user's QR codes.

        Args:
            user_id: User ID
            organization_id: Optional organization ID

        Returns:
            Statistics dictionary
        """
        query: Dict[str, Any] = {"user_id": user_id}
        if organization_id:
            query["organization_id"] = organization_id

        # Aggregate statistics
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": None,
                    "total_qr_codes": {"$sum": 1},
                    "total_downloads": {"$sum": "$download_count"},
                    "total_file_size": {"$sum": "$file_size"},
                    "qr_codes_with_logo": {
                        "$sum": {"$cond": ["$has_logo", 1, 0]}
                    },
                    "categories": {"$addToSet": "$category"}
                }
            }
        ]

        result = await self.collection.aggregate(pipeline).to_list(length=1)

        if not result:
            return {
                "total_qr_codes": 0,
                "total_downloads": 0,
                "total_file_size": 0,
                "total_file_size_mb": 0.0,
                "qr_codes_with_logo": 0,
                "categories": []
            }

        stats = result[0]
        stats["total_file_size_mb"] = stats["total_file_size"] / (1024 * 1024)
        stats.pop("_id", None)

        # Remove None from categories
        stats["categories"] = [c for c in stats["categories"] if c is not None]

        return stats

    async def bulk_delete(
        self,
        qr_code_ids: List[str],
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> int:
        """
        Delete multiple QR codes.

        Args:
            qr_code_ids: List of QR code IDs
            user_id: Optional user ID for authorization
            organization_id: Optional organization ID for multi-tenancy

        Returns:
            Number of deleted QR codes
        """
        # Build query
        query: Dict[str, Any] = {
            "_id": {"$in": [ObjectId(id) for id in qr_code_ids]}
        }

        if user_id:
            query["user_id"] = user_id
        if organization_id:
            query["organization_id"] = organization_id

        # Delete documents
        result = await self.collection.delete_many(query)

        return result.deleted_count
