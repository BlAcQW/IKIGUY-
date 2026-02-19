"""
Tests for LLM service functionality.

Tests LLM provider and model management, including listing providers and models,
getting default configurations, and error handling.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from backend.services import llm_service


class TestLLMService:
    """Test suite for LLM service operations."""

    @pytest.fixture
    def mock_llm_providers(self):
        """Mock LLM providers data."""
        return [
            MagicMock(name="openai", display_name="OpenAI", active=True),
            MagicMock(name="anthropic", display_name="Anthropic", active=True),
            MagicMock(name="google", display_name="Google", active=False)
        ]

    @pytest.fixture
    def mock_llm_models(self):
        """Mock LLM models data."""
        return [
            MagicMock(name="gpt-4", display_name="GPT-4", provider_id="openai", active=True),
            MagicMock(name="gpt-3.5-turbo", display_name="GPT-3.5 Turbo", provider_id="openai", active=True),
            MagicMock(name="claude-3-sonnet", display_name="Claude 3 Sonnet", provider_id="anthropic", active=True),
            MagicMock(name="gemini-pro", display_name="Gemini Pro", provider_id="google", active=False)
        ]

    @pytest.mark.asyncio
    async def test_get_providers_active_only(self, mock_llm_providers):
        """Test getting active LLM providers only."""
        with patch.object(llm_service, 'get_providers', return_value=mock_llm_providers[:2]):
            providers = await llm_service.get_providers(active_only=True)

            assert len(providers) == 2
            assert all(provider.active for provider in providers)
            assert providers[0].name == "openai"
            assert providers[1].name == "anthropic"

    @pytest.mark.asyncio
    async def test_get_providers_all(self, mock_llm_providers):
        """Test getting all LLM providers."""
        with patch.object(llm_service, 'get_providers', return_value=mock_llm_providers):
            providers = await llm_service.get_providers(active_only=False)

            assert len(providers) == 3
            assert providers[0].name == "openai"
            assert providers[1].name == "anthropic"
            assert providers[2].name == "google"

    @pytest.mark.asyncio
    async def test_get_models_active_only(self, mock_llm_models):
        """Test getting active LLM models only."""
        active_models = [model for model in mock_llm_models if model.active]

        with patch.object(llm_service, 'get_models', return_value=active_models):
            models = await llm_service.get_models(active_only=True)

            assert len(models) == 3
            assert all(model.active for model in models)
            assert models[0].name == "gpt-4"
            assert models[1].name == "gpt-3.5-turbo"
            assert models[2].name == "claude-3-sonnet"

    @pytest.mark.asyncio
    async def test_get_models_all(self, mock_llm_models):
        """Test getting all LLM models."""
        with patch.object(llm_service, 'get_models', return_value=mock_llm_models):
            models = await llm_service.get_models(active_only=False)

            assert len(models) == 4
            assert models[0].name == "gpt-4"
            assert models[-1].name == "gemini-pro"

    @pytest.mark.asyncio
    async def test_get_models_by_provider(self, mock_llm_models):
        """Test getting models filtered by provider."""
        openai_models = [model for model in mock_llm_models if model.provider_id == "openai"]

        with patch.object(llm_service, 'get_models', return_value=openai_models):
            models = await llm_service.get_models(provider_id="openai")

            assert len(models) == 2
            assert all(model.provider_id == "openai" for model in models)
            assert models[0].name == "gpt-4"
            assert models[1].name == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_get_default_model_exists(self, mock_llm_models):
        """Test getting default model when it exists."""
        default_model = mock_llm_models[0]  # gpt-4

        with patch.object(llm_service, 'get_default_model', return_value=default_model):
            model = await llm_service.get_default_model()

            assert model is not None
            assert model.name == "gpt-4"
            assert model.display_name == "GPT-4"
            assert model.provider_id == "openai"

    @pytest.mark.asyncio
    async def test_get_default_model_none(self):
        """Test getting default model when none is set."""
        with patch.object(llm_service, 'get_default_model', return_value=None):
            model = await llm_service.get_default_model()

            assert model is None

    @pytest.mark.asyncio
    async def test_get_providers_empty_list(self):
        """Test getting providers when none exist."""
        with patch.object(llm_service, 'get_providers', return_value=[]):
            providers = await llm_service.get_providers()

            assert len(providers) == 0

    @pytest.mark.asyncio
    async def test_get_models_empty_list(self):
        """Test getting models when none exist."""
        with patch.object(llm_service, 'get_models', return_value=[]):
            models = await llm_service.get_models()

            assert len(models) == 0

    @pytest.mark.asyncio
    async def test_service_error_handling(self):
        """Test error handling in LLM service."""
        with patch.object(llm_service, 'get_providers', side_effect=Exception("Database error")):
            with pytest.raises(Exception):
                await llm_service.get_providers()

    @pytest.mark.asyncio
    async def test_get_provider_by_name(self, mock_llm_providers):
        """Test getting a specific provider by name."""
        openai_provider = mock_llm_providers[0]

        with patch.object(llm_service, 'get_provider_by_name', return_value=openai_provider):
            provider = await llm_service.get_provider_by_name("openai")

            assert provider is not None
            assert provider.name == "openai"
            assert provider.display_name == "OpenAI"

    @pytest.mark.asyncio
    async def test_get_model_by_name(self, mock_llm_models):
        """Test getting a specific model by name."""
        gpt4_model = mock_llm_models[0]

        with patch.object(llm_service, 'get_model_by_name', return_value=gpt4_model):
            model = await llm_service.get_model_by_name("gpt-4")

            assert model is not None
            assert model.name == "gpt-4"
            assert model.display_name == "GPT-4"
            assert model.provider_id == "openai"

    @pytest.mark.asyncio
    async def test_provider_availability_check(self, mock_llm_providers):
        """Test checking if a provider is available."""
        with patch.object(llm_service, 'is_provider_available', return_value=True):
            available = await llm_service.is_provider_available("openai")

            assert available is True

        with patch.object(llm_service, 'is_provider_available', return_value=False):
            available = await llm_service.is_provider_available("unavailable_provider")

            assert available is False