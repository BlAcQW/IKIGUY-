"""
Discussion service for community-wide discussions.
"""

from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException, status

from app.db.mongodb import get_database
from app.models.discussion import (
    DiscussionCreate,
    DiscussionResponse,
    DiscussionListResponse,
)
import logging

logger = logging.getLogger(__name__)


async def create_discussion(
    discussion_data: DiscussionCreate, creator_id: str
) -> DiscussionResponse:
    """
    Create a new discussion.

    Args:
        discussion_data: Discussion creation data.
        creator_id: ID of the user creating the discussion.

    Returns:
        DiscussionResponse: Created discussion data.
    """
    db = get_database()

    # Get creator info
    creator = await db.users.find_one({"_id": ObjectId(creator_id)})
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get devotional info if linked
    devotional_title = None
    if discussion_data.devotional_id:
        devotional = await db.devotionals.find_one(
            {"_id": ObjectId(discussion_data.devotional_id)}
        )
        if devotional:
            devotional_title = devotional.get("title")

    # Create discussion document
    discussion_dict = {
        "title": discussion_data.title,
        "description": discussion_data.description,
        "devotional_id": ObjectId(discussion_data.devotional_id)
        if discussion_data.devotional_id
        else None,
        "devotional_title": devotional_title,
        "scripture_reference": discussion_data.scripture_reference,
        "author_id": ObjectId(creator_id),
        "author_name": creator.get("name", "Unknown"),
        "author_avatar": creator.get("avatar_url"),
        "participants_count": 1,  # Creator is first participant
        "messages_count": 0,
        "category": discussion_data.category,
        "participants": [ObjectId(creator_id)],  # Track participants
        "last_activity_at": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await db.discussions.insert_one(discussion_dict)
    discussion_dict["_id"] = result.inserted_id

    return _discussion_dict_to_response(discussion_dict)


async def get_discussion_by_id(discussion_id: str) -> Optional[DiscussionResponse]:
    """
    Get a discussion by ID.

    Args:
        discussion_id: Discussion ID.

    Returns:
        DiscussionResponse or None if not found.
    """
    db = get_database()
    discussion = await db.discussions.find_one({"_id": ObjectId(discussion_id)})
    if not discussion:
        return None

    return _discussion_dict_to_response(discussion)


async def list_discussions(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    category: Optional[str] = None,
) -> DiscussionListResponse:
    """
    List discussions with filters and pagination.

    Args:
        page: Page number.
        page_size: Items per page.
        search: Search query for title/description.
        category: Filter by category.

    Returns:
        DiscussionListResponse: Paginated list of discussions.
    """
    db = get_database()

    # Build query
    query = {}
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]
    if category:
        query["category"] = category

    # Count total
    total = await db.discussions.count_documents(query)

    # Calculate pagination
    skip = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size

    # Get discussions
    discussions_cursor = (
        db.discussions.find(query)
        .sort("last_activity_at", -1)
        .skip(skip)
        .limit(page_size)
    )

    discussions = await discussions_cursor.to_list(length=page_size)

    # Convert to response models
    items = [_discussion_dict_to_response(d) for d in discussions]

    return DiscussionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


async def add_discussion_message(
    discussion_id: str, user_id: str, message_text: str
) -> None:
    """
    Add a message to a discussion and update counts.

    Args:
        discussion_id: Discussion ID.
        user_id: User ID posting the message.
        message_text: Message text.
    """
    db = get_database()

    # Get user info
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Create message
    message_dict = {
        "discussion_id": ObjectId(discussion_id),
        "user_id": ObjectId(user_id),
        "user_name": user.get("name", "Unknown"),
        "user_avatar": user.get("avatar_url"),
        "text": message_text,
        "created_at": datetime.utcnow(),
    }

    await db.discussion_messages.insert_one(message_dict)

    # Update discussion counts
    discussion = await db.discussions.find_one({"_id": ObjectId(discussion_id)})
    if discussion:
        participants = set(discussion.get("participants", []))
        participants.add(ObjectId(user_id))

        messages_count = await db.discussion_messages.count_documents(
            {"discussion_id": ObjectId(discussion_id)}
        )

        await db.discussions.update_one(
            {"_id": ObjectId(discussion_id)},
            {
                "$set": {
                    "participants_count": len(participants),
                    "messages_count": messages_count,
                    "last_activity_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
                "$addToSet": {"participants": ObjectId(user_id)},
            },
        )


def _discussion_dict_to_response(discussion_dict: dict) -> DiscussionResponse:
    """Convert discussion dict to response model."""
    return DiscussionResponse(
        id=str(discussion_dict["_id"]),
        title=discussion_dict.get("title", ""),
        description=discussion_dict.get("description", ""),
        devotional_id=str(discussion_dict["devotional_id"])
        if discussion_dict.get("devotional_id")
        else None,
        devotional_title=discussion_dict.get("devotional_title"),
        scripture_reference=discussion_dict.get("scripture_reference"),
        author_id=str(discussion_dict["author_id"]),
        author_name=discussion_dict.get("author_name", "Unknown"),
        author_avatar=discussion_dict.get("author_avatar"),
        participants_count=discussion_dict.get("participants_count", 0),
        messages_count=discussion_dict.get("messages_count", 0),
        last_activity_at=discussion_dict.get(
            "last_activity_at", discussion_dict.get("created_at")
        ),
        created_at=discussion_dict.get("created_at"),
        category=discussion_dict.get("category"),
    )

