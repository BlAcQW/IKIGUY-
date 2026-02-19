import pathlib
import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open
from pathlib import Path
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

os.environ["CORE_DB_URL"] = "sqlite:///:memory:"
from backend.main import app
from backend.models import DemoDeployRequest


client = TestClient(app)


@pytest.fixture()
def auth_header(monkeypatch) -> dict[str, str]:
    """Create authentication header for testing."""
    # Set a test API deploy key (not a real key)
    test_key = "sk_test_deploy_key_123456789"
    monkeypatch.setenv("API_DEPLOY_KEY", test_key)

    return {"Authorization": f"Bearer {test_key}"}


class TestDemoDeploy:
    """Test cases for the demo deployment endpoint."""
    
    def test_deploy_demo_success(self, auth_header):
        """Test successful demo deployment."""
        payload = {
            "fileName": "asst_abc123-1703123456789.html",
            "html": "<!DOCTYPE html><html><body><h1>Hello World</h1></body></html>",
            "demoId": "asst_abc123-1703123456789",
            "assistantName": "Customer Support Bot",
            "assistantType": "customer_support"
        }
        
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('pathlib.Path.mkdir') as mock_mkdir:
            
            response = client.post("/deploy-demo", json=payload, headers=auth_header)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["demoUrl"] == "https://ailabsafrica.com/demos/asst_abc123-1703123456789.html"
            assert data["filePath"] == "/var/www/ailabsafrica/demos/asst_abc123-1703123456789.html"
            
            # Verify the file was opened for writing
            mock_file.assert_called_once()
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    def test_deploy_demo_invalid_filename(self, auth_header):
        """Test deployment with invalid filename."""
        payload = {
            "fileName": "../malicious.html",
            "html": "<html><body><h1>Malicious</h1></body></html>",
            "demoId": "malicious-demo",
            "assistantName": "Malicious Bot",
            "assistantType": "malicious"
        }
        
        response = client.post("/deploy-demo", json=payload, headers=auth_header)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Invalid filename"
    
    def test_deploy_demo_filename_with_slash(self, auth_header):
        """Test deployment with filename containing slash."""
        payload = {
            "fileName": "folder/file.html",
            "html": "<html><body><h1>Test</h1></body></html>",
            "demoId": "folder-demo",
            "assistantName": "Folder Bot",
            "assistantType": "folder"
        }
        
        response = client.post("/deploy-demo", json=payload, headers=auth_header)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Invalid filename"
    
    def test_deploy_demo_permission_error(self, auth_header):
        """Test deployment with permission error."""
        payload = {
            "fileName": "demo-123.html",
            "html": "<html><body><h1>Hello World</h1></body></html>",
            "demoId": "demo-123",
            "assistantName": "Demo Bot",
            "assistantType": "demo"
        }
        
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            response = client.post("/deploy-demo", json=payload, headers=auth_header)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert data["error"] == "Failed to create file: Permission denied"
    
    def test_deploy_demo_missing_fields(self, auth_header):
        """Test deployment with missing required fields."""
        payload = {
            "fileName": "demo-123.html"
            # Missing html field
        }
        
        response = client.post("/deploy-demo", json=payload, headers=auth_header)
        
        assert response.status_code == 422  # Validation error
    
    def test_deploy_demo_empty_html(self, auth_header):
        """Test deployment with empty HTML content."""
        payload = {
            "fileName": "demo-123.html",
            "html": "",
            "demoId": "demo-123",
            "assistantName": "Empty Bot",
            "assistantType": "empty"
        }
        
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('pathlib.Path.mkdir'):
            
            response = client.post("/deploy-demo", json=payload, headers=auth_header)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            # Verify the file was opened for writing (even with empty content)
            mock_file.assert_called_once()
    
    def test_deploy_demo_large_html(self, auth_header):
        """Test deployment with large HTML content."""
        large_html = "<html><body>" + "<p>Large content</p>" * 1000 + "</body></html>"
        payload = {
            "fileName": "large-demo.html",
            "html": large_html,
            "demoId": "large-demo",
            "assistantName": "Large Bot",
            "assistantType": "large"
        }
        
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('pathlib.Path.mkdir'):
            
            response = client.post("/deploy-demo", json=payload, headers=auth_header)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            # Verify the file was opened for writing
            mock_file.assert_called_once()
    
    def test_deploy_demo_special_characters(self, auth_header):
        """Test deployment with special characters in filename."""
        payload = {
            "fileName": "demo-123_@#$%.html",
            "html": "<html><body><h1>Special chars</h1></body></html>",
            "demoId": "special-demo",
            "assistantName": "Special Bot",
            "assistantType": "special"
        }
        
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('pathlib.Path.mkdir'):
            
            response = client.post("/deploy-demo", json=payload, headers=auth_header)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["demoUrl"] == "https://ailabsafrica.com/demos/demo-123_@#$%.html"
    
    def test_deploy_demo_invalid_auth(self):
        """Test deployment with invalid authentication."""
        payload = {
            "fileName": "demo-123.html",
            "html": "<html><body><h1>Hello World</h1></body></html>",
            "demoId": "demo-123",
            "assistantName": "Demo Bot",
            "assistantType": "demo"
        }
        
        response = client.post("/deploy-demo", json=payload, headers={"Authorization": "Bearer invalid-key"})
        
        assert response.status_code == 401
        assert "Invalid API deploy key" in response.json()["detail"]
    
    def test_deploy_demo_missing_auth(self):
        """Test deployment without authentication."""
        payload = {
            "fileName": "demo-123.html",
            "html": "<html><body><h1>Hello World</h1></body></html>",
            "demoId": "demo-123",
            "assistantName": "Demo Bot",
            "assistantType": "demo"
        }
        
        response = client.post("/deploy-demo", json=payload)
        
        assert response.status_code == 422  # Missing required header
