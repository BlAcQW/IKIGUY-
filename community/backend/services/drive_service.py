"""
Community Drive Service - File management for African Language Community Platform.

Provides Google Drive-like file management functionality with:
- Language-organized folder structures
- File upload, download, delete, rename, move
- Folder navigation with breadcrumbs
- Search and filtering
- Sharing and permissions
- Integration with Hetzner Storage Box via shared library

Uses shared library: @shared/services/drive_service.py
"""

import os
import sys
import uuid
import mimetypes
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from bson import ObjectId
import logging

# Add shared library to path
sys.path.insert(0, '/opt/kasaai/apps')

from motor.motor_asyncio import AsyncIOMotorDatabase
from shared.storage.hetzner_storage_box import (
    HetznerStorageBox,
    StorageProtocol,
    get_storage
)

logger = logging.getLogger(__name__)


class CommunityDriveError(Exception):
    """Base exception for community drive errors."""
    pass


class FileNotFoundError(CommunityDriveError):
    """Raised when a file is not found."""
    pass


class PermissionDeniedError(CommunityDriveError):
    """Raised when user lacks permission for an operation."""
    pass


class CommunityDriveService:
    """
    Community-specific drive service for African Language Platform.

    Provides file management with language-based organization:
    - /datasets/{language_code}/...
    - /models/{language_code}/...
    - /notebooks/{language_code}/...
    - /user-uploads/{user_id}/...
    - /community-resources/{language_code}/...

    Features:
    - Hetzner Storage Box integration
    - MongoDB metadata storage
    - Language-based folder organization
    - Full file CRUD operations
    - Folder navigation and breadcrumbs
    - Search functionality
    - Sharing and permissions
    """

    # Supported file categories and their MIME types
    SUPPORTED_CATEGORIES = {
        "audio": ["audio/wav", "audio/mpeg", "audio/mp3", "audio/ogg", "audio/flac", "audio/x-wav"],
        "text": ["text/plain", "text/csv", "application/json"],
        "document": ["application/pdf", "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
        "model": ["application/octet-stream", "application/x-pytorch", "application/x-tensorflow"],
        "notebook": ["application/x-ipynb+json", "application/json"],
        "image": ["image/jpeg", "image/png", "image/gif", "image/webp"],
    }

    # Maximum file sizes by category (in bytes)
    MAX_FILE_SIZES = {
        "audio": 100 * 1024 * 1024,      # 100 MB for audio
        "text": 10 * 1024 * 1024,         # 10 MB for text
        "document": 50 * 1024 * 1024,     # 50 MB for documents
        "model": 500 * 1024 * 1024,       # 500 MB for models
        "notebook": 50 * 1024 * 1024,     # 50 MB for notebooks
        "image": 20 * 1024 * 1024,        # 20 MB for images
        "default": 50 * 1024 * 1024,      # 50 MB default
    }

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        storage: Optional[HetznerStorageBox] = None,
        base_path: str = "african-languages"
    ):
        """
        Initialize Community Drive Service.

        Args:
            db: MongoDB database instance
            storage: Hetzner storage instance (optional, will create if None)
            base_path: Base path for all storage operations
        """
        self.db = db
        self.storage = storage
        self.base_path = base_path
        self.collection = db.drive_items

    async def initialize(self):
        """Initialize storage connection and create indexes."""
        if self.storage is None:
            self.storage = await get_storage(
                protocol=StorageProtocol.SFTP,
                base_path=self.base_path
            )

        # Create indexes for efficient queries
        await self.collection.create_index([("language_code", 1), ("parent_id", 1)])
        await self.collection.create_index([("owner_id", 1)])
        await self.collection.create_index([("path", 1)])
        await self.collection.create_index([("name", "text"), ("description", "text")])
        await self.collection.create_index([("is_deleted", 1), ("deleted_at", 1)])
        await self.collection.create_index([("category", 1)])
        await self.collection.create_index([("tags", 1)])

        logger.info("Community Drive Service initialized successfully")

    # ==================== FILE OPERATIONS ====================

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        owner_id: str,
        language_code: str,
        category: str = "resource",
        description: str = "",
        tags: Optional[List[str]] = None,
        parent_id: Optional[str] = None,
        license: str = "CC-BY-4.0",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to the community drive.

        Args:
            file_content: File binary content
            filename: Original filename
            owner_id: User ID of the file owner
            language_code: Language code for organization
            category: File category (audio, text, model, notebook, etc.)
            description: File description
            tags: List of tags
            parent_id: Parent folder ID (None for category root)
            license: File license (default: CC-BY-4.0)
            metadata: Additional metadata

        Returns:
            Dict containing file metadata including ID, path, size, etc.

        Raises:
            CommunityDriveError: If upload fails
        """
        # Validate file size
        file_size = len(file_content)
        max_size = self.MAX_FILE_SIZES.get(category, self.MAX_FILE_SIZES["default"])
        if file_size > max_size:
            raise CommunityDriveError(
                f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds "
                f"maximum for {category} ({max_size / 1024 / 1024:.2f} MB)"
            )

        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)

        # Generate unique file ID
        file_id = str(uuid.uuid4())

        # Determine storage path
        storage_path = self._generate_storage_path(
            file_id=file_id,
            filename=safe_filename,
            language_code=language_code,
            category=category,
            owner_id=owner_id
        )

        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(safe_filename)
        if not mime_type:
            mime_type = "application/octet-stream"

        # Calculate file hash
        import hashlib
        file_hash = hashlib.sha256(file_content).hexdigest()

        # Upload to Hetzner storage
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        try:
            await self.storage.upload_file(
                local_path=tmp_path,
                remote_path=storage_path,
                overwrite=True
            )
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        # Create metadata document
        file_doc = {
            "_id": file_id,
            "name": safe_filename,
            "type": "file",
            "path": storage_path,
            "parent_id": parent_id,
            "language_code": language_code,
            "category": category,
            "owner_id": owner_id,
            "size": file_size,
            "mime_type": mime_type,
            "file_hash": file_hash,
            "description": description,
            "tags": tags or [],
            "license": license,
            "download_count": 0,
            "view_count": 0,
            "created_at": datetime.utcnow(),
            "modified_at": datetime.utcnow(),
            "is_deleted": False,
            "deleted_at": None,
            "is_starred": False,
            "is_public": False,
            "permissions": [],
            "share_link": None,
            "metadata": metadata or {}
        }

        # Insert into database
        await self.collection.insert_one(file_doc)

        logger.info(f"File uploaded: {safe_filename} ({file_size} bytes) for language {language_code}")

        return self._format_item(file_doc)

    async def download_file(
        self,
        file_id: str,
        user_id: str
    ) -> Tuple[bytes, str, str]:
        """
        Download a file from the drive.

        Args:
            file_id: File ID to download
            user_id: User requesting the download

        Returns:
            Tuple of (file_content, filename, mime_type)

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionDeniedError: If user lacks permission
        """
        # Get file metadata
        file_doc = await self.collection.find_one({
            "_id": file_id,
            "is_deleted": False
        })

        if not file_doc:
            raise FileNotFoundError(f"File not found: {file_id}")

        # Check permissions
        if not await self._check_permission(file_doc, user_id, "view"):
            raise PermissionDeniedError("User lacks permission to download this file")

        # Download from Hetzner
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            await self.storage.download_file(
                remote_path=file_doc['path'],
                local_path=tmp_path
            )

            with open(tmp_path, "rb") as f:
                content = f.read()

            # Increment download count
            await self.collection.update_one(
                {"_id": file_id},
                {"$inc": {"download_count": 1}}
            )

            return content, file_doc['name'], file_doc['mime_type']

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    async def delete_file(
        self,
        file_id: str,
        user_id: str,
        permanent: bool = False
    ) -> Dict[str, Any]:
        """
        Delete a file (move to trash or permanent delete).

        Args:
            file_id: File ID to delete
            user_id: User performing the deletion
            permanent: If True, permanently delete; if False, move to trash

        Returns:
            Dict with deletion status
        """
        # Get file metadata
        file_doc = await self.collection.find_one({"_id": file_id})

        if not file_doc:
            raise FileNotFoundError(f"File not found: {file_id}")

        # Check permissions
        if not await self._check_permission(file_doc, user_id, "manage"):
            raise PermissionDeniedError("User lacks permission to delete this file")

        if permanent:
            # Permanently delete from storage
            try:
                await self.storage.delete_file(file_doc['path'])
            except Exception as e:
                logger.warning(f"Failed to delete from storage: {e}")

            # Remove from database
            await self.collection.delete_one({"_id": file_id})

            logger.info(f"File permanently deleted: {file_id}")
            return {"status": "permanently_deleted", "file_id": file_id}
        else:
            # Move to trash (soft delete)
            await self.collection.update_one(
                {"_id": file_id},
                {
                    "$set": {
                        "is_deleted": True,
                        "deleted_at": datetime.utcnow(),
                        "deleted_by": user_id
                    }
                }
            )

            logger.info(f"File moved to trash: {file_id}")
            return {"status": "trashed", "file_id": file_id}

    async def rename_file(
        self,
        file_id: str,
        new_name: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Rename a file.

        Args:
            file_id: File ID to rename
            new_name: New filename
            user_id: User performing the rename

        Returns:
            Updated file metadata
        """
        # Get file metadata
        file_doc = await self.collection.find_one({
            "_id": file_id,
            "is_deleted": False
        })

        if not file_doc:
            raise FileNotFoundError(f"File not found: {file_id}")

        # Check permissions
        if not await self._check_permission(file_doc, user_id, "edit"):
            raise PermissionDeniedError("User lacks permission to rename this file")

        # Sanitize new name
        safe_name = self._sanitize_filename(new_name)

        # Update in database
        await self.collection.update_one(
            {"_id": file_id},
            {
                "$set": {
                    "name": safe_name,
                    "modified_at": datetime.utcnow()
                }
            }
        )

        # Get updated document
        updated_doc = await self.collection.find_one({"_id": file_id})

        logger.info(f"File renamed: {file_id} -> {safe_name}")
        return self._format_item(updated_doc)

    async def get_file_info(
        self,
        file_id: str,
        user_id: str,
        increment_views: bool = False
    ) -> Dict[str, Any]:
        """
        Get file metadata and information.

        Args:
            file_id: File ID
            user_id: User requesting info
            increment_views: Whether to increment view count

        Returns:
            File metadata dictionary
        """
        file_doc = await self.collection.find_one({
            "_id": file_id,
            "is_deleted": False
        })

        if not file_doc:
            raise FileNotFoundError(f"File not found: {file_id}")

        # Check permissions
        if not await self._check_permission(file_doc, user_id, "view"):
            raise PermissionDeniedError("User lacks permission to view this file")

        if increment_views:
            await self.collection.update_one(
                {"_id": file_id},
                {"$inc": {"view_count": 1}}
            )
            file_doc["view_count"] = file_doc.get("view_count", 0) + 1

        return self._format_item(file_doc)

    # ==================== FOLDER OPERATIONS ====================

    async def create_folder(
        self,
        name: str,
        owner_id: str,
        language_code: str,
        category: str = "resource",
        parent_id: Optional[str] = None,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Create a new folder.

        Args:
            name: Folder name
            owner_id: User ID of the folder owner
            language_code: Language code for organization
            category: File category (for organizing)
            parent_id: Parent folder ID (None for root)
            description: Folder description

        Returns:
            Folder metadata dictionary
        """
        # Sanitize folder name
        safe_name = self._sanitize_filename(name)

        # Verify parent exists (if not None)
        if parent_id:
            parent_doc = await self.collection.find_one({
                "_id": parent_id,
                "type": "folder",
                "is_deleted": False
            })
            if not parent_doc:
                raise FileNotFoundError(f"Parent folder not found: {parent_id}")

        # Create folder document
        folder_id = str(uuid.uuid4())
        storage_path = self._generate_folder_path(
            folder_id=folder_id,
            name=safe_name,
            language_code=language_code,
            category=category
        )

        folder_doc = {
            "_id": folder_id,
            "name": safe_name,
            "type": "folder",
            "path": storage_path,
            "parent_id": parent_id,
            "language_code": language_code,
            "category": category,
            "owner_id": owner_id,
            "description": description,
            "size": 0,
            "mime_type": "application/vnd.community.folder",
            "created_at": datetime.utcnow(),
            "modified_at": datetime.utcnow(),
            "is_deleted": False,
            "deleted_at": None,
            "is_starred": False,
            "is_public": False,
            "permissions": [],
            "share_link": None
        }

        # Insert into database
        await self.collection.insert_one(folder_doc)

        # Create directory in storage
        try:
            await self.storage.create_directory(storage_path)
        except Exception as e:
            logger.warning(f"Failed to create storage directory: {e}")

        logger.info(f"Folder created: {safe_name} at {storage_path}")
        return self._format_item(folder_doc)

    async def get_folder_contents(
        self,
        folder_id: Optional[str],
        user_id: str,
        language_code: Optional[str] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "name",
        sort_order: str = "asc",
        include_subfolders: bool = True
    ) -> Dict[str, Any]:
        """
        Get contents of a folder.

        Args:
            folder_id: Folder ID (None for root)
            user_id: User requesting contents
            language_code: Filter by language code
            category: Filter by category
            skip: Number of items to skip (pagination)
            limit: Max number of items to return
            sort_by: Field to sort by (name, modified_at, size, type)
            sort_order: Sort order (asc, desc)
            include_subfolders: Whether to include folders in results

        Returns:
            Dict with items list and pagination info
        """
        # Build query
        query = {
            "parent_id": folder_id,
            "is_deleted": False
        }

        if language_code:
            query["language_code"] = language_code

        if category:
            query["category"] = category

        if not include_subfolders:
            query["type"] = "file"

        # Determine sort direction
        sort_direction = 1 if sort_order == "asc" else -1

        # Query items (folders first, then files)
        cursor = self.collection.find(query).sort([
            ("type", -1),  # folders first
            (sort_by, sort_direction)
        ]).skip(skip).limit(limit)

        items = await cursor.to_list(length=limit)

        # Get total count
        total_count = await self.collection.count_documents(query)

        # Filter items by permissions and format
        accessible_items = []
        for item in items:
            if await self._check_permission(item, user_id, "view"):
                accessible_items.append(self._format_item(item))

        return {
            "items": accessible_items,
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + len(accessible_items)) < total_count
        }

    async def get_breadcrumbs(
        self,
        folder_id: Optional[str],
        language_code: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Get breadcrumb trail for a folder.

        Args:
            folder_id: Folder ID (None for root)
            language_code: Language code context

        Returns:
            List of breadcrumb items from root to current folder
        """
        breadcrumbs = [{"id": None, "name": "Community Drive"}]

        if language_code:
            breadcrumbs.append({"id": f"lang_{language_code}", "name": language_code.upper()})

        if not folder_id:
            return breadcrumbs

        current_id = folder_id

        # Traverse up to root
        while current_id:
            folder_doc = await self.collection.find_one({
                "_id": current_id,
                "type": "folder"
            })

            if not folder_doc:
                break

            breadcrumbs.insert(len(breadcrumbs), {
                "id": folder_doc["_id"],
                "name": folder_doc["name"]
            })

            current_id = folder_doc.get("parent_id")

        return breadcrumbs

    # ==================== SEARCH & FILTER ====================

    async def search_files(
        self,
        query: str,
        user_id: str,
        language_code: Optional[str] = None,
        category: Optional[str] = None,
        file_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Search files and folders.

        Args:
            query: Search query string
            user_id: User performing search
            language_code: Filter by language
            category: Filter by category
            file_type: Filter by file type (file/folder)
            tags: Filter by tags
            date_from: Filter by modified date (from)
            date_to: Filter by modified date (to)
            skip: Pagination skip
            limit: Pagination limit

        Returns:
            Dict with search results and pagination info
        """
        # Build search query
        search_query = {
            "is_deleted": False
        }

        # Text search
        if query:
            search_query["$text"] = {"$search": query}

        # Filter by language
        if language_code:
            search_query["language_code"] = language_code

        # Filter by category
        if category:
            search_query["category"] = category

        # Filter by type
        if file_type:
            search_query["type"] = file_type

        # Filter by tags
        if tags:
            search_query["tags"] = {"$all": tags}

        # Filter by date range
        if date_from or date_to:
            date_filter = {}
            if date_from:
                date_filter["$gte"] = date_from
            if date_to:
                date_filter["$lte"] = date_to
            search_query["modified_at"] = date_filter

        # Execute search
        cursor = self.collection.find(search_query).skip(skip).limit(limit)
        items = await cursor.to_list(length=limit)

        # Get total count
        total_count = await self.collection.count_documents(search_query)

        # Filter by permissions
        accessible_items = []
        for item in items:
            if await self._check_permission(item, user_id, "view"):
                accessible_items.append(self._format_item(item))

        return {
            "items": accessible_items,
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "query": query
        }

    async def get_files_by_language(
        self,
        language_code: str,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all files for a specific language.

        Args:
            language_code: Language code
            user_id: User ID
            category: Optional category filter
            limit: Max number of files to return

        Returns:
            List of files
        """
        query = {
            "language_code": language_code,
            "type": "file",
            "is_deleted": False
        }

        if category:
            query["category"] = category

        cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
        items = await cursor.to_list(length=limit)

        # Filter by permissions
        accessible_items = []
        for item in items:
            if await self._check_permission(item, user_id, "view"):
                accessible_items.append(self._format_item(item))

        return accessible_items

    async def get_recent_files(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recently modified files for a user.

        Args:
            user_id: User ID
            limit: Max number of files to return

        Returns:
            List of recent files
        """
        cursor = self.collection.find({
            "type": "file",
            "is_deleted": False,
            "$or": [
                {"owner_id": user_id},
                {"is_public": True},
                {"permissions.user_id": user_id}
            ]
        }).sort("modified_at", -1).limit(limit)

        items = await cursor.to_list(length=limit)

        return [self._format_item(item) for item in items]

    async def get_user_files(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get all files owned by a user.

        Args:
            user_id: User ID
            skip: Pagination skip
            limit: Pagination limit

        Returns:
            Dict with files and pagination info
        """
        query = {
            "owner_id": user_id,
            "type": "file",
            "is_deleted": False
        }

        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        items = await cursor.to_list(length=limit)

        total_count = await self.collection.count_documents(query)

        return {
            "items": [self._format_item(item) for item in items],
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + len(items)) < total_count
        }

    # ==================== SHARING ====================

    async def toggle_public(
        self,
        file_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Toggle public visibility of a file.

        Args:
            file_id: File ID
            user_id: User ID

        Returns:
            Updated file metadata
        """
        file_doc = await self.collection.find_one({
            "_id": file_id,
            "is_deleted": False
        })

        if not file_doc:
            raise FileNotFoundError(f"File not found: {file_id}")

        if not await self._check_permission(file_doc, user_id, "manage"):
            raise PermissionDeniedError("User lacks permission to modify this file")

        new_public_status = not file_doc.get("is_public", False)

        await self.collection.update_one(
            {"_id": file_id},
            {"$set": {"is_public": new_public_status, "modified_at": datetime.utcnow()}}
        )

        updated_doc = await self.collection.find_one({"_id": file_id})
        return self._format_item(updated_doc)

    async def toggle_star(
        self,
        file_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Toggle star status of a file.

        Args:
            file_id: File ID
            user_id: User ID

        Returns:
            Updated file metadata
        """
        file_doc = await self.collection.find_one({
            "_id": file_id,
            "is_deleted": False
        })

        if not file_doc:
            raise FileNotFoundError(f"File not found: {file_id}")

        if not await self._check_permission(file_doc, user_id, "view"):
            raise PermissionDeniedError("User lacks permission to star this file")

        new_star_status = not file_doc.get("is_starred", False)

        await self.collection.update_one(
            {"_id": file_id},
            {"$set": {"is_starred": new_star_status}}
        )

        updated_doc = await self.collection.find_one({"_id": file_id})
        return self._format_item(updated_doc)

    # ==================== STATISTICS ====================

    async def get_storage_stats(
        self,
        user_id: Optional[str] = None,
        language_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get storage statistics.

        Args:
            user_id: Filter by user (optional)
            language_code: Filter by language (optional)

        Returns:
            Dict with storage statistics
        """
        query = {"type": "file", "is_deleted": False}

        if user_id:
            query["owner_id"] = user_id

        if language_code:
            query["language_code"] = language_code

        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$category",
                "count": {"$sum": 1},
                "total_size": {"$sum": "$size"},
                "total_downloads": {"$sum": "$download_count"}
            }}
        ]

        results = await self.collection.aggregate(pipeline).to_list(length=None)

        # Calculate totals
        total_files = sum(r["count"] for r in results)
        total_size = sum(r["total_size"] for r in results)
        total_downloads = sum(r["total_downloads"] for r in results)

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_downloads": total_downloads,
            "by_category": {r["_id"]: {
                "count": r["count"],
                "size_bytes": r["total_size"],
                "downloads": r["total_downloads"]
            } for r in results}
        }

    # ==================== UTILITY METHODS ====================

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to remove dangerous characters."""
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        safe_name = filename
        for char in dangerous_chars:
            safe_name = safe_name.replace(char, '_')
        return safe_name.strip()

    def _generate_storage_path(
        self,
        file_id: str,
        filename: str,
        language_code: str,
        category: str,
        owner_id: str
    ) -> str:
        """Generate storage path for a file."""
        # Structure: {category}/{language_code}/{owner_id}/{file_id}_{filename}
        return f"{category}/{language_code}/{owner_id}/{file_id}_{filename}"

    def _generate_folder_path(
        self,
        folder_id: str,
        name: str,
        language_code: str,
        category: str
    ) -> str:
        """Generate storage path for a folder."""
        return f"{category}/{language_code}/{folder_id}_{name}"

    async def _check_permission(
        self,
        item_doc: Dict[str, Any],
        user_id: str,
        required_role: str
    ) -> bool:
        """
        Check if user has required permission on an item.

        Permission hierarchy: view < edit < manage
        """
        # Owner has all permissions
        if item_doc.get("owner_id") == user_id:
            return True

        # Public files can be viewed by anyone
        if item_doc.get("is_public", False) and required_role == "view":
            return True

        # Check explicit permissions
        permissions = item_doc.get("permissions", [])
        role_hierarchy = {"view": 1, "edit": 2, "manage": 3}
        required_level = role_hierarchy.get(required_role, 0)

        for perm in permissions:
            if perm.get("user_id") == user_id:
                user_level = role_hierarchy.get(perm.get("role"), 0)
                return user_level >= required_level

        return False

    def _format_item(self, item_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Format database item for API response."""
        return {
            "id": str(item_doc["_id"]),
            "name": item_doc["name"],
            "type": item_doc["type"],
            "path": item_doc.get("path"),
            "parent_id": item_doc.get("parent_id"),
            "language_code": item_doc.get("language_code"),
            "category": item_doc.get("category"),
            "size": item_doc.get("size", 0),
            "mime_type": item_doc.get("mime_type"),
            "description": item_doc.get("description", ""),
            "tags": item_doc.get("tags", []),
            "license": item_doc.get("license"),
            "download_count": item_doc.get("download_count", 0),
            "view_count": item_doc.get("view_count", 0),
            "created_at": item_doc["created_at"].isoformat() if item_doc.get("created_at") else None,
            "modified_at": item_doc["modified_at"].isoformat() if item_doc.get("modified_at") else None,
            "owner_id": item_doc.get("owner_id"),
            "is_starred": item_doc.get("is_starred", False),
            "is_public": item_doc.get("is_public", False),
            "is_deleted": item_doc.get("is_deleted", False),
            "permissions": item_doc.get("permissions", []),
            "share_link": item_doc.get("share_link"),
            "metadata": item_doc.get("metadata", {})
        }


# ==================== FACTORY FUNCTION ====================

_drive_service_instance: Optional[CommunityDriveService] = None


async def get_community_drive_service(
    db: AsyncIOMotorDatabase
) -> CommunityDriveService:
    """
    Get or create community drive service instance.

    Args:
        db: MongoDB database instance

    Returns:
        Initialized CommunityDriveService instance
    """
    global _drive_service_instance

    if _drive_service_instance is None:
        _drive_service_instance = CommunityDriveService(db)
        await _drive_service_instance.initialize()

    return _drive_service_instance
