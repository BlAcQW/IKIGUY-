"""
Bible Study Group API routes for DevotionalFlow.
Handles group creation, membership, discussions, and chat.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
import logging

from app.models.group import (
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    GroupMessage,
    GroupMessageResponse,
    GroupListResponse,
)
from app.services.group_service import (
    create_group,
    get_group_by_id,
    list_groups,
    join_group,
    leave_group,
    update_group,
    delete_group,
    create_group_message,
    list_group_messages,
)
from app.utils.auth import get_current_user
from app.models.user import TokenData

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group_endpoint(
    group_data: GroupCreate,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Create a new Bible study group.

    **Auth Required:** Yes
    """
    logger.info(f"Creating group '{group_data.name}' by user {current_user.user_id}")
    group = await create_group(group_data, current_user.user_id)
    logger.info(f"Group created: {group.id}")
    return group


@router.get("/", response_model=GroupListResponse)
async def list_groups_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_public: Optional[bool] = None,
    search: Optional[str] = None,
):
    """
    List Bible study groups with filters and pagination.

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - is_public: Filter by public/private groups
    - search: Search by name or description

    **Auth Required:** No (public groups only)
    """
    result = await list_groups(page=page, page_size=page_size, is_public=is_public, search=search)
    return result


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group_endpoint(group_id: str):
    """
    Get a single group by ID.

    **Path Parameters:**
    - group_id: Group ID

    **Auth Required:** No
    """
    group = await get_group_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    return group


@router.post("/{group_id}/join", response_model=GroupResponse)
async def join_group_endpoint(
    group_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Join a Bible study group.

    **Path Parameters:**
    - group_id: Group ID

    **Auth Required:** Yes
    """
    logger.info(f"User {current_user.user_id} joining group {group_id}")
    group = await join_group(group_id, current_user.user_id)
    return group


@router.post("/{group_id}/leave", status_code=status.HTTP_200_OK)
async def leave_group_endpoint(
    group_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Leave a Bible study group.

    **Path Parameters:**
    - group_id: Group ID

    **Auth Required:** Yes
    """
    logger.info(f"User {current_user.user_id} leaving group {group_id}")
    await leave_group(group_id, current_user.user_id)
    return {"message": "Left group successfully"}


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group_endpoint(
    group_id: str,
    group_data: GroupUpdate,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Update a Bible study group.

    **Path Parameters:**
    - group_id: Group ID

    **Request Body:**
    - name: Optional group name
    - description: Optional group description
    - is_public: Optional privacy setting
    - discussion_topic: Optional discussion topic

    **Auth Required:** Yes (must be creator or admin)
    """
    logger.info(f"User {current_user.user_id} updating group {group_id}")
    group = await update_group(group_id, group_data, current_user.user_id)
    return group


@router.delete("/{group_id}", status_code=status.HTTP_200_OK)
async def delete_group_endpoint(
    group_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Delete a Bible study group.

    **Path Parameters:**
    - group_id: Group ID

    **Auth Required:** Yes (must be creator)

    **Note:** This will delete the group and all associated messages and invites.
    """
    logger.info(f"User {current_user.user_id} deleting group {group_id}")
    await delete_group(group_id, current_user.user_id)
    return {"message": "Group deleted successfully"}


@router.post("/{group_id}/messages", response_model=GroupMessageResponse)
async def create_message_endpoint(
    group_id: str,
    message_data: GroupMessage,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Create a message in a group chat.

    **Path Parameters:**
    - group_id: Group ID

    **Request Body:**
    - text: Message text (1-1000 characters)
    - devotional_id: Optional devotional reference

    **Auth Required:** Yes (must be a group member)
    """
    logger.info(f"User {current_user.user_id} posting message in group {group_id}")
    message = await create_group_message(group_id, current_user.user_id, message_data)
    return message


@router.get("/{group_id}/messages", response_model=List[GroupMessageResponse])
async def list_messages_endpoint(
    group_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """
    List messages in a group chat.

    **Path Parameters:**
    - group_id: Group ID

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Messages per page (default: 50, max: 100)

    **Auth Required:** No
    """
    messages = await list_group_messages(group_id, page=page, page_size=page_size)
    return messages

