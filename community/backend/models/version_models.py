"""
Version control models for datasets and models.

Handles semantic versioning, changelogs, and version comparison.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId


class VersionDiff(BaseModel):
    """Difference between two versions."""
    files_added: int = 0
    files_removed: int = 0
    files_modified: int = 0
    size_change_mb: float = 0.0
    added_files: List[str] = []
    removed_files: List[str] = []
    modified_files: List[str] = []


class VersionStats(BaseModel):
    """Statistics for a version."""
    total_files: int
    total_size_mb: float
    total_duration_hours: Optional[float] = None
    speakers: Optional[int] = None
    avg_quality_score: Optional[float] = None


class DatasetSplit(BaseModel):
    """Dataset split information."""
    files: int
    hours: Optional[float] = None
    samples: Optional[int] = None


class QualityReport(BaseModel):
    """Quality metrics for a dataset version."""
    transcription_accuracy: Optional[float] = Field(None, ge=0, le=1)
    avg_snr_db: Optional[float] = None
    audio_quality_score: Optional[float] = Field(None, ge=0, le=1)
    consistency_score: Optional[float] = Field(None, ge=0, le=1)
    completeness_score: Optional[float] = Field(None, ge=0, le=1)


class DatasetVersionCreate(BaseModel):
    """Model for creating a new dataset version."""
    # dataset_id is optional in body since it comes from URL path parameter
    dataset_id: Optional[str] = Field(None, description="Parent dataset ObjectId (provided via URL path)")
    version: str = Field(..., pattern=r'^\d+\.\d+\.\d+$')
    storage_path: str
    changelog: str = Field(..., min_length=10, max_length=2000)

    # Changes from parent
    parent_version: Optional[str] = None
    diff_summary: Optional[VersionDiff] = None

    # Statistics
    stats: VersionStats

    # Quality
    quality_report: Optional[QualityReport] = None

    # Splits
    splits: Dict[str, DatasetSplit] = {}

    # Release info
    is_stable: bool = True
    is_prerelease: bool = False
    release_notes: Optional[str] = None

    @validator('version')
    def validate_version(cls, v):
        """Validate semantic version format."""
        parts = v.split('.')
        if len(parts) != 3:
            raise ValueError("Version must be in format X.Y.Z")
        for part in parts:
            if not part.isdigit():
                raise ValueError("Version parts must be integers")
        return v


class DatasetVersionUpdate(BaseModel):
    """Model for updating a dataset version."""
    changelog: Optional[str] = Field(None, min_length=10, max_length=2000)
    is_stable: Optional[bool] = None
    is_deprecated: Optional[bool] = None
    deprecation_reason: Optional[str] = None
    quality_report: Optional[QualityReport] = None


class DatasetVersion(BaseModel):
    """Complete dataset version document."""
    id: str = Field(alias="_id")
    dataset_id: str
    version: str

    # Storage
    storage_path: str
    manifest_url: str

    # Changes
    parent_version: Optional[str] = None
    changelog: str
    diff_summary: Optional[VersionDiff] = None

    # Statistics
    stats: VersionStats

    # Quality
    quality_report: Optional[QualityReport] = None

    # Splits
    splits: Dict[str, DatasetSplit] = {}

    # Checksums
    checksum: str
    file_checksums_url: str

    # Release info
    is_stable: bool
    is_prerelease: bool
    release_notes: Optional[str] = None
    released_by: str
    released_at: datetime

    # Deprecation
    is_deprecated: bool = False
    deprecation_reason: Optional[str] = None

    # Usage tracking
    download_count: int = 0
    used_in_models: List[str] = []

    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class VersionComparison(BaseModel):
    """Comparison between two versions."""
    version_a: str
    version_b: str
    diff: VersionDiff
    stats_comparison: Dict[str, Any]
    quality_comparison: Optional[Dict[str, Any]] = None
    recommendation: str  # upgrade, downgrade, or equivalent


class VersionListResponse(BaseModel):
    """Response for version listing."""
    versions: List[DatasetVersion]
    total: int
    latest_version: str
    stable_version: str


class VersionSearchQuery(BaseModel):
    """Version search parameters."""
    dataset_id: str
    include_deprecated: bool = False
    include_prerelease: bool = False
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    sort_by: str = "version"
    sort_order: str = "desc"


def compare_versions(version_a: str, version_b: str) -> int:
    """
    Compare two semantic versions.

    Args:
        version_a: First version (e.g., "1.2.3")
        version_b: Second version (e.g., "1.3.0")

    Returns:
        -1 if version_a < version_b
        0 if version_a == version_b
        1 if version_a > version_b
    """
    parts_a = [int(x) for x in version_a.split('.')]
    parts_b = [int(x) for x in version_b.split('.')]

    for a, b in zip(parts_a, parts_b):
        if a < b:
            return -1
        elif a > b:
            return 1

    return 0


def increment_version(version: str, bump_type: str = "patch") -> str:
    """
    Increment a semantic version.

    Args:
        version: Current version (e.g., "1.2.3")
        bump_type: Type of bump ("major", "minor", or "patch")

    Returns:
        Incremented version
    """
    major, minor, patch = [int(x) for x in version.split('.')]

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def is_compatible(version_a: str, version_b: str) -> bool:
    """
    Check if two versions are compatible (same major version).

    Args:
        version_a: First version
        version_b: Second version

    Returns:
        True if compatible
    """
    major_a = int(version_a.split('.')[0])
    major_b = int(version_b.split('.')[0])

    return major_a == major_b
