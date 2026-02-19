#!/usr/bin/env python3
"""
Script to reprocess a book with AI chapter detection.
Run from inkwave/backend directory with proper environment.
"""
import asyncio
import sys
import os

# Add paths
sys.path.insert(0, '/opt/kasaai/apps')
sys.path.insert(0, '/opt/kasaai/apps/inkwave/backend')

# Set environment variables from .env file if needed
os.environ.setdefault('SUPABASE_URL', 'https://supabase.ailabsafrica.com')
os.environ.setdefault('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0')
os.environ.setdefault('MONGODB_URI', 'mongodb://admin:aawwER4444%40@127.0.0.1:27017/?authSource=admin')
os.environ.setdefault('MONGODB_DB_NAME', 'inkwave')
os.environ.setdefault('GEMINI_API_KEY', os.getenv('GEMINI_API_KEY', ''))
os.environ.setdefault('OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))


async def main():
    """Reprocess a book with AI chapter detection."""
    # Import after setting env vars
    from app.core.database import Database
    from app.services.book_service import BookService

    # Get book_id and user_id from command line
    if len(sys.argv) < 3:
        print("Usage: python reprocess_book.py <book_id> <user_id>")
        print("Example: python reprocess_book.py book_da7705efdff4 admin-test-user")
        sys.exit(1)

    book_id = sys.argv[1]
    user_id = sys.argv[2]

    print(f"Connecting to MongoDB...")
    await Database.connect()
    print("Connected!")

    print(f"\nStarting reprocessing of book: {book_id}")
    print("Using AI chapter detection...")
    print("-" * 50)

    try:
        result = await BookService.reprocess_book(
            book_id=book_id,
            user_id=user_id,
            use_ai_chapter_detection=True
        )

        print("\n" + "=" * 50)
        print("REPROCESSING RESULT")
        print("=" * 50)
        print(f"Status: {result.get('status')}")
        print(f"Chapters detected: {result.get('chapters')}")
        print(f"Processing status: {result.get('processing_status')}")
        print(f"\nCleanup summary:")
        cleanup = result.get('cleanup', {})
        print(f"  - Embeddings deleted: {cleanup.get('embeddings_deleted', 0)}")
        print(f"  - Chunks deleted: {cleanup.get('chunks_deleted', 0)}")
        print(f"  - Audio cache deleted: {cleanup.get('audio_cache_deleted', 0)}")
        print(f"  - Voice settings deleted: {cleanup.get('voice_settings_deleted', 0)}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
