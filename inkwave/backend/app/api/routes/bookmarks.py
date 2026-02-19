"""
Bookmarks API Routes.

Endpoints for managing user's bookmarked books.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
import logging

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])


@router.post("/{book_id}")
async def add_bookmark(
    book_id: str,
    user: User = Depends(get_current_user)
):
    """
    Add a book to user's bookmarks.

    Args:
        book_id: Book ID to bookmark
        user: Current authenticated user

    Returns:
        Success message
    """
    try:
        db = get_db()

        # Check if book exists
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )

        # Check if already bookmarked
        existing = await db.bookmarked_books.find_one({
            "user_id": user.user_id,
            "book_id": book_id
        })

        if existing:
            return {"message": "Book already bookmarked", "bookmarked": True}

        # Add bookmark
        bookmark_doc = {
            "user_id": user.user_id,
            "book_id": book_id,
            "created_at": datetime.utcnow()
        }

        await db.bookmarked_books.insert_one(bookmark_doc)
        logger.info(f"User {user.email} bookmarked book {book_id}")

        return {"message": "Book bookmarked successfully", "bookmarked": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bookmarking book: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bookmark book"
        )


@router.delete("/{book_id}")
async def remove_bookmark(
    book_id: str,
    user: User = Depends(get_current_user)
):
    """
    Remove a book from user's bookmarks.

    Args:
        book_id: Book ID to remove from bookmarks
        user: Current authenticated user

    Returns:
        Success message
    """
    try:
        db = get_db()

        result = await db.bookmarked_books.delete_one({
            "user_id": user.user_id,
            "book_id": book_id
        })

        if result.deleted_count == 0:
            return {"message": "Book was not bookmarked", "bookmarked": False}

        logger.info(f"User {user.email} removed bookmark for book {book_id}")
        return {"message": "Bookmark removed successfully", "bookmarked": False}

    except Exception as e:
        logger.error(f"Error removing bookmark: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove bookmark"
        )


@router.get("/{book_id}/status")
async def get_bookmark_status(
    book_id: str,
    user: User = Depends(get_current_user)
):
    """
    Check if a book is bookmarked by the user.

    Args:
        book_id: Book ID to check
        user: Current authenticated user

    Returns:
        Bookmark status
    """
    try:
        db = get_db()

        bookmark = await db.bookmarked_books.find_one({
            "user_id": user.user_id,
            "book_id": book_id
        })

        return {"bookmarked": bookmark is not None}

    except Exception as e:
        logger.error(f"Error checking bookmark status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check bookmark status"
        )


@router.get("")
async def list_bookmarks(
    user: User = Depends(get_current_user)
):
    """
    Get all bookmarked books for the current user.

    Args:
        user: Current authenticated user

    Returns:
        List of bookmarked books with details
    """
    try:
        db = get_db()

        # Get all bookmarks for user
        bookmarks_cursor = db.bookmarked_books.find({"user_id": user.user_id})
        bookmarks = await bookmarks_cursor.to_list(length=1000)

        if not bookmarks:
            return {"books": []}

        # Get book IDs
        book_ids = [bookmark["book_id"] for bookmark in bookmarks]

        # Fetch book details
        books_cursor = db.books.find({"book_id": {"$in": book_ids}})
        books = await books_cursor.to_list(length=1000)

        # Map books to response format
        books_map = {book["book_id"]: book for book in books}

        result_books = []
        for bookmark in bookmarks:
            book = books_map.get(bookmark["book_id"])
            if book:
                result_books.append({
                    "id": book["book_id"],
                    "title": book["title"],
                    "author": book["author"],
                    "description": book.get("description", ""),
                    "cover_url": book.get("cover_url"),
                    "background_url": book.get("background_url"),
                    "duration": book.get("duration", 0),
                    "genre": book.get("genre"),
                    "bookmarked_at": bookmark["created_at"].isoformat()
                })

        return {"books": result_books}

    except Exception as e:
        logger.error(f"Error listing bookmarks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list bookmarks"
        )
