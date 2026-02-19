"""
Verify Book Display Script

Tests that uploaded books are visible on all user-facing pages:
1. Checks if books appear in /api/v1/books endpoint
2. Verifies book details endpoint
3. Tests search functionality
4. Checks if the demo book is present

Usage:
    python verify_book_display.py [book_id]
"""

import asyncio
import sys
from pathlib import Path
import httpx
from typing import Optional

# Configuration
BACKEND_URL = "https://inkwave-api.ailabsafrica.com/api/v1"
# BACKEND_URL = "http://localhost:30033/api/v1"  # Use for local testing


async def fetch_all_books():
    """
    Fetch all books from the API.

    Returns:
        List of books and total count
    """
    print("📚 Fetching all books from API...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BACKEND_URL}/books",
            params={"per_page": 100}
        )

        if response.status_code != 200:
            print(f"❌ Failed to fetch books: {response.status_code}")
            return [], 0

        data = response.json()
        books = data.get("books", [])
        total = data.get("total", 0)

        print(f"✅ Found {total} books in database")

        if books:
            print(f"\n📖 Books list:")
            for i, book in enumerate(books, 1):
                print(f"   {i}. {book.get('title')} by {book.get('author')}")
                print(f"      ID: {book.get('id')}")
                print(f"      Cover: {book.get('cover_url', 'N/A')[:60]}...")
        else:
            print("   ⚠️  No books found")

        return books, total


async def fetch_book_detail(book_id: str):
    """
    Fetch detailed book information.

    Args:
        book_id: Book identifier

    Returns:
        Book detail data or None
    """
    print(f"\n🔍 Fetching details for book: {book_id}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BACKEND_URL}/books/{book_id}")

        if response.status_code != 200:
            print(f"❌ Failed to fetch book: {response.status_code}")
            if response.status_code == 404:
                print("   Book not found in database")
            return None

        book = response.json()

        print(f"✅ Book details retrieved:")
        print(f"   Title: {book.get('title')}")
        print(f"   Author: {book.get('author')}")
        print(f"   Description: {book.get('description', '')[:100]}...")
        print(f"   Cover URL: {book.get('cover_url', 'N/A')}")
        print(f"   Duration: {book.get('duration', 0)} minutes")
        print(f"   Chapters: {len(book.get('chapters', []))}")
        print(f"   Pages: {book.get('metadata', {}).get('page_count', 0)}")
        print(f"   Words: {book.get('metadata', {}).get('word_count', 0)}")
        print(f"   Processing Status: {book.get('processing_status', 'unknown')}")

        return book


async def search_books(query: str):
    """
    Search for books by title or author.

    Args:
        query: Search query

    Returns:
        List of matching books
    """
    print(f"\n🔎 Searching for: '{query}'")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BACKEND_URL}/books/search",
            params={"q": query, "per_page": 20}
        )

        if response.status_code != 200:
            print(f"❌ Search failed: {response.status_code}")
            return []

        data = response.json()
        books = data.get("books", [])

        print(f"✅ Found {len(books)} matching books:")
        for i, book in enumerate(books, 1):
            print(f"   {i}. {book.get('title')} by {book.get('author')}")

        return books


async def check_demo_book():
    """
    Check if the demo book "Binding The Strong Man" exists.

    Returns:
        True if found, False otherwise
    """
    print("\n🎯 Checking for demo book...")

    # Search for the demo book
    books = await search_books("Binding The Strong Man")

    for book in books:
        if "Binding" in book.get("title", "") and "Duncan-Williams" in book.get("author", ""):
            print(f"✅ Demo book found!")
            print(f"   ID: {book.get('id')}")
            print(f"   Title: {book.get('title')}")
            return True

    print("⚠️  Demo book not found")
    return False


async def verify_user_pages():
    """
    Verify that user-facing pages can access book data.

    Tests:
    - Homepage shelves (latest, recommended)
    - All books page
    - Browse/search functionality
    """
    print("\n🌐 Verifying user page endpoints...")

    checks = []

    # Test: Fetch all books (used by /all-books page)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/books",
                params={"per_page": 20}
            )
            checks.append(("All Books Endpoint", response.status_code == 200))
    except Exception as e:
        checks.append(("All Books Endpoint", False))

    # Test: Search functionality (used by search bar)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/books/search",
                params={"q": "test", "per_page": 20}
            )
            checks.append(("Search Endpoint", response.status_code == 200))
    except Exception as e:
        checks.append(("Search Endpoint", False))

    # Print results
    print("\nEndpoint Status:")
    for name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {name}")

    return all(status for _, status in checks)


async def main(book_id: Optional[str] = None):
    """
    Run the complete verification.

    Args:
        book_id: Optional specific book ID to check
    """
    print("=" * 70)
    print("InkWave Book Display Verification")
    print("=" * 70)

    try:
        # 1. Fetch all books
        books, total = await fetch_all_books()

        # 2. If book_id provided, fetch that specific book
        if book_id:
            book = await fetch_book_detail(book_id)
            if not book:
                print("\n❌ Specified book not found!")
                sys.exit(1)

        # 3. Check if demo book exists
        demo_found = await check_demo_book()

        # 4. Test search functionality
        await search_books("Archbishop")

        # 5. Verify user page endpoints
        pages_ok = await verify_user_pages()

        # Summary
        print("\n" + "=" * 70)
        print("Verification Summary")
        print("=" * 70)
        print(f"{'✅' if total > 0 else '❌'} Books in database: {total}")
        print(f"{'✅' if demo_found else '⚠️ '} Demo book present: {'Yes' if demo_found else 'No'}")
        print(f"{'✅' if pages_ok else '❌'} User page endpoints: {'Working' if pages_ok else 'Failed'}")

        if book_id:
            print(f"{'✅' if book else '❌'} Specified book ({book_id}): {'Found' if book else 'Not Found'}")

        print("\n🌐 User-facing pages:")
        print(f"   Homepage: https://inkwave.ailabsafrica.com/")
        print(f"   All Books: https://inkwave.ailabsafrica.com/all-books")
        print(f"   Browse: https://inkwave.ailabsafrica.com/browse")
        print(f"   Admin Upload: https://inkwave.ailabsafrica.com/admin/books/upload")

        if total > 0 and pages_ok:
            print("\n✅ Verification PASSED - Books are displayable on user pages!")
        elif total > 0:
            print("\n⚠️  Verification PARTIAL - Books exist but some endpoints failing")
        else:
            print("\n❌ Verification FAILED - No books found")
            print("\n💡 Next steps:")
            print("   1. Navigate to: https://inkwave.ailabsafrica.com/admin/books/upload")
            print("   2. Upload demo book: backend/test_books/binding_the_strong_man_demo.pdf")
            print("   3. Run this script again to verify")

    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    book_id_arg = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(book_id_arg))
