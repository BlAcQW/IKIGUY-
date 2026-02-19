"""
Tool Call Logging Models for MongoDB.
Tracks all RAG knowledge base queries for analytics and monitoring.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ToolCallStatus(str, Enum):
    """Status of a tool call."""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


class CityNormalization(BaseModel):
    """City normalization details."""
    original: str
    normalized: Optional[str] = None
    confidence: float = 0.0
    method: str = "none"
    is_region: bool = False  # Flag if input was detected as a region


class ToolCallLog(BaseModel):
    """
    MongoDB model for logging RAG tool calls.

    Retention: 7 days (TTL index on created_at)
    """
    # Identifiers
    id: Optional[str] = Field(default=None, alias="_id")
    tool_call_id: str  # VAPI toolCallId
    company_name: str  # e.g., "premier_health_production"

    # Query details
    query_original: str  # Original query from user
    query_normalized: Optional[str] = None  # After city normalization
    city_normalization: Optional[CityNormalization] = None

    # Response details
    response: str
    response_length: int
    status: ToolCallStatus = ToolCallStatus.SUCCESS
    error_message: Optional[str] = None

    # Performance metrics
    processing_time: float  # Total time in seconds
    retrieval_time: Optional[float] = None  # Vector search time
    llm_time: Optional[float] = None  # LLM generation time

    # RAG metrics
    documents_retrieved: int = 0
    documents_sent_to_llm: int = 0  # Track how many we actually used
    confidence_score: float = 0.0
    requires_escalation: bool = False
    escalation_reason: Optional[str] = None

    # Source documents (for analysis)
    sources_used: List[str] = []  # List of document titles

    # Request metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    vapi_call_id: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Flags for analysis
    is_cached: bool = False  # Was response served from cache?
    cache_key: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PreComputedQuery(BaseModel):
    """
    Pre-computed responses for common queries.

    Regenerated daily to ensure freshness.
    """
    id: Optional[str] = Field(default=None, alias="_id")

    # Query details
    query_pattern: str  # e.g., "general practitioners in MADINA"
    company_name: str

    # Pre-computed response
    response: str
    confidence_score: float
    sources_used: List[str]

    # Metadata
    query_count: int = 0  # How many times this query was made
    last_requested: Optional[datetime] = None

    # Computation details
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(days=1)
    )

    # Performance
    avg_processing_time: float = 0.0  # Before pre-compute

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MonitoringMetrics(BaseModel):
    """Real-time monitoring metrics."""

    # Time period
    period_start: datetime
    period_end: datetime

    # Query volume
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    cached_responses: int = 0

    # Performance
    avg_response_time: float = 0.0
    min_response_time: float = 0.0
    max_response_time: float = 0.0
    p50_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0

    # Quality
    avg_confidence: float = 0.0
    escalation_rate: float = 0.0

    # Top queries
    top_queries: List[Dict[str, Any]] = []
    top_cities: List[Dict[str, Any]] = []
    top_specialties: List[Dict[str, Any]] = []

    # Errors
    error_count: int = 0
    common_errors: List[Dict[str, Any]] = []


class QueryAnalytics(BaseModel):
    """Analytics for a specific query pattern."""
    query_pattern: str
    total_count: int
    avg_confidence: float
    avg_processing_time: float
    success_rate: float
    last_queried: datetime
    is_pre_computed: bool = False
