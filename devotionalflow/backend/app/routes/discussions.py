"""
Discussion API routes for community-wide discussions.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
import logging

from app.models.discussion import (
    DiscussionCreate,
    DiscussionResponse,
    DiscussionListResponse,
)
from app.services.discussion_service import (
    create_discussion,
    get_discussion_by_id,
    list_discussions,
    add_discussion_message,
)
from app.utils.auth import get_current_user, get_current_user_optional
from app.models.user import TokenData

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=DiscussionResponse, status_code=status.HTTP_201_CREATED)
async def create_discussion_endpoint(
    discussion_data: DiscussionCreate,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Create a new discussion.

    **Auth Required:** Yes
    """
    logger.info(f"User {current_user.user_id} creating discussion: {discussion_data.title}")
    discussion = await create_discussion(discussion_data, current_user.user_id)
    logger.info(f"Discussion created: {discussion.id}")
    return discussion


@router.get("/", response_model=DiscussionListResponse)
async def list_discussions_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
):
    """
    List discussions with filters and pagination.

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - search: Search by title or description
    - category: Filter by category

    **Auth Required:** No
    """
    result = await list_discussions(
        page=page, page_size=page_size, search=search, category=category
    )
    return result


@router.get("/{discussion_id}", response_model=DiscussionResponse)
async def get_discussion_endpoint(discussion_id: str):
    """
    Get a single discussion by ID.

    **Path Parameters:**
    - discussion_id: Discussion ID

    **Auth Required:** No
    """
    discussion = await get_discussion_by_id(discussion_id)
    if not discussion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discussion not found",
        )
    return discussion


from pydantic import BaseModel


class DiscussionMessageCreate(BaseModel):
    """Model for creating a discussion message."""
    text: str


@router.post("/{discussion_id}/messages")
async def post_discussion_message(
    discussion_id: str,
    message_data: DiscussionMessageCreate,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Post a message to a discussion.

    **Path Parameters:**
    - discussion_id: Discussion ID

    **Request Body:**
    - text: Message text (1-1000 characters)

    **Auth Required:** Yes
    """
    logger.info(
        f"User {current_user.user_id} posting message to discussion {discussion_id}"
    )
    await add_discussion_message(discussion_id, current_user.user_id, message_data.text)
    return {"message": "Message posted successfully"}

