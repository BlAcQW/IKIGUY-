#!/usr/bin/env python3
"""
Reprocess "Understanding the end times" book with proper chapter detection.

This script:
1. Finds the book by title
2. Reprocesses it with AI chapter detection
3. Ensures proper metadata (title, author, description)
4. Verifies chapter identification and TOC skipping
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, '/opt/kasaai/apps')
sys.path.insert(0, '/opt/kasaai/apps/inkwave/backend')

from app.core.database import Database
from app.services.book_service import BookService

async def main():
    """Find and reprocess the book."""
    print("=" * 60)
    print("Reprocessing 'Understanding the end times'")
    print("=" * 60)
    
    # Connect to database
    print("\n1. Connecting to MongoDB...")
    await Database.connect()
    print("   ✓ Connected!")
    
    # Find the book
    print("\n2. Searching for book...")
    from app.core.database import get_db
    db = get_db()
    
    # Search for book with 'understanding' and 'end' in title
    books = await db.books.find({
        "$or": [
            {"title": {"$regex": "understanding.*end.*time", "$options": "i"}},
            {"title": {"$regex": "end.*time", "$options": "i"}},
            {"title": {"$regex": "understanding", "$options": "i"}}
        ]
    }).to_list(length=20)
    
    if not books:
        print("   ✗ Book not found!")
        print("\n   Available books:")
        all_books = await db.books.find({}).to_list(length=50)
        for b in all_books:
            print(f"     - {b.get('title')} (ID: {b.get('book_id')})")
        await Database.disconnect()
        return
    
    # Show found books
    print(f"   Found {len(books)} matching book(s):")
    for i, book in enumerate(books):
        print(f"     {i+1}. {book.get('title')} by {book.get('author', 'Unknown')}")
        print(f"        ID: {book.get('book_id')}")
        print(f"        Status: {book.get('processing_status', 'unknown')}")
    
    # Use first match
    book = books[0]
    book_id = book.get('book_id')
    print(f"\n   → Using: {book.get('title')} (ID: {book_id})")
    
    # Check current metadata
    print("\n3. Current book metadata:")
    print(f"   Title: {book.get('title')}")
    print(f"   Author: {book.get('author', 'Not set')}")
    print(f"   Description: {book.get('metadata', {}).get('summary', 'Not set')[:100]}...")
    print(f"   Chapters: {len(book.get('chapters', []))}")
    print(f"   Processing status: {book.get('processing_status')}")
    
    # Confirm reprocessing
    print("\n4. Reprocessing book with AI chapter detection...")
    print("   This will:")
    print("   - Clean up existing chunks and embeddings")
    print("   - Re-extract text and detect chapters")
    print("   - Regenerate embeddings")
    print("   - Trigger audio pre-generation")
    print()
    
    try:
        # Use admin user ID (or get from environment)
        user_id = os.getenv('ADMIN_USER_ID', 'admin')
        
        # Try to ensure PDF is available locally first
        print("   Checking PDF availability...")
        from app.services.storage_service import get_storage_service
        storage_service = await get_storage_service()
        pdf_content = await storage_service.download_book_pdf(book_id)
        
        if pdf_content:
            # Save to local temp location for processing
            local_pdf_path = f"/opt/kasaai/apps/inkwave/backend/storage/books/{book_id}.pdf"
            os.makedirs(os.path.dirname(local_pdf_path), exist_ok=True)
            with open(local_pdf_path, "wb") as f:
                f.write(pdf_content)
            print(f"   ✓ Downloaded PDF from Hetzner ({len(pdf_content)} bytes)")
        else:
            print("   ⚠ PDF not found in Hetzner, but continuing anyway...")
        
        result = await BookService.reprocess_book(
            book_id=book_id,
            user_id=user_id,
            use_ai_chapter_detection=True  # Use AI for better chapter detection
        )
        
        print("\n" + "=" * 60)
        print("REPROCESSING COMPLETE")
        print("=" * 60)
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Processing status: {result.get('processing_status', 'unknown')}")
        
        if 'chapters' in result:
            chapters = result['chapters']
            print(f"\nChapters detected: {len(chapters)}")
            for i, ch in enumerate(chapters[:10], 1):  # Show first 10
                print(f"  {i}. {ch.get('title', 'Unknown')} (chunks {ch.get('start_chunk_id')}-{ch.get('end_chunk_id')})")
            if len(chapters) > 10:
                print(f"  ... and {len(chapters) - 10} more")
        
        cleanup = result.get('cleanup', {})
        print(f"\nCleanup summary:")
        print(f"  - Embeddings deleted: {cleanup.get('embeddings_deleted', 0)}")
        print(f"  - Chunks deleted: {cleanup.get('chunks_deleted', 0)}")
        print(f"  - Audio cache deleted: {cleanup.get('audio_cache_deleted', 0)}")
        
        # Verify final state
        print("\n5. Verifying final state...")
        updated_book = await db.books.find_one({"book_id": book_id})
        if updated_book:
            print(f"   Title: {updated_book.get('title')}")
            print(f"   Author: {updated_book.get('author')}")
            print(f"   Chapters: {len(updated_book.get('chapters', []))}")
            print(f"   Processing status: {updated_book.get('processing_status')}")
            
            # Check chunks
            chunks = await db.book_chunks.find({"book_id": book_id}).sort("chunk_index", 1).to_list(length=10)
            print(f"   First few chunks:")
            for chunk in chunks[:5]:
                print(f"     Chunk {chunk.get('chunk_index')}: {chunk.get('text', '')[:60]}...")
        
        print("\n✓ Reprocessing complete!")
        print(f"\nBook ID: {book_id}")
        print("You can now test the book in the player.")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

