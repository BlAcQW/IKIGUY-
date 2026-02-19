"""
Tests for Voice Settings Routes

Tests the /voice-settings/* endpoints.

Run with:
    PYTHONPATH=/opt/kasaai:/opt/kasaai/apps pytest apps/shared/routes/tests/test_voice_settings_routes.py -v
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI, Depends
from unittest.mock import AsyncMock, MagicMock
import sys

sys.path.insert(0, "/opt/kasaai/apps")

from shared.routes.voice_settings_routes import (
    create_voice_settings_router,
    create_simple_voice_settings_router,
    VOICE_PRESETS,
)
from shared.services.voice_settings_service import (
    VoiceSettings,
    TTSSettings,
    ASRSettings,
    LLMSettings,
    VoicePreferences,
)
from datetime import datetime


# Mock user for testing
MOCK_USER = {
    "sub": "test_user_123",
    "organization_id": "test_org_456",
    "role": "user"
}

MOCK_ADMIN = {
    "sub": "admin_user_123",
    "organization_id": "test_org_456",
    "role": "admin"
}


# Mock settings
MOCK_SETTINGS = VoiceSettings(
    user_id="test_user_123",
    organization_id="test_org_456",
    tts=TTSSettings(default_provider="coqui_xtts", speed=1.0),
    asr=ASRSettings(default_provider="faster_whisper_large", language="en"),
    llm=LLMSettings(default_model="gemini-2.5-flash", temperature=0.7),
    voices=VoicePreferences(),
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
)


@pytest.fixture
def mock_voice_service():
    """Create mock voice settings service."""
    service = AsyncMock()
    service.get_settings = AsyncMock(return_value=MOCK_SETTINGS)
    service.update_settings = AsyncMock(return_value=MOCK_SETTINGS)
    service.delete_settings = AsyncMock(return_value=True)
    service.get_organization_defaults = AsyncMock(return_value=None)
    service.set_organization_defaults = AsyncMock(return_value=MOCK_SETTINGS)
    service.get_statistics = AsyncMock(return_value={
        "total_users": 10,
        "tts_providers": ["coqui_xtts", "f5tts"],
        "asr_providers": ["faster_whisper_large"],
        "llm_models": ["gemini-2.5-flash"]
    })
    return service


@pytest.fixture
def app_with_user(mock_voice_service):
    """Create FastAPI app with authenticated user."""
    app = FastAPI()

    async def get_current_user():
        return MOCK_USER

    def get_database():
        return MagicMock()

    # Patch service creation
    original_init = None

    router = create_voice_settings_router(
        get_current_user_func=get_current_user,
        get_database_func=get_database,
    )
    app.include_router(router, prefix="/api/voice-settings")

    # Store mock service for patching
    app.state.mock_service = mock_voice_service

    return app


@pytest.fixture
def app_with_admin(mock_voice_service):
    """Create FastAPI app with admin user."""
    app = FastAPI()

    async def get_current_user():
        return MOCK_ADMIN

    def get_database():
        return MagicMock()

    router = create_voice_settings_router(
        get_current_user_func=get_current_user,
        get_database_func=get_database,
    )
    app.include_router(router, prefix="/api/voice-settings")

    return app


@pytest.fixture
def simple_app():
    """Create FastAPI app with simple router (no auth)."""
    app = FastAPI()

    def get_database():
        return MagicMock()

    router = create_simple_voice_settings_router(get_database_func=get_database)
    app.include_router(router, prefix="/api/voice-settings")

    return app


@pytest_asyncio.fixture
async def client(app_with_user):
    """Create async test client with user auth."""
    transport = ASGITransport(app=app_with_user)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def admin_client(app_with_admin):
    """Create async test client with admin auth."""
    transport = ASGITransport(app=app_with_admin)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def simple_client(simple_app):
    """Create async test client without auth."""
    transport = ASGITransport(app=simple_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestPresets:
    """Tests for presets endpoint (no auth required)."""

    @pytest.mark.asyncio
    async def test_get_presets(self, simple_client):
        """Test GET /presets returns preset list."""
        response = await simple_client.get("/api/voice-settings/presets")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == len(VOICE_PRESETS)

        # Check preset structure
        preset = data[0]
        assert "id" in preset
        assert "name" in preset
        assert "description" in preset
        assert "tts" in preset
        assert "asr" in preset
        assert "llm" in preset

    @pytest.mark.asyncio
    async def test_presets_have_required_ids(self, simple_client):
        """Test that all presets have required fields."""
        response = await simple_client.get("/api/voice-settings/presets")
        data = response.json()

        expected_ids = {"default", "fast_response", "high_quality", "african_languages", "cost_effective"}
        actual_ids = {p["id"] for p in data}

        assert expected_ids == actual_ids


class TestPresetsContent:
    """Tests for preset content."""

    def test_default_preset(self):
        """Test default preset has correct values."""
        default = next((p for p in VOICE_PRESETS if p["id"] == "default"), None)
        assert default is not None
        assert default["tts"]["default_provider"] == "coqui_xtts"
        assert default["asr"]["default_provider"] == "faster_whisper_large"
        assert default["llm"]["default_model"] == "gemini-2.5-flash"

    def test_fast_response_preset(self):
        """Test fast response preset uses fast providers."""
        fast = next((p for p in VOICE_PRESETS if p["id"] == "fast_response"), None)
        assert fast is not None
        assert fast["tts"]["speed"] == 1.2  # Faster speech
        assert "turbo" in fast["asr"]["default_provider"] or "groq" in fast["asr"]["default_provider"]

    def test_cost_effective_preset(self):
        """Test cost effective preset uses free tier."""
        cost = next((p for p in VOICE_PRESETS if p["id"] == "cost_effective"), None)
        assert cost is not None
        # Should use self-hosted or free tier services
        assert cost["asr"]["default_provider"] == "faster_whisper_large"  # Self-hosted


class TestRouterFactory:
    """Tests for router factory function."""

    def test_create_router_returns_router(self):
        """Test create_voice_settings_router returns an APIRouter."""
        from fastapi import APIRouter

        router = create_voice_settings_router(
            get_current_user_func=lambda: {},
            get_database_func=lambda: None,
        )

        assert isinstance(router, APIRouter)

    def test_simple_router_returns_router(self):
        """Test create_simple_voice_settings_router returns an APIRouter."""
        from fastapi import APIRouter

        router = create_simple_voice_settings_router(
            get_database_func=lambda: None,
        )

        assert isinstance(router, APIRouter)


class TestUpdateModels:
    """Tests for update request models."""

    def test_tts_settings_update_validation(self):
        """Test TTSSettingsUpdate validates speed range."""
        from shared.routes.voice_settings_routes import TTSSettingsUpdate

        # Valid speed
        update = TTSSettingsUpdate(speed=1.5)
        assert update.speed == 1.5

        # Invalid speed (too high)
        with pytest.raises(Exception):
            TTSSettingsUpdate(speed=3.0)

        # Invalid speed (too low)
        with pytest.raises(Exception):
            TTSSettingsUpdate(speed=0.1)

    def test_llm_settings_update_validation(self):
        """Test LLMSettingsUpdate validates temperature range."""
        from shared.routes.voice_settings_routes import LLMSettingsUpdate

        # Valid temperature
        update = LLMSettingsUpdate(temperature=1.5)
        assert update.temperature == 1.5

        # Invalid temperature (too high)
        with pytest.raises(Exception):
            LLMSettingsUpdate(temperature=3.0)


class TestVoiceSettingsUpdate:
    """Tests for VoiceSettingsUpdate model."""

    def test_partial_update(self):
        """Test partial updates work correctly."""
        from shared.routes.voice_settings_routes import (
            VoiceSettingsUpdate,
            TTSSettingsUpdate,
        )

        # Only update TTS speed
        update = VoiceSettingsUpdate(
            tts=TTSSettingsUpdate(speed=1.2)
        )

        assert update.tts is not None
        assert update.tts.speed == 1.2
        assert update.tts.default_provider is None  # Not set
        assert update.asr is None
        assert update.llm is None

    def test_empty_update(self):
        """Test empty update is valid."""
        from shared.routes.voice_settings_routes import VoiceSettingsUpdate

        update = VoiceSettingsUpdate()

        assert update.tts is None
        assert update.asr is None
        assert update.llm is None


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
