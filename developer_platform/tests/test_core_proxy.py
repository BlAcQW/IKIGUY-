"""
Unit tests for Core Backend proxy functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException
import httpx

from ..core_proxy import CoreBackendProxy
from ..security import MTLSClient


class TestCoreBackendProxy:
    """Test Core Backend proxy functionality."""
    
    @pytest.fixture
    def proxy(self):
        """Create a test proxy instance."""
        return CoreBackendProxy(
            core_url="https://core.example.com",
            cert_path="/path/to/cert.crt",
            key_path="/path/to/key.key",
            ca_path="/path/to/ca.crt"
        )
        
    @pytest.fixture
    def tenant_id(self):
        """Create a test tenant ID."""
        return uuid4()
        
    @pytest.fixture
    def assistant_data(self):
        """Create test assistant data."""
        return {
            "name": "Test Assistant",
            "type": "sales",
            "languages": ["en"],
            "voice_pace": "normal",
            "guardrails": {
                "consent": True,
                "grounding": True
            }
        }
        
    @pytest.fixture
    def campaign_data(self):
        """Create test campaign data."""
        return {
            "name": "Test Campaign",
            "assistant_id": str(uuid4()),
            "goal": "sales",
            "audience": {"size": 1000},
            "schedule": {"start_time": "2024-01-01T00:00:00Z"}
        }
        
    @pytest.mark.asyncio
    async def test_validate_assistant_data_valid(self, proxy, assistant_data):
        """Test assistant data validation with valid data."""
        result = proxy._validate_assistant_data(assistant_data)
        
        assert result["name"] == "Test Assistant"
        assert result["type"] == "sales"
        assert result["languages"] == ["en"]
        assert result["voice_pace"] == "normal"
        assert result["guardrails"]["consent"] is True
        
    @pytest.mark.asyncio
    async def test_validate_assistant_data_missing_field(self, proxy):
        """Test assistant data validation with missing required field."""
        invalid_data = {
            "name": "Test Assistant",
            "type": "sales"
            # Missing languages field
        }
        
        with pytest.raises(HTTPException) as exc_info:
            proxy._validate_assistant_data(invalid_data)
            
        assert exc_info.value.status_code == 400
        assert "Missing required field: languages" in str(exc_info.value.detail)
        
    @pytest.mark.asyncio
    async def test_validate_assistant_data_invalid_guardrail(self, proxy):
        """Test assistant data validation with invalid guardrail."""
        invalid_data = {
            "name": "Test Assistant",
            "type": "sales",
            "languages": ["en"],
            "guardrails": {
                "invalid_guardrail": True
            }
        }
        
        with pytest.raises(HTTPException) as exc_info:
            proxy._validate_assistant_data(invalid_data)
            
        assert exc_info.value.status_code == 400
        assert "Invalid guardrail: invalid_guardrail" in str(exc_info.value.detail)
        
    @pytest.mark.asyncio
    async def test_validate_campaign_data_valid(self, proxy, campaign_data):
        """Test campaign data validation with valid data."""
        result = proxy._validate_campaign_data(campaign_data)
        
        assert result["name"] == "Test Campaign"
        assert result["goal"] == "sales"
        assert "audience" in result
        assert "schedule" in result
        
    @pytest.mark.asyncio
    async def test_validate_campaign_data_missing_field(self, proxy):
        """Test campaign data validation with missing required field."""
        invalid_data = {
            "name": "Test Campaign",
            "assistant_id": str(uuid4())
            # Missing goal field
        }
        
        with pytest.raises(HTTPException) as exc_info:
            proxy._validate_campaign_data(invalid_data)
            
        assert exc_info.value.status_code == 400
        assert "Missing required field: goal" in str(exc_info.value.detail)
        
    @pytest.mark.asyncio
    async def test_validate_campaign_data_invalid_goal(self, proxy):
        """Test campaign data validation with invalid goal."""
        invalid_data = {
            "name": "Test Campaign",
            "assistant_id": str(uuid4()),
            "goal": "invalid_goal"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            proxy._validate_campaign_data(invalid_data)
            
        assert exc_info.value.status_code == 400
        assert "Invalid goal: invalid_goal" in str(exc_info.value.detail)
        
    @pytest.mark.asyncio
    async def test_map_core_error_400(self, proxy):
        """Test error mapping for 400 status code."""
        error = proxy._map_core_error(400, "Bad request")
        
        assert isinstance(error, HTTPException)
        assert error.status_code == 400
        assert "Invalid request: Bad request" in str(error.detail)
        
    @pytest.mark.asyncio
    async def test_map_core_error_401(self, proxy):
        """Test error mapping for 401 status code."""
        error = proxy._map_core_error(401, "Unauthorized")
        
        assert isinstance(error, HTTPException)
        assert error.status_code == 401
        assert "Authentication failed" in str(error.detail)
        
    @pytest.mark.asyncio
    async def test_map_core_error_403(self, proxy):
        """Test error mapping for 403 status code."""
        error = proxy._map_core_error(403, "Forbidden")
        
        assert isinstance(error, HTTPException)
        assert error.status_code == 403
        assert "Insufficient permissions" in str(error.detail)
        
    @pytest.mark.asyncio
    async def test_map_core_error_404(self, proxy):
        """Test error mapping for 404 status code."""
        error = proxy._map_core_error(404, "Not found")
        
        assert isinstance(error, HTTPException)
        assert error.status_code == 404
        assert "Resource not found" in str(error.detail)
        
    @pytest.mark.asyncio
    async def test_map_core_error_500(self, proxy):
        """Test error mapping for 500 status code."""
        error = proxy._map_core_error(500, "Internal server error")
        
        assert isinstance(error, HTTPException)
        assert error.status_code == 503
        assert "Core Backend service unavailable" in str(error.detail)
        
    @pytest.mark.asyncio
    async def test_create_assistant_success(self, proxy, tenant_id, assistant_data):
        """Test successful assistant creation."""
        # Mock the mTLS client
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = {"id": str(uuid4()), "name": "Test Assistant"}
        mock_client.request.return_value = mock_response
        
        with patch.object(proxy, '_get_mtls_client', return_value=mock_client):
            with patch.object(proxy, '_create_auth_headers', return_value={"Authorization": "Bearer token"}):
                result = await proxy.create_assistant(tenant_id, assistant_data)
                
        assert result["name"] == "Test Assistant"
        mock_client.request.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_create_assistant_http_error(self, proxy, tenant_id, assistant_data):
        """Test assistant creation with HTTP error."""
        # Mock the mTLS client to raise HTTP error
        mock_client = AsyncMock()
        mock_client.request.side_effect = httpx.HTTPStatusError(
            "400 Bad Request",
            request=MagicMock(),
            response=MagicMock(status_code=400, text="Invalid data")
        )
        
        with patch.object(proxy, '_get_mtls_client', return_value=mock_client):
            with patch.object(proxy, '_create_auth_headers', return_value={"Authorization": "Bearer token"}):
                with pytest.raises(HTTPException) as exc_info:
                    await proxy.create_assistant(tenant_id, assistant_data)
                    
        assert exc_info.value.status_code == 400
        assert "Invalid request: Invalid data" in str(exc_info.value.detail)
        
    @pytest.mark.asyncio
    async def test_list_assistants_success(self, proxy, tenant_id):
        """Test successful assistant listing."""
        # Mock the mTLS client
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = [
            {"id": str(uuid4()), "name": "Assistant 1"},
            {"id": str(uuid4()), "name": "Assistant 2"}
        ]
        mock_client.request.return_value = mock_response
        
        with patch.object(proxy, '_get_mtls_client', return_value=mock_client):
            with patch.object(proxy, '_create_auth_headers', return_value={"Authorization": "Bearer token"}):
                result = await proxy.list_assistants(tenant_id)
                
        assert len(result) == 2
        assert result[0]["name"] == "Assistant 1"
        assert result[1]["name"] == "Assistant 2"
        
    @pytest.mark.asyncio
    async def test_campaign_action_invalid_action(self, proxy, tenant_id):
        """Test campaign action with invalid action."""
        campaign_id = uuid4()
        
        with pytest.raises(HTTPException) as exc_info:
            await proxy.campaign_action(tenant_id, campaign_id, "invalid_action")
            
        assert exc_info.value.status_code == 400
        assert "Invalid action: invalid_action" in str(exc_info.value.detail)
        
    @pytest.mark.asyncio
    async def test_campaign_action_success(self, proxy, tenant_id):
        """Test successful campaign action."""
        campaign_id = uuid4()
        
        # Mock the mTLS client
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = {"status": "started", "campaign_id": str(campaign_id)}
        mock_client.request.return_value = mock_response
        
        with patch.object(proxy, '_get_mtls_client', return_value=mock_client):
            with patch.object(proxy, '_create_auth_headers', return_value={"Authorization": "Bearer token"}):
                result = await proxy.campaign_action(tenant_id, campaign_id, "start")
                
        assert result["status"] == "started"
        assert result["campaign_id"] == str(campaign_id)


class TestMTLSClient:
    """Test mTLS client functionality."""
    
    @pytest.fixture
    def client(self):
        """Create a test mTLS client."""
        return MTLSClient(
            core_url="https://core.example.com",
            cert_path="/path/to/cert.crt",
            key_path="/path/to/key.key",
            ca_path="/path/to/ca.crt"
        )
        
    @pytest.mark.asyncio
    async def test_request_success(self, client):
        """Test successful request."""
        # Mock httpx.AsyncClient
        mock_httpx_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_httpx_client.request.return_value = mock_response
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            with patch.object(client, '_create_client'):
                client._client = mock_httpx_client
                response = await client.request("GET", "/test", headers={"Test": "header"})
                
        assert response.json() == {"status": "ok"}
        mock_httpx_client.request.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_request_http_error(self, client):
        """Test request with HTTP error."""
        # Mock httpx.AsyncClient to raise HTTP error
        mock_httpx_client = AsyncMock()
        mock_httpx_client.request.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404, text="Not found")
        )
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            with patch.object(client, '_create_client'):
                client._client = mock_httpx_client
                with pytest.raises(httpx.HTTPStatusError):
                    await client.request("GET", "/test")
                    
    @pytest.mark.asyncio
    async def test_request_connection_error(self, client):
        """Test request with connection error."""
        # Mock httpx.AsyncClient to raise connection error
        mock_httpx_client = AsyncMock()
        mock_httpx_client.request.side_effect = httpx.RequestError("Connection failed")
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            with patch.object(client, '_create_client'):
                client._client = mock_httpx_client
                with pytest.raises(httpx.RequestError):
                    await client.request("GET", "/test") 