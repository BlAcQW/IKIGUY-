"""
Security Service for KasaAI Developer Platform.

This service provides security capabilities using the shared security library,
with developer-specific optimizations and extensions.
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
from uuid import uuid4

# Use centralized import configuration
try:
    from .import_config import get_security_engine, get_storage_backend
    SecurityEngine = get_security_engine()
    MemoryStorageBackend = get_storage_backend()
    from apps.shared.security import (
        SecurityAuditor, SecurityMonitor, AccessController,
        ComplianceMonitor, EncryptionManager, SecurityManager,
        SecurityAudit, SecurityEvent, AccessControl, ComplianceRule, ComplianceViolation
    )
    from apps.shared.storage import StorageConfig
    SHARED_LIBRARY_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Shared security library not available: {e}")
    SHARED_LIBRARY_AVAILABLE = False
    # Create placeholder classes for fallback
    class SecurityEngine: pass
    class SecurityAudit: pass
    class SecurityEvent: pass
    class ComplianceViolation: pass
    class MemoryStorageBackend: pass
    class StorageConfig: pass


class DeveloperSecurityService:
    """
    Developer Platform Security Service.
    
    Provides security capabilities using the shared security library with
    developer-specific optimizations and extensions.
    """
    
    def __init__(self, storage_backend: Optional[Any] = None):
        self.logger = logging.getLogger("DeveloperSecurityService")
        
        if not SHARED_LIBRARY_AVAILABLE:
            self.logger.warning("Using fallback security service - shared library not available")
            self._init_fallback()
            return
            
        if storage_backend is None:
            storage_config = StorageConfig(backend_type="memory")
            self.storage = MemoryStorageBackend(storage_config)
        else:
            self.storage = storage_backend
        
        # Initialize security components
        try:
            self.security_engine = SecurityEngine(self.storage)
        except Exception as e:
            self.logger.warning(f"Failed to initialize security engine: {e}")
            self.security_engine = None
        
        # Developer-specific configuration
        self.dev_config = self._load_developer_environment_config()
    
    def _init_fallback(self):
        """Initialize fallback components when shared library is not available."""
        self.storage = None
        self.security_engine = None
        self.dev_config = self._load_developer_environment_config()
    
    def _load_developer_environment_config(self):
        """Load developer-specific environment configuration."""
        return {
            'audit_enabled': os.getenv('DEV_SECURITY_AUDIT_ENABLED', 'true').lower() == 'true',
            'monitoring_enabled': os.getenv('DEV_SECURITY_MONITORING_ENABLED', 'true').lower() == 'true',
            'access_control_enabled': os.getenv('DEV_SECURITY_ACCESS_CONTROL_ENABLED', 'true').lower() == 'true',
            'compliance_enabled': os.getenv('DEV_SECURITY_COMPLIANCE_ENABLED', 'true').lower() == 'true',
            'encryption_enabled': os.getenv('DEV_SECURITY_ENCRYPTION_ENABLED', 'true').lower() == 'true',
            'fallback_enabled': os.getenv('DEV_SECURITY_FALLBACK_ENABLED', 'true').lower() == 'true',
            'log_level': os.getenv('DEV_SECURITY_LOG_LEVEL', 'INFO')
        }
    
    async def start(self):
        """Start the security service."""
        self.logger.info("Starting Developer Security Service")
        if SHARED_LIBRARY_AVAILABLE and self.security_engine:
            try:
                await self.security_engine.initialize_security("developer_platform")
            except Exception as e:
                self.logger.warning(f"Failed to initialize security engine: {e}")
    
    async def stop(self):
        """Stop the security service."""
        self.logger.info("Stopping Developer Security Service")
    
    async def create_audit_log(
        self,
        event_type: str,
        user_id: str,
        resource: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a security audit log entry."""
        if not SHARED_LIBRARY_AVAILABLE or self.security_engine is None:
            return {
                "log_id": f"fallback_log_{uuid4()}",
                "event_type": event_type,
                "user_id": user_id,
                "status": "fallback_created"
            }
        
        try:
            audit = SecurityAudit(
                audit_id=str(uuid4()),
                tenant_id="developer_platform",
                user_id=user_id,
                action=action,
                resource=resource,
                timestamp=datetime.now(),
                ip_address=metadata.get('ip') if metadata else None,
                user_agent=metadata.get('user_agent') if metadata else None,
                success=True,
                details=metadata or {},
                risk_level="low"
            )
            
            success = await self.security_engine.log_audit(audit)
            return {'log_id': audit.audit_id, 'status': 'created' if success else 'failed'}
        except Exception as e:
            self.logger.error(f"Error creating audit log: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def get_audit_logs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get security audit logs."""
        if not SHARED_LIBRARY_AVAILABLE or self.security_engine is None:
            return [
                {"log_id": "fallback_log_1", "event_type": "fallback_event"},
                {"log_id": "fallback_log_2", "event_type": "fallback_event"}
            ]
        
        try:
            tenant_id = filters.get('tenant_id', 'developer_platform') if filters else 'developer_platform'
            start_date = filters.get('start_date') if filters else None
            end_date = filters.get('end_date') if filters else None
            
            logs = await self.security_engine.get_audit_logs(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit or 100
            )
            return logs
        except Exception as e:
            self.logger.error(f"Error getting audit logs: {e}")
            return []
    
    async def check_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Check if user has access to resource."""
        if not SHARED_LIBRARY_AVAILABLE or self.security_engine is None:
            return {
                "allowed": True,
                "reason": "fallback_authorized",
                "user_id": user_id,
                "resource": resource
            }
        
        try:
            result = await self.security_engine.check_access(
                tenant_id="developer_platform",
                user_id=user_id,
                resource=resource,
                action=action,
                context=context or {}
            )
            return result
        except Exception as e:
            self.logger.error(f"Error checking access: {e}")
            return {'allowed': False, 'reason': str(e)}
    
    async def encrypt_data(
        self,
        data: str,
        key_id: Optional[str] = None,
        algorithm: str = "AES-256"
    ) -> Dict[str, Any]:
        """Encrypt data."""
        if not SHARED_LIBRARY_AVAILABLE or self.security_engine is None:
            return {
                "encrypted_data": f"fallback_encrypted_{data}",
                "key_id": key_id or "fallback_key",
                "algorithm": algorithm,
                "fallback": True
            }
        
        try:
            encrypted = await self.security_engine.encrypt_data(
                data=data,
                key_id=key_id
            )
            return {'encrypted_data': encrypted, 'key_id': key_id, 'algorithm': algorithm}
        except Exception as e:
            self.logger.error(f"Error encrypting data: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def decrypt_data(
        self,
        encrypted_data: str,
        key_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Decrypt data."""
        if not SHARED_LIBRARY_AVAILABLE or self.security_engine is None:
            return {
                "decrypted_data": encrypted_data.replace("fallback_encrypted_", ""),
                "key_id": key_id or "fallback_key",
                "fallback": True
            }
        
        try:
            decrypted = await self.security_engine.decrypt_data(
                encrypted_data=encrypted_data,
                key_id=key_id
            )
            return {'decrypted_data': decrypted, 'key_id': key_id}
        except Exception as e:
            self.logger.error(f"Error decrypting data: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def get_developer_security_config(self) -> Dict[str, Any]:
        """Get developer security configuration."""
        return {
            "config": self.dev_config,
            "shared_library_available": SHARED_LIBRARY_AVAILABLE,
            "components": {
                "security_engine": self.security_engine is not None
            }
        }
