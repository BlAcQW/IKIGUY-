"""
Tests for Multi-tenant Architecture

This module tests the multi-tenant architecture capabilities including:
- Tenant isolation and data segregation
- Custom branding and white-labeling
- Role-based access control (RBAC)
- Audit logging and compliance
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from apps.shared.tenant.multi_tenant_manager import (
    MultiTenantManager,
    TenantStatus,
    UserRole,
    Permission,
    AuditEventType,
    TenantBranding,
    TenantLimits,
    TenantConfig,
    User,
    AuditLog,
    Tenant
)


class TestMultiTenantManager:
    """Test cases for MultiTenantManager"""

    @pytest.fixture
    def config(self):
        """Test configuration"""
        return {
            'session_timeout_hours': 24,
            'password_min_length': 8,
            'max_login_attempts': 5,
            'lockout_duration_minutes': 30,
            'audit_log_retention_days': 365,
            'audit_log_max_entries': 1000
        }

    @pytest.fixture
    def multi_tenant_manager(self, config):
        """Fixture for MultiTenantManager instance"""
        with patch('shared.tenant.multi_tenant_manager.logging.getLogger'):
            return MultiTenantManager(config)

    @pytest.fixture
    def sample_tenant_data(self):
        """Sample tenant data"""
        return {
            'name': 'Test Company',
            'domain': 'testcompany.com',
            'admin_email': 'admin@testcompany.com',
            'admin_username': 'admin',
            'subscription_plan': 'premium'
        }

    @pytest.fixture
    def sample_branding(self):
        """Sample branding configuration"""
        return TenantBranding(
            logo_url='https://example.com/logo.png',
            primary_color='#ff0000',
            secondary_color='#00ff00',
            company_name='Test Company',
            support_email='support@testcompany.com'
        )

    @pytest.fixture
    def sample_limits(self):
        """Sample resource limits"""
        return TenantLimits(
            max_users=50,
            max_calls_per_month=5000,
            max_storage_gb=100,
            max_api_requests_per_day=50000
        )

    @pytest.fixture
    def sample_config(self):
        """Sample tenant configuration"""
        return TenantConfig(
            features_enabled={'analytics', 'ai_features', 'compliance'},
            custom_settings={'timezone': 'UTC', 'language': 'en'},
            compliance_requirements={'PCI_DSS', 'GDPR'},
            data_sovereignty_region='EU'
        )

    # Tenant Management Tests

    @pytest.mark.asyncio
    async def test_create_tenant_success(self, multi_tenant_manager, sample_tenant_data):
        """Test successful tenant creation"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        
        assert tenant is not None
        assert tenant.name == sample_tenant_data['name']
        assert tenant.domain == sample_tenant_data['domain']
        assert tenant.status == TenantStatus.PENDING
        assert tenant.subscription_plan == sample_tenant_data['subscription_plan']
        assert tenant.tenant_id in multi_tenant_manager.tenants
        
        # Check that admin user was created
        admin_users = [u for u in multi_tenant_manager.users.values() 
                      if u.tenant_id == tenant.tenant_id and u.role == UserRole.TENANT_ADMIN]
        assert len(admin_users) == 1
        assert admin_users[0].email == sample_tenant_data['admin_email']

    @pytest.mark.asyncio
    async def test_create_tenant_with_custom_config(self, multi_tenant_manager, sample_tenant_data, 
                                                   sample_branding, sample_limits, sample_config):
        """Test tenant creation with custom configuration"""
        tenant = await multi_tenant_manager.create_tenant(
            **sample_tenant_data,
            branding=sample_branding,
            limits=sample_limits,
            config=sample_config
        )
        
        assert tenant.branding == sample_branding
        assert tenant.limits == sample_limits
        assert tenant.config == sample_config

    @pytest.mark.asyncio
    async def test_update_tenant_success(self, multi_tenant_manager, sample_tenant_data):
        """Test successful tenant update"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        
        updates = {
            'name': 'Updated Company',
            'status': TenantStatus.ACTIVE
        }
        
        updated_tenant = await multi_tenant_manager.update_tenant(
            tenant.tenant_id, updates, tenant.tenant_id
        )
        
        assert updated_tenant is not None
        assert updated_tenant.name == 'Updated Company'
        assert updated_tenant.status == TenantStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_update_tenant_not_found(self, multi_tenant_manager):
        """Test tenant update with non-existent tenant"""
        result = await multi_tenant_manager.update_tenant(
            'non-existent-id', {'name': 'Test'}, 'user-id'
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_tenant_success(self, multi_tenant_manager, sample_tenant_data):
        """Test getting tenant by ID"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        retrieved_tenant = await multi_tenant_manager.get_tenant(tenant.tenant_id)
        
        assert retrieved_tenant == tenant

    @pytest.mark.asyncio
    async def test_get_tenant_not_found(self, multi_tenant_manager):
        """Test getting non-existent tenant"""
        result = await multi_tenant_manager.get_tenant('non-existent-id')
        assert result is None

    @pytest.mark.asyncio
    async def test_list_tenants(self, multi_tenant_manager, sample_tenant_data):
        """Test listing tenants"""
        # Create multiple tenants
        tenant1 = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        tenant2 = await multi_tenant_manager.create_tenant(
            name='Another Company',
            domain='another.com',
            admin_email='admin@another.com',
            admin_username='admin2'
        )
        
        # List all tenants
        all_tenants = await multi_tenant_manager.list_tenants()
        assert len(all_tenants) == 2
        
        # List by status
        pending_tenants = await multi_tenant_manager.list_tenants(status=TenantStatus.PENDING)
        assert len(pending_tenants) == 2

    # User Management Tests

    @pytest.mark.asyncio
    async def test_create_user_success(self, multi_tenant_manager, sample_tenant_data):
        """Test successful user creation"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        
        user = await multi_tenant_manager.create_user(
            tenant_id=tenant.tenant_id,
            email='user@testcompany.com',
            username='testuser',
            role=UserRole.USER,
            created_by=tenant.tenant_id
        )
        
        assert user is not None
        assert user.email == 'user@testcompany.com'
        assert user.username == 'testuser'
        assert user.role == UserRole.USER
        assert user.tenant_id == tenant.tenant_id
        assert user.user_id in multi_tenant_manager.users

    @pytest.mark.asyncio
    async def test_create_user_tenant_not_found(self, multi_tenant_manager):
        """Test user creation with non-existent tenant"""
        result = await multi_tenant_manager.create_user(
            tenant_id='non-existent-id',
            email='user@test.com',
            username='testuser',
            role=UserRole.USER
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_create_user_with_custom_permissions(self, multi_tenant_manager, sample_tenant_data):
        """Test user creation with custom permissions"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        
        custom_permissions = {Permission.VIEW_ANALYTICS, Permission.EXPORT_DATA}
        
        user = await multi_tenant_manager.create_user(
            tenant_id=tenant.tenant_id,
            email='user@testcompany.com',
            username='testuser',
            role=UserRole.USER,
            permissions=custom_permissions,
            created_by=tenant.tenant_id
        )
        
        assert user.permissions == custom_permissions

    @pytest.mark.asyncio
    async def test_update_user_success(self, multi_tenant_manager, sample_tenant_data):
        """Test successful user update"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        user = await multi_tenant_manager.create_user(
            tenant_id=tenant.tenant_id,
            email='user@testcompany.com',
            username='testuser',
            role=UserRole.USER,
            created_by=tenant.tenant_id
        )
        
        updates = {
            'username': 'updateduser',
            'is_active': False
        }
        
        updated_user = await multi_tenant_manager.update_user(
            user.user_id, updates, tenant.tenant_id
        )
        
        assert updated_user is not None
        assert updated_user.username == 'updateduser'
        assert updated_user.is_active is False

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, multi_tenant_manager):
        """Test user update with non-existent user"""
        result = await multi_tenant_manager.update_user(
            'non-existent-id', {'username': 'test'}, 'user-id'
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_success(self, multi_tenant_manager, sample_tenant_data):
        """Test getting user by ID"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        user = await multi_tenant_manager.create_user(
            tenant_id=tenant.tenant_id,
            email='user@testcompany.com',
            username='testuser',
            role=UserRole.USER,
            created_by=tenant.tenant_id
        )
        
        retrieved_user = await multi_tenant_manager.get_user(user.user_id)
        assert retrieved_user == user

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, multi_tenant_manager):
        """Test getting non-existent user"""
        result = await multi_tenant_manager.get_user('non-existent-id')
        assert result is None

    @pytest.mark.asyncio
    async def test_list_users(self, multi_tenant_manager, sample_tenant_data):
        """Test listing users in a tenant"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        
        # Create multiple users
        user1 = await multi_tenant_manager.create_user(
            tenant_id=tenant.tenant_id,
            email='user1@testcompany.com',
            username='user1',
            role=UserRole.USER,
            created_by=tenant.tenant_id
        )
        user2 = await multi_tenant_manager.create_user(
            tenant_id=tenant.tenant_id,
            email='user2@testcompany.com',
            username='user2',
            role=UserRole.READ_ONLY,
            created_by=tenant.tenant_id
        )
        
        # List all users
        all_users = await multi_tenant_manager.list_users(tenant.tenant_id)
        assert len(all_users) == 3  # Including admin user
        
        # List by role
        regular_users = await multi_tenant_manager.list_users(
            tenant.tenant_id, role=UserRole.USER
        )
        assert len(regular_users) == 1

    # Authentication & Authorization Tests

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, multi_tenant_manager, sample_tenant_data):
        """Test successful user authentication"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        
        # Get admin user
        admin_user = [u for u in multi_tenant_manager.users.values() 
                     if u.tenant_id == tenant.tenant_id and u.role == UserRole.TENANT_ADMIN][0]
        
        result = await multi_tenant_manager.authenticate_user(
            email=admin_user.email,
            password='validpassword',
            tenant_id=tenant.tenant_id,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0'
        )
        
        assert result is not None
        assert 'session_id' in result
        assert result['user'] == admin_user
        assert result['tenant'] == tenant
        assert result['session_id'] in multi_tenant_manager.active_sessions

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self, multi_tenant_manager, sample_tenant_data):
        """Test authentication with invalid password"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        admin_user = [u for u in multi_tenant_manager.users.values() 
                     if u.tenant_id == tenant.tenant_id and u.role == UserRole.TENANT_ADMIN][0]
        
        result = await multi_tenant_manager.authenticate_user(
            email=admin_user.email,
            password='',
            tenant_id=tenant.tenant_id
        )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, multi_tenant_manager, sample_tenant_data):
        """Test authentication with non-existent user"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        
        result = await multi_tenant_manager.authenticate_user(
            email='nonexistent@testcompany.com',
            password='password',
            tenant_id=tenant.tenant_id
        )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_session_success(self, multi_tenant_manager, sample_tenant_data):
        """Test successful session validation"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        admin_user = [u for u in multi_tenant_manager.users.values() 
                     if u.tenant_id == tenant.tenant_id and u.role == UserRole.TENANT_ADMIN][0]
        
        auth_result = await multi_tenant_manager.authenticate_user(
            email=admin_user.email,
            password='password',
            tenant_id=tenant.tenant_id
        )
        
        session_data = await multi_tenant_manager.validate_session(auth_result['session_id'])
        
        assert session_data is not None
        assert session_data['user'] == admin_user
        assert session_data['tenant'] == tenant

    @pytest.mark.asyncio
    async def test_validate_session_invalid(self, multi_tenant_manager):
        """Test session validation with invalid session ID"""
        result = await multi_tenant_manager.validate_session('invalid-session-id')
        assert result is None

    @pytest.mark.asyncio
    async def test_logout_success(self, multi_tenant_manager, sample_tenant_data):
        """Test successful logout"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        admin_user = [u for u in multi_tenant_manager.users.values() 
                     if u.tenant_id == tenant.tenant_id and u.role == UserRole.TENANT_ADMIN][0]
        
        auth_result = await multi_tenant_manager.authenticate_user(
            email=admin_user.email,
            password='password',
            tenant_id=tenant.tenant_id
        )
        
        session_id = auth_result['session_id']
        assert session_id in multi_tenant_manager.active_sessions
        
        result = await multi_tenant_manager.logout(session_id)
        assert result is True
        assert session_id not in multi_tenant_manager.active_sessions

    @pytest.mark.asyncio
    async def test_logout_invalid_session(self, multi_tenant_manager):
        """Test logout with invalid session ID"""
        result = await multi_tenant_manager.logout('invalid-session-id')
        assert result is False

    @pytest.mark.asyncio
    async def test_check_permission_super_admin(self, multi_tenant_manager, sample_tenant_data):
        """Test permission check for super admin"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        
        # Create super admin user
        super_admin = await multi_tenant_manager.create_user(
            tenant_id=tenant.tenant_id,
            email='superadmin@testcompany.com',
            username='superadmin',
            role=UserRole.SUPER_ADMIN,
            created_by=tenant.tenant_id
        )
        
        # Super admin should have all permissions
        for permission in Permission:
            has_permission = await multi_tenant_manager.check_permission(
                super_admin.user_id, permission
            )
            assert has_permission is True

    @pytest.mark.asyncio
    async def test_check_permission_tenant_admin(self, multi_tenant_manager, sample_tenant_data):
        """Test permission check for tenant admin"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        admin_user = [u for u in multi_tenant_manager.users.values() 
                     if u.tenant_id == tenant.tenant_id and u.role == UserRole.TENANT_ADMIN][0]
        
        # Tenant admin should have specific permissions
        assert await multi_tenant_manager.check_permission(
            admin_user.user_id, Permission.MANAGE_USERS
        ) is True
        assert await multi_tenant_manager.check_permission(
            admin_user.user_id, Permission.VIEW_ANALYTICS
        ) is True
        assert await multi_tenant_manager.check_permission(
            admin_user.user_id, Permission.MANAGE_TENANTS
        ) is False  # Tenant admin can't manage other tenants

    @pytest.mark.asyncio
    async def test_check_permission_cross_tenant(self, multi_tenant_manager, sample_tenant_data):
        """Test permission check across tenants"""
        tenant1 = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        tenant2 = await multi_tenant_manager.create_tenant(
            name='Another Company',
            domain='another.com',
            admin_email='admin@another.com',
            admin_username='admin2'
        )
        
        admin1 = [u for u in multi_tenant_manager.users.values() 
                 if u.tenant_id == tenant1.tenant_id and u.role == UserRole.TENANT_ADMIN][0]
        
        # Admin from tenant1 should not have access to tenant2 resources
        assert await multi_tenant_manager.check_permission(
            admin1.user_id, Permission.VIEW_USERS, resource_tenant_id=tenant2.tenant_id
        ) is False

    # Branding & Customization Tests

    @pytest.mark.asyncio
    async def test_get_tenant_branding(self, multi_tenant_manager, sample_tenant_data, sample_branding):
        """Test getting tenant branding"""
        tenant = await multi_tenant_manager.create_tenant(
            **sample_tenant_data, branding=sample_branding
        )
        
        branding = await multi_tenant_manager.get_tenant_branding(tenant.tenant_id)
        assert branding == sample_branding

    @pytest.mark.asyncio
    async def test_get_tenant_branding_not_found(self, multi_tenant_manager):
        """Test getting branding for non-existent tenant"""
        result = await multi_tenant_manager.get_tenant_branding('non-existent-id')
        assert result is None

    @pytest.mark.asyncio
    async def test_update_tenant_branding_success(self, multi_tenant_manager, sample_tenant_data):
        """Test successful branding update"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        
        new_branding = TenantBranding(
            logo_url='https://newlogo.com/logo.png',
            primary_color='#0000ff',
            company_name='New Company Name'
        )
        
        result = await multi_tenant_manager.update_tenant_branding(
            tenant.tenant_id, new_branding, tenant.tenant_id
        )
        
        assert result is True
        
        updated_branding = await multi_tenant_manager.get_tenant_branding(tenant.tenant_id)
        assert updated_branding == new_branding

    @pytest.mark.asyncio
    async def test_update_tenant_branding_not_found(self, multi_tenant_manager):
        """Test branding update for non-existent tenant"""
        new_branding = TenantBranding(company_name='Test')
        result = await multi_tenant_manager.update_tenant_branding(
            'non-existent-id', new_branding, 'user-id'
        )
        assert result is False

    # Audit Logging Tests

    @pytest.mark.asyncio
    async def test_audit_log_creation(self, multi_tenant_manager, sample_tenant_data):
        """Test audit log creation during operations"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        
        # Check that tenant creation was logged
        logs = await multi_tenant_manager.get_audit_logs(tenant.tenant_id)
        assert len(logs) > 0
        
        create_log = [log for log in logs if log.event_type == AuditEventType.CREATE and 
                     log.resource_type == 'tenant']
        assert len(create_log) == 1
        assert create_log[0].resource_id == tenant.tenant_id

    @pytest.mark.asyncio
    async def test_get_audit_logs_filtering(self, multi_tenant_manager, sample_tenant_data):
        """Test audit log filtering"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        admin_user = [u for u in multi_tenant_manager.users.values() 
                     if u.tenant_id == tenant.tenant_id and u.role == UserRole.TENANT_ADMIN][0]
        
        # Create some activity
        await multi_tenant_manager.authenticate_user(
            email=admin_user.email,
            password='password',
            tenant_id=tenant.tenant_id
        )
        
        # Filter by event type
        login_logs = await multi_tenant_manager.get_audit_logs(
            tenant.tenant_id, event_type=AuditEventType.LOGIN
        )
        assert len(login_logs) > 0
        
        # Filter by user
        user_logs = await multi_tenant_manager.get_audit_logs(
            tenant.tenant_id, user_id=admin_user.user_id
        )
        assert len(user_logs) > 0

    @pytest.mark.asyncio
    async def test_audit_log_retention(self, multi_tenant_manager, sample_tenant_data):
        """Test audit log retention limits"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        
        # Add more logs than the limit
        for i in range(1100):  # More than the 1000 limit
            await multi_tenant_manager._log_audit_event(
                tenant_id=tenant.tenant_id,
                user_id='test-user',
                event_type=AuditEventType.ACCESS,
                resource_type='test',
                details={'test': i}
            )
        
        # Check that logs are limited
        assert len(multi_tenant_manager.audit_logs) <= multi_tenant_manager.audit_log_max_entries

    # Data Segregation Tests

    @pytest.mark.asyncio
    async def test_tenant_data_prefix(self, multi_tenant_manager, sample_tenant_data):
        """Test tenant data prefix generation"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        
        prefix = await multi_tenant_manager.get_tenant_data_prefix(tenant.tenant_id)
        assert prefix == f"tenant_{tenant.tenant_id}_"

    @pytest.mark.asyncio
    async def test_tenant_data_identification(self, multi_tenant_manager, sample_tenant_data):
        """Test tenant data identification"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        prefix = await multi_tenant_manager.get_tenant_data_prefix(tenant.tenant_id)
        
        # Test valid tenant data
        assert await multi_tenant_manager.is_tenant_data(
            f"{prefix}user_data", tenant.tenant_id
        ) is True
        
        # Test invalid tenant data
        assert await multi_tenant_manager.is_tenant_data(
            "global_data", tenant.tenant_id
        ) is False

    # Statistics & Monitoring Tests

    @pytest.mark.asyncio
    async def test_tenant_statistics(self, multi_tenant_manager, sample_tenant_data):
        """Test tenant statistics generation"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        
        stats = await multi_tenant_manager.get_tenant_statistics(tenant.tenant_id)
        
        assert stats['tenant_id'] == tenant.tenant_id
        assert stats['name'] == tenant.name
        assert stats['status'] == tenant.status.value
        assert 'user_count' in stats
        assert 'active_sessions' in stats
        assert 'audit_log_count' in stats

    @pytest.mark.asyncio
    async def test_system_statistics(self, multi_tenant_manager, sample_tenant_data):
        """Test system-wide statistics"""
        # Create multiple tenants
        tenant1 = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        tenant2 = await multi_tenant_manager.create_tenant(
            name='Another Company',
            domain='another.com',
            admin_email='admin@another.com',
            admin_username='admin2'
        )
        
        stats = await multi_tenant_manager.get_system_statistics()
        
        assert stats['total_tenants'] == 2
        assert stats['total_users'] == 2  # 2 tenants * 1 admin user each
        assert 'tenants_by_status' in stats
        assert stats['tenants_by_status'][TenantStatus.PENDING.value] == 2

    # Background Tasks Tests

    @pytest.mark.asyncio
    async def test_start_and_stop(self, multi_tenant_manager):
        """Test starting and stopping the manager"""
        await multi_tenant_manager.start()
        assert multi_tenant_manager._cleanup_task is not None
        assert multi_tenant_manager._audit_cleanup_task is not None
        
        await multi_tenant_manager.stop()
        # Tasks should be cancelled
        await asyncio.sleep(0.1)  # Give time for cancellation to process
        assert multi_tenant_manager._cleanup_task.done() is True
        assert multi_tenant_manager._audit_cleanup_task.done() is True

    # Helper Methods Tests

    def test_get_default_permissions(self, multi_tenant_manager):
        """Test default permission assignment"""
        # Test super admin permissions
        super_admin_perms = multi_tenant_manager._get_default_permissions(UserRole.SUPER_ADMIN)
        assert len(super_admin_perms) == len(Permission)
        
        # Test tenant admin permissions
        tenant_admin_perms = multi_tenant_manager._get_default_permissions(UserRole.TENANT_ADMIN)
        assert Permission.MANAGE_USERS in tenant_admin_perms
        assert Permission.MANAGE_TENANTS not in tenant_admin_perms  # Can't manage other tenants
        
        # Test user permissions
        user_perms = multi_tenant_manager._get_default_permissions(UserRole.USER)
        assert Permission.VIEW_CONFIG in user_perms
        assert Permission.MANAGE_USERS not in user_perms

    # Edge Cases and Error Handling

    @pytest.mark.asyncio
    async def test_create_tenant_duplicate_domain(self, multi_tenant_manager, sample_tenant_data):
        """Test creating tenant with duplicate domain"""
        tenant1 = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        
        # Create another tenant with same domain (should be allowed for now)
        tenant2 = await multi_tenant_manager.create_tenant(
            name='Another Company',
            domain=sample_tenant_data['domain'],  # Same domain
            admin_email='admin2@testcompany.com',
            admin_username='admin2'
        )
        
        assert tenant2 is not None
        assert tenant2.domain == sample_tenant_data['domain']

    @pytest.mark.asyncio
    async def test_session_timeout(self, multi_tenant_manager, sample_tenant_data):
        """Test session timeout functionality"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        admin_user = [u for u in multi_tenant_manager.users.values() 
                     if u.tenant_id == tenant.tenant_id and u.role == UserRole.TENANT_ADMIN][0]
        
        auth_result = await multi_tenant_manager.authenticate_user(
            email=admin_user.email,
            password='password',
            tenant_id=tenant.tenant_id
        )
        
        session_id = auth_result['session_id']
        
        # Manually expire the session
        multi_tenant_manager.active_sessions[session_id]['last_activity'] = (
            datetime.utcnow() - timedelta(hours=25)  # More than 24 hour timeout
        )
        
        # Session should be invalid
        result = await multi_tenant_manager.validate_session(session_id)
        assert result is None
        assert session_id not in multi_tenant_manager.active_sessions

    @pytest.mark.asyncio
    async def test_inactive_user_authentication(self, multi_tenant_manager, sample_tenant_data):
        """Test authentication with inactive user"""
        tenant = await multi_tenant_manager.create_tenant(**sample_tenant_data)
        
        # Create user and deactivate
        user = await multi_tenant_manager.create_user(
            tenant_id=tenant.tenant_id,
            email='inactive@testcompany.com',
            username='inactive',
            role=UserRole.USER,
            created_by=tenant.tenant_id
        )
        
        await multi_tenant_manager.update_user(
            user.user_id, {'is_active': False}, tenant.tenant_id
        )
        
        # Try to authenticate inactive user
        result = await multi_tenant_manager.authenticate_user(
            email=user.email,
            password='password',
            tenant_id=tenant.tenant_id
        )
        
        assert result is None
