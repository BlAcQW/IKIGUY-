"""
Book Comments API Routes.

Endpoints for creating, reading, updating, and deleting book comments/reviews.
"""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, status
import uuid

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.comment import (
    BookComment,
    BookCommentInDB,
    CommentCreateRequest,
    CommentUpdateRequest,
    CommentResponse,
    CommentHelpful
)

router = APIRouter(prefix="/comments", tags=["Comments"])
logger = logging.getLogger(__name__)


async def get_user_info(db, user_id: str):
    """Helper to get user display info."""
    user = await db.users.find_one({"user_id": user_id})
    if user:
        return {
            "email": user.get("email", "Unknown"),
            "display_name": user.get("display_name"),
            "avatar_url": user.get("avatar_url")
        }
    return {"email": "Unknown", "display_name": None, "avatar_url": None}


@router.post("/books/{book_id}", status_code=status.HTTP_201_CREATED)
async def create_comment(
    book_id: str,
    request: CommentCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new comment/review for a book.

    Args:
        book_id: Book ID
        request: Comment data
        current_user: Authenticated user

    Returns:
        Created comment
    """
    try:
        db = get_db()

        # Check if book exists
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Create comment
        comment = BookComment(
            comment_id=str(uuid.uuid4()),
            book_id=book_id,
            user_id=current_user.user_id,
            rating=request.rating,
            title=request.title,
            comment_text=request.comment_text,
            helpful_count=0,
            helpful_votes=[]
        )

        # Insert into database
        await db.book_comments.insert_one(comment.model_dump(by_alias=True, exclude={"id"}))

        # Update book average rating if rating provided
        if request.rating:
            await update_book_average_rating(db, book_id)

        logger.info(f"User {current_user.user_id} created comment on book {book_id}")

        return {
            "success": True,
            "message": "Comment created successfully",
            "comment_id": comment.comment_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create comment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/books/{book_id}", response_model=List[CommentResponse])
async def get_book_comments(
    book_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("recent", regex="^(recent|helpful|rating)$"),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Get comments for a book.

    Args:
        book_id: Book ID
        limit: Maximum number of comments to return
        offset: Number of comments to skip
        sort_by: Sort order (recent, helpful, rating)
        current_user: Optional authenticated user

    Returns:
        List of comments with user info
    """
    try:
        db = get_db()

        # Build query
        query = {
            "book_id": book_id,
            "is_hidden": False  # Don't show hidden comments
        }

        # Get comments
        cursor = db.book_comments.find(query)

        # Sort
        if sort_by == "recent":
            cursor = cursor.sort("created_at", -1)
        elif sort_by == "helpful":
            cursor = cursor.sort("helpful_count", -1)
        elif sort_by == "rating":
            cursor = cursor.sort("rating", -1)

        # Pagination
        cursor = cursor.skip(offset).limit(limit)
        comments = await cursor.to_list(length=limit)

        # Get user info for all comments
        user_ids = list(set(c.get("user_id") for c in comments))
        users_cursor = db.users.find({"user_id": {"$in": user_ids}})
        users = await users_cursor.to_list(length=len(user_ids))
        users_dict = {u.get("user_id"): u for u in users}

        # Build response
        current_user_id = current_user.user_id if current_user else None
        response = []

        for comment in comments:
            user_id = comment.get("user_id")
            user_info = users_dict.get(user_id, {})

            # Check if current user found this helpful
            helpful_votes = comment.get("helpful_votes", [])
            user_found_helpful = False
            if current_user_id:
                user_found_helpful = any(v.get("user_id") == current_user_id for v in helpful_votes)

            response.append(CommentResponse(
                comment_id=comment.get("comment_id"),
                book_id=comment.get("book_id"),
                user_id=user_id,
                user_email=user_info.get("email", "Unknown"),
                user_display_name=user_info.get("display_name"),
                user_avatar_url=user_info.get("avatar_url"),
                rating=comment.get("rating"),
                title=comment.get("title"),
                comment_text=comment.get("comment_text"),
                helpful_count=comment.get("helpful_count", 0),
                user_found_helpful=user_found_helpful,
                is_author=(user_id == current_user_id),
                created_at=comment.get("created_at").isoformat() if isinstance(comment.get("created_at"), datetime) else str(comment.get("created_at", "")),
                updated_at=comment.get("updated_at").isoformat() if isinstance(comment.get("updated_at"), datetime) else str(comment.get("updated_at", ""))
            ))

        return response

    except Exception as e:
        logger.error(f"Failed to get comments: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{comment_id}")
async def update_comment(
    comment_id: str,
    request: CommentUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a comment.

    Args:
        comment_id: Comment ID
        request: Update data
        current_user: Authenticated user

    Returns:
        Success message
    """
    try:
        db = get_db()

        # Get existing comment
        comment = await db.book_comments.find_one({"comment_id": comment_id})
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        # Check ownership
        if comment.get("user_id") != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this comment")

        # Build update
        update_data = {"updated_at": datetime.utcnow()}
        if request.rating is not None:
            update_data["rating"] = request.rating
        if request.title is not None:
            update_data["title"] = request.title
        if request.comment_text is not None:
            update_data["comment_text"] = request.comment_text

        # Update
        await db.book_comments.update_one(
            {"comment_id": comment_id},
            {"$set": update_data}
        )

        # Update book average rating if rating changed
        if request.rating is not None:
            await update_book_average_rating(db, comment.get("book_id"))

        logger.info(f"User {current_user.user_id} updated comment {comment_id}")

        return {"success": True, "message": "Comment updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update comment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a comment.

    Args:
        comment_id: Comment ID
        current_user: Authenticated user

    Returns:
        Success message
    """
    try:
        db = get_db()

        # Get existing comment
        comment = await db.book_comments.find_one({"comment_id": comment_id})
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        # Check ownership (or admin)
        user = await db.users.find_one({"user_id": current_user.user_id})
        is_admin = user and user.get("role") in ["admin", "superadmin", "universal_admin"]

        if comment.get("user_id") != current_user.user_id and not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

        # Delete
        await db.book_comments.delete_one({"comment_id": comment_id})

        # Update book average rating
        await update_book_average_rating(db, comment.get("book_id"))

        logger.info(f"User {current_user.user_id} deleted comment {comment_id}")

        return {"success": True, "message": "Comment deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete comment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{comment_id}/helpful")
async def toggle_helpful(
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Toggle helpful vote on a comment.

    Args:
        comment_id: Comment ID
        current_user: Authenticated user

    Returns:
        Updated helpful status
    """
    try:
        db = get_db()

        # Get comment
        comment = await db.book_comments.find_one({"comment_id": comment_id})
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        # Check if user already voted
        helpful_votes = comment.get("helpful_votes", [])
        user_voted = any(v.get("user_id") == current_user.user_id for v in helpful_votes)

        if user_voted:
            # Remove vote
            helpful_votes = [v for v in helpful_votes if v.get("user_id") != current_user.user_id]
            await db.book_comments.update_one(
                {"comment_id": comment_id},
                {
                    "$set": {
                        "helpful_votes": helpful_votes,
                        "helpful_count": len(helpful_votes)
                    }
                }
            )
            return {"success": True, "helpful": False, "helpful_count": len(helpful_votes)}
        else:
            # Add vote
            new_vote = CommentHelpful(user_id=current_user.user_id)
            await db.book_comments.update_one(
                {"comment_id": comment_id},
                {
                    "$push": {"helpful_votes": new_vote.model_dump()},
                    "$inc": {"helpful_count": 1}
                }
            )
            return {"success": True, "helpful": True, "helpful_count": len(helpful_votes) + 1}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle helpful: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def update_book_average_rating(db, book_id: str):
    """
    Update book's average rating based on comments.

    Args:
        db: Database instance
        book_id: Book ID
    """
    try:
        # Get all ratings for this book
        pipeline = [
            {"$match": {"book_id": book_id, "rating": {"$ne": None}, "is_hidden": False}},
            {
                "$group": {
                    "_id": None,
                    "avg_rating": {"$avg": "$rating"},
                    "rating_count": {"$sum": 1}
                }
            }
        ]

        result = await db.book_comments.aggregate(pipeline).to_list(length=1)

        if result:
            avg_rating = round(result[0].get("avg_rating", 0), 1)
            rating_count = result[0].get("rating_count", 0)
        else:
            avg_rating = 0
            rating_count = 0

        # Update book
        await db.books.update_one(
            {"book_id": book_id},
            {
                "$set": {
                    "rating": avg_rating,
                    "rating_count": rating_count
                }
            }
        )

        logger.info(f"Updated book {book_id} rating: {avg_rating} ({rating_count} reviews)")

    except Exception as e:
        logger.error(f"Failed to update book rating: {e}", exc_info=True)
