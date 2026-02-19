"""
Dataset Version Control API Router

Handles semantic versioning for datasets with changelog,
diff tracking, quality reports, and download management.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional, List
from datetime import datetime, timedelta
import hashlib

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from models.version_models import (
    DatasetVersion,
    DatasetVersionCreate,
    DatasetVersionUpdate,
    VersionListResponse,
    VersionSearchQuery,
    VersionComparison,
    compare_versions,
    increment_version,
    is_compatible,
)
from database import get_database
from core.auth import get_current_user
from services.storage_service import HetznerStorageService
from services.manifest_service import ManifestService
import os

# Note: Main.py mounts this router with prefix="/api/v1/datasets"
# so we don't need a prefix here
router = APIRouter(tags=["dataset-versions"])


# ========================================
# Helper Functions
# ========================================

def serialize_version(version_doc: dict) -> dict:
    """Convert MongoDB document to API response format."""
    if version_doc:
        version_doc["id"] = str(version_doc["_id"])
        version_doc["_id"] = str(version_doc["_id"])
        if "dataset_id" in version_doc and isinstance(version_doc["dataset_id"], ObjectId):
            version_doc["dataset_id"] = str(version_doc["dataset_id"])
        if "released_by" in version_doc and isinstance(version_doc["released_by"], ObjectId):
            version_doc["released_by"] = str(version_doc["released_by"])
        if "used_in_models" in version_doc:
            version_doc["used_in_models"] = [str(m) if isinstance(m, ObjectId) else m for m in version_doc["used_in_models"]]
    return version_doc


async def generate_manifest_checksum(manifest_service: ManifestService, manifest_id: str) -> str:
    """Generate checksum for entire dataset version."""
    # Get manifest
    manifest = await manifest_service.get_manifest(manifest_id)
    if not manifest:
        return ""

    # Combine all file checksums
    checksums = [f["checksum"] for f in manifest.get("files", []) if "checksum" in f]
    combined = "".join(sorted(checksums))

    # Hash the combined checksums
    return hashlib.sha256(combined.encode()).hexdigest()


# ========================================
# Dataset Version CRUD Operations
# ========================================

@router.post("/{dataset_id}/versions", response_model=DatasetVersion, status_code=status.HTTP_201_CREATED)
async def create_dataset_version(
    dataset_id: str,
    version_data: DatasetVersionCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new version of a dataset.

    Args:
        dataset_id: Dataset ObjectId
        version_data: Version creation data

    Returns:
        Created version document

    Raises:
        404: Dataset not found
        400: Version already exists or invalid version
        401: Not authenticated
    """
    # Validate dataset_id
    if not ObjectId.is_valid(dataset_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset ID format"
        )

    # Check if dataset exists
    dataset = await db.external_datasets.find_one({"_id": ObjectId(dataset_id)})
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {dataset_id} not found"
        )

    # Check if version already exists
    existing_version = await db.dataset_versions.find_one({
        "dataset_id": dataset_id,
        "version": version_data.version
    })
    if existing_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Version {version_data.version} already exists for this dataset"
        )

    # Create manifest for this version
    manifest_service = ManifestService(db)
    manifest = await manifest_service.create_manifest(
        entity_type="dataset",
        entity_id=dataset_id,
        version=version_data.version,
        storage_path=version_data.storage_path
    )
    manifest_id = str(manifest["_id"])

    # Generate checksum from manifest
    checksum = await generate_manifest_checksum(manifest_service, manifest_id)

    # Prepare version document
    version_doc = {
        "dataset_id": dataset_id,
        "version": version_data.version,
        "storage_path": version_data.storage_path,
        "manifest_url": f"{version_data.storage_path}/manifest.json",
        "parent_version": version_data.parent_version,
        "changelog": version_data.changelog,
        "diff_summary": version_data.diff_summary.dict() if version_data.diff_summary else None,
        "stats": version_data.stats.dict(),
        "quality_report": version_data.quality_report.dict() if version_data.quality_report else None,
        "splits": version_data.splits,
        "checksum": checksum,
        "file_checksums_url": f"{version_data.storage_path}/checksums.txt",
        "is_stable": version_data.is_stable,
        "is_prerelease": version_data.is_prerelease,
        "release_notes": version_data.release_notes,
        "released_by": str(current_user["id"]),
        "released_at": datetime.utcnow(),
        "is_deprecated": False,
        "deprecation_reason": None,
        "download_count": 0,
        "used_in_models": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    # Insert into database
    result = await db.dataset_versions.insert_one(version_doc)
    version_doc["_id"] = result.inserted_id

    # Update parent dataset with version reference
    await db.external_datasets.update_one(
        {"_id": ObjectId(dataset_id)},
        {
            "$push": {"version_history": str(result.inserted_id)},
            "$set": {
                "version": version_data.version,
                "is_latest_version": True,
                "updated_at": datetime.utcnow()
            }
        }
    )

    return DatasetVersion(**serialize_version(version_doc))


@router.get("/{dataset_id}/versions", response_model=VersionListResponse)
async def list_dataset_versions(
    dataset_id: str,
    include_deprecated: bool = False,
    include_prerelease: bool = False,
    min_version: Optional[str] = None,
    max_version: Optional[str] = None,
    sort_by: str = "version",
    sort_order: str = "desc",
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List all versions of a dataset.

    Args:
        dataset_id: Dataset ObjectId
        include_deprecated: Include deprecated versions
        include_prerelease: Include prerelease versions
        min_version: Minimum version (inclusive)
        max_version: Maximum version (inclusive)
        sort_by: Sort field
        sort_order: asc or desc

    Returns:
        List of versions with metadata

    Raises:
        404: Dataset not found
    """
    # Validate dataset_id
    if not ObjectId.is_valid(dataset_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset ID format"
        )

    # Check if dataset exists
    dataset = await db.external_datasets.find_one({"_id": ObjectId(dataset_id)})
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {dataset_id} not found"
        )

    # Build filter query
    filter_query = {"dataset_id": dataset_id}

    if not include_deprecated:
        filter_query["is_deprecated"] = False

    if not include_prerelease:
        filter_query["is_prerelease"] = False

    # TODO: Implement min/max version filtering with semantic version comparison

    # Sort
    sort_direction = -1 if sort_order == "desc" else 1

    # Query versions
    cursor = db.dataset_versions.find(filter_query).sort(sort_by, sort_direction)
    versions = await cursor.to_list(length=1000)

    # Serialize
    versions = [DatasetVersion(**serialize_version(v)) for v in versions]

    # Determine latest and stable versions
    latest_version = versions[0].version if versions else "0.0.0"
    stable_versions = [v for v in versions if v.is_stable and not v.is_deprecated]
    stable_version = stable_versions[0].version if stable_versions else latest_version

    return VersionListResponse(
        versions=versions,
        total=len(versions),
        latest_version=latest_version,
        stable_version=stable_version
    )


# NOTE: /compare route MUST come before /{version} route to avoid "compare" being matched as a version
@router.get("/{dataset_id}/versions/compare", response_model=VersionComparison)
async def compare_dataset_versions(
    dataset_id: str,
    version_a: str = Query(..., description="First version to compare"),
    version_b: str = Query(..., description="Second version to compare"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Compare two versions of a dataset.

    Args:
        dataset_id: Dataset ObjectId
        version_a: First version (e.g., "1.0.0")
        version_b: Second version (e.g., "1.1.0")

    Returns:
        Comparison details including diff and recommendations

    Raises:
        404: Dataset or version not found
    """
    # Validate dataset_id
    if not ObjectId.is_valid(dataset_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset ID format"
        )

    # Find both versions
    version_a_doc = await db.dataset_versions.find_one({
        "dataset_id": dataset_id,
        "version": version_a
    })
    version_b_doc = await db.dataset_versions.find_one({
        "dataset_id": dataset_id,
        "version": version_b
    })

    if not version_a_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_a} not found"
        )
    if not version_b_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_b} not found"
        )

    # Get diff from version_b (assuming it's newer and has diff_summary)
    diff = version_b_doc.get("diff_summary", {
        "files_added": 0,
        "files_removed": 0,
        "files_modified": 0,
        "size_change_mb": 0.0,
        "added_files": [],
        "removed_files": [],
        "modified_files": []
    })

    # Compare stats
    stats_a = version_a_doc.get("stats", {})
    stats_b = version_b_doc.get("stats", {})
    stats_comparison = {
        "total_files": {
            "version_a": stats_a.get("total_files", 0),
            "version_b": stats_b.get("total_files", 0),
            "change": stats_b.get("total_files", 0) - stats_a.get("total_files", 0)
        },
        "total_size_mb": {
            "version_a": stats_a.get("total_size_mb", 0),
            "version_b": stats_b.get("total_size_mb", 0),
            "change": stats_b.get("total_size_mb", 0) - stats_a.get("total_size_mb", 0)
        },
    }

    # Compare quality
    quality_a = version_a_doc.get("quality_report", {})
    quality_b = version_b_doc.get("quality_report", {})
    quality_comparison = None
    if quality_a and quality_b:
        quality_comparison = {
            "transcription_accuracy": {
                "version_a": quality_a.get("transcription_accuracy", 0),
                "version_b": quality_b.get("transcription_accuracy", 0),
            },
            "avg_snr_db": {
                "version_a": quality_a.get("avg_snr_db", 0),
                "version_b": quality_b.get("avg_snr_db", 0),
            }
        }

    # Determine recommendation
    comparison_result = compare_versions(version_a, version_b)
    if comparison_result < 0:
        recommendation = "upgrade"  # version_b is newer
    elif comparison_result > 0:
        recommendation = "downgrade"  # version_a is newer
    else:
        recommendation = "equivalent"

    # Check quality improvements
    if quality_comparison:
        if quality_b.get("transcription_accuracy", 0) > quality_a.get("transcription_accuracy", 0):
            recommendation = "upgrade"

    return VersionComparison(
        version_a=version_a,
        version_b=version_b,
        diff=diff,
        stats_comparison=stats_comparison,
        quality_comparison=quality_comparison,
        recommendation=recommendation
    )


@router.get("/{dataset_id}/versions/{version}", response_model=DatasetVersion)
async def get_dataset_version(
    dataset_id: str,
    version: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get details of a specific dataset version.

    Args:
        dataset_id: Dataset ObjectId
        version: Semantic version string (e.g., "1.2.0")

    Returns:
        Version details

    Raises:
        404: Dataset or version not found
    """
    # Validate dataset_id
    if not ObjectId.is_valid(dataset_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset ID format"
        )

    # Find version
    version_doc = await db.dataset_versions.find_one({
        "dataset_id": dataset_id,
        "version": version
    })

    if not version_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} not found for dataset {dataset_id}"
        )

    return DatasetVersion(**serialize_version(version_doc))


@router.put("/{dataset_id}/versions/{version}", response_model=DatasetVersion)
async def update_dataset_version(
    dataset_id: str,
    version: str,
    update_data: DatasetVersionUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Update dataset version metadata (not the data itself).

    Args:
        dataset_id: Dataset ObjectId
        version: Version string
        update_data: Fields to update

    Returns:
        Updated version

    Raises:
        404: Dataset or version not found
        403: Not authorized
    """
    # Validate dataset_id
    if not ObjectId.is_valid(dataset_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset ID format"
        )

    # Find version
    version_doc = await db.dataset_versions.find_one({
        "dataset_id": dataset_id,
        "version": version
    })

    if not version_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} not found for dataset {dataset_id}"
        )

    # Check authorization (must be releaser)
    user_id = str(current_user["id"])
    if str(version_doc["released_by"]) != user_id:
        # TODO: Add admin override
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this version"
        )

    # Build update document
    update_doc = {"updated_at": datetime.utcnow()}

    if update_data.changelog is not None:
        update_doc["changelog"] = update_data.changelog
    if update_data.is_stable is not None:
        update_doc["is_stable"] = update_data.is_stable
    if update_data.is_deprecated is not None:
        update_doc["is_deprecated"] = update_data.is_deprecated
    if update_data.deprecation_reason is not None:
        update_doc["deprecation_reason"] = update_data.deprecation_reason
    if update_data.quality_report is not None:
        update_doc["quality_report"] = update_data.quality_report.dict()

    # Update in database
    await db.dataset_versions.update_one(
        {"_id": version_doc["_id"]},
        {"$set": update_doc}
    )

    # Fetch updated version
    updated_version = await db.dataset_versions.find_one({"_id": version_doc["_id"]})

    return DatasetVersion(**serialize_version(updated_version))


# ========================================
# Version Downloads
# ========================================

@router.get("/{dataset_id}/versions/{version}/download")
async def get_version_download_url(
    dataset_id: str,
    version: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Get authenticated download URL for dataset version.

    Args:
        dataset_id: Dataset ObjectId
        version: Version string

    Returns:
        Download URLs with expiration

    Raises:
        404: Dataset or version not found
        403: Not authorized to download
    """
    # Validate dataset_id
    if not ObjectId.is_valid(dataset_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset ID format"
        )

    # Find version
    version_doc = await db.dataset_versions.find_one({
        "dataset_id": dataset_id,
        "version": version
    })

    if not version_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} not found for dataset {dataset_id}"
        )

    # Check dataset access level
    dataset = await db.external_datasets.find_one({"_id": ObjectId(dataset_id)})
    if dataset and not dataset.get("is_public", True):
        # TODO: Implement proper authorization checks
        pass

    # Get storage service
    storage = HetznerStorageService(
        host=os.getenv("HETZNER_STORAGE_HOST"),
        username=os.getenv("HETZNER_STORAGE_USERNAME"),
        password=os.getenv("HETZNER_STORAGE_PASSWORD"),
        port=int(os.getenv("HETZNER_STORAGE_PORT", "23")),
    )

    # Generate presigned URLs
    expiry_hours = 2  # Longer for datasets
    storage_path = version_doc["storage_path"]

    # Generate download URL for the whole dataset archive
    archive_path = f"{storage_path}/dataset.tar.gz"
    download_url = storage.generate_download_url(archive_path, expiry_hours=expiry_hours)

    # Generate manifest URL
    manifest_url = storage.generate_download_url(
        version_doc["manifest_url"],
        expiry_hours=expiry_hours
    )

    # Increment download count (async)
    await db.dataset_versions.update_one(
        {"_id": version_doc["_id"]},
        {"$inc": {"download_count": 1}}
    )

    return {
        "dataset_id": dataset_id,
        "version": version,
        "download_url": download_url,
        "manifest_url": manifest_url,
        "checksums_url": storage.generate_download_url(
            version_doc["file_checksums_url"],
            expiry_hours=expiry_hours
        ),
        "expires_at": datetime.utcnow() + timedelta(hours=expiry_hours),
        "size_mb": version_doc.get("stats", {}).get("total_size_mb", 0.0),
        "checksum": version_doc.get("checksum", "")
    }


# ========================================
# Version Utilities
# ========================================

@router.post("/{dataset_id}/versions/{version}/increment")
async def suggest_next_version(
    dataset_id: str,
    version: str,
    bump_type: str = Query(..., description="major, minor, or patch"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Suggest next version number based on semantic versioning.

    Args:
        dataset_id: Dataset ObjectId
        version: Current version
        bump_type: Type of version bump (major, minor, patch)

    Returns:
        Suggested next version

    Raises:
        404: Version not found
        400: Invalid bump type
    """
    if bump_type not in ["major", "minor", "patch"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="bump_type must be one of: major, minor, patch"
        )

    # Validate dataset_id
    if not ObjectId.is_valid(dataset_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset ID format"
        )

    # Find version
    version_doc = await db.dataset_versions.find_one({
        "dataset_id": dataset_id,
        "version": version
    })

    if not version_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} not found"
        )

    # Calculate next version
    next_version = increment_version(version, bump_type)

    # Check if next version already exists
    existing = await db.dataset_versions.find_one({
        "dataset_id": dataset_id,
        "version": next_version
    })

    return {
        "current_version": version,
        "suggested_version": next_version,
        "bump_type": bump_type,
        "already_exists": existing is not None
    }


@router.get("/{dataset_id}/versions/{version}/compatible")
async def check_version_compatibility(
    dataset_id: str,
    version: str,
    compare_with: str = Query(..., description="Version to compare with"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Check if two versions are compatible (same major version).

    Args:
        dataset_id: Dataset ObjectId
        version: First version
        compare_with: Second version to compare

    Returns:
        Compatibility information
    """
    compatible = is_compatible(version, compare_with)

    return {
        "version_a": version,
        "version_b": compare_with,
        "compatible": compatible,
        "explanation": "Compatible (same major version)" if compatible else "Incompatible (different major versions)"
    }
