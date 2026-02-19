"""
Configuration Models

This module contains additional configuration-related data models.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class FeatureFlags(BaseModel):
    """Feature flags configuration"""

    advanced_analytics: bool = Field(False, description="Enable advanced analytics")
    ai_summarization: bool = Field(False, description="Enable AI call summarization")
    multi_language: bool = Field(True, description="Enable multi-language support")
    real_time_transcription: bool = Field(
        True, description="Enable real-time transcription"
    )
    call_recording: bool = Field(True, description="Enable call recording")
    sentiment_analysis: bool = Field(False, description="Enable sentiment analysis")
    predictive_analytics: bool = Field(False, description="Enable predictive analytics")
    custom_workflows: bool = Field(False, description="Enable custom workflows")
    third_party_integrations: bool = Field(
        False, description="Enable third-party integrations"
    )
    white_labeling: bool = Field(False, description="Enable white labeling")
    custom_branding: bool = Field(True, description="Enable custom branding")
    api_access: bool = Field(False, description="Enable API access")
    webhook_support: bool = Field(True, description="Enable webhook support")
    mobile_app: bool = Field(False, description="Enable mobile app features")
    voice_biometrics: bool = Field(False, description="Enable voice biometrics")


class ModuleConfig(BaseModel):
    """Module configuration"""

    module_id: str = Field(..., description="Module identifier")
    name: str = Field(..., description="Module name")
    version: str = Field(..., description="Module version")
    enabled: bool = Field(True, description="Whether module is enabled")
    dependencies: List[str] = Field(
        default_factory=list, description="Module dependencies"
    )
    settings: Dict[str, Any] = Field(
        default_factory=dict, description="Module settings"
    )
    permissions: List[str] = Field(
        default_factory=list, description="Required permissions"
    )
    features: List[str] = Field(default_factory=list, description="Provided features")
    api_endpoints: List[str] = Field(default_factory=list, description="API endpoints")
    ui_components: List[str] = Field(default_factory=list, description="UI components")


class WorkflowConfig(BaseModel):
    """Workflow configuration"""

    workflow_id: str = Field(..., description="Workflow identifier")
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    enabled: bool = Field(True, description="Whether workflow is enabled")
    trigger_events: List[str] = Field(
        default_factory=list, description="Trigger events"
    )
    steps: List[Dict[str, Any]] = Field(
        default_factory=list, description="Workflow steps"
    )
    conditions: Dict[str, Any] = Field(
        default_factory=dict, description="Workflow conditions"
    )
    actions: Dict[str, Any] = Field(
        default_factory=dict, description="Workflow actions"
    )
    timeout_seconds: int = Field(300, description="Workflow timeout in seconds")
    retry_attempts: int = Field(3, description="Number of retry attempts")
    error_handling: Dict[str, Any] = Field(
        default_factory=dict, description="Error handling configuration"
    )


class SystemConfig(BaseModel):
    """System-wide configuration"""

    system_id: str = Field(..., description="System identifier")
    environment: str = Field(
        "production", description="Environment: development, staging, production"
    )
    debug_mode: bool = Field(False, description="Enable debug mode")
    log_level: str = Field("info", description="Log level: debug, info, warning, error")
    max_concurrent_calls: int = Field(1000, description="Maximum concurrent calls")
    max_call_duration: int = Field(3600, description="Maximum call duration in seconds")
    data_retention_days: int = Field(90, description="Data retention period in days")
    backup_enabled: bool = Field(True, description="Enable automated backups")
    backup_interval_hours: int = Field(24, description="Backup interval in hours")
    monitoring_enabled: bool = Field(True, description="Enable system monitoring")
    alerting_enabled: bool = Field(True, description="Enable alerting")
    maintenance_window: Dict[str, str] = Field(
        default_factory=dict, description="Maintenance window configuration"
    )
    security_settings: Dict[str, Any] = Field(
        default_factory=dict, description="Security settings"
    )
    performance_settings: Dict[str, Any] = Field(
        default_factory=dict, description="Performance settings"
    )
    language_detect_threshold: float = Field(
        0.5,
        description="Minimum confidence required to publish language detection events",
    )
