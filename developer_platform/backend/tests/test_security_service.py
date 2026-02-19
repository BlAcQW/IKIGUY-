"""
Unit tests for Developer Security Service.

Tests the Developer Platform Security service that uses the shared security library.
"""

import pytest
import os
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from ..services.security_service import DeveloperSecurityService
from apps.shared.security import SecurityEngine
from apps.shared.storage import MemoryStorageBackend, StorageConfig


class TestDeveloperSecurityService:
    """Test cases for DeveloperSecurityService."""
    
    @pytest.fixture
    def security_service(self):
        """Create a security service instance for testing."""
        return DeveloperSecurityService()
    
    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage backend."""
        return Mock(spec=MemoryStorageBackend)
    
    @pytest.fixture
    def security_service_with_mock_storage(self, mock_storage):
        """Create a security service with mock storage."""
        return DeveloperSecurityService(storage_backend=mock_storage)
    
    def test_initialization(self, security_service):
        """Test service initialization."""
        assert security_service.logger is not None
        assert security_service.storage is not None
        assert security_service.security_engine is not None
        assert security_service._dev_config_cache != {}  # Should be populated during init
        assert security_service._cache_ttl == {}
    
    def test_initialization_with_custom_storage(self, mock_storage):
        """Test service initialization with custom storage."""
        service = DeveloperSecurityService(storage_backend=mock_storage)
        assert service.storage == mock_storage
    
    @patch.dict(os.environ, {
        'DEV_SECURITY_AUDIT_ENABLED': 'true',
        'DEV_SECURITY_MONITORING_ENABLED': 'true',
        'DEV_SECURITY_ACCESS_CONTROL_ENABLED': 'true',
        'DEV_SECURITY_COMPLIANCE_ENABLED': 'true',
        'DEV_SECURITY_ENCRYPTION_ENABLED': 'true',
        'DEV_SECURITY_OFFLINE_MODE': 'false',
        'DEV_SECURITY_SYNC_INTERVAL': '300',
        'DEV_SECURITY_CACHE_TTL': '3600',
        'DEV_SECURITY_FALLBACK_ENABLED': 'true',
        'DEV_SECURITY_LOG_LEVEL': 'INFO'
    })
    def test_load_developer_environment_config(self, security_service):
        """Test environment configuration loading."""
        security_service._load_developer_environment_config()
        
        config = security_service._dev_config_cache
        assert config['audit_enabled'] is True
        assert config['monitoring_enabled'] is True
        assert config['access_control_enabled'] is True
        assert config['compliance_enabled'] is True
        assert config['encryption_enabled'] is True
        assert config['offline_mode'] is False
        assert config['sync_interval'] == 300
        assert config['cache_ttl'] == 3600
        assert config['fallback_enabled'] is True
        assert config['log_level'] == 'INFO'
    
    @pytest.mark.asyncio
    async def test_start(self, security_service):
        """Test service start."""
        with patch.object(security_service.security_engine, 'initialize_security', new_callable=AsyncMock) as mock_start:
            await security_service.start()
            mock_start.assert_called_once_with("developer_platform")
    
    @pytest.mark.asyncio
    async def test_stop(self, security_service):
        """Test service stop."""
        await security_service.stop()
        # No cleanup method to mock, just verify it doesn't raise an exception
    
    # Security Audit Operations
    @pytest.mark.asyncio
    async def test_create_audit_log(self, security_service):
        """Test creating audit log."""
        # Ensure fallback is disabled for this test
        security_service._dev_config_cache['fallback_enabled'] = False
        
        with patch.object(security_service.security_engine, 'log_audit', new_callable=AsyncMock) as mock_log:
            mock_log.return_value = True
            
            result = await security_service.create_audit_log('user_login', 'user123', '/api/data', 'read', {'ip': '192.168.1.1'})
            
            mock_log.assert_called_once()
            assert result['status'] == 'created'
            assert 'log_id' in result
    
    @pytest.mark.asyncio
    async def test_get_audit_logs(self, security_service):
        """Test getting audit logs."""
        with patch.object(security_service.security_engine, 'get_audit_logs', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [{'audit_id': 'log1'}, {'audit_id': 'log2'}]
            
            result = await security_service.get_audit_logs({'tenant_id': 'developer_platform'}, limit=10)
            
            mock_get.assert_called_once_with(
                tenant_id='developer_platform',
                start_date=None,
                end_date=None,
                limit=10
            )
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_export_audit_logs(self, security_service):
        """Test exporting audit logs."""
        with patch.object(security_service.security_engine, 'export_audit_logs', new_callable=AsyncMock) as mock_export:
            mock_export.return_value = '{"logs": [{"id": "log1"}]}'
            
            result = await security_service.export_audit_logs('json', {'tenant_id': 'developer_platform'})
            
            mock_export.assert_called_once_with(
                tenant_id='developer_platform',
                format='json',
                start_date=None,
                end_date=None
            )
            assert result == '{"logs": [{"id": "log1"}]}'
    
    # Security Monitoring Operations
    @pytest.mark.asyncio
    async def test_monitor_security_event(self, security_service):
        """Test monitoring security event."""
        with patch.object(security_service.security_engine, 'record_event', new_callable=AsyncMock) as mock_record:
            mock_record.return_value = True
            
            result = await security_service.monitor_security_event({'event_type': 'failed_login'}, 'high')
            
            mock_record.assert_called_once()
            assert result['status'] == 'recorded'
            assert 'event_id' in result
    
    @pytest.mark.asyncio
    async def test_get_security_alerts(self, security_service):
        """Test getting security alerts."""
        with patch.object(security_service.security_engine, 'get_active_events', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [{'event_id': 'alert1'}, {'event_id': 'alert2'}]
            
            result = await security_service.get_security_alerts('high', 'last_24h')
            
            mock_get.assert_called_once_with(
                tenant_id='developer_platform',
                severity='high',
                limit=100
            )
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, security_service):
        """Test acknowledging alert."""
        with patch.object(security_service.security_engine, 'resolve_event', new_callable=AsyncMock) as mock_resolve:
            mock_resolve.return_value = True
            
            result = await security_service.acknowledge_alert('alert123', 'user123', 'Resolved')
            
            mock_resolve.assert_called_once_with(
                event_id='alert123',
                resolution_notes='Resolved'
            )
            assert result['status'] == 'acknowledged'
    
    # Access Control Operations
    @pytest.mark.asyncio
    async def test_check_access(self, security_service):
        """Test checking access."""
        with patch.object(security_service.security_engine, 'check_access', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = {'allowed': True, 'reason': 'authorized'}
            
            result = await security_service.check_access('user123', '/api/data', 'read', {'ip': '192.168.1.1'})
            
            mock_check.assert_called_once_with(
                tenant_id='developer_platform',
                user_id='user123',
                resource='/api/data',
                action='read',
                context={'ip': '192.168.1.1'}
            )
            assert result == {'allowed': True, 'reason': 'authorized'}
    
    @pytest.mark.asyncio
    async def test_grant_access(self, security_service):
        """Test granting access."""
        expires_at = datetime.now() + timedelta(hours=1)
        with patch.object(security_service.security_engine, 'grant_access', new_callable=AsyncMock) as mock_grant:
            mock_grant.return_value = {'access_id': 'access123', 'status': 'granted'}
            
            result = await security_service.grant_access('user123', '/api/data', ['read', 'write'], expires_at)
            
            mock_grant.assert_called_once_with(
                tenant_id='developer_platform',
                user_id='user123',
                resource='/api/data',
                permissions=['read', 'write'],
                expires_at=expires_at
            )
            assert result == {'access_id': 'access123', 'status': 'granted'}
    
    @pytest.mark.asyncio
    async def test_revoke_access(self, security_service):
        """Test revoking access."""
        with patch.object(security_service.security_engine, 'revoke_access', new_callable=AsyncMock) as mock_revoke:
            mock_revoke.return_value = {'access_id': 'access123', 'status': 'revoked'}
            
            result = await security_service.revoke_access('user123', '/api/data', 'Security violation')
            
            mock_revoke.assert_called_once_with(
                tenant_id='developer_platform',
                user_id='user123',
                resource='/api/data',
                reason='Security violation'
            )
            assert result == {'access_id': 'access123', 'status': 'revoked'}
    
    # Compliance Operations
    @pytest.mark.asyncio
    async def test_check_compliance(self, security_service):
        """Test checking compliance."""
        with patch.object(security_service.security_engine, 'check_compliance', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = {'compliant': True, 'violations': []}
            
            result = await security_service.check_compliance('gdpr', {'user_data': {'email': 'test@example.com'}})
            
            mock_check.assert_called_once_with(
                tenant_id='developer_platform',
                rule_id='gdpr',
                data={'user_data': {'email': 'test@example.com'}}
            )
            assert result == {'compliant': True, 'violations': []}
    
    @pytest.mark.asyncio
    async def test_get_compliance_report(self, security_service):
        """Test getting compliance report."""
        with patch.object(security_service.security_engine, 'get_compliance_report', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {'framework': 'gdpr', 'status': 'compliant', 'score': 95.5}
            
            result = await security_service.get_compliance_report('gdpr', 'last_month')
            
            mock_get.assert_called_once_with(
                tenant_id='developer_platform',
                framework='gdpr',
                time_range='last_month'
            )
            assert result['framework'] == 'gdpr'
    
    @pytest.mark.asyncio
    async def test_report_violation(self, security_service):
        """Test reporting violation."""
        with patch.object(security_service.security_engine, 'record_violation', new_callable=AsyncMock) as mock_record:
            mock_record.return_value = True
            
            result = await security_service.report_violation('rule123', {'rule': 'data_retention'}, 'high')
            
            mock_record.assert_called_once()
            assert result['status'] == 'reported'
            assert 'violation_id' in result
    
    # Encryption Operations
    @pytest.mark.asyncio
    async def test_encrypt_data(self, security_service):
        """Test encrypting data."""
        # Ensure fallback is disabled for this test
        security_service._dev_config_cache['fallback_enabled'] = False
        
        with patch.object(security_service.security_engine, 'encrypt_data', new_callable=AsyncMock) as mock_encrypt:
            mock_encrypt.return_value = 'encrypted_string'
            
            result = await security_service.encrypt_data('sensitive_data', 'key123', 'AES-256')
            
            mock_encrypt.assert_called_once_with(
                data='sensitive_data',
                key_id='key123'
            )
            assert result['encrypted_data'] == 'encrypted_string'
    
    @pytest.mark.asyncio
    async def test_decrypt_data(self, security_service):
        """Test decrypting data."""
        with patch.object(security_service.security_engine, 'decrypt_data', new_callable=AsyncMock) as mock_decrypt:
            mock_decrypt.return_value = 'sensitive_data'
            
            result = await security_service.decrypt_data('encrypted_string', 'key123')
            
            mock_decrypt.assert_called_once_with(
                encrypted_data='encrypted_string',
                key_id='key123'
            )
            assert result['decrypted_data'] == 'sensitive_data'
    
    @pytest.mark.asyncio
    async def test_generate_key(self, security_service):
        """Test generating key."""
        with patch.object(security_service.security_engine, 'generate_key', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = 'key123'
            
            result = await security_service.generate_key('AES-256', 'test_key')
            
            mock_generate.assert_called_once_with(
                key_name='test_key',
                key_type='AES-256'
            )
            assert result['key_id'] == 'key123'
    
    # Developer-specific Operations
    @pytest.mark.asyncio
    async def test_get_developer_security_config(self, security_service):
        """Test getting developer security config."""
        with patch.object(security_service, '_get_cache_status') as mock_cache:
            with patch.object(security_service, '_get_offline_status') as mock_offline:
                with patch.object(security_service, '_get_security_status') as mock_security:
                    mock_cache.return_value = {'cache_size': 100}
                    mock_offline.return_value = {'enabled': False}
                    mock_security.return_value = {'alerts_count': 5}
                    
                    result = await security_service.get_developer_security_config()
                    
                    assert 'config' in result
                    assert 'cache_status' in result
                    assert 'offline_status' in result
                    assert 'security_status' in result
    
    @pytest.mark.asyncio
    async def test_validate_developer_security_config(self, security_service):
        """Test validating developer security config."""
        security_service._dev_config_cache = {'audit_enabled': True, 'monitoring_enabled': True, 'access_control_enabled': True}
        result = await security_service.validate_developer_security_config()
        assert result is True
        
        security_service._dev_config_cache = {}
        result = await security_service.validate_developer_security_config()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_offline_security_status(self, security_service):
        """Test getting offline security status."""
        result = await security_service.get_offline_security_status()
        assert 'enabled' in result
        assert 'fallback_enabled' in result
    
    @pytest.mark.asyncio
    async def test_sync_security_with_core(self, security_service):
        """Test syncing security with core."""
        result = await security_service.sync_security_with_core('https://core.example.com', 'token123')
        assert result is True  # Placeholder implementation
    
    @pytest.mark.asyncio
    async def test_get_security_metrics(self, security_service):
        """Test getting security metrics."""
        with patch.object(security_service.security_engine, 'get_security_metrics', new_callable=AsyncMock) as mock_metrics:
            mock_metrics.return_value = {'total_events': 100}
            
            result = await security_service.get_security_metrics('tenant123')
            
            mock_metrics.assert_called_once_with(
                tenant_id='tenant123',
                time_range='last_30_days'
            )
            assert 'metrics' in result
            assert 'config' in result
            assert 'cache_status' in result
    
    @pytest.mark.asyncio
    async def test_get_security_reports(self, security_service):
        """Test getting security reports."""
        with patch.object(security_service, 'get_audit_logs', new_callable=AsyncMock) as mock_audit:
            mock_audit.return_value = [{'log_id': 'log1'}]
            
            result = await security_service.get_security_reports('audit', {'user_id': 'user123'})
            
            mock_audit.assert_called_once_with({'user_id': 'user123'})
            assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_batch_security_check(self, security_service):
        """Test batch security check."""
        checks = [
            {'type': 'access', 'user_id': 'user1', 'resource': '/api/data', 'action': 'read'},
            {'type': 'compliance', 'rule': 'gdpr', 'data': {'email': 'test@example.com'}}
        ]
        
        with patch.object(security_service, 'check_access', new_callable=AsyncMock) as mock_access:
            with patch.object(security_service, 'check_compliance', new_callable=AsyncMock) as mock_compliance:
                mock_access.return_value = {'allowed': True}
                mock_compliance.return_value = {'compliant': True}
                
                result = await security_service.batch_security_check(checks)
                
                assert len(result) == 2
                assert result[0]['allowed'] is True
                assert result[1]['compliant'] is True
    
    # Helper methods
    def test_get_cache_status(self, security_service):
        """Test getting cache status."""
        security_service._dev_config_cache = {'test': 'value'}
        security_service._cache_ttl = {'test': datetime.now()}
        
        result = security_service._get_cache_status()
        
        assert 'cache_size' in result
        assert 'cache_hits' in result
        assert 'cache_misses' in result
        assert 'cache_ttl' in result
        assert 'enabled' in result
    
    def test_get_offline_status(self, security_service):
        """Test getting offline status."""
        result = security_service._get_offline_status()
        
        assert 'enabled' in result
        assert 'fallback_enabled' in result
        assert 'grace_period_hours' in result
        assert 'sync_status' in result
    
    @pytest.mark.asyncio
    async def test_get_security_status(self, security_service):
        """Test getting security status."""
        with patch.object(security_service, 'get_security_alerts', new_callable=AsyncMock) as mock_alerts:
            mock_alerts.return_value = [{'event_id': 'alert1'}]
            
            result = await security_service._get_security_status()
            
            assert 'alerts_count' in result
            assert 'violations_count' in result
            assert 'compliance_score' in result
    
    @pytest.mark.asyncio
    async def test_get_last_sync_time(self, security_service):
        """Test getting last sync time."""
        result = await security_service._get_last_sync_time()
        assert result is not None  # Should return current timestamp
    
    # Edge cases and error handling
    @pytest.mark.asyncio
    async def test_create_audit_log_fallback(self, security_service):
        """Test audit log creation with fallback enabled."""
        security_service._dev_config_cache['fallback_enabled'] = True
        
        result = await security_service.create_audit_log('test', 'user123', '/api', 'read')
        
        assert result == {'status': 'fallback', 'message': 'Service unavailable, using fallback'}
    
    @pytest.mark.asyncio
    async def test_encrypt_data_fallback(self, security_service):
        """Test data encryption with fallback enabled."""
        security_service._dev_config_cache['fallback_enabled'] = True
        
        result = await security_service.encrypt_data('test_data')
        
        assert result == {'encrypted_data': 'fallback_encrypted', 'fallback': True}
    
    def test_validate_developer_security_config_missing_keys(self, security_service):
        """Test config validation with missing required keys."""
        security_service._dev_config_cache = {'audit_enabled': True}  # Missing other keys
        
        # This is now an async method, so we need to await it
        import asyncio
        result = asyncio.run(security_service.validate_developer_security_config())
        assert result is False
