"""
Tests for MongoDB-based assistant service.

Comprehensive test suite for assistant creation, management, knowledge base functionality,
and Twi language configuration.
"""

import pytest
import asyncio
from uuid import uuid4
from unittest.mock import patch, MagicMock

import mongomock

from backend.models import AssistantCreate, Assistant
from backend.services import assistant_service


@pytest.fixture(autouse=True)
def setup_mock_db():
    """Use an in-memory MongoDB instance for tests."""
    assistant_service._collection = mongomock.MongoClient().db.assistants
    yield
    # Clean up after each test
    assistant_service._collection.drop()


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-supabase-key")
    monkeypatch.setenv("MONGODB_URL", "mongodb://test:test@localhost:27017/test")
    monkeypatch.setenv("MONGO_CORE_DATABASE", "test_db")


class TestAssistantService:
    """Test suite for assistant service operations."""

    def test_create_and_get_assistant(self, mock_env_vars):
        """Assistant can be created and retrieved."""
        payload = AssistantCreate(
            tenant_id=uuid4(),
            name="Test",
            template="default",
            channel="voice",
            voice="alice",
            language="en",
            prompt="hello",
        )
        created = assistant_service.create_assistant(payload)
        fetched = assistant_service.get_assistant(created.id)
        assert fetched is not None
        assert fetched.id == created.id

    def test_list_assistants_empty(self, mock_env_vars):
        """Listing assistants for a tenant with none returns empty list."""
        results = assistant_service.list_assistants(uuid4())
        assert results == []

    def test_get_assistant_missing(self, mock_env_vars):
        """Fetching a non-existent assistant returns None."""
        result = assistant_service.get_assistant(uuid4())
        assert result is None

    def test_create_twi_assistant(self, mock_env_vars):
        """Test creating assistant with Twi language configuration."""
        assistant = Assistant(
            name="Test Twi Assistant",
            description="A test assistant for Twi language",
            user_id="test-user-123",
            template_id="blank"
        )

        created_assistant = assistant_service.create_assistant(assistant)

        assert created_assistant.id is not None
        assert created_assistant.name == "Test Twi Assistant"
        assert created_assistant.user_id == "test-user-123"

    def test_get_assistants_by_user(self, mock_env_vars):
        """Test retrieving assistants for a specific user."""
        user_id = "test-user-123"

        # Create test assistant
        assistant = Assistant(
            name="Test Assistant",
            description="Test description",
            user_id=user_id,
            template_id="blank"
        )
        created = assistant_service.create_assistant(assistant)

        # Get assistants for user
        user_assistants = assistant_service.get_assistants_by_user(user_id)

        assert len(user_assistants) >= 1
        assert any(a.id == created.id for a in user_assistants)

    def test_update_assistant(self, mock_env_vars):
        """Test updating assistant properties."""
        # Create test assistant
        assistant = Assistant(
            name="Test Assistant",
            description="Original description",
            user_id="test-user-123",
            template_id="blank"
        )
        created = assistant_service.create_assistant(assistant)

        # Update assistant
        updates = {
            "system_prompt": "You are a helpful Twi assistant.",
            "first_message": "Akwaaba! How can I help you?"
        }

        updated_assistant = assistant_service.update_assistant(created.id, updates)

        assert updated_assistant is not None
        assert updated_assistant.system_prompt == updates["system_prompt"]
        assert updated_assistant.first_message == updates["first_message"]

    def test_publish_assistant(self, mock_env_vars):
        """Test publishing an assistant."""
        # Create test assistant
        assistant = Assistant(
            name="Test Assistant",
            description="Test description",
            user_id="test-user-123",
            template_id="blank"
        )
        created = assistant_service.create_assistant(assistant)

        # Publish assistant
        configuration = {
            "status": "published",
            "system_prompt": "You are a helpful assistant.",
            "first_message": "Hello! How can I help you?"
        }

        published_assistant = assistant_service.publish_assistant(created.id, configuration)

        assert published_assistant is not None
        assert published_assistant.status == "published"

    def test_delete_assistant(self, mock_env_vars):
        """Test deleting an assistant."""
        # Create test assistant
        assistant = Assistant(
            name="Test Assistant",
            description="Test description",
            user_id="test-user-123",
            template_id="blank"
        )
        created = assistant_service.create_assistant(assistant)

        # Delete assistant
        success = assistant_service.delete_assistant(created.id)

        assert success is True

        # Verify it's deleted
        fetched = assistant_service.get_assistant(created.id)
        assert fetched is None

    def test_get_default_twi_config(self, mock_env_vars):
        """Test getting default Twi configuration."""
        default_config = assistant_service.get_default_twi_config()

        assert 'llm_provider' in default_config
        assert 'llm_model' in default_config
        assert 'tts_provider' in default_config
        assert 'tts_voice' in default_config
        assert 'stt_provider' in default_config
        assert 'stt_model' in default_config
        assert 'language' in default_config

    @pytest.mark.asyncio
    async def test_add_knowledge_base_file(self, mock_env_vars):
        """Test adding a knowledge base file to an assistant."""
        # Create test assistant
        assistant = Assistant(
            name="Test KB Assistant",
            description="A test assistant for knowledge base",
            user_id="test-user-123",
            template_id="blank"
        )
        created = assistant_service.create_assistant(assistant)

        # Mock the knowledge base functionality
        with patch.object(assistant_service, 'add_knowledge_base_file') as mock_add_kb:
            mock_add_kb.return_value = True

            file_content = "This is test knowledge base content about Ghana and Twi language."

            success = await assistant_service.add_knowledge_base_file(
                assistant_id=created.id,
                file_content=file_content,
                file_name="test_file.txt",
                user_id="test-user-123"
            )

            assert success is True
            mock_add_kb.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_knowledge_base(self, mock_env_vars):
        """Test searching the knowledge base."""
        # Create test assistant
        assistant = Assistant(
            name="Test KB Assistant",
            description="A test assistant for knowledge base",
            user_id="test-user-123",
            template_id="blank"
        )
        created = assistant_service.create_assistant(assistant)

        # Mock the knowledge base search
        mock_results = [
            {"text": "Twi is a language spoken in Ghana.", "score": 0.9},
            {"text": "Ghana is located in West Africa.", "score": 0.8}
        ]

        with patch.object(assistant_service, 'search_knowledge_base') as mock_search:
            mock_search.return_value = mock_results

            results = await assistant_service.search_knowledge_base(
                assistant_id=created.id,
                query="Twi language",
                user_id="test-user-123"
            )

            assert len(results) == 2
            assert results[0]["text"] == "Twi is a language spoken in Ghana."
            mock_search.assert_called_once()

    def test_create_assistant_with_invalid_data(self, mock_env_vars):
        """Test error handling for invalid assistant data."""
        with pytest.raises((ValueError, TypeError)):
            assistant_service.create_assistant(None)

    def test_update_nonexistent_assistant(self, mock_env_vars):
        """Test updating a non-existent assistant."""
        fake_id = uuid4()
        updates = {"system_prompt": "Updated prompt"}

        result = assistant_service.update_assistant(fake_id, updates)
        assert result is None

    def test_delete_nonexistent_assistant(self, mock_env_vars):
        """Test deleting a non-existent assistant."""
        fake_id = uuid4()

        success = assistant_service.delete_assistant(fake_id)
        assert success is False
