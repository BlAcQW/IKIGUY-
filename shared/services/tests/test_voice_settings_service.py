"""
Unit tests for VoiceSettingsService

Tests CRUD operations, organization defaults, and statistics for voice settings.

Author: KasaAI
Date: 2025-11-03
"""

import pytest
import pytest_asyncio
import asyncio
import sys
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from voice_settings_service import (
    VoiceSettingsService,
    VoiceSettings,
    TTSSettings,
    ASRSettings,
    LLMSettings,
    VoicePreferences
)


# Test configuration
from urllib.parse import quote_plus
password = quote_plus("aawwER4444")
TEST_MONGODB_URI = f"mongodb://admin:{password}@127.0.0.1:27017/"
TEST_DATABASE = "test_voice_settings"


@pytest_asyncio.fixture
async def db():
    """Create test database connection."""
    client = AsyncIOMotorClient(TEST_MONGODB_URI)
    database = client[TEST_DATABASE]
    yield database

    # Cleanup: Drop test database
    await client.drop_database(TEST_DATABASE)
    client.close()


@pytest_asyncio.fixture
async def service(db):
    """Create VoiceSettingsService instance."""
    svc = VoiceSettingsService(db)
    await svc.ensure_indexes()
    return svc


@pytest.mark.asyncio
async def test_create_default_settings(service):
    """Test creating default settings for a new user."""
    user_id = "user_001"
    org_id = "org_001"

    settings = await service.get_settings(user_id, org_id)

    assert settings.user_id == user_id
    assert settings.organization_id == org_id
    assert settings.tts.default_provider == "coqui_xtts"
    assert settings.tts.speed == 1.0
    assert settings.tts.pitch == 0.0
    assert settings.asr.default_provider == "whisper_local"
    assert settings.asr.language == "en"
    assert settings.llm.default_model == "llama3.2"
    assert settings.llm.temperature == 0.7
    assert settings.llm.max_tokens == 2000
    assert settings.voices.favorite_voices == []


@pytest.mark.asyncio
async def test_get_existing_settings(service):
    """Test retrieving existing settings."""
    user_id = "user_002"
    org_id = "org_001"

    # Create settings
    settings1 = await service.get_settings(user_id, org_id)

    # Retrieve settings again
    settings2 = await service.get_settings(user_id, org_id)

    assert settings1.user_id == settings2.user_id
    assert settings1.organization_id == settings2.organization_id
    assert settings1.tts.default_provider == settings2.tts.default_provider


@pytest.mark.asyncio
async def test_update_tts_settings(service):
    """Test updating TTS settings."""
    user_id = "user_003"
    org_id = "org_001"

    # Get initial settings
    settings = await service.get_settings(user_id, org_id)
    assert settings.tts.speed == 1.0

    # Update TTS settings
    updates = {
        "tts": {
            "default_provider": "f5tts",
            "speed": 1.5,
            "pitch": 0.2
        }
    }
    updated = await service.update_settings(user_id, org_id, updates)

    assert updated.tts.default_provider == "f5tts"
    assert updated.tts.speed == 1.5
    assert updated.tts.pitch == 0.2
    # Other settings should remain unchanged
    assert updated.asr.default_provider == "whisper_local"
    assert updated.llm.default_model == "llama3.2"


@pytest.mark.asyncio
async def test_update_asr_settings(service):
    """Test updating ASR settings."""
    user_id = "user_004"
    org_id = "org_001"

    updates = {
        "asr": {
            "default_provider": "whisper_cloud",
            "language": "es"
        }
    }
    updated = await service.update_settings(user_id, org_id, updates)

    assert updated.asr.default_provider == "whisper_cloud"
    assert updated.asr.language == "es"
    assert updated.asr.task == "transcribe"  # Should remain unchanged


@pytest.mark.asyncio
async def test_update_llm_settings(service):
    """Test updating LLM settings."""
    user_id = "user_005"
    org_id = "org_001"

    updates = {
        "llm": {
            "default_model": "gpt-4",
            "temperature": 0.9,
            "max_tokens": 4000
        }
    }
    updated = await service.update_settings(user_id, org_id, updates)

    assert updated.llm.default_model == "gpt-4"
    assert updated.llm.temperature == 0.9
    assert updated.llm.max_tokens == 4000


@pytest.mark.asyncio
async def test_update_favorite_voices(service):
    """Test updating favorite voices."""
    user_id = "user_006"
    org_id = "org_001"

    updates = {
        "voices": {
            "favorite_voices": ["voice_001", "voice_002", "voice_003"]
        }
    }
    updated = await service.update_settings(user_id, org_id, updates)

    assert len(updated.voices.favorite_voices) == 3
    assert "voice_001" in updated.voices.favorite_voices
    assert "voice_002" in updated.voices.favorite_voices
    assert "voice_003" in updated.voices.favorite_voices


@pytest.mark.asyncio
async def test_partial_update(service):
    """Test partial update (only updating one field)."""
    user_id = "user_007"
    org_id = "org_001"

    # Get initial settings
    initial = await service.get_settings(user_id, org_id)

    # Update only speed
    updates = {"tts": {"speed": 1.8}}
    updated = await service.update_settings(user_id, org_id, updates)

    # Speed should change
    assert updated.tts.speed == 1.8
    # Other TTS settings should remain
    assert updated.tts.default_provider == initial.tts.default_provider
    assert updated.tts.pitch == initial.tts.pitch


@pytest.mark.asyncio
async def test_delete_settings(service):
    """Test deleting user settings."""
    user_id = "user_008"
    org_id = "org_001"

    # Create settings
    await service.get_settings(user_id, org_id)

    # Delete settings
    deleted = await service.delete_settings(user_id, org_id)
    assert deleted is True

    # Try deleting again (should return False)
    deleted_again = await service.delete_settings(user_id, org_id)
    assert deleted_again is False


@pytest.mark.asyncio
async def test_organization_defaults(service):
    """Test organization default settings."""
    org_id = "org_002"

    # Set organization defaults
    org_settings = {
        "tts": {
            "default_provider": "openai_tts",
            "speed": 1.2
        },
        "asr": {
            "default_provider": "google_asr",
            "language": "fr"
        },
        "llm": {
            "default_model": "claude-3",
            "temperature": 0.5
        }
    }

    org_defaults = await service.set_organization_defaults(org_id, org_settings)

    assert org_defaults.user_id == "org_default"
    assert org_defaults.organization_id == org_id
    assert org_defaults.tts.default_provider == "openai_tts"
    assert org_defaults.tts.speed == 1.2
    assert org_defaults.asr.default_provider == "google_asr"
    assert org_defaults.asr.language == "fr"
    assert org_defaults.llm.default_model == "claude-3"


@pytest.mark.asyncio
async def test_user_inherits_org_defaults(service):
    """Test that new users inherit organization defaults."""
    org_id = "org_003"

    # Set organization defaults
    org_settings = {
        "tts": {"default_provider": "custom_tts", "speed": 1.3},
        "asr": {"language": "de"},
        "llm": {"temperature": 0.8}
    }
    await service.set_organization_defaults(org_id, org_settings)

    # Create new user in this org
    user_id = "user_009"
    user_settings = await service.get_settings(user_id, org_id)

    # User should inherit org defaults
    assert user_settings.tts.default_provider == "custom_tts"
    assert user_settings.tts.speed == 1.3
    assert user_settings.asr.language == "de"
    assert user_settings.llm.temperature == 0.8


@pytest.mark.asyncio
async def test_get_organization_defaults_none(service):
    """Test getting organization defaults when none exist."""
    org_id = "org_004"

    defaults = await service.get_organization_defaults(org_id)
    assert defaults is None


@pytest.mark.asyncio
async def test_get_all_settings_for_org(service):
    """Test getting all user settings for an organization."""
    org_id = "org_005"

    # Create settings for multiple users
    await service.get_settings("user_010", org_id)
    await service.get_settings("user_011", org_id)
    await service.get_settings("user_012", org_id)

    # Get all settings
    all_settings = await service.get_all_settings_for_org(org_id, limit=10)

    assert len(all_settings) == 3
    user_ids = [s.user_id for s in all_settings]
    assert "user_010" in user_ids
    assert "user_011" in user_ids
    assert "user_012" in user_ids


@pytest.mark.asyncio
async def test_get_statistics(service):
    """Test getting statistics for an organization."""
    org_id = "org_006"

    # Create settings with different providers
    await service.update_settings("user_013", org_id, {
        "tts": {"default_provider": "provider_a"},
        "asr": {"default_provider": "asr_a"},
        "llm": {"default_model": "model_a"}
    })

    await service.update_settings("user_014", org_id, {
        "tts": {"default_provider": "provider_b"},
        "asr": {"default_provider": "asr_a"},
        "llm": {"default_model": "model_a"}
    })

    await service.update_settings("user_015", org_id, {
        "tts": {"default_provider": "provider_a"},
        "asr": {"default_provider": "asr_b"},
        "llm": {"default_model": "model_b"}
    })

    stats = await service.get_statistics(org_id)

    assert stats["total_users"] == 3
    assert stats["organization_id"] == org_id
    assert "provider_a" in stats["tts_providers"]
    assert "provider_b" in stats["tts_providers"]
    assert "asr_a" in stats["asr_providers"]
    assert "model_a" in stats["llm_models"]
    assert "model_b" in stats["llm_models"]


@pytest.mark.asyncio
async def test_unique_constraint(service):
    """Test that user_id + organization_id is unique."""
    user_id = "user_016"
    org_id = "org_007"

    # Create settings
    settings1 = await service.get_settings(user_id, org_id)

    # Update settings
    updates = {"tts": {"speed": 1.5}}
    settings2 = await service.update_settings(user_id, org_id, updates)

    # Should update existing, not create new
    all_settings = await service.get_all_settings_for_org(org_id)
    assert len(all_settings) == 1
    assert all_settings[0].tts.speed == 1.5


@pytest.mark.asyncio
async def test_updated_at_timestamp(service):
    """Test that updated_at is updated on changes."""
    user_id = "user_017"
    org_id = "org_008"

    # Create settings
    settings1 = await service.get_settings(user_id, org_id)
    initial_timestamp = settings1.updated_at

    # Wait a bit
    await asyncio.sleep(0.1)

    # Update settings
    updates = {"tts": {"speed": 1.6}}
    settings2 = await service.update_settings(user_id, org_id, updates)
    updated_timestamp = settings2.updated_at

    # Timestamp should be newer
    assert updated_timestamp > initial_timestamp


@pytest.mark.asyncio
async def test_pagination(service):
    """Test pagination for get_all_settings_for_org."""
    org_id = "org_009"

    # Create 10 users
    for i in range(10):
        await service.get_settings(f"user_{100+i}", org_id)

    # Get first 5
    page1 = await service.get_all_settings_for_org(org_id, limit=5, skip=0)
    assert len(page1) == 5

    # Get next 5
    page2 = await service.get_all_settings_for_org(org_id, limit=5, skip=5)
    assert len(page2) == 5

    # Should be different users
    page1_ids = {s.user_id for s in page1}
    page2_ids = {s.user_id for s in page2}
    assert len(page1_ids.intersection(page2_ids)) == 0


@pytest.mark.asyncio
async def test_validation_speed_range(service):
    """Test that speed validation works."""
    user_id = "user_018"
    org_id = "org_010"

    # Valid speed
    updates = {"tts": {"speed": 1.5}}
    updated = await service.update_settings(user_id, org_id, updates)
    assert updated.tts.speed == 1.5

    # Speed outside valid range should fail validation
    with pytest.raises(Exception):  # Pydantic validation error
        updates = {"tts": {"speed": 3.0}}  # Max is 2.0
        await service.update_settings(user_id, org_id, updates)


@pytest.mark.asyncio
async def test_validation_temperature_range(service):
    """Test that temperature validation works."""
    user_id = "user_019"
    org_id = "org_011"

    # Valid temperature
    updates = {"llm": {"temperature": 1.5}}
    updated = await service.update_settings(user_id, org_id, updates)
    assert updated.llm.temperature == 1.5

    # Temperature outside valid range should fail
    with pytest.raises(Exception):  # Pydantic validation error
        updates = {"llm": {"temperature": 3.0}}  # Max is 2.0
        await service.update_settings(user_id, org_id, updates)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
