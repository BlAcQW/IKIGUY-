"""
Usage Tracking Interfaces

This module defines the core usage tracking interfaces used across all components.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class UsageRecord(BaseModel):
    """Usage record structure"""
    tenant_id: str = Field(..., description="Tenant identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Usage timestamp")
    service: str = Field(..., description="Service name")
    metric: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    cost: float = Field(0.0, description="Cost in USD")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    call_id: Optional[str] = Field(None, description="Associated call ID")
    user_id: Optional[str] = Field(None, description="Associated user ID")
    campaign_id: Optional[str] = Field(None, description="Associated campaign ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UsageTracker(ABC):
    """Usage tracking and aggregation"""
    
    def __init__(self, storage_backend: Any):
        self.storage = storage_backend
    
    @abstractmethod
    async def record_usage(self, record: UsageRecord) -> bool:
        """
        Record usage event
        
        Args:
            record: Usage record to store
            
        Returns:
            bool: True if recording was successful
        """
        pass
    
    @abstractmethod
    async def get_usage_summary(self, tenant_id: str, period: str) -> Dict[str, float]:
        """
        Get usage summary for period
        
        Args:
            tenant_id: Tenant identifier
            period: Time period (daily, weekly, monthly, yearly)
            
        Returns:
            Dict[str, float]: Usage summary by metric
        """
        pass
    
    @abstractmethod
    async def calculate_costs(self, tenant_id: str, period: str) -> Dict[str, float]:
        """
        Calculate costs for period
        
        Args:
            tenant_id: Tenant identifier
            period: Time period (daily, weekly, monthly, yearly)
            
        Returns:
            Dict[str, float]: Cost breakdown by service
        """
        pass
    
    @abstractmethod
    async def export_usage(self, tenant_id: str, format: str = "json") -> bytes:
        """
        Export usage data
        
        Args:
            tenant_id: Tenant identifier
            format: Export format (json, csv, xml)
            
        Returns:
            bytes: Exported usage data
        """
        pass
    
    @abstractmethod
    async def get_usage_by_service(self, tenant_id: str, service: str, period: str) -> List[UsageRecord]:
        """
        Get usage records by service
        
        Args:
            tenant_id: Tenant identifier
            service: Service name
            period: Time period
            
        Returns:
            List[UsageRecord]: Usage records
        """
        pass
    
    @abstractmethod
    async def get_usage_by_metric(self, tenant_id: str, metric: str, period: str) -> List[UsageRecord]:
        """
        Get usage records by metric
        
        Args:
            tenant_id: Tenant identifier
            metric: Metric name
            period: Time period
            
        Returns:
            List[UsageRecord]: Usage records
        """
        pass
    
    @abstractmethod
    async def get_total_usage(self, tenant_id: str, period: str) -> float:
        """
        Get total usage value for period
        
        Args:
            tenant_id: Tenant identifier
            period: Time period
            
        Returns:
            float: Total usage value
        """
        pass
    
    @abstractmethod
    async def get_total_cost(self, tenant_id: str, period: str) -> float:
        """
        Get total cost for period
        
        Args:
            tenant_id: Tenant identifier
            period: Time period
            
        Returns:
            float: Total cost in USD
        """
        pass
    
    @abstractmethod
    async def cleanup_old_records(self, days_to_keep: int) -> int:
        """
        Clean up old usage records
        
        Args:
            days_to_keep: Number of days to keep records
            
        Returns:
            int: Number of records deleted
        """
        pass
