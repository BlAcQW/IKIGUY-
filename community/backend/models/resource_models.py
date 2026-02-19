"""
Resource management models for external links, file uploads, and user contributions.
"""

from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId


class ResourceType(str, Enum):
    """Types of external resources."""
    DATASET = "dataset"
    MODEL = "model"
    PAPER = "paper"
    TOOL = "tool"
    NOTEBOOK = "notebook"
    DOCUMENTATION = "documentation"
    TUTORIAL = "tutorial"
    OTHER = "other"


class Platform(str, Enum):
    """External platforms."""
    HUGGINGFACE = "huggingface"
    GITHUB = "github"
    KAGGLE = "kaggle"
    ZENODO = "zenodo"
    ARXIV = "arxiv"
    OPENSLR = "openslr"
    COMMONVOICE = "commonvoice"
    CUSTOM = "custom"


class VerificationStatus(str, Enum):
    """Resource verification status."""
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    FLAGGED = "flagged"
    BROKEN = "broken"


class UploadType(str, Enum):
    """Types of user uploads."""
    DATASET = "dataset"
    MODEL = "model"
    NOTEBOOK = "notebook"
    RESOURCE = "resource"


class ProcessingStatus(str, Enum):
    """Upload processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResourceLinkCreate(BaseModel):
    """Model for submitting an external resource link."""
    title: str = Field(..., min_length=3, max_length=200)
    url: HttpUrl
    resource_type: ResourceType
    platform: Platform = Platform.CUSTOM

    # Classification
    model_type: Optional[str] = Field(None, description="tts, asr, llm, nmt, etc.")
    data_type: Optional[str] = Field(None, description="audio, text, parallel, multimodal")

    # Language association
    languages: List[str] = Field(..., min_items=1)
    is_multilingual: bool = False

    # Metadata
    description: str = Field(..., min_length=20, max_length=2000)
    tags: List[str] = []
    license: Optional[str] = None
    citation: Optional[str] = None

    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags."""
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        return [tag.lower().strip() for tag in v if tag.strip()]


class ResourceLinkUpdate(BaseModel):
    """Model for updating a resource link."""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=20, max_length=2000)
    tags: Optional[List[str]] = None
    license: Optional[str] = None
    citation: Optional[str] = None


class ResourceLink(BaseModel):
    """Complete resource link document."""
    id: str = Field(alias="_id")
    link_uuid: str

    # Resource info
    title: str
    url: str
    resource_type: ResourceType
    platform: Platform

    # Classification
    model_type: Optional[str] = None
    data_type: Optional[str] = None

    # Language association
    languages: List[str]
    language_ids: List[str] = []
    is_multilingual: bool

    # Metadata
    description: str
    tags: List[str] = []
    license: Optional[str] = None
    citation: Optional[str] = None

    # Quality & status
    quality_rating: float = Field(0.0, ge=0, le=5)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None

    # Availability monitoring
    last_checked: Optional[datetime] = None
    is_available: bool = True
    availability_checks: int = 0
    downtime_count: int = 0

    # Contributor
    submitted_by: str

    # Engagement
    upvotes: int = 0
    downvotes: int = 0
    view_count: int = 0
    click_count: int = 0

    # Pipeline association
    used_in_pipelines: List[str] = []
    used_in_models: List[str] = []

    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class FileUploadCreate(BaseModel):
    """Model for initiating a file upload."""
    upload_type: UploadType
    file_type: str = Field(..., description="audio, text, model, notebook")
    original_filename: str
    file_size_mb: float
    mime_type: str

    # Language & metadata
    language_code: str
    tags: List[str] = []
    description: str = Field(..., min_length=10, max_length=1000)
    license: str = "CC-BY-4.0"

    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags."""
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        return [tag.lower().strip() for tag in v if tag.strip()]


class FileUpload(BaseModel):
    """Complete file upload document."""
    id: str = Field(alias="_id")
    upload_uuid: str

    # User info
    uploaded_by: str
    upload_type: UploadType

    # File info
    original_filename: str
    file_type: str
    mime_type: str
    file_size_mb: float

    # Storage
    storage_path: str
    access_url: str
    is_temporary: bool = False

    # Processing
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    processing_error: Optional[str] = None

    # Validation
    validation_results: Optional[Dict[str, Any]] = None

    # Language & metadata
    language_code: str
    language_id: Optional[str] = None
    tags: List[str] = []
    description: str

    # Integration
    integrated_into_dataset: Optional[str] = None
    integrated_at: Optional[datetime] = None

    # Access control
    access_level: str = "authenticated"  # public, authenticated, private
    license: str

    # Security (quarantine for virus scanning)
    is_quarantined: bool = False
    virus_scan_result: Optional[str] = None
    scanned_at: Optional[datetime] = None

    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class ResourceSearchQuery(BaseModel):
    """Resource search parameters."""
    query: Optional[str] = None
    resource_type: Optional[ResourceType] = None
    platform: Optional[Platform] = None
    languages: Optional[List[str]] = None
    model_type: Optional[str] = None
    data_type: Optional[str] = None
    verification_status: Optional[VerificationStatus] = None
    min_quality_rating: Optional[float] = Field(None, ge=0, le=5)
    tags: Optional[List[str]] = None
    sort_by: str = "updated_at"
    sort_order: str = "desc"
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class ResourceListResponse(BaseModel):
    """Response for resource listing."""
    resources: List[ResourceLink]
    total: int
    page: int
    page_size: int
    total_pages: int


class UploadSearchQuery(BaseModel):
    """Upload search parameters."""
    upload_type: Optional[UploadType] = None
    processing_status: Optional[ProcessingStatus] = None
    language_code: Optional[str] = None
    uploaded_by: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class UploadListResponse(BaseModel):
    """Response for upload listing."""
    uploads: List[FileUpload]
    total: int
    page: int
    page_size: int
    total_pages: int


class ResourceVerification(BaseModel):
    """Model for verifying a resource link."""
    is_available: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    verification_notes: Optional[str] = None


class ResourceVote(BaseModel):
    """Model for voting on a resource."""
    vote_type: str = Field(..., description="upvote or downvote")

    @validator('vote_type')
    def validate_vote_type(cls, v):
        """Validate vote type."""
        if v not in ['upvote', 'downvote']:
            raise ValueError("Vote type must be 'upvote' or 'downvote'")
        return v


class ResourceStats(BaseModel):
    """Statistics for resources."""
    total_links: int
    links_by_type: Dict[str, int]
    links_by_platform: Dict[str, int]
    links_by_language: Dict[str, int]
    verified_links: int
    broken_links: int
    total_uploads: int
    uploads_by_type: Dict[str, int]
    uploads_by_status: Dict[str, int]
    total_storage_used_gb: float


class UploadProgressUpdate(BaseModel):
    """Model for updating upload processing progress."""
    processing_status: ProcessingStatus
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    processing_error: Optional[str] = None
    validation_results: Optional[Dict[str, Any]] = None
