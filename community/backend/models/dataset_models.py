"""
External dataset integration models for African Language Community Platform.

Handles integration with Common Voice, OpenSLR, Masakhane, and custom datasets.
"""

from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from bson import ObjectId


class DatasetSource(str, Enum):
    """Supported external dataset sources."""
    COMMON_VOICE = "common_voice"
    OPENSLR = "openslr"
    MASAKHANE = "masakhane"
    CUSTOM_SCRAPE = "custom_scrape"
    MANUAL_UPLOAD = "manual_upload"
    COMMUNITY_SUBMISSION = "community_submission"


class DatasetType(str, Enum):
    """Types of datasets."""
    AUDIO_SPEECH = "audio_speech"
    TEXT_CORPUS = "text_corpus"
    TRANSLATION_PAIRS = "translation_pairs"
    PRONUNCIATION_DICT = "pronunciation_dict"
    LANGUAGE_MODEL = "language_model"
    ACOUSTIC_MODEL = "acoustic_model"


class ProcessingStatus(str, Enum):
    """Dataset processing status."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    VALIDATING = "validating"
    INTEGRATING = "integrating"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class LicenseType(str, Enum):
    """Dataset license types."""
    CC0 = "cc0"
    CC_BY = "cc_by"
    CC_BY_SA = "cc_by_sa"
    CC_BY_NC = "cc_by_nc"
    MIT = "mit"
    APACHE_2 = "apache_2"
    GPL_V3 = "gpl_v3"
    CUSTOM = "custom"
    PROPRIETARY = "proprietary"


class HostingType(str, Enum):
    """Dataset hosting type."""
    LOCAL = "local"  # Hosted on our Hetzner storage
    EXTERNAL = "external"  # Hosted externally (links to external source)
    HYBRID = "hybrid"  # Metadata local, points to external download


class ExternalDatasetCreate(BaseModel):
    """Model for creating external dataset integration."""
    name: str = Field(..., min_length=3, max_length=200)
    source: DatasetSource
    dataset_type: DatasetType
    language_code: str = Field(..., min_length=2, max_length=10)
    language_family: Optional[str] = None

    # Source information
    source_url: Optional[HttpUrl] = None
    source_version: Optional[str] = None
    source_metadata: Dict[str, Any] = {}

    # License and attribution
    license_type: LicenseType
    license_url: Optional[HttpUrl] = None
    attribution: Optional[str] = None
    commercial_use_allowed: bool = True

    # Processing configuration
    auto_process: bool = True
    quality_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_file_size_mb: Optional[int] = Field(default=1000, gt=0)
    target_format: Optional[str] = None

    # Integration settings
    merge_with_existing: bool = True
    priority: int = Field(default=3, ge=1, le=5)  # 1=highest, 5=lowest

    description: Optional[str] = None
    tags: List[str] = []

    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags."""
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        return [tag.lower().strip() for tag in v if tag.strip()]


class ExternalDataset(BaseModel):
    """Complete external dataset model."""
    id: str = Field(alias="_id")
    dataset_uuid: str = Field(..., description="Unique identifier for version tracking")
    name: str
    source: DatasetSource
    dataset_type: DatasetType
    language_code: str
    language_family: Optional[str] = None
    language_id: Optional[str] = Field(None, description="Reference to Language ObjectId")

    # Versioning
    version: str = Field(default="1.0.0", pattern=r'^\d+\.\d+\.\d+$')
    is_latest_version: bool = True
    version_history: List[str] = Field(default=[], description="List of version ObjectIds")

    # Source information
    source_url: Optional[str] = None
    source_version: Optional[str] = None
    source_metadata: Dict[str, Any] = {}

    # License and attribution
    license_type: LicenseType
    license_url: Optional[str] = None
    attribution: Optional[str] = None
    commercial_use_allowed: bool = True

    # Processing status
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    processing_error: Optional[str] = None
    processing_logs: List[str] = []

    # Dataset statistics
    total_files: Optional[int] = None
    total_size_mb: Optional[float] = None
    total_duration_hours: Optional[float] = None  # For audio datasets
    total_words: Optional[int] = None  # For text datasets
    quality_score: Optional[float] = None

    # Integration results
    files_processed: int = 0
    files_integrated: int = 0
    files_rejected: int = 0
    duplicate_files: int = 0

    # Configuration
    auto_process: bool = True
    quality_threshold: float = 0.7
    max_file_size_mb: Optional[int] = 1000
    target_format: Optional[str] = None
    merge_with_existing: bool = True
    priority: int = 3

    # Storage and distribution (NEW - Hetzner Storage Box integration)
    storage_path: Optional[str] = Field(None, description="Path in Hetzner Storage Box")
    manifest_id: Optional[str] = Field(None, description="Storage manifest ObjectId")
    checksum: Optional[str] = Field(None, description="SHA256 checksum for integrity")
    download_url: Optional[str] = Field(None, description="Authenticated download URL")
    is_public: bool = Field(default=True, description="Public or authenticated access")
    hosting_type: HostingType = Field(default=HostingType.EXTERNAL, description="Where the dataset is hosted")

    # MLOps pipeline tracking (NEW)
    used_in_pipelines: List[str] = Field(default=[], description="Pipeline ObjectIds")
    used_in_models: List[str] = Field(default=[], description="Model ObjectIds")
    training_ready: bool = Field(default=False, description="Ready for training use")

    # Dataset splits (NEW)
    has_train_split: bool = False
    has_validation_split: bool = False
    has_test_split: bool = False
    split_ratios: Optional[Dict[str, float]] = Field(None, description="train/val/test ratios")

    # Metadata
    description: Optional[str] = None
    tags: List[str] = []
    created_by: str
    created_at: datetime
    updated_at: datetime
    last_processed_at: Optional[datetime] = None
    published_at: Optional[datetime] = Field(None, description="When made publicly available")

    # Integration tracking
    integrated_submissions: List[str] = []  # IDs of created submissions
    integration_manifest_url: Optional[str] = None

    # Downloads and usage tracking (NEW)
    download_count: int = 0
    view_count: int = 0
    citation_count: int = 0

    class Config:
        populate_by_name = True


class DatasetProcessingJob(BaseModel):
    """Model for dataset processing jobs."""
    id: str = Field(alias="_id")
    dataset_id: str
    job_type: str  # download, process, validate, integrate
    status: ProcessingStatus

    # Job configuration
    config: Dict[str, Any] = {}
    dependencies: List[str] = []  # Other job IDs this depends on

    # Execution tracking
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percentage: float = 0.0
    current_step: Optional[str] = None

    # Results
    result_data: Dict[str, Any] = {}
    error_message: Optional[str] = None
    logs: List[str] = []

    # Resource usage
    cpu_time_seconds: Optional[float] = None
    memory_peak_mb: Optional[float] = None
    disk_usage_mb: Optional[float] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class DatasetIntegrationManifest(BaseModel):
    """Manifest for dataset integration with voice-lab."""
    id: str = Field(alias="_id")
    dataset_id: str
    language_code: str
    language_family: str

    # Training compatibility
    voice_lab_compatible: bool = True
    moshi_compatible: bool = True
    training_format: str = "wav"  # wav, mp3, flac

    # File organization
    total_files: int
    training_files: int
    validation_files: int
    test_files: int

    # Quality metrics
    average_quality_score: float
    duration_distribution: Dict[str, int]  # {duration_range: count}
    speaker_distribution: Dict[str, int]   # {speaker_id: file_count}

    # File paths and metadata
    manifest_url: str
    training_manifest_url: str
    validation_manifest_url: str
    test_manifest_url: str

    # Integration metadata
    created_at: datetime
    voice_lab_integration_date: Optional[datetime] = None
    last_training_date: Optional[datetime] = None
    model_performance_metrics: Dict[str, float] = {}

    class Config:
        populate_by_name = True


class DatasetStats(BaseModel):
    """Statistics for external datasets."""
    total_datasets: int
    datasets_by_source: Dict[str, int]
    datasets_by_language: Dict[str, int]
    datasets_by_status: Dict[str, int]
    total_files_integrated: int
    total_size_gb: float
    total_audio_hours: float
    average_quality_score: float
    processing_queue_length: int


class CommonVoiceIntegration(BaseModel):
    """Specific model for Common Voice dataset integration."""
    dataset_id: str
    cv_version: str = "11.0"  # Common Voice version
    languages: List[str] = []
    download_splits: List[str] = ["train", "dev", "test"]

    # Processing options
    min_duration_seconds: float = 1.0
    max_duration_seconds: float = 30.0
    min_votes: int = 2
    max_other_votes: int = 0  # Maximum "other" votes allowed

    # Quality filters
    filter_by_accent: bool = False
    filter_by_age: bool = False
    filter_by_gender: bool = False

    # Integration settings
    create_speaker_embeddings: bool = True
    normalize_audio: bool = True
    target_sample_rate: int = 16000

    class Config:
        populate_by_name = True


class OpenSLRIntegration(BaseModel):
    """Specific model for OpenSLR dataset integration."""
    dataset_id: str
    slr_resource_id: int  # OpenSLR resource ID (e.g., SLR32 for Yoruba)
    resource_url: str

    # Processing configuration
    extract_archives: bool = True
    validate_checksums: bool = True
    expected_format: str = "wav"

    # Language-specific settings
    language_code: str
    language_name: str
    dialect_code: Optional[str] = None

    # Quality control
    validate_transcriptions: bool = True
    check_audio_quality: bool = True
    min_snr_db: float = 10.0

    class Config:
        populate_by_name = True


class MasakhaneIntegration(BaseModel):
    """Specific model for Masakhane dataset integration."""
    dataset_id: str
    masakhane_repo: str  # GitHub repository
    dataset_name: str

    # Dataset configuration
    task_type: str  # translation, ner, pos, sentiment
    language_pairs: List[str] = []  # For translation tasks

    # Processing options
    split_validation: float = 0.1
    split_test: float = 0.1
    max_sequence_length: int = 512

    # Quality filters
    min_sentence_length: int = 3
    max_sentence_length: int = 200
    filter_duplicates: bool = True

    class Config:
        populate_by_name = True


# Response models for API
class DatasetIntegrationResponse(BaseModel):
    """Response for dataset integration operations."""
    dataset: ExternalDataset
    processing_jobs: List[DatasetProcessingJob]
    estimated_completion_time: Optional[datetime] = None


class DatasetSearchResponse(BaseModel):
    """Response for dataset search operations."""
    datasets: List[ExternalDataset]
    total_count: int
    filters_applied: Dict[str, Any]
    suggestions: List[str] = []