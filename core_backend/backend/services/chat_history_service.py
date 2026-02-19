"""
Chat History Service

MongoDB-based service for storing and managing LLM chat history with conversation
threading, full-text search, and user statistics.

Features:
- Conversation threading with conversation_id
- Full-text search on messages and responses
- Soft deletes with deleted_at timestamp
- 30-day TTL automatic cleanup
- Pagination and filtering
- User statistics and analytics
- Export capabilities

Created: 2025-10-27
Phase: LLM Improvements - Phase 2 (Chat History Service)
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.collection import Collection
from pymongo.database import Database
from bson import ObjectId
from pydantic import BaseModel, Field
import os
import json

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class ChatMessage(BaseModel):
    """Chat message in conversation."""
    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")


class ChatHistoryItem(BaseModel):
    """Chat history item with all metadata."""
    id: Optional[str] = Field(None, description="Item ID")
    user_id: str = Field(..., description="User ID")
    conversation_id: Optional[str] = Field(None, description="Conversation thread ID")
    model_id: str = Field(..., description="Model used")
    messages: List[ChatMessage] = Field(..., description="All messages in the request")
    response: str = Field(..., description="Assistant's response")
    response_preview: str = Field(..., description="Response preview (first 200 chars)")
    usage: Dict[str, int] = Field(..., description="Token usage")
    cost: float = Field(..., description="Cost in USD")
    processing_time: float = Field(..., description="Processing time in seconds")
    created_at: datetime = Field(..., description="Creation timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Soft delete timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class ChatHistoryListResponse(BaseModel):
    """Paginated chat history list response."""
    items: List[ChatHistoryItem]
    total: int = Field(..., description="Total number of items")
    page: int
    limit: int
    has_more: bool


class UserStatistics(BaseModel):
    """User chat statistics."""
    total_chats: int = Field(..., description="Total number of chats")
    total_cost: float = Field(..., description="Total cost in USD")
    total_tokens: int = Field(..., description="Total tokens used")
    avg_processing_time: float = Field(..., description="Average processing time")
    unique_models: int = Field(..., description="Number of unique models used")
    period_days: int = Field(..., description="Statistics period in days")
    conversations_count: int = Field(0, description="Number of unique conversations")


# ============================================================================
# Chat History Service
# ============================================================================

class ChatHistoryService:
    """
    MongoDB-based chat history service with threading and search.

    Features:
    - Non-blocking saves (doesn't fail chat requests)
    - Conversation threading
    - Full-text search
    - Soft deletes
    - 30-day TTL retention
    - User statistics

    Usage:
        service = ChatHistoryService()
        await service.add_to_history(
            user_id="user_123",
            model_id="llama_32_3b",
            messages=[...],
            response="Hello!",
            usage={"total_tokens": 100},
            cost=0.001,
            processing_time=1.2
        )
    """

    def __init__(self, database: Optional[Database] = None):
        """
        Initialize chat history service.

        Args:
            database: MongoDB database instance (optional, creates if not provided)
        """
        if database is not None:
            self.db = database
        else:
            # Get MongoDB connection from environment
            mongodb_url = os.getenv(
                "MONGODB_URL",
                "mongodb://admin:aawwER444444%25@127.0.0.1:27017/kasaai_core?authSource=admin"
            )
            self.client = MongoClient(mongodb_url)
            self.db = self.client["kasaai_core"]

        self.collection: Collection = self.db["llm_chat_history"]

        # Create indexes on initialization
        self._create_indexes()

        logger.info("ChatHistoryService initialized with MongoDB")

    def _create_indexes(self):
        """Create MongoDB indexes for performance."""
        try:
            # 1. Main query index: user_id + deleted_at + created_at (descending)
            self.collection.create_index(
                [
                    ("user_id", ASCENDING),
                    ("deleted_at", ASCENDING),
                    ("created_at", DESCENDING)
                ],
                name="user_history_index"
            )

            # 2. Full-text search index on messages and response
            self.collection.create_index(
                [
                    ("messages.content", TEXT),
                    ("response", TEXT)
                ],
                name="text_search_index"
            )

            # 3. Model filter index
            self.collection.create_index(
                [
                    ("user_id", ASCENDING),
                    ("model_id", ASCENDING),
                    ("deleted_at", ASCENDING)
                ],
                name="model_filter_index"
            )

            # 4. Conversation thread index
            self.collection.create_index(
                [("conversation_id", ASCENDING)],
                name="conversation_index"
            )

            # 5. TTL index for automatic cleanup (30 days)
            self.collection.create_index(
                [("created_at", ASCENDING)],
                expireAfterSeconds=30 * 24 * 60 * 60,  # 30 days
                name="ttl_index"
            )

            logger.info("Chat history indexes created successfully")

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    async def add_to_history(
        self,
        user_id: str,
        model_id: str,
        messages: List[ChatMessage],
        response: str,
        usage: Dict[str, int],
        cost: float,
        processing_time: float,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add chat interaction to history (non-blocking).

        Args:
            user_id: User ID
            model_id: Model used
            messages: List of messages in the conversation
            response: Assistant's response
            usage: Token usage dict (prompt_tokens, completion_tokens, total_tokens)
            cost: Cost in USD
            processing_time: Processing time in seconds
            conversation_id: Conversation thread ID (creates new if None)
            metadata: Additional metadata

        Returns:
            Item ID of the saved history entry
        """
        try:
            # Generate conversation_id if not provided
            if not conversation_id:
                conversation_id = str(uuid.uuid4())

            # Create response preview (first 200 characters)
            response_preview = response[:200] if len(response) > 200 else response

            # Prepare document
            document = {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "model_id": model_id,
                "messages": [msg.dict() for msg in messages],
                "response": response,
                "response_preview": response_preview,
                "usage": usage,
                "cost": cost,
                "processing_time": processing_time,
                "created_at": datetime.utcnow(),
                "deleted_at": None,
                "metadata": metadata or {}
            }

            # Insert into MongoDB
            result = self.collection.insert_one(document)
            item_id = str(result.inserted_id)

            logger.info(
                f"Chat history saved: user={user_id}, model={model_id}, "
                f"conversation={conversation_id}, item_id={item_id}"
            )

            return item_id

        except Exception as e:
            # Log error but don't raise (non-blocking)
            logger.error(f"Failed to save chat history: {e}")
            return None

    async def get_user_history(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        search_text: Optional[str] = None,
        model_filter: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> ChatHistoryListResponse:
        """
        Get paginated chat history for a user with filters.

        Args:
            user_id: User ID
            page: Page number (1-indexed)
            limit: Items per page (max 100)
            search_text: Full-text search query
            model_filter: Filter by model ID
            conversation_id: Filter by conversation thread

        Returns:
            ChatHistoryListResponse with paginated items
        """
        # Build query
        query = {
            "user_id": user_id,
            "deleted_at": None
        }

        if search_text:
            query["$text"] = {"$search": search_text}

        if model_filter:
            query["model_id"] = model_filter

        if conversation_id:
            query["conversation_id"] = conversation_id

        # Calculate skip
        skip = (page - 1) * limit
        limit = min(limit, 100)  # Max 100 items per page

        # Get total count
        total = self.collection.count_documents(query)

        # Query with pagination
        # Note: For now, include all fields for simplicity
        # In future, can optimize by creating separate model for list view
        cursor = self.collection.find(query).sort("created_at", DESCENDING).skip(skip).limit(limit + 1)

        items = list(cursor)

        # Check if there are more items
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]

        # Convert to Pydantic models
        history_items = []
        for item in items:
            item["id"] = str(item.pop("_id"))
            history_items.append(ChatHistoryItem(**item))

        return ChatHistoryListResponse(
            items=history_items,
            total=total,
            page=page,
            limit=limit,
            has_more=has_more
        )

    async def get_history_item(
        self,
        user_id: str,
        item_id: str
    ) -> Optional[ChatHistoryItem]:
        """
        Get specific chat history item with full details.

        Args:
            user_id: User ID (for security check)
            item_id: Item ID

        Returns:
            ChatHistoryItem or None if not found
        """
        try:
            document = self.collection.find_one({
                "_id": ObjectId(item_id),
                "user_id": user_id,
                "deleted_at": None
            })

            if document:
                document["id"] = str(document.pop("_id"))
                return ChatHistoryItem(**document)

            return None

        except Exception as e:
            logger.error(f"Failed to get history item {item_id}: {e}")
            return None

    async def get_conversation_history(
        self,
        user_id: str,
        conversation_id: str
    ) -> List[ChatHistoryItem]:
        """
        Get all messages in a conversation thread.

        Args:
            user_id: User ID (for security check)
            conversation_id: Conversation thread ID

        Returns:
            List of ChatHistoryItem in chronological order
        """
        cursor = self.collection.find({
            "user_id": user_id,
            "conversation_id": conversation_id,
            "deleted_at": None
        }).sort("created_at", ASCENDING)

        items = []
        for document in cursor:
            document["id"] = str(document.pop("_id"))
            items.append(ChatHistoryItem(**document))

        return items

    async def delete_history_item(
        self,
        user_id: str,
        item_id: str
    ) -> bool:
        """
        Soft delete a chat history item.

        Args:
            user_id: User ID (for security check)
            item_id: Item ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            result = self.collection.update_one(
                {
                    "_id": ObjectId(item_id),
                    "user_id": user_id,
                    "deleted_at": None
                },
                {
                    "$set": {"deleted_at": datetime.utcnow()}
                }
            )

            success = result.modified_count > 0

            if success:
                logger.info(f"Chat history item deleted: item_id={item_id}, user={user_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to delete history item {item_id}: {e}")
            return False

    async def get_user_statistics(
        self,
        user_id: str,
        days: int = 30
    ) -> UserStatistics:
        """
        Get aggregated statistics for a user.

        Args:
            user_id: User ID
            days: Number of days to look back (default: 30)

        Returns:
            UserStatistics with aggregated data
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # Aggregation pipeline
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "deleted_at": None,
                        "created_at": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_chats": {"$sum": 1},
                        "total_cost": {"$sum": "$cost"},
                        "total_tokens": {"$sum": "$usage.total_tokens"},
                        "avg_processing_time": {"$avg": "$processing_time"},
                        "models_used": {"$addToSet": "$model_id"},
                        "conversations": {"$addToSet": "$conversation_id"}
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))

            if result:
                stats = result[0]
                return UserStatistics(
                    total_chats=stats.get("total_chats", 0),
                    total_cost=stats.get("total_cost", 0.0),
                    total_tokens=stats.get("total_tokens", 0),
                    avg_processing_time=stats.get("avg_processing_time", 0.0),
                    unique_models=len(stats.get("models_used", [])),
                    conversations_count=len(stats.get("conversations", [])),
                    period_days=days
                )

            return UserStatistics(
                total_chats=0,
                total_cost=0.0,
                total_tokens=0,
                avg_processing_time=0.0,
                unique_models=0,
                conversations_count=0,
                period_days=days
            )

        except Exception as e:
            logger.error(f"Failed to get user statistics: {e}")
            return UserStatistics(
                total_chats=0,
                total_cost=0.0,
                total_tokens=0,
                avg_processing_time=0.0,
                unique_models=0,
                conversations_count=0,
                period_days=days
            )

    async def export_user_history(
        self,
        user_id: str,
        format: str = "json",
        conversation_id: Optional[str] = None
    ) -> Any:
        """
        Export user's chat history in various formats.

        Args:
            user_id: User ID
            format: Export format ("json", "csv", "markdown")
            conversation_id: Optional conversation filter

        Returns:
            Exported data in requested format
        """
        # Build query
        query = {
            "user_id": user_id,
            "deleted_at": None
        }

        if conversation_id:
            query["conversation_id"] = conversation_id

        # Get all items
        cursor = self.collection.find(query).sort("created_at", ASCENDING)
        items = list(cursor)

        if format == "json":
            # Convert ObjectId to string
            for item in items:
                item["_id"] = str(item["_id"])
                if "deleted_at" in item and item["deleted_at"]:
                    item["deleted_at"] = item["deleted_at"].isoformat()
                item["created_at"] = item["created_at"].isoformat()
            return items

        elif format == "csv":
            # Convert to CSV format
            csv_rows = []
            csv_rows.append("timestamp,conversation_id,model,user_message,response,tokens,cost")

            for item in items:
                timestamp = item["created_at"].isoformat()
                conv_id = item["conversation_id"]
                model = item["model_id"]
                user_msg = " ".join([msg["content"] for msg in item["messages"] if msg["role"] == "user"])
                response = item["response"].replace('"', '""')  # Escape quotes
                tokens = item["usage"].get("total_tokens", 0)
                cost = item["cost"]

                csv_rows.append(f'"{timestamp}","{conv_id}","{model}","{user_msg}","{response}",{tokens},{cost}')

            return "\n".join(csv_rows)

        elif format == "markdown":
            # Convert to Markdown format
            md_lines = []
            md_lines.append(f"# Chat History Export")
            md_lines.append(f"**User:** {user_id}")
            md_lines.append(f"**Exported:** {datetime.utcnow().isoformat()}")
            md_lines.append("")

            for item in items:
                md_lines.append(f"## Conversation: {item['conversation_id']}")
                md_lines.append(f"**Model:** {item['model_id']} | **Time:** {item['created_at'].isoformat()}")
                md_lines.append("")

                for msg in item["messages"]:
                    role = msg["role"].title()
                    content = msg["content"]
                    md_lines.append(f"**{role}:** {content}")
                    md_lines.append("")

                md_lines.append(f"**Assistant:** {item['response']}")
                md_lines.append("")
                md_lines.append(f"*Tokens: {item['usage'].get('total_tokens', 0)} | Cost: ${item['cost']:.4f}*")
                md_lines.append("")
                md_lines.append("---")
                md_lines.append("")

            return "\n".join(md_lines)

        else:
            raise ValueError(f"Unsupported export format: {format}")


# ============================================================================
# Singleton Instance
# ============================================================================

_chat_history_service_instance: Optional[ChatHistoryService] = None


def get_chat_history_service() -> ChatHistoryService:
    """
    Get singleton instance of ChatHistoryService.

    Returns:
        Initialized ChatHistoryService instance
    """
    global _chat_history_service_instance

    if _chat_history_service_instance is None:
        _chat_history_service_instance = ChatHistoryService()
        logger.info("ChatHistoryService singleton initialized")

    return _chat_history_service_instance
