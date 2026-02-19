"""
Security interfaces for KasaAI platform.

This module defines abstract interfaces for security components including
audit logging, encryption, access control, and compliance monitoring.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field


class SecurityAudit(BaseModel):
    """Security audit record"""
    audit_id: str = Field(..., description="Unique audit identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    action: str = Field(..., description="Action performed")
    resource: str = Field(..., description="Resource accessed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Audit timestamp")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    success: bool = Field(..., description="Whether action was successful")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")
    risk_level: str = Field(default="low", description="Risk level (low, medium, high, critical)")


class SecurityEvent(BaseModel):
    """Security event for monitoring"""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of security event")
    severity: str = Field(..., description="Event severity (info, warning, error, critical)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    source: str = Field(..., description="Event source")
    message: str = Field(..., description="Event message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Event metadata")
    resolved: bool = Field(default=False, description="Whether event is resolved")


class AccessControl(BaseModel):
    """Access control configuration"""
    resource: str = Field(..., description="Resource identifier")
    action: str = Field(..., description="Action to perform")
    roles: List[str] = Field(default_factory=list, description="Allowed roles")
    permissions: List[str] = Field(default_factory=list, description="Required permissions")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Access conditions")
    tenant_scope: bool = Field(default=True, description="Whether access is tenant-scoped")


class ComplianceRule(BaseModel):
    """Compliance rule definition"""
    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    category: str = Field(..., description="Compliance category (GDPR, SOC2, etc.)")
    severity: str = Field(..., description="Rule severity")
    enabled: bool = Field(default=True, description="Whether rule is enabled")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Rule conditions")
    actions: List[str] = Field(default_factory=list, description="Actions to take on violation")


class ComplianceViolation(BaseModel):
    """Compliance violation record"""
    violation_id: str = Field(..., description="Unique violation identifier")
    rule_id: str = Field(..., description="Rule that was violated")
    tenant_id: str = Field(..., description="Tenant identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Violation timestamp")
    severity: str = Field(..., description="Violation severity")
    description: str = Field(..., description="Violation description")
    details: Dict[str, Any] = Field(default_factory=dict, description="Violation details")
    resolved: bool = Field(default=False, description="Whether violation is resolved")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")


class SecurityAuditor(ABC):
    """Abstract interface for security audit logging"""
    
    @abstractmethod
    async def log_audit(self, audit: SecurityAudit) -> bool:
        """Log a security audit record"""
        pass
    
    @abstractmethod
    async def get_audit_logs(self, tenant_id: str, 
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           action: Optional[str] = None,
                           user_id: Optional[str] = None) -> List[SecurityAudit]:
        """Get audit logs with optional filtering"""
        pass
    
    @abstractmethod
    async def export_audit_logs(self, tenant_id: str, 
                              format: str = "json",
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> str:
        """Export audit logs in specified format"""
        pass


class SecurityMonitor(ABC):
    """Abstract interface for security monitoring"""
    
    @abstractmethod
    async def record_event(self, event: SecurityEvent) -> bool:
        """Record a security event"""
        pass
    
    @abstractmethod
    async def get_active_events(self, tenant_id: Optional[str] = None,
                              severity: Optional[str] = None) -> List[SecurityEvent]:
        """Get active security events"""
        pass
    
    @abstractmethod
    async def resolve_event(self, event_id: str, resolution_notes: str) -> bool:
        """Mark an event as resolved"""
        pass
    
    @abstractmethod
    async def get_security_metrics(self, tenant_id: str,
                                 period: str = "daily") -> Dict[str, Any]:
        """Get security metrics for a period"""
        pass


class AccessController(ABC):
    """Abstract interface for access control"""
    
    @abstractmethod
    async def check_access(self, tenant_id: str, user_id: str, 
                          resource: str, action: str) -> bool:
        """Check if user has access to resource"""
        pass
    
    @abstractmethod
    async def grant_access(self, tenant_id: str, user_id: str,
                          resource: str, action: str, 
                          roles: List[str] = None) -> bool:
        """Grant access to a resource"""
        pass
    
    @abstractmethod
    async def revoke_access(self, tenant_id: str, user_id: str,
                           resource: str, action: str) -> bool:
        """Revoke access to a resource"""
        pass
    
    @abstractmethod
    async def get_user_permissions(self, tenant_id: str, user_id: str) -> Dict[str, List[str]]:
        """Get all permissions for a user"""
        pass


class ComplianceMonitor(ABC):
    """Abstract interface for compliance monitoring"""
    
    @abstractmethod
    async def add_rule(self, rule: ComplianceRule) -> bool:
        """Add a compliance rule"""
        pass
    
    @abstractmethod
    async def check_compliance(self, tenant_id: str, 
                             category: Optional[str] = None) -> List[ComplianceViolation]:
        """Check compliance for a tenant"""
        pass
    
    @abstractmethod
    async def record_violation(self, violation: ComplianceViolation) -> bool:
        """Record a compliance violation"""
        pass
    
    @abstractmethod
    async def resolve_violation(self, violation_id: str, 
                              resolution_notes: str) -> bool:
        """Mark a violation as resolved"""
        pass
    
    @abstractmethod
    async def get_compliance_report(self, tenant_id: str,
                                  category: Optional[str] = None) -> Dict[str, Any]:
        """Get compliance report for a tenant"""
        pass


class EncryptionManager(ABC):
    """Abstract interface for encryption management"""
    
    @abstractmethod
    async def encrypt_data(self, data: str, key_id: Optional[str] = None) -> str:
        """Encrypt data"""
        pass
    
    @abstractmethod
    async def decrypt_data(self, encrypted_data: str, key_id: Optional[str] = None) -> str:
        """Decrypt data"""
        pass
    
    @abstractmethod
    async def generate_key(self, key_name: str, key_type: str = "AES") -> str:
        """Generate a new encryption key"""
        pass
    
    @abstractmethod
    async def rotate_key(self, key_id: str) -> bool:
        """Rotate an encryption key"""
        pass
    
    @abstractmethod
    async def get_key_info(self, key_id: str) -> Dict[str, Any]:
        """Get information about an encryption key"""
        pass


class SecurityManager(ABC):
    """Abstract interface for overall security management"""
    
    @abstractmethod
    async def initialize_security(self, tenant_id: str) -> bool:
        """Initialize security for a tenant"""
        pass
    
    @abstractmethod
    async def perform_security_audit(self, tenant_id: str) -> Dict[str, Any]:
        """Perform a comprehensive security audit"""
        pass
    
    @abstractmethod
    async def get_security_status(self, tenant_id: str) -> Dict[str, Any]:
        """Get overall security status for a tenant"""
        pass
    
    @abstractmethod
    async def update_security_settings(self, tenant_id: str, 
                                     settings: Dict[str, Any]) -> bool:
        """Update security settings for a tenant"""
        pass
