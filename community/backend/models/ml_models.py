"""
ML Model registry models for African Language Community Platform.

Handles trained models (TTS, ASR, LLM, NMT) with versioning, performance metrics,
and multi-language support.
"""

from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId


class ModelType(str, Enum):
    """Types of ML models."""
    TTS = "tts"
    ASR = "asr"
    LLM = "llm"
    NMT = "nmt"  # Neural Machine Translation
    NER = "ner"  # Named Entity Recognition
    POS = "pos"  # Part-of-Speech Tagging
    SENTIMENT = "sentiment"
    CUSTOM = "custom"


class ModelArchitecture(str, Enum):
    """Model architecture types."""
    MELOTTS = "melotts"
    STYLETTS = "styletts"
    XTTS = "xtts"
    WHISPER = "whisper"
    MOSHI = "moshi"
    LLAMA = "llama"
    MISTRAL = "mistral"
    TRANSFORMER = "transformer"
    CUSTOM = "custom"


class DeploymentStatus(str, Enum):
    """Model deployment status."""
    EXPERIMENTAL = "experimental"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class AccessLevel(str, Enum):
    """Model access levels."""
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    RESTRICTED = "restricted"
    PRIVATE = "private"


class ModelVersion(BaseModel):
    """Model version information."""
    version: str = Field(..., description="Semantic version (e.g., v1.2.0)")
    released_at: datetime
    changelog: str
    storage_path: str
    performance_metrics: Dict[str, float] = {}
    model_size_mb: Optional[float] = None
    is_stable: bool = True
    is_deprecated: bool = False
    deprecation_reason: Optional[str] = None


class TrainingDataset(BaseModel):
    """Training dataset reference."""
    dataset_id: str = Field(..., description="Dataset ObjectId")
    version: str
    split: str = Field(..., description="train, validation, or test")
    hours: Optional[float] = None
    samples: Optional[int] = None


class KnownIssue(BaseModel):
    """Known issue with the model."""
    issue: str
    severity: str = Field(..., description="low, medium, high, critical")
    reported_by: str = Field(..., description="User ObjectId")
    reported_at: datetime
    workaround: Optional[str] = None
    is_resolved: bool = False


class PerformanceMetrics(BaseModel):
    """Model performance metrics."""
    # ASR metrics
    wer: Optional[float] = Field(None, ge=0, le=1, description="Word Error Rate")
    cer: Optional[float] = Field(None, ge=0, le=1, description="Character Error Rate")

    # TTS metrics
    mos: Optional[float] = Field(None, ge=1, le=5, description="Mean Opinion Score")
    rtf: Optional[float] = Field(None, ge=0, description="Real-Time Factor")

    # LLM metrics
    perplexity: Optional[float] = Field(None, ge=0, description="Perplexity")
    bleu: Optional[float] = Field(None, ge=0, le=100, description="BLEU score")

    # General metrics
    inference_time_ms: Optional[float] = Field(None, ge=0)
    throughput: Optional[float] = Field(None, ge=0, description="Samples per second")

    # Custom metrics
    custom_metrics: Dict[str, float] = {}


class MLModelCreate(BaseModel):
    """Model for creating a new ML model."""
    name: str = Field(..., min_length=3, max_length=200)
    model_type: ModelType
    architecture: ModelArchitecture

    # Language support
    languages: List[str] = Field(..., min_items=1, description="Language codes")
    primary_language: str
    is_multilingual: bool = False

    # Version
    version: str = Field(default="1.0.0", pattern=r'^\d+\.\d+\.\d+$')

    # Training references
    pipeline_id: Optional[str] = None
    parent_model_id: Optional[str] = Field(None, description="For fine-tuned models")
    base_model: Optional[str] = Field(None, description="Pretrained base model name")

    # Storage
    storage_path: str
    checkpoint_path: str
    config_path: Optional[str] = None

    # Performance
    performance_metrics: Optional[PerformanceMetrics] = None

    # Datasets
    training_datasets: List[TrainingDataset] = []
    evaluation_datasets: List[TrainingDataset] = []

    # Deployment
    deployment_status: DeploymentStatus = DeploymentStatus.EXPERIMENTAL
    deployment_url: Optional[HttpUrl] = None
    docker_image: Optional[str] = None

    # Access & Licensing
    license: str = "MIT"
    is_public: bool = True
    access_level: AccessLevel = AccessLevel.PUBLIC

    # Metadata
    description: Optional[str] = None
    tags: List[str] = []
    paper_url: Optional[HttpUrl] = None
    demo_url: Optional[HttpUrl] = None

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

    @validator('primary_language')
    def validate_primary_language(cls, v, values):
        """Ensure primary language is in languages list."""
        if 'languages' in values and v not in values['languages']:
            raise ValueError("Primary language must be in languages list")
        return v


class MLModelUpdate(BaseModel):
    """Model for updating an ML model."""
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    deployment_status: Optional[DeploymentStatus] = None
    deployment_url: Optional[HttpUrl] = None
    docker_image: Optional[str] = None
    is_public: Optional[bool] = None
    access_level: Optional[AccessLevel] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    paper_url: Optional[HttpUrl] = None
    demo_url: Optional[HttpUrl] = None


class MLModel(BaseModel):
    """Complete ML model document."""
    id: str = Field(alias="_id")
    model_uuid: str
    name: str
    model_type: ModelType
    architecture: ModelArchitecture

    # Version management
    version: str
    version_history: List[ModelVersion] = []

    # Language support
    languages: List[str]
    language_ids: List[str] = []  # ObjectIds as strings
    primary_language: str
    is_multilingual: bool

    # Training pipeline reference
    pipeline_id: Optional[str] = None
    parent_model_id: Optional[str] = None
    base_model: Optional[str] = None

    # Storage & files
    storage_path: str
    model_size_mb: Optional[float] = None
    checkpoint_path: str
    config_path: Optional[str] = None

    # Performance metrics
    performance_metrics: PerformanceMetrics

    # Dataset lineage
    training_datasets: List[TrainingDataset] = []
    evaluation_datasets: List[TrainingDataset] = []

    # Deployment
    deployment_status: DeploymentStatus
    deployment_url: Optional[str] = None
    docker_image: Optional[str] = None

    # Access & licensing
    license: str
    is_public: bool
    access_level: AccessLevel
    download_count: int = 0

    # Contributors
    created_by: str
    contributors: List[str] = []

    # Known issues
    known_issues: List[KnownIssue] = []

    # Metadata
    tags: List[str] = []
    description: Optional[str] = None
    paper_url: Optional[str] = None
    demo_url: Optional[str] = None

    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class ModelLanguageAssociation(BaseModel):
    """Association between a model and a language."""
    id: str = Field(alias="_id")
    model_id: str
    model_uuid: str
    language_id: str
    language_code: str
    language_family_id: str

    # Association type
    association_type: str = Field(..., description="primary, secondary, or supported")
    is_primary_language: bool = False

    # Performance for this language
    language_specific_metrics: Dict[str, float] = {}

    # Training data for this language
    training_hours: Optional[float] = None
    training_samples: Optional[int] = None
    datasets_used: List[str] = []

    # Support level
    support_quality: str = Field(..., description="excellent, good, fair, or limited")
    support_notes: Optional[str] = None

    # Dialect support
    dialects_supported: List[str] = []

    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class ModelSearchQuery(BaseModel):
    """Model search parameters."""
    query: Optional[str] = None
    model_type: Optional[ModelType] = None
    architecture: Optional[ModelArchitecture] = None
    languages: Optional[List[str]] = None
    deployment_status: Optional[DeploymentStatus] = None
    is_public: Optional[bool] = None
    min_performance: Optional[float] = None
    tags: Optional[List[str]] = None
    sort_by: str = "updated_at"
    sort_order: str = "desc"
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class ModelListResponse(BaseModel):
    """Response for model listing."""
    models: List[MLModel]
    total: int
    page: int
    page_size: int
    total_pages: int


class ModelVersionCreate(BaseModel):
    """Model for creating a new model version."""
    version: str = Field(..., pattern=r'^\d+\.\d+\.\d+$')
    changelog: str
    storage_path: str
    checkpoint_path: str
    config_path: Optional[str] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    model_size_mb: Optional[float] = None
    is_stable: bool = True

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


class ModelIssueCreate(BaseModel):
    """Model for reporting a model issue."""
    issue: str = Field(..., min_length=10, max_length=1000)
    severity: str = Field(..., description="low, medium, high, or critical")
    workaround: Optional[str] = Field(None, max_length=500)

    @validator('severity')
    def validate_severity(cls, v):
        """Validate severity level."""
        valid_severities = ['low', 'medium', 'high', 'critical']
        if v not in valid_severities:
            raise ValueError(f"Severity must be one of {valid_severities}")
        return v


class ModelDownloadRequest(BaseModel):
    """Model download request."""
    model_uuid: str
    version: Optional[str] = None  # If None, download latest
    include_config: bool = True
    include_checksum: bool = True


class ModelDownloadResponse(BaseModel):
    """Model download response."""
    model_uuid: str
    version: str
    download_url: str
    config_url: Optional[str] = None
    checksum: Optional[str] = None
    expires_at: datetime
    file_size_mb: float


class ModelStats(BaseModel):
    """Statistics for ML models."""
    total_models: int
    models_by_type: Dict[str, int]
    models_by_language: Dict[str, int]
    models_by_status: Dict[str, int]
    total_downloads: int
    multilingual_models: int
    average_performance: Dict[str, float] = {}
