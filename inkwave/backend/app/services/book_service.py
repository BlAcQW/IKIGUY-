"""
Book Service.

Handles book CRUD operations, search, and management.
"""

import logging
import os
import uuid
import aiofiles
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.models.book import Book, BookInDB, BookChunk
from app.services.book_processing_service import get_book_processing_service

logger = logging.getLogger(__name__)


class BookService:
    """Service for managing books."""

    @staticmethod
    async def list_books(
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        genre: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None
    ):
        """
        List books with pagination and filters.

        Applies visibility filtering based on user permissions.

        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            search: Search query (title or author)
            genre: Filter by genre (optional)
            status: Filter by processing status
            user_id: Optional user ID for visibility filtering
            user_role: Optional user role for visibility filtering

        Returns:
            Tuple of (books list, total count)
        """
        db = get_db()

        # Start with visibility filter
        query = BookService.get_book_visibility_filter(
            user_id=user_id,
            user_role=user_role,
            include_hidden=False
        )

        # Add search filter
        if search:
            # Merge with existing $or if present
            search_or = [
                {"title": {"$regex": search, "$options": "i"}},
                {"author": {"$regex": search, "$options": "i"}}
            ]
            if "$or" in query:
                # Combine visibility $or with search $or using $and
                query = {
                    "$and": [
                        {"$or": query["$or"]},  # Visibility filter
                        {"$or": search_or}  # Search filter
                    ]
                }
                # Remove the standalone $or from query
                del query["$or"]
            else:
                query["$or"] = search_or

        if genre:
            query["genre"] = genre

        if status:
            query["processing_status"] = status

        # Calculate skip from page number
        skip = (page - 1) * per_page

        # Get total count
        total = await db.books.count_documents(query)

        # Get books for current page
        cursor = db.books.find(query).sort("created_at", -1).skip(skip).limit(per_page)
        books = []

        async for doc in cursor:
            doc["_id"] = str(doc["_id"])

            # Check if this is user's own book and if it's hidden
            visibility_badge = None
            if user_id and doc.get("uploaded_by") == user_id:
                if doc.get("is_hidden", False):
                    visibility_badge = f"Hidden by Admin: {doc.get('hidden_reason', 'No reason provided')}"
                elif doc.get("visibility") in ["draft", "private", "unlisted"]:
                    visibility_badge = doc.get("visibility", "").capitalize()

            # Convert to dict format expected by route
            book_dict = {
                "id": doc["book_id"],
                "title": doc["title"],
                "author": doc["author"],
                "description": doc.get("description"),
                "cover_url": doc.get("cover_url"),
                "author_image_url": doc.get("author_image_url"),  # Dynamic author photo URL
                "duration": doc.get("metadata", {}).get("duration_minutes", 0),
                "genre": doc.get("genre"),
                "progress": None,  # Will be filled by route if user session exists
                "visibility": doc.get("visibility", "private"),
                "visibility_badge": visibility_badge
            }
            books.append(book_dict)

        logger.info(f"Listed {len(books)} books (page={page}, per_page={per_page}, total={total}, user_id={user_id})")
        return books, total

    @staticmethod
    async def get_book(book_id: str, user_id: Optional[str] = None):
        """
        Get a book by ID with optional user progress.

        Args:
            book_id: Book identifier
            user_id: Optional user ID for fetching progress

        Returns:
            Book dict with details or None if not found
        """
        db = get_db()
        doc = await db.books.find_one({"book_id": book_id})

        if not doc:
            return None

        doc["_id"] = str(doc["_id"])

        # Get chunk count from metadata or count from collection
        chunk_count = doc.get("metadata", {}).get("chunk_count", 0)
        if chunk_count == 0:
            # Count chunks from collection
            chunk_count = await db.book_chunks.count_documents({"book_id": book_id})

        # Calculate chunk durations for chapter start_time calculation
        # Fetch all chunks to get durations (or estimate from text length)
        chunks = await db.book_chunks.find(
            {"book_id": book_id},
            {"chunk_index": 1, "audio_duration": 1, "text": 1}
        ).sort("chunk_index", 1).to_list(None)

        # Calculate chunk durations (estimate from text if audio not generated)
        def estimate_duration(text_length: int) -> float:
            return max(5.0, text_length / 12.5)  # ~12.5 chars/sec average TTS

        chunk_durations = []
        for c in chunks:
            if c.get("audio_duration") and c.get("audio_duration") > 0:
                chunk_durations.append(c.get("audio_duration"))
            else:
                text = c.get("text", "")
                chunk_durations.append(estimate_duration(len(text)))

        total_audio_duration = sum(chunk_durations)

        # Detect first "real" content chunk (skip TOC, copyright, title pages)
        # Priority: Use manually configured content_metadata.skip_to_chunk if set
        content_metadata = doc.get("content_metadata", {})
        if content_metadata and content_metadata.get("skip_to_chunk") is not None:
            # Use manually configured skip setting
            content_start_chunk = content_metadata.get("skip_to_chunk", 0)
        else:
            # Auto-detect by looking for introduction/chapter markers
            content_start_chunk = 0
            for c in chunks[:20]:  # Check first 20 chunks max
                text = c.get("text", "").strip().upper()
                # Look for introduction, preface, or chapter 1
                if any(marker in text[:200] for marker in [
                    "INTRODUCTION",
                    "PREFACE",
                    "PROLOGUE",
                    "CHAPTER 1",
                    "CHAPTER ONE"
                ]):
                    content_start_chunk = c.get("chunk_index", 0)
                    break

        # Build response dict matching BookDetail schema
        book_dict = {
            "id": doc["book_id"],
            "title": doc["title"],
            "author": doc["author"],
            "description": doc.get("description"),
            "genre": doc.get("genre"),
            "duration": doc.get("metadata", {}).get("duration_minutes", 0),
            "cover_url": doc.get("cover_url"),
            "author_image_url": doc.get("author_image_url"),  # Dynamic author photo URL
            "background_url": None,
            "audio_url": None,  # Audio is generated on-demand via chunk-based TTS
            "pdf_url": doc.get("pdf_url"),  # PDF URL for reading/download
            "total_chunks": chunk_count,
            "content_start_chunk": content_start_chunk,  # First chunk with actual content
            "chapters": [],
            "progress": None,
            "last_position": None
        }

        # Convert chapters with calculated start_time from chunk durations
        for ch in doc.get("chapters", []):
            start_chunk_id = ch.get("start_chunk_id", 0)
            end_chunk_id = ch.get("end_chunk_id", start_chunk_id)
            # Calculate start_time as sum of all chunk durations before this chapter
            calculated_start_time = sum(chunk_durations[:start_chunk_id]) if chunk_durations else 0

            chapter_dict = {
                "id": ch.get("id", f"ch_{start_chunk_id}"),  # Use stored id, fallback to chunk-based
                "title": ch.get("title", "Chapter"),
                "duration": (ch.get("word_count") or 0) // 200,  # Rough estimate: ~200 words/min
                "order": ch.get("order", len(book_dict["chapters"]) + 1),  # Use stored order
                "start_time": int(calculated_start_time),  # Calculated from chunk durations
                "start_chunk": start_chunk_id,  # Chunk index where chapter starts (for frontend)
                "end_chunk": end_chunk_id  # Chunk index where chapter ends (for frontend)
            }
            book_dict["chapters"].append(chapter_dict)

        # Fetch user progress if user_id provided
        if user_id:
            session = await db.reading_sessions.find_one({
                "user_id": user_id,
                "book_id": book_id
            })
            if session:
                book_dict["progress"] = session.get("progress_percentage", 0)
                book_dict["last_position"] = session.get("current_position", 0)

        return book_dict

    @staticmethod
    async def get_book_chunks(
        book_id: str,
        chapter_id: Optional[int] = None,
        start_idx: Optional[int] = None,
        limit: int = 10
    ) -> List[BookChunk]:
        """
        Get book chunks.

        Args:
            book_id: Book identifier
            chapter_id: Optional chapter filter
            start_idx: Optional start chunk index
            limit: Maximum chunks to return

        Returns:
            List of book chunks
        """
        db = get_db()
        query = {"book_id": book_id}

        if chapter_id is not None:
            query["chapter_id"] = chapter_id

        if start_idx is not None:
            query["chunk_index"] = {"$gte": start_idx}

        cursor = db.book_chunks.find(query).sort("chunk_index", 1).limit(limit)
        chunks = []

        async for doc in cursor:
            chunks.append(BookChunk(**doc))

        return chunks

    @staticmethod
    async def save_uploaded_file(
        file_content: bytes,
        filename: str,
        book_id: str
    ) -> str:
        """
        Save uploaded file to storage.

        Args:
            file_content: File content bytes
            filename: Original filename
            book_id: Book identifier

        Returns:
            File path
        """
        # Ensure storage directory exists
        storage_dir = os.path.join(settings.STORAGE_PATH, "books")
        os.makedirs(storage_dir, exist_ok=True)

        # Generate unique filename
        file_ext = os.path.splitext(filename)[1]
        safe_filename = f"{book_id}{file_ext}"
        file_path = os.path.join(storage_dir, safe_filename)

        # Save file asynchronously
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)

        logger.info(f"Saved uploaded file: {file_path}")
        return file_path

    @staticmethod
    async def upload_book(
        file_content: bytes,
        filename: str,
        title: str,
        author: str,
        description: str,
        uploaded_by: str,
        cover_url: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        narrator: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload and process a new book.

        Args:
            file_content: Book file content
            filename: Original filename
            title: Book title
            author: Book author
            description: Book description
            uploaded_by: User ID
            cover_url: Optional cover image URL
            duration_minutes: Optional duration
            narrator: Optional narrator

        Returns:
            Upload response with book_id and status
        """
        import time
        start_time = time.time()

        # Generate book ID
        book_id = f"book_{uuid.uuid4().hex[:12]}"

        # Save file to storage
        file_path = await BookService.save_uploaded_file(
            file_content, filename, book_id
        )

        # Prepare metadata
        metadata = {
            "title": title,
            "author": author,
            "description": description,
            "cover_url": cover_url,
            "duration_minutes": duration_minutes,
            "narrator": narrator
        }

        # Start async processing
        try:
            processing_service = await get_book_processing_service()
            book = await processing_service.process_book_file(
                file_path, metadata, uploaded_by
            )

            processing_time = time.time() - start_time

            return {
                "book_id": book.book_id,
                "title": book.title,
                "status": book.processing_status,
                "message": f"Book '{title}' processed successfully",
                "chapters_extracted": len(book.chapters),
                "processing_time_seconds": processing_time
            }

        except Exception as e:
            logger.error(f"Book upload failed: {e}")
            raise

    @staticmethod
    async def delete_book(book_id: str) -> bool:
        """
        Delete a book and its chunks.

        Args:
            book_id: Book identifier

        Returns:
            True if deleted
        """
        db = get_db()

        # Delete book chunks
        await db.book_chunks.delete_many({"book_id": book_id})

        # Delete book
        result = await db.books.delete_one({"book_id": book_id})

        if result.deleted_count > 0:
            logger.info(f"Deleted book: {book_id}")
            return True

        return False

    @staticmethod
    async def search_books(
        query: str,
        page: int = 1,
        per_page: int = 20,
        category: Optional[str] = None
    ):
        """
        Search sermons by title, author, description, or keywords.

        Args:
            query: Search query
            page: Page number
            per_page: Items per page
            category: Optional category filter

        Returns:
            Tuple of (books list, total count)
        """
        db = get_db()

        # Build search query with text search across multiple fields
        search_filter = {
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"author": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"metadata.summary": {"$regex": query, "$options": "i"}},
                {"metadata.themes": {"$regex": query, "$options": "i"}}
            ],
            "processing_status": "ready",
            "processed": True
        }

        # Add category filter if specified
        if category:
            search_filter["metadata.genre"] = category

        # Calculate skip from page number
        skip = (page - 1) * per_page

        # Get total count
        total = await db.books.count_documents(search_filter)

        # Get books for current page
        cursor = db.books.find(search_filter).sort("created_at", -1).skip(skip).limit(per_page)
        books = []

        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            # Convert to dict format expected by route
            book_dict = {
                "id": doc["book_id"],
                "title": doc["title"],
                "author": doc["author"],
                "description": doc.get("description") or doc.get("metadata", {}).get("summary", ""),
                "cover_url": doc.get("cover_url"),
                "author_image_url": doc.get("author_image_url"),  # Dynamic author photo URL
                "duration": doc.get("metadata", {}).get("estimated_reading_time_minutes", 0),
                "genre": doc.get("metadata", {}).get("genre", []),
                "progress": None
            }
            books.append(book_dict)

        logger.info(f"Search '{query}' found {total} results (page={page}, category={category})")
        return books, total

    @staticmethod
    async def get_book_count() -> int:
        """
        Get total book count.

        Returns:
            Number of books
        """
        db = get_db()
        return await db.books.count_documents({})

    @staticmethod
    async def get_ready_book_count() -> int:
        """
        Get count of ready books.

        Returns:
            Number of ready books
        """
        db = get_db()
        return await db.books.count_documents({"processing_status": "ready"})

    @staticmethod
    async def get_continue_reading(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get user's in-progress books for Continue Reading shelf.

        Args:
            user_id: User identifier
            limit: Maximum number of books to return

        Returns:
            List of books with progress > 0 and < 100
        """
        db = get_db()

        # Get reading sessions that are in progress (not completed, with some progress)
        cursor = db.reading_sessions.find({
            "user_id": user_id,
            "completed": False,
            "$or": [
                {"current_chunk_index": {"$gt": 0}},
                {"total_time_spent_minutes": {"$gt": 0}}
            ]
        }).sort("last_accessed", -1).limit(limit)

        books = []
        async for session in cursor:
            # Fetch book details
            book_doc = await db.books.find_one({"book_id": session["book_id"]})
            if book_doc:
                book_dict = {
                    "id": book_doc["book_id"],
                    "title": book_doc["title"],
                    "author": book_doc["author"],
                    "description": book_doc.get("description"),
                    "cover_url": book_doc.get("cover_url"),
                    "author_image_url": book_doc.get("author_image_url"),  # Dynamic author photo URL
                    "duration": book_doc.get("metadata", {}).get("duration_minutes", 0),
                    "genre": book_doc.get("genre"),
                    "progress": session.get("progress_percentage", 0)
                }
                books.append(book_dict)

        logger.info(f"Found {len(books)} in-progress books for user {user_id}")
        return books

    @staticmethod
    async def get_reading_session(
        book_id: str,
        user_id: str,
        chapter_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get or create a reading session for a user and book.

        Args:
            book_id: Book identifier
            user_id: User identifier
            chapter_id: Optional starting chapter

        Returns:
            Reading session with book details

        Raises:
            ValueError: If book not found
        """
        db = get_db()

        # Get book details
        book = await BookService.get_book(book_id, user_id)
        if not book:
            raise ValueError(f"Book {book_id} not found")

        # Get or create session
        session = await db.reading_sessions.find_one({
            "user_id": user_id,
            "book_id": book_id
        })

        if not session:
            # Create new session
            session_id = f"session_{uuid.uuid4().hex[:12]}"
            session = {
                "session_id": session_id,
                "user_id": user_id,
                "book_id": book_id,
                "current_position": 0,
                "progress_percentage": 0,
                "started_at": datetime.now(),
                "updated_at": datetime.now()
            }
            await db.reading_sessions.insert_one(session)
            logger.info(f"Created new reading session: {session_id}")
        else:
            session_id = session.get("session_id", f"session_{uuid.uuid4().hex[:12]}")

        return {
            "book": book,
            "session_id": session_id,
            "started_at": session["started_at"].isoformat() if isinstance(session["started_at"], datetime) else session["started_at"]
        }

    @staticmethod
    async def update_progress(
        user_id: str,
        book_id: str,
        position: int,
        progress: Optional[int] = None
    ) -> None:
        """
        Update user's reading progress.

        Args:
            user_id: User identifier
            book_id: Book identifier
            position: Current position in seconds
            progress: Optional progress percentage (0-100)
        """
        db = get_db()

        # Update or create session
        update_data = {
            "current_position": position,
            "updated_at": datetime.now()
        }

        if progress is not None:
            update_data["progress_percentage"] = progress

        result = await db.reading_sessions.update_one(
            {"user_id": user_id, "book_id": book_id},
            {
                "$set": update_data,
                "$setOnInsert": {
                    "session_id": f"session_{uuid.uuid4().hex[:12]}",
                    "started_at": datetime.now()
                }
            },
            upsert=True
        )

        logger.info(f"Updated reading progress for user {user_id}, book {book_id}: position={position}, progress={progress}")


    @staticmethod
    async def list_books_by_uploader(
        uploader_id: str,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None
    ):
        """
        List books uploaded by a specific user.

        Args:
            uploader_id: User ID of the uploader
            page: Page number (1-indexed)
            per_page: Items per page
            status: Optional filter by processing status

        Returns:
            Tuple of (books list, total count)
        """
        db = get_db()
        query = {"uploaded_by": uploader_id}

        if status:
            query["processing_status"] = status

        # Calculate skip from page number
        skip = (page - 1) * per_page

        # Get total count
        total = await db.books.count_documents(query)

        # Get books for current page
        cursor = db.books.find(query).sort("created_at", -1).skip(skip).limit(per_page)
        books = []

        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            book_dict = {
                "id": doc["book_id"],
                "title": doc["title"],
                "author": doc["author"],
                "description": doc.get("description"),
                "cover_url": doc.get("cover_url"),
                "author_image_url": doc.get("author_image_url"),  # Dynamic author photo URL
                "duration": doc.get("metadata", {}).get("duration_minutes", 0),
                "genre": doc.get("genre"),
                "processing_status": doc.get("processing_status", "pending"),
                "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
                "progress": None
            }
            books.append(book_dict)

        logger.info(f"Listed {len(books)} books for uploader {uploader_id} (page={page}, total={total})")
        return books, total

    @staticmethod
    async def can_user_manage_book(user_id: str, book_id: str, is_admin: bool = False) -> bool:
        """
        Check if a user can manage (edit/delete) a book.

        Admins can manage any book. Regular users can only manage their own uploads.

        Args:
            user_id: User ID
            book_id: Book identifier
            is_admin: Whether the user is an admin

        Returns:
            True if user can manage the book, False otherwise
        """
        if is_admin:
            return True

        db = get_db()
        book = await db.books.find_one({"book_id": book_id})

        if not book:
            return False

        return book.get("uploaded_by") == user_id

    @staticmethod
    async def get_book_uploader(book_id: str) -> Optional[str]:
        """
        Get the uploader ID for a book.

        Args:
            book_id: Book identifier

        Returns:
            User ID of the uploader, or None if not found
        """
        db = get_db()
        book = await db.books.find_one({"book_id": book_id}, {"uploaded_by": 1})

        if book:
            return book.get("uploaded_by")
        return None

    @staticmethod
    def get_book_visibility_filter(
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        include_hidden: bool = False
    ) -> Dict[str, Any]:
        """
        Build MongoDB query filter based on user role and visibility rules.

        Visibility Rules:
        - Anonymous: Only public books
        - User: Public books + own books
        - Admin: Everything (optionally include hidden)
        - Always exclude deleted books (unless admin with include_hidden)

        Args:
            user_id: User ID (None for anonymous)
            user_role: User role (admin, superadmin, author, user, None)
            include_hidden: Whether to include hidden books (admin only)

        Returns:
            MongoDB query filter dict
        """
        query: Dict[str, Any] = {}

        # Always exclude deleted books unless admin specifically includes them
        if not (user_role in ["admin", "superadmin"] and include_hidden):
            query["is_deleted"] = {"$ne": True}

        # Admin can see everything (including hidden if requested)
        if user_role in ["admin", "superadmin"]:
            if not include_hidden:
                query["is_hidden"] = {"$ne": True}
            return query

        # Always exclude hidden books for non-admin users
        query["is_hidden"] = {"$ne": True}

        # Anonymous users: only public books
        if not user_id:
            query["visibility"] = "public"
            return query

        # Authenticated users: public books OR own books (any visibility)
        query["$or"] = [
            {"visibility": "public"},
            {"uploaded_by": user_id}
        ]

        return query

    @staticmethod
    async def can_user_access_book(
        book_id: str,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if a user can access a specific book.

        Access Rules:
        - Public: Anyone
        - Unlisted: Anyone with link
        - Private: Must be in user's library OR be the uploader
        - Draft: Only uploader
        - Hidden: Admin OR uploader (with badge)
        - Deleted: Only admin

        Args:
            book_id: Book identifier
            user_id: User ID (None for anonymous)
            user_role: User role (admin, superadmin, author, user, None)

        Returns:
            Dict with:
                - can_access (bool): Whether user can access the book
                - book (dict): Book document if accessible
                - visibility_badge (str): Badge to show (e.g., "Hidden by Admin")
                - reason (str): Reason for access denial if can_access is False
        """
        db = get_db()
        book = await db.books.find_one({"book_id": book_id})

        if not book:
            return {
                "can_access": False,
                "book": None,
                "visibility_badge": None,
                "reason": "Book not found"
            }

        is_uploader = user_id and book.get("uploaded_by") == user_id
        is_admin = user_role in ["admin", "superadmin"]

        # Check if book is deleted
        if book.get("is_deleted", False):
            if is_admin:
                return {
                    "can_access": True,
                    "book": book,
                    "visibility_badge": "Deleted (Admin View)",
                    "reason": None
                }
            return {
                "can_access": False,
                "book": None,
                "visibility_badge": None,
                "reason": "Book has been deleted"
            }

        # Check if book is hidden
        if book.get("is_hidden", False):
            if is_admin:
                return {
                    "can_access": True,
                    "book": book,
                    "visibility_badge": "Hidden by Admin",
                    "reason": None
                }
            if is_uploader:
                return {
                    "can_access": True,
                    "book": book,
                    "visibility_badge": f"Hidden by Admin: {book.get('hidden_reason', 'No reason provided')}",
                    "reason": None
                }
            return {
                "can_access": False,
                "book": None,
                "visibility_badge": None,
                "reason": "Book is not available"
            }

        visibility = book.get("visibility", "private")

        # Public books: anyone can access
        if visibility == "public":
            return {
                "can_access": True,
                "book": book,
                "visibility_badge": None,
                "reason": None
            }

        # Unlisted books: anyone with link can access
        if visibility == "unlisted":
            return {
                "can_access": True,
                "book": book,
                "visibility_badge": "Unlisted" if is_uploader or is_admin else None,
                "reason": None
            }

        # Draft books: only uploader
        if visibility == "draft":
            if is_uploader or is_admin:
                return {
                    "can_access": True,
                    "book": book,
                    "visibility_badge": "Draft",
                    "reason": None
                }
            return {
                "can_access": False,
                "book": None,
                "visibility_badge": None,
                "reason": "Book is in draft mode"
            }

        # Private books: must be in user's library OR be uploader
        if visibility == "private":
            if is_uploader or is_admin:
                return {
                    "can_access": True,
                    "book": book,
                    "visibility_badge": "Private" if is_uploader else None,
                    "reason": None
                }

            # Check if user has book in library
            if user_id:
                user = await db.users.find_one({"user_id": user_id})
                if user:
                    library_books = user.get("library_books", [])
                    has_access = any(
                        lib_book.get("book_id") == book_id
                        for lib_book in library_books
                    )
                    if has_access:
                        return {
                            "can_access": True,
                            "book": book,
                            "visibility_badge": None,
                            "reason": None
                        }

            return {
                "can_access": False,
                "book": None,
                "visibility_badge": None,
                "reason": "You need access to this book. Contact the author."
            }

        # Unknown visibility state - deny by default
        return {
            "can_access": False,
            "book": None,
            "visibility_badge": None,
            "reason": "Invalid book visibility state"
        }

    @staticmethod
    async def hide_book(
        book_id: str,
        admin_id: str,
        admin_email: str,
        admin_role: str,
        reason: str
    ) -> bool:
        """
        Hide a book (admin action).

        Hidden books are only visible to the uploader and admins.
        Creates an audit log entry.

        Args:
            book_id: Book identifier
            admin_id: Admin user ID
            admin_email: Admin email
            admin_role: Admin role
            reason: Reason for hiding (required)

        Returns:
            True if successfully hidden, False otherwise
        """
        db = get_db()

        # Get current book state for audit log
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            return False

        # Update book
        result = await db.books.update_one(
            {"book_id": book_id},
            {
                "$set": {
                    "is_hidden": True,
                    "hidden_by": admin_id,
                    "hidden_by_email": admin_email,
                    "hidden_at": datetime.utcnow(),
                    "hidden_reason": reason,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:
            # Create audit log
            from app.services.audit_log_service import AuditLogService
            from app.models.audit_log import AuditAction

            audit_service = AuditLogService(db)
            await audit_service.log_action(
                action=AuditAction.BOOK_HIDDEN,
                entity_id=book_id,
                actor_id=admin_id,
                actor_email=admin_email,
                actor_role=admin_role,
                reason=reason,
                changes={
                    "is_hidden": {"before": book.get("is_hidden", False), "after": True}
                },
                metadata={
                    "book_title": book.get("title"),
                    "book_author": book.get("author"),
                    "uploader_id": book.get("uploaded_by")
                }
            )

            logger.info(f"Book {book_id} hidden by admin {admin_email}. Reason: {reason}")
            return True

        return False

    @staticmethod
    async def unhide_book(
        book_id: str,
        admin_id: str,
        admin_email: str,
        admin_role: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Restore a hidden book (admin action).

        Creates an audit log entry.

        Args:
            book_id: Book identifier
            admin_id: Admin user ID
            admin_email: Admin email
            admin_role: Admin role
            reason: Optional reason for restoring

        Returns:
            True if successfully restored, False otherwise
        """
        db = get_db()

        # Get current book state for audit log
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            return False

        # Update book
        result = await db.books.update_one(
            {"book_id": book_id},
            {
                "$set": {
                    "is_hidden": False,
                    "updated_at": datetime.utcnow()
                },
                "$unset": {
                    "hidden_by": "",
                    "hidden_by_email": "",
                    "hidden_at": "",
                    "hidden_reason": ""
                }
            }
        )

        if result.modified_count > 0:
            # Create audit log
            from app.services.audit_log_service import AuditLogService
            from app.models.audit_log import AuditAction

            audit_service = AuditLogService(db)
            await audit_service.log_action(
                action=AuditAction.BOOK_UNHIDDEN,
                entity_id=book_id,
                actor_id=admin_id,
                actor_email=admin_email,
                actor_role=admin_role,
                reason=reason,
                changes={
                    "is_hidden": {"before": True, "after": False}
                },
                metadata={
                    "book_title": book.get("title"),
                    "book_author": book.get("author"),
                    "uploader_id": book.get("uploaded_by")
                }
            )

            logger.info(f"Book {book_id} unhidden by admin {admin_email}")
            return True

        return False

    @staticmethod
    async def soft_delete_book(
        book_id: str,
        admin_id: str,
        admin_email: str,
        admin_role: str,
        reason: str
    ) -> bool:
        """
        Soft delete a book (admin action).

        Book is marked as deleted but can be restored.
        Creates an audit log entry.

        Args:
            book_id: Book identifier
            admin_id: Admin user ID
            admin_email: Admin email
            admin_role: Admin role
            reason: Reason for deletion (required)

        Returns:
            True if successfully deleted, False otherwise
        """
        db = get_db()

        # Get current book state for audit log
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            return False

        # Update book
        result = await db.books.update_one(
            {"book_id": book_id},
            {
                "$set": {
                    "is_deleted": True,
                    "deleted_by": admin_id,
                    "deleted_by_email": admin_email,
                    "deleted_at": datetime.utcnow(),
                    "deletion_reason": reason,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:
            # Create audit log
            from app.services.audit_log_service import AuditLogService
            from app.models.audit_log import AuditAction

            audit_service = AuditLogService(db)
            await audit_service.log_action(
                action=AuditAction.BOOK_DELETED,
                entity_id=book_id,
                actor_id=admin_id,
                actor_email=admin_email,
                actor_role=admin_role,
                reason=reason,
                changes={
                    "is_deleted": {"before": book.get("is_deleted", False), "after": True}
                },
                metadata={
                    "book_title": book.get("title"),
                    "book_author": book.get("author"),
                    "uploader_id": book.get("uploaded_by")
                }
            )

            logger.info(f"Book {book_id} soft deleted by admin {admin_email}. Reason: {reason}")
            return True

        return False

    @staticmethod
    async def restore_book(
        book_id: str,
        admin_id: str,
        admin_email: str,
        admin_role: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Restore a soft-deleted book (admin action).

        Creates an audit log entry.

        Args:
            book_id: Book identifier
            admin_id: Admin user ID
            admin_email: Admin email
            admin_role: Admin role
            reason: Optional reason for restoring

        Returns:
            True if successfully restored, False otherwise
        """
        db = get_db()

        # Get current book state for audit log
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            return False

        # Update book
        result = await db.books.update_one(
            {"book_id": book_id},
            {
                "$set": {
                    "is_deleted": False,
                    "updated_at": datetime.utcnow()
                },
                "$unset": {
                    "deleted_by": "",
                    "deleted_by_email": "",
                    "deleted_at": "",
                    "deletion_reason": ""
                }
            }
        )

        if result.modified_count > 0:
            # Create audit log
            from app.services.audit_log_service import AuditLogService
            from app.models.audit_log import AuditAction

            audit_service = AuditLogService(db)
            await audit_service.log_action(
                action=AuditAction.BOOK_RESTORED,
                entity_id=book_id,
                actor_id=admin_id,
                actor_email=admin_email,
                actor_role=admin_role,
                reason=reason,
                changes={
                    "is_deleted": {"before": True, "after": False}
                },
                metadata={
                    "book_title": book.get("title"),
                    "book_author": book.get("author"),
                    "uploader_id": book.get("uploaded_by")
                }
            )

            logger.info(f"Book {book_id} restored by admin {admin_email}")
            return True

        return False

    @staticmethod
    async def change_visibility(
        book_id: str,
        new_visibility: str,
        user_id: str,
        user_email: str,
        user_role: str
    ) -> Dict[str, Any]:
        """
        Change book visibility (author or admin action).

        Creates an audit log entry.

        Args:
            book_id: Book identifier
            new_visibility: New visibility state (draft, unlisted, private, public)
            user_id: User ID making the change
            user_email: User email
            user_role: User role

        Returns:
            Dict with:
                - success (bool): Whether change was successful
                - book (dict): Updated book document if successful
                - error (str): Error message if unsuccessful
        """
        from app.models.book import BookVisibility
        from app.services.audit_log_service import AuditLogService
        from app.models.audit_log import AuditAction

        # Validate visibility value
        valid_visibilities = [v.value for v in BookVisibility]
        if new_visibility not in valid_visibilities:
            return {
                "success": False,
                "book": None,
                "error": f"Invalid visibility. Must be one of: {', '.join(valid_visibilities)}"
            }

        db = get_db()

        # Get current book
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            return {
                "success": False,
                "book": None,
                "error": "Book not found"
            }

        # Check permission: uploader or admin
        is_uploader = book.get("uploaded_by") == user_id
        is_admin = user_role in ["admin", "superadmin"]

        if not (is_uploader or is_admin):
            return {
                "success": False,
                "book": None,
                "error": "Only the book uploader or admin can change visibility"
            }

        old_visibility = book.get("visibility", "private")

        # No change needed
        if old_visibility == new_visibility:
            return {
                "success": True,
                "book": book,
                "error": None
            }

        # Update book
        result = await db.books.update_one(
            {"book_id": book_id},
            {
                "$set": {
                    "visibility": new_visibility,
                    "visibility_changed_at": datetime.utcnow(),
                    "visibility_changed_by": user_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:
            # Create audit log
            audit_service = AuditLogService(db)
            await audit_service.log_action(
                action=AuditAction.VISIBILITY_CHANGED,
                entity_id=book_id,
                actor_id=user_id,
                actor_email=user_email,
                actor_role=user_role,
                reason=None,
                changes={
                    "visibility": {"before": old_visibility, "after": new_visibility}
                },
                metadata={
                    "book_title": book.get("title"),
                    "book_author": book.get("author"),
                    "uploader_id": book.get("uploaded_by")
                }
            )

            # Get updated book
            updated_book = await db.books.find_one({"book_id": book_id})

            logger.info(f"Book {book_id} visibility changed from {old_visibility} to {new_visibility} by {user_email}")

            return {
                "success": True,
                "book": updated_book,
                "error": None
            }

        return {
            "success": False,
            "book": None,
            "error": "Failed to update book visibility"
        }

    @staticmethod
    async def update_book(
        book_id: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        description: Optional[str] = None,
        cover_url: Optional[str] = None,
        genre: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update book metadata.

        Args:
            book_id: Book identifier
            title: New title (optional)
            author: New author (optional)
            description: New description (optional)
            cover_url: New cover URL (optional)
            genre: New genre (optional)

        Returns:
            Updated book dict, or None if not found
        """
        db = get_db()

        # Build update document
        update_data = {"updated_at": datetime.now()}

        if title is not None:
            update_data["title"] = title
        if author is not None:
            update_data["author"] = author
        if description is not None:
            update_data["description"] = description
        if cover_url is not None:
            update_data["cover_url"] = cover_url
        if genre is not None:
            update_data["genre"] = genre

        result = await db.books.update_one(
            {"book_id": book_id},
            {"$set": update_data}
        )

        if result.modified_count == 0:
            # Check if book exists
            exists = await db.books.find_one({"book_id": book_id})
            if not exists:
                return None

        # Return updated book
        return await BookService.get_book(book_id)

    @staticmethod
    async def delete_book_with_embeddings(book_id: str) -> bool:
        """
        Delete a book, its chunks, and its embeddings.

        Args:
            book_id: Book identifier

        Returns:
            True if deleted
        """
        # Use comprehensive delete
        return await BookService.delete_book_complete(book_id, delete_source_file=True)

    @staticmethod
    async def delete_book_complete(
        book_id: str,
        delete_source_file: bool = True
    ) -> bool:
        """
        Comprehensively delete a book and ALL associated data.

        Deletes:
        - Embeddings from pgvector
        - Book chunks from MongoDB
        - Reading sessions from MongoDB
        - Interactions from MongoDB
        - Book voice settings from MongoDB
        - Bookmarks from MongoDB
        - Storage files (PDF, covers, audio) from Hetzner/local
        - Local audio cache files
        - Book record from MongoDB

        Args:
            book_id: Book identifier
            delete_source_file: Whether to delete the source PDF file

        Returns:
            True if deleted successfully
        """
        db = get_db()
        deleted_items = {
            "embeddings": 0,
            "chunks": 0,
            "reading_sessions": 0,
            "interactions": 0,
            "voice_settings": 0,
            "storage_files": False,
            "audio_cache": 0,
            "book": False
        }

        # 1. Delete embeddings from pgvector
        try:
            from app.services.embedding_service import get_embedding_service
            embedding_service = await get_embedding_service()
            deleted_items["embeddings"] = await embedding_service.delete_book_embeddings(book_id)
            logger.info(f"Deleted {deleted_items['embeddings']} embeddings for book {book_id}")
        except Exception as e:
            logger.warning(f"Failed to delete embeddings for book {book_id}: {e}")

        # 2. Delete book chunks
        result = await db.book_chunks.delete_many({"book_id": book_id})
        deleted_items["chunks"] = result.deleted_count
        logger.info(f"Deleted {deleted_items['chunks']} chunks for book {book_id}")

        # 3. Delete reading sessions (includes bookmarks)
        result = await db.reading_sessions.delete_many({"book_id": book_id})
        deleted_items["reading_sessions"] = result.deleted_count
        logger.info(f"Deleted {deleted_items['reading_sessions']} reading sessions for book {book_id}")

        # 4. Delete interactions
        result = await db.interactions.delete_many({"book_id": book_id})
        deleted_items["interactions"] = result.deleted_count
        logger.info(f"Deleted {deleted_items['interactions']} interactions for book {book_id}")

        # 5. Delete book voice settings
        result = await db.book_voice_settings.delete_many({"book_id": book_id})
        deleted_items["voice_settings"] = result.deleted_count
        logger.info(f"Deleted {deleted_items['voice_settings']} voice settings for book {book_id}")

        # 6. Delete storage files (Hetzner/local PDF, covers, audio)
        if delete_source_file:
            try:
                from app.services.storage_service import get_storage_service
                storage_service = await get_storage_service()
                await storage_service.delete_book_files(book_id)
                deleted_items["storage_files"] = True
                logger.info(f"Deleted storage files for book {book_id}")
            except Exception as e:
                logger.warning(f"Failed to delete storage files for book {book_id}: {e}")

        # 7. Delete local audio cache files
        try:
            deleted_items["audio_cache"] = await BookService._delete_audio_cache(book_id)
            logger.info(f"Deleted {deleted_items['audio_cache']} audio cache files for book {book_id}")
        except Exception as e:
            logger.warning(f"Failed to delete audio cache for book {book_id}: {e}")

        # 8. Delete book record
        result = await db.books.delete_one({"book_id": book_id})
        deleted_items["book"] = result.deleted_count > 0

        if deleted_items["book"]:
            logger.info(f"✅ Completely deleted book {book_id}: {deleted_items}")
            return True

        logger.warning(f"Book {book_id} not found in database")
        return False

    @staticmethod
    async def _delete_audio_cache(book_id: str) -> int:
        """
        Delete local audio cache files for a book.

        Audio files are stored in /opt/kasaai/apps/inkwave/backend/storage/audiobooks/
        with naming pattern: book_{id}_chunk_{index}*.mp3 and *.meta

        Args:
            book_id: Book identifier

        Returns:
            Number of files deleted
        """
        import glob
        import os

        cache_dir = "/opt/kasaai/apps/inkwave/backend/storage/audiobooks"
        if not os.path.exists(cache_dir):
            return 0

        # Find all files matching the book_id pattern
        patterns = [
            f"{book_id}_*.mp3",
            f"{book_id}_*.mp3.meta",
            f"{book_id}_*.wav",
            f"{book_id}_*.wav.meta"
        ]

        deleted_count = 0
        for pattern in patterns:
            for file_path in glob.glob(os.path.join(cache_dir, pattern)):
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete audio cache file {file_path}: {e}")

        return deleted_count

    @staticmethod
    async def cleanup_for_reprocessing(book_id: str) -> Dict[str, Any]:
        """
        Clean up book data for reprocessing WITHOUT deleting the source PDF.

        Keeps:
        - Book record (with reset status)
        - Source PDF file

        Deletes:
        - Embeddings
        - Chunks
        - Audio cache
        - Voice settings

        Args:
            book_id: Book identifier

        Returns:
            Cleanup summary
        """
        db = get_db()
        cleanup_result = {
            "book_id": book_id,
            "embeddings_deleted": 0,
            "chunks_deleted": 0,
            "audio_cache_deleted": 0,
            "voice_settings_deleted": 0,
            "status_reset": False
        }

        # 1. Delete embeddings from pgvector
        try:
            from app.services.embedding_service import get_embedding_service
            embedding_service = await get_embedding_service()
            cleanup_result["embeddings_deleted"] = await embedding_service.delete_book_embeddings(book_id)
        except Exception as e:
            logger.warning(f"Failed to delete embeddings for reprocessing {book_id}: {e}")

        # 2. Delete book chunks
        result = await db.book_chunks.delete_many({"book_id": book_id})
        cleanup_result["chunks_deleted"] = result.deleted_count

        # 3. Delete local audio cache files
        try:
            cleanup_result["audio_cache_deleted"] = await BookService._delete_audio_cache(book_id)
        except Exception as e:
            logger.warning(f"Failed to delete audio cache for reprocessing {book_id}: {e}")

        # 4. Delete voice settings (will be regenerated)
        result = await db.book_voice_settings.delete_many({"book_id": book_id})
        cleanup_result["voice_settings_deleted"] = result.deleted_count

        # 5. Reset book processing status
        result = await db.books.update_one(
            {"book_id": book_id},
            {
                "$set": {
                    "processed": False,
                    "processing_status": "pending",
                    "processing_stage": "cleanup_complete",
                    "processing_progress": 0,
                    "processing_message": "Ready for reprocessing",
                    "processing_error": None,
                    "chapters": [],
                    "metadata.topics": [],
                    "updated_at": datetime.now()
                }
            }
        )
        cleanup_result["status_reset"] = result.modified_count > 0

        logger.info(f"✅ Cleaned up book {book_id} for reprocessing: {cleanup_result}")
        return cleanup_result

    @staticmethod
    async def reprocess_book(
        book_id: str,
        user_id: str,
        use_ai_chapter_detection: bool = False
    ) -> Dict[str, Any]:
        """
        Reprocess an existing book.

        1. Cleans up existing processed data
        2. Re-runs the processing pipeline
        3. Triggers audio pre-generation

        Args:
            book_id: Book identifier
            user_id: User requesting reprocessing (for voice settings)
            use_ai_chapter_detection: If True, use Gemini AI for enhanced chapter
                detection (for non-standard chapter formats). Default: False

        Returns:
            Reprocessing status

        Raises:
            ValueError: If book not found or PDF not available
        """
        db = get_db()

        # Get book record
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            raise ValueError(f"Book {book_id} not found")

        # Get PDF path
        pdf_path = book.get("pdf_url") or book.get("storage", {}).get("pdf_path")
        storage_type = book.get("storage", {}).get("storage_type", "local")
        
        if not pdf_path:
            raise ValueError(f"PDF file not found for book {book_id}")

        # Resolve PDF path
        local_pdf_path = f"/opt/kasaai/apps/inkwave/backend/storage/books/{book_id}.pdf"
        
        if pdf_path.startswith("/api/"):
            # It's a storage API path, use local path
            pdf_path = local_pdf_path
        elif storage_type == "hetzner":
            # PDF is in Hetzner, need to download it
            pdf_path = local_pdf_path

        # Check if PDF exists locally
        if not os.path.exists(pdf_path):
            # Try to download from Hetzner or storage service
            try:
                from app.services.storage_service import get_storage_service
                storage_service = await get_storage_service()
                pdf_content = await storage_service.download_book_pdf(book_id)
                if pdf_content:
                    # Save temporarily for processing
                    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                    with open(pdf_path, "wb") as f:
                        f.write(pdf_content)
                    logger.info(f"Downloaded PDF from storage for reprocessing: {len(pdf_content)} bytes")
                else:
                    # Try alternative: check if we can access via storage API
                    # For now, raise error but with helpful message
                    raise ValueError(
                        f"PDF file not available for book {book_id}. "
                        f"Storage type: {storage_type}. "
                        f"Please ensure Hetzner credentials are configured or PDF is accessible."
                    )
            except Exception as e:
                # If download fails, check if we can proceed with existing chunks
                # (for metadata-only updates)
                logger.warning(f"Could not download PDF for reprocessing: {e}")
                raise ValueError(
                    f"Cannot retrieve PDF for book {book_id}: {e}. "
                    f"Please ensure storage is configured correctly."
                )

        # Step 1: Cleanup existing data
        cleanup_result = await BookService.cleanup_for_reprocessing(book_id)

        # Step 2: Update status to processing
        await db.books.update_one(
            {"book_id": book_id},
            {
                "$set": {
                    "processing_status": "processing",
                    "processing_stage": "reprocessing",
                    "processing_progress": 5,
                    "processing_message": "Starting reprocessing...",
                    "updated_at": datetime.now()
                }
            }
        )

        # Step 3: Re-run processing
        try:
            processing_service = await get_book_processing_service()

            # Prepare metadata from existing book
            # IMPORTANT: Preserve content_metadata (skip_to_chunk, etc.) during reprocessing
            metadata = {
                "title": book.get("title", "Unknown"),
                "author": book.get("author", "Unknown"),
                "description": book.get("description"),
                "cover_url": book.get("cover_url"),
                "genre": book.get("genre"),
                "content_metadata": book.get("content_metadata")  # Preserve TOC skip settings
            }

            # Process the book
            processed_book = await processing_service.process_book_file(
                pdf_path,
                metadata,
                user_id,
                book_id=book_id,  # Use existing book_id
                use_ai_chapter_detection=use_ai_chapter_detection
            )

            return {
                "book_id": book_id,
                "status": "success",
                "message": "Book reprocessed successfully",
                "cleanup": cleanup_result,
                "chapters": len(processed_book.chapters),
                "processing_status": processed_book.processing_status
            }

        except Exception as e:
            # Update book status to error
            await db.books.update_one(
                {"book_id": book_id},
                {
                    "$set": {
                        "processing_status": "error",
                        "processing_stage": "reprocessing_failed",
                        "processing_error": str(e)[:200],
                        "processing_message": f"Reprocessing failed: {str(e)[:100]}",
                        "updated_at": datetime.now()
                    }
                }
            )
            raise

    @staticmethod
    async def update_chapter_durations(book_id: str) -> Dict[str, Any]:
        """
        Calculate and update chapter durations from chunk audio durations.

        Call this after audio has been generated for a book's chunks.

        Args:
            book_id: Book identifier

        Returns:
            Summary of updated chapters
        """
        db = get_db()

        # Get book with chapters
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            return {"error": f"Book {book_id} not found"}

        chapters = book.get("chapters", [])
        if not chapters:
            return {"book_id": book_id, "chapters_updated": 0, "message": "No chapters"}

        # Calculate duration for each chapter from chunk audio
        updated_chapters = []
        cumulative_time = 0
        chapters_with_audio = 0

        for chapter in chapters:
            start_idx = chapter.get("start_chunk_id", 0)
            end_idx = chapter.get("end_chunk_id", 0)

            # Sum audio duration for chunks in this chapter
            pipeline = [
                {
                    "$match": {
                        "book_id": book_id,
                        "chunk_index": {"$gte": start_idx, "$lte": end_idx},
                        "audio_duration": {"$exists": True, "$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_duration": {"$sum": "$audio_duration"}
                    }
                }
            ]

            result = await db.book_chunks.aggregate(pipeline).to_list(length=1)
            chapter_duration = int(result[0]["total_duration"]) if result else None

            # Update chapter with calculated values
            chapter["start_time"] = cumulative_time if chapter_duration else None
            chapter["duration"] = chapter_duration

            if chapter_duration:
                cumulative_time += chapter_duration
                chapters_with_audio += 1

            updated_chapters.append(chapter)

        # Update book with new chapter durations
        await db.books.update_one(
            {"book_id": book_id},
            {
                "$set": {
                    "chapters": updated_chapters,
                    "updated_at": datetime.now()
                }
            }
        )

        logger.info(
            f"✅ Updated chapter durations for {book_id}: "
            f"{chapters_with_audio}/{len(chapters)} chapters have audio"
        )

        return {
            "book_id": book_id,
            "chapters_updated": chapters_with_audio,
            "total_chapters": len(chapters),
            "total_duration_seconds": cumulative_time
        }


# Global book service instance
book_service = BookService()
