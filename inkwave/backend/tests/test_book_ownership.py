"""
Unit tests for Book Ownership Service.

Tests author book management with real MongoDB data.
"""

import pytest
import asyncio
import uuid
from datetime import datetime

import sys
sys.path.insert(0, '/opt/kasaai/apps/shared')

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.services.book_service import BookService


@pytest.fixture
async def db_client():
    """Create MongoDB client."""
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    yield client
    client.close()


@pytest.fixture
async def test_db(db_client):
    """Get test database."""
    return db_client[settings.MONGODB_DB_NAME]


@pytest.fixture
def test_author_id():
    """Generate unique test author ID."""
    return f"test_author_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def other_user_id():
    """Generate unique other user ID."""
    return f"other_user_{uuid.uuid4().hex[:8]}"


@pytest.fixture
async def create_author_books(test_db, test_author_id):
    """Create test books for author."""
    books = []
    for i in range(5):
        book_doc = {
            "book_id": f"test_book_{uuid.uuid4().hex[:8]}",
            "title": f"Test Book {i + 1}",
            "author": "Test Author",
            "uploader_id": test_author_id,
            "uploaded_by": test_author_id,
            "description": f"Description for test book {i + 1}",
            "processing_status": "ready" if i < 3 else "processing",
            "processed": i < 3,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "genre": ["Fiction", "Test"],
        }
        await test_db.books.insert_one(book_doc)
        books.append(book_doc)

    yield books

    # Cleanup
    for book in books:
        await test_db.books.delete_one({"book_id": book["book_id"]})


@pytest.fixture
async def create_single_book(test_db, test_author_id):
    """Create single test book."""
    book_doc = {
        "book_id": f"test_book_{uuid.uuid4().hex[:8]}",
        "title": "Single Test Book",
        "author": "Test Author",
        "uploader_id": test_author_id,
        "uploaded_by": test_author_id,
        "description": "A single test book",
        "processing_status": "ready",
        "processed": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "genre": ["Fiction"],
        "cover_url": "https://example.com/cover.jpg",
    }
    await test_db.books.insert_one(book_doc)
    yield book_doc

    # Cleanup
    await test_db.books.delete_one({"book_id": book_doc["book_id"]})


class TestListBooksByUploader:
    """Tests for listing books by uploader."""

    @pytest.mark.asyncio
    async def test_list_books_returns_correct_count(
        self, test_author_id, create_author_books
    ):
        """Test listing all books for author."""
        books, total = await BookService.list_books_by_uploader(
            uploader_id=test_author_id,
            page=1,
            per_page=10
        )

        assert total == 5
        assert len(books) == 5

    @pytest.mark.asyncio
    async def test_list_books_pagination(
        self, test_author_id, create_author_books
    ):
        """Test pagination works correctly."""
        # First page
        books1, total1 = await BookService.list_books_by_uploader(
            uploader_id=test_author_id,
            page=1,
            per_page=2
        )
        assert len(books1) == 2
        assert total1 == 5

        # Second page
        books2, total2 = await BookService.list_books_by_uploader(
            uploader_id=test_author_id,
            page=2,
            per_page=2
        )
        assert len(books2) == 2

        # Books should be different
        ids1 = {b["id"] for b in books1}
        ids2 = {b["id"] for b in books2}
        assert ids1.isdisjoint(ids2)

    @pytest.mark.asyncio
    async def test_list_books_status_filter(
        self, test_author_id, create_author_books
    ):
        """Test filtering by processing status."""
        # Ready books only
        books, total = await BookService.list_books_by_uploader(
            uploader_id=test_author_id,
            page=1,
            per_page=10,
            status="ready"
        )

        assert total == 3
        for book in books:
            assert book["processing_status"] == "ready"

    @pytest.mark.asyncio
    async def test_list_books_empty_for_unknown_user(self):
        """Test listing books for user with no uploads."""
        books, total = await BookService.list_books_by_uploader(
            uploader_id="unknown_user_12345",
            page=1,
            per_page=10
        )

        assert total == 0
        assert len(books) == 0


class TestCanUserManageBook:
    """Tests for book management permission check."""

    @pytest.mark.asyncio
    async def test_owner_can_manage(
        self, test_author_id, create_single_book
    ):
        """Test book owner can manage their book."""
        can_manage = await BookService.can_user_manage_book(
            user_id=test_author_id,
            book_id=create_single_book["book_id"]
        )

        assert can_manage is True

    @pytest.mark.asyncio
    async def test_other_user_cannot_manage(
        self, other_user_id, create_single_book
    ):
        """Test non-owner cannot manage book."""
        can_manage = await BookService.can_user_manage_book(
            user_id=other_user_id,
            book_id=create_single_book["book_id"]
        )

        assert can_manage is False

    @pytest.mark.asyncio
    async def test_admin_can_manage_any(
        self, other_user_id, create_single_book
    ):
        """Test admin can manage any book."""
        can_manage = await BookService.can_user_manage_book(
            user_id=other_user_id,
            book_id=create_single_book["book_id"],
            is_admin=True
        )

        assert can_manage is True

    @pytest.mark.asyncio
    async def test_nonexistent_book_returns_false(
        self, test_author_id
    ):
        """Test non-existent book returns False."""
        can_manage = await BookService.can_user_manage_book(
            user_id=test_author_id,
            book_id="nonexistent_book_12345"
        )

        assert can_manage is False


class TestUpdateBook:
    """Tests for updating book metadata."""

    @pytest.mark.asyncio
    async def test_update_book_title(
        self, test_db, create_single_book
    ):
        """Test updating book title."""
        result = await BookService.update_book(
            book_id=create_single_book["book_id"],
            title="Updated Title"
        )

        assert result is not None

        # Verify in database
        book = await test_db.books.find_one(
            {"book_id": create_single_book["book_id"]}
        )
        assert book["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_multiple_fields(
        self, test_db, create_single_book
    ):
        """Test updating multiple book fields."""
        result = await BookService.update_book(
            book_id=create_single_book["book_id"],
            title="New Title",
            description="New description",
            author="New Author",
            genre="Non-Fiction"
        )

        assert result is not None

        # Verify in database
        book = await test_db.books.find_one(
            {"book_id": create_single_book["book_id"]}
        )
        assert book["title"] == "New Title"
        assert book["description"] == "New description"
        assert book["author"] == "New Author"
        assert book["genre"] == "Non-Fiction"

    @pytest.mark.asyncio
    async def test_update_nonexistent_book(self):
        """Test updating non-existent book returns None."""
        result = await BookService.update_book(
            book_id="nonexistent_book_12345",
            title="New Title"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_update_returns_book_dict(
        self, create_single_book
    ):
        """Test update returns updated book dict."""
        result = await BookService.update_book(
            book_id=create_single_book["book_id"],
            title="Updated Book Title"
        )

        assert result is not None
        assert result["title"] == "Updated Book Title"


class TestDeleteBook:
    """Tests for deleting books with embeddings."""

    @pytest.mark.asyncio
    async def test_delete_book_removes_from_db(
        self, test_db, test_author_id
    ):
        """Test deleting book removes it from database."""
        # Create a book to delete
        book_id = f"delete_test_{uuid.uuid4().hex[:8]}"
        book_doc = {
            "book_id": book_id,
            "title": "Book to Delete",
            "author": "Test Author",
            "uploaded_by": test_author_id,
            "created_at": datetime.utcnow(),
        }
        await test_db.books.insert_one(book_doc)

        # Verify it exists
        book = await test_db.books.find_one({"book_id": book_id})
        assert book is not None

        # Delete it
        result = await BookService.delete_book_with_embeddings(book_id)
        assert result is True

        # Verify deleted
        book = await test_db.books.find_one({"book_id": book_id})
        assert book is None

    @pytest.mark.asyncio
    async def test_delete_book_removes_chunks(
        self, test_db, test_author_id
    ):
        """Test deleting book also removes chunks."""
        # Create book with chunks
        book_id = f"delete_chunks_test_{uuid.uuid4().hex[:8]}"
        book_doc = {
            "book_id": book_id,
            "title": "Book with Chunks",
            "author": "Test Author",
            "uploaded_by": test_author_id,
            "created_at": datetime.utcnow(),
        }
        await test_db.books.insert_one(book_doc)

        # Add some chunks
        for i in range(3):
            chunk_doc = {
                "book_id": book_id,
                "chunk_index": i,
                "text": f"Chunk {i} content",
            }
            await test_db.book_chunks.insert_one(chunk_doc)

        # Verify chunks exist
        chunk_count = await test_db.book_chunks.count_documents(
            {"book_id": book_id}
        )
        assert chunk_count == 3

        # Delete book
        await BookService.delete_book_with_embeddings(book_id)

        # Verify chunks deleted
        chunk_count = await test_db.book_chunks.count_documents(
            {"book_id": book_id}
        )
        assert chunk_count == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_book(self):
        """Test deleting non-existent book returns False."""
        result = await BookService.delete_book_with_embeddings(
            "nonexistent_book_12345"
        )

        assert result is False


class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_user_with_many_books_pagination(
        self, test_db, test_author_id
    ):
        """Test pagination with many books."""
        # Create many books
        book_ids = []
        for i in range(25):
            book_id = f"many_books_{uuid.uuid4().hex[:8]}"
            book_doc = {
                "book_id": book_id,
                "title": f"Book {i + 1}",
                "author": "Test Author",
                "uploaded_by": test_author_id,
                "processing_status": "ready",
                "created_at": datetime.utcnow(),
            }
            await test_db.books.insert_one(book_doc)
            book_ids.append(book_id)

        try:
            # Get last page
            books, total = await BookService.list_books_by_uploader(
                uploader_id=test_author_id,
                page=3,
                per_page=10
            )

            assert total == 25
            assert len(books) == 5  # Last page has 5 items
        finally:
            # Cleanup
            for book_id in book_ids:
                await test_db.books.delete_one({"book_id": book_id})

    @pytest.mark.asyncio
    async def test_concurrent_access(
        self, test_db, create_single_book, test_author_id
    ):
        """Test concurrent access to same book."""
        book_id = create_single_book["book_id"]

        # Multiple concurrent permission checks
        tasks = [
            BookService.can_user_manage_book(test_author_id, book_id)
            for _ in range(10)
        ]

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(r is True for r in results)
