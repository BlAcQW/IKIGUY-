#!/usr/bin/env python3
"""
Update metadata and chapter info for "Understanding the end times" book.

Since Hetzner credentials aren't configured, we'll update metadata directly
and ensure proper chapter identification and TOC skipping.
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, '/opt/kasaai/apps')
sys.path.insert(0, '/opt/kasaai/apps/inkwave/backend')

from app.core.database import Database, get_db

async def main():
    """Update book metadata and chapters."""
    print("=" * 60)
    print("Updating 'Understanding the end times' metadata")
    print("=" * 60)
    
    await Database.connect()
    db = get_db()
    
    book_id = 'book_da7705efdff4'
    book = await db.books.find_one({'book_id': book_id})
    
    if not book:
        print(f"Book {book_id} not found!")
        await Database.disconnect()
        return
    
    print(f"\nCurrent state:")
    print(f"  Title: {book.get('title')}")
    print(f"  Author: {book.get('author')}")
    print(f"  Chapters: {len(book.get('chapters', []))}")
    
    # Get chunks to identify skip chunks (TOC)
    chunks = await db.book_chunks.find({'book_id': book_id}).sort('chunk_index', 1).to_list(length=None)
    print(f"  Total chunks: {len(chunks)}")
    
    # Identify TOC chunks (chunks with "table of contents" or lots of chapter references)
    skip_chunks = []
    for chunk in chunks[:10]:  # Check first 10 chunks
        text = chunk.get('text', '').lower()
        if 'table of contents' in text or ('contents' in text and 'chapter' in text):
            # Count chapter/page references
            chapter_refs = text.count('chapter') + text.count('part')
            dots = text.count('...') + text.count('.')
            if chapter_refs >= 2 and dots > 5:
                skip_chunks.append(chunk.get('chunk_index'))
                print(f"    → Marking chunk {chunk.get('chunk_index')} as TOC (skip)")
    
    # Find first playable chunk (after TOC)
    first_playable = 0
    for i, chunk in enumerate(chunks):
        if i not in skip_chunks and len(chunk.get('text', '')) > 50:
            first_playable = i
            print(f"    → First playable chunk: {i}")
            print(f"      Preview: {chunk.get('text', '')[:100]}...")
            break
    
    # Update book with skip_chunks
    update_data = {
        'skip_chunks': skip_chunks,
        'updated_at': datetime.utcnow()
    }
    
    # Ensure metadata is complete
    if not book.get('metadata', {}).get('summary'):
        update_data['metadata.summary'] = 'Sounding the trumpet of readiness to the end-time church'
    
    await db.books.update_one(
        {'book_id': book_id},
        {'$set': update_data}
    )
    
    print(f"\n✓ Updated book:")
    print(f"  - Skip chunks (TOC): {skip_chunks}")
    print(f"  - First playable chunk: {first_playable}")
    print(f"\nNote: Full reprocessing with chapter detection requires Hetzner credentials.")
    print(f"      Current chunks and metadata have been updated.")
    
    await Database.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

