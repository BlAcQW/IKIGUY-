"""
Manifest generation and management service for African Language Community Platform.

Handles automatic file indexing, integrity verification, and manifest generation
for datasets, models, and notebooks stored on Hetzner Storage Box.
"""

import os
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Union

logger = logging.getLogger(__name__)


class ManifestService:
    """
    Service for generating and managing storage manifests.

    Manifest structure tracks all files in a specific version of a dataset/model,
    including checksums, sizes, and metadata for integrity verification.
    """

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        storage_service=None
    ):
        """
        Initialize ManifestService.

        Args:
            db: AsyncIOMotorDatabase instance
            storage_service: Optional HetznerStorageService instance (for file scanning)
        """
        self.db = db
        self.storage = storage_service
        self.manifests_collection = self.db["storage_manifests"]

    async def create_manifest(
        self,
        entity_type: str,
        entity_id: str,
        version: str,
        storage_path: str,
        file_list: Optional[List[Dict[str, Any]]] = None,
        auto_scan: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new manifest for a dataset/model/notebook version.

        Args:
            entity_type: Type of entity ('dataset', 'model', 'notebook')
            entity_id: Entity ObjectId as string
            version: Semantic version (e.g., 'v1.0.0')
            storage_path: Relative storage path (e.g., 'datasets/twi/audio/uuid/v1.0.0/')
            file_list: Optional pre-computed file list with checksums
            auto_scan: If True and file_list is None, automatically scan storage path

        Returns:
            Created manifest document
        """
        logger.info(f"Creating manifest for {entity_type} {entity_id} version {version}")

        # Get or scan file list
        if file_list is None and auto_scan:
            file_list = await self._scan_storage_path(storage_path)
        elif file_list is None:
            file_list = []

        # Compute aggregate statistics
        total_files = len(file_list)
        total_size_bytes = sum(f.get("size_bytes", 0) for f in file_list)

        # Create manifest document
        manifest = {
            "manifest_uuid": self._generate_manifest_uuid(),
            "entity_type": entity_type,
            "entity_id": ObjectId(entity_id),
            "version": version,
            "storage_path": storage_path,
            "storage_provider": "hetzner_storage_box",
            "files": file_list,
            "total_files": total_files,
            "total_size_bytes": total_size_bytes,
            "is_complete": True,
            "last_indexed": datetime.utcnow(),
            "index_frequency": "on_change",
            "integrity_verified": False,
            "last_verified": None,
            "corrupted_files": [],
            "access_protocol": "https",  # WebDAV/HTTPS for downloads
            "base_url": f"https://{os.getenv('HETZNER_STORAGE_HOST', '')}/",
            "auth_required": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Insert into MongoDB
        result = await self.manifests_collection.insert_one(manifest)
        manifest["_id"] = result.inserted_id

        logger.info(f"Created manifest {manifest['manifest_uuid']} with {total_files} files")

        return manifest

    async def update_manifest(
        self,
        manifest_id: str,
        changes: Dict[str, Any],
        rescan: bool = False
    ) -> Dict[str, Any]:
        """
        Update an existing manifest.

        Args:
            manifest_id: Manifest ObjectId as string
            changes: Dictionary of fields to update
            rescan: If True, rescan the storage path for new/deleted files

        Returns:
            Updated manifest document
        """
        manifest = await self.manifests_collection.find_one({"_id": ObjectId(manifest_id)})

        if not manifest:
            raise ValueError(f"Manifest {manifest_id} not found")

        if rescan:
            # Rescan storage path
            new_file_list = await self._scan_storage_path(manifest["storage_path"])
            changes["files"] = new_file_list
            changes["total_files"] = len(new_file_list)
            changes["total_size_bytes"] = sum(f.get("size_bytes", 0) for f in new_file_list)
            changes["last_indexed"] = datetime.utcnow()

        changes["updated_at"] = datetime.utcnow()

        # Update in MongoDB
        await self.manifests_collection.update_one(
            {"_id": ObjectId(manifest_id)},
            {"$set": changes}
        )

        # Fetch updated manifest
        updated_manifest = await self.manifests_collection.find_one({"_id": ObjectId(manifest_id)})

        logger.info(f"Updated manifest {manifest_id}")

        return updated_manifest

    async def verify_manifest_integrity(
        self,
        manifest_id: str,
        sample_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Verify integrity of all files in manifest.

        Args:
            manifest_id: Manifest ObjectId as string
            sample_size: If provided, only verify a random sample of this size

        Returns:
            Verification report with corrupted files list
        """
        manifest = await self.manifests_collection.find_one({"_id": ObjectId(manifest_id)})

        if not manifest:
            raise ValueError(f"Manifest {manifest_id} not found")

        logger.info(f"Verifying integrity of manifest {manifest_id}")

        files_to_verify = manifest.get("files", [])

        if sample_size and sample_size < len(files_to_verify):
            import random
            files_to_verify = random.sample(files_to_verify, sample_size)

        corrupted_files = []
        verified_count = 0

        # If no storage service configured, skip verification
        if not self.storage:
            logger.warning("No storage service configured, skipping integrity verification")
            return {
                "manifest_id": manifest_id,
                "total_files": len(files_to_verify),
                "verified_files": 0,
                "corrupted_files": 0,
                "is_intact": True,
                "corrupted_file_list": [],
                "verified_at": datetime.utcnow(),
                "skipped": True,
                "reason": "No storage service configured"
            }

        with self.storage:
            for file_info in files_to_verify:
                file_path = f"{manifest['storage_path']}/{file_info['relative_path']}"
                expected_checksum = file_info.get("checksum")

                if not expected_checksum:
                    continue

                try:
                    # Verify checksum
                    is_valid = self.storage.verify_integrity(file_path, expected_checksum)

                    if not is_valid:
                        corrupted_files.append({
                            "path": file_path,
                            "expected_checksum": expected_checksum,
                            "error": "Checksum mismatch"
                        })
                    else:
                        verified_count += 1

                except Exception as e:
                    corrupted_files.append({
                        "path": file_path,
                        "expected_checksum": expected_checksum,
                        "error": str(e)
                    })

        # Update manifest with verification results
        await self.manifests_collection.update_one(
            {"_id": ObjectId(manifest_id)},
            {
                "$set": {
                    "integrity_verified": len(corrupted_files) == 0,
                    "last_verified": datetime.utcnow(),
                    "corrupted_files": corrupted_files,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        verification_report = {
            "manifest_id": manifest_id,
            "total_files": len(files_to_verify),
            "verified_files": verified_count,
            "corrupted_files": len(corrupted_files),
            "is_intact": len(corrupted_files) == 0,
            "corrupted_file_list": corrupted_files,
            "verified_at": datetime.utcnow()
        }

        logger.info(f"Verification complete: {verified_count}/{len(files_to_verify)} files intact")

        return verification_report

    async def index_storage_path(
        self,
        storage_path: str,
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Index all files in a storage path.

        Args:
            storage_path: Relative storage path to index
            recursive: Whether to index recursively

        Returns:
            List of file information dictionaries
        """
        logger.info(f"Indexing storage path: {storage_path}")

        # If no storage service configured, return empty list
        if not self.storage:
            logger.warning("No storage service configured, returning empty file list")
            return []

        indexed_files = []

        with self.storage:
            files = self.storage.list_files(storage_path, recursive=recursive)

            for file_info in files:
                # Get full file path for checksum computation
                relative_path = file_info["path"].replace(f"{storage_path}/", "")

                # Try to get metadata
                metadata = self.storage.get_file_metadata(file_info["path"])

                indexed_file = {
                    "relative_path": relative_path,
                    "filename": file_info["filename"],
                    "size_bytes": file_info["size"],
                    "checksum": metadata.get("checksum") if metadata else None,
                    "mime_type": self._guess_mime_type(file_info["filename"]),
                    "metadata": metadata or {},
                    "indexed_at": datetime.utcnow()
                }

                indexed_files.append(indexed_file)

        logger.info(f"Indexed {len(indexed_files)} files in {storage_path}")

        return indexed_files

    async def get_manifest(
        self,
        manifest_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get manifest by ID or by entity_id + version.

        Args:
            manifest_id: Manifest ObjectId as string
            entity_id: Entity ObjectId as string
            version: Version string

        Returns:
            Manifest document or None if not found
        """
        if manifest_id:
            return await self.manifests_collection.find_one({"_id": ObjectId(manifest_id)})
        elif entity_id and version:
            return await self.manifests_collection.find_one({
                "entity_id": ObjectId(entity_id),
                "version": version
            })
        else:
            raise ValueError("Must provide either manifest_id or (entity_id + version)")

    async def list_manifests(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List manifests with optional filtering.

        Args:
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            limit: Maximum number of results
            skip: Number of results to skip

        Returns:
            List of manifest documents
        """
        query = {}

        if entity_type:
            query["entity_type"] = entity_type
        if entity_id:
            query["entity_id"] = ObjectId(entity_id)

        cursor = self.manifests_collection.find(query).skip(skip).limit(limit).sort("created_at", -1)

        return await cursor.to_list(length=limit)

    async def delete_manifest(self, manifest_id: str) -> bool:
        """
        Delete a manifest.

        Args:
            manifest_id: Manifest ObjectId as string

        Returns:
            True if deleted successfully
        """
        result = await self.manifests_collection.delete_one({"_id": ObjectId(manifest_id)})

        if result.deleted_count > 0:
            logger.info(f"Deleted manifest {manifest_id}")
            return True
        else:
            logger.warning(f"Manifest {manifest_id} not found for deletion")
            return False

    async def generate_download_manifest(
        self,
        manifest_id: str,
        include_checksums: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a downloadable manifest file (JSON) for users.

        Args:
            manifest_id: Manifest ObjectId as string
            include_checksums: Whether to include file checksums

        Returns:
            Manifest data suitable for download
        """
        manifest = await self.get_manifest(manifest_id=manifest_id)

        if not manifest:
            raise ValueError(f"Manifest {manifest_id} not found")

        download_manifest = {
            "manifest_version": "1.0.0",
            "entity_type": manifest["entity_type"],
            "entity_id": str(manifest["entity_id"]),
            "version": manifest["version"],
            "total_files": manifest["total_files"],
            "total_size_bytes": manifest["total_size_bytes"],
            "created_at": manifest["created_at"].isoformat(),
            "files": []
        }

        for file_info in manifest.get("files", []):
            file_entry = {
                "path": file_info["relative_path"],
                "size": file_info["size_bytes"],
                "download_url": self._generate_download_url(
                    manifest["storage_path"],
                    file_info["relative_path"]
                )
            }

            if include_checksums and file_info.get("checksum"):
                file_entry["checksum"] = {
                    "algorithm": "sha256",
                    "value": file_info["checksum"]
                }

            download_manifest["files"].append(file_entry)

        return download_manifest

    async def _scan_storage_path(self, storage_path: str) -> List[Dict[str, Any]]:
        """Scan storage path and return file list."""
        return await self.index_storage_path(storage_path, recursive=True)

    @staticmethod
    def _generate_manifest_uuid() -> str:
        """Generate unique manifest UUID."""
        import uuid
        return str(uuid.uuid4())

    @staticmethod
    def _guess_mime_type(filename: str) -> str:
        """Guess MIME type from filename extension."""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"

    def _generate_download_url(self, storage_path: str, relative_file_path: str) -> str:
        """
        Generate WebDAV/HTTPS download URL for a file.

        Args:
            storage_path: Base storage path
            relative_file_path: Relative path within storage path

        Returns:
            HTTPS download URL
        """
        from urllib.parse import quote

        host = os.getenv("HETZNER_STORAGE_HOST", "")
        base_path = os.getenv("HETZNER_STORAGE_BASE_PATH", "/african-languages")

        full_path = f"{base_path}/{storage_path}/{relative_file_path}"
        encoded_path = quote(full_path)

        # WebDAV/HTTPS URL (requires HTTP Basic Auth)
        return f"https://{host}/{encoded_path}"

    @staticmethod
    def compute_manifest_checksum(manifest_files: List[Dict[str, Any]]) -> str:
        """
        Compute checksum of entire manifest (for version comparison).

        Args:
            manifest_files: List of file info dicts with checksums

        Returns:
            SHA256 checksum of concatenated file checksums
        """
        # Concatenate all file checksums in sorted order
        checksums = sorted([f.get("checksum", "") for f in manifest_files])
        combined = "".join(checksums)

        return hashlib.sha256(combined.encode()).hexdigest()


# Helper function to get manifest service instance
def get_manifest_service(db: AsyncIOMotorDatabase, storage_service=None) -> ManifestService:
    """
    Get configured ManifestService instance.

    Args:
        db: AsyncIOMotorDatabase instance
        storage_service: Optional HetznerStorageService instance

    Returns:
        ManifestService instance
    """
    return ManifestService(db, storage_service)
