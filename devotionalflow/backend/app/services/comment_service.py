"""
Comment service for managing devotional comments and replies.
Supports threaded comments with pastor reply badges.
"""

from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException, status

from app.db.mongodb import get_database
from app.models.comment import CommentCreate, CommentUpdate, CommentResponse
from app.services import gamification_service


async def create_comment(
    devotional_id: str,
    user_id: str,
    comment_data: CommentCreate,
) -> CommentResponse:
    """
    Create a new comment on a devotional.

    Args:
        devotional_id (str): Devotional ID.
        user_id (str): User ID of commenter.
        comment_data (CommentCreate): Comment data.

    Returns:
        CommentResponse: Created comment.

    Raises:
        HTTPException: If devotional not found.
    """
    db = get_database()

    # Verify devotional exists
    devotional = await db.devotionals.find_one({"_id": ObjectId(devotional_id)})
    if not devotional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devotional not found",
        )

    # Check if parent comment exists (for threaded replies)
    if comment_data.parent_comment_id:
        parent_comment = await db.comments.find_one(
            {"_id": ObjectId(comment_data.parent_comment_id)}
        )
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent comment not found",
            )

    # Check if commenter is the devotional author (for is_pastor_reply badge)
    is_pastor_reply = str(devotional["author_id"]) == user_id

    # Create comment
    comment_dict = {
        "devotional_id": ObjectId(devotional_id),
        "user_id": ObjectId(user_id),
        "text": comment_data.text,
        "parent_comment_id": (
            ObjectId(comment_data.parent_comment_id)
            if comment_data.parent_comment_id
            else None
        ),
        "is_pastor_reply": is_pastor_reply,
        "likes_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "deleted_at": None,
    }

    result = await db.comments.insert_one(comment_dict)

    # Update devotional comment count
    await db.devotionals.update_one(
        {"_id": ObjectId(devotional_id)}, {"$inc": {"comments_count": 1}}
    )

    # Award gamification points for commenting
    await gamification_service.handle_comment(user_id, devotional_id)

    # Fetch and return created comment
    created_comment = await db.comments.find_one({"_id": result.inserted_id})
    return CommentResponse(**await serialize_comment(created_comment))


async def list_comments(
    devotional_id: str,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    user_id: Optional[str] = None,
) -> List[CommentResponse]:
    """
    List comments for a devotional with pagination.

    Args:
        devotional_id (str): Devotional ID.
        page (int): Page number (1-indexed).
        page_size (int): Number of comments per page.
        sort_by (str): Sort field (created_at, likes_count).
        user_id (Optional[str]): User ID to check for likes.

    Returns:
        List[CommentResponse]: List of comments.
    """
    db = get_database()

    # Only show non-deleted top-level comments
    query = {
        "devotional_id": ObjectId(devotional_id),
        "parent_comment_id": None,
        "deleted_at": None,
    }

    # Sort direction
    sort_order = -1 if sort_by in ["created_at", "likes_count"] else 1

    # Pagination
    skip = (page - 1) * page_size

    cursor = (
        db.comments.find(query)
        .sort(sort_by, sort_order)
        .skip(skip)
        .limit(page_size)
    )

    comments = []
    async for comment_doc in cursor:
        # Fetch replies for this comment
        replies_cursor = db.comments.find(
            {
                "parent_comment_id": comment_doc["_id"],
                "deleted_at": None,
            }
        ).sort("created_at", 1)

        replies = []
        async for reply_doc in replies_cursor:
            replies.append(CommentResponse(**await serialize_comment(reply_doc, user_id)))

        comment = CommentResponse(**await serialize_comment(comment_doc, user_id))
        comment.replies = replies
        comments.append(comment)

    return comments


async def update_comment(
    comment_id: str,
    user_id: str,
    update_data: CommentUpdate,
) -> CommentResponse:
    """
    Update a comment (text only).

    Args:
        comment_id (str): Comment ID.
        user_id (str): User ID (must be comment author).
        update_data (CommentUpdate): Updated comment data.

    Returns:
        CommentResponse: Updated comment.

    Raises:
        HTTPException: If comment not found or user not authorized.
    """
    db = get_database()

    # Fetch comment
    comment = await db.comments.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # Verify author
    if str(comment["user_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this comment",
        )

    # Update comment
    await db.comments.update_one(
        {"_id": ObjectId(comment_id)},
        {"$set": {"text": update_data.text, "updated_at": datetime.utcnow()}},
    )

    # Return updated comment
    updated_comment = await db.comments.find_one({"_id": ObjectId(comment_id)})
    return CommentResponse(**await serialize_comment(updated_comment))


async def delete_comment(comment_id: str, user_id: str) -> bool:
    """
    Soft delete a comment.

    Args:
        comment_id (str): Comment ID.
        user_id (str): User ID (must be comment author).

    Returns:
        bool: True if deleted successfully.

    Raises:
        HTTPException: If comment not found or user not authorized.
    """
    db = get_database()

    # Fetch comment
    comment = await db.comments.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # Verify author
    if str(comment["user_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment",
        )

    # Soft delete
    await db.comments.update_one(
        {"_id": ObjectId(comment_id)}, {"$set": {"deleted_at": datetime.utcnow()}}
    )

    # Decrease devotional comment count
    await db.devotionals.update_one(
        {"_id": comment["devotional_id"]}, {"$dec": {"comments_count": 1}}
    )

    return True


async def like_comment(comment_id: str, user_id: str) -> dict:
    """
    Like or unlike a comment.

    Args:
        comment_id (str): Comment ID.
        user_id (str): User ID.

    Returns:
        dict: Like status with is_liked and likes_count.

    Raises:
        HTTPException: If comment not found.
    """
    db = get_database()

    # Check if comment exists
    comment = await db.comments.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # Check if user already liked this comment
    existing_like = await db.comment_likes.find_one(
        {"comment_id": ObjectId(comment_id), "user_id": ObjectId(user_id)}
    )

    if existing_like:
        # Unlike: remove like
        await db.comment_likes.delete_one({"_id": existing_like["_id"]})
        await db.comments.update_one(
            {"_id": ObjectId(comment_id)}, {"$inc": {"likes_count": -1}}
        )

        # Get updated count
        updated_comment = await db.comments.find_one({"_id": ObjectId(comment_id)})

        return {
            "is_liked": False,
            "likes_count": updated_comment.get("likes_count", 0),
        }
    else:
        # Like: create like
        await db.comment_likes.insert_one(
            {
                "comment_id": ObjectId(comment_id),
                "user_id": ObjectId(user_id),
                "created_at": datetime.utcnow(),
            }
        )
        await db.comments.update_one(
            {"_id": ObjectId(comment_id)}, {"$inc": {"likes_count": 1}}
        )

        # Get updated count
        updated_comment = await db.comments.find_one({"_id": ObjectId(comment_id)})

        return {
            "is_liked": True,
            "likes_count": updated_comment.get("likes_count", 0),
        }


async def serialize_comment(comment_doc: dict, user_id: Optional[str] = None) -> dict:
    """
    Serialize MongoDB comment document to Pydantic model format.
    Fetches user data to populate user_name and user_avatar_url.

    Args:
        comment_doc (dict): Comment document from MongoDB.
        user_id (Optional[str]): User ID to check for likes.

    Returns:
        dict: Serialized comment data.
    """
    db = get_database()

    # Fetch user data
    user = await db.users.find_one({"_id": comment_doc["user_id"]})
    user_name = user.get("name", "Unknown User") if user else "Unknown User"
    user_avatar_url = user.get("avatar_url") if user else None

    # Check if current user liked this comment
    is_liked = False
    if user_id:
        existing_like = await db.comment_likes.find_one({
            "comment_id": comment_doc["_id"],
            "user_id": ObjectId(user_id)
        })
        is_liked = existing_like is not None

    return {
        "id": str(comment_doc["_id"]),
        "devotional_id": str(comment_doc["devotional_id"]),
        "user_id": str(comment_doc["user_id"]),
        "user_name": user_name,
        "user_avatar_url": user_avatar_url,
        "text": comment_doc["text"],
        "parent_comment_id": (
            str(comment_doc["parent_comment_id"])
            if comment_doc.get("parent_comment_id")
            else None
        ),
        "is_pastor_reply": comment_doc.get("is_pastor_reply", False),
        "likes_count": comment_doc.get("likes_count", 0),
        "is_liked": is_liked,
        "created_at": comment_doc["created_at"],
        "updated_at": comment_doc.get("updated_at", comment_doc["created_at"]),
        "deleted_at": comment_doc.get("deleted_at"),
        "replies": [],  # Will be populated by list_comments
    }
