"""
Process 'Destined To Make An Impact' book with enhanced filtering.

This script processes the book with the updated publisher review page filtering
and assigns the downloaded cover image.

Usage:
    python scripts/process_destined_impact.py <path_to_pdf>
"""

import asyncio
import sys
import os
import logging
import shutil
from pathlib import Path

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


async def process_book(pdf_path: str):
    """Process the Destined To Make An Impact book."""

    book_id = "book_ab5214413fb1"

    # Validate PDF exists
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return False

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

        # Copy PDF to storage location if not already there
        storage_path = f"/opt/kasaai/apps/inkwave/backend/storage/books/{book_id}.pdf"

        if os.path.abspath(pdf_path) == os.path.abspath(storage_path):
            logger.info(f"📄 PDF already in storage location: {storage_path}")
        else:
            logger.info(f"📄 Copying PDF to: {storage_path}")
            shutil.copy2(pdf_path, storage_path)
            logger.info(f"✅ PDF copied successfully")

        # Delete existing chunks if any
        deleted_chunks = await db.book_chunks.delete_many({"book_id": book_id})
        if deleted_chunks.deleted_count > 0:
            logger.info(f"🗑️ Deleted {deleted_chunks.deleted_count} existing chunks")

        # Prepare metadata
        book_metadata = {
            "title": book['title'],
            "author": book['author'],
            "cover_url": book.get('cover_url', '/api/v1/storage/covers/book_ab5214413fb1.jpg'),
            "genre": book.get('genre', 'Religious'),
            "description": book.get('description', 'Strategies and guidelines on how to make a dynamic impact on the earth.')
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
                    "processing_message": "Processing with enhanced filtering...",
                    "pdf_url": f"/api/v1/storage/books/{book_id}.pdf"
                }
            }
        )

        logger.info(f"🔄 Starting processing...")
        logger.info(f"📋 The new filtering will skip:")
        logger.info(f"   ✓ Publisher review/galley instructions")
        logger.info(f"   ✓ Xulon Press instructions")
        logger.info(f"   ✓ 'IMPORTANT, PLEASE READ THIS PAGE' sections")
        logger.info(f"   ✓ Copyright pages")
        logger.info(f"   ✓ Table of contents")

        # Process the book
        service = await get_book_processing_service()
        result = await service.process_book_file(
            file_path=storage_path,
            book_metadata=book_metadata,
            uploaded_by=book['uploaded_by'],
            book_id=book_id,
            use_ai_chapter_detection=False
        )

        logger.info(f"✅ Processing completed!")
        logger.info(f"📊 Chapters detected: {len(result.chapters)}")
        logger.info(f"📦 Total chunks: {len(result.chapters)}")

        # Show first few chunks
        chunks = await db.book_chunks.find(
            {"book_id": book_id}
        ).sort("chunk_index", 1).limit(5).to_list(5)

        logger.info(f"\n📖 First {len(chunks)} chunks:")
        for chunk in chunks:
            text_preview = chunk['text'][:150].replace('\n', ' ')
            logger.info(f"  [{chunk['chunk_index']}] {text_preview}...")

        logger.info(f"\n🎉 Book successfully processed with enhanced filtering!")
        logger.info(f"🔗 Cover image: {book_metadata['cover_url']}")

        return True

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/process_destined_impact.py <path_to_pdf>")
        print("\nExample:")
        print("  python scripts/process_destined_impact.py /path/to/destined_to_make_an_impact.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    success = asyncio.run(process_book(pdf_path))
    sys.exit(0 if success else 1)
