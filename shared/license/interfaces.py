"""
License Management Interfaces

This module defines the core license management interfaces used across all components.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class LicenseInfo(BaseModel):
    """License information structure"""
    license_key: str = Field(..., description="License key")
    tenant_id: str = Field(..., description="Tenant identifier")
    license_type: str = Field(..., description="License type: basic, standard, enterprise, industry")
    features: List[str] = Field(default_factory=list, description="Enabled features")
    limits: Dict[str, int] = Field(default_factory=dict, description="Usage limits")
    issued_date: datetime = Field(..., description="License issue date")
    expiry_date: Optional[datetime] = Field(None, description="License expiry date")
    is_active: bool = Field(True, description="Whether license is active")
    max_users: int = Field(1, description="Maximum number of users")
    max_calls_per_month: int = Field(1000, description="Maximum calls per month")
    max_storage_gb: int = Field(10, description="Maximum storage in GB")
    support_level: str = Field("basic", description="Support level: basic, standard, premium")
    customizations: Dict[str, Any] = Field(default_factory=dict, description="Custom license settings")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LicenseValidator(ABC):
    """License validation and management"""
    
    def __init__(self, storage_backend: Any):
        self.storage = storage_backend
    
    @abstractmethod
    async def validate_license(self, license_key: str) -> LicenseInfo:
        """
        Validate license and return license info
        
        Args:
            license_key: License key to validate
            
        Returns:
            LicenseInfo: License information
        """
        pass
    
    @abstractmethod
    async def check_feature_access(self, tenant_id: str, feature: str) -> bool:
        """
        Check if tenant has access to feature
        
        Args:
            tenant_id: Tenant identifier
            feature: Feature name
            
        Returns:
            bool: True if feature is accessible
        """
        pass
    
    @abstractmethod
    async def record_usage(self, tenant_id: str, feature: str, usage: int) -> bool:
        """
        Record feature usage for license tracking
        
        Args:
            tenant_id: Tenant identifier
            feature: Feature name
            usage: Usage amount
            
        Returns:
            bool: True if usage was recorded successfully
        """
        pass
    
    @abstractmethod
    async def sync_license(self, tenant_id: str) -> bool:
        """
        Sync license with on-premise deployment
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            bool: True if sync was successful
        """
        pass
    
    @abstractmethod
    async def get_license_status(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get current license status
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Dict[str, Any]: License status information
        """
        pass
    
    @abstractmethod
    async def check_usage_limits(self, tenant_id: str, feature: str, requested_usage: int) -> bool:
        """
        Check if usage is within limits
        
        Args:
            tenant_id: Tenant identifier
            feature: Feature name
            requested_usage: Requested usage amount
            
        Returns:
            bool: True if usage is within limits
        """
        pass
    
    @abstractmethod
    async def get_remaining_quota(self, tenant_id: str, feature: str) -> int:
        """
        Get remaining quota for feature
        
        Args:
            tenant_id: Tenant identifier
            feature: Feature name
            
        Returns:
            int: Remaining quota
        """
        pass
    
    @abstractmethod
    async def revoke_license(self, tenant_id: str) -> bool:
        """
        Revoke license for tenant
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            bool: True if license was revoked successfully
        """
        pass
    
    @abstractmethod
    async def renew_license(self, tenant_id: str, new_expiry_date: datetime) -> bool:
        """
        Renew license for tenant
        
        Args:
            tenant_id: Tenant identifier
            new_expiry_date: New expiry date
            
        Returns:
            bool: True if license was renewed successfully
        """
        pass
