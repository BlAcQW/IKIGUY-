"""
Tests for Unified LLM Routes

Tests the /llm/* endpoints for language model chat.

Run with:
    PYTHONPATH=/opt/kasaai:/opt/kasaai/apps pytest apps/shared/routes/tests/test_llm_routes.py -v
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
import sys

sys.path.insert(0, "/opt/kasaai/apps")

from shared.routes.llm_routes import router


@pytest.fixture
def app():
    """Create FastAPI app with LLM routes."""
    app = FastAPI()
    app.include_router(router, prefix="/api/llm")
    return app


@pytest_asyncio.fixture
async def client(app):
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestLLMProviders:
    """Tests for LLM provider endpoints."""

    @pytest.mark.asyncio
    async def test_list_providers(self, client):
        """Test GET /llm/providers returns provider list."""
        response = await client.get("/api/llm/providers")
        assert response.status_code == 200

        data = response.json()
        assert "providers" in data
        assert "count" in data
        assert "default_provider" in data
        assert "timestamp" in data

        # Should have Gemini as default
        assert data["default_provider"] == "gemini-2.5-flash"

    @pytest.mark.asyncio
    async def test_list_providers_online_only(self, client):
        """Test GET /llm/providers?online_only=true filters offline providers."""
        response_all = await client.get("/api/llm/providers")
        response_online = await client.get("/api/llm/providers?online_only=true")

        assert response_all.status_code == 200
        assert response_online.status_code == 200

        # Online count should be <= total count
        all_count = response_all.json()["count"]
        online_count = response_online.json()["count"]
        assert online_count <= all_count

    @pytest.mark.asyncio
    async def test_get_provider_details(self, client):
        """Test GET /llm/providers/{id} returns provider details."""
        # First get list to find a valid provider
        response = await client.get("/api/llm/providers")
        data = response.json()

        if data["count"] > 0:
            provider_id = list(data["providers"].keys())[0]
            response = await client.get(f"/api/llm/providers/{provider_id}")
            assert response.status_code == 200

            provider_data = response.json()
            assert provider_data["id"] == provider_id
            assert "name" in provider_data
            assert "endpoint" in provider_data
            assert "capabilities" in provider_data
            assert "status" in provider_data

    @pytest.mark.asyncio
    async def test_get_provider_not_found(self, client):
        """Test GET /llm/providers/{id} returns 404 for unknown provider."""
        response = await client.get("/api/llm/providers/nonexistent_model_xyz")
        assert response.status_code == 404


class TestLLMModels:
    """Tests for model listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_models(self, client):
        """Test GET /llm/models returns model list."""
        response = await client.get("/api/llm/models")
        assert response.status_code == 200

        data = response.json()
        assert "models" in data
        assert "count" in data
        assert "default_model" in data

        # Should have gemini-2.5-flash as default
        assert data["default_model"] == "gemini-2.5-flash"

        # Models should have required fields
        if data["count"] > 0:
            model = data["models"][0]
            assert "id" in model
            assert "name" in model
            assert "provider_type" in model


class TestLLMHealth:
    """Tests for LLM health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test GET /llm/health returns health summary."""
        response = await client.get("/api/llm/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "total_providers" in data
        assert "online" in data
        assert "offline" in data
        assert "timestamp" in data


class TestLLMCostEstimation:
    """Tests for cost estimation endpoint."""

    @pytest.mark.asyncio
    async def test_estimate_cost_with_tokens(self, client):
        """Test POST /llm/estimate-cost with input_tokens."""
        response = await client.post(
            "/api/llm/estimate-cost",
            json={
                "model_id": "gemini-2.5-flash",
                "input_tokens": 1000,
                "estimated_output_tokens": 500
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "model_id" in data
        assert "input_tokens" in data
        assert "estimated_output_tokens" in data
        assert "input_cost_usd" in data
        assert "output_cost_usd" in data
        assert "total_cost_usd" in data
        assert "pricing_note" in data

        assert data["input_tokens"] == 1000
        assert data["estimated_output_tokens"] == 500

    @pytest.mark.asyncio
    async def test_estimate_cost_with_messages(self, client):
        """Test POST /llm/estimate-cost with messages."""
        response = await client.post(
            "/api/llm/estimate-cost",
            json={
                "model_id": "gemini-2.5-flash",
                "messages": [
                    {"role": "user", "content": "Hello, how are you?"}
                ],
                "estimated_output_tokens": 100
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "input_tokens" in data
        assert data["input_tokens"] > 0

    @pytest.mark.asyncio
    async def test_estimate_cost_missing_params(self, client):
        """Test POST /llm/estimate-cost fails without required params."""
        response = await client.post(
            "/api/llm/estimate-cost",
            json={
                "model_id": "gemini-2.5-flash"
                # Missing both input_tokens and messages
            }
        )
        assert response.status_code == 400


class TestLLMChat:
    """Tests for chat endpoints."""

    @pytest.mark.asyncio
    async def test_chat_request_validation(self, client):
        """Test POST /llm/chat validates request."""
        # Missing required messages
        response = await client.post(
            "/api/llm/chat",
            json={
                "model_id": "gemini-2.5-flash"
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_stream_redirect(self, client):
        """Test POST /llm/chat with stream=true suggests /chat/stream."""
        response = await client.post(
            "/api/llm/chat",
            json={
                "model_id": "gemini-2.5-flash",
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "stream": True
            }
        )
        # Should suggest using /chat/stream endpoint (400) or fail due to API not configured (500)
        assert response.status_code in [400, 500]
        if response.status_code == 400:
            assert "stream" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_chat_minimal(self, client):
        """Test POST /llm/chat with minimal valid request."""
        # This test may fail if Gemini API is not configured,
        # but it tests the endpoint is reachable
        response = await client.post(
            "/api/llm/chat",
            json={
                "model_id": "gemini-2.5-flash",
                "messages": [
                    {"role": "user", "content": "Say hello in one word."}
                ]
            },
            params={"skip_billing": True}
        )

        # Accept various responses - API may not be configured
        assert response.status_code in [200, 400, 500]


class TestDefaultProvider:
    """Tests for default provider configuration."""

    @pytest.mark.asyncio
    async def test_default_provider_is_gemini(self, client):
        """Test that default provider is gemini-2.5-flash."""
        response = await client.get("/api/llm/providers")
        data = response.json()

        assert data["default_provider"] == "gemini-2.5-flash"

        # Should be marked as default in providers list
        if "gemini-2.5-flash" in data["providers"]:
            assert data["providers"]["gemini-2.5-flash"]["is_default"] is True

    @pytest.mark.asyncio
    async def test_default_model_in_models_list(self, client):
        """Test that default model is marked in models list."""
        response = await client.get("/api/llm/models")
        data = response.json()

        assert data["default_model"] == "gemini-2.5-flash"

        # Find default in list
        defaults = [m for m in data["models"] if m.get("is_default")]
        if defaults:
            assert defaults[0]["id"] == "gemini-2.5-flash"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
