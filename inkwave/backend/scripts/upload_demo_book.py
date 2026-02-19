"""
Upload Demo Book Script

Tests the complete end-to-end book upload flow:
1. Authenticates as admin user
2. Uploads the demo PDF
3. Monitors processing status
4. Verifies book appears in database and API

Usage:
    python upload_demo_book.py
"""

import asyncio
import os
import sys
from pathlib import Path
import httpx
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables
load_dotenv("/opt/kasaai/.env")

# Configuration
BACKEND_URL = "https://inkwave-api.ailabsafrica.com/api/v1"
# BACKEND_URL = "http://localhost:30033/api/v1"  # Use for local testing
SUPABASE_URL = "https://supabase.ailabsafrica.com"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvY2FsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEzMjIwNzUsImV4cCI6MjA3NjY4MjA3NX0.bwOq689zcxepQnidP5k4pU7e_MOr_SP-00UVEQFz0eQ"

# Admin credentials
ADMIN_EMAIL = "admin@ailabsafrica.com"
ADMIN_PASSWORD = "admin123"  # Default admin password

# Demo book
DEMO_BOOK_PATH = Path(__file__).parent.parent / "test_books" / "binding_the_strong_man_demo.pdf"


async def authenticate_admin():
    """
    Authenticate as admin user.

    Returns:
        Access token for API requests
    """
    print("🔐 Authenticating as admin user...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={
                "apikey": SUPABASE_KEY,
                "Content-Type": "application/json"
            },
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
        )

        if response.status_code != 200:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"   Response: {response.text}")
            raise Exception(f"Authentication failed: {response.text}")

        data = response.json()
        access_token = data.get("access_token")

        if not access_token:
            raise Exception("No access token in response")

        print(f"✅ Authenticated successfully")
        print(f"   User: {data.get('user', {}).get('email')}")

        return access_token


async def upload_book(access_token: str):
    """
    Upload the demo book via admin API.

    Args:
        access_token: Admin JWT token

    Returns:
        Book ID and upload response
    """
    print(f"\n📚 Uploading demo book: {DEMO_BOOK_PATH.name}")

    if not DEMO_BOOK_PATH.exists():
        raise FileNotFoundError(f"Demo book not found: {DEMO_BOOK_PATH}")

    # Book metadata
    metadata = {
        "title": "Binding The Strong Man",
        "author": "Archbishop Nicholas Duncan-Williams",
        "description": "A powerful study on spiritual warfare and breaking free from demonic strongholds. Learn to identify the strong man, use spiritual weapons, and walk in victory.",
        "cover_url": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=400&h=600&fit=crop",
        "duration_minutes": 45,
        "narrator": "Archbishop Duncan-Williams"
    }

    # Prepare multipart form data
    files = {
        "file": (DEMO_BOOK_PATH.name, open(DEMO_BOOK_PATH, "rb"), "application/pdf")
    }

    data = {
        "title": metadata["title"],
        "author": metadata["author"],
        "description": metadata["description"],
        "cover_url": metadata["cover_url"],
        "duration_minutes": str(metadata["duration_minutes"]),
        "narrator": metadata["narrator"]
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{BACKEND_URL}/admin/books/upload",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            files=files,
            data=data
        )

        # Close file
        files["file"][1].close()

        if response.status_code not in [200, 201]:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            raise Exception(f"Upload failed: {response.text}")

        result = response.json()
        book_id = result.get("book_id")

        print(f"✅ Book uploaded successfully!")
        print(f"   Book ID: {book_id}")
        print(f"   Title: {result.get('title')}")
        print(f"   Status: {result.get('status')}")
        print(f"   Chapters: {result.get('chapters_extracted', 0)}")

        return book_id, result


async def check_processing_status(access_token: str, book_id: str, max_wait: int = 60):
    """
    Monitor book processing status.

    Args:
        access_token: Admin JWT token
        book_id: Book identifier
        max_wait: Maximum seconds to wait for processing

    Returns:
        Final processing status
    """
    print(f"\n⏳ Monitoring processing status (max {max_wait}s)...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        waited = 0
        while waited < max_wait:
            response = await client.get(
                f"{BACKEND_URL}/admin/books/{book_id}/status",
                headers={
                    "Authorization": f"Bearer {access_token}"
                }
            )

            if response.status_code != 200:
                print(f"⚠️  Status check failed: {response.status_code}")
                break

            status_data = response.json()
            processing_status = status_data.get("processing_status", "unknown")

            print(f"   [{waited}s] Status: {processing_status}")

            if processing_status in ["ready", "completed", "error"]:
                print(f"\n✅ Processing finished: {processing_status}")
                return status_data

            await asyncio.sleep(5)
            waited += 5

        print(f"\n⏰ Timeout reached after {waited}s")
        return None


async def verify_book_in_list(access_token: str, book_id: str):
    """
    Verify the book appears in the books list API.

    Args:
        access_token: Admin JWT token
        book_id: Book identifier

    Returns:
        True if book found, False otherwise
    """
    print(f"\n🔍 Verifying book appears in API...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get all books
        response = await client.get(
            f"{BACKEND_URL}/books",
            params={"per_page": 50}
        )

        if response.status_code != 200:
            print(f"⚠️  Failed to fetch books: {response.status_code}")
            return False

        data = response.json()
        books = data.get("books", [])

        # Check if our book is in the list
        found = False
        for book in books:
            if book.get("id") == book_id:
                found = True
                print(f"✅ Book found in API!")
                print(f"   Title: {book.get('title')}")
                print(f"   Author: {book.get('author')}")
                print(f"   Cover: {book.get('cover_url', 'N/A')}")
                break

        if not found:
            print(f"❌ Book NOT found in API")
            print(f"   Total books: {data.get('total', 0)}")

        return found


async def verify_book_detail(access_token: str, book_id: str):
    """
    Verify the book detail endpoint works.

    Args:
        access_token: Admin JWT token (optional for this endpoint)
        book_id: Book identifier

    Returns:
        Book detail data
    """
    print(f"\n📖 Fetching book details...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BACKEND_URL}/books/{book_id}"
        )

        if response.status_code != 200:
            print(f"⚠️  Failed to fetch book details: {response.status_code}")
            return None

        book = response.json()

        print(f"✅ Book details retrieved!")
        print(f"   Title: {book.get('title')}")
        print(f"   Author: {book.get('author')}")
        print(f"   Description: {book.get('description', '')[:100]}...")
        print(f"   Chapters: {len(book.get('chapters', []))}")
        print(f"   Pages: {book.get('metadata', {}).get('page_count', 0)}")
        print(f"   Words: {book.get('metadata', {}).get('word_count', 0)}")

        return book


async def main():
    """Run the complete upload test."""
    print("=" * 70)
    print("InkWave Demo Book Upload Test")
    print("=" * 70)

    try:
        # 1. Authenticate
        access_token = await authenticate_admin()

        # 2. Upload book
        book_id, upload_result = await upload_book(access_token)

        # 3. Check processing status
        status = await check_processing_status(access_token, book_id, max_wait=120)

        # 4. Verify in books list
        in_list = await verify_book_in_list(access_token, book_id)

        # 5. Verify book details
        details = await verify_book_detail(access_token, book_id)

        # Summary
        print("\n" + "=" * 70)
        print("Upload Test Summary")
        print("=" * 70)
        print(f"✅ Authentication: Success")
        print(f"✅ Upload: Success (Book ID: {book_id})")
        print(f"{'✅' if status else '⚠️ '} Processing: {status.get('processing_status') if status else 'Timeout'}")
        print(f"{'✅' if in_list else '❌'} API List: {'Found' if in_list else 'Not Found'}")
        print(f"{'✅' if details else '❌'} Book Details: {'Retrieved' if details else 'Failed'}")

        print("\n🌐 Test the book on user pages:")
        print(f"   Homepage: https://inkwave.ailabsafrica.com/")
        print(f"   All Books: https://inkwave.ailabsafrica.com/all-books")
        print(f"   Player: https://inkwave.ailabsafrica.com/player/{book_id}")
        print(f"   Admin: https://inkwave.ailabsafrica.com/admin/books/upload")

        if status and details:
            print("\n✅ Upload test PASSED - Book is ready!")
        else:
            print("\n⚠️  Upload test PARTIAL - Book uploaded but processing may be incomplete")

    except Exception as e:
        print(f"\n❌ Upload test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
