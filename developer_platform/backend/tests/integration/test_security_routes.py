"""
Integration tests for Security routes.

Tests the security-related API endpoints using the DeveloperSecurityService.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json

from main import app

client = TestClient(app)

class TestSecurityRoutes:
    """Test cases for Security routes."""
    
    @pytest.fixture
    def mock_api_key(self):
        """Mock API key for testing."""
        return "test_api_key_123"
    
    def test_create_audit_log_success(self, mock_api_key):
        """Test successful audit log creation."""
        with patch('routes.security_routes.security_service.create_audit_log', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {"log_id": "log_123", "status": "created"}
            
            response = client.post(
                "/v1/security/audit/log",
                headers={"x-api-key": mock_api_key},
                json={
                    "event_type": "user_login",
                    "user_id": "user_123",
                    "resource": "/api/data",
                    "action": "read"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["log_id"] == "log_123"
    
    def test_get_audit_logs_success(self, mock_api_key):
        """Test successful audit logs retrieval."""
        with patch('routes.security_routes.security_service.get_audit_logs', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [{"log_id": "log_1"}, {"log_id": "log_2"}]
            
            response = client.get(
                "/v1/security/audit/logs",
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 2
    
    def test_check_access_success(self, mock_api_key):
        """Test successful access check."""
        with patch('routes.security_routes.security_service.check_access', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = {"allowed": True, "reason": "authorized"}
            
            response = client.post(
                "/v1/security/access/check",
                headers={"x-api-key": mock_api_key},
                json={
                    "user_id": "user_123",
                    "resource": "/api/data",
                    "action": "read"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["allowed"] is True
    
    def test_encrypt_data_success(self, mock_api_key):
        """Test successful data encryption."""
        with patch('routes.security_routes.security_service.encrypt_data', new_callable=AsyncMock) as mock_encrypt:
            mock_encrypt.return_value = {"encrypted_data": "encrypted_text", "key_id": "key_123"}
            
            response = client.post(
                "/v1/security/encrypt",
                headers={"x-api-key": mock_api_key},
                json={
                    "data": "sensitive_data",
                    "algorithm": "AES-256"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["encrypted_data"] == "encrypted_text"
    
    def test_decrypt_data_success(self, mock_api_key):
        """Test successful data decryption."""
        with patch('routes.security_routes.security_service.decrypt_data', new_callable=AsyncMock) as mock_decrypt:
            mock_decrypt.return_value = {"decrypted_data": "original_data", "key_id": "key_123"}
            
            response = client.post(
                "/v1/security/decrypt",
                headers={"x-api-key": mock_api_key},
                json={
                    "encrypted_data": "encrypted_text",
                    "key_id": "key_123"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["decrypted_data"] == "original_data"
    
    def test_get_security_config_success(self, mock_api_key):
        """Test successful security config retrieval."""
        with patch('routes.security_routes.security_service.get_developer_security_config', new_callable=AsyncMock) as mock_config:
            mock_config.return_value = {"security_enabled": True, "audit_enabled": True}
            
            response = client.get(
                "/v1/security/config",
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["security_enabled"] is True
