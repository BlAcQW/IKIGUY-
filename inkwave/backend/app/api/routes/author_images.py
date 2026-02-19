"""
Author Image API routes.

Endpoints for searching and managing author images dynamically.
Images are fetched from external sources - no local storage.
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Body
from typing import Optional, Dict, Any
import logging

from app.schemas.book import AuthorImageSearchRequest, AuthorImageSearchResponse
from app.services.author_image_service import (
    author_image_service,
    AuthorImageResult
)
from apps.shared.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/author-images", tags=["author-images"])


@router.get("/search", response_model=AuthorImageSearchResponse)
async def search_author_images(
    author_name: str = Query(..., min_length=2, description="Author name to search for"),
    context: Optional[str] = Query(None, description="Additional context (e.g., 'religious leader', 'fiction author')"),
    max_results: int = Query(5, ge=1, le=10, description="Maximum images to return")
):
    """
    Search for author images dynamically.

    Searches web sources (Amazon, Wikipedia, etc.) for author photos.
    Returns external URLs - images are not stored locally.

    This endpoint does NOT require authentication to allow
    image preview during book upload.

    Args:
        author_name: Name of the author to search for
        context: Additional context for better results
        max_results: Maximum number of images to return (1-10)

    Returns:
        AuthorImageSearchResponse with image URLs and metadata

    Example:
        GET /api/v1/author-images/search?author_name=Nicholas%20Duncan-Williams&context=bishop

    Note:
        - Images are fetched dynamically from external sources
        - Primary image URL is the best/highest quality result
        - Source pages show where images were found
    """
    try:
        result = await author_image_service.search_author_image(
            author_name=author_name,
            context=context,
            max_results=max_results
        )

        return AuthorImageSearchResponse(
            query=result.query,
            image_urls=result.image_urls,
            source_pages=result.source_pages,
            thumbnail_urls=result.thumbnail_urls,
            primary_image_url=result.primary_image_url,
            status=result.status,
            message=result.message
        )

    except Exception as e:
        logger.error(f"Author image search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search for author images: {str(e)}"
        )


@router.post("/search", response_model=AuthorImageSearchResponse)
async def search_author_images_post(
    request: AuthorImageSearchRequest = Body(...)
):
    """
    Search for author images (POST method).

    Same as GET but accepts request body for complex queries.

    Args:
        request: AuthorImageSearchRequest with author_name, context, max_results

    Returns:
        AuthorImageSearchResponse with image URLs
    """
    try:
        result = await author_image_service.search_author_image(
            author_name=request.author_name,
            context=request.context,
            max_results=request.max_results
        )

        return AuthorImageSearchResponse(
            query=result.query,
            image_urls=result.image_urls,
            source_pages=result.source_pages,
            thumbnail_urls=result.thumbnail_urls,
            primary_image_url=result.primary_image_url,
            status=result.status,
            message=result.message
        )

    except Exception as e:
        logger.error(f"Author image search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search for author images: {str(e)}"
        )


@router.post("/lookup-for-book/{book_id}")
async def lookup_author_image_for_book(
    book_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Look up and save author image for an existing book.

    Searches for author image and updates the book record.
    Requires authentication.

    Args:
        book_id: Book ID to update
        user: Authenticated user

    Returns:
        Updated book with author_image_url
    """
    from app.services.book_service import book_service
    from app.core.database import get_db

    try:
        # Get book details
        book = await book_service.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        author_name = book.get("author")
        if not author_name:
            raise HTTPException(status_code=400, detail="Book has no author name")

        # Search for author image
        result = await author_image_service.search_author_image(
            author_name=author_name,
            max_results=1
        )

        if result.status != "success" or not result.primary_image_url:
            return {
                "book_id": book_id,
                "author": author_name,
                "author_image_url": None,
                "status": "not_found",
                "message": "No author image found"
            }

        # Update book with author image URL
        db = get_db()
        await db.books.update_one(
            {"book_id": book_id},
            {"$set": {"author_image_url": result.primary_image_url}}
        )

        logger.info(f"Updated book {book_id} with author image: {result.primary_image_url}")

        return {
            "book_id": book_id,
            "author": author_name,
            "author_image_url": result.primary_image_url,
            "status": "success",
            "all_images_found": result.image_urls
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to lookup author image for book {book_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to lookup author image: {str(e)}"
        )


@router.post("/bulk-update")
async def bulk_update_author_images(
    limit: int = Query(10, ge=1, le=50, description="Max books to process"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Bulk update author images for books without author photos.

    Finds books missing author_image_url and searches for images.
    Processes up to `limit` books per request.

    Requires authentication.

    Args:
        limit: Maximum number of books to process
        user: Authenticated user

    Returns:
        Summary of updated books
    """
    from app.core.database import get_db

    try:
        db = get_db()

        # Find books without author images
        cursor = db.books.find({
            "$or": [
                {"author_image_url": None},
                {"author_image_url": {"$exists": False}},
                {"author_image_url": ""}
            ],
            "author": {"$exists": True, "$ne": ""}
        }).limit(limit)

        books = await cursor.to_list(length=limit)

        updated = []
        failed = []

        for book in books:
            book_id = book.get("book_id")
            author_name = book.get("author")

            try:
                result = await author_image_service.search_author_image(
                    author_name=author_name,
                    max_results=1
                )

                if result.primary_image_url:
                    await db.books.update_one(
                        {"book_id": book_id},
                        {"$set": {"author_image_url": result.primary_image_url}}
                    )
                    updated.append({
                        "book_id": book_id,
                        "author": author_name,
                        "image_url": result.primary_image_url
                    })
                else:
                    failed.append({
                        "book_id": book_id,
                        "author": author_name,
                        "reason": "No images found"
                    })

            except Exception as e:
                failed.append({
                    "book_id": book_id,
                    "author": author_name,
                    "reason": str(e)
                })

        return {
            "processed": len(books),
            "updated": len(updated),
            "failed": len(failed),
            "updated_books": updated,
            "failed_books": failed
        }

    except Exception as e:
        logger.error(f"Bulk author image update failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Bulk update failed: {str(e)}"
        )
