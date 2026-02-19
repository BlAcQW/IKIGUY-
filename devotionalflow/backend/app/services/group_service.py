"""
Bible Study Group service for DevotionalFlow.
Handles group creation, membership, discussions, and chat messages.
"""

from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException, status

from app.db.mongodb import get_database
from app.models.group import (
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    GroupMember,
    GroupMessage,
    GroupMessageResponse,
    GroupListResponse,
)
import logging

logger = logging.getLogger(__name__)


async def create_group(group_data: GroupCreate, creator_id: str) -> GroupResponse:
    """
    Create a new Bible study group.

    Args:
        group_data: Group creation data.
        creator_id: ID of the user creating the group.

    Returns:
        GroupResponse: Created group data.
    """
    db = get_database()

    # Get creator info
    creator = await db.users.find_one({"_id": ObjectId(creator_id)})
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Creator not found",
        )

    # Create group document
    group_dict = {
        "name": group_data.name,
        "description": group_data.description,
        "is_public": group_data.is_public,
        "creator_id": ObjectId(creator_id),
        "devotional_id": ObjectId(group_data.devotional_id) if group_data.devotional_id else None,
        "discussion_topic": group_data.discussion_topic,
        "members": [
            {
                "user_id": ObjectId(creator_id),
                "name": creator.get("name", "Unknown"),
                "avatar_url": creator.get("avatar_url"),
                "role": "admin",
                "joined_at": datetime.utcnow(),
            }
        ],
        "members_count": 1,
        "messages_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await db.groups.insert_one(group_dict)
    group_dict["_id"] = result.inserted_id

    return _group_dict_to_response(group_dict, creator)


async def get_group_by_id(group_id: str) -> Optional[GroupResponse]:
    """
    Get a group by ID.

    Args:
        group_id: Group ID.

    Returns:
        GroupResponse or None if not found.
    """
    db = get_database()

    if not ObjectId.is_valid(group_id):
        return None

    group_doc = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group_doc:
        return None

    # Get creator info
    creator = await db.users.find_one({"_id": group_doc["creator_id"]})
    if not creator:
        creator = {"name": "Unknown", "avatar_url": None}

    return _group_dict_to_response(group_doc, creator)


async def list_groups(
    page: int = 1,
    page_size: int = 20,
    is_public: Optional[bool] = None,
    search: Optional[str] = None,
) -> GroupListResponse:
    """
    List groups with filters and pagination.

    Args:
        page: Page number.
        page_size: Items per page.
        is_public: Filter by public/private.
        search: Search by name or description.

    Returns:
        GroupListResponse: Paginated list of groups.
    """
    db = get_database()

    # Build query
    query = {}
    if is_public is not None:
        query["is_public"] = is_public
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    # Count total
    total = await db.groups.count_documents(query)

    # Get groups
    skip = (page - 1) * page_size
    cursor = (
        db.groups.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )

    groups = []
    async for group_doc in cursor:
        creator = await db.users.find_one({"_id": group_doc["creator_id"]})
        if not creator:
            creator = {"name": "Unknown", "avatar_url": None}
        groups.append(_group_dict_to_response(group_doc, creator))

    total_pages = (total + page_size - 1) // page_size

    return GroupListResponse(
        items=groups,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


async def join_group(group_id: str, user_id: str) -> GroupResponse:
    """
    Join a group.

    Args:
        group_id: Group ID.
        user_id: User ID joining the group.

    Returns:
        GroupResponse: Updated group data.
    """
    db = get_database()

    if not ObjectId.is_valid(group_id) or not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group or user ID",
        )

    # Check if group exists
    group_doc = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # Check if already a member
    existing_member = any(
        str(member["user_id"]) == user_id for member in group_doc.get("members", [])
    )
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member of this group",
        )

    # Get user info
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Add member
    new_member = {
        "user_id": ObjectId(user_id),
        "name": user.get("name", "Unknown"),
        "avatar_url": user.get("avatar_url"),
        "role": "member",
        "joined_at": datetime.utcnow(),
    }

    await db.groups.update_one(
        {"_id": ObjectId(group_id)},
        {
            "$push": {"members": new_member},
            "$inc": {"members_count": 1},
            "$set": {"updated_at": datetime.utcnow()},
        },
    )

    # Get updated group
    updated_group = await db.groups.find_one({"_id": ObjectId(group_id)})
    creator = await db.users.find_one({"_id": updated_group["creator_id"]})
    if not creator:
        creator = {"name": "Unknown", "avatar_url": None}

    return _group_dict_to_response(updated_group, creator)


async def leave_group(group_id: str, user_id: str) -> None:
    """
    Leave a group.

    Args:
        group_id: Group ID.
        user_id: User ID leaving the group.
    """
    db = get_database()

    if not ObjectId.is_valid(group_id) or not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group or user ID",
        )

    # Check if group exists
    group_doc = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # Check if creator (cannot leave own group)
    if str(group_doc["creator_id"]) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group creator cannot leave the group",
        )

    # Remove member
    result = await db.groups.update_one(
        {"_id": ObjectId(group_id)},
        {
            "$pull": {"members": {"user_id": ObjectId(user_id)}},
            "$inc": {"members_count": -1},
            "$set": {"updated_at": datetime.utcnow()},
        },
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not a member of this group",
        )


async def update_group(
    group_id: str, group_data: GroupUpdate, user_id: str
) -> GroupResponse:
    """
    Update a group. Only the creator or admin members can update.

    Args:
        group_id: Group ID.
        group_data: Group update data.
        user_id: User ID making the update.

    Returns:
        GroupResponse: Updated group data.
    """
    db = get_database()

    if not ObjectId.is_valid(group_id) or not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group or user ID",
        )

    # Check if group exists
    group_doc = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # Check if user is creator or admin
    is_creator = str(group_doc["creator_id"]) == user_id
    is_admin = any(
        str(member["user_id"]) == user_id and member.get("role") == "admin"
        for member in group_doc.get("members", [])
    )

    if not (is_creator or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group creator or admins can update the group",
        )

    # Build update dict (only include fields that are provided)
    update_dict = {"updated_at": datetime.utcnow()}
    if group_data.name is not None:
        update_dict["name"] = group_data.name
    if group_data.description is not None:
        update_dict["description"] = group_data.description
    if group_data.is_public is not None:
        update_dict["is_public"] = group_data.is_public
    if group_data.discussion_topic is not None:
        update_dict["discussion_topic"] = group_data.discussion_topic

    # Update group
    await db.groups.update_one({"_id": ObjectId(group_id)}, {"$set": update_dict})

    # Get updated group
    updated_group = await db.groups.find_one({"_id": ObjectId(group_id)})
    creator = await db.users.find_one({"_id": updated_group["creator_id"]})
    if not creator:
        creator = {"name": "Unknown", "avatar_url": None}

    return _group_dict_to_response(updated_group, creator)


async def delete_group(group_id: str, user_id: str) -> None:
    """
    Delete a group. Only the creator can delete.

    Args:
        group_id: Group ID.
        user_id: User ID deleting the group.
    """
    db = get_database()

    if not ObjectId.is_valid(group_id) or not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group or user ID",
        )

    # Check if group exists
    group_doc = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # Check if user is creator
    if str(group_doc["creator_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group creator can delete the group",
        )

    # Delete all group messages
    await db.group_messages.delete_many({"group_id": ObjectId(group_id)})

    # Delete all group invites
    await db.group_invites.delete_many({"group_id": ObjectId(group_id)})

    # Delete the group
    result = await db.groups.delete_one({"_id": ObjectId(group_id)})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete group",
        )

    logger.info(f"Group {group_id} deleted by user {user_id}")


async def create_group_message(
    group_id: str, user_id: str, message_data: GroupMessage
) -> GroupMessageResponse:
    """
    Create a message in a group chat.

    Args:
        group_id: Group ID.
        user_id: User ID sending the message.
        message_data: Message data.

    Returns:
        GroupMessageResponse: Created message.
    """
    db = get_database()

    if not ObjectId.is_valid(group_id) or not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group or user ID",
        )

    # Check if group exists and user is a member
    group_doc = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    is_member = any(
        str(member["user_id"]) == user_id for member in group_doc.get("members", [])
    )
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must be a member to post messages",
        )

    # Get user info
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Create message
    message_dict = {
        "group_id": ObjectId(group_id),
        "user_id": ObjectId(user_id),
        "text": message_data.text,
        "devotional_id": ObjectId(message_data.devotional_id) if message_data.devotional_id else None,
        "created_at": datetime.utcnow(),
    }

    result = await db.group_messages.insert_one(message_dict)
    message_dict["_id"] = result.inserted_id

    # Increment message count
    await db.groups.update_one(
        {"_id": ObjectId(group_id)},
        {"$inc": {"messages_count": 1}, "$set": {"updated_at": datetime.utcnow()}},
    )

    return GroupMessageResponse(
        id=str(message_dict["_id"]),
        group_id=group_id,
        user_id=user_id,
        user_name=user.get("name", "Unknown"),
        user_avatar_url=user.get("avatar_url"),
        text=message_dict["text"],
        devotional_id=str(message_dict["devotional_id"]) if message_dict["devotional_id"] else None,
        created_at=message_dict["created_at"],
    )


async def list_group_messages(
    group_id: str, page: int = 1, page_size: int = 50
) -> List[GroupMessageResponse]:
    """
    List messages in a group.

    Args:
        group_id: Group ID.
        page: Page number.
        page_size: Items per page.

    Returns:
        List of messages.
    """
    db = get_database()

    if not ObjectId.is_valid(group_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group ID",
        )

    skip = (page - 1) * page_size
    cursor = (
        db.group_messages.find({"group_id": ObjectId(group_id)})
        .sort("created_at", 1)
        .skip(skip)
        .limit(page_size)
    )

    messages = []
    async for message_doc in cursor:
        user = await db.users.find_one({"_id": message_doc["user_id"]})
        if not user:
            user = {"name": "Unknown", "avatar_url": None}

        messages.append(
            GroupMessageResponse(
                id=str(message_doc["_id"]),
                group_id=group_id,
                user_id=str(message_doc["user_id"]),
                user_name=user.get("name", "Unknown"),
                user_avatar_url=user.get("avatar_url"),
                text=message_doc["text"],
                devotional_id=str(message_doc["devotional_id"]) if message_doc.get("devotional_id") else None,
                created_at=message_doc["created_at"],
            )
        )

    return messages


def _group_dict_to_response(group_doc: dict, creator: dict) -> GroupResponse:
    """Convert group document to response model."""
    members = []
    for member in group_doc.get("members", []):
        members.append(
            GroupMember(
                user_id=str(member["user_id"]),
                name=member.get("name", "Unknown"),
                avatar_url=member.get("avatar_url"),
                role=member.get("role", "member"),
                joined_at=member.get("joined_at", datetime.utcnow()),
            )
        )

    return GroupResponse(
        id=str(group_doc["_id"]),
        name=group_doc["name"],
        description=group_doc.get("description"),
        is_public=group_doc.get("is_public", True),
        creator_id=str(group_doc["creator_id"]),
        creator_name=creator.get("name", "Unknown"),
        devotional_id=str(group_doc["devotional_id"]) if group_doc.get("devotional_id") else None,
        discussion_topic=group_doc.get("discussion_topic"),
        members_count=group_doc.get("members_count", 0),
        messages_count=group_doc.get("messages_count", 0),
        members=members,
        created_at=group_doc.get("created_at", datetime.utcnow()),
        updated_at=group_doc.get("updated_at", datetime.utcnow()),
    )

