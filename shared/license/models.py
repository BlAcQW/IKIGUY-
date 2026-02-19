"""
License Models

This module contains additional license-related data models.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class LicenseFeatures(BaseModel):
    """License features configuration"""
    basic_features: List[str] = Field(default_factory=list, description="Basic license features")
    standard_features: List[str] = Field(default_factory=list, description="Standard license features")
    enterprise_features: List[str] = Field(default_factory=list, description="Enterprise license features")
    industry_features: List[str] = Field(default_factory=list, description="Industry license features")
    custom_features: Dict[str, List[str]] = Field(default_factory=dict, description="Custom features by tenant")


class LicenseLimits(BaseModel):
    """License limits configuration"""
    basic_limits: Dict[str, int] = Field(default_factory=dict, description="Basic license limits")
    standard_limits: Dict[str, int] = Field(default_factory=dict, description="Standard license limits")
    enterprise_limits: Dict[str, int] = Field(default_factory=dict, description="Enterprise license limits")
    industry_limits: Dict[str, int] = Field(default_factory=dict, description="Industry license limits")
    custom_limits: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="Custom limits by tenant")


class LicenseStatus(BaseModel):
    """License status information"""
    tenant_id: str = Field(..., description="Tenant identifier")
    license_key: str = Field(..., description="License key")
    status: str = Field(..., description="License status: active, expired, revoked, suspended")
    last_check: datetime = Field(default_factory=datetime.utcnow, description="Last license check")
    next_check: datetime = Field(..., description="Next license check")
    usage_summary: Dict[str, int] = Field(default_factory=dict, description="Current usage summary")
    limit_summary: Dict[str, int] = Field(default_factory=dict, description="Current limits")
    warnings: List[str] = Field(default_factory=list, description="License warnings")
    errors: List[str] = Field(default_factory=list, description="License errors")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LicenseSync(BaseModel):
    """License synchronization information"""
    tenant_id: str = Field(..., description="Tenant identifier")
    sync_id: str = Field(..., description="Sync identifier")
    sync_type: str = Field(..., description="Sync type: full, incremental, usage_only")
    status: str = Field(..., description="Sync status: pending, in_progress, completed, failed")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Sync start time")
    completed_at: Optional[datetime] = Field(None, description="Sync completion time")
    data_synced: Dict[str, Any] = Field(default_factory=dict, description="Synced data")
    errors: List[str] = Field(default_factory=list, description="Sync errors")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LicenseAudit(BaseModel):
    """License audit trail"""
    audit_id: str = Field(..., description="Audit identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    action: str = Field(..., description="Audit action")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Audit timestamp")
    user_id: Optional[str] = Field(None, description="User who performed action")
    details: Dict[str, Any] = Field(default_factory=dict, description="Audit details")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LicenseCompliance(BaseModel):
    """License compliance information"""
    tenant_id: str = Field(..., description="Tenant identifier")
    compliance_status: str = Field(..., description="Compliance status: compliant, non_compliant, warning")
    last_check: datetime = Field(default_factory=datetime.utcnow, description="Last compliance check")
    violations: List[Dict[str, Any]] = Field(default_factory=list, description="Compliance violations")
    recommendations: List[str] = Field(default_factory=list, description="Compliance recommendations")
    auto_remediation: bool = Field(False, description="Enable auto-remediation")
    grace_period_days: int = Field(7, description="Grace period in days")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
