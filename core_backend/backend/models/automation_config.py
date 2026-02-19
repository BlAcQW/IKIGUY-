"""
Automation Configuration Models
Data models for saving and managing automation configurations
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class AutomationStatus(str, Enum):
    """Status of automation configuration"""
    DRAFT = "draft"
    DEPLOYED = "deployed"
    STOPPED = "stopped"

class SyncStatus(str, Enum):
    """VAPI sync status"""
    SYNCED = "synced"
    OUT_OF_SYNC = "out_of_sync"
    NEVER_SYNCED = "never_synced"
    ERROR = "error"

class CompanyInfo(BaseModel):
    """Company information extracted from website"""
    name: str
    description: str
    url: str
    extracted_info: Optional[Dict[str, Any]] = None

class VoiceSettings(BaseModel):
    """Voice configuration settings"""
    voice_id: str
    model: str
    max_duration: int = 600
    provider: Optional[str] = None
    speed: Optional[float] = None
    temperature: Optional[float] = None

class TranscriberSettings(BaseModel):
    """Speech-to-Text transcriber settings (Deepgram, etc.)"""
    provider: Optional[str] = None
    model: Optional[str] = None
    language: Optional[str] = None
    keywords: Optional[List[str]] = Field(default_factory=list, description="STT keywords for improved recognition")
    keyterms: Optional[List[str]] = Field(default_factory=list, description="STT keyterms/phrases")
    endpointing: Optional[int] = None
    smart_format: Optional[bool] = None

class ModelSettings(BaseModel):
    """LLM model settings"""
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None

class VAPIAgent(BaseModel):
    """
    Comprehensive VAPI agent configuration.

    This model captures ALL VAPI assistant settings to ensure
    full configuration sync between VAPI and platform.
    """
    # Core identification
    assistant_id: str = ""
    assistant_name: Optional[str] = None
    phone_number_id: str = ""

    # System configuration
    system_prompt: str
    voice_settings: VoiceSettings
    tools: List[Any] = Field(default_factory=list, description="Tool IDs or tool objects")

    # Enhanced VAPI settings (previously missing)
    transcriber: Optional[TranscriberSettings] = Field(None, description="STT transcriber config (Deepgram keywords, etc.)")
    model_settings: Optional[ModelSettings] = Field(None, description="LLM model configuration")

    # Messages and prompts
    first_message: Optional[str] = Field(None, description="Opening message when call starts")
    voicemail_message: Optional[str] = Field(None, description="Message left on voicemail")
    end_call_message: Optional[str] = Field(None, description="Message before ending call")

    # Advanced settings
    server_messages: Optional[List[str]] = Field(default_factory=list, description="Webhook event types")
    analysis_plan: Optional[Dict[str, Any]] = Field(None, description="Structured data extraction plan")
    artifact_plan: Optional[Dict[str, Any]] = Field(None, description="Artifact generation plan")
    message_plan: Optional[Dict[str, Any]] = Field(None, description="Message routing plan")
    start_speaking_plan: Optional[Dict[str, Any]] = Field(None, description="Start speaking configuration")

    # Call behavior
    silence_timeout_seconds: Optional[int] = Field(None, description="Silence timeout")
    max_duration_seconds: Optional[int] = Field(None, description="Maximum call duration")
    background_denoising_enabled: Optional[bool] = Field(None, description="Background noise removal")
    voicemail_detection: Optional[Dict[str, Any]] = Field(None, description="Voicemail detection config")

    # Features
    dial_keypad_function_enabled: Optional[bool] = Field(None, description="Enable DTMF keypad")
    end_call_function_enabled: Optional[bool] = Field(None, description="Enable end call function")
    recording_enabled: Optional[bool] = Field(None, description="Record calls")

    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom metadata")
    
    # Custom Settings Override
    custom_settings_override: Optional[Dict[str, Any]] = Field(
        None, 
        description="Custom TTS/ASR/LLM settings to override VAPI defaults. When set, these will be used instead of VAPI assistant settings."
    )

class N8NEndpoints(BaseModel):
    """N8N workflow endpoints"""
    calendar: str = "/calendar/availability"
    tickets: str = "/tickets/create"
    availability: str = "/availability/check"
    escalation: str = "/escalation/route"
    analytics: str = "/analytics/track"

class N8NWorkflow(BaseModel):
    """N8N workflow configuration"""
    workflow_id: str = ""
    workflow_name: str
    webhook_url: str = ""
    endpoints: N8NEndpoints = Field(default_factory=N8NEndpoints)

class Integration(BaseModel):
    """Generic integration configuration"""
    enabled: bool = False
    apiKey: str = ""

class ProjectIntegration(BaseModel):
    """Integration with project ID"""
    enabled: bool = False
    projectId: str = ""

class Integrations(BaseModel):
    """All available integrations"""
    calendly: Integration = Field(default_factory=Integration)
    supabase: ProjectIntegration = Field(default_factory=ProjectIntegration)
    tavily: Integration = Field(default_factory=Integration)
    resend: Integration = Field(default_factory=Integration)
    vonage: Integration = Field(default_factory=Integration)

class DemoSettings(BaseModel):
    """Demo deployment settings"""
    enable_demo: bool = True
    demo_url: str = ""
    html_template: str = ""

class Analytics(BaseModel):
    """Analytics and monitoring settings"""
    enable_tracking: bool = True
    webhook_url: str = ""
    report_email: str = ""

class CustomTool(BaseModel):
    """Custom business tool configuration"""
    name: str
    description: str
    endpoint: str
    method: str = "POST"
    category: str
    enabled: bool = True

class CustomTools(BaseModel):
    """Custom tools configuration"""
    enabled: bool = False
    selected_tools: List[str] = []
    available_tools: List[CustomTool] = []

class AutomationConfig(BaseModel):
    """Complete automation configuration"""
    id: Optional[str] = None
    automation_name: str
    company_info: CompanyInfo
    vapi_agent: VAPIAgent
    n8n_workflow: N8NWorkflow
    integrations: Integrations = Field(default_factory=Integrations)
    custom_tools: CustomTools = Field(default_factory=CustomTools)
    demo_settings: DemoSettings = Field(default_factory=DemoSettings)
    analytics: Analytics = Field(default_factory=Analytics)
    knowledge_base_collections: List[str] = Field(default_factory=list, description="Linked knowledge base collection names")
    status: AutomationStatus = AutomationStatus.DRAFT
    template_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_id: Optional[str] = None  # For user association
    organization_id: Optional[str] = None  # For organization association

    # VAPI Sync metadata
    vapi_sync_status: Optional[SyncStatus] = Field(None, description="VAPI synchronization status")
    vapi_last_synced_at: Optional[datetime] = Field(None, description="Last successful sync with VAPI")
    vapi_config_hash: Optional[str] = Field(None, description="Hash of VAPI config for change detection")
    full_vapi_config: Optional[Dict[str, Any]] = Field(None, description="Complete VAPI assistant JSON response")

class AutomationConfigCreate(BaseModel):
    """Request model for creating automation configuration"""
    automation_name: str
    company_info: Optional[CompanyInfo] = None
    vapi_agent: Optional[VAPIAgent] = None
    n8n_workflow: Optional[N8NWorkflow] = None
    integrations: Optional[Integrations] = None
    custom_tools: Optional[CustomTools] = None
    demo_settings: Optional[DemoSettings] = None
    analytics: Optional[Analytics] = None
    template_id: Optional[str] = None

class AutomationConfigUpdate(BaseModel):
    """Request model for updating automation configuration"""
    automation_name: Optional[str] = None
    company_info: Optional[CompanyInfo] = None
    vapi_agent: Optional[VAPIAgent] = None
    n8n_workflow: Optional[N8NWorkflow] = None
    integrations: Optional[Integrations] = None
    custom_tools: Optional[CustomTools] = None
    demo_settings: Optional[DemoSettings] = None
    analytics: Optional[Analytics] = None
    knowledge_base_collections: Optional[List[str]] = None
    status: Optional[AutomationStatus] = None

class AutomationConfigResponse(BaseModel):
    """Response model for automation configuration"""
    id: str
    automation_name: str
    company_info: CompanyInfo
    vapi_agent: VAPIAgent
    n8n_workflow: N8NWorkflow
    integrations: Integrations
    custom_tools: CustomTools
    demo_settings: DemoSettings
    analytics: Analytics
    knowledge_base_collections: List[str] = Field(default_factory=list)
    config: Optional[Dict[str, Any]] = None
    status: AutomationStatus
    template_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str] = None
    organization_id: Optional[str] = None

    # VAPI Sync metadata
    vapi_sync_status: Optional[SyncStatus] = None
    vapi_last_synced_at: Optional[datetime] = None
    vapi_config_hash: Optional[str] = None
    full_vapi_config: Optional[Dict[str, Any]] = None

class AutomationConfigList(BaseModel):
    """Response model for listing automation configurations"""
    configs: List[AutomationConfigResponse]
    total: int

class DeploymentResult(BaseModel):
    """Result of deployment operation"""
    success: bool
    demo_url: Optional[str] = None
    error: Optional[str] = None
    workflowId: Optional[str] = None
    assistantId: Optional[str] = None

class AutomationStatusResponse(BaseModel):
    """Automation status and metrics"""
    status: AutomationStatus
    lastActivity: Optional[datetime] = None
    callCount: Optional[int] = 0
    successRate: Optional[float] = 0.0
    errors: List[str] = []
    uptime: Optional[str] = None

class DuplicateRequest(BaseModel):
    """Request to duplicate an automation configuration"""
    newName: str