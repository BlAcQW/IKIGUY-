"""
Conversation Manager

Manages conversation state persistence in MongoDB.
Handles CRUD operations for conversations and turns.

Author: KasaAI Team
Date: 2025-11-26
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from .models import (
    ConversationState,
    ConversationTurn,
    ConversationConfig,
    ConversationStatus,
    TurnRole,
)

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages conversation persistence and retrieval.

    Stores conversations in MongoDB with proper indexing.
    """

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        collection_name: str = "conversations"
    ):
        """
        Initialize the manager.

        Args:
            db: MongoDB database connection
            collection_name: Name of the conversations collection
        """
        self.db = db
        self.collection = db[collection_name]
        self._indexes_created = False

    async def ensure_indexes(self) -> None:
        """Create MongoDB indexes for performance."""
        if self._indexes_created:
            return

        try:
            # Index on user_id for listing user's conversations
            await self.collection.create_index(
                [("user_id", 1)],
                name="user_id_index"
            )

            # Index on organization_id
            await self.collection.create_index(
                [("organization_id", 1)],
                name="organization_index"
            )

            # Compound index for user + status
            await self.collection.create_index(
                [("user_id", 1), ("status", 1)],
                name="user_status_index"
            )

            # Index on updated_at for sorting
            await self.collection.create_index(
                [("updated_at", -1)],
                name="updated_at_index"
            )

            # TTL index for auto-cleanup of old conversations (optional)
            # Conversations older than 30 days will be deleted
            # await self.collection.create_index(
            #     [("updated_at", 1)],
            #     expireAfterSeconds=30*24*60*60,
            #     name="ttl_index"
            # )

            self._indexes_created = True
            logger.info("Conversation indexes created")

        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    async def create_conversation(
        self,
        user_id: str,
        organization_id: str = "default",
        config: Optional[ConversationConfig] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationState:
        """
        Create a new conversation.

        Args:
            user_id: User who owns the conversation
            organization_id: Organization context
            config: Conversation configuration
            title: Optional title
            metadata: Optional metadata

        Returns:
            Created ConversationState
        """
        await self.ensure_indexes()

        conversation = ConversationState(
            id=f"conv_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            organization_id=organization_id,
            config=config or ConversationConfig(),
            title=title,
            metadata=metadata or {},
        )

        await self.collection.insert_one(conversation.dict())
        logger.info(f"Created conversation {conversation.id} for user {user_id}")

        return conversation

    async def get_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[ConversationState]:
        """
        Get a conversation by ID.

        Args:
            conversation_id: Conversation ID
            user_id: Optional user ID for access control

        Returns:
            ConversationState or None if not found
        """
        query = {"id": conversation_id}
        if user_id:
            query["user_id"] = user_id

        doc = await self.collection.find_one(query)

        if not doc:
            return None

        doc.pop("_id", None)
        return ConversationState(**doc)

    async def update_conversation(
        self,
        conversation_id: str,
        updates: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Optional[ConversationState]:
        """
        Update a conversation.

        Args:
            conversation_id: Conversation ID
            updates: Fields to update
            user_id: Optional user ID for access control

        Returns:
            Updated ConversationState or None
        """
        query = {"id": conversation_id}
        if user_id:
            query["user_id"] = user_id

        # Always update timestamp
        updates["updated_at"] = datetime.utcnow()

        result = await self.collection.update_one(
            query,
            {"$set": updates}
        )

        if result.modified_count == 0:
            return None

        return await self.get_conversation(conversation_id, user_id)

    async def add_turn(
        self,
        conversation_id: str,
        turn: ConversationTurn,
        user_id: Optional[str] = None,
    ) -> Optional[ConversationState]:
        """
        Add a turn to a conversation.

        Args:
            conversation_id: Conversation ID
            turn: Turn to add
            user_id: Optional user ID for access control

        Returns:
            Updated ConversationState or None
        """
        query = {"id": conversation_id}
        if user_id:
            query["user_id"] = user_id

        result = await self.collection.update_one(
            query,
            {
                "$push": {"turns": turn.dict()},
                "$inc": {
                    "total_turns": 1,
                    "total_cost_usd": turn.cost_usd
                },
                "$set": {
                    "last_turn_at": turn.created_at,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            return None

        return await self.get_conversation(conversation_id, user_id)

    async def list_conversations(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
        status: Optional[ConversationStatus] = None,
        limit: int = 20,
        skip: int = 0,
    ) -> List[ConversationState]:
        """
        List conversations for a user.

        Args:
            user_id: User ID
            organization_id: Optional organization filter
            status: Optional status filter
            limit: Max results
            skip: Offset for pagination

        Returns:
            List of ConversationState (without full turn history)
        """
        query = {"user_id": user_id}

        if organization_id:
            query["organization_id"] = organization_id

        if status:
            query["status"] = status.value

        cursor = self.collection.find(
            query,
            # Exclude full turns for list view
            {"turns": {"$slice": -1}}  # Only last turn
        ).sort("updated_at", -1).skip(skip).limit(limit)

        conversations = []
        async for doc in cursor:
            doc.pop("_id", None)
            conversations.append(ConversationState(**doc))

        return conversations

    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: Optional user ID for access control

        Returns:
            True if deleted, False otherwise
        """
        query = {"id": conversation_id}
        if user_id:
            query["user_id"] = user_id

        result = await self.collection.delete_one(query)

        if result.deleted_count > 0:
            logger.info(f"Deleted conversation {conversation_id}")
            return True

        return False

    async def end_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[ConversationState]:
        """
        Mark a conversation as completed.

        Args:
            conversation_id: Conversation ID
            user_id: Optional user ID for access control

        Returns:
            Updated ConversationState or None
        """
        return await self.update_conversation(
            conversation_id,
            {"status": ConversationStatus.COMPLETED.value},
            user_id
        )

    async def get_conversation_summary(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get conversation summary (without full history).

        Args:
            conversation_id: Conversation ID
            user_id: Optional user ID for access control

        Returns:
            Summary dict or None
        """
        conversation = await self.get_conversation(conversation_id, user_id)

        if not conversation:
            return None

        return {
            "id": conversation.id,
            "title": conversation.title,
            "status": conversation.status.value,
            "total_turns": conversation.total_turns,
            "total_cost_usd": conversation.total_cost_usd,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "last_turn_at": conversation.last_turn_at.isoformat() if conversation.last_turn_at else None,
            "config": {
                "llm_model": conversation.config.llm_model,
                "asr_provider": conversation.config.asr_provider,
                "tts_provider": conversation.config.tts_provider,
            }
        }

    async def search_conversations(
        self,
        user_id: str,
        query_text: str,
        limit: int = 10,
    ) -> List[ConversationState]:
        """
        Search conversations by content.

        Args:
            user_id: User ID
            query_text: Search text
            limit: Max results

        Returns:
            List of matching ConversationState
        """
        # Text search in turn content
        cursor = self.collection.find(
            {
                "user_id": user_id,
                "$or": [
                    {"title": {"$regex": query_text, "$options": "i"}},
                    {"turns.content": {"$regex": query_text, "$options": "i"}}
                ]
            }
        ).sort("updated_at", -1).limit(limit)

        conversations = []
        async for doc in cursor:
            doc.pop("_id", None)
            conversations.append(ConversationState(**doc))

        return conversations

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get conversation statistics for a user.

        Args:
            user_id: User ID

        Returns:
            Statistics dict
        """
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": None,
                "total_conversations": {"$sum": 1},
                "total_turns": {"$sum": "$total_turns"},
                "total_cost": {"$sum": "$total_cost_usd"},
                "active_conversations": {
                    "$sum": {"$cond": [{"$eq": ["$status", "active"]}, 1, 0]}
                }
            }}
        ]

        result = await self.collection.aggregate(pipeline).to_list(1)

        if result:
            stats = result[0]
            stats.pop("_id", None)
            return stats

        return {
            "total_conversations": 0,
            "total_turns": 0,
            "total_cost": 0.0,
            "active_conversations": 0
        }
