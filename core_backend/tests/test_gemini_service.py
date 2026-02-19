"""
Tests for the Gemini Service

This module contains unit tests for the centralized Gemini service to ensure
proper functionality and error handling.
"""

import pytest
import asyncio
import os
from unittest.mock import AsyncMock, patch, MagicMock
from backend.services.gemini_service import GeminiService, get_gemini_service, set_gemini_model


class TestGeminiService:
    """Test cases for the GeminiService class."""

    def test_initialization_with_api_key(self):
        """Test service initialization with provided API key."""
        service = GeminiService(api_key="test-key", model="gemini-2.5-flash")
        assert service.api_key == "test-key"
        assert service.model == "gemini-2.5-flash"
        assert service.is_available() is True

    def test_initialization_without_api_key(self):
        """Test service initialization without API key."""
        with patch.dict(os.environ, {}, clear=True):
            service = GeminiService()
            assert service.api_key is None
            assert service.is_available() is False

    @patch.dict(os.environ, {"GEMINI_API_KEY": "env-test-key"})
    def test_initialization_with_env_api_key(self):
        """Test service initialization with environment variable API key."""
        service = GeminiService()
        assert service.api_key == "env-test-key"
        assert service.is_available() is True

    def test_model_update(self):
        """Test updating the model."""
        service = GeminiService(api_key="test-key")
        assert service.model == "gemini-2.5-flash"

        service.update_model("gemini-2.5-pro")
        assert service.model == "gemini-2.5-pro"

    @pytest.mark.asyncio
    async def test_generate_content_success(self):
        """Test successful content generation."""
        service = GeminiService(api_key="test-key")

        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "Generated content here"
                    }]
                }
            }]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await service.generate_content("Test prompt")

            assert result["success"] is True
            assert result["content"] == "Generated content here"
            assert result["model"] == "gemini-2.5-flash"

    @pytest.mark.asyncio
    async def test_generate_content_no_api_key(self):
        """Test content generation without API key."""
        service = GeminiService()  # No API key

        with pytest.raises(Exception, match="Gemini API key not configured"):
            await service.generate_content("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_content_api_error(self):
        """Test content generation with API error."""
        service = GeminiService(api_key="test-key")

        # Mock failed HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            with pytest.raises(Exception, match="Gemini API failed with status 400"):
                await service.generate_content("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_system_prompt(self):
        """Test system prompt generation."""
        service = GeminiService(api_key="test-key")

        with patch.object(service, 'generate_content') as mock_generate:
            mock_generate.return_value = {"content": "System prompt content"}

            result = await service.generate_system_prompt("Create a system prompt")

            assert result == "System prompt content"
            mock_generate.assert_called_once_with(
                prompt="Create a system prompt",
                temperature=0.7,
                max_output_tokens=1000,
                max_input_length=20000
            )

    @pytest.mark.asyncio
    async def test_generate_summary(self):
        """Test summary generation."""
        service = GeminiService(api_key="test-key")

        with patch.object(service, 'generate_content') as mock_generate:
            mock_generate.return_value = {"content": "Summary content"}

            result = await service.generate_summary("Content to summarize")

            assert result == "Summary content"
            mock_generate.assert_called_once_with(
                prompt="Content to summarize",
                temperature=0.3,
                max_output_tokens=500,
                max_input_length=15000
            )

    @pytest.mark.asyncio
    async def test_extract_structured_data(self):
        """Test structured data extraction."""
        service = GeminiService(api_key="test-key")

        with patch.object(service, 'generate_content') as mock_generate:
            mock_generate.return_value = {"content": "Extracted data"}

            result = await service.extract_structured_data("Extract data from this")

            assert result == "Extracted data"
            mock_generate.assert_called_once_with(
                prompt="Extract data from this",
                temperature=0.1,
                max_output_tokens=1500,
                max_input_length=20000
            )

    def test_prompt_truncation(self):
        """Test that long prompts are truncated properly."""
        service = GeminiService(api_key="test-key")
        long_prompt = "A" * 25000  # Longer than max_input_length

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "candidates": [{
                    "content": {"parts": [{"text": "response"}]}
                }]
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            # This should not raise an exception
            asyncio.run(service.generate_content(long_prompt, max_input_length=20000))

            # Verify the request was made with truncated content
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            request_data = call_args[1]["json"]
            sent_text = request_data["contents"][0]["parts"][0]["text"]
            assert len(sent_text) == 20000


class TestGlobalService:
    """Test cases for global service functions."""

    def test_get_gemini_service_singleton(self):
        """Test that get_gemini_service returns the same instance."""
        service1 = get_gemini_service()
        service2 = get_gemini_service()
        assert service1 is service2

    def test_set_gemini_model(self):
        """Test setting the global model."""
        service = get_gemini_service()
        original_model = service.model

        set_gemini_model("gemini-2.5-pro")
        assert service.model == "gemini-2.5-pro"

        # Reset to original
        set_gemini_model(original_model)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_response_candidates(self):
        """Test handling of empty candidates in response."""
        service = GeminiService(api_key="test-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"candidates": []}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            with pytest.raises(Exception, match="No content in Gemini response"):
                await service.generate_content("Test prompt")

    @pytest.mark.asyncio
    async def test_malformed_response_structure(self):
        """Test handling of malformed response structure."""
        service = GeminiService(api_key="test-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"unexpected": "structure"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            with pytest.raises(Exception, match="No content in Gemini response"):
                await service.generate_content("Test prompt")


if __name__ == "__main__":
    pytest.main([__file__])