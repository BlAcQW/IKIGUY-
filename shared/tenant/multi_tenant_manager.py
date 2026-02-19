"""
Multi-tenant Architecture

This module provides multi-tenant architecture capabilities including:
- Tenant isolation and data segregation
- Custom branding and white-labeling
- Role-based access control (RBAC)
- Audit logging and compliance
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import secrets
from pathlib import Path

# Optional advanced libraries
try:
    import bcrypt
    ADVANCED_SECURITY_AVAILABLE = True
except ImportError:
    ADVANCED_SECURITY_AVAILABLE = False
    logging.warning("Advanced security libraries not available. Install bcrypt for enhanced password hashing.")


class TenantStatus(Enum):
    """Tenant status enumeration"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    CANCELLED = "cancelled"


class UserRole(Enum):
    """User role enumeration"""
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    USER = "user"
    READ_ONLY = "read_only"
    CUSTOMER_SUPPORT = "customer_support"


class Permission(Enum):
    """Permission enumeration"""
    # Tenant management
    MANAGE_TENANTS = "manage_tenants"
    VIEW_TENANTS = "view_tenants"
    
    # User management
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    
    # Configuration
    MANAGE_CONFIG = "manage_config"
    VIEW_CONFIG = "view_config"
    
    # Data access
    ACCESS_DATA = "access_data"
    EXPORT_DATA = "export_data"
    
    # Analytics
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_ANALYTICS = "manage_analytics"
    
    # Billing
    VIEW_BILLING = "view_billing"
    MANAGE_BILLING = "manage_billing"
    
    # Security
    MANAGE_SECURITY = "manage_security"
    VIEW_AUDIT_LOGS = "view_audit_logs"


class AuditEventType(Enum):
    """Audit event types"""
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ACCESS = "access"
    EXPORT = "export"
    CONFIG_CHANGE = "config_change"
    SECURITY_EVENT = "security_event"


@dataclass
class TenantBranding:
    """Tenant branding configuration"""
    logo_url: Optional[str] = None
    primary_color: str = "#007bff"
    secondary_color: str = "#6c757d"
    company_name: str = "KasaAI"
    support_email: Optional[str] = None
    custom_domain: Optional[str] = None
    favicon_url: Optional[str] = None
    css_customizations: Optional[str] = None


@dataclass
class TenantLimits:
    """Tenant resource limits"""
    max_users: int = 10
    max_calls_per_month: int = 1000
    max_storage_gb: int = 10
    max_api_requests_per_day: int = 10000
    max_concurrent_calls: int = 5
    data_retention_days: int = 365


@dataclass
class TenantConfig:
    """Tenant configuration"""
    features_enabled: Set[str] = field(default_factory=set)
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    compliance_requirements: Set[str] = field(default_factory=set)
    data_sovereignty_region: Optional[str] = None
    backup_frequency_hours: int = 24
    monitoring_enabled: bool = True


@dataclass
class User:
    """User information"""
    user_id: str
    tenant_id: str
    email: str
    username: str
    role: UserRole
    permissions: Set[Permission] = field(default_factory=set)
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuditLog:
    """Audit log entry"""
    log_id: str
    tenant_id: str
    user_id: str
    event_type: AuditEventType
    resource_type: str
    resource_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    success: bool = True


@dataclass
class Tenant:
    """Tenant information"""
    tenant_id: str
    name: str
    domain: str
    status: TenantStatus
    branding: TenantBranding
    limits: TenantLimits
    config: TenantConfig
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    subscription_plan: str = "basic"
    billing_cycle: str = "monthly"


class MultiTenantManager:
    """
    Multi-tenant architecture manager
    
    Provides tenant isolation, data segregation, custom branding,
    role-based access control, and audit logging capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the multi-tenant manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Tenant storage
        self.tenants: Dict[str, Tenant] = {}
        self.users: Dict[str, User] = {}
        self.audit_logs: List[AuditLog] = []
        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout_hours = config.get('session_timeout_hours', 24)
        
        # Security settings
        self.password_min_length = config.get('password_min_length', 8)
        self.max_login_attempts = config.get('max_login_attempts', 5)
        self.lockout_duration_minutes = config.get('lockout_duration_minutes', 30)
        
        # Audit settings
        self.audit_log_retention_days = config.get('audit_log_retention_days', 365)
        self.audit_log_max_entries = config.get('audit_log_max_entries', 10000)
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._audit_cleanup_task: Optional[asyncio.Task] = None
        
        self.logger.info("MultiTenantManager initialized")
    
    async def start(self):
        """Start the multi-tenant manager"""
        self._cleanup_task = asyncio.create_task(self._cleanup_sessions_loop())
        self._audit_cleanup_task = asyncio.create_task(self._cleanup_audit_logs_loop())
        self.logger.info("MultiTenantManager started")
    
    async def stop(self):
        """Stop the multi-tenant manager"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._audit_cleanup_task:
            self._audit_cleanup_task.cancel()
        self.logger.info("MultiTenantManager stopped")
    
    # Tenant Management
    
    async def create_tenant(
        self,
        name: str,
        domain: str,
        admin_email: str,
        admin_username: str,
        subscription_plan: str = "basic",
        branding: Optional[TenantBranding] = None,
        limits: Optional[TenantLimits] = None,
        config: Optional[TenantConfig] = None
    ) -> Tenant:
        """
        Create a new tenant.
        
        Args:
            name: Tenant name
            domain: Tenant domain
            admin_email: Admin user email
            admin_username: Admin username
            subscription_plan: Subscription plan
            branding: Custom branding
            limits: Resource limits
            config: Tenant configuration
            
        Returns:
            Created tenant
        """
        tenant_id = str(uuid.uuid4())
        
        # Create tenant
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            domain=domain,
            status=TenantStatus.PENDING,
            branding=branding or TenantBranding(),
            limits=limits or TenantLimits(),
            config=config or TenantConfig(),
            subscription_plan=subscription_plan
        )
        
        self.tenants[tenant_id] = tenant
        
        # Create admin user
        admin_user = User(
            user_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            email=admin_email,
            username=admin_username,
            role=UserRole.TENANT_ADMIN,
            permissions={
                Permission.MANAGE_USERS,
                Permission.VIEW_USERS,
                Permission.MANAGE_CONFIG,
                Permission.VIEW_CONFIG,
                Permission.ACCESS_DATA,
                Permission.VIEW_ANALYTICS,
                Permission.VIEW_BILLING
            }
        )
        
        self.users[admin_user.user_id] = admin_user
        
        # Log creation
        await self._log_audit_event(
            tenant_id=tenant_id,
            user_id=admin_user.user_id,
            event_type=AuditEventType.CREATE,
            resource_type="tenant",
            resource_id=tenant_id,
            details={"name": name, "domain": domain}
        )
        
        self.logger.info(f"Created tenant {name} ({tenant_id})")
        return tenant
    
    async def update_tenant(
        self,
        tenant_id: str,
        updates: Dict[str, Any],
        user_id: str
    ) -> Optional[Tenant]:
        """
        Update tenant information.
        
        Args:
            tenant_id: Tenant ID
            updates: Update dictionary
            user_id: User performing the update
            
        Returns:
            Updated tenant or None if not found
        """
        if tenant_id not in self.tenants:
            return None
        
        tenant = self.tenants[tenant_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)
        
        tenant.updated_at = datetime.utcnow()
        
        # Log update
        await self._log_audit_event(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=AuditEventType.UPDATE,
            resource_type="tenant",
            resource_id=tenant_id,
            details=updates
        )
        
        self.logger.info(f"Updated tenant {tenant_id}")
        return tenant
    
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        return self.tenants.get(tenant_id)
    
    async def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Tenant]:
        """List tenants with optional filtering"""
        tenants = list(self.tenants.values())
        
        if status:
            tenants = [t for t in tenants if t.status == status]
        
        return tenants[offset:offset + limit]
    
    # User Management
    
    async def create_user(
        self,
        tenant_id: str,
        email: str,
        username: str,
        role: UserRole,
        permissions: Optional[Set[Permission]] = None,
        created_by: str = "system"
    ) -> Optional[User]:
        """
        Create a new user.
        
        Args:
            tenant_id: Tenant ID
            email: User email
            username: Username
            role: User role
            permissions: Custom permissions
            created_by: User creating this user
            
        Returns:
            Created user or None if tenant not found
        """
        if tenant_id not in self.tenants:
            return None
        
        user_id = str(uuid.uuid4())
        
        # Set default permissions based on role
        if permissions is None:
            permissions = self._get_default_permissions(role)
        
        user = User(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            username=username,
            role=role,
            permissions=permissions
        )
        
        self.users[user_id] = user
        
        # Log creation
        await self._log_audit_event(
            tenant_id=tenant_id,
            user_id=created_by,
            event_type=AuditEventType.CREATE,
            resource_type="user",
            resource_id=user_id,
            details={"email": email, "username": username, "role": role.value}
        )
        
        self.logger.info(f"Created user {username} in tenant {tenant_id}")
        return user
    
    async def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any],
        updated_by: str
    ) -> Optional[User]:
        """
        Update user information.
        
        Args:
            user_id: User ID
            updates: Update dictionary
            updated_by: User performing the update
            
        Returns:
            Updated user or None if not found
        """
        if user_id not in self.users:
            return None
        
        user = self.users[user_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        
        # Log update
        await self._log_audit_event(
            tenant_id=user.tenant_id,
            user_id=updated_by,
            event_type=AuditEventType.UPDATE,
            resource_type="user",
            resource_id=user_id,
            details=updates
        )
        
        self.logger.info(f"Updated user {user_id}")
        return user
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    async def list_users(
        self,
        tenant_id: str,
        role: Optional[UserRole] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        """List users in a tenant"""
        users = [u for u in self.users.values() if u.tenant_id == tenant_id]
        
        if role:
            users = [u for u in users if u.role == role]
        
        return users[offset:offset + limit]
    
    # Authentication & Authorization
    
    async def authenticate_user(
        self,
        email: str,
        password: str,
        tenant_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user.
        
        Args:
            email: User email
            password: User password
            tenant_id: Tenant ID
            ip_address: IP address
            user_agent: User agent string
            
        Returns:
            Authentication result or None if failed
        """
        # Find user
        user = None
        for u in self.users.values():
            if u.email == email and u.tenant_id == tenant_id:
                user = u
                break
        
        if not user or not user.is_active:
            await self._log_audit_event(
                tenant_id=tenant_id,
                user_id="unknown",
                event_type=AuditEventType.LOGIN,
                resource_type="user",
                details={"email": email, "reason": "user_not_found_or_inactive"},
                ip_address=ip_address,
                user_agent=user_agent,
                success=False
            )
            return None

        # TODO: Implement actual password verification
        # For now, just check if password is not empty
        if not password:
            await self._log_audit_event(
                tenant_id=tenant_id,
                user_id=user.user_id,
                event_type=AuditEventType.LOGIN,
                resource_type="user",
                details={"email": email, "reason": "invalid_password"},
                ip_address=ip_address,
                user_agent=user_agent,
                success=False
            )
            return None
        
        # Create session
        session_id = str(uuid.uuid4())
        session_data = {
            "user_id": user.user_id,
            "tenant_id": tenant_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        
        self.active_sessions[session_id] = session_data
        
        # Update user last login
        user.last_login = datetime.utcnow()
        
        # Log successful login
        await self._log_audit_event(
            tenant_id=tenant_id,
            user_id=user.user_id,
            event_type=AuditEventType.LOGIN,
            resource_type="user",
            details={"email": email, "session_id": session_id},
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        
        self.logger.info(f"User {email} authenticated in tenant {tenant_id}")
        
        return {
            "session_id": session_id,
            "user": user,
            "tenant": self.tenants[tenant_id]
        }
    
    async def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if invalid
        """
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        # Check session timeout
        if datetime.utcnow() - session["last_activity"] > timedelta(hours=self.session_timeout_hours):
            del self.active_sessions[session_id]
            return None
        
        # Update last activity
        session["last_activity"] = datetime.utcnow()
        
        # Get user and tenant
        user = self.users.get(session["user_id"])
        tenant = self.tenants.get(session["tenant_id"])
        
        if not user or not tenant or not user.is_active:
            del self.active_sessions[session_id]
            return None
        
        return {
            "session_id": session_id,
            "user": user,
            "tenant": tenant,
            "session": session
        }
    
    async def logout(self, session_id: str) -> bool:
        """
        Logout a user.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful
        """
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        # Log logout
        await self._log_audit_event(
            tenant_id=session["tenant_id"],
            user_id=session["user_id"],
            event_type=AuditEventType.LOGOUT,
            resource_type="session",
            details={"session_id": session_id}
        )
        
        del self.active_sessions[session_id]
        self.logger.info(f"User logged out from session {session_id}")
        return True
    
    async def check_permission(
        self,
        user_id: str,
        permission: Permission,
        resource_tenant_id: Optional[str] = None
    ) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user_id: User ID
            permission: Permission to check
            resource_tenant_id: Tenant ID of the resource (for cross-tenant access)
            
        Returns:
            True if user has permission
        """
        user = self.users.get(user_id)
        if not user or not user.is_active:
            return False
        
        # Super admin has all permissions
        if user.role == UserRole.SUPER_ADMIN:
            return True
        
        # Check tenant access
        if resource_tenant_id and user.tenant_id != resource_tenant_id:
            return False
        
        return permission in user.permissions
    
    # Branding & Customization
    
    async def get_tenant_branding(self, tenant_id: str) -> Optional[TenantBranding]:
        """Get tenant branding configuration"""
        tenant = self.tenants.get(tenant_id)
        return tenant.branding if tenant else None
    
    async def update_tenant_branding(
        self,
        tenant_id: str,
        branding: TenantBranding,
        user_id: str
    ) -> bool:
        """
        Update tenant branding.
        
        Args:
            tenant_id: Tenant ID
            branding: New branding configuration
            user_id: User performing the update
            
        Returns:
            True if successful
        """
        if tenant_id not in self.tenants:
            return False
        
        tenant = self.tenants[tenant_id]
        tenant.branding = branding
        tenant.updated_at = datetime.utcnow()
        
        # Log update
        await self._log_audit_event(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=AuditEventType.UPDATE,
            resource_type="branding",
            resource_id=tenant_id,
            details={"company_name": branding.company_name}
        )
        
        self.logger.info(f"Updated branding for tenant {tenant_id}")
        return True
    
    # Audit Logging
    
    async def _log_audit_event(
        self,
        tenant_id: str,
        user_id: str,
        event_type: AuditEventType,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True
    ):
        """Log an audit event"""
        log_entry = AuditLog(
            log_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
        
        self.audit_logs.append(log_entry)
        
        # Maintain log size limit
        if len(self.audit_logs) > self.audit_log_max_entries:
            self.audit_logs = self.audit_logs[-self.audit_log_max_entries:]
    
    async def get_audit_logs(
        self,
        tenant_id: str,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get audit logs with filtering"""
        logs = [log for log in self.audit_logs if log.tenant_id == tenant_id]
        
        if event_type:
            logs = [log for log in logs if log.event_type == event_type]
        
        if user_id:
            logs = [log for log in logs if log.user_id == user_id]
        
        if start_date:
            logs = [log for log in logs if log.timestamp >= start_date]
        
        if end_date:
            logs = [log for log in logs if log.timestamp <= end_date]
        
        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        return logs[offset:offset + limit]
    
    # Data Segregation
    
    async def get_tenant_data_prefix(self, tenant_id: str) -> str:
        """Get data prefix for tenant isolation"""
        return f"tenant_{tenant_id}_"
    
    async def is_tenant_data(self, data_key: str, tenant_id: str) -> bool:
        """Check if data belongs to a specific tenant"""
        prefix = await self.get_tenant_data_prefix(tenant_id)
        return data_key.startswith(prefix)
    
    # Background Tasks
    
    async def _cleanup_sessions_loop(self):
        """Background task to clean up expired sessions"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                current_time = datetime.utcnow()
                expired_sessions = []
                
                for session_id, session in self.active_sessions.items():
                    if current_time - session["last_activity"] > timedelta(hours=self.session_timeout_hours):
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    del self.active_sessions[session_id]
                
                if expired_sessions:
                    self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in session cleanup: {e}")
    
    async def _cleanup_audit_logs_loop(self):
        """Background task to clean up old audit logs"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                cutoff_date = datetime.utcnow() - timedelta(days=self.audit_log_retention_days)
                original_count = len(self.audit_logs)
                
                self.audit_logs = [log for log in self.audit_logs if log.timestamp > cutoff_date]
                
                cleaned_count = original_count - len(self.audit_logs)
                if cleaned_count > 0:
                    self.logger.info(f"Cleaned up {cleaned_count} old audit logs")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in audit log cleanup: {e}")
    
    # Helper Methods
    
    def _get_default_permissions(self, role: UserRole) -> Set[Permission]:
        """Get default permissions for a role"""
        if role == UserRole.SUPER_ADMIN:
            return set(Permission)
        elif role == UserRole.TENANT_ADMIN:
            return {
                Permission.MANAGE_USERS,
                Permission.VIEW_USERS,
                Permission.MANAGE_CONFIG,
                Permission.VIEW_CONFIG,
                Permission.ACCESS_DATA,
                Permission.EXPORT_DATA,
                Permission.VIEW_ANALYTICS,
                Permission.MANAGE_ANALYTICS,
                Permission.VIEW_BILLING,
                Permission.MANAGE_BILLING,
                Permission.VIEW_AUDIT_LOGS
            }
        elif role == UserRole.USER:
            return {
                Permission.VIEW_CONFIG,
                Permission.ACCESS_DATA,
                Permission.VIEW_ANALYTICS
            }
        elif role == UserRole.READ_ONLY:
            return {
                Permission.VIEW_CONFIG,
                Permission.VIEW_ANALYTICS
            }
        elif role == UserRole.CUSTOMER_SUPPORT:
            return {
                Permission.VIEW_USERS,
                Permission.VIEW_CONFIG,
                Permission.VIEW_ANALYTICS,
                Permission.VIEW_AUDIT_LOGS
            }
        else:
            return set()
    
    # Statistics & Monitoring
    
    async def get_tenant_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant statistics"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return {}
        
        # Count users
        user_count = len([u for u in self.users.values() if u.tenant_id == tenant_id])
        
        # Count active sessions
        active_sessions = len([s for s in self.active_sessions.values() if s["tenant_id"] == tenant_id])
        
        # Count audit logs
        audit_log_count = len([log for log in self.audit_logs if log.tenant_id == tenant_id])
        
        return {
            "tenant_id": tenant_id,
            "name": tenant.name,
            "status": tenant.status.value,
            "user_count": user_count,
            "active_sessions": active_sessions,
            "audit_log_count": audit_log_count,
            "created_at": tenant.created_at.isoformat(),
            "updated_at": tenant.updated_at.isoformat()
        }
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        return {
            "total_tenants": len(self.tenants),
            "total_users": len(self.users),
            "active_sessions": len(self.active_sessions),
            "total_audit_logs": len(self.audit_logs),
            "tenants_by_status": {
                status.value: len([t for t in self.tenants.values() if t.status == status])
                for status in TenantStatus
            }
        }
