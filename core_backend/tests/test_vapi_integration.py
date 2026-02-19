"""
Tests for VAPI Integration

This module contains comprehensive tests for the VAPI voice agent integration,
including agent creation, webhook handling, and analytics.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import json
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Import the modules we're testing
from backend.routes.vapi import (
    router as vapi_router,
    VapiAgentCreate,
    WebhookEvent,
    create_vapi_assistant,
    convert_integration_to_vapi_tool,
    process_vapi_webhook_event
)
from backend.routes.ai_prompt_generator import (
    router as ai_router,
    SystemPromptGenerate,
    analyze_website_content,
    generate_ai_system_prompt,
    AGENT_TEMPLATES
)
from backend.routes.integrations_manager import (
    router as integrations_router,
    Integration,
    IntegrationCreate,
    IntegrationType,
    IntegrationStatus
)


class TestVapiIntegration:
    """Test suite for VAPI integration functionality."""
    
    @pytest.fixture
    def vapi_agent_data(self):
        """Sample VAPI agent creation data."""
        return VapiAgentCreate(
            name="Test Sales Agent",
            description="AI-powered sales assistant for testing",
            agent_type="sales",
            system_prompt="You are a helpful sales assistant.",
            vapi_phone_id="test-phone-123",
            call_type="both",
            voice="alloy",
            language="en",
            speed=1.0,
            integrations=["calendar", "email"],
            custom_tools=[
                {
                    "name": "custom_webhook",
                    "description": "Custom webhook tool",
                    "webhook_url": "https://example.com/webhook"
                }
            ],
            max_duration=600,
            silence_timeout=10,
            interruptible=True,
            record_calls=True,
            webhook_url="https://api.ailabsafrica.com/vapi/webhooks/test/agent-123",
            enable_webhooks=True,
            tenant_id="test-tenant"
        )
    
    @pytest.fixture
    def webhook_event_data(self):
        """Sample webhook event data."""
        return {
            "type": "call-end",
            "call": {
                "id": "call-123",
                "orgId": "org-456",
                "durationSeconds": 145,
                "cost": 2.34,
                "status": "completed"
            },
            "assistant": {
                "id": "assistant-789"
            },
            "customer": {
                "number": "+1234567890"
            }
        }
    
    @pytest.fixture
    def mock_mongodb(self):
        """Mock MongoDB collection operations."""
        mock_collection = AsyncMock()
        mock_collection.insert_one = AsyncMock()
        mock_collection.find_one = AsyncMock()
        mock_collection.update_one = AsyncMock()
        mock_collection.delete_one = AsyncMock()
        mock_collection.aggregate = AsyncMock()
        
        with patch('backend.database.mongodb.get_collection', return_value=mock_collection):
            yield mock_collection
    
    @pytest.mark.asyncio
    async def test_create_vapi_agent_success(self, vapi_agent_data, mock_mongodb):
        """Test successful VAPI agent creation."""
        # Mock VAPI API response
        with patch('backend.routes.vapi.create_vapi_assistant') as mock_create_assistant:
            mock_create_assistant.return_value = {
                "id": "vapi-assistant-123",
                "name": vapi_agent_data.name,
                "status": "active"
            }
            
            # Create test client
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(vapi_router)
            client = TestClient(app)
            
            # Make request
            response = client.post("/vapi/agents", json=vapi_agent_data.dict())
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["agent"]["name"] == vapi_agent_data.name
            assert data["agent"]["agent_type"] == vapi_agent_data.agent_type
            assert data["vapi_assistant_id"] == "vapi-assistant-123"
            assert data["webhook_url"] is not None
            
            # Verify database insertion
            mock_mongodb.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_vapi_agent_missing_name(self):
        """Test VAPI agent creation with missing required fields."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(vapi_router)
        client = TestClient(app)
        
        # Missing name field
        invalid_data = {
            "description": "Test agent",
            "agent_type": "sales",
            "system_prompt": "Test prompt"
        }
        
        response = client.post("/vapi/agents", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_webhook_handling(self, webhook_event_data, mock_mongodb):
        """Test VAPI webhook event handling."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(vapi_router)
        client = TestClient(app)
        
        # Make webhook request
        response = client.post(
            "/vapi/webhooks/test-tenant/agent-123",
            json=webhook_event_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Webhook processed"
    
    @pytest.mark.asyncio
    async def test_get_agent_analytics(self, mock_mongodb):
        """Test fetching agent analytics."""
        # Mock analytics data
        mock_analytics = {
            "_id": None,
            "total_calls": 50,
            "completed_calls": 45,
            "started_calls": 48,
            "total_duration": 7200,
            "total_cost": 25.50
        }
        
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[mock_analytics])
        mock_mongodb.aggregate.return_value = mock_cursor
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(vapi_router)
        client = TestClient(app)
        
        response = client.get("/vapi/agents/test-agent-123/analytics?tenant_id=test-tenant")
        
        assert response.status_code == 200
        data = response.json()
        assert data["calls"]["total"] == 50
        assert data["calls"]["successful"] == 45
        assert data["costs"]["total"] == 25.50
    
    @pytest.mark.asyncio
    async def test_list_agents(self, mock_mongodb):
        """Test listing VAPI agents."""
        # Mock agents data
        mock_agents = [
            {
                "_id": "obj-id-1",
                "id": "agent-1",
                "name": "Test Agent 1",
                "tenant_id": "test-tenant",
                "status": "active",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "_id": "obj-id-2", 
                "id": "agent-2",
                "name": "Test Agent 2",
                "tenant_id": "test-tenant",
                "status": "active",
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        mock_mongodb.count_documents = AsyncMock(return_value=2)
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=mock_agents)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_mongodb.find.return_value = mock_cursor
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(vapi_router)
        client = TestClient(app)
        
        response = client.get("/vapi/agents?tenant_id=test-tenant")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["agents"]) == 2
        assert data["total"] == 2


class TestAIPromptGenerator:
    """Test suite for AI prompt generation functionality."""
    
    @pytest.fixture
    def website_analysis_data(self):
        """Sample website analysis data."""
        return {
            "url": "https://example-company.com",
            "title": "Example Company - Leading Tech Solutions",
            "company_info": {
                "name": "Example Company",
                "description": "We provide cutting-edge technology solutions for businesses.",
                "mission": "To empower businesses with innovative technology"
            },
            "business_type": "technology",
            "services_products": ["Software Development", "Cloud Solutions", "AI Consulting"],
            "contact_info": {
                "email": "contact@example-company.com",
                "phone": "(555) 123-4567"
            },
            "key_content": [
                "Innovative Technology Solutions",
                "Enterprise Software Development",
                "24/7 Customer Support"
            ],
            "tone_style": "professional",
            "target_audience": "business"
        }
    
    @pytest.mark.asyncio
    async def test_analyze_website_content_success(self):
        """Test successful website content analysis."""
        mock_html = """
        <html>
            <head><title>Test Company</title></head>
            <body>
                <h1>Test Company</h1>
                <meta name="description" content="We are a leading software company">
                <div class="about">
                    We provide innovative software solutions for businesses worldwide.
                </div>
                <div class="services">
                    <li>Web Development</li>
                    <li>Mobile Apps</li>
                    <li>Cloud Solutions</li>
                </div>
                <p>Contact us at info@testcompany.com or (555) 123-4567</p>
            </body>
        </html>
        """
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.text = mock_html
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await analyze_website_content("https://testcompany.com")
            
            assert result["title"] == "Test Company"
            assert result["company_info"]["name"] == "Test Company"
            assert "innovative software solutions" in result["company_info"]["description"].lower()
            assert result["contact_info"]["email"] == "info@testcompany.com"
            assert result["contact_info"]["phone"] == "(555) 123-4567"
    
    @pytest.mark.asyncio
    async def test_analyze_website_content_http_error(self):
        """Test website analysis with HTTP error."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.HTTPError("Not found")
            
            with pytest.raises(HTTPException) as exc_info:
                await analyze_website_content("https://nonexistent.com")
            
            assert exc_info.value.status_code == 400
            assert "Unable to fetch website" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_generate_ai_system_prompt_success(self, website_analysis_data):
        """Test AI system prompt generation."""
        mock_openai_response = AsyncMock()
        mock_openai_response.choices = [
            AsyncMock(message=AsyncMock(content="You are a professional sales representative for Example Company..."))
        ]
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
            mock_openai.return_value = mock_client
            
            result = await generate_ai_system_prompt(
                website_analysis=website_analysis_data,
                agent_template=AGENT_TEMPLATES["sales"],
                agent_type="sales",
                language="en",
                company_name="Example Company"
            )
            
            assert isinstance(result, str)
            assert len(result) > 100  # Should be a substantial prompt
            assert "Example Company" in result
            mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_ai_system_prompt_fallback(self, website_analysis_data):
        """Test fallback to template-based generation when AI fails."""
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_openai.side_effect = Exception("API error")
            
            result = await generate_ai_system_prompt(
                website_analysis=website_analysis_data,
                agent_template=AGENT_TEMPLATES["sales"],
                agent_type="sales",
                language="en",
                company_name="Example Company"
            )
            
            assert isinstance(result, str)
            assert "Example Company" in result
            assert "sales representative" in result.lower()
    
    def test_generate_system_prompt_endpoint(self):
        """Test the system prompt generation API endpoint."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(ai_router)
        client = TestClient(app)
        
        request_data = {
            "website_url": "https://example.com",
            "agent_type": "sales",
            "language": "en"
        }
        
        with patch('backend.routes.ai_prompt_generator.analyze_website_content') as mock_analyze:
            with patch('backend.routes.ai_prompt_generator.generate_ai_system_prompt') as mock_generate:
                mock_analyze.return_value = {
                    "company_info": {"name": "Test Co", "description": "Test company"},
                    "business_type": "technology",
                    "tone_style": "professional",
                    "target_audience": "business",
                    "services_products": ["Software"],
                    "contact_info": {}
                }
                mock_generate.return_value = "Generated system prompt"
                
                response = client.post("/ai/generate-system-prompt", json=request_data)
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["system_prompt"] == "Generated system prompt"
                assert data["agent_type"] == "sales"


class TestIntegrationsManager:
    """Test suite for integrations management functionality."""
    
    @pytest.fixture
    def integration_data(self):
        """Sample integration creation data."""
        return IntegrationCreate(
            name="Google Calendar Integration",
            type=IntegrationType.CALENDAR,
            provider="google",
            description="Integration with Google Calendar for appointment scheduling",
            config={
                "calendar_id": "primary",
                "timezone": "UTC",
                "default_duration": 30
            },
            credentials={
                "client_id": "test-client-id",
                "client_secret": "test-client-secret",
                "refresh_token": "test-refresh-token"
            },
            tenant_id="test-tenant"
        )
    
    @pytest.mark.asyncio
    async def test_create_integration_success(self, integration_data, mock_mongodb):
        """Test successful integration creation."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(integrations_router)
        client = TestClient(app)
        
        response = client.post("/integrations/", json=integration_data.dict())
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == integration_data.name
        assert data["type"] == integration_data.type
        assert data["provider"] == integration_data.provider
        assert data["category"] == "Scheduling"
        
        # Verify database insertion
        mock_mongodb.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_integrations(self, mock_mongodb):
        """Test listing integrations."""
        # Mock integrations data
        mock_integrations = [
            {
                "_id": "obj-id-1",
                "id": "integration-1",
                "name": "Google Calendar",
                "type": "calendar",
                "provider": "google",
                "category": "Scheduling",
                "tenant_id": "test-tenant",
                "status": "active",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        ]
        
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=mock_integrations)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_mongodb.find.return_value = mock_cursor
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(integrations_router)
        client = TestClient(app)
        
        response = client.get("/integrations/?tenant_id=test-tenant")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Google Calendar"
        assert data[0]["type"] == "calendar"
    
    @pytest.mark.asyncio
    async def test_test_integration(self, mock_mongodb):
        """Test integration testing functionality."""
        # Mock integration data
        mock_integration = {
            "_id": "obj-id-1",
            "id": "integration-1",
            "name": "Google Calendar",
            "type": "calendar",
            "provider": "google",
            "config": {"calendar_id": "primary"},
            "credentials": {"access_token": "test-token"},
            "tenant_id": "test-tenant",
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_mongodb.find_one.return_value = mock_integration
        mock_mongodb.update_one = AsyncMock()
        
        # Mock HTTP request for calendar test
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(integrations_router)
            client = TestClient(app)
            
            response = client.post("/integrations/integration-1/test", json={"test_data": {}})
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_get_integration_templates(self):
        """Test fetching integration templates."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(integrations_router)
        client = TestClient(app)
        
        response = client.get("/integrations/templates")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "templates" in data
        assert "google_calendar" in data["templates"]
        assert "sendgrid" in data["templates"]


class TestVapiAssistantCreation:
    """Test suite for VAPI assistant creation functionality."""
    
    @pytest.mark.asyncio
    async def test_create_vapi_assistant_success(self):
        """Test successful VAPI assistant creation with API call."""
        config = {
            "name": "Test Assistant",
            "model": {"provider": "openai", "model": "gpt-4"},
            "voice": {"provider": "openai", "voiceId": "alloy"}
        }
        
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "id": "vapi-assistant-123",
            "name": "Test Assistant",
            "status": "active"
        }
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            # Mock environment variable
            with patch.dict('os.environ', {'VAPI_API_KEY': 'test-key'}):
                result = await create_vapi_assistant(config)
                
                assert result["id"] == "vapi-assistant-123"
                assert result["name"] == "Test Assistant"
                assert result["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_create_vapi_assistant_no_api_key(self):
        """Test VAPI assistant creation without API key (fallback to mock)."""
        config = {
            "name": "Test Assistant",
            "model": {"provider": "openai", "model": "gpt-4"}
        }
        
        with patch.dict('os.environ', {}, clear=True):
            result = await create_vapi_assistant(config)
            
            assert "id" in result
            assert result["name"] == "Test Assistant"
            assert result["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_create_vapi_assistant_api_error(self):
        """Test VAPI assistant creation with API error."""
        config = {
            "name": "Test Assistant",
            "model": {"provider": "openai", "model": "gpt-4"}
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.HTTPError("API Error")
            
            with patch.dict('os.environ', {'VAPI_API_KEY': 'test-key'}):
                result = await create_vapi_assistant(config)
                
                # Should return mock response as fallback
                assert "id" in result
                assert result["name"] == "Test Assistant"
                assert result["status"] == "error"


class TestIntegrationConversion:
    """Test suite for converting platform integrations to VAPI tools."""
    
    @pytest.mark.asyncio
    async def test_convert_calendar_integration(self):
        """Test converting calendar integration to VAPI tool."""
        result = await convert_integration_to_vapi_tool("calendar", "test-tenant")
        
        assert result is not None
        assert result["type"] == "function"
        assert result["function"]["name"] == "check_calendar_availability"
        assert "server" in result
        assert "test-tenant" in result["server"]["url"]
    
    @pytest.mark.asyncio
    async def test_convert_email_integration(self):
        """Test converting email integration to VAPI tool."""
        result = await convert_integration_to_vapi_tool("email", "test-tenant")
        
        assert result is not None
        assert result["type"] == "function"
        assert result["function"]["name"] == "send_email"
        assert result["function"]["parameters"]["properties"]["to"]["type"] == "string"
    
    @pytest.mark.asyncio
    async def test_convert_nonexistent_integration(self):
        """Test converting nonexistent integration returns None."""
        result = await convert_integration_to_vapi_tool("nonexistent", "test-tenant")
        assert result is None


class TestWebhookProcessing:
    """Test suite for webhook event processing."""
    
    @pytest.mark.asyncio
    async def test_process_webhook_event_call_end(self, mock_mongodb):
        """Test processing call-end webhook event."""
        event = WebhookEvent(
            event_type="call-end",
            call_id="call-123",
            assistant_id="assistant-456",
            data={
                "call": {
                    "durationSeconds": 180,
                    "cost": 3.25
                }
            }
        )
        
        # Mock collections
        events_collection = AsyncMock()
        analytics_collection = AsyncMock()
        
        def get_collection_side_effect(name):
            if name == "vapi_webhook_events":
                return events_collection
            elif name == "vapi_analytics":
                return analytics_collection
            return AsyncMock()
        
        with patch('backend.database.mongodb.get_collection', side_effect=get_collection_side_effect):
            await process_vapi_webhook_event("test-tenant", "agent-123", event)
            
            # Verify event storage
            events_collection.insert_one.assert_called_once()
            
            # Verify analytics update
            analytics_collection.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_webhook_event_with_tools(self, mock_mongodb):
        """Test processing webhook event with tool calls."""
        event = WebhookEvent(
            event_type="tool-calls",
            call_id="call-123",
            assistant_id="assistant-456",
            data={
                "toolCalls": [
                    {
                        "id": "tool-call-1",
                        "function": {
                            "name": "send_email",
                            "arguments": {"to": "test@example.com", "subject": "Test"}
                        }
                    }
                ]
            }
        )
        
        events_collection = AsyncMock()
        tool_calls_collection = AsyncMock()
        
        def get_collection_side_effect(name):
            if name == "vapi_webhook_events":
                return events_collection
            elif name == "vapi_tool_calls":
                return tool_calls_collection
            return AsyncMock()
        
        with patch('backend.database.mongodb.get_collection', side_effect=get_collection_side_effect):
            await process_vapi_webhook_event("test-tenant", "agent-123", event)
            
            # Verify tool call logging
            tool_calls_collection.insert_one.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])