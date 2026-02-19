import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from ..backend.main import app
from ..backend.models import MCPServer

client = TestClient(app)


def test_create_mcp_server():
    """Test creating an MCP server."""
    server_data = {
        "tenant_id": str(uuid4()),
        "url": "https://example.com/mcp",
        "tool_names": ["crm.createLead", "crm.updateContact"]
    }
    
    response = client.post("/mcp/servers", json=server_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["url"] == server_data["url"]
    assert data["tool_names"] == server_data["tool_names"]
    assert data["status"] == "active"


def test_list_mcp_servers():
    """Test listing MCP servers."""
    response = client.get("/mcp/servers")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_mcp_server():
    """Test getting a specific MCP server."""
    # First create a server
    server_data = {
        "tenant_id": str(uuid4()),
        "url": "https://example.com/mcp",
        "tool_names": ["crm.createLead"]
    }
    
    create_response = client.post("/mcp/servers", json=server_data)
    server_id = create_response.json()["id"]
    
    # Then get it
    response = client.get(f"/mcp/servers/{server_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == server_id
    assert data["url"] == server_data["url"]


def test_delete_mcp_server():
    """Test deleting an MCP server."""
    # First create a server
    server_data = {
        "tenant_id": str(uuid4()),
        "url": "https://example.com/mcp",
        "tool_names": ["crm.createLead"]
    }
    
    create_response = client.post("/mcp/servers", json=server_data)
    server_id = create_response.json()["id"]
    
    # Then delete it
    response = client.delete(f"/mcp/servers/{server_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    
    # Verify it's gone
    get_response = client.get(f"/mcp/servers/{server_id}")
    assert get_response.status_code == 404


def test_call_mcp_tool():
    """Test calling a tool on an MCP server."""
    # First create a server
    server_data = {
        "tenant_id": str(uuid4()),
        "url": "https://example.com/mcp",
        "tool_names": ["crm.createLead"]
    }
    
    create_response = client.post("/mcp/servers", json=server_data)
    server_id = create_response.json()["id"]
    
    # Then call a tool
    tool_params = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890"
    }
    
    response = client.post(
        "/mcp/call",
        params={"server_id": server_id, "tool_name": "crm.createLead"},
        json=tool_params
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "result" in data
    assert data["result"]["server_id"] == str(server_id)
    assert data["result"]["tool_name"] == "crm.createLead"


def test_call_mcp_tool_nonexistent_server():
    """Test calling a tool on a server that doesn't exist."""
    tool_params = {"name": "John Doe"}
    
    response = client.post(
        "/mcp/call",
        params={"server_id": str(uuid4()), "tool_name": "crm.createLead"},
        json=tool_params
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "MCP server not found"


def test_get_nonexistent_mcp_server():
    """Test getting an MCP server that doesn't exist."""
    response = client.get(f"/mcp/servers/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "MCP server not found"


def test_delete_nonexistent_mcp_server():
    """Test deleting an MCP server that doesn't exist."""
    response = client.delete(f"/mcp/servers/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "MCP server not found" 