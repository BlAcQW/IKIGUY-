"""
Security Foundation Module

This module provides comprehensive security management including audit logging,
monitoring, access control (RBAC), compliance, and data encryption.
"""

from .interfaces import (
    SecurityAuditor, SecurityMonitor, AccessController, ComplianceMonitor, EncryptionManager, SecurityManager,
    SecurityAudit, SecurityEvent, AccessControl, ComplianceRule, ComplianceViolation
)

from .engine import SecurityEngine

__all__ = [
    # Abstract interfaces
    'SecurityAuditor', 'SecurityMonitor', 'AccessController', 'ComplianceMonitor', 'EncryptionManager', 'SecurityManager',
    
    # Data models
    'SecurityAudit', 'SecurityEvent', 'AccessControl', 'ComplianceRule', 'ComplianceViolation',
    
    # Engine implementation
    'SecurityEngine'
]
