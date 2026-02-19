"""Data models for Core Backend."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from enum import Enum


class EventType(str, Enum):
    """Event types for the event bus."""

    VOICE_SESSION_STARTED = "voice_session_started"
    VOICE_SESSION_ENDED = "voice_session_ended"
    VOICE_TURN_COMPLETED = "voice_turn_completed"
    VOICE_ERROR = "voice_error"
    VOICE_WARNING = "voice_warning"
    VOICE_INFO = "voice_info"


class VoiceProvider(BaseModel):
    """Voice Provider model for database storage."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Provider name (e.g., ElevenLabs, Google Cloud, Azure)")
    display_name: str = Field(..., description="Display name for UI")
    description: str = Field(..., description="Provider description")
    website: str = Field(..., description="Provider website URL")
    api_base_url: str = Field(..., description="API base URL")
    provider_type: str = Field(..., description="Provider type (STT, TTS, or both)")
    pricing_model: str = Field(..., description="Pricing model (per_character, per_minute, etc.)")
    features: List[str] = Field(default_factory=list, description="Available features")
    supported_languages: List[str] = Field(default_factory=list, description="Supported languages")
    supported_voices: int = Field(default=0, description="Number of available voices")
    max_audio_length: int = Field(default=0, description="Maximum audio length in seconds")
    latency_ms: int = Field(default=0, description="Average latency in milliseconds")
    is_active: bool = Field(default=True, description="Whether provider is active")
    is_default: bool = Field(default=False, description="Whether this is the default provider")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Voice(BaseModel):
    """Voice model for database storage."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    provider_id: str = Field(..., description="Reference to voice provider")
    name: str = Field(..., description="Voice name (e.g., en-US-Neural2-A)")
    display_name: str = Field(..., description="Display name for UI")
    description: str = Field(..., description="Voice description")
    gender: str = Field(..., description="Voice gender (male, female, neutral)")
    language: str = Field(..., description="Voice language code")
    language_name: str = Field(..., description="Voice language name")
    country: str = Field(default="", description="Voice country code")
    country_name: str = Field(default="", description="Voice country name")
    voice_type: str = Field(default="neural", description="Voice type (neural, standard, custom)")
    sample_rate: int = Field(default=24000, description="Sample rate in Hz")
    quality: str = Field(default="standard", description="Voice quality (standard, hd, ultra)")
    features: List[str] = Field(default_factory=list, description="Voice features")
    is_active: bool = Field(default=True, description="Whether voice is active")
    is_default: bool = Field(default=False, description="Whether this is the default voice")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LLMProvider(BaseModel):
    """LLM Provider model for database storage."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Provider name (e.g., OpenAI, Anthropic)")
    display_name: str = Field(..., description="Display name for UI")
    description: str = Field(..., description="Provider description")
    website: str = Field(..., description="Provider website URL")
    api_base_url: str = Field(..., description="API base URL")
    pricing_model: str = Field(..., description="Pricing model (per_token, per_request, etc.)")
    features: List[str] = Field(default_factory=list, description="Available features")
    supported_languages: List[str] = Field(default_factory=list, description="Supported languages")
    max_context_length: int = Field(..., description="Maximum context length in tokens")
    is_active: bool = Field(default=True, description="Whether provider is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LLMModel(BaseModel):
    """LLM Model model for database storage."""
    
    model_config = {"protected_namespaces": ()}
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    provider_id: str = Field(..., description="Reference to LLM provider")
    name: str = Field(..., description="Model name (e.g., gpt-4o, claude-3-5-sonnet)")
    display_name: str = Field(..., description="Display name for UI")
    description: str = Field(..., description="Model description")
    model_type: str = Field(..., description="Model type (chat, completion, etc.)")
    context_length: int = Field(..., description="Context length in tokens")
    input_cost_per_1k_tokens: float = Field(..., description="Input cost per 1K tokens")
    output_cost_per_1k_tokens: float = Field(..., description="Output cost per 1K tokens")
    capabilities: List[str] = Field(default_factory=list, description="Model capabilities")
    supported_languages: List[str] = Field(default_factory=list, description="Supported languages")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")
    is_active: bool = Field(default=True, description="Whether model is active")
    is_default: bool = Field(default=False, description="Whether this is the default model")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VoiceTurn(BaseModel):
    """Voice turn model for database storage."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str = Field(..., description="Voice session ID")
    turn_number: int = Field(..., description="Turn number in session")
    user_audio_samples: List[int] = Field(default_factory=list, description="User audio samples")
    user_text: str = Field(default="", description="Transcribed user text")
    assistant_text: str = Field(default="", description="Assistant response text")
    assistant_audio_samples: List[int] = Field(default_factory=list, description="Assistant audio samples")
    stt_provider: str = Field(default="", description="STT provider used")
    stt_model: str = Field(default="", description="STT model used")
    tts_provider: str = Field(default="", description="TTS provider used")
    tts_voice: str = Field(default="", description="TTS voice used")
    llm_provider: str = Field(default="", description="LLM provider used")
    llm_model: str = Field(default="", description="LLM model used")
    language: str = Field(default="", description="Detected language")
    country: str = Field(default="", description="Detected country")
    confidence: float = Field(default=0.0, description="Confidence score")
    duration_ms: int = Field(default=0, description="Turn duration in milliseconds")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VoiceSession(BaseModel):
    """Voice session model for database storage."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID")
    assistant_id: str = Field(..., description="Assistant ID")
    session_type: str = Field(default="conversation", description="Session type")
    status: str = Field(default="active", description="Session status")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = Field(default=None, description="Session end time")
    total_duration_ms: int = Field(default=0, description="Total session duration")
    total_turns: int = Field(default=0, description="Total number of turns")
    language: str = Field(default="", description="Primary language used")
    country: str = Field(default="", description="Primary country detected")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Session metadata")
    turns: List[VoiceTurn] = Field(default_factory=list, description="Session turns")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Event(BaseModel):
    """Event model for the event bus."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    type: EventType = Field(..., description="Event type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(default="", description="Event source")


class VoiceAgent(BaseModel):
    """Voice Agent model for database storage."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Agent name")
    description: str = Field(default="", description="Agent description")
    user_id: str = Field(..., description="Owner user ID")
    stt_provider: str = Field(..., description="STT provider")
    stt_model: str = Field(..., description="STT model")
    tts_provider: str = Field(..., description="TTS provider")
    tts_voice: str = Field(..., description="TTS voice")
    llm_provider: str = Field(..., description="LLM provider")
    llm_model: str = Field(..., description="LLM model")
    language: str = Field(default="English", description="Primary language")
    country: str = Field(default="Ghana", description="Primary country")
    detect_language: bool = Field(default=True, description="Enable language detection")
    system_prompt: str = Field(default="", description="System prompt")
    is_active: bool = Field(default=True, description="Whether agent is active")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Agent metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AssistantCreate(BaseModel):
    """Request model for creating an assistant."""
    name: str = Field(..., description="Assistant name")
    description: str = Field(default="", description="Assistant description")
    user_id: str = Field(..., description="User ID")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    template_id: str = Field(default="blank", description="Template ID")


class KbSource(BaseModel):
    """Knowledge Base Source model for database storage."""
    
    id: UUID = Field(default_factory=uuid4, description="Source ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    type: str = Field(..., description="Source type (file, url, text)")
    uri: str = Field(..., description="Source URI or identifier")
    status: str = Field(default="ready", description="Source status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class KbChunk(BaseModel):
    """Knowledge Base Chunk model for database storage."""
    
    id: UUID = Field(default_factory=uuid4, description="Chunk ID")
    source_id: UUID = Field(..., description="Reference to source")
    text: str = Field(..., description="Chunk text content")
    embedding: List[float] = Field(..., description="Text embedding vector")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class KbIngestRequest(BaseModel):
    """Request model for knowledge base ingestion."""
    
    tenant_id: UUID = Field(..., description="Tenant ID")
    content: Optional[str] = Field(default=None, description="Raw text content")
    url: Optional[str] = Field(default=None, description="URL to fetch content from")


class KbSearchRequest(BaseModel):
    """Request model for knowledge base search."""
    
    tenant_id: UUID = Field(..., description="Tenant ID")
    query: str = Field(..., description="Search query")
    top_k: int = Field(default=5, description="Number of results to return")


class KbSearchResult(BaseModel):
    """Result model for knowledge base search."""
    
    source_id: UUID = Field(..., description="Source ID")
    text: str = Field(..., description="Chunk text")
    score: float = Field(..., description="Search score")


class ServiceAccountCreate(BaseModel):
    """Request model for creating a service account."""
    
    name: str = Field(..., description="Account name")
    tenant_id: UUID = Field(..., description="Tenant ID")
    permissions: Optional[Dict[str, Any]] = Field(default=None, description="Account permissions")
    is_active: bool = Field(default=True, description="Whether account is active")


class ServiceAccount(BaseModel):
    """Service Account model for database storage."""
    
    id: UUID = Field(default_factory=uuid4, description="Account ID")
    name: str = Field(..., description="Account name")
    token: str = Field(..., description="Authentication token")
    tenant_id: UUID = Field(..., description="Tenant ID")
    permissions: Optional[Dict[str, Any]] = Field(default=None, description="Account permissions")
    is_active: bool = Field(default=True, description="Whether account is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class HandoverRequest(BaseModel):
    """Request model for session handover."""
    
    target: str = Field(..., description="Handover target")


class Message(BaseModel):
    """Message model for session communication."""
    
    role: str = Field(..., description="Message role (user, assistant)")
    text: str = Field(..., description="Message text")


class SessionStatus(BaseModel):
    """Session status model."""
    
    handover_target: Optional[str] = Field(default=None, description="Handover target")
    messages: List[Message] = Field(default_factory=list, description="Session messages")


class CampaignCreate(BaseModel):
    """Request model for creating a campaign."""

    name: str = Field(..., description="Campaign name")
    description: Optional[str] = Field(default=None, description="Campaign description")
    assistant_id: Optional[UUID] = Field(default=None, description="Assistant ID")
    audience_id: Optional[UUID] = Field(default=None, description="Audience ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    status: str = Field(default="draft", description="Campaign status")

    # Template and integration support
    template_id: Optional[str] = Field(default=None, description="Campaign template ID")
    category: Optional[str] = Field(default=None, description="Campaign category (sales, marketing, support, etc.)")
    difficulty: Optional[str] = Field(default=None, description="Template difficulty level")
    features: Optional[List[str]] = Field(default=None, description="Template features")
    default_integrations: Optional[List[str]] = Field(default=None, description="Default integrations from template")
    integrations: Optional[Dict[str, Any]] = Field(default=None, description="Configured integrations")

    # n8n workflow integration
    n8n_template_id: Optional[int] = Field(default=None, description="n8n template ID from repository")
    n8n_workflow_id: Optional[str] = Field(default=None, description="Created n8n workflow ID")
    n8n_workflow_json: Optional[Dict[str, Any]] = Field(default=None, description="n8n workflow configuration JSON")
    n8n_config: Optional[Dict[str, Any]] = Field(default=None, description="n8n workflow configuration")


class Campaign(BaseModel):
    """Campaign model for database storage."""

    id: UUID = Field(default_factory=uuid4, description="Campaign ID")
    name: str = Field(..., description="Campaign name")
    description: Optional[str] = Field(default=None, description="Campaign description")
    assistant_id: Optional[UUID] = Field(default=None, description="Assistant ID")
    audience_id: Optional[UUID] = Field(default=None, description="Audience ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    status: str = Field(default="draft", description="Campaign status")

    # Template and integration support
    template_id: Optional[str] = Field(default=None, description="Campaign template ID")
    category: Optional[str] = Field(default=None, description="Campaign category (sales, marketing, support, etc.)")
    difficulty: Optional[str] = Field(default=None, description="Template difficulty level")
    features: Optional[List[str]] = Field(default=None, description="Template features")
    default_integrations: Optional[List[str]] = Field(default=None, description="Default integrations from template")
    integrations: Optional[Dict[str, Any]] = Field(default=None, description="Configured integrations")

    # n8n workflow integration
    n8n_template_id: Optional[int] = Field(default=None, description="n8n template ID from repository")
    n8n_workflow_id: Optional[str] = Field(default=None, description="Created n8n workflow ID")
    n8n_workflow_json: Optional[Dict[str, Any]] = Field(default=None, description="n8n workflow configuration JSON")
    n8n_config: Optional[Dict[str, Any]] = Field(default=None, description="n8n workflow configuration")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DemoDeployRequest(BaseModel):
    """Request model for demo deployment."""
    
    fileName: str = Field(..., description="Demo file name")
    html: str = Field(..., description="HTML content for the demo")


class EdgeSyncResponse(BaseModel):
    """Response model for edge synchronization."""
    
    license: Optional[Dict[str, Any]] = Field(default=None, description="License information")
    capabilities: List[str] = Field(default_factory=list, description="Available capabilities")


class EventRecord(BaseModel):
    """Event Record model for database storage."""
    
    id: UUID = Field(default_factory=uuid4, description="Event record ID")
    event_type: str = Field(..., description="Event type")
    tenant_id: UUID = Field(..., description="Tenant ID")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Event data")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Assistant(BaseModel):
    """Assistant model for database storage."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Assistant name")
    description: str = Field(default="", description="Assistant description")
    user_id: str = Field(..., description="Owner user ID")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    template_id: str = Field(default="blank", description="Template used for creation")
    status: str = Field(default="draft", description="Assistant status (draft, published)")
    
    # Model Configuration
    llm_provider: str = Field(default="", description="LLM provider")
    llm_model: str = Field(default="", description="LLM model")
    first_message_mode: str = Field(default="assistant_first", description="First message mode")
    first_message: str = Field(default="", description="First message text")
    system_prompt: str = Field(default="", description="System prompt")
    
    # Voice Configuration
    tts_provider: str = Field(default="", description="TTS provider")
    tts_model: str = Field(default="meta_mms", description="TTS model (meta_mms, meta_tts_aka)")
    tts_voice: str = Field(default="", description="TTS voice")
    language: str = Field(default="en", description="Primary language")
    country: str = Field(default="US", description="Primary country")
    
    # Voice Parameters
    background_sound: str = Field(default="default", description="Background sound setting")
    background_sound_url: str = Field(default="", description="Background sound URL")
    input_min_characters: int = Field(default=30, description="Minimum input characters")
    punctuation_boundaries: str = Field(default="", description="Punctuation boundaries")
    stability: float = Field(default=0.5, description="Voice stability (0-1)")
    clarity_similarity: float = Field(default=0.75, description="Clarity and similarity (0-1)")
    speed: float = Field(default=1.0, description="Voice speed (0.5-2)")
    style_exaggeration: float = Field(default=0.0, description="Style exaggeration (0-1)")
    optimize_streaming_latency: float = Field(default=0.0, description="Optimize streaming latency (0-1)")
    
    # Transcriber Configuration
    stt_provider: str = Field(default="", description="STT provider")
    stt_model: str = Field(default="", description="STT model")
    background_denoising: bool = Field(default=False, description="Enable background denoising")
    confidence_threshold: float = Field(default=0.4, description="Confidence threshold (0-1)")
    use_numerals: bool = Field(default=False, description="Use numerals in transcription")
    
    # Files/Knowledge Base
    knowledge_base_files: List[str] = Field(default_factory=list, description="Knowledge base file IDs")

    # Phone Number Integration (.fastphone() and provider numbers)
    phone_number_ids: List[str] = Field(default_factory=list, description="Assigned phone number IDs")
    test_phone_number: Optional[str] = Field(default=None, description="Temporary test phone number from .fastphone()")
    test_phone_country: Optional[str] = Field(default=None, description="Test phone country code")
    test_phone_expires_at: Optional[datetime] = Field(default=None, description="Test phone expiration time")

    # Shareable Testing Link (.ui.launch())
    shareable_link: Optional[str] = Field(default=None, description="Shareable testing link from .ui.launch()")
    shareable_link_expires_at: Optional[datetime] = Field(default=None, description="Shareable link expiration time")
    shareable_link_active: bool = Field(default=False, description="Whether shareable link is active")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Assistant metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OrganizationRole(str, Enum):
    """Organization role types."""

    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"
    UNIVERSAL_ADMIN = "universal_admin"


class InvitationStatus(str, Enum):
    """Invitation status types."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class Organization(BaseModel):
    """Organization model for database storage."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Organization name")
    display_name: str = Field(..., description="Display name for UI")
    description: Optional[str] = Field(default="", description="Organization description")

    # Organization Info
    industry: Optional[str] = Field(default="", description="Industry sector")
    company_size: Optional[str] = Field(default="", description="Company size category")
    website: Optional[str] = Field(default="", description="Company website")
    phone: Optional[str] = Field(default="", description="Contact phone number")
    address: Optional[str] = Field(default="", description="Business address")

    # Products/Services
    products: List[str] = Field(default_factory=list, description="Organization products/services")
    target_audience: Optional[str] = Field(default="", description="Target audience description")
    key_markets: List[str] = Field(default_factory=list, description="Key markets/regions")

    # Style Settings
    style_settings: Dict[str, Any] = Field(default_factory=dict, description="Organization style configuration")

    # Settings
    is_active: bool = Field(default=True, description="Whether organization is active")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Organization settings")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OrganizationUser(BaseModel):
    """Organization user membership model."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str = Field(..., description="Organization ID")
    user_id: str = Field(..., description="User ID (from Supabase)")
    email: str = Field(..., description="User email")
    role: OrganizationRole = Field(default=OrganizationRole.MEMBER, description="User role in organization")

    # User Info
    first_name: Optional[str] = Field(default="", description="User first name")
    last_name: Optional[str] = Field(default="", description="User last name")
    display_name: Optional[str] = Field(default="", description="Display name")
    avatar_url: Optional[str] = Field(default="", description="User avatar URL")

    # Permissions
    permissions: Dict[str, bool] = Field(default_factory=dict, description="Specific permissions")

    # Status
    is_active: bool = Field(default=True, description="Whether membership is active")
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: Optional[datetime] = Field(default=None, description="Last activity timestamp")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OrganizationInvitation(BaseModel):
    """Organization invitation model."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str = Field(..., description="Organization ID")
    email: str = Field(..., description="Invitee email")
    role: OrganizationRole = Field(default=OrganizationRole.MEMBER, description="Invited role")

    # Invitation Details
    invited_by_user_id: str = Field(..., description="User ID who sent invitation")
    invited_by_email: str = Field(..., description="Email of user who sent invitation")
    invitation_token: str = Field(..., description="Unique invitation token")

    # Status
    status: InvitationStatus = Field(default=InvitationStatus.PENDING, description="Invitation status")
    expires_at: datetime = Field(..., description="Invitation expiry date")

    # Response Details
    responded_at: Optional[datetime] = Field(default=None, description="Response timestamp")
    response_message: Optional[str] = Field(default="", description="Response message")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OrganizationStyleSettings(BaseModel):
    """Organization style settings model."""

    # Brand Colors
    primary_color: Optional[str] = Field(default="#3B82F6", description="Primary brand color")
    secondary_color: Optional[str] = Field(default="#6B7280", description="Secondary brand color")
    accent_color: Optional[str] = Field(default="#F59E0B", description="Accent color")

    # Logo & Assets
    logo_url: Optional[str] = Field(default="", description="Organization logo URL")
    favicon_url: Optional[str] = Field(default="", description="Favicon URL")
    banner_url: Optional[str] = Field(default="", description="Banner/header image URL")

    # Typography
    font_family: Optional[str] = Field(default="Inter", description="Primary font family")
    heading_font: Optional[str] = Field(default="Inter", description="Heading font family")

    # Voice & Tone
    brand_voice: Optional[str] = Field(default="professional", description="Brand voice style")
    tone_of_voice: Optional[str] = Field(default="friendly", description="Communication tone")

    # Campaign Defaults
    default_language: Optional[str] = Field(default="en", description="Default language for campaigns")
    default_voice_provider: Optional[str] = Field(default="", description="Default voice provider")
    default_voice_model: Optional[str] = Field(default="", description="Default voice model")

    # Custom Fields
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom style fields")


# Request/Response Models
class OrganizationCreate(BaseModel):
    """Request model for creating an organization."""

    name: Optional[str] = Field(default=None, description="Organization name (auto-generated from display_name if not provided)")
    display_name: str = Field(..., description="Display name")
    description: Optional[str] = Field(default="", description="Description")
    industry: Optional[str] = Field(default="", description="Industry")
    website: Optional[str] = Field(default="", description="Website")


class OrganizationUpdate(BaseModel):
    """Request model for updating an organization."""

    name: Optional[str] = Field(default=None, description="Organization name")
    display_name: Optional[str] = Field(default=None, description="Display name")
    description: Optional[str] = Field(default=None, description="Description")
    industry: Optional[str] = Field(default=None, description="Industry")
    company_size: Optional[str] = Field(default=None, description="Company size")
    website: Optional[str] = Field(default=None, description="Website")
    phone: Optional[str] = Field(default=None, description="Phone")
    address: Optional[str] = Field(default=None, description="Address")
    products: Optional[List[str]] = Field(default=None, description="Products")
    target_audience: Optional[str] = Field(default=None, description="Target audience")
    key_markets: Optional[List[str]] = Field(default=None, description="Key markets")


class OrganizationUserUpdate(BaseModel):
    """Request model for updating organization user."""

    role: Optional[OrganizationRole] = Field(default=None, description="User role")
    permissions: Optional[Dict[str, bool]] = Field(default=None, description="Permissions")
    is_active: Optional[bool] = Field(default=None, description="Active status")


class OrganizationInviteRequest(BaseModel):
    """Request model for inviting users to organization."""

    email: str = Field(..., description="Email to invite")
    role: OrganizationRole = Field(default=OrganizationRole.MEMBER, description="Role to assign")
    message: Optional[str] = Field(default="", description="Invitation message")


class OrganizationInviteResponse(BaseModel):
    """Response model for invitation actions."""

    invitation_token: str = Field(..., description="Invitation token")
    accepted: bool = Field(..., description="Whether invitation was accepted")
    message: Optional[str] = Field(default="", description="Response message")


# MongoDB Authentication Models

class User(BaseModel):
    """User model for MongoDB-based authentication."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    email: str = Field(..., description="User email address")
    password_hash: str = Field(..., description="Hashed password")
    first_name: Optional[str] = Field(default="", description="User first name")
    last_name: Optional[str] = Field(default="", description="User last name")
    display_name: Optional[str] = Field(default="", description="Display name")
    avatar_url: Optional[str] = Field(default="", description="Avatar URL")

    # Status and verification
    is_active: bool = Field(default=True, description="Whether user account is active")
    is_verified: bool = Field(default=False, description="Whether email is verified")
    email_verified_at: Optional[datetime] = Field(default=None, description="Email verification timestamp")

    # Organization context
    primary_organization_id: Optional[str] = Field(default=None, description="Primary organization ID")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="User metadata")
    last_login_at: Optional[datetime] = Field(default=None, description="Last login timestamp")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserSession(BaseModel):
    """User session model for token management."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID")
    token: str = Field(..., description="JWT token")
    refresh_token: str = Field(..., description="Refresh token")

    # Session info
    expires_at: datetime = Field(..., description="Token expiry time")
    refresh_expires_at: datetime = Field(..., description="Refresh token expiry time")

    # Device/client info
    device_info: Dict[str, Any] = Field(default_factory=dict, description="Device information")
    user_agent: Optional[str] = Field(default="", description="User agent string")
    ip_address: Optional[str] = Field(default="", description="IP address")

    # Status
    is_active: bool = Field(default=True, description="Whether session is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: datetime = Field(default_factory=datetime.utcnow)


# Authentication Request/Response Models

class SignupRequest(BaseModel):
    """Request model for user signup."""

    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    first_name: Optional[str] = Field(default="", description="First name")
    last_name: Optional[str] = Field(default="", description="Last name")
    organization_name: Optional[str] = Field(default="", description="Organization name")


class SigninRequest(BaseModel):
    """Request model for user signin."""

    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(default=False, description="Extended session duration")


class AuthResponse(BaseModel):
    """Response model for authentication."""

    success: bool = Field(..., description="Authentication success")
    user: Optional[Dict[str, Any]] = Field(default=None, description="User information")
    access_token: Optional[str] = Field(default=None, description="JWT access token")
    refresh_token: Optional[str] = Field(default=None, description="Refresh token")
    expires_at: Optional[datetime] = Field(default=None, description="Token expiry")
    organization: Optional[Dict[str, Any]] = Field(default=None, description="Primary organization")
    message: Optional[str] = Field(default="", description="Response message")


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str = Field(..., description="Refresh token")


class PasswordResetRequest(BaseModel):
    """Request model for password reset."""

    email: str = Field(..., description="User email")


class PasswordResetConfirmRequest(BaseModel):
    """Request model for password reset confirmation."""

    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")
