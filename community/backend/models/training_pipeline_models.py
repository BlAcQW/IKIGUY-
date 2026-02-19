"""
Training pipeline models for African Language Community Platform.

Handles MLOps-style pipeline tracking with detailed stage information,
metrics, and artifacts.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId


class PipelineStage(str, Enum):
    """Training pipeline stages."""
    DATA_ACQUISITION = "data_acquisition"
    PREPROCESSING = "preprocessing"
    TRAINING = "training"
    EVALUATION = "evaluation"
    DEPLOYMENT = "deployment"


class StageStatus(str, Enum):
    """Status of a pipeline stage."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelinePriority(str, Enum):
    """Pipeline priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PreprocessingDetails(BaseModel):
    """Detailed preprocessing configuration."""
    frequency: Optional[str] = Field(None, description="e.g., 16kHz, 22.05kHz")
    format: Optional[str] = Field(None, description="e.g., wav, mp3")
    normalization: Optional[str] = Field(None, description="e.g., peak, rms")
    augmentations: List[str] = []

    # Phonetic analysis
    phonetic_analysis: Optional[Dict[str, Any]] = Field(
        None,
        description="Phoneme count, tone levels, click consonants, etc."
    )

    # Quality filters
    quality_filters: Optional[Dict[str, Any]] = Field(
        None,
        description="SNR thresholds, silence ratio, duration limits"
    )


class TrainingConfig(BaseModel):
    """Training configuration details."""
    base_model: Optional[str] = None
    epochs: int
    current_epoch: Optional[int] = None
    batch_size: int
    learning_rate: float
    optimizer: str
    scheduler: Optional[str] = None
    hardware: Optional[str] = Field(None, description="e.g., 4x A100 GPUs")
    mixed_precision: bool = False
    gradient_accumulation_steps: int = 1


class StageArtifact(BaseModel):
    """Artifact produced by a pipeline stage."""
    name: str
    path: str
    size_mb: Optional[float] = None
    artifact_type: str = Field(..., description="dataset, model, report, config")
    description: Optional[str] = None
    checksum: Optional[str] = None


class PipelineStageInfo(BaseModel):
    """Detailed information about a pipeline stage."""
    stage_name: PipelineStage
    status: StageStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None

    # Stage-specific details
    preprocessing_details: Optional[PreprocessingDetails] = None
    training_config: Optional[TrainingConfig] = None
    evaluation_plan: Optional[Dict[str, Any]] = None

    # Artifacts produced
    artifacts: List[StageArtifact] = []

    # Metrics
    metrics: Dict[str, Any] = {}

    # Checkpoints (for training stage)
    checkpoints: List[Dict[str, Any]] = []

    # Notes and logs
    notes: Optional[str] = None
    logs: List[str] = []
    error_message: Optional[str] = None

    # Responsible user
    responsible_user: Optional[str] = Field(None, description="User ObjectId")

    # Resource usage
    resource_usage: Optional[Dict[str, float]] = Field(
        None,
        description="GPU hours, cost, memory peak, etc."
    )


class DatasetReference(BaseModel):
    """Reference to a dataset used in training."""
    dataset_id: str
    version: str
    role: str = Field(..., description="training, validation, or test")
    storage_path: Optional[str] = None


class ExperimentConfig(BaseModel):
    """Reproducibility configuration."""
    seed: int = 42
    framework: str = Field(..., description="pytorch, tensorflow, jax")
    framework_version: str
    python_version: str
    cuda_version: Optional[str] = None
    environment_variables: Dict[str, str] = {}


class TrainingPipelineCreate(BaseModel):
    """Model for creating a new training pipeline."""
    name: str = Field(..., min_length=3, max_length=200)
    model_type: str = Field(..., description="tts, asr, llm, nmt")

    # Initial stage
    current_stage: PipelineStage = PipelineStage.DATA_ACQUISITION

    # Datasets
    datasets: List[DatasetReference] = []

    # Target version
    target_version: str = Field(..., pattern=r'^\d+\.\d+\.\d+$')

    # Reproducibility
    experiment_config: Optional[ExperimentConfig] = None

    # Team
    team_members: List[str] = []

    # Priority
    priority: PipelinePriority = PipelinePriority.MEDIUM

    # Description
    description: Optional[str] = None
    tags: List[str] = []

    @validator('target_version')
    def validate_version(cls, v):
        """Validate semantic version format."""
        parts = v.split('.')
        if len(parts) != 3:
            raise ValueError("Version must be in format X.Y.Z")
        for part in parts:
            if not part.isdigit():
                raise ValueError("Version parts must be integers")
        return v


class TrainingPipelineUpdate(BaseModel):
    """Model for updating a training pipeline."""
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    current_stage: Optional[PipelineStage] = None
    stage_progress: Optional[float] = Field(None, ge=0, le=100)
    priority: Optional[PipelinePriority] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class StageUpdate(BaseModel):
    """Model for updating a specific pipeline stage."""
    status: StageStatus
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    metrics: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    error_message: Optional[str] = None


class TrainingPipeline(BaseModel):
    """Complete training pipeline document."""
    id: str = Field(alias="_id")
    pipeline_uuid: str
    name: str
    model_type: str

    # Current state
    current_stage: PipelineStage
    stage_progress: float = Field(0.0, ge=0, le=100)

    # Pipeline stages
    stages: List[PipelineStageInfo] = []

    # Version & results
    target_version: str
    result_model_id: Optional[str] = None

    # Datasets used
    datasets: List[DatasetReference] = []

    # Reproducibility
    experiment_config: Optional[ExperimentConfig] = None

    # Collaboration
    team_members: List[str] = []
    created_by: str

    # Status
    is_active: bool = True
    priority: PipelinePriority

    # Metadata
    description: Optional[str] = None
    tags: List[str] = []

    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class PipelineArtifactUpload(BaseModel):
    """Model for uploading a pipeline artifact."""
    artifact_name: str
    artifact_type: str = Field(..., description="dataset, model, report, config")
    stage_name: PipelineStage
    file_path: str  # Relative path in storage
    description: Optional[str] = None
    metadata: Dict[str, Any] = {}


class PipelineMetricsUpdate(BaseModel):
    """Model for updating pipeline metrics."""
    stage_name: PipelineStage
    metrics: Dict[str, Any]
    append: bool = False  # If True, append to existing metrics; if False, replace


class PipelineSearchQuery(BaseModel):
    """Pipeline search parameters."""
    query: Optional[str] = None
    model_type: Optional[str] = None
    current_stage: Optional[PipelineStage] = None
    is_active: Optional[bool] = None
    priority: Optional[PipelinePriority] = None
    created_by: Optional[str] = None
    sort_by: str = "updated_at"
    sort_order: str = "desc"
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PipelineListResponse(BaseModel):
    """Response for pipeline listing."""
    pipelines: List[TrainingPipeline]
    total: int
    page: int
    page_size: int
    total_pages: int


class PipelineStageProgress(BaseModel):
    """Summary of pipeline stage progress."""
    pipeline_id: str
    pipeline_name: str
    current_stage: PipelineStage
    stage_progress: float
    overall_progress: float
    estimated_completion: Optional[datetime] = None
    is_active: bool


class PipelineStats(BaseModel):
    """Statistics for training pipelines."""
    total_pipelines: int
    active_pipelines: int
    completed_pipelines: int
    failed_pipelines: int
    pipelines_by_stage: Dict[str, int]
    pipelines_by_type: Dict[str, int]
    average_duration_days: Optional[float] = None


class CheckpointCreate(BaseModel):
    """Model for creating a training checkpoint."""
    epoch: int
    path: str
    metrics: Dict[str, float]
    is_best: bool = False
    notes: Optional[str] = None


class PipelineCompletion(BaseModel):
    """Model for marking a pipeline as complete."""
    result_model_id: str
    final_metrics: Dict[str, float]
    completion_notes: Optional[str] = None
    success: bool = True
