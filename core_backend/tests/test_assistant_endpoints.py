"""Tests for assistant endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.routes.voice_engine import app
from backend.models import Assistant

client = TestClient(app)


@pytest.fixture
def mock_assistant():
    """Mock assistant data."""
    return {
        "id": "test-assistant-123",
        "name": "Test Assistant",
        "description": "A test assistant",
        "user_id": "user-123",
        "template_id": "blank",
        "status": "draft",
        "llm_provider": "",
        "llm_model": "",
        "first_message_mode": "assistant_first",
        "first_message": "",
        "system_prompt": "",
        "tts_provider": "",
        "tts_voice": "",
        "language": "en",
        "country": "US",
        "background_sound": "default",
        "background_sound_url": "",
        "input_min_characters": 30,
        "punctuation_boundaries": "",
        "stability": 0.5,
        "clarity_similarity": 0.75,
        "speed": 1.0,
        "style_exaggeration": 0.0,
        "optimize_streaming_latency": 0.0,
        "stt_provider": "",
        "stt_model": "",
        "background_denoising": False,
        "confidence_threshold": 0.4,
        "use_numerals": False,
        "knowledge_base_files": [],
        "metadata": {},
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }


class TestAssistantEndpoints:
    """Test assistant endpoints."""

    @patch('backend.routes.voice_engine.assistant_service')
    def test_create_assistant(self, mock_service, mock_assistant):
        """Test creating an assistant."""
        # Mock the service response
        mock_service.create_assistant.return_value = Assistant(**mock_assistant)
        
        # Test data
        create_data = {
            "name": "Test Assistant",
            "description": "A test assistant",
            "user_id": "user-123",
            "template_id": "blank"
        }
        
        # Make request
        response = client.post("/voice/assistants", json=create_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Assistant"
        assert data["user_id"] == "user-123"
        assert data["status"] == "draft"
        
        # Verify service was called
        mock_service.create_assistant.assert_called_once()

    @patch('backend.routes.voice_engine.assistant_service')
    def test_get_assistants(self, mock_service, mock_assistant):
        """Test getting assistants for a user."""
        # Mock the service response
        mock_service.get_assistants_by_user.return_value = [Assistant(**mock_assistant)]
        
        # Make request
        response = client.get("/voice/assistants?user_id=user-123")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Assistant"
        
        # Verify service was called
        mock_service.get_assistants_by_user.assert_called_once_with("user-123")

    @patch('backend.routes.voice_engine.assistant_service')
    def test_get_published_assistants(self, mock_service, mock_assistant):
        """Test getting published assistants."""
        # Mock the service response
        mock_assistant["status"] = "published"
        mock_service.get_published_assistants.return_value = [Assistant(**mock_assistant)]
        
        # Make request
        response = client.get("/voice/assistants?user_id=user-123&status=published")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "published"
        
        # Verify service was called
        mock_service.get_published_assistants.assert_called_once_with("user-123")

    @patch('backend.routes.voice_engine.assistant_service')
    def test_get_assistant(self, mock_service, mock_assistant):
        """Test getting a specific assistant."""
        # Mock the service response
        mock_service.get_assistant.return_value = Assistant(**mock_assistant)
        
        # Make request
        response = client.get("/voice/assistants/test-assistant-123")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-assistant-123"
        assert data["name"] == "Test Assistant"
        
        # Verify service was called
        mock_service.get_assistant.assert_called_once_with("test-assistant-123")

    @patch('backend.routes.voice_engine.assistant_service')
    def test_get_assistant_not_found(self, mock_service):
        """Test getting a non-existent assistant."""
        # Mock the service response
        mock_service.get_assistant.return_value = None
        
        # Make request
        response = client.get("/voice/assistants/non-existent")
        
        # Assertions
        assert response.status_code == 404
        assert "Assistant not found" in response.json()["detail"]

    @patch('backend.routes.voice_engine.assistant_service')
    def test_update_assistant(self, mock_service, mock_assistant):
        """Test updating an assistant."""
        # Mock the service response
        mock_assistant["name"] = "Updated Assistant"
        mock_service.update_assistant.return_value = Assistant(**mock_assistant)
        
        # Test data
        update_data = {
            "name": "Updated Assistant",
            "description": "Updated description"
        }
        
        # Make request
        response = client.put("/voice/assistants/test-assistant-123", json=update_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Assistant"
        assert data["description"] == "Updated description"
        
        # Verify service was called
        mock_service.update_assistant.assert_called_once()

    @patch('backend.routes.voice_engine.assistant_service')
    def test_publish_assistant(self, mock_service, mock_assistant):
        """Test publishing an assistant."""
        # Mock the service response
        mock_assistant["status"] = "published"
        mock_service.publish_assistant.return_value = Assistant(**mock_assistant)
        
        # Test data
        publish_data = {
            "llm_provider": "openai",
            "llm_model": "gpt-4o",
            "tts_provider": "elevenlabs",
            "tts_voice": "adam"
        }
        
        # Make request
        response = client.post("/voice/assistants/test-assistant-123/publish", json=publish_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"
        
        # Verify service was called
        mock_service.publish_assistant.assert_called_once()

    @patch('backend.routes.voice_engine.assistant_service')
    def test_delete_assistant(self, mock_service):
        """Test deleting an assistant."""
        # Mock the service response
        mock_service.delete_assistant.return_value = True
        
        # Make request
        response = client.delete("/voice/assistants/test-assistant-123")
        
        # Assertions
        assert response.status_code == 200
        assert response.json()["message"] == "Assistant deleted successfully"
        
        # Verify service was called
        mock_service.delete_assistant.assert_called_once_with("test-assistant-123")

    @patch('backend.routes.voice_engine.assistant_service')
    def test_delete_assistant_not_found(self, mock_service):
        """Test deleting a non-existent assistant."""
        # Mock the service response
        mock_service.delete_assistant.return_value = False
        
        # Make request
        response = client.delete("/voice/assistants/non-existent")
        
        # Assertions
        assert response.status_code == 404
        assert "Assistant not found" in response.json()["detail"]
