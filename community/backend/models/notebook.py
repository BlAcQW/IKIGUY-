"""
Notebook sharing models for the African Language Community Platform
Enables sharing and rating of Jupyter notebooks for various language processing tasks
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from enum import Enum

class NotebookCategory(str, Enum):
    """Categories for different types of notebooks"""
    DATA_ACQUISITION = "data_acquisition"
    DATA_PROCESSING = "data_processing"
    ASR_TRAINING = "asr_training"
    TTS_TRAINING = "tts_training"
    LLM_TRAINING = "llm_training"
    EVALUATION = "evaluation"
    DEPLOYMENT = "deployment"
    RESEARCH = "research"
    TUTORIAL = "tutorial"
    OTHER = "other"

class NotebookDifficulty(str, Enum):
    """Difficulty levels for notebooks"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class NotebookStatus(str, Enum):
    """Status of notebook"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    FLAGGED = "flagged"

class VoteType(str, Enum):
    """Vote types for notebooks"""
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"

class NotebookMetadata(BaseModel):
    """Metadata extracted from Jupyter notebook"""
    kernel_name: Optional[str] = None
    language: Optional[str] = None
    cell_count: Optional[int] = None
    execution_time: Optional[float] = None
    last_executed: Optional[datetime] = None
    dependencies: List[str] = Field(default_factory=list)
    gpu_required: bool = False
    memory_requirements: Optional[str] = None

class NotebookVersion(BaseModel):
    """Version information for a notebook"""
    version: str
    file_path: str
    file_size: int
    checksum: str
    upload_date: datetime
    changelog: Optional[str] = None
    is_current: bool = False

class NotebookBase(BaseModel):
    """Base notebook model"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    category: NotebookCategory
    difficulty: NotebookDifficulty = NotebookDifficulty.INTERMEDIATE
    language_codes: List[str] = Field(default_factory=list, description="Language codes this notebook supports")
    tags: List[str] = Field(default_factory=list, max_length=20)
    is_public: bool = True
    license: str = "MIT"

class NotebookCreate(NotebookBase):
    """Model for creating a new notebook"""
    file_content: str = Field(..., description="Base64 encoded notebook content")

class NotebookUpdate(BaseModel):
    """Model for updating notebook metadata"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    category: Optional[NotebookCategory] = None
    difficulty: Optional[NotebookDifficulty] = None
    language_codes: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    license: Optional[str] = None

class NotebookVersionCreate(BaseModel):
    """Model for creating a new notebook version"""
    file_content: str = Field(..., description="Base64 encoded notebook content")
    changelog: Optional[str] = Field(None, max_length=1000)

class NotebookVote(BaseModel):
    """Model for notebook voting"""
    vote_type: VoteType
    comment: Optional[str] = Field(None, max_length=500)

class NotebookComment(BaseModel):
    """Model for notebook comments"""
    content: str = Field(..., min_length=1, max_length=1000)
    parent_comment_id: Optional[str] = None

class NotebookUsageStats(BaseModel):
    """Usage statistics for a notebook"""
    downloads: int = 0
    views: int = 0
    forks: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    avg_execution_time: Optional[float] = None

class NotebookInDB(NotebookBase):
    """Complete notebook model as stored in database"""
    id: str = Field(alias="_id")
    author_id: str
    author_name: str
    author_email: str
    status: NotebookStatus = NotebookStatus.DRAFT

    # File information
    current_version: str = "1.0.0"
    file_path: str
    file_size: int
    checksum: str

    # Metadata
    metadata: Optional[NotebookMetadata] = None

    # Versioning
    versions: List[NotebookVersion] = Field(default_factory=list)

    # Engagement
    upvotes: int = 0
    downvotes: int = 0
    rating: float = 0.0
    comment_count: int = 0

    # Usage statistics
    usage_stats: NotebookUsageStats = Field(default_factory=NotebookUsageStats)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

    # Moderation
    flagged_count: int = 0
    moderation_notes: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class NotebookResponse(BaseModel):
    """Response model for notebook APIs"""
    id: str
    title: str
    description: str
    category: NotebookCategory
    difficulty: NotebookDifficulty
    language_codes: List[str]
    tags: List[str]
    is_public: bool
    license: str
    author_name: str
    current_version: str
    file_size: int
    upvotes: int
    downvotes: int
    rating: float
    comment_count: int
    usage_stats: NotebookUsageStats
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]

    # User-specific fields (populated based on current user)
    user_vote: Optional[VoteType] = None
    is_bookmarked: bool = False
    is_owner: bool = False

class NotebookListResponse(BaseModel):
    """Response model for notebook listing"""
    notebooks: List[NotebookResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class NotebookSearchQuery(BaseModel):
    """Model for notebook search parameters"""
    query: Optional[str] = None
    category: Optional[NotebookCategory] = None
    difficulty: Optional[NotebookDifficulty] = None
    language_codes: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    author_id: Optional[str] = None
    min_rating: Optional[float] = None
    sort_by: str = "updated_at"  # created_at, updated_at, rating, upvotes, downloads
    sort_order: str = "desc"  # asc, desc
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

# MongoDB collection models
class NotebookVoteInDB(BaseModel):
    """Vote record in database"""
    id: str = Field(alias="_id")
    notebook_id: str
    user_id: str
    vote_type: VoteType
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class NotebookCommentInDB(BaseModel):
    """Comment record in database"""
    id: str = Field(alias="_id")
    notebook_id: str
    user_id: str
    user_name: str
    content: str
    parent_comment_id: Optional[str] = None
    replies: List[str] = Field(default_factory=list)  # List of reply comment IDs
    upvotes: int = 0
    downvotes: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = False

class NotebookBookmarkInDB(BaseModel):
    """Bookmark record in database"""
    id: str = Field(alias="_id")
    notebook_id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NotebookDownloadInDB(BaseModel):
    """Download record in database"""
    id: str = Field(alias="_id")
    notebook_id: str
    user_id: Optional[str] = None  # Can be anonymous
    ip_address: str
    user_agent: str
    downloaded_at: datetime = Field(default_factory=datetime.utcnow)

class NotebookViewInDB(BaseModel):
    """View record in database"""
    id: str = Field(alias="_id")
    notebook_id: str
    user_id: Optional[str] = None  # Can be anonymous
    ip_address: str
    user_agent: str
    viewed_at: datetime = Field(default_factory=datetime.utcnow)