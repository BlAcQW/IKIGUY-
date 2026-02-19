"""
Reprocess 'Divine Timing' with enhanced Xulon Press filtering.

This script reprocesses the book to apply the enhanced publisher review
and TOC filtering.
"""

import asyncio
import sys
import os
import logging
import shutil

# Add paths
sys.path.insert(0, '/opt/kasaai/apps')
sys.path.insert(0, '/opt/kasaai/apps/inkwave/backend')

from app.core.database import Database, get_db
from app.services.book_processing_service import get_book_processing_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def reprocess_book():
    """Reprocess the Divine Timing book."""

    book_id = "book_b8734beff0b5"

    # Connect to database
    await Database.connect()
    logger.info("✅ Connected to database")

    try:
        db = get_db()

        # Get book info
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            logger.error(f"Book {book_id} not found in database")
            return False

        logger.info(f"📚 Found book: {book['title']} by {book['author']}")
        logger.info(f"📷 Cover image: {book.get('cover_url', 'Not set')}")

        # PDF path
        storage_path = f"/opt/kasaai/apps/inkwave/backend/storage/books/{book_id}.pdf"

        if not os.path.exists(storage_path):
            logger.error(f"PDF file not found: {storage_path}")
            return False

        logger.info(f"📄 PDF found: {storage_path}")

        # Delete existing chunks
        deleted_chunks = await db.book_chunks.delete_many({"book_id": book_id})
        logger.info(f"🗑️ Deleted {deleted_chunks.deleted_count} existing chunks")

        # Prepare metadata
        book_metadata = {
            "title": book['title'],
            "author": book['author'],
            "cover_url": book.get('cover_url', ''),
            "genre": book.get('genre', 'Religious'),
            "description": book.get('description', '')
        }

        # Reset book status
        await db.books.update_one(
            {"book_id": book_id},
            {
                "$set": {
                    "processed": False,
                    "processing_status": "processing",
                    "processing_stage": "initializing",
                    "processing_progress": 0,
                    "processing_message": "Reprocessing with enhanced filtering...",
                    "pdf_url": f"/api/v1/storage/books/{book_id}.pdf"
                }
            }
        )

        logger.info(f"🔄 Starting reprocessing with enhanced filtering...")
        logger.info(f"📋 Enhanced filtering will skip:")
        logger.info(f"   ✓ Publisher review/galley instructions (Xulon Press)")
        logger.info(f"   ✓ 'IMPORTANT, PLEASE READ THIS PAGE' sections")
        logger.info(f"   ✓ 'To the author:' instructions")
        logger.info(f"   ✓ Table of Contents")
        logger.info(f"   ✓ Copyright pages")

        # Process the book
        service = await get_book_processing_service()
        result = await service.process_book_file(
            file_path=storage_path,
            book_metadata=book_metadata,
            uploaded_by=book['uploaded_by'],
            book_id=book_id,
            use_ai_chapter_detection=False
        )

        logger.info(f"✅ Reprocessing completed!")
        logger.info(f"📊 Chapters detected: {len(result.chapters)}")

        # Show first few chunks
        chunks = await db.book_chunks.find(
            {"book_id": book_id}
        ).sort("chunk_index", 1).limit(5).to_list(5)

        logger.info(f"\n📖 First {len(chunks)} chunks:")
        for chunk in chunks:
            text_preview = chunk['text'][:100].replace('\n', ' ')
            logger.info(f"  [{chunk['chunk_index']}] {text_preview}...")

        # Verify no Xulon Press instructions
        xulon_check = await db.book_chunks.count_documents({
            "book_id": book_id,
            "text": {"$regex": "IMPORTANT, PLEASE READ THIS PAGE", "$options": "i"}
        })

        if xulon_check == 0:
            logger.info(f"\n✅ VERIFIED: No Xulon Press instructions in chunks!")
        else:
            logger.warning(f"\n⚠️ WARNING: Found {xulon_check} chunks with Xulon instructions!")

        return True

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(reprocess_book())
    sys.exit(0 if success else 1)
