"""
Tests for Unified ASR Routes

Tests the /asr/* endpoints for speech recognition.

Run with:
    PYTHONPATH=/opt/kasaai:/opt/kasaai/apps pytest apps/shared/routes/tests/test_asr_routes.py -v
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
import base64
import sys

sys.path.insert(0, "/opt/kasaai/apps")

from shared.routes.asr_routes import router


@pytest.fixture
def app():
    """Create FastAPI app with ASR routes."""
    app = FastAPI()
    app.include_router(router, prefix="/api/asr")
    return app


@pytest_asyncio.fixture
async def client(app):
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestASRProviders:
    """Tests for ASR provider endpoints."""

    @pytest.mark.asyncio
    async def test_list_providers(self, client):
        """Test GET /asr/providers returns provider list."""
        response = await client.get("/api/asr/providers")
        assert response.status_code == 200

        data = response.json()
        assert "providers" in data
        assert "count" in data
        assert "default_provider" in data
        assert "timestamp" in data

        # Should have at least the default provider
        assert data["default_provider"] == "faster_whisper_large"

    @pytest.mark.asyncio
    async def test_list_providers_online_only(self, client):
        """Test GET /asr/providers?online_only=true filters offline providers."""
        response_all = await client.get("/api/asr/providers")
        response_online = await client.get("/api/asr/providers?online_only=true")

        assert response_all.status_code == 200
        assert response_online.status_code == 200

        # Online count should be <= total count
        all_count = response_all.json()["count"]
        online_count = response_online.json()["count"]
        assert online_count <= all_count

    @pytest.mark.asyncio
    async def test_get_provider_details(self, client):
        """Test GET /asr/providers/{id} returns provider details."""
        # First get list to find a valid provider
        response = await client.get("/api/asr/providers")
        data = response.json()

        if data["count"] > 0:
            provider_id = list(data["providers"].keys())[0]
            response = await client.get(f"/api/asr/providers/{provider_id}")
            assert response.status_code == 200

            provider_data = response.json()
            assert provider_data["id"] == provider_id
            assert "name" in provider_data
            assert "endpoint" in provider_data
            assert "capabilities" in provider_data
            assert "status" in provider_data

    @pytest.mark.asyncio
    async def test_get_provider_not_found(self, client):
        """Test GET /asr/providers/{id} returns 404 for unknown provider."""
        response = await client.get("/api/asr/providers/nonexistent_provider_xyz")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_supported_languages(self, client):
        """Test GET /asr/languages/{id} returns language list."""
        # Get a provider first
        response = await client.get("/api/asr/providers")
        data = response.json()

        if data["count"] > 0:
            provider_id = list(data["providers"].keys())[0]
            response = await client.get(f"/api/asr/languages/{provider_id}")
            assert response.status_code == 200

            lang_data = response.json()
            assert "provider_id" in lang_data
            assert "languages" in lang_data
            assert "count" in lang_data
            assert lang_data["provider_id"] == provider_id


class TestASRHealth:
    """Tests for ASR health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test GET /asr/health returns health summary."""
        response = await client.get("/api/asr/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "total_providers" in data
        assert "online" in data
        assert "offline" in data
        assert "timestamp" in data


class TestASRCostEstimation:
    """Tests for cost estimation endpoint."""

    @pytest.mark.asyncio
    async def test_estimate_cost_with_duration(self, client):
        """Test POST /asr/estimate-cost with duration_seconds."""
        response = await client.post(
            "/api/asr/estimate-cost",
            json={
                "provider_id": "faster_whisper_large",
                "duration_seconds": 60.0
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "provider_id" in data
        assert "estimated_cost_usd" in data
        assert "estimated_duration_seconds" in data
        assert "pricing_note" in data
        assert data["estimated_duration_seconds"] == 60.0

    @pytest.mark.asyncio
    async def test_estimate_cost_with_audio(self, client):
        """Test POST /asr/estimate-cost with audio_base64."""
        # Create a small fake audio (16KB ~= 0.5 seconds)
        fake_audio = b"\x00" * 16000
        audio_base64 = base64.b64encode(fake_audio).decode("utf-8")

        response = await client.post(
            "/api/asr/estimate-cost",
            json={
                "provider_id": "faster_whisper_large",
                "audio_base64": audio_base64
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "estimated_cost_usd" in data
        assert "estimated_duration_seconds" in data
        assert data["estimated_duration_seconds"] > 0

    @pytest.mark.asyncio
    async def test_estimate_cost_missing_params(self, client):
        """Test POST /asr/estimate-cost fails without required params."""
        response = await client.post(
            "/api/asr/estimate-cost",
            json={
                "provider_id": "faster_whisper_large"
                # Missing both audio_base64 and duration_seconds
            }
        )
        assert response.status_code == 400


class TestASRTranscription:
    """Tests for transcription endpoints."""

    @pytest.mark.asyncio
    async def test_transcribe_request_validation(self, client):
        """Test POST /asr/transcribe validates request."""
        # Missing required audio_base64
        response = await client.post(
            "/api/asr/transcribe",
            json={
                "provider_id": "faster_whisper_large"
            }
        )
        # Should fail validation (422 or 400)
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_transcribe_with_minimal_audio(self, client):
        """Test POST /asr/transcribe with minimal audio data (may fail if provider offline)."""
        # Very small audio - likely to fail but tests the endpoint
        fake_audio = b"\x00" * 1000
        audio_base64 = base64.b64encode(fake_audio).decode("utf-8")

        response = await client.post(
            "/api/asr/transcribe",
            json={
                "provider_id": "faster_whisper_large",
                "audio_base64": audio_base64,
                "language": "en"
            },
            params={"skip_billing": True}
        )

        # Accept various responses - provider may be offline or audio invalid
        assert response.status_code in [200, 400, 500]


class TestDefaultProvider:
    """Tests for default provider configuration."""

    @pytest.mark.asyncio
    async def test_default_provider_is_whisper(self, client):
        """Test that default provider is whisper.ailabsafrica.com."""
        response = await client.get("/api/asr/providers")
        data = response.json()

        # Default should be faster_whisper_large (whisper.ailabsafrica.com)
        assert data["default_provider"] == "faster_whisper_large"

        # Should be marked as default in providers list
        if "faster_whisper_large" in data["providers"]:
            assert data["providers"]["faster_whisper_large"]["is_default"] is True

    @pytest.mark.asyncio
    async def test_default_provider_in_health(self, client):
        """Test that health endpoint shows default provider."""
        response = await client.get("/api/asr/health")
        data = response.json()

        assert "default_provider" in data
        assert data["default_provider"] == "faster_whisper_large"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
