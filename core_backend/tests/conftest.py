"""
Pytest configuration for Core Backend tests.

This file provides standardized fixtures used across multiple test files,
reducing duplication and ensuring consistency in test data.
"""

import pytest
import asyncio
import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any
import mongomock
from dotenv import load_dotenv

from backend.models import ServiceAccount, Assistant, AssistantCreate
from backend.services import service_account_service

# Load environment variables from .env for integration tests
env_path = Path("/opt/kasaai/.env")
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from {env_path}")
else:
    print(f"⚠️ .env not found at {env_path}")


@pytest.fixture(autouse=True)
def mock_mcp_manager():
    """Mock the MCP manager to prevent initialization errors in tests."""
    try:
        with patch('apps.core_backend.backend.mcp.get_mcp_manager') as mock_get:
            # Create a mock MCP manager
            mock_manager = Mock()
            mock_manager.client = Mock()

            # Mock the call_tool method
            async def mock_call_tool(server_id, tool_name, params, tenant_id):
                return {"status": "success", "data": {"id": "mock-id"}}

            mock_manager.client.call_tool = mock_call_tool

            # Mock the MCP manager methods
            async def mock_create_crm_lead(tenant_id, lead_data):
                return {"status": "success", "lead_id": "mock-lead-id"}

            async def mock_update_crm_contact(tenant_id, contact_id, contact_data):
                return {"status": "success", "contact_id": contact_id}

            async def mock_create_helpdesk_ticket(tenant_id, ticket_data):
                return {"status": "success", "ticket_id": "mock-ticket-id"}

            async def mock_process_payment(tenant_id, payment_data):
                return {"status": "success", "payment_id": "mock-payment-id"}

            mock_manager.create_crm_lead = mock_create_crm_lead
            mock_manager.update_crm_contact = mock_update_crm_contact
            mock_manager.create_helpdesk_ticket = mock_create_helpdesk_ticket
            mock_manager.process_payment = mock_process_payment

            mock_get.return_value = mock_manager
            yield mock_manager
    except (ImportError, ModuleNotFoundError):
        # MCP module doesn't exist or can't be imported - skip mocking
        yield None


@pytest.fixture(autouse=True)
def mock_init_mcp_manager():
    """Mock the MCP manager initialization."""
    try:
        with patch('apps.core_backend.backend.mcp.init_mcp_manager') as mock_init:
            yield mock_init
    except (ImportError, ModuleNotFoundError):
        # MCP module doesn't exist or can't be imported - skip mocking
        yield None


@pytest.fixture(autouse=True)
def mock_conversation_manager_task():
    """Mock the ConversationManager async task creation."""
    try:
        with patch('asyncio.create_task') as mock_create_task:
            # Return a mock task that does nothing
            mock_task = AsyncMock()
            mock_create_task.return_value = mock_task
            yield mock_create_task
    except Exception:
        # If patching fails, continue anyway
        yield None


@pytest.fixture
def sample_tenant_id():
    """Sample tenant ID for testing."""
    from uuid import uuid4
    return uuid4()


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    from uuid import uuid4
    return uuid4()


@pytest.fixture
def sample_campaign_data():
    """Sample campaign data for testing."""
    return {
        "name": "Test Campaign",
        "description": "A test campaign",
        "target_audience": "test_audience",
        "budget": 1000.0,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }


@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "company": "Test Company"
    }


@pytest.fixture
def sample_payment_data():
    """Sample payment data for testing."""
    return {
        "amount": 100.0,
        "currency": "USD",
        "method": "credit_card",
        "card_number": "4111111111111111",
        "expiry": "12/25",
        "cvv": "123"
    }


# ========== Additional Standardized Test Fixtures ==========

@pytest.fixture(autouse=True)
def mock_secure_environment_variables(monkeypatch, request):
    """Mock secure environment variables for testing.

    Skips mocking for integration tests (marked with @pytest.mark.integration).
    """
    # Skip mocking for integration tests
    if "integration" in request.keywords:
        return

    secure_test_env_vars = {
        "OPENAI_API_KEY": "test-openai-key-123456789",
        "ANTHROPIC_API_KEY": "test-anthropic-key-123456789",
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_ANON_KEY": "test-supabase-anon-key",
        "MONGODB_URL": os.getenv("MONGODB_URL", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin"),
        "MONGO_CORE_DATABASE": "kasaai_core",
        "VAPI_API_KEY": "test-vapi-key-123456789",
        "VAPI_US_PHONE_ID": "test-vapi-phone-id",
        "RESEND_API_KEY": "test-resend-key",
        "HUBSPOT_ACCESS_TOKEN": "test-hubspot-token",
        "STRIPE_SECRET_KEY": "test-stripe-key",
        "VONAGE_API_KEY": "test-vonage-key",
        "VONAGE_API_SECRET": "test-vonage-secret",
        "FIRECRAWL_API_KEY": "test-firecrawl-key",
        "TAVILY_API_KEY": "test-tavily-key",
        "CORE_DB_URL": "sqlite:///:memory:",
        "API_DEPLOY_KEY": "test-deploy-key-123456789"
    }

    for key, value in secure_test_env_vars.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB collection operations."""
    mock_collection = AsyncMock()
    mock_collection.insert_one = AsyncMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.update_one = AsyncMock()
    mock_collection.delete_one = AsyncMock()
    mock_collection.aggregate = AsyncMock()
    mock_collection.count_documents = AsyncMock(return_value=0)

    # Mock cursor for find operations
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[])
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_collection.find.return_value = mock_cursor

    return mock_collection


@pytest.fixture
def auth_header() -> dict[str, str]:
    """Create authentication header for testing."""
    return {"X-Service-Token": "test-service-token-123456789"}


@pytest.fixture
def sample_assistant():
    """Create sample assistant for testing."""
    return {
        "id": str(uuid4()),
        "name": "Test Assistant",
        "description": "A test assistant for unit testing",
        "user_id": "test-user-123",
        "template_id": "blank",
        "llm_provider": "openai",
        "llm_model": "gpt-4",
        "tts_provider": "openai",
        "tts_voice": "alloy",
        "stt_provider": "openai",
        "stt_model": "whisper-1",
        "language": "en",
        "system_prompt": "You are a helpful test assistant.",
        "first_message": "Hello! I'm your test assistant.",
        "status": "draft"
    }


@pytest.fixture
def sample_vapi_agent_data():
    """Sample VAPI agent creation data."""
    return {
        "name": "Test Healthcare Agent",
        "description": "AI-powered healthcare assistant for testing",
        "agent_type": "healthcare",
        "system_prompt": "You are a helpful healthcare assistant.",
        "vapi_phone_id": "test-phone-123",
        "call_type": "both",
        "voice": "alloy",
        "language": "en",
        "speed": 1.0,
        "integrations": ["calendar", "email"],
        "custom_tools": [
            {
                "name": "search_providers",
                "description": "Search for healthcare providers",
                "endpoint": "https://api.example.com/providers/search",
                "method": "POST"
            }
        ],
        "max_duration": 600,
        "silence_timeout": 10,
        "interruptible": True,
        "record_calls": True,
        "webhook_url": "https://api.ailabsafrica.com/vapi/webhooks/test/agent-123",
        "enable_webhooks": True,
        "tenant_id": "test-tenant"
    }


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for testing external API calls."""
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True}
    mock_response.text = '{"success": true}'
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.raise_for_status = MagicMock()

    mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
    mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
    mock_client.return_value.__aenter__.return_value.put.return_value = mock_response
    mock_client.return_value.__aenter__.return_value.delete.return_value = mock_response

    return mock_client


@pytest.fixture
def phone_numbers():
    """Common phone numbers for testing."""
    return {
        "us": "+1234567890",
        "uk": "+441234567890",
        "ghana": "+233244123456",
        "invalid": "invalid-phone"
    }


@pytest.fixture
def email_addresses():
    """Common email addresses for testing."""
    return {
        "valid": "test@example.com",
        "invalid": "invalid-email",
        "admin": "admin@test.com",
        "user": "user@test.com"
    }


# ========== Pytest Configuration ==========

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "vapi: marks tests related to VAPI functionality"
    )
    config.addinivalue_line(
        "markers", "database: marks tests that require database access"
    ) 