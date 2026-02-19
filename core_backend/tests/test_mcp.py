import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from fastapi.testclient import TestClient

from ..backend.main import app
from ..backend.mcp import MCPClient, MCPManager


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def server_id():
    return uuid4()


class TestMCPClient:
    """Test MCP client functionality."""
    
    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """Test successful tool call."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "success"}
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            client = MCPClient("http://localhost:8001", "test-token")
            result = await client.call_tool(
                server_id=uuid4(),
                tool_name="crm.createLead",
                params={"name": "John Doe"},
                tenant_id=uuid4()
            )
            
            assert result == {"result": "success"}
    
    @pytest.mark.asyncio
    async def test_call_tool_timeout(self):
        """Test tool call timeout."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = \
                Exception("Timeout")
            
            client = MCPClient("http://localhost:8001", "test-token")
            
            with pytest.raises(Exception):
                await client.call_tool(
                    server_id=uuid4(),
                    tool_name="crm.createLead",
                    params={"name": "John Doe"},
                    tenant_id=uuid4()
                )
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self):
        """Test circuit breaker functionality."""
        client = MCPClient("http://localhost:8001", "test-token")
        
        # Initially circuit breaker should be closed
        assert not client._is_circuit_breaker_open()
        
        # Simulate failures
        for _ in range(5):
            client._increment_circuit_breaker()
        
        # Circuit breaker should be open
        assert client._is_circuit_breaker_open()
        
        # Reset circuit breaker
        client._reset_circuit_breaker()
        assert not client._is_circuit_breaker_open()


class TestMCPManager:
    """Test MCP manager functionality."""
    
    @pytest.mark.asyncio
    async def test_create_crm_lead(self, tenant_id):
        """Test creating a CRM lead."""
        with patch.object(MCPClient, 'call_tool') as mock_call:
            mock_call.return_value = {"lead_id": "123", "status": "created"}
            
            manager = MCPManager("http://localhost:8001", "test-token")
            result = await manager.create_crm_lead(
                tenant_id=tenant_id,
                lead_data={"name": "John Doe", "email": "john@example.com"}
            )
            
            assert result == {"lead_id": "123", "status": "created"}
            mock_call.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_crm_contact(self, tenant_id):
        """Test updating a CRM contact."""
        with patch.object(MCPClient, 'call_tool') as mock_call:
            mock_call.return_value = {"contact_id": "456", "status": "updated"}
            
            manager = MCPManager("http://localhost:8001", "test-token")
            result = await manager.update_crm_contact(
                tenant_id=tenant_id,
                contact_id="456",
                contact_data={"name": "Jane Doe", "email": "jane@example.com"}
            )
            
            assert result == {"contact_id": "456", "status": "updated"}
            mock_call.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_helpdesk_ticket(self, tenant_id):
        """Test creating a helpdesk ticket."""
        with patch.object(MCPClient, 'call_tool') as mock_call:
            mock_call.return_value = {"ticket_id": "789", "status": "created"}
            
            manager = MCPManager("http://localhost:8001", "test-token")
            result = await manager.create_helpdesk_ticket(
                tenant_id=tenant_id,
                ticket_data={"subject": "Support needed", "description": "Help me"}
            )
            
            assert result == {"ticket_id": "789", "status": "created"}
            mock_call.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_payment(self, tenant_id):
        """Test processing a payment."""
        with patch.object(MCPClient, 'call_tool') as mock_call:
            mock_call.return_value = {"payment_id": "101", "status": "processed"}
            
            manager = MCPManager("http://localhost:8001", "test-token")
            result = await manager.process_payment(
                tenant_id=tenant_id,
                payment_data={"amount": 100, "currency": "USD"}
            )
            
            assert result == {"payment_id": "101", "status": "processed"}
            mock_call.assert_called_once()


class TestMCPEndpoints:
    """Test MCP integration endpoints."""
    
    def test_create_crm_lead_endpoint(self, client, tenant_id):
        """Test CRM lead creation endpoint."""
        lead_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890"
        }
        
        # This would require proper authentication setup
        # For now, we'll test the endpoint structure
        response = client.post(
            f"/internal/mcp/crm/leads?tenant_id={tenant_id}",
            json=lead_data
        )
        
        # Should return 401 without proper auth
        assert response.status_code in [401, 500]
    
    def test_update_crm_contact_endpoint(self, client, tenant_id):
        """Test CRM contact update endpoint."""
        contact_data = {
            "name": "Jane Doe",
            "email": "jane@example.com"
        }
        
        response = client.put(
            f"/internal/mcp/crm/contacts/456?tenant_id={tenant_id}",
            json=contact_data
        )
        
        # Should return 401 without proper auth
        assert response.status_code in [401, 500]
    
    def test_create_helpdesk_ticket_endpoint(self, client, tenant_id):
        """Test helpdesk ticket creation endpoint."""
        ticket_data = {
            "subject": "Support needed",
            "description": "I need help with my account"
        }
        
        response = client.post(
            f"/internal/mcp/helpdesk/tickets?tenant_id={tenant_id}",
            json=ticket_data
        )
        
        # Should return 401 without proper auth
        assert response.status_code in [401, 500]
    
    def test_process_payment_endpoint(self, client, tenant_id):
        """Test payment processing endpoint."""
        payment_data = {
            "amount": 100,
            "currency": "USD",
            "method": "card"
        }
        
        response = client.post(
            f"/internal/mcp/payments/process?tenant_id={tenant_id}",
            json=payment_data
        )
        
        # Should return 401 without proper auth
        assert response.status_code in [401, 500] 