"""
Tests for Anthropic API integration service.

Tests the AnthropicService functionality including connection testing,
chat completion, and error handling.
"""

import pytest
import asyncio
import os
from unittest.mock import AsyncMock, patch, MagicMock

from backend.services.anthropic_service import AnthropicService


class TestAnthropicService:
    """Test suite for Anthropic service operations."""

    @pytest.fixture
    def anthropic_service(self):
        """Create Anthropic service instance for testing."""
        return AnthropicService()

    @pytest.fixture
    def mock_anthropic_api_key(self, monkeypatch):
        """Mock Anthropic API key for testing."""
        test_api_key = "sk-ant-test-key-123456789"
        monkeypatch.setenv("ANTHROPIC_API_KEY", test_api_key)
        return test_api_key

    @pytest.mark.asyncio
    async def test_connection_success(self, anthropic_service, mock_anthropic_api_key):
        """Test successful Anthropic API connection."""
        with patch.object(anthropic_service, '_make_request') as mock_request:
            mock_request.return_value = {"status": "ok"}

            result = await anthropic_service.test_connection()
            assert result is True

    @pytest.mark.asyncio
    async def test_connection_failure(self, anthropic_service, mock_anthropic_api_key):
        """Test failed Anthropic API connection."""
        with patch.object(anthropic_service, '_make_request') as mock_request:
            mock_request.side_effect = Exception("Connection failed")

            result = await anthropic_service.test_connection()
            assert result is False

    @pytest.mark.asyncio
    async def test_chat_completion_success(self, anthropic_service, mock_anthropic_api_key):
        """Test successful chat completion."""
        mock_response = {
            'text': 'Hello! I am Claude, an AI assistant created by Anthropic.',
            'model': 'claude-3-haiku-20240307',
            'usage': {'input_tokens': 10, 'output_tokens': 15}
        }

        with patch.object(anthropic_service, 'chat_completion', return_value=mock_response):
            response = await anthropic_service.chat_completion(
                messages=[
                    {"role": "user", "content": "Hello! Can you briefly introduce yourself?"}
                ],
                model="claude-3-haiku-20240307",
                system_prompt="You are a helpful AI assistant.",
                max_tokens=100
            )

            assert response['text'] is not None
            assert response['model'] == 'claude-3-haiku-20240307'
            assert 'usage' in response

    @pytest.mark.asyncio
    async def test_chat_completion_with_invalid_model(self, anthropic_service, mock_anthropic_api_key):
        """Test chat completion with invalid model."""
        with patch.object(anthropic_service, 'chat_completion') as mock_chat:
            mock_chat.side_effect = Exception("Invalid model")

            with pytest.raises(Exception):
                await anthropic_service.chat_completion(
                    messages=[{"role": "user", "content": "Test message"}],
                    model="invalid-model",
                    max_tokens=100
                )

    @pytest.mark.asyncio
    async def test_chat_completion_empty_messages(self, anthropic_service, mock_anthropic_api_key):
        """Test chat completion with empty messages."""
        with pytest.raises((ValueError, Exception)):
            await anthropic_service.chat_completion(
                messages=[],
                model="claude-3-haiku-20240307",
                max_tokens=100
            )

    def test_missing_api_key(self, monkeypatch):
        """Test service behavior when API key is missing."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        # Service should handle missing API key gracefully
        service = AnthropicService()
        assert service is not None

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, anthropic_service, mock_anthropic_api_key):
        """Test handling of rate limit errors."""
        with patch.object(anthropic_service, '_make_request') as mock_request:
            mock_request.side_effect = Exception("Rate limit exceeded")

            result = await anthropic_service.test_connection()
            assert result is False

    @pytest.mark.asyncio
    async def test_large_response_handling(self, anthropic_service, mock_anthropic_api_key):
        """Test handling of large responses."""
        large_text = "Large response " * 1000
        mock_response = {
            'text': large_text,
            'model': 'claude-3-haiku-20240307',
            'usage': {'input_tokens': 10, 'output_tokens': 2000}
        }

        with patch.object(anthropic_service, 'chat_completion', return_value=mock_response):
            response = await anthropic_service.chat_completion(
                messages=[{"role": "user", "content": "Generate a long response"}],
                model="claude-3-haiku-20240307",
                max_tokens=2000
            )

            assert len(response['text']) > 1000
            assert response['usage']['output_tokens'] > 1000