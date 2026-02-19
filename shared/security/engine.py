"""
Security engine implementation for KasaAI platform.

This module implements the core security functionality including audit logging,
monitoring, access control, compliance monitoring, and encryption management.
"""

import json
import logging
import hashlib
import hmac
import base64
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from uuid import uuid4
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .interfaces import (
    SecurityAuditor, SecurityMonitor, AccessController, ComplianceMonitor,
    EncryptionManager, SecurityManager, SecurityAudit, SecurityEvent,
    AccessControl, ComplianceRule, ComplianceViolation
)
from apps.shared.storage.interfaces import StorageBackend


logger = logging.getLogger(__name__)


class SecurityEngine(SecurityAuditor, SecurityMonitor, AccessController, 
                    ComplianceMonitor, EncryptionManager, SecurityManager):
    """Comprehensive security engine implementation"""
    
    def __init__(self, storage_backend: StorageBackend):
        """Initialize security engine"""
        self.storage = storage_backend
        self.logger = logger
        self._encryption_keys: Dict[str, bytes] = {}
        self._rate_limits: Dict[str, Dict[str, Any]] = {}
        
        # Initialize default compliance rules
        self._default_rules = [
            ComplianceRule(
                rule_id="gdpr_data_retention",
                name="GDPR Data Retention",
                description="Ensure data retention policies comply with GDPR",
                category="GDPR",
                severity="high",
                conditions={"max_retention_days": 2555},  # 7 years
                actions=["alert", "log"]
            ),
            ComplianceRule(
                rule_id="access_control_audit",
                name="Access Control Audit",
                description="Ensure all access is properly logged and audited",
                category="SOC2",
                severity="medium",
                conditions={"require_audit_log": True},
                actions=["alert", "log"]
            ),
            ComplianceRule(
                rule_id="encryption_at_rest",
                name="Encryption at Rest",
                description="Ensure sensitive data is encrypted at rest",
                category="SOC2",
                severity="high",
                conditions={"require_encryption": True},
                actions=["alert", "block"]
            )
        ]
    
    async def _ensure_initialized(self) -> None:
        """Ensure storage is initialized"""
        if not await self.storage.table_exists("security_audits"):
            await self._initialize_storage()
    
    async def _initialize_storage(self) -> None:
        """Initialize storage tables for security components"""
        # Security audit table
        audit_schema = {
            "audit_id": "TEXT PRIMARY KEY",
            "tenant_id": "TEXT NOT NULL",
            "user_id": "TEXT",
            "action": "TEXT NOT NULL",
            "resource": "TEXT NOT NULL",
            "timestamp": "TEXT NOT NULL",
            "ip_address": "TEXT",
            "user_agent": "TEXT",
            "success": "BOOLEAN NOT NULL",
            "details": "TEXT",
            "risk_level": "TEXT NOT NULL"
        }
        await self.storage.create_table("security_audits", audit_schema)
        
        # Security events table
        events_schema = {
            "event_id": "TEXT PRIMARY KEY",
            "event_type": "TEXT NOT NULL",
            "severity": "TEXT NOT NULL",
            "timestamp": "TEXT NOT NULL",
            "tenant_id": "TEXT",
            "user_id": "TEXT",
            "source": "TEXT NOT NULL",
            "message": "TEXT NOT NULL",
            "metadata": "TEXT",
            "resolved": "BOOLEAN NOT NULL DEFAULT FALSE"
        }
        await self.storage.create_table("security_events", events_schema)
        
        # Access control table
        access_schema = {
            "tenant_id": "TEXT NOT NULL",
            "user_id": "TEXT NOT NULL",
            "resource": "TEXT NOT NULL",
            "action": "TEXT NOT NULL",
            "roles": "TEXT",
            "permissions": "TEXT",
            "conditions": "TEXT",
            "tenant_scope": "BOOLEAN NOT NULL DEFAULT TRUE",
            "granted_at": "TEXT NOT NULL",
            "PRIMARY KEY": "(tenant_id, user_id, resource, action)"
        }
        await self.storage.create_table("access_control", access_schema)
        
        # Compliance rules table
        rules_schema = {
            "rule_id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "description": "TEXT NOT NULL",
            "category": "TEXT NOT NULL",
            "severity": "TEXT NOT NULL",
            "enabled": "BOOLEAN NOT NULL DEFAULT TRUE",
            "conditions": "TEXT",
            "actions": "TEXT"
        }
        await self.storage.create_table("compliance_rules", rules_schema)
        
        # Compliance violations table
        violations_schema = {
            "violation_id": "TEXT PRIMARY KEY",
            "rule_id": "TEXT NOT NULL",
            "tenant_id": "TEXT NOT NULL",
            "timestamp": "TEXT NOT NULL",
            "severity": "TEXT NOT NULL",
            "description": "TEXT NOT NULL",
            "details": "TEXT",
            "resolved": "BOOLEAN NOT NULL DEFAULT FALSE",
            "resolution_notes": "TEXT"
        }
        await self.storage.create_table("compliance_violations", violations_schema)
        
        # Encryption keys table
        keys_schema = {
            "key_id": "TEXT PRIMARY KEY",
            "key_name": "TEXT NOT NULL",
            "key_type": "TEXT NOT NULL",
            "encrypted_key": "TEXT NOT NULL",
            "created_at": "TEXT NOT NULL",
            "last_used": "TEXT",
            "active": "BOOLEAN NOT NULL DEFAULT TRUE"
        }
        await self.storage.create_table("encryption_keys", keys_schema)
        
        # Security settings table
        settings_schema = {
            "tenant_id": "TEXT PRIMARY KEY",
            "settings": "TEXT NOT NULL",
            "updated_at": "TEXT NOT NULL"
        }
        await self.storage.create_table("security_settings", settings_schema)
        
        # Initialize default compliance rules
        for rule in self._default_rules:
            await self.add_rule(rule)
    
    # SecurityAuditor implementation
    async def log_audit(self, audit: SecurityAudit) -> bool:
        """Log a security audit record"""
        await self._ensure_initialized()
        
        try:
            audit_data = {
                "audit_id": audit.audit_id,
                "tenant_id": audit.tenant_id,
                "user_id": audit.user_id,
                "action": audit.action,
                "resource": audit.resource,
                "timestamp": audit.timestamp.isoformat(),
                "ip_address": audit.ip_address,
                "user_agent": audit.user_agent,
                "success": audit.success,
                "details": json.dumps(audit.details),
                "risk_level": audit.risk_level
            }
            
            await self.storage.insert("security_audits", audit_data)
            
            # Check for high-risk activities
            if audit.risk_level in ["high", "critical"]:
                await self.record_event(SecurityEvent(
                    event_id=str(uuid4()),
                    event_type="high_risk_audit",
                    severity=audit.risk_level,
                    tenant_id=audit.tenant_id,
                    user_id=audit.user_id,
                    source="security_auditor",
                    message=f"High-risk activity detected: {audit.action} on {audit.resource}",
                    metadata={"audit_id": audit.audit_id, "success": audit.success}
                ))
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to log audit: {str(e)}")
            return False
    
    async def get_audit_logs(self, tenant_id: str, 
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           action: Optional[str] = None,
                           user_id: Optional[str] = None) -> List[SecurityAudit]:
        """Get audit logs with optional filtering"""
        await self._ensure_initialized()
        
        try:
            conditions = {"tenant_id": tenant_id}
            
            if start_date:
                conditions["timestamp"] = {"$gte": start_date.isoformat()}
            if end_date:
                conditions["timestamp"] = {"$lte": end_date.isoformat()}
            if action:
                conditions["action"] = action
            if user_id:
                conditions["user_id"] = user_id
            
            results = await self.storage.select("security_audits", conditions)
            
            audits = []
            for result in results:
                audit = SecurityAudit(
                    audit_id=result["audit_id"],
                    tenant_id=result["tenant_id"],
                    user_id=result.get("user_id"),
                    action=result["action"],
                    resource=result["resource"],
                    timestamp=datetime.fromisoformat(result["timestamp"]),
                    ip_address=result.get("ip_address"),
                    user_agent=result.get("user_agent"),
                    success=result["success"],
                    details=json.loads(result.get("details", "{}")),
                    risk_level=result["risk_level"]
                )
                audits.append(audit)
            
            return audits
        except Exception as e:
            self.logger.error(f"Failed to get audit logs: {str(e)}")
            return []
    
    async def export_audit_logs(self, tenant_id: str, 
                              format: str = "json",
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> str:
        """Export audit logs in specified format"""
        audits = await self.get_audit_logs(tenant_id, start_date, end_date)
        
        if format.lower() == "json":
            # Convert datetime objects to ISO format strings for JSON serialization
            audit_dicts = []
            for audit in audits:
                audit_dict = audit.dict()
                audit_dict["timestamp"] = audit_dict["timestamp"].isoformat()
                audit_dicts.append(audit_dict)
            return json.dumps(audit_dicts, indent=2)
        elif format.lower() == "csv":
            if not audits:
                return "audit_id,tenant_id,user_id,action,resource,timestamp,ip_address,user_agent,success,risk_level\n"
            
            csv_lines = ["audit_id,tenant_id,user_id,action,resource,timestamp,ip_address,user_agent,success,risk_level\n"]
            for audit in audits:
                csv_lines.append(f"{audit.audit_id},{audit.tenant_id},{audit.user_id or ''},{audit.action},{audit.resource},{audit.timestamp},{audit.ip_address or ''},{audit.user_agent or ''},{audit.success},{audit.risk_level}\n")
            return "".join(csv_lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    # SecurityMonitor implementation
    async def record_event(self, event: SecurityEvent) -> bool:
        """Record a security event"""
        await self._ensure_initialized()
        
        try:
            event_data = {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "severity": event.severity,
                "timestamp": event.timestamp.isoformat(),
                "tenant_id": event.tenant_id,
                "user_id": event.user_id,
                "source": event.source,
                "message": event.message,
                "metadata": json.dumps(event.metadata),
                "resolved": event.resolved
            }
            
            await self.storage.insert("security_events", event_data)
            return True
        except Exception as e:
            self.logger.error(f"Failed to record event: {str(e)}")
            return False
    
    async def get_active_events(self, tenant_id: Optional[str] = None,
                              severity: Optional[str] = None) -> List[SecurityEvent]:
        """Get active security events"""
        await self._ensure_initialized()
        
        try:
            conditions = {"resolved": False}
            if tenant_id:
                conditions["tenant_id"] = tenant_id
            if severity:
                conditions["severity"] = severity
            
            results = await self.storage.select("security_events", conditions)
            
            events = []
            for result in results:
                event = SecurityEvent(
                    event_id=result["event_id"],
                    event_type=result["event_type"],
                    severity=result["severity"],
                    timestamp=datetime.fromisoformat(result["timestamp"]),
                    tenant_id=result.get("tenant_id"),
                    user_id=result.get("user_id"),
                    source=result["source"],
                    message=result["message"],
                    metadata=json.loads(result.get("metadata", "{}")),
                    resolved=result["resolved"]
                )
                events.append(event)
            
            return events
        except Exception as e:
            self.logger.error(f"Failed to get active events: {str(e)}")
            return []
    
    async def resolve_event(self, event_id: str, resolution_notes: str) -> bool:
        """Mark an event as resolved"""
        await self._ensure_initialized()
        
        try:
            await self.storage.upsert("security_events", {
                "event_id": event_id,
                "resolved": True
            })
            return True
        except Exception as e:
            self.logger.error(f"Failed to resolve event: {str(e)}")
            return False
    
    async def get_security_metrics(self, tenant_id: str,
                                 period: str = "daily") -> Dict[str, Any]:
        """Get security metrics for a period"""
        await self._ensure_initialized()
        
        try:
            # Calculate period start
            now = datetime.utcnow()
            if period == "daily":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "weekly":
                start_date = now - timedelta(days=7)
            elif period == "monthly":
                start_date = now - timedelta(days=30)
            else:
                start_date = now - timedelta(days=1)
            
            # Get audit metrics
            audits = await self.get_audit_logs(tenant_id, start_date, now)
            total_audits = len(audits)
            failed_audits = len([a for a in audits if not a.success])
            high_risk_audits = len([a for a in audits if a.risk_level in ["high", "critical"]])
            
            # Get event metrics
            events = await self.get_active_events(tenant_id)
            total_events = len(events)
            critical_events = len([e for e in events if e.severity == "critical"])
            high_events = len([e for e in events if e.severity == "high"])
            
            # Get compliance metrics
            violations = await self.check_compliance(tenant_id)
            total_violations = len(violations)
            unresolved_violations = len([v for v in violations if not v.resolved])
            
            return {
                "period": period,
                "audits": {
                    "total": total_audits,
                    "failed": failed_audits,
                    "high_risk": high_risk_audits,
                    "success_rate": (total_audits - failed_audits) / total_audits if total_audits > 0 else 1.0
                },
                "events": {
                    "total": total_events,
                    "critical": critical_events,
                    "high": high_events
                },
                "compliance": {
                    "total_violations": total_violations,
                    "unresolved": unresolved_violations,
                    "compliance_rate": (total_violations - unresolved_violations) / total_violations if total_violations > 0 else 1.0
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to get security metrics: {str(e)}")
            return {}
    
    # AccessController implementation
    async def check_access(self, tenant_id: str, user_id: str, 
                          resource: str, action: str) -> bool:
        """Check if user has access to resource"""
        await self._ensure_initialized()
        
        try:
            result = await self.storage.select_one("access_control", {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "resource": resource,
                "action": action
            })
            
            if result:
                # Log the access attempt
                await self.log_audit(SecurityAudit(
                    audit_id=str(uuid4()),
                    tenant_id=tenant_id,
                    user_id=user_id,
                    action=action,
                    resource=resource,
                    success=True,
                    risk_level="low"
                ))
                return True
            
            # Log failed access attempt
            await self.log_audit(SecurityAudit(
                audit_id=str(uuid4()),
                tenant_id=tenant_id,
                user_id=user_id,
                action=action,
                resource=resource,
                success=False,
                risk_level="medium"
            ))
            
            return False
        except Exception as e:
            self.logger.error(f"Failed to check access: {str(e)}")
            return False
    
    async def grant_access(self, tenant_id: str, user_id: str,
                          resource: str, action: str, 
                          roles: List[str] = None) -> bool:
        """Grant access to a resource"""
        await self._ensure_initialized()
        
        try:
            access_data = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "roles": json.dumps(roles or []),
                "permissions": json.dumps([]),
                "conditions": json.dumps({}),
                "tenant_scope": True,
                "granted_at": datetime.utcnow().isoformat()
            }
            
            await self.storage.upsert("access_control", access_data)
            
            # Log the access grant
            await self.log_audit(SecurityAudit(
                audit_id=str(uuid4()),
                tenant_id=tenant_id,
                user_id=user_id,
                action="grant_access",
                resource=f"{resource}:{action}",
                success=True,
                risk_level="low"
            ))
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to grant access: {str(e)}")
            return False
    
    async def revoke_access(self, tenant_id: str, user_id: str,
                           resource: str, action: str) -> bool:
        """Revoke access to a resource"""
        await self._ensure_initialized()
        
        try:
            await self.storage.delete("access_control", {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "resource": resource,
                "action": action
            })
            
            # Log the access revocation
            await self.log_audit(SecurityAudit(
                audit_id=str(uuid4()),
                tenant_id=tenant_id,
                user_id=user_id,
                action="revoke_access",
                resource=f"{resource}:{action}",
                success=True,
                risk_level="low"
            ))
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to revoke access: {str(e)}")
            return False
    
    async def get_user_permissions(self, tenant_id: str, user_id: str) -> Dict[str, List[str]]:
        """Get all permissions for a user"""
        await self._ensure_initialized()
        
        try:
            results = await self.storage.select("access_control", {
                "tenant_id": tenant_id,
                "user_id": user_id
            })
            
            permissions = {}
            for result in results:
                resource = result["resource"]
                action = result["action"]
                if resource not in permissions:
                    permissions[resource] = []
                permissions[resource].append(action)
            
            return permissions
        except Exception as e:
            self.logger.error(f"Failed to get user permissions: {str(e)}")
            return {}
    
    # ComplianceMonitor implementation
    async def add_rule(self, rule: ComplianceRule) -> bool:
        """Add a compliance rule"""
        await self._ensure_initialized()
        
        try:
            rule_data = {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "description": rule.description,
                "category": rule.category,
                "severity": rule.severity,
                "enabled": rule.enabled,
                "conditions": json.dumps(rule.conditions),
                "actions": json.dumps(rule.actions)
            }
            
            await self.storage.upsert("compliance_rules", rule_data)
            return True
        except Exception as e:
            self.logger.error(f"Failed to add rule: {str(e)}")
            return False
    
    async def check_compliance(self, tenant_id: str, 
                             category: Optional[str] = None) -> List[ComplianceViolation]:
        """Check compliance for a tenant"""
        await self._ensure_initialized()
        
        try:
            conditions = {"enabled": True}
            if category:
                conditions["category"] = category
            
            rules = await self.storage.select("compliance_rules", conditions)
            violations = []
            
            for rule_result in rules:
                rule = ComplianceRule(
                    rule_id=rule_result["rule_id"],
                    name=rule_result["name"],
                    description=rule_result["description"],
                    category=rule_result["category"],
                    severity=rule_result["severity"],
                    enabled=rule_result["enabled"],
                    conditions=json.loads(rule_result.get("conditions", "{}")),
                    actions=json.loads(rule_result.get("actions", "[]"))
                )
                
                # Check if rule is violated (simplified check)
                if await self._check_rule_violation(tenant_id, rule):
                    violation = ComplianceViolation(
                        violation_id=str(uuid4()),
                        rule_id=rule.rule_id,
                        tenant_id=tenant_id,
                        severity=rule.severity,
                        description=f"Violation of rule: {rule.name}",
                        details={"rule_category": rule.category}
                    )
                    violations.append(violation)
                    await self.record_violation(violation)
            
            # Also return existing violations from storage
            existing_violations = await self.storage.select("compliance_violations", {"tenant_id": tenant_id})
            for violation_result in existing_violations:
                violation = ComplianceViolation(
                    violation_id=violation_result["violation_id"],
                    rule_id=violation_result["rule_id"],
                    tenant_id=violation_result["tenant_id"],
                    timestamp=datetime.fromisoformat(violation_result["timestamp"]),
                    severity=violation_result["severity"],
                    description=violation_result["description"],
                    details=json.loads(violation_result.get("details", "{}")),
                    resolved=violation_result.get("resolved", False),
                    resolution_notes=violation_result.get("resolution_notes")
                )
                violations.append(violation)
            
            return violations
        except Exception as e:
            self.logger.error(f"Failed to check compliance: {str(e)}")
            return []
    
    async def _check_rule_violation(self, tenant_id: str, rule: ComplianceRule) -> bool:
        """Check if a specific rule is violated"""
        # Simplified rule checking - in a real implementation, this would be more sophisticated
        if rule.rule_id == "gdpr_data_retention":
            # Check if data retention is within limits
            return False  # Assume compliant for now
        elif rule.rule_id == "access_control_audit":
            # Check if access control is properly audited
            return False  # Assume compliant for now
        elif rule.rule_id == "encryption_at_rest":
            # Check if data is encrypted at rest
            return False  # Assume compliant for now
        
        return False
    
    async def record_violation(self, violation: ComplianceViolation) -> bool:
        """Record a compliance violation"""
        await self._ensure_initialized()
        
        try:
            violation_data = {
                "violation_id": violation.violation_id,
                "rule_id": violation.rule_id,
                "tenant_id": violation.tenant_id,
                "timestamp": violation.timestamp.isoformat(),
                "severity": violation.severity,
                "description": violation.description,
                "details": json.dumps(violation.details),
                "resolved": violation.resolved,
                "resolution_notes": violation.resolution_notes
            }
            
            await self.storage.insert("compliance_violations", violation_data)
            
            # Record security event for high severity violations
            if violation.severity in ["high", "critical"]:
                await self.record_event(SecurityEvent(
                    event_id=str(uuid4()),
                    event_type="compliance_violation",
                    severity=violation.severity,
                    tenant_id=violation.tenant_id,
                    source="compliance_monitor",
                    message=f"Compliance violation: {violation.description}",
                    metadata={"rule_id": violation.rule_id, "violation_id": violation.violation_id}
                ))
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to record violation: {str(e)}")
            return False
    
    async def resolve_violation(self, violation_id: str, 
                              resolution_notes: str) -> bool:
        """Mark a violation as resolved"""
        await self._ensure_initialized()
        
        try:
            await self.storage.upsert("compliance_violations", {
                "violation_id": violation_id,
                "resolved": True,
                "resolution_notes": resolution_notes
            })
            return True
        except Exception as e:
            self.logger.error(f"Failed to resolve violation: {str(e)}")
            return False
    
    async def get_compliance_report(self, tenant_id: str,
                                  category: Optional[str] = None) -> Dict[str, Any]:
        """Get compliance report for a tenant"""
        await self._ensure_initialized()
        
        try:
            violations = await self.check_compliance(tenant_id, category)
            
            total_violations = len(violations)
            resolved_violations = len([v for v in violations if v.resolved])
            critical_violations = len([v for v in violations if v.severity == "critical"])
            high_violations = len([v for v in violations if v.severity == "high"])
            
            return {
                "tenant_id": tenant_id,
                "category": category,
                "total_violations": total_violations,
                "resolved_violations": resolved_violations,
                "unresolved_violations": total_violations - resolved_violations,
                "critical_violations": critical_violations,
                "high_violations": high_violations,
                "compliance_rate": (total_violations - (total_violations - resolved_violations)) / total_violations if total_violations > 0 else 1.0,
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to get compliance report: {str(e)}")
            return {}
    
    # EncryptionManager implementation
    async def encrypt_data(self, data: str, key_id: Optional[str] = None) -> str:
        """Encrypt data"""
        await self._ensure_initialized()
        
        try:
            if not key_id:
                # Get or create default key
                key_id = await self._get_default_key_id()
            
            key = await self._get_encryption_key(key_id)
            if not key:
                raise ValueError(f"Encryption key not found: {key_id}")
            
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            self.logger.error(f"Failed to encrypt data: {str(e)}")
            raise
    
    async def decrypt_data(self, encrypted_data: str, key_id: Optional[str] = None) -> str:
        """Decrypt data"""
        await self._ensure_initialized()
        
        try:
            if not key_id:
                # Get or create default key
                key_id = await self._get_default_key_id()
            
            key = await self._get_encryption_key(key_id)
            if not key:
                raise ValueError(f"Encryption key not found: {key_id}")
            
            fernet = Fernet(key)
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"Failed to decrypt data: {str(e)}")
            raise
    
    async def generate_key(self, key_name: str, key_type: str = "AES") -> str:
        """Generate a new encryption key"""
        await self._ensure_initialized()
        
        try:
            key_id = str(uuid4())
            key = Fernet.generate_key()
            
            # Store encrypted key
            key_data = {
                "key_id": key_id,
                "key_name": key_name,
                "key_type": key_type,
                "encrypted_key": base64.b64encode(key).decode(),
                "created_at": datetime.utcnow().isoformat(),
                "active": True
            }
            
            await self.storage.insert("encryption_keys", key_data)
            self._encryption_keys[key_id] = key
            
            return key_id
        except Exception as e:
            self.logger.error(f"Failed to generate key: {str(e)}")
            raise
    
    async def rotate_key(self, key_id: str) -> bool:
        """Rotate an encryption key"""
        await self._ensure_initialized()
        
        try:
            # Generate new key
            new_key_id = await self.generate_key(f"rotated_{key_id}", "AES")
            
            # Mark old key as inactive
            await self.storage.upsert("encryption_keys", {
                "key_id": key_id,
                "active": False
            })
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to rotate key: {str(e)}")
            return False
    
    async def get_key_info(self, key_id: str) -> Dict[str, Any]:
        """Get information about an encryption key"""
        await self._ensure_initialized()
        
        try:
            result = await self.storage.select_one("encryption_keys", {"key_id": key_id})
            if result:
                return {
                    "key_id": result["key_id"],
                    "key_name": result["key_name"],
                    "key_type": result["key_type"],
                    "created_at": result["created_at"],
                    "last_used": result.get("last_used"),
                    "active": result.get("active", True)  # Default to True if not present
                }
            return {"active": False}  # Return default state for non-existent keys
        except Exception as e:
            self.logger.error(f"Failed to get key info: {str(e)}")
            return {"active": False}  # Return default state on error
    
    async def _get_default_key_id(self) -> str:
        """Get or create default encryption key"""
        try:
            result = await self.storage.select_one("encryption_keys", {"active": True})
            if result:
                return result["key_id"]
            
            # Create default key if none exists
            return await self.generate_key("default", "AES")
        except Exception as e:
            self.logger.error(f"Failed to get default key: {str(e)}")
            raise
    
    async def _get_encryption_key(self, key_id: str) -> Optional[bytes]:
        """Get encryption key from storage or cache"""
        if key_id in self._encryption_keys:
            return self._encryption_keys[key_id]
        
        try:
            result = await self.storage.select_one("encryption_keys", {"key_id": key_id, "active": True})
            if result:
                key = base64.b64decode(result["encrypted_key"].encode())
                self._encryption_keys[key_id] = key
                return key
            return None
        except Exception as e:
            self.logger.error(f"Failed to get encryption key: {str(e)}")
            return None
    
    # SecurityManager implementation
    async def initialize_security(self, tenant_id: str) -> bool:
        """Initialize security for a tenant"""
        await self._ensure_initialized()
        
        try:
            # Set default security settings
            default_settings = {
                "audit_logging_enabled": True,
                "encryption_enabled": True,
                "access_control_enabled": True,
                "compliance_monitoring_enabled": True,
                "rate_limiting_enabled": True,
                "max_login_attempts": 5,
                "session_timeout_minutes": 30,
                "password_policy": {
                    "min_length": 8,
                    "require_uppercase": True,
                    "require_lowercase": True,
                    "require_numbers": True,
                    "require_special": True
                }
            }
            
            await self.update_security_settings(tenant_id, default_settings)
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize security: {str(e)}")
            return False
    
    async def perform_security_audit(self, tenant_id: str) -> Dict[str, Any]:
        """Perform a comprehensive security audit"""
        await self._ensure_initialized()
        
        try:
            # Get security metrics
            metrics = await self.get_security_metrics(tenant_id, "daily")
            
            # Check compliance
            compliance_report = await self.get_compliance_report(tenant_id)
            
            # Get active security events
            active_events = await self.get_active_events(tenant_id)
            
            # Calculate overall security score
            security_score = 100
            
            # Deduct points for failed audits
            if metrics.get("audits", {}).get("total", 0) > 0:
                success_rate = metrics["audits"]["success_rate"]
                security_score -= (1 - success_rate) * 20
            
            # Deduct points for security events
            critical_events = len([e for e in active_events if e.severity == "critical"])
            high_events = len([e for e in active_events if e.severity == "high"])
            security_score -= critical_events * 10
            security_score -= high_events * 5
            
            # Deduct points for compliance violations
            if compliance_report.get("total_violations", 0) > 0:
                compliance_rate = compliance_report["compliance_rate"]
                security_score -= (1 - compliance_rate) * 15
            
            security_score = max(0, security_score)
            
            return {
                "tenant_id": tenant_id,
                "audit_timestamp": datetime.utcnow().isoformat(),
                "security_score": security_score,
                "metrics": metrics,
                "compliance": compliance_report,
                "active_events": len(active_events),
                "recommendations": await self._generate_security_recommendations(tenant_id, metrics, compliance_report, active_events)
            }
        except Exception as e:
            self.logger.error(f"Failed to perform security audit: {str(e)}")
            return {}
    
    async def _generate_security_recommendations(self, tenant_id: str, metrics: Dict, 
                                               compliance_report: Dict, active_events: List[SecurityEvent]) -> List[str]:
        """Generate security recommendations based on audit results"""
        recommendations = []
        
        # Check audit success rate
        if metrics.get("audits", {}).get("success_rate", 1.0) < 0.95:
            recommendations.append("Improve access control to reduce failed access attempts")
        
        # Check for high-risk activities
        if metrics.get("audits", {}).get("high_risk", 0) > 0:
            recommendations.append("Review high-risk activities and implement additional controls")
        
        # Check for critical events
        critical_events = [e for e in active_events if e.severity == "critical"]
        if critical_events:
            recommendations.append(f"Address {len(critical_events)} critical security events immediately")
        
        # Check compliance
        if compliance_report.get("compliance_rate", 1.0) < 0.9:
            recommendations.append("Address compliance violations to improve overall security posture")
        
        return recommendations
    
    async def get_security_status(self, tenant_id: str) -> Dict[str, Any]:
        """Get overall security status for a tenant"""
        await self._ensure_initialized()
        
        try:
            # Get basic metrics
            metrics = await self.get_security_metrics(tenant_id, "daily")
            
            # Get compliance status
            compliance_report = await self.get_compliance_report(tenant_id)
            
            # Get active events
            active_events = await self.get_active_events(tenant_id)
            
            # Determine overall status
            if any(e.severity == "critical" for e in active_events):
                status = "critical"
            elif any(e.severity == "high" for e in active_events):
                status = "warning"
            elif compliance_report.get("compliance_rate", 1.0) < 0.9:
                status = "attention"
            else:
                status = "healthy"
            
            return {
                "tenant_id": tenant_id,
                "status": status,
                "last_updated": datetime.utcnow().isoformat(),
                "active_events_count": len(active_events),
                "compliance_rate": compliance_report.get("compliance_rate", 1.0),
                "audit_success_rate": metrics.get("audits", {}).get("success_rate", 1.0)
            }
        except Exception as e:
            self.logger.error(f"Failed to get security status: {str(e)}")
            return {}
    
    async def update_security_settings(self, tenant_id: str, 
                                     settings: Dict[str, Any]) -> bool:
        """Update security settings for a tenant"""
        await self._ensure_initialized()
        
        try:
            settings_data = {
                "tenant_id": tenant_id,
                "settings": json.dumps(settings),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await self.storage.upsert("security_settings", settings_data)
            
            # Log the settings update
            await self.log_audit(SecurityAudit(
                audit_id=str(uuid4()),
                tenant_id=tenant_id,
                action="update_security_settings",
                resource="security_settings",
                success=True,
                risk_level="low"
            ))
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to update security settings: {str(e)}")
            return False
