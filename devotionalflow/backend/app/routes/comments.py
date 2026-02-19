"""
Comment API routes for DevotionalFlow.
Handles comment CRUD, threaded replies, and likes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import logging

from app.services.comment_service import (
    create_comment,
    list_comments,
    update_comment,
    delete_comment,
    like_comment,
)
from app.models.comment import CommentCreate, CommentUpdate, CommentResponse
from app.utils.auth import get_current_user, get_current_user_optional
from app.models.user import TokenData

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/devotionals/{devotional_id}/comments", response_model=CommentResponse)
async def post_comment(
    devotional_id: str,
    comment_data: CommentCreate,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Create a new comment on a devotional.

    **Path Parameters:**
    - devotional_id: Devotional ID

    **Request Body:**
    - text: Comment text (1-500 characters)
    - parent_comment_id: Parent comment ID for threaded replies (optional)

    **Returns:**
    - Comment with user data, likes count, and pastor reply badge

    **Auth Required:** Yes
    """
    logger.info(
        f"User {current_user.user_id} commenting on devotional {devotional_id}"
    )

    comment = await create_comment(
        devotional_id=devotional_id,
        user_id=current_user.user_id,
        comment_data=comment_data,
    )

    return comment


@router.get("/devotionals/{devotional_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    devotional_id: str,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
):
    """
    List comments for a devotional.

    **Path Parameters:**
    - devotional_id: Devotional ID

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Comments per page (default: 20)
    - sort_by: Sort field - created_at or likes_count (default: created_at)

    **Returns:**
    - List of comments with nested replies

    **Auth Required:** No (but provides is_liked if authenticated)
    """
    user_id = current_user.user_id if current_user else None
    comments = await list_comments(
        devotional_id=devotional_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        user_id=user_id,
    )

    return comments


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def edit_comment(
    comment_id: str,
    update_data: CommentUpdate,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Update a comment.

    **Path Parameters:**
    - comment_id: Comment ID

    **Request Body:**
    - text: Updated comment text (1-500 characters)

    **Returns:**
    - Updated comment

    **Auth Required:** Yes (must be comment author)
    """
    logger.info(f"User {current_user.user_id} updating comment {comment_id}")

    comment = await update_comment(
        comment_id=comment_id,
        user_id=current_user.user_id,
        update_data=update_data,
    )

    return comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_comment(
    comment_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Delete a comment (soft delete).

    **Path Parameters:**
    - comment_id: Comment ID

    **Auth Required:** Yes (must be comment author)
    """
    logger.info(f"User {current_user.user_id} deleting comment {comment_id}")

    await delete_comment(comment_id=comment_id, user_id=current_user.user_id)

    return None


@router.post("/comments/{comment_id}/like")
async def toggle_comment_like(
    comment_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Like or unlike a comment.

    **Path Parameters:**
    - comment_id: Comment ID

    **Returns:**
    - is_liked: Whether user currently likes the comment
    - likes_count: Total likes count

    **Auth Required:** Yes
    """
    logger.info(f"User {current_user.user_id} toggling like on comment {comment_id}")

    result = await like_comment(comment_id=comment_id, user_id=current_user.user_id)

    return result
