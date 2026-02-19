"""
Book API routes.

Endpoints for book management:
- GET /books - List books with filtering
- GET /books/{id} - Get book details
- GET /books/continue-reading - Get in-progress books
- GET /reading/session/{book_id} - Get reading session
- PUT /reading/progress - Update reading progress
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Header, File, Form, UploadFile, BackgroundTasks
from typing import Optional, Dict, Any
import sys
import os
import logging

logger = logging.getLogger(__name__)

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from app.schemas.book import (
    BookListResponse,
    BookDetail,
    BookListItem,
    ReadingSessionRequest,
    ReadingSessionResponse
)
from app.services.book_service import book_service
from apps.shared.dependencies.auth import get_current_user, get_current_user_optional
from app.core.auth import get_current_author_or_admin
import urllib.parse


def _generate_default_cover_url(title: str, author: str = "") -> str:
    """
    Generate a default cover image URL using ui-avatars.com.
    
    Creates a unique placeholder cover with book initials and a color
    based on the title. This ensures every book has a cover image.
    
    Args:
        title: Book title
        author: Book author (optional)
    
    Returns:
        URL to placeholder cover image
    """
    # Extract initials from title (first letter of each word, max 3 words)
    words = [w for w in title.split() if w][:3]
    initials = "".join([word[0].upper() for word in words if word])
    
    # If no initials, use "BK" as fallback
    if not initials:
        initials = "BK"
    
    # Generate a color based on title hash for consistency
    title_hash = abs(hash(title)) % 360  # Hue value (0-360)
    
    # Convert HSL to hex for URL
    # HSL to RGB conversion
    h = title_hash / 360.0
    s = 0.7
    l = 0.5
    
    def hsl_to_hex(h, s, l):
        """Convert HSL to hex color."""
        import colorsys
        # colorsys uses HLS, so we need to convert HSL to HLS
        # HLS: hue, lightness, saturation
        # HSL: hue, saturation, lightness
        rgb = colorsys.hls_to_rgb(h, l, s)
        return f"{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
    
    hex_color = hsl_to_hex(h, s, l)
    
    # Generate URL with ui-avatars.com
    name = urllib.parse.quote(initials)
    return f"https://ui-avatars.com/api/?name={name}&size=400&background={hex_color}&color=fff&bold=true&format=png"


router = APIRouter(prefix="/books", tags=["books"])


@router.get("/search", response_model=BookListResponse)
async def search_books(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Search sermons by title, author, description, or keywords.

    Supports:
    - Full-text search across title, author, description
    - Optional category filtering
    - Pagination
    """
    try:
        books, total = await book_service.search_books(
            query=q,
            page=page,
            per_page=per_page,
            category=category
        )

        book_items = [BookListItem(**book) for book in books]

        return BookListResponse(
            books=book_items,
            total=total,
            page=page,
            per_page=per_page
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search books: {str(e)}"
        )


@router.get("", response_model=BookListResponse)
async def list_books(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    search: Optional[str] = Query(None, description="Search query"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    List available books with optional filtering.

    Applies visibility filtering based on user authentication:
    - Anonymous users: Only public books
    - Authenticated users: Public books + own books
    - Admins: All books except hidden/deleted

    Supports:
    - Pagination
    - Genre filtering
    - Search by title/author
    """
    try:
        # Extract user info for visibility filtering
        user_id = None
        user_role = None
        if current_user:
            user_id = current_user.get("sub") or current_user.get("id")
            # Check user role from user_metadata or app_metadata
            user_metadata = current_user.get("user_metadata", {})
            app_metadata = current_user.get("app_metadata", {})
            user_role = user_metadata.get("role") or app_metadata.get("role")

        books, total = await book_service.list_books(
            page=page,
            per_page=per_page,
            genre=genre,
            search=search,
            user_id=user_id,
            user_role=user_role
        )

        # Convert to BookListItem format
        book_items = [BookListItem(**book) for book in books]

        return BookListResponse(
            books=book_items,
            total=total,
            page=page,
            per_page=per_page
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch books: {str(e)}"
        )


@router.get("/my-books", response_model=BookListResponse)
async def list_my_books(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by processing status"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List books uploaded by the current user.

    Returns books that the authenticated user has uploaded.
    Includes processing status so authors can track their uploads.
    """
    try:
        user_id = user.get("id") or user.get("user_id")

        books, total = await book_service.list_books_by_uploader(
            uploader_id=user_id,
            page=page,
            per_page=per_page,
            status=status
        )

        book_items = [BookListItem(**book) for book in books]

        return BookListResponse(
            books=book_items,
            total=total,
            page=page,
            per_page=per_page
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch your books: {str(e)}"
        )


@router.get("/continue-reading", response_model=BookListResponse)
async def get_continue_reading(
    limit: int = Query(10, ge=1, le=50, description="Number of books"),
    authorization: Optional[str] = Header(None)
):
    """
    Get user's in-progress books (Continue Reading shelf).

    Returns books with progress > 0 and < 100 for authenticated users.
    Returns empty list for unauthenticated users.
    """
    try:
        # Try to get user if authenticated
        user_id = None
        if authorization:
            try:
                user = await get_current_user(authorization)
                user_id = user.get("id") or user.get("user_id")
            except:
                pass  # Not authenticated, will return empty list

        # If not authenticated, return empty list
        if not user_id:
            return BookListResponse(
                books=[],
                total=0,
                page=1,
                per_page=limit
            )

        books = await book_service.get_continue_reading(
            user_id=user_id,
            limit=limit
        )

        book_items = [BookListItem(**book) for book in books]

        return BookListResponse(
            books=book_items,
            total=len(books),
            page=1,
            per_page=limit
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch continue reading: {str(e)}"
        )


@router.get("/check-duplicate-title")
async def check_duplicate_title(
    title: str = Query(..., min_length=1, description="Book title to check"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Check if a book title already exists in the database.

    Performs a case-insensitive search for exact and similar titles to help
    authors avoid uploading duplicate books.

    Args:
        title: Book title to check for duplicates
        current_user: Current user (optional, for better results)

    Returns:
        Dict with:
            - exists: bool - True if exact match found
            - duplicates: list - Exact matches
            - similar: list - Similar titles (fuzzy match)
            - total_count: int - Total number of potential duplicates
    """
    from app.core.database import get_db
    import re

    try:
        db = get_db()

        # Normalize title for comparison
        normalized_title = title.strip().lower()

        # Check for exact match (case-insensitive)
        exact_matches = await db.books.find(
            {
                "title": {"$regex": f"^{re.escape(title)}$", "$options": "i"},
                "is_deleted": {"$ne": True}
            },
            {
                "book_id": 1,
                "title": 1,
                "author": 1,
                "visibility": 1,
                "is_hidden": 1,
                "uploaded_by": 1,
                "created_at": 1
            }
        ).limit(10).to_list(length=10)

        # Check for similar titles (contains or partial match)
        # Reason: Help users find books that might be the same with slight variations
        similar_matches = []
        if len(exact_matches) == 0:
            # Only search for similar if no exact match
            # Split title into words and create a pattern for partial matching
            words = [w.strip() for w in normalized_title.split() if len(w.strip()) > 2]
            if words:
                # Create regex to find titles containing significant words
                pattern = "|".join([re.escape(word) for word in words[:3]])  # Use first 3 significant words
                similar_matches = await db.books.find(
                    {
                        "title": {"$regex": pattern, "$options": "i"},
                        "is_deleted": {"$ne": True}
                    },
                    {
                        "book_id": 1,
                        "title": 1,
                        "author": 1,
                        "visibility": 1,
                        "is_hidden": 1,
                        "uploaded_by": 1,
                        "created_at": 1
                    }
                ).limit(5).to_list(length=5)

                # Filter out exact matches from similar
                exact_ids = {book["book_id"] for book in exact_matches}
                similar_matches = [book for book in similar_matches if book["book_id"] not in exact_ids]

        # Format response
        def format_book(book):
            """Format book data for response."""
            user_id = None
            if current_user:
                user_id = current_user.get("sub") or current_user.get("id")

            is_own_book = user_id and book.get("uploaded_by") == user_id

            return {
                "book_id": book["book_id"],
                "title": book["title"],
                "author": book.get("author", "Unknown"),
                "visibility": book.get("visibility", "private"),
                "is_hidden": book.get("is_hidden", False),
                "is_own_book": is_own_book,
                "created_at": book.get("created_at", "").isoformat() if book.get("created_at") else None
            }

        formatted_exact = [format_book(book) for book in exact_matches]
        formatted_similar = [format_book(book) for book in similar_matches]

        return {
            "exists": len(exact_matches) > 0,
            "duplicates": formatted_exact,
            "similar": formatted_similar,
            "total_count": len(formatted_exact) + len(formatted_similar),
            "message": (
                f"Found {len(formatted_exact)} exact match(es) and {len(formatted_similar)} similar title(s)"
                if (formatted_exact or formatted_similar)
                else "No duplicates found"
            )
        }

    except Exception as e:
        logger.error(f"Error checking duplicate title: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check duplicate title: {str(e)}"
        )


@router.get("/{book_id}", response_model=BookDetail)
async def get_book(
    book_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Get detailed book information.

    Applies visibility access control:
    - Public: Anyone can access
    - Unlisted: Anyone with link can access
    - Private: Must be in user's library or be uploader
    - Draft: Only uploader can access
    - Hidden: Admin or uploader (with badge)
    - Deleted: Only admin

    Includes:
    - Full metadata
    - Chapter list with timestamps
    - User's progress (if authenticated)
    - Audio URL
    - Visibility badge (if applicable)

    Works for both authenticated and anonymous users.
    """
    try:
        # Extract user info for access control
        user_id = None
        user_role = None
        if current_user:
            user_id = current_user.get("sub") or current_user.get("id")
            user_metadata = current_user.get("user_metadata", {})
            app_metadata = current_user.get("app_metadata", {})
            user_role = user_metadata.get("role") or app_metadata.get("role")

        # Check if user can access this book
        from app.services.book_service import BookService
        access_result = await BookService.can_user_access_book(
            book_id=book_id,
            user_id=user_id,
            user_role=user_role
        )

        if not access_result["can_access"]:
            if access_result["reason"] == "Book not found":
                raise HTTPException(status_code=404, detail="Book not found")
            else:
                raise HTTPException(
                    status_code=403,
                    detail=access_result["reason"]
                )

        # Get book details
        book = await book_service.get_book(book_id, user_id)

        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Add visibility badge to book details
        book["visibility_badge"] = access_result.get("visibility_badge")
        book["visibility"] = access_result["book"].get("visibility", "private")

        return BookDetail(**book)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch book: {str(e)}"
        )


@router.get("/{book_id}/chunks/info")
async def get_book_chunks_info(
    book_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Get chunk information for a book.

    Returns total chunk count and durations for audio playback planning.
    Used by the chunk-based audio player to:
    - Know total number of chunks
    - Calculate global seek positions
    - Display progress accurately

    Args:
        book_id: Book identifier

    Returns:
        dict with book_id, total_chunks, chunk_durations, total_duration
    """
    from app.core.database import get_db

    try:
        db = get_db()

        # Get book record to check content_metadata.skip_to_chunk
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Get content_start_chunk from content_metadata if set
        content_metadata = book.get("content_metadata", {})
        content_start_chunk = content_metadata.get("skip_to_chunk", 0) if content_metadata else 0

        # Get all chunks for this book (include text for duration estimation and classification data)
        chunks = await db.book_chunks.find(
            {"book_id": book_id},
            {
                "chunk_index": 1,
                "audio_duration": 1,
                "audio_generated": 1,
                "chapter_title": 1,
                "text": 1,
                "skip_audio": 1,
                "is_toc": 1,
                # Content classification fields (professional narration)
                "narratable": 1,
                "content_type": 1,
                "is_chapter_start": 1,
                "skip_reason": 1
            }
        ).sort("chunk_index", 1).to_list(None)

        if not chunks:
            raise HTTPException(status_code=404, detail="Book has no chunks")

        # Extract durations (estimate from text length if not generated)
        # Average TTS speed is ~150 words/min or ~750 chars/min (12.5 chars/sec)
        def estimate_duration(text_length: int) -> float:
            return max(5.0, text_length / 12.5)  # Min 5 seconds

        chunk_durations = []
        for c in chunks:
            if c.get("audio_duration") and c.get("audio_duration") > 0:
                chunk_durations.append(c.get("audio_duration"))
            else:
                # Estimate from text length
                text = c.get("text", "")
                chunk_durations.append(estimate_duration(len(text)))
        total_duration = sum(chunk_durations)
        generated_count = sum(1 for c in chunks if c.get("audio_generated"))

        # Get chapter boundaries with calculated start times
        chapter_boundaries = []
        current_chapter = None
        for c in chunks:
            chapter = c.get("chapter_title")
            if chapter and chapter != current_chapter:
                chunk_idx = c.get("chunk_index", 0)
                # Calculate start_time as sum of all previous chunk durations
                start_time = sum(chunk_durations[:chunk_idx])
                chapter_boundaries.append({
                    "chunk_index": chunk_idx,
                    "chapter_title": chapter,
                    "start_time": start_time  # Time in seconds where chapter starts
                })
                current_chapter = chapter

        # Build list of chunks to skip for professional narration
        # Priority 1: Use content classification 'narratable' field (from ingestion)
        # Priority 2: Use content_metadata.skip_to_chunk if set (manual override)
        # Priority 3: Respect explicit legacy flags from preprocessing
        # Priority 4: Apply defensive heuristics for legacy books without classification
        skip_chunks = []
        content_type_counts = {}

        # Add all chunks below content_start_chunk to skip list (manual override)
        if content_start_chunk > 0:
            for idx in range(content_start_chunk):
                skip_chunks.append(idx)

        for c in chunks:
            idx = c.get("chunk_index")
            text = (c.get("text") or "").strip()
            content_type = c.get("content_type", "unknown")

            # Count content types for analytics
            content_type_counts[content_type] = content_type_counts.get(content_type, 0) + 1

            # Skip if already in skip list (from content_start_chunk)
            if idx is not None and idx in skip_chunks:
                continue

            # Priority 1: Use content classification (professional narration system)
            # If 'narratable' field exists and is explicitly False, skip the chunk
            if "narratable" in c and c.get("narratable") is False:
                if idx is not None:
                    skip_chunks.append(idx)
                continue

            # Priority 3: Respect explicit legacy flags from preprocessing
            if c.get("skip_audio") or c.get("is_toc"):
                if idx is not None:
                    skip_chunks.append(idx)
                continue

            # Priority 4: Apply defensive heuristics for legacy books without classification
            # Only apply if chunk has no classification data (legacy books)
            has_classification = "narratable" in c or "content_type" in c
            if not has_classification and idx is not None and idx < 10 and text:
                lower = text.lower()

                # Short chunks dominated by copyright / ISBN / publisher info
                if len(lower) < 600:
                    copyright_keywords = [
                        "copyright",
                        "all rights reserved",
                        "©",
                        "published by",
                        "isbn",
                        "printed in",
                        "goshen publishers",
                        "cover design by",
                    ]
                    if sum(1 for kw in copyright_keywords if kw in lower) >= 2:
                        skip_chunks.append(idx)
                        continue

                # Table of contents style pages
                if "table of contents" in lower or ("contents" in lower and "chapter" in lower):
                    chapter_refs = lower.count("chapter") + lower.count("part")
                    dots = lower.count("...") + lower.count(".")
                    if (chapter_refs >= 2 and dots > 5) or chapter_refs >= 3:
                        if len(lower) < 1500:
                            skip_chunks.append(idx)
                            continue

                # Lots of dot leaders / page numbers and relatively short
                if lower.count("...") > 8 and len(lower) < 800:
                    skip_chunks.append(idx)
                    continue

        # Calculate playable chunks (excluding skipped ones)
        playable_chunks = len(chunks) - len(skip_chunks)
        playable_duration = sum(d for i, d in enumerate(chunk_durations) if i not in skip_chunks)

        return {
            "book_id": book_id,
            "total_chunks": len(chunks),
            "chunk_durations": chunk_durations,
            "total_duration": total_duration,
            "generated_count": generated_count,
            "all_generated": generated_count == len(chunks),
            "chapter_boundaries": chapter_boundaries,
            "skip_chunks": skip_chunks,  # Chunk indices to skip during playback
            "playable_chunks": playable_chunks,
            "playable_duration": playable_duration,
            # Content classification analytics
            "content_type_counts": content_type_counts
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chunk info: {str(e)}"
        )


@router.get("/reading/session/{book_id}", response_model=ReadingSessionResponse)
async def get_reading_session(
    book_id: str,
    chapter_id: Optional[str] = Query(None, description="Starting chapter"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get or create a reading session.

    Used by the player to:
    - Load book details with chapters
    - Resume from last position
    - Start from specific chapter
    """
    try:
        user_id = user.get("id") or user.get("user_id")
        session = await book_service.get_reading_session(
            book_id=book_id,
            user_id=user_id,
            chapter_id=chapter_id
        )

        return ReadingSessionResponse(**session)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}"
        )


@router.put("/reading/progress")
async def update_reading_progress(
    book_id: str = Query(..., description="Book ID"),
    position: int = Query(..., ge=0, description="Position in seconds"),
    progress: Optional[int] = Query(None, ge=0, le=100, description="Progress percentage"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update reading progress.

    Called periodically during playback to:
    - Save current position
    - Update progress percentage
    - Enable "Continue Reading" feature
    """
    try:
        user_id = user.get("id") or user.get("user_id")
        await book_service.update_progress(
            user_id=user_id,
            book_id=book_id,
            position=position,
            progress=progress
        )

        return {"status": "success", "message": "Progress updated"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update progress: {str(e)}"
        )


# PDF Upload Endpoints

@router.post("/upload")
async def upload_book(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF file to upload"),
    title: str = Form(..., description="Book title"),
    author: str = Form(..., description="Book author"),
    author_id: Optional[str] = Form(None, description="Author user_id (if linked to author account)"),
    description: Optional[str] = Form(None, description="Book description"),
    cover_image: Optional[UploadFile] = File(None, description="Cover image file (JPG, PNG, WebP)"),
    cover_url: Optional[str] = Form(None, description="Optional cover image URL (if no file uploaded)"),
    author_image_url: Optional[str] = Form(None, description="Optional author image URL (dynamic)"),
    auto_search_author_image: bool = Form(True, description="Auto-search for author image if not provided"),
    use_ai_chapters: bool = Form(False, description="Use AI-enhanced chapter detection for non-standard chapter formats"),
    user = Depends(get_current_author_or_admin)
):
    """
    Upload a PDF book for processing.

    **Requires AUTHOR, ADMIN, or SUPERADMIN role.**

    The book will be processed asynchronously:
    1. PDF upload to Hetzner cloud storage
    2. PDF text extraction
    3. Chapter detection (optional AI-enhanced)
    4. Chunking
    5. Embedding generation
    6. Author image search (if auto_search_author_image=True)
    7. Ready for reading and Q&A

    Args:
        file: PDF file to upload
        title: Book title
        author: Book author
        description: Book description
        cover_image: Cover image file (JPG, PNG, WebP, max 5MB)
        cover_url: Optional cover image URL (if no file uploaded)
        author_image_url: Optional author image URL (dynamic, not stored locally)
        auto_search_author_image: Auto-search for author image if not provided (default: True)
        use_ai_chapters: Use AI-enhanced chapter detection for books with non-standard
            chapter formats (creative titles, multi-language). Uses Gemini AI.
            Default: False (uses regex-based detection)
        user: Authenticated user with author/admin privileges

    Returns:
        Book ID, processing status, and author image URL

    Raises:
        HTTPException: If upload or processing fails or user lacks permission
    """
    from app.services.book_processing_service import BookProcessingService
    from app.services.storage_service import get_storage_service
    import tempfile
    import uuid
    from pathlib import Path

    try:
        user_id = user.user_id

        # Generate book ID before processing
        book_id = f"book_{uuid.uuid4().hex[:12]}"

        # Get storage service
        storage_service = await get_storage_service()

        # Read uploaded PDF file content
        pdf_bytes = await file.read()

        # Upload PDF to cloud storage (or local fallback)
        pdf_storage = await storage_service.upload_book_pdf(
            book_id=book_id,
            file_content=pdf_bytes,
            filename=file.filename
        )
        logger.info(f"📚 Uploaded PDF: {pdf_storage['storage_type']} - {pdf_storage.get('public_url', pdf_storage.get('storage_path'))}")

        # Handle cover image upload
        final_cover_url = cover_url
        cover_storage = None

        if cover_image:
            # Validate cover image
            allowed_types = ["image/jpeg", "image/png", "image/webp"]
            if cover_image.content_type not in allowed_types:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid cover image format. Allowed: JPG, PNG, WebP"
                )

            # Check file size (max 5MB)
            cover_bytes = await cover_image.read()
            if len(cover_bytes) > 5 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail="Cover image too large. Maximum size: 5MB"
                )

            # Upload cover to cloud storage
            cover_storage = await storage_service.upload_cover_image(
                book_id=book_id,
                file_content=cover_bytes,
                content_type=cover_image.content_type
            )
            final_cover_url = cover_storage.get("public_url")
            logger.info(f"🖼️ Uploaded cover: {cover_storage['storage_type']} - {final_cover_url}")

        # Generate default cover if none provided
        if not final_cover_url:
            final_cover_url = _generate_default_cover_url(title, author)

        # Search for author image if not provided and auto_search is enabled
        final_author_image_url = author_image_url
        if not final_author_image_url and auto_search_author_image and author:
            try:
                from app.services.author_image_service import author_image_service
                result = await author_image_service.search_author_image(
                    author_name=author,
                    context="book author",
                    max_results=1
                )
                if result.status == "success" and result.primary_image_url:
                    final_author_image_url = result.primary_image_url
            except Exception as e:
                # Don't fail upload if author image search fails
                logger.warning(f"Author image search failed: {e}")

        # Create initial book record with "processing" status and storage metadata
        from app.models.book import Book, BookMetadata, BookStorage
        from app.core.database import get_db

        db = get_db()

        # Build storage metadata
        storage_metadata = BookStorage(
            storage_type=pdf_storage.get("storage_type", "local"),
            pdf_path=pdf_storage.get("storage_path"),
            pdf_url=pdf_storage.get("public_url"),
            pdf_size=pdf_storage.get("size", 0),
            pdf_checksum=pdf_storage.get("checksum"),
            cover_path=cover_storage.get("storage_path") if cover_storage else None,
            cover_url=cover_storage.get("public_url") if cover_storage else final_cover_url
        )

        book = Book(
            book_id=book_id,
            title=title,
            author=author,
            author_id=author_id,
            cover_url=final_cover_url,
            author_image_url=final_author_image_url,
            pdf_url=pdf_storage.get("public_url") or pdf_storage.get("storage_path"),
            storage=storage_metadata,
            processed=False,
            processing_status="processing",
            processing_stage="uploading",
            processing_progress=10,
            processing_message="Files uploaded, starting text extraction...",
            uploaded_by=user_id,
            metadata=BookMetadata(summary=description or "")
        )

        await db.books.insert_one(book.model_dump())
        logger.info(f"📝 Created book record: {book_id}")

        # For processing, we need a local file path
        # If using Hetzner, save a local temp copy for processing
        if pdf_storage.get("storage_type") == "hetzner":
            # Save to local temp for processing
            uploads_dir = Path(__file__).parent.parent.parent.parent / "storage" / "uploads" / "books"
            uploads_dir.mkdir(parents=True, exist_ok=True)
            local_file_path = uploads_dir / f"{book_id}.pdf"

            with open(local_file_path, "wb") as f:
                f.write(pdf_bytes)
            file_path = str(local_file_path)
        else:
            file_path = pdf_storage.get("storage_path")

        # Queue background task for processing
        from app.tasks.book_processing_tasks import process_book_background

        background_tasks.add_task(
            process_book_background,
            book_id=book_id,
            file_path=file_path,
            book_metadata={
                "title": title,
                "author": author,
                "description": description or "",
                "cover_url": final_cover_url
            },
            uploaded_by=user_id,
            use_ai_chapter_detection=use_ai_chapters
        )

        return {
            "book_id": book_id,
            "title": title,
            "author": author,
            "cover_url": final_cover_url,
            "author_image_url": final_author_image_url,
            "pdf_url": pdf_storage.get("public_url"),
            "storage_type": pdf_storage.get("storage_type"),
            "status": "processing",  # Frontend expects 'status'
            "processing_status": "processing",  # Keep for backward compatibility
            "processing_stage": "uploading",
            "processing_progress": 10,
            "processing_message": "Files uploaded, starting text extraction...",
            "message": "Book uploaded and processing started in background",
            "chapters_extracted": 0,
            "use_ai_chapters": use_ai_chapters
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Book upload failed: {e}", exc_info=True)

        raise HTTPException(
            status_code=500,
            detail=f"Book upload failed: {str(e)}"
        )


@router.put("/{book_id}")
async def update_book(
    book_id: str,
    title: Optional[str] = Form(None, description="New book title"),
    author: Optional[str] = Form(None, description="New book author"),
    description: Optional[str] = Form(None, description="New book description"),
    cover_url: Optional[str] = Form(None, description="New cover image URL"),
    genre: Optional[str] = Form(None, description="New book genre"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update book metadata.

    Authors can only update their own books.
    Admins can update any book.

    Args:
        book_id: Book identifier
        title: New title (optional)
        author: New author (optional)
        description: New description (optional)
        cover_url: New cover URL (optional)
        genre: New genre (optional)
        user: Authenticated user

    Returns:
        Updated book details

    Raises:
        HTTPException 403: If user doesn't own the book
        HTTPException 404: If book not found
    """
    try:
        user_id = user.get("id") or user.get("user_id")
        is_admin = user.get("is_admin", False)

        # Check ownership
        can_manage = await book_service.can_user_manage_book(user_id, book_id, is_admin)
        if not can_manage:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to edit this book"
            )

        # Update book
        updated_book = await book_service.update_book(
            book_id=book_id,
            title=title,
            author=author,
            description=description,
            cover_url=cover_url,
            genre=genre
        )

        if not updated_book:
            raise HTTPException(status_code=404, detail="Book not found")

        return {
            "message": "Book updated successfully",
            "book": updated_book
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update book: {str(e)}"
        )


@router.patch("/{book_id}/visibility")
async def update_book_visibility(
    book_id: str,
    visibility: str = Query(..., regex="^(draft|unlisted|private|public)$", description="New visibility state"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update book visibility (author/admin only).

    Visibility states:
    - draft: Incomplete/processing, only uploader can see
    - unlisted: Anyone with link, not in discovery
    - private: Library/invitation only, not in discovery (default)
    - public: In "All Books" discovery, anyone can add to library

    Only the book uploader or admin can change visibility.
    """
    try:
        from app.core.database import get_db
        from app.services.audit_log_service import AuditLogService
        from app.models.audit_log import AuditAction
        from datetime import datetime

        user_id = user.get("sub") or user.get("id")
        user_email = user.get("email", "")
        user_metadata = user.get("user_metadata", {})
        app_metadata = user.get("app_metadata", {})
        user_role = user_metadata.get("role") or app_metadata.get("role")

        db = get_db()

        # Get book
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Check permissions: uploader or admin
        is_uploader = book.get("uploaded_by") == user_id
        is_admin = user_role in ["admin", "superadmin"]

        if not (is_uploader or is_admin):
            raise HTTPException(
                status_code=403,
                detail="Only the book uploader or admin can change visibility"
            )

        old_visibility = book.get("visibility", "private")

        # Update visibility
        result = await db.books.update_one(
            {"book_id": book_id},
            {
                "$set": {
                    "visibility": visibility,
                    "visibility_changed_at": datetime.utcnow(),
                    "visibility_changed_by": user_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Failed to update visibility")

        # Create audit log
        audit_service = AuditLogService(db)
        await audit_service.log_action(
            action=AuditAction.VISIBILITY_CHANGED,
            entity_id=book_id,
            actor_id=user_id,
            actor_email=user_email,
            actor_role=user_role or "user",
            changes={
                "visibility": {"before": old_visibility, "after": visibility}
            },
            metadata={
                "book_title": book.get("title"),
                "book_author": book.get("author")
            }
        )

        return {
            "success": True,
            "message": f"Book visibility updated to '{visibility}'",
            "book_id": book_id,
            "visibility": visibility
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update book visibility: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update visibility: {str(e)}"
        )


@router.post("/{book_id}/add-to-library")
async def add_book_to_library(
    book_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Add a public book to user's library.

    Only works for public books. Private books must be added via invitations.
    """
    try:
        from app.core.database import get_db
        from datetime import datetime

        user_id = user.get("sub") or user.get("id")

        db = get_db()

        # Get book
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Check if book is public
        visibility = book.get("visibility", "private")
        if visibility != "public":
            raise HTTPException(
                status_code=403,
                detail="Only public books can be added to library. This book is private - you need an invitation."
            )

        # Check if already in library
        user_doc = await db.users.find_one({"user_id": user_id})
        if user_doc:
            library_books = user_doc.get("library_books", [])
            if any(lib_book.get("book_id") == book_id for lib_book in library_books):
                return {
                    "success": True,
                    "message": "Book is already in your library",
                    "book_id": book_id
                }

        # Add to library
        result = await db.users.update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "library_books": {
                        "book_id": book_id,
                        "access_type": "public",
                        "added_at": datetime.utcnow(),
                        "invitation_id": None,
                        "granted_by": None
                    }
                }
            }
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Failed to add book to library")

        return {
            "success": True,
            "message": f"'{book.get('title')}' added to your library",
            "book_id": book_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add book to library: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add book: {str(e)}"
        )


@router.delete("/{book_id}")
async def delete_book(
    book_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a book and all its associated data.

    Authors can only delete their own books.
    Admins can delete any book.

    This will permanently delete:
    - Book record
    - All book chunks
    - All embeddings
    - All reading sessions
    - All interactions

    Args:
        book_id: Book identifier
        user: Authenticated user

    Returns:
        Success message

    Raises:
        HTTPException 403: If user doesn't own the book
        HTTPException 404: If book not found
    """
    try:
        user_id = user.get("id") or user.get("user_id")
        is_admin = user.get("is_admin", False)

        # Check ownership
        can_manage = await book_service.can_user_manage_book(user_id, book_id, is_admin)
        if not can_manage:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to delete this book"
            )

        # Delete book with all associated data
        deleted = await book_service.delete_book_with_embeddings(book_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Book not found")

        return {
            "message": "Book deleted successfully",
            "book_id": book_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete book: {str(e)}"
        )


@router.post("/{book_id}/reprocess")
async def reprocess_book(
    book_id: str,
    use_ai_chapters: bool = Query(False, description="Use AI-enhanced chapter detection for non-standard chapter formats"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Reprocess an existing book (Admin only).

    This will:
    1. Clean up all existing processed data (chunks, embeddings, audio)
    2. Re-run the text extraction and chunking
    3. Regenerate embeddings
    4. Trigger audio pre-generation

    The source PDF file is preserved.

    Args:
        book_id: Book identifier
        use_ai_chapters: Use AI-enhanced chapter detection (Gemini) for books
            with non-standard chapter formats. Default: False (regex-based)
        user: Authenticated admin user

    Returns:
        Reprocessing status and cleanup summary

    Raises:
        HTTPException 403: If user is not admin
        HTTPException 404: If book not found
        HTTPException 400: If PDF file not available
    """
    try:
        user_id = user.get("id") or user.get("user_id")
        is_admin = user.get("is_admin", False)

        # Admin-only endpoint
        if not is_admin:
            raise HTTPException(
                status_code=403,
                detail="Admin access required to reprocess books"
            )

        # Reprocess the book
        result = await book_service.reprocess_book(book_id, user_id, use_ai_chapters)

        return {
            "message": "Book reprocessing started",
            **result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reprocess book: {str(e)}"
        )


@router.post("/{book_id}/reclassify")
async def reclassify_book_chunks(
    book_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Reclassify book chunks for content type and narratability (Admin only).

    Re-applies the content classification system to all chunks in a book.
    This is useful for books ingested before the classification system was added.

    Marks front matter, copyright, TOC, etc. as non-narratable so AI narration
    skips them and starts at actual content.

    Args:
        book_id: Book identifier
        user: Authenticated admin user

    Returns:
        Reclassification statistics
    """
    from app.services.book_processing_service import get_book_processing_service

    try:
        is_admin = user.get("is_admin", False)

        if not is_admin:
            raise HTTPException(
                status_code=403,
                detail="Admin access required to reclassify books"
            )

        service = await get_book_processing_service()
        result = await service.reclassify_book_chunks(book_id)

        return {
            "success": True,
            "message": "Book chunks reclassified successfully",
            **result
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reclassify book: {str(e)}"
        )


@router.post("/reclassify-all")
async def reclassify_all_books(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Reclassify all books that don't have classification data (Admin only).

    Finds all books with unclassified chunks and applies the content
    classification system to mark front matter as non-narratable.

    Returns:
        Overall reclassification statistics for all processed books
    """
    from app.services.book_processing_service import get_book_processing_service

    try:
        is_admin = user.get("is_admin", False)

        if not is_admin:
            raise HTTPException(
                status_code=403,
                detail="Admin access required to reclassify books"
            )

        service = await get_book_processing_service()
        result = await service.reclassify_all_books()

        return {
            "success": True,
            "message": f"Reclassified {result['books_processed']} books",
            **result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reclassify books: {str(e)}"
        )


@router.get("/{book_id}/deletion-preview")
async def preview_book_deletion(
    book_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Preview what will be deleted when deleting a book (Admin only).

    Shows counts of all associated data that will be removed.

    Args:
        book_id: Book identifier
        user: Authenticated admin user

    Returns:
        Preview of items to be deleted
    """
    from app.core.database import get_db

    try:
        is_admin = user.get("is_admin", False)

        if not is_admin:
            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )

        db = get_db()

        # Get book info
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Count all associated data
        chunks_count = await db.book_chunks.count_documents({"book_id": book_id})
        sessions_count = await db.reading_sessions.count_documents({"book_id": book_id})
        interactions_count = await db.interactions.count_documents({"book_id": book_id})
        voice_settings_count = await db.book_voice_settings.count_documents({"book_id": book_id})

        # Count embeddings
        embeddings_count = 0
        try:
            from app.services.embedding_service import get_embedding_service
            embedding_service = await get_embedding_service()
            stats = await embedding_service.get_embedding_stats(book_id)
            embeddings_count = stats.get("embedding_count", 0)
        except Exception:
            pass

        # Count audio cache files
        import glob
        import os
        cache_dir = "/opt/kasaai/apps/inkwave/backend/storage/audiobooks"
        audio_files_count = 0
        if os.path.exists(cache_dir):
            for pattern in [f"{book_id}_*.mp3", f"{book_id}_*.mp3.meta"]:
                audio_files_count += len(glob.glob(os.path.join(cache_dir, pattern)))

        return {
            "book_id": book_id,
            "book_title": book.get("title"),
            "will_delete": {
                "book_record": 1,
                "chunks": chunks_count,
                "embeddings": embeddings_count,
                "reading_sessions": sessions_count,
                "interactions": interactions_count,
                "voice_settings": voice_settings_count,
                "audio_cache_files": audio_files_count,
                "storage_files": ["PDF", "cover", "audio directory"]
            },
            "warning": "This action cannot be undone!"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to preview deletion: {str(e)}"
        )


@router.get("/{book_id}/processing-status")
async def get_processing_status(
    book_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get book processing status.

    Args:
        book_id: Book identifier
        user: Authenticated user

    Returns:
        Processing status and details

    Raises:
        HTTPException: If book not found
    """
    from app.core.database import get_db

    try:
        # Query MongoDB directly to get raw document with processing fields
        db = get_db()
        book = await db.books.find_one({"book_id": book_id})

        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        return {
            "book_id": book_id,
            "status": book.get("processing_status", "unknown"),  # Frontend expects 'status'
            "processing_status": book.get("processing_status", "unknown"),  # Keep for backward compatibility
            "processed": book.get("processed", False),
            "processing_error": book.get("processing_error"),
            "processing_stage": book.get("processing_stage", ""),
            "processing_progress": book.get("processing_progress", 0),
            "processing_message": book.get("processing_message", ""),
            "metadata": {
                "page_count": book.get("metadata", {}).get("page_count", 0),
                "word_count": book.get("metadata", {}).get("word_count", 0),
                "chapters": len(book.get("chapters", []))
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get processing status: {str(e)}"
        )


@router.post("/{book_id}/generate-audio")
async def generate_book_audio_preview(
    book_id: str,
    provider_id: str = Query(default="f5tts", description="TTS provider to use"),
    voice_id: Optional[str] = Query(default="archbishop_1", description="Voice ID for narration"),
    speed: float = Query(default=1.0, ge=0.5, le=2.0, description="Playback speed"),
    pitch: float = Query(default=0.0, ge=-20.0, le=20.0, description="Voice pitch adjustment"),
    language: str = Query(default="en", description="Language code"),
    authorization: Optional[str] = Header(None)
):
    """
    Generate audio preview for a book using TTS.

    Generates narration for a sample of the book content (first few pages or description).
    Returns base64-encoded audio for immediate playback.

    Args:
        book_id: Book identifier
        provider_id: TTS provider (coqui_xtts, f5tts, etc.)
        voice_id: Optional voice identifier for cloning
        speed: Playback speed multiplier
        language: Language code
        authorization: Optional auth header

    Returns:
        {
            "audio_url": "data:audio/mp3;base64,...",
            "text": "Sample text that was narrated",
            "duration": 45.2,
            "provider_used": "coqui_xtts",
            "cost": 0.002
        }
    """
    import base64
    import PyPDF2
    from apps.shared.services.tts_provider_service import (
        TTSProviderService,
        SynthesisRequest
    )

    try:
        # Get book from database
        book = await book_service.get_book(book_id)

        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Extract sample text for TTS
        sample_text = None

        # Try to get text from PDF file if available
        if book.get("file_path") and os.path.exists(book["file_path"]):
            try:
                with open(book["file_path"], 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    # Extract first 2-3 pages
                    text_parts = []
                    for page_num in range(min(3, len(pdf_reader.pages))):
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)

                    if text_parts:
                        full_text = " ".join(text_parts)
                        # Limit to ~500 words for reasonable audio length
                        words = full_text.split()
                        sample_text = " ".join(words[:min(500, len(words))])
            except Exception as e:
                print(f"Could not extract PDF text: {e}")

        # Fallback to book description if no PDF text
        if not sample_text:
            sample_text = book.get("description") or f"Welcome to {book['title']} by {book.get('author', 'Unknown Author')}. This is a preview audio sample."

        # Clean up text - add null check to prevent NoneType error
        sample_text = sample_text.strip() if sample_text else ""
        if not sample_text:
            raise HTTPException(status_code=400, detail="No content available for audio generation")

        # Initialize TTS service
        tts_service = TTSProviderService(enable_billing=False)  # Disable billing for previews
        await tts_service.initialize()

        # Wait for service to be ready (similar to ChurchFlow)
        import asyncio
        await asyncio.sleep(2)  # Give providers time to come online

        # Get user ID if authenticated
        user_id = "anonymous"
        if authorization:
            try:
                current_user = await get_current_user(authorization)
                user_id = current_user.user_id if hasattr(current_user, 'user_id') else current_user.get("user_id", "anonymous")
            except:
                pass

        # Try f5tts with archbishop voice, fallback to other providers
        providers_config = [
            {'provider': provider_id, 'voice': voice_id},  # f5tts with archbishop_1
            {'provider': 'kokoro', 'voice': 'af_sky'},      # Fallback 1
            {'provider': 'melotts', 'voice': None},         # Fallback 2
            {'provider': 'openvoice', 'voice': None},       # Fallback 3
        ]
        result = None
        last_error = None

        for config in providers_config:
            try:
                synthesis_request = SynthesisRequest(
                    provider_id=config['provider'],
                    text=sample_text,
                    voice_id=config['voice'],
                    speed=speed,
                    pitch=pitch,
                    language=language
                )

                result = await tts_service.synthesize(
                    user_id=user_id,
                    request=synthesis_request
                )
                break  # Success! Exit loop
            except ValueError as e:
                last_error = e
                print(f"Provider {config['provider']} failed: {e}")
                continue  # Try next provider

        if not result:
            raise HTTPException(
                status_code=503,
                detail="We're unable to generate audio right now. Our text-to-speech services are temporarily unavailable. Please try again in a few moments."
            )

        # Return as data URL for immediate playback (like ChurchFlow greetings)
        audio_url = f"data:audio/mp3;base64,{result.audio_base64}"

        return {
            "audio_url": audio_url,
            "text": sample_text[:200] + "..." if len(sample_text) > 200 else sample_text,  # Return preview of text
            "duration": result.duration,
            "provider_used": result.provider_id,
            "cost": 0.0,  # No cost for previews
            "is_preview": True,
            "full_text_length": len(sample_text)
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate audio: {str(e)}"
        )


# =============================================================================
# AUDIO PRE-GENERATION ENDPOINTS
# =============================================================================

@router.get("/{book_id}/audio-status")
async def get_audio_generation_status(
    book_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get audio generation status for a book.

    Args:
        book_id: Book identifier
        user: Authenticated user

    Returns:
        Audio generation status and progress
    """
    from app.services.audio_pregeneration_service import get_audio_pregeneration_service

    try:
        service = await get_audio_pregeneration_service()
        status = await service.get_audio_generation_status(book_id)
        return status

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get audio status: {str(e)}"
        )


@router.post("/{book_id}/generate-audio")
async def trigger_audio_generation(
    book_id: str,
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_current_user),
    provider_id: str = Form(default="kokoro"),
    voice_id: str = Form(default="am_michael"),
    speed: float = Form(default=1.0)
):
    """
    Manually trigger audio generation for a book.

    This starts audio generation in the background and returns immediately.
    Use GET /{book_id}/audio-status to poll for progress.

    Args:
        book_id: Book identifier
        background_tasks: FastAPI background tasks
        user: Authenticated user
        provider_id: TTS provider (default: kokoro)
        voice_id: Voice ID (default: am_michael)
        speed: Playback speed (default: 1.0)

    Returns:
        Confirmation message
    """
    from app.services.audio_pregeneration_service import get_audio_pregeneration_service
    from app.core.database import get_db

    try:
        user_id = user.get("id") or user.get("user_id")
        is_admin = user.get("is_admin", False)

        # Verify book exists
        db = get_db()
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Check if user can manage this book
        can_manage = await book_service.can_user_manage_book(user_id, book_id, is_admin)
        if not can_manage:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to generate audio for this book"
            )

        # Get service and trigger generation
        service = await get_audio_pregeneration_service()

        # Run in background
        async def generate_audio():
            await service.pregenerate_book_audio(
                book_id=book_id,
                user_id=user_id,
                voice_settings={
                    "provider_id": provider_id,
                    "voice_id": voice_id,
                    "speed": speed,
                    "language": "en"
                }
            )

        background_tasks.add_task(generate_audio)

        return {
            "message": "Audio generation started",
            "book_id": book_id,
            "provider": provider_id,
            "voice_id": voice_id,
            "status": "generating"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger audio generation: {str(e)}"
        )