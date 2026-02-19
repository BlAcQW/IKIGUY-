"""
Tests for conversation manager.

Tests MongoDB persistence and CRUD operations.
"""

import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from motor.motor_asyncio import AsyncIOMotorDatabase

from apps.shared.conversation.manager import ConversationManager
from apps.shared.conversation.models import (
    ConversationState,
    ConversationTurn,
    ConversationConfig,
    ConversationStatus,
    TurnRole,
)


@pytest_asyncio.fixture
async def mock_db():
    """Create a mock MongoDB database."""
    db = MagicMock(spec=AsyncIOMotorDatabase)
    collection = AsyncMock()
    db.__getitem__ = MagicMock(return_value=collection)
    return db, collection


@pytest_asyncio.fixture
async def manager(mock_db):
    """Create a conversation manager with mock database."""
    db, _ = mock_db
    return ConversationManager(db)


class TestConversationManager:
    """Tests for ConversationManager class."""

    @pytest.mark.asyncio
    async def test_ensure_indexes(self, mock_db):
        """Test index creation."""
        db, collection = mock_db
        manager = ConversationManager(db)

        await manager.ensure_indexes()

        # Should create indexes
        assert collection.create_index.call_count >= 4
        assert manager._indexes_created is True

        # Calling again should be a no-op
        collection.create_index.reset_mock()
        await manager.ensure_indexes()
        assert collection.create_index.call_count == 0

    @pytest.mark.asyncio
    async def test_create_conversation(self, mock_db):
        """Test creating a new conversation."""
        db, collection = mock_db
        collection.insert_one = AsyncMock()
        manager = ConversationManager(db)

        result = await manager.create_conversation(
            user_id="user_123",
            organization_id="org_456",
            title="Test Chat",
            metadata={"source": "api"},
        )

        assert result.user_id == "user_123"
        assert result.organization_id == "org_456"
        assert result.title == "Test Chat"
        assert result.status == ConversationStatus.ACTIVE
        assert result.id.startswith("conv_")
        collection.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_conversation_with_config(self, mock_db):
        """Test creating conversation with custom config."""
        db, collection = mock_db
        collection.insert_one = AsyncMock()
        manager = ConversationManager(db)

        config = ConversationConfig(
            llm_model="gemini-1.5-pro",
            tts_provider="openai",
            system_prompt="You are a tutor.",
        )

        result = await manager.create_conversation(
            user_id="user_123",
            config=config,
        )

        assert result.config.llm_model == "gemini-1.5-pro"
        assert result.config.tts_provider == "openai"
        assert result.config.system_prompt == "You are a tutor."

    @pytest.mark.asyncio
    async def test_get_conversation_found(self, mock_db):
        """Test getting an existing conversation."""
        db, collection = mock_db

        # Mock find_one to return a conversation document
        doc = {
            "id": "conv_test123",
            "user_id": "user_123",
            "organization_id": "default",
            "status": "active",
            "config": {
                "asr_provider": "faster_whisper_large",
                "llm_model": "gemini-2.5-flash",
                "tts_provider": "coqui_xtts",
            },
            "turns": [],
            "title": "Test",
            "tags": [],
            "metadata": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "total_cost_usd": 0.0,
            "total_turns": 0,
            "_id": "mongo_id",
        }
        collection.find_one = AsyncMock(return_value=doc)
        manager = ConversationManager(db)

        result = await manager.get_conversation("conv_test123")

        assert result is not None
        assert result.id == "conv_test123"
        assert result.user_id == "user_123"

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, mock_db):
        """Test getting a non-existent conversation."""
        db, collection = mock_db
        collection.find_one = AsyncMock(return_value=None)
        manager = ConversationManager(db)

        result = await manager.get_conversation("conv_nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_conversation_with_user_access_control(self, mock_db):
        """Test getting conversation with user access control."""
        db, collection = mock_db
        collection.find_one = AsyncMock(return_value=None)
        manager = ConversationManager(db)

        await manager.get_conversation("conv_123", user_id="user_456")

        # Should include user_id in query
        call_args = collection.find_one.call_args[0][0]
        assert call_args["id"] == "conv_123"
        assert call_args["user_id"] == "user_456"

    @pytest.mark.asyncio
    async def test_update_conversation(self, mock_db):
        """Test updating a conversation."""
        db, collection = mock_db

        # Mock update and get
        collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        doc = {
            "id": "conv_test123",
            "user_id": "user_123",
            "organization_id": "default",
            "status": "active",
            "config": {},
            "turns": [],
            "title": "Updated Title",
            "tags": [],
            "metadata": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "total_cost_usd": 0.0,
            "total_turns": 0,
        }
        collection.find_one = AsyncMock(return_value=doc)
        manager = ConversationManager(db)

        result = await manager.update_conversation(
            "conv_test123",
            {"title": "Updated Title"},
        )

        assert result is not None
        collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_turn(self, mock_db):
        """Test adding a turn to conversation."""
        db, collection = mock_db

        collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        doc = {
            "id": "conv_test123",
            "user_id": "user_123",
            "organization_id": "default",
            "status": "active",
            "config": {},
            "turns": [],
            "title": None,
            "tags": [],
            "metadata": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "total_cost_usd": 0.001,
            "total_turns": 1,
        }
        collection.find_one = AsyncMock(return_value=doc)
        manager = ConversationManager(db)

        turn = ConversationTurn(
            id="turn_001",
            conversation_id="conv_test123",
            role=TurnRole.USER,
            content="Hello",
            cost_usd=0.001,
        )

        result = await manager.add_turn("conv_test123", turn)

        assert result is not None
        collection.update_one.assert_called_once()

        # Verify the update operation
        call_args = collection.update_one.call_args
        update_doc = call_args[0][1]

        assert "$push" in update_doc
        assert "$inc" in update_doc
        assert "$set" in update_doc

    @pytest.mark.asyncio
    async def test_delete_conversation(self, mock_db):
        """Test deleting a conversation."""
        db, collection = mock_db
        collection.delete_one = AsyncMock(
            return_value=MagicMock(deleted_count=1)
        )
        manager = ConversationManager(db)

        result = await manager.delete_conversation("conv_test123")

        assert result is True
        collection.delete_one.assert_called_once_with({"id": "conv_test123"})

    @pytest.mark.asyncio
    async def test_delete_conversation_not_found(self, mock_db):
        """Test deleting a non-existent conversation."""
        db, collection = mock_db
        collection.delete_one = AsyncMock(
            return_value=MagicMock(deleted_count=0)
        )
        manager = ConversationManager(db)

        result = await manager.delete_conversation("conv_nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_end_conversation(self, mock_db):
        """Test ending a conversation."""
        db, collection = mock_db

        collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        doc = {
            "id": "conv_test123",
            "user_id": "user_123",
            "organization_id": "default",
            "status": "completed",
            "config": {},
            "turns": [],
            "title": None,
            "tags": [],
            "metadata": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "total_cost_usd": 0.0,
            "total_turns": 0,
        }
        collection.find_one = AsyncMock(return_value=doc)
        manager = ConversationManager(db)

        result = await manager.end_conversation("conv_test123")

        assert result is not None

        # Verify status update
        call_args = collection.update_one.call_args[0][1]
        assert call_args["$set"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_conversation_summary(self, mock_db):
        """Test getting conversation summary."""
        db, collection = mock_db

        doc = {
            "id": "conv_test123",
            "user_id": "user_123",
            "organization_id": "default",
            "status": "active",
            "config": {
                "asr_provider": "faster_whisper_large",
                "llm_model": "gemini-2.5-flash",
                "tts_provider": "coqui_xtts",
            },
            "turns": [],
            "title": "Test Chat",
            "tags": [],
            "metadata": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_turn_at": None,
            "total_cost_usd": 0.005,
            "total_turns": 4,
        }
        collection.find_one = AsyncMock(return_value=doc)
        manager = ConversationManager(db)

        result = await manager.get_conversation_summary("conv_test123")

        assert result is not None
        assert result["id"] == "conv_test123"
        assert result["title"] == "Test Chat"
        assert result["total_turns"] == 4
        assert result["total_cost_usd"] == 0.005
        assert "config" in result

    @pytest.mark.asyncio
    async def test_get_user_stats(self, mock_db):
        """Test getting user statistics."""
        db, collection = mock_db

        # Mock aggregation result
        agg_result = [{
            "total_conversations": 10,
            "total_turns": 50,
            "total_cost": 0.25,
            "active_conversations": 3,
            "_id": None,
        }]

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=agg_result)
        collection.aggregate = MagicMock(return_value=mock_cursor)
        manager = ConversationManager(db)

        result = await manager.get_user_stats("user_123")

        assert result["total_conversations"] == 10
        assert result["total_turns"] == 50
        assert result["total_cost"] == 0.25
        assert result["active_conversations"] == 3

    @pytest.mark.asyncio
    async def test_get_user_stats_no_data(self, mock_db):
        """Test getting user stats with no data."""
        db, collection = mock_db

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        collection.aggregate = MagicMock(return_value=mock_cursor)
        manager = ConversationManager(db)

        result = await manager.get_user_stats("user_new")

        assert result["total_conversations"] == 0
        assert result["total_turns"] == 0
        assert result["total_cost"] == 0.0
        assert result["active_conversations"] == 0


class TestConversationManagerListAndSearch:
    """Tests for list and search operations."""

    @pytest.mark.asyncio
    async def test_list_conversations(self, mock_db):
        """Test listing user conversations."""
        db, collection = mock_db

        docs = [
            {
                "id": "conv_001",
                "user_id": "user_123",
                "organization_id": "default",
                "status": "active",
                "config": {},
                "turns": [{
                    "id": "turn_last",
                    "conversation_id": "conv_001",
                    "role": "user",
                    "content": "Last message",
                    "created_at": datetime.utcnow(),
                    "cost_usd": 0.0,
                }],
                "title": "Chat 1",
                "tags": [],
                "metadata": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "total_cost_usd": 0.0,
                "total_turns": 5,
            },
            {
                "id": "conv_002",
                "user_id": "user_123",
                "organization_id": "default",
                "status": "completed",
                "config": {},
                "turns": [],
                "title": "Chat 2",
                "tags": [],
                "metadata": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "total_cost_usd": 0.0,
                "total_turns": 3,
            },
        ]

        # Mock cursor with async iteration
        class MockCursor:
            def __init__(self, items):
                self._items = items
                self._index = 0

            def sort(self, *args):
                return self

            def skip(self, n):
                return self

            def limit(self, n):
                return self

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self._index >= len(self._items):
                    raise StopAsyncIteration
                item = self._items[self._index]
                self._index += 1
                return item

        collection.find = MagicMock(return_value=MockCursor(docs))
        manager = ConversationManager(db)

        result = await manager.list_conversations("user_123")

        assert len(result) == 2
        assert result[0].id == "conv_001"
        assert result[1].id == "conv_002"

    @pytest.mark.asyncio
    async def test_search_conversations(self, mock_db):
        """Test searching conversations."""
        db, collection = mock_db

        docs = [
            {
                "id": "conv_001",
                "user_id": "user_123",
                "organization_id": "default",
                "status": "active",
                "config": {},
                "turns": [],
                "title": "Python Tutorial",
                "tags": [],
                "metadata": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "total_cost_usd": 0.0,
                "total_turns": 3,
            },
        ]

        class MockCursor:
            def __init__(self, items):
                self._items = items
                self._index = 0

            def sort(self, *args):
                return self

            def limit(self, n):
                return self

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self._index >= len(self._items):
                    raise StopAsyncIteration
                item = self._items[self._index]
                self._index += 1
                return item

        collection.find = MagicMock(return_value=MockCursor(docs))
        manager = ConversationManager(db)

        result = await manager.search_conversations("user_123", "Python")

        assert len(result) == 1
        assert result[0].title == "Python Tutorial"

        # Verify search query
        call_args = collection.find.call_args[0][0]
        assert call_args["user_id"] == "user_123"
        assert "$or" in call_args
