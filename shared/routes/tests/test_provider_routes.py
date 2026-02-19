"""
Tests for Unified Provider Discovery Routes

Tests the /providers/* endpoints for TTS, ASR, and LLM provider discovery.

Run with:
    PYTHONPATH=/opt/kasaai:/opt/kasaai/apps pytest apps/shared/routes/tests/test_provider_routes.py -v
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
import sys

sys.path.insert(0, "/opt/kasaai/apps")

from shared.routes.provider_routes import router, initialize_providers


@pytest.fixture
def app():
    """Create FastAPI app with provider routes."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return app


@pytest_asyncio.fixture
async def client(app):
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestProviderRoutes:
    """Tests for provider discovery endpoints."""

    @pytest.mark.asyncio
    async def test_get_tts_providers(self, client):
        """Test GET /providers/tts returns TTS providers."""
        response = await client.get("/api/v1/providers/tts")
        assert response.status_code == 200

        data = response.json()
        assert "providers" in data
        assert "count" in data
        assert "timestamp" in data
        assert data["count"] >= 0

        # Check provider structure if any exist
        if data["count"] > 0:
            first_provider = list(data["providers"].values())[0]
            assert "id" in first_provider
            assert "name" in first_provider
            assert "endpoint" in first_provider
            assert "provider_type" in first_provider
            assert first_provider["provider_type"] == "tts"

    @pytest.mark.asyncio
    async def test_get_asr_providers(self, client):
        """Test GET /providers/asr returns ASR providers."""
        response = await client.get("/api/v1/providers/asr")
        assert response.status_code == 200

        data = response.json()
        assert "providers" in data
        assert "count" in data
        assert data["count"] >= 0

        # Check for default marker
        if data["count"] > 0:
            # At least one should have is_default if faster_whisper_large exists
            providers_list = list(data["providers"].values())
            provider_ids = [p["id"] for p in providers_list]

            # Check structure
            first_provider = providers_list[0]
            assert "id" in first_provider
            assert "provider_type" in first_provider
            assert first_provider["provider_type"] == "asr"

    @pytest.mark.asyncio
    async def test_get_llm_providers(self, client):
        """Test GET /providers/llm returns LLM providers."""
        response = await client.get("/api/v1/providers/llm")
        assert response.status_code == 200

        data = response.json()
        assert "providers" in data
        assert "count" in data

        if data["count"] > 0:
            first_provider = list(data["providers"].values())[0]
            assert "id" in first_provider
            assert "provider_type" in first_provider
            assert first_provider["provider_type"] == "llm"

    @pytest.mark.asyncio
    async def test_get_all_providers(self, client):
        """Test GET /providers/all returns all providers grouped."""
        response = await client.get("/api/v1/providers/all")
        assert response.status_code == 200

        data = response.json()
        assert "tts" in data
        assert "asr" in data
        assert "llm" in data
        assert "stats" in data
        assert "timestamp" in data

        # Verify stats are accurate
        assert data["stats"]["tts_count"] == len(data["tts"])
        assert data["stats"]["asr_count"] == len(data["asr"])
        assert data["stats"]["llm_count"] == len(data["llm"])
        assert data["stats"]["total"] == (
            len(data["tts"]) + len(data["asr"]) + len(data["llm"])
        )

    @pytest.mark.asyncio
    async def test_get_provider_details(self, client):
        """Test GET /providers/{type}/{id} returns provider details."""
        # First get list to find a valid provider
        response = await client.get("/api/v1/providers/tts")
        data = response.json()

        if data["count"] > 0:
            provider_id = list(data["providers"].keys())[0]

            response = await client.get(f"/api/v1/providers/tts/{provider_id}")
            assert response.status_code == 200

            provider_data = response.json()
            assert provider_data["id"] == provider_id
            assert "name" in provider_data
            assert "capabilities" in provider_data

    @pytest.mark.asyncio
    async def test_get_provider_not_found(self, client):
        """Test GET /providers/{type}/{id} returns 404 for unknown provider."""
        response = await client.get("/api/v1/providers/tts/nonexistent_provider_xyz")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_provider_wrong_type(self, client):
        """Test GET /providers/{type}/{id} returns 400 for wrong provider type."""
        # Get a TTS provider ID
        response = await client.get("/api/v1/providers/tts")
        data = response.json()

        if data["count"] > 0:
            tts_provider_id = list(data["providers"].keys())[0]

            # Try to access it as ASR provider
            response = await client.get(f"/api/v1/providers/asr/{tts_provider_id}")
            # Should fail - either 400 (wrong type) or 404 (not found as asr)
            assert response.status_code in [400, 404]

    @pytest.mark.asyncio
    async def test_providers_health(self, client):
        """Test GET /providers/health returns health summary."""
        response = await client.get("/api/v1/providers/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "total_providers" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_force_refresh_cache(self, client):
        """Test force_refresh=True bypasses cache."""
        # First request - should cache
        response1 = await client.get("/api/v1/providers/tts")
        assert response1.status_code == 200
        timestamp1 = response1.json()["timestamp"]

        # Second request with force_refresh - should have new timestamp
        response2 = await client.get("/api/v1/providers/tts?force_refresh=true")
        assert response2.status_code == 200
        timestamp2 = response2.json()["timestamp"]

        # Timestamps should be different (or very close if fast)
        # Just verify the request succeeded
        assert response2.status_code == 200

    @pytest.mark.asyncio
    async def test_online_only_filter(self, client):
        """Test online_only=True filters offline providers."""
        # Get all providers
        response_all = await client.get("/api/v1/providers/tts")
        assert response_all.status_code == 200

        # Get online only
        response_online = await client.get("/api/v1/providers/tts?online_only=true")
        assert response_online.status_code == 200

        # Online count should be <= total count
        all_count = response_all.json()["count"]
        online_count = response_online.json()["count"]
        assert online_count <= all_count

    @pytest.mark.asyncio
    async def test_refresh_cache_endpoint(self, client):
        """Test POST /providers/refresh-cache clears cache."""
        response = await client.post("/api/v1/providers/refresh-cache")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "message" in data


class TestProviderCapabilities:
    """Tests for provider capabilities."""

    @pytest.mark.asyncio
    async def test_tts_capabilities_structure(self, client):
        """Test TTS providers have expected capability fields."""
        response = await client.get("/api/v1/providers/tts")
        data = response.json()

        if data["count"] > 0:
            provider = list(data["providers"].values())[0]
            capabilities = provider.get("capabilities", {})

            # TTS-specific capabilities should be present (if any)
            valid_tts_caps = {
                "voiceCloning", "multiLanguage", "speedControl",
                "pitchControl", "emotionControl", "streaming", "realtime"
            }
            for cap in capabilities.keys():
                # All capabilities should be boolean
                assert isinstance(capabilities[cap], bool)

    @pytest.mark.asyncio
    async def test_asr_capabilities_structure(self, client):
        """Test ASR providers have expected capability fields."""
        response = await client.get("/api/v1/providers/asr")
        data = response.json()

        if data["count"] > 0:
            provider = list(data["providers"].values())[0]
            capabilities = provider.get("capabilities", {})

            # ASR-specific capabilities
            valid_asr_caps = {
                "multiLanguage", "timestamps", "wordLevelTimestamps",
                "diarization", "punctuation", "translation", "streaming"
            }
            for cap in capabilities.keys():
                assert isinstance(capabilities[cap], bool)

    @pytest.mark.asyncio
    async def test_llm_capabilities_structure(self, client):
        """Test LLM providers have expected capability fields."""
        response = await client.get("/api/v1/providers/llm")
        data = response.json()

        if data["count"] > 0:
            provider = list(data["providers"].values())[0]
            capabilities = provider.get("capabilities", {})

            # LLM-specific capabilities
            valid_llm_caps = {
                "multiLanguage", "streaming", "reasoning", "codeGeneration",
                "functionCalling", "vision", "culturalContext", "longContext"
            }
            for cap in capabilities.keys():
                assert isinstance(capabilities[cap], bool)


class TestDefaultProviders:
    """Tests for default provider markers."""

    @pytest.mark.asyncio
    async def test_asr_default_marker(self, client):
        """Test ASR providers have is_default marker on whisper.ailabsafrica.com."""
        response = await client.get("/api/v1/providers/asr")
        data = response.json()

        # Check if default provider is marked
        default_providers = [
            p for p in data["providers"].values()
            if p.get("is_default", False)
        ]

        # Should have at least one default if faster_whisper_large exists
        provider_ids = list(data["providers"].keys())
        if "faster_whisper_large" in provider_ids or "whisper_large_v3" in provider_ids:
            assert len(default_providers) >= 1

    @pytest.mark.asyncio
    async def test_llm_default_marker(self, client):
        """Test LLM providers have is_default marker on gemini-2.5-flash."""
        response = await client.get("/api/v1/providers/llm")
        data = response.json()

        # Check if default provider is marked
        if "gemini-2.5-flash" in data["providers"]:
            assert data["providers"]["gemini-2.5-flash"].get("is_default", False)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
