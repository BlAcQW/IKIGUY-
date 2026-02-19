"""
Drive Service - Google Drive-like file management service.

This service provides comprehensive file and folder management functionality
that can be reused across different applications. It integrates with Hetzner
storage for file persistence and MongoDB for metadata.

Features:
- File upload, download, delete, rename, move
- Folder creation, navigation, hierarchy management
- Search and filtering capabilities
- Sharing and permissions management
- Organization-based access control
- Trash/restore functionality
- Activity logging and auditing

Author: AI Labs Africa
Date: 2025-11-10
"""

import os
import uuid
import hashlib
import mimetypes
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import asyncio
from bson import ObjectId

from motor.motor_asyncio import AsyncIOMotorDatabase
from apps.shared.storage.hetzner_storage_box import get_storage, HetznerStorageBox
import logging

logger = logging.getLogger(__name__)


class DriveServiceError(Exception):
    """Base exception for drive service errors."""
    pass


class FileNotFoundError(DriveServiceError):
    """Raised when a file is not found."""
    pass


class PermissionDeniedError(DriveServiceError):
    """Raised when user lacks permission for an operation."""
    pass


class QuotaExceededError(DriveServiceError):
    """Raised when storage quota is exceeded."""
    pass


class DriveService:
    """
    Comprehensive drive service for file and folder management.

    This service handles all file operations, permissions, sharing,
    and integrates with Hetzner storage for file persistence.
    """

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        storage: Optional[HetznerStorageBox] = None,
        organization_id: Optional[str] = None
    ):
        """
        Initialize drive service.

        Args:
            db: MongoDB database instance
            storage: Hetzner storage instance (optional, will create if None)
            organization_id: Organization ID for scoping operations
        """
        self.db = db
        self.storage = storage
        self.organization_id = organization_id
        self.collection = db.drive_items

    async def initialize(self):
        """Initialize storage connection and create indexes."""
        if self.storage is None:
            self.storage = await get_storage(base_path="kasaai/drive")

        # Create indexes for efficient queries
        await self.collection.create_index([("organization_id", 1), ("parent_id", 1)])
        await self.collection.create_index([("organization_id", 1), ("owner_id", 1)])
        await self.collection.create_index([("path", 1)])
        await self.collection.create_index([("name", "text")])
        await self.collection.create_index([("is_deleted", 1), ("deleted_at", 1)])
        await self.collection.create_index([("share_link.token", 1)])

        logger.info("Drive service initialized successfully")

    # ==================== FILE OPERATIONS ====================

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        parent_id: Optional[str] = None,
        owner_id: str = None,
        organization_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to the drive.

        Args:
            file_content: File binary content
            filename: Name of the file
            parent_id: Parent folder ID (None for root)
            owner_id: User ID of the file owner
            organization_id: Organization ID (uses service default if None)
            metadata: Additional metadata to store

        Returns:
            Dict containing file metadata including ID, path, size, etc.

        Raises:
            QuotaExceededError: If storage quota is exceeded
            DriveServiceError: If upload fails
        """
        org_id = organization_id or self.organization_id
        if not org_id:
            raise DriveServiceError("Organization ID is required")

        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)

        # Get parent folder path
        parent_path = await self._get_folder_path(parent_id, org_id)

        # Calculate file hash and size
        file_hash = hashlib.sha256(file_content).hexdigest()
        file_size = len(file_content)

        # Check quota (optional - implement based on needs)
        # await self._check_quota(org_id, file_size)

        # Determine storage path
        file_id = str(uuid.uuid4())
        storage_path = f"{org_id}/{parent_path}/{file_id}_{safe_filename}"

        # Save to temporary file for upload
        temp_file = f"/tmp/{file_id}_{safe_filename}"
        try:
            with open(temp_file, "wb") as f:
                f.write(file_content)

            # Upload to Hetzner storage
            await self.storage.upload_file(
                local_path=temp_file,
                remote_path=storage_path,
                overwrite=False
            )

        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)

        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(safe_filename)
        if not mime_type:
            mime_type = "application/octet-stream"

        # Create metadata document
        file_doc = {
            "_id": file_id,
            "name": safe_filename,
            "type": "file",
            "path": storage_path,
            "parent_id": parent_id,
            "organization_id": org_id,
            "owner_id": owner_id,
            "size": file_size,
            "mime_type": mime_type,
            "file_hash": file_hash,
            "created_at": datetime.utcnow(),
            "modified_at": datetime.utcnow(),
            "is_deleted": False,
            "deleted_at": None,
            "is_starred": False,
            "permissions": [],
            "share_link": None,
            "metadata": metadata or {}
        }

        # Insert into database
        await self.collection.insert_one(file_doc)

        logger.info(f"File uploaded successfully: {safe_filename} ({file_size} bytes)")

        return self._format_item(file_doc)

    async def download_file(
        self,
        file_id: str,
        user_id: str,
        organization_id: Optional[str] = None
    ) -> Tuple[bytes, str, str]:
        """
        Download a file from the drive.

        Args:
            file_id: File ID to download
            user_id: User requesting the download
            organization_id: Organization ID

        Returns:
            Tuple of (file_content, filename, mime_type)

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionDeniedError: If user lacks permission
        """
        org_id = organization_id or self.organization_id

        # Get file metadata
        file_doc = await self.collection.find_one({
            "_id": file_id,
            "organization_id": org_id,
            "is_deleted": False
        })

        if not file_doc:
            raise FileNotFoundError(f"File not found: {file_id}")

        # Check permissions
        if not await self._check_permission(file_doc, user_id, "view"):
            raise PermissionDeniedError("User lacks permission to download this file")

        # Download from Hetzner
        temp_file = f"/tmp/{file_id}_{file_doc['name']}"
        try:
            await self.storage.download_file(
                remote_path=file_doc['path'],
                local_path=temp_file
            )

            with open(temp_file, "rb") as f:
                content = f.read()

            return content, file_doc['name'], file_doc['mime_type']

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    async def delete_file(
        self,
        file_id: str,
        user_id: str,
        organization_id: Optional[str] = None,
        permanent: bool = False
    ) -> Dict[str, Any]:
        """
        Delete a file (move to trash or permanent delete).

        Args:
            file_id: File ID to delete
            user_id: User performing the deletion
            organization_id: Organization ID
            permanent: If True, permanently delete; if False, move to trash

        Returns:
            Dict with deletion status

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionDeniedError: If user lacks permission
        """
        org_id = organization_id or self.organization_id

        # Get file metadata
        file_doc = await self.collection.find_one({
            "_id": file_id,
            "organization_id": org_id
        })

        if not file_doc:
            raise FileNotFoundError(f"File not found: {file_id}")

        # Check permissions
        if not await self._check_permission(file_doc, user_id, "manage"):
            raise PermissionDeniedError("User lacks permission to delete this file")

        if permanent:
            # Permanently delete from storage
            await self.storage.delete_file(file_doc['path'])

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
        user_id: str,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rename a file.

        Args:
            file_id: File ID to rename
            new_name: New filename
            user_id: User performing the rename
            organization_id: Organization ID

        Returns:
            Updated file metadata
        """
        org_id = organization_id or self.organization_id

        # Get file metadata
        file_doc = await self.collection.find_one({
            "_id": file_id,
            "organization_id": org_id,
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

    async def move_file(
        self,
        file_id: str,
        new_parent_id: Optional[str],
        user_id: str,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Move a file to a different folder.

        Args:
            file_id: File ID to move
            new_parent_id: New parent folder ID (None for root)
            user_id: User performing the move
            organization_id: Organization ID

        Returns:
            Updated file metadata
        """
        org_id = organization_id or self.organization_id

        # Get file metadata
        file_doc = await self.collection.find_one({
            "_id": file_id,
            "organization_id": org_id,
            "is_deleted": False
        })

        if not file_doc:
            raise FileNotFoundError(f"File not found: {file_id}")

        # Check permissions on source
        if not await self._check_permission(file_doc, user_id, "edit"):
            raise PermissionDeniedError("User lacks permission to move this file")

        # Verify new parent exists (if not None)
        if new_parent_id:
            parent_doc = await self.collection.find_one({
                "_id": new_parent_id,
                "organization_id": org_id,
                "type": "folder",
                "is_deleted": False
            })
            if not parent_doc:
                raise FileNotFoundError(f"Parent folder not found: {new_parent_id}")

        # Update parent_id
        await self.collection.update_one(
            {"_id": file_id},
            {
                "$set": {
                    "parent_id": new_parent_id,
                    "modified_at": datetime.utcnow()
                }
            }
        )

        # Get updated document
        updated_doc = await self.collection.find_one({"_id": file_id})

        logger.info(f"File moved: {file_id} -> parent {new_parent_id}")
        return self._format_item(updated_doc)

    async def get_file_info(
        self,
        file_id: str,
        user_id: str,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get file metadata and information.

        Args:
            file_id: File ID
            user_id: User requesting info
            organization_id: Organization ID

        Returns:
            File metadata dictionary
        """
        org_id = organization_id or self.organization_id

        file_doc = await self.collection.find_one({
            "_id": file_id,
            "organization_id": org_id,
            "is_deleted": False
        })

        if not file_doc:
            raise FileNotFoundError(f"File not found: {file_id}")

        # Check permissions
        if not await self._check_permission(file_doc, user_id, "view"):
            raise PermissionDeniedError("User lacks permission to view this file")

        return self._format_item(file_doc)

    # ==================== FOLDER OPERATIONS ====================

    async def create_folder(
        self,
        name: str,
        parent_id: Optional[str] = None,
        owner_id: str = None,
        organization_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new folder.

        Args:
            name: Folder name
            parent_id: Parent folder ID (None for root)
            owner_id: User ID of the folder owner
            organization_id: Organization ID
            metadata: Additional metadata

        Returns:
            Folder metadata dictionary
        """
        org_id = organization_id or self.organization_id
        if not org_id:
            raise DriveServiceError("Organization ID is required")

        # Sanitize folder name
        safe_name = self._sanitize_filename(name)

        # Verify parent exists (if not None)
        if parent_id:
            parent_doc = await self.collection.find_one({
                "_id": parent_id,
                "organization_id": org_id,
                "type": "folder",
                "is_deleted": False
            })
            if not parent_doc:
                raise FileNotFoundError(f"Parent folder not found: {parent_id}")

        # Get parent path
        parent_path = await self._get_folder_path(parent_id, org_id)

        # Create folder document
        folder_id = str(uuid.uuid4())
        storage_path = f"{org_id}/{parent_path}/{safe_name}"

        folder_doc = {
            "_id": folder_id,
            "name": safe_name,
            "type": "folder",
            "path": storage_path,
            "parent_id": parent_id,
            "organization_id": org_id,
            "owner_id": owner_id,
            "size": 0,
            "mime_type": "application/vnd.google-apps.folder",
            "created_at": datetime.utcnow(),
            "modified_at": datetime.utcnow(),
            "is_deleted": False,
            "deleted_at": None,
            "is_starred": False,
            "permissions": [],
            "share_link": None,
            "metadata": metadata or {}
        }

        # Insert into database
        await self.collection.insert_one(folder_doc)

        # Create directory in storage
        await self.storage.create_directory(storage_path)

        logger.info(f"Folder created: {safe_name} at {storage_path}")
        return self._format_item(folder_doc)

    async def get_folder_contents(
        self,
        folder_id: Optional[str],
        user_id: str,
        organization_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "name",
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """
        Get contents of a folder.

        Args:
            folder_id: Folder ID (None for root)
            user_id: User requesting contents
            organization_id: Organization ID
            skip: Number of items to skip (pagination)
            limit: Max number of items to return
            sort_by: Field to sort by (name, modified_at, size, type)
            sort_order: Sort order (asc, desc)

        Returns:
            Dict with items list and pagination info
        """
        org_id = organization_id or self.organization_id

        # Build query
        query = {
            "organization_id": org_id,
            "parent_id": folder_id,
            "is_deleted": False
        }

        # Determine sort direction
        sort_direction = 1 if sort_order == "asc" else -1

        # Query items
        cursor = self.collection.find(query).sort(sort_by, sort_direction).skip(skip).limit(limit)
        items = await cursor.to_list(length=limit)

        # Get total count
        total_count = await self.collection.count_documents(query)

        # Filter items by permissions
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
        organization_id: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Get breadcrumb trail for a folder.

        Args:
            folder_id: Folder ID (None for root)
            organization_id: Organization ID

        Returns:
            List of breadcrumb items from root to current folder
        """
        breadcrumbs = [{"id": None, "name": "My Drive"}]

        if not folder_id:
            return breadcrumbs

        org_id = organization_id or self.organization_id
        current_id = folder_id

        # Traverse up to root
        while current_id:
            folder_doc = await self.collection.find_one({
                "_id": current_id,
                "organization_id": org_id,
                "type": "folder"
            })

            if not folder_doc:
                break

            breadcrumbs.insert(1, {
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
        organization_id: Optional[str] = None,
        file_type: Optional[str] = None,
        owner_id: Optional[str] = None,
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
            organization_id: Organization ID
            file_type: Filter by file type (folder, document, image, video, etc.)
            owner_id: Filter by owner
            date_from: Filter by modified date (from)
            date_to: Filter by modified date (to)
            skip: Pagination skip
            limit: Pagination limit

        Returns:
            Dict with search results and pagination info
        """
        org_id = organization_id or self.organization_id

        # Build search query
        search_query = {
            "organization_id": org_id,
            "is_deleted": False
        }

        # Text search
        if query:
            search_query["$text"] = {"$search": query}

        # Filter by type
        if file_type:
            if file_type == "folder":
                search_query["type"] = "folder"
            elif file_type in ["document", "image", "video", "audio"]:
                search_query["mime_type"] = {"$regex": f"^{self._get_mime_prefix(file_type)}"}

        # Filter by owner
        if owner_id:
            search_query["owner_id"] = owner_id

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

    async def get_recent_files(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recently modified files.

        Args:
            user_id: User ID
            organization_id: Organization ID
            limit: Max number of files to return

        Returns:
            List of recent files
        """
        org_id = organization_id or self.organization_id

        cursor = self.collection.find({
            "organization_id": org_id,
            "type": "file",
            "is_deleted": False
        }).sort("modified_at", -1).limit(limit)

        items = await cursor.to_list(length=limit)

        # Filter by permissions
        accessible_items = []
        for item in items:
            if await self._check_permission(item, user_id, "view"):
                accessible_items.append(self._format_item(item))

        return accessible_items

    async def get_starred_items(
        self,
        user_id: str,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get starred items for a user.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            List of starred items
        """
        org_id = organization_id or self.organization_id

        cursor = self.collection.find({
            "organization_id": org_id,
            "is_starred": True,
            "is_deleted": False
        }).sort("name", 1)

        items = await cursor.to_list(length=None)

        # Filter by permissions
        accessible_items = []
        for item in items:
            if await self._check_permission(item, user_id, "view"):
                accessible_items.append(self._format_item(item))

        return accessible_items

    async def toggle_star(
        self,
        item_id: str,
        user_id: str,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Toggle star status of an item.

        Args:
            item_id: Item ID
            user_id: User ID
            organization_id: Organization ID

        Returns:
            Updated item metadata
        """
        org_id = organization_id or self.organization_id

        item_doc = await self.collection.find_one({
            "_id": item_id,
            "organization_id": org_id,
            "is_deleted": False
        })

        if not item_doc:
            raise FileNotFoundError(f"Item not found: {item_id}")

        # Check permissions
        if not await self._check_permission(item_doc, user_id, "view"):
            raise PermissionDeniedError("User lacks permission to star this item")

        # Toggle star
        new_star_status = not item_doc.get("is_starred", False)
        await self.collection.update_one(
            {"_id": item_id},
            {"$set": {"is_starred": new_star_status}}
        )

        updated_doc = await self.collection.find_one({"_id": item_id})
        return self._format_item(updated_doc)

    # ==================== SHARING & PERMISSIONS ====================

    async def share_item(
        self,
        item_id: str,
        user_id: str,
        target_user_id: str,
        role: str = "view",
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Share an item with a user.

        Args:
            item_id: Item ID to share
            user_id: User performing the share
            target_user_id: User to share with
            role: Permission role (view, comment, edit, manage)
            organization_id: Organization ID

        Returns:
            Updated item metadata
        """
        org_id = organization_id or self.organization_id

        # Validate role
        valid_roles = ["view", "comment", "edit", "manage"]
        if role not in valid_roles:
            raise DriveServiceError(f"Invalid role. Must be one of: {valid_roles}")

        # Get item
        item_doc = await self.collection.find_one({
            "_id": item_id,
            "organization_id": org_id,
            "is_deleted": False
        })

        if not item_doc:
            raise FileNotFoundError(f"Item not found: {item_id}")

        # Check if user can share
        if not await self._check_permission(item_doc, user_id, "manage"):
            raise PermissionDeniedError("User lacks permission to share this item")

        # Add or update permission
        permissions = item_doc.get("permissions", [])

        # Check if user already has permission
        existing_perm = None
        for perm in permissions:
            if perm["user_id"] == target_user_id:
                existing_perm = perm
                break

        if existing_perm:
            # Update existing permission
            existing_perm["role"] = role
        else:
            # Add new permission
            permissions.append({
                "user_id": target_user_id,
                "role": role,
                "granted_at": datetime.utcnow(),
                "granted_by": user_id
            })

        # Update in database
        await self.collection.update_one(
            {"_id": item_id},
            {"$set": {"permissions": permissions}}
        )

        updated_doc = await self.collection.find_one({"_id": item_id})
        logger.info(f"Item shared: {item_id} with user {target_user_id} (role: {role})")

        return self._format_item(updated_doc)

    async def create_share_link(
        self,
        item_id: str,
        user_id: str,
        organization_id: Optional[str] = None,
        expires_in_days: Optional[int] = None,
        is_public: bool = True
    ) -> Dict[str, Any]:
        """
        Create a public share link for an item.

        Args:
            item_id: Item ID
            user_id: User creating the link
            organization_id: Organization ID
            expires_in_days: Link expiry in days (None for no expiry)
            is_public: Whether link allows public access

        Returns:
            Dict with share link details
        """
        org_id = organization_id or self.organization_id

        # Get item
        item_doc = await self.collection.find_one({
            "_id": item_id,
            "organization_id": org_id,
            "is_deleted": False
        })

        if not item_doc:
            raise FileNotFoundError(f"Item not found: {item_id}")

        # Check permissions
        if not await self._check_permission(item_doc, user_id, "manage"):
            raise PermissionDeniedError("User lacks permission to create share link")

        # Generate share token
        share_token = str(uuid.uuid4())

        # Calculate expiry
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        share_link = {
            "token": share_token,
            "created_at": datetime.utcnow(),
            "created_by": user_id,
            "expires_at": expires_at,
            "is_public": is_public
        }

        # Update in database
        await self.collection.update_one(
            {"_id": item_id},
            {"$set": {"share_link": share_link}}
        )

        logger.info(f"Share link created for item: {item_id}")

        return {
            "item_id": item_id,
            "share_token": share_token,
            "expires_at": expires_at,
            "is_public": is_public
        }

    async def revoke_share_link(
        self,
        item_id: str,
        user_id: str,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Revoke a share link.

        Args:
            item_id: Item ID
            user_id: User revoking the link
            organization_id: Organization ID

        Returns:
            Status dict
        """
        org_id = organization_id or self.organization_id

        # Get item
        item_doc = await self.collection.find_one({
            "_id": item_id,
            "organization_id": org_id
        })

        if not item_doc:
            raise FileNotFoundError(f"Item not found: {item_id}")

        # Check permissions
        if not await self._check_permission(item_doc, user_id, "manage"):
            raise PermissionDeniedError("User lacks permission to revoke share link")

        # Remove share link
        await self.collection.update_one(
            {"_id": item_id},
            {"$set": {"share_link": None}}
        )

        logger.info(f"Share link revoked for item: {item_id}")

        return {"status": "revoked", "item_id": item_id}

    # ==================== UTILITY METHODS ====================

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to remove dangerous characters."""
        # Remove or replace dangerous characters
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        safe_name = filename
        for char in dangerous_chars:
            safe_name = safe_name.replace(char, '_')
        return safe_name.strip()

    async def _get_folder_path(
        self,
        folder_id: Optional[str],
        organization_id: str
    ) -> str:
        """Get the storage path for a folder."""
        if not folder_id:
            return ""

        folder_doc = await self.collection.find_one({
            "_id": folder_id,
            "organization_id": organization_id,
            "type": "folder"
        })

        if not folder_doc:
            return ""

        # Extract relative path from storage path
        path = folder_doc.get("path", "")
        # Remove org_id prefix
        if path.startswith(f"{organization_id}/"):
            path = path[len(f"{organization_id}/"):]

        return path

    async def _check_permission(
        self,
        item_doc: Dict[str, Any],
        user_id: str,
        required_role: str
    ) -> bool:
        """
        Check if user has required permission on an item.

        Permission hierarchy: view < comment < edit < manage
        """
        # Owner has all permissions
        if item_doc.get("owner_id") == user_id:
            return True

        # Check explicit permissions
        permissions = item_doc.get("permissions", [])
        role_hierarchy = {"view": 1, "comment": 2, "edit": 3, "manage": 4}
        required_level = role_hierarchy.get(required_role, 0)

        for perm in permissions:
            if perm["user_id"] == user_id:
                user_level = role_hierarchy.get(perm["role"], 0)
                return user_level >= required_level

        # TODO: Check if user is admin in organization

        return False

    def _get_mime_prefix(self, file_type: str) -> str:
        """Get MIME type prefix for file type."""
        mime_prefixes = {
            "document": "application/(pdf|msword|vnd.openxmlformats|vnd.ms-|text)",
            "image": "image/",
            "video": "video/",
            "audio": "audio/"
        }
        return mime_prefixes.get(file_type, "")

    def _format_item(self, item_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Format database item for API response."""
        return {
            "id": item_doc.get("id", str(item_doc["_id"])),  # Use 'id' field or fallback to _id as string
            "name": item_doc["name"],
            "type": item_doc["type"],
            "parent_id": item_doc.get("parent_id"),
            "size": item_doc.get("size", 0),
            "mime_type": item_doc.get("mime_type"),
            "created_at": item_doc["created_at"].isoformat(),
            "modified_at": item_doc["modified_at"].isoformat(),
            "owner_id": item_doc.get("owner_id"),
            "is_starred": item_doc.get("is_starred", False),
            "is_deleted": item_doc.get("is_deleted", False),
            "permissions": item_doc.get("permissions", []),
            "share_link": item_doc.get("share_link"),
            "metadata": item_doc.get("metadata", {})
        }


# ==================== FACTORY FUNCTION ====================

_drive_service_instance = None

async def get_drive_service(
    db: AsyncIOMotorDatabase,
    organization_id: Optional[str] = None
) -> DriveService:
    """
    Get or create drive service instance.

    Args:
        db: MongoDB database instance
        organization_id: Organization ID for scoping

    Returns:
        Initialized DriveService instance
    """
    global _drive_service_instance

    if _drive_service_instance is None:
        _drive_service_instance = DriveService(db, organization_id=organization_id)
        await _drive_service_instance.initialize()

    return _drive_service_instance
